"""Opportunity Engine foundation (Mission 1.28).

The deterministic path from Evidence to a packet that MAY support one future
opportunity hypothesis:

    Evidence -> facets -> dimension mapping -> eligibility -> subject grouping
             -> packet -> sufficiency -> [ external synthesis gate ] -> hypothesis

Everything up to the gate is deterministic and reproducible, needs no model, and
reaches no network. The gate is where a model would be reached and is the reason
one is not reached today.

**Nothing here requires `SAME_PROBLEM_FAMILY`** (Mission 1.28 §6). The parked
classifier is not imported, not optional-imported and not referenced; a test
asserts it over the AST. Recurring-problem Evidence can be added later as another
signal type in `mapping.py`, which is a data change rather than an architectural
one.

**No ranking, no score, no leaderboard** (§15). There is no numeric aggregate in
this package: no 0-100 field, no weight, no priority order and no comparison
between packets. Building one before the dimensions and the sufficiency model are
established is what would make a future score meaningless.
"""

from __future__ import annotations

from .dimensions import (
    COMMERCIAL_DIMENSIONS,
    DIMENSION_DEFINITIONS,
    DIMENSION_TAXONOMY_VERSION,
    DimensionDefinition,
    EvidenceDimension,
)
from .eligibility import (
    ELIGIBILITY_PROCEDURE_VERSION,
    EligibilityDecision,
    PacketEligibility,
    SourcePolicyStanding,
    assess_eligibility,
)
from .external_synthesis import (
    EGRESS_PROCEDURE_VERSION,
    ExternalSynthesisDecision,
    ExternalSynthesisRefusedError,
    SynthesisAvailability,
    authorize_packet_for_external_synthesis,
    serialize_packet_for_model,
)
from .facets import EvidenceFacets, IndependenceState, ReliabilityStatus
from .grouping import (
    GROUPING_PROCEDURE_VERSION,
    CandidateGroup,
    SubjectKey,
    group_by_subject,
    subject_key,
)
from .guards import (
    FORBIDDEN_TERMS,
    GUARD_VERSION,
    VALIDATION_WORDS,
    GuardViolation,
    check_no_validation_language,
    check_statement,
)
from .hypothesis import (
    HYPOTHESIS_PROCEDURE_VERSION,
    OpportunityHypothesis,
    OpportunityStatus,
    UnsupportedClaimError,
)
from .mapping import (
    COUNTING_DIMENSIONS,
    DIMENSION_MAP_VERSION,
    SIGNAL_DIMENSION_MAP,
    SignalDimensionMapping,
    counting_dimensions,
    map_signal_type,
)
from .packet import (
    PACKET_PROCEDURE_VERSION,
    OpportunityEvidencePacket,
    build_packet,
)
from .subjects import (
    SUBJECT_REGISTRY_VERSION,
    CanonicalSubject,
    CanonicalSubjectRegistry,
    SubjectIdentifier,
    load_subject_registry,
)
from .sufficiency import (
    SUFFICIENCY_PROCEDURE_VERSION,
    SUFFICIENCY_V1,
    HypothesisStatus,
    SufficiencyResult,
    SufficiencyRule,
    evaluate,
)
from .transmission import (
    PERMITTED_PAYLOAD_KEYS,
    PERSONAL_DATA_MARKERS,
    PROHIBITED_REPRESENTATIONS,
    TRANSMISSION_REPRESENTATION_VERSION,
    RepresentationBoundError,
    RepresentationViolation,
    check_representation,
)

__all__ = [
    "COMMERCIAL_DIMENSIONS",
    "COUNTING_DIMENSIONS",
    "DIMENSION_DEFINITIONS",
    "DIMENSION_MAP_VERSION",
    "DIMENSION_TAXONOMY_VERSION",
    "EGRESS_PROCEDURE_VERSION",
    "ELIGIBILITY_PROCEDURE_VERSION",
    "FORBIDDEN_TERMS",
    "GROUPING_PROCEDURE_VERSION",
    "GUARD_VERSION",
    "HYPOTHESIS_PROCEDURE_VERSION",
    "PACKET_PROCEDURE_VERSION",
    "PERMITTED_PAYLOAD_KEYS",
    "PERSONAL_DATA_MARKERS",
    "PROHIBITED_REPRESENTATIONS",
    "SIGNAL_DIMENSION_MAP",
    "SUFFICIENCY_PROCEDURE_VERSION",
    "SUBJECT_REGISTRY_VERSION",
    "SUFFICIENCY_V1",
    "TRANSMISSION_REPRESENTATION_VERSION",
    "VALIDATION_WORDS",
    "CandidateGroup",
    "CanonicalSubject",
    "CanonicalSubjectRegistry",
    "DimensionDefinition",
    "EligibilityDecision",
    "EvidenceDimension",
    "EvidenceFacets",
    "ExternalSynthesisDecision",
    "ExternalSynthesisRefusedError",
    "GuardViolation",
    "HypothesisStatus",
    "IndependenceState",
    "OpportunityEvidencePacket",
    "OpportunityHypothesis",
    "OpportunityStatus",
    "PacketEligibility",
    "ReliabilityStatus",
    "RepresentationBoundError",
    "RepresentationViolation",
    "SignalDimensionMapping",
    "SourcePolicyStanding",
    "SubjectIdentifier",
    "SubjectKey",
    "SufficiencyResult",
    "SufficiencyRule",
    "SynthesisAvailability",
    "UnsupportedClaimError",
    "assess_eligibility",
    "authorize_packet_for_external_synthesis",
    "build_packet",
    "check_no_validation_language",
    "check_representation",
    "check_statement",
    "counting_dimensions",
    "evaluate",
    "group_by_subject",
    "load_subject_registry",
    "map_signal_type",
    "serialize_packet_for_model",
    "subject_key",
]
