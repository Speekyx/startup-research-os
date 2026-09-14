"""Mission 1.84.23. CI gate 100 over execution packet V10, and the refusals it must make.

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
V8_SHA256 = "583946460c6cf68c1be5519916f92d268e36ed65924aeb24901731439586c399"
V9_SHA256 = "ba681da94b3e89f22c7e39bdb2dc4ef95d0527ca3db561c849eb089652d9425d"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module(
        "gate_100_under_test", SCRIPTS / "render_second_opportunity_execution_packet_v10.py"
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
        assert gate.validate()["PRIMARY_OUTCOME"] == gate.READY

    def test_the_page_is_the_rendering(self, gate, packet):
        assert gate.PACKET_MD.read_text(encoding="utf-8") == gate.render_packet(packet)

    def test_the_approval_surface(self, gate, packet):
        assert packet["EXECUTION_PACKET_ID"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V10"
        assert packet["EXECUTION_PACKET_VERSION"] == 10
        assert packet["PREDECESSOR_EXECUTION_PACKET_SHA256"] == V9_SHA256
        assert packet["PREDECESSOR_STATUS"] == "CONSUMED"
        assert packet["PREDECESSOR_OUTCOME"] == "EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY"
        assert packet["PREDECESSOR_APPROVAL_CONSUMED"] is True
        assert packet["PREVIOUS_PREDECESSOR_SHA256"] == V8_SHA256
        assert packet["PREVIOUS_PREDECESSOR_STATUS"] == "SUPERSEDED_BEFORE_EXECUTION"
        assert packet["LAST_EXECUTED_PREDECESSOR_SHA256"] == V9_SHA256
        assert packet["PROMPT_VERSION"] == "1.6.0"
        assert packet["PROMPT_SHA256"] == gate.PROMPT_V1_6_SHA256
        assert packet["PROMPT_V1_6_FREEZE_COMMIT"] == gate.FREEZE_COMMIT
        assert (
            packet["PROMPT_V1_6_FREEZE_PUSH"]["PROMPT_V1_6_FREEZE_PUSH_VERIFIED_BEFORE_V10"] is True
        )
        assert packet["REQUEST_TIMEOUT"] == 240.0
        assert (packet["MAX_OUTPUT_TOKENS"], packet["MAX_MODEL_CALLS"], packet["MAX_RETRIES"]) == (
            128000,
            1,
            0,
        )
        assert packet["HARD_EXECUTION_COST_CEILING"] == "3.608"
        assert packet["PLANNING_COST_ESTIMATE"] == "1.31972"
        assert packet["RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V10"] is False
        assert packet["STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10"] is False
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False
        assert packet["NEW_APPROVAL_REQUIRED"] is True
        assert packet["PREVIOUS_APPROVAL_REUSABLE"] is False

    def test_only_the_prompt_and_what_follows_from_it_moved_from_v9(self, gate, packet):
        v9 = json.loads(gate.PACKET_V9.read_text(encoding="utf-8"))
        moved = sorted(
            key
            for key in gate.G97.DIGEST_FIELDS
            if key in packet and key in v9 and packet[key] != v9[key]
        )
        assert moved == sorted(
            [
                "EXECUTION_PACKET_ID",
                "EXECUTION_PACKET_VERSION",
                "PREDECESSOR_EXECUTION_PACKET_ID",
                "PREDECESSOR_EXECUTION_PACKET_SHA256",
                "PREDECESSOR_APPROVAL_CONSUMED",
                "PREDECESSOR_STATUS",
                "PREDECESSOR_EXECUTED",
                "PREDECESSOR_APPROVED",
                "PREVIOUS_PREDECESSOR_ID",
                "PREVIOUS_PREDECESSOR_SHA256",
                "LAST_EXECUTED_PREDECESSOR_ID",
                "LAST_EXECUTED_PREDECESSOR_SHA256",
                "LAST_EXECUTED_PREDECESSOR_OUTCOME",
                "CONSUMED_EXECUTION_PACKETS",
                "PROMPT_VERSION",
                "PROMPT_SHA256",
                "PROMPT_CHANGED",
                "PROMPT_RECORD_SHA256",
                "PERSISTENCE_POLICY",
                "REQUEST_BODY_DIFFERENTIAL",
                "REQUEST_BODY_SHA256",
                "REQUEST_BODY_CHARACTERS",
                "PLANNING_INPUT_TOKEN_ESTIMATE",
                "PLANNING_INPUT_COST_ESTIMATE",
                "PLANNING_COST_ESTIMATE",
            ]
        )

    def test_no_approval_is_recorded_beside_v10(self, gate, packet):
        """True while V10 awaits the operator. A later mission that records an approval re-points
        this to what the approval must then be, as Mission 1.84.22 did for V9."""
        assert not gate.APPROVAL.exists()
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False

    def test_the_request_is_v9s_bytes_with_the_v1_6_system_region(self, packet):
        differential = packet["REQUEST_BODY_DIFFERENTIAL"]
        assert differential["byte_identical"] is False
        assert differential["differences"] == ["system: changed"]
        assert differential["v10_body_is_v9_body_with_the_v1_6_system_region"] is True
        assert differential["unapproved_drift"] == []
        assert differential["timeout_in_the_provider_body"] is False


class TestIdentityAndApproval:
    def test_a_bound_field_moved_without_its_digest_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("PROMPT_VERSION", "1.5.0"), redigest=False
        )
        with pytest.raises(gate.ValidationError, match="hash"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V10", True),
            ("STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10", True),
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
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9",
            "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9",
            "OPERATOR_STATED_INTENTIONS",
            "V8_RECONFIRMATION",
            "EXECUTION_COST_CEILING",
        ],
    )
    def test_a_predecessors_field_brought_back_is_refused(self, gate, packet, key):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, False), redigest=False)
        with pytest.raises(gate.ValidationError, match="nothing reviews"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize(
        "word", ["V9", "V8", "V7", "superseded", "spent", "timeout", "residual", "egress"]
    )
    def test_an_approval_note_that_forgets_a_distinction_is_refused(self, gate, packet, word):
        mutated = _changed(
            gate,
            packet,
            lambda p: p.__setitem__("approval_note", p["approval_note"].replace(word, "other")),
        )
        with pytest.raises(gate.ValidationError, match="approval note"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize("name", ["SHAS", "V8_SHA256", "V7_SHA256", "V9_SHA256"])
    def test_a_spent_or_superseded_digest_is_refused(self, gate, packet, monkeypatch, name):
        digest = gate.packet_digest(packet)
        monkeypatch.setattr(gate, name, (*gate.SHAS, digest) if name == "SHAS" else digest)
        with pytest.raises(gate.ValidationError, match="spent or superseded"):
            gate._check_identity_and_approval(packet)

    @pytest.mark.parametrize(
        "recorded_by, digest, match",
        [
            ("mission-1.84.23", None, "prepared it"),
            ("mission-1.84.22", None, "prepared it"),
            ("mission-9.9.9", V9_SHA256, "other than V10's"),
        ],
    )
    def test_an_approval_that_cannot_stand_beside_v10_is_refused(
        self, gate, packet, tmp_path, monkeypatch, recorded_by, digest, match
    ):
        approval = tmp_path / gate.APPROVAL.name
        approval.write_text(
            json.dumps(
                {
                    "recorded_by": recorded_by,
                    "EXECUTION_PACKET_SHA256": digest or packet["EXECUTION_PACKET_SHA256"],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(gate, "APPROVAL", approval)
        with pytest.raises(gate.ValidationError, match=match):
            gate._check_identity_and_approval(packet)


class TestPredecessors:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("PREDECESSOR_EXECUTION_PACKET_SHA256", V8_SHA256),
            ("PREDECESSOR_STATUS", "SUPERSEDED_BEFORE_EXECUTION"),
            ("PREDECESSOR_STATUS", "FAILED"),
            ("PREDECESSOR_EXECUTED", False),
            ("PREDECESSOR_APPROVAL_CONSUMED", False),
            ("PREDECESSOR_OUTCOME", "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW"),
            ("PREVIOUS_PREDECESSOR_SHA256", "0" * 64),
            ("PREVIOUS_PREDECESSOR_STATUS", "RESTORED"),
            ("LAST_EXECUTED_PREDECESSOR_FAILED_STAGE", "5_schema_validation_v1_2_0"),
            ("V9_EXECUTION_RECORD_SHA256", "0" * 64),
            ("V8_SUPERSESSION_RECORD_SHA256", "0" * 64),
            ("TIMEOUT_DECISION_RECORD_SHA256", "0" * 64),
            ("V7_SUPERSESSION_RECORD_SHA256", "0" * 64),
        ],
    )
    def test_a_predecessor_field_moved_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_predecessors(mutated)

    def test_v9_missing_from_the_consumed_list_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p["CONSUMED_EXECUTION_PACKETS"].pop())
        with pytest.raises(gate.ValidationError, match="CONSUMED_EXECUTION_PACKETS"):
            gate._check_predecessors(mutated)

    def test_v9_listed_as_superseded_is_refused(self, gate, packet):
        def supersede(p):
            p["SUPERSEDED_EXECUTION_PACKETS"].append(
                {"id": gate.V9_ID, "sha256": V9_SHA256, "status": "SUPERSEDED_BEFORE_EXECUTION"}
            )

        mutated = _changed(gate, packet, supersede)
        with pytest.raises(gate.ValidationError, match="SUPERSEDED_EXECUTION_PACKETS"):
            gate._check_predecessors(mutated)

    def test_a_v9_reconfirmation_edited_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["V9_RECONFIRMATION"].__setitem__("V9_WOULD_HAVE_PASSED_CLAIMED", True),
        )
        with pytest.raises(gate.ValidationError, match="V9_RECONFIRMATION"):
            gate._check_v9_reconfirmation(mutated)

    def test_the_families_recounted_are_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["V9_REFUSAL_FAMILIES"].__setitem__(
                "GENERATION_SURFACE_FORM_MISALIGNMENT", 7
            ),
        )
        with pytest.raises(gate.ValidationError, match="V9_REFUSAL_FAMILIES"):
            gate._check_v9_reconfirmation(mutated)


class TestThePromptAndItsFreeze:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("PROMPT_VERSION", "1.5.0"),
            ("PROMPT_SHA256", "0713eb8053e83627e1156324cc9003031fff1f8e81289efe5cc89f182f542abb"),
            ("PROMPT_CHANGED", False),
            ("PROMPT_RECORD_SHA256", "0" * 64),
            ("GENERATION_SURFACE_POLICY", "second-opportunity-generation-surface-policy@0.9.0"),
            ("GENERATION_SURFACE_BLOCK_SHA256", "0" * 64),
            ("PROMPT_V1_6_FREEZE_COMMIT", "0" * 40),
        ],
    )
    def test_a_prompt_field_moved_is_refused(self, gate, packet, snap, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_prompt(mutated, snap[2])

    def test_a_freeze_push_recorded_after_v10_is_refused(self, gate, packet, snap):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["PROMPT_V1_6_FREEZE_PUSH"].__setitem__(
                "PROMPT_V1_6_FREEZE_PUSH_VERIFIED_BEFORE_V10", False
            ),
        )
        with pytest.raises(gate.ValidationError, match="PROMPT_V1_6_FREEZE_PUSH"):
            gate._check_prompt(mutated, snap[2])

    @pytest.mark.parametrize(
        "key",
        [
            "SUPPORTED_ASSERTION_POLICY_WEAKENED",
            "REQUEST_PARSER_EXPANDED",
            "SEMANTIC_GATE_RULES_CHANGED",
        ],
    )
    def test_a_prompt_decision_that_weakens_the_gate_is_refused(self, gate, packet, snap, key):
        mutated = _changed(gate, packet, lambda p: p["PROMPT_DECISION"].__setitem__(key, True))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_prompt(mutated, snap[2])

    def test_the_v1_5_regions_are_not_v10s_prompt(self, gate, packet, snap):
        with pytest.raises(gate.ValidationError, match="not the frozen v1.6.0"):
            gate._check_prompt(packet, snap[1])


class TestTheTimeout:
    @pytest.mark.parametrize("value", [60.0, 180.0, 300.0, 240])
    def test_a_timeout_other_than_the_operators_is_refused(self, gate, packet, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__("REQUEST_TIMEOUT", value))
        if value == 240:
            gate._check_calls_and_timeout(mutated)
            return
        with pytest.raises(
            gate.ValidationError, match="TIMEOUT_POLICY_REQUIRES_ARCHITECTURE_DECISION"
        ):
            gate._check_calls_and_timeout(mutated)

    def test_a_timeout_moved_in_the_request_parameters_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p["GENERATION_PARAMETERS"].__setitem__("timeout_seconds", 60.0)
        )
        with pytest.raises(gate.ValidationError, match="generation parameters"):
            gate._check_calls_and_timeout(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("PROVIDER_GUARANTEED", True),
            ("END_TO_END_LATENCY_BOUND", "240 SECONDS"),
            ("TIMEOUT_RISK_ELIMINATED", True),
            ("TIMEOUT_CHANGED_BY_THIS_MISSION", True),
            ("RETRY_ADDED_TO_OFFSET_THE_RISK", True),
            ("STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V10", True),
        ],
    )
    def test_the_timeout_block_misstated_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p["TIMEOUT"].__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_calls_and_timeout(mutated)

    def test_a_retry_to_offset_the_risk_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p.__setitem__("MAX_RETRIES", 1))
        with pytest.raises(gate.ValidationError, match="retry"):
            gate._check_calls_and_timeout(mutated)


class TestTheRequestAndCost:
    @pytest.mark.parametrize(
        "change",
        [
            lambda b: b.__setitem__("timeout", 240),
            lambda b: b["tools"][0].__setitem__("strict", False),
            lambda b: b.__setitem__("cache_control", {"type": "ephemeral"}),
            lambda b: b.__setitem__("max_tokens", 64000),
        ],
        ids=["timeout_in_body", "strict_off", "cache", "max_tokens"],
    )
    def test_a_body_that_moved_outside_the_system_region_is_refused(
        self, gate, packet, snap, monkeypatch, change
    ):
        honest = gate.request_bodies

        def drifted(parts_v1_5, parts_v1_6, p):
            v9, v10 = honest(parts_v1_5, parts_v1_6, p)
            v10 = copy.deepcopy(v10)
            change(v10)
            return v9, v10

        monkeypatch.setattr(gate, "request_bodies", drifted)
        with pytest.raises(gate.ValidationError, match="V10_REQUEST_BODY_HAS_UNAPPROVED_DRIFT"):
            gate._check_request(packet, snap[1], snap[2])

    def test_a_system_region_other_than_v1_6_is_refused(self, gate, packet, snap, monkeypatch):
        honest = gate.request_bodies

        def drifted(parts_v1_5, parts_v1_6, p):
            v9, v10 = honest(parts_v1_5, parts_v1_6, p)
            v10 = json.loads(json.dumps(v10).replace("GENERATION SURFACE", "GENERATION SURFACES"))
            return v9, v10

        monkeypatch.setattr(gate, "request_bodies", drifted)
        with pytest.raises(gate.ValidationError, match="V10_REQUEST_BODY_HAS_UNAPPROVED_DRIFT"):
            gate._check_request(packet, snap[1], snap[2])

    def test_a_forged_differential_is_refused(self, gate, packet, snap):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["REQUEST_BODY_DIFFERENTIAL"].__setitem__("v10_body_characters", 1),
        )
        with pytest.raises(gate.ValidationError, match="REQUEST_BODY_DIFFERENTIAL"):
            gate._check_request(mutated, snap[1], snap[2])

    @pytest.mark.parametrize(
        "key, value",
        [
            ("HARD_EXECUTION_COST_CEILING", "3.9"),
            ("PLANNING_COST_ESTIMATE", "1.316316"),
            ("PLANNING_INPUT_TOKEN_ESTIMATE", 18158),
            ("MAX_BILLABLE_INPUT_TOKENS", 18158),
            ("HARD_EXECUTION_COST_CEILING_PROVEN", False),
        ],
    )
    def test_a_cost_figure_that_moved_or_was_carried_from_v9_is_refused(
        self, gate, packet, key, value
    ):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_cost(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("PROVIDER_STRICT_MODE", False),
            ("PROVIDER_STRICT_SCHEMA_SHA256", "0" * 64),
            ("STRICT_PROJECTION_FREEZE_COMMIT", "0" * 40),
        ],
    )
    def test_the_strict_mechanism_moved_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._through(gate.G93._check_strict, mutated)

    @pytest.mark.parametrize(
        "key, value",
        [("OUTPUT_SCHEMA_SHA256", "0" * 64), ("SEMANTIC_GATE_IMPLEMENTATION_SHA256", "0" * 64)],
    )
    def test_the_contract_or_gate_moved_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._through(gate.G93._check_contract_and_gate, mutated)

    def test_the_representation_moved_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p.__setitem__("REPRESENTATION_SHA256", "0" * 64))
        with pytest.raises(gate.ValidationError, match="REPRESENTATION_SHA256"):
            gate._through(gate.G93._check_route, mutated)


class TestVerificationPreflightAndAccounting:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("v9_refused_as_consumed", False),
            ("request_timeout_seconds", 60.0),
            ("request_body_sha256", "0" * 64),
            ("unstated_generation_surface_rules", 1),
            ("prompt_sha256", "0713eb8053e83627e1156324cc9003031fff1f8e81289efe5cc89f182f542abb"),
        ],
    )
    def test_verification_that_found_something_else_is_refused(self, gate, packet, key, value):
        mutated = _changed(
            gate, packet, lambda p: p["PREPARATION_VERIFICATION"].__setitem__(key, value)
        )
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_verification(mutated)

    def test_a_preflight_row_edited_is_refused(self, gate, packet):
        def lie(p):
            p["V10_PREFLIGHT"][-1]["stopped_at"] = None

        mutated = _changed(gate, packet, lie)
        with pytest.raises(gate.ValidationError, match="V10_PREFLIGHT"):
            gate._check_preflight(mutated)

    @pytest.mark.parametrize(
        "key",
        ["MODEL_CALLS", "MESSAGES_API_REQUESTS", "TOKEN_COUNT_API_REQUESTS", "TED_BYTES_SENT"],
    )
    def test_a_preparation_call_is_refused(self, gate, packet, key):
        mutated = _changed(gate, packet, lambda p: p["preparation_accounting"].__setitem__(key, 1))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_accounting(mutated)

    def test_documentation_reads_are_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["preparation_accounting"].__setitem__("DOCUMENTATION_FETCHES", 12),
        )
        with pytest.raises(gate.ValidationError, match="documentation reads"):
            gate._check_accounting(mutated)

    @pytest.mark.parametrize("key", ["PERSISTENCE_POLICY", "PROVIDER_COMPLETION_POLICY"])
    def test_a_moved_policy_is_refused(self, gate, packet, key):
        mutated = _changed(gate, packet, lambda p: p[key].__setitem__("probe", True))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_boundaries(mutated)


class TestTheRunner:
    def _with(self, gate, monkeypatch, change):
        honest = gate.runner

        def altered():
            module = honest()
            change(module)
            return module

        monkeypatch.setattr(gate, "runner", altered)

    def test_a_runner_prepared_for_another_digest_is_refused(self, gate, packet, snap):
        mutated = copy.deepcopy(packet)
        mutated["EXECUTION_PACKET_SHA256"] = "0" * 64
        with pytest.raises(gate.ValidationError, match="another digest"):
            gate._check_runner(mutated, snap[1], snap[2])

    def test_a_runner_waiting_60_seconds_is_refused(self, gate, packet, snap, monkeypatch):
        self._with(gate, monkeypatch, lambda m: m.EXPECTED.__setitem__("REQUEST_TIMEOUT", 60.0))
        with pytest.raises(gate.ValidationError, match="REQUEST_TIMEOUT"):
            gate._check_runner(packet, snap[1], snap[2])

    def test_v9s_risk_decisions_in_the_runner_are_refused(self, gate, packet, snap, monkeypatch):
        self._with(
            gate,
            monkeypatch,
            lambda m: setattr(
                m,
                "RISK_DECISIONS",
                {
                    "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9": "RESIDUAL_SEMANTIC_LIMITATION_NOT_ACCEPTED",
                    "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9": "STRICT_FIRST_REQUEST_TIMEOUT_RISK_NOT_ACCEPTED",
                },
            ),
        )
        with pytest.raises(gate.ValidationError, match="risk decisions"):
            gate._check_runner(packet, snap[1], snap[2])

    @pytest.mark.parametrize("digest", [V7_SHA256, V8_SHA256], ids=["V7", "V8"])
    def test_a_guard_that_calls_a_superseded_digest_consumed_is_refused(
        self, gate, packet, snap, monkeypatch, digest
    ):
        def rename(module):
            honest = module.refuse_if_consumed

            def renamed(sha):
                if sha == digest:
                    raise module.RefusedError("EXECUTION_APPROVAL_ALREADY_CONSUMED", "renamed")
                honest(sha)

            module.refuse_if_consumed = renamed

        self._with(gate, monkeypatch, rename)
        with pytest.raises(gate.ValidationError, match="not as superseded"):
            gate._check_runner(packet, snap[1], snap[2])

    @pytest.mark.parametrize(
        "digest, match",
        [(V8_SHA256, "V8_STILL_EXECUTABLE"), (V9_SHA256, "would execute V9's spent digest")],
        ids=["V8", "V9"],
    )
    def test_a_guard_that_lets_a_predecessor_through_is_refused(
        self, gate, packet, snap, monkeypatch, digest, match
    ):
        def let_through(module):
            honest = module.refuse_if_consumed

            def lenient(sha):
                if sha != digest:
                    honest(sha)

            module.refuse_if_consumed = lenient

        self._with(gate, monkeypatch, let_through)
        with pytest.raises(gate.ValidationError, match=match):
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
        with pytest.raises(gate.ValidationError, match="does not decide and accept both"):
            gate._check_approval_behaviour(module, packet)

    def test_a_runner_whose_request_would_retry_is_refused(self, gate, packet, snap, monkeypatch):
        def retrying(module):
            honest = module.build_request

            def build_request(parts, p):
                return honest(parts, {**p, "GENERATION_PARAMETERS": {"max_retries": 1}})

            module.build_request = build_request

        self._with(gate, monkeypatch, retrying)
        with pytest.raises(gate.ValidationError, match="would retry 1"):
            gate._check_runner(packet, snap[1], snap[2])

    def test_a_runner_whose_surface_check_is_hollow_is_refused(
        self, gate, packet, snap, monkeypatch
    ):
        self._with(gate, monkeypatch, lambda m: setattr(m, "unstated_surface", lambda parts: []))
        with pytest.raises(gate.ValidationError, match="would pass prompt v1.5.0"):
            gate._check_runner(packet, snap[1], snap[2])

    @pytest.mark.parametrize("name", ["packet_digest", "freeze_gate"])
    def test_a_packet_authority_the_runner_cannot_use_is_refused(
        self, gate, packet, snap, monkeypatch, name
    ):
        def hollow(module):
            authority = module.packet_gate()
            delattr(authority, name)
            module.packet_gate = lambda: authority

        self._with(gate, monkeypatch, hollow)
        with pytest.raises(gate.ValidationError, match=f"no {name}"):
            gate._check_runner(packet, snap[1], snap[2])
