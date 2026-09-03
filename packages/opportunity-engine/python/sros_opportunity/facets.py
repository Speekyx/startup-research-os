"""What is separately known about one candidate Evidence row.

Mission 1.28 §4. **There is deliberately no single evidence score.** Twelve facts
are exposed side by side, each keeping its own name and its own absence, because
the moment they collapse into one number the reasons stop being recoverable and
the number starts being quoted.

**Missing stays missing.** Every optional field means *nobody established this*,
and none of them has a default. The rule this enforces is the one
`evidence-reliability-contract-v1.md` paid for: `0.5 because unknown`,
`0.8 because reputable` and `0.0 because we do not know` are all measurements
nobody made, and `q_i = min(components)` must never be handed one. The
constructor refuses the substitutions rather than trusting a caller to avoid
them.

**`UNKNOWN` independence is a value, not a gap to fill.** It says the question was
recorded and not answered, which is different from a missing field and very
different from `KNOWN_INDEPENDENT`. Mission 1.28 §13 forbids promoting it, and
`__post_init__` refuses a facet set that claims independence it cannot name.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .dimensions import EvidenceDimension

__all__ = [
    "IndependenceState",
    "ReliabilityStatus",
    "EvidenceFacets",
]


class IndependenceState(enum.Enum):
    """Mirrors the values `scoring.evidence.independence_state` already stores."""

    KNOWN_INDEPENDENT = "KNOWN_INDEPENDENT"
    KNOWN_DEPENDENT = "KNOWN_DEPENDENT"
    UNKNOWN = "UNKNOWN"


class ReliabilityStatus(enum.Enum):
    """Whether a reviewed reliability resolved for this row's scope.

    `NO_APPLICABLE_ASSESSMENT` and `SUPERSEDED_ONLY` are kept apart on purpose:
    *nobody looked* and *somebody looked and withdrew it* are different facts,
    and `evidence-reliability-contract-v1.md` refuses to merge them.
    """

    RESOLVED = "RESOLVED"
    NO_APPLICABLE_ASSESSMENT = "NO_APPLICABLE_ASSESSMENT"
    SUPERSEDED_ONLY = "SUPERSEDED_ONLY"


@dataclass(frozen=True)
class EvidenceFacets:
    """One Evidence row's separately-known properties. No aggregate anywhere."""

    evidence_id: str
    claim_id: str

    # --- provenance -------------------------------------------------------
    source_id: str
    source_family: str
    use_profile_id: str
    extraction_method: str | None

    # --- epistemic --------------------------------------------------------
    claim_type: str
    claim_lifecycle: str
    claim_temporality: str
    claim_origin: str
    #: The Evidence relation to its Claim: SUPPORTS or CONTRADICTS. A generated
    #: row may never be NEUTRAL -- a Signal bearing on nothing produces no row.
    direction: str
    observation_category: str
    evidence_level: int

    # --- measured factors, each independently absent ----------------------
    relevance: float | None
    directness: float | None
    extraction_confidence: float | None
    reliability: float | None
    reliability_status: ReliabilityStatus

    # --- independence -----------------------------------------------------
    independence_state: IndependenceState
    independence_group_id: str | None

    # --- temporality of the observation itself ----------------------------
    #: None where the source never established an instant. Mission 1.10's rule:
    #: an unestablished timezone is stated, never chosen, so this is NULL on
    #: every row in the current corpus rather than a plausible datetime.
    observed_at: str | None

    # --- opportunity layer ------------------------------------------------
    signal_type_id: str | None
    dimensions: frozenset[EvidenceDimension]
    #: The source-bounded meaning that travels with `dimensions`.
    dimension_bound: str

    def __post_init__(self) -> None:
        if self.direction == "NEUTRAL":
            raise ValueError(
                f"{self.evidence_id}: direction NEUTRAL. A Signal bearing on nothing "
                "produces no Evidence row; a neutral row is a row that should not exist."
            )
        if self.reliability is None and self.reliability_status is ReliabilityStatus.RESOLVED:
            raise ValueError(
                f"{self.evidence_id}: reliability_status RESOLVED with no value. "
                "A resolution that produced no number did not resolve."
            )
        if self.reliability is not None and self.reliability_status is not (
            ReliabilityStatus.RESOLVED
        ):
            raise ValueError(
                f"{self.evidence_id}: a reliability value with status "
                f"{self.reliability_status.value}. A value that no assessment produced "
                "is a number nobody made, which is exactly what the reliability "
                "contract exists to refuse."
            )
        if (
            self.independence_state is not IndependenceState.UNKNOWN
            and self.independence_group_id is None
            and self.independence_state is IndependenceState.KNOWN_DEPENDENT
        ):
            raise ValueError(
                f"{self.evidence_id}: KNOWN_DEPENDENT with no independence group. "
                "A dependence with no named group is a claim nobody can re-check."
            )
        if self.dimensions and not self.dimension_bound.strip():
            raise ValueError(
                f"{self.evidence_id}: dimensions carried with no bound. A dimension "
                "detached from the sentence that bounds it is how a source-bounded "
                "measurement becomes a market claim."
            )

    @property
    def is_scorable(self) -> bool:
        """Whether aggregation could produce a number for this row.

        The single blocker in the current corpus, and it is the designed
        behaviour rather than a gap: no reviewed reliability applies to any of
        the four measurement-by-purpose scopes in use.
        """
        return self.reliability is not None

    @property
    def missing_factors(self) -> tuple[str, ...]:
        """Named absences, in a fixed order, for a report that cannot round up."""
        missing = []
        if self.relevance is None:
            missing.append("relevance")
        if self.directness is None:
            missing.append("directness")
        if self.extraction_confidence is None:
            missing.append("extraction_confidence")
        if self.reliability is None:
            missing.append("reliability")
        if self.observed_at is None:
            missing.append("observed_at")
        if not self.dimensions:
            missing.append("evidence_dimension")
        return tuple(missing)
