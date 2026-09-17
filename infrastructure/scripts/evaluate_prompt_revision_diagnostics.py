"""Mission 1.85.12 (N08-B-PILOT). Development diagnostics for prompt 1.1.0, from committed artifacts only.

Written and committed BEFORE the packet v5 run, like the Mission 1.85.9 rules it reuses. Three questions are
answered separately and never merged into one score:

    A. KNOWN_OVERREAD (9 records, Mission 1.85.10): does prompt 1.1.0 still call REPORTED_FAILED_ATTEMPT
       PRESENT where the operator confirmed a model over-read?
    B. POSITIVE_SENSITIVITY (15 blind-reference PRESENT records): does prompt 1.1.0 keep finding them, or did
       it buy precision by answering ABSENT?
    C. VALID OVERLAP: prompt 1.0.0 (Mission 1.85.9, a partial run) against prompt 1.1.0 (the v5 run), only on
       records where BOTH runs have an accepted extraction. Never "1.0.0 over 46" against "1.1.0 over 46".

A and B are POST_MODEL_DEVELOPMENT_REGRESSION_DIAGNOSTIC: not preregistered thresholds, not certification, and
not a redefinition of pilot success. C is not an independent test set: prompt 1.1.0 was revised after seeing the
nine over-reads, so improvement on them is developmental regression evidence, not generalisation evidence.

Per record a label reads, as in evaluate_semantic_extraction_pilot.py: PRESENT, ABSENT, ABSTAIN,
NO_VALID_OUTPUT (attempted, no accepted extraction, including a provider failure) or NOT_ATTEMPTED.

    uv run python infrastructure/scripts/evaluate_prompt_revision_diagnostics.py --write
    uv run python infrastructure/scripts/evaluate_prompt_revision_diagnostics.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infrastructure" / "scripts"))

import evaluate_semantic_extraction_pilot as pilot_evaluator  # noqa: E402

DATA = ROOT / "docs" / "data"
SPEC = DATA / "semantic-extraction-rfa-regression-spec-development-v1.json"
REFERENCE = pilot_evaluator.REFERENCE
OUTPUT = DATA / "semantic-extraction-prompt-revision-diagnostics-development-v1.json"
PAGE = DATA / "semantic-extraction-prompt-revision-diagnostics-development-v1.md"
DIAGNOSTICS_ID = "semantic-extraction-prompt-revision-diagnostics"
DIAGNOSTICS_VERSION = "1.0.0"
RFA = "REPORTED_FAILED_ATTEMPT"
NEG = "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION"
CALLS = ("PRESENT", "ABSENT", "ABSTAIN", "NO_VALID_OUTPUT", "NOT_ATTEMPTED")
TRANSITIONS = (
    ("PRESENT", "ABSENT"),
    ("PRESENT", "ABSTAIN"),
    ("ABSENT", "PRESENT"),
    ("ABSENT", "ABSTAIN"),
    ("PRESENT", "PRESENT"),
    ("ABSENT", "ABSENT"),
)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def calls_for(summary: dict[str, Any], label: str) -> dict[str, str]:
    return {
        r["normalized_record_id"]: pilot_evaluator.model_call(r, label) for r in summary["records"]
    }


def call(calls: dict[str, str], rid: str) -> str:
    return calls.get(rid, "NOT_ATTEMPTED")


def final_outcome(summary: dict[str, Any], rid: str) -> str:
    record = next((r for r in summary["records"] if r["normalized_record_id"] == rid), None)
    return pilot_evaluator.final_outcome(record)


def prompt_measures(
    ids: list[str], calls: dict[str, str], reference: dict[str, str]
) -> dict[str, Any]:
    decided = [rid for rid in ids if reference[rid] in ("PRESENT", "ABSENT")]
    tp = sum(1 for rid in decided if reference[rid] == "PRESENT" and calls[rid] == "PRESENT")
    fp = sum(1 for rid in decided if reference[rid] == "ABSENT" and calls[rid] == "PRESENT")
    tn = sum(1 for rid in decided if reference[rid] == "ABSENT" and calls[rid] == "ABSENT")
    fn = sum(1 for rid in decided if reference[rid] == "PRESENT" and calls[rid] == "ABSENT")
    ref_present = sum(1 for rid in decided if reference[rid] == "PRESENT")
    present_calls = tp + fp
    return {
        "records": len(ids),
        "reference": {
            s: sum(1 for rid in ids if reference[rid] == s)
            for s in ("PRESENT", "ABSENT", "UNCERTAIN")
        },
        "model": {s: sum(1 for rid in ids if calls[rid] == s) for s in CALLS},
        "model_present_on_decided_records": present_calls,
        "true_present": tp,
        "false_present": fp,
        "true_absent": tn,
        "missed_reference_present_as_absent": fn,
        "reference_present_recovered": f"{tp}/{ref_present}",
        "recall_on_reference_present": round(tp / ref_present, 6) if ref_present else None,
        "precision": round(tp / present_calls, 6) if present_calls else None,
        "false_present_rate": round(fp / present_calls, 6) if present_calls else None,
        "false_present_rate_upper_95_descriptive": (
            pilot_evaluator.clopper_pearson_upper(fp, present_calls) if present_calls else None
        ),
    }


def delta(before: Any, after: Any) -> Any:
    if before is None or after is None:
        return None
    return round(after - before, 6)


def build() -> dict[str, Any]:
    spec = load(SPEC)
    v1_summary = load(pilot_evaluator.V1.summary)
    v2_summary = load(pilot_evaluator.V2.summary)
    v1_packet = load(pilot_evaluator.V1.packet)
    v2_packet = load(pilot_evaluator.V2.packet)
    if v2_summary["packet_sha256"] != v2_packet["packet_sha256"]:
        raise SystemExit("REFUSED  the v2 run summary does not name packet v5")
    if v1_summary["packet_sha256"] != v1_packet["packet_sha256"]:
        raise SystemExit("REFUSED  the v1 run summary does not name packet v4")
    labels = {r["normalized_record_id"]: r["labels"] for r in load(REFERENCE)["records"]}
    reference = {
        label: {rid: labels[rid][label]["state"] for rid in labels} for label in (RFA, NEG)
    }
    v1_calls = {label: calls_for(v1_summary, label) for label in (RFA, NEG)}
    v2_calls = {label: calls_for(v2_summary, label) for label in (RFA, NEG)}
    approved = v2_packet["selection"]["egress_approved_record_ids"]

    # -- A. known over-reads --
    overread = [r["normalized_record_id"] for r in spec["sets"]["KNOWN_OVERREAD"]["records"]]
    a_rows = []
    for rid in overread:
        now = call(v2_calls[RFA], rid)
        a_rows.append(
            {
                "normalized_record_id": rid,
                "prompt_1_0_0_call": call(v1_calls[RFA], rid),
                "prompt_1_1_0_call": now,
                "prompt_1_1_0_final_outcome": final_outcome(v2_summary, rid),
                "status": {
                    "ABSENT": "CORRECTED",
                    "PRESENT": "PERSISTENT_OVERREAD",
                    "ABSTAIN": "ABSTAINED",
                }.get(now, "UNAVAILABLE_UNSCORED"),
            }
        )
    count = lambda rows, status: sum(1 for r in rows if r["status"] == status)  # noqa: E731
    known_overread = {
        "diagnostic_type": "POST_MODEL_DEVELOPMENT_REGRESSION_DIAGNOSTIC",
        "is_threshold": False,
        "is_certification": False,
        "prior_overreads": len(overread),
        "corrected_rfa_absent": count(a_rows, "CORRECTED"),
        "persistent_rfa_present": count(a_rows, "PERSISTENT_OVERREAD"),
        "abstained": count(a_rows, "ABSTAINED"),
        "unavailable_unscored": count(a_rows, "UNAVAILABLE_UNSCORED"),
        "records": a_rows,
    }

    # -- B. positive sensitivity --
    positives = [r["normalized_record_id"] for r in spec["sets"]["POSITIVE_SENSITIVITY"]["records"]]
    b_rows = [
        {
            "normalized_record_id": rid,
            "prompt_1_1_0_call": call(v2_calls[RFA], rid),
            "prompt_1_1_0_final_outcome": final_outcome(v2_summary, rid),
        }
        for rid in positives
    ]
    b_calls = [r["prompt_1_1_0_call"] for r in b_rows]
    evaluated = sum(1 for c in b_calls if c in ("PRESENT", "ABSENT", "ABSTAIN"))
    retained = b_calls.count("PRESENT")
    positive_sensitivity = {
        "diagnostic_type": "POST_MODEL_DEVELOPMENT_REGRESSION_DIAGNOSTIC",
        "is_threshold": False,
        "is_certification": False,
        "reference_positives": len(positives),
        "evaluated_with_valid_output": evaluated,
        "true_present_retained": retained,
        "missed_present_as_absent": b_calls.count("ABSENT"),
        "abstentions": b_calls.count("ABSTAIN"),
        "unavailable": b_calls.count("NO_VALID_OUTPUT") + b_calls.count("NOT_ATTEMPTED"),
        "descriptive_recall_over_all_positives": round(retained / len(positives), 6),
        "descriptive_recall_over_evaluated_positives": (
            round(retained / evaluated, 6) if evaluated else None
        ),
        "records": b_rows,
    }

    # -- C. valid overlap --
    valid = ("PRESENT", "ABSENT", "ABSTAIN")
    overlap = [
        rid
        for rid in approved
        if call(v1_calls[RFA], rid) in valid and call(v2_calls[RFA], rid) in valid
    ]
    comparison: dict[str, Any] = {
        "is_independent_test_set": False,
        "why_not_independent": "prompt 1.1.0 was revised after the operator reviewed the nine Mission 1.85.9 over-reads, which lie inside this overlap; an improvement on them is developmental regression evidence, not unbiased generalisation evidence",
        "overlap_rule": "records where the Mission 1.85.9 run (prompt 1.0.0) and the Mission 1.85.12 run (prompt 1.1.0) both have an accepted extraction",
        "prompt_1_0_0_run_records_accepted": sum(
            1 for rid in approved if call(v1_calls[RFA], rid) in valid
        ),
        "prompt_1_1_0_run_records_accepted": sum(
            1 for rid in approved if call(v2_calls[RFA], rid) in valid
        ),
        "overlap_records": len(overlap),
        "overlap_record_ids": sorted(overlap),
        "labels": {},
    }
    for label in (RFA, NEG):
        before = prompt_measures(overlap, v1_calls[label], reference[label])
        after = prompt_measures(overlap, v2_calls[label], reference[label])
        transitions = {
            f"{a}_to_{b}": sorted(
                rid for rid in overlap if v1_calls[label][rid] == a and v2_calls[label][rid] == b
            )
            for a, b in TRANSITIONS
        }
        comparison["labels"][label] = {
            "prompt_1_0_0": before,
            "prompt_1_1_0": after,
            "delta": {
                "false_present": after["false_present"] - before["false_present"],
                "true_present": after["true_present"] - before["true_present"],
                "model_present_on_decided_records": after["model_present_on_decided_records"]
                - before["model_present_on_decided_records"],
                "precision": delta(before["precision"], after["precision"]),
                "false_present_rate": delta(
                    before["false_present_rate"], after["false_present_rate"]
                ),
                "recall_on_reference_present": delta(
                    before["recall_on_reference_present"], after["recall_on_reference_present"]
                ),
            },
            "changed_classifications": {k: len(v) for k, v in transitions.items()},
            "changed_classification_records": transitions,
        }

    return {
        "$comment": "PROMPT 1.1.0 DEVELOPMENT DIAGNOSTICS (Mission 1.85.12). Ids and counts only, from committed artifacts. A and B are POST_MODEL_DEVELOPMENT_REGRESSION_DIAGNOSTIC, not thresholds and not certification; C compares prompts only on the valid overlap and is not an independent test set. Mission 1.85.9 stays PILOT_OUTSIDE_PROPOSED_BOUND. Evaluation artifact only.",
        "diagnostics_id": DIAGNOSTICS_ID,
        "version": DIAGNOSTICS_VERSION,
        "RESULT_SCOPE": "DEVELOPMENT_PILOT",
        "result_label": "PILOT_NOT_CERTIFICATION",
        "REFERENCE_STRENGTH": "SINGLE_HUMAN_REFERENCE",
        "inputs": {
            "regression_spec_sha256": sha(SPEC),
            "reference_sha256": sha(REFERENCE),
            "prompt_1_0_0_run_summary_sha256": sha(pilot_evaluator.V1.summary),
            "prompt_1_0_0_packet_sha256": v1_packet["packet_sha256"],
            "prompt_1_1_0_run_summary_sha256": sha(pilot_evaluator.V2.summary),
            "prompt_1_1_0_packet_sha256": v2_packet["packet_sha256"],
        },
        "A_known_overread": known_overread,
        "B_positive_sensitivity": positive_sensitivity,
        "C_valid_overlap_comparison": comparison,
        "mission_1_85_9_reading_unchanged": "PILOT_OUTSIDE_PROPOSED_BOUND",
    }


def page(doc: dict[str, Any]) -> bytes:
    a, b, c = (
        doc["A_known_overread"],
        doc["B_positive_sensitivity"],
        doc["C_valid_overlap_comparison"],
    )
    lines = [
        "# Prompt 1.1.0 DEVELOPMENT diagnostics (v1)",
        "",
        "> Generated by `infrastructure/scripts/evaluate_prompt_revision_diagnostics.py` from committed artifacts. Do not edit by hand.",
        "",
        "`SINGLE_HUMAN_REFERENCE` / `DEVELOPMENT_PILOT` / `PILOT_NOT_CERTIFICATION`. A and B are post-model development regression diagnostics, not thresholds. C is not an independent test set.",
        "",
        "## A. Known over-reads",
        "",
        f"Prior {a['prior_overreads']}; corrected (ABSENT) {a['corrected_rfa_absent']}; persistent (PRESENT) {a['persistent_rfa_present']}; abstained {a['abstained']}; unavailable {a['unavailable_unscored']}.",
        "",
        "| Record | Prompt 1.0.0 | Prompt 1.1.0 | Status |",
        "|---|---|---|---|",
    ]
    for r in a["records"]:
        lines.append(
            f"| `{r['normalized_record_id'][:8]}` | {r['prompt_1_0_0_call']} | {r['prompt_1_1_0_call']} | {r['status']} |"
        )
    lines += [
        "",
        "## B. Positive sensitivity",
        "",
        f"Reference positives {b['reference_positives']}; evaluated {b['evaluated_with_valid_output']}; retained PRESENT {b['true_present_retained']}; missed as ABSENT {b['missed_present_as_absent']}; abstentions {b['abstentions']}; unavailable {b['unavailable']}; descriptive recall {b['descriptive_recall_over_all_positives']} over all, {b['descriptive_recall_over_evaluated_positives']} over evaluated.",
        "",
        "## C. Valid overlap, prompt 1.0.0 against prompt 1.1.0",
        "",
        f"Overlap {c['overlap_records']} records (prompt 1.0.0 run accepted {c['prompt_1_0_0_run_records_accepted']}, prompt 1.1.0 run accepted {c['prompt_1_1_0_run_records_accepted']}).",
        "",
    ]
    for label, data in c["labels"].items():
        before, after = data["prompt_1_0_0"], data["prompt_1_1_0"]
        lines += [
            f"### {label}",
            "",
            "| Measure | Prompt 1.0.0 | Prompt 1.1.0 |",
            "|---|---|---|",
            f"| Model PRESENT (decided records) | {before['model_present_on_decided_records']} | {after['model_present_on_decided_records']} |",
            f"| Reference PRESENT | {before['reference']['PRESENT']} | {after['reference']['PRESENT']} |",
            f"| True PRESENT | {before['true_present']} | {after['true_present']} |",
            f"| False PRESENT | {before['false_present']} | {after['false_present']} |",
            f"| Reference PRESENT recovered | {before['reference_present_recovered']} | {after['reference_present_recovered']} |",
            f"| Precision | {before['precision']} | {after['precision']} |",
            f"| False-PRESENT rate | {before['false_present_rate']} | {after['false_present_rate']} |",
            "",
            "Changed classifications: "
            + ", ".join(f"{k} {v}" for k, v in data["changed_classifications"].items())
            + ".",
            "",
        ]
    return "\n".join(lines).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not pilot_evaluator.V2.attempt.exists():
        print("ok       no packet v5 attempt exists: nothing to diagnose")
        return 0
    doc = build()
    targets = {OUTPUT: pilot_evaluator.dump(doc), PAGE: page(doc)}
    if args.write:
        for path, content in targets.items():
            path.write_bytes(content)
        print(f"wrote {OUTPUT.name} and {PAGE.name}")
        return 0
    stale = [
        p.name for p, content in targets.items() if not p.exists() or p.read_bytes() != content
    ]
    for name in stale:
        print(f"FAIL     {name} is stale")
    if not stale:
        print(f"ok       {OUTPUT.name} matches")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
