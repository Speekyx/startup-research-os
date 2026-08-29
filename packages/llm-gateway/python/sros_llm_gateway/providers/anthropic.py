"""Anthropic Messages API adapter.

Mission 0.4 §18. One of the two provider modules where vendor knowledge is
allowed to live (ADR-006). Nothing outside `providers/` knows this file exists;
business services request `STRONG_MODEL` and never a name.

**No vendor SDK.** The adapter speaks the HTTP API through the injectable
`HttpTransport`, which is what lets §20 hold: the whole suite runs with a fake
transport, no key and no bill. The trade-off is written up in `transport.py`.

**Structured output uses forced tool use**, not a "reply in JSON" instruction.
Asking a model in prose to return JSON is an instruction competing with every
other instruction in the prompt — including any an attacker managed to place in
a data region. A forced tool call is enforced by the provider's decoder, so the
failure mode becomes "no output" rather than "plausible output shaped by
whoever asked last".
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

__all__ = ["AnthropicProvider", "ANTHROPIC_API_VERSION", "STRUCTURED_TOOL_NAME"]

ANTHROPIC_API_VERSION = "2023-06-01"
DEFAULT_ENDPOINT = "https://api.anthropic.com/v1/messages"

# The tool a structured request is forced into. Named for what it does rather
# than after a domain concept: the schema is supplied per request.
STRUCTURED_TOOL_NAME = "emit_structured_output"


@dataclass
class AnthropicProvider:
    """Anthropic behind the provider-neutral interface.

    The api key is read from the environment at construction and never logged,
    never echoed into an error, and never placed in a URL.
    """

    name: str = "anthropic"
    api_key: str = ""
    endpoint: str = DEFAULT_ENDPOINT
    transport: HttpTransport | None = None
    max_output_tokens: int = 4096
    # Embeddings are local BGE-M3 (ADR-006). Advertising support here would let
    # the router send embedding volume to a paid API, which is the single
    # largest avoidable cost in the system.
    supported_tiers: tuple[LlmTier, ...] = (
        LlmTier.FAST_MODEL,
        LlmTier.BALANCED_MODEL,
        LlmTier.STRONG_MODEL,
    )

    def __post_init__(self) -> None:
        if not self.api_key:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if self.transport is None:
            self.transport = UrllibTransport()

    def supports(self, tier: LlmTier) -> bool:
        return tier in self.supported_tiers

    # -- request translation ------------------------------------------------

    def build_body(self, request: LlmRequest, model: str) -> dict[str, Any]:
        """Translate an LlmRequest into an Anthropic request body.

        Separate from `complete` so a test can assert on the translation without
        a transport at all (§37).
        """
        if request.prompt is None:
            raise ProviderInvalidRequestError(
                "a provider request requires a rendered prompt. Prompts are versioned "
                "template artifacts, never assembled at a call site (ADR-006).",
                provider=self.name,
            )
        system_text, user_text = request.prompt.to_payload_parts()

        body: dict[str, Any] = {
            "model": model,
            "max_tokens": self.max_output_tokens,
            # The system region stays in the system field. Folding it into the
            # user turn would put our instructions at the same level as the
            # source data quoted beneath them.
            "system": system_text,
            "messages": [{"role": "user", "content": user_text}],
        }
        if request.response_schema is not None:
            body["tools"] = [
                {
                    "name": STRUCTURED_TOOL_NAME,
                    "description": "Return the analysis as structured data.",
                    "input_schema": request.response_schema,
                }
            ]
            body["tool_choice"] = {"type": "tool", "name": STRUCTURED_TOOL_NAME}
        return body

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderAuthenticationError(
                "ANTHROPIC_API_KEY is not configured. No request was sent.",
                provider=self.name,
            )
        return {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
        }

    # -- execution ----------------------------------------------------------

    def complete(self, request: LlmRequest, model: str) -> ProviderResult:
        body = self.build_body(request, model)
        headers = self._headers()
        assert self.transport is not None  # set in __post_init__  # noqa: S101

        try:
            response = self.transport.post_json(
                self.endpoint, headers, body, request.timeout_seconds
            )
        except TimeoutError as exc:
            raise ProviderTimeoutError(str(exc), provider=self.name) from exc
        except TransportError as exc:
            raise ProviderTemporaryError(str(exc), provider=self.name) from exc

        if response.status != 200:
            raise self._error_for(response)
        return self._normalize(response)

    # -- response normalization ---------------------------------------------

    def _normalize(self, response: HttpResponse) -> ProviderResult:
        payload = response.json()
        blocks = payload.get("content") or []
        if not isinstance(blocks, list):
            raise ProviderTemporaryError(
                "malformed response: `content` was not a list", provider=self.name
            )

        text_parts: list[str] = []
        structured: dict[str, Any] | None = None
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                text_parts.append(block["text"])
            elif block.get("type") == "tool_use" and block.get("name") == STRUCTURED_TOOL_NAME:
                candidate = block.get("input")
                if isinstance(candidate, dict):
                    structured = candidate

        usage = payload.get("usage") or {}
        return ProviderResult(
            content="".join(text_parts),
            structured=structured,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            # Cost is computed by the gateway from the versioned pricing table.
            # A provider that priced its own calls would put a tariff inside
            # business logic, which §15 forbids.
            cost_units=0.0,
        )

    def _error_for(self, response: HttpResponse) -> Exception:
        """Map a status onto the internal category vocabulary (§21).

        The provider's own message is included because it is diagnostic, and the
        api key never is: it appears in no request echo, no log line and no
        exception text.
        """
        detail = _error_detail(response)
        status = response.status

        if status in (401, 403):
            return ProviderAuthenticationError(
                f"anthropic rejected the credential ({status}): {detail}",
                provider=self.name,
                status_code=status,
            )
        if status == 429:
            return ProviderRateLimitedError(
                f"anthropic rate limited the request: {detail}",
                provider=self.name,
                status_code=status,
                retry_after_seconds=_retry_after(response),
            )
        if status in (408, 504):
            return ProviderTimeoutError(
                f"anthropic timed out ({status}): {detail}",
                provider=self.name,
                status_code=status,
            )
        if status >= 500:
            # 529 is Anthropic's "overloaded": transient by definition.
            return ProviderTemporaryError(
                f"anthropic returned {status}: {detail}",
                provider=self.name,
                status_code=status,
            )
        return ProviderInvalidRequestError(
            f"anthropic rejected the request ({status}): {detail}",
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
