"""Mission 1.44 §37. A third reliability question prepared, and not answered.

The negative assertions are the load-bearing half again, and this scope makes
one of them harder than Mission 1.42's did. There, the near miss was TED against
TED: four scope fields shared, one differing. Here the near miss is **the same
publisher, the same resource, the same record kind and the same claim type**,
with a `0.65` already reviewed and sitting one field away — the most inviting
number in the repository to reach for.

The other half is a distinction this scope forced and the TED one did not.
Mission 1.42 could assert `NOT_ESTABLISHED` for TED's mutability because the
basis said **nothing**. Here the basis says **something and not enough**: a
known-problems list records that a classification incident happened, without
stating a revision policy. *Something and not enough* is a judgement about
sufficiency, so software must leave it blank — and a test holds that line,
because it is exactly the place where a generator would be tempted to be
helpful.

`unittest`, not pytest: `run_python_tests.py` discovers this package with
`unittest discover`.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import unittest

from sros_contracts import (
    ClaimType,
    ReliabilityAssessmentOrigin,
    ReliabilityBasisType,
    ReliabilityResolutionOutcome,
)
from sros_evidence_reliability import (
    ReliabilityAssessment,
    ReliabilityBasis,
    ReliabilityScope,
    resolve_reliability,
    rubric,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
PACKET = DOCS / "wikimedia-convergent-reliability-review-packet-v1.json"
WORKSHEET = DOCS / "wikimedia-convergent-reliability-review-packet-v1.md"
AUDIT = DOCS / "calibration-feasibility-audit-v1.json"
SHAPE = DOCS / "calibration-corpus-shape-after-v1.json"
CONTRACT_DOC = REPO_ROOT / "docs" / "CLAUDE.md"

SCOPE_FIELDS = (
    "source_id",
    "resource_id",
    "record_kind_id",
    "claim_type",
    "proposition_kind",
)
CONVERGENT_KIND = "platform_counted_content_request_change_witnessed"
DETAILED_KIND = "platform_counted_content_request_change"

SOURCE = "wikimedia-pageviews"
RESOURCE = "metrics/pageviews/per-article/en.wikipedia.org"
RECORD_KIND = "content_request_count"


def packet() -> dict:
    return json.loads(PACKET.read_text(encoding="utf-8"))


def without_notes(value: object) -> object:
    """Strip `$comment` and `$note` at any depth.

    A note is where a RULE is written -- *0.65 is not a baseline* -- and a rule
    may name the value it forbids. A FIELD may not. `testing-strategy.md` §23,
    handled structurally rather than by loosening the pattern.
    """
    if isinstance(value, dict):
        return {k: without_notes(v) for k, v in value.items() if k not in ("$comment", "$note")}
    if isinstance(value, list):
        return [without_notes(v) for v in value]
    return value


def _basis() -> tuple[ReliabilityBasis, ...]:
    return (
        ReliabilityBasis(
            basis_type=ReliabilityBasisType.MEASUREMENT_METHODOLOGY,
            document_title="Research:Page view",
            summarized_finding="(fixture)",
            document_url="https://meta.wikimedia.org/wiki/Research:Page_view",
            section_reference="Definition; Tagging",
            retrieved_at=dt.date(2026, 9, 3),
        ),
    )


def assessment(kind: str, reliability: float) -> ReliabilityAssessment:
    """A stand-in at a real scope, reconstructed rather than read from a database.

    The property under test is the SCOPE ALGEBRA, which is deployment-independent,
    and CI's integration job starts from an empty database.
    """
    return ReliabilityAssessment(
        id=f"stand-in-{kind}",
        scope=ReliabilityScope(
            source_id=SOURCE,
            resource_id=RESOURCE,
            record_kind_id=RECORD_KIND,
            claim_type=ClaimType.OBSERVED,
            proposition_kind=kind,
        ),
        version=1,
        reliability=reliability,
        origin=ReliabilityAssessmentOrigin.HUMAN_REVIEW,
        rationale="(fixture)",
        stated_limitation="(fixture)",
        reviewed_by="thibchm",
        reviewed_at=None,
        basis=_basis(),
        calibration_dataset_ref=None,
    )


class TheScopeIsMeasuredNotAssumed(unittest.TestCase):
    """§0, §1. One scope, the exact five fields, from the live rows."""

    def test_exactly_one_reliability_scope_covers_the_convergent_rows(self):
        measured = packet()["measured_scopes"]
        self.assertEqual(len(measured), 1)
        self.assertEqual(tuple(measured[0]["scope"]), SCOPE_FIELDS)

    def test_the_scope_is_the_expected_five_part_key(self):
        scope = packet()["measured_scopes"][0]["scope"]
        self.assertEqual(
            scope,
            {
                "source_id": SOURCE,
                "resource_id": RESOURCE,
                "record_kind_id": RECORD_KIND,
                "claim_type": "OBSERVED",
                "proposition_kind": CONVERGENT_KIND,
            },
        )

    def test_eighteen_evidence_across_six_claims(self):
        measured = packet()["measured_scopes"][0]
        self.assertEqual(measured["evidence_count"], 18)
        self.assertEqual(measured["claim_count"], 6)
        self.assertEqual(len(packet()["affected_rows"]), 18)
        self.assertEqual(len(packet()["affected_claims"]), 6)

    def test_the_witness_cardinalities_are_the_ones_mission_1_43_created(self):
        counts = sorted(c["witness_count"] for c in packet()["affected_claims"])
        self.assertEqual(counts, [2, 3, 3, 3, 3, 4])

    def test_the_resolver_returns_no_applicable_assessment(self):
        measured = packet()["measured_scopes"][0]
        self.assertEqual(measured["outcome"], "NO_APPLICABLE_ASSESSMENT")
        self.assertIsNone(measured["reliability"])

    def test_the_scope_carries_no_article_direction_or_period(self):
        """One judgement binds all six Claims, so there is one question."""
        for field in (
            "content_id",
            "direction",
            "audience_class",
            "period_label_from",
            "period_label_to",
            "witness_count",
            "claim_id",
        ):
            self.assertNotIn(field, SCOPE_FIELDS)
            self.assertNotIn(field, packet()["measured_scopes"][0]["scope"])


class TheNearMissIsTheWholeTest(unittest.TestCase):
    """§2, §3. Four fields shared, one differing, and that is enough."""

    def test_the_detailed_wikimedia_assessment_does_not_resolve_the_convergent_scope(self):
        detailed = assessment(DETAILED_KIND, 0.65)
        convergent_scope = ReliabilityScope(
            source_id=SOURCE,
            resource_id=RESOURCE,
            record_kind_id=RECORD_KIND,
            claim_type=ClaimType.OBSERVED,
            proposition_kind=CONVERGENT_KIND,
        )
        resolution = resolve_reliability(
            scope=convergent_scope, candidates=[detailed], supplied=None
        )
        self.assertIs(resolution.outcome, ReliabilityResolutionOutcome.NO_APPLICABLE_ASSESSMENT)
        self.assertIsNone(resolution.reliability)

    def test_proposition_kind_alone_decides_it_in_both_directions(self):
        detailed = assessment(DETAILED_KIND, 0.65)
        convergent = assessment(CONVERGENT_KIND, 0.4)

        for field in SCOPE_FIELDS:
            if field == "proposition_kind":
                continue
            self.assertEqual(getattr(detailed.scope, field), getattr(convergent.scope, field))

        # Each resolves its own scope and neither reaches the other's.
        self.assertEqual(
            resolve_reliability(
                scope=detailed.scope, candidates=[detailed, convergent], supplied=None
            ).reliability,
            0.65,
        )
        self.assertEqual(
            resolve_reliability(
                scope=convergent.scope, candidates=[detailed, convergent], supplied=None
            ).reliability,
            0.4,
        )
        self.assertIsNone(
            resolve_reliability(
                scope=convergent.scope, candidates=[detailed], supplied=None
            ).reliability
        )
        self.assertIsNone(
            resolve_reliability(
                scope=detailed.scope, candidates=[convergent], supplied=None
            ).reliability
        )

    def test_there_is_no_source_wide_coefficient_to_fall_back_on(self):
        """A scope naming only the source matches nothing, by construction."""
        detailed = assessment(DETAILED_KIND, 0.65)
        for kind in ("", SOURCE, "anything_else"):
            if not kind:
                continue
            probe = ReliabilityScope(
                source_id=SOURCE,
                resource_id=RESOURCE,
                record_kind_id=RECORD_KIND,
                claim_type=ClaimType.OBSERVED,
                proposition_kind=kind,
            )
            self.assertIsNone(
                resolve_reliability(scope=probe, candidates=[detailed], supplied=None).reliability
            )

    def test_the_packet_ran_leak_checks_over_the_whole_neighbourhood(self):
        checks = packet()["leak_checks"]
        self.assertEqual(checks["leaks_found"], 0)
        # Every proposition kind in the corpus is probed, not a chosen few.
        probed = {c["probed_proposition_kind"] for c in checks["checks"]}
        for kind in (
            DETAILED_KIND,
            CONVERGENT_KIND,
            "source_reported_procurement_value_contrast",
            "source_reported_metric_period_change",
            "community_site_published_questions_carrying_tag",
            "source_reported_term_frequency_change",
        ):
            self.assertIn(kind, probed)
        for check in checks["checks"]:
            self.assertIs(check["resolved"], check["scopes_identical"])


class SoftwarePreparedItAndAnsweredAlmostNothing(unittest.TestCase):
    """§25-§29. One absence asserted; every judgement blank."""

    def test_every_judgement_field_is_blank(self):
        judgement = packet()["operator_worksheet"]["judgement"]
        self.assertIsNone(judgement["reliability"])
        self.assertIsNone(judgement["reviewed_by"])
        self.assertIsNone(judgement["review_timestamp"])
        self.assertIsNone(judgement["hard_stops_triggered"])
        self.assertEqual(judgement["rationale"], "")
        self.assertEqual(judgement["stated_limitation"], "")

    def test_the_numeric_gate_is_unanswered(self):
        worksheet = packet()["operator_worksheet"]
        self.assertEqual(worksheet["judgement"]["numeric_judgement_gate"], "UNANSWERED")
        self.assertEqual(
            set(worksheet["numeric_judgement_gate_options"]),
            {outcome.value for outcome in rubric.NumericJudgementGate},
        )

    def test_exactly_one_dimension_state_was_assigned_by_software(self):
        states = packet()["operator_worksheet"]["judgement"]["dimension_states"]
        self.assertEqual(set(states), {d.id for d in rubric.DIMENSIONS})
        assigned = {k: v for k, v in states.items() if v is not None}
        self.assertEqual(set(assigned), {"SOURCE_SIDE_CHECKABILITY"})
        self.assertEqual(assigned["SOURCE_SIDE_CHECKABILITY"], "NOT_ESTABLISHED")

    def test_the_only_assigned_state_is_the_one_the_rubric_permits(self):
        states = packet()["operator_worksheet"]["judgement"]["dimension_states"]
        permitted = {s.value for s in rubric.SOFTWARE_ASSIGNABLE_STATES}
        for state in states.values():
            if state is not None:
                self.assertIn(state, permitted)

    def test_historical_mutability_is_left_blank_although_it_is_the_obvious_one(self):
        """The distinction this scope forced.

        The basis says SOMETHING and not enough -- an incident happened, no
        revision policy is stated -- and *something and not enough* is a
        judgement about sufficiency rather than a claim about what the corpus
        contains. TED's equivalent basis said nothing at all, which is why
        Mission 1.42 could assert the absence there and this one may not.
        """
        states = packet()["operator_worksheet"]["judgement"]["dimension_states"]
        self.assertIsNone(states["HISTORICAL_MUTABILITY"])
        reasons = packet()["software_assignable_states"]["not_assigned_and_why"]
        self.assertIn("HISTORICAL_MUTABILITY", reasons)
        self.assertIn("judgement", reasons["HISTORICAL_MUTABILITY"])

    def test_no_materiality_answer_was_supplied(self):
        unknowns = packet()["operator_worksheet"]["material_unknowns"]
        self.assertTrue(unknowns)
        for unknown in unknowns:
            self.assertIsNone(unknown["reviewer_answer"])
            self.assertEqual(unknown["materiality_question"], rubric.MATERIALITY_QUESTION)
            self.assertEqual(set(unknown["permitted_answers"]), set(rubric.MATERIALITY_ANSWERS))

    def test_no_hard_stop_was_decided(self):
        stops = packet()["operator_worksheet"]["hard_stops"]
        self.assertEqual({s["id"] for s in stops}, {h.id for h in rubric.HARD_STOPS})
        for stop in stops:
            self.assertIsNone(stop["factual_trigger_present"])
            self.assertIsNone(stop["reviewer_decision"])

    def test_the_reviewer_is_not_inferred(self):
        rendered = json.dumps(without_notes(packet()["operator_worksheet"]))
        prior = [
            entry
            for entry in packet()["historical_other_scope_context"]
            if entry.get("reviewed_by")
        ]
        self.assertTrue(prior)
        for entry in prior:
            self.assertNotIn(entry["reviewed_by"], rendered)

    def test_no_recommendation_range_or_threshold_adjective_appears(self):
        scanned = json.dumps(without_notes(packet())).lower()
        for phrase in (
            "recommended reliability",
            "suggested reliability",
            "reliability range",
            "high reliability",
            "medium reliability",
            "low reliability",
            "slightly lower",
            "slightly higher",
            "probably 0.65",
            "same as the detailed",
        ):
            self.assertNotIn(phrase, scanned)
        self.assertIsNone(packet()["reliability_scale"]["threshold_labels"])


class TheHistoricalValueIsContextAndNothingElse(unittest.TestCase):
    """§6, §30. 0.65 is a persisted fact about a different question."""

    def test_it_appears_in_no_field_that_could_be_read_as_a_value(self):
        """Over FIELDS, with the rule blocks excluded.

        `what_this_packet_is_not` and `what_a_value_would_not_do` are where the
        RULES live -- *not an assertion that the existing 0.65 is near the right
        answer* -- and a rule may name the value it forbids. A field may not.
        Scanning both together is the `testing-strategy.md` §23 mistake, met for
        the fourth time in this arc and handled the same way each time.
        """
        doc = without_notes(packet())
        for rule_block in (
            "historical_other_scope_context",
            "what_this_packet_is_not",
            "what_a_value_would_not_do",
        ):
            doc.pop(rule_block, None)
        self.assertNotIn("0.65", json.dumps(doc))

    def test_the_rule_blocks_do_forbid_it_by_name(self):
        """The other half: the rules must actually say the thing."""
        rules = json.dumps(
            packet()["what_this_packet_is_not"] + packet()["what_a_value_would_not_do"]
        )
        self.assertIn("0.65", rules)

    def test_no_field_named_like_an_anchor_exists_anywhere(self):
        def keys(value: object):
            if isinstance(value, dict):
                for key, nested in value.items():
                    yield key
                    yield from keys(nested)
            elif isinstance(value, list):
                for item in value:
                    yield from keys(item)

        for key in keys(packet()):
            lowered = key.lower()
            for forbidden in (
                "recommended",
                "suggested",
                "candidate_value",
                "anchor",
                "default_reliability",
                "baseline_value",
                "prior",
            ):
                self.assertNotIn(forbidden, lowered, f"anchor-shaped field: {key}")

    def test_the_historical_entry_says_it_is_not_the_scope_under_review(self):
        entries = packet()["historical_other_scope_context"]
        self.assertTrue(entries)
        for entry in entries:
            self.assertIs(entry["is_the_scope_under_review"], False)
            self.assertNotEqual(entry["scope"]["proposition_kind"], CONVERGENT_KIND)

    def test_the_pre_rubric_assessments_keep_null_provenance(self):
        """§31. Not backfilled: NULL is true rather than missing."""
        wikimedia = [
            entry
            for entry in packet()["historical_other_scope_context"]
            if entry["scope"]["source_id"] == SOURCE
        ]
        self.assertEqual(len(wikimedia), 1)
        self.assertIs(wikimedia[0]["predates_the_rubric"], True)
        self.assertIsNone(wikimedia[0]["review_rubric"])
        self.assertEqual(wikimedia[0]["reliability"], 0.65)

    def test_a_future_assessment_can_record_its_rubric(self):
        provenance = packet()["operator_worksheet"]["rubric_provenance_for_a_future_assessment"]
        self.assertEqual(provenance["review_rubric_id"], rubric.RUBRIC_ID)
        self.assertEqual(provenance["review_rubric_version"], rubric.RUBRIC_VERSION)


class NothingStandsInForTheJudgement(unittest.TestCase):
    """§12, §13, §15, §24. What must not be read as reliability."""

    def test_engineering_validation_is_recorded_and_refused_as_basis(self):
        inputs = packet()["engineering_validation_inputs"]
        self.assertIs(inputs["may_be_used_as_reliability_basis"], False)
        self.assertEqual(inputs["classification"], "ENGINEERING_VALIDATION_INPUT")
        self.assertTrue(inputs["inputs"])

    def test_extraction_confidence_is_not_source_reliability(self):
        """§15. Every row reads 1.0, and that is about our extractor."""
        for row in packet()["affected_rows"]:
            self.assertEqual(row["extraction_confidence"], 1.0)
        excluded = " ".join(packet()["what_reliability_means"]["it_is_not"]).lower()
        self.assertIn("extractor read the signal correctly", excluded)

    def test_witness_cardinality_is_not_offered_as_reliability(self):
        """§12. Four witnesses is not four independent sources."""
        text = WORKSHEET.read_text(encoding="utf-8")
        self.assertIn("Cardinality belongs to aggregation", text)
        excluded = json.dumps(packet()["what_a_value_would_not_do"]).lower()
        self.assertIn("witness count", excluded)

    def test_independence_remains_unknown_with_no_groups(self):
        """§13. Different days, articles and directions establish nothing."""
        for row in packet()["affected_rows"]:
            self.assertEqual(row["independence_state"], "UNKNOWN")
            self.assertIsNone(row["independence_group_id"])

    def test_the_requester_class_is_never_translated(self):
        """§16. `user` is the platform's own label, not `human`."""
        for claim in packet()["affected_claims"]:
            self.assertEqual(claim["audience_class"], "user")
        rendered = json.dumps(without_notes(packet())).lower()
        for translation in ('"human"', "human traffic", "actual readers"):
            self.assertNotIn(translation, rendered)

    def test_reliability_is_not_written_onto_any_evidence_row(self):
        for row in packet()["affected_rows"]:
            self.assertIsNone(row["evidence_reliability_column"])


