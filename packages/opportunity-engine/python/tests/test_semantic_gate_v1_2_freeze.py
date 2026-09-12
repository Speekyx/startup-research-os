"""Mission 1.84.10. CI gate 75: the gate v1.2.0 freeze record, and what it refuses.

The freeze is only worth recording if it can fail. Each case below edits one thing the freeze pins
(a digest, a flag, the decision, a disposition, a concept, a channel) in a copy of the record, or
points the gate at a changed copy of a pinned file, and asserts the gate refuses it by name.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE_PATH = (
    REPO_ROOT / "infrastructure" / "scripts" / "render_second_opportunity_semantic_gate_v1_2.py"
)


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def gate():
    return _module("semantic_gate_v1_2_freeze_under_test", GATE_PATH)


@pytest.fixture
def record(gate) -> dict:
    return json.loads(gate.RECORD.read_text(encoding="utf-8"))


def _refused(gate, monkeypatch, tmp_path, record: dict, match: str) -> None:
    copy = tmp_path / gate.RECORD.name
    copy.write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(gate, "RECORD", copy)
    with pytest.raises(gate.ValidationError, match=match):
        gate.validate()


class TestTheCommittedFreeze:
    def test_it_validates(self, gate) -> None:
        record = gate.validate()
        assert record["GATE_VERSION"] == "second-opportunity-output-gate@1.2.0"

    def test_the_rendered_page_is_current(self, gate) -> None:
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(gate.validate())

    def test_the_order_is_recorded(self, record) -> None:
        assert record["GATE_V1_2_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY"] is True
        assert record["V3_DIAGNOSTIC_REPLAY_PERFORMED_BEFORE_FREEZE"] is False
        assert record["V3_TEXT_USED_AS_TEST_CASE"] is False
        assert record["WHITELIST_ENTRIES"] == 0
        assert record["FORBIDDEN_CONCEPTS_REMOVED"] == 0

    def test_nothing_was_sent(self, record) -> None:
        assert set(record["accounting"].values()) == {0}

    def test_the_schema_and_prompt_did_not_move(self, record) -> None:
        assert record["OUTPUT_SCHEMA_CHANGED"] is False
        assert record["PROMPT_CHANGED"] is False
        assert (
            record["OUTPUT_SCHEMA_SHA256"]
            == "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988"
        )

    def test_the_pins_are_not_placeholders(self, gate) -> None:
        assert len(gate.FROZEN_IMPLEMENTATION_SHA256) == 64
        assert len(gate.FROZEN_TEST_SHA256) == 64


class TestWhatTheFreezeRefuses:
    @pytest.mark.parametrize(
        ("key", "value", "match"),
        [
            ("GATE_V1_2_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY", False, "FROZEN_BEFORE"),
            ("V3_DIAGNOSTIC_REPLAY_PERFORMED_BEFORE_FREEZE", True, "PERFORMED_BEFORE_FREEZE"),
            ("V3_TEXT_USED_AS_TEST_CASE", True, "V3_TEXT_USED"),
            ("WHITELIST_ENTRIES", 1, "WHITELIST_ENTRIES"),
            ("FORBIDDEN_CONCEPTS_REMOVED", 1, "FORBIDDEN_CONCEPTS_REMOVED"),
            ("PREDECESSOR_GATE_MUTATED", True, "PREDECESSOR_GATE_MUTATED"),
            ("OUTPUT_SCHEMA_CHANGED", True, "OUTPUT_SCHEMA_CHANGED"),
            ("PROMPT_CHANGED", True, "PROMPT_CHANGED"),
            ("GATE_VERSION", "second-opportunity-output-gate@1.1.0", "GATE_VERSION"),
            ("IMPLEMENTATION_SHA256", "0" * 64, "IMPLEMENTATION_SHA256"),
        ],
    )
    def test_a_moved_field_is_refused(
        self, gate, record, monkeypatch, tmp_path, key, value, match
    ) -> None:
        record[key] = value
        _refused(gate, monkeypatch, tmp_path, record, match)

    def test_an_edited_decision_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        record["OPERATOR_DECISION"] = record["OPERATOR_DECISION"][:-1]
        _refused(gate, monkeypatch, tmp_path, record, "OPERATOR_DECISION")

    def test_a_softened_disposition_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        for entry in record["FIELD_POLICY"]:
            if entry["field"] == "commercial_claims_supported":
                entry["disposition"] = "EXPLICITLY_NOT_SUPPORTED"
        _refused(gate, monkeypatch, tmp_path, record, "FIELD_POLICY")

    def test_a_dropped_phrase_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        record["FORBIDDEN_CONCEPTS"][0]["phrases"] = record["FORBIDDEN_CONCEPTS"][0]["phrases"][1:]
        _refused(gate, monkeypatch, tmp_path, record, "FORBIDDEN_CONCEPTS")

    def test_prompt_text_as_evidence_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        record["SUPPORT_UNIVERSE"]["PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE"] = False
        _refused(gate, monkeypatch, tmp_path, record, "SUPPORT_UNIVERSE")

    def test_a_wider_trusted_licence_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        record["SUPPORT_UNIVERSE"]["trusted_context_licenses"] = "ANY_TEXT_IN_THE_FACT"
        _refused(gate, monkeypatch, tmp_path, record, "SUPPORT_UNIVERSE")

    def test_a_field_the_code_does_not_derive_is_refused(
        self, gate, record, monkeypatch, tmp_path
    ) -> None:
        record["ALLOWLIST"] = ["a sentence"]
        _refused(gate, monkeypatch, tmp_path, record, "does not derive")

    def test_a_missing_record_is_refused(self, gate, monkeypatch, tmp_path) -> None:
        monkeypatch.setattr(gate, "RECORD", tmp_path / "absent.json")
        with pytest.raises(gate.ValidationError, match="does not exist"):
            gate.validate()


class TestWhatThePinsRefuse:
    def test_a_changed_implementation_is_refused(self, gate, monkeypatch, tmp_path) -> None:
        source = gate.ROOT / gate.IMPLEMENTATION_FILES[0]
        changed = tmp_path / "assertion_context.py"
        shutil.copyfile(source, changed)
        changed.write_text(changed.read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8")
        monkeypatch.setattr(gate, "ROOT", tmp_path)
        monkeypatch.setattr(gate, "IMPLEMENTATION_FILES", ("assertion_context.py",))
        with pytest.raises(gate.ValidationError, match="not the one frozen"):
            gate.validate()

    def test_a_re_freeze_without_editing_the_pin_is_refused(self, gate, monkeypatch) -> None:
        monkeypatch.setattr(gate, "FROZEN_IMPLEMENTATION_SHA256", "f" * 64)
        with pytest.raises(gate.ValidationError, match="not the one frozen"):
            gate.validate()

    def test_a_changed_frozen_test_file_is_refused(self, gate, monkeypatch) -> None:
        monkeypatch.setattr(gate, "FROZEN_TEST_SHA256", "e" * 64)
        with pytest.raises(gate.ValidationError, match="frozen test file"):
            gate.validate()

    def test_a_historical_module_that_moved_is_refused(self, gate, monkeypatch) -> None:
        pinned = dict(gate.HISTORICAL_SHA256)
        first = next(iter(pinned))
        pinned[first] = "d" * 64
        monkeypatch.setattr(gate, "HISTORICAL_SHA256", pinned)
        with pytest.raises(gate.ValidationError, match="bb0f50a"):
            gate.validate()

    def test_a_thin_matrix_is_refused(self, gate, monkeypatch) -> None:
        demands = dict(gate.MATRIX_CLASSES)
        demands["TestSection5AssertionNotTokenPresence"] = 999
        monkeypatch.setattr(gate, "MATRIX_CLASSES", demands)
        with pytest.raises(gate.ValidationError, match="holds"):
            gate.validate()

    def test_a_whitelisted_answer_run_would_be_refused(self, gate, monkeypatch) -> None:
        answer = gate._answer_shingles()
        monkeypatch.setattr(gate, "_shingles", lambda text, width=6: set(list(answer)[:1]))
        with pytest.raises(gate.ValidationError, match="historical answer"):
            gate.validate()
