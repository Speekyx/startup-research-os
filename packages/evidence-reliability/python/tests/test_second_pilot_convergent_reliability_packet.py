"""Mission 1.42 §29. A second reliability question prepared, and not answered.

The load-bearing assertions are negative, as in Mission 1.36: **no value, no
range, no threshold adjective, and no reviewer inferred from anything.** What is
new here is the *near miss*. An assessment already exists for this source, this
resource, this record kind and this claim type -- four of the five scope fields
-- at `0.5`. The single field that differs is `proposition_kind`, and these
tests exercise the real resolver to show that one field is enough, in both
directions.

The other new assertion is arithmetic the brief did not predict. Mission 1.41
produced two Claims with two Evidence rows each, so four rows were expected. The
live scope holds **six rows across four Claims**, because a reliability scope
carries no classification division and no currency. That is scope BREADTH, not
scope DRIFT, and the packet has to say so where a reviewer will read it.

`unittest`, not pytest, because `run_python_tests.py` discovers this package
with `unittest discover` -- a suite of bare functions here would be collected as
zero tests and never run.
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
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
PACKET = DOCS / "second-pilot-convergent-reliability-review-packet-v1.json"
WORKSHEET = DOCS / "second-pilot-convergent-reliability-review-packet-v1.md"

SCOPE_FIELDS = (
    "source_id",
    "resource_id",
    "record_kind_id",
    "claim_type",
    "proposition_kind",
)

CONVERGENT_KIND = "source_published_classification_value_contrast_witnessed"
DETAILED_KIND = "source_reported_procurement_value_contrast"


def packet() -> dict:
    return json.loads(PACKET.read_text(encoding="utf-8"))


def without_notes(value: object) -> object:
    """Strip every `$comment` and `$note` key, at any depth.

    A note is where a RULE is written -- *this is not copied from the existing
    TED 0.5* -- and a rule may name the values it forbids. A FIELD may not.
    Scanning both together is the `testing-strategy.md` §23 mistake, and it has
    now been met in five missions, so it is handled structurally rather than by
    loosening the pattern.
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
            document_title="eForms SDK 1.15.1 BT-161 Notice Value",
            summarized_finding="the value of all contracts awarded in this notice",
            document_url="https://docs.ted.europa.eu/eforms/1.15.1/",
            section_reference="BT-161",
            retrieved_at=dt.date(2026, 9, 1),
        ),
    )


def detailed_assessment() -> ReliabilityAssessment:
    """A stand-in for the live TED assessment, at its real scope and value.

    Reconstructed here rather than read from the database, because a test that
    needs a deployment cannot run in CI -- and the property under test is about
    the SCOPE algebra, which is deployment-independent.
    """
    return ReliabilityAssessment(
        id="detailed",
        scope=ReliabilityScope(
            source_id="ted-eu",
            resource_id="notices/eforms-contract-and-award",
            record_kind_id="procurement_notice",
            claim_type=ClaimType.OBSERVED,
            proposition_kind=DETAILED_KIND,
        ),
        version=1,
        reliability=0.5,
        origin=ReliabilityAssessmentOrigin.HUMAN_REVIEW,
        rationale="(not reproduced here)",
        stated_limitation="a published total, not a realised payment",
        reviewed_by="thibchm",
        reviewed_at=None,
        basis=_basis(),
        calibration_dataset_ref=None,
    )


def convergent_scope() -> ReliabilityScope:
    return ReliabilityScope(
        source_id="ted-eu",
        resource_id="notices/eforms-contract-and-award",
        record_kind_id="procurement_notice",
        claim_type=ClaimType.OBSERVED,
        proposition_kind=CONVERGENT_KIND,
    )


class ScopeCountedNotAssumed(unittest.TestCase):
    """§0. The scope is measured by grouping real rows, never inferred."""

    def test_the_scope_is_exactly_the_five_fields_and_no_more(self):
        # A scope carrying a CPV division would be a sixth field nobody reviewed.
        for measured in packet()["measured_scopes"]:
            self.assertEqual(tuple(measured["scope"]), SCOPE_FIELDS)

    def test_there_is_exactly_one_scope_over_the_convergent_rows(self):
        measured = packet()["measured_scopes"]
        self.assertEqual(len(measured), 1)
        self.assertEqual(measured[0]["scope"]["proposition_kind"], CONVERGENT_KIND)
        self.assertEqual(measured[0]["scope"]["claim_type"], ClaimType.OBSERVED.value)

    def test_the_one_scope_resolves_to_no_applicable_assessment(self):
        measured = packet()["measured_scopes"][0]
        self.assertEqual(measured["outcome"], "NO_APPLICABLE_ASSESSMENT")
        self.assertIsNone(measured["reliability"])

    def test_every_affected_row_is_counted_by_the_single_scope(self):
        doc = packet()
        self.assertEqual(doc["measured_scopes"][0]["evidence_count"], len(doc["affected_rows"]))


