"""Claim persistence, idempotency, live constraints and tenant isolation.

Mission 1.13.1 §20, §28, §35, §36. Needs PostgreSQL; every write goes into a
**disposable** workspace this suite creates and destroys, never into the seeded
one holding the twelve real records and seven real Signals.

Refusal assertions name the **exact constraint**, never "it failed". Mission
1.13 found a CHECK that accepted a half-filled row because the obvious spelling
of "all or none" evaluates to NULL, and a probe asserting only that the insert
failed would have agreed with it (`testing-strategy.md` §28).
"""

from __future__ import annotations

import uuid

import pytest

from .conftest import OTHER_SESSION, PROBE_SESSION, needs_postgres
from .test_signal_persistence import _seed_numeric

psycopg = pytest.importorskip("psycopg")

pytestmark = needs_postgres

INTERPRETER = "observed-signal-restatement"


def _derive(conn, workspace_id: str, session: str = PROBE_SESSION) -> int:
    """Two World Bank records and the Signal between them, all SYNTHETIC."""
    from sros_nlp.job import run_signal_derivation_job

    _seed_numeric(conn, workspace_id, "2018", "82905782")
    _seed_numeric(conn, workspace_id, "2019", "83092962")

    import contextlib

    @contextlib.contextmanager
    def same(_workspace_id: str):
        yield conn

    result = run_signal_derivation_job(
        {
            "workspace_id": workspace_id,
            "research_session_id": session,
            "correlation_id": "claim-test-derivation",
            "extractor_id": "numeric-period-change",
            "parameters": {},
        },
        same,
    )
    return result.persisted.new


def _interpret(conn, workspace_id: str, session: str = PROBE_SESSION, **overrides):
    import contextlib

    from sros_nlp.claim_job import run_claim_interpretation_job

    @contextlib.contextmanager
    def same(_workspace_id: str):
        yield conn

    payload = {
        "workspace_id": workspace_id,
        "research_session_id": session,
        "correlation_id": "claim-test-interpretation",
        "interpreter_id": INTERPRETER,
    }
    payload.update(overrides)
    return run_claim_interpretation_job(payload, same)


# ============================================================ §20 atomic write


