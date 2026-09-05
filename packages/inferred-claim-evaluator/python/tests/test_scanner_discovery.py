"""Mission 1.67. Two apparatuses nobody in this arc had evaluated, and neither qualifies.

The two failures are worth more than either would have been alone, because they are the
two halves of one conjunction, seen separately and never together.

Project Sonar publishes what every earlier candidate lacked: dated, immutable,
individually addressed per-study artifacts, so a window is selected BEFORE any value is
retrieved. And the one retrievable dataset covering arbitrary TCP ports carries SYN
responses — which addresses answered, and not one byte the peer sent. The apparatus
states its TCP studies include SSH; the catalogue does not carry it. That is the
retrievable frame differing from the measured frame, which is a rule this repository
already had.

Shodan publishes the other half. Its crawler algorithm is documented, its own probing is
stated plainly, and its database is documented as updated in real time with no time or
date filter anywhere in its filter reference. The only history is per-address, ninety
days, capped. So the window cannot be chosen in the request, and the frame-level
temporal object is a maintained current state.

Two further things this mission establishes rather than assumes. The frame-uniformity
rule was adopted on a SECOND independent instance in a different shape — ONYPHE
partitions by region, Shodan randomises the port under test per crawl step — because a
rule demonstrated once looks like a rule about one provider's habits. And four discovery
hits died at the documentation pre-gate, which is a fact about this mission's reach and
not a finding about those apparatuses.

Nothing was executed, trialled, registered, measured or contacted.
"""

from __future__ import annotations

import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

BASELINE = DATA / "mission-1.67-baseline-v1.json"
RULE_REVIEW = DATA / "apparatus-frame-uniformity-requirement-review-v1.json"
UNIVERSE = DATA / "scanner-discovery-universe-v1.json"
PRESCREEN = DATA / "scanner-candidate-prescreen-v1.json"
SONAR = DATA / "scanner-qualification-rapid7-sonar-v1.json"
SHODAN = DATA / "scanner-qualification-shodan-v1.json"
QUALIFICATION = DATA / "scanner-individual-qualification-v1.json"
READINESS = DATA / "qualified-apparatus-readiness-v4.json"
READINESS_V3 = DATA / "qualified-apparatus-readiness-v3.json"
LEDGER = DATA / "mission-1.67-documentation-ledger-v1.json"
CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"
ONYPHE_PACKAGE = DATA / "onyphe-package-recomputed-v2.json"

RENDERER = SCRIPTS / "render_scanner_discovery.py"

PAGES = (
    DATA / "mission-1.67-scanner-discovery-v1.md",
    DATA / "apparatus-frame-uniformity-requirement-review-v1.md",
    DATA / "scanner-individual-qualification-v1.md",
)


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk(node):
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


class Preconditions(unittest.TestCase):
    def test_mission_1_66_2_is_recorded_as_merged_at_its_commit(self) -> None:
        precondition = _load(BASELINE)["repository_precondition"]
        self.assertTrue(precondition["mission_1_66_2_merged"])
        self.assertEqual(precondition["pull_request"], 111)
        self.assertEqual(precondition["pull_request_state"], "MERGED")
        self.assertEqual(precondition["merge_commit_short"], "6f9c901")
        self.assertTrue(precondition["verified_from_git_not_from_prompt"])

    def test_the_baseline_is_unchanged(self) -> None:
        baseline = _load(BASELINE)["canonical_baseline"]
        self.assertEqual(baseline["drift_from_mission_1_66_2"], "none")
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
            ("claims_carrying_both_directions", 0),
            ("reliability_assessments", 4),
            ("evidence_independence_groups", 0),
            ("registered_sources", 29),
        ):
            self.assertEqual(baseline[key], expected, key)
        self.assertEqual(baseline["scores_table"], "ABSENT")
        self.assertEqual(baseline["reference_profile"], "UNCALIBRATED")
        self.assertEqual(baseline["problem_family"], "PARKED")
        self.assertEqual(baseline["migration_head"], "0035_refusal_provenance")

    def test_the_registry_started_at_fourteen(self) -> None:
        before = _load(BASELINE)["requirement_registry_before"]
        self.assertEqual(before["count"], 14)
        self.assertEqual(len(before["names_in_order"]), 14)
        self.assertEqual(
            before["source_artifact"],
            "docs/data/observation-addressable-apparatus-contract-v1.json",
        )