class TheContractAndTheCorpusWereNotTouched(unittest.TestCase):
    """§34, §36. Preparation changes nothing."""

    def test_the_convergence_contract_is_the_one_mission_1_43_registered(self):
        contract = packet()["convergence_contract"]
        self.assertEqual(
            contract["contract_id"], "platform-counted-content-request-change-witnessed"
        )
        self.assertEqual(contract["version"], "1.0.0")
        self.assertEqual(set(contract["witness_fields"]), {"period_label_from", "period_label_to"})
        for field in ("audience_class", "direction", "content_id"):
            self.assertIn(field, contract["identity_fields"])

    def test_increasing_and_decreasing_remain_different_propositions(self):
        directions = {c["direction"] for c in packet()["affected_claims"]}
        self.assertEqual(directions, {"INCREASING", "DECREASING"})
        # And every Evidence row still SUPPORTS its own Claim.
        for row in packet()["affected_rows"]:
            self.assertEqual(row["direction"], "SUPPORTS")

    def test_no_contradiction_or_temporal_claim_was_invented(self):
        shape = json.loads(SHAPE.read_text(encoding="utf-8"))["mechanisms_exercised"]
        self.assertEqual(shape["claims_with_contradiction"], 0)
        self.assertEqual(shape["claims_temporally_sensitive"], 0)
        self.assertEqual(shape["claims_with_established_independence"], 0)

    def test_the_six_claims_are_still_unavailable(self):
        units = [
            unit
            for unit in json.loads(SHAPE.read_text(encoding="utf-8"))["units"]
            if unit["proposition_kind"] == CONVERGENT_KIND
        ]
        self.assertEqual(len(units), 6)
        for unit in units:
            self.assertEqual(unit["aggregation_status"], "UNAVAILABLE")

    def test_the_profile_is_still_uncalibrated(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(audit["profile"]["status"], "UNCALIBRATED")
        self.assertGreaterEqual(audit["totals"]["current_reliability_assessments"], 3)

    def test_problem_family_is_still_parked(self):
        self.assertIn("PARK_PROBLEM_FAMILY_CLASSIFIER", CONTRACT_DOC.read_text(encoding="utf-8"))

    def test_no_model_or_embedding_appears_in_the_packet(self):
        rendered = json.dumps(packet()).lower()
        for phrase in ("model_version", "prompt_version", "embedding", "model_guessed"):
            self.assertNotIn(phrase, rendered)


class TheRenderedWorksheet(unittest.TestCase):
    """§32, §33. The half a person actually reads."""

    def test_it_carries_the_scope_and_the_blanks(self):
        text = WORKSHEET.read_text(encoding="utf-8")
        self.assertIn(CONVERGENT_KIND, text)
        self.assertIn("NUMERIC_JUDGEMENT_GATE           UNANSWERED", text)
        self.assertIn("Reliability [0.0, 1.0]           ______", text)
        self.assertIn("YES / NO / UNSURE   ______", text)

    def test_it_names_the_rubric_it_was_prepared_under(self):
        text = WORKSHEET.read_text(encoding="utf-8")
        self.assertIn(f"{rubric.RUBRIC_ID}@{rubric.RUBRIC_VERSION}", text)

    def test_it_states_that_one_judgement_binds_every_claim(self):
        text = WORKSHEET.read_text(encoding="utf-8")
        self.assertIn("One judgement binds every row above", text)

    def test_it_carries_no_recommendation(self):
        text = WORKSHEET.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"reliability\s*(of|:|=)\s*0\.\d", text, re.IGNORECASE))
        self.assertNotIn("we recommend", text.lower())


