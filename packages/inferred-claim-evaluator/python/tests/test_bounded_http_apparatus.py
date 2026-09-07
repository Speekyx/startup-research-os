"""Mission 1.71. An apparatus we control, designed and not authorised.

Mission 1.70 closed the external pair because neither Common Crawl nor HTTP Archive
documents whether an attempted-and-failed URL appears in what it publishes. The obvious
repair is to run the fetcher ourselves, and the obvious repair has two traps in it.

The first is that running an apparatus supplies DIRECTABILITY and not INDEPENDENCE. We
would still need a second producer, and two of our own processes are one apparatus run
twice.

The second is quieter and is what most of this file is about: an apparatus we control
could reproduce the very defect that closed the external routes, in a system where
nobody else could be blamed for it. A fetcher that stored only responses would publish
exactly as little as Common Crawl does about what it tried. So the accounting invariant
is the deliverable — one terminal record per manifest item, always, and missingness as
first-class provenance rather than an absence.

And the governance answer is not the one the design wanted. The existing gate governs
collection from a REGISTERED source; a corpus of arbitrary public sites has no shape in
it, and routed through it every target is refused because nobody asked. That is the gate
working. Closing it is an ADR-level act, not something a design mission does in passing.

Nothing was fetched, crawled, queried, downloaded, registered or measured.
"""

from __future__ import annotations

import ast
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

BASELINE = DATA / "mission-1.71-baseline-v1.json"
GOVERNANCE = DATA / "bounded-http-governance-feasibility-v1.json"
APPARATUS = DATA / "sros-bounded-http-apparatus-contract-v1.json"
REQUEST = DATA / "bounded-http-request-contract-schema-v1.json"
CORPUS = DATA / "bounded-http-corpus-manifest-contract-v1.json"
RUN = DATA / "bounded-http-run-manifest-contract-v1.json"
TERMINALS = DATA / "bounded-http-terminal-outcome-taxonomy-v1.json"
MISSINGNESS = DATA / "bounded-http-missingness-contract-v1.json"
NETWORK = DATA / "bounded-http-network-safety-contract-v1.json"
MINIMIZATION = DATA / "bounded-http-data-minimization-review-v1.json"
COUNTERPART = DATA / "bounded-http-independent-counterpart-requirements-v1.json"
PILOT = DATA / "bounded-http-bounded-pilot-feasibility-v1.json"
CANDIDATE = DATA / "coverage-semantics-candidate-rule-review-v1.json"

APPARATUS_REGISTRY = DATA / "observation-addressable-apparatus-contract-v1.json"
DECISION_V2 = DATA / "quantity-class-selection-decision-v2.json"
FETCHER_1_70 = DATA / "sros-bounded-http-fetcher-feasibility-v1.json"
SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"

RENDERER = SCRIPTS / "render_bounded_http_apparatus.py"
PAGE = DATA / "mission-1.71-bounded-http-apparatus-v1.md"
ACCOUNTING_PAGE = DATA / "bounded-http-accounting-model-v1.md"

ALL_RECORDS = (
    BASELINE,
    GOVERNANCE,
    APPARATUS,
    REQUEST,
    CORPUS,
    RUN,
    TERMINALS,
    MISSINGNESS,
    NETWORK,
    MINIMIZATION,
    COUNTERPART,
    PILOT,
    CANDIDATE,
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

    def test_mission_1_70_is_merged_at_the_expected_commit(self):
        pre = self.baseline["repository_precondition"]
        self.assertIs(pre["mission_1_70_merged"], True)
        self.assertEqual(pre["pull_request"], 115)
        self.assertEqual(pre["observed_main"], pre["expected_main"])

    def test_the_baseline_records_no_drift(self):
        self.assertEqual(self.baseline["canonical_baseline"]["drift_from_mission_1_70"], "none")

    def test_the_migration_head_is_unchanged(self):
        self.assertEqual(
            self.baseline["canonical_baseline"]["migration_head"], "0035_refusal_provenance"
        )

    def test_the_registry_starts_at_fifteen(self):
        self.assertEqual(self.baseline["requirement_registry"]["count_before"], 15)
        registry = load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]
        self.assertEqual(len(registry), 15)

    def test_q1_state_is_preserved(self):
        self.assertEqual(
            self.baseline["parallel_state_untouched"]["q1_status"],
            "PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED",
        )

    def test_no_quantity_class_is_selected(self):
        self.assertIsNone(load(DECISION_V2)["selected_quantity_class"])
        selection_authorises_nothing(self, SELECTED_CLASS)

    def test_no_construct_is_selected(self):
        self.assertFalse(SELECTED_CONSTRUCT.exists())
        self.assertIs(self.baseline["scope"]["construct_selected"], False)

    def test_no_broad_discovery_and_no_reopened_analysis(self):
        scope = self.baseline["scope"]
        self.assertIs(scope["broad_apparatus_discovery_performed"], False)
        self.assertIs(scope["scanner_class_reopened"], False)
        self.assertIs(scope["common_crawl_http_archive_population_analysis_reopened"], False)


