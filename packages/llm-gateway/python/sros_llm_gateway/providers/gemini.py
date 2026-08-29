"""Google Gemini generateContent adapter.

Mission 0.4 §18. The second provider module. Same contract as
`anthropic.py`, same absence of a vendor SDK, same rule that nothing outside
`providers/` may import it.

ADR-006's initial strategy puts Gemini on cheap, high-volume work and Claude on
strong reasoning. Neither preference lives here: the tier -> provider mapping is
configuration, and this adapter has no opinion about which tier it serves beyond
what it can actually do.

**Structured output uses `responseMimeType` plus `responseSchema`**, the
provider's own JSON mode, for the reason given in the Anthropic adapter: a
decoder constraint cannot be talked out of by text inside a data region, and a
prose instruction can.

One caveat worth stating rather than discovering: Gemini's `responseSchema`
accepts a **subset** of JSON Schema. A schema the gateway is happy with can be
rejected here as an invalid argument. That surfaces as `INVALID_REQUEST`, which
is deliberately not retried — retrying a schema the provider structurally cannot
accept would burn budget on a certainty.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from sros_contracts import LlmTier

from ..gateway import ProviderResult
from ..transport import HttpResponse, HttpTransport, TransportError, UrllibTransport
from ..types import (
    LlmRequest,
    ProviderAuthenticationError,
    ProviderInvalidRequestError,
    ProviderRateLimitedError,
    ProviderTemporaryError,
    ProviderTimeoutError,
)

__all__ = ["GeminiProvider", "DEFAULT_API_BASE"]

DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


@dataclass
class GeminiProvider:
    name: str = "gemini"
    api_key: str = ""
    api_base: str = DEFAULT_API_BASE
    transport: HttpTransport | None = None
    max_output_tokens: int = 4096
    # Embeddings stay local (ADR-006): BGE-M3 removes the dominant recurring
    # cost and a network dependency from the hottest path in the pipeline.
    supported_tiers: tuple[LlmTier, ...] = (
        LlmTier.FAST_MODEL,
        LlmTier.BALANCED_MODEL,
        LlmTier.STRONG_MODEL,
    )

    def __post_init__(self) -> None:
        if not self.api_key:
            self.api_key = os.environ.get("GEMINI_API_KEY", "")
        if self.transport is None:
            self.transport = UrllibTransport()

    def supports(self, tier: LlmTier) -> bool:
        return tier in self.supported_tiers

    # -- request translation ------------------------------------------------

    def endpoint_for(self, model: str) -> str:
        """The model is a path segment, so it is validated rather than trusted.

        Model names come from configuration; configuration reaches production.
        A name containing a slash or a query separator would silently retarget
        the request at another endpoint.
        """
        if not model or any(ch in model for ch in "/?#&"):
            raise ProviderInvalidRequestError(
                f"invalid gemini model name {model!r}: a model is a single path segment",
                provider=self.name,
            )
        return f"{self.api_base}/models/{model}:generateContent"

    def build_body(self, request: LlmRequest, model: str) -> dict[str, Any]:
        if request.prompt is None:
            raise ProviderInvalidRequestError(
                "a provider request requires a rendered prompt. Prompts are versioned "
                "template artifacts, never assembled at a call site (ADR-006).",
                provider=self.name,
            )
        system_text, user_text = request.prompt.to_payload_parts()

        generation: dict[str, Any] = {"maxOutputTokens": self.max_output_tokens}
        if request.response_schema is not None:
            generation["responseMimeType"] = "application/json"
            generation["responseSchema"] = request.response_schema

        return {
            # systemInstruction keeps our instructions out of the turn that
            # carries the quoted source data.
            "systemInstruction": {"parts": [{"text": system_text}]},
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
            "generationConfig": generation,
        }

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderAuthenticationError(
                "GEMINI_API_KEY is not configured. No request was sent.", provider=self.name
            )
        # The header form, never `?key=`: a credential in a query string is
        # logged by every proxy between here and the provider.
        return {"x-goog-api-key": self.api_key}

    # -- execution ----------------------------------------------------------

    def complete(self, request: LlmRequest, model: str) -> ProviderResult:
        body = self.build_body(request, model)
        headers = self._headers()
        assert self.transport is not None  # set in __post_init__  # noqa: S101

        try:
            response = self.transport.post_json(
                self.endpoint_for(model), headers, body, request.timeout_seconds
            )
        except TimeoutError as exc:
            raise ProviderTimeoutError(str(exc), provider=self.name) from exc
        except TransportError as exc:
            raise ProviderTemporaryError(str(exc), provider=self.name) from exc

        if response.status != 200:
            raise self._error_for(response)
        return self._normalize(response, structured=request.response_schema is not None)

    # -- response normalization ---------------------------------------------

    def _normalize(self, response: HttpResponse, structured: bool) -> ProviderResult:
        payload = response.json()
        candidates = payload.get("candidates") or []
        text_parts: list[str] = []
        if isinstance(candidates, list) and candidates:
            first = candidates[0]
            if isinstance(first, dict):
                content = first.get("content") or {}
                parts = content.get("parts") if isinstance(content, dict) else None
                for part in parts or []:
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        text_parts.append(part["text"])

        text = "".join(text_parts)

        parsed: dict[str, Any] | None = None
        if structured and text:
            # JSON mode was requested, so the body should be JSON. A malformed
            # body is NOT an error here: it becomes `structured=None`, and the
            # gateway raises a schema failure — which is where a possible
            # injection is meant to surface (llm-reasoning-rules.md §7).
            import json

            try:
                candidate = json.loads(text)
            except ValueError:
                candidate = None
            if isinstance(candidate, dict):
                parsed = candidate

        usage = payload.get("usageMetadata") or {}
        return ProviderResult(
            content=text,
            structured=parsed,
            input_tokens=int(usage.get("promptTokenCount") or 0),
            output_tokens=int(usage.get("candidatesTokenCount") or 0),
            cost_units=0.0,
        )

    def _error_for(self, response: HttpResponse) -> Exception:
        detail = _error_detail(response)
        status = response.status

        if status in (401, 403):
            return ProviderAuthenticationError(
                f"gemini rejected the credential ({status}): {detail}",
                provider=self.name,
                status_code=status,
            )
        if status == 429:
            return ProviderRateLimitedError(
                f"gemini rate limited the request: {detail}",
                provider=self.name,
                status_code=status,
                retry_after_seconds=_retry_after(response),
            )
        if status in (408, 504):
            return ProviderTimeoutError(
                f"gemini timed out ({status}): {detail}",
                provider=self.name,
                status_code=status,
            )
        if status >= 500:
            return ProviderTemporaryError(
                f"gemini returned {status}: {detail}", provider=self.name, status_code=status
            )
        return ProviderInvalidRequestError(
            f"gemini rejected the request ({status}): {detail}",
            provider=self.name,
            status_code=status,
        )


def _error_detail(response: HttpResponse) -> str:
    try:
        payload = response.json()
    except TransportError:
        return response.body[:200].decode("utf-8", errors="replace")
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str):
            return message
    return str(payload)[:200]


def _retry_after(response: HttpResponse) -> float | None:
    raw = response.header("retry-after")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
