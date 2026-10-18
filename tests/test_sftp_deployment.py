"""Real host builds, not unit imports or mocked workflow steps."""
import json
import os
import subprocess
import sys
import tomllib

import pytest

from e2e_harness.sftp import CASE, prepare


@pytest.mark.parametrize('allow_hidden', [False, True])
def test_sftp_build_filters_final_output_and_relocates_bundle(tmp_path, allow_hidden):
    original = {p.relative_to(CASE): p.read_bytes() for p in CASE.rglob('*') if p.is_file()}
    manifest = tomllib.loads((CASE / 'manifest.toml').read_text())
    downloaded = prepare(tmp_path / 'package', hidden_paths=manifest['build']['hidden_paths'] if allow_hidden else None)
    site = downloaded / 'site'
    bundle = downloaded / 'deployment'
    assert (site / 'index.html').is_file()
    assert (site / 'comic/001/index.html').is_file()
    assert (site / 'marker.txt').read_text().strip() == 'SFTP fixture marker'
    assert 'ignored/inferred-path' not in (site / 'index.html').read_text()
    assert (site / '.htaccess').exists() == allow_hidden
    assert (site / '.allowed/nested/value.txt').exists() == allow_hidden
    assert not (site / '.private').exists()
    assert not (site / '.hook-private').exists()
    assert not (site / 'your_content/comics/future').exists()
    assert not (site / 'comic/future').exists()
    assert not (site / 'deployment').exists()
    assert {p.name for p in bundle.iterdir()} == {'connection.json', 'deploy.lftp', 'deploy.py'}
    assert json.loads((bundle / 'connection.json').read_text()) == {'host': '127.0.0.1', 'port': 22}
    assert str(tmp_path) not in (bundle / 'deploy.lftp').read_text()
    assert original == {p.relative_to(CASE): p.read_bytes() for p in CASE.rglob('*') if p.is_file()}
    # Execute the relocated public entrypoint without credentials or engine imports.
    result = subprocess.run([sys.executable, str(bundle / 'deploy.py'), '--output-dir', str(site)],
                            cwd=downloaded, env={'PATH': '', 'SYSTEMROOT': os.environ.get('SYSTEMROOT', '')},
                            text=True, capture_output=True, timeout=30)
    assert result.returncode != 0
    assert 'Set SFTP_USERNAME' in result.stderr
    assert 'ModuleNotFoundError' not in result.stderr
