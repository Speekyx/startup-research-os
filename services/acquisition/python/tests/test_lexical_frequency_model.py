"""The canonical model for a lexical frequency observation, and what it refuses.

Mission 1.10 §18. **No normalizer is implemented and no record is normalized.**
These prove the MODEL can represent a GDELT WEB-NGRAM observation without
inventing a timezone, a language code, a geography or a classification — and
that it refuses each invention when one is attempted.

The two real RawRecords collected by Mission 1.9.3 are the specimen. They are
read from a literal here rather than from the database, because a model test
that needed Postgres would be skipped exactly where the model is least
exercised.
"""

from __future__ import annotations

import inspect
import pathlib
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sros_acquisition.normalization import (
    RECORD_KINDS,
    CanonicalLanguage,
    CanonicalPeriod,
    CanonicalValue,
    LexicalFrequencyObservation,
    NumericObservation,
    build_normalized,
    canonical_json,
)
from sros_acquisition.normalization import model as model_module
from sros_contracts import (
    NormalizationQualityReason,
    NormalizedLanguageMapping,
    NormalizedPeriodType,
    NormalizedTimezoneState,
    NormalizedUnitState,
    NormalizedValueState,
)

from .conftest import REPO_ROOT

KIND = "lexical_frequency_observation"
BUCKET = "20260830091500"
CLD2 = "cld2-language-name"

#: The two real observations Mission 1.9.3 collected, as the collector wrote
#: them. Copied rather than queried so this module needs no database.
REAL_RECORDS = (
    {"gram_kind": "1gram", "date": BUCKET, "lang": "ENGLISH", "ngram": "climate", "count": "55"},
    {"gram_kind": "1gram", "date": BUCKET, "lang": "ENGLISH", "ngram": "weather", "count": "36"},
)


def bucket_period(label: str = BUCKET) -> CanonicalPeriod:
    """A 15-minute bucket with the timezone left unestablished.

    `INTERVAL` rather than a new period type: the contract already means "an
    arbitrary interval the source stated explicitly, where no calendar unit
    describes it", which is what a 15-minute bucket is. Adding a `MINUTE_15`
    member would encode one source's cadence into a closed enum.
    """
    # NAIVE on purpose, and this is the whole subject of the test module: a
    # wall-clock reading with no zone is what GDELT published, and Python's naive
    # datetime is exactly that. An aware one here would be the invention.
    start = datetime(  # noqa: DTZ001
        int(label[0:4]), int(label[4:6]), int(label[6:8]), int(label[8:10]), int(label[10:12])
    )
    return CanonicalPeriod(
        type=NormalizedPeriodType.INTERVAL,
        label=label,
        start=start,
        end=start.replace(minute=start.minute + 15) if start.minute < 45 else start,
        timezone_state=NormalizedTimezoneState.NOT_ESTABLISHED,
    )


def observation(row: dict[str, str]) -> LexicalFrequencyObservation:
    """Build the canonical payload from a real record, inventing nothing."""
    return LexicalFrequencyObservation(
        term_text=row["ngram"],
        term_gram_size=int(row["gram_kind"][0]),
        term_scheme="gdelt-web-ngram",
        language=CanonicalLanguage.unmapped(row["lang"], CLD2),
        value=CanonicalValue(
            value=Decimal(row["count"]),
            state=NormalizedValueState.REPORTED,
            unit=None,
            unit_state=NormalizedUnitState.NOT_PUBLISHED,
        ),
        period=bucket_period(row["date"]),
        dataset="web-ngrams",
        resource_id=f"web-ngrams/{row['gram_kind']}",
    )


# ================================================================ the period


