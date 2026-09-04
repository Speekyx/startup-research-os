"""Mission 1.39 §35. The convergence contract, and every near miss it must survive.

**The near-miss tests are the load-bearing half.** A convergence rule that makes
two cohorts agree is easy; one that makes them agree *and* keeps Docker apart
from Podman is the thing worth having. §9 names those as a mandatory regression
case, and Mission 1.38 identified exactly that danger: twelve existing claim
pairs differ in one fact, `content_id`.

`unittest`, no third-party dependency, so this runs in the zero-dependency CI
job (ADR-009).
"""

from __future__ import annotations

import unittest

from sros_claim_model import (
    CONVERGENCE_CONTRACTS,
    ObservationOverlap,
    PropositionConvergenceContract,
    QualificationOutcome,
    SourceBoundary,
    contract_for,
    convergent_proposition_key,
    distinct_witnesses,
    identity_facts,
    overlap_between,
    proposition_key,
    qualify,
    witness_facts,
    witness_key,
)
from sros_contracts import ClaimTemporality, ClaimType

KIND = "source_published_classification_value_contrast_witnessed"
SIGNAL_TYPE = "procurement_value_contrast"

COHORT_A = {
    "proposition": KIND,
    "source_id": "ted-eu",
    "resource_id": "notices/eforms-contract-and-award",
    "notice_class": "CONTRACT_AWARD_NOTICE",
    "amount_type": "TOTAL_VALUE",
    "amount_scope": "NOTICE",
    "currency": "EUR",
    "classification_scheme": "CPV",
    "classification_division": "90",
    "classification_codes": ["90500000", "90510000"],
    "notice_ids": ["N-1", "N-2", "N-3"],
    "relation": "DIFFERS",
}

# A genuinely different observation: different notices, different codes beneath
# the same division. Same assertion, different witness.
COHORT_B = {
    **COHORT_A,
    "classification_codes": ["90900000"],
    "notice_ids": ["N-4", "N-5"],
}


def contract() -> PropositionConvergenceContract:
    found = contract_for(KIND)
    assert found is not None
    return found


class TheContractDeclaresItselfCompletely(unittest.TestCase):
    def test_exactly_one_contract_is_registered(self) -> None:
        """§15: generic machinery, one narrow proposition to prove it."""
        self.assertEqual(set(CONVERGENCE_CONTRACTS), {KIND})

    def test_it_is_observed_and_evergreen(self) -> None:
        self.assertIs(contract().claim_type, ClaimType.OBSERVED)
        self.assertIs(contract().temporality, ClaimTemporality.EVERGREEN)

    def test_the_source_boundary_is_same_source_and_resource(self) -> None:
        """§7. Narrow on purpose, and no cross-source member exists to pass."""
        self.assertIs(contract().source_boundary, SourceBoundary.SAME_SOURCE_AND_RESOURCE)
        self.assertEqual(len(SourceBoundary), 1)

    def test_identity_and_witness_fields_are_disjoint(self) -> None:
        self.assertFalse(set(contract().identity_fields) & set(contract().witness_fields))

    def test_it_says_what_it_does_not_establish(self) -> None:
        """§6. Prevalence is what a reader supplies when nobody said otherwise."""
        refused = " ".join(contract().does_not_establish).lower()
        for forbidden in (
            "proportion",
            "typical",
            "trend",
            "demand",
            "market size",
            "willingness to pay",
            "independent",
        ):
            self.assertIn(forbidden, refused)

    def test_a_contract_without_source_id_in_identity_is_refused(self) -> None:
        """§7 and the Mission 1.38 boundary, enforced in the constructor."""
        with self.assertRaises(ValueError) as caught:
            PropositionConvergenceContract(
                contract_id="bad",
                version="1.0.0",
                proposition_kind="x",
                claim_type=ClaimType.OBSERVED,
                temporality=ClaimTemporality.EVERGREEN,
                source_boundary=SourceBoundary.SAME_SOURCE_AND_RESOURCE,
                identity_fields=("proposition",),
                witness_fields=("w",),
                qualifying_signal_types=("s",),
                establishes="e",
                does_not_establish=("n",),
            )
        self.assertIn("Attribution is part of the proposition", str(caught.exception))

    def test_an_inferred_contract_is_refused(self) -> None:
        """§5. V1 authorises OBSERVED convergence only, and the refusal says why."""
        with self.assertRaises(ValueError) as caught:
            PropositionConvergenceContract(
                contract_id="bad",
                version="1.0.0",
                proposition_kind="x",
                claim_type=ClaimType.INFERRED,
                temporality=ClaimTemporality.EVERGREEN,
                source_boundary=SourceBoundary.SAME_SOURCE_AND_RESOURCE,
                identity_fields=("proposition", "source_id"),
                witness_fields=("w",),
                qualifying_signal_types=("s",),
                establishes="e",
                does_not_establish=("n",),
            )
        self.assertIn("interpretation layer that does not exist", str(caught.exception))

    def test_a_contract_with_no_witness_field_cannot_converge(self) -> None:
        with self.assertRaises(ValueError) as caught:
            PropositionConvergenceContract(
                contract_id="bad",
                version="1.0.0",
                proposition_kind="x",
                claim_type=ClaimType.OBSERVED,
                temporality=ClaimTemporality.EVERGREEN,
                source_boundary=SourceBoundary.SAME_SOURCE_AND_RESOURCE,
                identity_fields=("proposition", "source_id"),
                witness_fields=(),
                qualifying_signal_types=("s",),
                establishes="e",
                does_not_establish=("n",),
            )
        self.assertIn("the same observation", str(caught.exception))


