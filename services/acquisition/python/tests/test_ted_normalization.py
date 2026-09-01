"""TED notices into canonical records, without inventing what the source did not say.

Mission 1.15.8. **No network and no database.** Every case builds a
`RawRecordView` by hand from the sanitized fixtures, so the adapter is exercised
against shapes rather than against whatever this machine happens to hold.

The properties this file exists to protect, and each is a way the mission could
have gone wrong quietly:

    a published DATE does not become a moment
    a multilingual name does not become an English one
    three lots do not become one amount
    four monetary meanings do not become one number
    an amount without its semantic is not stored at all
"""

from __future__ import annotations

import ast
import json
import pathlib
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sros_acquisition.normalization import (
    NORMALIZER_REGISTRY,
    TedSearchApiNoticeNormalizer,
    select_normalizer,
)
from sros_acquisition.normalization.errors import NormalizationFailedError
from sros_acquisition.normalization.model import (
    MONETARY_AMOUNT_TYPES,
    NOTICE_TYPE_CLASSES,
    RECORD_KINDS,
    CanonicalMultilingualText,
    RawRecordView,
)
from sros_acquisition.normalization.ted_search_api import (
    MONETARY_FIELDS,
    TED_NORMALIZER_ID,
    TED_NORMALIZER_VERSION,
    TED_RESOURCE_ID,
)
from sros_acquisition.registry.retention import EffectiveRetention
from sros_contracts import (
    NormalizedPeriodType,
    NormalizedRecordQuality,
    NormalizedTimezoneState,
)

from . import ted_search_fixtures as fx
from .conftest import REPO_ROOT

NORMALIZER_SOURCE = (
    REPO_ROOT
    / "services"
    / "acquisition"
    / "python"
    / "sros_acquisition"
    / "normalization"
    / "ted_search_api.py"
)

MOMENT = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
WORKSPACE = "11111111-1111-1111-1111-111111111111"

RETENTION = EffectiveRetention(
    raw_days=30,
    normalized_days=365,
    aggregate_permitted=True,
    raw_source="baseline",
    normalized_source="baseline",
)


def raw(payload: dict[str, object], **overrides: object) -> RawRecordView:
    """One raw record, shaped as `read_raw_records` returns it."""
    provenance: dict[str, object] = {
        "source_id": "ted-eu",
        "resource_id": TED_RESOURCE_ID,
        "dataset_family": "ted-search-api-notices",
        "access_profile": "ted-search-api",
        "attribution": {"text": "Tenders Electronic Daily (TED)", "elements": []},
        "review_version": 2,
    }
    provenance.update(overrides.pop("provenance_extra", {}))  # type: ignore[arg-type]
    if "provenance" in overrides:
        provenance = overrides.pop("provenance")  # type: ignore[assignment]
    base: dict[str, object] = {
        "record_id": "aaaaaaaa-0000-0000-0000-000000000001",
        "workspace_id": WORKSPACE,
        "research_session_id": None,
        "source_id": "ted-eu",
        "observation_key": "ted-eu|notice|00123456-2023",
        "content_hash": "sha256:deadbeef",
        "acquisition_method": "OFFICIAL_API",
        "payload": payload,
        "provenance": provenance,
        "review_version": 2,
        "collector_id": "ted-search-api",
        "collector_version": "1.0.0",
        "correlation_id": "mission-1.15.8-test",
        "collected_at": MOMENT,
        "observed_at": None,
        "expires_at": MOMENT,
    }
    base.update(overrides)
    return RawRecordView(**base)  # type: ignore[arg-type]


@pytest.fixture
def normalizer() -> TedSearchApiNoticeNormalizer:
    return TedSearchApiNoticeNormalizer(RETENTION)


