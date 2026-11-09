"""Stage and build the independent SFTP fixture using only the public CLI."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tomllib

from e2e_harness import runner

CASE = runner.ROOT / 'test_cases/deployment/sftp'


def stage_host(workspace: Path) -> None:
    """Copy the deployment fixture and engine into a disposable host."""
    runner.stage_test_case_content(workspace, CASE / 'your_content')
    # Copy instead of linking so fixtures clean up safely on Windows and Linux.
    for directory in ['src', 'templates', 'css', 'js', 'schemas']:
        shutil.copytree(runner.resolve_engine_target() / directory,
                        workspace / 'comic_git_engine' / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))


def stage_artifact(destination: Path, hidden_paths: str = "") -> Path:
    """Build without deployment settings, then relocate the site as Actions does."""
    destination.mkdir()
    manifest = tomllib.loads((CASE / 'manifest.toml').read_text(encoding='utf-8'))
    workspace = destination / 'host'
    stage_host(workspace)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith('SFTP_') and key not in ('INPUTS', 'SECRETS', 'OUTPUT_DIR')}
    env.update({key: value for key, value in manifest['env'].items() if not key.startswith('SFTP_')})
    env['OUTPUT_DIR'] = 'build'
    command = [sys.executable, '-B', str(workspace / 'comic_git_engine/src/build/build_site.py'),
               '--delete-scheduled-posts', '--hidden-paths', hidden_paths]
    result = subprocess.run(command, cwd=workspace, env=env, capture_output=True, text=True, timeout=120)
    if result.returncode or '============= ERROR =============' in result.stdout + result.stderr:
        raise AssertionError(result.stdout + result.stderr)
    site = destination / 'downloaded' / 'site'
    shutil.copytree(workspace / 'build', site)
    return site
