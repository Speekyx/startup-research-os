"""Mission 1.84.25: CI gate 102 over the stage 6 diagnostic of V10, and the refusals it must make.

The diagnosis changes nothing: gate v1.4.0, its clause reader, the schema, the prompt and V10's record
stay byte for byte as they were. These tests pin what the diagnosis found, that it still re-derives
from the frozen code and the retained answer, and that the gate refuses a record, a quote, a digest or
a classification that drifted from it. Every mutation is made on a copy or on the loaded module, never
on a committed file, and no test can reach a provider: the one full derivation runs with the transport
and urlopen tripwired.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import pathlib
from typing import Any

import pytest
from sros_opportunity.assertion_audit_v1_3 import classify
from sros_opportunity.assertion_context import _clauses
from sros_opportunity.second_opportunity_gate_v1_4 import evaluate_second_opportunity_output_v1_4

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "infrastructure" / "scripts" / "render_second_opportunity_stage6_diagnostic_v10.py"
FIXTURE = pathlib.Path(__file__).resolve().parent / "test_semantic_gate_v1_3.py"
CATEGORIES = {
    "GENUINE_OUTPUT_DEFECT",
    "PROMPT_GATE_ALIGNMENT_DEFECT",
    "GATE_DEFECT",
    "SOURCE_SUPPORT_GAP",
}
REFUSED_FIELDS = {"observed_need", "candidate_intervention_class"}
#: The operator's own minimum cases. They are the only matrix text allowed to occur in V10's answer.
BRIEF_CASES = {
    "Software gap is established.",
    "Software gap is not established.",
    "Whether a software gap exists is unknown.",
    "Whether this reflects a software gap is not established.",
    "Whether this reflects a need, problem, or software gap is not established.",
    "Whether this reflects a need, problem or software gap is not established.",
    "No evidence establishes a need, problem, or software gap.",
    "A software gap is not established, but it probably exists.",
}


def _load_module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _load_module("gate_102_under_test", GATE)


@pytest.fixture(scope="module")
def derivation(gate: Any) -> tuple[dict[str, Any], list[int]]:
    """The one full derivation, under a tripwire on the real transport and on urlopen."""
    import urllib.request

    import sros_llm_gateway.transport as transport_module

    built: list[int] = []

    def fire(*args: object, **kwargs: object) -> None:  # pragma: no cover - must never run
        built.append(1)
        raise AssertionError("a transport was built")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(transport_module.UrllibTransport, "__init__", fire)
        patch.setattr(urllib.request, "urlopen", fire)
        record: dict[str, Any] = gate.validate()
    return record, built


@pytest.fixture(scope="module")
def record(derivation: tuple[dict[str, Any], list[int]]) -> dict[str, Any]:
    return derivation[0]


@pytest.fixture
def derived(gate: Any, record: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    """The derivation, reused: what the gate compares a record against, without deriving again."""
    monkeypatch.setattr(gate, "derive", lambda: copy.deepcopy(record))


@pytest.fixture(scope="module")
def fixture() -> Any:
    return _load_module("frozen_v1_3_fixture_under_test", FIXTURE)


def _observed_need(fixture: Any, sentence: str) -> tuple[str, ...]:
    reasons: tuple[str, ...] = evaluate_second_opportunity_output_v1_4(
        fixture.good_output(observed_need=sentence),
        fixture.PACKET,
        fixture.STATEMENTS,
        fixture.E2C,
        trusted_context=fixture.TRUSTED,
        source_metadata=fixture.META,
    ).refusal_reasons
    return reasons


class TestTheCommittedDiagnosis:
    def test_the_record_validates(self, record):
        assert record["PRIMARY_OUTCOME"] == (
            "STAGE_6_ROOT_CAUSE_ESTABLISHED_OPERATOR_DECISION_REQUIRED"
        )
        assert record["MISSION"] == "mission-1.84.25"

    def test_the_page_is_the_rendering_of_the_record(self, gate, record):
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(record)

    def test_the_record_is_written_with_lf_only(self, gate):
        assert b"\r" not in gate.RECORD.read_bytes()
        assert b"\r" not in gate.RECORD_MD.read_bytes()

    def test_the_invariants_are_the_operators(self, record):
        assert record["INVARIANTS"] == {
            "PROVIDER_CALLS": 0,
            "MODEL_INFERENCES": 0,
            "RETRIES": 0,
            "PERSISTENCE": 0,
            "NEW_EXECUTION_PACKET": "NO",
            "V11_CREATION": "NO",
            "OPPORTUNITY_2_CREATION": "NO",
            "HISTORICAL_VERDICTS_MUTABLE": "NO",
            "V10_REEXECUTION": "FORBIDDEN",
            "V10_OUTPUT_REWRITE_OR_REPAIR": "FORBIDDEN",
        }
        assert set(record["UNCHANGED"].values()) == {False}

    def test_the_check_writes_nothing(self, gate, derived, capsys):
        before = {p: p.read_bytes() for p in (gate.RECORD, gate.RECORD_MD)}
        assert gate.main(["--check"]) == 0
        assert "ok" in capsys.readouterr().out
        assert {p: p.read_bytes() for p in before} == before


class TestV10Reproduced:
    def test_the_frozen_gate_returns_the_retained_reasons(self, record, gate):
        v10 = record["V10_REPRODUCED"]
        retained = json.loads(gate.G101.RESPONSE.read_text(encoding="utf-8"))["validation"]
        assert v10["reasons"] == retained["reasons"]
        assert v10["persist"] is False
        assert [(r["field"], r["word"]) for r in v10["refused"]] == [
            ("observed_need", "software"),
            ("candidate_intervention_class", "market"),
        ]

    def test_software_is_split_off_its_whether_by_the_coordinated_clause_pattern(self, record):
        trace = record["V10_REPRODUCED"]["traces"][0]
        (sentence,) = trace["sentences"]
        assert [b["pattern"] for b in sentence["boundaries"]] == ["coord"]
        assert sentence["clauses"][0]["text"].startswith("whether ")
        assert sentence["clauses"][1]["text"].startswith("software gap is not established")
        assert [o["state"] for o in trace["occurrences"]] == ["ASSERTED"]
        assert trace["content_carries_word"] is False

    def test_market_is_asserted_in_one_clause_and_supplied_nowhere(self, record):
        trace = record["V10_REPRODUCED"]["traces"][1]
        (sentence,) = trace["sentences"]
        assert sentence["boundaries"] == []
        assert len(sentence["clauses"]) == 1
        assert [o["state"] for o in trace["occurrences"]] == ["ASSERTED"]
        assert trace["content_carries_word"] is False
        assert trace["metadata_labels_carrying_word"] == []
        assert trace["word_survives_the_supported_dimension_mask"] is True

    def test_v9_was_refused_on_the_same_word(self, record):
        v9 = record["V9_MARKET"]
        assert v9["prompt"] == "1.5.0"
        assert [o["state"] for o in v9["occurrences"]] == ["ASSERTED"]
        assert record["REQUEST_FORMS"] == {
            "V9": {"items": 6, "request_shaped": 0},
            "V10": {"items": 7, "request_shaped": 7},
        }

    def test_v10_is_rejected_whatever_the_gate_defect(self, record):
        assert record["V10_VERDICT_STANDS_WITHOUT_THE_GATE_DEFECT"] is True


class TestClassification:
    def test_each_refusal_gets_exactly_one_of_the_four_categories(self, record):
        found = {(c["field"], c["word"]): c["classification"] for c in record["CLASSIFICATIONS"]}
        assert found == {
            ("observed_need", "software"): "GATE_DEFECT",
            ("candidate_intervention_class", "market"): "GENUINE_OUTPUT_DEFECT",
        }
        for c in record["CLASSIFICATIONS"]:
            assert set(c["not"]) == CATEGORIES - {c["classification"]}

    def test_every_rule_a_classification_rests_on_is_quoted_from_its_file(self, record):
        quotes = record["POLICY_QUOTES"]
        for c in record["CLASSIFICATIONS"]:
            for key in c["rests_on"]:
                source = ROOT / quotes[key]["source"]
                text = " ".join(source.read_text(encoding="utf-8").split())
                assert " ".join(quotes[key]["quote"].split()) in text, key

    def test_prompt_v1_6_states_the_class_rule_and_not_the_whole_phrase_boundary(self, record):
        prompt = record["PROMPT"]
        assert prompt["STRUCTURAL_CHANNEL_SENTENCE_IN_V1_6"] is True
        assert prompt["STRUCTURAL_CHANNEL_SENTENCE_IN_V1_5"] is False
        assert prompt["DIMENSION_NAME_WHOLE_PHRASE_BOUNDARY_STATED"] is False

    def test_the_field_level_wording_is_corrected_and_left_where_written(self, record, gate):
        earlier = record["EARLIER_WORDING_CORRECTED"]
        assert earlier["EDITED_WHERE_WRITTEN"] is False
        assert set(earlier["quotes"]) == {
            "V10_RECORD_SEMANTIC_NOTE",
            "MISSION_1_84_24_REPORT",
            "CLAUDE_MD_1_159",
        }
        assert "only where the word is ASSERTED" in earlier["correction"]
        assert record["FROZEN"]["V10_RECORD_FILE_SHA256"] == gate.G101.RECORD_FILE_SHA256

    def test_no_v11_is_recommended_and_no_decision_is_taken(self, record):
        assessment = record["GENERATION_ASSESSMENT"]
        assert assessment["V11_RECOMMENDED"] is False
        assert (
            assessment["ANOTHER_ATTEMPT_UNDER_UNCHANGED_PROMPT_SCHEMA_AND_GATE_JUSTIFIED"] is False
        )
        assert [d["id"][:3] for d in record["OPERATOR_DECISIONS"]] == [
            "D1_",
            "D2_",
            "D3_",
            "D4_",
            "D5_",
        ]


class TestTheSyntheticMatrix:
    def test_the_divergences_are_the_scoped_lists_and_nothing_else(self, record):
        matrix = record["SYNTHETIC_MATRIX"]
        assert matrix["divergences"] == [f"L{n}" for n in range(1, 11)]
        groups = {r["case"]: r["group"] for r in matrix["cases"]}
        assert {groups[c] for c in matrix["divergences"]} == {"LIST_UNDER_ONE_SCOPE"}

    def test_every_asserted_control_is_refused_and_every_scoped_control_passes(self, record):
        for row in record["SYNTHETIC_MATRIX"]["cases"]:
            verdict = row["gate"]["observed_need"]["verdict"]
            if row["group"] == "ASSERTED_CONTROL":
                assert verdict == "REFUSE", row["case"]
            if row["group"] == "SCOPED_CONTROL":
                assert verdict == "PASS", row["case"]

    def test_the_premodifier_cases_are_left_undetermined(self, record):
        undetermined = record["SYNTHETIC_MATRIX"]["undetermined"]
        assert [u["case"] for u in undetermined] == ["M1", "M2", "M3"]
        assert {u["gate"] for u in undetermined} == {"REFUSE"}

    def test_no_case_outside_the_brief_occurs_in_the_v10_answer(self, record, gate):
        parsed = json.loads(gate.G101.RESPONSE.read_text(encoding="utf-8"))["parsed_output"]
        texts = json.dumps(parsed, ensure_ascii=False).lower()
        for row in record["SYNTHETIC_MATRIX"]["cases"]:
            if row["sentence"] in BRIEF_CASES:
                continue
            assert row["sentence"].lower().rstrip(".") not in texts, row["case"]

    def test_the_smallest_failing_pattern_on_the_frozen_gate_itself(self, fixture):
        """Independent of gate 102: one list item before a questioned gated word refuses it."""
        failing = "Whether a need or software exists is unknown."
        control = "Whether software exists is unknown."
        assert _observed_need(fixture, control) == ()
        (reason,) = _observed_need(fixture, failing)
        assert reason.startswith("observed_need audited UNSUPPORTED: 'software' appears in no")
        assert [(c.boundary, c.text) for c in _clauses(failing)] == [
            ("start", "whether a need"),
            ("coord", "software exists is unknown."),
        ]
        assert [o.state.value for o in classify(failing, "software")] == ["ASSERTED"]

    def test_a_conjunct_with_its_own_subject_still_splits(self):
        """What a successor must keep: an asserted clause after `and` is its own clause."""
        text = "No statement establishes a need, and buyers are willing to pay."
        assert [c.boundary for c in _clauses(text)] == ["start", "coord"]
        assert [o.state.value for o in classify(text, "willing to pay")] == ["ASSERTED"]


class TestTheGateRefuses:
    def test_an_edited_record(self, gate, derived, tmp_path, monkeypatch):
        target = tmp_path / gate.RECORD.name
        doc = json.loads(gate.RECORD.read_text(encoding="utf-8"))
        doc["CLASSIFICATIONS"][0]["classification"] = "GENUINE_OUTPUT_DEFECT"
        target.write_bytes((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode())
        monkeypatch.setattr(gate, "RECORD", target)
        with pytest.raises(gate.ValidationError, match="not what the diagnosis re-derives"):
            gate.validate()

    def test_a_page_that_is_not_the_rendering(self, gate, derived, tmp_path, monkeypatch, capsys):
        target = tmp_path / gate.RECORD_MD.name
        target.write_bytes(gate.RECORD_MD.read_bytes().replace(b"GATE_DEFECT", b"SOURCE_GAP"))
        monkeypatch.setattr(gate, "RECORD_MD", target)
        assert gate.main(["--check"]) == 1
        assert "is not the rendering" in capsys.readouterr().out

    def test_a_missing_record(self, gate, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "RECORD", tmp_path / "absent.json")
        with pytest.raises(gate.ValidationError, match="is missing"):
            gate.validate()

    def test_a_quote_no_longer_in_its_file(self, gate, monkeypatch):
        quotes = dict(gate.POLICY_QUOTES)
        path, quote = quotes["ONE_DENIAL_COVERS_A_LIST"]
        quotes["ONE_DENIAL_COVERS_A_LIST"] = (path, quote.replace("stays one", "is two"))
        monkeypatch.setattr(gate, "POLICY_QUOTES", quotes)
        with pytest.raises(gate.ValidationError, match="no longer in"):
            gate.check_quotes()

    def test_earlier_wording_that_is_no_longer_where_it_was_written(self, gate, monkeypatch):
        wording = dict(gate.EARLIER_WORDING)
        path, quote = wording["MISSION_1_84_24_REPORT"]
        wording["MISSION_1_84_24_REPORT"] = (path, quote.replace("asserted field", "assertion"))
        monkeypatch.setattr(gate, "EARLIER_WORDING", wording)
        with pytest.raises(gate.ValidationError, match="no longer in"):
            gate.earlier_wording()

    @pytest.mark.parametrize(
        "name", ["GATE_V1_4_SHA256", "GATE_V1_2_SHA256", "CLAUSE_READER_SHA256", "FIXTURE_SHA256"]
    )
    def test_a_frozen_digest_that_moved(self, gate, monkeypatch, name):
        monkeypatch.setattr(gate, name, "0" * 64)
        with pytest.raises(gate.ValidationError, match="not the frozen"):
            gate.frozen()

    def test_a_divergence_list_that_drifted(self, gate, monkeypatch):
        keep = {"L1", "S6"}
        monkeypatch.setattr(gate, "CASES", tuple(c for c in gate.CASES if c.case_id in keep))
        monkeypatch.setattr(gate, "EXPECTED_DIVERGENCES", ("S6",))
        with pytest.raises(gate.ValidationError, match="the matrix finds divergences"):
            gate.run_matrix()

    def test_the_small_matrix_itself_finds_the_divergence(self, gate, monkeypatch):
        keep = {"L1", "S6"}
        monkeypatch.setattr(gate, "CASES", tuple(c for c in gate.CASES if c.case_id in keep))
        monkeypatch.setattr(gate, "EXPECTED_DIVERGENCES", ("L1",))
        assert gate.run_matrix()["divergences"] == ["L1"]

    def test_a_case_whose_word_the_statements_carry(self, gate, monkeypatch):
        case = gate.Case(
            "X1",
            "SCOPED_CONTROL",
            "No notices exist.",
            "notices",
            "PASS",
            "SCOPED_IN_ITS_OWN_CLAUSE",
        )
        monkeypatch.setattr(gate, "CASES", (case,))
        with pytest.raises(gate.ValidationError, match="synthetic statements carry"):
            gate.run_matrix()

    def test_a_classification_of_a_field_that_was_not_refused(self, gate, monkeypatch):
        changed = copy.deepcopy(list(gate.CLASSIFICATIONS))
        changed[1]["field"] = "hypothesis_statement"
        monkeypatch.setattr(gate, "CLASSIFICATIONS", tuple(changed))
        with pytest.raises(gate.ValidationError, match="are not the ones classified"):
            gate.check_classifications(REFUSED_FIELDS)

    def test_a_classification_outside_the_four_categories(self, gate, monkeypatch):
        changed = copy.deepcopy(list(gate.CLASSIFICATIONS))
        changed[0]["classification"] = "MODEL_WAS_UNLUCKY"
        monkeypatch.setattr(gate, "CLASSIFICATIONS", tuple(changed))
        with pytest.raises(gate.ValidationError, match="not classified once"):
            gate.check_classifications(REFUSED_FIELDS)

    def test_a_classification_resting_on_an_unquoted_rule(self, gate, monkeypatch):
        changed = copy.deepcopy(list(gate.CLASSIFICATIONS))
        changed[0]["rests_on"] = [*changed[0]["rests_on"], "A_RULE_NOBODY_WROTE"]
        monkeypatch.setattr(gate, "CLASSIFICATIONS", tuple(changed))
        with pytest.raises(gate.ValidationError, match="unquoted rule"):
            gate.check_classifications(REFUSED_FIELDS)

    def test_the_committed_classifications_pass_their_own_check(self, gate):
        gate.check_classifications(REFUSED_FIELDS)

    def test_a_prompt_line_the_prompt_does_not_state(self, gate, monkeypatch):
        monkeypatch.setattr(
            gate, "PROMPT_V1_6_LINES", (*gate.PROMPT_V1_6_LINES[:-1], "a line nobody rendered")
        )
        monkeypatch.setattr(gate, "ADDED_IN_V1_6", "a line nobody rendered")
        with pytest.raises(gate.ValidationError, match="no longer states"):
            gate.prompt_lines()


class TestNothingMovedAndNothingWasCalled:
    def test_the_diagnosis_built_no_transport(self, derivation):
        assert derivation[1] == []

    def test_the_gate_imports_no_network_module(self):
        tree = ast.parse(GATE.read_text(encoding="utf-8"))
        imported = {
            (node.module or "") if isinstance(node, ast.ImportFrom) else alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for alias in node.names
        }
        for name in imported:
            assert not any(
                bad in name for bad in ("urllib", "http", "socket", "transport", "anthropic")
            ), name

    def test_v10_stays_consumed_and_its_later_stages_not_reached(self, record):
        governance = record["GOVERNANCE"]
        assert governance["V10_EXECUTION_APPROVAL_CONSUMED"] is True
        assert governance["V10_FURTHER_CALLS_AUTHORIZED"] is False
        assert set(governance["V10_STAGES_7_TO_10"].values()) == {"NOT_REACHED"}
        assert governance["HUMAN_REVIEW_PACKET_V10_EXISTS"] is False
        assert governance["OPPORTUNITY_2_EXISTS"] is False

    def test_no_packet_approval_or_record_for_a_v11_exists(self):
        data = ROOT / "docs" / "data"
        assert not [p.name for p in data.glob("*-v11*")]
        assert not [p.name for p in data.glob("*v11.json")]

    def test_the_frozen_digests_are_the_ones_v10_ran_under(self, record):
        frozen = record["FROZEN"]
        assert frozen["SEMANTIC_GATE_V1_4_SHA256"] == (
            "eb03899bbf7cc56f51994679dc4514f5c3c7ef63f4b6126aeb19ff18ccb160bb"
        )
        assert frozen["V10_RESPONSE_FILE_SHA256"] == (
            "6a9e5d4d59b7cf4d1ded6790042c747362bc47e75049611498bac88b1c10d8ea"
        )
        assert frozen["V10_RECORD_FILE_SHA256"] == (
            "981cfb436213de89d8afdc7d7e5f48ca492a67482b947c2d3bfa116dec30e8cd"
        )
        assert frozen["V10_APPROVAL_FILE_SHA256"] == (
            "5b0090e2f305e578d4600a3c4e109e87e4f1750b1ffc06703a3954f61599f9ea"
        )