class TestGovernanceIsNotAuthorization(unittest.TestCase):
    """§3 and §50."""

    def setUp(self):
        self.governance = load(GOVERNANCE)

    def test_run_authorization_is_required(self):
        self.assertIs(self.governance["run_authorization_required"], True)

    def test_this_mission_authorised_nothing(self):
        self.assertIs(self.governance["authorised_by_this_mission"], False)
        self.assertIs(self.governance["this_is_not_a_run_authorization"], True)

    def test_this_is_not_legal_advice(self):
        self.assertIs(self.governance["this_is_not_legal_advice"], True)

    def test_the_verdict_claims_no_blanket_permission(self):
        for banned in ("LEGAL", "COMPLIANT", "PERMITTED_EVERYWHERE", "AUTHORIZED_TO_RUN"):
            self.assertNotIn(banned, self.governance["overall"])

    def test_every_rubric_dimension_is_evaluated_with_a_reason(self):
        rubric = {row["dimension"]: row for row in self.governance["rubric"]}
        for dimension in (
            "TARGET_SCOPE",
            "NETWORK_SAFETY",
            "REQUEST_SAFETY",
            "LOAD_SAFETY",
            "AUTHENTICATION_BOUNDARY",
            "ANTI_BOT_BOUNDARY",
            "DATA_MINIMIZATION",
            "SENSITIVE_CONTENT_HANDLING",
            "ROBOTS_POLICY",
            "TARGET_TERMS_HANDLING",
            "LOGGING",
            "RETENTION",
            "OPERATOR_AUTHORIZATION",
            "ABORTABILITY",
            "AUDITABILITY",
            "RUN_REPRODUCIBILITY",
        ):
            self.assertIn(dimension, rubric)
            self.assertTrue(str(rubric[dimension]["why"]).strip(), dimension)

    def test_no_numerical_score(self):
        self.assertIs(self.governance["numerical_score_issued"], False)

    def test_outstanding_policies_are_each_named_and_unsettled(self):
        outstanding = [
            r for r in self.governance["rubric"] if r["verdict"] == "REQUIRES_DEDICATED_POLICY"
        ]
        self.assertTrue(outstanding)
        named = self.governance["named_policy_decisions_required"]
        self.assertTrue(named)
        for decision in named:
            self.assertIs(decision["settled_here"], False, decision["id"])

    def test_the_architecture_is_not_blocked_by_an_existing_rule(self):
        """An absence of a shape is not a prohibition."""
        self.assertIs(self.governance["blocked_by_an_existing_rule"], False)
        self.assertTrue(str(self.governance["why_not_blocked"]).strip())

    def test_target_specific_review_is_required(self):
        self.assertIs(self.governance["target_specific_review_required"], True)

    def test_nothing_governance_bearing_was_mutated(self):
        for counter in ("sources_registered", "source_governance_mutated", "governance_approvals"):
            self.assertEqual(self.governance[counter], 0, counter)


class TestNetworkSafety(unittest.TestCase):
    """§5, §6, §7."""

    def setUp(self):
        self.network = load(NETWORK)
        self.blocked = {row["class"] for row in self.network["blocked_destination_classes"]}

    def test_a_public_looking_url_is_not_assumed_safe(self):
        self.assertIs(self.network["a_public_looking_url_is_assumed_safe"], False)
        self.assertIs(self.network["destination_check_required_before_every_connection"], True)

    def test_only_http_and_https_are_allowed(self):
        self.assertEqual(set(self.network["schemes"]["allowed"]), {"http", "https"})

    def test_the_dangerous_schemes_are_refused(self):
        for scheme in ("file", "ftp", "gopher", "data", "javascript"):
            self.assertIn(scheme, self.network["schemes"]["refused"], scheme)

    def test_private_destinations_are_refused(self):
        self.assertIn("IPV4_PRIVATE", self.blocked)
        self.assertIn("IPV6_UNIQUE_LOCAL", self.blocked)

    def test_loopback_is_refused(self):
        self.assertIn("IPV4_LOOPBACK", self.blocked)
        self.assertIn("IPV6_LOOPBACK", self.blocked)

    def test_link_local_is_refused(self):
        self.assertIn("IPV4_LINK_LOCAL", self.blocked)
        self.assertIn("IPV6_LINK_LOCAL", self.blocked)

    def test_cloud_metadata_is_refused(self):
        self.assertIn("CLOUD_METADATA_ENDPOINTS", self.blocked)

    def test_localhost_and_internal_names_are_refused(self):
        self.assertIn("LOCALHOST_NAMES", self.blocked)
        self.assertIn("INTERNAL_OR_SINGLE_LABEL_HOSTNAMES", self.blocked)

    def test_every_blocked_class_names_an_authority(self):
        for row in self.network["blocked_destination_classes"]:
            self.assertTrue(str(row["authority"]).strip(), row["class"])

    def test_no_recalled_numeric_ranges_were_written_in(self):
        """rule 4 refuses model recall and rule 7 refuses invented numbers."""
        self.assertIs(self.network["numeric_ranges"]["written_into_this_document"], False)

    def test_redirect_destinations_are_revalidated(self):
        self.assertIs(
            self.network["redirects"]["destination_revalidated_after_every_redirect"], True
        )
        self.assertIs(self.network["redirects"]["the_original_hostname_is_sufficient"], False)

    def test_dns_rebinding_is_addressed(self):
        dns = self.network["dns_safety"]
        self.assertEqual(dns["status"], "DNS_SAFETY_REQUIRED")
        self.assertIs(dns["rebinding_addressed"], True)
        self.assertIs(dns["connection_pinned_to_a_validated_resolved_address"], True)
        self.assertIs(dns["a_hostname_resolving_public_then_private_is_refused"], True)

    def test_one_public_address_does_not_validate_a_host(self):
        dns = self.network["dns_safety"]
        self.assertIs(dns["every_resolved_address_must_pass"], True)
        self.assertIs(dns["one_passing_address_is_enough"], False)


