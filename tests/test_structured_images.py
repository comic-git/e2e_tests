from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_BUILDS = ROOT / "golden_builds"
STRUCTURED_BUILD = GOLDEN_BUILDS / "structured-images"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def image_anchor(image_id: str) -> str:
    return f"comic-image-{hashlib.sha256(image_id.encode('utf-8')).hexdigest()}"


def test_every_generated_page_metadata_document_validates_against_deployed_schema() -> None:
    documents = sorted(GOLDEN_BUILDS.glob("*/**/comic/page_info_list.json"))
    assert documents

    for document_path in documents:
        case_root = next(parent for parent in document_path.parents if parent.parent == GOLDEN_BUILDS)
        schema_path = case_root / "comic_git_engine" / "schemas" / "page_info_list.schema.json"
        assert schema_path.is_file(), f"missing deployed schema for {document_path}"
        validator = Draft202012Validator(load_json(schema_path), format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(load_json(document_path)), key=lambda error: list(error.path))
        assert not errors, f"{document_path}: {errors}"


def test_structured_metadata_preserves_resolution_order_and_collision_safe_identity() -> None:
    main = load_json(STRUCTURED_BUILD / "comic" / "page_info_list.json")
    side = load_json(STRUCTURED_BUILD / "side-story" / "comic" / "page_info_list.json")

    assert [page["page_name"] for page in main["pages"]] == ["001", "002", "003", "004"]
    assert main["comic"] == {"id": "main", "name": "Structured Images Fixture"}
    assert side["comic"] == {"id": "side-story", "name": "Structured Side Story"}

    flat, sectioned, no_image, toml = main["pages"]
    assert [image["filename"] for image in flat["images"]] == ["shared.png", "flat-second.png"]
    assert [image["title"] for image in flat["images"]] == ["Flat Legacy Page", "Flat Legacy Page"]
    assert [image["alt_text"] for image in flat["images"]] == [
        "Flat page inherited alt text.",
        "Flat page inherited alt text.",
    ]
    assert flat["thumbnail_url"].endswith("/custom-page-thumb.png")
    assert flat["images"][0]["thumbnail_url"] == flat["thumbnail_url"]
    assert flat["images"][1]["thumbnail_url"].endswith(
        f"/_thumbnail_{hashlib.sha256(flat['images'][1]['id'].encode()).hexdigest()}.jpg"
    )

    assert [image["filename"] for image in sectioned["images"]] == ["ordered-b.png", "ordered-a.png"]
    assert sectioned["thumbnail_url"].endswith("/_thumbnail.jpg")
    assert sectioned["images"][0]["title"] == ""
    assert sectioned["images"][0]["alt_text"] == ""
    assert sectioned["images"][0]["thumbnail_url"] is None
    assert sectioned["images"][1]["title"] == "Sectioned Legacy Page"
    assert sectioned["images"][1]["alt_text"] == "Sectioned page inherited alt text."

    assert no_image["images"] == []
    assert no_image["thumbnail_url"] is None
    assert toml["images"][0]["thumbnail_url"].endswith("/toml-image-thumb.png")
    assert toml["images"][1]["title"] == "Native TOML Page"
    assert toml["images"][1]["alt_text"] == "TOML page inherited alt text."
    assert toml["extra"] == {"Review": "public custom metadata"}

    main_shared = flat["images"][0]
    side_shared = side["pages"][0]["images"][0]
    assert main_shared["id"] == "main/001/shared.png"
    assert side_shared["id"] == "side-story/001/shared.png"
    assert main_shared["anchor_id"] == image_anchor(main_shared["id"])
    assert side_shared["anchor_id"] == image_anchor(side_shared["id"])
    assert main_shared["anchor_id"] != side_shared["anchor_id"]
    assert "!Configured secret" not in json.dumps(main)
    assert "!Private TOML note" not in json.dumps(main)


