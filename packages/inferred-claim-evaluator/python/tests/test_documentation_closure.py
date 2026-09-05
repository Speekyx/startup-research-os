"""Mission 1.63 §44. Four targeted reads, two recomputations, one frozen enquiry.

The rule this mission paid for is that a load-bearing scan-configuration fact must
be attributable to the observation period the measurement comes from. Both
apparatuses publish a current port list and neither binds it to a window.

The other thing worth a test is negative: a retrieval summary reported a sentence
that the verbatim re-read could not find, and the verdict that would have rested on
it was not recorded.

Nothing here is persisted and no measurement was retrieved to construct it.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"

BASELINE = DATA / "targeted-documentation-closure-baseline-v1.json"
INDICES = DATA / "netlas-indices-port-window-review-v1.json"
TEMPORAL = DATA / "onyphe-datascan-temporal-object-review-v1.json"
PORTS = DATA / "onyphe-scanned-port-review-v1.json"
RETENTION = DATA / "onyphe-full-fidelity-retention-review-v1.json"
A8 = DATA / "anchor-a8-recomputed-v1.json"
PACKAGE = DATA / "onyphe-package-recomputed-v1.json"
READINESS = DATA / "qualified-apparatus-readiness-v1.json"
ENQUIRY = DATA / "mission-1.61-enquiry-reassessment-v1.json"
CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"

ENQUIRY_V1_JSON = DATA / "anchor-technical-lineage-enquiry-v1.json"
ENQUIRY_V1_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"

ALL_RECORDS = (
    BASELINE,
    INDICES,
    TEMPORAL,
    PORTS,
    RETENTION,
    A8,
    PACKAGE,
    READINESS,
    ENQUIRY,
)
B_SLOTS = ("B1", "B2", "B3", "B4", "B5", "B6")


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


class TestPortMembershipOverTime(unittest.TestCase):
    """§44.1 to §44.4."""

    def test_current_membership_is_not_window_membership(self) -> None:
        self.assertEqual(
            _load(INDICES)["verdict"]["result"], "PORT_22_WINDOW_COVERAGE_NOT_ESTABLISHED"
        )
        self.assertTrue(
            _load(INDICES)["no_forbidden_inference_was_used"]["from_current_port_list"].strip()
        )

    def test_a_versioned_configuration_would_establish_window_membership(self) -> None:
        mechanisms = _load(INDICES)["how_this_could_still_be_closed"]["mechanisms"]
        forms = " ".join(m["form"] for m in mechanisms).lower()
        self.assertIn("port set", forms)
        self.assertTrue(any(m["status"] != "" for m in mechanisms))

    def test_port_list_cardinality_cannot_establish_membership(self) -> None:
        self.assertTrue(
            _load(INDICES)["no_forbidden_inference_was_used"]["from_list_cardinality"].strip()
        )

    def test_absence_of_removal_does_not_prove_continuous_inclusion(self) -> None:
        self.assertTrue(
            _load(INDICES)["no_forbidden_inference_was_used"]["from_absence_of_removals"].strip()
        )

    def test_the_configuration_endpoint_was_not_executed(self) -> None:
        block = _load(INDICES)["the_endpoint_was_not_executed"]
        self.assertFalse(block["executed"])
        self.assertTrue(block["the_circularity_that_was_refused"].strip())
        self.assertEqual(
            _load(BASELINE)["request_accounting"]["configuration_endpoints_executed"], 0
        )

    def test_an_endpoint_existing_is_not_documented_semantics(self) -> None:
        found = _load(INDICES)["what_was_found"]
        self.assertTrue(found["endpoint_located"])
        self.assertFalse(found["response_schema_available"])
        self.assertEqual(
            _load(INDICES)["verdict"]["result"], "PORT_22_WINDOW_COVERAGE_NOT_ESTABLISHED"
        )


class TestTemporalObject(unittest.TestCase):
    """§44.5 to §44.8."""

    def test_an_observation_event_model_would_pass_and_a_maintained_one_would_fail(self) -> None:
        """The rule, asserted as a rule rather than as this apparatus's answer."""
        verdict = _load(TEMPORAL)["verdict"]
        self.assertIn(
            verdict["record_model"],
            (
                "OBSERVATION_EVENT",
                "MAINTAINED_SERVICE_STATE",
                "APPEND_WITH_VERSIONED_OBSERVATIONS",
                "AMBIGUOUS",
            ),
        )
        if verdict["record_model"] == "MAINTAINED_SERVICE_STATE":
            self.assertEqual(verdict["b2_result"], "FAIL")
        if verdict["b2_result"] == "PASS":
            self.assertIn(
                verdict["record_model"],
                ("OBSERVATION_EVENT", "APPEND_WITH_VERSIONED_OBSERVATIONS"),
            )

    def test_the_documentation_remains_ambiguous(self) -> None:
        verdict = _load(TEMPORAL)["verdict"]
        self.assertEqual(verdict["record_model"], "AMBIGUOUS")
        self.assertEqual(verdict["b2_result"], "PARTIAL")

    def test_an_ambiguous_model_was_not_resolved_favourably(self) -> None:
        verdict = _load(TEMPORAL)["verdict"]
        self.assertNotEqual(verdict["b2_result"], "PASS")
        self.assertTrue(verdict["the_interpretation_that_was_not_chosen"].strip())

    def test_no_empirical_query_resolved_the_ambiguity(self) -> None:
        block = _load(TEMPORAL)["no_empirical_resolution_was_attempted"]
        for name in ("records_queried", "hosts_queried", "timestamps_compared"):
            self.assertEqual(block[name], 0, name)

    def test_the_diagnostic_was_answered(self) -> None:
        self.assertEqual(
            _load(TEMPORAL)["the_diagnostic"]["answer"], "NOT_DETERMINABLE_FROM_DOCUMENTATION"
        )

    def test_a_retrieval_summary_is_not_a_document(self) -> None:
        """The finding this mission is most likely to be quoted for."""
        refuted = _load(TEMPORAL)["the_summary_that_was_refuted"]
        self.assertTrue(refuted["what_the_first_read_reported"].strip())
        self.assertTrue(refuted["what_the_verbatim_read_found"].strip())
        self.assertIn("does not contain", refuted["what_the_verbatim_read_found"])
        baseline = _load(BASELINE)["the_verbatim_re_read_that_changed_a_verdict"]
        self.assertTrue(baseline["the_rule_this_confirms"].strip())