class TestBoundariesTheApparatusDoesNotHave(unittest.TestCase):
    """§4, §20, §21, §26."""

    def setUp(self):
        self.apparatus = load(APPARATUS)

    def test_authentication_is_absent_rather_than_disabled(self):
        request = {row["field"]: row for row in load(REQUEST)["fields"]}
        self.assertEqual(request["authentication_policy"]["value_fixed_by_this_contract"], "NONE")
        self.assertIs(self.apparatus["prohibited_capabilities"]["authentication_bypass"], False)

    def test_anti_bot_and_captcha_bypass_are_prohibited(self):
        prohibited = self.apparatus["prohibited_capabilities"]
        self.assertIs(prohibited["anti_bot_circumvention"], False)
        self.assertIs(prohibited["captcha_bypass"], False)
        self.assertIs(prohibited["rate_limit_circumvention"], False)

    def test_a_refusal_is_never_retried_with_a_different_identity(self):
        self.assertIs(
            self.apparatus["prohibited_capabilities"]["retry_with_varied_identity_after_refusal"],
            False,
        )

    def test_probing_and_scanning_are_prohibited(self):
        prohibited = self.apparatus["prohibited_capabilities"]
        for capability in (
            "vulnerability_probing",
            "directory_brute_forcing",
            "credential_testing",
            "hidden_endpoint_discovery",
            "parameter_fuzzing",
            "port_scanning",
            "non_http_service_probing",
        ):
            self.assertIs(prohibited[capability], False, capability)

    def test_target_expansion_is_prohibited(self):
        expansion = self.apparatus["crawl_expansion"]
        for flag in (
            "recursive_discovery",
            "links_in_responses_become_targets",
            "sitemap_expansion",
            "robots_discovered_expansion",
        ):
            self.assertIs(expansion[flag], False, flag)

    def test_redirects_do_not_expand_the_corpus(self):
        self.assertIs(self.apparatus["crawl_expansion"]["redirects_expand_the_corpus"], False)
        self.assertIs(
            self.apparatus["crawl_expansion"][
                "the_measured_population_is_exactly_the_frozen_manifest"
            ],
            True,
        )

    def test_javascript_is_not_silently_enabled(self):
        javascript = self.apparatus["javascript"]
        self.assertIs(javascript["enabled_by_default"], False)
        self.assertIs(javascript["required_by_the_default_architecture"], False)
        self.assertEqual(
            javascript["browser_rendered_mode"],
            "A_SEPARATE_APPARATUS_MODE_AND_A_SEPARATE_GOVERNANCE_REVIEW",
        )


