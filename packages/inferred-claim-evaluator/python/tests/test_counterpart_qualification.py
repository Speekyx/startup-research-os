"""Mission 1.73. An independent HTTP producer exists, and it is two questions short.

Every apparatus this arc examined since Mission 1.58 failed on the temporal object: a
maintained current-state view, or a historical snapshot whose coverage nobody documents.
This mission's shift is that the counterpart does not need a historical dataset at all.
It can be an on-demand apparatus, and the window is then prospective by construction --
which dissolves the problem rather than solving it.

Globalping is that shape. It is directable at an exact target, its community-hosted
probes perform the request themselves, its per-result statuses name `failed` and
`offline` so apparatus trouble is distinguishable from target silence, its default
method is HEAD so a transport-only observation needs no body, and its measurement
carries createdAt and updatedAt.

Two questions remain and both are narrow. The 124 KB specification contains no
occurrence of the word redirect, and the probe's non-following behaviour is an
implementation rather than a documented contract. And the Permitted Use section scopes
the platform to the user's OWN infrastructure while reserving rights not expressly
granted.

So most of this file is about refusing the cheap readings: a brand is not a producer, an
implementation is not a contract, a free API is not permission, and a consumer-scoped
liability clause is not a blanket commercial prohibition.

Nothing was measured, submitted, executed or retrieved from a target.
"""

from __future__ import annotations

import ast
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

BASELINE = DATA / "mission-1.73-baseline-v1.json"
UNIVERSE = DATA / "independent-http-counterpart-universe-v1.json"
PRESCREEN = DATA / "independent-http-counterpart-prescreen-v1.json"
LEDGER = DATA / "mission-1.73-documentation-ledger-v1.json"
QUALIFICATION = DATA / "independent-http-counterpart-qualification-v1.json"
LINEAGE = DATA / "counterpart-measurement-lineage-v1.json"
CONTRACT = DATA / "counterpart-request-contract-compatibility-v1.json"
MINIMIZATION = DATA / "counterpart-result-minimization-v1.json"
RIGHTS = DATA / "counterpart-rights-feasibility-v1.json"
READINESS = DATA / "q1-two-route-readiness-v1.json"
DECISION = DATA / "quantity-class-selection-decision-v3.json"

SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"
APPARATUS_REGISTRY = DATA / "observation-addressable-apparatus-contract-v1.json"
GOVERNANCE_DECISION = DATA / "public-http-observation-governance-decision-v1.json"
APPARATUS_CONTRACT = DATA / "sros-bounded-http-apparatus-contract-v1.json"
ADR_039 = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "adr"
    / "ADR-039-public-http-observation-governance-track.md"
)

RENDERER = SCRIPTS / "render_counterpart_qualification.py"
PAGE = DATA / "mission-1.73-counterpart-qualification-v1.md"
MATRIX_PAGE = DATA / "counterpart-qualification-matrix-v1.md"

ALL_RECORDS = (
    BASELINE,
    UNIVERSE,
    PRESCREEN,
    LEDGER,
    QUALIFICATION,
    LINEAGE,
    CONTRACT,
    MINIMIZATION,
    RIGHTS,
    READINESS,
    DECISION,
)


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def selection_authorises_nothing(case, path):
    """Re-pointed by Mission 1.76.6. These files asserted the selection artifact did not
    exist, which was true until Mission 1.76.6 selected Q1. What each defends is that its own
    mission selected nothing, and that whatever selection exists authorises no run."""
    if not path.exists():
        return
    record = json.loads(path.read_text(encoding="utf-8"))
    case.assertEqual(record["state"], "CLASS_SELECTED")
    case.assertFalse(record["states_kept_apart"]["CONSTRUCT_SELECTED"])
    case.assertFalse(record["states_kept_apart"]["RUN_AUTHORIZED"])
    case.assertFalse(record["corpus_frozen"])
    case.assertEqual(record["measurements_executed"], 0)


