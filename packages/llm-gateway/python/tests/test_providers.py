"""Provider adapter tests.

Mission 0.4 §37. Every case runs against `FakeTransport`: **no network, no API
key, no bill**, which is §20 stated as a property of the suite rather than a
promise in a comment.

The one thing these tests deliberately do NOT check is whether the providers'
real APIs still look like this. That needs a live call and a credential, so it
lives in `test_provider_smoke.py`, opt-in and skipped by default.
"""

from __future__ import annotations

import json
import unittest

from sros_contracts import LlmTier
from sros_llm_gateway import (
    ErrorCategory,
    FakeTransport,
    GatewayConfig,
    HttpResponse,
    LlmGateway,
    LlmRequest,
    ProviderAuthenticationError,
    ProviderInvalidRequestError,
    ProviderRateLimitedError,
    ProviderTemporaryError,
    ProviderTimeoutError,
    RenderedPrompt,
    TierBinding,
    TransportError,
    UntrustedText,
    category_of,
    is_retryable,
)
from sros_llm_gateway.providers import AnthropicProvider, GeminiProvider

WORKSPACE = "00000000-0000-4000-8000-000000000001"
SESSION = "00000000-0000-4000-8000-0000000000aa"

SCHEMA = {
    "type": "object",
    "required": ["claim_type"],
    "properties": {"claim_type": {"type": "string"}},
}


def prompt(with_untrusted: bool = False) -> RenderedPrompt:
    return RenderedPrompt(
        system_instructions="You classify statements. Return one claim type.",
        trusted_context="market_scope=COUNTRY:FR",
        task="Classify the statement.",
        untrusted=(UntrustedText("the export button fails", "review-42"),)
        if with_untrusted
        else (),
    )


def request(**kwargs: object) -> LlmRequest:
    defaults: dict[str, object] = {
        "tier": LlmTier.BALANCED_MODEL,
        "task": "classify.signal",
        "prompt_template_id": "signal-classify",
        "prompt_template_version": "1.0.0",
        "workspace_id": WORKSPACE,
        "research_session_id": SESSION,
        "correlation_id": "corr-1",
        "prompt": prompt(),
    }
    defaults.update(kwargs)
    return LlmRequest(**defaults)  # type: ignore[arg-type]


def anthropic_ok(
    text: str = "OBSERVED", tool_input: dict[str, object] | None = None
) -> HttpResponse:
    content: list[dict[str, object]] = [{"type": "text", "text": text}]
    if tool_input is not None:
        content.append({"type": "tool_use", "name": "emit_structured_output", "input": tool_input})
    return HttpResponse(
        200,
        json.dumps({"content": content, "usage": {"input_tokens": 120, "output_tokens": 8}}).encode(
            "utf-8"
        ),
    )


def gemini_ok(text: str = "OBSERVED") -> HttpResponse:
    return HttpResponse(
        200,
        json.dumps(
            {
                "candidates": [{"content": {"parts": [{"text": text}]}}],
                "usageMetadata": {"promptTokenCount": 120, "candidatesTokenCount": 8},
            }
        ).encode("utf-8"),
    )


def error_response(
    status: int, message: str, headers: dict[str, str] | None = None
) -> HttpResponse:
    return HttpResponse(
        status,
        json.dumps({"error": {"message": message}}).encode("utf-8"),
        headers or {},
    )


# ======================================================== request translation


