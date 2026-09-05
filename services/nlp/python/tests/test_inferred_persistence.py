"""Mission 1.55. The two persistence paths, against the real database.

Everything here runs through the REAL `persist_evaluation_outcome` over REAL
`EvaluationOutcome` objects produced by the REAL evaluator. Nothing is
hand-rolled: an orchestration test that constructed its own outcome would prove
the test's understanding of the contract rather than the code's.

The load-bearing tests are the atomicity ones. The evidence requirement is a
DEFERRED trigger, so a directional transaction that never commits proves
nothing -- each rollback test injects a failure at a named point and then
re-reads through a SEPARATE connection, because a read inside the aborted
transaction would see its own uncommitted work.

Every fixture row is SYNTHETIC and lives in a disposable workspace. No canonical
research row is read or written.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sros_claim_model import proposition_key
from sros_inferred_claim_evaluator import (
    ALL_EQUIVALENCE_DIMENSIONS,
    EquivalenceVerdict,
    EvaluationResult,
    MeasurementWitness,
    SemanticEquivalenceDecision,
    TargetProposition,
    ThresholdOperator,
    ThresholdProvenanceStatus,
    ThresholdRegistration,
    evaluate,
    target_proposition_facts,
)
from sros_nlp.inferred_persistence import (
    PersistenceError,
    PersistencePath,
    PersistenceStatus,
    claim_statement,
    persist_evaluation_outcome,
)

from .conftest import needs_postgres

psycopg = pytest.importorskip("psycopg")

pytestmark = needs_postgres

RETRIEVED = datetime(2026, 6, 1, tzinfo=UTC)
FROZEN = datetime(2026, 1, 1, tzinfo=UTC)
BASIS = "equivalence-basis-mission-1.55"


# ------------------------------------------------------------------ fixtures


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
                   'mission-1.55-fixture')""",
        (
            signal_id,
            workspace_id,
            now,
            now + timedelta(days=365),
            json.dumps({"fixture": True}),
            f"pf-{signal_id}",
            f"df-{signal_id}",
            json.dumps({"source_ids": ["world-bank"]}),
            json.dumps({"basis": "NONE", "resolution": "DAY", "period_labels": []}),
        ),
    )
    return signal_id


def _threshold_row(conn, workspace_id: str, threshold_id: str, subject: str) -> None:
    conn.execute(
        """INSERT INTO research.threshold_registrations (
               id, workspace_id, threshold_operator, threshold_value, unit,
               metric_definition_id, scope_subject_id, scope_population,
               scope_time_bound, provenance_status, recorded_at, recorded_by,
               provenance_reference)
           VALUES (%s,%s,'GTE','100','unit-1','metric-def-1',%s,'population-1',
                   '2024','PREREGISTERED',%s,'mission-1.55-fixture','fixture')""",
        (threshold_id, workspace_id, subject, FROZEN),
    )


def target(**overrides) -> TargetProposition:
    fields = {
        "proposition_kind": "metric_threshold_state",
        "canonical_subject_id": "subject-1",
        "metric_definition_id": "metric-def-1",
        "time_bound": "2024",
        "population_or_geography": "population-1",
        "unit": "unit-1",
        "threshold_operator": ThresholdOperator.GTE,
        "threshold_value": Decimal("100"),
    }
    fields.update(overrides)
    return TargetProposition(**fields)


def registration(workspace_id: str, threshold_id: str, **overrides) -> ThresholdRegistration:
    fields = {
        "registration_id": threshold_id,
        "workspace_id": workspace_id,
        "metric_definition_id": "metric-def-1",
        "scope_subject_id": "subject-1",
        "scope_population": "population-1",
        "scope_time_bound": "2024",
        "unit": "unit-1",
        "threshold_operator": ThresholdOperator.GTE,
        "threshold_value": Decimal("100"),
        "provenance_status": ThresholdProvenanceStatus.PREREGISTERED,
        "recorded_at": FROZEN,
        "recorded_by": "fixture",
        "provenance_reference": "fixture-registration",
    }
    fields.update(overrides)
    return ThresholdRegistration(**fields)


