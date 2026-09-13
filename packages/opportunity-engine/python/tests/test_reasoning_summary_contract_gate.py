"""Mission 1.84.16: CI gate 86 over the reasoning-summary contract record, and the refusals it must make.

Mutations are made on copies in a temporary directory, or on schemas built in memory, with the gate
pointed at them, so the committed artifacts are never touched. Nothing here reaches a network.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
from collections.abc import Callable
from typing import Any

import pytest
from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
from sros_opportunity.second_opportunity_schema_v1_2 import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = (
    ROOT / "infrastructure" / "scripts" / "render_second_opportunity_reasoning_summary_contract.py"
)


@pytest.fixture(scope="module")
def gate() -> Any:
    spec = importlib.util.spec_from_file_location("gate_86_under_test", GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def copies(gate: Any, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    out = {}
    for name in ("RECORD", "DECISION", "V5_RECORD", "V5_RESPONSE"):
        source = getattr(gate, name)
        target = tmp_path / source.name
        target.write_bytes(source.read_bytes())
        monkeypatch.setattr(gate, name, target)
        out[name] = target
    monkeypatch.setattr(gate, "V5_REVIEW_PACKET", tmp_path / gate.V5_REVIEW_PACKET.name)
    monkeypatch.setattr(
        gate, "NOT_PREPARED", tuple(tmp_path / path.name for path in gate.NOT_PREPARED)
    )
    return out


def _edit(path: pathlib.Path, change: Callable[[dict], None]) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    change(doc)
    path.write_bytes((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def _schema(change: Callable[[dict], None]) -> dict:
    schema = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
    change(schema)
    return schema


class TestTheCommittedRecord:
    def test_the_record_is_the_rebuild(self, gate):
        record = gate.validate()
        assert record["PRIMARY_OUTCOME"] == "DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY"
        assert record["BLOCKER"] == "SEMANTIC_GATE_V1_3_0_BINDS_OUTPUT_SCHEMA_V1_1_0"

    def test_the_page_is_the_rendering(self, gate):
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(gate.validate())

    def test_the_copies_validate(self, gate, copies):
        gate.validate()

    def test_persistence_is_compatible_and_says_where_it_looked(self, gate):
        persistence = gate.validate()["PERSISTENCE"]
        assert persistence["PERSISTENCE_COMPATIBILITY"] == "COMPATIBLE"
        assert persistence["C_database_column"]["type"] == "TEXT"
        assert persistence["A_model"]["length_bound"] == "NONE"

    def test_the_target_is_derived_not_written(self, gate):
        headroom = gate.validate()["HEADROOM"]
        assert headroom["summary_v1_2_0"] == {"hard_maximum": 1500, "target": 1200}
        assert headroom["rows_changed"] == ["evidence_bound_reasoning_summary"]

    def test_the_accounting_is_zero(self, gate):
        assert set(gate.validate()["ACCOUNTING"].values()) == {0}


class TestTheDecisionIsTheOperators:
    @pytest.mark.parametrize(
        "key, value",
        [
            ("MATHEMATICALLY_DERIVED", True),
            ("HISTORICAL_OUTPUT_LENGTH_DERIVED", True),
            ("STATISTICALLY_ESTIMATED", True),
            ("PROVEN_OPTIMAL", True),
            ("historical_observations_used_to_derive_1500", True),
            ("new_hard_maximum", 1178),
        ],
    )
    def test_a_rewritten_decision_is_refused(self, gate, copies, key, value):
        _edit(copies["DECISION"], lambda d: d.__setitem__(key, value))
        with pytest.raises(gate.ValidationError):
            gate.validate()


class TestTheSchemaChangeIsExactlyOne:
    @pytest.mark.parametrize("bound", [1031, 1078, 1178, 900])
    def test_another_summary_bound_is_refused(self, gate, bound):
        schema = _schema(
            lambda s: s["properties"]["evidence_bound_reasoning_summary"].__setitem__(
                "maxLength", bound
            )
        )
        with pytest.raises(gate.ValidationError):
            gate.build(new=schema)

    def test_a_second_bound_is_refused(self, gate):
        schema = _schema(
            lambda s: s["properties"]["candidate_intervention_class"].__setitem__("maxLength", 400)
        )
        with pytest.raises(gate.ValidationError, match="UNAPPROVED_CHANGE"):
            gate.build(new=schema)

    def test_an_unbounded_field_is_refused(self, gate):
        schema = _schema(lambda s: s["properties"]["observed_need"].pop("maxLength"))
        with pytest.raises(gate.ValidationError):
            gate.build(new=schema)

    def test_v1_1_edited_in_place_is_refused(self, gate):
        old = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
        old["properties"]["evidence_bound_reasoning_summary"]["maxLength"] = 1500
        with pytest.raises(gate.ValidationError, match="v1.1.0 moved"):
            gate.build(old=old)


class TestV5StaysAsItWas:
    def test_v5_cannot_gain_a_review_packet(self, gate, copies):
        gate.V5_REVIEW_PACKET.write_bytes(b"{}\n")
        with pytest.raises(gate.ValidationError, match="review packet"):
            gate.validate()

    def test_v5s_record_cannot_change(self, gate, copies):
        _edit(copies["V5_RECORD"], lambda d: d.__setitem__("EXECUTION_APPROVAL_CONSUMED", False))
        with pytest.raises(gate.ValidationError, match="V5"):
            gate.validate()

    def test_v5_truncated_is_refused(self, gate, copies):
        def trim(doc: dict) -> None:
            doc["parsed_output"]["evidence_bound_reasoning_summary"] = doc["parsed_output"][
                "evidence_bound_reasoning_summary"
            ][:900]

        _edit(copies["V5_RESPONSE"], trim)
        with pytest.raises(gate.ValidationError, match="V5"):
            gate.validate()

    def test_a_v1_2_verdict_for_v5_is_refused(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["V5"].__setitem__("REVALIDATED_UNDER_V1_2_0", True))
        with pytest.raises(gate.ValidationError, match="rebuild"):
            gate.validate()


class TestNothingPastSectionTen:
    @pytest.mark.parametrize("index", range(6))
    def test_a_v6_artifact_no_later_mission_authored_is_refused(self, gate, copies, index):
        gate.NOT_PREPARED[index].write_bytes(b"{}\n")
        with pytest.raises(gate.ValidationError, match="section 10"):
            gate.validate()


def _authored(path: pathlib.Path, mission: str) -> None:
    if path.suffix == ".json":
        path.write_bytes(json.dumps({"recorded_by": f"mission-{mission}"}).encode("utf-8"))
    else:
        path.write_bytes(f'"""Mission {mission}. A successor artifact."""\n'.encode())


class TestTheDecisionSectionTenAskedFor:
    """Mission 1.84.17 re-pointed the absence check to the decision: a later mission's frozen
    successor gate re-opens the V6 path, and the record of what 1.84.16 did stays as it was."""

    def test_artifacts_a_later_mission_authored_are_admitted(self, gate, copies):
        for path in gate.NOT_PREPARED:
            _authored(path, "1.84.17")
        record = gate.validate()
        assert record["NOT_PREPARED"]["V6_CREATED"] is False

    def test_without_a_successor_freeze_they_are_refused(self, gate, copies, tmp_path, monkeypatch):
        monkeypatch.setattr(gate, "SUCCESSOR_FREEZE", tmp_path / "no-freeze.json")
        _authored(gate.NOT_PREPARED[4], "1.84.17")
        with pytest.raises(gate.ValidationError, match="section 10"):
            gate.validate()

    @pytest.mark.parametrize(
        "key, value",
        [
            ("mission", "mission-1.84.16"),
            ("GATE_V1_4_FROZEN", False),
            ("PREDECESSOR_GATE_VERSION", "second-opportunity-output-gate@1.2.0"),
        ],
    )
    def test_a_successor_freeze_that_is_not_the_decision_is_refused(
        self, gate, copies, tmp_path, monkeypatch, key, value
    ):
        freeze = tmp_path / gate.SUCCESSOR_FREEZE.name
        freeze.write_bytes(gate.SUCCESSOR_FREEZE.read_bytes())
        _edit(freeze, lambda d: d.__setitem__(key, value))
        monkeypatch.setattr(gate, "SUCCESSOR_FREEZE", freeze)
        _authored(gate.NOT_PREPARED[4], "1.84.17")
        with pytest.raises(gate.ValidationError, match="section 10"):
            gate.validate()

    def test_a_successor_bound_to_another_schema_is_refused(
        self, gate, copies, tmp_path, monkeypatch
    ):
        freeze = tmp_path / gate.SUCCESSOR_FREEZE.name
        freeze.write_bytes(gate.SUCCESSOR_FREEZE.read_bytes())
        _edit(freeze, lambda d: d["OUTPUT_SCHEMA"].__setitem__("sha256", "0" * 64))
        monkeypatch.setattr(gate, "SUCCESSOR_FREEZE", freeze)
        _authored(gate.NOT_PREPARED[4], "1.84.17")
        with pytest.raises(gate.ValidationError, match="section 10"):
            gate.validate()

    @pytest.mark.parametrize("index", range(6))
    def test_an_artifact_naming_this_mission_is_still_refused(self, gate, copies, index):
        _authored(gate.NOT_PREPARED[index], "1.84.16")
        with pytest.raises(gate.ValidationError, match="section 10"):
            gate.validate()

    @pytest.mark.parametrize(
        "key, value",
        [
            ("V6_CREATED", True),
            ("OPERATOR_EXECUTION_APPROVAL_RECORDED", True),
            ("RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6", True),
        ],
    )
    def test_the_record_cannot_claim_v6(self, gate, copies, key, value):
        _edit(copies["RECORD"], lambda d: d["NOT_PREPARED"].__setitem__(key, value))
        with pytest.raises(gate.ValidationError):
            gate.validate()

    @pytest.mark.parametrize(
        "key", ["MODEL_CALLS", "PROVIDER_REQUESTS", "TOKEN_COUNT_API_REQUESTS", "TED_BYTES_SENT"]
    )
    def test_the_accounting_cannot_move(self, gate, copies, key):
        _edit(copies["RECORD"], lambda d: d["ACCOUNTING"].__setitem__(key, 1))
        with pytest.raises(gate.ValidationError):
            gate.validate()

    def test_persistence_cannot_be_claimed_without_the_audit(self, gate, copies):
        _edit(copies["RECORD"], lambda d: d["PERSISTENCE"].pop("C_database_column"))
        with pytest.raises(gate.ValidationError):
            gate.validate()

    def test_the_coupling_cannot_be_hidden(self, gate, copies):
        _edit(
            copies["RECORD"],
            lambda d: d["SEMANTIC_GATE"]["coupling"].__setitem__(
                "requires_a_successor_identity", False
            ),
        )
        with pytest.raises(gate.ValidationError):
            gate.validate()