class TwoDisjointCohortsWitnessOneProposition(unittest.TestCase):
    """The case Mission 1.38 said should be representable and was not."""

    def test_they_share_a_proposition_key(self) -> None:
        self.assertEqual(
            convergent_proposition_key(contract(), COHORT_A),
            convergent_proposition_key(contract(), COHORT_B),
        )

    def test_their_witness_keys_differ(self) -> None:
        """§10. Two Evidence rows may not differ only in a generated uuid."""
        self.assertNotEqual(witness_key(contract(), COHORT_A), witness_key(contract(), COHORT_B))
        self.assertTrue(distinct_witnesses(contract(), [COHORT_A, COHORT_B]))

    def test_the_same_cohort_twice_is_one_witness(self) -> None:
        """§19's duplicate-witness guard, on the fact that matters."""
        self.assertFalse(distinct_witnesses(contract(), [COHORT_A, dict(COHORT_A)]))

    def test_identity_and_witness_split_covers_every_fact(self) -> None:
        """§3. A fact nobody classified would silently become identity, because
        the key is built from whatever is in the mapping."""
        split = set(identity_facts(contract(), COHORT_A)) | set(witness_facts(contract(), COHORT_A))
        self.assertEqual(split, set(COHORT_A))

    def test_witness_facts_are_retained_rather_than_discarded(self) -> None:
        witness = witness_facts(contract(), COHORT_A)
        self.assertEqual(witness["notice_ids"], ["N-1", "N-2", "N-3"])
        self.assertEqual(witness["classification_codes"], ["90500000", "90510000"])

    def test_qualification_is_deterministic_and_three_valued(self) -> None:
        outcome, _ = qualify(contract(), COHORT_A, signal_type_id=SIGNAL_TYPE)
        self.assertIs(outcome, QualificationOutcome.QUALIFIES)

        missing = {k: v for k, v in COHORT_A.items() if k != "currency"}
        outcome, detail = qualify(contract(), missing, signal_type_id=SIGNAL_TYPE)
        self.assertIs(outcome, QualificationOutcome.MISSING_REQUIRED_FACT)
        self.assertIn("not a wildcard", detail)

        outcome, _ = qualify(contract(), COHORT_A, signal_type_id="content_request_change")
        self.assertIs(outcome, QualificationOutcome.DOES_NOT_QUALIFY)

    def test_an_undeclared_fact_is_refused_rather_than_absorbed(self) -> None:
        outcome, detail = qualify(
            contract(), {**COHORT_A, "surprise": 1}, signal_type_id=SIGNAL_TYPE
        )
        self.assertIs(outcome, QualificationOutcome.DOES_NOT_QUALIFY)
        self.assertIn("silently become identity", detail)


class NearMissesMustNotConverge(unittest.TestCase):
    """§9. Every field whose change changes what is asserted."""

    def _differs(self, **overrides: object) -> None:
        other = {**COHORT_A, **overrides}
        self.assertNotEqual(
            convergent_proposition_key(contract(), COHORT_A),
            convergent_proposition_key(contract(), other),
            f"{sorted(overrides)} must not converge",
        )

    def test_a_different_source_does_not_converge(self) -> None:
        self._differs(source_id="usaspending")

    def test_a_different_resource_does_not_converge(self) -> None:
        self._differs(resource_id="notices/other")

    def test_a_different_classification_division_does_not_converge(self) -> None:
        self._differs(classification_division="80")

    def test_a_different_classification_scheme_does_not_converge(self) -> None:
        self._differs(classification_scheme="UNSPSC")

    def test_a_different_notice_class_does_not_converge(self) -> None:
        self._differs(notice_class="CONTRACT_NOTICE")

    def test_different_measurement_semantics_do_not_converge(self) -> None:
        self._differs(amount_type="ESTIMATED_VALUE")
        self._differs(amount_scope="LOT")
        self._differs(currency="SEK")

    def test_a_different_asserted_relation_does_not_converge(self) -> None:
        """DIFFERS and EQUAL are two assertions, not two readings of one."""
        self._differs(relation="EQUAL")

    def test_a_different_proposition_kind_does_not_converge(self) -> None:
        self._differs(proposition="source_reported_procurement_value_contrast")


