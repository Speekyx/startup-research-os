"""The interpretation contract, over synthetic objects only.

Mission 1.13 §53. **No network, no database, no LLM.** Every statement below is
invented; the ones shaped after the seven real Signals say so.

The suite is organised around the boundary the mission exists to draw:

    §3   a Signal never automatically becomes a market Claim
    §6   OBSERVED restates what a source reported
    §7   INFERRED asserts something the source did not measure
    §8   HYPOTHESIS may be unsupported, and says so on its face
    §11  Evidence is claim-relative, so it lives on neither the Signal nor alone
    §20  a model is a reasoning mechanism, never the evidence
    §22  a machine may not store an unsupported assertion
"""

from __future__ import annotations

import unittest

from sros_claim_model import (
    AUTOMATED_ORIGINS,
    ClaimInterpretation,
    ClaimRefusedError,
    EvidenceDraft,
    build_claim,
    canonical_json,
    proposition_key,
    requires_evidence,
)
from sros_contracts import (
    ClaimEvidenceRefusalReason,
    ClaimInterpretationKind,
    ClaimOrigin,
    ClaimTemporality,
    ClaimType,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
)

WORKSPACE = "11111111-1111-4111-8111-111111111111"

DETERMINISTIC = ClaimInterpretation(
    interpreter_id="numeric-period-change-observed",
    interpreter_version="1.0.0",
    kind=ClaimInterpretationKind.DETERMINISTIC,
)

# SYNTHETIC, shaped after the real World Bank signal DE 2018 -> 2019.
WORLD_BANK_FACTS = {
    "source_id": "world-bank",
    "metric_id": "SP.POP.TOTL",
    "geography_code": "DE",
    "period_from": "2018",
    "period_to": "2019",
    "direction": "INCREASING",
}

OBSERVED_STATEMENT = (
    "World Bank reported that the measured value of SP.POP.TOTL for DE increased "
    "by 187,180 between 2018 and 2019."
)


def evidence(**overrides) -> EvidenceDraft:
    kwargs = {
        "signal_id": "sig-1",
        "direction": EvidenceDirection.SUPPORTS,
        "source_id": "world-bank",
        "observation_category": EvidenceObservationCategory.MARKET_ACTIVITY,
        "relevance": 1.0,
        "directness": 1.0,
    }
    kwargs.update(overrides)
    return EvidenceDraft(**kwargs)


def observed(**overrides):
    kwargs = {
        "workspace_id": WORKSPACE,
        "claim_type": ClaimType.OBSERVED,
        "temporality": ClaimTemporality.EVERGREEN,
        "origin": ClaimOrigin.DETERMINISTIC_EXTRACTION,
        "statement": OBSERVED_STATEMENT,
        "facts": WORLD_BANK_FACTS,
        "evidence": [evidence()],
        "interpretation": DETERMINISTIC,
        "interpretation_confidence": 1.0,
    }
    kwargs.update(overrides)
    return build_claim(**kwargs)


# ============================================ §3 a Signal is not a market Claim


class TestTheInterpretationBoundary(unittest.TestCase):
    def test_a_faithful_restatement_is_observed(self):
        draft = observed()
        self.assertIs(draft.claim_type, ClaimType.OBSERVED)
        self.assertEqual(draft.cited_signal_ids, ("sig-1",))

    def test_an_observed_claim_may_not_assert_demand(self):
        """§3's first example. The arithmetic is identical and the proposition
        is not."""
        with self.assertRaises(ClaimRefusedError) as caught:
            observed(statement="The German SaaS market is growing, per population data.")
        self.assertIs(
            caught.exception.refusal.reason,
            ClaimEvidenceRefusalReason.UNSUPPORTED_INTERPRETATION,
        )

    def test_an_observed_claim_may_not_assert_interest(self):
        with self.assertRaises(ClaimRefusedError) as caught:
            observed(statement="Interest in climate SaaS is growing.")
        self.assertIs(
            caught.exception.refusal.reason,
            ClaimEvidenceRefusalReason.UNSUPPORTED_INTERPRETATION,
        )

    def test_an_observed_claim_may_not_assert_an_opportunity(self):
        with self.assertRaises(ClaimRefusedError):
            observed(statement="Climate represents a better business opportunity.")

    def test_the_same_sentence_is_permitted_as_inferred(self):
        """The vocabulary is not banned from the system. It is banned from
        OBSERVED, which is where the epistemic line is."""
        draft = observed(
            claim_type=ClaimType.INFERRED,
            statement="Media attention around climate appears to be increasing.",
            origin=ClaimOrigin.INFERRED,
        )
        self.assertIs(draft.claim_type, ClaimType.INFERRED)

    def test_a_market_named_metric_must_be_restated_by_id(self):
        """The stated cost of catching §3's example with the bare word. A source
        metric whose published TITLE contains it cannot be restated by title."""
        with self.assertRaises(ClaimRefusedError):
            observed(
                statement="World Bank reported market capitalization of listed "
                "companies for DE rose in 2019.",
                facts={**WORLD_BANK_FACTS, "metric_id": "CM.MKT.LCAP.CD"},
            )
        draft = observed(
            statement="World Bank reported CM.MKT.LCAP.CD for DE rose in 2019.",
            facts={**WORLD_BANK_FACTS, "metric_id": "CM.MKT.LCAP.CD"},
        )
        self.assertIs(draft.claim_type, ClaimType.OBSERVED)

    def test_growth_is_not_treated_as_interpretive_vocabulary(self):
        """`population growth` is the name of a quantity a source publishes.
        A guard that refused it would refuse a faithful restatement."""
        draft = observed(
            statement="World Bank reported population growth of 187,180 for DE in 2019."
        )
        self.assertIs(draft.claim_type, ClaimType.OBSERVED)


