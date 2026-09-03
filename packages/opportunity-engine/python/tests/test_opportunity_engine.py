"""Mission 1.28 §19. Regression tests for the Opportunity Engine foundation.

Each class corresponds to a property the engine must keep, and most of them
exist because the opposite behaviour is the natural thing to write.
"""

from __future__ import annotations

import ast
import json
import pathlib

import pytest
from sros_opportunity import (
    COUNTING_DIMENSIONS,
    DIMENSION_DEFINITIONS,
    DIMENSION_MAP_VERSION,
    DIMENSION_TAXONOMY_VERSION,
    SUFFICIENCY_V1,
    VALIDATION_WORDS,
    EvidenceDimension,
    EvidenceFacets,
    ExternalSynthesisRefusedError,
    HypothesisStatus,
    IndependenceState,
    OpportunityHypothesis,
    OpportunityStatus,
    PacketEligibility,
    ReliabilityStatus,
    SourcePolicyStanding,
    SynthesisAvailability,
    assess_eligibility,
    authorize_packet_for_external_synthesis,
    build_packet,
    check_no_validation_language,
    check_statement,
    evaluate,
    group_by_subject,
    map_signal_type,
    subject_key,
)

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1] / "sros_opportunity"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"


def facets(**overrides: object) -> EvidenceFacets:
    """A row that is eligible-as-context by default, so a test changes one thing."""
    base: dict[str, object] = dict(
        evidence_id="e1",
        claim_id="c1",
        source_id="wikimedia-pageviews",
        source_family="knowledge",
        use_profile_id="local-private-research-v1",
        extraction_method="deterministic",
        claim_type="OBSERVED",
        claim_lifecycle="ACTIVE",
        claim_temporality="EVERGREEN",
        claim_origin="DETERMINISTIC_EXTRACTION",
        direction="SUPPORTS",
        observation_category="UNCATEGORISED",
        evidence_level=1,
        relevance=1.0,
        directness=1.0,
        extraction_confidence=1.0,
        reliability=None,
        reliability_status=ReliabilityStatus.NO_APPLICABLE_ASSESSMENT,
        independence_state=IndependenceState.UNKNOWN,
        independence_group_id=None,
        observed_at=None,
        signal_type_id="content_request_change",
        dimensions=frozenset({EvidenceDimension.AUDIENCE_OR_USAGE}),
        dimension_bound="requests for one article on one wiki in one day",
    )
    base.update(overrides)
    return EvidenceFacets(**base)  # type: ignore[arg-type]


def standing(**overrides: object) -> SourcePolicyStanding:
    base: dict[str, object] = dict(
        source_id="wikimedia-pageviews",
        use_profile_id="local-private-research-v1",
        permits_local_processing=True,
        permits_external_model_transmission=None,
        basis="local review v1: APPROVED_WITH_CONDITIONS",
    )
    base.update(overrides)
    return SourcePolicyStanding(**base)  # type: ignore[arg-type]


