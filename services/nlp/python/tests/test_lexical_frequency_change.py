"""`lexical-frequency-change@1.0.0`, over synthetic observations only.

Mission 1.12.1 §32. **No network, no database, no real record.** The GDELT shape
follows the two real observations (one bucket, `ENGLISH`, 1gram) because that is
the shape the extractor must read; every id and figure is invented.

The two rules this suite exists to hold are §10 and §11:

    a gap is never bridged      -- NON_CONTIGUOUS_SOURCE_BUCKETS
    an absent term is ABSENT    -- never a frequency of zero

Refusal tests assert the **reason**, never that something was refused.
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
    LexicalFrequencyChangeExtractor,
    NormalizedObservation,
    select_extractor,
)
from sros_nlp.extractors.lexical_frequency_change import MAX_SELECTED_TERMS
from sros_signal_model import SignalRefusedError, canonical_json

WORKSPACE = "11111111-1111-4111-8111-111111111111"
DERIVED_AT = datetime(2026, 8, 30, 12, tzinfo=UTC)
REQUEST = DerivationRequest(
    workspace_id=WORKSPACE,
    correlation_id="corr-1",
    derived_at=DERIVED_AT,
    expires_at=DERIVED_AT + timedelta(days=365),
    research_session_id=None,
)

CHANGE = LexicalFrequencyChangeExtractor()

BUCKET_A = "20260830091500"
BUCKET_B = "20260830093000"  # +15m, adjacent to A
BUCKET_C = "20260830094500"  # +15m, adjacent to B
BUCKET_D = "20260830100000"  # +15m, adjacent to C


def observation(
    term: str,
    count: str | None,
    bucket: str,
    *,
    record_id: str | None = None,
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
    record_id = record_id or f"{term}-{bucket}"
    start = datetime.strptime(bucket, "%Y%m%d%H%M%S")  # noqa: DTZ007 -- a naive label
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
                "start": start.isoformat(),
                "end": (start + timedelta(minutes=15)).isoformat(),
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


def derive(observations, terms=("climate",), **parameters):
    derivation = CHANGE.resolve({"terms": list(terms), **parameters})
    keys = {CHANGE.group_key(o) for o in observations}
    group = CandidateGroup(key=sorted(k or "" for k in keys)[0], observations=tuple(observations))
    return CHANGE.derive(group, derivation, REQUEST)


# ============================================================== arithmetic


class TestArithmetic(unittest.TestCase):
    def test_an_increase(self):
        outcome = derive(
            [
                observation("climate", "55", BUCKET_A),
                observation("climate", "81", BUCKET_B),
            ]
        )
        (draft,) = outcome.drafts
        self.assertEqual(draft.magnitude.value, Decimal("26"))
        self.assertIs(draft.direction, SignalDirection.INCREASING)

    def test_a_decrease(self):
        outcome = derive(
            [
                observation("climate", "81", BUCKET_A),
                observation("climate", "55", BUCKET_B),
            ]
        )
        (draft,) = outcome.drafts
        self.assertEqual(draft.magnitude.value, Decimal("-26"))
        self.assertIs(draft.direction, SignalDirection.DECREASING)

    def test_unchanged(self):
        outcome = derive(
            [
                observation("climate", "55", BUCKET_A),
                observation("climate", "55", BUCKET_B),
            ]
        )
        (draft,) = outcome.drafts
        self.assertEqual(draft.magnitude.value, Decimal("0"))
        self.assertIs(draft.direction, SignalDirection.UNCHANGED)

    def test_a_zero_frequency_is_a_measurement(self):
        """GDELT publishing 0 for a term in a bucket is the source saying "none
        in this window". That is a measurement, and it is subtracted normally."""
        outcome = derive(
            [
                observation("climate", "0", BUCKET_A),
                observation("climate", "7", BUCKET_B),
            ]
        )
        self.assertEqual(outcome.drafts[0].magnitude.value, Decimal("7"))

    def test_exactness_beyond_float_range(self):
        outcome = derive(
            [
                observation("climate", "9007199254740993", BUCKET_A),
                observation("climate", "9007199254740995", BUCKET_B),
            ]
        )
        self.assertEqual(outcome.drafts[0].magnitude.to_json()["value"], "2")

    def test_the_magnitude_kind_is_a_change_not_a_difference(self):
        """§15. The same-bucket contrast uses ABSOLUTE_DIFFERENCE because
        nothing changed. This IS a movement over ordered buckets."""
        outcome = derive(
            [
                observation("climate", "55", BUCKET_A),
                observation("climate", "81", BUCKET_B),
            ]
        )
        self.assertIs(outcome.drafts[0].magnitude.kind, SignalMagnitudeKind.ABSOLUTE_CHANGE)

    def test_no_unit_is_invented(self):
        outcome = derive(
            [
                observation("climate", "55", BUCKET_A),
                observation("climate", "81", BUCKET_B),
            ]
        )
        magnitude = outcome.drafts[0].magnitude
        self.assertIs(magnitude.unit_state, SignalMagnitudeUnitState.NOT_ESTABLISHED)
        self.assertIsNone(magnitude.unit)
        serialised = canonical_json(magnitude.to_json()).lower()
        for invented in ("mentions", "occurrences", "articles", "percent", "%"):
            self.assertNotIn(invented, serialised)


