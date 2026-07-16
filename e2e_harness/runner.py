from __future__ import annotations

import argparse
import difflib
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_CASES_ROOT = ROOT / 'test_cases'
GOLDEN_BUILDS_ROOT = ROOT / 'golden_builds'
GOLDEN_TOML_ROOT = ROOT / 'golden_toml'
DEFAULT_CASE = 'baseline'
DEFAULT_PYTHON = ROOT / 'venv' / 'Scripts' / 'python.exe'
DEFAULT_MIGRATION_SCRIPT = Path('src/build/migrate_to_toml.py')
REQUIRED_BUILD_ENV_VARS = {'GITHUB_REPOSITORY'}
MAX_TEXT_DIFF_LINES = 120
TEXT_FILE_SUFFIXES = {
    '.css',
    '.csv',
    '.html',
    '.htm',
    '.ini',
    '.js',
    '.json',
    '.md',
    '.py',
    '.svg',
    '.toml',
    '.txt',
    '.xml',
    '.yaml',
    '.yml',
}
TEXT_ENCODINGS = ('utf-8-sig', 'utf-8', 'cp1252')


@dataclass(frozen=True)
class HarnessOptions:
    command: str
    case: str | None = None
    all: bool = False
    github_repository: str | None = None
    python_executable: str = str(DEFAULT_PYTHON if DEFAULT_PYTHON.exists() else Path(sys.executable))
    migration_script: str | None = None
    keep_temp: bool = False


@dataclass(frozen=True)
class DirectoryDifference:
    path: Path
    message: str
    kind: str
    diff_lines: tuple[str, ...] = ()

    def format_lines(self) -> tuple[str, ...]:
        if not self.diff_lines:
            return (self.message,)
        return (self.message, *self.diff_lines)


@dataclass(frozen=True)
class CheckResult:
    case_name: str
    check_name: str
    status: str
    message: str
    differences: tuple[DirectoryDifference, ...] = ()
    exit_code: int = 0

    @property
    def passed(self) -> bool:
        return self.status == 'passed'

    @property
    def skipped(self) -> bool:
        return self.status == 'skipped'


def passed_result(case_name: str, check_name: str, message: str) -> CheckResult:
    return CheckResult(case_name, check_name, 'passed', message)


def failed_result(
        case_name: str,
        check_name: str,
        message: str,
        differences: list[DirectoryDifference] | tuple[DirectoryDifference, ...] = (),
        exit_code: int = 1,
) -> CheckResult:
    return CheckResult(case_name, check_name, 'failed', message, tuple(differences), exit_code)


def skipped_result(case_name: str, check_name: str, message: str) -> CheckResult:
    return CheckResult(case_name, check_name, 'skipped', message, exit_code=2)


def print_check_result(result: CheckResult) -> None:
    if result.passed:
        print(result.message)
        return
    stream = sys.stderr if not result.skipped else sys.stdout
    print(result.message, file=stream)
    for diff in result.differences[:50]:
        lines = diff.format_lines()
        print(f'  - {lines[0]}', file=stream)
        for line in lines[1:]:
            print(f'    {line}', file=stream)
    if len(result.differences) > 50:
        print(f'  ... {len(result.differences) - 50} more differences', file=stream)


def parse_args() -> HarnessOptions:
    parser = argparse.ArgumentParser(description='Local e2e harness for comic_git_engine')
    parser.add_argument(
        'command',
        choices=['refresh-build', 'check-build', 'refresh-migration', 'check-migration', 'check-migrated-build'],
        help='Harness command to run.',
    )
    parser.add_argument(
        '--case',
        '--scenario',
        dest='case',
        default=None,
        help=f'Test case name under test_cases/. Defaults to {DEFAULT_CASE}. --scenario is accepted as a compatibility alias.',
    )
    parser.add_argument('--all', action='store_true', help='Run the command for every enabled test case.')
    parser.add_argument(
        '--github-repository',
        default=None,
        help='Override the manifest value for GITHUB_REPOSITORY during builds.',
    )
    parser.add_argument(
        '--python',
        dest='python_executable',
        default=str(DEFAULT_PYTHON if DEFAULT_PYTHON.exists() else Path(sys.executable)),
        help='Python executable to use when running comic_git_engine.',
    )
    parser.add_argument(
        '--migration-script',
        default=None,
        help='Migration script path relative to comic_git_engine/. Defaults to src/build/migrate_to_toml.py.',
    )
    parser.add_argument('--keep-temp', action='store_true', help='Keep the temporary workspace for debugging.')
    args = parser.parse_args()
    return HarnessOptions(
        command=args.command,
        case=args.case,
        all=args.all,
        github_repository=args.github_repository,
        python_executable=args.python_executable,
        migration_script=args.migration_script,
        keep_temp=args.keep_temp,
    )


