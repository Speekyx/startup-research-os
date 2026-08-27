"""LLM Gateway infrastructure tests.

No network, no API key, no bill: the gateway's routing, budget, retry and
validation paths are exercised through test doubles.

ADR-006 governs the expectations here.
"""

from __future__ import annotations

import pathlib
import unittest

from sros_contracts import LlmTier
from sros_llm_gateway import (
    BudgetExhaustedError,
    BudgetLedger,
    BudgetLimits,
    GatewayConfig,
    LlmGateway,
    LlmRequest,
    NoProviderAvailableError,
    SchemaValidationError,
    TierBinding,
    load_config_from_env,
)
from sros_llm_gateway.providers import EchoProvider, FailingProvider

WORKSPACE = "00000000-0000-4000-8000-000000000001"
SESSION = "00000000-0000-4000-8000-0000000000aa"


def make_config(**overrides: object) -> GatewayConfig:
    bindings = {
        LlmTier.FAST_MODEL: TierBinding(LlmTier.FAST_MODEL, "fake-echo", "fake-fast-v1"),
        LlmTier.BALANCED_MODEL: TierBinding(
            LlmTier.BALANCED_MODEL, "fake-echo", "fake-balanced-v1"
        ),
        LlmTier.STRONG_MODEL: TierBinding(LlmTier.STRONG_MODEL, "fake-echo", "fake-strong-v1"),
        LlmTier.EMBEDDING_MODEL: TierBinding(LlmTier.EMBEDDING_MODEL, "local", "bge-m3"),
    }
    return GatewayConfig(
        routing_version="test-1",
        bindings=bindings,
        budgets=BudgetLimits(**overrides) if overrides else BudgetLimits(),
    )


def make_request(tier: LlmTier = LlmTier.FAST_MODEL, **kwargs: object) -> LlmRequest:
    defaults: dict[str, object] = {
        "tier": tier,
        "task": "classify.signal",
        "prompt_template_id": "signal-classify",
        "prompt_template_version": "1.0.0",
        "workspace_id": WORKSPACE,
        "research_session_id": SESSION,
        "correlation_id": "corr-1",
    }
    defaults.update(kwargs)
    return LlmRequest(**defaults)  # type: ignore[arg-type]


class RequestContract(unittest.TestCase):
    def test_workspace_id_is_required(self) -> None:
        with self.assertRaises(ValueError):
            make_request(workspace_id="")

    def test_prompt_must_be_a_versioned_template(self) -> None:
        """Prompts are versioned artifacts, never assembled at a call site."""
        with self.assertRaises(ValueError):
            make_request(prompt_template_version="")

    def test_timeout_is_mandatory_and_positive(self) -> None:
        with self.assertRaises(ValueError):
            make_request(timeout_seconds=0)

    def test_request_carries_no_provider_or_model_field(self) -> None:
        """The abstraction is only useful if callers cannot name a provider."""
        fields = set(LlmRequest.__dataclass_fields__)
        self.assertNotIn("provider", fields)
        self.assertNotIn("model", fields)