class TheRequirementDecision(unittest.TestCase):
    def test_the_candidate_rule_was_reviewed_and_the_review_is_mandatory(self) -> None:
        review = _load(RULE_REVIEW)
        for question in (
            "q1_exact_failure_mode",
            "q2_distinct_from_sampling",
            "q3_distinct_from_retrievable_frame",
            "q4_distinct_from_time_addressability",
            "q5_demonstrated_by_onyphe_evidence",
            "q6_reusable_across_apparatuses",
            "q7_changes_future_qualification",
            "q8_decision",
        ):
            self.assertIn(question, review)

    def test_the_review_was_produced_before_candidate_selection(self) -> None:
        review = _load(RULE_REVIEW)
        self.assertTrue(review["candidate_requirement"]["produced_before_candidate_selection"])
        self.assertTrue(
            _load(QUALIFICATION)["registry_decision"]["produced_before_final_candidate_selection"]
        )

    def test_the_decision_is_adopt_and_is_not_ambiguous(self) -> None:
        decision = _load(RULE_REVIEW)["q8_decision"]
        self.assertIn(decision["decision"], {"ADOPT", "DECLINE"})
        self.assertEqual(decision["decision"], "ADOPT")
        self.assertIsNone(decision["existing_rule_that_would_have_covered_it"])

    def test_an_adopted_rule_increments_the_registry_exactly_once(self) -> None:
        names = [r["name"] for r in _load(CONTRACT)["requirement_registry"]["requirements"]]
        self.assertEqual(len(names), 15)
        self.assertEqual(names.count("APPARATUS_CONFIGURATION_MUST_BE_UNIFORM_ACROSS_THE_FRAME"), 1)

    def test_the_fourteen_existing_requirements_are_untouched(self) -> None:
        before = _load(BASELINE)["requirement_registry_before"]["names_in_order"]
        names = [r["name"] for r in _load(CONTRACT)["requirement_registry"]["requirements"]]
        self.assertEqual(names[:14], before)
        decision = _load(QUALIFICATION)["registry_decision"]
        self.assertEqual(decision["existing_requirements_renamed"], 0)
        self.assertEqual(decision["existing_requirements_merged"], 0)

    def test_the_rule_is_distinct_from_the_three_it_could_have_duplicated(self) -> None:
        review = _load(RULE_REVIEW)
        self.assertEqual(review["q2_distinct_from_sampling"]["verdict"], "DISTINCT")
        self.assertEqual(review["q3_distinct_from_retrievable_frame"]["verdict"], "DISTINCT")
        self.assertEqual(review["q4_distinct_from_time_addressability"]["verdict"], "DISTINCT")

    def test_uniformity_is_not_sampling(self) -> None:
        # Sampling asks which ELIGIBLE targets were attempted. Uniformity asks whether the
        # predicate was eligible at all. A complete census of a partition that never opens
        # TCP/22 returns zero, and no sampling disclosure repairs that.
        reason = _load(RULE_REVIEW)["q2_distinct_from_sampling"]["reason"]
        self.assertIn("ELIGIBLE", reason)
        self.assertIn("eligible at all", reason.lower())

    def test_uniformity_is_not_the_retrievable_frame(self) -> None:
        reason = _load(RULE_REVIEW)["q3_distinct_from_retrievable_frame"]["reason"]
        self.assertIn("REQUESTER", reason)
        self.assertIn("MEASURED", reason)

    def test_uniformity_is_not_time_addressability(self) -> None:
        reason = _load(RULE_REVIEW)["q4_distinct_from_time_addressability"]["reason"]
        self.assertIn("WHEN", reason)
        self.assertIn("WHERE", reason)

    def test_the_rule_rests_on_two_independent_instances_in_two_shapes(self) -> None:
        review = _load(RULE_REVIEW)
        self.assertEqual(review["q5_demonstrated_by_onyphe_evidence"]["verdict"], "DEMONSTRATED")
        second = review["q6_reusable_across_apparatuses"]["second_instance"]
        self.assertEqual(second["apparatus"], "Shodan")
        self.assertTrue(second["source_says"])
        self.assertTrue(second["why_the_two_shapes_matter"].strip())

    def test_separable_strata_can_still_satisfy_the_rule(self) -> None:
        # The rule fails an apparatus for not PUBLISHING the mapping, never for being
        # heterogeneous. An apparatus whose partitions are separable satisfies it.
        rule = _load(CONTRACT)["requirement_registry"]["requirements"][-1]["rule"]
        self.assertIn("separable partitions satisfy it", rule)
        self.assertIn("included in every partition", rule)

    def test_no_historical_verdict_was_rewritten_to_fail_the_new_rule(self) -> None:
        self.assertEqual(_load(QUALIFICATION)["registry_decision"]["historical_verdicts_edited"], 0)
        self.assertEqual(
            _load(READINESS)["how_the_existing_four_would_be_viewed_under_the_current_contract"][
                "historical_verdicts_edited"
            ],
            0,
        )
        self.assertEqual(
            _load(ONYPHE_PACKAGE)["individual_status"]["verdict"], "INDIVIDUALLY_UNRESOLVED"
        )

    def test_the_existing_four_keep_the_verdicts_readiness_v3_recorded(self) -> None:
        previous = {a["name"]: a["individual"] for a in _load(READINESS_V3)["apparatuses"]}
        for apparatus in _load(READINESS)["apparatuses"]:
            if apparatus.get("new_this_mission"):
                continue
            self.assertEqual(
                apparatus["individual"], previous[apparatus["name"]], apparatus["name"]
            )


