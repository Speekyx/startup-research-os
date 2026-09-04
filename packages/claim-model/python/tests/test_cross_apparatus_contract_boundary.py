"""Mission 1.47 §18. The contract cannot express a cross-apparatus proposition.

This is gate 7 of §26, proved through the REAL constructor rather than asserted
in a document. It lives in `claim-model` because that is the package that OWNS
`PropositionConvergenceContract`: the rest of Mission 1.47's suite sits in
`evidence-aggregation`, and reaching across for this proof there imports a
package the zero-dependency runner does not put on that suite's path.

Two refusals, and they are independent of each other. Either one alone stops a
cross-apparatus contract, which is why both are asserted separately: a later
change that relaxed one would still be caught by the other.

`unittest`, no third-party dependency, so this runs in the zero-dependency CI
job (ADR-009).
"""

from __future__ import annotations

import unittest

from sros_claim_model import PropositionConvergenceContract, SourceBoundary
from sros_contracts import ClaimTemporality, ClaimType


def cross_apparatus_contract(**overrides):
    """The contract Mission 1.47 would have needed, built as faithfully as the
    dataclass allows. `source_id` sits in WITNESS, which is the whole point: two
    publishers cannot share one proposition key while it is identity."""
    fields = {
        "contract_id": "cross-apparatus-public-platform-activity",
        "version": "1.0.0",
        "proposition_kind": "public_platform_activity_witnessed",
        "claim_type": ClaimType.OBSERVED,
        "temporality": ClaimTemporality.EVERGREEN,
        "source_boundary": SourceBoundary.SAME_SOURCE_AND_RESOURCE,
        "identity_fields": ("proposition", "canonical_subject_id", "period_bound"),
        "witness_fields": ("source_id", "resource_id", "period_label_from"),
        "qualifying_signal_types": ("content_request_change", "community_question_volume"),
        "establishes": "at least one platform recorded a qualifying event for the subject",
        "does_not_establish": ("prevalence", "attention", "a shared problem"),
    }
    fields.update(overrides)
    return PropositionConvergenceContract(**fields)


class TheContractRefusesACrossApparatusProposition(unittest.TestCase):
    def test_source_id_may_not_be_demoted_to_a_witness_fact(self):
        with self.assertRaises(ValueError) as raised:
            cross_apparatus_contract()
        self.assertIn("source_id", str(raised.exception))

    def test_the_refusal_says_attribution_is_part_of_the_proposition(self):
        """The reason matters as much as the refusal: this is not an arbitrary
        required field, it is Mission 1.38's finding that for an OBSERVED claim
        the attribution IS the claim."""
        with self.assertRaises(ValueError) as raised:
            cross_apparatus_contract()
        self.assertIn("Attribution is part of the proposition", str(raised.exception))

    def test_the_same_contract_is_accepted_once_source_id_is_identity(self):
        """The refusal is specific to demoting `source_id`, not to the shape of
        the contract. Without this the test above could be passing for an
        unrelated reason and nobody would know."""
        contract = cross_apparatus_contract(
            identity_fields=("proposition", "source_id", "canonical_subject_id", "period_bound"),
            witness_fields=("resource_id", "period_label_from"),
        )
        self.assertIn("source_id", contract.identity_fields)

    def test_but_that_accepted_contract_is_single_source_and_converges_nothing(self):
        """And so it is not the contract Mission 1.47 needed. With `source_id`
        back in identity, two publishers produce two proposition keys, which is
        two Claims rather than one Claim with two support groups."""
        contract = cross_apparatus_contract(
            identity_fields=("proposition", "source_id", "canonical_subject_id", "period_bound"),
            witness_fields=("resource_id", "period_label_from"),
        )
        self.assertIs(contract.source_boundary, SourceBoundary.SAME_SOURCE_AND_RESOURCE)

    def test_the_source_boundary_enum_has_no_cross_source_member(self):
        """The second, independent refusal. There is no value a caller could
        pass to widen the boundary, so this is structural rather than a policy
        check somebody could relax with a flag."""
        self.assertEqual({member.value for member in SourceBoundary}, {"SAME_SOURCE_AND_RESOURCE"})

    def test_the_absence_of_a_cross_source_member_is_documented_as_deliberate(self):
        """An enum that merely happens to have one member today would be widened
        by the next person who needed two. The docstring records that the
        absence is a decision."""
        self.assertIn("deliberately absent", SourceBoundary.__doc__)


if __name__ == "__main__":
    unittest.main()
