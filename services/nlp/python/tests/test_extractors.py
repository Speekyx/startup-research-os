"""The two deterministic extractors, over synthetic observations only.

Mission 1.11.1 §35, §36. **No network, no database, no real record.** Every
fixture below is invented; where one is shaped after a real observation the
docstring says so and says it is a shape rather than a capture.

Refusal tests assert the **reason**, never that "something was refused" --
Mission 1.11 found a probe where ten cases passed for the wrong reason, and
seven refusal codes share one exception type here.
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sros_contracts import (
    NormalizationQualityReason as Reason,
)
from sros_contracts import (
    NormalizedRecordQuality,
    SignalDirection,
    SignalMagnitudeKind,
    SignalMagnitudeUnitState,
    SignalRefusalReason,
    SignalRequiredFact,
    SignalTemporalBasis,
)
from sros_nlp import (
    CandidateGroup,
    DerivationRequest,
    LexicalFrequencyContrastExtractor,
    NormalizedObservation,
    NumericPeriodChangeExtractor,
    select_extractor,
)
from sros_signal_model import SignalRefusedError, withheld_facts

WORKSPACE = "11111111-1111-4111-8111-111111111111"
DERIVED_AT = datetime(2026, 8, 30, 12, tzinfo=UTC)
REQUEST = DerivationRequest(
    workspace_id=WORKSPACE,
    correlation_id="corr-1",
    derived_at=DERIVED_AT,
    expires_at=DERIVED_AT + timedelta(days=365),
    research_session_id=None,
)

NUMERIC = NumericPeriodChangeExtractor()
LEXICAL = LexicalFrequencyContrastExtractor()


# --------------------------------------------------------------- fixtures
#
# SYNTHETIC. The World Bank shape follows the six real records (SP.POP.TOTL,
# DEU/FRA, 2018-2020) and the GDELT shape follows the two real ones (one bucket,
# ENGLISH, two 1gram terms), because those are the shapes the extractors must
# support. Every id, hash and figure below is invented.


def numeric_observation(
    year: str,
    value: str | None,
    *,
    record_id: str,
    geography: str = "DEU",
    canonical: str | None = "DE",
    metric: str = "SP.POP.TOTL",
    unit: str | None = None,
    unit_state: str = "NOT_PUBLISHED",
    quality: NormalizedRecordQuality = NormalizedRecordQuality.VALID,
    reasons: frozenset[Reason] = frozenset(),
    period_type: str = "YEAR",
) -> NormalizedObservation:
    start = f"{year}-01-01T00:00:00+00:00"
    end = f"{int(year) + 1}-01-01T00:00:00+00:00"
    geo: dict[str, object] = {
        "kind": "COUNTRY" if canonical else "UNKNOWN",
        "source_code": geography,
        "source_name": geography,
        "canonical_scheme": "ISO-3166-1-ALPHA-2" if canonical else None,
        "canonical_code": canonical,
    }
    return NormalizedObservation(
        normalized_record_id=record_id,
        raw_record_id=f"raw-{record_id}",
        source_id="world-bank",
        observation_key=f"world-bank|indicator/{metric}|{geography}|{year}",
        record_kind_id="numeric_observation",
        quality=quality,
        quality_reasons=reasons,
        payload={
            "record_kind": "numeric_observation",
            "metric": {"id": metric, "name": None, "scheme": "world-bank-indicator"},
            "geography": geo,
            "series": {
                "dataset": "indicators",
                "frequency": "ANNUAL",
                "resource_id": f"indicator/{metric}",
                "source_last_updated": "2026-07-13",
            },
            "period": {
                "type": period_type,
                "label": year,
                "start": start,
                "end": end,
                "end_inclusive": False,
            },
            "observation": {
                "value": value,
                "value_state": "REPORTED" if value is not None else "NOT_REPORTED",
                "unit": unit,
                "unit_state": unit_state,
                "decimals": 0,
            },
        },
    )


def lexical_observation(
    term: str,
    count: str | None,
    *,
    record_id: str,
    bucket: str = "20260830091500",
    language: str = "ENGLISH",
    scheme: str = "cld2-language-name",
    gram_size: int = 1,
    resource: str = "web-ngrams/1gram",
    source_id: str = "gdelt",
    quality: NormalizedRecordQuality = NormalizedRecordQuality.PARTIAL,
    reasons: frozenset[Reason] | None = None,
) -> NormalizedObservation:
    if reasons is None:
        reasons = frozenset({Reason.PERIOD_TIMEZONE_NOT_ESTABLISHED, Reason.LANGUAGE_NOT_MAPPED})
    return NormalizedObservation(
        normalized_record_id=record_id,
        raw_record_id=f"raw-{record_id}",
        source_id=source_id,
        observation_key=f"{source_id}|{resource}|{bucket}|{language}|{term}",
        record_kind_id="lexical_frequency_observation",
        quality=quality,
        quality_reasons=reasons,
        payload={
            "record_kind": "lexical_frequency_observation",
            "term": {"text": term, "gram_size": gram_size, "scheme": "gdelt-web-ngram"},
            "language": {
                "source_label": language,
                "source_scheme": scheme,
                "mapping_state": "NOT_ESTABLISHED",
                "canonical_tag": None,
                "canonical_scheme": None,
            },
            "series": {
                "dataset": resource.replace("/", "-"),
                "resource_id": resource,
                "source_last_updated": None,
            },
            "period": {
                "type": "INTERVAL",
                "label": bucket,
                "start": "2026-08-30T09:15:00",
                "end": "2026-08-30T09:30:00",
                "end_inclusive": False,
                "timezone_state": "NOT_ESTABLISHED",
            },
            "observation": {
                "value": count,
                "value_state": "REPORTED" if count is not None else "NOT_REPORTED",
                "unit": None,
                "unit_state": "NOT_PUBLISHED",
                "decimals": None,
            },
        },
    )


def group_of(extractor, observations):
    keys = {extractor.group_key(o) for o in observations}
    return CandidateGroup(key=sorted(k or "" for k in keys)[0], observations=tuple(observations))


def derive(extractor, observations, parameters=None):
    derivation = extractor.resolve(parameters or {})
    return extractor.derive(group_of(extractor, observations), derivation, REQUEST)


# ================================================== numeric_period_change (§35)


class TestNumericArithmetic(unittest.TestCase):
    def test_an_increase(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "82905782", record_id="a"),
                numeric_observation("2019", "83092962", record_id="b"),
            ],
        )
        (draft,) = outcome.drafts
        self.assertEqual(draft.magnitude.value, Decimal("187180"))
        self.assertIs(draft.direction, SignalDirection.INCREASING)
        self.assertIs(draft.magnitude.kind, SignalMagnitudeKind.ABSOLUTE_CHANGE)

    def test_a_decrease(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "100", record_id="a"),
                numeric_observation("2019", "95", record_id="b"),
            ],
        )
        (draft,) = outcome.drafts
        self.assertEqual(draft.magnitude.value, Decimal("-5"))
        self.assertIs(draft.direction, SignalDirection.DECREASING)

    def test_unchanged(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "100", record_id="a"),
                numeric_observation("2019", "100", record_id="b"),
            ],
        )
        (draft,) = outcome.drafts
        self.assertEqual(draft.magnitude.value, Decimal("0"))
        self.assertIs(draft.direction, SignalDirection.UNCHANGED)

    def test_a_zero_measurement_is_a_measurement(self):
        """Zero is a value the source published. Absence is `NOT_REPORTED` and
        is a different fact -- the normalization layer's rule, one level up."""
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "0", record_id="a"),
                numeric_observation("2019", "4", record_id="b"),
            ],
        )
        (draft,) = outcome.drafts
        self.assertEqual(draft.magnitude.value, Decimal("4"))

    def test_negative_values(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "-3", record_id="a", metric="NY.GDP.MKTP.KD.ZG"),
                numeric_observation("2019", "-8", record_id="b", metric="NY.GDP.MKTP.KD.ZG"),
            ],
        )
        (draft,) = outcome.drafts
        self.assertEqual(draft.magnitude.value, Decimal("-5"))
        self.assertIs(draft.direction, SignalDirection.DECREASING)

    def test_exactness_beyond_float_range(self):
        """A float round-trip returns ...92. The arithmetic is exact on both
        sides of the subtraction because nothing here is ever a float."""
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "9007199254740993", record_id="a"),
                numeric_observation("2019", "9007199254740995", record_id="b"),
            ],
        )
        (draft,) = outcome.drafts
        self.assertEqual(draft.magnitude.value, Decimal("2"))
        self.assertEqual(draft.magnitude.to_json()["value"], "2")

    def test_a_published_unit_is_inherited(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "10", record_id="a", unit="kg", unit_state="PUBLISHED"),
                numeric_observation("2019", "12", record_id="b", unit="kg", unit_state="PUBLISHED"),
            ],
        )
        (draft,) = outcome.drafts
        self.assertIs(draft.magnitude.unit_state, SignalMagnitudeUnitState.INHERITED)
        self.assertEqual(draft.magnitude.unit, "kg")

    def test_an_unpublished_unit_is_not_invented(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "10", record_id="a"),
                numeric_observation("2019", "12", record_id="b"),
            ],
        )
        (draft,) = outcome.drafts
        self.assertIs(draft.magnitude.unit_state, SignalMagnitudeUnitState.NOT_ESTABLISHED)
        self.assertIsNone(draft.magnitude.unit)


