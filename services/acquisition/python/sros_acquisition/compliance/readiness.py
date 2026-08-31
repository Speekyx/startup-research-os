"""Four separate facts about one source, none of them stored.

Mission 1.9.2 §23.

    eligible         may we collect from this source at all
    resource_ready   is there a concrete resource the review actually authorises
    implemented      does a collector exist
    enabled          is collection switched on here

The first, third and fourth already existed and were already kept apart -- the
package docstring on `IMPLEMENTED_COLLECTORS` records why, and Mission 1.6 added
`normalizable` as a fourth after a planner blocked normalization for a reason
that had stopped being true.

**`resource_ready` is the one this mission needed and did not have.** Between
Mission 1.7 and Mission 1.9.1, GDELT was eligible with an empty `datasets`
tuple: the gate said yes, the resource layer refused everything, and no single
answer said so. "Eligible" was the most specific word available and it read as
further along than it was.

**Nothing here is persisted.** Every field is derived on the spot from the
catalog, the compliance configuration and the registered collectors. A stored
`resource_ready` column would be a copy of a derivation, and a copy of a
derivation is a thing that goes stale -- which is the argument
`source-registry-v1.md` §3 makes for eligibility being a view.

**Nothing here is a gate.** `build_authorization` refuses; this explains. A
caller that consulted this instead of the gate would be reading a report where
it should be asking permission.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from sros_contracts import ResourceContentOrigin

from ..registry.models import SourceRecord
from .authorization import AcquisitionNotAuthorizedError, build_authorization
from .config import ComplianceConfig
from .resources import ResourceDescriptor, authorize_resource
from .verification import ConditionVerificationRecord

__all__ = ["AcquisitionReadiness", "evaluate_readiness"]


@dataclass(frozen=True)
class AcquisitionReadiness:
    """What stands between a source and a running collector, in order.

    **`enabled` is the switch on the record you passed in, and only that.**
    Enablement is a per-deployment fact that `sros-source enable` writes to
    `registry.sources`, while the catalog file is the governance record; a
    source can therefore read `enabled=False` here and be switched on in a
    particular database, which is World Bank's situation today. That is the
    separation working rather than a disagreement, and the CLI labels which
    record it read. The other three fields are the same everywhere.
    """

    source_id: str
    eligible: bool
    resource_ready: bool
    implemented: bool
    enabled: bool
    authorized_resources: tuple[str, ...] = ()
    blocking_reasons: tuple[str, ...] = ()
    resource_gaps: tuple[str, ...] = ()

    @property
    def next_step(self) -> str:
        """The one sentence a reader usually wants.

        Ordered by dependency, so it never names a later step while an earlier
        one is unmet -- the failure Mission 1.6 found in the planner.
        """
        if not self.eligible:
            return "pass the eligibility gate"
        if not self.resource_ready:
            return "authorise a concrete resource"
        if not self.implemented:
            return "implement a collector"
        if not self.enabled:
            return "enable the collector in this deployment"
        return "none: collection is available here"

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "eligible": self.eligible,
            "resource_ready": self.resource_ready,
            "implemented": self.implemented,
            "enabled": self.enabled,
            "authorized_resources": list(self.authorized_resources),
            "blocking_reasons": list(self.blocking_reasons),
            "resource_gaps": list(self.resource_gaps),
            "next_step": self.next_step,
        }


def evaluate_readiness(
    source: SourceRecord,
    use_profile_id: str,
    config: ComplianceConfig,
    environ: Mapping[str, str] | None = None,
    now: datetime | None = None,
    decisions: Sequence[ConditionVerificationRecord] = (),
) -> AcquisitionReadiness:
    """Report; never refuse. Building the context is how one refuses."""
    # Deferred so that importing the compliance package does not import the
    # package root that imports the registry -- the same shape
    # `_normalizable_sources` uses in `__init__.py`.
    from .. import IMPLEMENTED_COLLECTORS

    moment = now or datetime.now(UTC)
    implemented = source.source_id in IMPLEMENTED_COLLECTORS
    enabled = bool(source.collector_enabled)

    try:
        context = build_authorization(
            source, use_profile_id, config, environ=environ, now=moment, decisions=decisions
        )
    except AcquisitionNotAuthorizedError as exc:
        return AcquisitionReadiness(
            source_id=source.source_id,
            eligible=False,
            resource_ready=False,
            implemented=implemented,
            enabled=enabled,
            blocking_reasons=exc.reasons,
            resource_gaps=("no authorization context exists, so no resource can be reached",),
        )

    gaps: list[str] = []
    if not context.datasets:
        gaps.append(
            "no resource is enumerated for this source, so authorized_dataset() returns None "
            "for everything and no collector could build a descriptor"
        )

    # The self-consistency check, and the reason this is worth deriving rather
    # than reading `bool(datasets)`. An entry can be enumerated and still be
    # refused by the scope it sits next to -- a family the review did not
    # assess, a content origin the scope denies. Catching that here means the
    # contradiction surfaces in a diagnostic instead of on the first request.
    reachable: list[str] = []
    for dataset in context.datasets:
        descriptor = ResourceDescriptor(
            source_id=source.source_id,
            resource_id=dataset.resource_id,
            licence=dataset.licence,
            rights_basis=dataset.rights_basis,
            content_origin=_origin(dataset.content_origin),
            dataset_family=dataset.dataset_family,
        )
        result = authorize_resource(context.resource_scope, descriptor)
        if result.allowed:
            reachable.append(dataset.resource_id)
        else:
            gaps.append(
                f"{dataset.resource_id} is enumerated but its own scope refuses it: "
                + "; ".join(result.denial_reasons)
            )

    if context.datasets and not any(a.endpoint_url for a in context.access):
        gaps.append(
            "no access profile records an endpoint, so the host allowlist derived from the "
            "registry is empty and the transport refuses every request"
        )

    return AcquisitionReadiness(
        source_id=source.source_id,
        eligible=True,
        resource_ready=bool(reachable) and not gaps,
        implemented=implemented,
        enabled=enabled,
        authorized_resources=tuple(reachable),
        resource_gaps=tuple(gaps),
    )


def _origin(value: str) -> ResourceContentOrigin:
    """The configured content origin, as the enum the rules branch on.

    An unrecognised string becomes `UNKNOWN` rather than raising, because this
    module reports and the resource gate already denies `UNKNOWN` -- so a
    malformed entry shows up as a gap instead of as a crash in a diagnostic.
    """
    try:
        return ResourceContentOrigin(value)
    except ValueError:
        return ResourceContentOrigin.UNKNOWN
