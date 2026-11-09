"""Real host builds, not unit imports or mocked workflow steps."""
import tomllib

import pytest

from e2e_harness.sftp import CASE, stage_artifact


@pytest.mark.parametrize('allow_hidden', [False, True])
def test_sftp_build_filters_final_output_without_deploy_settings(tmp_path, allow_hidden):
    original = {p.relative_to(CASE): p.read_bytes() for p in CASE.rglob('*') if p.is_file()}
    manifest = tomllib.loads((CASE / 'manifest.toml').read_text())
    site = stage_artifact(tmp_path / 'package', manifest['build']['hidden_paths'] if allow_hidden else '')
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
    assert original == {p.relative_to(CASE): p.read_bytes() for p in CASE.rglob('*') if p.is_file()}
