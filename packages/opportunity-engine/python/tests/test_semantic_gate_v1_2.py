"""Mission 1.84.10. The semantic output gate v1.2.0: assertion, not token presence.

Every case here is SYNTHETIC. The packet is built from the repository's own procurement mapping over
invented ids, statements and CPV class, and no case is V3's text: §4 makes V3's five refusals test
INPUTS for a later diagnostic replay, never exemptions, and a gate tuned on them would pass V3 and
nothing else. What these tests pin is the general property, on unseen equivalents:

* a concept is refused when it is ASSERTED and not when it is denied, requested, uncertain, listed as
  not supported or classified as unknown (§5, §13);
* each field keeps the disposition and the shape its policy gives it (§7 to §12);
* the support universe has three typed channels, and the trusted one licenses definitional
  identifiers only (§15 to §19);
* every forbidden concept is still forbidden as an assertion (§20);
* v1.0.0 and v1.1.0 are byte-identical, and the gate's components are versioned (§21).
"""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import re

import pytest
from sros_opportunity import (
    EvidenceDimension,
    EvidenceFacets,
    IndependenceState,
    PacketEligibility,
    ReliabilityStatus,
    build_packet,
)
from sros_opportunity.assertion_context import (
    PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE,
    Disposition,
    FieldContext,
    Shape,
    SupportCategory,
    TrustedContext,
    TrustedFact,
    TrustedFactKind,
    audit_text,
    build_support_universe,
    canonical_dimension_phrase,
    classify,
    is_asserted,
    is_request_shaped,
    is_uncertainty_shaped,
)
from sros_opportunity.mapping import SIGNAL_DIMENSION_MAP
from sros_opportunity.second_opportunity import (
    _FORBIDDEN_PHRASES,
    PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    evaluate_second_opportunity_output_v1_1,
)
from sros_opportunity.second_opportunity_gate_v1_2 import (
    CLASSIFICATION_DISPOSITIONS,
    COMPONENT_VERSIONS_V1_2,
    FORBIDDEN_CONCEPTS_V1_2,
    SECOND_OPPORTUNITY_FIELD_POLICY,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_2,
    SEMANTIC_GATE_REPAIR_DECISION,
    TRUSTED_CONTEXT_VERSION,
    build_trusted_context,
    evaluate_second_opportunity_output_v1_2,
)
from sros_opportunity.synthesis import MANDATORY_UNSUPPORTED_REPORT

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
PACKAGE = REPO_ROOT / "packages" / "opportunity-engine" / "python" / "sros_opportunity"
DATA = REPO_ROOT / "docs" / "data"

EVIDENCE = ("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222")
CLAIMS = ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
SUBJECT = "ted-eu:CPV-class:5555"
STATEMENTS = {
    CLAIMS[0]: (
        "Tenders Electronic Daily (EU public procurement) reported that, in its "
        '"notices/eforms-contract-and-award" resource, within a bounded set of 4 "CONTRACT_NOTICE" '
        'notices classified under "CPV" class "5555" (division "55"), the largest "TOTAL_VALUE" '
        'amount at "NOTICE" scope stated in "EUR" exceeded the smallest by 120000.'
    ),
    CLAIMS[1]: (
        'The source "ted-eu" published, in its "notices/eforms-contract-and-award" resource, at '
        'least one bounded set of "CONTRACT_NOTICE" notices classified under "CPV" class "5555" '
        '(division "55") whose stated "TOTAL_VALUE" amounts in "EUR" at "NOTICE" scope differ '
        "from one another."
    ),
}
E2C = dict(zip(EVIDENCE, CLAIMS, strict=True))


def _facets(evidence_id: str, claim_id: str, signal: str) -> EvidenceFacets:
    mapping = SIGNAL_DIMENSION_MAP[signal]
    return EvidenceFacets(
        evidence_id=evidence_id,
        claim_id=claim_id,
        source_id="ted-eu",
        source_family="public_procurement",
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
        reliability=0.5,
        reliability_status=ReliabilityStatus.RESOLVED,
        independence_state=IndependenceState.UNKNOWN,
        independence_group_id=None,
        observed_at=None,
        signal_type_id=signal,
        dimensions=mapping.dimensions,
        dimension_bound=mapping.bound,
    )


def _packet(signal: str = "procurement_value_contrast"):
    return build_packet(
        None,
        SUBJECT,
        tuple(
            (_facets(e, c, signal), PacketEligibility.ELIGIBLE_SCORING)
            for e, c in zip(EVIDENCE, CLAIMS, strict=True)
        ),
    )


PACKET = _packet()
AUDIENCE_PACKET = _packet("content_request_change")
MANDATORY = [d.value for d in MANDATORY_UNSUPPORTED_REPORT if d not in PACKET.dimensions]


