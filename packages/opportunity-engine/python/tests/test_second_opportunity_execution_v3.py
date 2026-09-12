"""Mission 1.84.8. Execution packet V3's runner: V2's call, the aligned prompt, and nothing looser.

Five things this file defends, with synthetic transports and never with a network.

THE PROMPT SENT IS v1.2.0, and it states the bound V2 was refused on. The runner's own drift check
refuses V2's prompt, which left generation-relevant constraints to the tool schema.

THE SCHEMA STILL DECIDES. A summary at the bound passes stage 5 and one character over is refused
there, and the refused answer is kept whole rather than trimmed.

THE COMPLETION SIGNAL STILL OUTRANKS THE CONTENT, with one request and nothing that finishes the JSON.

NO APPROVAL, NO TRANSPORT, and neither V1's nor V2's spent digest can run; an unseen digest is not
refused merely because they are spent.

WHAT ARRIVED IS KEPT on each of the ten terminal paths the brief names, and when judging fails.
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
RUNNER_PATH = SCRIPTS / "run_second_opportunity_execution_v3.py"
BOUNDED_GATE_PATH = SCRIPTS / "render_second_opportunity_bounded_contract.py"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
SYNTHETIC_SHA = "c" * 64
STRUCTURED_TOOL_NAME = "emit_structured_output"
EVIDENCE_ID = "0b407e80-336a-4b71-8a59-09f0464bf43f"
CLAIM_ID = "d25bd256-49a1-494f-b6f8-4f1c3271d78e"
REQUEST_ID = "req_synthetic_v3"
SUMMARY = "evidence_bound_reasoning_summary"
MISSING = object()


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _module("runner_v3_under_test", RUNNER_PATH)


@pytest.fixture(scope="module")
def bounded():
    return _module("bounded_gate_for_runner_v3_tests", BOUNDED_GATE_PATH)


def _packet_file(sha: str = SYNTHETIC_SHA) -> dict:
    return {
        "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V3",
        "EXECUTION_PACKET_VERSION": 3,
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


def _real_parts():
    from sros_opportunity.second_opportunity import render_second_opportunity_prompt_v1_2

    return render_second_opportunity_prompt_v1_2(
        _evidence_packet(), {CLAIM_ID: "Synthetic statement."}, {EVIDENCE_ID: CLAIM_ID}
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
        "EXECUTION_PACKET_ID": "SECOND-OPPORTUNITY-SYNTH-EXEC-V3",
        "EXECUTION_PACKET_VERSION": 3,
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
    path = tmp_path / "approval-v3.json"
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


def _accepting_gate():
    from sros_opportunity.validation import PersistenceDecision, SynthesisAudit

    accepted = PersistenceDecision(
        persist=True,
        gate_version="synthetic",
        audit=SynthesisAudit(audit_version="synthetic", fields=()),
    )
    return lambda _output: accepted


def _citing_output(bounded) -> dict:
    output = _schema_valid_output(bounded)
    output["supporting_evidence_ids"] = [EVIDENCE_ID]
    output["supporting_claim_ids"] = [CLAIM_ID]
    return output


# ================================================================== the prompt sent


class TestThePromptSentIsTheAlignedOne:
    def test_the_request_carries_the_v1_2_system_region(self, runner, approved):
        context = _context()
        context["parts"] = _real_parts()
        transport = ScriptedTransport(body=_body(None, "max_tokens"))
        _run(runner, transport, context)
        sent = json.dumps(transport.calls[0]["body"])
        assert f"{SUMMARY}\\n    at most 900 characters" in sent
        assert "the exact string UNKNOWN_NOT_SUPPORTED" in sent
        assert runner.unstated_constraints(context["parts"].system_instructions) == []

    def test_the_drift_check_refuses_v2s_prompt(self, runner):
        from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_SYSTEM_V1_1

        unstated = runner.unstated_constraints(SECOND_OPPORTUNITY_SYSTEM_V1_1)
        assert f"{SUMMARY} maxLength" in unstated
        assert "subject maxLength" in unstated
        assert len(unstated) == 24

    def test_the_request_names_prompt_1_2_0_and_schema_1_1_0(self, runner):
        request = runner.build_request(PARTS, _packet_file())
        assert request.prompt_template_version == "1.2.0"
        assert request.response_schema["properties"][SUMMARY]["maxLength"] == 900


# ================================================================== the schema still decides


class TestTheSchemaStillDecides:
    def test_a_summary_at_the_bound_passes_stage_5(self, runner, bounded, approved):
        output = _schema_valid_output(bounded)
        output[SUMMARY] = "x" * 900
        report, _ = _report(runner, ScriptedTransport(body=_body(output, "tool_use")))
        assert report["stages"]["5_schema_validation_v1_1_0"] == "PASSED"

    def test_a_summary_one_over_is_refused_at_stage_5_and_kept_whole(
        self, runner, bounded, approved
    ):
        output = _schema_valid_output(bounded)
        output[SUMMARY] = "x" * 901
        result, context = _run(runner, ScriptedTransport(body=_body(output, "tool_use")))
        report = runner.validate_execution(result, context)
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY"
        assert report["reasons"] == [f"{SUMMARY}: 901 characters exceeds maxLength 900"]
        artifact = runner.build_artifact(result, report)
        assert len(artifact["parsed_output"][SUMMARY]) == 901
        assert artifact["PERSISTED"] == "NOTHING"


# ================================================================== the completion signal first


class TestTheCompletionSignalDecidesFirst:
    def test_a_complete_response_continues_to_the_schema_gate(self, runner, bounded, approved):
        report, _ = _report(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "tool_use"))
        )
        assert report["stages"]["3_provider_completion"] == "PASSED"
        assert report["stages"]["5_schema_validation_v1_1_0"] == "PASSED"
        assert report["persist"] is False

    def test_an_output_limit_stop_is_refused_before_persistence(self, runner, approved):
        report, _ = _report(runner, ScriptedTransport(body=_body(None, "max_tokens")))
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"
        assert _not_reached_after(runner, report, "3_provider_completion")

    def test_an_output_limit_stop_satisfying_the_full_schema_is_still_refused(
        self, runner, bounded, approved
    ):
        report, _ = _report(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "max_tokens"))
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY"
        assert report["stages"]["5_schema_validation_v1_1_0"] == "NOT_REACHED"

    @pytest.mark.parametrize("stop_reason", ["end_turn", "pause_turn", None, "a_value_added_later"])
    def test_an_unknown_stop_reason_fails_closed(self, runner, bounded, approved, stop_reason):
        report, _ = _report(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), stop_reason))
        )
        assert report["outcome"] == "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY"
        assert report["failed_stage"] == "3_provider_completion"

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


# ================================================================== one request


class TestOneRequestAndNothingThatFinishesTheJson:
    def test_exactly_one_request_even_at_the_limit(self, runner, approved):
        transport = ScriptedTransport(body=_body(_required_keys_only(), "max_tokens"))
        _report(runner, transport)
        assert len(transport.calls) == 1

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
            ({"EXECUTION_PACKET_SHA256": "d" * 64}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
            ({"EXECUTION_PACKET_VERSION": 2}, "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"),
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

    def test_a_v2_approval_does_not_authorise_v3(self, runner, tmp_path, monkeypatch):
        path = tmp_path / "approval.json"
        path.write_text(
            json.dumps(
                _approval(
                    EXECUTION_PACKET_ID="SECOND-OPPORTUNITY-SYNTH-EXEC-V2",
                    EXECUTION_PACKET_VERSION=2,
                    EXECUTION_PACKET_SHA256=V2_SHA256,
                )
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, ScriptedTransport(body=_body(None, "tool_use")))
        assert refusal.value.code == "OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET"

    @pytest.mark.parametrize("spent", [V1_SHA256, V2_SHA256], ids=["V1", "V2"])
    def test_a_spent_digest_cannot_run_under_v3(self, runner, tmp_path, monkeypatch, spent):
        """Even with an approval naming it, the consumed-approval guard refuses a spent digest."""
        path = tmp_path / "approval.json"
        path.write_text(json.dumps(_approval(EXECUTION_PACKET_SHA256=spent)), encoding="utf-8")
        monkeypatch.setattr(runner, "APPROVAL_FILE", path)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, transport, _context(_packet_file(spent)))
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"
        assert transport.calls == []

    def test_an_unseen_digest_is_not_refused_because_v1_and_v2_are_spent(self, runner):
        runner.refuse_if_consumed("0" * 64)
        runner.refuse_if_consumed(SYNTHETIC_SHA)

    def test_v3s_own_record_refuses_its_digest_once_spent(self, runner, approved, monkeypatch):
        record = approved.parent / "record-v3.json"
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
        monkeypatch.setattr(runner, "EXECUTION_RECORD_V3", record)
        transport = ScriptedTransport(body=_body(None, "tool_use"))
        with pytest.raises(runner.RefusedError) as refusal:
            _run(runner, transport)
        assert refusal.value.code == "EXECUTION_APPROVAL_ALREADY_CONSUMED"
        assert transport.calls == []


# ================================================================== what arrived is kept


class TestWhatArrivedIsKept:
    def _artifact(self, runner, transport, context: dict | None = None, **kwargs):
        result, context = _run(runner, transport, context)
        report = runner.validate_execution(result, context, **kwargs)
        return runner.build_artifact(result, report), result, report

    # -- the ten terminal paths --------------------------------------------------------------

    def test_retention_on_a_complete_response(self, runner, bounded, approved):
        artifact, _, report = self._artifact(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "tool_use"))
        )
        assert report["stages"]["3_provider_completion"] == "PASSED"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert isinstance(artifact["RAW_PROVIDER_RESPONSE_BODY"], dict)
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_JUDGED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_an_output_limit_stop(self, runner, approved):
        partial = {"decision": "FORM_HYPOTHESIS", "subject": "cut off here"}
        artifact, result, _ = self._artifact(
            runner, ScriptedTransport(body=_body(partial, "max_tokens"))
        )
        assert result["failure"] is not None
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["STOP_REASON"] == "max_tokens"
        assert artifact["PROVIDER_COMPLETION"] == "OUTPUT_LIMIT_REACHED"
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_JUDGED"] is False
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_timeout(self, runner, approved):
        artifact, _, report = self._artifact(
            runner, ScriptedTransport(raises=TimeoutError("synthetic timeout"))
        )
        assert report["outcome"] == "EXECUTION_FAILED_TIMEOUT_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is False
        assert artifact["RAW_PROVIDER_RESPONSE_BODY"] == "NOT_AVAILABLE"
        assert artifact["transport_errors"]
        assert artifact["TERMINAL_OUTCOME"] == "EXECUTION_FAILED_TIMEOUT_NO_RETRY"

    def test_retention_on_a_provider_refusal(self, runner, bounded, approved):
        artifact, _, report = self._artifact(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "refusal"))
        )
        assert report["outcome"] == "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["STOP_REASON"] == "refusal"
        assert artifact["PARSED_OUTPUT_JUDGED"] is False

    def test_retention_on_an_unsupported_stop_reason(self, runner, bounded, approved):
        artifact, _, report = self._artifact(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "end_turn"))
        )
        assert report["outcome"] == "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["STOP_REASON"] == "end_turn"
        assert artifact["PROVIDER_COMPLETION"] == report["completion"] != "COMPLETE"
        assert artifact["PARSED_OUTPUT_JUDGED"] is False

    def test_retention_on_a_parse_failure(self, runner, approved):
        artifact, _, report = self._artifact(
            runner, ScriptedTransport(body=_body(None, "tool_use"))
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_STRUCTURED_PARSE_NO_RETRY"
        assert report["failed_stage"] == "4_structured_output_parse"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_RETAINED"] is False

    def test_retention_on_a_schema_failure(self, runner, approved):
        artifact, _, report = self._artifact(
            runner, ScriptedTransport(body=_body(_required_keys_only(), "tool_use"))
        )
        assert report["failed_stage"] == "5_schema_validation_v1_1_0"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_semantic_failure(self, runner, bounded, approved):
        artifact, _, report = self._artifact(
            runner, ScriptedTransport(body=_body(_schema_valid_output(bounded), "tool_use"))
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_SEMANTIC_GATE_NO_RETRY"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_JUDGED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_provenance_failure(self, runner, bounded, approved):
        context = _context()
        context["representation"] = ""
        artifact, _, report = self._artifact(
            runner,
            ScriptedTransport(body=_body(_citing_output(bounded), "tool_use")),
            context,
            semantic_gate=_accepting_gate(),
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_REJECTED_AT_ATTRIBUTION_NO_RETRY"
        assert report["failed_stage"] == "8_attribution_and_provenance"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_retention_on_a_human_review_ready_success(self, runner, bounded, approved):
        artifact, _, report = self._artifact(
            runner,
            ScriptedTransport(body=_body(_citing_output(bounded), "tool_use")),
            semantic_gate=_accepting_gate(),
        )
        assert report["outcome"] == "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"
        assert report["stages"]["9_persistence_eligibility"] == "ELIGIBLE_FOR_HUMAN_REVIEW_ONLY"
        assert report["stages"]["10_human_review"] == "REQUIRED_NOT_PERFORMED"
        assert report["provenance"]["provider_request_id"] == REQUEST_ID
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    # -- the properties every path keeps -----------------------------------------------------

    def test_usage_is_retained_from_the_response_when_the_gateway_refused(self, runner, approved):
        partial = {"decision": "FORM_HYPOTHESIS"}
        artifact, result, _ = self._artifact(
            runner, ScriptedTransport(body=_body(partial, "max_tokens", usage=(4321, 1234)))
        )
        assert result["failure"] is not None
        assert artifact["USAGE_FROM_RESPONSE"] == {"input_tokens": 4321, "output_tokens": 1234}
        assert artifact["USAGE_RETAINED"] is True

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
        assert artifact["execution_packet_id"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V3"

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

    def test_a_credential_shape_is_redacted_from_the_body(self, runner, approved):
        leaked = "echoed key sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAA"
        body = _body(None, "max_tokens", extra_blocks=({"type": "text", "text": leaked},))
        artifact, _, _ = self._artifact(runner, ScriptedTransport(body=body))
        written = json.dumps(artifact)
        assert "sk-ant-api03" not in written
        assert "[REDACTED]" in written

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

    def test_the_fail_safe_keeps_the_bytes_when_judging_fails(self, runner, approved, monkeypatch):
        result, context = _run(runner, ScriptedTransport(body=_body(None, "max_tokens")))

        def broken(*args, **kwargs):
            raise RuntimeError("synthetic failure after the call")

        monkeypatch.setattr(runner, "validate_execution", broken)
        report, text = runner.settle(result, context)
        kept = json.loads(text)
        assert report["outcome"] == runner.POST_CALL_FAILURE
        assert kept["POST_CALL_HANDLING_FAILED"] is True
        assert kept["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert kept["transport_responses"][0]["body"]["stop_reason"] == "max_tokens"
        assert kept["execution_packet_id"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V3"
        assert kept["PERSISTED"] == "NOTHING"
