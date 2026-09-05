"""Mission 1.68. Five constructs, seven apparatuses, and every construct has one route.

The finding is only visible because five were compared rather than one pursued: each
construct has exactly ONE plausible apparatus route, and it is a DIFFERENT apparatus
each time. The apparatuses are individually capable and pairwise disjoint.

There is a reason, and it is about what these products sell. A commercial scanner
publishes SERVICES — what is running where — because that is what its customers buy, and
a service record presupposes a response. The discovery stage, which port answered, is an
internal step they do not publish as a separately addressable artifact. Sonar publishes
it because sonar.tcp is a research dataset rather than a search product.

So the tests here are mostly about distinctions that had to be kept apart:

  - a SYN response is a transport-layer fact and never an SSH server, whatever port 22 is
    conventionally assigned to;
  - a blocker is GLOBAL or CONSTRUCT-SPECIFIC, and getting that wrong in either direction
    is a real error. Sonar's Mission 1.67 rejection is construct-specific and must
    disappear under a transport-level predicate; Shodan's temporal architecture is global
    and no predicate repairs it;
  - Netlas's web-port population problem appeared where it had never been relevant, and
    it exists only on ports 80 and 443;
  - a count of names is not a count of addresses;
  - and one plausible route is one.

Nothing was retrieved as a value, downloaded, executed, registered or measured.
"""

from __future__ import annotations

import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

BASELINE = DATA / "mission-1.68-baseline-v1.json"
MATRIX = DATA / "scanner-apparatus-capability-matrix-v1.json"
UNIVERSE = DATA / "construct-candidate-universe-v1.json"
COMPARISON = DATA / "product-relevant-construct-comparison-v1.json"
FEASIBILITY = DATA / "construct-route-feasibility-v1.json"
DECISION = DATA / "construct-selection-decision-v1.json"
SELECTED = DATA / "selected-construct-v1.json"
CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"
RENDERER = SCRIPTS / "render_construct_selection.py"

C0 = DATA / "construct-package-c0-ssh-identification-v1.json"
C1 = DATA / "construct-package-c1-tcp22-syn-responsiveness-v1.json"
C2 = DATA / "construct-package-c2-http-response-to-ip-addressed-get-v1.json"
C3 = DATA / "construct-package-c3-tls-certificate-observation-v1.json"
C4 = DATA / "construct-package-c4-dns-record-configuration-v1.json"
ALL_PACKAGES = (C0, C1, C2, C3, C4)

PAGES = (
    DATA / "mission-1.68-construct-selection-v1.md",
    DATA / "construct-route-feasibility-v1.md",
)

APPARATUSES = (
    "Censys",
    "Netlas",
    "LeakIX",
    "Shadowserver",
    "ONYPHE",
    "Rapid7 Project Sonar",
    "Shodan",
)


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Preconditions(unittest.TestCase):
    def test_mission_1_67_is_recorded_as_merged_at_its_commit(self) -> None:
        precondition = _load(BASELINE)["repository_precondition"]
        self.assertTrue(precondition["mission_1_67_merged"])
        self.assertEqual(precondition["pull_request"], 112)
        self.assertEqual(precondition["pull_request_state"], "MERGED")
        self.assertEqual(precondition["merge_commit_short"], "c4049cd")
        self.assertTrue(precondition["verified_from_git_not_from_prompt"])

    def test_the_baseline_is_unchanged(self) -> None:
        baseline = _load(BASELINE)["canonical_baseline"]
        self.assertEqual(baseline["drift_from_mission_1_67"], "none")
        self.assertTrue(baseline["measured_live_not_quoted_from_a_report"])
        for key, expected in (
            ("raw_records", 325),
            ("normalized_records", 325),
            ("signals", 33),
            ("claims", 44),
            ("claim_revisions", 45),
            ("evidence", 58),
            ("inferred_claims", 1),
            ("evidence_supports", 57),
            ("evidence_contradicts", 1),
            ("reliability_assessments", 4),
            ("evidence_independence_groups", 0),
            ("registered_sources", 29),
        ):
            self.assertEqual(baseline[key], expected, key)
        self.assertEqual(baseline["problem_family"], "PARKED")
        self.assertEqual(baseline["migration_head"], "0035_refusal_provenance")

    def test_the_registry_starts_and_ends_at_fifteen(self) -> None:
        requirements = _load(CONTRACT)["requirement_registry"]["requirements"]
        self.assertEqual(len(requirements), 15)
        registry = _load(BASELINE)["requirement_registry"]
        self.assertEqual(registry["count_before"], 15)
        self.assertEqual(registry["count_after"], 15)
        self.assertIsNone(registry["requirement_added_this_mission"])

    def test_a_reusable_rule_was_offered_and_not_added(self) -> None:
        offered = _load(DECISION)["requirement_registry"]["candidate_offered_and_not_added"]
        names = {r["name"] for r in _load(CONTRACT)["requirement_registry"]["requirements"]}
        self.assertNotIn(offered["name"], names)
        self.assertTrue(offered["why_it_was_not_added"].strip())
        # The standard applied is the one Mission 1.67 used when it adopted the previous
        # candidate: a second independent instance in a different shape.
        self.assertIn("second", offered["why_it_was_not_added"].lower())


