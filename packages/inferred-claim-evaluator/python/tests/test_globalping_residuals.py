"""Mission 1.74, continued by Mission 1.74.7. One residual closed, one still open.

Mission 1.74 pursued both residuals to the end of the public record and closed neither,
froze two enquiries, and sent nothing. Mission 1.74.7 recorded the provider's answer to
the first: R1 is now R1_PASS_PROVIDER_DECLARED_NO_REDIRECT at an evidence level that did
not exist when this file was written, C6 is PASS, and the tally reads 11/1/0.

So this file now guards two things at once. The current records -- the v2 review, the v2
closure, the v3 qualification and the v5 decision -- are what the gate validates. The
superseded ones are asserted to STILL SAY WHAT THEY SAID: 10/2/0, two residuals
remaining, R1_PARTIAL_IMPLEMENTATION_ONLY. They were right when they were written, and a
mission that backdated a later closure into them would be rewriting history rather than
continuing it.

Most of it is still about the readings that were available and refused. An implementation
is not a contract. A dependency default is not a provider commitment. Zero matches for a
word mean the word is absent, not the behaviour. A commercial-use answer that defers to
the Terms does not widen them. A schema accepting a public target is validation, not
permission. Silence is not permission and ambiguity is not prohibition either. And, added
by 1.74.7: a provider DECLARATION is not documentation, and a better tally is not a
verdict.
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

BASELINE = DATA / "mission-1.74-baseline-v1.json"
LEDGER = DATA / "mission-1.74-documentation-ledger-v1.json"
REDIRECT = DATA / "globalping-redirect-contract-review-v2.json"
TERMS_SCOPE = DATA / "globalping-provider-terms-scope-review-v1.json"
COMMERCIAL = DATA / "globalping-commercial-purpose-review-v1.json"
THIRD_PARTY = DATA / "globalping-third-party-target-scope-review-v1.json"
CLOSURE = DATA / "globalping-residual-closure-v2.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v3.json"
READINESS = DATA / "q1-two-route-readiness-v2.json"
DECISION = DATA / "quantity-class-selection-decision-v5.json"
R1_PACKET = DATA / "globalping-r1-enquiry-packet-v1.json"
R2_PACKET = DATA / "globalping-r2-enquiry-packet-v1.json"

QUALIFICATION_V1 = DATA / "independent-http-counterpart-qualification-v1.json"
SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"
APPARATUS_REGISTRY = DATA / "observation-addressable-apparatus-contract-v1.json"
GOVERNANCE_DECISION = DATA / "public-http-observation-governance-decision-v1.json"
MINIMIZATION_1_72 = DATA / "public-http-data-minimization-policy-v1.json"
RENDERER = SCRIPTS / "render_globalping_residuals.py"
DECISION_PAGE = DATA / "mission-1.74-globalping-residuals-v1.md"
REDIRECT_PAGE = DATA / "globalping-redirect-evidence-v1.md"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


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


class TestTheRecordsExist(unittest.TestCase):
    """1 to 4. Twelve records, and none of them is a stub."""

    def test_every_record_exists_and_is_an_object(self):
        for path in (
            BASELINE,
            LEDGER,
            REDIRECT,
            TERMS_SCOPE,
            COMMERCIAL,
            THIRD_PARTY,
            CLOSURE,
            QUALIFICATION,
            READINESS,
            DECISION,
            R1_PACKET,
            R2_PACKET,
        ):
            with self.subTest(record=path.name):
                self.assertTrue(path.exists(), path.name)
                self.assertIsInstance(load(path), dict)

    def test_every_record_names_the_mission_that_wrote_it(self):
        moved_by_1_74_7 = {
            "globalping-redirect-contract-review-v2.json",
            "globalping-residual-closure-v2.json",
            "globalping-counterpart-qualification-v3.json",
            "quantity-class-selection-decision-v5.json",
        }
        for path in (
            BASELINE,
            LEDGER,
            REDIRECT,
            TERMS_SCOPE,
            COMMERCIAL,
            THIRD_PARTY,
            CLOSURE,
            QUALIFICATION,
            READINESS,
            DECISION,
            R1_PACKET,
            R2_PACKET,
        ):
            with self.subTest(record=path.name):
                expected = "1.74.7" if path.name in moved_by_1_74_7 else "1.74"
                self.assertEqual(load(path)["mission"], expected)

    def test_the_superseded_records_still_say_what_they_said(self):
        # Mission 1.74's records were right when they were written, and a later mission
        # that backdated the closure into them would be rewriting history rather than
        # continuing it.
        for name, verdict in (
            ("globalping-redirect-contract-review-v1.json", "R1_PARTIAL_IMPLEMENTATION_ONLY"),
            ("globalping-residual-closure-v1.json", None),
            ("globalping-counterpart-qualification-v2.json", None),
            ("quantity-class-selection-decision-v4.json", None),
        ):
            record = load(DATA / name)
            with self.subTest(record=name):
                self.assertEqual(record["mission"], "1.74")
                self.assertEqual(record["forward_pointer"]["appended_by_mission"], "1.74.7")
                if verdict is not None:
                    self.assertEqual(record["verdict"], verdict)
        self.assertEqual(
            load(DATA / "globalping-residual-closure-v1.json")["residuals_remaining"], 2
        )
        old_tally = load(DATA / "globalping-counterpart-qualification-v2.json")["tally"]
        self.assertEqual((old_tally["PASS"], old_tally["PARTIAL"]), (10, 2))
        self.assertEqual(
            load(DATA / "quantity-class-selection-decision-v4.json")["primary_outcome"],
            "GLOBALPING_TWO_PROVIDER_CLARIFICATIONS_REQUIRED",
        )

    def test_both_generated_pages_exist(self):
        self.assertTrue(DECISION_PAGE.exists())
        self.assertTrue(REDIRECT_PAGE.exists())

    def test_the_renderer_exists(self):
        self.assertTrue(RENDERER.exists())


class TestThePrecondition(unittest.TestCase):
    """5 to 10. The mission starts where Mission 1.73 stopped."""

    def setUp(self):
        self.pre = load(BASELINE)["repository_precondition"]

    def test_mission_1_73_is_merged_at_its_own_commit(self):
        self.assertTrue(self.pre["mission_1_73_merged"])
        self.assertEqual(self.pre["expected_main"], "2c05b73")
        self.assertEqual(self.pre["observed_main"], self.pre["expected_main"])

    def test_the_working_tree_was_clean_and_matched_origin(self):
        self.assertTrue(self.pre["working_tree_clean"])
        self.assertTrue(self.pre["local_matches_origin"])

    def test_the_globalping_package_was_present(self):
        self.assertTrue(self.pre["globalping_qualification_package_present"])
        self.assertTrue(self.pre["adr_039_present"])

    def test_the_initial_state_is_ten_two_zero(self):
        self.assertEqual(self.pre["globalping_initial_pass"], 10)
        self.assertEqual(self.pre["globalping_initial_partial"], 2)
        self.assertEqual(self.pre["globalping_initial_fail"], 0)

    def test_mission_1_73s_record_still_says_the_same(self):
        tally = load(QUALIFICATION_V1)["tally"]
        self.assertEqual((tally["PASS"], tally["PARTIAL"], tally["FAIL"]), (10, 2, 0))

    def test_no_sros_fetcher_exists(self):
        self.assertFalse(self.pre["sros_fetcher_implemented"])

    def test_no_selection_artifact_existed_or_exists(self):
        self.assertTrue(self.pre["selected_quantity_class_artifact_absent"])
        self.assertTrue(self.pre["selected_construct_artifact_absent"])
        selection_authorises_nothing(self, SELECTED_CLASS)
        self.assertFalse(SELECTED_CONSTRUCT.exists())

    def test_the_baseline_records_no_drift(self):
        baseline = load(BASELINE)["canonical_baseline"]
        self.assertEqual(baseline["drift_from_mission_1_73"], "none")
        self.assertEqual(baseline["migration_head"], "0035_refusal_provenance")


class TestTheScope(unittest.TestCase):
    """11 to 14. One candidate, and no arc reopened to reach it."""

    def setUp(self):
        self.scope = load(BASELINE)["scope"]

    def test_globalping_is_the_only_candidate(self):
        self.assertEqual(self.scope["only_candidate"], "GLOBALPING")
        self.assertEqual(self.scope["alternative_counterparts_evaluated"], 0)

    def test_no_discovery_was_restarted(self):
        for flag in (
            "counterpart_discovery_performed",
            "quantity_class_discovery_performed",
            "scanner_discovery_performed",
        ):
            with self.subTest(flag=flag):
                self.assertFalse(self.scope[flag])

    def test_nothing_was_selected_or_frozen(self):
        self.assertFalse(self.scope["construct_selected"])
        self.assertFalse(self.scope["predicate_selected"])

    def test_the_mission_resolves_exactly_the_two_residuals(self):
        self.assertEqual(sorted(self.scope["resolves"]), ["R1", "R2"])


class TestTheDocumentationBudget(unittest.TestCase):
    """15 to 18. Failed retrievals count, and no request touched the API."""

    def setUp(self):
        self.ledger = load(LEDGER)

    def test_the_budget_was_not_exceeded(self):
        self.assertLessEqual(self.ledger["used"], self.ledger["maximum_requests"])

    def test_each_sub_budget_was_respected(self):
        for name, cap in self.ledger["caps"].items():
            with self.subTest(sub_budget=name):
                self.assertLessEqual(self.ledger["split"][name], cap)

    def test_the_split_sums_to_what_was_used(self):
        self.assertEqual(sum(self.ledger["split"].values()), self.ledger["used"])
        self.assertEqual(len(self.ledger["requests"]), self.ledger["used"])

    def test_failed_retrievals_were_counted(self):
        self.assertTrue(self.ledger["failed_counted_against_budget"])
        self.assertGreater(self.ledger["failed_or_empty"], 0)

    def test_no_api_execution_and_no_target_request(self):
        self.assertEqual(self.ledger["globalping_api_executions"], 0)
        self.assertEqual(self.ledger["target_http_requests"], 0)


class TestR1TheRedirectContract(unittest.TestCase):
    """19 to 30. The evidence is graded rather than pooled."""

    def setUp(self):
        self.redirect = load(REDIRECT)

    def test_the_question_is_frozen_and_narrow(self):
        question = self.redirect["exact_question"]
        self.assertIn("HEAD", question["question"])
        self.assertIn("3xx", question["question"])
        self.assertFalse(question["broadened_into_generic_redirect_support"])

    def test_more_than_one_surface_was_reviewed(self):
        surfaces = self.redirect["surfaces_reviewed"]
        self.assertGreaterEqual(len(surfaces), 5)
        self.assertEqual(len(surfaces), self.redirect["surfaces_reviewed_count"])

    def test_zero_matches_mean_an_absence_in_a_surface(self):
        self.assertFalse(self.redirect["zero_matches_proves_no_redirect"])
        self.assertEqual(self.redirect["zero_matches_means"], "NOT_DOCUMENTED_IN_REVIEWED_SURFACE")

    def test_the_implementation_is_not_a_contract(self):
        implementation = self.redirect["implementation"]
        self.assertEqual(implementation["IMPLEMENTATION_CONTRACT_STATUS"], "NON_NORMATIVE")
        self.assertEqual(implementation["CURRENT_IMPLEMENTATION_FOLLOWS_REDIRECTS"], "NO")

    def test_the_implementation_was_not_run_against_a_target(self):
        implementation = self.redirect["implementation"]
        self.assertFalse(implementation["run_against_a_live_target"])
        self.assertFalse(
            implementation["local_redirect_test_constructed_and_presented_as_provider_behaviour"]
        )

    def test_the_dependency_default_binds_nobody(self):
        dependency = self.redirect["dependency_default"]
        self.assertFalse(dependency["globalping_normatively_binds_to_it"])
        self.assertFalse(dependency["can_close_r1_by_itself"])

    def test_no_provider_test_asserts_the_behaviour(self):
        tests = self.redirect["provider_tests"]
        self.assertEqual(tests["tests_asserting_http_measurement_redirect_behaviour"], 0)
        self.assertFalse(tests["treated_as_public_api_contract"])

    def test_the_maintainer_statement_is_graded_as_incidental(self):
        statements = self.redirect["provider_statements_found"]
        self.assertTrue(statements)
        for statement in statements:
            with self.subTest(locator=statement["locator"]):
                self.assertEqual(
                    statement["evidence_level"], "PROVIDER_MAINTAINER_STATEMENT_INCIDENTAL"
                )
                self.assertTrue(statement["what_it_does_not_establish"].strip())

    def test_the_verdict_closes_on_a_declaration_and_says_declaration(self):
        # Mission 1.74.7. DOCUMENTED would claim a surface that does not exist: the
        # specification still has zero occurrences of the word.
        self.assertEqual(self.redirect["verdict"], "R1_PASS_PROVIDER_DECLARED_NO_REDIRECT")
        self.assertEqual(
            self.redirect["evidence_level"], "R1_A2_SOLICITED_RESPONSIVE_PROVIDER_ANSWER"
        )
        self.assertFalse(self.redirect["documented_in_any_reviewed_surface"])

    def test_it_closed_the_way_mission_1_74_said_it_could(self):
        closed_by = self.redirect["closed_by"]
        self.assertTrue(closed_by["as_anticipated_by_mission_1_74"])
        self.assertTrue(closed_by["condition_written_before_the_answer_existed"])
        self.assertIn("technical channel", closed_by["anticipated_wording"])

    def test_the_solicited_answer_meets_every_condition_and_states_its_limit(self):
        answer = self.redirect["solicited_provider_answer"]
        for condition in (
            "solicited",
            "responsive_to_the_exact_predicate",
            "attributable_to_the_provider",
            "durable_and_citable",
            "retrieved_without_a_summarising_extraction",
        ):
            with self.subTest(condition=condition):
                self.assertTrue(answer[condition])
        self.assertEqual(answer["redirect_response_returned"], "ESTABLISHED")
        self.assertEqual(answer["redirect_not_followed"], "ESTABLISHED")
        self.assertFalse(answer["treated_as_broader_than_the_question"])
        self.assertFalse(answer["reply_restated_here"])
        self.assertIn("zero occurrences", answer["what_it_does_not_establish"])

    def test_the_statement_did_not_upgrade_the_evidence_level(self):
        self.assertFalse(self.redirect["evidence_level_upgraded_by_the_maintainer_statement"])
        self.assertTrue(self.redirect["why_not_upgraded"].strip())

    def test_nothing_in_the_reviewed_surfaces_documents_it(self):
        self.assertFalse(self.redirect["documented_in_any_reviewed_surface"])

    def test_why_it_is_load_bearing_names_the_invisible_divergence(self):
        reason = self.redirect["why_it_is_load_bearing"]
        self.assertTrue(reason["invisible_in_the_values"])
        self.assertTrue(reason["statement"].strip())


class TestR2TheTerms(unittest.TestCase):
    """31 to 40. The Terms read whole, with their headings."""

    def setUp(self):
        self.terms = load(TERMS_SCOPE)

    def test_the_terms_version_is_recorded(self):
        version = self.terms["terms_version"]
        for field in ("document", "source", "effective_date", "retrieved_at"):
            with self.subTest(field=field):
                self.assertTrue(str(version[field]).strip())

    def test_versions_were_not_combined_and_none_was_chosen_for_being_favourable(self):
        self.assertFalse(self.terms["versions_silently_combined"])
        self.assertFalse(
            self.terms["website_shell_versus_repository_copy"]["favourable_version_chosen"]
        )

    def test_the_consumer_clause_stays_consumer_scoped(self):
        clause = self.terms["consumer_commercial_clause"]
        self.assertEqual(clause["heading_scope"], "CONSUMER_ONLY")
        self.assertFalse(clause["applied_globally"])

    def test_business_users_being_mentioned_is_not_a_grant(self):
        structure = self.terms["structure"]
        self.assertTrue(structure["business_users_contemplated"])
        self.assertFalse(structure["mention_treated_as_a_grant"])

    def test_the_reservation_clause_keeps_its_scope(self):
        reservation = self.terms["reservation_of_rights"]
        self.assertEqual(reservation["scope"], "SERVICE_AND_IP_RIGHTS")
        self.assertFalse(reservation["read_as_everything_unmentioned_is_prohibited"])
        self.assertFalse(reservation["ignored"])

    def test_copyright_licence_semantics_were_not_imported(self):
        self.assertFalse(
            self.terms["reservation_of_rights"][
                "copyright_licence_semantics_imported_without_textual_basis"
            ]
        )

    def test_prohibited_use_silence_creates_no_grant(self):
        self.assertFalse(self.terms["prohibited_use"]["absence_creates_a_grant"])

    def test_the_faq_and_examples_rank_below_the_terms(self):
        ranking = self.terms["authority_ranking"]
        self.assertFalse(ranking["faq_may_override_contradictory_terms"])
        self.assertFalse(ranking["examples_may_override_terms"])

    def test_the_definitions_hook_was_followed_in_both_directions(self):
        hook = self.terms["definitions_hook"]
        self.assertTrue(hook["so_the_website_description_was_read"])
        self.assertFalse(hook["does_it_widen_the_scope"])
        self.assertTrue(hook["what_the_website_says"].strip())


class TestR2ACommercialUse(unittest.TestCase):
    """41 to 45. The half that closes, and what it does not reach."""

    def setUp(self):
        self.commercial = load(COMMERCIAL)

    def test_it_closes_on_the_providers_own_answer(self):
        self.assertEqual(
            self.commercial["verdict"], "COMMERCIAL_USE_GENERAL_PERMITTED_WITHIN_TERMS"
        )
        evidence = self.commercial["first_party_evidence"]
        self.assertTrue(evidence["provider_answer"].strip())
        self.assertTrue(evidence["read_from_website_source_rather_than_a_rendered_shell"])

    def test_it_was_not_overstated(self):
        self.assertFalse(self.commercial["overstated_beyond_the_provider_text"])

    def test_it_does_not_resolve_third_party_target_scope(self):
        limits = self.commercial["what_the_answer_does_not_do"]
        self.assertFalse(limits["resolves_third_party_target_scope"])
        self.assertFalse(limits["widens_the_terms"])

    def test_public_access_does_not_establish_r2(self):
        access = self.commercial["access_recorded_separately"]
        self.assertTrue(access["ACCESS_WITHOUT_ACCOUNT"])
        self.assertFalse(access["establishes_r2"])


class TestR2BThirdPartyTargetScope(unittest.TestCase):
    """46 to 54. The half that does not close, and why it does not close either way."""

    def setUp(self):
        self.third = load(THIRD_PARTY)

    def test_the_intended_activity_is_frozen_and_unsimplified(self):
        activity = self.third["frozen_intended_activity"]
        self.assertTrue(activity["description"].strip())
        self.assertFalse(activity["simplified_to_commercial_scraping"])
        self.assertFalse(activity["simplified_to_monitoring_our_infrastructure"])

    def test_the_permitted_use_question_is_answered_as_ambiguous(self):
        section = self.third["permitted_use_section"]
        self.assertEqual(section["is_it_an_exclusive_purpose_limitation"], "AMBIGUOUS")
        self.assertTrue(section["exact_wording"].strip())
        self.assertEqual(section["form"], "DESCRIPTIVE")
        self.assertEqual(section["heading_suggests"], "LIMITATION")

    def test_the_api_schema_is_technical_validation_only(self):
        api = self.third["api_target_definition"]
        self.assertEqual(api["classification"], "TECHNICAL_TARGET_VALIDATION_ONLY")
        self.assertFalse(api["is_an_express_permitted_use_grant"])

    def test_product_design_is_neither_a_grant_nor_an_override(self):
        design = self.third["product_design_evidence"]
        self.assertFalse(design["product_design_is_a_terms_grant"])
        self.assertFalse(design["provider_examples_override_terms"])

    def test_the_evidence_points_both_ways_and_says_so(self):
        design = self.third["product_design_evidence"]
        self.assertTrue(design["pointing_toward_third_party_targets"])
        self.assertTrue(design["pointing_toward_own_infrastructure"])

    def test_silence_was_not_turned_favourable_and_ambiguity_not_into_prohibition(self):
        self.assertFalse(self.third["terms_silence_turned_favourable"])
        self.assertFalse(self.third["terms_ambiguity_turned_into_prohibition"])

    def test_the_verdict_is_unresolved(self):
        self.assertEqual(self.third["verdict"], "THIRD_PARTY_TARGET_SCOPE_UNRESOLVED")


class TestTheClosure(unittest.TestCase):
    """55 to 66. Both residuals moved and neither closed."""

    def setUp(self):
        self.closure = load(CLOSURE)
        self.residuals = {r["id"]: r for r in self.closure["residuals"]}

    def test_one_residual_remains_and_it_is_r2(self):
        self.assertEqual(self.closure["residuals_remaining"], 1)
        self.assertEqual(sum(1 for r in self.closure["residuals"] if not r["closed"]), 1)
        self.assertTrue(self.residuals["R1"]["closed"])
        self.assertFalse(self.residuals["R2"]["closed"])
        self.assertFalse(self.residuals["R1"]["closed_on_documentation"])
        self.assertFalse(self.closure["r2_touched_by_this_mission"])

    def test_both_residuals_moved_and_say_how(self):
        for residual_id, residual in self.residuals.items():
            with self.subTest(residual=residual_id):
                self.assertTrue(residual["moved"])
                self.assertTrue(residual["what_moved"].strip())

    def test_r2_needs_both_halves(self):
        both = self.closure["r2_pass_requires_both"]
        self.assertTrue(both["A_commercial_purpose_compatible"])
        self.assertFalse(both["B_third_party_targets_within_permitted_use"])
        self.assertEqual(both["verdict"], "R2_PARTIAL")

    def test_the_sub_results_restate_the_reviews(self):
        self.assertEqual(
            self.closure["sub_results"]["R2_A_COMMERCIAL_USE"], "PERMITTED_WITHIN_TERMS"
        )
        self.assertEqual(self.closure["sub_results"]["R2_B_THIRD_PARTY_TARGET_SCOPE"], "UNRESOLVED")

    def test_refusing_under_ambiguity_is_governance_not_impossibility(self):
        governance = self.closure["project_governance_classification"]
        self.assertEqual(governance["classification"], "PROVIDER_TERMS_REQUIRE_CLARIFICATION")
        self.assertFalse(governance["provider_terms_block_the_intended_activity"])
        self.assertFalse(governance["refusing_under_ambiguity_is_legal_impossibility"])
        self.assertTrue(governance["and_that_is_not_the_same_as_permission"])

    def test_adr_039_was_not_weakened_anywhere(self):
        for flag, value in self.closure["adr_039_unchanged"].items():
            if flag.startswith("$"):
                continue
            with self.subTest(flag=flag):
                self.assertTrue(value)

    def test_the_1_72_body_default_is_still_disabled(self):
        self.assertEqual(load(MINIMIZATION_1_72)["body"]["BODY_PERSISTENCE_DEFAULT"], "DISABLED")

    def test_the_1_72_governance_decision_was_not_edited(self):
        self.assertEqual(
            load(GOVERNANCE_DECISION)["decision"], "PUBLIC_HTTP_OBSERVATION_TRACK_ADOPTED"
        )


class TestTheEnquiries(unittest.TestCase):
    """67 to 78. Prepared, frozen, hashed, and not sent."""

    def setUp(self):
        self.closure = load(CLOSURE)
        self.packets = [load(R1_PACKET), load(R2_PACKET)]

    def test_both_were_sent_and_only_one_was_answered(self):
        enquiries = self.closure["enquiries"]
        self.assertEqual(enquiries["enquiries_sent"], 2)
        self.assertTrue(enquiries["operator_approval_recorded"])
        self.assertTrue(enquiries["r1_reply_received"])
        self.assertFalse(enquiries["r2_reply_received"])
        # A contact is receipt demonstrated. R1's reply demonstrates it; R2's own record
        # still reads provider_contacted false, and this may not overrule it.
        self.assertTrue(enquiries["provider_contacted"])
        self.assertIn("R1 only", enquiries["provider_contacted_basis"])
        self.assertFalse(
            load(DATA / "globalping-r2-v2-dispatch-approval-v1.json")["execution"][
                "provider_contacted"
            ]
        )

    def test_a_review_mission_still_authorises_no_dispatch(self):
        self.assertFalse(self.closure["enquiries"]["dispatch_authorised_by_this_mission"])

    def test_the_public_review_was_exhausted_first(self):
        self.assertFalse(self.closure["enquiries"]["prepared_before_public_review_was_exhausted"])

    def test_each_question_maps_to_exactly_one_gate(self):
        enquiries = self.closure["enquiries"]
        self.assertTrue(enquiries["each_question_maps_to_exactly_one_gate"])
        self.assertFalse(enquiries["combined_ambiguous_question_asked"])

    def test_two_packets_because_two_channels_are_designated(self):
        self.assertTrue(self.closure["enquiries"]["two_packets_because"].strip())
        channels = {packet["channel"] for packet in self.packets}
        self.assertEqual(len(channels), 2)

    def test_every_packet_is_unsent_and_unapproved(self):
        for packet in self.packets:
            with self.subTest(question=packet["question_id"]):
                self.assertEqual(packet["send_status"], "NOT_AUTHORIZED")
                self.assertFalse(packet["sent"])
                self.assertFalse(packet["operator_approval_recorded"])
                self.assertFalse(packet["execution_record_created"])

    def test_no_recipient_was_guessed(self):
        for packet in self.packets:
            with self.subTest(question=packet["question_id"]):
                self.assertFalse(packet["recipient_guessed"])
                self.assertTrue(packet["first_party_channel_basis"].strip())

    def test_each_packet_answers_to_its_recorded_hash(self):
        for packet in self.packets:
            with self.subTest(question=packet["question_id"]):
                binding = {key: packet[key] for key in packet["hash_covers"]}
                digest = hashlib.sha256(
                    json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8")
                ).hexdigest()
                self.assertEqual(digest, packet["content_sha256"])

    def test_the_hash_excludes_itself_the_status_and_the_date(self):
        for packet in self.packets:
            with self.subTest(question=packet["question_id"]):
                for excluded in ("content_sha256", "send_status", "recorded_at"):
                    self.assertNotIn(excluded, packet["hash_covers"])
                    self.assertIn(excluded, packet["hash_excludes"])

    def test_each_packet_says_why_the_documentation_is_insufficient(self):
        for packet in self.packets:
            with self.subTest(question=packet["question_id"]):
                self.assertTrue(packet["why_public_documentation_is_insufficient"].strip())
                self.assertTrue(packet["expected_answer_discriminator"].strip())

    def test_the_packets_cover_exactly_the_open_residuals(self):
        prepared = {packet["residual_id"] for packet in self.packets}
        needing = {r["id"] for r in self.closure["residuals"] if r["enquiry_prepared"]}
        self.assertEqual(prepared, needing)


class TestTheQualification(unittest.TestCase):
    """79 to 88. Twelve dimensions recomputed, and the tally did not move."""

    def setUp(self):
        self.qualification = load(QUALIFICATION)
        self.gates = {g["dimension"]: g for g in self.qualification["gates"]}

    def test_twelve_mandatory_dimensions_are_present(self):
        self.assertEqual(len(self.qualification["gates"]), 12)
        for gate in self.qualification["gates"]:
            with self.subTest(dimension=gate["dimension"]):
                self.assertTrue(gate["mandatory"])
                self.assertTrue(gate["why"].strip())

    def test_the_tally_is_eleven_one_zero_and_matches_the_matrix(self):
        tally = self.qualification["tally"]
        self.assertEqual((tally["PASS"], tally["PARTIAL"], tally["FAIL"]), (11, 1, 0))
        counted = {name: 0 for name in ("PASS", "PARTIAL", "FAIL", "UNKNOWN")}
        for gate in self.qualification["gates"]:
            counted[gate["status"]] += 1
        self.assertEqual(counted, tally)

    def test_the_tally_changed_and_the_verdict_did_not(self):
        self.assertTrue(self.qualification["tally_changed"])
        self.assertEqual(
            (
                self.qualification["tally_before"]["PASS"],
                self.qualification["tally_before"]["PARTIAL"],
            ),
            (10, 2),
        )
        self.assertFalse(self.qualification["verdict_changed"])
        self.assertEqual(self.qualification["verdict"], "COUNTERPART_UNRESOLVED")

    def test_c6_follows_r1_and_c9_follows_r2(self):
        self.assertEqual(self.gates["C6_REQUEST_CONTRACT_RECONSTRUCTABILITY"]["status"], "PASS")
        self.assertEqual(self.gates["C9_RIGHTS_FEASIBILITY"]["status"], "PARTIAL")
        self.assertTrue(self.gates["C6_REQUEST_CONTRACT_RECONSTRUCTABILITY"]["recomputed"])
        # C9 is NOT recomputed: R2 was not examined, and a reply about redirects
        # establishes nothing about Terms scope.
        self.assertFalse(self.gates["C9_RIGHTS_FEASIBILITY"]["recomputed"])

    def test_the_counterpart_is_not_qualified(self):
        self.assertEqual(self.qualification["verdict"], "COUNTERPART_UNRESOLVED")

    def test_no_passing_dimension_was_reopened(self):
        self.assertFalse(self.qualification["passing_dimensions_reopened"])
        self.assertFalse(self.qualification["contradicting_evidence_found"])

    def test_no_score_was_issued(self):
        self.assertTrue(self.qualification["no_score_issued"])

    def test_mission_1_74s_record_is_superseded_rather_than_edited(self):
        self.assertEqual(
            self.qualification["supersedes"], "globalping-counterpart-qualification-v2.json"
        )
        self.assertTrue(QUALIFICATION_V1.exists())
        self.assertTrue((DATA / "globalping-counterpart-qualification-v2.json").exists())
        self.assertTrue(self.qualification["supersedes_note"].strip())

    def test_the_mission_records_what_it_added(self):
        self.assertTrue(self.qualification["what_this_mission_added"])


class TestQ1AndIndependence(unittest.TestCase):
    """89 to 96. Nothing about a pair, because there is no pair."""

    def setUp(self):
        self.readiness = load(READINESS)

    def test_q1_did_not_move(self):
        self.assertEqual(
            self.readiness["q1_status_before"], "PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED"
        )
        self.assertEqual(self.readiness["q1_status_after"], self.readiness["q1_status_before"])
        self.assertFalse(self.readiness["q1_status_changed_this_mission"])

    def test_the_load_bearing_failure_is_the_unqualified_counterpart(self):
        conditions = self.readiness["conditions_for_strategic_viability"]
        self.assertEqual(conditions["verdict"], "NOT_YET_STRATEGICALLY_VIABLE")
        self.assertFalse(conditions["one_external_counterpart_qualified"])
        self.assertEqual(conditions["load_bearing_failure"], "one_external_counterpart_qualified")

    def test_no_independence_group_exists(self):
        self.assertEqual(self.readiness["independence"]["evidence_independence_groups"], 0)
        self.assertEqual(
            self.readiness["independence"]["classification"], "INDEPENDENCE_ARCHITECTURE_PLAUSIBLE"
        )

    def test_no_pair_language_is_used(self):
        independence = self.readiness["independence"]
        for flag in (
            "called_an_independent_evidence_pair",
            "called_a_validated_evidence_pair",
            "called_corroborating_measurements",
        ):
            with self.subTest(flag=flag):
                self.assertFalse(independence[flag])

    def test_pair_analysis_is_not_ready(self):
        self.assertEqual(self.readiness["pair_analysis"], "PAIR_ANALYSIS_NOT_READY")

    def test_what_changed_and_what_did_not_are_both_recorded(self):
        changed = self.readiness["what_did_change"]
        self.assertTrue(changed["resolved_this_mission"])
        self.assertEqual(len(changed["still_unresolved"]), 2)


class TestTheDecision(unittest.TestCase):
    """97 to 112. One outcome, seven refusals, and every counter at zero."""

    def setUp(self):
        self.decision = load(DECISION)

    def test_the_primary_outcome_names_which_residual_closed(self):
        # A count would have been true and weaker: exactly one remains either way.
        self.assertEqual(
            self.decision["primary_outcome"],
            "GLOBALPING_REDIRECT_CONTRACT_CLOSED_RIGHTS_SCOPE_REMAINS",
        )

    def test_nothing_downstream_followed_from_r1_closing(self):
        did_not = self.decision["what_did_not_follow_from_r1_closing"]
        self.assertFalse(did_not["quantity_class_selected"])
        self.assertFalse(did_not["construct_selected"])
        self.assertEqual(did_not["evidence_independence_groups_created"], 0)
        self.assertFalse(did_not["counterpart_qualified"])
        self.assertFalse(did_not["q1_strategically_viable"])
        self.assertTrue(did_not["why"].strip())

    def test_every_other_outcome_was_refused_with_a_reason(self):
        refused = self.decision["outcomes_considered_and_refused"]
        self.assertGreaterEqual(len(refused), 7)
        for name, entry in refused.items():
            with self.subTest(outcome=name):
                self.assertTrue(entry["refused"])
                self.assertTrue(entry["why"].strip())

    def test_nothing_was_selected(self):
        self.assertIsNone(self.decision["selected_quantity_class"])
        self.assertEqual(self.decision["selection_outcome"], "NO_SELECTION")
        self.assertFalse(self.decision["selected_class_artifact_created"])
        self.assertFalse(self.decision["selected_construct_created"])

    def test_the_counterpart_is_not_qualified_and_q1_is_not_viable(self):
        self.assertFalse(self.decision["counterpart_qualified"])
        self.assertFalse(self.decision["q1_strategically_viable"])

    def test_no_legal_conclusion_was_drawn(self):
        self.assertFalse(self.decision["legal_conclusion_made"])
        self.assertEqual(self.decision["external_legal_conclusion"], "NO_EXTERNAL_LEGAL_CONCLUSION")

    def test_the_outcome_uses_no_legal_vocabulary(self):
        for banned in ("LEGAL", "UNLAWFUL", "DEFINITIVELY_LEGALLY_PERMITTED"):
            with self.subTest(word=banned):
                self.assertNotEqual(self.decision["primary_outcome"], banned)

    def test_every_hard_zero_counter_is_zero(self):
        accounting = self.decision["mission_accounting"]
        for counter in (
            "GLOBALPING_MEASUREMENTS_CREATED",
            "GLOBALPING_MEASUREMENTS_READ",
            "GLOBALPING_API_EXECUTIONS",
            "GLOBALPING_PROBE_RUNS",
            "TARGET_HTTP_REQUESTS",
            "SROS_FETCHER_RUNS",
            "TARGET_VALUE_EXPOSURES",
            "ACCOUNTS_CREATED",
            "TOKENS_CREATED",
            "TRIALS",
            "PURCHASES",
            "CREDENTIAL_READS",
            "MAILBOX_SEARCHES",
            "ENQUIRIES_SENT",
            "PROVIDER_CONTACTS",
            "ALTERNATIVE_COUNTERPARTS_EVALUATED",
            "SOURCES_REGISTERED",
            "SOURCE_GOVERNANCE_MUTATIONS",
            "THRESHOLDS_REGISTERED",
            "CLAIMS_CREATED",
            "EVIDENCE_CREATED",
            "INDEPENDENCE_GROUPS_CREATED",
            "RELIABILITY_VALUES_ASSIGNED",
            "SCORES",
            "OPPORTUNITY_MUTATIONS",
            "MODEL_CALLS",
            "EMBEDDINGS",
            "MIGRATIONS",
            "CONSTRUCTS_SELECTED",
            "QUANTITY_CLASSES_SELECTED",
        ):
            with self.subTest(counter=counter):
                self.assertEqual(accounting[counter], 0)

    def test_the_documentation_budget_was_respected_in_accounting(self):
        accounting = self.decision["mission_accounting"]
        self.assertLessEqual(
            accounting["FIRST_PARTY_DOCUMENT_REQUESTS"], accounting["FIRST_PARTY_REQUEST_BUDGET"]
        )

    def test_no_parallel_arc_was_touched(self):
        parallel = self.decision["parallel_state_untouched"]
        for flag, value in parallel.items():
            if flag.startswith("$") or isinstance(value, str):
                continue
            with self.subTest(flag=flag):
                self.assertFalse(value)

    def test_the_two_parallel_states_did_not_move(self):
        parallel = self.decision["parallel_state_untouched"]
        self.assertEqual(parallel["onyphe_response_status"], "NOT_CHECKED_AFTER_DISPATCH")
        self.assertEqual(parallel["netlas_contact_state"], "STILL_PENDING")

    def test_no_canonical_mutation(self):
        self.assertEqual(self.decision["canonical_mutation_boundary"]["mutations_this_mission"], 0)

    def test_the_next_mission_was_not_started(self):
        next_action = self.decision["recommended_next_action"]
        self.assertTrue(next_action["mission_1_75_not_started"])
        self.assertTrue(next_action["dispatch_requires_a_separate_explicitly_authorized_action"])

    def test_the_registry_did_not_grow(self):
        registry = self.decision["requirement_registry"]
        self.assertEqual(registry["count_before"], 15)
        self.assertEqual(registry["count_after"], 15)
        self.assertIsNone(registry["requirement_added"])
        self.assertFalse(registry["registry_growth_forced"])

    def test_the_registry_file_still_holds_fifteen(self):
        requirements = load(APPARATUS_REGISTRY)["requirement_registry"]["requirements"]
        self.assertEqual(len(requirements), 15)

    def test_it_supersedes_the_v4_decision_rather_than_editing_it(self):
        self.assertEqual(self.decision["supersedes"], "quantity-class-selection-decision-v4.json")
        self.assertTrue((DATA / "quantity-class-selection-decision-v4.json").exists())
        self.assertTrue((DATA / "quantity-class-selection-decision-v3.json").exists())


class TestNothingWasMeasuredOrFrozen(unittest.TestCase):
    """113 to 116. The counters that appear on every record of this arc."""

    def test_no_record_froze_a_predicate(self):
        for path in (BASELINE, REDIRECT, CLOSURE, QUALIFICATION, READINESS, DECISION):
            record = load(path)
            if "exact_predicate_frozen" in record:
                with self.subTest(record=path.name):
                    self.assertFalse(record["exact_predicate_frozen"])

    def test_no_record_retrieved_a_target_value(self):
        for path in (BASELINE, CLOSURE, QUALIFICATION, READINESS, DECISION):
            record = load(path)
            if "target_values_retrieved" in record:
                with self.subTest(record=path.name):
                    self.assertEqual(record["target_values_retrieved"], 0)

    def test_no_reliability_number_appears_outside_a_census(self):
        census = ("canonical_baseline", "canonical_mutation_boundary", "mission_accounting")

        def walk(node, key=None):
            if key in census:
                return
            if isinstance(node, dict):
                for child_key, value in node.items():
                    if (
                        "reliability" in child_key.lower()
                        and isinstance(value, (int, float))
                        and not isinstance(value, bool)
                    ):
                        raise AssertionError(f"a reliability number appears: {child_key}")
                    walk(value, child_key)
            elif isinstance(node, list):
                for item in node:
                    walk(item, key)

        for path in (
            BASELINE,
            LEDGER,
            REDIRECT,
            TERMS_SCOPE,
            COMMERCIAL,
            THIRD_PARTY,
            CLOSURE,
            QUALIFICATION,
            READINESS,
            DECISION,
        ):
            with self.subTest(record=path.name):
                walk(load(path))


class TestTheRenderer(unittest.TestCase):
    """117 to 124. Deterministic, offline, and refusing rather than repairing."""

    def setUp(self):
        self.tree = ast.parse(RENDERER.read_text(encoding="utf-8"))

    def test_it_imports_nothing_that_reaches_a_network(self):
        forbidden = {
            "requests",
            "httpx",
            "urllib",
            "urllib3",
            "socket",
            "http",
            "aiohttp",
            "psycopg",
            "sqlalchemy",
        }
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn(alias.name.split(".")[0], forbidden)
            elif isinstance(node, ast.ImportFrom) and node.module:
                self.assertNotIn(node.module.split(".")[0], forbidden)

    def test_it_reads_no_clock(self):
        source = RENDERER.read_text(encoding="utf-8")
        for banned in ("datetime.now", "utcnow", "time.time("):
            with self.subTest(call=banned):
                self.assertNotIn(banned, source)

    def test_it_defines_a_validation_error_and_a_validate(self):
        names = {
            node.name
            for node in ast.walk(self.tree)
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }
        self.assertIn("ValidationError", names)
        self.assertIn("validate", names)

    def test_it_supports_check(self):
        self.assertIn("--check", RENDERER.read_text(encoding="utf-8"))

    def test_it_names_the_three_census_blocks(self):
        source = RENDERER.read_text(encoding="utf-8")
        for block in ("canonical_baseline", "canonical_mutation_boundary", "mission_accounting"):
            with self.subTest(block=block):
                self.assertIn(block, source)

    def test_the_pages_are_marked_generated(self):
        for page in (DECISION_PAGE, REDIRECT_PAGE):
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                self.assertIn("Do not edit by hand", text)

    def test_the_decision_page_reports_the_outcome_and_names_which_residual_closed(self):
        text = DECISION_PAGE.read_text(encoding="utf-8")
        self.assertIn("GLOBALPING_REDIRECT_CONTRACT_CLOSED_RIGHTS_SCOPE_REMAINS", text)
        self.assertIn("COUNTERPART_UNRESOLVED", text)
        # The packet field still reads NOT_AUTHORIZED and the page must not let that be
        # read as "nothing was sent": the dispatch column is beside it.
        self.assertIn("NOT_AUTHORIZED", text)
        self.assertIn("THIS DOCUMENT RECORDS NO AUTHORIZATION", text)

    def test_the_redirect_page_keeps_the_implementation_non_normative(self):
        text = REDIRECT_PAGE.read_text(encoding="utf-8")
        self.assertIn("NON_NORMATIVE", text)
        self.assertIn("R1_PASS_PROVIDER_DECLARED_NO_REDIRECT", text)
        # The incidental statement keeps its non-closing grade beside the answer.
        self.assertIn("PROVIDER_MAINTAINER_STATEMENT_INCIDENTAL", text)
        self.assertIn("R1_A2_SOLICITED_RESPONSIVE_PROVIDER_ANSWER", text)


class TestGovernanceRecordsThis(unittest.TestCase):
    """125 to 128. The mission is visible in the documents that govern the project."""

    def test_the_manifest_lists_every_new_record(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for path in (
            REDIRECT,
            TERMS_SCOPE,
            COMMERCIAL,
            THIRD_PARTY,
            CLOSURE,
            QUALIFICATION,
            READINESS,
            DECISION,
            R1_PACKET,
            R2_PACKET,
        ):
            with self.subTest(record=path.name):
                self.assertIn(path.name, text)

    def test_the_manifest_lists_the_renderer(self):
        self.assertIn(RENDERER.name, MANIFEST.read_text(encoding="utf-8"))

    def test_ci_runs_the_new_gate(self):
        self.assertIn(RENDERER.name, CI.read_text(encoding="utf-8"))

    def test_the_mission_report_exists(self):
        report = REPO_ROOT / "docs" / "architecture" / "mission-1.74-report.md"
        self.assertTrue(report.exists())


if __name__ == "__main__":
    unittest.main()
