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

from .prompts.rendering import RenderedPrompt

__all__ = [
    "LlmTier",
    "LlmRequest",
    "LlmResponse",
    "UsageMetadata",
    "ProviderOutcome",
    "ErrorCategory",
    "RETRYABLE_CATEGORIES",
    "GatewayError",
    "ProviderError",
    "BudgetExhaustedError",
    "SchemaValidationError",
    "NoProviderAvailableError",
    "ProviderTimeoutError",
    "ProviderRateLimitedError",
    "ProviderTemporaryError",
    "ProviderInvalidRequestError",
    "ProviderAuthenticationError",
    "category_of",
    "is_retryable",
]


class ErrorCategory(StrEnum):
    """The normalized failure vocabulary (Mission 0.4 §21).

    Business services branch on THESE, never on a vendor exception class. An
    `except anthropic.RateLimitError` in a service is a service pinned to one
    provider, and the pin is invisible until the day the provider changes.

    The categories are chosen by what a caller can DO about the failure, which
    is the only distinction that changes behaviour:

        TIMEOUT / RATE_LIMITED / TEMPORARY   wait and try again
        INVALID_REQUEST / AUTHENTICATION     fix something; retrying burns money
        SCHEMA_FAILURE                       investigate; may be an injection attempt
        BUDGET                               stop, and report reduced coverage
        NO_PROVIDER                          the tier cannot be served at all
    """

    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    TEMPORARY = "TEMPORARY"
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHENTICATION = "AUTHENTICATION"
    SCHEMA_FAILURE = "SCHEMA_FAILURE"
    BUDGET = "BUDGET"
    NO_PROVIDER = "NO_PROVIDER"


# Retry only what a retry can fix (§22). Retrying a deterministic failure burns
# budget, hides the bug, and — for an authentication error — can trip a
# provider's abuse detection while never once succeeding.
RETRYABLE_CATEGORIES: frozenset[ErrorCategory] = frozenset(
    {ErrorCategory.TIMEOUT, ErrorCategory.RATE_LIMITED, ErrorCategory.TEMPORARY}
)


class GatewayError(RuntimeError):
    """Base class for every gateway failure.

    Carries a `category` so a caller can branch without importing a taxonomy of
    exception classes, and without a vendor SDK ever entering its import graph.
    """

    category: ErrorCategory = ErrorCategory.TEMPORARY


class ProviderError(GatewayError):
    """A failure attributable to a provider, after normalization.

    `provider` and `status_code` are carried for telemetry. They are NOT part of
    the contract a business service reads: that is `category`.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str = "",
        status_code: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds


class BudgetExhaustedError(GatewayError):
    """The run or workspace budget is spent.

    This is a **first-class result**, not a crash. A session that exhausts its
    budget reaches COMPLETED with reduced Research Completeness -- never FAILED
    (Ontology V2 §15, ADR-006).
    """

    category = ErrorCategory.BUDGET


class SchemaValidationError(GatewayError):
    """The provider returned output that does not match the requested schema.

    Treated as a possible prompt-injection signal, never retried blindly into a
    fallback provider (llm-reasoning-rules.md §7).
    """

    category = ErrorCategory.SCHEMA_FAILURE


class NoProviderAvailableError(GatewayError):
    """No configured provider can serve the tier, or all candidates failed."""

    category = ErrorCategory.NO_PROVIDER


class ProviderTimeoutError(ProviderError):
    """A request exceeded its explicit timeout. There are no unbounded calls."""

    category = ErrorCategory.TIMEOUT


class ProviderRateLimitedError(ProviderError):
    """The provider refused the request for rate reasons.

    Retryable, with backoff and jitter. Synchronized retries across workers are
    how a rate limit becomes a ban (ADR-004).
    """

    category = ErrorCategory.RATE_LIMITED


class ProviderTemporaryError(ProviderError):
    """A 5xx or a transport failure. Retryable."""

    category = ErrorCategory.TEMPORARY


class ProviderInvalidRequestError(ProviderError):
    """A 4xx the provider will reject identically every time.

    Deterministic, therefore never retried: a context-length error or a
    malformed prompt costs the same on the second attempt and tells you nothing
    new (ADR-006 §Retries).
    """

    category = ErrorCategory.INVALID_REQUEST


class ProviderAuthenticationError(ProviderError):
    """A missing, invalid or unauthorized credential. Never retried."""

    category = ErrorCategory.AUTHENTICATION


def category_of(error: BaseException) -> ErrorCategory:
    """Normalize any exception into the internal vocabulary.

    An unrecognized exception is TEMPORARY rather than a new category: an
    unknown failure is more likely a transport hiccup than a permanent state,
    and the retry budget bounds the cost of being wrong about it.
    """
    if isinstance(error, GatewayError):
        return error.category
    if isinstance(error, TimeoutError):
        return ErrorCategory.TIMEOUT
    return ErrorCategory.TEMPORARY


def is_retryable(error: BaseException) -> bool:
    return category_of(error) in RETRYABLE_CATEGORIES


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

    # The rendered template, with its three regions still separate
    # (Mission 0.4 §29). Optional so the request stays constructible in tests
    # that exercise routing and budget rather than content; a provider adapter
    # requires it, because there is nothing else to send.
    prompt: RenderedPrompt | None = None

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

    # Prompt identity (llm-reasoning-rules.md §9). Without it a prompt change
    # silently reinterprets every historical signal and nothing says which ones.
    prompt_template_id: str = ""
    prompt_template_version: str = ""

    # Cost provenance. `priced` False means no tariff was configured for this
    # model, so `cost_units` is 0 because nothing is known -- NOT because the
    # call was free. Reporting an unpriced call as a zero-cost one would show
    # every budget untouched while real money was spent (see pricing.py).
    pricing_version: str = ""
    priced: bool = False

    # Correlation (Mission 0.4 §23). These are ids, never content: raw prompt
    # text and scraped source data must not reach telemetry.
    workspace_id: str = ""
    research_session_id: str = ""
    correlation_id: str = ""
    task: str = ""
    error_category: ErrorCategory | None = None

    def to_log_fields(self) -> dict[str, object]:
        """Structured log fields.

        Deliberately absent: the prompt text, the variables and any response
        content. Telemetry that carried them would put scraped source data into
        the log pipeline, where `data-principles.md` §8 and ADR-004
        §Observability say it must never go.
        """
        fields: dict[str, object] = {
            "llm_provider": self.provider,
            "llm_model": self.model,
            "llm_tier": self.tier.value,
            "llm_routing_version": self.routing_version,
            "llm_prompt_template_id": self.prompt_template_id,
            "llm_prompt_template_version": self.prompt_template_version,
            "llm_input_tokens": self.input_tokens,
            "llm_output_tokens": self.output_tokens,
            "llm_cost_units": self.cost_units,
            "llm_pricing_version": self.pricing_version,
            "llm_priced": self.priced,
            "llm_latency_ms": self.latency_ms,
            "llm_retries": self.retries,
            "llm_fallbacks": self.fallbacks,
            "llm_outcome": self.outcome.value,
            "llm_task": self.task,
            "workspace_id": self.workspace_id,
            "research_session_id": self.research_session_id,
            "correlation_id": self.correlation_id,
        }
        if self.error_category is not None:
            fields["llm_error_category"] = self.error_category.value
        return fields


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