class TestNumericPairing(unittest.TestCase):
    def test_adjacent_pairs_only(self):
        """2018->2019 and 2019->2020. NOT 2018->2020, which is a different
        question and would need a strategy that says so."""
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "1", record_id="a"),
                numeric_observation("2019", "2", record_id="b"),
                numeric_observation("2020", "4", record_id="c"),
            ],
        )
        self.assertEqual(len(outcome.drafts), 2)
        self.assertEqual(
            [d.window.period_labels for d in outcome.drafts],
            [("2018", "2019"), ("2019", "2020")],
        )

    def test_reverse_database_order_is_the_same_signal(self):
        """§27. Order comes from the canonical period start, never from the row
        order a query happened to return."""
        forwards = derive(
            NUMERIC,
            [
                numeric_observation("2018", "1", record_id="a"),
                numeric_observation("2019", "2", record_id="b"),
            ],
        )
        backwards = derive(
            NUMERIC,
            [
                numeric_observation("2019", "2", record_id="b"),
                numeric_observation("2018", "1", record_id="a"),
            ],
        )
        self.assertEqual(
            forwards.drafts[0].derivation_fingerprint,
            backwards.drafts[0].derivation_fingerprint,
        )
        self.assertEqual(forwards.drafts[0].magnitude.value, backwards.drafts[0].magnitude.value)

    def test_the_temporal_basis_is_a_shared_timeline(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "1", record_id="a"),
                numeric_observation("2019", "2", record_id="b"),
            ],
        )
        draft = outcome.drafts[0]
        self.assertIs(draft.window.basis, SignalTemporalBasis.COMPARABLE_INSTANTS)
        self.assertIsNotNone(draft.observed_at)

    def test_the_parameter_fingerprint_is_stable(self):
        first = NUMERIC.resolve({}).parameter_fingerprint
        second = NUMERIC.resolve({"pairing_strategy": "adjacent_periods"}).parameter_fingerprint
        self.assertEqual(first, second)

    def test_an_unimplemented_strategy_is_refused(self):
        with self.assertRaises(SignalRefusedError) as caught:
            NUMERIC.resolve({"pairing_strategy": "all_pairs"})
        self.assertIs(caught.exception.refusal.reason, SignalRefusalReason.PARAMETERS_INCOMPLETE)

    def test_an_ignored_parameter_is_refused(self):
        with self.assertRaises(SignalRefusedError) as caught:
            NUMERIC.resolve({"smoothing": "none"})
        self.assertIs(caught.exception.refusal.reason, SignalRefusalReason.PARAMETERS_INCOMPLETE)


