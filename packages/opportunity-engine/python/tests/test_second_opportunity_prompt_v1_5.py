"""Mission 1.84.17. Prompt v1.5.0 and CI gate 88: v1.4.0 rebound to schema v1.2.0, and the capacity under it.

The module checks run over the synthetic fixture packet; the gate's refusals run its own functions over
inputs this file changes, so the committed artifacts are never touched. Nothing here reaches a network.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import inspect
import json
import pathlib
import re
from typing import Any

import pytest
from sros_opportunity import second_opportunity_prompt_v1_5 as prompt_module
from sros_opportunity import second_opportunity_schema_v1_2 as schema_module
from sros_opportunity.generation_headroom import generation_target
from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
from sros_opportunity.second_opportunity_prompt_v1_3 import SEMANTIC_GENERATION_RULES_BLOCK_V1_3
from sros_opportunity.second_opportunity_prompt_v1_4 import (
    render_second_opportunity_prompt_v1_4,
    second_opportunity_prompt_hash_v1_4,
)
from sros_opportunity.second_opportunity_prompt_v1_5 import (
    PROMPT_V1_5_OUTPUT_SCHEMA_VERSION,
    PROMPT_V1_5_SEMANTIC_GATE_VERSION,
    SECOND_OPPORTUNITY_SYSTEM_V1_5,
    SEMANTIC_GENERATION_RULES_BLOCK_V1_5,
    render_second_opportunity_prompt_v1_5,
    second_opportunity_prompt_hash_v1_5,
    unstated_constraints_in,
    unstated_headroom_in,
    unstated_semantic_rules_in,
)
from sros_opportunity.second_opportunity_schema_v1_2 import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2

ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "infrastructure" / "scripts"
SUMMARY = "evidence_bound_reasoning_summary"
OLD = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][SUMMARY]["maxLength"]
NEW = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2["properties"][SUMMARY]["maxLength"]


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fx() -> Any:
    return _module(
        "fixtures_for_prompt_v1_5_tests", SCRIPTS / "second_opportunity_synthetic_fixtures.py"
    )


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module("gate_88_under_test", SCRIPTS / "render_second_opportunity_prompt_v1_5.py")


def _render(fx: Any, render: Any) -> Any:
    return render(fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata())


def _with_system(parts: Any, system: str) -> Any:
    return type(parts)(
        system_instructions=system,
        trusted_context=parts.trusted_context,
        untrusted=parts.untrusted,
        task=parts.task,
        metadata=parts.metadata,
    )


@pytest.fixture(scope="module")
def both(fx: Any) -> dict[str, Any]:
    return {
        "v1_4": _render(fx, render_second_opportunity_prompt_v1_4),
        "v1_5": _render(fx, render_second_opportunity_prompt_v1_5),
        "synthetic": _render(fx, render_second_opportunity_prompt_v1_5),
    }


class TestTheComposition:
    def test_exactly_two_system_lines_move_and_only_in_their_number(self, both):
        a = str(both["v1_4"].system_instructions).split("\n")
        b = str(both["v1_5"].system_instructions).split("\n")
        assert len(a) == len(b)
        moved = [(x, y) for x, y in zip(a, b, strict=True) if x != y]
        assert len(moved) == 2
        for before, after in moved:
            assert re.sub(r"\d+", "#", before) == re.sub(r"\d+", "#", after)
            assert set(re.findall(r"\d+", before)) <= {str(OLD), str(generation_target(OLD))}
            assert set(re.findall(r"\d+", after)) <= {str(NEW), str(generation_target(NEW))}

    def test_the_other_regions_are_byte_identical(self, both):
        for region in ("trusted_context", "untrusted", "task"):
            assert getattr(both["v1_4"], region) == getattr(both["v1_5"], region)
        assert "SOURCE NAMES" in both["v1_5"].trusted_context

    def test_the_semantic_block_is_gate_v1_3_s_census_as_rendered(self):
        assert SEMANTIC_GENERATION_RULES_BLOCK_V1_5 is SEMANTIC_GENERATION_RULES_BLOCK_V1_3
        assert "\n" + SEMANTIC_GENERATION_RULES_BLOCK_V1_3 + "\n" in SECOND_OPPORTUNITY_SYSTEM_V1_5

    def test_nothing_is_left_unstated(self, both):
        parts = both["v1_5"]
        assert unstated_constraints_in(parts) == []
        assert unstated_semantic_rules_in(parts) == []
        assert unstated_headroom_in(parts) == []

    def test_the_checks_catch_prompt_v1_4_under_schema_v1_2(self, both):
        assert unstated_constraints_in(both["v1_4"]) == [f"{SUMMARY} maxLength"]
        assert unstated_headroom_in(both["v1_4"]) == [SUMMARY]

    def test_the_module_writes_no_number(self):
        tree = ast.parse(inspect.getsource(prompt_module))
        assert [
            n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and type(n.value) is int
        ] == []

    def test_the_old_bound_occurs_nowhere_in_the_regions(self, both):
        parts = both["v1_5"]
        texts = [str(parts.system_instructions), str(parts.trusted_context), str(parts.task)]
        texts += [str(value) for pair in parts.untrusted for value in pair]
        for text in texts:
            assert not re.search(rf"\b({OLD}|{generation_target(OLD)})\b", text)

    def test_the_new_bound_and_target_are_stated_side_by_side(self):
        line = f"  {SUMMARY}: generation target {generation_target(NEW)} characters; hard maximum {NEW} characters"
        assert line in SECOND_OPPORTUNITY_SYSTEM_V1_5.split("\n")

    def test_the_system_region_names_no_gate_and_no_execution(self):
        assert "output-gate@" not in SECOND_OPPORTUNITY_SYSTEM_V1_5
        assert not re.search(r"\bV[1-6]\b", SECOND_OPPORTUNITY_SYSTEM_V1_5)

    def test_the_digest_binds_the_schema_and_the_gate(self, both, monkeypatch):
        parts = both["v1_5"]
        live = second_opportunity_prompt_hash_v1_5(parts)
        assert live != second_opportunity_prompt_hash_v1_4(both["v1_4"])
        monkeypatch.setattr(
            prompt_module, "PROMPT_V1_5_SEMANTIC_GATE_VERSION", "another-gate@9.9.9"
        )
        assert second_opportunity_prompt_hash_v1_5(parts) != live

    def test_the_identities_are_schema_v1_2_and_gate_v1_4(self):
        assert PROMPT_V1_5_OUTPUT_SCHEMA_VERSION == "second-opportunity-synthesis-output@1.2.0"
        assert PROMPT_V1_5_SEMANTIC_GATE_VERSION == "second-opportunity-output-gate@1.4.0"


class TestGate88:
    def test_the_records_are_the_rebuild(self, gate):
        prompt, capacity = gate.validate()
        assert prompt["DIFFERENTIAL"]["SYSTEM_LINES_ADDED"] == 0
        assert len(prompt["DIFFERENTIAL"]["SYSTEM_LINES_MOVED"]) == 2
        assert capacity["FINITE_BOUND"] is True
        assert capacity["REACHABILITY"]["CONTRACT_FULL_DOMAIN_REACHABLE"] is False
        assert capacity["HEADROOM"]["OTHER_HEADROOM_ROW_DRIFT"] == 0
        assert capacity["PERSISTENCE"]["PERSISTENCE_COMPATIBILITY"] == "COMPATIBLE"
        assert capacity["accounting"]["TOKEN_COUNT_API_REQUESTS"] == 0

    def test_the_maximum_moves_by_what_the_one_bound_explains(self, gate):
        block = gate.capacity_block()
        delta = block["DELTA_FROM_V1_1_0"]["characters"]
        assert delta == (NEW - OLD) * 12
        assert [row["field"] for row in block["FIELD_CONTRIBUTIONS"] if row["delta"]] == [SUMMARY]
        assert block["PREDECESSOR_MAXIMUM_VALID_INSTANCE"]["MAX_VALID_OUTPUT_CHARACTERS"] == 309729

    def test_a_third_moved_line_is_refused(self, gate, both):
        parts = dict(both)
        system = str(parts["v1_5"].system_instructions)
        parts["v1_5"] = _with_system(
            parts["v1_5"], system.replace("USE ONLY THE SUPPLIED", "USE THE SUPPLIED", 1)
        )
        with pytest.raises(gate.ValidationError):
            gate.prompt_differential(parts)

    def test_a_bound_moved_to_another_number_is_refused(self, gate, both):
        parts = dict(both)
        system = str(parts["v1_5"].system_instructions)
        parts["v1_5"] = _with_system(
            parts["v1_5"], system.replace(f"at most {NEW} characters", "at most 1400 characters", 1)
        )
        with pytest.raises(gate.ValidationError, match="numbers other than the summary"):
            gate.prompt_differential(parts)

    def test_a_moved_trusted_context_is_refused(self, gate, both):
        parts = dict(both)
        v15 = parts["v1_5"]
        parts["v1_5"] = type(v15)(
            system_instructions=v15.system_instructions,
            trusted_context=v15.trusted_context + " An extra sentence.",
            untrusted=v15.untrusted,
            task=v15.task,
            metadata=v15.metadata,
        )
        with pytest.raises(gate.ValidationError, match="trusted_context"):
            gate.prompt_differential(parts)

    def test_checks_that_would_pass_prompt_v1_4_are_refused(self, gate, both, monkeypatch):
        monkeypatch.setattr(prompt_module, "unstated_headroom", lambda system, schema: [])
        with pytest.raises(gate.ValidationError):
            gate.prompt_checks(dict(both))

    def test_a_headroom_row_other_than_the_summary_is_refused(self, gate, monkeypatch):
        schema = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
        schema["properties"]["candidate_intervention_class"]["maxLength"] = 350
        monkeypatch.setattr(schema_module, "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2", schema)
        with pytest.raises(gate.ValidationError, match="OTHER_HEADROOM_ROW_DRIFT"):
            gate.headroom_block()

    def test_a_maximum_moved_by_another_field_is_refused(self, gate, monkeypatch):
        schema = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
        schema["properties"]["observed_need"]["maxLength"] = 600
        monkeypatch.setattr(schema_module, "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2", schema)
        with pytest.raises(gate.ValidationError, match="other than the summary"):
            gate.capacity_block()

    def test_an_estimate_inside_the_envelope_is_refused(self, gate, tmp_path, monkeypatch):
        measurement = json.loads(gate.TOKEN_MEASUREMENT.read_text(encoding="utf-8"))
        measurement["MEASUREMENT"]["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"] = 100000
        path = tmp_path / gate.TOKEN_MEASUREMENT.name
        path.write_text(json.dumps(measurement), encoding="utf-8")
        monkeypatch.setattr(gate, "TOKEN_MEASUREMENT", path)
        with pytest.raises(gate.ValidationError, match="envelope"):
            gate.reachability_block(gate.capacity_block())

    def test_a_moved_catalog_is_refused(self, gate, monkeypatch):
        monkeypatch.setitem(gate.OBSERVED_DATABASE, "existing_longest_value_characters", 1600)
        with pytest.raises(gate.ValidationError, match="PERSISTENCE_COMPATIBILITY_CHANGED"):
            gate.persistence_block()

    def test_a_moved_historical_artifact_is_refused(self, gate, monkeypatch):
        pinned = dict(gate.HISTORY_SHA256)
        first = next(iter(pinned))
        pinned[first] = "0" * 64
        monkeypatch.setattr(gate, "HISTORY_SHA256", pinned)
        with pytest.raises(gate.ValidationError, match="merged"):
            gate.history()

    def test_the_gate_carries_no_token_request(self, gate):
        source = (SCRIPTS / "render_second_opportunity_prompt_v1_5.py").read_text(encoding="utf-8")
        assert "count_tokens" not in source
        assert "urllib" not in source and "requests" not in source.split("TOKEN_COUNT")[0]
