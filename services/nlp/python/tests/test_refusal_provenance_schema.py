"""Mission 1.54. The refusal table, against the real database.

ADR-038 said a refusal is not a derivation of a Claim. This file is where that
stops being a sentence: the table is created, and the three properties the whole
design rests on are exercised against real rows rather than inspected as DDL.

    1  a refusal OUTLIVES the execution log that produced it
    2  a Signal it cites cannot be silently purged out from under it
    3  deleting the whole tenant still succeeds

The third is not obvious and Mission 1.51 learned it the hard way: an undeferred
NO ACTION is checked at the end of each CASCADING statement, so a workspace
teardown fails on ordering. Both halves are tested here, because a design that
traded one for the other would pass half a suite.

Every fixture row is SYNTHETIC and lives in a disposable workspace. No count of
live deployment rows is asserted anywhere: CI starts from an empty database, and
Mission 1.53 spent a red build learning that.
"""

from __future__ import annotations

import json
import pathlib
import sys
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sros_claim_model import proposition_key

from .conftest import DATABASE_URL, needs_postgres

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "infrastructure"))
from testing.workspace_guard import disposable  # noqa: E402

psycopg = pytest.importorskip("psycopg")

pytestmark = needs_postgres

# Every SQL string in this file interpolates `TABLE`, the module constant
# naming this suite's own table, and nothing user-supplied reaches one. A
# per-line suppression cannot be used: ruff reports the diagnostic on the
# line that OPENS a multi-line f-string, so the comment lands inside the
# query. One module rule with a stated reason is the honest form.
# ruff: noqa: S608

TABLE = "research.proposition_evaluation_refusals"
RULE = "threshold-state-evaluator"
BASIS = "equivalence-basis-fixture-1"

# The candidate proposition a refusal carries. Same vocabulary as
# `research.claims.proposition_facts`, and the discriminator key is
# `proposition` because that is what all 43 live Claims and the evaluator use.
FACTS = {
    "proposition": "metric_threshold_state",
    "claim_type": "INFERRED",
    "canonical_subject_id": "subject-1",
    "metric_definition_id": "metric-def-1",
    "time_bound": "2024",
    "population_or_geography": "population-1",
    "unit": "unit-1",
    "threshold_operator": "GTE",
    "threshold_value": "100",
}

GATE_ONE = (
    ("SEMANTIC_MISMATCH", "NOT_APPLICABLE"),
    ("EQUIVALENCE_NOT_ESTABLISHED", "UNKNOWN"),
    ("EQUIVALENCE_DIMENSIONS_INCOMPLETE", "UNKNOWN"),
)
POST_GATE_ONE = (
    ("THRESHOLD_REGISTRATION_MISMATCH", "NOT_APPLICABLE"),
    ("UNIT_MISMATCH", "NOT_APPLICABLE"),
    ("TIME_BOUND_MISMATCH", "NOT_APPLICABLE"),
    ("PREREGISTRATION_TIMING_INCONSISTENT", "UNKNOWN"),
)
ALL_PAIRS = GATE_ONE + POST_GATE_ONE


# ---------------------------------------------------------------- fixtures


def _signal(conn, workspace_id: str) -> str:
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
                   'mission-1.54-fixture')""",
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


def _threshold(conn, workspace_id: str) -> str:
    threshold_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO research.threshold_registrations (
               id, workspace_id, threshold_operator, threshold_value, unit,
               metric_definition_id, scope_subject_id, scope_population,
               scope_time_bound, provenance_status, recorded_at, recorded_by,
               provenance_reference)
           VALUES (%s,%s,'GTE','100','unit-1','metric-def-1',%s,'population-1',
                   '2024','PREREGISTERED',%s,'mission-1.54-fixture','fixture')""",
        (threshold_id, workspace_id, f"subject-{uuid.uuid4()}", datetime(2026, 1, 1, tzinfo=UTC)),
    )
    return threshold_id