def test_case_dir(case_name: str) -> Path:
    return TEST_CASES_ROOT / case_name


def test_case_content_dir(case_name: str) -> Path:
    return test_case_dir(case_name) / 'your_content'


def test_case_manifest_path(case_name: str) -> Path:
    return test_case_dir(case_name) / 'manifest.toml'


def test_case_doc_path(case_name: str) -> Path:
    return test_case_dir(case_name) / 'TEST_CASE.md'


def case_golden_build_dir(case_name: str) -> Path:
    return GOLDEN_BUILDS_ROOT / case_name


def case_golden_toml_dir(case_name: str) -> Path:
    return GOLDEN_TOML_ROOT / case_name


def selected_case(args: HarnessOptions) -> str:
    return args.case or DEFAULT_CASE


def list_test_cases() -> list[str]:
    if not TEST_CASES_ROOT.exists():
        return []
    return sorted(
        child.name
        for child in TEST_CASES_ROOT.iterdir()
        if child.is_dir() and (child / 'manifest.toml').exists()
    )


def warn_if_missing_test_case_doc(case_name: str) -> None:
    doc_path = test_case_doc_path(case_name)
    if not doc_path.exists():
        print(f'Warning: missing test case documentation: {doc_path}', file=sys.stderr)


def load_test_case_manifest(case_name: str) -> dict:
    manifest_path = test_case_manifest_path(case_name)
    if not manifest_path.exists():
        raise FileNotFoundError(f'Missing test case manifest: {manifest_path}')
    with manifest_path.open('rb') as manifest_file:
        manifest = tomllib.load(manifest_file)
    manifest_name = manifest.get('name')
    if manifest_name is not None and manifest_name != case_name:
        raise ValueError(f'Manifest name {manifest_name!r} does not match test case {case_name!r}')
    if not isinstance(manifest.get('description', ''), str):
        raise ValueError('description must be a string when present')
    if 'source_format' not in manifest:
        raise ValueError('manifest must include source_format')
    if not isinstance(manifest['source_format'], str):
        raise ValueError('source_format must be a string')
    tags = manifest.get('tags', [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise ValueError('tags must be a list of strings when present')
    return manifest


def build_check_enabled(manifest: dict) -> bool:
    return check_enabled(manifest, 'build')


def migration_check_enabled(manifest: dict) -> bool:
    return check_enabled(manifest, 'migration')


def migrated_build_check_enabled(manifest: dict) -> bool:
    return check_enabled(manifest, 'migrated_build')


def check_enabled(manifest: dict, check_name: str) -> bool:
    if 'checks' not in manifest:
        raise ValueError('manifest must include a [checks] table')
    checks = manifest['checks']
    if not isinstance(checks, dict):
        raise ValueError('checks must be a table')
    for required_check_name in ('build', 'migration', 'migrated_build'):
        if required_check_name not in checks:
            raise ValueError(f'checks.{required_check_name} must be explicitly set')
        if not isinstance(checks[required_check_name], bool):
            raise ValueError(f'checks.{required_check_name} must be a boolean')
    return checks[check_name]


def build_env_overrides(args: HarnessOptions, manifest: dict) -> dict[str, str]:
    if 'env' not in manifest:
        raise ValueError('manifest must include an [env] table')
    env_config = manifest['env']
    if not isinstance(env_config, dict):
        raise ValueError('env must be a table of environment variable names and string values')
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in env_config.items()):
        raise ValueError('env must only contain string keys and string values')
    missing = sorted(REQUIRED_BUILD_ENV_VARS - env_config.keys())
    if missing:
        raise ValueError(f'env is missing required build variables: {", ".join(missing)}')
    env_overrides = dict(env_config)
    if args.github_repository:
        env_overrides['GITHUB_REPOSITORY'] = args.github_repository
    return env_overrides


def migration_script_relative_path(args: HarnessOptions, manifest: dict) -> Path:
    configured_path = args.migration_script
    migration_config = manifest.get('migration', {})
    if migration_config:
        if not isinstance(migration_config, dict):
            raise ValueError('migration must be a table when present')
        manifest_script = migration_config.get('script')
        if manifest_script is not None:
            if not isinstance(manifest_script, str):
                raise ValueError('migration.script must be a string when present')
            configured_path = manifest_script
    return Path(configured_path) if configured_path else DEFAULT_MIGRATION_SCRIPT


def resolve_engine_target() -> Path:
    engine_path = ROOT / 'comic_git_engine'
    if not engine_path.exists():
        raise FileNotFoundError('comic_git_engine link or folder is missing from e2e_tests')
    return engine_path.resolve()


def stage_test_case_content(destination: Path, content_source: Path) -> None:
    if not content_source.exists():
        raise FileNotFoundError(f'Missing test case content directory: {content_source}')
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(content_source, destination / 'your_content')


def create_engine_junction(workspace: Path, engine_target: Path) -> None:
    subprocess.run(
        ['cmd', '/c', 'mklink', '/J', str(workspace / 'comic_git_engine'), str(engine_target)],
        check=True,
    )


def run_engine_script(
        workspace: Path,
        script_relative_path: Path,
        env_overrides: dict[str, str],
        python_executable: str,
        error_label: str,
        missing_hint: str = '',
        script_args: list[str] | None = None,
) -> None:
    script_path = workspace / 'comic_git_engine' / script_relative_path
    if not script_path.exists():
        hint = f'\n{missing_hint}' if missing_hint else ''
        raise FileNotFoundError(
            f'{error_label} script is missing: {script_relative_path}\n'
            f'Expected to find it under comic_git_engine/.{hint}'
        )
    env = os.environ.copy()
    env.update(env_overrides)
    command = [python_executable, str(script_path)]
    if script_args:
        command.extend(script_args)
    result = subprocess.run(
        command,
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args)
    if '============= ERROR =============' in result.stdout:
        raise RuntimeError(f'{error_label} reported an error. Check output above.')


def run_migration(
        workspace: Path,
        env_overrides: dict[str, str],
        python_executable: str,
        script_relative_path: Path,
) -> None:
    run_engine_script(
        workspace,
        script_relative_path,
        env_overrides,
        python_executable,
        'TOML migration',
        'Pass --migration-script if the script lands elsewhere.',
        ['--write'],
    )
    run_engine_script(
        workspace,
        script_relative_path,
        env_overrides,
        python_executable,
        'TOML migration',
        'Pass --migration-script if the script lands elsewhere.',
        ['--write', '--delete-legacy'],
    )


def build_site(workspace: Path, env_overrides: dict[str, str], python_executable: str) -> Path:
    run_engine_script(
        workspace,
        Path('src/build/build_site.py'),
        env_overrides,
        python_executable,
        'Engine build',
    )
    build_dir = workspace / 'build'
    if not build_dir.exists():
        raise RuntimeError('Build did not produce a build/ directory. Check build output above.')
    return build_dir


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def refresh_golden_build(source_build: Path, golden_dir: Path) -> None:
    reset_directory(golden_dir)
    for child in source_build.iterdir():
        target = golden_dir / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)
    normalize_text_line_endings(golden_dir)