class TestAccountingInvariant(unittest.TestCase):
    """§12, §13, §14, §15, §43. The deliverable."""

    def setUp(self):
        self.terminals = load(TERMINALS)
        self.missingness = load(MISSINGNESS)

    def test_one_target_one_terminal_status(self):
        invariant = self.terminals["invariant"]
        self.assertEqual(
            invariant["statement"], "corpus_manifest_count == terminal_target_records_count"
        )
        self.assertIs(invariant["exactly_one_terminal_per_target_per_run"], True)
        self.assertIs(invariant["a_target_may_disappear_silently"], False)

    def test_retries_do_not_create_population_members(self):
        self.assertIs(self.terminals["invariant"]["retries_create_extra_population_members"], False)

    def test_attempted_is_not_successful(self):
        stages = load(APPARATUS)["stages"]
        self.assertIs(stages["attempted_equals_successful"], False)
        self.assertEqual(
            stages["ordered"],
            ["SCHEDULED", "ATTEMPTED", "RESPONSE_RECEIVED", "PREDICATE_EVALUABLE"],
        )

    def test_response_absence_is_not_population_removal(self):
        self.assertIs(
            self.missingness["forbidden_readings"][
                "response_absence_means_target_absent_from_population"
            ],
            False,
        )

    def test_every_terminal_maps_to_exactly_one_declared_missingness_class(self):
        classes = {row["class"] for row in self.missingness["classes"]}
        seen = set()
        for row in self.terminals["terminals"]:
            self.assertNotIn(row["terminal"], seen)
            seen.add(row["terminal"])
            self.assertIn(row["missingness_class"], classes, row["terminal"])

    def test_no_missingness_class_is_unreachable(self):
        """A class no terminal reaches is a class that never fires."""
        classes = {row["class"] for row in self.missingness["classes"]}
        mapped = {row["missingness_class"] for row in self.terminals["terminals"]}
        self.assertEqual(classes - mapped, set())

    def test_an_apparatus_failure_is_not_the_targets_silence(self):
        by_terminal = {row["terminal"]: row for row in self.terminals["terminals"]}
        self.assertEqual(
            by_terminal["INTERNAL_FETCHER_ERROR"]["missingness_class"],
            "APPARATUS_FAILURE_NOT_A_WORLD_FACT",
        )
        attempted = {
            row["class"]: row["counts_as_attempted"] for row in self.missingness["classes"]
        }
        self.assertIs(attempted["APPARATUS_FAILURE_NOT_A_WORLD_FACT"], False)

    def test_predicate_evaluability_is_not_an_apparatus_stage(self):
        self.assertNotIn("PREDICATE_EVALUABLE", self.terminals["stages"])
        self.assertEqual(
            self.terminals["predicate_evaluable_is_not_an_apparatus_stage"]["determined_by"],
            "THE_CONSTRUCT, over the apparatus's records",
        )

    def test_the_denominator_counters_are_representable(self):
        denominator = self.missingness["denominator_integrity"]
        for counter in ("N_population", "A_attempted", "R_response_observed"):
            self.assertIs(denominator[counter]["computable_by_the_apparatus"], True, counter)

    def test_the_construct_owns_the_last_two_counters(self):
        denominator = self.missingness["denominator_integrity"]
        for counter in ("E_predicate_evaluable", "P_positive"):
            self.assertIs(denominator[counter]["computable_by_the_apparatus"], False, counter)
            self.assertEqual(denominator[counter]["computable_by"], "THE_CONSTRUCT")

    def test_this_mission_did_not_choose_the_denominator(self):
        self.assertEqual(
            self.missingness["denominator_integrity"]["which_classes_enter_the_denominator"],
            "NOT_CHOSEN_BY_THIS_MISSION",
        )

    def test_missingness_may_not_be_dropped_and_positives_are_not_the_only_store(self):
        forbidden = self.missingness["forbidden_readings"]
        self.assertIs(forbidden["missingness_may_be_dropped_from_the_record"], False)
        self.assertIs(forbidden["only_positive_observations_are_stored"], False)
        self.assertIs(forbidden["only_responses_are_stored"], False)


class TestCorpusContract(unittest.TestCase):
    """§8, §9, §10, §11."""

    def setUp(self):
        self.corpus = load(CORPUS)

    def test_no_corpus_exists(self):
        self.assertIs(self.corpus["corpus_created"], False)
        self.assertEqual(self.corpus["targets_in_any_corpus"], 0)

    def test_a_frozen_hash_is_required(self):
        self.assertEqual(self.corpus["hashing"]["algorithm"], "sha256")
        self.assertIs(self.corpus["hashing"]["required_before_a_run_may_reference_it"], True)

    def test_the_manifest_is_immutable_within_a_run(self):
        immutability = self.corpus["immutability"]
        self.assertIs(immutability["immutable_once_referenced_by_a_run"], True)
        self.assertIs(immutability["membership_may_change_after_execution_begins"], False)
        self.assertIs(
            immutability["the_old_manifest_may_be_mutated_under_the_same_run_identity"], False
        )

    def test_the_requested_url_is_preserved_verbatim(self):
        required = {row["field"] for row in self.corpus["fields"] if row["required"]}
        self.assertIn("requested_url_verbatim", required)

    def test_every_canonicalization_aspect_is_addressed(self):
        rules = self.corpus["canonical_url_rules"]
        for aspect in (
            "scheme",
            "host_case",
            "idn_punycode",
            "default_ports",
            "path_normalization",
            "trailing_slash",
            "fragment",
            "query_string",
            "duplicate_urls",
        ):
            self.assertTrue(str(rules[aspect]).strip(), aspect)

    def test_http_and_https_are_not_declared_one_entity(self):
        self.assertIs(
            self.corpus["canonical_url_rules"]["http_and_https_are_the_same_entity"], False
        )

    def test_the_query_string_policy_is_explicit_and_unsettled(self):
        query = self.corpus["query_string_policy"]
        self.assertEqual(query["status"], "QUERY_STRING_POLICY_REQUIRED")
        self.assertIs(query["settled_by_this_mission"], False)
        self.assertIs(query["silently_stripped"], False)


