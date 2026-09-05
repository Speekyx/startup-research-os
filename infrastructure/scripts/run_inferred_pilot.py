"""Execute the Mission 1.56 pilot, once, against the real database.

    uv run python infrastructure/scripts/run_inferred_pilot.py --approve <sha256>

This is the only thing in the repository that writes a canonical INFERRED row,
and it refuses to do so unless an operator supplies the SHA-256 of the manifest
they read. That is not ceremony: the hash is what makes "approved" name a
specific document rather than the idea of one, so a manifest edited after
approval no longer answers to the string the operator typed.

Four things it will not do, and each is a refusal rather than a convention.

  * It never registers the threshold "on the way past" during evaluation. The
    bound is written first, in its own committed transaction, and the evaluator
    is handed the row that exists -- because a bound created while the
    measurement is being compared against it is a bound chosen after seeing the
    measurement.
  * It never picks a persistence path. `persist_evaluation_outcome` routes on
    the evaluator's own result, and all four results are acceptable outcomes of
    this run. There is no branch here that prefers SUPPORTS.
  * It never widens the mutation envelope. The counters are read before and
    after; anything outside what the manifest authorises stops the run with
    PILOT_MUTATION_ENVELOPE_VIOLATION.
  * It never evaluates a measurement that has drifted from the frozen one. Every
    input the manifest fixed is re-read from the live rows and compared, so a
    Signal that changed since the manifest was hashed refuses instead of
    quietly evaluating something else.

It is idempotent by construction rather than by promise: phase C replays the
whole evaluation and persistence and asserts that nothing new was written.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
EXECUTION = DATA / "first-deterministic-inferred-pilot-v1.json"

sys.path.insert(0, str(ROOT / "infrastructure" / "scripts"))

from render_inferred_pilot import manifest_hash, validate  # noqa: E402

DEFAULT_DATABASE_URL = "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros"

# Read before and after. Every one of them must land inside the envelope the
# manifest froze, including the ones that must not move at all.
COUNTERS = {
    "raw_records": "acquisition.raw_records",
    "normalized_records": "acquisition.normalized_records",
    "signals": "nlp.signals",
    "claims": "research.claims",
    "claim_revisions": "research.claim_revisions",
    "evidence": "scoring.evidence",
    "reliability_assessments": "epistemic.reliability_assessments",
    "threshold_registrations": "research.threshold_registrations",
    "claim_derivations": "research.claim_derivations",
    "proposition_evaluation_refusals": "research.proposition_evaluation_refusals",
    "opportunities": "research.opportunities",
    "opportunity_revisions": "research.opportunity_hypothesis_revisions",
    "opportunity_evidence_links": "research.opportunity_hypothesis_evidence",
    "embeddings": "nlp.embedding_provenance",
    "sources": "registry.sources",
}


class PilotRefusedError(Exception):
    """The run stops. Nothing half-written, because every phase commits or
    rolls back whole."""


# ------------------------------------------------------------------ the guards


def _require_approval(manifest: dict, supplied: str) -> str:
    digest = manifest_hash(manifest)
    if supplied.strip().lower() != digest:
        raise PilotRefusedError(
            "the approval names a different manifest.\n"
            f"  approved: {supplied.strip().lower()}\n"
            f"  on disk:  {digest}\n"
            "A manifest edited after approval is a manifest nobody approved."
        )
    return digest


def _counters(conn: Any) -> dict[str, int]:
    return {
        name: int(conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0])  # noqa: S608
        for name, table in COUNTERS.items()
    }


def _inferred_claims(conn: Any) -> int:
    return int(
        conn.execute(
            "SELECT count(*) FROM research.claims WHERE claim_type = 'INFERRED'"
        ).fetchone()[0]
    )


def _live_signal(conn: Any, signal_id: str, manifest: dict) -> dict[str, Any]:
    """Re-read what the manifest froze, plus the two provenance facts it does
    NOT freeze.

    `resource_id` and `observed_claim_id` are read from the rows rather than
    from the manifest deliberately. The manifest fixes the DECISIONS an operator
    approved -- which candidate, which bound, which equivalence basis. Where the
    measurement was acquired from and which OBSERVED Claim already restates it
    are facts about rows that already exist, and copying a fact into a document
    so a script can read it back is how the document becomes a second authority.
    """
    row = conn.execute(
        """SELECT s.magnitude, s.magnitude_unit, s.signal_type_id,
                  min(rr.collected_at), max(rr.collected_at),
                  count(DISTINCT nr.provenance -> 'acquisition' ->> 'resource_id'),
                  min(nr.provenance -> 'acquisition' ->> 'resource_id')
             FROM nlp.signals s
             JOIN nlp.signal_inputs si ON si.signal_id = s.id
             JOIN acquisition.normalized_records nr ON nr.id = si.normalized_record_id
             JOIN acquisition.raw_records rr ON rr.id = nr.raw_record_id
            WHERE s.id = %s
            GROUP BY s.magnitude, s.magnitude_unit, s.signal_type_id""",
        (signal_id,),
    ).fetchone()
    if row is None:
        raise PilotRefusedError(f"Signal {signal_id} does not exist in this workspace")
    magnitude, unit, signal_type_id, first_seen, last_seen, resources, resource_id = row
    if first_seen != last_seen:
        raise PilotRefusedError(
            "the contributing observations were retrieved at different instants, so there "
            "is no single retrieval time for the preregistration rule to compare against"
        )
    if resources != 1 or not resource_id:
        raise PilotRefusedError(
            f"the contributing observations name {resources} resources. A reliability scope "
            "is per resource, so a witness spanning two of them has no single scope"
        )

    # The DETAILED OBSERVED restatement of exactly this measurement, selected by
    # the one property that separates it from the CONVERGENT existential this
    # Signal also witnesses (Mission 1.43): the detailed proposition names the
    # SAME two day labels the target does, and the convergent one deliberately
    # names no period at all, because there the labels are witness rather than
    # identity. Selecting on that costs the manifest no extra field, and it says
    # what is actually meant -- the derivation names the observation restating
    # the same bounded measurement, not a broader claim built from it.
    period_from, _, period_to = manifest["target_proposition"]["facts"]["time_bound"].partition("/")
    observed = conn.execute(
        """SELECT cl.id::text
             FROM scoring.evidence e
             JOIN research.claims cl ON cl.id = e.claim_id
            WHERE e.signal_id = %s
              AND cl.claim_type = 'OBSERVED'
              AND cl.proposition_facts ->> 'period_label_from' = %s
              AND cl.proposition_facts ->> 'period_label_to' = %s""",
        (signal_id, period_from, period_to),
    ).fetchall()
    if len(observed) != 1:
        raise PilotRefusedError(
            f"{len(observed)} OBSERVED Claims restate this Signal over {period_from}..{period_to}. "
            "The derivation names the observation it reasoned from, and it can name only one"
        )
    return {
        "magnitude": magnitude,
        "unit": unit,
        "signal_type_id": signal_type_id,
        "retrieved_at": first_seen,
        "resource_id": resource_id,
        "observed_claim_id": observed[0][0],
    }


def _require_no_drift(manifest: dict, live: dict[str, Any]) -> None:
    frozen = manifest["selected_signal"]
    checks = [
        ("measurement_value", Decimal(frozen["measurement_value"]), live["magnitude"]),
        ("unit", frozen["unit"], live["unit"]),
        ("signal_type_id", frozen["signal_type_id"], live["signal_type_id"]),
        (
            "retrieved_at",
            datetime.fromisoformat(frozen["retrieved_at"]),
            live["retrieved_at"],
        ),
    ]
    for field, expected, actual in checks:
        if expected != actual:
            raise PilotRefusedError(
                f"the Signal's {field} has drifted since the manifest was hashed: "
                f"frozen {expected!r}, live {actual!r}. The operator approved an "
                "evaluation of the frozen measurement"
            )


# --------------------------------------------------------- phase A, the bound


def _register_threshold(conn: Any, manifest: dict, workspace_id: str) -> tuple[str, datetime, bool]:
    """Write the bound, or find the one already written.

    Committed BEFORE the evaluator is constructed, so the evaluation reads a
    registration that exists rather than one it is creating.
    """
    threshold = manifest["threshold_registration"]
    key = (
        workspace_id,
        threshold["metric_definition_id"],
        threshold["scope_subject_id"],
        threshold["scope_population"],
        threshold["scope_time_bound"],
        threshold["threshold_operator"],
        Decimal(threshold["threshold_value"]),
        threshold["provenance_status"],
    )
    existing = conn.execute(
        """SELECT id::text, recorded_at FROM research.threshold_registrations
            WHERE workspace_id = %s AND metric_definition_id = %s AND scope_subject_id = %s
              AND scope_population = %s AND scope_time_bound = %s
              AND threshold_operator = %s AND threshold_value = %s
              AND provenance_status = %s""",
        key,
    ).fetchone()
    if existing is not None:
        return existing[0], existing[1], False

    registration_id = str(uuid.uuid4())
    recorded_at = datetime.now(UTC)
    conn.execute(
        """INSERT INTO research.threshold_registrations (
               id, workspace_id, threshold_operator, threshold_value, unit,
               metric_definition_id, scope_subject_id, scope_population, scope_time_bound,
               provenance_status, recorded_at, recorded_by, provenance_reference)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            registration_id,
            workspace_id,
            threshold["threshold_operator"],
            Decimal(threshold["threshold_value"]),
            threshold["unit"],
            threshold["metric_definition_id"],
            threshold["scope_subject_id"],
            threshold["scope_population"],
            threshold["scope_time_bound"],
            threshold["provenance_status"],
            recorded_at,
            threshold["recorded_by"],
            # POST_HOC needs none, and the CHECK says so. It is written anyway
            # because "a round decimal bound an operator chose today" is exactly
            # what a later reader needs and exactly what the status alone omits.
            threshold["provenance_reference"],
        ),
    )
    return registration_id, recorded_at, True


