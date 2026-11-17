import json
import re

from pydantic import Field, ValidationError

from app.schemas import Concept, PackQuestion, Schema


class ValidationFailed(Exception):
    """Generated output rejected. Message is a short machine reason, never lesson text."""


class GeneratedPack(Schema):
    guide: list[Concept] = Field(min_length=1)
    comparison: list[Concept] | None = None
    questions: list[PackQuestion] = Field(min_length=5, max_length=5)


_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)
_PUNCT = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def _norm(text: str) -> str:
    return " ".join(text.translate(_PUNCT).casefold().split())


def validate_output(raw: str, paragraphs: list[dict]) -> GeneratedPack:
    m = _FENCE.match(raw or "")
    text = m.group(1) if m else (raw or "")
    try:
        data = json.loads(text)
    except ValueError:
        raise ValidationFailed("bad_json") from None
    try:
        pack = GeneratedPack.model_validate(data)
    except ValidationError as e:
        # Field locations only; pydantic messages can echo input values.
        locs = sorted({".".join(str(p) for p in err["loc"]) for err in e.errors()})
        raise ValidationFailed("schema:" + ",".join(locs)[:200]) from None
    by_id = {p["id"]: _norm(p["text"]) for p in paragraphs}
    for i, q in enumerate(pack.questions, start=1):
        if q.paragraph_id not in by_id:
            raise ValidationFailed(f"unknown_paragraph:q{i}")
        if _norm(q.quote) not in by_id[q.paragraph_id]:
            raise ValidationFailed(f"quote_not_found:q{i}")
    return pack
