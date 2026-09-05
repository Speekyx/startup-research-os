"""Mission 1.69. Most classes have exactly one party able to produce the quantity.

That is Missions 1.46 and 1.57's law recurring across five domains it had not been tested
in: package registries, code forges, publication registries, procurement publishers and
attention platforms. In each, one party's own records are the origin and every other
publisher is a distribution layer.

The exceptions are three, and they are exactly the classes whose quantity nobody is
positioned to publish authoritatively: what services answer on the internet, what a web
server returns for a defined request, and what a resolver receives for a defined query.
Each must be established by asking, which is the condition Mission 1.58 identified as
making a quantity independently measurable. The first of the three is the scanner class,
already parked for a different reason — it has two producers and no construct they can
both witness.

So the tests here are mostly about a distinction that decides everything: a PRODUCER of
this quantity versus a publisher of somebody's number.

  - an aggregator, a mirror and a publisher of a submitted document are not producers,
    however different their organisations;
  - a route can measure its own events perfectly and still not produce THIS quantity,
    which is why the producer count is over routes that produce the class's own unit —
    a search is not a content request;
  - GitHub and GitLab are different populations, not two routes;
  - a shared domain list is not a shared measurement, because the request is part of the
    predicate;
  - and the scanner arc stays PARKED rather than refuted, because Mission 1.68 declined
    the stronger claim and this mission may not make it on its behalf.

Nothing was crawled, queried, downloaded, registered or measured.
"""

from __future__ import annotations

import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

BASELINE = DATA / "mission-1.69-baseline-v1.json"
UNIVERSE = DATA / "quantity-class-universe-v1.json"
MATRIX = DATA / "quantity-class-route-matrix-v1.json"
LINEAGE = DATA / "independent-measurement-lineage-review-v1.json"
FIXED_CORPUS = DATA / "fixed-corpus-http-class-review-v1.json"
COMPARISON = DATA / "quantity-class-comparison-v1.json"
RULE_REVIEW = DATA / "mission-1-68-candidate-rule-review-v1.json"
DECISION = DATA / "quantity-class-selection-decision-v1.json"
SELECTED = DATA / "selected-quantity-class-v1.json"
CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"
CONSTRUCT_DECISION = DATA / "construct-selection-decision-v1.json"
RENDERER = SCRIPTS / "render_quantity_class_selection.py"

CLASS_IDS = ("Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7")
PACKAGES = {cid: DATA / f"quantity-class-package-{cid.lower()}-v1.json" for cid in CLASS_IDS}

PAGES = (
    DATA / "mission-1.69-quantity-class-selection-v1.md",
    DATA / "fixed-corpus-http-class-review-v1.md",
)


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _producers(package: dict) -> list[dict]:
    return [
        r
        for r in package["routes"]
        if r["production"] == "OWN_MEASUREMENT" and r["produces_the_class_world_state_unit"]
    ]


class Preconditions(unittest.TestCase):
    def test_mission_1_68_is_recorded_as_merged_at_its_commit(self) -> None:
        precondition = _load(BASELINE)["repository_precondition"]
        self.assertTrue(precondition["mission_1_68_merged"])
        self.assertEqual(precondition["pull_request"], 113)
        self.assertEqual(precondition["merge_commit_short"], "ad1175a")
        self.assertTrue(precondition["selected_construct_artifact_absent"])
        self.assertTrue(precondition["verified_from_git_not_from_prompt"])

    def test_the_baseline_is_unchanged(self) -> None:
        baseline = _load(BASELINE)["canonical_baseline"]
        self.assertEqual(baseline["drift_from_mission_1_68"], "none")
        for key, expected in (
            ("raw_records", 325),
            ("normalized_records", 325),
            ("signals", 33),
            ("claims", 44),
            ("claim_revisions", 45),
            ("evidence", 58),
            ("inferred_claims", 1),
            ("reliability_assessments", 4),
            ("evidence_independence_groups", 0),
            ("registered_sources", 29),
        ):
            self.assertEqual(baseline[key], expected, key)
        self.assertEqual(baseline["problem_family"], "PARKED")
        self.assertEqual(baseline["migration_head"], "0035_refusal_provenance")

    def test_the_registry_starts_and_stays_at_fifteen(self) -> None:
        self.assertEqual(len(_load(CONTRACT)["requirement_registry"]["requirements"]), 15)
        registry = _load(BASELINE)["requirement_registry"]
        self.assertEqual(registry["count_before"], 15)
        self.assertEqual(registry["count_after"], 15)
        self.assertIsNone(registry["requirement_added_this_mission"])


