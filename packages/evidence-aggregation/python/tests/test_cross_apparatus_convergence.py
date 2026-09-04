"""Mission 1.47 §35. Cross-apparatus convergence, and the shapes it is not.

The failure this guards is more seductive than Mission 1.46's. There the trap
was two publishers of ONE number looking like two witnesses. Here the trap is
two genuinely different apparatuses looking like corroboration when they are
answering different questions -- and the tempting sentence writes itself:
*people are reading about Docker AND asking about Docker, so two independent
lines of evidence agree.* Neither half of that supports the whole of it.

**Non-empty fixtures for all five shapes §35 names**, so every branch actually
executes rather than being asserted about:

    VALID_SAME_PROPOSITION_INDEPENDENT
    COMPLEMENTARY_ONLY
    LATENT_INFERENCE_REQUIRED
    JOINT_CONJUNCTION_NOT_CORROBORATION
    UNKNOWN_INDEPENDENCE

That requirement is not decoration. Missions 1.36.1, 1.42.1, 1.43 and 1.44 each
shipped a branch no data had ever entered, and each was found by real data
rather than by a passing suite.

Nothing here persists a row. `unittest`, not pytest: `run_python_tests.py`
discovers this package, and a pytest-style function here would be collected as
zero tests, silently.
"""

from __future__ import annotations

import json
import pathlib
import unittest

from sros_contracts import EvidenceDirection, EvidenceIndependenceState
from sros_evidence_aggregation.independence import group_by_independence
from sros_evidence_aggregation.items import EvidenceItem, ItemContribution

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
FEASIBILITY = DOCS / "cross-apparatus-convergence-feasibility-v1.json"
HOLDINGS = DOCS / "cross-apparatus-holdings-baseline-v1.json"
REGISTRY = DOCS / "canonical-subject-registry-v1.json"


def record() -> dict:
    return json.loads(FEASIBILITY.read_text(encoding="utf-8"))


def holdings() -> dict:
    return json.loads(HOLDINGS.read_text(encoding="utf-8"))


def registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def candidate(candidate_id: str) -> dict:
    return next(c for c in record()["candidate_propositions"] if c["id"] == candidate_id)


def entailment(candidate_id: str) -> dict:
    return next(r for r in record()["entailment_table"] if r["candidate"] == candidate_id)


def item(
    evidence_id: str,
    state: EvidenceIndependenceState,
    group: str | None = None,
    reliability: float = 0.6,
):
    """One scorable supporting item, shaped like a real Evidence row."""
    return EvidenceItem(
        evidence_id=evidence_id,
        direction=EvidenceDirection.SUPPORTS,
        relevance=1.0,
        directness=1.0,
        reliability=reliability,
        extraction_confidence=1.0,
        independence_state=state,
        independence_group_id=group,
        observed_at=None,
    )


def contributions(*items) -> dict[str, ItemContribution]:
    return {
        element.evidence_id: ItemContribution(
            evidence_id=element.evidence_id,
            direction=element.direction,
            components={
                "relevance": element.relevance,
                "directness": element.directness,
                "reliability": element.reliability,
                "extraction_confidence": element.extraction_confidence,
                "freshness": 1.0,
            },
            scorable=True,
            q=element.reliability,
            limiting_component="reliability",
        )
        for element in items
    }


def groups(*items):
    return group_by_independence(items, contributions(*items), EvidenceDirection.SUPPORTS)


# ============================================ §0 — the inventory exists and is counted


