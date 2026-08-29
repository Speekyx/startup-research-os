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
D-07 blocks acquisition, D-03 blocks scoring, and §34 puts NLP out of scope. A
planner that emitted runnable stages for those would be describing a system that
does not exist. The planner therefore returns a plan whose stages all carry an
explicit unavailable reason, and the orchestrator refuses to dispatch them.

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

__all__ = [
    "Capability",
    "BlockedCapability",
    "BLOCKED_CAPABILITIES",
    "PlannedStage",
    "ResearchExecutionPlan",
    "ResearchPlanner",
    "PLANNER_VERSION",
]

# Bumped whenever the stage graph or the blocking set changes. Recorded on the
# persisted plan so a session can be read years later against the planner that
# produced it (llm-reasoning-rules.md §9 applied to orchestration).
PLANNER_VERSION = "0.4.0"


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
    """

    capability: Capability
    decision_id: str
    reason: str
    governing_document: str

    def to_json(self) -> dict[str, object]:
        return {
            "capability": self.capability.value,
            "decision_id": self.decision_id,
            "reason": self.reason,
            "governing_document": self.governing_document,
        }


BLOCKED_CAPABILITIES: dict[Capability, BlockedCapability] = {
    Capability.ACQUISITION: BlockedCapability(
        capability=Capability.ACQUISITION,
        decision_id="D-07",
        reason=(
            "the source registry and its per-source legal review records do not exist, "
            "so no source may lawfully be collected from"
        ),
        governing_document="docs/data/data-principles.md §13",
    ),
    Capability.NORMALIZATION: BlockedCapability(
        capability=Capability.NORMALIZATION,
        decision_id="D-07",
        reason="there is nothing to normalize while acquisition is blocked",
        governing_document="docs/data/data-principles.md §13",
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
    Capability.SCORING: BlockedCapability(
        capability=Capability.SCORING,
        decision_id="D-03",
        reason=(
            "the evidence aggregation formula, recency behaviour and independence rules "
            "are undefined; implementing scoring would mean choosing them"
        ),
        governing_document="docs/domain/scoring-framework-v1.1.md §13",
    ),
}


@dataclass(frozen=True)
class PlannedStage:
    """One capability's place in the plan."""

    capability: Capability
    job_type: str
    depends_on: tuple[Capability, ...] = ()
    estimated_cost_units: float = 0.0

    @property
    def blocked(self) -> BlockedCapability | None:
        return BLOCKED_CAPABILITIES.get(self.capability)


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

    def incompleteness_reasons(self) -> tuple[str, ...]:
        """Human-readable reasons this plan cannot cover the search space."""
        return tuple(
            f"{b.capability.value} unavailable ({b.decision_id}): {b.reason}"
            for b in sorted(self.blocked, key=lambda b: b.capability.value)
        )


class ResearchPlanner:
    """Turns a ResearchContext into a plan.

    It does **not** decide research strategy — depth, source selection and
    breadth-then-depth ordering are meaningless while every source is blocked.
    What it does today is enumerate the pipeline honestly and say, per stage,
    why it cannot run.
    """

    def __init__(self, stages: tuple[PlannedStage, ...] = DEFAULT_STAGES) -> None:
        self._stages = stages

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

        jobs: list[JobSpec] = []
        blocked: list[BlockedCapability] = []

        for stage in self._stages:
            block = stage.blocked
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
        )
        # Fail here rather than at dispatch: a cycle discovered at dispatch is a
        # plan that runs partially and then stalls with no error.
        plan.ordered_jobs()
        return plan
