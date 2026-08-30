"""The World Bank collector: transport, pagination, records, persistence.

Mission 1.5 §42–§46. The authorization boundary is covered separately in
`test_collector_conformance.py`; this is everything else.

**No test here reaches the internet.** Every transport is a fake, and the one
that would reach it (`HttpxTransport`) is exercised only for its refusals, which
happen before a socket. §52: normal CI makes zero external requests.
"""

from __future__ import annotations

import contextlib
import json
import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import psycopg
import pytest
from sros_acquisition.collection import (
    COLLECTOR_ID,
    COLLECTOR_VERSION,
    CollectionBounds,
    HttpRequest,
    HttpResponse,
    PacingPolicy,
    RequestPacer,
    WorldBankCollector,
    WorldBankRequest,
    canonical_fingerprint,
    canonical_number,
    count_records,
    observation_key,
    persist_drafts,
    read_observation_history,
)
from sros_acquisition.collection.errors import AcquisitionFailedError
from sros_acquisition.collection.job import WorldBankJobPayload, run_world_bank_job
from sros_acquisition.collection.pacing import WORLD_BANK_PACING
from sros_acquisition.compliance import build_authorization, load_compliance
from sros_contracts import AcquisitionErrorCode

from .conftest import REPO_ROOT, WORKSPACE_A, WORKSPACE_P, needs_postgres

INDICATOR = "SP.POP.TOTL"
NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


@pytest.fixture(scope="session")
def compliance():
    return load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")


@pytest.fixture
def context(catalog, compliance):
    return build_authorization(catalog.get("world-bank"), compliance, environ={})


# ------------------------------------------------------------------ fake transports


@dataclass
class ScriptedTransport:
    """Returns a scripted response per call. Never opens a socket."""

    responses: list[object]
    calls: list[dict[str, str]] = field(default_factory=list)

    def get(
        self, base_url: str, request: HttpRequest, allowed_hosts: frozenset[str]
    ) -> HttpResponse:
        self.calls.append(dict(request.query))
        item = self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]
        if isinstance(item, BaseException):
            raise item
        if isinstance(item, HttpResponse):
            return item
        return HttpResponse(200, str(item), 0.01, request.path)


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "indicator": {"id": INDICATOR, "value": "Population, total"},
        "country": {"id": "FR", "value": "France"},
        "countryiso3code": "FRA",
        "date": "2020",
        "value": 67571107,
        "unit": "",
        "obs_status": "",
        "decimal": 0,
    }
    row.update(overrides)
    return row


def _envelope(rows: object, **meta: object) -> str:
    envelope: dict[str, object] = {
        "page": 1,
        "pages": 1,
        "per_page": 50,
        "total": 1,
        "lastupdated": "2025-07-01",
    }
    envelope.update(meta)
    return json.dumps([envelope, rows])


def _collector(transport: object, now: datetime = NOW, **kwargs: object) -> WorldBankCollector:
    return WorldBankCollector(
        transport,  # type: ignore[arg-type]
        pacer=RequestPacer(WORLD_BANK_PACING, sleep=lambda _: None),
        now=lambda: now,
        **kwargs,  # type: ignore[arg-type]
    )


def _collect(context, transport, request=None, workspace=WORKSPACE_A, **kwargs):
    return _collector(transport).collect(
        context,
        request or WorldBankRequest(indicators=(INDICATOR,), countries=("FR",)),
        workspace_id=workspace,
        correlation_id="test-correlation",
        **kwargs,
    )


# ============================================================================ HTTP


