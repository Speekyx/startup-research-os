"""`wikimedia-pageviews-per-article@1.0.0`, over a fake transport and no network.

Mission 1.19. Every response below is constructed in this file. The one real
acquisition the mission performed is recorded in the report, not repeated here:
a test that needs the public internet fails for reasons that are not about the
code (ADR-009).

What the suite is organised around, and each is a way this collector could be
wrong in a way nobody would notice:

    project/agent/access are constants  -- the authorised scope is not a runtime choice
    the PATH names them                 -- a narrowing only in a dataclass is not one
    identity is checked against the WIRE -- the gate no earlier collector has
    404 is an ABSENCE                   -- never a count of zero (ADR-023)
    the agent class is IN the key       -- two populations cannot collide on one identity
    bounds have no defaults             -- an unbounded production mode cannot exist
    the source's echoed title wins      -- we do not attribute its data to our spelling
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date

import pytest
from sros_acquisition.collection.transport import DEFAULT_USER_AGENT, HttpRequest, HttpResponse
from sros_acquisition.collection.wikimedia_pageviews import (
    WM_ACCESS,
    WM_AGENT,
    WM_COLLECTOR_ID,
    WM_COLLECTOR_VERSION,
    WM_GRANULARITY,
    WM_PACING,
    WM_PROJECT,
    WM_RESOURCE_ID,
    WikimediaPageviewsBounds,
    WikimediaPageviewsCollector,
    WikimediaPageviewsRequest,
)
from sros_acquisition.compliance.config import load_compliance

from .conftest import LOCAL_PROFILE, REPO_ROOT

WORKSPACE = "00000000-0000-4000-8000-0000000000aa"


def bounds(**overrides) -> WikimediaPageviewsBounds:
    kwargs = {
        "articles": ("Kubernetes",),
        "from_date": date(2024, 3, 1),
        "to_date": date(2024, 3, 5),
        "max_articles": 5,
        "max_days": 31,
    }
    kwargs.update(overrides)
    return WikimediaPageviewsBounds(**kwargs)


def item(day: str, views: int, article: str = "Kubernetes") -> dict:
    return {
        "project": "en.wikipedia",
        "article": article,
        "granularity": "daily",
        "timestamp": day,
        "access": "all-access",
        "agent": "user",
        "views": views,
    }


def envelope(items: list[dict]) -> str:
    return json.dumps({"items": items})


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


class _NoPacer:
    def acquire(self) -> None:
        return None


@pytest.fixture(scope="module")
def compliance():
    """The REAL compliance configuration, so a test cannot pass against a
    permission the repository does not actually record."""
    return load_compliance(REPO_ROOT / "docs" / "data" / "source-compliance-v1.json")


@pytest.fixture
def context(catalog, compliance):
    from sros_acquisition.compliance.authorization import build_authorization

    return build_authorization(catalog.get("wikimedia-pageviews"), LOCAL_PROFILE, compliance)


def collect(context, transport, request=None, **overrides):
    collector = WikimediaPageviewsCollector(
        transport, pacer=_NoPacer(), user_agent=overrides.pop("user_agent", DEFAULT_USER_AGENT)
    )
    kwargs = {
        "workspace_id": WORKSPACE,
        "research_session_id": None,
        "correlation_id": "corr-1",
        "sleep": lambda _: None,
    }
    kwargs.update(overrides)
    return collector.collect(
        context, request or WikimediaPageviewsRequest(bounds=bounds()), **kwargs
    )


# ======================================================== the authorised scope


class TestTheScopeIsNotARuntimeChoice:
    def test_project_agent_access_and_granularity_are_not_parameters(self) -> None:
        """Four constants, and each hides a different mistake if it becomes an
        argument.

        `project` would let one call reach any of 300+ Wikipedias the review did
        not assess. `agent` would let one call silently answer a different
        question: `all-agents` folds in self-identified bots and detected
        automation. `access` would make "which readers count" an editorial
        choice. `granularity` would make adjacency ambiguous across months.
        """
        import inspect

        fields = set(WikimediaPageviewsBounds.__dataclass_fields__)
        params = set(inspect.signature(WikimediaPageviewsRequest).parameters)
        for name in ("project", "agent", "access", "granularity"):
            assert name not in fields, name
            assert name not in params, name

    def test_the_path_the_source_receives_names_them(self, context) -> None:
        """Mission 1.15.10's lesson, applied before it could repeat: a narrowing
        that reaches a dataclass and not the wire is not a narrowing."""
        transport = FakeTransport([envelope([item("2024030100", 10)])])
        collect(context, transport)
        path = transport.requests[0].path
        assert path.startswith(
            f"metrics/pageviews/per-article/{WM_PROJECT}/{WM_ACCESS}/{WM_AGENT}/"
        )
        assert f"/{WM_GRANULARITY}/20240301/20240305" in path

    def test_an_article_title_is_percent_encoded(self, context) -> None:
        """A real title can contain a slash, and an unescaped one becomes a
        different path segment -- a request for an article nobody asked for."""
        transport = FakeTransport([envelope([])], status=404)
        collect(
            context,
            transport,
            WikimediaPageviewsRequest(bounds=bounds(articles=("AC/DC",))),
        )
        assert "AC%2FDC" in transport.requests[0].path
        assert "AC/DC" not in transport.requests[0].path

    def test_only_the_authorised_host_is_reachable(self, context) -> None:
        transport = FakeTransport([envelope([item("2024030100", 10)])])
        collect(context, transport)
        assert transport.hosts[0] == frozenset({"wikimedia.org"})

    def test_a_blocked_route_has_no_endpoint_to_reach(self, context) -> None:
        """The bulk dumps route is registered SO THAT it can be refused by name,
        and the enforcement is that it is absent from the context entirely."""
        labels = {a.label for a in context.access}
        assert labels == {"wikimedia-analytics-api"}
        assert context.route_authorization is not None
        assert "wikimedia-dumps" in context.route_authorization.blocked_labels
        assert context.authorize_route("wikimedia-dumps")


# ============================================== the identity gate (Mission 1.19)


class TestTheClientIdentifiesItself:
    def test_the_review_declares_the_user_agent_the_transport_sends(self, context) -> None:
        assert context.client_identification is not None
        assert context.client_identification.user_agent == DEFAULT_USER_AGENT
        assert context.authorize_client_identification(DEFAULT_USER_AGENT) == ()

    def test_a_mismatch_refuses_before_any_request(self, context) -> None:
        """The point of the gate: a declaration nobody sends verifies against a
        document instead of against behaviour."""
        transport = FakeTransport([envelope([item("2024030100", 10)])])
        result = collect(context, transport, user_agent="something-else/9.9 (nobody)")
        assert not result.succeeded
        assert transport.requests == []
        assert "client identification refused" in result.failure.detail

    def test_a_generic_library_default_is_refused_by_name(self, context) -> None:
        """The Foundation's policy names `python-requests/x` as a string that may
        be blocked. A check that only asked "is it non-empty" would pass it."""
        refusals = context.authorize_client_identification("python-requests/2.31.0")
        assert refusals
        assert any("python-requests" in r for r in refusals)

    def test_a_browser_string_is_refused_too(self, context) -> None:
        """Copying a browser identifies somebody we are not, which is the shape
        of every circumvention this repository refuses."""
        assert context.authorize_client_identification("Mozilla/5.0 (Windows NT 10.0)")

    def test_the_declared_string_carries_a_contact(self, context) -> None:
        declared = context.client_identification
        assert declared.contact in declared.user_agent


# ================================================================ the bounds


class TestBoundsHaveNoDefaults:
    def test_constructing_bounds_with_nothing_is_a_type_error(self) -> None:
        with pytest.raises(TypeError):
            WikimediaPageviewsBounds()  # type: ignore[call-arg]

    @pytest.mark.parametrize("field_name", ["max_articles", "max_days"])
    def test_a_ceiling_of_zero_is_refused(self, field_name) -> None:
        with pytest.raises(ValueError, match="at least 1"):
            bounds(**{field_name: 0})

    def test_an_empty_article_list_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no subject"):
            bounds(articles=())

    def test_a_repeated_article_is_refused(self) -> None:
        """The same series fetched twice and counted once makes the request
        count a lie, and the request count is what pacing is judged on."""
        with pytest.raises(ValueError, match="twice"):
            bounds(articles=("Kubernetes", "Kubernetes"))

    def test_a_window_before_the_sources_own_floor_is_refused(self) -> None:
        """2015-07-01 is the SOURCE's limit, documented on the page-views
        reference. Refused on this side of the network rather than the other."""
        with pytest.raises(ValueError, match="2015-07-01"):
            bounds(from_date=date(2015, 6, 30), to_date=date(2015, 7, 2))

    def test_more_articles_than_our_own_per_job_ceiling_is_refused(self) -> None:
        many = tuple(f"Article_{i}" for i in range(WM_PACING.max_requests_per_job + 1))
        with pytest.raises(ValueError, match="per-job ceiling"):
            bounds(articles=many, max_articles=len(many))

    def test_our_pacing_says_whose_number_it_is(self) -> None:
        assert WM_PACING.basis.startswith("OURS, AND FAR INSIDE THEIRS")
        assert "Robot Policy" in WM_PACING.basis


# ============================================================== the response


class TestAbsenceIsNotZero:
    def test_a_404_records_the_article_as_absent(self, context) -> None:
        """ADR-023, applied one layer up. The endpoint returns 404 for an article
        with no recorded views in the window. Writing a zero would be
        indistinguishable from a real measurement of zero, and nothing
        downstream could tell them apart."""
        transport = FakeTransport(["not found"], status=404)
        result = collect(context, transport)
        assert result.succeeded
        assert result.drafts == ()
        assert result.articles_absent == ("Kubernetes",)
        assert result.articles_returned == 0

    def test_an_absent_article_does_not_stop_the_others(self, context) -> None:
        transport = FakeTransport(["not found"], status=404)
        result = collect(
            context,
            transport,
            WikimediaPageviewsRequest(bounds=bounds(articles=("Kubernetes", "Podman"))),
        )
        assert result.requests_made == 2
        assert result.articles_absent == ("Kubernetes", "Podman")

    def test_no_payload_anywhere_carries_a_zero_we_invented(self, context) -> None:
        transport = FakeTransport(["not found"], status=404)
        result = collect(context, transport)
        assert all("views" not in d.payload for d in result.drafts)


class TestRefusalsRatherThanCoercion:
    def test_a_non_200_that_is_not_404_is_a_failure(self, context) -> None:
        transport = FakeTransport(["<html>rate limited</html>"], status=429)
        result = collect(context, transport)
        assert not result.succeeded
        assert "HTTP 429" in result.failure.detail

    def test_there_is_no_html_fallback(self, context) -> None:
        transport = FakeTransport(["<html>hello</html>"], status=200)
        result = collect(context, transport)
        assert not result.succeeded
        assert "not JSON" in result.failure.detail

    def test_a_non_integer_view_count_is_refused_not_coerced(self, context) -> None:
        transport = FakeTransport([envelope([{**item("2024030100", 0), "views": "many"}])])
        result = collect(context, transport)
        assert not result.succeeded
        assert "not a count" in result.failure.detail

    def test_a_missing_timestamp_is_refused(self, context) -> None:
        broken = {k: v for k, v in item("2024030100", 5).items() if k != "timestamp"}
        transport = FakeTransport([envelope([broken])])
        result = collect(context, transport)
        assert not result.succeeded
        assert "timestamp" in result.failure.detail

    def test_a_field_the_review_did_not_assess_arriving_is_a_failure(self, context) -> None:
        """Not a cleanup. By the time it could be dropped it has been fetched,
        and the endpoints next door are the ones that observe contributors."""
        transport = FakeTransport([envelope([{**item("2024030100", 5), "country": "FR"}])])
        result = collect(context, transport)
        assert not result.succeeded
        assert "did not assess" in result.failure.detail


# ================================================================= identity


class TestIdentity:
    def test_the_agent_class_is_part_of_the_key(self, context) -> None:
        """The same article on the same day has a different count under `user`
        and under `all-agents`. A key that omitted the agent would let two
        measurements collide on one identity, one silently overwriting the
        other as a revision."""
        transport = FakeTransport([envelope([item("2024030100", 10)])])
        key = collect(context, transport).drafts[0].observation_key
        assert WM_AGENT in key
        assert WM_PROJECT in key
        assert "Kubernetes" in key
        assert "2024030100" in key

    def test_the_key_is_not_the_view_count(self, context) -> None:
        """WHICH observation and WHAT the source said are different facts. A
        revised count must append a revision to one identity, not create a
        second observation."""
        first = FakeTransport([envelope([item("2024030100", 10)])])
        second = FakeTransport([envelope([item("2024030100", 11)])])
        a = collect(context, first).drafts[0]
        b = collect(context, second).drafts[0]
        assert a.observation_key == b.observation_key
        assert a.content_hash != b.content_hash

    def test_the_article_recorded_is_the_one_the_source_echoed(self, context) -> None:
        """Titles are normalised upstream. Recording our own request would
        attribute the source's data to a name the source did not use."""
        transport = FakeTransport(
            [envelope([item("2024030100", 10, article="Kubernetes_(software)")])]
        )
        draft = collect(
            context, transport, WikimediaPageviewsRequest(bounds=bounds(articles=("kubernetes",)))
        ).drafts[0]
        assert "Kubernetes_(software)" in draft.observation_key
        assert draft.provenance["article"] == "Kubernetes_(software)"
        assert draft.provenance["requested_article"] == "kubernetes"


