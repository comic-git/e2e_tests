from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path


JsonDocumentLoader = Callable[[Path], dict]


def test_image_mode_archive_links_each_entry_to_its_primary_content(
    structured_build: Path,
    load_json_document: JsonDocumentLoader,
) -> None:
    main = load_json_document(structured_build / "comic" / "page_info_list.json")
    main_archive = (structured_build / "archive" / "index.html").read_text(encoding="utf-8")

    expected_links = []
    for page in main["pages"]:
        if page["images"]:
            expected_links.extend(
                f'{page["url"]}#comic-image-{image_index}'
                for image_index in range(1, len(page["images"]) + 1)
            )
        else:
            expected_links.append(f'{page["url"]}#post-body')

    actual_links = re.findall(r'<a href="([^"]+/comic/[^"]+)">', main_archive)
    assert actual_links == expected_links
    assert "Text Only Interlude" in main_archive
    assert "archive-thumbnail-page" in main_archive
    assert f'<img src="{main["pages"][0]["thumbnail_url"]}" alt="">' in main_archive


def test_page_mode_archive_links_each_page_to_its_primary_content(
    golden_builds_root: Path,
    load_json_document: JsonDocumentLoader,
) -> None:
    social_build = golden_builds_root / "social-media"
    pages = load_json_document(social_build / "comic" / "page_info_list.json")["pages"]
    archive = (social_build / "archive" / "index.html").read_text(encoding="utf-8")

    actual_links = re.findall(r'<a href="([^"]+/comic/[^"]+)">', archive)
    assert actual_links == [
        f'{pages[0]["url"]}#comic-image-1',
        f'{pages[1]["url"]}#comic-image-1',
        f'{pages[2]["url"]}#post-body',
    ]


def test_extra_comic_archive_uses_its_own_page_and_thumbnail_urls(
    structured_build: Path,
    load_json_document: JsonDocumentLoader,
) -> None:
    side = load_json_document(
        structured_build / "side-story" / "comic" / "page_info_list.json"
    )
    side_archive = (structured_build / "side-story" / "archive" / "index.html").read_text(
        encoding="utf-8"
    )

    assert re.findall(r'<a href="([^"]+/comic/[^"]+)">', side_archive) == [
        "/structured-images/side-story/comic/001/#comic-image-1"
    ]
    assert "archive-thumbnail-page" in side_archive
    assert f'<img src="{side["pages"][0]["thumbnail_url"]}" alt="">' in side_archive


def test_standalone_image_markup_agrees_with_public_metadata(
    structured_build: Path,
    load_json_document: JsonDocumentLoader,
) -> None:
    main = load_json_document(structured_build / "comic" / "page_info_list.json")
    comic_html = (structured_build / "comic" / "002" / "index.html").read_text(
        encoding="utf-8"
    )

    for image_index, image in enumerate(main["pages"][1]["images"], start=1):
        assert f'id="comic-image-{image_index}"' in comic_html
        assert f'src="{image["url"]}" alt="{image["alt_text"]}"' in comic_html
    assert 'class="comic-page"' in comic_html
    assert 'id="comic-page"' not in comic_html


def test_infinite_scroll_chapters_target_the_first_positional_image(
    structured_build: Path,
) -> None:
    infinite_scroll = (structured_build / "infinite_scroll" / "index.html").read_text(
        encoding="utf-8"
    )

    assert re.findall(r'class="button chapter-links" href="([^"]+)"', infinite_scroll) == [
        "#001_01"
    ]


def test_tagged_pages_link_to_complete_pages_without_content_fragments(
    golden_builds_root: Path,
) -> None:
    tagged_page = (
        golden_builds_root / "baseline" / "tagged" / "Alice" / "index.html"
    ).read_text(encoding="utf-8")

    comic_links = re.findall(r'<li><a href="([^"]+/comic/[^"]+)">', tagged_page)
    assert comic_links
    assert all("#" not in link for link in comic_links)
