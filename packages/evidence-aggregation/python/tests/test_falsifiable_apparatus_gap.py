"""Mission 1.48 §36. Contradiction: the machinery, and everything that is not one.

The failure this guards is the one the aggregator cannot guard itself. Grouping
is claim-centric and provenance-based: it has never heard of the proposition, so
it cannot tell a genuine disagreement from two observations that merely differ.
Every rule below therefore has to hold UPSTREAM of the aggregator, in the
proposition semantics -- and the tests that matter most are the ones showing the
aggregator would happily accept a shape that is semantically wrong.

**Non-empty fixtures throughout**, including a POSITIVE contradiction fixture
that drives the real `aggregate()` and shows non-zero contradiction and conflict
mass. That fixture is the point: the machinery works, and no real Claim can
reach it.

Fixtures are SYNTHETIC and nothing here is persisted. `unittest`, not pytest,
and this file imports only `sros_contracts` and `sros_evidence_aggregation` --
the packages the zero-dependency runner puts on this suite's path. Mission 1.47
shipped a cross-package import here and CI caught it; §33 made the rule
load-bearing.
"""

from __future__ import annotations

import json
import pathlib
import unittest
from datetime import UTC, datetime

from sros_contracts import ClaimTemporality, EvidenceDirection, EvidenceIndependenceState
from sros_evidence_aggregation import REFERENCE_PROFILE_V1, aggregate
from sros_evidence_aggregation.independence import group_by_independence
from sros_evidence_aggregation.items import EvidenceItem, ItemContribution

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
REQUIREMENTS = DOCS / "falsifiable-evidence-apparatus-requirements-v1.json"
TRADEOFF = DOCS / "falsifiability-vs-convergence-tradeoff-v1.json"
BASELINE = DOCS / "falsifiable-evidence-apparatus-gap-baseline-v1.json"

MOMENT = datetime(2026, 9, 4, tzinfo=UTC)


def requirements() -> dict:
    return json.loads(REQUIREMENTS.read_text(encoding="utf-8"))


def tradeoff() -> dict:
    return json.loads(TRADEOFF.read_text(encoding="utf-8"))


def baseline() -> dict:
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def family(family_id: str) -> dict:
    return next(f for f in tradeoff()["proposition_families"] if f["id"] == family_id)


def item(
    evidence_id: str,
    direction: EvidenceDirection = EvidenceDirection.SUPPORTS,
    state: EvidenceIndependenceState = EvidenceIndependenceState.KNOWN_INDEPENDENT,
    reliability: float = 0.6,
) -> EvidenceItem:
    """One SYNTHETIC scorable item. Fixture-owned values, never a reviewed one."""
    return EvidenceItem(
        evidence_id=evidence_id,
        direction=direction,
        relevance=1.0,
        directness=1.0,
        reliability=reliability,
        extraction_confidence=1.0,
        independence_state=state,
        independence_group_id=None,
        observed_at=None,
    )


def run(claim_id: str, *items: EvidenceItem):
    return aggregate(
        claim_id,
        items,
        REFERENCE_PROFILE_V1,
        temporality=ClaimTemporality.EVERGREEN,
        now=MOMENT,
        allow_uncalibrated=True,
    )


def contributions(*items) -> dict[str, ItemContribution]:
    return {
        element.evidence_id: ItemContribution(
            evidence_id=element.evidence_id,
            direction=element.direction,
            components={
                "relevance": element.relevance,
                "directness": element.directness,
                "reliability": element.reliability,
                "extraction_confidence": element.extraction_confidence,
                "freshness": 1.0,
            },
            scorable=True,
            q=element.reliability,
            limiting_component="reliability",
        )
        for element in items
    }


# ================================================ §30 the contradiction fixture


class ContradictionMachineryWorks(unittest.TestCase):
    """POSITIVE control. If this ever fails, the mission's central claim -- that
    the machinery is fine and unreachable -- has become false in the first half."""

    def setUp(self):
        self.result = run(
            "synthetic-contradiction",
            item("supports", EvidenceDirection.SUPPORTS, reliability=0.6),
            item("contradicts", EvidenceDirection.CONTRADICTS, reliability=0.5),
        )

    def test_one_support_group_and_one_contradiction_group(self):
        self.assertEqual(self.result.support_group_count, 1)
        self.assertEqual(self.result.contradiction_group_count, 1)

    def test_contradiction_strength_is_non_zero(self):
        self.assertGreater(self.result.masses.contradiction_strength, 0)

    def test_conflict_mass_is_non_zero(self):
        self.assertGreater(self.result.masses.conflict_mass, 0)

    def test_all_four_masses_sum_to_one(self):
        masses = self.result.masses
        total = (
            masses.supported_mass
            + masses.contradicted_mass
            + masses.conflict_mass
            + masses.uncertainty_mass
        )
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_the_record_reports_the_machinery_as_working(self):
        block = requirements()["structural_reconstruction"][
            "C_contradiction_produces_non_zero_mass"
        ]
        self.assertTrue(block["established"])
        self.assertIn("NOT the gap", block["conclusion"])


