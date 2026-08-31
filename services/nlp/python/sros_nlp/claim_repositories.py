"""Reading Signals with their lineage, and writing Claims, Evidence and runs.

`claim-interpretation-runtime-v1.md` §5. Mission 1.13.1.

Three outcomes per claim, mirroring the signal layer's three:

    NEW         the first time this proposition was stored
    UNCHANGED   this proposition is stored and its statement is byte-identical.
                Nothing is written -- what makes redelivery safe
    REVISED     this proposition is stored with a DIFFERENT statement. A new
                revision is appended and the pointer moves

`REVISED` is where this layer differs from `persist_signals`, and deliberately.
A signal whose fingerprint is stored with different content is a CONFLICT: the
extractor is not deterministic and the stored row stands. A claim is not that,
because the proposition key is over the facts the proposition asserts and **not
over the magnitude** (`claim-evidence-interpretation-contract-v1.md` §5.2). So a
source revising 187,180 to 187,200 is the SAME proposition worded differently,
and appending a revision is exactly the mechanism for it. Revision 1 is never
modified: an aggregation that evaluated revision N must still read revision N.

**Claim, revision and evidence are written in ONE transaction.** Not a
preference: `research.require_evidence_for_generated_claim` is a
`DEFERRABLE INITIALLY DEFERRED` constraint trigger that fires at COMMIT, so
evidence arriving in a second transaction is too late by construction (§20).

**Writes go through a tenant transaction.** The explicit `workspace_id` filter
is layer one, RLS is layer two (ADR-012), and the composite foreign keys are
layer three. None replaces another.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sros_claim_model import ClaimDraft, canonical_json
from sros_contracts import ClaimInterpretationInputRole, SignalDirection

from .interpreters import OBSERVED_EVIDENCE_LEVEL, SignalLineage, SignalView

__all__ = [
    "ClaimOutcome",
    "ClaimPersistenceReport",
    "ConsideredSignal",
    "InterpretationRunRecord",
    "count_claims",
    "persist_claims",
    "persist_considered",
    "persist_interpretation_run",
    "read_signal_views",
]

_SIGNAL_COLUMNS = (
    "s.id, s.signal_type_id, s.magnitude, s.magnitude_kind, s.magnitude_unit, "
    "s.magnitude_unit_state, s.direction, s.derivation_confidence, s.extractor_id, "
    "s.extractor_version, s.scope, s.temporal_basis, s.temporal_window, src.canonical_name"
)


class ClaimOutcome(StrEnum):
    NEW = "NEW"
    UNCHANGED = "UNCHANGED"
    REVISED = "REVISED"


@dataclass
class ClaimPersistenceReport:
    new: int = 0
    unchanged: int = 0
    revised: int = 0
    evidence_new: int = 0
    evidence_unchanged: int = 0
    claim_ids: tuple[str, ...] = ()
    # Which claim each Signal ended up in, so the run's considered-inputs can
    # name it without a second lookup.
    claim_by_signal: dict[str, str] = field(default_factory=dict)

    @property
    def revisions_created(self) -> int:
        """Revision 1 for a new claim, revision N+1 for a revised one."""
        return self.new + self.revised

    def to_json(self) -> dict[str, object]:
        return {
            "claims_new": self.new,
            "claims_unchanged": self.unchanged,
            "claims_revised": self.revised,
            "revisions_created": self.revisions_created,
            "evidence_new": self.evidence_new,
            "evidence_unchanged": self.evidence_unchanged,
            "claim_ids": list(self.claim_ids),
        }


@dataclass(frozen=True)
class ConsideredSignal:
    """GAP-5. One Signal a run looked at, and what became of it.

    A row of `research.claim_interpretation_inputs`. `EXCLUDED` was never
    attempted; `REFUSED` was attempted and the model rejected the draft.
    Collapsing the two loses which of them happened.
    """

    signal_id: str
    signal_type_id: str
    role: ClaimInterpretationInputRole
    claim_id: str | None = None
    reason_code: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class InterpretationRunRecord:
    """One interpreter EXECUTION, not one logical job.

    Delivery is at-least-once (ADR-004), so a redelivery writes a second run row
    while writing zero new claims. That is the honest record: the CLAIMS are
    what is idempotent.
    """

    workspace_id: str
    interpreter_id: str
    interpreter_version: str
    interpretation_kind: str
    correlation_id: str
    started_at: datetime
    finished_at: datetime
    expires_at: datetime
    research_session_id: str | None = None
    signals_considered: int = 0
    signals_cited: int = 0
    signals_excluded: int = 0
    signals_refused: int = 0
    claims_new: int = 0
    claims_unchanged: int = 0
    revisions_created: int = 0
    evidence_new: int = 0
    evidence_unchanged: int = 0
    refusals: tuple[dict[str, object], ...] = ()
    truncated_by: str | None = None

    def to_json(self) -> dict[str, object]:
        return {
            "interpreter": f"{self.interpreter_id}@{self.interpreter_version}",
            "interpretation_kind": self.interpretation_kind,
            "signals_considered": self.signals_considered,
            "signals_cited": self.signals_cited,
            "signals_excluded": self.signals_excluded,
            "signals_refused": self.signals_refused,
            "claims_new": self.claims_new,
            "claims_unchanged": self.claims_unchanged,
            "revisions_created": self.revisions_created,
            "evidence_new": self.evidence_new,
            "evidence_unchanged": self.evidence_unchanged,
            "refusals": [dict(r) for r in self.refusals],
            "truncated_by": self.truncated_by,
        }


# ------------------------------------------------------------------- reading


def read_signal_views(
    conn: Any,
    workspace_id: str,
    *,
    signal_ids: Sequence[str] | None = None,
    signal_type_ids: Sequence[str] | None = None,
    research_session_id: str | None = None,
    limit: int = 200,
) -> list[SignalView]:
    """Signals with their lineage, in a stable order.

    The lineage join reaches `acquisition.normalized_records` for the
    **attribution facts the Signal's scope does not carry** -- the published
    resource, the source's own geography name, the term scheme. Not for the
    proposition: what is asserted comes from the Signal (§44). It never reaches
    `acquisition.raw_records`.

    `registry.sources` is joined for the canonical display name. The registry is
    global and SELECT-only for the runtime role, so this is a read of reference
    data rather than of another tenant's rows.

    `limit` is our own bound and is always applied. "The caller will pass one"
    is not a bound; the default is.
    """
    clauses = ["s.workspace_id = %s"]
    params: list[Any] = [workspace_id]
    if signal_ids:
        clauses.append("s.id = ANY(%s::uuid[])")
        params.append(list(signal_ids))
    if signal_type_ids:
        clauses.append("s.signal_type_id = ANY(%s)")
        params.append(list(signal_type_ids))
    if research_session_id:
        clauses.append("s.research_session_id = %s")
        params.append(research_session_id)
    params.append(limit)

    # The interpolated parts are the column list and the clause TEMPLATES, both
    # literals in this module. Every caller-supplied value is a bound parameter.
    rows = conn.execute(
        f"SELECT {_SIGNAL_COLUMNS} "  # noqa: S608 - see above
        "FROM nlp.signals s "
        "LEFT JOIN registry.sources src ON src.id = ("
        "    SELECT i.source_id FROM nlp.signal_inputs i "
        "    WHERE i.workspace_id = s.workspace_id AND i.signal_id = s.id "
        "    ORDER BY i.input_position LIMIT 1) "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY s.signal_type_id, s.derivation_fingerprint LIMIT %s",
        tuple(params),
    ).fetchall()
    if not rows:
        return []

    ids = [str(row[0]) for row in rows]
    lineage = _read_lineage(conn, workspace_id, ids)
    return [_signal_view(row, lineage.get(str(row[0]), ())) for row in rows]


def _read_lineage(
    conn: Any, workspace_id: str, signal_ids: Sequence[str]
) -> dict[str, tuple[SignalLineage, ...]]:
    rows = conn.execute(
        """SELECT i.signal_id, i.normalized_record_id, i.raw_record_id, i.source_id,
                  i.observation_key, i.record_kind_id, i.period_label, i.role, n.payload
             FROM nlp.signal_inputs i
             LEFT JOIN acquisition.normalized_records n
                    ON n.workspace_id = i.workspace_id AND n.id = i.normalized_record_id
            WHERE i.workspace_id = %s AND i.signal_id = ANY(%s::uuid[])
            ORDER BY i.signal_id, i.input_position""",
        (workspace_id, list(signal_ids)),
    ).fetchall()
    grouped: dict[str, list[SignalLineage]] = {}
    for row in rows:
        grouped.setdefault(str(row[0]), []).append(
            SignalLineage(
                normalized_record_id=str(row[1]),
                raw_record_id=str(row[2]),
                source_id=str(row[3]),
                observation_key=str(row[4]),
                record_kind_id=str(row[5]),
                period_label=None if row[6] is None else str(row[6]),
                role=str(row[7]),
                payload=row[8] or {},
            )
        )
    return {key: tuple(value) for key, value in grouped.items()}


def _signal_view(row: Sequence[Any], lineage: tuple[SignalLineage, ...]) -> SignalView:
    return SignalView(
        signal_id=str(row[0]),
        signal_type_id=str(row[1]),
        source_ids=tuple(sorted({item.source_id for item in lineage})),
        # Exact, from the numeric column. Never through float: a magnitude that
        # passed through a binary double is not the magnitude the extractor
        # computed.
        magnitude=Decimal(str(row[2])),
        magnitude_kind=str(row[3]),
        magnitude_unit=None if row[4] is None else str(row[4]),
        magnitude_unit_state=str(row[5]),
        direction=SignalDirection(str(row[6])),
        derivation_confidence=float(row[7]),
        extractor_id=str(row[8]),
        extractor_version=str(row[9]),
        scope=row[10] or {},
        source_name=None if row[13] is None else str(row[13]),
        temporal_basis=str(row[11]),
        temporal_window=row[12] or {},
        inputs=lineage,
    )


def count_claims(conn: Any, workspace_id: str) -> int:
    row = conn.execute(
        "SELECT count(*) FROM research.claims WHERE workspace_id = %s", (workspace_id,)
    ).fetchone()
    return int(row[0]) if row else 0


# ------------------------------------------------------------------- writing


def persist_claims(conn: Any, drafts: Sequence[ClaimDraft]) -> ClaimPersistenceReport:
    """Write a batch of claims with their revisions and evidence."""
    report = ClaimPersistenceReport()
    ids: list[str] = []
    for draft in drafts:
        outcome, claim_id = _persist_one(conn, draft, report)
        if outcome is ClaimOutcome.NEW:
            report.new += 1
        elif outcome is ClaimOutcome.UNCHANGED:
            report.unchanged += 1
        else:
            report.revised += 1
        ids.append(claim_id)
        for item in draft.evidence:
            report.claim_by_signal[item.signal_id] = claim_id
    report.claim_ids = tuple(ids)
    return report


def _persist_one(
    conn: Any, draft: ClaimDraft, report: ClaimPersistenceReport
) -> tuple[ClaimOutcome, str]:
    existing = conn.execute(
        """SELECT c.id, c.current_revision, r.statement
             FROM research.claims c
             JOIN research.claim_revisions r
               ON r.workspace_id = c.workspace_id AND r.claim_id = c.id
              AND r.revision = c.current_revision
            WHERE c.workspace_id = %s AND c.proposition_key = %s""",
        (draft.workspace_id, draft.proposition_key),
    ).fetchone()

    if existing is not None:
        claim_id, revision, statement = str(existing[0]), int(existing[1]), str(existing[2])
        if statement == draft.statement:
            # A redelivery writes NOTHING. Idempotent persistence, without a
            # claim of exactly-once delivery -- which Celery does not provide.
            _persist_evidence(conn, draft, claim_id, report)
            return ClaimOutcome.UNCHANGED, claim_id
        _append_revision(conn, draft, claim_id, revision + 1)
        _persist_evidence(conn, draft, claim_id, report)
        return ClaimOutcome.REVISED, claim_id

    claim_id = str(uuid.uuid4())
    interpretation = draft.interpretation
    conn.execute(
        """INSERT INTO research.claims (
               id, workspace_id, opportunity_id, claim_type, temporality, claim_feature,
               origin, origin_session_id, origin_detail,
               interpreter_id, interpreter_version, interpretation_kind,
               model_version, prompt_version,
               proposition_key, proposition_facts, created_by, current_revision)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, 1)""",
        (
            claim_id,
            draft.workspace_id,
            # NULL, always, and this is the point of ADR-024: the pipeline runs
            # Signal -> Claim -> Opportunity, and no Opportunity exists.
            draft.opportunity_id,
            draft.claim_type.value,
            draft.temporality.value,
            draft.claim_feature,
            draft.origin.value,
            draft.research_session_id,
            draft.rationale,
            interpretation.interpreter_id if interpretation else None,
            interpretation.interpreter_version if interpretation else None,
            interpretation.kind.value if interpretation else None,
            interpretation.model_version if interpretation else None,
            interpretation.prompt_version if interpretation else None,
            draft.proposition_key,
            # The preimage of the key, so the identity can be verified and
            # explained rather than merely trusted (migration 0018).
            canonical_json(dict(draft.cited_facts)),
            f"{interpretation.interpreter_id}@{interpretation.interpreter_version}"
            if interpretation
            else None,
        ),
    )
    _append_revision(conn, draft, claim_id, 1, initial=True)
    _persist_evidence(conn, draft, claim_id, report)
    return ClaimOutcome.NEW, claim_id


def _append_revision(
    conn: Any, draft: ClaimDraft, claim_id: str, revision: int, *, initial: bool = False
) -> None:
    """Append-only. The previous revision is never modified."""
    conn.execute(
        """INSERT INTO research.claim_revisions (
               id, workspace_id, claim_id, revision, statement, revision_reason,
               material_change, created_by, research_session_id, interpretation_confidence)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            str(uuid.uuid4()),
            draft.workspace_id,
            claim_id,
            revision,
            draft.statement,
            "initial statement"
            if initial
            else "the source's reported magnitude changed under an unchanged proposition",
            # A restated magnitude changes what the sentence says, which is
            # material by any reading. Revision 1 is not a change.
            not initial,
            draft.interpretation.interpreter_id if draft.interpretation else None,
            draft.research_session_id,
            draft.interpretation_confidence,
        ),
    )
    if not initial:
        conn.execute(
            """UPDATE research.claims
                  SET current_revision = %s, updated_at = now()
                WHERE workspace_id = %s AND id = %s""",
            (revision, draft.workspace_id, claim_id),
        )


