"""`wikimedia-pageview@1.0.0` -- one article-day count, one observation.

`wikimedia-pageviews-v1.md`. Mission 1.19.

**What one normalized record means, in full:** Wikimedia counted this many
requests for this article on `en.wikipedia.org`, on this UTC day, from traffic it
attributed to the `user` class. The operator's own definition is *"a request for
content of a page that receives a response of 200 OK or 304 Not Modified"*.

**What it does not mean**, and every one of these is a step the number invites
because it looks like a measurement of people: a reader, a person, a user, a
customer, interest, curiosity, desire, demand, popularity, adoption, a product,
or a market. A count of requests is a count of requests.

**The requester class is carried on every record and is part of its identity.**
Wikimedia separates `spider` (self-identified bots) and `automated`
(heuristically detected) from `user`, which is more than any other source in this
catalog does -- and it documents the second as heuristic. So `user` means *traffic
Wikimedia did not attribute to a bot*, not *humans*, and the payload says so in
its own words rather than leaving a reader to assume the stronger reading.

**The period is a UTC DAY and the timezone is ESTABLISHED on documentation, not
on shape.** The Analytics API's own concepts page says *"For a complete definition
of a page view and extra background information, see Research:Page view"*, and
that page states a *"UTC timestamp of the request"* and *"daily partitioning 0:00
UTC - 23:59 UTC"*. That chain is what licenses `ESTABLISHED` here, and it is
recorded as an open question that the API REFERENCE does not restate it. GDELT's
H-29 stays open for the opposite reason: nothing there states the zone at all.

**A day is an interval, not a moment.** `[start, start+1 day)`, half-open, the
same treatment a World Bank year gets. `observed_at` is the interval's start
because the model derives it from an established period, and nothing downstream
may read it as the instant a request happened.

**A retrieval window is not a trend.** The collector bounded its window to scope
retrieval. Nothing here reads that as growth, seasonality or momentum, and one
record is one day.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
    "WM_NORMALIZER_ID",
    "WM_NORMALIZER_VERSION",
    "ContentRequestCountObservation",
    "WikimediaPageviewNormalizer",
]

WM_NORMALIZER_ID = "wikimedia-pageview"
WM_NORMALIZER_VERSION = "1.0.0"
RECORD_KIND = "content_request_count"

# The source's own words, carried onto every record. Not a paraphrase: the
# distinction between "request" and "view" is the whole semantic, and a
# summary of it would be the first place the stronger reading crept back in.
COUNT_SEMANTICS = (
    "a count of requests for the page that received HTTP 200 or 304, as the platform "
    "defines a page view. Not readers, not people, not users, not customers, not "
    "interest, not demand, not adoption and not a market"
)
AUDIENCE_SEMANTICS = (
    "the platform's own class for traffic it did not attribute to a self-identified bot "
    "or detect as automated. It means 'not identified as automated', never 'human'; the "
    "platform documents the detection as heuristic"
)


@dataclass(frozen=True)
class ContentRequestCountObservation:
    """One item, one period, one requester class, one count."""

    content_id: str
    platform: str
    content_url: str | None
    audience_class: str
    access_channel: str
    period: CanonicalPeriod
    request_count: int

    @property
    def record_kind(self) -> str:
        return RECORD_KIND

    def to_payload(self) -> dict[str, object]:
        return {
            "record_kind": RECORD_KIND,
            "content": {
                "id": self.content_id,
                "platform": self.platform,
                "url": self.content_url,
            },
            # REQUIRED by the kind, and required for a reason: the same item on
            # the same day carries a different count for `user` than for
            # `all-agents`, and a record that did not say which one it held
            # would be two measurements wearing one name.
            "audience": {
                "class": self.audience_class,
                "access_channel": self.access_channel,
                "semantics": AUDIENCE_SEMANTICS,
            },
            "period": {
                "type": self.period.type.value,
                "label": self.period.label,
                "start": self.period.start.isoformat(),
                "end": self.period.end.isoformat(),
                "end_inclusive": self.period.end_inclusive,
                "timezone_state": self.period.timezone_state.value,
            },
            "observation": {
                "count": self.request_count,
                "unit": "requests",
                "semantics": COUNT_SEMANTICS,
            },
            # No author, no reader, no session, no device. Not omitted for
            # tidiness -- the endpoint publishes an aggregate and nothing else
            # was ever acquired.
            "subject": None,
        }


class WikimediaPageviewNormalizer:
    """One raw article-day count into one canonical content request count."""

    normalizer_id = WM_NORMALIZER_ID
    normalizer_version = WM_NORMALIZER_VERSION
    source_id = "wikimedia-pageviews"
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

        # A record that carried a per-person field must not be normalized into
        # one that merely omits it. The collector refuses such a response and
        # this refuses such a record, because the two are different moments and
        # a record already in the database can only be caught here.
        for forbidden in ("editor", "user_text", "user_id", "user_name", "ip", "country"):
            if forbidden in payload:
                raise self._fail(
                    record,
                    NormalizationErrorCode.INVALID_RAW_RECORD,
                    f"the raw record carries {forbidden!r}, which the review excludes at "
                    "acquisition. Normalizing it into a record that simply omits the "
                    "field would hide that it was collected",
                )

        article = payload.get("article")
        if not isinstance(article, str) or not article.strip():
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record names no article, so the count has no subject and none "
                "may be constructed for it",
            )

        views = payload.get("views")
        if not isinstance(views, int) or isinstance(views, bool):
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record carries no integer `views`. A count that is not a count "
                "is refused rather than coerced, and MISSING IS NEVER ZERO",
            )

        # THE REQUESTER CLASS IS REQUIRED. A record that could not say which
        # population it counted would be usable and wrong: `user` and
        # `all-agents` are different measurements of the same article-day.
        agent = payload.get("agent")
        if not isinstance(agent, str) or not agent.strip():
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record names no requester class. The same item on the same day "
                "carries a different count for human-attributed traffic than for all "
                "traffic, so a record that did not say which it held would be two "
                "measurements wearing one name",
            )

        timestamp = payload.get("timestamp")
        if not isinstance(timestamp, str) or len(timestamp) != 10 or not timestamp.isdigit():
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                "the raw record carries no ten-digit `timestamp`, so the day it counts "
                "cannot be placed",
            )
        try:
            start = datetime.strptime(timestamp, "%Y%m%d%H").replace(tzinfo=UTC)
        except ValueError as exc:
            raise self._fail(
                record,
                NormalizationErrorCode.INVALID_RAW_RECORD,
                f"the raw record's timestamp {timestamp!r} is not a valid day bucket",
            ) from exc

        # ESTABLISHED, on the operator's own documentation rather than on the
        # shape of the value. The API concepts page designates `Research:Page
        # view` as the complete definition, and that page states a "UTC
        # timestamp of the request" and "daily partitioning 0:00 UTC - 23:59
        # UTC". GDELT's H-29 stays open for the opposite reason: nothing there
        # states the zone at all, and a bucket that merely LOOKS like a day is
        # not a bucket somebody documented.
        #
        # A DAY, not an instant: half-open [start, start + 1 day), the same
        # treatment a World Bank year gets. `observed_at` follows from the
        # established period and is the interval's start, which is not the
        # moment a request happened and must never be read as one.
        period = CanonicalPeriod(
            type=NormalizedPeriodType.DAY,
            label=start.date().isoformat(),
            start=start,
            end=start + timedelta(days=1),
            timezone_state=NormalizedTimezoneState.ESTABLISHED,
        )

        observation = ContentRequestCountObservation(
            content_id=article,
            platform=_platform_of(record),
            content_url=_url_of(record),
            audience_class=agent,
            access_channel=str(payload.get("access") or "unspecified"),
            period=period,
            request_count=views,
        )

        # ALWAYS VALID, and the adapter has no PARTIAL branch at all. Every
        # GDELT record is PARTIAL because H-29 and H-30 are open and every TED
        # record is PARTIAL because H-37 is; nothing of that kind is open here.
        # A record either carries the four facts the kind requires -- and is
        # refused above if it does not -- or it is complete.
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


def _platform_of(record: RawRecordView) -> str:
    """The project, from the collector's provenance rather than parsed from a URL.

    Parsing it out of the article link would work today and would be inventing a
    fact the record already states.
    """
    project = (record.provenance or {}).get("project")
    return str(project) if isinstance(project, str) and project else "en.wikipedia.org"


def _url_of(record: RawRecordView) -> str | None:
    """The canonical item URL, read from the record's own rendered attribution.

    `SOURCE_ITEM_LINK` is the element ADR-031 added for exactly this: a link to
    the specific item the content came from. Reading it here rather than
    recomposing one from the project and the title matters for the reason the
    ADR gives -- a link this layer built would be a link nobody rendered, and
    the record already carries the one that was.
    """
    attribution = (record.provenance or {}).get("attribution")
    if not isinstance(attribution, dict):
        return None
    for element in attribution.get("elements") or ():
        if isinstance(element, dict) and element.get("element") == "SOURCE_ITEM_LINK":
            value = element.get("value")
            if isinstance(value, str) and value:
                return value
    return None
