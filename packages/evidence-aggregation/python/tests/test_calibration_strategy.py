"""Mission 1.37 §38. The calibration contracts, and everything the strategy did not do.

**A strategy is not a calibration**, so most of these are negative: they assert
that no parameter moved, no profile changed status, and no label of any kind came
into existence. The positive ones test the machine-readable contracts the mission
does create.

They live in this package rather than beside the mission's other artifacts
because this package owns the aggregation contract and already depends on it.
`sros-opportunity` declares only `sros-contracts`, and a test importing
`sros_evidence_aggregation` from there would quietly widen that boundary.

`unittest`, no third-party dependency, so this runs in the zero-dependency CI job
(ADR-009) like its sibling suite.
"""

from __future__ import annotations

import json
import pathlib
import unittest

from sros_contracts import (
    AggregationProfileStatus,
    ClaimTemporality,
    EvidenceDirection,
)
from sros_evidence_aggregation import (
    REFERENCE_PROFILE_V1,
    EvidenceAggregationProfile,
    EvidenceItem,
    aggregate,
)
from sros_evidence_aggregation.errors import ProfileError, UncalibratedProfileError

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
STRATEGY = DOCS / "evidence-aggregation-calibration-strategy-v1.json"
STRATEGY_MD = DOCS / "evidence-aggregation-calibration-strategy-v1.md"
SCHEMA = DOCS / "calibration-reference-dataset-schema-v1.json"
AUDIT = DOCS / "calibration-feasibility-audit-v1.json"
FRAMEWORK = REPO_ROOT / "docs" / "domain" / "evidence-aggregation-framework-v1.md"
PRIOR_PLAN = REPO_ROOT / "docs" / "domain" / "evidence-aggregation-calibration-plan-v1.md"


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def strategy() -> dict:
    return _load(STRATEGY)


def schema() -> dict:
    return _load(SCHEMA)


def audit() -> dict:
    return _load(AUDIT)


def _supporting_item(reliability: float | None) -> EvidenceItem:
    return EvidenceItem(
        evidence_id="e1",
        direction=EvidenceDirection.SUPPORTS,
        relevance=1.0,
        directness=1.0,
        reliability=reliability,
        extraction_confidence=1.0,
    )


class TheProfileIsUntouched(unittest.TestCase):
    """§31, §36. Nothing in a strategy mission may move a parameter."""

    def test_reference_profile_v1_is_still_uncalibrated(self) -> None:
        self.assertIs(REFERENCE_PROFILE_V1.status, AggregationProfileStatus.UNCALIBRATED)
        self.assertFalse(REFERENCE_PROFILE_V1.is_calibrated)
        self.assertIsNone(REFERENCE_PROFILE_V1.calibration_dataset_ref)
        self.assertIsNone(REFERENCE_PROFILE_V1.calibrated_at)

    def test_no_half_life_was_invented(self) -> None:
        """§17. Not a universal one, not a Docker one, not any."""
        self.assertEqual(dict(REFERENCE_PROFILE_V1.half_life_days), {})
        self.assertIsNone(REFERENCE_PROFILE_V1.half_life_for("anything"))
        self.assertIsNone(REFERENCE_PROFILE_V1.half_life_for(None))

    def test_no_level_threshold_changed(self) -> None:
        """§18. The structural floors, unmoved."""
        thresholds = REFERENCE_PROFILE_V1.level_thresholds
        self.assertEqual(thresholds.repeated_signal_min_groups, 2)
        self.assertEqual(thresholds.multi_source_min_groups, 3)
        self.assertEqual(thresholds.multi_source_min_families, 2)

    def test_the_required_component_set_is_unchanged(self) -> None:
        self.assertEqual(
            REFERENCE_PROFILE_V1.required_item_fields,
            ("relevance", "directness", "reliability", "extraction_confidence", "freshness"),
        )

    def test_production_aggregate_still_refuses_an_uncalibrated_profile(self) -> None:
        """The gate that makes UNCALIBRATED mean something."""
        with self.assertRaises(UncalibratedProfileError):
            aggregate(
                "c1",
                [_supporting_item(0.65)],
                REFERENCE_PROFILE_V1,
                temporality=ClaimTemporality.EVERGREEN,
            )

    def test_the_override_must_be_said_out_loud_and_is_reported(self) -> None:
        result = aggregate(
            "c1",
            [_supporting_item(0.65)],
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality.EVERGREEN,
            allow_uncalibrated=True,
        )
        self.assertFalse(result.calibrated)
        self.assertTrue(any("UNCALIBRATED" in w for w in result.warnings))

    def test_a_calibrated_profile_cannot_exist_without_a_dataset_reference(self) -> None:
        """A calibration nobody can re-run is a claim, not a calibration."""
        with self.assertRaises(ProfileError):
            EvidenceAggregationProfile(
                profile_id="fabricated",
                version="1.0.0",
                status=AggregationProfileStatus.CALIBRATED,
            )


