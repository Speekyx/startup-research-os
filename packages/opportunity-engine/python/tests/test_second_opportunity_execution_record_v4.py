"""Mission 1.84.13: CI gate 82 over the V4 execution record, and the refusals it must make.

Every mutation is made on a copy in a temporary directory, with the gate pointed at the copy, so the
committed record, approval and response are never touched.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
from collections.abc import Callable
from typing import Any

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "infrastructure" / "scripts" / "render_second_opportunity_execution_record_v4.py"
V4 = "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b"


@pytest.fixture(scope="module")
def gate() -> Any:
    spec = importlib.util.spec_from_file_location("gate_82_under_test", GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def copies(gate: Any, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """The record, approval, response and V3's record, copied byte for byte; the gate reads these."""
    out = {}
    for name in ("RECORD", "APPROVAL", "RESPONSE", "RECORD_V3"):
        source = getattr(gate, name)
        target = tmp_path / source.name
        target.write_bytes(source.read_bytes())
        monkeypatch.setattr(gate, name, target)
        out[name] = target
    monkeypatch.setattr(gate, "REVIEW_PACKET", tmp_path / gate.REVIEW_PACKET.name)
    return out


def _edit(path: pathlib.Path, change: Callable[[dict], None]) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    change(doc)
    path.write_bytes((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def _refused(gate: Any, match: str | None = None) -> None:
    with pytest.raises(gate.ValidationError, match=match):
        gate.validate()


class TestTheCommittedRecord:
    def test_the_record_validates(self, gate):
        record = gate.validate()
        assert record["PRIMARY_OUTCOME"] == "EXECUTION_SCHEMA_REJECTED_NO_RETRY"

    def test_the_page_is_the_rendering_of_the_record(self, gate):
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(gate.validate())

    def test_the_copies_validate_before_any_mutation(self, gate, copies):
        gate.validate()


class TestV4CannotExecuteTwice:
    def test_the_runner_refuses_v4_by_name(self, gate):
        runner = gate._module("runner_v4_for_record_tests", gate.RUNNER)
        with pytest.raises(runner.RefusedError) as refusal:
            runner.refuse_if_consumed(V4)
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"

    def test_an_unseen_digest_is_not_refused(self, gate):
        runner = gate._module("runner_v4_for_record_tests_unseen", gate.RUNNER)
        runner.refuse_if_consumed("ab" * 32)

    def test_the_approval_cannot_be_marked_unused(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("EXECUTION_APPROVAL_CONSUMED", False))
        _refused(gate)

    def test_further_calls_cannot_be_authorised(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("FURTHER_CALLS_AUTHORIZED_BY_V4", True))
        _refused(gate)

    def test_a_retry_cannot_be_recorded(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("retries", 1))
        _refused(gate)

    def test_a_second_request_cannot_be_recorded(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("actual_provider_requests", 2))
        _refused(gate)


class TestActualUsageIsNotTheWorstCase:
    def test_the_worst_case_cannot_stand_for_the_cost(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["ACTUAL_COST"].__setitem__("cost_units", 1.312398))
        _refused(gate)

    def test_usage_cannot_be_called_unestablished(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("ACTUAL_USAGE", "NOT_ESTABLISHED"))
        _refused(gate)

    def test_the_output_tokens_cannot_be_rounded(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["ACTUAL_USAGE"].__setitem__("output_tokens", 4000))
        _refused(gate)


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
                "PRIMARY_OUTCOME", "SECOND_OPPORTUNITY_SYNTHESIS_V4_READY_FOR_HUMAN_REVIEW"
            ),
        )
        _refused(gate)


class TestNothingAfterTheFailureIsPassed:
    @pytest.mark.parametrize(
        "stage",
        [
            "6_semantic_output_gate_v1_3_0",
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
            lambda d: d["VALIDATION_STAGES"].__setitem__("5_schema_validation_v1_1_0", "PASSED"),
        )
        _refused(gate)

    def test_the_passed_count_cannot_grow(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("STAGES_PASSED", 5))
        _refused(gate)

    def test_a_violation_cannot_be_dropped(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["SCHEMA_VIOLATIONS"].pop())
        _refused(gate)

    def test_a_semantic_verdict_cannot_be_invented(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("SEMANTIC_GATE_VERDICT", "PASSED"))
        _refused(gate)


class TestTheResponseCannotBecomeACandidate:
    def test_a_consistent_rewrite_is_still_not_what_arrived(self, gate, copies):
        """Trim both fields to their bounds and recompute every digest: the pins still refuse it."""
        response = json.loads(copies["RESPONSE"].read_text(encoding="utf-8"))
        parsed = response["parsed_output"]
        parsed["evidence_bound_reasoning_summary"] = parsed["evidence_bound_reasoning_summary"][
            :900
        ]
        parsed["candidate_intervention_class"] = parsed["candidate_intervention_class"][:300]
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
        text = json.dumps(response, indent=2, ensure_ascii=False) + "\n"
        copies["RESPONSE"].write_bytes(text.encode("utf-8"))

        def rebind(record: dict) -> None:
            kept = record["RESPONSE_ARTIFACT"]
            kept["file_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            kept["raw_response_sha256"] = response["RAW_PROVIDER_RESPONSE_SHA256"]
            kept["raw_response_characters"] = len(raw)
            kept["parsed_output_sha256"] = response["PARSED_OUTPUT_SHA256"]

        _edit(copies["RECORD"], rebind)
        _refused(gate, "not the one that arrived")

    def test_the_response_file_cannot_change_under_the_record(self, gate, copies):
        _edit(copies["RESPONSE"], lambda d: d.__setitem__("$comment", "edited"))
        _refused(gate)


class TestHistoryAndCounters:
    def test_v3s_record_stays_as_it_was(self, gate, copies):
        _edit(copies["RECORD_V3"], lambda d: d.__setitem__("EXECUTION_APPROVAL_CONSUMED", False))
        _refused(gate, "V3")

    def test_a_canonical_counter_cannot_move(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d["CANONICAL_COUNTERS_AFTER"].__setitem__("research.opportunities", 2),
        )
        _refused(gate)

    def test_nothing_is_persisted(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("OPPORTUNITY_PERSISTED", True))
        _refused(gate)

    def test_the_approval_cannot_change_after_the_call(self, gate, copies):
        _edit(copies["APPROVAL"], lambda d: d["NOT_AUTHORISED"].remove("any retry;"))
        _refused(gate)

    def test_a_credential_shape_is_refused(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d.__setitem__("retention_note", "sk-ant-synthetic-marker-000000"),
        )
        _refused(gate, "credential")