class TestPreconditions(unittest.TestCase):
    def setUp(self):
        self.baseline = load(BASELINE)

    def test_mission_1_72_merged_at_the_expected_commit(self):
        pre = self.baseline["repository_precondition"]
        self.assertIs(pre["mission_1_72_merged"], True)
        self.assertEqual(pre["pull_request"], 117)
        self.assertEqual(pre["observed_main"], pre["expected_main"])
        self.assertEqual(pre["observed_main"], "a21547c")

    def test_the_baseline_is_unchanged(self):
        baseline = self.baseline["canonical_baseline"]
        self.assertEqual(baseline["drift_from_mission_1_72"], "none")
        self.assertEqual(baseline["migration_head"], "0035_refusal_provenance")
        for key, value in {
            "raw_records": 325,
            "claims": 44,
            "evidence": 58,
            "inferred_claims": 1,
            "reliability_assessments": 4,
            "evidence_independence_groups": 0,
            "registered_sources": 29,
            "embeddings": 0,
        }.items():
            self.assertEqual(baseline[key], value, key)

    def test_the_registry_starts_at_fifteen(self):
        self.assertEqual(self.baseline["requirement_registry"]["count_before"], 15)
        self.assertEqual(len(load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]), 15)

    def test_adr_039_is_present_and_the_public_http_track_stays_ready(self):
        self.assertTrue(ADR_039.exists())
        self.assertEqual(
            load(GOVERNANCE_DECISION)["decision"], "PUBLIC_HTTP_OBSERVATION_TRACK_ADOPTED"
        )

    def test_no_run_is_authorized_and_no_fetcher_exists(self):
        self.assertIs(
            self.baseline["repository_precondition"]["sros_fetcher_implementation_exists"], False
        )
        self.assertIs(load(APPARATUS_CONTRACT)["implemented"], False)
        self.assertIs(load(APPARATUS_CONTRACT)["run_authorization_required"], True)

    def test_the_search_scope_is_counterpart_only(self):
        scope = self.baseline["scope"]
        self.assertEqual(scope["searching_for"], "ONE_INDEPENDENT_HTTP_MEASUREMENT_COUNTERPART")
        for flag in (
            "quantity_class_discovery_performed",
            "scanner_discovery_performed",
            "general_web_source_discovery_performed",
            "common_crawl_http_archive_analysis_reopened",
            "market_landscape_produced",
        ):
            self.assertIs(scope[flag], False, flag)


class TestSearchDiscipline(unittest.TestCase):
    """§2, §3, §52, §53, §54."""

    def setUp(self):
        self.universe = load(UNIVERSE)
        self.ledger = load(LEDGER)

    def test_the_serious_candidate_budget_was_respected(self):
        self.assertLessEqual(
            self.universe["serious_candidates"], self.universe["serious_candidate_cap"]
        )
        self.assertIs(self.universe["cap_exceeded"], False)

    def test_discovery_stops_after_a_qualification(self):
        if self.universe["qualified_counterparts"]:
            self.assertIs(self.universe["discovery_stopped_after_first_qualification"], True)

    def test_no_exhaustive_market_claim(self):
        self.assertIs(self.universe["exhaustive_market_coverage_claimed"], False)

    def test_every_pre_gate_failure_names_its_cause(self):
        for candidate in self.universe["candidates"]:
            if candidate["status"] == "PRE_GATE_FAILED":
                self.assertTrue(str(candidate["pre_gate_failure"]).strip(), candidate["name"])

    def test_the_documentation_budget_was_respected_and_failures_counted(self):
        self.assertLessEqual(self.ledger["used"], self.ledger["maximum_requests"])
        self.assertEqual(len(self.ledger["requests"]), self.ledger["used"])
        self.assertIs(self.ledger["failed_counted_against_budget"], True)
        self.assertGreater(self.ledger["failed_or_empty"], 0)

    def test_search_engines_were_navigation_only(self):
        self.assertIs(self.ledger["search_engines_used_for_navigation_only"], True)

    def test_no_target_was_measured_and_no_counterpart_api_executed(self):
        self.assertEqual(self.ledger["target_sites_measured"], 0)
        self.assertEqual(self.ledger["counterpart_api_executions"], 0)

    def test_the_prescreen_says_what_it_does_not_establish(self):
        self.assertTrue(load(PRESCREEN)["what_this_does_not_establish"])