class TestThePeriodCanSayTheTimezoneIsUnknown:
    def test_an_unestablished_period_refuses_aware_bounds(self) -> None:
        """§4. An aware bound under NOT_ESTABLISHED carries an offset the source
        never published — the invention this state exists to prevent."""
        with pytest.raises(ValueError, match="timezone-NAIVE"):
            CanonicalPeriod(
                type=NormalizedPeriodType.INTERVAL,
                label=BUCKET,
                start=datetime(2026, 8, 30, 9, 15, tzinfo=UTC),
                end=datetime(2026, 8, 30, 9, 30, tzinfo=UTC),
                timezone_state=NormalizedTimezoneState.NOT_ESTABLISHED,
            )

    def test_an_established_period_still_refuses_naive_bounds(self) -> None:
        """The Mission 1.6 rule, unchanged. This is not a weakening."""
        with pytest.raises(ValueError, match="timezone-aware"):
            CanonicalPeriod(
                type=NormalizedPeriodType.YEAR,
                label="2018",
                # Naive under the default ESTABLISHED state, which is what the
                # constructor must refuse.
                start=datetime(2018, 1, 1),  # noqa: DTZ001
                end=datetime(2019, 1, 1),  # noqa: DTZ001
            )

    def test_the_default_state_is_established(self) -> None:
        """Every period written before Mission 1.10 was one, and none had to be
        touched."""
        from sros_acquisition.normalization import year_period

        assert year_period("2018").timezone_state is NormalizedTimezoneState.ESTABLISHED

    def test_an_unestablished_period_offers_no_event_time(self) -> None:
        """§4. `observed_at` is a TIMESTAMPTZ: a naive start cannot go in it and
        an aware one would be the invented offset."""
        assert bucket_period().event_time is None

    def test_an_established_period_offers_its_start(self) -> None:
        from sros_acquisition.normalization import year_period

        assert year_period("2018").event_time == datetime(2018, 1, 1, tzinfo=UTC)

    def test_the_serialised_period_discloses_the_unknown_zone(self) -> None:
        payload = bucket_period().to_json()
        assert payload["timezone_state"] == "NOT_ESTABLISHED"
        assert payload["label"] == BUCKET
        assert payload["type"] == "INTERVAL"
        # No offset in the ISO string — the absence is visible without the key.
        assert "+00:00" not in payload["start"]
        assert not payload["start"].endswith("Z")

    def test_an_established_period_serialises_exactly_as_before(self) -> None:
        """§15. The payload is inside the content fingerprint, so an
        unconditional key would change the hash of every record ever written."""
        from sros_acquisition.normalization import year_period

        payload = year_period("2018").to_json()
        assert "timezone_state" not in payload
        assert payload == {
            "type": "YEAR",
            "label": "2018",
            "start": "2018-01-01T00:00:00+00:00",
            "end": "2019-01-01T00:00:00+00:00",
            "end_inclusive": False,
        }

    def test_the_bucket_duration_is_fifteen_minutes(self) -> None:
        period = bucket_period()
        assert (period.end - period.start).total_seconds() == 900


# ============================================================== the language


class TestTheLanguageCanStayUnmapped:
    def test_an_unmapped_label_carries_no_tag(self) -> None:
        """H-30. `ENGLISH` is not `en`, and resemblance is not a mapping."""
        language = CanonicalLanguage.unmapped("ENGLISH", CLD2)
        assert language.source_label == "ENGLISH"
        assert language.canonical_tag is None
        assert language.mapping_state is NormalizedLanguageMapping.NOT_ESTABLISHED
        assert language.mapped is False

    def test_the_missing_mapping_stays_visible(self) -> None:
        """§5. Three facts — source label, canonical tag, mapping status — and
        the third is what makes the absence readable rather than inferable."""
        payload = CanonicalLanguage.unmapped("ENGLISH", CLD2).to_json()
        assert payload["source_label"] == "ENGLISH"
        assert payload["source_scheme"] == CLD2
        assert payload["mapping_state"] == "NOT_ESTABLISHED"
        assert payload["canonical_tag"] is None

    def test_a_tag_without_an_established_mapping_is_refused(self) -> None:
        with pytest.raises(ValueError, match="guess"):
            CanonicalLanguage(
                source_label="ENGLISH",
                source_scheme=CLD2,
                mapping_state=NormalizedLanguageMapping.NOT_ESTABLISHED,
                canonical_tag="en",
                canonical_scheme="BCP-47",
            )

    def test_an_established_mapping_without_a_tag_is_refused(self) -> None:
        """The absence wearing the clothes of a fact, from the other side."""
        with pytest.raises(ValueError, match="must carry the tag"):
            CanonicalLanguage(
                source_label="ENGLISH",
                source_scheme=CLD2,
                mapping_state=NormalizedLanguageMapping.ESTABLISHED,
            )

    def test_an_established_mapping_carries_both_tag_and_scheme(self) -> None:
        """The shape a future mapping would take. Constructed here, not applied
        to any source: H-30 stays open."""
        language = CanonicalLanguage(
            source_label="ENGLISH",
            source_scheme=CLD2,
            mapping_state=NormalizedLanguageMapping.ESTABLISHED,
            canonical_tag="en",
            canonical_scheme="BCP-47",
        )
        assert language.mapped is True
        assert language.to_json()["canonical_tag"] == "en"

    def test_the_source_scheme_is_required(self) -> None:
        """`ENGLISH` means something only once a reader knows it came from CLD2
        rather than from ISO 639's English names, which overlap and differ."""
        with pytest.raises(ValueError, match="vocabulary it came from"):
            CanonicalLanguage.unmapped("ENGLISH", "")

    def test_language_is_not_geography(self) -> None:
        """§5, structurally. The two value objects share no field, so a language
        cannot be assigned where a geography is expected."""
        from sros_acquisition.normalization import CanonicalGeography

        language_fields = set(CanonicalLanguage.__dataclass_fields__)
        geography_fields = set(CanonicalGeography.__dataclass_fields__)
        assert language_fields & geography_fields == {"canonical_scheme"}
        for forbidden in ("country", "geography", "iso", "region", "canonical_code"):
            assert forbidden not in language_fields


