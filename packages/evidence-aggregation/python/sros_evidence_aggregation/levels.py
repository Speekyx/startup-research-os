"""EvidenceLevel: qualitative maturity, deliberately not a score threshold.

Mission 1.1 §22–§23.

EvidenceLevel and EvidenceScore answer different questions and must not be
derived from each other. The score says how strongly the accumulated evidence
supports the claim under this aggregation model. The level says **what kind of
evidence exists at all**. A single recorded payment is Level 5 with a modest
score; ten thousand enthusiastic comments are Level 1 with a high one.

Deriving level from score thresholds — `80 -> level 4` — would erase exactly
that distinction, and no authoritative specification licenses it.

Two structural rules carry the ladder:

**Independence gates levels 2 and 3.** Level 2 is *Repeated Signal*. Repetition
means separate observations, not separate copies, so it requires independent
groups rather than record count. A duplicated article cannot create a repeated
signal, which is the whole point of §11.

**Category gates levels 4 and 5.** Level 4 is *Market Evidence* and Level 5 is
*Direct Validation*; both are statements about what was observed. No quantity of
stated opinion reaches them, because accumulating opinions produces more
opinion. `EvidenceObservationCategory` carries this and is closed for exactly
this branching.

The ladder is not strictly nested at the top, and that is intentional. A single
recorded preorder is Level 5 without three independent supporting groups behind
it, because the *kind* of evidence dominates its *quantity*. The original
framework says so directly: Level 5 examples include "user interviews", singular.

**Level describes supporting evidence only.** Contradiction does not lower it: a
contested claim still has whatever evidence it has. So a level must never be
read alone — `contradiction_strength` and `conflict_mass` sit beside it in every
result for this reason.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sros_contracts import EvidenceDirection, EvidenceIndependenceState
from sros_contracts import EvidenceObservationCategory as Category

from .independence import GroupKind, IndependenceGroup
from .items import EvidenceItem, ItemContribution

__all__ = ["LEVEL_NAMES", "EvidenceLevelAssessment", "assess_evidence_level"]

LEVEL_NAMES = {
    0: "Hypothesis",
    1: "Weak Signal",
    2: "Repeated Signal",
    3: "Strong Multi-Source Signal",
    4: "Market Evidence",
    5: "Direct Validation",
}

# Categories that constitute market behaviour rather than talk about it.
MARKET_CATEGORIES = frozenset({Category.MARKET_ACTIVITY, Category.DIRECT_VALIDATION})
VALIDATION_CATEGORIES = frozenset({Category.DIRECT_VALIDATION})


@dataclass(frozen=True)
class EvidenceLevelAssessment:
    """The level reached, and why each higher one was not."""

    level: int
    label: str
    reasons: tuple[str, ...]
    blocked_reasons: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "evidence_level": self.level,
            "label": self.label,
            "reasons": list(self.reasons),
            "blocked_reasons": list(self.blocked_reasons),
        }


def _qualifying_items(
    items: Sequence[EvidenceItem],
    contributions: dict[str, ItemContribution],
    categories: frozenset[Category],
) -> list[EvidenceItem]:
    """Supporting, scorable, categorised, and of established provenance.

    The provenance condition is the one worth defending. A record whose origin
    was never traced may well be a syndicated copy of something else, and
    "Market Evidence" resting on a record nobody has placed is the popularity
    -becomes-truth failure wearing a better label. Establishing provenance is
    work; levels 4 and 5 require it to have been done.
    """
    qualifying = []
    for item in items:
        if item.direction is not EvidenceDirection.SUPPORTS:
            continue
        contribution = contributions.get(item.evidence_id)
        if contribution is None or not contribution.scorable:
            continue
        if item.observation_category not in categories:
            continue
        if item.independence_state is EvidenceIndependenceState.UNKNOWN:
            continue
        qualifying.append(item)
    return qualifying


def assess_evidence_level(
    items: Sequence[EvidenceItem],
    contributions: dict[str, ItemContribution],
    support_groups: Sequence[IndependenceGroup],
    *,
    repeated_signal_min_groups: int,
    multi_source_min_groups: int,
    multi_source_min_families: int,
) -> EvidenceLevelAssessment:
    """The highest level whose own conditions hold.

    The three thresholds come from the profile rather than from constants here.
    They are structural minimums — "repeated" cannot mean fewer than two,
    "multi-source" cannot mean one source — not fitted values, and a calibrated
    profile may raise them. Making them parameters is what keeps that honest.
    """
    reasons: list[str] = []
    blocked: list[str] = []

    scorable_support = [
        item
        for item in items
        if item.direction is EvidenceDirection.SUPPORTS
        and (c := contributions.get(item.evidence_id)) is not None
        and c.scorable
    ]

    # Levels 2 and 3 count only groups whose independence was ESTABLISHED. The
    # unknown-provenance bucket is excluded entirely, not counted as one group:
    # one known record plus a bucket of unlabelled ones is not two observations,
    # because the unlabelled ones may all derive from the known one. "Repeated"
    # has to mean established repetition or it means nothing (§22).
    independent_groups = [g for g in support_groups if g.kind is not GroupKind.UNKNOWN]
    families = {item.source_family for item in scorable_support if item.source_family}

    level = 0
    if scorable_support:
        level = 1
        reasons.append(f"{len(scorable_support)} scorable supporting record(s)")
    else:
        blocked.append("no scorable supporting evidence")

    if level >= 1:
        if len(independent_groups) >= repeated_signal_min_groups:
            level = 2
            reasons.append(
                f"{len(independent_groups)} supporting group(s) of established "
                f"independence >= {repeated_signal_min_groups} required for Repeated Signal"
            )
        else:
            blocked.append(
                f"Repeated Signal needs {repeated_signal_min_groups} supporting groups of "
                f"established independence, found {len(independent_groups)}"
                + (
                    f" (plus {len(support_groups) - len(independent_groups)} "
                    "unknown-provenance group, which does not count)"
                    if len(support_groups) > len(independent_groups)
                    else ""
                )
            )

    if level >= 2:
        if (
            len(independent_groups) >= multi_source_min_groups
            and len(families) >= multi_source_min_families
        ):
            level = 3
            reasons.append(
                f"{len(independent_groups)} independent groups across {len(families)} "
                "source families"
            )
        else:
            blocked.append(
                f"Strong Multi-Source needs {multi_source_min_groups} independent groups "
                f"across {multi_source_min_families} source families, found "
                f"{len(independent_groups)} groups across {len(families)} families"
            )

    # Category gates. Reached independently of the counts above: the kind of
    # observation dominates its quantity, and a single recorded payment is
    # stronger evidence than any number of comments.
    market = _qualifying_items(items, contributions, MARKET_CATEGORIES)
    validation = _qualifying_items(items, contributions, VALIDATION_CATEGORIES)

    if market:
        level = max(level, 4)
        reasons.append(f"{len(market)} record(s) of established provenance in a market category")
    else:
        blocked.append(
            "Market Evidence needs a supporting record categorised MARKET_ACTIVITY or "
            "DIRECT_VALIDATION with established provenance; quantity of opinion cannot "
            "substitute for it"
        )

    if validation:
        level = max(level, 5)
        reasons.append(f"{len(validation)} direct-validation record(s)")
    else:
        blocked.append(
            "Direct Validation needs a supporting record categorised DIRECT_VALIDATION "
            "with established provenance"
        )

    return EvidenceLevelAssessment(
        level=level,
        label=LEVEL_NAMES[level],
        reasons=tuple(reasons),
        blocked_reasons=tuple(blocked),
    )
