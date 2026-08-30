"""Claim and Evidence persistence.

Mission 1.2 §33–§34. Resolves A-13: evidence aggregation is claim-centric and
until now there was no persisted Claim.

    Workspace -> Opportunity -> Claim -> Evidence

A separate module from `repositories.py` because these two are the aggregation
data model and they are read together; splitting them across the existing file
would have buried them among the lifecycle machinery.

**Same two-layer tenancy rule as every other repository.** Every method takes
`workspace_id` first, filters on it explicitly (layer 1), and runs inside
`tenant_transaction` so the row-level-security policy applies (layer 2). The
composite foreign keys in migration 0005 add a third: a claim cannot reference
an opportunity in another workspace even if both other layers were bypassed.

**Nothing here aggregates.** No score is computed, stored or returned. The
reference engine is not imported: a service that imported it would make an
uncalibrated implementation a runtime dependency (ADR-014). Reading evidence and
aggregating it are different acts, and only the first belongs here.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sros_contracts import (
    ClaimLifecycle,
    ClaimOrigin,
    ClaimTemporality,
    ClaimType,
    ContractError,
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
    ObservationKind,
    WorkspaceId,
)

from .repositories import NotFoundError

__all__ = [
    "ClaimRow",
    "ClaimRepository",
    "EvidenceRepository",
    "ClaimStatementUnchangedError",
]


class ClaimStatementUnchangedError(ContractError):
    """A revision that changes nothing.

    Refused rather than accepted as a no-op: a revision row is a claim that the
    statement was reconsidered, and one that records no change makes the history
    longer without making it more informative.
    """

    def __init__(self) -> None:
        super().__init__("statement", "a revision must change the statement")


@dataclass(frozen=True)
class ClaimRow:
    """A claim as read, with the statement of its current revision joined in."""

    id: uuid.UUID
    workspace_id: uuid.UUID
    opportunity_id: uuid.UUID
    claim_type: str
    lifecycle: str
    withdrawn_reason: str | None
    temporality: str
    claim_feature: str | None
    origin: str
    origin_session_id: uuid.UUID | None
    origin_detail: str | None
    model_version: str | None
    prompt_version: str | None
    created_by: str | None
    current_revision: int
    statement: str
    created_at: datetime
    updated_at: datetime

    def to_json(self) -> dict[str, Any]:
        return {
            "claim_id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "opportunity_id": str(self.opportunity_id),
            "claim_type": self.claim_type,
            "lifecycle": self.lifecycle,
            "withdrawn_reason": self.withdrawn_reason,
            "temporality": self.temporality,
            "claim_feature": self.claim_feature,
            "origin": self.origin,
            "provenance": {
                "origin_session_id": (
                    str(self.origin_session_id) if self.origin_session_id else None
                ),
                "origin_detail": self.origin_detail,
                "model_version": self.model_version,
                "prompt_version": self.prompt_version,
                "created_by": self.created_by,
            },
            "revision": self.current_revision,
            "statement": self.statement,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def _require_workspace(workspace_id: WorkspaceId | uuid.UUID) -> uuid.UUID:
    """No default, no ambient context. ADR-005."""
    if workspace_id is None:
        raise ContractError("workspace_id", "required on every tenant-scoped call")
    return uuid.UUID(str(workspace_id))


def _enum_value(name: str, value: Any, enum: Any) -> str:
    """Accept the enum or its string form; refuse anything else.

    The CHECK constraints in migration 0005 would catch a bad value anyway. This
    catches it earlier, with a message naming the field and the allowed set,
    because a constraint-violation traceback names neither.
    """
    if isinstance(value, enum):
        return str(value.value)
    allowed = {member.value for member in enum}
    if isinstance(value, str) and value in allowed:
        return value
    raise ContractError(name, f"must be one of {sorted(allowed)}, got {value!r}")


_CLAIM_SELECT = """
    SELECT c.id, c.workspace_id, c.opportunity_id, c.claim_type, c.lifecycle,
           c.withdrawn_reason, c.temporality, c.claim_feature, c.origin,
           c.origin_session_id, c.origin_detail, c.model_version, c.prompt_version,
           c.created_by, c.current_revision, r.statement, c.created_at, c.updated_at
      FROM research.claims c
      JOIN research.claim_revisions r
        ON r.workspace_id = c.workspace_id
       AND r.claim_id = c.id
       AND r.revision = c.current_revision
