"""Mission 1.84.21. CI gate 97 over execution packet V9, and the refusals it must make.

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


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module(
        "gate_97_under_test", SCRIPTS / "render_second_opportunity_execution_packet_v9.py"
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
        assert packet["EXECUTION_PACKET_ID"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V9"
        assert packet["EXECUTION_PACKET_VERSION"] == 9
        assert packet["PREDECESSOR_EXECUTION_PACKET_SHA256"] == V8_SHA256
        assert packet["PREDECESSOR_STATUS"] == "SUPERSEDED_BEFORE_EXECUTION"
        assert packet["PREVIOUS_PREDECESSOR_SHA256"] == V7_SHA256
        assert packet["PREVIOUS_PREDECESSOR_STATUS"] == "SUPERSEDED_BEFORE_EXECUTION"
        assert packet["LAST_EXECUTED_PREDECESSOR_SHA256"] == gate.V6_SHA256
        assert packet["REQUEST_TIMEOUT"] == 240.0
        assert packet["TIMEOUT_DECISION_BASIS"] == "OPERATOR_AVAILABILITY_BUDGET"
        assert (packet["MAX_OUTPUT_TOKENS"], packet["MAX_MODEL_CALLS"], packet["MAX_RETRIES"]) == (
            128000,
            1,
            0,
        )
        assert packet["HARD_EXECUTION_COST_CEILING"] == "3.608"
        assert packet["PLANNING_COST_ESTIMATE"] == "1.316316"
        assert packet["RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9"] is False
        assert packet["STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9"] is False
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False
        assert packet["NEW_APPROVAL_REQUIRED"] is True
        assert packet["PREVIOUS_APPROVAL_REUSABLE"] is False

    def test_only_the_timeout_moved_from_v8(self, gate, packet):
        v8 = json.loads(gate.PACKET_V8.read_text(encoding="utf-8"))
        moved = sorted(
            key
            for key in gate.G95.DIGEST_FIELDS
            if key in packet and key in v8 and packet[key] != v8[key]
        )
        assert moved == sorted(
            [
                "EXECUTION_PACKET_ID",
                "EXECUTION_PACKET_VERSION",
                "PREDECESSOR_EXECUTION_PACKET_ID",
                "PREDECESSOR_EXECUTION_PACKET_SHA256",
                "SUPERSEDED_EXECUTION_PACKETS",
                "REQUEST_TIMEOUT",
                "GENERATION_PARAMETERS",
                "REQUEST_BODY_DIFFERENTIAL",
            ]
        )

    def test_the_approval_beside_the_packet_is_a_later_missions(self, gate, packet):
        """Re-pointed in Mission 1.84.22, when the operator approved exactly one execution of V9.

        This asserted that no approval existed beside the packet. One does now, and what it must be
        is what gate 97 already required of any: recorded by a mission later than the one that
        prepared V9, naming V9's digest, with the packet itself still recording no approval.
        """
        approval = json.loads(gate.APPROVAL.read_text(encoding="utf-8"))
        assert approval["recorded_by"] == "mission-1.84.22"
        assert approval["EXECUTION_PACKET_SHA256"] == packet["EXECUTION_PACKET_SHA256"]
        assert packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"] is False

    def test_the_request_is_v8s_bytes(self, packet):
        differential = packet["REQUEST_BODY_DIFFERENTIAL"]
        assert differential["byte_identical"] is True
        assert differential["REQUEST_BODY_DIFFERENCES_V8_TO_V9"] == 0
        assert differential["timeout_in_the_provider_body"] is False


class TestIdentityAndApproval:
    def test_a_bound_field_moved_without_its_digest_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p.__setitem__("REQUEST_TIMEOUT", 60.0), redigest=False
        )
        with pytest.raises(gate.ValidationError, match="hash"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9", True),
            ("STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9", True),
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
            "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8",
            "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8",
            "EXECUTION_COST_CEILING",
        ],
    )
    def test_a_predecessors_field_brought_back_is_refused(self, gate, packet, key):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, False), redigest=False)
        with pytest.raises(gate.ValidationError, match="nothing reviews"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize("word", ["V8", "V7", "superseded", "timeout", "residual", "egress"])
    def test_an_approval_note_that_forgets_a_distinction_is_refused(self, gate, packet, word):
        mutated = _changed(
            gate,
            packet,
            lambda p: p.__setitem__("approval_note", p["approval_note"].replace(word, "other")),
        )
        with pytest.raises(gate.ValidationError, match="approval note"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize("name", ["SHAS", "V8_SHA256", "V7_SHA256"])
    def test_a_spent_or_superseded_digest_is_refused(self, gate, packet, monkeypatch, name):
        digest = gate.packet_digest(packet)
        monkeypatch.setattr(gate, name, (*gate.SHAS, digest) if name == "SHAS" else digest)
        with pytest.raises(gate.ValidationError, match="spent or superseded"):
            gate._check_identity_and_approval(packet)

    def test_an_intention_recorded_as_an_approval_is_refused(self, gate, packet):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["OPERATOR_STATED_INTENTIONS"].__setitem__("IS_AN_APPROVAL", True),
        )
        with pytest.raises(gate.ValidationError, match="IS_AN_APPROVAL"):
            gate._check_identity_and_approval(mutated)

    @pytest.mark.parametrize(
        "recorded_by, digest, match",
        [
            ("mission-1.84.21", None, "prepared it"),
            ("mission-1.84.20", None, "prepared it"),
            ("mission-9.9.9", V8_SHA256, "other than V9's"),
        ],
    )
    def test_an_approval_that_cannot_stand_beside_v9_is_refused(
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
            ("PREDECESSOR_EXECUTION_PACKET_SHA256", V7_SHA256),
            ("PREDECESSOR_STATUS", "CONSUMED"),
            ("PREDECESSOR_STATUS", "FAILED"),
            ("PREDECESSOR_EXECUTED", True),
            ("PREDECESSOR_APPROVED", True),
            ("PREDECESSOR_APPROVAL_CONSUMED", True),
            ("PREVIOUS_PREDECESSOR_SHA256", "0" * 64),
            ("PREVIOUS_PREDECESSOR_STATUS", "RESTORED"),
            ("V8_SUPERSESSION_RECORD_SHA256", "0" * 64),
            ("TIMEOUT_DECISION_RECORD_SHA256", "0" * 64),
            ("V7_SUPERSESSION_RECORD_SHA256", "0" * 64),
        ],
    )
    def test_a_predecessor_field_moved_is_refused(self, gate, packet, key, value):
        mutated = _changed(gate, packet, lambda p: p.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_predecessors(mutated)

    def test_v8_missing_from_the_superseded_list_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p["SUPERSEDED_EXECUTION_PACKETS"].pop())
        with pytest.raises(gate.ValidationError, match="SUPERSEDED_EXECUTION_PACKETS"):
            gate._check_predecessors(mutated)

    def test_v8_listed_as_consumed_is_refused(self, gate, packet):
        def consume(p):
            p["CONSUMED_EXECUTION_PACKETS"].append(
                {"id": gate.V8_ID, "sha256": V8_SHA256, "outcome": "CONSUMED"}
            )

        mutated = _changed(gate, packet, consume)
        with pytest.raises(gate.ValidationError, match="CONSUMED_EXECUTION_PACKETS"):
            gate._check_predecessors(mutated)

    def test_a_v8_reconfirmation_edited_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p["V8_RECONFIRMATION"].__setitem__("approval_recorded", True)
        )
        with pytest.raises(gate.ValidationError, match="V8_RECONFIRMATION"):
            gate._check_reconfirmations(mutated)


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

    def test_a_timeout_left_at_60_in_the_request_parameters_is_refused(self, gate, packet):
        mutated = _changed(
            gate, packet, lambda p: p["GENERATION_PARAMETERS"].__setitem__("timeout_seconds", 60.0)
        )
        with pytest.raises(gate.ValidationError, match="generation parameters"):
            gate._check_calls_and_timeout(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("PROVIDER_GUARANTEED", True),
            ("STATISTICALLY_ESTIMATED", True),
            ("MATHEMATICALLY_DERIVED", True),
            ("END_TO_END_LATENCY_BOUND", "240 SECONDS"),
            ("TIMEOUT_RISK_ELIMINATED", True),
            ("TIMEOUT_CHANGES_BILLING", True),
            ("RETRY_ADDED_TO_OFFSET_THE_RISK", True),
            ("STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9", True),
            ("REQUEST_TIMEOUT_SECONDS", 60.0),
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

    def test_another_basis_is_refused(self, gate, packet):
        mutated = _changed(gate, packet, lambda p: p.__setitem__("TIMEOUT_DECISION_BASIS", "P99"))
        with pytest.raises(gate.ValidationError, match="TIMEOUT_DECISION_BASIS"):
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
    def test_a_body_that_is_not_v8s_bytes_is_refused(self, gate, packet, snap, monkeypatch, change):
        honest = gate.request_bodies

        def drifted(parts, p):
            v8, v9 = honest(parts, p)
            v9 = copy.deepcopy(v9)
            change(v9)
            return v8, v9

        monkeypatch.setattr(gate, "request_bodies", drifted)
        with pytest.raises(gate.ValidationError, match="V9_REQUEST_BODY_HAS_UNAPPROVED_DRIFT"):
            gate._check_request(packet, snap[1])

    def test_a_forged_differential_is_refused(self, gate, packet, snap):
        mutated = _changed(
            gate,
            packet,
            lambda p: p["REQUEST_BODY_DIFFERENTIAL"].__setitem__("v9_body_characters", 1),
        )
        with pytest.raises(gate.ValidationError, match="REQUEST_BODY_DIFFERENTIAL"):
            gate._check_request(mutated, snap[1])

    @pytest.mark.parametrize(
        "key, value",
        [
            ("HARD_EXECUTION_COST_CEILING", "3.9"),
            ("PLANNING_COST_ESTIMATE", "1.4"),
            ("MAX_BILLABLE_INPUT_TOKENS", 18158),
            ("HARD_EXECUTION_COST_CEILING_PROVEN", False),
        ],
    )
    def test_a_cost_figure_that_moved_is_refused(self, gate, packet, key, value):
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
            ("v8_refused_as_superseded", False),
            ("request_timeout_seconds", 60.0),
            ("request_body_sha256", "0" * 64),
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
            p["V9_PREFLIGHT"][-1]["stopped_at"] = None

        mutated = _changed(gate, packet, lie)
        with pytest.raises(gate.ValidationError, match="V9_PREFLIGHT"):
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

    def test_a_runner_still_waiting_60_seconds_is_refused(self, gate, packet, snap, monkeypatch):
        self._with(gate, monkeypatch, lambda m: m.EXPECTED.__setitem__("REQUEST_TIMEOUT", 60.0))
        with pytest.raises(gate.ValidationError, match="REQUEST_TIMEOUT"):
            gate._check_runner(packet, snap[1], snap[2])

    def test_a_runner_whose_request_waits_otherwise_is_refused(
        self, gate, packet, snap, monkeypatch
    ):
        def shorten(module):
            honest = module.build_request

            def build_request(parts, p):
                return honest(parts, {**p, "REQUEST_TIMEOUT": 60.0})

            module.build_request = build_request

        self._with(gate, monkeypatch, shorten)
        with pytest.raises(gate.ValidationError, match="would wait 60.0"):
            gate._check_runner(packet, snap[1], snap[2])

    def test_v8s_risk_decisions_in_the_runner_are_refused(self, gate, packet, snap, monkeypatch):
        self._with(
            gate,
            monkeypatch,
            lambda m: setattr(
                m,
                "RISK_DECISIONS",
                {
                    "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8": "RESIDUAL_SEMANTIC_LIMITATION_NOT_ACCEPTED",
                    "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8": "STRICT_FIRST_REQUEST_TIMEOUT_RISK_NOT_ACCEPTED",
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

    def test_a_guard_that_lets_v8_through_is_refused(self, gate, packet, snap, monkeypatch):
        def let_through(module):
            honest = module.refuse_if_consumed

            def lenient(sha):
                if sha != V8_SHA256:
                    honest(sha)

            module.refuse_if_consumed = lenient

        self._with(gate, monkeypatch, let_through)
        with pytest.raises(gate.ValidationError, match="V8_STILL_EXECUTABLE"):
            gate._check_runner(packet, snap[1], snap[2])

    def test_the_shipped_approval_check_decides_both_risks(self, gate, packet):
        before = gate.APPROVAL.read_bytes()
        gate._check_approval_behaviour(gate.runner(), packet)
        # Re-pointed in Mission 1.84.22: the check writes its synthetic approvals to a temporary copy,
        # and the operator's approval beside the packet is left byte for byte as it was.
        assert gate.APPROVAL.read_bytes() == before

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