class TestHttpBehaviour:
    def test_a_successful_response_produces_records(self, context) -> None:
        result = _collect(context, ScriptedTransport([_envelope([_row()])]))
        assert result.succeeded
        assert len(result.drafts) == 1

    def test_a_timeout_is_normalised_and_retried(self, context) -> None:
        """§14, §42. A timeout is transient, so it is retried up to the bound
        and then reported as a normalised code -- never as the library's."""

        transport = ScriptedTransport([AcquisitionFailedError(_failure("NETWORK_TIMEOUT"))])
        result = _collect(context, transport)
        assert result.failures[0].code is AcquisitionErrorCode.NETWORK_TIMEOUT
        assert len(transport.calls) == 3  # the default max_attempts

    def test_a_429_is_retried_then_reported(self, context) -> None:
        transport = ScriptedTransport([HttpResponse(429, "", 0.01, "p")])
        result = _collect(context, transport)
        assert result.failures[0].code is AcquisitionErrorCode.RATE_LIMITED
        assert len(transport.calls) == 3

    def test_a_500_is_retried(self, context) -> None:
        transport = ScriptedTransport([HttpResponse(503, "", 0.01, "p")])
        result = _collect(context, transport)
        assert result.failures[0].code is AcquisitionErrorCode.TEMPORARY_UPSTREAM
        assert len(transport.calls) == 3

    def test_a_deterministic_4xx_is_never_retried(self, context) -> None:
        """§14. The same request produces the same rejection, and repeating it
        is how a rate limit becomes a ban. ONE call, not three."""
        transport = ScriptedTransport([HttpResponse(400, "", 0.01, "p")])
        result = _collect(context, transport)
        assert result.failures[0].code is AcquisitionErrorCode.UPSTREAM_CLIENT_ERROR
        assert len(transport.calls) == 1

    def test_a_transient_failure_that_then_succeeds_is_recovered(self, context) -> None:
        """The retry has to be able to succeed, or it is a delay dressed as a
        recovery."""
        transport = ScriptedTransport(
            [HttpResponse(503, "", 0.01, "p"), HttpResponse(200, _envelope([_row()]), 0.01, "p")]
        )
        result = _collect(context, transport)
        assert result.succeeded
        assert len(result.drafts) == 1

    def test_malformed_json_is_a_parsing_failure_and_is_not_retried(self, context) -> None:
        transport = ScriptedTransport(["{not json"])
        result = _collect(context, transport)
        assert result.failures[0].code is AcquisitionErrorCode.PARSING_FAILURE
        assert len(transport.calls) == 1

    def test_an_invalid_response_shape_is_reported_not_absorbed(self, context) -> None:
        """§14: a schema error is not retried. A source that changed its
        contract needs a person, not another attempt."""
        for body in ('{"page": 1}', "[]", '[{"a": 1}, [], "extra"]', "[[], []]"):
            result = _collect(context, ScriptedTransport([body]))
            assert result.failures[0].code is AcquisitionErrorCode.INVALID_RESPONSE, body

    def test_the_documented_error_envelope_is_a_client_error(self, context) -> None:
        body = json.dumps([{"message": [{"id": "120", "key": "Invalid value"}]}])
        result = _collect(context, ScriptedTransport([body]))
        assert result.failures[0].code is AcquisitionErrorCode.UPSTREAM_CLIENT_ERROR

    def test_a_failure_never_carries_a_response_body(self, context) -> None:
        """§33. The body is exactly what must not reach a job result."""
        secret = "a-value-that-must-not-be-echoed"
        result = _collect(context, ScriptedTransport([HttpResponse(400, secret, 0.01, "p")]))
        assert secret not in json.dumps(result.to_json())

    def test_retries_are_bounded_by_max_attempts(self, context) -> None:
        transport = ScriptedTransport([HttpResponse(503, "", 0.01, "p")])
        collector = _collector(transport, max_attempts=2)
        collector.collect(
            context,
            WorldBankRequest(indicators=(INDICATOR,)),
            workspace_id=WORKSPACE_A,
            correlation_id="c",
        )
        assert len(transport.calls) == 2

    def test_pacing_is_ours_and_says_so(self) -> None:
        """§13. The number is local and the basis says it is. A rate limit the
        source published and one we chose must never be written down as if they
        were the same thing."""
        assert "documents no rate limit" in WORLD_BANK_PACING.basis
        assert "World Bank" in WORLD_BANK_PACING.basis

    def test_the_pacer_waits_between_requests(self) -> None:
        slept: list[float] = []
        # The clock is consumed once by the first acquire, then twice by the
        # second: before the wait and after it.
        clock = iter([0.0, 0.05, 0.30])
        pacer = RequestPacer(
            PacingPolicy(0.25, 10, "test"),
            monotonic=lambda: next(clock),
            sleep=slept.append,
        )
        pacer.acquire()
        pacer.acquire()
        assert slept == [pytest.approx(0.20)]

    def test_the_per_job_request_ceiling_is_enforced(self) -> None:
        pacer = RequestPacer(PacingPolicy(0.0, 2, "test"), sleep=lambda _: None)
        pacer.acquire()
        pacer.acquire()
        with pytest.raises(RuntimeError, match="ceiling"):
            pacer.acquire()

    def test_the_transport_requires_finite_timeouts(self) -> None:
        from sros_acquisition.collection import TransportConfig

        for field_name in ("connect_timeout_seconds", "read_timeout_seconds"):
            with pytest.raises(ValueError, match="hang"):
                TransportConfig(**{field_name: 0})