class TestNumericCompatibility(unittest.TestCase):
    def test_two_geographies_are_not_one_series(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "1", record_id="a", geography="DEU", canonical="DE"),
                numeric_observation("2019", "2", record_id="b", geography="FRA", canonical="FR"),
            ],
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_two_metrics_are_not_one_series(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "1", record_id="a", metric="SP.POP.TOTL"),
                numeric_observation("2019", "2", record_id="b", metric="NY.GDP.MKTP.CD"),
            ],
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_two_units_are_not_one_series(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "1", record_id="a", unit="kg", unit_state="PUBLISHED"),
                numeric_observation("2019", "2", record_id="b", unit="t", unit_state="PUBLISHED"),
            ],
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_two_resolutions_are_not_comparable(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "1", record_id="a"),
                numeric_observation("2019", "2", record_id="b", period_type="QUARTER"),
            ],
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_a_lexical_record_is_the_wrong_kind(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "1", record_id="a"),
                lexical_observation("climate", "5", record_id="x"),
            ],
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS)

    def test_one_observation_is_not_a_signal(self):
        outcome = derive(NUMERIC, [numeric_observation("2018", "1", record_id="a")])
        self.assertEqual(outcome.drafts, ())
        self.assertIs(
            outcome.refusals[0].reason, SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS
        )

    def test_two_rows_of_one_observation_are_refused(self):
        """D-08. Two normalizer versions of one observation are two rows and one
        observation; counting both would manufacture a change out of nothing."""
        first = numeric_observation("2018", "1", record_id="a")
        second = numeric_observation("2018", "1", record_id="a-v2")
        outcome = derive(NUMERIC, [first, second])
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE)