"""


def _row(record: tuple[Any, ...]) -> ClaimRow:
    return ClaimRow(*record)


_EVIDENCE_INSERT = """
INSERT INTO scoring.evidence
       (id, workspace_id, claim_id, research_session_id,
        direction, evidence_level, relevance, directness, reliability,
        extraction_confidence, confidence, observation_category,
        independence_state, independence_group_id, source_id,
        source_reference, extraction_method, model_version, prompt_version,
        observed_at, collected_at, expires_at)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""


def _write_evidence(
    conn: Any,
    ws: uuid.UUID,
    claim_id: uuid.UUID,
    direction: EvidenceDirection | str,
    *,
    evidence_level: int,
    collected_at: datetime,
    expires_at: datetime,
    observation_category: EvidenceObservationCategory | str = (
        EvidenceObservationCategory.UNCATEGORISED
    ),
    independence_state: EvidenceIndependenceState | str = EvidenceIndependenceState.UNKNOWN,
    independence_group_id: uuid.UUID | None = None,
    relevance: float | None = None,
    directness: float | None = None,
    reliability: float | None = None,
    extraction_confidence: float | None = None,
    confidence: float | None = None,
    observed_at: datetime | None = None,
    source_id: str | None = None,
    source_reference: str | None = None,
    extraction_method: str | None = None,
    model_version: str | None = None,
    prompt_version: str | None = None,
    research_session_id: uuid.UUID | None = None,
    evidence_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Validate and insert one evidence row on an OPEN connection.

    Factored out of `EvidenceRepository.create` in Mission 1.13 so that
    `ClaimRepository.create` can write a claim and its evidence in one
    transaction. The evidence requirement for a generated claim is a
    `DEFERRABLE INITIALLY DEFERRED` trigger that fires at COMMIT, so evidence
    arriving in a later transaction is too late by construction
    (`claim-evidence-interpretation-contract-v1.md` §9).
    """
    state = _enum_value("independence_state", independence_state, EvidenceIndependenceState)

    # Checked here as well as by the CHECK constraint, because a constraint
    # violation names the constraint and this names the mistake.
    if state == EvidenceIndependenceState.KNOWN_DEPENDENT.value:
        if independence_group_id is None:
            raise ContractError(
                "independence_group_id",
                "KNOWN_DEPENDENT asserts a dependency on nothing without a group. "
                "Name the group, or record the state as UNKNOWN",
            )
    elif independence_group_id is not None:
        raise ContractError(
            "independence_group_id",
            f"{state} must not name a group: it would claim independence, or an "
            "unresolved question, and membership at the same time",
        )

    for name, value in (
        ("relevance", relevance),
        ("directness", directness),
        ("reliability", reliability),
        ("extraction_confidence", extraction_confidence),
        ("confidence", confidence),
    ):
        if value is not None and not (0.0 <= float(value) <= 1.0):
            raise ContractError(name, f"must be on the unit interval [0,1], got {value!r}")
    if not (0 <= int(evidence_level) <= 5):
        raise ContractError("evidence_level", "must be an integer 0-5")

    new_id = evidence_id or uuid.uuid4()
    conn.execute(
        _EVIDENCE_INSERT,
        (
            new_id,
            ws,
            claim_id,
            research_session_id,
            _enum_value("direction", direction, EvidenceDirection),
            int(evidence_level),
            relevance,
            directness,
            reliability,
            extraction_confidence,
            confidence,
            _enum_value("observation_category", observation_category, EvidenceObservationCategory),
            state,
            independence_group_id,
            source_id,
            source_reference,
            extraction_method,
            model_version,
            prompt_version,
            observed_at,
            collected_at,
            expires_at,
        ),
    )
    return new_id


class ClaimRepository:
    """Claims, their statement revisions, and which sessions met them.

    **The statement is read through a join, never from a column on `claims`.**
    Keeping a copy of the current text beside the history would be one fewer
    join and one more thing that can drift; the history is the only place a
    statement lives, so drift is impossible rather than unlikely.
    """

    def __init__(self, db: Any) -> None:
        self._db = db

    # -- writing -------------------------------------------------------------

    def create(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        opportunity_id: uuid.UUID | None,
        statement: str,
        claim_type: ClaimType | str,
        temporality: ClaimTemporality | str,
        origin: ClaimOrigin | str,
        *,
        evidence: Sequence[Mapping[str, Any]] = (),
        claim_feature: str | None = None,
        origin_session_id: uuid.UUID | None = None,
        origin_detail: str | None = None,
        model_version: str | None = None,
        prompt_version: str | None = None,
        created_by: str | None = None,
        claim_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        """Create a claim and its first revision, atomically.

        `temporality` is required and never inferred. The same platform carries
        an evergreen fact and a trend stale in a week, so guessing from the
        source would be wrong for one of them with no way to tell which
        (evidence-aggregation-framework-v1.md §9).

        The claim and revision reference each other, so the pointer constraint
        is DEFERRABLE and checked at COMMIT — both halves land or neither does.

        `opportunity_id` may be **None** since Mission 1.13 (ADR-024): the
        pipeline runs Signal → Claim → Opportunity, so a claim about a source
        fact exists before anybody has conceived of the product it might justify.

        `evidence` is a sequence of keyword mappings for `_write_evidence`,
        written in **this** transaction. A generated claim that is not a
        HYPOTHESIS needs at least one, and the requirement is a deferred trigger
        firing at COMMIT — so evidence attached afterwards, in a second
        transaction, is too late by construction
        (`claim-evidence-interpretation-contract-v1.md` §9).
        """
        ws = _require_workspace(workspace_id)
        text = statement.strip()
        if not text:
            raise ContractError("statement", "a claim must say something")

        new_id = claim_id or uuid.uuid4()
        with self._db.tenant_transaction(ws) as conn:
            conn.execute(
                """INSERT INTO research.claims
                       (id, workspace_id, opportunity_id, claim_type, temporality,
                        claim_feature, origin, origin_session_id, origin_detail,
                        model_version, prompt_version, created_by, current_revision)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, 1)""",
                (
                    new_id,
                    ws,
                    opportunity_id,
                    _enum_value("claim_type", claim_type, ClaimType),
                    _enum_value("temporality", temporality, ClaimTemporality),
                    claim_feature,
                    _enum_value("origin", origin, ClaimOrigin),
                    origin_session_id,
                    origin_detail,
                    model_version,
                    prompt_version,
                    created_by,
                ),
            )
            conn.execute(
                """INSERT INTO research.claim_revisions
                       (id, workspace_id, claim_id, revision, statement,
                        revision_reason, material_change, created_by, research_session_id)
                   VALUES (%s,%s,%s, 1, %s, 'initial statement', FALSE, %s, %s)""",
                (uuid.uuid4(), ws, new_id, text, created_by, origin_session_id),
            )
            for item in evidence:
                _write_evidence(conn, ws, new_id, **dict(item))
        return new_id

    def revise(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        claim_id: uuid.UUID,
        statement: str,
        *,
        revision_reason: str,
        material_change: bool,
        created_by: str | None = None,
        research_session_id: uuid.UUID | None = None,
    ) -> int:
        """Append a revision and move the pointer. Returns the new revision.

        **The previous revision is not touched.** That is the whole point: an
        aggregation that evaluated revision 2 must still be able to read the
        text of revision 2 years later, or a historical result becomes
        unreproducible (Mission 1.2 §25).

        `material_change` is the author's declaration that the MEANING changed,
        not just the wording. Nothing acts on it automatically — deciding what a
        material change does to already-attached evidence is part of D-08, which
        stays open. It is recorded now because only the person making the edit
        knows, and it cannot be reconstructed afterwards.
        """
        ws = _require_workspace(workspace_id)
        text = statement.strip()
        if not text:
            raise ContractError("statement", "a claim must say something")
        if not revision_reason.strip():
            raise ContractError(
                "revision_reason",
                "required: a revision with no stated reason cannot be reviewed later",
            )

        with self._db.tenant_transaction(ws) as conn:
            current = conn.execute(
                """SELECT c.current_revision, r.statement
                     FROM research.claims c
                     JOIN research.claim_revisions r
                       ON r.workspace_id = c.workspace_id
                      AND r.claim_id = c.id
                      AND r.revision = c.current_revision
                    WHERE c.workspace_id = %s AND c.id = %s
                    FOR UPDATE OF c""",
                (ws, claim_id),
            ).fetchone()
            if current is None:
                raise NotFoundError(f"claim {claim_id} not found in this workspace")
            if current[1] == text:
                raise ClaimStatementUnchangedError

            next_revision = int(current[0]) + 1
            conn.execute(
                """INSERT INTO research.claim_revisions
                       (id, workspace_id, claim_id, revision, statement,
                        revision_reason, material_change, created_by, research_session_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    uuid.uuid4(),
                    ws,
                    claim_id,
                    next_revision,
                    text,
                    revision_reason,
                    material_change,
                    created_by,
                    research_session_id,
                ),
            )
            conn.execute(
                """UPDATE research.claims
                      SET current_revision = %s, updated_at = now()
                    WHERE workspace_id = %s AND id = %s""",
                (next_revision, ws, claim_id),
            )
        return next_revision

    def withdraw(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        claim_id: uuid.UUID,
        reason: str,
    ) -> None:
        """Take a claim out of use without deleting what was believed.

        Editorial, never epistemic. A claim is withdrawn because it was
        malformed, duplicated or out of scope — never because its evidence came
        out badly. Evidence changes, and a lifecycle state derived from evidence
        would freeze a conclusion the evidence no longer supports (§38).
        """
        ws = _require_workspace(workspace_id)
        if not reason.strip():
            raise ContractError(
                "reason",
                "required: a withdrawal with no reason is indistinguishable from an accident",
            )
        with self._db.tenant_transaction(ws) as conn:
            updated = conn.execute(
                """UPDATE research.claims
                      SET lifecycle = %s, withdrawn_reason = %s, updated_at = now()
                    WHERE workspace_id = %s AND id = %s""",
                (ClaimLifecycle.WITHDRAWN.value, reason, ws, claim_id),
            ).rowcount
        if not updated:
            raise NotFoundError(f"claim {claim_id} not found in this workspace")

    def record_observation(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        claim_id: uuid.UUID,
        research_session_id: uuid.UUID,
        observation_kind: ObservationKind | str,
        *,
        notes: str | None = None,
        observation_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        """Record that a session met this claim.

        A claim is NOT owned by the session that first found it, for the same
        reason an Opportunity is not (Ontology V2 §12). Duplicating the claim
        because a second session encountered it would split its evidence in two,
        which is precisely what the aggregation model must not have happen.
        """
        ws = _require_workspace(workspace_id)
        new_id = observation_id or uuid.uuid4()
        with self._db.tenant_transaction(ws) as conn:
            conn.execute(
                """INSERT INTO research.claim_session_observations
                       (id, workspace_id, claim_id, research_session_id,
                        observation_kind, notes)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (
                    new_id,
                    ws,
                    claim_id,
                    research_session_id,
                    _enum_value("observation_kind", observation_kind, ObservationKind),
                    notes,
                ),
            )
        return new_id

    # -- reading -------------------------------------------------------------

    def get(self, workspace_id: WorkspaceId | uuid.UUID, claim_id: uuid.UUID) -> ClaimRow:
        ws = _require_workspace(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            record = conn.execute(
                _CLAIM_SELECT + " WHERE c.workspace_id = %s AND c.id = %s",
                (ws, claim_id),
            ).fetchone()
        if record is None:
            raise NotFoundError(f"claim {claim_id} not found in this workspace")
        return _row(record)

    def list_for_opportunity(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        opportunity_id: uuid.UUID,
        *,
        include_withdrawn: bool = False,
    ) -> list[ClaimRow]:
        """Every claim on one opportunity.

        Withdrawn claims are excluded by default and retrievable on request: a
        listing that silently dropped them would make a withdrawal look like a
        deletion, and the record of what was once believed is worth keeping.
        """
        ws = _require_workspace(workspace_id)
        clause = "" if include_withdrawn else " AND c.lifecycle = 'ACTIVE'"
        with self._db.tenant_transaction(ws) as conn:
            records = conn.execute(
                _CLAIM_SELECT
                + " WHERE c.workspace_id = %s AND c.opportunity_id = %s"
                + clause
                + " ORDER BY c.created_at",
                (ws, opportunity_id),
            ).fetchall()
        return [_row(record) for record in records]

    def revisions(
        self, workspace_id: WorkspaceId | uuid.UUID, claim_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        """The full statement history, oldest first."""
        ws = _require_workspace(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            records = conn.execute(
                """SELECT revision, statement, revision_reason, material_change,
                          created_at, created_by, research_session_id
                     FROM research.claim_revisions
                    WHERE workspace_id = %s AND claim_id = %s
                    ORDER BY revision""",
                (ws, claim_id),
            ).fetchall()
        return [
            {
                "revision": r[0],
                "statement": r[1],
                "revision_reason": r[2],
                "material_change": r[3],
                "created_at": r[4],
                "created_by": r[5],
                "research_session_id": r[6],
            }
            for r in records
        ]

    def statement_at(
        self, workspace_id: WorkspaceId | uuid.UUID, claim_id: uuid.UUID, revision: int
    ) -> str:
        """The exact text a given revision carried.

        What makes a historical aggregation re-readable: a stored result names a
        revision, and this returns what that revision said — not what the claim
        says now (§25).
        """
        ws = _require_workspace(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            record = conn.execute(
                """SELECT statement FROM research.claim_revisions
                    WHERE workspace_id = %s AND claim_id = %s AND revision = %s""",
                (ws, claim_id, revision),
            ).fetchone()
        if record is None:
            raise NotFoundError(f"claim {claim_id} has no revision {revision} in this workspace")
        return str(record[0])

    def observations(
        self, workspace_id: WorkspaceId | uuid.UUID, claim_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        ws = _require_workspace(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            records = conn.execute(
                """SELECT id, research_session_id, observation_kind, notes, observed_at
                     FROM research.claim_session_observations
                    WHERE workspace_id = %s AND claim_id = %s
                    ORDER BY observed_at DESC""",
                (ws, claim_id),
            ).fetchall()
        return [
            {
                "id": r[0],
                "research_session_id": r[1],
                "observation_kind": r[2],
                "notes": r[3],
                "observed_at": r[4],
            }
            for r in records
        ]


class EvidenceRepository:
    """Evidence attached to a claim, and the provenance groups among it.

    **Reads and writes only.** No aggregation happens here and the reference
    engine is not imported. The rows this returns are the INPUT to aggregation;
    turning them into a score is a separate act that needs a calibrated profile
    (ADR-014, evidence-aggregation-framework-v1.md §14).
    """

    def __init__(self, db: Any) -> None:
        self._db = db

    def create_independence_group(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        claim_id: uuid.UUID,
        *,
        basis: str,
        detection_method: str,
        origin_reference: str | None = None,
        created_by: str | None = None,
        group_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        """Declare that some records share an underlying information origin.

        Not "came from the same website". Two independent posts on one platform
        are two observations; one announcement repeated by a blog and linked
        from a forum is three records and one observation.

        `basis` is mandatory. Grouping is the operation with the largest single
        effect on a result — it collapses several records into one contribution —
        and one with no stated reason cannot be re-checked.
        """
        ws = _require_workspace(workspace_id)
        if not basis.strip():
            raise ContractError(
                "basis", "required: a grouping nobody can re-check should not collapse evidence"
            )
        if not detection_method.strip():
            raise ContractError("detection_method", "required")
        new_id = group_id or uuid.uuid4()
        with self._db.tenant_transaction(ws) as conn:
            conn.execute(
                """INSERT INTO scoring.evidence_independence_groups
                       (id, workspace_id, claim_id, basis, origin_reference,
                        detection_method, created_by)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (new_id, ws, claim_id, basis, origin_reference, detection_method, created_by),
            )
        return new_id

    def create(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        claim_id: uuid.UUID,
        direction: EvidenceDirection | str,
        *,
        evidence_level: int,
        collected_at: datetime,
        expires_at: datetime,
        observation_category: EvidenceObservationCategory | str = (
            EvidenceObservationCategory.UNCATEGORISED
        ),
        independence_state: EvidenceIndependenceState | str = EvidenceIndependenceState.UNKNOWN,
        independence_group_id: uuid.UUID | None = None,
        relevance: float | None = None,
        directness: float | None = None,
        reliability: float | None = None,
        extraction_confidence: float | None = None,
        confidence: float | None = None,
        observed_at: datetime | None = None,
        source_id: str | None = None,
        source_reference: str | None = None,
        extraction_method: str | None = None,
        model_version: str | None = None,
        prompt_version: str | None = None,
        research_session_id: uuid.UUID | None = None,
        evidence_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        """Attach one evidence record to a claim.

        `claim_id` is required, not optional. Evidence bears on a CLAIM: one
        opportunity carries many claims, some contradicted while others are well
        supported, and attaching evidence at the opportunity level would average
        away exactly what the aggregation model preserves (Mission 1.1 I-2).

        The unit-interval factors are all optional, and a missing one is NOT
        given a default. Aggregation reports such a record non-scorable and
        names the field. An unknown number stays unknown
        (evidence-aggregation-framework-v1.md §6).

        **`claim_type` was removed in Mission 1.13** (migration 0016, GAP-7). It
        duplicated `research.claims.claim_type`, and two answers to one question
        eventually disagree. Read it from the claim.

        This writes into its OWN transaction, so it cannot satisfy the evidence
        requirement for a claim being created — that trigger fires at the claim's
        commit, before this method could run. Pass `evidence=` to
        `ClaimRepository.create` for a generated claim
        (`claim-evidence-interpretation-contract-v1.md` §9).
        """
        ws = _require_workspace(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            return _write_evidence(
                conn,
                ws,
                claim_id,
                direction,
                evidence_level=evidence_level,
                collected_at=collected_at,
                expires_at=expires_at,
                observation_category=observation_category,
                independence_state=independence_state,
                independence_group_id=independence_group_id,
                relevance=relevance,
                directness=directness,
                reliability=reliability,
                extraction_confidence=extraction_confidence,
                confidence=confidence,
                observed_at=observed_at,
                source_id=source_id,
                source_reference=source_reference,
                extraction_method=extraction_method,
                model_version=model_version,
                prompt_version=prompt_version,
                research_session_id=research_session_id,
                evidence_id=evidence_id,
            )

    def list_for_claim(
        self, workspace_id: WorkspaceId | uuid.UUID, claim_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        """Every evidence record on a claim, in a stable order.

        Ordered by id rather than by time so two reads of an unchanged claim
        return the same sequence. Aggregation is order-independent by
        construction, but a stable read order makes a diff between two snapshots
        legible to a human.
        """
        ws = _require_workspace(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            records = conn.execute(
                """SELECT id, claim_id, direction, relevance, directness, reliability,
                          extraction_confidence, confidence, observation_category,
                          independence_state, independence_group_id, evidence_level,
                          source_id, source_reference, extraction_method,
                          model_version, prompt_version, observed_at, collected_at,
                          expires_at, research_session_id
                     FROM scoring.evidence
                    WHERE workspace_id = %s AND claim_id = %s
                    ORDER BY id""",
                (ws, claim_id),
            ).fetchall()
        return [
            {
                "evidence_id": str(r[0]),
                "claim_id": str(r[1]),
                "direction": r[2],
                "relevance": r[3],
                "directness": r[4],
                "reliability": r[5],
                "extraction_confidence": r[6],
                "confidence": r[7],
                "observation_category": r[8],
                "independence_state": r[9],
                "independence_group_id": str(r[10]) if r[10] else None,
                "evidence_level": r[11],
                "source_id": r[12],
                "source_reference": r[13],
                "extraction_method": r[14],
                "model_version": r[15],
                "prompt_version": r[16],
                "observed_at": r[17],
                "collected_at": r[18],
                "expires_at": r[19],
                "research_session_id": str(r[20]) if r[20] else None,
            }
            for r in records
        ]

    def independence_groups(
        self, workspace_id: WorkspaceId | uuid.UUID, claim_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        ws = _require_workspace(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            records = conn.execute(
                """SELECT id, basis, origin_reference, detection_method, created_at, created_by
                     FROM scoring.evidence_independence_groups
                    WHERE workspace_id = %s AND claim_id = %s
                    ORDER BY created_at, id""",
                (ws, claim_id),
            ).fetchall()
        return [
            {
                "group_id": str(r[0]),
                "basis": r[1],
                "origin_reference": r[2],
                "detection_method": r[3],
                "created_at": r[4],
                "created_by": r[5],
            }
            for r in records
        ]
