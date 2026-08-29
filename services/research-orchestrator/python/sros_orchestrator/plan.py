"""The ResearchExecutionPlan.

Mission 0.4 §10. **An execution structure, not a domain entity.** Ontology V2
does not define a plan, and this module does not invent one: nothing here
becomes part of the opportunity vocabulary, nothing here is scored, and no
consumer outside the orchestrator reads it.

What it does is make "intended versus covered" answerable. Without a recorded
intention, Research Completeness has nothing to measure against and degrades
into whatever the collectors happened to return
(`services/research-orchestrator/README.md` §Why it exists).

**Every domain stage is currently BLOCKED, and that is the honest output.**
No CALIBRATED aggregation profile exists so scoring cannot run, §34 puts NLP out
of scope, and no source has passed the governance gate. A planner that emitted runnable stages for those would be
describing a system that does not exist. The planner therefore returns a plan
whose stages all carry an explicit unavailable reason, and the orchestrator
refuses to dispatch them.

**Acquisition is the exception to "statically blocked" (Mission 1.0 §22).** D-07
is resolved: the Source Registry exists, so the reason acquisition cannot run is
no longer *the registry is missing* but *these specific sources are not
collectable, for these specific reasons*. That answer is read from the registry
at plan time, per source, and never restated from memory here. A planner wired
to no registry blocks acquisition, because silence is a refusal.

The dispatch, retry, resume and budget machinery is still real and still tested.
It is exercised with job specs supplied directly by a caller, which is what a
future capability will do once it is unblocked.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum

from sros_contracts import ResearchContext

from .dag import topological_order
from .jobs import JobSpec, JobStatus, build_idempotency_key, deterministic_job_id
from .sources import (
    SourceAvailability,
    SourceAvailabilityProvider,
    SourceAvailabilityReport,
    UnconsultedRegistry,
)

__all__ = [
    "Capability",
    "BlockedCapability",
    "BLOCKED_CAPABILITIES",
    "STATIC_BLOCKED_CAPABILITIES",
    "acquisition_block",
    "PlannedStage",
    "ResearchExecutionPlan",
    "ResearchPlanner",
    "PLANNER_VERSION",
]

# Bumped whenever the stage graph or the blocking set changes. Recorded on the
# persisted plan so a session can be read years later against the planner that
# produced it (llm-reasoning-rules.md §9 applied to orchestration).
PLANNER_VERSION = "1.0.0"


class Capability(StrEnum):
    """A pipeline capability the plan may need.

    These mirror the manifest pipeline stages, not a queue and not a service
    class: a capability is a thing the system can or cannot currently do.
    """

    ACQUISITION = "ACQUISITION"
    NORMALIZATION = "NORMALIZATION"
    NLP_EXTRACTION = "NLP_EXTRACTION"
    OPPORTUNITY_DISCOVERY = "OPPORTUNITY_DISCOVERY"
    SCORING = "SCORING"


@dataclass(frozen=True)
class BlockedCapability:
    """Why a capability cannot be planned, and under whose authority.

    `decision_id` is not decoration. A blocked stage with a prose reason invites
    someone to decide the prose no longer applies. A blocked stage that names
    D-03 points at a register entry that says who may unblock it
    (`mission-0.1.1-decisions.md` §3).

    Since Mission 1.0 it names either a decision-register entry (`D-03`, `D-12`)
    or a **governance gate** (`SOURCE-REGISTRY-GATE`). The distinction matters:
    a decision is unblocked by someone deciding, a gate is unblocked by a source
    passing review. Neither is unblocked by editing this file.

    `source_states` is populated only for a gate. It is what turns "acquisition
    is unavailable" into "these thirteen sources are unavailable, each for a
    stated reason", which is the difference between a blocker a reader can act
    on and one they can only accept.
    """

    capability: Capability
    decision_id: str
    reason: str
    governing_document: str
    source_states: tuple[SourceAvailability, ...] = ()

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "capability": self.capability.value,
            "decision_id": self.decision_id,
            "reason": self.reason,
            "governing_document": self.governing_document,
        }
        if self.source_states:
            payload["source_states"] = [s.to_json() for s in self.source_states]
        return payload


# Capabilities blocked by something that does not change between plans.
# ACQUISITION is deliberately absent: its block is derived per source from the
# registry by `acquisition_block`, because since Mission 1.0 the answer differs
# per source and changes when a review lands.
STATIC_BLOCKED_CAPABILITIES: dict[Capability, BlockedCapability] = {
    Capability.NORMALIZATION: BlockedCapability(
        capability=Capability.NORMALIZATION,
        decision_id="NO-COLLECTOR",
        reason=(
            "no collector is implemented, so acquisition produces no raw record to "
            "normalize; this stays true independently of how many sources pass review"
        ),
        governing_document="docs/data/source-registry-v1.md §Collector eligibility",
    ),
    Capability.NLP_EXTRACTION: BlockedCapability(
        capability=Capability.NLP_EXTRACTION,
        decision_id="D-12",
        reason=(
            "embedding model versioning and the re-embedding strategy are undecided, "
            "and NLP execution is outside this mission's scope"
        ),
        governing_document="docs/domain/opportunity-ontology-v2.md §16",
    ),
    Capability.OPPORTUNITY_DISCOVERY: BlockedCapability(
        capability=Capability.OPPORTUNITY_DISCOVERY,
        decision_id="D-12",
        reason="discovery consumes NLP signals, which are not produced",
        governing_document="docs/domain/opportunity-ontology-v2.md §16",
    ),
    # The reason CHANGED in Mission 1.2, because the old one became false.
    #
    # It used to read "the aggregation formula is undefined". Mission 1.1
    # defined it, so that sentence stopped being true -- and a false blocking
    # reason is worse than a vague one: it invites someone to conclude the block
    # no longer applies. What actually blocks scoring now is the SECOND gate.
    Capability.SCORING: BlockedCapability(
        capability=Capability.SCORING,
        decision_id="PROFILE-NOT-CALIBRATED",
        reason=(
            "the aggregation algorithm is defined but no CALIBRATED "
            "EvidenceAggregationProfile exists; its parameters were never fitted to "
            "labelled data, so a score would carry numbers nobody measured"
        ),
        governing_document="docs/domain/evidence-aggregation-framework-v1.md §14",
    ),
}

# Kept under the pre-Mission-1.0 name so existing readers and imports still
# resolve. It is the static register: ACQUISITION is not in it.
BLOCKED_CAPABILITIES = STATIC_BLOCKED_CAPABILITIES

# The gate's identifier. Not a decision id: no one unblocks acquisition by
# deciding. A source becomes collectable by passing the review recorded in the
# registry, and by nothing else.
SOURCE_REGISTRY_GATE = "SOURCE-REGISTRY-GATE"
SOURCE_REGISTRY_DOCUMENT = "docs/data/source-registry-v1.md §Collector eligibility"


def acquisition_block(report: SourceAvailabilityReport) -> BlockedCapability | None:
    """Derive the ACQUISITION block from what the registry said.

    Returns `None` only when the registry was consulted **and** named at least
    one eligible source. Every other outcome blocks, including the outcome where
    the registry was never read: Mission 1.0 §31 forbids turning an unknown into
    a permission, and an unwired planner is an unknown.
    """
    if not report.consulted:
        return BlockedCapability(
            capability=Capability.ACQUISITION,
            decision_id=SOURCE_REGISTRY_GATE,
            reason=(
                report.unavailable_reason
                or "the source registry was not consulted, so no source may be collected"
            ),
            governing_document=SOURCE_REGISTRY_DOCUMENT,
        )
    if report.eligible:
        return None

    blocked = report.blocked
    if not blocked:
        # A registry that holds no source at all. Distinguished from one whose
        # sources are all refused, because the remedy is different: register a
        # candidate, rather than finish a review.
        reason = "the source registry is empty, so there is no source to collect from"
    else:
        reason = (
            f"no source has passed the governance gate "
            f"({len(blocked)} registered, 0 collector-eligible)"
        )
    return BlockedCapability(
        capability=Capability.ACQUISITION,
        decision_id=SOURCE_REGISTRY_GATE,
        reason=reason,
        governing_document=SOURCE_REGISTRY_DOCUMENT,
        source_states=blocked,
    )


@dataclass(frozen=True)
class PlannedStage:
    """One capability's place in the plan."""

    capability: Capability
    job_type: str
    depends_on: tuple[Capability, ...] = ()
    estimated_cost_units: float = 0.0

    @property
    def blocked(self) -> BlockedCapability | None:
        """The static block, if any. ACQUISITION's is resolved by the planner."""
        return STATIC_BLOCKED_CAPABILITIES.get(self.capability)


