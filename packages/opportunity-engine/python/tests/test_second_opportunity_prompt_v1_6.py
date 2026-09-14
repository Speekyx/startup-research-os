"""Mission 1.84.23. Prompt v1.6.0 and CI gate 99: v1.5.0 plus the generation-surface block.

The module checks run over the synthetic fixture packet; the gate's refusals run its own functions over
inputs this file changes, so the committed artifacts are never touched. Nothing here reaches a network.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import pathlib
import re
from typing import Any

import pytest
from sros_opportunity import second_opportunity_prompt_v1_6 as prompt_module
from sros_opportunity.generation_surface_policy import (
    SURFACE_RULE_IDS,
    render_generation_surface_block,
)
from sros_opportunity.second_opportunity_prompt_v1_5 import (
    SECOND_OPPORTUNITY_SYSTEM_V1_5,
    render_second_opportunity_prompt_v1_5,
    second_opportunity_prompt_hash_v1_5,
)
from sros_opportunity.second_opportunity_prompt_v1_6 import (
    GENERATION_SURFACE_BLOCK_V1_6,
    PROMPT_V1_6_OUTPUT_SCHEMA_VERSION,
    PROMPT_V1_6_SEMANTIC_GATE_VERSION,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_6,
    SECOND_OPPORTUNITY_SYSTEM_V1_6,
    render_second_opportunity_prompt_v1_6,
    second_opportunity_prompt_hash_v1_6,
    unstated_constraints_in,
    unstated_headroom_in,
    unstated_semantic_rules_in,
    unstated_surface_rules_in,
)

ROOT = pathlib.Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "infrastructure" / "scripts"
GATE = SCRIPTS / "render_second_opportunity_prompt_v1_6.py"


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fx() -> Any:
    return _module(
        "fixtures_for_prompt_v1_6_tests", SCRIPTS / "second_opportunity_synthetic_fixtures.py"
    )


@pytest.fixture(scope="module")
def gate() -> Any:
    return _module("gate_99_under_test", GATE)


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
    v1_6 = _render(fx, render_second_opportunity_prompt_v1_6)
    return {
        "v1_5": _render(fx, render_second_opportunity_prompt_v1_5),
        "v1_6": v1_6,
        "synthetic": v1_6,
    }


@pytest.fixture(scope="module")
def record(gate: Any) -> dict[str, Any]:
    return gate.validate()


class TestTheComposition:
    def test_v1_5_s_system_region_is_a_byte_identical_prefix(self, both):
        assert str(both["v1_6"].system_instructions).startswith(SECOND_OPPORTUNITY_SYSTEM_V1_5)

    def test_only_the_surface_block_is_added(self):
        added = SECOND_OPPORTUNITY_SYSTEM_V1_6[len(SECOND_OPPORTUNITY_SYSTEM_V1_5) :]
        assert added == "\n" + render_generation_surface_block() + "\n"
        assert render_generation_surface_block() == GENERATION_SURFACE_BLOCK_V1_6

    def test_the_other_regions_are_byte_identical(self, both):
        for region in ("trusted_context", "untrusted", "task"):
            assert getattr(both["v1_5"], region) == getattr(both["v1_6"], region)
        assert "SOURCE NAMES" in both["v1_6"].trusted_context

    def test_nothing_is_left_unstated(self, both):
        parts = both["v1_6"]
        assert unstated_constraints_in(parts) == []
        assert unstated_semantic_rules_in(parts) == []
        assert unstated_headroom_in(parts) == []
        assert unstated_surface_rules_in(parts) == []

    def test_the_surface_census_catches_prompt_v1_5(self, both):
        assert unstated_surface_rules_in(both["v1_5"]) == list(SURFACE_RULE_IDS)

    def test_the_module_writes_no_number(self):
        tree = ast.parse(inspect.getsource(prompt_module))
        assert [
            n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and type(n.value) is int
        ] == []

    def test_the_digest_binds_the_surface_policy(self, both, monkeypatch):
        parts = both["v1_6"]
        live = second_opportunity_prompt_hash_v1_6(parts)
        assert live != second_opportunity_prompt_hash_v1_5(both["v1_5"])
        monkeypatch.setattr(prompt_module, "GENERATION_SURFACE_POLICY_VERSION", "another@9.9.9")
        assert second_opportunity_prompt_hash_v1_6(parts) != live

    def test_the_identities(self):
        assert SECOND_OPPORTUNITY_PROMPT_VERSION_V1_6 == "1.6.0"
        assert PROMPT_V1_6_OUTPUT_SCHEMA_VERSION == "second-opportunity-synthesis-output@1.2.0"
        assert PROMPT_V1_6_SEMANTIC_GATE_VERSION == "second-opportunity-output-gate@1.4.0"

    def test_the_system_region_names_no_gate_and_no_execution(self):
        assert "output-gate@" not in SECOND_OPPORTUNITY_SYSTEM_V1_6
        assert not re.search(r"\bV[1-9]\b", SECOND_OPPORTUNITY_SYSTEM_V1_6)

    def test_prompt_v1_5_is_the_merged_file(self, gate):
        relative = (
            "packages/opportunity-engine/python/sros_opportunity/second_opportunity_prompt_v1_5.py"
        )
        assert gate.file_sha(relative) == gate.HISTORY_SHA256[relative]


class TestGate99:
    def test_the_record_is_the_rebuild(self, record):
        v9 = record["V9_RECONFIRMATION"]
        assert v9["SEMANTIC_REFUSALS"] == 7
        assert (
            v9["FAMILIES"]["GENUINE_OUTPUT_SUPPORT_FAILURE_UNDER_CURRENT_POLICY"]["refusals"] == 1
        )
        assert v9["FAMILIES"]["GENERATION_SURFACE_FORM_MISALIGNMENT"]["refusals"] == 6
        assert v9["V9_WOULD_HAVE_PASSED_CLAIMED"] is False
        assert record["DIFFERENTIAL"]["PROMPT_V1_6_HAS_UNAPPROVED_DRIFT"] is False
        assert record["CENSUS"]["UNSTATED_GENERATION_SURFACE_RULES"] == 0
        assert record["CONFORMANCE"]["GATE_BEHAVIOR_CHANGED"] is False
        assert record["CONFORMANCE"]["CASES_AS_THE_POLICY_SAYS"] == 9
        assert record["SEMANTIC_GATE_IMPLEMENTATION_SHA256"] == gate_digest()
        assert set(record["accounting"].values()) == {0}

    def test_a_line_added_outside_the_block_is_refused(self, gate, both):
        parts = dict(both)
        parts["v1_6"] = _with_system(
            parts["v1_6"], str(parts["v1_6"].system_instructions) + "More.\n"
        )
        with pytest.raises(gate.ValidationError, match="PROMPT_V1_6_HAS_UNAPPROVED_DRIFT"):
            gate.prompt_differential(parts)

    def test_a_moved_v1_5_line_is_refused(self, gate, both):
        parts = dict(both)
        system = str(parts["v1_6"].system_instructions)
        parts["v1_6"] = _with_system(
            parts["v1_6"], system.replace("USE ONLY THE SUPPLIED", "USE THE SUPPLIED", 1)
        )
        with pytest.raises(gate.ValidationError, match="byte-identical prefix"):
            gate.prompt_differential(parts)

    def test_a_moved_trusted_context_is_refused(self, gate, both):
        parts = dict(both)
        v16 = parts["v1_6"]
        parts["v1_6"] = type(v16)(
            system_instructions=v16.system_instructions,
            trusted_context=v16.trusted_context + " An extra sentence.",
            untrusted=v16.untrusted,
            task=v16.task,
            metadata=v16.metadata,
        )
        with pytest.raises(gate.ValidationError, match="trusted_context"):
            gate.prompt_differential(parts)

    def test_a_surface_census_that_would_pass_v1_5_is_refused(self, gate, both, monkeypatch):
        monkeypatch.setattr(prompt_module, "unstated_surface_rules", lambda system: [])
        with pytest.raises(gate.ValidationError, match="do not catch prompt v1.5.0"):
            gate.prompt_checks(dict(both))

    def test_a_moved_gate_stops_the_mission(self, gate, monkeypatch):
        monkeypatch.setattr(gate, "GATE_V1_4_IMPLEMENTATION_SHA256", "0" * 64)
        with pytest.raises(
            gate.ValidationError, match="PROMPT_SUCCESSOR_WOULD_MODIFY_FROZEN_SEMANTIC_GATE"
        ):
            gate.gate_v1_4_digest()

    def test_a_case_the_gate_judges_otherwise_is_refused(self, gate):
        flipped = dict(gate.CONFORMANCE_CASES[1], persist=True, reason=None)
        with pytest.raises(gate.ValidationError, match="the frozen gate judged it"):
            gate.conformance([flipped])

    def test_a_refusal_outside_the_two_families_is_refused(self, gate):
        with pytest.raises(gate.ValidationError, match="neither family"):
            gate.family_of({"field": "recommended_next_evidence[0]", "kind": "UNSUPPORTED_TERM"})

    def test_a_refused_sentence_in_the_prompt_is_refused(self, gate, both):
        parts = dict(both)
        system = str(parts["v1_6"].system_instructions) + "An imagined refused sentence.\n"
        parts["v1_6"] = _with_system(parts["v1_6"], system)
        with pytest.raises(gate.ValidationError, match="sentence"):
            gate.exposure(parts, ["An imagined refused sentence."])

    def test_a_moved_historical_artifact_is_refused(self, gate, monkeypatch):
        pinned = dict(gate.HISTORY_SHA256)
        pinned[next(iter(pinned))] = "0" * 64
        monkeypatch.setattr(gate, "HISTORY_SHA256", pinned)
        with pytest.raises(gate.ValidationError, match="merged"):
            gate.history()

    def test_the_gate_carries_no_request(self):
        source = GATE.read_text(encoding="utf-8")
        assert "count_tokens" not in source
        assert "urlopen" not in source and "import urllib" not in source


def gate_digest() -> str:
    gate_87 = _module(
        "gate_87_for_prompt_v1_6_tests", SCRIPTS / "render_second_opportunity_semantic_gate_v1_4.py"
    )
    return str(gate_87.implementation_sha256())
