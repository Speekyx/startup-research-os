"""The World Bank normalizer: mapping, quality, persistence and the job.

Mission 1.6 §54, §55 and the job half of §56.

**No test here reaches the internet or an LLM.** Normalization has no code path
that could; these tests exercise the mapping against fixture raw records and,
where a database is available, against rows written through the real collector.
"""

from __future__ import annotations

import contextlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import psycopg
import pytest
from sros_acquisition.normalization import (
    MAX_NORMALIZATION_BATCH,
    NormalizationJobPayload,
    canonical_decimal_text,
    count_normalized,
    persist_normalized,
    read_normalized_history,
    read_raw_records,
    run_normalization_job,
)
from sros_acquisition.normalization.errors import NormalizationFailedError
from sros_contracts import (
    NormalizationErrorCode,
    NormalizationQualityReason,
    NormalizedGeographyKind,
    NormalizedRecordQuality,
)

from .conftest import WORKSPACE_P, needs_postgres
from .normalization_fixtures import (
    NORMALIZED_AT,
    make_normalizer,
    raw_view,
)


def _normalize(**overrides):
    return make_normalizer().normalize(
        raw_view(**overrides), correlation_id="test-correlation", normalized_at=NORMALIZED_AT
    )


def _reasons(draft) -> set[NormalizationQualityReason]:
    return {reason.code for reason in draft.quality_reasons}


# --------------------------------------------------------------------- mapping


class TestValidObservation:
    """§54. The ordinary case: a population figure for a mapped country."""

    def test_a_population_record_normalizes_to_a_valid_numeric_observation(self) -> None:
        draft = _normalize()
        assert draft.quality is NormalizedRecordQuality.VALID
        assert draft.quality_reasons == ()
        assert draft.record_kind_id == "numeric_observation"

    def test_the_canonical_payload_carries_the_source_value_exactly(self) -> None:
        draft = _normalize(value=Decimal("67158348"))
        observation = draft.payload["observation"]
        assert observation["value"] == "67158348"
        assert observation["value_state"] == "REPORTED"

    def test_a_country_resolves_to_its_canonical_code_and_keeps_its_source_code(
        self,
    ) -> None:
        draft = _normalize(geography_code="DEU", geography_name="Germany")
        geography = draft.payload["geography"]
        assert geography["source_code"] == "DEU"
        assert geography["kind"] == "COUNTRY"
        assert geography["canonical_code"] == "DE"
        assert geography["canonical_scheme"] == "ISO-3166-1-ALPHA-2"

    def test_the_unit_is_recorded_as_unpublished_rather_than_inferred(self) -> None:
        """§17. `SP.POP.TOTL` obviously counts people; the endpoint does not say so."""
        draft = _normalize()
        observation = draft.payload["observation"]
        assert observation["unit"] is None
        assert observation["unit_state"] == "NOT_PUBLISHED"
        # And it is NOT a quality reason: a state every record shares carries no
        # information, and marking them all PARTIAL would waste the vocabulary.
        assert draft.quality is NormalizedRecordQuality.VALID

    def test_the_metric_name_is_null_because_the_endpoint_publishes_none(self) -> None:
        draft = _normalize()
        assert draft.payload["metric"]["name"] is None
        assert draft.payload["metric"]["id"] == "SP.POP.TOTL"


class TestMissingAndMalformedValues:
    """§14 and §26. Absence, failure to read, and zero are three things."""

    def test_a_value_the_source_did_not_report_is_partial_and_never_zero(self) -> None:
        draft = _normalize(value=None)
        assert draft.quality is NormalizedRecordQuality.PARTIAL
        assert _reasons(draft) == {NormalizationQualityReason.VALUE_NOT_REPORTED}
        observation = draft.payload["observation"]
        assert observation["value"] is None
        assert observation["value_state"] == "NOT_REPORTED"
        # The assertion that matters: nowhere in the canonical payload is there
        # a zero standing in for an absence.
        assert observation["value"] != "0"

    def test_a_reported_zero_stays_a_measurement_and_the_record_stays_valid(self) -> None:
        draft = _normalize(value=Decimal("0"))
        assert draft.quality is NormalizedRecordQuality.VALID
        observation = draft.payload["observation"]
        assert observation["value"] == "0"
        assert observation["value_state"] == "REPORTED"

    def test_an_unreadable_value_is_distinguished_from_an_absent_one(self) -> None:
        draft = _normalize(value="not a number")
        assert draft.quality is NormalizedRecordQuality.PARTIAL
        assert _reasons(draft) == {NormalizationQualityReason.MALFORMED_NUMERIC_VALUE}
        assert draft.payload["observation"]["value_state"] == "UNREADABLE"
        assert draft.payload["observation"]["value"] is None

    def test_the_two_missing_value_reasons_are_never_the_same_code(self) -> None:
        absent = _reasons(_normalize(value=None))
        unreadable = _reasons(_normalize(value="oops"))
        assert absent != unreadable


