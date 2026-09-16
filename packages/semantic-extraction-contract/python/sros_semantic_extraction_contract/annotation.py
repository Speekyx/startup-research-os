"""Human reference annotation: working packs, import validation and the committed form (Mission 1.85.4).

A human annotator works OUTSIDE the repository on a copy of the blank development pack and reads the
surface rendered locally from the held record. Evidence is entered exactly as the model would enter it:
a verbatim quote and an occurrence index. The tool, not the person, computes offsets.

What this module can and cannot establish. It can refuse a pack that is incomplete, inconsistent,
inherits the wrong split, cites text that is not in the surface, or declares a non-human origin. It
cannot prove a human typed the labels. That rests on the attestation block and the operator's own
statement, and every document that reports these labels says so.

Nothing here writes a label state. The only producer of a state is a person editing their own working
file, and the only thing this module does with a state is check it and copy it into the committed form.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .finding import MAX_QUOTE, MIN_QUOTE, RefusalReason, locate_quote
from .labels import LABELS, LabelStatus
from .surface import marker_regions, surface_sha256

__all__ = [
    "ANNOTATION_STATES",
    "ATTESTATION_FLAGS",
    "ATTESTATION_ID",
    "AnnotationImportReport",
    "AnnotationOrigin",
    "HoldoutAccessError",
    "IMPORTER_VERSION",
    "annotator_record_order",
    "committed_form",
    "validate_annotation_pack",
]

IMPORTER_VERSION = "semantic-annotation-importer@1.0.0"
ATTESTATION_ID = "n08b-human-annotation-attestation@1"
ATTESTATION_FLAGS = (
    "no_model_output_seen",
    "no_model_assistance_used",
    "did_not_see_other_annotators_labels",
    "labelled_from_rendered_surface_only",
)
ANNOTATION_STATES = ("PRESENT", "ABSENT", "UNCERTAIN")
SHUFFLE_SEED = "n08b-annotator-shuffle-v1"
_MODEL_KEYS = {
    "prediction",
    "model_output",
    "model_label",
    "classifier",
    "confidence",
    "run_id",
    "provider",
    "model",
    "prompt",
}
_MODEL_LIKE_IDS = (
    "claude",
    "gpt",
    "gemini",
    "assistant",
    "model",
    "llm",
    "bot",
    "agent",
    "anthropic",
    "openai",
)


class AnnotationOrigin(StrEnum):
    """Mirrors the human members of the historical ReferenceOrigin. AI_ASSISTED_PROVISIONAL is absent."""

    HUMAN_OPERATOR = "HUMAN_OPERATOR"
    HUMAN_EXPERT = "HUMAN_EXPERT"
    HUMAN_NON_EXPERT = "HUMAN_NON_EXPERT"


class HoldoutAccessError(PermissionError):
    """A development path touched holdout material."""


@dataclass
class AnnotationImportReport:
    refusals: list[tuple[str, str]] = field(default_factory=list)
    committed: dict[str, Any] | None = None

    @property
    def accepted(self) -> bool:
        return not self.refusals and self.committed is not None


def annotator_record_order(split: str, annotator_id: str, record_ids: list[str]) -> list[str]:
    return sorted(
        record_ids,
        key=lambda rid: hashlib.sha256(
            f"{SHUFFLE_SEED}|{split}|{annotator_id}|{rid}".encode()
        ).hexdigest(),
    )


def _labels() -> dict[str, Any]:
    return {label.label_id: label for label in LABELS if label.status is not LabelStatus.NOT_SAFE}


def _walk_keys(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def validate_annotation_pack(
    pack: Any,
    *,
    split: str,
    split_record_ids: set[str],
    other_split_record_ids: set[str],
    surfaces: dict[str, str],
    blank_pack: dict[str, Any],
) -> AnnotationImportReport:
    """Every check runs; any refusal rejects the whole pack."""
    report = AnnotationImportReport()

    def refuse(code: str, detail: str) -> None:
        report.refusals.append((code, detail))

    if not isinstance(pack, dict):
        refuse("PACK_NOT_AN_OBJECT", type(pack).__name__)
        return report
    if split != "DEVELOPMENT":
        raise HoldoutAccessError("N08-B imports DEVELOPMENT annotations only; holdout is N08-C")
    if pack.get("split") != split:
        raise HoldoutAccessError(f"pack declares split {pack.get('split')!r}, opened as {split}")
    ids = {r.get("normalized_record_id") for r in pack.get("records", []) if isinstance(r, dict)}
    if ids & other_split_record_ids:
        raise HoldoutAccessError("the pack contains records of another split")

    for key in ("dataset_id", "dataset_version", "corpus", "label_set", "text_surface"):
        if pack.get(key) != blank_pack.get(key):
            refuse("DATASET_OR_LABEL_SET_MISMATCH", key)
    if pack.get("synthetic") is not False:
        refuse("SYNTHETIC_PACK", "a synthetic pack is never a reference")
    origin = pack.get("reference_origin")
    if origin is None:
        refuse("ORIGIN_MISSING", "reference_origin is required and has no default")
    elif origin not in {o.value for o in AnnotationOrigin}:
        refuse("ORIGIN_NOT_HUMAN", repr(origin))
    annotator = str(pack.get("annotator_id") or "").strip()
    if not annotator:
        refuse("ANNOTATOR_ID_MISSING", "")
    elif annotator.lower() in {"unknown", "none", "n/a", "tbd", "annotator"} or any(
        m in annotator.lower() for m in _MODEL_LIKE_IDS
    ):
        refuse(
            "ANNOTATOR_ID_NOT_ACCEPTED",
            "placeholder or model-like identifier (a weak check; attestation is the control)",
        )
    started, completed = pack.get("annotation_started_at"), pack.get("annotation_completed_at")
    if not started or not completed or str(started) > str(completed):
        refuse(
            "TIMESTAMPS_INVALID",
            "annotation_started_at and annotation_completed_at are required and ordered",
        )
    attestation = pack.get("attestation")
    if (
        not isinstance(attestation, dict)
        or attestation.get("attestation_id") != ATTESTATION_ID
        or attestation.get("annotator_id") != pack.get("annotator_id")
        or not attestation.get("attested_at")
        or any(attestation.get(flag) is not True for flag in ATTESTATION_FLAGS)
    ):
        refuse("ATTESTATION_INCOMPLETE", "every attestation flag must be literally true")
    if set(_walk_keys(pack)) & _MODEL_KEYS:
        refuse("MODEL_FIELD_PRESENT", ",".join(sorted(set(_walk_keys(pack)) & _MODEL_KEYS)))
    if ids != split_record_ids:
        refuse(
            "RECORD_SET_MISMATCH",
            f"{len(ids)} records against {len(split_record_ids)} in the split",
        )
    if annotator and pack.get("record_order") != annotator_record_order(
        split, annotator, sorted(split_record_ids)
    ):
        refuse(
            "SHUFFLE_ORDER_MISMATCH",
            "record_order is not the deterministic order for this annotator",
        )

    labels = _labels()
    committed_records = []
    for record in pack.get("records", []):
        if not isinstance(record, dict):
            refuse("UNKNOWN_OR_MISSING_KEY", "record")
            continue
        rid = str(record.get("normalized_record_id"))
        surface = surfaces.get(rid)
        if surface is None or surface_sha256(surface) != record.get("surface_sha256"):
            refuse("SURFACE_DIGEST_MISMATCH", rid)
            continue
        regions = marker_regions(surface)
        cells = record.get("labels", {})
        if set(cells) != set(labels):
            refuse("LABEL_SET_MISMATCH", rid)
            continue
        committed_cells: dict[str, Any] = {}
        for label_id, label in labels.items():
            cell = cells[label_id]
            where = f"{rid}/{label_id}"
            state = cell.get("state") if isinstance(cell, dict) else None
            if state == "UNLABELLED":
                refuse("UNLABELLED_CELL", where)
                continue
            if state not in ANNOTATION_STATES:
                refuse("UNKNOWN_STATE", where)
                continue
            note = cell.get("note")
            if state == "UNCERTAIN" and not (isinstance(note, str) and note.strip()):
                refuse("UNCERTAIN_WITHOUT_NOTE", where)
            if label.status is not LabelStatus.EXTRACTABLE:
                if "evidence" in cell or "subject" in cell:
                    refuse("INCIDENCE_LABEL_WITH_SPAN", where)
                committed_cells[label_id] = {"state": state, "note_present": bool(note)}
                continue
            evidence = cell.get("evidence", [])
            subject = cell.get("subject")
            if state != "PRESENT" and (evidence or subject is not None):
                refuse("SPAN_WITH_NON_PRESENT_STATE", where)
            spans = []
            for item in evidence if isinstance(evidence, list) else []:
                located = locate_quote(
                    surface,
                    item.get("quote") if isinstance(item, dict) else None,
                    item.get("occurrence") if isinstance(item, dict) else None,
                    min_len=MIN_QUOTE,
                    max_len=MAX_QUOTE,
                )
                if not isinstance(located, tuple):
                    refuse(str(located), where)
                    continue
                start, end = located
                if any(k == "QUOTE" and start < b and a < end for k, a, b in regions):
                    refuse(RefusalReason.SPAN_IN_QUOTED_MATERIAL.value, where)
                if not label.evidence_may_be_in_code and any(
                    k == "CODE" and start < b and a < end for k, a, b in regions
                ):
                    refuse(RefusalReason.SPAN_IN_CODE_NOT_PERMITTED.value, where)
                span = {
                    "start": start,
                    "end": end,
                    "occurrence": item["occurrence"],
                    "quote_sha256": hashlib.sha256(surface[start:end].encode("utf-8")).hexdigest(),
                    "quote_length": end - start,
                }
                if span in spans:
                    refuse("DUPLICATE_SPAN", where)
                spans.append(span)
            if state == "PRESENT" and not spans:
                refuse("PRESENT_WITHOUT_SPAN", where)
            committed_subject = None
            if state == "PRESENT" and label.requires_subject and subject is None:
                refuse(RefusalReason.SUBJECT_REQUIRED.value, where)
            if subject is not None and not label.requires_subject:
                refuse(RefusalReason.SUBJECT_NOT_PERMITTED.value, where)
            if subject is not None and label.requires_subject and state == "PRESENT":
                located = locate_quote(
                    surface,
                    subject.get("quote") if isinstance(subject, dict) else None,
                    subject.get("occurrence") if isinstance(subject, dict) else None,
                    min_len=2,
                    max_len=120,
                )
                if not isinstance(located, tuple):
                    refuse(str(located), f"{where}.subject")
                else:
                    start, end = located
                    if any(k in {"QUOTE", "CODE"} and start < b and a < end for k, a, b in regions):
                        refuse(
                            RefusalReason.SPAN_IN_QUOTED_MATERIAL.value,
                            f"{where}.subject outside prose",
                        )
                    committed_subject = {
                        "start": start,
                        "end": end,
                        "occurrence": subject["occurrence"],
                        "quote_sha256": hashlib.sha256(
                            surface[start:end].encode("utf-8")
                        ).hexdigest(),
                        "quote_length": end - start,
                    }
            committed_cells[label_id] = {
                "state": state,
                "spans": sorted(spans, key=lambda s: (s["start"], s["end"])),
                "subject": committed_subject,
                "note_present": bool(note),
            }
        committed_records.append(
            {
                "normalized_record_id": rid,
                "surface_sha256": record.get("surface_sha256"),
                "labels": committed_cells,
                "record_note_present": bool(record.get("record_note")),
            }
        )

    if not report.refusals:
        report.committed = committed_form(pack, committed_records)
    return report


def committed_form(pack: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """What may enter the repository: states, offsets and digests. Never a quote, never a note."""
    canonical = json.dumps(pack, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    counts: dict[str, dict[str, int]] = {}
    for record in records:
        for label_id, cell in record["labels"].items():
            counts.setdefault(label_id, {s: 0 for s in ANNOTATION_STATES})[cell["state"]] += 1
    return {
        "$comment": "Committed human annotation (N08-B). States, offsets and digests only: quotes and notes stay in the annotator's local working file. Origin and attestation are the annotator's own statements; this tool cannot prove a human typed the labels.",
        "importer": IMPORTER_VERSION,
        "dataset_id": pack["dataset_id"],
        "dataset_version": pack["dataset_version"],
        "split": pack["split"],
        "corpus": pack["corpus"],
        "label_set": pack["label_set"],
        "text_surface": pack["text_surface"],
        "annotator_id": pack["annotator_id"],
        "reference_origin": pack["reference_origin"],
        "annotation_started_at": pack["annotation_started_at"],
        "annotation_completed_at": pack["annotation_completed_at"],
        "attestation": pack["attestation"],
        "working_pack_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "state_counts": counts,
        "records": sorted(records, key=lambda r: r["normalized_record_id"]),
    }