def _persist_evidence(
    conn: Any, draft: ClaimDraft, claim_id: str, report: ClaimPersistenceReport
) -> None:
    """One row per cited Signal, in THIS transaction.

    Idempotent on `(workspace_id, claim_id, signal_id)`: a redelivery finds the
    row and writes nothing. There is no unique constraint behind that -- a claim
    may legitimately carry two records citing one Signal when a human adds one --
    so the check is the interpreter's, over the rows it generated.
    """
    for item in draft.evidence:
        existing = conn.execute(
            """SELECT id FROM scoring.evidence
                WHERE workspace_id = %s AND claim_id = %s AND signal_id = %s
                  AND extraction_method = %s""",
            (draft.workspace_id, claim_id, item.signal_id, _extraction_method(draft)),
        ).fetchone()
        if existing is not None:
            report.evidence_unchanged += 1
            continue
        conn.execute(
            """INSERT INTO scoring.evidence (
                   id, workspace_id, claim_id, signal_id, research_session_id,
                   direction, evidence_level, relevance, directness, reliability,
                   extraction_confidence, observation_category, independence_state,
                   independence_group_id, source_id, extraction_method,
                   model_version, prompt_version, observed_at, collected_at, expires_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                       now(), now() + interval '365 days')""",
            (
                str(uuid.uuid4()),
                draft.workspace_id,
                claim_id,
                item.signal_id,
                draft.research_session_id,
                item.direction.value,
                OBSERVED_EVIDENCE_LEVEL,
                item.relevance,
                item.directness,
                # NULL. Purpose-relative and D-03 is blocked; the record is
                # NON_SCORABLE with MISSING_RELIABILITY, honestly.
                item.reliability,
                item.extraction_confidence,
                item.observation_category.value,
                item.independence_state.value,
                item.independence_group_id,
                item.source_id,
                _extraction_method(draft),
                # A DETERMINISTIC interpretation names no model, and the claim's
                # own CHECK refuses one that does.
                None,
                None,
                # NULL, deliberately. `observed_at` is a globally comparable
                # instant, and H-29 leaves the GDELT bucket without one. Setting
                # it from the claim's creation time would date the evidence to
                # when we looked (`normalized-record-v1.md`, ADR-019).
                None,
            ),
        )
        report.evidence_new += 1


