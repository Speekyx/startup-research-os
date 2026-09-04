"""Mission 1.44.1 §23. The operator's answers, carried and not adjusted.

Every assertion here is that something the reviewer supplied survived the trip
unchanged. The failure mode this guards is not a crash: it is a generator being
helpful — rounding `0.6`, resolving an `UNSURE`, deriving the gate from the
ordinal states, or nudging toward the `0.65` that sits one scope field away.

The review artifact is BOTH the record of the reasoning and the exact input the
persistence command consumes, so there is one source of truth rather than two
that can drift. These tests read that artifact.

`unittest`, not pytest: `run_python_tests.py` discovers this package with
`unittest discover`.
"""

from __future__ import annotations

import json
import pathlib
import unittest

from sros_contracts import ReliabilityAssessmentOrigin, ReliabilityBasisType
from sros_evidence_reliability import rubric

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
REVIEW = DOCS / "wikimedia-convergent-operator-reliability-review-v1.json"
REVIEW_MD = DOCS / "wikimedia-convergent-operator-reliability-review-v1.md"
PACKET = DOCS / "wikimedia-convergent-reliability-review-packet-v1.json"

SOURCE = "wikimedia-pageviews"
RESOURCE = "metrics/pageviews/per-article/en.wikipedia.org"
RECORD_KIND = "content_request_count"
CONVERGENT_KIND = "platform_counted_content_request_change_witnessed"
DETAILED_KIND = "platform_counted_content_request_change"


def review() -> dict:
    return json.loads(REVIEW.read_text(encoding="utf-8"))


def packet() -> dict:
    return json.loads(PACKET.read_text(encoding="utf-8"))


class TheScopeIsTheOneThatWasPrepared(unittest.TestCase):
    """The review answers the question the packet asked, not a nearby one."""

    def test_the_five_part_scope_matches_the_preparation_packet(self):
        self.assertEqual(review()["scope"], packet()["operator_worksheet"]["scope"])
        self.assertEqual(
            review()["scope"],
            {
                "source_id": SOURCE,
                "resource_id": RESOURCE,
                "record_kind_id": RECORD_KIND,
                "claim_type": "OBSERVED",
                "proposition_kind": CONVERGENT_KIND,
            },
        )

    def test_it_covers_what_the_packet_measured(self):
        covers = review()["covers"]
        measured = packet()["measured_scopes"][0]
        self.assertEqual(covers["evidence_rows"], measured["evidence_count"])
        self.assertEqual(covers["claims"], measured["claim_count"])
        self.assertEqual(sorted(covers["witness_cardinalities"]), [2, 3, 3, 3, 3, 4])

    def test_the_scope_was_not_narrowed_to_an_article_or_a_direction(self):
        """One judgement binds all six Claims; three articles is not three reviews."""
        scope = review()["scope"]
        for field in ("content_id", "direction", "audience_class", "witness_count"):
            self.assertNotIn(field, scope)
        covers = review()["covers"]
        self.assertGreater(len(covers["articles"]), 1)
        self.assertEqual(set(covers["directions"]), {"INCREASING", "DECREASING"})


