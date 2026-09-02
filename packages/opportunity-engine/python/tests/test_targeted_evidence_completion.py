"""Mission 1.30 §20. Targeted evidence completion, and the bounds around it.

The subject of most of these is the CANONICAL SUBJECT REGISTRY, because it is the
one thing this mission added that could quietly become the parked classifier.
"""

from __future__ import annotations

import ast
import json
import pathlib

import pytest
from sros_opportunity import (
    SUBJECT_REGISTRY_VERSION,
    CanonicalSubject,
    CanonicalSubjectRegistry,
    EvidenceDimension,
    PacketEligibility,
    SubjectIdentifier,
    build_packet,
    evaluate,
    group_by_subject,
    load_subject_registry,
    map_signal_type,
    subject_key,
)
from sros_opportunity.mapping import COUNTING_DIMENSIONS
from sros_opportunity.sufficiency import SUFFICIENCY_PROCEDURE_VERSION, SUFFICIENCY_V1

from .test_opportunity_engine import facets

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
REGISTRY_PATH = DOCS / "canonical-subject-registry-v1.json"
PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1] / "sros_opportunity"


def registry() -> CanonicalSubjectRegistry:
    return load_subject_registry(REGISTRY_PATH)


def report() -> dict:
    return json.loads((DOCS / "opportunity-preparation-v1.json").read_text(encoding="utf-8"))


class TestTheSourceSelectionWasRecordedFirst:
    """§20. The decision exists as a document, before any derivation."""

    def test_the_selection_document_names_the_source_and_the_alternatives(self) -> None:
        doc = (DOCS / "targeted-evidence-completion-v1.md").read_text(encoding="utf-8")
        assert "Selected: `stack-exchange`" in doc
        # The matrix has to show what was rejected, or it is not a selection.
        for rejected in ("gdelt", "world-bank", "openalex", "eurostat", "ted-eu"):
            assert rejected in doc, rejected

    def test_it_states_why_no_acquisition_happened(self) -> None:
        doc = (DOCS / "targeted-evidence-completion-v1.md").read_text(encoding="utf-8")
        assert "A truncated count is not a count" in doc
        assert "did not truncate" in doc

    def test_the_dimension_was_decided_before_the_packet_was_inspected(self) -> None:
        """§16 forbids changing a mapping after seeing whether a packet passes."""
        doc = (DOCS / "targeted-evidence-completion-v1.md").read_text(encoding="utf-8")
        assert "before any Signal, Claim or Evidence was created" in doc
        assert "PROBLEM_OR_NEED" in doc


