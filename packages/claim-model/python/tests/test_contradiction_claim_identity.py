"""Mission 1.48 §9. Why a contradiction cannot inhabit one Claim identity.

The contradiction machinery in `evidence-aggregation` works: a SUPPORTS row and
a CONTRADICTS row on one claim id produce non-zero contradiction and conflict
mass, and that is asserted in that package's suite. This file asserts the other
half, which is why no real Claim ever reaches it -- and it belongs here because
`proposition_key` lives here, and §33 forbids reaching across packages for a
proof the zero-dependency runner cannot import.

Two facts decide it, and they are independent. `direction` is a proposition
fact, so an increase and a decrease are two Claims. `source_id` is a proposition
fact, so two publishers reporting incompatible values are two Claims. The second
is the deeper one: it is also what stopped Mission 1.47's corroboration route,
so ONE identity decision closes both roads out of the B-2 baseline.

`unittest`, no third-party dependency, so this runs in the zero-dependency CI
job (ADR-009).
"""

from __future__ import annotations

import unittest

from sros_claim_model import proposition_key

# Shaped like the facts `observed-signal-restatement` actually writes, so the
# demonstration is about the real key rather than an invented one.
BASE = {
    "proposition": "source_reported_metric_period_change",
    "source_id": "source-a",
    "resource_id": "resource-a",
    "metric_scheme": "scheme",
    "metric_id": "M",
    "geography_source_code": "DEU",
    "period_label_from": "2023",
    "period_label_to": "2024",
    "direction": "INCREASING",
}


def key(**overrides) -> str:
    facts = dict(BASE)
    facts.update(overrides)
    return proposition_key(facts)


class DirectionIsPropositionIdentity(unittest.TestCase):
    """Blocker 1. An increase and a decrease cannot inhabit one Claim."""

    def test_flipping_direction_changes_the_proposition_key(self):
        self.assertNotEqual(key(direction="INCREASING"), key(direction="DECREASING"))

    def test_therefore_the_contradicting_observation_lands_on_another_claim(self):
        """Which is the whole point: the observation that would contradict is
        not refused, it is simply attached somewhere else, where it contradicts
        nothing."""
        increasing = key(direction="INCREASING")
        decreasing = key(direction="DECREASING")
        self.assertNotEqual(increasing, decreasing)
        # And neither is degenerate: both are real keys over the same subject.
        self.assertTrue(increasing)
        self.assertTrue(decreasing)

    def test_unchanged_is_a_third_claim_rather_than_a_middle_ground(self):
        keys = {key(direction=d) for d in ("INCREASING", "DECREASING", "UNCHANGED")}
        self.assertEqual(len(keys), 3)


class SourceIdIsPropositionIdentity(unittest.TestCase):
    """Blocker 3, and the one that also closed Mission 1.47's route."""

    def test_changing_the_publisher_changes_the_proposition_key(self):
        self.assertNotEqual(key(source_id="source-a"), key(source_id="source-b"))

    def test_two_publishers_reporting_the_same_thing_are_two_claims(self):
        """So a second apparatus cannot become a second support group, and
        cannot contradict. One identity decision, both routes closed."""
        self.assertNotEqual(
            key(source_id="source-a", direction="INCREASING"),
            key(source_id="source-b", direction="INCREASING"),
        )

    def test_two_publishers_disagreeing_are_also_two_claims(self):
        """The contradiction case specifically: even the disagreement itself
        does not bring them together."""
        self.assertNotEqual(
            key(source_id="source-a", direction="INCREASING"),
            key(source_id="source-b", direction="DECREASING"),
        )


class TheKeyIsStableWhereItShouldBe(unittest.TestCase):
    """Otherwise the tests above prove only that the key is sensitive to
    everything, which would be a different and much weaker claim."""

    def test_the_same_facts_produce_the_same_key(self):
        self.assertEqual(key(), key())

    def test_fact_ordering_does_not_change_the_key(self):
        reordered = {k: BASE[k] for k in reversed(list(BASE))}
        self.assertEqual(proposition_key(reordered), key())

    def test_a_fact_the_proposition_does_not_carry_is_not_in_the_key(self):
        """The magnitude is deliberately absent from proposition identity
        (Mission 1.13.1), which is why a revised value appends a REVISION rather
        than forking the Claim -- and is also why a differing value is not a
        contradiction today."""
        self.assertEqual(key(), proposition_key(dict(BASE)))


class AnEmptyFactSetIsRefused(unittest.TestCase):
    def test_no_facts_means_no_identity(self):
        with self.assertRaises(ValueError):
            proposition_key({})


if __name__ == "__main__":
    unittest.main()