class TheScannerArc(unittest.TestCase):
    def test_the_scanner_class_is_parked_not_refuted(self) -> None:
        arc = _load(BASELINE)["scanner_arc_preserved"]
        self.assertEqual(
            arc["scanner_class_result"], "NO_PRODUCT_RELEVANT_CONSTRUCT_WITH_TWO_ROUTES_IDENTIFIED"
        )
        self.assertEqual(arc["status"], "PARKED_BUT_REOPENABLE_ON_NEW_FIRST_PARTY_EVIDENCE")
        for forbidden in (
            "SCANNERS_CANNOT_WORK",
            "SCANNER_CLASS_IMPOSSIBLE",
            "SCANNER_CLASS_INVALID",
        ):
            self.assertNotEqual(arc["scanner_class_result"], forbidden)
            self.assertIn(forbidden, arc["result_is_not"])

    def test_parking_names_how_it_reopens(self) -> None:
        arc = _load(BASELINE)["scanner_arc_preserved"]
        self.assertGreaterEqual(len(arc["reopening_conditions"]), 3)
        joined = " ".join(arc["reopening_conditions"])
        self.assertIn("ONYPHE", joined)
        self.assertIn("Netlas", joined)
        self.assertIn("without producing an application response", joined)

    def test_mission_1_68s_record_was_not_edited(self) -> None:
        previous = _load(CONSTRUCT_DECISION)
        self.assertEqual(
            previous["primary_outcome"], "NO_PRODUCT_RELEVANT_CONSTRUCT_WITH_TWO_ROUTES_IDENTIFIED"
        )
        self.assertIsNone(previous["selected_construct"])
        self.assertEqual(
            _load(BASELINE)["scanner_arc_preserved"]["historical_missions_rewritten"], 0
        )

    def test_only_the_permitted_budget_was_spent_reopening_it(self) -> None:
        budget = _load(UNIVERSE)["budget"]
        self.assertLessEqual(budget["requests_spent_on_Q0"], budget["Q0_request_cap"])
        self.assertEqual(budget["requests_spent_on_Q0"], 0)


class ClassIsNotConstruct(unittest.TestCase):
    def test_a_quantity_class_is_broader_than_a_construct(self) -> None:
        statement = _load(UNIVERSE)["class_is_not_a_construct"]
        self.assertFalse(statement["exact_construct_frozen_this_mission"])
        self.assertIn("broader than a construct", statement["statement"])

    def test_no_package_froze_a_construct(self) -> None:
        for cid, path in PACKAGES.items():
            self.assertFalse(_load(path)["exact_construct_frozen"], cid)

    def test_no_class_was_assessed_with_values_in_hand(self) -> None:
        for cid, path in PACKAGES.items():
            self.assertEqual(_load(path)["values_consulted"], 0, cid)

    def test_structural_viability_is_not_a_selected_class(self) -> None:
        decision = _load(DECISION)
        self.assertEqual(decision["mission_accounting"]["CONSTRUCTS_FROZEN"], 0)
        self.assertEqual(decision["mission_accounting"]["PAIRS_SELECTED"], 0)


