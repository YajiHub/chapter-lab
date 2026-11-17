from pathlib import Path
from typing import Literal

import httpx

from app.generation.prompt import OUTPUT_JSON_SCHEMA

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

STUB_PACK_PATH = Path(__file__).with_name("stub_pack.json")


class ProviderError(Exception):
    """Provider call failed. Messages carry status/kind only, never response bodies."""


class ProviderQuota(ProviderError):
    pass


class ProviderTimeout(ProviderError):
    pass


class ProviderUnavailable(ProviderError):
    pass


class OpenAICompatibleProvider:
    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        json_mode: Literal["schema", "object"] = "schema",
        timeout: float = 25.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.name, self.base_url, self.model = name, base_url.rstrip("/"), model
        self._api_key, self.json_mode = api_key, json_mode
        self.timeout, self._transport = timeout, transport

    def _response_format(self) -> dict:
        if self.json_mode == "object":
            return {"type": "json_object"}
        return {
            "type": "json_schema",
            "json_schema": {"name": "study_pack", "schema": OUTPUT_JSON_SCHEMA},
        }

    def complete(self, messages: list[dict]) -> str:
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "response_format": self._response_format(),
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
                r = client.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
        except httpx.TimeoutException:
            raise ProviderTimeout("timeout") from None
        except httpx.HTTPError as e:
            raise ProviderUnavailable(f"connection:{type(e).__name__}") from None
        if r.status_code == 429:
            raise ProviderQuota("http_429")
        if r.status_code >= 400:
            raise ProviderUnavailable(f"http_{r.status_code}")
        try:
            return r.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProviderUnavailable("bad_response_shape") from None


class StubProvider:
    def __init__(
        self, output: str | Exception | None = None, name: str = "stub", model: str = "stub"
    ) -> None:
        self.name, self.model, self.output = name, model, output

    def complete(self, messages: list[dict]) -> str:
        if isinstance(self.output, Exception):
            raise self.output
        if self.output is None:
            return STUB_PACK_PATH.read_text(encoding="utf-8")
        return self.output