class Discovery(unittest.TestCase):
    def test_the_four_frozen_apparatuses_cannot_be_counted_as_new(self) -> None:
        universe = _load(UNIVERSE)
        classification = {h["name"]: h["classification"] for h in universe["hits"]}
        for name in ("Netlas", "ONYPHE", "LeakIX", "Shadowserver"):
            self.assertEqual(classification[name], "DUPLICATE_EXISTING_APPARATUS", name)
        self.assertEqual(classification["Censys"], "DUPLICATE_EXISTING_APPARATUS")

    def test_the_universe_does_not_claim_to_be_exhaustive(self) -> None:
        exhaustiveness = _load(UNIVERSE)["exhaustiveness"]
        self.assertFalse(exhaustiveness["claimed"])
        self.assertIn("does not establish that none exists", exhaustiveness["statement"])

    def test_every_hit_carries_a_reason_and_a_basis(self) -> None:
        for hit in _load(UNIVERSE)["hits"]:
            self.assertTrue(hit["reason"].strip(), hit["name"])
            self.assertTrue(hit["basis"].strip(), hit["name"])

    def test_uninvestigated_leads_are_not_classified_out_of_the_class(self) -> None:
        # §41. A third-party page can locate a source and cannot close a gate, and
        # classifying something OUT of the apparatus class closes one.
        for hit in _load(UNIVERSE)["hits"]:
            if hit["classification"] == "DISCOVERED_NOT_EVALUATED":
                self.assertEqual(hit["basis"], "PROJECT_HYPOTHESIS_NOT_ESTABLISHED", hit["name"])

    def test_first_party_documentation_is_required_before_serious_status(self) -> None:
        for candidate in _load(PRESCREEN)["candidates"]:
            if candidate["verdict"] == "SERIOUS":
                self.assertTrue(candidate["first_party_method_docs_retrievable"], candidate["name"])
                self.assertGreaterEqual(candidate["documents_retrieved"], 1, candidate["name"])

    def test_a_prescreen_rejection_says_what_it_does_not_establish(self) -> None:
        for candidate in _load(PRESCREEN)["candidates"]:
            if candidate["verdict"] != "SERIOUS":
                self.assertIn(
                    "Nothing about the apparatus",
                    candidate["what_this_does_not_establish"],
                    candidate["name"],
                )

    def test_the_serious_candidate_budget_was_respected(self) -> None:
        serious = [c for c in _load(PRESCREEN)["candidates"] if c["verdict"] == "SERIOUS"]
        self.assertLessEqual(len(serious), 6)
        self.assertEqual(len(serious), 2)

    def test_no_403_was_retried_and_no_header_varied(self) -> None:
        discipline = _load(PRESCREEN)["no_retry_discipline"]
        self.assertFalse(discipline["http_403_retried"])
        self.assertFalse(discipline["headers_varied"])
        self.assertFalse(discipline["anti_bot_measures_bypassed"])
        self.assertFalse(
            discipline["third_party_mirror_or_cache_substituted_for_a_first_party_document"]
        )


