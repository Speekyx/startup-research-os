"""The result, and the lineage that makes it re-checkable.

Mission 1.1 §26–§28.

**No score without lineage.** A result carries every input decision behind it:
which records were considered, which were dropped and for what, which shared a
provenance group, which member represented each group, every `q` and every
component that produced it. A number a reader cannot take apart is a number they
can only believe or not.

**Reproducibility is built on a snapshot digest, not on a timestamp.** The
digest is a hash of the canonical form of the evidence set actually used. Two
runs over the same evidence and the same profile produce the same digest and the
same numbers; if either changed, the digest says so. That is what lets a later
recomputation be distinguished from the original rather than silently replacing
it — D-08 is not resolved here, but nothing here makes resolving it harder.

`computed_at` is deliberately excluded from `canonical_json()`. Including it
would make every rerun differ, which would defeat the byte-equality check that
proves the pipeline is deterministic.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime

from sros_contracts import EvidenceAggregationStatus

from .independence import IndependenceGroup
from .items import ItemContribution
from .levels import EvidenceLevelAssessment
from .masses import MassDecomposition

__all__ = ["GroupExplanation", "EvidenceAggregationResult", "snapshot_digest"]


def snapshot_digest(contributions: list[ItemContribution]) -> str:
    """A stable fingerprint of the evidence set as aggregation saw it.

    Over the CONTRIBUTIONS rather than the raw records, because that is what the
    result depends on: if extraction confidence is revised, the contribution
    changes, the digest changes, and a stored result is correctly identified as
    having been computed over different inputs.

    Sorted by evidence id so input ordering cannot change the digest.
    """
    payload = [c.to_json() for c in sorted(contributions, key=lambda c: c.evidence_id)]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class GroupExplanation:
    """Groups, split by direction, as the explanation presents them."""

    support: tuple[IndependenceGroup, ...]
    contradiction: tuple[IndependenceGroup, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "support": [g.to_json() for g in self.support],
            "contradiction": [g.to_json() for g in self.contradiction],
        }


@dataclass(frozen=True)
class EvidenceAggregationResult:
    """One claim's aggregated evidence, and everything needed to re-derive it."""

    claim_id: str

    aggregation_profile_id: str
    aggregation_profile_version: str
    aggregation_profile_status: str
    algorithm_version: str

    masses: MassDecomposition
    level: EvidenceLevelAssessment
    status: EvidenceAggregationStatus

    raw_evidence_count: int
    scorable_evidence_count: int
    neutral_evidence_count: int
    non_scorable_evidence_count: int
    independence_group_count: int
    support_group_count: int
    contradiction_group_count: int
    unknown_independence_count: int
    source_count: int
    source_family_count: int

    missing_requirements: tuple[str, ...]

    contributions: tuple[ItemContribution, ...]
    groups: GroupExplanation
    evidence_snapshot_digest: str
    computed_at: datetime

    calibrated: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)

    # -- the score -----------------------------------------------------------

    @property
    def evidence_score(self) -> float | None:
        """None when nothing was scorable. **Not 0.0.**

        A score of zero says the evidence was measured and found not to support
        the claim. No score says nothing was measured. Returning 0.0 for the
        second would be the single most damaging default in this package.
        """
        if self.status is EvidenceAggregationStatus.UNAVAILABLE:
            return None
        return self.masses.evidence_score

    @property
    def presented_evidence_score(self) -> int | None:
        """Rounded for display. `82`, never `82.37` (`scoring-framework-v1.1.md` §10)."""
        score = self.evidence_score
        return None if score is None else int(round(score))

    # -- serialisation -------------------------------------------------------

    def to_json(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "aggregation_profile_id": self.aggregation_profile_id,
            "aggregation_profile_version": self.aggregation_profile_version,
            "aggregation_profile_status": self.aggregation_profile_status,
            "algorithm_version": self.algorithm_version,
            "calibrated": self.calibrated,
            "evidence_score": self.evidence_score,
            **self.masses.to_json(),
            **self.level.to_json(),
            "aggregation_status": self.status.value,
            "counts": {
                "raw_evidence_count": self.raw_evidence_count,
                "scorable_evidence_count": self.scorable_evidence_count,
                "neutral_evidence_count": self.neutral_evidence_count,
                "non_scorable_evidence_count": self.non_scorable_evidence_count,
                "independence_group_count": self.independence_group_count,
                "support_group_count": self.support_group_count,
                "contradiction_group_count": self.contradiction_group_count,
                "unknown_independence_count": self.unknown_independence_count,
                "source_count": self.source_count,
                "source_family_count": self.source_family_count,
            },
            "missing_requirements": list(self.missing_requirements),
            "warnings": list(self.warnings),
            "evidence_snapshot_digest": self.evidence_snapshot_digest,
            "explanation": {
                "items": [c.to_json() for c in self.contributions],
                "groups": self.groups.to_json(),
            },
        }

    def canonical_json(self) -> str:
        """Byte-stable form. `computed_at` is excluded on purpose.

        Two runs over one snapshot under one profile must produce identical
        bytes. A wall-clock field inside would make that impossible to assert,
        and the assertion is what proves the pipeline has no hidden ordering or
        iteration dependence.
        """
        return json.dumps(self.to_json(), sort_keys=True, separators=(",", ":"))

    def explain(self) -> str:
        """A human-readable derivation. For review and for the sensitivity report."""
        lines = [
            f"claim {self.claim_id}",
            f"  profile {self.aggregation_profile_id} v{self.aggregation_profile_version} "
            f"[{self.aggregation_profile_status}]  algorithm {self.algorithm_version}",
            f"  status {self.status.value}"
            + ("" if self.calibrated else "   (parameters NOT calibrated)"),
            "",
            "  items",
        ]
        for contribution in sorted(self.contributions, key=lambda c: c.evidence_id):
            if contribution.scorable and contribution.q is not None:
                components = ", ".join(
                    f"{name}={value:.3f}"
                    for name, value in contribution.components.items()
                    if value is not None
                )
                lines.append(
                    f"    {contribution.evidence_id:<24} {contribution.direction.value:<12} "
                    f"q={contribution.q:.4f}  limited by {contribution.limiting_component}"
                )
                lines.append(f"        {components}")
            else:
                reasons = ", ".join(str(r) for r in contribution.non_scorable_reasons)
                lines.append(
                    f"    {contribution.evidence_id:<24} {contribution.direction.value:<12} "
                    f"NON-SCORABLE  {reasons}"
                )

        for label, groups in (
            ("support groups", self.groups.support),
            ("contradiction groups", self.groups.contradiction),
        ):
            lines.append("")
            lines.append(f"  {label}")
            if not groups:
                lines.append("    none")
            for group in groups:
                collapsed = (
                    f"  (+{group.collapsed_member_count} collapsed)"
                    if group.collapsed_member_count
                    else ""
                )
                lines.append(
                    f"    {group.group_id:<28} {group.kind.value:<18} "
                    f"g={group.strength:.4f}  via {group.representative_evidence_id}{collapsed}"
                )

        masses = self.masses
        score = self.evidence_score
        lines.extend(
            [
                "",
                f"  support_strength        {masses.support_strength:.4f}",
                f"  contradiction_strength  {masses.contradiction_strength:.4f}",
                f"  supported_mass          {masses.supported_mass:.4f}",
                f"  contradicted_mass       {masses.contradicted_mass:.4f}",
                f"  conflict_mass           {masses.conflict_mass:.4f}",
                f"  uncertainty_mass        {masses.uncertainty_mass:.4f}",
                "",
                "  EvidenceScore           " + ("unavailable" if score is None else f"{score:.2f}"),
                f"  EvidenceLevel           {self.level.level} ({self.level.label})",
            ]
        )
        if self.missing_requirements:
            lines.append("")
            lines.append("  missing")
            for requirement in self.missing_requirements:
                lines.append(f"    {requirement}")
        return "\n".join(lines)
