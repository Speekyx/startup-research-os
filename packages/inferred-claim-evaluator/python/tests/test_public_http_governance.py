"""Mission 1.72. Which gate applies is a function of what is retained.

Mission 1.71 could not clear the operator apparatus because the acquisition gate governs
collection from a REGISTERED source, and a corpus of arbitrary public sites has no shape
in it. Routed through that gate every target is refused, not because a publisher objected
but because nobody asked, and restricting the corpus to reviewed targets collapses it to
the 29 registered sources.

This mission decides that bounded public HTTP observation is a distinct governed
activity. The decision is only defensible because of a condition that ties it to GOV-3:
the track is available while the retained material is transport-level, and the moment a
response body is retained the retained thing IS the publisher's material and source
collection governs instead.

So most of this file is about the boundary holding under pressure:

  - the caller does not choose its track; the declared retention profile does;
  - the boundary is structural, because the observation track's own contract has no
    persistable body class to configure;
  - public visibility is still not permission, and a track pass is still not a legal
    conclusion;
  - robots is a state machine quoted from RFC 9309 where it follows the standard and
    marked as ours where it is stricter;
  - an excluded target keeps its place in the population;
  - and every load number says out loud that it is a project policy default rather than
    something anybody discovered.

Nothing was fetched, crawled, registered or measured.
"""

from __future__ import annotations

import ast
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"
ADR_DIR = REPO_ROOT / "docs" / "architecture" / "adr"

BASELINE = DATA / "mission-1.72-baseline-v1.json"
DECISION = DATA / "public-http-observation-governance-decision-v1.json"
PRECEDENCE = DATA / "governance-track-precedence-v1.json"
POLICY = DATA / "public-http-observation-policy-v1.json"
ROBOTS = DATA / "public-http-robots-policy-v1.json"
MINIMIZATION = DATA / "public-http-data-minimization-policy-v1.json"
RETENTION = DATA / "public-http-retention-policy-v1.json"
TARGET = DATA / "public-http-target-policy-v1.json"
EXCLUSIONS = DATA / "public-http-target-exclusion-registry-contract-v1.json"
LOAD = DATA / "bounded-http-load-profile-v1.json"
LINKAGE = DATA / "bounded-http-apparatus-policy-linkage-v1.json"

ADR = ADR_DIR / "ADR-039-public-http-observation-governance-track.md"
APPARATUS_REGISTRY = DATA / "observation-addressable-apparatus-contract-v1.json"
APPARATUS_CONTRACT = DATA / "sros-bounded-http-apparatus-contract-v1.json"
COUNTERPART = DATA / "bounded-http-independent-counterpart-requirements-v1.json"
SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"

RENDERER = SCRIPTS / "render_public_http_governance.py"
PAGE = DATA / "mission-1.72-public-http-governance-v1.md"
LOAD_PAGE = DATA / "bounded-http-load-profile-v1.md"

ALL_RECORDS = (
    BASELINE,
    DECISION,
    PRECEDENCE,
    POLICY,
    ROBOTS,
    MINIMIZATION,
    RETENTION,
    TARGET,
    EXCLUSIONS,
    LOAD,
    LINKAGE,
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

    def test_mission_1_71_merged_at_the_expected_commit(self):
        pre = self.baseline["repository_precondition"]
        self.assertIs(pre["mission_1_71_merged"], True)
        self.assertEqual(pre["pull_request"], 116)
        self.assertEqual(pre["observed_main"], pre["expected_main"])

    def test_the_baseline_is_unchanged(self):
        baseline = self.baseline["canonical_baseline"]
        self.assertEqual(baseline["drift_from_mission_1_71"], "none")
        self.assertEqual(baseline["migration_head"], "0035_refusal_provenance")
        for key, value in {
            "raw_records": 325,
            "normalized_records": 325,
            "signals": 33,
            "claims": 44,
            "claim_revisions": 45,
            "evidence": 58,
            "inferred_claims": 1,
            "reliability_assessments": 4,
            "evidence_independence_groups": 0,
            "registered_sources": 29,
            "embeddings": 0,
        }.items():
            self.assertEqual(baseline[key], value, key)

    def test_the_registry_is_fifteen(self):
        self.assertEqual(self.baseline["requirement_registry"]["count_before"], 15)
        self.assertEqual(len(load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]), 15)

    def test_gov_1_is_resolved_before_the_others_are_activated(self):
        """GOV-1 decides whether GOV-2..5 are settings or blockers, so it is first."""
        self.assertEqual(
            self.baseline["scope"]["resolves"], ["GOV-1", "GOV-2", "GOV-3", "GOV-4", "GOV-5"]
        )
        linkage = load(LINKAGE)["resolved_rows"]
        self.assertEqual(linkage[0]["gov"], "GOV-1")

    def test_no_crawler_and_no_corpus(self):
        self.assertIs(
            self.baseline["repository_precondition"]["crawler_implementation_exists"], False
        )
        self.assertIs(load(TARGET)["corpus_exists"], False)

    def test_no_counterpart_class_or_construct(self):
        scope = self.baseline["scope"]
        self.assertIs(scope["counterpart_discovery_performed"], False)
        self.assertIs(scope["quantity_class_discovery_performed"], False)
        self.assertIs(scope["construct_selected"], False)
        selection_authorises_nothing(self, SELECTED_CLASS)
        self.assertFalse(SELECTED_CONSTRUCT.exists())