class ApparatusInventory(unittest.TestCase):
    def test_inventory_is_non_empty(self):
        self.assertTrue(holdings()["apparatus_inventory"])

    def test_an_apparatus_is_source_crossed_with_proposition_kind_not_a_source(self):
        """Four sources, nine apparatuses. Counting sources would merge two
        reliability scopes the contract already holds apart."""
        inventory = holdings()["apparatus_inventory"]
        sources = {row["source_id"] for row in inventory}
        apparatuses = {(row["source_id"], row["proposition_kind"]) for row in inventory}
        self.assertLess(len(sources), len(apparatuses))

    def test_two_sources_operate_more_than_one_apparatus_each(self):
        inventory = holdings()["apparatus_inventory"]
        per_source: dict[str, int] = {}
        for row in inventory:
            per_source[row["source_id"]] = per_source.get(row["source_id"], 0) + 1
        multi = {source for source, count in per_source.items() if count > 1}
        self.assertIn("wikimedia-pageviews", multi)
        self.assertIn("ted-eu", multi)

    def test_every_apparatus_carries_evidence_or_is_not_an_apparatus(self):
        for row in holdings()["apparatus_inventory"]:
            with self.subTest(apparatus=row["proposition_kind"]):
                self.assertGreater(row["evidence"], 0)


# ============================================ §2 — overlap uses canonical identity only


class SubjectOverlapUsesCanonicalIdentity(unittest.TestCase):
    def test_overlap_is_computed_from_the_reviewed_registry(self):
        registered = {subject["subject_id"] for subject in registry()["subjects"]}
        measured = {row["subject_id"] for row in holdings()["cross_apparatus_subject_overlap"]}
        self.assertEqual(registered, measured)

    def test_a_mapped_identifier_with_no_evidence_is_not_a_cross_apparatus_subject(self):
        """kubernetes and podman are mapped and unusable. The registry says so
        itself, and the measurement agrees rather than being told."""
        overlap = {row["subject_id"]: row for row in holdings()["cross_apparatus_subject_overlap"]}
        for subject_id in ("kubernetes", "podman"):
            with self.subTest(subject=subject_id):
                self.assertFalse(overlap[subject_id]["cross_apparatus_evidence_available"])
                sides = {
                    side["source_id"]: side["evidence"] for side in overlap[subject_id]["sides"]
                }
                self.assertEqual(sides["stack-exchange"], 0)

    def test_docker_is_the_only_cross_apparatus_subject(self):
        available = [
            row["subject_id"]
            for row in holdings()["cross_apparatus_subject_overlap"]
            if row["cross_apparatus_evidence_available"]
        ]
        self.assertEqual(available, ["docker"])

    def test_the_record_reports_that_as_measured_rather_than_assumed(self):
        self.assertFalse(
            record()["subject_overlap"]["pre_selection_refused"].startswith(
                "Wikimedia + Stack Exchange WAS"
            )
        )
        self.assertIn("NOT", record()["subject_overlap"]["pre_selection_refused"])


# ================================ shared subject != same proposition, apparatus != proposition


class SharedSubjectIsNotSameProposition(unittest.TestCase):
    def test_docker_is_one_subject_and_more_than_one_proposition_kind(self):
        inventory = holdings()["apparatus_inventory"]
        docker_kinds = {
            row["proposition_kind"]
            for row in inventory
            if row["source_id"] in ("wikimedia-pageviews", "stack-exchange")
        }
        self.assertGreater(len(docker_kinds), 1)

    def test_a_strengthened_proposition_over_the_shared_subject_is_refused(self):
        """P-A2 is the first strengthening that would carry information, and it
        is exactly where the shared subject stops being a shared proposition."""
        self.assertEqual(candidate("P-A2")["verdict"], "SHARED_SUBJECT_NOT_SAME_PROPOSITION")

    def test_different_apparatus_does_not_imply_same_proposition(self):
        row = entailment("P-A2")
        self.assertEqual(row["a_alone_entails_full_claim"], "NO")
        self.assertEqual(row["b_alone_entails_full_claim"], "NO")


# ============================================ §4/§8 — each Evidence must support the FULL claim