class SupportAndContradictConditionsWork(unittest.TestCase):
    def test_exact_support_condition_produces_support_strength(self):
        result = run("supported", item("a", EvidenceDirection.SUPPORTS))
        self.assertGreater(result.masses.support_strength, 0)
        self.assertEqual(result.masses.contradiction_strength, 0)

    def test_exact_contradict_condition_produces_contradiction_strength(self):
        result = run("contradicted", item("a", EvidenceDirection.CONTRADICTS))
        self.assertGreater(result.masses.contradiction_strength, 0)
        self.assertEqual(result.masses.support_strength, 0)

    def test_the_falsifier_specification_names_both_conditions(self):
        falsifier = requirements()["falsifier_specification"]
        self.assertIn(">= X", falsifier["SUPPORT_CONDITION"])
        self.assertIn("< X", falsifier["CONTRADICT_CONDITION"])


# ================================================ §2 monotone existentials


class MonotoneExistentialsCannotBeContradicted(unittest.TestCase):
    def test_the_existential_families_are_marked_monotone(self):
        for family_id in (
            "SOURCE_ATTRIBUTED_EXISTENTIAL_WITNESS",
            "SOURCE_ATTRIBUTED_HISTORICAL_RESTATEMENT",
        ):
            with self.subTest(family=family_id):
                self.assertTrue(family(family_id)["monotone"])

    def test_no_monotone_family_is_falsifiable(self):
        for entry in tradeoff()["proposition_families"]:
            if entry["monotone"]:
                with self.subTest(family=entry["id"]):
                    self.assertFalse(entry["falsifiable"])
                    self.assertEqual(entry["CONTRADICTION_CAPABILITY"], "NOT_APPLICABLE")

    def test_no_monotone_family_names_a_falsifier(self):
        for entry in tradeoff()["proposition_families"]:
            if entry["monotone"]:
                with self.subTest(family=entry["id"]):
                    self.assertTrue(entry["falsifier"].startswith("NONE"))

    def test_a_counterexample_from_another_apparatus_is_not_a_contradiction(self):
        """The rejection is recorded with its reason code, and the reason names
        the actual logic rather than gesturing at it."""
        rejected = {r["family"]: r for r in tradeoff()["rejected_as_contradiction_targets"]}
        entry = rejected["existential witness Claims"]
        self.assertEqual(entry["code"], "MONOTONE_EXISTENTIAL_NOT_CONTRADICTION_CAPABLE")
        self.assertIn("does not falsify", entry["why"])

    def test_at_least_one_family_is_non_monotone_and_falsifiable(self):
        """Otherwise the tests above pass vacuously over a table with no
        contrast in it."""
        falsifiable = [f for f in tradeoff()["proposition_families"] if f["falsifiable"]]
        self.assertTrue(falsifiable)
        for entry in falsifiable:
            self.assertFalse(entry["monotone"])


class PointClaimsCanDefineAFalsifier(unittest.TestCase):
    def test_the_preferred_family_is_falsifiable_and_non_monotone(self):
        selected = requirements()["preferred_proposition_family"]["selected"]
        entry = family(selected)
        self.assertTrue(entry["falsifiable"])
        self.assertFalse(entry["monotone"])

    def test_every_falsifiable_family_names_its_falsifier(self):
        for entry in tradeoff()["proposition_families"]:
            if entry["falsifiable"]:
                with self.subTest(family=entry["id"]):
                    self.assertTrue(entry["falsifier"].strip())
                    self.assertFalse(entry["falsifier"].startswith("NONE"))


# ================================================ §4 what is NOT a contradiction


