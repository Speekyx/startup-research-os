"""Mission 1.85.9 (N08-B-PILOT). Summarise the one approved DEVELOPMENT pilot run and evaluate it.

The rules below were written and committed BEFORE the run they evaluate, and the report states that commit.
Nothing here is chosen after seeing a result.

Two steps:

    1. --summarise <run file>
       Reads the runner's run record from its directory OUTSIDE the repository (it holds the model payloads,
       which contain verbatim quotes of Stack Overflow text) and the DEVELOPMENT surfaces from the research
       database. Writes a committed summary that carries NO source text: quotes become sha256 digests and
       validator offsets, request ids become digests, and every accepted finding's span is checked
       mechanically against the surface.

    2. --write / --check
       From committed artifacts only (the run summary, the single-human reference, the packet and the
       operator decisions): computes the nine authorised pilot readings and the disagreement lists, and
       renders a JSON evaluation and a Markdown page. No database, no network, no model.

    DATABASE_URL=... uv run python infrastructure/scripts/evaluate_semantic_extraction_pilot.py --summarise <run>
    uv run python infrastructure/scripts/evaluate_semantic_extraction_pilot.py --write
    uv run python infrastructure/scripts/evaluate_semantic_extraction_pilot.py --check

Readings use only PILOT_WITHIN_PROPOSED_BOUND, PILOT_OUTSIDE_PROPOSED_BOUND and PILOT_INSUFFICIENT_SUPPORT,
under RESULT_SCOPE DEVELOPMENT_PILOT and PILOT_NOT_CERTIFICATION. A descriptive item with no proposed bound
has reading null. The run-to-run flip rate is not evaluated: the operator rejected it for this first pilot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import statistics
import sys
from decimal import Decimal
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
PACKET = DATA / "semantic-extraction-evaluation-packet-development-v1.json"
DECISIONS = DATA / "semantic-extraction-operator-decisions-development-v1.json"
CONTRACT = DATA / "first-person-semantic-extraction-contract-v1.json"
REFERENCE = DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json"
SUMMARY = DATA / "semantic-extraction-pilot-run-development-v1.json"
EVALUATION = DATA / "semantic-extraction-pilot-evaluation-development-v1.json"
PAGE = DATA / "semantic-extraction-pilot-evaluation-development-v1.md"

EVALUATOR_ID = "semantic-extraction-development-pilot-evaluator"
EVALUATOR_VERSION = "1.0.0"
EXTRACTABLE = ("REPORTED_FAILED_ATTEMPT", "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION")
WITHIN = "PILOT_WITHIN_PROPOSED_BOUND"
OUTSIDE = "PILOT_OUTSIDE_PROPOSED_BOUND"
INSUFFICIENT = "PILOT_INSUFFICIENT_SUPPORT"
DECIDED = ("PRESENT", "ABSENT")
# Frozen minimums (Mission 1.85.7 decision package): acceptance rate and abstention need 20 units.
MIN_ATTEMPTED_FOR_ACCEPTANCE = 20
MIN_DECIDED_CELLS_FOR_ABSTENTION = 20
CONFIDENCE = Decimal("0.95")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def dump(doc: Any) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


# -- statistics ---------------------------------------------------------------------------------------


def _binomial_cdf(x: int, n: int, p: float) -> float:
    total, term = 0.0, (1.0 - p) ** n
    for k in range(0, x + 1):
        if k > 0:
            term *= (n - k + 1) / k * (p / (1.0 - p)) if p < 1.0 else 0.0
        total += term
    return total


def clopper_pearson_upper(x: int, n: int, confidence: float = 0.95) -> float:
    """One-sided exact upper bound: the p at which P(X <= x) = 1 - confidence. 3/n-ish at x = 0."""
    if n <= 0:
        raise ValueError("n must be positive")
    if x >= n:
        return 1.0
    alpha = 1.0 - confidence
    low, high = x / n, 1.0
    for _ in range(200):
        mid = (low + high) / 2
        if _binomial_cdf(x, n, mid) > alpha:
            low = mid
        else:
            high = mid
    return round(high, 6)


def nearest_rank(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, -(-percentile * len(ordered) // 100))
    return ordered[rank - 1]


# -- step 1: summarise --------------------------------------------------------------------------------


def summarise(run_path: pathlib.Path, surfaces: dict[str, str]) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "packages" / "semantic-extraction-contract" / "python"))
    from sros_semantic_extraction_contract import surface_sha256

    raw = run_path.read_bytes()
    run = json.loads(raw.decode("utf-8"))
    records = []
    for result in run["records"]:
        surface = surfaces[result["normalized_record_id"]]
        if surface_sha256(surface) != result["surface_sha256"]:
            raise SystemExit(f"surface changed for {result['normalized_record_id']}")
        attempts = []
        for attempt in result["attempts"]:
            attempts.append(
                {
                    "call_number": attempt.get("call_number"),
                    "retry_number": attempt.get("retry_number"),
                    "outcome": attempt["outcome"],
                    "error": attempt.get("error"),
                    "transport": [
                        {
                            "status": t.get("status"),
                            "transport_error": t.get("transport_error"),
                            "request_id_sha256": sha(t["request_id"].encode("utf-8"))
                            if t.get("request_id")
                            else None,
                            "body_sha256": t.get("body_sha256"),
                            "stop_reason": t.get("stop_reason"),
                            "usage": t.get("usage"),
                            "elapsed_seconds": t.get("elapsed_seconds"),
                        }
                        for t in attempt.get("transport", [])
                    ],
                }
            )
        payload = result.get("payload")
        payload_findings = (payload or {}).get("findings") if isinstance(payload, dict) else None
        extraction = result.get("extraction")
        findings = []
        if extraction:
            for finding in extraction["findings"]:
                evidence = surface[finding["evidence_start"] : finding["evidence_end"]]
                subject = (
                    surface[finding["subject_start"] : finding["subject_end"]]
                    if finding["subject_start"] is not None
                    else None
                )
                quotes = [
                    p
                    for p in (payload_findings or [])
                    if isinstance(p, dict) and p.get("finding_type") == finding["finding_type"]
                ]
                findings.append(
                    {
                        "finding_id": finding["finding_id"],
                        "finding_type": finding["finding_type"],
                        "evidence_start": finding["evidence_start"],
                        "evidence_end": finding["evidence_end"],
                        "subject_start": finding["subject_start"],
                        "subject_end": finding["subject_end"],
                        "evidence_sha256": sha(evidence.encode("utf-8")),
                        "evidence_span_matches_a_returned_quote": any(
                            p.get("evidence_quote") == evidence for p in quotes
                        ),
                        "subject_span_matches_a_returned_quote": (
                            None
                            if subject is None
                            else any(p.get("subject_quote") == subject for p in quotes)
                        ),
                    }
                )
        records.append(
            {
                "normalized_record_id": result["normalized_record_id"],
                "surface_sha256": result["surface_sha256"],
                "attempts": attempts,
                "accepted": result.get("accepted", False),
                "refusal_codes": sorted({r[0] for r in result.get("refusals") or []}),
                "payload_extraction_state": payload.get("extraction_state")
                if isinstance(payload, dict)
                else None,
                "payload_finding_types": sorted(
                    p.get("finding_type") for p in payload_findings or [] if isinstance(p, dict)
                ),
                "extraction": (
                    {
                        "extraction_id": extraction["extraction_id"],
                        "extraction_state": extraction["extraction_state"],
                        "findings": findings,
                    }
                    if extraction
                    else None
                ),
            }
        )
    return {
        "$comment": "Summary of the one approved DEVELOPMENT pilot run (Mission 1.85.9). No source text: quotes are digests and offsets. The full run record, with model payloads, stays outside the repository. Evaluation artifact only; nothing here is a Signal, Claim, Evidence or finding.",
        "summary_id": "semantic-extraction-pilot-run-development",
        "version": "1.0.0",
        "run_file_sha256": sha(raw),
        "packet_id": run.get("packet_id"),
        "packet_version": run.get("packet_version"),
        "packet_sha256": run["packet_sha256"],
        "approval_sha256": run.get("approval_sha256"),
        "provider": run.get("provider"),
        "model": run.get("model"),
        "REFERENCE_STRENGTH": run.get("REFERENCE_STRENGTH"),
        "RESULT_SCOPE": run.get("RESULT_SCOPE"),
        "result_label": run.get("result_label"),
        "records_approved": run.get("records_approved"),
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "elapsed_seconds": run.get("elapsed_seconds"),
        "calls": run["calls"],
        "stopped": run["stopped"],
        "cost": run["cost"],
        "canonical_writes": run.get("canonical_writes"),
        "records": records,
    }


# -- step 2: evaluate ---------------------------------------------------------------------------------


def model_call(record: dict[str, Any] | None, label: str) -> str:
    if record is None or not record["attempts"]:
        return "NOT_ATTEMPTED"
    extraction = record.get("extraction")
    if not record["accepted"] or extraction is None:
        return "NO_VALID_OUTPUT"
    state = extraction["extraction_state"]
    if state == "ABSTAINED_TEXT_INSUFFICIENT":
        return "ABSTAIN"
    if state == "FINDINGS_PRESENT" and any(
        f["finding_type"] == label for f in extraction["findings"]
    ):
        return "PRESENT"
    return "ABSENT"


def final_outcome(record: dict[str, Any] | None) -> str:
    if record is None or not record["attempts"]:
        return "NOT_ATTEMPTED"
    return record["attempts"][-1]["outcome"]


def evaluate() -> dict[str, Any]:
    summary = load(SUMMARY)
    packet = load(PACKET)
    decisions = load(DECISIONS)
    contract = load(CONTRACT)
    reference = load(REFERENCE)
    approved = packet["selection"]["egress_approved_record_ids"]
    by_id = {r["normalized_record_id"]: r for r in summary["records"]}
    ref = {r["normalized_record_id"]: r["labels"] for r in reference["records"]}
    required = {
        i["label"]: i["required_present_predictions"]
        for i in contract["proposed_thresholds"]["items"]
        if i["metric"] == "false_present_rate_upper_95"
    }
    proposed = {
        i["metric"] + "::" + i["label"]: i["proposed"]
        for i in load(DATA / "semantic-extraction-threshold-partition-v1.json")["buckets"][
            "SINGLE_HUMAN_PILOT_VALID"
        ]
    }
    authorised = set(packet["operator_decisions"]["thresholds_authorised"])

    # -- run execution --
    attempts = [a for r in summary["records"] for a in r["attempts"]]
    transports = [t for a in attempts for t in a["transport"]]
    latencies = [t["elapsed_seconds"] for t in transports if t.get("elapsed_seconds") is not None]
    usage = [t["usage"] for t in transports if t.get("usage")]
    outcomes: dict[str, int] = {}
    for r in summary["records"]:
        outcomes[final_outcome(r)] = outcomes.get(final_outcome(r), 0) + 1
    ceiling = Decimal(summary["cost"]["accepted_hard_ceiling_usd"])
    spent = Decimal(summary["cost"]["spent_usd"])
    attempted = sum(1 for rid in approved if by_id.get(rid) and by_id[rid]["attempts"])
    accepted_records = sum(1 for rid in approved if by_id.get(rid) and by_id[rid]["accepted"])
    execution = {
        "records_approved": len(approved),
        "records_attempted": attempted,
        "records_accepted": accepted_records,
        "records_not_attempted": len(approved) - attempted,
        "provider_calls": summary["calls"],
        "schema_retries": sum(1 for a in attempts if (a.get("retry_number") or 0) > 0),
        "final_outcomes": dict(sorted(outcomes.items())),
        "attempt_outcomes": {
            o: sum(1 for a in attempts if a["outcome"] == o)
            for o in sorted({a["outcome"] for a in attempts})
        },
        "http_statuses": {
            str(s): sum(1 for t in transports if t.get("status") == s)
            for s in sorted({t.get("status") for t in transports}, key=str)
        },
        "bounded_stop": summary["stopped"],
        "run_elapsed_seconds": summary["elapsed_seconds"],
        "call_latency_seconds": {
            "total": round(sum(latencies), 3),
            "median": statistics.median(latencies) if latencies else None,
            "p95_nearest_rank": nearest_rank(latencies, 95),
            "max": max(latencies) if latencies else None,
        },
        "input_tokens_reported": sum(u["input_tokens"] for u in usage),
        "output_tokens_reported": sum(u["output_tokens"] for u in usage),
        "calls_without_reported_usage": len(transports) - len(usage),
        "cost_usd": str(spent),
        "accepted_hard_ceiling_usd": str(ceiling),
        "ceiling_consumed_percent": str((spent / ceiling * 100).quantize(Decimal("0.01"))),
        "cost_within_ceiling": spent <= ceiling,
        "canonical_writes": summary["canonical_writes"],
    }

    # -- per label --
    labels: dict[str, Any] = {}
    readings: list[dict[str, Any]] = []
    for label in EXTRACTABLE:
        cells = {
            rid: (ref[rid][label]["state"], model_call(by_id.get(rid), label)) for rid in approved
        }
        count = lambda h, m, cells=cells: sum(  # noqa: E731
            1 for hh, mm in cells.values() if hh == h and mm == m
        )
        ref_counts = {
            s: sum(1 for h, _ in cells.values() if h == s)
            for s in ("PRESENT", "ABSENT", "UNCERTAIN")
        }
        model_counts = {
            s: sum(1 for _, m in cells.values() if m == s)
            for s in ("PRESENT", "ABSENT", "ABSTAIN", "NO_VALID_OUTPUT", "NOT_ATTEMPTED")
        }
        tp, fp = count("PRESENT", "PRESENT"), count("ABSENT", "PRESENT")
        fn, tn = count("PRESENT", "ABSENT"), count("ABSENT", "ABSENT")
        n_present_decided = tp + fp
        # false PRESENT rate among PRESENT calls on records the human decided
        need = required[label]
        upper = clopper_pearson_upper(fp, n_present_decided) if n_present_decided else None
        bound = proposed[f"false_present_rate_upper_95::{label}"]
        if n_present_decided < need:
            fp_reading = INSUFFICIENT
        else:
            fp_reading = WITHIN if upper is not None and upper <= bound else OUTSIDE
        readings.append(
            {
                "item_id": f"false_present_rate_upper_95::{label}",
                "reading": fp_reading,
                "proposed_bound": bound,
                "support": {
                    "present_calls_on_decided_records": n_present_decided,
                    "required": need,
                },
                "false_present": fp,
                "point_estimate": round(fp / n_present_decided, 6) if n_present_decided else None,
                "clopper_pearson_upper_95_one_sided": upper if n_present_decided >= need else None,
                "clopper_pearson_upper_95_descriptive": upper,
            }
        )
        if ref_counts["PRESENT"] == 0 or ref_counts["ABSENT"] == 0:
            mt_reading = INSUFFICIENT
        else:
            mt_reading = WITHIN if tp >= 1 and tn >= 1 else OUTSIDE
        readings.append(
            {
                "item_id": f"min_true_present_and_min_true_absent::{label}",
                "reading": mt_reading,
                "proposed_bound": 1,
                "true_present": tp,
                "true_absent": tn,
            }
        )
        composition_met = ref_counts["PRESENT"] >= 4 and ref_counts["ABSENT"] >= 4
        readings.append(
            {
                "item_id": f"composition_gate::{label}, DEVELOPMENT",
                "reading": WITHIN if composition_met else INSUFFICIENT,
                "proposed_bound": {"min_present": 4, "min_absent": 4},
                "reference_present": ref_counts["PRESENT"],
                "reference_absent": ref_counts["ABSENT"],
                "reference_set_insufficient": not composition_met,
            }
        )
        recall = round(tp / ref_counts["PRESENT"], 6) if ref_counts["PRESENT"] else None
        readings.append(
            {
                "item_id": f"recall::{label}",
                "reading": INSUFFICIENT if ref_counts["PRESENT"] == 0 else None,
                "proposed_bound": None,
                "descriptive_only": True,
                "recall": recall,
                "recall_state": "UNDEFINED_NO_REFERENCE_PRESENT" if recall is None else "DEFINED",
                "true_present": tp,
                "reference_present": ref_counts["PRESENT"],
            }
        )
        decided_valid = [
            (h, m)
            for h, m in cells.values()
            if h in DECIDED and m in ("PRESENT", "ABSENT", "ABSTAIN")
        ]
        labels[label] = {
            "reference": ref_counts,
            "model": model_counts,
            "confusion": {
                f"reference_{h}__model_{m}": count(h, m)
                for h in ("PRESENT", "ABSENT", "UNCERTAIN")
                for m in ("PRESENT", "ABSENT", "ABSTAIN", "NO_VALID_OUTPUT", "NOT_ATTEMPTED")
            },
            "true_present": tp,
            "false_present": fp,
            "missed_reference_present": fn
            + count("PRESENT", "ABSTAIN")
            + count("PRESENT", "NO_VALID_OUTPUT")
            + count("PRESENT", "NOT_ATTEMPTED"),
            "true_absent": tn,
            "recall": recall,
            "false_present_point_estimate": round(fp / n_present_decided, 6)
            if n_present_decided
            else None,
            "abstention_on_decided_cells": {
                "abstained": sum(1 for _, m in decided_valid if m == "ABSTAIN"),
                "decided_cells_with_valid_output": len(decided_valid),
            },
            "disagreements": {
                "model_PRESENT_reference_ABSENT": sorted(
                    r for r, (h, m) in cells.items() if h == "ABSENT" and m == "PRESENT"
                ),
                "model_ABSENT_reference_PRESENT": sorted(
                    r for r, (h, m) in cells.items() if h == "PRESENT" and m == "ABSENT"
                ),
                "model_ABSTAIN_reference_decided": sorted(
                    r for r, (h, m) in cells.items() if h in DECIDED and m == "ABSTAIN"
                ),
                "reference_UNCERTAIN": sorted(
                    f"{r} (model {m})" for r, (h, m) in cells.items() if h == "UNCERTAIN"
                ),
            },
        }

    # -- all-label items --
    accepted_findings = [
        f
        for r in summary["records"]
        if r["accepted"] and r["extraction"]
        for f in r["extraction"]["findings"]
    ]
    unsupported = sum(
        1
        for f in accepted_findings
        if not f["evidence_span_matches_a_returned_quote"]
        or f["subject_span_matches_a_returned_quote"] is False
    )
    readings.append(
        {
            "item_id": "mechanical_unsupported_assertions_accepted::all",
            "reading": INSUFFICIENT
            if accepted_records == 0
            else (WITHIN if unsupported == 0 else OUTSIDE),
            "proposed_bound": 0,
            "accepted_findings_checked": len(accepted_findings),
            "unsupported_accepted": unsupported,
        }
    )
    rate = round(accepted_records / attempted, 6) if attempted else None
    readings.append(
        {
            "item_id": "validator_acceptance_rate::all",
            "reading": INSUFFICIENT
            if attempted < MIN_ATTEMPTED_FOR_ACCEPTANCE
            else (WITHIN if rate is not None and rate >= 0.95 else OUTSIDE),
            "proposed_bound": 0.95,
            "accepted": accepted_records,
            "attempted": attempted,
            "rate": rate,
        }
    )
    abstained = sum(
        labels[label]["abstention_on_decided_cells"]["abstained"] for label in EXTRACTABLE
    )
    cells_total = sum(
        labels[label]["abstention_on_decided_cells"]["decided_cells_with_valid_output"]
        for label in EXTRACTABLE
    )
    abstention_rate = round(abstained / cells_total, 6) if cells_total else None
    readings.append(
        {
            "item_id": "unnecessary_abstention_rate_on_gold_decided::all",
            "reading": INSUFFICIENT
            if cells_total < MIN_DECIDED_CELLS_FOR_ABSTENTION
            else (WITHIN if abstention_rate is not None and abstention_rate <= 0.10 else OUTSIDE),
            "proposed_bound": 0.10,
            "gold_reads": "the single-human decided reference, as preregistered",
            "abstained_cells": abstained,
            "decided_cells_with_valid_output": cells_total,
            "rate": abstention_rate,
        }
    )
    readings.append(
        {
            "item_id": "cost_and_latency::all",
            "reading": None,
            "proposed_bound": None,
            "descriptive_only": True,
            "cost_usd": execution["cost_usd"],
            "ceiling_consumed_percent": execution["ceiling_consumed_percent"],
            "call_latency_seconds": execution["call_latency_seconds"],
        }
    )
    refusal_codes: dict[str, int] = {}
    for r in summary["records"]:
        for code in r["refusal_codes"]:
            refusal_codes[code] = refusal_codes.get(code, 0) + 1
    record_failures = {
        "validator_refused": sorted(
            r["normalized_record_id"]
            for r in summary["records"]
            if final_outcome(r) == "VALIDATOR_REFUSED"
        ),
        "schema_failure": sorted(
            r["normalized_record_id"]
            for r in summary["records"]
            if final_outcome(r) == "SCHEMA_FAILURE"
        ),
        "provider_error": sorted(
            r["normalized_record_id"]
            for r in summary["records"]
            if final_outcome(r) == "PROVIDER_ERROR"
        ),
        "output_limit_reached": sorted(
            r["normalized_record_id"]
            for r in summary["records"]
            if final_outcome(r) == "OUTPUT_LIMIT_REACHED"
        ),
        "model_refused": sorted(
            r["normalized_record_id"]
            for r in summary["records"]
            if final_outcome(r) == "MODEL_REFUSED"
        ),
        "unexpected_error": sorted(
            r["normalized_record_id"]
            for r in summary["records"]
            if final_outcome(r) == "UNEXPECTED_ERROR"
        ),
        "not_attempted": sorted(
            rid for rid in approved if not by_id.get(rid) or not by_id[rid]["attempts"]
        ),
    }
    flip = next(d for d in decisions["A_pilot_thresholds"] if d["item_id"].startswith("run_to_run"))
    return {
        "$comment": "DEVELOPMENT PILOT EVALUATION (Mission 1.85.9). PILOT_NOT_CERTIFICATION. Against a SINGLE_HUMAN_REFERENCE, which is the pilot reference and not absolute truth. Rendered from committed artifacts; evaluation artifact only, never a Signal, Claim, Evidence or production finding.",
        "evaluation_id": "semantic-extraction-pilot-evaluation-development",
        "evaluator": f"{EVALUATOR_ID}@{EVALUATOR_VERSION}",
        "REFERENCE_STRENGTH": packet["reference"]["REFERENCE_STRENGTH"],
        "RESULT_SCOPE": packet["reference"]["RESULT_SCOPE"],
        "result_label": packet["reference"]["result_label"],
        "prohibited_claims": packet["reference"]["prohibited_claims"],
        "inputs": {
            "packet_sha256": packet["packet_sha256"],
            "run_summary_sha256": sha(SUMMARY.read_bytes()),
            "reference_sha256": sha(REFERENCE.read_bytes()),
            "decisions_sha256": sha(DECISIONS.read_bytes()),
        },
        "summary_names_this_packet": summary["packet_sha256"] == packet["packet_sha256"],
        "run_execution": execution,
        "readings": readings,
        "not_evaluated": [
            {
                "item_id": flip["item_id"],
                "operator_decision": flip["operator_decision"],
                "repeatability_disposition": flip["repeatability_disposition"],
                "why": "rejected for this first pilot; no additional model run is authorised",
            }
        ],
        "authorised_items_read": sorted(authorised),
        "labels": labels,
        "validator": {
            "acceptance_rate": rate,
            "unsupported_accepted": unsupported,
            "refusal_codes": dict(sorted(refusal_codes.items())),
        },
        "record_failures": record_failures,
    }


def page(evaluation: dict[str, Any]) -> bytes:
    e = evaluation["run_execution"]
    lines = [
        "# Semantic extraction DEVELOPMENT pilot evaluation (v1)",
        "",
        "> Generated by `infrastructure/scripts/evaluate_semantic_extraction_pilot.py` from committed artifacts. Do not edit by hand.",
        "",
        f"`{evaluation['REFERENCE_STRENGTH']}` / `{evaluation['RESULT_SCOPE']}` / `{evaluation['result_label']}`. The single-human reference is the pilot reference, not absolute truth. Packet `{evaluation['inputs']['packet_sha256']}`.",
        "",
        "## Run",
        "",
        "| Fact | Value |",
        "|---|---|",
        f"| Records approved / attempted / accepted | {e['records_approved']} / {e['records_attempted']} / {e['records_accepted']} |",
        f"| Provider calls / schema retries | {e['provider_calls']} / {e['schema_retries']} |",
        f"| Final outcomes | {json.dumps(e['final_outcomes'])} |",
        f"| Bounded stop | {e['bounded_stop']} |",
        f"| Tokens in / out | {e['input_tokens_reported']} / {e['output_tokens_reported']} |",
        f"| Cost | ${e['cost_usd']} of ${e['accepted_hard_ceiling_usd']} ({e['ceiling_consumed_percent']}%) |",
        f"| Call latency total / median / p95 / max (s) | {e['call_latency_seconds']['total']} / {e['call_latency_seconds']['median']} / {e['call_latency_seconds']['p95_nearest_rank']} / {e['call_latency_seconds']['max']} |",
        "",
        "## Readings",
        "",
        "| Item | Reading |",
        "|---|---|",
    ]
    for r in evaluation["readings"]:
        lines.append(f"| `{r['item_id']}` | {r['reading'] or 'descriptive, no bound'} |")
    for n in evaluation["not_evaluated"]:
        lines.append(
            f"| `{n['item_id']}` | not evaluated: {n['operator_decision']}, {n['repeatability_disposition']} |"
        )
    for label, data in evaluation["labels"].items():
        lines += [
            "",
            f"## {label}",
            "",
            f"Reference {json.dumps(data['reference'])}; model {json.dumps(data['model'])}.",
            "",
            f"True PRESENT {data['true_present']}, false PRESENT {data['false_present']}, missed reference PRESENT {data['missed_reference_present']}, true ABSENT {data['true_absent']}, recall {data['recall'] if data['recall'] is not None else 'undefined'}.",
            "",
        ]
        for kind, ids in data["disagreements"].items():
            lines.append(f"- {kind}: {len(ids)}" + (f" ({', '.join(ids)})" if ids else ""))
    lines += ["", "## Record failures", ""]
    for kind, ids in evaluation["record_failures"].items():
        lines.append(f"- {kind}: {len(ids)}" + (f" ({', '.join(ids)})" if ids else ""))
    lines += [
        "",
        f"Validator refusal codes: {json.dumps(evaluation['validator']['refusal_codes'])}.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--summarise", metavar="RUN_FILE")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.summarise:
        sys.path.insert(0, str(ROOT / "infrastructure" / "scripts"))
        for path in (
            "packages/semantic-extraction-contract/python",
            "packages/contracts/python",
            "services/acquisition/python",
        ):
            sys.path.insert(0, str(ROOT / path))
        from build_semantic_egress_eligibility import development_surfaces

        SUMMARY.write_bytes(dump(summarise(pathlib.Path(args.summarise), development_surfaces())))
        print(f"wrote {SUMMARY.name}")
        return 0
    evaluation = evaluate()
    targets = {EVALUATION: dump(evaluation), PAGE: page(evaluation)}
    if args.write:
        for path, content in targets.items():
            path.write_bytes(content)
        print(f"wrote {EVALUATION.name} and {PAGE.name}")
        return 0
    stale = [p.name for p, c in targets.items() if not p.exists() or p.read_bytes() != c]
    for name in stale:
        print(f"FAIL     {name} is stale")
    if not stale:
        print(f"ok       {EVALUATION.name} matches")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
