"""Mission 1.84.11. CI gate 77: the gate v1.3.0 freeze record, and what it refuses.

The freeze is only worth recording if it can fail. Each case below edits one thing the freeze pins
(a digest, a flag, the decision, an origin, the symmetry, the metadata decision) in a copy of the
record, or points the gate at a changed copy of a pinned file, and asserts the gate refuses it by
name.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import shutil

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE_PATH = (
    REPO_ROOT / "infrastructure" / "scripts" / "render_second_opportunity_semantic_gate_v1_3.py"
)


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def gate():
    return _module("semantic_gate_v1_3_freeze_under_test", GATE_PATH)


@pytest.fixture
def record(gate) -> dict:
    return json.loads(gate.RECORD.read_text(encoding="utf-8"))


@pytest.fixture
def decision(gate) -> dict:
    return json.loads(gate.DECISION.read_text(encoding="utf-8"))


def _refused(gate, monkeypatch, tmp_path, record: dict, match: str) -> None:
    copy = tmp_path / gate.RECORD.name
    copy.write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(gate, "RECORD", copy)
    with pytest.raises(gate.ValidationError, match=match):
        gate.validate()


def _decision_refused(gate, monkeypatch, tmp_path, decision: dict, match: str) -> None:
    copy = tmp_path / gate.DECISION.name
    copy.write_text(json.dumps(decision), encoding="utf-8")
    monkeypatch.setattr(gate, "DECISION", copy)
    with pytest.raises(gate.ValidationError, match=match):
        gate.validate_decision()


class TestTheCommittedFreeze:
    def test_it_validates(self, gate) -> None:
        record = gate.validate()
        assert record["GATE_VERSION"] == "second-opportunity-output-gate@1.3.0"

    def test_the_rendered_pages_are_current(self, gate) -> None:
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(gate.validate())
        assert gate.DECISION_MD.read_text(encoding="utf-8") == gate.render_decision(
            gate.validate_decision()
        )

    def test_the_order_is_recorded(self, record) -> None:
        assert record["GATE_V1_3_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY"] is True
        assert record["V3_DIAGNOSTIC_REPLAY_PERFORMED_BEFORE_FREEZE"] is False
        assert record["V3_TEXT_USED_AS_TEST_CASE"] is False
        assert record["WHITELIST_ENTRIES"] == 0
        assert record["SPECIAL_CASES"] == 0
        assert record["FORBIDDEN_CONCEPTS_REMOVED"] == 0

    def test_the_asymmetry_was_established_before_it_was_repaired(self, record) -> None:
        assert record["INFLECTION_NORMALIZATION_ASYMMETRY"] == "ESTABLISHED"

    def test_the_symmetry_matrix_found_nothing(self, record) -> None:
        matrix = record["SYMMETRY_MATRIX"]
        assert matrix["asymmetries"] == matrix["metadata_leaks"] == 0
        assert matrix["unlicensed_absences_missed"] == 0
        assert matrix["markers"] > 40 and matrix["concept_phrases"] > 20

    def test_one_function_reads_both_sides(self, record) -> None:
        invariant = record["NORMALIZATION_INVARIANT"]
        assert invariant["equal"] is True and invariant["one_function"] is True
        assert invariant["second_normalizers"] == []

    def test_nothing_was_sent_and_nothing_historical_moved(self, record) -> None:
        assert set(record["accounting"].values()) == {0}
        assert record["OUTPUT_SCHEMA_CHANGED"] is False
        assert record["PROMPT_CHANGED"] is False
        assert record["TED_REPRESENTATION_CHANGED"] is False
        assert record["PREDECESSOR_GATES_MUTATED"] is False

    def test_the_pins_are_not_placeholders(self, gate) -> None:
        assert gate.FROZEN_IMPLEMENTATION_SHA256 != "0" * 64
        assert gate.FROZEN_TEST_SHA256 != "0" * 64


class TestWhatTheFreezeRefuses:
    @pytest.mark.parametrize(
        ("key", "value", "match"),
        [
            ("GATE_V1_3_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY", False, "FROZEN_BEFORE"),
            ("V3_DIAGNOSTIC_REPLAY_PERFORMED_BEFORE_FREEZE", True, "PERFORMED_BEFORE_FREEZE"),
            ("V3_TEXT_USED_AS_TEST_CASE", True, "V3_TEXT_USED"),
            ("WHITELIST_ENTRIES", 1, "WHITELIST_ENTRIES"),
            ("SPECIAL_CASES", 1, "SPECIAL_CASES"),
            ("FORBIDDEN_CONCEPTS_REMOVED", 1, "FORBIDDEN_CONCEPTS_REMOVED"),
            ("PREDECESSOR_GATES_MUTATED", True, "PREDECESSOR_GATES_MUTATED"),
            ("OUTPUT_SCHEMA_CHANGED", True, "OUTPUT_SCHEMA_CHANGED"),
            ("PROMPT_CHANGED", True, "PROMPT_CHANGED"),
            ("TED_REPRESENTATION_CHANGED", True, "TED_REPRESENTATION_CHANGED"),
            ("LEXICAL_MATCH_IS_FACTUAL_SUPPORT", True, "LEXICAL_MATCH_IS_FACTUAL_SUPPORT"),
            ("INFLECTION_NORMALIZATION_ASYMMETRY", "NOT_REPRODUCED", "ASYMMETRY"),
            ("GATE_VERSION", "second-opportunity-output-gate@1.2.0", "GATE_VERSION"),
            ("IMPLEMENTATION_SHA256", "0" * 64, "IMPLEMENTATION_SHA256"),
        ],
    )
    def test_a_moved_field_is_refused(
        self, gate, record, monkeypatch, tmp_path, key, value, match
    ) -> None:
        record[key] = value
        _refused(gate, monkeypatch, tmp_path, record, match)

    def test_an_edited_decision_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        record["OPERATOR_DECISION"] = record["OPERATOR_DECISION"][1:]
        _refused(gate, monkeypatch, tmp_path, record, "OPERATOR_DECISION")

    def test_a_hidden_asymmetry_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        record["SYMMETRY_MATRIX"]["asymmetries"] = 0
        record["SYMMETRY_MATRIX"]["markers"] = 1
        _refused(gate, monkeypatch, tmp_path, record, "SYMMETRY_MATRIX")

    def test_a_metadata_origin_moved_into_structure_is_refused(
        self, gate, record, monkeypatch, tmp_path
    ) -> None:
        record["SOURCE_METADATA_POLICY"]["structural_facts_fields"].append("source_labels")
        _refused(gate, monkeypatch, tmp_path, record, "SOURCE_METADATA_POLICY")

    def test_a_wider_metadata_licence_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        record["SOURCE_METADATA_POLICY"]["licenses"] = "ANY_WORD_IN_THE_LABEL"
        _refused(gate, monkeypatch, tmp_path, record, "SOURCE_METADATA_POLICY")

    def test_a_softened_disjunction_policy_is_refused(
        self, gate, record, monkeypatch, tmp_path
    ) -> None:
        record["DISJUNCTION_POLICY"]["evaluates_disjunctions"] = True
        _refused(gate, monkeypatch, tmp_path, record, "DISJUNCTION_POLICY")

    def test_a_field_the_code_does_not_derive_is_refused(
        self, gate, record, monkeypatch, tmp_path
    ) -> None:
        record["ALLOWLIST"] = ["a sentence"]
        _refused(gate, monkeypatch, tmp_path, record, "does not derive")

    def test_a_missing_record_is_refused(self, gate, monkeypatch, tmp_path) -> None:
        monkeypatch.setattr(gate, "RECORD", tmp_path / "absent.json")
        with pytest.raises(gate.ValidationError, match="does not exist"):
            gate.validate()


class TestWhatTheDecisionRefuses:
    @pytest.mark.parametrize(
        ("key", "value", "match"),
        [
            ("SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT", True, "COUNTS_AS"),
            ("SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS", False, "MUST_NOT_LICENSE"),
            ("decision_owner", "SOFTWARE", "decision_owner"),
            ("decision_type", "STYLE", "decision_type"),
            ("mathematically_derived", True, "mathematically_derived"),
            ("moved_into_packet_structural_facts", True, "moved_into"),
            ("independent_of_any_answer", False, "independent_of_any_answer"),
        ],
    )
    def test_a_moved_decision_field_is_refused(
        self, gate, decision, monkeypatch, tmp_path, key, value, match
    ) -> None:
        decision[key] = value
        _decision_refused(gate, monkeypatch, tmp_path, decision, match)

    def test_a_reworded_operator_line_is_refused(
        self, gate, decision, monkeypatch, tmp_path
    ) -> None:
        decision["operator_decision"][1] = "SOURCE_NAME_COUNTS_WHEN_HELPFUL = true"
        _decision_refused(gate, monkeypatch, tmp_path, decision, "operator_decision")

    def test_a_missing_decision_is_refused(self, gate, monkeypatch, tmp_path) -> None:
        monkeypatch.setattr(gate, "DECISION", tmp_path / "absent.json")
        with pytest.raises(gate.ValidationError, match="does not exist"):
            gate.validate_decision()


class TestWhatThePinsRefuse:
    def test_a_changed_implementation_is_refused(self, gate, monkeypatch, tmp_path) -> None:
        source = gate.ROOT / gate.IMPLEMENTATION_FILES[0]
        changed = tmp_path / "lexical_inflection.py"
        shutil.copyfile(source, changed)
        changed.write_text(changed.read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8")
        monkeypatch.setattr(gate, "ROOT", tmp_path)
        monkeypatch.setattr(gate, "IMPLEMENTATION_FILES", ("lexical_inflection.py",))
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

    def test_a_thin_matrix_is_refused(self, gate, monkeypatch) -> None:
        demands = dict(gate.MATRIX_CLASSES)
        demands["TestSection18MetadataMatrix"] = 999
        monkeypatch.setattr(gate, "MATRIX_CLASSES", demands)
        with pytest.raises(gate.ValidationError, match="holds"):
            gate.validate()

    def test_a_whitelisted_answer_run_would_be_refused(self, gate, monkeypatch) -> None:
        answer = gate._answer_shingles()
        monkeypatch.setattr(gate, "_shingles", lambda text, width=6: set(list(answer)[:1]))
        with pytest.raises(gate.ValidationError, match="historical answer"):
            gate.validate()

    def test_a_one_sided_fold_is_refused_by_behaviour(self, gate, monkeypatch) -> None:
        """Fold the answer only, as v1.2.0 did: the symmetry matrix must see it."""
        from sros_opportunity import support_origin

        def exact_supply(lowered: str, phrase: str) -> list[tuple[int, int]]:
            pattern = r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])"
            return [(m.start(), m.end()) for m in re.finditer(pattern, lowered)]

        monkeypatch.setattr(support_origin, "inflection_spans", exact_supply)
        with pytest.raises(gate.ValidationError, match="symmetry matrix"):
            gate.validate()

    def test_a_second_normalizer_is_refused(self, gate, monkeypatch) -> None:
        monkeypatch.setattr(gate, "one_canonical_function", lambda: ["support_origin.py strips s"])
        with pytest.raises(gate.ValidationError, match="second normalizer"):
            gate.validate()
