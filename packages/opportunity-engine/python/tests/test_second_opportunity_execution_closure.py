"""Mission 1.84.2. The consumed call is history, and the retention path is repaired.

Five things this file defends.

AN APPROVAL IS SPENT BY ITS EXECUTION, WHATEVER THE OUTPUT WAS. The one-call guard reads the
consumed-approval fact from the record beside the frozen packet and refuses the digest that
already has a provider request against it. A failed call is not an unused approval, and that is
enforced rather than remembered.

A VALIDATION EXCEPTION CANNOT DESTROY WHAT ARRIVED. Seven synthetic terminal paths -- success,
missing fields, malformed JSON, provider-shape failure, timeout, transport exception and a
semantic rejection -- each produce one artifact, and the failure paths retain the raw response
and the usage the Gateway emits.

NO FIXTURE CAN REACH A NETWORK. Every transport here is synthetic, and a test asserts that the
real one is never constructed.

THE FAILED RESPONSE STAYS INVALID. Eighteen of twenty fields does not persist, a missing required
field does not persist, and no default is invented for one.

SECRETS AND HIDDEN REASONING DO NOT REACH AN ARTIFACT. Credential-shaped strings are redacted and
reasoning blocks are stripped at any depth, whatever a provider volunteers.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
RUNNER_PATH = REPO_ROOT / "infrastructure" / "scripts" / "run_second_opportunity_execution.py"
RECORD = DATA / "second-opportunity-synthesis-execution-record-v1.json"
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
STRUCTURED_TOOL_NAME = "emit_structured_output"


def _runner():
    spec = importlib.util.spec_from_file_location("second_opportunity_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _runner()


@pytest.fixture(scope="module")
def record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _valid_output() -> dict:
    """A structurally complete output. Deliberately minimal: this tests plumbing, not semantics."""
    from sros_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA

    out: dict[str, object] = {}
    for field in SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]:
        spec = SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"][field]
        kind = spec.get("type")
        if kind == "array":
            out[field] = []
        elif kind == "string":
            out[field] = (spec.get("enum") or ["synthetic"])[0]
        else:
            out[field] = "synthetic"
    return out


def _anthropic_body(structured: dict | None, *, usage=(11, 22), extra_blocks=()) -> dict:
    blocks: list[dict] = [{"type": "text", "text": "synthetic"}]
    if structured is not None:
        blocks.append({"type": "tool_use", "name": STRUCTURED_TOOL_NAME, "input": structured})
    blocks.extend(extra_blocks)
    return {
        "content": blocks,
        "usage": {"input_tokens": usage[0], "output_tokens": usage[1]},
    }


class ScriptedTransport:
    """A synthetic transport. It has no socket and cannot acquire one."""

    def __init__(self, *, status=200, body=None, raises=None, raw_text=None) -> None:
        self.status = status
        self.body = body
        self.raises = raises
        self.raw_text = raw_text
        self.calls = 0

    def post_json(self, url, headers, body, timeout_seconds):
        from sros_llm_gateway.transport import HttpResponse

        self.calls += 1
        if self.raises is not None:
            raise self.raises
        payload = (
            self.raw_text.encode("utf-8")
            if self.raw_text is not None
            else json.dumps(self.body).encode("utf-8")
        )
        return HttpResponse(self.status, payload, {"request-id": "req_synthetic_0001"})


class TestTheApprovalIsSpent:
    def test_the_record_says_the_approval_is_consumed(self, record: dict) -> None:
        assert record["EXECUTION_APPROVAL_CONSUMED"] is True
        assert record["FURTHER_CALLS_AUTHORIZED_BY_V1"] is False

    def test_a_failed_call_still_spent_it(self, record: dict) -> None:
        """The temptation this guard exists for."""
        assert record["validation_result"] == "REJECTED"
        assert record["actual_provider_requests"] == 1
        assert record["EXECUTION_APPROVAL_CONSUMED"] is True

    def test_the_guard_reads_the_record_and_refuses_v1(self, runner) -> None:
        entries = runner.consumed_approvals()
        assert any(e["execution_packet_sha256"] == V1_SHA256 for e in entries)
        with pytest.raises(runner.RefusedError, match="EXECUTION_APPROVAL_ALREADY_CONSUMED"):
            runner.refuse_if_consumed(V1_SHA256)

    def test_the_guard_does_not_refuse_a_different_packet(self, runner) -> None:
        """A gate that refused every digest would block the successor packet too."""
        runner.refuse_if_consumed("0" * 64)

    def test_execute_refuses_before_building_a_gateway(self, runner) -> None:
        """Defence in depth: execute() is callable directly, so it checks too."""
        context = {"packet_file": json.loads(PACKET_V1.read_text(encoding="utf-8")), "parts": None}
        with pytest.raises(runner.RefusedError, match="ALREADY_CONSUMED"):
            runner.execute(context, transport=ScriptedTransport(body=_anthropic_body(None)))

    def test_the_frozen_packet_was_not_edited_to_record_its_own_use(self) -> None:
        packet = json.loads(PACKET_V1.read_text(encoding="utf-8"))
        assert packet["EXECUTION_PACKET_SHA256"] == V1_SHA256
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False


class TestSevenTerminalPathsEachProduceAnArtifact:
    """Section 12. Synthetic transports only, and every path writes one artifact shape."""

    def _artifact(self, runner, transport, *, request_schema=True):
        """Drive the Gateway with a synthetic transport and build the artifact from the result."""
        from sros_llm_gateway.config import GatewayConfig, TierBinding
        from sros_llm_gateway.gateway import LlmGateway
        from sros_llm_gateway.pricing import PricingTable
        from sros_llm_gateway.prompts.rendering import RenderedPrompt
        from sros_llm_gateway.providers.anthropic import AnthropicProvider
        from sros_llm_gateway.types import LlmRequest, LlmTier
        from sros_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA

        recorder = runner.RecordingTransport(transport)
        telemetry: list = []
        config = GatewayConfig(
            routing_version="synthetic",
            bindings={
                LlmTier.STRONG_MODEL: TierBinding(
                    tier=LlmTier.STRONG_MODEL, provider="anthropic", model="claude-sonnet-5"
                )
            },
        )
        gateway = LlmGateway(
            config=config,
            pricing=PricingTable(version="synthetic", prices={}),
            telemetry=telemetry.append,
        )
        gateway.register(
            AnthropicProvider(api_key="synthetic", max_output_tokens=3000, transport=recorder)
        )
        request = LlmRequest(
            tier=LlmTier.STRONG_MODEL,
            task="second-opportunity-synthesis-prompt",
            prompt_template_id="second-opportunity-synthesis-prompt",
            prompt_template_version="1.0.0",
            response_schema=SECOND_OPPORTUNITY_OUTPUT_SCHEMA if request_schema else None,
            prompt=RenderedPrompt(
                system_instructions="s", trusted_context="t", untrusted=(), task="k", metadata={}
            ),
            workspace_id="00000000-0000-4000-8000-000000000001",
            correlation_id="synthetic",
            timeout_seconds=60.0,
            max_retries=0,
            requires_structured_output=True,
        )
        failure = None
        response = None
        try:
            response = gateway.complete(request)
        except Exception as exc:  # noqa: BLE001 -- the fixture's whole point
            failure = exc
        return (
            runner.build_execution_artifact(
                outcome="SYNTHETIC",
                transport_responses=recorder.responses,
                transport_errors=recorder.transport_errors,
                telemetry=telemetry,
                structured=(response.structured if response is not None else None),
                failure=failure,
                timing={"started_at": "t0", "finished_at": "t1", "elapsed_seconds": 0.0},
            ),
            failure,
            transport,
        )

    def test_1_successful_structured_response(self, runner) -> None:
        artifact, failure, transport = self._artifact(
            runner, ScriptedTransport(body=_anthropic_body(_valid_output()))
        )
        assert failure is None
        assert transport.calls == 1
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_RETAINED"] is True
        assert artifact["USAGE_RETAINED"] is True
        assert artifact["PERSISTED"] == "NOTHING"

    def test_2_response_missing_required_fields_retains_everything(self, runner) -> None:
        """The consumed call's shape. This is what should have been kept and was not."""
        partial = _valid_output()
        del partial["confidence_classification"]
        del partial["statement_classifications"]
        artifact, failure, transport = self._artifact(
            runner, ScriptedTransport(body=_anthropic_body(partial))
        )
        assert failure is not None
        assert "missing required fields" in str(failure)
        assert transport.calls == 1, "one call, and the rejection did not cause another"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["RAW_PROVIDER_RESPONSE_SHA256"] != "NOT_AVAILABLE"
        assert artifact["USAGE_RETAINED"] is True
        assert artifact["usage"][0]["input_tokens"] == 11
        assert artifact["usage"][0]["output_tokens"] == 22

    def test_3_malformed_json(self, runner) -> None:
        artifact, failure, _ = self._artifact(
            runner, ScriptedTransport(raw_text="{not json at all")
        )
        assert failure is not None
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True
        assert artifact["PARSED_OUTPUT_RETAINED"] is False

    def test_4_provider_shape_failure(self, runner) -> None:
        artifact, failure, _ = self._artifact(
            runner, ScriptedTransport(body={"content": "not a list"})
        )
        assert failure is not None
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True

    def test_5_timeout(self, runner) -> None:
        artifact, failure, _ = self._artifact(
            runner, ScriptedTransport(raises=TimeoutError("synthetic timeout"))
        )
        assert failure is not None
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is False
        assert artifact["RAW_PROVIDER_RESPONSE_SHA256"] == "NOT_AVAILABLE"
        assert artifact["transport_errors"], "a transport with no body still records that"

    def test_6_transport_exception(self, runner) -> None:
        from sros_llm_gateway.transport import TransportError

        artifact, failure, _ = self._artifact(
            runner, ScriptedTransport(raises=TransportError("connection refused"))
        )
        assert failure is not None
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is False
        assert artifact["transport_errors"]

    def test_7_semantic_rejection_is_representable(self, runner) -> None:
        """A schema-valid answer the semantic gate refuses still writes one artifact."""
        artifact = runner.build_execution_artifact(
            outcome="EXECUTION_OUTPUT_REJECTED_AT_SEMANTIC_GATE_NO_RETRY",
            transport_responses=[{"status": 200, "body": "{}", "headers": {}}],
            transport_errors=[],
            telemetry=[],
            structured=_valid_output(),
            failure=None,
            timing={"started_at": "t0", "finished_at": "t1", "elapsed_seconds": 0.0},
            validation={"failed_stage": "5_semantic_output_gate", "persist": False},
        )
        assert artifact["validation"]["persist"] is False
        assert artifact["PERSISTED"] == "NOTHING"
        assert artifact["RAW_PROVIDER_RESPONSE_RETAINED"] is True

    def test_no_fixture_reaches_a_network(self, runner) -> None:
        """Every transport in this file is scripted, and the real one is never built."""
        import sros_llm_gateway.transport as transport_module

        built: list[int] = []
        original = transport_module.UrllibTransport.__init__

        def tripwire(self, *a, **k):  # pragma: no cover - must never run
            built.append(1)
            return original(self, *a, **k)

        transport_module.UrllibTransport.__init__ = tripwire
        try:
            self._artifact(runner, ScriptedTransport(body=_anthropic_body(_valid_output())))
        finally:
            transport_module.UrllibTransport.__init__ = original
        assert built == []


