"""The served API must expose every route + method in the design contract (docs/openapi.yaml)."""

import re
from pathlib import Path

import yaml

from app.main import app

DESIGN = Path(__file__).resolve().parents[2] / "docs" / "openapi.yaml"
METHODS = {"get", "post", "put", "patch", "delete"}


def _snake_path(p: str) -> str:
    # Design uses {lessonId}; FastAPI uses {lesson_id}.
    return re.sub(r"\{(\w+)\}", lambda m: "{" + re.sub(r"([A-Z])", r"_\1", m[1]).lower() + "}", p)


def test_every_design_route_is_served():
    design = yaml.safe_load(DESIGN.read_text())
    served = app.openapi()["paths"]
    missing = [
        f"{m.upper()} /api{path}"
        for path, ops in design["paths"].items()
        for m in ops
        if m in METHODS and m not in served.get("/api" + _snake_path(path), {})
    ]
    assert missing == []


def test_quiz_payloads_hide_answer_keys():
    schemas = app.openapi()["components"]["schemas"]
    item = schemas["AttemptItemOut"]["properties"]
    assert "correctChoice" not in item and "explanation" not in item and "quote" not in item