class TestProducerIdentity(unittest.TestCase):
    """§6, §7, §8, §30, §31, §33, §34, §35."""

    def setUp(self):
        self.lineage = load(LINEAGE)

    def test_the_producer_is_not_a_reseller_a_proxy_or_unknown(self):
        self.assertNotIn(
            self.lineage["producer_classification"],
            {"THIRD_PARTY_MEASUREMENT_UPSTREAM", "PURE_PROXY", "UNKNOWN"},
        )
        self.assertIs(self.lineage["reseller_or_passthrough"], False)
        self.assertIs(self.lineage["is_a_proxy_for_an_sros_request"], False)

    def test_shared_software_is_not_shared_measurement(self):
        shared = self.lineage["shared_software_with_sros"]
        self.assertTrue(str(shared["and_it_would_not_matter_by_itself"]).strip())

    def test_no_shared_observation_upstream(self):
        self.assertIs(self.lineage["shared_observation_upstream_with_sros"], False)
        common = self.lineage["common_upstream_measurement"]
        for upstream in ("common_crawl", "http_archive", "sros"):
            self.assertIs(common[upstream], False, upstream)

    def test_auxiliary_shared_infrastructure_does_not_defeat_independence(self):
        self.assertIs(
            self.lineage["common_upstream_measurement"]["auxiliary_sharing_defeats_independence"],
            False,
        )

    def test_the_sros_fetcher_elsewhere_is_not_a_counterpart(self):
        infra = self.lineage["sros_execution_infrastructure_is_not_a_counterpart"]
        self.assertIs(infra["running_the_sros_fetcher_elsewhere_creates_a_second_apparatus"], False)

    def test_an_externally_triggered_job_may_still_be_independent(self):
        triggered = self.lineage["externally_triggered_but_independently_produced"]
        self.assertIs(triggered["sros_initiates_the_job"], True)
        self.assertIs(triggered["that_makes_the_measurement_sros_produced"], False)

    def test_external_analysis_of_an_sros_response_is_not_independent(self):
        self.assertTrue(str(self.lineage["why_not_a_proxy"]).strip())

    def test_vantage_is_not_independence(self):
        vantage = self.lineage["vantage_is_not_independence"]
        self.assertIs(vantage["a_different_geography_is_independence"], False)
        self.assertIs(vantage["a_matching_geography_is_the_same_apparatus"], False)

    def test_marketing_language_was_not_used_as_evidence(self):
        self.assertIs(self.lineage["marketing_language_used_as_evidence"], False)

    def test_frame_uniformity_is_met_explicitly(self):
        """The registry rule Mission 1.67 added, satisfied by a provider statement."""
        frame = self.lineage["frame_uniformity"]
        self.assertIs(frame["satisfied"], True)
        self.assertIn("modify", frame["provider_statement"])