class TheOperatorsAnswersAreCarriedVerbatim(unittest.TestCase):
    """§ Operator ordinal profile, material unknowns, hard stops, gate."""

    def test_the_exact_ordinal_profile(self):
        profile = {k: v for k, v in review()["rubric_profile"].items() if k != "$comment"}
        self.assertEqual(
            profile,
            {
                "MEASUREMENT_DEFINITION": "DOCUMENTED_AND_BOUNDED",
                "SOURCE_SIDE_VALIDATION": "DOCUMENTED_WITH_UNBOUNDED_LIMITATION",
                "HISTORICAL_MUTABILITY": "PARTIALLY_DOCUMENTED",
                "COMPLETENESS_AND_MISSINGNESS": "PARTIALLY_DOCUMENTED",
                "SOURCE_SIDE_CHECKABILITY": "NOT_ESTABLISHED",
            },
        )

    def test_every_state_is_one_the_rubric_defines(self):
        defined = {state.value for state in rubric.ReviewState}
        profile = {k: v for k, v in review()["rubric_profile"].items() if k != "$comment"}
        self.assertEqual(set(profile), {d.id for d in rubric.DIMENSIONS})
        for state in profile.values():
            self.assertIn(state, defined)

    def test_not_established_was_not_converted_to_a_number(self):
        """It has no ordinal rank precisely so it cannot be interpolated."""
        self.assertIsNone(rubric.ORDINAL_RANK[rubric.ReviewState.NOT_ESTABLISHED])
        profile = review()["rubric_profile"]
        self.assertEqual(profile["SOURCE_SIDE_CHECKABILITY"], "NOT_ESTABLISHED")
        note = review()["rubric_profile_note"].lower()
        for wrong in ("is 0", "= 0", "midpoint"):
            self.assertNotIn(f"not_established {wrong}", note)

    def test_the_exact_six_materiality_answers_in_order(self):
        answers = [u["reviewer_materiality"] for u in review()["material_unknowns"]]
        self.assertEqual(answers, ["YES", "YES", "NO", "NO", "UNSURE", "UNSURE"])

    def test_unsure_is_preserved_as_unsure(self):
        unsure = [u for u in review()["material_unknowns"] if u["reviewer_materiality"] == "UNSURE"]
        self.assertEqual(len(unsure), 2)
        for unknown in unsure:
            self.assertIn(unknown["reviewer_materiality"], rubric.MATERIALITY_ANSWERS)
            self.assertNotIn(unknown["reviewer_materiality"], ("YES", "NO"))

    def test_both_unsure_unknowns_survive_into_the_stated_limitation(self):
        """An UNSURE that vanishes from the limitation has been resolved silently."""
        limitation = review()["stated_limitation"].lower()
        self.assertIn("retrievability", limitation)
        self.assertIn("known-problem", limitation)

    def test_every_unknown_names_a_real_dimension(self):
        known = {d.id for d in rubric.DIMENSIONS}
        for unknown in review()["material_unknowns"]:
            self.assertIn(unknown["dimension_id"], known)

    def test_all_four_hard_stops_answered_no_and_none_triggered(self):
        answered = review()["hard_stops_answered"]
        self.assertEqual(set(answered), {stop.id for stop in rubric.HARD_STOPS})
        self.assertEqual(set(answered.values()), {"NO"})
        self.assertEqual(review()["hard_stops_triggered"], [])

    def test_checkability_not_established_was_not_read_as_the_hard_stop(self):
        """The weaker fact and the stronger claim are different answers.

        `SOURCE_SIDE_CHECKABILITY = NOT_ESTABLISHED` says the held basis does not
        establish long-term checkability. `SOURCE_OBSERVATIONS_NOT_RECOVERABLE`
        would be the claim that the observations are KNOWN to be unrecoverable.
        The reviewer answered them separately and software derived neither.
        """
        self.assertEqual(review()["rubric_profile"]["SOURCE_SIDE_CHECKABILITY"], "NOT_ESTABLISHED")
        self.assertEqual(
            review()["hard_stops_answered"]["SOURCE_OBSERVATIONS_NOT_RECOVERABLE"], "NO"
        )

    def test_the_gate_is_the_operators_and_was_not_computed(self):
        self.assertEqual(
            review()["numeric_judgement_gate"],
            rubric.NumericJudgementGate.NUMERIC_JUDGEMENT_PERMITTED.value,
        )
        # Two YES materiality answers did not automatically refuse it: the rubric
        # forbids blocking on every unknown, and the gate is a judgement.
        yes = [u for u in review()["material_unknowns"] if u["reviewer_materiality"] == "YES"]
        self.assertTrue(yes)
        self.assertNotIn("computed", review()["gate_note"].lower().split("recomputed")[0])


class TheNumberIsTheOperatorsAndNothingElse(unittest.TestCase):
    """§ Reliability value contract."""

    def test_reliability_is_exactly_zero_point_six(self):
        self.assertEqual(review()["reliability"], 0.6)

    def test_it_is_in_range_and_was_not_rounded_or_rescaled(self):
        value = review()["reliability"]
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)

    def test_it_is_not_a_copy_of_any_existing_assessment(self):
        """Copying is the failure mode the brief names, and none occurred here.

        **An arithmetic check for averaging was written, failed, and was
        removed rather than the value being questioned.** `0.6` happens to be
        exactly the midpoint of the detailed Wikimedia `0.65` and the convergent
        TED `0.55`, and that is a coincidence of two numbers rather than evidence
        of derivation: the reviewer supplied `0.6` directly, and a test that
        forbade a legitimate human choice because of what it resembles would be
        numerology dressed as a guard. **What software cannot do is prove the
        provenance of a number from the number.** Provenance comes from the
        reviewer supplying it and typing the confirmation, which is exactly why
        that keystroke exists.
        """
        value = review()["reliability"]
        self.assertNotEqual(value, 0.65)  # detailed Wikimedia, one scope field away
        self.assertNotEqual(value, 0.55)  # convergent TED
        self.assertNotEqual(value, 0.5)  # detailed TED

    def test_it_was_not_derived_from_the_ordinal_ranks(self):
        """No arithmetic over the profile could have produced it, and none ran."""
        profile = {k: v for k, v in review()["rubric_profile"].items() if k != "$comment"}
        ranks = [rubric.ORDINAL_RANK[rubric.ReviewState(state)] for state in profile.values()]
        self.assertIn(None, ranks, "an unranked state is present, so no mean exists")
        self.assertTrue(rubric.ORDINAL_RANKS_ARE_NEVER_SUMMED)

    def test_the_reviewer_is_exactly_the_supplied_identifier(self):
        self.assertEqual(review()["reviewed_by"], "thibchm")

    def test_the_origin_is_human_review(self):
        self.assertEqual(review()["origin"], ReliabilityAssessmentOrigin.HUMAN_REVIEW.value)