class TheScoreIsNotAProbability(unittest.TestCase):
    """§1, §15."""

    def test_the_strategy_states_what_the_construct_is_not(self) -> None:
        joined = " ".join(strategy()["construct"]["does_not_measure"]).lower()
        self.assertIn("state of the world", joined)
        self.assertIn("probability", joined)
        self.assertIn("whether the claim is true", joined)

    def test_probability_metrics_are_forbidden_by_name(self) -> None:
        """The names matter: a reader reaches for whichever is familiar."""
        forbidden = {m["metric"] for m in strategy()["metrics"]["forbidden"]}
        self.assertIn("Brier score", forbidden)
        self.assertIn("log loss", forbidden)
        self.assertTrue(any("reliability diagram" in m for m in forbidden))

    def test_every_permitted_metric_names_a_failure_it_detects(self) -> None:
        """A metric chosen because it is a standard name detects nothing."""
        for metric in strategy()["metrics"]["permitted"]:
            self.assertTrue(metric["detects"].strip(), metric["metric"])

    def test_the_target_is_ordinal_and_says_why(self) -> None:
        construct = strategy()["construct"]
        self.assertEqual(construct["scale_status"], "ORDINAL_DEFINED_ABSOLUTE_UNANCHORED")
        self.assertIn("ordering", construct["calibratable_form"])


class ReliabilityIsAnInputNotALabel(unittest.TestCase):
    """§4, §29."""

    def test_reliability_is_classified_as_a_human_assessed_input(self) -> None:
        entry = next(e for e in strategy()["element_inventory"] if e["element"] == "reliability")
        self.assertEqual(entry["classification"], "HUMAN_ASSESSED_INPUT")

    def test_no_element_classifies_reliability_as_calibratable(self) -> None:
        for entry in strategy()["element_inventory"]:
            if entry["element"] == "reliability":
                self.assertNotEqual(entry["classification"], "EMPIRICALLY_CALIBRATABLE_PARAMETER")

    def test_the_reliability_pass_through_baseline_is_mandatory(self) -> None:
        """Without it, reproducing the operator's judgement looks like success."""
        baselines = {b["id"]: b for b in strategy()["baselines"]["required"]}
        self.assertIn("B-2", baselines)
        self.assertIn("pass-through", baselines["B-2"]["baseline"])
        self.assertIn("CRITICAL", baselines["B-2"]["why"])

    def test_the_echo_hazard_is_measured_rather_than_asserted(self) -> None:
        self.assertTrue(strategy()["echo_hazard_controls"]["measured_severity"].startswith("TOTAL"))
        # The PROPERTY, not the count. Mission 1.40 legitimately grew the corpus
        # from 19 scorable claims to 20, and a pinned number would have failed on
        # a change that strengthens the finding rather than weakening it
        # (`testing-strategy.md` §68).
        counts = audit()["limiting_component_counts"]
        self.assertEqual(set(counts), {"reliability"})
        self.assertEqual(sum(counts.values()), audit()["totals"]["claims_with_scorable_evidence"])

    def test_reliability_is_consumed_as_an_input_and_never_refitted(self) -> None:
        """§33. The property, not the count.

        This pinned two assessments, and Mission 1.42.1 legitimately reviewed a
        third scope. What Mission 1.37 established does not depend on how many
        exist: aggregation calibration CONSUMES reviewed reliability and may not
        refit it, so every distinct support strength is a value a named person
        decided, and the profile stays UNCALIBRATED however many there are.
        """
        totals = audit()["totals"]
        self.assertGreaterEqual(totals["current_reliability_assessments"], 2)
        self.assertEqual(audit()["profile"]["status"], "UNCALIBRATED")
        self.assertEqual(audit()["reference_target_tables_present"], [])