def as_stored(payload: dict[str, object]) -> dict[str, object]:
    """The payload as normalization actually receives it.

    **The whole numeric path, modelled rather than assumed.** The collector
    stores what the API sent as JSON, PostgreSQL keeps it as `jsonb`, and
    `read_raw_records` reads `payload::text` back with `parse_float=Decimal`.
    Handing the adapter a Python float would test a shape production never
    produces -- and would hide the fact that a float is REFUSED rather than
    rounded, which is the property §18 is about.
    """
    return json.loads(json.dumps(payload, default=str), parse_float=Decimal)


def normalize(normalizer, payload: dict[str, object], **overrides: object):
    return normalizer.normalize(
        raw(as_stored(payload), **overrides),
        correlation_id="mission-1.15.8-test",
        normalized_at=MOMENT,
    )


def reason_codes(draft) -> set[str]:
    return {r.code.value for r in draft.quality_reasons}


# ================================================= registration and lineage


class TestRegistrationAndLineage:
    def test_the_adapter_is_registered_for_the_collector(self) -> None:
        spec = NORMALIZER_REGISTRY[("ted-eu", "ted-search-api")]
        assert spec.normalizer_id == TED_NORMALIZER_ID
        assert spec.normalizer_version == TED_NORMALIZER_VERSION
        assert spec.supported_collector_versions == frozenset({"1.0.0"})

    def test_selection_finds_it_for_a_real_record(self) -> None:
        spec = select_normalizer(raw(as_stored(fx.CONTRACT_NOTICE)))
        assert spec.normalizer_id == TED_NORMALIZER_ID

    def test_an_unsupported_collector_version_is_refused(self) -> None:
        """A collector version this adapter has never seen may have changed the
        payload shape, and a parse that half-works on an unknown one is worse
        than one that stops."""
        with pytest.raises(NormalizationFailedError):
            select_normalizer(raw(as_stored(fx.CONTRACT_NOTICE), collector_version="9.9.9"))

    def test_the_record_kind_is_declared(self) -> None:
        kind = RECORD_KINDS["procurement_notice"]
        assert kind.required == ("notice.publication_number", "notice.source_type", "period")

    def test_a_record_from_another_source_is_refused(self, normalizer) -> None:
        with pytest.raises(NormalizationFailedError) as caught:
            normalize(normalizer, fx.CONTRACT_NOTICE, source_id="world-bank")
        assert "not 'ted-eu'" in caught.value.failure.detail

    def test_a_record_from_another_collector_is_refused(self, normalizer) -> None:
        with pytest.raises(NormalizationFailedError) as caught:
            normalize(normalizer, fx.CONTRACT_NOTICE, collector_id="ted-bulk-xml")
        assert "parses a different shape" in caught.value.failure.detail

    @pytest.mark.parametrize(
        "resource",
        ["packages/daily-2023-03-01", "csv/contract-awards-2018-2023", "notices/mystery"],
    )
    def test_an_unauthorised_resource_is_refused(self, normalizer, resource: str) -> None:
        """§5. Bulk, the historical CSV and an unreviewed resource are refused
        here as well as at acquisition -- a second gate, because a raw record
        can outlive the configuration that produced it."""
        with pytest.raises(NormalizationFailedError) as caught:
            normalize(
                normalizer,
                fx.CONTRACT_NOTICE,
                provenance={
                    "resource_id": resource,
                    "dataset_family": "ted-search-api-notices",
                    "attribution": {"text": "TED", "elements": []},
                },
            )
        assert "authorised" in caught.value.failure.detail

    def test_a_foreign_dataset_family_is_refused(self, normalizer) -> None:
        with pytest.raises(NormalizationFailedError):
            normalize(
                normalizer,
                fx.CONTRACT_NOTICE,
                provenance={
                    "resource_id": TED_RESOURCE_ID,
                    "dataset_family": "ted-bulk-xml-daily",
                    "attribution": {"text": "TED", "elements": []},
                },
            )


# ============================================================ identity