class TestScannedPorts(unittest.TestCase):
    def test_a_port_list_for_one_category_does_not_establish_another(self) -> None:
        record = _load(PORTS)
        found = record["what_was_found"]
        self.assertNotEqual(
            found["the_category_this_documents"], found["the_category_the_construct_needs"]
        )
        self.assertEqual(record["verdict"]["result"], "PORT_22_STATUS_UNKNOWN")

    def test_an_undated_list_cannot_establish_versioned_inclusion(self) -> None:
        record = _load(PORTS)
        self.assertTrue(record["what_was_found"]["temporal_binding"].startswith("NONE"))
        self.assertNotIn(
            record["verdict"]["result"],
            ("PORT_22_CONTINUOUSLY_INCLUDED", "PORT_22_INCLUDED_IN_VERSIONED_SCAN_SET"),
        )

    def test_the_construct_was_not_broadened_beyond_tcp_22(self) -> None:
        block = _load(PORTS)["port_22_is_not_universally_ssh"]
        self.assertFalse(block["construct_broadened"])
        self.assertIn("TCP/22", block["rule"])

    def test_not_included_was_not_asserted_either(self) -> None:
        self.assertTrue(_load(PORTS)["verdict"]["why_not_NOT_INCLUDED"].strip())


class TestRetention(unittest.TestCase):
    """§44.9 to §44.13."""

    def test_the_raw_field_is_named_as_truncated_not_removed(self) -> None:
        settles = _load(RETENTION)["what_the_sentence_settles"]
        self.assertTrue(settles["the_data_field_is_named"])
        self.assertIn("TRUNCATED", settles["truncation"].upper())
        self.assertEqual(settles["does_the_ssh_prefix_survive"], "YES")

    def test_unnamed_removed_fields_stay_unknown(self) -> None:
        unsettled = _load(RETENTION)["what_the_sentence_does_not_settle"]
        for key in (
            "which_fields_are_removed",
            "does_the_observation_timestamp_survive",
            "does_the_ip_address_survive",
        ):
            self.assertTrue(str(unsettled[key]).startswith("UNKNOWN"), key)

    def test_finite_retention_with_a_known_window_remains_viable(self) -> None:
        record = _load(RETENTION)
        self.assertFalse(
            record["finite_retention_is_not_automatic_disqualification"][
                "does_retention_block_this_apparatus"
            ]
        )
        self.assertTrue(record["retrieval_deadlines"]["MAX_FULL_FIDELITY_RETRIEVAL_DELAY"].strip())

    def test_b3_was_not_reopened_merely_because_retention_is_finite(self) -> None:
        b3 = _load(RETENTION)["b3_is_not_reopened"]
        self.assertFalse(b3["reopened_merely_because_retention_is_finite"])
        self.assertEqual(b3["verdict"], "ONYPHE_B3_PASS")

    def test_an_expired_banner_would_destroy_retrospective_protocol_use(self) -> None:
        """The rule, held even though this apparatus does not trip it."""
        conditions = _load(RETENTION)["b3_is_not_reopened"][
            "the_three_conditions_that_would_have_reopened_it"
        ]
        self.assertIn("retention_removes_it_before_usable_retrieval", conditions)
        self.assertIn("refuted", conditions["retention_removes_it_before_usable_retrieval"])

    def test_a_lost_timestamp_would_destroy_retrospective_window_use(self) -> None:
        deadlines = _load(RETENTION)["retrieval_deadlines"]
        self.assertEqual(deadlines["MAX_PREDICATE_SUFFICIENT_RETRIEVAL_DELAY"], "NOT_ESTABLISHED")
        self.assertIn("timestamp", deadlines["why_not_established"].lower())

    def test_no_dates_were_chosen(self) -> None:
        deadlines = _load(RETENTION)["retrieval_deadlines"]
        for flag in ("no_dates_chosen", "no_window_selected", "no_values_retrieved"):
            self.assertTrue(deadlines[flag], flag)