# =============================================================== provenance


class TestProvenance:
    def test_the_record_says_which_population_was_counted(self, context) -> None:
        """The one fact a reader most needs and would most easily lose."""
        transport = FakeTransport([envelope([item("2024030100", 10)])])
        prov = collect(context, transport).drafts[0].provenance
        assert prov["agent"] == "user"
        assert "heuristic" in str(prov["agent_semantics"])

    def test_the_bounds_and_the_path_are_recorded(self, context) -> None:
        """Mission 1.15.10 found that an acquisition's bounds left no trace in
        the record. They leave one here."""
        transport = FakeTransport([envelope([item("2024030100", 10)])])
        prov = collect(context, transport).drafts[0].provenance
        assert prov["date_window"] == ["2024-03-01", "2024-03-05"]
        assert prov["max_articles"] == 5
        assert prov["max_days"] == 31
        assert prov["path"].startswith("metrics/pageviews/per-article/")

    def test_the_use_profile_and_the_user_agent_are_recorded(self, context) -> None:
        transport = FakeTransport([envelope([item("2024030100", 10)])])
        prov = collect(context, transport).drafts[0].provenance
        assert prov["use_profile"] == LOCAL_PROFILE
        assert prov["user_agent"] == DEFAULT_USER_AGENT

    def test_the_collector_names_and_versions_itself(self, context) -> None:
        transport = FakeTransport([envelope([item("2024030100", 10)])])
        draft = collect(context, transport).drafts[0]
        assert draft.collector_id == WM_COLLECTOR_ID
        assert draft.collector_version == WM_COLLECTOR_VERSION

    def test_the_source_reference_is_the_article_url(self, context) -> None:
        transport = FakeTransport([envelope([item("2024030100", 10)])])
        draft = collect(context, transport).drafts[0]
        assert draft.source_reference == "https://en.wikipedia.org/wiki/Kubernetes"

    def test_a_day_becomes_one_record(self, context) -> None:
        days = [item(f"202403{d:02d}00", 10 + d) for d in range(1, 6)]
        transport = FakeTransport([envelope(days)])
        result = collect(context, transport)
        assert len(result.drafts) == 5
        assert result.items_seen == 5
        assert result.requests_made == 1


# ============================================================ the resource


class TestTheResourceIsAuthorisedNotAssumed:
    def test_the_authorised_resource_is_the_narrow_one(self, context) -> None:
        dataset = context.authorized_dataset(WM_RESOURCE_ID)
        assert dataset is not None
        assert dataset.licence == "CC0-1.0"
        assert dataset.dataset_family == "wikimedia-pageviews-per-article"

    def test_the_endpoints_next_door_are_refused_by_name(self, context) -> None:
        for excluded in ("editor", "user_id", "country", "ip"):
            assert context.authorize_fields((*context.data_minimisation.allowed, excluded))

    def test_an_unreviewed_field_fails_closed(self, context) -> None:
        assert context.authorize_fields(("views", "something_nobody_reviewed"))

    def test_a_request_that_states_no_fields_is_refused(self, context) -> None:
        assert context.authorize_fields(())