def _observed_claim(conn, workspace_id: str) -> str:
    """HYPOTHESIS/MANUAL, so the evidence requirement exempts it and a schema
    fixture needs no Evidence row.

    The revision is not optional: `claims_current_revision_fkey` is a composite
    FK from the Claim to the revision it names as current, so a Claim without
    one is refused. Found by writing the helper without it.
    """
    claim_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO research.claims (id, workspace_id, claim_type, temporality, origin)"
        " VALUES (%s,%s,'HYPOTHESIS','EVERGREEN','MANUAL')",
        (claim_id, workspace_id),
    )
    conn.execute(
        "INSERT INTO research.claim_revisions (id, workspace_id, claim_id, revision,"
        " statement, interpretation_confidence) VALUES (%s,%s,%s,1,'fixture',1.0)",
        (str(uuid.uuid4()), workspace_id, claim_id),
    )
    return claim_id


def _refusal(conn, workspace_id: str, signal_id: str, **overrides) -> str:
    facts = overrides.pop("facts", FACTS)
    row = {
        "id": str(uuid.uuid4()),
        "workspace_id": workspace_id,
        "input_signal_id": signal_id,
        "target_proposition_key": proposition_key(facts),
        "target_proposition_facts": json.dumps(facts),
        "derivation_rule_id": RULE,
        "derivation_rule_version": "1.0.0",
        "evaluator_version": "1.0.0",
        "semantic_equivalence_basis_id": BASIS,
        "evaluation_result": "NOT_APPLICABLE",
        "reason_code": "SEMANTIC_MISMATCH",
        "interpretation_kind": "DETERMINISTIC",
        "rationale": "The reviewed basis finds this measures a different quantity.",
    }
    row.update(overrides)
    columns = ", ".join(row)
    placeholders = ", ".join(["%s"] * len(row))
    conn.execute(
        f"INSERT INTO {TABLE} ({columns}) VALUES ({placeholders})",
        tuple(row.values()),
    )
    return row["id"]


# ============================================ §50.1-5 the table, and what it is not


class TestTheTableExists:
    def test_it_exists_after_the_migration(self, privileged_conn):
        assert privileged_conn.execute(f"SELECT to_regclass('{TABLE}')").fetchone()[0] is not None

    def test_every_frozen_column_is_present_with_the_right_nullability(self, privileged_conn):
        rows = privileged_conn.execute(
            """SELECT column_name, is_nullable FROM information_schema.columns
                WHERE table_schema='research' AND table_name='proposition_evaluation_refusals'"""
        ).fetchall()
        nullable = dict(rows)
        expected = {
            "id": "NO",
            "workspace_id": "NO",
            "input_signal_id": "NO",
            "input_observed_claim_id": "YES",
            "target_proposition_key": "NO",
            "target_proposition_facts": "NO",
            "derivation_rule_id": "NO",
            "derivation_rule_version": "NO",
            "evaluator_version": "NO",
            "semantic_equivalence_basis_id": "NO",
            "threshold_registration_id": "YES",
            "evaluation_result": "NO",
            "reason_code": "NO",
            "interpretation_kind": "NO",
            "model_version": "YES",
            "rationale": "NO",
            "created_at": "NO",
        }
        assert nullable == expected

    def test_the_primary_key_is_id(self, privileged_conn):
        definition = privileged_conn.execute(
            f"""SELECT pg_get_constraintdef(oid) FROM pg_constraint
                 WHERE conrelid = '{TABLE}'::regclass AND contype = 'p'"""
        ).fetchone()[0]
        assert definition == "PRIMARY KEY (id)"

    def test_row_level_security_is_enabled_and_forced(self, privileged_conn):
        enabled, forced = privileged_conn.execute(
            f"SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid='{TABLE}'::regclass"
        ).fetchone()
        assert (enabled, forced) == (True, True)

    def test_the_tenant_isolation_policy_exists(self, privileged_conn):
        policies = privileged_conn.execute(
            f"SELECT polname FROM pg_policy WHERE polrelid = '{TABLE}'::regclass"
        ).fetchall()
        assert [row[0] for row in policies] == ["tenant_isolation"]


