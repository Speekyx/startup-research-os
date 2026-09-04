"""Reviewed reliability: what it applies to, what it rests on, how it is found.

Mission 1.14. Full specification:
`docs/data/evidence-reliability-contract-v1.md`. Scope and binding decisions:
ADR-026.

**Reliability is purpose-relative.** The same measurement is dependable evidence
for one kind of proposition and worthless for another, so a number attached to a
*source* is always wrong for something:

    source_reliability["world-bank"] = 0.95     forbidden. A platform is not a
                                                reliability
    reliability = 0.5 because unknown           forbidden. A measurement
                                                claiming the middle

An assessment therefore applies to a **five-part scope** -- three parts naming
the measurement, two naming the purpose -- and matches only when all five agree.
`world-bank` alone matches nothing.

**This package names no source.** It matches data against data.
`packages/evidence-aggregation` may not contain a registered source id at all
(asserted against the catalog), which is what keeps source identity out of the
mathematics; the resolver lives here, on the same side of the seam as the row
adapter, so that guard stays intact.

**Nothing here reaches a network, a model, an embedder or a database.** The
package depends on `sros_contracts` and the standard library.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from sros_contracts import (
    ClaimType,
    ReliabilityAssessmentOrigin,
    ReliabilityBasisType,
    ReliabilityResolutionOutcome,
)

__all__ = [
    "DOCUMENT_BACKED_BASIS_TYPES",
    "ReliabilityAssessment",
    "ReliabilityBasis",
    "ReliabilityBinding",
    "ReliabilityResolution",
    "ReliabilityScope",
    "assessment_key",
    "canonical_json",
    "resolve_reliability",
]


# Basis types that name a RETRIEVED DOCUMENT. `REVIEWER_DOCUMENTED_JUDGEMENT` is
# deliberately absent: reasoning about documents is permitted alongside them and
# never instead of them. On its own it is an opinion with a citation field,
# which is exactly what "the publisher is reputable" amounts to.
DOCUMENT_BACKED_BASIS_TYPES: frozenset[ReliabilityBasisType] = frozenset(
    t for t in ReliabilityBasisType if t is not ReliabilityBasisType.REVIEWER_DOCUMENTED_JUDGEMENT
)


def canonical_json(payload: object) -> str:
    """Sorted keys, no incidental whitespace, stable separators."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class ReliabilityScope:
    """What an assessment applies to: a MEASUREMENT, for a PURPOSE.

    The first three fields name what was measured and how it was normalized. The
    last two name what the evidence is being used *for*, and they are what makes
    the scope purpose-relative rather than source-shaped.

    `proposition_kind` is not invented here. Mission 1.13.1 put a discriminator
    at the head of every `proposition_facts` object so two proposition shapes
    could not collide in a hash; it names what a claim asserts IN KIND, which is
    precisely what "purpose" means in "reliability is purpose-relative".

    **`signal_type_id` is deliberately absent.** The derivation between a
    measurement and a proposition is the interpreter's business, and whether it
    read the Signal correctly is `extraction_confidence` -- a different field
    answering a different question.
    """

    source_id: str
    resource_id: str
    record_kind_id: str
    claim_type: ClaimType
    proposition_kind: str

    def __post_init__(self) -> None:
        for name in ("source_id", "resource_id", "record_kind_id", "proposition_kind"):
            if not str(getattr(self, name)).strip():
                raise ValueError(
                    f"a reliability scope names its {name}. A scope missing one part would "
                    "match more evidence than it was reviewed for, which is how a "
                    "purpose-relative judgement becomes a source coefficient"
                )

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "resource_id": self.resource_id,
            "record_kind_id": self.record_kind_id,
            "claim_type": self.claim_type.value,
            "proposition_kind": self.proposition_kind,
        }

    @property
    def key(self) -> str:
        return assessment_key(self)


