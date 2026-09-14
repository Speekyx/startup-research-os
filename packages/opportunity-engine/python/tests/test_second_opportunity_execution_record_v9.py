"""Mission 1.84.22: CI gate 98 over the V9 execution record, and the refusals it must make.

Every mutation is made on a copy in a temporary directory, with the gate pointed at the copy, so the
committed record, approval and response are never touched. No test here can reach a provider: the
runner is only asked whether it would refuse a digest, the replay builds no transport, and `--execute`
runs under a tripwire on the real transport and on urlopen.
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
from sros_opportunity.assertion_context import is_request_shaped
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity_schema_v1_2 import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "infrastructure" / "scripts" / "render_second_opportunity_execution_record_v9.py"
V9 = "ba681da94b3e89f22c7e39bdb2dc4ef95d0527ca3db561c849eb089652d9425d"
STAGE_6 = "6_semantic_output_gate_v1_4_0"
LATER = (
    "7_evidence_boundary_and_no_distortion",
    "8_attribution_and_provenance",
    "9_persistence_eligibility",
    "10_human_review",
)


@pytest.fixture(scope="module")
def gate() -> Any:
    spec = importlib.util.spec_from_file_location("gate_98_under_test", GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def packet(gate: Any) -> dict:
    return json.loads(gate.PACKET_V9.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def response(gate: Any) -> dict:
    return json.loads(gate.RESPONSE.read_text(encoding="utf-8"))


@pytest.fixture
def copies(gate: Any, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """The record, approval and response, copied byte for byte; the gate reads these."""
    out = {}
    for name in ("RECORD", "APPROVAL", "RESPONSE"):
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


def _tripwire(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    import urllib.request

    import sros_llm_gateway.transport as transport_module

    built: list[int] = []

    def fire(*args: object, **kwargs: object) -> None:  # pragma: no cover - must never run
        built.append(1)
        raise AssertionError("a transport was built")

    monkeypatch.setattr(transport_module.UrllibTransport, "__init__", fire)
    monkeypatch.setattr(urllib.request, "urlopen", fire)
    return built


class TestTheCommittedRecord:
    def test_the_record_validates(self, gate):
        record = gate.validate()
        assert record["PRIMARY_OUTCOME"] == "EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY"
        assert record["FAILED_STAGE"] == STAGE_6
        assert record["STAGES_PASSED"] == 5
        assert len(record["SEMANTIC_GATE_REFUSAL_REASONS"]) == 7
        assert record["HARD_SCHEMA_VERDICT"] == "PASSED"
        assert record["UNKNOWN_ROOT_PROPERTIES_RETURNED"] == []

    def test_the_page_is_the_rendering_of_the_record(self, gate):
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(gate.validate())

    def test_the_copies_validate_before_any_mutation(self, gate, copies):
        gate.validate()

    @pytest.mark.parametrize("name", ["RECORD", "APPROVAL", "RESPONSE"])
    def test_a_missing_file_is_refused_by_name(self, gate, copies, name):
        """Without the record the runner's guard cannot see V9 spent: refused, never a crash."""
        copies[name].unlink()
        _refused(gate, "is missing")

    def test_the_cost_is_the_reported_usage_and_neither_bound(self, gate):
        record = gate.validate()
        cost = record["ACTUAL_COST"]["cost_units"]
        assert cost == "0.062326"
        assert cost not in (record["PLANNING_COST_ESTIMATE"], record["HARD_EXECUTION_COST_CEILING"])
        assert record["ACTUAL_COST_WITHIN_HARD_CEILING"] is True
        assert record["BILLED_CATEGORY_CONTRADICTIONS"] == []

    def test_the_summary_is_within_the_operators_bound_and_target(self, gate):
        summary = gate.validate()["REASONING_SUMMARY"]
        assert summary["within_target"] and summary["within_hard_maximum"]