class TestIdentity:
    def test_the_publication_number_is_the_identity(self, normalizer) -> None:
        draft = normalize(normalizer, fx.CONTRACT_NOTICE)
        assert draft.payload["notice"]["publication_number"] == "00123456-2023"
        assert draft.raw_record_id == "aaaaaaaa-0000-0000-0000-000000000001"

    def test_the_source_identifiers_survive(self, normalizer) -> None:
        draft = normalize(normalizer, fx.CONTRACT_NOTICE)
        notice = draft.payload["notice"]
        assert notice["identifier"] == "11111111-2222-3333-4444-555555555555"
        assert notice["version"] == 1

    def test_absent_identifiers_are_null_not_invented(self, normalizer) -> None:
        """The three real records carry neither. A placeholder would make two
        different notices look alike."""
        payload = {
            k: v
            for k, v in fx.CONTRACT_NOTICE.items()
            if k not in {"notice-identifier", "notice-version"}
        }
        notice = normalize(normalizer, payload).payload["notice"]
        assert notice["identifier"] is None
        assert notice["version"] is None

    def test_normalization_is_deterministic(self, normalizer) -> None:
        one = normalize(normalizer, fx.AWARD_NOTICE)
        two = normalize(normalizer, fx.AWARD_NOTICE)
        assert one.record_id == two.record_id
        assert one.content_hash == two.content_hash

    def test_a_record_without_identity_is_refused(self, normalizer) -> None:
        """§29. Defensive: collection already refuses this."""
        with pytest.raises(NormalizationFailedError) as caught:
            normalize(normalizer, fx.NOTICE_WITHOUT_IDENTITY)
        assert "source-native identity" in caught.value.failure.detail


# ======================================================== the notice type


class TestNoticeType:
    def test_both_the_class_and_the_source_type_are_kept(self, normalizer) -> None:
        """§7. A normalized class alone loses which vocabulary produced it; a
        source type alone makes every consumer learn TED's spelling."""
        notice = normalize(normalizer, fx.CONTRACT_NOTICE).payload["notice"]
        assert notice["class"] == "CONTRACT_NOTICE"
        assert notice["source_type"] == "cn-standard"
        assert notice["source_type_scheme"] == "ted-notice-type"

    def test_an_award_notice_is_a_different_class(self, normalizer) -> None:
        notice = normalize(normalizer, fx.AWARD_NOTICE).payload["notice"]
        assert notice["class"] == "CONTRACT_AWARD_NOTICE"
        assert notice["source_type"] == "can-standard"

    def test_the_two_families_never_collapse(self) -> None:
        assert len(set(NOTICE_TYPE_CLASSES.values())) == 2

    def test_a_notice_family_outside_the_resource_is_refused(self, normalizer) -> None:
        with pytest.raises(NormalizationFailedError) as caught:
            normalize(normalizer, {**fx.CONTRACT_NOTICE, "notice-type": "pin-only"})
        assert "outside the authorised resource" in caught.value.failure.detail


# ============================================================== temporal


