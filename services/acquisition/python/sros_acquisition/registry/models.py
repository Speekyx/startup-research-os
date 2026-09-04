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
    "AssessedUseProfile",
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
    "EXTERNAL_MODEL_EGRESS_STATES",
    "EGRESS_NOT_ASSESSED",
    "EGRESS_DENIED",
    "EGRESS_PERMITTED_TO_APPROVED_PROVIDERS",
    "SOURCE_ID_PATTERN",
    "USE_PROFILE_ID_PATTERN",
    "LEGACY_USE_PROFILE",
]


class SourceRegistryError(ContractError):
    """A registry record is not in a state the governance model permits."""

    def __init__(self, field_name: str, reason: str) -> None:
        super().__init__(field_name, reason)


# A use-profile id is a slug with an explicit semantic version, because §7 of
# Mission 1.15.5 requires identity to be independent of display wording and to
# change when the semantics do. `local-private-research-v2` would be a different
# profile, not an edit of this one, and no review would silently follow it.
USE_PROFILE_ID_PATTERN = r"^[a-z][a-z0-9-]*-v[0-9]+$"

# The profile every review from Mission 1.0 to Mission 1.15.4 actually assessed.
# Attaching it is a migration interpretation of the historical scope, not a new
# policy conclusion -- the catalog's own `assessed_use_case` prose has said
# "a COMMERCIAL multi-tenant SaaS" since Mission 1.0.
LEGACY_USE_PROFILE = "commercial-multi-tenant-research-v1"


# What a deployment permits by way of sending source-derived content to a
# third-party model processor (ADR-033). Three states, and the default refuses.
#
# A BOOLEAN COULD NOT CARRY THIS. `false` would conflate *decided against* with
# *never asked*, and those are the two states this repository spends most of its
# care keeping apart.
EGRESS_NOT_ASSESSED = "NOT_ASSESSED"
EGRESS_DENIED = "DENIED"
EGRESS_PERMITTED_TO_APPROVED_PROVIDERS = "PERMITTED_TO_APPROVED_PROVIDERS"

EXTERNAL_MODEL_EGRESS_STATES: frozenset[str] = frozenset(
    {EGRESS_NOT_ASSESSED, EGRESS_DENIED, EGRESS_PERMITTED_TO_APPROVED_PROVIDERS}
)


