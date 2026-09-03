"""The Signal contract, over synthetic objects only.

Mission 1.11 §42. **No network, no database, no real record.** Every fixture
below is invented; where one is shaped after a real observation the docstring
says so and says it is a shape rather than a capture.

The suite is organised around the decisions the contract makes, because those
are what a later change is most likely to erode:

    §3   two observations, or no Signal
    §5   magnitude is exact, typed, and not a strength
    §6   direction is change, and needs an order
    §7   parameters are declared and fingerprinted
    §8   deterministic means no model provenance
    §10  PARTIAL is not unusable; INVALID is
    §13  scope omits what the inputs do not carry
    §14  only a shared timeline carries bounds
    §15  identity is inputs, extractor, parameters and window -- not outputs
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sros_contracts import (
    NormalizationQualityReason as Reason,
)
from sros_contracts import (
    NormalizedPeriodType,
    NormalizedRecordQuality,
    SignalDerivationKind,
    SignalDirection,
    SignalInputRole,
    SignalMagnitudeKind,
    SignalMagnitudeUnitState,
    SignalQuantityFamily,
    SignalRefusalReason,
    SignalRequiredFact,
    SignalTemporalBasis,
)
from sros_signal_model import (
    MINIMUM_DISTINCT_OBSERVATIONS,
    ORDER_ESTABLISHED_WITHOUT_TIMEZONE,
    ORDERED_BASES,
    SIGNAL_EXTRACTORS,
    SIGNAL_TYPES,
    ObservationInput,
    SignalDerivation,
    SignalMagnitude,
    SignalRefusedError,
    SignalScope,
    SignalWindow,
    TemporalOrderCertification,
    assess_inputs,
    build_signal,
    canonical_fingerprint,
    canonical_json,
    order_certification,
    withheld_facts,
)

WORKSPACE = "11111111-1111-4111-8111-111111111111"
SESSION = "22222222-2222-4222-8222-222222222222"
DERIVED_AT = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)
EXPIRES_AT = DERIVED_AT + timedelta(days=365)


# --------------------------------------------------------------- fixtures
#
# SYNTHETIC. The GDELT pair is shaped after the two real normalized records --
# one bucket, one language label, two terms -- because that is the shape the
# contract has to support. The ids and hashes are invented and no byte here came
# from a source.


def gdelt_observation(
    term: str,
    *,
    record_id: str,
    bucket: str = "20260830091500",
    resource_id: str | None = "web-ngrams/1gram",
):
    return ObservationInput(
        normalized_record_id=record_id,
        raw_record_id=f"raw-{record_id}",
        source_id="gdelt",
        resource_id=resource_id,
        observation_key=f"gdelt|web-ngrams/1gram|{bucket}|ENGLISH|{term}",
        record_kind_id="lexical_frequency_observation",
        period_type=NormalizedPeriodType.INTERVAL,
        period_label=bucket,
        quality=NormalizedRecordQuality.PARTIAL,
        quality_reasons=frozenset(
            {Reason.PERIOD_TIMEZONE_NOT_ESTABLISHED, Reason.LANGUAGE_NOT_MAPPED}
        ),
    )


def world_bank_observation(year: str, *, record_id: str, geography: str = "DEU"):
    return ObservationInput(
        normalized_record_id=record_id,
        raw_record_id=f"raw-{record_id}",
        source_id="world-bank",
        observation_key=f"world-bank|indicator/SP.POP.TOTL|{geography}|{year}",
        record_kind_id="numeric_observation",
        period_type=NormalizedPeriodType.YEAR,
        period_label=year,
        quality=NormalizedRecordQuality.VALID,
    )


LEXICAL_DERIVATION = SignalDerivation(
    extractor_id="gdelt-lexical-contrast",
    extractor_version="1.0.0",
    kind=SignalDerivationKind.DETERMINISTIC,
    required_facts=frozenset(
        {
            SignalRequiredFact.EXACT_NUMERIC_VALUE,
            SignalRequiredFact.LEXICAL_TERM,
            SignalRequiredFact.SOURCE_PERIOD_LABEL,
            SignalRequiredFact.SOURCE_LANGUAGE_LABEL,
        }
    ),
    parameter_names=frozenset({"comparison"}),
    parameters={"comparison": "ratio_to_first"},
)

NUMERIC_DERIVATION = SignalDerivation(
    extractor_id="world-bank-numeric-change",
    extractor_version="1.0.0",
    kind=SignalDerivationKind.DETERMINISTIC,
    required_facts=frozenset(
        {
            SignalRequiredFact.EXACT_NUMERIC_VALUE,
            SignalRequiredFact.COMPARABLE_INSTANT,
            SignalRequiredFact.CLASSIFIED_GEOGRAPHY,
        }
    ),
    parameter_names=frozenset({"comparison"}),
    parameters={"comparison": "later_minus_earlier"},
)

LEXICAL_WINDOW = SignalWindow(
    basis=SignalTemporalBasis.SAME_PERIOD_LABEL,
    period_labels=("20260830091500", "20260830091500"),
    resolution=NormalizedPeriodType.INTERVAL,
    observation_count=2,
)

NUMERIC_WINDOW = SignalWindow(
    basis=SignalTemporalBasis.COMPARABLE_INSTANTS,
    period_labels=("2018", "2019"),
    resolution=NormalizedPeriodType.YEAR,
    observation_count=2,
    start=datetime(2018, 1, 1, tzinfo=UTC),
    end=datetime(2020, 1, 1, tzinfo=UTC),
)


def lexical_signal(**overrides):
    kwargs = dict(
        workspace_id=WORKSPACE,
        signal_type_id="lexical_frequency_contrast",
        observations=[
            gdelt_observation("climate", record_id="n-1"),
            gdelt_observation("weather", record_id="n-2"),
        ],
        derivation=LEXICAL_DERIVATION,
        direction=SignalDirection.NOT_APPLICABLE,
        magnitude=SignalMagnitude(
            value=Decimal("1.47"),
            kind=SignalMagnitudeKind.RATIO,
            unit_state=SignalMagnitudeUnitState.DIMENSIONLESS,
        ),
        derivation_confidence=1.0,
        scope=SignalScope(
            source_ids=("gdelt",),
            terms=("climate", "weather"),
            source_language_labels=("ENGLISH",),
            source_language_scheme="cld2-language-name",
        ),
        window=LEXICAL_WINDOW,
        derived_at=DERIVED_AT,
        expires_at=EXPIRES_AT,
        correlation_id="corr-1",
        research_session_id=SESSION,
    )
    kwargs.update(overrides)
    return build_signal(**kwargs)


def numeric_signal(**overrides):
    kwargs = dict(
        workspace_id=WORKSPACE,
        signal_type_id="numeric_period_change",
        observations=[
            world_bank_observation("2018", record_id="n-10"),
            world_bank_observation("2019", record_id="n-11"),
        ],
        derivation=NUMERIC_DERIVATION,
        direction=SignalDirection.INCREASING,
        magnitude=SignalMagnitude(
            value=Decimal("139000"),
            kind=SignalMagnitudeKind.ABSOLUTE_CHANGE,
            unit_state=SignalMagnitudeUnitState.NOT_ESTABLISHED,
        ),
        derivation_confidence=1.0,
        scope=SignalScope(
            source_ids=("world-bank",),
            metric_ids=("SP.POP.TOTL",),
            geography_codes=("DE",),
        ),
        window=NUMERIC_WINDOW,
        derived_at=DERIVED_AT,
        expires_at=EXPIRES_AT,
        correlation_id="corr-2",
    )
    kwargs.update(overrides)
    return build_signal(**kwargs)


# ============================================================ §3 the contrast rule


class TestOneObservationIsNotASignal(unittest.TestCase):
    """§3, §37. There is no predetermined answer in the brief, and this is it."""

    def test_two_is_the_floor(self):
        self.assertEqual(MINIMUM_DISTINCT_OBSERVATIONS, 2)

    def test_a_single_observation_is_refused(self):
        with self.assertRaises(SignalRefusedError) as caught:
            lexical_signal(
                observations=[gdelt_observation("climate", record_id="n-1")],
                window=SignalWindow(
                    basis=SignalTemporalBasis.SAME_PERIOD_LABEL,
                    period_labels=("20260830091500",),
                    resolution=NormalizedPeriodType.INTERVAL,
                    observation_count=2,
                ),
            )
        self.assertIs(
            caught.exception.refusal.reason,
            SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS,
        )

    def test_two_rows_of_one_observation_do_not_make_a_contrast(self):
        """D-08. Distinctness is over `observation_key`, never over the row id.

        Two normalizer versions of one observation are two rows and one
        observation. Counting rows would let an UPGRADE manufacture a finding.
        """
        first = gdelt_observation("climate", record_id="n-1")
        renormalized = ObservationInput(
            normalized_record_id="n-1-v2",
            raw_record_id=first.raw_record_id,
            source_id=first.source_id,
            observation_key=first.observation_key,
            record_kind_id=first.record_kind_id,
            period_type=first.period_type,
            period_label=first.period_label,
            quality=first.quality,
            quality_reasons=first.quality_reasons,
        )
        with self.assertRaises(SignalRefusedError) as caught:
            lexical_signal(observations=[first, renormalized])
        self.assertIs(
            caught.exception.refusal.reason,
            SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE,
        )

    def test_a_refusal_is_a_value_object_and_serialises(self):
        assessment = assess_inputs(
            [gdelt_observation("climate", record_id="n-1")],
            LEXICAL_DERIVATION,
            family=SignalQuantityFamily.LEXICAL_FREQUENCY,
            resolution=NormalizedPeriodType.INTERVAL,
        )
        self.assertIsNotNone(assessment.refusal)
        payload = assessment.refusal.to_json()
        self.assertEqual(payload["reason"], "INSUFFICIENT_INPUT_OBSERVATIONS")


# ================================================== §10 quality and required facts


class TestQualityInteraction(unittest.TestCase):
    """§10. PARTIAL is not unusable; INVALID is; the SPECIFIC fact is what counts."""

    def test_partial_gdelt_records_still_produce_a_signal(self):
        """The whole point. Both records carry two quality reasons and neither
        touches a within-bucket contrast between two terms."""
        draft = lexical_signal()
        self.assertEqual(len(draft.contributed), 2)
        self.assertTrue(
            all(a.observation.quality is NormalizedRecordQuality.PARTIAL for a in draft.contributed)
        )

    def test_an_invalid_record_is_excluded_not_read(self):
        broken = ObservationInput(
            normalized_record_id="n-3",
            raw_record_id="raw-n-3",
            source_id="gdelt",
            observation_key="gdelt|web-ngrams/1gram|20260830091500|ENGLISH|storm",
            record_kind_id="lexical_frequency_observation",
            period_type=NormalizedPeriodType.INTERVAL,
            period_label="20260830091500",
            quality=NormalizedRecordQuality.INVALID,
            quality_reasons=frozenset({Reason.PERIOD_NOT_SUPPORTED}),
        )
        draft = lexical_signal(
            observations=[
                gdelt_observation("climate", record_id="n-1"),
                gdelt_observation("weather", record_id="n-2"),
                broken,
            ]
        )
        excluded = draft.inputs[-1]
        self.assertIs(excluded.role, SignalInputRole.EXCLUDED)
        self.assertIs(excluded.refusal_reason, SignalRefusalReason.INPUT_RECORD_INVALID)
        self.assertEqual(len(draft.contributed), 2)

    def test_an_excluded_input_is_recorded_rather_than_dropped(self):
        """§19. 'We looked at three and used two' has to be visible."""
        draft = lexical_signal(
            observations=[
                gdelt_observation("climate", record_id="n-1"),
                gdelt_observation("weather", record_id="n-2"),
                ObservationInput(
                    normalized_record_id="n-4",
                    raw_record_id="raw-n-4",
                    source_id="gdelt",
                    observation_key="gdelt|web-ngrams/1gram|20260830091500|ENGLISH|hail",
                    record_kind_id="lexical_frequency_observation",
                    period_type=NormalizedPeriodType.INTERVAL,
                    period_label="20260830091500",
                    quality=NormalizedRecordQuality.PARTIAL,
                    quality_reasons=frozenset(
                        {
                            Reason.PERIOD_TIMEZONE_NOT_ESTABLISHED,
                            Reason.LANGUAGE_NOT_MAPPED,
                            Reason.VALUE_NOT_REPORTED,
                        }
                    ),
                ),
            ]
        )
        self.assertEqual(len(draft.inputs), 3)
        lineage = draft.lineage_json()
        self.assertEqual(lineage[2]["role"], "EXCLUDED")
        self.assertEqual(lineage[2]["refusal_reason"], "REQUIRED_FACT_WITHHELD")
        self.assertEqual(lineage[2]["withheld_facts"], ["EXACT_NUMERIC_VALUE"])

    def test_h30_blocks_only_the_derivations_that_need_a_canonical_tag(self):
        """§14, §44. The source label is enough within one source; the tag is not
        available at all."""
        observation = gdelt_observation("climate", record_id="n-1")
        self.assertEqual(
            withheld_facts(
                frozenset({SignalRequiredFact.SOURCE_LANGUAGE_LABEL}),
                record_kind_id=observation.record_kind_id,
                quality_reasons=observation.quality_reasons,
                source_id=observation.source_id,
            ),
            frozenset(),
        )
        self.assertEqual(
            withheld_facts(
                frozenset({SignalRequiredFact.CANONICAL_LANGUAGE}),
                record_kind_id=observation.record_kind_id,
                quality_reasons=observation.quality_reasons,
                source_id=observation.source_id,
            ),
            frozenset({SignalRequiredFact.CANONICAL_LANGUAGE}),
        )

    def test_a_fact_the_record_kind_cannot_supply_is_withheld(self):
        """`withheld_by` being empty does not make a fact decorative."""
        self.assertEqual(
            withheld_facts(
                frozenset({SignalRequiredFact.LEXICAL_TERM}),
                record_kind_id="numeric_observation",
                quality_reasons=frozenset(),
                source_id="world-bank",
            ),
            frozenset({SignalRequiredFact.LEXICAL_TERM}),
        )


# ============================================= §12 H-29, order, and the two facts


class TestTemporalSemantics(unittest.TestCase):
    """§12, §13, §43. ORDER and GLOBAL INSTANT are different questions."""

    def test_h29_blocks_a_comparable_instant_for_gdelt(self):
        observation = gdelt_observation("climate", record_id="n-1")
        self.assertEqual(
            withheld_facts(
                frozenset({SignalRequiredFact.COMPARABLE_INSTANT}),
                record_kind_id=observation.record_kind_id,
                quality_reasons=observation.quality_reasons,
                source_id=observation.source_id,
            ),
            frozenset({SignalRequiredFact.COMPARABLE_INSTANT}),
        )

    def test_h32_grants_source_relative_order_to_the_reviewed_stream(self):
        """Until Mission 1.12 this asserted the opposite, and correctly.

        H-32 was closed on GDELT's own evidence -- its BigQuery analysis orders
        this table by DATE, its MASTERFILELIST is sequenced by the label at
        15-minute resolution, and its LASTUPDATE names the maximal label as the
        newest publication. The record still says
        PERIOD_TIMEZONE_NOT_ESTABLISHED and the certification overrides that
        reason and NO other."""
        observation = gdelt_observation("climate", record_id="n-1")
        self.assertEqual(
            withheld_facts(
                frozenset({SignalRequiredFact.SOURCE_RELATIVE_ORDER}),
                record_kind_id=observation.record_kind_id,
                quality_reasons=observation.quality_reasons,
                source_id=observation.source_id,
                resource_id=observation.resource_id,
            ),
            frozenset(),
        )

    def test_order_does_not_leak_into_a_comparable_instant(self):
        """The whole point of keeping B and C apart. The same record, the same
        quality reasons, and the two facts get opposite answers."""
        observation = gdelt_observation("climate", record_id="n-1")
        self.assertEqual(
            withheld_facts(
                frozenset(
                    {
                        SignalRequiredFact.SOURCE_RELATIVE_ORDER,
                        SignalRequiredFact.COMPARABLE_INSTANT,
                    }
                ),
                record_kind_id=observation.record_kind_id,
                quality_reasons=observation.quality_reasons,
                source_id=observation.source_id,
                resource_id=observation.resource_id,
            ),
            frozenset({SignalRequiredFact.COMPARABLE_INSTANT}),
        )

    def test_an_unreviewed_resource_inherits_nothing(self):
        """`chargram` is published in the same directory, by the same source,
        with the same label scheme, and no review has assessed it. A prefix
        match on `web-ngrams/` would have covered it silently."""
        observation = gdelt_observation(
            "climate", record_id="n-1", resource_id="web-ngrams/chargram"
        )
        self.assertEqual(
            withheld_facts(
                frozenset({SignalRequiredFact.SOURCE_RELATIVE_ORDER}),
                record_kind_id=observation.record_kind_id,
                quality_reasons=observation.quality_reasons,
                source_id=observation.source_id,
                resource_id=observation.resource_id,
            ),
            frozenset({SignalRequiredFact.SOURCE_RELATIVE_ORDER}),
        )

    def test_an_observation_that_cannot_name_its_resource_inherits_nothing(self):
        """The default is a refusal, not a convenience."""
        observation = gdelt_observation("climate", record_id="n-1", resource_id=None)
        self.assertEqual(
            withheld_facts(
                frozenset({SignalRequiredFact.SOURCE_RELATIVE_ORDER}),
                record_kind_id=observation.record_kind_id,
                quality_reasons=observation.quality_reasons,
                source_id=observation.source_id,
                resource_id=observation.resource_id,
            ),
            frozenset({SignalRequiredFact.SOURCE_RELATIVE_ORDER}),
        )

    def test_an_unreviewed_source_inherits_nothing(self):
        """Ordering is certified per stream, never per label shape. A source
        publishing identical-looking YYYYMMDDHHMMSS labels gets nothing."""
        self.assertIsNone(order_certification("some-other-source", "web-ngrams/1gram"))
        self.assertIsNone(order_certification("gdelt", "webngrams"))

    def test_a_period_that_could_not_be_represented_still_has_no_order(self):
        """The certification overrides an unestablished TIMEZONE and nothing
        else. A period the adapter could not represent has no order either."""
        broken = ObservationInput(
            normalized_record_id="n-9",
            raw_record_id="raw-n-9",
            source_id="gdelt",
            resource_id="web-ngrams/1gram",
            observation_key="gdelt|web-ngrams/1gram|nonsense|ENGLISH|climate",
            record_kind_id="lexical_frequency_observation",
            period_type=NormalizedPeriodType.INTERVAL,
            period_label="nonsense",
            quality=NormalizedRecordQuality.INVALID,
            quality_reasons=frozenset(
                {Reason.PERIOD_NOT_SUPPORTED, Reason.PERIOD_TIMEZONE_NOT_ESTABLISHED}
            ),
        )
        self.assertEqual(
            withheld_facts(
                frozenset({SignalRequiredFact.SOURCE_RELATIVE_ORDER}),
                record_kind_id=broken.record_kind_id,
                quality_reasons=broken.quality_reasons,
                source_id=broken.source_id,
                resource_id=broken.resource_id,
            ),
            frozenset({SignalRequiredFact.SOURCE_RELATIVE_ORDER}),
        )

    def test_the_label_itself_is_available_with_h29_open(self):
        observation = gdelt_observation("climate", record_id="n-1")
        self.assertEqual(
            withheld_facts(
                frozenset({SignalRequiredFact.SOURCE_PERIOD_LABEL}),
                record_kind_id=observation.record_kind_id,
                quality_reasons=observation.quality_reasons,
                source_id=observation.source_id,
            ),
            frozenset(),
        )

    def test_exactly_one_stream_is_order_certified(self):
        """Until Mission 1.12 this asserted the map was EMPTY.

        It holds one entry now, and the constraints on it are what the old
        assertion was protecting: every entry states its basis, names its
        resources rather than matching a prefix, and grants ordering only."""
        self.assertEqual(len(ORDER_ESTABLISHED_WITHOUT_TIMEZONE), 1)
        (certification,) = ORDER_ESTABLISHED_WITHOUT_TIMEZONE
        self.assertEqual(certification.source_id, "gdelt")
        self.assertEqual(
            certification.resource_ids,
            frozenset({"web-ngrams/1gram", "web-ngrams/2gram"}),
        )
        self.assertEqual(certification.label_scheme, "gdelt-web-ngram-bucket")
        self.assertEqual(certification.review_version, 3)

    def test_every_certification_states_its_basis(self):
        """A certification nobody can re-check is a guess with a citation field."""
        for certification in ORDER_ESTABLISHED_WITHOUT_TIMEZONE:
            self.assertTrue(certification.basis.strip())
            self.assertTrue(certification.scope.strip())

    def test_a_certification_may_not_cover_everything(self):
        with self.assertRaises(ValueError):
            TemporalOrderCertification(
                source_id="gdelt",
                resource_ids=frozenset(),
                label_scheme="x",
                review_version=3,
                basis="b",
                scope="s",
            )

    def test_a_certification_may_not_omit_its_basis(self):
        with self.assertRaises(ValueError):
            TemporalOrderCertification(
                source_id="gdelt",
                resource_ids=frozenset({"web-ngrams/1gram"}),
                label_scheme="x",
                review_version=3,
                basis="   ",
                scope="s",
            )

    def test_no_certification_grants_a_timezone(self):
        """H-29 is untouched. Nothing in the certification vocabulary can say
        UTC, an offset, or an instant."""
        for certification in ORDER_ESTABLISHED_WITHOUT_TIMEZONE:
            serialised = canonical_json(
                {
                    "source": certification.source_id,
                    "scheme": certification.label_scheme,
                    "scope": certification.scope,
                }
            ).lower()
            for invented in ("utc", "gmt", "+00:00", "offset"):
                self.assertNotIn(invented, serialised)
            self.assertFalse(hasattr(certification, "timezone"))
            self.assertFalse(hasattr(certification, "utc_offset"))

    def test_ordered_periods_carries_no_bounds_and_no_event_time(self):
        """§14. Closing H-32 gave GDELT an ORDER, not an INSTANT. An
        ORDERED_PERIODS window has no start, no end and no observed_at, so
        nothing can convert one to a TIMESTAMPTZ."""
        window = SignalWindow(
            basis=SignalTemporalBasis.ORDERED_PERIODS,
            period_labels=("20260830091500", "20260830093000"),
            resolution=NormalizedPeriodType.INTERVAL,
            observation_count=2,
        )
        self.assertIsNone(window.event_time)
        self.assertNotIn("start", window.to_json())
        self.assertNotIn("end", window.to_json())
        with self.assertRaises(ValueError):
            SignalWindow(
                basis=SignalTemporalBasis.ORDERED_PERIODS,
                period_labels=("20260830091500", "20260830093000"),
                resolution=NormalizedPeriodType.INTERVAL,
                observation_count=2,
                start=datetime(2026, 8, 30, 9, 15, tzinfo=UTC),
                end=datetime(2026, 8, 30, 9, 45, tzinfo=UTC),
            )

    def test_an_ordered_basis_permits_a_direction_without_a_timeline(self):
        """The point of closing H-32: `INCREASING` becomes sayable about two
        buckets in one stream, and still says nothing about when either was."""
        self.assertIn(SignalTemporalBasis.ORDERED_PERIODS, ORDERED_BASES)
        self.assertIn(SignalTemporalBasis.COMPARABLE_INSTANTS, ORDERED_BASES)
        self.assertNotIn(SignalTemporalBasis.SAME_PERIOD_LABEL, ORDERED_BASES)
        self.assertNotIn(SignalTemporalBasis.NONE, ORDERED_BASES)

    def test_only_a_shared_timeline_carries_bounds(self):
        with self.assertRaises(ValueError):
            SignalWindow(
                basis=SignalTemporalBasis.SAME_PERIOD_LABEL,
                period_labels=("20260830091500", "20260830091500"),
                resolution=NormalizedPeriodType.INTERVAL,
                observation_count=2,
                start=datetime(2026, 8, 30, 9, 15, tzinfo=UTC),
                end=datetime(2026, 8, 30, 9, 30, tzinfo=UTC),
            )

    def test_a_naive_bound_is_refused_under_comparable_instants(self):
        with self.assertRaises(ValueError):
            SignalWindow(
                basis=SignalTemporalBasis.COMPARABLE_INSTANTS,
                period_labels=("2018", "2019"),
                resolution=NormalizedPeriodType.YEAR,
                observation_count=2,
                start=datetime(2018, 1, 1),  # noqa: DTZ001 -- the thing being refused
                end=datetime(2020, 1, 1, tzinfo=UTC),
            )

    def test_same_period_label_means_exactly_one_label(self):
        with self.assertRaises(ValueError):
            SignalWindow(
                basis=SignalTemporalBasis.SAME_PERIOD_LABEL,
                period_labels=("20260830091500", "20260830093000"),
                resolution=NormalizedPeriodType.INTERVAL,
                observation_count=2,
            )

    def test_observed_at_is_null_without_a_shared_timeline(self):
        self.assertIsNone(lexical_signal().observed_at)
        self.assertEqual(numeric_signal().observed_at, datetime(2020, 1, 1, tzinfo=UTC))

    def test_mixed_resolutions_refuse_the_whole_derivation(self):
        """Never silently coarsened: excluding the odd one out would be the same
        thing by another route."""
        with self.assertRaises(SignalRefusedError) as caught:
            numeric_signal(
                observations=[
                    world_bank_observation("2018", record_id="n-10"),
                    ObservationInput(
                        normalized_record_id="n-12",
                        raw_record_id="raw-n-12",
                        source_id="world-bank",
                        observation_key="world-bank|indicator/SP.POP.TOTL|DEU|2019-Q1",
                        record_kind_id="numeric_observation",
                        period_type=NormalizedPeriodType.QUARTER,
                        period_label="2019Q1",
                        quality=NormalizedRecordQuality.VALID,
                    ),
                ]
            )
        self.assertIs(
            caught.exception.refusal.reason,
            SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS,
        )


# ============================================================== §6 direction


class TestDirection(unittest.TestCase):
    def test_direction_requires_an_order(self):
        """No GDELT signal can carry a direction while H-29 and H-32 are open."""
        with self.assertRaises(ValueError) as caught:
            lexical_signal(direction=SignalDirection.INCREASING)
        self.assertIn("before and after", str(caught.exception))

    def test_an_ordered_basis_permits_one(self):
        self.assertIs(numeric_signal().direction, SignalDirection.INCREASING)

    def test_there_is_no_sentiment_value(self):
        """§7. POSITIVE and NEGATIVE were on the candidate list and are absent: a
        complaint-frequency signal can be INCREASING while its sentiment is
        negative, and one enum holding both makes that unrepresentable."""
        values = {member.value for member in SignalDirection}
        self.assertEqual(
            values,
            {"INCREASING", "DECREASING", "UNCHANGED", "INDETERMINATE", "NOT_APPLICABLE"},
        )


# ============================================================== §5 magnitude


class TestMagnitude(unittest.TestCase):
    def test_a_float_is_refused(self):
        with self.assertRaises(ValueError):
            SignalMagnitude(
                value=1.47,  # type: ignore[arg-type]
                kind=SignalMagnitudeKind.RATIO,
                unit_state=SignalMagnitudeUnitState.DIMENSIONLESS,
            )

    def test_exactness_survives_beyond_float_range(self):
        magnitude = SignalMagnitude(
            value=Decimal("9007199254740993"),
            kind=SignalMagnitudeKind.ABSOLUTE_CHANGE,
            unit_state=SignalMagnitudeUnitState.NOT_ESTABLISHED,
        )
        self.assertEqual(magnitude.to_json()["value"], "9007199254740993")

    def test_a_magnitude_is_not_bounded_to_the_unit_interval(self):
        """The column it replaces was `CHECK (value BETWEEN 0 AND 1)`."""
        magnitude = SignalMagnitude(
            value=Decimal("26"),
            kind=SignalMagnitudeKind.ABSOLUTE_CHANGE,
            unit_state=SignalMagnitudeUnitState.NOT_ESTABLISHED,
        )
        self.assertEqual(magnitude.to_json()["value"], "26")

    def test_a_ratio_is_always_dimensionless(self):
        with self.assertRaises(ValueError):
            SignalMagnitude(
                value=Decimal("1.47"),
                kind=SignalMagnitudeKind.RATIO,
                unit="mentions",
                unit_state=SignalMagnitudeUnitState.INHERITED,
            )

    def test_an_inherited_unit_state_must_carry_its_unit(self):
        with self.assertRaises(ValueError):
            SignalMagnitude(
                value=Decimal("26"),
                kind=SignalMagnitudeKind.ABSOLUTE_CHANGE,
                unit_state=SignalMagnitudeUnitState.INHERITED,
            )

    def test_a_unit_is_never_named_where_none_was_published(self):
        with self.assertRaises(ValueError):
            SignalMagnitude(
                value=Decimal("26"),
                kind=SignalMagnitudeKind.ABSOLUTE_CHANGE,
                unit="mentions",
                unit_state=SignalMagnitudeUnitState.NOT_ESTABLISHED,
            )

    def test_a_gdelt_magnitude_names_no_unit(self):
        serialised = canonical_json(lexical_signal().magnitude.to_json()).lower()
        for invented in ("mentions", "occurrences", "articles"):
            self.assertNotIn(invented, serialised)


# ============================================================= §12 confidence


class TestConfidence(unittest.TestCase):
    def test_out_of_range_is_rejected_not_clamped(self):
        for value in (-0.1, 1.4):
            with self.assertRaises(ValueError):
                lexical_signal(derivation_confidence=value)

    def test_the_bounds_are_inclusive(self):
        self.assertEqual(lexical_signal(derivation_confidence=0.0).derivation_confidence, 0.0)
        self.assertEqual(lexical_signal(derivation_confidence=1.0).derivation_confidence, 1.0)

    def test_confidence_is_independent_of_magnitude(self):
        """§38. A large change over two observations says nothing about whether
        two observations were enough."""
        big = numeric_signal(
            magnitude=SignalMagnitude(
                value=Decimal("100000000"),
                kind=SignalMagnitudeKind.ABSOLUTE_CHANGE,
                unit_state=SignalMagnitudeUnitState.NOT_ESTABLISHED,
            ),
            derivation_confidence=0.2,
            correlation_id="corr-3",
        )
        self.assertEqual(big.derivation_confidence, 0.2)


# ======================================================= §7, §8 the extractor


class TestDerivationIdentityAndParameters(unittest.TestCase):
    def test_a_deterministic_derivation_may_not_carry_a_model_version(self):
        with self.assertRaises(ValueError):
            SignalDerivation(
                extractor_id="x",
                extractor_version="1.0.0",
                kind=SignalDerivationKind.DETERMINISTIC,
                required_facts=frozenset(),
                model_version="claude-x",
            )

    def test_a_model_derived_derivation_must(self):
        with self.assertRaises(ValueError):
            SignalDerivation(
                extractor_id="x",
                extractor_version="1.0.0",
                kind=SignalDerivationKind.MODEL_DERIVED,
                required_facts=frozenset(),
            )

    def test_an_undeclared_parameter_is_refused(self):
        with self.assertRaises(SignalRefusedError) as caught:
            lexical_signal(
                derivation=SignalDerivation(
                    extractor_id="gdelt-lexical-contrast",
                    extractor_version="1.0.0",
                    kind=SignalDerivationKind.DETERMINISTIC,
                    required_facts=LEXICAL_DERIVATION.required_facts,
                    parameter_names=frozenset({"comparison", "minimum_observations"}),
                    parameters={"comparison": "ratio_to_first"},
                )
            )
        self.assertIs(caught.exception.refusal.reason, SignalRefusalReason.PARAMETERS_INCOMPLETE)

    def test_parameter_order_does_not_change_the_fingerprint(self):
        """§42. Deterministic parameter ordering."""
        forwards = SignalDerivation(
            extractor_id="x",
            extractor_version="1.0.0",
            kind=SignalDerivationKind.DETERMINISTIC,
            required_facts=frozenset(),
            parameter_names=frozenset({"a", "b"}),
            parameters={"a": 1, "b": Decimal("2.50")},
        )
        backwards = SignalDerivation(
            extractor_id="x",
            extractor_version="1.0.0",
            kind=SignalDerivationKind.DETERMINISTIC,
            required_facts=frozenset(),
            parameter_names=frozenset({"b", "a"}),
            parameters={"b": Decimal("2.5"), "a": 1},
        )
        self.assertEqual(forwards.parameter_fingerprint, backwards.parameter_fingerprint)

    def test_a_float_parameter_cannot_be_fingerprinted(self):
        derivation = SignalDerivation(
            extractor_id="x",
            extractor_version="1.0.0",
            kind=SignalDerivationKind.DETERMINISTIC,
            required_facts=frozenset(),
            parameter_names=frozenset({"threshold"}),
            parameters={"threshold": 0.1},
        )
        with self.assertRaises(ValueError):
            _ = derivation.parameter_fingerprint

    def test_an_unregistered_type_is_refused(self):
        with self.assertRaises(SignalRefusedError) as caught:
            lexical_signal(signal_type_id="lexical_attention_growth")
        self.assertIs(caught.exception.refusal.reason, SignalRefusalReason.UNSUPPORTED_SIGNAL_TYPE)

    def test_every_registered_type_is_justified_by_a_real_data_shape(self):
        """Until Mission 1.12.1 this asserted TWO types, and correctly.

        `lexical_frequency_change` joined them once H-32 closed: it is the first
        type whose window basis is ORDERED_PERIODS, and it could not have
        existed while ordering was unestablished.

        `procurement_value_contrast` joined in Mission 1.15.9, and it is the
        mirror image: the first type whose basis is NONE, and it exists BECAUSE
        H-37 is open -- a derivation over TED notices that needed an order could
        not have been written at all. Its data shape is the `procurement_notice`
        record kind Mission 1.15.8 added.

        `content_request_change` joined in Mission 1.19 under ADR-032, over the
        `content_request_count` record kind migration 0025 added. It is the
        second type whose basis is COMPARABLE_INSTANTS, and it could exist only
        because the platform documents its day bucket as UTC -- the fact GDELT's
        H-29 still lacks.

        `community_question_volume` joined in Mission 1.30 under ADR-034, over
        the `community_question` record kind Mission 1.18 added and nothing had
        derived from since. It is the first type that counts PUBLICATIONS rather
        than reading a measured value out of each input, which is why its family
        could not be `CONTENT_REQUEST_VOLUME`: a request is something a reader
        makes of a server, and a question is something a person publishes about
        being stuck.

        The rule the original assertion protected is unchanged: every type is
        justified by a data shape this repository holds, and each declares the
        family whose record kind it reads."""
        self.assertEqual(
            set(SIGNAL_TYPES),
            {
                "lexical_frequency_contrast",
                "lexical_frequency_change",
                "numeric_period_change",
                "procurement_value_contrast",
                "content_request_change",
                "community_question_volume",
            },
        )
        for spec in SIGNAL_TYPES.values():
            self.assertTrue(spec.summary.strip())
            self.assertIn(spec.family, set(SignalQuantityFamily))

    def test_no_extractor_exists(self):
        """Mission 1.11 §41. A registered type is vocabulary; this is the claim
        that code exists, and it is empty."""
        self.assertEqual(dict(SIGNAL_EXTRACTORS), {})


# ============================================================== §15 identity


class TestIdentity(unittest.TestCase):
    def test_the_same_derivation_converges(self):
        first, second = lexical_signal(), lexical_signal()
        self.assertEqual(first.derivation_fingerprint, second.derivation_fingerprint)
        self.assertEqual(first.id, second.id)

    def test_the_outputs_are_not_in_the_identity(self):
        """A changed magnitude under an unchanged identity is a REPORT, not a
        new row."""
        base = lexical_signal()
        other = lexical_signal(
            magnitude=SignalMagnitude(
                value=Decimal("2.00"),
                kind=SignalMagnitudeKind.RATIO,
                unit_state=SignalMagnitudeUnitState.DIMENSIONLESS,
            ),
            derivation_confidence=0.5,
        )
        self.assertEqual(base.derivation_fingerprint, other.derivation_fingerprint)

    def test_volatile_metadata_is_not_in_the_identity(self):
        later = lexical_signal(
            derived_at=DERIVED_AT + timedelta(days=3),
            expires_at=EXPIRES_AT + timedelta(days=3),
            correlation_id="a-different-run",
        )
        self.assertEqual(lexical_signal().derivation_fingerprint, later.derivation_fingerprint)

    def test_the_session_is_lineage_not_identity(self):
        """§39. Two sessions deriving the same thing converge on ONE signal;
        two rows would read as two independent findings."""
        other_session = lexical_signal(research_session_id="33333333-3333-4333-8333-333333333333")
        self.assertEqual(
            lexical_signal().derivation_fingerprint, other_session.derivation_fingerprint
        )
        self.assertEqual(other_session.research_session_id, "33333333-3333-4333-8333-333333333333")

    def test_the_workspace_is_in_the_identity(self):
        elsewhere = lexical_signal(workspace_id="44444444-4444-4444-8444-444444444444")
        self.assertNotEqual(
            lexical_signal().derivation_fingerprint, elsewhere.derivation_fingerprint
        )

    def test_a_different_extractor_version_is_a_different_signal(self):
        bumped = lexical_signal(
            derivation=SignalDerivation(
                extractor_id="gdelt-lexical-contrast",
                extractor_version="1.1.0",
                kind=SignalDerivationKind.DETERMINISTIC,
                required_facts=LEXICAL_DERIVATION.required_facts,
                parameter_names=LEXICAL_DERIVATION.parameter_names,
                parameters=dict(LEXICAL_DERIVATION.parameters),
            )
        )
        self.assertNotEqual(lexical_signal().derivation_fingerprint, bumped.derivation_fingerprint)

    def test_different_parameters_are_a_different_signal(self):
        other = lexical_signal(
            derivation=SignalDerivation(
                extractor_id="gdelt-lexical-contrast",
                extractor_version="1.0.0",
                kind=SignalDerivationKind.DETERMINISTIC,
                required_facts=LEXICAL_DERIVATION.required_facts,
                parameter_names=frozenset({"comparison"}),
                parameters={"comparison": "difference"},
            )
        )
        self.assertNotEqual(lexical_signal().derivation_fingerprint, other.derivation_fingerprint)

    def test_input_order_is_part_of_the_derivation(self):
        reversed_inputs = lexical_signal(
            observations=[
                gdelt_observation("weather", record_id="n-2"),
                gdelt_observation("climate", record_id="n-1"),
            ],
            scope=SignalScope(
                source_ids=("gdelt",),
                terms=("weather", "climate"),
                source_language_labels=("ENGLISH",),
                source_language_scheme="cld2-language-name",
            ),
        )
        self.assertNotEqual(
            lexical_signal().derivation_fingerprint, reversed_inputs.derivation_fingerprint
        )

    def test_closing_h32_did_not_move_an_existing_signal(self):
        """§16. A same-bucket contrast is unchanged: the certification grants a
        fact this derivation never required, and `resource_id` is lineage rather
        than identity."""
        draft = lexical_signal()
        self.assertEqual(
            draft.derivation_fingerprint,
            canonical_fingerprint(
                {
                    "extractor": {"id": "gdelt-lexical-contrast", "version": "1.0.0"},
                    "inputs": [
                        {
                            "normalized_record_id": "n-1",
                            "observation_key": draft.inputs[0].observation.observation_key,
                        },
                        {
                            "normalized_record_id": "n-2",
                            "observation_key": draft.inputs[1].observation.observation_key,
                        },
                    ],
                    "parameter_fingerprint": draft.parameter_fingerprint,
                    "quantity_family": "LEXICAL_FREQUENCY",
                    "schema": {"id": "sros.signal", "version": 1},
                    "signal_type": {"id": "lexical_frequency_contrast", "registry": "signal_type"},
                    "window": {
                        "basis": "SAME_PERIOD_LABEL",
                        "period_labels": ["20260830091500", "20260830091500"],
                        "resolution": "INTERVAL",
                    },
                    "workspace_id": WORKSPACE,
                }
            ),
        )

    def test_serialisation_is_stable_across_runs(self):
        payloads = {canonical_json(lexical_signal().lineage_json()) for _ in range(3)}
        self.assertEqual(len(payloads), 1)


# ================================================================== §13 scope


class TestScope(unittest.TestCase):
    def test_a_lexical_signal_carries_no_geography(self):
        serialised = lexical_signal().scope.to_json()
        self.assertNotIn("geography_codes", serialised)
        self.assertNotIn("metric_ids", serialised)

    def test_a_lexical_signal_may_not_be_given_one(self):
        with self.assertRaises(ValueError) as caught:
            lexical_signal(
                scope=SignalScope(
                    source_ids=("gdelt",),
                    terms=("climate", "weather"),
                    geography_codes=("US",),
                )
            )
        self.assertIn("language is not a place", str(caught.exception))

    def test_a_numeric_signal_states_its_metric(self):
        with self.assertRaises(ValueError):
            numeric_signal(scope=SignalScope(source_ids=("world-bank",)))

    def test_a_canonical_tag_needs_the_fact_behind_it(self):
        """H-30. A tag cannot appear because the label looked like one."""
        with self.assertRaises(ValueError) as caught:
            lexical_signal(
                scope=SignalScope(
                    source_ids=("gdelt",),
                    terms=("climate", "weather"),
                    source_language_labels=("ENGLISH",),
                    source_language_scheme="cld2-language-name",
                    canonical_language_tags=("en",),
                )
            )
        self.assertIn("H-30", str(caught.exception))

    def test_a_language_label_needs_its_vocabulary(self):
        with self.assertRaises(ValueError):
            SignalScope(source_ids=("gdelt",), source_language_labels=("ENGLISH",))

    def test_scope_sources_must_match_the_lineage(self):
        with self.assertRaises(ValueError) as caught:
            lexical_signal(
                scope=SignalScope(
                    source_ids=("gdelt", "world-bank"),
                    terms=("climate", "weather"),
                    source_language_labels=("ENGLISH",),
                    source_language_scheme="cld2-language-name",
                )
            )
        self.assertIn("derived from the lineage", str(caught.exception))

    def test_no_market_topic_or_category_dimension_exists(self):
        """§50. A lexical term does not become a topic by being in a signal."""
        serialised = canonical_json(lexical_signal().scope.to_json()).lower()
        for interpretation in ("topic", "category", "market", "motivation", "sentiment"):
            self.assertNotIn(interpretation, serialised)


# ========================================================= structural guards


class TestWorkspaceAndRetention(unittest.TestCase):
    def test_a_workspace_is_never_defaulted(self):
        with self.assertRaises(ValueError):
            lexical_signal(workspace_id="   ")

    def test_an_expiry_in_the_past_is_a_policy_never_applied(self):
        with self.assertRaises(ValueError):
            lexical_signal(expires_at=DERIVED_AT - timedelta(days=1))

    def test_naive_timestamps_are_refused(self):
        with self.assertRaises(ValueError):
            lexical_signal(derived_at=datetime(2026, 8, 30, 12))  # noqa: DTZ001

    def test_a_family_mismatch_refuses_the_derivation(self):
        with self.assertRaises(SignalRefusedError) as caught:
            lexical_signal(
                observations=[
                    world_bank_observation("2018", record_id="n-10"),
                    world_bank_observation("2019", record_id="n-11"),
                ]
            )
        self.assertIs(
            caught.exception.refusal.reason,
            SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS,
        )

    def test_a_window_must_describe_its_inputs(self):
        with self.assertRaises(ValueError):
            lexical_signal(
                window=SignalWindow(
                    basis=SignalTemporalBasis.SAME_PERIOD_LABEL,
                    period_labels=("20260830091500",),
                    resolution=NormalizedPeriodType.INTERVAL,
                    observation_count=3,
                )
            )


class TestTaxonomyBoundaries(unittest.TestCase):
    """§4, §5, §6. The Signal family is not the demand family."""

    def test_the_quantity_family_is_not_a_demand_family(self):
        """Three now, and the property is unchanged and is the whole point.

        `TRANSACTION_VALUE` was added in Mission 1.15.9 under ADR-029, because
        the `procurement_notice` record kind mapped to neither existing family
        and `MEASURED_SERIES` could not be widened without making `metric`
        optional for every World Bank signal ever written.

        **It is still not a demand family.** A public body paying for cleaning
        services is a transaction that happened; whether it evidences demand
        anybody could sell into is an inference this axis does not make, and
        Ontology V2 §3.6 is not amended.

        `CONTENT_REQUEST_VOLUME` was added in Mission 1.19 under ADR-032, and it
        is the one most easily mistaken for a demand family: a page request
        LOOKS like somebody wanting something. It is a count of HTTP responses.
        The names refused here are the evidence that the distinction was made
        deliberately rather than by luck.

        `COMMUNITY_QUESTION_VOLUME` was added in Mission 1.30 under ADR-034, and
        it is the one that comes CLOSEST to a demand family without being one: a
        person publishing that they are stuck looks a great deal like a need.
        It is a count of published questions. It says nothing about how many
        PEOPLE -- author identity is never acquired -- nothing about whether two
        questions share a problem, which is the relation Mission 1.27 parked,
        and nothing about anybody wanting to buy anything. `PAIN` is refused
        here for exactly the reason it is tempting.
        """
        values = {member.value for member in SignalQuantityFamily}
        self.assertEqual(
            values,
            {
                "LEXICAL_FREQUENCY",
                "MEASURED_SERIES",
                "TRANSACTION_VALUE",
                "CONTENT_REQUEST_VOLUME",
                "COMMUNITY_QUESTION_VOLUME",
            },
        )
        self.assertFalse(values & {"PAIN", "DESIRE", "BEHAVIORAL", "MARKET"})
        self.assertNotIn("WILLINGNESS_TO_PAY", values)
        # Every name that would have put the interpretation in the vocabulary.
        for tempting in ("CONTENT_VIEWS", "ATTENTION", "CONTENT_POPULARITY", "ADOPTION"):
            self.assertNotIn(tempting, values)
        # Mission 1.30. The names that would have put the interpretation in THIS
        # family's vocabulary, and each was available and rejected.
        for tempting in (
            "PROBLEM_VOLUME",
            "PROBLEM_FREQUENCY",
            "USER_PAIN_VOLUME",
            "COMMUNITY_DEMAND",
            "UNMET_NEED_VOLUME",
        ):
            self.assertNotIn(tempting, values)

    def test_a_signal_carries_no_demand_family_and_no_motivation(self):
        draft = lexical_signal()
        serialised = canonical_json(
            {
                "scope": draft.scope.to_json(),
                "window": draft.window.to_json(),
                "magnitude": draft.magnitude.to_json(),
                "lineage": draft.lineage_json(),
                "parameters": draft.derivation.parameters_json(),
            }
        ).upper()
        for interpretation in ("PAIN", "DESIRE", "BEHAVIORAL", "CURIOSITY", "ATTENTION"):
            self.assertNotIn(interpretation, serialised)

    def test_each_type_declares_the_family_its_records_belong_to(self):
        self.assertIs(
            SIGNAL_TYPES["lexical_frequency_contrast"].family,
            SignalQuantityFamily.LEXICAL_FREQUENCY,
        )
        self.assertIs(
            SIGNAL_TYPES["numeric_period_change"].family,
            SignalQuantityFamily.MEASURED_SERIES,
        )


class TestNoAggregationOrEvidenceVocabulary(unittest.TestCase):
    """§17, §18, §22. A Signal is not Evidence and does not judge independence."""

    def test_a_signal_carries_no_evidence_field(self):
        draft = lexical_signal()
        for forbidden in (
            "independence_state",
            "independence_group_id",
            "reliability",
            "relevance",
            "directness",
            "claim_id",
            "evidence_level",
        ):
            self.assertFalse(hasattr(draft, forbidden), forbidden)

    def test_the_lineage_carries_sources_but_no_independence_judgement(self):
        """The facts, so aggregation can decide later. Never the decision."""
        lineage = lexical_signal().lineage_json()
        self.assertEqual({row["source_id"] for row in lineage}, {"gdelt"})
        for row in lineage:
            self.assertNotIn("independence_state", row)
            self.assertNotIn("reliability", row)


if __name__ == "__main__":
    unittest.main()