class TestTemporal:
    def test_the_period_is_the_published_day(self, normalizer) -> None:
        period = normalize(normalizer, fx.CONTRACT_NOTICE).payload["period"]
        assert period["type"] == NormalizedPeriodType.DAY.value
        assert period["label"] == "2023-03-02Z"
        assert period["start"] == "2023-03-02T00:00:00"
        assert period["end"] == "2023-03-03T00:00:00"

    def test_the_bounds_are_naive(self, normalizer) -> None:
        """A wall-clock reading, which is what the value is. An aware bound would
        carry an offset whose meaning nobody has established."""
        period = normalize(normalizer, fx.CONTRACT_NOTICE).payload["period"]
        assert period["timezone_state"] == NormalizedTimezoneState.NOT_ESTABLISHED.value
        assert "+" not in period["start"] and "Z" not in period["start"]

    def test_observed_at_is_null(self, normalizer) -> None:
        """§8, §39. The mission's hardest question, answered by not answering it.
        There is no time of day in the value, so any instant is a choice -- and
        midnight is the choice that looks like no choice."""
        assert normalize(normalizer, fx.CONTRACT_NOTICE).observed_at is None

    def test_the_source_value_survives_verbatim(self, normalizer) -> None:
        """So a later mission can close H-37 by re-deriving over records already
        held, rather than by collecting again."""
        publication = normalize(normalizer, fx.CONTRACT_NOTICE).payload["publication"]
        assert publication["source_value"] == "2023-03-02Z"
        assert publication["precision"] == "DAY"
        assert publication["offset_semantics"] == "NOT_ESTABLISHED"

    def test_a_real_offset_is_preserved(self, normalizer) -> None:
        payload = {**fx.CONTRACT_NOTICE, "publication-date": "2023-03-01+01:00"}
        publication = normalize(normalizer, payload).payload["publication"]
        assert publication["utc_offset"] == "+01:00"
        assert publication["source_value"] == "2023-03-01+01:00"

    def test_every_record_says_the_timezone_is_unestablished(self, normalizer) -> None:
        draft = normalize(normalizer, fx.CONTRACT_NOTICE)
        assert "PERIOD_TIMEZONE_NOT_ESTABLISHED" in reason_codes(draft)
        assert draft.quality is NormalizedRecordQuality.PARTIAL

    def test_a_date_of_an_unexpected_shape_is_drift(self, normalizer) -> None:
        """§30. Not an absence: a known field whose shape changed."""
        with pytest.raises(NormalizationFailedError) as caught:
            normalize(normalizer, {**fx.CONTRACT_NOTICE, "publication-date": "01/03/2023"})
        assert "response-contract change" in caught.value.failure.detail

    def test_a_missing_publication_date_is_refused(self, normalizer) -> None:
        payload = {k: v for k, v in fx.CONTRACT_NOTICE.items() if k != "publication-date"}
        with pytest.raises(NormalizationFailedError) as caught:
            normalize(normalizer, payload)
        assert "when we happened to fetch it" in caught.value.failure.detail

    def test_award_and_contract_dates_stay_separate_and_native(self, normalizer) -> None:
        """§9. Three date concepts, never merged, and the two below have no
        established temporal semantics either -- so they stay as source strings
        rather than being parsed into a shape that would imply one."""
        dates = normalize(normalizer, fx.AWARD_NOTICE).payload["dates"]
        assert dates["award_decision"] == ["2023-02-20Z"]
        assert dates["contract_conclusion"] == ["2023-02-28Z"]

    def test_both_are_absent_on_a_contract_notice(self, normalizer) -> None:
        dates = normalize(normalizer, fx.CONTRACT_NOTICE).payload["dates"]
        assert dates["award_decision"] == []
        assert dates["contract_conclusion"] == []


# ========================================================== multilingual


class TestMultilingual:
    def test_every_language_is_kept(self, normalizer) -> None:
        buyer = normalize(normalizer, fx.CONTRACT_NOTICE).payload["organisations"]["buyer"]
        assert buyer["by_language"] == {
            "eng": ["Example Public Buyer"],
            "fra": ["Acheteur Public"],
        }
        assert buyer["language_tags"] == ["eng", "fra"]

    def test_no_language_is_selected_as_the_canonical_one(self, normalizer) -> None:
        """§10. There is no `display` key, and its absence is the design: a
        canonical display value would be read as *the* name and the rule that
        produced it would live in code rather than where a reader can see it."""
        buyer = normalize(normalizer, fx.CONTRACT_NOTICE).payload["organisations"]["buyer"]
        assert "display" not in buyer
        assert "canonical" not in buyer

    def test_ordering_is_deterministic(self) -> None:
        one = CanonicalMultilingualText.from_source({"fra": ["b"], "eng": ["a"]})
        two = CanonicalMultilingualText.from_source({"eng": ["a"], "fra": ["b"]})
        assert one == two
        assert one.language_tags == ("eng", "fra")

    def test_nothing_is_translated(self, normalizer) -> None:
        buyer = normalize(normalizer, fx.CONTRACT_NOTICE).payload["organisations"]["buyer"]
        assert buyer["by_language"]["fra"] == ["Acheteur Public"]

    def test_an_unexpected_shape_is_drift_not_a_string(self, normalizer) -> None:
        with pytest.raises(NormalizationFailedError) as caught:
            normalize(
                normalizer,
                {**fx.CONTRACT_NOTICE, "organisation-name-buyer": "Example Public Buyer"},
            )
        assert "language-keyed object" in caught.value.failure.detail


