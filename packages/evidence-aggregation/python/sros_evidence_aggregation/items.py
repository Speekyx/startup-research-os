"""One evidence record, and how strongly it can contribute.

Mission 1.1 §6, §8, §9.

**The contribution is the weakest component, not a weighted average.**

    q = min(relevance, directness, reliability, extraction_confidence, freshness)

A weighted average lets a strong dimension pay for a weak one, and the two cases
that matters for are exactly the two the system must not get wrong: a highly
relevant record from a source that cannot be relied on, and a highly reliable
source discussing something else. An average scores both as middling. The
minimum scores both as weak, which is what they are.

The cost is real and worth stating: `min` throws away information. A record
scoring 0.9 on four dimensions and 0.3 on one is treated identically to a record
scoring 0.3 on all five. V1 accepts that, because being wrong in the
conservative direction is recoverable and being wrong in the permissive
direction produces confident nonsense. The explanation records every component,
so a later calibrated profile can revisit the operator with the data to justify
it.

**`q` is not a probability.** It is a bounded contribution strength. There is no
event whose likelihood it expresses, and it must never be presented as one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sros_contracts import (
    ClaimTemporality,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
)

from .errors import InvalidEvidenceItemError, InvalidFactorError
from .recency import freshness

__all__ = [
    "ITEM_QUALITY_COMPONENTS",
    "EvidenceItem",
    "ItemContribution",
    "NonScorableReason",
    "evaluate_item",
    "validate_factor",
]

# The order is the reported order, so two explanations of the same record read
# identically. `freshness` is derived rather than supplied, so it is last.
ITEM_QUALITY_COMPONENTS = (
    "relevance",
    "directness",
    "reliability",
    "extraction_confidence",
    "freshness",
)


class NonScorableReason(str):
    """A stated reason a record contributed no number.

    A plain string subclass rather than an enum: the set is open by design. Each
    missing component names itself, and inventing a closed enum would mean
    deciding in advance every way a record can be incomplete.
    """

    __slots__ = ()


def validate_factor(name: str, value: float | None) -> float | None:
    """Reject an out-of-range factor. Do not clamp it.

    `scoring-framework-v1.1.md` §4.1 fixes these on `[0,1]`. A value of 1.4 means
    the producer is working to a different scale, and clamping to 1.0 would hide
    that while producing a plausible-looking result.
    """
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise InvalidFactorError(f"{name} must be a number, got {value!r}")
    numeric = float(value)
    if numeric != numeric:
        raise InvalidFactorError(f"{name} must be a number, got NaN")
    if not (0.0 <= numeric <= 1.0):
        raise InvalidFactorError(
            f"{name} must be on the unit interval [0,1], got {numeric!r} "
            "(scoring-framework-v1.1.md §4.1)"
        )
    return numeric


@dataclass(frozen=True)
class EvidenceItem:
    """One Evidence record as aggregation sees it.

    Deliberately not the database row. `scoring.evidence` stores raw evidence
    metadata; this is the projection aggregation needs, and keeping them
    separate is what lets the schema evolve without the mathematics moving.
    """

    evidence_id: str
    direction: EvidenceDirection

    relevance: float | None = None
    directness: float | None = None
    reliability: float | None = None
    extraction_confidence: float | None = None

    observation_category: EvidenceObservationCategory = EvidenceObservationCategory.UNCATEGORISED
    independence_state: EvidenceIndependenceState = EvidenceIndependenceState.UNKNOWN
    independence_group_id: str | None = None

    observed_at: datetime | None = None

    # Provenance, carried for diagnostics and EvidenceLevel only. Neither is
    # ever read as a weight: see the package docstring and §7.
    source_id: str | None = None
    source_family: str | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise InvalidEvidenceItemError(
                "evidence_id is required; a record with no id cannot appear in an explanation"
            )
        for name in ("relevance", "directness", "reliability", "extraction_confidence"):
            validate_factor(name, getattr(self, name))

        state = self.independence_state
        if state is EvidenceIndependenceState.KNOWN_DEPENDENT and not self.independence_group_id:
            raise InvalidEvidenceItemError(
                f"{self.evidence_id}: KNOWN_DEPENDENT without an independence_group_id "
                "asserts a dependency on nothing. Either name the group or record the "
                "state as UNKNOWN"
            )
        if state is EvidenceIndependenceState.KNOWN_INDEPENDENT and self.independence_group_id:
            raise InvalidEvidenceItemError(
                f"{self.evidence_id}: KNOWN_INDEPENDENT with an independence_group_id "
                "claims independence and group membership at once"
            )


@dataclass(frozen=True)
class ItemContribution:
    """What one record contributed, and why it contributed that.

    Every component is retained even when the record is non-scorable. An
    explanation that only showed the surviving records would make the ones that
    dropped out invisible, and those are usually the interesting ones.
    """

    evidence_id: str
    direction: EvidenceDirection
    scorable: bool
    q: float | None
    components: dict[str, float | None]
    limiting_component: str | None
    non_scorable_reasons: tuple[NonScorableReason, ...] = field(default_factory=tuple)

    def to_json(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "direction": self.direction.value,
            "scorable": self.scorable,
            "q": self.q,
            "components": dict(self.components),
            "limiting_component": self.limiting_component,
            "non_scorable_reasons": [str(r) for r in self.non_scorable_reasons],
        }


def evaluate_item(
    item: EvidenceItem,
    *,
    temporality: ClaimTemporality,
    now: datetime,
    half_life_days: float | None,
    required_components: tuple[str, ...] = ITEM_QUALITY_COMPONENTS,
) -> ItemContribution:
    """Compute `q` for one record, or say precisely why there is none.

    NEUTRAL records are evaluated like any other and then excluded from both
    aggregations by the engine. They are not failures: a record that bears on a
    claim without bearing either way is a real finding, it belongs in the
    explanation, and it counts towards research coverage.
    """
    fresh, missing_temporal = freshness(temporality, item.observed_at, now, half_life_days)

    components: dict[str, float | None] = {
        "relevance": item.relevance,
        "directness": item.directness,
        "reliability": item.reliability,
        "extraction_confidence": item.extraction_confidence,
        "freshness": fresh,
    }

    reasons: list[NonScorableReason] = []
    if missing_temporal is not None:
        reasons.append(NonScorableReason(missing_temporal))
    for name in required_components:
        if components.get(name) is None and name != "freshness":
            reasons.append(NonScorableReason(f"MISSING_{name.upper()}"))
    if fresh is None and missing_temporal is None and "freshness" in required_components:
        reasons.append(NonScorableReason("MISSING_FRESHNESS"))

    if reasons:
        # No number. Not 0.0 either -- a zero would enter the mathematics as a
        # measured weakness, and this is an absence of measurement (§9).
        return ItemContribution(
            evidence_id=item.evidence_id,
            direction=item.direction,
            scorable=False,
            q=None,
            components=components,
            limiting_component=None,
            non_scorable_reasons=tuple(dict.fromkeys(reasons)),
        )

    scored = {name: components[name] for name in required_components}
    # Ties resolve to the first component in DECLARED order, not alphabetical
    # order. When every component is equal the limit is not really any one of
    # them, and reporting whichever name sorts first would read as a finding
    # about that dimension. Declared order at least matches how the components
    # are listed everywhere else, so the arbitrariness is consistent.
    order = {name: index for index, name in enumerate(required_components)}
    limiting = min(scored, key=lambda name: (scored[name] or 0.0, order[name]))
    return ItemContribution(
        evidence_id=item.evidence_id,
        direction=item.direction,
        scorable=True,
        q=float(scored[limiting]),  # type: ignore[arg-type]
        components=components,
        limiting_component=limiting,
    )
