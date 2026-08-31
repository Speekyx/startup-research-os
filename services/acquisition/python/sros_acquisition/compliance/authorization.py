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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from sros_contracts import SourceApprovalState
from sros_contracts.errors import ContractError

from ..registry.eligibility import evaluate_eligibility
from ..registry.models import AccessProfile, SourceRecord
from ..registry.retention import EffectiveRetention, resolve_retention
from .config import (
    AcquisitionBounds,
    AttributionObligation,
    AuthorizedDataset,
    ComplianceConfig,
    DataMinimisationProfile,
    ResourceScope,
    RouteAuthorization,
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
    # WHICH USE this authorization was granted for (Mission 1.15.5 §13). A
    # collector holding a context can be asked what it is authorised to be
    # doing, and a job that recorded it can be asked years later under which
    # profile its data was collected.
    use_profile_id: str
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
    datasets: tuple[AuthorizedDataset, ...]
    verifications: tuple[ConditionVerificationRecord, ...]
    issued_at: datetime
    # The reviewed route restriction, carried so a refusal can NAME the blocked
    # route rather than reporting an absence (Mission 1.15.6 §13). `None` where
    # no review has restricted routes for this (source, profile), in which case
    # `access` holds every registered profile exactly as it did before.
    route_authorization: RouteAuthorization | None = None
    # `None` when no review has set a ceiling for this source. Not "unbounded":
    # unasked (Mission 1.9.2 §15).
    acquisition_bounds: AcquisitionBounds | None = None

    def authorized_dataset(self, resource_id: str) -> AuthorizedDataset | None:
        """The entry that authorises one resource, or `None`.

        A collector builds its descriptor from this, never from what a caller
        claims about a resource (§7). `None` is a refusal the caller must
        handle: there is no permissive default, because a resource nobody
        reviewed has no licence to check against.
        """
        return next((d for d in self.datasets if d.resource_id == resource_id), None)

    def authorize_resource(self, descriptor: ResourceDescriptor) -> ResourceAuthorization:
        """The only sanctioned way to reach a specific dataset, series or record.

        Source-level authorization is not resource-level authorization
        (§11, §12). Holding this context permits nothing on its own; each
        resource is asked for separately and refused by default.
        """
        return authorize_resource(self.resource_scope, descriptor)

    def authorize_route(self, label: str | None) -> tuple[str, ...]:
        """Why binding acquisition to this access route is refused, or nothing.

        Mission 1.15.6 §22. The load-bearing guarantee is not this method: it is
        that `access` below holds ONLY authorised routes, so a collector that
        selects a route by label the way `GdeltWebNgramCollector._route` does
        finds nothing for a blocked one and cannot reach a host. This method
        exists so that the refusal is *named* -- "refused by name" reads
        differently from "not found", and the second is what an engineer
        debugs for an hour.

        A source with no reviewed route restriction returns nothing, which says
        the question has not been asked rather than that any route is approved.
        """
        if self.route_authorization is None:
            return ()
        return self.route_authorization.refusals(label)

    def authorize_fields(self, requested: Sequence[str] | None) -> tuple[str, ...]:
        """Why this field selection is not the minimised one, or nothing.

        Mission 1.15.6 §8. Asked BEFORE a request is composed, because the
        source supports field selection and an obligation about what is
        retrieved cannot be met by discarding afterwards (§9).
        """
        return self.data_minimisation.refusals(requested)

    @property
    def authorized_route_labels(self) -> tuple[str, ...]:
        """The routes a collector may bind to, in registry order."""
        return tuple(access.label for access in self.access)

    def authorize_job_size(self, file_count: int | None) -> tuple[str, ...]:
        """Why a job of this size exceeds what the review approved, or nothing.

        Mission 1.9.2 §15. Separate from `authorize_resource` because the two
        answer different questions -- *may we reach this* and *may we take this
        much* -- and a source can fail the second while passing the first.

        A source with no reviewed bound returns nothing, which says the question
        has not been asked rather than that any size is approved.
        """
        if self.acquisition_bounds is None:
            return ()
        return self.acquisition_bounds.refusals(file_count)

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
            "use_profile_id": self.use_profile_id,
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
            "authorized_datasets": [
                {
                    "resource_id": d.resource_id,
                    "dataset_family": d.dataset_family,
                    "rights_basis": d.rights_basis.value,
                    "licence": d.licence,
                    "content_origin": d.content_origin,
                }
                for d in self.datasets
            ],
            "acquisition_bounds": (
                self.acquisition_bounds.to_json() if self.acquisition_bounds else None
            ),
            "route_authorization": (
                self.route_authorization.to_json() if self.route_authorization else None
            ),
            "authorized_route_labels": list(self.authorized_route_labels),
            "verifications": [v.to_json() for v in self.verifications],
            "design_eligible": self.design_eligible,
            "issued_at": self.issued_at.isoformat(),
        }