# The pipeline shape from PROJECT_MANIFEST.md §Mission, expressed as stages.
# Job types route through sros_workers.TASK_ROUTES, so the orchestrator and the
# broker cannot disagree about which queue a stage belongs to.
DEFAULT_STAGES: tuple[PlannedStage, ...] = (
    PlannedStage(Capability.ACQUISITION, "acquire.collect"),
    PlannedStage(Capability.NORMALIZATION, "normalize.records", (Capability.ACQUISITION,)),
    PlannedStage(Capability.NLP_EXTRACTION, "nlp.extract.signals", (Capability.NORMALIZATION,)),
    PlannedStage(
        Capability.OPPORTUNITY_DISCOVERY,
        "nlp.cluster.opportunities",
        (Capability.NLP_EXTRACTION,),
    ),
    PlannedStage(Capability.SCORING, "score.opportunity", (Capability.OPPORTUNITY_DISCOVERY,)),
)


@dataclass(frozen=True)
class ResearchExecutionPlan:
    """What the orchestrator intended to run for one session."""

    workspace_id: str
    research_session_id: str
    correlation_id: str
    jobs: tuple[JobSpec, ...]
    blocked: tuple[BlockedCapability, ...]
    planner_version: str = PLANNER_VERSION
    plan_id: uuid.UUID = field(default_factory=uuid.uuid4)
    # What the registry said when this plan was built. Recorded rather than
    # recomputed: a plan read back next year must show the sources that were
    # available THEN, not the ones available at the moment someone reads it.
    source_availability: SourceAvailabilityReport | None = None

    @property
    def estimated_cost_units(self) -> float:
        """Cost of the work that could actually be dispatched.

        Blocked jobs contribute nothing: reserving budget for work that will not
        run would understate what remains available for work that will.
        """
        return sum(job.estimated_cost_units for job in self.jobs if not self.is_blocked(job))

    @staticmethod
    def is_blocked(job: JobSpec) -> bool:
        return job.status is JobStatus.BLOCKED

    @property
    def dispatchable_jobs(self) -> tuple[JobSpec, ...]:
        return tuple(job for job in self.jobs if not self.is_blocked(job))

    @property
    def blocked_jobs(self) -> tuple[JobSpec, ...]:
        return tuple(job for job in self.jobs if self.is_blocked(job))

    @property
    def blocked_capability_names(self) -> tuple[str, ...]:
        return tuple(sorted(b.capability.value for b in self.blocked))

    def blocked_reasons_json(self) -> dict[str, object]:
        return {b.capability.value: b.to_json() for b in self.blocked}

    def ordered_jobs(self) -> list[JobSpec]:
        """Jobs in dependency order. Raises on a cycle."""
        return topological_order(list(self.jobs))

    @property
    def eligible_source_ids(self) -> tuple[str, ...]:
        """Sources the registry cleared for collection when this plan was built.

        Empty today, and empty is the correct answer rather than a placeholder:
        no source in the catalog has passed the gate.
        """
        report = self.source_availability
        return report.eligible_source_ids if report is not None else ()

    def incompleteness_reasons(self) -> tuple[str, ...]:
        """Human-readable reasons this plan cannot cover the search space."""
        return tuple(
            f"{b.capability.value} unavailable ({b.decision_id}): {b.reason}"
            for b in sorted(self.blocked, key=lambda b: b.capability.value)
        )

    def blocked_source_reasons(self) -> tuple[str, ...]:
        """Per-source detail behind an acquisition block, one line each.

        Separate from `incompleteness_reasons` because the audiences differ: the
        session-level reason says the search space was not covered, and this
        says which door was closed and by what.
        """
        return tuple(
            f"{state.source_id} ({state.approval_state or 'NO REVIEW'}): "
            + "; ".join(state.blocking_reasons)
            for block in self.blocked
            for state in block.source_states
        )