class TestQualificationMatrix(unittest.TestCase):
    """§44, §45, §46, §47."""

    def setUp(self):
        self.qualification = load(QUALIFICATION)
        self.gates = {g["dimension"]: g for g in self.qualification["gates"]}

    def test_all_twelve_dimensions_were_evaluated(self):
        self.assertEqual(len(self.gates), 12)
        for dimension in (
            "C1_DIRECTABLE_TARGET",
            "C2_OWN_MEASUREMENT_PRODUCTION",
            "C3_TERMINAL_SUBMISSION_ACCOUNTING",
            "C4_TRANSPORT_LEVEL_RESULT_SURFACE",
            "C5_PROSPECTIVE_TEMPORAL_ADDRESSABILITY",
            "C6_REQUEST_CONTRACT_RECONSTRUCTABILITY",
            "C7_VANTAGE_REVIEWABILITY",
            "C8_RESULT_MINIMIZATION",
            "C9_RIGHTS_FEASIBILITY",
            "C10_INDEPENDENCE_PLAUSIBILITY",
            "C11_BOUNDED_PILOT_FEASIBILITY",
            "C12_SAME_HTTP_WORLD_STATE_FAMILY",
        ):
            self.assertIn(dimension, self.gates, dimension)

    def test_every_pass_has_a_basis_and_every_gate_a_reason(self):
        for name, gate in self.gates.items():
            self.assertTrue(str(gate["why"]).strip(), name)
            if gate["status"] == "PASS":
                self.assertTrue(str(gate["basis"]).strip(), name)

    def test_every_unresolved_gate_names_a_residual(self):
        for name, gate in self.gates.items():
            if gate["status"] in {"PARTIAL", "UNKNOWN"}:
                self.assertTrue(str(gate["residual"]).strip(), name)

    def test_the_verdict_is_unresolved_rather_than_qualified(self):
        self.assertEqual(self.qualification["verdict"], "COUNTERPART_UNRESOLVED")
        partial = [n for n, g in self.gates.items() if g["status"] == "PARTIAL"]
        self.assertEqual(
            sorted(partial), ["C6_REQUEST_CONTRACT_RECONSTRUCTABILITY", "C9_RIGHTS_FEASIBILITY"]
        )

    def test_it_is_not_a_rejection_either(self):
        self.assertNotEqual(self.qualification["verdict"], "COUNTERPART_NOT_QUALIFIED")
        self.assertTrue(str(self.qualification["why_not_rejected"]).strip())
        self.assertEqual(self.qualification["tally"]["FAIL"], 0)

    def test_no_score_was_issued(self):
        self.assertIs(self.qualification["no_score_issued"], True)

    def test_qualification_is_construct_family_level(self):
        family = self.qualification["qualification_is_construct_family_level"]
        self.assertEqual(family["exact_predicate_chosen_by"], "Mission 1.74")
        self.assertIn("arbitrary", family["does_not_mean"])

    def test_both_residuals_are_closable_without_a_new_search(self):
        self.assertEqual(len(self.qualification["residuals"]), 2)
        for residual in self.qualification["residuals"]:
            self.assertIs(residual["requires_a_new_search"], False, residual["id"])
            self.assertTrue(str(residual["closable_by"]).strip(), residual["id"])


class TestAccountingAndMissingness(unittest.TestCase):
    """§11, §12, §13, §14."""

    def setUp(self):
        self.gates = {g["dimension"]: g for g in load(QUALIFICATION)["gates"]}

    def test_per_target_terminal_accounting_is_possible(self):
        self.assertEqual(self.gates["C3_TERMINAL_SUBMISSION_ACCOUNTING"]["status"], "PASS")

    def test_the_provider_names_apparatus_failure_itself(self):
        """`offline` and `failed` are the provider's words, not our inference."""
        why = self.gates["C3_TERMINAL_SUBMISSION_ACCOUNTING"]["why"]
        self.assertIn("offline", why)
        self.assertIn("failed", why)

    def test_a_provider_failure_is_not_a_target_no_response(self):
        why = self.gates["C3_TERMINAL_SUBMISSION_ACCOUNTING"]["why"]
        self.assertIn("apparatus missingness", why)


