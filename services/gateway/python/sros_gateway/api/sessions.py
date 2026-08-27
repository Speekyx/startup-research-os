"""ResearchSession API.

Ontology V2 §11.4: the ONLY persisted execution entity. Creating one creates
the execution RECORD -- it does not execute research.

**There is deliberately no PATCH for research_context.** The snapshot is the
reproducibility guarantee: editing what a past session says it ran with would
destroy it. A new specification means a new session (Ontology V2 §11.3).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request, status
from sros_contracts import CONTRACT_VERSION, ONTOLOGY_VERSION

from ..db.repositories import ResearchSessionRepository
from .schemas import CreateResearchSession, ResearchSessionOut, to_domain_context

router = APIRouter(tags=["research-sessions"])


def _repo(request: Request) -> ResearchSessionRepository:
    return ResearchSessionRepository(request.app.state.db)


@router.post(
    "/research-projects/{project_id}/sessions",
    response_model=ResearchSessionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    request: Request, project_id: UUID, body: CreateResearchSession
) -> ResearchSessionOut:
    """Create the execution record.

    Validates and canonicalizes the ResearchContext through the domain
    contracts, then persists it as an immutable snapshot with its schema
    version and content hash. Initial status is the canonical PENDING.
    """
    workspace_id = request.state.context.require_workspace()

    # Domain rules live in sros_contracts, not here. A ContractError becomes 422.
    context = to_domain_context(body.research_context)

    row = _repo(request).create(
        workspace_id=workspace_id,
        project_id=project_id,
        context=context,
        contract_version=CONTRACT_VERSION,
        ontology_version=ONTOLOGY_VERSION,
    )
    return ResearchSessionOut(**row.__dict__)


@router.get("/research-sessions/{research_session_id}", response_model=ResearchSessionOut)
def get_session(request: Request, research_session_id: UUID) -> ResearchSessionOut:
    workspace_id = request.state.context.require_workspace()
    row = _repo(request).get(workspace_id, research_session_id)
    return ResearchSessionOut(**row.__dict__)


@router.get("/research-projects/{project_id}/sessions", response_model=list[ResearchSessionOut])
def list_project_sessions(request: Request, project_id: UUID) -> list[ResearchSessionOut]:
    workspace_id = request.state.context.require_workspace()
    rows = _repo(request).list_for_project(workspace_id, project_id)
    return [ResearchSessionOut(**row.__dict__) for row in rows]
