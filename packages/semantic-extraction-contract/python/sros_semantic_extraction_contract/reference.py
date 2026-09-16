"""Reference strength for semantic-extraction evaluation (Mission 1.85.5, N08-B single-human pilot).

The operator has no second independent human annotator. Rather than fabricate one, or let a model stand
in for one, this module names what a reference set is actually worth:

- SINGLE_HUMAN_REFERENCE: exactly one genuine, attested, complete human DEVELOPMENT annotation. Good
  enough for a development PILOT. It says nothing about whether another person would label the same way,
  so every inter-annotator metric is NOT_APPLICABLE_SINGLE_ANNOTATOR, never zero: a zero would claim a
  disagreement was measured.
- MULTI_HUMAN_REFERENCE: at least two independent human annotations plus adjudication. The stronger,
  preferred path of Mission 1.85.4, unchanged.
- AI_ASSISTED_PROVISIONAL: a model's annotation. Diagnostic only. It never satisfies a human gate, never
  enters a human agreement metric and is never stored with, or imported as, a human annotation.

The human origins keep their meaning: HUMAN_OPERATOR, HUMAN_EXPERT and HUMAN_NON_EXPERT still mean a
person labelled the records. Only how many such people exist changes what may be concluded.

HOLDOUT stays behind the stronger reference. There is deliberately no flag that lets a single-human
reference reach holdout: a later operator decision would have to change this code, visibly.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .annotation import (
    _MODEL_LIKE_IDS,
    ANNOTATION_STATES,
    ATTESTATION_FLAGS,
    ATTESTATION_ID,
    IMPORTER_VERSION,
    AnnotationOrigin,
)
from .labels import LABELS, LabelStatus

__all__ = [
    "AI_ASSISTED_PROVISIONAL",
    "HOLDOUT_POLICY",
    "INTER_ANNOTATOR_METRICS",
    "NOT_APPLICABLE_SINGLE_ANNOTATOR",
    "PILOT_NOT_CERTIFICATION",
    "PILOT_ROADMAP_STATUS",
    "PROHIBITED_PILOT_CLAIMS",
    "REFERENCE_MODEL_ID",
    "RESULT_SCOPE_DEVELOPMENT_PILOT",
    "ReferenceAssessment",
    "ReferenceStrength",
    "assess_reference",
    "holdout_reference_permitted",
    "human_reference_file_problems",
    "single_annotator_agreement",
]

REFERENCE_MODEL_ID = "semantic-reference-strength@1.0.0"
AI_ASSISTED_PROVISIONAL = "AI_ASSISTED_PROVISIONAL"
NOT_APPLICABLE_SINGLE_ANNOTATOR = "NOT_APPLICABLE_SINGLE_ANNOTATOR"
PILOT_NOT_CERTIFICATION = "PILOT_NOT_CERTIFICATION"
RESULT_SCOPE_DEVELOPMENT_PILOT = "DEVELOPMENT_PILOT"
HOLDOUT_POLICY = "HOLDOUT_REQUIRES_MULTI_HUMAN_OR_NEW_OPERATOR_DECISION"
PILOT_ROADMAP_STATUS = "DEVELOPMENT_PILOT_SINGLE_HUMAN_REFERENCE"
INTER_ANNOTATOR_METRICS = (
    "cohen_kappa",
    "krippendorff_alpha",
    "positive_specific_agreement",
    "negative_specific_agreement",
    "span_agreement_between_humans",
    "subject_agreement_between_humans",
)
PROHIBITED_PILOT_CLAIMS = (
    "INTER_HUMAN_RELIABILITY",
    "VALIDATED_HUMAN_CONSENSUS",
    "GENERALISATION_TO_HOLDOUT",
    "PRODUCTION_READINESS",
    "CALIBRATED_SEMANTIC_ACCURACY",
)


class ReferenceStrength(StrEnum):
    SINGLE_HUMAN_REFERENCE = "SINGLE_HUMAN_REFERENCE"
    MULTI_HUMAN_REFERENCE = "MULTI_HUMAN_REFERENCE"
    AI_ASSISTED_PROVISIONAL = AI_ASSISTED_PROVISIONAL
    NO_HUMAN_REFERENCE = "NO_HUMAN_REFERENCE"


def single_annotator_agreement() -> dict[str, str]:
    """Every inter-annotator metric for a single annotator: not measured, so not a number."""
    return dict.fromkeys(INTER_ANNOTATOR_METRICS, NOT_APPLICABLE_SINGLE_ANNOTATOR)


def _label_ids() -> set[str]:
    return {label.label_id for label in LABELS if label.status is not LabelStatus.NOT_SAFE}


def human_reference_file_problems(
    committed: Any, *, split_record_ids: set[str], surface_sha256_by_id: dict[str, str]
) -> list[str]:
    """Re-check a COMMITTED human annotation file before it may count as a reference.

    The importer already refused anything worse; this runs again on what is in the repository, so a file
    edited after import, or an AI file dropped next to the human ones, counts for nothing.
    """
    if not isinstance(committed, dict):
        return ["NOT_AN_OBJECT"]
    problems = []
    if committed.get("split") != "DEVELOPMENT":
        problems.append("NOT_DEVELOPMENT")
    if committed.get("importer") != IMPORTER_VERSION:
        problems.append("NOT_IMPORTED_BY_THE_HUMAN_IMPORTER")
    origin = committed.get("reference_origin")
    if origin == AI_ASSISTED_PROVISIONAL:
        problems.append("AI_ASSISTED_PROVISIONAL_IS_NEVER_A_HUMAN_REFERENCE")
    elif origin not in {o.value for o in AnnotationOrigin}:
        problems.append("ORIGIN_NOT_HUMAN")
    annotator = str(committed.get("annotator_id") or "").strip().lower()
    if not annotator or any(m in annotator for m in _MODEL_LIKE_IDS):
        problems.append("ANNOTATOR_ID_NOT_ACCEPTED")
    attestation = committed.get("attestation")
    if (
        not isinstance(attestation, dict)
        or attestation.get("attestation_id") != ATTESTATION_ID
        or attestation.get("annotator_id") != committed.get("annotator_id")
        or not attestation.get("attested_at")
        or any(attestation.get(flag) is not True for flag in ATTESTATION_FLAGS)
    ):
        problems.append("ATTESTATION_INVALID")
    started, completed = (
        committed.get("annotation_started_at"),
        committed.get("annotation_completed_at"),
    )
    if not started or not completed or str(started) > str(completed):
        problems.append("TIMESTAMPS_INVALID")
    records = committed.get("records")
    if not isinstance(records, list):
        return [*problems, "RECORDS_MISSING"]
    if {r.get("normalized_record_id") for r in records if isinstance(r, dict)} != split_record_ids:
        problems.append("RECORD_SET_MISMATCH")
    labels = _label_ids()
    for record in records:
        rid = record.get("normalized_record_id") if isinstance(record, dict) else None
        if (
            rid not in surface_sha256_by_id
            or record.get("surface_sha256") != surface_sha256_by_id[rid]
        ):
            problems.append(f"SURFACE_DIGEST_MISMATCH {rid}")
            continue
        cells = record.get("labels")
        if not isinstance(cells, dict) or set(cells) != labels:
            problems.append(f"LABEL_SET_MISMATCH {rid}")
            continue
        for label_id, cell in cells.items():
            if not isinstance(cell, dict) or cell.get("state") not in ANNOTATION_STATES:
                problems.append(f"CELL_NOT_LABELLED {rid}/{label_id}")
            elif "quote" in cell or "note" in cell:
                problems.append(f"TEXT_COMMITTED {rid}/{label_id}")
    return problems


@dataclass(frozen=True)
class ReferenceAssessment:
    strength: ReferenceStrength
    human_files: tuple[str, ...]
    refused_files: tuple[tuple[str, tuple[str, ...]], ...]
    adjudication_present: bool
    pilot_gate: bool
    multi_human_gate: bool

    @property
    def result_scope(self) -> str | None:
        if self.strength is ReferenceStrength.SINGLE_HUMAN_REFERENCE:
            return RESULT_SCOPE_DEVELOPMENT_PILOT
        if self.strength is ReferenceStrength.MULTI_HUMAN_REFERENCE:
            return "DEVELOPMENT_MULTI_HUMAN_REFERENCE"
        return None

    @property
    def result_label(self) -> str | None:
        if self.strength is ReferenceStrength.SINGLE_HUMAN_REFERENCE:
            return PILOT_NOT_CERTIFICATION
        return None

    @property
    def inter_annotator_agreement(self) -> dict[str, str] | str:
        if self.strength is ReferenceStrength.SINGLE_HUMAN_REFERENCE:
            return single_annotator_agreement()
        if self.strength is ReferenceStrength.MULTI_HUMAN_REFERENCE:
            return "COMPUTED_IN_THE_COMPOSITION_REPORT"
        return "NO_HUMAN_REFERENCE"


def assess_reference(
    files: Iterable[tuple[str, Any]],
    *,
    split_record_ids: set[str],
    surface_sha256_by_id: dict[str, str],
    adjudication_present: bool,
) -> ReferenceAssessment:
    """Which human-reference gate, if any, the committed DEVELOPMENT annotation files satisfy.

    - the pilot gate: exactly one valid human file and no refused file;
    - the multi-human gate: two or more valid human files from distinct annotators, adjudication
      present, and no refused file (the Mission 1.85.4 rule, unchanged).

    A refused file blocks both gates: a reference set with an invalid member is not trimmed to its valid
    part. An AI_ASSISTED_PROVISIONAL file is always refused here, so it can satisfy neither gate.
    """
    valid: list[tuple[str, dict[str, Any]]] = []
    refused: list[tuple[str, tuple[str, ...]]] = []
    for name, committed in files:
        problems = human_reference_file_problems(
            committed, split_record_ids=split_record_ids, surface_sha256_by_id=surface_sha256_by_id
        )
        if problems:
            refused.append((name, tuple(problems)))
        else:
            valid.append((name, committed))
    annotators = [c["annotator_id"] for _, c in valid]
    distinct = len(set(annotators)) == len(annotators)
    pilot = not refused and len(valid) == 1
    multi = not refused and len(valid) >= 2 and distinct and adjudication_present
    if pilot:
        strength = ReferenceStrength.SINGLE_HUMAN_REFERENCE
    elif multi:
        strength = ReferenceStrength.MULTI_HUMAN_REFERENCE
    else:
        strength = ReferenceStrength.NO_HUMAN_REFERENCE
    return ReferenceAssessment(
        strength=strength,
        human_files=tuple(name for name, _ in valid),
        refused_files=tuple(refused),
        adjudication_present=adjudication_present,
        pilot_gate=pilot,
        multi_human_gate=multi,
    )


def holdout_reference_permitted(strength: ReferenceStrength) -> bool:
    """HOLDOUT_REQUIRES_MULTI_HUMAN_OR_NEW_OPERATOR_DECISION.

    No parameter can widen this. A single-human holdout needs a recorded operator decision AND a change to
    this function in the same reviewed diff.
    """
    return strength is ReferenceStrength.MULTI_HUMAN_REFERENCE