class TestTemporalSemantics(unittest.TestCase):
    """§20, §21, §22. The shift that dissolves the arc's recurring problem."""

    def setUp(self):
        self.gates = {g["dimension"]: g for g in load(QUALIFICATION)["gates"]}
        self.readiness = load(READINESS)

    def test_prospective_addressability_passes(self):
        self.assertEqual(self.gates["C5_PROSPECTIVE_TEMPORAL_ADDRESSABILITY"]["status"], "PASS")

    def test_no_historical_global_snapshot_was_required(self):
        why = self.gates["C5_PROSPECTIVE_TEMPORAL_ADDRESSABILITY"]["why"]
        self.assertIn("historical", why.lower())

    def test_observation_timestamps_are_required_by_the_provider_schema(self):
        why = self.gates["C5_PROSPECTIVE_TEMPORAL_ADDRESSABILITY"]["why"]
        self.assertIn("createdAt", why)
        self.assertIn("REQUIRED", why)

    def test_the_readiness_record_lists_this_as_resolved(self):
        resolved = " ".join(self.readiness["what_did_change"]["resolved_this_mission"])
        self.assertIn("prospective", resolved.lower())


class TestRequestContract(unittest.TestCase):
    """§23, §24, §25, §26, §27, §28."""

    def setUp(self):
        self.contract = load(CONTRACT)
        self.fields = {f["field"]: f for f in self.contract["fields"]}

    def test_the_matrix_covers_the_load_bearing_fields(self):
        for field in (
            "http_method",
            "url_scheme",
            "host_header",
            "user_agent",
            "accept_language",
            "cookies",
            "authentication",
            "redirects",
            "javascript_execution",
            "dns_behaviour",
            "ip_version",
            "vantage",
        ):
            self.assertIn(field, self.fields, field)

    def test_a_fixed_documented_contract_was_not_rejected_for_being_fixed(self):
        """§24. The User-Agent is provider-reserved and that is not disqualifying."""
        self.assertIs(
            self.contract["a_fixed_documented_contract_was_rejected_for_being_fixed"], False
        )
        self.assertEqual(self.fields["user_agent"]["classification"], "FIXED_AND_DOCUMENTED")

    def test_the_undocumented_field_is_redirects(self):
        unknown = [n for n, f in self.fields.items() if f["classification"] == "UNKNOWN"]
        self.assertIn("redirects", unknown)

    def test_the_contract_is_unresolved_because_of_it(self):
        self.assertEqual(self.contract["overall"], "REQUEST_CONTRACT_COMPATIBILITY_UNRESOLVED")

    def test_an_observed_implementation_is_not_a_documented_contract(self):
        gap = self.contract["the_single_load_bearing_gap"]
        self.assertIs(gap["implementation_is_a_documented_contract"], False)
        self.assertTrue(str(gap["why_that_distinction_is_not_pedantry"]).strip())

    def test_the_absence_was_measured_rather_than_assumed(self):
        gap = self.contract["the_single_load_bearing_gap"]
        self.assertIn("zero occurrences", gap["evidence"])
        self.assertIs(gap["result_schema_carries_a_hop_array"], False)

    def test_a_browser_page_load_was_not_equated_with_a_get(self):
        self.assertIs(self.contract["browser_page_load_equated_with_a_single_get"], False)


class TestResultMinimization(unittest.TestCase):
    """§15, §16, §17, §60."""

    def setUp(self):
        self.minimization = load(MINIMIZATION)

    def test_a_transport_only_path_is_available(self):
        self.assertEqual(
            self.minimization["transport_only_result_path"], "TRANSPORT_ONLY_RESULT_PATH_AVAILABLE"
        )

    def test_no_body_is_ingested_to_extract_a_status(self):
        self.assertIs(self.minimization["body_would_be_ingested_to_extract_a_status"], False)

    def test_the_mechanism_is_the_request_rather_than_a_provider_filter(self):
        self.assertIn("HEAD", self.minimization["how"])

    def test_status_and_headers_are_available_without_page_content(self):
        for field in ("statusCode", "headers", "rawHeaders"):
            self.assertIn(field, self.minimization["transport_fields_available"], field)

    def test_no_screenshot_dom_or_har_is_required(self):
        self.assertIs(self.minimization["screenshots_dom_or_har_required"], False)

    def test_governance_was_not_weakened_to_let_the_candidate_pass(self):
        adr = self.minimization["adr_039_compatibility"]
        self.assertIs(adr["governance_weakened_to_accommodate_the_candidate"], False)
        self.assertIs(adr["satisfied_under_head"], True)
        self.assertIs(adr["satisfied_under_get"], False)


