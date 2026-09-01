"""TED Search API notices into canonical procurement notices. Mission 1.15.8.

**One notice in, one notice out.** Lots are structured data on the record, never
records of their own: TED publishes one notice under one publication number, and
a per-lot record would invent an identity the source does not have and make one
publication read as several.

**This layer renames and reshapes. It does not decide.** Four things it
deliberately refuses to do, each because doing it would be an interpretation
wearing a fact's clothes:

**It does not turn a published DATE into a moment.** `publication-date` arrives
as `2023-03-01+01:00` -- a calendar day carrying a UTC offset and no time of
day. The period is that day, its bounds are timezone-NAIVE and `observed_at` is
NULL. See §Temporal below; the choice is argued rather than assumed.

**It does not choose a language.** Organisation names arrive keyed by language
and the Search API request has no language selector, so no source-supported
preference exists. Every language is kept and there is no `display` field to
read as *the* name.

**It does not flatten money.** Four source fields carry four different meanings
and each becomes its own typed entry. There is no `price_paid`, no generic
amount, and an amount whose semantic is not in the vocabulary is not stored.

**It does not pair arrays it cannot prove are aligned.** TED declares amounts
and currencies as arrays and states nothing about positional correspondence, so
pairing is `ESTABLISHED` only where there is one of each.

Temporal, stated in full because it is the mission's hardest question:

    the value      2023-03-01+01:00 -- a DAY, with an offset, and NO time
    the period     DAY, bounds NAIVE, timezone_state NOT_ESTABLISHED
    observed_at    NULL

`ESTABLISHED` was considered and refused. Its own definition is *"the source
states the timezone, or authoritative documentation does"*, and neither has: an
offset appearing inside one value is data, not a statement about what that
offset means, and the API's OpenAPI document describes `publication-date` with
no temporal semantics at all. GDELT needed a `TemporalOrderCertification` --
evidence -- to establish an ordering the labels already implied, and the same
standard applies here. Recorded as **H-37**.

And there is no time of day in the value under any reading, so an instant would
have to be chosen. Midnight is the choice that looks like no choice.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sros_contracts import (
    NormalizationErrorCode,
    NormalizationQualityReason,
    NormalizedPeriodType,
    NormalizedRecordQuality,
    NormalizedTimezoneState,
)

from ..registry.retention import EffectiveRetention
from .errors import NormalizationFailedError, NormalizationFailure
from .model import (
    NORMALIZATION_SCHEMA_ID,
    NORMALIZATION_SCHEMA_VERSION,
    NOTICE_TYPE_CLASSES,
    CanonicalClassification,
    CanonicalMonetaryAmount,
    CanonicalMultilingualText,
    CanonicalPeriod,
    NormalizedRecordDraft,
    ProcurementNoticeObservation,
    QualityAssessment,
    QualityReason,
    RawRecordView,
    build_normalized,
    decimal_from,
)

__all__ = [
    "MONETARY_FIELDS",
    "TED_NORMALIZER_ID",
    "TED_NORMALIZER_VERSION",
    "TED_RESOURCE_ID",
    "TedSearchApiNoticeNormalizer",
]

TED_NORMALIZER_ID = "ted-search-api-notice"
# 1.0.0. A changed SEMANTIC mapping -- a different notice class, a promoted
# `observed_at`, a currency paired where it was not -- is a version bump, never
# a quiet reinterpretation of records already written.
TED_NORMALIZER_VERSION = "1.0.0"

TED_SOURCE_ID = "ted-eu"
TED_COLLECTOR_ID = "ted-search-api"
TED_RESOURCE_ID = "notices/eforms-contract-and-award"
TED_DATASET_FAMILY = "ted-search-api-notices"

# The four monetary semantics, each bound to the one source field that carries
# it and the one currency field that accompanies it. A table rather than a rule,
# so a reader can check the mapping instead of deducing it.
MONETARY_FIELDS: tuple[tuple[str, str, str | None, str], ...] = (
    ("total-value", "TOTAL_VALUE", "total-value-cur", "NOTICE"),
    ("tender-value", "TENDER_VALUE", "tender-value-cur", "LOT"),
    ("estimated-value-lot", "ESTIMATED_VALUE", "estimated-value-cur-lot", "LOT"),
    (
        "framework-maximum-value-lot",
        "FRAMEWORK_MAXIMUM",
        "framework-maximum-value-cur-lot",
        "LOT",
    ),
)

# What a normalized notice may carry from the `links` block TED attaches to every
# response. Two references, not the block: the block is ~94% of a raw record's
# bytes, it is presentation, and the RawRecord already holds all of it. Copying
# it here would put kilobytes of per-language URLs into every canonical record
# for no canonical purpose.
SOURCE_REFERENCE_FORMATS = ("html", "xml")
SOURCE_REFERENCE_LANGUAGE = "ENG"

# The natural-person keys the review excludes. None was requested and none has
# been received, and this normalizer refuses to promote one if a future record
# carries it anyway -- §23 asks for visible refusal rather than silent canonical
# data, and a field nobody asked for arriving is exactly when that matters.
PROHIBITED_KEY_MARKERS = (
    "contact",
    "email",
    "tel",
    "fax",
    "ubo",
    "person",
    "postal",
    "street",
)

_DATE_WITH_OFFSET = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(Z|[+-]\d{2}:\d{2})?$")


@dataclass(frozen=True)
class _Publication:
    """The publication date as the source wrote it, beside the period built from it."""

    source_value: str
    utc_offset: str | None
    precision: str = "DAY"
    offset_semantics: str = "NOT_ESTABLISHED"


class TedSearchApiNoticeNormalizer:
    """One TED notice into one canonical procurement notice."""

    normalizer_id = TED_NORMALIZER_ID
    normalizer_version = TED_NORMALIZER_VERSION
    source_id = TED_SOURCE_ID
    schema_id = NORMALIZATION_SCHEMA_ID
    schema_version = NORMALIZATION_SCHEMA_VERSION

    def __init__(self, retention: EffectiveRetention) -> None:
        self._retention = retention

    def normalize(
        self, record: RawRecordView, *, correlation_id: str, normalized_at: datetime
    ) -> NormalizedRecordDraft:
        self._require_lineage(record)
        payload = record.payload
        reasons: list[QualityReason] = []

        publication_number = _text(payload.get("publication-number"))
        if not publication_number:
            # §29. Defensive: collection already refuses this. A raw record with
            # no source identity cannot become a canonical one, because the
            # canonical identity would have to be invented.
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record carries no 'publication-number', so the notice has no "
                "source-native identity and none may be constructed for it",
            )

        source_type = _text(payload.get("notice-type"))
        notice_class = NOTICE_TYPE_CLASSES.get(source_type or "")
        if notice_class is None:
            raise self._fail(
                record,
                NormalizationErrorCode.UNSUPPORTED_RECORD_TYPE,
                f"notice type {source_type!r} is outside the authorised resource, which "
                f"contains {sorted(NOTICE_TYPE_CLASSES)} and nothing else. Classifying it "
                "anyway would normalise a notice family nobody reviewed",
            )

        period, publication = self._period(record, payload, reasons)
        amounts = self._amounts(record, payload, reasons)
        buyer = self._organisations(record, payload, "organisation-name-buyer", reasons)
        tenderer = self._organisations(record, payload, "organisation-name-tenderer", reasons)
        self._refuse_personal_data(record, payload, reasons)

        observation = ProcurementNoticeObservation(
            publication_number=publication_number,
            notice_class=notice_class,
            source_type=source_type or "",
            source_type_scheme="ted-notice-type",
            period=period,
            publication_source_value=publication.source_value,
            publication_precision=publication.precision,
            publication_utc_offset=publication.utc_offset,
            publication_offset_semantics=publication.offset_semantics,
            notice_identifier=_text(payload.get("notice-identifier")),
            notice_version=_int(payload.get("notice-version")),
            form_type=_text(payload.get("form-type")),
            contract_nature=_strings(payload.get("contract-nature")),
            classifications=tuple(
                CanonicalClassification(code=code, scheme="CPV")
                for code in _strings(payload.get("classification-cpv"))
            ),
            buyer_organisations=buyer,
            tenderer_organisations=tenderer,
            award_selection_status=_strings(payload.get("winner-selection-status")),
            # Kept as the source's own strings. §9: three date concepts, and the
            # two below have had no temporal semantics established either -- so
            # they are preserved verbatim rather than parsed into a shape that
            # would imply one.
            award_decision_dates=_strings(payload.get("winner-decision-date")),
            contract_conclusion_dates=_strings(payload.get("contract-conclusion-date")),
            buyer_countries=_strings(payload.get("organisation-country-buyer")),
            performance_countries=_strings(payload.get("place-of-performance-country-lot")),
            performance_subdivisions=_strings(payload.get("place-of-performance-subdiv-lot")),
            amounts=amounts,
            resource_id=_provenance_text(record, "resource_id"),
            source_reference=self._source_reference(payload),
        )

        return build_normalized(
            record,
            observation,
            self._assess(reasons),
            self._retention,
            normalizer_id=self.normalizer_id,
            normalizer_version=self.normalizer_version,
            normalized_at=normalized_at,
            correlation_id=correlation_id,
            schema_id=self.schema_id,
            schema_version=self.schema_version,
        )

    @staticmethod
    def _assess(reasons: list[QualityReason]) -> QualityAssessment:
        """PARTIAL is the expected state for every TED notice written today.

        Each one carries `PERIOD_TIMEZONE_NOT_ESTABLISHED`, because H-37 is open
        for every record rather than for unlucky ones -- so `VALID` is
        unreachable for this adapter by construction, exactly as it is for
        GDELT. That is honest rather than unfortunate: the alternative is a
        record that reads as complete while an open question sits inside its
        period.

        `INVALID` is not reachable here either, and for a different reason: a
        record missing something the kind requires raises instead, so a draft
        that exists has its required fields.
        """
        return QualityAssessment(
            state=(NormalizedRecordQuality.PARTIAL if reasons else NormalizedRecordQuality.VALID),
            reasons=tuple(reasons),
        )

    # --------------------------------------------------------------- lineage

    def _require_lineage(self, record: RawRecordView) -> None:
        """§5. The provenance must say this record came from what this reads.

        Checked against the RECORD's provenance rather than trusted from the
        registry key, because the registry answers *which adapter serves this
        source and collector* and this answers *is this particular record the
        thing that adapter parses*. A bulk XML package, an ODS result or an
        unreviewed TED resource would fail here even if it somehow arrived with
        the right collector id.
        """
        if record.source_id != TED_SOURCE_ID:
            raise self._fail(
                record,
                NormalizationErrorCode.UNSUPPORTED_SOURCE,
                f"{record.source_id!r} is not {TED_SOURCE_ID!r}",
            )
        if record.collector_id != TED_COLLECTOR_ID:
            raise self._fail(
                record,
                NormalizationErrorCode.UNSUPPORTED_SOURCE,
                f"collector {record.collector_id!r} is not {TED_COLLECTOR_ID!r}; a "
                "different collector parses a different shape, and a parse that "
                "half-works on an unknown one is worse than one that stops",
            )
        resource = _provenance_text(record, "resource_id")
        if resource != TED_RESOURCE_ID:
            raise self._fail(
                record,
                NormalizationErrorCode.UNSUPPORTED_RECORD_TYPE,
                f"resource {resource!r} is not the authorised {TED_RESOURCE_ID!r}. Bulk "
                "packages, the historical CSV and the SPARQL route are refused here as "
                "well as at acquisition",
            )
        family = _provenance_text(record, "dataset_family")
        if family != TED_DATASET_FAMILY:
            raise self._fail(
                record,
                NormalizationErrorCode.UNSUPPORTED_RECORD_TYPE,
                f"dataset family {family!r} is not {TED_DATASET_FAMILY!r}",
            )

    # -------------------------------------------------------------- temporal

    def _period(
        self, record: RawRecordView, payload: Mapping[str, object], reasons: list[QualityReason]
    ) -> tuple[CanonicalPeriod, _Publication]:
        """The publication DAY, with naive bounds and no moment. See the module docstring."""
        source_value = _text(payload.get("publication-date"))
        if not source_value:
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record carries no 'publication-date', and the record kind "
                "requires a period. A notice with no published date has no interval to "
                "record, and inventing one from the collection time would date the "
                "notice by when we happened to fetch it",
            )
        match = _DATE_WITH_OFFSET.match(source_value)
        if match is None:
            # §30. A known field whose shape changed incompatibly is drift, not
            # an absence: stringifying it would hide a source change behind a
            # record that looks complete.
            raise self._fail(
                record,
                NormalizationErrorCode.UNSUPPORTED_RECORD_TYPE,
                f"'publication-date' is {source_value!r}, which is not the "
                "YYYY-MM-DD[offset] shape every observed value and the source's own "
                "schema carry. This is a response-contract change, not a missing value",
            )
        year, month, day, offset = match.groups()
        # NAIVE by construction, and the linter's suggestion to pass a tzinfo is
        # exactly what this must not do: a `timezone.utc` here would be the
        # invented offset H-37 exists to avoid, in the one field a consumer
        # trusts most. The period's own `timezone_state` says so, and
        # `CanonicalPeriod` refuses an aware bound under it.
        start = datetime(int(year), int(month), int(day))  # noqa: DTZ001
        end = _next_day(start)

        reasons.append(
            QualityReason(
                code=NormalizationQualityReason.PERIOD_TIMEZONE_NOT_ESTABLISHED,
                detail=(
                    "TED publishes a UTC offset inside the publication date and no "
                    "documentation of what it means, and the value carries no time of "
                    "day. The period is the published day with NAIVE bounds and "
                    "observed_at is null (H-37)"
                ),
            )
        )
        period = CanonicalPeriod(
            type=NormalizedPeriodType.DAY,
            label=source_value,
            start=start,
            end=end,
            timezone_state=NormalizedTimezoneState.NOT_ESTABLISHED,
        )
        # Named so the open question travels with the record rather than living
        # only in a document.
        return period, _Publication(source_value=source_value, utc_offset=offset)

    # --------------------------------------------------------------- amounts

    def _amounts(
        self, record: RawRecordView, payload: Mapping[str, object], reasons: list[QualityReason]
    ) -> tuple[CanonicalMonetaryAmount, ...]:
        """One typed entry per source field that carries a value. §15, §16, §19."""
        entries: list[CanonicalMonetaryAmount] = []
        for field_name, amount_type, currency_field, scope in MONETARY_FIELDS:
            raw_amount = payload.get(field_name)
            if raw_amount is None:
                # An absent monetary block is an absence, not a zero and not a
                # failure: a contract notice has no total value because no award
                # has happened. §28.
                continue
            amounts = _decimals(raw_amount)
            if amounts is None:
                raise self._fail(
                    record,
                    NormalizationErrorCode.UNSUPPORTED_RECORD_TYPE,
                    f"{field_name!r} is not a number or a list of numbers. A monetary "
                    "field whose shape changed is drift; reading it as absent would "
                    "silently lose an amount the source published",
                )
            currencies = _strings(payload.get(currency_field)) if currency_field else ()
            paired = len(amounts) == 1 and len(currencies) == 1
            if not paired:
                reasons.append(
                    QualityReason(
                        code=NormalizationQualityReason.MONETARY_PAIRING_NOT_ESTABLISHED,
                        detail=(
                            f"{field_name!r} carries {len(amounts)} amount(s) and "
                            f"{len(currencies)} currency code(s). The Search API declares "
                            "both as arrays and states nothing about positional "
                            "correspondence, so both are preserved unpaired rather than "
                            "matched by index (H-38)"
                        ),
                    )
                )
            entries.append(
                CanonicalMonetaryAmount(
                    amount_type=amount_type,
                    source_field=field_name,
                    scope=scope,
                    amounts=amounts,
                    currencies=currencies,
                    currency_source_field=currency_field,
                    pairing="ESTABLISHED" if paired else "NOT_ESTABLISHED",
                )
            )
            if not currencies:
                reasons.append(
                    QualityReason(
                        code=NormalizationQualityReason.MONETARY_CURRENCY_ABSENT,
                        detail=(
                            f"{field_name!r} carries an amount and {currency_field!r} "
                            "carries no currency. The amount is kept with its type and "
                            "no currency is inferred from a country"
                        ),
                    )
                )
        return tuple(entries)

    # --------------------------------------------------------- organisations

    def _organisations(
        self,
        record: RawRecordView,
        payload: Mapping[str, object],
        field_name: str,
        reasons: list[QualityReason],
    ) -> CanonicalMultilingualText | None:
        raw = payload.get(field_name)
        if raw is None:
            return None
        value = CanonicalMultilingualText.from_source(raw)
        if value is None:
            raise self._fail(
                record,
                NormalizationErrorCode.UNSUPPORTED_RECORD_TYPE,
                f"{field_name!r} is not the language-keyed object the source's schema "
                "declares. Flattening an unexpected structure into a string is how a "
                "contract change becomes a plausible-looking name",
            )
        return value

    # ------------------------------------------------------- personal data

    def _refuse_personal_data(
        self, record: RawRecordView, payload: Mapping[str, object], reasons: list[QualityReason]
    ) -> None:
        """§23. Nothing here promotes a natural-person field, and it says so.

        No such field was requested and none has arrived. If one does, it is
        NOT promoted -- there is no branch that could, because every field this
        normalizer reads is named explicitly -- and the record is marked so the
        arrival is visible rather than silently dropped.
        """
        offenders = sorted(
            key
            for key in payload
            if any(marker in key.lower() for marker in PROHIBITED_KEY_MARKERS)
        )
        if offenders:
            reasons.append(
                QualityReason(
                    code=NormalizationQualityReason.PERSONAL_DATA_FIELD_NOT_PROMOTED,
                    detail=(
                        f"the raw record carries {offenders}, which the review excludes. "
                        "No such field is read into the canonical payload; the raw record "
                        "keeps what the source sent and this record records that it was "
                        "refused"
                    ),
                )
            )

    # ------------------------------------------------------------ references

    def _source_reference(self, payload: Mapping[str, object]) -> dict[str, str]:
        """Two links, not the block. §22."""
        links = payload.get("links")
        if not isinstance(links, dict):
            return {}
        references: dict[str, str] = {}
        for fmt in SOURCE_REFERENCE_FORMATS:
            by_language = links.get(fmt)
            if isinstance(by_language, dict):
                value = by_language.get(SOURCE_REFERENCE_LANGUAGE)
                if isinstance(value, str) and value:
                    references[fmt] = value
        return references

    # ---------------------------------------------------------------- errors

    def _fail(
        self, record: RawRecordView, code: NormalizationErrorCode, detail: str
    ) -> NormalizationFailedError:
        return NormalizationFailedError(
            NormalizationFailure(
                code=code,
                detail=detail,
                source_id=record.source_id,
                raw_record_id=record.record_id,
                context={"observation_key": record.observation_key},
            )
        )


# ------------------------------------------------------------------ helpers


def _text(value: object) -> str | None:
    """A scalar string, or the single member of a one-element list.

    The response schema declares some fields scalar and some as arrays, and the
    two shapes occur for the same concept. A longer list is NOT reduced: it is a
    real multiplicity and the caller reads it as a sequence.
    """
    if isinstance(value, list):
        value = value[0] if len(value) == 1 else None
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, int | Decimal) and not isinstance(value, bool):
        return str(value)
    return None


def _int(value: object) -> int | None:
    if isinstance(value, list):
        value = value[0] if len(value) == 1 else None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return None


def _strings(value: object) -> tuple[str, ...]:
    """Every string the source published for a field, in source order.

    Source order is preserved rather than sorted: for a per-lot field the
    position is the only thing relating one entry to another, and sorting would
    destroy it.
    """
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value if isinstance(item, str | int | Decimal))
    return ()


def _decimals(value: object) -> tuple[Decimal, ...] | None:
    """Exact decimals, or `None` when the shape is not a number or list of them.

    `decimal_from` is the model's own converter and never routes through a
    binary float. The raw payload reaches normalization parsed with
    `parse_float=Decimal`, so a decimal literal the source published survives
    unrounded all the way to the canonical string.
    """
    items: Sequence[object] = value if isinstance(value, list) else [value]
    out: list[Decimal] = []
    for item in items:
        if isinstance(item, bool):
            return None
        number = decimal_from(item)
        if number is None:
            return None
        out.append(number)
    return tuple(out) if out else None


def _provenance_text(record: RawRecordView, key: str) -> str | None:
    value = record.provenance.get(key)
    return value if isinstance(value, str) else None


def _next_day(moment: datetime) -> datetime:
    """The day after, by calendar arithmetic that crosses months and years."""
    from datetime import timedelta

    return moment + timedelta(days=1)
