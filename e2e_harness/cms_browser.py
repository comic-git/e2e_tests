from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
import threading
import time
import tomllib
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from e2e_harness import runner


BROWSER_CASES_ROOT = runner.ROOT / 'test_cases' / 'browser'
DEFAULT_CASE = 'cms'
DECAP_SERVER_PACKAGE = runner.ROOT / 'node_modules' / 'decap-server' / 'package.json'
DECAP_PROXY_PORT = 8081
PRODUCTION_DECAP_SCRIPT_PATH = 'vendor/decap-cms-3.16.2-comic-git-b28103c19f4d/decap-cms.js'
ARTIFACTS_ROOT = runner.ROOT / 'artifacts' / 'browser'


@dataclass(frozen=True)
class BrowserFixture:
    name: str
    root: Path
    content_root: Path
    env: dict[str, str]


@dataclass(frozen=True)
class BrowserHarnessOptions:
    bundle_source: str | None = None
    keep_temp: bool = False
    python_executable: str = str(
        runner.DEFAULT_PYTHON if runner.DEFAULT_PYTHON.exists() else Path(sys.executable)
    )


def load_browser_fixture(case_name: str = DEFAULT_CASE) -> BrowserFixture:
    root = BROWSER_CASES_ROOT / case_name
    manifest_path = root / 'manifest.toml'
    content_root = root / 'your_content'
    if not manifest_path.is_file():
        raise FileNotFoundError(f'Missing browser fixture manifest: {manifest_path}')
    if not content_root.is_dir():
        raise FileNotFoundError(f'Missing browser fixture content: {content_root}')

    with manifest_path.open('rb') as manifest_file:
        manifest = tomllib.load(manifest_file)
    if manifest.get('name') != case_name:
        raise ValueError(f'Browser fixture name must be {case_name!r}')
    env = manifest.get('env')
    valid_env = isinstance(env, dict) and all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in env.items()
    )
    if not valid_env:
        raise ValueError('Browser fixture manifest must contain an [env] table of strings')
    return BrowserFixture(case_name, root, content_root, dict(env))


def resolve_bundle_source(configured_source: str) -> str | Path:
    parsed = urlparse(configured_source)
    if parsed.scheme in {'http', 'https'}:
        return configured_source
    path = Path(configured_source)
    if not path.is_absolute():
        path = runner.ROOT / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(
            f'Decap CMS bundle path is missing: {path}\n'
            'Run npm install from the e2e_tests root or pass --decap-bundle.'
        )
    return path


def install_test_bundle(build_dir: Path, configured_source: str) -> None:
    index_path = build_dir / 'admin' / 'index.html'
    html = index_path.read_text(encoding='utf-8')
    if html.count(PRODUCTION_DECAP_SCRIPT_PATH) != 1:
        raise RuntimeError(
            'Generated admin/index.html did not contain exactly one expected '
            f'Decap runtime path: {PRODUCTION_DECAP_SCRIPT_PATH}'
        )

    source = resolve_bundle_source(configured_source)
    if isinstance(source, Path):
        if source.is_dir():
            source_bundle = source / 'decap-cms.js'
            if not source_bundle.is_file():
                raise FileNotFoundError(
                    f'Decap CMS bundle directory has no decap-cms.js: {source}'
                )
            for asset in source.iterdir():
                if asset.is_file() and asset.suffix != '.map':
                    shutil.copy2(asset, index_path.parent / asset.name)
        else:
            shutil.copy2(source, index_path.parent / 'decap-cms.js')
        browser_source = '/admin/decap-cms.js'
    else:
        browser_source = source
    index_path.write_text(html.replace(PRODUCTION_DECAP_SCRIPT_PATH, browser_source), encoding='utf-8')


def resolve_decap_server_command() -> list[str]:
    if not DECAP_SERVER_PACKAGE.is_file():
        raise FileNotFoundError(
            f'Decap server package is missing: {DECAP_SERVER_PACKAGE}\n'
            'Run npm install from the e2e_tests root.'
        )
    package = json.loads(DECAP_SERVER_PACKAGE.read_text(encoding='utf-8'))
    bin_config = package.get('bin')
    if isinstance(bin_config, str):
        relative_entry = bin_config
    elif isinstance(bin_config, dict) and isinstance(bin_config.get('decap-server'), str):
        relative_entry = bin_config['decap-server']
    else:
        raise RuntimeError('The installed decap-server package does not declare a decap-server executable.')
    node = shutil.which('node')
    if node is None:
        raise FileNotFoundError('Node.js is required to run Decap browser tests.')
    entry = (DECAP_SERVER_PACKAGE.parent / relative_entry).resolve()
    return [node, str(entry)]


def wait_for_port(port: int, process: subprocess.Popen, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f'Decap server exited before opening port {port}.')
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.25):
                return
        except OSError:
            time.sleep(0.1)
    raise TimeoutError(f'Decap server did not open port {port} within {timeout:g} seconds.')


