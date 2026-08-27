"""ResearchContext: the research specification.

Ontology V2 section 11.3. This is a **value object**, not an entity: it has no
identity and no lifecycle, and two contexts with identical parameters are the
same specification.

It is serialized as an **immutable snapshot** on a ResearchSession. The snapshot
is the reproducibility guarantee: editing a project default context must never
retroactively change what a past session says it ran with.

``canonical_json()`` is what gets persisted and hashed. It is deterministic --
sorted keys, canonicalized members -- so the same specification always produces
the same bytes, which is what makes the snapshot comparable and its hash stable.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace

from .errors import ContractError
from .generated.domain import RESEARCH_CONTEXT_SCHEMA_VERSION
from .market_scope import MarketScope
from .registry import RegistryRef

__all__ = ["ResearchContext", "BudgetConstraints", "RESEARCH_CONTEXT_SCHEMA_VERSION"]

_FIELDS = {
    "schema_version",
    "market_scope",
    "market_types",
    "product_types",
    "domains",
    "audience",
    "languages",
    "budget_constraints",
    "technical_constraints",
    "desired_mvp_complexity",
    "research_depth",
    "time_horizon_days",
    "excluded_markets",
    "excluded_categories",
    "filters",
}


@dataclass(frozen=True)
class BudgetConstraints:
    """Per-session cost ceiling. Concrete figures are configuration (ADR-006).

    Budget exhaustion is COMPLETED with reduced Research Completeness, never a
    session failure (Ontology V2 section 15).
    """

    max_cost_units: float | None = None
    max_llm_calls: int | None = None

    def __post_init__(self) -> None:
        if self.max_cost_units is not None and self.max_cost_units < 0:
            raise ContractError("budget_constraints.max_cost_units", "must not be negative")
        if self.max_llm_calls is not None and self.max_llm_calls < 0:
            raise ContractError("budget_constraints.max_llm_calls", "must not be negative")

    def to_json(self) -> dict[str, object]:
        return {"max_cost_units": self.max_cost_units, "max_llm_calls": self.max_llm_calls}

    @classmethod
    def from_json(cls, data: object) -> BudgetConstraints:
        if not isinstance(data, dict):
            raise ContractError("budget_constraints", "expected an object")
        unknown = set(data) - {"max_cost_units", "max_llm_calls"}
        if unknown:
            raise ContractError("budget_constraints", f"unknown fields: {sorted(unknown)}")
        return cls(
            max_cost_units=data.get("max_cost_units"),
            max_llm_calls=data.get("max_llm_calls"),
        )


@dataclass(frozen=True)
class ResearchContext:
    """Immutable research specification. Not an entity."""

    market_scope: MarketScope
    market_types: tuple[RegistryRef, ...] = ()
    product_types: tuple[RegistryRef, ...] = ()
    domains: tuple[str, ...] = ()
    audience: str | None = None
    languages: tuple[str, ...] = ()
    budget_constraints: BudgetConstraints | None = None
    technical_constraints: tuple[str, ...] = ()
    desired_mvp_complexity: str | None = None
    research_depth: str | None = None
    time_horizon_days: int | None = None
    excluded_markets: tuple[RegistryRef, ...] = ()
    excluded_categories: tuple[str, ...] = ()
    filters: dict[str, object] = field(default_factory=dict)

    schema_version: str = RESEARCH_CONTEXT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.market_scope, MarketScope):
            raise ContractError("research_context.market_scope", "a MarketScope is required")

        if self.time_horizon_days is not None and (
            not isinstance(self.time_horizon_days, int)
            or isinstance(self.time_horizon_days, bool)
            or self.time_horizon_days < 1
        ):
            raise ContractError("research_context.time_horizon_days", "must be a positive integer")

        normalized = tuple(sorted({lang.lower() for lang in self.languages}))
        object.__setattr__(self, "languages", normalized)

        for ref in (*self.market_types, *self.product_types, *self.excluded_markets):
            if not isinstance(ref, RegistryRef):
                raise ContractError("research_context", "registry fields require a RegistryRef")

    # -- serialization ------------------------------------------------------

    @classmethod
    def from_json(cls, data: object) -> ResearchContext:
        if not isinstance(data, dict):
            raise ContractError("research_context", "expected an object")

        unknown = set(data) - _FIELDS
        if unknown:
            raise ContractError(
                "research_context",
                f"unknown fields: {sorted(unknown)}. Unknown fields are rejected so a "
                "typo is not silently dropped from a snapshot.",
            )
        if "market_scope" not in data:
            raise ContractError("research_context.market_scope", "required")

        budget = data.get("budget_constraints")
        return cls(
            market_scope=MarketScope.from_json(data["market_scope"]),
            market_types=_refs(data.get("market_types")),
            product_types=_refs(data.get("product_types")),
            domains=tuple(data.get("domains") or ()),
            audience=data.get("audience"),
            languages=tuple(data.get("languages") or ()),
            budget_constraints=BudgetConstraints.from_json(budget) if budget else None,
            technical_constraints=tuple(data.get("technical_constraints") or ()),
            desired_mvp_complexity=data.get("desired_mvp_complexity"),
            research_depth=data.get("research_depth"),
            time_horizon_days=data.get("time_horizon_days"),
            excluded_markets=_refs(data.get("excluded_markets")),
            excluded_categories=tuple(data.get("excluded_categories") or ()),
            filters=dict(data.get("filters") or {}),
            schema_version=data.get("schema_version", RESEARCH_CONTEXT_SCHEMA_VERSION),
        )

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "audience": self.audience,
            "desired_mvp_complexity": self.desired_mvp_complexity,
            "domains": list(self.domains),
            "excluded_categories": list(self.excluded_categories),
            "excluded_markets": [r.to_json() for r in self.excluded_markets],
            "filters": dict(self.filters),
            "languages": list(self.languages),
            "market_scope": self.market_scope.to_json(),
            "market_types": [r.to_json() for r in self.market_types],
            "product_types": [r.to_json() for r in self.product_types],
            "research_depth": self.research_depth,
            "schema_version": self.schema_version,
            "technical_constraints": list(self.technical_constraints),
            "time_horizon_days": self.time_horizon_days,
        }
        if self.budget_constraints is not None:
            payload["budget_constraints"] = self.budget_constraints.to_json()
        return payload

    def canonical_json(self) -> str:
        """Deterministic serialization. This is what gets snapshotted and hashed."""
        return json.dumps(self.to_json(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def snapshot_hash(self) -> str:
        """Stable content hash of the canonical form."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def with_changes(self, **changes: object) -> ResearchContext:
        """Return a NEW context. The original is never mutated."""
        return replace(self, **changes)  # type: ignore[arg-type]


def _refs(value: object) -> tuple[RegistryRef, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ContractError("research_context", "registry fields expect a list")
    return tuple(
        item if isinstance(item, RegistryRef) else RegistryRef.from_json(item) for item in value
    )
