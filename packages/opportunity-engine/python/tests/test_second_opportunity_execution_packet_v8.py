"""Mission 1.84.20. CI gate 95 over execution packet V8, and the refusals it must make.

The whole gate runs once. Every refusal feeds one of its checks a deep copy of the packet with one field
changed, so the committed packet is never touched and each refusal is attributed to the check that
makes it. Nothing here reaches a network: request bodies are built and never sent.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
from typing import Any

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "infrastructure" / "scripts"
V7_SHA256 = "51023d0d2ed780db4c7d5018a289939e7c9c83061f8768051ef1cd7b8ae674e8"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module(
        "gate_95_under_test", SCRIPTS / "render_second_opportunity_execution_packet_v8.py"
    )


@pytest.fixture(scope="module")
def packet(gate) -> dict[str, Any]:
    return json.loads(gate.PACKET.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def snap(gate) -> tuple[Any, Any, Any]:
    return gate.snapshot()


def _changed(gate, packet: dict[str, Any], change, *, redigest: bool = True) -> dict[str, Any]:
    mutated = copy.deepcopy(packet)
    change(mutated)
    if redigest:
        mutated["EXECUTION_PACKET_SHA256"] = gate.packet_digest(mutated)
    return mutated


class TestTheCommittedPacket:
    def test_the_packet_validates(self, gate):
        packet = gate.validate()
        assert packet["PRIMARY_OUTCOME"] == gate.READY

    def test_the_page_is_the_rendering(self, gate, packet):
        assert gate.PACKET_MD.read_text(encoding="utf-8") == gate.render_packet(packet)

    def test_the_approval_surface(self, gate, packet):
        assert packet["EXECUTION_PACKET_ID"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V8"
        assert packet["EXECUTION_PACKET_VERSION"] == 8
        assert packet["PREDECESSOR_EXECUTION_PACKET_SHA256"] == V7_SHA256
        assert packet["PREDECESSOR_STATUS"] == "SUPERSEDED_BEFORE_EXECUTION"
        assert packet["PREDECESSOR_EXECUTED"] is False
        assert packet["PREDECESSOR_APPROVED"] is False
        assert packet["PREDECESSOR_APPROVAL_CONSUMED"] is False
        assert packet["LAST_EXECUTED_PREDECESSOR_SHA256"] == gate.V6_SHA256
        assert packet["LAST_EXECUTED_PREDECESSOR_OUTCOME"] == "EXECUTION_SCHEMA_REJECTED_NO_RETRY"
        assert packet["OUTPUT_SCHEMA_VERSION"] == "second-opportunity-synthesis-output@1.2.0"
        assert packet["OUTPUT_GATE_VERSION"] == "second-opportunity-output-gate@1.4.0"
        assert packet["PROMPT_VERSION"] == "1.5.0"
        assert packet["PROVIDER_STRICT_MODE"] is True
        assert (
            packet["STRICT_PROJECTION_FREEZE_COMMIT"] == "57154affb934516650b84480c2438a75c9b9a5a5"
        )
        assert (packet["MAX_OUTPUT_TOKENS"], packet["MAX_MODEL_CALLS"], packet["MAX_RETRIES"]) == (
            128000,
            1,
            0,
        )
        assert packet["REQUEST_TIMEOUT"] == 60.0
        assert packet["HARD_EXECUTION_COST_CEILING"] == "3.608"
        assert packet["HARD_EXECUTION_COST_CEILING_PROVEN"] is True
        assert packet["PLANNING_COST_ESTIMATE"] == "1.316316"
        assert packet["PLANNING_COST_ESTIMATE"] != packet["HARD_EXECUTION_COST_CEILING"]
        assert packet["RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8"] is False
        assert packet["STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8"] is False
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False
        assert packet["NEW_APPROVAL_REQUIRED"] is True
        assert packet["PREVIOUS_APPROVAL_REUSABLE"] is False

    def test_no_v7_cost_field_survives(self, gate, packet):
        for key in gate.V7_COST_FIELDS:
            assert key not in packet

    def test_no_approval_exists_beside_the_packet(self, gate):
        assert not gate.APPROVAL.exists()

    def test_the_request_is_v7s_bytes(self, packet):
        differential = packet["REQUEST_BODY_DIFFERENTIAL"]
        assert differential["byte_identical"] is True
        assert differential["differences"] == []
        assert differential["REQUEST_BODY_DIFFERENCES_V7_TO_V8"] == 0
        assert differential["v7_body_sha256"] == differential["v8_body_sha256"]


class TestIdentityAndApproval:
    def test_a_bound_field_moved_without_its_digest_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p.__setitem__("HARD_EXECUTION_COST_CEILING", "1.316316"),
            redigest=False,
        )
        with pytest.raises(gate.ValidationError, match="hash"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8", True),
            ("STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8", True),
            ("OPERATOR_EXECUTION_APPROVAL_RECORDED", True),
            ("PREVIOUS_APPROVAL_REUSABLE", True),
            ("HUMAN_REVIEW_REQUIRED", False),
        ],
    )
    def test_an_approval_or_risk_flag_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize(
        "key",
        [
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V7",
            "EXECUTION_COST_CEILING",
            "WORST_CASE_CALL_COST",
        ],
    )
    def test_a_v7_field_brought_back_is_refused(self, gate, packet, key):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, 1.316316), redigest=False)
        with pytest.raises(gate.ValidationError, match="nothing reviews"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize("word", ["V7", "superseded", "timeout", "residual", "V6"])
    def test_an_approval_note_that_forgets_a_distinction_is_refused(self, gate, packet, word):
        mutated = _changed(
            gate,
            packet,
            lambda p: p.__setitem__("approval_note", p["approval_note"].replace(word, "other")),
        )
        with pytest.raises(gate.ValidationError, match="approval note"):
            gate._check_identity_and_approval(mutated)

    def test_a_spent_digest_is_refused(self, gate, packet, monkeypatch):
        monkeypatch.setattr(gate, "SHAS", (*gate.SHAS, gate.packet_digest(packet)))
        with pytest.raises(gate.ValidationError, match="spent or superseded"):
            gate._check_identity_and_approval(packet)

    def test_v7s_digest_is_refused(self, gate, packet, monkeypatch):
        monkeypatch.setattr(gate, "V7_SHA256", gate.packet_digest(packet))
        with pytest.raises(gate.ValidationError, match="spent or superseded"):
            gate._check_identity_and_approval(packet)

    def test_an_approval_recorded_by_this_mission_is_refused(
        self, gate, packet, tmp_path, monkeypatch
    ):
        approval = tmp_path / gate.APPROVAL.name
        approval.write_text(
            json.dumps(
                {
                    "recorded_by": "mission-1.84.20",
                    "EXECUTION_PACKET_SHA256": packet["EXECUTION_PACKET_SHA256"],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(gate, "APPROVAL", approval)
        with pytest.raises(gate.ValidationError, match="prepared it"):
            gate._check_identity_and_approval(packet)

    def test_a_v6_approval_placed_beside_v8_is_refused(self, gate, packet, tmp_path, monkeypatch):
        approval = tmp_path / gate.APPROVAL.name
        approval.write_text(
            json.dumps({"recorded_by": "mission-9.9.9", "EXECUTION_PACKET_SHA256": gate.V6_SHA256}),
            encoding="utf-8",
        )
        monkeypatch.setattr(gate, "APPROVAL", approval)
        with pytest.raises(gate.ValidationError, match="other than V8's"):
            gate._check_identity_and_approval(packet)


class TestPredecessorsAndSupersession:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("PREDECESSOR_EXECUTION_PACKET_SHA256", "0" * 64),
            ("PREDECESSOR_STATUS", "CONSUMED"),
            ("PREDECESSOR_STATUS", "FAILED"),
            ("PREDECESSOR_EXECUTED", True),
            ("PREDECESSOR_APPROVED", True),
            ("PREDECESSOR_APPROVAL_CONSUMED", True),
            ("LAST_EXECUTED_PREDECESSOR_SHA256", "0" * 64),
            ("LAST_EXECUTED_PREDECESSOR_SCHEMA_VIOLATION", "LENGTH_BOUND"),
            ("V7_SUPERSESSION_RECORD_SHA256", "0" * 64),
        ],
    )
    def test_a_predecessor_field_moved_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_predecessors(mutated)

    def test_a_consumed_list_without_v6_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p["CONSUMED_EXECUTION_PACKETS"].pop())
        with pytest.raises(gate.ValidationError, match="CONSUMED_EXECUTION_PACKETS"):
            gate._check_predecessors(mutated)

    def test_v7_listed_as_consumed_is_refused(self, gate, packet):
        def consume(p):
            p["CONSUMED_EXECUTION_PACKETS"].append(
                {"id": gate.V7_ID, "sha256": V7_SHA256, "outcome": "CONSUMED"}
            )

        mutated = _changed(gate, packet, consume)
        with pytest.raises(gate.ValidationError, match="CONSUMED_EXECUTION_PACKETS"):
            gate._check_predecessors(mutated)

    def test_an_omitted_supersession_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("SUPERSEDED_EXECUTION_PACKETS", [])
        )
        with pytest.raises(gate.ValidationError, match="SUPERSEDED_EXECUTION_PACKETS"):
            gate._check_predecessors(mutated)

    def test_a_v7_reconfirmation_edited_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p["V7_RECONFIRMATION"].__setitem__("approval_recorded", True)
        )
        with pytest.raises(gate.ValidationError, match="V7_RECONFIRMATION"):
            gate._check_v7_reconfirmation(mutated)


class TestWhatDidNotMove:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("SCHEMA_CHANGED", True),
            ("REASONING_SUMMARY_HARD_MAX", 1501),
            ("OUTPUT_SCHEMA_SHA256", "0" * 64),
            ("SEMANTIC_GATE_IMPLEMENTATION_SHA256", "0" * 64),
        ],
    )
    def test_a_moved_contract_field_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError):
            gate._through(gate.G93._check_contract_and_gate, mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("PROVIDER_STRICT_MODE", False),
            ("PROVIDER_STRICT_SCHEMA_SHA256", "0" * 64),
            ("STRICT_CAPABILITY_PROFILE_SHA256", "0" * 64),
            ("STRICT_PROJECTION_FREEZE_COMMIT", "0" * 40),
        ],
    )
    def test_a_strict_field_moved_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._through(gate.G93._check_strict, mutated)

    def test_a_prompt_change_is_refused(self, gate, packet, snap):
        mutated = _changed(
            gate, packet, lambda p: p["PROMPT_DECISION"].__setitem__("PROMPT_TEXT_CHANGED", True)
        )
        with pytest.raises(gate.ValidationError, match="PROMPT_TEXT_CHANGED"):
            gate._through(gate.G93._check_prompt, mutated, snap[1])

    @pytest.mark.parametrize(
        "key, value",
        [("MODEL_ID", "claude-opus-5"), ("THINKING", "ADAPTIVE"), ("MAX_OUTPUT_TOKENS", 64000)],
    )
    def test_a_moved_route_field_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._through(gate.G93._check_route, mutated)

    def test_a_silently_changed_timeout_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p.__setitem__("REQUEST_TIMEOUT", 180.0))
        with pytest.raises(gate.ValidationError, match="timeout"):
            gate._check_calls_and_timeout(mutated)

    def test_a_silently_accepted_timeout_risk_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["TIMEOUT"].__setitem__(
                "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8", True
            ),
        )
        with pytest.raises(gate.ValidationError, match="STRICT_FIRST_REQUEST_TIMEOUT_RISK"):
            gate._check_calls_and_timeout(mutated)


class TestTheRequest:
    def _patched(self, gate, monkeypatch, change):
        honest = gate.request_bodies

        def drifted(parts, p):
            v7, v8 = honest(parts, p)
            v8 = copy.deepcopy(v8)
            change(v8)
            return v7, v8

        monkeypatch.setattr(gate, "request_bodies", drifted)

    @pytest.mark.parametrize(
        "change",
        [
            lambda b: b.__setitem__("temperature", 0.0),
            lambda b: b["tools"][0].__setitem__("strict", False),
            lambda b: b.__setitem__("cache_control", {"type": "ephemeral"}),
            lambda b: b.__setitem__("inference_geo", "global"),
            lambda b: b.__setitem__("max_tokens", 64000),
        ],
        ids=["temperature", "strict_off", "cache", "geo", "max_tokens"],
    )
    def test_a_body_that_is_not_v7s_bytes_is_refused(self, gate, packet, snap, monkeypatch, change):
        self._patched(gate, monkeypatch, change)
        with pytest.raises(gate.ValidationError, match="V8_REQUEST_BODY_HAS_UNAPPROVED_DRIFT"):
            gate._check_request(packet, snap[1])

    def test_a_forged_differential_is_refused(self, gate, packet, snap):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["REQUEST_BODY_DIFFERENTIAL"].__setitem__("v8_body_characters", 1),
        )
        with pytest.raises(gate.ValidationError, match="REQUEST_BODY_DIFFERENTIAL"):
            gate._check_request(mutated, snap[1])

    def test_a_body_the_strict_adapter_refuses_is_a_named_refusal(
        self, gate, packet, snap, monkeypatch
    ):
        from sros_llm_gateway.types import ProviderInvalidRequestError

        honest = gate.runner

        def refusing():
            module = honest()

            def request_body(parts, p):
                raise ProviderInvalidRequestError(
                    "outside the reviewed subset", provider="anthropic"
                )

            module.request_body = request_body
            return module

        monkeypatch.setattr(gate, "runner", refusing)
        with pytest.raises(gate.ValidationError, match="cannot be built"):
            gate._check_request(packet, snap[1])


class TestCost:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("HARD_EXECUTION_COST_CEILING", "1.316316"),
            ("HARD_EXECUTION_COST_CEILING", "3.28"),
            ("MAX_BILLABLE_INPUT_TOKENS", 18158),
            ("MAX_BILLABLE_INPUT_TOKENS", 12903),
            ("DATA_RESIDENCY_MULTIPLIER", "1"),
            ("HARD_EXECUTION_COST_CEILING_PROVEN", False),
            ("UNKNOWN_COST_CATEGORIES", ["STRICT_SCHEMA_COMPILATION_FEE"]),
            ("PLANNING_COST_ESTIMATE", "3.608"),
            ("PLANNING_COST_ESTIMATE_CLASSIFICATION", "HARD_CEILING"),
        ],
    )
    def test_a_cost_figure_that_is_not_gate_94s_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_cost(mutated)

    def test_v7s_figure_brought_back_as_a_ceiling_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("EXECUTION_COST_CEILING", 1.316316)
        )
        with pytest.raises(gate.ValidationError, match="ESTIMATE_CALLED_HARD_CEILING"):
            gate._check_cost(mutated)

    def test_another_cost_record_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("COST_CEILING_RECORD_SHA256", "0" * 64)
        )
        with pytest.raises(gate.ValidationError, match="another cost-ceiling record"):
            gate._check_cost(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("covers_the_strict_format_prompt", True),
            ("strict_format_prompt_tokens", 0),
            ("is_a_bound", True),
            ("classification", "WORST_CASE"),
        ],
    )
    def test_an_estimate_said_to_bound_or_cover_is_refused(self, gate, packet, key, value):
        mutated = _changed(
            gate, packet, lambda p: p["PLANNING_ESTIMATION_BASIS"].__setitem__(key, value)
        )
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_cost(mutated)

    def test_observed_usage_used_for_the_ceiling_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["OBSERVED_USAGE_NOT_USED"].__setitem__("USED_FOR_THE_HARD_CEILING", True),
        )
        with pytest.raises(gate.ValidationError, match="USED_FOR_THE_HARD_CEILING"):
            gate._check_cost(mutated)


class TestVerificationPreflightAndAccounting:
    def test_verification_that_found_v7_executable_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["PREPARATION_VERIFICATION"].__setitem__("v7_refused_as_superseded", False),
        )
        with pytest.raises(gate.ValidationError, match="v7_refused_as_superseded"):
            gate._check_verification(mutated)

    def test_a_preflight_row_edited_is_refused(self, gate, packet):
        def lie(p):
            p["V8_PREFLIGHT"][-1]["stopped_at"] = None

        mutated = _changed(gate, packet, lie)
        with pytest.raises(gate.ValidationError, match="V8_PREFLIGHT"):
            gate._check_preflight(mutated)

    def test_the_extra_key_and_the_bound_cases_are_in_the_preflight(self, packet):
        rows = {row["fixture"]: row for row in packet["V8_PREFLIGHT"]}
        assert rows["J_EXTRA_ROOT_PROPERTY_REFUSED_AT_LOCAL_STAGE_5"]["stopped_at"] == (
            "5_schema_validation_v1_2_0"
        )
        assert (
            rows["I_SUMMARY_ONE_OVER_THE_NEW_BOUND"]["stopped_at"] == "5_schema_validation_v1_2_0"
        )
        assert rows["H_SUMMARY_AT_THE_NEW_BOUND"]["stopped_at"] is None
        assert rows["F_LONG_SUMMARY_POSITIVE"]["summary_characters"] == 1189

    @pytest.mark.parametrize(
        "key",
        ["MODEL_CALLS", "MESSAGES_API_REQUESTS", "TOKEN_COUNT_API_REQUESTS", "TED_BYTES_SENT"],
    )
    def test_a_preparation_call_is_refused(self, gate, packet, key):
        mutated = _changed(gate, packet, lambda p: p["preparation_accounting"].__setitem__(key, 1))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_accounting(mutated)

    def test_documentation_reads_other_than_gate_94s_are_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["preparation_accounting"].__setitem__("DOCUMENTATION_FETCHES", 8),
        )
        with pytest.raises(gate.ValidationError, match="documentation reads"):
            gate._check_accounting(mutated)

    def test_a_moved_persistence_policy_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["PERSISTENCE_POLICY"].__setitem__("persist_if_gate_accepts", True),
        )
        with pytest.raises(gate.ValidationError, match="persistence policy"):
            gate._check_boundaries(mutated)


class TestTheRunner:
    def test_a_runner_prepared_for_another_digest_is_refused(self, gate, packet, snap):
        mutated = copy.deepcopy(packet)
        mutated["EXECUTION_PACKET_SHA256"] = "0" * 64
        with pytest.raises(gate.ValidationError, match="another digest"):
            gate._check_runner(mutated, snap[1], snap[2])

    def _with(self, gate, monkeypatch, change):
        honest = gate.runner

        def altered():
            module = honest()
            change(module)
            return module

        monkeypatch.setattr(gate, "runner", altered)

    def test_an_approval_check_with_one_risk_decision_is_refused(
        self, gate, packet, snap, monkeypatch
    ):
        self._with(
            gate,
            monkeypatch,
            lambda m: setattr(
                m,
                "RISK_DECISIONS",
                {
                    "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8": "RESIDUAL_SEMANTIC_LIMITATION_NOT_ACCEPTED"
                },
            ),
        )
        with pytest.raises(gate.ValidationError, match="both risk decisions"):
            gate._check_runner(packet, snap[1], snap[2])

    def test_a_guard_that_calls_v7_consumed_is_refused(self, gate, packet, snap, monkeypatch):
        def rename(module):
            honest = module.refuse_if_consumed

            def renamed(digest):
                if digest == V7_SHA256:
                    raise module.RefusedError("EXECUTION_APPROVAL_ALREADY_CONSUMED", "renamed")
                honest(digest)

            module.refuse_if_consumed = renamed

        self._with(gate, monkeypatch, rename)
        with pytest.raises(gate.ValidationError, match="not as superseded"):
            gate._check_runner(packet, snap[1], snap[2])

    def test_a_guard_that_lets_v7_through_is_refused(self, gate, packet, snap, monkeypatch):
        def let_through(module):
            honest = module.refuse_if_consumed

            def lenient(digest):
                if digest != V7_SHA256:
                    honest(digest)

            module.refuse_if_consumed = lenient

        self._with(gate, monkeypatch, let_through)
        with pytest.raises(gate.ValidationError, match="V7_STILL_EXECUTABLE"):
            gate._check_runner(packet, snap[1], snap[2])

    def test_other_cost_selectors_are_refused(self, gate, packet, snap, monkeypatch):
        self._with(
            gate,
            monkeypatch,
            lambda m: setattr(m, "COST_SELECTORS_REQUIRED", {"cache_control": True}),
        )
        with pytest.raises(gate.ValidationError, match="cost selectors"):
            gate._check_runner(packet, snap[1], snap[2])

    def test_the_shipped_approval_check_decides_both_risks(self, gate, packet):
        gate._check_approval_behaviour(gate.runner(), packet)
        assert not gate.APPROVAL.exists()

    def test_an_approval_check_that_ignores_the_risks_is_refused(self, gate, packet):
        module = gate.runner()
        honest = module.check_approval

        def lenient(sha):
            saved = module.RISK_DECISIONS
            module.RISK_DECISIONS = {}
            try:
                return honest(sha)
            finally:
                module.RISK_DECISIONS = saved

        module.check_approval = lenient
        with pytest.raises(gate.ValidationError, match="does not decide and accept both risks"):
            gate._check_approval_behaviour(module, packet)

    def test_an_approval_check_that_misnames_a_refusal_is_refused(self, gate, packet):
        module = gate.runner()
        module.RISK_DECISIONS = dict.fromkeys(module.RISK_DECISIONS, "OPERATOR_APPROVAL_INCOMPLETE")
        with pytest.raises(gate.ValidationError, match="it must say"):
            gate._check_approval_behaviour(module, packet)