class TestGeography:
    """§15. An aggregate is not a country and an unknown is not promoted."""

    def test_an_unmapped_code_is_unknown_and_gains_no_country_code(self) -> None:
        draft = _normalize(geography_code="WLD", geography_name="World")
        assert draft.quality is NormalizedRecordQuality.PARTIAL
        assert _reasons(draft) == {NormalizationQualityReason.GEOGRAPHY_NOT_CLASSIFIED}
        geography = draft.payload["geography"]
        assert geography["source_code"] == "WLD"
        assert geography["kind"] == "UNKNOWN"
        assert geography["canonical_code"] is None

    def test_world_is_never_mapped_to_a_country(self) -> None:
        """§15, stated as the rule rather than as an implementation detail."""
        for code, name in (("WLD", "World"), ("HIC", "High income"), ("EUU", "Euro area")):
            draft = _normalize(geography_code=code, geography_name=name)
            assert draft.payload["geography"]["kind"] != "COUNTRY"
            assert draft.payload["geography"]["canonical_code"] is None

    def test_an_aggregate_in_the_map_is_preserved_as_an_aggregate(self) -> None:
        """The AGGREGATE kind is reachable, and a mapped aggregate stays one.

        Exercised against a FIXTURE map rather than the reviewed one, because
        the reviewed one deliberately seeds no aggregate: classifying a real
        World Bank aggregate needs evidence Mission 1.6 did not retrieve, and
        writing one down from recall is what the file exists to prevent.
        """
        from sros_acquisition.normalization import GeographyEntry, GeographyMap

        fixture = GeographyMap(
            canonical_scheme="ISO-3166-1-ALPHA-2",
            entries={
                "world-bank": {
                    "WLD": GeographyEntry(
                        source_code="WLD",
                        kind=NormalizedGeographyKind.AGGREGATE,
                        canonical_code=None,
                        name="World",
                        basis="fixture: an aggregate a reviewer had established",
                    )
                }
            },
        )
        draft = make_normalizer(geography=fixture).normalize(
            raw_view(geography_code="WLD", geography_name="World"),
            correlation_id="c",
            normalized_at=NORMALIZED_AT,
        )
        assert draft.payload["geography"]["kind"] == "AGGREGATE"
        assert draft.payload["geography"]["canonical_code"] is None
        # A classified aggregate is not a defect, so it is not a quality reason.
        assert draft.quality is NormalizedRecordQuality.VALID

    def test_a_record_with_no_geography_is_invalid(self) -> None:
        draft = _normalize(geography_code="")
        assert draft.quality is NormalizedRecordQuality.INVALID
        assert NormalizationQualityReason.GEOGRAPHY_MISSING in _reasons(draft)


class TestPeriod:
    """§16. Only what the real records use, and nothing approximated."""

    def test_an_unsupported_period_is_invalid_rather_than_approximated(self) -> None:
        for label in ("2020Q1", "2020M03", "2020-03-15", ""):
            draft = _normalize(period=label)
            assert draft.quality is NormalizedRecordQuality.INVALID, label
            assert NormalizationQualityReason.PERIOD_NOT_SUPPORTED in _reasons(draft)

    def test_a_yearly_period_keeps_its_label_beside_its_start(self) -> None:
        draft = _normalize(period="2020")
        period = draft.payload["period"]
        assert period == {
            "type": "YEAR",
            "label": "2020",
            "start": "2020-01-01T00:00:00+00:00",
            "end": "2021-01-01T00:00:00+00:00",
            "end_inclusive": False,
        }


