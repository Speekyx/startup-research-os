"""`stack-exchange-question@1.0.0` -- one Stack Overflow question, one observation.

`stack-exchange-questions-v1.md`. Mission 1.18.

**What one normalized record means, in full:** Stack Exchange published a public
question on Stack Overflow with these source fields. That is the whole assertion.

**What it does not mean**, and every one of these is a step somebody will be
tempted to take because the data looks like it supports them: a repeated problem, a
validated problem, product demand, dissatisfaction, willingness to pay,
purchase intent, a market need, or a commercial opportunity. One record is one
PUBLISHED QUESTION, once.

**And it is not one PERSON either.** Author identity is never acquired, so this
system cannot count distinct askers and must not word itself as though it could.
Fifteen records are fifteen published solution-seeking observations; how many
people wrote them is a fact the deployment deliberately does not hold.

**The tags are the SITE's vocabulary and stay in it.** `python`, `pandas`,
`google-cloud-platform` are preserved verbatim and never mapped to a taxonomy of
ours. A tag identifies a SUBJECT; it does not identify a problem, and Mission
1.18's own sample is the evidence -- three questions tagged
`google-cloud-platform` there ask about event duplication, a packaging error and
document text extraction.

**An accepted answer is a source fact and nothing more.** `has_accepted_answer`
means the asker marked an answer accepted. It is not SOLVED, not SUCCESSFUL, not
GOOD_SOLUTION and not PROBLEM_RESOLVED, and the field name is chosen so that a
reader who never opens this docstring still cannot read it as one.

**The timestamp is genuinely established, and that is new here.** Stack
Exchange's `creation_date` is a Unix epoch second, which is an unambiguous
instant -- unlike TED's offset-without-a-time (H-37) or GDELT's unzoned bucket
(H-29). So this is the first adapter whose period is `ESTABLISHED` on its own
evidence and whose `observed_at` is therefore a real moment.

**A retrieval window is not a trend.** The collector bounded `fromdate`/`todate`
to scope retrieval. Nothing here reads that as frequency, growth or momentum, and
the period of one observation is the instant the question was asked.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sros_contracts import (
    NormalizationErrorCode,
    NormalizedPeriodType,
    NormalizedRecordQuality,
    NormalizedTimezoneState,
)

from .errors import NormalizationFailedError, NormalizationFailure
from .model import (
    CanonicalPeriod,
    NormalizedRecordDraft,
    QualityAssessment,
    RawRecordView,
    build_normalized,
)
from .normalizers import NormalizationContext

__all__ = [
    "SE_NORMALIZER_ID",
    "SE_NORMALIZER_VERSION",
    "CommunityQuestionObservation",
    "StackExchangeQuestionNormalizer",
]

SE_NORMALIZER_ID = "stack-exchange-question"
SE_NORMALIZER_VERSION = "1.0.0"
RECORD_KIND = "community_question"


@dataclass(frozen=True)
class CommunityQuestionObservation:
    """One public question, in the shape the record kind declares."""

    question_id: str
    site: str
    title: str
    body: str | None
    tags: tuple[str, ...]
    question_url: str
    content_licence: str | None
    period: CanonicalPeriod
    answer_count: int | None
    has_accepted_answer: bool
    accepted_answer_id: str | None
    score: int | None
    view_count: int | None

    @property
    def record_kind(self) -> str:
        return RECORD_KIND

    def to_payload(self) -> dict[str, object]:
        return {
            "record_kind": RECORD_KIND,
            "question": {
                "id": self.question_id,
                "site": self.site,
                "title": self.title,
                "body": self.body,
                "url": self.question_url,
                "content_licence": self.content_licence,
            },
            # The SITE's vocabulary, preserved and untranslated. A tag says what
            # a question is ABOUT; it does not say what problem it has.
            "tags": {
                "scheme": f"stack-exchange-tags:{self.site}",
                "values": list(self.tags),
            },
            "period": {
                "type": self.period.type.value,
                "label": self.period.label,
                "start": self.period.start.isoformat(),
                "end": self.period.end.isoformat(),
                "end_inclusive": self.period.end_inclusive,
                "timezone_state": self.period.timezone_state.value,
            },
            # Source metadata, kept as source metadata. `has_accepted_answer`
            # says the ASKER accepted an answer -- not that the problem is
            # solved, the answer is correct, or anyone paid for anything.
            "answers": {
                "count": self.answer_count,
                "has_accepted_answer": self.has_accepted_answer,
                "accepted_answer_id": self.accepted_answer_id,
                "accepted_answer_semantics": (
                    "the asker marked an answer accepted; not a statement that the problem "
                    "is objectively resolved"
                ),
            },
            # Present because the source publishes them, and deliberately inert.
            # A score is not importance, a view count is not demand, and an
            # answer count is not difficulty.
            "engagement": {
                "score": self.score,
                "view_count": self.view_count,
                "semantics": (
                    "source counters, carried unpromoted: not importance, not demand, not "
                    "market size"
                ),
            },
            # No author. Not omitted for tidiness -- never acquired.
            "author": None,
        }


class StackExchangeQuestionNormalizer:
    """One raw Stack Overflow question into one canonical community question."""

    normalizer_id = SE_NORMALIZER_ID
    normalizer_version = SE_NORMALIZER_VERSION
    source_id = "stack-exchange"
    schema_id = "normalization.v1"
    schema_version = 1

    def __init__(self, context: NormalizationContext) -> None:
        self._retention = context.retention

    def _fail(
        self, record: RawRecordView, code: NormalizationErrorCode, detail: str
    ) -> NormalizationFailedError:
        return NormalizationFailedError(
            NormalizationFailure(
                code=code,
                detail=detail,
                raw_record_id=record.record_id,
                source_id=record.source_id,
            )
        )

    def normalize(
        self, record: RawRecordView, *, correlation_id: str, normalized_at: datetime
    ) -> NormalizedRecordDraft:
        payload: dict[str, Any] = dict(record.payload)

        # A record that carried an owner must not be normalized into one that
        # merely omits it. The collector refuses such a response; this refuses
        # such a record, because the two are different moments and a record
        # already in the database can only be caught here.
        for forbidden in ("owner", "last_editor", "comments"):
            if forbidden in payload:
                raise self._fail(
                    record,
                    NormalizationErrorCode.INVALID_RAW_RECORD,
                    f"the raw record carries {forbidden!r}, which the review excludes at "
                    "acquisition. Normalizing it into a record that simply omits the field "
                    "would hide that it was collected",
                )

        question_id = payload.get("question_id")
        if not isinstance(question_id, int):
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record carries no integer 'question_id', so the question has no "
                "source-native identity and none may be constructed for it",
            )

        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record carries no title. A question with no title is not a "
                "question anyone asked",
            )

        created = payload.get("creation_date")
        if not isinstance(created, int) or isinstance(created, bool):
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record carries no integer 'creation_date'. The instant is the "
                "period, and a question with no asked-at moment cannot be placed",
            )

        # ESTABLISHED, on the source's own evidence. A Unix epoch second is an
        # unambiguous instant -- there is no offset to interpret and no bucket
        # whose zone nobody stated. This is the first adapter for which that is
        # true, and it is why `observed_at` is a real moment here.
        asked_at = datetime.fromtimestamp(created, tz=UTC)
        period = CanonicalPeriod(
            type=NormalizedPeriodType.INSTANT,
            label=str(created),
            start=asked_at,
            end=asked_at,
            timezone_state=NormalizedTimezoneState.ESTABLISHED,
        )

        tags = payload.get("tags")
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record carries no list of string tags",
            )

        link = payload.get("link")
        if not isinstance(link, str) or not link:
            # The canonical URL is the licence's attribution target (ADR-031).
            # A record without one cannot be attributed, so it is refused rather
            # than normalized into something that cannot be displayed.
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record carries no canonical question URL, which CC BY-SA requires "
                "as the link to the licensed material",
            )

        body = payload.get("body")
        if not isinstance(body, str) or not body.strip():
            # VALID, and the absence is visible in the payload itself as
            # `question.body: null`. NOT `PARTIAL`: the record kind does not
            # require a body, and `NormalizationQualityReason` has no member
            # that would truthfully name this absence. Reaching for the nearest
            # one -- `VALUE_NOT_REPORTED` is about a numeric observation's value
            # -- would put a wrong code where a consumer branches, and adding a
            # member to a generated closed enum is a contract change with an ADR
            # behind it, which no record in the real sample calls for.
            body = None

        site = _site_of(record)

        observation = CommunityQuestionObservation(
            question_id=str(question_id),
            site=site,
            title=title,
            body=body,
            tags=tuple(tags),
            question_url=link,
            content_licence=_str_or_none(payload.get("content_license")),
            period=period,
            answer_count=_int_or_none(payload.get("answer_count")),
            has_accepted_answer=payload.get("accepted_answer_id") is not None,
            accepted_answer_id=_str_or_none(payload.get("accepted_answer_id")),
            score=_int_or_none(payload.get("score")),
            view_count=_int_or_none(payload.get("view_count")),
        )

        # **Always VALID, and that is a difference worth stating.** Every GDELT
        # record is `PARTIAL` because H-29 and H-30 are open, and every TED
        # record is `PARTIAL` because H-37 is. Nothing is open here: the epoch
        # is an unambiguous instant, a question has no geography to classify,
        # and no language is read at all. A record either carries the four facts
        # the kind requires -- and is refused above if it does not -- or it is
        # complete. There is no third state for this adapter to be in, so it has
        # no branch that could produce one.
        assessment = QualityAssessment(state=NormalizedRecordQuality.VALID, reasons=())

        return build_normalized(
            record,
            observation,
            assessment,
            self._retention,
            normalizer_id=self.normalizer_id,
            normalizer_version=self.normalizer_version,
            normalized_at=normalized_at,
            correlation_id=correlation_id,
        )


def _site_of(record: RawRecordView) -> str:
    """The site, from the collector's provenance rather than guessed from a URL.

    Parsing it out of the question link would work today and would be inventing
    a fact the record already states -- and would start reading source content
    for identity, which is the habit §4 of the review forbids.
    """
    site = (record.provenance or {}).get("site")
    return str(site) if isinstance(site, str) and site else "stackoverflow"


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _str_or_none(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