@dataclass(frozen=True)
class AssessedUseProfile:
    """WHAT THE SYSTEM DOES WITH A SOURCE -- the subject of a policy review.

    Mission 1.15.5. Every review has always answered a question about a use
    case; the catalog stated it in prose at the top and every review inherited
    it. What was missing is that the prose had no IDENTITY, so it could not be
    compared, required or matched, and the gate never saw it.

    **A profile is not a deployment environment.** `development` and
    `production` say where code runs; a profile says what is being done with
    somebody else's data. The same binary in the same container can be operated
    under either profile, and the difference is a governance fact, not an
    infrastructural one -- which is why §12 forbids inferring it from localhost,
    Docker, an environment name, a user count or the absence of billing.

    **A profile never widens what a source permits.** It narrows what we claim
    to do. `commercial_purpose` is TRUE on both registered profiles for exactly
    that reason: running locally does not make the use non-commercial, and a
    commercial-use right still has to be granted by the source's own evidence.
    """

    use_profile_id: str
    name: str
    description: str
    semantic_version: int = 1
    status: str = "ACTIVE"

    deployment: str = "LOCAL"
    operator_scope: str = "SINGLE_OPERATOR"
    public_access: bool = False
    external_customers: bool = False
    raw_redistribution: bool = False
    raw_resale: bool = False
    customer_facing_source_access: bool = False
    derived_internal_analysis: bool = True
    commercial_purpose: bool = True
    model_inference: bool = True
    model_training: bool = False
    embeddings: bool = False
    # Mission 1.23, ADR-033. WHERE inference may execute, which `model_inference`
    # above never said: that field states the ACTIVITY is in scope, and
    # `deployment` states where SROS runs. Neither says whether source-derived
    # content may leave for a third-party processor.
    #
    # Defaults to NOT_ASSESSED so a profile written before ADR-033 refuses
    # external inference rather than inheriting a permission nobody granted. A
    # LOCAL inference provider would need `model_inference` and NOT this, which
    # is the clearest statement of why they are two fields.
    external_model_egress: str = EGRESS_NOT_ASSESSED
    personal_data_posture: str = "MINIMISED"
    notes: str | None = None

    def __post_init__(self) -> None:
        import re

        if not re.match(USE_PROFILE_ID_PATTERN, self.use_profile_id):
            raise SourceRegistryError(
                "use_profile_id",
                f"must match {USE_PROFILE_ID_PATTERN}: a slug carrying its semantic "
                "version, so a changed meaning is a changed identity",
            )
        if not self.name.strip() or not self.description.strip():
            raise SourceRegistryError(
                "use_profile",
                "a profile with no description is a subject nobody can check a review against",
            )
        if self.external_model_egress not in EXTERNAL_MODEL_EGRESS_STATES:
            raise SourceRegistryError(
                "use_profile.external_model_egress",
                f"{self.external_model_egress!r} is not one of "
                f"{sorted(EXTERNAL_MODEL_EGRESS_STATES)}. An unrecognised state cannot "
                "fail closed, because nothing downstream knows which way it points",
            )

    @property
    def permits_external_model_egress(self) -> bool:
        """Whether this deployment permits source-derived content to leave for a
        third-party model processor.

        `NOT_ASSESSED` and `DENIED` both answer no, and the DISTINCTION between
        them is why the field is not a boolean: one is a decision and the other
        is a question nobody asked. Callers that only need the yes/no use this;
        callers that must explain a refusal read the state itself.
        """
        return self.external_model_egress == EGRESS_PERMITTED_TO_APPROVED_PROVIDERS

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"


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
    # Mission 1.23, ADR-033. `model_processing` asks whether a model may READ
    # this material. This asks whether the material may LEAVE the local
    # deployment so that a third party's model can read it. They are different
    # acts with different exposure, and until this existed no review could scope
    # itself to a location -- there was no slot to put the answer in.
    #
    # NOT one of rule 8's materially required activities. Those six gate whether
    # a source may be collected from at all; this gates ONE operation. A World
    # Bank deterministic acquisition must not fail because nobody assessed LLM
    # egress for it.
    "external_model_transmission",
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
        self._check_locator()
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

    # A correspondence locator is addressed differently because it is a
    # different kind of thing (migration 0033).
    _CORRESPONDENCE_TYPES = (
        PolicyEvidenceType.OPERATOR_CORRESPONDENCE,
        PolicyEvidenceType.LEGAL_REVIEW,
    )

    def _check_locator(self) -> None:
        """Where the document is addressed, and how it is checked.

        A published page is identified by its ADDRESS: it changes under a stable
        URL, so re-opening it is how you find out whether it still says what the
        review claims. That is the whole argument for requiring http(s), and it
        does not reach a letter. Correspondence is fixed when it is sent, cannot
        be silently amended, and is re-verified by producing the message.

        So the two correspondence types may address themselves with `mailto:`,
        and must then carry a fingerprint. **Both halves or neither**: a mailbox
        with no fingerprint names a channel rather than a document, and a
        fingerprint with no locator names bytes nobody can ask about.
        """
        if self.document_url.startswith(("http://", "https://")):
            return
        if self.document_type not in self._CORRESPONDENCE_TYPES:
            raise SourceRegistryError(
                "evidence.document_url",
                "must be an absolute http(s) URL: an assessment that cannot be "
                "re-opened cannot be re-verified when the platform changes its terms",
            )
        address = self.document_url.removeprefix("mailto:")
        if not self.document_url.startswith("mailto:") or address.count("@") != 1:
            raise SourceRegistryError(
                "evidence.document_url",
                "correspondence may be addressed by a single `mailto:` mailbox "
                "instead of a URL, because a letter has no address to fetch. "
                "Nothing else may be",
            )
        if not address.split("@")[0] or not address.split("@")[1]:
            raise SourceRegistryError(
                "evidence.document_url",
                "a `mailto:` locator needs a mailbox on both sides of the @",
            )
        if self.document_fingerprint is None or not self.document_fingerprint.strip():
            raise SourceRegistryError(
                "evidence.document_fingerprint",
                "required for mailto-addressed correspondence: there is no address "
                "to re-fetch, so the checksum of the artifact read is the only "
                "thing a later reader can check",
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
    # WHICH use profile this review answered. Required: a verdict with no
    # subject cannot be relied on for anything, and Mission 1.15.5 made the
    # subject checkable rather than only stated.
    assessed_use_profile: str
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
        import re as _re

        if not _re.match(USE_PROFILE_ID_PATTERN, self.assessed_use_profile or ""):
            raise SourceRegistryError(
                "review.assessed_use_profile",
                "required, and must be a registered use-profile id: a review is an "
                "answer to a question about a use, and a verdict whose subject is "
                "unstated cannot be transferred, compared or refused correctly",
            )
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
    # The current review UNDER THE LEGACY PROFILE, and nothing else.
    #
    # Mission 1.15.5 kept this field rather than removing it, because it is what
    # every existing document, validator and rendered catalog was written about:
    # `commercial-multi-tenant-research-v1` is the profile the whole history
    # assessed, so every statement already made about a source stays true.
    #
    # **It is not an authorization input.** The gate uses `review_for`, and a
    # structural test asserts that `eligibility.py`, `authorization.py` and
    # `verification.py` never read this attribute -- because reading it would be
    # exactly the silent fallback to a global verdict that §15 forbids.
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
    def _reviews(self) -> tuple[PolicyReview, ...]:
        """Every review, however the record was constructed.

        A record built by hand may set `review` and leave `review_history`
        empty; the catalog loader always fills both. Normalising here rather
        than at each call site is what `repositories.py` already does, and it
        keeps profile matching honest either way -- a single review still only
        answers for its OWN profile.
        """
        return self.review_history or ((self.review,) if self.review else ())

    @property
    def use_profiles(self) -> tuple[str, ...]:
        """Every profile this source has ever been reviewed under, in order."""
        seen: list[str] = []
        for past in self._reviews:
            if past.assessed_use_profile not in seen:
                seen.append(past.assessed_use_profile)
        return tuple(seen)

    def review_for(self, use_profile_id: str) -> PolicyReview | None:
        """The CURRENT review for one use profile, or None.

        **This is the accessor the gate uses, and the only one it may use.**
        `review` below answers a different question and is not an authorization
        input.

        None means "nobody has reviewed this source for this use", which is a
        refusal and never a reason to look at another profile (§15, §16).
        """
        candidates = [past for past in self._reviews if past.assessed_use_profile == use_profile_id]
        if not candidates:
            return None
        return max(candidates, key=lambda past: past.review_version)

    def reviews_by_profile(self) -> dict[str, PolicyReview]:
        """Current review per profile. For presentation and reporting (§31)."""
        return {
            profile: current
            for profile in self.use_profiles
            if (current := self.review_for(profile)) is not None
        }

    @property
    def has_credentialed_profile_without_reference(self) -> bool:
        return any(
            profile.requires_credential and not profile.secret_references
            for profile in self.access_profiles
        )
