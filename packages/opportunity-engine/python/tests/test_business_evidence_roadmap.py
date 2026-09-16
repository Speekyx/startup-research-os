"""Mission 1.85.0. The business-evidence acquisition roadmap agrees with the repository.

The roadmap is a plan, and a plan that names a source the catalog does not hold, a dimension the
taxonomy does not define, or a dependency that does not exist would send the next mission to build
on a fact nobody can find. These checks keep it honest and nothing more: they do not grant, rank or
score anything.

One check is deliberately a staleness alarm rather than a permanent assertion. When a signal type
starts mapping to a dimension the roadmap records as NOT_SUPPORTED, the coverage table is out of
date and the roadmap must be revised, not this test.
"""

from __future__ import annotations

import json
import pathlib

import pytest
from sros_opportunity import EvidenceDimension
from sros_opportunity.mapping import SIGNAL_DIMENSION_MAP

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
ROADMAP = json.loads((DOCS / "business-evidence-acquisition-roadmap-v1.json").read_text("utf-8"))
CATALOG = json.loads((DOCS / "source-catalog-v1.json").read_text("utf-8"))
SOURCE_IDS = {s["source_id"] for s in CATALOG["sources"]}
DIMENSION_NAMES = {d.value for d in EvidenceDimension}
MAPPED = {d.value for m in SIGNAL_DIMENSION_MAP.values() for d in m.dimensions}
NODES = {n["id"]: n for n in ROADMAP["nodes"]}


def _ancestors(node_id: str) -> set[str]:
    seen: set[str] = set()
    stack = list(NODES[node_id]["depends_on"])
    while stack:
        current = stack.pop()
        if current not in seen:
            seen.add(current)
            stack.extend(NODES[current]["depends_on"])
    return seen


class TestIdentity:
    def test_version_and_mission(self) -> None:
        assert ROADMAP["roadmap_version"] == "business-evidence-acquisition-roadmap@1.0.0"
        assert ROADMAP["mission"] == "mission-1.85.0"

    def test_the_operator_decision_on_ted_is_carried(self) -> None:
        decisions = " ".join(ROADMAP["operator_decisions_in_force"])
        assert "NO further synthesis on the current TED packet" in decisions
        assert "NO V11" in decisions and "NO Opportunity #2" in decisions


class TestCoverage:
    def test_every_named_evidence_dimension_exists(self) -> None:
        for row in ROADMAP["business_dimensions"]:
            if row["evidence_dimension"] is not None:
                assert row["evidence_dimension"] in DIMENSION_NAMES, row["id"]

    def test_states_and_holders_are_known(self) -> None:
        for row in ROADMAP["business_dimensions"]:
            assert row["coverage"] in ROADMAP["coverage_states"], row["id"]
            assert set(row["held_by"]) <= SOURCE_IDS, row["id"]
            assert bool(row["held_by"]) == (row["coverage"] != "NOT_SUPPORTED"), row["id"]

    def test_a_supported_dimension_is_one_a_signal_type_maps_to(self) -> None:
        for row in ROADMAP["business_dimensions"]:
            if row["coverage"] == "SUPPORTED_TODAY":
                assert row["evidence_dimension"] in MAPPED, row["id"]

    @pytest.mark.parametrize(
        "dimension",
        ["SOLUTION_DISSATISFACTION", "SOLUTION_GAP", "RECURRENCE_OR_FREQUENCY",
         "WILLINGNESS_TO_PAY", "COMPETITIVE_SUPPLY"],
    )  # fmt: skip
    def test_staleness_alarm_for_dimensions_recorded_as_missing(self, dimension: str) -> None:
        assert dimension not in MAPPED, (
            f"a signal type now maps to {dimension}; revise the roadmap's coverage table"
        )

    def test_the_brief_asks_about_twenty_dimensions(self) -> None:
        assert len({row["id"] for row in ROADMAP["business_dimensions"]}) == 20


class TestSources:
    def test_registered_sources_exist_in_the_catalog(self) -> None:
        for family in ROADMAP["source_families"]:
            assert set(family["registered_sources"]) <= SOURCE_IDS, family["id"]

    def test_family_dimensions_are_roadmap_dimensions(self) -> None:
        ids = {row["id"] for row in ROADMAP["business_dimensions"]}
        for family in ROADMAP["source_families"]:
            named = set(family["dimensions_strong"]) | set(family["dimensions_weak"])
            assert named <= ids, family["id"]
            assert not set(family["dimensions_strong"]) & set(family["dimensions_weak"])
            assert set(family["requires_semantic_extraction_for"]) <= named, family["id"]

    def test_the_recommendation_names_families_and_real_dimensions(self) -> None:
        recommendation = ROADMAP["first_source_recommendation"]
        families = {f["id"] for f in ROADMAP["source_families"]}
        assert set(recommendation["families"]) <= families
        assert {n["family"] for n in recommendation["not_first"]} <= families
        for unlocked in recommendation["unlocks_first"]:
            assert unlocked.split(" ")[0] in DIMENSION_NAMES

    def test_market_activity_sources_are_not_recommended_first(self) -> None:
        not_first = {n["family"] for n in ROADMAP["first_source_recommendation"]["not_first"]}
        assert {"F-PROCUREMENT", "F-STATISTICS-TRENDS"} <= not_first


class TestDependencies:
    def test_node_ids_are_unique_and_dependencies_exist(self) -> None:
        assert len(NODES) == len(ROADMAP["nodes"])
        for node in ROADMAP["nodes"]:
            assert set(node["depends_on"]) <= set(NODES), node["id"]

    def test_the_graph_is_acyclic(self) -> None:
        for node_id in NODES:
            assert node_id not in _ancestors(node_id)

    @pytest.mark.parametrize(
        "path",
        [ROADMAP["critical_path"], *(b["path"] for b in ROADMAP["critical_branches"])],
    )
    def test_each_path_step_depends_on_the_previous(self, path: list[str]) -> None:
        for earlier, later in zip(path, path[1:], strict=False):
            assert earlier in _ancestors(later), (earlier, later)

    def test_the_critical_path_ends_in_selection_and_starts_unblocked(self) -> None:
        path = ROADMAP["critical_path"]
        assert NODES[path[-1]]["kind"] == "SELECTION"
        assert NODES[path[0]]["depends_on"] == []
        assert NODES[path[0]]["mission"] == "1.85.1"

    def test_selection_depends_on_calibration_and_independence(self) -> None:
        assert {"N11", "N14"} <= _ancestors("N15")


class TestScoringAndIndependence:
    def test_no_component_is_ready(self) -> None:
        allowed = set(ROADMAP["scoring_status_values"])
        for component in ROADMAP["scoring_components"]:
            assert component["status"] and set(component["status"]) <= allowed
            assert "READY" not in component["status"], component["component"]

    def test_dependence_rules_never_yield_independence(self) -> None:
        for rule in ROADMAP["dependence_rules_designed_not_active"]:
            assert rule["yields"] == "KNOWN_DEPENDENT", rule["id"]

    def test_the_level_hazard_is_resolved_before_any_detector(self) -> None:
        assert "N05" in _ancestors("N06")


class TestMission1851:
    def test_scope_excludes_implementation_and_models(self) -> None:
        brief = ROADMAP["mission_1_85_1"]
        out = " ".join(brief["out_of_scope"])
        for excluded in ("collector", "migration", "model calls", "scores", "opportunities"):
            assert excluded in out
        assert brief["stop_rule"]