class EachEvidenceMustSupportTheFullClaim(unittest.TestCase):
    def test_the_only_standard_corroboration_candidate_satisfies_the_full_conjunction(self):
        row = entailment("P-A1")
        self.assertEqual(row["a_alone_entails_full_claim"], "YES")
        self.assertEqual(row["b_alone_entails_full_claim"], "YES")
        self.assertEqual(row["requires_both_jointly"], "NO")
        self.assertEqual(row["requires_latent_inference"], "NO")

    def test_no_candidate_failing_the_conjunction_is_recorded_as_corroboration(self):
        for row in record()["entailment_table"]:
            qualifies = (
                row["a_alone_entails_full_claim"] == "YES"
                and row["b_alone_entails_full_claim"] == "YES"
                and row["requires_both_jointly"] == "NO"
                and row["requires_latent_inference"] == "NO"
            )
            with self.subTest(candidate=row["candidate"]):
                if not qualifies:
                    self.assertEqual(
                        row["standard_two_group_corroboration"],
                        "NO",
                        "a candidate that fails the §8 conjunction was recorded as "
                        "standard two-group corroboration",
                    )


class JointConjunctionIsNotCorroboration(unittest.TestCase):
    """JOINT_CONJUNCTION_NOT_CORROBORATION, on a non-empty fixture."""

    def test_the_cross_platform_existence_claim_is_classified_as_joint(self):
        self.assertEqual(candidate("P-B1")["verdict"], "JOINT_CONJUNCTION_NOT_CORROBORATION")

    def test_neither_witness_alone_entails_the_two_platform_claim(self):
        row = entailment("P-B1")
        self.assertEqual(row["a_alone_entails_full_claim"], "NO")
        self.assertEqual(row["b_alone_entails_full_claim"], "NO")
        self.assertEqual(row["requires_both_jointly"], "YES")

    def test_a_joint_claim_is_not_offered_as_two_support_groups(self):
        self.assertEqual(entailment("P-B1")["standard_two_group_corroboration"], "NO")

    def test_but_the_grouping_machinery_would_happily_have_made_two(self):
        """The point of the classification. `group_by_independence` groups by
        provenance and has never heard of the Claim, so it cannot refuse a
        conjunction -- which is why the refusal has to happen upstream, in the
        proposition semantics, and why §12 orders the gates that way."""
        result = groups(
            item("wikimedia", EvidenceIndependenceState.KNOWN_INDEPENDENT),
            item("stack_exchange", EvidenceIndependenceState.KNOWN_INDEPENDENT),
        )
        self.assertEqual(len(result), 2)


# ============================================ §14 — complementary is not corroborating


class ComplementaryIsNotCorroborating(unittest.TestCase):
    """COMPLEMENTARY_ONLY, on a non-empty fixture."""

    def test_the_two_apparatuses_share_no_opportunity_dimension(self):
        analysis = record()["complementarity_analysis"]
        self.assertEqual(analysis["dimension_overlap"], [])
        self.assertNotEqual(
            set(analysis["wikimedia_dimensions"]) & set(analysis["stack_exchange_dimensions"]),
            set(analysis["wikimedia_dimensions"]),
        )

    def test_audience_and_problem_were_not_collapsed_into_a_shared_category(self):
        analysis = record()["complementarity_analysis"]
        self.assertIn("AUDIENCE_OR_USAGE", analysis["wikimedia_dimensions"])
        self.assertIn("PROBLEM_OR_NEED", analysis["stack_exchange_dimensions"])
        self.assertNotIn("PROBLEM_OR_NEED", analysis["wikimedia_dimensions"])
        self.assertNotIn("AUDIENCE_OR_USAGE", analysis["stack_exchange_dimensions"])

    def test_complementarity_and_corroboration_are_defined_separately(self):
        analysis = record()["complementarity_analysis"]
        self.assertNotEqual(
            analysis["corroborating_definition"], analysis["complementary_definition"]
        )

    def test_complementarity_is_recorded_as_a_finding_not_as_the_route(self):
        codes = {finding["code"] for finding in record()["secondary_findings"]}
        self.assertIn("CROSS_APPARATUS_EVIDENCE_IS_COMPLEMENTARY_NOT_CORROBORATING", codes)
        self.assertIsNone(record()["selected_route"])


# ============================================ §6/§17 — no latent promotion, no human promotion