class TierResolution(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = EchoProvider()
        self.gateway = LlmGateway(config=make_config())
        self.gateway.register(self.provider)

    def test_each_tier_resolves_to_its_configured_model(self) -> None:
        expected = {
            LlmTier.FAST_MODEL: "fake-fast-v1",
            LlmTier.BALANCED_MODEL: "fake-balanced-v1",
            LlmTier.STRONG_MODEL: "fake-strong-v1",
        }
        for tier, model in expected.items():
            with self.subTest(tier=tier.value):
                _, resolved = self.gateway.resolve(tier)
                self.assertEqual(resolved, model)

    def test_unconfigured_tier_refuses_rather_than_downgrading(self) -> None:
        """Serving STRONG from FAST gives a worse answer that looks identical."""
        config = make_config()
        config.bindings[LlmTier.STRONG_MODEL] = TierBinding(LlmTier.STRONG_MODEL, None, None)
        gateway = LlmGateway(config=config)
        gateway.register(EchoProvider())
        with self.assertRaises(NoProviderAvailableError):
            gateway.resolve(LlmTier.STRONG_MODEL)

    def test_open_circuit_removes_a_provider_from_routing(self) -> None:
        self.gateway.open_circuit("fake-echo")
        with self.assertRaises(NoProviderAvailableError):
            self.gateway.resolve(LlmTier.FAST_MODEL)
        self.gateway.close_circuit("fake-echo")
        self.gateway.resolve(LlmTier.FAST_MODEL)

    def test_all_four_logical_tiers_exist(self) -> None:
        self.assertEqual(
            {t.value for t in LlmTier},
            {"FAST_MODEL", "BALANCED_MODEL", "STRONG_MODEL", "EMBEDDING_MODEL"},
        )


class Completion(unittest.TestCase):
    def test_response_records_full_reproducibility_metadata(self) -> None:
        gateway = LlmGateway(config=make_config())
        gateway.register(EchoProvider())
        response = gateway.complete(make_request())

        self.assertEqual(response.usage.provider, "fake-echo")
        self.assertEqual(response.usage.model, "fake-fast-v1")
        self.assertEqual(response.usage.tier, LlmTier.FAST_MODEL)
        self.assertEqual(response.usage.routing_version, "test-1")
        self.assertEqual(response.prompt_template_version, "1.0.0")
        self.assertIn("llm_cost_units", response.usage.to_log_fields())

    def test_retries_then_succeeds(self) -> None:
        gateway = LlmGateway(config=make_config())
        config = gateway.config
        config.bindings[LlmTier.FAST_MODEL] = TierBinding(LlmTier.FAST_MODEL, "fake-failing", "m")
        gateway.register(FailingProvider(failures_before_success=1))
        response = gateway.complete(make_request(max_retries=2))
        self.assertEqual(response.content, "recovered")
        self.assertEqual(response.usage.retries, 1)

    def test_exhausted_retries_fail_rather_than_fabricate(self) -> None:
        gateway = LlmGateway(config=make_config())
        gateway.config.bindings[LlmTier.FAST_MODEL] = TierBinding(
            LlmTier.FAST_MODEL, "fake-failing", "m"
        )
        gateway.register(FailingProvider(failures_before_success=99))
        with self.assertRaises(NoProviderAvailableError):
            gateway.complete(make_request(max_retries=1))


class StructuredOutput(unittest.TestCase):
    def test_missing_structured_output_is_a_schema_failure(self) -> None:
        gateway = LlmGateway(config=make_config())
        gateway.register(EchoProvider(structured=None))
        with self.assertRaises(SchemaValidationError):
            gateway.complete(make_request(response_schema={"required": ["claim_type"]}))

    def test_missing_required_field_is_a_schema_failure(self) -> None:
        gateway = LlmGateway(config=make_config())
        gateway.register(EchoProvider(structured={"other": 1}))
        with self.assertRaises(SchemaValidationError):
            gateway.complete(make_request(response_schema={"required": ["claim_type"]}))

    def test_valid_structured_output_passes_through(self) -> None:
        gateway = LlmGateway(config=make_config())
        gateway.register(EchoProvider(structured={"claim_type": "HYPOTHESIS"}))
        response = gateway.complete(make_request(response_schema={"required": ["claim_type"]}))
        self.assertEqual(response.structured, {"claim_type": "HYPOTHESIS"})

    def test_schema_failure_is_not_retried_into_a_fallback(self) -> None:
        """A schema failure may signal prompt injection (§7). It surfaces."""
        provider = EchoProvider(structured=None)
        gateway = LlmGateway(config=make_config())
        gateway.register(provider)
        with self.assertRaises(SchemaValidationError):
            gateway.complete(make_request(response_schema={"required": ["x"]}, max_retries=3))
        self.assertEqual(len(provider.calls), 1, "must not retry a schema failure")


class Budget(unittest.TestCase):
    def test_budget_exhaustion_refuses_before_dispatch(self) -> None:
        ledger = BudgetLedger(BudgetLimits(max_cost_units_per_session=2.0))
        provider = EchoProvider(cost_units=1.0)
        gateway = LlmGateway(config=make_config(), ledger=ledger)
        gateway.register(provider)

        gateway.complete(make_request())
        gateway.complete(make_request())
        with self.assertRaises(BudgetExhaustedError):
            gateway.complete(make_request())

        self.assertEqual(len(provider.calls), 2, "refusal must happen before dispatch")

    def test_budget_exhaustion_message_states_the_lifecycle_rule(self) -> None:
        """Exhaustion is COMPLETED with reduced completeness, not FAILED."""
        ledger = BudgetLedger(BudgetLimits(max_llm_calls_per_session=0))
        gateway = LlmGateway(config=make_config(), ledger=ledger)
        gateway.register(EchoProvider())
        with self.assertRaises(BudgetExhaustedError) as ctx:
            gateway.complete(make_request())
        self.assertIn("does not fail", str(ctx.exception))

    def test_workspace_daily_cap_is_enforced(self) -> None:
        ledger = BudgetLedger(
            BudgetLimits(
                max_cost_units_per_session=1000,
                max_llm_calls_per_session=1000,
                max_cost_units_per_workspace_day=1.0,
            )
        )
        gateway = LlmGateway(config=make_config(), ledger=ledger)
        gateway.register(EchoProvider(cost_units=1.0))
        gateway.complete(make_request())
        with self.assertRaises(BudgetExhaustedError):
            gateway.complete(make_request(research_session_id="another-session"))


class ConfigurationFromEnv(unittest.TestCase):
    def test_no_model_name_is_hard_coded(self) -> None:
        """Models change faster than release cycles (ADR-006)."""
        config = load_config_from_env(
            {
                "LLM_TIER_STRONG_PROVIDER": "anthropic",
                "LLM_TIER_STRONG_MODEL": "whatever-the-current-model-is",
                "LLM_ROUTING_VERSION": "9.9.9",
            }
        )
        binding = config.binding_for(LlmTier.STRONG_MODEL)
        self.assertEqual(binding.model, "whatever-the-current-model-is")
        self.assertEqual(config.routing_version, "9.9.9")

    def test_unconfigured_tiers_are_permitted(self) -> None:
        config = load_config_from_env({})
        self.assertFalse(config.binding_for(LlmTier.FAST_MODEL).configured)

    def test_null_provider_counts_as_unconfigured(self) -> None:
        config = load_config_from_env({"LLM_TIER_FAST_PROVIDER": "null"})
        self.assertFalse(config.binding_for(LlmTier.FAST_MODEL).configured)


class ProviderIndependence(unittest.TestCase):
    """The abstraction is only real if the SDKs cannot leak out of providers/."""

    FORBIDDEN = ("anthropic", "openai", "google.generativeai", "genai", "openrouter", "cohere")

    def test_no_provider_sdk_import_outside_providers_package(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[1] / "sros_llm_gateway"
        offenders: list[str] = []
        for path in sorted(root.glob("*.py")):
            text = path.read_text(encoding="utf-8").lower()
            for line in text.splitlines():
                stripped = line.strip()
                if not (stripped.startswith("import ") or stripped.startswith("from ")):
                    continue
                for sdk in self.FORBIDDEN:
                    if sdk in stripped:
                        offenders.append(f"{path.name}: {stripped}")
        self.assertEqual(offenders, [], f"provider SDK leaked into the gateway core: {offenders}")

    def test_gateway_core_never_names_a_provider_in_code(self) -> None:
        """Tokenized, so a provider named in a docstring is not a false positive.

        What matters is that no identifier, attribute or literal in executable
        code names a vendor. Prose may explain the abstraction.
        """
        import tokenize

        root = pathlib.Path(__file__).resolve().parents[1] / "sros_llm_gateway"
        offenders: list[str] = []
        for module in ("gateway.py", "types.py", "budget.py", "config.py"):
            path = root / module
            with tokenize.open(path) as handle:
                for token in tokenize.generate_tokens(handle.readline):
                    if token.type in (tokenize.COMMENT, tokenize.STRING):
                        continue
                    lowered = token.string.lower()
                    for sdk in self.FORBIDDEN:
                        if sdk in lowered:
                            offenders.append(f"{module}:{token.start[0]} {token.string}")
        self.assertEqual(offenders, [], f"provider named in gateway code: {offenders}")


if __name__ == "__main__":
    unittest.main()