class TestCountEndpoint(unittest.TestCase):
    """§44.14 and §44.15."""

    def test_an_estimated_count_cannot_feed_a_deterministic_evaluator(self) -> None:
        block = _load(READINESS)["count_endpoint_constraint_carried_forward"]
        self.assertEqual(
            block["status_word"], "ESTIMATED_COUNT_ENDPOINT_PROHIBITED_FOR_DETERMINISTIC_THRESHOLD"
        )
        self.assertTrue(block["no_probabilistic_semantics_introduced"])
        self.assertTrue(block["no_confidence_interval_evaluator_introduced"])

    def test_the_exact_route_remains_conceptual(self) -> None:
        block = _load(READINESS)["count_endpoint_constraint_carried_forward"]
        self.assertFalse(block["executed_this_mission"])
        self.assertTrue(block["potential_future_exact_route"].strip())


class TestRecomputations(unittest.TestCase):
    """§44.16 to §44.21."""

    def test_a8_was_recomputed_without_enquiry_answers(self) -> None:
        self.assertFalse(_load(A8)["basis"]["enquiry_answers_used"])

    def test_a8_reports_every_topic_and_no_topic_changed(self) -> None:
        matrix = _load(A8)["matrix"]
        self.assertEqual(len(matrix), 10)
        for row in matrix:
            self.assertEqual(row["changed"], row["before"] != row["after"], row["topic"])
        self.assertEqual(_load(A8)["tally"]["changed_this_mission"], 0)

    def test_a8_remains_partial_with_load_bearing_unknowns(self) -> None:
        record = _load(A8)
        self.assertFalse(record["verdict"]["reviewable"])
        unknowns = [r for r in record["matrix"] if r["after"] == "UNKNOWN" and r["load_bearing"]]
        self.assertGreater(len(unknowns), 0)

    def test_the_onyphe_package_reports_every_slot(self) -> None:
        pkg = _load(PACKAGE)["package"]
        for slot in B_SLOTS:
            self.assertIn(slot, pkg)
            self.assertTrue(pkg[slot]["basis"].strip())
            self.assertIn("binding_blocker", pkg[slot])

    def test_package_completeness_is_not_qualification(self) -> None:
        qual = _load(PACKAGE)["individual_qualification"]
        self.assertEqual(qual["verdict"], "INDIVIDUALLY_UNRESOLVED")
        self.assertNotEqual(qual["verdict"], "INDIVIDUALLY_QUALIFIED")

    def test_leakix_remains_not_qualified(self) -> None:
        entry = next(a for a in _load(READINESS)["apparatuses"] if a["name"] == "LeakIX")
        self.assertEqual(entry["individual_status"], "INDIVIDUALLY_NOT_QUALIFIED")
        self.assertFalse(entry["researched_this_mission"])

    def test_shadowserver_remains_not_qualified(self) -> None:
        entry = next(
            a for a in _load(READINESS)["apparatuses"] if a["name"] == "The Shadowserver Foundation"
        )
        self.assertEqual(entry["individual_status"], "INDIVIDUALLY_NOT_QUALIFIED")
        self.assertFalse(entry["researched_this_mission"])

    def test_the_qualified_count_is_computed_without_pair_selection(self) -> None:
        record = _load(READINESS)
        counted = sum(
            1 for a in record["apparatuses"] if a["individual_status"] == "INDIVIDUALLY_QUALIFIED"
        )
        self.assertEqual(record["readiness"]["QUALIFIED_APPARATUS_COUNT"], counted)
        self.assertEqual(record["no_pair_work_was_performed"]["pairs_selected"], 0)

    def test_fewer_than_two_qualified_gives_not_ready(self) -> None:
        block = _load(READINESS)["readiness"]
        self.assertLess(block["QUALIFIED_APPARATUS_COUNT"], 2)
        self.assertFalse(block["PAIR_ANALYSIS_READY"])

    def test_readiness_is_a_status_not_a_selection(self) -> None:
        record = _load(READINESS)
        self.assertTrue(record["readiness"]["this_is_a_status_not_a_selection"])
        pair = record["no_pair_work_was_performed"]
        for flag in (
            "same_frame_evaluated",
            "same_observation_window_evaluated",
            "vantage_compatibility_evaluated",
            "lineage_independence_evaluated",
            "shared_measurement_upstream_evaluated",
            "same_target_proposition_evaluated",
            "threshold_preregistrability_evaluated",
        ):
            self.assertFalse(pair[flag], flag)


