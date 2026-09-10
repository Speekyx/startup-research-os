"""Mission 1.83. The transmission gate for the already-selected subject, prepared and not taken.

Four things this file defends.

THE REVIEW ANSWERS ONE QUESTION. One source, one use profile, one activity, one processing
purpose taken from the vocabulary that already had one, one selected subject. The commercial
profile, redistribution, customer access, training, fine-tuning and embeddings are recorded as
out of scope and none of them is proposed as permitted.

THE FOUR GATES STAY FOUR. A model may read this material, the profile permits this class of
egress, the provider posture is approved on its own contract text, and whether the material may
LEAVE was never asked. No vendor is named in anything that would become a source condition, and
a provider approval is not a source permission in either direction.

WHAT WOULD LEAVE IS MEASURED, NOT DESCRIBED. The payload was reconstructed through the current
deterministic path and serialized by the production function; it satisfies the allowlist, was
not trimmed, and carries no personal data, no raw notice, no notice body and no API response.
The character count was recomputed rather than carried forward, and it changed.

NOBODY APPROVED ANYTHING. No source review appended, no reviewer recorded, no option defaulted,
no approval inside the frozen packet, and a digest that recomputes from the packet's own bound
fields.
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

REVIEW = DATA / "ted-selected-candidate-egress-review-v1.json"
PACKET = DATA / "ted-selected-candidate-egress-decision-packet-v1.json"
PREPARATION = DATA / "opportunity-preparation-v4.json"
SEMANTICS = DATA / "procurement-subject-semantics-class-grain-v1.json"
GATE = SCRIPTS / "render_ted_selected_candidate_egress.py"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

SUBJECT = "ted-eu:CPV-class:9261"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_ted_selected_candidate_egress", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheScope(unittest.TestCase):
    def setUp(self):
        self.record = load(REVIEW)

    def test_one_source_one_profile_one_activity_one_subject(self):
        scope = self.record["scope"]
        self.assertEqual(scope["source_id"], "ted-eu")
        self.assertEqual(scope["use_profile_id"], "local-private-research-v1")
        self.assertEqual(scope["activity"], "external_model_transmission")
        self.assertEqual(scope["selected_subject"], SUBJECT)

    def test_the_purpose_is_the_one_the_vocabulary_already_had(self):
        purpose = self.record["scope"]["processing_purpose"]
        self.assertEqual(purpose, "bounded external inference for Opportunity hypothesis synthesis")
        governance = (DATA / "opportunity-synthesis-egress-governance-v1.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(purpose, governance)

    def test_the_commercial_profile_does_not_inherit_this_review(self):
        outside = self.record["scope"]["explicitly_out_of_scope"]
        self.assertIn("commercial-multi-tenant-research-v1", outside)
        for widening in ("public redistribution", "resale", "model training", "embeddings"):
            self.assertIn(widening, outside)


class TestTheFourGates(unittest.TestCase):
    def setUp(self):
        self.gates = load(REVIEW)["four_gates"]

    def test_three_are_open_and_the_one_that_refuses_was_never_asked(self):
        self.assertEqual(self.gates["gates_open"], 3)
        self.assertEqual(self.gates["gates_refusing"], 1)
        self.assertEqual(self.gates["may_it_leave_this_deployment"]["state"], "NOT_ASSESSED")
        self.assertEqual(self.gates["may_a_model_read_this_material"]["state"], "PERMITTED")
        self.assertEqual(self.gates["what_does_the_processor_do_with_it"]["state"], "APPROVED")
        self.assertEqual(
            self.gates["does_this_deployment_permit_that_class_of_egress"]["state"],
            "PERMITTED_TO_APPROVED_PROVIDERS",
        )

    def test_each_gate_names_the_field_and_the_document_that_decides_it(self):
        for name, entry in self.gates.items():
            if not isinstance(entry, dict) or "field" not in entry:
                continue
            self.assertTrue(str(entry["where"]).strip(), name)
            self.assertTrue(str(entry["bound"]).strip(), name)

    def test_the_provider_question_is_answered_by_the_provider_register(self):
        where = self.gates["what_does_the_processor_do_with_it"]["where"]
        self.assertTrue(where.startswith("docs/data/model-provider-policy-v1.json"))
        policy = load(DATA / "model-provider-policy-v1.json")
        postures = {p["provider_id"]: p["posture"] for p in policy["providers"]}
        self.assertEqual(postures["anthropic"], "APPROVED")

    def test_no_vendor_is_named_in_anything_that_would_become_a_condition(self):
        module = gate()
        conditions = " ".join(load(PACKET)["CONDITIONS"]).lower()
        for vendor in module.VENDOR_NAMES:
            self.assertNotIn(vendor, conditions)

    def test_the_profile_permits_this_class_of_egress_and_not_training(self):
        catalog = load(DATA / "source-catalog-v1.json")
        profile = next(
            p for p in catalog["use_profiles"] if p["use_profile_id"] == "local-private-research-v1"
        )
        self.assertEqual(profile["external_model_egress"], "PERMITTED_TO_APPROVED_PROVIDERS")
        self.assertTrue(profile["model_inference"])
        self.assertFalse(profile["model_training"])
        self.assertFalse(profile["embeddings"])


class TestWhatWouldLeave(unittest.TestCase):
    def setUp(self):
        self.rep = load(REVIEW)["representation"]

    def test_it_is_the_current_preparation_packet(self):
        packets = {p["subject"]: p for p in load(PREPARATION)["packets"]}
        live = packets[SUBJECT]
        self.assertEqual(self.rep["PACKET_ID"], live["packet_id"])
        self.assertEqual(self.rep["EVIDENCE_COUNT"], live["size"])
        self.assertEqual(self.rep["EVIDENCE_COUNT"], 6)
        self.assertEqual(self.rep["CLAIM_COUNT"], 5)

    def test_the_payload_satisfies_its_own_contract_and_was_not_trimmed(self):
        self.assertTrue(self.rep["ALLOWLIST_VALID"])
        self.assertEqual(self.rep["REPRESENTATION_VIOLATIONS"], 0)
        self.assertFalse(self.rep["trimmed_to_pass"])
        self.assertEqual(
            self.rep["REPRESENTATION_SCHEMA"], "opportunity-transmission-representation@1.0.0"
        )

    def test_the_keys_are_the_nine_the_allowlist_names(self):
        """The identity with the production constant is asserted in the opportunity-engine suite.

        This package does not depend on `sros_opportunity`, and widening the zero-dependency
        runner to make the import work would delete the boundary the runner exists to check.
        """
        self.assertEqual(
            set(self.rep["TOP_LEVEL_KEYS"]),
            {
                "packet_id",
                "subject",
                "procedures",
                "source_families",
                "dimensions",
                "dimension_bounds",
                "independence",
                "claims",
                "evidence_ids",
            },
        )

    def test_the_payload_carries_the_code_and_not_the_retrieved_label(self):
        self.assertIsNone(self.rep["SUBJECT_LABEL_IN_PAYLOAD"])
        self.assertEqual(self.rep["SUBJECT_KEY"], SUBJECT)

    def test_the_live_gate_refuses_and_names_the_field(self):
        self.assertEqual(self.rep["REAL_GATE_AVAILABILITY"], "UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS")
        reasons = " ".join(self.rep["REAL_GATE_REFUSAL_REASONS"])
        self.assertIn("external_model_transmission is NOT_ASSESSED", reasons)
        self.assertIn("not a prohibition", reasons)

    def test_the_character_count_was_recomputed_and_it_changed(self):
        recomputed = self.rep["mission_1_82_diagnostic_recomputed"]
        self.assertEqual(recomputed["characters_now"], self.rep["SERIALIZED_CHARACTER_COUNT"])
        self.assertNotEqual(recomputed["characters_now"], recomputed["characters_then"])
        self.assertTrue(str(recomputed["why_the_character_count_differs"]).strip())
        self.assertFalse(recomputed["mission_1_82_record_corrected"])

    def test_the_earlier_record_still_says_what_it_measured(self):
        semantics = load(SEMANTICS)
        self.assertEqual(semantics["representation_check"]["packets"][SUBJECT]["characters"], 3252)


class TestPersonalData(unittest.TestCase):
    def setUp(self):
        self.scan = load(REVIEW)["personal_data"]

    def test_nothing_of_any_class_is_present(self):
        module = gate()
        for field in (
            "PERSONAL_DATA_FIELDS",
            "RAW_SOURCE_PAYLOAD_FIELDS",
            "NOTICE_BODY_FIELDS",
            "SOURCE_API_PAYLOAD_FIELDS",
        ):
            self.assertEqual(self.scan[field], 0, field)
        for cls in module.PERSONAL_DATA_CLASSES:
            self.assertEqual(self.scan[cls], 0, cls)

    def test_nothing_was_stripped_to_get_there(self):
        self.assertFalse(self.scan["stripping_performed"])

    def test_an_organisation_is_not_treated_as_a_natural_person(self):
        self.assertTrue(str(self.scan["organisation_is_not_a_natural_person"]).strip())


class TestTheAuthority(unittest.TestCase):
    def setUp(self):
        self.held = load(REVIEW)["held_authority"]

    def test_the_question_is_partly_answered_and_nothing_was_fetched(self):
        self.assertEqual(
            self.held["IS_THE_CURRENT_QUESTION_ALREADY_ANSWERED_BY_HELD_AUTHORITY"], "PARTIAL"
        )
        self.assertEqual(self.held["NEW_DOCUMENTATION_FETCHES"], 0)
        self.assertEqual(self.held["RESEARCH_DATA_FETCHES"], 0)

    def test_every_cited_document_says_what_it_does_not_establish(self):
        self.assertEqual(self.held["HELD_AUTHORITY_COUNT"], len(self.held["documents"]))
        for document in self.held["documents"]:
            self.assertIn(document["bears_on_this_question"], ("YES", "NO", "PARTIAL"))
            self.assertTrue(str(document["what_it_does_not_establish"]).strip())

    def test_the_instrument_names_no_act_and_that_is_measured(self):
        scan = self.held["mechanical_scan_of_the_held_decision_text"]
        for term in ("processor", "transmit", "transfer", "automated"):
            self.assertEqual(scan[term], 0, term)
        self.assertEqual(scan["third_party"], 2)
        self.assertIn("intellectual-property exclusion", scan["third_party_context"])

    def test_no_argument_is_recorded_as_sufficient_alone(self):
        record = load(REVIEW)
        self.assertTrue(record["arguments_toward_permission"])
        for argument in record["arguments_toward_permission"]:
            self.assertFalse(argument["sufficient_alone"], argument["id"])
            self.assertTrue(str(argument["why_not"]).strip())
            self.assertTrue(str(argument["authority"]).strip())

    def test_the_operator_acceptance_is_the_residual_that_only_they_can_close(self):
        defeats = {item["id"]: item for item in load(REVIEW)["what_defeats_mechanical_closure"]}
        self.assertIn("B1", defeats)
        self.assertEqual(defeats["B1"]["kind"], "SCOPE_OF_A_HUMAN_CONFIRMATION")
        self.assertIn("bounded quer", defeats["B1"]["statement"].lower())
        self.assertIn("operator", defeats["B1"]["closeable_by"])


class TestActivitiesAndPurpose(unittest.TestCase):
    def setUp(self):
        self.record = load(REVIEW)
        self.matrix = self.record["activity_matrix"]

    def test_every_activity_is_assessed_separately_and_none_changed(self):
        module = gate()
        for activity in module.REQUIRED_ACTIVITIES:
            self.assertIn(activity, self.matrix)
            self.assertFalse(self.matrix[activity]["changed"], activity)

    def test_an_inference_review_widens_neither_training_nor_embeddings(self):
        for activity in ("MODEL_TRAINING", "FINE_TUNING", "EMBEDDINGS"):
            entry = self.matrix[activity]
            self.assertEqual(entry["current"], entry["proposed"], activity)
            self.assertEqual(entry["proposed"], "NOT_ASSESSED", activity)
        boundary = self.record["inference_is_not_training"]
        self.assertFalse(boundary["MODEL_INFERENCE_and_MODEL_TRAINING_are_the_same_activity"])
        for field in (
            "an_inference_approval_would_widen_training",
            "an_inference_approval_would_widen_fine_tuning",
            "an_inference_approval_would_widen_embeddings",
        ):
            self.assertFalse(boundary[field], field)

    def test_it_grants_neither_redistribution_nor_customer_access(self):
        for activity in ("PUBLIC_REDISTRIBUTION", "CUSTOMER_FACING_SOURCE_DATA"):
            self.assertEqual(self.matrix[activity]["proposed"], "NOT_PERMITTED")

    def test_the_reviewed_activity_is_not_answered_here(self):
        entry = self.matrix["EXTERNAL_MODEL_TRANSMISSION"]
        self.assertEqual(entry["current"], "NOT_ASSESSED")
        self.assertNotIn(entry["proposed"], ("PERMITTED", "PERMITTED_WITH_CONDITIONS"))

    def test_a_permission_would_be_purpose_and_representation_bound(self):
        limit = self.record["purpose_limit"]
        self.assertEqual(limit["processing_purpose"], self.record["scope"]["processing_purpose"])
        self.assertEqual(
            limit["representation"], "bounded canonical subject and canonical Claims only"
        )
        self.assertIn("sent to models", limit["what_it_must_not_become"])


class TestAttributionAndDerivedOutput(unittest.TestCase):
    def setUp(self):
        self.record = load(REVIEW)

    def test_the_obligation_is_met_by_the_payload_and_not_injected(self):
        attribution = self.record["attribution"]
        self.assertTrue(attribution["ATTRIBUTION_REQUIRED"])
        self.assertTrue(attribution["already_satisfied_by_the_payload"])
        self.assertFalse(attribution["injected_into_the_packet_by_this_mission"])
        self.assertFalse(attribution["dropped_because_the_use_is_internal"])
        self.assertIn("6(2)(a)", attribution["obligation"])

    def test_derived_output_is_neither_unrestricted_nor_called_redistribution(self):
        derived = self.record["derived_output"]
        self.assertFalse(derived["is_it_unrestricted"])
        self.assertFalse(derived["is_it_redistribution_of_a_ted_database"])
        self.assertTrue(derived["DERIVED_OUTPUT_CONDITIONS"])
        joined = " ".join(derived["DERIVED_OUTPUT_CONDITIONS"])
        self.assertIn("6(2)(b)", joined)
        self.assertIn("DISTORT", joined)


class TestNobodyApproved(unittest.TestCase):
    def setUp(self):
        self.record = load(REVIEW)
        self.packet = load(PACKET)

    def test_no_review_was_appended_and_no_reviewer_recorded(self):
        judgement = self.record["human_judgement"]
        self.assertTrue(judgement["HUMAN_JUDGEMENT_REQUIRED"])
        self.assertFalse(judgement["SOURCE_REVIEW_APPENDED"])
        self.assertFalse(judgement["claude_recorded_as_reviewer"])
        self.assertFalse(judgement["impersonated_the_reviewer"])
        self.assertIn("INVESTIGATE", judgement["why_no_review_was_appended"])

    def test_the_packet_records_no_approval_and_defaults_no_option(self):
        self.assertFalse(self.packet["approval_recorded"])
        self.assertIsNone(self.packet["default_option"])
        offered = [option["option"] for option in self.packet["PROPOSED_DECISION_OPTIONS"]]
        self.assertEqual(sorted(offered), ["DEFER", "PERMIT_WITH_EXACT_CONDITIONS", "REFUSE"])
        for option in self.packet["PROPOSED_DECISION_OPTIONS"]:
            self.assertTrue(str(option["cost"]).strip(), option["option"])

    def test_the_permit_option_states_the_cost_of_appending_a_review(self):
        permit = next(
            option
            for option in self.packet["PROPOSED_DECISION_OPTIONS"]
            if option["option"] == "PERMIT_WITH_EXACT_CONDITIONS"
        )
        self.assertIn("orphans", permit["cost"])
        self.assertIn("records it again", permit["cost"])

    def test_the_digest_recomputes_from_the_packets_own_bound_fields(self):
        module = gate()
        self.assertEqual(self.packet["DECISION_PACKET_SHA256"], module.packet_digest(self.packet))
        self.assertEqual(
            self.record["decision_packet"]["DECISION_PACKET_SHA256"],
            self.packet["DECISION_PACKET_SHA256"],
        )

    def test_the_digest_moves_when_a_bound_field_moves(self):
        module = gate()
        before = module.packet_digest(self.packet)
        for field, value in (
            ("SUBJECT", "ted-eu:CPV-class:9252"),
            ("USE_PROFILE", "commercial-multi-tenant-research-v1"),
            ("REPRESENTATION_SHA256", "0" * 64),
            ("TRAINING", True),
        ):
            mutated = copy.deepcopy(self.packet)
            mutated[field] = value
            self.assertNotEqual(module.packet_digest(mutated), before, field)

    def test_the_digest_does_not_move_when_the_preparation_date_moves(self):
        module = gate()
        mutated = copy.deepcopy(self.packet)
        mutated["prepared_at"] = "2027-01-01"
        self.assertEqual(module.packet_digest(mutated), self.packet["DECISION_PACKET_SHA256"])

    def test_the_packet_names_the_measured_representation(self):
        rep = self.record["representation"]
        self.assertEqual(self.packet["REPRESENTATION_SHA256"], rep["REPRESENTATION_SHA256"])
        self.assertEqual(self.packet["PACKET_ID"], rep["PACKET_ID"])
        self.assertEqual(
            self.packet["REPRESENTATION_CHARACTER_COUNT"], rep["SERIALIZED_CHARACTER_COUNT"]
        )

    def test_the_packet_asserts_none_of_the_eight_negatives(self):
        for field in (
            "RAW_TED_PAYLOAD_INCLUDED",
            "PERSONAL_DATA_INCLUDED",
            "NOTICE_BODY_INCLUDED",
            "TRAINING",
            "FINE_TUNING",
            "EMBEDDINGS",
            "PUBLIC_REDISTRIBUTION",
            "CUSTOMER_SOURCE_DATA_ACCESS",
        ):
            self.assertFalse(self.packet[field], field)


class TestNothingElseMoved(unittest.TestCase):
    def setUp(self):
        self.record = load(REVIEW)

    def test_no_canonical_row_moved(self):
        state = self.record["canonical_state"]
        self.assertEqual(state["before"], state["after"])
        self.assertEqual(state["CANONICAL_RESEARCH_MUTATION"], 0)
        self.assertEqual(state["source_review_rows_written"], 0)
        self.assertEqual(state["condition_verification_rows_written"], 0)

    def test_no_model_no_acquisition_no_opportunity(self):
        accounting = self.record["mission_accounting"]
        for key, value in accounting.items():
            self.assertEqual(value, 0, key)

    def test_the_selected_candidate_did_not_move(self):
        candidate = self.record["selected_candidate_unchanged"]
        selection = load(SEMANTICS)["selection"]
        self.assertEqual(candidate["SELECTED_SUBJECT"], selection["SELECTED_SUBJECT"])
        self.assertEqual(candidate["SELECTED_LABEL"], selection["SELECTED_LABEL"])
        self.assertFalse(candidate["candidate_ranking_reopened"])
        self.assertFalse(candidate["descended_to_category_grain"])
        self.assertFalse(candidate["another_candidate_selected"])

    def test_the_evidence_still_establishes_what_it_established(self):
        semantics = self.record["evidence_semantics_unchanged"]
        self.assertEqual(
            semantics["supports"],
            ["BUYER_OR_BUDGET_EXISTENCE", "ECONOMIC_VALUE", "MARKET_ACTIVITY"],
        )
        self.assertEqual(semantics["claims_widened_by_this_mission"], 0)
        for forbidden in ("willingness to pay", "market size", "demand"):
            self.assertIn(forbidden, semantics["does_not_establish"])

    def test_the_parked_arc_is_preserved(self):
        parked = self.record["parked_states_preserved"]
        self.assertFalse(parked["changed_by_this_mission"])
        self.assertTrue(parked["q1"]["CLASS_SELECTED"])
        self.assertFalse(parked["q1"]["CONSTRUCT_SELECTED"])
        self.assertEqual(parked["globalping"]["PASS"], 12)


class TestTheGate(unittest.TestCase):
    def test_it_validates_and_renders_the_shipped_records(self):
        module = gate()
        record, packet = module.validate()
        self.assertEqual(
            module.render(record),
            (DATA / "ted-selected-candidate-egress-review-v1.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            module.render_packet(packet),
            (DATA / "ted-selected-candidate-egress-decision-packet-v1.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_the_outcome_is_one_of_the_seven(self):
        module = gate()
        self.assertIn(load(REVIEW)["primary_outcome"], module.ACCEPTABLE_OUTCOMES)
        self.assertEqual(
            load(REVIEW)["primary_outcome"], "TED_EGRESS_REVIEW_READY_FOR_OPERATOR_DECISION"
        )

    def test_a_mechanically_settled_permission_stays_expressible(self):
        """A gate that could only ever say 'ask a person' would misdescribe a future finding."""
        module = gate()
        record = load(REVIEW)
        record["held_authority"]["IS_THE_CURRENT_QUESTION_ALREADY_ANSWERED_BY_HELD_AUTHORITY"] = (
            "YES"
        )
        record["human_judgement"]["HUMAN_JUDGEMENT_REQUIRED"] = False
        record["what_defeats_mechanical_closure"] = []
        record["activity_matrix"]["EXTERNAL_MODEL_TRANSMISSION"]["proposed"] = (
            "PERMITTED_WITH_CONDITIONS"
        )
        record["activity_matrix"]["EXTERNAL_MODEL_TRANSMISSION"]["mechanical_basis"] = (
            "the publisher states the act in terms"
        )
        module._check_the_activity_matrix(record)
        module._check_the_arguments(record)

    def test_a_permission_reached_by_judgement_is_refused(self):
        module = gate()
        record = load(REVIEW)
        record["activity_matrix"]["EXTERNAL_MODEL_TRANSMISSION"]["proposed"] = "PERMITTED"
        with self.assertRaises(module.ValidationError):
            module._check_the_activity_matrix(record)

    def test_a_residual_beside_no_judgement_required_is_refused(self):
        module = gate()
        record = load(REVIEW)
        record["human_judgement"]["HUMAN_JUDGEMENT_REQUIRED"] = False
        with self.assertRaises(module.ValidationError):
            module._check_the_arguments(record)

    def test_the_gate_is_registered_in_ci(self):
        self.assertIn(
            "render_ted_selected_candidate_egress.py --check", CI.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