class TestRunContract(unittest.TestCase):
    """§16, §18, §31, §32, §33, §34, §41, §42."""

    def setUp(self):
        self.run = load(RUN)

    def test_no_run_was_executed(self):
        self.assertEqual(self.run["runs_executed"], 0)

    def test_all_three_hashes_are_mandatory(self):
        for digest in (
            "apparatus_contract_sha256",
            "corpus_manifest_sha256",
            "request_contract_sha256",
        ):
            self.assertIn(digest, self.run["three_hashes_are_mandatory"], digest)

    def test_software_provenance_is_required(self):
        required = {row["field"] for row in self.run["fields"] if row["required"]}
        for field in (
            "software_version",
            "git_commit",
            "dependency_lock_state",
            "runtime_version",
            "configuration_hash",
        ):
            self.assertIn(field, required, field)

    def test_containerization_is_not_required_for_provenance(self):
        self.assertIs(
            self.run["containerization"]["containerization_is_required_for_provenance"], False
        )

    def test_timestamp_semantics_are_explicit(self):
        time = self.run["time_semantics"]
        self.assertEqual(time["timezone"], "UTC")
        self.assertIs(time["unlabeled_local_timestamps_permitted"], False)
        for stamp in ("attempt_started_at", "attempt_finished_at"):
            self.assertIn(stamp, time["per_attempt_timestamps"])

    def test_the_construct_chooses_the_load_bearing_time(self):
        self.assertEqual(
            self.run["time_semantics"]["which_time_is_load_bearing"],
            "CHOSEN_BY_THE_CONSTRUCT_NOT_BY_THE_APPARATUS",
        )

    def test_retries_are_preserved_individually(self):
        retry = self.run["retry_semantics"]
        self.assertIs(retry["attempt_1_may_be_overwritten_by_attempt_2"], False)
        self.assertIs(retry["all_attempts_are_retained"], True)

    def test_the_construct_chooses_the_terminal_attempt(self):
        self.assertEqual(
            self.run["retry_semantics"]["which_attempt_defines_the_observation"],
            "CHOSEN_BY_THE_CONSTRUCT_NOT_BY_THE_APPARATUS",
        )

    def test_abort_preserves_the_accounting(self):
        abort = self.run["abortability"]
        self.assertIs(abort["immediate_safe_stop_supported"], True)
        self.assertIs(abort["no_new_attempts_after_abort"], True)
        self.assertIs(abort["targets_may_disappear_on_abort"], False)
        self.assertEqual(abort["remaining_items_become"], "RUN_ABORTED_BEFORE_ATTEMPT")
        self.assertIs(abort["the_accounting_invariant_survives_an_abort"], True)

    def test_resumability_is_explicit_and_creates_a_new_run(self):
        resume = self.run["resumability"]
        self.assertIs(resume["an_interrupted_run_resumes_automatically"], False)
        self.assertIs(resume["run_identity_is_preserved_across_a_resume"], False)
        self.assertTrue(str(resume["rule"]).strip())

    def test_vantage_identity_is_represented_without_leaking_detail(self):
        vantage = self.run["vantage"]
        self.assertIs(vantage["vantage_id_required"], True)
        self.assertIs(vantage["vantage_id_is_opaque"], True)
        self.assertIs(vantage["sensitive_local_network_detail_published"], False)
        self.assertIs(vantage["a_different_machine_or_network_is_a_distinct_vantage"], True)