def good_output(**changes: object) -> dict:
    output: dict = {
        "decision": "FORM_HYPOTHESIS",
        "subject": SUBJECT,
        "target_actor_if_supported": (
            "Contracting authorities that published notices under CPV class 5555."
        ),
        "observed_need": (
            "The packet records published notices with differing stated amounts; it does not "
            "establish a need."
        ),
        "candidate_intervention_class": (
            "No intervention class is supported; only an inquiry into the published notices "
            "could be scoped."
        ),
        "hypothesis_statement": (
            "One question worth testing is whether these authorities publish comparable notices "
            "repeatedly; nothing supplied establishes that they do."
        ),
        "supported_dimensions": ["BUYER_OR_BUDGET_EXISTENCE", "ECONOMIC_VALUE", "MARKET_ACTIVITY"],
        "unsupported_dimensions": list(MANDATORY),
        "supporting_evidence_ids": list(EVIDENCE),
        "supporting_claim_ids": list(CLAIMS),
        "source_families": ["public_procurement"],
        "independence_status": "Independence is UNKNOWN for 2 of 2 rows.",
        "reliability_status": "Both rows are SCORABLE; no score exists.",
        "evidence_bound_reasoning_summary": (
            "The statements show 4 notices under CPV class 5555 whose stated TOTAL_VALUE amounts "
            "differ by 120000 EUR, which is market activity in the bounded scope. They do not "
            "establish willingness to pay or actual expenditure."
        ),
        "critical_uncertainties": ["Whether any authority publishes such notices repeatedly."],
        "commercial_claims_supported": [
            "Contracting authorities under CPV class 5555 published notices with stated amounts."
        ],
        "commercial_claims_not_supported": ["Buyers are willing to pay for software."],
        "recommended_next_evidence": ["Evidence of payments actually made under these notices."],
        "confidence_classification": "EXPLORATORY",
        "statement_classifications": [
            {
                "statement": "Notices under CPV class 5555 state differing amounts.",
                "classification": "OBSERVED_OR_EVIDENCE_SUPPORTED",
            },
            {
                "statement": "The same authority publishes such notices repeatedly.",
                "classification": "HYPOTHESIS_TO_VALIDATE",
            },
            {
                "statement": "An authority would pay for a new service.",
                "classification": "UNKNOWN_REQUIRES_EVIDENCE",
            },
        ],
    }
    output.update(changes)
    return output


def gate(output: dict, *, packet=PACKET, trusted: TrustedContext | None = None):
    context = build_trusted_context(packet) if trusted is None else trusted
    return evaluate_second_opportunity_output_v1_2(
        output, packet, STATEMENTS, E2C, trusted_context=context
    )


def reasons_with(field: str, value: object, **kwargs: object) -> tuple[str, ...]:
    return gate(good_output(**{field: value}), **kwargs).refusal_reasons  # type: ignore[arg-type]


def passes(field: str, value: object) -> bool:
    return not reasons_with(field, value)


SUMMARY = "evidence_bound_reasoning_summary"


# ============================================================================ the baseline


class TestTheSyntheticBaseline:
    def test_a_well_formed_synthetic_answer_passes(self) -> None:
        decision = gate(good_output())
        assert decision.refusal_reasons == ()
        assert decision.persist is True
        assert decision.gate_version == SECOND_OPPORTUNITY_GATE_VERSION_V1_2

    def test_it_also_satisfies_the_unchanged_v1_1_0_schema(self) -> None:
        from sros_opportunity.schema_validation import schema_violations

        assert schema_violations(good_output(), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1) == []

    def test_a_schema_violation_is_still_reported_first(self) -> None:
        reasons = reasons_with(SUMMARY, "x" * 901)
        assert reasons[0].startswith("second-opportunity-synthesis-output@1.1.0:")

    def test_insufficient_evidence_is_a_correct_answer_and_creates_nothing(self) -> None:
        decision = gate(good_output(decision="INSUFFICIENT_EVIDENCE"))
        assert decision.persist is False
        assert any("INSUFFICIENT_EVIDENCE" in r for r in decision.refusal_reasons)


# ============================================================================ §5 and §13


class TestSection5AssertionNotTokenPresence:
    MUST_FAIL = (
        "Customers are willing to pay.",
        "The evidence establishes willingness to pay.",
        "Actual expenditure was 10 million EUR.",
        "These Evidence rows are scored.",
        "There is a solution gap.",
        "The procurement values prove market demand.",
    )
    MUST_PASS = (
        "No evidence establishes willingness to pay.",
        "Willingness to pay is not established.",
        "Actual expenditure is not established by this packet.",
        "No score exists.",
        "These rows are scoring-ready, not scored.",
        "Evidence of actual expenditure would be required.",
    )

    @pytest.mark.parametrize("text", MUST_FAIL)
    def test_an_assertion_is_refused(self, text: str) -> None:
        assert not passes(SUMMARY, text), text

    @pytest.mark.parametrize("text", MUST_PASS)
    def test_the_concept_alone_is_not_refused(self, text: str) -> None:
        assert passes(SUMMARY, text), reasons_with(SUMMARY, text)


