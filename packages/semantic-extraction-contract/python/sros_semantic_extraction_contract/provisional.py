"""AI_ASSISTED_PROVISIONAL annotations: a separate, diagnostic-only path (Mission 1.85.5).

Nothing in this mission produces one. This module only defines where one would live and what it may be
used for, so that if a model annotation is ever made it cannot be mistaken for, merged with or counted as
a human reference:

- it lives under its own file name, which the human glob never matches, and the human importer refuses
  its origin;
- it carries no attestation (a model cannot attest to not having used a model);
- its only use is `diagnostic_disagreements`: the records where it and the single human differ, to find
  ambiguous label definitions. That comparison is explicitly NOT human agreement, carries no kappa, and
  never changes a human label.
"""

from __future__ import annotations

import fnmatch
from typing import Any

from .annotation import ANNOTATION_STATES, AnnotationOrigin
from .labels import LABELS, LabelStatus
from .reference import (
    AI_ASSISTED_PROVISIONAL,
    NOT_APPLICABLE_SINGLE_ANNOTATOR,
    ReferenceStrength,
    single_annotator_agreement,
)

__all__ = [
    "HUMAN_ANNOTATION_GLOB",
    "PROVISIONAL_ANNOTATION_GLOB",
    "PROVISIONAL_USE",
    "diagnostic_disagreements",
    "provisional_annotation_problems",
]

HUMAN_ANNOTATION_GLOB = "stack-overflow-semantic-annotations-development-*-v1.json"
PROVISIONAL_ANNOTATION_GLOB = (
    "stack-overflow-semantic-provisional-ai-annotations-development-*-v1.json"
)
PROVISIONAL_USE = "DIAGNOSTIC_ONLY"


def provisional_annotation_problems(
    doc: Any, *, file_name: str, split_record_ids: set[str]
) -> list[str]:
    if not isinstance(doc, dict):
        return ["NOT_AN_OBJECT"]
    problems = []
    if fnmatch.fnmatch(file_name, HUMAN_ANNOTATION_GLOB) or not fnmatch.fnmatch(
        file_name, PROVISIONAL_ANNOTATION_GLOB
    ):
        problems.append("NOT_STORED_SEPARATELY_FROM_HUMAN_REFERENCE")
    if doc.get("reference_origin") != AI_ASSISTED_PROVISIONAL:
        problems.append("ORIGIN_IS_NOT_AI_ASSISTED_PROVISIONAL")
    if doc.get("reference_origin") in {o.value for o in AnnotationOrigin}:
        problems.append("AI_ANNOTATION_CLAIMS_A_HUMAN_ORIGIN")
    if doc.get("reference_strength") != ReferenceStrength.AI_ASSISTED_PROVISIONAL.value:
        problems.append("REFERENCE_STRENGTH_NOT_AI_ASSISTED_PROVISIONAL")
    if doc.get("use") != PROVISIONAL_USE:
        problems.append("USE_NOT_DIAGNOSTIC_ONLY")
    if doc.get("split") != "DEVELOPMENT":
        problems.append("NOT_DEVELOPMENT")
    if "attestation" in doc:
        problems.append("A_MODEL_CANNOT_ATTEST")
    records = doc.get("records")
    if not isinstance(records, list):
        return [*problems, "RECORDS_MISSING"]
    if (
        not {r.get("normalized_record_id") for r in records if isinstance(r, dict)}
        <= split_record_ids
    ):
        problems.append("RECORD_OUTSIDE_DEVELOPMENT")
    for record in records:
        for label_id, cell in (record.get("labels") or {}).items():
            if not isinstance(cell, dict) or cell.get("state") not in ANNOTATION_STATES:
                problems.append(f"UNKNOWN_STATE {record.get('normalized_record_id')}/{label_id}")
    return problems


def diagnostic_disagreements(
    human: dict[str, Any], provisional: dict[str, Any], *, provisional_file_name: str
) -> dict[str, Any]:
    """Cells where the single human and the AI provisional annotation differ. Read-only on both."""
    if human.get("reference_origin") not in {o.value for o in AnnotationOrigin}:
        raise ValueError("the reference side must be a human annotation")
    human_ids = {r["normalized_record_id"] for r in human["records"]}
    problems = provisional_annotation_problems(
        provisional, file_name=provisional_file_name, split_record_ids=human_ids
    )
    if problems:
        raise ValueError(f"PROVISIONAL_ANNOTATION_REFUSED: {problems}")
    ai = {r["normalized_record_id"]: r["labels"] for r in provisional["records"]}
    rows = []
    for record in sorted(human["records"], key=lambda r: r["normalized_record_id"]):
        rid = record["normalized_record_id"]
        for label in LABELS:
            if label.status is LabelStatus.NOT_SAFE or rid not in ai:
                continue
            human_state = record["labels"][label.label_id]["state"]
            ai_state = (ai[rid].get(label.label_id) or {}).get("state")
            if ai_state is not None and ai_state != human_state:
                rows.append(
                    {
                        "normalized_record_id": rid,
                        "label_id": label.label_id,
                        "human_state": human_state,
                        "ai_provisional_state": ai_state,
                    }
                )
    return {
        "comparison": "AI_ASSISTED_PROVISIONAL_VS_HUMAN_DIAGNOSTIC",
        "is_human_agreement": False,
        "use": PROVISIONAL_USE,
        "human_labels_changed": 0,
        "inter_annotator_agreement": single_annotator_agreement(),
        "note": f"an AI annotation is not an annotator: human agreement stays {NOT_APPLICABLE_SINGLE_ANNOTATOR}",
        "disagreements": rows,
    }