class TheLedger(unittest.TestCase):
    def test_the_document_budget_was_not_exceeded(self) -> None:
        budget = _load(LEDGER)["budget"]
        self.assertLessEqual(budget["used"], budget["maximum_first_party_requests"])
        self.assertEqual(budget["used"], 24)
        self.assertEqual(budget["maximum_first_party_requests"], 36)

    def test_failed_retrievals_are_counted(self) -> None:
        # A budget that only counts successes is not a budget.
        ledger = _load(LEDGER)
        counts = ledger["outcome_counts"]
        self.assertGreater(counts["failed"], 0)
        self.assertGreater(counts["retrieved_without_load_bearing_content"], 0)
        self.assertEqual(sum(counts.values()), len(ledger["requests"]))

    def test_a_redirect_to_irrelevant_content_still_counts(self) -> None:
        redirects = [
            r
            for r in _load(LEDGER)["requests"]
            if "301" in r["detail"] and r["outcome"] == "FAILED"
        ]
        self.assertGreaterEqual(len(redirects), 3)

    def test_no_gate_rests_on_a_search_summary(self) -> None:
        ledger = _load(LEDGER)
        self.assertTrue(ledger["search_navigation_requests"]["no_gate_closed_by_a_search_summary"])
        instances = ledger["retrieval_summary_guard"]["instances"]
        self.assertGreaterEqual(len(instances), 2)
        for instance in instances:
            self.assertTrue(instance["what_the_summary_reported"].strip())
            self.assertTrue(instance["what_the_live_documents_returned"].strip())

    def test_every_load_bearing_quote_names_a_document_that_was_retrieved(self) -> None:
        import re

        retrieved = {
            r["url"] for r in _load(LEDGER)["requests"] if r["outcome"] == "RETRIEVED_LOAD_BEARING"
        }
        pattern = re.compile(r"https?://[^\s,()\[\]\"]+")
        for package_path in (SONAR, SHODAN):
            package = _load(package_path)
            for node in _walk(package):
                if not isinstance(node, dict):
                    continue
                for key, value in node.items():
                    if not key.endswith("_provenance"):
                        continue
                    for url in pattern.findall(json.dumps(value)):
                        self.assertIn(url.rstrip(".,;"), retrieved, f"{package_path.name}: {url}")


