"""Mission 1.85.15 (N08-B-PILOT). A reference adjudicated by the only human available, and labelled as such.

There is no second annotator. The operator has seen their own blind labels, the model's outputs and two
post-model reviews, so no reading they make can be a blind second reference, and none is called one. What
this module supports instead is a written protocol whose every step says what it is:

    1. REREAD           the operator labels the two extractable labels again on all 46 EGRESS_APPROVED records,
                        in a fresh order, with their earlier labels hidden. Blind to their earlier labels at the
                        time of reading; NOT blind to model output, which they declare. All 46, so the reread does
                        not reveal which records were contested. Protocol 1.0.0 also required a 24-hour delay after
                        the last post-model decision; protocol 1.1.0 (Mission 1.85.16, an operator decision)
                        removes it. The delay was a memory-decay safeguard only, and removing it claims no
                        stronger blindness.
    2. ADJUDICATION     only where the readings of a cell disagree or one is UNCERTAIN: the original blind
                        label, the reread, and the post-model judgement where one exists. The operator sees every
                        reading and decides a final state with a reason.
    3. REFERENCE        a new SINGLE_HUMAN_ADJUDICATED_REFERENCE file. It never overwrites the original blind
                        annotation, is never called consensus or inter-human, and certifies nothing.

The reread against the original is INTRA-RATER agreement: one person's consistency, never inter-human
reliability.

Pure functions: no file, database, network or model access.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

from .agreement import cohen_kappa, krippendorff_alpha_nominal
from .finding import MAX_QUOTE, MIN_QUOTE, locate_quote
from .labels import LABELS
from .surface import marker_regions

__all__ = [
    "ADJUDICATED",
    "CONSISTENT",
    "FINAL_STATES",
    "MINIMUM_DELAY_POLICY",
    "MIN_DELAY",
    "PROTOCOLS",
    "PROTOCOL_DECISION",
    "PROTOCOL_ID",
    "PROTOCOL_ID_V1_0",
    "REFERENCE_STRENGTH",
    "REREAD_ATTESTATION",
    "REREAD_LABELS",
    "AdjudicationRefusedError",
    "build_reference",
    "cells_to_adjudicate",
    "earliest_reread",
    "implied_state",
    "intra_rater_agreement",
    "make_adjudication",
    "validate_reread_pack",
]

PROTOCOL_ID_V1_0 = (
    "single-operator-adjudication-protocol@1.0.0"  # historical: mandatory 24-hour delay
)
PROTOCOL_ID = "single-operator-adjudication-protocol@1.1.0"
PROTOCOLS = (PROTOCOL_ID_V1_0, PROTOCOL_ID)
REFERENCE_STRENGTH = "SINGLE_HUMAN_ADJUDICATED_REFERENCE"
READING = "SAME_OPERATOR_DELAYED_REREAD"
REREAD_LABELS = ("REPORTED_FAILED_ATTEMPT", "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION")
STATES = ("PRESENT", "ABSENT", "UNCERTAIN")
FINAL_STATES = STATES
MIN_DELAY = timedelta(hours=24)  # protocol 1.0.0 only, kept so its rule stays reproducible
MINIMUM_DELAY_POLICY = {
    PROTOCOL_ID_V1_0: "MANDATORY_24_HOURS_AFTER_LAST_POST_MODEL_DECISION",
    PROTOCOL_ID: "NO_MANDATORY_DELAY",
}
# Why 1.1.0 exists. Recorded in the committed reread so the change is attributed, never silent.
PROTOCOL_DECISION = {
    "protocol": PROTOCOL_ID,
    "supersedes": PROTOCOL_ID_V1_0,
    "change": "the mandatory 24-hour delay before the reread is removed; mandatory_delay_seconds = 0",
    "decided_by": "operator-a",
    "decided_in": "Mission 1.85.16",
    "reason": "the delay is only a memory-decay safeguard and does not affect model behaviour; for this DEVELOPMENT workflow the operator judges the cost of waiting larger than the methodological benefit",
    "claims_stronger_blindness": False,
    "unchanged": "records, labels, order rule, hidden material, attestation including the prior model exposure disclosure, annotation and adjudication rules, reference labelling",
}
CONSISTENT = "CONSISTENT_ORIGINAL_REREAD_AND_REVIEW"
ADJUDICATED = "ADJUDICATED_BY_THE_SINGLE_OPERATOR"
MAX_NOTE = 600
# The reread's own attestation. The last flag is a DISCLOSURE, and it must be true: the operator has seen model
# output on some of these records, and the reread says so rather than claiming a blindness it cannot have.
REREAD_ATTESTATION = {
    "previous_labels_not_consulted": "Pendant cette relecture, je n'ai consulté ni mes labels précédents ni les revues.",
    "no_model_assistance_used": "Je n'ai utilisé aucune assistance d'IA pour décider ou rédiger mes réponses.",
    "labelled_from_rendered_surface_only": "J'ai répondu uniquement à partir du texte affiché.",
    "prior_model_exposure_acknowledged": "Je reconnais avoir déjà vu, lors des revues, des sorties du modèle sur certaines de ces questions.",
}
# What a post-model decision says about the state of the label on that record.
IMPLIED_STATE = {
    "HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD": "ABSENT",
    "POST_MODEL_HUMAN_REVISION": "PRESENT",
    "POST_MODEL_HUMAN_REVISION_TO_PRESENT": "PRESENT",
    "HUMAN_REFERENCE_CONFIRMED_MODEL_UNDERREAD": "PRESENT",
    "POST_MODEL_HUMAN_REVISION_TO_ABSENT": "ABSENT",
    "LABEL_DEFINITION_AMBIGUOUS": "UNCERTAIN",
}


class AdjudicationRefusedError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}{': ' + detail if detail else ''}")
        self.code = code


def _labels() -> dict[str, Any]:
    return {label.label_id: label for label in LABELS if label.label_id in REREAD_LABELS}


def _aware(value: Any) -> datetime | None:
    try:
        moment = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return moment if moment.utcoffset() is not None else None


def earliest_reread(last_exposure: str) -> str:
    """Protocol 1.0.0's earliest reread start. Historical: protocol 1.1.0 has no mandatory delay."""
    moment = _aware(last_exposure)
    if moment is None:
        raise AdjudicationRefusedError("LAST_EXPOSURE_NOT_TIMEZONE_AWARE", str(last_exposure))
    return (moment + MIN_DELAY).isoformat(timespec="seconds")


