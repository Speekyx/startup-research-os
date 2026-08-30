"""The GDELT WEB-NGRAM normalizer.

Mission 1.10.1. The second adapter, and the first that produces a canonical
shape other than a numeric observation.

**Pure, deterministic transformation.** It reads a `RawRecordView` and produces
a canonical `LexicalFrequencyObservation`. It opens no socket, fetches no
metadata, consults no language table, calls no model and creates no signal,
claim, embedding or score. CI asserts the network and model bans mechanically
rather than trusting this paragraph.

**Everything it cannot establish stays unestablished, and says so.** Two facts
are known to be missing and both are represented rather than filled in:

    H-29  GDELT documents no timezone for the DATE bucket, so the period's
          bounds are timezone-NAIVE and `observed_at` is NULL
    H-30  no CLD2-to-language-tag mapping is established, so the language
          carries its source label and no canonical tag

Every record this adapter produces is therefore **PARTIAL**, and that is the
design rather than a defect: two things a consumer would reasonably expect are
absent, both have a canonical reason code, and marking the records VALID would
say nothing is missing when two known things are.

**The gram size comes from the resource, never from the text.** Counting spaces
in the term would make a two-word entry in a unigram file look like a bigram
instead of surfacing it as the contract violation it would be — so a payload
whose own `gram_kind` contradicts its resource id is refused rather than
quietly corrected.

What it does NOT do: interpret, classify, embed, cluster or score. It maps one
source-native observation into one canonical observation and stops.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sros_contracts import (
    NormalizationErrorCode,
    NormalizationQualityReason,
    NormalizedPeriodType,
    NormalizedRecordQuality,
    NormalizedTimezoneState,
    NormalizedUnitState,
    NormalizedValueState,
)

from ..registry.retention import EffectiveRetention
from .errors import NormalizationFailedError, NormalizationFailure
from .model import (
    NORMALIZATION_SCHEMA_ID,
    NORMALIZATION_SCHEMA_VERSION,
    CanonicalLanguage,
    CanonicalPeriod,
    CanonicalValue,
    LexicalFrequencyObservation,
    NormalizedRecordDraft,
    QualityAssessment,
    QualityReason,
    RawRecordView,
    build_normalized,
)

__all__ = [
    "GDELT_WEB_NGRAM_NORMALIZER_ID",
    "GDELT_WEB_NGRAM_NORMALIZER_VERSION",
    "GRAM_SIZES",
    "GdeltWebNgramLexicalNormalizer",
]

# §3. Bumped when the PARSE or the canonical mapping changes -- never when a
# message is reworded. Recorded on every row, so a future change cannot make
# existing records unauditable, and bumping it is the mechanism by which output
# is allowed to differ from what is already stored.
#
# The four changes that would require one are named in
# `gdelt-normalization-contract-v1.md` §5.1, and two of them are the open
# questions above: answering H-29 or H-30 changes what a record MEANS.
GDELT_WEB_NGRAM_NORMALIZER_ID = "gdelt-web-ngram-lexical"
GDELT_WEB_NGRAM_NORMALIZER_VERSION = "1.0.0"

_SOURCE_ID = "gdelt"
_COLLECTOR_ID = "gdelt-web-ngram"

# The two resources GDELT review 3 authorised, and the gram size each one means.
# **This mapping is the only source of gram size** (§9): the resource id is a
# governance fact recorded at collection, and the term's text is not.
GRAM_SIZES: dict[str, int] = {
    "web-ngrams/1gram": 1,
    "web-ngrams/2gram": 2,
}

_TERM_SCHEME = "gdelt-web-ngram"
_LANGUAGE_SCHEME = "cld2-language-name"
_BUCKET_MINUTES = 15
_ALIGNED_MINUTES = frozenset({0, 15, 30, 45})
_BUCKET_LENGTH = 14


class GdeltWebNgramLexicalNormalizer:
    """Maps GDELT WEB-NGRAM rows to canonical lexical frequency observations."""

    normalizer_id = GDELT_WEB_NGRAM_NORMALIZER_ID
    normalizer_version = GDELT_WEB_NGRAM_NORMALIZER_VERSION
    source_id = _SOURCE_ID
    collector_id = _COLLECTOR_ID
    schema_id = NORMALIZATION_SCHEMA_ID
    schema_version = NORMALIZATION_SCHEMA_VERSION

    # One version, because one exists. Declared rather than assumed: a collector
    # version this adapter has never seen may have changed the payload shape,
    # and a parse that half-works on an unknown shape is worse than one that
    # stops.
    supported_collector_versions: frozenset[str] = frozenset({"1.0.0"})

    def __init__(self, retention: EffectiveRetention) -> None:
        # Governance input, never a normalizer's choice. It arrives resolved --
        # `resolve_retention` has already taken the stricter of the baseline and
        # any source override, in that direction only -- so there is no argument
        # here through which a longer window could be requested.
        #
        # No geography map, unlike the World Bank adapter: a WEB-NGRAM row has
        # no geography, and holding a classification table it never consults
        # would suggest it might.
        self.retention = retention

    # -------------------------------------------------------------- entry point

    def normalize(
        self, record: RawRecordView, *, correlation_id: str, normalized_at: datetime
    ) -> NormalizedRecordDraft:
        """One raw record into one canonical record.

        Raises only when NO record can be produced -- a record from the wrong
        source, an unreviewed resource, or a payload whose own fields contradict
        each other. A record that CAN be produced and is incomplete comes back
        with a quality state and reasons, because discarding it would make a
        normalizer defect look like a source that returned nothing.
        """
        payload = self._accept(record, correlation_id)

        reasons: list[QualityReason] = []
        observation = self._observation(record, payload, reasons, correlation_id)
        assessment = self._assess(reasons)

        return build_normalized(
            record,
            observation,
            assessment,
            self.retention,
            normalizer_id=self.normalizer_id,
            normalizer_version=self.normalizer_version,
            normalized_at=normalized_at,
            correlation_id=correlation_id,
            schema_id=self.schema_id,
            schema_version=self.schema_version,
        )

    # --------------------------------------------------------------- acceptance

    def _accept(self, record: RawRecordView, correlation_id: str) -> dict[str, object]:
        """§4. Refuse anything this adapter does not serve, before mapping.

        Defence in depth: `select_normalizer` already refuses a wrong source or
        an unsupported collector version, and a guard that only exists further
        up is one a future caller can route around -- the same argument the
        transport makes for re-checking its host allowlist.
        """
        if record.source_id != self.source_id:
            raise self._refuse(
                record,
                correlation_id,
                NormalizationErrorCode.UNSUPPORTED_SOURCE,
                f"this normalizer serves {self.source_id!r} and was handed a record from "
                f"{record.source_id!r}. One source's shape never describes another's",
            )
        if record.collector_id != self.collector_id:
            raise self._refuse(
                record,
                correlation_id,
                NormalizationErrorCode.UNSUPPORTED_SOURCE,
                f"this normalizer reads what {self.collector_id!r} writes and was handed a "
                f"record from {record.collector_id!r}. A second collector for one source "
                "parses a different shape",
            )
        payload = record.payload
        if not payload:
            raise self._refuse(
                record,
                correlation_id,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record carries no payload, so there is nothing to normalize. Never "
                "repaired: the raw layer records what the source returned",
            )

        resource_id = _text(payload.get("resource_id"))
        if resource_id not in GRAM_SIZES:
            # §4. `web-ngrams/3gram`, NGrams 3.0, the quadgram files, a DOC API
            # mode -- none has a reviewed canonical shape, and guessing one
            # would produce records that look right and are not.
            raise self._refuse(
                record,
                correlation_id,
                NormalizationErrorCode.UNSUPPORTED_SOURCE,
                f"{resource_id!r} is not a resource this adapter represents. GDELT review 3 "
                f"assessed {sorted(GRAM_SIZES)} and nothing else",
            )

        # §9. The payload's own `gram_kind` against the resource it claims to
        # come from. A contradiction means the record is not what it says it is,
        # and correcting it silently would pick a winner between two source
        # facts -- so the record fails instead.
        gram_kind = _text(payload.get("gram_kind"))
        if gram_kind and not resource_id.endswith(f"/{gram_kind}"):
            raise self._refuse(
                record,
                correlation_id,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                f"the payload says gram kind {gram_kind!r} and resource {resource_id!r}, "
                "which disagree. Neither is corrected: choosing one would decide which of "
                "two source facts to believe",
            )
        return payload

    def _refuse(
        self,
        record: RawRecordView,
        correlation_id: str,
        code: NormalizationErrorCode,
        detail: str,
    ) -> NormalizationFailedError:
        return NormalizationFailedError(
            NormalizationFailure(
                code=code,
                detail=detail,
                source_id=record.source_id,
                raw_record_id=record.record_id,
                correlation_id=correlation_id,
            )
        )

    # ------------------------------------------------------------------ mapping

    def _observation(
        self,
        record: RawRecordView,
        payload: dict[str, object],
        reasons: list[QualityReason],
        correlation_id: str,
    ) -> LexicalFrequencyObservation:
        """Build the canonical payload.

        The reasons are appended in a FIXED order -- period, language, value --
        so two runs over one record produce byte-identical quality reasons (§16).
        Nothing here sorts them afterwards, because the order they are collected
        in is already the order a reader wants: what the observation is about,
        then what it measures.
        """
        resource_id = _text(payload.get("resource_id"))
        # §9. VERBATIM: `_source_text` does not strip. A term the source
        # published with an edge space is that term, and returning a trimmed one
        # would put a value GDELT never wrote into the payload, the fingerprint
        # and the observation's identity -- invisibly, because the difference is
        # whitespace.
        term = _source_text(payload.get("ngram"))
        language_label = _source_text(payload.get("lang"))

        # Both are `required` for this record kind and the collector's own parser
        # refuses an empty one, so a record arriving without them is not a
        # WEB-NGRAM row. Refused rather than stored as INVALID: there is nothing
        # to represent, not merely something missing.
        # Whitespace-only is not a term, and neither is empty. Checked on the
        # STRIPPED value while the unstripped one is what gets stored: the two
        # questions are different, and only the second is about what the source
        # said.
        if not term.strip():
            raise self._refuse(
                record,
                correlation_id,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw payload carries no ngram, so there is no term the count is a frequency OF",
            )
        if not language_label.strip():
            raise self._refuse(
                record,
                correlation_id,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw payload carries no language label, and a WEB-NGRAM frequency is "
                "counted within one language",
            )

        # Built in this order so the quality reasons come out in it: when the
        # observation is, then what language it is in, then what it measures.
        # `_assess` does not sort afterwards, so the collection order IS the
        # output order and §16's determinism is a property of this sequence.
        period = self._period(payload, reasons)
        language = self._language(language_label, reasons)
        value = self._value(payload, reasons)

        return LexicalFrequencyObservation(
            # §9. Verbatim. Not normalised, not case-folded, not stripped of
            # anything the source published.
            term_text=term,
            # §9. From the RESOURCE, never from the text.
            term_gram_size=GRAM_SIZES[resource_id],
            term_scheme=_TERM_SCHEME,
            language=language,
            value=value,
            period=period,
            dataset=_text(record.provenance.get("dataset_family")) or None,
            resource_id=resource_id,
            # GDELT publishes no revision stamp for a bucket file. An absence,
            # recorded faithfully.
            source_last_updated=None,
        )

    # ------------------------------------------------------------------- period

    def _period(self, payload: dict[str, object], reasons: list[QualityReason]) -> CanonicalPeriod:
        """§6, §7. A 15-minute interval with **no timezone assigned**.

        The bounds are timezone-NAIVE, which is what a wall-clock reading with no
        offset actually is. Nothing here calls `astimezone`, reads the machine's
        zone, appends `Z`, or infers one from where GDELT is hosted — and H-29
        stays open in a form a future normalizer version can resolve without
        reacquiring anything, because the exact source label survives in
        `period.label` and in the payload.
        """
        # Unstripped, like the term: a padded label is not a valid bucket label
        # and `_parse_bucket` refuses it, which is more honest than trimming it
        # into one the source did not publish.
        label = _source_text(payload.get("date"))
        start = _parse_bucket(label)
        if start is None:
            reasons.append(
                QualityReason(
                    code=NormalizationQualityReason.PERIOD_NOT_SUPPORTED,
                    detail=(
                        f"{label!r} is not a 15-minute bucket label in the documented "
                        "YYYYMMDDHHMMSS form on the published quarter-hour grid. Reported "
                        "rather than approximated: a moment the source did not state would "
                        "be invented"
                    ),
                    field_path="period",
                )
            )
            # A sentinel so the record can still be stored and audited. Reachable
            # only alongside PERIOD_NOT_SUPPORTED, which makes the record
            # INVALID, so nothing reads it as a time.
            start = datetime(1970, 1, 1)  # noqa: DTZ001 - naive by contract, see the docstring
        else:
            reasons.append(
                QualityReason(
                    code=NormalizationQualityReason.PERIOD_TIMEZONE_NOT_ESTABLISHED,
                    detail=(
                        "GDELT publishes this bucket label with no offset and states no "
                        "timezone in its documentation, so the bounds are wall-clock "
                        "readings and no event time is claimed (H-29)"
                    ),
                    field_path="period.timezone_state",
                )
            )
        return CanonicalPeriod(
            type=NormalizedPeriodType.INTERVAL,
            label=label,
            start=start,
            end=start + timedelta(minutes=_BUCKET_MINUTES),
            end_inclusive=False,
            timezone_state=NormalizedTimezoneState.NOT_ESTABLISHED,
        )

    # ----------------------------------------------------------------- language

    def _language(self, label: str, reasons: list[QualityReason]) -> CanonicalLanguage:
        """§8. The source label, and no tag.

        `ENGLISH` is not `en`. The resemblance is exactly why this is dangerous:
        the mapping is obvious for the labels a reader thinks of and silently
        wrong for the first one they do not — a CLD2 name with an underscore, or
        a distinction ISO 639 draws that CLD2 does not. H-30 is unresolved and
        this adapter resolves nothing.
        """
        reasons.append(
            QualityReason(
                code=NormalizationQualityReason.LANGUAGE_NOT_MAPPED,
                detail=(
                    f"{label!r} is a CLD2 human-readable language name and no reviewed "
                    "mapping to a language tag exists, so the label is preserved and no "
                    "tag is assigned (H-30)"
                ),
                field_path="language.canonical_tag",
            )
        )
        return CanonicalLanguage.unmapped(label, _LANGUAGE_SCHEME)

    # -------------------------------------------------------------------- value

    def _value(self, payload: dict[str, object], reasons: list[QualityReason]) -> CanonicalValue:
        """§11, §12. An exact non-negative integer, with no unit.

        The count arrives as the canonical decimal STRING the collector wrote, so
        it never passes through a float on either side of persistence. Values
        above 2**53 survive exactly, which a JSON number would not.
        """
        raw = payload.get("count")
        exact = _exact_count(raw)
        if exact is None:
            reasons.append(
                QualityReason(
                    code=NormalizationQualityReason.MALFORMED_NUMERIC_VALUE,
                    detail=(
                        "the count could not be read as an exact non-negative integer. "
                        "GDELT documents it as the number of times the term was mentioned, "
                        "and a value that is not one is not a smaller count"
                    ),
                    field_path="observation.value",
                )
            )
            return CanonicalValue(
                value=None,
                state=NormalizedValueState.UNREADABLE,
                unit=None,
                # §12. The Mission 1.10 decision, applied unchanged: the file has
                # four columns and none is a unit, and the record kind already
                # says the number is an occurrence count over a window.
                unit_state=NormalizedUnitState.NOT_PUBLISHED,
            )
        return CanonicalValue(
            value=exact,
            # A zero count is the source saying "none in this bucket", which is a
            # measurement. NOT_REPORTED would make it indistinguishable from a
            # term the file never listed.
            state=NormalizedValueState.REPORTED,
            unit=None,
            unit_state=NormalizedUnitState.NOT_PUBLISHED,
            # GDELT publishes no decimal metadata; World Bank's comes from a
            # field its API sends.
            decimals=None,
        )

    # ------------------------------------------------------------------ quality

    @staticmethod
    def _assess(reasons: list[QualityReason]) -> QualityAssessment:
        """§15. PARTIAL is the expected state, and INVALID beats it.

        Every record carries the two open-question reasons, so `VALID` is
        unreachable for this adapter by construction — and that is honest rather
        than defeatist: two canonical facts a consumer would expect really are
        missing, and a state saying nothing is missing would be false.

        The fatal set contains only genuine defects. **H-29 and H-30 are not in
        it**: a known, representable absence is not a reason to make a record
        unreadable.
        """
        fatal = {NormalizationQualityReason.PERIOD_NOT_SUPPORTED}
        if any(reason.code in fatal for reason in reasons):
            state = NormalizedRecordQuality.INVALID
        elif reasons:
            state = NormalizedRecordQuality.PARTIAL
        else:  # pragma: no cover - unreachable while H-29 and H-30 are open
            state = NormalizedRecordQuality.VALID
        return QualityAssessment(state=state, reasons=tuple(reasons))


def _parse_bucket(label: str) -> datetime | None:
    """A source bucket label as naive wall-clock bounds, or `None`.

    Validated the same way the collector validates it, on purpose: this is the
    defensive second read §6 asks for, and a normalizer that trusted the
    collector's validation would be trusting a version of it that may since have
    changed.

    **Returns a NAIVE datetime.** No `tzinfo`, no `astimezone`, no `Z`. The
    result is a wall-clock reading because that is all GDELT published.
    """
    if len(label) != _BUCKET_LENGTH or not label.isdigit():
        return None
    year, month, day = int(label[0:4]), int(label[4:6]), int(label[6:8])
    hour, minute, second = int(label[8:10]), int(label[10:12]), int(label[12:14])
    if minute not in _ALIGNED_MINUTES or second != 0:
        return None
    try:
        return datetime(year, month, day, hour, minute)  # noqa: DTZ001 - naive by contract
    except ValueError:
        return None


def _exact_count(value: object) -> Decimal | None:
    """A non-negative integer count, exactly, or `None`.

    Accepts the canonical decimal string the collector writes and an `int`, and
    refuses everything else -- including a `float`, which has already been
    through IEEE-754 and would bake in the rounding this layer exists to avoid.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Decimal(value) if value >= 0 else None
    if isinstance(value, Decimal):
        return value if value >= 0 and value == value.to_integral_value() else None
    if isinstance(value, str):
        text = value.strip()
        # `isdigit` rejects a sign, a decimal point and whitespace in one test.
        return Decimal(text) if text.isdigit() else None
    return None


def _text(value: object) -> str:
    """A string from OUR OWN provenance or configuration, trimmed.

    Safe to strip because these are values this codebase wrote -- a resource id,
    a dataset family. Never used on something the source published.
    """
    return str(value).strip() if isinstance(value, str) else ""


def _source_text(value: object) -> str:
    """A string the SOURCE published, exactly as it published it.

    Not trimmed, not case-folded, not normalised. §9: what reaches the payload,
    the fingerprint and the observation identity has to be what GDELT wrote, and
    a whitespace difference is the kind that is impossible to notice later.
    """
    return value if isinstance(value, str) else ""
