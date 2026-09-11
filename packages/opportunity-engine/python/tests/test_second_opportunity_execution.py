"""Mission 1.84. The frozen artifacts against the code that renders them.

The sibling suite in `packages/inferred-claim-evaluator` reads the JSON documents and cannot
import this package. This one can, so it asks the question that one cannot: **do the frozen
records still describe what the code would actually send?** A record that agrees with itself and
disagrees with the executable prompt is a record of a call nobody would make.

It also drives the gate directly, including against mutated copies, so the refusals are observed
rather than described.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib

import pytest
from sros_opportunity import (
    ANTI_DISTORTION_RULES,
    CONFIDENCE_CLASSIFICATIONS,
    FORBIDDEN_TRANSFORMATIONS,
    PERSISTENCE_GATE_VERSION,
    SECOND_OPPORTUNITY_GATE_VERSION,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION,
    SECOND_OPPORTUNITY_PROCEDURE_VERSION,
    SECOND_OPPORTUNITY_PROMPT_ID,
    SECOND_OPPORTUNITY_PROMPT_VERSION,
    SECOND_OPPORTUNITY_SYSTEM,
    SYNTHESIS_SYSTEM,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
GATE_PATH = (
    REPO_ROOT / "infrastructure" / "scripts" / ("render_second_opportunity_execution_packet.py")
)

PROMPT = DATA / "second-opportunity-synthesis-prompt-v1.json"
CONTRACT = DATA / "second-opportunity-synthesis-output-contract-v1.json"
PACKET = DATA / "second-opportunity-synthesis-execution-packet-v1.json"


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _gate():
    spec = importlib.util.spec_from_file_location("second_opportunity_gate", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate():
    return _gate()


@pytest.fixture(scope="module")
def prompt() -> dict:
    return _load(PROMPT)


@pytest.fixture(scope="module")
def contract() -> dict:
    return _load(CONTRACT)


@pytest.fixture(scope="module")
def packet() -> dict:
    return _load(PACKET)


class TestTheRecordsMatchTheCode:
    """A frozen artifact is worth nothing if the executable has moved underneath it."""

    def test_the_system_instruction_is_the_one_the_code_renders(self, prompt: dict) -> None:
        assert prompt["SYSTEM_INSTRUCTION"] == SECOND_OPPORTUNITY_SYSTEM

    def test_the_system_instruction_inherits_the_frozen_base_byte_for_byte(self) -> None:
        """Mission 1.31's text is imported rather than copied, so it cannot drift."""
        assert SECOND_OPPORTUNITY_SYSTEM.startswith(SYNTHESIS_SYSTEM)

    def test_the_recorded_region_digests_hash_their_own_text(self, prompt: dict) -> None:
        for text_key, digest_key in (
            ("SYSTEM_INSTRUCTION", "SYSTEM_SHA256"),
            ("USER_INSTRUCTION", "TASK_SHA256"),
        ):
            expected = hashlib.sha256(prompt[text_key].encode("utf-8")).hexdigest()
            assert prompt[digest_key] == expected, text_key

    def test_the_schema_digest_is_the_live_schema(self, prompt: dict) -> None:
        expected = hashlib.sha256(
            json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA, sort_keys=True).encode("utf-8")
        ).hexdigest()
        assert prompt["OUTPUT_SCHEMA_SHA256"] == expected

    def test_the_versions_are_the_code_s(self, prompt: dict, contract: dict) -> None:
        assert prompt["PROMPT_ID"] == SECOND_OPPORTUNITY_PROMPT_ID
        assert prompt["PROMPT_VERSION"] == SECOND_OPPORTUNITY_PROMPT_VERSION
        assert prompt["PROCEDURE"] == SECOND_OPPORTUNITY_PROCEDURE_VERSION
        assert contract["OUTPUT_SCHEMA_VERSION"] == SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION
        assert contract["OUTPUT_GATE_VERSION"] == SECOND_OPPORTUNITY_GATE_VERSION
        assert contract["BASE_GATE_VERSION"] == PERSISTENCE_GATE_VERSION

    def test_the_required_fields_are_the_live_schema_s(self, contract: dict) -> None:
        assert list(contract["required_fields"]) == list(
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]
        )

    def test_the_anti_distortion_rules_are_the_code_s(self, prompt: dict) -> None:
        assert prompt["SEMANTIC_BOUNDARIES"]["anti_distortion_rules"] == ANTI_DISTORTION_RULES

    def test_the_forbidden_transformations_are_the_code_s(self, contract: dict) -> None:
        recorded = {entry["name"] for entry in contract["forbidden_transformations"]}
        assert recorded == {name for name, _, _ in FORBIDDEN_TRANSFORMATIONS}

    def test_the_confidence_enum_is_the_code_s(self, contract: dict) -> None:
        assert list(contract["confidence_classifications"]) == list(CONFIDENCE_CLASSIFICATIONS)

    def test_one_supplied_statement_per_evidence_row(self, prompt: dict, packet: dict) -> None:
        """Five Claims witness six rows, so a count that matched both would be wrong once."""
        supplied = prompt["INPUT_PLACEHOLDER"]["count"]
        assert supplied == packet["SUPPLIED_STATEMENT_COUNT"]
        assert supplied == packet["REPRESENTATION_EVIDENCE_COUNT"]
        assert supplied != packet["REPRESENTATION_CLAIM_COUNT"]
        assert len(prompt["INPUT_PLACEHOLDER"]["labels"]) == supplied