def test_existing_cases_expose_the_versioned_structured_metadata_contract() -> None:
    baseline = load_json(GOLDEN_BUILDS / "baseline" / "comic" / "page_info_list.json")
    publishing = load_json(
        GOLDEN_BUILDS / "publishing-filtering" / "comic" / "page_info_list.json"
    )

    assert baseline["schema_version"] == 1
    baseline_multi_image = baseline["pages"][2]
    assert [image["filename"] for image in baseline_multi_image["images"]] == [
        "panel-b.png",
        "panel-a.png",
    ]
    assert all(
        image["anchor_id"] == image_anchor(image["id"])
        for image in baseline_multi_image["images"]
    )

    assert [page["page_name"] for page in publishing["pages"]] == ["001", "002"]
    assert [image["filename"] for image in publishing["pages"][1]["images"]] == [
        "alpha.png",
        "beta.png",
    ]
    assert "_hidden.png" not in json.dumps(publishing)
    assert "!Private reviewer note" not in json.dumps(publishing)


def test_structured_archives_render_image_and_page_entry_modes() -> None:
    main = load_json(STRUCTURED_BUILD / "comic" / "page_info_list.json")
    side = load_json(STRUCTURED_BUILD / "side-story" / "comic" / "page_info_list.json")
    main_archive = (STRUCTURED_BUILD / "archive" / "index.html").read_text(encoding="utf-8")
    side_archive = (STRUCTURED_BUILD / "side-story" / "archive" / "index.html").read_text(encoding="utf-8")

    expected_main_links = [
        f'{page["url"]}#{image["anchor_id"]}'
        for page in main["pages"]
        for image in page["images"]
    ]
    expected_main_links.insert(4, main["pages"][2]["url"])
    actual_main_links = re.findall(r'<a href="([^"]+/comic/[^"]+)">', main_archive)
    assert actual_main_links == expected_main_links
    assert "Text Only Interlude" in main_archive
    assert "archive-thumbnail-page" in main_archive
    assert f'<img src="{main["pages"][0]["thumbnail_url"]}" alt="">' in main_archive

    assert re.findall(r'<a href="([^"]+/comic/[^"]+)">', side_archive) == [
        "/structured-images/side-story/comic/001/"
    ]
    assert "archive-thumbnail-page" in side_archive
    assert f'<img src="{side["pages"][0]["thumbnail_url"]}" alt="">' in side_archive


def test_structured_html_infinite_scroll_rss_and_social_values_agree() -> None:
    main = load_json(STRUCTURED_BUILD / "comic" / "page_info_list.json")
    comic_html = (STRUCTURED_BUILD / "comic" / "002" / "index.html").read_text(encoding="utf-8")
    infinite_scroll_js = (
        STRUCTURED_BUILD / "comic_git_engine" / "js" / "infinite_scroll.js"
    ).read_text(encoding="utf-8")

    for image in main["pages"][1]["images"]:
        assert f'id="{image["anchor_id"]}"' in comic_html
        assert f'src="{image["url"]}" alt="{image["alt_text"]}"' in comic_html
    for field in ('page["url"]', 'image["anchor_id"]', 'image["url"]', 'image["alt_text"]'):
        assert field in infinite_scroll_js

    feed = ET.parse(STRUCTURED_BUILD / "feed.xml").getroot()
    side_feed = ET.parse(STRUCTURED_BUILD / "side-story" / "feed.xml").getroot()
    items = feed.findall("./channel/item")
    assert len(items) == 4
    assert len(side_feed.findall("./channel/item")) == 1
    assert "ordered-b.png" in (items[1].findtext("description") or "")
    assert 'alt=""' in (items[1].findtext("description") or "")
    assert "This no-image page remains visible" in (items[2].findtext("description") or "")
    assert (items[3].findtext("description") or "").index("toml-first.png") < (
        items[3].findtext("description") or ""
    ).index("toml-second.png")

    page_html = (STRUCTURED_BUILD / "comic" / "001" / "index.html").read_text(encoding="utf-8")
    assert "your_content/comics/001/custom-page-thumb.png" in page_html
    assert 'property="og:image:alt" content="Flat page inherited alt text."' in page_html


def test_social_media_no_thumbnail_page_uses_site_preview_image() -> None:
    page_html = (
        GOLDEN_BUILDS / "social-media" / "comic" / "003" / "index.html"
    ).read_text(encoding="utf-8")
    assert (
        'property="og:image" '
        'content="https://comic-git.github.io/social-media/your_content/images/preview_image.png"'
    ) in page_html