class AnthropicRequestTranslation(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = FakeTransport()
        self.provider = AnthropicProvider(api_key="k", transport=self.transport)

    def test_the_system_region_stays_in_the_system_field(self) -> None:
        """Folding it into the user turn would put our instructions at the same
        level as the source data quoted beneath them."""
        body = self.provider.build_body(request(prompt=prompt(with_untrusted=True)), "m")
        self.assertIn("You classify statements", body["system"])
        self.assertNotIn("the export button fails", body["system"])

    def test_untrusted_content_appears_only_in_the_user_turn(self) -> None:
        body = self.provider.build_body(request(prompt=prompt(with_untrusted=True)), "m")
        user = body["messages"][0]["content"]
        self.assertIn("the export button fails", user)
        self.assertIn("UNTRUSTED_SOURCE_DATA", user)

    def test_the_model_comes_from_the_caller_not_from_the_adapter(self) -> None:
        body = self.provider.build_body(request(), "a-configured-model")
        self.assertEqual(body["model"], "a-configured-model")

    def test_a_structured_request_forces_a_tool_call(self) -> None:
        """A prose "reply in JSON" instruction competes with every other
        instruction in the prompt, including any an attacker placed in a data
        region. A decoder constraint does not."""
        body = self.provider.build_body(request(response_schema=SCHEMA), "m")
        self.assertEqual(body["tools"][0]["input_schema"], SCHEMA)
        self.assertEqual(body["tool_choice"], {"type": "tool", "name": "emit_structured_output"})

    def test_an_unstructured_request_declares_no_tool(self) -> None:
        body = self.provider.build_body(request(), "m")
        self.assertNotIn("tools", body)

    def test_a_request_without_a_rendered_prompt_is_refused(self) -> None:
        with self.assertRaises(ProviderInvalidRequestError):
            self.provider.build_body(request(prompt=None), "m")

    def test_the_api_version_header_is_sent(self) -> None:
        self.transport.queue([anthropic_ok()])
        self.provider.complete(request(), "m")
        self.assertEqual(self.transport.calls[0]["headers"]["anthropic-version"], "2023-06-01")


class GeminiRequestTranslation(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = FakeTransport()
        self.provider = GeminiProvider(api_key="k", transport=self.transport)

    def test_the_system_instruction_is_a_separate_field(self) -> None:
        body = self.provider.build_body(request(prompt=prompt(with_untrusted=True)), "m")
        system = body["systemInstruction"]["parts"][0]["text"]
        self.assertIn("You classify statements", system)
        self.assertNotIn("the export button fails", system)

    def test_a_structured_request_uses_json_mode(self) -> None:
        body = self.provider.build_body(request(response_schema=SCHEMA), "m")
        self.assertEqual(body["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(body["generationConfig"]["responseSchema"], SCHEMA)

    def test_the_model_is_a_single_path_segment(self) -> None:
        """A model name comes from configuration, and configuration reaches
        production. A slash would silently retarget the request."""
        self.assertIn("/models/gemini-x:generateContent", self.provider.endpoint_for("gemini-x"))
        for bad in ("../admin", "a/b", "a?key=x", "a#frag", ""):
            with self.subTest(model=bad), self.assertRaises(ProviderInvalidRequestError):
                self.provider.endpoint_for(bad)

    def test_the_credential_travels_in_a_header_not_the_url(self) -> None:
        """A key in a query string is logged by every proxy in between."""
        self.transport.queue([gemini_ok()])
        self.provider.complete(request(), "m")
        call = self.transport.calls[0]
        self.assertEqual(call["headers"]["x-goog-api-key"], "k")
        self.assertNotIn("k", call["url"].split("?")[-1] if "?" in call["url"] else "")


# ====================================================== response normalization


class ResponseNormalization(unittest.TestCase):
    def test_anthropic_usage_metadata_is_read(self) -> None:
        transport = FakeTransport.returning(anthropic_ok())
        result = AnthropicProvider(api_key="k", transport=transport).complete(request(), "m")
        self.assertEqual(result.input_tokens, 120)
        self.assertEqual(result.output_tokens, 8)
        self.assertEqual(result.content, "OBSERVED")

    def test_gemini_usage_metadata_is_read(self) -> None:
        transport = FakeTransport.returning(gemini_ok())
        result = GeminiProvider(api_key="k", transport=transport).complete(request(), "m")
        self.assertEqual(result.input_tokens, 120)
        self.assertEqual(result.output_tokens, 8)

    def test_anthropic_tool_output_becomes_the_structured_result(self) -> None:
        transport = FakeTransport.returning(anthropic_ok(tool_input={"claim_type": "OBSERVED"}))
        result = AnthropicProvider(api_key="k", transport=transport).complete(
            request(response_schema=SCHEMA), "m"
        )
        self.assertEqual(result.structured, {"claim_type": "OBSERVED"})

    def test_gemini_json_mode_output_is_parsed(self) -> None:
        transport = FakeTransport.returning(gemini_ok(json.dumps({"claim_type": "OBSERVED"})))
        result = GeminiProvider(api_key="k", transport=transport).complete(
            request(response_schema=SCHEMA), "m"
        )
        self.assertEqual(result.structured, {"claim_type": "OBSERVED"})

    def test_malformed_json_becomes_no_structured_output_not_an_exception(self) -> None:
        """It must reach the gateway as a SCHEMA failure, which is where a
        possible injection is meant to surface, rather than as a parse error
        the adapter swallowed or a crash the caller cannot classify."""
        transport = FakeTransport.returning(gemini_ok("this is not json"))
        result = GeminiProvider(api_key="k", transport=transport).complete(
            request(response_schema=SCHEMA), "m"
        )
        self.assertIsNone(result.structured)

    def test_a_provider_never_prices_its_own_call(self) -> None:
        """§15: pricing is versioned configuration, not a number a provider
        module decides. Both adapters report zero and let the gateway apply the
        table, so a tariff can never enter through a provider."""
        providers = (
            AnthropicProvider(api_key="k", transport=FakeTransport.returning(anthropic_ok())),
            GeminiProvider(api_key="k", transport=FakeTransport.returning(gemini_ok())),
        )
        for provider in providers:
            with self.subTest(provider=provider.name):
                self.assertEqual(provider.complete(request(), "m").cost_units, 0.0)


# ================================================================ error mapping


class ErrorMapping(unittest.TestCase):
    CASES = [
        (401, ProviderAuthenticationError, ErrorCategory.AUTHENTICATION, False),
        (403, ProviderAuthenticationError, ErrorCategory.AUTHENTICATION, False),
        (400, ProviderInvalidRequestError, ErrorCategory.INVALID_REQUEST, False),
        (404, ProviderInvalidRequestError, ErrorCategory.INVALID_REQUEST, False),
        (413, ProviderInvalidRequestError, ErrorCategory.INVALID_REQUEST, False),
        (429, ProviderRateLimitedError, ErrorCategory.RATE_LIMITED, True),
        (408, ProviderTimeoutError, ErrorCategory.TIMEOUT, True),
        (500, ProviderTemporaryError, ErrorCategory.TEMPORARY, True),
        (503, ProviderTemporaryError, ErrorCategory.TEMPORARY, True),
        (529, ProviderTemporaryError, ErrorCategory.TEMPORARY, True),
    ]

    def test_both_providers_map_statuses_to_the_same_categories(self) -> None:
        """§21: a business service branches on the category, so the two
        providers must agree about what a 429 means."""
        for status, expected_type, expected_category, retryable in self.CASES:
            for factory in (AnthropicProvider, GeminiProvider):
                with self.subTest(status=status, provider=factory.__name__):
                    transport = FakeTransport.returning(error_response(status, "boom"))
                    provider = factory(api_key="k", transport=transport)
                    with self.assertRaises(expected_type) as ctx:
                        provider.complete(request(), "m")
                    self.assertIs(category_of(ctx.exception), expected_category)
                    self.assertIs(is_retryable(ctx.exception), retryable)

    def test_a_rate_limit_carries_retry_after_when_the_provider_sends_it(self) -> None:
        transport = FakeTransport.returning(error_response(429, "slow down", {"retry-after": "12"}))
        with self.assertRaises(ProviderRateLimitedError) as ctx:
            AnthropicProvider(api_key="k", transport=transport).complete(request(), "m")
        self.assertEqual(ctx.exception.retry_after_seconds, 12.0)

    def test_a_transport_timeout_becomes_a_timeout_category(self) -> None:
        transport = FakeTransport.returning(TimeoutError("too slow"))
        with self.assertRaises(ProviderTimeoutError) as ctx:
            AnthropicProvider(api_key="k", transport=transport).complete(request(), "m")
        self.assertIs(category_of(ctx.exception), ErrorCategory.TIMEOUT)

    def test_a_transport_failure_is_temporary_and_retryable(self) -> None:
        transport = FakeTransport.returning(TransportError("connection reset"))
        with self.assertRaises(ProviderTemporaryError) as ctx:
            GeminiProvider(api_key="k", transport=transport).complete(request(), "m")
        self.assertTrue(is_retryable(ctx.exception))

    def test_a_missing_credential_fails_before_any_request_is_sent(self) -> None:
        transport = FakeTransport()
        for factory in (AnthropicProvider, GeminiProvider):
            with self.subTest(provider=factory.__name__):
                provider = factory(api_key="", transport=transport)
                with self.assertRaises(ProviderAuthenticationError):
                    provider.complete(request(), "m")
        self.assertEqual(transport.calls, [], "no request may be sent without a credential")

    def test_the_credential_never_appears_in_an_error_message(self) -> None:
        secret = "sk-do-not-leak-this"  # noqa: S105 - a fixture, not a credential
        transport = FakeTransport.returning(error_response(500, "internal"))
        with self.assertRaises(ProviderTemporaryError) as ctx:
            AnthropicProvider(api_key=secret, transport=transport).complete(request(), "m")
        self.assertNotIn(secret, str(ctx.exception))


# ============================================================== tier selection


class TierSelection(unittest.TestCase):
    def test_neither_provider_offers_the_embedding_tier(self) -> None:
        """ADR-006 keeps embeddings on local BGE-M3. Advertising the tier here
        would let the router send the highest-volume operation in the system to
        a paid API."""
        for provider in (AnthropicProvider(api_key="k"), GeminiProvider(api_key="k")):
            with self.subTest(provider=provider.name):
                self.assertFalse(provider.supports(LlmTier.EMBEDDING_MODEL))
                self.assertTrue(provider.supports(LlmTier.STRONG_MODEL))

    def test_a_tier_bound_to_an_unsupported_provider_refuses(self) -> None:
        config = GatewayConfig(
            routing_version="v1",
            bindings={
                LlmTier.EMBEDDING_MODEL: TierBinding(LlmTier.EMBEDDING_MODEL, "anthropic", "m")
            },
        )
        gateway = LlmGateway(config=config)
        gateway.register(AnthropicProvider(api_key="k", transport=FakeTransport()))
        with self.assertRaises(Exception) as ctx:
            gateway.resolve(LlmTier.EMBEDDING_MODEL)
        self.assertIn("does not support", str(ctx.exception))


# ====================================================== gateway retry contract


class RetryPolicyThroughTheGateway(unittest.TestCase):
    def _gateway(self, transport: FakeTransport) -> tuple[LlmGateway, AnthropicProvider]:
        provider = AnthropicProvider(api_key="k", transport=transport)
        config = GatewayConfig(
            routing_version="v1",
            bindings={
                LlmTier.BALANCED_MODEL: TierBinding(LlmTier.BALANCED_MODEL, "anthropic", "m")
            },
        )
        gateway = LlmGateway(config=config)
        gateway.register(provider)
        return gateway, provider

    def test_a_rate_limit_is_retried_and_can_succeed(self) -> None:
        transport = FakeTransport.returning(error_response(429, "slow down"), anthropic_ok())
        gateway, _ = self._gateway(transport)
        response = gateway.complete(request(max_retries=2))
        self.assertEqual(response.usage.retries, 1)
        self.assertEqual(len(transport.calls), 2)

    def test_an_authentication_error_is_never_retried(self) -> None:
        """§22. It costs the same on the second attempt, tells you nothing new,
        and repeated failed auth is what trips a provider's abuse detection."""
        transport = FakeTransport.returning(error_response(401, "bad key"))
        gateway, _ = self._gateway(transport)
        with self.assertRaises(ProviderAuthenticationError):
            gateway.complete(request(max_retries=5))
        self.assertEqual(len(transport.calls), 1)

    def test_an_invalid_request_is_never_retried(self) -> None:
        transport = FakeTransport.returning(error_response(400, "context too long"))
        gateway, _ = self._gateway(transport)
        with self.assertRaises(ProviderInvalidRequestError):
            gateway.complete(request(max_retries=5))
        self.assertEqual(len(transport.calls), 1)

    def test_retries_are_bounded(self) -> None:
        transport = FakeTransport.returning(*[error_response(503, "down") for _ in range(10)])
        gateway, _ = self._gateway(transport)
        with self.assertRaises(ProviderTemporaryError):
            gateway.complete(request(max_retries=2))
        self.assertEqual(len(transport.calls), 3, "one attempt plus two retries")


if __name__ == "__main__":
    unittest.main()
