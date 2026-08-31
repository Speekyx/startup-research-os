"""The reliability assessment schema, against a live database.

Mission 1.14 §38. Every refusal asserts the **exact constraint name**, never
"the insert failed": Mission 1.13 found a CHECK that accepted a half-filled row
because the obvious spelling of "all or none" evaluates to NULL, and a probe
that tolerated any exception would have agreed with it
(`testing-strategy.md` §28).

**No workspace is involved.** `epistemic.reliability_assessments` is global by
ADR-026 Decision 3 — a statement about a published dataset's measurement
contract is not a statement about a tenant — so these tests write global rows
inside transactions that roll back, and a separate test asserts the table
carries no tenant column and no policy.
"""

from __future__ import annotations

import uuid

import pytest

from .conftest import needs_postgres

psycopg = pytest.importorskip("psycopg")

pytestmark = needs_postgres

# A scope key is a sha256; these are syntactically valid and identify nothing.
KEY_A = "a" * 64
KEY_B = "b" * 64


def _assessment(conn, **overrides) -> str:
    assessment_id = str(uuid.uuid4())
    row = {
        "id": assessment_id,
        "assessment_key": KEY_A,
        "version": 1,
        "source_id": "world-bank",
        "resource_id": "indicator/PROBE.ONLY",
        "record_kind_id": "numeric_observation",
        "claim_type": "OBSERVED",
        "proposition_kind": "probe_only_proposition",
        # A PROBE VALUE. Not a judgement about any source: every row written by
        # this module is rolled back, and none is a review.
        "reliability": 0.5,
        "origin": "HUMAN_REVIEW",
        "rationale": "a probe row",
        "stated_limitation": "invented for a constraint probe",
        "reviewed_by": "probe",
        "reviewed_at": "2026-08-31T00:00:00Z",
    }
    row.update(overrides)
    columns = ", ".join(row)
    placeholders = ", ".join(f"%({k})s" for k in row)
    conn.execute(
        f"INSERT INTO epistemic.reliability_assessments ({columns}) "  # noqa: S608
        f"VALUES ({placeholders})",
        row,
    )
    return assessment_id


def _basis(conn, assessment_id: str, **overrides) -> None:
    row = {
        "id": str(uuid.uuid4()),
        "assessment_id": assessment_id,
        "basis_type": "DATASET_METHODOLOGY",
        "document_title": "a probe document",
        "document_url": "https://example.invalid/probe",
        "summarized_finding": "states something",
        "retrieved_at": "2026-08-31T00:00:00Z",
    }
    row.update(overrides)
    columns = ", ".join(row)
    placeholders = ", ".join(f"%({k})s" for k in row)
    conn.execute(
        f"INSERT INTO epistemic.reliability_assessment_basis ({columns}) "  # noqa: S608
        f"VALUES ({placeholders})",
        row,
    )


class TestAcceptance:
    def test_an_assessment_with_a_documented_basis_is_accepted(self, database) -> None:
        with (
            database.privileged_transaction() as conn,
            conn.transaction(force_rollback=True),
        ):
            assessment_id = _assessment(conn)
            _basis(conn, assessment_id)
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            stored = conn.execute(
                "SELECT reliability, origin, superseded_at FROM "
                "epistemic.reliability_assessments WHERE id = %s",
                (assessment_id,),
            ).fetchone()
            assert stored is not None
            assert stored[0] == 0.5
            assert stored[1] == "HUMAN_REVIEW"
            assert stored[2] is None

    def test_two_versions_of_one_scope_coexist_when_the_first_is_superseded(self, database) -> None:
        """§17. An aggregation that used version 1 must still be able to read
        version 1 after version 2 lands."""
        with (
            database.privileged_transaction() as conn,
            conn.transaction(force_rollback=True),
        ):
            first = _assessment(
                conn,
                version=1,
                superseded_at="2026-08-31T01:00:00Z",
                superseded_reason="methodology restated",
            )
            _basis(conn, first)
            second = _assessment(conn, version=2, reliability=0.7)
            _basis(conn, second)
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            rows = conn.execute(
                "SELECT version, reliability FROM epistemic.reliability_assessments "
                "WHERE assessment_key = %s ORDER BY version",
                (KEY_A,),
            ).fetchall()
            assert [(r[0], r[1]) for r in rows] == [(1, 0.5), (2, 0.7)]

    def test_reviewer_reasoning_is_accepted_beside_a_document(self, database) -> None:
        with (
            database.privileged_transaction() as conn,
            conn.transaction(force_rollback=True),
        ):
            assessment_id = _assessment(conn)
            _basis(conn, assessment_id)
            _basis(
                conn,
                assessment_id,
                basis_type="REVIEWER_DOCUMENTED_JUDGEMENT",
                document_url=None,
                retrieved_at=None,
                document_title="reviewer note",
                summarized_finding="reads the revision policy as bounding the value",
            )
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")


