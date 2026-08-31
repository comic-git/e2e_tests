from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest


JsonDocumentLoader = Callable[[Path], dict]


@pytest.fixture(scope="session")
def golden_builds_root() -> Path:
    return Path(__file__).resolve().parents[2] / "golden_builds"


@pytest.fixture(scope="session")
def structured_build(golden_builds_root: Path) -> Path:
    return golden_builds_root / "structured-images"


@pytest.fixture(scope="session")
def load_json_document() -> JsonDocumentLoader:
    def load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    return load
