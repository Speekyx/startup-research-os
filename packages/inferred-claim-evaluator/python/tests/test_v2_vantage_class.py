"""Mission 1.76.7. V2 is sound for refutation and out of reach for support.

Four things this file defends.

THE CLASS IS DEFINED BEFORE THE RUN AND WITHOUT NAMING AN APPARATUS. A frame chosen from what
answered is Mission 1.70's failure arriving one layer up.

A SINGLETON CLASS IS NOT A UNIVERSAL. It is the proposition with a vantage qualifier attached,
which is the V1 the operator rejected -- so any class of cardinality one collapses V2 into it.

ONE POSITIVE MEMBER DOES NOT SUPPORT A UNIVERSAL, and for an abstract-member class it does not
even establish its own member.

THE SHORTFALL IS STATED, NOT HIDDEN. Globalping is qualified and the support half is still out
of reach, and the limit is the logical form rather than the size of the fleet.
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

DECISION = DATA / "v2-vantage-class-decision-v1.json"
CONSTRUCTS = DATA / "http-construct-candidate-evaluation-v1.json"
SELECTED = DATA / "selected-quantity-class-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v4.json"
RENDERER = SCRIPTS / "render_v2_vantage_class.py"
PAGE = DATA / "v2-vantage-class-decision-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_v2_vantage_class", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheOperatorDecisionIsATransition(unittest.TestCase):
    def setUp(self):
        self.operator = load(DECISION)["operator_decision"]

    def test_v2_was_selected_and_only_the_semantic_model(self):
        self.assertEqual(self.operator["decision"], "V2")
        self.assertEqual(self.operator["what_the_decision_selects"], "THE_SEMANTIC_MODEL_ONLY")
        self.assertIn("a construct", self.operator["what_it_does_not_select"])

    def test_both_rejections_carry_their_reasons(self):
        self.assertIn("distinct propositions", self.operator["v1_rejected_because"])
        self.assertIn("noise", self.operator["v3_rejected_because"])

    def test_mission_1_76_6_still_records_that_it_chose_nothing(self):
        """It offered three resolutions and chose none, which was true at its completion."""
        self.assertFalse(self.operator["mission_1_76_6_rewritten"])
        constructs = load(CONSTRUCTS)
        self.assertIsNone(constructs["vantage"]["which_was_chosen"])
        self.assertIsNone(constructs["selected_construct"])


class TestTheClassesAreFrameIndependent(unittest.TestCase):
    def setUp(self):
        self.classes = {c["class_id"]: c for c in load(DECISION)["candidate_classes"]}

    def test_three_shapes_were_evaluated(self):
        self.assertEqual(tuple(self.classes), gate().REQUIRED_CLASSES)

    def test_every_class_is_finite_and_decidable_before_the_run(self):
        for class_id, candidate in self.classes.items():
            with self.subTest(class_id=class_id):
                self.assertTrue(candidate["finite_before_run"])
                self.assertTrue(candidate["membership_decidable_before_run"])

    def test_no_membership_rule_is_written_in_terms_of_what_answered(self):
        import re

        for class_id, candidate in self.classes.items():
            for pattern in gate().FORBIDDEN_MEMBERSHIP:
                with self.subTest(class_id=class_id, pattern=pattern):
                    self.assertIsNone(
                        re.search(pattern, candidate["membership_rule"], re.IGNORECASE)
                    )

    def test_the_singleton_class_is_refused_twice_over(self):
        singleton = self.classes["VC_B_SINGLETON_OPERATOR_VANTAGE"]
        self.assertFalse(singleton["apparatus_independent_definition"])
        self.assertTrue(singleton["frame_inside_definition"])
        self.assertEqual(singleton["semantic_verdict"], "REFUSED_TWICE_OVER")
        self.assertIn("V1", singleton["why_refused"])

    def test_the_two_independent_classes_are_genuinely_independent(self):
        for class_id in (
            "VC_A_EXTERNAL_GEOGRAPHIC_TUPLE_SET",
            "VC_C_EXTERNALLY_ENUMERATED_CONCRETE_VANTAGES",
        ):
            with self.subTest(class_id=class_id):
                self.assertTrue(self.classes[class_id]["apparatus_independent_definition"])
                self.assertFalse(self.classes[class_id]["frame_inside_definition"])


class TestTheDilemma(unittest.TestCase):
    def setUp(self):
        self.dilemma = load(DECISION)["the_dilemma"]

    def test_abstract_members_are_sampled_and_concrete_members_name_an_apparatus(self):
        self.assertIn("ABSTRACT", self.dilemma["statement"])
        self.assertIn("CONCRETE", self.dilemma["statement"])
        self.assertIn("SAMPLED", self.dilemma["statement"])

    def test_it_is_not_a_topology_problem(self):
        """The limit survives any fleet size, which is why outcome D is refused."""
        self.assertFalse(self.dilemma["is_this_a_topology_problem"])
        self.assertIn("fleet", self.dilemma["why_not"])
        self.assertIn("does not fix", self.dilemma["consequence_for_outcome_d"])


class TestTheSupportSemantics(unittest.TestCase):
    def setUp(self):
        self.models = load(DECISION)["support_models"]

    def test_partial_positive_support_is_refused(self):
        u3 = self.models["U3_PARTIAL_POSITIVE_SUPPORT"]
        self.assertFalse(u3["selected"])
        self.assertFalse(u3["logically_sound"])
        self.assertIn("not evidence for a universal", u3["why_refused"])

    def test_pooling_across_apparatuses_does_not_solve_independence(self):
        u2 = self.models["U2_MEMBER_EVIDENCE_PLUS_DETERMINISTIC_DERIVATION"]
        self.assertFalse(u2["solves_the_independence_goal"])
        self.assertIn("pooled", u2["why_not"].lower())

    def test_exactly_one_model_is_selected_and_it_is_the_sound_one(self):
        selected = [name for name, model in self.models.items() if model["selected"]]
        self.assertEqual(selected, ["U1_COMPLETE_CLASS_WITNESS"])
        self.assertTrue(self.models["U1_COMPLETE_CLASS_WITNESS"]["logically_sound"])

    def test_the_selected_model_is_recorded_as_unattainable(self):
        """Selecting the truthful model and recording that it cannot be met is the honest
        pair; selecting an attainable but false one would not be."""
        u1 = self.models["U1_COMPLETE_CLASS_WITNESS"]
        self.assertFalse(u1["attainable_here"])
        self.assertTrue(u1["why_selected_despite_being_unattainable"].strip())


class TestMissingnessIsNeverRefutation(unittest.TestCase):
    def setUp(self):
        self.refutation = load(DECISION)["refutation_semantics"]

    def test_refutation_is_sound_from_one_in_scope_counterexample(self):
        self.assertTrue(self.refutation["sound"])
        self.assertIn("predicate-false", self.refutation["rule"])
        self.assertIn("inside a member of V", self.refutation["rule"])

    def test_all_five_missingness_states_are_kept_apart(self):
        for state in gate().NOT_REFUTATION:
            with self.subTest(state=state):
                self.assertIn(state, self.refutation["states_that_are_not_refutation"])

    def test_two_refutations_agree_and_the_record_says_so(self):
        self.assertTrue(self.refutation["both_apparatuses_can_refute"])
        self.assertIn("AGREE", self.refutation["but"])


class TestTheApparatusRealityWasReadNotAssumed(unittest.TestCase):
    def setUp(self):
        self.reality = load(DECISION)["apparatus_vantage_reality"]

    def test_the_fetcher_has_one_vantage_and_was_not_redesigned(self):
        sros = self.reality["sros"]
        self.assertEqual(sros["capability"], "SINGLE_DEPLOYMENT_VANTAGE")
        self.assertEqual(sros["cardinality_of_vantages_it_can_occupy_in_one_run"], 1)
        self.assertFalse(sros["multi_vantage_today"])
        self.assertFalse(sros["redesigned_by_this_mission"])
        self.assertIn("one machine", sros["basis"])

    def test_the_provider_selection_semantics_come_from_the_qualification(self):
        globalping = self.reality["globalping"]
        self.assertEqual(globalping["capability"], "MULTIPLE_SELECTABLE_VANTAGES")
        self.assertTrue(globalping["selection_semantics_established"])
        self.assertIn("C7", globalping["basis"])

    def test_no_probe_availability_was_checked(self):
        self.assertFalse(self.reality["globalping"]["current_availability_checked"])

    def test_the_qualification_still_supports_the_analysis(self):
        self.assertEqual(load(QUALIFICATION)["verdict"], "COUNTERPART_RESOLVED")


class TestTheShortfallIsStated(unittest.TestCase):
    def setUp(self):
        self.independence = load(DECISION)["dual_apparatus_independence"]

    def test_neither_apparatus_can_independently_support_the_universal(self):
        self.assertFalse(self.independence["sros_can_independently_support_v2"])
        self.assertFalse(self.independence["globalping_can_independently_support_v2"])
        self.assertIn("sample", self.independence["why_globalping_cannot_either"])

    def test_dual_support_and_contradiction_are_both_unreachable(self):
        self.assertFalse(self.independence["dual_independent_support_reachable"])
        self.assertFalse(self.independence["contradiction_reachable"])
        self.assertIn("SUPPORTS", self.independence["why_contradiction_is_not_reachable"])

    def test_what_v2_does_deliver_is_recorded_too(self):
        delivered = self.independence["what_v2_does_deliver"]
        self.assertGreaterEqual(len(delivered), 3)
        self.assertTrue(any("refutation" in item for item in delivered))

    def test_the_calibration_goal_shortfall_is_named(self):
        self.assertIn("calibration", self.independence["what_it_does_not_deliver"])

    def test_no_new_evidence_direction_member_is_proposed(self):
        contract = load(DECISION)["evidence_direction_contract"]
        self.assertFalse(contract["new_evidence_direction_member_required"])
        self.assertIn("refusal store", contract["smallest_required_extension"])


class TestNothingWasSelectedOrRun(unittest.TestCase):
    def setUp(self):
        self.decision = load(DECISION)

    def test_no_class_construct_corpus_or_measurement(self):
        self.assertFalse(self.decision["exact_predicate_frozen"])
        self.assertFalse(self.decision["corpus_frozen"])
        self.assertEqual(self.decision["measurements_executed"], 0)
        self.assertFalse((DATA / "selected-construct-v1.json").exists())

    def test_the_class_selection_was_not_promoted(self):
        states = load(SELECTED)["states_kept_apart"]
        self.assertTrue(states["CLASS_SELECTED"])
        self.assertFalse(states["CONSTRUCT_SELECTED"])
        self.assertFalse(states["RUN_AUTHORIZED"])

    def test_the_worked_example_names_no_target(self):
        example = self.decision["worked_semantic_test_case"]
        self.assertFalse(example["target_named"])
        self.assertFalse(example["construct_selected"])
        self.assertFalse(example["request_contract_frozen"])

    def test_target_level_was_not_reopened(self):
        self.assertFalse(self.decision["target_level_preserved"]["reopened_corpus_aggregate"])

    def test_every_counter_is_zero(self):
        accounting = self.decision["mission_accounting"]
        for counter in gate().HARD_ZERO:
            with self.subTest(counter=counter):
                self.assertEqual(accounting[counter], 0)

    def test_the_next_action_authorises_nothing(self):
        action = self.decision["recommended_next_action"]
        self.assertFalse(action["corpus_freeze_authorized"])
        self.assertFalse(action["run_authorized"])
        self.assertTrue(action["mission_1_77_not_started"])
        self.assertTrue(action["mission_1_76_8_not_recommended_yet"])


class TestTheGateRefusesTheShortcuts(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.decision = load(DECISION)

    def refused(self, checker, *args):
        with self.assertRaises(self.gate.ValidationError):
            checker(*args)

    def test_the_record_as_committed_passes(self):
        self.gate.validate()

    def test_a_class_defined_by_what_answered_is_refused(self):
        for rule in (
            "the probes currently online",
            "the vantages both apparatuses successfully measured",
            "the vantages from which the target responded",
            "the vantages for which the predicate is evaluable",
        ):
            with self.subTest(rule=rule):
                decision = copy.deepcopy(self.decision)
                decision["candidate_classes"][0]["membership_rule"] = rule
                self.refused(self.gate._check_the_classes_are_frame_independent, decision)

    def test_a_class_not_decidable_before_the_run_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["candidate_classes"][0]["membership_decidable_before_run"] = False
        self.refused(self.gate._check_the_classes_are_frame_independent, decision)

    def test_an_apparatus_defined_class_that_is_not_refused_is_refused(self):
        decision = copy.deepcopy(self.decision)
        for candidate in decision["candidate_classes"]:
            if candidate["class_id"] == "VC_B_SINGLETON_OPERATOR_VANTAGE":
                candidate["semantic_verdict"] = "VALID"
        self.refused(self.gate._check_the_classes_are_frame_independent, decision)

    def test_partial_positive_support_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["support_models"]["U3_PARTIAL_POSITIVE_SUPPORT"]["selected"] = True
        self.refused(self.gate._check_the_support_semantics_are_truthful, decision)

    def test_pooling_claimed_to_solve_independence_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["support_models"]["U2_MEMBER_EVIDENCE_PLUS_DETERMINISTIC_DERIVATION"][
            "solves_the_independence_goal"
        ] = True
        self.refused(self.gate._check_the_support_semantics_are_truthful, decision)

    def test_missingness_admitted_as_refutation_is_refused(self):
        for state in self.gate.NOT_REFUTATION:
            with self.subTest(state=state):
                decision = copy.deepcopy(self.decision)
                decision["refutation_semantics"]["states_that_are_not_refutation"] = [
                    s
                    for s in decision["refutation_semantics"]["states_that_are_not_refutation"]
                    if s != state
                ]
                self.refused(self.gate._check_missingness_is_never_refutation, decision)

    def test_crediting_the_fetcher_with_several_vantages_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["apparatus_vantage_reality"]["sros"][
            "cardinality_of_vantages_it_can_occupy_in_one_run"
        ] = 5
        self.refused(self.gate._check_the_apparatus_reality_was_read_not_assumed, decision)

    def test_checking_probe_availability_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["apparatus_vantage_reality"]["globalping"]["current_availability_checked"] = True
        self.refused(self.gate._check_the_apparatus_reality_was_read_not_assumed, decision)

    def test_claiming_dual_support_while_an_apparatus_cannot_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["dual_apparatus_independence"]["dual_independent_support_reachable"] = True
        self.refused(self.gate._check_the_independence_finding_is_not_hidden, decision)

    def test_claiming_contradiction_with_no_admissible_support_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["dual_apparatus_independence"]["contradiction_reachable"] = True
        self.refused(self.gate._check_the_independence_finding_is_not_hidden, decision)

    def test_recording_the_limit_as_a_topology_problem_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["the_dilemma"]["is_this_a_topology_problem"] = True
        self.refused(self.gate._check_the_independence_finding_is_not_hidden, decision)

    def test_backdating_the_predecessor_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["operator_decision"]["mission_1_76_6_rewritten"] = True
        self.refused(self.gate._check_the_operator_decision_is_a_transition, decision)

    def test_the_ready_outcome_with_support_unreachable_is_refused(self):
        decision = copy.deepcopy(self.decision)
        decision["primary_outcome"] = "V2_VANTAGE_CLASS_CONTRACT_READY_FOR_CONSTRUCT_SELECTION"
        self.refused(self.gate._check_the_outcome, decision)

    def test_a_missing_field_is_a_refusal_rather_than_a_crash(self):
        self.assertIn('ValidationError(f"the records do not carry', RENDERER.read_text("utf-8"))


class TestTheReadyOutcomeStaysExpressible(unittest.TestCase):
    """INVERTED. A gate that could only express this mission's negative would decide the next
    mission by refusing its positive."""

    def test_a_pair_that_could_reach_ready_validates(self):
        module = gate()
        decision = copy.deepcopy(load(DECISION))
        decision["dual_apparatus_independence"].update(
            sros_can_independently_support_v2=True,
            globalping_can_independently_support_v2=True,
            dual_independent_support_reachable=True,
            contradiction_reachable=True,
        )
        decision["primary_outcome"] = "V2_VANTAGE_CLASS_CONTRACT_READY_FOR_CONSTRUCT_SELECTION"
        module._check_the_independence_finding_is_not_hidden(decision)
        module._check_the_outcome(decision)


class TestTheRendererAndGovernance(unittest.TestCase):
    def test_the_renderer_reaches_no_network(self):
        source = RENDERER.read_text(encoding="utf-8")
        for banned in ("requests", "httpx", "urllib", "socket", "subprocess"):
            with self.subTest(module=banned):
                self.assertNotIn(f"import {banned}", source)

    def test_the_page_reports_the_outcome_and_the_shortfall(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Do not edit by hand", text)
        self.assertIn("V2_VALID_FOR_REFUTATION_BUT_NOT_INDEPENDENT_SUPPORT", text)
        self.assertIn("The dilemma", text)
        self.assertIn("What it does not", text)

    def test_ci_runs_the_gate(self):
        self.assertIn(RENDERER.name, CI.read_text(encoding="utf-8"))

    def test_the_manifest_lists_the_record_and_the_renderer(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for path in (DECISION, RENDERER):
            with self.subTest(record=path.name):
                self.assertIn(path.name, text)

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "reports" / "mission-1.76.7-report.md").exists())


if __name__ == "__main__":
    unittest.main()