class TestRights(unittest.TestCase):
    """§36, §37, §38, §39, §43."""

    def setUp(self):
        self.rights = load(RIGHTS)

    def test_no_account_trial_purchase_or_credential(self):
        for flag in ("account_created", "trial_started", "purchase_made", "credential_read"):
            self.assertIs(self.rights[flag], False, flag)

    def test_access_status_is_recorded_separately_from_rights(self):
        self.assertEqual(self.rights["access_status"], "PUBLIC_NO_ACCOUNT")
        self.assertNotEqual(self.rights["classification"], self.rights["access_status"])

    def test_a_free_api_is_not_commercial_permission(self):
        self.assertIs(self.rights["free_api_treated_as_commercial_permission"], False)

    def test_silence_is_not_permission(self):
        self.assertIs(self.rights["terms_silence_treated_as_permission"], False)

    def test_the_consumer_clause_was_not_read_as_a_blanket_prohibition(self):
        clause = self.rights["the_commercial_clause_read_in_context"]
        self.assertIs(clause["read_as_a_blanket_commercial_prohibition"], False)
        self.assertEqual(clause["the_heading_it_sits_under"], "If you are a consumer user:")
        self.assertTrue(str(clause["why_not"]).strip())

    def test_the_prohibited_use_section_does_not_prohibit_our_activity(self):
        prohibited = self.rights["prohibited_use_section"]
        for flag in (
            "prohibits_commercial_use",
            "prohibits_automated_or_programmatic_access",
            "prohibits_measuring_third_parties",
        ):
            self.assertIs(prohibited[flag], False, flag)

    def test_the_scope_sentence_is_neither_a_grant_nor_a_prohibition(self):
        scope = self.rights["the_scope_sentence_that_does_bite"]
        self.assertIs(scope["is_a_prohibition"], False)
        self.assertIs(scope["is_a_grant"], False)
        self.assertIn("your internet infrastructure", scope["sentence"])

    def test_the_classification_requires_a_dedicated_review(self):
        self.assertEqual(self.rights["classification"], "DEDICATED_GOVERNANCE_REVIEW_REQUIRED")
        self.assertIs(self.rights["clearly_blocks_the_intended_use"], False)
        self.assertIs(self.rights["clearly_permits_the_intended_use"], False)

    def test_provider_terms_do_not_replace_sros_governance(self):
        self.assertIs(self.rights["provider_terms_replace_sros_governance"], False)

    def test_no_legal_or_governance_approval_was_performed(self):
        self.assertIs(self.rights["final_legal_or_governance_approval_performed"], False)
        self.assertEqual(self.rights["external_legal_conclusion"], "NO_EXTERNAL_LEGAL_CONCLUSION")