class TheSshControl(unittest.TestCase):
    def test_the_ssh_construct_is_preserved_not_retired(self) -> None:
        ssh = _load(BASELINE)["current_ssh_construct"]
        self.assertEqual(ssh["status"], "NO_TWO_QUALIFIED_APPARATUS_ROUTE_IDENTIFIED")
        for forbidden in ("FAILED", "BAD_CONSTRUCT", "INVALID"):
            self.assertNotEqual(ssh["status"], forbidden)
            self.assertIn(forbidden, ssh["status_is_not"])
        self.assertEqual(ssh["historical_missions_rewritten"], 0)

    def test_the_control_was_evaluated_through_the_same_matrix(self) -> None:
        self.assertTrue(
            _load(BASELINE)["current_ssh_construct"]["evaluated_as_a_control_this_mission"]
        )
        outcome = _load(DECISION)["current_ssh_construct_outcome"]
        self.assertTrue(outcome["evaluated_through_the_same_matrix"])
        self.assertFalse(outcome["selected"])

    def test_a_favourable_control_result_would_not_have_been_suppressed(self) -> None:
        # §31. The control has one plausible route, which is recorded rather than hidden.
        package = _load(C0)
        plausible = [n for n, c in package["routes"].items() if c["verdict"] == "PLAUSIBLE_ROUTE"]
        self.assertEqual(plausible, ["Netlas"])
        self.assertEqual(package["plausible_apparatus_route_count"], 1)

    def test_the_pivot_is_justified_rather_than_assumed(self) -> None:
        why = _load(BASELINE)["why_a_construct_pivot_is_allowed"]
        self.assertEqual(len(why["conditions_all_of_which_hold_here"]), 6)
        self.assertIn("not a relaxation", why["what_this_is_not"].lower())


