from __future__ import annotations

from pathlib import Path

import pytest

from e2e_harness import cms_browser, runner


def test_browser_harness_uses_the_generated_vendored_runtime_by_default() -> None:
    assert cms_browser.BrowserHarnessOptions().bundle_source is None
    assert cms_browser.PRODUCTION_DECAP_SCRIPT_PATH.startswith('vendor/decap-cms-')


def test_load_browser_fixture_reads_mutable_source_contract() -> None:
    fixture = cms_browser.load_browser_fixture('cms')

    assert fixture.name == 'cms'
    assert fixture.content_root == cms_browser.BROWSER_CASES_ROOT / 'cms' / 'your_content'
    assert fixture.env['GITHUB_REPOSITORY'] == 'comic-git/cms-browser'


def test_install_test_bundle_copies_local_bundle_and_rewrites_only_temp_admin(tmp_path: Path) -> None:
    build_dir = tmp_path / 'build'
    admin_dir = build_dir / 'admin'
    admin_dir.mkdir(parents=True)
    bundle = tmp_path / 'source-decap.js'
    bundle.write_text('window.CMS = {};', encoding='utf-8')
    index = f'<script src="{cms_browser.PRODUCTION_DECAP_SCRIPT_PATH}"></script>'
    (admin_dir / 'index.html').write_text(index, encoding='utf-8')

    cms_browser.install_test_bundle(build_dir, str(bundle))

    assert (admin_dir / 'decap-cms.js').read_text(encoding='utf-8') == 'window.CMS = {};'
    assert (admin_dir / 'index.html').read_text(encoding='utf-8') == (
        '<script src="/admin/decap-cms.js"></script>'
    )


def test_install_test_bundle_copies_runtime_assets_from_dist_directory(tmp_path: Path) -> None:
    build_dir = tmp_path / 'build'
    admin_dir = build_dir / 'admin'
    admin_dir.mkdir(parents=True)
    dist_dir = tmp_path / 'dist'
    dist_dir.mkdir()
    (dist_dir / 'decap-cms.js').write_text('main', encoding='utf-8')
    (dist_dir / '123.decap-cms.js').write_text('chunk', encoding='utf-8')
    (dist_dir / 'codec.wasm').write_bytes(b'wasm')
    (dist_dir / 'decap-cms.js.map').write_text('large map', encoding='utf-8')
    index = f'<script src="{cms_browser.PRODUCTION_DECAP_SCRIPT_PATH}"></script>'
    (admin_dir / 'index.html').write_text(index, encoding='utf-8')

    cms_browser.install_test_bundle(build_dir, str(dist_dir))

    assert (admin_dir / 'decap-cms.js').read_text(encoding='utf-8') == 'main'
    assert (admin_dir / '123.decap-cms.js').read_text(encoding='utf-8') == 'chunk'
    assert (admin_dir / 'codec.wasm').read_bytes() == b'wasm'
    assert not (admin_dir / 'decap-cms.js.map').exists()


def test_install_test_bundle_accepts_remote_override_without_copying(tmp_path: Path) -> None:
    admin_dir = tmp_path / 'admin'
    admin_dir.mkdir()
    index = f'<script src="{cms_browser.PRODUCTION_DECAP_SCRIPT_PATH}"></script>'
    (admin_dir / 'index.html').write_text(index, encoding='utf-8')

    cms_browser.install_test_bundle(tmp_path, 'http://127.0.0.1:9000/custom-decap.js')

    assert 'http://127.0.0.1:9000/custom-decap.js' in (admin_dir / 'index.html').read_text(encoding='utf-8')
    assert not (admin_dir / 'decap-cms.js').exists()


def test_install_test_bundle_rejects_unexpected_production_admin(tmp_path: Path) -> None:
    admin_dir = tmp_path / 'admin'
    admin_dir.mkdir()
    (admin_dir / 'index.html').write_text('<script src="other.js"></script>', encoding='utf-8')

    with pytest.raises(RuntimeError, match='exactly one expected Decap runtime path'):
        cms_browser.install_test_bundle(tmp_path, 'unused.js')


def test_require_available_port_reports_active_listener(monkeypatch) -> None:
    class ActiveConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

    monkeypatch.setattr(
        cms_browser.socket,
        'create_connection',
        lambda *_args, **_kwargs: ActiveConnection(),
    )

    with pytest.raises(RuntimeError, match='already in use'):
        cms_browser.require_available_port(8081)


def test_require_available_port_reports_bind_collision(monkeypatch) -> None:
    class UnavailableSocket:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def bind(self, _address):
            raise OSError('occupied')

    def refuse_connection(*_args, **_kwargs):
        raise OSError('not listening')

    monkeypatch.setattr(cms_browser.socket, 'create_connection', refuse_connection)
    monkeypatch.setattr(cms_browser.socket, 'socket', lambda *_args: UnavailableSocket())

    with pytest.raises(RuntimeError, match='already in use'):
        cms_browser.require_available_port(8081)
