"""Claim and Evidence API.

Mission 1.2 §35. The minimum needed to develop against the new model and to
verify it by hand.

**Writes exist here, and they are not authorised.** Authentication does not
exist (ADR-005), so `x-workspace-id` is a development mechanism for saying which
tenant you are working in — not a claim that you are entitled to. It is the same
mechanism the research-project and session endpoints already use, and the same
caveat applies to all of them. Building an approval model was explicitly out of
scope for this mission; pretending these endpoints have one would be worse than
saying plainly that they do not.

Contrast with the Source Registry API, which is read-only: there, a write
endpoint could approve a source for collection, so its absence is the security
model. Here a write creates a claim inside one workspace, which is content
rather than permission.

**Nothing here aggregates.** No score is computed or returned, and the reference
engine is not imported. `GET /claims/{id}/evidence` returns the INPUT to
aggregation; turning it into a score needs a CALIBRATED profile, which does not
exist (ADR-014).
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, Field

from ..db.claims import ClaimRepository, EvidenceRepository

router = APIRouter(tags=["claims"])


# ============================================================= request bodies


class CreateClaimBody(BaseModel):
    """`temporality` is required, deliberately.

    It has no default and is never inferred from the source, because the same
    platform carries an evergreen fact and a trend stale in a week — a guess
    would be wrong for one of them with no way to tell which
    (evidence-aggregation-framework-v1.md §9).
    """

    opportunity_id: uuid.UUID
    statement: str = Field(min_length=1)
    claim_type: str
    temporality: str
    origin: str
    claim_feature: str | None = None
    origin_session_id: uuid.UUID | None = None
    origin_detail: str | None = None
    created_by: str | None = None


class ReviseClaimBody(BaseModel):
    statement: str = Field(min_length=1)
    revision_reason: str = Field(min_length=1)
    # The author's declaration that the MEANING changed, not just the wording.
    # Nothing acts on it automatically -- that is part of D-08 -- but only the
    # person making the edit knows, and it cannot be reconstructed later.
    material_change: bool = False
    created_by: str | None = None
    research_session_id: uuid.UUID | None = None


# ==================================================================== reading


@router.get("/opportunities/{opportunity_id}/claims")
def list_claims(
    request: Request, opportunity_id: uuid.UUID, include_withdrawn: bool = False
) -> dict[str, Any]:
    """Every claim on one opportunity.

    An opportunity carrying several claims is the normal case, and the point of
    the model: some may be well supported while others are contradicted, and
    aggregating at the opportunity level would average that away.
    """
    workspace = request.state.context.require_workspace()
    claims = ClaimRepository(request.app.state.db).list_for_opportunity(
        workspace, opportunity_id, include_withdrawn=include_withdrawn
    )
    return {
        "opportunity_id": str(opportunity_id),
        "claims": [claim.to_json() for claim in claims],
        "count": len(claims),
    }


@router.get("/claims/{claim_id}")
def get_claim(request: Request, claim_id: uuid.UUID) -> dict[str, Any]:
    """One claim, with its statement history and session observations.

    The history is returned rather than linked because it is small and it is the
    thing a reader needs in order to trust the current statement: a claim whose
    wording changed after evidence was attached is worth looking at closely.
    """
    workspace = request.state.context.require_workspace()
    repository = ClaimRepository(request.app.state.db)
    claim = repository.get(workspace, claim_id)
    payload = claim.to_json()
    payload["revisions"] = [
        {**revision, "created_at": revision["created_at"].isoformat()}
        for revision in repository.revisions(workspace, claim_id)
    ]
    payload["observations"] = [
        {**observation, "observed_at": observation["observed_at"].isoformat()}
        for observation in repository.observations(workspace, claim_id)
    ]
    return payload


@router.get("/claims/{claim_id}/evidence")
def list_evidence(request: Request, claim_id: uuid.UUID) -> dict[str, Any]:
    """A claim's evidence set, and the provenance groups within it.

    **This is aggregation INPUT, not a result.** No strength, no mass, no score:
    computing one requires a calibrated profile and none exists. The counts
    below are the honest summary a reader can form without one.
    """
    workspace = request.state.context.require_workspace()
    repository = EvidenceRepository(request.app.state.db)
    # Confirms the claim exists in THIS workspace before returning anything —
    # an empty list would otherwise be indistinguishable from a claim that
    # belongs to another tenant.
    ClaimRepository(request.app.state.db).get(workspace, claim_id)

    records = repository.list_for_claim(workspace, claim_id)
    groups = repository.independence_groups(workspace, claim_id)
    return {
        "claim_id": str(claim_id),
        "evidence": [_serialise(record) for record in records],
        "independence_groups": [
            {**group, "created_at": group["created_at"].isoformat()} for group in groups
        ],
        "counts": {
            "total": len(records),
            "supports": sum(1 for r in records if r["direction"] == "SUPPORTS"),
            "contradicts": sum(1 for r in records if r["direction"] == "CONTRADICTS"),
            "neutral": sum(1 for r in records if r["direction"] == "NEUTRAL"),
            # Reported separately because they mean different things. Unknown
            # provenance is not a small residue to round away: it is the state
            # most evidence starts in, and it caps what the set can support.
            "known_independent": sum(
                1 for r in records if r["independence_state"] == "KNOWN_INDEPENDENT"
            ),
            "known_dependent": sum(
                1 for r in records if r["independence_state"] == "KNOWN_DEPENDENT"
            ),
            "unknown_independence": sum(1 for r in records if r["independence_state"] == "UNKNOWN"),
            "independence_groups": len(groups),
        },
    }


def _serialise(record: dict[str, Any]) -> dict[str, Any]:
    """Timestamps to ISO strings. Missing factors stay missing.

    A null `relevance` is returned as null and never as 0. Aggregation treats an
    absent factor as making the record non-scorable, and a zero would enter the
    arithmetic as a measured weakness instead (framework §6).
    """
    serialised = dict(record)
    for field in ("observed_at", "collected_at", "expires_at"):
        value = serialised.get(field)
        if value is not None:
            serialised[field] = value.isoformat()
    return serialised


# ==================================================================== writing


@router.post("/claims", status_code=status.HTTP_201_CREATED)
def create_claim(request: Request, body: CreateClaimBody, response: Response) -> dict[str, Any]:
    """Create a claim and its first statement revision.

    Development only — see the module docstring. There is no authorisation here
    and this mission did not build one.
    """
    workspace = request.state.context.require_workspace()
    repository = ClaimRepository(request.app.state.db)
    claim_id = repository.create(
        workspace,
        body.opportunity_id,
        body.statement,
        body.claim_type,
        body.temporality,
        body.origin,
        claim_feature=body.claim_feature,
        origin_session_id=body.origin_session_id,
        origin_detail=body.origin_detail,
        created_by=body.created_by,
    )
    response.headers["location"] = f"/api/v1/claims/{claim_id}"
    return repository.get(workspace, claim_id).to_json()


@router.post("/claims/{claim_id}/revisions", status_code=status.HTTP_201_CREATED)
def revise_claim(request: Request, claim_id: uuid.UUID, body: ReviseClaimBody) -> dict[str, Any]:
    """Append a statement revision.

    The previous revision is never modified. An aggregation that evaluated
    revision 2 must still be able to read revision 2, or every historical result
    becomes unreproducible the moment somebody fixes a typo (§25).
    """
    workspace = request.state.context.require_workspace()
    repository = ClaimRepository(request.app.state.db)
    repository.revise(
        workspace,
        claim_id,
        body.statement,
        revision_reason=body.revision_reason,
        material_change=body.material_change,
        created_by=body.created_by,
        research_session_id=body.research_session_id,
    )
    return repository.get(workspace, claim_id).to_json()
