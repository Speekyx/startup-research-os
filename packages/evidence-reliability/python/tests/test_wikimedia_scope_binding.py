"""Mission 1.77. The resource was in the lineage all along, and the rule that reads it.

Four things this file defends.

A RESOURCE IS READ FROM LINEAGE OR IT IS NOT A RESOURCE. `scope_from_lineage` builds the
five-part scope from the one distinct resource the RawRecords carry, and refuses an
ambiguous or absent lineage rather than picking. It names no source, and it cannot be handed
a resource from anywhere else.

THE SCOPE IS EXACT. The real resolver over the shipped diagnostic binds every resolved row to
an assessment whose scope equals the row's on all five parts, so the two Wikimedia kinds
cannot swap values and a Stack Exchange row cannot borrow one.

NOTHING WAS WRITTEN. The diagnostic's counters are equal before and after, no reliability is
on any Evidence row, no assessment, no independence group, no score, no revision.

THE STALE LIMITATION IS REPORTED, NOT EDITED, and the predecessors that carried the false
lineage sentence still carry it under a forward pointer.

`unittest`, not pytest: `run_python_tests.py` discovers this package with `unittest discover`.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import pathlib
import unittest

from sros_contracts import ClaimType, ReliabilityResolutionOutcome
from sros_evidence_reliability import (
    BASIS_ABSENT,
    BASIS_AMBIGUOUS,
    BASIS_EXPLICIT,
    LineageScope,
    ReliabilityScope,
    resolve_reliability,
    scope_from_lineage,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"
PACKAGE = REPO_ROOT / "packages" / "evidence-reliability" / "python" / "sros_evidence_reliability"

DECISION = DATA / "wikimedia-measurement-scope-binding-v1.json"
DIAGNOSTIC = DATA / "reliability-resource-binding-diagnostic-v1.json"
GATE = SCRIPTS / "render_wikimedia_scope_binding.py"
DIAGNOSTIC_SCRIPT = SCRIPTS / "report_reliability_resource_binding.py"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

FACTS = {"proposition": "some_kind"}


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_wikimedia_scope_binding", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ============================================================ the rule, by itself


class TestTheRuleReadsLineageOrRefuses(unittest.TestCase):
    def test_one_distinct_resource_and_kind_builds_the_five_part_scope(self):
        built = scope_from_lineage(
            source_id="a-source",
            claim_type=ClaimType.OBSERVED,
            proposition_facts=FACTS,
            lineage_resource_ids=["res/one", "res/one", None],
            lineage_record_kind_ids=["kind_a", "kind_a"],
        )
        self.assertEqual(built.basis, BASIS_EXPLICIT)
        self.assertEqual(
            built.scope,
            ReliabilityScope("a-source", "res/one", "kind_a", ClaimType.OBSERVED, "some_kind"),
        )

    def test_two_distinct_resources_build_no_scope(self):
        """The positive control the brief asks for: ambiguity stays unresolved."""
        built = scope_from_lineage(
            source_id="a-source",
            claim_type=ClaimType.OBSERVED,
            proposition_facts=FACTS,
            lineage_resource_ids=["res/one", "res/two"],
            lineage_record_kind_ids=["kind_a"],
        )
        self.assertIsNone(built.scope)
        self.assertEqual(built.basis, BASIS_AMBIGUOUS)
        result = resolve_reliability(scope=built.scope, candidates=[])
        self.assertIs(result.outcome, ReliabilityResolutionOutcome.NO_APPLICABLE_ASSESSMENT)
        self.assertIsNone(result.reliability)

    def test_two_record_kinds_build_no_scope(self):
        built = scope_from_lineage(
            source_id="a-source",
            claim_type=ClaimType.OBSERVED,
            proposition_facts=FACTS,
            lineage_resource_ids=["res/one"],
            lineage_record_kind_ids=["kind_a", "kind_b"],
        )
        self.assertIsNone(built.scope)
        self.assertEqual(built.basis, BASIS_AMBIGUOUS)

    def test_an_absent_resource_or_kind_or_proposition_builds_no_scope(self):
        for resources, kinds, facts in (
            ([], ["kind_a"], FACTS),
            (["res/one"], [], FACTS),
            (["res/one"], ["kind_a"], {}),
            (["", None], ["kind_a"], FACTS),
        ):
            built = scope_from_lineage(
                source_id="a-source",
                claim_type=ClaimType.OBSERVED,
                proposition_facts=facts,
                lineage_resource_ids=resources,
                lineage_record_kind_ids=kinds,
            )
            self.assertIsNone(built.scope, (resources, kinds, facts))
            self.assertEqual(built.basis, BASIS_ABSENT)

    def test_a_scope_without_an_explicit_basis_cannot_be_constructed(self):
        """There is nowhere to put a resource that came from anywhere else."""
        scope = ReliabilityScope("s", "r", "k", ClaimType.OBSERVED, "p")
        with self.assertRaises(ValueError):
            LineageScope(scope, BASIS_AMBIGUOUS)
        with self.assertRaises(ValueError):
            LineageScope(None, BASIS_EXPLICIT)

    def test_the_rule_takes_no_resource_parameter(self):
        import inspect

        params = set(inspect.signature(scope_from_lineage).parameters)
        self.assertNotIn("resource_id", params)
        self.assertEqual(
            params,
            {
                "source_id",
                "claim_type",
                "proposition_facts",
                "lineage_resource_ids",
                "lineage_record_kind_ids",
            },
        )

    def test_the_rule_and_the_diagnostic_name_no_source_and_no_resource(self):
        diagnostic = load(DIAGNOSTIC)
        inventory = diagnostic["lineage_audit"]["raw_record_resources"]
        names = {e["source_id"] for e in inventory} | {e["resource_id"] for e in inventory}
        for path in (PACKAGE / "lineage.py", DIAGNOSTIC_SCRIPT):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            docstrings = {
                ast.get_docstring(n)
                for n in ast.walk(tree)
                if isinstance(n, ast.Module | ast.ClassDef | ast.FunctionDef)
            }
            literals = {
                n.value
                for n in ast.walk(tree)
                if isinstance(n, ast.Constant)
                and isinstance(n.value, str)
                and n.value not in docstrings
            }
            self.assertEqual(sorted(literals & names), [], path.name)
            imports = {
                (n.module or "").split(".")[0]
                for n in ast.walk(tree)
                if isinstance(n, ast.ImportFrom)
            } | {
                a.name.split(".")[0]
                for n in ast.walk(tree)
                if isinstance(n, ast.Import)
                for a in n.names
            }
            self.assertNotIn("sros_acquisition", imports, path.name)


# ============================================================ the shipped diagnostic


class TestTheDiagnosticBindsExactly(unittest.TestCase):
    def setUp(self):
        self.diagnostic = load(DIAGNOSTIC)
        self.decision = load(DECISION)
        self.rows = self.diagnostic["rows"]
        self.assessments = {a["id"]: a for a in self.diagnostic["current_assessments"]}

    def test_every_row_has_exactly_one_lineage_resource(self):
        m = self.diagnostic["measurements"]
        self.assertEqual(m["rows_with_exactly_one_lineage_resource"], m["evidence_rows"])
        self.assertEqual(m["rows_with_ambiguous_lineage_resource"], 0)
        self.assertEqual(m["rows_with_no_lineage_resource"], 0)

    def test_every_resolved_row_is_bound_on_all_five_parts(self):
        resolved = [r for r in self.rows if r["resolution_via_lineage"]["outcome"] == "RESOLVED"]
        self.assertGreater(len(resolved), 0)
        for row in resolved:
            self.assertEqual(row["resource_basis"], BASIS_EXPLICIT)
            self.assertEqual(row["scope"]["resource_id"], row["lineage"]["resources"][0])
            binding = row["resolution_via_lineage"]
            self.assertEqual(binding["assessment_scope"], row["scope"])
            self.assertEqual(self.assessments[binding["assessment_id"]]["scope"], row["scope"])
            self.assertEqual(
                binding["reliability"], self.assessments[binding["assessment_id"]]["reliability"]
            )

    def test_the_two_wikimedia_kinds_resolve_different_assessments(self):
        by_kind = {}
        for row in self.rows:
            if (
                row["source_id"] == "wikimedia-pageviews"
                and row["resolution_via_lineage"]["outcome"] == "RESOLVED"
            ):
                by_kind.setdefault(row["proposition_kind"], set()).add(
                    (
                        row["resolution_via_lineage"]["assessment_id"],
                        row["resolution_via_lineage"]["reliability"],
                    )
                )
        self.assertEqual(len(by_kind), 2)
        values = list(by_kind.values())
        self.assertEqual(len(values[0]), 1)
        self.assertEqual(len(values[1]), 1)
        self.assertNotEqual(values[0], values[1])

    def test_the_same_resolver_resolves_more_through_lineage_than_through_claim_facts(self):
        m = self.diagnostic["measurements"]
        self.assertGreater(m["resolved_via_lineage"], m["resolved_via_claim_facts"])
        self.assertEqual(m["scorable_via_stored_column"], 0)
        self.assertEqual(m["scorable_via_lineage"], m["resolved_via_lineage"])

    def test_stack_exchange_stays_unresolved_and_ted_stays_resolved(self):
        se = [r for r in self.rows if r["source_id"] == "stack-exchange"]
        self.assertTrue(se)
        for row in se:
            self.assertEqual(row["resolution_via_lineage"]["outcome"], "NO_APPLICABLE_ASSESSMENT")
            self.assertIsNone(row["resolution_via_lineage"]["reliability"])
        ted = [r for r in self.rows if r["source_id"] == "ted-eu"]
        self.assertTrue(ted)
        for row in ted:
            self.assertEqual(row["resolution_via_claim_facts"]["outcome"], "RESOLVED")
            self.assertEqual(row["resolution_via_lineage"]["outcome"], "RESOLVED")
            self.assertEqual(
                row["resolution_via_lineage"]["assessment_id"],
                row["resolution_via_claim_facts"]["assessment_id"],
            )

    def test_the_opportunity_linked_rows_resolve_except_the_stack_exchange_one(self):
        linked = [r for r in self.rows if r["on_opportunity"]]
        self.assertEqual(
            len(linked), self.decision["canonical_baseline"]["opportunity_evidence_links"]
        )
        unresolved = [
            r["source_id"] for r in linked if r["resolution_via_lineage"]["outcome"] != "RESOLVED"
        ]
        self.assertEqual(unresolved, ["stack-exchange"])

    def test_nothing_was_written(self):
        counters = self.diagnostic["counters"]
        self.assertEqual(counters["before"], counters["after"])
        self.assertEqual(counters["after"]["evidence_reliability_written"], 0)
        self.assertEqual(counters["after"]["scores_table"], "ABSENT")
        self.assertEqual(counters["after"]["independence_groups"], 0)
        self.assertEqual(counters["after"]["opportunity_revisions"], 1)

    def test_the_aggregation_is_diagnostic_only_and_identical_to_pass_through(self):
        agg = self.diagnostic["aggregation_diagnostic"]
        self.assertEqual(
            agg["$banner"], ["UNCALIBRATED", "DIAGNOSTIC_ONLY", "NOT_AN_OPPORTUNITY_SCORE"]
        )
        self.assertFalse(agg["persisted"])
        self.assertEqual(agg["calibration"], "UNCALIBRATED")
        self.assertEqual(agg["claims_where_full_aggregator_differs_from_pass_through"], 0)
        self.assertEqual(agg["claims_with_established_independence"], 0)
        for claim in agg["claims"]:
            self.assertEqual(claim["support_group_count"], 1)
            self.assertEqual(claim["limiting_components"], ["reliability"])


# ============================================================ the decision record


class TestTheDecisionRecord(unittest.TestCase):
    def setUp(self):
        self.decision = load(DECISION)

    def test_the_outcome_is_root_cause_revised_and_says_why_not_repaired(self):
        self.assertEqual(
            self.decision["primary_outcome"], "RELIABILITY_APPLICABILITY_ROOT_CAUSE_REVISED"
        )
        self.assertTrue(self.decision["why_not_REPAIRED"].strip())
        criteria = self.decision["repaired_criteria_section_27"]
        self.assertTrue(criteria["all_met"])

    def test_the_binding_basis_is_explicit_and_independent_of_current_config(self):
        identity = self.decision["resource_identity"]
        self.assertEqual(identity["binding_basis"], BASIS_EXPLICIT)
        self.assertEqual(identity["RESOURCE_BINDING_DEPENDS_ON_CURRENT_MUTABLE_CONFIG"], "NO")
        self.assertEqual(identity["explicit_or_derived"], "EXPLICIT")
        self.assertFalse(identity["verification_target"]["used_as_implementation_authority"])
        self.assertEqual(len(identity["insufficient_bases_not_relied_on"]), 8)

    def test_option_a_alone_is_selected(self):
        selected = [k for k, v in self.decision["options"].items() if v["verdict"] == "SELECTED"]
        self.assertEqual(selected, ["A"])
        self.assertEqual(self.decision["selected_option"], "A")

    def test_the_stale_limitation_is_reported_and_not_edited(self):
        limitation = self.decision["opportunity_limitation"]
        self.assertTrue(limitation["stale"])
        self.assertTrue(limitation["true_when_written"])
        self.assertEqual(limitation["action"], "STOP")
        self.assertEqual(limitation["code"], "OPPORTUNITY_LIMITATION_RECONCILIATION_REQUIRED")
        self.assertFalse(limitation["historical_revision_edited"])
        self.assertFalse(limitation["revision_2_created"])

    def test_mission_accounting_is_zero_everywhere(self):
        self.assertEqual({k: v for k, v in self.decision["mission_accounting"].items() if v}, {})

    def test_the_parked_arc_is_untouched(self):
        parked = self.decision["parked_states_preserved"]
        self.assertFalse(parked["changed_by_this_mission"])
        self.assertEqual(
            parked["globalping"],
            {"PASS": 12, "PARTIAL": 0, "FAIL": 0, "verdict": "COUNTERPART_RESOLVED"},
        )
        self.assertFalse(parked["q1"]["CONSTRUCT_SELECTED"])

    def test_the_predecessors_point_forward_and_still_carry_their_sentences(self):
        moves = load(DATA / "evidence-completion-candidate-moves-v1.json")
        m1 = next(c for c in moves["candidates"] if c["candidate_id"] == "M1")
        self.assertTrue(
            any("absent from the whole acquisition lineage" in b for b in m1["known_blockers"])
        )
        for name in self.decision["opportunity_limitation"][
            "derived_carriers_given_forward_pointers"
        ]:
            record = load(REPO_ROOT / name)
            self.assertEqual(record["forward_pointer"]["appended_by_mission"], "1.77")
            self.assertEqual(
                record["forward_pointer"]["superseded_by"], f"docs/data/{DECISION.name}"
            )
            self.assertFalse(record["forward_pointer"]["record_edited"])
            self.assertNotEqual(record.get("mission"), "1.77")


# ============================================================ the gate


class TestTheGate(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.decision, self.diagnostic = self.gate.validate()

    def test_the_shipped_records_pass(self):
        self.assertEqual(
            self.decision["primary_outcome"], "RELIABILITY_APPLICABILITY_ROOT_CAUSE_REVISED"
        )

    def test_a_closest_match_binding_is_refused(self):
        diagnostic = copy.deepcopy(self.diagnostic)
        row = next(
            r for r in diagnostic["rows"] if r["resolution_via_lineage"]["outcome"] == "RESOLVED"
        )
        row["resolution_via_lineage"]["assessment_scope"]["proposition_kind"] = "another_kind"
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_every_resolution_is_exact(diagnostic)

    def test_a_resource_from_somewhere_else_is_refused(self):
        diagnostic = copy.deepcopy(self.diagnostic)
        row = next(
            r for r in diagnostic["rows"] if r["resolution_via_lineage"]["outcome"] == "RESOLVED"
        )
        row["lineage"]["resources"] = ["somewhere/else"]
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_every_resolution_is_exact(diagnostic)

    def test_an_ambiguous_lineage_that_still_built_a_scope_is_refused(self):
        diagnostic = copy.deepcopy(self.diagnostic)
        row = next(r for r in diagnostic["rows"] if r["scope"] is not None)
        row["lineage"]["resources"] = [row["lineage"]["resources"][0], "another/resource"]
        row["lineage"]["distinct_resource_count"] = 2
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_every_resolution_is_exact(diagnostic)

    def test_an_ambiguous_lineage_that_built_no_scope_is_accepted(self):
        """Inverted control: the refusal state stays representable."""
        diagnostic = copy.deepcopy(self.diagnostic)
        row = next(r for r in diagnostic["rows"] if r["scope"] is not None)
        row["lineage"]["resources"] = [row["lineage"]["resources"][0], "another/resource"]
        row["lineage"]["distinct_resource_count"] = 2
        row["scope"] = None
        row["resource_basis"] = BASIS_AMBIGUOUS
        row["resolution_via_lineage"] = {
            "outcome": "NO_APPLICABLE_ASSESSMENT",
            "reliability": None,
            "assessment_id": None,
            "assessment_version": None,
            "origin": None,
        }
        row["scorable_via_lineage"] = False
        self.gate._check_every_resolution_is_exact(diagnostic)

    def test_the_two_wikimedia_values_swapped_are_refused(self):
        diagnostic = copy.deepcopy(self.diagnostic)
        detailed = next(
            r
            for r in diagnostic["rows"]
            if r["proposition_kind"] == "platform_counted_content_request_change"
        )
        convergent = next(
            r
            for r in diagnostic["rows"]
            if r["proposition_kind"] == "platform_counted_content_request_change_witnessed"
        )
        detailed["resolution_via_lineage"]["reliability"] = convergent["resolution_via_lineage"][
            "reliability"
        ]
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_every_resolution_is_exact(diagnostic)

    def test_a_moved_counter_is_refused(self):
        diagnostic = copy.deepcopy(self.diagnostic)
        diagnostic["counters"]["after"]["reliability_assessments"] += 1
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_nothing_was_written(self.decision, diagnostic)

    def test_an_edited_revision_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["opportunity_limitation"]["historical_revision_edited"] = True
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_limitation_is_reported_not_edited(decision, self.diagnostic)

    def test_a_forced_repaired_outcome_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["primary_outcome"] = "WIKIMEDIA_MEASUREMENT_SCOPE_BINDING_REPAIRED"
        decision["repaired_criteria_section_27"]["16_zero_probe_escapes"] = False
        decision["repaired_criteria_section_27"]["all_met"] = False
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_outcome(decision)

    def test_a_proven_repaired_outcome_is_accepted(self):
        """Inverted control: the gate does not pin the repository to this mission's verdict."""
        decision = copy.deepcopy(self.decision)
        decision["primary_outcome"] = "WIKIMEDIA_MEASUREMENT_SCOPE_BINDING_REPAIRED"
        self.gate._check_the_outcome(decision)

    def test_the_gate_is_registered_in_ci(self):
        self.assertIn("render_wikimedia_scope_binding.py --check", CI.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