class TestTheStagesAreReplayedWithNoDatabase:
    def test_the_replay_reproduces_the_retained_verdict(self, gate, packet, response):
        report, _statements, found = gate.replay(response, packet)
        for key in ("stages", "failed_stage", "reasons", "outcome", "stop_reason", "completion"):
            assert report[key] == response["validation"][key], key
        assert found["prompt_sha256"] == packet["PROMPT_SHA256"]
        assert found["representation_sha256"] == packet["REPRESENTATION_SHA256"]

    def test_the_replay_builds_no_transport(self, gate, packet, response, monkeypatch):
        built = _tripwire(monkeypatch)
        gate.replay(response, packet)
        assert built == []

    def test_an_edited_snapshot_is_refused(self, gate, packet, response, tmp_path, monkeypatch):
        doc = json.loads(gate.SNAPSHOT_RECORD.read_text(encoding="utf-8"))
        first = next(iter(doc["PACKET_SNAPSHOT"]["claim_statements"]))
        doc["PACKET_SNAPSHOT"]["claim_statements"][first] += " Edited."
        target = tmp_path / gate.SNAPSHOT_RECORD.name
        target.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        monkeypatch.setattr(gate, "SNAPSHOT_RECORD", target)
        with pytest.raises(gate.ValidationError, match="snapshot"):
            gate.replay(response, packet)

    def test_a_snapshot_rebuilding_another_packet_is_refused_even_repinned(
        self, gate, packet, response, tmp_path, monkeypatch
    ):
        doc = json.loads(gate.SNAPSHOT_RECORD.read_text(encoding="utf-8"))
        first = next(iter(doc["PACKET_SNAPSHOT"]["claim_statements"]))
        doc["PACKET_SNAPSHOT"]["claim_statements"][first] += " Edited."
        target = tmp_path / gate.SNAPSHOT_RECORD.name
        target.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        monkeypatch.setattr(gate, "SNAPSHOT_RECORD", target)
        monkeypatch.setattr(
            gate, "SNAPSHOT_RECORD_SHA256", hashlib.sha256(target.read_bytes()).hexdigest()
        )
        with pytest.raises(gate.ValidationError, match="rebuilds"):
            gate.replay(response, packet)


class TestEachRefusalIsMeasuredAgainstTheAnswer:
    def test_the_unsupported_term_is_in_the_class_and_in_no_statement(self, gate):
        details = gate.validate()["SEMANTIC_REFUSAL_DETAILS"]
        terms = [d for d in details if d["kind"] == "UNSUPPORTED_TERM"]
        assert [(d["field"], d["term"]) for d in terms] == [
            ("candidate_intervention_class", "market")
        ]
        assert "market" in terms[0]["text"]

    def test_the_six_items_are_imperatives_and_not_requests(self, gate):
        details = gate.validate()["SEMANTIC_REFUSAL_DETAILS"]
        requests = [d for d in details if d["kind"] == "NOT_REQUEST_SHAPED"]
        assert [d["first_word"] for d in requests] == [
            "Identify",
            "Obtain",
            "Observe",
            "Determine",
            "Identify",
            "Observe",
        ]
        assert [d["field"] for d in requests if d["confirmation_words"]] == [
            "recommended_next_evidence[3]"
        ]

    def test_the_gate_reads_a_named_request_as_a_request(self):
        tail = "whether the same contracting authority appears across multiple notices over time."
        assert is_request_shaped(f"Evidence of {tail}")
        assert not is_request_shaped(f"Identify {tail}")

    def test_a_term_the_answer_does_not_carry_cannot_have_refused_it(self, gate, response):
        parsed = copy.deepcopy(response["parsed_output"])
        parsed["candidate_intervention_class"] = parsed["candidate_intervention_class"].replace(
            "market-intelligence", "analyst"
        )
        _packet, statements, _pairs = gate.snapshot_packet()
        with pytest.raises(gate.ValidationError, match="does not carry"):
            gate.semantic_details(parsed, statements, response["validation"]["reasons"])

    def test_a_request_shaped_item_cannot_have_been_refused_as_not(self, gate, response):
        parsed = copy.deepcopy(response["parsed_output"])
        parsed["recommended_next_evidence"][0] = (
            "Evidence of whether the same contracting authority appears across multiple notices."
        )
        _packet, statements, _pairs = gate.snapshot_packet()
        with pytest.raises(gate.ValidationError, match="is request-shaped"):
            gate.semantic_details(parsed, statements, response["validation"]["reasons"])

    def test_a_refusal_of_an_unknown_kind_is_refused(self, gate, response):
        _packet, statements, _pairs = gate.snapshot_packet()
        with pytest.raises(gate.ValidationError, match="does not describe"):
            gate.semantic_details(
                response["parsed_output"],
                statements,
                ["candidate_intervention_class audited SOMETHING_ELSE: unexplained"],
            )

    def test_a_detail_cannot_be_rewritten(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d["SEMANTIC_REFUSAL_DETAILS"][1].__setitem__("request_shaped", True),
        )
        _refused(gate, "details")

    def test_a_reason_cannot_be_dropped(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["SEMANTIC_GATE_REFUSAL_REASONS"].pop())
        _refused(gate)

    def test_the_prompts_words_cannot_be_misreported(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d["PROMPT_STATED_RULES"].__setitem__("no_wording_of_confirmation", False),
        )
        _refused(gate, "PROMPT_STATED_RULES")