def implied_state(decision: str) -> str:
    if decision not in IMPLIED_STATE:
        raise AdjudicationRefusedError("UNKNOWN_POST_MODEL_DECISION", decision)
    return IMPLIED_STATE[decision]


def _span(surface: str, start: int, end: int) -> dict[str, Any]:
    return {
        "start": start,
        "end": end,
        "quote_sha256": hashlib.sha256(surface[start:end].encode("utf-8")).hexdigest(),
        "quote_length": end - start,
    }


def _check_cell(
    label: Any, cell: Any, surface: str, where: str, refuse: Any
) -> dict[str, Any] | None:
    """The original annotation rules for one extractable cell, as the blind importer applies them."""
    state = cell.get("state") if isinstance(cell, dict) else None
    if state == "UNLABELLED":
        refuse("UNLABELLED_CELL", where)
        return None
    if state not in STATES:
        refuse("UNKNOWN_STATE", where)
        return None
    note = cell.get("note")
    if state == "UNCERTAIN" and not (isinstance(note, str) and note.strip()):
        refuse("UNCERTAIN_WITHOUT_NOTE", where)
    evidence, subject = cell.get("evidence", []), cell.get("subject")
    if state != "PRESENT" and (evidence or subject is not None):
        refuse("SPAN_WITH_NON_PRESENT_STATE", where)
    regions = marker_regions(surface)
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
            refuse("SPAN_IN_QUOTED_MATERIAL", where)
        if not label.evidence_may_be_in_code and any(
            k == "CODE" and start < b and a < end for k, a, b in regions
        ):
            refuse("SPAN_IN_CODE_NOT_PERMITTED", where)
        spans.append(_span(surface, start, end))
    if state == "PRESENT" and not spans:
        refuse("PRESENT_WITHOUT_SPAN", where)
    committed_subject = None
    if state == "PRESENT" and label.requires_subject:
        if not isinstance(subject, dict):
            refuse("SUBJECT_REQUIRED", where)
        else:
            located = locate_quote(
                surface, subject.get("quote"), subject.get("occurrence"), min_len=2, max_len=120
            )
            if not isinstance(located, tuple):
                refuse(str(located), f"{where}.subject")
            else:
                committed_subject = _span(surface, *located)
    elif subject is not None:
        refuse("SUBJECT_NOT_PERMITTED", where)
    return {
        "state": state,
        "spans": sorted(spans, key=lambda s: (s["start"], s["end"])),
        "subject": committed_subject,
        "note_present": bool(note),
    }