class TestRefusals:
    """§54. What produces no record at all, and under which code."""

    def test_a_record_with_no_metric_is_invalid_not_refused(self) -> None:
        # INVALID rather than a refusal: §26 forbids discarding it, because a
        # raw record that could not be normalized is a fact someone must find.
        draft = _normalize(indicator="")
        assert draft.quality is NormalizedRecordQuality.INVALID
        assert NormalizationQualityReason.METRIC_MISSING in _reasons(draft)

    def test_an_empty_payload_is_refused_as_an_invalid_raw_record(self) -> None:
        with pytest.raises(NormalizationFailedError) as caught:
            make_normalizer().normalize(
                raw_view(payload={}), correlation_id="c", normalized_at=NORMALIZED_AT
            )
        assert caught.value.failure.code is NormalizationErrorCode.INVALID_RAW_RECORD

    def test_a_record_from_another_source_is_refused(self) -> None:
        with pytest.raises(NormalizationFailedError) as caught:
            make_normalizer().normalize(
                raw_view(source_id="eurostat"),
                correlation_id="c",
                normalized_at=NORMALIZED_AT,
            )
        assert caught.value.failure.code is NormalizationErrorCode.UNSUPPORTED_SOURCE

    def test_a_failure_carries_no_payload_and_no_library_text(self) -> None:
        """§33's rule, applied at this layer: a failure is safe to log."""
        with pytest.raises(NormalizationFailedError) as caught:
            make_normalizer().normalize(
                raw_view(payload={}), correlation_id="c", normalized_at=NORMALIZED_AT
            )
        serialized = json.dumps(caught.value.failure.to_json())
        assert "Traceback" not in serialized
        assert "SP.POP.TOTL" not in serialized

    def test_only_persistence_failure_is_retryable(self) -> None:
        from sros_acquisition.normalization import is_retryable

        assert is_retryable(NormalizationErrorCode.PERSISTENCE_FAILURE)
        for code in (
            NormalizationErrorCode.UNSUPPORTED_SOURCE,
            NormalizationErrorCode.UNSUPPORTED_COLLECTOR_VERSION,
            NormalizationErrorCode.INVALID_RAW_RECORD,
            NormalizationErrorCode.NON_DETERMINISTIC_OUTPUT,
        ):
            assert not is_retryable(code)


class TestJobPayload:
    """§33 and §34. Context is required and the batch is bounded."""

    def test_a_payload_without_a_workspace_is_refused(self) -> None:
        with pytest.raises(ValueError, match="workspace_id"):
            NormalizationJobPayload.from_payload(
                {"research_session_id": "s", "correlation_id": "c"}
            )

    def test_a_payload_without_a_session_is_refused(self) -> None:
        with pytest.raises(ValueError, match="research_session_id"):
            NormalizationJobPayload.from_payload(
                {"workspace_id": WORKSPACE_P, "correlation_id": "c"}
            )

    def test_a_larger_batch_than_the_ceiling_is_capped(self) -> None:
        job = NormalizationJobPayload.from_payload(
            {
                "workspace_id": WORKSPACE_P,
                "research_session_id": "s",
                "correlation_id": "c",
                "max_records": 10_000,
            }
        )
        assert job.max_records == MAX_NORMALIZATION_BATCH

    def test_a_smaller_batch_is_honoured(self) -> None:
        job = NormalizationJobPayload.from_payload(
            {
                "workspace_id": WORKSPACE_P,
                "research_session_id": "s",
                "correlation_id": "c",
                "max_records": 5,
            }
        )
        assert job.max_records == 5

    def test_the_idempotency_key_excludes_the_clock(self) -> None:
        payload = {
            "workspace_id": WORKSPACE_P,
            "research_session_id": "s",
            "correlation_id": "first-delivery",
        }
        first = NormalizationJobPayload.from_payload(payload).idempotency_key
        second = NormalizationJobPayload.from_payload(
            {**payload, "correlation_id": "second-delivery"}
        ).idempotency_key
        # Two deliveries of the same logical job. Different correlation ids,
        # same key -- otherwise every redelivery would look like new work.
        assert first == second


# ----------------------------------------------------------------- persistence