class TestDeterministicSubjectIdentity:
    """§4. A reviewed registry, matched by equality, and nothing fuzzy."""

    def test_the_registry_is_versioned_and_loads(self) -> None:
        assert registry().registry_version == SUBJECT_REGISTRY_VERSION

    def test_every_identifier_states_a_basis(self) -> None:
        for subject in registry().subjects:
            for identifier in subject.identifiers:
                assert identifier.basis.strip(), (subject.subject_id, identifier.key)

    def test_a_mapping_with_no_basis_is_refused_at_construction(self) -> None:
        with pytest.raises(ValueError, match="basis is required"):
            SubjectIdentifier(key="a:b:c", source_id="a", basis="   ")

    def test_a_subject_with_no_identifiers_is_refused(self) -> None:
        with pytest.raises(ValueError, match="maps\nnothing|maps nothing"):
            CanonicalSubject(subject_id="x", display_name="X", description="", identifiers=())

    def test_one_identifier_may_not_name_two_subjects(self) -> None:
        shared = SubjectIdentifier(key="s:k:v", source_id="s", basis="b")
        with pytest.raises(ValueError, match="names one subject"):
            CanonicalSubjectRegistry(
                registry_version="v",
                subjects=(
                    CanonicalSubject("a", "A", "", (shared,)),
                    CanonicalSubject("b", "B", "", (shared,)),
                ),
            )

    def test_matching_is_by_exact_equality_and_not_by_shape(self) -> None:
        table = registry()
        assert (
            table.subject_for("wikimedia-pageviews:content:en.wikipedia.org|Docker_(software)")
            == "docker"
        )
        # Near misses are not matches. Every one of these would be caught by a
        # similarity rule and none is caught here.
        for near in (
            "wikimedia-pageviews:content:en.wikipedia.org|Docker",
            "wikimedia-pageviews:content:de.wikipedia.org|Docker_(software)",
            "stack-exchange:community-tag:stackoverflow|Docker",
            "stack-exchange:community-tag:serverfault|docker",
            "stack-exchange:community-tag:stackoverflow|docker-compose",
        ):
            assert table.subject_for(near) is None, near

    def test_an_unmapped_identifier_keeps_its_own_packet(self) -> None:
        rows = [
            (
                facets(evidence_id="e1", claim_id="c1", source_id="world-bank"),
                {"metric_ids": ["SP.POP.TOTL"], "geography_codes": ["DE"]},
            ),
        ]
        groups = group_by_subject(rows, registry=registry())
        assert len(groups) == 1
        assert groups[0].canonical_subject_id is None

    def test_passing_no_registry_reproduces_the_previous_behaviour(self) -> None:
        rows = [
            (
                facets(evidence_id="e1", claim_id="c1"),
                {"content_ids": ["Docker_(software)"], "content_platforms": ["en.wikipedia.org"]},
            ),
        ]
        without = group_by_subject(rows)
        assert without[0].label.startswith("wikimedia-pageviews:")
        assert without[0].canonical_subject_id is None

    def test_the_registry_module_has_no_similarity_machinery(self) -> None:
        """No distance, no stem, no synonym expansion, no threshold."""
        source = (PACKAGE_ROOT / "subjects.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in ("difflib", "re", "Levenshtein")
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "") not in ("difflib", "re")

    def test_the_registry_refuses_to_merge_the_three_subjects(self) -> None:
        """Docker, Podman and Kubernetes are three subjects and stay three."""
        raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        ids = {s["subject_id"] for s in raw["subjects"]}
        assert ids == {"docker", "kubernetes", "podman"}
        assert "container_tooling" in raw["deliberately_absent"]
        assert "docker_compose" in raw["deliberately_absent"]

    def test_the_parked_classifier_is_not_reachable_from_the_package(self) -> None:
        for path in sorted(PACKAGE_ROOT.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "semantic_equivalence" not in alias.name, path.name
                if isinstance(node, ast.ImportFrom):
                    assert "semantic_equivalence" not in (node.module or ""), path.name


class TestTheNewDimensionMapping:
    """§12. Warranted, bounded, and with the negative boundaries asserted."""

    def test_question_volume_maps_to_problem_or_need(self) -> None:
        mapping = map_signal_type("community_question_volume")
        assert mapping is not None
        assert mapping.dimensions == frozenset({EvidenceDimension.PROBLEM_OR_NEED})

    def test_it_does_not_claim_recurrence(self) -> None:
        """The mapping a reader most wants, and the one the parked relation owns."""
        mapping = map_signal_type("community_question_volume")
        assert mapping is not None
        assert EvidenceDimension.RECURRENCE_OR_FREQUENCY not in mapping.dimensions
        assert "PARKED" in mapping.rationale

    def test_it_claims_no_commercial_dimension(self) -> None:
        mapping = map_signal_type("community_question_volume")
        assert mapping is not None
        for forbidden in (
            EvidenceDimension.WILLINGNESS_TO_PAY,
            EvidenceDimension.MARKET_ACTIVITY,
            EvidenceDimension.ECONOMIC_VALUE,
            EvidenceDimension.BUYER_OR_BUDGET_EXISTENCE,
            EvidenceDimension.COMPETITIVE_SUPPLY,
        ):
            assert forbidden not in mapping.dimensions, forbidden

    def test_the_bound_names_every_over_reading(self) -> None:
        mapping = map_signal_type("community_question_volume")
        assert mapping is not None
        bound = mapping.bound
        for refusal in (
            "NOT a count of PEOPLE",
            "share a",
            "severity",
            "demand",
            "willingness to pay",
            "SUBJECT, not a problem",
        ):
            assert refusal in bound, refusal

    def test_it_is_a_different_dimension_from_the_pageview_one(self) -> None:
        """The whole point of the mission: a genuinely new counting dimension."""
        question = map_signal_type("community_question_volume")
        pageview = map_signal_type("content_request_change")
        assert question is not None and pageview is not None
        counting_q = question.dimensions & COUNTING_DIMENSIONS
        counting_p = pageview.dimensions & COUNTING_DIMENSIONS
        assert counting_q and counting_p
        assert not (counting_q & counting_p)


class TestTheFrozenSufficiencyRuleIsUnchanged:
    """§16. The gate did not move; the evidence did."""

    def test_the_procedure_version_is_unchanged(self) -> None:
        assert SUFFICIENCY_PROCEDURE_VERSION == "opportunity-sufficiency@1.0.0"
        assert SUFFICIENCY_V1.min_eligible_rows == 2
        assert SUFFICIENCY_V1.min_distinct_dimensions == 2

    def test_trend_or_change_still_does_not_count(self) -> None:
        assert EvidenceDimension.TREND_OR_CHANGE not in COUNTING_DIMENSIONS

    def test_a_packet_of_pageviews_alone_is_still_insufficient(self) -> None:
        """The Kubernetes and Podman shape. Adding the registry did not help
        them, and it must not."""
        rows = tuple(
            (
                facets(
                    evidence_id=f"e{i}",
                    claim_id=f"c{i}",
                    dimensions=frozenset(
                        {EvidenceDimension.AUDIENCE_OR_USAGE, EvidenceDimension.TREND_OR_CHANGE}
                    ),
                ),
                PacketEligibility.ELIGIBLE_CONTEXT,
            )
            for i in range(6)
        )
        result = evaluate(build_packet(None, "subject:kubernetes", rows))
        assert result.status.value == "HYPOTHESIS_INSUFFICIENT_EVIDENCE"


class TestTheRealRun:
    """§15 and §21, over the committed artifact."""

    def test_one_packet_became_formable(self) -> None:
        totals = report()["totals"]
        assert totals["packets_built"] == 9
        assert totals["packets_formable"] == 1

    def test_the_formable_packet_is_docker_and_spans_two_source_families(self) -> None:
        formable = [
            p for p in report()["packets"] if p["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
        ]
        assert len(formable) == 1
        packet = formable[0]
        assert packet["canonical_subject_id"] == "docker"
        assert packet["source_families"] == ["forum", "knowledge"]
        assert sorted(packet["counting_dimensions"]) == ["AUDIENCE_OR_USAGE", "PROBLEM_OR_NEED"]

    def test_it_is_formable_and_not_scoring_ready(self) -> None:
        """§13. ELIGIBLE_CONTEXT does not become ELIGIBLE_SCORING."""
        packet = next(
            p for p in report()["packets"] if p["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
        )
        assert packet["scoring_eligible"] == 0
        assert packet["sufficiency"]["scoring_ready"] is False
        assert report()["totals"]["eligible_scoring"] == 0

    def test_independence_is_still_unknown_across_two_families(self) -> None:
        """§14. Two source families is diversity, not established independence."""
        packet = next(
            p for p in report()["packets"] if p["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
        )
        assert "independence is UNKNOWN for 7 of 7" in packet["independence"]
        assert "independent sources" not in packet["independence"]

    def test_the_formable_packet_is_egress_authorized(self) -> None:
        """§17. Deterministic check only; nothing was serialised or sent."""
        packet = next(
            p for p in report()["packets"] if p["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
        )
        assert packet["external_synthesis"]["availability"] == "AVAILABLE"

    def test_no_model_call_and_no_opportunity(self) -> None:
        totals = report()["totals"]
        assert totals["model_calls"] == 0
        assert totals["cost_units"] == 0.0
        assert totals["opportunity_hypotheses_generated"] == 0

    def test_exactly_one_evidence_row_was_added(self) -> None:
        """§21. 26 -> 27, and no synthetic evidence."""
        totals = report()["totals"]
        assert totals["evidence_rows_inspected"] == 27
        assert totals["eligible_context"] == 27

    def test_the_run_records_the_registry_it_grouped_under(self) -> None:
        assert report()["procedures"]["subject_registry"] == SUBJECT_REGISTRY_VERSION
        assert report()["procedures"]["grouping"] == "source-native-subject-grouping@1.1.0"
        assert report()["procedures"]["sufficiency"] == "opportunity-sufficiency@1.0.0"


class TestTheSubjectKeyRuleForCommunityTags:
    """The new source-native key, before any registry is consulted."""

    def test_the_key_carries_the_site_and_the_tag(self) -> None:
        key = subject_key(
            "stack-exchange",
            "community_question_volume",
            {"community_tags": ["docker"], "community_sites": ["stackoverflow"]},
        )
        assert key is not None
        assert str(key) == "stack-exchange:community-tag:stackoverflow|docker"

    def test_the_same_tag_on_two_sites_is_two_keys(self) -> None:
        one = subject_key(
            "stack-exchange",
            "community_question_volume",
            {"community_tags": ["docker"], "community_sites": ["stackoverflow"]},
        )
        two = subject_key(
            "stack-exchange",
            "community_question_volume",
            {"community_tags": ["docker"], "community_sites": ["serverfault"]},
        )
        assert one != two

    def test_a_scope_with_no_tag_has_no_key(self) -> None:
        assert (
            subject_key("stack-exchange", "community_question_volume", {"community_sites": ["x"]})
            is None
        )
