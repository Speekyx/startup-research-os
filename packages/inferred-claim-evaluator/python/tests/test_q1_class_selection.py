"""Mission 1.76.6. A class was selected. A construct was not, and no run is authorised.

Four things this file defends.

THREE STATES STAY APART. CLASS_SELECTED says which world-state unit is worth measuring;
CONSTRUCT_SELECTED says which exact proposition; RUN_AUTHORIZED says a measurement may
happen. Collapsing them is how a selection becomes an authorisation without anybody deciding.

THE PREMISE IS ASSERTED LIVE. The selection rests on a qualification, and a quoted premise is
not a premise: the gate recounts the twelve dimensions rather than reading the tally.

VANTAGE IS UNRESOLVED AND WAS NOT RESOLVED SILENTLY. Three coherent resolutions are recorded
with their costs and none is chosen, because choosing the one that makes a construct appear
is choosing a semantics for its convenience.

A CATEGORICAL PREDICATE IS NOT A THRESHOLD. The evaluator gap is reported as a finding rather
than routed around by pushing HTTP status classes through a bound.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

SELECTED = DATA / "selected-quantity-class-v1.json"
DECISION_V5 = DATA / "quantity-class-selection-decision-v5.json"
DECISION_V6 = DATA / "quantity-class-selection-decision-v6.json"
PACKAGE_V1 = DATA / "quantity-class-package-q1-v1.json"
PACKAGE_V2 = DATA / "quantity-class-package-q1-v2.json"
CONSTRUCTS = DATA / "http-construct-candidate-evaluation-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v4.json"
CLOSURE = DATA / "globalping-residual-closure-v3.json"
PRIORITY = DATA / "evidence-completion-priority-v1.json"
RENDERER = SCRIPTS / "render_q1_class_selection.py"
PAGE = DATA / "selected-quantity-class-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_q1_class_selection", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheThreeStatesStayApart(unittest.TestCase):
    def setUp(self):
        self.selected = load(SELECTED)
        self.decision = load(DECISION_V6)

    def test_a_class_was_selected_and_nothing_more(self):
        self.assertEqual(self.selected["class_id"], "Q1")
        self.assertEqual(self.selected["state"], "CLASS_SELECTED")
        states = self.selected["states_kept_apart"]
        self.assertTrue(states["CLASS_SELECTED"])
        self.assertFalse(states["CONSTRUCT_SELECTED"])
        self.assertFalse(states["RUN_AUTHORIZED"])

    def test_no_corpus_no_predicate_no_measurement(self):
        self.assertFalse(self.selected["corpus_frozen"])
        self.assertFalse(self.selected["exact_predicate_frozen"])
        self.assertEqual(self.selected["measurements_executed"], 0)

    def test_no_construct_artifact_exists(self):
        self.assertFalse((DATA / "selected-construct-v1.json").exists())
        self.assertFalse(self.decision["selected_construct_created"])

    def test_the_selection_says_what_it_does_not_authorise(self):
        refused = self.selected["what_selection_does_not_authorise"]
        self.assertGreaterEqual(len(refused), 5)
        for phrase in ("freezing a corpus", "issuing a score"):
            with self.subTest(phrase=phrase):
                self.assertTrue(any(phrase in item for item in refused))

    def test_the_provider_limitations_travel_with_the_selection(self):
        limits = self.selected["limitations_carried_from_the_provider_declaration"]
        self.assertEqual(limits, load(CLOSURE)["limitations_carried_forward"])
        self.assertIn("no use as a proxy", limits)


class TestThePremiseIsAssertedLive(unittest.TestCase):
    def test_the_twelve_dimensions_are_recounted_not_read(self):
        counted = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "UNKNOWN": 0}
        for row in load(QUALIFICATION)["gates"]:
            counted[row["status"]] += 1
        self.assertEqual(counted, {"PASS": 12, "PARTIAL": 0, "FAIL": 0, "UNKNOWN": 0})

    def test_the_verdict_and_the_residuals_still_support_a_selection(self):
        self.assertEqual(load(QUALIFICATION)["verdict"], "COUNTERPART_RESOLVED")
        self.assertEqual(load(CLOSURE)["residuals_remaining"], 0)

    def test_the_decision_records_the_premise_it_rests_on(self):
        decision = load(DECISION_V6)
        self.assertTrue(decision["counterpart_qualified"])
        self.assertTrue(decision["q1_strategically_viable"])


class TestTheSupersessions(unittest.TestCase):
    def test_the_superseded_decision_still_records_no_selection(self):
        v5 = load(DECISION_V5)
        self.assertIsNone(v5["selected_quantity_class"])
        self.assertEqual(v5["selection_outcome"], "NO_SELECTION")
        self.assertEqual(v5["superseded_by"], DECISION_V6.name)

    def test_the_superseded_package_keeps_its_verdict_on_its_own_routes(self):
        """It graded Common Crawl and HTTP Archive. That grade is about that pair."""
        v1 = load(PACKAGE_V1)
        self.assertNotEqual(v1["class_verdict"], "STRATEGICALLY_VIABLE")
        self.assertEqual(v1["superseded_by"], PACKAGE_V2.name)

    def test_the_new_package_grades_a_different_route_pair(self):
        v2 = load(PACKAGE_V2)
        self.assertEqual(v2["class_verdict"], "STRATEGICALLY_VIABLE")
        self.assertEqual(len(v2["routes"]), 2)
        names = {r["apparatus"] for r in v2["routes"]}
        self.assertNotIn("Common Crawl", names)
        self.assertTrue(all(r["production"] == "OWN_MEASUREMENT" for r in v2["routes"]))

    def test_the_same_proposition_is_still_not_established(self):
        v2 = load(PACKAGE_V2)
        self.assertEqual(v2["same_proposition"], "PLAUSIBLE_BUT_NOT_ESTABLISHED")
        self.assertTrue(v2["why_still_not_established"].strip())

    def test_one_route_is_a_contract_and_not_code(self):
        """An execution fact, recorded as one rather than hidden."""
        fetcher = next(r for r in load(PACKAGE_V2)["routes"] if "fetcher" in r["apparatus"])
        self.assertFalse(fetcher["implemented"])


class TestVantageIsOpenAndWasNotClosedSilently(unittest.TestCase):
    def setUp(self):
        self.vantage = load(CONSTRUCTS)["vantage"]

    def test_no_resolution_was_chosen(self):
        self.assertIsNone(self.vantage["which_was_chosen"])
        self.assertTrue(self.vantage["why_none_was_chosen_here"].strip())

    def test_all_three_resolutions_are_recorded_with_their_costs(self):
        ids = [r["id"] for r in self.vantage["three_coherent_resolutions"]]
        self.assertEqual(tuple(ids), gate().VANTAGE_RESOLUTIONS)
        for resolution in self.vantage["three_coherent_resolutions"]:
            with self.subTest(resolution=resolution["id"]):
                self.assertTrue(resolution["cost"].strip())

    def test_the_finding_is_underspecification_and_not_noise(self):
        self.assertEqual(
            self.vantage["the_finding"],
            "VANTAGE_IS_PROPOSITION_UNDERSPECIFICATION_NOT_MEASUREMENT_NOISE",
        )

    def test_the_universal_route_names_the_trap_it_must_avoid(self):
        v2 = next(
            r
            for r in self.vantage["three_coherent_resolutions"]
            if r["id"] == "V2_UNIVERSAL_OVER_A_DEFINED_VANTAGE_CLASS"
        )
        self.assertIn("FRAME_INSIDE_THE_DEFINITION", v2["the_trap_it_must_avoid"])

    def test_both_vantages_are_stated_which_1_70_could_not_say(self):
        self.assertTrue(self.vantage["both_vantages_are_stated"])
        text = self.vantage["improvement_over_mission_1_70"]
        self.assertIn("DIFFERENT_AND_LOAD_BEARING", text)
        self.assertIn("does not remove the difference", text)


class TestTheCandidatesAndTheDenominator(unittest.TestCase):
    def setUp(self):
        self.constructs = load(CONSTRUCTS)

    def test_no_construct_was_selected(self):
        self.assertIsNone(self.constructs["selected_construct"])
        self.assertFalse(self.constructs["exact_predicate_frozen"])
        self.assertEqual(self.constructs["measurements_executed"], 0)

    def test_all_three_candidates_were_evaluated_and_none_selected(self):
        ids = [c["id"] for c in self.constructs["candidates"]]
        self.assertEqual(tuple(ids), gate().CANDIDATES)
        for candidate in self.constructs["candidates"]:
            with self.subTest(candidate=candidate["id"]):
                self.assertFalse(candidate["verdict"].startswith("SELECTED"))

    def test_candidate_a_was_not_preferred_merely_because_r1_work_exists(self):
        a = next(c for c in self.constructs["candidates"] if c["id"] == "CANDIDATE_A")
        self.assertTrue(a["not_selected_merely_because_r1_work_exists"])

    def test_candidate_c_is_refused_on_semantics_before_vantage(self):
        """Numeric status ordering is an artifact of the numbering, not a scale."""
        c = next(c for c in self.constructs["candidates"] if c["id"] == "CANDIDATE_C")
        self.assertIn("SEMANTICS", c["verdict"])
        self.assertIn("categorical", c["why"])

    def test_target_level_is_preferred_and_the_reason_is_the_denominator(self):
        shape = self.constructs["proposition_shape"]
        self.assertEqual(shape["preferred"], "TARGET_LEVEL")
        self.assertIn("denominator", shape["why"])

    def test_the_population_is_never_defined_by_what_answered(self):
        missing = self.constructs["missingness"]
        self.assertEqual(missing["targets_removed_from_N_for_any_outcome"], 0)
        self.assertTrue(missing["excluded_targets_remain_terminal_records"])
        self.assertFalse(missing["outcome_selected_denominator"])
        self.assertIn("manifest", missing["denominator_rule"])

    def test_apparatus_failure_is_not_a_world_fact(self):
        self.assertTrue(self.constructs["missingness"]["apparatus_failure_is_not_a_world_fact"])

    def test_target_level_is_what_makes_contradiction_reachable(self):
        self.assertIn(
            "contradiction", self.constructs["proposition_shape"]["what_target_level_unlocks"]
        )


class TestTheEvaluatorGapIsReported(unittest.TestCase):
    def setUp(self):
        self.evaluator = load(CONSTRUCTS)["evaluator_compatibility"]

    def test_a_categorical_predicate_does_not_fit_the_threshold_evaluator(self):
        self.assertFalse(self.evaluator["fits_a_target_level_http_predicate"])
        self.assertEqual(
            self.evaluator["what_would_be_required"], "CATEGORICAL_MEMBERSHIP_EVALUATOR"
        )

    def test_the_gap_is_reported_as_small_and_additive_rather_than_routed_around(self):
        self.assertIn("additive", self.evaluator["size_of_the_gap"])
        self.assertTrue(self.evaluator["this_is_not_the_primary_blocker"].strip())

    def test_the_inferred_claim_architecture_is_compatible(self):
        compat = self.evaluator["inferred_claim_compatibility"]
        self.assertEqual(compat["proposition_identity"], "COMPATIBLE")
        self.assertFalse(compat["source_id_in_identity"])
        self.assertFalse(compat["measurement_value_in_identity"])

    def test_no_threshold_is_contemplated_for_a_categorical_predicate(self):
        compat = self.evaluator["inferred_claim_compatibility"]
        self.assertIn("NOT_APPLICABLE", compat["threshold_registration"])

    def test_the_request_contract_pins_method_and_redirect_following(self):
        fields = {f["field"]: f for f in load(CONSTRUCTS)["request_comparability"]["fields"]}
        self.assertEqual(fields["METHOD"]["value"], "HEAD")
        self.assertEqual(fields["REDIRECT_FOLLOWING"]["value"], "DISABLED")
        for name in gate().MUST_MATCH_FIELDS:
            with self.subTest(field=name):
                self.assertEqual(fields[name]["classification"], "MUST_MATCH")

    def test_the_field_that_would_have_broken_it_silently_is_named(self):
        text = load(CONSTRUCTS)["request_comparability"][
            "the_field_that_would_have_broken_it_silently"
        ]
        self.assertIn("REDIRECT_FOLLOWING", text)


class TestThePriorityDeltaIsHonest(unittest.TestCase):
    def setUp(self):
        self.delta = load(DECISION_V6)["priority_delta"]

    def test_all_five_criteria_were_compared(self):
        recorded = {row["criterion"] for row in self.delta["comparison"]}
        self.assertEqual(recorded, set(gate().DELTA_CRITERIA))

    def test_the_1_76_priority_was_narrowed_and_not_overturned(self):
        self.assertFalse(self.delta["mission_1_76_priority_overturned"])
        self.assertTrue(self.delta["mission_1_76_priority_narrowed"])
        self.assertIn("executable", self.delta["why"])

    def test_no_broad_portfolio_research_was_rerun(self):
        self.assertFalse(self.delta["broad_portfolio_research_rerun"])

    def test_it_quotes_mission_1_76_correctly(self):
        prior = load(PRIORITY)
        self.assertEqual(
            self.delta["what_mission_1_76_recorded"]["selected"],
            prior["selection"]["selected_candidate"],
        )
        self.assertFalse(prior["globalping_dependency"]["selectable_now"])

    def test_the_http_route_wins_on_independence_and_loses_on_readiness(self):
        by = {row["criterion"]: row["favours"] for row in self.delta["comparison"]}
        self.assertEqual(by["ESTABLISHED_INDEPENDENCE_POTENTIAL"], "HTTP")
        self.assertEqual(by["CONTRADICTION_POTENTIAL"], "HTTP")
        self.assertEqual(by["EXECUTION_READINESS"], "M1")
        self.assertEqual(by["SCORABILITY_REPAIR"], "M1")


class TestNothingRanAndNothingWasPromoted(unittest.TestCase):
    def setUp(self):
        self.decision = load(DECISION_V6)
        self.constructs = load(CONSTRUCTS)

    def test_every_outward_and_canonical_counter_is_zero(self):
        accounting = self.decision["mission_accounting"]
        for counter in gate().HARD_ZERO:
            with self.subTest(counter=counter):
                self.assertEqual(accounting[counter], 0)

    def test_independence_is_capability_and_not_a_judgement(self):
        independence = self.constructs["independence"]
        self.assertEqual(independence["state"], "INDEPENDENCE_ARCHITECTURALLY_CAPABLE")
        self.assertEqual(independence["groups_created"], 0)

    def test_product_relevance_is_bounded_and_the_promotion_is_refused(self):
        relevance = self.constructs["product_relevance"]
        self.assertIn("MODERATE", relevance["honest_bound"])
        self.assertIn("WTP", relevance["promotion_refused"])

    def test_the_next_action_authorises_neither_a_freeze_nor_a_run(self):
        action = self.decision["recommended_next_action"]
        self.assertFalse(action["corpus_freeze_authorized"])
        self.assertFalse(action["run_authorized"])
        self.assertTrue(action["mission_1_77_not_started"])
        self.assertFalse(action["not_selected_by_this_mission"] is False)

    def test_the_refused_outcomes_each_say_why(self):
        refused = self.decision["outcomes_considered_and_refused"]
        self.assertGreaterEqual(len(refused), 4)
        for entry in refused:
            with self.subTest(outcome=entry["outcome"]):
                self.assertTrue(entry["refused_because"].strip())


class TestTheGateRefusesTheShortcuts(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.selected = load(SELECTED)
        self.decision = load(DECISION_V6)
        self.constructs = load(CONSTRUCTS)

    def refused(self, checker, *args):
        with self.assertRaises(self.gate.ValidationError):
            checker(*args)

    def test_the_records_as_committed_pass(self):
        self.gate.validate()

    def test_a_selection_that_authorises_a_run_is_refused(self):
        selected = copy.deepcopy(self.selected)
        selected["states_kept_apart"]["RUN_AUTHORIZED"] = True
        self.refused(self.gate._check_three_states_stay_apart, selected, self.decision)

    def test_a_selection_that_freezes_a_corpus_is_refused(self):
        selected = copy.deepcopy(self.selected)
        selected["corpus_frozen"] = True
        self.refused(self.gate._check_three_states_stay_apart, selected, self.decision)

    def test_a_selection_whose_premise_has_gone_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["counterpart_qualified"] = False
        self.refused(self.gate._check_the_premise_still_holds, decision)

    def test_a_construct_selected_anyway_is_refused(self):
        constructs = copy.deepcopy(self.constructs)
        constructs["selected_construct"] = "CANDIDATE_A"
        self.refused(self.gate._check_no_construct_was_selected_and_vantage_is_open, constructs)

    def test_choosing_a_vantage_semantics_silently_is_refused(self):
        for resolution in self.gate.VANTAGE_RESOLUTIONS:
            with self.subTest(resolution=resolution):
                constructs = copy.deepcopy(self.constructs)
                constructs["vantage"]["which_was_chosen"] = resolution
                self.refused(
                    self.gate._check_no_construct_was_selected_and_vantage_is_open, constructs
                )

    def test_treating_vantage_divergence_as_noise_is_refused(self):
        constructs = copy.deepcopy(self.constructs)
        constructs["vantage"]["the_finding"] = "VANTAGE_IS_MEASUREMENT_NOISE"
        self.refused(self.gate._check_no_construct_was_selected_and_vantage_is_open, constructs)

    def test_a_corpus_aggregate_denominator_is_refused(self):
        constructs = copy.deepcopy(self.constructs)
        constructs["proposition_shape"]["preferred"] = "CORPUS_RATE"
        self.refused(self.gate._check_the_denominator_is_never_outcome_selected, constructs)

    def test_removing_a_target_from_the_population_is_refused(self):
        constructs = copy.deepcopy(self.constructs)
        constructs["missingness"]["targets_removed_from_N_for_any_outcome"] = 1
        self.refused(self.gate._check_the_denominator_is_never_outcome_selected, constructs)

    def test_pushing_a_categorical_predicate_through_the_threshold_is_refused(self):
        constructs = copy.deepcopy(self.constructs)
        constructs["evaluator_compatibility"]["fits_a_target_level_http_predicate"] = True
        self.refused(self.gate._check_the_evaluator_gap_is_reported_not_routed_around, constructs)

    def test_a_differing_path_or_query_is_refused(self):
        for field in ("PATH", "QUERY", "METHOD", "REDIRECT_FOLLOWING"):
            with self.subTest(field=field):
                constructs = copy.deepcopy(self.constructs)
                for row in constructs["request_comparability"]["fields"]:
                    if row["field"] == field:
                        row["classification"] = "MAY_DIFFER_AS_APPARATUS_METHOD"
                self.refused(
                    self.gate._check_the_evaluator_gap_is_reported_not_routed_around, constructs
                )

    def test_claiming_the_1_76_priority_was_overturned_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["priority_delta"]["mission_1_76_priority_overturned"] = True
        self.refused(self.gate._check_the_priority_delta_is_honest, decision)

    def test_promoting_independence_is_refused(self):
        constructs = copy.deepcopy(self.constructs)
        constructs["independence"]["state"] = "INDEPENDENCE_ESTABLISHED"
        self.refused(self.gate._check_nothing_ran, self.decision, self.selected, constructs)

    def test_any_nonzero_counter_is_refused(self):
        for counter in self.gate.HARD_ZERO:
            with self.subTest(counter=counter):
                decision = copy.deepcopy(self.decision)
                decision["mission_accounting"][counter] = 1
                self.refused(self.gate._check_nothing_ran, decision, self.selected, self.constructs)

    def test_a_missing_field_is_a_refusal_rather_than_a_crash(self):
        self.assertIn('ValidationError(f"the records do not carry', RENDERER.read_text("utf-8"))


class TestTheRendererAndGovernance(unittest.TestCase):
    def test_the_renderer_reaches_no_network(self):
        source = RENDERER.read_text(encoding="utf-8")
        for banned in ("requests", "httpx", "urllib", "socket", "subprocess"):
            with self.subTest(module=banned):
                self.assertNotIn(f"import {banned}", source)

    def test_the_page_reports_the_class_and_the_absent_construct(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Do not edit by hand", text)
        self.assertIn("Q1", text)
        self.assertIn("CLASS_SELECTED", text)
        self.assertIn("Vantage is what stops all three", text)

    def test_ci_runs_the_gate(self):
        self.assertIn(RENDERER.name, CI.read_text(encoding="utf-8"))

    def test_the_manifest_lists_the_new_records(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for path in (SELECTED, CONSTRUCTS, RENDERER):
            with self.subTest(record=path.name):
                self.assertIn(path.name, text)

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "reports" / "mission-1.76.6-report.md").exists())


if __name__ == "__main__":
    unittest.main()
