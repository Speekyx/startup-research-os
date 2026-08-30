"""Persistence, idempotency, live constraints and tenant isolation.

Mission 1.11.1 §30-§33, §41, §42. Needs PostgreSQL; every write goes into a
**disposable** workspace this suite creates and destroys, never into the seeded
one holding the eight real records.

Refusal assertions name the **exact constraint** that refused, never "it
failed": Mission 1.11 found a probe where ten cases passed because a `NOT NULL`
fired before any CHECK could.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from .conftest import OTHER_SESSION, PROBE_SESSION, needs_postgres

psycopg = pytest.importorskip("psycopg")

pytestmark = needs_postgres


def _seed_numeric(conn, workspace_id: str, year: str, value: str, geography: str = "DEU"):
    """One raw and one normalized World Bank record, SYNTHETIC.

    Shaped after the real six so the extractor sees the shape it must support.
    Every id and hash is invented and no byte came from a source.
    """
    raw_id, normalized_id = str(uuid.uuid4()), str(uuid.uuid4())
    key = f"world-bank|indicator/SP.POP.TOTL|{geography}|{year}"
    now = datetime.now(UTC)
    conn.execute(
        """INSERT INTO acquisition.raw_records (
               id, workspace_id, source_id, source_reference, acquisition_method,
               content_hash, observation_key, payload_ref, provenance, collector_id,
               collector_version, review_version, correlation_id, last_seen_at,
               collected_at, expires_at)
           VALUES (%s,%s,'world-bank','indicator/SP.POP.TOTL','PUBLIC_API',%s,%s,%s,%s,
                   'world-bank-indicators','1.0.0',1,'test',%s,%s,%s)""",
        (
            raw_id,
            workspace_id,
            f"hash-{normalized_id}",
            key,
            json.dumps({"value": value}),
            json.dumps({"source_id": "world-bank"}),
            now,
            now,
            now + timedelta(days=30),
        ),
    )
    conn.execute(
        """INSERT INTO acquisition.normalized_records (
               id, workspace_id, raw_record_id, source_id, extraction_method,
               normalizer_version, content_hash, payload, record_kind_id,
               normalizer_id, normalization_schema_id, normalization_schema_version,
               observation_key, normalized_at, correlation_id, collector_id,
               collector_version, review_version, provenance, quality,
               quality_reasons, collected_at, expires_at)
           VALUES (%s,%s,%s,'world-bank','deterministic','1.0.0',%s,%s,
                   'numeric_observation','world-bank-indicators-numeric',
                   'sros.normalized-record',1,%s,%s,'test','world-bank-indicators',
                   '1.0.0',1,%s,'VALID','[]',%s,%s)""",
        (
            normalized_id,
            workspace_id,
            raw_id,
            f"content-{normalized_id}",
            json.dumps(
                {
                    "record_kind": "numeric_observation",
                    "metric": {
                        "id": "SP.POP.TOTL",
                        "name": None,
                        "scheme": "world-bank-indicator",
                    },
                    "geography": {
                        "kind": "COUNTRY",
                        "source_code": geography,
                        "source_name": geography,
                        "canonical_scheme": "ISO-3166-1-ALPHA-2",
                        "canonical_code": geography[:2],
                    },
                    "series": {
                        "dataset": "indicators",
                        "frequency": "ANNUAL",
                        "resource_id": "indicator/SP.POP.TOTL",
                        "source_last_updated": "2026-07-13",
                    },
                    "period": {
                        "type": "YEAR",
                        "label": year,
                        "start": f"{year}-01-01T00:00:00+00:00",
                        "end": f"{int(year) + 1}-01-01T00:00:00+00:00",
                        "end_inclusive": False,
                    },
                    "observation": {
                        "value": value,
                        "value_state": "REPORTED",
                        "unit": None,
                        "unit_state": "NOT_PUBLISHED",
                        "decimals": 0,
                    },
                }
            ),
            key,
            now,
            json.dumps({"source_id": "world-bank"}),
            now,
            now + timedelta(days=365),
        ),
    )
    return normalized_id


def _payload(workspace_id: str, **overrides):
    payload = {
        "workspace_id": workspace_id,
        "research_session_id": PROBE_SESSION,
        "correlation_id": "derivation-test",
        "extractor_id": "numeric-period-change",
        "parameters": {},
    }
    payload.update(overrides)
    return payload


class TestPersistence:
    def test_a_signal_is_written_with_its_lineage_and_its_run(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        from sros_nlp import run_signal_derivation_job

        with committing_tenant_conn(probe_workspace) as conn:
            _seed_numeric(conn, probe_workspace, "2018", "100")
            _seed_numeric(conn, probe_workspace, "2019", "150")

        result = run_signal_derivation_job(_payload(probe_workspace), committing_tenant_conn)
        assert result.persisted.new == 1

        with committing_tenant_conn(probe_workspace) as conn:
            signal = conn.execute(
                "SELECT id, magnitude, direction, temporal_basis, derivation_confidence, "
                "quantity_family, signal_type_id, extractor_id, extractor_version, "
                "observed_at FROM nlp.signals WHERE workspace_id = %s",
                (probe_workspace,),
            ).fetchall()
            assert len(signal) == 1
            row = signal[0]
            assert row[1] == Decimal("50")
            assert row[2] == "INCREASING"
            assert row[3] == "COMPARABLE_INSTANTS"
            assert row[4] == 1.0
            assert row[5] == "MEASURED_SERIES"
            assert row[6] == "numeric_period_change"
            assert row[7] == "numeric-period-change"
            assert row[8] == "1.0.0"
            assert row[9] is not None

            inputs = conn.execute(
                "SELECT role, input_position, observation_key FROM nlp.signal_inputs "
                "WHERE workspace_id = %s ORDER BY input_position",
                (probe_workspace,),
            ).fetchall()
            assert [r[0] for r in inputs] == ["CONTRIBUTED", "CONTRIBUTED"]
            assert inputs[0][2].endswith("|2018")
            assert inputs[1][2].endswith("|2019")

            runs = conn.execute(
                "SELECT groups_considered, groups_derived, groups_refused, signals_new "
                "FROM nlp.signal_derivation_runs WHERE workspace_id = %s",
                (probe_workspace,),
            ).fetchall()
            assert runs == [(1, 1, 0, 1)]

    def test_a_refused_group_is_recorded_without_a_signal(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§4. The whole point of the run log: a derivation that produced
        nothing leaves a durable trace, and NOT a row in nlp.signals."""
        from sros_nlp import run_signal_derivation_job

        with committing_tenant_conn(probe_workspace) as conn:
            _seed_numeric(conn, probe_workspace, "2018", "100")

        result = run_signal_derivation_job(_payload(probe_workspace), committing_tenant_conn)
        assert result.persisted.new == 0
        assert result.run.groups_refused == 1

        with committing_tenant_conn(probe_workspace) as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM nlp.signals WHERE workspace_id = %s",
                    (probe_workspace,),
                ).fetchone()[0]
                == 0
            )
            refusals = conn.execute(
                "SELECT refusals FROM nlp.signal_derivation_runs WHERE workspace_id = %s",
                (probe_workspace,),
            ).fetchone()[0]
            assert refusals[0]["reason"] == "INSUFFICIENT_INPUT_OBSERVATIONS"
            assert "two periods" in refusals[0]["detail"]

    def test_repeating_the_derivation_creates_no_duplicate(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """§31, §41. Idempotent PERSISTENCE, not exactly-once delivery."""
        from sros_nlp import run_signal_derivation_job

        with committing_tenant_conn(probe_workspace) as conn:
            _seed_numeric(conn, probe_workspace, "2018", "100")
            _seed_numeric(conn, probe_workspace, "2019", "150")

        first = run_signal_derivation_job(_payload(probe_workspace), committing_tenant_conn)
        second = run_signal_derivation_job(_payload(probe_workspace), committing_tenant_conn)

        assert first.persisted.new == 1
        assert second.persisted.new == 0
        assert second.persisted.unchanged == 1

        with committing_tenant_conn(probe_workspace) as conn:
            counts = conn.execute(
                "SELECT (SELECT count(*) FROM nlp.signals WHERE workspace_id = %s), "
                "(SELECT count(*) FROM nlp.signal_inputs WHERE workspace_id = %s), "
                "(SELECT count(*) FROM nlp.signal_derivation_runs WHERE workspace_id = %s)",
                (probe_workspace, probe_workspace, probe_workspace),
            ).fetchone()
        # One signal, two lineage rows -- and TWO runs, because two executions
        # happened and the run log records executions rather than logical jobs.
        assert counts == (1, 2, 2)

    def test_adjacent_pairing_over_three_periods(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        from sros_nlp import run_signal_derivation_job

        with committing_tenant_conn(probe_workspace) as conn:
            _seed_numeric(conn, probe_workspace, "2018", "100")
            _seed_numeric(conn, probe_workspace, "2019", "150")
            _seed_numeric(conn, probe_workspace, "2020", "150")

        result = run_signal_derivation_job(_payload(probe_workspace), committing_tenant_conn)
        assert result.persisted.new == 2

        with committing_tenant_conn(probe_workspace) as conn:
            directions = conn.execute(
                "SELECT direction, magnitude FROM nlp.signals WHERE workspace_id = %s "
                "ORDER BY magnitude DESC",
                (probe_workspace,),
            ).fetchall()
        assert directions == [("INCREASING", Decimal("50")), ("UNCHANGED", Decimal("0"))]

    def test_two_geographies_are_two_series(self, committing_tenant_conn, probe_workspace) -> None:
        from sros_nlp import run_signal_derivation_job

        with committing_tenant_conn(probe_workspace) as conn:
            for geography in ("DEU", "FRA"):
                _seed_numeric(conn, probe_workspace, "2018", "100", geography)
                _seed_numeric(conn, probe_workspace, "2019", "150", geography)

        result = run_signal_derivation_job(_payload(probe_workspace), committing_tenant_conn)
        assert result.run.groups_considered == 2
        assert result.persisted.new == 2


class TestLiveConstraints:
    """§33. Each refusal names the constraint that refused it."""

    @staticmethod
    def _insert(conn, workspace_id: str, **overrides):
        row = {
            "quantity_family": "MEASURED_SERIES",
            "signal_type_registry": "signal_type",
            "signal_type_id": "numeric_period_change",
            "magnitude": "5",
            "magnitude_kind": "ABSOLUTE_CHANGE",
            "magnitude_unit": None,
            "magnitude_unit_state": "NOT_ESTABLISHED",
            "direction": "NOT_APPLICABLE",
            "derivation_confidence": 1.0,
            "extractor_id": "probe",
            "extractor_version": "1.0.0",
            "signal_schema_id": "sros.signal",
            "signal_schema_version": 1,
            "derivation_kind": "DETERMINISTIC",
            "model_version": None,
            "prompt_version": None,
            "extraction_method": "probe",
            "correlation_id": "probe",
            "parameters": "{}",
            "parameter_fingerprint": "p" * 64,
            "derivation_fingerprint": str(uuid.uuid4()),
            "scope": json.dumps({"source_ids": ["world-bank"]}),
            "temporal_basis": "SAME_PERIOD_LABEL",
            "temporal_window": json.dumps(
                {
                    "basis": "SAME_PERIOD_LABEL",
                    "period_labels": ["2018", "2018"],
                    "resolution": "YEAR",
                    "observation_count": 2,
                }
            ),
            "observed_at": None,
        }
        row.update(overrides)
        columns = ", ".join(row)
        placeholders = ", ".join(f"%({name})s" for name in row)
        conn.execute(
            f"INSERT INTO nlp.signals (id, workspace_id, derived_at, expires_at, {columns}) "  # noqa: S608
            f"SELECT gen_random_uuid(), %(workspace)s, now(), "
            f"now() + interval '365 days', {placeholders}",
            dict(row, workspace=workspace_id),
        )

    @pytest.mark.parametrize(
        ("overrides", "constraint"),
        [
            ({}, None),
            (
                {"observed_at": datetime(2018, 1, 1, tzinfo=UTC)},
                "signals_observed_at_requires_comparable_instants_check",
            ),
            ({"direction": "INCREASING"}, "signals_direction_requires_order_check"),
            ({"model_version": "m"}, "signals_derivation_kind_provenance_check"),
            (
                {"derivation_kind": "MODEL_DERIVED"},
                "signals_derivation_kind_provenance_check",
            ),
            ({"derivation_confidence": 1.5}, "signals_derivation_confidence_unit_interval_check"),
            ({"quantity_family": "PAIN"}, "signals_quantity_family_check"),
            (
                {
                    "magnitude_kind": "RATIO",
                    "magnitude_unit_state": "INHERITED",
                    "magnitude_unit": "mentions",
                },
                "signals_dimensionless_kind_check",
            ),
            (
                {"magnitude_kind": "ABSOLUTE_DIFFERENCE"},
                None,
            ),
            ({"temporal_basis": "ORDERED_PERIODS"}, "signals_temporal_basis_matches_window_check"),
            ({"signal_type_id": "trend"}, "signals_signal_type_registry_signal_type_id_fkey"),
        ],
    )
    def test_the_named_constraint_refuses(
        self, tenant_conn, probe_workspace, overrides, constraint
    ) -> None:
        with tenant_conn(probe_workspace) as conn:
            if constraint is None:
                self._insert(conn, probe_workspace, **overrides)
                return
            with pytest.raises(psycopg.Error) as caught:
                self._insert(conn, probe_workspace, **overrides)
            assert caught.value.diag.constraint_name == constraint

    def test_a_duplicate_derivation_fingerprint_is_refused(
        self, tenant_conn, probe_workspace
    ) -> None:
        fingerprint = "f" * 64
        with tenant_conn(probe_workspace) as conn:
            self._insert(conn, probe_workspace, derivation_fingerprint=fingerprint)
            with pytest.raises(psycopg.Error) as caught:
                self._insert(conn, probe_workspace, derivation_fingerprint=fingerprint)
            assert caught.value.diag.constraint_name == "signals_derivation_unique"

    def test_a_refused_group_count_needs_its_reasons(self, tenant_conn, probe_workspace) -> None:
        """A count with no reasons behind it is the "something did not happen"
        the run log exists to replace."""
        now = datetime.now(UTC)
        with tenant_conn(probe_workspace) as conn, pytest.raises(psycopg.Error) as caught:
            conn.execute(
                """INSERT INTO nlp.signal_derivation_runs (
                       id, workspace_id, extractor_id, extractor_version,
                       signal_type_id, parameter_fingerprint, groups_considered,
                       groups_refused, correlation_id, started_at, finished_at,
                       expires_at)
                   VALUES (gen_random_uuid(), %s, 'probe', '1.0.0',
                           'numeric_period_change', 'p', 1, 1, 'probe', %s, %s, %s)""",
                (probe_workspace, now, now, now + timedelta(days=90)),
            )
        assert (
            caught.value.diag.constraint_name == "signal_derivation_runs_refusals_explained_check"
        )


class TestTenantIsolation:
    """§42. Proved through a connection the policies actually bind."""

    def test_a_workspace_cannot_read_another_workspaces_signals(
        self, committing_tenant_conn, probe_workspace, other_workspace
    ) -> None:
        from sros_nlp import count_signals, run_signal_derivation_job

        with committing_tenant_conn(probe_workspace) as conn:
            _seed_numeric(conn, probe_workspace, "2018", "100")
            _seed_numeric(conn, probe_workspace, "2019", "150")
        run_signal_derivation_job(_payload(probe_workspace), committing_tenant_conn)

        with committing_tenant_conn(probe_workspace) as conn:
            assert count_signals(conn, probe_workspace) == 1
        with committing_tenant_conn(other_workspace) as conn:
            # Unscoped on purpose: the explicit filter is layer one and this
            # asserts layer two. A query with a WHERE clause would prove nothing
            # about the policy.
            assert conn.execute("SELECT count(*) FROM nlp.signals").fetchone()[0] == 0
            assert conn.execute("SELECT count(*) FROM nlp.signal_inputs").fetchone()[0] == 0
            assert (
                conn.execute("SELECT count(*) FROM nlp.signal_derivation_runs").fetchone()[0] == 0
            )

    def test_a_signal_input_cannot_cross_a_tenant_boundary(
        self, committing_tenant_conn, privileged_conn, probe_workspace, other_workspace
    ) -> None:
        from sros_nlp import run_signal_derivation_job

        with committing_tenant_conn(probe_workspace) as conn:
            _seed_numeric(conn, probe_workspace, "2018", "100")
            _seed_numeric(conn, probe_workspace, "2019", "150")
        run_signal_derivation_job(_payload(probe_workspace), committing_tenant_conn)

        foreign_record = privileged_conn.execute(
            "SELECT id, raw_record_id FROM acquisition.normalized_records "
            "WHERE workspace_id = %s LIMIT 1",
            (probe_workspace,),
        ).fetchone()

        with privileged_conn.transaction(force_rollback=True):
            signal_id = str(uuid.uuid4())
            TestLiveConstraints._insert(privileged_conn, other_workspace)
            other_signal = privileged_conn.execute(
                "SELECT id FROM nlp.signals WHERE workspace_id = %s", (other_workspace,)
            ).fetchone()[0]
            with pytest.raises(psycopg.Error) as caught:
                privileged_conn.execute(
                    """INSERT INTO nlp.signal_inputs (
                           id, workspace_id, signal_id, normalized_record_id,
                           raw_record_id, source_id, observation_key, record_kind_id,
                           period_label, period_type, input_quality, role, input_position)
                       VALUES (%s,%s,%s,%s,%s,'world-bank','k','numeric_observation',
                               '2018','YEAR','VALID','CONTRIBUTED',0)""",
                    (
                        signal_id,
                        other_workspace,
                        other_signal,
                        foreign_record[0],
                        foreign_record[1],
                    ),
                )
            assert caught.value.diag.constraint_name == "signal_inputs_record_tenant_fkey"

    def test_a_worker_cannot_derive_across_workspaces(
        self, committing_tenant_conn, probe_workspace, other_workspace
    ) -> None:
        """The records live in one workspace and the job runs in the other, so
        the derivation sees nothing rather than reaching across."""
        from sros_nlp import run_signal_derivation_job

        with committing_tenant_conn(probe_workspace) as conn:
            _seed_numeric(conn, probe_workspace, "2018", "100")
            _seed_numeric(conn, probe_workspace, "2019", "150")

        result = run_signal_derivation_job(
            _payload(other_workspace, research_session_id=OTHER_SESSION),
            committing_tenant_conn,
        )
        assert result.run.records_considered == 0
        assert result.persisted.new == 0