class TestGov1(unittest.TestCase):
    """§1 to §8, §49."""

    def setUp(self):
        self.decision = load(DECISION)

    def test_the_adr_exists_and_is_named(self):
        self.assertEqual(self.decision["adr"], "ADR-039")
        self.assertTrue(ADR.exists())

    def test_all_four_models_were_evaluated_with_reasons(self):
        models = self.decision["models_evaluated"]
        for model in (
            "MODEL_A_SOURCE_COLLECTION_ONLY",
            "MODEL_B_PUBLIC_HTTP_OBSERVATION_TRACK",
            "MODEL_C_PER_TARGET_OPERATOR_REVIEW",
            "MODEL_D_NO_GOVERNED_ROUTE",
        ):
            self.assertIn(model, models)
            self.assertTrue(str(models[model]["why"]).strip(), model)

    def test_exactly_one_model_was_adopted(self):
        adopted = [m for m, v in self.decision["models_evaluated"].items() if v["adopted"]]
        self.assertEqual(len(adopted), 1)
        self.assertEqual(adopted[0], "MODEL_B_PUBLIC_HTTP_OBSERVATION_TRACK")

    def test_the_adoption_is_conditional_on_gov_3(self):
        """The finding that makes this defensible rather than convenient."""
        self.assertIs(self.decision["adopted_conditionally"], True)
        condition = self.decision["the_condition"]
        self.assertTrue(str(condition["statement"]).strip())
        self.assertIs(condition["satisfied_by_gov_3"], True)
        self.assertEqual(
            condition["gov_3_decision_that_satisfies_it"], "BODY_PERSISTENCE_DEFAULT_DISABLED"
        )

    def test_the_distinguishing_test_actually_distinguishes(self):
        test = self.decision["distinguishing_test"]
        self.assertEqual(test["answer_1"], "no")
        self.assertEqual(test["answer_2"], "yes")
        self.assertIs(test["and_it_holds_only_under_the_condition_above"], True)

    def test_the_obvious_objection_was_answered(self):
        self.assertTrue(
            str(self.decision["distinguishing_test"]["objection_considered"]["response"]).strip()
        )

    def test_source_collection_governance_is_not_weakened(self):
        self.assertIs(self.decision["source_collection_governance_weakened"], False)
        self.assertIs(self.decision["no_target_becomes_a_source_automatically"], True)
        self.assertEqual(
            self.decision["registered_sources_before"], self.decision["registered_sources_after"]
        )

    def test_no_legal_conclusion_was_made(self):
        self.assertIs(self.decision["legal_conclusion_made"], False)
        for banned in (
            "LEGAL",
            "COMPLIANT_WITH_ALL_TARGET_TERMS",
            "ROBOTS_EQUALS_PERMISSION",
            "PUBLIC_MEANS_ALLOWED",
        ):
            self.assertNotIn(banned, self.decision["vocabulary_used"], banned)

    def test_run_authorization_stays_separate(self):
        self.assertIs(self.decision["run_authorization_required"], True)
        self.assertIs(self.decision["authorised_by_this_mission"], False)