class TestSection13SentenceScopedDenial:
    PASS = (
        "No evidence establishes willingness to pay.",
        "The packet does not establish actual expenditure.",
        "Scoring-ready is not the same as scored, and no score exists.",
    )
    FAIL = (
        "No evidence establishes willingness to pay. Buyers are willing to pay.",
        "Actual expenditure is not established, but is probably substantial.",
        "These rows are not unscored; they are scored.",
    )

    @pytest.mark.parametrize("text", PASS)
    def test_a_denial_clears_its_own_clause(self, text: str) -> None:
        assert passes(SUMMARY, text), reasons_with(SUMMARY, text)

    @pytest.mark.parametrize("text", FAIL)
    def test_a_denial_does_not_reach_past_its_clause(self, text: str) -> None:
        assert not passes(SUMMARY, text), text

    def test_the_second_sentence_is_what_fails(self) -> None:
        occurrences = classify(
            "No evidence establishes willingness to pay. Buyers are willing to pay.",
            "willing to pay",
        )
        assert [o.asserted for o in occurrences] == [True]
        assert occurrences[0].sentence == "Buyers are willing to pay."

    def test_a_contrastive_continuation_re_asserts_the_denied_subject(self) -> None:
        (occurrence,) = classify(
            "Actual expenditure is not established, but is probably substantial.",
            "actual expenditure",
        )
        assert occurrence.asserted
        assert "contrast" in occurrence.why

    def test_a_hedged_continuation_in_the_same_clause_re_asserts_too(self) -> None:
        assert is_asserted(
            "Actual expenditure is not established and is probably substantial.",
            "actual expenditure",
        )

    def test_a_list_under_one_denial_stays_denied(self) -> None:
        text = (
            "This record does not show dissatisfaction, feasibility, a solution gap, repeat "
            "purchasing or willingness to pay."
        )
        for phrase in ("willingness to pay", "solution gap", "dissatisfaction"):
            assert not is_asserted(text, phrase), phrase

    def test_a_coordinated_clause_with_its_own_subject_is_read_on_its_own(self) -> None:
        assert is_asserted(
            "No evidence establishes demand for a product, and buyers are willing to pay.",
            "willing to pay",
        )
        assert not is_asserted(
            "No evidence establishes demand for a product, and no buyer is willing to pay.",
            "willing to pay",
        )

    def test_an_intensifier_is_not_a_denial(self) -> None:
        assert is_asserted("Buyers are not only willing to pay but eager.", "willing to pay")

    def test_never_no_longer_matches_inside_nevertheless(self) -> None:
        assert is_asserted("Nevertheless, buyers would pay.", "would pay")


# ============================================================================ §14


class TestSection14Scored:
    FAIL = (
        "Both rows are SCORABLE and are scored.",
        "Both rows are SCORABLE. They have been scored.",
        "Both rows are SCORABLE; each row carries a score.",
        "Both rows are SCORABLE and the evidence score is 2.",
        "Both rows are SCORABLE, not unscored; they are scored.",
        "Scored rows: 2.",
    )
    PASS = (
        "Both rows are SCORABLE; no score exists.",
        "Both rows are SCORABLE, which is not the same as scored.",
        "Both rows are SCORABLE; neither row has been scored.",
        "Both rows are SCORABLE, not scored, and no row has a score.",
        "Both rows are SCORABLE; none of them is scored.",
        "Both rows are SCORABLE; scoring-ready does not mean scored, and there is no score.",
    )

    @pytest.mark.parametrize("text", FAIL)
    def test_a_score_asserted_in_any_form_is_refused(self, text: str) -> None:
        assert not passes("reliability_status", text), text

    @pytest.mark.parametrize("text", PASS)
    def test_a_score_denied_in_any_form_passes(self, text: str) -> None:
        assert passes("reliability_status", text), reasons_with("reliability_status", text)

    def test_the_repair_is_general_rather_than_a_field_special_case(self) -> None:
        """v1.1.0 checked a substring in one field; v1.2.0 asserts nowhere that a score exists."""
        assert not passes(SUMMARY, "Each of the 2 rows was scored.")
        assert not passes(
            "commercial_claims_supported", ["The rows have been scored by the pipeline."]
        )

    def test_scorability_must_still_be_stated(self) -> None:
        assert not passes("reliability_status", "No score exists.")


# ============================================================================ §7 to §12