class ConstructRelativeQualification(unittest.TestCase):
    def test_every_blocker_is_classified_global_or_construct_specific(self) -> None:
        for apparatus in _load(MATRIX)["apparatuses"]:
            for blocker in apparatus["blockers"]:
                self.assertIn(
                    blocker["kind"],
                    {"APPARATUS_GLOBAL_BLOCKER", "CONSTRUCT_SPECIFIC_BLOCKER"},
                    apparatus["name"],
                )

    def test_a_global_temporal_blocker_persists_across_every_construct(self) -> None:
        for path in ALL_PACKAGES:
            routes = _load(path)["routes"]
            for name in ("Shodan", "LeakIX"):
                self.assertEqual(routes[name]["verdict"], "BLOCKED_TEMPORAL", f"{path.name}/{name}")

    def test_a_global_frame_blocker_persists_across_every_construct(self) -> None:
        for path in ALL_PACKAGES:
            self.assertEqual(
                _load(path)["routes"]["Shadowserver"]["verdict"], "BLOCKED_FRAME", path.name
            )

    def test_sonars_construct_specific_blocker_correctly_disappears(self) -> None:
        # Mission 1.67 blocked Sonar because its arbitrary-TCP resource carries no response
        # bytes. That is construct-specific, and a transport-level predicate does not ask
        # for response bytes. Carrying it forward would repeat 1.67's answer without
        # repeating its work.
        self.assertEqual(
            _load(C0)["routes"]["Rapid7 Project Sonar"]["verdict"],
            "BLOCKED_PREDICATE_NOT_RETRIEVABLE",
        )
        self.assertEqual(_load(C1)["routes"]["Rapid7 Project Sonar"]["verdict"], "PLAUSIBLE_ROUTE")

    def test_a_construct_specific_blocker_appeared_where_it_had_not_applied(self) -> None:
        # Netlas is fine for a non-web-port construct and blocked for a web-port one, on
        # its own documentation. The direction runs both ways or the distinction is
        # decorative.
        self.assertEqual(_load(C0)["routes"]["Netlas"]["verdict"], "PLAUSIBLE_ROUTE")
        self.assertEqual(
            _load(C2)["routes"]["Netlas"]["verdict"], "BLOCKED_PREDICATE_NOT_RETRIEVABLE"
        )

    def test_sonars_two_studies_are_separate_resources(self) -> None:
        sonar = next(a for a in _load(MATRIX)["apparatuses"] if a["name"] == "Rapid7 Project Sonar")
        surfaces = " ".join(sonar["surfaces_evaluated"]).lower()
        self.assertIn("sonar.tcp", surfaces)
        self.assertIn("http", surfaces)

    def test_censys_was_re_evaluated_on_a_resource_specific_basis(self) -> None:
        censys = next(a for a in _load(MATRIX)["apparatuses"] if a["name"] == "Censys")
        self.assertGreaterEqual(len(censys["surfaces_evaluated"]), 2)
        blockers = " ".join(b["blocker"] for b in censys["blockers"])
        self.assertIn("TEMPORAL", blockers)

    def test_censys_last_observed_timestamp_is_quoted_first_party(self) -> None:
        censys = next(a for a in _load(MATRIX)["apparatuses"] if a["name"] == "Censys")
        quoted = " ".join(str(b.get("source_says", "")) for b in censys["blockers"])
        self.assertIn("last observed", quoted)

    def test_shodans_temporal_architecture_cannot_be_waived_by_a_new_predicate(self) -> None:
        split = _load(FEASIBILITY)["global_versus_construct_specific"]
        self.assertIn("Shodan", split["global_blockers_that_persist_across_every_construct"])

    def test_access_terms_are_not_an_epistemic_disqualifier(self) -> None:
        censys = next(a for a in _load(MATRIX)["apparatuses"] if a["name"] == "Censys")
        self.assertFalse(censys["access"]["used_as_an_epistemic_disqualifier"])