# ================================================== §22 unsupported claim rules


class TestEvidenceRequirement(unittest.TestCase):
    def test_a_generated_claim_with_no_evidence_is_refused(self):
        with self.assertRaises(ClaimRefusedError) as caught:
            observed(evidence=[])
        self.assertIs(
            caught.exception.refusal.reason,
            ClaimEvidenceRefusalReason.NO_SUPPORTING_SIGNAL,
        )

    def test_a_hypothesis_may_be_unsupported(self):
        """§8. The exemption is the category's definition: requiring evidence
        would make HYPOTHESIS unusable and push unsupported ideas into
        INFERRED, which is the failure the rule exists to prevent."""
        draft = observed(
            claim_type=ClaimType.HYPOTHESIS,
            statement="Developers may be willing to pay for a tool solving deployment.",
            origin=ClaimOrigin.SYSTEM_GENERATED,
            evidence=[],
        )
        self.assertIs(draft.claim_type, ClaimType.HYPOTHESIS)
        self.assertEqual(draft.evidence, ())

    def test_a_manual_claim_may_be_unsupported(self):
        """A person asserting something and looking for evidence afterwards is
        the ordinary research motion. The rule is about what a MACHINE stores."""
        draft = observed(
            origin=ClaimOrigin.MANUAL,
            evidence=[],
            interpretation=None,
            interpretation_confidence=None,
        )
        self.assertIs(draft.origin, ClaimOrigin.MANUAL)

    def test_the_requirement_is_stated_as_a_function(self):
        for claim_type in ClaimType:
            for origin in ClaimOrigin:
                expected = claim_type is not ClaimType.HYPOTHESIS and origin in AUTOMATED_ORIGINS
                self.assertIs(requires_evidence(claim_type, origin), expected)

    def test_a_generated_evidence_row_may_not_be_neutral(self):
        """§12. A Signal that bears on nothing produces no row; attaching it
        would inflate the record without changing what is supported."""
        with self.assertRaises(ClaimRefusedError) as caught:
            observed(evidence=[evidence(direction=EvidenceDirection.NEUTRAL)])
        self.assertIs(
            caught.exception.refusal.reason,
            ClaimEvidenceRefusalReason.UNSUPPORTED_INTERPRETATION,
        )

    def test_evidence_must_cite_a_signal(self):
        with self.assertRaises(ClaimRefusedError) as caught:
            evidence(signal_id="   ")
        self.assertIs(caught.exception.refusal.reason, ClaimEvidenceRefusalReason.SIGNAL_NOT_CITED)


# ============================================================ §20 the LLM boundary