class TheRowCountTheBriefDidNotPredict(unittest.TestCase):
    """§1. Four rows were expected and six exist, in one unchanged scope."""

    def test_the_row_count_difference_is_reported_and_is_not_scope_drift(self):
        # Reported rather than smoothed over: a mission that quietly delivers a
        # different corpus from the one its brief described has changed what the
        # operator is agreeing to.
        finding = packet()["scope_breadth_finding"]
        self.assertEqual(finding["brief_expected_evidence_rows"], 4)
        self.assertGreater(finding["live_evidence_rows"], finding["brief_expected_evidence_rows"])
        self.assertIs(finding["is_scope_drift"], False)
        self.assertEqual(len(packet()["measured_scopes"]), 1)

    def test_the_reason_is_that_a_scope_carries_no_division_and_no_currency(self):
        finding = packet()["scope_breadth_finding"]
        self.assertGreater(len(finding["distinct_classification_divisions_in_scope"]), 1)
        self.assertGreater(len(finding["distinct_currencies_in_scope"]), 1)
        for field in ("classification_division", "currency", "notice_class"):
            self.assertNotIn(field, SCOPE_FIELDS)

    def test_the_multi_evidence_claims_are_a_subset_of_what_is_bound(self):
        finding = packet()["scope_breadth_finding"]
        self.assertLess(finding["live_multi_evidence_claims"], finding["live_claims"])
        self.assertIn("not answering only for", finding["what_this_changes_for_the_reviewer"])


class OneFieldIsTheWholeDifference(unittest.TestCase):
    """§21, §22. Four of five matching is as inapplicable as none matching."""

    def test_the_ted_detailed_assessment_does_not_resolve_the_convergent_scope(self):
        resolution = resolve_reliability(
            scope=convergent_scope(), candidates=[detailed_assessment()], supplied=None
        )
        self.assertIs(resolution.outcome, ReliabilityResolutionOutcome.NO_APPLICABLE_ASSESSMENT)
        self.assertIsNone(resolution.reliability)

    def test_proposition_kind_alone_decides_it_in_both_directions(self):
        # Vary ONLY `proposition_kind`. This is the pair where a "closest match"
        # resolver would leak first: same publisher, same resource, same record
        # kind, same claim type, same underlying BT-161 amount.
        detailed = detailed_assessment()
        convergent = convergent_scope()
        matching = ReliabilityScope(
            source_id=convergent.source_id,
            resource_id=convergent.resource_id,
            record_kind_id=convergent.record_kind_id,
            claim_type=convergent.claim_type,
            proposition_kind=DETAILED_KIND,
        )

        for field in SCOPE_FIELDS:
            if field == "proposition_kind":
                continue
            self.assertEqual(getattr(convergent, field), getattr(matching, field))
        self.assertNotEqual(convergent.proposition_kind, matching.proposition_kind)

        self.assertEqual(
            resolve_reliability(scope=matching, candidates=[detailed], supplied=None).reliability,
            0.5,
        )
        self.assertIsNone(
            resolve_reliability(scope=convergent, candidates=[detailed], supplied=None).reliability
        )

    def test_the_packet_ran_the_leak_checks_and_found_no_leak(self):
        checks = packet()["leak_checks"]
        self.assertTrue(checks)
        for check in checks:
            self.assertEqual(check["only_field_differing"], "proposition_kind")
            self.assertIs(check["resolved"], check["scopes_identical"])


class SoftwarePreparedItAndAnsweredNothing(unittest.TestCase):
    """§16, §17. Every judgement position is empty and stays empty."""

    def test_every_judgement_field_is_blank(self):
        judgement = without_notes(packet()["operator_worksheet"]["judgement"])
        self.assertEqual(
            set(judgement),
            {
                "review_decision",
                "reliability",
                "reviewed_by",
                "reviewer_rationale",
                "stated_limitation",
            },
        )
        self.assertIsNone(judgement["reliability"])
        self.assertIsNone(judgement["review_decision"])
        self.assertIsNone(judgement["reviewed_by"])
        self.assertEqual(judgement["reviewer_rationale"], "")
        self.assertEqual(judgement["stated_limitation"], "")
        self.assertIsNone(packet()["operator_worksheet"]["question_1_answer"])

    def test_no_confirmation_is_pre_checked(self):
        confirmations = packet()["operator_worksheet"]["confirmations"]
        self.assertTrue(confirmations)
        for item in confirmations:
            self.assertIs(item["checked"], False)

    def test_the_reviewer_is_not_inferred_from_anything(self):
        # Not from a git author, a PR author, an OS username, or the 0.5 row.
        rendered = json.dumps(without_notes(packet()["operator_worksheet"]))
        prior = [a for a in packet()["other_scope_historical_context"] if a.get("reviewed_by")]
        self.assertTrue(prior, "the historical context should name its own reviewer")
        for assessment in prior:
            self.assertNotIn(
                assessment["reviewed_by"],
                rendered,
                "a reviewer for another scope is not the reviewer for this one",
            )

    def test_no_recommended_value_range_or_threshold_adjective_appears(self):
        scanned = json.dumps(without_notes(packet())).lower()
        for phrase in (
            "recommended reliability",
            "suggested reliability",
            "reliability range",
            "high reliability",
            "medium reliability",
            "low reliability",
        ):
            self.assertNotIn(phrase, scanned)
        self.assertIsNone(packet()["reliability_scale"]["threshold_labels"])
        self.assertEqual(packet()["reliability_scale"]["range"], "[0.0, 1.0]")

    def test_no_number_sits_anywhere_a_judgement_would_go(self):
        for field in (
            "what_reliability_means",
            "documentary_review_matrix",
            "open_questions",
        ):
            rendered = json.dumps(without_notes(packet()[field]))
            self.assertIsNone(re.search(r"\b0\.\d+\b", rendered))