def _failure(code: str):
    from sros_acquisition.collection.errors import AcquisitionFailure

    return AcquisitionFailure(
        code=AcquisitionErrorCode(code), detail="probe", source_id="world-bank"
    )


# ====================================================================== pagination


class TestPagination:
    def test_a_single_page_stops(self, context) -> None:
        transport = ScriptedTransport([_envelope([_row()], page=1, pages=1)])
        result = _collect(context, transport)
        assert len(transport.calls) == 1
        assert result.pages_read == 1

    def test_multiple_pages_are_followed_to_the_last(self, context) -> None:
        transport = ScriptedTransport(
            [
                _envelope([_row(date="2020")], page=1, pages=3),
                _envelope([_row(date="2019")], page=2, pages=3),
                _envelope([_row(date="2018")], page=3, pages=3),
            ]
        )
        result = _collect(context, transport)
        assert [c["page"] for c in transport.calls] == ["1", "2", "3"]
        assert len(result.drafts) == 3

    def test_repeated_page_metadata_is_refused_rather_than_looped(self, context) -> None:
        """§43. A source that keeps answering page 1 while we ask for 2 would
        otherwise spin until a bound stopped it -- and the bound would hide a
        real upstream fault behind a limit."""
        transport = ScriptedTransport([_envelope([_row()], page=1, pages=5)])
        result = _collect(context, transport)
        assert len(transport.calls) == 2
        assert result.failures[0].code is AcquisitionErrorCode.INVALID_RESPONSE
        assert "not advancing" in result.failures[0].detail

    def test_the_page_bound_stops_a_source_claiming_endless_pages(self, context) -> None:
        pages = [_envelope([_row(date=str(2000 + i))], page=i + 1, pages=9_999) for i in range(20)]
        transport = ScriptedTransport(pages)
        result = _collect(context, transport, bounds=CollectionBounds(max_pages=3))
        assert len(transport.calls) == 3
        assert result.pages_read == 3

    def test_the_record_bound_stops_mid_page(self, context) -> None:
        rows = [_row(date=str(2000 + i)) for i in range(50)]
        transport = ScriptedTransport([_envelope(rows, page=1, pages=1)])
        result = _collect(context, transport, bounds=CollectionBounds(max_records=7))
        assert len(result.drafts) == 7

    def test_an_empty_result_is_not_an_error(self, context) -> None:
        """A country/indicator pair with nothing to report is a real answer."""
        result = _collect(context, ScriptedTransport([_envelope(None, page=1, pages=1)]))
        assert result.succeeded
        assert result.drafts == []

    def test_malformed_metadata_does_not_loop(self, context) -> None:
        transport = ScriptedTransport([_envelope([_row()], page="x", pages="y")])
        result = _collect(context, transport)
        assert len(transport.calls) <= 2
        assert not result.succeeded

    def test_a_deadline_stops_before_the_next_request(self, context) -> None:
        """§31. A running request is not interrupted and nothing here claims it
        can be. What is guaranteed is that no NEW request starts."""
        transport = ScriptedTransport([_envelope([_row()], page=1, pages=9)])
        result = _collect(
            context, transport, bounds=CollectionBounds(deadline=NOW - timedelta(seconds=1))
        )
        assert transport.calls == []
        assert result.failures[0].code is AcquisitionErrorCode.CANCELLED

    def test_cancellation_stops_before_the_next_request(self, context) -> None:
        transport = ScriptedTransport([_envelope([_row()], page=1, pages=9)])
        result = _collect(context, transport, cancelled=lambda: True)
        assert transport.calls == []
        assert result.failures[0].code is AcquisitionErrorCode.CANCELLED


# ================================================================= record semantics


