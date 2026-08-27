"""Pydantic boundary models.

ADR-003 requires Pydantic at HTTP boundaries. ADR-009 keeps the domain contracts
dependency-free. This module is the seam between them.

**These models adapt; they do not redefine.** No domain rule is re-implemented
here: `MarketScope` validation, canonicalization, `ResearchContext` field rules
and the closed enums all come from `sros_contracts`. A Pydantic model that
re-stated those rules would be a second source of truth, which is exactly the
drift audit C-02 recorded.

The flow is:

    HTTP JSON -> Pydantic (shape) -> sros_contracts (domain rules) -> application
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sros_contracts import (
    CONTRACT_VERSION,
    ContractError,
    MarketScope,
    ResearchContext,
    ResearchSessionStatus,
)

__all__ = [
    "CreateResearchProject",
    "ResearchProjectOut",
    "CreateResearchSession",
    "ResearchSessionOut",
    "HealthOut",
    "ReadinessOut",
    "ErrorOut",
    "to_domain_context",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# --------------------------------------------------------------- projects


class CreateResearchProject(_Base):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ResearchProjectOut(_Base):
    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------- sessions


class CreateResearchSession(_Base):
    """The request body is a ResearchContext.

    Only the shape is checked here. Every domain rule — scope invariants,
    registry references, canonicalization — is delegated to
    `sros_contracts.ResearchContext` by `to_domain_context`.
    """

    research_context: dict[str, Any]

    @field_validator("research_context")
    @classmethod
    def _must_be_an_object(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("research_context must be an object")
        return value


class ResearchSessionOut(_Base):
    id: UUID
    workspace_id: UUID
    project_id: UUID
    status: ResearchSessionStatus

    # The immutable snapshot, exactly as persisted.
    research_context: dict[str, Any]
    research_context_hash: str
    research_context_schema_version: str

    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    # A score family on 0-100 (scoring-framework-v1.1.md §4.1), not a
    # confidence. Null until scoring runs, which is blocked on D-03.
    research_completeness_score: int | None


# --------------------------------------------------------------- infra


class HealthOut(_Base):
    status: str
    service: str
    contract_version: str = CONTRACT_VERSION


class ReadinessOut(_Base):
    status: str
    dependencies: dict[str, str]
    correlation_id: str


class ErrorOut(_Base):
    error: str
    detail: str
    correlation_id: str


# --------------------------------------------------------------- adapters


def to_domain_context(payload: dict[str, Any]) -> ResearchContext:
    """Adapt an HTTP payload into the domain value object.

    Raises `ContractError`, which the application layer maps to HTTP 422. The
    error carries the offending field and the reason, because a contract
    violation is a bug at a boundary and the message is written for whoever has
    to fix it.
    """
    return ResearchContext.from_json(payload)


def market_scope_from(payload: dict[str, Any]) -> MarketScope:
    return MarketScope.from_json(payload)


def contract_error_detail(exc: ContractError) -> str:
    return f"{exc.field}: {exc.reason}"