class TestTrackBoundary(unittest.TestCase):
    """§4, §7, §48, §49. The boundary has to hold when somebody leans on it."""

    def setUp(self):
        self.precedence = load(PRECEDENCE)
        self.minimization = load(MINIMIZATION)

    def test_the_caller_does_not_choose_its_track(self):
        rule = self.precedence["precedence_rule"]
        self.assertIs(rule["caller_may_choose_its_track"], False)
        self.assertEqual(rule["when_both_could_apply"], "SOURCE_COLLECTION wins")

    def test_the_track_is_a_function_of_the_declared_retention_profile(self):
        self.assertIn("RETENTION PROFILE", self.precedence["precedence_rule"]["rule"].upper())

    def test_the_observation_track_cannot_ingest_arbitrary_content(self):
        prohibited = self.precedence["the_observation_track_may_not_be_used_for"]
        for use in (
            "article ingestion",
            "document corpus acquisition",
            "page-content research",
            "web scraping for ideation",
            "news ingestion",
            "forum ingestion",
            "dataset ingestion",
            "commercial content harvesting",
            "general-purpose site crawling",
        ):
            self.assertIn(use, prohibited, use)

    def test_the_boundary_is_structural_rather_than_prose(self):
        """The claim has to be true of the contract, not merely asserted beside it."""
        self.assertIs(self.precedence["enforced_structurally_rather_than_by_prose"], True)
        persisted = {
            row["class"]
            for row in self.minimization["data_classes"]
            if row["persist_allowed"] is True
        }
        self.assertNotIn("RESPONSE_BODY", persisted)

    def test_the_source_collection_track_was_not_changed(self):
        self.assertIs(
            self.precedence["tracks"]["SOURCE_COLLECTION"]["unchanged_by_this_mission"], True
        )

    def test_no_target_is_auto_registered_as_a_source(self):
        forbidden = self.precedence["forbidden_repository_changes"]
        for flag in (
            "making_arbitrary_public_sites_eligible_sources",
            "making_unknown_source_rights_pass",
            "relabelling_measurement_targets_as_registered_sources",
        ):
            self.assertIs(forbidden[flag], False, flag)

    def test_a_caller_can_determine_the_gate_deterministically(self):
        self.assertIs(self.precedence["a_caller_can_determine_the_gate_deterministically"], True)


class TestObservationPolicy(unittest.TestCase):
    """§5, §26, §41, §42, §43."""

    def setUp(self):
        self.policy = load(POLICY)

    def test_no_eligibility_requirement_defaults_to_approval(self):
        for requirement in self.policy["eligibility_requirements"]:
            self.assertIs(
                requirement["defaults_to_approval_when_unknown"], False, requirement["requirement"]
            )

    def test_a_purpose_is_required(self):
        purpose = self.policy["measurement_purpose"]
        self.assertIs(purpose["required"], True)
        self.assertIs(purpose["no_reason_supplied_is_acceptable"], False)
        self.assertIs(purpose["general_exploration_is_authorization"], False)

    def test_public_visibility_is_still_not_permission(self):
        visibility = self.policy["public_visibility_and_permission"]
        self.assertIs(visibility["public_implies_permission"], False)
        self.assertIn("TRACK_REQUIREMENTS_PASS", visibility["the_rule_under_this_track"])

    def test_a_track_pass_is_not_a_legal_conclusion(self):
        visibility = self.policy["public_visibility_and_permission"]
        self.assertIs(visibility["this_is_a_claim_about_external_legal_rights"], False)
        self.assertIs(visibility["target_specific_review_may_still_apply"], True)
        self.assertEqual(self.policy["external_legal_conclusion"], "NO_EXTERNAL_LEGAL_CONCLUSION")

    def test_run_authorization_is_required_and_ungranted(self):
        authorization = self.policy["run_authorization"]
        self.assertIs(authorization["required"], True)
        self.assertIs(authorization["granted_by_this_mission"], False)
        self.assertIs(authorization["governance_track_membership_is_operator_authorization"], False)

    def test_no_construct_detail_was_chosen(self):
        boundary = self.policy["future_construct_boundary"]
        for key in (
            "header_selected",
            "status_code_selected",
            "html_token_selected",
            "technology_selected",
        ):
            self.assertIsNone(boundary[key], key)
        self.assertEqual(boundary["what_fact_will_be_measured"], "NOT_CHOSEN_BY_THIS_MISSION")