class TestNumericQuality(unittest.TestCase):
    """§12. Generic required-fact evaluation, never `if quality != VALID`."""

    def test_an_invalid_input_never_contributes(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "1", record_id="a"),
                numeric_observation(
                    "2019",
                    "2",
                    record_id="b",
                    quality=NormalizedRecordQuality.INVALID,
                    reasons=frozenset({Reason.METRIC_MISSING}),
                ),
            ],
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(
            outcome.refusals[0].reason, SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS
        )

    def test_partial_missing_an_irrelevant_fact_still_contributes(self):
        """`LANGUAGE_NOT_MAPPED` withholds a fact this derivation never asks
        for. PARTIAL is not a verdict on usability."""
        outcome = derive(
            NUMERIC,
            [
                numeric_observation(
                    "2018",
                    "1",
                    record_id="a",
                    quality=NormalizedRecordQuality.PARTIAL,
                    reasons=frozenset({Reason.LANGUAGE_NOT_MAPPED}),
                ),
                numeric_observation("2019", "2", record_id="b"),
            ],
        )
        self.assertEqual(len(outcome.drafts), 1)

    def test_partial_missing_a_required_fact_is_refused(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation("2018", "1", record_id="a"),
                numeric_observation(
                    "2019",
                    None,
                    record_id="b",
                    quality=NormalizedRecordQuality.PARTIAL,
                    reasons=frozenset({Reason.VALUE_NOT_REPORTED}),
                ),
            ],
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(
            outcome.refusals[0].reason, SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS
        )

    def test_an_unclassified_geography_is_refused(self):
        outcome = derive(
            NUMERIC,
            [
                numeric_observation(
                    "2018",
                    "1",
                    record_id="a",
                    canonical=None,
                    quality=NormalizedRecordQuality.PARTIAL,
                    reasons=frozenset({Reason.GEOGRAPHY_NOT_CLASSIFIED}),
                ),
                numeric_observation(
                    "2019",
                    "2",
                    record_id="b",
                    canonical=None,
                    quality=NormalizedRecordQuality.PARTIAL,
                    reasons=frozenset({Reason.GEOGRAPHY_NOT_CLASSIFIED}),
                ),
            ],
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(
            outcome.refusals[0].reason, SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS
        )


# ============================================== lexical_frequency_contrast (§36)


class TestLexicalContrast(unittest.TestCase):
    def test_a_same_bucket_contrast(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "55", record_id="x"),
                lexical_observation("weather", "36", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        )
        (draft,) = outcome.drafts
        self.assertEqual(draft.magnitude.value, Decimal("19"))
        self.assertIs(draft.magnitude.kind, SignalMagnitudeKind.ABSOLUTE_DIFFERENCE)
        self.assertIs(draft.direction, SignalDirection.NOT_APPLICABLE)
        self.assertIs(draft.window.basis, SignalTemporalBasis.SAME_PERIOD_LABEL)
        self.assertIsNone(draft.observed_at)
        self.assertEqual(draft.derivation_confidence, 1.0)

    def test_equal_counts(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "40", record_id="x"),
                lexical_observation("weather", "40", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        )
        self.assertEqual(outcome.drafts[0].magnitude.value, Decimal("0"))
        self.assertIs(outcome.drafts[0].direction, SignalDirection.NOT_APPLICABLE)

    def test_the_second_term_larger_gives_a_negative_difference(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "10", record_id="x"),
                lexical_observation("weather", "40", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        )
        self.assertEqual(outcome.drafts[0].magnitude.value, Decimal("-30"))
        self.assertIs(outcome.drafts[0].direction, SignalDirection.NOT_APPLICABLE)

    def test_a_zero_frequency_is_a_measurement(self):
        """No denominator anywhere: the magnitude is a difference, so there is
        no zero-denominator case to handle."""
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "5", record_id="x"),
                lexical_observation("weather", "0", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        )
        self.assertEqual(outcome.drafts[0].magnitude.value, Decimal("5"))

    def test_terms_are_preserved_verbatim(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("  spaced  ", "5", record_id="x"),
                lexical_observation("climat\\e|d", "3", record_id="y"),
            ],
            {"terms": ["  spaced  ", "climat\\e|d"]},
        )
        self.assertEqual(outcome.drafts[0].scope.terms, ("  spaced  ", "climat\\e|d"))

    def test_unicode_terms(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("климат", "7", record_id="x"),
                lexical_observation("気候", "2", record_id="y"),
            ],
            {"terms": ["климат", "気候"]},
        )
        self.assertEqual(len(outcome.drafts), 1)

    def test_reverse_database_order_is_the_same_signal(self):
        forwards = derive(
            LEXICAL,
            [
                lexical_observation("climate", "55", record_id="x"),
                lexical_observation("weather", "36", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        )
        backwards = derive(
            LEXICAL,
            [
                lexical_observation("weather", "36", record_id="y"),
                lexical_observation("climate", "55", record_id="x"),
            ],
            {"terms": ["weather", "climate"]},
        )
        self.assertEqual(
            forwards.drafts[0].derivation_fingerprint,
            backwards.drafts[0].derivation_fingerprint,
        )
        self.assertEqual(forwards.drafts[0].magnitude.value, backwards.drafts[0].magnitude.value)


class TestLexicalCompatibility(unittest.TestCase):
    def test_two_buckets_are_refused(self):
        """H-32. Two labels that look ordered are still not ordered."""
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "10", record_id="x", bucket="20260830091500"),
                lexical_observation("climate", "40", record_id="y", bucket="20260830093000"),
            ],
            {"terms": ["climate", "weather"]},
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_two_source_language_labels_are_refused(self):
        """H-30. `ENGLISH` and `FRENCH` are different labels, and nothing here
        knows what either maps to."""
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "10", record_id="x", language="ENGLISH"),
                lexical_observation("climat", "8", record_id="y", language="FRENCH"),
            ],
            {"terms": ["climate", "climat"]},
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_one_gram_and_two_gram_are_refused(self):
        """§19. A unigram count and a bigram count are counts of different kinds
        of thing."""
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "10", record_id="x", gram_size=1),
                lexical_observation(
                    "climate change",
                    "4",
                    record_id="y",
                    gram_size=2,
                    resource="web-ngrams/2gram",
                ),
            ],
            {"terms": ["climate", "climate change"]},
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_two_sources_are_refused(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "10", record_id="x"),
                lexical_observation("weather", "4", record_id="y", source_id="world-bank"),
            ],
            {"terms": ["climate", "weather"]},
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_a_numeric_record_is_the_wrong_kind(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "10", record_id="x"),
                numeric_observation("2018", "1", record_id="a"),
            ],
            {"terms": ["climate", "weather"]},
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS)

    def test_a_missing_term_is_refused(self):
        outcome = derive(
            LEXICAL,
            [lexical_observation("climate", "10", record_id="x")],
            {"terms": ["climate", "weather"]},
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(
            outcome.refusals[0].reason, SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS
        )

    def test_two_rows_for_one_term_are_refused(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "10", record_id="x"),
                lexical_observation("climate", "10", record_id="x-v2"),
                lexical_observation("weather", "4", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE)

    def test_an_invalid_input_never_contributes(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "10", record_id="x"),
                lexical_observation(
                    "weather",
                    "4",
                    record_id="y",
                    quality=NormalizedRecordQuality.INVALID,
                    reasons=frozenset({Reason.PERIOD_NOT_SUPPORTED}),
                ),
            ],
            {"terms": ["climate", "weather"]},
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(
            outcome.refusals[0].reason, SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS
        )