class TestRequestContract(unittest.TestCase):
    """§19, §20, §22, §27, §30."""

    def setUp(self):
        self.request = load(REQUEST)
        self.fields = {row["field"]: row for row in self.request["fields"]}

    def test_every_field_is_required_before_a_run(self):
        self.assertIs(self.request["every_field_is_required_before_a_run"], True)
        for name, row in self.fields.items():
            self.assertIs(row["required_before_run"], True, name)

    def test_response_size_limits_are_required(self):
        for field in ("response_byte_cap", "header_byte_cap", "connect_timeout", "read_timeout"):
            self.assertIn(field, self.fields, field)
            self.assertIs(self.fields[field]["required_before_run"], True, field)

    def test_unbounded_is_not_representable(self):
        self.assertIs(self.request["unbounded_is_representable"], False)

    def test_get_versus_head_is_not_frozen_here(self):
        self.assertIs(self.request["default_minimality"]["get_versus_head_frozen_here"], False)
        self.assertIsNone(self.fields["http_method"]["value_fixed_by_this_contract"])

    def test_raw_headers_are_preserved(self):
        headers = self.request["header_handling"]
        self.assertIs(headers["raw_header_structure_preserved"], True)
        for flag in (
            "duplicate_headers_collapsed",
            "header_order_discarded",
            "raw_values_normalized_away",
            "response_hop_identity_discarded",
        ):
            self.assertIs(headers[flag], False, flag)

    def test_a_redirect_does_not_silently_change_the_entity(self):
        self.assertIs(
            self.request["redirects"]["a_redirect_may_silently_change_the_measured_entity"], False
        )

    def test_each_redirect_hop_is_recorded_with_its_safety_decision(self):
        for field in (
            "source_url",
            "status",
            "location_target",
            "resolved_destination_safety_decision",
            "timestamp",
        ):
            self.assertIn(field, self.request["redirects"]["per_hop_record_fields"], field)

    def test_the_construct_chooses_which_response_the_predicate_applies_to(self):
        self.assertEqual(
            self.request["redirects"]["which_response_the_predicate_applies_to"],
            "CHOSEN_BY_THE_CONSTRUCT_NOT_BY_THE_APPARATUS",
        )


class TestDataMinimization(unittest.TestCase):
    """§28, §29."""

    def setUp(self):
        self.minimization = load(MINIMIZATION)

    def test_body_capture_policy_is_required_before_a_run(self):
        self.assertEqual(
            self.minimization["permitted_retention"]["status"],
            "BODY_CAPTURE_POLICY_REQUIRED_BEFORE_RUN",
        )

    def test_full_body_retention_is_not_the_default_assumption(self):
        self.assertIs(
            self.minimization["permitted_retention"]["arbitrary_full_body_retention_assumed"], False
        )

    def test_capability_and_permitted_retention_are_separate(self):
        self.assertIn("transport_capture_capability", self.minimization)
        self.assertIn("permitted_retention", self.minimization)

    def test_sensitive_content_needs_hooks_before_any_body_is_stored(self):
        sensitive = self.minimization["sensitive_content"]
        self.assertIs(sensitive["a_public_page_may_return_personal_or_sensitive_data"], True)
        self.assertIs(sensitive["redaction_hooks_required_before_body_retention"], True)
        self.assertEqual(sensitive["content_retrieved_in_this_mission"], 0)

    def test_the_retention_regime_claim_carries_its_own_bound(self):
        """§50. A distinction, never a legal conclusion."""
        self.assertTrue(
            str(
                self.minimization["why_this_is_not_a_side_policy"]["and_the_bound_on_that_claim"]
            ).strip()
        )


class TestIndependenceIsNotGranted(unittest.TestCase):
    """§35, §36, §37, §38."""

    def setUp(self):
        self.apparatus = load(APPARATUS)
        self.counterpart = load(COUNTERPART)

    def test_self_operation_does_not_establish_independence(self):
        independence = self.apparatus["independence"]
        self.assertIs(independence["self_operation_establishes_independence"], False)
        self.assertIs(independence["independent_evidence_group_ready"], False)

    def test_the_classification_is_plausible_rather_than_ready(self):
        self.assertEqual(
            self.apparatus["independence"]["classification"], "INDEPENDENCE_ARCHITECTURE_PLAUSIBLE"
        )

    def test_two_local_processes_are_not_two_independence_groups(self):
        self.assertIs(
            self.apparatus["independence"]["two_local_processes_are_two_independence_groups"], False
        )

    def test_operator_identity_is_not_apparatus_identity(self):
        provenance = self.apparatus["operator_and_apparatus_are_separate_provenance"]
        self.assertIs(provenance["same_human_implies_same_apparatus"], False)
        self.assertIs(provenance["different_process_implies_independent_apparatus"], False)

    def test_no_independence_group_was_created(self):
        self.assertEqual(self.apparatus["independence"]["independence_groups_created"], 0)
        self.assertEqual(self.counterpart["independence_groups_created"], 0)

    def test_a_second_route_is_still_required(self):
        self.assertIs(
            self.apparatus["independence"]["second_independent_route_still_required"], True
        )
        self.assertIs(self.counterpart["second_independent_route_still_required"], True)

    def test_counterpart_requirements_exist_and_none_is_selected(self):
        self.assertTrue(self.counterpart["requirements"])
        self.assertEqual(
            len(self.counterpart["requirements"]), self.counterpart["requirement_count"]
        )
        self.assertIs(self.counterpart["counterpart_selected"], False)
        self.assertIs(self.counterpart["counterpart_ranked"], False)
        self.assertEqual(self.counterpart["counterpart_candidates_evaluated"], 0)

    def test_common_crawl_and_http_archive_states_are_not_rewritten(self):
        held = self.counterpart["held_state_not_reopened"]
        for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
            self.assertIs(held[route]["independently_produces_http_observations"], True)
            self.assertEqual(
                held[route]["population_and_attempt_semantics"],
                "INSUFFICIENT_UNDER_CURRENT_EVIDENCE",
            )
            self.assertIs(held[route]["state_changed_this_mission"], False)

    def test_the_fetcher_does_not_repair_external_records(self):
        self.assertIs(
            self.counterpart["held_state_not_reopened"][
                "the_operator_fetcher_repairs_their_records_retroactively"
            ],
            False,
        )

    def test_the_observation_is_not_claimed_reproducible(self):
        self.assertIs(self.apparatus["reproducibility"]["the_observation_is_reproducible"], False)
        self.assertIs(self.apparatus["reproducibility"]["the_run_is_reconstructible"], True)


