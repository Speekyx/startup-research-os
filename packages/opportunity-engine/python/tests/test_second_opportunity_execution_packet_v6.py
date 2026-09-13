"""Mission 1.84.17. CI gate 90 over execution packet V6, and the refusals it must make.

The whole gate runs once. Every refusal feeds one of its checks a deep copy of the packet with one field
changed, so the committed packet is never touched and each refusal is attributed to the check that
makes it. Nothing here reaches a network.
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


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module(
        "gate_90_under_test", SCRIPTS / "render_second_opportunity_execution_packet_v6.py"
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
        assert packet["EXECUTION_PACKET_ID"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V6"
        assert packet["EXECUTION_PACKET_VERSION"] == 6
        assert packet["PREDECESSOR_EXECUTION_PACKET_SHA256"] == gate.V5_SHA256
        assert packet["OUTPUT_SCHEMA_VERSION"] == "second-opportunity-synthesis-output@1.2.0"
        assert packet["OUTPUT_GATE_VERSION"] == "second-opportunity-output-gate@1.4.0"
        assert packet["PROMPT_VERSION"] == "1.5.0"
        assert (
            packet["REASONING_SUMMARY_HARD_MAX"],
            packet["REASONING_SUMMARY_GENERATION_TARGET"],
        ) == (
            1500,
            1200,
        )
        assert packet["THINKING"] == "DISABLED"
        assert (packet["MAX_OUTPUT_TOKENS"], packet["MAX_MODEL_CALLS"], packet["MAX_RETRIES"]) == (
            128000,
            1,
            0,
        )
        assert packet["REQUEST_TIMEOUT"] == 60.0
        assert packet["HUMAN_REVIEW_REQUIRED"] is True
        assert packet["RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6"] is False
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False
        assert packet["NEW_APPROVAL_REQUIRED"] is True
        assert packet["PREVIOUS_APPROVAL_REUSABLE"] is False
        assert packet["EXECUTION_COST_CEILING"] == packet["WORST_CASE_CALL_COST"]

    def test_the_approval_lives_beside_the_packet_and_names_its_digest(self, gate, packet):
        """Mission 1.84.18 recorded the operator's approval beside V6; the packet still records none."""
        approval = json.loads(gate.APPROVAL.read_text(encoding="utf-8"))
        assert approval["recorded_by"] == "mission-1.84.18"
        assert approval["EXECUTION_PACKET_SHA256"] == packet["EXECUTION_PACKET_SHA256"]
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False


class TestIdentityAndApproval:
    def test_a_bound_field_moved_without_its_digest_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("MAX_OUTPUT_TOKENS", 64000), redigest=False
        )
        with pytest.raises(gate.ValidationError, match="hash"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6", True),
            ("OPERATOR_EXECUTION_APPROVAL_RECORDED", True),
            ("PREVIOUS_APPROVAL_REUSABLE", True),
            ("HUMAN_REVIEW_REQUIRED", False),
        ],
    )
    def test_an_approval_or_risk_flag_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_identity_and_approval(mutated)

    def test_an_unreviewed_field_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p.__setitem__("APPROVED", True), redigest=False)
        with pytest.raises(gate.ValidationError, match="nothing reviews"):
            gate._check_identity_and_approval(mutated)

    def test_an_approval_note_that_forgets_the_residual_risk_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p.__setitem__(
                "approval_note", p["approval_note"].replace("residual", "other")
            ),
        )
        with pytest.raises(gate.ValidationError, match="approval note"):
            gate._check_identity_and_approval(mutated)

    def test_an_approval_recorded_by_this_mission_is_refused(
        self, gate, packet, tmp_path, monkeypatch
    ):
        approval = tmp_path / gate.APPROVAL.name
        approval.write_text(
            json.dumps(
                {
                    "recorded_by": "mission-1.84.17",
                    "EXECUTION_PACKET_SHA256": packet["EXECUTION_PACKET_SHA256"],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(gate, "APPROVAL", approval)
        with pytest.raises(gate.ValidationError, match="prepared it"):
            gate._check_identity_and_approval(packet)


class TestPredecessors:
    def test_another_predecessor_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("PREDECESSOR_EXECUTION_PACKET_SHA256", "0" * 64)
        )
        with pytest.raises(gate.ValidationError, match="PREDECESSOR"):
            gate._check_predecessors(mutated)

    def test_a_consumed_list_without_v5_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p["CONSUMED_EXECUTION_PACKETS"].pop())
        with pytest.raises(gate.ValidationError, match="CONSUMED"):
            gate._check_predecessors(mutated)


class TestContractAndGate:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("REASONING_SUMMARY_HARD_MAX", 900),
            ("REASONING_SUMMARY_GENERATION_TARGET", 720),
            ("OUTPUT_SCHEMA_VERSION", "second-opportunity-synthesis-output@1.1.0"),
            ("OUTPUT_GATE_VERSION", "second-opportunity-output-gate@1.3.0"),
            (
                "SEMANTIC_GATE_IMPLEMENTATION_SHA256",
                "cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3",
            ),
            ("SEMANTIC_GATE_FREEZE_COMMIT", "0" * 40),
            ("REASONING_SUMMARY_DECISION_BASIS", "DERIVED_FROM_V5"),
            ("CONTRACT_FULL_DOMAIN_REACHABLE_BY_SELECTED_MODEL", True),
        ],
    )
    def test_a_moved_contract_or_gate_field_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_contract_and_gate(mutated)

    def test_post_processing_to_fit_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p["OUTPUT_POST_PROCESSING"].__setitem__("TRUNCATION", True)
        )
        with pytest.raises(gate.ValidationError, match="changed to fit"):
            gate._check_contract_and_gate(mutated)