class TestNoForbiddenBinding:
    """§30, §31 and §20. What the table must NOT be able to say."""

    def test_there_is_no_claim_revision_id(self, privileged_conn):
        columns = self._columns(privileged_conn)
        assert "claim_revision_id" not in columns

    def test_there_is_no_bare_claim_id(self, privileged_conn):
        """`input_observed_claim_id` is an optional INPUT, not the target. A
        column called `claim_id` would read as the Claim this refusal is about,
        and the point of the table is that there is none."""
        assert "claim_id" not in self._columns(privileged_conn)

    def test_there_is_no_evidence_id(self, privileged_conn):
        assert "evidence_id" not in self._columns(privileged_conn)

    def test_there_is_no_descriptor_schema_version(self, privileged_conn):
        """§29 and the operator's accepted deviation: the descriptor follows the
        canonical Claim proposition-facts contract, which carries no version of
        its own, so a refusal-only version namespace must not exist."""
        for column in self._columns(privileged_conn):
            assert "schema_version" not in column
            assert "descriptor_version" not in column

    def test_there_are_no_supersession_columns(self, privileged_conn):
        columns = self._columns(privileged_conn)
        for forbidden in ("superseded_at", "is_current", "replaces_id"):
            assert forbidden not in columns

    def test_no_foreign_key_reaches_an_expiring_run(self, privileged_conn):
        """Structural rather than by column name: even a nullable FK would make
        the dependency available for somebody to rely on later."""
        referenced = {
            row[0]
            for row in privileged_conn.execute(
                f"""SELECT DISTINCT confrelid::regclass::text FROM pg_constraint
                     WHERE conrelid = '{TABLE}'::regclass AND contype = 'f'"""
            ).fetchall()
        }
        assert "research.claim_interpretation_runs" not in referenced
        assert "research.claim_interpretation_inputs" not in referenced
        assert "research.claim_revisions" not in referenced
        assert "scoring.evidence" not in referenced

    @staticmethod
    def _columns(conn) -> set[str]:
        return {
            row[0]
            for row in conn.execute(
                """SELECT column_name FROM information_schema.columns
                    WHERE table_schema='research'
                      AND table_name='proposition_evaluation_refusals'"""
            ).fetchall()
        }


# ============================================ §50.6-13 the vocabularies


