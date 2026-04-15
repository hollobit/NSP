"""pytest configuration — make src/parser/ importable and provide shared fixtures."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "parser"))

PROCESSED = ROOT / "data" / "processed"


@pytest.fixture(scope="session")
def projects_data() -> dict:
    """Load projects.v1.json once per session."""
    path = PROCESSED / "projects.v1.json"
    if not path.exists():
        pytest.skip("projects.v1.json not found — run parser first")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def tech_taxonomy() -> list[dict]:
    """Load tech_categories.v1.json once per session."""
    path = PROCESSED / "tech_categories.v1.json"
    if not path.exists():
        pytest.skip("tech_categories.v1.json not found — run parser first")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("categories") or data.get("tech_categories") or data