class TestRecordSemantics:
    def test_one_record_is_one_observation_not_one_response(self, context) -> None:
        """§17. A page carries observations that revise independently; storing
        the page would make one changed value invalidate the rest."""
        rows = [_row(date=str(2015 + i)) for i in range(5)]
        result = _collect(context, ScriptedTransport([_envelope(rows)]))
        assert len(result.drafts) == 5
        assert len({d.observation_key for d in result.drafts}) == 5

    def test_the_fingerprint_ignores_the_retrieval_time(self, context) -> None:
        """§25. Hashing it would make every retrieval a revision, which is how
        an idempotent collector becomes one that grows a table forever."""
        first = _collect(context, ScriptedTransport([_envelope([_row()])]))
        later = _collector(ScriptedTransport([_envelope([_row()])]), now=NOW + timedelta(days=9))
        second = later.collect(
            context,
            WorldBankRequest(indicators=(INDICATOR,), countries=("FR",)),
            workspace_id=WORKSPACE_A,
            correlation_id="c2",
        )
        assert first.drafts[0].content_hash == second.drafts[0].content_hash
        assert first.drafts[0].collected_at != second.drafts[0].collected_at

    def test_a_changed_value_changes_the_fingerprint(self, context) -> None:
        a = _collect(context, ScriptedTransport([_envelope([_row(value=1)])]))
        b = _collect(context, ScriptedTransport([_envelope([_row(value=2)])]))
        assert a.drafts[0].content_hash != b.drafts[0].content_hash
        # ...and it is the SAME observation, which is what makes it a revision.
        assert a.drafts[0].observation_key == b.drafts[0].observation_key

    def test_the_fingerprint_is_stable_across_key_order(self) -> None:
        assert canonical_fingerprint({"a": 1, "b": 2}) == canonical_fingerprint({"b": 2, "a": 1})

    def test_the_observation_key_refuses_an_ambiguous_part(self) -> None:
        with pytest.raises(ValueError, match="separator"):
            observation_key("world-bank", "indicator/X|Y", "FRA", "2020")

    def test_event_time_is_the_period_not_the_retrieval(self, context) -> None:
        """`data-principles.md` §9. Trend analysis on ingestion timestamps
        produces artifacts that look exactly like real market movements."""
        result = _collect(context, ScriptedTransport([_envelope([_row(date="2011")])]))
        assert result.drafts[0].observed_at == datetime(2011, 1, 1, tzinfo=UTC)
        assert result.drafts[0].payload["period"] == "2011"

    def test_retention_comes_from_governance_and_cannot_be_lengthened(self, context) -> None:
        """§21. There is no parameter through which a collector could ask for
        longer, and the window is the resolved raw-retention policy."""
        result = _collect(context, ScriptedTransport([_envelope([_row()])]))
        draft = result.drafts[0]
        assert draft.expires_at == draft.collected_at + timedelta(days=context.retention.raw_days)
        assert context.retention.raw_days == 30
        import inspect

        from sros_acquisition.collection.records import build_draft

        assert not {"expires_at", "retention_days", "attribution"} & set(
            inspect.signature(build_draft).parameters
        )

    def test_attribution_travels_with_every_record(self, context) -> None:
        """§20. Composed by the Mission 1.4 capability from the obligation the
        review recorded, never reconstructed by the collector."""
        result = _collect(context, ScriptedTransport([_envelope([_row()])]))
        draft = result.drafts[0]
        assert "The World Bank" in draft.attribution_text
        assert "CC-BY-4.0" in draft.attribution_text
        assert draft.provenance["attribution"]["source_id"] == "world-bank"  # type: ignore[index]

    def test_provenance_answers_every_question_section_19_asks(self, context) -> None:
        result = _collect(context, ScriptedTransport([_envelope([_row()])]))
        provenance = result.drafts[0].provenance
        for key in (
            "source_id",
            "access_profile",
            "review_version",
            "resource_id",
            "dataset_family",
            "indicator",
            "geography",
            "period",
            "licence",
            "content_origin",
            "attribution",
            "request_path",
            "page",
            "condition_snapshot",
        ):
            assert provenance.get(key) is not None, key
        assert result.drafts[0].correlation_id == "test-correlation"
        assert result.drafts[0].collector_id == "world-bank-indicators"

    def test_a_row_with_no_identity_is_skipped_not_invented(self, context) -> None:
        rows = [_row(), {"date": "2020", "value": 1}, _row(date="")]
        result = _collect(context, ScriptedTransport([_envelope(rows)]))
        assert len(result.drafts) == 1

    def test_a_null_value_is_kept(self, context) -> None:
        """An absence the source stated is a fact about the source; dropping it
        would make it indistinguishable from never having asked."""
        result = _collect(context, ScriptedTransport([_envelope([_row(value=None)])]))
        assert len(result.drafts) == 1
        assert result.drafts[0].payload["value"] is None

    def test_no_personal_data_category_is_collected(self, context) -> None:
        """§22. The payload carries the economic-series categories and nothing
        the minimisation profile excludes."""
        result = _collect(context, ScriptedTransport([_envelope([_row()])]))
        payload = result.drafts[0].payload
        assert set(payload) == {
            "source_id",
            "resource_id",
            "indicator",
            "geography",
            "geography_name",
            "period",
            "value",
            "unit",
            "obs_status",
            "decimals",
            "source_last_updated",
        }
        for excluded in context.data_minimisation.excluded:
            assert excluded not in payload


