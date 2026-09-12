"""Mission 1.84.10. CI gate 76: V3's answer replayed diagnostically through the frozen gate v1.2.0.

The replay ran once, after the freeze. These tests defend the record it wrote and state, as facts,
what it found: the five historical refusals no longer fire, and ONE new refusal does, which is a
defect of the frozen gate rather than of the answer. Nothing here repairs it: a gate tuned after
seeing how V3 fares is tuned on V3, and the brief stops the mission at the first blocker.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re

import pytest
from sros_opportunity.assertion_context import (
    Disposition,
    Shape,
    TrustedContext,
    audit_text,
    build_support_universe,
)
from sros_opportunity.second_opportunity import PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS
from sros_opportunity.second_opportunity_gate_v1_2 import FORBIDDEN_CONCEPTS_V1_2

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE_PATH = (
    REPO_ROOT / "infrastructure" / "scripts" / "render_second_opportunity_v3_diagnostic_replay.py"
)


def _module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate():
    return _module("v3_diagnostic_replay_under_test", GATE_PATH)


@pytest.fixture(scope="module")
def record(gate) -> dict:
    return json.loads(gate.RECORD.read_text(encoding="utf-8"))


def _refused(gate, monkeypatch, tmp_path, record: dict, match: str) -> None:
    copy = tmp_path / gate.RECORD.name
    copy.write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(gate, "RECORD", copy)
    with pytest.raises(gate.ValidationError, match=match):
        gate.validate()


class TestTheReplayRecord:
    def test_it_re_derives(self, gate) -> None:
        assert gate.validate()["DIAGNOSTIC_ONLY"] is True

    def test_the_page_is_current(self, gate) -> None:
        assert gate.RECORD_MD.read_text(encoding="utf-8") == gate.render(gate.validate())

    def test_it_names_the_freeze_it_ran_after(self, gate, record) -> None:
        assert record["FREEZE_COMMIT"] == gate.FREEZE_COMMIT
        assert record["GATE_V1_2_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY"] is True
        ordering = gate.git_ordering()
        if ordering["state"] == "CHECKED":
            assert all(v is True for k, v in ordering.items() if k != "state"), ordering

    def test_v3_is_reconfirmed_as_it_happened(self, record) -> None:
        facts = record["V3_FACTS"]
        assert facts["actual_provider_requests"] == 1
        assert facts["actual_model_calls"] == 1
        assert facts["retries"] == facts["continuation_requests"] == facts["repair_calls"] == 0
        assert (facts["input_tokens"], facts["output_tokens"], facts["thinking_tokens"]) == (
            9491,
            3880,
            0,
        )
        assert facts["cost_units"] == 0.057782
        assert facts["STOP_REASON"] == "tool_use"
        assert facts["EXECUTION_APPROVAL_CONSUMED"] is True
        assert record["HISTORICAL_V3_GATE_V1_1_VERDICT"] == "FAILED"
        assert record["HISTORICAL_REASONS_REPRODUCED"] is True
        assert record["HISTORICAL_REASON_COUNT"] == 5

    def test_v3_stays_what_it_was(self, record) -> None:
        assert record["V3_HISTORICALLY_REJECTED"] is True
        assert record["V3_CANDIDATE"] is False
        assert record["V3_PERSISTABLE"] is False
        assert record["V3_HUMAN_REVIEW_PACKET"] == "NOT_PRODUCED"
        assert record["STAGE_10_MANUFACTURED"] is False
        assert record["DIAGNOSTIC_STAGES"]["10_human_review"] == "NOT_MANUFACTURED_DIAGNOSTIC_ONLY"
        assert set(record["accounting"].values()) == {0}

    def test_the_snapshot_is_v3s_packet(self, record) -> None:
        auth = record["SNAPSHOT_AUTHENTICATION"]
        assert auth["representation_sha256"].startswith("2528a56a")
        assert auth["prompt_sha256"].startswith("1677cbe5")


class TestWhatTheReplayFound:
    """Recorded as facts. The frozen gate is not touched on the strength of them."""

    def test_the_five_historical_refusals_no_longer_fire(self, record) -> None:
        verdicts = {a["field"]: a["verdict"] for a in record["DIAGNOSTIC_AUDIT"]}
        assert verdicts["reliability_status"] == "SUPPORTED"
        assert verdicts["evidence_bound_reasoning_summary"] == "SUPPORTED"
        reasons = " ".join(record["DIAGNOSTIC_GATE_V1_2_REASONS"])
        for historical in ("SCORED", "161", "'market'", "actual expenditure", "willing"):
            assert historical not in reasons, historical

    def test_one_new_refusal_stops_stage_6(self, record) -> None:
        assert record["DIAGNOSTIC_GATE_V1_2_VERDICT"] == "FAILED"
        assert record["DIAGNOSTIC_FAILED_STAGE"] == "6_semantic_output_gate_v1_2_0"
        assert record["DIAGNOSTIC_OUTCOME"] == "V3_DIAGNOSTIC_REVEALED_NEXT_EXECUTION_BLOCKER"
        (reason,) = record["DIAGNOSTIC_GATE_V1_2_REASONS"]
        assert reason.startswith("statement_classifications[7].statement audited UNSUPPORTED")
        assert "'tender'" in reason
        failed = [a for a in record["DIAGNOSTIC_AUDIT"] if a["verdict"] != "SUPPORTED"]
        assert [
            a["field"] for a in failed if a["verdict"] in ("UNSUPPORTED", "BOUND_EXCEEDED")
        ] == ["statement_classifications[7].statement"]

    def test_the_refused_word_is_supplied_in_its_other_grammatical_number(self, record) -> None:
        """The finding says 'tender' appears in no supplied statement. The statements carry
        'Tenders': the audit folds a plural on the answer's side and compares the licence
        exactly, so its own sentence is false. A defect of gate v1.2.0, found by the replay."""
        supplied = " ".join(record["PACKET_SNAPSHOT"]["claim_statements"].values()).lower()
        tokens = set(re.findall(r"[a-z0-9]+", supplied))
        assert "tenders" in tokens
        assert "tender" not in tokens

    def test_the_defect_is_general_and_not_v3s(self) -> None:
        """The same refusal on a synthetic packet: any supplied plural refuses its singular."""
        from sros_opportunity import (
            EvidenceFacets,
            IndependenceState,
            PacketEligibility,
            ReliabilityStatus,
            build_packet,
        )
        from sros_opportunity.mapping import SIGNAL_DIMENSION_MAP

        mapping = SIGNAL_DIMENSION_MAP["procurement_value_contrast"]
        facets = EvidenceFacets(
            evidence_id="11111111-1111-4111-8111-111111111111",
            claim_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            source_id="ted-eu",
            source_family="public_procurement",
            use_profile_id="local-private-research-v1",
            extraction_method="deterministic",
            claim_type="OBSERVED",
            claim_lifecycle="ACTIVE",
            claim_temporality="EVERGREEN",
            claim_origin="DETERMINISTIC_EXTRACTION",
            direction="SUPPORTS",
            observation_category="UNCATEGORISED",
            evidence_level=1,
            relevance=1.0,
            directness=1.0,
            extraction_confidence=1.0,
            reliability=0.5,
            reliability_status=ReliabilityStatus.RESOLVED,
            independence_state=IndependenceState.UNKNOWN,
            independence_group_id=None,
            observed_at=None,
            signal_type_id="procurement_value_contrast",
            dimensions=mapping.dimensions,
            dimension_bound=mapping.bound,
        )
        packet = build_packet(None, "synthetic", ((facets, PacketEligibility.ELIGIBLE_SCORING),))
        universe = build_support_universe(
            packet,
            {facets.claim_id: "Suppliers published notices listing their tenders."},
            TrustedContext(version="synthetic", facts=()),
        )
        _verdict, findings = audit_text(
            "A tender was published.",
            Disposition.SUPPORTED_ASSERTION,
            Shape.FREE,
            universe,
            FORBIDDEN_CONCEPTS_V1_2,
            PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
            frozenset(packet.counting_dimensions),
        )
        assert any("'tender' appears in no supplied statement" in f for f in findings)


class TestWhatTheRecordRefuses:
    @pytest.mark.parametrize(
        ("key", "value", "match"),
        [
            ("V3_CANDIDATE", True, "V3_CANDIDATE"),
            ("V3_PERSISTABLE", True, "V3_PERSISTABLE"),
            ("STAGE_10_MANUFACTURED", True, "STAGE_10_MANUFACTURED"),
            ("V3_HUMAN_REVIEW_PACKET", "PRODUCED", "human-review packet"),
            ("DIAGNOSTIC_ONLY", False, "DIAGNOSTIC_ONLY"),
            ("V3_HISTORICALLY_REJECTED", False, "V3_HISTORICALLY_REJECTED"),
            ("DIAGNOSTIC_GATE_V1_2_VERDICT", "PASSED", "DIAGNOSTIC_GATE_V1_2_VERDICT"),
            ("DIAGNOSTIC_OUTCOME", "DIAGNOSTIC_STAGES_6_TO_9_PASSED", "DIAGNOSTIC_OUTCOME"),
            ("HISTORICAL_REASONS_REPRODUCED", False, "HISTORICAL_REASONS_REPRODUCED"),
            ("FREEZE_COMMIT", "0" * 40, "freeze commit"),
            ("FREEZE_RECORD_SHA256", "0" * 64, "FREEZE_RECORD_SHA256"),
        ],
    )
    def test_a_moved_field_is_refused(
        self, gate, record, monkeypatch, tmp_path, key, value, match
    ) -> None:
        edited = json.loads(json.dumps(record))
        edited[key] = value
        _refused(gate, monkeypatch, tmp_path, edited, match)

    def test_a_softened_reason_list_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        edited = json.loads(json.dumps(record))
        edited["DIAGNOSTIC_GATE_V1_2_REASONS"] = []
        _refused(gate, monkeypatch, tmp_path, edited, "DIAGNOSTIC_GATE_V1_2_REASONS")

    def test_a_manufactured_stage_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        edited = json.loads(json.dumps(record))
        edited["DIAGNOSTIC_STAGES"]["9_persistence_eligibility"] = "PASSED"
        _refused(gate, monkeypatch, tmp_path, edited, "DIAGNOSTIC_STAGES")

    def test_a_tampered_snapshot_is_refused(self, gate, record, monkeypatch, tmp_path) -> None:
        edited = json.loads(json.dumps(record))
        first = next(iter(edited["PACKET_SNAPSHOT"]["claim_statements"]))
        edited["PACKET_SNAPSHOT"]["claim_statements"][first] += " Buyers are willing to pay."
        _refused(gate, monkeypatch, tmp_path, edited, "not the packet")

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

    def test_a_moved_v3_artifact_is_refused(self, gate, monkeypatch) -> None:
        pinned = dict(gate.V3_ARTIFACTS_SHA256)
        pinned[next(iter(pinned))] = "a" * 64
        monkeypatch.setattr(gate, "V3_ARTIFACTS_SHA256", pinned)
        with pytest.raises(gate.ValidationError, match="Mission 1.84.9 committed"):
            gate.validate()

    def test_the_replay_constructs_no_transport(self, gate) -> None:
        from sros_llm_gateway.transport import UrllibTransport

        with gate.no_transport(), pytest.raises(AssertionError, match="real transport"):
            UrllibTransport()