class SonarPackage(unittest.TestCase):
    def setUp(self) -> None:
        self.package = _load(SONAR)

    def test_active_production_passes_on_a_quoted_first_party_statement(self) -> None:
        gate = self.package["gates"]["A1_ACTIVE_MEASUREMENT_PRODUCER"]
        self.assertEqual(gate["status"], "PASS")
        self.assertTrue(gate["source_says"])
        self.assertTrue(any("internet-wide surveys" in quote for quote in gate["source_says"]))

    def test_the_temporal_object_is_the_right_shape_and_still_not_a_pass(self) -> None:
        # Dated immutable per-study artifacts are §13's own PASS example. What is missing
        # is what the date DENOTES, so a window cannot be mapped onto it.
        gate = self.package["gates"]["A2_OBSERVATION_ADDRESSABLE_EXPOSURE"]
        self.assertEqual(gate["status"], "PARTIAL")
        self.assertEqual(
            self.package["repeated_service_discriminator"]["answer"], "OBSERVATION_EVENT_APPEND"
        )
        self.assertIn("bound_stated", self.package["repeated_service_discriminator"])

    def test_a_syn_response_cannot_carry_an_identification_string(self) -> None:
        gate = self.package["gates"]["A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE"]
        self.assertEqual(gate["status"], "FAIL")
        self.assertTrue(gate["decisive"])
        self.assertEqual(gate["exposure_class"], "NOT_EXPOSED")
        self.assertTrue(
            any("responded positively to the SYN" in quote for quote in gate["source_says"])
        )

    def test_the_measured_frame_differs_from_the_retrievable_frame(self) -> None:
        gate = self.package["gates"]["A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE"]
        self.assertIn("SSH", " ".join(gate["source_says"]))
        self.assertIn(
            "THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME",
            gate["this_is_the_measured_versus_retrievable_frame_rule"],
        )

    def test_semantics_are_not_transferred_between_resources(self) -> None:
        scope = self.package["resource_scope"]
        self.assertFalse(scope["semantics_transferred_between_resources"])
        self.assertEqual(scope["evaluated_resource"], "Sonar Data — TCP Scans dataset")
        self.assertIn(
            "HTTP GET Responses",
            scope["other_resources_present_and_not_evaluated_as_the_construct_carrier"],
        )

    def test_tcp_22_membership_is_not_inferred_from_a_generic_statement(self) -> None:
        slot = self.package["additional_slots"]["configuration_membership_tcp_22"]
        self.assertEqual(slot["status"], "UNKNOWN")
        self.assertIn("STUDIES", slot["project_interpretation"])

    def test_sampling_silence_stays_unknown(self) -> None:
        slot = self.package["additional_slots"]["sampling"]
        self.assertNotEqual(slot["status"], "PASS")
        self.assertIn("UNKNOWN", slot["project_interpretation"])

    def test_access_is_recorded_and_is_not_the_reason_for_the_verdict(self) -> None:
        slot = self.package["additional_slots"]["access"]
        self.assertEqual(slot["status"], "SPECIAL_ACCESS")
        self.assertFalse(slot["used_as_a_disqualifier"])
        self.assertNotIn("access", self.package["verdict"]["decisive_fail_gate"].lower())

    def test_a_hard_fail_produces_not_qualified(self) -> None:
        verdict = self.package["verdict"]
        self.assertEqual(verdict["individual_status"], "INDIVIDUALLY_NOT_QUALIFIED")
        self.assertEqual(verdict["decisive_fail_gate"], "A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE")
        self.assertFalse(verdict["point_score_used"])

    def test_the_package_is_complete_without_being_qualified(self) -> None:
        self.assertTrue(self.package["verdict"]["package_complete"])
        allowed = {
            "PASS",
            "FAIL",
            "PARTIAL",
            "UNKNOWN",
            "NOT_APPLICABLE",
            "NOT_EVALUATED_AFTER_DECISIVE_FAIL",
        }
        for name, gate in self.package["gates"].items():
            self.assertIn(gate["status"], allowed, name)