class SemanticDiscipline(unittest.TestCase):
    def test_a_syn_response_is_never_an_ssh_server(self) -> None:
        package = _load(C1)
        self.assertIn("SYN", package["proposition"]["predicate"])
        self.assertNotIn("ssh", package["proposition"]["canonical_subject"].lower())
        self.assertTrue(package["why_tcp_responsiveness_is_not_ssh"].strip())
        self.assertTrue(
            any("NOT that an SSH server" in claim for claim in package["explicit_non_claims"])
        )

    def test_the_syn_construct_states_the_transport_layer_reason(self) -> None:
        why = _load(C1)["why_tcp_responsiveness_is_not_ssh"]
        self.assertIn("transport-layer", why)
        self.assertIn("RFC 4253", why)

    def test_tcp_responsiveness_is_allowed_as_an_exact_observation_level_fact(self) -> None:
        package = _load(C1)
        self.assertEqual(package["structural_verdict"], "NOT_STRUCTURALLY_VIABLE")
        # It fails on routes, never on the proposition being unstatable.
        self.assertEqual(
            package["failed_hard_conditions"], ["at least TWO apparatus routes are PLAUSIBLE"]
        )
        # The statement stays at the observation level: a completed handshake on a
        # named port from a named vantage, with no application named anywhere.
        established = package["what_a_positive_observation_establishes"]
        self.assertIn("TCP handshake", established)
        self.assertIn("port 22", established)
        self.assertNotIn("ssh", established.lower())

    def test_every_construct_states_explicit_non_claims(self) -> None:
        for path in ALL_PACKAGES:
            self.assertTrue(_load(path)["explicit_non_claims"], path.name)

    def test_product_relevance_is_required_and_classified(self) -> None:
        allowed = {
            "STRONG_PRODUCT_RELEVANCE",
            "MODERATE_PRODUCT_RELEVANCE",
            "WEAK_PRODUCT_RELEVANCE",
            "NON_PRODUCT_RELEVANT",
        }
        for path in ALL_PACKAGES:
            package = _load(path)
            self.assertIn(package["product_relevance"]["class"], allowed, path.name)
            self.assertNotEqual(package["product_relevance"]["class"], "NON_PRODUCT_RELEVANT")
            self.assertTrue(package["product_relevance"]["weakest_truthful_interpretation"].strip())

    def test_weak_relevance_candidates_are_recorded_as_weak(self) -> None:
        for path in (C3, C4):
            package = _load(path)
            self.assertEqual(package["product_relevance"]["class"], "WEAK_PRODUCT_RELEVANCE")
            self.assertIn("product relevance >= MODERATE", package["failed_hard_conditions"])

    def test_a_certificate_is_not_a_purchase(self) -> None:
        claims = " ".join(_load(C3)["explicit_non_claims"]).lower()
        self.assertIn("purchase", claims)
        self.assertIn("not", claims)

    def test_dns_configuration_is_not_customership(self) -> None:
        claims = " ".join(_load(C4)["explicit_non_claims"]).lower()
        self.assertIn("customer", claims)

    def test_ct_log_presence_is_not_an_active_measurement(self) -> None:
        package = _load(C3)
        self.assertIn("Certificate Transparency", package["proposition"]["exclusion_rule"])
        self.assertEqual(package["routes"]["Censys"]["verdict"], "BLOCKED_LINEAGE")


class PropositionSchema(unittest.TestCase):
    def test_every_proposition_field_is_frozen(self) -> None:
        for path in ALL_PACKAGES:
            proposition = _load(path)["proposition"]
            for field in (
                "canonical_subject",
                "population",
                "population_type",
                "unit",
                "deduplication_unit",
                "observation_window_semantics",
                "predicate",
                "inclusion_rule",
                "exclusion_rule",
                "vantage_semantics",
                "configuration_assumptions",
            ):
                self.assertTrue(str(proposition[field]).strip(), f"{path.name}: {field}")

    def test_an_ip_population_counts_distinct_addresses_and_not_rows(self) -> None:
        for path in ALL_PACKAGES:
            proposition = _load(path)["proposition"]
            if proposition["population_type"] != "IP_ADDRESS":
                continue
            self.assertIn("distinct", proposition["unit"].lower(), path.name)
            self.assertNotIn("row", proposition["deduplication_unit"].lower(), path.name)

    def test_a_name_population_is_never_compared_with_an_address_population(self) -> None:
        package = _load(C4)
        self.assertEqual(package["proposition"]["population_type"], "DOMAIN_NAME")
        statement = package["population_incomparability"]["statement"]
        self.assertIn("never", statement.lower())
        self.assertIn("IP_ADDRESS", statement)

    def test_the_window_is_selectable_before_retrieval_in_every_proposition(self) -> None:
        for path in ALL_PACKAGES:
            semantics = _load(path)["proposition"]["observation_window_semantics"]
            self.assertIn("before retrieval", semantics, path.name)

    def test_vantage_is_recorded_separately_from_reliability(self) -> None:
        for path in ALL_PACKAGES:
            self.assertTrue(_load(path)["proposition"]["vantage_semantics"].strip(), path.name)
        # §16. A SYN predicate makes vantage more important, not less.
        self.assertIn("ELEVATED", _load(C1)["proposition"]["vantage_semantics"])

    def test_sampling_configuration_and_frame_stay_separate_concerns(self) -> None:
        split = _load(FEASIBILITY)["global_versus_construct_specific"]
        self.assertIn("elevated_rather_than_removed", split)
        self.assertIn("vantage", split["elevated_rather_than_removed"])


