"""Loading the source catalog.

`docs/data/source-catalog-v1.json` is the hand-edited source of truth for which
sources exist and what was found about them. This module turns it into the
domain model, and every constructor it calls validates -- so a malformed catalog
fails at load rather than at collection time.

The catalog lives in `docs/data/` rather than beside the code because it is a
governance record, not configuration: it is read by people deciding whether a
source may be used, and it is the artefact a reviewer edits. The markdown table
in `source-catalog-v1.md` is rendered from it, so the two cannot drift.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sros_contracts import (
    ConditionVerification,
    PersonalDataRisk,
    PolicyAssessment,
    PolicyEvidenceType,
    SourceAccessMethod,
    SourceAcquisitionCost,
    SourceApprovalState,
    SourceLifecycle,
)

from .models import (
    EGRESS_NOT_ASSESSED,
    LEGACY_USE_PROFILE,
    AccessProfile,
    AssessedUseProfile,
    BehaviorCoverage,
    Coverage,
    PolicyEvidence,
    PolicyReview,
    RetentionOverride,
    ReviewCondition,
    SignalCoverage,
    SourceRecord,
    SourceRegistryError,
)

__all__ = ["SourceCatalog", "load_catalog", "DEFAULT_CATALOG_PATH", "find_catalog"]

DEFAULT_CATALOG_PATH = pathlib.Path("docs/data/source-catalog-v1.json")


def find_catalog(start: pathlib.Path | None = None) -> pathlib.Path:
    """Locate the catalog by walking up from `start` to the repository root.

    Walking up rather than resolving relative to this module keeps the CLI
    usable from any directory, which is what an operator actually does.
    """
    current = (start or pathlib.Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        path = candidate / DEFAULT_CATALOG_PATH
        if path.exists():
            return path
    raise SourceRegistryError("catalog", f"no {DEFAULT_CATALOG_PATH} found above {current}")


@dataclass(frozen=True)
class SourceCatalog:
    catalog_version: str
    assessed_use_case: str
    reviewer: str
    review_date: str
    sources: tuple[SourceRecord, ...]
    known_limitations: tuple[str, ...] = ()
    # The registered use profiles (Mission 1.15.5). A review may only name one
    # of these, and an id that is not here is refused at load rather than at the
    # gate -- an unregistered profile is a typo or an invention, and both should
    # fail before anything asks it a question.
    use_profiles: tuple[AssessedUseProfile, ...] = ()

    def use_profile(self, use_profile_id: str) -> AssessedUseProfile:
        for profile in self.use_profiles:
            if profile.use_profile_id == use_profile_id:
                return profile
        raise SourceRegistryError(
            "use_profile_id",
            f"no use profile {use_profile_id!r} is registered. Known: "
            f"{', '.join(p.use_profile_id for p in self.use_profiles)}. An unknown "
            "profile is never authorised (Mission 1.15.5 §6)",
        )

    def has_use_profile(self, use_profile_id: str) -> bool:
        return any(p.use_profile_id == use_profile_id for p in self.use_profiles)

    def get(self, source_id: str) -> SourceRecord:
        for source in self.sources:
            if source.source_id == source_id:
                return source
        raise SourceRegistryError(
            "source_id",
            f"no source {source_id!r} in the catalog. Known: "
            f"{', '.join(s.source_id for s in self.sources)}",
        )

    def __len__(self) -> int:
        return len(self.sources)

    def __iter__(self) -> Any:
        return iter(self.sources)


def load_catalog(path: pathlib.Path | str | None = None) -> SourceCatalog:
    file = pathlib.Path(path) if path else find_catalog()
    try:
        payload = json.loads(file.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SourceRegistryError("catalog", f"{file} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SourceRegistryError("catalog", "the catalog must be a JSON object")

    use_case = str(payload.get("assessed_use_case") or "")
    if not use_case.strip():
        raise SourceRegistryError(
            "catalog.assessed_use_case",
            "required: an assessment that does not state what it assessed cannot be "
            "relied on for a different use",
        )

    raw_profiles = payload.get("use_profiles")
    if not isinstance(raw_profiles, list) or not raw_profiles:
        raise SourceRegistryError(
            "catalog.use_profiles",
            "at least one use profile is required: every review is an answer to a "
            "question about a use, and the question must be registered before the "
            "answer can be checked (Mission 1.15.5 §4)",
        )
    use_profiles = tuple(_use_profile_from_json(item) for item in raw_profiles)
    profile_ids = {p.use_profile_id for p in use_profiles}
    if len(profile_ids) != len(use_profiles):
        raise SourceRegistryError("catalog.use_profiles", "duplicate use_profile_id")

    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise SourceRegistryError("catalog.sources", "at least one source is required")

    sources: list[SourceRecord] = []
    seen: set[str] = set()
    for entry in raw_sources:
        record = _source_from_json(entry, use_case)
        for past in record.review_history:
            if past.assessed_use_profile not in profile_ids:
                raise SourceRegistryError(
                    f"{record.source_id}.reviews[{past.review_version}].assessed_use_profile",
                    f"{past.assessed_use_profile!r} is not a registered use profile. "
                    f"Known: {', '.join(sorted(profile_ids))}",
                )
        if record.source_id in seen:
            raise SourceRegistryError(
                "catalog.sources",
                f"duplicate source_id {record.source_id!r}. A stable identifier that "
                "appears twice makes provenance ambiguous",
            )
        seen.add(record.source_id)
        sources.append(record)

    return SourceCatalog(
        catalog_version=str(payload.get("catalog_version") or "0"),
        assessed_use_case=use_case,
        reviewer=str(payload.get("reviewer") or "unknown"),
        review_date=str(payload.get("review_date") or ""),
        sources=tuple(sources),
        known_limitations=tuple(payload.get("known_limitations") or ()),
        use_profiles=use_profiles,
    )


def _use_profile_from_json(raw: object) -> AssessedUseProfile:
    if not isinstance(raw, dict):
        raise SourceRegistryError("catalog.use_profiles", "each entry must be an object")
    return AssessedUseProfile(
        use_profile_id=str(raw.get("use_profile_id") or ""),
        name=str(raw.get("name") or ""),
        description=str(raw.get("description") or ""),
        semantic_version=int(raw.get("semantic_version") or 1),
        status=str(raw.get("status") or "ACTIVE"),
        deployment=str(raw.get("deployment") or "LOCAL"),
        operator_scope=str(raw.get("operator_scope") or "SINGLE_OPERATOR"),
        public_access=bool(raw.get("public_access", False)),
        external_customers=bool(raw.get("external_customers", False)),
        raw_redistribution=bool(raw.get("raw_redistribution", False)),
        raw_resale=bool(raw.get("raw_resale", False)),
        customer_facing_source_access=bool(raw.get("customer_facing_source_access", False)),
        derived_internal_analysis=bool(raw.get("derived_internal_analysis", True)),
        commercial_purpose=bool(raw.get("commercial_purpose", True)),
        model_inference=bool(raw.get("model_inference", True)),
        model_training=bool(raw.get("model_training", False)),
        embeddings=bool(raw.get("embeddings", False)),
        # ADR-033. Absent means NOT_ASSESSED: a profile written before the
        # field existed refuses external inference rather than inheriting a
        # permission nobody granted.
        external_model_egress=str(raw.get("external_model_egress") or EGRESS_NOT_ASSESSED),
        personal_data_posture=str(raw.get("personal_data_posture") or "MINIMISED"),
        notes=raw.get("notes"),
    )


def _timestamp(value: object, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise SourceRegistryError(field_name, "must be an ISO-8601 timestamp string")
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise SourceRegistryError(field_name, f"not an ISO-8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise SourceRegistryError(field_name, "must carry a timezone offset")
    return parsed


def _source_from_json(entry: object, use_case: str) -> SourceRecord:
    if not isinstance(entry, dict):
        raise SourceRegistryError("catalog.sources", "each source must be an object")

    source_id = str(entry.get("source_id") or "")
    coverage_raw = entry.get("coverage") or {}
    coverage = Coverage(
        scope=str(coverage_raw.get("scope") or "UNKNOWN"),
        countries=tuple(coverage_raw.get("countries") or ()),
        regions=tuple(coverage_raw.get("regions") or ()),
        languages=tuple(coverage_raw.get("languages") or ()),
    )

    profiles = tuple(
        _profile_from_json(item, source_id) for item in entry.get("access_profiles") or ()
    )

    # Two accepted shapes. `reviews` is a HISTORY, oldest first, each with its
    # own evidence -- the Mission 1.3 form. `review` plus a sibling `evidence`
    # list is the Mission 1.0 form, read as a one-entry history so an older
    # catalog still loads and still means the same thing.
    history: list[PolicyReview] = []
    reviews_raw = entry.get("reviews")
    if reviews_raw:
        if not isinstance(reviews_raw, list):
            raise SourceRegistryError(f"{source_id}.reviews", "must be a list, oldest first")
        for item in reviews_raw:
            if not isinstance(item, dict):
                raise SourceRegistryError(f"{source_id}.reviews", "each entry must be an object")
            evidence = tuple(_evidence_from_json(e, source_id) for e in item.get("evidence") or ())
            history.append(_review_from_json(item, evidence, use_case, source_id))
    elif entry.get("review"):
        evidence = tuple(
            _evidence_from_json(item, source_id) for item in entry.get("evidence") or ()
        )
        history.append(_review_from_json(entry["review"], evidence, use_case, source_id))

    if history:
        # Each PROFILE keeps its own append-only version line (Mission 1.15.5).
        # Version 1 under a second profile is a first review of a new question,
        # not a duplicate of the first review of the old one.
        keys = [(r.assessed_use_profile, r.review_version) for r in history]
        if len(set(keys)) != len(keys):
            raise SourceRegistryError(
                f"{source_id}.reviews",
                f"duplicate (use profile, review_version) in {keys}. Two reviews sharing "
                "both cannot be told apart, and the later one would silently shadow the "
                "earlier",
            )
        history.sort(key=lambda r: (r.assessed_use_profile, r.review_version))
    # `review` is the current review UNDER THE LEGACY PROFILE, and nothing else
    # (Mission 1.15.5). Every document, validator and rendered catalog written
    # before profiles existed was written about that profile, so keeping this
    # field scoped to it leaves every existing statement true. The gate does not
    # read it -- `SourceRecord.review_for` is the authorization accessor, and a
    # structural test keeps it that way.
    legacy = [r for r in history if r.assessed_use_profile == LEGACY_USE_PROFILE]
    review: PolicyReview | None = legacy[-1] if legacy else None

    override_raw = entry.get("retention_override")
    override: RetentionOverride | None = None
    if override_raw:
        override = RetentionOverride(
            basis=str(override_raw.get("basis") or ""),
            reviewed_by=str(override_raw.get("reviewed_by") or ""),
            raw_days=override_raw.get("raw_days"),
            normalized_days=override_raw.get("normalized_days"),
            aggregate_permitted=bool(override_raw.get("aggregate_permitted", True)),
            evidence_url=override_raw.get("evidence_url"),
        )

    return SourceRecord(
        source_id=source_id,
        canonical_name=str(entry.get("canonical_name") or ""),
        source_family=str(entry.get("source_family") or ""),
        description=str(entry.get("description") or ""),
        lifecycle=SourceLifecycle(entry.get("lifecycle") or "ACTIVE"),
        homepage_url=entry.get("homepage_url"),
        developer_portal_url=entry.get("developer_portal_url"),
        documentation_url=entry.get("documentation_url"),
        coverage=coverage,
        quality_notes=dict(entry.get("quality_notes") or {}),
        capabilities=tuple(entry.get("capabilities") or ()),
        signal_coverage=_signal_coverage_from_json(entry, source_id),
        behavior_coverage=_behavior_coverage_from_json(entry, source_id),
        access_profiles=profiles,
        review=review,
        review_history=tuple(history),
        retention_override=override,
        # Never read from the catalog. Enabling a collector is an operational
        # decision taken against a live registry through the CLI, where the
        # database gate applies; a JSON file must not be able to grant it.
        collector_enabled=False,
        suspended=bool(entry.get("suspended", False)),
        suspended_reason=entry.get("suspended_reason"),
    )


def _signal_coverage_from_json(
    entry: dict[str, object], source_id: str
) -> tuple[SignalCoverage, ...]:
    """Mission 1.7 §4. Absent is legal and means nobody has profiled the source.

    An empty profile is NOT the same statement as "this source exposes
    nothing", and the loader keeps them distinguishable by never inventing a
    default.
    """
    items = entry.get("signal_coverage")
    if items is None:
        return ()
    if not isinstance(items, list):
        raise SourceRegistryError(f"{source_id}.signal_coverage", "must be a list")
    out = []
    for item in items:
        if not isinstance(item, dict):
            raise SourceRegistryError(
                f"{source_id}.signal_coverage",
                "each entry must be an object with signal_family and basis",
            )
        out.append(
            SignalCoverage(
                signal_family=str(item.get("signal_family") or ""),
                basis=str(item.get("basis") or ""),
                notes=item.get("notes"),
            )
        )
    return tuple(out)


def _behavior_coverage_from_json(
    entry: dict[str, object], source_id: str
) -> tuple[BehaviorCoverage, ...]:
    """Mission 1.7 §5, against Ontology V2 §3.4's canonical `user_behavior`."""
    items = entry.get("behavior_coverage")
    if items is None:
        return ()
    if not isinstance(items, list):
        raise SourceRegistryError(f"{source_id}.behavior_coverage", "must be a list")
    out = []
    for item in items:
        if not isinstance(item, dict):
            raise SourceRegistryError(
                f"{source_id}.behavior_coverage",
                "each entry must be an object with behavior and basis",
            )
        out.append(
            BehaviorCoverage(
                behavior=str(item.get("behavior") or ""),
                basis=str(item.get("basis") or ""),
                notes=item.get("notes"),
            )
        )
    return tuple(out)


