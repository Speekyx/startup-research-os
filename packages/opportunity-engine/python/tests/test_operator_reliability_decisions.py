"""Mission 1.36.1 §23. Three operator decisions, and what only one of them changed.

**These test what is TRUE.** The first version of this file was written before
the operator confirmed, so it asserted that nothing resolved and that the TED
assessment was the only one -- correct then, and a test claiming six rows resolve
would have been asserting a future. The operator has since typed `record it`, so
two assertions were re-pointed at the new present and every other one is
unchanged, because everything else really did stay put.

What did NOT move is the interesting half: `scoring.evidence.reliability` is
still NULL on all eight rows (reliability binds late, ADR-026), both Stack
Exchange scopes still have no assessment, the TED assessment is untouched at
version 1, and the negative checks still find no leak -- now over six checks
rather than three, because a second assessment doubled the ways one could leak.
"""

from __future__ import annotations

import json
import pathlib

from sros_contracts import ReliabilityBasisType

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
REVIEW = DOCS / "docker-wikimedia-reliability-review-v1.json"
PACKET = DOCS / "docker-evidence-reliability-review-packet-v1.json"
RESOLUTION = DOCS / "docker-reliability-resolution-v1.json"
DIAGNOSTIC = DOCS / "docker-diagnostic-aggregation-v1.json"
DECISIONS = DOCS / "docker-reliability-operator-decisions-v1.md"
PREPARATION = DOCS / "opportunity-preparation-v1.json"

SCOPE_FIELDS = (
    "source_id",
    "resource_id",
    "record_kind_id",
    "claim_type",
    "proposition_kind",
)

SCOPE_3 = {
    "source_id": "wikimedia-pageviews",
    "resource_id": "metrics/pageviews/per-article/en.wikipedia.org",
    "record_kind_id": "content_request_count",
    "claim_type": "OBSERVED",
    "proposition_kind": "platform_counted_content_request_change",
}


def review() -> dict:
    return json.loads(REVIEW.read_text(encoding="utf-8"))


def packet() -> dict:
    return json.loads(PACKET.read_text(encoding="utf-8"))


def resolution() -> dict:
    return json.loads(RESOLUTION.read_text(encoding="utf-8"))


def diagnostic() -> dict:
    return json.loads(DIAGNOSTIC.read_text(encoding="utf-8"))


def decisions() -> str:
    """Whitespace-collapsed, because a sentence is a sentence whether or not the
    markdown source wrapped it at 80 columns."""
    return " ".join(DECISIONS.read_text(encoding="utf-8").split())


# ================================================== the operator's own judgement