class TestV9CannotExecuteTwice:
    def test_the_runner_refuses_v9_as_spent(self, gate):
        runner = gate.runner()
        with pytest.raises(runner.RefusedError) as refusal:
            runner.refuse_if_consumed(V9)
        assert refusal.value.code == gate.CONSUMED

    @pytest.mark.parametrize("label", ["V1", "V2", "V3", "V4", "V5", "V6"])
    def test_the_runner_refuses_a_spent_predecessor_by_name(self, gate, label):
        runner = gate.runner()
        with pytest.raises(runner.RefusedError) as refusal:
            runner.refuse_if_consumed(gate.SPENT[label])
        assert refusal.value.code == gate.CONSUMED

    @pytest.mark.parametrize("label", ["V7", "V8"])
    def test_the_runner_refuses_a_superseded_packet_by_name(self, gate, label):
        runner = gate.runner()
        digest = gate.V7_SHA256 if label == "V7" else gate.V8_SHA256
        with pytest.raises(runner.RefusedError) as refusal:
            runner.refuse_if_consumed(digest)
        assert refusal.value.code == gate.SUPERSEDED

    def test_an_unseen_digest_is_not_refused(self, gate):
        gate.runner().refuse_if_consumed("ab" * 32)

    def test_a_second_execute_stops_before_any_transport(self, gate, monkeypatch, capsys):
        built = _tripwire(monkeypatch)
        runner = gate.runner()

        def no_execute(*args: object, **kwargs: object) -> None:  # pragma: no cover
            built.append(2)
            raise AssertionError("execute() was reached")

        monkeypatch.setattr(runner, "execute", no_execute)
        assert runner.main(["--execute"]) == 1
        assert gate.CONSUMED in capsys.readouterr().out
        assert built == []

    def test_the_approval_is_spent_whatever_the_terminal_outcome(self, gate, tmp_path, monkeypatch):
        runner = gate.runner()
        for outcome in sorted(gate.FACTUAL):
            record = tmp_path / f"record-v9-{outcome}.json"
            record.write_text(
                json.dumps(
                    {
                        "EXECUTION_APPROVAL_CONSUMED": True,
                        "execution_packet_sha256": V9,
                        "RUNNER_OUTCOME": outcome,
                        "actual_provider_requests": 1,
                    }
                ),
                encoding="utf-8",
            )
            monkeypatch.setattr(runner, "EXECUTION_RECORD_V9", record)
            with pytest.raises(runner.RefusedError) as refusal:
                runner.refuse_if_consumed(V9)
            assert refusal.value.code == gate.CONSUMED, outcome

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("EXECUTION_APPROVAL_CONSUMED", False),
            ("FURTHER_CALLS_AUTHORIZED_BY_V9", True),
            ("actual_provider_requests", 2),
            ("actual_model_calls", 2),
            ("retries", 1),
            ("fallbacks", 1),
            ("continuation_requests", 1),
            ("repair_calls", 1),
        ],
    )
    def test_the_record_cannot_restore_authority_or_add_a_call(self, gate, copies, key, value):
        _edit(copies["RECORD"], lambda d: d.__setitem__(key, value))
        _refused(gate)