class ProducersNotPublishers(unittest.TestCase):
    def test_every_route_says_whether_it_produces_the_class_unit(self) -> None:
        for cid, path in PACKAGES.items():
            for r in _load(path)["routes"]:
                self.assertIn("produces_the_class_world_state_unit", r, f"{cid}/{r['apparatus']}")

    def test_an_aggregator_is_not_an_independent_producer(self) -> None:
        q4 = _load(PACKAGES["Q4"])
        openalex = next(r for r in q4["routes"] if r["apparatus"] == "OpenAlex")
        self.assertEqual(openalex["production"], "AGGREGATOR")
        self.assertFalse(openalex["produces_the_class_world_state_unit"])
        self.assertFalse(q4["independence_plausible"])

    def test_a_mirror_is_not_an_independent_producer(self) -> None:
        q2 = _load(PACKAGES["Q2"])
        mirror = next(r for r in q2["routes"] if r["production"] == "MIRROR")
        self.assertFalse(mirror["produces_the_class_world_state_unit"])
        self.assertFalse(q2["independence_plausible"])

    def test_a_publisher_of_a_submitted_document_is_not_a_producer(self) -> None:
        q5 = _load(PACKAGES["Q5"])
        ted = next(r for r in q5["routes"] if r["apparatus"] == "TED")
        self.assertEqual(ted["production"], "PUBLISHER_OF_SUBMITTED_DOCUMENTS")
        self.assertEqual(_producers(q5), [])

    def test_measuring_a_different_event_is_not_producing_this_quantity(self) -> None:
        # Q6 is the case that made this rule machine-checked. A search engine measures its
        # own searches perfectly and a search is not a content request.
        q6 = _load(PACKAGES["Q6"])
        wikimedia = next(r for r in q6["routes"] if r["apparatus"] == "Wikimedia")
        search = next(r for r in q6["routes"] if "search engine" in r["apparatus"])
        self.assertEqual(wikimedia["production"], "OWN_MEASUREMENT")
        self.assertEqual(search["production"], "OWN_MEASUREMENT")
        self.assertTrue(wikimedia["produces_the_class_world_state_unit"])
        self.assertFalse(search["produces_the_class_world_state_unit"])
        self.assertEqual(len(_producers(q6)), 1)

    def test_a_different_forge_is_a_different_population_not_a_route(self) -> None:
        q3 = _load(PACKAGES["Q3"])
        forge = next(r for r in q3["routes"] if "GitLab" in r["apparatus"])
        self.assertIn("DIFFERENT POPULATION", forge["note"])

    def test_exactly_three_classes_have_two_producers(self) -> None:
        two = [cid for cid, path in PACKAGES.items() if len(_producers(_load(path))) >= 2]
        self.assertEqual(sorted(two), ["Q0", "Q1", "Q7"])
        self.assertEqual(_load(MATRIX)["classes_with_two_own_measurement_routes"], two)

    def test_five_classes_have_one_producer_or_none(self) -> None:
        few = [cid for cid, path in PACKAGES.items() if len(_producers(_load(path))) < 2]
        self.assertEqual(len(few), 5)

    def test_independence_requires_two_producers(self) -> None:
        for cid, path in PACKAGES.items():
            package = _load(path)
            if package["independence_plausible"]:
                self.assertGreaterEqual(len(_producers(package)), 2, cid)


class SameProposition(unittest.TestCase):
    def test_complementary_metrics_do_not_satisfy_the_same_proposition(self) -> None:
        for cid in ("Q2", "Q3", "Q4", "Q5", "Q6"):
            package = _load(PACKAGES[cid])
            self.assertEqual(package["same_proposition"], "NOT_AVAILABLE", cid)
            self.assertTrue(package["same_proposition_reason"].strip(), cid)

    def test_a_shared_proposition_is_never_claimed_without_two_producers(self) -> None:
        for cid, path in PACKAGES.items():
            package = _load(path)
            if package["same_proposition"] in {"ESTABLISHED", "PLAUSIBLE_BUT_NOT_ESTABLISHED"}:
                self.assertGreaterEqual(len(_producers(package)), 2, cid)

    def test_views_are_not_searches(self) -> None:
        reason = _load(PACKAGES["Q6"])["same_proposition_reason"]
        self.assertIn("search volume", reason)
        self.assertIn("not two measurements of one event", reason)

    def test_downloads_are_not_measured_twice(self) -> None:
        reason = _load(PACKAGES["Q2"])["same_proposition_reason"]
        self.assertIn("SOURCE_EXCLUSIVE_METRIC", reason)

    def test_index_diversity_is_not_measurement_independence(self) -> None:
        reason = _load(PACKAGES["Q4"])["same_proposition_reason"]
        self.assertIn("index diversity is not measurement", reason)