class TestScopeThreeCarriesExactlyWhatTheOperatorSaid:
    def test_the_scope_is_mission_1_36_scope_3_unchanged(self) -> None:
        assert review()["scope"] == SCOPE_3

    def test_the_scope_still_matches_the_packet(self) -> None:
        """§0. A decision made about a drifted scope is a decision about
        something else."""
        prepared = next(
            s["scope"]
            for s in packet()["scopes"]
            if s["scope"]["source_id"] == "wikimedia-pageviews"
        )
        for field in SCOPE_FIELDS:
            assert prepared[field] == SCOPE_3[field], field

    def test_reliability_is_exactly_the_operator_value(self) -> None:
        """Not normalised, not rounded, not relabelled."""
        assert review()["reliability"] == 0.65
        assert 0.0 <= review()["reliability"] <= 1.0

    def test_the_reviewer_is_the_named_person(self) -> None:
        assert review()["reviewed_by"] == "thibchm"

    def test_the_origin_is_human_review(self) -> None:
        assert review()["origin"] == "HUMAN_REVIEW"

    def test_the_rationale_is_the_operator_text(self) -> None:
        assert review()["rationale"].startswith(
            "The Wikimedia pageview measurement has documented first-party counting rules"
        )
        assert "documented methodology and a bounded meaning" in review()["rationale"]

    def test_the_limitation_names_both_failure_modes(self) -> None:
        limitation = review()["stated_limitation"]
        assert limitation.startswith("Automated traffic detection is heuristic")
        assert "revision/backfill policy" in limitation

    def test_there_is_no_calibration_dataset(self) -> None:
        """A `HUMAN_REVIEW` assessment may not name one; that belongs to
        `CALIBRATED_EMPIRICALLY` alone."""
        assert "calibration_dataset_ref" not in review()

    def test_the_value_carries_no_invented_label(self) -> None:
        """§3. The contract has no threshold vocabulary."""
        text = json.dumps(review()).lower()
        for label in ("good", "medium reliability", "high reliability", "65%", "confident"):
            assert label not in text, label

    def test_the_basis_is_document_backed_and_reused(self) -> None:
        """§4. The prepared rows, not replacement documentation."""
        prepared = next(
            s for s in packet()["scopes"] if s["scope"]["source_id"] == "wikimedia-pageviews"
        )["candidate_basis_rows"]
        assert review()["basis"]
        assert len(review()["basis"]) == len(prepared)
        for row, source in zip(review()["basis"], prepared, strict=True):
            assert row["document_title"] == source["document_title"]
            assert row["summarized_finding"] == source["summarized_finding"]
            assert row["document_url"].startswith("https://")
            assert row["retrieved_at"] == "2026-09-03"

    def test_every_basis_type_is_a_real_contract_member(self) -> None:
        """The defect Mission 1.36 shipped and this mission found: the packet's
        candidate rows carried invented strings, so the rows it prepared could
        not have recorded an assessment -- which is what they are for."""
        known = {m.value for m in ReliabilityBasisType}
        for row in review()["basis"]:
            assert row["basis_type"] in known, row["basis_type"]
        for scope in packet()["scopes"]:
            for row in scope["candidate_basis_rows"]:
                assert row["basis_type"] in known, (scope["scope"], row["basis_type"])

    def test_the_file_records_that_the_judgement_is_the_operator_s(self) -> None:
        provenance = " ".join(review()["_provenance"])
        assert "OPERATOR'S" in provenance
        assert "thibchm" in provenance
        assert "Software chose no value" in provenance


# ===================================================== scopes 1 and 2 stay absent


class TestTheRefusalsCreatedNothing:
    """§1, §2, §8. A NO is not a number."""

    def test_no_assessment_exists_for_either_stack_exchange_scope(self) -> None:
        for entry in resolution()["by_scope"]:
            if entry["source_id"] == "stack-exchange":
                assert entry["outcomes"] == ["NO_APPLICABLE_ASSESSMENT"]
                assert entry["reliability"] == ["None"]

    def test_the_two_current_assessments_are_ted_and_wikimedia_and_nothing_else(self) -> None:
        """Two scopes reviewed, three scopes in use. The Stack Exchange pair has
        no row at all, which is what a NO leaves behind."""
        current = resolution()["current_assessments"]
        assert {a["source_id"] for a in current} == {"ted-eu", "wikimedia-pageviews"}
        assert len(current) == 2
        for a in current:
            assert a["version"] == 1, a
            assert a["origin"] == "HUMAN_REVIEW", a
            assert a["reviewed_by"] == "thibchm", a

    def test_the_ted_assessment_was_not_superseded_by_the_new_one(self) -> None:
        """A new scope is a new line, never a revision of somebody else's."""
        ted = next(a for a in resolution()["current_assessments"] if a["source_id"] == "ted-eu")
        assert ted["proposition_kind"] == "source_reported_procurement_value_contrast"
        assert ted["version"] == 1

    def test_the_refusal_is_recorded_as_prose_and_not_as_data(self) -> None:
        text = decisions()
        assert "no human reliability judgement exists" in text.lower()
        for misreading in ("`reliability = 0`", "`reliability = 0.5`"):
            assert misreading in text, misreading
        assert "It does **not** mean" in text

    def test_the_decisions_document_names_the_unresolved_questions(self) -> None:
        text = decisions()
        assert "whether tags may change after publication" in text
        assert "whether accepted-answer state can later change" in text


# ================================================== nothing leaked, nothing moved


