"""Mission 1.81. A finer classification level is identity when present, and absent otherwise.

A detailed procurement claim keyed at the division carries no level facts and keeps the
proposition key it has always had. One keyed at a CPV group carries the level and its
code, and gets a key of its own -- so a group cohort never witnesses the division's
proposition, and the division's witnessed claim is not widened by a narrower cohort.
"""

from __future__ import annotations

import unittest

from sros_claim_model.convergence import (
    CONVERGENCE_CONTRACTS,
    QualificationOutcome,
    convergent_proposition_key,
    identity_facts,
    qualify,
    witness_facts,
)

KIND = "source_published_classification_value_contrast_witnessed"

DIVISION_FACTS = {
    "proposition": KIND,
    "source_id": "ted-eu",
    "resource_id": "notices/eforms-contract-and-award",
    "notice_class": "CONTRACT_NOTICE",
    "amount_type": "TOTAL_VALUE",
    "amount_scope": "NOTICE",
    "currency": "EUR",
    "classification_scheme": "CPV",
    "classification_division": "92",
    "relation": "DIFFERS",
    "notice_ids": ["1-2023", "2-2023"],
    "classification_codes": ["92500000", "92610000"],
}
GROUP_FACTS = {
    **DIVISION_FACTS,
    "classification_level": "group",
    "classification_level_code": "925",
    "notice_ids": ["3-2023", "4-2023"],
    "classification_codes": ["92512000", "92521000"],
}


def contract():
    return CONVERGENCE_CONTRACTS[KIND]


class ConditionalIdentity(unittest.TestCase):
    def test_the_procurement_contract_declares_the_level_as_conditional(self) -> None:
        self.assertEqual(
            contract().conditional_identity_fields,
            ("classification_level", "classification_level_code"),
        )
        self.assertNotIn("classification_level", contract().identity_fields)
        self.assertNotIn("classification_level", contract().witness_fields)

    def test_a_division_claim_still_qualifies_without_the_level(self) -> None:
        outcome, _ = qualify(
            contract(), DIVISION_FACTS, signal_type_id="procurement_value_contrast"
        )
        self.assertIs(outcome, QualificationOutcome.QUALIFIES)

    def test_a_group_claim_qualifies_with_the_level(self) -> None:
        outcome, _ = qualify(contract(), GROUP_FACTS, signal_type_id="procurement_value_contrast")
        self.assertIs(outcome, QualificationOutcome.QUALIFIES)

    def test_the_level_is_identity_when_present(self) -> None:
        identity = identity_facts(contract(), GROUP_FACTS)
        self.assertEqual(identity["classification_level"], "group")
        self.assertEqual(identity["classification_level_code"], "925")
        self.assertNotIn("classification_level", identity_facts(contract(), DIVISION_FACTS))

    def test_a_group_cohort_does_not_witness_the_division_proposition(self) -> None:
        self.assertNotEqual(
            convergent_proposition_key(contract(), GROUP_FACTS),
            convergent_proposition_key(contract(), DIVISION_FACTS),
        )

    def test_two_group_cohorts_of_one_group_converge(self) -> None:
        other = {
            **GROUP_FACTS,
            "notice_ids": ["9-2023", "8-2023"],
            "classification_codes": ["92511000", "92521100"],
        }
        self.assertEqual(
            convergent_proposition_key(contract(), GROUP_FACTS),
            convergent_proposition_key(contract(), other),
        )
        self.assertNotEqual(
            witness_facts(contract(), GROUP_FACTS), witness_facts(contract(), other)
        )

    def test_two_different_groups_do_not_converge(self) -> None:
        other = {**GROUP_FACTS, "classification_level_code": "926"}
        self.assertNotEqual(
            convergent_proposition_key(contract(), GROUP_FACTS),
            convergent_proposition_key(contract(), other),
        )

    def test_the_division_key_is_what_it_was_before_the_field_existed(self) -> None:
        """The conditional fields add nothing to a mapping that lacks them, so a 1.0.0 key
        recomputes byte-identically under 1.1.0."""
        legacy = {name: DIVISION_FACTS[name] for name in contract().identity_fields}
        self.assertEqual(identity_facts(contract(), DIVISION_FACTS), legacy)

    def test_the_content_request_contract_declares_none(self) -> None:
        self.assertEqual(
            CONVERGENCE_CONTRACTS[
                "platform_counted_content_request_change_witnessed"
            ].conditional_identity_fields,
            (),
        )


if __name__ == "__main__":
    unittest.main()
