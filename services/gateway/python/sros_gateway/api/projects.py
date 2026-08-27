"""ResearchProject API.

Ontology V2 §11.2: a persistent, workspace-scoped container for a research
objective. It exists independently of whether any session has run.

No deletion endpoint. Retention and lifecycle semantics for a project are not
specified yet (`data-retention-policy-v1.md` covers records, not project
lifecycle), and an unspecified delete is how data disappears in ways nobody
intended.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request, status

from ..db.repositories import ResearchProjectRepository
from .schemas import CreateResearchProject, ResearchProjectOut

router = APIRouter(prefix="/research-projects", tags=["research-projects"])


def _repo(request: Request) -> ResearchProjectRepository:
    return ResearchProjectRepository(request.app.state.db)


@router.post("", response_model=ResearchProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(request: Request, body: CreateResearchProject) -> ResearchProjectOut:
    workspace_id = request.state.context.require_workspace()
    row = _repo(request).create(workspace_id, body.name, body.description)
    return ResearchProjectOut(**row.__dict__)


@router.get("", response_model=list[ResearchProjectOut])
def list_projects(request: Request, limit: int = 50, offset: int = 0) -> list[ResearchProjectOut]:
    workspace_id = request.state.context.require_workspace()
    rows = _repo(request).list(workspace_id, limit=min(limit, 200), offset=offset)
    return [ResearchProjectOut(**row.__dict__) for row in rows]


@router.get("/{project_id}", response_model=ResearchProjectOut)
def get_project(request: Request, project_id: UUID) -> ResearchProjectOut:
    workspace_id = request.state.context.require_workspace()
    row = _repo(request).get(workspace_id, project_id)
    return ResearchProjectOut(**row.__dict__)