def is_supported_text_file(path: Path) -> bool:
    if path.suffix.lower() not in TEXT_FILE_SUFFIXES:
        return False
    content = path.read_bytes()
    if b'\x00' in content:
        return False
    for encoding in TEXT_ENCODINGS:
        try:
            content.decode(encoding)
        except UnicodeDecodeError:
            continue
        return True
    return False


def normalize_text_file_line_endings(path: Path) -> None:
    if not is_supported_text_file(path):
        return
    content = path.read_bytes()
    normalized = content.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    if normalized != content:
        path.write_bytes(normalized)


def normalize_text_line_endings(root: Path) -> None:
    if root.is_file():
        normalize_text_file_line_endings(root)
        return
    for path in root.rglob('*'):
        if path.is_file():
            normalize_text_file_line_endings(path)


def read_text_file(path: Path) -> str | None:
    if not is_supported_text_file(path):
        return None
    content = path.read_bytes()
    for encoding in TEXT_ENCODINGS:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def text_file_diff(expected: Path, actual: Path) -> tuple[str, ...]:
    expected_text = read_text_file(expected)
    actual_text = read_text_file(actual)
    if expected_text is None or actual_text is None:
        return ()

    diff_lines = tuple(difflib.unified_diff(
        expected_text.splitlines(),
        actual_text.splitlines(),
        fromfile=f'expected: {expected}',
        tofile=f'actual: {actual}',
        lineterm='',
    ))
    if not diff_lines and expected_text != actual_text:
        return ('text differs only by line endings or final newline',)
    if len(diff_lines) <= MAX_TEXT_DIFF_LINES:
        return diff_lines
    omitted = len(diff_lines) - MAX_TEXT_DIFF_LINES
    return (*diff_lines[:MAX_TEXT_DIFF_LINES], f'... {omitted} diff lines omitted')


