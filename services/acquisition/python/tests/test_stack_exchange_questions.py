"""`stack-exchange-questions@1.0.0`, over a fake transport and no network.

Mission 1.18. Every response below is constructed in this file. The one real
acquisition the mission performed is recorded in the report, not repeated here:
a test that needs the public internet fails for reasons that are not about the
code (ADR-009).

What the suite is organised around, and each is a way the collector could be
wrong in a way nobody would notice:

    the site is not a parameter        -- one authorised site, not a runtime choice
    the filter reaches the query       -- minimisation the SOURCE performs, not us
    owner arriving is a FAILURE        -- not something to clean up afterwards
    bounds have no defaults            -- an unbounded production mode cannot exist
    backoff is obeyed                  -- the source's instruction, not a datum
    identity is the source's id        -- never a title, a hash or a page position
    no HTML fallback                   -- a refused API request is a refused acquisition
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date

import pytest
from sros_acquisition.collection.stack_exchange_questions import (
    SE_COLLECTOR_ID,
    SE_COLLECTOR_VERSION,
    SE_FILTER,
    SE_PACING,
    SE_RESOURCE_ID,
    SE_SITE,
    StackExchangeBounds,
    StackExchangeQuestion,
    StackExchangeQuestionsCollector,
    StackExchangeRequest,
)
from sros_acquisition.collection.transport import HttpRequest, HttpResponse
from sros_acquisition.compliance.config import load_compliance

from .conftest import LOCAL_PROFILE, REPO_ROOT

WORKSPACE = "00000000-0000-4000-8000-0000000000aa"


def bounds(**overrides) -> StackExchangeBounds:
    kwargs = {
        "from_date": date(2024, 3, 4),
        "to_date": date(2024, 3, 5),
        "page_size": 10,
        "max_pages": 2,
        "max_records": 15,
        "tagged": "python",
    }
    kwargs.update(overrides)
    return StackExchangeBounds(**kwargs)


def question(question_id: int = 78098368, **overrides) -> dict:
    item = {
        "question_id": question_id,
        "title": "Python multithreading I/O operation",
        "body": "<p>How do I …</p>",
        "tags": ["python", "multiprocessing"],
        "creation_date": 1709545000,
        "last_activity_date": 1709550000,
        "answer_count": 1,
        "is_answered": True,
        "score": 0,
        "view_count": 42,
        "link": f"https://stackoverflow.com/questions/{question_id}/python-multithreading",
        "content_license": "CC BY-SA 4.0",
    }
    item.update(overrides)
    return item


def envelope(items: list[dict], **overrides) -> str:
    body = {
        "items": items,
        "has_more": False,
        "quota_max": 300,
        "quota_remaining": 294,
    }
    body.update(overrides)
    return json.dumps(body)


@dataclass
class FakeTransport:
    """Records what was asked for, which is the artefact that matters."""

    bodies: list[str]
    requests: list[HttpRequest] = field(default_factory=list)
    hosts: list[frozenset[str]] = field(default_factory=list)
    status: int = 200

    def get(
        self, base_url: str, request: HttpRequest, allowed_hosts: frozenset[str]
    ) -> HttpResponse:
        self.requests.append(request)
        self.hosts.append(allowed_hosts)
        body = self.bodies[min(len(self.requests) - 1, len(self.bodies) - 1)]
        return HttpResponse(
            status_code=self.status, text=body, elapsed_seconds=0.01, url_path=request.path
        )


@pytest.fixture(scope="module")
def compliance():
    """The REAL compliance configuration, for the reason `catalog` is real."""
    return load_compliance(REPO_ROOT / "docs" / "data" / "source-compliance-v1.json")


@pytest.fixture
def context(catalog, compliance):
    from sros_acquisition.compliance.authorization import build_authorization

    return build_authorization(catalog.get("stack-exchange"), LOCAL_PROFILE, compliance)


def collect(context, transport, request=None, **overrides):
    collector = StackExchangeQuestionsCollector(transport, pacer=_NoPacer())
    kwargs = {
        "workspace_id": WORKSPACE,
        "research_session_id": None,
        "correlation_id": "corr-1",
        "sleep": lambda _: None,
    }
    kwargs.update(overrides)
    return collector.collect(context, request or StackExchangeRequest(bounds=bounds()), **kwargs)


class _NoPacer:
    def acquire(self) -> None:
        return None


# ======================================================== the authorised scope


class TestOneSiteAndOneRoute:
    def test_the_site_is_a_constant_not_a_parameter(self) -> None:
        """The review authorised `questions/stackoverflow` and nothing else.

        A `site` parameter would make the authorised scope a runtime choice,
        which is the mistake ADR-028 records for routes. Asserted over the
        request signature rather than by reading the constant, because the
        constant could stay while a parameter appeared beside it.
        """
        import inspect

        fields = set(StackExchangeBounds.__dataclass_fields__)
        assert "site" not in fields
        assert "site" not in inspect.signature(StackExchangeRequest).parameters

    def test_the_query_the_source_receives_names_the_authorised_site(self, context) -> None:
        """Mission 1.15.10's lesson, applied before it could repeat.

        A narrowing that exists only in a dataclass is not a narrowing, so this
        asserts the composed query -- the only artefact the source ever sees.
        """
        transport = FakeTransport([envelope([question()])])
        collect(context, transport)
        assert transport.requests[0].query["site"] == SE_SITE == "stackoverflow"

    def test_the_host_allowlist_comes_from_the_authorisation(self, context) -> None:
        transport = FakeTransport([envelope([question()])])
        collect(context, transport)
        assert transport.hosts[0] == frozenset({"api.stackexchange.com"})

    def test_an_unauthorised_route_refuses_before_any_request(self, context) -> None:
        stripped = type(context)(**{**context.__dict__, "access": ()})
        transport = FakeTransport([envelope([question()])])
        result = collect(stripped, transport)
        assert not result.succeeded
        assert transport.requests == []
        assert result.stopped_by == "refused before any request"


# ==================================================== minimisation and privacy


class TestPersonalDataIsExcludedAtAcquisition:
    def test_the_filter_reaches_the_query(self, context) -> None:
        """The condition is satisfied by this string being IN THE REQUEST.

        Minimisation performed by the source, before it sends anything. A
        collector that filtered afterwards would have fetched the owner, and no
        method removes a field from a record already collected.
        """
        transport = FakeTransport([envelope([question()])])
        collect(context, transport)
        assert transport.requests[0].query["filter"] == SE_FILTER

    def test_an_owner_arriving_is_a_failure_not_a_cleanup(self, context) -> None:
        """The filter is the guarantee; this is the check that it held.

        A collector that quietly dropped the owner here would report success
        over data it should never have received, which is the failure the
        review's acquisition-time rule exists to prevent.
        """
        leaked = question()
        leaked["owner"] = {"user_id": 1, "display_name": "someone"}
        result = collect(context, FakeTransport([envelope([leaked])]))
        assert not result.succeeded
        assert "excluded personal-data fields" in result.failure.detail
        assert result.drafts == ()

    @pytest.mark.parametrize("key", ["last_editor", "comments", "answers", "closed_by"])
    def test_every_identity_bearing_key_is_refused(self, context, key: str) -> None:
        leaked = question()
        leaked[key] = [{"x": 1}]
        result = collect(context, FakeTransport([envelope([leaked])]))
        assert not result.succeeded, key

    def test_an_unexpected_field_is_dropped_rather_than_stored(self, context) -> None:
        """Belt as well as braces: only keys the review authorised survive."""
        extra = question()
        extra["some_future_field"] = "whatever"
        result = collect(context, FakeTransport([envelope([extra])]))
        assert result.succeeded
        assert "some_future_field" not in result.drafts[0].payload


# ================================================================ bounds


class TestBoundsHaveNoDefaults:
    def test_every_bound_is_required(self) -> None:
        with pytest.raises(TypeError):
            StackExchangeBounds()  # type: ignore[call-arg]

    @pytest.mark.parametrize("field_name", ["page_size", "max_pages", "max_records"])
    def test_a_bound_of_zero_is_refused(self, field_name: str) -> None:
        with pytest.raises(ValueError, match="at least 1"):
            bounds(**{field_name: 0})

    def test_the_api_page_size_maximum_is_the_sources_not_ours(self) -> None:
        """Both limits exist and both are enforced.

        A page size that satisfied ours and broke theirs would be refused after
        the request, which is the wrong side of the network to find out.
        """
        with pytest.raises(ValueError, match="the SOURCE's limit"):
            bounds(page_size=101)

    def test_max_pages_cannot_exceed_our_own_per_job_ceiling(self) -> None:
        with pytest.raises(ValueError, match="request ceiling"):
            bounds(max_pages=SE_PACING.max_requests_per_job + 1)

    def test_an_empty_window_is_refused(self) -> None:
        with pytest.raises(ValueError, match="window is empty"):
            bounds(from_date=date(2024, 3, 6), to_date=date(2024, 3, 5))

    def test_max_records_stops_collection_mid_page(self, context) -> None:
        items = [question(700 + i) for i in range(10)]
        result = collect(
            context,
            FakeTransport([envelope(items, has_more=True)]),
            StackExchangeRequest(bounds=bounds(max_records=4)),
        )
        assert len(result.drafts) == 4
        assert result.stopped_by == "max_records reached"

    def test_max_pages_stops_collection_even_when_more_exist(self, context) -> None:
        page = envelope([question(800)], has_more=True)
        transport = FakeTransport([page])
        result = collect(context, transport, StackExchangeRequest(bounds=bounds(max_pages=2)))
        assert transport.requests and len(transport.requests) == 2
        assert result.has_more is True
        assert result.stopped_by == "max_pages reached"


# ======================================================= quota, backoff, errors


class TestTheSourcesOwnInstructions:
    def test_quota_is_recorded_from_the_envelope(self, context) -> None:
        result = collect(context, FakeTransport([envelope([question()])]))
        assert result.quota_remaining == 294
        assert result.quota_max == 300

    def test_backoff_is_obeyed_and_not_merely_recorded(self, context) -> None:
        """`backoff` means *do not call this method again for N seconds*.

        Recorded AND waited on. A collector that logged it and carried on would
        be ignoring the one rate instruction this source actually publishes.
        """
        slept: list[float] = []
        page = envelope([question(900)], has_more=True, backoff=2)
        collect(
            context,
            FakeTransport([page]),
            StackExchangeRequest(bounds=bounds(max_pages=2)),
            sleep=slept.append,
        )
        assert slept == [2.0]

    def test_a_non_200_is_a_refused_acquisition_with_no_fallback(self, context) -> None:
        transport = FakeTransport([envelope([])], status=400)
        result = collect(context, transport)
        assert not result.succeeded
        assert "no HTML fallback" in result.failure.detail

    def test_an_api_error_envelope_is_a_failure_even_with_http_200(self, context) -> None:
        body = json.dumps({"error_id": 502, "error_message": "throttle violation"})
        result = collect(context, FakeTransport([body]))
        assert not result.succeeded
        assert "error envelope" in result.failure.detail

    def test_a_body_that_is_not_json_fails_rather_than_yielding_nothing(self, context) -> None:
        result = collect(context, FakeTransport(["<html>go away</html>"]))
        assert not result.succeeded
        assert "not JSON" in result.failure.detail

    def test_the_pacing_basis_says_whose_number_it_is(self) -> None:
        """The distinction matters more here than for TED, because this source
        publishes a real quota and the two must not be confused."""
        assert "OURS, NOT THE SOURCE'S" in SE_PACING.basis


# ============================================================ identity


class TestIdentity:
    def test_the_key_is_the_sources_own_id_scoped_by_site(self) -> None:
        key = StackExchangeQuestion(question_id=78098368, payload={}).key
        assert "78098368" in key and SE_SITE in key

    def test_two_questions_differ_and_one_question_is_stable(self) -> None:
        a = StackExchangeQuestion(question_id=1, payload={"title": "x"})
        b = StackExchangeQuestion(question_id=2, payload={"title": "x"})
        assert a.key != b.key
        assert a.key == StackExchangeQuestion(question_id=1, payload={"title": "y"}).key

    def test_the_content_hash_moves_with_the_content_and_the_key_does_not(self) -> None:
        """Which question versus what it said: two different facts."""
        a = StackExchangeQuestion(question_id=1, payload={"title": "x"})
        b = StackExchangeQuestion(question_id=1, payload={"title": "y"})
        assert a.key == b.key
        assert a.content_hash != b.content_hash

    def test_an_item_without_an_integer_id_is_refused(self, context) -> None:
        broken = question()
        broken["question_id"] = "78098368"
        result = collect(context, FakeTransport([envelope([broken])]))
        assert not result.succeeded
        assert "stable identity" in result.failure.detail

    def test_observed_at_is_absent_because_that_is_a_normalization_decision(self) -> None:
        assert StackExchangeQuestion(question_id=1, payload={}).observed_at is None


# ============================================================ the record


class TestTheRecordItBuilds:
    def test_provenance_records_the_query_the_bounds_and_the_profile(self, context) -> None:
        result = collect(context, FakeTransport([envelope([question()])]))
        provenance = result.drafts[0].provenance
        assert provenance["site"] == SE_SITE
        assert provenance["question_id"] == 78098368
        assert provenance["licence"] == "CC-BY-SA-4.0"
        assert provenance["filter"] == SE_FILTER
        assert provenance["max_records"] == 15
        assert provenance["date_window"] == ["2024-03-04", "2024-03-05"]
        assert provenance["query"]["site"] == SE_SITE
        # Mission 1.17 found this missing from every record; added prospectively.
        assert provenance["use_profile"] == LOCAL_PROFILE

    def test_the_attribution_carries_the_per_item_link(self, context) -> None:
        """ADR-031. Both obligations, and the licence's one names the item.

        Before ADR-031 the vocabulary could not express this and the condition
        reported satisfied anyway, which is why the element exists.
        """
        result = collect(context, FakeTransport([envelope([question()])]))
        text = result.drafts[0].attribution_text
        assert "Stack Exchange Network" in text
        assert "CC BY-SA 4.0" in text
        assert "https://stackoverflow.com/questions/78098368" in text

    def test_the_collector_names_itself_and_its_version(self, context) -> None:
        result = collect(context, FakeTransport([envelope([question()])]))
        assert result.drafts[0].collector_id == SE_COLLECTOR_ID == "stack-exchange-questions"
        assert result.drafts[0].collector_version == SE_COLLECTOR_VERSION == "1.0.0"

    def test_the_resource_is_the_one_the_review_authorised(self, context) -> None:
        result = collect(context, FakeTransport([envelope([question()])]))
        assert result.drafts[0].provenance["resource_id"] == SE_RESOURCE_ID

    def test_a_repeated_question_within_one_run_is_counted_once(self, context) -> None:
        same = question(555)
        result = collect(context, FakeTransport([envelope([same, dict(same)])]))
        assert result.items_seen == 2
        assert len(result.drafts) == 1