class TestQ1AndDecision(unittest.TestCase):
    """§48, §49, §61, §68."""

    def setUp(self):
        self.readiness = load(READINESS)
        self.decision = load(DECISION)

    def test_q1_is_not_strategically_viable(self):
        conditions = self.readiness["conditions_for_strategic_viability"]
        self.assertEqual(conditions["verdict"], "NOT_YET_STRATEGICALLY_VIABLE")
        self.assertEqual(conditions["load_bearing_failure"], "one_external_counterpart_qualified")

    def test_two_of_the_four_conditions_are_met(self):
        conditions = self.readiness["conditions_for_strategic_viability"]
        self.assertIs(conditions["sros_governance_track_ready"], True)
        self.assertIs(conditions["independent_production_plausible"], True)
        self.assertIs(conditions["common_http_world_state_family_exists"], True)
        self.assertIs(conditions["one_external_counterpart_qualified"], False)

    def test_q1_status_did_not_change(self):
        self.assertEqual(
            self.readiness["q1_status_after"], "PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED"
        )
        self.assertIs(self.readiness["q1_status_changed_this_mission"], False)

    def test_no_quantity_class_was_selected(self):
        self.assertIsNone(self.decision["selected_quantity_class"])
        self.assertEqual(self.decision["selection_outcome"], "NO_SELECTION")
        self.assertIs(self.decision["selected_class_artifact_created"], False)
        selection_authorises_nothing(self, SELECTED_CLASS)

    def test_no_construct_and_no_counterpart_were_selected(self):
        self.assertIs(self.decision["selected_construct_created"], False)
        self.assertFalse(SELECTED_CONSTRUCT.exists())
        self.assertIs(self.decision["counterpart_selected"], False)

    def test_pair_analysis_stays_at_the_canonical_layer(self):
        self.assertEqual(self.readiness["pair_analysis"], "PAIR_ANALYSIS_NOT_READY")
        self.assertEqual(self.readiness["evidence_independence_groups"], 0)

    def test_the_primary_outcome_names_the_request_contract(self):
        self.assertEqual(
            self.decision["primary_outcome"], "COUNTERPART_FOUND_REQUEST_CONTRACT_UNRESOLVED"
        )

    def test_the_imperfect_fit_is_recorded_rather_than_smoothed(self):
        self.assertIs(self.decision["outcome_fits_imperfectly"], True)
        self.assertTrue(str(self.decision["why_it_fits_imperfectly"]).strip())

    def test_every_refused_outcome_carries_a_reason(self):
        refused = self.decision["outcomes_considered_and_refused"]
        self.assertGreaterEqual(len(refused), 6)
        for name, entry in refused.items():
            self.assertIs(entry["refused"], True, name)
            self.assertTrue(str(entry["why"]).strip(), name)

    def test_the_no_counterpart_outcome_was_refused_as_an_understatement(self):
        why = self.decision["outcomes_considered_and_refused"][
            "I_NO_COMPATIBLE_COUNTERPART_IDENTIFIED"
        ]["why"]
        self.assertIn("understate", why)


class TestNothingWasExecuted(unittest.TestCase):
    """§56, §57, §58, §60."""

    def setUp(self):
        self.accounting = load(DECISION)["mission_accounting"]

    def test_every_hard_zero_is_zero(self):
        for counter in (
            "COUNTERPART_API_EXECUTIONS",
            "TARGET_HTTP_REQUESTS",
            "SROS_FETCHER_RUNS",
            "EXTERNAL_MEASUREMENT_JOBS",
            "COMMON_CRAWL_QUERIES",
            "HTTP_ARCHIVE_BIGQUERY",
            "HAR_DOWNLOADS",
            "WARC_DOWNLOADS",
            "TARGET_VALUE_EXPOSURES",
            "ACCOUNTS_CREATED",
            "TRIALS",
            "PURCHASES",
            "CREDENTIAL_READS",
            "MAILBOX_SEARCHES",
            "ENQUIRIES_SENT",
            "SOURCES_REGISTERED",
            "THRESHOLDS_REGISTERED",
            "CLAIMS_CREATED",
            "EVIDENCE_CREATED",
            "INDEPENDENCE_GROUPS_CREATED",
            "RELIABILITY_VALUES_ASSIGNED",
            "SCORES",
            "MODEL_CALLS",
            "EMBEDDINGS",
            "MIGRATIONS",
            "CONSTRUCTS_SELECTED",
            "QUANTITY_CLASSES_SELECTED",
            "COUNTERPARTS_SELECTED",
        ):
            self.assertEqual(self.accounting[counter], 0, counter)

    def test_the_documentation_budget_holds(self):
        self.assertLessEqual(
            self.accounting["FIRST_PARTY_DOCUMENT_REQUESTS"],
            self.accounting["FIRST_PARTY_REQUEST_BUDGET"],
        )

    def test_governance_was_not_touched(self):
        parallel = load(DECISION)["parallel_state_untouched"]
        for flag in (
            "adr_039_weakened",
            "public_http_governance_altered",
            "source_collection_gate_weakened",
            "scanner_arc_reopened",
            "counterpart_provider_contacted",
            "onyphe_mailbox_searched",
            "netlas_enquiry_sent",
        ):
            self.assertIs(parallel[flag], False, flag)

    def test_no_canonical_mutation(self):
        self.assertEqual(load(DECISION)["canonical_mutation_boundary"]["mutations_this_mission"], 0)

    def test_problem_family_is_still_parked(self):
        self.assertEqual(load(BASELINE)["canonical_baseline"]["problem_family"], "PARKED")

    def test_no_record_froze_a_predicate_or_retrieved_values(self):
        for path in ALL_RECORDS:
            record = load(path)
            if "exact_predicate_frozen" in record:
                self.assertIs(record["exact_predicate_frozen"], False, path.name)
            if "target_values_retrieved" in record:
                self.assertEqual(record["target_values_retrieved"], 0, path.name)

    def test_the_next_mission_was_not_started(self):
        self.assertIs(load(DECISION)["recommended_next_mission"]["mission_1_74_not_started"], True)


