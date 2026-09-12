"""Mission 1.84.6. Execution packet V2's runner: the completion signal decides first.

Four things this file defends, with synthetic transports and never with a network.

THE PROVIDER'S COMPLETION SIGNAL OUTRANKS THE CONTENT. A response that stopped at the output limit
is refused at stage 3 whatever it carries: parseable JSON, every required key, even an object the
whole v1.1.0 schema accepts. Cases A to H of the brief, plus the refusal and context-window stops.

ONE REQUEST, AND NOTHING THAT FINISHES THE JSON. A limit stop is followed by no second request, no
continuation and no repair, and the request that was sent disables thinking and asks for 128000.

NO APPROVAL, NO TRANSPORT. Without an approval naming the packet's digest the runner refuses before
a transport exists, and V1's spent digest cannot be run under V2.

WHAT ARRIVED IS KEPT, ON EVERY PATH WHERE SOMETHING ARRIVED. The raw body, the usage, the request id,
the digests and the terminal outcome, with secrets redacted and hidden reasoning stripped.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import types

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"
RUNNER_PATH = SCRIPTS / "run_second_opportunity_execution_v2.py"
BOUNDED_GATE_PATH = SCRIPTS / "render_second_opportunity_bounded_contract.py"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
SYNTHETIC_SHA = "b" * 64
STRUCTURED_TOOL_NAME = "emit_structured_output"
EVIDENCE_ID = "0b407e80-336a-4b71-8a59-09f0464bf43f"
CLAIM_ID = "d25bd256-49a1-494f-b6f8-4f1c3271d78e"
REQUEST_ID = "req_synthetic_v2"
MISSING = object()


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _module("runner_v2_under_test", RUNNER_PATH)


@pytest.fixture(scope="module")
def bounded():
    return _module("bounded_gate_for_runner_v2_tests", BOUNDED_GATE_PATH)


def _packet_file(sha: str = SYNTHETIC_SHA) -> dict:
    return {
        "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V2",
        "EXECUTION_PACKET_VERSION": 2,
        "EXECUTION_PACKET_SHA256": sha,
        "ADAPTER_PARAMETERS": {"max_output_tokens": 128000, "thinking": "DISABLED"},
        "REQUEST_TIMEOUT": 60.0,
        "GENERATION_PARAMETERS": {"max_retries": 0},
        "MODEL_ID": "claude-sonnet-5",
        "PROVIDER_ID": "anthropic",
        "SELECTED_PACKET_ID": "synthetic-packet",
        "PREPARATION_VERSION": "opportunity-preparation@5.0.0",
    }


PARTS = types.SimpleNamespace(
    system_instructions="s", trusted_context="t", untrusted=(), task="k", metadata={}
)


def _evidence_packet():
    from sros_opportunity import (
        EvidenceDimension,
        EvidenceFacets,
        IndependenceState,
        PacketEligibility,
        ReliabilityStatus,
        build_packet,
    )

    facets = EvidenceFacets(
        evidence_id=EVIDENCE_ID,
        claim_id=CLAIM_ID,
        source_id="wikimedia-pageviews",
        source_family="knowledge",
        use_profile_id="local-private-research-v1",
        extraction_method="deterministic",
        claim_type="OBSERVED",
        claim_lifecycle="ACTIVE",
        claim_temporality="EVERGREEN",
        claim_origin="DETERMINISTIC_EXTRACTION",
        direction="SUPPORTS",
        observation_category="UNCATEGORISED",
        evidence_level=1,
        relevance=1.0,
        directness=1.0,
        extraction_confidence=1.0,
        reliability=None,
        reliability_status=ReliabilityStatus.NO_APPLICABLE_ASSESSMENT,
        independence_state=IndependenceState.UNKNOWN,
        independence_group_id=None,
        observed_at=None,
        signal_type_id="content_request_change",
        dimensions=frozenset({EvidenceDimension.AUDIENCE_OR_USAGE}),
        dimension_bound="requests for one article on one wiki in one day",
    )
    return build_packet(None, "synthetic subject", ((facets, PacketEligibility.ELIGIBLE_CONTEXT),))


def _context(packet_file: dict | None = None) -> dict:
    return {
        "packet_file": packet_file or _packet_file(),
        "parts": PARTS,
        "packet": _evidence_packet(),
        "statements": {CLAIM_ID: "Synthetic statement."},
        "evidence_to_claim": {EVIDENCE_ID: CLAIM_ID},
        "prompt_hash": "p" * 64,
        "representation": "r" * 64,
    }


def _schema_valid_output(bounded) -> dict:
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1

    output = bounded.maximum_instance(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, bounded.ASCII_FILL)
    output["decision"] = "FORM_HYPOTHESIS"
    return output


def _required_keys_only() -> dict:
    """Every required key present and nothing valid: enough for the Gateway's presence check."""
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

    def __init__(self, *, status=200, body=None, raises=None, raw_text=None, headers=None) -> None:
        self.status = status
        self.body = body
        self.raises = raises
        self.raw_text = raw_text
        self.headers = {"request-id": REQUEST_ID} if headers is None else headers
        self.calls: list[dict] = []

    def post_json(self, url, headers, body, timeout_seconds):
        from sros_llm_gateway.transport import HttpResponse

        self.calls.append({"url": url, "body": body, "timeout_seconds": timeout_seconds})
        if len(self.calls) > 1:
            raise AssertionError("a second request: a retry, a continuation or a repair")
        if self.raises is not None:
            raise self.raises
        payload = (
            self.raw_text.encode("utf-8")
            if self.raw_text is not None
            else json.dumps(self.body).encode("utf-8")
        )
        return HttpResponse(self.status, payload, dict(self.headers))


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
        "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V2",
        "EXECUTION_PACKET_VERSION": 2,
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
    path = tmp_path / "approval-v2.json"
    path.write_text(json.dumps(_approval()), encoding="utf-8")
    monkeypatch.setattr(runner, "APPROVAL_FILE", path)
    return path


