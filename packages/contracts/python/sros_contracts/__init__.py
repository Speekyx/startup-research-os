"""Startup Research OS shared domain contracts.

Stdlib only, by design (ADR-009): every service and every tool must be able to
import the domain vocabulary without pulling a dependency tree. Services adapt
these types to Pydantic at their HTTP boundary (ADR-003); the vocabulary itself
stays dependency-free.

The generated vocabulary lives in ``sros_contracts.generated.domain`` and is
derived from ``packages/contracts/schema/domain.v1.json``. Do not edit it.
"""

from __future__ import annotations

from .errors import ContractError
from .generated.domain import (
    CONTRACT_VERSION,
    ONTOLOGY_VERSION,
    REGISTRY_NAMES,
    RESEARCH_CONTEXT_SCHEMA_VERSION,
    AggregationProfileStatus,
    ClaimTemporality,
    ClaimType,
    DemandSignalFamily,
    EvidenceAggregationStatus,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
    LlmTier,
    MarketScopeType,
    PersonalDataRisk,
    PolicyAssessment,
    PolicyEvidenceType,
    RegistryStatus,
    ResearchSessionStatus,
    ScoreFamily,
    SourceAccessMethod,
    SourceAcquisitionCost,
    SourceApprovalState,
    SourceLifecycle,
)
from .ids import (
    EvidenceId,
    OpportunityId,
    ResearchProjectId,
    ResearchSessionId,
    SignalId,
    SourceId,
    UserId,
    WorkspaceId,
)
from .market_scope import MarketScope
from .numeric import (
    confidence,
    confidence_to_percent,
    evidence_level,
    independence,
    probability,
    reliability,
    score,
)
from .registry import RegistryEntry, RegistryRef
from .research_context import BudgetConstraints, ResearchContext

__all__ = [
    "CONTRACT_VERSION",
    "ONTOLOGY_VERSION",
    "RESEARCH_CONTEXT_SCHEMA_VERSION",
    "REGISTRY_NAMES",
    "ContractError",
    "ClaimType",
    "DemandSignalFamily",
    "LlmTier",
    "MarketScopeType",
    "RegistryStatus",
    "ResearchSessionStatus",
    "ScoreFamily",
    "SourceApprovalState",
    "SourceAccessMethod",
    "SourceLifecycle",
    "SourceAcquisitionCost",
    "PolicyAssessment",
    "PolicyEvidenceType",
    "PersonalDataRisk",
    "EvidenceDirection",
    "EvidenceIndependenceState",
    "EvidenceObservationCategory",
    "ClaimTemporality",
    "AggregationProfileStatus",
    "EvidenceAggregationStatus",
    "UserId",
    "WorkspaceId",
    "ResearchProjectId",
    "ResearchSessionId",
    "OpportunityId",
    "EvidenceId",
    "SignalId",
    "SourceId",
    "MarketScope",
    "RegistryRef",
    "RegistryEntry",
    "ResearchContext",
    "BudgetConstraints",
    "confidence",
    "confidence_to_percent",
    "probability",
    "reliability",
    "independence",
    "score",
    "evidence_level",
]
