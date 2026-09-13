"""Mission 1.84.17. CI gate 89: the V6 runner's stages 5 to 9, and every retention path, on synthetic answers.

The gate is run once and its record read; the refusals feed its own functions a runner source this file
changes, so no committed file is touched. Nothing here reaches a network.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
from typing import Any

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "infrastructure" / "scripts"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module(
        "gate_89_under_test", SCRIPTS / "render_second_opportunity_stage_6_9_preflight_v2.py"
    )


@pytest.fixture(scope="module")
def built(gate) -> dict[str, Any]:
    return gate.run()


@pytest.fixture(scope="module")
def source(gate) -> str:
    return gate.RUNNER_V6.read_text(encoding="utf-8")


class TestTheRecord:
    def test_the_committed_record_is_the_run(self, gate, built):
        assert json.loads(gate.RECORD.read_text(encoding="utf-8")) == json.loads(json.dumps(built))

    def test_the_path_is_ready_and_retention_too(self, built):
        assert built["OUTCOME"] == "DETERMINISTIC_STAGE_6_TO_9_PATH_READY"
        assert built["RETENTION_OUTCOME"] == "RETENTION_PATH_READY_FOR_NEXT_EXECUTION"

    def test_the_long_summary_cases(self, built):
        by_id = {f["fixture"]: f for f in built["FIXTURES"]}
        positive = by_id["F_LONG_SUMMARY_POSITIVE"]
        negative = by_id["G_LONG_SUMMARY_SEMANTIC_NEGATIVE"]
        bounds = built["SUMMARY_BOUNDS"]
        assert bounds["v1_1_0"] < positive["summary_characters"] <= bounds["v1_2_0"]
        assert positive["intended_stage"] == "NONE_ELIGIBLE_AT_9"
        assert positive["stages"]["9_persistence_eligibility"] == "ELIGIBLE_FOR_HUMAN_REVIEW_ONLY"
        assert negative["stages"]["5_schema_validation_v1_2_0"] == "PASSED"
        assert negative["failed_stage"] == "6_semantic_output_gate_v1_4_0"
        assert by_id["H_SUMMARY_AT_THE_NEW_BOUND"]["summary_characters"] == bounds["v1_2_0"]
        assert (
            by_id["I_SUMMARY_ONE_OVER_THE_NEW_BOUND"]["failed_stage"]
            == "5_schema_validation_v1_2_0"
        )

    def test_every_terminal_path_is_retained(self, built):
        assert set(built["RETENTION_PATHS"]) == {
            "success",
            "timeout",
            "provider_refusal",
            "provider_output_limit_max_tokens",
            "provider_output_limit_context_window",
            "unsupported_stop_reason",
            "parse_failure",
            "schema_failure",
            "semantic_failure",
            "evidence_boundary_failure",
            "provenance_failure",
            "persistence_eligibility_failure",
            "human_review_ready_success",
        }
        for path, row in built["RETENTION_PATHS"].items():
            assert row["persisted"] == "NOTHING"
            assert row["raw_response_retained"] is (path != "timeout")

    def test_a_record_that_disagrees_is_refused(self, gate, built, tmp_path, monkeypatch):
        record = json.loads(json.dumps(built))
        record["LONG_SUMMARY"]["POSITIVE_REACHES_STAGE_9"] = False
        path = tmp_path / gate.RECORD.name
        path.write_text(json.dumps(record), encoding="utf-8")
        monkeypatch.setattr(gate, "RECORD", path)
        monkeypatch.setattr(gate, "run", lambda: built)
        with pytest.raises(gate.ValidationError, match="derives"):
            gate.validate()


class TestTheRunnerStructure:
    def test_stage_5_must_read_schema_v1_2(self, gate, built, source):
        changed = source.replace(
            "schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)",
            "schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)",
        )
        assert changed != source
        with pytest.raises(gate.ValidationError, match="stage 5"):
            gate._structure(changed, built["STAGES"])

    def test_stage_6_must_be_gate_v1_4(self, gate, built, source):
        changed = source.replace(
            "evaluate_second_opportunity_output_v1_4(", "evaluate_second_opportunity_output_v1_3("
        )
        assert changed != source
        with pytest.raises(gate.ValidationError, match="stage 6"):
            gate._structure(changed, built["STAGES"])

    def test_a_runner_that_cannot_refuse_at_stage_9_is_refused(self, gate, built, source):
        changed = source.replace("STAGES[8],\n", "STAGES[7],\n")
        assert changed != source
        with pytest.raises(gate.ValidationError, match="refuses only"):
            gate._structure(changed, built["STAGES"])

    def test_the_live_runner_passes(self, gate, built, source):
        assert gate._structure(source, built["STAGES"])["REFUSES_AT"] == built["STAGES"][4:9]
