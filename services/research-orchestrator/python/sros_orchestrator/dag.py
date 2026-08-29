"""Dependency-aware execution ordering.

Mission 0.4 §12. A small explicit orchestration layer, not a workflow engine.

**Why not Airflow or Temporal.** The system already has Celery (ADR-004), which
provides the queue, the retry, the routing and the dead-letter path. What is
missing is a dependency list and a rule for when a job becomes runnable. That is
this module: about a hundred lines, no new process, no new datastore, no second
scheduler competing with Celery for authority over what runs.

Adding a workflow engine now would buy a UI and a DSL, and cost a second
operational surface, a second retry semantics and a second place where a job can
be stuck. ADR-004 already rejected a dual-queue architecture for that reason.

**When a workflow engine becomes justified** — recorded so the decision has a
trigger rather than a preference:

  1. Dynamic fan-out where the number of downstream jobs is unknown until an
     upstream job finishes, and that count is large enough that materialising
     the edges eagerly is impractical.
  2. Long-running human-in-the-loop steps (`llm-reasoning-rules.md` §11 review)
     that must survive days, where a durable timer beats a database poll.
  3. Cross-session workflows: work that spans several ResearchSessions and
     therefore has no single owner row to hang state on.
  4. More than one team operating the pipeline, at which point a shared UI stops
     being a convenience.

None of those is true today. Two of them are plausible within a year, which is
why this module keeps its dependency data in a table rather than in code.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping, Sequence

from .jobs import JobSpec, JobStatus

__all__ = [
    "DependencyCycleError",
    "UnknownDependencyError",
    "topological_order",
    "ready_job_ids",
    "blocked_by_dependencies",
    "dependency_closure",
]


class DependencyCycleError(ValueError):
    """The dependency graph contains a cycle.

    Detected at planning time rather than at dispatch time: a cycle discovered
    at dispatch is a plan that runs partially and then stalls with no error, and
    a stalled queue is the failure mode ADR-004 §Observability calls out as
    worse than a visible one.
    """


class UnknownDependencyError(ValueError):
    """A job depends on an id that is not in the graph."""


def _index(jobs: Iterable[JobSpec]) -> dict[uuid.UUID, JobSpec]:
    indexed: dict[uuid.UUID, JobSpec] = {}
    for job in jobs:
        if job.job_id in indexed:
            raise ValueError(f"duplicate job id in graph: {job.job_id}")
        indexed[job.job_id] = job
    return indexed


def _validate_edges(indexed: Mapping[uuid.UUID, JobSpec]) -> None:
    for job in indexed.values():
        for dependency in job.dependencies:
            if dependency not in indexed:
                raise UnknownDependencyError(
                    f"job {job.job_id} depends on {dependency}, which is not in the graph. "
                    "A dependency outside the plan cannot be waited on, so the job would "
                    "never become ready."
                )


def topological_order(jobs: Sequence[JobSpec]) -> list[JobSpec]:
    """Order jobs so every job follows its dependencies.

    Kahn's algorithm. Ties are broken by job id so the order is deterministic:
    a plan that reorders between two runs makes a resumed session hard to
    compare with the run it resumed.
    """
    indexed = _index(jobs)
    _validate_edges(indexed)

    remaining = {job_id: set(job.dependencies) for job_id, job in indexed.items()}
    ordered: list[JobSpec] = []

    while remaining:
        available = sorted(
            (job_id for job_id, deps in remaining.items() if not deps), key=lambda j: str(j)
        )
        if not available:
            stuck = sorted(str(job_id) for job_id in remaining)
            raise DependencyCycleError(
                f"dependency cycle among {len(stuck)} job(s): {stuck}. "
                "A cycle would stall the queue silently rather than fail."
            )
        for job_id in available:
            ordered.append(indexed[job_id])
            del remaining[job_id]
        for deps in remaining.values():
            deps.difference_update(available)

    return ordered


def ready_job_ids(
    jobs: Sequence[JobSpec],
    statuses: Mapping[uuid.UUID, JobStatus],
) -> list[uuid.UUID]:
    """Jobs whose dependencies have all SUCCEEDED and that are still waiting.

    A dependency that did not succeed does not make its dependents ready, and it
    does not make them fail either: `blocked_by_dependencies` reports those
    separately, because "did not run because an upstream did not run" is a gap
    with a cause, not a failure of its own.
    """
    indexed = _index(jobs)
    _validate_edges(indexed)

    ready: list[uuid.UUID] = []
    for job_id, job in indexed.items():
        if statuses.get(job_id, job.status) is not JobStatus.PENDING:
            continue
        if all(statuses.get(dep) is JobStatus.SUCCEEDED for dep in job.dependencies):
            ready.append(job_id)
    return sorted(ready, key=lambda j: str(j))


def blocked_by_dependencies(
    jobs: Sequence[JobSpec],
    statuses: Mapping[uuid.UUID, JobStatus],
) -> dict[uuid.UUID, list[uuid.UUID]]:
    """Waiting jobs whose dependencies reached a terminal non-success state.

    These can never become ready. Reporting them is what turns a stalled plan
    into a gap report instead of a queue that quietly stops moving.
    """
    indexed = _index(jobs)
    _validate_edges(indexed)

    dead_ends: dict[uuid.UUID, list[uuid.UUID]] = {}
    unsuccessful = {JobStatus.FAILED, JobStatus.BLOCKED, JobStatus.CANCELLED}
    for job_id, job in indexed.items():
        if statuses.get(job_id, job.status) in (
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
            JobStatus.BLOCKED,
            JobStatus.CANCELLED,
        ):
            continue
        causes = [dep for dep in job.dependencies if statuses.get(dep) in unsuccessful]
        if causes:
            dead_ends[job_id] = sorted(causes, key=lambda j: str(j))
    return dead_ends


def dependency_closure(jobs: Sequence[JobSpec], job_id: uuid.UUID) -> set[uuid.UUID]:
    """Every job that must succeed before `job_id` can run, transitively."""
    indexed = _index(jobs)
    _validate_edges(indexed)
    if job_id not in indexed:
        raise UnknownDependencyError(f"{job_id} is not in the graph")

    seen: set[uuid.UUID] = set()
    stack = list(indexed[job_id].dependencies)
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(indexed[current].dependencies)
    return seen
