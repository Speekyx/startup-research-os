"""Tier -> provider/model resolution.

ADR-006: **no model name is hard-coded.** Models change faster than release
cycles, so the mapping lives in configuration and a model change is a config
change plus a recorded routing version, never a code change.

The routing configuration is versioned, and the resolved version is recorded on
every response. Without that, a routing change silently alters historical
comparability and nothing records why results shifted.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from sros_contracts import LlmTier

__all__ = ["TierBinding", "GatewayConfig", "load_config_from_env", "BudgetLimits"]


@dataclass(frozen=True)
class TierBinding:
    """Which provider and model serve a logical tier, in preference order."""

    tier: LlmTier
    provider: str | None
    model: str | None

    @property
    def configured(self) -> bool:
        return bool(self.provider) and self.provider != "null"


@dataclass(frozen=True)
class BudgetLimits:
    """Configurable ceilings. No product pricing is invented here.

    Cost units are provider-agnostic on purpose: a unit is whatever the cost
    model says it is, and the gateway only has to compare and subtract.
    """

    max_cost_units_per_session: float = 100.0
    max_llm_calls_per_session: int = 500
    max_cost_units_per_workspace_day: float | None = 1000.0


@dataclass(frozen=True)
class GatewayConfig:
    routing_version: str
    bindings: dict[LlmTier, TierBinding]
    budgets: BudgetLimits = field(default_factory=BudgetLimits)
    request_timeout_seconds: float = 60.0
    max_retries: int = 2

    def binding_for(self, tier: LlmTier) -> TierBinding:
        binding = self.bindings.get(tier)
        if binding is None:
            raise KeyError(f"no binding configured for tier {tier.value}")
        return binding


_ENV_PREFIX = {
    LlmTier.FAST_MODEL: "LLM_TIER_FAST",
    LlmTier.BALANCED_MODEL: "LLM_TIER_BALANCED",
    LlmTier.STRONG_MODEL: "LLM_TIER_STRONG",
    LlmTier.EMBEDDING_MODEL: "LLM_TIER_EMBEDDING",
}


def load_config_from_env(env: dict[str, str] | None = None) -> GatewayConfig:
    """Build the gateway configuration from environment variables.

    Unconfigured tiers are permitted and resolve to an unconfigured binding: in
    Mission 0.2 no real provider is wired, and the gateway must still be
    constructible so the rest of the system can depend on it.
    """
    source = env if env is not None else dict(os.environ)

    bindings: dict[LlmTier, TierBinding] = {}
    for tier, prefix in _ENV_PREFIX.items():
        bindings[tier] = TierBinding(
            tier=tier,
            provider=source.get(f"{prefix}_PROVIDER") or None,
            model=source.get(f"{prefix}_MODEL") or None,
        )

    def _float(name: str, default: float) -> float:
        raw = source.get(name)
        return float(raw) if raw not in (None, "") else default

    def _int(name: str, default: int) -> int:
        raw = source.get(name)
        return int(raw) if raw not in (None, "") else default

    budgets = BudgetLimits(
        max_cost_units_per_session=_float("BUDGET_MAX_COST_UNITS_PER_SESSION", 100.0),
        max_llm_calls_per_session=_int("BUDGET_MAX_LLM_CALLS_PER_SESSION", 500),
        max_cost_units_per_workspace_day=_float("BUDGET_MAX_COST_UNITS_PER_WORKSPACE_DAY", 1000.0),
    )

    return GatewayConfig(
        routing_version=source.get("LLM_ROUTING_VERSION", "1.0.0"),
        bindings=bindings,
        budgets=budgets,
        request_timeout_seconds=_float("LLM_REQUEST_TIMEOUT_SECONDS", 60.0),
        max_retries=_int("LLM_MAX_RETRIES", 2),
    )
