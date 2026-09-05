"""Mission 1.66.2. Twelve documents read, and not one gate moved.

The tests here are mostly about readings that were available and refused.

Each of the following is true of ONYPHE's public documentation, and each is
compatible with BOTH storage models the B2 gate distinguishes: seven months of
history, time functions described as querying data collected in a past window, a
default sort putting the latest result first, and a function for reaching an
older one. A mission that wanted B2 to pass could assemble those four into a
case. None of them addresses what happens when the SAME service is observed
twice, which is the only question B2 turns on.

The same shape recurs in the other two areas. A page saying 500 ports says how
many, never which. A retention sentence naming the field it TRUNCATES does not
thereby name the fields it REMOVES. And an endpoint documented as showing an API
key is not probed to find out whether the documentation was loose.

Nothing here is persisted, nothing was executed, and no mailbox was read.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"

BASELINE = DATA / "mission-1.66.2-baseline-v1.json"
RECONCILIATION = DATA / "onyphe-public-documentation-reconciliation-v1.json"
TEMPORAL = DATA / "onyphe-temporal-object-public-doc-review-v2.json"
PORTS = DATA / "onyphe-datascan-port-configuration-public-doc-review-v2.json"
USER_API = DATA / "onyphe-user-api-configuration-surface-review-v1.json"
RETENTION = DATA / "onyphe-retention-public-doc-review-v2.json"
CONTACT = DATA / "onyphe-contact-channel-reconciliation-v1.json"
REASSESSMENT = DATA / "onyphe-three-question-reassessment-v1.json"
PACKAGE = DATA / "onyphe-package-recomputed-v2.json"
READINESS = DATA / "qualified-apparatus-readiness-v3.json"

ONYPHE_ENQUIRY_MD = DATA / "onyphe-technical-methodology-enquiry-v1.md"
ONYPHE_ENVELOPE = DATA / "onyphe-dispatch-envelope-v1.json"
NETLAS_ENVELOPE = DATA / "netlas-dispatch-envelope-v1.json"
ATTESTATION = DATA / "onyphe-manual-dispatch-attestation-v1.json"

ONYPHE_CONTENT_SHA256 = "0b39ef325fd42836a3b65284a7386cbca7ae8f22afcb9629d5574e0ff0f23e9f"

ALL_RECORDS = (
    BASELINE,
    RECONCILIATION,
    TEMPORAL,
    PORTS,
    USER_API,
    RETENTION,
    CONTACT,
    REASSESSMENT,
    PACKAGE,
    READINESS,
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


class TestPreconditionAndBaseline(unittest.TestCase):
    """§48.1 and §48.2."""

    def test_mission_1_66_1_is_recorded_as_merged_and_verified_from_git(self) -> None:
        pre = _load(BASELINE)["repository_precondition"]
        self.assertIs(pre["mission_1_66_1_merged"], True)
        self.assertEqual(pre["merge_commit_short"], "61fb5fb")
        self.assertIs(pre["verified_from_git_not_from_prompt"], True)
        self.assertIs(pre["operator_report_agrees_with_git"], True)

    def test_the_baseline_is_what_mission_1_66_1_left(self) -> None:
        base = _load(BASELINE)["canonical_baseline"]
        self.assertEqual(base["raw_records"], 325)
        self.assertEqual(base["normalized_records"], 325)
        self.assertEqual(base["signals"], 33)
        self.assertEqual(base["claims"], 44)
        self.assertEqual(base["claim_revisions"], 45)
        self.assertEqual(base["evidence"], 58)
        self.assertEqual(base["evidence_supports"], 57)
        self.assertEqual(base["evidence_contradicts"], 1)
        self.assertEqual(base["reliability_assessments"], 4)
        self.assertEqual(base["registered_sources"], 29)
        self.assertEqual(base["migration_head"], "0035_refusal_provenance")
        self.assertEqual(base["drift_from_mission_1_66_1"], "none")

    def test_the_budget_was_bounded_and_every_request_is_ledgered(self) -> None:
        budget = _load(BASELINE)["documentation_budget"]
        self.assertLessEqual(budget["used"], budget["maximum"])
        self.assertEqual(len(budget["requests"]), budget["used"])
        for entry in budget["requests"]:
            self.assertTrue(entry["url"].startswith("https://"))
            self.assertTrue(entry["sought"].strip())

    def test_a_retrieval_that_returned_nothing_usable_is_still_counted(self) -> None:
        # A budget that only counts successes is not a budget.
        outcomes = {e["outcome"] for e in _load(BASELINE)["documentation_budget"]["requests"]}
        self.assertIn("HTTP_404_NOT_THIS_PATH", outcomes)

    def test_no_search_summary_was_used_as_evidence(self) -> None:
        boundary = _load(BASELINE)["source_boundary"]
        self.assertIs(boundary["search_summary_used_as_evidence"], False)
        self.assertIs(boundary["every_load_bearing_claim_requoted_from_the_page"], True)
        self.assertTrue(boundary["why_that_matters_here"].strip())


class TestHistoricalWordingCannotPromoteB2(unittest.TestCase):
    """§48.3 to §48.8. Four true statements, none of which closes the gate."""

    def setUp(self) -> None:
        self.record = _load(TEMPORAL)

    def test_the_discriminator_is_the_repeated_observation_of_the_same_service(self) -> None:
        case = self.record["the_exact_discriminator"]["case"].lower()
        self.assertIn("same", case)
        self.assertIn("again", case)

    def test_the_time_functions_are_quoted_verbatim(self) -> None:
        functions = self.record["what_the_pages_actually_say"]["query_language_time_functions"]
        names = {f["function"] for f in functions}
        self.assertEqual(names, {"-hourago", "-dayago", "-weekago", "-monthago", "-since"})
        for f in functions:
            self.assertTrue(f["verbatim"].strip())

    def test_historical_support_strengthens_the_basis_and_does_not_pass_the_gate(self) -> None:
        refused = self.record["inferences_that_were_available_and_refused"]
        self.assertTrue(refused["historical_data_exists"].strip())
        self.assertEqual(self.record["verdict"]["B2"], "PARTIAL")

    def test_data_collected_wording_was_not_promoted(self) -> None:
        self.assertIn("maintained record", refused_text(self.record, "data_collected_wording"))

    def test_latest_first_was_not_read_as_versioned_observations(self) -> None:
        text = refused_text(self.record, "latest_first_default")
        self.assertIn("says nothing about", text)

    def test_the_timestamp_sentence_is_recorded_as_carrying_both_readings(self) -> None:
        definition = self.record["what_the_pages_actually_say"]["timestamp_definition"]
        self.assertIn("collected", definition["verbatim"])
        self.assertIn("last observed", definition["verbatim"])
        self.assertTrue(definition["why_it_does_not_settle_the_case"].strip())

    def test_the_best_candidate_page_was_fetched_and_does_not_answer_it(self) -> None:
        best = self.record["the_page_most_likely_to_answer_it_does_not"]
        self.assertIn("historical queries", best["why_it_was_the_best_candidate"].lower())
        self.assertTrue(best["finding"].strip())

    def test_ambiguity_remains_partial(self) -> None:
        self.assertEqual(self.record["verdict"]["B2"], "PARTIAL")
        self.assertEqual(self.record["verdict"]["state"], "AMBIGUOUS")
        self.assertIs(self.record["verdict"]["changed_this_mission"], False)

    def test_no_empirical_query_was_run_to_distinguish_the_models(self) -> None:
        self.assertIn(
            "measurement query", self.record["what_would_close_it"]["empirical_route_refused"]
        )
        self.assertEqual(_load(BASELINE)["request_accounting"]["MEASUREMENT_QUERIES"], 0)


def refused_text(record: dict, key: str) -> str:
    return record["inferences_that_were_available_and_refused"][key]


class TestCardinalityIsNotMembership(unittest.TestCase):
    """§48.9 to §48.14."""

    def setUp(self) -> None:
        self.record = _load(PORTS)

    def test_the_us_fr_500_port_statement_is_recorded_verbatim(self) -> None:
        quotes = [
            i["verbatim"]
            for i in self.record["current_documented_configuration"]["datascan_ip_scanning"]
        ]
        self.assertTrue(any("500 ports" in q for q in quotes))
        self.assertTrue(any("TOP 25 ports" in q for q in quotes))

    def test_the_record_states_that_a_count_is_not_a_set(self) -> None:
        self.assertTrue(
            self.record["current_documented_configuration"]["cardinality_is_not_membership"].strip()
        )

    def test_tcp_22_stays_unknown(self) -> None:
        self.assertEqual(self.record["tcp_22_membership"]["verdict"], "DATASCAN_TCP22_UNKNOWN")

    def test_port_22_appears_only_under_a_ctiscan_heading(self) -> None:
        tcp = self.record["tcp_22_membership"]
        self.assertIn("ctiscan", tcp["port_22_appears_under"])
        self.assertIs(tcp["datascan_tcp_section_exists"], False)

    def test_no_category_transfer_was_made(self) -> None:
        self.assertIn(
            "does not establish it for another",
            self.record["tcp_22_membership"]["what_that_does_not_establish"],
        )

    def test_a_missing_section_is_not_a_denial(self) -> None:
        self.assertTrue(self.record["tcp_22_membership"]["absence_is_not_denial"].strip())

    def test_configuration_drift_is_established_and_quoted(self) -> None:
        drift = self.record["historical_configuration_drift"]
        self.assertIs(drift["DATASCAN_CONFIGURATION_HISTORICALLY_MUTABLE"], True)
        self.assertGreaterEqual(len(drift["verbatim"]), 4)
        self.assertTrue(drift["basis_page"].strip())

    def test_the_drift_covers_ports_cadence_and_regions(self) -> None:
        changed = self.record["historical_configuration_drift"]["what_changed_over_time"]
        joined = " ".join(changed)
        self.assertIn("ports", joined)
        self.assertIn("cadence", joined)
        self.assertIn("regions", joined)

    def test_current_membership_is_not_historical_membership(self) -> None:
        addressable = self.record["configuration_time_addressability"]
        self.assertIs(addressable["current_membership_is_not_historical_membership"], True)
        self.assertEqual(addressable["verdict"], "CONFIGURATION_TIME_UNKNOWN")

    def test_documented_drift_makes_addressability_worse_not_better(self) -> None:
        self.assertTrue(
            self.record["configuration_time_addressability"][
                "why_the_drift_makes_this_worse_rather_than_better"
            ].strip()
        )

    def test_the_region_dependence_finding_is_recorded(self) -> None:
        finding = self.record["the_finding_this_mission_adds"]
        self.assertEqual(finding["name"], "DATASCAN_PORT_SET_IS_REGION_DEPENDENT")
        self.assertIn("500", finding["evidence"])
        self.assertIn("TOP 25", finding["evidence"])
        self.assertTrue(finding["it_is_not_a_refutation"].strip())


class TestTheRegistryWasNotEditedInPassing(unittest.TestCase):
    """§48.39."""

    def test_the_registry_stays_at_fourteen(self) -> None:
        offered = _load(PORTS)["candidate_registry_requirement_offered_and_not_added"]
        self.assertEqual(offered["REGISTRY_UNCHANGED"], 14)
        self.assertEqual(_load(RECONCILIATION)["boundaries_held"]["registry_count"], 14)
        self.assertEqual(_load(RECONCILIATION)["boundaries_held"]["registry_additions"], 0)

    def test_the_candidate_requirement_is_offered_with_its_justification(self) -> None:
        offered = _load(PORTS)["candidate_registry_requirement_offered_and_not_added"]
        for field in (
            "statement",
            "demonstrated_by",
            "why_it_is_not_already_represented",
            "why_it_was_not_added_here",
            "recommended_adopter",
        ):
            self.assertTrue(offered[field].strip(), field)

    def test_it_names_the_existing_rules_it_is_distinct_from(self) -> None:
        reason = _load(PORTS)["candidate_registry_requirement_offered_and_not_added"][
            "why_it_is_not_already_represented"
        ]
        self.assertIn("SAMPLING_IS_LOAD_BEARING", reason)
        self.assertIn("APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE", reason)


class TestTheUserApiWasNotExecuted(unittest.TestCase):
    """§48.15 to §48.19."""

    def setUp(self) -> None:
        self.record = _load(USER_API)

    def test_it_was_not_executed(self) -> None:
        self.assertIs(self.record["endpoint"]["EXECUTED"], False)
        self.assertEqual(self.record["endpoint"]["execution_attempts"], 0)
        self.assertEqual(_load(BASELINE)["request_accounting"]["USER_API_EXECUTIONS"], 0)

    def test_no_credential_was_read(self) -> None:
        self.assertEqual(self.record["endpoint"]["credentials_read"], 0)
        self.assertEqual(_load(BASELINE)["request_accounting"]["CREDENTIALS_READ"], 0)

    def test_the_response_is_classified_as_mixed_rather_than_pure_configuration(self) -> None:
        exposes = self.record["what_the_documentation_says_it_exposes"]
        self.assertIs(exposes["it_is_not_pure_configuration_metadata"], True)
        self.assertEqual(exposes["classification"], "SECRET_BEARING_MIXED_METADATA_SURFACE")

    def test_a_credential_bearing_surface_is_not_executed_as_a_metadata_probe(self) -> None:
        self.assertEqual(
            self.record["verdict"]["ENDPOINT_EXECUTION_SAFETY"], "SECRET_BEARING_DO_NOT_EXECUTE"
        )
        self.assertIn("API key", self.record["the_credential_finding"]["exact_wording"])

    def test_avoiding_measurement_does_not_justify_credential_exposure(self) -> None:
        self.assertIn(
            "credential", self.record["why_it_was_looked_at_at_all"]["the_trap_in_that_appeal"]
        )

    def test_the_port_list_is_not_attributed_to_datascan(self) -> None:
        gap = self.record["the_configuration_semantic_gap"]
        self.assertEqual(gap["USER_API_PORT_LIST_RESOURCE_MAPPING"], "UNKNOWN")
        self.assertEqual(gap["whether_the_list_is_datascan_specific"], "NOT_DOCUMENTED")
        self.assertTrue(gap["the_inference_refused"].strip())

    def test_both_refusal_reasons_are_independent(self) -> None:
        self.assertTrue(self.record["verdict"]["both_reasons_are_independent"].strip())


class TestRetentionSilenceIsUnknown(unittest.TestCase):
    """§48.20 to §48.25."""

    def setUp(self) -> None:
        self.record = _load(RETENTION)

    def test_the_datascan_horizon_is_recorded(self) -> None:
        self.assertEqual(self.record["retention_horizons"]["datascan_horizon"], "7 months")

    def test_truncation_is_not_removal(self) -> None:
        raw = self.record["raw_response_field"]
        self.assertEqual(raw["post_30_day_treatment"], "TRUNCATED to 4KB")
        self.assertEqual(raw["is_not"], "REMOVED")
        self.assertEqual(raw["B3"], "PASS")
        self.assertIs(raw["reopened"], False)

    def test_the_optimisation_sentence_is_quoted_exactly(self) -> None:
        verbatim = self.record["the_optimisation_sentence"]["verbatim"]
        self.assertIn("we remove some fields", verbatim)
        self.assertIn("truncate data field to 4KB", verbatim)

    def test_the_removed_fields_are_unnamed_and_stay_unknown(self) -> None:
        removed = self.record["the_optimisation_sentence"]["two_operations_not_one"]["REMOVED"]
        self.assertIn("does not name", removed)

    def test_each_location_field_is_independent(self) -> None:
        fields = self.record["location_fields"]
        for name in ("ip", "@timestamp", "node.id", "node.country", "node.physicalcountry"):
            self.assertEqual(fields[name]["post_30_day_state"], "UNKNOWN", name)

    def test_ip_retention_was_not_guessed_from_usefulness(self) -> None:
        refused = self.record["arguments_available_and_refused"]
        self.assertIn(
            "sensible provider", refused["the_archive_would_be_useless_without_addresses"]
        )

    def test_timestamp_retention_was_not_guessed_from_historical_querying(self) -> None:
        refused = self.record["arguments_available_and_refused"]
        self.assertIn("does not prove", refused["historical_querying_proves_timestamps_survive"])

    def test_a_documented_schema_is_not_a_retention_promise(self) -> None:
        refused = self.record["arguments_available_and_refused"]
        self.assertIn(
            "never how long it lives", refused["the_fields_are_documented_so_they_are_retained"]
        )

    def test_the_verdicts_agree_with_the_fields(self) -> None:
        verdict = self.record["verdict"]
        self.assertEqual(verdict["ADDRESS_RETENTION"], "UNKNOWN")
        self.assertEqual(verdict["OBSERVATION_TIME_RETENTION"], "UNKNOWN")
        self.assertEqual(verdict["VANTAGE_FIELD_RETENTION"], "UNKNOWN")
        self.assertEqual(verdict["RAW_RESPONSE_RETENTION"], "TRUNCATED_NOT_REMOVED")


class TestTheSupportChannelWasCitedNotInferred(unittest.TestCase):
    """§48.26 to §48.29."""

    def setUp(self) -> None:
        self.record = _load(CONTACT)

    def test_it_is_established_from_a_first_party_publication(self) -> None:
        evidence = self.record["the_new_first_party_evidence"]
        self.assertEqual(evidence["how_established"], "RETRIEVED_FROM_FIRST_PARTY_PAGE")
        self.assertTrue(evidence["url"].startswith("https://blog.onyphe.io/"))
        self.assertTrue(evidence["verbatim_instruction"].strip())

    def test_it_was_not_inferred_from_spelling(self) -> None:
        self.assertIs(self.record["the_new_first_party_evidence"]["inferred_from_spelling"], False)

    def test_the_address_is_recorded_as_printed(self) -> None:
        printed = self.record["the_new_first_party_evidence"]["address_as_printed"]
        self.assertIn("[at]", printed)
        self.assertIn("{dot}", printed)

    def test_it_was_not_normalised_into_a_usable_mailbox(self) -> None:
        on_form = self.record["on_the_printed_form"]
        self.assertIs(on_form["normalised_into_a_usable_mailbox_by_this_mission"], False)
        self.assertTrue(on_form["how_this_differs_from_the_netlas_case"].strip())

    def test_mission_1_65_is_not_rewritten(self) -> None:
        self.assertIs(self.record["mission_1_65_rewritten"], False)
        self.assertIs(self.record["append_only"], True)
        self.assertIs(self.record["what_mission_1_65_recorded"]["was_it_accurate"], True)

    def test_the_mission_1_65_record_still_says_what_it_said(self) -> None:
        provenance = _load(ONYPHE_ENVELOPE)["recipient_provenance"]
        self.assertIn("No such channel is published", provenance["what_it_is_not"])

    def test_finding_a_mailbox_moves_no_gate(self) -> None:
        self.assertIn("no gate moves", self.record["verdict"]["apparatus_effect"])


class TestTheDispatchIsUntouched(unittest.TestCase):
    """§48.30 to §48.33."""

    def test_the_sent_enquiry_still_hashes_to_its_sent_value(self) -> None:
        self.assertEqual(
            hashlib.sha256(ONYPHE_ENQUIRY_MD.read_bytes()).hexdigest(), ONYPHE_CONTENT_SHA256
        )
        self.assertIs(_load(REASSESSMENT)["the_enquiry_was_not_edited"]["edited"], False)

    def test_one_send_still_stands(self) -> None:
        self.assertEqual(_load(ATTESTATION)["exactly_once"]["send_count"], 1)
        self.assertIs(_load(CONTACT)["what_this_does_not_authorise"]["resend_to_support"], False)
        self.assertEqual(_load(CONTACT)["what_this_does_not_authorise"]["one_send_stands"], 1)

    def test_no_second_enquiry_and_no_second_envelope(self) -> None:
        not_authorised = _load(CONTACT)["what_this_does_not_authorise"]
        self.assertIs(not_authorised["second_enquiry_created"], False)
        self.assertIs(not_authorised["new_dispatch_envelope_created"], False)
        self.assertIs(not_authorised["previous_manual_send_superseded"], False)

    def test_no_mailbox_was_searched_and_no_reply_inferred(self) -> None:
        self.assertEqual(_load(BASELINE)["request_accounting"]["MAILBOX_SEARCHES"], 0)
        boundaries = _load(RECONCILIATION)["boundaries_held"]
        self.assertIs(boundaries["mailbox_searched"], False)
        self.assertIs(boundaries["provider_reply_checked"], False)
        self.assertIs(boundaries["provider_reply_inferred"], False)

    def test_the_provider_response_status_did_not_move(self) -> None:
        self.assertEqual(
            _load(ATTESTATION)["provider_response"]["status"], "NOT_CHECKED_AFTER_DISPATCH"
        )

    def test_netlas_is_untouched(self) -> None:
        self.assertIsNone(_load(NETLAS_ENVELOPE)["recipient_address"])
        boundaries = _load(RECONCILIATION)["boundaries_held"]
        self.assertIs(boundaries["netlas_sent"], False)
        self.assertIs(boundaries["netlas_address_guessed"], False)


class TestTheThreeQuestionsWereReassessedIndependently(unittest.TestCase):
    """§G. One answered subpart may not stand for a whole question."""

    def setUp(self) -> None:
        self.record = _load(REASSESSMENT)
        self.questions = {q["n"]: q for q in self.record["questions"]}

    def test_all_three_questions_are_covered(self) -> None:
        self.assertEqual(set(self.questions), {1, 2, 3})

    def test_question_2_keeps_its_three_subparts_apart(self) -> None:
        subparts = self.questions[2]["subparts"]
        self.assertEqual(len(subparts), 3)
        labels = " ".join(s["subpart"] for s in subparts)
        self.assertIn("TCP/22", labels)
        self.assertIn("current", labels)
        self.assertIn("date", labels)

    def test_question_3_classifies_each_field_independently(self) -> None:
        fields = {s["field"] for s in self.questions[3]["subparts"]}
        self.assertIn("ip", fields)
        self.assertIn("@timestamp", fields)

    def test_no_question_was_answered_by_public_documentation(self) -> None:
        self.assertEqual(self.record["summary"]["questions_answered_by_public_documentation"], 0)

    def test_the_honest_reading_is_recorded(self) -> None:
        self.assertTrue(self.record["summary"]["the_honest_reading"].strip())

    def test_no_question_was_added_or_removed(self) -> None:
        self.assertIs(self.record["summary"]["no_question_was_added_or_removed"], True)


class TestNoGateMovedAndNothingQualifies(unittest.TestCase):
    """§48.34 to §48.38."""

    def test_zero_gates_changed(self) -> None:
        package = _load(PACKAGE)
        self.assertEqual(package["gates_changed_this_mission"], 0)
        for name, gate in package["gates"].items():
            self.assertIs(gate["changed"], False, name)

    def test_partial_and_unknown_cannot_qualify(self) -> None:
        status = _load(PACKAGE)["individual_status"]
        self.assertIs(status["PARTIAL_cannot_qualify"], True)
        self.assertIs(status["UNKNOWN_cannot_qualify"], True)
        self.assertEqual(status["verdict"], "INDIVIDUALLY_UNRESOLVED")

    def test_a_better_contact_route_did_not_qualify_the_apparatus(self) -> None:
        self.assertEqual(_load(PACKAGE)["individual_status"]["verdict"], "INDIVIDUALLY_UNRESOLVED")
        self.assertIn("no gate moves", _load(CONTACT)["verdict"]["apparatus_effect"])

    def test_pair_readiness_needs_two_qualified(self) -> None:
        readiness = _load(READINESS)
        self.assertEqual(readiness["qualified_apparatus_count"], 0)
        self.assertIs(readiness["pair_analysis_ready"], False)
        self.assertEqual(readiness["minimum_required"], 2)

    def test_no_pair_was_selected(self) -> None:
        pair = _load(READINESS)["no_pair_work_was_performed"]
        for counter in ("pairs_compared", "pairs_ranked", "pairs_selected"):
            self.assertEqual(pair[counter], 0, counter)

    def test_the_construct_was_not_narrowed(self) -> None:
        construct = _load(READINESS)["measurement_construct_unchanged"]
        self.assertIn("SSH-", construct["quantity"])
        self.assertIs(construct["substituted_with_a_protocol_label"], False)
        self.assertIs(construct["substituted_with_a_vendor_product"], False)


class TestNothingWasExecutedOrMutated(unittest.TestCase):
    """§48.40 to §48.44."""

    def test_no_api_of_any_kind_was_executed(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        for name in (
            "ONYPHE_DATA_API_EXECUTIONS",
            "USER_API_EXECUTIONS",
            "SEARCH_API_EXECUTIONS",
            "EXPORT_API_EXECUTIONS",
            "SUMMARY_API_EXECUTIONS",
            "SIMPLE_API_EXECUTIONS",
            "DISCOVERY_API_EXECUTIONS",
            "ONDEMAND_SCAN_EXECUTIONS",
        ):
            self.assertEqual(acct[name], 0, name)

    def test_no_measurement_was_retrieved(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        for name in (
            "MEASUREMENT_QUERIES",
            "COUNTS_FETCHED",
            "HOST_RECORDS_FETCHED",
            "BANNERS_FETCHED",
        ):
            self.assertEqual(acct[name], 0, name)

    def test_no_trial_and_no_purchase(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        self.assertEqual(acct["TRIALS"], 0)
        self.assertEqual(acct["PURCHASES"], 0)

    def test_no_source_was_registered_and_no_governance_review_created(self) -> None:
        boundaries = _load(RECONCILIATION)["boundaries_held"]
        self.assertEqual(boundaries["sources_registered"], 0)
        self.assertEqual(boundaries["governance_reviews"], 0)

    def test_no_canonical_mutation(self) -> None:
        for name, value in _load(BASELINE)["canonical_mutations"].items():
            if name.startswith("$"):
                continue
            self.assertIn(value, (0, 0.0, False), name)

    def test_no_reliability_assigned_and_no_independence_group(self) -> None:
        boundaries = _load(RECONCILIATION)["boundaries_held"]
        self.assertEqual(boundaries["reliability_assigned"], 0)
        self.assertEqual(boundaries["independence_groups_created"], 0)

    def test_no_model_and_no_embedding(self) -> None:
        acct = _load(BASELINE)["request_accounting"]
        self.assertEqual(acct["MODEL_CALLS"], 0)
        self.assertEqual(acct["EMBEDDINGS"], 0)

    def test_problem_family_stays_parked_and_the_profile_uncalibrated(self) -> None:
        boundaries = _load(RECONCILIATION)["boundaries_held"]
        self.assertEqual(boundaries["problem_family"], "PARKED")
        self.assertEqual(boundaries["reference_profile"], "UNCALIBRATED")


class TestTheOutcomeIsNotForced(unittest.TestCase):
    """Outcome C is a valid successful mission, and B was declined for a reason."""

    def setUp(self) -> None:
        self.record = _load(RECONCILIATION)

    def test_the_outcome_is_reconciled_residuals_remain(self) -> None:
        self.assertEqual(
            self.record["primary_outcome"],
            "ONYPHE_PUBLIC_DOCUMENTATION_RECONCILED_RESIDUALS_REMAIN",
        )
        self.assertTrue(self.record["this_is_a_valid_successful_mission"].strip())

    def test_outcome_b_was_declined_because_the_closed_question_moves_no_gate(self) -> None:
        why = self.record["why_this_outcome_and_not_another"]["why_not_B"]
        self.assertIn("moves no gate", why)
        self.assertIn("opposite", why)

    def test_drift_between_two_pages_was_not_called_a_contradiction(self) -> None:
        why = self.record["why_this_outcome_and_not_another"]["why_not_F"]
        self.assertIn("different moments", why)

    def test_the_reusable_observation_is_stated(self) -> None:
        reusable = self.record["the_reusable_observation"]
        self.assertIn("unpublished answer", reusable["statement"])
        self.assertTrue(reusable["why_that_difference_is_operational"].strip())

    def test_the_secondary_outcomes_agree_with_the_reviews(self) -> None:
        secondary = self.record["secondary_outcomes"]
        self.assertIs(secondary["B2_PARTIAL"], True)
        self.assertIs(secondary["DATASCAN_TCP22_UNKNOWN"], True)
        self.assertIs(secondary["USER_API_SECRET_BEARING_DO_NOT_EXECUTE"], True)
        self.assertIs(secondary["ONYPHE_SUPPORT_CONTACT_CHANNEL_ESTABLISHED"], True)
        self.assertEqual(secondary["TOTAL_QUALIFIED_APPARATUSES"], 0)

    def test_the_stop_condition_holds_in_every_clause(self) -> None:
        for name, value in self.record["stop_condition"].items():
            if name.startswith("$") or name == "awaiting":
                continue
            self.assertIs(value, False, name)


class TestNoRecordOverclaims(unittest.TestCase):
    """A methodology review is not a market finding."""

    def test_no_record_uses_commercial_or_adoption_vocabulary(self) -> None:
        for path in ALL_RECORDS:
            for sentence in _prose(_load(path)):
                tokens = set(re.findall(r"[a-z0-9]+", sentence.lower()))
                for term in (
                    "installation",
                    "customer",
                    "subscription",
                    "revenue",
                    "adoption",
                    "demand",
                ):
                    self.assertNotIn(term, tokens, f"{path.name}: {sentence[:80]!r}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