class TestDimensionMapping:
    """§3. The taxonomy is versioned and every mapping states its bounds."""

    def test_the_taxonomy_and_map_are_versioned(self) -> None:
        assert DIMENSION_TAXONOMY_VERSION == "opportunity-evidence-dimensions@1.0.0"
        assert DIMENSION_MAP_VERSION == "signal-type-dimension-map@1.0.0"

    def test_every_dimension_states_what_it_never_means(self) -> None:
        """The over-readings are the failure mode, so they are required data."""
        assert set(DIMENSION_DEFINITIONS) == set(EvidenceDimension)
        for definition in DIMENSION_DEFINITIONS.values():
            assert definition.never_means, definition.dimension

    def test_a_pageview_change_is_usage_and_never_demand(self) -> None:
        mapping = map_signal_type("content_request_change")
        assert mapping is not None
        assert EvidenceDimension.AUDIENCE_OR_USAGE in mapping.dimensions
        assert EvidenceDimension.MARKET_ACTIVITY not in mapping.dimensions
        assert EvidenceDimension.WILLINGNESS_TO_PAY not in mapping.dimensions
        assert "request is not a reader" in mapping.bound

    def test_a_procurement_total_is_never_willingness_to_pay(self) -> None:
        """§3's own example, and the mapping a reader most wants."""
        mapping = map_signal_type("procurement_value_contrast")
        assert mapping is not None
        assert EvidenceDimension.WILLINGNESS_TO_PAY not in mapping.dimensions
        assert EvidenceDimension.MARKET_ACTIVITY in mapping.dimensions
        assert "INCLUDING OPTIONS AND RENEWALS" in mapping.bound

    def test_gdelt_lexical_frequency_maps_to_nothing(self) -> None:
        """Not weakly, not with low relevance, not with a caveat."""
        for signal_type in ("lexical_frequency_change", "lexical_frequency_contrast"):
            mapping = map_signal_type(signal_type)
            assert mapping is not None
            assert mapping.dimensions == frozenset(), signal_type

    def test_missing_dimensions_remain_missing(self) -> None:
        """§4. An unmapped row carries the empty set, never a placeholder."""
        row = facets(signal_type_id="numeric_period_change", dimensions=frozenset())
        assert row.dimensions == frozenset()
        assert "evidence_dimension" in row.missing_factors

    def test_an_unregistered_signal_type_is_not_the_empty_mapping(self) -> None:
        """None means nobody decided; frozenset() means somebody decided nothing."""
        assert map_signal_type("some_future_type") is None
        assert map_signal_type("numeric_period_change") is not None

    def test_a_mapping_with_dimensions_must_state_a_bound(self) -> None:
        from sros_opportunity.mapping import SignalDimensionMapping

        with pytest.raises(ValueError, match="source-bounded meaning"):
            SignalDimensionMapping(
                signal_type_id="x",
                dimensions=frozenset({EvidenceDimension.MARKET_ACTIVITY}),
                rationale="because",
            )

    def test_trend_or_change_may_not_stand_alone(self) -> None:
        """Every Signal here is a derivation, so change is universal and empty."""
        from sros_opportunity.mapping import SignalDimensionMapping

        with pytest.raises(ValueError, match="may not stand alone"):
            SignalDimensionMapping(
                signal_type_id="x",
                dimensions=frozenset({EvidenceDimension.TREND_OR_CHANGE}),
                rationale="because",
                bound="bounded",
            )

    def test_trend_or_change_never_counts_toward_diversity(self) -> None:
        assert EvidenceDimension.TREND_OR_CHANGE not in COUNTING_DIMENSIONS
        assert len(COUNTING_DIMENSIONS) == len(EvidenceDimension) - 1


class TestEligibility:
    """§5. Four states, and nothing promotes across the scoring line."""

    def test_non_scorable_evidence_stays_context_only(self) -> None:
        decision = assess_eligibility(facets(), standing())
        assert decision.eligibility is PacketEligibility.ELIGIBLE_CONTEXT
        assert decision.may_enter_packet
        assert "NON_SCORABLE" in " ".join(decision.reasons)

    def test_nothing_promotes_non_scorable_to_scoring(self) -> None:
        """There is no parameter, threshold or override that would do it."""
        import inspect

        signature = inspect.signature(assess_eligibility)
        assert list(signature.parameters) == ["facets", "standing"]
        assert (
            assess_eligibility(facets(), standing()).eligibility
            is PacketEligibility.ELIGIBLE_CONTEXT
        )

    def test_a_reviewed_reliability_is_the_only_route_to_scoring(self) -> None:
        scorable = facets(reliability=0.5, reliability_status=ReliabilityStatus.RESOLVED)
        assert (
            assess_eligibility(scorable, standing()).eligibility
            is PacketEligibility.ELIGIBLE_SCORING
        )

    def test_a_missing_policy_standing_requires_review_and_never_permits(self) -> None:
        decision = assess_eligibility(facets(), None)
        assert decision.eligibility is PacketEligibility.REQUIRES_REVIEW
        assert "uncertainty is never permission" in " ".join(decision.reasons)

    def test_source_policy_is_preserved_and_a_refusal_blocks(self) -> None:
        refused = standing(permits_local_processing=False, basis="review is RESTRICTED")
        decision = assess_eligibility(facets(), refused)
        assert decision.eligibility is PacketEligibility.INELIGIBLE
        assert not decision.may_enter_packet

    def test_approval_never_transfers_between_use_profiles(self) -> None:
        other = standing(use_profile_id="commercial-multi-tenant-research-v1")
        decision = assess_eligibility(facets(), other)
        assert decision.eligibility is PacketEligibility.INELIGIBLE
        assert "approval never transfers" in " ".join(decision.reasons)

    def test_a_withdrawn_claim_blocks(self) -> None:
        decision = assess_eligibility(facets(claim_lifecycle="WITHDRAWN"), standing())
        assert decision.eligibility is PacketEligibility.INELIGIBLE

    def test_every_blocking_reason_is_returned_not_just_the_first(self) -> None:
        decision = assess_eligibility(
            facets(claim_lifecycle="WITHDRAWN", direction="NONSENSE"), standing()
        )
        assert len(decision.reasons) >= 2

    def test_a_standing_with_no_basis_is_refused_at_construction(self) -> None:
        with pytest.raises(ValueError, match="basis is required"):
            standing(basis="   ")


