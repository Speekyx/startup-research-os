"""Mission 1.84.18: CI gate 91 over the V6 execution record, and the refusals it must make.

Every mutation is made on a copy in a temporary directory, with the gate pointed at the copy, so the
committed record, approval and response are never touched. No test here builds a transport: the
runner is only asked whether it would refuse a digest.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
from collections.abc import Callable
from typing import Any

import pytest
from sros_opportunity.generation_headroom import headroom_table
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity_schema_v1_2 import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "infrastructure" / "scripts" / "render_second_opportunity_execution_record_v6.py"
V6 = "969128dd2453ab2a6907335d9386c9c3f3fac991db91c674b151c9db777aa8a9"
V5 = "da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a"
ROWS = headroom_table(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
EXTRA = "parameter name"


@pytest.fixture(scope="module")
def gate() -> Any:
    spec = importlib.util.spec_from_file_location("gate_91_under_test", GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def copies(gate: Any, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """The record, approval, response and V5's record, copied byte for byte; the gate reads these."""
    out = {}
    for name in ("RECORD", "APPROVAL", "RESPONSE"):
        source = getattr(gate, name)
        target = tmp_path / source.name
        target.write_bytes(source.read_bytes())
        monkeypatch.setattr(gate, name, target)
        out[name] = target
    history = dict(gate.HISTORY)
    v5 = next(
        p for p in history if p.name == "second-opportunity-synthesis-execution-record-v5.json"
    )
    target = tmp_path / v5.name
    target.write_bytes(v5.read_bytes())
    history[target] = history.pop(v5)
    monkeypatch.setattr(gate, "HISTORY", history)
    out["RECORD_V5"] = target
    monkeypatch.setattr(gate, "REVIEW_PACKET", tmp_path / gate.REVIEW_PACKET.name)
    return out


