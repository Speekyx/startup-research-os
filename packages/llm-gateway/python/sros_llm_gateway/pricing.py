"""Provider pricing as versioned configuration.

Mission 0.4 §15: *"Do not invent product prices. Do not hard-code provider
pricing into business logic. Provider pricing should be configuration/versioned
data."*

**The default table is empty, and that is the point.** Provider tariffs change
without notice and vary by region, tier and contract. A plausible-looking
constant compiled into this module would be wrong within months, would look
authoritative, and every budget decision in the system would rest on it. The
same argument D-03 makes about the Evidence Score applies to a price: the
implementer who fills it in fills it in forever, unfalsifiably.

So a model with no configured price is **unpriced**, not free. The distinction
is carried through to the telemetry and to the budget ledger:

    priced=True   cost_units is a computed figure from a stated pricing version
    priced=False  cost_units is 0 because nothing is known, not because it cost nothing

A system that reported an unpriced call as costing zero would show every budget
as untouched while spending real money.

Configuration:

    LLM_PRICING_VERSION   an opaque label recorded with every spend record
    LLM_PRICING_JSON      {"<provider>:<model>": {"input_per_1k": …, "output_per_1k": …}}

Cost units are provider-agnostic (ADR-006). Whether one unit is a dollar, a
cent or a token is a decision for whoever writes the table.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

__all__ = ["ModelPrice", "PricingTable", "load_pricing_from_env", "UNPRICED_VERSION"]

# Recorded instead of a version when nothing is configured, so a spend record
# says "no price was known" rather than implying a priced zero.
UNPRICED_VERSION = "unpriced"


@dataclass(frozen=True)
class ModelPrice:
    """Cost per 1000 tokens, in cost units."""

    input_per_1k: float
    output_per_1k: float

    def __post_init__(self) -> None:
        if self.input_per_1k < 0 or self.output_per_1k < 0:
            raise ValueError("a price must not be negative")

    def cost_for(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens / 1000.0) * self.input_per_1k + (
            output_tokens / 1000.0
        ) * self.output_per_1k


@dataclass(frozen=True)
class PricingTable:
    """A versioned set of model prices.

    Keys are `"<provider>:<model>"`. Both are needed: the same model name can be
    served by more than one provider at different prices, and a table keyed on
    the model alone would silently apply one provider's tariff to another's.
    """

    version: str = UNPRICED_VERSION
    prices: dict[str, ModelPrice] = field(default_factory=dict)

    @staticmethod
    def key(provider: str, model: str) -> str:
        return f"{provider}:{model}"

    def price_for(self, provider: str, model: str) -> ModelPrice | None:
        return self.prices.get(self.key(provider, model))

    def cost_for(
        self, provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> tuple[float, bool]:
        """Return `(cost_units, priced)`.

        `priced` is False when no tariff is configured. Callers must record it:
        an unpriced call is not a free call, and a budget that treats it as one
        will let a session spend without limit while reporting nothing used.
        """
        price = self.price_for(provider, model)
        if price is None:
            return 0.0, False
        return price.cost_for(input_tokens, output_tokens), True

    @property
    def is_empty(self) -> bool:
        return not self.prices


def load_pricing_from_env(env: dict[str, str] | None = None) -> PricingTable:
    """Build the pricing table from configuration.

    Malformed configuration raises rather than falling back to an empty table.
    A silently ignored price list is worse than no price list: the operator
    believes budgets are enforced and they are not.
    """
    source = env if env is not None else dict(os.environ)

    raw = (source.get("LLM_PRICING_JSON") or "").strip()
    if not raw:
        return PricingTable(version=source.get("LLM_PRICING_VERSION") or UNPRICED_VERSION)

    try:
        parsed = json.loads(raw)
    except ValueError as exc:
        raise ValueError(f"LLM_PRICING_JSON is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("LLM_PRICING_JSON must be an object keyed by '<provider>:<model>'")

    prices: dict[str, ModelPrice] = {}
    for key, entry in parsed.items():
        if not isinstance(entry, dict):
            raise ValueError(f"LLM_PRICING_JSON entry {key!r} must be an object")
        missing = {"input_per_1k", "output_per_1k"} - set(entry)
        if missing:
            raise ValueError(f"LLM_PRICING_JSON entry {key!r} is missing {sorted(missing)}")
        if ":" not in key:
            raise ValueError(
                f"LLM_PRICING_JSON key {key!r} must be '<provider>:<model>'. A table keyed "
                "on the model alone would apply one provider's tariff to another's."
            )
        prices[key] = ModelPrice(
            input_per_1k=float(entry["input_per_1k"]),
            output_per_1k=float(entry["output_per_1k"]),
        )

    version = source.get("LLM_PRICING_VERSION")
    if not version:
        raise ValueError(
            "LLM_PRICING_VERSION is required whenever LLM_PRICING_JSON is set: a spend "
            "record whose tariff cannot be identified cannot be audited or recomputed."
        )
    return PricingTable(version=version, prices=prices)
