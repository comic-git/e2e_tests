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


@pytest.mark.xfail(
    strict=True,
    reason='Decap 3.16.0 suffixes a fixed path filename instead of its slug placeholder.',
)
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
    reason='Decap 3.16.0 writes info-1.toml instead of reporting a title-derived slug collision.',
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
