"""Queue topology, routing and retry policy.

Deliberately free of any Celery import: this module is pure data plus pure
functions, so the routing and retry rules can be tested without a broker, a
worker or even the Celery package installed. `celery_app.py` consumes it.

ADR-004 governs everything here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "Queue",
    "RetryPolicy",
    "QUEUES",
    "RETRY_POLICIES",
    "TASK_ROUTES",
    "route_task",
    "retry_policy_for",
    "REQUIRED_HEADERS",
]


class Queue(StrEnum):
    """One queue per job class, each with its own worker pool.

    Slow acquisition must not starve fast analysis, and heavy embedding work
    must not monopolize the pool. Per-source concurrency limits live here too,
    which is how rate-limit compliance becomes a queue configuration rather than
    something each new collector has to remember.
    """

    ACQUISITION = "acquisition"
    NLP = "nlp"
    EMBEDDING = "embedding"
    ANALYSIS = "analysis"
    MAINTENANCE = "maintenance"


@dataclass(frozen=True)
class QueueConfig:
    name: str
    concurrency: int
    prefetch_multiplier: int
    task_time_limit_seconds: int
    description: str


# Prefetch is 1 for every long-running queue on purpose. The Celery default (4)
# lets one worker reserve four slow jobs while its siblings idle, which turns a
# rate-limited collector into a stalled queue.
QUEUES: dict[Queue, QueueConfig] = {
    Queue.ACQUISITION: QueueConfig(
        name="acquisition",
        concurrency=4,
        prefetch_multiplier=1,
        task_time_limit_seconds=600,
        description="Network-bound collection and browser automation. External rate limits apply.",
    ),
    Queue.NLP: QueueConfig(
        name="nlp",
        concurrency=2,
        prefetch_multiplier=1,
        task_time_limit_seconds=300,
        description="Extraction and classification. LLM-backed, so budget-consuming.",
    ),
    Queue.EMBEDDING: QueueConfig(
        name="embedding",
        concurrency=1,
        prefetch_multiplier=1,
        task_time_limit_seconds=900,
        description="Compute-heavy batched embedding and clustering.",
    ),
    Queue.ANALYSIS: QueueConfig(
        name="analysis",
        concurrency=4,
        prefetch_multiplier=2,
        task_time_limit_seconds=180,
        description="Pure computation over stored inputs. Fast.",
    ),
    Queue.MAINTENANCE: QueueConfig(
        name="maintenance",
        concurrency=1,
        prefetch_multiplier=1,
        task_time_limit_seconds=1800,
        description="Scheduled work: retention sweeps, decay, re-embedding. Never starved.",
    ),
}


@dataclass(frozen=True)
class RetryPolicy:
    """Retry policy per job class. Never global.

    A global policy is either too aggressive for a rate-limited source or too
    timid for a transient network blip.
    """

    max_retries: int
    initial_backoff_seconds: float
    backoff_multiplier: float
    jitter: bool
    max_backoff_seconds: float = 600.0

    def backoff_for(self, attempt: int) -> float:
        """Backoff before `attempt` (1-based), before jitter is applied."""
        if attempt < 1:
            raise ValueError("attempt is 1-based")
        delay = self.initial_backoff_seconds * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_backoff_seconds)


# Jitter is mandatory on anything that touches an external source: synchronized
# retries across workers are how a rate limit becomes a ban (ADR-004).
RETRY_POLICIES: dict[Queue, RetryPolicy] = {
    Queue.ACQUISITION: RetryPolicy(5, 5.0, 2.0, jitter=True),
    Queue.NLP: RetryPolicy(3, 2.0, 2.0, jitter=True),
    Queue.EMBEDDING: RetryPolicy(2, 5.0, 2.0, jitter=False),
    Queue.ANALYSIS: RetryPolicy(2, 1.0, 1.0, jitter=False),
    Queue.MAINTENANCE: RetryPolicy(1, 60.0, 1.0, jitter=False),
}


# Task name prefix -> queue. Prefixes match the job types in
# services/workers/README.md.
TASK_ROUTES: dict[str, Queue] = {
    "acquire.": Queue.ACQUISITION,
    "normalize.": Queue.ACQUISITION,
    "nlp.extract": Queue.NLP,
    "nlp.classify": Queue.NLP,
    "nlp.embed": Queue.EMBEDDING,
    "nlp.cluster": Queue.EMBEDDING,
    "score.": Queue.ANALYSIS,
    "market.": Queue.ANALYSIS,
    "competition.": Queue.ANALYSIS,
    "execution.": Queue.ANALYSIS,
    "maintenance.": Queue.MAINTENANCE,
    "infra.": Queue.MAINTENANCE,
}


# Every task payload carries these. `workspace_id` is required because a worker
# must never resolve a workspace itself -- a worker that could look up "the
# current workspace" could look up the wrong one (ADR-005).
REQUIRED_HEADERS: tuple[str, ...] = (
    "workspace_id",
    "research_session_id",
    "correlation_id",
)


def route_task(task_name: str) -> Queue:
    """Resolve a task name to its queue.

    Longest prefix wins, so `nlp.embed` reaches the embedding queue rather than
    being swallowed by a shorter `nlp.` rule.
    """
    matches = [
        (prefix, queue) for prefix, queue in TASK_ROUTES.items() if task_name.startswith(prefix)
    ]
    if not matches:
        raise KeyError(
            f"no queue route for task {task_name!r}. Add a prefix to TASK_ROUTES; "
            "an unrouted task would silently land on the default queue."
        )
    matches.sort(key=lambda item: len(item[0]), reverse=True)
    return matches[0][1]


def retry_policy_for(task_name: str) -> RetryPolicy:
    return RETRY_POLICIES[route_task(task_name)]


def celery_task_routes() -> dict[str, dict[str, str]]:
    """The `task_routes` mapping Celery expects, derived from TASK_ROUTES."""
    return {f"{prefix}*": {"queue": queue.value} for prefix, queue in TASK_ROUTES.items()}