class TestRobots(unittest.TestCase):
    """§9 to §15."""

    def setUp(self):
        self.robots = load(ROBOTS)
        self.machine = {row["condition"]: row for row in self.robots["state_machine"]}

    def test_a_robots_policy_was_selected(self):
        selected = [k for k, v in self.robots["options_evaluated"].items() if v["selected"]]
        self.assertEqual(len(selected), 1)
        self.assertEqual(self.robots["decision"], "R1_RESPECT_DISALLOW")

    def test_ignoring_robots_was_refused_on_an_existing_project_rule(self):
        why = self.robots["options_evaluated"]["R0_IGNORE_ROBOTS"]["why"]
        self.assertIn("rule 6", why)

    def test_robots_is_not_a_permission_system(self):
        self.assertIs(self.robots["robots_is_a_legal_permission_system"], False)

    def test_the_failure_semantics_are_deterministic(self):
        for condition in (
            "ROBOTS_404_OR_410",
            "ROBOTS_401_OR_403",
            "ROBOTS_5XX",
            "ROBOTS_NETWORK_FAILURE",
            "ROBOTS_TIMEOUT",
        ):
            self.assertIn(condition, self.machine, condition)
            self.assertTrue(str(self.machine[condition]["outcome"]).strip(), condition)
        self.assertIs(self.robots["a_target_may_switch_behaviour_silently"], False)

    def test_404_proceeds_and_5xx_excludes(self):
        """The standard's own split, and the reason 404 does not exclude."""
        self.assertEqual(self.machine["ROBOTS_404_OR_410"]["outcome"], "TARGET_PROCEEDS")
        self.assertEqual(self.machine["ROBOTS_5XX"]["outcome"], "TARGET_EXCLUDED")
        self.assertIs(self.machine["ROBOTS_404_OR_410"]["stricter_than_the_rfc"], False)
        self.assertIs(self.machine["ROBOTS_5XX"]["stricter_than_the_rfc"], False)

    def test_401_and_403_exclude_and_say_that_is_ours(self):
        row = self.machine["ROBOTS_401_OR_403"]
        self.assertEqual(row["outcome"], "TARGET_EXCLUDED")
        self.assertIs(row["stricter_than_the_rfc"], True)
        self.assertTrue(str(row["why"]).strip())

    def test_a_timeout_is_treated_as_unreachable_and_marked_as_our_choice(self):
        row = self.machine["ROBOTS_TIMEOUT"]
        self.assertEqual(row["outcome"], "TARGET_EXCLUDED")
        self.assertIs(row["stricter_than_the_rfc"], True)

    def test_every_row_states_the_standard_position(self):
        for condition, row in self.machine.items():
            self.assertTrue(str(row["rfc_9309_position"]).strip(), condition)

    def test_the_standard_was_read_rather_than_recalled(self):
        provenance = self.robots["rfc_provenance"]
        self.assertIs(provenance["quoted_rather_than_recalled"], True)
        self.assertIs(provenance["retrieved_this_mission"], True)
        self.assertIn("rfc9309", provenance["retrieved_from"])

    def test_robots_retrieval_is_a_governed_stage(self):
        preflight = self.robots["preflight"]
        self.assertIs(preflight["robots_fetch_required"], True)
        self.assertIs(preflight["consumes_request_budget"], True)
        self.assertIs(preflight["counted_toward_per_origin_budget"], True)

    def test_a_robots_excluded_target_stays_in_the_population(self):
        self.assertIs(self.robots["preflight"]["an_excluded_target_leaves_the_population"], False)

    def test_the_user_agent_binds_to_the_robots_evaluation(self):
        agent = self.robots["user_agent_binding"]
        self.assertIs(agent["apparatus_has_a_named_product_token"], True)
        self.assertIs(agent["the_token_is_the_same_string_sent_in_user_agent"], True)
        self.assertIs(agent["evaluating_the_wildcard_group_when_a_specific_group_exists"], False)

    def test_no_robots_request_was_made(self):
        self.assertEqual(self.robots["robots_target_requests"], 0)
        self.assertEqual(self.robots["requests_made_this_mission"], 0)


