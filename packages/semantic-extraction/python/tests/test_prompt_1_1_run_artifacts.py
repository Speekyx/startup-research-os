"""Mission 1.85.12. The one approved packet v5 (prompt 1.1.0) run, checked from its committed artifacts.

These tests never reach a provider. They read the committed approval, attempt record, run summary, evaluation
and diagnostics, and prove that the v5 approval cannot be used again: a second `--execute` is refused before
the credential, the compose .env or any transport, all tripwired.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO / "docs" / "data"
SCRIPTS = REPO / "infrastructure" / "scripts"
V5 = "6b27bccbc22c7051be9d8f1df4dd22a4635d0f664d4b4fa05ede820e90a72a7e"
V4 = "5f96b418e75374b098b44b7fe3ba756a5155af94f92cd607ea251fa131d18c0e"
APPROVAL_PATH = DATA / "semantic-extraction-evaluation-approval-development-v2.json"
APPROVAL_SHA = "9fc8fac724bdfa54a2967aaab668524f778ed476e6a1668a596efd6ac57c9974"


def load(name: str):
    return json.loads((DATA / name).read_text("utf-8"))


def load_script(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(f"v5_artifacts_{name}", SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


APPROVAL = load("semantic-extraction-evaluation-approval-development-v2.json")
ATTEMPT = load("semantic-extraction-evaluation-attempt-development-v2.json")
SUMMARY = load("semantic-extraction-pilot-run-development-v2.json")
EVALUATION = load("semantic-extraction-pilot-evaluation-development-v2.json")
DIAGNOSTICS = load("semantic-extraction-prompt-revision-diagnostics-development-v1.json")
PACKET = load("semantic-extraction-evaluation-packet-development-v2.json")
V1_SUMMARY = load("semantic-extraction-pilot-run-development-v1.json")
CORPUS = load("stack-overflow-semantic-evaluation-corpus-v1.json")


def test_the_approval_names_exactly_packet_v5_and_one_execution() -> None:
    assert hashlib.sha256(APPROVAL_PATH.read_bytes()).hexdigest() == APPROVAL_SHA
    assert APPROVAL["packet_sha256"] == V5 == PACKET["packet_sha256"]
    assert APPROVAL["packet_version"] == 5
    assert APPROVAL["approval_scope"] == "ONE_DEVELOPMENT_PILOT_EXECUTION"
    assert APPROVAL["decision"] == "APPROVE_EXACTLY_ONE_EVALUATION_RUN"
    assert (APPROVAL["approved_provider"], APPROVAL["approved_model"]) == (
        "anthropic",
        "claude-sonnet-5",
    )
    assert APPROVAL["approved_record_count"] == 46
    assert APPROVAL["accepted_hard_ceiling_usd"] == "9.000000"
    assert APPROVAL["approved_by"] == "operator-a"
    assert APPROVAL["approved_at"].endswith("+04:00")
    assert APPROVAL["repeatability_runs_authorised"] == 0
    assert APPROVAL["holdout_prohibited"] is True
    assert APPROVAL["production_persistence_prohibited"] is True
    assert APPROVAL["operator_statement"] == (
        f"This approval authorises exactly one full DEVELOPMENT evaluation execution of packet {V5} and no "
        "other packet, split, continuation, rerun, repeatability run, HOLDOUT run, or production persistence."
    )


def test_the_attempt_and_the_summary_name_packet_v5_and_its_approval() -> None:
    assert ATTEMPT["state"] == "ATTEMPT_STARTED"
    assert ATTEMPT["packet_sha256"] == SUMMARY["packet_sha256"] == V5
    assert ATTEMPT["approval_sha256"] == SUMMARY["approval_sha256"] == APPROVAL_SHA
    assert (SUMMARY["provider"], SUMMARY["model"]) == ("anthropic", "claude-sonnet-5")
    assert SUMMARY["packet_version"] == 5


def test_one_clean_full_run_within_bounds_no_holdout_no_repeat_no_canonical_writes() -> None:
    assert SUMMARY["calls"] <= PACKET["execution_bounds"]["max_calls"]
    assert float(SUMMARY["cost"]["spent_usd"]) <= 9.0
    assert SUMMARY["canonical_writes"] == 0
    development = {
        r["normalized_record_id"] for r in CORPUS["records"] if r["split"] == "DEVELOPMENT"
    }
    holdout = {r["normalized_record_id"] for r in CORPUS["records"] if r["split"] != "DEVELOPMENT"}
    ids = [r["normalized_record_id"] for r in SUMMARY["records"]]
    assert len(ids) == len(set(ids))
    assert set(ids) <= set(PACKET["selection"]["egress_approved_record_ids"]) <= development
    assert not set(ids) & holdout
    for record in SUMMARY["records"]:
        assert len(record["attempts"]) <= 2
        assert [a["retry_number"] for a in record["attempts"]] == list(
            range(len(record["attempts"]))
        )
    calls = [a["call_number"] for r in SUMMARY["records"] for a in r["attempts"]]
    assert calls == list(range(1, SUMMARY["calls"] + 1))
    assert not any("run_to_run" in r["item_id"] for r in EVALUATION["readings"])


def test_no_source_text_or_request_id_is_committed() -> None:
    for name in (
        "semantic-extraction-pilot-run-development-v2.json",
        "semantic-extraction-pilot-evaluation-development-v2.json",
        "semantic-extraction-prompt-revision-diagnostics-development-v1.json",
    ):
        text = (DATA / name).read_text("utf-8")
        assert "evidence_quote" not in text and "subject_quote" not in text
        assert '"request_id"' not in text
    assert all("payload" not in record for record in SUMMARY["records"])


def test_the_evaluation_and_the_diagnostics_reproduce_from_committed_artifacts() -> None:
    evaluator = load_script("evaluate_semantic_extraction_pilot")
    evaluation = evaluator.evaluate(evaluator.V2)
    assert evaluator.dump(evaluation) == evaluator.V2.evaluation.read_bytes()
    assert evaluator.page(evaluation, evaluator.V2) == evaluator.V2.page.read_bytes()
    v1 = evaluator.evaluate()
    assert evaluator.dump(v1) == evaluator.V1.evaluation.read_bytes()
    assert EVALUATION["summary_names_this_packet"] is True
    vocabulary = {
        "PILOT_WITHIN_PROPOSED_BOUND",
        "PILOT_OUTSIDE_PROPOSED_BOUND",
        "PILOT_INSUFFICIENT_SUPPORT",
        None,
    }
    assert {r["reading"] for r in EVALUATION["readings"]} <= vocabulary
    diagnostics = load_script("evaluate_prompt_revision_diagnostics")
    doc = diagnostics.build()
    assert diagnostics.pilot_evaluator.dump(doc) == diagnostics.OUTPUT.read_bytes()
    assert diagnostics.page(doc) == diagnostics.PAGE.read_bytes()
    assert DIAGNOSTICS["A_known_overread"]["diagnostic_type"] == (
        "POST_MODEL_DEVELOPMENT_REGRESSION_DIAGNOSTIC"
    )
    assert DIAGNOSTICS["A_known_overread"]["is_threshold"] is False
    assert DIAGNOSTICS["mission_1_85_9_reading_unchanged"] == "PILOT_OUTSIDE_PROPOSED_BOUND"


def test_the_prompt_comparison_uses_only_the_valid_overlap() -> None:
    def accepted(summary):
        return {
            r["normalized_record_id"]
            for r in summary["records"]
            if r["accepted"] and r["extraction"] is not None
        }

    comparison = DIAGNOSTICS["C_valid_overlap_comparison"]
    overlap = set(comparison["overlap_record_ids"])
    assert overlap == accepted(V1_SUMMARY) & accepted(SUMMARY)
    assert comparison["overlap_records"] == len(overlap) <= 23
    assert comparison["is_independent_test_set"] is False
    before = comparison["labels"]["REPORTED_FAILED_ATTEMPT"]["prompt_1_0_0"]
    assert before["records"] == len(overlap)
    assert (before["model_present_on_decided_records"], before["false_present"]) == (18, 9)


def test_a_second_execution_of_v5_is_refused_before_the_key_or_any_transport(monkeypatch) -> None:
    from sros_llm_gateway import transport

    runner = load_script("run_semantic_extraction_evaluation")

    class KeyTripwire(dict):
        def get(self, key, default=None):
            assert key != "ANTHROPIC_API_KEY", "the runner read the API key"
            return super().get(key, default)

        def __getitem__(self, key):
            assert key != "ANTHROPIC_API_KEY", "the runner read the API key"
            return super().__getitem__(key)

    def forbidden(*args, **kwargs):
        raise AssertionError("a transport was built or the compose .env was loaded")

    monkeypatch.setattr(os, "environ", KeyTripwire(os.environ))
    monkeypatch.setattr(transport.UrllibTransport, "__init__", forbidden)
    monkeypatch.setattr(runner, "_load_compose_env", forbidden)
    # Provider documentation ages; the spent-attempt refusal must not depend on its review interval.
    monkeypatch.setattr(runner, "check_provider_verification", lambda packet, today: None)
    with pytest.raises(runner.Refused) as refused:
        runner.main(
            ["--execute", "--approval-sha256", APPROVAL_SHA, "--output-dir", str(REPO.parent / "x")]
        )
    assert refused.value.refusal == "EVALUATION_APPROVAL_ALREADY_SPENT"
    # The spent v4 approval names another packet and unlocks nothing either.
    assert V4 != V5
    monkeypatch.setattr(runner, "APPROVAL", runner.HISTORICAL_APPROVAL)
    with pytest.raises(runner.Refused) as refused:
        runner.main(
            [
                "--execute",
                "--approval-sha256",
                hashlib.sha256(runner.HISTORICAL_APPROVAL.read_bytes()).hexdigest(),
                "--output-dir",
                str(REPO.parent / "x"),
            ]
        )
    assert refused.value.refusal == "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"
