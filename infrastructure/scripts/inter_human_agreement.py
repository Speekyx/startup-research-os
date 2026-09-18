"""Mission 1.85.14 (N08-B-PILOT). Agreement between two BLIND human annotations of the DEVELOPMENT records.

Written and committed before the second annotation exists, so nothing here is chosen after seeing it.

The two sides are fixed by file name and are the only annotation inputs:

    A  stack-overflow-semantic-annotations-development-operator-a-v1.json  (the original blind reference)
    B  stack-overflow-semantic-annotations-development-operator-b-v1.json  (the second blind annotation)

The post-model reviews of Missions 1.85.10 and 1.85.13 are NEVER an input to the agreement: those
judgements were made after seeing a model's answer, and mixing them in would make a blind-to-blind comparison
something else. They appear only afterwards, in a separately labelled post-hoc block, and only as record ids.

    --write   compute and write the agreement, the page and the A/B disagreement set (once B is imported)
    --check   verify them; while B is not imported, verify that nothing has been written yet

Until B exists the state is WAITING_FOR_SECOND_BLIND_HUMAN_ANNOTATION and nothing is computed. No database,
no network, no model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from collections import Counter
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/semantic-extraction-contract/python"))

from sros_semantic_extraction_contract.agreement import (  # noqa: E402
    cohen_kappa,
    krippendorff_alpha_nominal,
)
from sros_semantic_extraction_contract.labels import LABELS, LabelStatus  # noqa: E402

DATA = ROOT / "docs" / "data"
A_FILE = DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json"
B_FILE = DATA / "stack-overflow-semantic-annotations-development-operator-b-v1.json"
# The original blind reference, pinned: a changed A would not be the reference the pilots were read against.
A_SHA256 = "449ff10f8a60217bbf4b7887254cf81b492fdba962b39283f39d2acdf1a9fa3c"
CONTRACT = DATA / "first-person-semantic-extraction-contract-v1.json"
PRIOR_REVIEWS = (
    DATA / "semantic-extraction-post-model-review-development-v1.json",
    DATA / "semantic-extraction-balanced-post-model-review-development-v1.json",
)
AGREEMENT = DATA / "stack-overflow-semantic-inter-human-agreement-development-v1.json"
PAGE = DATA / "stack-overflow-semantic-inter-human-agreement-development-v1.md"
DISAGREEMENTS = DATA / "stack-overflow-semantic-a-b-disagreements-development-v1.json"
STATES = ("PRESENT", "ABSENT", "UNCERTAIN")
WAITING = "WAITING_FOR_SECOND_BLIND_HUMAN_ANNOTATION"
ADJUDICATION_REQUIRED = "SECOND_BLIND_HUMAN_REFERENCE_COMPLETE_ADJUDICATION_REQUIRED"
NO_EXTRACTABLE_DISAGREEMENT = "SECOND_BLIND_HUMAN_REFERENCE_COMPLETE_NO_EXTRACTABLE_DISAGREEMENT"


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def dump(doc: Any) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def check_inputs(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Refuse any input that is not two distinct, blind, human DEVELOPMENT annotations."""
    problems = []
    for side, doc in (("A", a), ("B", b)):
        if doc.get("reference_origin") not in {
            "HUMAN_OPERATOR",
            "HUMAN_EXPERT",
            "HUMAN_NON_EXPERT",
        }:
            problems.append(f"{side}_NOT_HUMAN")
        if doc.get("split") != "DEVELOPMENT":
            problems.append(f"{side}_NOT_DEVELOPMENT")
        attestation = doc.get("attestation") or {}
        for flag in ("no_model_output_seen", "did_not_see_other_annotators_labels"):
            if attestation.get(flag) is not True:
                problems.append(f"{side}_NOT_ATTESTED_BLIND:{flag}")
        for key in ("provenance", "blind"):
            if key in doc:
                problems.append(f"{side}_IS_A_REVIEW_NOT_AN_ANNOTATION")
    if a.get("annotator_id") == b.get("annotator_id"):
        problems.append("SAME_ANNOTATOR")
    if (
        b.get("blind_to_model_outputs") is not True
        or b.get("blind_to_other_annotators") is not True
    ):
        problems.append("B_BLINDNESS_NOT_RECORDED")
    if b.get("record_scope") != "DEVELOPMENT_EGRESS_APPROVED":
        problems.append("B_SCOPE_NOT_EGRESS_APPROVED")
    for key in ("dataset_id", "dataset_version", "corpus", "label_set", "text_surface"):
        if a.get(key) != b.get(key):
            problems.append(f"DATASET_MISMATCH:{key}")
    return problems