# ============================================================ the record kind


class TestTheRecordKind:
    def test_the_kind_exists_and_describes_source_data(self) -> None:
        """§6. It must describe SOURCE DATA, never a derived signal."""
        kind = RECORD_KINDS[KIND]
        assert "signal" not in kind.description.lower().replace("not a signal", "")
        assert "count the source measured" in kind.description

    def test_the_kind_requires_the_term_the_language_and_the_period(self) -> None:
        kind = RECORD_KINDS[KIND]
        for field in ("term.text", "term.gram_size", "language.source_label", "period"):
            assert field in kind.required

    def test_the_kind_does_not_require_a_geography(self) -> None:
        """§6. A WEB-NGRAM row has none, and requiring one would make every
        record INVALID for a fact about the source rather than about the row."""
        kind = RECORD_KINDS[KIND]
        assert not any("geography" in field for field in kind.required + kind.optional)

    def test_the_canonical_tag_is_optional_while_no_mapping_exists(self) -> None:
        """H-30. A required field nothing can satisfy would make every record
        INVALID for a condition that is universal and known; the absence stays
        visible through `mapping_state` instead."""
        assert "language.canonical_tag" in RECORD_KINDS[KIND].optional

    def test_the_numeric_kind_is_untouched(self) -> None:
        """§15. Widening `numeric_observation` to fit GDELT would have let a
        World Bank record exist with no geography."""
        kind = RECORD_KINDS["numeric_observation"]
        assert "geography.source_code" in kind.required
        assert "metric.id" in kind.required


# ================================================== the two real observations


