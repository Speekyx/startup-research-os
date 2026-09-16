"""Mission 1.85.2 (roadmap N05). The differential cases for the independence-level repair.

One definition of every case, shared by the predecessor baseline writer and the tests that compare the
repaired algorithm against it, so the two can never drift apart. Nothing here is persisted evidence.

Default quality is 0.6 on every component, one family unless stated. `KNOWN_DEPENDENT` items carry a
lineage in `group`; items sharing a lineage are copies of one origin.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime

from sros_contracts import (
    ClaimTemporality,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
)
from sros_evidence_aggregation import REFERENCE_PROFILE_V1, EvidenceItem, aggregate

D = EvidenceDirection
IND = EvidenceIndependenceState
C = EvidenceObservationCategory
NOW = datetime(2026, 8, 29, 12, 0, 0, tzinfo=UTC)


def item(
    evidence_id: str,
    *,
    q: float = 0.6,
    direction: EvidenceDirection = D.SUPPORTS,
    state: EvidenceIndependenceState = IND.KNOWN_INDEPENDENT,
    group: str | None = None,
    category: EvidenceObservationCategory = C.STATED_OPINION,
    family: str | None = "family-a",
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        direction=direction,
        relevance=q,
        directness=q,
        reliability=q,
        extraction_confidence=q,
        independence_state=state,
        independence_group_id=group,
        observation_category=category,
        source_id=f"src-{evidence_id}",
        source_family=family,
        observed_at=None,
    )


def unknown(evidence_id: str, **kwargs) -> EvidenceItem:
    return item(evidence_id, state=IND.UNKNOWN, **kwargs)


def dependent(evidence_id: str, lineage: str, **kwargs) -> EvidenceItem:
    return item(evidence_id, state=IND.KNOWN_DEPENDENT, group=lineage, **kwargs)


def run(items: list[EvidenceItem]):
    return aggregate(
        "claim-under-test",
        list(items),
        REFERENCE_PROFILE_V1,
        temporality=ClaimTemporality.EVERGREEN,
        now=NOW,
        allow_uncalibrated=True,
    )


#: The fifteen required cases of the Mission 1.85.1 brief (13 to 15 are properties checked over all
#: cases, so they carry no input of their own), then the adversarial cases.
CASES: dict[str, list[EvidenceItem]] = {
    "C01_all_unknown": [unknown("u1"), unknown("u2"), unknown("u3"), unknown("u4")],
    "C02_one_dependent_lineage_plus_unknown": [dependent("d1", "g1"), unknown("u1")],
    "C03_two_dependent_lineages": [
        dependent("d1", "g1"),
        dependent("d2", "g1"),
        dependent("d3", "g2"),
        dependent("d4", "g2"),
    ],
    "C04_three_dependent_lineages_two_families": [
        dependent("d1", "g1", family="f1"),
        dependent("d2", "g2", family="f2"),
        dependent("d3", "g3", family="f1"),
    ],
    "C05_two_independent": [item("i1"), item("i2")],
    "C06_independent_plus_dependent": [item("i1"), dependent("d1", "g1")],
    "C07_three_independent_two_families_plus_dependent": [
        item("i1", family="f1"),
        item("i2", family="f2"),
        item("i3", family="f1"),
        dependent("d1", "g1", family="f2"),
    ],
    "C08_ten_copies_one_lineage": [dependent(f"d{n}", "g1") for n in range(10)],
    "C09_dependent_contradiction_against_unknown_support": [
        unknown("u1"),
        dependent("c1", "g1", direction=D.CONTRADICTS),
        dependent("c2", "g2", direction=D.CONTRADICTS),
    ],
    "C10_contradiction_only": [
        item("c1", direction=D.CONTRADICTS),
        dependent("c2", "g1", direction=D.CONTRADICTS),
    ],
    "C11_single_dependent_market_activity": [
        dependent("m1", "g1", category=C.MARKET_ACTIVITY),
    ],
    "C12_reproducibility_fixture": [
        item("a", q=0.8, family="f1"),
        item("b", q=0.6, family="f2"),
        item("c", q=0.4, direction=D.CONTRADICTS),
        dependent("d", "g1", q=0.5),
        unknown("e", q=0.7),
    ],
    # --- adversarial ---------------------------------------------------------------------------
    "A01_zero_support": [],
    "A02_one_independent_one_unknown": [item("i1"), unknown("u1")],
    "A03_one_independent_two_dependent_lineages": [
        item("i1"),
        dependent("d1", "g1"),
        dependent("d2", "g2"),
    ],
    "A04_two_independent_plus_dependent_lineages_same_family": [
        item("i1", family="f1"),
        item("i2", family="f1"),
        dependent("d1", "g1", family="f2"),
        dependent("d2", "g2", family="f2"),
    ],
    "A05_three_independent_one_family_second_family_only_dependent": [
        item("i1", family="f1"),
        item("i2", family="f1"),
        item("i3", family="f1"),
        dependent("d1", "g1", family="f2"),
    ],
    "A06_mixed_all_three_states_with_contradiction": [
        item("i1", family="f1"),
        dependent("d1", "g1", family="f2"),
        dependent("d2", "g2", family="f2"),
        unknown("u1", family="f3"),
        item("c1", direction=D.CONTRADICTS),
        dependent("c2", "g3", direction=D.CONTRADICTS),
    ],
    "A07_dependent_direct_validation": [
        dependent("v1", "g1", category=C.DIRECT_VALIDATION),
        dependent("v2", "g2", category=C.DIRECT_VALIDATION),
    ],
    "A08_unknown_market_activity_only": [unknown("m1", category=C.MARKET_ACTIVITY)],
    "A09_same_lineage_both_directions": [
        dependent("d1", "g1"),
        dependent("d2", "g1", direction=D.CONTRADICTS),
    ],
    "A10_independent_contradiction_three_groups": [
        unknown("u1"),
        item("c1", direction=D.CONTRADICTS),
        item("c2", direction=D.CONTRADICTS),
        item("c3", direction=D.CONTRADICTS, family="f2"),
    ],
    "A11_three_independent_two_families": [
        item("i1", family="f1"),
        item("i2", family="f2"),
        item("i3", family="f1"),
    ],
    "A12_three_dependent_lineages_plus_two_independent_two_families": [
        item("i1", family="f1"),
        item("i2", family="f2"),
        dependent("d1", "g1", family="f1"),
        dependent("d2", "g2", family="f2"),
        dependent("d3", "g3", family="f1"),
    ],
}

#: Levels the operator's brief fixes, before and after the repair.
EXPECTED_LEVELS: dict[str, tuple[int, int]] = {
    "C01_all_unknown": (1, 1),
    "C02_one_dependent_lineage_plus_unknown": (1, 1),
    "C03_two_dependent_lineages": (2, 1),
    "C04_three_dependent_lineages_two_families": (3, 1),
    "C05_two_independent": (2, 2),
    "C06_independent_plus_dependent": (2, 1),
    "C07_three_independent_two_families_plus_dependent": (3, 3),
    "C08_ten_copies_one_lineage": (1, 1),
    "C11_single_dependent_market_activity": (4, 4),
    "C12_reproducibility_fixture": (3, 2),
}


def permutations(items: list[EvidenceItem], count: int = 6) -> list[list[EvidenceItem]]:
    """The forward order, the reversed order, and seeded shuffles. Deterministic."""
    orders = [list(items), list(reversed(items))]
    rng = random.Random(1852)  # noqa: S311 -- a seeded order, not a secret
    for _ in range(count):
        shuffled = list(items)
        rng.shuffle(shuffled)
        orders.append(shuffled)
    return orders
