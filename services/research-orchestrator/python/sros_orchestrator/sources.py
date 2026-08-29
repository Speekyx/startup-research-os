"""Per-source acquisition availability.

Mission 1.0 §22. Before this module the orchestrator blocked ACQUISITION with
one sentence for the whole pipeline: *the source registry does not exist*. That
was true, and it was also unusable — it could not tell a caller which source was
missing, nor what would have to change for one to become collectable.

D-07 is resolved (`mission-1.0-report.md` §Decision resolution), so the sentence
is no longer true and the block must be **derived, per source, from the registry
itself** rather than restated from memory.

**Fail closed.** A planner given no provider, or a provider that cannot reach the
registry, blocks acquisition. Mission 1.0 §31 states the rule this implements:
uncertainty is never converted into permission. A source is collectable only
when the registry positively says so; silence is a refusal, not an approval.

**The database is the authority.** `RegistrySourceAvailability` reads
`registry.source_eligibility`, the same view `registry.require_eligibility_for_collector`
consults before it will let `collector_enabled` be set. The orchestrator
therefore cannot believe a source is usable that the database would refuse to
enable. `sros_acquisition` computes the same verdict in Python for review
tooling, and a test asserts the two agree rather than assuming it.

No credential, endpoint or access detail is read here. Availability answers
*whether*, never *how* — `how` belongs to a collector, and there is none.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Protocol

__all__ = [
    "SourceAvailability",
    "SourceAvailabilityReport",
    "SourceAvailabilityProvider",
    "UnconsultedRegistry",
    "StaticSourceAvailability",
    "RegistryDatabase",
    "RegistrySourceAvailability",
]


@dataclass(frozen=True)
class SourceAvailability:
    """One source's collectability, and the reasons against it.

    `blocking_reasons` is a list rather than a first reason, for the same cause
    the eligibility gate reports all failures: a reviewer who fixes one blocker
    and rediscovers the next on the following pass learns to distrust the tool.
    """

    source_id: str
    approval_state: str | None
    eligible: bool
    blocking_reasons: tuple[str, ...] = ()

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "approval_state": self.approval_state,
            "eligible": self.eligible,
            "blocking_reasons": list(self.blocking_reasons),
        }


@dataclass(frozen=True)
class SourceAvailabilityReport:
    """What the registry said, including whether it was asked.

    `consulted` is not redundant with an empty `sources`. "The registry holds no
    eligible source" and "the registry was never read" are different facts, and
    collapsing them would let an unwired planner produce the same output as a
    wired one that found nothing — which is how a missing integration survives
    review.
    """

    consulted: bool
    sources: tuple[SourceAvailability, ...] = ()
    unavailable_reason: str | None = None

    @property
    def eligible(self) -> tuple[SourceAvailability, ...]:
        return tuple(s for s in self.sources if s.eligible)

    @property
    def blocked(self) -> tuple[SourceAvailability, ...]:
        return tuple(s for s in self.sources if not s.eligible)

    @property
    def eligible_source_ids(self) -> tuple[str, ...]:
        return tuple(sorted(s.source_id for s in self.eligible))


class SourceAvailabilityProvider(Protocol):
    """The only thing the planner needs to know about sources."""

    def source_availability(self) -> SourceAvailabilityReport: ...


@dataclass(frozen=True)
class UnconsultedRegistry:
    """The default provider: nothing was asked, so nothing is permitted.

    Used when a planner is constructed without a registry — in a unit test, or
    in a caller that forgot to wire one. Both must behave the same as a refusal.
    """

    reason: str = "the source registry was not consulted, so no source may be assumed collectable"

    def source_availability(self) -> SourceAvailabilityReport:
        return SourceAvailabilityReport(consulted=False, unavailable_reason=self.reason)


@dataclass(frozen=True)
class StaticSourceAvailability:
    """A fixed answer. For tests, and only for tests.

    It exists so a test can exercise the *unblocked* branch without approving a
    real platform: eligibility in production comes from a reviewed registry row,
    never from a literal in code.
    """

    sources: tuple[SourceAvailability, ...] = ()

    def source_availability(self) -> SourceAvailabilityReport:
        return SourceAvailabilityReport(consulted=True, sources=self.sources)


class RegistryDatabase(Protocol):
    """A non-tenant connection provider.

    Deliberately not `TenantDatabase`. Source definitions and their reviews are
    global platform metadata with no `workspace_id` and no row-level security
    policy (Mission 1.0 §25): a source assessed differently per workspace would
    make provenance incomparable across workspaces. Reading them through a
    tenant transaction would imply an isolation that does not exist.
    """

    def connection(self) -> AbstractContextManager[Any]: ...


@dataclass(frozen=True)
class RegistrySourceAvailability:
    """Reads `registry.source_eligibility`.

    Read-only by construction as well as by intent: the runtime role holds
    SELECT and nothing else on `registry.*`, so this class could not enable a
    source even if it tried to.
    """

    db: RegistryDatabase

    def source_availability(self) -> SourceAvailabilityReport:
        with self.db.connection() as conn:
            rows = conn.execute(
                """SELECT source_id, approval_state, blocking_reasons
                     FROM registry.source_eligibility
                    ORDER BY source_id"""
            ).fetchall()
        return SourceAvailabilityReport(
            consulted=True,
            sources=tuple(
                SourceAvailability(
                    source_id=row[0],
                    approval_state=row[1],
                    # The view's contract: an empty reason array is the pass.
                    # Eligibility is never stored as a boolean anywhere, so
                    # there is no flag that can drift away from its reasons.
                    eligible=not row[2],
                    blocking_reasons=tuple(row[2] or ()),
                )
                for row in rows
            ),
        )
