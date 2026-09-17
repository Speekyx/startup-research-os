"""Mission 1.85.9. The DEVELOPMENT pilot evaluator, exercised on synthetic runs before the real one exists.

No provider, no database. A synthetic run record goes through `summarise` with in-memory surfaces, and a
synthetic summary over the real 46 approved ids goes through `evaluate`. Nothing is written to the
repository: the evaluator's output paths are redirected to a temporary directory.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest
from sros_semantic_extraction_contract import render_question_surface, surface_sha256

REPO = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "infrastructure" / "scripts"
DATA = REPO / "docs" / "data"


def load_evaluator():
    spec = importlib.util.spec_from_file_location(
        "pilot_evaluator", SCRIPTS / "evaluate_semantic_extraction_pilot.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PACKET = json.loads(
    (DATA / "semantic-extraction-evaluation-packet-development-v1.json").read_text("utf-8")
)
REFERENCE = json.loads(
    (DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json").read_text("utf-8")
)


def synthetic_summary(policy) -> dict:
    """policy(record_id, reference_labels) -> (outcome, extraction or None)."""
    ref = {r["normalized_record_id"]: r["labels"] for r in REFERENCE["records"]}
    records = []
    for call, rid in enumerate(PACKET["selection"]["egress_approved_record_ids"], start=1):
        outcome, extraction = policy(rid, ref[rid])
        records.append(
            {
                "normalized_record_id": rid,
                "surface_sha256": "0" * 64,
                "attempts": [
                    {
                        "call_number": call,
                        "retry_number": 0,
                        "outcome": outcome,
                        "error": None,
                        "transport": [
                            {
                                "status": 200,
                                "stop_reason": "tool_use",
                                "usage": {"input_tokens": 1000, "output_tokens": 100},
                                "elapsed_seconds": float(call),
                            }
                        ],
                    }
                ],
                "accepted": outcome == "ACCEPTED",
                "refusal_codes": ["QUOTE_NOT_IN_SURFACE"] if outcome == "VALIDATOR_REFUSED" else [],
                "extraction": extraction,
            }
        )
    return {
        "packet_sha256": PACKET["packet_sha256"],
        "calls": len(records),
        "stopped": None,
        "elapsed_seconds": 100.0,
        "canonical_writes": 0,
        "cost": {
            "accepted_hard_ceiling_usd": "9.000000",
            "spent_usd": "0.500000",
            "charges": [],
        },
        "records": records,
    }


def findings(*types: str) -> dict:
    return {
        "extraction_id": "x",
        "extraction_state": "FINDINGS_PRESENT" if types else "NO_FINDING_ESTABLISHED",
        "findings": [
            {
                "finding_id": t,
                "finding_type": t,
                "evidence_start": 0,
                "evidence_end": 10,
                "subject_start": None,
                "subject_end": None,
                "evidence_sha256": "0" * 64,
                "evidence_span_matches_a_returned_quote": True,
                "subject_span_matches_a_returned_quote": None,
            }
            for t in types
        ],
    }


@pytest.fixture
def evaluator(tmp_path, monkeypatch):
    module = load_evaluator()
    monkeypatch.setattr(module, "SUMMARY", tmp_path / "summary.json")
    monkeypatch.setattr(module, "EVALUATION", tmp_path / "evaluation.json")
    monkeypatch.setattr(module, "PAGE", tmp_path / "evaluation.md")
    return module


def readings(evaluation: dict) -> dict[str, str | None]:
    return {r["item_id"]: r["reading"] for r in evaluation["readings"]}


def test_clopper_pearson_upper_bound_matches_the_rule_of_three() -> None:
    module = load_evaluator()
    assert module.clopper_pearson_upper(0, 30) == pytest.approx(0.0950, abs=1e-3)
    assert module.clopper_pearson_upper(0, 15) == pytest.approx(0.1810, abs=1e-3)
    assert module.clopper_pearson_upper(5, 5) == 1.0
    assert module.clopper_pearson_upper(1, 20) == pytest.approx(0.2161, abs=1e-3)


def test_a_reference_mirroring_run_reads_as_expected(evaluator) -> None:
    def mirror(rid, labels):
        present = [label for label in evaluator.EXTRACTABLE if labels[label]["state"] == "PRESENT"]
        return "ACCEPTED", findings(*present)

    evaluator.SUMMARY.write_text(json.dumps(synthetic_summary(mirror)), encoding="utf-8")
    evaluation = evaluator.evaluate()
    got = readings(evaluation)
    rfa, neg = "REPORTED_FAILED_ATTEMPT", "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION"
    # 15 PRESENT calls, 0 false: upper bound 0.181 > 0.2? no, 0.181 <= 0.2
    assert got[f"false_present_rate_upper_95::{rfa}"] == evaluator.WITHIN
    assert got[f"false_present_rate_upper_95::{neg}"] == evaluator.INSUFFICIENT
    assert got[f"min_true_present_and_min_true_absent::{rfa}"] == evaluator.WITHIN
    assert got[f"min_true_present_and_min_true_absent::{neg}"] == evaluator.INSUFFICIENT
    assert got[f"composition_gate::{rfa}, DEVELOPMENT"] == evaluator.WITHIN
    assert got[f"composition_gate::{neg}, DEVELOPMENT"] == evaluator.INSUFFICIENT
    assert got[f"recall::{rfa}"] is None
    assert got[f"recall::{neg}"] == evaluator.INSUFFICIENT
    assert evaluation["labels"][rfa]["recall"] == 1.0
    assert evaluation["labels"][neg]["recall"] is None
    assert got["validator_acceptance_rate::all"] == evaluator.WITHIN
    assert got["mechanical_unsupported_assertions_accepted::all"] == evaluator.WITHIN
    assert got["unnecessary_abstention_rate_on_gold_decided::all"] == evaluator.WITHIN
    assert got["cost_and_latency::all"] is None
    assert not any("run_to_run" in item for item in got)
    assert evaluation["run_execution"]["ceiling_consumed_percent"] == "5.56"
    assert evaluation["run_execution"]["cost_within_ceiling"] is True


def test_constant_and_failing_runs_are_not_read_as_within(evaluator) -> None:
    def all_present(rid, labels):
        return "ACCEPTED", findings(*evaluator.EXTRACTABLE)

    evaluator.SUMMARY.write_text(json.dumps(synthetic_summary(all_present)), encoding="utf-8")
    got = readings(evaluator.evaluate())
    assert got["false_present_rate_upper_95::REPORTED_FAILED_ATTEMPT"] == evaluator.OUTSIDE
    assert got["min_true_present_and_min_true_absent::REPORTED_FAILED_ATTEMPT"] == evaluator.OUTSIDE

    def abstain(rid, labels):
        return "ACCEPTED", {
            "extraction_id": "x",
            "extraction_state": "ABSTAINED_TEXT_INSUFFICIENT",
            "findings": [],
        }

    evaluator.SUMMARY.write_text(json.dumps(synthetic_summary(abstain)), encoding="utf-8")
    got = readings(evaluator.evaluate())
    assert got["unnecessary_abstention_rate_on_gold_decided::all"] == evaluator.OUTSIDE
    assert got["false_present_rate_upper_95::REPORTED_FAILED_ATTEMPT"] == evaluator.INSUFFICIENT

    def refused(rid, labels):
        return "VALIDATOR_REFUSED", None

    evaluator.SUMMARY.write_text(json.dumps(synthetic_summary(refused)), encoding="utf-8")
    evaluation = evaluator.evaluate()
    got = readings(evaluation)
    assert got["validator_acceptance_rate::all"] == evaluator.OUTSIDE
    assert got["mechanical_unsupported_assertions_accepted::all"] == evaluator.INSUFFICIENT
    assert len(evaluation["record_failures"]["validator_refused"]) == 46
    assert evaluation["validator"]["refusal_codes"] == {"QUOTE_NOT_IN_SURFACE": 46}


def test_summarise_removes_source_text_and_checks_spans(tmp_path) -> None:
    module = load_evaluator()
    surface = render_question_surface(
        "Title", "<p>I tried reinstalling the package but it fails.</p>"
    )
    quote = "I tried reinstalling the package but it fails."
    start = surface.index(quote)
    run = {
        "packet_sha256": PACKET["packet_sha256"],
        "calls": 1,
        "stopped": None,
        "cost": {"accepted_hard_ceiling_usd": "9.000000", "spent_usd": "0.01", "charges": []},
        "records": [
            {
                "normalized_record_id": "r-1",
                "surface_sha256": surface_sha256(surface),
                "attempts": [
                    {
                        "call_number": 1,
                        "retry_number": 0,
                        "outcome": "ACCEPTED",
                        "error": None,
                        "transport": [
                            {
                                "status": 200,
                                "request_id": "req_secret_ish",
                                "usage": {"input_tokens": 1, "output_tokens": 1},
                            }
                        ],
                    }
                ],
                "payload": {
                    "extraction_state": "FINDINGS_PRESENT",
                    "findings": [
                        {"finding_type": "REPORTED_FAILED_ATTEMPT", "evidence_quote": quote}
                    ],
                },
                "refusals": [],
                "accepted": True,
                "extraction": {
                    "extraction_id": "e",
                    "extraction_state": "FINDINGS_PRESENT",
                    "findings": [
                        {
                            "finding_id": "f",
                            "finding_type": "REPORTED_FAILED_ATTEMPT",
                            "evidence_start": start,
                            "evidence_end": start + len(quote),
                            "subject_start": None,
                            "subject_end": None,
                        }
                    ],
                },
            }
        ],
    }
    path = tmp_path / "run.json"
    path.write_text(json.dumps(run), encoding="utf-8")
    summary = module.summarise(path, {"r-1": surface})
    text = json.dumps(summary)
    assert quote not in text and "reinstalling" not in text
    assert "req_secret_ish" not in text
    finding = summary["records"][0]["extraction"]["findings"][0]
    assert finding["evidence_span_matches_a_returned_quote"] is True