class TestDataMinimization(unittest.TestCase):
    """§16 to §22."""

    def setUp(self):
        self.minimization = load(MINIMIZATION)
        self.headers = self.minimization["headers"]

    def test_a_minimization_option_was_selected(self):
        selected = [k for k, v in self.minimization["options_evaluated"].items() if v["selected"]]
        self.assertEqual(len(selected), 1)
        self.assertEqual(self.minimization["decision"], "D2_ALLOWLISTED_HEADERS_AND_STATUS")

    def test_body_persistence_is_disabled_by_default(self):
        body = self.minimization["body"]
        self.assertEqual(body["BODY_PERSISTENCE_DEFAULT"], "DISABLED")
        self.assertIs(body["body_bytes_may_be_persisted_in_the_initial_profile"], False)

    def test_capability_does_not_decide_policy(self):
        self.assertIs(self.minimization["body"]["available_because_the_client_supports_it"], False)

    def test_not_persisting_is_not_the_same_as_not_receiving(self):
        body = self.minimization["body"]
        self.assertIs(body["not_persisting_is_the_same_as_not_receiving"], False)
        self.assertIs(body["network_read_still_bounded"], True)

    def test_headers_are_an_allowlist_rather_than_everything(self):
        self.assertIs(self.headers["all_response_headers_persisted"], False)
        self.assertEqual(self.headers["mechanism"], "HEADER_ALLOWLIST")

    def test_the_secret_bearing_headers_are_always_excluded(self):
        excluded = {h.lower() for h in self.headers["always_excluded"]}
        for header in ("set-cookie", "www-authenticate", "proxy-authenticate", "authorization"):
            self.assertIn(header, excluded, header)

    def test_a_run_cannot_widen_the_allowlist_into_the_excluded_set(self):
        """An allowlist a run could widen into secrets is not an allowlist."""
        self.assertIs(self.headers["a_run_may_extend_the_allowlist"], True)
        self.assertIs(self.headers["a_run_may_extend_it_into_the_always_excluded_set"], False)

    def test_the_default_allowlist_and_the_excluded_set_are_disjoint(self):
        excluded = {h.lower() for h in self.headers["always_excluded"]}
        for header in self.headers["default_persisted_allowlist"]:
            self.assertNotIn(header.lower(), excluded, header)

    def test_no_perfect_secret_detection_is_claimed(self):
        self.assertIs(self.headers["perfect_secret_detection_claimed"], False)

    def test_the_location_header_is_minimized_rather_than_dropped_silently(self):
        location = self.minimization["location_header"]
        self.assertEqual(location["raw_value"], "TRANSIENT_ONLY")
        self.assertIs(location["query_string_persisted"], False)
        self.assertIs(location["information_discarded_while_claiming_exact_provenance"], False)

    def test_data_classes_have_their_own_rules(self):
        self.assertIs(self.minimization["one_global_retention_rule"], False)
        classes = {row["class"]: row for row in self.minimization["data_classes"]}
        self.assertIs(classes["RESPONSE_BODY"]["persist_allowed"], False)
        self.assertEqual(classes["RESPONSE_HEADERS"]["persist_allowed"], "ALLOWLIST_ONLY")

    def test_nothing_sensitive_is_persisted_by_default(self):
        sensitive = self.minimization["sensitive_content"]
        for flag in (
            "arbitrary_full_body_persistence_by_default",
            "credential_or_token_persistence_by_default",
            "target_response_content_copied_into_debug_logs",
        ):
            self.assertIs(sensitive[flag], False, flag)


class TestRetention(unittest.TestCase):
    """§23."""

    def setUp(self):
        self.retention = load(RETENTION)

    def test_every_retention_value_is_a_project_policy_default(self):
        for row in self.retention["retention_by_class"]:
            self.assertEqual(row["decision_kind"], "PROJECT_POLICY_DEFAULT", row["retention_class"])

    def test_no_retention_value_is_presented_as_evidence(self):
        for flag in (
            "values_presented_as_evidence_derived",
            "values_presented_as_industry_safe",
            "values_presented_as_legally_required",
            "values_presented_as_provider_recommended",
        ):
            self.assertIs(self.retention[flag], False, flag)

    def test_every_span_is_finite_and_reasoned(self):
        for row in self.retention["retention_by_class"]:
            self.assertIsInstance(row["retention_days"], int)
            self.assertGreaterEqual(row["retention_days"], 0)
            self.assertTrue(str(row["why"]).strip(), row["retention_class"])

    def test_a_non_persisted_class_retains_nothing(self):
        rows = {row["retention_class"]: row for row in self.retention["retention_by_class"]}
        self.assertEqual(rows["NOT_PERSISTED"]["retention_days"], 0)

    def test_this_policy_does_not_lengthen_an_existing_retention(self):
        relationship = self.retention["relationship_to_the_project_retention_policy"]
        self.assertIs(relationship["this_policy_lengthens_any_existing_retention"], False)
        self.assertIs(relationship["the_stricter_rule_wins_where_both_apply"], True)