def build_authorization(
    source: SourceRecord,
    use_profile_id: str,
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

    `use_profile_id` is required and never defaulted (Mission 1.15.5 §12, §15).
    An authorization that did not name the use it was granted for could be held
    by a collector running under any use at all, which is the failure the whole
    profile mechanism exists to prevent.
    """
    moment = now or datetime.now(UTC)
    records = (
        verifications
        if verifications is not None
        else verify_source(source, use_profile_id, config, environ)
    )

    result = evaluate_eligibility(source, use_profile_id, moment, satisfied_condition_keys(records))
    if not result.eligible:
        raise AcquisitionNotAuthorizedError(source.source_id, result.blocking_reasons)

    review = source.review_for(use_profile_id)
    if review is None:  # pragma: no cover - the gate above already refuses this
        raise AcquisitionNotAuthorizedError(
            source.source_id, (f"no policy review exists for use profile {use_profile_id!r}",)
        )

    compliance = config.get(source.source_id, use_profile_id)
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

    access = _reviewed_access(source, compliance.route_authorization)

    return AcquisitionAuthorizationContext(
        source_id=source.source_id,
        use_profile_id=use_profile_id,
        canonical_name=source.canonical_name,
        approval_state=review.approval_state,
        review_version=review.review_version,
        reviewed_at=review.reviewed_at,
        next_review_at=review.next_review_at,
        access=access,
        resource_scope=compliance.resource_scope,
        # Governance input, never a collector's choice (§30). Resolution takes
        # the stricter of the baseline and any override, in that direction only.
        retention=resolve_retention(source.retention_override),
        attribution=compliance.attribution,
        data_minimisation=compliance.data_minimisation,
        datasets=compliance.datasets,
        acquisition_bounds=compliance.acquisition_bounds,
        route_authorization=compliance.route_authorization,
        verifications=tuple(records),
        issued_at=moment,
    )


def _reviewed_access(
    source: SourceRecord, routes: RouteAuthorization | None
) -> tuple[AuthorizedAccess, ...]:
    """The routes the context hands a collector: the reviewed ones, and no others.

    Mission 1.15.6 §22, ADR-028. Before this mission the context carried EVERY
    registered access profile, because an access profile is a fact about the
    source and the context had nothing to filter it with. That was survivable
    while no approving source had a route its review refused; TED is the first
    that does, and its refused route is a full bulk download of the corpus whose
    database-right exposure is the open question.

    A collector selects its route by label -- `GdeltWebNgramCollector._route`
    is the existing pattern, and its own docstring records that taking
    `context.access[0]` would silently authorise a second host. Filtering here
    is what makes that pattern safe rather than careful: a blocked label is not
    in the tuple, so there is no endpoint to read, no host to allowlist, and the
    transport has nothing to be pointed at.

    Sources with no reviewed route restriction are unchanged. `None` means the
    question was never asked for that (source, profile), and answering it here
    by inventing an allowlist would be this module setting permissions.
    """
    if routes is None:
        return tuple(_authorized_access(profile) for profile in source.access_profiles)
    registered = {profile.label: profile for profile in source.access_profiles}
    missing = sorted(routes.allowed_labels - registered.keys())
    if missing:
        # §13. A route the review authorised and the registry does not record is
        # not a route: there is no endpoint, no rate-limit metadata and nothing
        # to bind to. Refused rather than skipped, because skipping it would
        # quietly narrow the authorisation to whatever happened to exist.
        raise AcquisitionNotAuthorizedError(
            source.source_id,
            (
                f"the review authorises access route(s) {missing} that the registry does "
                "not record for this source. An authorised route with no access profile "
                "has no endpoint to reach and nothing to check a host against",
            ),
        )
    return tuple(_authorized_access(registered[label]) for label in sorted(routes.allowed_labels))


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
