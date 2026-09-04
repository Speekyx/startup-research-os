"""Mission 1.51. The two additive records, against the real database.

The load-bearing test in this file is `TheDerivationOutlivesTheExecutionLog`.
ADR-037's entire schema verdict rests on one claim: a durable derivation must not
disappear when a retention-bounded interpretation run does. That is a property of
foreign keys, not of prose, so it is exercised against real rows and a real
DELETE rather than asserted.

The second is `TheTwoIdempotencyKeysDiffer`. Evidence must NOT duplicate when a
rule version changes; a derivation record MUST. Those two facts are deliberately
in tension and a future evaluator could easily collapse them, so the difference
is pinned here.

Every fixture row is SYNTHETIC and lives in a disposable probe workspace.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from .conftest import needs_postgres

psycopg = pytest.importorskip("psycopg")

pytestmark = needs_postgres

RULE = "threshold-state-evaluator"
BASIS = "equivalence-basis-fixture-1"


def _threshold(conn, workspace_id: str, **overrides) -> str:
    """One synthetic threshold registration. Fixture-owned bound, never a
    reviewed one."""
    row = {
        "id": str(uuid.uuid4()),
        "workspace_id": workspace_id,
        "threshold_operator": "GTE",
        "threshold_value": "100",
        "unit": "unit-1",
        "metric_definition_id": "metric-def-1",
        # A fresh scope per call by default, so two registrations in one test do
        # not collide on the idempotency key by accident. A test that WANTS the
        # collision passes the same scope explicitly.
        "scope_subject_id": f"subject-{uuid.uuid4()}",
        "scope_population": "population-1",
        "scope_time_bound": "2024",
        "provenance_status": "PREREGISTERED",
        "recorded_at": datetime(2026, 1, 1, tzinfo=UTC),
        "recorded_by": "mission-1.51-fixture",
        "provenance_reference": "fixture-registration",
    }
    row.update(overrides)
    columns = ", ".join(row)
    placeholders = ", ".join(["%s"] * len(row))
    conn.execute(
        f"INSERT INTO research.threshold_registrations ({columns}) VALUES ({placeholders})",  # noqa: S608
        tuple(row.values()),
    )
    return row["id"]


def _signal(conn, workspace_id: str) -> str:
    """One synthetic Signal. No byte came from any source."""
    signal_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    conn.execute(
        """INSERT INTO nlp.signals (
               id, workspace_id, quantity_family, signal_type_id, extraction_method,
               derived_at, expires_at, magnitude, magnitude_kind, magnitude_unit,
               magnitude_unit_state, direction, extractor_id, extractor_version,
               signal_schema_id, signal_schema_version, derivation_kind, parameters,
               parameter_fingerprint, derivation_fingerprint, scope, temporal_basis,
               temporal_window, correlation_id)
           VALUES (%s,%s,'MEASURED_SERIES','numeric_period_change','fixture@1.0.0',
                   %s,%s,'110','ABSOLUTE_DIFFERENCE','unit-1','INHERITED','NOT_APPLICABLE',
                   'fixture','1.0.0','sros.signal',1,'DETERMINISTIC',%s,%s,%s,%s,'NONE',%s,
                   'mission-1.51-fixture')""",
        (
            signal_id,
            workspace_id,
            now,
            now + timedelta(days=365),
            json.dumps({"fixture": True}),
            f"pf-{signal_id}",
            f"df-{signal_id}",
            json.dumps({"source_ids": ["fixture-source"]}),
            json.dumps({"basis": "NONE", "resolution": "DAY", "period_labels": []}),
        ),
    )
    return signal_id


def _claim_revision(conn, workspace_id: str) -> tuple[str, str]:
    """A HYPOTHESIS/MANUAL Claim, which is exempt from the evidence requirement,
    so a schema fixture needs no Evidence row to exist."""
    claim_id = str(uuid.uuid4())
    revision_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO research.claims (id, workspace_id, claim_type, temporality, origin)"
        " VALUES (%s,%s,'HYPOTHESIS','EVERGREEN','MANUAL')",
        (claim_id, workspace_id),
    )
    conn.execute(
        "INSERT INTO research.claim_revisions (id, workspace_id, claim_id, revision,"
        " statement, interpretation_confidence) VALUES (%s,%s,%s,1,'probe',1.0)",
        (revision_id, workspace_id, claim_id),
    )
    return claim_id, revision_id


def _derivation(conn, workspace_id: str, revision_id: str, signal_id: str, **overrides) -> str:
    row = {
        "id": str(uuid.uuid4()),
        "workspace_id": workspace_id,
        "claim_revision_id": revision_id,
        "input_signal_id": signal_id,
        "derivation_rule_id": RULE,
        "derivation_rule_version": "1.0.0",
        "evaluator_version": "1.0.0",
        "measurement_value": "110",
        "evaluation_result": "SUPPORTS",
        "semantic_equivalence_basis_id": BASIS,
        "interpretation_kind": "DETERMINISTIC",
        "rationale": "110 satisfies the preregistered bound >= 100.",
    }
    row.update(overrides)
    columns = ", ".join(row)
    placeholders = ", ".join(["%s"] * len(row))
    conn.execute(
        f"INSERT INTO research.claim_derivations ({columns}) VALUES ({placeholders})",  # noqa: S608
        tuple(row.values()),
    )
    return row["id"]


# ============================================ §32 the retention proof


class TheDerivationOutlivesTheExecutionLog:
    """The load-bearing test. ADR-037 rejected `claim_interpretation_inputs` as
    the derivation home because it cascades from an EXPIRING run. If the new
    table ever acquired the same dependency, a Claim would again outlive its own
    reasoning -- so this deletes a real run and checks a real derivation."""


class TestRetentionIndependence:
    def test_a_derivation_survives_deleting_an_interpretation_run(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        run_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            _, revision_id = _claim_revision(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            derivation_id = _derivation(
                conn,
                probe_workspace,
                revision_id,
                signal_id,
                threshold_registration_id=threshold_id,
            )
            # A real interpretation run with a bounded expiry, and a real input
            # row naming the same Signal -- the shape ADR-037 measured.
            conn.execute(
                """INSERT INTO research.claim_interpretation_runs (
                       id, workspace_id, interpreter_id, interpreter_version,
                       interpretation_kind, started_at, finished_at, expires_at,
                       correlation_id)
                   VALUES (%s,%s,'fixture','1.0.0','DETERMINISTIC',%s,%s,%s,
                           'mission-1.51-fixture')""",
                (run_id, probe_workspace, now, now, now + timedelta(days=90)),
            )
            conn.execute(
                """INSERT INTO research.claim_interpretation_inputs (
                       id, workspace_id, run_id, signal_id, signal_type_registry,
                       signal_type_id, role, reason_code, input_position)
                   VALUES (%s,%s,%s,%s,'signal_type','numeric_period_change',
                           'EXCLUDED','UNSUPPORTED_SIGNAL_TYPE',0)""",
                (str(uuid.uuid4()), probe_workspace, run_id, signal_id),
            )

        with committing_tenant_conn(probe_workspace) as conn:
            # The legitimate cleanup: delete the expired run. Its inputs cascade.
            conn.execute("DELETE FROM research.claim_interpretation_runs WHERE id = %s", (run_id,))

        with committing_tenant_conn(probe_workspace) as conn:
            inputs = conn.execute(
                "SELECT count(*) FROM research.claim_interpretation_inputs WHERE run_id = %s",
                (run_id,),
            ).fetchone()[0]
            survived = conn.execute(
                "SELECT count(*) FROM research.claim_derivations WHERE id = %s",
                (derivation_id,),
            ).fetchone()[0]

        assert inputs == 0, "the interpretation inputs should have cascaded away"
        assert survived == 1, (
            "the derivation must outlive the execution log. If this fails, a Claim "
            "can again outlive the record of how it was derived, which is the exact "
            "defect ADR-037 exists to prevent"
        )

    def test_the_derivation_table_has_no_foreign_key_to_an_expiring_run(
        self, privileged_conn
    ) -> None:
        """Structural, not behavioural: even a nullable FK would make the
        dependency possible for someone to add later."""
        referenced = privileged_conn.execute(
            """SELECT DISTINCT confrelid::regclass::text
                 FROM pg_constraint
                WHERE conrelid = 'research.claim_derivations'::regclass
                  AND contype = 'f'"""
        ).fetchall()
        names = {row[0] for row in referenced}
        assert "research.claim_interpretation_runs" not in names
        assert "research.claim_interpretation_inputs" not in names

    def test_a_signal_cited_by_a_derivation_cannot_be_silently_purged(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        """`nlp.signals` carries a populated `expires_at` on every row, so a
        future retention purge must not take the reasoning with it. NO ACTION
        makes that deletion fail rather than succeed quietly."""

        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            _, revision_id = _claim_revision(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _derivation(
                conn,
                probe_workspace,
                revision_id,
                signal_id,
                threshold_registration_id=threshold_id,
            )

        with (
            pytest.raises(psycopg.errors.ForeignKeyViolation),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            conn.execute("DELETE FROM nlp.signals WHERE id = %s", (signal_id,))


# ============================================ §33 the idempotency contrast


class TestTheTwoIdempotencyKeysDiffer:
    def test_a_new_rule_version_creates_a_second_derivation(
        self, committing_tenant_conn, probe_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            _, revision_id = _claim_revision(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _derivation(
                conn,
                probe_workspace,
                revision_id,
                signal_id,
                derivation_rule_version="1.0.0",
                threshold_registration_id=threshold_id,
            )
            _derivation(
                conn,
                probe_workspace,
                revision_id,
                signal_id,
                derivation_rule_version="2.0.0",
                threshold_registration_id=threshold_id,
                evaluation_result="CONTRADICTS",
                measurement_value="90",
                rationale="90 does not satisfy the preregistered bound >= 100.",
            )
            count = conn.execute(
                """SELECT count(*) FROM research.claim_derivations
                    WHERE claim_revision_id = %s AND input_signal_id = %s""",
                (revision_id, signal_id),
            ).fetchone()[0]

        assert count == 2, (
            "two rule versions over one input are two pieces of reasoning, and both "
            "must remain inspectable"
        )

    def test_the_same_rule_version_twice_is_refused(
        self, committing_tenant_conn, probe_workspace
    ) -> None:

        with (
            pytest.raises(psycopg.errors.UniqueViolation) as exc,
            committing_tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _, revision_id = _claim_revision(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            for _ in range(2):
                _derivation(
                    conn,
                    probe_workspace,
                    revision_id,
                    signal_id,
                    threshold_registration_id=threshold_id,
                )
        assert exc.value.diag.constraint_name == "claim_derivations_identity_key"

    def test_the_evidence_key_deliberately_excludes_the_procedure_version(
        self, privileged_conn
    ) -> None:
        """The other half of the contrast, read from the live schema. Mission
        1.41 REMOVED the procedure version from Evidence identity so a version
        bump could not INSERT a duplicate. The derivation key INCLUDES it. If
        these ever converged, one of the two guarantees would be lost."""
        evidence_keys = privileged_conn.execute(
            """SELECT pg_get_constraintdef(oid) FROM pg_constraint
                WHERE conrelid = 'scoring.evidence'::regclass AND contype IN ('u','p')"""
        ).fetchall()
        derivation_key = privileged_conn.execute(
            """SELECT pg_get_constraintdef(oid) FROM pg_constraint
                WHERE conrelid = 'research.claim_derivations'::regclass
                  AND conname = 'claim_derivations_identity_key'"""
        ).fetchone()[0]

        assert "derivation_rule_version" in derivation_key
        assert not any("extraction_method" in definition[0] for definition in evidence_keys)


# ============================================ threshold registration


class TestThresholdRegistration:
    STATUSES = ("PREREGISTERED", "SOURCE_NATIVE", "EXTERNAL_NORM", "POST_HOC", "UNKNOWN")

    def _norm_fields(self, status: str) -> dict:
        if status != "EXTERNAL_NORM":
            return {}
        return {
            "norm_issuer": "issuer",
            "norm_document_id": "doc-1",
            "norm_version": "2024",
            "norm_section": "§4",
        }

    def test_all_five_statuses_are_accepted(self, tenant_conn, probe_workspace) -> None:
        with tenant_conn(probe_workspace) as conn:
            for index, status in enumerate(self.STATUSES):
                _threshold(
                    conn,
                    probe_workspace,
                    provenance_status=status,
                    threshold_value=str(100 + index),
                    **self._norm_fields(status),
                )

    def test_a_sixth_status_is_refused(self, tenant_conn, probe_workspace) -> None:

        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            _threshold(conn, probe_workspace, provenance_status="PROBABLY_FINE")
        assert exc.value.diag.constraint_name == "threshold_registrations_provenance_status_check"

    def test_preregistered_requires_a_provenance_reference(
        self, tenant_conn, probe_workspace
    ) -> None:

        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            _threshold(conn, probe_workspace, provenance_reference=None)
        assert exc.value.diag.constraint_name == "threshold_registrations_reference_required_check"

    def test_post_hoc_and_unknown_need_no_reference(self, tenant_conn, probe_workspace) -> None:
        """Their whole content is that the origin is late or unestablished.
        Demanding a citation would invite a fabricated one."""
        with tenant_conn(probe_workspace) as conn:
            _threshold(
                conn, probe_workspace, provenance_status="POST_HOC", provenance_reference=None
            )
            _threshold(
                conn,
                probe_workspace,
                provenance_status="UNKNOWN",
                provenance_reference=None,
                threshold_value="200",
            )

    def test_external_norm_must_identify_the_norm(self, tenant_conn, probe_workspace) -> None:

        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            _threshold(conn, probe_workspace, provenance_status="EXTERNAL_NORM")
        assert exc.value.diag.constraint_name == "threshold_registrations_external_norm_check"

    def test_a_post_hoc_bound_may_not_borrow_an_issuer(self, tenant_conn, probe_workspace) -> None:

        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            _threshold(conn, probe_workspace, provenance_status="POST_HOC", norm_issuer="issuer")
        assert exc.value.diag.constraint_name == "threshold_registrations_norm_fields_scoped_check"

    def test_one_bound_may_hold_two_provenance_registrations(
        self, tenant_conn, probe_workspace
    ) -> None:
        """ADR-037 §3. The same logical threshold registered once as
        PREREGISTERED and once as EXTERNAL_NORM is two provenance facts about
        one proposition, and the key must not merge them."""
        scope = "subject-shared-bound"
        with tenant_conn(probe_workspace) as conn:
            _threshold(
                conn,
                probe_workspace,
                scope_subject_id=scope,
                provenance_status="PREREGISTERED",
            )
            _threshold(
                conn,
                probe_workspace,
                scope_subject_id=scope,
                provenance_status="EXTERNAL_NORM",
                **self._norm_fields("EXTERNAL_NORM"),
            )

    def test_the_same_bound_under_one_status_is_idempotent(
        self, tenant_conn, probe_workspace
    ) -> None:

        with (
            pytest.raises(psycopg.errors.UniqueViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            scope = "subject-repeated"
            _threshold(conn, probe_workspace, scope_subject_id=scope)
            _threshold(conn, probe_workspace, scope_subject_id=scope)
        assert exc.value.diag.constraint_name == "threshold_registrations_identity_key"

    def test_the_bound_is_stored_exactly(self, tenant_conn, probe_workspace) -> None:
        """NUMERIC, not float. A bound compared against an exact decimal must
        not acquire a binary artifact."""
        with tenant_conn(probe_workspace) as conn:
            threshold_id = _threshold(conn, probe_workspace, threshold_value="100.10")
            stored = conn.execute(
                "SELECT threshold_value::text, threshold_operator, recorded_at"
                " FROM research.threshold_registrations WHERE id = %s",
                (threshold_id,),
            ).fetchone()
        assert stored[0] == "100.10"
        assert stored[1] == "GTE"
        assert stored[2] == datetime(2026, 1, 1, tzinfo=UTC)

    def test_the_table_stores_no_proposition_key(self, privileged_conn) -> None:
        """Threshold provenance must never become Claim identity, so there is
        nowhere here to put one."""
        columns = privileged_conn.execute(
            """SELECT column_name FROM information_schema.columns
                WHERE table_schema='research' AND table_name='threshold_registrations'"""
        ).fetchall()
        names = {row[0] for row in columns}
        assert "proposition_key" not in names
        assert "claim_id" not in names
        assert "calibration_eligible" not in names


# ============================================ derivation constraints


class TestDerivationConstraints:
    def test_the_four_results_are_accepted(self, tenant_conn, probe_workspace) -> None:
        with tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            _, revision_id = _claim_revision(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            for index, result in enumerate(
                ("SUPPORTS", "CONTRADICTS", "NOT_APPLICABLE", "UNKNOWN")
            ):
                _derivation(
                    conn,
                    probe_workspace,
                    revision_id,
                    signal_id,
                    derivation_rule_version=f"{index}.0.0",
                    evaluation_result=result,
                    threshold_registration_id=threshold_id,
                )

    def test_neutral_is_not_a_result(self, tenant_conn, probe_workspace) -> None:
        """A NEUTRAL row would assert that an observation bears on the Claim
        without bearing either way, which is a positive finding and a different
        thing from not knowing."""

        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _, revision_id = _claim_revision(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _derivation(
                conn,
                probe_workspace,
                revision_id,
                signal_id,
                evaluation_result="NEUTRAL",
                threshold_registration_id=threshold_id,
            )
        assert exc.value.diag.constraint_name == "claim_derivations_evaluation_result_check"

    def test_deterministic_must_not_carry_a_model_version(
        self, tenant_conn, probe_workspace
    ) -> None:

        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _, revision_id = _claim_revision(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _derivation(
                conn,
                probe_workspace,
                revision_id,
                signal_id,
                model_version="some-model@1",
                threshold_registration_id=threshold_id,
            )
        assert exc.value.diag.constraint_name == "claim_derivations_model_version_pairing_check"

    def test_a_directional_result_must_name_its_threshold(
        self, tenant_conn, probe_workspace
    ) -> None:

        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _, revision_id = _claim_revision(conn, probe_workspace)
            _derivation(conn, probe_workspace, revision_id, signal_id)
        assert exc.value.diag.constraint_name == "claim_derivations_threshold_required_check"

    def test_a_refusal_needs_no_threshold_and_no_evidence(
        self, tenant_conn, probe_workspace
    ) -> None:
        """NOT_APPLICABLE and UNKNOWN stop before the comparison, so they carry
        no threshold -- and they persist with no Evidence row, which is what
        makes a refusal auditable rather than invisible."""
        with tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            _, revision_id = _claim_revision(conn, probe_workspace)
            for index, result in enumerate(("NOT_APPLICABLE", "UNKNOWN")):
                _derivation(
                    conn,
                    probe_workspace,
                    revision_id,
                    signal_id,
                    derivation_rule_version=f"{index}.0.0",
                    evaluation_result=result,
                    rationale="equivalence not established",
                )
            evidence = conn.execute(
                "SELECT count(*) FROM scoring.evidence WHERE workspace_id = %s",
                (probe_workspace,),
            ).fetchone()[0]
        assert evidence == 0

    def test_the_rationale_may_not_be_blank(self, tenant_conn, probe_workspace) -> None:

        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _, revision_id = _claim_revision(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _derivation(
                conn,
                probe_workspace,
                revision_id,
                signal_id,
                rationale="   ",
                threshold_registration_id=threshold_id,
            )
        assert exc.value.diag.constraint_name == "claim_derivations_rationale_present_check"

    def test_the_observed_claim_reference_is_optional(self, tenant_conn, probe_workspace) -> None:
        """The Signal is the load-bearing input, because Evidence attaches
        Signal to Claim. A derivation must not become impossible because no
        source-attributed Claim happens to exist over the same Signal."""
        with tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            claim_id, revision_id = _claim_revision(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _derivation(
                conn,
                probe_workspace,
                revision_id,
                signal_id,
                threshold_registration_id=threshold_id,
            )
            _derivation(
                conn,
                probe_workspace,
                revision_id,
                signal_id,
                derivation_rule_version="2.0.0",
                input_observed_claim_id=claim_id,
                threshold_registration_id=threshold_id,
            )

    def test_a_revision_is_required(self, tenant_conn, probe_workspace) -> None:

        with (
            pytest.raises(psycopg.errors.NotNullViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _derivation(
                conn,
                probe_workspace,
                None,
                signal_id,
                threshold_registration_id=threshold_id,
            )


# ============================================ §19/§20 tenancy


class TestWorkspaceIsolation:
    def test_a_derivation_cannot_cite_a_revision_in_another_workspace(
        self, committing_tenant_conn, probe_workspace, other_workspace
    ) -> None:

        with committing_tenant_conn(other_workspace) as conn:
            _, foreign_revision = _claim_revision(conn, other_workspace)

        with (
            pytest.raises(psycopg.errors.ForeignKeyViolation),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _derivation(
                conn,
                probe_workspace,
                foreign_revision,
                signal_id,
                threshold_registration_id=threshold_id,
            )

    def test_a_tenant_cannot_read_another_workspaces_rows(
        self, committing_tenant_conn, probe_workspace, other_workspace
    ) -> None:
        with committing_tenant_conn(probe_workspace) as conn:
            _threshold(conn, probe_workspace)

        with committing_tenant_conn(other_workspace) as conn:
            visible = conn.execute(
                "SELECT count(*) FROM research.threshold_registrations"
            ).fetchone()[0]
        assert visible == 0

    def test_a_tenant_cannot_write_another_workspaces_rows(
        self, committing_tenant_conn, probe_workspace, other_workspace
    ) -> None:

        with (
            pytest.raises(psycopg.errors.InsufficientPrivilege),
            committing_tenant_conn(other_workspace) as conn,
        ):
            _threshold(conn, probe_workspace)

    def test_both_tables_enforce_row_level_security(self, privileged_conn) -> None:
        rows = privileged_conn.execute(
            """SELECT relname, relrowsecurity, relforcerowsecurity
                 FROM pg_class
                WHERE relname IN ('threshold_registrations', 'claim_derivations')"""
        ).fetchall()
        assert len(rows) == 2
        for _, enabled, forced in rows:
            assert enabled and forced