class BranchesTheLiveResolverNeverEnters(unittest.TestCase):
    """§37. The reporting branch that no live data reaches.

    The live resolver returns `NO_APPLICABLE_ASSESSMENT` for every row in this
    scope, so the packet's *resolved* branches — the ones that read a binding —
    never execute against real data. Mission 1.42.1 shipped a wrong attribute
    name in exactly such a branch. These force them with a non-empty fixture.
    """

    def test_the_resolved_branch_produces_a_complete_binding(self):
        convergent = assessment(CONVERGENT_KIND, 0.4)
        resolution = resolve_reliability(
            scope=convergent.scope, candidates=[convergent], supplied=None
        )
        self.assertIs(resolution.outcome, ReliabilityResolutionOutcome.RESOLVED)
        binding = resolution.binding
        self.assertIsNotNone(binding)
        payload = binding.to_json()
        for field in (
            "assessment_id",
            "assessment_key",
            "version",
            "origin",
            "reliability",
            "reviewed_by",
            "reviewed_at",
            "review_rubric_id",
            "review_rubric_version",
        ):
            self.assertIn(field, payload)

    def test_a_rubric_stamped_assessment_reports_its_provenance(self):
        stamped = ReliabilityAssessment(
            **{
                **assessment(CONVERGENT_KIND, 0.4).__dict__,
                "review_rubric_id": rubric.RUBRIC_ID,
                "review_rubric_version": rubric.RUBRIC_VERSION,
            }
        )
        binding = resolve_reliability(
            scope=stamped.scope, candidates=[stamped], supplied=None
        ).binding
        self.assertIsNotNone(binding)
        self.assertEqual(binding.review_rubric_id, rubric.RUBRIC_ID)
        self.assertEqual(binding.review_rubric_version, rubric.RUBRIC_VERSION)

    def test_two_assessments_for_one_scope_are_refused_rather_than_chosen_between(self):
        """The branch a second review would enter, and it must not pick one."""
        first = assessment(CONVERGENT_KIND, 0.4)
        second = ReliabilityAssessment(**{**first.__dict__, "id": "stand-in-second"})
        resolution = resolve_reliability(
            scope=first.scope, candidates=[first, second], supplied=None
        )
        self.assertIs(resolution.outcome, ReliabilityResolutionOutcome.AMBIGUOUS_ASSESSMENTS)
        self.assertIsNone(resolution.reliability)


if __name__ == "__main__":
    unittest.main()
