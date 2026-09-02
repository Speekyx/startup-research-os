"""Mission 1.32 §18. The acceptance measurement, and everything it may not become.

Most of these guard a single inference: **no accepted answer does not mean the
problem is unsolved.** It is the most natural reading of the field, it is wrong,
and the source itself says so in the payload beside the value.
"""

from __future__ import annotations

import ast
import json
import pathlib

from sros_opportunity import (
    EvidenceDimension,
    HypothesisStatus,
    PacketEligibility,
    build_packet,
    evaluate,
    map_signal_type,
)
from sros_opportunity.mapping import COUNTING_DIMENSIONS
from sros_opportunity.sufficiency import SUFFICIENCY_PROCEDURE_VERSION, SUFFICIENCY_V1

from .test_opportunity_engine import facets

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1] / "sros_opportunity"
SIGNAL_TYPE = "community_question_without_accepted_answer_volume"


def report() -> dict:
    return json.loads((DOCS / "opportunity-preparation-v1.json").read_text(encoding="utf-8"))


def docker_packet() -> dict:
    return next(p for p in report()["packets"] if p.get("canonical_subject_id") == "docker")


class TestTheAssessmentWasFrozenFirst:
    """§0. The semantics were decided before any Signal existed."""

    def test_the_assessment_document_exists_and_decides(self) -> None:
        doc = (DOCS / "answer-acceptance-semantics-v1.md").read_text(encoding="utf-8")
        assert "written before any Signal, Claim, Evidence or dimension" in doc
        assert "NO_EXISTING_DIMENSION" in doc

    def test_it_answers_both_candidate_dimensions_explicitly(self) -> None:
        doc = (DOCS / "answer-acceptance-semantics-v1.md").read_text(encoding="utf-8")
        assert "Sufficient for `SOLUTION_GAP`? **No.**" in doc
        assert "Sufficient for `SOLUTION_DISSATISFACTION`? **No" in doc

    def test_it_records_the_split_that_decided_it(self) -> None:
        """16 zero-answer and 38 answered-but-unaccepted are different facts, and
        a single count of 54 conflates them."""
        doc = (DOCS / "answer-acceptance-semantics-v1.md").read_text(encoding="utf-8")
        for number in ("34", "38", "16", "54", "88"):
            assert number in doc, number


class TestTheDimensionMappingIsEmptyAndSaysWhy:
    """§9, §10. Zero dimensions is a decision, not a gap."""

    def test_it_maps_to_no_dimension(self) -> None:
        mapping = map_signal_type(SIGNAL_TYPE)
        assert mapping is not None
        assert mapping.dimensions == frozenset()

    def test_it_is_a_registered_decision_and_not_an_unknown_type(self) -> None:
        """`None` means nobody decided; `frozenset()` means somebody decided nothing."""
        assert map_signal_type(SIGNAL_TYPE) is not None
        assert map_signal_type("some_future_type") is None

    def test_the_rationale_names_both_rejected_dimensions(self) -> None:
        mapping = map_signal_type(SIGNAL_TYPE)
        assert mapping is not None
        assert "SOLUTION_GAP" in mapping.rationale
        assert "SOLUTION_DISSATISFACTION" in mapping.rationale
        assert "RECURRENCE_OR_FREQUENCY" in mapping.rationale

    def test_the_rationale_quotes_the_dimension_guard_it_fails(self) -> None:
        """SOLUTION_GAP's own never_means settles it, and the mapping says so."""
        mapping = map_signal_type(SIGNAL_TYPE)
        assert mapping is not None
        assert "absence of evidence of a solution is evidence of its absence" in (mapping.rationale)

    def test_no_dimension_was_invented_for_this_source(self) -> None:
        """§9. The taxonomy has exactly the fourteen it had."""
        assert len(EvidenceDimension) == 14
        for invented in (
            "UNANSWERED_VOLUME",
            "UNSOLVED_PROBLEM",
            "ACCEPTANCE_RATE",
            "COMMUNITY_RESPONSE",
        ):
            assert invented not in {d.value for d in EvidenceDimension}


class TestUnacceptedIsNotTheThingsItLooksLike:
    """§1, §10. The forbidden implications, each asserted separately."""

    def _text(self) -> str:
        mapping = map_signal_type(SIGNAL_TYPE)
        assert mapping is not None
        doc = (DOCS / "answer-acceptance-semantics-v1.md").read_text(encoding="utf-8")
        return mapping.rationale + doc

    def test_unaccepted_is_not_unsolved(self) -> None:
        assert "objectively resolved" in self._text() or "unsolved" in self._text().lower()

    def test_unaccepted_is_not_dissatisfaction(self) -> None:
        assert "no dissatisfaction datum" in self._text()

    def test_unaccepted_is_not_willingness_to_pay(self) -> None:
        assert "not willingness to pay" in self._text()

    def test_unaccepted_is_not_recurrence(self) -> None:
        text = self._text()
        assert "PARKED" in text or "parked" in text
        assert "RECURRENCE_OR_FREQUENCY" in text

    def test_zero_answers_is_named_and_still_refused(self) -> None:
        """The sharpest subset, and it still does not reach SOLUTION_GAP."""
        doc = (DOCS / "answer-acceptance-semantics-v1.md").read_text(encoding="utf-8")
        assert "zero answers" in doc
        assert "does not rescue it" in doc