def validate_reread_pack(
    pack: Any,
    *,
    scope_record_ids: set[str],
    surfaces: dict[str, str],
    earliest: str | None = None,
) -> tuple[list[tuple[str, str]], dict[str, Any] | None]:
    """Every problem with a reread pack, and its committed form when there is none. Refuses, never repairs.

    Each protocol is validated by its own rule: a 1.0.0 pack still needs `earliest` and the 24-hour delay (its
    historical rule, unchanged); a 1.1.0 pack has no time gate, and its actual start time is still required."""
    refusals: list[tuple[str, str]] = []

    def refuse(code: str, detail: str) -> None:
        refusals.append((code, detail))

    if not isinstance(pack, dict) or pack.get("protocol") not in PROTOCOLS:
        return [("NOT_A_REREAD_PACK", "")], None
    protocol = pack["protocol"]
    if pack.get("reading") != READING or pack.get("split") != "DEVELOPMENT":
        refuse("READING_OR_SPLIT_INVALID", str(pack.get("reading")))
    ids = [r.get("normalized_record_id") for r in pack.get("records", []) if isinstance(r, dict)]
    if set(ids) != scope_record_ids or len(ids) != len(scope_record_ids):
        refuse("RECORD_SET_MISMATCH", f"{len(ids)} records, {len(scope_record_ids)} in scope")
    started, completed = (
        _aware(pack.get("annotation_started_at")),
        _aware(pack.get("annotation_completed_at")),
    )
    floor = _aware(earliest)
    if started is None or completed is None or started > completed:
        refuse(
            "TIMESTAMPS_INVALID",
            "annotation_started_at and annotation_completed_at are required and ordered",
        )
    elif protocol == PROTOCOL_ID_V1_0 and (floor is None or started < floor):
        refuse(
            "REREAD_STARTED_BEFORE_THE_MINIMUM_DELAY",
            f"started {pack.get('annotation_started_at')}, earliest {earliest}",
        )
    attestation = pack.get("attestation") or {}
    if any(attestation.get(flag) is not True for flag in REREAD_ATTESTATION) or not _aware(
        attestation.get("attested_at")
    ):
        refuse(
            "ATTESTATION_INCOMPLETE",
            "every reread attestation flag, the disclosure included, must be true",
        )
    for key in ("no_model_output_seen", "did_not_see_other_annotators_labels"):
        if key in attestation:
            refuse("BLIND_ATTESTATION_NOT_PERMITTED", key)
    labels = _labels()
    records = []
    for record in pack.get("records", []):
        rid = str(record.get("normalized_record_id"))
        surface = surfaces.get(rid)
        if surface is None or hashlib.sha256(surface.encode("utf-8")).hexdigest() != record.get(
            "surface_sha256"
        ):
            refuse("SURFACE_DIGEST_MISMATCH", rid)
            continue
        cells = record.get("labels", {})
        if set(cells) != set(labels):
            refuse("LABEL_SET_MISMATCH", rid)
            continue
        committed = {}
        for label_id, label in labels.items():
            cell = _check_cell(label, cells[label_id], surface, f"{rid}/{label_id}", refuse)
            if cell is not None:
                committed[label_id] = cell
        records.append(
            {
                "normalized_record_id": rid,
                "surface_sha256": record["surface_sha256"],
                "labels": committed,
            }
        )
    if refusals:
        return refusals, None
    return [], {
        "$comment": "SAME-OPERATOR DELAYED REREAD (Mission 1.85.15). The operator labelled the two extractable labels again with their earlier labels hidden. It is NOT a second annotator and NOT blind to model output, which the attestation discloses. States, offsets and digests only.",
        "protocol": protocol,
        "reading": READING,
        "split": "DEVELOPMENT",
        "operator_id": pack["operator_id"],
        "record_scope": pack["record_scope"],
        "blind_to_previous_labels_at_reading": True,
        "blind_to_model_outputs": False,
        "is_a_second_annotator": False,
        "minimum_delay_policy": MINIMUM_DELAY_POLICY[protocol],
        **(
            {"earliest_permitted_start": earliest}
            if protocol == PROTOCOL_ID_V1_0
            else {"protocol_decision": PROTOCOL_DECISION}
        ),
        "annotation_started_at": pack["annotation_started_at"],
        "annotation_completed_at": pack["annotation_completed_at"],
        "attestation": attestation,
        "records": sorted(records, key=lambda r: r["normalized_record_id"]),
    }