# ====================================================================== persistence


@needs_postgres
class TestPersistence:
    def test_a_record_is_written_with_its_provenance(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        result = _collect(
            context, ScriptedTransport([_envelope([_row()])]), workspace=probe_workspace
        )
        with tenant_conn(probe_workspace) as conn:
            report = persist_drafts(conn, result.drafts)
            assert report.new == 1
            row = conn.execute(
                """SELECT observation_key, content_hash, collector_id, collector_version,
                          review_version, correlation_id, provenance, payload,
                          observed_at, expires_at, collected_at, last_seen_at, superseded_at
                     FROM acquisition.raw_records WHERE workspace_id = %s""",
                (probe_workspace,),
            ).fetchone()
        assert row is not None
        assert row[0] == "world-bank|indicator/SP.POP.TOTL|FRA|2020"
        assert row[2] == "world-bank-indicators"
        assert row[4] == 2
        assert row[6]["licence"] == "CC-BY-4.0"
        # The canonical decimal STRING the 1.1.0 collector writes, derived
        # from the value the fixture sent rather than written out again --
        # two literals for one fact drift.
        assert row[7]["value"] == canonical_number(Decimal(_row()["value"]))
        assert row[8] == datetime(2020, 1, 1, tzinfo=UTC)
        assert row[9] == row[10] + timedelta(days=30)
        assert row[12] is None

    def test_the_same_response_twice_is_idempotent(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        """§23, §44. The second write finds the row and moves a timestamp."""
        result = _collect(
            context, ScriptedTransport([_envelope([_row()])]), workspace=probe_workspace
        )
        with tenant_conn(probe_workspace) as conn:
            first = persist_drafts(conn, result.drafts)
            second = persist_drafts(conn, result.drafts)
            total = count_records(conn, probe_workspace, "world-bank")
        assert (first.new, second.new, second.unchanged) == (1, 0, 1)
        assert total == 1

    def test_a_later_retrieval_moves_last_seen_without_a_new_row(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        first = _collect(
            context, ScriptedTransport([_envelope([_row()])]), workspace=probe_workspace
        )
        later = _collector(ScriptedTransport([_envelope([_row()])]), now=NOW + timedelta(days=2))
        second = later.collect(
            context,
            WorldBankRequest(indicators=(INDICATOR,), countries=("FR",)),
            workspace_id=probe_workspace,
            correlation_id="c2",
        )
        with tenant_conn(probe_workspace) as conn:
            persist_drafts(conn, first.drafts)
            report = persist_drafts(conn, second.drafts)
            row = conn.execute(
                "SELECT collected_at, last_seen_at FROM acquisition.raw_records "
                "WHERE workspace_id = %s",
                (probe_workspace,),
            ).fetchone()
        assert report.unchanged == 1
        assert row[1] > row[0]

    def test_an_upstream_revision_creates_a_linked_row_and_supersedes(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        """§24. Both statements are true about when the source made them, so the
        earlier one is superseded rather than overwritten."""
        original = _collect(
            context,
            ScriptedTransport([_envelope([_row(value=67571107)])]),
            workspace=probe_workspace,
        )
        revised_collector = _collector(
            ScriptedTransport([_envelope([_row(value=68000000)])]), now=NOW + timedelta(days=30)
        )
        revised = revised_collector.collect(
            context,
            WorldBankRequest(indicators=(INDICATOR,), countries=("FR",)),
            workspace_id=probe_workspace,
            correlation_id="c2",
        )
        with tenant_conn(probe_workspace) as conn:
            persist_drafts(conn, original.drafts)
            report = persist_drafts(conn, revised.drafts)
            history = read_observation_history(
                conn, probe_workspace, original.drafts[0].observation_key
            )
        assert report.revised == 1
        assert len(history) == 2
        assert [h["current"] for h in history] == [True, False]
        assert history[0]["payload"]["value"] == canonical_number(Decimal(68000000))
        assert history[1]["payload"]["value"] == canonical_number(Decimal(67571107))

    def test_a_rollback_leaves_no_partial_acquisition(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        """§44. Half a page is not a smaller success; it is a page whose
        provenance is now wrong."""
        result = _collect(
            context,
            ScriptedTransport([_envelope([_row(date=str(2000 + i)) for i in range(5)])]),
            workspace=probe_workspace,
        )
        with tenant_conn(probe_workspace) as conn:
            persist_drafts(conn, result.drafts)
            assert count_records(conn, probe_workspace, "world-bank") == 5
        # The fixture rolled the transaction back.
        with tenant_conn(probe_workspace) as conn:
            assert count_records(conn, probe_workspace, "world-bank") == 0

    def test_the_database_refuses_an_expiry_before_collection(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        result = _collect(
            context, ScriptedTransport([_envelope([_row()])]), workspace=probe_workspace
        )
        draft = replace(result.drafts[0], expires_at=result.drafts[0].collected_at)
        with tenant_conn(probe_workspace) as conn, pytest.raises(Exception, match="expiry_after"):
            persist_drafts(conn, [draft])


# ================================================================ tenant isolation


@needs_postgres
class TestTenantIsolation:
    def test_one_workspace_cannot_read_anothers_records(
        self, tenant_conn, second_workspace, context, probe_workspace
    ) -> None:
        """§45. Two workspaces, because an isolation assertion needs something
        to be isolated from."""
        result = _collect(
            context, ScriptedTransport([_envelope([_row()])]), workspace=probe_workspace
        )
        b_drafts = [replace(d, workspace_id=second_workspace) for d in result.drafts]
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as writer, writer.transaction():
            writer.execute("SET LOCAL ROLE sros_app")
            writer.execute("SELECT set_config('app.workspace_id', %s, true)", (second_workspace,))
            persist_drafts(writer, b_drafts)

        with tenant_conn(probe_workspace) as conn:
            # No WHERE workspace_id. The policy is what must answer.
            visible = conn.execute("SELECT count(*) FROM acquisition.raw_records").fetchone()[0]
        assert visible == 0

    def test_a_worker_cannot_write_into_another_workspace(
        self, tenant_conn, second_workspace, context, probe_workspace
    ) -> None:
        """The policy's WITH CHECK. A task whose payload named the wrong tenant
        must not be able to write there even so."""
        result = _collect(
            context, ScriptedTransport([_envelope([_row()])]), workspace=probe_workspace
        )
        smuggled = [replace(d, workspace_id=second_workspace) for d in result.drafts]
        # The policy's own error, not any exception: a row rejected for an
        # unrelated reason would pass a blind `raises` and prove nothing.
        with (
            tenant_conn(probe_workspace) as conn,
            pytest.raises(psycopg.errors.InsufficientPrivilege),
        ):
            persist_drafts(conn, smuggled)

    def test_a_query_with_no_tenant_filter_is_still_protected(
        self, tenant_conn, second_workspace, context, probe_workspace
    ) -> None:
        """ADR-012 layer two: a forgotten WHERE returns this tenant's rows only,
        rather than everyone's."""
        result = _collect(
            context, ScriptedTransport([_envelope([_row()])]), workspace=probe_workspace
        )
        with tenant_conn(probe_workspace) as conn:
            persist_drafts(conn, result.drafts)
            rows = conn.execute(
                "SELECT DISTINCT workspace_id FROM acquisition.raw_records"
            ).fetchall()
        assert [str(r[0]) for r in rows] == [probe_workspace]

    def test_a_missing_tenant_context_returns_nothing(self, context) -> None:
        """A connection with no workspace set returns no rows rather than wrong
        ones -- the failure mode ADR-012 chose deliberately."""
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn, conn.transaction(force_rollback=True):
            conn.execute("SET LOCAL ROLE sros_app")
            visible = conn.execute("SELECT count(*) FROM acquisition.raw_records").fetchone()[0]
        assert visible == 0


# ============================================================================ jobs


class TestJobPayload:
    def test_a_payload_without_a_workspace_is_refused(self) -> None:
        """§29. A worker never resolves the workspace itself and never falls
        back to a default (ADR-005)."""
        for missing in ("workspace_id", "research_session_id", "correlation_id"):
            payload = {
                "workspace_id": WORKSPACE_A,
                "research_session_id": str(uuid.uuid4()),
                "correlation_id": "c",
                "indicators": [INDICATOR],
            }
            del payload[missing]
            with pytest.raises(ValueError, match="missing required headers"):
                WorldBankJobPayload.from_payload(payload)

    def test_a_payload_without_an_indicator_is_refused(self) -> None:
        with pytest.raises(ValueError, match="at least one indicator"):
            WorldBankJobPayload.from_payload(
                {
                    "workspace_id": WORKSPACE_A,
                    "research_session_id": str(uuid.uuid4()),
                    "correlation_id": "c",
                }
            )

    def test_the_idempotency_key_is_stable_across_deliveries(self) -> None:
        """§30. Two deliveries of the same logical job share it; the retrieval
        time is deliberately absent, or every redelivery would be a new job."""
        base = {
            "workspace_id": WORKSPACE_A,
            "research_session_id": str(uuid.uuid4()),
            "correlation_id": "c",
            "indicators": [INDICATOR, "NY.GDP.MKTP.CD"],
            "countries": ["FR", "DE"],
        }
        first = WorldBankJobPayload.from_payload(base)
        # Order must not matter: the same work described differently is the
        # same work.
        shuffled = {**base, "indicators": ["NY.GDP.MKTP.CD", INDICATOR], "countries": ["DE", "FR"]}
        assert first.idempotency_key == WorldBankJobPayload.from_payload(shuffled).idempotency_key
        assert (
            first.idempotency_key
            != WorldBankJobPayload.from_payload({**base, "countries": ["FR"]}).idempotency_key
        )

    def test_a_payload_cannot_carry_an_authorization(self) -> None:
        """The gate runs inside the job. A serialized permission would outlive
        the state it came from, and a source suspended between planning and
        execution would still be collected."""
        fields = set(WorldBankJobPayload.__dataclass_fields__)
        assert not fields & {"authorization", "context", "token", "allowed_hosts", "url"}

    def test_a_job_refuses_an_ineligible_source(self, catalog, compliance) -> None:
        payload = {
            "workspace_id": WORKSPACE_A,
            "research_session_id": str(uuid.uuid4()),
            "correlation_id": "c",
            "indicators": [INDICATOR],
            "source_id": "youtube",
        }
        result = run_world_bank_job(
            payload,
            connection_factory=_never_called,
            catalog=catalog,
            compliance=compliance,
        )
        assert not result.succeeded
        assert result.failures[0].code is AcquisitionErrorCode.AUTHORIZATION_REJECTED
        assert result.persisted.total == 0


def _never_called(workspace_id: str):  # pragma: no cover - asserted by not being called
    raise AssertionError("a refused job must not open a connection")


@needs_postgres
class TestJobExecution:
    def test_a_job_refuses_a_source_whose_collector_is_not_enabled(
        self, tenant_conn, catalog, compliance, probe_workspace, disabled_world_bank
    ) -> None:
        """§27, §46. Eligible says *may we*; enabled says *is it turned on*.

        This gate exists because a test in the Mission 1.4 suite enabled a real
        collector as a side effect of asserting it could not be enabled -- the
        moment World Bank gained one. The switch is now checked before anything
        is fetched, so an unenabled source costs zero requests."""
        transport = ScriptedTransport([_envelope([_row()])])
        result = run_world_bank_job(
            _payload(),
            connection_factory=tenant_conn,
            catalog=catalog,
            compliance=compliance,
            transport=transport,
        )
        assert transport.calls == []
        assert result.failures[0].code is AcquisitionErrorCode.AUTHORIZATION_REJECTED
        assert "not enabled" in result.failures[0].detail
        assert result.persisted.total == 0

    def test_an_enabled_source_collects_and_persists(
        self, tenant_conn, catalog, compliance, probe_workspace, enabled_world_bank, dev_session
    ) -> None:
        transport = ScriptedTransport([_envelope([_row()])])
        result = run_world_bank_job(
            _payload(research_session_id=dev_session),
            connection_factory=tenant_conn,
            catalog=catalog,
            compliance=compliance,
            collector=_collector(transport),
        )
        assert result.succeeded, result.to_json()
        assert result.persisted.new == 1
        # Pinned to the constants, not to a literal: a version bump is a
        # deliberate act (Mission 1.6.1 §5) and should not also require
        # editing an assertion that was only ever restating them.
        assert result.collector == f"{COLLECTOR_ID}@{COLLECTOR_VERSION}"

    def test_duplicate_delivery_writes_no_second_row(
        self, catalog, compliance, probe_workspace, enabled_world_bank, dev_session
    ) -> None:
        """§30. At-least-once delivery, and nothing here claims exactly-once:
        the second delivery re-collects, finds every observation unchanged and
        moves a timestamp instead of writing a row.

        Both deliveries share one connection, because a redelivery that could
        not see the first delivery's rows would prove nothing."""
        payload = _payload(research_session_id=dev_session)
        results = []
        with _shared_connection() as (connection, factory):
            for _ in range(2):
                results.append(
                    run_world_bank_job(
                        payload,
                        connection_factory=factory,
                        catalog=catalog,
                        compliance=compliance,
                        collector=_collector(ScriptedTransport([_envelope([_row()])])),
                    )
                )
            stored = connection.execute(
                "SELECT count(*) FROM acquisition.raw_records WHERE workspace_id = %s",
                (WORKSPACE_P,),
            ).fetchone()[0]

        assert results[0].persisted.new == 1
        assert results[1].persisted.unchanged == 1
        assert results[1].persisted.new == 0
        assert stored == 1
        assert results[0].idempotency_key == results[1].idempotency_key

    def test_correlation_and_session_travel_into_every_record(
        self, catalog, compliance, probe_workspace, enabled_world_bank, dev_session
    ) -> None:
        """§29, §34. A record that cannot be traced back to the job that wrote
        it is a record nobody can debug."""
        with _shared_connection() as (connection, factory):
            result = run_world_bank_job(
                {**_payload(research_session_id=dev_session), "correlation_id": "corr-xyz"},
                connection_factory=factory,
                catalog=catalog,
                compliance=compliance,
                collector=_collector(ScriptedTransport([_envelope([_row()])])),
            )
            assert result.succeeded, result.to_json()
            assert result.persisted.new == 1
            rows = connection.execute(
                """SELECT correlation_id, research_session_id, collector_id,
                          collector_version, review_version
                     FROM acquisition.raw_records WHERE workspace_id = %s""",
                (WORKSPACE_P,),
            ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "corr-xyz"
        assert str(rows[0][1]) == dev_session
        assert rows[0][2] == "world-bank-indicators"
        assert rows[0][4] == 2

    def test_a_persistence_failure_is_normalised_not_leaked(
        self, catalog, compliance, enabled_world_bank
    ) -> None:
        """§32, §33. The orchestrator branches on a meaning, and a driver's
        exception text never reaches a job result."""
        import contextlib

        secret = "postgresql://user:hunter2@host/db"
        # The switch check opens the first connection, so the factory reports
        # enabled once and then fails -- which is what puts the failure in
        # PERSISTENCE rather than in the gate.
        calls = {"n": 0}

        @contextlib.contextmanager
        def enabled_then_broken(workspace_id: str):
            calls["n"] += 1
            if calls["n"] == 1:

                class Ok:
                    def execute(self, *args: object, **kwargs: object) -> object:
                        class R:
                            def fetchone(self) -> tuple[bool]:
                                return (True,)

                        return R()

                yield Ok()
            else:

                class Failing:
                    def execute(self, *args: object, **kwargs: object) -> object:
                        raise RuntimeError(secret)

                yield Failing()

        result = run_world_bank_job(
            _payload(),
            connection_factory=enabled_then_broken,
            catalog=catalog,
            compliance=compliance,
            collector=_collector(ScriptedTransport([_envelope([_row()])])),
        )
        blob = json.dumps(result.to_json())
        assert result.failures[-1].code is AcquisitionErrorCode.PERSISTENCE_FAILURE
        assert "hunter2" not in blob
        assert secret not in blob
        assert result.persisted.total == 0


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "workspace_id": WORKSPACE_P,
        "research_session_id": str(uuid.uuid4()),
        "correlation_id": "job-test",
        "indicators": [INDICATOR],
        "countries": ["FR"],
        "start_year": 2020,
        "end_year": 2020,
    }
    payload.update(overrides)
    return payload


@contextlib.contextmanager
def _shared_connection(workspace_id: str = WORKSPACE_P):
    """One tenant transaction, handed to every call, rolled back at the end.

    A job normally opens its own connection per step, which is right in
    production and useless in a test that has to observe what a previous call
    wrote. This shares one so two deliveries see each other, and rolls back so
    nothing survives the test.
    """
    import psycopg

    from .conftest import DATABASE_URL

    connection = psycopg.connect(DATABASE_URL)
    try:
        with connection.transaction(force_rollback=True):
            connection.execute("SET LOCAL ROLE sros_app")
            connection.execute("SELECT set_config('app.workspace_id', %s, true)", (workspace_id,))

            @contextlib.contextmanager
            def factory(workspace_id: str):
                yield connection

            yield connection, factory
    finally:
        connection.close()
