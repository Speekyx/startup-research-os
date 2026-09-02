"""The Evidence Packet: what MAY support one future opportunity hypothesis.

Mission 1.28 §7. Deterministic, immutable, versioned, and it contains
**references, never copied truth**.

**The packet holds ids and facts about ids.** It does not hold claim statements,
source text, magnitudes or any restatement of what a source said. That is the
rule that keeps a packet from becoming a second place an assertion lives -- the
same argument ADR-024 made when it refused a candidate-claim table. If a consumer
wants the statement it reads `research.claim_revisions`, where the revision that
was current at packet time is still addressable.

**`packet_id` is derived, not assigned.** sha256 over the procedure versions and
the ordered evidence ids, so the same inputs under the same procedure produce the
same packet and a changed procedure produces a different one. The construction
TIME is excluded, exactly as `observation_key` excludes the retrieval time: a
packet rebuilt tomorrow from the same evidence is the same packet, and a packet
built from different evidence cannot pretend to be.

**A packet reports its own composition rather than summarising it.** Source
families, independence states and dimensions are exposed as sets with counts. It
never says "multiple independent sources": Mission 1.28 §13 forbids that unless
independence is established, and `independence_summary` is built so the sentence
cannot be constructed from a packet whose rows are all `UNKNOWN`.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field

from .dimensions import EvidenceDimension
from .eligibility import ELIGIBILITY_PROCEDURE_VERSION, PacketEligibility
from .facets import EvidenceFacets, IndependenceState
from .grouping import GROUPING_PROCEDURE_VERSION, SubjectKey
from .mapping import DIMENSION_MAP_VERSION, counting_dimensions

__all__ = [
    "PACKET_PROCEDURE_VERSION",
    "OpportunityEvidencePacket",
    "build_packet",
]

PACKET_PROCEDURE_VERSION = "opportunity-evidence-packet@1.0.0"


@dataclass(frozen=True)
class OpportunityEvidencePacket:
    """An immutable, reference-only gathering of evidence about one subject."""

    packet_id: str
    packet_version: str
    subject: SubjectKey | None
    subject_label: str

    #: Ordered and de-duplicated. These are the packet's identity.
    evidence_ids: tuple[str, ...]
    claim_ids: tuple[str, ...]
    signal_type_ids: tuple[str, ...]

    source_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    use_profile_ids: tuple[str, ...]

    dimensions: frozenset[EvidenceDimension]
    counting_dimensions: frozenset[EvidenceDimension]
    #: One bound per contributing signal type, so no dimension can be read
    #: without the sentence that limits it.
    dimension_bounds: tuple[str, ...]

    eligibility_counts: dict[str, int]
    independence_counts: dict[str, int]
    reliability_status_counts: dict[str, int]
    observed_at_present: int

    procedures: dict[str, str] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.evidence_ids)

    @property
    def scoring_eligible_count(self) -> int:
        return self.eligibility_counts.get(PacketEligibility.ELIGIBLE_SCORING.value, 0)

    @property
    def single_source_family(self) -> bool:
        return len(self.source_families) == 1

    def independence_summary(self) -> str:
        """A sentence about independence that cannot overstate it.

        Mission 1.28 §13. Two rows are not independent because they are two rows,
        and this deployment has never established independence for anything: every
        Evidence row in the corpus carries `UNKNOWN`. The phrase *multiple
        independent sources* is unreachable from here -- it is emitted only when
        every row is `KNOWN_INDEPENDENT` and more than one source family
        contributed, which no packet in this deployment satisfies.
        """
        unknown = self.independence_counts.get(IndependenceState.UNKNOWN.value, 0)
        dependent = self.independence_counts.get(IndependenceState.KNOWN_DEPENDENT.value, 0)
        independent = self.independence_counts.get(IndependenceState.KNOWN_INDEPENDENT.value, 0)
        if unknown:
            return (
                f"independence is UNKNOWN for {unknown} of {self.size} rows; this packet "
                "does not establish that its evidence is independent, and the count of "
                "rows is not a count of independent findings"
            )
        if dependent:
            return (
                f"{dependent} of {self.size} rows are KNOWN_DEPENDENT and share an "
                "origin; they count once, not once each"
            )
        if independent == self.size and len(self.source_families) > 1:
            return (
                f"all {self.size} rows are KNOWN_INDEPENDENT across "
                f"{len(self.source_families)} source families"
            )
        return (
            f"all {self.size} rows are KNOWN_INDEPENDENT within a single source family "
            f"({self.source_families[0] if self.source_families else 'none'}); one "
            "family is not multiple independent sources"
        )


def _ordered(values: Iterable[object]) -> tuple[str, ...]:
    return tuple(sorted({str(v) for v in values if v is not None}))


def build_packet(
    subject: SubjectKey | None,
    subject_label: str,
    members: tuple[tuple[EvidenceFacets, PacketEligibility], ...],
) -> OpportunityEvidencePacket:
    """Assemble a packet from rows already assessed for eligibility.

    Members are sorted by `evidence_id` before hashing, so packet identity does
    not depend on the order a query returned rows in -- the same reason a Signal's
    inputs are ordered before entering its derivation identity, and the same
    failure avoided: an identity chosen by the query optimiser.
    """
    ordered = tuple(sorted(members, key=lambda m: m[0].evidence_id))
    facets = tuple(m[0] for m in ordered)

    evidence_ids = tuple(f.evidence_id for f in facets)
    dimensions: frozenset[EvidenceDimension] = (
        frozenset().union(*(f.dimensions for f in facets)) if facets else frozenset()
    )

    digest = hashlib.sha256(
        "\x00".join(
            (
                PACKET_PROCEDURE_VERSION,
                GROUPING_PROCEDURE_VERSION,
                DIMENSION_MAP_VERSION,
                ELIGIBILITY_PROCEDURE_VERSION,
                subject_label,
                *evidence_ids,
            )
        ).encode()
    ).hexdigest()

    return OpportunityEvidencePacket(
        packet_id=digest,
        packet_version=PACKET_PROCEDURE_VERSION,
        subject=subject,
        subject_label=subject_label,
        evidence_ids=evidence_ids,
        claim_ids=_ordered(f.claim_id for f in facets),
        signal_type_ids=_ordered(f.signal_type_id for f in facets),
        source_ids=_ordered(f.source_id for f in facets),
        source_families=_ordered(f.source_family for f in facets),
        use_profile_ids=_ordered(f.use_profile_id for f in facets),
        dimensions=dimensions,
        counting_dimensions=counting_dimensions(dimensions),
        dimension_bounds=tuple(sorted({f.dimension_bound for f in facets if f.dimension_bound})),
        eligibility_counts=dict(Counter(e.value for _, e in ordered)),
        independence_counts=dict(Counter(f.independence_state.value for f in facets)),
        reliability_status_counts=dict(Counter(f.reliability_status.value for f in facets)),
        observed_at_present=sum(1 for f in facets if f.observed_at is not None),
        procedures={
            "packet": PACKET_PROCEDURE_VERSION,
            "grouping": GROUPING_PROCEDURE_VERSION,
            "dimension_map": DIMENSION_MAP_VERSION,
            "eligibility": ELIGIBILITY_PROCEDURE_VERSION,
        },
    )
