"""Repositories.

Explicit repositories around domain resources, not a generic ORM abstraction
(ADR-011).

**The rule that matters:** every tenant-scoped method takes `workspace_id` as a
required first argument and puts it in the WHERE clause. There is no default,
no ambient context, and no session-scoped tenant. A method that could be called
without a workspace will eventually be called without one, and in a
multi-tenant system that is a data leak rather than a bug (ADR-005).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sros_contracts import (
    ContractError,
    MarketScope,
    ResearchContext,
    ResearchSessionStatus,
    WorkspaceId,
)

__all__ = [
    "WorkspaceRepository",
    "ResearchProjectRepository",
    "ResearchSessionRepository",
    "OpportunityRepository",
    "ResearchProjectRow",
    "ResearchSessionRow",
    "NotFoundError",
    "InvalidTransitionError",
    "ALLOWED_TRANSITIONS",
    "OBSERVATION_KINDS",
]


class NotFoundError(LookupError):
    """A resource does not exist *within the requested workspace*.

    Deliberately indistinguishable from "exists in another workspace": telling
    a caller that an id exists elsewhere is itself a cross-tenant disclosure.
    """


class InvalidTransitionError(ValueError):
    """A ResearchSession status transition that Ontology V2 §15 does not allow."""


# Ontology V2 §15. No state is invented here; this is the authorized lifecycle.
ALLOWED_TRANSITIONS: dict[ResearchSessionStatus, frozenset[ResearchSessionStatus]] = {
    ResearchSessionStatus.PENDING: frozenset(
        {
            ResearchSessionStatus.PLANNING,
            ResearchSessionStatus.CANCELLED,
            ResearchSessionStatus.FAILED,
        }
    ),
    ResearchSessionStatus.PLANNING: frozenset(
        {
            ResearchSessionStatus.COLLECTING,
            ResearchSessionStatus.CANCELLED,
            ResearchSessionStatus.FAILED,
        }
    ),
    ResearchSessionStatus.COLLECTING: frozenset(
        {
            ResearchSessionStatus.ANALYZING,
            ResearchSessionStatus.CANCELLED,
            ResearchSessionStatus.FAILED,
        }
    ),
    ResearchSessionStatus.ANALYZING: frozenset(
        {
            ResearchSessionStatus.SCORING,
            ResearchSessionStatus.CANCELLED,
            ResearchSessionStatus.FAILED,
        }
    ),
    # SCORING may reach COMPLETED even with partial coverage: budget exhaustion
    # is COMPLETED with reduced Research Completeness, never FAILED
    # (Ontology V2 §15, ADR-006).
    ResearchSessionStatus.SCORING: frozenset(
        {
            ResearchSessionStatus.COMPLETED,
            ResearchSessionStatus.CANCELLED,
            ResearchSessionStatus.FAILED,
        }
    ),
    # Terminal.
    ResearchSessionStatus.COMPLETED: frozenset(),
    ResearchSessionStatus.FAILED: frozenset(),
    ResearchSessionStatus.CANCELLED: frozenset(),
}

# From the authoritative schema CHECK constraint. Not extended here.
OBSERVATION_KINDS = frozenset({"DISCOVERED", "CORROBORATED", "CONTRADICTED"})


@dataclass(frozen=True)
class ResearchProjectRow:
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ResearchSessionRow:
    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: uuid.UUID
    status: ResearchSessionStatus
    research_context: dict[str, Any]
    research_context_hash: str
    research_context_schema_version: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    research_completeness_score: int | None


def _require_workspace(workspace_id: object) -> uuid.UUID:
    """Fail closed. Called at the top of every tenant-scoped method."""
    if workspace_id is None or workspace_id == "":
        raise ContractError(
            "workspace_id",
            "a tenant-scoped repository call requires an explicit workspace_id; "
            "there is no default (ADR-005)",
        )
    if isinstance(workspace_id, uuid.UUID):
        return workspace_id
    return uuid.UUID(str(workspace_id))


class WorkspaceRepository:
    def __init__(self, db: Any) -> None:
        self._db = db

    def exists(self, workspace_id: WorkspaceId | uuid.UUID) -> bool:
        ws = _require_workspace(workspace_id)
        with self._db.connection() as conn:
            row = conn.execute("SELECT 1 FROM core.workspaces WHERE id = %s", (ws,)).fetchone()
        return row is not None

    def get_slug(self, workspace_id: WorkspaceId | uuid.UUID) -> str:
        ws = _require_workspace(workspace_id)
        with self._db.connection() as conn:
            row = conn.execute("SELECT slug FROM core.workspaces WHERE id = %s", (ws,)).fetchone()
        if row is None:
            raise NotFoundError(f"workspace {ws} does not exist")
        return str(row[0])


class ResearchProjectRepository:
    def __init__(self, db: Any) -> None:
        self._db = db

    def create(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        name: str,
        description: str | None = None,
        project_id: uuid.UUID | None = None,
    ) -> ResearchProjectRow:
        ws = _require_workspace(workspace_id)
        if not name.strip():
            raise ContractError("name", "a research project requires a name")
        new_id = project_id or uuid.uuid4()
        with self._db.transaction() as conn:
            row = conn.execute(
                """INSERT INTO research.research_projects
                       (id, workspace_id, name, description)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id, workspace_id, name, description, created_at, updated_at""",
                (new_id, ws, name, description),
            ).fetchone()
        return ResearchProjectRow(*row)

    def list(
        self, workspace_id: WorkspaceId | uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[ResearchProjectRow]:
        ws = _require_workspace(workspace_id)
        with self._db.connection() as conn:
            rows = conn.execute(
                """SELECT id, workspace_id, name, description, created_at, updated_at
                   FROM research.research_projects
                   WHERE workspace_id = %s
                   ORDER BY created_at DESC
                   LIMIT %s OFFSET %s""",
                (ws, limit, offset),
            ).fetchall()
        return [ResearchProjectRow(*row) for row in rows]

    def get(
        self, workspace_id: WorkspaceId | uuid.UUID, project_id: uuid.UUID
    ) -> ResearchProjectRow:
        ws = _require_workspace(workspace_id)
        with self._db.connection() as conn:
            row = conn.execute(
                """SELECT id, workspace_id, name, description, created_at, updated_at
                   FROM research.research_projects
                   WHERE workspace_id = %s AND id = %s""",
                (ws, project_id),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"research project {project_id} not found in this workspace")
        return ResearchProjectRow(*row)


class ResearchSessionRepository:
    def __init__(self, db: Any) -> None:
        self._db = db

    def create(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        project_id: uuid.UUID,
        context: ResearchContext,
        contract_version: str,
        ontology_version: str,
        session_id: uuid.UUID | None = None,
    ) -> ResearchSessionRow:
        """Create the execution record. Does NOT execute research.

        The ResearchContext is canonicalized and snapshotted here, once. It is
        never updated afterwards: a new specification means a new session
        (Ontology V2 §11.3).

        The project lookup and the insert share one transaction, so a project
        deleted concurrently cannot leave an orphan session.
        """
        ws = _require_workspace(workspace_id)
        new_id = session_id or uuid.uuid4()

        with self._db.transaction() as conn:
            project = conn.execute(
                "SELECT 1 FROM research.research_projects WHERE workspace_id = %s AND id = %s",
                (ws, project_id),
            ).fetchone()
            if project is None:
                raise NotFoundError(f"research project {project_id} not found in this workspace")

            budget = context.budget_constraints
            row = conn.execute(
                """INSERT INTO research.research_sessions (
                       id, workspace_id, project_id,
                       research_context, research_context_hash,
                       research_context_schema_version,
                       status,
                       budget_max_cost_units, budget_max_llm_calls,
                       contract_version, ontology_version)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id, workspace_id, project_id, status,
                             research_context, research_context_hash,
                             research_context_schema_version,
                             created_at, started_at, completed_at,
                             research_completeness_score""",
                (
                    new_id,
                    ws,
                    project_id,
                    json.dumps(context.to_json(), sort_keys=True),
                    context.snapshot_hash(),
                    context.schema_version,
                    ResearchSessionStatus.PENDING.value,
                    budget.max_cost_units if budget else None,
                    budget.max_llm_calls if budget else None,
                    contract_version,
                    ontology_version,
                ),
            ).fetchone()
        return _session_row(row)

    def get(
        self, workspace_id: WorkspaceId | uuid.UUID, session_id: uuid.UUID
    ) -> ResearchSessionRow:
        ws = _require_workspace(workspace_id)
        with self._db.connection() as conn:
            row = conn.execute(
                """SELECT id, workspace_id, project_id, status,
                          research_context, research_context_hash,
                          research_context_schema_version,
                          created_at, started_at, completed_at,
                          research_completeness_score
                   FROM research.research_sessions
                   WHERE workspace_id = %s AND id = %s""",
                (ws, session_id),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"research session {session_id} not found in this workspace")
        return _session_row(row)

    def list_for_project(
        self, workspace_id: WorkspaceId | uuid.UUID, project_id: uuid.UUID
    ) -> list[ResearchSessionRow]:
        ws = _require_workspace(workspace_id)
        with self._db.connection() as conn:
            rows = conn.execute(
                """SELECT id, workspace_id, project_id, status,
                          research_context, research_context_hash,
                          research_context_schema_version,
                          created_at, started_at, completed_at,
                          research_completeness_score
                   FROM research.research_sessions
                   WHERE workspace_id = %s AND project_id = %s
                   ORDER BY created_at DESC""",
                (ws, project_id),
            ).fetchall()
        return [_session_row(row) for row in rows]

    def transition(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        session_id: uuid.UUID,
        target: ResearchSessionStatus,
    ) -> ResearchSessionRow:
        """Move a session to `target`, or refuse.

        Only the transitions Ontology V2 §15 authorizes are permitted. No state
        is invented, and terminal states are terminal.
        """
        ws = _require_workspace(workspace_id)
        current = self.get(ws, session_id)
        allowed = ALLOWED_TRANSITIONS[current.status]
        if target not in allowed:
            raise InvalidTransitionError(
                f"{current.status.value} -> {target.value} is not a permitted "
                f"transition. Allowed from {current.status.value}: "
                f"{sorted(s.value for s in allowed) or 'none (terminal)'}"
            )

        # Static SQL with bound parameters. An earlier draft interpolated
        # fragments into the statement; even with trusted inputs that is a
        # pattern a reviewer has to re-verify every time, so the timestamps are
        # driven by parameters instead.
        set_started = target is ResearchSessionStatus.PLANNING
        set_completed = target in (
            ResearchSessionStatus.COMPLETED,
            ResearchSessionStatus.FAILED,
            ResearchSessionStatus.CANCELLED,
        )
        with self._db.transaction() as conn:
            row = conn.execute(
                """UPDATE research.research_sessions
                   SET status = %(status)s,
                       started_at = CASE WHEN %(set_started)s
                                         THEN COALESCE(started_at, now())
                                         ELSE started_at END,
                       completed_at = CASE WHEN %(set_completed)s
                                           THEN now()
                                           ELSE completed_at END
                   WHERE workspace_id = %(workspace_id)s AND id = %(session_id)s
                   RETURNING id, workspace_id, project_id, status,
                             research_context, research_context_hash,
                             research_context_schema_version,
                             created_at, started_at, completed_at,
                             research_completeness_score""",
                {
                    "status": target.value,
                    "set_started": set_started,
                    "set_completed": set_completed,
                    "workspace_id": ws,
                    "session_id": session_id,
                },
            ).fetchone()
        return _session_row(row)


class OpportunityRepository:
    """Opportunity persistence and session observations.

    Ontology V2 §12: an Opportunity is a domain hypothesis in its own right,
    NOT owned by the session that first found it. Sessions produce
    *observations*, and the same opportunity may be observed by many sessions.

    **Deliberately absent: any identity resolution.** No title matching, no
    embedding distance, no URL comparison. Deciding two discoveries are the same
    opportunity is an analytical problem (§12.3) and this layer must not settle
    it with a convenient uniqueness rule.
    """

    def __init__(self, db: Any) -> None:
        self._db = db

    def create(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        title: str,
        market_scope: MarketScope,
        summary: str | None = None,
        opportunity_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        ws = _require_workspace(workspace_id)
        new_id = opportunity_id or uuid.uuid4()
        with self._db.transaction() as conn:
            conn.execute(
                """INSERT INTO research.opportunities
                       (id, workspace_id, title, summary, market_scope, market_scope_key)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    new_id,
                    ws,
                    title,
                    summary,
                    json.dumps(market_scope.to_json(), sort_keys=True),
                    market_scope.key(),
                ),
            )
        return new_id

    def get(
        self, workspace_id: WorkspaceId | uuid.UUID, opportunity_id: uuid.UUID
    ) -> dict[str, Any]:
        ws = _require_workspace(workspace_id)
        with self._db.connection() as conn:
            row = conn.execute(
                """SELECT id, workspace_id, title, summary, market_scope, market_scope_key
                   FROM research.opportunities
                   WHERE workspace_id = %s AND id = %s""",
                (ws, opportunity_id),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"opportunity {opportunity_id} not found in this workspace")
        return {
            "id": row[0],
            "workspace_id": row[1],
            "title": row[2],
            "summary": row[3],
            "market_scope": row[4],
            "market_scope_key": row[5],
        }

    def record_observation(
        self,
        workspace_id: WorkspaceId | uuid.UUID,
        opportunity_id: uuid.UUID,
        research_session_id: uuid.UUID,
        observation_kind: str,
        claim_type: str,
        observation_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        """Record that a session observed an opportunity.

        `observation_kind` and `claim_type` come from the authoritative schema
        and contracts. No aggregation, no scoring: D-03 is blocked.
        """
        ws = _require_workspace(workspace_id)
        if observation_kind not in OBSERVATION_KINDS:
            raise ContractError(
                "observation_kind",
                f"must be one of {sorted(OBSERVATION_KINDS)}, got {observation_kind!r}",
            )
        new_id = observation_id or uuid.uuid4()
        with self._db.transaction() as conn:
            conn.execute(
                """INSERT INTO research.opportunity_session_observations
                       (id, workspace_id, opportunity_id, research_session_id,
                        observation_kind, claim_type)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (new_id, ws, opportunity_id, research_session_id, observation_kind, claim_type),
            )
        return new_id

    def list_observations(
        self, workspace_id: WorkspaceId | uuid.UUID, opportunity_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        ws = _require_workspace(workspace_id)
        with self._db.connection() as conn:
            rows = conn.execute(
                """SELECT id, research_session_id, observation_kind, claim_type, observed_at
                   FROM research.opportunity_session_observations
                   WHERE workspace_id = %s AND opportunity_id = %s
                   ORDER BY observed_at DESC""",
                (ws, opportunity_id),
            ).fetchall()
        return [
            {
                "id": r[0],
                "research_session_id": r[1],
                "observation_kind": r[2],
                "claim_type": r[3],
                "observed_at": r[4],
            }
            for r in rows
        ]


def _session_row(row: tuple[Any, ...]) -> ResearchSessionRow:
    return ResearchSessionRow(
        id=row[0],
        workspace_id=row[1],
        project_id=row[2],
        status=ResearchSessionStatus(row[3]),
        research_context=row[4],
        research_context_hash=row[5],
        research_context_schema_version=row[6],
        created_at=row[7],
        started_at=row[8],
        completed_at=row[9],
        research_completeness_score=row[10],
    )