class Routes(unittest.TestCase):
    def test_every_construct_evaluates_all_seven_known_apparatuses(self) -> None:
        for path in ALL_PACKAGES:
            self.assertEqual(set(_load(path)["routes"]), set(APPARATUSES), path.name)

    def test_no_unnamed_hypothetical_scanner_is_counted_as_a_route(self) -> None:
        for path in ALL_PACKAGES:
            for name in _load(path)["routes"]:
                self.assertIn(name, APPARATUSES, f"{path.name}: {name}")

    def test_a_route_count_equals_the_plausible_cells(self) -> None:
        for path in ALL_PACKAGES:
            package = _load(path)
            plausible = [
                n for n, c in package["routes"].items() if c["verdict"] == "PLAUSIBLE_ROUTE"
            ]
            self.assertEqual(package["plausible_apparatus_route_count"], len(plausible), path.name)

    def test_one_plausible_route_is_recorded_as_a_shortfall(self) -> None:
        for path in ALL_PACKAGES:
            package = _load(path)
            if package["plausible_apparatus_route_count"] == 1:
                self.assertEqual(package["route_shortfall"], "SECOND_ROUTE_MISSING", path.name)

    def test_one_route_is_insufficient_for_structural_viability(self) -> None:
        for path in ALL_PACKAGES:
            package = _load(path)
            if package["plausible_apparatus_route_count"] < 2:
                self.assertEqual(
                    package["structural_verdict"], "NOT_STRUCTURALLY_VIABLE", path.name
                )

    def test_a_plausible_route_is_not_a_qualified_apparatus(self) -> None:
        stated = _load(FEASIBILITY)["a_plausible_route_is_not_a_qualified_apparatus"]
        self.assertEqual(stated["qualified_apparatus_count"], 0)
        self.assertEqual(stated["pair_analysis_state"], "PAIR_ANALYSIS_NOT_READY")

    def test_structural_viability_is_not_pair_selection(self) -> None:
        accounting = _load(DECISION)["mission_accounting"]
        self.assertEqual(accounting["PAIRS_SELECTED"], 0)
        self.assertEqual(accounting["APPARATUS_PAIRS_COMPARED"], 0)

    def test_independence_plausibility_is_recorded_without_being_proven(self) -> None:
        independence = _load(FEASIBILITY)["independence_plausibility"]
        self.assertEqual(independence["assessment"], "INDEPENDENCE_NOT_DISPROVEN")
        self.assertTrue(independence["not_established"].strip())
        self.assertIn("tooling", independence["reasoning"].lower())
        self.assertIn("is not shared DATA", independence["reasoning"])

    def test_the_dated_filename_is_not_given_observation_semantics(self) -> None:
        unresolved = " ".join(_load(C1)["unresolved_load_bearing_questions"])
        self.assertIn("date in a Sonar study filename denotes", unresolved)