def witness(workspace_id: str, signal_id: str, value: str = "110", **overrides):
    fields = {
        "workspace_id": workspace_id,
        "signal_id": signal_id,
        # A REGISTERED source id, because `scoring.evidence.source_id` carries a
        # foreign key into `registry.sources`. Nothing about this fixture uses
        # World Bank data -- the row is synthetic -- but Evidence may not name a
        # publisher the registry has never heard of, which is the constraint
        # working.
        "source_id": "world-bank",
        "resource_id": "resource-a",
        "record_kind_id": "numeric_observation",
        "canonical_subject_id": "subject-1",
        "source_native_metric_id": "NATIVE.M",
        "metric_definition_id": "metric-def-1",
        "measurement_value": Decimal(value),
        "unit": "unit-1",
        "time_bound": "2024",
        "population_or_geography": "population-1",
        "retrieved_at": RETRIEVED,
    }
    fields.update(overrides)
    return MeasurementWitness(**fields)


def equivalence(verdict=EquivalenceVerdict.EQUIVALENT, basis_id: str = BASIS):
    return SemanticEquivalenceDecision(
        basis_id=basis_id,
        verdict=verdict,
        dimensions_checked=frozenset(ALL_EQUIVALENCE_DIMENSIONS)
        if verdict is EquivalenceVerdict.EQUIVALENT
        else frozenset(),
        reviewed_by="mission-1.55-fixture",
        reviewed_at=FROZEN,
        interpretation_confidence=0.8 if verdict is EquivalenceVerdict.EQUIVALENT else None,
    )


class Scenario:
    """One evaluated outcome, with its fixture rows already written."""

    def __init__(
        self, conn, workspace_id: str, *, value="110", verdict=None, unit=None, basis=BASIS
    ):
        self.workspace_id = workspace_id
        self.signal_id = _signal(conn, workspace_id)
        self.threshold_id = str(uuid.uuid4())
        _threshold_row(conn, workspace_id, self.threshold_id, f"subject-{uuid.uuid4()}")
        self.target = target()
        witness_kwargs = {} if unit is None else {"unit": unit}
        self.outcome = evaluate(
            witness(workspace_id, self.signal_id, value, **witness_kwargs),
            self.target,
            registration(workspace_id, self.threshold_id),
            equivalence(verdict or EquivalenceVerdict.EQUIVALENT, basis),
        )


def counts(conn, workspace_id: str) -> dict[str, int]:
    tables = {
        "claims": "research.claims",
        "revisions": "research.claim_revisions",
        "evidence": "scoring.evidence",
        "derivations": "research.claim_derivations",
        "refusals": "research.proposition_evaluation_refusals",
        "thresholds": "research.threshold_registrations",
    }
    return {
        name: conn.execute(
            f"SELECT count(*) FROM {table} WHERE workspace_id = %s",  # noqa: S608
            (workspace_id,),
        ).fetchone()[0]
        for name, table in tables.items()
    }


# ============================================ §70.1-7 routing


