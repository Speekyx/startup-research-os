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

**Every governance read requires an explicit `use_profile`** (Mission 1.75).
Policy reviews are per `(source, use profile)` and have been since Mission
1.15.5, so a governance verdict served without naming its profile is a verdict
with no subject. Until Mission 1.75 these routes joined `source_eligibility` on
`source_id` alone: `/sources` returned a source once per profile that had
reviewed it, and the other two returned an arbitrary profile's row plus the
UNION of every profile's conditions.

There is **no default profile**, and the reason is not caution. Both registered
profiles are real deployments with different verdicts for the same sources, so
any default would answer a question the caller did not ask and would look
exactly like an answer. A missing profile is a 422; an unregistered one is a
422; an absent review under the requested profile is a refusal and never a
reason to consult another profile -- which is the contract
`registry.source_eligibility` states in its own COMMENT.

`use_profile` is **not** `workspace_id`. A request's tenant says whose data is
being worked on; a use profile says which governance regime the caller is
asking about. Neither answers the other, and `RequestContext` deliberately
carries no profile.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request
from sros_contracts import ContractError

from ..db.repositories import NotFoundError

router = APIRouter(prefix="/sources", tags=["source-registry"])


def _blocking_reasons(recorded: list[str] | None, use_profile: str) -> list[str]:
    """The gate's reasons, or the one that applies when there is no row at all.

    `registry.source_eligibility` has no row for a source the profile has never
    reviewed, and its own COMMENT says an absent row is a refusal and never a
    reason to consult another profile. This is that sentence served: the absence
    becomes a stated reason here rather than an empty list, because an empty
    list is what a PASS looks like.
    """
    if recorded is not None:
        return list(recorded)
    return [f"no policy review exists for use profile '{use_profile}'"]


def require_use_profile(request: Request, use_profile: str = Query(...)) -> str:
    """Resolve the caller's explicit use profile, or fail closed.

    Validity comes from `registry.use_profiles`, the canonical vocabulary, so
    this is generic over registered profiles rather than over the two that
    happen to be prominent today. Status is deliberately not filtered: reading
    the governance history of a retired profile is a legitimate question, and
    inventing a status rule here would be a governance decision made in a
    router.
    """
    with request.app.state.db.connection() as conn:
        known = conn.execute(
            "SELECT 1 FROM registry.use_profiles WHERE id = %s",
            (use_profile,),
        ).fetchone()
    if known is None:
        raise ContractError(
            "use_profile",
            f"{use_profile!r} is not a registered use profile. Governance facts belong to "
            "one profile and there is no default; a profile this registry does not know "
            "cannot be answered for.",
        )
    return use_profile


@router.get("")
def list_sources(
    request: Request,
    use_profile: str = Query(
        ...,
        description=(
            "The use profile to answer for. Required: governance facts belong to one "
            "profile and this registry has no default."
        ),
    ),
    family: str | None = None,
) -> dict[str, Any]:
    """Every registered source with its governance state under ONE use profile.

    `collector_eligible` comes from `registry.source_eligibility`, the same view
    the database trigger consults, so this endpoint cannot report a source as
    usable that the database would refuse to enable.

    The join is LEFT and scoped to the requested profile, which settles two
    things at once. Each source appears **exactly once**, whatever else has
    reviewed it -- the profile is in the join predicate, so there is no
    duplication to deduplicate. And a source the requested profile has never
    reviewed is still LISTED, marked unreviewed and ineligible, rather than
    disappearing because a different profile happens to know it.
    """
    profile = require_use_profile(request, use_profile)
    with request.app.state.db.connection() as conn:
        rows = conn.execute(
            """SELECT s.id, s.canonical_name, s.source_family, s.lifecycle,
                      s.description, s.homepage_url, s.documentation_url,
                      s.collector_enabled, s.suspended,
                      s.coverage_scope, s.coverage_countries, s.coverage_languages,
                      s.collector_use_profile,
                      e.approval_state, e.review_stale, coalesce(e.evidence_count, 0),
                      e.blocking_reasons, e.reviewed_at, e.next_review_at,
                      (e.source_id IS NOT NULL)
                 FROM registry.sources s
                 LEFT JOIN registry.source_eligibility e
                        ON e.source_id = s.id
                       AND e.use_profile_id = %s
                -- Casts are required: with no other context psycopg cannot infer
                -- the type of a parameter that only ever appears next to NULL.
                WHERE (%s::text IS NULL OR s.source_family = %s::text)
                ORDER BY s.id""",
            (profile, family, family),
        ).fetchall()

    sources = [_source_summary(row, profile) for row in rows]
    return {
        # The response says which profile it describes, so a stored or forwarded
        # body cannot be read as a verdict about a profile nobody asked for.
        "use_profile": profile,
        "sources": sources,
        "count": len(sources),
        # Surfaced rather than left to be counted, because "how many sources can
        # we actually use" is the question this registry answers.
        "collector_eligible_count": sum(1 for s in sources if s["collector_eligible"]),
        "reviewed_under_profile_count": sum(
            1 for s in sources if s["reviewed_under_requested_profile"]
        ),
    }