class ShodanPackage(unittest.TestCase):
    def setUp(self) -> None:
        self.package = _load(SHODAN)

    def test_own_crawling_is_established_first_party(self) -> None:
        gate = self.package["gates"]["A1_ACTIVE_MEASUREMENT_PRODUCER"]
        self.assertEqual(gate["status"], "PASS")
        self.assertTrue(any("crawlers work 24/7" in q for q in gate["source_says"]))

    def test_a_maintained_current_state_fails_observation_addressability(self) -> None:
        gate = self.package["gates"]["A2_OBSERVATION_ADDRESSABLE_EXPOSURE"]
        self.assertEqual(gate["status"], "FAIL")
        self.assertTrue(gate["decisive"])
        self.assertEqual(gate["temporal_object"], "MAINTAINED_SERVICE_STATE")

    def test_the_absence_of_a_time_filter_was_checked_rather_than_assumed(self) -> None:
        # Failing a gate on an absence nobody looked for is the error. The filter
        # reference was fetched precisely so this absence is an examined one.
        facts = self.package["gates"]["A2_OBSERVATION_ADDRESSABLE_EXPOSURE"][
            "three_independent_blocking_facts"
        ]
        checked = [f for f in facts if "why_this_one_matters_most" in f]
        self.assertEqual(len(checked), 1)
        self.assertIn("shodan.io/search/filters", checked[0]["source_says_provenance"])
        self.assertIn("POSITIVE CHECK", checked[0]["why_this_one_matters_most"])

    def test_a_per_address_history_is_not_a_window_addressable_frame(self) -> None:
        gate = self.package["gates"]["A2_OBSERVATION_ADDRESSABLE_EXPOSURE"]
        self.assertIn("retrieve-then-inspect", gate["project_interpretation"])
        discriminator = self.package["repeated_service_discriminator"]
        self.assertEqual(discriminator["answer_at_frame_level"], "MAINTAINED_SERVICE_STATE")
        self.assertEqual(discriminator["answer_at_address_level"], "VERSIONED_OBSERVATION_HISTORY")
        self.assertEqual(discriminator["which_one_the_construct_needs"], "frame level")

    def test_the_second_resource_was_evaluated_rather_than_failed_by_inheritance(self) -> None:
        trends = self.package["second_resource_shodan_trends"]
        self.assertEqual(trends["resource"], "Shodan Trends")
        self.assertEqual(trends["date_range_parameter"], "ABSENT")
        self.assertEqual(trends["A2_status"], "FAIL")
        self.assertEqual(trends["A3_status"], "NOT_EXPOSED")
        self.assertFalse(trends["endpoint_executed"])

    def test_an_undocumented_count_unit_cannot_be_a_distinct_ip_count(self) -> None:
        trends = self.package["second_resource_shodan_trends"]
        self.assertEqual(trends["count_unit"], "UNSTATED")
        self.assertIn("DISTINCT IPv4", trends["project_interpretation"])
        self.assertIn("banner counts", trends["project_interpretation"])

    def test_configuration_heterogeneity_is_recorded_rather_than_merged(self) -> None:
        slot = self.package["additional_slots"]["configuration_frame_uniformity"]
        self.assertEqual(slot["status"], "HETEROGENEITY_OBSERVED")
        self.assertEqual(slot["separable"], "UNKNOWN")
        self.assertTrue(any("random port" in q for q in slot["source_says"]))

    def test_internet_wide_coverage_is_not_read_as_a_census(self) -> None:
        frame = self.package["gates"]["A5_FRAME_DOCUMENTED"]
        self.assertEqual(frame["attempted_frame"], "a random sample, by documented design")
        self.assertIn("randomisation rather than enumeration", frame["project_interpretation"])

    def test_a_credential_bearing_endpoint_was_reviewed_and_not_executed(self) -> None:
        review = self.package["metadata_endpoint_safety_review"]
        self.assertEqual(
            review["classification"], "SECRET_BEARING_AND_MEASUREMENT_BEARING_DO_NOT_EXECUTE"
        )
        self.assertFalse(review["executed"])
        self.assertFalse(review["credential_read_to_check"])

    def test_finite_retention_is_not_treated_as_disqualifying(self) -> None:
        slot = self.package["additional_slots"]["retention"]
        self.assertEqual(slot["status"], "PARTIAL")
        self.assertIn("finite retention to pass", slot["project_interpretation"])

    def test_access_requirement_does_not_auto_disqualify(self) -> None:
        self.assertFalse(self.package["additional_slots"]["access"]["used_as_a_disqualifier"])