class TestTheCallIsV5s:
    def test_a_response_schema_back_at_v1_1_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["GENERATION_PARAMETERS"].__setitem__(
                "response_schema", "second-opportunity-synthesis-output@1.1.0"
            ),
        )
        with pytest.raises(gate.ValidationError, match="generation parameters"):
            gate._check_calls_and_timeout(mutated)

    def test_a_retry_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p.__setitem__("MAX_RETRIES", 1))
        with pytest.raises(gate.ValidationError):
            gate._check_calls_and_timeout(mutated)

    def test_the_old_stage_names_are_refused(self, gate, packet):
        def old_names(p):
            p["VALIDATION_STAGES"] = [
                s.replace("v1_2_0", "v1_1_0").replace("v1_4_0", "v1_3_0")
                for s in p["VALIDATION_STAGES"]
            ]

        mutated = _changed(gate, packet, old_names)
        with pytest.raises(gate.ValidationError, match="VALIDATION_STAGES"):
            gate._check_route(mutated)

    def test_a_ceiling_basis_that_forgets_v5_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p["MAX_OUTPUT_TOKENS_NOT_BASED_ON"].pop())
        with pytest.raises(gate.ValidationError, match="V5's observed output"):
            gate._check_route(mutated)

    def test_a_ceiling_other_than_the_recomputed_worst_case_is_refused(self, gate, packet, snap):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("EXECUTION_COST_CEILING", 1.317056)
        )
        _snap, parts, parts_v1_4 = snap
        with pytest.raises(gate.ValidationError, match="EXECUTION_COST_CEILING"):
            gate._check_cost(mutated, _snap, parts, parts_v1_4)


class TestBoundariesAccountingAndRunner:
    def test_persisting_on_acceptance_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["PERSISTENCE_POLICY"].__setitem__("persist_if_gate_accepts", True),
        )
        with pytest.raises(gate.ValidationError, match="persist_if_gate_accepts"):
            gate._check_boundaries(mutated)

    def test_a_retention_path_no_test_defines_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["RETENTION_VERIFIED_PATHS"].__setitem__(
                "timeout", "test_nothing_like_this"
            ),
        )
        with pytest.raises(gate.ValidationError, match="no V6 runner test"):
            gate._check_boundaries(mutated)

    def test_a_preparation_call_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p["preparation_accounting"].__setitem__("MODEL_CALLS", 1)
        )
        with pytest.raises(gate.ValidationError, match="MODEL_CALLS"):
            gate._check_accounting(mutated)

    def test_a_runner_prepared_for_another_digest_is_refused(self, gate, packet, snap):
        mutated = _changed(gate, packet, lambda p: p.__setitem__("prepared_at", "2026-09-14"))
        mutated["EXECUTION_PACKET_SHA256"] = "0" * 64
        _snap, parts, parts_v1_4 = snap
        with pytest.raises(gate.ValidationError, match="another digest"):
            gate._check_runner(mutated, parts, parts_v1_4)
