"""Mission 1.53. The schema facts ADR-038 rests on, against the real database.

This mission creates nothing. What it does is decide a design, and the design's
whole argument rests on four properties of the deployment as it stands. If any of
them changes, ADR-038 is reasoning about a schema that no longer exists — so each
one is checked here rather than quoted from a report.

    1  an INFERRED Claim with no Evidence is refused, and a HYPOTHESIS one is not
    2  a derivation with a NULL claim_revision_id is refused
    3  a UNIQUE containing a nullable column stops constraining
    4  interpretation runs expire and take their inputs with them

The third is the one that decides Option B, and it is the one a report could most
easily get wrong: it is a property of PostgreSQL's default NULL handling rather
than of anything this repository wrote.

Every fixture row is SYNTHETIC and lives in a disposable probe workspace.
"""

from __future__ import annotations

import json
import uuid

import pytest

from .conftest import needs_postgres

psycopg = pytest.importorskip("psycopg")

pytestmark = needs_postgres

RULE = "threshold-state-evaluator"


def _claim(conn, workspace_id: str, claim_type: str, origin: str) -> str:
    """One synthetic Claim plus its first revision, with NO Evidence."""
    claim_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO research.claims
            (id, workspace_id, claim_type, lifecycle, temporality, origin,
             current_revision, proposition_key, proposition_facts)
        VALUES (%s, %s, %s, 'ACTIVE', 'EVERGREEN', %s, 1, %s, %s)
        """,
        (
            claim_id,
            workspace_id,
            claim_type,
            origin,
            f"mission-1.53-fixture-{claim_id}",
            json.dumps({"proposition": "fixture_threshold_state"}),
        ),
    )
    conn.execute(
        """
        INSERT INTO research.claim_revisions
            (id, workspace_id, claim_id, revision, statement)
        VALUES (%s, %s, %s, 1, 'fixture statement')
        """,
        (str(uuid.uuid4()), workspace_id, claim_id),
    )
    return claim_id


class TestTheEvidenceRequirementStillRefusesInferred:
    """§46.1 and §46.2. The first half of the conflict."""

    def test_an_inferred_claim_with_no_evidence_is_refused(self, tenant_conn, probe_workspace: str):
        """`SET CONSTRAINTS ALL IMMEDIATE` is what makes this a test.

        The trigger is DEFERRABLE INITIALLY DEFERRED, so it fires at COMMIT --
        and this fixture rolls back. Without forcing the check the INSERT simply
        succeeds and the test reports a pass for a rule that never ran.
        """
        with (  # noqa: PT012
            pytest.raises(psycopg.errors.CheckViolation) as raised,
            tenant_conn(probe_workspace) as conn,
        ):
            _claim(conn, probe_workspace, "INFERRED", "DETERMINISTIC_EXTRACTION")
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
        assert "no evidence" in str(raised.value).lower()

    def test_a_hypothesis_claim_with_no_evidence_is_accepted(
        self, tenant_conn, probe_workspace: str
    ):
        """The control. Without it the test above shows only that SOMETHING
        refused, and the first draft of this mission's probe was refused by an
        unrelated `origin` constraint while looking exactly like a pass."""
        with tenant_conn(probe_workspace) as conn:
            claim_id = _claim(conn, probe_workspace, "HYPOTHESIS", "MANUAL")
            # Forced for the same reason, and here it is what stops the control
            # passing vacuously: an unforced deferred check never fires, so an
            # exempt claim and a forbidden one would look identical.
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            row = conn.execute(
                "SELECT claim_type FROM research.claims WHERE id = %s", (claim_id,)
            ).fetchone()
        assert row[0] == "HYPOTHESIS"

    def test_inferred_is_not_in_the_exemption_list(self, privileged_conn):
        """§46.1 read from the live function rather than from the migration
        file, because what refuses an INSERT is the function that is installed."""
        definition = privileged_conn.execute(
            """
            SELECT pg_get_functiondef(p.oid)
            FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'research'
              AND p.proname = 'require_evidence_for_generated_claim'
            """
        ).fetchone()[0]
        assert "HYPOTHESIS" in definition
        assert "MANUAL" in definition
        assert "WITHDRAWN" in definition
        assert "INFERRED" not in definition


class TestTheDerivationStillRequiresARevision:
    """§46.3. The second half of the conflict."""

    def test_a_derivation_with_a_null_revision_is_refused(self, tenant_conn, probe_workspace: str):
        with (  # noqa: PT012
            pytest.raises(psycopg.errors.NotNullViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            conn.execute(
                """
                    INSERT INTO research.claim_derivations
                        (id, workspace_id, claim_revision_id, input_signal_id,
                         derivation_rule_id, derivation_rule_version, evaluator_version,
                         measurement_value, evaluation_result,
                         semantic_equivalence_basis_id, interpretation_kind, rationale)
                    VALUES (%s, %s, NULL, %s, %s, '1.0.0', '1.0.0', 110,
                            'NOT_APPLICABLE', 'basis-fixture', 'DETERMINISTIC', 'fixture')
                    """,
                (str(uuid.uuid4()), probe_workspace, str(uuid.uuid4()), RULE),
            )

    def test_the_column_is_still_not_null(self, privileged_conn):
        nullable = privileged_conn.execute(
            """
            SELECT is_nullable FROM information_schema.columns
            WHERE table_schema = 'research' AND table_name = 'claim_derivations'
              AND column_name = 'claim_revision_id'
            """
        ).fetchone()[0]
        assert nullable == "NO"


class TestANullableColumnStopsAUniqueConstraining:
    """§46.17 and the measurement that decides Option B.

    A temp table mirroring `claim_derivations_identity_key`, so nothing
    canonical is touched and the property is exercised rather than argued.
    """

    IDENTITY = """
        CREATE TEMP TABLE identity_probe (
            workspace_id UUID NOT NULL,
            claim_revision_id UUID,
            input_signal_id UUID NOT NULL,
            derivation_rule_version TEXT NOT NULL,
            UNIQUE (workspace_id, claim_revision_id, input_signal_id, derivation_rule_version)
        ) ON COMMIT DROP
    """

    def test_three_identical_rows_are_admitted_when_the_revision_is_null(
        self, tenant_conn, probe_workspace: str
    ):
        with tenant_conn(probe_workspace) as conn:
            conn.execute(self.IDENTITY)
            signal = str(uuid.uuid4())
            for _ in range(3):
                conn.execute(
                    "INSERT INTO identity_probe VALUES (%s, NULL, %s, '1.0.0')",
                    (probe_workspace, signal),
                )
            count = conn.execute("SELECT count(*) FROM identity_probe").fetchone()[0]
        assert count == 3, (
            "PostgreSQL treats NULLs as distinct, so a nullable claim_revision_id would "
            "remove the table's only idempotency guarantee from exactly the refusal rows "
            "Option B exists to add"
        )

    def test_the_same_key_still_refuses_a_duplicate_when_the_revision_is_present(
        self, tenant_conn, probe_workspace: str
    ):
        """The control that makes the test above mean something: the constraint
        is real, and it is the NULL that switches it off."""
        with (  # noqa: PT012
            pytest.raises(psycopg.errors.UniqueViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            conn.execute(self.IDENTITY)
            signal, revision = str(uuid.uuid4()), str(uuid.uuid4())
            for _ in range(2):
                conn.execute(
                    "INSERT INTO identity_probe VALUES (%s, %s, %s, '1.0.0')",
                    (probe_workspace, revision, signal),
                )

    def test_the_live_identity_key_is_the_one_the_probe_mirrors(self, privileged_conn):
        definition = privileged_conn.execute(
            """
            SELECT pg_get_constraintdef(oid) FROM pg_constraint
            WHERE conrelid = 'research.claim_derivations'::regclass
              AND conname = 'claim_derivations_identity_key'
            """
        ).fetchone()[0]
        assert "claim_revision_id" in definition
        assert "input_signal_id" in definition
        assert "derivation_rule_version" in definition


class TestTheRunLogsStillExpire:
    """§46.4 and §46.6. Option C is refused from live state."""

    def test_an_interpretation_run_can_carry_an_expiry(self, privileged_conn):
        """The SCHEMA property, which holds on an empty database.

        `12 of 12 runs carry an expires_at` is deployment state and lives in the
        mission record, not here: CI starts from an empty database, so a test
        asserting a live count is red for a reason that has nothing to do with
        the code (`testing-strategy.md` §68, and Mission 1.37's rule that an
        artifact measuring a deployment cannot be checked in CI). This version
        first failed in CI for exactly that reason.
        """
        column = privileged_conn.execute(
            """
            SELECT count(*) FROM information_schema.columns
            WHERE table_schema = 'research'
              AND table_name = 'claim_interpretation_runs'
              AND column_name = 'expires_at'
            """
        ).fetchone()[0]
        assert column == 1

    def test_no_run_that_exists_lacks_one(self, privileged_conn):
        """Vacuous on an empty database and load-bearing on a populated one,
        which is the honest split: the row above is the invariant, this is the
        observation."""
        without_expiry = privileged_conn.execute(
            """
            SELECT count(*) FROM research.claim_interpretation_runs
            WHERE expires_at IS NULL
            """
        ).fetchone()[0]
        assert without_expiry == 0

    def test_inputs_cascade_from_their_run(self, privileged_conn):
        cascades = privileged_conn.execute(
            """
            SELECT count(*) FROM pg_constraint
            WHERE conrelid = 'research.claim_interpretation_inputs'::regclass
              AND contype = 'f'
              AND confrelid = 'research.claim_interpretation_runs'::regclass
              AND confdeltype = 'c'
            """
        ).fetchone()[0]
        assert cascades == 1

    def test_a_durable_derivation_references_no_run_table(self, privileged_conn):
        """§46.5. The independence Mission 1.51 built, still standing."""
        references = privileged_conn.execute(
            """
            SELECT count(*) FROM pg_constraint
            WHERE conrelid = 'research.claim_derivations'::regclass
              AND confrelid IN ('research.claim_interpretation_runs'::regclass,
                                'research.claim_interpretation_inputs'::regclass)
            """
        ).fetchone()[0]
        assert references == 0


class TestNothingWasCreated:
    """§46.21 to §46.24."""

    def test_the_table_the_design_named_is_the_one_that_got_built(self, privileged_conn):
        """This asserted the table did NOT exist, which was true of Mission 1.53:
        a design mission that also built its design would have skipped the review
        its STOP condition exists for. Mission 1.54 built it, and a test
        asserting a design is never implemented is not one worth keeping.

        What survives is the link between the two: the table that exists carries
        the exact name ADR-038 froze. A build under a different name would mean
        the design and the schema had drifted apart with nothing noticing.
        """
        present = privileged_conn.execute(
            "SELECT to_regclass('research.proposition_evaluation_refusals') IS NOT NULL"
        ).fetchone()[0]
        assert present is True

    def test_no_inferred_claim_exists(self, privileged_conn):
        count = privileged_conn.execute(
            "SELECT count(*) FROM research.claims WHERE claim_type = 'INFERRED'"
        ).fetchone()[0]
        assert count == 0

    def test_no_derivation_or_threshold_row_exists(self, privileged_conn):
        derivations = privileged_conn.execute(
            "SELECT count(*) FROM research.claim_derivations"
        ).fetchone()[0]
        thresholds = privileged_conn.execute(
            "SELECT count(*) FROM research.threshold_registrations"
        ).fetchone()[0]
        assert (derivations, thresholds) == (0, 0)

    def test_the_migration_this_design_reasons_about_is_still_applied(self, privileged_conn):
        """This pinned the head at 0034, which was true while no migration
        followed. Pinning a HEAD makes every later mission edit this test for no
        epistemic reason; what ADR-038's argument actually depends on is that
        0034 is still in the ledger, because every claim it makes about
        `claim_derivations` reasons about what 0034 created.
        """
        applied = privileged_conn.execute(
            "SELECT count(*) FROM core.schema_migrations WHERE version = %s",
            ("0034_deterministic_derivation_provenance",),
        ).fetchone()[0]
        assert applied == 1