class Verdicts(unittest.TestCase):
    def test_partial_and_unknown_both_block_qualification(self) -> None:
        vocabulary = _load(QUALIFICATION)["verdict_vocabulary"]
        self.assertTrue(vocabulary["partial_blocks_qualification"])
        self.assertTrue(vocabulary["unknown_blocks_qualification"])
        self.assertTrue(vocabulary["hard_fail_produces_not_qualified"])
        self.assertTrue(vocabulary["qualification_requires_every_mandatory_gate_pass"])

    def test_no_point_score_was_used_anywhere(self) -> None:
        self.assertFalse(_load(QUALIFICATION)["verdict_vocabulary"]["point_score_used"])
        for path in (SONAR, SHODAN):
            self.assertFalse(_load(path)["verdict"]["point_score_used"], path.name)

    def test_a_complete_not_qualified_package_is_a_legitimate_output(self) -> None:
        for path in (SONAR, SHODAN):
            package = _load(path)
            self.assertEqual(package["verdict"]["individual_status"], "INDIVIDUALLY_NOT_QUALIFIED")
            self.assertTrue(package["verdict"]["package_complete"], path.name)

    def test_the_roll_up_agrees_with_the_packages(self) -> None:
        by_name = {p["apparatus"]: p for p in (_load(SONAR), _load(SHODAN))}
        for item in _load(QUALIFICATION)["new_serious_candidates"]:
            package = by_name[item["name"]]
            self.assertEqual(item["individual_status"], package["verdict"]["individual_status"])
            self.assertEqual(item["decisive_fail_gate"], package["verdict"]["decisive_fail_gate"])

    def test_zero_new_apparatuses_qualified(self) -> None:
        counts = _load(QUALIFICATION)["counts"]
        self.assertEqual(counts["new_serious_candidates"], 2)
        self.assertEqual(counts["new_individually_qualified"], 0)
        self.assertEqual(counts["new_individually_not_qualified"], 2)

    def test_the_blocker_distribution_keeps_reach_apart_from_epistemics(self) -> None:
        distribution = _load(QUALIFICATION)["blocker_distribution"]
        self.assertEqual(distribution["observation_addressability"], 1)
        self.assertEqual(distribution["protocol_native_exposure"], 1)
        self.assertEqual(distribution["documentation_retrievability"], 4)
        self.assertIn("this mission's reach", distribution["note_on_documentation"])

    def test_the_primary_outcome_is_the_established_blocker_not_the_largest_group(self) -> None:
        record = _load(QUALIFICATION)
        self.assertEqual(
            record["primary_outcome"],
            "NO_NEW_QUALIFYING_APPARATUS_IDENTIFIED_WITHIN_BOUNDED_SEARCH",
        )
        reasoning = record["primary_outcome_reasoning"]
        self.assertIn("misdescribe", reasoning["why_not_J_documentation_insufficient"])
        self.assertIn(
            "does not mean no qualifying apparatus exists",
            reasoning["what_C_explicitly_does_not_mean"],
        )


class Readiness(unittest.TestCase):
    def test_readiness_counts_and_does_not_select(self) -> None:
        readiness = _load(READINESS)
        self.assertEqual(readiness["qualified_apparatus_count"], 0)
        self.assertFalse(readiness["pair_analysis_ready"])
        self.assertEqual(readiness["pair_analysis_state"], "PAIR_ANALYSIS_NOT_READY")
        for key, value in readiness["no_pair_work_was_performed"].items():
            if key.startswith("$"):
                continue
            self.assertIn(value, (0, False), key)

    def test_all_six_apparatuses_appear(self) -> None:
        readiness = _load(READINESS)
        names = {a["name"] for a in readiness["apparatuses"]}
        self.assertEqual(readiness["total_apparatus_count"], 6)
        for required in (
            "Netlas",
            "ONYPHE",
            "LeakIX",
            "The Shadowserver Foundation",
            "Rapid7 Project Sonar",
            "Shodan",
        ):
            self.assertIn(required, names)

    def test_the_construct_was_not_relaxed_to_admit_a_candidate(self) -> None:
        construct = _load(READINESS)["measurement_construct_unchanged"]
        self.assertEqual(construct["count_unit"], "DISTINCT_IPV4")
        self.assertEqual(construct["authority"], "RFC 4253 §4.2")
        self.assertFalse(construct["relaxed_to_admit_a_candidate"])
        self.assertFalse(construct["substituted_with_a_protocol_label"])
        self.assertFalse(construct["substituted_with_a_vendor_product"])

    def test_a_distinct_ip_count_is_required_and_row_counts_are_forbidden(self) -> None:
        construct = _load(BASELINE)["frozen_construct_unchanged"]
        self.assertEqual(construct["count_unit"], "DISTINCT_IPV4")
        for forbidden in ("ROW_COUNT", "SERVICE_ROW_COUNT", "BANNER_COUNT"):
            self.assertIn(forbidden, construct["count_unit_must_never_be"])


