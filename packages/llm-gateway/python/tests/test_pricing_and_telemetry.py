"""Pricing configuration and usage telemetry.

Mission 0.4 §15 (pricing is versioned configuration) and §23 (what a usage
record carries, and what it must never carry).
"""

from __future__ import annotations

import json
import unittest

from sros_contracts import LlmTier
from sros_llm_gateway import (
    UNPRICED_VERSION,
    ErrorCategory,
    FakeTransport,
    GatewayConfig,
    HttpResponse,
    LlmGateway,
    LlmRequest,
    ModelPrice,
    PricingTable,
    ProviderTemporaryError,
    RenderedPrompt,
    TierBinding,
    UntrustedText,
    UsageMetadata,
    load_pricing_from_env,
)
from sros_llm_gateway.providers import AnthropicProvider, EchoProvider

WORKSPACE = "00000000-0000-4000-8000-000000000001"
SESSION = "00000000-0000-4000-8000-0000000000aa"
SECRET_CONTENT = "a customer complaint that must never reach a log"


def request(**kwargs: object) -> LlmRequest:
    defaults: dict[str, object] = {
        "tier": LlmTier.FAST_MODEL,
        "task": "classify.signal",
        "prompt_template_id": "signal-classify",
        "prompt_template_version": "2.1.0",
        "workspace_id": WORKSPACE,
        "research_session_id": SESSION,
        "correlation_id": "corr-xyz",
        "prompt": RenderedPrompt(
            system_instructions="Classify.",
            untrusted=(UntrustedText(SECRET_CONTENT, "review-1"),),
        ),
    }
    defaults.update(kwargs)
    return LlmRequest(**defaults)  # type: ignore[arg-type]


def gateway_with(provider_name: str, model: str, **kwargs: object) -> LlmGateway:
    config = GatewayConfig(
        routing_version="v1",
        bindings={LlmTier.FAST_MODEL: TierBinding(LlmTier.FAST_MODEL, provider_name, model)},
    )
    return LlmGateway(config=config, **kwargs)  # type: ignore[arg-type]


# ==================================================================== pricing


class Pricing(unittest.TestCase):
    def test_the_default_table_is_empty(self) -> None:
        """§15: no product price is invented. A plausible constant compiled in
        here would be wrong within months and would look authoritative."""
        table = PricingTable()
        self.assertTrue(table.is_empty)
        self.assertEqual(table.version, UNPRICED_VERSION)

    def test_an_unpriced_model_is_unpriced_not_free(self) -> None:
        """The distinction matters: reporting an unpriced call as costing zero
        shows every budget untouched while real money is spent."""
        cost, priced = PricingTable().cost_for("anthropic", "some-model", 1000, 1000)
        self.assertEqual(cost, 0.0)
        self.assertFalse(priced)

    def test_a_configured_price_is_applied_per_thousand_tokens(self) -> None:
        table = PricingTable(
            version="2026.08",
            prices={"p:m": ModelPrice(input_per_1k=3.0, output_per_1k=15.0)},
        )
        cost, priced = table.cost_for("p", "m", 2000, 1000)
        self.assertTrue(priced)
        self.assertAlmostEqual(cost, 6.0 + 15.0)

    def test_the_table_is_keyed_by_provider_and_model(self) -> None:
        """The same model name served by two providers has two prices; a table
        keyed on the model alone would apply one tariff to the other."""
        table = PricingTable(version="v", prices={"a:m": ModelPrice(1.0, 1.0)})
        self.assertTrue(table.cost_for("a", "m", 1000, 0)[1])
        self.assertFalse(table.cost_for("b", "m", 1000, 0)[1])

    def test_configuration_is_loaded_from_the_environment(self) -> None:
        table = load_pricing_from_env(
            {
                "LLM_PRICING_VERSION": "2026.08",
                "LLM_PRICING_JSON": json.dumps(
                    {"anthropic:m": {"input_per_1k": 3.0, "output_per_1k": 15.0}}
                ),
            }
        )
        self.assertEqual(table.version, "2026.08")
        self.assertIsNotNone(table.price_for("anthropic", "m"))

    def test_a_price_list_without_a_version_is_refused(self) -> None:
        """A spend record whose tariff cannot be identified cannot be audited."""
        with self.assertRaises(ValueError):
            load_pricing_from_env(
                {"LLM_PRICING_JSON": json.dumps({"a:m": {"input_per_1k": 1, "output_per_1k": 1}})}
            )

    def test_malformed_configuration_raises_rather_than_falling_back(self) -> None:
        """A silently ignored price list is worse than none: the operator
        believes budgets are enforced and they are not."""
        for bad in ("{not json", json.dumps({"nokey": {"input_per_1k": 1, "output_per_1k": 1}})):
            with self.subTest(config=bad[:20]), self.assertRaises(ValueError):
                load_pricing_from_env({"LLM_PRICING_VERSION": "v", "LLM_PRICING_JSON": bad})

    def test_a_negative_price_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            ModelPrice(input_per_1k=-1.0, output_per_1k=1.0)

    def test_no_provider_tariff_is_hard_coded_anywhere_in_the_package(self) -> None:
        """The guard behind §15: a number in a module is a decision nobody
        recorded making."""
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[1] / "sros_llm_gateway"
        offenders = [
            str(path.relative_to(root))
            for path in root.rglob("*.py")
            if "input_per_1k=" in path.read_text(encoding="utf-8")
            and path.name not in {"pricing.py"}
        ]
        self.assertEqual(
            offenders, [], f"a tariff leaked outside pricing configuration: {offenders}"
        )


