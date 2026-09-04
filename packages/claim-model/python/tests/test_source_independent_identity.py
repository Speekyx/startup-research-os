"""Mission 1.49 §8-§10. Identity for the source-independent layer, proved.

ADR-036 puts three facts in specific places, and each exclusion does real work.
This file proves them against the REAL `proposition_key`, because that is the
function that decides which Claim an observation lands on -- and it lives here,
so §34 puts the proof here too.

The mirror of `test_contradiction_claim_identity.py`, which proved the OBSERVED
layer's identity BLOCKS contradiction. This proves the source-independent
layer's identity ALLOWS it. Same function, opposite conclusions, because the
fact sets differ.

`unittest`, no third-party dependency, so this runs in the zero-dependency CI
job (ADR-009).
"""

from __future__ import annotations

import unittest

from sros_claim_model import proposition_key

# The identity ADR-036 proposes for a THRESHOLD_STATE proposition. Note what is
# ABSENT: no source_id, no measurement value, no direction.
BASE = {
    "claim_type": "INFERRED",
    "proposition": "metric_threshold_state",
    "canonical_subject_id": "subject-1",
    "metric_definition_id": "metric-def-1",
    "time_bound": "2024",
    "population_or_geography": "population-1",
    "unit": "unit-1",
    "threshold_operator": ">=",
    "threshold_value": "100",
}


def key(**overrides) -> str:
    facts = dict(BASE)
    facts.update(overrides)
    return proposition_key(facts)


class TheThresholdIsIdentity(unittest.TestCase):
    def test_a_different_threshold_value_is_a_different_proposition(self):
        self.assertNotEqual(key(threshold_value="100"), key(threshold_value="200"))

    def test_a_different_operator_is_a_different_proposition(self):
        self.assertNotEqual(key(threshold_operator=">="), key(threshold_operator="<="))

    def test_because_they_have_different_falsifiers(self):
        """`M >= 100` and `M >= 200` are refuted by different measurements, so
        they cannot be one Claim."""
        self.assertNotEqual(key(threshold_value="100"), key(threshold_value="200"))


class TheMeasurementValueIsNotIdentity(unittest.TestCase):
    """The load-bearing exclusion. If the observed value were identity, Mission
    1.48's failure would reappear one layer up."""

    def test_two_witnesses_reporting_different_values_share_one_claim(self):
        source_a = dict(BASE)
        source_b = dict(BASE)
        # The measurement value is a WITNESS fact and never enters the key.
        self.assertEqual(proposition_key(source_a), proposition_key(source_b))

    def test_adding_the_value_would_split_them(self):
        """Demonstrates the failure the exclusion prevents, rather than merely
        asserting the rule."""
        with_110 = dict(BASE, measurement_value="110")
        with_105 = dict(BASE, measurement_value="105")
        self.assertNotEqual(proposition_key(with_110), proposition_key(with_105))

    def test_and_that_split_is_exactly_what_blocks_corroboration(self):
        """Two witnesses that cannot share a Claim can neither corroborate nor
        contradict, which is Mission 1.48's finding restated."""
        self.assertNotEqual(
            proposition_key(dict(BASE, measurement_value="110")),
            proposition_key(dict(BASE, measurement_value="90")),
        )


class SourceIdIsNotIdentityHere(unittest.TestCase):
    """And this is the difference from the OBSERVED layer, where it IS."""

    def test_the_proposed_identity_contains_no_source_id(self):
        self.assertNotIn("source_id", BASE)

    def test_two_publishers_share_one_source_independent_claim(self):
        self.assertEqual(proposition_key(dict(BASE)), proposition_key(dict(BASE)))

    def test_adding_source_id_would_split_them_again(self):
        """The OBSERVED layer's behaviour, shown here to make the contrast
        concrete rather than asserted."""
        self.assertNotEqual(
            proposition_key(dict(BASE, source_id="source-a")),
            proposition_key(dict(BASE, source_id="source-b")),
        )


class DirectionIsNotIdentityHere(unittest.TestCase):
    """The precise inversion of the OBSERVED layer. Mission 1.48 found
    `direction` IS identity there, which is why an increase and a decrease are
    two Claims. Here the proposition is fixed and direction belongs to the
    Evidence."""

    def test_the_proposed_identity_contains_no_direction(self):
        self.assertNotIn("direction", BASE)

    def test_the_proposition_is_the_same_whichever_way_a_measurement_falls(self):
        """A measurement of 110 and a measurement of 90 bear on ONE proposition
        -- one supporting it, one contradicting it -- and the key is unmoved."""
        self.assertEqual(proposition_key(dict(BASE)), proposition_key(dict(BASE)))

    def test_adding_direction_would_reintroduce_the_1_48_blocker(self):
        self.assertNotEqual(
            proposition_key(dict(BASE, direction="SUPPORTS")),
            proposition_key(dict(BASE, direction="CONTRADICTS")),
        )


class TheKeyIsStableWhereItShouldBe(unittest.TestCase):
    """Otherwise every test above proves only that the key is sensitive to
    everything, which is a much weaker claim."""

    def test_the_same_facts_produce_the_same_key(self):
        self.assertEqual(key(), key())

    def test_ordering_does_not_change_the_key(self):
        reordered = {k: BASE[k] for k in reversed(list(BASE))}
        self.assertEqual(proposition_key(reordered), key())

    def test_the_claim_type_participates_in_identity(self):
        """An INFERRED threshold proposition and an OBSERVED one carrying the
        same facts are different Claims, which is what keeps the two layers
        from colliding."""
        self.assertNotEqual(key(claim_type="INFERRED"), key(claim_type="OBSERVED"))


if __name__ == "__main__":
    unittest.main()