class TestSection7FieldPolicy:
    def test_the_policy_covers_every_schema_property_and_nothing_else(self) -> None:
        schema_fields = set(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"])  # type: ignore[index]
        assert {fc.field_name for fc in SECOND_OPPORTUNITY_FIELD_POLICY} == schema_fields

    def test_each_listed_field_has_the_disposition_the_brief_names(self) -> None:
        policy = {fc.field_name: fc for fc in SECOND_OPPORTUNITY_FIELD_POLICY}
        expected = {
            "commercial_claims_supported": (Disposition.SUPPORTED_ASSERTION, Shape.FREE),
            "commercial_claims_not_supported": (Disposition.EXPLICITLY_NOT_SUPPORTED, Shape.FREE),
            "critical_uncertainties": (Disposition.UNKNOWN_REQUIRES_EVIDENCE, Shape.UNCERTAINTY),
            "recommended_next_evidence": (Disposition.FUTURE_EVIDENCE_REQUEST, Shape.REQUEST),
            "supported_dimensions": (Disposition.STRUCTURAL_FACT, Shape.ENUMERATION),
            "unsupported_dimensions": (Disposition.EXPLICITLY_NOT_SUPPORTED, Shape.ENUMERATION),
            "reliability_status": (Disposition.STRUCTURAL_FACT, Shape.FREE),
            "independence_status": (Disposition.STRUCTURAL_FACT, Shape.FREE),
            "hypothesis_statement": (Disposition.HYPOTHESIS_TO_VALIDATE, Shape.FREE),
            SUMMARY: (Disposition.SUPPORTED_ASSERTION, Shape.FREE),
            "observed_need": (Disposition.SUPPORTED_ASSERTION, Shape.FREE),
            "candidate_intervention_class": (Disposition.SUPPORTED_ASSERTION, Shape.FREE),
        }
        for name, (disposition, shape) in expected.items():
            assert (policy[name].disposition, policy[name].shape) == (disposition, shape), name
        labelled = policy["statement_classifications"]
        assert labelled.item_label_key == "classification"
        assert labelled.item_text_key == "statement"

    def test_the_seven_dispositions_exist(self) -> None:
        assert {d.value for d in Disposition} == {
            "SUPPORTED_ASSERTION",
            "HYPOTHESIS_TO_VALIDATE",
            "EXPLICITLY_NOT_SUPPORTED",
            "UNKNOWN_REQUIRES_EVIDENCE",
            "FUTURE_EVIDENCE_REQUEST",
            "STRUCTURAL_FACT",
            "TRUSTED_LIMITING_FACT",
        }

    def test_no_output_field_may_claim_the_trusted_category(self) -> None:
        with pytest.raises(ValueError, match="TRUSTED_LIMITING_FACT"):
            FieldContext("x", Disposition.TRUSTED_LIMITING_FACT, Shape.FREE, "because")

    def test_a_field_the_policy_does_not_name_fails_closed(self) -> None:
        output = good_output()
        output["unexpected_prose"] = "Buyers would pay."
        assert any("unexpected_prose" in r for r in gate(output).refusal_reasons)


class TestSection9CommercialClaims:
    def test_a_supported_claim_is_checked_strictly(self) -> None:
        assert not passes("commercial_claims_supported", ["Buyers are willing to pay."])
        assert not passes("commercial_claims_supported", ["Demand exists for this service."])

    def test_a_claim_listed_as_not_supported_is_the_enumeration_asked_for(self) -> None:
        assert passes(
            "commercial_claims_not_supported",
            ["Any authority would pay for a tool.", "A solution gap exists in this class."],
        )

    def test_a_not_supported_item_that_says_it_is_established_contradicts_its_field(self) -> None:
        assert not passes(
            "commercial_claims_not_supported",
            ["Buyers are willing to pay, as the notices establish."],
        )

    def test_a_not_supported_item_still_may_not_introduce_a_figure(self) -> None:
        assert not passes("commercial_claims_not_supported", ["Buyers would pay 40 EUR."])


class TestSection10StatementClassifications:
    @staticmethod
    def _with(statement: str, classification: str) -> dict:
        output = good_output()
        output["statement_classifications"] = [
            *output["statement_classifications"],
            {"statement": statement, "classification": classification},
        ]
        return output

    def test_observed_requires_support(self) -> None:
        output = self._with("Buyers are willing to pay.", "OBSERVED_OR_EVIDENCE_SUPPORTED")
        assert not gate(output).persist

    def test_a_hypothesis_to_validate_is_not_an_assertion(self) -> None:
        output = self._with(
            "Authorities would pay for a scheduling tool.", "HYPOTHESIS_TO_VALIDATE"
        )
        assert gate(output).persist, gate(output).refusal_reasons

    def test_a_hypothesis_is_not_promoted(self) -> None:
        for statement in (
            "It is proven that authorities would pay.",
            "Authorities definitely would pay.",
        ):
            output = self._with(statement, "HYPOTHESIS_TO_VALIDATE")
            assert not gate(output).persist, statement

    def test_an_unknown_is_not_an_assertion(self) -> None:
        output = self._with(
            "Buyers are dissatisfied with current tools.", "UNKNOWN_REQUIRES_EVIDENCE"
        )
        assert gate(output).persist, gate(output).refusal_reasons

    def test_an_unknown_is_not_promoted_either(self) -> None:
        output = self._with("Buyers are clearly willing to pay.", "UNKNOWN_REQUIRES_EVIDENCE")
        assert not gate(output).persist

    def test_every_label_maps_to_a_disposition(self) -> None:
        enum = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]["statement_classifications"][  # type: ignore[index]
            "items"
        ]["properties"]["classification"]["enum"]
        assert set(CLASSIFICATION_DISPOSITIONS) == set(enum)