# ------------------------------------------------- phases B and C, the pilot


def _build_inputs(
    manifest: dict,
    equivalence_record: dict,
    live: dict,
    workspace_id: str,
    registration_id: str,
    recorded_at: datetime,
):
    from sros_inferred_claim_evaluator import (
        EquivalenceDimension,
        EquivalenceVerdict,
        MeasurementWitness,
        SemanticEquivalenceDecision,
        TargetProposition,
        ThresholdOperator,
        ThresholdProvenanceStatus,
        ThresholdRegistration,
    )

    facts = manifest["target_proposition"]["facts"]
    signal = manifest["selected_signal"]
    threshold = manifest["threshold_registration"]

    target = TargetProposition(
        proposition_kind=facts["proposition"],
        canonical_subject_id=facts["canonical_subject_id"],
        metric_definition_id=facts["metric_definition_id"],
        time_bound=facts["time_bound"],
        population_or_geography=facts["population_or_geography"],
        unit=facts["unit"],
        threshold_operator=ThresholdOperator(facts["threshold_operator"]),
        threshold_value=Decimal(facts["threshold_value"]),
    )
    witness = MeasurementWitness(
        workspace_id=workspace_id,
        signal_id=signal["signal_id"],
        source_id=signal["source_id"],
        resource_id=live["resource_id"],
        record_kind_id=signal["record_kind_id"],
        canonical_subject_id=facts["canonical_subject_id"],
        source_native_metric_id=signal["signal_type_id"],
        metric_definition_id=facts["metric_definition_id"],
        # From the LIVE row, not from the manifest. The manifest is what was
        # approved; the row is what is being evaluated, and the drift check
        # above is what makes them the same thing.
        measurement_value=live["magnitude"],
        unit=live["unit"],
        time_bound=facts["time_bound"],
        population_or_geography=facts["population_or_geography"],
        retrieved_at=live["retrieved_at"],
        observed_claim_id=live["observed_claim_id"],
    )
    registration = ThresholdRegistration(
        registration_id=registration_id,
        workspace_id=workspace_id,
        metric_definition_id=threshold["metric_definition_id"],
        scope_subject_id=threshold["scope_subject_id"],
        scope_population=threshold["scope_population"],
        scope_time_bound=threshold["scope_time_bound"],
        unit=threshold["unit"],
        threshold_operator=ThresholdOperator(threshold["threshold_operator"]),
        threshold_value=Decimal(threshold["threshold_value"]),
        provenance_status=ThresholdProvenanceStatus(threshold["provenance_status"]),
        recorded_at=recorded_at,
        recorded_by=threshold["recorded_by"],
        provenance_reference=threshold["provenance_reference"],
    )
    equivalence = SemanticEquivalenceDecision(
        basis_id=equivalence_record["basis_id"],
        verdict=EquivalenceVerdict(equivalence_record["verdict"]),
        dimensions_checked=frozenset(
            EquivalenceDimension(entry["dimension"]) for entry in equivalence_record["dimensions"]
        ),
        reviewed_by=equivalence_record["reviewed_by"],
        reviewed_at=datetime.fromisoformat(equivalence_record["recorded_at"] + "T00:00:00+00:00"),
        interpretation_confidence=equivalence_record["interpretation_confidence"]["proposed_value"],
    )
    return witness, target, registration, equivalence