class TestRouting:
    def test_supports_routes_directional(self, committing_tenant_conn, probe_workspace):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace)
            assert scenario.outcome.result is EvaluationResult.SUPPORTS
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
        assert result.path is PersistencePath.DIRECTIONAL

    def test_contradicts_routes_directional(self, committing_tenant_conn, probe_workspace):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, value="90")
            assert scenario.outcome.result is EvaluationResult.CONTRADICTS
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
        assert result.path is PersistencePath.DIRECTIONAL

    def test_not_applicable_routes_refusal(self, committing_tenant_conn, probe_workspace):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, unit="unit-2")
            assert scenario.outcome.result is EvaluationResult.NOT_APPLICABLE
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
        assert result.path is PersistencePath.REFUSAL

    def test_unknown_routes_refusal(self, committing_tenant_conn, probe_workspace):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, verdict=EquivalenceVerdict.UNKNOWN)
            assert scenario.outcome.result is EvaluationResult.UNKNOWN
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
        assert result.path is PersistencePath.REFUSAL

    def test_there_are_exactly_two_paths(self):
        assert {member.value for member in PersistencePath} == {"DIRECTIONAL", "REFUSAL"}

    def test_neutral_is_not_an_evaluation_result_at_all(self):
        """So there is nothing to route. The guarantee is producer-side, and this
        records where it lives rather than pretending a branch refuses it."""
        assert "NEUTRAL" not in {member.value for member in EvaluationResult}

    def test_a_mismatched_target_is_refused_before_any_write(
        self, committing_tenant_conn, probe_workspace
    ):
        with (
            pytest.raises(PersistenceError, match="TARGET_MISMATCH"),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            scenario = Scenario(conn, probe_workspace)
            persist_evaluation_outcome(
                conn, scenario.outcome, target(threshold_value=Decimal("200"))
            )


# ============================================ §70.8-12 the directional path


class TestDirectionalPersistence:
    def test_one_claim_one_revision_one_derivation_one_evidence(
        self, committing_tenant_conn, probe_workspace
    ):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace)
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)

        with committing_tenant_conn(probe_workspace) as conn:
            after = counts(conn, probe_workspace)
            claim_type = conn.execute(
                "SELECT claim_type, interpretation_kind, model_version FROM research.claims "
                "WHERE id = %s",
                (result.claim_id,),
            ).fetchone()

        assert (after["claims"], after["revisions"]) == (1, 1)
        assert (after["derivations"], after["evidence"]) == (1, 1)
        assert after["refusals"] == 0
        assert claim_type == ("INFERRED", "DETERMINISTIC", None)
        assert result.status is PersistenceStatus.PERSISTED

    def test_the_claim_key_equals_the_evaluator_target_key(
        self, committing_tenant_conn, probe_workspace
    ):
        """§53. Both branches tie back to one semantic target."""
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace)
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            stored = conn.execute(
                "SELECT proposition_key FROM research.claims WHERE id = %s", (result.claim_id,)
            ).fetchone()[0]
        assert stored == proposition_key(target_proposition_facts(scenario.target))
        assert stored == scenario.outcome.proposition_key

    def test_the_derivation_binds_to_the_current_revision(
        self, committing_tenant_conn, probe_workspace
    ):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace)
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            bound = conn.execute(
                "SELECT claim_revision_id FROM research.claim_derivations WHERE id = %s",
                (result.derivation_id,),
            ).fetchone()[0]
            current = conn.execute(
                """SELECT r.id FROM research.claim_revisions r
                     JOIN research.claims c ON c.id = r.claim_id
                      AND c.current_revision = r.revision
                    WHERE c.id = %s""",
                (result.claim_id,),
            ).fetchone()[0]
        assert str(bound) == str(current) == result.claim_revision_id

    def test_a_post_hoc_threshold_still_persists_a_directional_result(
        self, committing_tenant_conn, probe_workspace
    ):
        """§70.34. Provenance changes calibration eligibility, never entailment."""
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            threshold_id = str(uuid.uuid4())
            _threshold_row(conn, probe_workspace, threshold_id, f"subject-{uuid.uuid4()}")
            outcome = evaluate(
                witness(probe_workspace, signal_id),
                target(),
                registration(
                    probe_workspace,
                    threshold_id,
                    provenance_status=ThresholdProvenanceStatus.POST_HOC,
                    provenance_reference=None,
                ),
                equivalence(),
            )
            assert outcome.result is EvaluationResult.SUPPORTS
            assert outcome.calibration_eligible is False
            result = persist_evaluation_outcome(conn, outcome, target())
        assert result.status is PersistenceStatus.PERSISTED

    def test_the_statement_names_no_source_and_no_measurement(self):
        """The property §9 and §10 depend on: two witnesses of one proposition
        must word it identically, or every extra Signal looks like a revision."""
        statement = claim_statement(target())
        for forbidden in ("110", "105", "fixture-source", "SUPPORTS", "signal"):
            assert forbidden not in statement


