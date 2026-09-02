"""Persisting WEB-NGRAM observations, and the job that does it.

Mission 1.9.3 §31, §34, §41, §48, §49. Everything here uses fixture files; no
test contacts GDELT.

The persistence assertions are the ones that decide whether duplicate Celery
delivery is safe, so each is written against what the DATABASE holds rather than
against what the collector returned.
"""

from __future__ import annotations

from dataclasses import replace

import psycopg
import pytest
from sros_acquisition.collection import (
    GdeltWebNgramCollector,
    WebNgramRequest,
    count_records,
    persist_drafts,
    read_observation_history,
)
from sros_acquisition.collection.job import (
    WebNgramJobPayload,
    run_gdelt_web_ngram_job,
)
from sros_acquisition.collection.pacing import WEB_NGRAM_PACING, RequestPacer
from sros_acquisition.compliance import build_authorization
from sros_contracts import AcquisitionErrorCode

from .conftest import DATABASE_URL, LEGACY_PROFILE, REPO_ROOT, needs_postgres
from .web_ngram_fixtures import (
    BUCKET,
    NOT_GZIP,
    FakeStreamingTransport,
    revised_unigram_file,
    transport_with_defaults,
)

UNIGRAM = "web-ngrams/1gram"
CORRELATION = "web-ngram-job"
ENGLISH_ONLY = ("ENGLISH",)


@pytest.fixture(scope="session")
def compliance():
    from sros_acquisition.compliance import load_compliance

    return load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")


@pytest.fixture(scope="session")
def context(catalog, compliance):
    return build_authorization(catalog.get("gdelt"), LEGACY_PROFILE, compliance)


def collect_into(workspace, context, transport=None, **request_kwargs):
    collector = GdeltWebNgramCollector(
        transport or transport_with_defaults(),
        pacer=RequestPacer(WEB_NGRAM_PACING, sleep=lambda _: None),
    )
    return collector.collect(
        context,
        WebNgramRequest(buckets=(BUCKET,), languages=ENGLISH_ONLY, **request_kwargs),
        workspace_id=workspace,
        correlation_id=CORRELATION,
    )


@pytest.fixture()
def enabled_gdelt():
    """Turn the operational switch on for one test, then restore it.

    Enabled through the DATABASE, which refuses it for an ineligible source, so
    this fixture cannot make a source collectable that the gate would not clear.
    It RESTORES rather than forcing false: a test that changes the deployment and
    does not put it back is a test that decides what production does.
    """
    with psycopg.connect(DATABASE_URL) as connection:
        previous = connection.execute(
            "SELECT collector_enabled FROM registry.sources WHERE id = 'gdelt'"
        ).fetchone()[0]
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = TRUE, "
            "collector_use_profile = 'commercial-multi-tenant-research-v1' "
            "WHERE id = 'gdelt'"
        )
        connection.commit()
    yield "gdelt"
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = %s WHERE id = 'gdelt'",
            (previous,),
        )
        connection.commit()


@pytest.fixture()
def disabled_gdelt():
    """Turn the operational switch OFF for one test, then restore it.

    The mirror of `enabled_gdelt`, and it exists because two tests below were
    relying on the DEPLOYMENT rather than setting the state they need. They
    passed for as long as nobody had run `sros-source enable gdelt`, and went red
    the moment Mission 1.9.3's controlled acquisition did -- which is
    `testing-strategy.md` §10 in its purest form: an assertion about the
    environment wearing the clothes of an assertion about behaviour.
    """
    with psycopg.connect(DATABASE_URL) as connection:
        previous = connection.execute(
            "SELECT collector_enabled FROM registry.sources WHERE id = 'gdelt'"
        ).fetchone()[0]
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = FALSE WHERE id = 'gdelt'"
        )
        connection.commit()
    yield "gdelt"
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = %s WHERE id = 'gdelt'",
            (previous,),
        )
        connection.commit()


# ==================================================================== persistence