class NothingMoved(unittest.TestCase):
    def test_every_hard_zero_is_zero(self) -> None:
        accounting = _load(QUALIFICATION)["mission_accounting"]
        for counter in (
            "RESEARCH_DATA_REQUESTS",
            "API_EXECUTIONS",
            "MEASUREMENT_API_EXECUTIONS",
            "COUNT_ENDPOINT_EXECUTIONS",
            "TARGET_COUNTS_FETCHED",
            "HOST_RECORDS_FETCHED",
            "HOSTS_FETCHED",
            "BANNERS_FETCHED",
            "FACETS_FETCHED",
            "MEASUREMENT_DOWNLOADS",
            "TRIALS",
            "PURCHASES",
            "ACCOUNTS_CREATED",
            "CREDENTIAL_READS",
            "MAILBOX_SEARCHES",
            "ENQUIRIES_SENT",
            "SOURCES_REGISTERED",
            "GOVERNANCE_REVIEWS",
            "THRESHOLDS_REGISTERED",
            "RELIABILITY_ASSESSMENTS_CREATED",
            "RELIABILITY_VALUES_ASSIGNED",
            "MODEL_CALLS",
            "EMBEDDINGS",
            "MIGRATIONS",
            "PAIRS_SELECTED",
            "PAIRS_RANKED",
        ):
            self.assertEqual(accounting[counter], 0, counter)

    def test_no_reliability_number_is_assigned_to_any_apparatus(self) -> None:
        for path in (SONAR, SHODAN, READINESS):
            for node in _walk(_load(path)):
                if not isinstance(node, dict):
                    continue
                for key, value in node.items():
                    if "reliability" in key.lower():
                        self.assertNotIsInstance(value, (int, float), f"{path.name}: {key}")

    def test_onyphe_was_not_polled_contacted_or_moved(self) -> None:
        parallel = _load(QUALIFICATION)["parallel_state_untouched"]
        self.assertEqual(parallel["onyphe_response_status"], "NOT_CHECKED_AFTER_DISPATCH")
        for key in (
            "onyphe_mailbox_searched",
            "onyphe_gmail_polled",
            "onyphe_reply_read",
            "onyphe_follow_up_sent",
            "onyphe_support_contacted",
            "onyphe_state_changed",
        ):
            self.assertFalse(parallel[key], key)

    def test_a_sent_question_is_still_not_an_answer(self) -> None:
        parallel = _load(QUALIFICATION)["parallel_state_untouched"]
        self.assertIn("improves no gate", parallel["a_sent_question_is_not_an_answer"])

    def test_netlas_was_not_decoded_guessed_or_written_to(self) -> None:
        parallel = _load(QUALIFICATION)["parallel_state_untouched"]
        for key in (
            "netlas_address_decoded",
            "netlas_address_guessed",
            "netlas_enquiry_sent",
            "netlas_state_changed",
        ):
            self.assertFalse(parallel[key], key)

    def test_no_canonical_mutation(self) -> None:
        boundary = _load(QUALIFICATION)["canonical_mutation_boundary"]
        self.assertEqual(boundary["mutations_this_mission"], 0)
        self.assertEqual(boundary["claims"], 44)
        self.assertEqual(boundary["evidence"], 58)
        self.assertEqual(boundary["registered_sources"], 29)
        self.assertEqual(boundary["problem_family"], "PARKED")


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
        recommendation = _load(QUALIFICATION)["recommended_next_mission"]
        self.assertTrue(recommendation["mission_1_68_not_started"])
        self.assertTrue(recommendation["requires_its_own_mission"])
        self.assertEqual(recommendation["do_not"], "rerun the same discovery search")
        self.assertEqual(len(recommendation["the_choice_this_mission_does_not_make"]), 3)


if __name__ == "__main__":
    unittest.main()