class TheDatasetContract(unittest.TestCase):
    """§8, §12, §24, §25, §36."""

    def test_the_schema_carries_no_examples(self) -> None:
        """An example in a schema is what a later reader copies."""
        self.assertEqual(schema()["units"], [])
        self.assertEqual(schema()["labels"], [])
        self.assertIsNone(schema()["split_manifest"])

    def test_a_label_requires_provenance_and_a_named_reviewer(self) -> None:
        fields = schema()["label_schema"]["fields"]
        self.assertTrue(fields["reference_origin"]["required"])
        self.assertTrue(fields["reviewer_id"]["required"])
        self.assertIn("impersonal", fields["reviewer_id"]["note"])

    def test_human_ground_truth_requires_every_label_to_be_human(self) -> None:
        rule = schema()["dataset_identity"]["reference_origin"]["human_ground_truth_established"]
        self.assertIn("EVERY", rule)
        self.assertIn("All, never any", rule)

    def test_a_model_generated_label_cannot_be_a_reference(self) -> None:
        """§8, §35."""
        targets = {t["id"]: t for t in strategy()["reference_targets"]["evaluated"]}
        self.assertEqual(targets["D_MODEL_GENERATED_LABELS"]["verdict"], "FORBIDDEN")
        self.assertIn(
            "model_generated_support_estimate", schema()["unit_schema"]["forbidden_fields"]
        )

    def test_problem_family_labels_are_forbidden(self) -> None:
        """§9. A different relation, and still PARKED."""
        targets = {t["id"]: t for t in strategy()["reference_targets"]["evaluated"]}
        self.assertEqual(targets["E_PROBLEM_FAMILY_LABELS"]["verdict"], "FORBIDDEN")

    def test_a_unit_belongs_to_exactly_one_split(self) -> None:
        invariants = " ".join(schema()["split_manifest_schema"]["invariants"])
        self.assertIn("exactly one split", invariants)
        self.assertIn("shares a split", invariants)

    def test_holdout_isolation_is_structural_rather_than_conventional(self) -> None:
        """Separate files, so a development loader cannot reach a holdout label."""
        invariants = " ".join(schema()["split_manifest_schema"]["invariants"])
        self.assertIn("SEPARATE FILES", invariants)
        self.assertIn("forgetting to filter", invariants)
        self.assertIn("structural", strategy()["split_discipline"]["holdout_isolation"])

    def test_the_holdout_is_evaluated_once_and_parameters_freeze_first(self) -> None:
        gate = {c["id"]: c for c in strategy()["acceptance_gate"]["conditions"]}
        self.assertIn("exactly once", gate["G-7"]["condition"])
        self.assertIn("frozen before the holdout", gate["G-6"]["condition"])

    def test_the_leakage_grouping_rule_is_explicit_and_required(self) -> None:
        leakage = strategy()["leakage_model"]
        self.assertTrue(leakage["composite_rule"].startswith("split by the tuple"))
        required = {
            k["key"] for k in leakage["grouping_key_candidates"] if k["verdict"] == "REQUIRED"
        }
        self.assertTrue({"reliability_scope", "proposition_kind", "subject_key"} <= required)

    def test_the_leakage_rule_is_not_weakened_to_fit_current_data(self) -> None:
        warning = strategy()["leakage_model"]["feasibility_warning"]
        self.assertIn("2 groups", warning)
        self.assertIn("not an argument for weakening", warning)

    def test_a_dataset_version_is_immutable(self) -> None:
        self.assertIn("immutable", strategy()["dataset_immutability"]["rule"])
        self.assertIn("new version", schema()["dataset_identity"]["immutability"])

    def test_disagreement_is_retained_rather_than_averaged(self) -> None:
        disagreement = schema()["label_schema"]["disagreement"]
        self.assertIn("never averaged", disagreement["representation"])
        self.assertIn("refused as the default", disagreement["majority_vote"])
        self.assertIn("IRRECONCILABLE", disagreement["adjudication_state"]["values"])

    def test_no_reviewer_count_was_invented(self) -> None:
        """§8. A number that exists to make a document look complete."""
        protocol = strategy()["reviewer_protocol"]
        self.assertEqual(protocol["reviewer_count"], "NOT_YET_QUANTIFIED")
        self.assertIn("floor", protocol["reviewer_count_basis"])

    def test_no_sample_size_was_invented(self) -> None:
        """§27."""
        sample = strategy()["sample_size"]
        self.assertEqual(sample["status"], "SAMPLE_REQUIREMENT_NOT_YET_QUANTIFIED")
        self.assertTrue(sample["analysis_required_first"])
        self.assertIn("100", sample["forbidden"])