def cells_to_adjudicate(
    original: dict[str, Any], reread: dict[str, Any], post_model: dict[str, str]
) -> list[dict[str, Any]]:
    """Cells whose readings disagree, or where any reading is UNCERTAIN. `post_model` maps a record id to the
    state implied by its latest post-model decision (REPORTED_FAILED_ATTEMPT only)."""
    by_original = {r["normalized_record_id"]: r["labels"] for r in original["records"]}
    queue = []
    for record in reread["records"]:
        rid = record["normalized_record_id"]
        for label_id in REREAD_LABELS:
            readings = {
                "ORIGINAL_BLIND": by_original[rid][label_id]["state"],
                "DELAYED_REREAD": record["labels"][label_id]["state"],
            }
            if label_id == "REPORTED_FAILED_ATTEMPT" and rid in post_model:
                readings["POST_MODEL_REVIEW"] = post_model[rid]
            states = set(readings.values())
            if len(states) > 1 or "UNCERTAIN" in states:
                queue.append(
                    {
                        "normalized_record_id": rid,
                        "label_id": label_id,
                        "readings": readings,
                        "reasons": (["READINGS_DIFFER"] if len(states) > 1 else [])
                        + (["UNCERTAIN_GIVEN"] if "UNCERTAIN" in states else []),
                    }
                )
    return sorted(queue, key=lambda q: (q["label_id"], q["normalized_record_id"]))


def make_adjudication(
    item: dict[str, Any],
    *,
    final_state: str,
    note: str,
    spans: list[dict[str, Any]],
    subject: dict[str, Any] | None,
    decided_at: str,
    operator_id: str,
) -> dict[str, Any]:
    """One adjudication, bound to the readings it was made on. Refuses rather than repairs."""
    if final_state not in FINAL_STATES:
        raise AdjudicationRefusedError("UNKNOWN_FINAL_STATE", final_state)
    note = note.strip()
    if not note:
        raise AdjudicationRefusedError("NOTE_REQUIRED", "every adjudication states its reason")
    if len(note) > MAX_NOTE:
        raise AdjudicationRefusedError("NOTE_TOO_LONG", str(len(note)))
    if final_state == "PRESENT" and not spans:
        raise AdjudicationRefusedError("PRESENT_WITHOUT_SPAN", item["normalized_record_id"])
    if final_state != "PRESENT" and (spans or subject):
        raise AdjudicationRefusedError("SPAN_WITH_NON_PRESENT_STATE", item["normalized_record_id"])
    label = _labels()[item["label_id"]]
    if final_state == "PRESENT" and label.requires_subject and not subject:
        raise AdjudicationRefusedError("SUBJECT_REQUIRED", item["normalized_record_id"])
    if _aware(decided_at) is None:
        raise AdjudicationRefusedError("DECIDED_AT_NOT_TIMEZONE_AWARE", decided_at)
    return {
        "normalized_record_id": item["normalized_record_id"],
        "label_id": item["label_id"],
        "readings": item["readings"],
        "final_state": final_state,
        "spans": spans,
        "subject": subject,
        "operator_note": note,
        "decided_by": operator_id,
        "decided_at": decided_at,
        "blind": False,
    }