class TestLexicalParameters(unittest.TestCase):
    def test_terms_are_required(self):
        """§9 of the runtime doc. A sweep over a bucket with 223,342 terms is
        quadratic, and any bound on it would be a threshold nobody reviewed."""
        with self.assertRaises(SignalRefusedError) as caught:
            LEXICAL.resolve({})
        self.assertIs(caught.exception.refusal.reason, SignalRefusalReason.PARAMETERS_INCOMPLETE)

    def test_exactly_two_terms(self):
        for terms in (["climate"], ["a", "b", "c"], ["climate", "climate"]):
            with self.assertRaises(SignalRefusedError) as caught:
                LEXICAL.resolve({"terms": terms})
            self.assertIs(
                caught.exception.refusal.reason, SignalRefusalReason.PARAMETERS_INCOMPLETE
            )

    def test_a_string_is_not_a_term_list(self):
        with self.assertRaises(SignalRefusedError):
            LEXICAL.resolve({"terms": "climate"})

    def test_term_order_does_not_change_the_fingerprint(self):
        self.assertEqual(
            LEXICAL.resolve({"terms": ["climate", "weather"]}).parameter_fingerprint,
            LEXICAL.resolve({"terms": ["weather", "climate"]}).parameter_fingerprint,
        )


class TestLexicalQualityAndAbsences(unittest.TestCase):
    """§22. The first production proof that PARTIAL does not mean unusable."""

    def test_both_partial_inputs_contribute(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "55", record_id="x"),
                lexical_observation("weather", "36", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        )
        draft = outcome.drafts[0]
        self.assertEqual(len(draft.contributed), 2)
        self.assertTrue(
            all(a.observation.quality is NormalizedRecordQuality.PARTIAL for a in draft.contributed)
        )

    def test_no_canonical_language_is_invented(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "55", record_id="x"),
                lexical_observation("weather", "36", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        )
        scope = outcome.drafts[0].scope
        self.assertEqual(scope.canonical_language_tags, ())
        self.assertEqual(scope.source_language_labels, ("ENGLISH",))
        self.assertEqual(scope.source_language_scheme, "cld2-language-name")

    def test_no_geography_and_no_timezone(self):
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "55", record_id="x"),
                lexical_observation("weather", "36", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        )
        draft = outcome.drafts[0]
        self.assertNotIn("geography_codes", draft.scope.to_json())
        self.assertNotIn("start", draft.window.to_json())
        self.assertIsNone(draft.observed_at)

    def test_no_interpretation_reaches_the_payload(self):
        from sros_signal_model import canonical_json

        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "55", record_id="x"),
                lexical_observation("weather", "36", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        )
        draft = outcome.drafts[0]
        serialised = canonical_json(
            {
                "scope": draft.scope.to_json(),
                "window": draft.window.to_json(),
                "magnitude": draft.magnitude.to_json(),
                "parameters": draft.derivation.parameters_json(),
            }
        ).lower()
        for interpretation in ("attention", "demand", "trend", "topic", "sentiment", "growth"):
            self.assertNotIn(interpretation, serialised)


