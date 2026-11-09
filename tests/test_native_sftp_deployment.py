"""Exercise the public native deploy command against a disposable SFTP server."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import PurePosixPath
import os
import posixpath
import socket
import subprocess
import sys
from threading import Event
import tomllib

import pytest

from e2e_harness.sftp import CASE, stage_host


@pytest.fixture
def sftp_endpoint(tmp_path):
    paramiko = pytest.importorskip("paramiko")
    server_root = tmp_path / "remote"
    site = server_root / "site"
    site.mkdir(parents=True)
    host_key = paramiko.RSAKey.generate(2048)

    class Login(paramiko.ServerInterface):
        def check_auth_password(self, username, password):
            if (username, password) == ("fixture", "local-only-password"):
                return paramiko.AUTH_SUCCESSFUL
            return paramiko.AUTH_FAILED

        def check_channel_request(self, kind, channel_id):
            return paramiko.OPEN_SUCCEEDED if kind == "session" else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    class Files(paramiko.SFTPServerInterface):
        def path(self, path):
            parts = PurePosixPath(path.lstrip("/")).parts
            assert ".." not in parts
            return server_root.joinpath(*parts)

        def canonicalize(self, path):
            return posixpath.normpath("/" + path.lstrip("/"))

        def stat(self, path):
            try:
                return paramiko.SFTPAttributes.from_stat(self.path(path).stat())
            except OSError as error:
                return paramiko.SFTPServer.convert_errno(error.errno)

        def lstat(self, path):
            try:
                return paramiko.SFTPAttributes.from_stat(self.path(path).lstat())
            except OSError as error:
                return paramiko.SFTPServer.convert_errno(error.errno)

        def list_folder(self, path):
            return [paramiko.SFTPAttributes.from_stat(entry.lstat(), entry.name)
                    for entry in self.path(path).iterdir()]

        def mkdir(self, path, attributes):
            self.path(path).mkdir()
            return paramiko.SFTP_OK

        def open(self, path, flags, attributes):
            handle = paramiko.SFTPHandle(flags)
            handle.writefile = os.fdopen(os.open(self.path(path), flags, 0o600), "wb")
            return handle

        def remove(self, path):
            self.path(path).unlink()
            return paramiko.SFTP_OK

    stop = Event()
    with socket.socket() as listener, ThreadPoolExecutor(max_workers=1) as pool:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        listener.settimeout(15)
        port = listener.getsockname()[1]

        def serve():
            connection, _ = listener.accept()
            with connection, paramiko.Transport(connection) as transport:
                transport.add_server_key(host_key)
                transport.set_subsystem_handler("sftp", paramiko.SFTPServer, Files)
                transport.start_server(server=Login())
                channel = transport.accept(10)
                stop.wait(30)
                if channel is not None:
                    channel.close()

        worker = pool.submit(serve)
        try:
            yield site, {
                "SFTP_PORT": str(port),
                "SFTP_USERNAME": "fixture",
                "SFTP_PASSWORD": "local-only-password",
                "SFTP_KNOWN_HOSTS": f"[localhost]:{port},[127.0.0.1]:{port} {host_key.get_name()} {host_key.get_base64()}",
            }
        finally:
            stop.set()
            worker.result(timeout=45)


@pytest.mark.parametrize("clean", [False, True])
def test_native_cli_builds_and_deploys_without_touching_working_files(tmp_path, sftp_endpoint, clean):
    site, endpoint = sftp_endpoint
    host = tmp_path / "comic checkout"
    stage_host(host)
    content = host / "your_content"
    cache = "themes/default/scripts/__pycache__/hooks.cpython-314.pyc"
    source_cache = content / cache
    source_cache.parent.mkdir(parents=True, exist_ok=True)
    source_cache.write_bytes(b"local fixture bytecode")
    original = {p.relative_to(content): p.read_bytes() for p in content.rglob("*") if p.is_file()}
    preview = host / "build"
    preview.mkdir()
    (preview / "preview.txt").write_text("local preview", encoding="utf-8")
    (site / ".well-known").mkdir()
    (site / ".well-known/token").write_text("server-owned", encoding="utf-8")
    (site / "obsolete.txt").write_text("old", encoding="utf-8")
    expected_marker = (content / "site_root/marker.txt").read_bytes()
    old_marker = site / "marker.txt"
    old_marker.write_bytes(b"x" * len(expected_marker))
    os.utime(old_marker, (2000000000, 2000000000))

    manifest = tomllib.loads((CASE / "manifest.toml").read_text(encoding="utf-8"))
    env = {name: value for name, value in os.environ.items() if not name.startswith("SFTP_")}
    env.update(manifest["env"], **endpoint, SFTP_CLEAN=str(clean).lower(),
               SFTP_HIDDEN_PATHS=manifest["build"]["hidden_paths"])
    script = host / "comic_git_engine/src/scripts/deploy_sftp.py"
    result = subprocess.run([sys.executable, str(script)], cwd=host, env=env, text=True,
                            capture_output=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr

    assert (site / "index.html").is_file()
    assert (site / "comic/001/index.html").is_file()
    assert old_marker.read_bytes() == expected_marker
    assert (site / "obsolete.txt").exists() is not clean
    assert (site / ".well-known/token").read_text(encoding="utf-8") == "server-owned"
    assert (site / ".htaccess").is_file()
    assert (site / ".allowed/nested/value.txt").is_file()
    assert not (site / ".private").exists()
    assert not (site / ".hook-private").exists()
    assert not (site / "comic/future").exists()
    assert not (site / "your_content/comics/future").exists()
    assert not (site / "your_content" / cache).parent.exists()
    assert original == {p.relative_to(content): p.read_bytes() for p in content.rglob("*") if p.is_file()}
    assert (preview / "preview.txt").read_text(encoding="utf-8") == "local preview"


def test_native_cli_rejects_links_to_files_outside_content(tmp_path):
    pytest.importorskip("paramiko")
    host = tmp_path / "comic checkout"
    stage_host(host)
    external = tmp_path / "outside content"
    external.mkdir()
    private = external / "local-only.txt"
    private.write_text("local-only fixture", encoding="utf-8")
    link = host / "your_content" / "linked-assets"
    if sys.platform == "win32":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(external)], check=True)
    else:
        link.symlink_to(external, target_is_directory=True)

    try:
        manifest = tomllib.loads((CASE / "manifest.toml").read_text(encoding="utf-8"))
        env = {name: value for name, value in os.environ.items() if not name.startswith("SFTP_")}
        env.update(manifest["env"], SFTP_USERNAME="fixture", SFTP_PASSWORD="fixture",
                   SFTP_KNOWN_HOSTS="127.0.0.1 ssh-ed25519 fixture-key")
        script = host / "comic_git_engine/src/scripts/deploy_sftp.py"
        result = subprocess.run([sys.executable, str(script)], cwd=host, env=env, text=True,
                                capture_output=True, timeout=15)
        assert result.returncode != 0
        assert "points outside your_content" in result.stderr
        assert "linked-assets" in result.stderr
        assert "Uploading to" not in result.stdout
        assert private.read_text(encoding="utf-8") == "local-only fixture"
    finally:
        if link.is_junction():
            link.rmdir()
        else:
            link.unlink()