class TestFactsStayApart:
    """§4 and §13. Missing stays missing and UNKNOWN is never upgraded."""

    def test_a_reliability_value_needs_an_assessment_behind_it(self) -> None:
        with pytest.raises(ValueError, match="number nobody made"):
            facets(reliability=0.5, reliability_status=ReliabilityStatus.NO_APPLICABLE_ASSESSMENT)

    def test_a_resolution_that_produced_no_number_did_not_resolve(self) -> None:
        with pytest.raises(ValueError, match="did not resolve"):
            facets(reliability=None, reliability_status=ReliabilityStatus.RESOLVED)

    def test_independence_unknown_is_never_upgraded_by_a_packet(self) -> None:
        rows = tuple(
            (facets(evidence_id=f"e{i}", claim_id=f"c{i}"), PacketEligibility.ELIGIBLE_CONTEXT)
            for i in range(6)
        )
        packet = build_packet(None, "subject", rows)
        assert packet.independence_counts == {IndependenceState.UNKNOWN.value: 6}
        summary = packet.independence_summary()
        assert "independence is UNKNOWN for 6 of 6" in summary
        assert "independent sources" not in summary

    def test_a_single_family_packet_never_says_multiple_independent_sources(self) -> None:
        rows = tuple(
            (
                facets(
                    evidence_id=f"e{i}",
                    claim_id=f"c{i}",
                    independence_state=IndependenceState.KNOWN_INDEPENDENT,
                ),
                PacketEligibility.ELIGIBLE_CONTEXT,
            )
            for i in range(3)
        )
        packet = build_packet(None, "subject", rows)
        assert packet.single_source_family
        assert "one family is not multiple independent sources" in packet.independence_summary()

    def test_a_neutral_evidence_row_cannot_exist(self) -> None:
        with pytest.raises(ValueError, match="should not exist"):
            facets(direction="NEUTRAL")

    def test_dimensions_cannot_travel_without_their_bound(self) -> None:
        with pytest.raises(ValueError, match="detached from the sentence"):
            facets(dimension_bound="")

    def test_canonical_evidence_to_claim_link_is_preserved(self) -> None:
        rows = (
            (facets(evidence_id="e1", claim_id="c1"), PacketEligibility.ELIGIBLE_CONTEXT),
            (facets(evidence_id="e2", claim_id="c2"), PacketEligibility.ELIGIBLE_CONTEXT),
        )
        packet = build_packet(None, "subject", rows)
        assert packet.evidence_ids == ("e1", "e2")
        assert packet.claim_ids == ("c1", "c2")