class TestBoundedPilot(unittest.TestCase):
    """§25, §27, §45, §46."""

    def setUp(self):
        self.pilot = load(PILOT)

    def test_every_dimension_must_be_bounded(self):
        dimensions = {
            row["dimension"]: row for row in self.pilot["dimensions_that_must_be_bounded"]
        }
        for dimension in (
            "number_of_targets",
            "requests_per_target",
            "redirect_count",
            "retries",
            "global_concurrency",
            "per_host_concurrency",
            "per_origin_rate",
            "total_run_duration",
            "maximum_bytes",
        ):
            self.assertIn(dimension, dimensions, dimension)
            self.assertIs(dimensions[dimension]["bounded_required"], True, dimension)

    def test_unbounded_is_permitted_nowhere(self):
        self.assertIs(self.pilot["unbounded_permitted_on_any_dimension"], False)

    def test_no_pilot_size_was_selected(self):
        self.assertIs(self.pilot["pilot_size_selected"], False)
        self.assertTrue(str(self.pilot["why_no_size_was_selected"]).strip())
        for row in self.pilot["dimensions_that_must_be_bounded"]:
            self.assertIsNone(row["value_chosen"], row["dimension"])

    def test_local_first_waives_nothing(self):
        local = self.pilot["local_first_constraint"]
        self.assertIs(local["distributed_infrastructure_required"], False)
        for waiver in (
            "local_first_waives_rate_limits",
            "local_first_waives_target_policies",
            "local_first_waives_security_controls",
            "local_first_waives_commercial_purpose_rights",
        ):
            self.assertIs(local[waiver], False, waiver)


class TestCandidateRegistryRule(unittest.TestCase):
    """§49. Designing around a failure mode is not observing a second instance of it."""

    def setUp(self):
        self.candidate = load(CANDIDATE)

    def test_the_registry_is_unchanged_at_fifteen(self):
        self.assertEqual(self.candidate["registry_count_before"], 15)
        self.assertEqual(self.candidate["registry_count_after"], 15)
        self.assertEqual(len(load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]), 15)

    def test_the_rule_was_not_added(self):
        self.assertEqual(self.candidate["decision"], "NOT_ADDED")
        names = {
            r["name"] for r in load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]
        }
        self.assertNotIn(self.candidate["candidate"]["name"], names)

    def test_it_was_not_added_because_it_is_useful(self):
        self.assertIs(self.candidate["added_because_it_is_useful"], False)
        self.assertTrue(str(self.candidate["why_usefulness_is_not_the_standard"]).strip())

    def test_our_own_design_does_not_count_as_an_instance(self):
        for instance in self.candidate["instances_considered"]:
            if "SROS" in instance["instance"]:
                self.assertIs(instance["counts_as_a_distinct_instance"], False)
                self.assertTrue(str(instance["why_it_does_not_count"]).strip())

    def test_only_one_distinct_instance_was_found(self):
        counted = [
            i for i in self.candidate["instances_considered"] if i["counts_as_a_distinct_instance"]
        ]
        self.assertEqual(len(counted), 1)
        self.assertEqual(self.candidate["distinct_instances_found"], 1)
        self.assertIs(self.candidate["second_instance_in_a_different_shape"], False)

    def test_registry_growth_was_not_forced(self):
        self.assertIs(self.candidate["registry_growth_forced"], False)