def _profile_from_json(item: object, source_id: str) -> AccessProfile:
    if not isinstance(item, dict):
        raise SourceRegistryError(f"{source_id}.access_profiles", "each profile must be an object")
    verified = item.get("rate_limit_verified_at")
    return AccessProfile(
        access_method=SourceAccessMethod(item.get("access_method")),
        label=str(item.get("label") or ""),
        endpoint_url=item.get("endpoint_url"),
        documentation_url=item.get("documentation_url"),
        requires_authentication=bool(item.get("requires_authentication", False)),
        requires_api_key=bool(item.get("requires_api_key", False)),
        requires_oauth=bool(item.get("requires_oauth", False)),
        requires_account=bool(item.get("requires_account", False)),
        requires_developer_app=bool(item.get("requires_developer_app", False)),
        requires_approval=bool(item.get("requires_approval", False)),
        approval_process_notes=item.get("approval_process_notes"),
        secret_references=tuple(item.get("secret_references") or ()),
        rate_limit_known=bool(item.get("rate_limit_known", False)),
        rate_limit_requests=item.get("rate_limit_requests"),
        rate_limit_period_seconds=item.get("rate_limit_period_seconds"),
        rate_limit_burst=item.get("rate_limit_burst"),
        rate_limit_concurrency=item.get("rate_limit_concurrency"),
        rate_limit_daily_quota=item.get("rate_limit_daily_quota"),
        pagination_limit=item.get("pagination_limit"),
        rate_limit_origin=item.get("rate_limit_origin"),
        rate_limit_verified_at=(
            _timestamp(verified, f"{source_id}.rate_limit_verified_at") if verified else None
        ),
        acquisition_cost=SourceAcquisitionCost(item.get("acquisition_cost") or "UNKNOWN"),
        cost_reference_url=item.get("cost_reference_url"),
        notes=item.get("notes"),
    )


