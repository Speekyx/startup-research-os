"""Mission 1.84.14. Execution packet V5's runner: V4's call, prompt v1.4.0, and nothing looser.

Seven things this file defends, with synthetic transports and never with a network.

THE PROMPT SENT IS v1.4.0, and it states every schema bound, every class-A semantic rule and every
generation target beside its hard maximum. The runner's headroom check refuses prompt v1.3.0.

A TARGET IS NOT A LIMIT: an answer over a target and within the hard maximum passes stage 5.

THE SCHEMA STILL DECIDES, and the completion signal still outranks the content, with one request and
nothing that finishes the JSON.

STAGE 6 IS GATE v1.3.0 AND CANNOT BE REPLACED. The stage function takes no gate.

STAGES 6 TO 9 EACH REFUSE AT THEIR OWN STAGE, with the real machinery.

NO APPROVAL, NO TRANSPORT, and V1's, V2's, V3's and V4's spent digests cannot run; an unseen digest can.

WHAT ARRIVED IS KEPT on each terminal path, and when judging fails.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"
RUNNER_PATH = SCRIPTS / "run_second_opportunity_execution_v5.py"
BOUNDED_GATE_PATH = SCRIPTS / "render_second_opportunity_bounded_contract.py"
FIXTURES_PATH = SCRIPTS / "second_opportunity_synthetic_fixtures.py"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
V3_SHA256 = "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2"
V4_SHA256 = "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b"
SYNTHETIC_SHA = "d" * 64
STRUCTURED_TOOL_NAME = "emit_structured_output"
REQUEST_ID = "req_synthetic_v5"
SUMMARY = "evidence_bound_reasoning_summary"
OBSERVED = "OBSERVED_OR_EVIDENCE_SUPPORTED"
MISSING = object()


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _module("runner_v5_under_test", RUNNER_PATH)


@pytest.fixture(scope="module")
def bounded():
    return _module("bounded_gate_for_runner_v5_tests", BOUNDED_GATE_PATH)


@pytest.fixture(scope="module")
def fx():
    return _module("fixtures_for_runner_v5_tests", FIXTURES_PATH)


def _packet_file(sha: str = SYNTHETIC_SHA) -> dict:
    return {
        "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V5",
        "EXECUTION_PACKET_VERSION": 5,
        "EXECUTION_PACKET_SHA256": sha,
        "ADAPTER_PARAMETERS": {"max_output_tokens": 128000, "thinking": "DISABLED"},
        "REQUEST_TIMEOUT": 60.0,
        "GENERATION_PARAMETERS": {"max_retries": 0},
    }


def _context(fx, sha: str = SYNTHETIC_SHA, **kwargs) -> dict:
    context = fx.runner_context(**kwargs)
    context["packet_file"] = {**context["packet_file"], **_packet_file(sha)}
    context["parts"] = render_parts(fx)
    return context


def render_parts(fx):
    from sros_opportunity.second_opportunity_prompt_v1_4 import (
        render_second_opportunity_prompt_v1_4,
    )

    return render_second_opportunity_prompt_v1_4(
        fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
    )


def _schema_valid_output(bounded) -> dict:
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1

    output = bounded.maximum_instance(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, bounded.ASCII_FILL)
    output["decision"] = "FORM_HYPOTHESIS"
    return output


def _required_keys_only() -> dict:
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1

    return {key: "x" for key in SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["required"]}


def _body(structured, stop_reason=MISSING, *, usage=(11, 22), extra_blocks=()) -> dict:
    blocks: list[dict] = [{"type": "text", "text": "synthetic"}]
    if structured is not None:
        blocks.append(
            {
                "type": "tool_use",
                "id": "toolu_synthetic",
                "name": STRUCTURED_TOOL_NAME,
                "input": structured,
            }
        )
    blocks.extend(extra_blocks)
    body = {
        "id": "msg_synthetic",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-5",
        "content": blocks,
        "usage": {"input_tokens": usage[0], "output_tokens": usage[1]},
    }
    if stop_reason is not MISSING:
        body["stop_reason"] = stop_reason
    return body


class ScriptedTransport:
    """A synthetic transport with no socket. A second call is a test failure, not a queue."""

    def __init__(self, *, status=200, body=None, raises=None, headers=None) -> None:
        self.status = status
        self.body = body
        self.raises = raises
        self.headers = {"request-id": REQUEST_ID} if headers is None else headers
        self.calls: list[dict] = []

    def post_json(self, url, headers, body, timeout_seconds):
        from sros_llm_gateway.transport import HttpResponse

        self.calls.append({"url": url, "body": body, "timeout_seconds": timeout_seconds})
        if len(self.calls) > 1:
            raise AssertionError("a second request: a retry, a continuation or a repair")
        if self.raises is not None:
            raise self.raises
        return HttpResponse(self.status, json.dumps(self.body).encode("utf-8"), dict(self.headers))


def _config():
    from sros_llm_gateway.config import GatewayConfig, TierBinding
    from sros_llm_gateway.types import LlmTier

    return GatewayConfig(
        routing_version="synthetic",
        bindings={
            LlmTier.STRONG_MODEL: TierBinding(
                tier=LlmTier.STRONG_MODEL, provider="anthropic", model="claude-sonnet-5"
            )
        },
    )


def _approval(**overrides) -> dict:
    base = {
        "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V5",
        "EXECUTION_PACKET_VERSION": 5,
        "EXECUTION_PACKET_SHA256": SYNTHETIC_SHA,
        "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
        "approved_by": "synthetic operator",
        "operator_statement": "a synthetic approval, for a test",
        "recorded_by": "mission-9.9.9",
    }
    base.update(overrides)
    return base


@pytest.fixture
def approved(runner, tmp_path, monkeypatch):
    path = tmp_path / "approval-v5.json"
    path.write_text(json.dumps(_approval()), encoding="utf-8")
    monkeypatch.setattr(runner, "APPROVAL_FILE", path)
    return path


def _run(runner, fx, transport, context: dict | None = None):
    from sros_llm_gateway.pricing import PricingTable

    context = context or _context(fx)
    result = runner.execute(
        context,
        transport=transport,
        config=_config(),
        pricing=PricingTable(version="synthetic", prices={}),
        api_key="synthetic-not-a-credential",
    )
    return result, context


def _report(runner, fx, transport, context: dict | None = None):
    result, context = _run(runner, fx, transport, context)
    return runner.validate_execution(result, context), result


def _not_reached_after(runner, report, stage: str) -> bool:
    index = runner.STAGES.index(stage)
    return all(report["stages"][s] == "NOT_REACHED" for s in runner.STAGES[index + 1 :])


# ================================================================== the prompt sent


class TestThePromptSentIsVersion140:
    def test_the_request_carries_the_semantic_block_and_the_source_names(
        self, runner, fx, approved
    ):
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, fx, transport)
        sent = json.dumps(transport.calls[0]["body"])
        assert "SEMANTIC RULES THE ANSWER IS AUDITED AGAINST." in sent
        assert "SOURCE NAMES ARE PROVENANCE, NEVER EVIDENCE." in sent
        assert "SOURCE NAMES. These exact strings occur" in sent
        assert f"{SUMMARY}\\n    at most 900 characters" in sent
        assert "GENERATION TARGETS: MARGIN BELOW THE HARD LIMITS." in sent
        assert (
            "candidate_intervention_class: generation target 240 characters; "
            "hard maximum 300 characters" in sent
        )

    def test_no_schema_bound_and_no_class_a_semantic_rule_is_left_unstated(self, runner, fx):
        parts = render_parts(fx)
        assert runner.unstated_constraints(parts.system_instructions) == []
        assert runner.unstated_semantic_rules(parts) == []
        assert runner.unstated_targets(parts) == []

    def test_the_headroom_check_refuses_prompt_v1_3(self, runner, fx):
        from sros_opportunity.second_opportunity_prompt_v1_3 import (
            render_second_opportunity_prompt_v1_3,
        )

        v1_3 = render_second_opportunity_prompt_v1_3(
            fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
        )
        assert "candidate_intervention_class" in runner.unstated_targets(v1_3)

    def test_the_semantic_drift_check_refuses_prompt_v1_2(self, runner, fx):
        from sros_opportunity.second_opportunity import render_second_opportunity_prompt_v1_2

        v1_2 = render_second_opportunity_prompt_v1_2(
            fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM
        )
        assert "OBSERVED_DISJUNCTION_FAILS_CLOSED" in runner.unstated_semantic_rules(v1_2)

    def test_the_request_names_prompt_1_4_0_and_schema_1_1_0(self, runner, fx):
        request = runner.build_request(render_parts(fx), _packet_file())
        assert request.prompt_template_version == "1.4.0"
        assert request.response_schema["properties"][SUMMARY]["maxLength"] == 900


# ================================================================== the schema still decides


class TestTheSchemaStillDecides:
    def test_a_class_over_its_target_and_within_its_bound_passes_stage_5(
        self, runner, fx, bounded, approved
    ):
        output = _schema_valid_output(bounded)
        output["candidate_intervention_class"] = "x" * 241
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        assert report["stages"]["5_schema_validation_v1_1_0"] == "PASSED"

    def test_a_summary_at_the_bound_passes_stage_5(self, runner, fx, bounded, approved):
        output = _schema_valid_output(bounded)
        output[SUMMARY] = "x" * 900
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        assert report["stages"]["5_schema_validation_v1_1_0"] == "PASSED"

    def test_a_summary_one_over_is_refused_at_stage_5_and_kept_whole(
        self, runner, fx, bounded, approved
    ):
        output = _schema_valid_output(bounded)
        output[SUMMARY] = "x" * 901
        result, context = _run(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        report = runner.validate_execution(result, context)
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY"
        assert report["reasons"] == [f"{SUMMARY}: 901 characters exceeds maxLength 900"]
        artifact = runner.build_artifact(result, report)
        assert len(artifact["parsed_output"][SUMMARY]) == 901
        assert artifact["PERSISTED"] == "NOTHING"


# ================================================================== the completion signal first


class TestTheCompletionSignalDecidesFirst:
    def test_an_output_limit_stop_is_refused_before_persistence(self, runner, fx, approved):
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(None, "max_tokens")))
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"
        assert _not_reached_after(runner, report, "3_provider_completion")

    def test_an_output_limit_stop_satisfying_the_full_answer_is_still_refused(
        self, runner, fx, approved
    ):
        report, _ = _report(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "max_tokens"))
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"
        assert report["stages"]["5_schema_validation_v1_1_0"] == "NOT_REACHED"

    @pytest.mark.parametrize("stop_reason", ["end_turn", "pause_turn", None, "a_value_added_later"])
    def test_an_unknown_stop_reason_fails_closed(self, runner, fx, approved, stop_reason):
        report, _ = _report(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), stop_reason))
        )
        assert report["outcome"] == "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY"
        assert report["failed_stage"] == "3_provider_completion"

    def test_a_refusal_stop_is_refused_before_any_parse(self, runner, fx, approved):
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(fx.good_output(), "refusal")))
        assert report["outcome"] == "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY"
        assert report["stages"]["4_structured_output_parse"] == "NOT_REACHED"

    def test_a_context_window_stop_is_an_output_limit(self, runner, fx, approved):
        report, _ = _report(
            runner, fx, ScriptedTransport(body=_body(None, "model_context_window_exceeded"))
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"

    def test_a_provider_error_status_fails_at_transport(self, runner, fx, approved):
        report, _ = _report(
            runner, fx, ScriptedTransport(status=500, body={"error": {"message": "overloaded"}})
        )
        assert report["outcome"] == "EXECUTION_FAILED_PROVIDER_ERROR_NO_RETRY"

    def test_an_insufficient_evidence_answer_forms_no_hypothesis(self, runner, fx, approved):
        output = fx.good_output(decision="INSUFFICIENT_EVIDENCE")
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        assert report["outcome"] == "EXECUTION_COMPLETED_INSUFFICIENT_EVIDENCE_NO_OPPORTUNITY"


# ================================================================== one request


class TestOneRequestAndNothingThatFinishesTheJson:
    def test_exactly_one_request_even_at_the_limit(self, runner, fx, approved):
        transport = ScriptedTransport(body=_body(_required_keys_only(), "max_tokens"))
        _report(runner, fx, transport)
        assert len(transport.calls) == 1

    def test_the_request_disables_thinking_and_asks_for_128000(self, runner, fx, approved):
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, fx, transport)
        sent = transport.calls[0]
        assert sent["body"]["thinking"] == {"type": "disabled"}
        assert sent["body"]["max_tokens"] == 128000
        assert sent["body"]["tool_choice"] == {"type": "tool", "name": STRUCTURED_TOOL_NAME}
        assert sent["timeout_seconds"] == 60.0
        assert sent["url"] == "https://api.anthropic.com/v1/messages"

    def test_the_runner_source_has_one_call_site_and_no_loop(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        assert source.count("gateway.complete(") == 1
        assert re.search(r"^\s*while\b", source, re.MULTILINE) is None
        assert "count_tokens" not in source


# ================================================================== stage 6 is gate v1.3.0


class TestStage6IsGate130AndCannotBeReplaced:
    def test_the_stage_function_takes_no_gate(self, runner):
        assert list(inspect.signature(runner.validate_execution).parameters) == [
            "result",
            "context",
        ]

    def test_stage_6_is_named_for_gate_v1_3(self, runner):
        assert runner.STAGES[5] == "6_semantic_output_gate_v1_3_0"


# ================================================================== stages 6 to 9, real machinery


class TestEachStageRefusesAtItsOwnStage:
    def test_a_valid_answer_reaches_stage_9_eligible_for_review_only(self, runner, fx):
        report = runner.validate_execution(
            fx.recorded_result(fx.good_output()), fx.runner_context()
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
        assert report["stages"]["9_persistence_eligibility"] == "ELIGIBLE_FOR_HUMAN_REVIEW_ONLY"
        assert report["stages"]["10_human_review"] == "REQUIRED_NOT_PERFORMED"
        assert report["persistence_eligibility"]["persisted"] is False
        assert (
            report["provenance"]["semantic_gate_version"] == "second-opportunity-output-gate@1.3.0"
        )

    def test_a_semantic_failure_stops_at_6(self, runner, fx):
        answer = fx.with_statement(
            "Notices under CPV class 7777 state amounts in EUR or in another currency.", OBSERVED
        )
        report = runner.validate_execution(fx.recorded_result(answer), fx.runner_context())
        assert report["failed_stage"] == "6_semantic_output_gate_v1_3_0"
        assert _not_reached_after(runner, report, "6_semantic_output_gate_v1_3_0")

    def test_a_stray_id_is_the_gate_s_refusal_never_stage_7_s(self, runner, fx):
        answer = fx.good_output(supporting_evidence_ids=[*fx.EVIDENCE, fx.EXTRA_ROW[0]])
        report = runner.validate_execution(fx.recorded_result(answer), fx.runner_context())
        assert report["failed_stage"] == "6_semantic_output_gate_v1_3_0"

    def test_an_answer_outside_the_approved_boundary_stops_at_7(self, runner, fx):
        wider = fx.packet(extra=True)
        answer = fx.good_output(
            supporting_evidence_ids=[*fx.EVIDENCE, fx.EXTRA_ROW[0]],
            supporting_claim_ids=[*fx.CLAIMS, fx.EXTRA_ROW[1]],
            independence_status="Independence is UNKNOWN for 3 of 3 rows.",
            reliability_status="All rows are SCORABLE; no score exists.",
            unsupported_dimensions=fx.mandatory_unsupported(wider),
        )
        context = fx.runner_context(evidence_packet=wider, supplied=fx.extra_statements())
        report = runner.validate_execution(fx.recorded_result(answer), context)
        assert report["failed_stage"] == "7_evidence_boundary_and_no_distortion"
        assert report["stages"]["6_semantic_output_gate_v1_3_0"] == "PASSED"
        assert "outside the approved evidence boundary" in report["reasons"][0]

    def test_an_empty_request_id_stops_at_8(self, runner, fx):
        report = runner.validate_execution(
            fx.recorded_result(fx.good_output(), request_id=""), fx.runner_context()
        )
        assert report["failed_stage"] == "8_attribution_and_provenance"
        assert report["reasons"] == ["no provider_request_id"]

    def test_an_absent_request_id_is_recorded_as_absent_and_passes(self, runner, fx):
        result = fx.recorded_result(fx.good_output())
        result["transport_responses"][0]["headers"] = {"content-type": "application/json"}
        report = runner.validate_execution(result, fx.runner_context())
        assert report["provenance"]["provider_request_id"] == "NOT_EXPOSED"

    def test_a_request_id_is_read_by_its_header_name(self, runner, fx):
        result = fx.recorded_result(fx.good_output())
        result["transport_responses"][0]["headers"] = {
            "content-type": "application/json",
            "request-id": "req_named",
        }
        report = runner.validate_execution(result, fx.runner_context())
        assert report["provenance"]["provider_request_id"] == "req_named"

    def test_an_answer_the_hypothesis_model_cannot_represent_stops_at_9(self, runner, fx):
        guarded = "Profitability Review (synthetic register)"
        summary = fx.good_output()[SUMMARY].replace(fx.SHORT_NAME, "Profitability Review")
        report = runner.validate_execution(
            fx.recorded_result(fx.good_output(**{SUMMARY: summary})),
            fx.runner_context(
                supplied=fx.statements(name=guarded), names=fx.metadata(name=guarded)
            ),
        )
        assert report["failed_stage"] == "9_persistence_eligibility"
        assert report["stages"]["8_attribution_and_provenance"] == "PASSED"
        assert "profitability" in report["reasons"][0]
        assert report["stages"]["10_human_review"] == "NOT_REACHED"


# ================================================================== approval and spent digests


class TestNoApprovalNoTransport:
    def _tripwire(self, monkeypatch) -> list[int]:
        import sros_llm_gateway.transport as transport_module

        built: list[int] = []
        original = transport_module.UrllibTransport.__init__

        def tripwire(self, *a, **k):  # pragma: no cover - must never run
            built.append(1)
            return original(self, *a, **k)

        monkeypatch.setattr(transport_module.UrllibTransport, "__init__", tripwire)
        return built

    def test_no_approval_refuses_before_a_transport_exists(self, runner, fx, tmp_path, monkeypatch):
        monkeypatch.setattr(runner, "APPROVAL_FILE", tmp_path / "absent.json")
        built = self._tripwire(monkeypatch)
        with pytest.raises(runner.RefusedError) as refusal:
            runner.execute(_context(fx))
        assert refusal.value.code == "OPERATOR_APPROVAL_NOT_RECORDED"
        assert built == []

    @pytest.mark.parametrize(
        ("override", "code"),
        [
            ({"EXECUTION_PACKET_SHA256": "e" * 64}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
            ({"EXECUTION_PACKET_VERSION": 3}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
            ({"decision": "DEFER"}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
            ({"approved_by": "  "}, "OPERATOR_APPROVAL_INCOMPLETE"),
            ({"operator_statement": ""}, "OPERATOR_APPROVAL_INCOMPLETE"),
        ],
    )
    def test_an_approval_that_does_not_approve_this_packet_is_refused(
        self, runner, fx, tmp_path, monkeypatch, override, code
    ):
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(_approval(**override)), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, transport)
        assert refusal.value.code == code
        assert transport.calls == []

    def test_a_v4_approval_does_not_authorise_v5(self, runner, fx, tmp_path, monkeypatch):
        path = tmp_path / "approval.json"
        path.write_text(
            json.dumps(
                _approval(
                    EXECUTION_PACKET_ID="SECOND-OPPORTUNITY-SYNTH-EXEC-V4",
                    EXECUTION_PACKET_VERSION=4,
                    EXECUTION_PACKET_SHA256=V4_SHA256,
                )
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, ScriptedTransport(body=_body(None, "tool_use")))
        assert refusal.value.code == "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"

    @pytest.mark.parametrize(
        "spent", [V1_SHA256, V2_SHA256, V3_SHA256, V4_SHA256], ids=["V1", "V2", "V3", "V4"]
    )
    def test_a_spent_digest_cannot_run_under_v5(self, runner, fx, tmp_path, monkeypatch, spent):
        """Even with an approval naming it, the consumed-approval guard refuses a spent digest."""
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(_approval(EXECUTION_PACKET_SHA256=spent)), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, transport, _context(fx, spent))
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"
        assert transport.calls == []

    def test_an_unseen_digest_is_not_refused_because_v1_to_v4_are_spent(self, runner):
        runner.refuse_if_consumed("0" * 64)
        runner.refuse_if_consumed(SYNTHETIC_SHA)

    def test_v5s_own_record_refuses_its_digest_once_spent(self, runner, fx, approved, monkeypatch):
        record = approved.parent / "record-v5.json"
        record.write_text(
            json.dumps(
                {
                    "EXECUTION_APPROVAL_CONSUMED": True,
                    "execution_packet_sha256": SYNTHETIC_SHA,
                    "actual_provider_requests": 1,
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner, "EXECUTION_RECORD_V5", record)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, transport)
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"
        assert transport.calls == []


# ================================================================== what arrived is kept


class TestWhatArrivedIsKept:
    def _artifact(self, runner, fx, transport, context: dict | None = None):
        result, context = _run(runner, fx, transport, context)
        report = runner.validate_execution(result, context)
        return runner.build_artifact(result, report), result, report

    # -- the terminal paths --------------------------------------------------------------------

    def test_retention_on_a_complete_response(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "tool_use"))
        )
        assert report["stages"]["3_provider_completion"] == "PASSED"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert isinstance(artifact["RAW_PROVIDER_RESPONSE_BODY"], dict)
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_JUDGED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_an_output_limit_stop(self, runner, fx, approved):
        partial = {"decision": "FORM_HYPOTHESIS", "subject": "cut off here"}
        artifact, result, _ = self._artifact(
            runner, fx, ScriptedTransport(body=_body(partial, "max_tokens"))
        )
        assert result["failure"] is not None
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["STOP_REASON"] == "max_tokens"
        assert artifact["PROVIDER_COMPLETION"] == "OUTPUT_LIMIT_REACHED"
        assert artifact["PARSED_OUTPUT_JUDGED"] is False
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_timeout(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(raises=TimeoutError("synthetic timeout"))
        )
        assert report["outcome"] == "EXECUTION_FAILED_TIMEOUT_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is False
        assert artifact["RAW_PROVIDER_RESPONSE_BODY"] == "NOT_AVAILABLE"
        assert artifact["transport_errors"]
        assert artifact["TERMINAL_OUTCOME"] == "EXECUTION_FAILED_TIMEOUT_NO_RETRY"

    def test_retention_on_a_provider_refusal(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "refusal"))
        )
        assert report["outcome"] == "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["STOP_REASON"] == "refusal"
        assert artifact["PARSED_OUTPUT_JUDGED"] is False

    def test_retention_on_an_unsupported_stop_reason(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "end_turn"))
        )
        assert report["outcome"] == "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["STOP_REASON"] == "end_turn"
        assert artifact["PARSED_OUTPUT_JUDGED"] is False

    def test_retention_on_a_parse_failure(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(None, "tool_use"))
        )
        assert report["failed_stage"] == "4_structured_output_parse"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_RETAINED"] is False

    def test_retention_on_a_schema_failure(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(_required_keys_only(), "tool_use"))
        )
        assert report["failed_stage"] == "5_schema_validation_v1_1_0"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_semantic_failure(self, runner, fx, approved):
        answer = fx.with_statement(
            "Notices under CPV class 7777 state amounts in EUR or in another currency.", OBSERVED
        )
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(answer, "tool_use"))
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_SEMANTIC_GATE_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_JUDGED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_provenance_failure(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner,
            fx,
            ScriptedTransport(body=_body(fx.good_output(), "tool_use"), headers={"request-id": ""}),
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_ATTRIBUTION_NO_RETRY"
        assert report["failed_stage"] == "8_attribution_and_provenance"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_persistence_eligibility_failure(self, runner, fx, approved):
        guarded = "Profitability Review (synthetic register)"
        summary = fx.good_output()[SUMMARY].replace(fx.SHORT_NAME, "Profitability Review")
        context = _context(
            fx, supplied=fx.statements(name=guarded), names=fx.metadata(name=guarded)
        )
        artifact, _, report = self._artifact(
            runner,
            fx,
            ScriptedTransport(body=_body(fx.good_output(**{SUMMARY: summary}), "tool_use")),
            context,
        )
        assert report["failed_stage"] == "9_persistence_eligibility"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_human_review_ready_success(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "tool_use"))
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
        assert report["stages"]["9_persistence_eligibility"] == "ELIGIBLE_FOR_HUMAN_REVIEW_ONLY"
        assert report["stages"]["10_human_review"] == "REQUIRED_NOT_PERFORMED"
        assert report["provenance"]["provider_request_id"] == REQUEST_ID
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    # -- the properties every path keeps --------------------------------------------------------

    def test_usage_is_retained_from_the_response_when_the_gateway_refused(
        self, runner, fx, approved
    ):
        partial = {"decision": "FORM_HYPOTHESIS"}
        artifact, result, _ = self._artifact(
            runner, fx, ScriptedTransport(body=_body(partial, "max_tokens", usage=(4321, 1234)))
        )
        assert result["failure"] is not None
        assert artifact["USAGE_FROM_RESPONSE"] == {"input_tokens": 4321, "output_tokens": 1234}
        assert artifact["USAGE_RETAINED"] is True

    def test_the_request_id_is_retained(self, runner, fx, approved):
        artifact, _, _ = self._artifact(
            runner, fx, ScriptedTransport(body=_body(None, "max_tokens"))
        )
        assert artifact["PROVIDER_REQUEST_ID"] == REQUEST_ID

    def test_raw_and_parsed_digests_are_retained(self, runner, fx, approved):
        artifact, _, _ = self._artifact(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "tool_use"))
        )
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["RAW_PROVIDER_RESPONSE_SHA256"])
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["PARSED_OUTPUT_SHA256"])

    def test_the_cost_is_retained_from_telemetry(self, runner, fx, approved):
        artifact, _, _ = self._artifact(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "tool_use"))
        )
        assert '"cost_units"' in json.dumps(artifact)

    def test_the_stage_table_is_retained(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "tool_use"))
        )
        assert artifact["validation"]["stages"] == report["stages"]

    def test_the_terminal_outcome_is_retained(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(None, "max_tokens"))
        )
        assert artifact["TERMINAL_OUTCOME"] == report["outcome"] == artifact["OUTCOME"]
        assert artifact["execution_packet_id"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V5"

    def test_a_volunteered_reasoning_block_is_stripped(self, runner, fx, approved):
        body = _body(
            None,
            "max_tokens",
            extra_blocks=({"type": "thinking", "thinking": "hidden reasoning text"},),
        )
        body["reasoning"] = "hidden reasoning text"
        artifact, _, _ = self._artifact(runner, fx, ScriptedTransport(body=body))
        assert "hidden reasoning text" not in json.dumps(artifact["RAW_PROVIDER_RESPONSE_BODY"])
        assert artifact["HIDDEN_REASONING_RETAINED"] is False

    def test_a_credential_shape_is_redacted_from_the_body(self, runner, fx, approved):
        leaked = "echoed key sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAA"
        body = _body(None, "max_tokens", extra_blocks=({"type": "text", "text": leaked},))
        artifact, _, _ = self._artifact(runner, fx, ScriptedTransport(body=body))
        written = json.dumps(artifact)
        assert "sk-ant-api03" not in written
        assert "[REDACTED]" in written

    def test_no_fixture_constructs_the_real_transport(self, runner, fx, approved, monkeypatch):
        import sros_llm_gateway.transport as transport_module

        built: list[int] = []
        original = transport_module.UrllibTransport.__init__

        def tripwire(self, *a, **k):  # pragma: no cover - must never run
            built.append(1)
            return original(self, *a, **k)

        monkeypatch.setattr(transport_module.UrllibTransport, "__init__", tripwire)
        self._artifact(runner, fx, ScriptedTransport(body=_body(None, "max_tokens")))
        assert built == []

    def test_the_fail_safe_keeps_the_bytes_when_judging_fails(
        self, runner, fx, approved, monkeypatch
    ):
        result, context = _run(runner, fx, ScriptedTransport(body=_body(None, "max_tokens")))

        def broken(*args, **kwargs):
            raise RuntimeError("synthetic failure after the call")

        monkeypatch.setattr(runner, "validate_execution", broken)
        report, text = runner.settle(result, context)
        kept = json.loads(text)
        assert report["outcome"] == runner.POST_CALL_FAILURE
        assert kept["POST_CALL_HANDLING_FAILED"] is True
        assert kept["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert kept["transport_responses"][0]["body"]["stop_reason"] == "max_tokens"
        assert kept["execution_packet_id"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V5"
        assert kept["PERSISTED"] == "NOTHING"