class TestTheCostIsWhatTheUsageSays:
    @pytest.mark.parametrize("bound", ["3.608", "1.316316"], ids=["ceiling", "planning-estimate"])
    def test_a_bound_cannot_stand_for_the_cost(self, gate, copies, bound):
        _edit(copies["RECORD"], lambda d: d["ACTUAL_COST"].__setitem__("cost_units", bound))
        _refused(gate, "ACTUAL_COST")

    def test_usage_cannot_be_called_unestablished(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("ACTUAL_USAGE", "NOT_ESTABLISHED"))
        _refused(gate)

    def test_the_output_tokens_cannot_be_rounded(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["ACTUAL_USAGE"].__setitem__("output_tokens", 4000))
        _refused(gate)

    def test_a_contradiction_cannot_be_invented_or_hidden(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d.__setitem__("BILLED_CATEGORY_CONTRADICTIONS", ["invented"]),
        )
        _refused(gate, "contradictions")

    @pytest.mark.parametrize(
        ("change", "fragment"),
        [
            (lambda u: u.__setitem__("service_tier", "priority"), "service_tier"),
            (lambda u: u.__setitem__("inference_geo", "eu"), "inference_geo"),
            (lambda u: u.__setitem__("cache_read_input_tokens", 10), "cache_read_input_tokens"),
            (
                lambda u: u["cache_creation"].__setitem__("ephemeral_5m_input_tokens", 5),
                "cache_creation",
            ),
            (
                lambda u: u["output_tokens_details"].__setitem__("thinking_tokens", 7),
                "thinking_tokens",
            ),
            (lambda u: u.__setitem__("output_tokens", 128001), "max_tokens"),
            (lambda u: u.__setitem__("input_tokens", 1000001), "context window"),
        ],
        ids=[
            "priority-tier",
            "undocumented-geo",
            "cache-read",
            "cache-write",
            "thinking",
            "over-max-tokens",
            "over-context-window",
        ],
    )
    def test_a_billed_category_outside_the_ceiling_is_a_contradiction(
        self, gate, packet, response, change, fragment
    ):
        usage = copy.deepcopy(response["RAW_PROVIDER_RESPONSE_BODY"]["usage"])
        change(usage)
        found = gate.billing_contradictions(usage, packet)
        assert found and any(fragment in item for item in found), found

    def test_us_only_inference_is_within_the_ceiling_and_costs_one_point_one_times(
        self, gate, packet, response
    ):
        usage = copy.deepcopy(response["RAW_PROVIDER_RESPONSE_BODY"]["usage"])
        usage["inference_geo"] = "us"
        assert gate.billing_contradictions(usage, packet) == []
        assert gate.actual_cost(usage, packet)["cost_units"] == "0.0685586"

    def test_the_observed_usage_contradicts_nothing(self, gate, packet, response):
        usage = response["RAW_PROVIDER_RESPONSE_BODY"]["usage"]
        assert gate.billing_contradictions(usage, packet) == []
        assert gate.actual_cost(usage, packet)["residency_multiplier"] == "1"


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
            lambda d: d.__setitem__("PRIMARY_OUTCOME", gate.READY_FOR_HUMAN_REVIEW),
        )
        _refused(gate)


class TestNothingAfterTheFailureIsPassed:
    @pytest.mark.parametrize("stage", LATER)
    def test_a_later_stage_cannot_be_marked_passed(self, gate, copies, stage):
        _edit(copies["RECORD"], lambda d: d["VALIDATION_STAGES"].__setitem__(stage, "PASSED"))
        _refused(gate)

    def test_the_semantic_stage_cannot_be_marked_passed(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["VALIDATION_STAGES"].__setitem__(STAGE_6, "PASSED"))
        _refused(gate)

    def test_the_passed_count_cannot_grow(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("STAGES_PASSED", 6))
        _refused(gate)

    def test_the_semantic_verdict_cannot_be_reversed(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d.__setitem__("SEMANTIC_GATE_VERDICT", "PASSED"))
        _refused(gate)

    def test_a_pass_after_a_failure_is_refused_by_rule(self, gate):
        stages = dict.fromkeys(gate.STAGES, "NOT_REACHED")
        for name in gate.STAGES[:5]:
            stages[name] = "PASSED"
        stages[STAGE_6] = "FAILED"
        gate._no_pass_after_failure(stages)
        stages[LATER[0]] = "PASSED"
        with pytest.raises(gate.ValidationError, match="never passed"):
            gate._no_pass_after_failure(stages)