class TestNothingLeakedAndNothingMoved:
    def test_the_negative_checks_ran_and_found_no_leak(self) -> None:
        """§10. The TED assessment must not reach a Docker scope."""
        negatives = resolution()["negative_checks"]
        assert negatives
        leaks = [n for n in negatives if n["resolved"] and not n["scopes_are_identical"]]
        assert leaks == []

    def test_six_rows_resolve_and_the_two_refused_scopes_do_not(self) -> None:
        """1 + 1 + 6 = 8, and the split follows the operator's decisions exactly."""
        totals = resolution()["totals"]
        assert totals["docker_evidence_rows"] == 8
        assert totals["resolved"] == 6
        assert totals["no_applicable_assessment"] == 2
        for row in resolution()["rows"]:
            if row["outcome"] == "RESOLVED":
                assert row["scope"]["source_id"] == "wikimedia-pageviews"
                assert row["reliability"] == 0.65
                assert row["assessment_version"] == 1
                assert row["assessment_origin"] == "HUMAN_REVIEW"
                assert row["reviewed_by"] == "thibchm"
            else:
                assert row["scope"]["source_id"] == "stack-exchange"
                assert row["reliability"] is None

    def test_all_six_resolved_rows_bind_the_same_single_assessment(self) -> None:
        """One scope, one assessment. Six bindings to six ids would mean the
        scope key was not doing its job."""
        bound = {r["assessment_id"] for r in resolution()["rows"] if r["outcome"] == "RESOLVED"}
        assert len(bound) == 1

    def test_the_evidence_reliability_column_is_null_everywhere(self) -> None:
        """§11. Reliability is late-bound and the column stays NULL."""
        assert resolution()["totals"]["evidence_rows_with_non_null_reliability_column"] == 0
        for row in resolution()["rows"]:
            assert row["evidence_row_reliability_column"] is None

    def test_the_opportunity_is_untouched(self) -> None:
        """§13. Reliability changing does not change what a hypothesis said."""
        report = json.loads(PREPARATION.read_text(encoding="utf-8"))
        packet_row = next(p for p in report["packets"] if p.get("canonical_subject_id") == "docker")
        assert packet_row["size"] == 8
        assert packet_row["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
        assert report["totals"]["opportunity_hypotheses_generated"] == 0

    def test_no_score_and_no_ranking_appear_anywhere(self) -> None:
        """§14. `scoring.scores` does not exist and nothing here creates one."""
        text = json.dumps(resolution()) + decisions()
        for forbidden in ("OpportunityScore", "RankingScore", "PriorityScore", "MarketScore"):
            assert forbidden not in text, forbidden

    def test_the_decisions_document_refuses_a_subject_wide_coefficient(self) -> None:
        """§16. Six rows matching one scope do not make 0.65 a Docker number."""
        text = decisions()
        assert "no average reliability" in text
        assert "*Docker 65%*" in text
        assert "scopes 1 and 2 remain **unknown**, and unknown is not a low number" in text

    def test_it_states_that_a_value_does_not_calibrate(self) -> None:
        """§14, §19."""
        text = decisions()
        assert "stays `UNCALIBRATED`" in text

    def test_independence_is_not_touched(self) -> None:
        """§17."""
        text = decisions()
        assert "does not establish independence" in text
        assert "`UNKNOWN` on all eight rows" in text


# ====================================================== the confirmation guard


class TestTheConfirmationGuardWasRespected:
    """§7. The one control that makes `reviewed_by` mean anything."""

    def test_the_document_records_the_guard_refusing(self) -> None:
        text = decisions()
        assert "no terminal to confirm on" in text
        assert "this is not a step a pipeline runs" in text

    def test_it_prints_the_exact_command_for_the_operator(self) -> None:
        text = decisions()
        assert "record_reliability_assessment.py --review-file" in text
        assert "docker-wikimedia-reliability-review-v1.json --apply" in text
        assert "type `record it`" in text

    def test_the_recording_tool_still_requires_a_typed_confirmation(self) -> None:
        """A guard removed to make a pipeline pass is a guard that never was."""
        tool = (
            REPO_ROOT / "infrastructure" / "scripts" / "record_reliability_assessment.py"
        ).read_text(encoding="utf-8")
        assert 'CONFIRMATION = "record it"' in tool
        assert "input(" in tool
        assert "no terminal to confirm on" in tool

    def test_nothing_in_this_mission_pipes_the_confirmation(self) -> None:
        """The bypass §7 forbids by name."""
        for path in (DECISIONS, REVIEW):
            text = path.read_text(encoding="utf-8")
            assert "echo 'record it'" not in text
            assert 'echo "record it"' not in text


# ===================================== §15, now that its precondition is true


class TestTheDiagnosticAggregation:
    """§15 was conditional on at least one row becoming scorable. Six did.

    Every assertion here is about the diagnostic staying a diagnostic.
    """

    def test_every_output_carries_the_three_required_words(self) -> None:
        assert diagnostic()["$banner"] == [
            "UNCALIBRATED",
            "DIAGNOSTIC ONLY",
            "NOT AN OPPORTUNITY SCORE",
        ]
        for entry in diagnostic()["scorable"] + diagnostic()["unavailable"]:
            assert entry["$banner"] == diagnostic()["$banner"], entry["claim_id"]

    def test_the_profile_is_still_uncalibrated(self) -> None:
        """A reviewed value is not a fitted parameter. D-03 is not resolved."""
        assert diagnostic()["profile"]["status"] == "UNCALIBRATED"
        for entry in diagnostic()["scorable"]:
            assert entry["profile_status"] == "UNCALIBRATED"
            assert entry["calibrated"] is False

    def test_nothing_was_persisted(self) -> None:
        totals = diagnostic()["totals"]
        assert totals["opportunity_scores_created"] == 0
        assert totals["rows_persisted"] == 0

    def test_it_is_eight_single_record_aggregations_not_one(self) -> None:
        """Reliability resolving does not turn six observations of one article
        into an aggregation. Eight Evidence rows, eight distinct Claims."""
        totals = diagnostic()["totals"]
        assert totals["claims_aggregated"] == 8
        assert totals["evidence_rows_per_claim"] == 1
        claims = {e["claim_id"] for e in diagnostic()["scorable"] + diagnostic()["unavailable"]}
        assert len(claims) == 8
        for entry in diagnostic()["scorable"] + diagnostic()["unavailable"]:
            assert entry["evidence_considered"] == 1

    def test_reliability_is_the_limiting_component_on_every_scorable_claim(self) -> None:
        """`q_i = min(components)`, and every other factor is 1.0 on these rows,
        so the reviewed value is exactly what the score is made of."""
        assert len(diagnostic()["scorable"]) == 6
        for entry in diagnostic()["scorable"]:
            assert entry["limiting_component"] == "reliability"
            assert entry["q"] == 0.65
            assert entry["components"]["reliability"] == 0.65
            for name in ("relevance", "directness", "extraction_confidence"):
                assert entry["components"][name] == 1.0, name

    def test_the_two_refused_scopes_are_reported_separately_and_score_nothing(self) -> None:
        """§15 asks for them apart, because a claim with no reviewed reliability
        is a different state from a claim with a low one."""
        unavailable = diagnostic()["unavailable"]
        assert len(unavailable) == 2
        for entry in unavailable:
            assert entry["source_id"] == "stack-exchange"
            assert entry["aggregation_status"] == "UNAVAILABLE"
            assert entry["q"] is None
            assert entry["non_scorable_reasons"] == ["MISSING_RELIABILITY"]
            assert entry["uncertainty_mass"] == 1.0
            assert entry["evidence_level"]["evidence_level"] == 0

    def test_a_reviewed_value_did_not_raise_the_evidence_level(self) -> None:
        """Level stays 1. The category gate and unknown independence both hold,
        and reliability cannot reach either of them -- the same result Mission
        1.15.13 recorded for TED at a different number."""
        for entry in diagnostic()["scorable"]:
            assert entry["evidence_level"]["evidence_level"] == 1
            assert entry["independence_state"] == "UNKNOWN"
            assert entry["independence_group_count"] <= 1
            blocked = " ".join(entry["evidence_level"]["blocked_reasons"])
            assert "established independence" in blocked
            assert "MARKET_ACTIVITY" in blocked

    def test_uncertainty_is_reported_rather_than_absorbed(self) -> None:
        """The four masses sum to 1 and none of them is a probability."""
        for entry in diagnostic()["scorable"]:
            total = (
                entry["supported_mass"]
                + entry["contradicted_mass"]
                + entry["conflict_mass"]
                + entry["uncertainty_mass"]
            )
            assert abs(total - 1.0) < 1e-9
            assert entry["uncertainty_mass"] > 0.0
            assert entry["contradiction_strength"] == 0.0
