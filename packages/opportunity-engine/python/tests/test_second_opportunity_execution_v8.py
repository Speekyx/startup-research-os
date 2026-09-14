"""Mission 1.84.20. Execution packet V8's runner: V7's request, byte for byte, under a hard cost
ceiling proven from documented bounds, with both disclosed risks left to the operator.

Every V7 runner test is kept and runs against V8's runner, because V8 changes nothing a provider
would see. What V8 adds is defended below them, with synthetic transports and never with a network.

THE TOOL IS STRICT, AT ITS TOP LEVEL, and its schema is the frozen projection.

STAGE 5 IS STILL THE FULL CONTRACT, and an extra root property is refused there if it arrives.

THE PROMPT SENT IS v1.5.0, and the completion signal still outranks the content, with one request.

STAGES 6 TO 9 EACH REFUSE AT THEIR OWN STAGE, with the real machinery.

NO APPROVAL, NO TRANSPORT; an approval must decide BOTH risks, and accept both, or nothing is sent.

V1 TO V6 ARE REFUSED AS SPENT AND V7 AS SUPERSEDED, each under its own name; an unseen digest is not.

THE BODY IS V7'S BYTES, selects no billing category the ceiling does not cover, and the ceiling is
computed from documented bounds, apart from the planning estimate and never from it.

WHAT ARRIVED IS KEPT on each terminal path, and when judging fails.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"
RUNNER_PATH = SCRIPTS / "run_second_opportunity_execution_v8.py"
RUNNER_V7_PATH = SCRIPTS / "run_second_opportunity_execution_v7.py"
BOUNDED_GATE_PATH = SCRIPTS / "render_second_opportunity_bounded_contract.py"
FIXTURES_PATH = SCRIPTS / "second_opportunity_synthetic_fixtures.py"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
V3_SHA256 = "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2"
V4_SHA256 = "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b"
V5_SHA256 = "da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a"
V6_SHA256 = "969128dd2453ab2a6907335d9386c9c3f3fac991db91c674b151c9db777aa8a9"
V7_SHA256 = "51023d0d2ed780db4c7d5018a289939e7c9c83061f8768051ef1cd7b8ae674e8"
V7_BODY_SHA256 = "58956019f78f414ee11392bee5e99eedda4eb1b4deb20d3f20219dfc60739842"
PROJECTION_SHA256 = "87028f451205494a948e83740e73b9ca59ce3243f54e24c123b7cc2354c69783"
CANONICAL_SHA256 = "7d67bad3df06691ba46a4dcc65cbf186bc5825a87719e985637aec68640e1b66"
SYNTHETIC_SHA = "d" * 64
STRUCTURED_TOOL_NAME = "emit_structured_output"
REQUEST_ID = "req_synthetic_v8"
SUMMARY = "evidence_bound_reasoning_summary"
OBSERVED = "OBSERVED_OR_EVIDENCE_SUPPORTED"
MISSING = object()


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def runner():
    return _module("runner_v8_under_test", RUNNER_PATH)


@pytest.fixture(scope="module")
def bounded():
    return _module("bounded_gate_for_runner_v8_tests", BOUNDED_GATE_PATH)


@pytest.fixture(scope="module")
def fx():
    return _module("fixtures_for_runner_v8_tests", FIXTURES_PATH)


def _packet_file(sha: str = SYNTHETIC_SHA) -> dict:
    return {
        "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V8",
        "EXECUTION_PACKET_VERSION": 8,
        "EXECUTION_PACKET_SHA256": sha,
        "MODEL_ID": "claude-sonnet-5",
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
    from sros_opportunity.second_opportunity_prompt_v1_5 import (
        render_second_opportunity_prompt_v1_5,
    )

    return render_second_opportunity_prompt_v1_5(
        fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
    )


def _schema_valid_output(bounded) -> dict:
    from sros_opportunity.second_opportunity_schema_v1_2 import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    )

    output = bounded.maximum_instance(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2, bounded.ASCII_FILL)
    output["decision"] = "FORM_HYPOTHESIS"
    return output


def _required_keys_only() -> dict:
    from sros_opportunity.second_opportunity_schema_v1_2 import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    )

    return {key: "x" for key in SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2["required"]}


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

        self.calls.append(
            {
                "url": url,
                "header_names": sorted(str(k).lower() for k in headers),
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
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
        "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V8",
        "EXECUTION_PACKET_VERSION": 8,
        "EXECUTION_PACKET_SHA256": SYNTHETIC_SHA,
        "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
        "approved_by": "synthetic operator",
        "operator_statement": "a synthetic approval, for a test",
        "recorded_by": "mission-9.9.9",
        "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8": True,
        "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8": True,
    }
    base.update(overrides)
    return base


@pytest.fixture
def approved(runner, tmp_path, monkeypatch):
    path = tmp_path / "approval-v8.json"
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


def _built_body(runner, fx) -> dict:
    return runner.request_body(render_parts(fx), _packet_file())


# ================================================================== the tool is strict


class TestTheToolIsStrictAtItsTopLevel:
    def test_the_sent_tool_carries_strict_beside_its_schema(self, runner, fx, approved):
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, fx, transport)
        tool = transport.calls[0]["body"]["tools"][0]
        assert list(tool) == ["name", "description", "strict", "input_schema"]
        assert tool["strict"] is True
        assert '"strict"' not in json.dumps(tool["input_schema"])

    def test_the_sent_tool_schema_is_the_frozen_projection(self, runner, fx, approved):
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, fx, transport)
        schema = transport.calls[0]["body"]["tools"][0]["input_schema"]
        assert _sha(schema) == PROJECTION_SHA256
        assert _sha(schema) != CANONICAL_SHA256
        sent = json.dumps(schema)
        for keyword in ('"maxLength"', '"minLength"', '"maxItems"', '"pattern"'):
            assert keyword not in sent
        assert schema["additionalProperties"] is False

    def test_no_beta_header_rides_along(self, runner, fx, approved):
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, fx, transport)
        assert "anthropic-beta" not in transport.calls[0]["header_names"]

    def test_tool_choice_still_forces_the_one_tool(self, runner, fx):
        body = _built_body(runner, fx)
        assert body["tool_choice"] == {"type": "tool", "name": STRUCTURED_TOOL_NAME}
        assert len(body["tools"]) == 1
        assert "output_config" not in body

    def test_the_built_body_has_no_strict_tool_problem(self, runner, fx):
        assert runner.strict_tool_problems(_built_body(runner, fx)) == []

    @pytest.mark.parametrize(
        "drift",
        ["not_strict", "strict_inside_the_schema", "the_full_schema", "auto_choice", "extra_key"],
    )
    def test_every_strict_tool_drift_is_named(self, runner, fx, drift):
        from sros_opportunity.second_opportunity_schema_v1_2 import (
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
        )

        body = json.loads(json.dumps(_built_body(runner, fx)))
        tool = body["tools"][0]
        if drift == "not_strict":
            tool["strict"] = False
        elif drift == "strict_inside_the_schema":
            tool["input_schema"]["strict"] = True
        elif drift == "the_full_schema":
            tool["input_schema"] = json.loads(json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2))
        elif drift == "auto_choice":
            body["tool_choice"] = {"type": "auto"}
        else:
            tool["cache_control"] = {"type": "ephemeral"}
        assert runner.strict_tool_problems(body) != []

    @pytest.mark.parametrize(
        ("key", "code"),
        [
            ("PROVIDER_STRICT_SCHEMA_SHA256", "STRICT_PROJECTION_MOVED"),
            ("STRICT_CAPABILITY_PROFILE_SHA256", "STRICT_CAPABILITY_PROFILE_MOVED"),
        ],
    )
    def test_a_moved_projection_or_profile_is_refused_before_a_body_exists(
        self, runner, fx, monkeypatch, key, code
    ):
        monkeypatch.setitem(runner.EXPECTED, key, "0" * 64)
        with pytest.raises(runner.RefusedError) as refusal:
            _built_body(runner, fx)
        assert refusal.value.code == code

    def test_the_adapter_is_the_strict_one(self, runner):
        from sros_llm_gateway.providers.anthropic_strict import AnthropicStrictToolProvider

        provider = runner.build_provider(
            _packet_file(), runner._NoSend(), api_key="synthetic-not-a-credential"
        )
        assert type(provider) is AnthropicStrictToolProvider


# ================================================================== stage 5 is the full contract


class TestStage5IsStillTheFullContract:
    @pytest.mark.parametrize("extra", ["parameter name", "unexpected"])
    def test_an_extra_root_property_is_refused_at_stage_5_and_kept_whole(
        self, runner, fx, approved, extra
    ):
        output = fx.good_output()
        output[extra] = "value"
        result, context = _run(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        report = runner.validate_execution(result, context)
        assert report["failed_stage"] == "5_schema_validation_v1_2_0"
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY"
        assert report["reasons"] == [
            f"<root>: unknown field {extra!r}; additionalProperties is false"
        ]
        assert _not_reached_after(runner, report, "5_schema_validation_v1_2_0")
        artifact = runner.build_artifact(result, report)
        assert artifact["parsed_output"][extra] == "value"
        assert artifact["PERSISTED"] == "NOTHING"

    def test_a_bound_the_projection_does_not_carry_is_refused_at_stage_5(
        self, runner, fx, approved
    ):
        projection = runner.strict_input_schema()
        assert "maxLength" not in projection["properties"]["candidate_intervention_class"]
        output = fx.good_output(candidate_intervention_class="x" * 301)
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        assert report["failed_stage"] == "5_schema_validation_v1_2_0"
        assert any("maxLength 300" in reason for reason in report["reasons"])

    def test_the_stage_function_validates_against_the_full_schema(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        assert "schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)" in source
        assert source.count("schema_violations(") == 1

    def test_the_runner_names_no_key_an_earlier_answer_carried(self):
        assert "parameter name" not in RUNNER_PATH.read_text(encoding="utf-8")


# ================================================================== the prompt sent


class TestThePromptSentIsVersion150:
    def test_the_request_carries_the_semantic_block_and_the_source_names(
        self, runner, fx, approved
    ):
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, fx, transport)
        sent = json.dumps(transport.calls[0]["body"])
        assert "SEMANTIC RULES THE ANSWER IS AUDITED AGAINST." in sent
        assert "SOURCE NAMES ARE PROVENANCE, NEVER EVIDENCE." in sent
        assert f"{SUMMARY}\\n    at most 1500 characters" in sent
        assert f"{SUMMARY}: generation target 1200 characters; hard maximum 1500 characters" in sent

    def test_no_schema_bound_and_no_class_a_semantic_rule_is_left_unstated(self, runner, fx):
        parts = render_parts(fx)
        assert runner.unstated_constraints(parts.system_instructions) == []
        assert runner.unstated_semantic_rules(parts) == []
        assert runner.unstated_targets(parts) == []

    def test_the_contract_checks_refuse_prompt_v1_4_under_schema_v1_2(self, runner, fx):
        from sros_opportunity.second_opportunity_prompt_v1_4 import (
            render_second_opportunity_prompt_v1_4,
        )

        v1_4 = render_second_opportunity_prompt_v1_4(
            fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
        )
        assert runner.unstated_targets(v1_4) == [SUMMARY]

    def test_the_request_names_prompt_1_5_0_and_carries_the_projection(self, runner, fx):
        request = runner.build_request(render_parts(fx), _packet_file())
        assert request.prompt_template_version == "1.5.0"
        assert _sha(request.response_schema) == PROJECTION_SHA256


# ================================================================== the schema still decides


class TestTheSchemaStillDecides:
    def test_a_class_over_its_target_and_within_its_bound_passes_stage_5(
        self, runner, fx, bounded, approved
    ):
        output = _schema_valid_output(bounded)
        output["candidate_intervention_class"] = "x" * 241
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        assert report["stages"]["5_schema_validation_v1_2_0"] == "PASSED"

    def test_a_summary_at_the_bound_passes_stage_5(self, runner, fx, bounded, approved):
        output = _schema_valid_output(bounded)
        output[SUMMARY] = "x" * 1500
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        assert report["stages"]["5_schema_validation_v1_2_0"] == "PASSED"

    def test_a_summary_one_over_is_refused_at_stage_5_and_kept_whole(
        self, runner, fx, bounded, approved
    ):
        output = _schema_valid_output(bounded)
        output[SUMMARY] = "x" * 1501
        result, context = _run(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        report = runner.validate_execution(result, context)
        assert report["reasons"] == [f"{SUMMARY}: 1501 characters exceeds maxLength 1500"]
        artifact = runner.build_artifact(result, report)
        assert len(artifact["parsed_output"][SUMMARY]) == 1501
        assert artifact["PERSISTED"] == "NOTHING"

    def test_a_long_summary_within_the_bound_reaches_stage_9(self, runner, fx, approved):
        summary = " ".join([fx.good_output()[SUMMARY]] * 5)
        assert 900 < len(summary) <= 1500
        output = fx.good_output(**{SUMMARY: summary})
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        assert report["outcome"] == "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
        assert report["stages"]["9_persistence_eligibility"] == "ELIGIBLE_FOR_HUMAN_REVIEW_ONLY"

    def test_a_semantic_violation_in_a_long_summary_is_refused_at_stage_6(
        self, runner, fx, approved
    ):
        summary = " ".join([fx.good_output()[SUMMARY]] * 5) + " Buyers are willing to pay."
        output = fx.good_output(**{SUMMARY: summary})
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(output, "tool_use")))
        assert report["stages"]["5_schema_validation_v1_2_0"] == "PASSED"
        assert report["failed_stage"] == "6_semantic_output_gate_v1_4_0"
        assert _not_reached_after(runner, report, "6_semantic_output_gate_v1_4_0")


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
        assert report["stages"]["5_schema_validation_v1_2_0"] == "NOT_REACHED"

    @pytest.mark.parametrize("stop_reason", ["end_turn", "pause_turn", None, "a_value_added_later"])
    def test_an_unknown_stop_reason_fails_closed(self, runner, fx, approved, stop_reason):
        report, _ = _report(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), stop_reason))
        )
        assert report["outcome"] == "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY"
        assert report["failed_stage"] == "3_provider_completion"

    def test_a_refusal_stop_is_refused_before_any_parse(self, runner, fx, approved):
        """Strict decoding does not hold on a refusal, and the provider says so: stage 3 decides."""
        report, _ = _report(runner, fx, ScriptedTransport(body=_body(fx.good_output(), "refusal")))
        assert report["outcome"] == "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY"
        assert report["stages"]["4_structured_output_parse"] == "NOT_REACHED"

    def test_a_provider_error_status_fails_at_transport(self, runner, fx, approved):
        report, _ = _report(
            runner, fx, ScriptedTransport(status=400, body={"error": {"message": "too complex"}})
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

    def test_exactly_one_request_on_a_timeout(self, runner, fx, approved):
        transport = ScriptedTransport(raises=TimeoutError("synthetic compilation wait"))
        report, _ = _report(runner, fx, transport)
        assert len(transport.calls) == 1
        assert report["outcome"] == "EXECUTION_FAILED_TIMEOUT_NO_RETRY"

    def test_the_request_disables_thinking_and_asks_for_128000(self, runner, fx, approved):
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, fx, transport)
        sent = transport.calls[0]
        assert sent["body"]["thinking"] == {"type": "disabled"}
        assert sent["body"]["max_tokens"] == 128000
        assert sent["body"]["model"] == "claude-sonnet-5"
        assert sent["timeout_seconds"] == 60.0
        assert sent["url"] == "https://api.anthropic.com/v1/messages"

    def test_the_runner_source_has_one_call_site_and_no_loop(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        assert source.count("gateway.complete(") == 1
        assert re.search(r"^\s*while\b", source, re.MULTILINE) is None
        assert "count_tokens" not in source


# ================================================================== stage 6 is gate v1.4.0


class TestStage6IsGate140AndCannotBeReplaced:
    def test_the_stage_function_takes_no_gate(self, runner):
        assert list(inspect.signature(runner.validate_execution).parameters) == [
            "result",
            "context",
        ]

    def test_the_stages_are_v6s_and_strict_is_not_one(self, runner):
        assert runner.STAGES[4] == "5_schema_validation_v1_2_0"
        assert runner.STAGES[5] == "6_semantic_output_gate_v1_4_0"
        assert len(runner.STAGES) == 10
        assert not any("strict" in stage for stage in runner.STAGES)


# ================================================================== stages 6 to 9, real machinery


class TestEachStageRefusesAtItsOwnStage:
    def test_a_valid_answer_reaches_stage_9_eligible_for_review_only(self, runner, fx):
        report = runner.validate_execution(
            fx.recorded_result(fx.good_output()), fx.runner_context()
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
        assert report["stages"]["10_human_review"] == "REQUIRED_NOT_PERFORMED"
        assert report["persistence_eligibility"]["persisted"] is False

    def test_a_semantic_failure_stops_at_6(self, runner, fx):
        answer = fx.with_statement(
            "Notices under CPV class 7777 state amounts in EUR or in another currency.", OBSERVED
        )
        report = runner.validate_execution(fx.recorded_result(answer), fx.runner_context())
        assert report["failed_stage"] == "6_semantic_output_gate_v1_4_0"

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

    def test_an_empty_request_id_stops_at_8(self, runner, fx):
        report = runner.validate_execution(
            fx.recorded_result(fx.good_output(), request_id=""), fx.runner_context()
        )
        assert report["failed_stage"] == "8_attribution_and_provenance"

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

    def test_the_committed_approval_file_does_not_exist(self, runner):
        assert not runner.APPROVAL_FILE.exists()

    @pytest.mark.parametrize(
        ("override", "code"),
        [
            ({"EXECUTION_PACKET_SHA256": "e" * 64}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
            ({"EXECUTION_PACKET_VERSION": 6}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
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

    def test_a_v6_approval_does_not_authorise_v8(self, runner, fx, tmp_path, monkeypatch):
        path = tmp_path / "approval.json"
        path.write_text(
            json.dumps(
                _approval(
                    EXECUTION_PACKET_ID="SECOND-OPPORTUNITY-SYNTH-EXEC-V6",
                    EXECUTION_PACKET_VERSION=6,
                    EXECUTION_PACKET_SHA256=V6_SHA256,
                )
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, ScriptedTransport(body=_body(None, "tool_use")))
        assert refusal.value.code == "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"

    @pytest.mark.parametrize(
        "spent",
        [V1_SHA256, V2_SHA256, V3_SHA256, V4_SHA256, V5_SHA256, V6_SHA256],
        ids=["V1", "V2", "V3", "V4", "V5", "V6"],
    )
    def test_a_spent_digest_cannot_run_under_v8(self, runner, fx, tmp_path, monkeypatch, spent):
        """Even with an approval naming it, the consumed-approval guard refuses a spent digest."""
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(_approval(EXECUTION_PACKET_SHA256=spent)), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, transport, _context(fx, spent))
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"
        assert transport.calls == []

    def test_an_unseen_digest_is_not_refused_because_v1_to_v6_are_spent(self, runner):
        runner.refuse_if_consumed("0" * 64)
        runner.refuse_if_consumed(SYNTHETIC_SHA)

    def test_v8s_own_record_refuses_its_digest_once_spent(self, runner, fx, approved, monkeypatch):
        record = approved.parent / "record-v8.json"
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
        monkeypatch.setattr(runner, "EXECUTION_RECORD_V8", record)
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
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_JUDGED"] is True
        assert artifact["PROVIDER_STRICT_MODE"] is True
        assert artifact["PROVIDER_STRICT_SCHEMA_SHA256"] == PROJECTION_SHA256
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_an_output_limit_stop(self, runner, fx, approved):
        partial = {"decision": "FORM_HYPOTHESIS", "subject": "cut off here"}
        artifact, result, _ = self._artifact(
            runner, fx, ScriptedTransport(body=_body(partial, "max_tokens"))
        )
        assert result["failure"] is not None
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["STOP_REASON"] == "max_tokens"
        assert artifact["PARSED_OUTPUT_JUDGED"] is False
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_timeout(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(raises=TimeoutError("synthetic timeout"))
        )
        assert report["outcome"] == "EXECUTION_FAILED_TIMEOUT_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_BODY"] == "NOT_AVAILABLE"
        assert artifact["transport_errors"]

    def test_retention_on_a_provider_refusal(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "refusal"))
        )
        assert report["outcome"] == "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_JUDGED"] is False

    def test_retention_on_an_unsupported_stop_reason(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "end_turn"))
        )
        assert report["outcome"] == "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY"
        assert artifact["STOP_REASON"] == "end_turn"

    def test_retention_on_a_parse_failure(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(None, "tool_use"))
        )
        assert report["failed_stage"] == "4_structured_output_parse"
        assert artifact["PARSED_OUTPUT_RETAINED"] is False

    def test_retention_on_a_schema_failure(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(_required_keys_only(), "tool_use"))
        )
        assert report["failed_stage"] == "5_schema_validation_v1_2_0"
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
        assert artifact["PARSED_OUTPUT_JUDGED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_provenance_failure(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner,
            fx,
            ScriptedTransport(body=_body(fx.good_output(), "tool_use"), headers={"request-id": ""}),
        )
        assert report["failed_stage"] == "8_attribution_and_provenance"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True

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
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_human_review_ready_success(self, runner, fx, approved):
        artifact, _, report = self._artifact(
            runner, fx, ScriptedTransport(body=_body(fx.good_output(), "tool_use"))
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
        assert report["stages"]["10_human_review"] == "REQUIRED_NOT_PERFORMED"
        assert report["provenance"]["provider_request_id"] == REQUEST_ID
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
        assert artifact["execution_packet_id"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V8"

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
        assert kept["transport_responses"][0]["body"]["stop_reason"] == "max_tokens"
        assert kept["execution_packet_id"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V8"
        assert kept["PERSISTED"] == "NOTHING"


# ================================================================== V8's governance


def _v7_runner():
    return _module("runner_v7_for_runner_v8_tests", RUNNER_V7_PATH)


class TestV1ToV6SpentAndV7Superseded:
    @pytest.mark.parametrize(
        "spent",
        [V1_SHA256, V2_SHA256, V3_SHA256, V4_SHA256, V5_SHA256, V6_SHA256],
        ids=["V1", "V2", "V3", "V4", "V5", "V6"],
    )
    def test_a_spent_digest_keeps_its_name_through_v7s_guard(self, runner, spent):
        with pytest.raises(runner.RefusedError) as refusal:
            runner.refuse_if_consumed(spent)
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"

    def test_v7_is_refused_as_superseded_and_never_as_consumed(self, runner):
        with pytest.raises(runner.RefusedError) as refusal:
            runner.refuse_if_consumed(V7_SHA256)
        assert refusal.value.code == "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
        assert "EXECUTION_APPROVAL_ALREADY_CONSUMED" not in str(refusal.value)

    def test_v7_cannot_run_under_v8_even_with_an_approval_naming_it(
        self, runner, fx, tmp_path, monkeypatch
    ):
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(_approval(EXECUTION_PACKET_SHA256=V7_SHA256)), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, transport, _context(fx, V7_SHA256))
        assert refusal.value.code == "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
        assert transport.calls == []

    def test_a_v7_approval_does_not_authorise_v8(self, runner, fx, tmp_path, monkeypatch):
        path = tmp_path / "approval.json"
        path.write_text(
            json.dumps(
                _approval(
                    EXECUTION_PACKET_ID="SECOND-OPPORTUNITY-SYNTH-EXEC-V7",
                    EXECUTION_PACKET_VERSION=7,
                    EXECUTION_PACKET_SHA256=V7_SHA256,
                )
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, transport)
        assert refusal.value.code == "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"
        assert transport.calls == []

    def test_the_v7_runner_itself_refuses_v7_before_any_transport(self, monkeypatch):
        import sros_llm_gateway.transport as transport_module

        v7 = _v7_runner()
        built: list[int] = []
        original = transport_module.UrllibTransport.__init__

        def tripwire(self, *a, **k):  # pragma: no cover - must never run
            built.append(1)
            return original(self, *a, **k)

        monkeypatch.setattr(transport_module.UrllibTransport, "__init__", tripwire)
        with pytest.raises(v7.RefusedError) as refusal:
            v7.execute({"packet_file": {"EXECUTION_PACKET_SHA256": V7_SHA256}, "parts": None})
        assert refusal.value.code == "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
        assert built == []

    def test_the_v8_runner_needs_v7s_supersession_to_be_recorded(
        self, runner, monkeypatch, tmp_path
    ):
        """Without the record, V7's guard would let V7 through, and V8's verification refuses it."""
        v7 = _v7_runner()
        monkeypatch.setattr(v7, "SUPERSESSION_RECORD", tmp_path / "absent.json")
        v7.refuse_if_consumed(V7_SHA256)
        monkeypatch.setattr(runner, "v7_runner", lambda: v7)
        runner.refuse_if_consumed(V7_SHA256)
        source = RUNNER_PATH.read_text(encoding="utf-8")
        assert "V7_SUPERSESSION_GUARD_INACTIVE" in source


class TestAnApprovalMustDecideBothRisks:
    @pytest.mark.parametrize(
        "key",
        [
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8",
            "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8",
        ],
    )
    @pytest.mark.parametrize("value", [None, "yes", 1, "true"])
    def test_an_approval_that_does_not_decide_a_risk_is_incomplete(
        self, runner, fx, tmp_path, monkeypatch, key, value
    ):
        approval = _approval()
        if value is None:
            approval.pop(key)
        else:
            approval[key] = value
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(approval), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, transport)
        assert refusal.value.code == "OPERATOR_APPROVAL_INCOMPLETE"
        assert key in str(refusal.value)
        assert transport.calls == []

    @pytest.mark.parametrize(
        ("key", "code"),
        [
            (
                "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8",
                "RESIDUAL_SEMANTIC_LIMITATION_NOT_ACCEPTED",
            ),
            (
                "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8",
                "STRICT_FIRST_REQUEST_TIMEOUT_RISK_NOT_ACCEPTED",
            ),
        ],
    )
    def test_an_approval_that_refuses_a_risk_executes_nothing(
        self, runner, fx, tmp_path, monkeypatch, key, code
    ):
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(_approval(**{key: False})), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, transport)
        assert refusal.value.code == code
        assert transport.calls == []

    def test_an_approval_deciding_both_risks_reaches_the_one_request(self, runner, fx, approved):
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, fx, transport)
        assert len(transport.calls) == 1

    def test_the_packet_accepts_neither_risk(self, runner):
        packet = json.loads(runner.PACKET_FILE.read_text(encoding="utf-8"))
        for key in runner.RISK_DECISIONS:
            assert packet[key] is False
            assert runner.EXPECTED[key] is False
        assert packet["TIMEOUT"]["STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8"] is False


class TestTheBodyIsV7sAndTheCeilingIsProven:
    def test_the_body_is_v7s_bytes(self, runner, fx):
        v7 = _v7_runner()
        parts = render_parts(fx)
        mine = json.dumps(runner.request_body(parts, _packet_file()))
        theirs = json.dumps(v7.request_body(parts, _packet_file()))
        assert mine == theirs

    def test_the_committed_body_identity_is_v7s(self, runner):
        packet = json.loads(runner.PACKET_FILE.read_text(encoding="utf-8"))
        assert packet["REQUEST_BODY_SHA256"] == runner.EXPECTED["REQUEST_BODY_SHA256"]
        assert packet["REQUEST_BODY_SHA256"] == V7_BODY_SHA256
        assert packet["REQUEST_BODY_DIFFERENTIAL"]["REQUEST_BODY_DIFFERENCES_V7_TO_V8"] == 0
        assert packet["REQUEST_BODY_DIFFERENTIAL"]["byte_identical"] is True

    def test_the_body_selects_no_billing_category_the_ceiling_leaves_out(self, runner, fx):
        body = _built_body(runner, fx)
        assert runner.billing_selectors(body) == runner.COST_SELECTORS_REQUIRED

    @pytest.mark.parametrize(
        ("change", "selector"),
        [
            (
                lambda b: b["tools"][0].__setitem__("cache_control", {"type": "ephemeral"}),
                "cache_control",
            ),
            (lambda b: b.__setitem__("cache_control", {"type": "ephemeral"}), "cache_control"),
            (lambda b: b.__setitem__("inference_geo", "us"), "inference_geo"),
            (lambda b: b.__setitem__("service_tier", "auto"), "service_tier"),
            (lambda b: b.__setitem__("speed", "fast"), "speed"),
            (
                lambda b: b["tools"].append({"type": "web_search_20260209", "name": "web_search"}),
                "server_tools",
            ),
        ],
    )
    def test_a_body_that_selects_another_category_is_seen(self, runner, fx, change, selector):
        body = json.loads(json.dumps(_built_body(runner, fx)))
        change(body)
        selectors = runner.billing_selectors(body)
        assert selectors[selector] != runner.COST_SELECTORS_REQUIRED[selector]

    def test_the_ceiling_and_the_estimate_are_computed_apart(self, runner):
        from decimal import Decimal

        from sros_llm_gateway.pricing import ModelPrice

        price = ModelPrice(input_per_1k=0.002, output_per_1k=0.01)
        packet = {key: runner.EXPECTED[key] for key in runner.EXPECTED}
        hard, planning = runner.cost_bounds(price, packet)
        assert (
            runner.decimal_text(hard) == "3.608" == runner.EXPECTED["HARD_EXECUTION_COST_CEILING"]
        )
        assert (
            runner.decimal_text(planning) == "1.316316" == runner.EXPECTED["PLANNING_COST_ESTIMATE"]
        )
        assert planning < hard
        assert hard == (Decimal(1000000) / 1000 * Decimal("0.002") + Decimal("1.28")) * Decimal(
            "1.1"
        )

    def test_the_ceiling_does_not_move_with_the_estimate(self, runner):
        from sros_llm_gateway.pricing import ModelPrice

        price = ModelPrice(input_per_1k=0.002, output_per_1k=0.01)
        packet = {key: runner.EXPECTED[key] for key in runner.EXPECTED}
        hard, _ = runner.cost_bounds(price, packet)
        packet["PLANNING_INPUT_TOKEN_ESTIMATE"] = 12903
        again, planning = runner.cost_bounds(price, packet)
        assert again == hard
        assert runner.decimal_text(planning) != "1.316316"
        packet["MAX_BILLABLE_INPUT_TOKENS"] = 18158
        smaller, _ = runner.cost_bounds(price, packet)
        assert smaller < hard

    def test_expected_pins_the_committed_packet_and_records(self, runner):
        packet = json.loads(runner.PACKET_FILE.read_text(encoding="utf-8"))
        assert packet["EXECUTION_PACKET_SHA256"] == runner.EXPECTED["EXECUTION_PACKET_SHA256"]
        for path, key in (
            (runner.COST_CEILING_RECORD, "COST_CEILING_RECORD_SHA256"),
            (runner.V7_SUPERSESSION_RECORD, "V7_SUPERSESSION_RECORD_SHA256"),
        ):
            text = path.read_text(encoding="utf-8")
            assert hashlib.sha256(text.encode("utf-8")).hexdigest() == runner.EXPECTED[key]
        for key in ("INPUT_TOKEN_ESTIMATE", "WORST_CASE_CALL_COST", "EXECUTION_COST_CEILING"):
            assert key not in packet
            assert key not in runner.EXPECTED

    def test_the_timeout_is_unchanged(self, runner):
        assert runner.EXPECTED["REQUEST_TIMEOUT"] == 60.0
        packet = json.loads(runner.PACKET_FILE.read_text(encoding="utf-8"))
        assert packet["REQUEST_TIMEOUT"] == 60.0
        assert packet["TIMEOUT"]["TIMEOUT_CHANGED_BY_THIS_MISSION"] is False