@router.get("/{source_id}/eligibility")
def get_source_eligibility(
    request: Request,
    source_id: str,
    use_profile: str = Query(
        ...,
        description=(
            "The use profile to answer for. Required: conditions and verdicts belong to "
            "one profile and this registry has no default."
        ),
    ),
) -> dict[str, Any]:
    """Why this source can or cannot be collected from, condition by condition.

    Mission 1.4 §32. Read-only, like everything else here, and deliberately so:
    an endpoint that could mark a condition satisfied would let anyone who can
    reach the service clear the gate that the review process exists to hold.
    Verification is administered through `sros-source verify`, which runs as the
    migration role.

    What is returned is the **recorded** state -- what a verifier wrote and when
    -- not a fresh verification. Running verifiers on an HTTP request would make
    the answer depend on the web process's environment rather than on the
    deployment the registry describes.

    Scoped to one profile since Mission 1.75. Two absences are distinguished
    here and they mean different things: a source this registry does not know is
    a 404, and a source it knows that the requested profile has never reviewed
    is a 200 saying exactly that. Collapsing them would let "we have no verdict
    for you" read as "no such source", and a caller would go looking for the
    wrong mistake.
    """
    profile = require_use_profile(request, use_profile)
    with request.app.state.db.connection() as conn:
        registered = conn.execute(
            """SELECT s.id, s.collector_enabled, s.collector_use_profile
                 FROM registry.sources s WHERE s.id = %s""",
            (source_id,),
        ).fetchone()
        if registered is None:
            raise NotFoundError(f"source {source_id} is not registered")

        row = conn.execute(
            """SELECT approval_state, review_stale, evidence_count,
                      condition_count, unsatisfied_condition_count, blocking_reasons,
                      next_review_at
                 FROM registry.source_eligibility
                WHERE source_id = %s AND use_profile_id = %s""",
            (source_id, profile),
        ).fetchone()

        conditions = conn.execute(
            """SELECT c.condition_key, c.description, c.verification, c.verification_detail,
                      c.satisfied, c.satisfied_at, c.satisfied_by,
                      v.verifier, v.verifier_version, v.result, v.reason, v.verified_at
                 FROM registry.source_review_conditions c
                 -- The view's own current-review selection, replicated so conditions
                 -- come from exactly the review the verdict came from. Joining every
                 -- non-superseded review would union review VERSIONS within one
                 -- profile, which is the same defect one level down.
                 JOIN (
                     SELECT DISTINCT ON (source_id, assessed_use_profile) *
                       FROM registry.source_policy_reviews
                      WHERE superseded_at IS NULL
                      ORDER BY source_id, assessed_use_profile, review_version DESC
                 ) r ON r.id = c.review_id
                 -- LATERAL rather than a window function so a condition that has
                 -- never been verified still appears. "Never checked" is a state
                 -- a reader has to be able to see.
                 LEFT JOIN LATERAL (
                     SELECT verifier, verifier_version, result, reason, verified_at
                       FROM registry.source_condition_verifications
                      WHERE condition_id = c.id
                      ORDER BY verified_at DESC, created_at DESC
                      LIMIT 1
                 ) v ON TRUE
                WHERE c.source_id = %s AND r.assessed_use_profile = %s
                ORDER BY c.condition_key""",
            (source_id, profile),
        ).fetchall()

    # An absent row is a refusal, and never a reason to consult another profile:
    # the view says so in its own COMMENT, and this is that sentence served.
    reviewed = row is not None
    blocking_reasons = _blocking_reasons(row[5] if reviewed else None, profile)
    return {
        "source_id": source_id,
        "use_profile": profile,
        "reviewed_under_requested_profile": reviewed,
        "approval_state": row[0] if reviewed else None,
        "review_stale": row[1] if reviewed else None,
        "evidence_count": row[2] if reviewed else 0,
        "condition_count": row[3] if reviewed else 0,
        "unsatisfied_condition_count": row[4] if reviewed else 0,
        "blocking_reasons": blocking_reasons,
        "collector_eligible": not blocking_reasons,
        # Eligible is not enabled and neither is a collector existing. Returned
        # explicitly so a caller cannot read the first as either of the others.
        "collector_enabled": registered[1],
        "collector_use_profile": registered[2],
        "collector_enabled_for_requested_profile": bool(registered[1]) and registered[2] == profile,
        "next_review_at": row[6] if reviewed else None,
        "conditions": [
            {
                "condition_key": c[0],
                "description": c[1],
                "verification": c[2],
                # A configuration KEY NAME where the verification is
                # CONFIG_REFERENCE. No credential value is stored in the
                # registry, so none can be served from it.
                "verification_detail": c[3],
                "satisfied": c[4],
                "satisfied_at": c[5],
                "satisfied_by": c[6],
                "latest_verification": (
                    {
                        "verifier": c[7],
                        "verifier_version": c[8],
                        "result": c[9],
                        "reason": c[10],
                        "verified_at": c[11],
                    }
                    if c[7] is not None
                    else None
                ),
            }
            for c in conditions
        ],
    }