class Populations(unittest.TestCase):
    def test_a_provider_defined_population_is_not_externally_frozen(self) -> None:
        for cid in ("Q2", "Q3", "Q6"):
            self.assertEqual(
                _load(PACKAGES[cid])["population_externally_freezable"],
                "PROVIDER_DEFINED_POPULATION",
                cid,
            )

    def test_no_class_claims_a_fully_externally_frozen_population(self) -> None:
        # Nothing in this mission could be pointed at a corpus, so the strong claim is
        # made nowhere.
        for cid, path in PACKAGES.items():
            self.assertNotEqual(
                _load(path)["population_externally_freezable"],
                "POPULATION_EXTERNALLY_FREEZABLE",
                cid,
            )

    def test_temporal_preselection_is_recorded_for_every_class(self) -> None:
        for cid, path in PACKAGES.items():
            self.assertTrue(str(_load(path)["temporal_preselection"]).strip(), cid)


class FixedCorpus(unittest.TestCase):
    def setUp(self) -> None:
        self.review = _load(FIXED_CORPUS)

    def test_both_web_routes_fetch_pages_themselves(self) -> None:
        q1 = _load(PACKAGES["Q1"])
        self.assertEqual(len(_producers(q1)), 2)
        names = {r["apparatus"] for r in _producers(q1)}
        self.assertEqual(names, {"Common Crawl", "HTTP Archive"})

    def test_independence_rests_on_first_party_evidence_from_both_sides(self) -> None:
        for r in _load(PACKAGES["Q1"])["routes"]:
            self.assertTrue(r["source_says"], r["apparatus"])
            self.assertTrue(r["source_says_provenance"], r["apparatus"])

    def test_neither_apparatus_can_be_pointed_at_the_corpus(self) -> None:
        delivered = self.review["what_was_delivered"]
        self.assertFalse(delivered["apparatus_directable_at_C"])
        self.assertTrue(delivered["apparatus_directable_at_C_reason"].strip())

    def test_the_sampling_sentence_is_quoted_verbatim(self) -> None:
        finding = self.review["the_load_bearing_finding"]
        self.assertIn("sample of the web", finding["source_says"])
        self.assertIn("randomly selected subset", finding["source_says"])
        self.assertIn("commoncrawl.org/faq", finding["source_says_provenance"])

    def test_a_fixed_corpus_alone_does_not_establish_the_same_request_semantics(self) -> None:
        differences = self.review["request_semantics"][
            "differences_that_would_have_to_be_reconciled"
        ]
        self.assertGreaterEqual(len(differences), 4)
        joined = " ".join(differences).lower()
        for topic in ("user agent", "vantage", "redirect", "url identity"):
            self.assertIn(topic, joined)

    def test_the_operator_route_is_documentation_only(self) -> None:
        operator = self.review["operator_route"]
        self.assertFalse(operator["crawled"])
        self.assertFalse(operator["implemented"])
        self.assertTrue(operator["not_automatically_independent"])
        self.assertGreaterEqual(len(operator["safeguards_it_would_require"]), 4)
        self.assertIn("SUBSTANTIAL", operator["governance_complexity"])

    def test_the_review_and_the_package_agree(self) -> None:
        self.assertEqual(self.review["verdict"], _load(PACKAGES["Q1"])["class_verdict"])
        self.assertEqual(self.review["verdict"], "PROMISING_REQUIRES_ROUTE_QUALIFICATION")