class TestFrozenEnquiry(unittest.TestCase):
    """§44.22 to §44.24."""

    def test_enquiry_v1_bytes_are_unchanged(self) -> None:
        recorded = _load(ENQUIRY)["artifact"]["sha256"]
        digest = hashlib.sha256(
            ENQUIRY_V1_MD.read_text(encoding="utf-8").encode("utf-8")
        ).hexdigest()
        self.assertEqual(digest, recorded)

    def test_enquiry_v1_was_not_edited(self) -> None:
        artifact = _load(ENQUIRY)["artifact"]
        self.assertFalse(artifact["edited"])
        self.assertTrue(artifact["bytes_unchanged"])
        self.assertEqual(_load(ENQUIRY_V1_JSON)["status"], "AWAITING_OPERATOR_APPROVAL")

    def test_no_question_was_answered_so_case_a_applies(self) -> None:
        record = _load(ENQUIRY)
        self.assertEqual(record["tally"]["answered_by_public_docs"], 0)
        self.assertEqual(record["case"]["selected"], "CASE_A")
        self.assertFalse(record["case"]["v2_created"])

    def test_an_answered_question_would_supersede_rather_than_edit(self) -> None:
        """The rule, held even though this mission is CASE A."""
        case = _load(ENQUIRY)["case"]
        self.assertTrue(case["why_not_CASE_B"].strip())
        self.assertFalse(_load(ENQUIRY)["artifact"]["edited"])

    def test_no_duplicate_hash_was_manufactured(self) -> None:
        record = _load(ENQUIRY)
        self.assertIn(record["artifact"]["sha256"], record["case"]["operative_approval_string"])
        self.assertIn("MISSION 1.61", record["case"]["operative_approval_string"])

    def test_the_enquiry_is_not_evidence(self) -> None:
        self.assertFalse(
            _load(ENQUIRY)["the_enquiry_is_not_evidence"][
                "enquiry_answers_used_in_the_a8_recomputation"
            ]
        )

    def test_no_contact_address_was_guessed(self) -> None:
        contact = _load(ENQUIRY)["contact_channel"]
        self.assertFalse(contact["address_invented"])
        self.assertFalse(contact["address_decoded_by_guess"])
        self.assertFalse(contact["conventional_mailboxes_inferred"])
        blob = json.dumps(contact)
        for guess in ("support@", "info@", "security@", "contact@"):
            self.assertNotIn(guess, blob)

    def test_no_outbound_enquiry_was_sent(self) -> None:
        self.assertEqual(_load(ENQUIRY)["contact_channel"]["outbound_messages_sent"], 0)
        self.assertEqual(_load(BASELINE)["request_accounting"]["OUTBOUND_ENQUIRIES_SENT"], 0)


