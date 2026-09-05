"""Mission 1.70. A coverage surface is not a population until membership means something.

Q1 entered this mission with what no earlier class had: two independent producers, dated
artifacts on both sides, raw headers on one, and coverage published rather than hidden.
It leaves with the coverage published and its SEMANTICS undocumented on both sides at
once — neither Common Crawl nor HTTP Archive states whether a URL that was attempted and
failed appears in what it publishes.

That is not a small gap and it is not the same gap as a hidden discovery frame. A hidden
frame means you cannot say which items were eligible. This means you cannot say whether
an item's ABSENCE is a fact about the world or a fact about the apparatus — and a
proposition over a jointly covered population would then have a denominator neither side
can describe.

So the tests here are mostly about readings this mission was offered and did not take:

  - a successfully fetched set is not a planned target set and not an attempted set;
  - a rule written before retrieval is preregistered only if what it selects on is
    defined, so ordering is necessary and never sufficient;
  - an HTTP status code sitting in a coverage index is measurement content, whatever
    column it occupies;
  - a dated release is not an immutable one, and a browser page load is not a bot fetch;
  - a recommendation to obtain legal advice is not a grant;
  - and an operator-run fetcher is neither independent because we would run it nor
    authorised because it is feasible.

Nothing was crawled, queried, downloaded, fetched, registered or measured.
"""

from __future__ import annotations

import ast
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

BASELINE = DATA / "mission-1.70-baseline-v1.json"
POPULATION = DATA / "fixed-corpus-population-preselection-review-v1.json"
CC = DATA / "common-crawl-route-qualification-v1.json"
HA = DATA / "http-archive-route-qualification-v1.json"
COMPAT = DATA / "http-request-contract-compatibility-v1.json"
TEMPORAL = DATA / "web-route-temporal-compatibility-v1.json"
RIGHTS = DATA / "web-route-rights-feasibility-v1.json"
FETCHER = DATA / "sros-bounded-http-fetcher-feasibility-v1.json"
QUALIFICATION = DATA / "fixed-corpus-web-route-qualification-v1.json"
DECISION = DATA / "quantity-class-selection-decision-v2.json"

DECISION_V1 = DATA / "quantity-class-selection-decision-v1.json"
APPARATUS = DATA / "observation-addressable-apparatus-contract-v1.json"
SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"
RENDERER = SCRIPTS / "render_web_route_qualification.py"

PAGE = DATA / "mission-1.70-web-route-qualification-v1.md"
POPULATION_PAGE = DATA / "fixed-corpus-population-preselection-review-v1.md"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def entries(block: dict):
    return [(k, v) for k, v in block.items() if not k.startswith("$")]


class TestRecordsExist(unittest.TestCase):
    def test_every_mission_record_exists(self):
        for path in (BASELINE, POPULATION, CC, HA, COMPAT, TEMPORAL, RIGHTS, FETCHER,
                     QUALIFICATION, DECISION):
            self.assertTrue(path.exists(), path.name)

    def test_the_renderer_exists(self):
        self.assertTrue(RENDERER.exists())

    def test_both_pages_were_generated(self):
        self.assertTrue(PAGE.exists())
        self.assertTrue(POPULATION_PAGE.exists())

    def test_no_selected_class_artifact_exists(self):
        """§41. The artifact exists only if Q1 became strategically viable, and it did not."""
        self.assertFalse(SELECTED_CLASS.exists())

    def test_no_selected_construct_artifact_exists(self):
        """§42. A construct belongs to a later mission whatever this one concluded."""
        self.assertFalse(SELECTED_CONSTRUCT.exists())