class TestTheResultVocabulary:
    @pytest.mark.parametrize(("reason", "result"), ALL_PAIRS)
    def test_every_evaluator_pairing_is_accepted(
        self, tenant_conn, probe_workspace, reason, result
    ):
        with tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            refusal_id = _refusal(
                conn,
                probe_workspace,
                signal_id,
                reason_code=reason,
                evaluation_result=result,
                threshold_registration_id=threshold_id,
            )
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            stored = conn.execute(
                f"SELECT reason_code, evaluation_result FROM {TABLE} WHERE id=%s",
                (refusal_id,),
            ).fetchone()
        assert stored == (reason, result)

    @pytest.mark.parametrize("result", ["SUPPORTS", "CONTRADICTS", "NEUTRAL"])
    def test_a_directional_or_neutral_result_is_refused(self, tenant_conn, probe_workspace, result):
        """The table is structurally incapable of holding an Evidence
        direction, which is what keeps refusals out of aggregation input."""
        with (
            pytest.raises(psycopg.errors.CheckViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, evaluation_result=result)

    @pytest.mark.parametrize("result", ["ERROR", "FAILED", "EXCEPTION", "TIMEOUT"])
    def test_a_system_failure_cannot_be_filed_as_a_refusal(
        self, tenant_conn, probe_workspace, result
    ):
        """§32. An execution failure is not an epistemic finding, and there is
        no generic status column that could quietly acquire one."""
        with (
            pytest.raises(psycopg.errors.CheckViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, evaluation_result=result)

    def test_an_unknown_reason_code_is_refused(self, tenant_conn, probe_workspace):
        with (
            pytest.raises(psycopg.errors.CheckViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, reason_code="VIBES_MISMATCH")

    def test_a_pairing_the_evaluator_can_never_emit_is_refused(self, tenant_conn, probe_workspace):
        """Both halves are individually legal and together they describe a shape
        no gate produces. Constraining the two vocabularies separately would
        admit all fourteen combinations."""
        with (
            pytest.raises(psycopg.errors.CheckViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _refusal(
                conn,
                probe_workspace,
                signal_id,
                reason_code="UNIT_MISMATCH",
                evaluation_result="UNKNOWN",
                threshold_registration_id=threshold_id,
            )

    def test_the_reason_vocabulary_matches_the_evaluator_source(self):
        """§7. The constraint and the evaluator must not drift apart."""
        import ast

        source = (
            pathlib.Path(__file__).resolve().parents[4]
            / "packages/inferred-claim-evaluator/python/sros_inferred_claim_evaluator/threshold_state.py"
        )
        tree = ast.parse(source.read_text(encoding="utf-8"))
        emitted = {
            node.args[1].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_refuse"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
        }
        assert emitted == {reason for reason, _ in ALL_PAIRS}


# ============================================ §50.14-17, 21-22 required and conditional


class TestRequiredColumns:
    @pytest.mark.parametrize(
        "column",
        ["semantic_equivalence_basis_id", "target_proposition_key", "target_proposition_facts"],
    )
    def test_the_column_is_required(self, tenant_conn, probe_workspace, column):
        with (
            pytest.raises(psycopg.errors.NotNullViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, **{column: None})

    def test_every_identity_member_is_not_null(self, privileged_conn):
        """§11 and §15. Probe C in Mission 1.53 proved a UNIQUE containing a
        nullable column stops constraining, so this is what makes the identity
        real rather than nominal."""
        definition = privileged_conn.execute(
            f"""SELECT pg_get_constraintdef(oid) FROM pg_constraint
                 WHERE conrelid = '{TABLE}'::regclass
                   AND conname = 'proposition_evaluation_refusals_identity_key'"""
        ).fetchone()[0]
        members = [
            part.strip()
            for part in definition[definition.index("(") + 1 : definition.rindex(")")].split(",")
        ]
        assert members == [
            "workspace_id",
            "input_signal_id",
            "target_proposition_key",
            "derivation_rule_version",
            "semantic_equivalence_basis_id",
        ]
        nullable = dict(
            privileged_conn.execute(
                """SELECT column_name, is_nullable FROM information_schema.columns
                    WHERE table_schema='research'
                      AND table_name='proposition_evaluation_refusals'"""
            ).fetchall()
        )
        assert all(nullable[member] == "NO" for member in members)

    def test_a_blank_rationale_is_refused(self, tenant_conn, probe_workspace):
        with (
            pytest.raises(psycopg.errors.CheckViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, rationale="   ")


class TestThresholdConditionality:
    @pytest.mark.parametrize(("reason", "result"), GATE_ONE)
    def test_a_gate_one_refusal_may_omit_the_registration(
        self, tenant_conn, probe_workspace, reason, result
    ):
        """Three of the seven refusals return BEFORE the registration is
        consulted, so requiring one would refuse the commonest cases."""
        with tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            refusal_id = _refusal(
                conn,
                probe_workspace,
                signal_id,
                reason_code=reason,
                evaluation_result=result,
                threshold_registration_id=None,
            )
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            stored = conn.execute(
                f"SELECT threshold_registration_id FROM {TABLE} WHERE id=%s",
                (refusal_id,),
            ).fetchone()[0]
        assert stored is None

    @pytest.mark.parametrize(("reason", "result"), GATE_ONE)
    def test_a_gate_one_refusal_may_also_carry_one(
        self, tenant_conn, probe_workspace, reason, result
    ):
        """The evaluator currently passes a registration to every refusal.
        Forbidding it here would mean changing evaluator behaviour to satisfy a
        constraint, and its presence never means gate 1 consulted it."""
        with tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _refusal(
                conn,
                probe_workspace,
                signal_id,
                reason_code=reason,
                evaluation_result=result,
                threshold_registration_id=threshold_id,
            )
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")

    @pytest.mark.parametrize(("reason", "result"), POST_GATE_ONE)
    def test_a_post_gate_one_refusal_must_name_the_registration_it_judged(
        self, tenant_conn, probe_workspace, reason, result
    ):
        with (
            pytest.raises(psycopg.errors.CheckViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(
                conn,
                probe_workspace,
                signal_id,
                reason_code=reason,
                evaluation_result=result,
                threshold_registration_id=None,
            )


# ============================================ §50.18-20 identity and history


class TestIdentityAndHistory:
    def test_an_exact_replay_is_refused(self, committing_tenant_conn, probe_workspace):
        """§14. The same workspace, Signal, target, rule version and basis is one
        evaluation however many times it runs."""
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id)

        with (
            pytest.raises(psycopg.errors.UniqueViolation),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            _refusal(conn, probe_workspace, signal_id)

    def test_a_different_rule_version_is_a_second_historical_row(
        self, committing_tenant_conn, probe_workspace
    ):
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, derivation_rule_version="1.0.0")
            _refusal(conn, probe_workspace, signal_id, derivation_rule_version="2.0.0")
            count = conn.execute(
                f"SELECT count(*) FROM {TABLE} WHERE input_signal_id=%s",
                (signal_id,),
            ).fetchone()[0]
        assert count == 2

    def test_a_different_reviewed_basis_is_a_second_historical_row(
        self, committing_tenant_conn, probe_workspace
    ):
        """§13. The basis is an INPUT to gate 1, so changing it changes what was
        evaluated. The earlier row is not updated."""
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, semantic_equivalence_basis_id="basis-1")
            _refusal(conn, probe_workspace, signal_id, semantic_equivalence_basis_id="basis-2")
            bases = conn.execute(
                f"SELECT semantic_equivalence_basis_id FROM {TABLE} "
                "WHERE input_signal_id=%s ORDER BY semantic_equivalence_basis_id",
                (signal_id,),
            ).fetchall()
        assert [row[0] for row in bases] == ["basis-1", "basis-2"]

    def test_a_different_target_is_a_second_historical_row(
        self, committing_tenant_conn, probe_workspace
    ):
        other = dict(FACTS, threshold_value="200")
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id)
            _refusal(conn, probe_workspace, signal_id, facts=other)
            keys = conn.execute(
                f"SELECT count(DISTINCT target_proposition_key) FROM {TABLE} "
                "WHERE input_signal_id=%s",
                (signal_id,),
            ).fetchone()[0]
        assert keys == 2


# ============================================ §50.23-25 the descriptor


class TestTheDescriptor:
    def test_the_key_recomputes_from_the_stored_facts(
        self, committing_tenant_conn, probe_workspace
    ):
        """§27. The stored key is verifiable rather than trusted.

        The ENFORCEMENT BOUNDARY is named honestly: the database stores both
        halves and does NOT reimplement the Python canonicalisation to check them
        against each other. What this proves is that a JSONB round trip preserves
        the preimage well enough for the key to recompute -- which is the part
        that could have silently failed.
        """
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            refusal_id = _refusal(conn, probe_workspace, signal_id)
            stored_key, stored_facts = conn.execute(
                f"SELECT target_proposition_key, target_proposition_facts FROM {TABLE} WHERE id=%s",
                (refusal_id,),
            ).fetchone()
        assert proposition_key(stored_facts) == stored_key

    def test_key_order_on_the_way_in_does_not_change_the_recomputed_key(
        self, committing_tenant_conn, probe_workspace
    ):
        """§28. JSONB does not preserve key order, and `canonical_json` sorts
        keys anyway, so the two facts cancel rather than compound."""
        reversed_facts = dict(reversed(list(FACTS.items())))
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            refusal_id = _refusal(conn, probe_workspace, signal_id, facts=reversed_facts)
            stored_key, stored_facts = conn.execute(
                f"SELECT target_proposition_key, target_proposition_facts FROM {TABLE} WHERE id=%s",
                (refusal_id,),
            ).fetchone()
        assert proposition_key(stored_facts) == stored_key == proposition_key(FACTS)

    def test_changing_one_load_bearing_fact_changes_the_key(self):
        assert proposition_key(dict(FACTS, threshold_value="200")) != proposition_key(FACTS)

    def test_a_descriptor_without_the_discriminator_is_refused(self, tenant_conn, probe_workspace):
        """Stricter than `research.claims` on purpose: a refusal's facts are the
        ONLY record of what was refused, so the descriptor has to say what kind
        of proposition it describes."""
        without = {k: v for k, v in FACTS.items() if k != "proposition"}
        with (
            pytest.raises(psycopg.errors.CheckViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, facts=without)

    def test_an_empty_descriptor_is_refused(self, tenant_conn, probe_workspace):
        with (
            pytest.raises(psycopg.errors.CheckViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, target_proposition_facts=json.dumps({}))

    def test_a_non_object_descriptor_is_refused(self, tenant_conn, probe_workspace):
        with (
            pytest.raises(psycopg.errors.CheckViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(
                conn, probe_workspace, signal_id, target_proposition_facts=json.dumps(["a", "b"])
            )

    def test_a_blank_key_is_refused(self, tenant_conn, probe_workspace):
        with (
            pytest.raises(psycopg.errors.CheckViolation),
            tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, target_proposition_key="  ")

    def test_an_array_valued_fact_is_accepted(self, committing_tenant_conn, probe_workspace):
        """The constraint deliberately NOT added, checked from the other side.

        Requiring every value to be a string was enforceable and would have made
        this table unable to represent a refusal about the procurement family,
        whose `notice_ids` and `classification_codes` are arrays of strings on 6
        live Claims. Only 37 of 43 would have passed.
        """
        cohort = dict(FACTS, notice_ids=["125972-2023", "126676-2023"])
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            refusal_id = _refusal(conn, probe_workspace, signal_id, facts=cohort)
            stored_key, stored_facts = conn.execute(
                f"SELECT target_proposition_key, target_proposition_facts FROM {TABLE} WHERE id=%s",
                (refusal_id,),
            ).fetchone()
        assert stored_facts["notice_ids"] == ["125972-2023", "126676-2023"]
        assert proposition_key(stored_facts) == stored_key


# ============================================ §50.26-30 tenancy


class TestCrossWorkspaceIsRefused:
    def test_a_refusal_cannot_cite_a_signal_in_another_workspace(
        self, committing_tenant_conn, privileged_conn, probe_workspace, other_workspace
    ):
        foreign_signal = _signal(privileged_conn, other_workspace)
        privileged_conn.commit()
        with (
            pytest.raises(psycopg.errors.ForeignKeyViolation),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            _refusal(conn, probe_workspace, foreign_signal)

    def test_a_refusal_cannot_cite_a_threshold_in_another_workspace(
        self, committing_tenant_conn, privileged_conn, probe_workspace, other_workspace
    ):
        foreign_threshold = _threshold(privileged_conn, other_workspace)
        privileged_conn.commit()
        with (
            pytest.raises(psycopg.errors.ForeignKeyViolation),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(
                conn,
                probe_workspace,
                signal_id,
                reason_code="UNIT_MISMATCH",
                evaluation_result="NOT_APPLICABLE",
                threshold_registration_id=foreign_threshold,
            )

    def test_a_refusal_cannot_cite_an_observed_claim_in_another_workspace(
        self, committing_tenant_conn, privileged_conn, probe_workspace, other_workspace
    ):
        foreign_claim = _observed_claim(privileged_conn, other_workspace)
        privileged_conn.commit()
        with (
            pytest.raises(psycopg.errors.ForeignKeyViolation),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id, input_observed_claim_id=foreign_claim)


class TestRowLevelSecurity:
    def test_a_tenant_cannot_read_another_tenants_refusal(
        self, committing_tenant_conn, probe_workspace, other_workspace
    ):
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            refusal_id = _refusal(conn, probe_workspace, signal_id)

        with committing_tenant_conn(other_workspace) as conn:
            visible = conn.execute(
                f"SELECT count(*) FROM {TABLE} WHERE id = %s",
                (refusal_id,),
            ).fetchone()[0]
        assert visible == 0

    def test_a_tenant_cannot_write_a_row_for_another_tenant(
        self, tenant_conn, privileged_conn, probe_workspace, other_workspace
    ):
        foreign_signal = _signal(privileged_conn, other_workspace)
        privileged_conn.commit()
        with (
            pytest.raises(psycopg.errors.InsufficientPrivilege),
            tenant_conn(probe_workspace) as conn,
        ):
            _refusal(conn, other_workspace, foreign_signal)


# ============================================ §50.31-36 retention and cascade


class TestRetentionIndependence:
    """The load-bearing pair. ADR-038 rejected the interpretation-run logs
    because they expire, and the whole point of a separate durable table is that
    a refusal outlives the run that produced it."""

    def test_a_refusal_survives_deleting_an_interpretation_run(
        self, committing_tenant_conn, probe_workspace
    ):
        run_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            refusal_id = _refusal(conn, probe_workspace, signal_id)
            conn.execute(
                """INSERT INTO research.claim_interpretation_runs (
                       id, workspace_id, interpreter_id, interpreter_version,
                       interpretation_kind, started_at, finished_at, expires_at,
                       correlation_id)
                   VALUES (%s,%s,'fixture','1.0.0','DETERMINISTIC',%s,%s,%s,
                           'mission-1.54-fixture')""",
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
            conn.execute("DELETE FROM research.claim_interpretation_runs WHERE id = %s", (run_id,))

        with committing_tenant_conn(probe_workspace) as conn:
            inputs = conn.execute(
                "SELECT count(*) FROM research.claim_interpretation_inputs WHERE run_id = %s",
                (run_id,),
            ).fetchone()[0]
            survived = conn.execute(
                f"SELECT count(*) FROM {TABLE} WHERE id = %s",
                (refusal_id,),
            ).fetchone()[0]

        assert inputs == 0, "the interpretation inputs should have cascaded away"
        assert survived == 1, (
            "the refusal must outlive the execution log. If this fails, a refusal "
            "again disappears on a retention schedule, which is the defect ADR-038 "
            "exists to prevent"
        )

    def test_a_signal_cited_by_a_refusal_cannot_be_silently_purged(
        self, committing_tenant_conn, probe_workspace
    ):
        """`nlp.signals` carries a populated `expires_at` on every row. NO ACTION
        makes a retention purge FAIL rather than quietly take the audit with it."""
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            _refusal(conn, probe_workspace, signal_id)

        with (
            pytest.raises(psycopg.errors.ForeignKeyViolation),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            conn.execute("DELETE FROM nlp.signals WHERE id = %s", (signal_id,))

    def test_a_threshold_cited_by_a_refusal_cannot_be_silently_purged(
        self, committing_tenant_conn, probe_workspace
    ):
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            threshold_id = _threshold(conn, probe_workspace)
            _refusal(
                conn,
                probe_workspace,
                signal_id,
                reason_code="UNIT_MISMATCH",
                evaluation_result="NOT_APPLICABLE",
                threshold_registration_id=threshold_id,
            )

        with (
            pytest.raises(psycopg.errors.ForeignKeyViolation),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            conn.execute(
                "DELETE FROM research.threshold_registrations WHERE id = %s", (threshold_id,)
            )

    def test_the_provenance_foreign_keys_are_deferrable(self, privileged_conn):
        """Both halves depend on this. Deferred is what lets a workspace cascade
        remove both sides before the check runs, while an isolated purge still
        finds a refusal pointing at its referent."""
        rows = privileged_conn.execute(
            f"""SELECT conname, condeferrable, condeferred FROM pg_constraint
                 WHERE conrelid = '{TABLE}'::regclass AND contype = 'f'
                   AND conname <> 'proposition_evaluation_refusals_workspace_id_fkey'"""
        ).fetchall()
        assert len(rows) == 3
        for name, deferrable, deferred in rows:
            assert deferrable, name
            assert deferred, name

    def test_the_workspace_foreign_key_cascades(self, privileged_conn):
        action = privileged_conn.execute(
            f"""SELECT confdeltype FROM pg_constraint
                 WHERE conrelid = '{TABLE}'::regclass
                   AND conname = 'proposition_evaluation_refusals_workspace_id_fkey'"""
        ).fetchone()[0]
        assert action == "c"


class TestWorkspaceDeletion:
    """§23. Mission 1.51 found that an undeferred NO ACTION fails during tenant
    cascade ordering. This is a REAL workspace, created and deleted here, so the
    guarantee is exercised rather than inferred from DDL."""

    WORKSPACE = "00000000-0000-4000-8000-0000000000cc"

    def test_deleting_a_workspace_removes_its_refusals_and_commits(self):
        disposable(self.WORKSPACE, what="mission-1.54 workspace cascade proof")
        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute(
                "INSERT INTO core.workspaces (id, name, slug) VALUES (%s,%s,%s)"
                " ON CONFLICT (id) DO NOTHING",
                (self.WORKSPACE, "test refusal-cascade", "refusal-cascade"),
            )
            connection.commit()
            try:
                signal_id = _signal(connection, self.WORKSPACE)
                threshold_id = _threshold(connection, self.WORKSPACE)
                claim_id = _observed_claim(connection, self.WORKSPACE)
                refusal_id = _refusal(
                    connection,
                    self.WORKSPACE,
                    signal_id,
                    reason_code="UNIT_MISMATCH",
                    evaluation_result="NOT_APPLICABLE",
                    threshold_registration_id=threshold_id,
                    input_observed_claim_id=claim_id,
                )
                connection.commit()

                present = connection.execute(
                    f"SELECT count(*) FROM {TABLE} WHERE id=%s",
                    (refusal_id,),
                ).fetchone()[0]
                assert present == 1

                # The whole tenant, in one statement, committed. If any
                # provenance FK were undeferred this raises instead.
                connection.execute("DELETE FROM core.workspaces WHERE id = %s", (self.WORKSPACE,))
                connection.commit()

                remaining = connection.execute(
                    f"SELECT count(*) FROM {TABLE} WHERE id=%s",
                    (refusal_id,),
                ).fetchone()[0]
                workspace = connection.execute(
                    "SELECT count(*) FROM core.workspaces WHERE id=%s", (self.WORKSPACE,)
                ).fetchone()[0]
            finally:
                connection.rollback()
                connection.execute("DELETE FROM core.workspaces WHERE id = %s", (self.WORKSPACE,))
                connection.commit()

        assert remaining == 0, "a refusal is tenant-owned data and goes with its workspace"
        assert workspace == 0


# ============================================ §50.37-43 nothing else moved


class TestNothingElseChanged:
    def test_the_evidence_requirement_trigger_is_unchanged(self, privileged_conn):
        definition = privileged_conn.execute(
            """SELECT pg_get_functiondef(p.oid) FROM pg_proc p
                 JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname='research' AND p.proname='require_evidence_for_generated_claim'"""
        ).fetchone()[0]
        assert "HYPOTHESIS" in definition
        assert "MANUAL" in definition
        assert "WITHDRAWN" in definition
        assert "INFERRED" not in definition

    def test_claim_derivations_still_requires_a_revision(self, privileged_conn):
        nullable = privileged_conn.execute(
            """SELECT is_nullable FROM information_schema.columns
                WHERE table_schema='research' AND table_name='claim_derivations'
                  AND column_name='claim_revision_id'"""
        ).fetchone()[0]
        assert nullable == "NO"

    def test_claim_derivations_keeps_its_identity_key(self, privileged_conn):
        definition = privileged_conn.execute(
            """SELECT pg_get_constraintdef(oid) FROM pg_constraint
                 WHERE conrelid='research.claim_derivations'::regclass
                   AND conname='claim_derivations_identity_key'"""
        ).fetchone()[0]
        assert (
            definition
            == "UNIQUE (workspace_id, claim_revision_id, input_signal_id, derivation_rule_version)"
        )

    def test_the_evidence_table_has_no_new_column(self, privileged_conn):
        columns = {
            row[0]
            for row in privileged_conn.execute(
                """SELECT column_name FROM information_schema.columns
                    WHERE table_schema='scoring' AND table_name='evidence'"""
            ).fetchall()
        }
        for forbidden in ("refusal_id", "evaluation_result", "reason_code"):
            assert forbidden not in columns

    def test_the_migration_head_is_the_new_one(self, privileged_conn):
        head = privileged_conn.execute(
            "SELECT max(version) FROM core.schema_migrations"
        ).fetchone()[0]
        assert head == "0035_refusal_provenance"

    def test_an_empty_table_is_a_valid_state(self, privileged_conn):
        """§38. No live count is asserted anywhere in this file; this is the only
        statement about population, and it is the one that holds on an empty CI
        database and on a populated one alike: nothing here backfills."""
        rows = privileged_conn.execute(
            f"SELECT count(*) FROM {TABLE} WHERE workspace_id IN "
            "(SELECT id FROM core.workspaces WHERE slug IN ('dev', 'dev-other'))"
        ).fetchone()[0]
        assert rows == 0, "no production refusal row may exist; this mission creates none"