class TestSection11RecommendedNextEvidence:
    PASS = (
        "Evidence of payments actually made under these notices.",
        "Direct evidence of a named authority stating a need.",
        "Identification of whether an authority recurs across notices.",
        "Records of actual expenditure for these notices.",
    )
    FAIL = (
        "Actual expenditure was 10 million EUR.",
        "Evidence shows that buyers are willing to pay.",
        "Evidence of payments; buyers are clearly willing to pay.",
    )

    @pytest.mark.parametrize("item", PASS)
    def test_a_request_passes(self, item: str) -> None:
        assert is_request_shaped(item)
        assert passes("recommended_next_evidence", [item]), reasons_with(
            "recommended_next_evidence", [item]
        )

    @pytest.mark.parametrize("item", FAIL)
    def test_an_assertion_in_a_request_field_fails(self, item: str) -> None:
        assert not passes("recommended_next_evidence", [item]), item

    def test_the_shape_failure_is_named(self) -> None:
        reasons = reasons_with(
            "recommended_next_evidence", ["Actual expenditure was 10 million EUR."]
        )
        joined = " ".join(reasons)
        assert "request-shaped" in joined
        assert "REALISED_SPEND" in joined


class TestSection12CriticalUncertainties:
    PASS = (
        "Whether any authority is willing to pay.",
        "How many notices a single authority publishes is unknown.",
        "It is unknown whether the amounts were actually paid.",
    )
    FAIL = (
        "Customers definitely have an unmet need.",
        "Whether demand exists; it clearly does.",
        "Buyers are willing to pay.",
    )

    @pytest.mark.parametrize("item", PASS)
    def test_an_uncertainty_passes(self, item: str) -> None:
        assert is_uncertainty_shaped(item)
        assert passes("critical_uncertainties", [item]), reasons_with(
            "critical_uncertainties", [item]
        )

    @pytest.mark.parametrize("item", FAIL)
    def test_an_assertion_in_an_uncertainty_field_fails(self, item: str) -> None:
        assert not passes("critical_uncertainties", [item]), item


class TestTheHypothesisStatement:
    def test_a_framed_hypothesis_passes(self) -> None:
        assert passes("hypothesis_statement", "It is worth testing whether authorities would pay.")

    def test_an_unframed_one_is_an_assertion(self) -> None:
        assert not passes(
            "hypothesis_statement", "Authorities would pay, so a product should be built."
        )


# ============================================================================ §15 to §19


class TestSection15SupportUniverse:
    def test_the_three_categories_are_separate(self) -> None:
        assert {c.value for c in SupportCategory} == {
            "SOURCE_STATEMENTS",
            "PACKET_STRUCTURAL_FACTS",
            "TRUSTED_LIMITING_OR_DEFINITIONAL_CONTEXT",
        }
        universe = build_support_universe(PACKET, STATEMENTS, build_trusted_context(PACKET))
        assert set(universe.source_statements) == set(CLAIMS)
        assert universe.structural.evidence_ids == EVIDENCE
        assert universe.structural.subject_label == SUBJECT
        assert universe.structural.scoring_eligible_count == 2
        assert universe.trusted.version == TRUSTED_CONTEXT_VERSION

    def test_trusted_context_contributes_no_tokens_and_no_numbers(self) -> None:
        universe = build_support_universe(PACKET, STATEMENTS, build_trusted_context(PACKET))
        assert "renewals" not in universe.supplied_tokens()
        assert "161" not in universe.supplied_numbers()
        assert "BT-161" in universe.trusted.identifiers

    def test_statements_outside_the_packet_are_not_supplied(self) -> None:
        extra = {**STATEMENTS, "cccccccc-cccc-4ccc-8ccc-cccccccccccc": "Buyers pay 999 EUR."}
        universe = build_support_universe(PACKET, extra, build_trusted_context(PACKET))
        assert "999" not in universe.supplied_numbers()


class TestSection16MarketActivity:
    def test_the_canonical_term_is_derived_from_the_enum(self) -> None:
        assert canonical_dimension_phrase(EvidenceDimension.MARKET_ACTIVITY) == "market activity"

    def test_the_canonical_term_passes_where_the_packet_supports_it(self) -> None:
        assert passes(SUMMARY, "The notices are market activity in the bounded scope.")

    def test_market_does_not_become_globally_safe(self) -> None:
        for text in (
            "The market wants a scheduling platform.",
            "The market size is large.",
            "This market is growing.",
        ):
            assert "'market' appears in no supplied statement" in " ".join(
                reasons_with(SUMMARY, text)
            ), text

    def test_the_term_is_refused_where_the_packet_does_not_support_it(self) -> None:
        universe = build_support_universe(
            AUDIENCE_PACKET, STATEMENTS, build_trusted_context(AUDIENCE_PACKET)
        )
        verdict, findings = audit_text(
            "The requests show market activity.",
            Disposition.SUPPORTED_ASSERTION,
            Shape.FREE,
            universe,
            FORBIDDEN_CONCEPTS_V1_2,
            PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
            frozenset(AUDIENCE_PACKET.counting_dimensions),
        )
        assert verdict.value == "UNSUPPORTED"
        assert any("'market'" in f for f in findings)

    def test_an_answer_that_does_not_claim_the_dimension_cannot_use_its_term(self) -> None:
        output = good_output(supported_dimensions=["BUYER_OR_BUDGET_EXISTENCE", "ECONOMIC_VALUE"])
        assert not gate(output).persist