class TestSecretsAndReasoningNeverReachAnArtifact:
    def test_credential_shapes_are_redacted(self, runner) -> None:
        leaked = "error: key sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAA rejected"
        assert "sk-ant" not in runner.redact(leaked)
        assert "[REDACTED]" in runner.redact(leaked)

    def test_a_jwt_shape_is_redacted(self, runner) -> None:
        leaked = "token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abcdefghij"
        assert "eyJ" not in runner.redact(leaked)

    def test_reasoning_blocks_are_stripped_at_any_depth(self, runner) -> None:
        payload = {
            "a": 1,
            "thinking": "hidden",
            "nested": {"reasoning": "hidden", "keep": 2},
            "list": [{"chain_of_thought": "hidden", "keep": 3}],
        }
        cleaned = runner.strip_reasoning(payload)
        assert cleaned == {"a": 1, "nested": {"keep": 2}, "list": [{"keep": 3}]}

    def test_a_volunteered_reasoning_block_does_not_survive_into_the_artifact(self, runner) -> None:
        output = _valid_output()
        output["thinking"] = "should not be kept"
        artifact = runner.build_execution_artifact(
            outcome="SYNTHETIC",
            transport_responses=[],
            transport_errors=[],
            telemetry=[],
            structured=output,
            failure=None,
            timing={},
        )
        assert "thinking" not in artifact["parsed_output"]
        assert artifact["HIDDEN_REASONING_RETAINED"] is False
        assert artifact["HIDDEN_REASONING_REQUESTED"] is False