class TestScope(unittest.TestCase):
    def setUp(self):
        self.baseline = load(BASELINE)

    def test_the_scope_is_q1_only(self):
        self.assertEqual(
            self.baseline["scope"]["in_scope_class"], "FIXED_CORPUS_HTTP_OBSERVATION"
        )

    def test_no_broad_class_discovery(self):
        self.assertIs(self.baseline["scope"]["broad_class_discovery_performed"], False)

    def test_seven_classes_stay_closed(self):
        closed = self.baseline["scope"]["classes_not_reopened"]
        for cid in ("Q0", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7"):
            self.assertIn(cid, closed)

    def test_the_scanner_class_was_not_reopened(self):
        self.assertIs(self.baseline["scope"]["scanner_class_reopened"], False)

    def test_the_scanner_arc_is_still_parked_and_reopenable(self):
        self.assertEqual(
            self.baseline["parallel_state_untouched"]["scanner_arc_status"],
            "PARKED_BUT_REOPENABLE_ON_NEW_FIRST_PARTY_EVIDENCE",
        )

    def test_the_baseline_records_no_drift(self):
        self.assertEqual(self.baseline["canonical_baseline"]["drift_from_mission_1_69"], "none")

    def test_the_documentation_budget_was_not_exceeded(self):
        budget = self.baseline["documentation_budget"]
        self.assertLessEqual(budget["used"], budget["maximum_first_party_requests"])
        self.assertEqual(sum(budget["split"].values()), budget["used"])


class TestPopulationConcepts(unittest.TestCase):
    """§4 to §6. Four concepts, and the whole mission turns on keeping them apart."""

    def setUp(self):
        self.review = load(POPULATION)

    def test_all_four_concepts_are_defined(self):
        concepts = self.review["the_four_population_concepts"]
        for name in ("TARGET_POPULATION", "ATTEMPTED_POPULATION", "OBSERVABLE_POPULATION",
                     "SUCCESSFUL_OBSERVATION_SET"):
            self.assertTrue(str(concepts[name]).strip(), name)

    def test_the_concepts_are_not_used_interchangeably(self):
        self.assertIs(self.review["the_four_population_concepts"]["used_interchangeably"], False)

    def test_neither_route_is_classified_as_an_attempted_set(self):
        """A successfully fetched set called an attempted set is the mission's core error."""
        for route, entry in entries(self.review["coverage_classification_per_route"]):
            self.assertNotEqual(entry["classification"], "ATTEMPTED_SET", route)

    def test_common_crawl_cannot_reconstruct_its_targeted_set(self):
        entry = self.review["coverage_classification_per_route"]["COMMON_CRAWL"]
        self.assertIs(entry["targeted_set_reconstructable"], False)

    def test_both_routes_can_reconstruct_what_they_captured(self):
        for route, entry in entries(self.review["coverage_classification_per_route"]):
            self.assertIs(entry["captured_set_reconstructable"], True, route)

    def test_every_coverage_classification_carries_a_reason(self):
        for route, entry in entries(self.review["coverage_classification_per_route"]):
            self.assertTrue(str(entry["why"]).strip(), route)

    def test_outcome_dependence_is_open_rather_than_asserted(self):
        """§6. Undocumented is not established-as-success-conditioned."""
        self.assertIs(self.review["outcome_dependence"]["established_as_outcome_dependent"], False)

    def test_both_routes_have_an_outcome_dependence_classification(self):
        outcome = self.review["outcome_dependence"]
        for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
            self.assertIn(
                outcome[route],
                {"COVERAGE_MAY_BE_OUTCOME_DEPENDENT", "COVERAGE_NOT_OUTCOME_DEPENDENT"},
            )


class TestMeasurementInsideCoverage(unittest.TestCase):
    """§8. An HTTP status in an index is measurement content wherever it sits."""

    def setUp(self):
        self.review = load(POPULATION)

    def test_the_semantic_boundary_is_addressed(self):
        self.assertTrue(
            str(self.review["metadata_value_boundary"]["the_semantic_boundary_is_not"]).strip()
        )

    def test_common_crawl_coverage_carries_a_status_field(self):
        fields = self.review["metadata_value_boundary"][
            "measurement_fields_present_in_coverage_surfaces"]["COMMON_CRAWL"]
        self.assertTrue({"status", "fetch_status"} & set(fields))

    def test_http_archive_coverage_carries_a_measurement_field(self):
        fields = self.review["metadata_value_boundary"][
            "measurement_fields_present_in_coverage_surfaces"]["HTTP_ARCHIVE"]
        self.assertTrue(fields)

    def test_the_common_crawl_index_status_is_the_fetch_status(self):
        """The CDXJ definition is the reason coverage cannot be called pure metadata."""
        blob = json.dumps(load(CC))
        self.assertIn("HTTP status code", blob)


class TestPopulationDecision(unittest.TestCase):
    """§36 to §38."""

    def setUp(self):
        self.review = load(POPULATION)

    def test_the_decision_is_the_operator_fetcher_one(self):
        self.assertEqual(
            self.review["decision"], "EXTERNALLY_FROZEN_POPULATION_REQUIRES_OPERATOR_FETCHER"
        )

    def test_all_five_strategies_were_evaluated_with_reasons(self):
        strategies = dict(entries(self.review["strategies_evaluated"]))
        for name in ("P1_provider_native_intersection",
                     "P2_frozen_C_plus_planned_target_coverage",
                     "P3_frozen_C_plus_attempted_coverage",
                     "P4_frozen_C_plus_realized_successful_coverage",
                     "P5_missingness_preserving"):
            self.assertIn(name, strategies)
            self.assertTrue(str(strategies[name]["why"]).strip(), name)

    def test_realized_successful_cocoverage_was_not_accepted(self):
        """§7. The one strategy that would quietly select on the outcome."""
        strategies = self.review["strategies_evaluated"]
        self.assertIs(
            strategies["P4_frozen_C_plus_realized_successful_coverage"]["accepted"], False
        )

    def test_the_missingness_preserving_strategy_was_taken_seriously(self):
        self.assertIs(
            self.review["strategies_evaluated"]["P5_missingness_preserving"][
                "considered_seriously"], True
        )

    def test_the_a_conditions_are_not_satisfied(self):
        self.assertNotEqual(self.review["conditions_for_A"]["verdict"], "SATISFIED")

    def test_the_a_conditions_carry_unknowns(self):
        unknown = [
            k for k, v in entries(self.review["conditions_for_A"])
            if isinstance(v, str) and v == "UNKNOWN"
        ]
        self.assertTrue(unknown)

    def test_ordering_alone_is_not_preregistration(self):
        """§10. Writing the rule first is necessary and is not sufficient."""
        ordering = self.review["temporal_ordering"]
        self.assertIs(ordering["called_automatically_preregistered"], False)
        self.assertTrue(str(ordering["why_that_ordering_is_not_sufficient"]).strip())

    def test_two_denominators_are_two_propositions(self):
        self.assertIs(
            self.review["denominator_discipline"][
                "different_denominators_called_the_same_proposition"], False
        )

    def test_the_review_states_what_it_does_not_establish(self):
        self.assertTrue(self.review["what_this_does_not_establish"])


class TestCommonCrawlRoute(unittest.TestCase):
    def setUp(self):
        self.record = load(CC)

    def test_a_date_is_not_immutability(self):
        self.assertIs(self.record["crawl_identity"]["date_alone_is_not_immutability"], True)
        self.assertIs(self.record["immutability"]["inferred_from_a_date"], False)

    def test_url_selection_was_not_established(self):
        """§14. No first-party page carrying the selection procedure was opened."""
        self.assertEqual(self.record["url_selection"]["status"], "NOT_ESTABLISHED_THIS_MISSION")

    def test_a_search_summary_offered_an_answer_and_was_not_used(self):
        """The Mission 1.63 guard, met again and again refused."""
        summary = self.record["url_selection"][
            "a_search_summary_offered_an_answer_and_it_was_not_used"]
        self.assertIs(summary["used"], False)

    def test_the_corpus_is_not_called_complete(self):
        self.assertIs(self.record["sampling"]["called_a_complete_web_corpus"], False)

    def test_nothing_was_queried_or_downloaded(self):
        self.assertIs(self.record["no_index_query_executed"], True)
        self.assertIs(self.record["no_warc_wat_wet_downloaded"], True)

    def test_the_route_is_plausible_and_not_qualified(self):
        self.assertEqual(self.record["route_status"], "ROUTE_PLAUSIBLE_REQUIRES_CONSTRUCT_DETAIL")


class TestHttpArchiveRoute(unittest.TestCase):
    def setUp(self):
        self.record = load(HA)

    def test_header_availability_is_evidenced_rather_than_assumed(self):
        self.assertIs(self.record["response_availability"]["assumed_rather_than_evidenced"], False)

    def test_response_headers_are_structured_rather_than_raw(self):
        self.assertEqual(
            self.record["response_availability"]["classification"],
            "STRUCTURED_RESPONSE_HEADERS_AVAILABLE",
        )

    def test_no_redirect_predicate_binding_was_chosen(self):
        """§21. The main document AFTER redirects is not the response to the requested URL."""
        self.assertIs(self.record["redirects"]["predicate_binding_chosen"], False)

    def test_a_browser_load_is_not_a_bot_fetch(self):
        self.assertIs(self.record["browser_semantics"]["treated_as_identical_to_a_bot_fetch"], False)

    def test_the_pages_table_carries_no_failure_column(self):
        """One row per page TESTED, and nothing saying whether the test succeeded."""
        pages = self.record["pages_table"]
        self.assertIs(pages["failure_indicator_present"], False)
        for column in pages["columns"]:
            self.assertNotIn("fail", column.lower())
            self.assertNotIn("error", column.lower())
            self.assertNotIn("status", column.lower())

    def test_the_attempt_level_fields_live_in_the_metadata_blob(self):
        """retry_count, tested_url and visited are attempt-level and carry no test status."""
        blob = self.record["page_metadata_blob"]
        for field in ("retry_count", "tested_url", "visited"):
            self.assertIn(field, json.dumps(blob))

    def test_nothing_was_executed_or_downloaded(self):
        self.assertIs(self.record["no_bigquery_executed"], True)
        self.assertIs(self.record["no_har_downloaded"], True)

    def test_the_route_is_plausible_and_not_qualified(self):
        self.assertEqual(self.record["route_status"], "ROUTE_PLAUSIBLE_REQUIRES_CONSTRUCT_DETAIL")


class TestRequestContractCompatibility(unittest.TestCase):
    """§23 to §25. A table, then a verdict — never a verdict alone."""

    def setUp(self):
        self.record = load(COMPAT)

    def test_no_opaque_pass_was_issued(self):
        self.assertIs(self.record["opaque_pass_issued_without_the_table"], False)

    def test_the_table_is_not_empty(self):
        self.assertTrue(self.record["fields"])

    def test_the_tally_matches_the_table(self):
        counted = {"MATCHABLE": 0, "DIFFERENT_BUT_NON_LOAD_BEARING": 0,
                   "DIFFERENT_AND_LOAD_BEARING": 0, "UNKNOWN": 0}
        for entry in self.record["fields"]:
            counted[entry["classification"]] += 1
        self.assertEqual(counted, self.record["tally"])

    def test_compatibility_was_not_established(self):
        self.assertEqual(self.record["overall"], "REQUEST_CONTRACT_COMPATIBILITY_NOT_ESTABLISHED")

    def test_load_bearing_differences_exist(self):
        self.assertGreater(self.record["tally"]["DIFFERENT_AND_LOAD_BEARING"], 0)

    def test_no_field_is_matchable(self):
        self.assertEqual(self.record["tally"]["MATCHABLE"], 0)

    def test_the_shared_world_state_family_is_conditional(self):
        self.assertEqual(
            self.record["same_world_state_family"]["classification"],
            "SAME_HTTP_WORLD_STATE_FAMILY_PLAUSIBLE_CONDITIONAL",
        )

    def test_request_equivalence_is_not_claimed_as_documented(self):
        self.assertIs(
            self.record["same_world_state_family"][
                "client_relative_propositions_are_allowed_if_explicit"]["equivalence_documented"],
            False,
        )


class TestTemporalCompatibility(unittest.TestCase):
    def setUp(self):
        self.record = load(TEMPORAL)

    def test_temporal_compatibility_is_plausible_and_unestablished(self):
        self.assertEqual(self.record["overall"], "TEMPORAL_COMPATIBILITY_PLAUSIBLE_NOT_ESTABLISHED")

    def test_neither_route_treats_a_date_as_immutability(self):
        for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
            self.assertIs(self.record["routes"][route]["date_treated_as_immutability"], False)

    def test_both_immutabilities_are_partial(self):
        for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
            self.assertEqual(self.record["routes"][route]["immutability"], "PARTIAL")


class TestRightsFeasibility(unittest.TestCase):
    """§28 to §30. Feasibility, and never approval."""

    def setUp(self):
        self.record = load(RIGHTS)

    def test_this_is_not_a_governance_review(self):
        self.assertIs(self.record["this_is_not_a_governance_review"], True)

    def test_no_source_was_registered_and_no_governance_mutated(self):
        self.assertEqual(self.record["sources_registered"], 0)
        self.assertEqual(self.record["source_governance_mutated"], 0)

    def test_rights_were_not_turned_into_approval(self):
        self.assertIs(self.record["turned_into_governance_approval"], False)

    def test_common_crawl_requires_a_rights_review(self):
        """A recommendation to obtain legal counsel is not a grant."""
        self.assertEqual(
            self.record["routes"]["COMMON_CRAWL"]["classification"], "ROUTE_RIGHTS_REVIEW_REQUIRED"
        )

    def test_http_archive_rights_are_unknown(self):
        self.assertEqual(self.record["routes"]["HTTP_ARCHIVE"]["classification"], "UNKNOWN")

    def test_commercial_purpose_compatibility_is_not_established(self):
        self.assertEqual(
            self.record["commercial_purpose_compatibility"],
            "NOT_ESTABLISHED_ON_EITHER_ROUTE",
        )


class TestOperatorFetcher(unittest.TestCase):
    """§31 to §35. An architecture, and nothing that ran."""

    def setUp(self):
        self.record = load(FETCHER)

    def test_nothing_was_implemented_or_crawled(self):
        self.assertIs(self.record["implemented"], False)
        self.assertIs(self.record["crawled"], False)
        self.assertEqual(self.record["http_measurement_requests"], 0)

    def test_governance_requires_a_dedicated_review(self):
        self.assertEqual(
            self.record["governance_feasibility"]["classification"], "REQUIRES_DEDICATED_REVIEW"
        )

    def test_this_mission_authorised_nothing(self):
        self.assertIs(self.record["governance_feasibility"]["authorised_by_this_mission"], False)

    def test_the_review_conditions_are_named(self):
        self.assertTrue(
            self.record["governance_feasibility"]["conditions_a_future_review_would_have_to_settle"]
        )

    def test_running_it_ourselves_does_not_make_it_independent(self):
        self.assertIs(self.record["independence_architecture"]["automatically_independent"], False)

    def test_the_independence_architecture_is_plausible_and_not_settled(self):
        self.assertEqual(
            self.record["independence_architecture"]["classification"],
            "INDEPENDENCE_ARCHITECTURE_PLAUSIBLE",
        )

    def test_the_residual_is_stated(self):
        self.assertTrue(
            str(self.record["fallback_not_forced_solution"]["the_honest_residual"]).strip()
        )


class TestQualification(unittest.TestCase):
    def setUp(self):
        self.record = load(QUALIFICATION)

    def test_no_route_is_qualified(self):
        for name, entry in entries(self.record["routes"]):
            self.assertNotEqual(entry["status"], "ROUTE_QUALIFIED_FOR_CLASS", name)

    def test_the_record_agrees_with_its_own_route_statuses(self):
        self.assertIs(self.record["route_status_meaning"]["neither_route_reached_it"], True)

    def test_q1_is_not_strategically_viable(self):
        self.assertNotEqual(
            self.record["q1_strategic_conditions"]["verdict"], "STRATEGICALLY_VIABLE"
        )

    def test_the_load_bearing_failure_is_named(self):
        self.assertTrue(str(self.record["q1_strategic_conditions"]["load_bearing_failure"]).strip())

    def test_q1_status_is_unchanged_from_mission_1_69(self):
        self.assertEqual(
            self.record["q1_status"], "PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED"
        )
        self.assertIs(self.record["q1_status_changed_this_mission"], False)

    def test_the_record_lists_what_it_resolved_and_what_it_did_not(self):
        changed = self.record["what_did_change"]
        self.assertTrue(changed["resolved_this_mission"])
        self.assertTrue(changed["still_unresolved"])

    def test_no_construct_and_no_predicate(self):
        self.assertIs(self.record["no_construct_selected"], True)
        self.assertIs(self.record["no_predicate_chosen"], True)


class TestDecision(unittest.TestCase):
    def setUp(self):
        self.record = load(DECISION)

    def test_the_primary_outcome_is_the_operator_route_one(self):
        self.assertEqual(
            self.record["primary_outcome"], "FIXED_CORPUS_WEB_REQUIRES_OPERATOR_CONTROLLED_ROUTE"
        )

    def test_no_class_was_selected(self):
        self.assertIsNone(self.record["selected_quantity_class"])
        self.assertEqual(self.record["selection_outcome"], "NO_SELECTION")
        self.assertIs(self.record["selected_class_artifact_created"], False)

    def test_no_construct_was_selected(self):
        self.assertIs(self.record["selected_construct_created"], False)

    def test_the_registry_is_unchanged_at_fifteen(self):
        requirements = load(APPARATUS)["requirement_registry"]["requirements"]
        self.assertEqual(len(requirements), 15)
        self.assertEqual(self.record["requirement_registry"]["count_after"], 15)
        self.assertIsNone(self.record["requirement_registry"]["requirement_added"])

    def test_registry_growth_was_not_forced(self):
        self.assertIs(self.record["requirement_registry"]["registry_growth_forced"], False)

    def test_the_candidate_rule_was_offered_and_declined_with_a_reason(self):
        offered = self.record["requirement_registry"]["candidate_offered_and_not_added"]
        names = {r["name"] for r in load(APPARATUS)["requirement_registry"]["requirements"]}
        self.assertNotIn(offered["name"], names)
        self.assertTrue(str(offered["why_it_was_not_added"]).strip())

    def test_every_hard_zero_counter_is_zero(self):
        accounting = self.record["mission_accounting"]
        for counter in ("TARGET_VALUE_EXPOSURES", "MEASUREMENT_VALUES_RETRIEVED", "CRAWLS",
                        "TARGET_HTTP_REQUESTS", "HTTP_MEASUREMENT_REQUESTS",
                        "COMMON_CRAWL_INDEX_QUERIES", "WARC_WAT_WET_DOWNLOADS",
                        "BIGQUERY_EXECUTIONS", "HAR_DOWNLOADS", "TRIALS", "PURCHASES",
                        "ACCOUNTS_CREATED", "CREDENTIAL_READS", "MAILBOX_SEARCHES",
                        "ENQUIRIES_SENT", "SOURCES_REGISTERED", "GOVERNANCE_APPROVALS",
                        "THRESHOLDS_REGISTERED", "CLAIMS_CREATED", "EVIDENCE_CREATED",
                        "INDEPENDENCE_GROUPS_CREATED", "RELIABILITY_VALUES_ASSIGNED", "SCORES",
                        "MODEL_CALLS", "EMBEDDINGS", "MIGRATIONS", "CONSTRUCTS_FROZEN",
                        "PREDICATES_CHOSEN", "PAIRS_SELECTED", "CRAWLERS_IMPLEMENTED"):
            self.assertEqual(accounting[counter], 0, counter)

    def test_the_budget_was_respected(self):
        accounting = self.record["mission_accounting"]
        self.assertLessEqual(
            accounting["FIRST_PARTY_DOCUMENT_REQUESTS"], accounting["FIRST_PARTY_REQUEST_BUDGET"]
        )

    def test_onyphe_and_netlas_did_not_move(self):
        parallel = self.record["parallel_state_untouched"]
        self.assertEqual(parallel["onyphe_response_status"], "NOT_CHECKED_AFTER_DISPATCH")
        for key in ("onyphe_mailbox_searched", "onyphe_gmail_polled", "onyphe_reply_read",
                    "onyphe_follow_up_sent", "onyphe_state_changed", "netlas_address_decoded",
                    "netlas_address_guessed", "netlas_enquiry_sent", "netlas_state_changed",
                    "scanner_arc_reopened"):
            self.assertIs(parallel[key], False, key)

    def test_no_canonical_mutation(self):
        self.assertEqual(self.record["canonical_mutation_boundary"]["mutations_this_mission"], 0)

    def test_the_next_mission_was_not_started(self):
        self.assertIs(self.record["recommended_next_mission"]["mission_1_71_not_started"], True)

    def test_the_two_censuses_agree(self):
        baseline = load(BASELINE)["canonical_baseline"]
        census = self.record["canonical_mutation_boundary"]
        for key in ("claims", "evidence", "reliability_assessments", "registered_sources"):
            self.assertEqual(baseline[key], census[key], key)


class TestMission169IsNotRewritten(unittest.TestCase):
    """A record says what was established when it was written."""

    def test_the_previous_decision_still_selects_nothing(self):
        self.assertIsNone(load(DECISION_V1)["selected_quantity_class"])

    def test_the_previous_outcome_is_unchanged(self):
        self.assertEqual(
            load(DECISION_V1)["primary_outcome"],
            "FIXED_CORPUS_WEB_MEASUREMENT_PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED",
        )

    def test_this_mission_does_not_claim_to_have_edited_it(self):
        self.assertIs(load(DECISION)["mission_1_69_record_edited"], False)


class TestNothingWasMeasured(unittest.TestCase):
    def test_no_record_froze_an_exact_predicate(self):
        for path in (BASELINE, POPULATION, CC, HA, COMPAT, TEMPORAL, RIGHTS, FETCHER,
                     QUALIFICATION, DECISION):
            record = load(path)
            if "exact_predicate_frozen" in record:
                self.assertIs(record["exact_predicate_frozen"], False, path.name)

    def test_no_record_retrieved_target_values(self):
        for path in (BASELINE, POPULATION, CC, HA, COMPAT, TEMPORAL, RIGHTS, FETCHER,
                     QUALIFICATION, DECISION):
            record = load(path)
            if "target_values_retrieved" in record:
                self.assertEqual(record["target_values_retrieved"], 0, path.name)


class TestValidatorRefusals(unittest.TestCase):
    """The validator has to REFUSE, and a refusal that never fires is not a check."""

    def setUp(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("_wrq170", RENDERER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_the_live_records_validate(self):
        self.module.validate()

    def test_the_validator_defines_the_five_population_decisions(self):
        self.assertEqual(len(self.module.POPULATION_DECISIONS), 5)

    def test_the_validator_defines_the_four_compatibility_classes(self):
        self.assertEqual(len(self.module.COMPAT_CLASSES), 4)

    def test_the_measurement_field_set_names_the_status_columns(self):
        self.assertIn("status", self.module.MEASUREMENT_FIELDS)
        self.assertIn("fetch_status", self.module.MEASUREMENT_FIELDS)

    def test_the_census_exemption_is_named_rather_than_open(self):
        """§23, met an eleventh time. The exemption is three named blocks and no more."""
        self.assertEqual(
            set(self.module.CENSUS_BLOCKS),
            {"canonical_baseline", "canonical_mutation_boundary", "mission_accounting"},
        )

    def test_every_reliability_named_accounting_entry_is_a_hard_zero(self):
        """The exemption above is safe only because the hard-zero loop covers it."""
        accounting = load(DECISION)["mission_accounting"]
        for key in accounting:
            if "reliability" in key.lower():
                self.assertIn(key, self.module.HARD_ZERO_COUNTERS, key)


class TestRendererIsDeterministic(unittest.TestCase):
    def test_the_renderer_opens_no_socket_and_calls_no_model(self):
        tree = ast.parse(RENDERER.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for forbidden in ("requests", "httpx", "urllib", "socket", "openai", "anthropic"):
            self.assertNotIn(forbidden, imported, forbidden)

    def test_the_pages_name_the_outcome_they_render(self):
        page = PAGE.read_text(encoding="utf-8")
        self.assertIn("FIXED_CORPUS_WEB_REQUIRES_OPERATOR_CONTROLLED_ROUTE", page)
        self.assertIn("Selected class: NONE", page)

    def test_the_population_page_names_its_decision(self):
        page = POPULATION_PAGE.read_text(encoding="utf-8")
        self.assertIn("EXTERNALLY_FROZEN_POPULATION_REQUIRES_OPERATOR_FETCHER", page)


if __name__ == "__main__":
    unittest.main()
