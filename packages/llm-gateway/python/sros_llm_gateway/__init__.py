"""Provider-agnostic LLM Gateway (ADR-006).

Business services import from here and request a logical TIER. They never
import a provider SDK, and never name a model.

    types.py       the request/response contract and the error taxonomy
    config.py      tier -> provider/model resolution, from configuration
    pricing.py     versioned provider tariffs. Empty by default, on purpose
    budget.py      per-session and per-workspace-day accounting
    transport.py   the HTTP seam that makes providers testable without a key
    gateway.py     routing, retry policy, schema validation, telemetry
    prompts/       versioned templates and the prompt-injection boundary
    providers/     the only place vendor knowledge is allowed to live
    evaluation/    datasets, metrics and regression comparison
"""

from .budget import BudgetLedger
from .config import BudgetLimits, GatewayConfig, TierBinding, load_config_from_env
from .gateway import LlmGateway, Provider, ProviderResult, TelemetrySink
from .pricing import UNPRICED_VERSION, ModelPrice, PricingTable, load_pricing_from_env
from .prompts import (
    PromptInjectionError,
    PromptNotFoundError,
    PromptRegistry,
    PromptTemplate,
    RenderedPrompt,
    UntrustedText,
)
from .transport import FakeTransport, HttpResponse, HttpTransport, TransportError, UrllibTransport
from .types import (
    RETRYABLE_CATEGORIES,
    BudgetExhaustedError,
    ErrorCategory,
    GatewayError,
    LlmRequest,
    LlmResponse,
    LlmTier,
    NoProviderAvailableError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderInvalidRequestError,
    ProviderOutcome,
    ProviderRateLimitedError,
    ProviderTemporaryError,
    ProviderTimeoutError,
    SchemaValidationError,
    UsageMetadata,
    category_of,
    is_retryable,
)

__all__ = [
    # gateway
    "LlmGateway",
    "Provider",
    "ProviderResult",
    "TelemetrySink",
    # configuration and budget
    "BudgetLedger",
    "GatewayConfig",
    "TierBinding",
    "BudgetLimits",
    "load_config_from_env",
    # pricing
    "PricingTable",
    "ModelPrice",
    "load_pricing_from_env",
    "UNPRICED_VERSION",
    # transport
    "HttpTransport",
    "HttpResponse",
    "UrllibTransport",
    "FakeTransport",
    "TransportError",
    # prompts
    "PromptTemplate",
    "PromptRegistry",
    "PromptNotFoundError",
    "RenderedPrompt",
    "UntrustedText",
    "PromptInjectionError",
    # contract
    "LlmRequest",
    "LlmResponse",
    "UsageMetadata",
    "LlmTier",
    "ProviderOutcome",
    # errors
    "ErrorCategory",
    "RETRYABLE_CATEGORIES",
    "category_of",
    "is_retryable",
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
]