# ==================================================== buyers and suppliers


class TestOrganisations:
    def test_buyer_and_tenderer_are_distinct_roles(self, normalizer) -> None:
        organisations = normalize(normalizer, fx.AWARD_NOTICE).payload["organisations"]
        assert organisations["buyer"]["by_language"]["eng"] == ["Example Public Buyer"]
        assert organisations["tenderer"]["by_language"]["eng"] == ["Example Winning Supplier Ltd"]

    def test_a_contract_notice_has_no_tenderer_and_that_is_valid(self, normalizer) -> None:
        """§11. Absence is valid: no award has happened yet."""
        organisations = normalize(normalizer, fx.CONTRACT_NOTICE).payload["organisations"]
        assert organisations["tenderer"] is None

    def test_the_payload_never_says_supplier_or_winner(self, normalizer) -> None:
        """§11, §32. A tenderer is not read as an awarded supplier. Only
        `award.selection_status` speaks to an outcome, and it is the source's
        own value."""
        import json

        text = json.dumps(normalize(normalizer, fx.AWARD_NOTICE).payload)
        assert '"supplier"' not in text
        assert '"winner"' not in text
        assert '"awarded_supplier"' not in text

    def test_multiplicity_is_preserved(self, normalizer) -> None:
        """§12. Three tenderers stay three, and are not concatenated."""
        tenderer = normalize(normalizer, fx.MULTI_LOT_NOTICE).payload["organisations"]["tenderer"]
        assert tenderer["by_language"]["eng"] == [
            "Supplier One Ltd",
            "Supplier Two Ltd",
            "Supplier Three Ltd",
        ]

    def test_award_status_is_the_source_value(self, normalizer) -> None:
        """§20. Never inferred from the presence of an amount or a supplier."""
        assert normalize(normalizer, fx.AWARD_NOTICE).payload["award"]["selection_status"] == [
            "selec-w"
        ]
        assert normalize(normalizer, fx.CONTRACT_NOTICE).payload["award"]["selection_status"] == []


# ========================================================= classification


class TestClassification:
    def test_cpv_codes_are_identifiers_with_their_scheme(self, normalizer) -> None:
        codes = normalize(normalizer, fx.CONTRACT_NOTICE).payload["classification"]["codes"]
        assert codes == [
            {"code": "72000000", "scheme": "CPV", "label": None},
        ]

    def test_no_sector_is_invented(self, normalizer) -> None:
        """§13. No market category, no SaaS, no IT. A taxonomy mapping is a
        reviewed act and belongs to the mission that does it."""
        import json

        text = json.dumps(normalize(normalizer, fx.CONTRACT_NOTICE).payload).lower()
        for invented in ("saas", "software", "sector", "industry", "market"):
            assert invented not in text, invented

    def test_contract_nature_is_preserved(self, normalizer) -> None:
        classification = normalize(normalizer, fx.CONTRACT_NOTICE).payload["classification"]
        assert classification["contract_nature"] == ["services"]

    def test_country_and_region_codes_are_kept_unmapped(self, normalizer) -> None:
        """§21. No geocoding, no inference from an organisation name."""
        place = normalize(normalizer, fx.CONTRACT_NOTICE).payload["place"]
        assert place["buyer_countries"] == ["DEU"]
        assert place["performance_subdivisions"] == ["DE300"]
        assert place["scheme"] == "ted-source-code"


# =================================================================== lots


