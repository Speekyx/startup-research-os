"""Mission 1.84.21. CI gate 96: the operator's client-timeout decision and V8's supersession, and the
refusals they must make.

The records are built once. Every refusal feeds one of the gate's checks a deep copy with one field
changed, so nothing committed is touched and each refusal is attributed to the rule that makes it.
The V8 runner's guard is exercised with its transport tripwired. Nothing here reaches a network.
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
SUPERSEDED = "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
CONSUMED = "EXECUTION_APPROVAL_ALREADY_CONSUMED"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module(
        "gate_96_under_test", SCRIPTS / "render_second_opportunity_execution_timeout_decision.py"
    )


@pytest.fixture(scope="module")
def record(gate) -> dict[str, Any]:
    return json.loads(gate.RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def supersession(gate) -> dict[str, Any]:
    return json.loads(gate.SUPERSESSION.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cost(gate) -> dict[str, Any]:
    return json.loads(gate.gate_94().RECORD.read_text(encoding="utf-8"))


def _changed(doc: dict[str, Any], change) -> dict[str, Any]:
    mutated = copy.deepcopy(doc)
    change(mutated)
    return mutated


class TestTheCommittedRecords:
    def test_the_records_validate(self, gate):
        record, supersession = gate.validate()
        assert record["PRIMARY_OUTCOME"] == gate.READY
        assert supersession["STATUS"] == "SUPERSEDED_BEFORE_EXECUTION"

    def test_the_page_is_the_rendering(self, gate, record, supersession):
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(record, supersession)

    def test_the_decision(self, record):
        decision = record["TIMEOUT_DECISION"]
        assert (decision["REQUEST_TIMEOUT_V8_SECONDS"], decision["REQUEST_TIMEOUT_V9_SECONDS"]) == (
            60.0,
            240.0,
        )
        assert decision["DECISION_OWNER"] == "OPERATOR"
        assert decision["DECISION_TYPE"] == "EXECUTION_AVAILABILITY"
        for key in (
            "MATHEMATICALLY_DERIVED",
            "STATISTICALLY_ESTIMATED",
            "PROVIDER_GUARANTEED",
            "GUARANTEES_SUCCESSFUL_COMPLETION",
            "TIMEOUT_RISK_ELIMINATED",
        ):
            assert decision[key] is False
        assert decision["TIMEOUT_MISMATCH_REDUCED"] is True
        assert decision["END_TO_END_LATENCY_BOUND"] == "NOT_ESTABLISHED"
        assert decision["CLIENT_TIMEOUT_EXCEEDS_PROVIDER_COMPILATION_TIMEOUT"] is True

    def test_the_mismatch_is_a_possibility(self, record):
        gap = record["TIMEOUT_MISMATCH"]
        assert gap["PROVIDER_GRAMMAR_COMPILATION_TIMEOUT_SECONDS"] == 180
        assert gap["CURRENT_CLIENT_REQUEST_TIMEOUT_SECONDS"] == 60.0
        assert gap["CLIENT_TIMEOUT_IS_SHORTER_THAN_PROVIDER_COMPILATION_TIMEOUT"] is True
        assert gap["CLAIMS_A_REQUEST_WILL_EXCEED_60_SECONDS"] is False
        assert gap["STRICT_GRAMMAR_COMPILATION_LATENCY"] == "NOT_ESTABLISHED"

    def test_cost_and_body_unchanged(self, record):
        assert record["COST_EQUALITY"]["HARD_EXECUTION_COST_CEILING"] == "3.608"
        assert record["COST_EQUALITY"]["PLANNING_COST_ESTIMATE"] == "1.316316"
        assert record["COST_EQUALITY"]["TIMEOUT_CHANGES_BILLING"] is False
        assert record["V8_RECONFIRMATION"]["timeout_in_the_provider_body"] is False
        assert record["V8_RECONFIRMATION"]["request_body_characters"] == 31326

    def test_the_intention_is_not_an_approval(self, record):
        intentions = record["OPERATOR_STATED_INTENTIONS"]
        assert intentions["RESIDUAL_SEMANTIC_LIMITATION_INTENDED_FOR_V9_APPROVAL"] == "ACCEPT"
        assert intentions["IS_AN_APPROVAL"] is False

    def test_no_request_of_any_kind(self, record):
        assert set(record["ACCOUNTING"].values()) == {0}


class TestTheDecision:
    @pytest.mark.parametrize("value", [60.0, 180.0, 300.0, 239.9])
    def test_a_timeout_other_than_240_is_refused(self, gate, record, value):
        mutated = _changed(
            record, lambda d: d["TIMEOUT_DECISION"].__setitem__("REQUEST_TIMEOUT_V9_SECONDS", value)
        )
        with pytest.raises(
            gate.ValidationError, match="TIMEOUT_POLICY_REQUIRES_ARCHITECTURE_DECISION"
        ):
            gate._check_decision(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("PROVIDER_GUARANTEED", True),
            ("STATISTICALLY_ESTIMATED", True),
            ("MATHEMATICALLY_DERIVED", True),
            ("LATENCY_PREDICTION", True),
            ("BILLING_BOUND", True),
            ("GUARANTEES_SUCCESSFUL_COMPLETION", True),
            ("END_TO_END_LATENCY_BOUND", "240 SECONDS"),
            ("TIMEOUT_RISK_ELIMINATED", True),
            ("RETRY_ADDED_TO_OFFSET_THE_RISK", True),
            ("MAX_RETRIES_V9", 1),
            ("STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9", True),
            ("DECISION_OWNER", "PROVIDER"),
        ],
    )
    def test_the_budget_called_something_else_is_refused(self, gate, record, key, value):
        mutated = _changed(record, lambda d: d["TIMEOUT_DECISION"].__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_decision(mutated)

    def test_an_intention_recorded_as_an_approval_is_refused(self, gate, record):
        mutated = _changed(
            record, lambda d: d["OPERATOR_STATED_INTENTIONS"].__setitem__("IS_AN_APPROVAL", True)
        )
        with pytest.raises(gate.ValidationError, match="IS_AN_APPROVAL"):
            gate._check_decision(mutated)


class TestTheMismatch:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("CLAIMS_A_REQUEST_WILL_EXCEED_60_SECONDS", True),
            ("STRICT_GRAMMAR_COMPILATION_LATENCY", "30 SECONDS"),
            ("PROVIDER_GRAMMAR_COMPILATION_TIMEOUT_SECONDS", 60),
            ("ISSUE", "FREQUENCY"),
            ("documentation", []),
        ],
    )
    def test_the_mismatch_misstated_is_refused(self, gate, record, cost, key, value):
        mutated = _changed(record, lambda d: d["TIMEOUT_MISMATCH"].__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_mismatch(mutated, cost)


class TestCostAndV8:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("TIMEOUT_CHANGES_BILLING", True),
            ("TIMEOUT_ENTERS_THE_COST_DERIVATION", True),
            ("TIMEOUT_RELATED_PROVIDER_FEE", "LISTED"),
            ("HARD_EXECUTION_COST_CEILING", "3.9"),
            ("PLANNING_COST_ESTIMATE", "1.4"),
            ("COST_CEILING_RECORD_SHA256", "0" * 64),
        ],
    )
    def test_a_cost_that_moved_with_the_timeout_is_refused(self, gate, record, key, value):
        mutated = _changed(record, lambda d: d["COST_EQUALITY"].__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_cost(mutated)

    @pytest.mark.parametrize(
        "key, value",
        [
            ("approval_recorded", True),
            ("approval_file_exists", True),
            ("execution_record_exists", True),
            ("timeout_in_the_provider_body", True),
            ("request_body_sha256", "0" * 64),
            ("REQUEST_TIMEOUT", 240.0),
        ],
    )
    def test_a_v8_reconfirmation_edited_is_refused(self, gate, record, key, value):
        mutated = _changed(record, lambda d: d["V8_RECONFIRMATION"].__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_v8(mutated)


class TestTheSupersession:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("STATUS", "CONSUMED"),
            ("STATUS", "FAILED"),
            ("STATUS", "REJECTED_BY_PROVIDER"),
            ("V8_EXECUTED", True),
            ("V8_APPROVED", True),
            ("V8_APPROVAL_CONSUMED", True),
            ("V8_PACKET_MODIFIED", True),
            ("REFUSAL_OUTCOME", CONSUMED),
            ("REASON", "COST_CEILING_SEMANTICS_NOT_PROVEN"),
            ("SUPERSEDED_EXECUTION_PACKET_SHA256", "0" * 64),
            ("TIMEOUT_DECISION_RECORD_SHA256", "0" * 64),
        ],
    )
    def test_a_misrecorded_supersession_is_refused(self, gate, record, supersession, key, value):
        mutated = _changed(supersession, lambda d: d.__setitem__(key, value))
        with pytest.raises(gate.ValidationError, match="V8_SUPERSESSION_MISRECORDED"):
            gate._check_supersession(mutated, record)

    def test_an_approval_of_v8_is_refused(self, gate, tmp_path, monkeypatch):
        forged = tmp_path / "approval-v8.json"
        forged.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(gate, "APPROVAL_V8", forged)
        with pytest.raises(gate.ValidationError, match="V8_APPROVAL_FABRICATED"):
            gate._check_live_v8()

    @pytest.mark.parametrize("name", ["RECORD_V8", "RESPONSE_V8"])
    def test_an_execution_of_v8_on_disk_is_refused(self, gate, tmp_path, monkeypatch, name):
        artifact = tmp_path / f"{name.lower()}.json"
        artifact.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(gate, name, artifact)
        with pytest.raises(gate.ValidationError, match="V8_EXECUTED"):
            gate._check_live_v8()

    def test_an_edited_v8_packet_is_refused(self, gate, tmp_path, monkeypatch):
        edited = tmp_path / "packet-v8.json"
        edited.write_bytes(gate.PACKET_V8.read_bytes().replace(b"60.0", b"240.0", 1))
        monkeypatch.setattr(gate, "PACKET_V8", edited)
        with pytest.raises(gate.ValidationError, match="packet V8 was edited"):
            gate._check_live_v8()


class TestTheV8Guard:
    @pytest.fixture
    def runner_v8(self, gate):
        return gate.runner_v8()

    @pytest.mark.parametrize("digest", [V7_SHA256, V8_SHA256], ids=["V7", "V8"])
    def test_v7_and_v8_are_refused_as_superseded(self, runner_v8, digest):
        with pytest.raises(runner_v8.RefusedError) as refusal:
            runner_v8.refuse_if_consumed(digest)
        assert refusal.value.code == SUPERSEDED

    def test_v1_to_v6_are_still_refused_as_consumed(self, gate, runner_v8):
        for digest in gate.SHAS:
            with pytest.raises(runner_v8.RefusedError) as refusal:
                runner_v8.refuse_if_consumed(digest)
            assert refusal.value.code == CONSUMED

    def test_an_unseen_digest_is_not_refused(self, runner_v8):
        runner_v8.refuse_if_consumed("0" * 64)

    def test_without_its_record_the_guard_would_let_v8_through(
        self, runner_v8, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(runner_v8, "V8_SUPERSESSION_RECORD", tmp_path / "absent.json")
        runner_v8.refuse_if_consumed(V8_SHA256)

    def test_the_shipped_guard_passes_the_gate(self, gate):
        gate._check_v8_guard()

    def test_a_removed_guard_is_refused(self, gate, monkeypatch):
        honest = gate.runner_v8

        def unguarded():
            module = honest()
            module.refuse_if_superseded = lambda digest: None
            return module

        monkeypatch.setattr(gate, "runner_v8", unguarded)
        with pytest.raises(gate.ValidationError, match="V8_STILL_EXECUTABLE"):
            gate._check_v8_guard()

    def test_a_guard_that_calls_v8_consumed_is_refused(self, gate, monkeypatch):
        honest = gate.runner_v8

        def renaming():
            module = honest()

            def renamed(digest):
                if digest == V8_SHA256:
                    raise module.RefusedError(CONSUMED, "renamed")

            module.refuse_if_superseded = renamed
            return module

        monkeypatch.setattr(gate, "runner_v8", renaming)
        with pytest.raises(gate.ValidationError, match="never had an approval to spend"):
            gate._check_v8_guard()


class TestAccounting:
    @pytest.mark.parametrize(
        "key", ["MODEL_CALLS", "PROVIDER_REQUESTS", "TOKEN_COUNT_API_REQUESTS", "TED_BYTES_SENT"]
    )
    def test_a_request_made_while_preparing_is_refused(self, gate, record, key):
        mutated = _changed(record, lambda d: d["ACCOUNTING"].__setitem__(key, 1))
        with pytest.raises(gate.ValidationError, match=key):
            gate._check_accounting(mutated)


class TestRefusalsItDoesNotMakeItself:
    def test_a_gate_94_refusal_is_named_as_this_gates(self, gate, monkeypatch):
        honest = gate.gate_94

        def refusing():
            module = honest()

            def validate():
                raise module.ValidationError("V7_SUPERSESSION_MISRECORDED: synthetic")

            module.validate = validate
            return module

        monkeypatch.setattr(gate, "gate_94", refusing)
        with pytest.raises(
            gate.ValidationError, match="gate 94 no longer validates: V7_SUPERSESSION"
        ):
            gate.validate()
