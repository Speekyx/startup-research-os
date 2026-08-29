"""Evidence Aggregation V1 — the properties, not the numbers.

Mission 1.1 §30, §46. These tests assert the twelve invariants the specification
commits to, plus the guards that keep the framework from quietly becoming
production scoring.

`unittest`, no third-party dependency, so this runs in the zero-dependency CI
job (ADR-009). Property-style cases are written as deterministic parameterised
sweeps rather than pulling in a generator library: the properties here are
algebraic, the interesting boundaries are known (0, 1, near-0, near-1, many
groups), and a dependency would buy shrinking we do not need.
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from sros_contracts import (
    AggregationProfileStatus,
    ClaimTemporality,
    EvidenceAggregationStatus,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
)
from sros_evidence_aggregation import (
    REFERENCE_PROFILE_V1,
    EvidenceAggregationProfile,
    EvidenceItem,
    GroupKind,
    InvalidFactorError,
    LevelThresholds,
    UncalibratedProfileError,
    aggregate,
    decompose,
    evidence_score,
    half_life_decay,
    saturate,
)
from sros_evidence_aggregation.errors import InvalidEvidenceItemError, ProfileError
from sros_evidence_aggregation.items import evaluate_item
from sros_evidence_aggregation.recency import (
    MISSING_OBSERVATION_TIME,
    MISSING_TEMPORAL_PARAMETER,
    freshness,
)

NOW = datetime(2026, 8, 29, 12, 0, 0, tzinfo=UTC)

D = EvidenceDirection
IND = EvidenceIndependenceState
C = EvidenceObservationCategory


def item(
    evidence_id: str,
    *,
    q: float | None = 0.5,
    direction: EvidenceDirection = D.SUPPORTS,
    state: EvidenceIndependenceState = IND.KNOWN_INDEPENDENT,
    group: str | None = None,
    category: EvidenceObservationCategory = C.STATED_OPINION,
    family: str | None = "family-a",
    reliability: float | None = -1.0,
    observed_at: datetime | None = None,
) -> EvidenceItem:
    """A record whose five components are all `q` unless overridden."""
    return EvidenceItem(
        evidence_id=evidence_id,
        direction=direction,
        relevance=q,
        directness=q,
        reliability=q if reliability == -1.0 else reliability,
        extraction_confidence=q,
        independence_state=state,
        independence_group_id=group,
        observation_category=category,
        source_id=f"src-{evidence_id}",
        source_family=family,
        observed_at=observed_at,
    )


def run(items, profile=REFERENCE_PROFILE_V1, **kwargs):
    kwargs.setdefault("temporality", ClaimTemporality.EVERGREEN)
    kwargs.setdefault("now", NOW)
    kwargs.setdefault("allow_uncalibrated", True)
    return aggregate("claim-under-test", list(items), profile, **kwargs)


# ============================================================ item contribution


class TestItemContribution(unittest.TestCase):
    def test_q_is_the_minimum_component_not_an_average(self) -> None:
        """A relevant record from an unreliable source stays unreliable. An
        average would score it middling and let the strength pay for the
        weakness, which is the case §8 exists to prevent."""
        contribution = evaluate_item(
            EvidenceItem(
                "e1",
                D.SUPPORTS,
                relevance=1.0,
                directness=1.0,
                reliability=0.1,
                extraction_confidence=1.0,
            ),
            temporality=ClaimTemporality.EVERGREEN,
            now=NOW,
            half_life_days=None,
        )
        self.assertEqual(contribution.q, 0.1)
        self.assertEqual(contribution.limiting_component, "reliability")
        # The mean would have been 0.82. Asserted so the intent is unmistakable.
        self.assertNotAlmostEqual(contribution.q or 0.0, 0.82, places=2)

    def test_a_strong_source_on_an_irrelevant_topic_stays_weak(self) -> None:
        contribution = evaluate_item(
            EvidenceItem(
                "e1",
                D.SUPPORTS,
                relevance=0.05,
                directness=0.9,
                reliability=0.95,
                extraction_confidence=0.9,
            ),
            temporality=ClaimTemporality.EVERGREEN,
            now=NOW,
            half_life_days=None,
        )
        self.assertEqual(contribution.q, 0.05)
        self.assertEqual(contribution.limiting_component, "relevance")

    def test_a_factor_outside_the_unit_interval_is_rejected_not_clamped(self) -> None:
        """1.4 means the producer is on a different scale. Clamping to 1.0 would
        hide that and return a plausible number."""
        for bad in (1.4, -0.1, float("nan")):
            with self.assertRaises(InvalidFactorError):
                EvidenceItem("e1", D.SUPPORTS, relevance=bad)

    def test_a_missing_component_makes_the_item_non_scorable(self) -> None:
        contribution = evaluate_item(
            EvidenceItem(
                "e1",
                D.SUPPORTS,
                relevance=0.9,
                directness=0.9,
                reliability=None,
                extraction_confidence=0.9,
            ),
            temporality=ClaimTemporality.EVERGREEN,
            now=NOW,
            half_life_days=None,
        )
        self.assertFalse(contribution.scorable)
        self.assertIsNone(contribution.q)
        self.assertIn("MISSING_RELIABILITY", [str(r) for r in contribution.non_scorable_reasons])

    def test_a_missing_component_is_never_given_a_default(self) -> None:
        """§9. Not 0.5, not 1.0, not 0.0. A zero would enter the mathematics as
        a measured weakness; this is an absence of measurement."""
        result = run([item("has-all", q=0.6), item("missing", q=0.6, reliability=None)])
        self.assertEqual(result.scorable_evidence_count, 1)
        self.assertEqual(result.status, EvidenceAggregationStatus.PARTIAL)
        self.assertAlmostEqual(result.masses.support_strength, 0.6)
        self.assertTrue(any("MISSING_RELIABILITY" in m for m in result.missing_requirements))

    def test_a_self_contradictory_record_is_refused(self) -> None:
        with self.assertRaises(InvalidEvidenceItemError):
            EvidenceItem("e1", D.SUPPORTS, independence_state=IND.KNOWN_DEPENDENT)
        with self.assertRaises(InvalidEvidenceItemError):
            EvidenceItem(
                "e1",
                D.SUPPORTS,
                independence_state=IND.KNOWN_INDEPENDENT,
                independence_group_id="g1",
            )


# ==================================================================== independence


class TestIndependence(unittest.TestCase):
    def test_duplicates_inside_a_group_do_not_increase_strength(self) -> None:
        """§30.6. The invariant the whole independence model exists for."""
        one = run([item("original", q=0.8, state=IND.KNOWN_DEPENDENT, group="g1")])
        ten = run(
            [item(f"copy-{i}", q=0.8, state=IND.KNOWN_DEPENDENT, group="g1") for i in range(10)]
        )
        self.assertAlmostEqual(one.masses.support_strength, ten.masses.support_strength)
        self.assertEqual(one.support_group_count, ten.support_group_count)

    def test_the_strongest_group_member_represents_it(self) -> None:
        result = run(
            [
                item("weak-copy", q=0.3, state=IND.KNOWN_DEPENDENT, group="g1"),
                item("original", q=0.9, state=IND.KNOWN_DEPENDENT, group="g1"),
            ]
        )
        group = result.groups.support[0]
        self.assertAlmostEqual(group.strength, 0.9)
        self.assertEqual(group.representative_evidence_id, "original")
        self.assertEqual(group.collapsed_member_count, 1)

    def test_a_weak_duplicate_never_drags_a_strong_original_down(self) -> None:
        """A mean would. A duplicate is not counter-evidence."""
        alone = run([item("original", q=0.9, state=IND.KNOWN_DEPENDENT, group="g1")])
        with_copy = run(
            [
                item("original", q=0.9, state=IND.KNOWN_DEPENDENT, group="g1"),
                item("copy", q=0.1, state=IND.KNOWN_DEPENDENT, group="g1"),
            ]
        )
        self.assertAlmostEqual(alone.masses.support_strength, with_copy.masses.support_strength)

    def test_separate_lineages_are_separate_groups(self) -> None:
        result = run(
            [
                item("a", q=0.5, state=IND.KNOWN_DEPENDENT, group="lineage-1"),
                item("b", q=0.5, state=IND.KNOWN_DEPENDENT, group="lineage-2"),
            ]
        )
        self.assertEqual(result.support_group_count, 2)
        self.assertAlmostEqual(result.masses.support_strength, 0.75)

    def test_explicitly_independent_records_accumulate(self) -> None:
        one = run([item("a", q=0.5)])
        two = run([item("a", q=0.5), item("b", q=0.5)])
        self.assertAlmostEqual(one.masses.support_strength, 0.5)
        self.assertAlmostEqual(two.masses.support_strength, 0.75)

    def test_unknown_provenance_forms_exactly_one_group(self) -> None:
        """§13, and §30.11. Unknown does not mean probably independent: the
        records most likely to share an origin are the ones that arrive in bulk."""
        result = run([item(f"u-{i}", q=0.5, state=IND.UNKNOWN) for i in range(10)])
        self.assertEqual(result.support_group_count, 1)
        self.assertEqual(result.groups.support[0].kind, GroupKind.UNKNOWN)
        self.assertAlmostEqual(result.masses.support_strength, 0.5)
        self.assertEqual(result.unknown_independence_count, 10)

    def test_unknown_records_still_raise_observed_volume(self) -> None:
        result = run([item(f"u-{i}", q=0.5, state=IND.UNKNOWN) for i in range(10)])
        self.assertEqual(result.raw_evidence_count, 10)
        self.assertEqual(result.scorable_evidence_count, 10)
        self.assertEqual(result.support_group_count, 1)
        self.assertTrue(any("provenance" in w for w in result.warnings))

    def test_unknown_and_known_groups_coexist(self) -> None:
        result = run(
            [item("known", q=0.5), *[item(f"u-{i}", q=0.5, state=IND.UNKNOWN) for i in range(5)]]
        )
        self.assertEqual(result.support_group_count, 2)


# ===================================================================== saturation


class TestSaturation(unittest.TestCase):
    def test_the_operator_stays_bounded(self) -> None:
        for count in (1, 2, 5, 50, 500):
            for g in (0.0, 1e-12, 0.5, 1 - 1e-12, 1.0):
                value = saturate([g] * count)
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)

    def test_an_empty_set_is_zero_strength(self) -> None:
        self.assertEqual(saturate([]), 0.0)

    def test_one_certain_group_saturates(self) -> None:
        self.assertEqual(saturate([1.0]), 1.0)
        self.assertEqual(saturate([1.0, 0.3]), 1.0)

    def test_accumulation_is_monotonic(self) -> None:
        """§30.4. Adding independent supporting evidence can never reduce support."""
        previous = 0.0
        strengths: list[float] = []
        for _ in range(30):
            strengths.append(0.3)
            current = saturate(strengths)
            self.assertGreaterEqual(current, previous)
            previous = current

    def test_marginal_gain_diminishes(self) -> None:
        gains = []
        for count in range(1, 12):
            gains.append(saturate([0.4] * count) - saturate([0.4] * (count - 1)))
        for earlier, later in zip(gains, gains[1:], strict=False):
            self.assertLess(later, earlier)

    def test_many_tiny_groups_stay_numerically_sane(self) -> None:
        """The naive `1 - prod(1-g)` cancels here. The log form does not."""
        value = saturate([1e-9] * 1000)
        self.assertGreater(value, 0.0)
        self.assertLess(value, 1e-5)

    def test_ordering_does_not_change_the_result(self) -> None:
        """§30.7. Floating-point addition is not associative, so this is
        engineered by sorting rather than assumed."""
        strengths = [0.11, 0.93, 0.4, 0.77, 0.02, 0.58]
        self.assertEqual(saturate(strengths), saturate(list(reversed(strengths))))
        self.assertEqual(saturate(strengths), saturate(sorted(strengths)))

    def test_an_out_of_range_strength_is_refused(self) -> None:
        with self.assertRaises(InvalidFactorError):
            saturate([0.5, 1.2])


# ============================================================= masses and score


class TestMasses(unittest.TestCase):
    GRID = (0.0, 1e-9, 0.01, 0.25, 0.5, 0.75, 0.99, 1 - 1e-9, 1.0)

    def test_the_four_masses_always_sum_to_one(self) -> None:
        for s in self.GRID:
            for c in self.GRID:
                masses = decompose(s, c)
                self.assertTrue(masses.sums_to_one(), (s, c))

    def test_every_mass_stays_on_the_unit_interval(self) -> None:
        for s in self.GRID:
            for c in self.GRID:
                masses = decompose(s, c)
                for name, value in masses.to_json().items():
                    self.assertGreaterEqual(value, 0.0, name)
                    self.assertLessEqual(value, 1.0, name)

    def test_the_score_stays_on_zero_to_one_hundred(self) -> None:
        for s in self.GRID:
            for c in self.GRID:
                score = evidence_score(decompose(s, c).supported_mass)
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 100.0)

    def test_no_evidence_and_contested_evidence_are_distinguishable(self) -> None:
        """The reason the decomposition exists. `s - c` nets both to zero; one
        needs more research and the other needs a human."""
        nothing = decompose(0.0, 0.0)
        contested = decompose(0.95, 0.95)
        self.assertAlmostEqual(nothing.uncertainty_mass, 1.0)
        self.assertAlmostEqual(nothing.conflict_mass, 0.0)
        self.assertGreater(contested.conflict_mass, 0.9)
        self.assertLess(contested.uncertainty_mass, 0.01)

    def test_stronger_contradiction_never_improves_the_score(self) -> None:
        """§30.5."""
        previous = evidence_score(decompose(0.8, 0.0).supported_mass)
        for c in (0.1, 0.3, 0.5, 0.7, 0.9, 1.0):
            current = evidence_score(decompose(0.8, c).supported_mass)
            self.assertLessEqual(current, previous)
            previous = current

    def test_more_contradiction_never_reduces_conflict(self) -> None:
        """§30.12."""
        previous = decompose(0.8, 0.0).conflict_mass
        for c in (0.1, 0.4, 0.6, 0.9):
            current = decompose(0.8, c).conflict_mass
            self.assertGreaterEqual(current, previous)
            previous = current


# ======================================================================== recency


class TestRecency(unittest.TestCase):
    def test_the_half_life_curve(self) -> None:
        self.assertAlmostEqual(half_life_decay(0, 30), 1.0)
        self.assertAlmostEqual(half_life_decay(30, 30), 0.5)
        self.assertAlmostEqual(half_life_decay(60, 30), 0.25)
        self.assertAlmostEqual(half_life_decay(90, 30), 0.125)

    def test_evergreen_evidence_does_not_decay(self) -> None:
        """§30.9."""
        value, missing = freshness(
            ClaimTemporality.EVERGREEN, NOW - timedelta(days=3650), NOW, None
        )
        self.assertEqual(value, 1.0)
        self.assertIsNone(missing)

    def test_an_older_observation_is_never_fresher_than_a_newer_one(self) -> None:
        """§30.8."""
        previous = 1.1
        for age in range(0, 400, 7):
            value, _ = freshness(
                ClaimTemporality.TEMPORALLY_SENSITIVE,
                NOW - timedelta(days=age),
                NOW,
                30.0,
            )
            assert value is not None
            self.assertLessEqual(value, previous)
            previous = value

    def test_clock_skew_never_produces_freshness_above_one(self) -> None:
        value, _ = freshness(
            ClaimTemporality.TEMPORALLY_SENSITIVE, NOW + timedelta(hours=2), NOW, 30.0
        )
        self.assertEqual(value, 1.0)

    def test_a_missing_half_life_fails_closed(self) -> None:
        """§19, §30.10. No universal half-life is invented; the evidence becomes
        non-scorable instead."""
        value, missing = freshness(ClaimTemporality.TEMPORALLY_SENSITIVE, NOW, NOW, None)
        self.assertIsNone(value)
        self.assertEqual(missing, MISSING_TEMPORAL_PARAMETER)

    def test_a_missing_observation_time_fails_closed(self) -> None:
        value, missing = freshness(ClaimTemporality.TEMPORALLY_SENSITIVE, None, NOW, 30.0)
        self.assertIsNone(value)
        self.assertEqual(missing, MISSING_OBSERVATION_TIME)

    def test_the_reference_profile_ships_no_half_life(self) -> None:
        """The mechanical form of §19. If this ever fails, somebody invented a
        decay parameter."""
        self.assertEqual(dict(REFERENCE_PROFILE_V1.half_life_days), {})

    def test_a_temporally_sensitive_claim_without_a_parameter_has_no_score(self) -> None:
        result = run(
            [item("a", q=0.9, observed_at=NOW)],
            temporality=ClaimTemporality.TEMPORALLY_SENSITIVE,
            claim_feature="unauthorised",
        )
        self.assertEqual(result.status, EvidenceAggregationStatus.UNAVAILABLE)
        self.assertIsNone(result.evidence_score)
        self.assertTrue(any(MISSING_TEMPORAL_PARAMETER in m for m in result.missing_requirements))

    def test_a_naive_timestamp_is_refused(self) -> None:
        with self.assertRaises(InvalidFactorError):
            freshness(
                ClaimTemporality.TEMPORALLY_SENSITIVE,
                datetime(2026, 8, 1),  # noqa: DTZ001 - the point of the test
                NOW,
                30.0,
            )


# ================================================================== contradiction


class TestContradiction(unittest.TestCase):
    def test_support_and_contradiction_are_aggregated_separately(self) -> None:
        result = run([item("s", q=0.8), item("c", q=0.6, direction=D.CONTRADICTS)])
        self.assertAlmostEqual(result.masses.support_strength, 0.8)
        self.assertAlmostEqual(result.masses.contradiction_strength, 0.6)
        self.assertEqual(result.support_group_count, 1)
        self.assertEqual(result.contradiction_group_count, 1)

    def test_strong_support_and_strong_contradiction_produce_conflict(self) -> None:
        result = run(
            [
                item("s1", q=0.9),
                item("s2", q=0.9, family="family-b"),
                item("c1", q=0.9, direction=D.CONTRADICTS),
                item("c2", q=0.9, direction=D.CONTRADICTS, family="family-b"),
            ]
        )
        self.assertGreater(result.masses.conflict_mass, 0.9)
        assert result.evidence_score is not None
        self.assertLess(result.evidence_score, 10.0)

    def test_adding_independent_contradiction_never_raises_the_score(self) -> None:
        """§30.5, end to end rather than on the masses alone."""
        base = [item("s1", q=0.8), item("s2", q=0.8, family="family-b")]
        previous = run(base).evidence_score
        assert previous is not None
        for i in range(5):
            base.append(item(f"c{i}", q=0.5, direction=D.CONTRADICTS))
            current = run(base).evidence_score
            assert current is not None
            self.assertLessEqual(current, previous)
            previous = current

    def test_contradiction_is_not_a_flat_penalty(self) -> None:
        """§17. A weak contradiction moves the score a little, a strong one a
        lot. A fixed `-20` would treat them identically."""
        weak = run([item("s", q=0.8), item("c", q=0.1, direction=D.CONTRADICTS)])
        strong = run([item("s", q=0.8), item("c", q=0.9, direction=D.CONTRADICTS)])
        assert weak.evidence_score is not None and strong.evidence_score is not None
        self.assertGreater(weak.evidence_score, strong.evidence_score)
        self.assertNotAlmostEqual(
            80.0 - weak.evidence_score, 80.0 - strong.evidence_score, places=1
        )

    def test_neutral_evidence_moves_neither_strength(self) -> None:
        without = run([item("s", q=0.7)])
        with_neutral = run([item("s", q=0.7), item("n", q=0.9, direction=D.NEUTRAL)])
        self.assertAlmostEqual(
            without.masses.support_strength, with_neutral.masses.support_strength
        )
        self.assertAlmostEqual(with_neutral.masses.contradiction_strength, 0.0)
        self.assertEqual(with_neutral.neutral_evidence_count, 1)
        # Retained rather than dropped: it bears on the claim and counts towards
        # coverage even though it moves no number.
        self.assertEqual(with_neutral.raw_evidence_count, 2)


# ================================================================= evidence level


class TestEvidenceLevel(unittest.TestCase):
    def test_no_supporting_evidence_is_hypothesis(self) -> None:
        self.assertEqual(run([]).level.level, 0)

    def test_one_supporting_record_is_a_weak_signal(self) -> None:
        self.assertEqual(run([item("a")]).level.level, 1)

    def test_duplicates_cannot_create_a_repeated_signal(self) -> None:
        """§22. Ten copies of one article are not a recurring pattern."""
        result = run([item(f"copy-{i}", state=IND.KNOWN_DEPENDENT, group="g1") for i in range(10)])
        self.assertEqual(result.level.level, 1)
        self.assertTrue(any("Repeated Signal" in r for r in result.level.blocked_reasons))

    def test_unknown_provenance_cannot_create_a_repeated_signal(self) -> None:
        result = run([item(f"u-{i}", state=IND.UNKNOWN) for i in range(10)])
        self.assertEqual(result.level.level, 1)

    def test_one_known_record_plus_unknown_ones_is_not_a_repeated_signal(self) -> None:
        """The unknown bucket is excluded from the level count entirely, not
        counted as one group. One established record plus a pile of unlabelled
        ones is not two observations: the unlabelled ones may all derive from
        the established one."""
        result = run([item("known"), *[item(f"u-{i}", state=IND.UNKNOWN) for i in range(10)]])
        self.assertEqual(result.support_group_count, 2)
        self.assertEqual(result.level.level, 1)
        self.assertTrue(
            any("does not count" in r for r in result.level.blocked_reasons),
            result.level.blocked_reasons,
        )

    def test_two_independent_groups_reach_repeated_signal(self) -> None:
        self.assertEqual(run([item("a"), item("b")]).level.level, 2)

    def test_multi_source_needs_groups_and_families(self) -> None:
        same_family = run([item("a"), item("b"), item("c")])
        self.assertEqual(same_family.level.level, 2)
        many_families = run(
            [item("a", family="f1"), item("b", family="f2"), item("c", family="f3")]
        )
        self.assertEqual(many_families.level.level, 3)

    def test_volume_of_opinion_never_reaches_market_evidence(self) -> None:
        """§23. The failure this gate exists to prevent."""
        result = run([item(f"o-{i}", q=0.9, family=f"f{i % 5}") for i in range(50)])
        self.assertEqual(result.level.level, 3)
        self.assertTrue(any("Market Evidence" in r for r in result.level.blocked_reasons))

    def test_one_market_record_reaches_level_four(self) -> None:
        """The kind of observation dominates its quantity."""
        result = run([item("m", category=C.MARKET_ACTIVITY)])
        self.assertEqual(result.level.level, 4)

    def test_one_validation_record_reaches_level_five(self) -> None:
        result = run([item("v", category=C.DIRECT_VALIDATION)])
        self.assertEqual(result.level.level, 5)

    def test_market_evidence_requires_established_provenance(self) -> None:
        """A record nobody has placed cannot be market evidence: it may be a
        syndicated copy of something else."""
        result = run([item("m", category=C.MARKET_ACTIVITY, state=IND.UNKNOWN)])
        self.assertLess(result.level.level, 4)

    def test_an_uncategorised_record_cannot_pass_level_three(self) -> None:
        result = run([item(f"u-{i}", category=C.UNCATEGORISED, family=f"f{i}") for i in range(6)])
        self.assertLessEqual(result.level.level, 3)

    def test_the_level_is_not_derived_from_the_score(self) -> None:
        """A high score with a low level, and a low score with a high level.
        Threshold-derived levels could produce neither."""
        loud = run([item(f"o-{i}", q=0.95, family=f"f{i % 4}") for i in range(20)])
        quiet = run([item("v", q=0.2, category=C.DIRECT_VALIDATION)])
        assert loud.evidence_score is not None and quiet.evidence_score is not None
        self.assertGreater(loud.evidence_score, quiet.evidence_score)
        self.assertLess(loud.level.level, quiet.level.level)


# =============================================================== reproducibility


class TestReproducibility(unittest.TestCase):
    def build(self):
        return [
            item("a", q=0.8, family="f1"),
            item("b", q=0.6, family="f2"),
            item("c", q=0.4, direction=D.CONTRADICTS),
            item("d", q=0.5, state=IND.KNOWN_DEPENDENT, group="g1"),
            item("e", q=0.7, state=IND.UNKNOWN),
        ]

    def test_evidence_ordering_does_not_change_the_result(self) -> None:
        """§30.7, on the whole pipeline rather than one operator."""
        forward = run(self.build())
        backward = run(list(reversed(self.build())))
        self.assertEqual(forward.canonical_json(), backward.canonical_json())

    def test_the_same_snapshot_produces_byte_identical_output(self) -> None:
        first = run(self.build())
        second = run(self.build())
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertEqual(first.evidence_snapshot_digest, second.evidence_snapshot_digest)

    def test_a_changed_input_changes_the_digest(self) -> None:
        """§28. A recomputation over different evidence must be identifiable as
        such rather than silently replacing the original."""
        base = run(self.build())
        changed = run([*self.build()[:-1], item("e", q=0.71, state=IND.UNKNOWN)])
        self.assertNotEqual(base.evidence_snapshot_digest, changed.evidence_snapshot_digest)

    def test_the_result_records_its_profile_and_algorithm_versions(self) -> None:
        result = run(self.build())
        self.assertEqual(result.aggregation_profile_id, "reference-v1")
        self.assertEqual(result.aggregation_profile_version, "1.0.0")
        self.assertEqual(result.aggregation_profile_status, "UNCALIBRATED")
        self.assertTrue(result.algorithm_version)

    def test_a_duplicate_evidence_id_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            run([item("a"), item("a")])

    def test_the_explanation_covers_every_record(self) -> None:
        """§27. No score without lineage, including the records that dropped out."""
        items = [*self.build(), item("dropped", reliability=None)]
        result = run(items)
        explained = {c.evidence_id for c in result.contributions}
        self.assertEqual(explained, {i.evidence_id for i in items})
        self.assertIn("dropped", result.explain())
        self.assertIn("NON-SCORABLE", result.explain())


# ========================================================================= gates


class TestProductionGates(unittest.TestCase):
    def test_an_uncalibrated_profile_refuses_to_run_silently(self) -> None:
        """§41. Defining the equations does not make production scoring
        available; the caller has to say the numbers are not calibrated."""
        with self.assertRaises(UncalibratedProfileError):
            aggregate(
                "c",
                [item("a")],
                REFERENCE_PROFILE_V1,
                temporality=ClaimTemporality.EVERGREEN,
                now=NOW,
            )

    def test_an_uncalibrated_result_carries_a_warning(self) -> None:
        result = run([item("a")])
        self.assertFalse(result.calibrated)
        self.assertTrue(any("not calibrated" in w for w in result.warnings))

    def test_no_calibrated_profile_ships_with_the_framework(self) -> None:
        """The state of the world after Mission 1.1: framework defined,
        parameters not fitted. If this ever fails, somebody calibrated something
        without a dataset."""
        self.assertIs(REFERENCE_PROFILE_V1.status, AggregationProfileStatus.UNCALIBRATED)
        self.assertIsNone(REFERENCE_PROFILE_V1.calibration_dataset_ref)

    def test_a_calibrated_profile_must_name_its_dataset(self) -> None:
        with self.assertRaises(ProfileError):
            EvidenceAggregationProfile(
                profile_id="p", version="1", status=AggregationProfileStatus.CALIBRATED
            )

    def test_a_draft_or_retired_profile_cannot_run(self) -> None:
        for status in (AggregationProfileStatus.DRAFT, AggregationProfileStatus.RETIRED):
            profile = EvidenceAggregationProfile(profile_id="p", version="1", status=status)
            with self.assertRaises(ProfileError):
                aggregate("c", [item("a")], profile, now=NOW, allow_uncalibrated=True)

    def test_level_thresholds_cannot_be_weakened_below_their_meaning(self) -> None:
        with self.assertRaises(ProfileError):
            LevelThresholds(repeated_signal_min_groups=1)
        with self.assertRaises(ProfileError):
            LevelThresholds(multi_source_min_families=1)


class TestNoSourceWeights(unittest.TestCase):
    """§7 and §42, asserted mechanically rather than remembered."""

    REGISTERED_SOURCES = (
        "reddit",
        "hacker-news",
        "stack-exchange",
        "product-hunt",
        "github",
        "apple-app-store",
        "google-play",
        "youtube",
        "tiktok",
        "google-trends",
        "world-bank",
        "eurostat",
        "fred",
    )

    def _package_sources(self) -> dict[str, str]:
        import pathlib

        import sros_evidence_aggregation

        root = pathlib.Path(sros_evidence_aggregation.__file__).parent
        return {p.name: p.read_text(encoding="utf-8") for p in root.glob("*.py")}

    def test_no_registered_source_appears_in_the_package(self) -> None:
        """A per-platform coefficient is the failure §7 forbids, and the surest
        way to detect one is that the platform is named at all."""
        for filename, text in self._package_sources().items():
            lowered = text.lower()
            for source_id in self.REGISTERED_SOURCES:
                self.assertNotIn(
                    source_id,
                    lowered,
                    f"{filename} names the source {source_id!r}. Reliability is a property "
                    "of an evidence record against a claim, never of the platform",
                )

    def test_source_identity_does_not_reach_the_arithmetic(self) -> None:
        """Two identical evidence sets differing only in source id must produce
        identical numbers."""
        a = run([item("e1", q=0.7), item("e2", q=0.5, family="f2")])
        b_items = [
            EvidenceItem(
                "e1",
                D.SUPPORTS,
                relevance=0.7,
                directness=0.7,
                reliability=0.7,
                extraction_confidence=0.7,
                independence_state=IND.KNOWN_INDEPENDENT,
                source_id="a-totally-different-platform",
                source_family="family-a",
            ),
            EvidenceItem(
                "e2",
                D.SUPPORTS,
                relevance=0.5,
                directness=0.5,
                reliability=0.5,
                extraction_confidence=0.5,
                independence_state=IND.KNOWN_INDEPENDENT,
                source_id="another-one",
                source_family="f2",
            ),
        ]
        b = run(b_items)
        self.assertAlmostEqual(a.masses.support_strength, b.masses.support_strength)
        self.assertEqual(a.evidence_score, b.evidence_score)

    def test_the_package_opens_no_network_and_no_database(self) -> None:
        """§43, §35. It governs how evidence combines; it collects nothing."""
        forbidden = (
            "import requests",
            "import httpx",
            "import urllib",
            "import socket",
            "import psycopg",
            "import aiohttp",
            "from urllib",
            "from psycopg",
        )
        for filename, text in self._package_sources().items():
            for token in forbidden:
                self.assertNotIn(token, text, f"{filename} imports {token!r}")


class TestSensitivityHarness(unittest.TestCase):
    def test_every_scenario_runs(self) -> None:
        from sros_evidence_aggregation.sensitivity import run_all

        results = run_all()
        self.assertGreaterEqual(len(results), 12)
        for scenario, result in results:
            self.assertTrue(result.canonical_json(), scenario.key)

    def test_the_duplicate_scenario_matches_the_single_group_scenario(self) -> None:
        """The headline claim of the report, asserted rather than eyeballed."""
        from sros_evidence_aggregation.sensitivity import SCENARIOS, run_scenario

        by_key = {s.key: s for s in SCENARIOS}
        one = run_scenario(by_key["one-strong-group"])
        ten = run_scenario(by_key["ten-duplicates"])
        self.assertEqual(one.evidence_score, ten.evidence_score)

    def test_the_harness_uses_no_real_source(self) -> None:
        from sros_evidence_aggregation.sensitivity import run_all

        for _, result in run_all():
            for contribution in result.contributions:
                self.assertTrue(contribution.evidence_id)
            for group in (*result.groups.support, *result.groups.contradiction):
                self.assertNotIn("reddit", group.group_id.lower())


if __name__ == "__main__":
    unittest.main()
