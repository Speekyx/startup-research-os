"""Source Registry API — read only.

Mission 1.0 §27. Two endpoints, both reads.

**There is deliberately no write path here.** Authentication does not exist
(ADR-005), so an HTTP endpoint that could approve a source, enable a collector
or edit a policy review would let anyone who can reach the service do the one
thing this registry exists to make deliberate. Review is administered through
`sros-source`, which runs as the migration role; `registry.*` is granted
SELECT-only to the runtime role, so even a bug in this file cannot write.

**No workspace is required.** Source definitions and their reviews are GLOBAL
platform metadata (`service-boundaries.md` §5, ADR-012 §4): a source review that
differed per workspace would make provenance incomparable across workspaces.
Requiring a tenant header here would imply an isolation that does not exist and
is not wanted.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from ..db.repositories import NotFoundError

router = APIRouter(prefix="/sources", tags=["source-registry"])


@router.get("")
def list_sources(request: Request, family: str | None = None) -> dict[str, Any]:
    """Every registered source with its governance state and gate verdict.

    `collector_eligible` comes from `registry.source_eligibility`, the same view
    the database trigger consults, so this endpoint cannot report a source as
    usable that the database would refuse to enable.
    """
    with request.app.state.db.connection() as conn:
        rows = conn.execute(
            """SELECT s.id, s.canonical_name, s.source_family, s.lifecycle,
                      s.description, s.homepage_url, s.documentation_url,
                      s.collector_enabled, s.suspended,
                      s.coverage_scope, s.coverage_countries, s.coverage_languages,
                      e.approval_state, e.review_stale, e.evidence_count,
                      e.blocking_reasons, e.reviewed_at, e.next_review_at
                 FROM registry.sources s
                 JOIN registry.source_eligibility e ON e.source_id = s.id
                -- Casts are required: with no other context psycopg cannot infer
                -- the type of a parameter that only ever appears next to NULL.
                WHERE (%s::text IS NULL OR s.source_family = %s::text)
                ORDER BY s.id""",
            (family, family),
        ).fetchall()

    sources = [_source_summary(row) for row in rows]
    return {
        "sources": sources,
        "count": len(sources),
        # Surfaced rather than left to be counted, because "how many sources can
        # we actually use" is the question this registry answers.
        "collector_eligible_count": sum(1 for s in sources if s["collector_eligible"]),
    }


@router.get("/{source_id}")
def get_source(request: Request, source_id: str) -> dict[str, Any]:
    """One source in full: access profiles, current review, evidence, retention.

    Evidence is returned with its URLs so a reader can re-open the documents the
    assessment rests on. That is the point of recording them: an approval whose
    basis cannot be re-read cannot be re-verified when the platform changes its
    terms.
    """
    with request.app.state.db.connection() as conn:
        row = conn.execute(
            """SELECT s.id, s.canonical_name, s.source_family, s.lifecycle,
                      s.description, s.homepage_url, s.documentation_url,
                      s.collector_enabled, s.suspended,
                      s.coverage_scope, s.coverage_countries, s.coverage_languages,
                      e.approval_state, e.review_stale, e.evidence_count,
                      e.blocking_reasons, e.reviewed_at, e.next_review_at
                 FROM registry.sources s
                 JOIN registry.source_eligibility e ON e.source_id = s.id
                WHERE s.id = %s""",
            (source_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"source {source_id} is not registered")

        profiles = conn.execute(
            """SELECT access_method, label, endpoint_url, documentation_url,
                      requires_authentication, requires_api_key, requires_oauth,
                      requires_account, requires_developer_app, requires_approval,
                      secret_references, rate_limit_known, rate_limit_requests,
                      rate_limit_period_seconds, rate_limit_origin, acquisition_cost, notes
                 FROM registry.source_access_profiles
                WHERE source_id = %s ORDER BY access_method, label""",
            (source_id,),
        ).fetchall()

        review = conn.execute(
            """SELECT id, review_version, approval_state, assessed_use_case,
                      automated_access, api_use, browser_automation, commercial_use,
                      storage, retention, redistribution, derived_analytics,
                      model_processing, personal_data_handling, attribution_required,
                      personal_data_risk, conditions, open_questions, review_notes,
                      reviewed_at, reviewed_by, next_review_at,
                      jurisdiction_review_required
                 FROM registry.source_policy_reviews
                WHERE source_id = %s AND superseded_at IS NULL
                ORDER BY review_version DESC LIMIT 1""",
            (source_id,),
        ).fetchone()

        evidence = []
        if review is not None:
            evidence = conn.execute(
                """SELECT document_type, document_title, document_url, section_reference,
                          summarized_finding, retrieved_at, effective_at
                     FROM registry.source_policy_evidence
                    WHERE review_id = %s ORDER BY retrieved_at DESC""",
                (review[0],),
            ).fetchall()

        retention = conn.execute(
            """SELECT raw_days, normalized_days, aggregate_permitted, basis, reviewed_at
                 FROM registry.source_retention_policies WHERE source_id = %s""",
            (source_id,),
        ).fetchone()

        capabilities = conn.execute(
            "SELECT capability FROM registry.source_capabilities WHERE source_id = %s ORDER BY 1",
            (source_id,),
        ).fetchall()

    payload = _source_summary(row)
    payload["capabilities"] = [c[0] for c in capabilities]
    payload["access_profiles"] = [
        {
            "access_method": p[0],
            "label": p[1],
            "endpoint_url": p[2],
            "documentation_url": p[3],
            "requires_authentication": p[4],
            "requires_api_key": p[5],
            "requires_oauth": p[6],
            "requires_account": p[7],
            "requires_developer_app": p[8],
            "requires_approval": p[9],
            # Configuration KEY NAMES. No credential value is stored anywhere in
            # the registry, so none can be served from it.
            "secret_references": p[10],
            "rate_limit": (
                {
                    "requests": p[12],
                    "period_seconds": p[13],
                    "origin": p[14],
                }
                if p[11]
                else None
            ),
            "acquisition_cost": p[15],
            "notes": p[16],
        }
        for p in profiles
    ]
    payload["review"] = (
        {
            "review_version": review[1],
            "approval_state": review[2],
            "assessed_use_case": review[3],
            "assessments": {
                "automated_access": review[4],
                "api_use": review[5],
                "browser_automation": review[6],
                "commercial_use": review[7],
                "storage": review[8],
                "retention": review[9],
                "redistribution": review[10],
                "derived_analytics": review[11],
                "model_processing": review[12],
                "personal_data_handling": review[13],
                "attribution_required": review[14],
            },
            "personal_data_risk": review[15],
            "conditions": review[16],
            "open_questions": review[17],
            "review_notes": review[18],
            "reviewed_at": review[19],
            "reviewed_by": review[20],
            "next_review_at": review[21],
            "jurisdiction_review_required": review[22],
        }
        if review is not None
        else None
    )
    payload["evidence"] = [
        {
            "document_type": e[0],
            "document_title": e[1],
            "document_url": e[2],
            "section_reference": e[3],
            "summarized_finding": e[4],
            "retrieved_at": e[5],
            "effective_at": e[6],
        }
        for e in evidence
    ]
    payload["retention_override"] = (
        {
            "raw_days": retention[0],
            "normalized_days": retention[1],
            "aggregate_permitted": retention[2],
            "basis": retention[3],
            "reviewed_at": retention[4],
        }
        if retention is not None
        else None
    )
    return payload


def _source_summary(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "source_id": row[0],
        "canonical_name": row[1],
        "source_family": row[2],
        "lifecycle": row[3],
        "description": row[4],
        "homepage_url": row[5],
        "documentation_url": row[6],
        "collector_enabled": row[7],
        "suspended": row[8],
        "coverage": {"scope": row[9], "countries": row[10], "languages": row[11]},
        "approval_state": row[12],
        "review_stale": row[13],
        "evidence_count": row[14],
        # Empty means the gate passes. Every other value is a specific reason,
        # so a caller never has to guess why a source is unusable.
        "blocking_reasons": row[15],
        "collector_eligible": not row[15],
        "reviewed_at": row[16],
        "next_review_at": row[17],
    }
