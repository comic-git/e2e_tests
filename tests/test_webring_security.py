"""Real CLI tests spanning config, untrusted JSON, templates and generated files."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

import pytest

from e2e_harness import runner

CASE = runner.ROOT / "test_cases/security/webring"


@pytest.fixture
def host(tmp_path):
    runner.stage_test_case_content(tmp_path, CASE / "your_content")
    for folder in ["src", "templates", "css", "js", "schemas"]:
        shutil.copytree(runner.resolve_engine_target() / folder, tmp_path / "comic_git_engine" / folder,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return tmp_path


def build(host):
    env = {k: v for k, v in os.environ.items() if k not in {"INPUTS", "SECRETS", "OUTPUT_DIR"}}
    env.update(tomllib.loads((CASE / "manifest.toml").read_text())["env"])
    return subprocess.run([sys.executable, str(host / "comic_git_engine/src/build/build_site.py")],
                          cwd=host, env=env, text=True, capture_output=True, timeout=30)


@pytest.mark.parametrize("mode", ["text", "markdown", "unsafe_html"])
@pytest.mark.parametrize("all_members", [True, False])
def test_modes_render_through_real_build(host, mode, all_members):
    config = host / "your_content/comic_info.toml"
    config.write_text(config.read_text().replace('text_mode = "text"', f'text_mode = "{mode}"')
                      .replace('show_all_members = true', f'show_all_members = {str(all_members).lower()}'))
    result = build(host)
    assert result.returncode == 0, result.stdout + result.stderr
    html = (host / "build/index.html").read_text(encoding="utf-8")
    assert '<strong>Trusted home formatting</strong>' in html
    assert ('<script>review_marker()</script>' in html) == (mode == "unsafe_html")
    assert ('<strong>Ring</strong>' in html) == (mode == "markdown")
    assert ('&lt;script&gt;' in html) == (mode == "text")
    assert 'title="" onerror=' not in html
    assert ('unsafe_html is enabled' in result.stdout + result.stderr) == (mode == "unsafe_html")
    assert (host / "build/tagged/Normal tag/index.html").exists()


@pytest.mark.parametrize("omit", [False, True])
def test_bad_json_failure_policy(host, omit):
    (host / "your_content/webring.json").write_text("invalid JSON")
    if omit:
        config = host / "your_content/comic_info.toml"
        config.write_text(config.read_text().replace('on_error = "abort"', 'on_error = "omit"'))
    result = build(host)
    if omit:
        assert result.returncode == 0, result.stdout + result.stderr
        assert 'Webring omitted' in result.stdout + result.stderr
        assert '<nav class="webring">' not in (host / "build/index.html").read_text()
    else:
        assert result.returncode != 0
        assert "Couldn't load webring" in result.stdout + result.stderr


def test_tag_escape_fails_without_overwriting_outside_output(host):
    outside = host / "outside/index.html"
    outside.parent.mkdir()
    outside.write_text("original")
    page = host / "your_content/comics/001/info.toml"
    page.write_text(page.read_text().replace('Normal tag', '../../outside'))
    result = build(host)
    assert result.returncode != 0
    assert 'Invalid tag or character name' in result.stdout + result.stderr
    assert 'info.toml' in result.stdout + result.stderr
    assert outside.read_text() == "original"