class TestTheModelRepresentsTheRealRecords:
    @pytest.mark.parametrize("row", REAL_RECORDS, ids=lambda r: r["ngram"])
    def test_a_real_record_becomes_a_payload_with_nothing_invented(self, row) -> None:
        payload = observation(row).to_payload()

        assert payload["record_kind"] == KIND
        assert payload["term"]["text"] == row["ngram"]
        assert payload["term"]["gram_size"] == 1
        assert payload["language"]["source_label"] == "ENGLISH"
        assert payload["language"]["canonical_tag"] is None
        assert payload["observation"]["value"] == row["count"]
        assert payload["observation"]["unit"] is None
        assert payload["observation"]["unit_state"] == "NOT_PUBLISHED"
        assert payload["period"]["label"] == BUCKET
        assert payload["period"]["timezone_state"] == "NOT_ESTABLISHED"

    def test_no_geography_key_exists_at_all(self) -> None:
        """§16. ABSENT rather than null: a null would invite a reader to think
        one was looked for and not found."""
        payload = observation(REAL_RECORDS[0]).to_payload()
        assert "geography" not in payload
        assert "geography" not in canonical_json(payload)

    def test_no_classification_appears_anywhere(self) -> None:
        """§17. The term is not a theme, an entity or a topic."""
        serialised = canonical_json(observation(REAL_RECORDS[0]).to_payload()).lower()
        for classification in ("theme", "entity", "topic", "keyword", "intent", "sentiment"):
            assert classification not in serialised

    def test_the_count_is_never_a_signal_or_a_score(self) -> None:
        """§7. A frequency the source measured, and nothing derived from it."""
        serialised = canonical_json(observation(REAL_RECORDS[0]).to_payload()).lower()
        for derived in ("signal", "score", "strength", "rank", "popularity", "trend"):
            assert derived not in serialised

    def test_no_timezone_is_invented(self) -> None:
        serialised = canonical_json(observation(REAL_RECORDS[0]).to_payload())
        assert "+00:00" not in serialised
        assert "UTC" not in serialised

    def test_no_language_code_is_invented(self) -> None:
        serialised = canonical_json(observation(REAL_RECORDS[0]).to_payload())
        assert '"canonical_tag":null' in serialised.replace(" ", "")

    def test_the_gram_kind_survives_in_content_and_provenance(self) -> None:
        """§10. Both, and not identity — the observation key already carries the
        resource id, so the two resources are already distinct."""
        payload = observation(REAL_RECORDS[0]).to_payload()
        assert payload["term"]["gram_size"] == 1
        assert payload["series"]["resource_id"] == "web-ngrams/1gram"

    def test_a_bigram_is_distinguishable_from_a_unigram(self) -> None:
        unigram = observation({**REAL_RECORDS[0], "gram_kind": "1gram"}).to_payload()
        bigram = observation(
            {
                "gram_kind": "2gram",
                "date": BUCKET,
                "lang": "ENGLISH",
                "ngram": "climate",
                "count": "55",
            }
        ).to_payload()
        assert unigram["term"]["gram_size"] != bigram["term"]["gram_size"]
        assert unigram["series"]["resource_id"] != bigram["series"]["resource_id"]

    def test_the_gram_size_is_never_inferred_from_the_term(self) -> None:
        """§10. A two-word entry in a unigram file is a contract violation, and
        counting spaces would hide it rather than surface it."""
        source = pathlib.Path(model_module.__file__).read_text(encoding="utf-8")
        block = source[source.index("class LexicalFrequencyObservation") :]
        block = block[: block.index("class CanonicalObservation")]
        assert ".split(" not in block
        assert ".count(" not in block

    def test_a_gram_size_below_one_is_refused(self) -> None:
        with pytest.raises(ValueError, match="gram size"):
            LexicalFrequencyObservation(
                term_text="climate",
                term_gram_size=0,
                term_scheme="gdelt-web-ngram",
                language=CanonicalLanguage.unmapped("ENGLISH", CLD2),
                value=CanonicalValue(value=Decimal("1"), state=NormalizedValueState.REPORTED),
                period=bucket_period(),
            )


# ==================================================================== numbers


class TestTheCountKeepsItsPrecision:
    def test_a_count_beyond_float_precision_is_exact(self) -> None:
        """§7. 9007199254740993 is not representable as a double; a float
        round-trip returns ...92."""
        row = {**REAL_RECORDS[0], "count": "9007199254740993"}
        assert observation(row).to_payload()["observation"]["value"] == "9007199254740993"

    def test_a_zero_count_stays_a_measurement(self) -> None:
        row = {**REAL_RECORDS[0], "count": "0"}
        payload = observation(row).to_payload()["observation"]
        assert payload["value"] == "0"
        assert payload["value_state"] == "REPORTED"

    def test_the_unit_is_not_published_rather_than_invented(self) -> None:
        """§8. GDELT publishes four columns and none is a unit. 'mentions' would
        assert the source did something it did not — and the record kind already
        says the number is an occurrence count over a window."""
        payload = observation(REAL_RECORDS[0]).to_payload()["observation"]
        assert payload["unit"] is None
        assert payload["unit_state"] == "NOT_PUBLISHED"

    def test_the_count_is_not_part_of_the_payload_identity_fields(self) -> None:
        """§9. Two rows differing only in COUNT are the same observation."""
        low = observation({**REAL_RECORDS[0], "count": "55"}).to_payload()
        high = observation({**REAL_RECORDS[0], "count": "9999"}).to_payload()
        for key in ("term", "language", "period"):
            assert low[key] == high[key]
        assert low["observation"] != high["observation"]