class TestTargetPolicy(unittest.TestCase):
    """§25 to §32."""

    def setUp(self):
        self.target = load(TARGET)
        self.classes = {row["class"]: row for row in self.target["classes"]}

    def test_only_the_eligible_class_proceeds(self):
        proceeding = [name for name, row in self.classes.items() if row["proceeds"]]
        self.assertEqual(proceeding, ["ELIGIBLE_PUBLIC_TARGET"])

    def test_known_restrictions_exclude(self):
        known = self.target["known_restrictions"]
        for flag in (
            "an_explicit_opt_out_excludes",
            "a_known_automation_restriction_relevant_to_this_activity_excludes",
            "an_operator_exclusion_excludes",
        ):
            self.assertIs(known[flag], True, flag)
        self.assertIs(known["a_known_restriction_may_be_deliberately_ignored"], False)

    def test_unknown_terms_are_not_permission(self):
        unknown = self.target["unknown_terms"]
        self.assertEqual(unknown["state"], "TARGET_TERMS_NOT_INDIVIDUALLY_REVIEWED")
        self.assertIs(unknown["absence_of_inspection_read_as_absence_of_restriction"], False)

    def test_unknown_terms_do_not_reinstate_a_per_item_human_review(self):
        """§28. No favourable fiction, and no impossible requirement added by accident."""
        self.assertIs(
            self.target["unknown_terms"]["manual_terms_review_of_every_corpus_item_required"], False
        )
        self.assertIs(self.target["unknown_terms"]["target_specific_review_may_still_apply"], True)

    def test_an_unclassifiable_condition_excludes(self):
        self.assertIs(self.classes["UNKNOWN_POLICY_CONDITION"]["proceeds"], False)

    def test_the_preflight_ordering_is_deterministic(self):
        ordering = self.target["preflight_ordering"]
        self.assertIs(ordering["first_match_wins"], True)
        self.assertEqual(len(ordering["order"]), len(set(ordering["order"])))
        self.assertEqual(ordering["order"][-1], "ELIGIBLE_PUBLIC_TARGET")
        for name in self.classes:
            self.assertIn(name, ordering["order"], name)

    def test_an_excluded_target_keeps_its_place_in_the_population(self):
        """Mission 1.71's invariant, which an exclusion must not break."""
        population = self.target["excluded_targets_and_the_population"]
        self.assertIs(population["an_excluded_target_is_removed_from_the_corpus"], False)
        self.assertIs(population["the_original_frozen_corpus_is_edited"], False)
        self.assertIn("NOT_ATTEMPTED", population["an_excluded_target_becomes"])


class TestExclusionRegistry(unittest.TestCase):
    """§29, §30."""

    def setUp(self):
        self.exclusions = load(EXCLUSIONS)

    def test_every_entry_needs_a_basis_and_an_operator(self):
        required = {row["field"] for row in self.exclusions["entry_fields"] if row["required"]}
        for field in (
            "target_scope",
            "reason",
            "basis",
            "recorded_at",
            "effective_from",
            "operator",
            "status",
        ):
            self.assertIn(field, required, field)

    def test_the_registry_is_versioned_and_hashed(self):
        self.assertEqual(self.exclusions["hashing"]["algorithm"], "sha256")
        self.assertIs(self.exclusions["hashing"]["a_run_binds_a_registry_version_and_hash"], True)

    def test_the_effective_set_is_frozen_before_execution(self):
        freeze = self.exclusions["freeze"]
        self.assertIs(freeze["effective_set_frozen_before_execution"], True)
        self.assertIs(freeze["the_pre_run_manifest_may_be_silently_rewritten"], False)

    def test_no_entries_exist_because_no_corpus_does(self):
        self.assertEqual(self.exclusions["entries"], [])
        self.assertEqual(self.exclusions["entry_count"], 0)