class TheRubricProvenanceIsRecordable(unittest.TestCase):
    """§2. And the historical rows keep their NULL."""

    def test_the_review_names_the_canonical_rubric_strings(self):
        declared = review()["review_rubric"]
        self.assertEqual(declared["id"], rubric.RUBRIC_ID)
        self.assertEqual(declared["version"], rubric.RUBRIC_VERSION)

    def test_the_historical_wikimedia_assessment_predates_the_rubric(self):
        entry = [
            e
            for e in packet()["historical_other_scope_context"]
            if e["scope"]["proposition_kind"] == DETAILED_KIND and e["scope"]["source_id"] == SOURCE
        ]
        self.assertEqual(len(entry), 1)
        self.assertIs(entry[0]["predates_the_rubric"], True)
        self.assertIsNone(entry[0]["review_rubric"])
        self.assertEqual(entry[0]["reliability"], 0.65)


class TheBasisIsDocumentBackedAndNotEngineering(unittest.TestCase):
    """§3. Two held first-party documents, and nothing fetched."""

    def test_both_basis_rows_are_real_basis_types_and_document_backed(self):
        basis = review()["basis"]
        self.assertEqual(len(basis), 2)
        for item in basis:
            ReliabilityBasisType(item["basis_type"])
            self.assertTrue(item["document_url"])
            self.assertTrue(item["retrieved_at"])
            self.assertTrue(item["summarized_finding"].strip())

    def test_the_applicability_matches_what_mission_1_44_classified(self):
        by_title = {i["document_title"]: i for i in review()["basis"]}
        prepared = {i["document_title"]: i for i in packet()["existing_basis_applicability"]}
        for title, item in by_title.items():
            self.assertIn(title, prepared)
            self.assertEqual(item["applicability_to_this_scope"], prepared[title]["verdict"])

    def test_the_documents_are_the_ones_already_held(self):
        titles = {i["document_title"] for i in review()["basis"]}
        held = {i["document_title"] for i in packet()["existing_basis_applicability"]}
        self.assertEqual(titles, held)

    def test_no_sros_engineering_validation_is_used_as_basis(self):
        rendered = json.dumps(review()["basis"]).lower()
        for phrase in (
            "mission 1.4",
            "test",
            "ci ",
            "idempotency",
            "witness-key",
            "contract is deterministic",
        ):
            self.assertNotIn(phrase, rendered)
        self.assertIn("not_reliability_basis", json.dumps(packet()).lower().replace(" ", "_"))


class NothingIsPersistedYet(unittest.TestCase):
    """The review is a proposal until the reviewer types the confirmation."""

    def test_the_artifact_says_what_it_has_not_yet_produced(self):
        self.assertIsNone(review()["persisted_assessment"])

    def test_the_drafts_are_labelled_as_not_yet_human_authored(self):
        """§ Rationale preparation. The keystroke is what converts a draft."""
        note = review()["rationale_and_limitation_note"].lower()
        self.assertIn("draft", note)
        self.assertIn("not yet human-authored", note)
        self.assertIn("confirmation", note)

    def test_the_rendered_page_says_the_scope_is_still_unresolved(self):
        text = REVIEW_MD.read_text(encoding="utf-8")
        self.assertIn("NO_APPLICABLE_ASSESSMENT", text)
        self.assertIn("NON_SCORABLE", text)


class WhatTheValueDoesNotMean(unittest.TestCase):
    """§1 labelling, asserted rather than trusted to prose."""

    def test_the_disclaimers_are_present_and_specific(self):
        rendered = " ".join(review()["what_this_is_not"]).lower()
        for phrase in (
            "not calibration",
            "not a probability",
            "not source-wide",
            "not an audience score",
            "not a product score",
            "not independent corroboration",
        ):
            self.assertIn(phrase, rendered)

    def test_it_does_not_claim_corroboration_from_witness_count(self):
        rendered = json.dumps(review()).lower()
        for phrase in ("independent corroboration is", "four independent", "corroborated by four"):
            self.assertNotIn(phrase, rendered)
        self.assertIn("witness cardinality does not establish", review()["stated_limitation"])


if __name__ == "__main__":
    unittest.main()