class TestTheGateAcceptsTheRealRecords:
    def test_validate_passes_as_committed(self, gate) -> None:
        prompt, contract, packet = gate.validate()
        assert packet["EXECUTION_PACKET_ID"] == "SECOND-OPPORTUNITY-SYNTH-EXEC-V1"
        assert contract["OUTPUT_GATE_VERSION"] == SECOND_OPPORTUNITY_GATE_VERSION
        assert prompt["PROMPT_ID"] == SECOND_OPPORTUNITY_PROMPT_ID

    def test_the_rendered_pages_match_their_records(self, gate) -> None:
        prompt, contract, packet = gate.validate()
        for path, text in (
            (gate.PROMPT_MD, gate.render_prompt(prompt)),
            (gate.CONTRACT_MD, gate.render_contract(contract)),
            (gate.PACKET_MD, gate.render_packet(packet)),
        ):
            assert path.read_text(encoding="utf-8") == text, path.name

    def test_the_digest_recomputes_from_the_bound_fields(self, gate, packet: dict) -> None:
        assert gate.packet_digest(packet) == packet["EXECUTION_PACKET_SHA256"]

    def test_the_approved_providers_are_derived_from_the_register(self, gate) -> None:
        register = json.loads(gate.PROVIDER_REGISTER.read_text(encoding="utf-8"))
        assert gate.approved_providers(register) == ["anthropic"]