class TestLots:
    def test_a_multi_lot_notice_stays_one_record(self, normalizer) -> None:
        """§14, §27. One notice, one record. A per-lot record would invent an
        identity the source does not have."""
        draft = normalize(normalizer, fx.MULTI_LOT_NOTICE)
        assert draft.payload["notice"]["publication_number"] == "00777777-2023"

    def test_the_lot_distinctions_survive(self, normalizer) -> None:
        payload = normalize(normalizer, fx.MULTI_LOT_NOTICE).payload
        assert len(payload["classification"]["codes"]) == 3
        assert len(payload["place"]["performance_subdivisions"]) == 3

    def test_the_three_lot_amounts_do_not_become_one(self, normalizer) -> None:
        """The failure this whole design exists to prevent."""
        amounts = normalize(normalizer, fx.MULTI_LOT_NOTICE).payload["amounts"]
        tender = next(a for a in amounts if a["amount_type"] == "TENDER_VALUE")
        assert tender["amounts"] == ["11000", "22000", "33000"]

    def test_lot_scope_is_recorded(self, normalizer) -> None:
        amounts = normalize(normalizer, fx.MULTI_LOT_NOTICE).payload["amounts"]
        assert {a["amount_type"]: a["scope"] for a in amounts} == {
            "TENDER_VALUE": "LOT",
            "FRAMEWORK_MAXIMUM": "LOT",
        }

    def test_source_order_is_preserved(self, normalizer) -> None:
        """Position is the only thing relating one lot entry to another, so
        nothing here sorts."""
        place = normalize(normalizer, fx.MULTI_LOT_NOTICE).payload["place"]
        assert place["performance_countries"] == ["FRA", "FRA", "BEL"]


# =============================================================== monetary