class LatentConstructsCannotBecomeObserved(unittest.TestCase):
    """LATENT_INFERENCE_REQUIRED, on a non-empty fixture."""

    LATENT = ("interest", "demand", "adoption", "popularity", "pain", "willingness to pay")

    def test_the_latent_candidate_is_recorded_and_refused(self):
        self.assertEqual(candidate("P-C1")["formal_validity"], "NOT_OBSERVED")
        self.assertEqual(candidate("P-C1")["verdict"], "LATENT_INFERENCE_REQUIRED")

    def test_no_candidate_offered_as_observed_contains_a_latent_construct(self):
        """Scanned in the ASSERTION position only. A candidate recorded in order
        to be REFUSED may name the construct it is refused for -- P-C1's whole
        point is that it says the word -- and a scan that could not tell those
        apart would forbid recording the refusal. `testing-strategy.md` §23."""
        for proposition in record()["candidate_propositions"]:
            if proposition["formal_validity"] != "VALID":
                continue
            statement = proposition["statement"].lower()
            for term in self.LATENT:
                with self.subTest(candidate=proposition["id"], term=term):
                    self.assertNotIn(term, statement)

    def test_the_refused_latent_candidate_really_does_name_one(self):
        """Otherwise the test above passes vacuously and proves nothing."""
        statement = candidate("P-C1")["statement"].lower()
        self.assertTrue(any(term in statement for term in self.LATENT))

    def test_no_inferred_bridge_was_implemented(self):
        self.assertNotEqual(
            record()["primary_outcome"], "CROSS_APPARATUS_CONVERGENCE_REQUIRES_INFERRED_BRIDGE"
        )
        self.assertIn("not proposed", candidate("P-C1")["why"])


class SourceSemanticsArePreserved(unittest.TestCase):
    def test_requester_class_user_is_not_translated_to_human(self):
        diagnostic = record()["section_16_diagnostic"]
        self.assertEqual(diagnostic["wikimedia_requester_class"], "user")
        humans = next(q for q in diagnostic["questions"] if q["n"] == 7)
        self.assertEqual(humans["answer"], "NO")
        self.assertIn("does not mean human", humans["note"])

    def test_question_count_is_not_translated_to_unique_people(self):
        note = next(q for q in record()["section_16_diagnostic"]["questions"] if q["n"] == 7)[
            "note"
        ]
        self.assertIn("not one unique person", note)
        self.assertIn("author identity was never acquired", note)

    def test_no_candidate_statement_claims_people_viewed_or_experienced(self):
        for proposition in record()["candidate_propositions"]:
            if proposition["formal_validity"] != "VALID":
                continue
            statement = proposition["statement"].lower()
            for phrase in ("people viewed", "users experienced", "developers", "customers"):
                with self.subTest(candidate=proposition["id"], phrase=phrase):
                    self.assertNotIn(phrase, statement)


# ============================================ §10/§11 — time grain and unlike quantities


class IncompatibleTimeGrainsAreRejected(unittest.TestCase):
    def test_the_windows_are_recorded_as_not_aligned(self):
        self.assertFalse(record()["time_overlap"]["aligned"])

    def test_the_stack_exchange_window_is_not_day_aligned(self):
        """The measured fact the alignment verdict rests on."""
        time = record()["time_overlap"]["stack_exchange"]
        self.assertIn("08:06:03", time["held_tag"])
        self.assertIn("04:17:20", time["held_tag"])

    def test_containment_is_not_recorded_as_alignment(self):
        """The two are distinguished in the record rather than conflated: the
        containment note must concede that containment is the weaker relation."""
        time = record()["time_overlap"]
        self.assertFalse(time["aligned"])
        self.assertIn("weaker than alignment", time["containment"])

    def test_the_strengthened_candidate_fails_the_time_gate(self):
        row = next(r for r in record()["decision_matrix"] if r["candidate"] == "P-A2")
        self.assertEqual(row["TIME_MATCH"], "NO")

    def test_no_monthly_aggregate_was_manufactured(self):
        aggregation = record()["deterministic_temporary_aggregation"]
        self.assertFalse(aggregation["available"])
        self.assertFalse(aggregation["needed"])
        self.assertIn("7 of 31", aggregation["available_reason"])