class TestLoadProfile(unittest.TestCase):
    """§33 to §40."""

    def setUp(self):
        self.load_profile = load(LOAD)
        self.bounds = {row["bound"]: row for row in self.load_profile["bounds"]}

    def test_every_required_bound_is_set(self):
        for bound in (
            "MAX_CORPUS_TARGETS",
            "GLOBAL_CONCURRENCY",
            "PER_ORIGIN_CONCURRENCY",
            "PER_ORIGIN_REQUEST_RATE",
            "CONNECT_TIMEOUT",
            "READ_TIMEOUT",
            "MAX_REDIRECTS",
            "MAX_RETRIES",
            "MAX_HEADER_BYTES",
            "MAX_RESPONSE_READ_BYTES",
            "MAX_TOTAL_BYTES_PER_TARGET",
            "MAX_RUN_DURATION",
            "ROBOTS_REQUEST_BUDGET",
            "MAX_REQUESTS_PER_TARGET",
            "BACKOFF_POLICY",
        ):
            self.assertIn(bound, self.bounds, bound)

    def test_every_value_is_finite_or_explicitly_disabled(self):
        for name, row in self.bounds.items():
            value = row["value"]
            if isinstance(value, str):
                self.assertEqual(value, "DISABLED", name)
            else:
                self.assertIsInstance(value, (int, float), name)
                self.assertGreaterEqual(value, 0, name)

    def test_no_bound_carries_a_non_limit_spelling(self):
        for name, row in self.bounds.items():
            self.assertNotIn(
                str(row["value"]).lower(),
                {"none", "unlimited", "infinite", "automatic", "library_default"},
                name,
            )

    def test_every_number_says_it_is_a_project_policy_default(self):
        for name, row in self.bounds.items():
            self.assertEqual(row["value_source"], "PROJECT_POLICY_DEFAULT", name)
        self.assertIs(self.load_profile["every_value_source_is_project_policy"], True)

    def test_no_number_is_presented_as_discovered(self):
        for flag in (
            "safe_according_to_industry",
            "legally_required",
            "provider_recommended",
            "evidence_derived",
        ):
            self.assertIs(self.load_profile["values_presented_as"][flag], False, flag)

    def test_concurrency_and_rate_are_bounded(self):
        self.assertLessEqual(self.bounds["GLOBAL_CONCURRENCY"]["value"], 8)
        self.assertEqual(self.bounds["PER_ORIGIN_CONCURRENCY"]["value"], 1)
        self.assertGreater(self.bounds["PER_ORIGIN_REQUEST_RATE"]["value"], 0)

    def test_retries_are_zero_and_the_reason_is_stated(self):
        self.assertEqual(self.bounds["MAX_RETRIES"]["value"], 0)
        self.assertTrue(str(self.load_profile["retry_reasoning"]["why_zero"]).strip())

    def test_the_per_target_budget_covers_its_own_redirect_limit(self):
        self.assertGreaterEqual(
            self.bounds["MAX_REQUESTS_PER_TARGET"]["value"],
            self.bounds["MAX_REDIRECTS"]["value"] + 1,
        )

    def test_one_target_is_not_one_request(self):
        accounting = self.load_profile["per_origin_accounting"]
        self.assertIs(accounting["one_target_equals_one_request"], False)
        self.assertIs(accounting["redirects_count_toward_the_origin_budget"], True)
        self.assertIs(accounting["robots_requests_count_toward_the_origin_budget"], True)

    def test_a_body_disabled_profile_still_bounds_the_network_read(self):
        interaction = self.load_profile["body_and_network_interaction"]
        self.assertEqual(interaction["body_persistence"], "DISABLED")
        self.assertIs(interaction["not_persisting_a_body_means_not_receiving_bytes"], False)
        self.assertIs(interaction["the_apparatus_terminates_reading_under_a_finite_bound"], True)
        self.assertGreater(self.bounds["MAX_RESPONSE_READ_BYTES"]["value"], 0)


class TestLinkageAndUnchangedState(unittest.TestCase):
    """§11, §45, §46, §47, §50."""

    def setUp(self):
        self.linkage = load(LINKAGE)

    def test_all_five_decisions_are_linked_to_an_artifact(self):
        resolved = {row["gov"]: row for row in self.linkage["resolved_rows"]}
        for gov in ("GOV-1", "GOV-2", "GOV-3", "GOV-4", "GOV-5"):
            self.assertIn(gov, resolved, gov)
            self.assertTrue(str(resolved[gov]["resolved_by"]).strip(), gov)
            self.assertTrue(str(resolved[gov]["decision"]).strip(), gov)
        self.assertIs(self.linkage["all_five_resolved"], True)

    def test_the_apparatus_contract_was_not_amended(self):
        self.assertIs(self.linkage["apparatus_contract_amended"], False)
        self.assertIs(load(APPARATUS_CONTRACT)["implemented"], False)

    def test_nothing_is_implemented_or_authorized(self):
        self.assertIs(self.linkage["fetcher_implemented"], False)
        self.assertIs(self.linkage["run_authorization_required"], True)

    def test_a_second_independent_route_is_still_required(self):
        self.assertIs(self.linkage["second_independent_route_still_required"], True)
        self.assertIs(load(COUNTERPART)["second_independent_route_still_required"], True)

    def test_no_counterpart_was_searched_or_selected(self):
        counterpart = load(COUNTERPART)
        self.assertIs(counterpart["counterpart_selected"], False)
        self.assertEqual(counterpart["counterpart_candidates_evaluated"], 0)

    def test_common_crawl_and_http_archive_are_unchanged(self):
        held = self.linkage["held_state_not_reopened"]
        for route in ("COMMON_CRAWL", "HTTP_ARCHIVE"):
            self.assertEqual(held[route], "unchanged from Mission 1.70", route)
        self.assertIs(held["a_new_internal_track_repairs_their_missingness"], False)

    def test_the_scanner_arc_is_still_parked(self):
        self.assertEqual(
            self.linkage["held_state_not_reopened"]["scanner_arc"],
            "PARKED_BUT_REOPENABLE_ON_NEW_FIRST_PARTY_EVIDENCE",
        )

    def test_the_candidate_rule_was_not_added_from_design_evidence(self):
        """§47. Writing a policy that respects a rule is not observing a failure."""
        registry = self.linkage["requirement_registry"]
        self.assertIs(registry["added"], False)
        self.assertEqual(registry["count_before"], 15)
        self.assertEqual(registry["count_after"], 15)
        names = {
            r["name"] for r in load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]
        }
        self.assertNotIn(registry["candidate_rule"], names)

    def test_problem_family_is_still_parked(self):
        self.assertEqual(load(BASELINE)["canonical_baseline"]["problem_family"], "PARKED")


