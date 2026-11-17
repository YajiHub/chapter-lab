import json
from pathlib import Path
from typing import Literal

import httpx
import pytest

from app.config import Settings
from app.generation import openrouter_picker
from app.generation.openrouter_picker import pick_free_models
from app.generation.paragraphs import split_paragraphs
from app.generation.prompt import build_messages
from app.generation.providers import (
    OpenAICompatibleProvider,
    ProviderQuota,
    ProviderTimeout,
    ProviderUnavailable,
    StubProvider,
)
from app.generation.service import ChainFailed, build_providers, run_chain
from app.generation.trial import DEMO_LESSON, demo_lesson_body
from app.generation.validate import ValidationFailed, validate_output

FIXTURES = Path(__file__).parent / "fixtures" / "generation"
PARAGRAPHS = split_paragraphs(demo_lesson_body(DEMO_LESSON.read_text(encoding="utf-8")))


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def valid() -> dict:
    return json.loads(fixture("valid_pack.json"))


# ---------- paragraphs / prompt ----------


def test_split_paragraphs():
    notes = "  First   line\nwraps here.\n\n\n  \nSecond\tpara.  \n \n"
    assert split_paragraphs(notes) == [
        {"id": 1, "text": "First line wraps here."},
        {"id": 2, "text": "Second para."},
    ]
    assert split_paragraphs("   \n\n ") == []


def test_demo_lesson_body_paragraphs():
    assert len(PARAGRAPHS) == 6
    assert PARAGRAPHS[1]["text"].startswith("Client-side rendering")
    assert not any("Evaluation anchors" in p["text"] for p in PARAGRAPHS)


def test_prompt_delimits_source_as_data():
    system, user = build_messages(PARAGRAPHS)
    assert "not instructions" in system["content"]
    assert "<<<SOURCE>>>" in user["content"] and "[2] Client-side" in user["content"]


# ---------- validate ----------


def test_validate_accepts_valid_and_fenced():
    raw = fixture("valid_pack.json")
    assert len(validate_output(raw, PARAGRAPHS).questions) == 5
    assert validate_output(f"```json\n{raw}\n```", PARAGRAPHS).guide


def test_validate_normalizes_quote_punctuation_and_case():
    data = valid()
    data["questions"][0]["quote"] = "STATIC site   generation prepares HTML at build time."
    validate_output(json.dumps(data), PARAGRAPHS)
    paras = [{"id": 1, "text": "It’s a “quote” — here."}]
    data["questions"] = [
        {**q, "paragraphId": 1, "quote": 'it\'s a "quote" - here'} for q in data["questions"]
    ]
    validate_output(json.dumps(data), paras)


def _mutate(fn) -> str:
    data = valid()
    fn(data)
    return json.dumps(data)


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        (fixture("bad_citation.json"), "quote_not_found:q1"),
        (fixture("bad_answer_index.json"), "schema:"),
        (_mutate(lambda d: d["questions"][0].update(paragraphId=99)), "unknown_paragraph:q1"),
        (
            _mutate(lambda d: d["questions"][1]["choices"].__setitem__(1, "AT BUILD TIME")),
            "schema:",
        ),
        (_mutate(lambda d: d["questions"].pop()), "schema:"),
        ("Sorry, here is your pack!", "bad_json"),
    ],
)
def test_validate_rejects(raw, reason):
    with pytest.raises(ValidationFailed) as e:
        validate_output(raw, PARAGRAPHS)
    assert str(e.value).startswith(reason)


def test_validation_reason_never_contains_lesson_text():
    with pytest.raises(ValidationFailed) as e:
        validate_output(fixture("bad_citation.json"), PARAGRAPHS)
    assert "Static" not in str(e.value)


# ---------- providers ----------


def _provider(
    handler, json_mode: Literal["schema", "object"] = "schema"
) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        "gemini",
        "https://example.test/v1",
        "sk-test",
        "m1",
        json_mode,
        transport=httpx.MockTransport(handler),
    )


def test_provider_success_sends_bearer_and_response_format():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    assert _provider(handler).complete([{"role": "user", "content": "x"}]) == "{}"
    assert seen["url"] == "https://example.test/v1/chat/completions"
    assert seen["auth"] == "Bearer sk-test"
    assert seen["body"]["response_format"]["type"] == "json_schema"
    assert seen["body"]["response_format"]["json_schema"]["name"] == "study_pack"
    assert seen["body"]["model"] == "m1" and seen["body"]["temperature"] == 0.3

    _provider(handler, "object").complete([])
    assert seen["body"]["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize(
    ("status", "exc"),
    [
        (429, ProviderQuota),
        (500, ProviderUnavailable),
        (401, ProviderUnavailable),
        (400, ProviderUnavailable),
    ],
)
def test_provider_status_mapping(status, exc):
    p = _provider(lambda r: httpx.Response(status, text="secret lesson echo"))
    with pytest.raises(exc) as e:
        p.complete([])
    assert "secret" not in str(e.value)