# ============================================== §10 adjacency and the gap policy


class TestAdjacency(unittest.TestCase):
    def test_exactly_one_bucket_apart_is_adjacent(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("climate", "20", BUCKET_B),
            ]
        )
        self.assertEqual(len(outcome.drafts), 1)
        self.assertEqual(outcome.drafts[0].window.period_labels, (BUCKET_A, BUCKET_B))

    def test_a_thirty_minute_gap_is_refused(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("climate", "20", BUCKET_C),
            ]
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.NON_CONTIGUOUS_SOURCE_BUCKETS)

    def test_a_forty_five_minute_gap_is_refused(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("climate", "20", BUCKET_D),
            ]
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.NON_CONTIGUOUS_SOURCE_BUCKETS)

    def test_a_missing_middle_observation_is_never_a_zero(self):
        """§11, the rule this suite exists for. A term absent from B does NOT
        make B a bucket where it occurred zero times, and A->C is not adjacent."""
        outcome = derive(
            [
                observation("climate", "55", BUCKET_A),
                observation("climate", "40", BUCKET_C),
            ]
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.NON_CONTIGUOUS_SOURCE_BUCKETS)
        self.assertIn("absent", outcome.refusals[0].detail)

    def test_a_sparse_series_yields_only_its_contiguous_pairs(self):
        """§12. A, B, then a hole, then D. One signal, one refusal, and no
        interpolation anywhere."""
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("climate", "20", BUCKET_B),
                observation("climate", "40", BUCKET_D),
            ]
        )
        self.assertEqual(len(outcome.drafts), 1)
        self.assertEqual(outcome.drafts[0].window.period_labels, (BUCKET_A, BUCKET_B))
        self.assertEqual(len(outcome.refusals), 1)
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.NON_CONTIGUOUS_SOURCE_BUCKETS)

    def test_three_contiguous_buckets_give_two_adjacent_pairs(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("climate", "20", BUCKET_B),
                observation("climate", "15", BUCKET_C),
            ]
        )
        self.assertEqual(
            [d.window.period_labels for d in outcome.drafts],
            [(BUCKET_A, BUCKET_B), (BUCKET_B, BUCKET_C)],
        )
        self.assertEqual(
            [d.direction for d in outcome.drafts],
            [SignalDirection.INCREASING, SignalDirection.DECREASING],
        )

    def test_reverse_database_order_is_the_same_signal(self):
        """§28. Order comes from the certified label, never from the rows a
        query returned."""
        forwards = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("climate", "20", BUCKET_B),
            ]
        )
        backwards = derive(
            [
                observation("climate", "20", BUCKET_B),
                observation("climate", "10", BUCKET_A),
            ]
        )
        self.assertEqual(
            forwards.drafts[0].derivation_fingerprint,
            backwards.drafts[0].derivation_fingerprint,
        )
        self.assertEqual(forwards.drafts[0].magnitude.value, backwards.drafts[0].magnitude.value)
        self.assertIs(backwards.drafts[0].direction, SignalDirection.INCREASING)

    def test_a_label_outside_the_scheme_is_refused(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                NormalizedObservation(
                    normalized_record_id="bad",
                    raw_record_id="raw-bad",
                    source_id="gdelt",
                    observation_key="gdelt|web-ngrams/1gram|nonsense|ENGLISH|climate",
                    record_kind_id="lexical_frequency_observation",
                    quality=NormalizedRecordQuality.PARTIAL,
                    quality_reasons=frozenset({Reason.PERIOD_TIMEZONE_NOT_ESTABLISHED}),
                    payload={
                        **observation("climate", "20", BUCKET_B).payload,
                        "period": {
                            "type": "INTERVAL",
                            "label": "nonsense",
                            "start": "2026-08-30T09:30:00",
                            "end": "2026-08-30T09:45:00",
                            "end_inclusive": False,
                            "timezone_state": "NOT_ESTABLISHED",
                        },
                    },
                ),
            ]
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INPUT_RECORD_INVALID)