def _edit(path: pathlib.Path, change: Callable[[dict], None]) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    change(doc)
    path.write_bytes((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def _refused(gate: Any, match: str | None = None) -> None:
    with pytest.raises(gate.ValidationError, match=match):
        gate.validate()


def _retained(gate: Any) -> dict:
    return json.loads(gate.RESPONSE.read_text(encoding="utf-8"))["parsed_output"]


def _set_text(parsed: dict, path: str, text: str) -> None:
    field, marker, rest = path.partition("[]")
    child = rest.lstrip(".")
    if not marker:
        parsed[field] = text
    elif child:
        parsed[field][0][child] = text
    else:
        parsed[field][0] = text


def _names(violations: list[str], path: str) -> bool:
    field, marker, rest = path.partition("[]")
    child = rest.lstrip(".")
    return any(
        v.partition(":")[0].startswith(field) and (not child or child in v.partition(":")[0])
        for v in violations
    )


class TestTheCommittedRecord:
    def test_the_record_validates(self, gate):
        record = gate.validate()
        assert record["PRIMARY_OUTCOME"] == "EXECUTION_SCHEMA_REJECTED_NO_RETRY"
        assert record["FAILED_STAGE"] == "5_schema_validation_v1_2_0"
        assert record["SCHEMA_VIOLATIONS"] == [
            "<root>: unknown field 'parameter name'; additionalProperties is false"
        ]

    def test_the_page_is_the_rendering_of_the_record(self, gate):
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(gate.validate())

    def test_the_copies_validate_before_any_mutation(self, gate, copies):
        gate.validate()

    def test_the_summary_is_within_the_operators_bound_and_target(self, gate):
        summary = gate.validate()["REASONING_SUMMARY"]
        assert summary["within_target"] and summary["within_hard_maximum"]
        assert summary["v1_1_0_verdict_applies"] is False


class TestV6CannotExecuteTwice:
    @pytest.mark.parametrize("digest", [V6, V5])
    def test_the_runner_refuses_a_spent_digest_by_name(self, gate, digest):
        runner = gate._module(f"runner_v6_for_record_tests_{digest[:6]}", gate.RUNNER)
        with pytest.raises(runner.RefusedError) as refusal:
            runner.refuse_if_consumed(digest)
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"

    def test_an_unseen_digest_is_not_refused(self, gate):
        runner = gate._module("runner_v6_for_record_tests_unseen", gate.RUNNER)
        runner.refuse_if_consumed("ab" * 32)

    def test_the_approval_cannot_be_marked_unused(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("EXECUTION_APPROVAL_CONSUMED", False))
        _refused(gate)

    def test_further_calls_cannot_be_authorised(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("FURTHER_CALLS_AUTHORIZED_BY_V6", True))
        _refused(gate)

    def test_a_retry_cannot_be_recorded(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("retries", 1))
        _refused(gate)

    def test_a_second_request_cannot_be_recorded(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("actual_provider_requests", 2))
        _refused(gate)


class TestActualUsageIsNotTheWorstCase:
    def test_the_worst_case_cannot_stand_for_the_cost(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["ACTUAL_COST"].__setitem__("cost_units", 1.31706))
        _refused(gate)

    def test_usage_cannot_be_called_unestablished(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("ACTUAL_USAGE", "NOT_ESTABLISHED"))
        _refused(gate)

    def test_the_output_tokens_cannot_be_rounded(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["ACTUAL_USAGE"].__setitem__("output_tokens", 4000))
        _refused(gate)


class TestATargetIsNotABound:
    """The retained answer, one composed text at a time: over its target passes, over its bound fails."""

    @pytest.mark.parametrize("row", ROWS, ids=[row.path for row in ROWS])
    def test_an_exceeded_soft_target_is_not_a_schema_failure(self, gate, row):
        parsed = copy.deepcopy(_retained(gate))
        _set_text(parsed, row.path, "x" * (row.generation_target + 1))
        violations = list(schema_violations(parsed, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2))
        assert not _names(violations, row.path), violations

    @pytest.mark.parametrize("row", ROWS, ids=[row.path for row in ROWS])
    def test_the_hard_maximum_itself_is_not_a_schema_failure(self, gate, row):
        parsed = copy.deepcopy(_retained(gate))
        _set_text(parsed, row.path, "x" * row.hard_maximum)
        violations = list(schema_violations(parsed, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2))
        assert not _names(violations, row.path), violations

    @pytest.mark.parametrize("row", ROWS, ids=[row.path for row in ROWS])
    def test_an_exceeded_hard_maximum_is_a_schema_failure(self, gate, row):
        parsed = copy.deepcopy(_retained(gate))
        _set_text(parsed, row.path, "x" * (row.hard_maximum + 1))
        violations = list(schema_violations(parsed, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2))
        assert _names(violations, row.path), violations

    def test_the_retained_answer_has_a_text_over_target_the_schema_did_not_refuse(self, gate):
        record = gate.validate()
        soft = [
            d["field"]
            for d in record["GENERATION_TARGET_DIAGNOSTICS"]
            if not d["within_target"] and d["within_hard_maximum"]
        ]
        assert soft == ["target_actor_if_supported"]
        assert not any(_names(record["SCHEMA_VIOLATIONS"], field) for field in soft)

    def test_a_diagnostic_cannot_be_rewritten(self, gate, copies):
        def soften(doc: dict) -> None:
            for row in doc["GENERATION_TARGET_DIAGNOSTICS"]:
                row["within_target"] = True

        _edit(copies["RECORD"], soften)
        _refused(gate, "diagnostics")

    def test_the_targets_cannot_be_said_to_decide(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("GENERATION_TARGETS_ALTER_VERDICT", True))
        _refused(gate)

    def test_the_hard_verdict_cannot_be_said_passed(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("HARD_SCHEMA_VERDICT", "PASSED"))
        _refused(gate)

    def test_the_old_contract_cannot_be_recorded_as_a_verdict(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d["HISTORICAL_CONTRACT_DIAGNOSTIC"].__setitem__("IS_A_VERDICT", True),
        )
        _refused(gate, "v1.1.0")


class TestAFailedAnswerGetsNoReview:
    def test_no_review_packet_is_recorded(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("HUMAN_REVIEW_PACKET", "PRODUCED"))
        _refused(gate)

    def test_no_review_packet_may_exist(self, gate, copies):
        gate.REVIEW_PACKET.write_bytes(b"{}\n")
        _refused(gate, "exists")

    def test_the_outcome_cannot_be_made_ready(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d.__setitem__(
                "PRIMARY_OUTCOME", "SECOND_OPPORTUNITY_SYNTHESIS_V6_READY_FOR_HUMAN_REVIEW"
            ),
        )
        _refused(gate)


class TestNothingAfterTheFailureIsPassed:
    @pytest.mark.parametrize(
        "stage",
        [
            "6_semantic_output_gate_v1_4_0",
            "7_evidence_boundary_and_no_distortion",
            "8_attribution_and_provenance",
            "9_persistence_eligibility",
            "10_human_review",
        ],
    )
    def test_a_later_stage_cannot_be_marked_passed(self, gate, copies, stage):
        _edit(copies["RECORD"], lambda d: d["VALIDATION_STAGES"].__setitem__(stage, "PASSED"))
        _refused(gate)

    def test_the_schema_stage_cannot_be_marked_passed(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d["VALIDATION_STAGES"].__setitem__("5_schema_validation_v1_2_0", "PASSED"),
        )
        _refused(gate)

    def test_the_passed_count_cannot_grow(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("STAGES_PASSED", 5))
        _refused(gate)

    def test_the_violation_cannot_be_dropped(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["SCHEMA_VIOLATIONS"].pop())
        _refused(gate)

    def test_a_semantic_verdict_cannot_be_invented(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("SEMANTIC_GATE_VERDICT", "PASSED"))
        _refused(gate)


class TestTheResponseCannotBecomeACandidate:
    @pytest.mark.parametrize(
        "truncate", [None, 900], ids=["field-removed", "field-removed-and-truncated"]
    )
    def test_a_consistent_repair_is_still_not_what_arrived(self, gate, copies, truncate):
        """Remove the undeclared field (and trim the summary) and recompute every digest: still refused."""
        response = json.loads(copies["RESPONSE"].read_text(encoding="utf-8"))
        parsed = response["parsed_output"]
        parsed.pop(EXTRA)
        if truncate is not None:
            parsed["evidence_bound_reasoning_summary"] = parsed["evidence_bound_reasoning_summary"][
                :truncate
            ]
        assert schema_violations(parsed, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2) == []
        body = response["RAW_PROVIDER_RESPONSE_BODY"]
        for block in body["content"]:
            if block.get("type") == "tool_use":
                block["input"] = parsed
        raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        response["RAW_PROVIDER_RESPONSE_SHA256"] = hashlib.sha256(raw.encode()).hexdigest()
        response["RAW_PROVIDER_RESPONSE_CHARACTERS"] = len(raw)
        response["PARSED_OUTPUT_SHA256"] = hashlib.sha256(
            json.dumps(parsed, sort_keys=True).encode()
        ).hexdigest()
        response["validation"]["reasons"] = []
        text = json.dumps(response, indent=2, ensure_ascii=False) + "\n"
        copies["RESPONSE"].write_bytes(text.encode("utf-8"))

        def rebind(record: dict) -> None:
            kept = record["RESPONSE_ARTIFACT"]
            kept["file_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            kept["raw_response_sha256"] = response["RAW_PROVIDER_RESPONSE_SHA256"]
            kept["raw_response_characters"] = len(raw)
            kept["parsed_output_sha256"] = response["PARSED_OUTPUT_SHA256"]
            record["SCHEMA_VIOLATIONS"] = []
            record["SCHEMA_VIOLATION_DETAILS"] = []

        _edit(copies["RECORD"], rebind)
        _refused(gate, "changed after the execution record bound it|not the one that arrived")

    def test_the_response_file_cannot_change_under_the_record(self, gate, copies):
        _edit(copies["RESPONSE"], lambda d: d.__setitem__("$comment", "edited"))
        _refused(gate)

    def test_the_extra_field_cannot_be_recorded_as_declared(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d["SCHEMA_VIOLATION_DETAILS"][0].__setitem__(
                "declared_in_schema_v1_2_0", True
            ),
        )
        _refused(gate, "violation details")


class TestTheApprovalAndHistory:
    def test_v5s_record_stays_as_it_was(self, gate, copies):
        _edit(copies["RECORD_V5"], lambda d: d.__setitem__("EXECUTION_APPROVAL_CONSUMED", False))
        _refused(gate, "V1 to V5 artifact")

    def test_the_approval_cannot_change_after_the_call(self, gate, copies):
        _edit(copies["APPROVAL"], lambda d: d["NOT_AUTHORISED"].remove("any retry;"))
        _refused(gate)

    def test_the_deviation_acceptance_cannot_outlive_v6(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d["OPERATOR_APPROVAL"].__setitem__(
                "PROCESS_DEVIATION_ACCEPTANCE_EXPIRED", False
            ),
        )
        _refused(gate)

    def test_the_residual_risk_cannot_outlive_the_attempt(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d["OPERATOR_APPROVAL"].__setitem__("RESIDUAL_RISK_ACCEPTANCE_EXPIRED", False),
        )
        _refused(gate)

    def test_a_canonical_counter_cannot_move(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d["CANONICAL_COUNTERS_AFTER"].__setitem__("research.opportunities", 2),
        )
        _refused(gate)

    def test_nothing_is_persisted(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("OPPORTUNITY_PERSISTED", True))
        _refused(gate)

    def test_a_credential_shape_is_refused(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d.__setitem__("retention_note", "sk-ant-synthetic-marker-000000"),
        )
        _refused(gate, "credential")

    def test_a_note_rewritten_is_caught_by_the_record_pin(self, gate, copies):
        _edit(
            copies["RECORD"], lambda d: d.__setitem__("retention_note", "rewritten after the fact")
        )
        _refused(gate, "pinned")