def require_available_port(port: int) -> None:
    try:
        with socket.create_connection(('localhost', port), timeout=0.25):
            pass
    except OSError:
        pass
    else:
        raise RuntimeError(
            f'Port {port} is already in use. Stop the existing Decap proxy before running browser tests.'
        )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(('127.0.0.1', port))
        except OSError as error:
            raise RuntimeError(
                f'Port {port} is already in use. Stop the existing Decap proxy before running browser tests.'
            ) from error


class QuietRequestHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        '.yml': 'application/yaml',
        '.yaml': 'application/yaml',
    }

    def log_message(self, format: str, *args) -> None:
        pass


class StaticSiteServer:
    def __init__(self, root: Path):
        handler = partial(QuietRequestHandler, directory=str(root))
        self._server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        host, port = self._server.server_address
        return f'http://{host}:{port}'

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


class CmsBrowserHarness:
    def __init__(self, fixture: BrowserFixture, options: BrowserHarnessOptions):
        self.fixture = fixture
        self.options = options
        self.workspace: Path | None = None
        self.build_dir: Path | None = None
        self.static_server: StaticSiteServer | None = None
        self.decap_process: subprocess.Popen | None = None
        self.decap_log_path: Path | None = None
        self._decap_log = None
        self._temp_workspace = runner.TempWorkspace(options.keep_temp)

    @property
    def admin_url(self) -> str:
        if self.static_server is None:
            raise RuntimeError('Browser harness has not started.')
        return f'{self.static_server.url}/admin/'

    @property
    def source_root(self) -> Path:
        if self.workspace is None:
            raise RuntimeError('Browser harness has not started.')
        return self.workspace / 'your_content'

    def __enter__(self) -> 'CmsBrowserHarness':
        self.workspace = self._temp_workspace.__enter__()
        try:
            runner.stage_test_case_content(self.workspace, self.fixture.content_root)
            runner.create_engine_junction(self.workspace, runner.resolve_engine_target())
            self.build_dir = runner.build_site(
                self.workspace,
                self.fixture.env,
                self.options.python_executable,
                cms_local_backend=True,
            )
            if self.options.bundle_source is not None:
                install_test_bundle(self.build_dir, self.options.bundle_source)

            self.static_server = StaticSiteServer(self.build_dir)
            self.static_server.start()
            require_available_port(DECAP_PROXY_PORT)
            self.decap_log_path = self.workspace / 'decap-server.log'
            self._decap_log = self.decap_log_path.open('w', encoding='utf-8')
            self.decap_process = subprocess.Popen(
                resolve_decap_server_command(),
                cwd=self.workspace,
                stdout=self._decap_log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            wait_for_port(DECAP_PROXY_PORT, self.decap_process)
            return self
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise

    def rebuild(self) -> Path:
        if self.workspace is None:
            raise RuntimeError('Browser harness has not started.')
        self.build_dir = runner.build_site(
            self.workspace,
            self.fixture.env,
            self.options.python_executable,
            cms_local_backend=True,
        )
        if self.options.bundle_source is not None:
            install_test_bundle(self.build_dir, self.options.bundle_source)
        return self.build_dir

    def capture_artifacts(self, test_name: str, page, console_messages: list[str]) -> Path:
        safe_name = ''.join(
            character if character.isalnum() or character in '-_' else '_'
            for character in test_name
        )
        artifact_dir = ARTIFACTS_ROOT / safe_name
        if artifact_dir.exists():
            shutil.rmtree(artifact_dir)
        artifact_dir.mkdir(parents=True)
        page.screenshot(path=artifact_dir / 'page.png', full_page=True)
        (artifact_dir / 'page.html').write_text(page.content(), encoding='utf-8')
        (artifact_dir / 'console.log').write_text('\n'.join(console_messages), encoding='utf-8')
        source_files = sorted(
            path.relative_to(self.source_root).as_posix()
            for path in self.source_root.rglob('*')
            if path.is_file()
        )
        (artifact_dir / 'source-tree.txt').write_text('\n'.join(source_files), encoding='utf-8')
        artifact_source = artifact_dir / 'source'
        for source_path in self.source_root.rglob('*'):
            if source_path.is_file() and source_path.suffix.lower() in runner.TEXT_FILE_SUFFIXES:
                target_path = artifact_source / source_path.relative_to(self.source_root)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
        if self.decap_log_path is not None and self.decap_log_path.exists():
            if self._decap_log is not None:
                self._decap_log.flush()
            shutil.copy2(self.decap_log_path, artifact_dir / 'decap-server.log')
        if self.workspace is not None:
            (artifact_dir / 'workspace.txt').write_text(str(self.workspace), encoding='utf-8')
        return artifact_dir

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.decap_process is not None and self.decap_process.poll() is None:
            self.decap_process.terminate()
            try:
                self.decap_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.decap_process.kill()
                self.decap_process.wait(timeout=5)
        if self._decap_log is not None:
            self._decap_log.close()
        if self.static_server is not None:
            self.static_server.stop()
        self._temp_workspace.__exit__(exc_type, exc, tb)