# ================================================= §7, §8 certification and H-29


class TestCertificationAndTimezone(unittest.TestCase):
    def test_the_certified_stream_derives(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("climate", "20", BUCKET_B),
            ]
        )
        self.assertEqual(len(outcome.drafts), 1)

    def test_an_uncertified_resource_is_refused(self):
        """`chargram` is in the same directory with the same label scheme and no
        review has assessed it."""
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A, resource="web-ngrams/chargram"),
                observation("climate", "20", BUCKET_B, resource="web-ngrams/chargram"),
            ]
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.REQUIRED_FACT_WITHHELD)
        self.assertIn("SOURCE_RELATIVE_ORDER", outcome.refusals[0].detail)

    def test_an_uncertified_source_is_refused(self):
        """§7. The extractor asks the certification. It does not infer order
        from a label that happens to sort."""
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A, source_id="some-other-source"),
                observation("climate", "20", BUCKET_B, source_id="some-other-source"),
            ]
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.REQUIRED_FACT_WITHHELD)

    def test_the_window_carries_no_instant(self):
        """§8. ORDERED_PERIODS, no bounds, no observed_at, no timezone."""
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("climate", "20", BUCKET_B),
            ]
        )
        draft = outcome.drafts[0]
        self.assertIs(draft.window.basis, SignalTemporalBasis.ORDERED_PERIODS)
        self.assertIsNone(draft.observed_at)
        window = draft.window.to_json()
        self.assertNotIn("start", window)
        self.assertNotIn("end", window)
        serialised = canonical_json(window).lower()
        for invented in ("utc", "gmt", "+00:00", 'z"', "timezone"):
            self.assertNotIn(invented, serialised)

    def test_it_requires_order_and_not_an_instant(self):
        derivation = CHANGE.resolve({"terms": ["climate"]})
        self.assertIn(SignalRequiredFact.SOURCE_RELATIVE_ORDER, derivation.required_facts)
        self.assertNotIn(SignalRequiredFact.COMPARABLE_INSTANT, derivation.required_facts)
        self.assertNotIn(SignalRequiredFact.CANONICAL_LANGUAGE, derivation.required_facts)
        self.assertNotIn(SignalRequiredFact.CLASSIFIED_GEOGRAPHY, derivation.required_facts)


# ============================================================== compatibility


class TestCompatibility(unittest.TestCase):
    def test_two_language_labels_are_not_one_series(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A, language="ENGLISH"),
                observation("climate", "20", BUCKET_B, language="FRENCH"),
            ]
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_two_language_schemes_are_not_one_series(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("climate", "20", BUCKET_B, scheme="iso-639-1"),
            ]
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_one_gram_and_two_gram_are_not_one_series(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A, gram_size=1),
                observation("climate", "20", BUCKET_B, gram_size=2, resource="web-ngrams/2gram"),
            ]
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_two_terms_are_not_one_series(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("weather", "20", BUCKET_B),
            ]
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_two_resources_are_not_one_series(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A, resource="web-ngrams/1gram"),
                observation("climate", "20", BUCKET_B, resource="web-ngrams/2gram"),
            ]
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_SERIES)

    def test_a_numeric_record_is_the_wrong_kind(self):
        numeric = NormalizedObservation(
            normalized_record_id="wb",
            raw_record_id="raw-wb",
            source_id="world-bank",
            observation_key="world-bank|indicator/SP.POP.TOTL|DEU|2018",
            record_kind_id="numeric_observation",
            quality=NormalizedRecordQuality.VALID,
            quality_reasons=frozenset(),
            payload={"record_kind": "numeric_observation"},
        )
        outcome = derive([observation("climate", "10", BUCKET_A), numeric])
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS)

    def test_terms_are_preserved_verbatim(self):
        outcome = derive(
            [
                observation("  spaced  ", "10", BUCKET_A),
                observation("  spaced  ", "20", BUCKET_B),
            ],
            terms=("  spaced  ",),
        )
        self.assertEqual(outcome.drafts[0].scope.terms, ("  spaced  ",))

    def test_a_pipe_and_backslash_term(self):
        outcome = derive(
            [
                observation("climat\\e|d", "10", BUCKET_A),
                observation("climat\\e|d", "20", BUCKET_B),
            ],
            terms=("climat\\e|d",),
        )
        self.assertEqual(outcome.drafts[0].scope.terms, ("climat\\e|d",))

    def test_a_unicode_term(self):
        outcome = derive(
            [
                observation("климат", "10", BUCKET_A),
                observation("климат", "20", BUCKET_B),
            ],
            terms=("климат",),
        )
        self.assertEqual(len(outcome.drafts), 1)