class MissingIsNotWeak(unittest.TestCase):
    """§21. No-data must stay distinguishable from weak evidence."""

    def test_unavailable_may_not_become_a_number(self) -> None:
        forbidden = " ".join(strategy()["missing_evidence_strategy"]["forbidden_in_calibration"])
        self.assertIn("mapping UNAVAILABLE to 0", forbidden)
        self.assertIn("mapping UNAVAILABLE to 50", forbidden)
        self.assertIn("imputing", forbidden)

    def test_unavailable_units_are_retained_in_the_dataset(self) -> None:
        self.assertIn("RETAINED", strategy()["missing_evidence_strategy"]["required"])

    def test_the_engine_still_refuses_to_score_a_missing_component(self) -> None:
        """Not a document claim: the real engine, with reliability absent."""
        result = aggregate(
            "c1",
            [_supporting_item(None)],
            REFERENCE_PROFILE_V1,
            temporality=ClaimTemporality.EVERGREEN,
            allow_uncalibrated=True,
        )
        self.assertEqual(result.status.value, "UNAVAILABLE")
        self.assertEqual(result.masses.uncertainty_mass, 1.0)
        self.assertEqual(result.masses.supported_mass, 0.0)
        self.assertIsNone(result.contributions[0].q)


class TheFeasibilityMeasurement(unittest.TestCase):
    """§26. Measured against the live database, not quoted from a report."""

    def test_the_aggregation_layer_has_now_aggregated(self) -> None:
        """Mission 1.37's one-sentence result was *the aggregation layer has
        never aggregated*. Mission 1.41 made it false, which is what it was for.

        The assertion is re-pointed rather than deleted: what it really guards is
        that this counter is MEASURED, and a test asserting 0 forever would have
        been a test asserting the project never progresses.
        """
        self.assertGreater(audit()["coverage"]["multi_evidence_claims"], 0)
        self.assertGreater(audit()["coverage"]["max_evidence_per_claim"], 1)

    def test_the_empty_coverage_dimensions_are_the_finding(self) -> None:
        coverage = audit()["coverage"]
        for dimension in (
            "contradiction_present",
            "mixed_support_and_contradiction",
            "conflict_mass_non_zero",
            "multi_source_claims",
            "independence_established_claims",
            "temporally_sensitive_claims",
            "claims_with_a_claim_feature",
            "categorised_market_or_validation",
        ):
            self.assertEqual(coverage[dimension], 0, dimension)

    def test_every_target_value_is_a_reviewed_reliability_value(self) -> None:
        """The property, not the count.

        This pinned `{"0.5", "0.65"}` until Mission 1.42.1 reviewed a third
        scope and made it `{"0.5", "0.55", "0.65"}` -- **a count that can
        legitimately grow is deployment state** (`testing-strategy.md` §68).
        What Mission 1.37 actually established survives every such review: the
        target variable is REVIEWED RELIABILITY and nothing else, because
        reliability is the limiting component on every scorable claim, so
        `min()` returns it unchanged. A fourth reviewed scope will add a fourth
        value and change none of that.
        """
        strengths = audit()["distinct_support_strengths"]
        self.assertTrue(strengths)
        limiting = audit()["limiting_component_counts"]
        self.assertEqual(set(limiting), {"reliability"})
        self.assertEqual(sum(strengths.values()), limiting["reliability"])

    def test_no_reference_label_table_exists(self) -> None:
        self.assertEqual(audit()["reference_target_tables_present"], [])

    def test_the_feasibility_answer_is_no(self) -> None:
        self.assertEqual(strategy()["feasibility"]["answer"], "NO")
        self.assertIn("never aggregated", strategy()["feasibility"]["headline"])

    def test_the_audit_reports_the_profile_it_ran_under(self) -> None:
        self.assertEqual(audit()["profile"]["status"], "UNCALIBRATED")
        self.assertEqual(audit()["profile"]["half_life_days"], {})


class ThePriorPlanCorrection(unittest.TestCase):
    """The mission's substantive finding, checked against both source texts."""

    def test_the_prior_plan_really_does_propose_an_outcome_target(self) -> None:
        """A correction is only worth making if the text says what it says."""
        prior = PRIOR_PLAN.read_text(encoding="utf-8")
        self.assertIn("Brier-style summary", prior)
        self.assertIn("resolve favourably more often", prior)

    def test_the_framework_really_does_disclaim_truth_estimation(self) -> None:
        framework = FRAMEWORK.read_text(encoding="utf-8")
        self.assertIn("Not a truth estimator", framework)
        self.assertIn("state of the world", framework)

    def test_the_correction_is_recorded_with_both_sides(self) -> None:
        correction = next(c for c in strategy()["corrections_to_prior_plan"] if c["id"] == "C-1")
        self.assertEqual(correction["severity"], "TARGET_CONSTRUCT_CONFLICT")
        self.assertIn("Brier", correction["problem"])
        self.assertTrue(correction["prior_text"])
        self.assertTrue(correction["resolution"])

    def test_the_outcome_target_is_rejected_rather_than_merely_unavailable(self) -> None:
        """§7. Unavailable and wrong-construct are different verdicts."""
        targets = {t["id"]: t for t in strategy()["reference_targets"]["evaluated"]}
        outcome = targets["B_DOCUMENTED_EXTERNAL_OUTCOME"]
        self.assertEqual(outcome["verdict"], "REJECTED_WRONG_CONSTRUCT")
        self.assertFalse(outcome["measures_the_construct"])