class TestMonetary:
    def test_the_four_semantics_are_the_vocabulary(self) -> None:
        assert set(MONETARY_AMOUNT_TYPES) == {
            "TOTAL_VALUE",
            "TENDER_VALUE",
            "ESTIMATED_VALUE",
            "FRAMEWORK_MAXIMUM",
        }
        assert {entry[1] for entry in MONETARY_FIELDS} == set(MONETARY_AMOUNT_TYPES)

    def test_a_total_value_keeps_its_type_and_field(self, normalizer) -> None:
        amounts = normalize(normalizer, fx.AWARD_NOTICE).payload["amounts"]
        total = next(a for a in amounts if a["amount_type"] == "TOTAL_VALUE")
        assert total["source_field"] == "total-value"
        assert total["scope"] == "NOTICE"
        # `1875000.5`, not `1875000.50`: the FIXTURE is a Python float and
        # `json.dumps` drops the trailing zero before the value is ever stored.
        # The canonical form is a normalized exact decimal; the source's own
        # lexical form is the RawRecord's job and it keeps it.
        assert total["amounts"] == ["1875000.5"]
        assert total["currencies"] == ["EUR"]

    def test_an_estimated_value_is_not_a_total(self, normalizer) -> None:
        """The distinction that matters most: an estimate is not what anybody
        paid, and a framework maximum is a ceiling."""
        amounts = normalize(normalizer, fx.CONTRACT_NOTICE).payload["amounts"]
        assert [a["amount_type"] for a in amounts] == ["ESTIMATED_VALUE"]
        assert amounts[0]["scope"] == "LOT"

    def test_several_semantics_coexist_on_one_notice(self, normalizer) -> None:
        amounts = normalize(normalizer, fx.MULTI_LOT_NOTICE).payload["amounts"]
        assert {a["amount_type"] for a in amounts} == {"TENDER_VALUE", "FRAMEWORK_MAXIMUM"}

    def test_an_absent_monetary_block_produces_no_entry(self, normalizer) -> None:
        """§28. Absent is not zero and not a failure."""
        assert normalize(normalizer, fx.NOTICE_WITHOUT_MONEY).payload["amounts"] == []

    def test_amounts_are_exact_decimal_strings(self, normalizer) -> None:
        """§18. No binary float anywhere on the path, and no rounding."""
        amounts = normalize(normalizer, fx.AWARD_NOTICE).payload["amounts"]
        total = next(a for a in amounts if a["amount_type"] == "TOTAL_VALUE")
        assert total["amounts"] == ["1875000.5"]
        assert isinstance(total["amounts"][0], str)

    def test_a_long_decimal_survives_the_whole_path_unrounded(self, normalizer) -> None:
        """The property the round trip above exists to prove: a decimal with
        more significant digits than a float64 can hold arrives intact."""
        payload = {**fx.AWARD_NOTICE, "total-value": Decimal("12345678901234567.89")}
        amounts = normalize(normalizer, payload).payload["amounts"]
        total = next(a for a in amounts if a["amount_type"] == "TOTAL_VALUE")
        assert total["amounts"] == ["12345678901234567.89"]

    def test_a_raw_binary_float_is_refused_rather_than_rounded(self, normalizer) -> None:
        """A float never reaches this adapter in production, because the raw
        payload is read back with `parse_float=Decimal`. If one ever did, it is
        refused: silently accepting it would put a binary approximation into the
        field that decides what a contract was worth."""
        record = raw({**fx.AWARD_NOTICE, "total-value": 1875000.50})
        with pytest.raises(NormalizationFailedError):
            normalizer.normalize(record, correlation_id="mission-1.15.8-test", normalized_at=MOMENT)

    def test_no_currency_is_converted(self, normalizer) -> None:
        """§17. A SEK lot beside two EUR lots stays SEK."""
        amounts = normalize(normalizer, fx.MULTI_LOT_NOTICE).payload["amounts"]
        tender = next(a for a in amounts if a["amount_type"] == "TENDER_VALUE")
        assert tender["currencies"] == ["EUR", "EUR", "SEK"]

    def test_a_single_pair_is_established(self, normalizer) -> None:
        amounts = normalize(normalizer, fx.AWARD_NOTICE).payload["amounts"]
        total = next(a for a in amounts if a["amount_type"] == "TOTAL_VALUE")
        assert total["pairing"] == "ESTABLISHED"

    def test_several_amounts_are_not_paired_by_index(self, normalizer) -> None:
        """§16. The source declares both as arrays and states nothing about
        positional correspondence, so both sequences are preserved unpaired."""
        draft = normalize(normalizer, fx.MULTI_LOT_NOTICE)
        tender = next(a for a in draft.payload["amounts"] if a["amount_type"] == "TENDER_VALUE")
        assert tender["pairing"] == "NOT_ESTABLISHED"
        assert "MONETARY_PAIRING_NOT_ESTABLISHED" in reason_codes(draft)

    def test_an_amount_with_no_currency_is_kept_and_flagged(self, normalizer) -> None:
        payload = {k: v for k, v in fx.AWARD_NOTICE.items() if k != "total-value-cur"}
        draft = normalize(normalizer, payload)
        total = next(a for a in draft.payload["amounts"] if a["amount_type"] == "TOTAL_VALUE")
        assert total["currencies"] == []
        assert "MONETARY_CURRENCY_ABSENT" in reason_codes(draft)

    def test_a_malformed_amount_is_drift(self, normalizer) -> None:
        with pytest.raises(NormalizationFailedError) as caught:
            normalize(normalizer, {**fx.AWARD_NOTICE, "total-value": "about a million"})
        assert "drift" in caught.value.failure.detail

    def test_an_unknown_semantic_cannot_be_constructed(self) -> None:
        """§19. An amount whose meaning is not in the vocabulary is not stored."""
        from sros_acquisition.normalization.model import CanonicalMonetaryAmount

        with pytest.raises(ValueError, match="not an established monetary semantic"):
            CanonicalMonetaryAmount(
                amount_type="GENERIC_AMOUNT",
                source_field="whatever",
                scope="NOTICE",
                amounts=(Decimal("1"),),
                currencies=("EUR",),
                currency_source_field=None,
                pairing="ESTABLISHED",
            )