class TestTheRealRun:
    """§13, §19. Over the committed preparation artifact."""

    def test_the_docker_packet_gained_exactly_one_row(self) -> None:
        assert docker_packet()["size"] == 8

    def test_the_new_signal_type_is_in_the_packet(self) -> None:
        assert SIGNAL_TYPE in docker_packet()["signal_type_ids"]

    def test_the_counting_dimensions_did_not_change(self) -> None:
        """§9 outcome B: new Evidence, no new dimension."""
        assert sorted(docker_packet()["counting_dimensions"]) == [
            "AUDIENCE_OR_USAGE",
            "PROBLEM_OR_NEED",
        ]

    def test_the_packet_is_still_formable_and_still_not_scoring_ready(self) -> None:
        packet = docker_packet()
        assert packet["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
        assert packet["sufficiency"]["scoring_ready"] is False
        assert packet["scoring_eligible"] == 0

    def test_every_row_including_the_new_one_is_context_only(self) -> None:
        """§8. No ReliabilityAssessment was manufactured."""
        assert docker_packet()["eligibility_counts"] == {"ELIGIBLE_CONTEXT": 8}
        assert report()["totals"]["eligible_scoring"] == 0

    def test_independence_is_still_unknown_on_all_eight(self) -> None:
        """§17. A second measurement over the SAME corpus is not independent."""
        packet = docker_packet()
        assert "independence is UNKNOWN for 8 of 8" in packet["independence"]
        assert "independent sources" not in packet["independence"]

    def test_the_source_family_count_did_not_change(self) -> None:
        """Still two: the new row comes from a source already in the packet."""
        assert docker_packet()["source_families"] == ["forum", "knowledge"]

    def test_it_is_still_egress_authorized(self) -> None:
        assert docker_packet()["external_synthesis"]["availability"] == "AVAILABLE"

    def test_no_model_call_and_no_opportunity_was_created(self) -> None:
        """§14, §16. Evidence changed; no synthesis was run."""
        totals = report()["totals"]
        assert totals["model_calls"] == 0
        assert totals["cost_units"] == 0.0
        assert totals["opportunity_hypotheses_generated"] == 0


class TestFrozenThingsStayedFrozen:
    """§13, §16, §11."""

    def test_the_sufficiency_rule_is_unchanged(self) -> None:
        assert SUFFICIENCY_PROCEDURE_VERSION == "opportunity-sufficiency@1.0.0"
        assert SUFFICIENCY_V1.min_eligible_rows == 2
        assert SUFFICIENCY_V1.min_distinct_dimensions == 2

    def test_trend_or_change_still_does_not_count(self) -> None:
        assert EvidenceDimension.TREND_OR_CHANGE not in COUNTING_DIMENSIONS

    def test_a_zero_dimension_row_cannot_make_a_packet_formable(self) -> None:
        """The property that makes outcome B honest: an unmapped row adds rows
        and never diversity."""
        rows = tuple(
            (
                facets(evidence_id=f"e{i}", claim_id=f"c{i}", dimensions=frozenset()),
                PacketEligibility.ELIGIBLE_CONTEXT,
            )
            for i in range(9)
        )
        result = evaluate(build_packet(None, "s", rows))
        assert result.status is HypothesisStatus.HYPOTHESIS_INSUFFICIENT_EVIDENCE

    def test_the_canonical_subject_is_unchanged(self) -> None:
        registry = json.loads(
            (DOCS / "canonical-subject-registry-v1.json").read_text(encoding="utf-8")
        )
        ids = {s["subject_id"] for s in registry["subjects"]}
        assert ids == {"docker", "kubernetes", "podman"}

    def test_the_parked_classifier_is_unreachable(self) -> None:
        for path in sorted(PACKAGE_ROOT.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "semantic_equivalence" not in alias.name, path.name
                if isinstance(node, ast.ImportFrom):
                    assert "semantic_equivalence" not in (node.module or ""), path.name

    def test_the_opportunity_history_is_preserved(self) -> None:
        """§14. No revision was created merely because Evidence changed."""
        for name in ("opportunity-synthesis-run-v1.json", "opportunity-synthesis-run-v1.1.json"):
            artifact = json.loads((DOCS / name).read_text(encoding="utf-8"))
            assert artifact["packet_id"], name
        historical = json.loads(
            (DOCS / "opportunity-synthesis-run-v1.json").read_text(encoding="utf-8")
        )
        assert historical["persistence"]["persist"] is False
