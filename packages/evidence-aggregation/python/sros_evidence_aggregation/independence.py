"""Independence grouping: the part that stops counting from becoming believing.

Mission 1.1 §10–§13.

    Original product announcement
      -> blog article repeating it
        -> forum post linking the article

Three records. One origin. A system that counts them as three independent
observations has learned that a press release is market evidence, which is the
single failure `evidence-confidence-framework-v1.md` §4 was written against.

**Within a group, the strongest member counts.**

    group_strength = max(q_1 ... q_n)

Not the sum, because ten copies would then overwhelm one original. Not the mean,
because adding weak copies of a strong observation would *weaken* it, and a
duplicate is not counter-evidence. Every member is retained for provenance;
only the arithmetic collapses.

**Unknown provenance is its own state, and it is conservative.**

Most evidence in a real system has unestablished provenance — deduplication is
`nlp`'s job, D-12 is open, and until then nothing has traced these lineages. The
tempting reading is that unknown means probably independent. It does not: the
records most likely to share an origin are exactly the ones that arrive
together in bulk, so unknown correlates with dependence rather than against it.

V1 therefore collapses *all* unknown-provenance records for one claim and one
direction into a single group. The strongest counts; the rest raise observed
volume and nothing else. This is deliberately strict, it is stated as strict,
and it is the kind of parameter calibration can later relax with evidence.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from sros_contracts import EvidenceDirection, EvidenceIndependenceState

from .items import EvidenceItem, ItemContribution

__all__ = ["GroupKind", "IndependenceGroup", "UNKNOWN_GROUP_ID", "group_by_independence"]

# One bucket per direction. Not per source, not per session: a shared id is the
# mechanism by which unknown records are prevented from accumulating.
UNKNOWN_GROUP_ID = "__unknown_independence__"


class GroupKind(StrEnum):
    """Why these records are one group.

    Kept in the explanation because the three cases warrant different follow-up.
    A DECLARED_DEPENDENT group means somebody traced the lineage. An UNKNOWN
    group means nobody has yet, and it is the one that shrinks a result the most
    — so a reader must be able to see it and go do the tracing.
    """

    INDEPENDENT = "INDEPENDENT"
    DECLARED_DEPENDENT = "DECLARED_DEPENDENT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class IndependenceGroup:
    """One contribution, and every record behind it."""

    group_id: str
    kind: GroupKind
    direction: EvidenceDirection
    strength: float
    representative_evidence_id: str
    member_evidence_ids: tuple[str, ...]

    @property
    def collapsed_member_count(self) -> int:
        """Records present that added no strength. The duplicate count, in effect."""
        return max(0, len(self.member_evidence_ids) - 1)

    def to_json(self) -> dict[str, object]:
        return {
            "group_id": self.group_id,
            "kind": self.kind.value,
            "direction": self.direction.value,
            "strength": self.strength,
            "representative_evidence_id": self.representative_evidence_id,
            "member_evidence_ids": list(self.member_evidence_ids),
            "collapsed_member_count": self.collapsed_member_count,
        }


def _group_key(item: EvidenceItem) -> tuple[GroupKind, str]:
    state = item.independence_state
    if state is EvidenceIndependenceState.KNOWN_DEPENDENT:
        # Two dependent records with DIFFERENT lineages are two groups. Sharing
        # the state does not make them share an origin.
        return GroupKind.DECLARED_DEPENDENT, str(item.independence_group_id)
    if state is EvidenceIndependenceState.KNOWN_INDEPENDENT:
        # Its own group. Independence was established, so it accumulates.
        return GroupKind.INDEPENDENT, item.evidence_id
    return GroupKind.UNKNOWN, UNKNOWN_GROUP_ID


def group_by_independence(
    items: Iterable[EvidenceItem],
    contributions: dict[str, ItemContribution],
    direction: EvidenceDirection,
) -> list[IndependenceGroup]:
    """Collapse scorable records of one direction into contribution groups.

    Non-scorable records are excluded from the arithmetic but are NOT excluded
    from the explanation, which the engine assembles separately. A record that
    dropped out for a missing timestamp still tells a reader something.

    The returned list is sorted by group id, and members within a group are
    sorted too. Ordering the inputs differently must not change the output —
    §30.7 — and floating-point addition downstream is not associative, so
    determinism has to be built in here rather than hoped for.
    """
    buckets: dict[tuple[GroupKind, str], list[tuple[float, str]]] = {}

    for item in items:
        if item.direction is not direction:
            continue
        contribution = contributions.get(item.evidence_id)
        if contribution is None or not contribution.scorable or contribution.q is None:
            continue
        buckets.setdefault(_group_key(item), []).append((contribution.q, item.evidence_id))

    groups: list[IndependenceGroup] = []
    for (kind, group_id), members in buckets.items():
        # Sort by strength, then by id: ties must resolve the same way every
        # run, or the representative in the explanation would wobble between
        # identical results.
        ordered: Sequence[tuple[float, str]] = sorted(members, key=lambda m: (-m[0], m[1]))
        strength, representative = ordered[0]
        groups.append(
            IndependenceGroup(
                group_id=group_id,
                kind=kind,
                direction=direction,
                strength=strength,
                representative_evidence_id=representative,
                member_evidence_ids=tuple(sorted(evidence_id for _, evidence_id in ordered)),
            )
        )

    return sorted(groups, key=lambda g: (g.kind.value, g.group_id))
