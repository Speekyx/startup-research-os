"""The Source Registry domain model.

Mission 1.0, resolving D-07. Governed by `docs/data/source-registry-v1.md`.

**The rule the whole model exists to enforce:** public visibility is not
permission. `data-principles.md` §13 puts it plainly — "a source being publicly
visible does not automatically mean unrestricted commercial reuse is permitted"
— and every type here is shaped so that no path leads from "we can reach it" to
"we may collect it".

Three separations do the work, and each one exists because collapsing it would
lose a distinction that matters:

    AccessProfile      HOW access is technically performed
    PolicyReview       WHETHER each activity is permitted, per activity
    RetentionOverride  HOW LONG anything collected may be kept

A source with an `OFFICIAL_API` profile and a `PROHIBITED` review is a normal,
common state. So is a source that permits automated access and forbids
commercial use. Only a per-activity model can express either.

**This module is dependency-free**, so the same rules run in the CLI, in the
validator with nothing installed, and against PostgreSQL (ADR-009's argument: a
check that cannot run is a check that gets skipped).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

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
from sros_contracts.errors import ContractError

__all__ = [
    "SourceRegistryError",
    "SourceRecord",
    "AccessProfile",
    "PolicyReview",
    "ReviewCondition",
    "PolicyEvidence",
    "RetentionOverride",
    "CoverageScope",
    "Coverage",
    "APPROVING_STATES",
    "AUTHORITATIVE_EVIDENCE_TYPES",
    "ASSESSED_ACTIVITIES",
    "SOURCE_ID_PATTERN",
]


class SourceRegistryError(ContractError):
    """A registry record is not in a state the governance model permits."""

    def __init__(self, field_name: str, reason: str) -> None:
        super().__init__(field_name, reason)


# The only states that let a source be collected from. Everything else --
# including DRAFT, which is the state a source starts in -- keeps the gate shut.
APPROVING_STATES: frozenset[SourceApprovalState] = frozenset(
    {SourceApprovalState.APPROVED, SourceApprovalState.APPROVED_WITH_CONDITIONS}
)

# Evidence types that may support an approving state. A blog post is not a term
# of service, and the hierarchy in `data-principles.md` §13 exists because the
# tempting evidence is always the convenient kind.
AUTHORITATIVE_EVIDENCE_TYPES: frozenset[PolicyEvidenceType] = frozenset(
    {
        PolicyEvidenceType.OFFICIAL_API_DOCS,
        PolicyEvidenceType.OFFICIAL_TERMS,
        PolicyEvidenceType.OFFICIAL_LICENCE,
        PolicyEvidenceType.OFFICIAL_PRIVACY,
        PolicyEvidenceType.OFFICIAL_ACCESS_CONTROL,
        PolicyEvidenceType.OPERATOR_CORRESPONDENCE,
        PolicyEvidenceType.LEGAL_REVIEW,
    }
)

# The activities assessed separately (§11). Listed once, so a new activity is
# added in one place and every consumer sees it.
ASSESSED_ACTIVITIES: tuple[str, ...] = (
    "automated_access",
    "api_use",
    "browser_automation",
    "commercial_use",
    "storage",
    "retention",
    "redistribution",
    "derived_analytics",
    "model_processing",
    "personal_data_handling",
    "attribution_required",
)

SOURCE_ID_PATTERN = r"^[a-z0-9][a-z0-9._-]{0,127}$"

# Fragments that suggest a credential VALUE rather than a configuration KEY.
# `secret_references` holds names like REDDIT_CLIENT_ID; anything that looks
# like the thing itself is refused, because a registry row is not a vault and a
# secret written here would reach every reader of the catalog.
_SECRET_VALUE_MARKERS = (
    "-----begin",
    "bearer ",
    "sk-",
    "ghp_",
    "gho_",
    "github_pat_",
    "xox",
    "aiza",
    "asia",
    "akia",
)


class CoverageScope:
    """How much of the world a source speaks for."""

    GLOBAL = "GLOBAL"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"

    ALL = frozenset({GLOBAL, PARTIAL, UNKNOWN})


@dataclass(frozen=True)
class Coverage:
    """Descriptive coverage (§17).

    Countries and languages are kept apart deliberately. A source dominated by
    English speakers is not thereby representative of any national market, and a
    model that let one field be inferred from the other would make that mistake
    silently and often.
    """

    scope: str = CoverageScope.UNKNOWN
    countries: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.scope not in CoverageScope.ALL:
            raise SourceRegistryError(
                "coverage.scope", f"must be one of {sorted(CoverageScope.ALL)}"
            )
        for code in self.countries:
            if len(code) != 2 or not code.isalpha() or code != code.upper():
                raise SourceRegistryError(
                    "coverage.countries",
                    f"{code!r} is not an uppercase ISO 3166-1 alpha-2 code (Ontology V2 §4.3)",
                )

    def to_json(self) -> dict[str, object]:
        return {
            "scope": self.scope,
            "countries": list(self.countries),
            "regions": list(self.regions),
            "languages": list(self.languages),
        }


@dataclass(frozen=True)
class PolicyEvidence:
    """A document a conclusion rests on (§13).

    Full documents are NOT stored. They are third-party copyrighted text, and
    mirroring them would show the same disregard for source terms this registry
    exists to prevent. What is kept is a reference, a retrieval time, a section
    pointer and a short finding in the reviewer's own words.
    """

    document_type: PolicyEvidenceType
    document_title: str
    document_url: str
    summarized_finding: str
    retrieved_at: datetime
    section_reference: str | None = None
    effective_at: datetime | None = None
    excerpt: str | None = None
    review_notes: str | None = None
    document_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.document_type, PolicyEvidenceType):
            raise SourceRegistryError("evidence.document_type", "must be a PolicyEvidenceType")
        if not self.document_title.strip():
            raise SourceRegistryError("evidence.document_title", "required")
        if not self.document_url.startswith(("http://", "https://")):
            raise SourceRegistryError(
                "evidence.document_url",
                "must be an absolute http(s) URL: an assessment that cannot be "
                "re-opened cannot be re-verified when the platform changes its terms",
            )
        if not self.summarized_finding.strip():
            raise SourceRegistryError(
                "evidence.summarized_finding",
                "required: a URL with no finding records that someone opened a page, "
                "not what it said",
            )
        if self.retrieved_at.tzinfo is None:
            raise SourceRegistryError(
                "evidence.retrieved_at",
                "must be timezone-aware: terms change, so when "
                "a document was read is part of what it proves",
            )
        if self.excerpt is not None and len(self.excerpt) > 1000:
            raise SourceRegistryError(
                "evidence.excerpt",
                "excerpts are capped at 1000 characters. A longer one is a copy of a "
                "third-party document, not a reference to it",
            )

    @property
    def is_authoritative(self) -> bool:
        return self.document_type in AUTHORITATIVE_EVIDENCE_TYPES


@dataclass(frozen=True)
class ReviewCondition:
    """One condition an approving review depends on, stated so it can be checked.

    Mission 1.3 §24. `APPROVED_WITH_CONDITIONS` must not silently mean "a
    collector may run". The old model recorded conditions as prose in a
    `TEXT[]`, which a reviewer could read and nothing could evaluate -- adequate
    while every review was blocking anyway, useless the moment one approves.

    So each condition names HOW it is verified. `HUMAN_CONFIRMATION` is a real
    answer and the honest one for anything a program cannot establish: §24
    forbids encoding legal prose as executable logic, and pretending a machine
    can check "attribution is adequate" would be exactly that.

    `satisfied` is ENVIRONMENT state, not catalog state. The catalog declares
    what must hold; whether it holds depends on what is deployed. A catalog load
    can never set it -- see `load_catalog_into`.
    """

    key: str
    description: str
    verification: ConditionVerification
    verification_detail: str | None = None

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise SourceRegistryError("condition.key", "required and stable across reviews")
        if not self.description.strip():
            raise SourceRegistryError(
                "condition.description",
                "required: a condition nobody can read cannot be argued with",
            )
        if not isinstance(self.verification, ConditionVerification):
            raise SourceRegistryError("condition.verification", "must be a ConditionVerification")
        # A mechanical check needs something to look at. Only human confirmation
        # can legitimately point at nothing.
        if (
            self.verification is not ConditionVerification.HUMAN_CONFIRMATION
            and not (self.verification_detail or "").strip()
        ):
            raise SourceRegistryError(
                "condition.verification_detail",
                f"{self.verification.value} must name what is checked -- a config key, a "
                "capability, a day count or an access method. If nothing can be checked, "
                "the verification is HUMAN_CONFIRMATION",
            )

    @property
    def mechanically_verifiable(self) -> bool:
        return self.verification is not ConditionVerification.HUMAN_CONFIRMATION

    def to_json(self) -> dict[str, object]:
        return {
            "key": self.key,
            "description": self.description,
            "verification": self.verification.value,
            "verification_detail": self.verification_detail,
        }


@dataclass(frozen=True)
class PolicyReview:
    """A dated, versioned assessment of one source for one stated use (§11).

    Every activity carries its own verdict. `NOT_ADDRESSED` means the documents
    were silent, and silence is never converted into permission: turning "the
    terms do not mention it" into "we may" is the single most likely way this
    registry could fail while looking complete.
    """

    approval_state: SourceApprovalState
    assessed_use_case: str
    reviewed_by: str
    reviewed_at: datetime
    evidence: tuple[PolicyEvidence, ...] = ()
    review_version: int = 1
    review_interval_days: int = 180

    assessments: dict[str, PolicyAssessment] = field(default_factory=dict)
    conditions: tuple[str, ...] = ()
    # Structured, individually satisfiable. `conditions` above stays as the
    # reviewer's own prose summary; this is what the gate evaluates.
    required_conditions: tuple[ReviewCondition, ...] = ()
    open_questions: tuple[str, ...] = ()
    review_notes: str | None = None

    personal_data_risk: PersonalDataRisk = PersonalDataRisk.UNKNOWN
    contains_user_generated_content: bool = False
    contains_user_identifiers: bool = False
    contains_location: bool = False
    sensitive_data_possible: bool = False
    pseudonymization_expected: bool = False
    discard_identifiers_after_normalization: bool = False
    jurisdiction_review_required: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.approval_state, SourceApprovalState):
            raise SourceRegistryError("review.approval_state", "must be a SourceApprovalState")
        if not self.assessed_use_case.strip():
            raise SourceRegistryError(
                "review.assessed_use_case",
                "required: an approval that does not say what it approved cannot be "
                "relied on for anything else",
            )
        if not self.reviewed_by.strip():
            raise SourceRegistryError("review.reviewed_by", "required")
        if self.reviewed_at.tzinfo is None:
            raise SourceRegistryError("review.reviewed_at", "must be timezone-aware")
        if self.review_interval_days <= 0:
            raise SourceRegistryError("review.review_interval_days", "must be positive")
        if self.review_version < 1:
            raise SourceRegistryError("review.review_version", "must be at least 1")

        unknown = set(self.assessments) - set(ASSESSED_ACTIVITIES)
        if unknown:
            raise SourceRegistryError(
                "review.assessments",
                f"unknown activities {sorted(unknown)}. Activities are a closed list so a "
                f"typo cannot silently create an unassessed dimension: {list(ASSESSED_ACTIVITIES)}",
            )
        for name, value in self.assessments.items():
            if not isinstance(value, PolicyAssessment):
                raise SourceRegistryError(
                    f"review.assessments.{name}", "must be a PolicyAssessment"
                )

        # §13, and the rule the mission is built around.
        if self.approval_state in APPROVING_STATES:
            if not self.evidence:
                raise SourceRegistryError(
                    "review.evidence",
                    f"{self.approval_state.value} requires at least one evidence record. "
                    "An approval with nothing behind it is an opinion with a timestamp",
                )
            if not any(item.is_authoritative for item in self.evidence):
                raise SourceRegistryError(
                    "review.evidence",
                    f"{self.approval_state.value} requires at least one official or "
                    "authoritative document. A blog post is not a term of service",
                )

        if (
            self.approval_state is SourceApprovalState.APPROVED_WITH_CONDITIONS
            and not self.conditions
            and not self.required_conditions
        ):
            raise SourceRegistryError(
                "review.conditions",
                "APPROVED_WITH_CONDITIONS must list its conditions. Conditions that are "
                "not written down are not conditions",
            )

        if (
            self.approval_state
            in (
                SourceApprovalState.RESTRICTED,
                SourceApprovalState.PROHIBITED,
                SourceApprovalState.SUSPENDED,
            )
            and not (self.review_notes or "").strip()
        ):
            raise SourceRegistryError(
                "review.review_notes",
                f"{self.approval_state.value} must say why. A refusal with no reason gets "
                "re-litigated by the next person who wants the data",
            )

    def assessment(self, activity: str) -> PolicyAssessment:
        """The verdict for one activity, defaulting to NOT_ASSESSED.

        Defaulting to NOT_ASSESSED rather than raising is deliberate: a missing
        activity means nobody looked, which is exactly what the value says.
        """
        if activity not in ASSESSED_ACTIVITIES:
            raise SourceRegistryError("activity", f"unknown activity {activity!r}")
        return self.assessments.get(activity, PolicyAssessment.NOT_ASSESSED)

    @property
    def next_review_at(self) -> datetime:
        return self.reviewed_at + timedelta(days=self.review_interval_days)

    def is_stale(self, now: datetime | None = None) -> bool:
        return (now or datetime.now(UTC)) > self.next_review_at

    @property
    def is_approving(self) -> bool:
        return self.approval_state in APPROVING_STATES


@dataclass(frozen=True)
class AccessProfile:
    """How a source can technically be reached (§8).

    **Says nothing about permission.** `BROWSER_AUTOMATION` appearing here means
    a browser could do it, never that anyone may. That answer lives in the
    review, and the two are separate types so no reader can take one for the
    other.

    Credentials are never held here. `secret_references` carries configuration
    KEY NAMES, and a value that looks like a credential is refused outright.
    """

    access_method: SourceAccessMethod
    label: str
    endpoint_url: str | None = None
    documentation_url: str | None = None

    requires_authentication: bool = False
    requires_api_key: bool = False
    requires_oauth: bool = False
    requires_account: bool = False
    requires_developer_app: bool = False
    requires_approval: bool = False
    approval_process_notes: str | None = None
    secret_references: tuple[str, ...] = ()

    rate_limit_known: bool = False
    rate_limit_requests: int | None = None
    rate_limit_period_seconds: int | None = None
    rate_limit_burst: int | None = None
    rate_limit_concurrency: int | None = None
    rate_limit_daily_quota: int | None = None
    pagination_limit: int | None = None
    rate_limit_origin: str | None = None
    rate_limit_verified_at: datetime | None = None

    acquisition_cost: SourceAcquisitionCost = SourceAcquisitionCost.UNKNOWN
    cost_reference_url: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.access_method, SourceAccessMethod):
            raise SourceRegistryError(
                "access_profile.access_method", "must be a SourceAccessMethod"
            )
        if not self.label.strip():
            raise SourceRegistryError("access_profile.label", "required")

        # §9. Requiring a credential without naming where it comes from makes a
        # source look usable and fail at the first call.
        if (self.requires_api_key or self.requires_oauth) and not self.secret_references:
            raise SourceRegistryError(
                "access_profile.secret_references",
                "a profile that requires an API key or OAuth must name at least one "
                "configuration reference, for example REDDIT_CLIENT_ID",
            )

        for reference in self.secret_references:
            lowered = reference.lower()
            if any(marker in lowered for marker in _SECRET_VALUE_MARKERS) or len(reference) > 64:
                raise SourceRegistryError(
                    "access_profile.secret_references",
                    f"{reference!r} looks like a credential value rather than a "
                    "configuration key name. Secrets belong in the environment or a "
                    "secret manager, never in the registry",
                )
            if not reference.replace("_", "").replace("-", "").isalnum():
                raise SourceRegistryError(
                    "access_profile.secret_references",
                    f"{reference!r} is not a configuration key name",
                )

        # §19. A number with no stated origin is a guess, and a collector would
        # trust it. UNKNOWN is a real answer.
        if self.rate_limit_known and self.rate_limit_origin not in ("DOCUMENTED", "OBSERVED"):
            raise SourceRegistryError(
                "access_profile.rate_limit_origin",
                "a known rate limit must record whether it is DOCUMENTED or OBSERVED",
            )
        if not self.rate_limit_known and any(
            value is not None
            for value in (
                self.rate_limit_requests,
                self.rate_limit_period_seconds,
                self.rate_limit_daily_quota,
            )
        ):
            raise SourceRegistryError(
                "access_profile.rate_limit_known",
                "rate-limit numbers are recorded but the limit is not marked known. "
                "Either the numbers came from somewhere, or they are a guess",
            )
        for name in ("rate_limit_requests", "rate_limit_period_seconds", "rate_limit_daily_quota"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise SourceRegistryError(f"access_profile.{name}", "must be positive")

    @property
    def requires_credential(self) -> bool:
        return self.requires_api_key or self.requires_oauth


@dataclass(frozen=True)
class RetentionOverride:
    """A per-source retention rule (`data-retention-policy-v1.md` §3).

    `basis` is mandatory, and §3 gives the reason: an override with no recorded
    justification is indistinguishable from someone having wanted more data, and
    cannot be re-verified when the source's terms change.

    An override may go in **both directions**, and the stricter applicable rule
    always wins (§1). Resolution lives in `retention.py`.
    """

    basis: str
    reviewed_by: str
    raw_days: int | None = None
    normalized_days: int | None = None
    aggregate_permitted: bool = True
    evidence_url: str | None = None

    def __post_init__(self) -> None:
        if not self.basis.strip():
            raise SourceRegistryError(
                "retention_override.basis",
                "required: an override without a justification cannot be re-verified "
                "(data-retention-policy-v1.md §3)",
            )
        if not self.reviewed_by.strip():
            raise SourceRegistryError("retention_override.reviewed_by", "required")
        for name in ("raw_days", "normalized_days"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise SourceRegistryError(f"retention_override.{name}", "must not be negative")
        if self.raw_days is None and self.normalized_days is None and self.aggregate_permitted:
            raise SourceRegistryError(
                "retention_override",
                "an override that overrides nothing is a row that will be read as a "
                "policy. Omit it and the baseline applies",
            )


# The vocabularies migration 0010 seeds, mirrored here so the model and the
# validators keep working with no database (ADR-009). Duplicated deliberately
# and compared by a test rather than trusted: `source-registry-v1.md` §4 takes
# the same approach to eligibility, which "exists twice, and the two are
# compared".
#
# `signal_family` (Mission 1.7 §4) says what a source COULD expose. It is not
# permission, it is not evidence weight, and it never enters EvidenceScore.
SIGNAL_FAMILIES: frozenset[str] = frozenset(
    {
        "problem",
        "desire",
        "entertainment",
        "creativity",
        "curiosity",
        "competition",
        "social",
        "discovery",
        "learning",
        "collection",
        "personalization",
        "status",
        "community",
        "trend",
        "commercial",
        "developer_activity",
    }
)

# Ontology V2 §3.4, unchanged. NOT a Mission 1.7 vocabulary: behaviour coverage
# reuses the canonical registry rather than defining a second one (§5).
USER_BEHAVIORS: frozenset[str] = frozenset(
    {
        "create",
        "discover",
        "consume",
        "play",
        "learn",
        "compare",
        "predict",
        "collect",
        "share",
        "compete",
        "customize",
        "track",
        "discuss",
        "buy",
        "sell",
        "collaborate",
        "automate",
    }
)


@dataclass(frozen=True)
class SignalCoverage:
    """One kind of opportunity signal a source could expose (Mission 1.7 §4).

    **Potential, never permission.** A source may cover `entertainment` and be
    `PROHIBITED`; the two facts live in different tables so that no view can
    collapse them into one verdict.

    `basis` is mandatory for the reason a retention override's is
    (`source-registry-v1.md` §6): a coverage claim with no stated justification
    cannot be re-checked when the source changes, and is indistinguishable from
    somebody having wanted the category filled in.

    There is deliberately no weight, score or confidence field. One would be a
    per-source reliability coefficient under another name, which is D-03 (§35).
    """

    signal_family: str
    basis: str
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.signal_family not in SIGNAL_FAMILIES:
            raise SourceRegistryError(
                "signal_coverage.signal_family",
                f"{self.signal_family!r} is not a signal family. "
                f"Known: {', '.join(sorted(SIGNAL_FAMILIES))}",
            )
        if not self.basis.strip():
            raise SourceRegistryError(
                "signal_coverage.basis",
                "required: which documented capability this rests on. A coverage claim "
                "with no basis cannot be re-checked when the source changes",
            )


@dataclass(frozen=True)
class BehaviorCoverage:
    """A canonical user behaviour a source records evidence of (Mission 1.7 §5).

    References Ontology V2 §3.4's `user_behavior` registry. No second behaviour
    vocabulary exists and none should: the canonical list is already exactly
    what §5 asks for.
    """

    behavior: str
    basis: str
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.behavior not in USER_BEHAVIORS:
            raise SourceRegistryError(
                "behavior_coverage.behavior",
                f"{self.behavior!r} is not a canonical user behaviour "
                f"(opportunity-ontology-v2.md §3.4). "
                f"Known: {', '.join(sorted(USER_BEHAVIORS))}",
            )
        if not self.basis.strip():
            raise SourceRegistryError("behavior_coverage.basis", "required")


@dataclass(frozen=True)
class SourceRecord:
    """One candidate or registered source.

    `source_id` is the identity and is never derived from a URL or a display
    name: both change while the source stays the same thing, and provenance
    written against it has to keep resolving.
    """

    source_id: str
    canonical_name: str
    source_family: str
    description: str = ""
    lifecycle: SourceLifecycle = SourceLifecycle.ACTIVE

    homepage_url: str | None = None
    developer_portal_url: str | None = None
    documentation_url: str | None = None

    coverage: Coverage = field(default_factory=Coverage)
    quality_notes: dict[str, str] = field(default_factory=dict)
    capabilities: tuple[str, ...] = ()

    # What could be LEARNED from this source, as opposed to what data it
    # returns (`capabilities`). Mission 1.7 §4/§5, ADR-017. Empty is a legal
    # and meaningful state: it says nobody has profiled the source yet, which
    # is different from saying it exposes nothing.
    signal_coverage: tuple[SignalCoverage, ...] = ()
    behavior_coverage: tuple[BehaviorCoverage, ...] = ()

    access_profiles: tuple[AccessProfile, ...] = ()
    review: PolicyReview | None = None
    # Every review this source has ever had, oldest first. Mission 1.3 §27:
    # a new review creates a new VERSION rather than overwriting the old one,
    # because the useful record is "Mission 1.0 concluded X, Mission 1.3 found
    # Y, because document Z became available". Overwriting destroys exactly
    # the part a reader needs in order to trust the current verdict.
    review_history: tuple[PolicyReview, ...] = ()
    retention_override: RetentionOverride | None = None

    # §21. False for every new source, always.
    collector_enabled: bool = False
    suspended: bool = False
    suspended_reason: str | None = None

    def __post_init__(self) -> None:
        import re

        if not re.match(SOURCE_ID_PATTERN, self.source_id):
            raise SourceRegistryError(
                "source_id",
                f"must match {SOURCE_ID_PATTERN}: a stable lowercase slug, never a URL",
            )
        if not self.canonical_name.strip():
            raise SourceRegistryError("canonical_name", "required")
        if not self.source_family.strip():
            raise SourceRegistryError("source_family", "required")
        if not isinstance(self.lifecycle, SourceLifecycle):
            raise SourceRegistryError("lifecycle", "must be a SourceLifecycle")
        if self.suspended and not (self.suspended_reason or "").strip():
            raise SourceRegistryError(
                "suspended_reason",
                "a suspension must say why. An unexplained stop is indistinguishable "
                "from an outage",
            )

        # Nothing may set this directly on a record: eligibility decides it, and
        # the database refuses it too (migration 0004 §8.2). Constructing a
        # record with it already true would be a way around the gate.
        if self.collector_enabled and self.review is None:
            raise SourceRegistryError(
                "collector_enabled",
                "cannot be enabled on a source with no policy review",
            )

    @property
    def has_credentialed_profile_without_reference(self) -> bool:
        return any(
            profile.requires_credential and not profile.secret_references
            for profile in self.access_profiles
        )
