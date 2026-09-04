from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def test_structured_feeds_preserve_page_scope_order_and_text_content(
    structured_build: Path,
) -> None:
    feed = ET.parse(structured_build / "feed.xml").getroot()
    side_feed = ET.parse(structured_build / "side-story" / "feed.xml").getroot()
    channel = feed.find("./channel")
    items = feed.findall("./channel/item")

    assert channel is not None
    assert channel.findtext("description") == "Structured image feed fixture."
    assert len(items) == 4
    assert len(side_feed.findall("./channel/item")) == 1
    assert "ordered-b.png" in (items[1].findtext("description") or "")
    assert 'alt=""' in (items[1].findtext("description") or "")
    assert "This no-image page remains visible" in (items[2].findtext("description") or "")
    assert (items[3].findtext("description") or "").index("toml-first.png") < (
        items[3].findtext("description") or ""
    ).index("toml-second.png")


def test_structured_social_metadata_uses_resolved_thumbnail_and_alt_text(
    structured_build: Path,
) -> None:
    page_html = (structured_build / "comic" / "001" / "index.html").read_text(
        encoding="utf-8"
    )

    assert "your_content/comics/001/custom-page-thumb.png" in page_html
    assert 'property="og:image:alt" content="Flat page inherited alt text."' in page_html


def test_text_only_page_social_metadata_uses_site_preview_image(
    golden_builds_root: Path,
) -> None:
    page_html = (
        golden_builds_root / "social-media" / "comic" / "003" / "index.html"
    ).read_text(encoding="utf-8")

    assert (
        'property="og:image" '
        'content="https://comic-git.github.io/social-media/your_content/images/preview_image.png"'
    ) in page_html
