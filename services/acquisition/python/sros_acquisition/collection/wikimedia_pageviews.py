"""`wikimedia-pageviews-per-article@1.0.0` -- bounded daily view counts, official API only.

`wikimedia-pageviews-v1.md`. Mission 1.19.

**The first collector for a CC0 source, and the first whose obligations run the
other way.** Every source before this one granted rights subject to conditions on
the OUTPUT: attribute the material, identify the licence, do not distort the
meaning. CC0 1.0 imposes none of those -- it waives copyright, related rights and
the sui generis database right outright. What Wikimedia does impose is a
condition on the REQUEST: the access policy states that the API requires a
User-Agent header and that clients sending none may be blocked without notice.

So this collector's fifth gate is one no previous collector has: it asks the
context whether the identity the transport will send is the identity the review
declared, before a socket opens. A declaration nobody sends would verify against
a document instead of against behaviour.

**Five gates, all before a socket:**

    bounds    -> a query with no ceiling is refused, and no default supplies one
    route     -> taken from context.access BY LABEL, never hard-coded
    resource  -> context.authorize_resource, built from the context's own entry
    fields    -> context.authorize_fields, on the CONCEPTUAL names
    identity  -> context.authorize_client_identification, on what will be SENT

**What one record means, in full:** Wikimedia counted this many requests for this
article on this project, on this UTC day, from this agent class. The operator's
own definition is *"a request for content of a page that receives a response of
200 OK or 304 Not Modified"*.

**What it does not mean**, and each of these is a step the number invites:
readers, people, users, customers, interest, curiosity, demand, popularity, a
market, or product adoption. A count of requests is a count of requests. The
`agent` value is carried on every record precisely so that no consumer can forget
which population was counted.

**One article is not a product and one day is not a trend.** The collector bounds
its window to scope retrieval; nothing here reads that window as growth,
seasonality or momentum.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sros_contracts import AcquisitionErrorCode, ResourceContentOrigin

from ..compliance.authorization import AcquisitionAuthorizationContext
from ..compliance.resources import ResourceDescriptor
from .errors import AcquisitionFailedError, AcquisitionFailure
from .pacing import PacingPolicy, RequestPacer
from .records import RawRecordDraft, build_raw_record, canonical_fingerprint, observation_key
from .transport import (
    DEFAULT_USER_AGENT,
    HttpRequest,
    HttpResponse,
    Transport,
    host_of,
    path_segment,
)

__all__ = [
    "WM_ACCESS",
    "WM_AGENT",
    "WM_COLLECTOR_ID",
    "WM_COLLECTOR_VERSION",
    "WM_GRANULARITY",
    "WM_PACING",
    "WM_PROJECT",
    "WM_RESOURCE_ID",
    "WM_ROUTE_LABEL",
    "WikimediaPageviewsBounds",
    "WikimediaPageviewsCollector",
    "WikimediaPageviewsRequest",
    "WikimediaPageviewsResult",
    "WikimediaPageviewObservation",
]

WM_COLLECTOR_ID = "wikimedia-pageviews-per-article"
WM_COLLECTOR_VERSION = "1.0.0"
WM_ROUTE_LABEL = "wikimedia-analytics-api"
WM_RESOURCE_ID = "metrics/pageviews/per-article/en.wikipedia.org"

# ONE PROJECT, and it is not a parameter. The review authorised
# `en.wikipedia.org` and nothing else: Wikimedia runs over 300 Wikipedias plus
# Commons, Wiktionary and more, they have different editorial communities and
# different reader populations, and a `project` argument would make the
# authorised scope a runtime choice -- the mistake ADR-028 records for routes.
WM_PROJECT = "en.wikipedia.org"

# ALSO NOT PARAMETERS, and each for a reason about meaning rather than scope.
#
# `agent=user` is the narrowest population the source publishes. `all-agents`
# would silently fold in self-identified bots and heuristically detected
# automation, and the resulting number would answer a different question under
# the same field name. The operator documents the heuristic as best-effort, and
# that limitation is carried onto every record rather than resolved here.
#
# `access=all-access` is the WIDEST access channel, deliberately: desktop,
# mobile-web and mobile-app are three ways to make the same request, and
# choosing one would be an editorial decision about which readers count.
#
# `granularity=daily` is the finest the endpoint offers and the only one from
# which a comparable series can be built. Monthly would make adjacency
# ambiguous across months of different lengths.
WM_AGENT = "user"
WM_ACCESS = "all-access"
WM_GRANULARITY = "daily"

# The conceptual field names the review authorised, asked of the context before
# the request is composed. Conceptual rather than native for the reason Mission
# 1.15.7 gives: a review approves a MEANING, and a native name is how one API
# spells it this year.
CONCEPTUAL_FIELDS: tuple[str, ...] = (
    "project",
    "article",
    "granularity",
    "timestamp",
    "access",
    "agent",
    "views",
)

# Native keys kept from a returned item. Anything else is dropped before the
# payload is built. Unlike Stack Exchange there is no filter mechanism to ask
# the source for less -- the endpoint is already narrow -- so this is the whole
# minimisation and it is enforced here.
KEPT_KEYS: frozenset[str] = frozenset(CONCEPTUAL_FIELDS)

# Keys whose arrival would mean the endpoint returned something the review did
# not assess. A failure rather than a cleanup: the data would already have been
# fetched, and no method removes a field from a record already collected.
FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {"editor", "user_text", "user_id", "user_name", "ip", "country"}
)

WM_PACING = PacingPolicy(
    min_interval_seconds=1.0,
    max_requests_per_job=10,
    basis=(
        "OURS, AND FAR INSIDE THEIRS. Wikimedia's Robot Policy asks for fewer than 10 "
        "concurrent requests and an average below 20 per second, and the Analytics API "
        "access policy asks callers to wait for each request to finish before sending the "
        "next. Those are the SOURCE's numbers. One second between serial requests and at "
        "most ten per job are OURS: chosen so a mistake costs Wikimedia nothing and so a "
        "loop cannot become a campaign. If the published guidance were ever tighter than "
        "this, the guidance wins."
    ),
)


def _fail(code: AcquisitionErrorCode, detail: str, source_id: str) -> AcquisitionFailedError:
    return AcquisitionFailedError(AcquisitionFailure(code=code, detail=detail, source_id=source_id))


@dataclass(frozen=True)
class WikimediaPageviewsBounds:
    """The ceilings one collection may not exceed. **No defaults, anywhere.**

    Every field is required, so `WikimediaPageviewsBounds()` is a `TypeError`
    and there is no unbounded production mode to reach. A default here would be
    a number nobody reviewed.

    `articles` is a tuple rather than a pattern, a category or a search: this
    collector cannot discover what to ask for. Discovery is a different act with
    a different rights and volume question, and a collector that could enumerate
    articles could enumerate the encyclopedia.
    """

    articles: tuple[str, ...]
    from_date: date
    to_date: date
    max_articles: int
    max_days: int

    # The source's own floor: the endpoints serve data starting 1 July 2015,
    # documented on the Analytics API page-views reference. Asking for earlier
    # is a request the source cannot answer, refused on this side of the
    # network rather than the other.
    EARLIEST = date(2015, 7, 1)

    def __post_init__(self) -> None:
        if not self.articles:
            raise ValueError("articles is empty; a collection with no subject collects nothing")
        if len(set(self.articles)) != len(self.articles):
            raise ValueError(
                "an article appears twice; the same series would be fetched twice and "
                "counted once, which makes the request count a lie"
            )
        for name in ("max_articles", "max_days"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1; a bound of zero collects nothing")
        if self.from_date > self.to_date:
            raise ValueError("from_date is after to_date; the window is empty")
        if self.from_date < self.EARLIEST:
            raise ValueError(
                f"from_date {self.from_date} precedes {self.EARLIEST}, the earliest day the "
                "Analytics API serves. That is the SOURCE's floor, not ours"
            )
        if len(self.articles) > self.max_articles:
            raise ValueError(
                f"{len(self.articles)} articles exceeds max_articles {self.max_articles}"
            )
        if len(self.articles) > WM_PACING.max_requests_per_job:
            raise ValueError(
                f"{len(self.articles)} articles would need one request each, exceeding our "
                f"own per-job ceiling of {WM_PACING.max_requests_per_job}"
            )
        span = (self.to_date - self.from_date).days + 1
        if span > self.max_days:
            raise ValueError(f"the window spans {span} days, exceeding max_days {self.max_days}")


@dataclass(frozen=True)
class WikimediaPageviewsRequest:
    """One bounded query. Project, access, agent and granularity are not parameters."""

    bounds: WikimediaPageviewsBounds
    conceptual_fields: tuple[str, ...] = CONCEPTUAL_FIELDS

    def path_for(self, article: str) -> str:
        """The path the API actually receives, which is the artefact that counts.

        Mission 1.15.10's lesson, applied before it could repeat: a narrowing
        that exists only in a dataclass field is not a narrowing, so the tests
        assert THIS rather than the bounds object.

        The article title is percent-encoded with `/` included, because a real
        title can contain one and an unescaped slash would silently become a
        different path segment -- a request for an article nobody asked for.
        """
        return "/".join(
            (
                "metrics",
                "pageviews",
                "per-article",
                WM_PROJECT,
                WM_ACCESS,
                WM_AGENT,
                path_segment(article),
                WM_GRANULARITY,
                self.bounds.from_date.strftime("%Y%m%d"),
                self.bounds.to_date.strftime("%Y%m%d"),
            )
        )


@dataclass(frozen=True)
class WikimediaPageviewObservation:
    """One article-day count, as the collector holds it before it becomes a record."""

    article: str
    timestamp: str
    payload: dict[str, object]

    @property
    def source_id(self) -> str:
        return "wikimedia-pageviews"

    @property
    def resource_id(self) -> str:
        return WM_RESOURCE_ID

    @property
    def key(self) -> str:
        """WHICH observation: one article, one project, one day, one agent class.

        The agent class is IN THE KEY and that is deliberate. The same article
        on the same day has a different count under `user` and under
        `all-agents`, and a key that omitted it would let two different
        measurements collide on one identity -- one silently overwriting the
        other as a revision.
        """
        return observation_key(
            "wikimedia-pageviews", WM_PROJECT, WM_AGENT, self.article, self.timestamp
        )

    @property
    def content_hash(self) -> str:
        """WHAT the source said, over the canonical payload."""
        return canonical_fingerprint(self.payload)

    @property
    def observed_at(self) -> None:
        """Deliberately absent.

        The day bucket is UTC on the source's own documentation, so an instant
        COULD be derived -- but `observed_at` on a RawRecord is a normalization
        decision and this collector does not make normalization decisions. The
        timestamp is preserved verbatim for that later step.
        """
        return None


@dataclass
class WikimediaPageviewsResult:
    """What one bounded collection produced, including what the source said back."""

    drafts: tuple[RawRecordDraft, ...] = ()
    articles_requested: int = 0
    articles_returned: int = 0
    items_seen: int = 0
    requests_made: int = 0
    articles_absent: tuple[str, ...] = ()
    stopped_by: str = ""
    failure: AcquisitionFailure | None = None

    @property
    def succeeded(self) -> bool:
        return self.failure is None

    def to_json(self) -> dict[str, object]:
        return {
            "records": len(self.drafts),
            "articles_requested": self.articles_requested,
            "articles_returned": self.articles_returned,
            "articles_absent": list(self.articles_absent),
            "items_seen": self.items_seen,
            "requests_made": self.requests_made,
            "stopped_by": self.stopped_by,
            "failure": None if self.failure is None else self.failure.to_json(),
        }


class WikimediaPageviewsCollector:
    """Bounded per-article daily view counts, over the Analytics API and nothing else."""

    def __init__(
        self,
        transport: Transport,
        *,
        pacer: RequestPacer | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self._transport = transport
        self._pacer = pacer or RequestPacer(WM_PACING)
        # What the transport will actually send. Passed in rather than assumed
        # so the identity gate compares the review against the WIRE, and a test
        # can prove that a mismatch refuses.
        self._user_agent = user_agent

    # ------------------------------------------------------------------ gates

    def _route(self, context: AcquisitionAuthorizationContext) -> Any:
        """The reviewed route, BY LABEL. No fallback exists and none is wanted.

        The bulk dumps route is registered and blocked, so it is not in
        `context.access` at all -- there is no endpoint to read and nothing for
        the transport to be pointed at (ADR-028).
        """
        refusals = context.authorize_route(WM_ROUTE_LABEL)
        route = next((a for a in context.access if a.label == WM_ROUTE_LABEL), None)
        if refusals or route is None or not (route.endpoint_url or "").strip():
            raise _fail(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                f"{WM_ROUTE_LABEL!r} is not an authorized route with an endpoint for this "
                "source and profile. There is no second route to try: the bulk dumps "
                "route is blocked by name and browser automation is refused by the review",
                context.source_id,
            )
        return route

    def _identify(self, context: AcquisitionAuthorizationContext) -> None:
        """The gate no earlier collector has, because no earlier source needed it.

        Wikimedia's access policy makes the User-Agent a condition of access in
        its own words. So the review declares the string and the collector
        refuses when the transport would send a different one -- a declaration
        nobody sends is a condition that verifies against a document instead of
        against behaviour.
        """
        refusals = context.authorize_client_identification(self._user_agent)
        if refusals:
            raise _fail(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                "client identification refused: " + "; ".join(refusals),
                context.source_id,
            )

    def _authorize(
        self, context: AcquisitionAuthorizationContext, request: WikimediaPageviewsRequest
    ) -> Any:
        """Resource and fields, both before a socket opens."""
        dataset = context.authorized_dataset(WM_RESOURCE_ID)
        if dataset is None:
            raise _fail(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                f"{WM_RESOURCE_ID!r} is not an authorized resource for this source and profile",
                context.source_id,
            )
        decision = context.authorize_resource(
            ResourceDescriptor(
                source_id=context.source_id,
                resource_id=dataset.resource_id,
                licence=dataset.licence,
                rights_basis=dataset.rights_basis,
                content_origin=ResourceContentOrigin(dataset.content_origin),
                dataset_family=dataset.dataset_family,
            )
        )
        if not decision.allowed:
            raise _fail(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                f"{WM_RESOURCE_ID!r} is refused by its own scope: "
                + "; ".join(decision.denial_reasons),
                context.source_id,
            )
        refusals = context.authorize_fields(request.conceptual_fields)
        if refusals:
            raise _fail(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                "field selection refused: " + "; ".join(refusals),
                context.source_id,
            )
        return dataset

    # --------------------------------------------------------------- response

    def _parse(
        self, response: HttpResponse, article: str, source_id: str
    ) -> list[WikimediaPageviewObservation]:
        """One article's series. A 404 is an ABSENCE, not a failure.

        The endpoint returns 404 for an article with no recorded views in the
        window -- a title that does not exist, or one nobody requested. That is
        a fact about the world, and turning it into zero would be the error
        ADR-023 names for GDELT: **an absent count is absent, never a frequency
        of zero.** So the article is recorded as absent and the collection
        continues.

        Parsed with `parse_float=Decimal` for the reason Mission 1.15.10
        established. `parse_int` stays unset: a view count is a JSON integer and
        was never at risk.
        """
        if response.status_code == 404:
            return []
        if response.status_code != 200:
            raise _fail(
                AcquisitionErrorCode.UPSTREAM_CLIENT_ERROR,
                f"the API returned HTTP {response.status_code} for {response.url_path}. "
                "There is no HTML fallback and no bulk route to fall back to: a refused "
                "API request is a refused acquisition",
                source_id,
            )
        try:
            body = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise _fail(
                AcquisitionErrorCode.INVALID_RESPONSE,
                f"the response is not JSON: {exc}",
                source_id,
            ) from exc
        if not isinstance(body, dict):
            raise _fail(
                AcquisitionErrorCode.INVALID_RESPONSE,
                f"the response is a {type(body).__name__}, not an object",
                source_id,
            )
        items = body.get("items")
        if not isinstance(items, list):
            raise _fail(
                AcquisitionErrorCode.INVALID_RESPONSE,
                "the response envelope carries no `items` list",
                source_id,
            )

        observations: list[WikimediaPageviewObservation] = []
        for raw in items:
            if not isinstance(raw, dict):
                raise _fail(
                    AcquisitionErrorCode.INVALID_RESPONSE,
                    f"an item is a {type(raw).__name__}, not an object",
                    source_id,
                )
            leaked = FORBIDDEN_KEYS & set(raw)
            if leaked:
                raise _fail(
                    AcquisitionErrorCode.INVALID_RESPONSE,
                    f"the response carries fields {sorted(leaked)} that this review did not "
                    "assess. Dropping them here would not undo having fetched them",
                    source_id,
                )
            timestamp = raw.get("timestamp")
            if not isinstance(timestamp, str) or len(timestamp) != 10:
                raise _fail(
                    AcquisitionErrorCode.INVALID_RESPONSE,
                    "an item carries no ten-character `timestamp`, so the day it counts "
                    "cannot be identified and no identity can be constructed for it",
                    source_id,
                )
            views = raw.get("views")
            if not isinstance(views, int) or isinstance(views, bool):
                raise _fail(
                    AcquisitionErrorCode.INVALID_RESPONSE,
                    "an item carries no integer `views`; a count that is not a count is "
                    "refused rather than coerced",
                    source_id,
                )
            # The article the SOURCE echoed, not the one we asked for. They
            # differ when a title is normalised, and recording our own request
            # would attribute the source's data to a name it did not use.
            echoed = raw.get("article")
            payload = {k: v for k, v in raw.items() if k in KEPT_KEYS}
            observations.append(
                WikimediaPageviewObservation(
                    article=str(echoed) if isinstance(echoed, str) and echoed else article,
                    timestamp=timestamp,
                    payload=payload,
                )
            )
        return observations

    # ---------------------------------------------------------------- collect

    def collect(
        self,
        context: AcquisitionAuthorizationContext,
        request: WikimediaPageviewsRequest,
        *,
        workspace_id: str,
        research_session_id: str | None,
        correlation_id: str,
        now: datetime | None = None,
        sleep: Any = time.sleep,  # noqa: ARG002 - pacing is the pacer's job here
    ) -> WikimediaPageviewsResult:
        """Run one bounded query. Every gate is closed before the first socket."""
        moment = now or datetime.now(UTC)
        result = WikimediaPageviewsResult(articles_requested=len(request.bounds.articles))

        try:
            route = self._route(context)
            self._identify(context)
            dataset = self._authorize(context, request)
        except AcquisitionFailedError as exc:
            result.failure = exc.failure
            result.stopped_by = "refused before any request"
            return result

        base_url = route.endpoint_url or ""
        allowed_hosts = frozenset({host_of(base_url)}) - {""}

        drafts: list[RawRecordDraft] = []
        seen: set[str] = set()
        absent: list[str] = []
        returned = 0

        for article in request.bounds.articles:
            if result.requests_made >= WM_PACING.max_requests_per_job:
                result.stopped_by = "per-job request ceiling reached"
                break

            self._pacer.acquire()
            path = request.path_for(article)
            try:
                response = self._transport.get(base_url, HttpRequest(path=path), allowed_hosts)
                observations = self._parse(response, article, context.source_id)
            except AcquisitionFailedError as exc:
                result.failure = exc.failure
                result.stopped_by = "upstream failure"
                result.drafts = tuple(drafts)
                result.articles_absent = tuple(absent)
                return result

            result.requests_made += 1
            if not observations:
                absent.append(article)
                continue
            returned += 1

            for observation in observations:
                result.items_seen += 1
                if observation.key in seen:
                    continue
                seen.add(observation.key)
                drafts.append(
                    build_raw_record(
                        observation,
                        context,
                        workspace_id=workspace_id,
                        research_session_id=research_session_id,
                        correlation_id=correlation_id,
                        collector_id=WM_COLLECTOR_ID,
                        collector_version=WM_COLLECTOR_VERSION,
                        collected_at=moment,
                        access_label=route.label,
                        source_reference=_article_url(observation.article),
                        source_item_link=_article_url(observation.article),
                        source_provenance={
                            "project": WM_PROJECT,
                            "article": observation.article,
                            "requested_article": article,
                            "access": WM_ACCESS,
                            "agent": WM_AGENT,
                            "granularity": WM_GRANULARITY,
                            "resource_id": WM_RESOURCE_ID,
                            "licence": dataset.licence,
                            "path": path,
                            "date_window": [
                                request.bounds.from_date.isoformat(),
                                request.bounds.to_date.isoformat(),
                            ],
                            "max_articles": request.bounds.max_articles,
                            "max_days": request.bounds.max_days,
                            "requested_conceptual_fields": list(request.conceptual_fields),
                            "user_agent": self._user_agent,
                            "pacing_basis": "INTERNAL_SAFETY_POLICY",
                            "agent_semantics": (
                                "'user' is the source's own class for traffic it did not "
                                "attribute to a self-identified bot or detect as automated. "
                                "The operator documents that detection as heuristic"
                            ),
                        },
                    )
                )

        result.articles_returned = returned
        result.articles_absent = tuple(absent)
        if not result.stopped_by:
            result.stopped_by = "every requested article was asked for once"
        result.drafts = tuple(drafts)
        return result


def _article_url(article: str) -> str:
    """The canonical article URL, composed from the project the review authorised.

    Not taken from the response, which returns no link. Composed rather than
    guessed: the project is a constant of this collector, and the title is the
    one the SOURCE echoed.
    """
    return f"https://{WM_PROJECT}/wiki/{path_segment(article)}"
