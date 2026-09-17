"""Mission 1.85.9. The one approved DEVELOPMENT pilot run, checked from its committed artifacts.

These tests never reach a provider. They read the committed approval, attempt record, run summary and
evaluation, and they prove that the approval cannot be used again: a second `--execute` is refused before
the credential or any transport, with tripwires on both.
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
APPROVED_PACKET = "5f96b418e75374b098b44b7fe3ba756a5155af94f92cd607ea251fa131d18c0e"


def load(name: str):
    return json.loads((DATA / name).read_text("utf-8"))


def load_script(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(f"artifacts_{name}", SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


APPROVAL_PATH = DATA / "semantic-extraction-evaluation-approval-development-v1.json"
APPROVAL = load("semantic-extraction-evaluation-approval-development-v1.json")
APPROVAL_SHA = hashlib.sha256(APPROVAL_PATH.read_bytes()).hexdigest()
ATTEMPT = load("semantic-extraction-evaluation-attempt-development-v1.json")
SUMMARY = load("semantic-extraction-pilot-run-development-v1.json")
EVALUATION = load("semantic-extraction-pilot-evaluation-development-v1.json")
PACKET = load("semantic-extraction-evaluation-packet-development-v1.json")
CORPUS = load("stack-overflow-semantic-evaluation-corpus-v1.json")


def test_the_approval_names_exactly_the_approved_packet_and_one_execution() -> None:
    assert APPROVAL["packet_sha256"] == APPROVED_PACKET == PACKET["packet_sha256"]
    assert APPROVAL["packet_version"] == 4
    assert APPROVAL["approval_scope"] == "ONE_DEVELOPMENT_PILOT_EXECUTION"
    assert APPROVAL["decision"] == "APPROVE_EXACTLY_ONE_EVALUATION_RUN"
    assert (APPROVAL["approved_provider"], APPROVAL["approved_model"]) == (
        "anthropic",
        "claude-sonnet-5",
    )
    assert APPROVAL["approved_record_count"] == 46
    assert APPROVAL["accepted_hard_ceiling_usd"] == "9.000000"
    assert APPROVAL["approved_by"] == "operator-a"
    assert "exactly one DEVELOPMENT pilot execution" in APPROVAL["operator_statement"]
    assert list(DATA.glob("semantic-extraction-evaluation-approval*")) == [APPROVAL_PATH]


def test_the_attempt_and_the_summary_name_this_packet_and_this_approval() -> None:
    assert ATTEMPT["state"] == "ATTEMPT_STARTED"
    assert ATTEMPT["packet_sha256"] == SUMMARY["packet_sha256"] == APPROVED_PACKET
    assert ATTEMPT["approval_sha256"] == SUMMARY["approval_sha256"] == APPROVAL_SHA
    assert (SUMMARY["provider"], SUMMARY["model"]) == ("anthropic", "claude-sonnet-5")


def test_one_run_within_bounds_no_holdout_no_repeat_no_canonical_writes() -> None:
    assert SUMMARY["calls"] <= PACKET["execution_bounds"]["max_calls"]
    assert float(SUMMARY["cost"]["spent_usd"]) <= 9.0
    assert SUMMARY["canonical_writes"] == 0
    development = {
        r["normalized_record_id"] for r in CORPUS["records"] if r["split"] == "DEVELOPMENT"
    }
    holdout = {r["normalized_record_id"] for r in CORPUS["records"] if r["split"] != "DEVELOPMENT"}
    ids = [r["normalized_record_id"] for r in SUMMARY["records"]]
    assert len(ids) == len(set(ids)), "a record was attempted twice outside the retry rule"
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
    assert (
        EVALUATION["not_evaluated"][0]["repeatability_disposition"] == "REJECT_FOR_THIS_FIRST_PILOT"
    )


def test_no_source_text_or_request_id_is_committed() -> None:
    text = (DATA / "semantic-extraction-pilot-run-development-v1.json").read_text("utf-8")
    assert "evidence_quote" not in text and "subject_quote" not in text
    assert '"request_id"' not in text
    assert all("payload" not in record for record in SUMMARY["records"])


def test_the_evaluation_reproduces_from_the_committed_artifacts() -> None:
    evaluator = load_script("evaluate_semantic_extraction_pilot")
    assert evaluator.dump(evaluator.evaluate()) == evaluator.EVALUATION.read_bytes()
    assert evaluator.page(evaluator.evaluate()) == evaluator.PAGE.read_bytes()
    assert EVALUATION["summary_names_this_packet"] is True
    assert (EVALUATION["RESULT_SCOPE"], EVALUATION["result_label"]) == (
        "DEVELOPMENT_PILOT",
        "PILOT_NOT_CERTIFICATION",
    )
    vocabulary = {
        "PILOT_WITHIN_PROPOSED_BOUND",
        "PILOT_OUTSIDE_PROPOSED_BOUND",
        "PILOT_INSUFFICIENT_SUPPORT",
        None,
    }
    assert {r["reading"] for r in EVALUATION["readings"]} <= vocabulary


def test_a_second_execution_is_refused_before_the_key_or_any_transport(monkeypatch) -> None:
    from sros_llm_gateway import transport

    runner = load_script("run_semantic_extraction_evaluation")

    class KeyTripwire(dict):
        def get(self, key, default=None):
            assert key != "ANTHROPIC_API_KEY", "the runner read the API key"
            return super().get(key, default)

        def __getitem__(self, key):
            assert key != "ANTHROPIC_API_KEY", "the runner read the API key"
            return super().__getitem__(key)

    def no_transport(*args, **kwargs):
        raise AssertionError("a transport was built")

    def no_env(*args, **kwargs):
        raise AssertionError("the compose .env was loaded")

    monkeypatch.setattr(os, "environ", KeyTripwire(os.environ))
    monkeypatch.setattr(transport.UrllibTransport, "__init__", no_transport)
    monkeypatch.setattr(runner, "_load_compose_env", no_env)
    # Mission 1.85.11: the current packet is version 5 and has no approval file.
    with pytest.raises(runner.Refused) as refused:
        runner.main(
            ["--execute", "--approval-sha256", APPROVAL_SHA, "--output-dir", str(REPO.parent / "x")]
        )
    assert refused.value.refusal == "OPERATOR_APPROVAL_NOT_RECORDED"
    # Even pointed at the spent approval file, it names the old packet and unlocks nothing.
    monkeypatch.setattr(runner, "APPROVAL", APPROVAL_PATH)
    with pytest.raises(runner.Refused) as refused:
        runner.main(
            ["--execute", "--approval-sha256", APPROVAL_SHA, "--output-dir", str(REPO.parent / "x")]
        )
    assert refused.value.refusal == "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"
