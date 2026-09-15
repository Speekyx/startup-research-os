"""Mission 1.84.23. Execution packet V10's runner: V9's request with prompt v1.6.0, and nothing else
changed.

Every V9 runner test is kept and runs against V10's runner, the prompt now v1.6.0 where a test renders
one. What V10 adds is defended below them, with synthetic transports and never with a network.

THE TOOL IS STRICT, AT ITS TOP LEVEL, and its schema is the frozen projection.

STAGE 5 IS STILL THE FULL CONTRACT, and an extra root property is refused there if it arrives.

THE PROMPT SENT IS v1.6.0: v1.5.0's system region and the generation-surface block, with nothing left
unstated, and the completion signal still outranks the content, with one request.

STAGES 6 TO 9 EACH REFUSE AT THEIR OWN STAGE, with the real machinery.

NO APPROVAL, NO TRANSPORT; an approval must decide BOTH of V10's risks, and accept both, or nothing
is sent.

V1 TO V6 AND V9 ARE REFUSED AS SPENT, AND V7 AND V8 AS SUPERSEDED, each under its own name; an unseen
digest is not.

THE REQUEST WAITS 240 SECONDS, the body is V9's bytes with the v1.6.0 system region, the hard ceiling
is V9's and the planning estimate is recomputed from V10's body.

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
RUNNER_PATH = SCRIPTS / "run_second_opportunity_execution_v10.py"
RUNNER_V9_PATH = SCRIPTS / "run_second_opportunity_execution_v9.py"
RUNNER_V8_PATH = SCRIPTS / "run_second_opportunity_execution_v8.py"
BOUNDED_GATE_PATH = SCRIPTS / "render_second_opportunity_bounded_contract.py"
FIXTURES_PATH = SCRIPTS / "second_opportunity_synthetic_fixtures.py"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
V3_SHA256 = "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2"
V4_SHA256 = "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b"
V5_SHA256 = "da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a"
V6_SHA256 = "969128dd2453ab2a6907335d9386c9c3f3fac991db91c674b151c9db777aa8a9"
V7_SHA256 = "51023d0d2ed780db4c7d5018a289939e7c9c83061f8768051ef1cd7b8ae674e8"
V8_SHA256 = "583946460c6cf68c1be5519916f92d268e36ed65924aeb24901731439586c399"
V9_SHA256 = "ba681da94b3e89f22c7e39bdb2dc4ef95d0527ca3db561c849eb089652d9425d"
V9_BODY_SHA256 = "58956019f78f414ee11392bee5e99eedda4eb1b4deb20d3f20219dfc60739842"
V10_BODY_SHA256 = "703fb27140412ee36fdfc9f1ab595c4d5192bd084fd9f99e2700783bd99ccb1c"
PROJECTION_SHA256 = "87028f451205494a948e83740e73b9ca59ce3243f54e24c123b7cc2354c69783"
CANONICAL_SHA256 = "7d67bad3df06691ba46a4dcc65cbf186bc5825a87719e985637aec68640e1b66"
SYNTHETIC_SHA = "d" * 64
STRUCTURED_TOOL_NAME = "emit_structured_output"
REQUEST_ID = "req_synthetic_v10"
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
    return _module("runner_v10_under_test", RUNNER_PATH)


@pytest.fixture(scope="module")
def bounded():
    return _module("bounded_gate_for_runner_v10_tests", BOUNDED_GATE_PATH)


@pytest.fixture(scope="module")
def fx():
    return _module("fixtures_for_runner_v10_tests", FIXTURES_PATH)


def _packet_file(sha: str = SYNTHETIC_SHA) -> dict:
    return {
        "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V10",
        "EXECUTION_PACKET_VERSION": 10,
        "EXECUTION_PACKET_SHA256": sha,
        "MODEL_ID": "claude-sonnet-5",
        "ADAPTER_PARAMETERS": {"max_output_tokens": 128000, "thinking": "DISABLED"},
        "REQUEST_TIMEOUT": 240.0,
        "GENERATION_PARAMETERS": {"max_retries": 0},
    }


def _context(fx, sha: str = SYNTHETIC_SHA, **kwargs) -> dict:
    context = fx.runner_context(**kwargs)
    context["packet_file"] = {**context["packet_file"], **_packet_file(sha)}
    context["parts"] = render_parts(fx)
    return context


def render_parts(fx):
    from sros_opportunity.second_opportunity_prompt_v1_6 import (
        render_second_opportunity_prompt_v1_6,
    )

    return render_second_opportunity_prompt_v1_6(
        fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
    )


def render_parts_v1_5(fx):
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
        "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V10",
        "EXECUTION_PACKET_VERSION": 10,
        "EXECUTION_PACKET_SHA256": SYNTHETIC_SHA,
        "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
        "approved_by": "synthetic operator",
        "operator_statement": "a synthetic approval, for a test",
        "recorded_by": "mission-9.9.9",
        "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V10": True,
        "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10": True,
    }
    base.update(overrides)
    return base


@pytest.fixture
def approved(runner, tmp_path, monkeypatch):
    path = tmp_path / "approval-v10.json"
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


def _escaped(text: str) -> str:
    return json.dumps(text)[1:-1]


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


class TestThePromptSentIsVersion160:
    def test_the_request_carries_the_semantic_block_the_names_and_the_surface_block(
        self, runner, fx, approved
    ):
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, fx, transport)
        sent = json.dumps(transport.calls[0]["body"])
        assert "SEMANTIC RULES THE ANSWER IS AUDITED AGAINST." in sent
        assert "SOURCE NAMES ARE PROVENANCE, NEVER EVIDENCE." in sent
        assert "GENERATION SURFACE: THE FORMS THE AUDITED FIELDS TAKE." in sent
        assert _escaped('"Evidence of ...", "Observation of ..." or') in sent
        assert f"{SUMMARY}\\n    at most 1500 characters" in sent
        assert f"{SUMMARY}: generation target 1200 characters; hard maximum 1500 characters" in sent

    def test_nothing_is_left_unstated_the_surface_included(self, runner, fx):
        parts = render_parts(fx)
        assert runner.unstated_constraints(parts.system_instructions) == []
        assert runner.unstated_semantic_rules(parts) == []
        assert runner.unstated_targets(parts) == []
        assert runner.unstated_surface(parts) == []

    def test_the_surface_check_refuses_prompt_v1_5(self, runner, fx):
        from sros_opportunity.generation_surface_policy import SURFACE_RULE_IDS

        assert runner.unstated_surface(render_parts_v1_5(fx)) == list(SURFACE_RULE_IDS)

    def test_the_contract_checks_refuse_prompt_v1_4_under_schema_v1_2(self, runner, fx):
        from sros_opportunity.second_opportunity_prompt_v1_4 import (
            render_second_opportunity_prompt_v1_4,
        )

        v1_4 = render_second_opportunity_prompt_v1_4(
            fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
        )
        assert runner.unstated_targets(v1_4) == [SUMMARY]

    def test_the_request_names_prompt_1_6_0_and_carries_the_projection(self, runner, fx):
        request = runner.build_request(render_parts(fx), _packet_file())
        assert request.prompt_template_version == "1.6.0"
        assert _sha(request.response_schema) == PROJECTION_SHA256

    def test_the_runner_reads_the_prompt_v1_6_record(self, runner):
        record = json.loads(runner.PROMPT_DOCUMENT.read_text(encoding="utf-8"))
        assert runner.PROMPT_DOCUMENT.name == "second-opportunity-synthesis-prompt-v7.json"
        assert record["PROMPT_SHA256"] == runner.EXPECTED["PROMPT_SHA256"]
        text = runner.PROMPT_DOCUMENT.read_text(encoding="utf-8")
        assert (
            hashlib.sha256(text.encode("utf-8")).hexdigest()
            == runner.EXPECTED["PROMPT_RECORD_SHA256"]
        )


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
        assert sent["timeout_seconds"] == 240.0
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

    @pytest.mark.parametrize(
        ("field", "value", "stage"),
        [
            (
                "candidate_intervention_class",
                "A comparison of the stated amounts in published notices.",
                None,
            ),
            ("candidate_intervention_class", "Software for buyers.", "6"),
            (
                "recommended_next_evidence",
                ["Evidence of whether the same authorities publish comparable notices again."],
                None,
            ),
            (
                "recommended_next_evidence",
                ["Investigate whether the same authorities publish comparable notices again."],
                "6",
            ),
            (
                "recommended_next_evidence",
                ["Evidence of the confirmed payments under these notices."],
                "6",
            ),
        ],
        ids=["supported_class", "unsupported_class", "noun_request", "imperative", "presupposed"],
    )
    def test_the_surface_forms_meet_the_gate_as_the_policy_says(
        self, runner, fx, field, value, stage
    ):
        report = runner.validate_execution(
            fx.recorded_result(fx.good_output(**{field: value})), fx.runner_context()
        )
        if stage is None:
            assert report["outcome"] == "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
        else:
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

    def test_no_approval_is_recorded_beside_v10(self, runner):
        """True while V10 awaits the operator. A later mission that records an approval re-points
        this to what the approval must then be, as Mission 1.84.22 did for V9."""
        assert not runner.APPROVAL_FILE.exists()
        with pytest.raises(runner.RefusedError) as refusal:
            runner.check_approval(str(runner.EXPECTED["EXECUTION_PACKET_SHA256"]))
        assert refusal.value.code == "OPERATOR_APPROVAL_NOT_RECORDED"

    @pytest.mark.parametrize(
        ("override", "code"),
        [
            ({"EXECUTION_PACKET_SHA256": "e" * 64}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
            ({"EXECUTION_PACKET_VERSION": 9}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
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

    @pytest.mark.parametrize(
        ("ident", "version", "sha"),
        [
            ("SECOND-OPPORTUNITY-SYNTH-EXEC-V6", 6, V6_SHA256),
            ("SECOND-OPPORTUNITY-SYNTH-EXEC-V9", 9, V9_SHA256),
        ],
        ids=["V6", "V9"],
    )
    def test_an_earlier_approval_does_not_authorise_v10(
        self, runner, fx, tmp_path, monkeypatch, ident, version, sha
    ):
        path = tmp_path / "approval.json"
        path.write_text(
            json.dumps(
                _approval(
                    EXECUTION_PACKET_ID=ident,
                    EXECUTION_PACKET_VERSION=version,
                    EXECUTION_PACKET_SHA256=sha,
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
        [V1_SHA256, V2_SHA256, V3_SHA256, V4_SHA256, V5_SHA256, V6_SHA256, V9_SHA256],
        ids=["V1", "V2", "V3", "V4", "V5", "V6", "V9"],
    )
    def test_a_spent_digest_cannot_run_under_v10(self, runner, fx, tmp_path, monkeypatch, spent):
        """Even with an approval naming it, the consumed-approval guard refuses a spent digest."""
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(_approval(EXECUTION_PACKET_SHA256=spent)), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, transport, _context(fx, spent))
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"
        assert transport.calls == []

    def test_an_unseen_digest_is_not_refused_because_v1_to_v9_are_spent(self, runner):
        runner.refuse_if_consumed("0" * 64)
        runner.refuse_if_consumed(SYNTHETIC_SHA)

    def test_v10s_own_record_refuses_its_digest_once_spent(self, runner, fx, approved, monkeypatch):
        record = approved.parent / "record-v10.json"
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
        monkeypatch.setattr(runner, "EXECUTION_RECORD_V10", record)
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
        assert artifact["execution_packet_id"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V10"

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
        assert kept["execution_packet_id"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V10"
        assert kept["PERSISTED"] == "NOTHING"


# ================================================================== V10's governance


def _v9_runner():
    return _module("runner_v9_for_runner_v10_tests", RUNNER_V9_PATH)


def _v8_runner():
    return _module("runner_v8_for_runner_v10_tests", RUNNER_V8_PATH)


class TestV1ToV6AndV9SpentAndV7AndV8Superseded:
    @pytest.mark.parametrize(
        "spent",
        [V1_SHA256, V2_SHA256, V3_SHA256, V4_SHA256, V5_SHA256, V6_SHA256, V9_SHA256],
        ids=["V1", "V2", "V3", "V4", "V5", "V6", "V9"],
    )
    def test_a_spent_digest_keeps_its_name_through_v9s_guard(self, runner, spent):
        with pytest.raises(runner.RefusedError) as refusal:
            runner.refuse_if_consumed(spent)
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"

    @pytest.mark.parametrize("superseded", [V7_SHA256, V8_SHA256], ids=["V7", "V8"])
    def test_v7_and_v8_are_refused_as_superseded_and_never_as_consumed(self, runner, superseded):
        with pytest.raises(runner.RefusedError) as refusal:
            runner.refuse_if_consumed(superseded)
        assert refusal.value.code == "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
        assert "EXECUTION_APPROVAL_ALREADY_CONSUMED" not in str(refusal.value)

    @pytest.mark.parametrize("superseded", [V7_SHA256, V8_SHA256], ids=["V7", "V8"])
    def test_a_superseded_digest_cannot_run_under_v10_even_with_an_approval_naming_it(
        self, runner, fx, tmp_path, monkeypatch, superseded
    ):
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(_approval(EXECUTION_PACKET_SHA256=superseded)), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, transport, _context(fx, superseded))
        assert refusal.value.code == "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
        assert transport.calls == []

    def test_the_v9_runner_itself_refuses_v9_as_spent(self):
        v9 = _v9_runner()
        with pytest.raises(v9.RefusedError) as refusal:
            v9.refuse_if_consumed(V9_SHA256)
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"

    def test_the_v8_runner_still_refuses_v8(self):
        v8 = _v8_runner()
        with pytest.raises(v8.RefusedError) as refusal:
            v8.refuse_if_consumed(V8_SHA256)
        assert refusal.value.code == "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"

    def test_without_v9s_record_the_chain_would_let_v9_through(self, runner, monkeypatch, tmp_path):
        """Which is why V10's verification refuses unless V9 is refused as spent."""
        v9 = _v9_runner()
        monkeypatch.setattr(v9, "EXECUTION_RECORD_V9", tmp_path / "absent.json")
        monkeypatch.setattr(runner, "v9_runner", lambda: v9)
        runner.refuse_if_consumed(V9_SHA256)
        assert "_GUARD_INACTIVE" in RUNNER_PATH.read_text(encoding="utf-8")


