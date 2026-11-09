"""Cross-output publication contracts exercised through the public build CLI."""
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from jsonschema import Draft202012Validator, FormatChecker
from PIL import Image
import pytest

from e2e_harness import runner

CASE = runner.ROOT / 'test_cases/build/selective-staging'
MOUNT = '/selective-staging/'
COMICS = ('', 'extras/story/', 'extras/story/bonus/')


@pytest.fixture
def host(tmp_path):
    runner.stage_test_case_content(tmp_path, CASE / 'your_content')
    for folder in ('src', 'templates', 'css', 'js', 'schemas'):
        shutil.copytree(runner.resolve_engine_target() / folder, tmp_path / 'comic_git_engine' / folder,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    return tmp_path


def build(host, *arguments, succeeds=True):
    env = {key: value for key, value in os.environ.items()
           if key not in ('INPUTS', 'SECRETS', 'OUTPUT_DIR', 'GITHUB_REPOSITORY', 'PYTHONPATH')}
    result = subprocess.run([sys.executable, '-B', str(host / 'comic_git_engine/src/build/build_site.py'),
                             *arguments], cwd=host, env=env, text=True, capture_output=True, timeout=45)
    if succeeds:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode != 0, result.stdout + result.stderr
    return result


def snapshot(content):
    return {path.relative_to(content): path.read_bytes() for path in content.rglob('*') if path.is_file()}


def site_path(output, url):
    path = unquote(urlsplit(url).path)
    assert path.startswith(MOUNT), url
    return output / path[len(MOUNT):]


class ComicLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == 'href' and value and value.startswith(MOUNT) and '/comic/' in value:
                self.links.append(value)


def assert_publication_contract(host, *, publish_all):
    output = host / 'build'
    schema = json.loads((output / 'comic_git_engine/schemas/page_info_list.schema.json').read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    expected_links = set()
    expected_thumbnails = set()
    for comic in COMICS:
        document = json.loads((output / comic / 'comic/page_info_list.json').read_text())
        validator.validate(document)
        names = {'001', 'future'} if publish_all else {'001'}
        if not comic:
            names.add('text')
        assert {page['page_name'] for page in document['pages']} == names
        assert document['scheduled_post_count'] == (0 if publish_all else 1)
        assert len(document['pages']) == len(names)
        source_root = host / 'your_content' / comic / 'comics'
        asset_root = output / 'your_content' / comic / 'comics'
        assert {p.name for p in asset_root.iterdir() if p.is_dir()} == names
        assert not (asset_root / 'loose.txt').exists()
        assert (source_root / 'future').is_dir()
        for page in document['pages']:
            page_output = site_path(output, page['url']) / 'index.html'
            assert page_output.is_file()
            expected_links.add('https://example.test' + page['url'])
            html = page_output.read_text(encoding='utf-8')
            parsed = ComicLinks()
            parsed.feed(html)
            for link in parsed.links:
                assert (site_path(output, link) / 'index.html').is_file(), link
            if page['page_name'] == 'text':
                assert page['images'] == []
                assert page['thumbnail_url'] is None
            for image in page['images']:
                assert site_path(output, image['url']).is_file()
                assert image['url'] in html
                assert image['thumbnail_url'] == page['thumbnail_url']
            if page['thumbnail_url']:
                thumbnail = site_path(output, page['thumbnail_url'])
                expected_thumbnails.add(thumbnail.relative_to(output / 'your_content'))
                assert thumbnail.read_bytes() == (host / 'your_content' / thumbnail.relative_to(output / 'your_content')).read_bytes()
                with Image.open(thumbnail) as image:
                    assert image.size == (20, 10)
    items = ElementTree.parse(output / 'feed.xml').findall('./channel/item')
    assert len(items) == len(expected_links)
    assert {item.findtext('link') for item in items} == expected_links
    assert len({item.findtext('guid') for item in items}) == len(items)
    assert (output / 'your_content/assets/shared.txt').is_file()
    for comic in COMICS[1:]:
        assert (output / 'your_content' / comic / 'cover.txt').is_file()
    assert (output / 'marker.txt').read_text().strip() == 'Selective staging root marker.'
    return expected_thumbnails


@pytest.mark.parametrize('publish_all', [False, True])
def test_selected_pages_agree_across_json_html_rss_assets_and_source_cache(host, publish_all):
    content = host / 'your_content'
    before = snapshot(content)
    build(host, '--delete-scheduled-posts', *(['--publish-all-comics'] if publish_all else []))
    thumbnails = assert_publication_contract(host, publish_all=publish_all)
    after = snapshot(content)
    assert set(after) == set(before) | thumbnails
    assert all(after[name] == data for name, data in before.items())
    for hidden in ('your_content/.private', 'your_content/comics/001/.notes',
                   'your_content/assets/.shared', '.htaccess', '.hook-private'):
        assert not (host / 'build' / hidden).exists()
    cache_times = {name: (content / name).stat().st_mtime_ns for name in thumbnails}
    build(host, *(['--publish-all-comics'] if publish_all else []))
    assert {name: (content / name).stat().st_mtime_ns for name in thumbnails} == cache_times


def test_include_all_and_explicit_allowlist_filter_root_assets_pages_and_hook_output(host):
    config = host / 'your_content/comic_info.ini'
    config.write_text(config.read_text().replace('Include hidden files = false', 'Include hidden files = true'))
    build(host)
    assert_publication_contract(host, publish_all=False)
    for name in ('your_content/.private', 'your_content/comics/001/.notes',
                 'your_content/assets/.shared/public.txt', '.htaccess', '.hook-private'):
        assert (host / 'build' / name).is_file()
    config.write_text(config.read_text().replace('[Build]', '[Build]\nHidden paths = your_content/.private'))
    build(host, '--hidden-paths', '.htaccess\nyour_content/comics/001/.notes\nyour_content/assets/.shared/public.txt')
    assert_publication_contract(host, publish_all=False)
    for name in ('.htaccess', 'your_content/comics/001/.notes', 'your_content/assets/.shared/public.txt'):
        assert (host / 'build' / name).is_file()
    for name in ('your_content/.private', '.hook-private', 'your_content/site_root/.htaccess'):
        assert not (host / 'build' / name).exists()


def test_rescheduling_removes_stale_html_rss_metadata_and_assets_without_source_deletion(host):
    config = host / 'your_content/comics/future/info.ini'
    original = config.read_text()
    config.write_text(original.replace('2099-01-01', '2020-01-03'))
    build(host)
    assert (host / 'build/comic/future/index.html').is_file()
    assert 'Main Future' in (host / 'build/feed.xml').read_text()
    assert (host / 'your_content/comics/future/_thumbnail.jpg').is_file()
    config.write_text(original)
    build(host)
    assert_publication_contract(host, publish_all=False)
    assert not (host / 'build/comic/future').exists()
    assert not (host / 'build/your_content/comics/future').exists()
    assert 'Main Future' not in (host / 'build/feed.xml').read_text()
    assert (host / 'your_content/comics/future/_thumbnail.jpg').is_file()


@pytest.mark.parametrize('folder,filename,value,diagnostic', [
    ('comics/incomplete', 'info.ini', 'Post date = invalid\n', 'post date'),
    ('extras/story/comics/incomplete', 'info.toml', 'title = 17\n', "Expected 'title'"),
])
def test_malformed_values_fail_instead_of_being_treated_as_incomplete(host, folder, filename, value, diagnostic):
    source = host / 'your_content' / folder / filename
    source.write_text(value)
    original = snapshot(host / 'your_content')
    result = build(host, succeeds=False)
    assert diagnostic in result.stderr
    assert all((host / 'your_content' / name).read_bytes() == data for name, data in original.items())


def test_source_thumbnail_overwrite_is_copied_to_published_output(host):
    cached = host / 'your_content/comics/001/_thumbnail.jpg'
    Image.new('RGB', (7, 7), 'blue').save(cached)
    old = cached.read_bytes()
    build(host)
    assert cached.read_bytes() == old
    assert (host / 'build/your_content/comics/001/_thumbnail.jpg').read_bytes() == old
    config = host / 'your_content/comic_info.ini'
    config.write_text(config.read_text().replace('Overwrite existing images = false', 'Overwrite existing images = true'))
    build(host)
    assert cached.read_bytes() != old
    assert_publication_contract(host, publish_all=False)


@pytest.mark.parametrize('newline', ['\n', '\r\n'], ids=['LF', 'CRLF'])
@pytest.mark.parametrize('first_path_inline', [True, False], ids=['inline-first', 'all-indented'])
def test_ini_multiline_hidden_paths_controls_real_build_without_cli_override(host, newline, first_path_inline):
    config = host / 'your_content/comic_info.ini'
    paths = ['.htaccess', 'your_content/comics/001/.notes', 'your_content/assets/.shared/public.txt']
    if first_path_inline:
        option = 'Hidden paths = ' + paths[0] + '\n' + '\n'.join('    ' + path for path in paths[1:])
    else:
        option = 'Hidden paths =\n' + '\n'.join('    ' + path for path in paths)
    text = config.read_text().replace('Include hidden files = false',
                                      'Include hidden files = true\n' + option)
    config.write_bytes(text.replace('\n', newline).encode('utf-8'))
    # No --hidden-paths argument: exercise the public INI loader and config policy.
    build(host)
    assert_publication_contract(host, publish_all=False)
    for path in paths:
        assert (host / 'build' / path).is_file(), path
    for path in ['your_content/.private', '.hook-private', 'your_content/site_root/.htaccess']:
        assert not (host / 'build' / path).exists(), path