class TestSection18TrustedIdentifiers:
    BT = "Amounts include options and renewals under BT-161 and may be withheld under BT-195 to BT-198."

    def test_a_trusted_identifier_restated_as_a_limit_passes(self) -> None:
        assert passes(SUMMARY, self.BT), reasons_with(SUMMARY, self.BT)

    def test_it_passes_only_through_the_explicit_channel(self) -> None:
        empty = TrustedContext(version=TRUSTED_CONTEXT_VERSION, facts=())
        reasons = reasons_with(SUMMARY, self.BT, trusted=empty)
        assert any("161" in r for r in reasons)

    def test_a_trusted_identifier_never_supports_realised_spend(self) -> None:
        reasons = " ".join(reasons_with(SUMMARY, "Per BT-161, the actual expenditure was large."))
        assert "REALISED_SPEND" in reasons
        assert "can never support it" in reasons

    def test_a_trusted_identifier_never_supports_willingness_to_pay(self) -> None:
        reasons = " ".join(reasons_with(SUMMARY, "BT-161 shows willingness to pay."))
        assert "WILLINGNESS_TO_PAY" in reasons

    def test_an_unknown_external_definition_fails(self) -> None:
        for text in (
            "Under eForms BT-27 the estimated value differs.",
            "Directive 2014/24/EU defines these notices.",
        ):
            assert not passes(SUMMARY, text), text

    def test_a_trusted_number_is_not_a_magnitude(self) -> None:
        assert not passes(SUMMARY, "The notices cost 161 EUR.")

    def test_a_trusted_fact_licenses_none_of_its_words(self) -> None:
        """The bound says 'not ... for a SaaS product'; that does not make SaaS supplied."""
        assert "SaaS" in SIGNAL_DIMENSION_MAP["procurement_value_contrast"].bound
        assert not passes(SUMMARY, "Buyers want a SaaS product.")

    def test_every_trusted_fact_has_provenance_and_a_kind(self) -> None:
        context = build_trusted_context(PACKET)
        assert context.facts
        for fact in context.facts:
            assert fact.provenance.strip()
            assert isinstance(fact.kind, TrustedFactKind)
        bound = next(f for f in context.facts if f.fact_id.startswith("DIMENSION_BOUND:"))
        assert {"REALISED_SPEND", "WILLINGNESS_TO_PAY"} <= set(bound.never_supports)

    def test_a_fact_without_provenance_is_refused(self) -> None:
        with pytest.raises(ValueError, match="provenance"):
            TrustedFact("x", TrustedFactKind.LIMITING, "BT-1", " ", ())

    def test_the_digest_moves_with_the_facts(self) -> None:
        context = build_trusted_context(PACKET)
        shrunk = TrustedContext(version=context.version, facts=context.facts[1:])
        assert context.digest() != shrunk.digest()
        assert context.digest() == build_trusted_context(PACKET).digest()


class TestSection19PromptTextIsNotEvidence:
    def test_the_flag_is_true(self) -> None:
        assert PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE is True

    def test_a_word_that_only_the_prompt_uses_is_not_licensed(self) -> None:
        """The prompt's own refused example, *Operators need scheduling software*."""
        assert not passes(SUMMARY, "Operators need scheduling software.")

    def test_the_gate_has_no_default_trusted_channel(self) -> None:
        with pytest.raises(TypeError):
            evaluate_second_opportunity_output_v1_2(good_output(), PACKET, STATEMENTS, E2C)  # type: ignore[call-arg]

    def test_no_module_reads_a_prompt_region(self) -> None:
        for name in ("assertion_context.py", "second_opportunity_gate_v1_2.py"):
            source = (PACKAGE / name).read_text(encoding="utf-8")
            for forbidden in (
                "SYSTEM_V1_2",
                "SECOND_OPPORTUNITY_SYSTEM",
                "render_second_opportunity",
            ):
                assert forbidden not in source, (name, forbidden)


# ============================================================================ §20


class TestSection20ForbiddenConceptsStayForbidden:
    SECTION_20 = (
        "realised spend",
        "actual expenditure",
        "willingness to pay",
        "software demand",
        "product demand",
        "market size",
        "buyer need",
        "unmet need",
        "dissatisfaction",
        "solution gap",
        "competitive gap",
        "product-market fit",
        "profitability",
    )

    def test_no_v1_0_0_phrase_was_removed(self) -> None:
        by_name = {c.name: set(c.phrases) for c in FORBIDDEN_CONCEPTS_V1_2}
        for name, phrases in _FORBIDDEN_PHRASES.items():
            assert set(phrases) <= by_name[name], name

    def test_every_section_20_concept_is_named(self) -> None:
        phrases = {p for c in FORBIDDEN_CONCEPTS_V1_2 for p in c.phrases}
        for concept in self.SECTION_20:
            assert concept in phrases, concept

    @pytest.mark.parametrize("phrase", SECTION_20)
    def test_asserted_it_is_refused(self, phrase: str) -> None:
        assert not passes(SUMMARY, f"The notices show {phrase}."), phrase

    @pytest.mark.parametrize("phrase", [p for p in SECTION_20 if p != "product-market fit"])
    def test_denied_it_passes(self, phrase: str) -> None:
        text = f"The packet does not establish {phrase}."
        assert passes(SUMMARY, text), reasons_with(SUMMARY, text)

    def test_validation_vocabulary_is_still_refused_unconditionally(self) -> None:
        """v1.1.0 refused it even in a denial, and v1.2.0 weakens nothing."""
        assert not passes(SUMMARY, "The packet does not establish a proven need.")