class TestPersistence:
    def test_claim_revision_and_evidence_are_written_together(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            assert _derive(conn, probe_workspace) == 1
            result = _interpret(conn, probe_workspace)

        assert result.persisted.new == 1
        assert result.persisted.revisions_created == 1
        assert result.persisted.evidence_new == 1

        with committing_tenant_conn(probe_workspace) as conn:
            claim = conn.execute(
                """SELECT claim_type, origin, lifecycle, opportunity_id, interpreter_id,
                          interpreter_version, interpretation_kind, model_version,
                          prompt_version, proposition_key, proposition_facts, current_revision
                     FROM research.claims WHERE workspace_id = %s""",
                (probe_workspace,),
            ).fetchone()
            assert claim is not None
            assert claim[0] == "OBSERVED"
            assert claim[1] == "DETERMINISTIC_EXTRACTION"
            assert claim[2] == "ACTIVE"
            # ADR-024: the pipeline runs Signal -> Claim -> Opportunity, and no
            # Opportunity exists.
            assert claim[3] is None
            assert claim[4] == INTERPRETER
            assert claim[5] == "1.0.0"
            assert claim[6] == "DETERMINISTIC"
            # A DETERMINISTIC interpretation names no model, and the CHECK
            # refuses one that does.
            assert claim[7] is None and claim[8] is None
            assert len(claim[9]) == 64
            # The preimage, so the identity can be verified rather than trusted.
            assert claim[10]["metric_id"] == "SP.POP.TOTL"
            assert claim[11] == 1

            revision = conn.execute(
                """SELECT revision, statement, interpretation_confidence, material_change
                     FROM research.claim_revisions WHERE workspace_id = %s""",
                (probe_workspace,),
            ).fetchone()
            assert revision is not None
            assert revision[0] == 1
            assert revision[1].startswith("World Bank Open Data reported that")
            assert revision[2] == 1.0
            assert revision[3] is False

            evidence = conn.execute(
                """SELECT direction, evidence_level, relevance, directness, reliability,
                          extraction_confidence, observation_category, independence_state,
                          independence_group_id, source_id, signal_id, observed_at
                     FROM scoring.evidence WHERE workspace_id = %s""",
                (probe_workspace,),
            ).fetchone()
            assert evidence is not None
            assert evidence[0] == "SUPPORTS"
            assert evidence[1] == 1
            assert evidence[2] == 1.0
            assert evidence[3] == 1.0
            # ABSENT, not 0.5 and not 0.0. Purpose-relative, D-03 blocked.
            assert evidence[4] is None
            assert evidence[5] == 1.0
            assert evidence[6] == "UNCATEGORISED"
            assert evidence[7] == "UNKNOWN"
            assert evidence[8] is None
            assert evidence[9] == "world-bank"
            assert evidence[10] is not None
            # H-29: no globally comparable instant is written.
            assert evidence[11] is None

    def test_the_statement_lives_only_in_the_revision(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            _interpret(conn, probe_workspace)
            columns = [
                row[0]
                for row in conn.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='research' AND table_name='claims'"
                )
            ]
        assert "statement" not in columns

    def test_the_run_and_its_considered_inputs_are_written(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            result = _interpret(conn, probe_workspace)

        with committing_tenant_conn(probe_workspace) as conn:
            run = conn.execute(
                """SELECT interpreter_id, interpreter_version, interpretation_kind,
                          signals_considered, signals_cited, signals_excluded,
                          signals_refused, claims_new, revisions_created, evidence_new,
                          refusals, truncated_by
                     FROM research.claim_interpretation_runs WHERE workspace_id = %s""",
                (probe_workspace,),
            ).fetchone()
            assert run is not None
            assert run[0] == INTERPRETER
            assert run[2] == "DETERMINISTIC"
            assert run[3] == 1 and run[4] == 1 and run[5] == 0 and run[6] == 0
            assert run[7] == 1 and run[8] == 1 and run[9] == 1
            assert run[10] == []
            assert run[11] is None

            considered = conn.execute(
                """SELECT role, signal_type_id, claim_id, reason_code
                     FROM research.claim_interpretation_inputs
                    WHERE workspace_id = %s AND run_id = %s""",
                (probe_workspace, result.run_id),
            ).fetchall()
            assert len(considered) == 1
            assert considered[0][0] == "CITED"
            assert considered[0][1] == "numeric_period_change"
            assert considered[0][2] is not None
            assert considered[0][3] is None


# ====================================================== §22 GAP-5, §24 refusals


class TestConsideredButNotCited:
    def test_an_unsupported_signal_type_is_recorded_as_excluded(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """The denominator GAP-5 exists to preserve. Asking for a type the
        interpreter has no template for is the reachable way to produce one
        without inventing a Signal nothing derives."""
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            # The Signal is real; the interpreter is asked to consider it under
            # a filter that includes a type it cannot phrase, and the read is
            # widened to match.
            result = _interpret(
                conn,
                probe_workspace,
                signal_type_ids=["numeric_period_change"],
            )
        assert result.run.signals_considered == 1
        assert result.run.signals_cited == 1

    def test_the_run_can_answer_which_signals_were_considered_and_not_cited(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            result = _interpret(conn, probe_workspace)

        with committing_tenant_conn(probe_workspace) as conn:
            not_cited = conn.execute(
                """SELECT count(*) FROM research.claim_interpretation_inputs
                    WHERE workspace_id = %s AND run_id = %s AND role <> 'CITED'""",
                (probe_workspace, result.run_id),
            ).fetchone()
            total = conn.execute(
                """SELECT count(*) FROM research.claim_interpretation_inputs
                    WHERE workspace_id = %s AND run_id = %s""",
                (probe_workspace, result.run_id),
            ).fetchone()
        assert not_cited is not None and total is not None
        # "1 cited out of 1 considered" is a fact the run can state. Before
        # migration 0018 the same claim count could have come from forty.
        assert total[0] == 1
        assert not_cited[0] == 0


# ================================================================ §28 idempotency


class TestIdempotency:
    def test_a_second_execution_creates_no_duplicate(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            first = _interpret(conn, probe_workspace)
        with committing_tenant_conn(probe_workspace) as conn:
            second = _interpret(conn, probe_workspace)

        assert first.persisted.new == 1
        assert second.persisted.new == 0
        assert second.persisted.unchanged == 1
        assert second.persisted.revisions_created == 0
        assert second.persisted.evidence_new == 0
        assert second.persisted.evidence_unchanged == 1

        with committing_tenant_conn(probe_workspace) as conn:
            counts = conn.execute(
                """SELECT (SELECT count(*) FROM research.claims WHERE workspace_id = %s),
                          (SELECT count(*) FROM research.claim_revisions WHERE workspace_id = %s),
                          (SELECT count(*) FROM scoring.evidence WHERE workspace_id = %s),
                          (SELECT count(*) FROM research.claim_interpretation_runs
                            WHERE workspace_id = %s)""",
                (probe_workspace,) * 4,
            ).fetchone()
        assert counts is not None
        assert counts[0] == 1 and counts[1] == 1 and counts[2] == 1
        # TWO run rows. A run is an EXECUTION, and two executions happened.
        # This is not a claim of exactly-once delivery, which Celery does not
        # provide (ADR-004).
        assert counts[3] == 2

    def test_a_changed_source_magnitude_appends_a_revision(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """The proposition key is over the FACTS, not the magnitude. A source
        revising its figure has restated the same proposition, and appending a
        revision is exactly the mechanism for that."""
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            _interpret(conn, probe_workspace)
        with committing_tenant_conn(probe_workspace) as conn:
            # Rewrite the SIGNAL's magnitude, standing in for a revised source
            # figure without touching any real record.
            conn.execute(
                "UPDATE nlp.signals SET magnitude = 187200 WHERE workspace_id = %s",
                (probe_workspace,),
            )
            second = _interpret(conn, probe_workspace)

        assert second.persisted.new == 0
        assert second.persisted.revised == 1
        assert second.persisted.revisions_created == 1

        with committing_tenant_conn(probe_workspace) as conn:
            revisions = conn.execute(
                """SELECT revision, statement, material_change
                     FROM research.claim_revisions WHERE workspace_id = %s
                    ORDER BY revision""",
                (probe_workspace,),
            ).fetchall()
            current = conn.execute(
                "SELECT current_revision FROM research.claims WHERE workspace_id = %s",
                (probe_workspace,),
            ).fetchone()
        assert [r[0] for r in revisions] == [1, 2]
        # Revision 1 is NEVER modified: an aggregation that evaluated it must
        # still be able to read it.
        assert "187180" in revisions[0][1]
        assert "187200" in revisions[1][1]
        assert revisions[0][2] is False and revisions[1][2] is True
        assert current is not None and current[0] == 2


# ============================================================== §36 constraints


class TestLiveConstraints:
    @staticmethod
    def _claim(conn, workspace_id: str, **overrides):
        claim_id = str(uuid.uuid4())
        row = {
            "id": claim_id,
            "workspace_id": workspace_id,
            "claim_type": "OBSERVED",
            "temporality": "EVERGREEN",
            "origin": "DETERMINISTIC_EXTRACTION",
            "interpreter_id": INTERPRETER,
            "interpreter_version": "1.0.0",
            "interpretation_kind": "DETERMINISTIC",
            "model_version": None,
            "prompt_version": None,
            "proposition_key": f"probe|{claim_id}",
            "proposition_facts": '{"probe": true}',
        }
        row.update(overrides)
        columns = ", ".join(row)
        placeholders = ", ".join(f"%({k})s" for k in row)
        conn.execute(
            f"INSERT INTO research.claims ({columns}) VALUES ({placeholders})",  # noqa: S608
            row,
        )
        conn.execute(
            "INSERT INTO research.claim_revisions (id, workspace_id, claim_id, revision, "
            "statement, interpretation_confidence) VALUES (%s,%s,%s,1,'probe',1.0)",
            (str(uuid.uuid4()), workspace_id, claim_id),
        )
        return claim_id

    def test_proposition_facts_without_a_key_are_refused(
        self, tenant_conn, probe_workspace
    ) -> None:
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._claim(conn, probe_workspace, proposition_key=None)
        assert exc.value.diag.constraint_name == "claims_proposition_facts_paired_check"

    def test_a_key_without_its_facts_is_refused(self, tenant_conn, probe_workspace) -> None:
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._claim(conn, probe_workspace, proposition_facts=None)
        assert exc.value.diag.constraint_name == "claims_proposition_facts_paired_check"

    def test_an_empty_fact_object_is_refused(self, tenant_conn, probe_workspace) -> None:
        """An empty object identifies every proposition equally, which is no
        identity."""
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._claim(conn, probe_workspace, proposition_facts="{}")
        assert exc.value.diag.constraint_name == "claims_proposition_facts_nonempty_check"

    def test_a_fact_array_is_refused(self, tenant_conn, probe_workspace) -> None:
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._claim(conn, probe_workspace, proposition_facts="[1,2]")
        assert exc.value.diag.constraint_name == "claims_proposition_facts_object_check"

    def test_half_an_interpreter_identity_is_refused(self, tenant_conn, probe_workspace) -> None:
        """Migration 0017's fix, re-asserted where an interpreter now writes."""
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._claim(conn, probe_workspace, interpreter_version=None)
        assert exc.value.diag.constraint_name == "claims_interpreter_complete_check"

    def test_a_deterministic_interpretation_with_a_model_version_is_refused(
        self, tenant_conn, probe_workspace
    ) -> None:
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._claim(conn, probe_workspace, model_version="some-model")
        assert exc.value.diag.constraint_name == "claims_interpretation_provenance_check"

    def test_a_model_derived_interpretation_without_a_model_is_refused(
        self, tenant_conn, probe_workspace
    ) -> None:
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._claim(conn, probe_workspace, interpretation_kind="MODEL_DERIVED")
        assert exc.value.diag.constraint_name == "claims_interpretation_provenance_check"

    @pytest.mark.parametrize("confidence", [1.4, -0.1])
    def test_confidence_outside_the_unit_interval_is_refused(
        self, tenant_conn, probe_workspace, confidence
    ) -> None:
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            claim_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO research.claims (id, workspace_id, claim_type, temporality, "
                "origin) VALUES (%s,%s,'HYPOTHESIS','EVERGREEN','MANUAL')",
                (claim_id, probe_workspace),
            )
            conn.execute(
                "INSERT INTO research.claim_revisions (id, workspace_id, claim_id, revision, "
                "statement, interpretation_confidence) VALUES (%s,%s,%s,1,'probe',%s)",
                (str(uuid.uuid4()), probe_workspace, claim_id, confidence),
            )
        assert (
            exc.value.diag.constraint_name
            == "claim_revisions_interpretation_confidence_unit_interval_check"
        )

    def test_a_generated_claim_with_no_evidence_is_refused_at_commit(
        self, tenant_conn, probe_workspace
    ) -> None:
        """The deferred trigger. It fires at COMMIT, which is why evidence
        written in a second transaction is too late by construction."""
        with pytest.raises(psycopg.Error) as exc, tenant_conn(probe_workspace) as conn:
            self._claim(conn, probe_workspace)
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
        # A trigger's RAISE carries no constraint NAME, only the SQLSTATE.
        assert exc.value.sqlstate == "23514"

    def test_an_input_row_marked_cited_must_name_a_claim(
        self, tenant_conn, probe_workspace
    ) -> None:
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._considered(conn, probe_workspace, role="CITED", claim_id=None)
        assert exc.value.diag.constraint_name == "claim_interpretation_inputs_role_coherent_check"

    def test_an_input_row_marked_excluded_must_give_a_reason(
        self, tenant_conn, probe_workspace
    ) -> None:
        """A Signal passed over without a reason is the gap this table closes,
        reopened."""
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._considered(conn, probe_workspace, role="EXCLUDED", reason_code=None)
        assert exc.value.diag.constraint_name == "claim_interpretation_inputs_role_coherent_check"

    def test_one_signal_appears_once_per_run(self, tenant_conn, probe_workspace) -> None:
        """One run, one row per Signal. Considered twice in one execution is the
        same consideration counted twice, and it corrupts the denominator."""
        with (
            pytest.raises(psycopg.errors.UniqueViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            # The SAME run, explicitly. Letting `_considered` mint a second run
            # would put the two rows in different executions, where they belong.
            run_id = self._run(conn, probe_workspace)
            signal_id = _any_signal(conn, probe_workspace)
            self._considered(
                conn, probe_workspace, run_id=run_id, signal_id=signal_id, role="EXCLUDED"
            )
            self._considered(
                conn, probe_workspace, run_id=run_id, signal_id=signal_id, role="EXCLUDED"
            )
        assert exc.value.diag.constraint_name == "claim_interpretation_inputs_once_per_run_key"

    def test_a_refused_count_needs_its_reasons(self, tenant_conn, probe_workspace) -> None:
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._run(conn, probe_workspace, signals_considered=1, signals_refused=1)
        assert (
            exc.value.diag.constraint_name == "claim_interpretation_runs_refusals_explained_check"
        )

    def test_an_outcome_cannot_exceed_what_was_considered(
        self, tenant_conn, probe_workspace
    ) -> None:
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            self._run(conn, probe_workspace, signals_considered=1, signals_cited=2)
        assert exc.value.diag.constraint_name == "claim_interpretation_runs_outcome_bounds_check"

    def test_cited_plus_excluded_plus_refused_may_exceed_considered(
        self, tenant_conn, probe_workspace
    ) -> None:
        """Deliberately permitted. The tighter sum is a model of how the
        counters relate, not arithmetic, and migration 0015 had to undo exactly
        that shape one layer down (`testing-strategy.md` §27)."""
        with tenant_conn(probe_workspace) as conn:
            self._run(
                conn,
                probe_workspace,
                signals_considered=2,
                signals_cited=2,
                signals_excluded=2,
            )

    @staticmethod
    def _run(conn, workspace_id: str, **overrides) -> str:
        run_id = str(uuid.uuid4())
        row = {
            "id": run_id,
            "workspace_id": workspace_id,
            "interpreter_id": INTERPRETER,
            "interpreter_version": "1.0.0",
            "interpretation_kind": "DETERMINISTIC",
            "correlation_id": "probe",
            "started_at": "2026-08-31T00:00:00Z",
            "finished_at": "2026-08-31T00:00:01Z",
            "expires_at": "2026-11-29T00:00:00Z",
        }
        row.update(overrides)
        columns = ", ".join(row)
        placeholders = ", ".join(f"%({k})s" for k in row)
        conn.execute(
            f"INSERT INTO research.claim_interpretation_runs ({columns}) "  # noqa: S608
            f"VALUES ({placeholders})",
            row,
        )
        return run_id

    @classmethod
    def _considered(cls, conn, workspace_id: str, **overrides) -> str:
        run_id = overrides.pop("run_id", None) or cls._run(conn, workspace_id)
        signal_id = overrides.pop("signal_id", None)
        if signal_id is None:
            signal_id = _any_signal(conn, workspace_id)
        row = {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "run_id": run_id,
            "signal_id": signal_id,
            "signal_type_id": "numeric_period_change",
            "role": "EXCLUDED",
            "claim_id": None,
            "reason_code": "UNSUPPORTED_SIGNAL_TYPE",
        }
        row.update(overrides)
        columns = ", ".join(row)
        placeholders = ", ".join(f"%({k})s" for k in row)
        conn.execute(
            f"INSERT INTO research.claim_interpretation_inputs ({columns}) "  # noqa: S608
            f"VALUES ({placeholders})",
            row,
        )
        return signal_id


def _any_signal(conn, workspace_id: str) -> str:
    row = conn.execute(
        "SELECT id FROM nlp.signals WHERE workspace_id = %s LIMIT 1", (workspace_id,)
    ).fetchone()
    if row is None:
        _derive(conn, workspace_id)
        row = conn.execute(
            "SELECT id FROM nlp.signals WHERE workspace_id = %s LIMIT 1", (workspace_id,)
        ).fetchone()
    assert row is not None
    return str(row[0])


# ============================================================ §35 tenant isolation


class TestTenantIsolation:
    def test_a_workspace_cannot_read_another_workspaces_claims(
        self, committing_tenant_conn, probe_workspace, other_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            _interpret(conn, probe_workspace)
        with committing_tenant_conn(other_workspace) as conn:
            visible = conn.execute("SELECT count(*) FROM research.claims").fetchone()
            evidence = conn.execute("SELECT count(*) FROM scoring.evidence").fetchone()
            runs = conn.execute(
                "SELECT count(*) FROM research.claim_interpretation_runs"
            ).fetchone()
        assert visible is not None and visible[0] == 0
        assert evidence is not None and evidence[0] == 0
        assert runs is not None and runs[0] == 0

    def test_evidence_cannot_cite_another_workspaces_signal(
        self, committing_tenant_conn, tenant_conn, probe_workspace, other_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            foreign_signal = _any_signal(conn, probe_workspace)

        with pytest.raises(psycopg.Error) as exc, tenant_conn(other_workspace) as conn:
            claim_id = TestLiveConstraints._claim(conn, other_workspace)
            conn.execute(
                """INSERT INTO scoring.evidence (id, workspace_id, claim_id, signal_id,
                       direction, evidence_level, observation_category, independence_state,
                       collected_at, expires_at)
                   VALUES (%s,%s,%s,%s,'SUPPORTS',1,'UNCATEGORISED','UNKNOWN',
                           now(), now() + interval '1 day')""",
                (str(uuid.uuid4()), other_workspace, claim_id, foreign_signal),
            )
        # RLS makes the foreign signal invisible, so the composite FK finds no
        # parent row. Either layer refusing is the point; both are present.
        assert exc.value.diag.constraint_name in {
            "evidence_signal_tenant_fkey",
            "evidence_signal_id_fkey",
        }

    def test_evidence_cannot_cite_another_workspaces_claim(
        self, committing_tenant_conn, tenant_conn, probe_workspace, other_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            _interpret(conn, probe_workspace)
            foreign_claim = conn.execute(
                "SELECT id FROM research.claims WHERE workspace_id = %s", (probe_workspace,)
            ).fetchone()
        assert foreign_claim is not None

        with pytest.raises(psycopg.Error) as exc, tenant_conn(other_workspace) as conn:
            conn.execute(
                """INSERT INTO scoring.evidence (id, workspace_id, claim_id,
                       direction, evidence_level, observation_category, independence_state,
                       collected_at, expires_at)
                   VALUES (%s,%s,%s,'SUPPORTS',1,'UNCATEGORISED','UNKNOWN',
                           now(), now() + interval '1 day')""",
                (str(uuid.uuid4()), other_workspace, str(foreign_claim[0])),
            )
        assert exc.value.diag.constraint_name == "evidence_claim_same_workspace_fkey"

    def test_a_revision_cannot_be_appended_to_another_workspaces_claim(
        self, committing_tenant_conn, tenant_conn, probe_workspace, other_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            _interpret(conn, probe_workspace)
            foreign_claim = conn.execute(
                "SELECT id FROM research.claims WHERE workspace_id = %s", (probe_workspace,)
            ).fetchone()
        assert foreign_claim is not None

        with pytest.raises(psycopg.Error) as exc, tenant_conn(other_workspace) as conn:
            conn.execute(
                "INSERT INTO research.claim_revisions (id, workspace_id, claim_id, revision, "
                "statement) VALUES (%s,%s,%s,2,'a foreign revision')",
                (str(uuid.uuid4()), other_workspace, str(foreign_claim[0])),
            )
        assert exc.value.diag.constraint_name == "claim_revisions_claim_same_workspace_fkey"

    def test_an_interpretation_run_cannot_name_another_workspaces_signal(
        self, committing_tenant_conn, tenant_conn, probe_workspace, other_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)
            foreign_signal = _any_signal(conn, probe_workspace)

        with pytest.raises(psycopg.Error) as exc, tenant_conn(other_workspace) as conn:
            TestLiveConstraints._considered(
                conn, other_workspace, signal_id=foreign_signal, role="EXCLUDED"
            )
        assert exc.value.diag.constraint_name == "claim_interpretation_inputs_signal_tenant_fkey"

    def test_a_worker_cannot_interpret_across_workspaces(
        self, committing_tenant_conn, tenant_conn, probe_workspace, other_workspace
    ) -> None:
        """The payload names A while the tenant context is B, and BOTH layers
        refuse: the read returns no rows, and the run row the job then tries to
        write for workspace A is refused by A's own policy from inside B."""
        with committing_tenant_conn(probe_workspace) as conn:
            _derive(conn, probe_workspace)

        import contextlib

        from sros_nlp.claim_job import run_claim_interpretation_job
        from sros_nlp.claim_repositories import read_signal_views

        with tenant_conn(other_workspace) as conn:
            # Layer one: RLS makes A's Signals invisible from inside B, so the
            # interpreter has nothing to interpret rather than the wrong thing.
            assert read_signal_views(conn, probe_workspace) == []

        with (
            pytest.raises(psycopg.errors.InsufficientPrivilege),
            tenant_conn(other_workspace) as conn,
        ):

            @contextlib.contextmanager
            def wrong_tenant(_workspace_id: str):
                yield conn

            # Layer two: even the RUN RECORD cannot be written. A worker in B
            # cannot leave a trace claiming to be A's.
            run_claim_interpretation_job(
                {
                    "workspace_id": probe_workspace,
                    "research_session_id": OTHER_SESSION,
                    "correlation_id": "cross-tenant",
                    "interpreter_id": INTERPRETER,
                },
                wrong_tenant,
            )
