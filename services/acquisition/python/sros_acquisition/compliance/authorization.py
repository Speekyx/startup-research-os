"""The authorization a collector must hold before it may run.

Mission 1.4 §26 and §27. There is no collector, and this module is what a
collector will be built against.

**A collector must not interpret policy.** Every question it could get wrong --
which access path is approved, which resources are in scope, how long anything
may be kept, what attribution follows the data, which fields may be requested at
all -- is answered here, once, from the registry and the compliance
configuration. A collector that read a source's terms itself would be a second
opinion about a decision the review already made.

**The context cannot be built for an ineligible source.** `build_authorization`
runs the canonical gate and raises when it does not pass. That is the whole
enforcement mechanism: not a flag the collector is asked to check, but the
absence of the object it needs in order to do anything.

    request collection
        -> load the registry
        -> verify conditions
        -> evaluate eligibility
        -> build AcquisitionAuthorizationContext   <- fails here, or not at all
        -> collector

**Nothing here opens a connection.** The context describes what is permitted; it
performs nothing, and the package it lives in is asserted network-free in CI.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from sros_contracts import SourceApprovalState
from sros_contracts.errors import ContractError

from ..registry.eligibility import evaluate_eligibility
from ..registry.models import AccessProfile, SourceRecord
from ..registry.retention import EffectiveRetention, resolve_retention
from .config import (
    AttributionObligation,
    ComplianceConfig,
    DataMinimisationProfile,
    ResourceScope,
)
from .resources import ResourceAuthorization, ResourceDescriptor, authorize_resource
from .verification import (
    ConditionVerificationRecord,
    design_eligible,
    satisfied_condition_keys,
    verify_source,
)

__all__ = [
    "AcquisitionAuthorizationContext",
    "AcquisitionNotAuthorizedError",
    "AuthorizedAccess",
    "RateLimit",
    "build_authorization",
]


class AcquisitionNotAuthorizedError(ContractError):
    """No authorization exists for this source, and therefore nothing may run.

    Carries every reason, like the gate it comes from: a caller who fixes one
    blocker and rediscovers the next on the following attempt learns to work
    around the gate rather than through it.
    """

    def __init__(self, source_id: str, reasons: tuple[str, ...]) -> None:
        self.source_id = source_id
        self.reasons = reasons
        super().__init__(
            f"acquisition.{source_id}",
            "not authorized: " + ("; ".join(reasons) if reasons else "no reason recorded"),
        )


@dataclass(frozen=True)
class RateLimit:
    """Documented or observed limits, or the honest absence of them.

    `known` is false far more often than it is true, and that is not a gap to
    fill. §29 forbids inventing a limit, and a collector told `known=False` must
    throttle conservatively on its own -- which is a different instruction from
    being handed a number that was made up.
    """

    known: bool
    requests: int | None = None
    period_seconds: int | None = None
    burst: int | None = None
    concurrency: int | None = None
    daily_quota: int | None = None
    origin: str | None = None

    def to_json(self) -> dict[str, object]:
        return {
            "known": self.known,
            "requests": self.requests,
            "period_seconds": self.period_seconds,
            "burst": self.burst,
            "concurrency": self.concurrency,
            "daily_quota": self.daily_quota,
            "origin": self.origin,
        }


@dataclass(frozen=True)
class AuthorizedAccess:
    """One approved way to reach a source.

    `credential_references` are configuration KEY NAMES. No value passes through
    this object, and there is no field one could occupy.
    """

    access_method: str
    label: str
    endpoint_url: str | None
    documentation_url: str | None
    credential_references: tuple[str, ...]
    rate_limit: RateLimit

    def to_json(self) -> dict[str, object]:
        return {
            "access_method": self.access_method,
            "label": self.label,
            "endpoint_url": self.endpoint_url,
            "documentation_url": self.documentation_url,
            "credential_references": list(self.credential_references),
            "rate_limit": self.rate_limit.to_json(),
        }


@dataclass(frozen=True)
class AcquisitionAuthorizationContext:
    """Everything a collector is allowed to know and required to obey."""

    source_id: str
    canonical_name: str
    approval_state: SourceApprovalState
    review_version: int
    reviewed_at: datetime
    next_review_at: datetime

    access: tuple[AuthorizedAccess, ...]
    resource_scope: ResourceScope
    retention: EffectiveRetention
    attribution: AttributionObligation
    data_minimisation: DataMinimisationProfile
    verifications: tuple[ConditionVerificationRecord, ...]
    issued_at: datetime

    def authorize_resource(self, descriptor: ResourceDescriptor) -> ResourceAuthorization:
        """The only sanctioned way to reach a specific dataset, series or record.

        Source-level authorization is not resource-level authorization
        (§11, §12). Holding this context permits nothing on its own; each
        resource is asked for separately and refused by default.
        """
        return authorize_resource(self.resource_scope, descriptor)

    @property
    def design_eligible(self) -> bool:
        """Every non-runtime condition satisfied. Reporting only (§24)."""
        return design_eligible(list(self.verifications))

    @property
    def runtime_credential_references(self) -> tuple[str, ...]:
        return tuple(sorted({r for a in self.access for r in a.credential_references}))

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "canonical_name": self.canonical_name,
            "approval_state": self.approval_state.value,
            "review_version": self.review_version,
            "reviewed_at": self.reviewed_at.isoformat(),
            "next_review_at": self.next_review_at.isoformat(),
            "access": [a.to_json() for a in self.access],
            "resource_scope": {
                "licence_allowlist": (
                    sorted(self.resource_scope.licence_allowlist)
                    if self.resource_scope.licence_allowlist is not None
                    else None
                ),
                "geography_allowlist": (
                    sorted(self.resource_scope.geography_allowlist)
                    if self.resource_scope.geography_allowlist is not None
                    else None
                ),
                "excluded_dataset_families": sorted(self.resource_scope.excluded_dataset_families),
                "require_dataset_family": self.resource_scope.require_dataset_family,
                "enumerated_exclusions": [
                    {"key": e.key, "reason": e.reason}
                    for e in self.resource_scope.enumerated_exclusions
                ],
                "excluded_note_markers": list(self.resource_scope.excluded_note_markers),
                "require_notes": self.resource_scope.require_notes,
                "third_party_denied": self.resource_scope.third_party_denied,
            },
            "retention": self.retention.to_json(),
            "attribution": {
                "evidence_url": self.attribution.evidence_url,
                "requirements": [
                    {
                        "element": r.element.value,
                        "text": r.text,
                        "supplied": r.supplied,
                        "when_modified": r.when_modified,
                    }
                    for r in self.attribution.requirements
                ],
            },
            "data_minimisation": {
                "allowed": list(self.data_minimisation.allowed),
                "excluded": list(self.data_minimisation.excluded),
            },
            "verifications": [v.to_json() for v in self.verifications],
            "design_eligible": self.design_eligible,
            "issued_at": self.issued_at.isoformat(),
        }


def build_authorization(
    source: SourceRecord,
    config: ComplianceConfig,
    verifications: tuple[ConditionVerificationRecord, ...] | None = None,
    environ: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> AcquisitionAuthorizationContext:
    """Build the context, or refuse and say why.

    Verifications are computed here when not supplied, so a caller cannot obtain
    an authorization by passing a hand-made list of satisfied conditions: the
    parameter exists for the CLI and the API, which have just run them and
    should not run them twice, not as a way in.
    """
    moment = now or datetime.now(UTC)
    records = verifications if verifications is not None else verify_source(source, config, environ)

    result = evaluate_eligibility(source, moment, satisfied_condition_keys(records))
    if not result.eligible:
        raise AcquisitionNotAuthorizedError(source.source_id, result.blocking_reasons)

    review = source.review
    if review is None:  # pragma: no cover - the gate above already refuses this
        raise AcquisitionNotAuthorizedError(source.source_id, ("no policy review exists",))

    compliance = config.get(source.source_id)
    if compliance is None:
        # A source can pass the gate with no compliance entry only if its review
        # declares no condition. It still gets no authorization: the context has
        # no attribution obligation, no resource scope and no minimisation
        # profile to give a collector, and an empty scope is not an open one.
        raise AcquisitionNotAuthorizedError(
            source.source_id,
            (
                "no compliance configuration exists for this source, so no attribution "
                "obligation, resource scope or data-minimisation profile can be supplied "
                "to a collector",
            ),
        )
    if compliance.review_version != review.review_version:
        raise AcquisitionNotAuthorizedError(
            source.source_id,
            (
                f"the compliance configuration targets review version "
                f"{compliance.review_version} and the current review is version "
                f"{review.review_version}",
            ),
        )

    return AcquisitionAuthorizationContext(
        source_id=source.source_id,
        canonical_name=source.canonical_name,
        approval_state=review.approval_state,
        review_version=review.review_version,
        reviewed_at=review.reviewed_at,
        next_review_at=review.next_review_at,
        access=tuple(_authorized_access(p) for p in source.access_profiles),
        resource_scope=compliance.resource_scope,
        # Governance input, never a collector's choice (§30). Resolution takes
        # the stricter of the baseline and any override, in that direction only.
        retention=resolve_retention(source.retention_override),
        attribution=compliance.attribution,
        data_minimisation=compliance.data_minimisation,
        verifications=tuple(records),
        issued_at=moment,
    )


def _authorized_access(profile: AccessProfile) -> AuthorizedAccess:
    return AuthorizedAccess(
        access_method=profile.access_method.value,
        label=profile.label,
        endpoint_url=profile.endpoint_url,
        documentation_url=profile.documentation_url,
        credential_references=tuple(profile.secret_references),
        rate_limit=RateLimit(
            known=profile.rate_limit_known,
            requests=profile.rate_limit_requests,
            period_seconds=profile.rate_limit_period_seconds,
            burst=profile.rate_limit_burst,
            concurrency=profile.rate_limit_concurrency,
            daily_quota=profile.rate_limit_daily_quota,
            origin=profile.rate_limit_origin,
        ),
    )
