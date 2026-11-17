import time
from collections.abc import Callable

import httpx

from app.generation.providers import OPENROUTER_BASE_URL

CACHE_SECONDS = 24 * 3600
MIN_CONTEXT = 16000

_cache: dict = {"at": None, "models": []}  # in-process list of eligible model dicts


def _is_free(m: dict) -> bool:
    p = m.get("pricing") or {}
    zero = str(p.get("prompt")) == "0" and str(p.get("completion")) == "0"
    return zero or str(m.get("id", "")).endswith(":free")


def _eligible(m: dict) -> bool:
    params = m.get("supported_parameters") or []
    structured = "response_format" in params or "structured_outputs" in params
    # Text-only output: excludes audio/image generators that also list response_format.
    text_only = (m.get("architecture") or {}).get("output_modalities") == ["text"]
    return (
        isinstance(m.get("id"), str)
        and _is_free(m)
        and structured
        and text_only
        and (m.get("context_length") or 0) >= MIN_CONTEXT
    )


def _fetch(api_key: str, transport: httpx.BaseTransport | None) -> list[dict]:
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=10.0, transport=transport) as client:
        r = client.get(f"{OPENROUTER_BASE_URL}/models", headers=headers)
        r.raise_for_status()
        return [m for m in r.json()["data"] if _eligible(m)]


def pick_free_models(
    api_key: str,
    preferred: list[str],
    limit: int = 2,
    transport: httpx.BaseTransport | None = None,
    now: Callable[[], float] = time.time,
) -> list[str]:
    t = now()
    if _cache["at"] is None or t - _cache["at"] >= CACHE_SECONDS:
        try:
            models = _fetch(api_key, transport)
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []  # don't cache failures; retry next call
        _cache.update(at=t, models=models)

    def rank(m: dict) -> tuple[int, int]:
        pref = next((i for i, p in enumerate(preferred) if m["id"].startswith(p)), len(preferred))
        return pref, -(m.get("context_length") or 0)

    return [m["id"] for m in sorted(_cache["models"], key=rank)[:limit]]
