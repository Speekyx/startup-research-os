"""Mission 1.62 §57. Anchor A8 closure, three partner packages, the frozen enquiry.

The rule this mission paid for is that what bounds a Claim is the frame the
acquisition surface EXPOSES, not the one the apparatus MEASURES. One candidate
scans the whole internet daily and can show a requester only that requester's own
networks, and it is the second fact that decides.

Nothing here is persisted, no measurement was retrieved to construct it, and no
test asserts a count of anything in the world.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"

BASELINE = DATA / "anchor-operational-closure-baseline-v1.json"
METHODOLOGY = DATA / "anchor-operational-methodology-v1.json"
SAMPLING = DATA / "anchor-sampling-frame-review-v1.json"
VANTAGE = DATA / "anchor-vantage-review-v1.json"
PORTWINDOW = DATA / "anchor-port-window-review-v1.json"
SHADOWSERVER = DATA / "partner-shadowserver-package-v1.json"
ONYPHE = DATA / "partner-onyphe-package-v1.json"
LEAKIX = DATA / "partner-leakix-package-v1.json"
COMPLETION = DATA / "partner-package-completion-v1.json"
CLOSURE = DATA / "anchor-operational-closure-and-partner-packages-v1.json"
CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"

ENQUIRY_V1_JSON = DATA / "anchor-technical-lineage-enquiry-v1.json"
ENQUIRY_V1_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"

B_SLOTS = ("B1", "B2", "B3", "B4", "B5", "B6")
PARTNERS = ("The Shadowserver Foundation", "ONYPHE", "LeakIX")
COMPATIBLE_EXPOSURE = (
    "RAW_IDENTIFICATION_STRING",
    "STRUCTURED_PROTOCOL_FIELD",
    "DETERMINISTIC_EQUIVALENT",
)


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _prose(node: object) -> list[str]:
    out: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.startswith("$"):
                continue
            out.extend(_prose(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_prose(item))
    elif isinstance(node, str):
        out.append(node)
    return out


class TestAnchorLineageStillStands(unittest.TestCase):
    """§57.1 to §57.3. A7 stands, and it proves nothing about coverage."""

    def test_a7_level_2_affirmative_closed_exception_list_remains_pass(self) -> None:
        lineage = _load(DATA / "anchor-lineage-review-v1.json")
        self.assertEqual(lineage["gate_a7_verdict"]["verdict"], "PASS")
        self.assertEqual(lineage["gate_a7_verdict"]["level_reached"], "LEVEL_2")
        self.assertTrue(lineage["level_2_evidence"]["exception_list_is_closed"])
        self.assertEqual(_load(CLOSURE)["anchor_gate_table"]["A7"]["verdict"], "PASS")

    def test_a7_was_not_reopened_and_no_contradictory_evidence_was_found(self) -> None:
        a7 = _load(CLOSURE)["a7_was_not_reopened"]
        self.assertFalse(a7["contradictory_lineage_evidence_found"])
        self.assertTrue(a7["documents_read_this_mission_that_could_have_contradicted_it"])

    def test_a7_does_not_imply_no_sampling(self) -> None:
        self.assertEqual(_load(SAMPLING)["sampling_verdict"]["result"], "SAMPLING_STATUS_UNKNOWN")
        self.assertEqual(_load(CLOSURE)["anchor_gate_table"]["A7"]["verdict"], "PASS")

    def test_lineage_does_not_imply_frame_exhaustiveness(self) -> None:
        frames = _load(SAMPLING)["two_frames"]
        self.assertIn("LINEAGE_EXHAUSTIVENESS_IS_NOT_FRAME_EXHAUSTIVENESS", json.dumps(frames))
        self.assertEqual(frames["ATTEMPTED_FRAME"]["status"], "NOT_ESTABLISHED")

    def test_frame_coverage_is_not_used_as_proof_of_lineage(self) -> None:
        self.assertTrue(
            _load(CLOSURE)["a7_was_not_reopened"][
                "a7_was_not_used_as_proof_of_anything_else"
            ].strip()
        )


class TestObservationAddressablePath(unittest.TestCase):
    """§57.4 and §57.5. The default surface is not the admissible one."""

    def test_default_current_state_surface_is_prohibited_for_this_contract(self) -> None:
        bound = _load(CLOSURE)["the_a2_bound_restated_with_new_evidence"]
        self.assertIn(
            "DEFAULT_CURRENT_STATE_PATH_PROHIBITED_FOR_THIS_CONTRACT", bound["status_words"]
        )
        self.assertTrue(bound["not_weakened"])

    def test_the_dated_index_path_is_the_admissible_one(self) -> None:
        bound = _load(CLOSURE)["the_a2_bound_restated_with_new_evidence"]
        self.assertIn("OBSERVATION_ADDRESSABLE_PATH_REQUIRED", bound["status_words"])
        self.assertIn("dated index", bound["admissible_path"])

    def test_a2_passes_and_carries_its_bound(self) -> None:
        a2 = _load(CLOSURE)["anchor_gate_table"]["A2"]
        self.assertEqual(a2["verdict"], "PASS")
        self.assertTrue(a2["bound"].strip())


class TestPortWindow(unittest.TestCase):
    """§57.6 and §57.7."""

    def test_current_inclusion_is_not_future_window_inclusion(self) -> None:
        verdict = _load(PORTWINDOW)["verdict"]
        self.assertEqual(verdict["current_inclusion_of_port_22"], "ESTABLISHED")
        self.assertEqual(
            verdict["window_coverage_of_port_22"], "PORT_22_WINDOW_COVERAGE_NOT_ESTABLISHED"
        )

    def test_absence_of_port_removal_is_not_a_continuity_proof(self) -> None:
        record = _load(PORTWINDOW)
        removals = record["findings"]["removals"]
        self.assertEqual(removals["status"], "NONE_RECORDED")
        self.assertTrue(removals["what_this_is_not"].strip())
        self.assertTrue(record["verdict"]["no_absence_reasoning_used"])

    def test_a_dated_size_is_not_a_dated_membership(self) -> None:
        self.assertEqual(
            _load(PORTWINDOW)["findings"]["configuration_versioning"]["status"], "NOT_ESTABLISHED"
        )


class TestCountingRules(unittest.TestCase):
    """§57.8 to §57.10."""

    def test_a_row_count_is_rejected_for_the_distinct_ip_metric(self) -> None:
        row = next(
            r
            for r in _load(METHODOLOGY)["closure_matrix"]
            if r["topic"] == "DISTINCT_ADDRESS_FIELD"
        )
        consequence = row["consequence"].lower()
        self.assertIn("distinct", consequence)
        self.assertIn("record count", consequence)

    def test_duplicate_responses_collapse_by_address_in_the_future_contract(self) -> None:
        row = next(r for r in _load(METHODOLOGY)["closure_matrix"] if r["topic"] == "DUPLICATION")
        self.assertIn(row["status"], ("PARTIAL", "UNKNOWN"))
        self.assertIn("distinct", row["why_load_bearing"].lower())

    def test_a_missing_observation_is_not_automatically_negative(self) -> None:
        missing = _load(SAMPLING)["missingness_semantics"]
        self.assertFalse(missing["does_this_destroy_the_construct"])
        self.assertTrue(missing["the_refusal"].strip())


class TestSamplingSilence(unittest.TestCase):
    """§57.11."""

    def test_sampling_silence_remains_unknown(self) -> None:
        verdict = _load(SAMPLING)["sampling_verdict"]
        self.assertEqual(verdict["result"], "SAMPLING_STATUS_UNKNOWN")
        self.assertEqual(verdict["selected"], "E")
        self.assertTrue(verdict["the_refusal"].strip())

    def test_an_unknown_sampling_state_is_not_a_blocker_outcome(self) -> None:
        self.assertFalse(_load(SAMPLING)["verdict"]["is_this_a_sampling_frame_blocker"])
        self.assertNotEqual(_load(CLOSURE)["primary_outcome"], "ANCHOR_SAMPLING_FRAME_BLOCKER")


class TestProtocolPredicate(unittest.TestCase):
    """§57.12 and §57.13."""

    def test_the_raw_ssh_prefix_remains_the_semantic_authority(self) -> None:
        lineage = _load(DATA / "anchor-lineage-review-v1.json")
        predicate = lineage["do_the_exceptions_touch_the_load_bearing_predicate"][
            "load_bearing_predicate"
        ]
        self.assertIn("SSH-", predicate)
        self.assertIn("22", predicate)

    def test_no_partner_passes_b3_on_a_vendor_label(self) -> None:
        for path in (SHADOWSERVER, ONYPHE, LEAKIX):
            pkg = _load(path)
            b3 = pkg["package"]["B3"]
            if b3["status"] == "PASS":
                self.assertIn(b3["classification"], COMPATIBLE_EXPOSURE, pkg["apparatus"])

    def test_banner_transformation_is_not_ignored(self) -> None:
        row = next(
            r for r in _load(METHODOLOGY)["closure_matrix"] if r["topic"] == "BANNER_FIDELITY"
        )
        self.assertEqual(row["classification"], "TRANSFORMATION_UNKNOWN")
        self.assertTrue(row["missing_fact"].strip())


class TestVantage(unittest.TestCase):
    """§57.14."""

    def test_undocumented_vantage_stays_undocumented(self) -> None:
        cls = _load(VANTAGE)["anchor_classification"]
        self.assertEqual(cls["verdict"], "VANTAGE_NOT_DOCUMENTED")

    def test_undocumented_vantage_is_not_silently_treated_as_global(self) -> None:
        needs = _load(VANTAGE)["does_the_proposition_need_scanner_identity"]
        self.assertNotEqual(needs["answer"], "NO")
        self.assertEqual(needs["answer"], "NOT_ESTABLISHED")

    def test_an_undocumented_vantage_is_not_a_blocker_outcome(self) -> None:
        needs = _load(VANTAGE)["does_the_proposition_need_scanner_identity"]
        self.assertFalse(needs["is_this_a_vantage_relative_population_blocker"])
        self.assertNotEqual(
            _load(CLOSURE)["primary_outcome"], "ANCHOR_VANTAGE_RELATIVE_POPULATION_BLOCKER"
        )


class TestPartnerPackages(unittest.TestCase):
    """§57.15 to §57.20."""

    def test_a_recovered_path_changed_documentation_availability(self) -> None:
        for path in (SHADOWSERVER, ONYPHE, LEAKIX):
            pkg = _load(path)
            self.assertTrue(pkg["documentation_paths_used"], pkg["apparatus"])

    def test_recovered_docs_alone_do_not_qualify_an_apparatus(self) -> None:
        for path in (SHADOWSERVER, ONYPHE, LEAKIX):
            pkg = _load(path)
            self.assertEqual(pkg["package_completion"]["status"], "PACKAGE_COMPLETE")
            self.assertNotEqual(
                pkg["individual_qualification"]["verdict"], "INDIVIDUALLY_QUALIFIED"
            )

    def test_an_open_ended_lineage_source_list_cannot_be_exhaustive(self) -> None:
        shadow = _load(SHADOWSERVER)
        self.assertEqual(shadow["package"]["B5"]["lineage_level"], "LEVEL_1")
        self.assertIn(
            "ENUMERATED_EXCEPTIONS_MAKE_A_LINEAGE_CLAIM_CHECKABLE",
            shadow["package"]["B5"]["why_not_LEVEL_2"],
        )

    def test_no_partner_reached_level_2_lineage(self) -> None:
        for path in (SHADOWSERVER, ONYPHE, LEAKIX):
            pkg = _load(path)
            for slot in pkg["package"].values():
                self.assertNotEqual(slot.get("lineage_level"), "LEVEL_2", pkg["apparatus"])

    def test_provider_level_lineage_is_not_transferred_to_a_resource(self) -> None:
        shadow = _load(SHADOWSERVER)
        self.assertEqual(
            shadow["package"]["B5"]["resource_specific_lineage"][:15], "NOT_ESTABLISHED"
        )

    def test_a_package_can_be_complete_and_not_qualified(self) -> None:
        for path in (SHADOWSERVER, LEAKIX):
            pkg = _load(path)
            self.assertEqual(pkg["package_completion"]["status"], "PACKAGE_COMPLETE")
            self.assertEqual(
                pkg["individual_qualification"]["verdict"], "INDIVIDUALLY_NOT_QUALIFIED"
            )

    def test_a_package_can_be_complete_and_unresolved(self) -> None:
        pkg = _load(ONYPHE)
        self.assertEqual(pkg["package_completion"]["status"], "PACKAGE_COMPLETE")
        self.assertEqual(pkg["individual_qualification"]["verdict"], "INDIVIDUALLY_UNRESOLVED")

    def test_every_slot_carries_an_explicit_status_and_no_silent_unknown(self) -> None:
        for path in (SHADOWSERVER, ONYPHE, LEAKIX):
            pkg = _load(path)
            self.assertEqual(pkg["package_completion"]["unread_slots"], 0, pkg["apparatus"])
            for slot in B_SLOTS:
                entry = pkg["package"][slot]
                self.assertTrue(entry["status"].strip())
                self.assertTrue(
                    entry.get("basis", "").strip()
                    or entry.get("fact_sought", "").strip()
                    or entry.get("not_pursued_further", "").strip(),
                    f"{pkg['apparatus']} {slot}",
                )

    def test_a_hard_fail_ends_qualification_regardless_of_other_slots(self) -> None:
        leakix = _load(LEAKIX)
        self.assertEqual(leakix["package"]["B2"]["status"], "FAIL")
        self.assertEqual(leakix["package"]["B3"]["status"], "PASS")
        self.assertEqual(
            leakix["individual_qualification"]["verdict"], "INDIVIDUALLY_NOT_QUALIFIED"
        )

    def test_the_retrievable_frame_decides_shadowserver(self) -> None:
        shadow = _load(SHADOWSERVER)
        self.assertEqual(shadow["package"]["B4"]["status"], "FAIL")
        self.assertEqual(shadow["package"]["B1"]["status"], "PASS")
        self.assertTrue(shadow["package"]["B4"]["why_this_is_a_FAIL_and_not_an_UNKNOWN"].strip())

    def test_public_documentation_is_not_accessible_data(self) -> None:
        qual = _load(ONYPHE)["individual_qualification"]
        self.assertTrue(qual["epistemic_documentation_status"].strip())
        self.assertTrue(qual["future_access_status"].strip())
        self.assertTrue(qual["these_two_are_recorded_separately"].strip())

    def test_thirty_day_truncation_is_not_ignored(self) -> None:
        retention = _load(ONYPHE)["thirty_day_retention_and_truncation"]
        self.assertTrue(retention["which_fields_are_removed"].startswith("UNKNOWN"))
        self.assertEqual(retention["does_the_raw_banner_survive"], "UNKNOWN")
        self.assertFalse(retention["does_this_disqualify"])
        self.assertTrue(retention["MAX_FULL_FIDELITY_RETRIEVAL_DELAY"].strip())


class TestNoPairWork(unittest.TestCase):
    """§57.21 and §57.22."""

    def test_no_pair_selection_exists(self) -> None:
        pair = _load(COMPLETION)["no_pair_work"]
        self.assertEqual(pair["pairs_selected"], 0)
        self.assertEqual(pair["pair_comparisons_performed"], 0)

    def test_no_pair_ranking_exists(self) -> None:
        completion = _load(COMPLETION)
        self.assertEqual(completion["no_pair_work"]["pairs_ranked"], 0)
        self.assertTrue(completion["no_pair_work"]["no_preference_expressed"].strip())

    def test_no_pair_gate_was_evaluated(self) -> None:
        pair = _load(COMPLETION)["no_pair_work"]
        for flag in (
            "same_frame_evaluated",
            "vantage_compatibility_evaluated",
            "pair_independence_evaluated",
            "shared_measurement_upstream_evaluated",
            "pair_time_contract_evaluated",
            "same_proposition_key_evaluated",
            "tie_break_applied",
        ):
            self.assertFalse(pair[flag], flag)

    def test_no_preference_vocabulary_appears_in_any_record(self) -> None:
        forbidden = ("best candidate", "preferred candidate", "strongest partner", "lead route")
        for path in (SHADOWSERVER, ONYPHE, LEAKIX, COMPLETION, CLOSURE, VANTAGE):
            for sentence in _prose(_load(path)):
                for word in forbidden:
                    self.assertNotIn(word, sentence.lower(), f"{path.name}: {sentence[:80]}")


class TestFrozenEnquiry(unittest.TestCase):
    """§57.23 to §57.26."""

    def test_enquiry_v1_bytes_remain_unchanged(self) -> None:
        recorded = _load(CLOSURE)["enquiry_v1_disposition"]["sha256"]
        digest = hashlib.sha256(
            ENQUIRY_V1_MD.read_text(encoding="utf-8").encode("utf-8")
        ).hexdigest()
        self.assertEqual(digest, recorded)

    def test_enquiry_v1_was_not_edited(self) -> None:
        disposition = _load(CLOSURE)["enquiry_v1_disposition"]
        self.assertFalse(disposition["edited"])
        self.assertTrue(disposition["bytes_unchanged"])
        v1 = _load(ENQUIRY_V1_JSON)
        self.assertEqual(v1["status"], "AWAITING_OPERATOR_APPROVAL")

    def test_every_v1_question_received_a_disposition(self) -> None:
        v1 = _load(ENQUIRY_V1_JSON)
        disposition = _load(CLOSURE)["enquiry_v1_disposition"]
        self.assertEqual(
            {q["topic"] for q in v1["questions"]},
            {d["topic"] for d in disposition["question_disposition"]},
        )

    def test_no_question_disappeared_so_v1_remains_current(self) -> None:
        disposition = _load(CLOSURE)["enquiry_v1_disposition"]
        self.assertEqual(disposition["answered_by_public_docs"], 0)
        self.assertEqual(disposition["verdict"], "V1_REMAINS_CURRENT")
        self.assertFalse(disposition["v2_created"])

    def test_no_duplicate_hash_was_manufactured(self) -> None:
        disposition = _load(CLOSURE)["enquiry_v1_disposition"]
        self.assertIn(disposition["sha256"], disposition["operative_approval_string"])
        self.assertIn("MISSION 1.61", disposition["operative_approval_string"])

    def test_no_contact_channel_was_invented(self) -> None:
        contact = _load(CLOSURE)["contact_channel"]
        self.assertTrue(contact["no_address_invented"])
        self.assertEqual(contact["status"], "FIRST_PARTY_CONTACT_CHANNEL_NOT_ESTABLISHED")
        for guess in ("support@", "info@", "security@", "contact@"):
            self.assertNotIn(guess, contact["what_was_found"])

    def test_a_valid_question_and_a_valid_channel_are_two_facts(self) -> None:
        contact = _load(CLOSURE)["contact_channel"]
        self.assertTrue(contact["TECHNICAL_ENQUIRY_REQUIRED"])
        self.assertEqual(contact["status"], "FIRST_PARTY_CONTACT_CHANNEL_NOT_ESTABLISHED")

    def test_no_outbound_enquiry_was_sent(self) -> None:
        self.assertEqual(_load(CLOSURE)["counters"]["outbound_enquiries_sent"], 0)
        self.assertFalse(_load(ENQUIRY_V1_JSON)["delivery"]["sent"])
        self.assertIsNone(_load(ENQUIRY_V1_JSON)["delivery"]["sent_at"])


class TestNothingWasRetrievedOrMutated(unittest.TestCase):
    """§57.27 to §57.35."""

    def test_no_measurement_query_was_executed(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        self.assertEqual(acct["MEASUREMENT_QUERIES_EXECUTED"], 0)
        self.assertEqual(acct["RESEARCH_DATA_REQUESTS"], 0)

    def test_a_count_is_classified_as_measurement(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        self.assertEqual(acct["TARGET_COUNTS_FETCHED"], 0)
        self.assertIn("measurement value", acct["the_count_is_measurement"])

    def test_a_trial_is_classified_as_potential_contamination(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        self.assertEqual(acct["TRIALS_STARTED"], 0)
        self.assertIn("contamination", acct["the_trial_is_not_free"].lower())

    def test_no_source_was_registered_and_no_governance_review_created(self) -> None:
        counters = _load(CLOSURE)["counters"]
        self.assertEqual(counters["sources_registered"], 0)
        self.assertEqual(counters["governance_reviews_created"], 0)

    def test_no_reliability_assessment_was_created(self) -> None:
        self.assertEqual(_load(CLOSURE)["counters"]["reliability_assessments_created"], 0)
        self.assertIsNone(_load(METHODOLOGY)["no_reliability_assigned"]["value_assigned"])

    def test_no_canonical_mutation(self) -> None:
        for name, value in _load(BASELINE)["canonical_mutations"].items():
            if name.startswith("$"):
                continue
            self.assertIn(value, (0, 0.0, False), name)

    def test_no_model_call_and_no_embeddings(self) -> None:
        counters = _load(CLOSURE)["counters"]
        self.assertEqual(counters["model_calls"], 0)
        self.assertEqual(counters["model_cost_usd"], 0.0)
        self.assertEqual(counters["embeddings"], 0)

    def test_opportunity_unchanged_and_profile_uncalibrated(self) -> None:
        counters = _load(CLOSURE)["counters"]
        self.assertEqual(counters["opportunity_changes"], 0)
        self.assertEqual(counters["scores_created"], 0)
        self.assertEqual(counters["reference_profile"], "UNCALIBRATED")

    def test_problem_family_stays_parked(self) -> None:
        self.assertEqual(_load(CLOSURE)["counters"]["problem_family"], "PARKED")

    def test_the_baseline_recorded_no_drift(self) -> None:
        self.assertEqual(_load(BASELINE)["canonical_baseline"]["drift_from_mission_1_61"], "none")

    def test_the_retrieval_budget_was_not_exceeded(self) -> None:
        ledger = _load(BASELINE)["documentation_ledger"]
        self.assertLessEqual(ledger["used_total"], ledger["budget_total"])
        self.assertEqual(ledger["used_total"], len(ledger["requests"]))


class TestOutcomeAndRegistry(unittest.TestCase):
    def test_the_outcome_was_not_forced_to_outcome_a(self) -> None:
        closure = _load(CLOSURE)
        self.assertEqual(
            closure["primary_outcome"], "ANCHOR_ENQUIRY_REQUIRED_PARTNER_PACKAGES_COMPLETE"
        )
        self.assertFalse(_load(METHODOLOGY)["gate_a8_verdict"]["reviewable"])

    def test_every_partner_is_reported_individually(self) -> None:
        partners = _load(CLOSURE)["secondary_outcomes"]["partners"]
        self.assertEqual(set(partners), set(PARTNERS))
        for name, states in partners.items():
            self.assertEqual(states[0], "PACKAGE_COMPLETE", name)

    def test_the_registry_carries_both_new_requirements(self) -> None:
        names = {r["name"] for r in _load(CONTRACT)["requirement_registry"]["requirements"]}
        self.assertIn("THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME", names)
        self.assertIn("DEFAULT_DATA_SURFACE_MUST_NOT_OVERRIDE_QUALIFIED_EXPOSURE_PATH", names)

    def test_the_earlier_requirements_survive(self) -> None:
        """Re-pointed in Mission 1.63.

        This asserted a registry length of 13, which the next mission's legitimate
        addition made false. A test pinning a total is a test asserting the registry
        never grows. What it is actually protecting is that no earlier requirement
        is dropped when a new one is appended, and that is what it now asserts.
        """
        requirements = _load(CONTRACT)["requirement_registry"]["requirements"]
        names = {r["name"] for r in requirements}
        for earlier in (
            "SOURCE_EXCLUSIVE_METRIC",
            "RELIABILITY_REVIEWABILITY",
            "FRAME_INSIDE_THE_DEFINITION",
            "AFFIRMATIVE_LINEAGE_REQUIRED",
            "PRODUCT_RELEVANCE",
            "READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT",
            "OBSERVATION_ADDRESSABLE_EXPOSURE",
            "THE_TEMPORAL_OBJECT_TEST",
            "SAMPLING_IS_LOAD_BEARING",
            "ENUMERATED_EXCEPTIONS_MAKE_A_LINEAGE_CLAIM_CHECKABLE",
            "LINEAGE_EXHAUSTIVENESS_IS_NOT_FRAME_EXHAUSTIVENESS",
        ):
            self.assertIn(earlier, names)
        self.assertGreaterEqual(len(requirements), 13)
        self.assertEqual(len(names), len(requirements), "a requirement name is duplicated")

    def test_earlier_mission_records_are_not_rewritten(self) -> None:
        selection = _load(DATA / "observation-addressable-scanner-pair-selection-v1.json")
        self.assertEqual(
            selection["primary_outcome"], "APPARATUS_LINEAGE_NOT_AFFIRMATIVELY_ESTABLISHED"
        )
        prior = _load(DATA / "anchor-lineage-and-documentation-closure-v1.json")
        self.assertEqual(
            prior["primary_outcome"], "ANCHOR_LINEAGE_CONFIRMED_OPERATIONAL_QUESTIONS_REMAIN"
        )

    def test_no_overclaim_vocabulary_in_any_record(self) -> None:
        forbidden = ("installation", "customer", "subscription", "revenue", "adoption", "demand")
        for path in (
            BASELINE,
            METHODOLOGY,
            SAMPLING,
            VANTAGE,
            PORTWINDOW,
            SHADOWSERVER,
            ONYPHE,
            LEAKIX,
            COMPLETION,
            CLOSURE,
        ):
            for sentence in _prose(_load(path)):
                tokens = re.findall(r"[a-z0-9]+", sentence.lower())
                for term in forbidden:
                    self.assertNotIn(term, tokens, f"{path.name}: {sentence[:80]}")

    def test_the_stop_condition_holds_in_every_field(self) -> None:
        for name, value in _load(CLOSURE)["stop_condition"].items():
            if name.startswith("$") or name == "awaiting":
                continue
            self.assertFalse(value, name)


if __name__ == "__main__":
    unittest.main()