class Selection(unittest.TestCase):
    def test_nothing_was_selected_and_no_artifact_exists(self) -> None:
        decision = _load(DECISION)
        self.assertIsNone(decision["selected_quantity_class"])
        self.assertEqual(decision["selection_outcome"], "NO_SELECTION")
        self.assertFalse(decision["selected_class_artifact_created"])
        self.assertFalse(SELECTED.exists())

    def test_no_class_is_strategically_viable(self) -> None:
        decision = _load(DECISION)
        self.assertEqual(decision["strategically_viable_count"], 0)
        for cid, path in PACKAGES.items():
            self.assertNotEqual(_load(path)["class_verdict"], "STRATEGICALLY_VIABLE", cid)

    def test_the_outcome_names_the_one_open_question(self) -> None:
        decision = _load(DECISION)
        self.assertEqual(
            decision["primary_outcome"],
            "FIXED_CORPUS_WEB_MEASUREMENT_PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED",
        )
        closest = decision["the_class_that_came_closest"]
        self.assertEqual(closest["class_id"], "Q1")
        self.assertTrue(closest["one_load_bearing_question"].strip())
        self.assertIn(
            "intersected with two independently determined coverages",
            closest["one_load_bearing_question"],
        )

    def test_the_none_identified_outcome_was_refused_for_a_stated_reason(self) -> None:
        reasoning = _load(DECISION)["primary_outcome_reasoning"]
        self.assertIn("HAS two credible independent routes", reasoning["why_not_H_none_identified"])

    def test_no_weighted_score_and_the_tie_break_was_not_reached(self) -> None:
        method = _load(COMPARISON)["scoring_method"]
        self.assertFalse(method["weighted_numeric_score_used"])
        self.assertFalse(method["tie_break_reached"])
        self.assertFalse(method["q1_tie_break_preference_not_exercised"]["used"])

    def test_complementary_value_is_recorded_apart_from_experiment_suitability(self) -> None:
        separation = _load(COMPARISON)["the_separation_that_matters"]
        self.assertEqual(len(separation["useful_complementary_signal"]), 8)
        self.assertEqual(separation["suitable_for_the_independence_experiment"], [])
        self.assertIn("different questions", separation["statement"])

    def test_a_ninth_class_was_not_invented(self) -> None:
        classes = _load(UNIVERSE)["classes"]
        q8 = next(c for c in classes if c["id"] == "Q8")
        self.assertEqual(q8["role"], "NOT_PROPOSED")
        self.assertIn("manufacturing a candidate", q8["why"])

    def test_the_class_budget_was_respected(self) -> None:
        budget = _load(UNIVERSE)["budget"]
        self.assertLessEqual(budget["serious_classes"], budget["maximum_serious_classes"])
        self.assertGreaterEqual(
            budget["serious_classes"], budget["minimum_meaningful_classes_required"]
        )
        self.assertLessEqual(budget["used"], budget["maximum_first_party_requests"])


class TheCandidateRule(unittest.TestCase):
    def test_the_mission_1_68_rule_was_reviewed_and_not_adopted(self) -> None:
        review = _load(RULE_REVIEW)
        self.assertEqual(review["decision"], "DO_NOT_ADOPT")
        self.assertEqual(review["registry_count_after"], 15)
        self.assertIsNone(review["requirement_added"])
        self.assertFalse(review["registry_growth_forced"])

    def test_second_instances_were_examined_and_each_was_rejected_with_a_reason(self) -> None:
        review = _load(RULE_REVIEW)
        self.assertGreaterEqual(len(review["candidate_second_instances_examined"]), 3)
        for candidate in review["candidate_second_instances_examined"]:
            self.assertEqual(candidate["verdict"], "NOT_A_SECOND_INSTANCE")
            self.assertTrue(candidate["why"].strip())

    def test_the_standard_applied_is_the_one_mission_1_67_set(self) -> None:
        standard = _load(RULE_REVIEW)["the_standard_applied"]
        self.assertIn("second independent instance", standard)
        self.assertIn("DIFFERENT SHAPE", standard)

    def test_the_declined_rule_is_absent_from_the_registry(self) -> None:
        names = {r["name"] for r in _load(CONTRACT)["requirement_registry"]["requirements"]}
        self.assertNotIn(_load(RULE_REVIEW)["candidate_requirement"]["name"], names)