class TestNothingWasRetrievedOrMutated(unittest.TestCase):
    """§44.25 to §44.36."""

    def test_no_measurement_query_was_executed(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        self.assertEqual(acct["MEASUREMENT_QUERIES_EXECUTED"], 0)
        self.assertEqual(acct["RESEARCH_DATA_REQUESTS"], 0)

    def test_no_counts_hosts_banners_or_downloads(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        for name in (
            "TARGET_COUNTS_FETCHED",
            "TARGET_HOST_RECORDS_FETCHED",
            "TARGET_IPS_FETCHED",
            "TARGET_BANNERS_FETCHED",
            "FACETS_FETCHED",
            "MEASUREMENT_DOWNLOADS",
        ):
            self.assertEqual(acct[name], 0, name)

    def test_no_trials_or_purchases(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        self.assertEqual(acct["TRIALS_STARTED"], 0)
        self.assertEqual(acct["PURCHASES"], 0)

    def test_no_canonical_mutation(self) -> None:
        for name, value in _load(BASELINE)["canonical_mutations"].items():
            if name.startswith("$"):
                continue
            self.assertIn(value, (0, 0.0, False), name)

    def test_no_reliability_value_and_no_governance_review(self) -> None:
        mut = _load(BASELINE)["canonical_mutations"]
        self.assertEqual(mut["reliability_values_assigned"], 0)
        self.assertEqual(mut["reliability_assessments_created"], 0)
        self.assertEqual(mut["governance_reviews_created"], 0)
        self.assertEqual(mut["sources_registered"], 0)

    def test_no_model_call_and_no_embeddings(self) -> None:
        mut = _load(BASELINE)["canonical_mutations"]
        self.assertEqual(mut["model_calls"], 0)
        self.assertEqual(mut["model_cost_usd"], 0.0)
        self.assertEqual(mut["embeddings"], 0)

    def test_problem_family_stays_parked_and_profile_uncalibrated(self) -> None:
        base = _load(BASELINE)["canonical_baseline"]
        self.assertEqual(base["problem_family"], "PARKED")
        self.assertEqual(base["reference_profile"], "UNCALIBRATED")

    def test_the_baseline_recorded_no_drift(self) -> None:
        self.assertEqual(_load(BASELINE)["canonical_baseline"]["drift_from_mission_1_62"], "none")

    def test_the_retrieval_budget_was_respected(self) -> None:
        ledger = _load(BASELINE)["documentation_ledger"]
        self.assertLessEqual(ledger["used"], ledger["budget"])
        self.assertEqual(ledger["used"], len(ledger["requests"]))

    def test_every_request_served_a_named_target(self) -> None:
        record = _load(BASELINE)
        named = {t["n"] for t in record["the_four_targets"]["targets"]}
        for entry in record["documentation_ledger"]["requests"]:
            self.assertIn(entry["target"], named, entry["url"])

    def test_the_stop_condition_holds_in_every_field(self) -> None:
        for name, value in _load(READINESS)["stop_condition"].items():
            if name.startswith("$") or name == "awaiting":
                continue
            self.assertFalse(value, name)


class TestOutcomeAndRegistry(unittest.TestCase):
    def test_the_outcome_was_not_forced_to_a(self) -> None:
        record = _load(READINESS)
        self.assertEqual(
            record["primary_outcome"], "ANCHOR_ENQUIRY_STILL_REQUIRED_ONYPHE_UNRESOLVED"
        )
        self.assertLess(record["readiness"]["QUALIFIED_APPARATUS_COUNT"], 2)

    def test_the_registry_carries_the_new_requirement(self) -> None:
        names = {r["name"] for r in _load(CONTRACT)["requirement_registry"]["requirements"]}
        self.assertIn("APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE", names)
        self.assertEqual(len(_load(CONTRACT)["requirement_registry"]["requirements"]), 14)

    def test_the_declined_requirement_states_its_reason(self) -> None:
        declined = _load(READINESS)["registry_decision"]["declined"]
        self.assertTrue(declined)
        for item in declined:
            self.assertTrue(item["why_declined"].strip())
        names = {r["name"] for r in _load(CONTRACT)["requirement_registry"]["requirements"]}
        for item in declined:
            self.assertNotIn(item["name"], names)

    def test_the_earlier_thirteen_requirements_survive(self) -> None:
        names = {r["name"] for r in _load(CONTRACT)["requirement_registry"]["requirements"]}
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
            "THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME",
            "DEFAULT_DATA_SURFACE_MUST_NOT_OVERRIDE_QUALIFIED_EXPOSURE_PATH",
        ):
            self.assertIn(earlier, names)

    def test_earlier_mission_records_are_not_rewritten(self) -> None:
        prior = _load(DATA / "anchor-operational-closure-and-partner-packages-v1.json")
        self.assertEqual(
            prior["primary_outcome"], "ANCHOR_ENQUIRY_REQUIRED_PARTNER_PACKAGES_COMPLETE"
        )

    def test_no_overclaim_vocabulary_in_any_record(self) -> None:
        forbidden = ("installation", "customer", "subscription", "revenue", "adoption", "demand")
        for path in ALL_RECORDS:
            for sentence in _prose(_load(path)):
                tokens = re.findall(r"[a-z0-9]+", sentence.lower())
                for term in forbidden:
                    self.assertNotIn(term, tokens, f"{path.name}: {sentence[:80]}")

    def test_no_preference_vocabulary_in_any_record(self) -> None:
        forbidden = ("best candidate", "preferred candidate", "strongest partner", "lead route")
        for path in ALL_RECORDS:
            for sentence in _prose(_load(path)):
                for word in forbidden:
                    self.assertNotIn(word, sentence.lower(), f"{path.name}: {sentence[:80]}")


if __name__ == "__main__":
    unittest.main()
