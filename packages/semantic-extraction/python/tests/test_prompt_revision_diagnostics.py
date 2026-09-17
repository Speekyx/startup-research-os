"""Mission 1.85.12. The prompt 1.1.0 diagnostics and the packet v5 evaluation, exercised on synthetic runs before
the real run exists.

No provider, no database. A synthetic v2 run summary over the real 46 approved ids is written to a temporary
directory; the committed Mission 1.85.9 summary is the prompt 1.0.0 side. Nothing is written to the repository.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "infrastructure" / "scripts"
DATA = REPO / "docs" / "data"
RFA = "REPORTED_FAILED_ATTEMPT"
NEG = "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION"
V5 = json.loads(
    (DATA / "semantic-extraction-evaluation-packet-development-v2.json").read_text("utf-8")
)
REFERENCE = json.loads(
    (DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json").read_text("utf-8")
)


def load_modules():
    sys.path.insert(0, str(SCRIPTS))
    modules = []
    for name in ("evaluate_semantic_extraction_pilot", "evaluate_prompt_revision_diagnostics"):
        sys.modules.pop(name, None)
        spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        modules.append(module)
    return modules


def synthetic_v2_summary(policy) -> dict:
    """policy(reference_state) -> model call for REPORTED_FAILED_ATTEMPT; NEG is always ABSENT."""
    ref = {r["normalized_record_id"]: r["labels"] for r in REFERENCE["records"]}
    records = []
    for number, rid in enumerate(V5["selection"]["egress_approved_record_ids"], start=1):
        rfa = policy(ref[rid][RFA]["state"])
        findings = (
            [
                {
                    "finding_id": f"f{number}",
                    "finding_type": RFA,
                    "evidence_start": 0,
                    "evidence_end": 10,
                    "subject_start": None,
                    "subject_end": None,
                    "evidence_sha256": "0" * 64,
                    "evidence_span_matches_a_returned_quote": True,
                    "subject_span_matches_a_returned_quote": None,
                }
            ]
            if rfa == "PRESENT"
            else []
        )
        state = {
            "PRESENT": "FINDINGS_PRESENT",
            "ABSENT": "NO_FINDING_ESTABLISHED",
            "ABSTAIN": "ABSTAINED_TEXT_INSUFFICIENT",
        }[rfa]
        records.append(
            {
                "normalized_record_id": rid,
                "surface_sha256": "0" * 64,
                "attempts": [
                    {
                        "call_number": number,
                        "retry_number": 0,
                        "outcome": "ACCEPTED",
                        "error": None,
                        "transport": [
                            {
                                "status": 200,
                                "stop_reason": "tool_use",
                                "usage": {"input_tokens": 3000, "output_tokens": 150},
                                "elapsed_seconds": 3.0,
                            }
                        ],
                    }
                ],
                "accepted": True,
                "refusal_codes": [],
                "extraction": {
                    "extraction_id": f"e{number}",
                    "extraction_state": state,
                    "findings": findings,
                },
            }
        )
    return {
        "packet_sha256": V5["packet_sha256"],
        "calls": len(records),
        "stopped": None,
        "elapsed_seconds": 150.0,
        "canonical_writes": 0,
        "cost": {
            "accepted_hard_ceiling_usd": "9.000000",
            "spent_usd": "0.400000",
            "charges": [],
        },
        "records": records,
    }


def run_with(tmp_path, monkeypatch, policy):
    evaluator, diagnostics = load_modules()
    summary = tmp_path / "run-v2.json"
    summary.write_text(json.dumps(synthetic_v2_summary(policy)), encoding="utf-8")
    attempt = tmp_path / "attempt-v2.json"
    attempt.write_text("{}", encoding="utf-8")
    v2 = dataclasses.replace(
        evaluator.V2,
        summary=summary,
        attempt=attempt,
        evaluation=tmp_path / "evaluation-v2.json",
        page=tmp_path / "evaluation-v2.md",
    )
    monkeypatch.setattr(evaluator, "V2", v2)
    monkeypatch.setattr(diagnostics.pilot_evaluator, "V2", v2)
    return evaluator, diagnostics, diagnostics.build()


def mirror(state: str) -> str:
    return "PRESENT" if state == "PRESENT" else "ABSENT"


def test_a_reference_mirroring_prompt_corrects_every_overread_and_keeps_every_positive(
    tmp_path, monkeypatch
) -> None:
    evaluator, _, doc = run_with(tmp_path, monkeypatch, mirror)
    a, b, c = (
        doc["A_known_overread"],
        doc["B_positive_sensitivity"],
        doc["C_valid_overlap_comparison"],
    )
    assert (a["prior_overreads"], a["corrected_rfa_absent"], a["persistent_rfa_present"]) == (
        9,
        9,
        0,
    )
    assert all(r["prompt_1_0_0_call"] == "PRESENT" for r in a["records"])
    assert (
        b["reference_positives"],
        b["true_present_retained"],
        b["missed_present_as_absent"],
    ) == (
        15,
        15,
        0,
    )
    # The overlap is the 23 records the partial Mission 1.85.9 run accepted, never 46 against 46.
    assert c["overlap_records"] == 23 and c["prompt_1_0_0_run_records_accepted"] == 23
    assert c["is_independent_test_set"] is False
    before, after = c["labels"][RFA]["prompt_1_0_0"], c["labels"][RFA]["prompt_1_1_0"]
    # Recomputed from the committed Mission 1.85.9 summary, not hardcoded in the script.
    assert (
        before["model_present_on_decided_records"],
        before["reference"]["PRESENT"],
        before["false_present"],
        before["true_present"],
        before["reference_present_recovered"],
    ) == (18, 9, 9, 9, "9/9")
    assert (after["false_present"], after["true_present"]) == (0, 9)
    assert c["labels"][RFA]["delta"]["false_present"] == -9
    assert c["labels"][RFA]["changed_classifications"]["PRESENT_to_ABSENT"] == 9
    assert doc["mission_1_85_9_reading_unchanged"] == "PILOT_OUTSIDE_PROPOSED_BOUND"
    evaluation = evaluator.evaluate(evaluator.V2)
    reading = {r["item_id"]: r for r in evaluation["readings"]}
    fp_reading = reading[f"false_present_rate_upper_95::{RFA}"]
    assert fp_reading["support"] == {"present_calls_on_decided_records": 15, "required": 15}
    assert (fp_reading["false_present"], fp_reading["reading"]) == (
        0,
        "PILOT_WITHIN_PROPOSED_BOUND",
    )


def test_a_prompt_that_buys_precision_by_answering_absent_is_visible(tmp_path, monkeypatch) -> None:
    _, _, doc = run_with(tmp_path, monkeypatch, lambda state: "ABSENT")
    b = doc["B_positive_sensitivity"]
    assert (b["true_present_retained"], b["missed_present_as_absent"]) == (0, 15)
    assert b["descriptive_recall_over_all_positives"] == 0.0
    rfa = doc["C_valid_overlap_comparison"]["labels"][RFA]
    assert rfa["prompt_1_1_0"]["precision"] is None
    assert rfa["delta"]["recall_on_reference_present"] == -1.0


def test_the_diagnostics_carry_ids_and_counts_only(tmp_path, monkeypatch) -> None:
    _, diagnostics, doc = run_with(tmp_path, monkeypatch, mirror)
    text = diagnostics.pilot_evaluator.dump(doc).decode("utf-8")
    assert "evidence_quote" not in text and "surface" not in text.replace("surface_sha256", "")
    assert doc["A_known_overread"]["is_threshold"] is False
    assert doc["B_positive_sensitivity"]["is_certification"] is False
    assert diagnostics.page(doc).startswith(b"# Prompt 1.1.0 DEVELOPMENT diagnostics")


def test_the_v1_evaluation_still_reproduces_byte_for_byte() -> None:
    evaluator, _ = load_modules()
    evaluation = evaluator.evaluate()
    assert evaluator.dump(evaluation) == evaluator.V1.evaluation.read_bytes()
    assert evaluator.page(evaluation) == evaluator.V1.page.read_bytes()