class Selection(unittest.TestCase):
    def test_nothing_was_selected_and_no_artifact_was_created(self) -> None:
        decision = _load(DECISION)
        self.assertIsNone(decision["selected_construct"])
        self.assertEqual(decision["selection_outcome"], "NO_SELECTION")
        self.assertFalse(decision["selected_construct_artifact_created"])
        self.assertFalse(SELECTED.exists())

    def test_no_construct_is_structurally_viable(self) -> None:
        decision = _load(DECISION)
        self.assertEqual(decision["structurally_viable_count"], 0)
        self.assertEqual(decision["structurally_viable_constructs"], [])

    def test_the_least_bad_was_not_selected_to_make_progress(self) -> None:
        closest = _load(DECISION)["the_construct_that_came_closest"]
        self.assertEqual(closest["construct_id"], "C1_TCP22_SYN_RESPONSIVENESS")
        self.assertTrue(closest["why_it_was_not_selected_anyway"].strip())

    def test_no_weighted_score_was_used(self) -> None:
        method = _load(COMPARISON)["scoring_method"]
        self.assertFalse(method["weighted_numeric_score_used"])
        self.assertEqual(method["method"], "HARD_GATES_THEN_LEXICOGRAPHIC_TIE_BREAK")
        self.assertFalse(method["tie_break_reached"])

    def test_the_comparison_covers_the_required_families(self) -> None:
        ids = {row["construct_id"] for row in _load(COMPARISON)["rows"]}
        self.assertIn("C0_SSH_IDENTIFICATION", ids)
        self.assertIn("C1_TCP22_SYN_RESPONSIVENESS", ids)
        self.assertTrue(any("HTTP" in cid for cid in ids))
        self.assertTrue(any("TLS" in cid or "DNS" in cid for cid in ids))

    def test_the_serious_construct_budget_was_respected(self) -> None:
        budget = _load(UNIVERSE)["budget"]
        self.assertLessEqual(budget["serious_constructs"], budget["maximum_serious_constructs"])
        self.assertEqual(budget["serious_constructs"], 5)
        self.assertLessEqual(budget["used"], budget["maximum_additional_first_party_requests"])

    def test_a_sixth_construct_was_not_invented_to_fill_a_slot(self) -> None:
        families = _load(UNIVERSE)["families_considered"]
        c5 = next(f for f in families if f["family"] == "C5")
        self.assertEqual(c5["status"], "NOT_PROPOSED")
        self.assertIn("fill slot 6", c5["why"])

    def test_the_pattern_is_recorded_as_an_observation_not_a_verdict(self) -> None:
        pattern = _load(COMPARISON)["the_pattern_across_rows"]
        self.assertEqual(len(pattern["detail"]), 5)
        self.assertIn("not established", pattern["this_is_an_observation_not_a_verdict"].lower())

    def test_the_primary_outcome_does_not_overstate_what_was_established(self) -> None:
        decision = _load(DECISION)
        self.assertEqual(
            decision["primary_outcome"], "NO_PRODUCT_RELEVANT_CONSTRUCT_WITH_TWO_ROUTES_IDENTIFIED"
        )
        reasoning = decision["primary_outcome_reasoning"]
        self.assertIn("could not establish", reasoning["why_not_F_class_insufficient"])
        self.assertIn(
            "does not mean no such construct exists", reasoning["what_E_explicitly_does_not_mean"]
        )