class TestNothingWasExecuted(unittest.TestCase):
    """§52, §53, §54."""

    def test_no_crawler_was_implemented(self):
        self.assertIs(load(APPARATUS)["implemented"], False)
        self.assertIs(load(NETWORK)["implemented"], False)

    def test_no_http_target_request_was_made(self):
        self.assertEqual(load(NETWORK)["requests_made"], 0)
        self.assertEqual(load(RUN)["runs_executed"], 0)

    def test_no_external_documentation_request_was_spent(self):
        budget = load(BASELINE)["documentation_budget"]
        self.assertEqual(budget["used"], 0)
        self.assertTrue(str(budget["why_zero"]).strip())

    def test_no_target_site_terms_were_inspected(self):
        budget = load(BASELINE)["documentation_budget"]
        self.assertEqual(budget["target_site_terms_inspected"], 0)
        self.assertEqual(budget["targets_browsed"], 0)

    def test_no_record_froze_a_predicate_or_retrieved_values(self):
        for path in ALL_RECORDS:
            record = load(path)
            if "exact_predicate_frozen" in record:
                self.assertIs(record["exact_predicate_frozen"], False, path.name)
            if "target_values_retrieved" in record:
                self.assertEqual(record["target_values_retrieved"], 0, path.name)

    def test_onyphe_and_netlas_are_unchanged(self):
        parallel = load(BASELINE)["parallel_state_untouched"]
        self.assertEqual(parallel["onyphe_response_status"], "NOT_CHECKED_AFTER_DISPATCH")
        self.assertEqual(parallel["netlas_contact"], "STILL_PENDING")

    def test_the_scanner_arc_is_still_parked(self):
        self.assertEqual(
            load(BASELINE)["parallel_state_untouched"]["scanner_arc_status"],
            "PARKED_BUT_REOPENABLE_ON_NEW_FIRST_PARTY_EVIDENCE",
        )

    def test_problem_family_is_still_parked(self):
        self.assertEqual(load(BASELINE)["canonical_baseline"]["problem_family"], "PARKED")

    def test_no_scores_and_no_calibration(self):
        baseline = load(BASELINE)["canonical_baseline"]
        self.assertEqual(baseline["scores_table"], "ABSENT")
        self.assertEqual(baseline["reference_profile"], "UNCALIBRATED")

    def test_the_canonical_counters_are_the_mission_1_70_ones(self):
        baseline = load(BASELINE)["canonical_baseline"]
        expected = {
            "raw_records": 325,
            "normalized_records": 325,
            "signals": 33,
            "claims": 44,
            "claim_revisions": 45,
            "evidence": 58,
            "inferred_claims": 1,
            "threshold_registrations": 1,
            "claim_derivations": 1,
            "proposition_evaluation_refusals": 0,
            "evidence_supports": 57,
            "evidence_contradicts": 1,
            "reliability_assessments": 4,
            "evidence_independence_groups": 0,
            "opportunities": 1,
            "registered_sources": 29,
            "embeddings": 0,
        }
        for key, value in expected.items():
            self.assertEqual(baseline[key], value, key)

    def test_mission_1_70_records_were_not_edited(self):
        decision = load(DECISION_V2)
        self.assertIsNone(decision["selected_quantity_class"])
        self.assertEqual(
            decision["primary_outcome"], "FIXED_CORPUS_WEB_REQUIRES_OPERATOR_CONTROLLED_ROUTE"
        )
        fetcher = load(FETCHER_1_70)
        self.assertIs(fetcher["implemented"], False)
        self.assertIs(fetcher["crawled"], False)


class TestValidatorAndRenderer(unittest.TestCase):
    def setUp(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("_bha171", RENDERER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_the_live_records_validate(self):
        self.module.validate()

    def test_the_validator_requires_every_dangerous_destination_class(self):
        for required in (
            "IPV4_LOOPBACK",
            "IPV4_PRIVATE",
            "IPV4_LINK_LOCAL",
            "CLOUD_METADATA_ENDPOINTS",
            "IPV6_UNIQUE_LOCAL",
            "LOCALHOST_NAMES",
        ):
            self.assertIn(required, self.module.REQUIRED_BLOCKED, required)

    def test_the_validator_requires_every_prohibited_capability(self):
        for capability in (
            "authentication_bypass",
            "captcha_bypass",
            "anti_bot_circumvention",
            "vulnerability_probing",
            "port_scanning",
        ):
            self.assertIn(capability, self.module.REQUIRED_PROHIBITED, capability)

    def test_the_validator_requires_every_bound(self):
        self.assertEqual(len(self.module.REQUIRED_BOUNDS), 9)

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

    def test_no_executable_fetcher_was_created(self):
        """§55. A design mission produces no crawler."""
        for candidate in ("bounded_http_fetcher.py", "http_fetcher.py", "sros_fetcher.py"):
            self.assertFalse((SCRIPTS / candidate).exists(), candidate)

    def test_both_pages_name_what_they_render(self):
        page = PAGE.read_text(encoding="utf-8")
        self.assertIn("GOVERNANCE_NOT_YET_FEASIBLE_IN_PRINCIPLE_NAMED_DECISIONS_REQUIRED", page)
        self.assertIn("Authorised by this mission: False", page)
        accounting = ACCOUNTING_PAGE.read_text(encoding="utf-8")
        self.assertIn("corpus_manifest_count == terminal_target_records_count", accounting)


if __name__ == "__main__":
    unittest.main()