class TestNothingWasExecuted(unittest.TestCase):
    """§51, §52."""

    def test_no_target_or_robots_request_was_made(self):
        self.assertEqual(load(ROBOTS)["robots_target_requests"], 0)
        self.assertEqual(load(ROBOTS)["requests_made_this_mission"], 0)

    def test_no_content_was_retrieved(self):
        self.assertEqual(load(MINIMIZATION)["content_retrieved_this_mission"], 0)

    def test_the_documentation_budget_holds_and_no_target_was_inspected(self):
        budget = load(BASELINE)["documentation_budget"]
        self.assertLessEqual(budget["used"], budget["maximum_requests"])
        self.assertEqual(len(budget["requests"]), budget["used"])
        self.assertEqual(budget["target_sites_inspected"], 0)
        self.assertEqual(budget["targets_browsed"], 0)
        for request in budget["requests"]:
            self.assertIs(request["is_a_target_inspection"], False)

    def test_no_record_froze_a_predicate_or_retrieved_values(self):
        for path in ALL_RECORDS:
            record = load(path)
            if "exact_predicate_frozen" in record:
                self.assertIs(record["exact_predicate_frozen"], False, path.name)
            if "target_values_retrieved" in record:
                self.assertEqual(record["target_values_retrieved"], 0, path.name)

    def test_no_migration_was_created(self):
        migrations = REPO_ROOT / "infrastructure" / "migrations"
        if migrations.exists():
            heads = sorted(p.name for p in migrations.glob("0036_*"))
            self.assertEqual(heads, [])

    def test_no_crawler_module_was_created(self):
        for candidate in ("bounded_http_fetcher.py", "http_fetcher.py", "public_http_fetcher.py"):
            self.assertFalse((SCRIPTS / candidate).exists(), candidate)


class TestValidatorAndRenderer(unittest.TestCase):
    def setUp(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("_phg172", RENDERER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_the_live_records_validate(self):
        self.module.validate()

    def test_the_validator_knows_every_prohibited_use(self):
        self.assertEqual(len(self.module.PROHIBITED_USES), 9)

    def test_the_validator_knows_the_secret_bearing_headers(self):
        for header in ("Set-Cookie", "WWW-Authenticate", "Proxy-Authenticate", "Authorization"):
            self.assertIn(header, self.module.SECRET_BEARING_HEADERS, header)

    def test_the_validator_requires_every_load_bound(self):
        self.assertEqual(len(self.module.REQUIRED_BOUNDS), 15)

    def test_the_validator_treats_every_non_limit_spelling_as_forbidden(self):
        for spelling in ("unlimited", "infinite", "automatic", "library_default", None):
            self.assertIn(spelling, self.module.FORBIDDEN_BOUND_VALUES, str(spelling))

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
        self.assertIn("PUBLIC_HTTP_OBSERVATION_TRACK_ADOPTED", page)
        self.assertIn("granted by this mission: **False**", page)
        load_page = LOAD_PAGE.read_text(encoding="utf-8")
        self.assertIn("Every value below is a project policy default", load_page)


if __name__ == "__main__":
    unittest.main()