def _spans(cell: dict[str, Any]) -> list[tuple[int, int]]:
    return [(s["start"], s["end"]) for s in cell.get("spans", [])]


def _overlap(x: list[tuple[int, int]], y: list[tuple[int, int]]) -> bool:
    return any(p < s and r < q for p, q in x for r, s in y)


def _chars(spans: list[tuple[int, int]]) -> set[int]:
    return {i for p, q in spans for i in range(p, q)}


def _ratio(numerator: int, denominator: int) -> float | str:
    return round(numerator / denominator, 6) if denominator else "UNDEFINED"


def agreement(a: dict[str, Any], b: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    """A against B, and nothing else. The only inputs are the two blind files and the frozen contract."""
    cells_a = {r["normalized_record_id"]: r for r in a["records"]}
    cells_b = {r["normalized_record_id"]: r for r in b["records"]}
    records = sorted(set(cells_a) & set(cells_b))
    min_present = contract["evaluation_protocol"]["composition_gate"]["per_split_per_label"][
        "min_present"
    ]
    labels: dict[str, Any] = {}
    disagreements: dict[str, Any] = {}
    for label in LABELS:
        if label.status is LabelStatus.NOT_SAFE:
            continue
        lid = label.label_id
        extractable = label.status is LabelStatus.EXTRACTABLE
        sa = [cells_a[r]["labels"][lid]["state"] for r in records]
        sb = [cells_b[r]["labels"][lid]["state"] for r in records]
        confusion = {
            f"A_{x}__B_{y}": sum(p == x and q == y for p, q in zip(sa, sb, strict=True))
            for x in STATES
            for y in STATES
        }
        both = [(p, q) for p, q in zip(sa, sb, strict=True) if "UNCERTAIN" not in (p, q)]
        pp = sum(p == q == "PRESENT" for p, q in both)
        aa = sum(p == q == "ABSENT" for p, q in both)
        pa = sum(p == "PRESENT" and q == "ABSENT" for p, q in both)
        ap = sum(p == "ABSENT" and q == "PRESENT" for p, q in both)
        counts = {"A": dict(Counter(sa)), "B": dict(Counter(sb))}
        counts = {side: {s: c.get(s, 0) for s in STATES} for side, c in counts.items()}
        support_ok = min(counts["A"]["PRESENT"], counts["B"]["PRESENT"]) >= min_present
        entry: dict[str, Any] = {
            "status": label.status.value,
            "records": len(records),
            "state_counts": counts,
            "confusion": confusion,
            "raw_agreement_three_state": _ratio(
                sum(p == q for p, q in zip(sa, sb, strict=True)), len(records)
            ),
            "raw_agreement_present_absent": _ratio(pp + aa, len(both)),
            "records_with_an_uncertain": len(records) - len(both),
            "uncertain": {
                "A_only": sum(p == "UNCERTAIN" != q for p, q in zip(sa, sb, strict=True)),
                "B_only": sum(q == "UNCERTAIN" != p for p, q in zip(sa, sb, strict=True)),
                "both": sum(p == q == "UNCERTAIN" for p, q in zip(sa, sb, strict=True)),
            },
            "present_specific_agreement": _ratio(2 * pp, 2 * pp + pa + ap),
            "absent_specific_agreement": _ratio(2 * aa, 2 * aa + pa + ap),
            "cohen_kappa_three_state": cohen_kappa(sa, sb, STATES),
            "cohen_kappa_present_absent": cohen_kappa(
                [p for p, _ in both], [q for _, q in both], ("PRESENT", "ABSENT")
            ),
            "krippendorff_alpha_three_state": krippendorff_alpha_nominal(
                [[p, q] for p, q in zip(sa, sb, strict=True)]
            ),
            "krippendorff_alpha_present_absent": krippendorff_alpha_nominal(
                [[p, q] for p, q in both]
            ),
            "positive_class_support": {
                "min_present_per_annotator_required": min_present,
                "sufficient": support_ok,
                "reading": "kappa, alpha and PRESENT-specific agreement say little about the positive class"
                if not support_ok
                else "enough PRESENT on both sides to read positive-class agreement descriptively",
            },
        }
        ids = {
            "A_PRESENT_B_ABSENT": [
                r
                for r, p, q in zip(records, sa, sb, strict=True)
                if p == "PRESENT" and q == "ABSENT"
            ],
            "A_ABSENT_B_PRESENT": [
                r
                for r, p, q in zip(records, sa, sb, strict=True)
                if p == "ABSENT" and q == "PRESENT"
            ],
            "A_OR_B_UNCERTAIN": [
                r for r, p, q in zip(records, sa, sb, strict=True) if "UNCERTAIN" in (p, q)
            ],
            "SPAN_ONLY": [],
            "SUBJECT_ONLY": [],
        }
        if extractable:
            both_present = [
                r for r, p, q in zip(records, sa, sb, strict=True) if p == q == "PRESENT"
            ]
            pairs = [
                (cells_a[r]["labels"][lid], cells_b[r]["labels"][lid], r) for r in both_present
            ]
            entry["span_agreement"] = {
                "records_both_present": len(pairs),
                "identical_span_sets": sum(set(_spans(x)) == set(_spans(y)) for x, y, _ in pairs),
                "overlapping": sum(_overlap(_spans(x), _spans(y)) for x, y, _ in pairs),
                "mean_character_jaccard": round(
                    sum(
                        len(_chars(_spans(x)) & _chars(_spans(y)))
                        / max(1, len(_chars(_spans(x)) | _chars(_spans(y))))
                        for x, y, _ in pairs
                    )
                    / len(pairs),
                    6,
                )
                if pairs
                else "UNDEFINED",
            }
            ids["SPAN_ONLY"] = [r for x, y, r in pairs if not _overlap(_spans(x), _spans(y))]
            if label.requires_subject:
                subject_pairs = [(x.get("subject"), y.get("subject"), r) for x, y, r in pairs]
                entry["subject_agreement"] = {
                    "records_both_present": len(subject_pairs),
                    "identical_offsets": sum(
                        bool(s and t) and (s["start"], s["end"]) == (t["start"], t["end"])
                        for s, t, _ in subject_pairs
                    ),
                    "overlapping": sum(
                        bool(s and t) and s["start"] < t["end"] and t["start"] < s["end"]
                        for s, t, _ in subject_pairs
                    ),
                }
                ids["SUBJECT_ONLY"] = [
                    r
                    for s, t, r in subject_pairs
                    if r not in ids["SPAN_ONLY"]
                    and not (s and t and s["start"] < t["end"] and t["start"] < s["end"])
                ]
        labels[lid] = entry
        disagreements[lid] = {
            "incidence_only": not extractable,
            **{kind: sorted(v) for kind, v in ids.items()},
        }
    return {"records": records, "labels": labels, "disagreements": disagreements}


def post_hoc(disagreements: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Read ONLY after the blind comparison is frozen, and never fed back into it: which records the earlier
    post-model reviews looked at, and what the second blind annotator said on them."""
    by_b = {r["normalized_record_id"]: r["labels"] for r in b["records"]}
    rfa = "REPORTED_FAILED_ATTEMPT"
    contested = set().union(
        *(
            disagreements[rfa][k]
            for k in ("A_PRESENT_B_ABSENT", "A_ABSENT_B_PRESENT", "A_OR_B_UNCERTAIN")
        )
    )
    reviews = []
    for path in PRIOR_REVIEWS:
        if not path.exists():
            continue
        doc = load(path)
        rows = [
            {
                "normalized_record_id": d["normalized_record_id"],
                "post_model_decision": d["decision"],
                "operator_b_blind_state": by_b.get(d["normalized_record_id"], {})
                .get(rfa, {})
                .get("state", "NOT_IN_SCOPE"),
                "a_b_disagree": d["normalized_record_id"] in contested,
            }
            for d in sorted(doc["decisions"], key=lambda d: d["normalized_record_id"])
        ]
        reviews.append({"review_id": doc["review_id"], "review_sha256": sha(path), "records": rows})
    return {
        "$comment": "POST-HOC DIAGNOSTIC, not part of the agreement. The post-model reviews were made after seeing a model's answer; they are shown next to the blind A/B comparison, never inside it.",
        "label": rfa,
        "reviews": reviews,
    }


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    a, b = load(A_FILE), load(B_FILE)
    if sha(A_FILE) != A_SHA256:
        raise SystemExit("REFUSED  the operator-a blind annotation is not the original reference")
    problems = check_inputs(a, b)
    if problems:
        raise SystemExit("REFUSED  " + ", ".join(problems))
    contract = load(CONTRACT)
    result = agreement(a, b, contract)
    extractable = [lbl.label_id for lbl in LABELS if lbl.status is LabelStatus.EXTRACTABLE]
    open_items = sum(
        len(result["disagreements"][lid][kind])
        for lid in extractable
        for kind in (
            "A_PRESENT_B_ABSENT",
            "A_ABSENT_B_PRESENT",
            "A_OR_B_UNCERTAIN",
            "SPAN_ONLY",
            "SUBJECT_ONLY",
        )
    )
    status = ADJUDICATION_REQUIRED if open_items else NO_EXTRACTABLE_DISAGREEMENT
    inputs = {
        "operator_a_sha256": sha(A_FILE),
        "operator_b_sha256": sha(B_FILE),
        "contract_sha256": sha(CONTRACT),
    }
    doc = {
        "$comment": "INTER-HUMAN AGREEMENT, DEVELOPMENT (Mission 1.85.14). The original blind operator-a annotation against the second blind operator-b annotation, on the records both labelled. No post-model review is an input. Not a consensus, not an adjudicated reference and not certification.",
        "analysis_id": "stack-overflow-semantic-inter-human-agreement-development",
        "version": "1.0.0",
        "status": status,
        "annotators": [a["annotator_id"], b["annotator_id"]],
        "inputs": inputs,
        "records_compared": len(result["records"]),
        "extractable_items_needing_adjudication": open_items,
        "labels": result["labels"],
        "adjudicated": False,
        "consensus_reference_created": False,
        "post_hoc_diagnostic_not_part_of_agreement": post_hoc(result["disagreements"], b),
    }
    disagreement_doc = {
        "$comment": "A/B DISAGREEMENTS for a future human adjudication (Mission 1.85.14). Ids only, derived mechanically from the two blind annotations. Nothing here is adjudicated.",
        "set_id": "stack-overflow-semantic-a-b-disagreements-development",
        "version": "1.0.0",
        "inputs": inputs,
        "adjudicated": False,
        "labels": result["disagreements"],
    }
    return doc, disagreement_doc


def page(doc: dict[str, Any], disagreements: dict[str, Any]) -> bytes:
    lines = [
        "# Inter-human agreement, DEVELOPMENT (v1)",
        "",
        "> Generated by `infrastructure/scripts/inter_human_agreement.py`. Do not edit by hand.",
        "",
        f"Status `{doc['status']}`. `{doc['annotators'][0]}` (original blind reference) against `{doc['annotators'][1]}` (second blind annotation) on {doc['records_compared']} records. No post-model review is an input. Not a consensus and not adjudicated.",
        "",
    ]
    for lid, e in doc["labels"].items():
        lines += [
            f"## {lid} ({e['status']})",
            "",
            "| A \\ B | PRESENT | ABSENT | UNCERTAIN |",
            "|---|---|---|---|",
        ]
        for x in STATES:
            lines.append(
                f"| {x} | "
                + " | ".join(str(e["confusion"][f"A_{x}__B_{y}"]) for y in STATES)
                + " |"
            )
        lines += [
            "",
            f"A {json.dumps(e['state_counts']['A'])}; B {json.dumps(e['state_counts']['B'])}.",
            "",
            f"Raw agreement {e['raw_agreement_three_state']} (three states), {e['raw_agreement_present_absent']} (PRESENT/ABSENT, {e['records_with_an_uncertain']} records with an UNCERTAIN excluded). PRESENT-specific {e['present_specific_agreement']}, ABSENT-specific {e['absent_specific_agreement']}. Cohen's kappa {e['cohen_kappa_three_state']} / {e['cohen_kappa_present_absent']}; Krippendorff's alpha {e['krippendorff_alpha_three_state']} / {e['krippendorff_alpha_present_absent']}. Positive-class support sufficient: {e['positive_class_support']['sufficient']}.",
            "",
        ]
        if "span_agreement" in e:
            s = e["span_agreement"]
            lines += [
                f"Spans on {s['records_both_present']} records both PRESENT: identical {s['identical_span_sets']}, overlapping {s['overlapping']}, mean character Jaccard {s['mean_character_jaccard']}.",
                "",
            ]
        for kind, ids in disagreements["labels"][lid].items():
            if kind != "incidence_only" and ids:
                lines.append(f"- {kind}: {len(ids)} ({', '.join(i[:8] for i in ids)})")
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = (AGREEMENT, PAGE, DISAGREEMENTS)
    if not B_FILE.exists():
        written = [p.name for p in outputs if p.exists()]
        if written:
            print(f"FAIL     agreement artifacts exist before the second annotation: {written}")
            return 1
        print(f"ok       {WAITING}: no second blind annotation imported; nothing computed")
        return 0
    doc, disagreements = build()
    targets = {
        AGREEMENT: dump(doc),
        PAGE: page(doc, disagreements),
        DISAGREEMENTS: dump(disagreements),
    }
    if args.write:
        for path, content in targets.items():
            path.write_bytes(content)
        print(
            f"wrote {AGREEMENT.name}, {PAGE.name} and {DISAGREEMENTS.name}; status {doc['status']}"
        )
        return 0
    stale = [p.name for p, c in targets.items() if not p.exists() or p.read_bytes() != c]
    for name in stale:
        print(f"FAIL     {name} is stale")
    if not stale:
        print(f"ok       {AGREEMENT.name} matches (status {doc['status']})")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
