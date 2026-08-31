from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


JsonDocumentLoader = Callable[[Path], dict]


def test_every_page_metadata_document_validates_against_its_deployed_schema(
    golden_builds_root: Path,
    load_json_document: JsonDocumentLoader,
) -> None:
    documents = sorted(golden_builds_root.glob("*/**/comic/page_info_list.json"))
    assert documents

    for document_path in documents:
        case_root = next(
            parent for parent in document_path.parents if parent.parent == golden_builds_root
        )
        schema_path = case_root / "comic_git_engine" / "schemas" / "page_info_list.schema.json"
        assert schema_path.is_file(), f"missing deployed schema for {document_path}"
        validator = Draft202012Validator(
            load_json_document(schema_path),
            format_checker=FormatChecker(),
        )
        errors = sorted(
            validator.iter_errors(load_json_document(document_path)),
            key=lambda error: list(error.path),
        )
        assert not errors, f"{document_path}: {errors}"


def test_structured_metadata_preserves_resolution_and_public_image_shape(
    structured_build: Path,
    load_json_document: JsonDocumentLoader,
) -> None:
    main = load_json_document(structured_build / "comic" / "page_info_list.json")
    side = load_json_document(
        structured_build / "side-story" / "comic" / "page_info_list.json"
    )

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
    assert flat["images"][1]["thumbnail_url"].endswith(".jpg")

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
    public_image_fields = {"filename", "url", "title", "alt_text", "thumbnail_url"}
    assert all(
        set(image) == public_image_fields
        for page in [*main["pages"], *side["pages"]]
        for image in page["images"]
    )
    assert main_shared["filename"] == side_shared["filename"] == "shared.png"
    assert main_shared["url"] != side_shared["url"]
    assert "!Configured secret" not in json.dumps(main)
    assert "!Private TOML note" not in json.dumps(main)


def test_existing_cases_use_the_minimal_versioned_metadata_contract(
    golden_builds_root: Path,
    load_json_document: JsonDocumentLoader,
) -> None:
    baseline = load_json_document(
        golden_builds_root / "baseline" / "comic" / "page_info_list.json"
    )
    publishing = load_json_document(
        golden_builds_root / "publishing-filtering" / "comic" / "page_info_list.json"
    )

    assert baseline["schema_version"] == 1
    baseline_multi_image = baseline["pages"][2]
    assert [image["filename"] for image in baseline_multi_image["images"]] == [
        "panel-b.png",
        "panel-a.png",
    ]
    assert all(
        "id" not in image and "anchor_id" not in image
        for image in baseline_multi_image["images"]
    )

    assert [page["page_name"] for page in publishing["pages"]] == ["001", "002"]
    assert [image["filename"] for image in publishing["pages"][1]["images"]] == [
        "alpha.png",
        "beta.png",
    ]
    assert "_hidden.png" not in json.dumps(publishing)
    assert "!Private reviewer note" not in json.dumps(publishing)
