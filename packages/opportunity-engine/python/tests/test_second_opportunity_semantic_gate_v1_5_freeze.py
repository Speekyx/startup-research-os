"""Mission 1.84.26: CI gate 103 over the v1.5.0 freeze record, and the refusals it must make.

The record is derived once, under a tripwire on the real transport and on urlopen, and every test that
needs a verdict reads that one derivation. Every mutation is made on the loaded module or on a copy in
a temporary directory, never on a committed file, and nothing here can reach a provider.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import pathlib
from typing import Any

import pytest
from sros_opportunity import assertion_audit_v1_5 as audit_v1_5
from sros_opportunity import assertion_scope_v1_5 as scope
from sros_opportunity.assertion_context import OccurrenceState

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "infrastructure" / "scripts" / "render_second_opportunity_semantic_gate_v1_5.py"


def _load(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _load("gate_103_under_test", GATE)


@pytest.fixture(scope="module")
def derivation(gate: Any) -> tuple[dict[str, Any], list[int]]:
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
    monkeypatch.setattr(gate, "derive", lambda: copy.deepcopy(record))


@pytest.fixture(scope="module")
def fixture(gate: Any) -> Any:
    return _load("fixture_for_gate_103_tests", gate.FIXTURE)


def _rows(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {r["case"]: r for r in record["MATRIX"]["cases"]}


class TestTheCommittedRecord:
    def test_the_record_validates(self, record):
        assert record["GATE_VERSION"] == "second-opportunity-output-gate@1.5.0"
        assert record["PREDECESSOR_GATE_VERSION"] == "second-opportunity-output-gate@1.4.0"
        assert record["MISSION"] == "mission-1.84.26"

    def test_the_page_is_the_rendering(self, gate, record):
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(record)

    def test_lf_only(self, gate):
        assert b"\r" not in gate.RECORD.read_bytes()
        assert b"\r" not in gate.RECORD_MD.read_bytes()

    def test_the_invariants_hold(self, record):
        invariants = record["INVARIANTS"]
        for key in ("PROVIDER_CALLS", "MODEL_INFERENCES", "TOKEN_COUNTS", "RETRIES", "PERSISTENCE"):
            assert invariants[key] == 0, key
        assert invariants["V11_CREATION"] == "NO"
        assert invariants["OPPORTUNITY_2_CREATION"] == "NO"
        assert invariants["V10_OUTCOME"] == "EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY"
        assert set(record["NOT_CHANGED"].values()) == {False}

    def test_the_check_writes_nothing(self, gate, derived, capsys):
        before = {p: p.read_bytes() for p in (gate.RECORD, gate.RECORD_MD)}
        assert gate.main(["--check"]) == 0
        assert "ok" in capsys.readouterr().out
        assert {p: p.read_bytes() for p in before} == before

    def test_the_derivation_built_no_transport(self, derivation):
        assert derivation[1] == []


class TestTheDifferential:
    def test_every_verdict_change_is_an_authorised_repair(self, record):
        rows = _rows(record)
        for case_id in record["MATRIX"]["VERDICT_CHANGES"]:
            row = rows[case_id]
            assert row["divergence_class"] != "NONE", case_id
            assert row["v1_4_0"] == "REFUSE" and row["v1_5_0"] == "PASS", case_id
            assert row["attribution"] and set(row["attribution"]) <= {"A", "B"}, case_id

    def test_no_case_the_policy_refuses_is_passed(self, record):
        for row in record["MATRIX"]["cases"]:
            if row["intended"] == "REFUSE":
                assert row["v1_5_0"] == "REFUSE", row["case"]

    def test_the_divergence_is_limited_to_a_and_b(self, record):
        matrix = record["MATRIX"]
        assert set(matrix["DIVERGENCES_BY_ATTRIBUTION"]) <= {"A", "B", "A+B"}
        assert matrix["UNATTRIBUTED_DIVERGENCES"] == 0
        assert matrix["SUCCESSOR_ADDED_ASSERTIONS"] == 0
        assert matrix["POLICY_REFUSALS_PASSED_BY_V1_5_0"] == 0

    def test_residual_over_refusals_keep_v1_4_0_s_refusing_verdict(self, record):
        rows = _rows(record)
        for case_id in record["MATRIX"]["RESIDUAL_OVER_REFUSALS"]:
            assert rows[case_id]["v1_4_0"] == rows[case_id]["v1_5_0"] == "REFUSE", case_id

    def test_the_three_explicit_proofs(self, record):
        matrix = record["MATRIX"]
        assert matrix["GENUINE_ASSERTIONS_STILL_REFUSED"] > 0
        assert matrix["GENUINE_COORDINATED_CLAUSES_STILL_SPLIT"] > 0
        assert matrix["CONTRASTIVE_REASSERTIONS_STILL_REFUSED"] > 0

    def test_the_operator_s_examples(self, record):
        rows = _rows(record)
        for case_id in ("L1", "L3", "M1"):
            assert rows[case_id]["v1_5_0"] == "PASS", case_id
        for case_id in ("S8",):
            assert rows[case_id]["v1_4_0"] == rows[case_id]["v1_5_0"] == "PASS"
        for case_id in ("N63", "N49", "N50", "N51"):
            assert rows[case_id]["v1_5_0"] == "REFUSE", case_id

    def test_the_39_diagnosis_cases_are_all_here(self, record):
        ids = set(_rows(record))
        expected = {f"A{n}" for n in range(1, 10)} | {f"S{n}" for n in range(1, 14)}
        expected |= {f"L{n}" for n in range(1, 15)} | {"M1", "M2", "M3"}
        assert expected <= ids

    def test_the_sweep_moves_nothing_it_cannot_attribute(self, record):
        sweep = record["SWEEP"]
        assert sweep["SENTENCES_WITH_A_GATED_WORD"] > 0
        assert sweep["UNATTRIBUTED"] == 0 and sweep["ASSERTIONS_ADDED"] == 0
        assert record["SEAM"]["DIFFERENCES"] == 0 and record["SEAM"]["READINGS_COMPARED"] > 0


class TestHistory:
    def test_v10_stays_refused_on_market_alone(self, record):
        v10 = record["HISTORY"]["V10"]
        assert v10["HISTORICAL_OUTCOME"] == "EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY"
        assert v10["HISTORICAL_RECORD_EDITED"] is False
        assert len(v10["RETAINED_REASONS"]) == 2
        (reason,) = v10["V1_5_0_WOULD_REFUSE_WITH"]
        assert reason.startswith("candidate_intervention_class audited UNSUPPORTED: 'market'")
        assert v10["V1_5_0_WOULD_PERSIST"] is False
        assert v10["ELIGIBLE_CANDIDATE"] is False
        assert v10["HUMAN_REVIEW_CANDIDATE"] is False
        assert v10["PERSISTENCE_CANDIDATE"] is False

    def test_v9_is_unchanged_under_the_successor(self, record):
        v9 = record["HISTORY"]["V9"]
        assert v9["V1_5_0_WOULD_REFUSE_WITH"] == v9["RETAINED_REASONS"]
        assert v9["V1_5_0_WOULD_REMOVE"] == []

    def test_the_historical_stage_tables_are_untouched(self, record):
        for label in ("V9", "V10"):
            stages = record["HISTORY"][label]["HISTORICAL_STAGES"]
            assert stages["6_semantic_output_gate_v1_4_0"] == "FAILED"
            assert stages["10_human_review"] == "NOT_REACHED"
        assert record["HISTORY"]["V11_ARTIFACTS"] == 0
        assert record["HISTORY"]["HUMAN_REVIEW_PACKETS"] == 0


class TestTheGateRefuses:
    def test_an_edited_record(self, gate, derived, tmp_path, monkeypatch):
        target = tmp_path / gate.RECORD.name
        doc = json.loads(gate.RECORD.read_text(encoding="utf-8"))
        doc["HISTORY"]["V10"]["PERSISTENCE_CANDIDATE"] = True
        target.write_bytes((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode())
        monkeypatch.setattr(gate, "RECORD", target)
        with pytest.raises(gate.ValidationError, match="is not what the code derives"):
            gate.validate()

    def test_a_page_that_is_not_the_rendering(self, gate, derived, tmp_path, monkeypatch, capsys):
        target = tmp_path / gate.RECORD_MD.name
        target.write_bytes(gate.RECORD_MD.read_bytes().replace(b"1.5.0", b"1.6.0"))
        monkeypatch.setattr(gate, "RECORD_MD", target)
        assert gate.main(["--check"]) == 1
        assert "is not the rendering" in capsys.readouterr().out

    def test_a_missing_record(self, gate, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "RECORD", tmp_path / "absent.json")
        with pytest.raises(gate.ValidationError, match="is missing"):
            gate.validate()

    @pytest.mark.parametrize("key", ["gate_75_v1_2_0", "gate_77_v1_3_0", "gate_87_v1_4_0"])
    def test_a_predecessor_that_moved(self, gate, monkeypatch, key):
        digests = dict(gate.PREDECESSOR_DIGESTS)
        digests[key] = (digests[key][0], "0" * 64)
        monkeypatch.setattr(gate, "PREDECESSOR_DIGESTS", digests)
        with pytest.raises(gate.ValidationError, match="not its frozen"):
            gate.frozen_block()

    @pytest.mark.parametrize(
        ("name", "match"),
        [
            ("CLAUSE_READER_SHA256", "clause reader moved"),
            ("FROZEN_IMPLEMENTATION_SHA256", "implementation is"),
            ("FROZEN_TEST_SHA256", "test file is"),
        ],
    )
    def test_a_pinned_digest_that_moved(self, gate, monkeypatch, name, match):
        monkeypatch.setattr(gate, name, "0" * 64)
        with pytest.raises(gate.ValidationError, match=match):
            gate.frozen_block()

    def test_the_diagnosis_moved(self, gate, monkeypatch):
        files = dict(gate.DIAGNOSIS_FILES)
        first = next(iter(files))
        files[first] = "0" * 64
        monkeypatch.setattr(gate, "DIAGNOSIS_FILES", files)
        with pytest.raises(gate.ValidationError, match="diagnosis"):
            gate.frozen_block()

    def test_a_successor_module_that_imports_the_network(self, gate, monkeypatch, tmp_path):
        rogue = tmp_path / "rogue.py"
        rogue.write_text("import urllib.request\n", encoding="utf-8")
        monkeypatch.setattr(gate, "SUCCESSOR_MODULES", (str(rogue),))
        with pytest.raises(gate.ValidationError, match="imports urllib"):
            gate.frozen_block()

    def test_a_rebound_function_that_was_rewritten(self, gate, monkeypatch):
        original = gate._functions

        def rewritten(relative: str) -> dict[str, ast.FunctionDef]:
            found = original(relative)
            if relative.endswith("assertion_audit_v1_5.py"):
                node = found["audit_output"]
                node.body = node.body[1:]
            return found

        monkeypatch.setattr(gate, "_functions", rewritten)
        with pytest.raises(gate.ValidationError, match="with only its renames"):
            gate.rebinding_block()

    def test_a_shared_helper_that_is_no_longer_v1_3_0_s(self, gate, monkeypatch):
        monkeypatch.setattr(audit_v1_5, "maskable_labels", lambda *a, **k: ())
        with pytest.raises(gate.ValidationError, match="is not v1.3.0's object"):
            gate.rebinding_block()

    def test_a_case_the_policy_refuses_and_the_successor_passes(self, gate, monkeypatch, fixture):
        case = gate.Case(
            "X1",
            "ASSERTED_CONTROL",
            "Whether a need or software exists is unknown.",
            "software",
            "REFUSE",
            gate.N,
        )
        monkeypatch.setattr(gate, "CASES", (case,))
        with pytest.raises(gate.ValidationError, match="the policy refuses it"):
            gate.matrix_block(fixture)

    def test_a_verdict_that_moves_where_no_repair_was_authorised(self, gate, monkeypatch, fixture):
        case = gate.Case(
            "X2",
            "SCOPED_CONTROL",
            "Software gap is not established.",
            "software",
            "PASS",
            gate.N,
        )
        monkeypatch.setattr(gate, "CASES", (case,))
        with pytest.raises(gate.ValidationError, match="no repair was authorised"):
            gate.matrix_block(fixture)

    def test_a_divergence_neither_repair_explains(self, gate, monkeypatch, fixture):
        readers = dict(gate.READERS)
        readers["d1_only"] = readers["v1_4_0"]
        readers["d2_only"] = readers["v1_4_0"]
        monkeypatch.setattr(gate, "READERS", readers)
        case = gate.Case(
            "X3",
            "LIST_UNDER_ONE_SCOPE",
            "Software gap is not established.",
            "software",
            "PASS",
            gate.B,
        )
        monkeypatch.setattr(gate, "CASES", (case,))
        with pytest.raises(gate.ValidationError, match="neither repair explains"):
            gate.matrix_block(fixture)

    def test_a_reader_that_adds_an_assertion(self, gate, monkeypatch):
        def always(clause: str, start: int, end: int, head: bool) -> tuple[OccurrenceState, str]:
            return OccurrenceState.ASSERTED, "asserted"

        readers = dict(gate.READERS)
        readers["v1_5_0"] = (scope.scoped_clauses, always)
        monkeypatch.setattr(gate, "READERS", readers)
        with pytest.raises(gate.ValidationError, match="that v1.4.0 did not"):
            gate.attribution("No software gap is established.")

    def test_a_pinned_divergence_set_that_drifted(self, gate, monkeypatch, fixture):
        keep = {"L1", "S6"}
        monkeypatch.setattr(gate, "CASES", tuple(c for c in gate.CASES if c.case_id in keep))
        with pytest.raises(gate.ValidationError, match="EXPECTED_VERDICT_CHANGES"):
            gate.matrix_block(fixture)

    def test_a_historical_response_that_moved(self, gate, monkeypatch):
        monkeypatch.setattr(gate.G101, "RESPONSE_FILE_SHA256", "0" * 64)
        with pytest.raises(gate.ValidationError):
            gate.history_block()