# ================================================================ the builder


class TestBuildNormalizedAcceptsBothShapes:
    def test_the_builder_is_typed_to_the_protocol_not_to_one_kind(self) -> None:
        """§14. A second kind existed, so the parameter had to widen — to a
        three-member protocol rather than to a union of two field sets."""
        signature = inspect.signature(build_normalized)
        assert signature.parameters["observation"].annotation == "CanonicalObservation"

    def test_the_builder_still_has_no_attribution_or_expiry_parameter(self) -> None:
        """Mission 1.6 §46 and §10, unchanged. A normalizer has nothing to pass."""
        parameters = set(inspect.signature(build_normalized).parameters)
        assert "attribution" not in parameters
        assert "expires_at" not in parameters

    def test_both_payload_classes_satisfy_the_protocol(self) -> None:
        for cls in (NumericObservation, LexicalFrequencyObservation):
            for member in ("record_kind", "period", "to_payload"):
                assert hasattr(cls, member) or member in cls.__dataclass_fields__


# ================================================== quality reasons and gates


class TestTheQualityVocabularyCanNameBothAbsences:
    def test_the_timezone_absence_has_a_reason_code(self) -> None:
        assert NormalizationQualityReason.PERIOD_TIMEZONE_NOT_ESTABLISHED

    def test_the_language_absence_has_a_reason_code(self) -> None:
        assert NormalizationQualityReason.LANGUAGE_NOT_MAPPED

    def test_neither_reason_is_an_error_code(self) -> None:
        """Both describe a source that published less than a consumer expects,
        not a failure to read what it did publish."""
        for reason in (
            NormalizationQualityReason.PERIOD_TIMEZONE_NOT_ESTABLISHED,
            NormalizationQualityReason.LANGUAGE_NOT_MAPPED,
        ):
            assert "MALFORMED" not in reason.value
            assert "MISSING" not in reason.value


# =========================================== nothing was implemented or written


class TestNoNormalizerExists:
    def test_no_gdelt_normalizer_is_registered(self) -> None:
        """§22. The registry says *code exists that can normalize this*, and
        none does. The record-kind registry row is a VOCABULARY entry, which is
        a different claim."""
        from sros_acquisition.normalization import NORMALIZER_REGISTRY

        assert not any(key[0] == "gdelt" for key in NORMALIZER_REGISTRY)

    def test_gdelt_is_not_normalizable(self) -> None:
        from sros_acquisition import IMPLEMENTED_NORMALIZERS

        assert frozenset({"world-bank"}) == IMPLEMENTED_NORMALIZERS

    def test_no_gdelt_normalizer_module_exists(self) -> None:
        package = REPO_ROOT / "services/acquisition/python/sros_acquisition/normalization"
        for name in ("gdelt.py", "gdelt_web_ngram.py", "lexical_frequency.py"):
            assert not (package / name).exists()

    def test_the_model_change_reached_no_model_or_network(self) -> None:
        """§17. Deterministic structural representation only."""
        source = pathlib.Path(model_module.__file__).read_text(encoding="utf-8")
        for forbidden in ("httpx", "requests", "anthropic", "openai", "qdrant", "embed"):
            assert forbidden not in source.lower()

    def test_the_registry_row_exists_without_an_adapter(self) -> None:
        """The deliberate split, asserted so it stays deliberate: the vocabulary
        is registered so the model can describe the shape, and no adapter claims
        to produce it."""
        migrations = (REPO_ROOT / "infrastructure/db/migrations").glob("*.sql")
        sql = "\n".join(path.read_text(encoding="utf-8") for path in migrations)
        assert f"'{KIND}'" in sql

        normalizers = pathlib.Path(model_module.__file__).parent / "normalizers.py"
        assert "gdelt" not in normalizers.read_text(encoding="utf-8").lower()