def _evidence_from_json(item: object, source_id: str) -> PolicyEvidence:
    if not isinstance(item, dict):
        raise SourceRegistryError(f"{source_id}.evidence", "each record must be an object")
    effective = item.get("effective_at")
    return PolicyEvidence(
        document_type=PolicyEvidenceType(item.get("document_type")),
        document_title=str(item.get("document_title") or ""),
        document_url=str(item.get("document_url") or ""),
        summarized_finding=str(item.get("summarized_finding") or ""),
        retrieved_at=_timestamp(item.get("retrieved_at"), f"{source_id}.evidence.retrieved_at"),
        section_reference=item.get("section_reference"),
        effective_at=(
            _timestamp(effective, f"{source_id}.evidence.effective_at") if effective else None
        ),
        excerpt=item.get("excerpt"),
        review_notes=item.get("review_notes"),
        document_fingerprint=item.get("document_fingerprint"),
    )


def _condition_from_json(item: object, source_id: str) -> ReviewCondition:
    """One mechanically checkable condition (Mission 1.3 §24)."""
    if not isinstance(item, dict):
        raise SourceRegistryError(f"{source_id}.required_conditions", "each must be an object")
    return ReviewCondition(
        key=str(item.get("key") or ""),
        description=str(item.get("description") or ""),
        verification=ConditionVerification(item.get("verification") or "HUMAN_CONFIRMATION"),
        verification_detail=item.get("verification_detail"),
    )


