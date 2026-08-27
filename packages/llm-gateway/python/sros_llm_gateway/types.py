"""LLM Gateway contracts.

ADR-006. Business services request a **logical tier**, never a provider or a
model name. Nothing in this module names Anthropic, Gemini or OpenAI: that is
the whole point of the abstraction, and it is asserted by a test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

# The tier enum comes from the generated contract vocabulary, so the gateway and
# the domain cannot drift on what a tier is.
from sros_contracts import LlmTier

__all__ = [
    "LlmTier",
    "LlmRequest",
    "LlmResponse",
    "UsageMetadata",
    "ProviderOutcome",
    "GatewayError",
    "BudgetExhaustedError",
    "SchemaValidationError",
    "NoProviderAvailableError",
    "ProviderTimeoutError",
]


class GatewayError(RuntimeError):
    """Base class for every gateway failure."""


class BudgetExhaustedError(GatewayError):
    """The run or workspace budget is spent.

    This is a **first-class result**, not a crash. A session that exhausts its
    budget reaches COMPLETED with reduced Research Completeness -- never FAILED
    (Ontology V2 §15, ADR-006).
    """


class SchemaValidationError(GatewayError):
    """The provider returned output that does not match the requested schema.

    Treated as a possible prompt-injection signal, never retried blindly into a
    fallback provider (llm-reasoning-rules.md §7).
    """


class NoProviderAvailableError(GatewayError):
    """No configured provider can serve the tier, or all candidates failed."""


class ProviderTimeoutError(GatewayError):
    """A request exceeded its explicit timeout. There are no unbounded calls."""


class ProviderOutcome(StrEnum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    SCHEMA_FAILURE = "SCHEMA_FAILURE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class LlmRequest:
    """What a business service asks for.

    It carries a tier, a task identifier and a versioned prompt template. It
    carries **no provider, no model name and no provider-specific parameter** --
    a leaky abstraction that passed those through would recreate the coupling it
    exists to prevent.
    """

    tier: LlmTier
    task: str
    prompt_template_id: str
    prompt_template_version: str
    variables: dict[str, object] = field(default_factory=dict)
    response_schema: dict[str, object] | None = None

    # Budget and correlation context. workspace_id is required (ADR-005).
    workspace_id: str = ""
    research_session_id: str = ""
    correlation_id: str = ""

    timeout_seconds: float = 60.0
    max_retries: int = 2

    # Capability requirements, declared by need rather than by provider name.
    requires_structured_output: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.tier, LlmTier):
            raise ValueError(f"tier must be an LlmTier, got {self.tier!r}")
        if not self.workspace_id:
            raise ValueError(
                "workspace_id is required on every LLM request: cost is attributed "
                "per tenant and per session (ADR-005, ADR-006)"
            )
        if not self.prompt_template_id or not self.prompt_template_version:
            raise ValueError(
                "prompts are versioned template artifacts, never assembled ad hoc "
                "at a call site (ADR-006)"
            )
        if self.timeout_seconds <= 0:
            raise ValueError("every request carries an explicit positive timeout")


@dataclass(frozen=True)
class UsageMetadata:
    """Cost and reproducibility record attached to every response.

    llm-reasoning-rules.md §9: without this, a model upgrade silently
    invalidates every historical signal with no way to tell which ones.
    """

    provider: str
    model: str
    tier: LlmTier
    routing_version: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_units: float = 0.0
    latency_ms: float = 0.0
    retries: int = 0
    fallbacks: int = 0
    outcome: ProviderOutcome = ProviderOutcome.SUCCESS

    def to_log_fields(self) -> dict[str, object]:
        return {
            "llm_provider": self.provider,
            "llm_model": self.model,
            "llm_tier": self.tier.value,
            "llm_routing_version": self.routing_version,
            "llm_input_tokens": self.input_tokens,
            "llm_output_tokens": self.output_tokens,
            "llm_cost_units": self.cost_units,
            "llm_latency_ms": self.latency_ms,
            "llm_retries": self.retries,
            "llm_fallbacks": self.fallbacks,
            "llm_outcome": self.outcome.value,
        }


@dataclass(frozen=True)
class LlmResponse:
    """A validated response plus its full reproducibility record.

    `usage.provider` is recorded because a fallback changes the model, and
    therefore changes the result. Comparing outputs across a silent fallback is
    comparing two different models (ADR-006).
    """

    content: str
    structured: dict[str, object] | None
    usage: UsageMetadata
    prompt_template_id: str
    prompt_template_version: str