class TheExistingValueIsHistoryNotABaseline(unittest.TestCase):
    """§3, §4. A different scope is a different question."""

    def test_the_existing_value_appears_only_as_other_scope_context(self):
        entries = packet()["other_scope_historical_context"]
        self.assertTrue(entries)
        for entry in entries:
            self.assertIs(entry["is_the_scope_under_review"], False)
            self.assertNotEqual(entry["scope"]["proposition_kind"], CONVERGENT_KIND)

    def test_no_assessment_exists_for_the_scope_under_review(self):
        # §27. Two assessments and six basis rows before this mission, and after.
        entries = packet()["other_scope_historical_context"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(sum(e["basis_row_count"] for e in entries), 6)

    def test_the_worksheet_forbids_copying_the_existing_value(self):
        statements = [c["statement"] for c in packet()["operator_worksheet"]["confirmations"]]
        self.assertTrue(any("not copied from the existing" in s for s in statements))
        self.assertTrue(any("not a source-wide" in s for s in statements))
        self.assertTrue(any("not a probability" in s for s in statements))


class NothingStandsInForAHumanJudgement(unittest.TestCase):
    """§7, §9, §10. Correct code is not a dependable measurement."""

    def test_engineering_validation_is_recorded_and_refused_as_basis(self):
        inputs = packet()["engineering_validation_inputs"]
        self.assertIs(inputs["may_be_used_as_reliability_basis"], False)
        self.assertTrue(inputs["inputs"])

        # Every candidate basis row is a RETRIEVED first-party document, and no
        # mission of ours is one. Rewarding the system numerically because its
        # own tests pass is the error this separation exists to prevent.
        validated = json.dumps(inputs["inputs"])
        for row in packet()["candidate_basis_rows"]:
            self.assertNotIn("Mission", row["document_title"])
            self.assertTrue(row["document_url"])
            self.assertNotIn(row["document_title"], validated)

    def test_every_candidate_basis_row_is_a_real_basis_type(self):
        # Mission 1.36 shipped rows the constructor would have raised on.
        for row in packet()["candidate_basis_rows"]:
            ReliabilityBasisType(row["basis_type"])

    def test_no_other_factor_is_offered_as_a_route_to_a_value(self):
        excluded = json.dumps(packet()["what_reliability_means"]["it_is_not"]).lower()
        self.assertIn("independen", excluded)
        for row in packet()["affected_rows"]:
            self.assertEqual(row["independence_state"], "UNKNOWN")
            self.assertIsNone(row["independence_group_id"])
            self.assertEqual(row["extraction_confidence"], 1.0)

    def test_reliability_is_not_written_onto_any_evidence_row(self):
        # ADR-026 Decision 2. Reliability binds late; the column stays NULL.
        for row in packet()["affected_rows"]:
            self.assertIsNone(row["evidence_reliability_column"])


class TheOutcomeStopsHere(unittest.TestCase):
    """§30 A, §32. The next action is a human decision."""

    def test_the_outcome_is_the_stop_condition(self):
        doc = packet()
        self.assertEqual(doc["outcome"], "READY_FOR_SECOND_PILOT_RELIABILITY_REVIEW")
        excluded = json.dumps(doc["what_a_value_would_not_do"]).lower()
        for phrase in ("calibrat", "independen"):
            self.assertIn(phrase, excluded)

    def test_a_value_here_would_calibrate_nothing_and_rank_nothing(self):
        rendered = json.dumps(without_notes(packet())).lower()
        for phrase in ("opportunity score", "ranking", "rank the", "leaderboard"):
            self.assertNotIn(phrase, rendered)

    def test_the_markdown_worksheet_carries_the_same_blank_fields(self):
        text = WORKSHEET.read_text(encoding="utf-8")
        self.assertIn(CONVERGENT_KIND, text)
        self.assertIn("YES / NO", text)
        self.assertIn("- [ ]", text)
        self.assertNotIn("- [x]", text)
        self.assertIn("Reliability [0.0, 1.0]  ______", text)
        self.assertIn("0.5", text)  # the existing value is named as history
        self.assertIsNone(re.search(r"reliability\s*(of|:|=)\s*0\.\d", text, re.I))

    def test_the_markdown_leads_with_the_row_count_correction(self):
        text = WORKSHEET.read_text(encoding="utf-8")
        head = text[: text.index("## 1.")]
        self.assertIn("6 rows across 4 Claims", head)
        self.assertTrue("not\ndrift" in head or "not drift" in head)


if __name__ == "__main__":
    unittest.main()