# ============================================ links, personal data, authenticity


class TestPayloadBoundaries:
    def test_the_links_block_is_not_copied(self, normalizer) -> None:
        """§22. ~94% of a raw record's bytes, and presentation. The RawRecord
        already holds all of it."""
        import json

        payload = {**fx.CONTRACT_NOTICE, "links": fx.LINKS}
        draft = normalize(normalizer, payload)
        text = json.dumps(draft.payload)
        assert "links" not in draft.payload
        assert text.count("ted.europa.eu") <= 2

    def test_two_source_references_are_kept(self, normalizer) -> None:
        payload = {**fx.CONTRACT_NOTICE, "links": fx.LINKS}
        references = normalize(normalizer, payload).payload["source_reference"]
        assert set(references) == {"html", "xml"}

    def test_a_notice_with_no_links_has_no_references(self, normalizer) -> None:
        assert normalize(normalizer, fx.CONTRACT_NOTICE).payload["source_reference"] == {}

    def test_a_personal_data_field_is_never_promoted(self, normalizer) -> None:
        """§23. Visible refusal, not silent canonical data."""
        import json

        payload = {**fx.CONTRACT_NOTICE, "organisation-email-tenderer": ["x@example.invalid"]}
        draft = normalize(normalizer, payload)
        assert "PERSONAL_DATA_FIELD_NOT_PROMOTED" in reason_codes(draft)
        assert "x@example.invalid" not in json.dumps(draft.payload)

    def test_a_clean_notice_raises_no_personal_data_reason(self, normalizer) -> None:
        assert "PERSONAL_DATA_FIELD_NOT_PROMOTED" not in reason_codes(
            normalize(normalizer, fx.CONTRACT_NOTICE)
        )

    def test_the_record_carries_its_attribution(self, normalizer) -> None:
        """§24. A normalized notice supports *TED reported ...* and nothing
        stronger, and the credit travels with it."""
        draft = normalize(normalizer, fx.CONTRACT_NOTICE)
        assert draft.provenance["attribution"]["text"].startswith("Tenders Electronic Daily")

    def test_provenance_links_back_to_the_raw_record(self, normalizer) -> None:
        """§25."""
        draft = normalize(normalizer, fx.CONTRACT_NOTICE)
        assert draft.raw_record_id == "aaaaaaaa-0000-0000-0000-000000000001"
        assert draft.collector_id == "ted-search-api"
        assert draft.collector_version == "1.0.0"
        assert draft.normalizer_id == TED_NORMALIZER_ID
        assert draft.normalizer_version == TED_NORMALIZER_VERSION
        assert draft.review_version == 2


# ================================================================ the fences


def test_the_normalizer_never_names_price_paid() -> None:
    """§42, asserted over the AST rather than over the text, so the paragraph
    explaining the rule cannot fail it."""
    tree = ast.parse(NORMALIZER_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id != "price_paid"
        # A docstring may explain what is forbidden; a value may not BE it.
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.strip() == "price_paid"
        ):
            raise AssertionError("price_paid appears as a value")


def test_the_normalizer_converts_no_currency() -> None:
    tree = ast.parse(NORMALIZER_SOURCE.read_text(encoding="utf-8"))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    for token in ("exchange_rate", "to_eur", "convert_currency", "fx_rate"):
        assert token not in names, token


def test_the_normalizer_uses_no_float() -> None:
    """§18. `decimal_from` is the one converter, and it never routes through a
    binary float."""
    tree = ast.parse(NORMALIZER_SOURCE.read_text(encoding="utf-8"))
    calls = {
        n.func.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "float" not in calls


def test_the_normalizer_reaches_no_network_and_no_database() -> None:
    tree = ast.parse(NORMALIZER_SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"httpx", "requests", "urllib", "psycopg", "socket"}


def test_no_test_in_this_file_reaches_the_network() -> None:
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"httpx", "requests", "urllib", "aiohttp", "socket"}