class UnlikeQuantitiesAreNeverNormalised(unittest.TestCase):
    def test_the_candidate_requiring_a_shared_metric_is_refused(self):
        self.assertEqual(candidate("P-A2")["formal_validity"], "INVALID")
        self.assertIn("pseudo-metric", candidate("P-A2")["why"])

    def test_no_candidate_statement_compares_the_two_magnitudes(self):
        for proposition in record()["candidate_propositions"]:
            if proposition["formal_validity"] != "VALID":
                continue
            statement = proposition["statement"]
            self.assertNotIn("88", statement)
            self.assertNotIn("per", statement.lower().split())

    def test_the_valid_candidate_is_existential_rather_than_quantitative(self):
        self.assertIn("At least one", candidate("P-A1")["statement"])


# ============================================ §12/§13 — independence


class DifferentPublisherIsNotIndependence(unittest.TestCase):
    """UNKNOWN_INDEPENDENCE, on a non-empty fixture."""

    def test_independence_is_unknown_not_known_independent(self):
        self.assertEqual(record()["independence_analysis"]["state"], "UNKNOWN")

    def test_two_different_publishers_did_not_produce_established_independence(self):
        analysis = record()["independence_analysis"]
        self.assertNotEqual(analysis["publisher_a"], analysis["publisher_b"])
        self.assertEqual(analysis["state"], "UNKNOWN")

    def test_absence_of_a_found_dependency_was_not_converted_into_independence(self):
        analysis = record()["independence_analysis"]
        self.assertFalse(analysis["shared_upstream_documented"])
        self.assertFalse(analysis["republished_values"])
        self.assertEqual(analysis["state"], "UNKNOWN")

    def test_the_justification_names_the_missing_documentation(self):
        justification = record()["independence_analysis"]["state_justification"]
        self.assertIn("documentary", justification)
        self.assertIn("robots", justification)

    def test_unknown_items_collapse_into_one_group(self):
        """What the real corpus would do today, exercised rather than asserted."""
        result = groups(
            item("wikimedia", EvidenceIndependenceState.UNKNOWN),
            item("stack_exchange", EvidenceIndependenceState.UNKNOWN),
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].member_evidence_ids), 2)

    def test_unknown_remains_unknown_and_is_never_promoted(self):
        result = groups(
            item("a", EvidenceIndependenceState.UNKNOWN),
            item("b", EvidenceIndependenceState.UNKNOWN),
            item("c", EvidenceIndependenceState.UNKNOWN),
        )
        self.assertEqual(len(result), 1, "three unknown items must not become three groups")

    def test_this_is_not_refuted_independence_which_is_a_different_state(self):
        """Mission 1.46 REFUTED independence on a documented common upstream.
        Conflating that with UNKNOWN would close a direction that is still open."""
        analysis = record()["independence_analysis"]
        self.assertIn("Mission 1.46", analysis["not_refuted"])
        self.assertFalse(analysis["shared_upstream_documented"])


class ValidIndependenceRequiresDocumentedLineages(unittest.TestCase):
    """VALID_SAME_PROPOSITION_INDEPENDENT, on a non-empty fixture. The shape the
    model can hold, and which no real pair in this corpus is entitled to."""

    def test_two_known_independent_items_form_two_groups(self):
        result = groups(
            item("a", EvidenceIndependenceState.KNOWN_INDEPENDENT),
            item("b", EvidenceIndependenceState.KNOWN_INDEPENDENT),
        )
        self.assertEqual(len(result), 2)

    def test_saturation_over_two_groups_can_exceed_the_pass_through_baseline(self):
        result = groups(
            item("a", EvidenceIndependenceState.KNOWN_INDEPENDENT, reliability=0.6),
            item("b", EvidenceIndependenceState.KNOWN_INDEPENDENT, reliability=0.5),
        )
        strengths = [group.strength for group in result]
        saturation = 1.0
        for strength in strengths:
            saturation *= 1.0 - strength
        saturation = 1.0 - saturation
        self.assertGreater(saturation, max(strengths))

    def test_the_record_does_not_claim_a_real_pair_reaches_this(self):
        aggregation = record()["hypothetical_aggregation"]
        self.assertFalse(aggregation["persisted"])
        self.assertIn("g_A = r_A", aggregation["group_a"]["strength"])
        self.assertIn("does not contain one", aggregation["what_this_shows"])

    def test_no_reliability_number_was_fabricated_for_the_symbolic_fixture(self):
        aggregation = json.dumps(record()["hypothetical_aggregation"])
        self.assertIn("symbolic", aggregation)
        self.assertNotIn("0.65", aggregation)
        self.assertNotIn("0.55", aggregation)