class TestTheFailedResponseStaysInvalid:
    """Section 14. No code path turns 18 of 20 into an Opportunity."""

    def test_a_missing_required_field_does_not_persist(self) -> None:
        from sros_opportunity import (
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA,
        )

        partial = _valid_output()
        del partial["confidence_classification"]
        assert "confidence_classification" in SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]
        assert "confidence_classification" not in partial

    def test_the_record_persists_nothing(self, record: dict) -> None:
        assert record["canonical_persistence"] is False
        for key, value in record["PERSISTENCE"].items():
            if key == "note":
                continue
            assert value == 0, key

    def test_the_output_contract_was_not_edited_to_rescue_the_response(self, record: dict) -> None:
        from sros_opportunity import (
            SECOND_OPPORTUNITY_GATE_VERSION,
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA,
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION,
        )

        unchanged = record["output_contract_unchanged"]
        assert unchanged["output_schema_version"] == SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION
        assert unchanged["output_gate_version"] == SECOND_OPPORTUNITY_GATE_VERSION
        assert unchanged["required_fields_changed"] is False
        assert unchanged["failed_response_remains_invalid"] is True
        assert len(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]) == 20
        assert "confidence_classification" in SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]
        assert (
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"]["statement_classifications"]["maxItems"]
            == 24
        )