class TestRegistry(unittest.TestCase):
    """§59."""

    def setUp(self):
        self.registry = load(DECISION)["requirement_registry"]

    def test_the_registry_is_unchanged_at_fifteen(self):
        self.assertEqual(self.registry["count_before"], 15)
        self.assertEqual(self.registry["count_after"], 15)

    def test_the_candidate_rule_was_reviewed_and_not_added(self):
        self.assertIs(self.registry["candidate_rule_reviewed"], True)
        self.assertIs(self.registry["candidate_rule_added"], False)
        self.assertTrue(str(self.registry["why_not_added"]).strip())

    def test_the_reason_is_that_the_counterpart_avoids_the_failure(self):
        """A candidate that avoids a failure mode is not an instance of it."""
        self.assertIn("AVOIDS", self.registry["why_not_added"].upper())

    def test_the_rule_is_not_in_the_registry(self):
        names = {
            r["name"] for r in load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]
        }
        self.assertNotIn(self.registry["mission_1_70_candidate_rule"], names)


class TestValidatorAndRenderer(unittest.TestCase):
    def setUp(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("_cq173", RENDERER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_the_live_records_validate(self):
        self.module.validate()

    def test_the_validator_knows_all_twelve_mandatory_dimensions(self):
        self.assertEqual(len(self.module.MANDATORY_DIMENSIONS), 12)

    def test_the_validator_refuses_the_disqualifying_producers(self):
        for producer in ("THIRD_PARTY_MEASUREMENT_UPSTREAM", "PURE_PROXY", "UNKNOWN"):
            self.assertIn(producer, self.module.DISQUALIFYING_PRODUCERS, producer)

    def test_the_validator_defines_every_primary_outcome(self):
        self.assertEqual(len(self.module.PRIMARY_OUTCOMES), 9)

    def test_the_census_exemption_is_named_rather_than_open(self):
        self.assertEqual(
            set(self.module.CENSUS_BLOCKS),
            {"canonical_baseline", "canonical_mutation_boundary", "mission_accounting"},
        )

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

    def test_both_pages_name_what_they_render(self):
        page = PAGE.read_text(encoding="utf-8")
        self.assertIn("COUNTERPART_FOUND_REQUEST_CONTRACT_UNRESOLVED", page)
        matrix = MATRIX_PAGE.read_text(encoding="utf-8")
        self.assertIn("Verdict: `COUNTERPART_UNRESOLVED`", matrix)
        self.assertIn("REQUEST_CONTRACT_COMPATIBILITY_UNRESOLVED", matrix)


if __name__ == "__main__":
    unittest.main()