# ============================================ §9/§18/§19 — the convergence contract


class SourceIdentityIsNotDroppedWithoutAContract(unittest.TestCase):
    """Gate 7 itself is proved against the REAL constructor in
    `packages/claim-model/python/tests/test_cross_apparatus_contract_boundary.py`,
    because that is the package owning `PropositionConvergenceContract` and the
    zero-dependency runner puts only a suite's own package on its path. What is
    asserted here is that this record REPORTS the refusal, and reports what the
    refusal cost."""

    def test_the_record_reports_the_contract_cannot_express_it(self):
        capability = record()["convergence_contract_capability"]
        self.assertEqual(capability["answer"], "NO")
        self.assertEqual(len(capability["refusals"]), 2)

    def test_source_attribution_was_not_removed_to_permit_a_merge(self):
        row = entailment("P-A1")
        self.assertNotEqual(row["source_identity_improperly_removed"], "YES")

    def test_the_relocation_of_attribution_is_recorded_rather_than_hidden(self):
        """The finding: the proposition's subject is source-independent and its
        predicate is not, because the event class enumerates both mechanisms."""
        note = entailment("P-A1")["source_identity_note"]
        self.assertIn("relocated", note)
        self.assertIn("predicate", note)


class IdentityAndWitnessCoverageRemainsComplete(unittest.TestCase):
    def test_the_proposed_field_split_is_disjoint(self):
        fields = record()["proposed_identity_and_witness_fields"]
        self.assertFalse(set(fields["identity_fields"]) & set(fields["witness_fields"]))
        self.assertTrue(fields["disjoint"])

    def test_the_proposed_split_is_recorded_as_incomplete_and_rejected(self):
        fields = record()["proposed_identity_and_witness_fields"]
        self.assertFalse(fields["complete"])
        self.assertTrue(fields["verdict"].startswith("REJECTED"))

    def test_the_incompleteness_names_the_fact_that_cannot_be_demoted(self):
        fields = record()["proposed_identity_and_witness_fields"]
        self.assertIn("audience_class", fields["complete_failure"])


# ============================================ §21 — no reliability inheritance


class NoReliabilityInheritanceByPropositionSimilarity(unittest.TestCase):
    def test_a_new_proposition_kind_is_a_new_scope_on_both_sides(self):
        consequence = record()["reliability_consequence"]
        self.assertTrue(consequence["both_sides_would_need_review"])
        self.assertIn("NEW proposition_kind", consequence["new_proposition_kind_is_new_scope"])

    def test_no_existing_wikimedia_value_is_carried_into_the_candidate(self):
        consequence = record()["reliability_consequence"]["new_proposition_kind_is_new_scope"]
        self.assertIn("Neither", consequence)
        self.assertIn("transfers", consequence)

    def test_stack_exchange_scopes_resolve_to_no_applicable_assessment(self):
        readiness = {row["apparatus"]: row for row in record()["reliability_readiness"]}
        for apparatus, row in readiness.items():
            if apparatus.startswith("stack-exchange"):
                with self.subTest(apparatus=apparatus):
                    self.assertEqual(row["current_scope_resolves"], "NO_APPLICABLE_ASSESSMENT")
                    self.assertIsNone(row["value"])

    def test_every_resolved_row_names_a_human_review_origin(self):
        for row in record()["reliability_readiness"]:
            with self.subTest(apparatus=row["apparatus"]):
                if row["current_scope_resolves"] == "RESOLVED":
                    self.assertEqual(row["origin"], "HUMAN_REVIEW")
                    self.assertIsNotNone(row["value"])

    def test_no_assessment_was_created_by_this_mission(self):
        counters = record()["counters"]["reliability_assessments"]
        self.assertEqual(counters["before"], counters["after"])