def intra_rater_agreement(original: dict[str, Any], reread: dict[str, Any]) -> dict[str, Any]:
    """One person's consistency between two readings. Never inter-human reliability."""
    by_original = {r["normalized_record_id"]: r["labels"] for r in original["records"]}
    records = [r["normalized_record_id"] for r in reread["records"]]
    by_reread = {r["normalized_record_id"]: r["labels"] for r in reread["records"]}
    result: dict[str, Any] = {}
    for label_id in REREAD_LABELS:
        first = [by_original[r][label_id]["state"] for r in records]
        second = [by_reread[r][label_id]["state"] for r in records]
        both = [(p, q) for p, q in zip(first, second, strict=True) if "UNCERTAIN" not in (p, q)]
        result[label_id] = {
            "records": len(records),
            "confusion": {
                f"ORIGINAL_{x}__REREAD_{y}": sum(
                    p == x and q == y for p, q in zip(first, second, strict=True)
                )
                for x in STATES
                for y in STATES
            },
            "raw_agreement_three_state": round(
                sum(p == q for p, q in zip(first, second, strict=True)) / len(records), 6
            )
            if records
            else "UNDEFINED",
            "cohen_kappa_three_state": cohen_kappa(first, second, STATES),
            "cohen_kappa_present_absent": cohen_kappa(
                [p for p, _ in both], [q for _, q in both], ("PRESENT", "ABSENT")
            ),
            "krippendorff_alpha_three_state": krippendorff_alpha_nominal(
                [[p, q] for p, q in zip(first, second, strict=True)]
            ),
        }
    return {
        "kind": "INTRA_RATER_DELAYED_REREAD",
        "is_inter_human_reliability": False,
        "caveat": "one person read twice; the second reading was blind to the first labels but not to model output seen in the reviews",
        "labels": result,
    }


def build_reference(
    original: dict[str, Any],
    reread: dict[str, Any],
    post_model: dict[str, str],
    adjudications: list[dict[str, Any]],
) -> dict[str, Any]:
    """The adjudicated reference for the two extractable labels. Every cell says where its state came from."""
    queue = {
        (q["normalized_record_id"], q["label_id"]): q
        for q in cells_to_adjudicate(original, reread, post_model)
    }
    decided = {(a["normalized_record_id"], a["label_id"]): a for a in adjudications}
    if set(decided) != set(queue):
        raise AdjudicationRefusedError(
            "ADJUDICATION_SET_MISMATCH", f"{len(decided)} decided, {len(queue)} to adjudicate"
        )
    for key, decision in decided.items():
        if decision["readings"] != queue[key]["readings"]:
            raise AdjudicationRefusedError("STALE_ADJUDICATION", f"{key[0]}/{key[1]}")
    by_original = {r["normalized_record_id"]: r["labels"] for r in original["records"]}
    records = []
    for record in reread["records"]:
        rid = record["normalized_record_id"]
        cells = {}
        for label_id in REREAD_LABELS:
            key = (rid, label_id)
            if key in decided:
                d = decided[key]
                cells[label_id] = {
                    "state": d["final_state"],
                    "basis": ADJUDICATED,
                    "spans": d["spans"],
                    "subject": d["subject"],
                }
                continue
            first = by_original[rid][label_id]
            cells[label_id] = {
                "state": first["state"],
                "basis": CONSISTENT,
                "spans": first.get("spans", []),
                "subject": first.get("subject"),
            }
        records.append(
            {
                "normalized_record_id": rid,
                "surface_sha256": record["surface_sha256"],
                "labels": cells,
            }
        )
    counts = {
        label_id: {s: sum(r["labels"][label_id]["state"] == s for r in records) for s in STATES}
        for label_id in REREAD_LABELS
    }
    return {
        "reference_strength": REFERENCE_STRENGTH,
        "protocol": PROTOCOL_ID,
        "is_consensus": False,
        "is_inter_human": False,
        "is_blind": False,
        "replaces_original_blind_annotation": False,
        "certification": False,
        "labels_covered": list(REREAD_LABELS),
        "state_counts": counts,
        "cells_adjudicated": len(decided),
        "cells_consistent": sum(len(REREAD_LABELS) for _ in records) - len(decided),
        "records": sorted(records, key=lambda r: r["normalized_record_id"]),
    }
