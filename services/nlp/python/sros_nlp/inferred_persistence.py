"""Where a deterministic evaluation becomes rows, and where it does not.

ADR-036 said a source-independent proposition is an `INFERRED` Claim, ADR-037
specified its derivation provenance, and ADR-038 said a refusal is not a
derivation of a Claim and gets its own record. Migrations 0034 and 0035 built the
tables. This module is the one place those decisions meet a transaction.

    EvaluationOutcome
        |
        +-- SUPPORTS / CONTRADICTS -> Claim, ClaimRevision, derivation, Evidence
        |
        +-- NOT_APPLICABLE / UNKNOWN -> one refusal row, and nothing else

**There is no third branch**, and the routing is exhaustive over
`EvaluationResult` rather than an if/else with a fallthrough: a member added
later reaches a `raise`, not a default.

**This module decides nothing epistemic.** It does not evaluate, select a
threshold, judge equivalence, adjudicate independence, resolve reliability,
aggregate or call a model. Every one of those is already decided by the time an
outcome arrives, and the imports say so -- there is no Gateway, no aggregator and
no acquisition import here.

**It does not own its transaction.** The connection arrives already inside the
caller's tenant transaction, exactly as `run_claim_interpretation_job` takes a
`connection_factory`. That is what makes the whole directional path atomic: the
evidence requirement is a deferred trigger firing at COMMIT, so Claim, revision,
derivation and Evidence must be able to fail together.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sros_claim_model import (
    ClaimInterpretation,
    EvidenceDraft,
    build_claim,
    canonical_json,
    proposition_key,
)
from sros_contracts import (
    ClaimInterpretationKind,
    ClaimOrigin,
    ClaimTemporality,
    ClaimType,
    EvidenceDirection,
)
from sros_inferred_claim_evaluator import (
    EvaluationOutcome,
    EvaluationResult,
    TargetProposition,
    target_proposition_facts,
)

from .claim_repositories import persist_claims

__all__ = [
    "PersistencePath",
    "PersistenceResult",
    "PersistenceStatus",
    "PersistenceError",
    "persist_evaluation_outcome",
    "claim_statement",
]


class PersistencePath(StrEnum):
    """Two, and only two."""

    DIRECTIONAL = "DIRECTIONAL"
    REFUSAL = "REFUSAL"


class PersistenceStatus(StrEnum):
    """What the attempt did, in terms a caller can branch on.

    `REVIEW_REQUIRED` is not a failure and not a success. It is the state Policy
    D produces: a new evaluation disagrees with a standing Evidence relation, and
    this layer is forbidden to resolve that by writing.
    """

    PERSISTED = "PERSISTED"
    REUSED = "REUSED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class PersistenceErrorCode(StrEnum):
    """A system or contract failure. **Never an epistemic finding.**

    A database error is not an `UNKNOWN` evaluation and a workspace mismatch is
    not a `NOT_APPLICABLE` one. Turning either into a refusal row would file a
    programming mistake as a judgement about the world.
    """

    INVALID_OUTCOME = "INVALID_OUTCOME"
    WORKSPACE_MISMATCH = "WORKSPACE_MISMATCH"
    TARGET_MISMATCH = "TARGET_MISMATCH"
    THRESHOLD_NOT_FOUND = "THRESHOLD_NOT_FOUND"
    PROPOSITION_IDEMPOTENCY_CONFLICT = "PROPOSITION_IDEMPOTENCY_CONFLICT"
    DERIVATION_IDEMPOTENCY_CONFLICT = "DERIVATION_IDEMPOTENCY_CONFLICT"
    REFUSAL_IDEMPOTENCY_CONFLICT = "REFUSAL_IDEMPOTENCY_CONFLICT"


class PersistenceError(Exception):
    """Raised so the caller's transaction unwinds.

    Carrying a code rather than only a message, because a caller that has to
    parse prose to tell a workspace mismatch from an idempotency conflict will
    eventually parse it wrong.
    """

    def __init__(self, code: PersistenceErrorCode, detail: str) -> None:
        super().__init__(f"{code.value}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class EvidenceDirectionConflict:
    """Policy D, as a structured object rather than a log line.

    Every field a reviewer needs to see the disagreement without re-running
    anything. `detected_at` is deliberately absent: the derivation row this
    conflict accompanies carries `created_at`, and a second timestamp would be a
    second authority for one moment.
    """

    workspace_id: str
    claim_id: str
    signal_id: str
    evidence_id: str
    existing_direction: str
    evaluated_direction: str
    derivation_rule_id: str
    derivation_rule_version: str
    evaluator_version: str
    target_proposition_key: str
    semantic_equivalence_basis_id: str
    reason: str = "EVIDENCE_DIRECTION_CONFLICT"


@dataclass(frozen=True)
class PersistenceResult:
    """What was written, and what was found already written.

    Ids are `None` for entities the branch never creates -- a refusal has no
    `claim_id`, and inventing one so the shape is uniform would be the fabricated
    Claim ADR-038 exists to prevent.
    """

    path: PersistencePath
    status: PersistenceStatus
    claim_id: str | None = None
    claim_revision_id: str | None = None
    derivation_id: str | None = None
    evidence_id: str | None = None
    refusal_id: str | None = None
    claim_created: bool = False
    derivation_created: bool = False
    evidence_created: bool = False
    refusal_created: bool = False
    conflict: EvidenceDirectionConflict | None = None


# ---------------------------------------------------------------- the wording


def claim_statement(target: TargetProposition) -> str:
    """The Claim's sentence, from the TARGET and nothing else.

    This is load-bearing and easy to get wrong. `_persist_one` appends a new
    ClaimRevision whenever the statement differs from the stored one, so a
    statement mentioning the witness, the measurement or the source would make
    every additional Signal supporting the same proposition look like a changed
    Claim -- revision churn that says the proposition was reformulated when only
    the evidence grew. ADR-036's whole point is that several witnesses reach ONE
    source-independent Claim, and that only holds if they all word it identically.

    So: no source, no measurement, no direction, no rule version. Exactly the
    facts that are already proposition identity.
    """
    operator = {
        "GTE": "at least",
        "GT": "greater than",
        "LTE": "at most",
        "LT": "less than",
    }[target.threshold_operator.value]
    return (
        f"{target.metric_definition_id} for {target.canonical_subject_id} "
        f"over {target.population_or_geography} in {target.time_bound} "
        f"is {operator} {target.threshold_value} {target.unit}."
    )


# ---------------------------------------------------------------- the command


def persist_evaluation_outcome(
    conn: Any,
    outcome: EvaluationOutcome,
    target: TargetProposition,
) -> PersistenceResult:
    """Route one outcome to exactly one persistence path.

    `target` is passed alongside rather than read off the outcome, and that is a
    deliberate consequence of the evaluator's own contract: a refusal carries no
    `proposition_key` and no claim draft, because the evaluator declines to name
    a proposition it just declined to establish. The TARGET is an INPUT the
    caller chose, not something the evaluation concluded, so the caller supplies
    it. For a directional outcome the two are cross-checked rather than trusted.
    """
    facts = target_proposition_facts(target)
    key = proposition_key(facts)

    if outcome.proposition_key is not None and outcome.proposition_key != key:
        raise PersistenceError(
            PersistenceErrorCode.TARGET_MISMATCH,
            "the outcome's proposition key is not the key of the target supplied with it. "
            "One of them describes a different proposition, and guessing which would "
            "attach reasoning to the wrong Claim",
        )

    # Exhaustive over the four members. No `else`, so a fifth member added later
    # reaches the raise below rather than silently taking a branch.
    result = outcome.result
    if result in (EvaluationResult.SUPPORTS, EvaluationResult.CONTRADICTS):
        return _persist_directional(conn, outcome, target, facts, key)
    if result in (EvaluationResult.NOT_APPLICABLE, EvaluationResult.UNKNOWN):
        return _persist_refusal(conn, outcome, facts, key)
    raise PersistenceError(  # pragma: no cover - unreachable until the enum grows
        PersistenceErrorCode.INVALID_OUTCOME,
        f"{result!r} routes to no persistence path. A new evaluation result needs a "
        "decision about what it means before it can be stored, and defaulting it to "
        "either branch would store a judgement nobody made",
    )


# ------------------------------------------------------------ directional path


def _persist_directional(
    conn: Any,
    outcome: EvaluationOutcome,
    target: TargetProposition,
    facts: Mapping[str, str],
    key: str,
) -> PersistenceResult:
    derivation = outcome.derivation
    decision = outcome.evidence_decision
    draft_claim = outcome.claim_draft
    if decision is None or draft_claim is None:
        raise PersistenceError(
            PersistenceErrorCode.INVALID_OUTCOME,
            "a directional outcome carries an Evidence decision and a Claim draft. "
            "Without both there is nothing to attach and nothing to attach it to",
        )

    workspace_id = derivation.workspace_id
    _require_threshold(conn, workspace_id, derivation.threshold_registration_id)

    # The canonical builder, not a hand-rolled insert: it enforces the evidence
    # requirement in the model as well as in the trigger, and refuses an
    # automated claim with no interpreter provenance or no confidence.
    draft = build_claim(
        workspace_id=workspace_id,
        claim_type=ClaimType.INFERRED,
        temporality=ClaimTemporality.EVERGREEN,
        origin=ClaimOrigin.DETERMINISTIC_EXTRACTION,
        statement=claim_statement(target),
        facts=facts,
        evidence=[
            EvidenceDraft(
                signal_id=decision.signal_id,
                direction=EvidenceDirection(decision.direction),
                source_id=decision.source_id,
                # Relevance and directness are 1.0 because the Claim is exactly
                # the proposition this evaluation was about, and extraction
                # confidence because a Decimal comparison either read the facts
                # or raised. Reliability stays NULL: it is purpose-relative and
                # resolved late from a reviewed assessment, so the first INFERRED
                # rows will be NON_SCORABLE and that is correct.
                relevance=1.0,
                directness=1.0,
                extraction_confidence=1.0,
                reliability=None,
            )
        ],
        interpretation=ClaimInterpretation(
            interpreter_id=derivation.derivation_rule_id,
            interpreter_version=derivation.derivation_rule_version,
            kind=ClaimInterpretationKind.DETERMINISTIC,
        ),
        # From the reviewed equivalence decision, never recomputed here: the
        # arithmetic being exact says nothing about whether the wording faithfully
        # reads the Signal.
        interpretation_confidence=draft_claim.interpretation_confidence,
        rationale=draft_claim.origin_detail,
    )

    report = persist_claims(conn, [draft])
    claim_id = report.claim_ids[0]
    claim_created = report.new == 1

    _verify_stored_proposition(conn, workspace_id, claim_id, key)
    revision_id = _current_revision_id(conn, workspace_id, claim_id)

    conflict = _conflict_from(conn, report, outcome, derivation, key, workspace_id)

    # Policy D, option A. The derivation is written EVEN when the Evidence
    # direction conflicts, because the derivation is an append-only record of
    # what a rule concluded and refusing to store it would lose the very finding
    # the reviewer is being asked about. What is not written is the Evidence:
    # `_persist_evidence` already refuses to overwrite a disagreeing relation,
    # and this layer does not go behind it.
    derivation_id, derivation_created = _persist_derivation(
        conn, derivation, claim_revision_id=revision_id
    )
    evidence_id = _evidence_id(conn, workspace_id, claim_id, decision.signal_id)

    if conflict is not None:
        return PersistenceResult(
            path=PersistencePath.DIRECTIONAL,
            status=PersistenceStatus.REVIEW_REQUIRED,
            claim_id=claim_id,
            claim_revision_id=revision_id,
            derivation_id=derivation_id,
            evidence_id=evidence_id,
            claim_created=claim_created,
            derivation_created=derivation_created,
            evidence_created=False,
            conflict=conflict,
        )

    evidence_created = report.evidence_new == 1
    return PersistenceResult(
        path=PersistencePath.DIRECTIONAL,
        status=PersistenceStatus.PERSISTED
        if (claim_created or derivation_created or evidence_created)
        else PersistenceStatus.REUSED,
        claim_id=claim_id,
        claim_revision_id=revision_id,
        derivation_id=derivation_id,
        evidence_id=evidence_id,
        claim_created=claim_created,
        derivation_created=derivation_created,
        evidence_created=evidence_created,
    )


def _conflict_from(
    conn: Any,
    report: Any,
    outcome: EvaluationOutcome,
    derivation: Any,
    key: str,
    workspace_id: str,
) -> EvidenceDirectionConflict | None:
    """Policy D detection, read off the repository's own report.

    Mission 1.41 already built the refusal: `_persist_evidence` compares the
    load-bearing factors of an existing relation and, on disagreement, records a
    conflict and writes NOTHING. This does not re-implement that comparison --
    two authorities for one question eventually disagree -- it turns the
    repository's finding into a result a caller can branch on.
    """
    if not report.evidence_conflicts:
        return None
    entry = report.evidence_conflicts[0]
    decision = outcome.evidence_decision
    assert decision is not None  # noqa: S101 - directional path only
    return EvidenceDirectionConflict(
        workspace_id=workspace_id,
        claim_id=str(entry["claim_id"]),
        signal_id=str(entry["signal_id"]),
        evidence_id=str(entry["evidence_id"]),
        existing_direction=_stored_direction(conn, workspace_id, entry),
        evaluated_direction=str(decision.direction),
        derivation_rule_id=derivation.derivation_rule_id,
        derivation_rule_version=derivation.derivation_rule_version,
        evaluator_version=derivation.evaluator_version,
        target_proposition_key=key,
        semantic_equivalence_basis_id=derivation.semantic_equivalence_basis_id,
    )


def _stored_direction(conn: Any, workspace_id: str, entry: Mapping[str, object]) -> str:
    """Read from the Evidence row rather than from the report.

    `_persist_evidence` records which relation conflicted and on what
    `extraction_method`, and deliberately does not enumerate the differing
    factors -- so the standing direction has to come from the row itself. A
    placeholder here would put an invented value in front of a reviewer.
    """
    row = conn.execute(
        "SELECT direction FROM scoring.evidence WHERE workspace_id = %s AND id = %s",
        (workspace_id, str(entry["evidence_id"])),
    ).fetchone()
    if row is None:  # pragma: no cover - the report names an existing row
        raise PersistenceError(
            PersistenceErrorCode.INVALID_OUTCOME,
            "the repository reported a conflict against an Evidence row that is not there",
        )
    return str(row[0])


# --------------------------------------------------------------- refusal path


def _persist_refusal(
    conn: Any,
    outcome: EvaluationOutcome,
    facts: Mapping[str, str],
    key: str,
) -> PersistenceResult:
    derivation = outcome.derivation
    if outcome.claim_draft is not None or outcome.evidence_decision is not None:
        raise PersistenceError(
            PersistenceErrorCode.INVALID_OUTCOME,
            "a refusal carries no Claim draft and no Evidence decision. One that does "
            "is not a refusal, and storing it here would hide a directional result",
        )
    if outcome.refusal_reason is None:
        raise PersistenceError(
            PersistenceErrorCode.INVALID_OUTCOME,
            "a refusal names WHY. The result says what happened and the reason code says "
            "why, and migration 0035 requires both",
        )

    workspace_id = derivation.workspace_id
    _require_threshold(conn, workspace_id, derivation.threshold_registration_id)

    # §52. The database stores key and preimage and does not recompute one from
    # the other, so the producer is the only place the two can be checked
    # against each other. A stored pair that disagrees is corrupted provenance.
    if proposition_key(facts) != key:
        raise PersistenceError(  # pragma: no cover - both sides computed here
            PersistenceErrorCode.TARGET_MISMATCH,
            "the target key does not recompute from the target facts",
        )

    payload = {
        "workspace_id": workspace_id,
        "input_signal_id": derivation.input_signal_id,
        "input_observed_claim_id": derivation.input_observed_claim_id,
        "target_proposition_key": key,
        "target_proposition_facts": canonical_json(dict(facts)),
        "derivation_rule_id": derivation.derivation_rule_id,
        "derivation_rule_version": derivation.derivation_rule_version,
        "evaluator_version": derivation.evaluator_version,
        "semantic_equivalence_basis_id": derivation.semantic_equivalence_basis_id,
        "threshold_registration_id": derivation.threshold_registration_id,
        "evaluation_result": outcome.result.value,
        "reason_code": outcome.refusal_reason,
        "interpretation_kind": derivation.interpretation_kind,
        "model_version": derivation.model_version,
        "rationale": derivation.rationale,
    }

    existing = conn.execute(
        """SELECT id, input_observed_claim_id, target_proposition_facts,
                  derivation_rule_id, threshold_registration_id, evaluation_result,
                  reason_code, interpretation_kind, model_version
             FROM research.proposition_evaluation_refusals
            WHERE workspace_id = %s AND input_signal_id = %s
              AND target_proposition_key = %s AND derivation_rule_version = %s
              AND semantic_equivalence_basis_id = %s""",
        (
            workspace_id,
            derivation.input_signal_id,
            key,
            derivation.derivation_rule_version,
            derivation.semantic_equivalence_basis_id,
        ),
    ).fetchone()

    if existing is not None:
        _compare_refusal(existing, payload, facts)
        return PersistenceResult(
            path=PersistencePath.REFUSAL,
            status=PersistenceStatus.REUSED,
            refusal_id=str(existing[0]),
            refusal_created=False,
        )

    refusal_id = str(uuid.uuid4())
    columns = ["id", *payload]
    values = [refusal_id, *payload.values()]
    conn.execute(
        f"INSERT INTO research.proposition_evaluation_refusals ({', '.join(columns)}) "  # noqa: S608
        f"VALUES ({', '.join(['%s'] * len(columns))})",
        tuple(values),
    )
    return PersistenceResult(
        path=PersistencePath.REFUSAL,
        status=PersistenceStatus.PERSISTED,
        refusal_id=refusal_id,
        refusal_created=True,
    )


def _compare_refusal(
    existing: Any, payload: Mapping[str, object], facts: Mapping[str, str]
) -> None:
    """Same identity is not the same evaluation.

    The unique key is narrower than the row, so a replay that matches on the key
    and disagrees on the result, the reason or the threshold is a CONFLICT rather
    than an idempotent no-op. `evaluator_version` is excluded on purpose: it is
    not part of the identity either, and rebuilding the software is not a new
    finding.
    """
    stored = {
        "input_observed_claim_id": None if existing[1] is None else str(existing[1]),
        "derivation_rule_id": str(existing[3]),
        "threshold_registration_id": None if existing[4] is None else str(existing[4]),
        "evaluation_result": str(existing[5]),
        "reason_code": str(existing[6]),
        "interpretation_kind": str(existing[7]),
        "model_version": None if existing[8] is None else str(existing[8]),
    }
    incoming = {name: (None if payload[name] is None else str(payload[name])) for name in stored}
    differing = sorted(name for name in stored if stored[name] != incoming[name])
    if dict(existing[2]) != dict(facts):
        differing.append("target_proposition_facts")
    if differing:
        raise PersistenceError(
            PersistenceErrorCode.REFUSAL_IDEMPOTENCY_CONFLICT,
            f"a refusal with this identity already exists and disagrees on {differing}. "
            "Nothing was written: overwriting it would destroy the evaluation that stood, "
            "and a second row is impossible by construction",
        )


# ------------------------------------------------------------- shared helpers


def _persist_derivation(conn: Any, derivation: Any, *, claim_revision_id: str) -> tuple[str, bool]:
    """Insert or reuse, comparing the payload rather than trusting the key."""
    existing = conn.execute(
        """SELECT id, input_observed_claim_id, measurement_value,
                  threshold_registration_id, evaluation_result,
                  semantic_equivalence_basis_id, interpretation_kind, model_version
             FROM research.claim_derivations
            WHERE workspace_id = %s AND claim_revision_id = %s
              AND input_signal_id = %s AND derivation_rule_version = %s""",
        (
            derivation.workspace_id,
            claim_revision_id,
            derivation.input_signal_id,
            derivation.derivation_rule_version,
        ),
    ).fetchone()

    if existing is not None:
        stored = {
            "input_observed_claim_id": None if existing[1] is None else str(existing[1]),
            "measurement_value": Decimal(str(existing[2])),
            "threshold_registration_id": None if existing[3] is None else str(existing[3]),
            "evaluation_result": str(existing[4]),
            "semantic_equivalence_basis_id": str(existing[5]),
            "interpretation_kind": str(existing[6]),
            "model_version": None if existing[7] is None else str(existing[7]),
        }
        incoming = {
            "input_observed_claim_id": derivation.input_observed_claim_id,
            "measurement_value": derivation.measurement_value,
            "threshold_registration_id": derivation.threshold_registration_id,
            "evaluation_result": derivation.evaluation_result.value,
            "semantic_equivalence_basis_id": derivation.semantic_equivalence_basis_id,
            "interpretation_kind": derivation.interpretation_kind,
            "model_version": derivation.model_version,
        }
        differing = sorted(name for name in stored if stored[name] != incoming[name])
        if differing:
            raise PersistenceError(
                PersistenceErrorCode.DERIVATION_IDEMPOTENCY_CONFLICT,
                f"a derivation with this identity already exists and disagrees on "
                f"{differing}. The identity excludes `evaluator_version` deliberately, so "
                "rebuilding the software is not a new derivation -- but reaching a "
                "different conclusion under the same rule version is a finding, not a "
                "replay",
            )
        return str(existing[0]), False

    derivation_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO research.claim_derivations (
               id, workspace_id, claim_revision_id, input_signal_id,
               input_observed_claim_id, derivation_rule_id, derivation_rule_version,
               evaluator_version, measurement_value, threshold_registration_id,
               evaluation_result, semantic_equivalence_basis_id, interpretation_kind,
               model_version, rationale)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            derivation_id,
            derivation.workspace_id,
            claim_revision_id,
            derivation.input_signal_id,
            derivation.input_observed_claim_id,
            derivation.derivation_rule_id,
            derivation.derivation_rule_version,
            derivation.evaluator_version,
            derivation.measurement_value,
            derivation.threshold_registration_id,
            derivation.evaluation_result.value,
            derivation.semantic_equivalence_basis_id,
            derivation.interpretation_kind,
            derivation.model_version,
            derivation.rationale,
        ),
    )
    return derivation_id, True


def _require_threshold(conn: Any, workspace_id: str, threshold_id: str | None) -> None:
    """Read-only, and in this workspace.

    The orchestrator never creates, selects, upgrades or re-provenances a
    threshold. A missing one is a contract failure the caller has to fix, not
    something to repair by registering the bound this evaluation happened to
    use -- which would be the analyst choosing the number after seeing the
    measurement.
    """
    if threshold_id is None:
        return
    row = conn.execute(
        "SELECT 1 FROM research.threshold_registrations WHERE workspace_id = %s AND id = %s",
        (workspace_id, threshold_id),
    ).fetchone()
    if row is None:
        raise PersistenceError(
            PersistenceErrorCode.THRESHOLD_NOT_FOUND,
            f"threshold registration {threshold_id} does not exist in workspace "
            f"{workspace_id}. The bound an evaluation compared against must be the one "
            "that was frozen, and this layer does not register it on the way past",
        )


def _current_revision_id(conn: Any, workspace_id: str, claim_id: str) -> str:
    row = conn.execute(
        """SELECT r.id FROM research.claim_revisions r
             JOIN research.claims c
               ON c.workspace_id = r.workspace_id AND c.id = r.claim_id
              AND c.current_revision = r.revision
            WHERE r.workspace_id = %s AND r.claim_id = %s""",
        (workspace_id, claim_id),
    ).fetchone()
    if row is None:  # pragma: no cover - persist_claims always writes one
        raise PersistenceError(
            PersistenceErrorCode.INVALID_OUTCOME,
            f"claim {claim_id} has no current revision",
        )
    return str(row[0])


def _verify_stored_proposition(conn: Any, workspace_id: str, claim_id: str, key: str) -> None:
    """A matching key is not enough on its own.

    Two propositions colliding on one sha256 is not the realistic failure; a
    stored preimage that no longer recomputes to its own key is, because it means
    something wrote facts and key from different sources. Attaching new reasoning
    to that Claim would compound it.
    """
    row = conn.execute(
        "SELECT proposition_key, proposition_facts FROM research.claims "
        "WHERE workspace_id = %s AND id = %s",
        (workspace_id, claim_id),
    ).fetchone()
    if row is None:  # pragma: no cover - just written in this transaction
        raise PersistenceError(PersistenceErrorCode.INVALID_OUTCOME, "the claim vanished")
    stored_key, stored_facts = str(row[0]), dict(row[1])
    if stored_key != key or proposition_key(stored_facts) != stored_key:
        raise PersistenceError(
            PersistenceErrorCode.PROPOSITION_IDEMPOTENCY_CONFLICT,
            f"claim {claim_id} matched on proposition key but its stored facts do not "
            "recompute to it. Nothing further was written",
        )


def _evidence_id(conn: Any, workspace_id: str, claim_id: str, signal_id: str) -> str | None:
    row = conn.execute(
        "SELECT id FROM scoring.evidence "
        "WHERE workspace_id = %s AND claim_id = %s AND signal_id = %s",
        (workspace_id, claim_id, signal_id),
    ).fetchone()
    return None if row is None else str(row[0])