def _run(runner, transport, context: dict | None = None):
    from sros_llm_gateway.pricing import PricingTable

    context = context or _context()
    result = runner.execute(
        context,
        transport=transport,
        config=_config(),
        pricing=PricingTable(version="synthetic", prices={}),
        api_key="synthetic-not-a-credential",
    )
    return result, context


def _report(runner, transport, context: dict | None = None, **kwargs):
    result, context = _run(runner, transport, context)
    return runner.validate_execution(result, context, **kwargs), result


def _not_reached_after(runner, report, stage: str) -> bool:
    index = runner.STAGES.index(stage)
    return all(report["stages"][s] == "NOT_REACHED" for s in runner.STAGES[index + 1 :])


# ================================================================== the completion signal first


class TestTheCompletionSignalDecidesFirst:
    def test_case_a_a_complete_response_continues_to_the_schema_gate(
        self, runner, bounded, approved
    ):
        report, _ = _report(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "tool_use"))
        )
        assert report["stages"]["3_provider_completion"] == "PASSED"
        assert report["stages"]["4_structured_output_parse"] == "PASSED"
        assert report["stages"]["5_schema_validation_v1_1_0"] == "PASSED"
        assert report["stages"]["6_semantic_output_gate_v1_1_0"] != "NOT_REACHED"
        assert report["persist"] is False

    def test_case_b_an_output_limit_stop_is_refused_before_persistence(self, runner, approved):
        report, _ = _report(runner, ScriptedTransport(body=_body(None, "max_tokens")))
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"
        assert report["failed_stage"] == "3_provider_completion"
        assert _not_reached_after(runner, report, "3_provider_completion")
        assert report["persist"] is False

    def test_case_c_an_output_limit_stop_with_parseable_json_is_still_refused(
        self, runner, approved
    ):
        partial = {"decision": "FORM_HYPOTHESIS", "subject": "cut off here"}
        report, result = _report(runner, ScriptedTransport(body=_body(partial, "max_tokens")))
        assert result["failure"] is not None, "the Gateway refused the missing keys"
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"
        assert report["stages"]["4_structured_output_parse"] == "NOT_REACHED"

    def test_case_d_an_output_limit_stop_passing_the_presence_check_is_still_refused(
        self, runner, approved
    ):
        report, result = _report(
            runner, ScriptedTransport(body=_body(_required_keys_only(), "max_tokens"))
        )
        assert result["failure"] is None, "the Gateway found every required key present"
        assert result["response"].structured is not None
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"
        assert _not_reached_after(runner, report, "3_provider_completion")

    def test_case_e_an_output_limit_stop_satisfying_the_full_schema_is_still_refused(
        self, runner, bounded, approved
    ):
        from sros_opportunity.schema_validation import schema_violations
        from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1

        output = _schema_valid_output(bounded)
        assert schema_violations(output, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1) == []
        report, _ = _report(runner, ScriptedTransport(body=_body(output, "max_tokens")))
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"
        assert report["stages"]["5_schema_validation_v1_1_0"] == "NOT_REACHED"
        assert report["persist"] is False

    @pytest.mark.parametrize(
        "stop_reason", ["end_turn", "pause_turn", "stop_sequence", None, "a_value_added_later"]
    )
    def test_case_f_an_unknown_or_unexpected_stop_reason_fails_closed(
        self, runner, bounded, approved, stop_reason
    ):
        report, _ = _report(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), stop_reason))
        )
        assert report["outcome"] == "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY"
        assert report["failed_stage"] == "3_provider_completion"
        assert report["persist"] is False

    def test_case_f_a_missing_stop_reason_fails_at_the_response_shape(
        self, runner, bounded, approved
    ):
        report, _ = _report(runner, ScriptedTransport(body=_body(_schema_valid_output(bounded))))
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_RESPONSE_SHAPE_NO_RETRY"
        assert report["failed_stage"] == "2_provider_response_shape"

    def test_case_g_a_complete_response_with_a_schema_failure(self, runner, approved):
        report, result = _report(
            runner, ScriptedTransport(body=_body(_required_keys_only(), "tool_use"))
        )
        assert result["failure"] is None
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY"
        assert report["failed_stage"] == "5_schema_validation_v1_1_0"
        assert report["stages"]["3_provider_completion"] == "PASSED"

    def test_case_h_a_complete_response_with_a_semantic_failure(self, runner, bounded, approved):
        report, _ = _report(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "tool_use"))
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_SEMANTIC_GATE_NO_RETRY"
        assert report["failed_stage"] == "6_semantic_output_gate_v1_1_0"
        assert report["reasons"], "the semantic gate names what it refused"

    def test_a_refusal_stop_is_refused(self, runner, bounded, approved):
        report, _ = _report(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "refusal"))
        )
        assert report["outcome"] == "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY"

    def test_a_context_window_stop_is_an_output_limit(self, runner, approved):
        report, _ = _report(
            runner, ScriptedTransport(body=_body(None, "model_context_window_exceeded"))
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"

    def test_a_provider_error_status_fails_at_transport(self, runner, approved):
        report, _ = _report(
            runner, ScriptedTransport(status=500, body={"error": {"message": "overloaded"}})
        )
        assert report["outcome"] == "EXECUTION_FAILED_PROVIDER_ERROR_NO_RETRY"
        assert report["failed_stage"] == "1_transport_success"

    def test_an_answer_passing_every_machine_stage_still_awaits_a_human(
        self, runner, bounded, approved
    ):
        from sros_opportunity.validation import PersistenceDecision, SynthesisAudit

        output = _schema_valid_output(bounded)
        output["supporting_evidence_ids"] = [EVIDENCE_ID]
        output["supporting_claim_ids"] = [CLAIM_ID]
        accepted = PersistenceDecision(
            persist=True,
            gate_version="synthetic",
            audit=SynthesisAudit(audit_version="synthetic", fields=()),
        )
        report, _ = _report(
            runner,
            ScriptedTransport(body=_body(output, "tool_use")),
            semantic_gate=lambda _output: accepted,
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
        assert report["stages"]["9_persistence_eligibility"] == "ELIGIBLE_FOR_HUMAN_REVIEW_ONLY"
        assert report["stages"]["10_human_review"] == "REQUIRED_NOT_PERFORMED"
        assert report["persist"] is False
        assert report["provenance"]["provider_request_id"] == REQUEST_ID

    def test_an_insufficient_evidence_answer_forms_no_hypothesis(self, runner, bounded, approved):
        from sros_opportunity.validation import PersistenceDecision

        output = _schema_valid_output(bounded)
        output["decision"] = "INSUFFICIENT_EVIDENCE"
        declined = PersistenceDecision(
            persist=False, gate_version="synthetic", refusal_reasons=("insufficient",)
        )
        report, _ = _report(
            runner,
            ScriptedTransport(body=_body(output, "tool_use")),
            semantic_gate=lambda _output: declined,
        )
        assert report["outcome"] == "EXECUTION_COMPLETED_INSUFFICIENT_EVIDENCE_NO_OPPORTUNITY"
        assert report["persist"] is False


# ================================================================== one request


class TestOneRequestAndNothingThatFinishesTheJson:
    def test_exactly_one_request_even_at_the_limit(self, runner, approved):
        transport = ScriptedTransport(body=_body(_required_keys_only(), "max_tokens"))
        report, _ = _report(runner, transport)
        assert len(transport.calls) == 1
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"

    def test_the_request_disables_thinking_and_asks_for_128000(self, runner, approved):
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, transport)
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


# ================================================================== approval


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

    def test_no_approval_refuses_before_a_transport_exists(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(runner, "APPROVAL_FILE", tmp_path / "absent.json")
        built = self._tripwire(monkeypatch)
        with pytest.raises(runner.RefusedError) as refusal:
            runner.execute(_context())
        assert refusal.value.code == "OPERATOR_APPROVAL_NOT_RECORDED"
        assert built == []

    @pytest.mark.parametrize(
        ("override", "code"),
        [
            ({"EXECUTION_PACKET_SHA256": "c" * 64}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
            ({"EXECUTION_PACKET_VERSION": 1}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
            ({"decision": "DEFER"}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
            ({"approved_by": "  "}, "OPERATOR_APPROVAL_INCOMPLETE"),
            ({"operator_statement": ""}, "OPERATOR_APPROVAL_INCOMPLETE"),
        ],
    )
    def test_an_approval_that_does_not_approve_this_packet_is_refused(
        self, runner, tmp_path, monkeypatch, override, code
    ):
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(_approval(**override)), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, transport)
        assert refusal.value.code == code
        assert transport.calls == []

    def test_a_v1_approval_does_not_authorise_v2(self, runner, tmp_path, monkeypatch):
        path = tmp_path / "approval.json"
        path.write_text(
            json.dumps(
                _approval(
                    EXECUTION_PACKET_ID="SECOND-OPPORTUNITY-SYNTH-EXEC-V1",
                    EXECUTION_PACKET_VERSION=1,
                    EXECUTION_PACKET_SHA256=V1_SHA256,
                )
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, ScriptedTransport(body=_body(None, "tool_use")))
        assert refusal.value.code == "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"

    def test_v1s_spent_digest_cannot_run_under_v2(self, runner, tmp_path, monkeypatch):
        """Even with an approval naming it, the consumed-approval guard refuses V1's digest."""
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(_approval(EXECUTION_PACKET_SHA256=V1_SHA256)), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, transport, _context(_packet_file(V1_SHA256)))
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"
        assert transport.calls == []


# ================================================================== retention


class TestWhatArrivedIsKept:
    def _artifact(self, runner, transport, context: dict | None = None):
        result, context = _run(runner, transport, context)
        report = runner.validate_execution(result, context)
        return runner.build_artifact(result, report), result, report

    def test_retention_on_a_complete_response(self, runner, bounded, approved):
        artifact, _, _ = self._artifact(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "tool_use"))
        )
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert isinstance(artifact["RAW_PROVIDER_RESPONSE_BODY"], dict)
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_JUDGED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_schema_failure(self, runner, approved):
        artifact, _, report = self._artifact(
            runner, ScriptedTransport(body=_body(_required_keys_only(), "tool_use"))
        )
        assert report["failed_stage"] == "5_schema_validation_v1_1_0"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert isinstance(artifact["RAW_PROVIDER_RESPONSE_BODY"], dict)
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_an_output_limit_stop(self, runner, approved):
        partial = {"decision": "FORM_HYPOTHESIS", "subject": "cut off here"}
        artifact, result, _ = self._artifact(
            runner, ScriptedTransport(body=_body(partial, "max_tokens"))
        )
        assert result["failure"] is not None
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["RAW_PROVIDER_RESPONSE_BODY"]["stop_reason"] == "max_tokens"
        assert artifact["STOP_REASON"] == "max_tokens"
        assert artifact["PROVIDER_COMPLETION"] == "OUTPUT_LIMIT_REACHED"
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_JUDGED"] is False
        assert artifact["PERSISTED"] == "NOTHING"

    def test_usage_is_retained_from_the_response_when_the_gateway_refused(self, runner, approved):
        partial = {"decision": "FORM_HYPOTHESIS"}
        artifact, result, _ = self._artifact(
            runner, ScriptedTransport(body=_body(partial, "max_tokens", usage=(4321, 1234)))
        )
        assert result["failure"] is not None
        assert artifact["USAGE_FROM_RESPONSE"] == {"input_tokens": 4321, "output_tokens": 1234}
        assert artifact["USAGE_RETAINED"] is True
        assert artifact["usage"][0]["output_tokens"] == 1234

    def test_the_request_id_is_retained(self, runner, approved):
        artifact, _, _ = self._artifact(runner, ScriptedTransport(body=_body(None, "max_tokens")))
        assert artifact["PROVIDER_REQUEST_ID"] == REQUEST_ID

    def test_raw_and_parsed_digests_are_retained(self, runner, bounded, approved):
        artifact, _, _ = self._artifact(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "tool_use"))
        )
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["RAW_PROVIDER_RESPONSE_SHA256"])
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["PARSED_OUTPUT_SHA256"])

    def test_the_terminal_outcome_is_retained(self, runner, approved):
        artifact, _, report = self._artifact(
            runner, ScriptedTransport(body=_body(None, "max_tokens"))
        )
        assert artifact["TERMINAL_OUTCOME"] == report["outcome"] == artifact["OUTCOME"]
        assert artifact["validation"]["failed_stage"] == "3_provider_completion"

    def test_a_volunteered_reasoning_block_is_stripped(self, runner, approved):
        body = _body(
            None,
            "max_tokens",
            extra_blocks=({"type": "thinking", "thinking": "hidden reasoning text"},),
        )
        body["reasoning"] = "hidden reasoning text"
        artifact, _, _ = self._artifact(runner, ScriptedTransport(body=body))
        assert "hidden reasoning text" not in json.dumps(artifact["RAW_PROVIDER_RESPONSE_BODY"])
        assert artifact["HIDDEN_REASONING_RETAINED"] is False
        assert artifact["HIDDEN_REASONING_REQUESTED"] is False

    def test_a_credential_shape_is_redacted_from_the_body(self, runner, approved):
        leaked = "echoed key sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAA"
        body = _body(None, "max_tokens", extra_blocks=({"type": "text", "text": leaked},))
        artifact, _, _ = self._artifact(runner, ScriptedTransport(body=body))
        written = json.dumps(artifact)
        assert "sk-ant-api03" not in written
        assert "[REDACTED]" in written

    def test_a_timeout_writes_an_artifact_with_no_body(self, runner, approved):
        artifact, _, report = self._artifact(
            runner, ScriptedTransport(raises=TimeoutError("synthetic timeout"))
        )
        assert report["outcome"] == "EXECUTION_FAILED_TIMEOUT_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is False
        assert artifact["RAW_PROVIDER_RESPONSE_BODY"] == "NOT_AVAILABLE"
        assert artifact["transport_errors"]

    def test_no_fixture_constructs_the_real_transport(self, runner, approved, monkeypatch):
        import sros_llm_gateway.transport as transport_module

        built: list[int] = []
        original = transport_module.UrllibTransport.__init__

        def tripwire(self, *a, **k):  # pragma: no cover - must never run
            built.append(1)
            return original(self, *a, **k)

        monkeypatch.setattr(transport_module.UrllibTransport, "__init__", tripwire)
        self._artifact(runner, ScriptedTransport(body=_body(None, "max_tokens")))
        assert built == []
