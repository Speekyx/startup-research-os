"""Provider-agnostic LLM Gateway (ADR-006).

Business services import from here and request a logical TIER. They never
import a provider SDK, and never name a model.
"""

from .budget import BudgetLedger
from .config import BudgetLimits, GatewayConfig, TierBinding, load_config_from_env
from .gateway import LlmGateway, Provider, ProviderResult
from .types import (
    BudgetExhaustedError,
    GatewayError,
    LlmRequest,
    LlmResponse,
    LlmTier,
    NoProviderAvailableError,
    ProviderOutcome,
    ProviderTimeoutError,
    SchemaValidationError,
    UsageMetadata,
)

__all__ = [
    "LlmGateway",
    "Provider",
    "ProviderResult",
    "BudgetLedger",
    "GatewayConfig",
    "TierBinding",
    "BudgetLimits",
    "load_config_from_env",
    "LlmRequest",
    "LlmResponse",
    "UsageMetadata",
    "LlmTier",
    "ProviderOutcome",
    "GatewayError",
    "BudgetExhaustedError",
    "SchemaValidationError",
    "NoProviderAvailableError",
    "ProviderTimeoutError",
]