def assessment_key(scope: ReliabilityScope) -> str:
    """WHICH scope, deterministically.

    Two reviewers assessing the same scope collide on one key; a reviewer
    revisiting a scope is recognised as revisiting it. The same construction
    `proposition_key` uses one layer down, and for the same reason.

    Never versioned: `(assessment_key, version)` is the row.
    """
    return hashlib.sha256(canonical_json(scope.to_json()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReliabilityBasis:
    """One retrieved document, or one piece of reasoning about the others.

    Shaped after `registry.source_policy_evidence`, deliberately: the system
    already has a pattern for "this judgement rests on these retrieved
    documents", and an epistemic review needs the same discipline. Full
    documents are not stored -- a reference, a section pointer, a short
    summarized finding and a fingerprint.
    """

    basis_type: ReliabilityBasisType
    document_title: str
    summarized_finding: str
    document_url: str | None = None
    section_reference: str | None = None
    excerpt: str | None = None
    retrieved_at: datetime | None = None
    effective_at: datetime | None = None
    document_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if not self.document_title.strip() or not self.summarized_finding.strip():
            raise ValueError(
                "a basis names a document and says what it found. A citation with no "
                "finding cannot be checked by a later reviewer"
            )
        if self.basis_type in DOCUMENT_BACKED_BASIS_TYPES and (
            not (self.document_url or "").strip() or self.retrieved_at is None
        ):
            raise ValueError(
                f"a {self.basis_type.value} basis names a retrieved document and when "
                "it was retrieved. A methodology statement that cannot be re-fetched "
                "is a memory of one"
            )
        if self.excerpt is not None and len(self.excerpt) > 1000:
            raise ValueError(
                "a long excerpt is a copy. The cap keeps this a reference rather than a "
                "mirror of third-party text, exactly as the policy-evidence table does"
            )

    @property
    def is_document_backed(self) -> bool:
        return self.basis_type in DOCUMENT_BACKED_BASIS_TYPES

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "basis_type": self.basis_type.value,
            "document_title": self.document_title,
            "summarized_finding": self.summarized_finding,
        }
        for name in ("document_url", "section_reference", "document_fingerprint"):
            value = getattr(self, name)
            if value is not None:
                payload[name] = value
        if self.retrieved_at is not None:
            payload["retrieved_at"] = self.retrieved_at.isoformat()
        return payload


@dataclass(frozen=True)
class ReliabilityAssessment:
    """A reviewed statement that this measurement has reliability R for this purpose.

    Superseded, never updated: an aggregation that used version N must still be
    able to read version N.
    """

    id: str
    scope: ReliabilityScope
    version: int
    reliability: float
    origin: ReliabilityAssessmentOrigin
    rationale: str
    stated_limitation: str
    reviewed_by: str
    reviewed_at: datetime
    basis: tuple[ReliabilityBasis, ...] = ()
    calibration_dataset_ref: str | None = None
    # Which review PROCEDURE produced this judgement (Mission 1.42.1, migration
    # 0032). `None` means the review predates any rubric -- which is true of
    # every assessment made before one existed -- and never that the reviewer
    # worked without one. Not backfilled, because a rubric id on a review that
    # did not use one is fabricated provenance.
    review_rubric_id: str | None = None
    review_rubric_version: str | None = None
    superseded_at: datetime | None = None
    superseded_reason: str | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("an assessment's first version is 1")
        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError(
                f"reliability {self.reliability} is outside [0,1]. Out of range is rejected "
                "rather than clamped: it means the reviewer is on a different scale, and "
                "clamping would hide that behind a plausible number"
            )
        if not self.rationale.strip() or not self.stated_limitation.strip():
            raise ValueError(
                "an assessment says what its value asserts AND what bounds it. A "
                "reliability with no stated limitation is a number nobody can argue with"
            )
        if not self.reviewed_by.strip():
            raise ValueError(
                "an assessment names who reviewed it. An unattributed judgement is one "
                "nobody can be asked about, and a model may not stand in for a reviewer"
            )
        calibrated = self.origin is ReliabilityAssessmentOrigin.CALIBRATED_EMPIRICALLY
        if calibrated and not (self.calibration_dataset_ref or "").strip():
            raise ValueError(
                "a CALIBRATED_EMPIRICALLY assessment names its calibration dataset. A "
                "calibration nobody can re-run is a claim, not a calibration "
                "(evidence-aggregation-framework-v1.md §12)"
            )
        if not calibrated and self.calibration_dataset_ref:
            raise ValueError(
                f"a {self.origin.value} assessment may not name a calibration dataset. "
                "Human review is not statistical calibration however careful it was "
                "(Mission 1.14 §22)"
            )
        if not any(item.is_document_backed for item in self.basis):
            raise ValueError(
                "an assessment rests on at least one retrieved document about the "
                "measurement. Reviewer reasoning is permitted alongside those and never "
                "instead of them: on its own it is an opinion with a citation field, "
                "which is what 'the publisher is reputable' amounts to"
            )
        # Supersession is all-or-nothing, and the check is written so a
        # half-filled value cannot slip through as NULL -- migration 0017's
        # lesson, restated where the object is built.
        filled = sum(1 for v in (self.superseded_at, self.superseded_reason) if v is not None)
        if filled == 1:
            raise ValueError(
                "a superseded assessment records when and why. Half a supersession is a "
                "withdrawal nobody can explain"
            )

        if (self.review_rubric_id is None) != (self.review_rubric_version is None):
            raise ValueError(
                "rubric provenance is both halves or neither. An id with no version "
                "names a moving target, and a version with no id names nothing"
            )

    @property
    def is_current(self) -> bool:
        return self.superseded_at is None

    @property
    def key(self) -> str:
        return self.scope.key

    def binding(self) -> ReliabilityBinding:
        return ReliabilityBinding(
            assessment_id=self.id,
            assessment_key=self.key,
            version=self.version,
            origin=self.origin,
            reliability=self.reliability,
            reviewed_by=self.reviewed_by,
            reviewed_at=self.reviewed_at,
            review_rubric_id=self.review_rubric_id,
            review_rubric_version=self.review_rubric_version,
        )


@dataclass(frozen=True)
class ReliabilityBinding:
    """Exactly which assessment produced a number, recorded with the result.

    ADR-026 Decision 2. A score whose coefficients cannot be reconstructed is a
    score nobody can check, so an aggregation records the binding per row rather
    than the value alone.
    """

    assessment_id: str
    assessment_key: str
    version: int
    origin: ReliabilityAssessmentOrigin
    reliability: float
    reviewed_by: str
    reviewed_at: datetime
    review_rubric_id: str | None = None
    review_rubric_version: str | None = None

    def to_json(self) -> dict[str, object]:
        return {
            "assessment_id": self.assessment_id,
            "assessment_key": self.assessment_key,
            "version": self.version,
            "origin": self.origin.value,
            "reliability": self.reliability,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat(),
            "review_rubric_id": self.review_rubric_id,
            "review_rubric_version": self.review_rubric_version,
        }


@dataclass(frozen=True)
class ReliabilityResolution:
    """What happened when one Evidence row asked for a reliability value."""

    outcome: ReliabilityResolutionOutcome
    reliability: float | None = None
    binding: ReliabilityBinding | None = None
    detail: str = ""
    candidates: tuple[str, ...] = field(default=())

    @property
    def scorable(self) -> bool:
        """Whether this row has a reliability at all.

        Not whether it will be scored: `q_i = min(components)` needs every
        component, and reliability is one of five.
        """
        return self.reliability is not None

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {"outcome": self.outcome.value, "detail": self.detail}
        if self.reliability is not None:
            payload["reliability"] = self.reliability
        if self.binding is not None:
            payload["binding"] = self.binding.to_json()
        if self.candidates:
            payload["candidates"] = list(self.candidates)
        return payload


def resolve_reliability(
    *,
    scope: ReliabilityScope | None,
    candidates: Sequence[ReliabilityAssessment] = (),
    supplied: float | None = None,
) -> ReliabilityResolution:
    """Find the one applicable assessment, or say precisely why there is none.

    **Precedence.** A value already on the Evidence row wins and no assessment is
    consulted. A statement about *that record* is more specific than a
    class-level judgement, and consulting both would create two answers to one
    question -- the mistake Mission 1.13 fixed by dropping
    `evidence.claim_type`, avoided here before the second answer exists.

    **Zero, one, many** (ADR-026 Decision 2):

        0    NO_APPLICABLE_ASSESSMENT -- reliability stays NULL
        1    RESOLVED -- the value, with its binding
        >1   AMBIGUOUS_ASSESSMENTS -- refused

    Never the closest: "closest" needs a distance nobody defined. Never the
    maximum: that is optimism with a mechanism. Never the mean: averaging two
    competing reviewed judgements produces a third judgement nobody made and
    nobody can defend.

    A partial unique index makes the many-case unreachable through the ordinary
    path. This refuses anyway, because a guard that trusts another guard is one
    schema change away from trusting nothing.
    """
    if supplied is not None:
        if not 0.0 <= supplied <= 1.0:
            raise ValueError(f"supplied reliability {supplied} is outside [0,1]")
        return ReliabilityResolution(
            outcome=ReliabilityResolutionOutcome.DIRECTLY_SUPPLIED,
            reliability=supplied,
            detail=(
                "the evidence record carries its own reliability, which is more specific "
                "than a class-level assessment. No assessment was consulted"
            ),
        )

    if scope is None:
        return ReliabilityResolution(
            outcome=ReliabilityResolutionOutcome.NO_APPLICABLE_ASSESSMENT,
            detail=(
                "this evidence record cannot state its measurement-and-purpose scope, so "
                "no assessment can apply to it. Reliability stays unknown"
            ),
        )

    key = scope.key
    matching = [a for a in candidates if a.key == key]
    current = [a for a in matching if a.is_current]

    if len(current) == 1:
        assessment = current[0]
        return ReliabilityResolution(
            outcome=ReliabilityResolutionOutcome.RESOLVED,
            reliability=assessment.reliability,
            binding=assessment.binding(),
            detail=f"{assessment.origin.value} assessment v{assessment.version}",
        )

    if len(current) > 1:
        return ReliabilityResolution(
            outcome=ReliabilityResolutionOutcome.AMBIGUOUS_ASSESSMENTS,
            detail=(
                f"{len(current)} current assessments cover this scope. Refused: choosing "
                "one would need a rule nobody wrote, and averaging two competing reviewed "
                "judgements produces a third that nobody made"
            ),
            candidates=tuple(sorted(a.id for a in current)),
        )

    if matching:
        return ReliabilityResolution(
            outcome=ReliabilityResolutionOutcome.SUPERSEDED_ONLY,
            detail=(
                f"{len(matching)} assessment(s) cover this scope and every one is "
                "superseded. Somebody reviewed this and withdrew it, which is a different "
                "fact from nobody having looked"
            ),
            candidates=tuple(sorted(a.id for a in matching)),
        )

    return ReliabilityResolution(
        outcome=ReliabilityResolutionOutcome.NO_APPLICABLE_ASSESSMENT,
        detail=(
            "no assessment covers this measurement for this purpose. Reliability stays "
            "NULL and the record is NON_SCORABLE, which is the honest state: a default "
            "here would be the source coefficient this layer exists to prevent"
        ),
    )


def scope_from_claim(
    *,
    source_id: str,
    resource_id: str,
    record_kind_id: str,
    claim_type: ClaimType,
    proposition_facts: Mapping[str, object],
) -> ReliabilityScope | None:
    """The scope an Evidence row falls under, or nothing.

    The purpose comes from the claim's own `proposition_facts` discriminator.
    A claim whose facts name no `proposition` kind cannot state its purpose, and
    a scope guessed for it would apply an assessment that was reviewed for
    something else -- so this returns `None` and the row stays NON_SCORABLE.
    """
    kind = proposition_facts.get("proposition")
    if not isinstance(kind, str) or not kind.strip():
        return None
    if not source_id.strip() or not resource_id.strip() or not record_kind_id.strip():
        return None
    return ReliabilityScope(
        source_id=source_id,
        resource_id=resource_id,
        record_kind_id=record_kind_id,
        claim_type=claim_type,
        proposition_kind=kind,
    )