class TestGroupingAndPackets:
    """§7 and §8. Deterministic, reference-only, and never semantic."""

    def test_the_subject_key_comes_from_source_native_identifiers(self) -> None:
        key = subject_key(
            "wikimedia-pageviews",
            "content_request_change",
            {"content_ids": ["Podman"], "content_platforms": ["en.wikipedia.org"]},
        )
        assert key is not None
        assert str(key) == "wikimedia-pageviews:content:en.wikipedia.org|Podman"

    def test_different_subjects_are_never_merged(self) -> None:
        """Docker, Podman and Kubernetes are three subjects. Merging them would be
        a SAME_PROBLEM_FAMILY judgement reached by hand instead of by the
        classifier Mission 1.27 parked."""
        rows = [
            (
                facets(evidence_id=f"e{i}", claim_id=f"c{i}"),
                {"content_ids": [name], "content_platforms": ["en.wikipedia.org"]},
            )
            for i, name in enumerate(("Docker_(software)", "Podman", "Kubernetes"))
        ]
        groups = group_by_subject(rows)
        assert len(groups) == 3
        assert all(len(g.facets) == 1 for g in groups)

    def test_grouping_has_no_similarity_machinery_at_all(self) -> None:
        source = (PACKAGE_ROOT / "grouping.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "difflib" not in alias.name
            if isinstance(node, ast.ImportFrom):
                assert node.module is None or "difflib" not in node.module

    def test_a_packet_is_deterministic_and_order_independent(self) -> None:
        a = facets(evidence_id="e1", claim_id="c1")
        b = facets(evidence_id="e2", claim_id="c2")
        forward = build_packet(
            None,
            "s",
            ((a, PacketEligibility.ELIGIBLE_CONTEXT), (b, PacketEligibility.ELIGIBLE_CONTEXT)),
        )
        reverse = build_packet(
            None,
            "s",
            ((b, PacketEligibility.ELIGIBLE_CONTEXT), (a, PacketEligibility.ELIGIBLE_CONTEXT)),
        )
        assert forward.packet_id == reverse.packet_id
        assert forward.evidence_ids == reverse.evidence_ids

    def test_a_different_evidence_set_is_a_different_packet(self) -> None:
        a = facets(evidence_id="e1", claim_id="c1")
        b = facets(evidence_id="e2", claim_id="c2")
        one = build_packet(None, "s", ((a, PacketEligibility.ELIGIBLE_CONTEXT),))
        two = build_packet(
            None,
            "s",
            ((a, PacketEligibility.ELIGIBLE_CONTEXT), (b, PacketEligibility.ELIGIBLE_CONTEXT)),
        )
        assert one.packet_id != two.packet_id

    def test_a_packet_records_every_procedure_it_was_built_under(self) -> None:
        packet = build_packet(None, "s", ((facets(), PacketEligibility.ELIGIBLE_CONTEXT),))
        assert set(packet.procedures) == {
            "packet",
            "grouping",
            "dimension_map",
            "eligibility",
        }

    def test_a_packet_carries_references_and_not_statements(self) -> None:
        """§7: references, never copied truth."""
        packet = build_packet(None, "s", ((facets(), PacketEligibility.ELIGIBLE_CONTEXT),))
        fields = set(packet.__dataclass_fields__)
        for forbidden in ("statement", "statements", "claim_text", "magnitude", "source_text"):
            assert forbidden not in fields


class TestSufficiency:
    """§12. Formable is not scoring-ready, and no quota forces anything."""

    def _packet(self, count: int, dimensions: frozenset[EvidenceDimension]):
        rows = tuple(
            (
                facets(evidence_id=f"e{i}", claim_id=f"c{i}", dimensions=dimensions),
                PacketEligibility.ELIGIBLE_CONTEXT,
            )
            for i in range(count)
        )
        return build_packet(None, "s", rows)

    def test_two_rows_and_two_counting_dimensions_are_formable(self) -> None:
        packet = self._packet(
            2, frozenset({EvidenceDimension.MARKET_ACTIVITY, EvidenceDimension.ECONOMIC_VALUE})
        )
        result = evaluate(packet)
        assert result.status is HypothesisStatus.HYPOTHESIS_FORMABLE

    def test_formable_is_not_scoring_ready(self) -> None:
        packet = self._packet(
            2, frozenset({EvidenceDimension.MARKET_ACTIVITY, EvidenceDimension.ECONOMIC_VALUE})
        )
        result = evaluate(packet)
        assert result.status is HypothesisStatus.HYPOTHESIS_FORMABLE
        assert result.scoring_ready is False
        assert result.scoring_eligible_rows == 0

    def test_one_row_with_three_dimensions_is_insufficient(self) -> None:
        """The TED shape: rich in dimensions, alone in the packet."""
        packet = self._packet(
            1,
            frozenset(
                {
                    EvidenceDimension.MARKET_ACTIVITY,
                    EvidenceDimension.ECONOMIC_VALUE,
                    EvidenceDimension.BUYER_OR_BUDGET_EXISTENCE,
                }
            ),
        )
        result = evaluate(packet)
        assert result.status is HypothesisStatus.HYPOTHESIS_INSUFFICIENT_EVIDENCE

    def test_six_rows_with_one_counting_dimension_are_insufficient(self) -> None:
        """The Wikimedia shape, and the case the TREND qualifier decides."""
        packet = self._packet(
            6,
            frozenset({EvidenceDimension.AUDIENCE_OR_USAGE, EvidenceDimension.TREND_OR_CHANGE}),
        )
        result = evaluate(packet)
        assert result.status is HypothesisStatus.HYPOTHESIS_INSUFFICIENT_EVIDENCE
        assert result.distinct_counting_dimensions == 1
        assert result.distinct_dimensions_literal == 2

    def test_rows_awaiting_review_produce_requires_review_not_insufficient(self) -> None:
        packet = self._packet(
            2, frozenset({EvidenceDimension.MARKET_ACTIVITY, EvidenceDimension.ECONOMIC_VALUE})
        )
        result = evaluate(packet, requires_review_rows=1)
        assert result.status is HypothesisStatus.HYPOTHESIS_REQUIRES_REVIEW

    def test_no_dimension_is_individually_required(self) -> None:
        """§12 forbids requiring every dimension; nothing names one."""
        statement = SUFFICIENCY_V1.statement
        for dimension in EvidenceDimension:
            assert dimension.value not in statement or dimension.value == "TREND_OR_CHANGE"

    def test_there_is_no_opportunity_quota(self) -> None:
        """§16: five is a maximum, never a target. Nothing counts toward one."""
        result = evaluate(self._packet(1, frozenset()))
        assert result.status is HypothesisStatus.HYPOTHESIS_INSUFFICIENT_EVIDENCE
        source = (PACKAGE_ROOT / "sufficiency.py").read_text(encoding="utf-8")
        assert "quota" not in source.lower() or "no quota" in source.lower()


class TestExternalSynthesisGate:
    """§9. Authorization is resolved before anything is serialised."""

    def _packet(self):
        return build_packet(None, "s", ((facets(), PacketEligibility.ELIGIBLE_CONTEXT),))

    def test_not_assessed_refuses_and_says_so_by_name(self) -> None:
        decision = authorize_packet_for_external_synthesis(
            self._packet(),
            {"wikimedia-pageviews": standing(permits_external_model_transmission=None)},
            provider_configured=True,
            provider_posture="APPROVED",
        )
        assert decision.availability is SynthesisAvailability.UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS
        assert any("NOT_ASSESSED" in r for r in decision.refusal_reasons)
        assert ("wikimedia-pageviews", "NOT_ASSESSED") in decision.per_source

    def test_a_permitted_source_with_a_configured_provider_is_authorised(self) -> None:
        decision = authorize_packet_for_external_synthesis(
            self._packet(),
            {"wikimedia-pageviews": standing(permits_external_model_transmission=True)},
            provider_configured=True,
            provider_posture="APPROVED",
        )
        assert decision.authorized

    def test_an_unconfigured_provider_refuses_by_name(self) -> None:
        decision = authorize_packet_for_external_synthesis(
            self._packet(),
            {"wikimedia-pageviews": standing(permits_external_model_transmission=True)},
            provider_configured=False,
            provider_posture="APPROVED",
        )
        assert any("PROVIDER_NOT_CONFIGURED" in r for r in decision.refusal_reasons)

    def test_serialization_refuses_before_reading_any_claim_statement(self) -> None:
        """A refused packet leaves no string containing source-derived text.

        The mapping raises if touched, so a passing test proves the gate came
        first rather than proving the output happened to be empty.
        """

        class Exploding(dict):
            def __contains__(self, key: object) -> bool:  # pragma: no cover - guard
                raise AssertionError("claim statements were read before authorization")

            def __getitem__(self, key: object) -> str:  # pragma: no cover - guard
                raise AssertionError("claim statements were read before authorization")

        from sros_opportunity import serialize_packet_for_model

        decision = authorize_packet_for_external_synthesis(
            self._packet(),
            {"wikimedia-pageviews": standing(permits_external_model_transmission=None)},
            provider_configured=True,
            provider_posture="APPROVED",
        )
        with pytest.raises(ExternalSynthesisRefusedError):
            serialize_packet_for_model(self._packet(), decision, Exploding())

    def test_an_authorization_is_not_transferable_between_packets(self) -> None:
        from sros_opportunity import serialize_packet_for_model

        other = build_packet(
            None,
            "other",
            ((facets(evidence_id="zz", claim_id="c9"), PacketEligibility.ELIGIBLE_CONTEXT),),
        )
        decision = authorize_packet_for_external_synthesis(
            self._packet(),
            {"wikimedia-pageviews": standing(permits_external_model_transmission=True)},
            provider_configured=True,
            provider_posture="APPROVED",
        )
        with pytest.raises(ExternalSynthesisRefusedError, match="not transferable"):
            serialize_packet_for_model(other, decision, {"c9": "a statement"})

    def test_a_packet_is_never_silently_trimmed_to_its_authorised_rows(self) -> None:
        """§9 names both failures: do not leak, and do not pretend completeness."""
        from sros_opportunity import serialize_packet_for_model

        packet = build_packet(
            None,
            "s",
            (
                (facets(evidence_id="e1", claim_id="c1"), PacketEligibility.ELIGIBLE_CONTEXT),
                (facets(evidence_id="e2", claim_id="c2"), PacketEligibility.ELIGIBLE_CONTEXT),
            ),
        )
        decision = authorize_packet_for_external_synthesis(
            packet,
            {"wikimedia-pageviews": standing(permits_external_model_transmission=True)},
            provider_configured=True,
            provider_posture="APPROVED",
        )
        with pytest.raises(ExternalSynthesisRefusedError, match="silently incomplete"):
            serialize_packet_for_model(packet, decision, {"c1": "only one statement"})

    def test_the_gate_reports_every_source_including_the_permitted_ones(self) -> None:
        decision = authorize_packet_for_external_synthesis(
            self._packet(),
            {"wikimedia-pageviews": standing(permits_external_model_transmission=True)},
            provider_configured=False,
            provider_posture="APPROVED",
        )
        assert ("wikimedia-pageviews", "PERMITTED") in decision.per_source


class TestNoUnsupportedCommercialClaims:
    """§11. The vocabulary is refused unless the exact dimension is supported."""

    ALL = frozenset(EvidenceDimension)

    def test_market_size_is_never_supportable(self) -> None:
        violations = check_statement("The market size is large.", self.ALL)
        assert violations and violations[0].required_dimension is None

    def test_willingness_to_pay_needs_that_exact_dimension(self) -> None:
        text = "Buyers in this category would pay for a managed service."
        assert check_statement(text, frozenset({EvidenceDimension.MARKET_ACTIVITY}))
        assert not check_statement(
            text,
            frozenset(
                {
                    EvidenceDimension.WILLINGNESS_TO_PAY,
                    EvidenceDimension.BUYER_OR_BUDGET_EXISTENCE,
                }
            ),
        )

    def test_matching_is_over_tokens_and_not_substrings(self) -> None:
        """`supermarket` is not `market`. Mission 1.13.1 paid for this already."""
        assert not check_statement("Supermarkets appear in the corpus.", frozenset())

    def test_plurals_and_possessives_still_match(self) -> None:
        assert check_statement("The customers are enterprises.", frozenset())
        assert check_statement("The customer's budget is fixed.", frozenset())

    def test_every_violation_is_reported_not_only_the_first(self) -> None:
        violations = check_statement("Revenue and adoption and TAM.", frozenset())
        assert len(violations) >= 3

    def test_the_forbidden_terms_reference_real_dimensions(self) -> None:
        from sros_opportunity import FORBIDDEN_TERMS

        for required in FORBIDDEN_TERMS.values():
            assert required is None or isinstance(required, EvidenceDimension)


class TestAHypothesisCannotClaimValidation:
    """§18, enforced in code rather than in prose."""

    def _kwargs(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = dict(
            hypothesis_id="h1",
            packet_id="p1",
            status=OpportunityStatus.OPPORTUNITY_HYPOTHESIS,
            target_actor="operators of container runtimes",
            observed_need_or_change="request counts for the subject moved between adjacent days",
            candidate_intervention="a tool that does something narrow",
            hypothesis_statement="It may be worth investigating whether such a tool helps.",
            reasoning_summary="Two evidence rows bear on attention to the subject.",
            supported_dimensions=frozenset({EvidenceDimension.AUDIENCE_OR_USAGE}),
            unsupported_dimensions=frozenset({EvidenceDimension.WILLINGNESS_TO_PAY}),
            key_evidence_ids=("e1", "e2"),
            key_claim_ids=("c1", "c2"),
            source_families=("knowledge",),
            uncertainties=("nothing establishes a buyer",),
            epistemic_limitations=("all evidence is NON_SCORABLE",),
            use_profile_id="local-private-research-v1",
        )
        base.update(overrides)
        return base

    def test_no_validated_state_exists_in_the_enum(self) -> None:
        values = {s.value for s in OpportunityStatus}
        assert values == {
            "OPPORTUNITY_HYPOTHESIS",
            "HYPOTHESIS_WITHDRAWN",
            "HYPOTHESIS_SUPERSEDED",
        }
        for forbidden in (
            "VALIDATED_OPPORTUNITY",
            "PROVEN_MARKET",
            "WINNING_IDEA",
            "PRODUCT_MARKET_FIT",
            "HIGH_CONFIDENCE_BUSINESS",
        ):
            assert forbidden not in values

    def test_is_validated_is_always_false(self) -> None:
        assert OpportunityHypothesis(**self._kwargs()).is_validated is False  # type: ignore[arg-type]

    def test_validation_language_is_refused_in_the_statement(self) -> None:
        from sros_opportunity import UnsupportedClaimError

        with pytest.raises(UnsupportedClaimError):
            OpportunityHypothesis(  # type: ignore[arg-type]
                **self._kwargs(hypothesis_statement="This is a proven and validated opportunity.")
            )

    def test_validation_words_are_detected_standalone(self) -> None:
        for word in VALIDATION_WORDS:
            assert check_no_validation_language(f"This is {word} work.")

    def test_a_hypothesis_must_state_what_it_does_not_support(self) -> None:
        from sros_opportunity import UnsupportedClaimError

        with pytest.raises(UnsupportedClaimError, match="not a hypothesis"):
            OpportunityHypothesis(**self._kwargs(unsupported_dimensions=frozenset()))  # type: ignore[arg-type]

    def test_a_hypothesis_with_no_evidence_cannot_be_built(self) -> None:
        from sros_opportunity import UnsupportedClaimError

        with pytest.raises(UnsupportedClaimError, match="does not record ideas"):
            OpportunityHypothesis(**self._kwargs(key_evidence_ids=()))  # type: ignore[arg-type]

    def test_a_model_version_requires_a_prompt_version(self) -> None:
        with pytest.raises(ValueError, match="prompt version"):
            OpportunityHypothesis(**self._kwargs(model_version="m", prompt_version=None))  # type: ignore[arg-type]

    def test_an_unsupported_commercial_claim_cannot_be_persisted(self) -> None:
        from sros_opportunity import UnsupportedClaimError

        with pytest.raises(UnsupportedClaimError):
            OpportunityHypothesis(  # type: ignore[arg-type]
                **self._kwargs(hypothesis_statement="Customers will pay 40 EUR per seat for this.")
            )


class TestNoRankingAndNoProblemFamilyDependency:
    """§6 and §15, asserted over the AST rather than promised in a docstring."""

    def _modules(self) -> list[pathlib.Path]:
        return sorted(PACKAGE_ROOT.glob("*.py"))

    def test_the_package_never_imports_the_parked_classifier(self) -> None:
        for path in self._modules():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "semantic_equivalence" not in alias.name, path.name
                if isinstance(node, ast.ImportFrom):
                    assert "semantic_equivalence" not in (node.module or ""), path.name

    def test_the_parked_relation_is_named_nowhere_in_executable_code(self) -> None:
        """Docstrings may EXPLAIN that the relation is not required; code may not
        reference it. Docstrings are excluded because a substring scan fails on
        the paragraph explaining the rule (testing-strategy §23)."""
        for path in self._modules():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    continue
                if isinstance(node, ast.Name):
                    assert "SAME_PROBLEM_FAMILY" not in node.id, path.name
                if isinstance(node, ast.Attribute):
                    assert "SAME_PROBLEM_FAMILY" not in node.attr, path.name

    def test_the_package_imports_no_gateway_provider_or_registry(self) -> None:
        forbidden = ("sros_llm_gateway", "sros_acquisition", "anthropic", "openai", "psycopg")
        for path in self._modules():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    for bad in forbidden:
                        assert not name.startswith(bad), f"{path.name} imports {name}"

    def test_no_ranking_score_field_exists_anywhere(self) -> None:
        """§15: no 0-100 score, no weight, no priority, no leaderboard."""
        banned = ("_score", "rank", "weight", "priority", "leaderboard", "percentile")
        for path in self._modules():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    for bad in banned:
                        assert bad not in node.name.lower(), f"{path.name}: {node.name}"
                if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    for bad in banned:
                        assert bad not in node.target.id.lower(), f"{path.name}: {node.target.id}"

    def test_a_hypothesis_carries_no_scores(self) -> None:
        from sros_opportunity.hypothesis import OpportunityHypothesis as H

        assert H.__dataclass_fields__["scores"].type == "tuple[()]"


class TestTheRealRunIsRecordedHonestly:
    """§16 and §20, over the committed artifact of the real run."""

    def _report(self) -> dict:
        path = DOCS / "opportunity-preparation-v1.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_the_run_inspected_every_canonical_evidence_row(self) -> None:
        report = self._report()
        assert report["totals"]["evidence_rows_inspected"] == 26

    def test_no_evidence_row_is_scoring_eligible(self) -> None:
        report = self._report()
        assert report["totals"]["eligible_scoring"] == 0
        assert report["totals"]["eligible_context"] == 26

    def test_no_opportunity_was_generated_and_no_model_was_called(self) -> None:
        report = self._report()
        assert report["totals"]["opportunity_hypotheses_generated"] == 0
        assert report["totals"]["model_calls"] == 0
        assert report["totals"]["cost_units"] == 0.0

    def test_the_egress_gate_is_evaluated_for_every_packet(self) -> None:
        """Mission 1.28 asserted here that EVERY packet was blocked at this gate,
        which was true then and is the state Mission 1.29 was chartered to
        change: three of the four contributing sources now have a transmission
        decision, and TED does not. The specific counts belong to
        `test_transmission_governance.py`; what this keeps is the property that
        matters to Mission 1.28's own claim -- the gate runs on every packet and
        records an answer, so no packet reaches a model without one."""
        report = self._report()
        assert report["packets"]
        for packet in report["packets"]:
            gate = packet["external_synthesis"]
            assert gate["availability"] in (
                "AVAILABLE",
                "UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS",
            )
            assert gate["per_source"], packet["subject"]

    def test_no_packet_claims_independent_sources(self) -> None:
        report = self._report()
        for packet in report["packets"]:
            assert "independence is UNKNOWN" in packet["independence"]

    def test_the_report_declares_its_use_profile_rather_than_inferring_it(self) -> None:
        report = self._report()
        assert report["use_profile_id"] == "local-private-research-v1"
        assert "DECLARED" in report["use_profile_note"]