class ResearchPlanner:
    """Turns a ResearchContext into a plan.

    It does **not** decide research strategy — depth, source selection and
    breadth-then-depth ordering are meaningless while every source is blocked.
    What it does today is enumerate the pipeline honestly and say, per stage,
    why it cannot run.

    `sources` is the registry it asks about acquisition. The default refuses
    everything, so a planner constructed the pre-Mission-1.0 way keeps producing
    a blocked acquisition stage instead of silently permitting collection.
    """

    def __init__(
        self,
        stages: tuple[PlannedStage, ...] = DEFAULT_STAGES,
        sources: SourceAvailabilityProvider | None = None,
    ) -> None:
        self._stages = stages
        self._sources: SourceAvailabilityProvider = sources or UnconsultedRegistry()

    def plan(
        self,
        workspace_id: str,
        research_session_id: str,
        correlation_id: str,
        context: ResearchContext,
    ) -> ResearchExecutionPlan:
        if not workspace_id:
            raise ValueError("workspace_id is required to plan a session (ADR-005)")
        if not isinstance(context, ResearchContext):
            raise TypeError("a ResearchContext is required to plan a session")

        # Payloads first, because the job id is derived from the idempotency
        # key, which is derived from the payload. Deterministic ids are what
        # make a replan after a crash converge on the existing ledger rows
        # instead of inserting a parallel copy (§13).
        payloads: dict[Capability, dict[str, object]] = {
            stage.capability: {
                "capability": stage.capability.value,
                # The scope the stage would have operated on. Recorded even for
                # a blocked stage: it is what makes the gap specific rather than
                # "something did not happen".
                "market_scope_key": context.market_scope.key(),
            }
            for stage in self._stages
        }
        job_ids: dict[Capability, uuid.UUID] = {
            stage.capability: deterministic_job_id(
                build_idempotency_key(
                    stage.job_type,
                    workspace_id,
                    research_session_id,
                    payloads[stage.capability],
                )
            )
            for stage in self._stages
        }

        # Asked once per plan, not once per stage: two reads of a live registry
        # inside one planning pass could disagree, and a plan that contradicts
        # itself is worse than one that is out of date.
        availability = self._sources.source_availability()
        acquisition = acquisition_block(availability)

        jobs: list[JobSpec] = []
        blocked: list[BlockedCapability] = []

        for stage in self._stages:
            block = acquisition if stage.capability is Capability.ACQUISITION else stage.blocked
            spec = JobSpec(
                job_id=job_ids[stage.capability],
                job_type=stage.job_type,
                workspace_id=workspace_id,
                research_session_id=research_session_id,
                correlation_id=correlation_id,
                dependencies=tuple(job_ids[dep] for dep in stage.depends_on),
                estimated_cost_units=stage.estimated_cost_units,
                payload=payloads[stage.capability],
            )
            if block is not None:
                blocked.append(block)
                spec = spec.blocked(f"{block.decision_id}: {block.reason}")
            jobs.append(spec)

        plan = ResearchExecutionPlan(
            workspace_id=workspace_id,
            research_session_id=research_session_id,
            correlation_id=correlation_id,
            jobs=tuple(jobs),
            blocked=tuple(blocked),
            source_availability=availability,
        )
        # Fail here rather than at dispatch: a cycle discovered at dispatch is a
        # plan that runs partially and then stalls with no error.
        plan.ordered_jobs()
        return plan
