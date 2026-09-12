"""Mission 1.84.11. CI gate 78: V3's answer replayed diagnostically through the frozen gate v1.3.0.

The replay ran once, after the freeze commit was pushed, from Mission 1.84.10's authenticated
snapshot. These tests defend the record it wrote and state, as facts, what it found: the historical
verdicts of v1.1.0 and v1.2.0 reproduce, and v1.3.0 stops the answer at stage 6 on one statement,
for a reason that is now TRUE. The answer asserts a word its sources supplied only inside a
publisher's name, and it joins two alternatives under one OBSERVED classification. That is a
genuine support failure of the answer, not another defect of the gate, so nothing is repaired and
no V4 exists.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest
from sros_opportunity.assertion_audit_v1_3 import (
    DISJUNCTIVE_OBSERVED_STATEMENT,
    SOURCE_METADATA_NOT_FACTUAL_SUPPORT,
)
from sros_opportunity.support_origin import SourceMetadataContext, split_statement

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE_PATH = (
    REPO_ROOT
    / "infrastructure"
    / "scripts"
    / "render_second_opportunity_v3_diagnostic_replay_v1_3.py"
)
FIELD = "statement_classifications[7].statement"


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate():
    return _module("v3_diagnostic_replay_v1_3_under_test", GATE_PATH)


@pytest.fixture(scope="module")
def record(gate) -> dict:
    return json.loads(gate.RECORD.read_text(encoding="utf-8"))


@pytest.fixture
def fast(gate, monkeypatch):
    """The history this replay stands on is checked by its own test; skip it where it is not the
    subject, so each refusal below is decided by the field it edits."""
    monkeypatch.setattr(gate, "_require_history", lambda: None)
    return gate


def _refused(gate, monkeypatch, tmp_path, record: dict, match: str) -> None:
    copy = tmp_path / gate.RECORD.name
    copy.write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(gate, "RECORD", copy)
    with pytest.raises(gate.ValidationError, match=match):
        gate.validate()


class TestTheReplayRecord:
    def test_it_re_derives_with_its_history_standing(self, gate) -> None:
        record = gate.validate()
        assert record["DIAGNOSTIC_ONLY"] is True

    def test_the_page_is_current(self, gate, record) -> None:
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(record)

    def test_it_names_the_freeze_it_ran_after(self, gate, record) -> None:
        assert record["FREEZE_COMMIT"] == gate.FREEZE_COMMIT
        assert record["GATE_V1_3_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY"] is True
        ordering = gate.git_ordering()
        if ordering["state"] == "CHECKED":
            assert all(v is True for k, v in ordering.items() if k != "state"), ordering

    def test_the_historical_verdicts_reproduce(self, record) -> None:
        assert record["HISTORICAL_V3_GATE_V1_1_VERDICT"] == "FAILED"
        assert record["HISTORICAL_V3_GATE_V1_1_REASONS_REPRODUCED"] is True
        assert record["HISTORICAL_V3_GATE_V1_1_REASON_COUNT"] == 5
        assert record["HISTORICAL_DIAGNOSTIC_GATE_V1_2_VERDICT"] == "FAILED"
        assert record["HISTORICAL_DIAGNOSTIC_GATE_V1_2_REASONS_REPRODUCED"] is True
        (reason,) = record["HISTORICAL_DIAGNOSTIC_GATE_V1_2_REASONS"]
        assert "'tender' appears in no supplied statement" in reason

    def test_the_snapshot_is_the_one_1_84_10_authenticated(self, gate, record) -> None:
        previous = json.loads(gate.REPLAY_V1_2_RECORD.read_text(encoding="utf-8"))
        assert record["PACKET_SNAPSHOT"] == previous["PACKET_SNAPSHOT"]
        auth = record["SNAPSHOT_AUTHENTICATION"]
        assert auth["representation_sha256"].startswith("2528a56a")
        assert auth["prompt_sha256"].startswith("1677cbe5")

    def test_v3_stays_what_it_was(self, record) -> None:
        assert record["V3_HISTORICALLY_REJECTED"] is True
        assert record["V3_CANDIDATE"] is False
        assert record["V3_PERSISTABLE"] is False
        assert record["V3_HUMAN_REVIEW_PACKET"] == "NOT_PRODUCED"
        assert record["V3_APPROVAL_CONSUMED"] is True
        assert record["STAGE_10_MANUFACTURED"] is False
        assert record["DIAGNOSTIC_STAGES"]["10_human_review"] == "NOT_MANUFACTURED_DIAGNOSTIC_ONLY"
        assert record["PERSISTED"] == "NOTHING"
        assert set(record["accounting"].values()) == {0}


class TestWhatTheReplayFound:
    """Recorded as facts. The gate is not touched on the strength of them."""

    def test_stage_6_stops_on_one_statement_and_nothing_else(self, record) -> None:
        assert record["DIAGNOSTIC_GATE_V1_3_VERDICT"] == "FAILED"
        assert record["DIAGNOSTIC_FAILED_STAGE"] == "6_semantic_output_gate_v1_3_0"
        (only,) = record["DIAGNOSTIC_GATE_V1_3_REASONS"]
        assert only.startswith(f"{FIELD} audited UNSUPPORTED")
        failed = [
            a["field"]
            for a in record["DIAGNOSTIC_AUDIT"]
            if a["verdict"] in ("UNSUPPORTED", "BOUND_EXCEEDED")
        ]
        assert failed == [FIELD]

    def test_the_refusal_is_now_true(self, record) -> None:
        (reason,) = record["DIAGNOSTIC_GATE_V1_3_REASONS"]
        assert f"{SOURCE_METADATA_NOT_FACTUAL_SUPPORT}: 'tender' is asserted" in reason
        assert "ted-eu:REGISTRY_DISPLAY_NAME:1" in reason
        assert "appears in no" not in reason

    def test_the_word_is_supplied_only_inside_the_publisher_s_name(self, record) -> None:
        metadata = record["SOURCE_METADATA_CONTEXT"]
        from sros_opportunity.support_origin import SourceMetadataLabel, SourceMetadataLabelKind

        labels = tuple(
            SourceMetadataLabel(
                lb["label_id"],
                lb["source_id"],
                SourceMetadataLabelKind(lb["kind"]),
                lb["text"],
                lb["provenance"],
            )
            for lb in metadata["labels"]
        )
        context = SourceMetadataContext(version=metadata["version"], labels=labels)
        for statement in record["PACKET_SNAPSHOT"]["claim_statements"].values():
            content, _carried = split_statement(statement, context.labels)
            assert "tender" not in content
        joined = " ".join(record["PACKET_SNAPSHOT"]["claim_statements"].values()).lower()
        assert "tenders electronic daily" in joined

    def test_the_statement_also_joins_two_alternatives_under_one_classification(
        self, record
    ) -> None:
        (reason,) = record["DIAGNOSTIC_GATE_V1_3_REASONS"]
        assert DISJUNCTIVE_OBSERVED_STATEMENT in reason

    def test_the_exact_unsupported_proposition_is_the_answer_s_own(self, gate, record) -> None:
        answer = json.loads(
            (gate.DATA / "second-opportunity-synthesis-response-v3.json").read_text(
                encoding="utf-8"
            )
        )["parsed_output"]
        (proposition,) = record["UNSUPPORTED_PROPOSITIONS"]
        assert proposition["field"] == FIELD
        assert proposition["text"] == answer["statement_classifications"][7]["statement"]
        assert answer["statement_classifications"][7]["classification"] == (
            "OBSERVED_OR_EVIDENCE_SUPPORTED"
        )

    def test_it_is_a_genuine_output_failure_and_no_v4_exists(self, record) -> None:
        assert (
            record["DIAGNOSTIC_OUTCOME"] == "V3_DIAGNOSTIC_REVEALED_GENUINE_OUTPUT_SUPPORT_FAILURE"
        )
        for stage in (
            "7_evidence_boundary_and_no_distortion",
            "8_attribution_and_provenance",
            "9_persistence_eligibility",
        ):
            assert record["DIAGNOSTIC_STAGES"][stage] == "NOT_REACHED"
        assert record["V4_CREATION_CONDITION_MET"] is False
        assert record["EXECUTION_PACKET_V4"] == "NOT_CREATED"

    def test_the_metadata_channel_came_from_the_registry(self, record) -> None:
        texts = [lb["text"] for lb in record["SOURCE_METADATA_CONTEXT"]["labels"]]
        assert "Tenders Electronic Daily (EU public procurement)" in texts
        assert "Tenders Electronic Daily" in texts
        assert all(
            "source-catalog-v1.json" in lb["provenance"]
            for lb in record["SOURCE_METADATA_CONTEXT"]["labels"]
        )

    def test_outcomes_are_classified_by_rule(self, gate) -> None:
        passed = dict.fromkeys(gate.DIAGNOSTIC_STAGES_JUDGED, "PASSED")
        assert gate.classify_outcome(passed, []) == gate.PASSED_DIAGNOSTIC
        failed = {**passed, gate.STAGE_6_V1_3: "FAILED"}
        assert gate.classify_outcome(failed, [f"x {DISJUNCTIVE_OBSERVED_STATEMENT}"]) == (
            gate.DISJUNCTION_ONLY
        )
        assert gate.classify_outcome(failed, ["an unrelated refusal"]) == gate.BLOCKER
        stage_8 = {**passed, "8_attribution_and_provenance": "FAILED"}
        assert gate.classify_outcome(stage_8, []) == gate.BLOCKER


class TestWhatTheRecordRefuses:
    @pytest.mark.parametrize(
        ("key", "value", "match"),
        [
            ("V3_CANDIDATE", True, "V3_CANDIDATE"),
            ("V3_PERSISTABLE", True, "V3_PERSISTABLE"),
            ("STAGE_10_MANUFACTURED", True, "STAGE_10_MANUFACTURED"),
            ("V3_HUMAN_REVIEW_PACKET", "PRODUCED", "human-review packet"),
            ("V3_APPROVAL_CONSUMED", False, "V3_APPROVAL_CONSUMED"),
            ("DIAGNOSTIC_ONLY", False, "DIAGNOSTIC_ONLY"),
            ("V3_HISTORICALLY_REJECTED", False, "V3_HISTORICALLY_REJECTED"),
            ("DIAGNOSTIC_GATE_V1_3_VERDICT", "PASSED", "DIAGNOSTIC_GATE_V1_3_VERDICT"),
            ("DIAGNOSTIC_OUTCOME", "DIAGNOSTIC_STAGES_6_TO_9_PASSED", "DIAGNOSTIC_OUTCOME"),
            ("EXECUTION_PACKET_V4", "READY_FOR_OPERATOR_APPROVAL", "EXECUTION_PACKET_V4"),
            ("V4_CREATION_CONDITION_MET", True, "V4_CREATION_CONDITION_MET"),
            (
                "HISTORICAL_V3_GATE_V1_1_REASONS_REPRODUCED",
                False,
                "HISTORICAL_V3_GATE_V1_1_REASONS_REPRODUCED",
            ),
            (
                "HISTORICAL_DIAGNOSTIC_GATE_V1_2_REASONS_REPRODUCED",
                False,
                "HISTORICAL_DIAGNOSTIC_GATE_V1_2_REASONS_REPRODUCED",
            ),
            ("FREEZE_COMMIT", "0" * 40, "freeze commit"),
            ("FREEZE_RECORD_SHA256", "0" * 64, "FREEZE_RECORD_SHA256"),
        ],
    )
    def test_a_moved_field_is_refused(
        self, fast, record, monkeypatch, tmp_path, key, value, match
    ) -> None:
        edited = json.loads(json.dumps(record))
        edited[key] = value
        _refused(fast, monkeypatch, tmp_path, edited, match)

    def test_a_softened_reason_list_is_refused(self, fast, record, monkeypatch, tmp_path) -> None:
        edited = json.loads(json.dumps(record))
        edited["DIAGNOSTIC_GATE_V1_3_REASONS"] = []
        _refused(fast, monkeypatch, tmp_path, edited, "DIAGNOSTIC_GATE_V1_3_REASONS")

    def test_a_hidden_proposition_is_refused(self, fast, record, monkeypatch, tmp_path) -> None:
        edited = json.loads(json.dumps(record))
        edited["UNSUPPORTED_PROPOSITIONS"] = []
        _refused(fast, monkeypatch, tmp_path, edited, "UNSUPPORTED_PROPOSITIONS")

    def test_a_manufactured_stage_is_refused(self, fast, record, monkeypatch, tmp_path) -> None:
        edited = json.loads(json.dumps(record))
        edited["DIAGNOSTIC_STAGES"]["7_evidence_boundary_and_no_distortion"] = "PASSED"
        _refused(fast, monkeypatch, tmp_path, edited, "DIAGNOSTIC_STAGES")

    def test_a_tampered_snapshot_is_refused(self, fast, record, monkeypatch, tmp_path) -> None:
        edited = json.loads(json.dumps(record))
        first = next(iter(edited["PACKET_SNAPSHOT"]["claim_statements"]))
        edited["PACKET_SNAPSHOT"]["claim_statements"][first] += " Tenders were observed."
        _refused(fast, monkeypatch, tmp_path, edited, "Mission 1.84.10 authenticated")

    def test_a_metadata_channel_the_registry_does_not_give_is_refused(
        self, fast, record, monkeypatch, tmp_path
    ) -> None:
        edited = json.loads(json.dumps(record))
        edited["SOURCE_METADATA_CONTEXT"]["labels"] = edited["SOURCE_METADATA_CONTEXT"]["labels"][
            :1
        ]
        _refused(fast, monkeypatch, tmp_path, edited, "SOURCE_METADATA_CONTEXT")

    def test_a_field_the_replay_does_not_derive_is_refused(
        self, fast, record, monkeypatch, tmp_path
    ) -> None:
        edited = json.loads(json.dumps(record))
        edited["V4_READY"] = True
        _refused(fast, monkeypatch, tmp_path, edited, "does not derive")

    def test_a_record_that_does_not_exist_is_refused(self, gate, monkeypatch, tmp_path) -> None:
        monkeypatch.setattr(gate, "RECORD", tmp_path / "absent.json")
        with pytest.raises(gate.ValidationError, match="does not exist"):
            gate.validate()

    def test_a_second_replay_is_refused(self, gate) -> None:
        with pytest.raises(gate.ValidationError, match="performed once"):
            gate.run_replay(gate.FREEZE_COMMIT)

    def test_a_replay_against_another_commit_is_refused(self, gate) -> None:
        with pytest.raises(gate.ValidationError, match="frozen commit"):
            gate.run_replay("f" * 40)

    def test_a_rewritten_1_84_10_record_is_refused(self, gate, monkeypatch) -> None:
        monkeypatch.setattr(gate, "REPLAY_V1_2_RECORD_SHA256", "b" * 64)
        with pytest.raises(gate.ValidationError, match="1.84.10's replay record"):
            gate.validate()

    def test_the_replay_constructs_no_transport(self, gate) -> None:
        from sros_llm_gateway.transport import UrllibTransport

        replay_v1_2 = gate._replay_v1_2()
        with replay_v1_2.no_transport(), pytest.raises(AssertionError, match="real transport"):
            UrllibTransport()