class TestRefusals:
    @staticmethod
    def _refused(database, expected: str, **overrides) -> None:
        with database.privileged_transaction() as conn:
            with (
                pytest.raises(psycopg.errors.CheckViolation) as caught,
                conn.transaction(force_rollback=True),
            ):
                assessment_id = _assessment(conn, **overrides)
                _basis(conn, assessment_id)
                conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            assert caught.value.diag.constraint_name == expected

    @pytest.mark.parametrize("value", [-0.1, 1.4])
    def test_reliability_outside_the_unit_interval_is_refused(self, database, value) -> None:
        self._refused(database, "reliability_assessments_unit_interval_check", reliability=value)

    def test_an_unknown_origin_is_refused(self, database) -> None:
        """There is no MODEL_GUESSED, and the closed list is what makes that
        enforceable rather than merely stated."""
        self._refused(database, "reliability_assessments_origin_check", origin="MODEL_GUESSED")

    def test_human_review_may_not_claim_a_calibration_dataset(self, database) -> None:
        """§22. However careful a reviewer was, they fitted nothing to data."""
        self._refused(
            database,
            "reliability_assessments_calibration_ref_check",
            calibration_dataset_ref="labelled-outcomes-v1",
        )

    def test_calibrated_empirically_without_a_dataset_is_refused(self, database) -> None:
        self._refused(
            database,
            "reliability_assessments_calibration_ref_check",
            origin="CALIBRATED_EMPIRICALLY",
        )

    def test_a_blank_rationale_or_limitation_is_refused(self, database) -> None:
        """A reliability with no stated limitation is a number nobody can
        argue with."""
        self._refused(database, "reliability_assessments_rationale_check", rationale="   ")
        self._refused(database, "reliability_assessments_rationale_check", stated_limitation="   ")

    def test_an_unattributed_assessment_is_refused(self, database) -> None:
        self._refused(
            database, "reliability_assessments_reviewer_identified_check", reviewed_by="  "
        )

    def test_a_scope_missing_a_part_is_refused(self, database) -> None:
        self._refused(
            database, "reliability_assessments_scope_identified_check", proposition_kind="  "
        )

    def test_half_a_supersession_is_refused(self, database) -> None:
        """Written with `num_nonnulls` because the obvious spelling returns NULL
        on a half-filled row, and a CHECK accepts NULL (migration 0017)."""
        self._refused(
            database,
            "reliability_assessments_supersession_complete_check",
            superseded_at="2026-08-31T01:00:00Z",
        )
        self._refused(
            database,
            "reliability_assessments_supersession_complete_check",
            superseded_reason="withdrawn",
        )

    def test_an_unknown_claim_type_is_refused(self, database) -> None:
        self._refused(database, "reliability_assessments_claim_type_check", claim_type="SPECULATED")

    def test_a_malformed_scope_key_is_refused(self, database) -> None:
        self._refused(
            database, "reliability_assessments_key_shape_check", assessment_key="not-a-hash"
        )

    def test_two_current_assessments_for_one_scope_are_refused(self, database) -> None:
        """§18's ambiguous case, made unreachable through the ordinary path. The
        resolver refuses it anyway, because a guard that trusts another guard is
        one schema change away from trusting nothing."""
        with database.privileged_transaction() as conn:
            with (
                pytest.raises(psycopg.errors.UniqueViolation) as caught,
                conn.transaction(force_rollback=True),
            ):
                first = _assessment(conn, version=1)
                _basis(conn, first)
                second = _assessment(conn, version=2)
                _basis(conn, second)
                conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            assert caught.value.diag.constraint_name == "idx_reliability_assessments_current"

    def test_an_assessment_with_no_documented_basis_is_refused_at_commit(self, database) -> None:
        """The deferred trigger. It fires at COMMIT, so an assessment and its
        basis rows land in one transaction and neither has to exist first."""
        with database.privileged_transaction() as conn:
            with (
                pytest.raises(psycopg.Error) as caught,
                conn.transaction(force_rollback=True),
            ):
                _assessment(conn)
                conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            # A trigger's RAISE carries no constraint NAME, only the SQLSTATE.
            assert caught.value.sqlstate == "23514"
            assert "document-backed basis" in str(caught.value)

    def test_reviewer_reasoning_alone_is_refused_at_commit(self, database) -> None:
        """ "The publisher is reputable" is an opinion with a citation field."""
        with database.privileged_transaction() as conn:
            with (
                pytest.raises(psycopg.Error) as caught,
                conn.transaction(force_rollback=True),
            ):
                assessment_id = _assessment(conn)
                _basis(
                    conn,
                    assessment_id,
                    basis_type="REVIEWER_DOCUMENTED_JUDGEMENT",
                    document_url=None,
                    retrieved_at=None,
                    summarized_finding="the publisher is reputable",
                )
                conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            assert caught.value.sqlstate == "23514"

    def test_a_document_backed_basis_must_name_a_retrieved_document(self, database) -> None:
        with database.privileged_transaction() as conn:
            with (
                pytest.raises(psycopg.errors.CheckViolation) as caught,
                conn.transaction(force_rollback=True),
            ):
                assessment_id = _assessment(conn)
                _basis(conn, assessment_id, document_url=None)
            assert (
                caught.value.diag.constraint_name == "reliability_assessment_basis_document_check"
            )

    def test_a_long_excerpt_is_refused(self, database) -> None:
        """A long excerpt is a copy of third-party text, not a reference — the
        same 1000-character cap `registry.source_policy_evidence` uses."""
        with database.privileged_transaction() as conn:
            with (
                pytest.raises(psycopg.errors.CheckViolation) as caught,
                conn.transaction(force_rollback=True),
            ):
                assessment_id = _assessment(conn)
                _basis(conn, assessment_id, excerpt="x" * 1001)
            assert (
                caught.value.diag.constraint_name
                == "reliability_assessment_basis_excerpt_length_check"
            )

    def test_an_assessment_for_an_unregistered_source_is_refused(self, database) -> None:
        with database.privileged_transaction() as conn:
            with (
                pytest.raises(psycopg.errors.ForeignKeyViolation) as caught,
                conn.transaction(force_rollback=True),
            ):
                _assessment(conn, source_id="a-source-nobody-registered")
            assert caught.value.diag.constraint_name == "reliability_assessments_source_id_fkey"

    def test_an_unregistered_record_kind_is_refused(self, database) -> None:
        with database.privileged_transaction() as conn:
            with (
                pytest.raises(psycopg.errors.ForeignKeyViolation) as caught,
                conn.transaction(force_rollback=True),
            ):
                _assessment(conn, record_kind_id="a_kind_nobody_registered")
            assert caught.value.diag.constraint_name == "reliability_assessments_record_kind_fkey"