def normalized_line_endings(text: str) -> str:
    return text.replace('\r\n', '\n').replace('\r', '\n')


def text_files_match_after_line_ending_normalization(expected: Path, actual: Path) -> bool:
    expected_text = read_text_file(expected)
    actual_text = read_text_file(actual)
    if expected_text is None or actual_text is None:
        return False
    return normalized_line_endings(expected_text) == normalized_line_endings(actual_text)


def compare_directories(expected: Path, actual: Path, ignored_roots: set[str] | None = None) -> list[DirectoryDifference]:
    differences: list[DirectoryDifference] = []
    ignored_roots = ignored_roots or set()

    def walk(exp: Path, act: Path, rel: Path = Path('.')) -> None:
        if rel.parts and rel.parts[0] in ignored_roots:
            return
        expected_entries = {p.name: p for p in exp.iterdir()} if exp.exists() else {}
        actual_entries = {p.name: p for p in act.iterdir()} if act.exists() else {}
        for name in sorted(expected_entries.keys() - actual_entries.keys()):
            child_rel = rel / name
            differences.append(DirectoryDifference(child_rel, f'missing in actual: {child_rel}', 'missing'))
        for name in sorted(actual_entries.keys() - expected_entries.keys()):
            child_rel = rel / name
            differences.append(DirectoryDifference(child_rel, f'unexpected in actual: {child_rel}', 'unexpected'))
        for name in sorted(expected_entries.keys() & actual_entries.keys()):
            exp_child = expected_entries[name]
            act_child = actual_entries[name]
            child_rel = rel / name
            if exp_child.is_dir() and act_child.is_dir():
                walk(exp_child, act_child, child_rel)
            elif exp_child.is_dir() != act_child.is_dir():
                differences.append(DirectoryDifference(child_rel, f'type mismatch: {child_rel}', 'type_mismatch'))
            elif not filecmp.cmp(exp_child, act_child, shallow=False):
                if text_files_match_after_line_ending_normalization(exp_child, act_child):
                    continue
                differences.append(DirectoryDifference(
                    child_rel,
                    f'content mismatch: {child_rel}',
                    'content_mismatch',
                    text_file_diff(exp_child, act_child),
                ))

    walk(expected, actual)
    return differences


class TempWorkspace:
    def __init__(self, keep_temp: bool):
        self.keep_temp = keep_temp
        self._tmp: tempfile.TemporaryDirectory[str] | None = None
        self.path: Path | None = None

    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory(prefix='comic_git_e2e_')
        self.path = Path(self._tmp.name)
        return self.path

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.keep_temp and self.path is not None:
            print(f'Kept temp workspace at {self.path}')
            return
        if self._tmp is not None:
            self._tmp.cleanup()


def cmd_refresh_build_case(args: HarnessOptions, case_name: str) -> int:
    warn_if_missing_test_case_doc(case_name)
    manifest = load_test_case_manifest(case_name)
    if not build_check_enabled(manifest):
        print(f'Test case {case_name} does not enable build output checks.', file=sys.stderr)
        return 2
    content_source = test_case_content_dir(case_name)
    env_overrides = build_env_overrides(args, manifest)
    engine_target = resolve_engine_target()
    golden_dir = case_golden_build_dir(case_name)
    with TempWorkspace(args.keep_temp) as workspace:
        stage_test_case_content(workspace, content_source)
        create_engine_junction(workspace, engine_target)
        build_dir = build_site(workspace, env_overrides, args.python_executable)
        refresh_golden_build(build_dir, golden_dir)
    print(f'Refreshed golden build at {golden_dir}')
    return 0


def cmd_refresh_build(args: HarnessOptions) -> int:
    if args.all:
        print('refresh-build does not support --all. Refresh one test case at a time.', file=sys.stderr)
        return 2
    return cmd_refresh_build_case(args, selected_case(args))