def _result_row(result: Any) -> dict[str, Any]:
    return {
        "path": result.path.value,
        "status": result.status.value,
        "claim_id": result.claim_id,
        "claim_revision_id": result.claim_revision_id,
        "derivation_id": result.derivation_id,
        "evidence_id": result.evidence_id,
        "refusal_id": result.refusal_id,
        "claim_created": result.claim_created,
        "derivation_created": result.derivation_created,
        "evidence_created": result.evidence_created,
        "refusal_created": result.refusal_created,
        "conflict": None if result.conflict is None else str(result.conflict),
    }


def _check_envelope(
    manifest: dict, before: dict[str, int], after: dict[str, int], path: str
) -> None:
    envelope = manifest["canonical_mutation_envelope"]
    allowed = dict.fromkeys(COUNTERS, 0)
    allowed["threshold_registrations"] = envelope["threshold_registrations"]
    allowed.update(
        envelope["directional_maximum"] if path == "DIRECTIONAL" else envelope["refusal_maximum"]
    )
    breaches = [
        f"{name}: {before[name]} -> {after[name]} (at most +{allowed[name]})"
        for name in COUNTERS
        if after[name] - before[name] != allowed[name]
    ]
    if breaches:
        raise PilotRefusedError("PILOT_MUTATION_ENVELOPE_VIOLATION\n  " + "\n  ".join(breaches))


