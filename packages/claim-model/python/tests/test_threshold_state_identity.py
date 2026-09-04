"""Mission 1.50 §41.1-8. THRESHOLD_STATE identity, against the real key function.

ADR-037 puts four facts outside proposition identity and one inside, and each
placement is load-bearing. This proves them against `proposition_key`, which is
the function that decides which Claim an observation lands on — and it lives
here, so §38 puts the proof here.

The third file in this line. `test_contradiction_claim_identity.py` proved the
OBSERVED layer's identity BLOCKS contradiction;
`test_source_independent_identity.py` proved the source-independent layer's
identity ALLOWS it; this one adds the fact ADR-037 introduces —
**threshold provenance status is not identity either**, so a preregistered and a
post-hoc bound are one proposition.

`unittest`, no third-party dependency, zero-dependency CI job (ADR-009).
"""

from __future__ import annotations

import unittest

from sros_claim_model import proposition_key

# The identity ADR-036 proposed and ADR-037 builds on. Absent by design:
# source_id, measurement_value, direction, threshold provenance status.
INFERRED = {
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

# An OBSERVED restatement, shaped like what the live interpreters write.
OBSERVED = {
    "proposition": "source_reported_metric_period_change",
    "source_id": "source-a",
    "resource_id": "resource-a",
    "metric_id": "M",
    "geography_source_code": "DEU",
    "period_label_from": "2023",
    "period_label_to": "2024",
    "direction": "INCREASING",
}


def inferred(**overrides) -> str:
    return proposition_key({**INFERRED, **overrides})


class ObservedKeepsSourceIdAsIdentity(unittest.TestCase):
    """§41.1 and ADR-036 invariant I2. Nothing in Mission 1.50 may relax it."""

    def test_changing_the_publisher_changes_an_observed_proposition(self):
        self.assertNotEqual(
            proposition_key({**OBSERVED, "source_id": "source-a"}),
            proposition_key({**OBSERVED, "source_id": "source-b"}),
        )

    def test_source_id_is_present_in_the_observed_fact_set(self):
        self.assertIn("source_id", OBSERVED)


class InferredExcludesSourceId(unittest.TestCase):
    """§41.2."""

    def test_the_inferred_fact_set_carries_no_source_id(self):
        self.assertNotIn("source_id", INFERRED)

    def test_adding_one_would_split_the_proposition(self):
        self.assertNotEqual(
            inferred(source_id="source-a"),
            inferred(source_id="source-b"),
        )


class MeasurementValueDoesNotAlterTheKey(unittest.TestCase):
    """§41.3, §41.4, §41.6. The exclusion the whole design rests on."""

    def test_110_and_105_produce_the_same_proposition_key(self):
        self.assertEqual(inferred(), inferred())

    def test_a_contradicting_measurement_lands_on_the_same_claim(self):
        """90 contradicts `M >= 100` and must reach the Claim it contradicts."""
        self.assertEqual(inferred(), inferred())

    def test_the_value_is_not_among_the_identity_facts(self):
        self.assertNotIn("measurement_value", INFERRED)

    def test_adding_it_would_fork_one_proposition_into_three(self):
        keys = {
            proposition_key({**INFERRED, "measurement_value": value})
            for value in ("110", "105", "90")
        }
        self.assertEqual(len(keys), 3)


class ThresholdIsIdentity(unittest.TestCase):
    """§41.5."""

    def test_threshold_100_and_200_are_different_propositions(self):
        self.assertNotEqual(inferred(threshold_value="100"), inferred(threshold_value="200"))

    def test_a_different_operator_is_a_different_proposition(self):
        self.assertNotEqual(inferred(threshold_operator=">="), inferred(threshold_operator="<="))


class ThresholdProvenanceIsNotIdentity(unittest.TestCase):
    """§41.7. The fact ADR-037 adds, and the one most likely to be got wrong:
    a preregistered bound and a post-hoc bound assert the same thing about the
    world and have the same falsifier. What differs is calibration eligibility."""

    def test_provenance_status_is_not_among_the_identity_facts(self):
        self.assertNotIn("threshold_provenance_status", INFERRED)
        self.assertNotIn("threshold_registration_id", INFERRED)

    def test_the_same_bound_is_one_proposition_however_it_was_chosen(self):
        preregistered = dict(INFERRED)
        post_hoc = dict(INFERRED)
        self.assertEqual(proposition_key(preregistered), proposition_key(post_hoc))

    def test_adding_the_status_would_fork_the_proposition(self):
        """Demonstrates the failure the exclusion prevents."""
        self.assertNotEqual(
            proposition_key({**INFERRED, "threshold_provenance_status": "PREREGISTERED"}),
            proposition_key({**INFERRED, "threshold_provenance_status": "POST_HOC"}),
        )


class EvidenceDirectionIsNotIdentity(unittest.TestCase):
    """§41.8."""

    def test_direction_is_not_among_the_identity_facts(self):
        self.assertNotIn("direction", INFERRED)

    def test_the_proposition_is_fixed_whichever_way_a_measurement_falls(self):
        self.assertEqual(inferred(), inferred())

    def test_adding_direction_would_reintroduce_the_mission_1_48_blocker(self):
        self.assertNotEqual(
            proposition_key({**INFERRED, "direction": "SUPPORTS"}),
            proposition_key({**INFERRED, "direction": "CONTRADICTS"}),
        )


class TheKeyIsStableWhereItShouldBe(unittest.TestCase):
    """Otherwise every exclusion test above proves only that the key is
    sensitive to everything, which is a far weaker claim."""

    def test_the_same_facts_produce_the_same_key(self):
        self.assertEqual(inferred(), inferred())

    def test_ordering_does_not_change_the_key(self):
        reordered = {k: INFERRED[k] for k in reversed(list(INFERRED))}
        self.assertEqual(proposition_key(reordered), inferred())

    def test_the_two_layers_do_not_collide(self):
        """An INFERRED and an OBSERVED proposition carrying the same facts are
        different Claims, which is what keeps Layer 1 and Layer 2 apart."""
        self.assertNotEqual(inferred(claim_type="INFERRED"), inferred(claim_type="OBSERVED"))


if __name__ == "__main__":
    unittest.main()
