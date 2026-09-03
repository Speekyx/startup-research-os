"""A packet that knows which of its rows are about its subject.

Mission 1.34 §14. The procedure is `scope-aware-opportunity-packet@1.0.0`.

**It VERSIONS the packet rather than changing it.** `build_packet` and
`opportunity-evidence-packet@1.0.0` are untouched, so every existing packet
reproduces byte for byte and `opportunity-sufficiency@1.0.0` sees exactly what it
saw before (§10, §11). A scoped packet is built alongside, and its DIRECT half is
required to equal the legacy packet -- asserted, not assumed, because the whole
compatibility claim rests on it.

**Sufficiency reads the DIRECT half and nothing else.** That is the single most
important line in this module. A contextual row is in `contextual_evidence`,
contributes to `contextual_dimensions_by_scope`, and reaches
`direct_counting_dimensions` through no path at all -- so a future category
observation cannot satisfy a diversity requirement written for direct product
evidence (§10). Multi-scope sufficiency is a separate, undesigned, unactivated
question; see `opportunity-multiscope-sufficiency-design-v1.md`.

**Dimensions are never returned bare.** `direct_dimensions` exists because
sufficiency needs a set of dimensions observed OF THE SUBJECT, and it is built
only from rows whose role is DIRECT. There is no property anywhere on this class
that unions direct and contextual dimensions, because that union is the sentence
*Docker supports MARKET_ACTIVITY* and it must not be one attribute access away.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from .dimensions import EvidenceDimension
from .mapping import counting_dimensions
from .scope_relations import ScopeRelation
from .scoped_evidence import (
    SCOPE_AWARE_EVIDENCE_VERSION,
    ScopedDimension,
    ScopedEvidence,
)
from .scopes import OBSERVATION_SCOPE_VERSION, ObservationScope

__all__ = [
    "SCOPED_PACKET_VERSION",
    "ScopedOpportunityEvidencePacket",
    "build_scoped_packet",
]

SCOPED_PACKET_VERSION = "scope-aware-opportunity-packet@1.0.0"


@dataclass(frozen=True)
class ScopedOpportunityEvidencePacket:
    """Direct and contextual evidence, kept apart by construction."""

    packet_id: str
    packet_version: str

    opportunity_scope: ObservationScope
    subject_label: str

    direct_evidence: tuple[ScopedEvidence, ...]
    contextual_evidence: tuple[ScopedEvidence, ...]
    #: Every edge that admitted a contextual row, de-duplicated. Empty whenever
    #: `contextual_evidence` is empty, and a reader can check that.
    scope_relations: tuple[ScopeRelation, ...]

    #: Rows that were considered and refused, with the clause that refused them.
    #: Kept because a packet that silently dropped them would look like a packet
    #: nobody offered those rows to.
    refusals: tuple[tuple[str, str, str], ...]

    procedures: dict[str, str] = field(default_factory=dict)

    # ---------------------------------------------------------------- direct

    @property
    def direct_dimensions(self) -> frozenset[EvidenceDimension]:
        """Observed OF THE SUBJECT. The only set sufficiency may read."""
        if not self.direct_evidence:
            return frozenset()
        return frozenset().union(*(e.facets.dimensions for e in self.direct_evidence))

    @property
    def direct_counting_dimensions(self) -> frozenset[EvidenceDimension]:
        return counting_dimensions(self.direct_dimensions)

    @property
    def direct_evidence_ids(self) -> tuple[str, ...]:
        return tuple(e.facets.evidence_id for e in self.direct_evidence)

    # ------------------------------------------------------------ contextual

    @property
    def contextual_dimensions_by_scope(self) -> dict[str, tuple[ScopedDimension, ...]]:
        """Contextual dimensions, grouped by the scope they were observed at.

        Keyed by scope id rather than flattened, so there is no representation in
        which a contextual dimension appears without the scope that qualifies it.
        """
        grouped: dict[str, list[ScopedDimension]] = {}
        for evidence in self.contextual_evidence:
            for scoped in evidence.scoped_dimensions:
                grouped.setdefault(scoped.scope.scope_id, []).append(scoped)
        return {
            scope_id: tuple(sorted(items, key=lambda s: s.dimension.value))
            for scope_id, items in sorted(grouped.items())
        }

    @property
    def contextual_evidence_ids(self) -> tuple[str, ...]:
        return tuple(e.facets.evidence_id for e in self.contextual_evidence)

    # --------------------------------------------------------------- reports

    @property
    def role_counts(self) -> dict[str, int]:
        return dict(
            Counter(e.role.value for e in (*self.direct_evidence, *self.contextual_evidence))
        )

    def limitations(self) -> tuple[str, ...]:
        """What this packet does not establish, one sentence per contextual scope.

        A packet with no contextual evidence returns one sentence saying so,
        rather than an empty tuple: *no broader-scope context* is a fact worth
        putting in a report, and an empty list reads as nobody having asked.
        """
        if not self.contextual_evidence:
            return (
                "This packet holds no broader-scope contextual evidence. Every row in "
                "it is observed of the Opportunity's own subject.",
            )
        sentences = []
        for scope_id, scoped in self.contextual_dimensions_by_scope.items():
            names = ", ".join(sorted({s.dimension.value for s in scoped}))
            sentences.append(
                f"{names} are observed of {scope_id!r}, which contains this "
                f"Opportunity's subject. They are NOT observed of the subject, and "
                f"nothing in this packet establishes them for it."
            )
        return tuple(sentences)

    def statements(self) -> tuple[str, ...]:
        """Every scoped dimension as a sentence carrying its own scope (§26)."""
        return tuple(
            scoped.statement()
            for evidence in (*self.direct_evidence, *self.contextual_evidence)
            for scoped in evidence.scoped_dimensions
        )


def build_scoped_packet(
    opportunity_scope: ObservationScope,
    subject_label: str,
    admitted: tuple[ScopedEvidence, ...],
    refusals: tuple[tuple[str, str, str], ...] = (),
) -> ScopedOpportunityEvidencePacket:
    """Assemble from rows the §15 gate already admitted.

    Rows are sorted by `evidence_id` before hashing, for the reason `build_packet`
    sorts: an identity chosen by the query optimiser is not an identity. The
    digest covers the ROLES as well as the ids, so the same rows admitted under
    different roles are a different packet -- which they are, because they support
    different sentences.
    """
    ordered = tuple(sorted(admitted, key=lambda e: e.facets.evidence_id))
    direct = tuple(e for e in ordered if e.role.is_direct)
    contextual = tuple(e for e in ordered if not e.role.is_direct)

    relations: list[ScopeRelation] = []
    seen: set[tuple[str, str, str]] = set()
    for evidence in contextual:
        relation = evidence.admitting_relation
        if relation is None:  # unreachable: ScopedEvidence refuses it
            continue
        token = (
            relation.narrower_scope_id,
            relation.broader_scope_id,
            relation.relation_type.value,
        )
        if token not in seen:
            seen.add(token)
            relations.append(relation)

    digest = hashlib.sha256(
        "\x00".join(
            (
                SCOPED_PACKET_VERSION,
                OBSERVATION_SCOPE_VERSION,
                SCOPE_AWARE_EVIDENCE_VERSION,
                opportunity_scope.scope_id,
                *(f"{e.facets.evidence_id}:{e.role.value}" for e in ordered),
            )
        ).encode()
    ).hexdigest()

    return ScopedOpportunityEvidencePacket(
        packet_id=digest,
        packet_version=SCOPED_PACKET_VERSION,
        opportunity_scope=opportunity_scope,
        subject_label=subject_label,
        direct_evidence=direct,
        contextual_evidence=contextual,
        scope_relations=tuple(relations),
        refusals=refusals,
        procedures={
            "scoped_packet": SCOPED_PACKET_VERSION,
            "observation_scope": OBSERVATION_SCOPE_VERSION,
            "scope_aware_evidence": SCOPE_AWARE_EVIDENCE_VERSION,
        },
    )