class TestTheGateRefusesWhatItSaysItRefuses:
    """Observed refusals. A gate nobody attacked is a gate nobody has tested."""

    def _refuses(self, gate, packet: dict, fragment: str) -> None:
        with pytest.raises(gate.ValidationError) as error:
            gate._check_the_payload(
                packet,
                json.loads(gate.APPROVAL.read_text(encoding="utf-8")),
                json.loads(gate.DECISION_PACKET.read_text(encoding="utf-8")),
            )
        assert fragment in str(error.value)

    def test_a_moved_representation_is_the_named_hard_stop(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["REPRESENTATION_SHA256"] = "0" * 64
        self._refuses(gate, mutated, "APPROVED_TED_EGRESS_REPRESENTATION_CHANGED")

    def test_a_widened_purpose_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["PROCESSING_PURPOSE"] = "general market research"
        self._refuses(gate, mutated, "processing purpose")

    def test_another_subject_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["SUBJECT_KEY"] = "subject:docker"
        self._refuses(gate, mutated, "subject")

    def test_an_unapproved_provider_is_refused(self, gate, packet: dict) -> None:
        register = json.loads(gate.PROVIDER_REGISTER.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(packet)
        mutated["PROVIDER_ID"] = "gemini"
        with pytest.raises(gate.ValidationError, match="not APPROVED"):
            gate._check_the_route(mutated, register)

    def test_a_deterministic_claim_over_two_approved_routes_is_refused(
        self, gate, packet: dict
    ) -> None:
        register = json.loads(gate.PROVIDER_REGISTER.read_text(encoding="utf-8"))
        register = copy.deepcopy(register)
        for entry in register["providers"]:
            if entry["provider_id"] == "gemini":
                entry["posture"] = "APPROVED"
        with pytest.raises(gate.ValidationError, match="OPERATOR_DECISION"):
            gate._check_the_route(packet, register)

    def test_a_retry_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["GENERATION_PARAMETERS"]["max_retries"] = 2
        with pytest.raises(gate.ValidationError, match="max_retries"):
            gate._check_the_parameters(mutated)

    def test_an_invented_parameter_is_refused(self, gate, packet: dict) -> None:
        """Section 21. A frozen temperature would freeze a value nothing reads."""
        mutated = copy.deepcopy(packet)
        mutated["GENERATION_PARAMETERS"]["temperature"] = 0.0
        with pytest.raises(gate.ValidationError, match="the Gateway"):
            gate._check_the_parameters(mutated)

    def test_a_real_parameter_recorded_as_unsupported_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["GENERATION_PARAMETERS"]["tier"] = None
        with pytest.raises(gate.ValidationError, match="recorded as unsupported"):
            gate._check_the_parameters(mutated)

    def test_a_second_call_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["MAX_MODEL_CALLS"] = 2
        with pytest.raises(gate.ValidationError, match="MAX_MODEL_CALLS"):
            gate._check_the_parameters(mutated)

    def test_a_ceiling_below_the_worst_case_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["EXECUTION_COST_CEILING"] = 0.0001
        with pytest.raises(gate.ValidationError, match="below the worst case"):
            gate._check_the_budget(mutated)

    def test_a_missing_pricing_version_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["PRICING_VERSION"] = ""
        with pytest.raises(gate.ValidationError, match="MODEL_COST_BASIS_REQUIRES_REFRESH"):
            gate._check_the_budget(mutated)

    def test_a_test_request_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["TOKEN_ESTIMATION_BASIS"]["no_test_request_was_sent"] = False
        with pytest.raises(gate.ValidationError, match="test request"):
            gate._check_the_budget(mutated)

    def test_an_approval_written_into_the_packet_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["OPERATOR_EXECUTION_APPROVAL_RECORDED"] = True
        approval = json.loads(gate.APPROVAL.read_text(encoding="utf-8"))
        with pytest.raises(gate.ValidationError, match="records an approval of itself"):
            gate._check_the_boundaries(mutated, approval)

    def test_a_widened_capability_is_refused(self, gate, packet: dict) -> None:
        approval = json.loads(gate.APPROVAL.read_text(encoding="utf-8"))
        for key in ("TRAINING", "FINE_TUNING", "EMBEDDINGS", "WEB", "TOOLS", "EXTERNAL_RETRIEVAL"):
            mutated = copy.deepcopy(packet)
            mutated[key] = True
            with pytest.raises(gate.ValidationError, match=key):
                gate._check_the_boundaries(mutated, approval)

    def test_retained_reasoning_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["RETENTION_ON_EXECUTION"]["hidden_reasoning"] = "RETAINED for audit"
        approval = json.loads(gate.APPROVAL.read_text(encoding="utf-8"))
        with pytest.raises(gate.ValidationError, match="hidden reasoning"):
            gate._check_the_boundaries(mutated, approval)

    def test_persistence_on_a_gate_verdict_alone_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["PERSISTENCE_POLICY"]["persist_if_gate_accepts"] = True
        approval = json.loads(gate.APPROVAL.read_text(encoding="utf-8"))
        with pytest.raises(gate.ValidationError, match="gate verdict alone"):
            gate._check_the_boundaries(mutated, approval)

    def test_dropping_human_review_is_refused(self, gate, packet: dict) -> None:
        mutated = copy.deepcopy(packet)
        mutated["PERSISTENCE_POLICY"]["human_review_required_before_persistence"] = False
        approval = json.loads(gate.APPROVAL.read_text(encoding="utf-8"))
        with pytest.raises(gate.ValidationError, match="human review"):
            gate._check_the_boundaries(mutated, approval)

    def test_a_nonzero_preparation_counter_is_refused(self, gate, packet: dict) -> None:
        preparation = json.loads(gate.PREPARATION_V5.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(packet)
        mutated["preparation_accounting"]["MODEL_CALLS"] = 1
        with pytest.raises(gate.ValidationError, match="MODEL_CALLS"):
            gate._check_the_preparation(mutated, preparation)

    def test_a_transmitted_byte_is_refused(self, gate, packet: dict) -> None:
        preparation = json.loads(gate.PREPARATION_V5.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(packet)
        mutated["preparation_accounting"]["BYTES_SENT_TO_ANY_EXTERNAL_MODEL"] = 3604
        with pytest.raises(gate.ValidationError, match="BYTES_SENT"):
            gate._check_the_preparation(mutated, preparation)

    def test_a_moved_digest_is_refused_by_validate(self, gate, tmp_path) -> None:
        """Section 33. The bound fields decide the digest, not the recorded string."""
        original = PACKET.read_text(encoding="utf-8")
        mutated = json.loads(original)
        mutated["MODEL_ID"] = "some-other-model"
        try:
            PACKET.write_text(
                json.dumps(mutated, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            with pytest.raises(gate.ValidationError, match="hash to"):
                gate.validate()
        finally:
            PACKET.write_text(original, encoding="utf-8", newline="\n")
        assert PACKET.read_text(encoding="utf-8") == original


class TestPositiveControls:
    """A gate that refuses everything is not a gate."""

    def test_a_higher_ceiling_is_accepted(self, gate, packet: dict) -> None:
        widened = copy.deepcopy(packet)
        widened["EXECUTION_COST_CEILING"] = 0.5
        gate._check_the_budget(widened)

    def test_a_longer_timeout_is_accepted(self, gate, packet: dict) -> None:
        slower = copy.deepcopy(packet)
        slower["GENERATION_PARAMETERS"]["timeout_seconds"] = 120.0
        slower["REQUEST_TIMEOUT"] = 120.0
        gate._check_the_parameters(slower)

    def test_a_register_approving_a_different_single_provider_is_accepted(
        self, gate, packet: dict
    ) -> None:
        """The gate checks posture, not a vendor it happens to know."""
        register = copy.deepcopy(json.loads(gate.PROVIDER_REGISTER.read_text(encoding="utf-8")))
        for entry in register["providers"]:
            entry["posture"] = "APPROVED" if entry["provider_id"] == "gemini" else "NOT_APPROVED"
        moved = copy.deepcopy(packet)
        moved["PROVIDER_ID"] = "gemini"
        gate._check_the_route(moved, register)