def check_build_case(args: HarnessOptions, case_name: str) -> CheckResult:
    warn_if_missing_test_case_doc(case_name)
    manifest = load_test_case_manifest(case_name)
    if not build_check_enabled(manifest):
        return skipped_result(case_name, 'build', f'Test case {case_name} does not enable build output checks.')
    content_source = test_case_content_dir(case_name)
    env_overrides = build_env_overrides(args, manifest)
    golden_dir = case_golden_build_dir(case_name)
    if not golden_dir.exists():
        return failed_result(case_name, 'build', f'{golden_dir} does not exist. Run refresh-build first.', exit_code=2)
    engine_target = resolve_engine_target()
    with TempWorkspace(args.keep_temp) as workspace:
        stage_test_case_content(workspace, content_source)
        create_engine_junction(workspace, engine_target)
        build_dir = build_site(workspace, env_overrides, args.python_executable)
        normalize_text_line_endings(build_dir)
        differences = compare_directories(golden_dir, build_dir)
    if differences:
        return failed_result(
            case_name,
            'build',
            f'Build output did not match golden build for test case {case_name}:',
            differences,
        )
    return passed_result(case_name, 'build', f'Build output matches golden build for test case {case_name}.')


def cmd_check_build_case(args: HarnessOptions, case_name: str) -> int:
    result = check_build_case(args, case_name)
    print_check_result(result)
    return result.exit_code


def cmd_check_build(args: HarnessOptions) -> int:
    if not args.all:
        return cmd_check_build_case(args, selected_case(args))

    case_names = list_test_cases()
    if not case_names:
        print(f'No test cases found under {TEST_CASES_ROOT}', file=sys.stderr)
        return 2

    failures = 0
    skipped = 0
    for case_name in case_names:
        manifest = load_test_case_manifest(case_name)
        if not build_check_enabled(manifest):
            skipped += 1
            print(f'Skipping test case {case_name}; build output checks are disabled.')
            continue
        print(f'Checking build output for test case {case_name}...', flush=True)
        result = cmd_check_build_case(args, case_name)
        if result != 0:
            failures += 1

    checked = len(case_names) - skipped
    if failures:
        print(f'Build output checks failed for {failures} of {checked} checked test cases.', file=sys.stderr)
        return 1
    print(f'Build output checks passed for {checked} test case(s); skipped {skipped}.')
    return 0


def cmd_refresh_migration_case(args: HarnessOptions, case_name: str) -> int:
    warn_if_missing_test_case_doc(case_name)
    manifest = load_test_case_manifest(case_name)
    if not migration_check_enabled(manifest):
        print(f'Test case {case_name} does not enable migration output checks.', file=sys.stderr)
        return 2
    content_source = test_case_content_dir(case_name)
    env_overrides = build_env_overrides(args, manifest)
    engine_target = resolve_engine_target()
    script_relative_path = migration_script_relative_path(args, manifest)
    golden_dir = case_golden_toml_dir(case_name)
    with TempWorkspace(args.keep_temp) as workspace:
        stage_test_case_content(workspace, content_source)
        create_engine_junction(workspace, engine_target)
        run_migration(workspace, env_overrides, args.python_executable, script_relative_path)
        refresh_golden_build(workspace / 'your_content', golden_dir)
    print(f'Refreshed golden TOML migration output at {golden_dir}')
    return 0


def cmd_refresh_migration(args: HarnessOptions) -> int:
    if args.all:
        print('refresh-migration does not support --all. Refresh one test case at a time.', file=sys.stderr)
        return 2
    return cmd_refresh_migration_case(args, selected_case(args))


def check_migration_case(args: HarnessOptions, case_name: str) -> CheckResult:
    warn_if_missing_test_case_doc(case_name)
    manifest = load_test_case_manifest(case_name)
    if not migration_check_enabled(manifest):
        return skipped_result(case_name, 'migration', f'Test case {case_name} does not enable migration output checks.')
    content_source = test_case_content_dir(case_name)
    env_overrides = build_env_overrides(args, manifest)
    golden_dir = case_golden_toml_dir(case_name)
    if not golden_dir.exists():
        return failed_result(case_name, 'migration', f'{golden_dir} does not exist. Run refresh-migration first.', exit_code=2)
    engine_target = resolve_engine_target()
    script_relative_path = migration_script_relative_path(args, manifest)
    with TempWorkspace(args.keep_temp) as workspace:
        stage_test_case_content(workspace, content_source)
        create_engine_junction(workspace, engine_target)
        run_migration(workspace, env_overrides, args.python_executable, script_relative_path)
        normalize_text_line_endings(workspace / 'your_content')
        differences = compare_directories(golden_dir, workspace / 'your_content')
    if differences:
        return failed_result(
            case_name,
            'migration',
            f'Migration output did not match golden TOML output for test case {case_name}:',
            differences,
        )
    return passed_result(case_name, 'migration', f'Migration output matches golden TOML output for test case {case_name}.')