def _extraction_method(draft: ClaimDraft) -> str:
    interpretation = draft.interpretation
    if interpretation is None:  # pragma: no cover -- refused before persistence
        return "unknown"
    return f"{interpretation.interpreter_id}@{interpretation.interpreter_version}"


def persist_interpretation_run(conn: Any, run: InterpretationRunRecord) -> str:
    """The run record, written in the same transaction as its claims.

    A random id, deliberately: this is an EVENT. Two executions of one logical
    job are two things that happened, and a deterministic id would silently
    overwrite the first with the second.
    """
    run_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO research.claim_interpretation_runs (
               id, workspace_id, research_session_id,
               interpreter_id, interpreter_version, interpretation_kind,
               signals_considered, signals_cited, signals_excluded, signals_refused,
               claims_new, claims_unchanged, revisions_created,
               evidence_new, evidence_unchanged,
               refusals, truncated_by, correlation_id,
               started_at, finished_at, expires_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            run_id,
            run.workspace_id,
            run.research_session_id,
            run.interpreter_id,
            run.interpreter_version,
            run.interpretation_kind,
            run.signals_considered,
            run.signals_cited,
            run.signals_excluded,
            run.signals_refused,
            run.claims_new,
            run.claims_unchanged,
            run.revisions_created,
            run.evidence_new,
            run.evidence_unchanged,
            canonical_json([dict(r) for r in run.refusals]),
            run.truncated_by,
            run.correlation_id,
            run.started_at,
            run.finished_at,
            run.expires_at,
        ),
    )
    return run_id


def persist_considered(
    conn: Any, workspace_id: str, run_id: str, considered: Sequence[ConsideredSignal]
) -> int:
    """GAP-5: every Signal the run looked at, with its role and why.

    Written for CITED Signals too, not only the passed-over ones. A table that
    held only exclusions could say what was skipped and not what the denominator
    was, and the denominator is the finding.
    """
    for position, item in enumerate(considered):
        conn.execute(
            """INSERT INTO research.claim_interpretation_inputs (
                   id, workspace_id, run_id, signal_id, signal_type_id,
                   role, claim_id, reason_code, detail, input_position)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                str(uuid.uuid4()),
                workspace_id,
                run_id,
                item.signal_id,
                item.signal_type_id,
                item.role.value,
                item.claim_id,
                item.reason_code,
                item.detail,
                position,
            ),
        )
    return len(considered)