class ThingsThatAreNotContradictions(unittest.TestCase):
    CASES = (
        "different periods",
        "different geography or population",
        "different units",
        "different measurement definitions",
        "different requester classes",
        "a missing observation",
        "another source being silent",
        "one source reporting a different but compatible statistic",
        "an INCREASING Claim beside a DECREASING Claim",
    )

    def setUp(self):
        self.cases = {c["case"]: c["why"] for c in requirements()["not_a_contradiction"]["cases"]}

    def test_every_named_case_is_recorded_with_a_reason(self):
        for case in self.CASES:
            with self.subTest(case=case):
                self.assertIn(case, self.cases)
                self.assertTrue(self.cases[case].strip())

    def test_different_period_unit_and_population_are_each_refused(self):
        for case in ("different periods", "different units", "different geography or population"):
            with self.subTest(case=case):
                self.assertIn(case, self.cases)

    def test_absence_of_a_record_is_not_a_contradiction_in_the_aggregator(self):
        """An absent observation is not a CONTRADICTS row; it is nothing. One
        supporting item alone produces zero contradiction strength."""
        result = run("only-support", item("a", EvidenceDirection.SUPPORTS))
        self.assertEqual(result.masses.contradiction_strength, 0)
        self.assertEqual(result.contradiction_group_count, 0)

    def test_differing_values_between_attributed_statements_are_jointly_satisfiable(self):
        rejected = {r["family"]: r for r in tradeoff()["rejected_as_contradiction_targets"]}
        entry = rejected["source-attributed historical restatements"]
        self.assertEqual(entry["code"], "SOURCE_ATTRIBUTED_STATEMENTS_ARE_JOINTLY_SATISFIABLE")
        self.assertIn("both true simultaneously", entry["why"])

    def test_two_observations_on_different_claims_never_interact(self):
        """The mechanical reason a different period, unit or population cannot
        contradict: aggregation is CLAIM-CENTRIC, so two observations that
        belong to different propositions are aggregated separately and neither
        can reach the other. This is what makes the semantic rules load-bearing
        upstream -- the aggregator cannot enforce them."""
        first = run("claim-period-1", item("a", EvidenceDirection.SUPPORTS))
        second = run("claim-period-2", item("b", EvidenceDirection.CONTRADICTS))
        self.assertEqual(first.masses.contradiction_strength, 0)
        self.assertEqual(second.masses.support_strength, 0)

    def test_but_the_aggregator_would_accept_them_on_one_claim(self):
        """And this is why the rules cannot live here. Hand the aggregator the
        same two items under ONE claim_id and it produces a contradiction
        happily, because it has never heard of the proposition."""
        result = run(
            "one-claim",
            item("a", EvidenceDirection.SUPPORTS),
            item("b", EvidenceDirection.CONTRADICTS),
        )
        self.assertGreater(result.masses.conflict_mass, 0)


# ================================================ §31 independence positive control


class IndependenceRegressionGuard(unittest.TestCase):
    def test_two_known_independent_supports_form_two_groups(self):
        result = run(
            "two-independent",
            item("a", state=EvidenceIndependenceState.KNOWN_INDEPENDENT, reliability=0.6),
            item("b", state=EvidenceIndependenceState.KNOWN_INDEPENDENT, reliability=0.5),
        )
        self.assertEqual(result.support_group_count, 2)

    def test_saturation_exceeds_the_strongest_single_group(self):
        result = run(
            "two-independent",
            item("a", state=EvidenceIndependenceState.KNOWN_INDEPENDENT, reliability=0.6),
            item("b", state=EvidenceIndependenceState.KNOWN_INDEPENDENT, reliability=0.5),
        )
        self.assertGreater(result.masses.support_strength, 0.6)

    def test_unknown_independence_collapses_into_one_group(self):
        result = run(
            "two-unknown",
            item("a", state=EvidenceIndependenceState.UNKNOWN),
            item("b", state=EvidenceIndependenceState.UNKNOWN),
        )
        self.assertEqual(result.support_group_count, 1)

    def test_unknown_remains_unknown_and_is_never_promoted(self):
        groups = group_by_independence(
            (
                item("a", state=EvidenceIndependenceState.UNKNOWN),
                item("b", state=EvidenceIndependenceState.UNKNOWN),
                item("c", state=EvidenceIndependenceState.UNKNOWN),
            ),
            contributions(
                item("a", state=EvidenceIndependenceState.UNKNOWN),
                item("b", state=EvidenceIndependenceState.UNKNOWN),
                item("c", state=EvidenceIndependenceState.UNKNOWN),
            ),
            EvidenceDirection.SUPPORTS,
        )
        self.assertEqual(len(groups), 1)


# ================================================ §0 the baseline


class BaselineUnchanged(unittest.TestCase):
    EXPECTED = {
        "raw_records": 325,
        "normalized_records": 325,
        "signals": 33,
        "claims": 43,
        "claim_revisions": 44,
        "evidence": 57,
        "reliability_assessments": 4,
        "reliability_basis_rows": 12,
        "independence_groups": 0,
        "opportunities": 1,
        "opportunity_revisions": 1,
        "opportunity_evidence_links": 7,
        "embeddings": 0,
        "registered_sources": 29,
        "evidence_with_stored_reliability": 0,
    }

    def test_measured_counters_match_the_frozen_baseline(self):
        counters = baseline()["counters"]
        for name, value in self.EXPECTED.items():
            with self.subTest(counter=name):
                self.assertEqual(counters[name], value)

    def test_scores_table_is_absent(self):
        self.assertEqual(baseline()["counters"]["scores_table"], "ABSENT")

    def test_profile_is_uncalibrated(self):
        self.assertEqual(baseline()["profile_calibration_status"], "UNCALIBRATED")

    def test_the_aggregator_matches_b2_on_every_live_claim(self):
        shape = baseline()["aggregation_shape"]
        self.assertEqual(shape["aggregator_differs_from_b2_cases"], 0)
        self.assertEqual(shape["max_support_groups_on_one_claim"], 1)
        self.assertEqual(shape["claims_with_any_contradiction_group"], 0)

    def test_the_requirements_record_reports_the_same_counters(self):
        recorded = requirements()["counters"]
        for name, value in self.EXPECTED.items():
            with self.subTest(counter=name):
                self.assertEqual(recorded[name]["before"], value)
                self.assertEqual(recorded[name]["after"], value)