class TestAnApprovalMustDecideBothOfV10sRisks:
    @pytest.mark.parametrize(
        "key",
        [
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V10",
            "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10",
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

    def test_v9s_risk_decisions_do_not_decide_v10s(self, runner, fx, tmp_path, monkeypatch):
        approval = _approval()
        for key in list(approval):
            if key.endswith("_FOR_V10"):
                approval[key.replace("_FOR_V10", "_FOR_V9")] = approval.pop(key)
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(approval), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, fx, ScriptedTransport(body=_body(None, "tool_use")))
        assert refusal.value.code == "OPERATOR_APPROVAL_INCOMPLETE"

    @pytest.mark.parametrize(
        ("key", "code"),
        [
            (
                "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V10",
                "RESIDUAL_SEMANTIC_LIMITATION_NOT_ACCEPTED",
            ),
            (
                "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10",
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

    def test_the_packet_accepts_neither_risk(self, runner):
        packet = json.loads(runner.PACKET_FILE.read_text(encoding="utf-8"))
        for key in runner.RISK_DECISIONS:
            assert key.endswith("_FOR_V10")
            assert packet[key] is False
            assert runner.EXPECTED[key] is False
        assert packet["TIMEOUT"]["STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10"] is False
        assert "OPERATOR_STATED_INTENTIONS" not in packet


class TestTheTimeoutIs240AndOnlyThePromptMoved:
    def test_the_request_waits_240_seconds(self, runner, fx):
        request = runner.build_request(render_parts(fx), _packet_file())
        assert request.timeout_seconds == 240.0 == runner.EXPECTED["REQUEST_TIMEOUT"]

    def test_the_transport_is_given_240_seconds_and_one_request(self, runner, fx, approved):
        transport = ScriptedTransport(raises=TimeoutError("synthetic: the budget ran out"))
        report, _ = _report(runner, fx, transport)
        assert [call["timeout_seconds"] for call in transport.calls] == [240.0]
        assert report["outcome"] == "EXECUTION_FAILED_TIMEOUT_NO_RETRY"

    def test_the_timeout_is_no_part_of_the_body(self, runner, fx):
        def keys(node):
            if isinstance(node, dict):
                return [*node, *(k for v in node.values() for k in keys(v))]
            if isinstance(node, list):
                return [k for v in node for k in keys(v)]
            return []

        assert not any("timeout" in str(k).lower() for k in keys(_built_body(runner, fx)))

    def test_the_body_is_v9s_bytes_with_the_v1_6_system_region(self, runner, fx):
        v9 = _v9_runner()
        parts_v1_5, parts_v1_6 = render_parts_v1_5(fx), render_parts(fx)
        theirs = json.dumps(v9.request_body(parts_v1_5, _packet_file()))
        mine = json.dumps(runner.request_body(parts_v1_6, _packet_file()))
        old = _escaped(str(parts_v1_5.system_instructions))
        new = _escaped(str(parts_v1_6.system_instructions))
        assert theirs.count(old) == 1
        assert theirs.replace(old, new) == mine
        assert mine != theirs

    def test_the_committed_body_identity(self, runner):
        packet = json.loads(runner.PACKET_FILE.read_text(encoding="utf-8"))
        differential = packet["REQUEST_BODY_DIFFERENTIAL"]
        assert (
            packet["REQUEST_BODY_SHA256"]
            == runner.EXPECTED["REQUEST_BODY_SHA256"]
            == V10_BODY_SHA256
        )
        assert differential["v9_body_sha256"] == V9_BODY_SHA256
        assert differential["differences"] == ["system: changed"]
        assert differential["v10_body_is_v9_body_with_the_v1_6_system_region"] is True
        assert differential["unapproved_drift"] == []
        assert differential["timeout_in_the_provider_body"] is False

    def test_the_body_selects_no_billing_category_the_ceiling_leaves_out(self, runner, fx):
        assert runner.billing_selectors(_built_body(runner, fx)) == runner.COST_SELECTORS_REQUIRED

    def test_the_ceiling_is_v9s_and_the_planning_estimate_is_v10s_own(self, runner):
        from sros_llm_gateway.pricing import ModelPrice

        price = ModelPrice(input_per_1k=0.002, output_per_1k=0.01)
        packet = {key: runner.EXPECTED[key] for key in runner.EXPECTED}
        hard, planning = runner.cost_bounds(price, packet)
        assert (runner.decimal_text(hard), runner.decimal_text(planning)) == ("3.608", "1.31972")
        assert runner.EXPECTED["PLANNING_INPUT_TOKEN_ESTIMATE"] == 19860
        packet["REQUEST_TIMEOUT"] = 60.0
        assert runner.cost_bounds(price, packet) == (hard, planning)

    def test_the_timeout_block_says_what_240_is_and_is_not(self, runner):
        timeout = json.loads(runner.PACKET_FILE.read_text(encoding="utf-8"))["TIMEOUT"]
        assert timeout["REQUEST_TIMEOUT_SECONDS"] == 240.0
        assert timeout["TIMEOUT_DECISION_BASIS"] == "OPERATOR_AVAILABILITY_BUDGET"
        assert timeout["TIMEOUT_CHANGED_BY_THIS_MISSION"] is False
        for key in ("PROVIDER_GUARANTEED", "STATISTICALLY_ESTIMATED", "MATHEMATICALLY_DERIVED"):
            assert timeout[key] is False
        assert timeout["TIMEOUT_RISK_ELIMINATED"] is False
        assert timeout["END_TO_END_LATENCY_BOUND"] == "NOT_ESTABLISHED"
        assert timeout["TIMEOUT_CHANGES_BILLING"] is False

    def test_no_retry_offsets_the_timeout(self, runner):
        packet = json.loads(runner.PACKET_FILE.read_text(encoding="utf-8"))
        assert runner.EXPECTED["MAX_RETRIES"] == 0 == packet["MAX_RETRIES"]
        assert packet["GENERATION_PARAMETERS"]["max_retries"] == 0
        assert packet["GENERATION_PARAMETERS"]["timeout_seconds"] == 240.0

    def test_expected_pins_the_committed_packet_and_records(self, runner):
        packet = json.loads(runner.PACKET_FILE.read_text(encoding="utf-8"))
        assert packet["EXECUTION_PACKET_SHA256"] == runner.EXPECTED["EXECUTION_PACKET_SHA256"]
        for path, key in (
            (runner.COST_CEILING_RECORD, "COST_CEILING_RECORD_SHA256"),
            (runner.V7_SUPERSESSION_RECORD, "V7_SUPERSESSION_RECORD_SHA256"),
            (runner.V8_SUPERSESSION_RECORD, "V8_SUPERSESSION_RECORD_SHA256"),
            (runner.TIMEOUT_DECISION_RECORD, "TIMEOUT_DECISION_RECORD_SHA256"),
            (runner.PROMPT_DOCUMENT, "PROMPT_RECORD_SHA256"),
            (runner.EXECUTION_RECORD_V9, "V9_EXECUTION_RECORD_SHA256"),
        ):
            text = path.read_text(encoding="utf-8")
            assert hashlib.sha256(text.encode("utf-8")).hexdigest() == runner.EXPECTED[key]
        for key in ("INPUT_TOKEN_ESTIMATE", "WORST_CASE_CALL_COST", "EXECUTION_COST_CEILING"):
            assert key not in packet