# ============================================ §70.13-20 the refusal path


class TestRefusalPersistence:
    def test_a_refusal_writes_one_row_and_nothing_else(
        self, committing_tenant_conn, probe_workspace
    ):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, unit="unit-2")
            before = counts(conn, probe_workspace)
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)

        with committing_tenant_conn(probe_workspace) as conn:
            after = counts(conn, probe_workspace)

        assert result.path is PersistencePath.REFUSAL
        assert after["refusals"] == before["refusals"] + 1
        assert after["claims"] == before["claims"] == 0
        assert after["revisions"] == before["revisions"] == 0
        assert after["evidence"] == before["evidence"] == 0
        assert after["derivations"] == before["derivations"] == 0
        assert after["thresholds"] == before["thresholds"]

    def test_the_refusal_carries_the_evaluator_reason_code(
        self, committing_tenant_conn, probe_workspace
    ):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, unit="unit-2")
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            row = conn.execute(
                "SELECT evaluation_result, reason_code FROM "
                "research.proposition_evaluation_refusals WHERE id = %s",
                (result.refusal_id,),
            ).fetchone()
        assert row == ("NOT_APPLICABLE", "UNIT_MISMATCH")
        assert scenario.outcome.refusal_reason == "UNIT_MISMATCH"

    def test_the_stored_key_recomputes_from_the_stored_facts(
        self, committing_tenant_conn, probe_workspace
    ):
        """§52. The database stores both halves and checks neither against the
        other, so the producer is the only place this can be verified."""
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, unit="unit-2")
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            key, facts = conn.execute(
                "SELECT target_proposition_key, target_proposition_facts FROM "
                "research.proposition_evaluation_refusals WHERE id = %s",
                (result.refusal_id,),
            ).fetchone()
        assert proposition_key(facts) == key

    def test_a_replayed_refusal_is_idempotent(self, committing_tenant_conn, probe_workspace):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, unit="unit-2")
            first = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)

        with committing_tenant_conn(probe_workspace) as conn:
            second = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            after = counts(conn, probe_workspace)

        assert first.refusal_created is True
        assert second.refusal_created is False
        assert second.status is PersistenceStatus.REUSED
        assert second.refusal_id == first.refusal_id
        assert after["refusals"] == 1

    def test_the_same_identity_with_a_different_result_is_a_conflict(
        self, committing_tenant_conn, probe_workspace
    ):
        """§51. Same unique key plus a different payload is not a replay.

        The unit mismatch and the time-bound mismatch share every identity
        column and differ on the reason code, which is exactly the case a
        swallowed unique violation would have hidden.
        """
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, unit="unit-2")
            persist_evaluation_outcome(conn, scenario.outcome, scenario.target)

        with committing_tenant_conn(probe_workspace) as conn:
            divergent = evaluate(
                witness(probe_workspace, scenario.signal_id, time_bound="2025"),
                scenario.target,
                registration(probe_workspace, scenario.threshold_id),
                equivalence(),
            )
            assert divergent.refusal_reason == "TIME_BOUND_MISMATCH"
            with pytest.raises(PersistenceError, match="REFUSAL_IDEMPOTENCY_CONFLICT"):
                persist_evaluation_outcome(conn, divergent, scenario.target)

    def test_a_refusal_does_not_mutate_its_threshold_registration(
        self, committing_tenant_conn, probe_workspace
    ):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, unit="unit-2")
            before = conn.execute(
                "SELECT provenance_status, threshold_value, recorded_at FROM "
                "research.threshold_registrations WHERE id = %s",
                (scenario.threshold_id,),
            ).fetchone()
            persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            after = conn.execute(
                "SELECT provenance_status, threshold_value, recorded_at FROM "
                "research.threshold_registrations WHERE id = %s",
                (scenario.threshold_id,),
            ).fetchone()
        assert before == after


