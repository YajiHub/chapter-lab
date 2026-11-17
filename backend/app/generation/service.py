import time
from collections.abc import Callable
from dataclasses import dataclass

from app.config import Settings
from app.generation.openrouter_picker import pick_free_models
from app.generation.prompt import build_messages
from app.generation.providers import (
    GEMINI_BASE_URL,
    GROQ_BASE_URL,
    OPENROUTER_BASE_URL,
    OpenAICompatibleProvider,
    ProviderQuota,
    ProviderTimeout,
    ProviderUnavailable,
    StubProvider,
)
from app.generation.validate import GeneratedPack, ValidationFailed, validate_output

# ChainFailed.outcome -> error code in app/errors.py
HTTP_ERROR = {
    "quota": "quota_exhausted",
    "timeout": "provider_unavailable",
    "unavailable": "provider_unavailable",
    "invalid_output": "provider_invalid_output",
}

OPENROUTER_PREFERRED = ["google/gemma", "nvidia/nemotron", "meta-llama/", "qwen/", "mistralai/"]


@dataclass
class ProviderTry:
    provider: str
    model: str | None
    outcome: str
    ms: int


@dataclass
class ChainResult:
    pack: GeneratedPack
    provider: str
    model: str
    trace: list[ProviderTry]
    duration_ms: int


class ChainFailed(Exception):
    def __init__(self, outcome: str, trace: list[ProviderTry] | None = None) -> None:
        super().__init__(outcome)
        self.outcome = outcome
        self.trace = trace if trace is not None else []


def _try(
    provider, messages: list[dict], paragraphs: list[dict]
) -> tuple[str, GeneratedPack | None]:
    try:
        return "success", validate_output(provider.complete(messages), paragraphs)
    except ProviderQuota:
        return "quota", None
    except ProviderTimeout:
        return "timeout", None
    except ProviderUnavailable:
        return "unavailable", None
    except ValidationFailed:
        return "invalid_output", None


def run_chain(
    paragraphs: list[dict],
    providers: list,
    deadline_s: float = 60.0,
    clock: Callable[[], float] = time.monotonic,
) -> ChainResult:
    start = clock()
    messages = build_messages(paragraphs)
    trace: list[ProviderTry] = []
    for p in providers:
        t = clock()
        if t - start >= deadline_s:
            break
        outcome, pack = _try(p, messages, paragraphs)
        trace.append(ProviderTry(p.name, p.model, outcome, int((clock() - t) * 1000)))
        if pack is not None:
            duration = int((clock() - start) * 1000)
            return ChainResult(pack, p.name, p.model, trace, duration)
    outcomes = [t.outcome for t in trace]
    if "invalid_output" in outcomes:
        raise ChainFailed("invalid_output", trace)
    if outcomes and all(o == "quota" for o in outcomes):
        raise ChainFailed("quota", trace)
    if "timeout" in outcomes:
        raise ChainFailed("timeout", trace)
    raise ChainFailed("unavailable", trace)


def build_providers(settings: Settings) -> list:
    if settings.provider_mode == "stub":
        return [StubProvider()]
    providers: list = []
    if settings.gemini_api_key:
        providers.append(
            OpenAICompatibleProvider(
                "gemini", GEMINI_BASE_URL, settings.gemini_api_key, settings.gemini_model
            )
        )
    if not settings.fallback_enabled:
        return providers
    if settings.groq_api_key:
        providers.append(
            OpenAICompatibleProvider(
                "groq", GROQ_BASE_URL, settings.groq_api_key, settings.groq_model, "object"
            )
        )
    if settings.openrouter_api_key:
        for model in pick_free_models(settings.openrouter_api_key, OPENROUTER_PREFERRED):
            providers.append(
                OpenAICompatibleProvider(
                    "openrouter", OPENROUTER_BASE_URL, settings.openrouter_api_key, model, "object"
                )
            )
    return providers