def _persist_at(*records) -> datetime:
    """A normalization time that is never before collection.

    `seeded_raw` runs the REAL collector, so its records carry a real-clock
    `collected_at`, while `NORMALIZED_AT` is a fixed instant. The database's
    `CHECK (normalized_at >= collected_at)` is right and the constant was a
    snapshot: it held until the wall clock passed 2026-08-31 09:00 UTC and then
    failed for good (`testing-strategy.md` §42).

    The offline tests keep the constant. They pair it with the fixed
    `COLLECTED_AT` and are deterministic, which is worth more there than
    clock-independence is here.
    """
    return max([NORMALIZED_AT, datetime.now(UTC), *(r.collected_at for r in records)])


@needs_postgres
class TestPersistence:
    """§55. Against a real database, with real row-level security."""

    def test_a_draft_persists_with_complete_lineage(self, tenant_conn, seeded_raw) -> None:
        draft = make_normalizer().normalize(
            seeded_raw[0], correlation_id="c", normalized_at=_persist_at(seeded_raw[0])
        )
        with tenant_conn(WORKSPACE_P) as conn:
            report = persist_normalized(conn, [draft])
            assert report.new == 1
            row = conn.execute(
                """SELECT raw_record_id, source_id, observation_key, record_kind_id,
                          normalizer_id, normalizer_version, normalization_schema_id,
                          normalization_schema_version, collector_id, collector_version,
                          review_version, correlation_id, quality, extraction_method,
                          observed_at, collected_at, normalized_at, expires_at,
                          provenance, payload, content_hash
                     FROM acquisition.normalized_records WHERE id = %s""",
                (draft.record_id,),
            ).fetchone()
        assert row is not None
        assert str(row[0]) == draft.raw_record_id
        assert row[1] == "world-bank"
        assert row[2] == draft.observation_key
        assert row[3] == "numeric_observation"
        assert row[4:8] == (
            draft.normalizer_id,
            draft.normalizer_version,
            draft.normalization_schema_id,
            draft.normalization_schema_version,
        )
        assert row[8] == "world-bank-indicators"
        assert row[12] == "VALID"
        assert row[13] == "DETERMINISTIC_ADAPTER"
        assert row[18]["attribution"]["text"]
        assert row[19]["record_kind"] == "numeric_observation"
        assert len(row[20]) == 64

    def test_running_twice_writes_nothing_the_second_time(self, tenant_conn, seeded_raw) -> None:
        """§23 and §35. The property that makes duplicate delivery safe."""
        normalizer = make_normalizer()
        at = _persist_at(*seeded_raw)
        drafts = [normalizer.normalize(r, correlation_id="c", normalized_at=at) for r in seeded_raw]
        with tenant_conn(WORKSPACE_P) as conn:
            first = persist_normalized(conn, drafts)
            # A LATER clock on the second pass, because a redelivery does not
            # happen at the same instant -- and the time must not matter.
            again = [
                normalizer.normalize(
                    r, correlation_id="redelivery", normalized_at=at + timedelta(hours=3)
                )
                for r in seeded_raw
            ]
            second = persist_normalized(conn, again)
            total = count_normalized(conn, WORKSPACE_P)

        assert first.new == len(seeded_raw)
        assert second.unchanged == len(seeded_raw)
        assert second.new == 0
        assert total == len(seeded_raw)

    def test_a_revised_raw_record_supersedes_without_overwriting(
        self, tenant_conn, seeded_raw
    ) -> None:
        """§48. Both versions survive and the latest is identifiable.

        Expected values are DERIVED from the raw payloads, never written down.
        §39 forbids hard-coding population figures, and the same discipline
        belongs here: a literal would make the test assert what somebody typed
        rather than that the value survived the transformation.
        """
        original = seeded_raw[0]
        original_value = canonical_decimal_text(Decimal(str(original.payload["value"])))
        normalizer = make_normalizer()
        first = normalizer.normalize(
            original, correlation_id="c", normalized_at=_persist_at(original)
        )

        revised_value = Decimal(str(original.payload["value"])) + Decimal("1000")
        revised_raw = _revise(original, revised_value)
        # The revision was collected a day later, so its normalization must be
        # later still -- `_revise` moves `collected_at` forward by design.
        second = normalizer.normalize(
            revised_raw, correlation_id="c", normalized_at=_persist_at(revised_raw)
        )

        with tenant_conn(WORKSPACE_P) as conn:
            _insert_raw(conn, revised_raw)
            persist_normalized(conn, [first])
            report = persist_normalized(conn, [second])
            history = read_normalized_history(conn, WORKSPACE_P, original.observation_key)

        assert report.revised == 1
        assert len(history) == 2
        current = [h for h in history if h["current"]]
        superseded = [h for h in history if not h["current"]]
        assert len(current) == 1 and len(superseded) == 1
        # v1 was not mutated into v2. Its value is still what the source said.
        assert superseded[0]["payload"]["observation"]["value"] == original_value
        assert current[0]["payload"]["observation"]["value"] == canonical_decimal_text(
            revised_value
        )
        assert original_value != canonical_decimal_text(revised_value)

    def test_two_normalizer_versions_coexist(self, tenant_conn, seeded_raw) -> None:
        """§49. Representation A survives when B is written."""
        record = seeded_raw[0]
        at = _persist_at(record)
        first = make_normalizer().normalize(record, correlation_id="c", normalized_at=at)
        newer = make_normalizer()
        newer.normalizer_version = "1.1.0"  # type: ignore[misc]
        second = newer.normalize(record, correlation_id="c", normalized_at=at + timedelta(hours=1))

        with tenant_conn(WORKSPACE_P) as conn:
            persist_normalized(conn, [first])
            report = persist_normalized(conn, [second])
            history = read_normalized_history(conn, WORKSPACE_P, record.observation_key)

        assert report.new == 1
        assert len(history) == 2
        assert {h["normalizer"] for h in history} == {
            "world-bank-indicators-numeric@1.0.0",
            "world-bank-indicators-numeric@1.1.0",
        }
        # NEITHER is superseded. Supersession tracks an upstream revision, not a
        # normalizer upgrade -- deciding which version to read is D-08.
        assert all(h["current"] for h in history)

    def test_different_content_under_one_identity_conflicts_rather_than_overwrites(
        self, tenant_conn, seeded_raw
    ) -> None:
        """The mechanism that makes a version bump necessary rather than polite."""
        record = seeded_raw[0]
        at = _persist_at(record)
        stored = make_normalizer().normalize(record, correlation_id="c", normalized_at=at)
        # A normalizer whose CONFIGURATION changed without its version changing:
        # the same identity, different canonical content.
        from sros_acquisition.normalization import GeographyMap

        blind = make_normalizer(
            geography=GeographyMap(canonical_scheme="ISO-3166-1-ALPHA-2", entries={})
        )
        divergent = blind.normalize(record, correlation_id="c", normalized_at=at)
        assert divergent.record_id == stored.record_id
        assert divergent.content_hash != stored.content_hash

        with tenant_conn(WORKSPACE_P) as conn:
            persist_normalized(conn, [stored])
            report = persist_normalized(conn, [divergent])
            row = conn.execute(
                "SELECT content_hash, quality FROM acquisition.normalized_records WHERE id = %s",
                (stored.record_id,),
            ).fetchone()

        assert report.conflicted == 1
        assert report.new == 0
        # The stored representation stands. Overwriting would destroy it.
        assert row[0] == stored.content_hash
        assert row[1] == "VALID"

    def test_a_rollback_leaves_no_partial_normalization(self, seeded_raw) -> None:
        """§29. Either the batch and its lineage, or nothing."""
        from .conftest import DATABASE_URL

        at = _persist_at(*seeded_raw)
        drafts = [
            make_normalizer().normalize(r, correlation_id="c", normalized_at=at) for r in seeded_raw
        ]
        connection = psycopg.connect(DATABASE_URL)
        try:
            with contextlib.suppress(RuntimeError), connection.transaction():
                connection.execute("SET LOCAL ROLE sros_app")
                connection.execute(
                    "SELECT set_config('app.workspace_id', %s, true)", (WORKSPACE_P,)
                )
                persist_normalized(connection, drafts)
                raise RuntimeError("simulated failure after the write")
            with connection.transaction():
                connection.execute("SET LOCAL ROLE sros_app")
                connection.execute(
                    "SELECT set_config('app.workspace_id', %s, true)", (WORKSPACE_P,)
                )
                assert count_normalized(connection, WORKSPACE_P) == 0
        finally:
            connection.close()

    def test_a_workspace_cannot_read_another_workspaces_normalized_records(
        self, tenant_conn, seeded_raw, second_workspace
    ) -> None:
        """§30. Two workspaces, because one cannot detect a missing filter."""
        draft = make_normalizer().normalize(
            seeded_raw[0], correlation_id="c", normalized_at=_persist_at(seeded_raw[0])
        )
        with tenant_conn(WORKSPACE_P) as conn:
            persist_normalized(conn, [draft])
            assert count_normalized(conn, WORKSPACE_P) == 1
            # Layer one: the explicit filter returns nothing for the other tenant.
            assert count_normalized(conn, second_workspace) == 0

        with tenant_conn(second_workspace) as conn:
            # Layer two: RLS. Even asking for the OTHER workspace's id by name
            # returns nothing, because the policy resolves to this tenant.
            assert count_normalized(conn, WORKSPACE_P) == 0
            rows = conn.execute("SELECT count(*) FROM acquisition.normalized_records").fetchone()
            assert rows[0] == 0

    def test_a_cross_tenant_reference_cannot_be_written(
        self, tenant_conn, seeded_raw, second_workspace
    ) -> None:
        """§31. Layer three: the composite FK makes it impossible, not merely wrong."""
        draft = make_normalizer().normalize(
            seeded_raw[0], correlation_id="c", normalized_at=_persist_at(seeded_raw[0])
        )
        # The same raw record, claimed by the other workspace.
        alien = _with_workspace(draft, second_workspace)
        with tenant_conn(second_workspace) as conn, pytest.raises(psycopg.errors.Error):
            persist_normalized(conn, [alien])

    def test_only_records_of_this_workspace_are_read(
        self, tenant_conn, seeded_raw, second_workspace
    ) -> None:
        with tenant_conn(second_workspace) as conn:
            assert read_raw_records(conn, second_workspace) == []