class NothingMoved(unittest.TestCase):
    def test_every_hard_zero_is_zero(self) -> None:
        accounting = _load(DECISION)["mission_accounting"]
        for counter in (
            "MEASUREMENT_API_EXECUTIONS",
            "DATASET_DOWNLOADS",
            "BIGQUERY_EXECUTIONS",
            "CRAWLS",
            "HTTP_MEASUREMENT_REQUESTS",
            "PACKAGE_COUNT_QUERIES",
            "REPOSITORY_EVENT_QUERIES",
            "PUBLICATION_COUNT_QUERIES",
            "PROCUREMENT_VALUE_QUERIES",
            "SEARCH_TREND_QUERIES",
            "DNS_MEASUREMENT_QUERIES",
            "VALUES_RETRIEVED",
            "TRIALS",
            "ACCOUNTS_CREATED",
            "CREDENTIAL_READS",
            "MAILBOX_SEARCHES",
            "ENQUIRIES_SENT",
            "SOURCES_REGISTERED",
            "GOVERNANCE_MUTATIONS",
            "SOURCE_REVIEWS_MUTATED",
            "THRESHOLDS_REGISTERED",
            "CLAIMS_CREATED",
            "EVIDENCE_CREATED",
            "RELIABILITY_VALUES_ASSIGNED",
            "SCORES",
            "MODEL_CALLS",
            "EMBEDDINGS",
            "MIGRATIONS",
        ):
            self.assertEqual(accounting[counter], 0, counter)

    def test_no_source_was_registered_or_reviewed(self) -> None:
        reuse = _load(UNIVERSE)["held_evidence_reused"]
        self.assertEqual(reuse["sources_registered"], 0)
        self.assertEqual(reuse["source_reviews_mutated"], 0)
        self.assertGreaterEqual(len(reuse["facts_taken_from_repository_records"]), 6)

    def test_onyphe_and_netlas_were_not_touched(self) -> None:
        parallel = _load(DECISION)["parallel_state_untouched"]
        self.assertEqual(parallel["onyphe_response_status"], "NOT_CHECKED_AFTER_DISPATCH")
        for key in (
            "onyphe_mailbox_searched",
            "onyphe_gmail_polled",
            "onyphe_reply_read",
            "onyphe_follow_up_sent",
            "onyphe_state_changed",
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
        self.assertEqual(boundary["problem_family"], "PARKED")

    def test_no_reliability_number_appears_in_any_class_record(self) -> None:
        for cid, path in PACKAGES.items():
            blob = json.dumps(_load(path))
            for fragment in blob.split(","):
                if "reliability" in fragment.lower():
                    self.assertNotRegex(fragment, r"reliability\S*\"\s*:\s*[0-9]", cid)

    def test_the_universe_does_not_claim_to_be_exhaustive(self) -> None:
        exhaustiveness = _load(UNIVERSE)["exhaustiveness"]
        self.assertFalse(exhaustiveness["claimed"])
        self.assertIn("does not establish that none exists", exhaustiveness["statement"])


class GeneratedPages(unittest.TestCase):
    def test_the_renderer_exists_and_the_pages_are_present(self) -> None:
        self.assertTrue(RENDERER.exists())
        for page in PAGES:
            self.assertTrue(page.exists(), page.name)
            self.assertGreater(len(page.read_text(encoding="utf-8")), 500, page.name)

    def test_the_renderer_reaches_no_network_and_no_database(self) -> None:
        source = RENDERER.read_text(encoding="utf-8")
        for forbidden in ("requests", "urllib", "httpx", "socket", "psycopg"):
            self.assertNotIn(f"import {forbidden}", source)

    def test_the_next_mission_is_scoped_and_not_started(self) -> None:
        recommendation = _load(DECISION)["recommended_next_mission"]
        self.assertTrue(recommendation["mission_1_70_not_started"])
        self.assertIn("Fixed-Corpus Web Route Qualification", recommendation["recommended"])
        self.assertEqual(recommendation["do_not"], "restart broad quantity-class discovery")
        self.assertTrue(recommendation["the_question_it_must_answer_first"].strip())


if __name__ == "__main__":
    unittest.main()
