from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_CASES_ROOT = ROOT / 'test_cases'
GOLDEN_BUILDS_ROOT = ROOT / 'golden_builds'
DEFAULT_CASE = 'baseline'
DEFAULT_PYTHON = ROOT / 'venv' / 'Scripts' / 'python.exe'
REQUIRED_BUILD_ENV_VARS = {'GITHUB_REPOSITORY'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Local e2e harness for comic_git_engine')
    parser.add_argument('command', choices=['refresh-build', 'check-build'], help='Harness command to run.')
    parser.add_argument(
        '--case',
        '--scenario',
        dest='case',
        default=None,
        help=f'Test case name under test_cases/. Defaults to {DEFAULT_CASE}. --scenario is accepted as a compatibility alias.',
    )
    parser.add_argument('--all', action='store_true', help='Run the command for every build-enabled test case.')
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
    parser.add_argument('--keep-temp', action='store_true', help='Keep the temporary workspace for debugging.')
    return parser.parse_args()


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


def selected_case(args: argparse.Namespace) -> str:
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
    if 'checks' not in manifest:
        raise ValueError('manifest must include a [checks] table')
    checks = manifest['checks']
    if not isinstance(checks, dict):
        raise ValueError('checks must be a table')
    for check_name in ('build', 'migration', 'migrated_build'):
        if check_name not in checks:
            raise ValueError(f'checks.{check_name} must be explicitly set')
        if not isinstance(checks[check_name], bool):
            raise ValueError(f'checks.{check_name} must be a boolean')
    return checks['build']


def build_env_overrides(args: argparse.Namespace, manifest: dict) -> dict[str, str]:
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


def build_site(workspace: Path, env_overrides: dict[str, str], python_executable: str) -> Path:
    env = os.environ.copy()
    env.update(env_overrides)
    result = subprocess.run(
        [python_executable, str(workspace / 'comic_git_engine' / 'src' / 'build' / 'build_site.py')],
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
        raise RuntimeError('Engine build reported an error. Check build output above.')
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


def compare_directories(expected: Path, actual: Path) -> list[str]:
    differences: list[str] = []

    def walk(exp: Path, act: Path, rel: Path = Path('.')) -> None:
        expected_entries = {p.name: p for p in exp.iterdir()} if exp.exists() else {}
        actual_entries = {p.name: p for p in act.iterdir()} if act.exists() else {}
        for name in sorted(expected_entries.keys() - actual_entries.keys()):
            differences.append(f'missing in actual: {rel / name}')
        for name in sorted(actual_entries.keys() - expected_entries.keys()):
            differences.append(f'unexpected in actual: {rel / name}')
        for name in sorted(expected_entries.keys() & actual_entries.keys()):
            exp_child = expected_entries[name]
            act_child = actual_entries[name]
            child_rel = rel / name
            if exp_child.is_dir() and act_child.is_dir():
                walk(exp_child, act_child, child_rel)
            elif exp_child.is_dir() != act_child.is_dir():
                differences.append(f'type mismatch: {child_rel}')
            elif not filecmp.cmp(exp_child, act_child, shallow=False):
                differences.append(f'content mismatch: {child_rel}')

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


def cmd_refresh_build_case(args: argparse.Namespace, case_name: str) -> int:
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


def cmd_refresh_build(args: argparse.Namespace) -> int:
    if args.all:
        print('refresh-build does not support --all. Refresh one test case at a time.', file=sys.stderr)
        return 2
    return cmd_refresh_build_case(args, selected_case(args))


def cmd_check_build_case(args: argparse.Namespace, case_name: str) -> int:
    warn_if_missing_test_case_doc(case_name)
    manifest = load_test_case_manifest(case_name)
    if not build_check_enabled(manifest):
        print(f'Test case {case_name} does not enable build output checks.', file=sys.stderr)
        return 2
    content_source = test_case_content_dir(case_name)
    env_overrides = build_env_overrides(args, manifest)
    golden_dir = case_golden_build_dir(case_name)
    if not golden_dir.exists():
        print(f'{golden_dir} does not exist. Run refresh-build first.', file=sys.stderr)
        return 2
    engine_target = resolve_engine_target()
    with TempWorkspace(args.keep_temp) as workspace:
        stage_test_case_content(workspace, content_source)
        create_engine_junction(workspace, engine_target)
        build_dir = build_site(workspace, env_overrides, args.python_executable)
        differences = compare_directories(golden_dir, build_dir)
    if differences:
        print(f'Build output did not match golden build for test case {case_name}:', file=sys.stderr)
        for diff in differences[:50]:
            print(f'  - {diff}', file=sys.stderr)
        if len(differences) > 50:
            print(f'  ... {len(differences) - 50} more differences', file=sys.stderr)
        return 1
    print(f'Build output matches golden build for test case {case_name}.')
    return 0


def cmd_check_build(args: argparse.Namespace) -> int:
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


def main() -> int:
    args = parse_args()
    if args.command == 'refresh-build':
        return cmd_refresh_build(args)
    if args.command == 'check-build':
        return cmd_check_build(args)
    raise AssertionError(f'Unhandled command: {args.command}')


if __name__ == '__main__':
    raise SystemExit(main())
