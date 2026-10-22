"""Stage and build the independent SFTP fixture using only the public CLI."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tomllib

from e2e_harness import runner

CASE = runner.ROOT / 'test_cases/deployment/sftp'


def prepare(destination: Path, *, hidden_paths: str | None = None, clean: bool = True) -> Path:
    """Create a new portable test package, without importing engine internals."""
    destination.mkdir(parents=True, exist_ok=False)
    manifest = tomllib.loads((CASE / 'manifest.toml').read_text())
    workspace = destination / 'host'
    runner.stage_test_case_content(workspace, CASE / 'your_content')
    # Copy instead of linking: safe cleanup on both Windows and Linux, and the
    # package proves the downloaded runner needs no engine checkout at deploy time.
    for directory in ['src', 'templates', 'css', 'js', 'schemas']:
        shutil.copytree(runner.resolve_engine_target() / directory,
                        workspace / 'comic_git_engine' / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    env = {key: value for key, value in os.environ.items()
           if not key.startswith('SFTP_') and key not in ('INPUTS', 'SECRETS', 'OUTPUT_DIR')}
    env.update(manifest['env'], OUTPUT_DIR='build', SFTP_CLEAN=str(clean).lower())
    command = [sys.executable, str(workspace / 'comic_git_engine/src/build/build_site.py'),
               '--delete-scheduled-posts', '--sftp-deploy-dir', 'deployment']
    if hidden_paths is not None:
        command += ['--hidden-paths', hidden_paths]
    result = subprocess.run(command, cwd=workspace, env=env, capture_output=True, text=True, timeout=120)
    if result.returncode or '============= ERROR =============' in result.stdout + result.stderr:
        raise AssertionError(result.stdout + result.stderr)
    downloaded = destination / 'downloaded'
    downloaded.mkdir()
    shutil.copytree(workspace / 'build', downloaded / 'site')
    shutil.copytree(workspace / 'deployment', downloaded / 'deployment')
    return downloaded


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path, help='New directory for the portable test package')
    args = parser.parse_args()
    manifest = tomllib.loads((CASE / 'manifest.toml').read_text())
    for name, clean in [('clean', True), ('keep', False)]:
        prepare(args.destination.resolve() / name, hidden_paths=manifest['build']['hidden_paths'], clean=clean)
    shutil.copyfile(runner.ROOT / 'scripts/check_sftp_transfer.py', args.destination / 'check_sftp_transfer.py')
    print(f'Prepared SFTP packages in {args.destination}')