def test_provider_timeout_and_connection_error():
    def timeout(request):
        raise httpx.ReadTimeout("slow", request=request)

    def refused(request):
        raise httpx.ConnectError("nope", request=request)

    with pytest.raises(ProviderTimeout):
        _provider(timeout).complete([])
    with pytest.raises(ProviderUnavailable):
        _provider(refused).complete([])


def test_stub_provider():
    assert StubProvider("x").complete([]) == "x"
    with pytest.raises(ProviderQuota):
        StubProvider(ProviderQuota()).complete([])
    pack = validate_output(StubProvider().complete([]), PARAGRAPHS)
    assert len(pack.questions) == 5


# ---------- openrouter picker ----------


def _model(id_, ctx=32000, price="0", params=("response_format",), out=("text",)):
    return {
        "id": id_,
        "architecture": {"output_modalities": list(out)},
        "context_length": ctx,
        "pricing": {"prompt": price, "completion": price},
        "supported_parameters": list(params),
    }


MODELS = [
    _model("qwen/q-big", ctx=128000),
    _model("meta-llama/llama-small", ctx=20000),
    _model("other/huge", ctx=1_000_000, params=("structured_outputs",)),
    _model("meta-llama/paid", price="0.0001"),
    _model("google/gemma:free", price="0.0001", ctx=64000),
    _model("meta-llama/tiny", ctx=8000),
    _model("meta-llama/no-json", params=("tools",)),
    _model("meta-llama/music", ctx=2_000_000, out=("text", "audio")),
]


@pytest.fixture
def clear_picker_cache():
    openrouter_picker._cache.update(at=None, models=[])
    yield
    openrouter_picker._cache.update(at=None, models=[])


def test_picker_filters_ranks_and_caches(clear_picker_cache):
    calls = []

    def handler(request):
        calls.append(request.headers["authorization"])
        return httpx.Response(200, json={"data": MODELS})

    t = [1000.0]
    pick = lambda limit=2: pick_free_models(  # noqa: E731
        "or-key", ["meta-llama/", "google/"], limit, httpx.MockTransport(handler), lambda: t[0]
    )
    assert pick(10) == ["meta-llama/llama-small", "google/gemma:free", "other/huge", "qwen/q-big"]
    assert pick() == ["meta-llama/llama-small", "google/gemma:free"]
    assert calls == ["Bearer or-key"]  # second call served from cache
    t[0] += 24 * 3600
    pick()
    assert len(calls) == 2


@pytest.mark.parametrize(
    "response",
    [httpx.Response(500), httpx.Response(200, text="not json"), httpx.Response(200, json={"x": 1})],
)
def test_picker_errors_return_empty(clear_picker_cache, response):
    assert pick_free_models("k", [], transport=httpx.MockTransport(lambda r: response)) == []


# ---------- chain ----------


VALID = fixture("valid_pack.json")


def test_chain_first_success_with_trace():
    r = run_chain(PARAGRAPHS, [StubProvider(VALID, "gemini", "g1"), StubProvider(VALID, "groq")])
    assert (r.provider, r.model) == ("gemini", "g1")
    assert [(t.provider, t.model, t.outcome) for t in r.trace] == [("gemini", "g1", "success")]
    assert len(r.pack.questions) == 5 and r.duration_ms >= 0


def test_chain_quota_then_success():
    r = run_chain(
        PARAGRAPHS, [StubProvider(ProviderQuota(), "gemini"), StubProvider(VALID, "groq")]
    )
    assert r.provider == "groq"
    assert [t.outcome for t in r.trace] == ["quota", "success"]


@pytest.mark.parametrize(
    ("outputs", "outcome"),
    [
        ([ProviderQuota(), ProviderQuota()], "quota"),
        ([fixture("bad_citation.json"), ProviderQuota()], "invalid_output"),
        ([ProviderQuota(), ProviderTimeout()], "timeout"),
        ([ProviderQuota(), ProviderUnavailable()], "unavailable"),
        ([], "unavailable"),
    ],
)
def test_chain_failures(outputs, outcome):
    with pytest.raises(ChainFailed) as e:
        run_chain(PARAGRAPHS, [StubProvider(o) for o in outputs])
    assert e.value.outcome == outcome
    assert len(e.value.trace) == len(outputs)


def test_chain_deadline_stops_tries():
    t = [0.0]

    class Slow(StubProvider):
        def complete(self, messages):
            t[0] += 40.0
            raise ProviderTimeout()

    with pytest.raises(ChainFailed) as e:
        run_chain(PARAGRAPHS, [Slow(), Slow(), Slow()], deadline_s=60.0, clock=lambda: t[0])
    assert e.value.outcome == "timeout"
    assert [tr.ms for tr in e.value.trace] == [40000, 40000]


def test_build_providers():
    assert [p.name for p in build_providers(Settings(provider_mode="stub"))] == ["stub"]
    s = Settings(
        provider_mode="chain",
        gemini_api_key="g",
        groq_api_key="q",
        openrouter_api_key="",
        fallback_enabled=True,
    )
    assert [(p.name, p.json_mode) for p in build_providers(s)] == [
        ("gemini", "schema"),
        ("groq", "object"),
    ]
    s.fallback_enabled = False
    assert [p.name for p in build_providers(s)] == ["gemini"]