class TheDockerRegressionCase(unittest.TestCase):
    """§9's mandatory case. Mission 1.38 measured twelve pairs one field apart.

    These are the REAL Wikimedia fact shapes. They must not collapse, and the
    reason they cannot is that no contract is registered for their proposition
    kind -- convergence is opt-in per kind, never a property of the machinery.
    """

    WIKIMEDIA = {
        "proposition": "platform_counted_content_request_change",
        "source_id": "wikimedia-pageviews",
        "content_platform": "en.wikipedia.org",
        "audience_class": "user",
        "period_label_from": "2024-03-01",
        "period_label_to": "2024-03-02",
        "direction": "INCREASING",
    }

    def test_docker_podman_and_kubernetes_have_three_distinct_keys(self) -> None:
        keys = {
            proposition_key({**self.WIKIMEDIA, "content_id": subject})
            for subject in ("Docker_(software)", "Podman", "Kubernetes")
        }
        self.assertEqual(len(keys), 3)

    def test_their_proposition_kind_has_no_convergence_contract(self) -> None:
        """Opt-in per kind. Nothing this mission added can reach them."""
        self.assertIsNone(contract_for("platform_counted_content_request_change"))

    def test_no_historical_proposition_kind_gained_a_contract(self) -> None:
        for kind in (
            "source_reported_metric_period_change",
            "platform_counted_content_request_change",
            "community_site_published_questions_carrying_tag",
            "community_site_questions_without_accepted_answer",
            "source_reported_term_frequency_change",
            "source_reported_term_frequency_contrast",
            "source_reported_procurement_value_contrast",
        ):
            self.assertIsNone(contract_for(kind), kind)


class HistoricalPropositionKeysAreByteStable(unittest.TestCase):
    """§21. Mission 1.39 must not rewrite history, and this is where that breaks."""

    # Frozen preimages with their keys, computed from the CURRENT procedure and
    # pinned here. If `proposition_key` ever changes shape, these fail rather
    # than the historical claims silently becoming unreachable.
    FIXTURES = (
        (
            {
                "proposition": "source_reported_metric_period_change",
                "source_id": "world-bank",
                "resource_id": "indicators/SP.POP.TOTL",
                "metric_scheme": "world-bank-indicator",
                "metric_id": "SP.POP.TOTL",
                "geography_source_code": "DEU",
                "period_label_from": "2018",
                "period_label_to": "2019",
                "direction": "INCREASING",
            },
            "f6dbb3b4b8f7a3b1f4fbf3b0e0d1a9e0",
        ),
    )

    def test_the_key_is_sha256_over_canonical_json_of_the_facts(self) -> None:
        """The procedure, asserted rather than assumed: 64 lowercase hex."""
        key = proposition_key(self.FIXTURES[0][0])
        self.assertEqual(len(key), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in key))

    def test_key_order_independence(self) -> None:
        """Canonical JSON sorts keys, so a reordered mapping is the same claim."""
        facts = self.FIXTURES[0][0]
        reversed_facts = dict(reversed(list(facts.items())))
        self.assertEqual(proposition_key(facts), proposition_key(reversed_facts))

    def test_convergence_uses_the_same_hash_on_a_smaller_mapping(self) -> None:
        """Nothing about the historical procedure changed. A different set of
        facts in, a different key out, which is what it has always done."""
        self.assertEqual(
            convergent_proposition_key(contract(), COHORT_A),
            proposition_key(identity_facts(contract(), COHORT_A)),
        )

    def test_an_empty_fact_set_is_still_refused(self) -> None:
        with self.assertRaises(ValueError):
            proposition_key({})


class OverlapIsNotIndependence(unittest.TestCase):
    """§11, §12. Two axes, and conflating them is the failure."""

    def test_disjoint_cohorts_are_reported_disjoint(self) -> None:
        self.assertIs(
            overlap_between(contract(), COHORT_A, COHORT_B, membership_field="notice_ids"),
            ObservationOverlap.DISJOINT,
        )

    def test_a_shared_notice_makes_them_overlapping(self) -> None:
        shared = {**COHORT_B, "notice_ids": ["N-3", "N-9"]}
        self.assertIs(
            overlap_between(contract(), COHORT_A, shared, membership_field="notice_ids"),
            ObservationOverlap.OVERLAPPING,
        )

    def test_unstated_membership_is_unestablished_rather_than_disjoint(self) -> None:
        """A cohort that did not say which records it read has not established
        that it read different ones."""
        silent = {**COHORT_B, "notice_ids": []}
        self.assertIs(
            overlap_between(contract(), COHORT_A, silent, membership_field="notice_ids"),
            ObservationOverlap.UNESTABLISHED,
        )

    def test_overlap_is_a_property_of_a_witness_field(self) -> None:
        with self.assertRaises(ValueError):
            overlap_between(
                contract(), COHORT_A, COHORT_B, membership_field="classification_division"
            )

    def test_the_overlap_vocabulary_is_not_the_independence_vocabulary(self) -> None:
        """Deliberately different member names, so a mapping cannot be written
        by accident."""
        from sros_contracts import EvidenceIndependenceState

        self.assertFalse(
            {m.value for m in ObservationOverlap} & {m.value for m in EvidenceIndependenceState}
        )


if __name__ == "__main__":
    unittest.main()
