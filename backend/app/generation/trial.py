"""Manual smoke test against real providers on the demo lesson.

    uv run python -m app.generation.trial [gemini|groq|openrouter|all]

Prints provider, model, duration and validation result only: never keys or generated text.
"""

import sys
import time
from pathlib import Path

from app.config import get_settings
from app.generation.openrouter_picker import pick_free_models
from app.generation.paragraphs import split_paragraphs
from app.generation.prompt import build_messages
from app.generation.providers import (
    GEMINI_BASE_URL,
    GROQ_BASE_URL,
    OPENROUTER_BASE_URL,
    OpenAICompatibleProvider,
    ProviderError,
)
from app.generation.service import OPENROUTER_PREFERRED
from app.generation.validate import ValidationFailed, validate_output

DEMO_LESSON = Path(__file__).resolve().parents[3] / "docs" / "DEMO_LESSON.md"


def demo_lesson_body(text: str) -> str:
    """Lesson body without the '# ' title line and the '## Evaluation anchors' section."""
    body = text.split("## Evaluation anchors")[0]
    return "\n".join(line for line in body.splitlines() if not line.startswith("# "))


def _providers(which: str) -> list[OpenAICompatibleProvider]:
    s = get_settings()
    out = []
    if which in ("gemini", "all") and s.gemini_api_key:
        out.append(
            OpenAICompatibleProvider("gemini", GEMINI_BASE_URL, s.gemini_api_key, s.gemini_model)
        )
    if which in ("groq", "all") and s.groq_api_key:
        out.append(
            OpenAICompatibleProvider(
                "groq", GROQ_BASE_URL, s.groq_api_key, s.groq_model, json_mode="object"
            )
        )
    if which in ("openrouter", "all") and s.openrouter_api_key:
        for m in pick_free_models(s.openrouter_api_key, OPENROUTER_PREFERRED):
            out.append(
                OpenAICompatibleProvider(
                    "openrouter", OPENROUTER_BASE_URL, s.openrouter_api_key, m, json_mode="object"
                )
            )
    return out


def main(which: str = "all") -> None:
    paragraphs = split_paragraphs(demo_lesson_body(DEMO_LESSON.read_text(encoding="utf-8")))
    messages = build_messages(paragraphs)
    providers = _providers(which)
    if not providers:
        print(f"no configured provider for {which!r}")
    for p in providers:
        t = time.monotonic()
        try:
            validate_output(p.complete(messages), paragraphs)
            result = "ok"
        except (ProviderError, ValidationFailed) as e:
            result = f"{type(e).__name__}: {e}"
        ms = int((time.monotonic() - t) * 1000)
        print(f"{p.name}\t{p.model}\t{ms} ms\t{result}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