# ============================================ §22/§26 — the gates and the decision


class GatesAndDecision(unittest.TestCase):
    def test_all_eight_gates_are_evaluated(self):
        self.assertEqual(len(record()["gate_evaluation"]["gates"]), 8)

    def test_the_outcome_was_not_forced_to_feasible(self):
        gates = record()["gate_evaluation"]
        self.assertFalse(gates["all_eight"])
        self.assertNotEqual(
            record()["primary_outcome"], "CROSS_APPARATUS_OBSERVED_CONVERGENCE_FEASIBLE"
        )

    def test_no_route_was_selected(self):
        self.assertIsNone(record()["selected_route"])

    def test_no_least_bad_fallback_was_taken(self):
        self.assertIn("least-bad", record()["selected_route_reason"])

    def test_structural_identification_and_semantic_usefulness_are_reported_apart(self):
        calibration = record()["calibration_information_value"]
        self.assertEqual(calibration["structurally_identifying"], "YES")
        self.assertEqual(calibration["semantically_useful"], "NO")

    def test_exactly_one_primary_outcome(self):
        self.assertIsInstance(record()["primary_outcome"], str)


# ============================================ §28-§32 — nothing moved


class NothingMoved(unittest.TestCase):
    def test_no_research_data_was_acquired(self):
        self.assertEqual(record()["network_budget"]["RESEARCH_DATA_REQUESTS"], 0)

    def test_no_canonical_research_row_changed(self):
        for name, pair in record()["counters"].items():
            if not isinstance(pair, dict):
                continue
            with self.subTest(counter=name):
                self.assertEqual(pair["before"], pair["after"])

    def test_no_independence_group_was_persisted(self):
        groups_counter = record()["counters"]["independence_groups"]
        self.assertEqual(groups_counter["before"], 0)
        self.assertEqual(groups_counter["after"], 0)

    def test_no_score_exists(self):
        scores = record()["counters"]["scores"]
        self.assertEqual(scores["before"], "table absent")
        self.assertEqual(scores["after"], "table absent")

    def test_no_opportunity_change(self):
        counters = record()["counters"]
        self.assertEqual(counters["opportunities"]["after"], 1)
        self.assertEqual(counters["opportunity_revisions"]["after"], 1)
        self.assertEqual(counters["opportunity_evidence_links"]["after"], 7)

    def test_no_model_call_and_no_embedding(self):
        model = record()["model_use"]
        self.assertEqual(model["llm_calls"], 0)
        self.assertEqual(model["embeddings"], 0)
        self.assertEqual(model["usd"], 0.0)
        self.assertFalse(model["semantic_classifier_used"])

    def test_no_calibration_label_and_no_parameter_fitting(self):
        text = json.dumps(record())
        self.assertNotIn('CALIBRATED"', text)
        self.assertIsNone(record()["selected_route"])

    def test_problem_family_remains_parked(self):
        self.assertEqual(record()["model_use"]["problem_family_status"], "PARKED")

    def test_no_reliability_was_written_onto_an_evidence_row(self):
        stored = record()["counters"]["evidence_with_stored_reliability"]
        self.assertEqual(stored["before"], 0)
        self.assertEqual(stored["after"], 0)


# ============================================ §34 — deployment-local confirmations


class DeploymentLocalHumanConfirmations(unittest.TestCase):
    def test_the_checklist_finding_is_recorded(self):
        checklist = record()["deployment_local_human_confirmations_require_migration_checklist"]
        self.assertIn("not portable", checklist["finding"])

    def test_no_replay_mechanism_was_created(self):
        checklist = record()["deployment_local_human_confirmations_require_migration_checklist"]
        self.assertIn("No replay mechanism was created", checklist["not_made_portable"])


if __name__ == "__main__":
    unittest.main()
