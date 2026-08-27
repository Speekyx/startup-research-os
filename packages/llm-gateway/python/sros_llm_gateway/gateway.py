"""The LLM Gateway.

ADR-006. This is the single chokepoint where budget enforcement, prompt
versioning, model-version recording and structured-output validation happen.
Implemented once here, they cannot be skipped; implemented per call site, each
is one hurried commit from being forgotten.

**No provider implementation lives here.** Mission 0.2 delivers interfaces,
configuration and test doubles. No real external API call is made.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol

from .budget import BudgetLedger
from .config import GatewayConfig
from .types import (
    BudgetExhaustedError,
    LlmRequest,
    LlmResponse,
    LlmTier,
    NoProviderAvailableError,
    ProviderOutcome,
    ProviderTimeoutError,
    SchemaValidationError,
    UsageMetadata,
)

__all__ = ["Provider", "ProviderResult", "LlmGateway"]


@dataclass(frozen=True)
class ProviderResult:
    """What a provider returns before the gateway validates and records it."""

    content: str
    structured: dict[str, object] | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_units: float = 0.0


class Provider(Protocol):
    """The only surface a provider implementation must satisfy.

    Deliberately narrow. Provider-specific features that cannot be expressed
    across providers are not surfaced: the second service that used such a
    parameter would have silently pinned the whole system to one vendor.
    """

    name: str

    def supports(self, tier: LlmTier) -> bool: ...

    def complete(self, request: LlmRequest, model: str) -> ProviderResult: ...


@dataclass
class LlmGateway:
    """Routes a logical tier to a provider, enforcing the ADR-006 obligations."""

    config: GatewayConfig
    providers: dict[str, Provider] = field(default_factory=dict)
    ledger: BudgetLedger | None = None
    _open_circuits: set[str] = field(default_factory=set, init=False)

    def register(self, provider: Provider) -> None:
        self.providers[provider.name] = provider

    # -- routing ------------------------------------------------------------

    def resolve(self, tier: LlmTier) -> tuple[Provider, str]:
        """Resolve a tier to a concrete provider and model.

        Raises NoProviderAvailableError rather than silently downgrading the tier.
        Serving a STRONG_MODEL request from FAST_MODEL because the strong
        provider is down produces a worse answer that looks identical.
        """
        binding = self.config.binding_for(tier)
        if not binding.configured or binding.model is None:
            raise NoProviderAvailableError(
                f"tier {tier.value} has no configured provider. "
                "Set the LLM_TIER_* environment variables (ADR-006)."
            )
        provider = self.providers.get(binding.provider or "")
        if provider is None:
            raise NoProviderAvailableError(
                f"provider {binding.provider!r} for tier {tier.value} is not registered"
            )
        if provider.name in self._open_circuits:
            raise NoProviderAvailableError(f"provider {provider.name} circuit is open")
        if not provider.supports(tier):
            raise NoProviderAvailableError(
                f"provider {provider.name} does not support tier {tier.value}"
            )
        return provider, binding.model

    def open_circuit(self, provider_name: str) -> None:
        self._open_circuits.add(provider_name)

    def close_circuit(self, provider_name: str) -> None:
        self._open_circuits.discard(provider_name)

    # -- execution ----------------------------------------------------------

    def complete(self, request: LlmRequest) -> LlmResponse:
        ledger = self.ledger or BudgetLedger(self.config.budgets)

        # Budget is checked BEFORE dispatch. Refusal is a first-class result:
        # the caller turns it into reduced Research Completeness, never a
        # fabricated answer (ADR-006, Ontology V2 §15).
        if not ledger.can_spend(request.workspace_id, request.research_session_id):
            raise BudgetExhaustedError(
                f"budget exhausted for session {request.research_session_id!r}. "
                "The session completes with reduced Research Completeness; it does not fail."
            )

        provider, model = self.resolve(request.tier)

        started = time.monotonic()
        retries = 0
        last_error: Exception | None = None

        while retries <= request.max_retries:
            try:
                result = provider.complete(request, model)
            except TimeoutError as exc:
                last_error = ProviderTimeoutError(str(exc))
                retries += 1
                continue
            except Exception as exc:  # provider-specific failures are opaque here
                last_error = exc
                retries += 1
                continue

            structured = self._validate_structured(request, result)

            latency_ms = (time.monotonic() - started) * 1000
            usage = UsageMetadata(
                provider=provider.name,
                model=model,
                tier=request.tier,
                routing_version=self.config.routing_version,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_units=result.cost_units,
                latency_ms=latency_ms,
                retries=retries,
                outcome=ProviderOutcome.SUCCESS,
            )
            ledger.record(request.workspace_id, request.research_session_id, result.cost_units)
            return LlmResponse(
                content=result.content,
                structured=structured,
                usage=usage,
                prompt_template_id=request.prompt_template_id,
                prompt_template_version=request.prompt_template_version,
            )

        raise NoProviderAvailableError(
            f"tier {request.tier.value} exhausted {retries} attempt(s) on "
            f"{provider.name}: {last_error}"
        )

    @staticmethod
    def _validate_structured(
        request: LlmRequest, result: ProviderResult
    ) -> dict[str, object] | None:
        """Structured-output validation hook.

        A schema failure is NOT retried into a fallback provider: it may signal
        prompt injection (llm-reasoning-rules.md §7), so it is surfaced and
        logged rather than routed around.

        Full JSON Schema validation arrives with the first real provider; this
        enforces the shape contract the callers depend on.
        """
        if request.response_schema is None:
            return result.structured

        if result.structured is None:
            raise SchemaValidationError(
                f"task {request.task!r} requested structured output but the provider "
                "returned none. Not retried into a fallback: a schema failure may "
                "indicate prompt injection."
            )

        required = request.response_schema.get("required", [])
        if isinstance(required, list):
            missing = [key for key in required if key not in result.structured]
            if missing:
                raise SchemaValidationError(
                    f"task {request.task!r} structured output is missing required fields: {missing}"
                )
        return result.structured