@router.get("/{source_id}")
def get_source(
    request: Request,
    source_id: str,
    use_profile: str = Query(
        ...,
        description=(
            "The use profile to answer for. Required: the review, its evidence and the "
            "gate verdict all belong to one profile and this registry has no default."
        ),
    ),
) -> dict[str, Any]:
    """One source in full: access profiles, current review, evidence, retention.

    Evidence is returned with its URLs so a reader can re-open the documents the
    assessment rests on. That is the point of recording them: an approval whose
    basis cannot be re-read cannot be re-verified when the platform changes its
    terms.

    This route was profile-blind in the same way as the other two and it was the
    worst of the three, because it returns the review body and the documents
    behind it. An arbitrary profile's row here does not merely mislabel a
    verdict; it hands back the evidence for an assessment the caller is not
    asking about, with nothing in the payload saying so.
    """
    profile = require_use_profile(request, use_profile)
    with request.app.state.db.connection() as conn:
        row = conn.execute(
            """SELECT s.id, s.canonical_name, s.source_family, s.lifecycle,
                      s.description, s.homepage_url, s.documentation_url,
                      s.collector_enabled, s.suspended,
                      s.coverage_scope, s.coverage_countries, s.coverage_languages,
                      s.collector_use_profile,
                      e.approval_state, e.review_stale, coalesce(e.evidence_count, 0),
                      e.blocking_reasons, e.reviewed_at, e.next_review_at,
                      (e.source_id IS NOT NULL)
                 FROM registry.sources s
                 LEFT JOIN registry.source_eligibility e
                        ON e.source_id = s.id
                       AND e.use_profile_id = %s
                WHERE s.id = %s""",
            (profile, source_id),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"source {source_id} is not registered")

        profiles = conn.execute(
            """SELECT access_method, label, endpoint_url, documentation_url,
                      requires_authentication, requires_api_key, requires_oauth,
                      requires_account, requires_developer_app, requires_approval,
                      secret_references, rate_limit_known, rate_limit_requests,
                      rate_limit_period_seconds, rate_limit_origin, acquisition_cost, notes,
                      rate_limit_daily_quota
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
                WHERE source_id = %s AND assessed_use_profile = %s
                  AND superseded_at IS NULL
                ORDER BY review_version DESC LIMIT 1""",
            (source_id, profile),
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

    payload = _source_summary(row, profile)
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
                    # A source may document a daily quota and no per-period
                    # rate -- Steam is the first, at 100,000 calls per day.
                    # Omitting it served `rate_limit_known` with every number
                    # null, which reads as "no limit is documented" and is the
                    # opposite of what the registry recorded.
                    "daily_quota": p[17],
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


def _source_summary(row: tuple[Any, ...], use_profile: str) -> dict[str, Any]:
    reasons = _blocking_reasons(row[16], use_profile)
    return {
        "source_id": row[0],
        # Carried on every source and not only on the envelope, because a single
        # source object is the thing a caller stores, forwards and compares --
        # and a governance verdict that travels without its profile is the
        # defect this mission repaired.
        "use_profile": use_profile,
        "reviewed_under_requested_profile": row[19],
        "canonical_name": row[1],
        "source_family": row[2],
        "lifecycle": row[3],
        "description": row[4],
        "homepage_url": row[5],
        "documentation_url": row[6],
        "collector_enabled": row[7],
        "suspended": row[8],
        "coverage": {"scope": row[9], "countries": row[10], "languages": row[11]},
        # Mission 1.75. `collector_enabled` is a column on the SOURCE and carries
        # its own profile: the database trigger checks eligibility under
        # `collector_use_profile`, not under whoever is asking. Returned flat
        # beside a profile-scoped verdict it reads as "enabled for you", which
        # for `ted-eu` -- enabled under local, listed under commercial -- would
        # be false. So the profile it was enabled for is returned with it, and
        # the relationship is stated rather than left to be inferred.
        "collector_use_profile": row[12],
        "collector_enabled_for_requested_profile": bool(row[7]) and row[12] == use_profile,
        "approval_state": row[13],
        "review_stale": row[14],
        "evidence_count": row[15],
        # Empty means the gate passes. Every other value is a specific reason,
        # so a caller never has to guess why a source is unusable.
        "blocking_reasons": reasons,
        "collector_eligible": not reasons,
        "reviewed_at": row[17],
        "next_review_at": row[18],
    }
