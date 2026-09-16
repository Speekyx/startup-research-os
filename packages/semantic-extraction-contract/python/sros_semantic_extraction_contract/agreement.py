"""Development-set composition, annotator agreement and adjudication (Mission 1.85.4).

Measurements for a later operator decision, never the decision. No threshold is a literal in this
module: the composition gate and the agreement floor are read from the contract JSON together with their
authorisation status, and while that status is PROPOSED_NOT_AUTHORISED every gate verdict is reported as
GATE_NOT_AUTHORISED rather than PASS or FAIL.

Agreement is reported several ways at once, because with an extreme prevalence a kappa can be low while
the annotators almost always agree (the kappa paradox). No single number decides anything.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from typing import Any

from .labels import LABELS, LabelStatus

__all__ = [
    "ADJUDICATION_RESOLUTIONS",
    "analyse_composition",
    "analyse_single_human_reference",
    "build_adjudication_queue",
    "cohen_kappa",
    "krippendorff_alpha_nominal",
    "reference_labels",
    "validate_adjudication",
]

STATES = ("PRESENT", "ABSENT", "UNCERTAIN")
ADJUDICATION_RESOLUTIONS = (
    "RESOLVED_TO_EXISTING_STATE",
    "RESOLVED_AFTER_REREAD",
    "UNRESOLVED_KEPT_UNCERTAIN",
)


def cohen_kappa(a: list[str], b: list[str], categories: tuple[str, ...]) -> float | str:
    n = len(a)
    if n == 0 or n != len(b):
        return "UNDEFINED"
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in categories)
    if pe == 1:
        return "UNDEFINED"
    return round((po - pe) / (1 - pe), 6)


def krippendorff_alpha_nominal(units: list[list[str]]) -> float | str:
    """units: the values given to each unit by the annotators who coded it (missing values omitted)."""
    coincidence: dict[tuple[str, str], float] = {}
    for values in units:
        m = len(values)
        if m < 2:
            continue
        for i, j in itertools.permutations(range(m), 2):
            key = (values[i], values[j])
            coincidence[key] = coincidence.get(key, 0.0) + 1 / (m - 1)
    n = sum(coincidence.values())
    if n == 0:
        return "UNDEFINED"
    marginals: dict[str, float] = {}
    for (c, _), count in coincidence.items():
        marginals[c] = marginals.get(c, 0.0) + count
    do = sum(v for (c, k), v in coincidence.items() if c != k)
    de = sum(marginals[c] * marginals[k] for c in marginals for k in marginals if c != k) / (n - 1)
    if de == 0:
        return "UNDEFINED"
    return round(1 - do / de, 6)


def _spans(cell: dict[str, Any]) -> list[tuple[int, int]]:
    return [(s["start"], s["end"]) for s in cell.get("spans", [])]


def _overlap(x: list[tuple[int, int]], y: list[tuple[int, int]]) -> bool:
    return any(a < d and c < b for a, b in x for c, d in y)


def _chars(spans: list[tuple[int, int]]) -> set[int]:
    return {i for a, b in spans for i in range(a, b)}


def _index(
    files: list[dict[str, Any]],
) -> tuple[list[str], list[str], dict[str, dict[str, dict[str, Any]]]]:
    annotators = [f["annotator_id"] for f in files]
    if len(set(annotators)) != len(annotators):
        raise ValueError("DUPLICATE_ANNOTATOR_ID")
    if len({f["split"] for f in files}) != 1 or files[0]["split"] != "DEVELOPMENT":
        raise ValueError("composition analysis in N08-B covers DEVELOPMENT only")
    record_ids = sorted({r["normalized_record_id"] for f in files for r in f["records"]})
    by_annotator = {
        f["annotator_id"]: {r["normalized_record_id"]: r["labels"] for r in f["records"]}
        for f in files
    }
    return annotators, record_ids, by_annotator


def build_adjudication_queue(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotators, record_ids, cells = _index(files)
    queue = []
    for label in LABELS:
        if label.status is LabelStatus.NOT_SAFE:
            continue
        for rid in record_ids:
            given = {a: cells[a][rid][label.label_id] for a in annotators}
            states = {c["state"] for c in given.values()}
            reasons = []
            if len(states) > 1:
                reasons.append("STATES_DIFFER")
            if "UNCERTAIN" in states:
                reasons.append("UNCERTAIN_GIVEN")
            if label.status is LabelStatus.EXTRACTABLE and states == {"PRESENT"}:
                pairs = list(itertools.combinations(given.values(), 2))
                if any(not _overlap(_spans(x), _spans(y)) for x, y in pairs):
                    reasons.append("EVIDENCE_SPANS_DO_NOT_OVERLAP")
                if label.requires_subject and any(
                    not (
                        x.get("subject")
                        and y.get("subject")
                        and _overlap(
                            [(x["subject"]["start"], x["subject"]["end"])],
                            [(y["subject"]["start"], y["subject"]["end"])],
                        )
                    )
                    for x, y in pairs
                ):
                    reasons.append("SUBJECTS_DO_NOT_OVERLAP")
            if label.status is not LabelStatus.EXTRACTABLE:
                reasons = [r for r in reasons if r == "STATES_DIFFER"]
            if reasons:
                queue.append(
                    {
                        "label_id": label.label_id,
                        "normalized_record_id": rid,
                        "reasons": reasons,
                        "incidence_only": label.status is not LabelStatus.EXTRACTABLE,
                    }
                )
    return sorted(queue, key=lambda q: (q["label_id"], q["normalized_record_id"]))


def analyse_composition(files: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    if len(files) < 2:
        raise ValueError(
            "FEWER_THAN_TWO_ANNOTATORS: agreement needs at least two independent human files"
        )
    annotators, record_ids, cells = _index(files)
    content = [json.dumps([r["labels"] for r in f["records"]], sort_keys=True) for f in files]
    gate = contract["evaluation_protocol"]["composition_gate"]
    kappa_item = next(
        i
        for i in contract["proposed_thresholds"]["items"]
        if i["metric"] == "inter_annotator_kappa_per_extractable_label"
    )
    per_label = {}
    for label in LABELS:
        if label.status is LabelStatus.NOT_SAFE:
            continue
        lid = label.label_id
        counts = {
            a: {s: sum(cells[a][r][lid]["state"] == s for r in record_ids) for s in STATES}
            for a in annotators
        }
        entry: dict[str, Any] = {"status": label.status.value, "state_counts": counts}
        entry["prevalence_present_among_decided"] = {
            a: (
                round(c["PRESENT"] / (c["PRESENT"] + c["ABSENT"]), 6)
                if c["PRESENT"] + c["ABSENT"]
                else "UNDEFINED"
            )
            for a, c in counts.items()
        }
        entry["krippendorff_alpha_three_state"] = krippendorff_alpha_nominal(
            [[cells[a][r][lid]["state"] for a in annotators] for r in record_ids]
        )
        decided = [
            [
                cells[a][r][lid]["state"]
                for a in annotators
                if cells[a][r][lid]["state"] != "UNCERTAIN"
            ]
            for r in record_ids
        ]
        entry["krippendorff_alpha_present_absent"] = krippendorff_alpha_nominal(decided)
        if len(annotators) == 2:
            x, y = annotators
            sx = [cells[x][r][lid]["state"] for r in record_ids]
            sy = [cells[y][r][lid]["state"] for r in record_ids]
            both = [(p, q) for p, q in zip(sx, sy, strict=True) if "UNCERTAIN" not in (p, q)]
            a_ = sum(p == q == "PRESENT" for p, q in both)
            d_ = sum(p == q == "ABSENT" for p, q in both)
            b_ = sum(p == "PRESENT" and q == "ABSENT" for p, q in both)
            c_ = sum(p == "ABSENT" and q == "PRESENT" for p, q in both)
            n = len(both)
            po = (a_ + d_) / n if n else None
            entry["pairwise"] = {
                "cohen_kappa_three_state": cohen_kappa(sx, sy, STATES),
                "cohen_kappa_present_absent": cohen_kappa(
                    [p for p, _ in both], [q for _, q in both], ("PRESENT", "ABSENT")
                ),
                "records_excluded_for_uncertain": len(record_ids) - n,
                "raw_agreement_present_absent": round(po, 6) if po is not None else "UNDEFINED",
                "positive_specific_agreement": round(2 * a_ / (2 * a_ + b_ + c_), 6)
                if (2 * a_ + b_ + c_)
                else "UNDEFINED",
                "negative_specific_agreement": round(2 * d_ / (2 * d_ + b_ + c_), 6)
                if (2 * d_ + b_ + c_)
                else "UNDEFINED",
                "prevalence_index": round(abs(a_ - d_) / n, 6) if n else "UNDEFINED",
                "bias_index": round(abs(b_ - c_) / n, 6) if n else "UNDEFINED",
                "pabak": round(2 * po - 1, 6) if po is not None else "UNDEFINED",
            }
        if label.status is LabelStatus.EXTRACTABLE:
            both_present = [
                r
                for r in record_ids
                if all(cells[a][r][lid]["state"] == "PRESENT" for a in annotators)
            ]
            pairs = [
                (cells[x][r][lid], cells[y][r][lid])
                for r in both_present
                for x, y in itertools.combinations(annotators, 2)
            ]
            entry["span_agreement"] = {
                "pairs_both_present": len(pairs),
                "exact": sum(bool(set(_spans(p)) & set(_spans(q))) for p, q in pairs),
                "overlap": sum(_overlap(_spans(p), _spans(q)) for p, q in pairs),
                "mean_character_jaccard": round(
                    sum(
                        len(_chars(_spans(p)) & _chars(_spans(q)))
                        / max(1, len(_chars(_spans(p)) | _chars(_spans(q))))
                        for p, q in pairs
                    )
                    / len(pairs),
                    6,
                )
                if pairs
                else "UNDEFINED",
            }
            if label.requires_subject:
                subject_pairs = [
                    (p["subject"], q["subject"])
                    for p, q in pairs
                    if p.get("subject") and q.get("subject")
                ]
                entry["subject_agreement"] = {
                    "pairs": len(subject_pairs),
                    "identical_offsets": sum(
                        (s["start"], s["end"]) == (t["start"], t["end"]) for s, t in subject_pairs
                    ),
                    "overlapping_offsets": sum(
                        s["start"] < t["end"] and t["start"] < s["end"] for s, t in subject_pairs
                    ),
                    "same_text_different_occurrence": sum(
                        s["quote_sha256"] == t["quote_sha256"]
                        and (s["start"], s["end"]) != (t["start"], t["end"])
                        for s, t in subject_pairs
                    ),
                    "case_folded_match": "NOT_COMPUTED_TEXT_NOT_COMMITTED",
                }
        per_label[lid] = entry
    queue = build_adjudication_queue(files)
    return {
        "$comment": "Development-set composition and agreement (N08-B). Measurements for an operator decision. Thresholds are read from the contract with their status; while PROPOSED_NOT_AUTHORISED, no gate verdict is issued. Prevalence describes this enriched query window only.",
        "split": "DEVELOPMENT",
        "annotators": annotators,
        "annotator_files_sha256": [hashlib.sha256(c.encode()).hexdigest() for c in content],
        "suspiciously_identical_label_content": len(set(content)) < len(content),
        "records": len(record_ids),
        "labels": per_label,
        "adjudication_queue_size": len(queue),
        "adjudication_queue_sha256": hashlib.sha256(
            json.dumps(queue, sort_keys=True).encode()
        ).hexdigest(),
        "gates": {
            "composition": {
                "rule": gate["per_split_per_label"],
                "status": gate["status"],
                "verdict": "GATE_NOT_AUTHORISED"
                if gate["status"] != "AUTHORISED"
                else "COMPUTE_AFTER_ADJUDICATION",
            },
            "agreement_floor": {
                "threshold": kappa_item["threshold"],
                "status": kappa_item["status"],
                "verdict": "GATE_NOT_AUTHORISED"
                if kappa_item["status"] != "AUTHORISED"
                else "COMPUTE",
            },
        },
    }


def analyse_single_human_reference(
    committed: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    """Composition of a SINGLE_HUMAN_REFERENCE (Mission 1.85.5). Not an agreement report.

    With one annotator nothing can be said about agreement between people, so every inter-annotator metric
    is NOT_APPLICABLE_SINGLE_ANNOTATOR (a string, never 0), no adjudication queue exists, and the
    agreement-floor gate has no verdict. The composition counts are the one annotator's own states: they
    describe a pilot reference, not a gold standard.
    """
    from .reference import (
        HOLDOUT_POLICY,
        NOT_APPLICABLE_SINGLE_ANNOTATOR,
        PILOT_NOT_CERTIFICATION,
        RESULT_SCOPE_DEVELOPMENT_PILOT,
        ReferenceStrength,
        single_annotator_agreement,
    )

    annotators, record_ids, cells = _index([committed])
    [annotator] = annotators
    gate = contract["evaluation_protocol"]["composition_gate"]
    per_label = {}
    for label in LABELS:
        if label.status is LabelStatus.NOT_SAFE:
            continue
        lid = label.label_id
        counts = {
            s: sum(cells[annotator][r][lid]["state"] == s for r in record_ids) for s in STATES
        }
        per_label[lid] = {
            "status": label.status.value,
            "state_counts": counts,
            "prevalence_present_among_decided": round(
                counts["PRESENT"] / (counts["PRESENT"] + counts["ABSENT"]), 6
            )
            if counts["PRESENT"] + counts["ABSENT"]
            else "UNDEFINED",
            "inter_annotator_agreement": single_annotator_agreement(),
        }
    content = json.dumps([r["labels"] for r in committed["records"]], sort_keys=True)
    return {
        "$comment": "SINGLE_HUMAN_REFERENCE composition (Mission 1.85.5). One genuine human annotator; no second human exists and none was simulated. Inter-annotator metrics are NOT_APPLICABLE_SINGLE_ANNOTATOR, not zero. A pilot reference, never inter-annotator gold.",
        "split": "DEVELOPMENT",
        "reference_strength": ReferenceStrength.SINGLE_HUMAN_REFERENCE.value,
        "result_scope": RESULT_SCOPE_DEVELOPMENT_PILOT,
        "result_label": PILOT_NOT_CERTIFICATION,
        "holdout_policy": HOLDOUT_POLICY,
        "annotators": annotators,
        "annotator_files_sha256": [hashlib.sha256(content.encode()).hexdigest()],
        "records": len(record_ids),
        "labels": per_label,
        "adjudication_queue_size": NOT_APPLICABLE_SINGLE_ANNOTATOR,
        "gates": {
            "composition": {
                "rule": gate["per_split_per_label"],
                "status": gate["status"],
                "verdict": "GATE_NOT_AUTHORISED"
                if gate["status"] != "AUTHORISED"
                else "COMPUTE_ON_THE_SINGLE_HUMAN_REFERENCE",
            },
            "agreement_floor": {
                "status": "REQUIRES_MULTI_HUMAN_REFERENCE",
                "verdict": NOT_APPLICABLE_SINGLE_ANNOTATOR,
            },
        },
    }


def validate_adjudication(adjudication: dict[str, Any], files: list[dict[str, Any]]) -> list[str]:
    problems = []
    annotators = {f["annotator_id"] for f in files}
    if adjudication.get("split") != "DEVELOPMENT":
        problems.append("adjudication in N08-B covers DEVELOPMENT only")
    if adjudication.get("method") not in ("THIRD_HUMAN", "JOINT_SESSION"):
        problems.append("method must be THIRD_HUMAN or JOINT_SESSION")
    if adjudication.get("adjudicator_origin") not in (
        "HUMAN_OPERATOR",
        "HUMAN_EXPERT",
        "HUMAN_NON_EXPERT",
    ):
        problems.append("adjudicator origin must be human")
    if (
        adjudication.get("method") == "THIRD_HUMAN"
        and adjudication.get("adjudicator_id") in annotators
    ):
        problems.append("a third-human adjudicator must not be one of the annotators")
    if adjudication.get("model_output_consulted") is not False:
        problems.append("model_output_consulted must be literally false")
    queue = build_adjudication_queue(files)
    if (
        adjudication.get("queue_sha256")
        != hashlib.sha256(json.dumps(queue, sort_keys=True).encode()).hexdigest()
    ):
        problems.append(
            "queue_sha256 does not match the queue recomputed from the annotation files"
        )
    wanted = {(q["label_id"], q["normalized_record_id"]) for q in queue}
    items = {
        (i.get("label_id"), i.get("normalized_record_id")): i for i in adjudication.get("items", [])
    }
    if set(items) != wanted:
        problems.append("items do not cover exactly the adjudication queue")
    _, _, cells = _index(files)
    for key, item in items.items():
        if key not in wanted:
            continue
        originals = {cells[a][key[1]][key[0]]["state"] for a in annotators}
        resolution, state = item.get("resolution"), item.get("resolved_state")
        if resolution not in ADJUDICATION_RESOLUTIONS:
            problems.append(f"{key}: unknown resolution")
        elif resolution == "RESOLVED_TO_EXISTING_STATE" and state not in originals:
            problems.append(f"{key}: resolved state is not one of the original states")
        elif resolution == "RESOLVED_AFTER_REREAD" and not item.get("note_present"):
            problems.append(f"{key}: a reread resolution needs a recorded note")
        elif resolution == "UNRESOLVED_KEPT_UNCERTAIN" and state != "UNCERTAIN":
            problems.append(f"{key}: unresolved items stay UNCERTAIN")
        if (
            state == "PRESENT"
            and not item.get("resolved_spans")
            and not any(
                lab.label_id == key[0] and lab.status is not LabelStatus.EXTRACTABLE
                for lab in LABELS
            )
        ):
            problems.append(f"{key}: a resolved PRESENT needs spans")
    return problems


def reference_labels(
    files: list[dict[str, Any]], adjudication: dict[str, Any] | None
) -> dict[str, dict[str, str]]:
    """Agreed cells plus adjudicated items. Recomputed, never stored. Unadjudicated disagreement is UNCERTAIN."""
    annotators, record_ids, cells = _index(files)
    items = {
        (i["label_id"], i["normalized_record_id"]): i for i in (adjudication or {}).get("items", [])
    }
    out: dict[str, dict[str, str]] = {}
    for label in LABELS:
        if label.status is LabelStatus.NOT_SAFE:
            continue
        for rid in record_ids:
            states = {cells[a][rid][label.label_id]["state"] for a in annotators}
            key = (label.label_id, rid)
            if key in items:
                state = items[key]["resolved_state"]
            elif len(states) == 1:
                state = states.pop()
            else:
                state = "UNCERTAIN"
            out.setdefault(label.label_id, {})[rid] = state
    return out