# ------------------------------------------------------------------- the run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--approve",
        required=True,
        help="the SHA-256 of the manifest the operator read. No default, ever.",
    )
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()

    import psycopg
    from sros_inferred_claim_evaluator import evaluate, target_proposition_facts
    from sros_nlp.inferred_persistence import persist_evaluation_outcome

    try:
        _, equivalence_record, manifest = validate()
    except Exception as error:
        print(f"REFUSED  the pilot documents do not validate: {error}")
        return 1

    try:
        digest = _require_approval(manifest, args.approve)
    except PilotRefusedError as error:
        print(f"REFUSED  {error}")
        return 1

    url = args.database_url or DEFAULT_DATABASE_URL
    conn = psycopg.connect(url, autocommit=False)
    workspace = manifest["selected_signal"]["workspace"]
    started_at = datetime.now(UTC)

    def tenant() -> None:
        row = conn.execute(
            "SELECT id::text FROM core.workspaces WHERE slug = %s", (workspace,)
        ).fetchone()
        if row is None:
            raise PilotRefusedError(f"workspace {workspace!r} does not exist")
        conn.execute("SELECT set_config('app.workspace_id', %s, true)", (row[0],))
        return row[0]

    try:
        # ------------------------------------------------------- the baseline
        workspace_id = tenant()
        before = _counters(conn)
        inferred_before = _inferred_claims(conn)
        live = _live_signal(conn, manifest["selected_signal"]["signal_id"], manifest)
        _require_no_drift(manifest, live)
        for name, expected in manifest["baseline_counters"].items():
            if name in COUNTERS and before[name] != expected:
                raise PilotRefusedError(
                    f"the deployment has moved since the manifest was hashed: {name} is "
                    f"{before[name]} and the manifest recorded {expected}"
                )
        conn.rollback()
        print(f"ok       baseline verified, {len(COUNTERS)} counters, no drift")

        # --------------------------------------------- phase A, the threshold
        workspace_id = tenant()
        registration_id, recorded_at, created = _register_threshold(conn, manifest, workspace_id)
        conn.commit()
        print(
            f"{'wrote' if created else 'found'}    threshold registration {registration_id} "
            f"({manifest['threshold_registration']['provenance_status']})"
        )

        workspace_id = tenant()
        stored = conn.execute(
            """SELECT threshold_operator, threshold_value, unit, provenance_status, recorded_by
                 FROM research.threshold_registrations WHERE id = %s""",
            (registration_id,),
        ).fetchone()
        conn.rollback()
        if stored is None:
            raise PilotRefusedError("the threshold registration is not readable after commit")
        print(f"ok       row verified: {stored[0]} {stored[1]} {stored[2]}, {stored[3]}")

        witness, target, registration, equivalence = _build_inputs(
            manifest, equivalence_record, live, workspace_id, registration_id, recorded_at
        )

        # ------------------------------------- phase B, evaluate then persist
        outcome = evaluate(witness, target, registration, equivalence)
        print(f"ok       evaluated once: {outcome.result.value}")

        workspace_id = tenant()
        result = persist_evaluation_outcome(conn, outcome, target)
        conn.commit()
        print(f"ok       persisted: path {result.path.value}, status {result.status.value}")

        workspace_id = tenant()
        after = _counters(conn)
        inferred_after = _inferred_claims(conn)
        conn.rollback()
        _check_envelope(manifest, before, after, result.path.value)
        print("ok       mutation envelope respected")

        # --------------------------------------------------- phase C, replay
        replay_outcome = evaluate(witness, target, registration, equivalence)
        workspace_id = tenant()
        replay = persist_evaluation_outcome(conn, replay_outcome, target)
        conn.commit()

        workspace_id = tenant()
        after_replay = _counters(conn)
        conn.rollback()
        if after_replay != after:
            raise PilotRefusedError(
                "the replay changed the database. The evaluation is not idempotent:\n  "
                + "\n  ".join(
                    f"{name}: {after[name]} -> {after_replay[name]}"
                    for name in COUNTERS
                    if after[name] != after_replay[name]
                )
            )
        print(f"ok       replayed: status {replay.status.value}, 0 rows created")

    except Exception as error:
        conn.rollback()
        conn.close()
        print(f"REFUSED  {error}")
        return 1

    conn.close()

    execution = {
        "mission": manifest["mission"],
        "artifact": "pilot execution record",
        "recorded_at": started_at.date().isoformat(),
        "status": "EXECUTED",
        "approval": {
            "manifest_sha256": digest,
            "approved_by": manifest["threshold_registration"]["recorded_by"],
            "the_hash_is_the_approval": (
                "The operator approved a specific document. This record names its hash so a "
                "later reader can check that the manifest in the repository is the one that "
                "was approved, rather than a manifest that agrees with this record."
            ),
            "the_manifest_was_not_edited_afterwards": (
                "Its status still reads AWAITING_OPERATOR_APPROVAL, deliberately. Marking it "
                "APPROVED would change its bytes and therefore its hash, and a frozen document "
                "that no longer answers to the hash it was frozen at is not frozen."
            ),
        },
        "evaluation": {
            "result": outcome.result.value,
            "rationale": outcome.rationale,
            "refusal_reason": outcome.refusal_reason,
            "calibration_eligible": outcome.calibration_eligible,
            "proposition_key": outcome.proposition_key,
            "target_proposition_facts": target_proposition_facts(target),
            "calls": 1,
            "second_call_with_adjusted_inputs": 0,
            "model_calls": 0,
            "network_requests": 0,
        },
        "threshold_registration": {
            "registration_id": registration_id,
            "created_by_this_run": created,
            "provenance_status": stored[3],
            "recorded_at": recorded_at.isoformat(),
            "recorded_by": stored[4],
            "written_before_the_evaluation": (
                "Phase A commits before the evaluator is constructed, so the bound was not "
                "chosen while the measurement was being compared against it."
            ),
        },
        "persistence": _result_row(result),
        "replay": {
            **_result_row(replay),
            "rows_created": 0,
            "what_it_proves": (
                "Running the whole evaluation and persistence again changed nothing. "
                "Idempotency is demonstrated rather than asserted."
            ),
        },
        "counters": {
            "before": before,
            "after": after,
            "after_replay": after_replay,
            "delta": {n: after[n] - before[n] for n in COUNTERS if after[n] != before[n]},
            "inferred_claims_before": inferred_before,
            "inferred_claims_after": inferred_after,
        },
        "what_this_run_did_not_do": manifest["what_this_pilot_will_not_do"],
        "known_limitation": manifest["known_limitation_the_operator_should_weigh"],
    }
    EXECUTION.write_text(
        json.dumps(execution, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote    {EXECUTION.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
