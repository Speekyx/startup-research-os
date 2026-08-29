"""Persisting the Source Registry.

Loads the catalog into PostgreSQL and reads it back. Idempotent: loading twice
converges on the same rows, because the catalog is a governance record that gets
re-applied whenever it is edited, not a one-shot fixture.

**No database driver is imported at module level.** The caller supplies a
connection, exactly as the orchestrator's repositories do, so the registry model
and the validator stay runnable with nothing installed (ADR-009).

**Writes are administrative.** `registry.*` is granted SELECT-only to the
runtime role (migration 0004 §10), so these functions run as the migration role
through the CLI. There is deliberately no path from an HTTP request to an
approval: a web endpoint that could approve a source would make the review
process a formality.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from .catalog import SourceCatalog
from .eligibility import EligibilityResult
from .models import ASSESSED_ACTIVITIES, SourceRecord

__all__ = ["LoadReport", "load_catalog_into", "read_eligibility", "read_sources"]

# Deterministic ids, so re-applying the catalog updates the same rows instead of
# accumulating parallel copies. Same argument as the orchestrator's job ids.
_NAMESPACE = uuid.UUID("2f1b6d84-5a3e-5c17-9d20-7e4a1f8c3b60")


def _row_id(*parts: str) -> uuid.UUID:
    return uuid.uuid5(_NAMESPACE, "|".join(parts))


@dataclass(frozen=True)
class LoadReport:
    sources: int
    access_profiles: int
    reviews: int
    evidence: int
    retention_overrides: int
    capabilities: int

    def describe(self) -> str:
        return (
            f"{self.sources} sources, {self.access_profiles} access profiles, "
            f"{self.reviews} reviews, {self.evidence} evidence records, "
            f"{self.retention_overrides} retention overrides, "
            f"{self.capabilities} capabilities"
        )


def load_catalog_into(conn: Any, catalog: SourceCatalog) -> LoadReport:
    """Apply the catalog to a live database, in one transaction.

    The caller owns the transaction. If any source fails a database rule -- an
    approval with no evidence, a collector enabled on an ineligible source --
    the whole load rolls back rather than leaving the registry half-applied,
    which would be a registry nobody could trust.
    """
    counts = dict.fromkeys(
        ("sources", "access_profiles", "reviews", "evidence", "retention", "capabilities"), 0
    )

    for source in catalog.sources:
        conn.execute(
            """INSERT INTO registry.sources
                   (id, canonical_name, source_family, homepage_url, developer_portal_url,
                    documentation_url, description, lifecycle, suspended, suspended_reason,
                    coverage_scope, coverage_countries, coverage_regions, coverage_languages,
                    quality_notes)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (id) DO UPDATE SET
                   canonical_name = EXCLUDED.canonical_name,
                   source_family = EXCLUDED.source_family,
                   homepage_url = EXCLUDED.homepage_url,
                   developer_portal_url = EXCLUDED.developer_portal_url,
                   documentation_url = EXCLUDED.documentation_url,
                   description = EXCLUDED.description,
                   lifecycle = EXCLUDED.lifecycle,
                   suspended = EXCLUDED.suspended,
                   suspended_reason = EXCLUDED.suspended_reason,
                   coverage_scope = EXCLUDED.coverage_scope,
                   coverage_countries = EXCLUDED.coverage_countries,
                   coverage_regions = EXCLUDED.coverage_regions,
                   coverage_languages = EXCLUDED.coverage_languages,
                   quality_notes = EXCLUDED.quality_notes,
                   updated_at = now()""",
            (
                source.source_id,
                source.canonical_name,
                source.source_family,
                source.homepage_url,
                source.developer_portal_url,
                source.documentation_url,
                source.description,
                source.lifecycle.value,
                source.suspended,
                source.suspended_reason,
                source.coverage.scope,
                list(source.coverage.countries),
                list(source.coverage.regions),
                list(source.coverage.languages),
                json.dumps(source.quality_notes, sort_keys=True),
            ),
        )
        counts["sources"] += 1

        for profile in source.access_profiles:
            conn.execute(
                """INSERT INTO registry.source_access_profiles
                       (id, source_id, access_method, label, endpoint_url, documentation_url,
                        requires_authentication, requires_api_key, requires_oauth,
                        requires_account, requires_developer_app, requires_approval,
                        approval_process_notes, secret_references,
                        rate_limit_known, rate_limit_requests, rate_limit_period_seconds,
                        rate_limit_burst, rate_limit_concurrency, rate_limit_daily_quota,
                        pagination_limit, rate_limit_origin, rate_limit_verified_at,
                        acquisition_cost, cost_reference_url, notes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (source_id, access_method, label) DO UPDATE SET
                       endpoint_url = EXCLUDED.endpoint_url,
                       documentation_url = EXCLUDED.documentation_url,
                       requires_authentication = EXCLUDED.requires_authentication,
                       requires_api_key = EXCLUDED.requires_api_key,
                       requires_oauth = EXCLUDED.requires_oauth,
                       requires_account = EXCLUDED.requires_account,
                       requires_developer_app = EXCLUDED.requires_developer_app,
                       requires_approval = EXCLUDED.requires_approval,
                       approval_process_notes = EXCLUDED.approval_process_notes,
                       secret_references = EXCLUDED.secret_references,
                       rate_limit_known = EXCLUDED.rate_limit_known,
                       rate_limit_requests = EXCLUDED.rate_limit_requests,
                       rate_limit_period_seconds = EXCLUDED.rate_limit_period_seconds,
                       rate_limit_origin = EXCLUDED.rate_limit_origin,
                       rate_limit_verified_at = EXCLUDED.rate_limit_verified_at,
                       acquisition_cost = EXCLUDED.acquisition_cost,
                       notes = EXCLUDED.notes,
                       updated_at = now()""",
                (
                    _row_id(
                        "profile", source.source_id, profile.access_method.value, profile.label
                    ),
                    source.source_id,
                    profile.access_method.value,
                    profile.label,
                    profile.endpoint_url,
                    profile.documentation_url,
                    profile.requires_authentication,
                    profile.requires_api_key,
                    profile.requires_oauth,
                    profile.requires_account,
                    profile.requires_developer_app,
                    profile.requires_approval,
                    profile.approval_process_notes,
                    list(profile.secret_references),
                    profile.rate_limit_known,
                    profile.rate_limit_requests,
                    profile.rate_limit_period_seconds,
                    profile.rate_limit_burst,
                    profile.rate_limit_concurrency,
                    profile.rate_limit_daily_quota,
                    profile.pagination_limit,
                    profile.rate_limit_origin,
                    profile.rate_limit_verified_at,
                    profile.acquisition_cost.value,
                    profile.cost_reference_url,
                    profile.notes,
                ),
            )
            counts["access_profiles"] += 1

        for capability in source.capabilities:
            conn.execute(
                """INSERT INTO registry.source_capabilities (id, source_id, capability)
                   VALUES (%s,%s,%s)
                   ON CONFLICT (source_id, capability) DO NOTHING""",
                (_row_id("capability", source.source_id, capability), source.source_id, capability),
            )
            counts["capabilities"] += 1

        review = source.review
        if review is None:
            continue

        review_id = _row_id("review", source.source_id, str(review.review_version))
        assessment_values = [review.assessment(activity).value for activity in ASSESSED_ACTIVITIES]
        conn.execute(
            f"""INSERT INTO registry.source_policy_reviews
                    (id, source_id, review_version, approval_state,
                     {", ".join(ASSESSED_ACTIVITIES)},
                     assessed_use_case, conditions, open_questions, review_notes,
                     personal_data_risk, contains_user_generated_content,
                     contains_user_identifiers, contains_location, sensitive_data_possible,
                     pseudonymization_expected, discard_identifiers_after_normalization,
                     jurisdiction_review_required,
                     reviewed_at, reviewed_by, review_interval_days)
                VALUES (%s,%s,%s,%s,{",".join(["%s"] * len(ASSESSED_ACTIVITIES))},
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (source_id, review_version) DO UPDATE SET
                    approval_state = EXCLUDED.approval_state,
                    assessed_use_case = EXCLUDED.assessed_use_case,
                    conditions = EXCLUDED.conditions,
                    open_questions = EXCLUDED.open_questions,
                    review_notes = EXCLUDED.review_notes,
                    personal_data_risk = EXCLUDED.personal_data_risk,
                    reviewed_at = EXCLUDED.reviewed_at,
                    reviewed_by = EXCLUDED.reviewed_by,
                    review_interval_days = EXCLUDED.review_interval_days,
                    next_review_at = NULL""",  # noqa: S608 - activity list is a module constant
            (
                review_id,
                source.source_id,
                review.review_version,
                review.approval_state.value,
                *assessment_values,
                review.assessed_use_case,
                list(review.conditions),
                list(review.open_questions),
                review.review_notes,
                review.personal_data_risk.value,
                review.contains_user_generated_content,
                review.contains_user_identifiers,
                review.contains_location,
                review.sensitive_data_possible,
                review.pseudonymization_expected,
                review.discard_identifiers_after_normalization,
                review.jurisdiction_review_required,
                review.reviewed_at,
                review.reviewed_by,
                review.review_interval_days,
            ),
        )
        counts["reviews"] += 1

        for item in review.evidence:
            conn.execute(
                """INSERT INTO registry.source_policy_evidence
                       (id, review_id, source_id, document_type, document_title, document_url,
                        section_reference, summarized_finding, excerpt, review_notes,
                        retrieved_at, effective_at, document_fingerprint)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET
                       summarized_finding = EXCLUDED.summarized_finding,
                       section_reference = EXCLUDED.section_reference,
                       retrieved_at = EXCLUDED.retrieved_at,
                       effective_at = EXCLUDED.effective_at""",
                (
                    _row_id("evidence", source.source_id, item.document_url, item.document_title),
                    review_id,
                    source.source_id,
                    item.document_type.value,
                    item.document_title,
                    item.document_url,
                    item.section_reference,
                    item.summarized_finding,
                    item.excerpt,
                    item.review_notes,
                    item.retrieved_at,
                    item.effective_at,
                    item.document_fingerprint,
                ),
            )
            counts["evidence"] += 1

        override = source.retention_override
        if override is not None:
            conn.execute(
                """INSERT INTO registry.source_retention_policies
                       (id, source_id, raw_days, normalized_days, aggregate_permitted,
                        basis, review_id, reviewed_by)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (source_id) DO UPDATE SET
                       raw_days = EXCLUDED.raw_days,
                       normalized_days = EXCLUDED.normalized_days,
                       aggregate_permitted = EXCLUDED.aggregate_permitted,
                       basis = EXCLUDED.basis,
                       review_id = EXCLUDED.review_id,
                       reviewed_by = EXCLUDED.reviewed_by""",
                (
                    _row_id("retention", source.source_id),
                    source.source_id,
                    override.raw_days,
                    override.normalized_days,
                    override.aggregate_permitted,
                    override.basis,
                    review_id,
                    override.reviewed_by,
                ),
            )
            counts["retention"] += 1

    return LoadReport(
        sources=counts["sources"],
        access_profiles=counts["access_profiles"],
        reviews=counts["reviews"],
        evidence=counts["evidence"],
        retention_overrides=counts["retention"],
        capabilities=counts["capabilities"],
    )


def read_sources(conn: Any) -> list[dict[str, Any]]:
    """Read the registry as the API and CLI present it."""
    rows = conn.execute(
        """SELECT s.id, s.canonical_name, s.source_family, s.lifecycle, s.description,
                  s.homepage_url, s.documentation_url, s.collector_enabled, s.suspended,
                  s.coverage_scope, s.coverage_countries, s.coverage_languages,
                  e.approval_state, e.review_stale, e.evidence_count, e.blocking_reasons
             FROM registry.sources s
             JOIN registry.source_eligibility e ON e.source_id = s.id
            ORDER BY s.id"""
    ).fetchall()
    return [
        {
            "source_id": r[0],
            "canonical_name": r[1],
            "source_family": r[2],
            "lifecycle": r[3],
            "description": r[4],
            "homepage_url": r[5],
            "documentation_url": r[6],
            "collector_enabled": r[7],
            "suspended": r[8],
            "coverage": {"scope": r[9], "countries": r[10], "languages": r[11]},
            "approval_state": r[12],
            "review_stale": r[13],
            "evidence_count": r[14],
            "blocking_reasons": r[15],
            "collector_eligible": not r[15],
        }
        for r in rows
    ]


def read_eligibility(conn: Any, source_id: str) -> EligibilityResult | None:
    """Ask the DATABASE for the verdict, not the model.

    Used by the tests that assert the SQL view and the Python gate agree. Two
    implementations of one rule is a real risk, and the answer is to compare
    them rather than to trust that they match.
    """
    from sros_contracts import SourceApprovalState

    row = conn.execute(
        """SELECT approval_state, review_stale, evidence_count, blocking_reasons
             FROM registry.source_eligibility WHERE source_id = %s""",
        (source_id,),
    ).fetchone()
    if row is None:
        return None
    return EligibilityResult(
        source_id=source_id,
        eligible=not row[3],
        blocking_reasons=tuple(row[3]),
        approval_state=SourceApprovalState(row[0]) if row[0] else None,
        review_stale=bool(row[1]),
        evidence_count=int(row[2] or 0),
    )


def source_from_row(row: dict[str, Any]) -> SourceRecord:  # pragma: no cover - convenience
    raise NotImplementedError(
        "The catalog file is the source of truth for source definitions. Reading a "
        "SourceRecord back from the database would create a second one."
    )