def cmd_check_migration_case(args: HarnessOptions, case_name: str) -> int:
    result = check_migration_case(args, case_name)
    print_check_result(result)
    return result.exit_code


def cmd_check_migration(args: HarnessOptions) -> int:
    if not args.all:
        return cmd_check_migration_case(args, selected_case(args))
    return cmd_check_all(args, migration_check_enabled, cmd_check_migration_case, 'migration output')


def check_migrated_build_case(args: HarnessOptions, case_name: str) -> CheckResult:
    warn_if_missing_test_case_doc(case_name)
    manifest = load_test_case_manifest(case_name)
    if not migrated_build_check_enabled(manifest):
        return skipped_result(case_name, 'migrated_build', f'Test case {case_name} does not enable migrated build output checks.')
    content_source = test_case_content_dir(case_name)
    env_overrides = build_env_overrides(args, manifest)
    golden_dir = case_golden_build_dir(case_name)
    if not golden_dir.exists():
        return failed_result(case_name, 'migrated_build', f'{golden_dir} does not exist. Run refresh-build first.', exit_code=2)
    engine_target = resolve_engine_target()
    script_relative_path = migration_script_relative_path(args, manifest)
    with TempWorkspace(args.keep_temp) as workspace:
        stage_test_case_content(workspace, content_source)
        create_engine_junction(workspace, engine_target)
        run_migration(workspace, env_overrides, args.python_executable, script_relative_path)
        build_dir = build_site(workspace, env_overrides, args.python_executable)
        normalize_text_line_endings(build_dir)
        differences = compare_directories(golden_dir, build_dir, ignored_roots={'your_content'})
    if differences:
        return failed_result(
            case_name,
            'migrated_build',
            f'Migrated build output did not match golden build for test case {case_name}:',
            differences,
        )
    return passed_result(case_name, 'migrated_build', f'Migrated build output matches golden build for test case {case_name}.')


def cmd_check_migrated_build_case(args: HarnessOptions, case_name: str) -> int:
    result = check_migrated_build_case(args, case_name)
    print_check_result(result)
    return result.exit_code


def cmd_check_migrated_build(args: HarnessOptions) -> int:
    if not args.all:
        return cmd_check_migrated_build_case(args, selected_case(args))
    return cmd_check_all(args, migrated_build_check_enabled, cmd_check_migrated_build_case, 'migrated build output')


def cmd_check_all(args: HarnessOptions, is_enabled, run_case, label: str) -> int:
    case_names = list_test_cases()
    if not case_names:
        print(f'No test cases found under {TEST_CASES_ROOT}', file=sys.stderr)
        return 2

    failures = 0
    skipped = 0
    for case_name in case_names:
        manifest = load_test_case_manifest(case_name)
        if not is_enabled(manifest):
            skipped += 1
            print(f'Skipping test case {case_name}; {label} checks are disabled.')
            continue
        print(f'Checking {label} for test case {case_name}...', flush=True)
        result = run_case(args, case_name)
        if result != 0:
            failures += 1

    checked = len(case_names) - skipped
    if failures:
        print(f'{label.capitalize()} checks failed for {failures} of {checked} checked test cases.', file=sys.stderr)
        return 1
    print(f'{label.capitalize()} checks passed for {checked} test case(s); skipped {skipped}.')
    return 0


def main() -> int:
    args = parse_args()
    if args.command == 'refresh-build':
        return cmd_refresh_build(args)
    if args.command == 'check-build':
        return cmd_check_build(args)
    if args.command == 'refresh-migration':
        return cmd_refresh_migration(args)
    if args.command == 'check-migration':
        return cmd_check_migration(args)
    if args.command == 'check-migrated-build':
        return cmd_check_migrated_build(args)
    raise AssertionError(f'Unhandled command: {args.command}')


if __name__ == '__main__':
    raise SystemExit(main())