class TestScopeAndTenancy:
    def test_the_table_is_global_and_carries_no_tenant_column(self, database) -> None:
        """ADR-026 Decision 3. No workspace_id means no tenant leakage path,
        which is a stronger property than a correctly written policy."""
        with database.privileged_transaction() as conn:
            columns = {
                row[0]
                for row in conn.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='epistemic'"
                )
            }
        assert "workspace_id" not in columns

    def test_no_row_level_security_policy_exists_on_the_schema(self, database) -> None:
        """A tenant policy on a global table is worse than none: it makes the
        schema look uniformly protected while the rows nobody can reach are the
        shared judgements every workspace needs."""
        with database.privileged_transaction() as conn:
            policies = conn.execute(
                "SELECT count(*) FROM pg_policies WHERE schemaname = 'epistemic'"
            ).fetchone()
        assert policies is not None and policies[0] == 0

    def test_the_runtime_role_may_read_and_not_write(self, database) -> None:
        """Assessments are administered through a review path, never by a
        service. A system that can write its own reliability can approve
        itself."""
        with database.privileged_transaction() as conn:
            grants = {
                (row[0], row[1])
                for row in conn.execute(
                    "SELECT table_name, privilege_type FROM "
                    "information_schema.role_table_grants "
                    "WHERE table_schema='epistemic' AND grantee='sros_app'"
                )
            }
        assert ("reliability_assessments", "SELECT") in grants
        for forbidden in ("INSERT", "UPDATE", "DELETE"):
            assert ("reliability_assessments", forbidden) not in grants
            assert ("reliability_assessment_basis", forbidden) not in grants

    def test_no_assessment_exists_in_production(self, database) -> None:
        """Mission 1.14 produced the machinery and no review. Seven Evidence
        rows stay NON_SCORABLE, which is the design working rather than a
        shortfall in it (§23, outcome B)."""
        with database.privileged_transaction() as conn:
            count = conn.execute(
                "SELECT count(*) FROM epistemic.reliability_assessments"
            ).fetchone()
        assert count is not None and count[0] == 0