# ================================================================== telemetry


class Telemetry(unittest.TestCase):
    def test_a_successful_call_emits_a_complete_usage_record(self) -> None:
        records: list[UsageMetadata] = []
        gateway = gateway_with(
            "fake-echo",
            "m",
            pricing=PricingTable(version="2026.08", prices={"fake-echo:m": ModelPrice(1.0, 2.0)}),
            telemetry=records.append,
        )
        gateway.register(EchoProvider())
        gateway.complete(request())

        self.assertEqual(len(records), 1)
        usage = records[0]
        self.assertEqual(usage.provider, "fake-echo")
        self.assertEqual(usage.tier, LlmTier.FAST_MODEL)
        self.assertEqual(usage.prompt_template_version, "2.1.0")
        self.assertEqual(usage.workspace_id, WORKSPACE)
        self.assertEqual(usage.research_session_id, SESSION)
        self.assertEqual(usage.correlation_id, "corr-xyz")
        self.assertEqual(usage.pricing_version, "2026.08")
        self.assertTrue(usage.priced)
        self.assertGreater(usage.latency_ms, 0)

    def test_an_unpriced_call_is_marked_as_such(self) -> None:
        records: list[UsageMetadata] = []
        gateway = gateway_with("fake-echo", "m", telemetry=records.append)
        gateway.register(EchoProvider(cost_units=0.0))
        gateway.complete(request())
        self.assertFalse(records[0].priced)
        self.assertEqual(records[0].pricing_version, UNPRICED_VERSION)

    def test_a_failure_is_also_recorded(self) -> None:
        """A provider that fails expensively and invisibly is what the
        cost-ladder metric in ADR-006 exists to make visible."""
        records: list[UsageMetadata] = []
        transport = FakeTransport.returning(
            HttpResponse(503, json.dumps({"error": {"message": "down"}}).encode("utf-8"))
        )
        gateway = gateway_with("anthropic", "m", telemetry=records.append)
        gateway.register(AnthropicProvider(api_key="k", transport=transport))

        with self.assertRaises(ProviderTemporaryError):
            gateway.complete(request(max_retries=0))

        self.assertEqual(len(records), 1)
        self.assertIs(records[0].error_category, ErrorCategory.TEMPORARY)

    def test_telemetry_carries_ids_and_never_content(self) -> None:
        """§23: no raw prompt text, no variables, no response body. Telemetry
        that carried them would put scraped source data into the log pipeline."""
        records: list[UsageMetadata] = []
        gateway = gateway_with("fake-echo", "m", telemetry=records.append)
        gateway.register(EchoProvider())
        gateway.complete(request(variables={"secret_variable": SECRET_CONTENT}))

        serialized = json.dumps(records[0].to_log_fields())
        self.assertNotIn(SECRET_CONTENT, serialized)
        self.assertNotIn("secret_variable", serialized)
        self.assertIn("correlation_id", serialized)
        self.assertIn("llm_prompt_template_version", serialized)

    def test_no_api_key_field_exists_on_a_usage_record(self) -> None:
        self.assertNotIn("api_key", UsageMetadata.__dataclass_fields__)

    def test_a_gateway_without_a_sink_still_works(self) -> None:
        gateway = gateway_with("fake-echo", "m")
        gateway.register(EchoProvider())
        self.assertTrue(gateway.complete(request()).content)


if __name__ == "__main__":
    unittest.main()
