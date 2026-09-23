from __future__ import annotations

import re
import time
import tomllib
from pathlib import Path

import pytest


pytestmark = pytest.mark.browser


def open_cms(session) -> None:
    page = session.page
    page.goto(session.harness.admin_url, wait_until='domcontentloaded')
    login = page.get_by_role('button', name=re.compile('login', re.IGNORECASE))
    login.wait_for(timeout=20_000)
    login.click()
    page.get_by_text('Main Comic Pages', exact=True).wait_for(timeout=20_000)


def open_main_collection(session) -> None:
    open_cms(session)
    session.page.get_by_text('Main Comic Pages', exact=True).click()
    session.page.get_by_role('link', name=re.compile('Same Title')).wait_for(timeout=20_000)


def publish_entry(page) -> None:
    page.get_by_role('button', name='Publish', exact=True).click()
    page.get_by_role('menuitem', name='Publish now', exact=True).click()


def create_page(session, title: str, post_date: str) -> None:
    open_main_collection(session)
    page = session.page
    page.get_by_role('link', name='Create entry of type Comic Page').click()
    page.get_by_label('Title', exact=True).fill(title)
    page.get_by_label('Post date', exact=True).fill(post_date)
    publish_entry(page)


def wait_for_toml_value(path: Path, key: str, expected: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            with path.open('rb') as source_file:
                if tomllib.load(source_file).get(key) == expected:
                    return
        time.sleep(0.1)
    raise AssertionError(f'{path} did not contain {key}={expected!r} within {timeout:g} seconds')


def wait_for_collision_result(page, result_paths: tuple[Path, ...], timeout: float = 10.0) -> None:
    collision_error = page.get_by_text(re.compile('already exists|collision', re.IGNORECASE))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if any(path.exists() for path in result_paths) or collision_error.is_visible():
            return
        time.sleep(0.1)
    raise AssertionError(f'No collision result appeared within {timeout:g} seconds')


def enable_reject_collision_policy(session) -> None:
    config_path = session.harness.build_dir / 'admin' / 'config.yml'
    config = config_path.read_text(encoding='utf-8')
    path_setting = '    path: "{{slug}}/info"\n'
    if path_setting not in config:
        raise AssertionError('Generated main collection path setting was not found')
    config_path.write_text(
        config.replace(
            path_setting,
            f'{path_setting}    slug_collision: "reject"\n',
            1,
        ),
        encoding='utf-8',
    )


def test_generated_admin_loads_main_comic_collection(cms_session) -> None:
    open_cms(cms_session)
    page = cms_session.page

    page.get_by_text('Main Comic Pages', exact=True).click()
    entry = page.get_by_role('link', name=re.compile('Same Title'))
    entry.wait_for(timeout=20_000)

    assert entry.is_visible()


def test_editing_title_preserves_page_folder_and_rebuilds(cms_session) -> None:
    open_main_collection(cms_session)
    page = cms_session.page
    page.get_by_role('link', name=re.compile('Same Title')).click()

    title = page.get_by_label('Title', exact=True)
    title.fill('Renamed Page')
    publish_entry(page)

    source_path = cms_session.harness.source_root / 'comics' / 'same-title' / 'info.toml'
    wait_for_toml_value(source_path, 'title', 'Renamed Page')
    assert not (cms_session.harness.source_root / 'comics' / 'renamed-page').exists()

    build_dir = cms_session.harness.rebuild()
    assert (build_dir / 'comic' / 'same-title' / 'index.html').is_file()


def test_supported_page_metadata_round_trips_without_losing_images(cms_session) -> None:
    open_main_collection(cms_session)
    page = cms_session.page
    page.get_by_role('link', name=re.compile('Same Title')).click()

    updated_post_text = 'The browser saved this representative CMS page.'
    page.locator('[aria-label="markdown field"] [role="textbox"]').first.fill(updated_post_text)
    publish_entry(page)

    source_path = cms_session.harness.source_root / 'comics' / 'same-title' / 'info.toml'
    wait_for_toml_value(source_path, 'post_text', updated_post_text)
    with source_path.open('rb') as source_file:
        source = tomllib.load(source_file)

    assert source['title'] == 'Same Title'
    assert source['post_date'] == '2026-09-01'
    assert source['alt_text'] == 'Page hover text'
    assert source['screen_reader_text'] == 'Page screen reader text'
    assert source['thumbnail'] == 'first.svg'
    assert source['storyline'] == 'Browser contract'
    assert source['characters'] == ['Alex', 'Bea']
    assert source['tags'] == ['contract', 'fixture']
    assert source['transcripts'] == {
        'English': 'Original English transcript.',
        'Spanish': 'Original Spanish transcript.',
    }
    assert source['social_media'] == {
        'og:title': 'Original social title',
        'twitter:card': 'summary',
    }
    assert source['images'] == [
        {
            'filename': 'first.svg',
            'title': 'First image',
            'alt_text': 'First image hover text',
            'screen_reader_text': 'First image screen reader text',
            'thumbnail': 'second.svg',
        },
        {
            'filename': 'second.svg',
            'title': 'Second image',
            'alt_text': 'Second image hover text',
            'screen_reader_text': 'Second image screen reader text',
        },
    ]

    build_dir = cms_session.harness.rebuild()
    assert (build_dir / 'comic' / 'same-title' / 'index.html').is_file()


def test_page_transcript_map_edits_and_round_trips_as_toml(cms_session) -> None:
    cms_session.page.add_init_script("localStorage.setItem('cms.md-mode', 'raw')")
    open_main_collection(cms_session)
    page = cms_session.page
    page.get_by_role('link', name=re.compile('Same Title')).click()
    remove_button = page.get_by_role('button', name='Remove transcript row 1')
    assert remove_button.bounding_box()['width'] <= 40
    assert page.get_by_role('group', name='Transcript text 1').get_by_text('Rich Text').is_visible()

    page.get_by_role('group', name='Transcript text 1').get_by_role('textbox').fill(
        'Updated English transcript.\nSecond line.'
    )
    page.get_by_role('button', name='Remove transcript row 2').click()
    page.get_by_role('button', name='Add transcript').click()
    page.get_by_label('Transcript language 2').fill('French')
    page.get_by_role('group', name='Transcript text 2').get_by_role('textbox').fill(
        'Texte de transcription.'
    )
    publish_entry(page)

    source_path = cms_session.harness.source_root / 'comics' / 'same-title' / 'info.toml'
    deadline = time.monotonic() + 10.0
    expected = {
        'English': 'Updated English transcript.\nSecond line.',
        'French': 'Texte de transcription.',
    }
    while time.monotonic() < deadline:
        if source_path.is_file():
            with source_path.open('rb') as source_file:
                source = tomllib.load(source_file)
            if source.get('transcripts') == expected:
                break
        time.sleep(0.1)
    else:
        raise AssertionError('CMS did not save the expected page transcript map')

    build_dir = cms_session.harness.rebuild()
    assert (build_dir / 'comic' / 'same-title' / 'index.html').is_file()


def test_page_transcript_rich_text_edits_round_trip_as_toml(cms_session) -> None:
    cms_session.page.add_init_script("localStorage.setItem('cms.md-mode', 'rich_text')")
    open_main_collection(cms_session)
    page = cms_session.page
    page.get_by_role('link', name=re.compile('Same Title')).click()

    page.get_by_role('group', name='Transcript text 1').get_by_role('textbox').fill(
        'A richly edited transcript.'
    )
    publish_entry(page)

    source_path = cms_session.harness.source_root / 'comics' / 'same-title' / 'info.toml'
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        with source_path.open('rb') as source_file:
            source = tomllib.load(source_file)
        if source.get('transcripts', {}).get('English') == 'A richly edited transcript.':
            break
        time.sleep(0.1)
    else:
        raise AssertionError('CMS did not save the rich-text transcript')


def test_page_social_media_map_edits_and_round_trips_as_toml(cms_session) -> None:
    cms_session.page.set_viewport_size({'width': 390, 'height': 844})
    open_main_collection(cms_session)
    page = cms_session.page
    page.get_by_role('link', name=re.compile('Same Title')).click()
    key_one = page.get_by_label('Social media key 1').bounding_box()
    key_two = page.get_by_label('Social media key 2').bounding_box()
    value_one = page.get_by_label('Social media value 1').bounding_box()
    grid = page.locator('.cg-metadata-grid').bounding_box()
    remove = page.get_by_role('button', name='Remove social media row 1').bounding_box()
    assert key_one['width'] == key_two['width']
    assert key_one['width'] < value_one['width']
    assert remove['x'] + remove['width'] <= grid['x'] + grid['width']

    page.get_by_label('Social media value 1').fill('Updated social title')
    page.get_by_role('button', name='Remove social media row 2').click()
    page.get_by_role('button', name='Add metadata').click()
    page.get_by_label('Social media key 2').fill('twitter:label1')
    page.get_by_label('Social media value 2').fill('A page-specific label')
    publish_entry(page)

    source_path = cms_session.harness.source_root / 'comics' / 'same-title' / 'info.toml'
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        if source_path.is_file():
            with source_path.open('rb') as source_file:
                source = tomllib.load(source_file)
            if source.get('social_media') == {
                'og:title': 'Updated social title',
                'twitter:label1': 'A page-specific label',
            }:
                break
        time.sleep(0.1)
    else:
        raise AssertionError('CMS did not save the expected page-level social media map')

    source_text = source_path.read_text(encoding='utf-8')
    assert '"og:title" = "Updated social title"' in source_text
    assert '"twitter:label1" = "A page-specific label"' in source_text

    build_dir = cms_session.harness.rebuild()
    assert (build_dir / 'comic' / 'same-title' / 'index.html').is_file()


def test_creating_unique_page_writes_canonical_source_and_rebuilds(cms_session) -> None:
    create_page(cms_session, 'Unique New Page', '2026-09-03')

    page_dir = cms_session.harness.source_root / 'comics' / 'unique-new-page'
    source_path = page_dir / 'info.toml'
    wait_for_toml_value(source_path, 'title', 'Unique New Page')
    assert [path.name for path in page_dir.iterdir()] == ['info.toml']

    build_dir = cms_session.harness.rebuild()
    assert (build_dir / 'comic' / 'unique-new-page' / 'index.html').is_file()


def test_new_page_collision_is_never_silently_accepted(cms_session) -> None:
    create_page(cms_session, 'Same Title', '2026-09-02')
    suffixed_source_path = (
        cms_session.harness.source_root
        / 'comics'
        / 'same-title-1'
        / 'info.toml'
    )
    duplicate_path = (
        cms_session.harness.source_root
        / 'comics'
        / 'same-title'
        / 'info-1.toml'
    )
    wait_for_collision_result(cms_session.page, (suffixed_source_path, duplicate_path))

    if duplicate_path.exists():
        with pytest.raises(RuntimeError, match='Engine build reported an error'):
            cms_session.harness.rebuild()
    elif suffixed_source_path.exists():
        build_dir = cms_session.harness.rebuild()
        assert (build_dir / 'comic' / 'same-title-1' / 'index.html').is_file()
    else:
        assert cms_session.page.get_by_text(
            re.compile('already exists|collision', re.IGNORECASE)
        ).is_visible()


@pytest.mark.parametrize(
    ('title', 'colliding_folder'),
    [('Same Title', 'same-title'), ('A & B', 'a-b')],
    ids=['exact-title', 'normalized-title'],
)
def test_path_aware_suffix_creates_a_sibling_page_bundle(
        cms_session,
        title: str,
        colliding_folder: str,
) -> None:
    create_page(cms_session, title, '2026-09-02')
    suffixed_folder = f'{colliding_folder}-1'
    source_path = cms_session.harness.source_root / 'comics' / suffixed_folder / 'info.toml'
    legacy_duplicate_path = (
        cms_session.harness.source_root
        / 'comics'
        / colliding_folder
        / 'info-1.toml'
    )

    wait_for_collision_result(cms_session.page, (source_path, legacy_duplicate_path))
    wait_for_toml_value(source_path, 'title', title)
    assert not legacy_duplicate_path.exists()

    build_dir = cms_session.harness.rebuild()
    assert (build_dir / 'comic' / suffixed_folder / 'index.html').is_file()


@pytest.mark.xfail(
    strict=True,
    reason='The vendored Decap runtime does not yet support the slug_collision: reject policy.',
)
@pytest.mark.parametrize(
    ('title', 'colliding_folder'),
    [('Same Title', 'same-title'), ('A & B', 'a-b')],
    ids=['exact-title', 'normalized-title'],
)
def test_new_page_title_collision_is_reported_without_writing_an_ignored_file(
        cms_session,
        title: str,
        colliding_folder: str,
) -> None:
    enable_reject_collision_policy(cms_session)
    create_page(cms_session, title, '2026-09-02')
    page = cms_session.page

    duplicate_path = (
        cms_session.harness.source_root
        / 'comics'
        / colliding_folder
        / 'info-1.toml'
    )
    wait_for_collision_result(page, (duplicate_path,))
    assert not duplicate_path.exists()
    assert page.get_by_text(re.compile('already exists|collision', re.IGNORECASE)).is_visible()