# ============================================================================ §4, unseen equivalents


class TestSection4UnseenEquivalents:
    """The shapes of the five historical refusals, in wording the historical answer never used."""

    def test_scorability_with_a_denied_score(self) -> None:
        text = "Each row is SCORABLE; scoring-ready does not mean scored, and there is no score."
        assert passes("reliability_status", text), reasons_with("reliability_status", text)

    def test_a_trusted_identifier_and_the_canonical_term(self) -> None:
        text = (
            "Amounts include options and renewals under BT-161, and the notices are market "
            "activity within the bounded scope."
        )
        assert passes(SUMMARY, text), reasons_with(SUMMARY, text)

    def test_the_refused_phrases_in_their_legitimate_places(self) -> None:
        output = good_output(
            hypothesis_statement=(
                "It is worth testing whether authorities would pay; nothing supplied establishes "
                "willingness to pay."
            ),
            commercial_claims_not_supported=["An authority would pay for a new product."],
            recommended_next_evidence=["Records of actual expenditure for these notices."],
        )
        assert gate(output).persist, gate(output).refusal_reasons


# ============================================================================ structure


class TestAdversarialAssertions:
    """Assertions dressed as denials, and denials in unusual dress. Frozen with the gate."""

    MUST_FAIL = (
        ("There is no doubt that buyers would pay.", "would pay"),
        ("Buyers would pay, which is not established.", "would pay"),
        ("Evidence of actual expenditure exists.", "actual expenditure"),
        ("Whether buyers would pay is unknown, but they probably would.", "would pay"),
        (
            "Nothing establishes demand for software, yet the notices show demand for it.",
            "demand for",
        ),
        ("Buyers are willing to pay; no evidence establishes it.", "willing to pay"),
        ("Nevertheless, buyers would pay.", "would pay"),
        ("Buyers are not only willing to pay but eager.", "willing to pay"),
    )
    MUST_PASS = (
        ("Buyers aren’t willing to pay, on this evidence.", "willing to pay"),
        ("NO EVIDENCE ESTABLISHES WILLINGNESS TO PAY.", "willingness to pay"),
        ("Willingness to pay: not established.", "willingness to pay"),
        ("Unsupported: willingness to pay, actual expenditure.", "actual expenditure"),
        ("It remains unknown whether buyers would pay.", "would pay"),
        ("The packet cannot establish whether buyers would pay.", "would pay"),
        ("Published ceilings rather than actual expenditure.", "actual expenditure"),
        ("The rows are SCORABLE (not scored).", "scored"),
    )

    @pytest.mark.parametrize(("text", "phrase"), MUST_FAIL)
    def test_an_assertion_in_disguise_is_asserted(self, text: str, phrase: str) -> None:
        assert is_asserted(text, phrase), text

    @pytest.mark.parametrize(("text", "phrase"), MUST_PASS)
    def test_a_denial_in_unusual_dress_is_not_asserted(self, text: str, phrase: str) -> None:
        assert not is_asserted(text, phrase), text

    def test_a_relative_clause_cannot_smuggle_an_assertion_into_a_request(self) -> None:
        assert not passes(
            "recommended_next_evidence", ["Evidence of payments, which proves market demand."]
        )

    def test_a_request_needs_a_requirement_outside_a_request_field(self) -> None:
        assert not passes(SUMMARY, "Evidence of actual expenditure exists.")
        assert passes(SUMMARY, "Evidence of actual expenditure would be required.")

    def test_a_contraction_and_a_curly_apostrophe_still_deny(self) -> None:
        assert passes(SUMMARY, "The packet doesn’t establish willingness to pay.")


class TestStructuralFactsTheGateNowChecks:
    def test_the_subject_must_be_the_packets(self) -> None:
        assert not passes("subject", "ted-eu:CPV-class:1234")

    def test_a_family_the_packet_does_not_carry_is_refused(self) -> None:
        assert not passes("source_families", ["public_procurement", "knowledge"])

    def test_a_dimension_cannot_be_both_supported_and_unsupported(self) -> None:
        assert not passes("unsupported_dimensions", [*MANDATORY, "MARKET_ACTIVITY"])

    def test_the_v1_1_0_structural_checks_still_hold(self) -> None:
        assert not passes("supporting_evidence_ids", ["33333333-3333-4333-8333-333333333333"])
        assert not passes("supported_dimensions", ["WILLINGNESS_TO_PAY"])
        assert not passes("unsupported_dimensions", MANDATORY[1:])
        assert not passes("independence_status", "Independent sources agree.")


