"""The canonical normalized model: what a source observation structurally is.

Mission 1.6 §5, §6, §11–§17, §21–§26. Full specification:
`docs/data/normalized-record-v1.md`.

**This layer renames and reshapes. It does not decide.** A field here that
encoded "this indicates growing demand" would put an interpretation somewhere
that looks like a fact, and every stage downstream would inherit it as one.
Normalization answers *what does this source observation structurally
represent*, and stops.

Three identities are kept apart, one level up from the raw layer's three:

    observation_key    WHICH observation. Inherited verbatim; stable across
                       revisions AND across normalizer versions
    raw_record_id      WHAT the source said, and when. A revision is a
                       different raw record
    record id          WHICH transformation of that. Derived from the raw
                       record and both version numbers

The normalization timestamp is in none of them (§22). Putting it in any would
make every re-run a new representation -- the same trap the raw layer avoided by
keeping the retrieval time out of `content_hash`.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Protocol

from sros_contracts import (
    NormalizationQualityReason,
    NormalizedGeographyKind,
    NormalizedLanguageMapping,
    NormalizedPeriodType,
    NormalizedRecordQuality,
    NormalizedTimezoneState,
    NormalizedUnitState,
    NormalizedValueState,
)

from ..registry.retention import EffectiveRetention
from .geography import GeographyEntry

__all__ = [
    "NORMALIZATION_SCHEMA_ID",
    "NORMALIZATION_SCHEMA_VERSION",
    "NORMALIZED_NAMESPACE",
    "RECORD_KINDS",
    "RECORD_KIND_REGISTRY",
    "CanonicalClassification",
    "CanonicalGeography",
    "CanonicalLanguage",
    "CanonicalObservation",
    "CanonicalPeriod",
    "CanonicalValue",
    "CanonicalMonetaryAmount",
    "CanonicalMultilingualText",
    "MONETARY_AMOUNT_TYPES",
    "NOTICE_CLASSES",
    "NOTICE_TYPE_CLASSES",
    "ProcurementNoticeObservation",
    "LexicalFrequencyObservation",
    "NormalizedRecordDraft",
    "NumericObservation",
    "QualityAssessment",
    "QualityReason",
    "RawRecordView",
    "RecordKind",
    "build_normalized",
    "canonical_decimal_text",
    "canonical_fingerprint",
    "canonical_json",
    "decimal_from",
    "year_period",
]

# The CANONICAL SCHEMA, versioned independently of any normalizer (§21). Bumped
# when what a normalized record MEANS changes -- a field added, a semantic
# redefined -- never when an implementation is fixed.
NORMALIZATION_SCHEMA_ID = "sros.normalized-record"
NORMALIZATION_SCHEMA_VERSION = 1

# Ontology V2 §14.3: an evolving taxonomy is registry rows, not a database enum.
RECORD_KIND_REGISTRY = "normalization_record_kind"

# Deterministic record ids, so a re-run converges on the row that exists rather
# than inserting a parallel copy. Same argument as the collector's namespace.
NORMALIZED_NAMESPACE = uuid.UUID("b1d7c3f2-6a48-5e91-8c02-4f7d9e15a3b6")


def canonical_json(payload: object) -> str:
    """Sorted keys, no incidental whitespace, stable separators.

    A fingerprint that changed when a dict was built in a different order would
    report a revision that did not happen.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_fingerprint(payload: object) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def decimal_from(value: object) -> Decimal | None:
    """An exact decimal, or `None` when the value cannot be read as one.

    §13. `float` is never accepted: a value that has already been through
    IEEE-754 may differ from what the source sent, and re-reading it here would
    bake that in rather than avoid it. Raw payloads are parsed from their JSON
    TEXT with `parse_float=Decimal`, so this receives `int`, `Decimal` or `str`.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return Decimal(text)
        except InvalidOperation:
            return None
    return None


def canonical_decimal_text(value: Decimal) -> str:
    """The exact value, free of an intermediate representation's artifacts.

    Plain notation, never scientific, and no trailing fractional zeros.

    The second half is not cosmetic, and the reason was found by running this
    against the real records rather than by reasoning about it. The Mission 1.5
    collector parses a value with `float(...)`, so the World Bank integer
    `82905782` reaches the raw payload as `82905782.0`. Carrying that through
    would put an artifact of an INTERMEDIATE step into the canonical form, and
    the day a collector version stops using `float` every re-normalization would
    produce a different fingerprint for identical source data -- a revision that
    did not happen, which is exactly what §22 exists to prevent.

    Stripping trailing zeros loses a source's stated PRECISION in principle
    ("2.50" is two decimal places, "2.5" reads as one). It does not lose it
    here: the source states precision separately, in `decimals`, and that field
    is preserved verbatim beside the value.
    """
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


# --------------------------------------------------------------------- period


@dataclass(frozen=True)
class CanonicalPeriod:
    """When the observation applies, as an interval and a label.

    §16. A half-open `[start, end)` plus the type and the source's own label, so
    **nothing downstream can mistake January 1 for an exact event time**. The
    interval says the observation covers a year; the label preserves what the
    source actually wrote; `type` says which of the two to trust.

    An `INSTANT` is the only type for which a single moment IS the observation,
    and it is reached only when a source states one.

    **`timezone_state` was added in Mission 1.10**, because a source can publish
    a period label and no offset. GDELT's WEB-NGRAM `DATE` is a 15-minute bucket
    stamp and nothing in its documentation states a zone (H-29), so every route
    into a period would have had to choose one -- in the field a consumer trusts
    most.

    The two states carry different kinds of bound, and that is the whole
    mechanism rather than a convention:

        ESTABLISHED      bounds are timezone-AWARE. The rule since Mission 1.6,
                         unchanged, still enforced, and true of every record
                         written to date
        NOT_ESTABLISHED  bounds are timezone-NAIVE -- wall-clock readings, which
                         is exactly what Python's naive datetime means and what
                         iCalendar calls floating time. Code that treats one as
                         UTC has made an error a type checker can see

    Making the bounds nullable instead would have weakened every period for one
    source's sake, and storing an aware UTC datetime beside a flag saying it is
    not really UTC would be a lie next to a disclaimer.
    """

    type: NormalizedPeriodType
    label: str
    start: datetime
    end: datetime
    end_inclusive: bool = False
    timezone_state: NormalizedTimezoneState = NormalizedTimezoneState.ESTABLISHED

    def __post_init__(self) -> None:
        established = self.timezone_state is NormalizedTimezoneState.ESTABLISHED
        for name in ("start", "end"):
            moment: datetime = getattr(self, name)
            if established and moment.tzinfo is None:
                raise ValueError(
                    f"period {name} must be timezone-aware when the timezone is "
                    "ESTABLISHED. A naive bound under that state would be a wall-clock "
                    "reading presented as a moment"
                )
            if not established and moment.tzinfo is not None:
                raise ValueError(
                    f"period {name} must be timezone-NAIVE when the timezone is not "
                    "established. An aware bound here carries an offset the source "
                    "never published, which is the invention this state exists to "
                    "prevent"
                )
        if self.end < self.start:
            raise ValueError("a period cannot end before it starts")
        if self.type is not NormalizedPeriodType.INSTANT and self.end == self.start:
            raise ValueError(
                "only an INSTANT has zero duration; a zero-length YEAR would be an "
                "interval pretending to be a moment"
            )

    @property
    def event_time(self) -> datetime | None:
        """The start, when it is a moment; `None` when the zone is unestablished.

        What `observed_at` is set from. A naive start cannot go into a
        `TIMESTAMPTZ` and an aware one would be the invented offset, so the
        honest answer is the absent one -- the same answer Mission 1.9.3 reached
        one layer down, for the same reason.
        """
        if self.timezone_state is not NormalizedTimezoneState.ESTABLISHED:
            return None
        return self.start

    def to_json(self) -> dict[str, object]:
        """The canonical form. `timezone_state` appears only when it is not
        ESTABLISHED, and that asymmetry is deliberate.

        The payload is inside the content fingerprint, so an unconditional key
        would change the hash of every record ever written -- for a fact those
        records already state. An ISO-8601 string **discloses its own offset or
        its absence**: `2018-01-01T00:00:00+00:00` and `20260830T091500` are
        self-describing to any reader.

        The explicit key is emitted where the answer is the surprising one,
        which is the direction "a missing mapping must remain visible" points.
        A consumer reading it should default it to ESTABLISHED.
        """
        payload: dict[str, object] = {
            "type": self.type.value,
            "label": self.label,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "end_inclusive": self.end_inclusive,
        }
        if self.timezone_state is not NormalizedTimezoneState.ESTABLISHED:
            payload["timezone_state"] = self.timezone_state.value
        return payload


def year_period(label: str) -> CanonicalPeriod:
    """A four-digit year as a half-open interval. Raises on anything else.

    Deliberately strict. A caller that wants "whatever this string is" is asking
    for a guess, and §16 is explicit that an exact date the source did not give
    must not be invented.
    """
    text = label.strip()
    if len(text) != 4 or not text.isdigit():
        raise ValueError(f"{label!r} is not a four-digit year")
    year = int(text)
    return CanonicalPeriod(
        type=NormalizedPeriodType.YEAR,
        label=text,
        start=datetime(year, 1, 1, tzinfo=UTC),
        end=datetime(year + 1, 1, 1, tzinfo=UTC),
        end_inclusive=False,
    )


# ------------------------------------------------------------------- language


@dataclass(frozen=True)
class CanonicalLanguage:
    """Which language the observation is in, with the source form always preserved.

    Mission 1.10 §5, and deliberately shaped after `CanonicalGeography`: the
    source label and the canonical tag are different facts, overwriting the first
    with the second would make the mapping unauditable, and an unmapped label
    would have nowhere to live.

    **A language is never a geography.** Spanish is not Spain and Arabic is not
    one country; a row stating a language says nothing about where anything
    happened. The registry model already keeps countries and languages apart
    (`registry/models.py`) and this is the same separation at the canonical
    layer.

    `source_scheme` has no geography counterpart and earns its place: `ENGLISH`
    means something only once a reader knows it came from CLD2 rather than from
    ISO 639's English names, which overlap and are not identical.
    """

    source_label: str
    source_scheme: str
    mapping_state: NormalizedLanguageMapping
    canonical_tag: str | None = None
    canonical_scheme: str | None = None

    def __post_init__(self) -> None:
        if not self.source_label.strip():
            raise ValueError("a canonical language must preserve the source label")
        if not self.source_scheme.strip():
            raise ValueError(
                "a source label needs the vocabulary it came from, or a reader cannot "
                "tell a CLD2 name from an ISO 639 English name"
            )
        established = self.mapping_state is NormalizedLanguageMapping.ESTABLISHED
        if established and not self.canonical_tag:
            raise ValueError(
                "an ESTABLISHED mapping must carry the tag it established. A state "
                "claiming a mapping with nothing mapped is the absence wearing the "
                "clothes of a fact"
            )
        if not established and self.canonical_tag:
            raise ValueError(
                "a tag without an ESTABLISHED mapping is a guess. The label is kept "
                "verbatim and the absence stays visible"
            )
        if bool(self.canonical_tag) != bool(self.canonical_scheme):
            raise ValueError("canonical_tag and canonical_scheme must agree")

    @classmethod
    def unmapped(cls, source_label: str, source_scheme: str) -> CanonicalLanguage:
        """What an unmapped label becomes. Never a tag.

        The counterpart of `CanonicalGeography.unclassified`, and reached for the
        same reason: resemblance is not a mapping. `ENGLISH` looks like `en` and
        `KOREAN` looks like `ko`, and the first label that does not -- a CLD2
        name with an underscore, or a distinction ISO 639 draws that CLD2 does
        not -- would be silently wrong with nothing to catch it.
        """
        return cls(
            source_label=source_label,
            source_scheme=source_scheme,
            mapping_state=NormalizedLanguageMapping.NOT_ESTABLISHED,
        )

    @property
    def mapped(self) -> bool:
        return self.mapping_state is NormalizedLanguageMapping.ESTABLISHED

    def to_json(self) -> dict[str, object]:
        return {
            "source_label": self.source_label,
            "source_scheme": self.source_scheme,
            "mapping_state": self.mapping_state.value,
            "canonical_tag": self.canonical_tag,
            "canonical_scheme": self.canonical_scheme,
        }


# ------------------------------------------------------------------ geography


@dataclass(frozen=True)
class CanonicalGeography:
    """Where the observation applies, with the source form always preserved.

    §15. Four fields rather than one, because the source code and the canonical
    code are different facts: overwriting the first with the second would make
    the mapping unauditable, and an unmapped code would have nowhere to live.
    """

    source_code: str
    source_name: str | None
    kind: NormalizedGeographyKind
    canonical_code: str | None
    canonical_scheme: str | None

    def __post_init__(self) -> None:
        if self.kind is not NormalizedGeographyKind.COUNTRY and self.canonical_code:
            raise ValueError(
                "only a COUNTRY carries a canonical country code. An AGGREGATE with one "
                "is the 'World is a country' error §15 forbids"
            )

    @classmethod
    def unclassified(cls, source_code: str, source_name: str | None) -> CanonicalGeography:
        """What an unreviewed code becomes. Never a country."""
        return cls(
            source_code=source_code,
            source_name=source_name,
            kind=NormalizedGeographyKind.UNKNOWN,
            canonical_code=None,
            canonical_scheme=None,
        )

    @classmethod
    def from_entry(
        cls, entry: GeographyEntry, source_code: str, source_name: str | None, scheme: str
    ) -> CanonicalGeography:
        return cls(
            source_code=source_code,
            source_name=source_name or entry.name,
            kind=entry.kind,
            canonical_code=entry.canonical_code,
            canonical_scheme=scheme if entry.canonical_code else None,
        )

    def to_json(self) -> dict[str, object]:
        return {
            "source_code": self.source_code,
            "source_name": self.source_name,
            "kind": self.kind.value,
            "canonical_code": self.canonical_code,
            "canonical_scheme": self.canonical_scheme,
        }


# ---------------------------------------------------------------------- value


@dataclass(frozen=True)
class CanonicalValue:
    """The measurement, its state, and its unit -- each recorded separately.

    §14 is the reason `state` exists and is mandatory. **Zero is a real
    measurement.** A source saying `0` and a source saying nothing are different
    statements about the world, and a layer that mapped both to `0` would make
    them permanently indistinguishable: no downstream stage could recover the
    difference, because the information would be gone.

    §17 is the reason `unit_state` exists. Deriving `US$` from an identifier
    that ends in `.CD` would be a guess dressed as a fact, and the first metric
    whose naming convention differed would make it silently wrong.
    """

    value: Decimal | None
    state: NormalizedValueState
    unit: str | None = None
    unit_state: NormalizedUnitState = NormalizedUnitState.UNKNOWN
    decimals: int | None = None

    def __post_init__(self) -> None:
        if self.state is NormalizedValueState.REPORTED and self.value is None:
            raise ValueError("a REPORTED value must carry a number")
        if self.state is not NormalizedValueState.REPORTED and self.value is not None:
            raise ValueError(
                "a value that was not reported must be null. Storing a number beside a "
                "NOT_REPORTED state is how an absence becomes a measurement"
            )
        if (self.unit_state is NormalizedUnitState.PUBLISHED) != bool(self.unit):
            raise ValueError("unit and unit_state must agree")

    def to_json(self) -> dict[str, object]:
        return {
            # An exact decimal STRING, never a JSON float (§13). Three reasons:
            # no binary rounding, a fingerprint that does not depend on a JSON
            # library's float formatting, and no loss of query ability --
            # `(payload -> 'observation' ->> 'value')::numeric` is exact.
            "value": None if self.value is None else canonical_decimal_text(self.value),
            "value_state": self.state.value,
            "unit": self.unit,
            "unit_state": self.unit_state.value,
            "decimals": self.decimals,
        }


# -------------------------------------------------------------- record kinds


@dataclass(frozen=True)
class RecordKind:
    """One canonical shape, and what it declares required.

    `required` is a property of the KIND, not a judgment made per record. That
    is what lets the quality state (§25) be computed rather than decided, and it
    is why a future kind brings its own answer instead of reinterpreting this
    one's.
    """

    kind_id: str
    required: tuple[str, ...]
    optional: tuple[str, ...]
    description: str


# ONE ENTRY, because one adapter exists (§11). Adding a kind means registering
# the entry, declaring its shape here and writing the adapter that produces it
# -- and NO migration, which is the extension mechanism §11 asks for.
#
# The ten hypothetical shapes §11 lists -- documents, discussion posts, reviews,
# repositories, events -- are deliberately absent. A registered kind with no
# adapter behind it is a promise the code does not keep, and this project has a
# standing rule about that: IMPLEMENTED_COLLECTORS gains a name as the LAST step
# of building a collector, never as preparation for one.
RECORD_KINDS: dict[str, RecordKind] = {
    # Mission 1.18, migration 0024. GENERIC, not `stack_exchange_question`: a
    # public Q&A question is a shape other sources share, and naming the kind
    # after the first source to reach it would make the vocabulary a list of
    # vendors. The SITE is a field; the source is provenance.
    "community_question": RecordKind(
        kind_id="community_question",
        required=("question.id", "question.site", "question.title", "period"),
        optional=(
            "question.body",
            "question.url",
            "question.content_licence",
            "tags.values",
            "answers.count",
            "answers.has_accepted_answer",
            "answers.accepted_answer_id",
            "engagement.score",
            "engagement.view_count",
        ),
        description=(
            "One public question a person asked on a community Q&A site, as the site "
            "published it. The tags are the SITE's vocabulary and are never translated; "
            "an accepted answer means only that the asker marked one accepted; the author "
            "is deliberately absent. It supports the claim that the site PUBLISHED a "
            "request for help, never that a market, a demand or an opportunity exists."
        ),
    ),
    "numeric_observation": RecordKind(
        kind_id="numeric_observation",
        required=("metric.id", "period", "geography.source_code", "observation.value_state"),
        optional=(
            "metric.name",
            "observation.value",
            "observation.unit",
            "observation.decimals",
            "geography.canonical_code",
            "series.frequency",
            "series.source_last_updated",
        ),
        description=(
            "One measured or reported numeric value for one metric, one geography and one period."
        ),
    ),
    # Mission 1.10. The second kind, and the first real use of the registry the
    # first one described. A GDELT WEB-NGRAM row has no geography and its term
    # is not a metric, so `numeric_observation` cannot hold it -- and widening
    # that kind to fit would let a World Bank record exist with no geography,
    # which is the existing model getting worse for a new source's sake.
    #
    # `language.canonical_tag` is OPTIONAL because no CLD2-to-tag mapping is
    # established (H-30) and a required field nothing can satisfy would render
    # every record INVALID for a condition that is universal and known. The
    # absence stays visible through `language.mapping_state` and a
    # LANGUAGE_NOT_MAPPED quality reason -- which is a PARTIAL, not a silence.
    "lexical_frequency_observation": RecordKind(
        kind_id="lexical_frequency_observation",
        required=(
            "term.text",
            "term.gram_size",
            "language.source_label",
            "period",
            "observation.value_state",
        ),
        optional=(
            "language.canonical_tag",
            "observation.value",
            "observation.unit",
            "series.resource_id",
            "series.source_last_updated",
        ),
        description=(
            "One occurrence count the source measured for one lexical term, in one "
            "language, over one period. Source data: the term carries no classification "
            "and the count is not a signal, a score or a rank."
        ),
    ),
    # Mission 1.15.8. The third kind. A procurement notice is neither a measured
    # metric nor a counted term: it is a DOCUMENT a public body published, whose
    # interesting content is a set of typed monetary facts, organisations in
    # roles, classifications and dates. Neither existing kind can hold that, and
    # widening one to fit would give a World Bank record an award status.
    #
    # `notice.source_type` is REQUIRED rather than optional, because the whole
    # point of the two families this resource contains is that a call for
    # competition and a report of an outcome are different things -- a notice
    # that cannot say which it is stays usable and is honestly PARTIAL.
    #
    # `period` is required and is the publication DAY. `observation.value` has no
    # counterpart here on purpose: a notice has no single measurement, and the
    # amounts it carries are a LIST of typed entries, each of which has to say
    # what it means (§19). A required scalar value would have forced exactly the
    # flattening this kind exists to avoid.
    "procurement_notice": RecordKind(
        kind_id="procurement_notice",
        required=("notice.publication_number", "notice.source_type", "period"),
        optional=(
            "notice.identifier",
            "notice.version",
            "notice.form_type",
            "classification.codes",
            "classification.contract_nature",
            "organisations.buyer",
            "organisations.tenderer",
            "award.selection_status",
            "dates.award_decision",
            "dates.contract_conclusion",
            "place.buyer_countries",
            "place.performance_countries",
            "place.performance_subdivisions",
            "amounts",
            "series.resource_id",
            "source_reference",
        ),
        description=(
            "One procurement notice a contracting authority published, as the source "
            "published it. Source data: the amounts are typed and unconverted, the "
            "organisations are multilingual and role-scoped, and nothing here is a "
            "transaction, a price or a market signal."
        ),
    ),
}


# -------------------------------------------------------------------- quality


@dataclass(frozen=True)
class QualityReason:
    """Why a record is not VALID, from a closed vocabulary plus free detail.

    The code is what a consumer branches on; the detail is what a human reads.
    Recording only the sentence would make the branch depend on a string
    somebody may reword.
    """

    code: NormalizationQualityReason
    detail: str
    field_path: str | None = None

    def to_json(self) -> dict[str, object]:
        return {"code": self.code.value, "detail": self.detail, "field": self.field_path}


@dataclass(frozen=True)
class QualityAssessment:
    """Structural completeness. Never an ML confidence (§25).

    A number on [0,1] here would invite a downstream stage to multiply a parsing
    outcome by an evidence weight, and the two mean entirely different things.
    """

    state: NormalizedRecordQuality
    reasons: tuple[QualityReason, ...] = ()

    @property
    def usable(self) -> bool:
        """Whether the record may be read as an observation at all."""
        return self.state is not NormalizedRecordQuality.INVALID

    def to_json(self) -> list[dict[str, object]]:
        return [reason.to_json() for reason in self.reasons]


# ------------------------------------------------------- the numeric payload


@dataclass(frozen=True)
class NumericObservation:
    """The canonical payload for `record_kind = numeric_observation`.

    Every field is present in the source response or derived from it by an
    explicit reviewed rule. **Nothing is defaulted from a metric name, and
    nothing is fetched** (§17, §18, §41).
    """

    metric_id: str
    metric_name: str | None
    metric_scheme: str
    value: CanonicalValue
    period: CanonicalPeriod
    geography: CanonicalGeography
    dataset: str | None = None
    resource_id: str | None = None
    frequency: str | None = None
    source_last_updated: str | None = None

    record_kind: str = "numeric_observation"

    def to_payload(self) -> dict[str, object]:
        return {
            "record_kind": self.record_kind,
            "metric": {
                "id": self.metric_id,
                "name": self.metric_name,
                "scheme": self.metric_scheme,
            },
            "observation": self.value.to_json(),
            "period": self.period.to_json(),
            "geography": self.geography.to_json(),
            "series": {
                "dataset": self.dataset,
                "resource_id": self.resource_id,
                "frequency": self.frequency,
                "source_last_updated": self.source_last_updated,
            },
        }


@dataclass(frozen=True)
class LexicalFrequencyObservation:
    """The canonical payload for `record_kind = lexical_frequency_observation`.

    Mission 1.10 §6. **Source data, never a derived signal.** The count is what
    the source measured over a stated window; nothing here ranks it, scores it,
    compares it or calls it a trend.

    Four properties are load-bearing and each answers a way this could have gone
    wrong:

    **The term is not a metric.** A metric is a definition -- population, GDP --
    reused across geographies and periods. `climate` is an observed lexical item
    and the thing measured is how often it appeared, so it lives in `term`
    rather than being pushed into `metric.id`.

    **There is no geography, and the key is ABSENT rather than null.** A WEB-NGRAM
    row states a language, and a language is not a place. A `null` geography
    would invite a reader to think one was looked for and not found.

    **`gram_size` comes from the resource, never from the term.** Counting spaces
    would make a two-word entry in a unigram file look like a bigram instead of
    surfacing it as the contract violation it would be.

    **The count carries no unit.** GDELT publishes four columns and none is a
    unit, so `unit_state` is NOT_PUBLISHED -- and this record kind already says
    the number is an occurrence count over a window, which is what a unit string
    would have said less reliably.
    """

    term_text: str
    term_gram_size: int
    term_scheme: str
    language: CanonicalLanguage
    value: CanonicalValue
    period: CanonicalPeriod
    dataset: str | None = None
    resource_id: str | None = None
    source_last_updated: str | None = None

    record_kind: str = "lexical_frequency_observation"

    def __post_init__(self) -> None:
        if not self.term_text:
            raise ValueError("a lexical observation must carry the term the source published")
        if self.term_gram_size < 1:
            raise ValueError(
                "gram size is how many words the term has and comes from the authorized "
                "resource, not from counting spaces"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "record_kind": self.record_kind,
            "term": {
                "text": self.term_text,
                "gram_size": self.term_gram_size,
                "scheme": self.term_scheme,
            },
            "language": self.language.to_json(),
            "observation": self.value.to_json(),
            "period": self.period.to_json(),
            "series": {
                "dataset": self.dataset,
                "resource_id": self.resource_id,
                "source_last_updated": self.source_last_updated,
            },
        }


# ----------------------------------------------- procurement (Mission 1.15.8)


# The monetary semantics TED publishes, as a CLOSED vocabulary. Each entry maps
# to exactly one source field and says what that field means; there is no
# generic member, and adding one would be the flattening the whole design
# refuses.
#
# **Not a domain enum, deliberately.** These are SOURCE semantics established
# for one source's field set. A cross-source `AmountType` would have to claim
# that a TED framework maximum and some future source's "budget ceiling" are the
# same concept, and nothing has established that. A vocabulary that grows a
# member per source is a vocabulary; one that grows a member per MEANING is an
# ontology, and that is a decision with an ADR behind it.
MONETARY_AMOUNT_TYPES: dict[str, str] = {
    "TOTAL_VALUE": (
        # eForms BT-161, VERBATIM. Mission 1.15.12 read the definition out of
        # the Publications Office's own SDK, and it says more than our earlier
        # wording did: the figure INCLUDES OPTIONS AND RENEWALS, so it is not
        # what was paid and not necessarily what will be. Anything downstream
        # reading it as revenue or a price is wrong at the source.
        "The value of all contracts awarded in this notice, including options and renewals "
        "(eForms BT-161, notice level). TED field `total-value`."
    ),
    "TENDER_VALUE": (
        "The value of a tender. TED field `tender-value`; published per lot, so "
        "a notice with several lots carries several."
    ),
    "ESTIMATED_VALUE": (
        "An estimated value, published before an outcome is known. TED field "
        "`estimated-value-lot`. NOT an amount anybody paid."
    ),
    "FRAMEWORK_MAXIMUM": (
        "The maximum value a framework agreement may reach. TED field "
        "`framework-maximum-value-lot`. A ceiling, not a transaction."
    ),
}

# Whether a monetary entry describes the notice as a whole or one of its lots.
MONETARY_SCOPES = ("NOTICE", "LOT")

# Whether amount i and currency i can be said to describe the same thing.
#
# ESTABLISHED   exactly one amount and one currency, so there is nothing to
#               align and the pairing is a fact rather than a reading
# NOT_ESTABLISHED
#               several amounts and/or several currencies. The Search API's
#               schema declares both as arrays and states NOTHING about
#               positional correspondence, so pairing by index would be a
#               reading of the source rather than the source's own statement.
#               Both sequences are preserved whole and unpaired
MONETARY_PAIRING_STATES = ("ESTABLISHED", "NOT_ESTABLISHED")


@dataclass(frozen=True)
class CanonicalMonetaryAmount:
    """One monetary fact, with the semantic that makes it usable.

    Mission 1.15.8 §15/§19. **An amount without its type is not stored.** The
    review's own note says a collector that cannot say which kind of amount it
    retrieved has not retrieved a usable one, and the same is true one layer up:
    a canonical amount whose meaning is unknown is exactly the `price_paid`
    flattening this model exists to prevent, wearing a different name.

    **Amount and currency are sequences, not scalars.** TED publishes both as
    arrays and says nothing about their correspondence, so a single-valued
    representation would have to pick or pair. `pairing` records whether the two
    can be read together, and it is `ESTABLISHED` only in the one shape where
    there is nothing to decide.
    """

    amount_type: str
    source_field: str
    scope: str
    amounts: tuple[Decimal, ...]
    currencies: tuple[str, ...]
    currency_source_field: str | None
    pairing: str

    def __post_init__(self) -> None:
        if self.amount_type not in MONETARY_AMOUNT_TYPES:
            raise ValueError(
                f"{self.amount_type!r} is not an established monetary semantic. An "
                "amount whose meaning is not in the vocabulary must not be stored: "
                "that is how a framework ceiling becomes a price somebody paid"
            )
        if self.scope not in MONETARY_SCOPES:
            raise ValueError(f"{self.scope!r} is not a monetary scope")
        if self.pairing not in MONETARY_PAIRING_STATES:
            raise ValueError(f"{self.pairing!r} is not a pairing state")
        if not self.amounts:
            raise ValueError(
                "a monetary entry with no amount is an absence, and an absence is "
                "represented by the entry not existing"
            )
        if self.pairing == "ESTABLISHED" and not (
            len(self.amounts) == 1 and len(self.currencies) == 1
        ):
            raise ValueError(
                "pairing is ESTABLISHED only where there is one amount and one "
                "currency. With several of either, positional correspondence is a "
                "reading the source has not published"
            )

    def to_json(self) -> dict[str, object]:
        return {
            "amount_type": self.amount_type,
            "source_field": self.source_field,
            "scope": self.scope,
            # Exact decimal STRINGS, never JSON floats -- the rule `CanonicalValue`
            # already states, for the same three reasons.
            "amounts": [canonical_decimal_text(a) for a in self.amounts],
            "currencies": list(self.currencies),
            "currency_source_field": self.currency_source_field,
            "pairing": self.pairing,
        }


@dataclass(frozen=True)
class CanonicalMultilingualText:
    """A value the source published in several languages, kept in all of them.

    Mission 1.15.8 §10. The Search API returns an object keyed by language and
    its request carries no language selector, so there is no source-supported
    preference to apply. Choosing English, or the first key, would be this
    layer inventing an editorial rule and discarding what it did not choose.

    **There is no `display` field**, and its absence is the design. A canonical
    display value would be read as *the* name by everything downstream, and the
    rule that produced it would live here rather than where a reader could see
    it. A consumer that needs one language asks for it by tag.

    Ordering is by language tag, so serialisation is deterministic and the
    content fingerprint does not depend on dictionary order.
    """

    values: tuple[tuple[str, tuple[str, ...]], ...]
    scheme: str = "ted-language-code"

    @classmethod
    def from_source(
        cls, raw: object, scheme: str = "ted-language-code"
    ) -> CanonicalMultilingualText | None:
        """Build from what TED returned, or `None` when it returned nothing.

        Accepts the object-keyed-by-language shape the API documents. A shape
        this does not recognise returns `None` and the caller records drift --
        silently stringifying an unexpected structure is what §30 forbids.
        """
        if not isinstance(raw, dict) or not raw:
            return None
        values: list[tuple[str, tuple[str, ...]]] = []
        for tag in sorted(raw):
            entry = raw[tag]
            if isinstance(entry, str):
                items: tuple[str, ...] = (entry,)
            elif isinstance(entry, list) and all(isinstance(i, str) for i in entry):
                items = tuple(entry)
            else:
                return None
            values.append((str(tag), items))
        return cls(values=tuple(values), scheme=scheme)

    @property
    def language_tags(self) -> tuple[str, ...]:
        return tuple(tag for tag, _ in self.values)

    def to_json(self) -> dict[str, object]:
        return {
            "scheme": self.scheme,
            "by_language": {tag: list(items) for tag, items in self.values},
            "language_tags": list(self.language_tags),
        }


@dataclass(frozen=True)
class CanonicalClassification:
    """One classification code, as the source published it.

    Mission 1.15.8 §13. A code and the scheme it belongs to, and nothing else.
    No label is invented, no sector is inferred, and no CPV is rolled up: a
    taxonomy mapping is a reviewed act and belongs to the mission that does it.
    """

    code: str
    scheme: str
    label: str | None = None

    def to_json(self) -> dict[str, object]:
        return {"code": self.code, "scheme": self.scheme, "label": self.label}


@dataclass(frozen=True)
class ProcurementNoticeObservation:
    """The canonical payload for `record_kind = procurement_notice`.

    Mission 1.15.8. **One notice, one record.** The lots inside it are structured
    data on this record and never records of their own: TED publishes one notice
    under one publication number, and a per-lot record would invent an identity
    the source does not have and make one publication look like several.

    **This is what TED published, not what happened.** A normalized notice
    supports the claim *TED reported that ...* and no stronger one; nothing here
    is independently verified, and the authenticity boundary the review draws is
    preserved by saying so rather than by omitting to say it.

    Four properties are load-bearing:

    **The period is the publication DAY and carries no moment.** See
    `publication` below and `ted-eu-normalization-v1.md` §5.

    **The notice type is preserved and also classified.** `source_type` is what
    TED wrote; `notice_class` is the normalized reading of it. Both, because a
    normalized class alone would lose which source vocabulary produced it, and a
    source type alone would make every consumer re-learn TED's spelling.

    **Money is a list of typed entries, never a number.** See
    `CanonicalMonetaryAmount`.

    **Organisations are multilingual and role-scoped.** A buyer and a tenderer
    are different roles, and a tenderer is never read as an awarded supplier
    here: only `award.selection_status` speaks to an outcome.
    """

    publication_number: str
    notice_class: str
    source_type: str
    source_type_scheme: str
    period: CanonicalPeriod
    publication_source_value: str
    publication_precision: str
    publication_utc_offset: str | None
    publication_offset_semantics: str
    notice_identifier: str | None = None
    notice_version: int | None = None
    form_type: str | None = None
    contract_nature: tuple[str, ...] = ()
    classifications: tuple[CanonicalClassification, ...] = ()
    buyer_organisations: CanonicalMultilingualText | None = None
    tenderer_organisations: CanonicalMultilingualText | None = None
    award_selection_status: tuple[str, ...] = ()
    award_decision_dates: tuple[str, ...] = ()
    contract_conclusion_dates: tuple[str, ...] = ()
    buyer_countries: tuple[str, ...] = ()
    performance_countries: tuple[str, ...] = ()
    performance_subdivisions: tuple[str, ...] = ()
    amounts: tuple[CanonicalMonetaryAmount, ...] = ()
    resource_id: str | None = None
    source_reference: dict[str, str] = field(default_factory=dict)

    record_kind: str = "procurement_notice"

    def __post_init__(self) -> None:
        if not self.publication_number:
            raise ValueError(
                "a procurement notice must carry the publication number the source "
                "published; identity is never reconstructed from position"
            )
        if self.notice_class not in NOTICE_CLASSES:
            raise ValueError(f"{self.notice_class!r} is not an established notice class")

    def to_payload(self) -> dict[str, object]:
        return {
            "record_kind": self.record_kind,
            "notice": {
                "publication_number": self.publication_number,
                "identifier": self.notice_identifier,
                "version": self.notice_version,
                # BOTH, always. §7.
                "class": self.notice_class,
                "source_type": self.source_type,
                "source_type_scheme": self.source_type_scheme,
                "form_type": self.form_type,
            },
            "period": self.period.to_json(),
            # The source value verbatim, beside the period derived from it, so a
            # later mission can close the open question without re-collecting.
            "publication": {
                "source_value": self.publication_source_value,
                "precision": self.publication_precision,
                "utc_offset": self.publication_utc_offset,
                "offset_semantics": self.publication_offset_semantics,
            },
            # THREE date concepts, never merged. §9.
            "dates": {
                "award_decision": list(self.award_decision_dates),
                "contract_conclusion": list(self.contract_conclusion_dates),
            },
            "classification": {
                "codes": [c.to_json() for c in self.classifications],
                "contract_nature": list(self.contract_nature),
            },
            "organisations": {
                "buyer": self.buyer_organisations.to_json() if self.buyer_organisations else None,
                "tenderer": (
                    self.tenderer_organisations.to_json() if self.tenderer_organisations else None
                ),
            },
            "award": {"selection_status": list(self.award_selection_status)},
            "place": {
                "buyer_countries": list(self.buyer_countries),
                "performance_countries": list(self.performance_countries),
                "performance_subdivisions": list(self.performance_subdivisions),
                "scheme": "ted-source-code",
            },
            "amounts": [a.to_json() for a in self.amounts],
            "series": {"resource_id": self.resource_id},
            "source_reference": dict(sorted(self.source_reference.items())),
        }


# What a notice IS, normalized. Closed, and both members correspond to a notice
# type this resource contains -- there is no OTHER member, because a notice
# outside the resource is refused rather than classified.
NOTICE_CLASSES: dict[str, str] = {
    "CONTRACT_NOTICE": "A call for competition. No award outcome exists yet.",
    "CONTRACT_AWARD_NOTICE": "A notice reporting the result of a procurement.",
}

# TED's own vocabulary, mapped to the classes above. The mapping is the whole of
# the interpretation this normalizer performs on the notice type, and it is a
# table rather than a rule so a reader can check it.
NOTICE_TYPE_CLASSES: dict[str, str] = {
    "cn-standard": "CONTRACT_NOTICE",
    "can-standard": "CONTRACT_AWARD_NOTICE",
}


class CanonicalObservation(Protocol):
    """What every canonical payload must be able to do.

    Mission 1.10. Introduced because a SECOND kind exists, not in anticipation of
    one: `build_normalized` was typed to `NumericObservation` and needed to
    accept a shape with no geography and no metric. What the two genuinely share
    is a kind id, a period and the ability to render themselves -- and nothing
    else, which is why this protocol has three members rather than a union of
    two field sets.
    """

    @property
    def record_kind(self) -> str: ...

    @property
    def period(self) -> CanonicalPeriod: ...

    def to_payload(self) -> dict[str, object]: ...


# ----------------------------------------------------------------- raw input


@dataclass(frozen=True)
class RawRecordView:
    """One raw record, as normalization reads it.

    A read model rather than the row, so a normalizer has no opinion about how
    the record was fetched and a test can construct one without a database.

    **Immutable input** (§27). Nothing here is written back. The raw layer
    records what the source returned, and a correction that made normalization
    pass would destroy the evidence that it did not.
    """

    record_id: str
    workspace_id: str
    research_session_id: str | None
    source_id: str
    observation_key: str
    content_hash: str
    acquisition_method: str
    payload: dict[str, object]
    provenance: dict[str, object]
    review_version: int
    collector_id: str
    collector_version: str
    correlation_id: str
    collected_at: datetime
    observed_at: datetime | None
    expires_at: datetime

    @property
    def attribution(self) -> dict[str, object] | None:
        """The rendered notice the collector attached, or `None`.

        `None` is a refusal the caller must handle (§46). A record with no
        attribution is not normalized into one with no credit attached.
        """
        value = self.provenance.get("attribution")
        return value if isinstance(value, dict) else None


# ------------------------------------------------------------------- the row


@dataclass(frozen=True)
class NormalizedRecordDraft:
    """A row ready to be written, with everything §8 requires already resolved."""

    record_id: uuid.UUID
    workspace_id: str
    raw_record_id: str
    research_session_id: str | None
    source_id: str
    observation_key: str
    record_kind_id: str
    record_kind_registry: str
    payload: dict[str, object]
    content_hash: str
    provenance: dict[str, object]
    quality: NormalizedRecordQuality
    quality_reasons: tuple[QualityReason, ...]
    normalizer_id: str
    normalizer_version: str
    normalization_schema_id: str
    normalization_schema_version: int
    collector_id: str
    collector_version: str
    review_version: int
    correlation_id: str
    extraction_method: str
    observed_at: datetime | None
    collected_at: datetime
    normalized_at: datetime
    expires_at: datetime
    content_language: str | None = None

    @property
    def identity(self) -> tuple[str, str, int, str, str]:
        """What the unique constraint is over (§6)."""
        return (
            self.workspace_id,
            self.raw_record_id,
            self.normalization_schema_version,
            self.normalizer_id,
            self.normalizer_version,
        )

    def to_json(self) -> dict[str, object]:
        return {
            "record_id": str(self.record_id),
            "raw_record_id": self.raw_record_id,
            "source_id": self.source_id,
            "observation_key": self.observation_key,
            "record_kind": self.record_kind_id,
            "content_hash": self.content_hash,
            "quality": self.quality.value,
            "quality_reasons": [r.to_json() for r in self.quality_reasons],
            "normalizer": f"{self.normalizer_id}@{self.normalizer_version}",
            "schema": f"{self.normalization_schema_id}/{self.normalization_schema_version}",
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "collected_at": self.collected_at.isoformat(),
            "normalized_at": self.normalized_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


# The canonical extraction method for a transformation no model influenced
# (§18, §41). Not a placeholder: a future LLM-assisted normalizer would carry a
# different value, and a reader filtering for "transformations nothing inferred"
# gets a correct answer without knowing which normalizers existed when.
DETERMINISTIC_ADAPTER = "DETERMINISTIC_ADAPTER"


def build_normalized(
    raw: RawRecordView,
    observation: CanonicalObservation,
    assessment: QualityAssessment,
    retention: EffectiveRetention,
    *,
    normalizer_id: str,
    normalizer_version: str,
    normalized_at: datetime,
    correlation_id: str,
    schema_id: str = NORMALIZATION_SCHEMA_ID,
    schema_version: int = NORMALIZATION_SCHEMA_VERSION,
) -> NormalizedRecordDraft:
    """Assemble one row. Retention and attribution come from GOVERNANCE.

    §9, §10 and §46 are enforced here by construction rather than by review:

    * there is **no attribution parameter**, so a normalizer has nothing to pass
      and nothing to omit. The notice is read from the raw record's own
      provenance -- rendered at collection time by the Mission 1.4 capability
      from the obligation the review recorded -- and a raw record carrying none
      is refused rather than normalized into a row with no credit attached;
    * there is **no expiry parameter**. `expires_at` is the resolved NORMALIZED
      window, anchored on the normalization time. The raw record's own expiry is
      deliberately not copied: the two tiers have different authoritative
      baselines (30 days and 12 months), and copying would delete normalized
      observations eleven months early for a reason no policy states.
    """
    attribution = raw.attribution
    if attribution is None:
        raise ValueError(
            f"raw record {raw.record_id} carries no rendered attribution, so no "
            "obligation could survive normalization. Refused rather than written: a "
            "derived record with no credit attached cannot be discovered to need one"
        )

    payload = observation.to_payload()
    content_hash = canonical_fingerprint(payload)

    # §6. Over the raw record and both versions -- NOT over the normalization
    # time, which would make every re-run a different representation.
    record_id = uuid.uuid5(
        NORMALIZED_NAMESPACE,
        "|".join(
            (
                raw.workspace_id,
                raw.record_id,
                schema_id,
                str(schema_version),
                normalizer_id,
                normalizer_version,
            )
        ),
    )

    acquisition = {
        # §8, copied rather than joined: the raw record is retained for 30 days
        # and this one for 12 months, so from day 31 a join answers nothing.
        # data-retention-policy-v1.md §4 requires exactly this.
        key: raw.provenance.get(key)
        for key in (
            "access_profile",
            "access_method",
            "approval_state",
            "resource_id",
            "dataset_family",
            "licence",
            "licence_basis",
            "content_origin",
            "condition_snapshot",
            "authorization_issued_at",
        )
    }

    provenance: dict[str, object] = {
        "raw_record_id": raw.record_id,
        "raw_content_hash": raw.content_hash,
        "raw_expires_at": raw.expires_at.isoformat(),
        "acquisition_method": raw.acquisition_method,
        "acquisition": acquisition,
        # §9, §46. The obligation, carried forward verbatim.
        "attribution": attribution,
        # §10. Which number applied and where it came from, so the decision
        # stays auditable after the policy changes.
        "retention": retention.to_json(),
        "normalization": {
            "schema_id": schema_id,
            "schema_version": schema_version,
            "normalizer_id": normalizer_id,
            "normalizer_version": normalizer_version,
            "extraction_method": DETERMINISTIC_ADAPTER,
            "record_kind": observation.record_kind,
        },
    }

    return NormalizedRecordDraft(
        record_id=record_id,
        workspace_id=raw.workspace_id,
        raw_record_id=raw.record_id,
        research_session_id=raw.research_session_id,
        source_id=raw.source_id,
        observation_key=raw.observation_key,
        record_kind_id=observation.record_kind,
        record_kind_registry=RECORD_KIND_REGISTRY,
        payload=payload,
        content_hash=content_hash,
        provenance=provenance,
        quality=assessment.state,
        quality_reasons=assessment.reasons,
        normalizer_id=normalizer_id,
        normalizer_version=normalizer_version,
        normalization_schema_id=schema_id,
        normalization_schema_version=schema_version,
        collector_id=raw.collector_id,
        collector_version=raw.collector_version,
        review_version=raw.review_version,
        correlation_id=correlation_id,
        extraction_method=DETERMINISTIC_ADAPTER,
        # Event time from the canonical period, not from the raw column: the
        # period is what the source stated, and `type` sits beside it on the row
        # so nothing reads January 1 as an exact moment (§16).
        #
        # `event_time` rather than `.start` since Mission 1.10: a period whose
        # timezone is not established has no moment to offer, and `observed_at`
        # is left NULL rather than filled with an offset the source never
        # published. World Bank periods are ESTABLISHED, so this is the same
        # value for every record written to date.
        observed_at=observation.period.event_time,
        collected_at=raw.collected_at,
        normalized_at=normalized_at,
        expires_at=normalized_at + timedelta(days=retention.normalized_days),
    )


@dataclass
class NormalizationCounts:
    """§52. What a normalization pass did, in the terms the brief asks for.

    Deliberately not a "data quality score": a single number over these would
    hide which of them moved, which is the only thing an operator wants to know.
    """

    records_input: int = 0
    records_normalized: int = 0
    records_valid: int = 0
    records_partial: int = 0
    records_invalid: int = 0
    records_failed: int = 0
    records_created: int = 0
    records_revised: int = 0
    records_unchanged: int = 0
    records_conflicted: int = 0
    reasons: dict[str, int] = field(default_factory=dict)

    def to_json(self) -> dict[str, object]:
        return {
            "records_input": self.records_input,
            "records_normalized": self.records_normalized,
            "records_valid": self.records_valid,
            "records_partial": self.records_partial,
            "records_invalid": self.records_invalid,
            "records_failed": self.records_failed,
            "records_created": self.records_created,
            "records_revised": self.records_revised,
            "records_unchanged": self.records_unchanged,
            "records_conflicted": self.records_conflicted,
            "quality_reasons": dict(sorted(self.reasons.items())),
        }