def _review_from_json(
    raw: object, evidence: tuple[PolicyEvidence, ...], use_case: str, source_id: str
) -> PolicyReview:
    if not isinstance(raw, dict):
        raise SourceRegistryError(f"{source_id}.review", "must be an object")

    from .models import ASSESSED_ACTIVITIES

    assessments = {
        activity: PolicyAssessment(raw.get(activity) or "NOT_ASSESSED")
        for activity in ASSESSED_ACTIVITIES
        if activity in raw
    }

    reviewed_at = raw.get("reviewed_at")
    return PolicyReview(
        approval_state=SourceApprovalState(raw.get("approval_state") or "DRAFT"),
        # The catalog states its scope once, at the top, and every review
        # inherits it. A per-source restatement would drift.
        assessed_use_profile=str(raw.get("assessed_use_profile") or ""),
        assessed_use_case=str(raw.get("assessed_use_case") or use_case),
        reviewed_by=str(raw.get("reviewed_by") or "mission-1.0"),
        reviewed_at=(
            _timestamp(reviewed_at, f"{source_id}.review.reviewed_at")
            if reviewed_at
            else datetime.fromisoformat("2026-08-29T00:00:00+00:00")
        ),
        evidence=evidence,
        review_version=int(raw.get("review_version") or 1),
        review_interval_days=int(raw.get("review_interval_days") or 180),
        assessments=assessments,
        conditions=tuple(raw.get("conditions") or ()),
        required_conditions=tuple(
            _condition_from_json(c, source_id) for c in raw.get("required_conditions") or ()
        ),
        open_questions=tuple(raw.get("open_questions") or ()),
        review_notes=raw.get("review_notes"),
        personal_data_risk=PersonalDataRisk(raw.get("personal_data_risk") or "UNKNOWN"),
        contains_user_generated_content=bool(raw.get("contains_user_generated_content", False)),
        contains_user_identifiers=bool(raw.get("contains_user_identifiers", False)),
        contains_location=bool(raw.get("contains_location", False)),
        sensitive_data_possible=bool(raw.get("sensitive_data_possible", False)),
        pseudonymization_expected=bool(raw.get("pseudonymization_expected", False)),
        discard_identifiers_after_normalization=bool(
            raw.get("discard_identifiers_after_normalization", False)
        ),
        jurisdiction_review_required=bool(raw.get("jurisdiction_review_required", True)),
    )