# ============================================================================ §21


#: bb0f50a's bytes. A historical gate resolves against the code it ran, so these must not move.
HISTORICAL_SHA256 = {
    "guards.py": "41c732fa3ccc8210cd0131c4ee9bb3ac5f181c6a4a5a68459b71c37a17e5e29c",
    "validation.py": "c62c3f91bc2255a411435eb8256f4a055c4f816a5172d3496c4382d96ddc8ed6",
    "second_opportunity.py": "24ba090d3ff750ae95105458ba5528a1597449a902184a1d009b58dc9bc9221b",
    "schema_validation.py": "243ef0532deaf6c85c3cee1e3cac50e8bfe356a45061d3f9f1beaf68b09ed790",
}


class TestSection21Versioning:
    def test_the_gate_is_a_new_version(self) -> None:
        assert SECOND_OPPORTUNITY_GATE_VERSION_V1_2 == "second-opportunity-output-gate@1.2.0"
        assert SECOND_OPPORTUNITY_GATE_VERSION_V1_1 == "second-opportunity-output-gate@1.1.0"

    def test_every_changed_component_has_its_own_version(self) -> None:
        assert COMPONENT_VERSIONS_V1_2 == {
            "gate": "second-opportunity-output-gate@1.2.0",
            "output_schema": "second-opportunity-synthesis-output@1.1.0",
            "persistence_gate": "opportunity-synthesis-persistence-gate@1.2.0",
            "audit": "opportunity-synthesis-audit@1.3.0",
            "claim_guard": "opportunity-claim-guard@1.3.0",
            "field_context_policy": "second-opportunity-field-context-policy@1.0.0",
            "support_universe": "opportunity-support-universe@1.0.0",
            "trusted_context": "second-opportunity-trusted-context@1.0.0",
        }

    @pytest.mark.parametrize("name", sorted(HISTORICAL_SHA256))
    def test_the_historical_modules_are_byte_identical(self, name: str) -> None:
        digest = hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest()
        assert digest == HISTORICAL_SHA256[name], name

    def test_the_v1_1_0_gate_still_refuses_what_it_refused(self) -> None:
        """A denial v1.1.0 refused is still refused by v1.1.0: nothing old was loosened."""
        decision = evaluate_second_opportunity_output_v1_1(
            good_output(**{SUMMARY: "No evidence establishes actual expenditure."}),
            PACKET,
            STATEMENTS,
            E2C,
        )
        assert decision.gate_version == SECOND_OPPORTUNITY_GATE_VERSION_V1_1
        assert any("REALISED_SPEND" in r for r in decision.refusal_reasons)

    def test_the_operator_decision_is_carried_as_data(self) -> None:
        assert SEMANTIC_GATE_REPAIR_DECISION == (
            "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED",
            "KEEP_PROMPT_V1_2_0_UNCHANGED",
            "REPAIR_SEMANTIC_GATE_ASSERTION_CONTEXT",
            "DO_NOT_WHITELIST_THE_V3_ANSWER",
            "DO_NOT_REMOVE_FORBIDDEN_CONCEPTS",
            "DO_NOT_WEAKEN_EVIDENCE_BOUNDARIES",
        )


# ============================================================================ §4, no whitelist


def _shingles(text: str, width: int = 6) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(words[i : i + width]) for i in range(len(words) - width + 1)}


class TestNoAnswerIsWhitelisted:
    def test_no_six_word_run_of_the_historical_answer_is_in_the_gate(self) -> None:
        response = json.loads(
            (DATA / "second-opportunity-synthesis-response-v3.json").read_text(encoding="utf-8")
        )
        answer: set[str] = set()

        def walk(value: object) -> None:
            if isinstance(value, str):
                answer.update(_shingles(value))
            elif isinstance(value, list):
                for item in value:
                    walk(item)
            elif isinstance(value, dict):
                for item in value.values():
                    walk(item)

        walk(response["parsed_output"])
        for name in ("assertion_context.py", "second_opportunity_gate_v1_2.py"):
            source = _shingles((PACKAGE / name).read_text(encoding="utf-8"))
            assert not (answer & source), (name, sorted(answer & source)[:5])

    def test_no_case_in_this_file_is_the_historical_answer(self) -> None:
        response = json.loads(
            (DATA / "second-opportunity-synthesis-response-v3.json").read_text(encoding="utf-8")
        )
        own = pathlib.Path(__file__).read_text(encoding="utf-8")
        texts = [v for v in json.dumps(response["parsed_output"]).split('"') if len(v.split()) >= 8]
        assert not [t for t in texts if t in own]


def test_the_good_output_is_not_mutated_by_the_gate() -> None:
    output = good_output()
    before = copy.deepcopy(output)
    gate(output)
    assert output == before