class TestTheResponseCannotBecomeACandidate:
    def test_a_consistent_rewrite_is_still_not_what_arrived(self, gate, copies):
        """Drop the unsupported word, make the requests requests, recompute every digest: refused."""
        response = json.loads(copies["RESPONSE"].read_text(encoding="utf-8"))
        parsed = response["parsed_output"]
        parsed["candidate_intervention_class"] = parsed["candidate_intervention_class"].replace(
            " or market-intelligence", ""
        )
        parsed["recommended_next_evidence"] = [
            "Evidence of whether the same contracting authority appears across multiple notices."
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
        response["validation"]["stages"][STAGE_6] = "PASSED"
        text = json.dumps(response, indent=2, ensure_ascii=False) + "\n"
        copies["RESPONSE"].write_bytes(text.encode("utf-8"))

        def rebind(record: dict) -> None:
            kept = record["RESPONSE_ARTIFACT"]
            kept["file_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            kept["raw_response_sha256"] = response["RAW_PROVIDER_RESPONSE_SHA256"]
            kept["raw_response_characters"] = len(raw)
            kept["parsed_output_sha256"] = response["PARSED_OUTPUT_SHA256"]
            record["SEMANTIC_GATE_REFUSAL_REASONS"] = []
            record["SEMANTIC_REFUSAL_DETAILS"] = []

        _edit(copies["RECORD"], rebind)
        _refused(gate, "changed after the execution record bound it|not the one that arrived")

    def test_the_response_file_cannot_change_under_the_record(self, gate, copies):
        _edit(copies["RESPONSE"], lambda d: d.__setitem__("$comment", "edited"))
        _refused(gate)


class TestTheApprovalAndHistory:
    def test_v5s_record_stays_as_it_was(self, gate, copies, tmp_path, monkeypatch):
        history = dict(gate.G91.HISTORY)
        v5 = next(
            p for p in history if p.name == "second-opportunity-synthesis-execution-record-v5.json"
        )
        target = tmp_path / v5.name
        target.write_bytes(v5.read_bytes())
        _edit(target, lambda d: d.__setitem__("EXECUTION_APPROVAL_CONSUMED", False))
        history[target] = history.pop(v5)
        monkeypatch.setattr(gate.G91, "HISTORY", history)
        _refused(gate, "V1 to V6")

    def test_v6s_record_stays_as_it_was(self, gate, copies, tmp_path, monkeypatch):
        target = tmp_path / gate.G91.RECORD.name
        target.write_bytes(gate.G91.RECORD.read_bytes())
        _edit(target, lambda d: d.__setitem__("EXECUTION_APPROVAL_CONSUMED", False))
        monkeypatch.setattr(gate.G91, "RECORD", target)
        _refused(gate, "V1 to V6")

    def test_v7_cannot_be_restored(self, gate, copies, tmp_path, monkeypatch):
        target = tmp_path / gate.SUPERSESSION["V7"].name
        target.write_bytes(gate.SUPERSESSION["V7"].read_bytes())
        _edit(target, lambda d: d.__setitem__("STATUS", "RESTORED"))
        monkeypatch.setattr(gate, "SUPERSESSION", {**gate.SUPERSESSION, "V7": target})
        _refused(gate, "V7")

    def test_v8_cannot_acquire_an_approval(self, gate, copies, tmp_path, monkeypatch):
        forged = tmp_path / "second-opportunity-synthesis-execution-approval-v8.json"
        forged.write_text("{}\n", encoding="utf-8")
        monkeypatch.setattr(gate, "NEVER_RUN", {**gate.NEVER_RUN, "V8": [forged]})
        _refused(gate, "never approved or run")

    def test_the_approval_cannot_change_after_the_call(self, gate, copies):
        _edit(copies["APPROVAL"], lambda d: d["NOT_AUTHORISED"].remove("retry"))
        _refused(gate)

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("RESIDUAL_RISK_ACCEPTANCE_EXPIRED", False),
            ("TIMEOUT_RISK_ACCEPTANCE_EXPIRED", False),
            ("INHERITABLE_BY_FUTURE_PACKET", True),
            ("V9_ONLY", False),
        ],
    )
    def test_the_acceptances_cannot_outlive_the_attempt(self, gate, copies, key, value):
        _edit(copies["RECORD"], lambda d: d["OPERATOR_APPROVAL"].__setitem__(key, value))
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