# ============================================================ inputs and quality


class TestInputsAndQuality(unittest.TestCase):
    def test_one_observation_is_not_a_signal(self):
        outcome = derive([observation("climate", "10", BUCKET_A)])
        self.assertEqual(outcome.drafts, ())
        self.assertIs(
            outcome.refusals[0].reason, SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS
        )
        self.assertIn("absent", outcome.refusals[0].detail)

    def test_two_rows_for_one_bucket_are_refused(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A, record_id="v1"),
                observation("climate", "10", BUCKET_A, record_id="v2"),
                observation("climate", "20", BUCKET_B),
            ]
        )
        self.assertIs(outcome.refusals[0].reason, SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE)

    def test_partial_inputs_missing_irrelevant_facts_contribute(self):
        """§24. Both real GDELT reasons are present and neither is a fact this
        derivation needs -- ordering is separately certified, and exact source
        language equality is enough."""
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation("climate", "20", BUCKET_B),
            ]
        )
        draft = outcome.drafts[0]
        self.assertEqual(len(draft.contributed), 2)
        for assessed in draft.contributed:
            self.assertIs(assessed.observation.quality, NormalizedRecordQuality.PARTIAL)
            self.assertEqual(assessed.withheld, frozenset())

    def test_partial_missing_a_required_fact_is_refused(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation(
                    "climate",
                    None,
                    BUCKET_B,
                    reasons=frozenset(
                        {
                            Reason.PERIOD_TIMEZONE_NOT_ESTABLISHED,
                            Reason.LANGUAGE_NOT_MAPPED,
                            Reason.VALUE_NOT_REPORTED,
                        }
                    ),
                ),
            ]
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(
            outcome.refusals[0].reason, SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS
        )

    def test_an_invalid_input_never_contributes(self):
        outcome = derive(
            [
                observation("climate", "10", BUCKET_A),
                observation(
                    "climate",
                    "20",
                    BUCKET_B,
                    quality=NormalizedRecordQuality.INVALID,
                    reasons=frozenset({Reason.PERIOD_NOT_SUPPORTED}),
                ),
            ]
        )
        self.assertEqual(outcome.drafts, ())
        self.assertIs(
            outcome.refusals[0].reason, SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS
        )

    def test_a_term_nobody_selected_is_not_a_refusal(self):
        """A group outside the requested selection is not a derivation that
        failed. It is one nobody asked for."""
        outcome = derive(
            [
                observation("weather", "10", BUCKET_A),
                observation("weather", "20", BUCKET_B),
            ],
            terms=("climate",),
        )
        self.assertEqual(outcome.drafts, ())
        self.assertEqual(outcome.refusals, ())


# ================================================================= parameters