# ============================================ §70.21-30 replay and Policy D


class TestReplayAndPolicyD:
    def test_an_identical_directional_replay_creates_nothing(
        self, committing_tenant_conn, probe_workspace
    ):
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace)
            first = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)

        with committing_tenant_conn(probe_workspace) as conn:
            second = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            after = counts(conn, probe_workspace)

        assert second.claim_id == first.claim_id
        assert second.claim_revision_id == first.claim_revision_id
        assert second.derivation_id == first.derivation_id
        assert second.evidence_id == first.evidence_id
        assert (second.claim_created, second.derivation_created) == (False, False)
        assert second.status is PersistenceStatus.REUSED
        assert (after["claims"], after["revisions"]) == (1, 1)
        assert (after["derivations"], after["evidence"]) == (1, 1)

    def test_two_supporting_witnesses_reach_one_claim_and_one_revision(
        self, committing_tenant_conn, probe_workspace
    ):
        """§10 and §43. The point of ADR-036, and the reason the statement may
        not name the witness."""
        with committing_tenant_conn(probe_workspace) as conn:
            first = Scenario(conn, probe_workspace, value="110")
            persist_evaluation_outcome(conn, first.outcome, first.target)
            second = Scenario(conn, probe_workspace, value="105")
            persist_evaluation_outcome(conn, second.outcome, second.target)
            after = counts(conn, probe_workspace)

        assert after["claims"] == 1, "two witnesses of one proposition are one Claim"
        assert after["revisions"] == 1, "a second witness is not a reformulation"
        assert after["evidence"] == 2
        assert after["derivations"] == 2

    def test_a_support_and_a_contradiction_reach_one_claim(
        self, committing_tenant_conn, probe_workspace
    ):
        """§42. The shape the aggregator has never seen on real data."""
        with committing_tenant_conn(probe_workspace) as conn:
            supporting = Scenario(conn, probe_workspace, value="110")
            persist_evaluation_outcome(conn, supporting.outcome, supporting.target)
            contradicting = Scenario(conn, probe_workspace, value="90")
            persist_evaluation_outcome(conn, contradicting.outcome, contradicting.target)
            after = counts(conn, probe_workspace)
            directions = conn.execute(
                "SELECT direction FROM scoring.evidence WHERE workspace_id = %s ORDER BY direction",
                (probe_workspace,),
            ).fetchall()

        assert after["claims"] == 1
        assert after["revisions"] == 1
        assert [row[0] for row in directions] == ["CONTRADICTS", "SUPPORTS"]
        assert after["derivations"] == 2

    def test_a_rule_bump_in_the_same_direction_adds_only_a_derivation(
        self, committing_tenant_conn, probe_workspace
    ):
        """§49. The critical invariant: procedure versioning belongs to the
        derivation, and epistemic identity belongs to the Evidence."""
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace)
            persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            bumped = _rule_bump(scenario.outcome, "2.0.0")
            result = persist_evaluation_outcome(conn, bumped, scenario.target)
            after = counts(conn, probe_workspace)

        assert result.derivation_created is True
        assert result.evidence_created is False
        assert (after["claims"], after["revisions"], after["evidence"]) == (1, 1, 1)
        assert after["derivations"] == 2

    def test_a_rule_bump_reversing_direction_requires_review(
        self, committing_tenant_conn, probe_workspace
    ):
        """§50 and Policy D. The Evidence is neither updated nor duplicated."""
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, value="110")
            first = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)

        with committing_tenant_conn(probe_workspace) as conn:
            reversed_outcome = _rule_bump(
                evaluate(
                    witness(probe_workspace, scenario.signal_id, "90"),
                    scenario.target,
                    registration(probe_workspace, scenario.threshold_id),
                    equivalence(),
                ),
                "2.0.0",
            )
            assert reversed_outcome.result is EvaluationResult.CONTRADICTS
            result = persist_evaluation_outcome(conn, reversed_outcome, scenario.target)
            after = counts(conn, probe_workspace)
            directions = conn.execute(
                "SELECT direction FROM scoring.evidence WHERE workspace_id = %s",
                (probe_workspace,),
            ).fetchall()

        assert result.status is PersistenceStatus.REVIEW_REQUIRED
        assert result.conflict is not None
        assert result.conflict.existing_direction == "SUPPORTS"
        assert result.conflict.evaluated_direction == "CONTRADICTS"
        assert result.conflict.reason == "EVIDENCE_DIRECTION_CONFLICT"
        assert after["evidence"] == 1, "Policy D never duplicates Evidence"
        assert [row[0] for row in directions] == ["SUPPORTS"], (
            "Policy D never updates a standing direction"
        )
        assert after["derivations"] == 2, (
            "the disagreeing derivation IS recorded: refusing to store it would lose "
            "the finding the reviewer is being asked about"
        )
        assert result.evidence_id == first.evidence_id

    def test_the_conflict_is_reconstructible_from_durable_rows(
        self, committing_tenant_conn, probe_workspace
    ):
        """The half that matters for an unattended pilot: after the command
        returns, can the disagreement still be found without the result object?"""
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, value="110")
            persist_evaluation_outcome(conn, scenario.outcome, scenario.target)

        with committing_tenant_conn(probe_workspace) as conn:
            persist_evaluation_outcome(
                conn,
                _rule_bump(
                    evaluate(
                        witness(probe_workspace, scenario.signal_id, "90"),
                        scenario.target,
                        registration(probe_workspace, scenario.threshold_id),
                        equivalence(),
                    ),
                    "2.0.0",
                ),
                scenario.target,
            )

        with committing_tenant_conn(probe_workspace) as conn:
            disagreeing = conn.execute(
                """SELECT count(*)
                     FROM research.claim_derivations d
                     JOIN research.claim_revisions r
                       ON r.workspace_id = d.workspace_id AND r.id = d.claim_revision_id
                     JOIN scoring.evidence e
                       ON e.workspace_id = d.workspace_id AND e.claim_id = r.claim_id
                      AND e.signal_id = d.input_signal_id
                    WHERE d.workspace_id = %s AND d.evaluation_result <> e.direction""",
                (probe_workspace,),
            ).fetchone()[0]
        assert disagreeing == 1, (
            "the conflict is durably DETECTABLE by an exact join. What no row says is "
            "that a human should look at it, which is the gap this mission reports"
        )

    def test_a_derivation_replay_with_a_different_result_is_a_conflict(
        self, committing_tenant_conn, probe_workspace
    ):
        """§23 and §29. Same identity, different conclusion, same rule version."""
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace, value="110")
            persist_evaluation_outcome(conn, scenario.outcome, scenario.target)

        with committing_tenant_conn(probe_workspace) as conn:
            divergent = evaluate(
                witness(probe_workspace, scenario.signal_id, "90"),
                scenario.target,
                registration(probe_workspace, scenario.threshold_id),
                equivalence(),
            )
            with pytest.raises(PersistenceError, match="DERIVATION_IDEMPOTENCY_CONFLICT"):
                persist_evaluation_outcome(conn, divergent, scenario.target)