class NothingMoved(unittest.TestCase):
    def test_every_hard_zero_is_zero(self) -> None:
        accounting = _load(DECISION)["mission_accounting"]
        for counter in (
            "TARGET_VALUE_EXPOSURES",
            "MEASUREMENT_VALUES_RETRIEVED",
            "RESEARCH_DATA_REQUESTS",
            "API_EXECUTIONS",
            "MEASUREMENT_API_EXECUTIONS",
            "COUNT_ENDPOINT_EXECUTIONS",
            "HOSTS_FETCHED",
            "BANNERS_FETCHED",
            "DATASET_DOWNLOADS",
            "TRIALS",
            "PURCHASES",
            "ACCOUNTS_CREATED",
            "CREDENTIAL_READS",
            "MAILBOX_SEARCHES",
            "ENQUIRIES_SENT",
            "SOURCES_REGISTERED",
            "GOVERNANCE_REVIEWS",
            "GOVERNANCE_MUTATIONS",
            "THRESHOLDS_REGISTERED",
            "CLAIMS_CREATED",
            "EVIDENCE_CREATED",
            "INDEPENDENCE_GROUPS_CREATED",
            "RELIABILITY_ASSESSMENTS_CREATED",
            "RELIABILITY_VALUES_ASSIGNED",
            "SCORES",
            "OPPORTUNITY_MUTATIONS",
            "MODEL_CALLS",
            "EMBEDDINGS",
            "MIGRATIONS",
            "PAIRS_SELECTED",
        ):
            self.assertEqual(accounting[counter], 0, counter)

    def test_no_construct_was_chosen_with_values_in_hand(self) -> None:
        for path in ALL_PACKAGES:
            self.assertEqual(_load(path)["values_consulted_to_choose_this_construct"], 0, path.name)

    def test_no_dataset_was_downloaded(self) -> None:
        # §35. A downloadable Sonar study file is measurement data.
        self.assertEqual(_load(DECISION)["mission_accounting"]["DATASET_DOWNLOADS"], 0)

    def test_onyphe_was_not_polled_contacted_or_moved(self) -> None:
        parallel = _load(DECISION)["parallel_state_untouched"]
        self.assertEqual(parallel["onyphe_response_status"], "NOT_CHECKED_AFTER_DISPATCH")
        for key in (
            "onyphe_mailbox_searched",
            "onyphe_gmail_polled",
            "onyphe_reply_read",
            "onyphe_follow_up_sent",
            "onyphe_state_changed",
        ):
            self.assertFalse(parallel[key], key)

    def test_netlas_was_not_decoded_guessed_or_written_to(self) -> None:
        parallel = _load(DECISION)["parallel_state_untouched"]
        for key in (
            "netlas_address_decoded",
            "netlas_address_guessed",
            "netlas_enquiry_sent",
            "netlas_state_changed",
        ):
            self.assertFalse(parallel[key], key)

    def test_no_canonical_mutation(self) -> None:
        boundary = _load(DECISION)["canonical_mutation_boundary"]
        self.assertEqual(boundary["mutations_this_mission"], 0)
        self.assertEqual(boundary["claims"], 44)
        self.assertEqual(boundary["evidence"], 58)
        self.assertEqual(boundary["registered_sources"], 29)
        self.assertEqual(boundary["problem_family"], "PARKED")

    def test_no_reliability_number_appears_in_any_construct_record(self) -> None:
        for path in ALL_PACKAGES + (FEASIBILITY, MATRIX):
            for node in json.dumps(_load(path)).split(","):
                if "reliability" in node.lower():
                    self.assertNotRegex(node, r"reliability\S*\"\s*:\s*[0-9]", path.name)


class GeneratedPages(unittest.TestCase):
    def test_the_renderer_exists_and_the_pages_are_present(self) -> None:
        self.assertTrue(RENDERER.exists())
        for page in PAGES:
            self.assertTrue(page.exists(), page.name)
            self.assertGreater(len(page.read_text(encoding="utf-8")), 500, page.name)

    def test_the_renderer_is_deterministic_and_reaches_no_network(self) -> None:
        source = RENDERER.read_text(encoding="utf-8")
        for forbidden in ("requests", "urllib", "httpx", "socket", "psycopg"):
            self.assertNotIn(f"import {forbidden}", source)

    def test_the_next_mission_is_recommended_and_not_started(self) -> None:
        recommendation = _load(DECISION)["recommended_next_mission"]
        self.assertTrue(recommendation["mission_1_69_not_started"])
        self.assertIn(
            "Independent Product-Relevant Quantity Class Selection", recommendation["recommended"]
        )
        self.assertEqual(recommendation["do_not"], "keep iterating scanner constructs blindly")

    def test_held_evidence_reduced_the_research_cost(self) -> None:
        reuse = _load(UNIVERSE)["reuse_of_held_evidence"]
        self.assertGreaterEqual(
            len(reuse["facts_taken_from_repository_records_without_re_retrieval"]), 6
        )
        self.assertIn("Eleven retrievals", reuse["cost_reduction_observed"])


if __name__ == "__main__":
    unittest.main()