# ------------------------------------------------------------------------ job


@needs_postgres
class TestJob:
    """§32–§35. The whole pass, in one tenant transaction."""

    def test_a_job_normalizes_the_sessions_raw_records(
        self, committing_tenant_conn, seeded_raw, dev_session
    ) -> None:
        result = run_normalization_job(
            {
                "workspace_id": WORKSPACE_P,
                "research_session_id": dev_session,
                "correlation_id": "job-1",
            },
            committing_tenant_conn,
        )
        assert result.succeeded
        assert result.counts.records_input == len(seeded_raw)
        assert result.counts.records_normalized == len(seeded_raw)
        assert result.persisted.new == len(seeded_raw)
        assert result.source_ids == ("world-bank",)
        assert result.normalizers == ("world-bank-indicators-numeric@1.0.0",)

    def test_a_duplicate_delivery_creates_nothing(
        self, committing_tenant_conn, seeded_raw, dev_session
    ) -> None:
        """§35. At-least-once, and this does not claim exactly-once."""
        payload = {
            "workspace_id": WORKSPACE_P,
            "research_session_id": dev_session,
            "correlation_id": "job-1",
        }
        first = run_normalization_job(payload, committing_tenant_conn)
        # The redelivery: same logical job, a different correlation id, and it
        # must find nothing left to do.
        second = run_normalization_job(
            {**payload, "correlation_id": "job-1-retry"}, committing_tenant_conn
        )

        assert first.persisted.new == len(seeded_raw)
        assert second.counts.records_input == 0
        assert second.persisted.new == 0
        assert first.idempotency_key == second.idempotency_key

    def test_renormalizing_the_same_lineage_writes_nothing(
        self, committing_tenant_conn, seeded_raw, dev_session
    ) -> None:
        payload = {
            "workspace_id": WORKSPACE_P,
            "research_session_id": dev_session,
            "correlation_id": "job-1",
        }
        run_normalization_job(payload, committing_tenant_conn)
        again = run_normalization_job(
            {**payload, "only_unnormalized": False, "correlation_id": "job-2"},
            committing_tenant_conn,
        )
        assert again.counts.records_input == len(seeded_raw)
        assert again.persisted.unchanged == len(seeded_raw)
        assert again.persisted.new == 0

    def test_the_correlation_id_reaches_every_record(
        self, committing_tenant_conn, seeded_raw, dev_session
    ) -> None:
        run_normalization_job(
            {
                "workspace_id": WORKSPACE_P,
                "research_session_id": dev_session,
                "correlation_id": "corr-propagated",
            },
            committing_tenant_conn,
        )
        with committing_tenant_conn(WORKSPACE_P) as conn:
            rows = conn.execute(
                "SELECT DISTINCT correlation_id FROM acquisition.normalized_records "
                "WHERE workspace_id = %s",
                (WORKSPACE_P,),
            ).fetchall()
        assert [r[0] for r in rows] == ["corr-propagated"]

    def test_a_cancelled_job_stops_before_the_next_record(
        self, tenant_conn, seeded_raw, dev_session
    ) -> None:
        result = run_normalization_job(
            {
                "workspace_id": WORKSPACE_P,
                "research_session_id": dev_session,
                "correlation_id": "job-cancel",
            },
            tenant_conn,
            cancelled=lambda: True,
        )
        assert result.counts.records_normalized == 0
        assert result.persisted.total == 0
        assert result.failures[0].code is NormalizationErrorCode.CANCELLED

    def test_a_record_from_an_unnormalizable_source_is_refused_not_guessed(
        self, tenant_conn, dev_session
    ) -> None:
        """§20 and §56. Another source cannot use the World Bank normalizer."""
        result = run_normalization_job(
            {
                "workspace_id": WORKSPACE_P,
                "research_session_id": dev_session,
                "correlation_id": "job-alien",
            },
            tenant_conn,
            registry={},
        )
        assert result.counts.records_normalized == 0
        assert all(f.code is NormalizationErrorCode.UNSUPPORTED_SOURCE for f in result.failures)

    def test_the_batch_bound_is_applied(
        self, committing_tenant_conn, seeded_raw, dev_session
    ) -> None:
        result = run_normalization_job(
            {
                "workspace_id": WORKSPACE_P,
                "research_session_id": dev_session,
                "correlation_id": "job-bounded",
                "max_records": 2,
            },
            committing_tenant_conn,
        )
        assert result.counts.records_input == 2
        assert result.persisted.new == 2

    def test_no_claim_evidence_or_signal_is_created(
        self, committing_tenant_conn, seeded_raw, dev_session
    ) -> None:
        """§43, §44, §45, verified against the database rather than asserted."""
        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as probe:
            before = _science_counts(probe)
        run_normalization_job(
            {
                "workspace_id": WORKSPACE_P,
                "research_session_id": dev_session,
                "correlation_id": "job-science",
            },
            committing_tenant_conn,
        )
        with psycopg.connect(DATABASE_URL) as probe:
            after = _science_counts(probe)
        assert before == after