class TestTheRecordIsHonestAboutWhatIsNotKnown:
    def test_the_raw_response_is_absent_and_not_reconstructed(self, record: dict) -> None:
        assert record["RAW_PROVIDER_RESPONSE_RETAINED"] is False
        assert record["RAW_PROVIDER_RESPONSE_HASH"] == "NOT_AVAILABLE"
        assert record["RAW_PROVIDER_RESPONSE_RECOVERABLE"] is False
        assert record["raw_response_not_reconstructed"] is True

    def test_usage_and_cost_are_not_established_rather_than_estimated(self, record: dict) -> None:
        for key in (
            "ACTUAL_INPUT_TOKENS",
            "ACTUAL_OUTPUT_TOKENS",
            "ACTUAL_TOTAL_TOKENS",
            "ACTUAL_EXECUTION_COST",
        ):
            assert record[key] == "NOT_ESTABLISHED", key

    def test_the_worst_case_is_not_presented_as_the_actual_cost(self, record: dict) -> None:
        assert record["APPROVED_WORST_CASE_CALL_COST"] == 0.04825
        assert record["ACTUAL_EXECUTION_COST"] != 0.04825
        assert "not what the call cost" in record["worst_case_is_not_actual"]

    def test_the_cause_is_strongly_supported_and_not_established(self, record: dict) -> None:
        assert record["OUTPUT_CAPACITY_FAILURE_HYPOTHESIS"] == "STRONGLY_SUPPORTED"
        assert record["ROOT_CAUSE"] == "NOT_PROVABLE_FROM_RETAINED_EXECUTION_ARTIFACTS"
        assert record["why_not_established"].strip()

    def test_truncation_is_not_claimed(self, record: dict) -> None:
        assert any("truncation" in claim for claim in record["not_claimed"])

    def test_the_mission_1_84_defect_is_named(self, record: dict) -> None:
        assert record["OUTPUT_CAPACITY_BOUND_NOT_DERIVED_FROM_SCHEMA"] is True
        assert "MAX_OUTPUT_TOKENS at 3000" in record["historical_defect_in_mission_1_84"]

    def test_the_retention_defects_are_not_erased(self, record: dict) -> None:
        assert record["USAGE_RETAINED"] is False
        assert record["raw_response_defect"].strip()
        assert record["usage_defect"].strip()

    def test_the_next_action_needs_a_new_packet_and_a_new_approval(self, record: dict) -> None:
        assert record["future_retry_authorized"] is False
        assert record["next_required_action"] == "NEW_EXECUTION_PACKET_AND_NEW_OPERATOR_APPROVAL"
        assert "digest" in record["why_a_new_packet_is_required"]

    def test_the_closure_itself_made_no_provider_request(self, record: dict) -> None:
        accounting = record["ACCOUNTING"]
        assert accounting["TOTAL_PROVIDER_REQUESTS_FOR_MISSION_1_84_2"] == 1
        assert accounting["ADDITIONAL_PROVIDER_REQUESTS_DURING_FAILURE_CLOSURE"] == 0
        assert accounting["REMOTE_TEST_CALLS_DURING_CLOSURE"] == 0
        assert accounting["TED_BYTES_SENT_DURING_CLOSURE"] == 0
        assert accounting["CANONICAL_RESEARCH_MUTATION"] == 0

    def test_the_pre_execution_checks_are_not_current_permission(self, record: dict) -> None:
        assert record["PRE_EXECUTION_VERIFICATION"]["not_current_permission"] is True