class TestParameters(unittest.TestCase):
    def test_terms_are_required(self):
        with self.assertRaises(SignalRefusedError) as caught:
            CHANGE.resolve({})
        self.assertIs(caught.exception.refusal.reason, SignalRefusalReason.PARAMETERS_INCOMPLETE)

    def test_an_empty_selection_is_a_refusal_not_everything(self):
        """§22. The most dangerous default this extractor could have."""
        with self.assertRaises(SignalRefusedError) as caught:
            CHANGE.resolve({"terms": []})
        self.assertIn("everything", caught.exception.refusal.detail)

    def test_a_string_is_not_a_term_list(self):
        with self.assertRaises(SignalRefusedError):
            CHANGE.resolve({"terms": "climate"})

    def test_the_selection_ceiling_is_ours_and_is_enforced(self):
        with self.assertRaises(SignalRefusedError) as caught:
            CHANGE.resolve({"terms": [f"t{i}" for i in range(MAX_SELECTED_TERMS + 1)]})
        self.assertIs(caught.exception.refusal.reason, SignalRefusalReason.PARAMETERS_INCOMPLETE)

    def test_term_order_does_not_change_the_fingerprint(self):
        self.assertEqual(
            CHANGE.resolve({"terms": ["climate", "weather"]}).parameter_fingerprint,
            CHANGE.resolve({"terms": ["weather", "climate"]}).parameter_fingerprint,
        )

    def test_the_pairing_strategy_is_persisted(self):
        derivation = CHANGE.resolve({"terms": ["climate"]})
        self.assertEqual(
            derivation.parameters_json(),
            {"pairing_strategy": "adjacent_source_buckets", "terms": ["climate"]},
        )

    def test_an_unimplemented_strategy_is_refused(self):
        with self.assertRaises(SignalRefusedError) as caught:
            CHANGE.resolve({"terms": ["climate"], "pairing_strategy": "all_pairs"})
        self.assertIs(caught.exception.refusal.reason, SignalRefusalReason.PARAMETERS_INCOMPLETE)

    def test_an_ignored_parameter_is_refused(self):
        with self.assertRaises(SignalRefusedError):
            CHANGE.resolve({"terms": ["climate"], "smoothing": "none"})


# =================================================================== identity


class TestIdentityAndBoundaries(unittest.TestCase):
    def test_the_same_derivation_converges(self):
        first = derive(
            [observation("climate", "10", BUCKET_A), observation("climate", "20", BUCKET_B)]
        )
        second = derive(
            [observation("climate", "10", BUCKET_A), observation("climate", "20", BUCKET_B)]
        )
        self.assertEqual(
            first.drafts[0].derivation_fingerprint, second.drafts[0].derivation_fingerprint
        )
        self.assertEqual(first.drafts[0].id, second.drafts[0].id)

    def test_the_outputs_are_not_in_the_identity(self):
        base = derive(
            [observation("climate", "10", BUCKET_A), observation("climate", "20", BUCKET_B)]
        )
        moved = derive(
            [observation("climate", "10", BUCKET_A), observation("climate", "99", BUCKET_B)]
        )
        self.assertEqual(
            base.drafts[0].derivation_fingerprint, moved.drafts[0].derivation_fingerprint
        )
        self.assertNotEqual(base.drafts[0].magnitude.value, moved.drafts[0].magnitude.value)

    def test_it_is_a_different_signal_from_the_same_bucket_contrast(self):
        """The two lexical extractors must never collide: different type,
        different family member, different basis, different magnitude kind."""
        draft = derive(
            [observation("climate", "10", BUCKET_A), observation("climate", "20", BUCKET_B)]
        ).drafts[0]
        self.assertEqual(draft.signal_type_id, "lexical_frequency_change")
        self.assertEqual(draft.derivation.extractor_id, "lexical-frequency-change")

    def test_no_interpretation_reaches_the_payload(self):
        draft = derive(
            [observation("climate", "10", BUCKET_A), observation("climate", "20", BUCKET_B)]
        ).drafts[0]
        serialised = canonical_json(
            {
                "scope": draft.scope.to_json(),
                "window": draft.window.to_json(),
                "magnitude": draft.magnitude.to_json(),
                "parameters": draft.derivation.parameters_json(),
            }
        ).lower()
        for interpretation in (
            "demand",
            "attention",
            "popularity",
            "interest",
            "momentum",
            "trend",
            "growth",
            "velocity",
            "topic",
            "sentiment",
        ):
            self.assertNotIn(interpretation, serialised)

    def test_no_canonical_language_and_no_geography(self):
        scope = (
            derive([observation("climate", "10", BUCKET_A), observation("climate", "20", BUCKET_B)])
            .drafts[0]
            .scope
        )
        self.assertEqual(scope.canonical_language_tags, ())
        self.assertEqual(scope.source_language_labels, ("ENGLISH",))
        self.assertEqual(scope.source_language_scheme, "cld2-language-name")
        self.assertNotIn("geography_codes", scope.to_json())

    def test_it_is_registered_and_deterministic(self):
        extractor = select_extractor("lexical-frequency-change")
        self.assertIsNotNone(extractor)
        self.assertEqual(extractor.extractor_version, "1.0.0")
        derivation = CHANGE.resolve({"terms": ["climate"]})
        self.assertIsNone(derivation.model_version)
        self.assertIsNone(derivation.prompt_version)


if __name__ == "__main__":
    unittest.main()
