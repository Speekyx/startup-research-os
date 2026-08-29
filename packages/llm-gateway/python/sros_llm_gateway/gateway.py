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
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from .budget import BudgetLedger
from .config import GatewayConfig
from .pricing import PricingTable
from .types import (
    RETRYABLE_CATEGORIES,
    BudgetExhaustedError,
    ErrorCategory,
    LlmRequest,
    LlmResponse,
    LlmTier,
    NoProviderAvailableError,
    ProviderOutcome,
    SchemaValidationError,
    UsageMetadata,
    category_of,
)

__all__ = ["Provider", "ProviderResult", "LlmGateway", "TelemetrySink"]

# Called once per completed or failed request with the full usage record.
# A sink rather than a logger call: the orchestrator needs the same record to
# write a budget entry, and producing it twice from two places is how the two
# would disagree.
TelemetrySink = Callable[[UsageMetadata], None]


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
    pricing: PricingTable = field(default_factory=PricingTable)
    telemetry: TelemetrySink | None = None
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

        while True:
            try:
                result = provider.complete(request, model)
                break
            except Exception as exc:
                category = category_of(exc)

                # Mission 0.4 §22. Retry only what a retry can fix. An
                # authentication error, an invalid request or a deterministic
                # rejection costs exactly the same on the second attempt and
                # tells you nothing new; retrying burns budget and hides the bug.
                if category not in RETRYABLE_CATEGORIES or retries >= request.max_retries:
                    self._emit(
                        self._usage(
                            request,
                            provider.name,
                            model,
                            started,
                            retries,
                            outcome=_outcome_for(category),
                            error_category=category,
                        )
                    )
                    # The ORIGINAL error propagates, with its category intact.
                    # Wrapping a timeout as "no provider available" would tell a
                    # caller the tier could not be served when in fact it was
                    # served and was slow -- two different operational problems.
                    raise

                retries += 1

        # Schema validation sits OUTSIDE the retry loop on purpose. A schema
        # failure may signal prompt injection (llm-reasoning-rules.md §7), so it
        # surfaces rather than being retried or routed into a fallback.
        try:
            structured = self._validate_structured(request, result)
        except SchemaValidationError:
            self._emit(
                self._usage(
                    request,
                    provider.name,
                    model,
                    started,
                    retries,
                    outcome=ProviderOutcome.SCHEMA_FAILURE,
                    error_category=ErrorCategory.SCHEMA_FAILURE,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                )
            )
            raise

        # Cost comes from the versioned pricing table, never from a constant in
        # business logic (Mission 0.4 §15). A provider's self-reported cost is
        # used only where the table says nothing, and is marked as such.
        cost_units, priced = self.pricing.cost_for(
            provider.name, model, result.input_tokens, result.output_tokens
        )
        if not priced and result.cost_units:
            cost_units, priced = result.cost_units, True

        usage = self._usage(
            request,
            provider.name,
            model,
            started,
            retries,
            outcome=ProviderOutcome.SUCCESS,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_units=cost_units,
            priced=priced,
        )
        ledger.record(request.workspace_id, request.research_session_id, cost_units)
        self._emit(usage)
        return LlmResponse(
            content=result.content,
            structured=structured,
            usage=usage,
            prompt_template_id=request.prompt_template_id,
            prompt_template_version=request.prompt_template_version,
        )

    # -- telemetry ----------------------------------------------------------

    def _usage(
        self,
        request: LlmRequest,
        provider_name: str,
        model: str,
        started: float,
        retries: int,
        *,
        outcome: ProviderOutcome,
        error_category: ErrorCategory | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_units: float = 0.0,
        priced: bool = False,
    ) -> UsageMetadata:
        """Build the record for one attempt sequence.

        Emitted for failures as well as successes: a provider that fails
        expensively and invisibly is exactly what the cost-ladder metric in
        ADR-006 exists to make visible.
        """
        return UsageMetadata(
            provider=provider_name,
            model=model,
            tier=request.tier,
            routing_version=self.config.routing_version,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_units=cost_units,
            latency_ms=(time.monotonic() - started) * 1000,
            retries=retries,
            outcome=outcome,
            prompt_template_id=request.prompt_template_id,
            prompt_template_version=request.prompt_template_version,
            pricing_version=self.pricing.version,
            priced=priced,
            workspace_id=request.workspace_id,
            research_session_id=request.research_session_id,
            correlation_id=request.correlation_id,
            task=request.task,
            error_category=error_category,
        )

    def _emit(self, usage: UsageMetadata) -> None:
        if self.telemetry is not None:
            self.telemetry(usage)

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


def _outcome_for(category: ErrorCategory) -> ProviderOutcome:
    """Map an internal category onto the coarser outcome recorded on usage."""
    if category is ErrorCategory.TIMEOUT:
        return ProviderOutcome.TIMEOUT
    if category is ErrorCategory.RATE_LIMITED:
        return ProviderOutcome.RATE_LIMITED
    if category is ErrorCategory.SCHEMA_FAILURE:
        return ProviderOutcome.SCHEMA_FAILURE
    return ProviderOutcome.ERROR