class NothingElseMoved(unittest.TestCase):
    """§19, §22, §31, §39."""

    def test_no_parameter_changed(self) -> None:
        self.assertEqual(strategy()["status"], "PREREGISTERED_STRATEGY_NOT_EXECUTED")
        for choice in strategy()["unresolved_semantic_choices"]:
            self.assertFalse(choice["changed_in_this_mission"], choice["id"])

    def test_no_independence_group_was_created(self) -> None:
        self.assertEqual(strategy()["independence_strategy"]["created_in_this_mission"], 0)
        self.assertEqual(audit()["coverage"]["independence_established_claims"], 0)

    def test_no_score_no_ranking_no_opportunity_layer(self) -> None:
        """§22."""
        text = json.dumps(strategy()) + json.dumps(schema())
        for forbidden in ("OpportunityScore", "RankingScore", "MarketScore", "PriorityScore"):
            self.assertNotIn(forbidden, text)
        self.assertIn("opportunity_score", schema()["unit_schema"]["forbidden_fields"])
        self.assertIn("opportunity_rank", schema()["unit_schema"]["forbidden_fields"])

    def test_d03_is_not_collapsed(self) -> None:
        """Five blockers, reported separately."""
        d03 = strategy()["d03_state_after_this_mission"]
        self.assertEqual(d03["1_reliability_definition_authority"], "RESOLVED")
        self.assertEqual(d03["2_reviewed_reliability_for_scopes_in_use"], "PARTIAL")
        self.assertEqual(d03["3_calibrated_aggregation_profile"], "OPEN")
        self.assertEqual(d03["4_temporal_half_life"], "OPEN")
        self.assertEqual(d03["5_evidence_level_thresholds_fitted"], "OPEN")
        self.assertEqual(d03["changed_by_this_mission"], "none. A strategy is not a calibration.")

    def test_the_next_mission_is_not_a_labelling_mission(self) -> None:
        """The blocker underneath the missing labels is corpus shape."""
        nxt = strategy()["next_mission"]
        self.assertIn("not a labelling mission", nxt["recommended"])
        self.assertIn("proposition_key", nxt["specific_precondition"])
        self.assertTrue(nxt["second_pilot"]["required"])
        self.assertTrue(nxt["not_started_by_this_mission"])

    def test_the_second_pilot_may_not_be_chosen_for_convenience(self) -> None:
        self.assertEqual(
            strategy()["next_mission"]["second_pilot"]["forbidden_selection_basis"],
            "ease of fetching",
        )

    def test_the_temporal_strategy_refuses_to_pick_a_half_life(self) -> None:
        """§17."""
        temporal = strategy()["temporal_strategy"]
        self.assertEqual(temporal["status"], "TEMPORAL_CALIBRATION_DATA_MISSING")
        self.assertEqual(temporal["measured"]["temporally_sensitive_claims"], 0)
        self.assertIn("no universal H and no Docker H", temporal["consequence"])

    def test_the_unquantified_gate_conditions_are_blockers_not_guesses(self) -> None:
        """§30. A gate weak enough for current data to pass is not a gate."""
        gate = strategy()["acceptance_gate"]
        unquantified = {c["id"] for c in gate["conditions"] if not c["quantified"]}
        self.assertEqual(unquantified, {"G-3", "G-5", "G-8"})
        for condition in gate["conditions"]:
            if not condition["quantified"]:
                self.assertTrue(condition["blocker"].strip(), condition["id"])

    def test_the_document_and_the_artifact_agree_on_the_outcome(self) -> None:
        self.assertEqual(strategy()["outcome"], "CALIBRATION_STRATEGY_READY_REFERENCE_DATA_MISSING")
        self.assertIn(strategy()["outcome"], STRATEGY_MD.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