class TestInterpreterProvenance(unittest.TestCase):
    def test_a_deterministic_interpretation_carries_no_model(self):
        with self.assertRaises(ClaimRefusedError) as caught:
            ClaimInterpretation(
                interpreter_id="x",
                interpreter_version="1.0.0",
                kind=ClaimInterpretationKind.DETERMINISTIC,
                model_version="some-model",
            )
        self.assertIs(
            caught.exception.refusal.reason,
            ClaimEvidenceRefusalReason.INTERPRETER_PROVENANCE_INCOMPLETE,
        )

    def test_a_model_derived_interpretation_must_name_its_model(self):
        with self.assertRaises(ClaimRefusedError):
            ClaimInterpretation(
                interpreter_id="x",
                interpreter_version="1.0.0",
                kind=ClaimInterpretationKind.MODEL_DERIVED,
            )

    def test_a_model_derived_interpretation_is_permitted_with_provenance(self):
        interpretation = ClaimInterpretation(
            interpreter_id="x",
            interpreter_version="1.0.0",
            kind=ClaimInterpretationKind.MODEL_DERIVED,
            model_version="claude-x",
            prompt_version="p1",
        )
        draft = observed(
            claim_type=ClaimType.INFERRED,
            statement="Media coverage of climate appears to have risen.",
            origin=ClaimOrigin.LLM_EXTRACTION,
            interpretation=interpretation,
            interpretation_confidence=0.7,
        )
        self.assertEqual(draft.interpretation.model_version, "claude-x")

    def test_a_model_derived_claim_still_needs_evidence(self):
        """§20. LLM output cannot itself satisfy Evidence. A model-derived claim
        with nothing cited is refused exactly like a deterministic one."""
        interpretation = ClaimInterpretation(
            interpreter_id="x",
            interpreter_version="1.0.0",
            kind=ClaimInterpretationKind.MODEL_DERIVED,
            model_version="claude-x",
        )
        with self.assertRaises(ClaimRefusedError) as caught:
            observed(
                claim_type=ClaimType.INFERRED,
                statement="Media coverage appears to have risen.",
                origin=ClaimOrigin.LLM_EXTRACTION,
                interpretation=interpretation,
                interpretation_confidence=0.7,
                evidence=[],
            )
        self.assertIs(
            caught.exception.refusal.reason,
            ClaimEvidenceRefusalReason.NO_SUPPORTING_SIGNAL,
        )

    def test_a_generated_claim_names_its_interpreter(self):
        with self.assertRaises(ClaimRefusedError) as caught:
            observed(interpretation=None)
        self.assertIs(
            caught.exception.refusal.reason,
            ClaimEvidenceRefusalReason.INTERPRETER_PROVENANCE_INCOMPLETE,
        )

    def test_a_generated_claim_states_its_interpretation_confidence(self):
        with self.assertRaises(ClaimRefusedError):
            observed(interpretation_confidence=None)

    def test_half_an_interpreter_identity_is_refused(self):
        with self.assertRaises(ClaimRefusedError):
            ClaimInterpretation(
                interpreter_id="x",
                interpreter_version="  ",
                kind=ClaimInterpretationKind.DETERMINISTIC,
            )

    def test_no_chain_of_thought_field_exists(self):
        """§46. A short rationale and cited facts are persisted; a private
        reasoning transcript is not, and there is nowhere to put one."""
        draft = observed(rationale="Signal sig-1 reports 82905782 -> 83092962.")
        serialised = canonical_json(draft.to_json())
        for forbidden in ("chain_of_thought", "reasoning_trace", "thoughts", "scratchpad"):
            self.assertNotIn(forbidden, serialised)
        self.assertFalse(hasattr(draft, "chain_of_thought"))


# ================================================================ §17 identity


class TestPropositionIdentity(unittest.TestCase):
    def test_the_same_facts_give_the_same_key(self):
        self.assertEqual(
            proposition_key(WORLD_BANK_FACTS),
            proposition_key(dict(reversed(list(WORLD_BANK_FACTS.items())))),
        )

    def test_rewording_does_not_move_the_claim(self):
        """Two interpreters wording the same fact differently have produced ONE
        claim, and a claim reworded in revision 3 is still the same claim."""
        first = observed()
        second = observed(
            statement="Between 2018 and 2019 World Bank's SP.POP.TOTL figure for DE rose "
            "by 187,180."
        )
        self.assertEqual(first.proposition_key, second.proposition_key)

    def test_different_facts_are_different_claims(self):
        other = observed(facts={**WORLD_BANK_FACTS, "geography_code": "FR"})
        self.assertNotEqual(observed().proposition_key, other.proposition_key)

    def test_the_research_question_is_not_part_of_identity(self):
        """§39. Two sessions asking different questions that both derive the
        same fact have produced the same claim, and should."""
        first = observed(research_session_id="session-a")
        second = observed(research_session_id="session-b")
        self.assertEqual(first.proposition_key, second.proposition_key)

    def test_an_empty_fact_set_cannot_identify_a_proposition(self):
        with self.assertRaises(ClaimRefusedError) as caught:
            observed(facts={})
        self.assertIs(
            caught.exception.refusal.reason,
            ClaimEvidenceRefusalReason.PROPOSITION_NOT_IDENTIFIABLE,
        )

    def test_identity_never_depends_on_an_embedding(self):
        """D-12 is open. Two claims whose prose is nearly identical and whose
        facts differ are DIFFERENT claims, which no vector distance would say."""
        near_identical = observed(
            statement=OBSERVED_STATEMENT.replace("DE", "FR"),
            facts={**WORLD_BANK_FACTS, "geography_code": "FR"},
        )
        self.assertNotEqual(observed().proposition_key, near_identical.proposition_key)