def _rule_bump(outcome, version: str):
    """The same outcome under a later rule version.

    `dataclasses.replace` on the frozen drafts, so nothing about the evaluation
    is re-decided here -- only the version label the derivation identity keys on.
    """
    import dataclasses

    return dataclasses.replace(
        outcome, derivation=dataclasses.replace(outcome.derivation, derivation_rule_version=version)
    )


# ============================================ §70.40-45 atomicity


class TestDirectionalAtomicity:
    """Every rollback is verified through a SEPARATE connection.

    A read inside the aborted transaction would see its own uncommitted writes,
    which is how a rollback test passes without proving anything.
    """

    def _arrange(self, conn, workspace_id):
        return Scenario(conn, workspace_id)

    def test_a_failure_after_the_derivation_rolls_everything_back(
        self, committing_tenant_conn, probe_workspace
    ):
        class InjectedFailureError(Exception):
            pass

        scenario_signal: dict[str, str] = {}
        with (  # noqa: PT012
            pytest.raises(InjectedFailureError),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            scenario = Scenario(conn, probe_workspace)
            scenario_signal["id"] = scenario.signal_id
            persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            raise InjectedFailureError

        with committing_tenant_conn(probe_workspace) as conn:
            after = counts(conn, probe_workspace)
        assert after == {
            "claims": 0,
            "revisions": 0,
            "evidence": 0,
            "derivations": 0,
            "refusals": 0,
            "thresholds": 0,
        }

    def test_a_failure_at_the_evidence_step_rolls_the_claim_back(
        self, committing_tenant_conn, probe_workspace
    ):
        """The failure is injected INSIDE the command, by removing the Signal the
        Evidence row must reference. The Claim and revision are written first, so
        this proves transaction ownership sits above the repositories."""
        with (  # noqa: PT012
            pytest.raises(psycopg.errors.Error),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            scenario = Scenario(conn, probe_workspace)
            conn.execute(
                "DELETE FROM nlp.signals WHERE id = %s AND workspace_id = %s",
                (scenario.signal_id, probe_workspace),
            )
            persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")

        with committing_tenant_conn(probe_workspace) as conn:
            after = counts(conn, probe_workspace)
        assert after["claims"] == 0
        assert after["revisions"] == 0
        assert after["derivations"] == 0
        assert after["evidence"] == 0

    def test_a_missing_threshold_fails_before_any_write(
        self, committing_tenant_conn, probe_workspace
    ):
        with (  # noqa: PT012
            pytest.raises(PersistenceError, match="THRESHOLD_NOT_FOUND"),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            signal_id = _signal(conn, probe_workspace)
            outcome = evaluate(
                witness(probe_workspace, signal_id),
                target(),
                registration(probe_workspace, str(uuid.uuid4())),
                equivalence(),
            )
            persist_evaluation_outcome(conn, outcome, target())

        with committing_tenant_conn(probe_workspace) as conn:
            after = counts(conn, probe_workspace)
        assert after["claims"] == 0
        assert after["derivations"] == 0

    def test_a_refusal_failure_leaves_nothing(self, committing_tenant_conn, probe_workspace):
        class InjectedFailureError(Exception):
            pass

        with (  # noqa: PT012
            pytest.raises(InjectedFailureError),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            scenario = Scenario(conn, probe_workspace, unit="unit-2")
            persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            raise InjectedFailureError

        with committing_tenant_conn(probe_workspace) as conn:
            after = counts(conn, probe_workspace)
        assert after["refusals"] == 0

    def test_a_committed_directional_transaction_satisfies_the_deferred_trigger(
        self, committing_tenant_conn, probe_workspace
    ):
        """§47. The evidence requirement fires at COMMIT, so the only proof that
        it is satisfied is a COMMIT that succeeded."""
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace)
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")

        with committing_tenant_conn(probe_workspace) as conn:
            survived = conn.execute(
                "SELECT count(*) FROM research.claims WHERE id = %s", (result.claim_id,)
            ).fetchone()[0]
        assert survived == 1


# ============================================ §70.46 the ADR-038 transition


class TestUnknownThenSupports:
    def test_a_later_supports_leaves_the_historical_refusal_alone(
        self, committing_tenant_conn, probe_workspace
    ):
        """§45. ADR-038's transition, end to end and on real rows."""
        with committing_tenant_conn(probe_workspace) as conn:
            signal_id = _signal(conn, probe_workspace)
            threshold_id = str(uuid.uuid4())
            _threshold_row(conn, probe_workspace, threshold_id, f"subject-{uuid.uuid4()}")
            unknown = evaluate(
                witness(probe_workspace, signal_id),
                target(),
                registration(probe_workspace, threshold_id),
                equivalence(EquivalenceVerdict.UNKNOWN, "basis-before-review"),
            )
            refusal = persist_evaluation_outcome(conn, unknown, target())

        with committing_tenant_conn(probe_workspace) as conn:
            supported = evaluate(
                witness(probe_workspace, signal_id),
                target(),
                registration(probe_workspace, threshold_id),
                equivalence(EquivalenceVerdict.EQUIVALENT, "basis-after-review"),
            )
            directional = persist_evaluation_outcome(conn, supported, target())

        with committing_tenant_conn(probe_workspace) as conn:
            after = counts(conn, probe_workspace)
            stored = conn.execute(
                "SELECT evaluation_result, reason_code, semantic_equivalence_basis_id FROM "
                "research.proposition_evaluation_refusals WHERE id = %s",
                (refusal.refusal_id,),
            ).fetchone()

        assert stored == ("UNKNOWN", "EQUIVALENCE_NOT_ESTABLISHED", "basis-before-review")
        assert after["refusals"] == 1, "the historical refusal is neither rewritten nor removed"
        assert (after["claims"], after["evidence"], after["derivations"]) == (1, 1, 1)
        assert directional.path is PersistencePath.DIRECTIONAL


# ============================================ §70.37-39, 48-59 boundaries


class TestBoundaries:
    def test_a_cross_workspace_signal_is_refused(
        self, committing_tenant_conn, privileged_conn, probe_workspace, other_workspace
    ):
        foreign_signal = _signal(privileged_conn, other_workspace)
        privileged_conn.commit()
        with (  # noqa: PT012
            pytest.raises(psycopg.errors.Error),
            committing_tenant_conn(probe_workspace) as conn,
        ):
            threshold_id = str(uuid.uuid4())
            _threshold_row(conn, probe_workspace, threshold_id, f"subject-{uuid.uuid4()}")
            outcome = evaluate(
                witness(probe_workspace, foreign_signal),
                target(),
                registration(probe_workspace, threshold_id),
                equivalence(),
            )
            persist_evaluation_outcome(conn, outcome, target())
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_the_orchestrator_imports_no_aggregator_gateway_or_acquisition(self):
        import pathlib

        source = pathlib.Path(
            pathlib.Path(__file__).resolve().parents[1] / "sros_nlp" / "inferred_persistence.py"
        ).read_text(encoding="utf-8")
        for forbidden in (
            "sros_evidence_aggregation",
            "sros_llm_gateway",
            "sros_acquisition",
            "sros_opportunity",
        ):
            assert f"import {forbidden}" not in source
            assert f"from {forbidden}" not in source

    def test_the_evaluator_still_reaches_no_database(self):
        """The dependency direction: persistence imports the evaluator, never
        the reverse."""
        import pathlib

        package = (
            pathlib.Path(__file__).resolve().parents[4]
            / "packages/inferred-claim-evaluator/python/sros_inferred_claim_evaluator"
        )
        for module in package.glob("*.py"):
            text = module.read_text(encoding="utf-8")
            assert "psycopg" not in text
            assert "sros_nlp" not in text

    def test_no_reliability_is_assigned(self, committing_tenant_conn, probe_workspace):
        """§57. The first INFERRED Evidence resolves NO_APPLICABLE_ASSESSMENT and
        is NON_SCORABLE, which is correct and is not this layer's to fix."""
        with committing_tenant_conn(probe_workspace) as conn:
            scenario = Scenario(conn, probe_workspace)
            result = persist_evaluation_outcome(conn, scenario.outcome, scenario.target)
            reliability, independence, group = conn.execute(
                "SELECT reliability, independence_state, independence_group_id "
                "FROM scoring.evidence WHERE id = %s",
                (result.evidence_id,),
            ).fetchone()
        assert reliability is None
        assert independence == "UNKNOWN"
        assert group is None