@needs_postgres
class TestPersistence:
    def test_one_row_becomes_one_record_with_its_provenance(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        """§23. One RawRecord is one source observation, not one file."""
        result = collect_into(probe_workspace, context, ngrams=("climate",))
        with tenant_conn(probe_workspace) as conn:
            report = persist_drafts(conn, result.drafts)
            row = conn.execute(
                """SELECT observation_key, content_hash, collector_id, collector_version,
                          review_version, correlation_id, provenance, payload,
                          observed_at, expires_at, collected_at, content_language,
                          source_reference, acquisition_method
                     FROM acquisition.raw_records
                    WHERE workspace_id = %s AND source_id = 'gdelt'""",
                (probe_workspace,),
            ).fetchone()
        assert report.new == 1
        assert row is not None
        assert row[0] == f"gdelt|{UNIGRAM}|{BUCKET}|ENGLISH|climate"
        assert row[2] == "gdelt-web-ngram"
        assert row[3] == "1.0.0"
        assert row[4] == 3
        assert row[6]["rights_basis"] == "DIRECT_GRANT"
        assert row[6]["licence"] is None
        assert row[6]["source_bucket_label"] == BUCKET
        assert row[6]["source_language_label"] == "ENGLISH"
        assert row[7]["count"] == "48210"
        assert row[7]["date"] == BUCKET
        # H-29: no timezone was established, so no event time is claimed.
        assert row[8] is None
        # H-30: the canonical language column stays empty rather than holding a
        # name a reader would take for a code.
        assert row[11] is None
        assert row[13] == "DATASET_DOWNLOAD"

    def test_the_expiry_is_the_governance_window(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        """§29. Thirty days, from the context and not from the collector."""
        from datetime import timedelta

        result = collect_into(probe_workspace, context, ngrams=("climate",))
        with tenant_conn(probe_workspace) as conn:
            persist_drafts(conn, result.drafts)
            row = conn.execute(
                "SELECT collected_at, expires_at FROM acquisition.raw_records "
                "WHERE workspace_id = %s AND source_id = 'gdelt'",
                (probe_workspace,),
            ).fetchone()
        assert row[1] == row[0] + timedelta(days=30)

    def test_the_same_file_twice_is_idempotent(self, tenant_conn, context, probe_workspace) -> None:
        """§34. First run NEW, second run UNCHANGED, one row."""
        first = collect_into(probe_workspace, context)
        second = collect_into(probe_workspace, context)
        with tenant_conn(probe_workspace) as conn:
            one = persist_drafts(conn, first.drafts)
            two = persist_drafts(conn, second.drafts)
            total = count_records(conn, probe_workspace, "gdelt")
        assert one.new == 3
        assert (two.new, two.unchanged) == (0, 3)
        assert total == 3

    def test_a_changed_count_is_a_revision_not_a_new_observation(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        """§34. GDELT correcting a COUNT supersedes rather than overwrites: what
        it said before is still true about when it said it."""
        first = collect_into(probe_workspace, context, ngrams=("climate",))
        revised = collect_into(
            probe_workspace,
            context,
            transport=FakeStreamingTransport(
                files={f"{BUCKET}.1gram.txt.gz": revised_unigram_file()}
            ),
            ngrams=("climate",),
        )
        key = f"gdelt|{UNIGRAM}|{BUCKET}|ENGLISH|climate"
        with tenant_conn(probe_workspace) as conn:
            persist_drafts(conn, first.drafts)
            report = persist_drafts(conn, revised.drafts)
            history = read_observation_history(conn, probe_workspace, key)
        assert report.revised == 1
        assert len(history) == 2
        current = [h for h in history if h["current"]]
        assert len(current) == 1
        assert current[0]["payload"]["count"] == "48999"
        superseded = [h for h in history if not h["current"]]
        assert superseded[0]["payload"]["count"] == "48210"

    def test_a_rollback_leaves_no_partial_acquisition(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        """§32. Half a file is not a smaller success."""
        result = collect_into(probe_workspace, context)
        with tenant_conn(probe_workspace) as conn:
            persist_drafts(conn, result.drafts)
        with tenant_conn(probe_workspace) as conn:
            assert count_records(conn, probe_workspace, "gdelt") == 0

    def test_the_two_resources_coexist_without_colliding(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        """§26. `climate` appears in the unigram file and `climate change` in the
        bigram file; the resource id is in the key, so neither shadows the other."""
        collector = GdeltWebNgramCollector(
            transport_with_defaults(),
            pacer=RequestPacer(WEB_NGRAM_PACING, sleep=lambda _: None),
        )
        result = collector.collect(
            context,
            WebNgramRequest(buckets=(BUCKET,), grams=("1gram", "2gram"), languages=ENGLISH_ONLY),
            workspace_id=probe_workspace,
            correlation_id=CORRELATION,
        )
        with tenant_conn(probe_workspace) as conn:
            persist_drafts(conn, result.drafts)
            families = conn.execute(
                """SELECT DISTINCT provenance ->> 'dataset_family'
                     FROM acquisition.raw_records
                    WHERE workspace_id = %s AND source_id = 'gdelt' ORDER BY 1""",
                (probe_workspace,),
            ).fetchall()
        assert [f[0] for f in families] == ["web-ngrams-1gram", "web-ngrams-2gram"]

    def test_attribution_reaches_the_stored_record(
        self, tenant_conn, context, probe_workspace
    ) -> None:
        """§28. A record whose obligation could not be resolved fails
        persistence rather than arriving without credit."""
        result = collect_into(probe_workspace, context, ngrams=("climate",))
        with tenant_conn(probe_workspace) as conn:
            persist_drafts(conn, result.drafts)
            provenance = conn.execute(
                "SELECT provenance FROM acquisition.raw_records "
                "WHERE workspace_id = %s AND source_id = 'gdelt'",
                (probe_workspace,),
            ).fetchone()[0]
        text = provenance["attribution"]["text"]
        assert "The GDELT Project" in text
        assert "https://www.gdeltproject.org/" in text


@needs_postgres
class TestTenantIsolation:
    def test_one_workspace_cannot_read_anothers_records(
        self, tenant_conn, second_workspace, context, probe_workspace
    ) -> None:
        """§49. Two workspaces, because an isolation assertion needs something
        to be isolated from."""
        result = collect_into(probe_workspace, context, ngrams=("climate",))
        elsewhere = [replace(d, workspace_id=second_workspace) for d in result.drafts]
        with psycopg.connect(DATABASE_URL) as writer, writer.transaction():
            writer.execute("SET LOCAL ROLE sros_app")
            writer.execute("SELECT set_config('app.workspace_id', %s, true)", (second_workspace,))
            persist_drafts(writer, elsewhere)

        with tenant_conn(probe_workspace) as conn:
            # No WHERE workspace_id. The policy is what must answer.
            visible = conn.execute(
                "SELECT count(*) FROM acquisition.raw_records WHERE source_id = 'gdelt'"
            ).fetchone()[0]
        assert visible == 0

    def test_a_worker_cannot_write_into_another_workspace(
        self, tenant_conn, second_workspace, context, probe_workspace
    ) -> None:
        """The policy's WITH CHECK. A payload naming the wrong tenant must not be
        able to write there even so."""
        result = collect_into(probe_workspace, context, ngrams=("climate",))
        smuggled = [replace(d, workspace_id=second_workspace) for d in result.drafts]
        with (
            tenant_conn(probe_workspace) as conn,
            pytest.raises(psycopg.errors.InsufficientPrivilege),
        ):
            persist_drafts(conn, smuggled)

    def test_a_query_with_no_tenant_filter_is_still_scoped(
        self, tenant_conn, second_workspace, context, probe_workspace
    ) -> None:
        result = collect_into(probe_workspace, context, ngrams=("climate",))
        with tenant_conn(probe_workspace) as conn:
            persist_drafts(conn, result.drafts)
            rows = conn.execute(
                "SELECT DISTINCT workspace_id FROM acquisition.raw_records "
                "WHERE source_id = 'gdelt'"
            ).fetchall()
        assert [str(r[0]) for r in rows] == [probe_workspace]


# ======================================================================= the job


class TestJobPayload:
    def test_a_payload_without_a_workspace_is_refused(self) -> None:
        with pytest.raises(ValueError, match="workspace_id"):
            WebNgramJobPayload.from_payload(
                {"research_session_id": "s", "correlation_id": "c", "buckets": [BUCKET]}
            )

    def test_a_payload_without_a_bucket_is_refused(self) -> None:
        """§37. There is no discovery crawl: a job collects the buckets it was
        told to, and an empty list is not 'find me something'."""
        with pytest.raises(ValueError, match="bucket"):
            WebNgramJobPayload.from_payload(
                {
                    "workspace_id": "w",
                    "research_session_id": "s",
                    "correlation_id": "c",
                    "buckets": [],
                }
            )

    def test_a_payload_naming_an_unreviewed_gram_kind_is_refused(self) -> None:
        with pytest.raises(ValueError, match="gram kind"):
            WebNgramJobPayload.from_payload(
                {
                    "workspace_id": "w",
                    "research_session_id": "s",
                    "correlation_id": "c",
                    "buckets": [BUCKET],
                    "grams": ["3gram"],
                }
            )

    def test_a_payload_cannot_carry_a_url_or_a_filename(self) -> None:
        fields = set(WebNgramJobPayload.__dataclass_fields__)
        for forbidden in ("url", "path", "host", "filename", "base_url", "endpoint"):
            assert forbidden not in fields

    def test_a_payload_cannot_carry_an_authorization(self) -> None:
        """§41. A serialized permission outlives the state it came from, so the
        payload has no field for one and the class does not mention the type.

        Asserted HERE rather than in the worker suite, which runs
        zero-dependency: importing this class from `sros_workers` passes on a
        machine with the workspace installed and fails in CI, and the boundary
        rule says the same thing anyway.
        """
        import inspect

        fields = set(WebNgramJobPayload.__dataclass_fields__)
        for forbidden in ("context", "authorization", "datasets", "resource_scope"):
            assert forbidden not in fields
        assert "AcquisitionAuthorizationContext" not in inspect.getsource(WebNgramJobPayload)

    def test_the_idempotency_key_is_stable_and_covers_the_filters(self) -> None:
        """Two deliveries of one logical job share it; two jobs over the same
        files with different filters do not, because they persist different
        observations."""
        base = {
            "workspace_id": "w",
            "research_session_id": "s",
            "correlation_id": "c1",
            "buckets": [BUCKET],
        }
        first = WebNgramJobPayload.from_payload(base)
        redelivered = WebNgramJobPayload.from_payload({**base, "correlation_id": "c2"})
        filtered = WebNgramJobPayload.from_payload({**base, "languages": ["ENGLISH"]})
        assert first.idempotency_key == redelivered.idempotency_key
        assert first.idempotency_key != filtered.idempotency_key


@needs_postgres
class TestJobExecution:
    def test_a_job_refuses_a_source_whose_collector_is_not_enabled(
        self, catalog, compliance, tenant_conn, probe_workspace, dev_session, disabled_gdelt
    ) -> None:
        """§43. Eligibility says *may we*; the switch says *is it on*. The job
        must not take that decision on an operator's behalf."""
        result = run_gdelt_web_ngram_job(
            {
                "workspace_id": probe_workspace,
                "research_session_id": dev_session,
                "correlation_id": CORRELATION,
                "buckets": [BUCKET],
            },
            tenant_conn,
            catalog=catalog,
            compliance=compliance,
            transport=transport_with_defaults(),
            use_profile=LEGACY_PROFILE,
        )
        assert not result.succeeded
        assert result.failures[0].code is AcquisitionErrorCode.AUTHORIZATION_REJECTED
        assert "not enabled" in result.failures[0].detail

    def test_an_enabled_source_collects_and_persists(
        self,
        catalog,
        compliance,
        committing_tenant_conn,
        probe_workspace,
        dev_session,
        enabled_gdelt,
    ) -> None:
        transport = transport_with_defaults()
        result = run_gdelt_web_ngram_job(
            {
                "workspace_id": probe_workspace,
                "research_session_id": dev_session,
                "correlation_id": CORRELATION,
                "buckets": [BUCKET],
                "languages": ["ENGLISH"],
            },
            committing_tenant_conn,
            catalog=catalog,
            compliance=compliance,
            collector=GdeltWebNgramCollector(
                transport, pacer=RequestPacer(WEB_NGRAM_PACING, sleep=lambda _: None)
            ),
            use_profile=LEGACY_PROFILE,
        )
        assert result.succeeded, result.failures
        assert result.persisted.new == 3
        assert result.files_requested == 1
        assert result.files_processed == 1
        assert result.rows_scanned == 9
        assert result.rows_matched == 3
        assert result.collector == "gdelt-web-ngram@1.0.0"

    def test_duplicate_delivery_writes_no_second_row(
        self,
        catalog,
        compliance,
        committing_tenant_conn,
        probe_workspace,
        dev_session,
        enabled_gdelt,
    ) -> None:
        """§54. At-least-once delivery is safe; this does not claim
        exactly-once, and the second delivery re-collects."""
        payload = {
            "workspace_id": probe_workspace,
            "research_session_id": dev_session,
            "correlation_id": CORRELATION,
            "buckets": [BUCKET],
            "languages": ["ENGLISH"],
        }

        def run():
            return run_gdelt_web_ngram_job(
                payload,
                committing_tenant_conn,
                catalog=catalog,
                compliance=compliance,
                collector=GdeltWebNgramCollector(
                    transport_with_defaults(),
                    pacer=RequestPacer(WEB_NGRAM_PACING, sleep=lambda _: None),
                ),
                use_profile=LEGACY_PROFILE,
            )

        first, second = run(), run()
        assert first.persisted.new == 3
        assert (second.persisted.new, second.persisted.unchanged) == (0, 3)
        with psycopg.connect(DATABASE_URL) as conn, conn.transaction(force_rollback=True):
            conn.execute("SET LOCAL ROLE sros_app")
            conn.execute("SELECT set_config('app.workspace_id', %s, true)", (probe_workspace,))
            assert count_records(conn, probe_workspace, "gdelt") == 3

    def test_a_failed_file_persists_nothing_from_that_file(
        self,
        catalog,
        compliance,
        committing_tenant_conn,
        probe_workspace,
        dev_session,
        enabled_gdelt,
    ) -> None:
        """§32 and §33. Per-file: the good file persists, the bad one does not,
        and the report says which was which."""
        transport = transport_with_defaults()
        transport.files[f"{BUCKET}.2gram.txt.gz"] = NOT_GZIP
        result = run_gdelt_web_ngram_job(
            {
                "workspace_id": probe_workspace,
                "research_session_id": dev_session,
                "correlation_id": CORRELATION,
                "buckets": [BUCKET],
                "grams": ["1gram", "2gram"],
                "languages": ["ENGLISH"],
            },
            committing_tenant_conn,
            catalog=catalog,
            compliance=compliance,
            collector=GdeltWebNgramCollector(
                transport, pacer=RequestPacer(WEB_NGRAM_PACING, sleep=lambda _: None)
            ),
            use_profile=LEGACY_PROFILE,
        )
        assert result.files_processed == 1
        assert result.files_failed == 1
        assert result.persisted.new == 3
        assert not result.succeeded

    def test_correlation_and_session_travel_into_every_record(
        self,
        catalog,
        compliance,
        committing_tenant_conn,
        probe_workspace,
        dev_session,
        enabled_gdelt,
    ) -> None:
        run_gdelt_web_ngram_job(
            {
                "workspace_id": probe_workspace,
                "research_session_id": dev_session,
                "correlation_id": "trace-me",
                "buckets": [BUCKET],
                "languages": ["ENGLISH"],
            },
            committing_tenant_conn,
            catalog=catalog,
            compliance=compliance,
            collector=GdeltWebNgramCollector(
                transport_with_defaults(),
                pacer=RequestPacer(WEB_NGRAM_PACING, sleep=lambda _: None),
            ),
            use_profile=LEGACY_PROFILE,
        )
        with psycopg.connect(DATABASE_URL) as conn, conn.transaction(force_rollback=True):
            conn.execute("SET LOCAL ROLE sros_app")
            conn.execute("SELECT set_config('app.workspace_id', %s, true)", (probe_workspace,))
            rows = conn.execute(
                "SELECT correlation_id, research_session_id FROM acquisition.raw_records "
                "WHERE workspace_id = %s AND source_id = 'gdelt'",
                (probe_workspace,),
            ).fetchall()
        assert rows
        assert {r[0] for r in rows} == {"trace-me"}
        assert {str(r[1]) for r in rows} == {dev_session}

    def test_the_job_rebuilds_the_authorization_rather_than_trusting_the_payload(
        self, catalog, compliance, tenant_conn, probe_workspace, dev_session, disabled_gdelt
    ) -> None:
        """§41. A payload key that looks like an authorization changes nothing —
        the gate runs from the registry at execution time."""
        result = run_gdelt_web_ngram_job(
            {
                "workspace_id": probe_workspace,
                "research_session_id": dev_session,
                "correlation_id": CORRELATION,
                "buckets": [BUCKET],
                "authorization": {"allowed": True},
                "max_files_per_job": 99,
            },
            tenant_conn,
            catalog=catalog,
            compliance=compliance,
            transport=transport_with_defaults(),
            use_profile=LEGACY_PROFILE,
        )
        # Refused on the operational switch, which is the next gate — proof that
        # the smuggled keys did not shortcut anything.
        assert not result.succeeded
        assert "not enabled" in result.failures[0].detail

    def test_a_job_over_the_reviewed_ceiling_never_reaches_the_transport(
        self,
        catalog,
        compliance,
        committing_tenant_conn,
        probe_workspace,
        dev_session,
        enabled_gdelt,
    ) -> None:
        transport = transport_with_defaults()
        buckets = [f"20260830{h:02d}0000" for h in range(9)]
        result = run_gdelt_web_ngram_job(
            {
                "workspace_id": probe_workspace,
                "research_session_id": dev_session,
                "correlation_id": CORRELATION,
                "buckets": buckets,
            },
            committing_tenant_conn,
            catalog=catalog,
            compliance=compliance,
            collector=GdeltWebNgramCollector(
                transport, pacer=RequestPacer(WEB_NGRAM_PACING, sleep=lambda _: None)
            ),
            use_profile=LEGACY_PROFILE,
        )
        assert transport.requests == []
        assert result.persisted.total == 0
        assert result.failures[0].code is AcquisitionErrorCode.AUTHORIZATION_REJECTED


# ================================================== implementation and planning


class TestTheCollectorIsRegistered:
    def test_gdelt_is_an_implemented_collector(self) -> None:
        """§40. Added only after the tests above pass — the LAST step of
        implementing a collector, never a way to prepare for one."""
        from sros_acquisition import IMPLEMENTED_COLLECTORS

        assert (
            frozenset({"world-bank", "gdelt", "ted-eu", "stack-exchange", "wikimedia-pageviews"})
            == IMPLEMENTED_COLLECTORS
        )

    def test_the_module_lives_in_the_collection_package(self) -> None:
        collection = REPO_ROOT / "services/acquisition/python/sros_acquisition/collection"
        assert (collection / "gdelt_web_ngram.py").exists()

    def test_gdelt_became_normalizable_two_missions_later(self) -> None:
        """Mission 1.9.3 §56 asserted the opposite, and the gap it recorded was
        the point: a collector says what was fetched, a normalizer says what it
        structurally represents, and one never implies the other.

        GDELT was collected in 1.9.3, the canonical model that could hold it was
        designed in 1.10, and the adapter arrived in 1.10.1 — three separate
        facts satisfied in three separate missions.

        TED took the same route over four: collected in 1.15.7, and normalizable
        in 1.15.8 once a canonical kind existed that could hold a notice.
        Stack Exchange took the same route inside ONE mission -- collected and
        normalizable in 1.18 -- which does not weaken the rule: the two facts
        were still established separately, and the collector shipped and ran
        before a record kind existed.
        """
        from sros_acquisition import IMPLEMENTED_NORMALIZERS

        assert (
            frozenset({"world-bank", "gdelt", "ted-eu", "stack-exchange", "wikimedia-pageviews"})
            == IMPLEMENTED_NORMALIZERS
        )

    def test_the_planner_now_sees_a_runnable_source(self, catalog) -> None:
        """§42. Derived from what exists, so nothing in the planner changed."""
        from sros_orchestrator.plan import acquisition_block

        pytest.importorskip("sros_orchestrator")
        from sros_acquisition import IMPLEMENTED_COLLECTORS

        assert "gdelt" in IMPLEMENTED_COLLECTORS
        assert callable(acquisition_block)

    def test_readiness_reports_gdelt_as_implemented(self, catalog, compliance) -> None:
        """§42's before/after, as one object."""
        from sros_acquisition.compliance import evaluate_readiness

        readiness = evaluate_readiness(catalog.get("gdelt"), LEGACY_PROFILE, compliance)
        assert readiness.eligible is True
        assert readiness.resource_ready is True
        assert readiness.implemented is True

    def test_world_bank_is_unaffected(self, catalog, compliance) -> None:
        from sros_acquisition.compliance import evaluate_readiness

        readiness = evaluate_readiness(catalog.get("world-bank"), LEGACY_PROFILE, compliance)
        assert readiness.eligible is True
        assert readiness.resource_ready is True
        assert readiness.implemented is True

    def test_the_normalizer_that_exists_serves_only_the_reviewed_route(self) -> None:
        """Mission 1.9.3 asserted that NO gdelt normalizer existed. One does now,
        for the WEB-NGRAM route. Nothing serves the DOC API, because H-27 is open
        and no timeline envelope has ever been observed."""
        normalization = REPO_ROOT / "services/acquisition/python/sros_acquisition/normalization"
        assert (normalization / "gdelt_web_ngram.py").exists()
        assert not (normalization / "gdelt.py").exists()
        assert not (normalization / "gdelt_doc_api.py").exists()