def _science_counts(conn) -> dict[str, int]:
    # The table names are literals in the tuple below, not input.
    return {
        table: int(conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0])  # noqa: S608
        for table in (
            "nlp.signals",
            "nlp.embedding_provenance",
            "research.claims",
            "scoring.evidence",
        )
    }


# -------------------------------------------------------------------- helpers


def _revise(record, value):
    from dataclasses import replace

    payload = {**record.payload, "value": value}
    return replace(
        record,
        record_id=str(uuid.uuid4()),
        payload=payload,
        content_hash="1" * 64,
        collected_at=record.collected_at + timedelta(days=1),
    )


def _with_workspace(draft, workspace_id: str):
    from dataclasses import replace

    return replace(draft, workspace_id=workspace_id, record_id=uuid.uuid4())


def _insert_raw(conn, record) -> None:
    """Write a `RawRecordView` back as a row, for the revision fixture.

    Deliberately narrow: it exists so a revision can be constructed in the
    database, and it is never used to bypass the collector for a record a test
    then treats as real.
    """
    conn.execute(
        """INSERT INTO acquisition.raw_records
               (id, workspace_id, research_session_id, source_id, source_reference,
                acquisition_method, content_hash, payload_ref, observation_key,
                last_seen_at, observed_at, provenance, review_version, correlation_id,
                collector_id, collector_version, payload, collected_at, expires_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,'inline',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            record.record_id,
            record.workspace_id,
            record.research_session_id,
            record.source_id,
            record.observation_key,
            record.acquisition_method,
            record.content_hash,
            record.observation_key,
            record.collected_at,
            record.observed_at,
            json.dumps(record.provenance, sort_keys=True),
            record.review_version,
            record.correlation_id,
            record.collector_id,
            record.collector_version,
            json.dumps(record.payload, sort_keys=True, default=str),
            record.collected_at,
            record.expires_at,
        ),
    )