# ================================================= §11-§16 evidence is claim-relative


class TestEvidenceSemantics(unittest.TestCase):
    def test_one_signal_may_bear_on_two_claims_differently(self):
        """The reason relevance, directness and direction live on Evidence and
        not on the Signal: the Signal has never heard of the claim."""
        supports = evidence(direction=EvidenceDirection.SUPPORTS, relevance=1.0)
        contradicts = evidence(direction=EvidenceDirection.CONTRADICTS, relevance=0.2)
        self.assertEqual(supports.signal_id, contradicts.signal_id)
        self.assertIsNot(supports.direction, contradicts.direction)

    def test_factors_out_of_range_are_rejected_not_clamped(self):
        for name in ("relevance", "directness", "reliability", "extraction_confidence"):
            with self.assertRaises(ValueError):
                evidence(**{name: 1.4})

    def test_a_factor_may_be_absent(self):
        """An absent factor is NON_SCORABLE at aggregation time, never 0.5 and
        never 0.0 (evidence-aggregation-framework-v1.md §6)."""
        item = evidence(relevance=None, directness=None)
        self.assertNotIn("relevance", item.to_json())

    def test_dependent_evidence_must_name_its_group(self):
        with self.assertRaises(ValueError):
            evidence(independence_state=EvidenceIndependenceState.KNOWN_DEPENDENT)

    def test_independent_evidence_may_not_name_a_group(self):
        with self.assertRaises(ValueError):
            evidence(
                independence_state=EvidenceIndependenceState.KNOWN_INDEPENDENT,
                independence_group_id="g-1",
            )

    def test_unknown_independence_is_the_default(self):
        self.assertIs(evidence().independence_state, EvidenceIndependenceState.UNKNOWN)

    def test_evidence_records_its_source_for_later_grouping(self):
        """§35. Two Signals from one publication stream are not automatically
        independent. The source travels; the judgement does not happen here."""
        item = evidence(source_id="gdelt")
        self.assertEqual(item.to_json()["source_id"], "gdelt")

    def test_evidence_carries_no_score(self):
        item = evidence()
        serialised = canonical_json(item.to_json())
        for forbidden in ("evidence_score", "support_strength", "mass", "score"):
            self.assertNotIn(forbidden, serialised)


class TestClaimShape(unittest.TestCase):
    def test_a_claim_needs_no_opportunity(self):
        """ADR-024. The pipeline runs Signal -> Claim -> Opportunity, so a claim
        about a source fact exists before anybody has thought of the product."""
        self.assertIsNone(observed().opportunity_id)

    def test_a_claim_may_name_an_opportunity(self):
        self.assertEqual(observed(opportunity_id="opp-1").opportunity_id, "opp-1")

    def test_a_blank_statement_is_refused(self):
        with self.assertRaises(ValueError):
            observed(statement="   ")

    def test_a_workspace_is_never_defaulted(self):
        with self.assertRaises(ValueError):
            observed(workspace_id="  ")

    def test_confidence_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            observed(interpretation_confidence=1.4)

    def test_the_five_claim_types_are_unchanged(self):
        """§5. Mission 1.13 changed no epistemic vocabulary."""
        self.assertEqual(
            {t.value for t in ClaimType},
            {"OBSERVED", "INFERRED", "PREDICTED", "RECOMMENDED", "HYPOTHESIS"},
        )

    def test_a_claim_carries_no_score_and_no_market_field(self):
        serialised = canonical_json(observed().to_json()).lower()
        for forbidden in (
            "evidence_score",
            "opportunity_score",
            "demand",
            "market_size",
            "revenue",
            "mrr",
        ):
            self.assertNotIn(forbidden, serialised)


if __name__ == "__main__":
    unittest.main()