class TestTemporalOrderCertification(unittest.TestCase):
    """Mission 1.12 §19. H-32 closed; nothing about the extractors changed."""

    def test_a_real_shaped_gdelt_observation_names_its_resource(self):
        """The certification is scoped to a publication STREAM, so an
        observation that could not say which resource it came from would claim
        nothing."""
        observation = lexical_observation("climate", "55", record_id="x")
        self.assertEqual(observation.resource_id, "web-ngrams/1gram")
        self.assertEqual(observation.to_input().resource_id, "web-ngrams/1gram")

    def test_the_certified_stream_now_supplies_source_relative_order(self):
        observation = lexical_observation("climate", "55", record_id="x")
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

    def test_a_comparable_instant_is_still_withheld(self):
        """H-29 is open and closing H-32 did not touch it."""
        observation = lexical_observation("climate", "55", record_id="x")
        self.assertEqual(
            withheld_facts(
                frozenset({SignalRequiredFact.COMPARABLE_INSTANT}),
                record_kind_id=observation.record_kind_id,
                quality_reasons=observation.quality_reasons,
                source_id=observation.source_id,
                resource_id=observation.resource_id,
            ),
            frozenset({SignalRequiredFact.COMPARABLE_INSTANT}),
        )

    def test_the_lexical_extractor_still_requires_no_ordering(self):
        """§17. No extractor was written this mission. The contrast requires the
        LABEL, not the order, so nothing it derives changed."""
        derivation = LEXICAL.resolve({"terms": ["climate", "weather"]})
        self.assertNotIn(SignalRequiredFact.SOURCE_RELATIVE_ORDER, derivation.required_facts)
        self.assertNotIn(SignalRequiredFact.COMPARABLE_INSTANT, derivation.required_facts)

    def test_two_buckets_are_still_refused(self):
        """§16, §17. Ordering being ESTABLISHED does not make the same-bucket
        extractor a sequential one. Its grouping key still carries the exact
        label, so two buckets never meet."""
        outcome = derive(
            LEXICAL,
            [
                lexical_observation("climate", "10", record_id="x", bucket="20260830091500"),
                lexical_observation("climate", "40", record_id="y", bucket="20260830093000"),
            ],
            {"terms": ["climate", "weather"]},
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_the_existing_signal_is_unmoved(self):
        """§16. The one real GDELT signal must not be reinterpreted: same
        magnitude, same basis, same direction, same fingerprint inputs."""
        draft = derive(
            LEXICAL,
            [
                lexical_observation("climate", "55", record_id="x"),
                lexical_observation("weather", "36", record_id="y"),
            ],
            {"terms": ["climate", "weather"]},
        ).drafts[0]
        self.assertEqual(draft.magnitude.value, Decimal("19"))
        self.assertIs(draft.window.basis, SignalTemporalBasis.SAME_PERIOD_LABEL)
        self.assertIs(draft.direction, SignalDirection.NOT_APPLICABLE)
        self.assertIsNone(draft.observed_at)


class TestRegistry(unittest.TestCase):
    def test_both_extractors_are_registered(self):
        self.assertIsNotNone(select_extractor("numeric-period-change"))
        self.assertIsNotNone(select_extractor("lexical-frequency-contrast"))

    def test_an_unknown_extractor_fails_closed(self):
        self.assertIsNone(select_extractor("trend-detector"))

    def test_versions(self):
        self.assertEqual(NUMERIC.extractor_version, "1.0.0")
        self.assertEqual(LEXICAL.extractor_version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