# ================================================ §17/§18 no source selected


class NoSourceWasSelected(unittest.TestCase):
    def test_the_record_says_so_explicitly(self):
        self.assertTrue(requirements()["registered_but_unheld"]["no_source_was_selected"])

    def test_no_candidate_is_promising_merely_because_it_is_registered(self):
        for candidate in requirements()["registered_but_unheld"]["candidates"]:
            with self.subTest(source=candidate["source_id"]):
                self.assertNotEqual(candidate["state"], "PROMISING_FROM_EXISTING_DOCUMENTATION")
                self.assertTrue(candidate["why"].strip())

    def test_at_most_three_candidates(self):
        self.assertLessEqual(len(requirements()["registered_but_unheld"]["candidates"]), 3)

    def test_no_held_apparatus_is_contradiction_capable(self):
        for row in requirements()["portfolio_matrix"]["held_apparatuses"]:
            with self.subTest(apparatus=row["apparatus"]):
                self.assertEqual(row["CONTRADICTION_CAPABLE"], "NO")
                self.assertEqual(row["FALSIFIABLE_POINT_CLAIM"], "NO")


class ReliabilityReviewabilityIsARequiredProperty(unittest.TestCase):
    def test_it_is_a_first_class_gate_with_a_minimum_list(self):
        gate = requirements()["reliability_reviewability_gate"]
        self.assertTrue(gate["minimum"])
        self.assertIn("first-party", " ".join(gate["minimum"]))

    def test_an_attractive_apparatus_may_not_bypass_it(self):
        self.assertIn(
            "must not be promoted", requirements()["reliability_reviewability_gate"]["rule"]
        )

    def test_the_apparatus_spec_requires_retrievable_methodology(self):
        spec = requirements()["apparatus_requirements"]
        self.assertIn("RETRIEVABLE", spec["methodology_documentation"])
        self.assertIn("DOCUMENTED", spec["lineage_documentation"])


# ================================================ nothing moved


class NothingMoved(unittest.TestCase):
    def test_no_research_data_acquired(self):
        self.assertEqual(requirements()["network_budget"]["RESEARCH_DATA_REQUESTS"], 0)

    def test_no_documentation_requests_either(self):
        budget = requirements()["network_budget"]
        self.assertEqual(budget["APPARATUS_DOCUMENTATION_REQUESTS"], 0)
        self.assertEqual(budget["GOVERNANCE_DOCUMENT_REQUESTS"], 0)

    def test_no_canonical_data_mutated(self):
        for name, pair in requirements()["counters"].items():
            with self.subTest(counter=name):
                self.assertEqual(pair["before"], pair["after"])

    def test_no_reliability_value_created_or_suggested(self):
        """Section 27. The mission defines reviewability criteria and no value."""
        self.assertEqual(requirements()["counters"]["reliability_assessments"]["after"], 4)
        gate = json.dumps(requirements()["reliability_reviewability_gate"])
        for number in ("0.5", "0.55", "0.6", "0.65"):
            with self.subTest(number=number):
                self.assertNotIn(number, gate)

    def test_no_independence_group_persisted(self):
        self.assertEqual(requirements()["counters"]["independence_groups"]["after"], 0)

    def test_no_score(self):
        self.assertEqual(requirements()["counters"]["scores"]["after"], "ABSENT")

    def test_no_opportunity_change(self):
        counters = requirements()["counters"]
        self.assertEqual(counters["opportunities"]["after"], 1)
        self.assertEqual(counters["opportunity_revisions"]["after"], 1)
        self.assertEqual(counters["opportunity_evidence_links"]["after"], 7)

    def test_no_model_call_and_no_embedding(self):
        model = requirements()["model_use"]
        self.assertEqual(model["llm_calls"], 0)
        self.assertEqual(model["embeddings"], 0)
        self.assertEqual(model["usd"], 0.0)
        self.assertFalse(model["semantic_matching_used"])

    def test_problem_family_remains_parked(self):
        self.assertEqual(requirements()["model_use"]["problem_family_status"], "PARKED")

    def test_no_calibration_declared(self):
        self.assertEqual(baseline()["profile_calibration_status"], "UNCALIBRATED")


if __name__ == "__main__":
    unittest.main()
