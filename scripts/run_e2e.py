from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_BUILDS_ROOT = ROOT / 'golden_builds'
DEFAULT_SCENARIO = 'e2e_tests'
DEFAULT_GITHUB_REPOSITORY = 'comic-git/e2e_tests'
IGNORE_WORKSPACE_NAMES = {
    '.git',
    '.idea',
    'venv',
    'build',
    'golden_builds',
    'golden_toml',
    'comic_git_engine',
    '__pycache__',
}
IGNORE_WORKSPACE_SUFFIXES = {'.pyc'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Local e2e harness for comic_git_engine')
    parser.add_argument('command', choices=['refresh-build', 'legacy-build'], help='Harness command to run.')
    parser.add_argument('--scenario', default=DEFAULT_SCENARIO, help='Golden build scenario name.')
    parser.add_argument(
        '--github-repository',
        default=DEFAULT_GITHUB_REPOSITORY,
        help='Value to use for GITHUB_REPOSITORY during builds.',
    )
    parser.add_argument('--keep-temp', action='store_true', help='Keep the temporary workspace for debugging.')
    return parser.parse_args()


def scenario_golden_build_dir(scenario: str) -> Path:
    return GOLDEN_BUILDS_ROOT / scenario


def resolve_engine_target() -> Path:
    engine_path = ROOT / 'comic_git_engine'
    if not engine_path.exists():
        raise FileNotFoundError('comic_git_engine link or folder is missing from e2e_tests')
    return engine_path.resolve()


def should_ignore(path: Path) -> bool:
    if path.name in IGNORE_WORKSPACE_NAMES:
        return True
    if path.suffix in IGNORE_WORKSPACE_SUFFIXES:
        return True
    return False


def copy_fixture_repo(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for child in ROOT.iterdir():
        if should_ignore(child):
            continue
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)


def create_engine_junction(workspace: Path, engine_target: Path) -> None:
    subprocess.run(
        ['cmd', '/c', 'mklink', '/J', str(workspace / 'comic_git_engine'), str(engine_target)],
        check=True,
    )


def build_legacy_site(workspace: Path, github_repository: str) -> Path:
    env = os.environ.copy()
    env['GITHUB_REPOSITORY'] = github_repository
    subprocess.run(
        [sys.executable, str(workspace / 'comic_git_engine' / 'src' / 'build' / 'build_site.py')],
        cwd=workspace,
        env=env,
        check=True,
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


def cmd_refresh_build(args: argparse.Namespace) -> int:
    engine_target = resolve_engine_target()
    golden_dir = scenario_golden_build_dir(args.scenario)
    with TempWorkspace(args.keep_temp) as workspace:
        copy_fixture_repo(workspace)
        create_engine_junction(workspace, engine_target)
        build_dir = build_legacy_site(workspace, args.github_repository)
        refresh_golden_build(build_dir, golden_dir)
    print(f'Refreshed golden build at {golden_dir}')
    return 0


def cmd_legacy_build(args: argparse.Namespace) -> int:
    golden_dir = scenario_golden_build_dir(args.scenario)
    if not golden_dir.exists():
        print(f'{golden_dir} does not exist. Run refresh-build first.', file=sys.stderr)
        return 2
    engine_target = resolve_engine_target()
    with TempWorkspace(args.keep_temp) as workspace:
        copy_fixture_repo(workspace)
        create_engine_junction(workspace, engine_target)
        build_dir = build_legacy_site(workspace, args.github_repository)
        differences = compare_directories(golden_dir, build_dir)
    if differences:
        print(f'Legacy build did not match golden build scenario {args.scenario}:', file=sys.stderr)
        for diff in differences[:50]:
            print(f'  - {diff}', file=sys.stderr)
        if len(differences) > 50:
            print(f'  ... {len(differences) - 50} more differences', file=sys.stderr)
        return 1
    print(f'Legacy build matches golden build scenario {args.scenario}.')
    return 0


def main() -> int:
    args = parse_args()
    if args.command == 'refresh-build':
        return cmd_refresh_build(args)
    if args.command == 'legacy-build':
        return cmd_legacy_build(args)
    raise AssertionError(f'Unhandled command: {args.command}')


if __name__ == '__main__':
    raise SystemExit(main())