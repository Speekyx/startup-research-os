"""Mission 1.84.19. CI gate 93 over execution packet V7, and the refusals it must make.

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


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module(
        "gate_93_under_test", SCRIPTS / "render_second_opportunity_execution_packet_v7.py"
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
        assert packet["EXECUTION_PACKET_ID"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V7"
        assert packet["EXECUTION_PACKET_VERSION"] == 7
        assert packet["PREDECESSOR_EXECUTION_PACKET_SHA256"] == gate.V6_SHA256
        assert packet["OUTPUT_SCHEMA_VERSION"] == "second-opportunity-synthesis-output@1.2.0"
        assert packet["OUTPUT_GATE_VERSION"] == "second-opportunity-output-gate@1.4.0"
        assert packet["PROMPT_VERSION"] == "1.5.0"
        assert packet["PROVIDER_STRICT_MODE"] is True
        assert packet["STRUCTURED_OUTPUT_MECHANISM"] == "FORCED_STRICT_TOOL_USE"
        assert packet["FULL_CANONICAL_STAGE_5_VALIDATION"] == "REQUIRED_OUTPUT_SCHEMA_V1_2_0_LOCAL"
        assert packet["STRICT_PROJECTION_FREEZE_COMMIT"] == gate.FREEZE_COMMIT
        assert packet["THINKING"] == "DISABLED"
        assert (packet["MAX_OUTPUT_TOKENS"], packet["MAX_MODEL_CALLS"], packet["MAX_RETRIES"]) == (
            128000,
            1,
            0,
        )
        assert packet["REQUEST_TIMEOUT"] == 60.0
        assert packet["BETA_HEADERS"] == []
        assert packet["HUMAN_REVIEW_REQUIRED"] is True
        assert packet["RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V7"] is False
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False
        assert packet["NEW_APPROVAL_REQUIRED"] is True
        assert packet["PREVIOUS_APPROVAL_REUSABLE"] is False
        assert packet["EXECUTION_COST_CEILING"] == packet["WORST_CASE_CALL_COST"]

    def test_the_ceiling_was_recomputed_not_copied(self, gate, packet):
        v6 = json.loads(gate.PACKET_V6.read_text(encoding="utf-8"))
        assert packet["EXECUTION_COST_CEILING"] != v6["EXECUTION_COST_CEILING"]
        assert packet["TOKEN_ESTIMATION_BASIS"]["wire_characters"] != gate.V6_WIRE_CHARACTERS

    def test_no_approval_exists_beside_the_packet(self, gate):
        assert not gate.APPROVAL.exists()

    def test_the_request_differs_from_v6_in_exactly_two_places(self, packet):
        differential = packet["REQUEST_BODY_DIFFERENTIAL"]
        assert differential["differences"] == [
            "tools[0].input_schema: changed",
            "tools[0].strict: added",
        ]
        assert differential["unapproved_drift"] == []


class TestIdentityAndApproval:
    def test_a_bound_field_moved_without_its_digest_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("PROVIDER_STRICT_MODE", False), redigest=False
        )
        with pytest.raises(gate.ValidationError, match="hash"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V7", True),
            ("OPERATOR_EXECUTION_APPROVAL_RECORDED", True),
            ("PREVIOUS_APPROVAL_REUSABLE", True),
            ("HUMAN_REVIEW_REQUIRED", False),
        ],
    )
    def test_an_approval_or_risk_flag_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_identity_and_approval(mutated)

    def test_v6s_residual_risk_flag_is_not_a_v7_field(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p.__setitem__("RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6", True),
            redigest=False,
        )
        with pytest.raises(gate.ValidationError, match="nothing reviews"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize("word", ["strict", "process", "residual", "V6"])
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
        with pytest.raises(gate.ValidationError, match="spent"):
            gate._check_identity_and_approval(packet)

    def test_an_approval_recorded_by_this_mission_is_refused(
        self, gate, packet, tmp_path, monkeypatch
    ):
        approval = tmp_path / gate.APPROVAL.name
        approval.write_text(
            json.dumps(
                {
                    "recorded_by": "mission-1.84.19",
                    "EXECUTION_PACKET_SHA256": packet["EXECUTION_PACKET_SHA256"],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(gate, "APPROVAL", approval)
        with pytest.raises(gate.ValidationError, match="prepared it"):
            gate._check_identity_and_approval(packet)


class TestPredecessorsAndV6:
    def test_another_predecessor_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("PREDECESSOR_EXECUTION_PACKET_SHA256", "0" * 64)
        )
        with pytest.raises(gate.ValidationError, match="PREDECESSOR"):
            gate._check_predecessors(mutated)

    def test_a_consumed_list_without_v6_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p["CONSUMED_EXECUTION_PACKETS"].pop())
        with pytest.raises(gate.ValidationError, match="CONSUMED"):
            gate._check_predecessors(mutated)

    def test_v6s_violation_relabelled_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("PREDECESSOR_SCHEMA_VIOLATION", "LENGTH_BOUND")
        )
        with pytest.raises(gate.ValidationError, match="PREDECESSOR_SCHEMA_VIOLATION"):
            gate._check_predecessors(mutated)

    def test_a_reconfirmation_that_hides_the_undeclared_key_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p["V6_RECONFIRMATION"].__setitem__("undeclared_root_keys", [])
        )
        with pytest.raises(gate.ValidationError, match="V6_RECONFIRMATION"):
            gate._check_v6_reconfirmation(mutated)

    def test_a_rate_claimed_from_one_event_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["V6_RECONFIRMATION"].__setitem__("PROVIDER_UNKNOWN_PROPERTY_RATE", 1.0),
        )
        with pytest.raises(gate.ValidationError, match="V6_RECONFIRMATION"):
            gate._check_v6_reconfirmation(mutated)


class TestWhatDidNotMove:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("SCHEMA_CHANGED", True),
            ("SEMANTIC_GATE_CHANGED_BY_THIS_MISSION", True),
            ("REASONING_SUMMARY_HARD_MAX", 1501),
            ("OUTPUT_SCHEMA_SHA256", "0" * 64),
            ("GENERATION_TARGET_RATIO", "9/10"),
        ],
    )
    def test_a_moved_contract_field_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError):
            gate._check_contract_and_gate(mutated)

    def test_filtering_an_unknown_key_away_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p["OUTPUT_POST_PROCESSING"].__setitem__("DROPPING", True)
        )
        with pytest.raises(gate.ValidationError, match="OUTPUT_POST_PROCESSING"):
            gate._check_contract_and_gate(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [("PROMPT_TEXT_CHANGED", True), ("EXTRA_PROPERTY_WARNING_ADDED", True)],
    )
    def test_a_prompt_change_is_refused(self, gate, packet, snap, key, value):
        mutated = _changed(gate, packet, lambda p: p["PROMPT_DECISION"].__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_prompt(mutated, snap[1])

    @pytest.mark.parametrize(
        "key, value",
        [
            ("MODEL_ID", "claude-opus-5"),
            ("THINKING", "ADAPTIVE"),
            ("MAX_OUTPUT_TOKENS", 64000),
            ("BETA_HEADERS", ["structured-outputs"]),
        ],
    )
    def test_a_moved_route_field_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_route(mutated)

    def test_a_ceiling_basis_that_forgets_v6_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p["MAX_OUTPUT_TOKENS_NOT_BASED_ON"].pop())
        with pytest.raises(gate.ValidationError, match="V6's observed output"):
            gate._check_route(mutated)

    def test_a_compilation_latency_claimed_as_known_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["TIMEOUT"].__setitem__("FIRST_REQUEST_GRAMMAR_COMPILATION_LATENCY", "LOW"),
        )
        with pytest.raises(gate.ValidationError, match="COMPILATION_LATENCY"):
            gate._check_calls_and_timeout(mutated)

    def test_the_full_schema_named_as_the_tool_schema_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["GENERATION_PARAMETERS"].__setitem__(
                "response_schema", "second-opportunity-synthesis-output@1.2.0"
            ),
        )
        with pytest.raises(gate.ValidationError, match="generation parameters"):
            gate._check_calls_and_timeout(mutated)


class TestTheStrictMechanism:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("STRUCTURED_OUTPUT_MECHANISM", "FORCED_TOOL_USE"),
            ("PROVIDER_STRICT_SCHEMA_SHA256", "0" * 64),
            ("STRICT_CAPABILITY_PROFILE_SHA256", "0" * 64),
            ("STRICT_PROJECTOR_IMPLEMENTATION_SHA256", "0" * 64),
            ("STRICT_PROJECTION_FREEZE_COMMIT", "0" * 40),
            ("FULL_CANONICAL_STAGE_5_VALIDATION", "PROVIDER_STRICT_MODE"),
        ],
    )
    def test_a_strict_field_other_than_the_frozen_one_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_strict(mutated)

    def test_an_unverified_freeze_push_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["STRICT_PROJECTION_FREEZE_PUSH"].__setitem__(
                "STRICT_PROJECTION_FREEZE_PUSH_VERIFIED_BEFORE_V7", False
            ),
        )
        with pytest.raises(gate.ValidationError, match="STRICT_PROJECTION_FREEZE_PUSH"):
            gate._check_strict(mutated)

    def test_a_body_with_a_third_difference_is_refused(self, gate, packet, snap, monkeypatch):
        honest = gate.request_bodies

        def drifted(parts, p):
            v6, v7 = honest(parts, p)
            return v6, {**v7, "temperature": 0.0}

        monkeypatch.setattr(gate, "request_bodies", drifted)
        with pytest.raises(gate.ValidationError, match="UNAPPROVED_DRIFT"):
            gate._check_request(packet, snap[1])

    def test_a_strict_flag_inside_the_schema_is_refused(self, gate, packet, snap, monkeypatch):
        honest = gate.request_bodies

        def nested(parts, p):
            v6, v7 = honest(parts, p)
            v7 = copy.deepcopy(v7)
            v7["tools"][0]["input_schema"]["strict"] = True
            return v6, v7

        monkeypatch.setattr(gate, "request_bodies", nested)
        with pytest.raises(gate.ValidationError, match="INCOMPATIBLE_WITH_EXECUTION_ARCHITECTURE"):
            gate._check_request(packet, snap[1])

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

    def test_an_unforced_tool_is_refused(self, gate, packet, snap, monkeypatch):
        honest = gate.request_bodies

        def auto(parts, p):
            v6, v7 = honest(parts, p)
            return v6, {**v7, "tool_choice": {"type": "auto"}}

        monkeypatch.setattr(gate, "request_bodies", auto)
        with pytest.raises(gate.ValidationError, match="no longer forced"):
            gate._check_request(packet, snap[1])


class TestCostPreflightAndAccounting:
    def test_v6s_ceiling_copied_into_v7_is_refused(self, gate, packet, snap):
        v6 = json.loads(gate.PACKET_V6.read_text(encoding="utf-8"))
        mutated = _changed(
            gate,
            packet,
            lambda p: p.__setitem__("EXECUTION_COST_CEILING", v6["EXECUTION_COST_CEILING"]),
        )
        wire = len(json.dumps(gate.request_bodies(snap[1], mutated)[1]))
        with pytest.raises(gate.ValidationError, match="EXECUTION_COST_CEILING"):
            gate._check_cost(mutated, wire)

    def test_a_strict_format_prompt_claimed_as_counted_is_refused(self, gate, packet, snap):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["TOKEN_ESTIMATION_BASIS"].__setitem__("strict_format_prompt_tokens", 0),
        )
        wire = len(json.dumps(gate.request_bodies(snap[1], mutated)[1]))
        with pytest.raises(gate.ValidationError, match="strict_format_prompt_tokens"):
            gate._check_cost(mutated, wire)

    def test_a_preflight_row_edited_is_refused(self, gate, packet):
        def lie(p):
            p["V7_PREFLIGHT"][-1]["stopped_at"] = None

        mutated = _changed(gate, packet, lie)
        with pytest.raises(gate.ValidationError, match="V7_PREFLIGHT"):
            gate._check_preflight(mutated)

    def test_the_extra_key_case_is_in_the_preflight(self, packet):
        rows = {row["fixture"]: row for row in packet["V7_PREFLIGHT"]}
        extra = rows["J_EXTRA_ROOT_PROPERTY_REFUSED_AT_LOCAL_STAGE_5"]
        assert extra["stopped_at"] == "5_schema_validation_v1_2_0"

    def test_a_preparation_call_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p["preparation_accounting"].__setitem__("MODEL_CALLS", 1)
        )
        with pytest.raises(gate.ValidationError, match="MODEL_CALLS"):
            gate._check_accounting(mutated)

    def test_documentation_reads_other_than_gate_92s_are_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["preparation_accounting"].__setitem__("DOCUMENTATION_FETCHES", 0),
        )
        with pytest.raises(gate.ValidationError, match="documentation reads"):
            gate._check_accounting(mutated)

    def test_persisting_on_acceptance_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["PERSISTENCE_POLICY"].__setitem__("persist_if_gate_accepts", True),
        )
        with pytest.raises(gate.ValidationError, match="persist_if_gate_accepts"):
            gate._check_boundaries(mutated)


class TestTheRunner:
    def test_a_runner_prepared_for_another_digest_is_refused(self, gate, packet, snap):
        mutated = copy.deepcopy(packet)
        mutated["EXECUTION_PACKET_SHA256"] = "0" * 64
        with pytest.raises(gate.ValidationError, match="another digest"):
            gate._check_runner(mutated, snap[1], snap[2])

    def test_stage_5_is_read_from_the_syntax(self, gate):
        source = gate.RUNNER.read_text(encoding="utf-8")
        assert gate._stage_5_schema(source) == "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2"
        swapped = source.replace(
            "schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)",
            "schema_violations(dict(output), PROVIDER_STRICT_PROJECTION)",
        )
        assert gate._stage_5_schema(swapped) == "PROVIDER_STRICT_PROJECTION"
