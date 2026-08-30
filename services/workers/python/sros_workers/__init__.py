"""Celery infrastructure for Startup Research OS.

INFRASTRUCTURE, plus the thin task surfaces of the two stages that exist. No
job BODY lives here: `acquisition_tasks` and `normalization_tasks` each merge
the correlation headers, refuse a payload with no tenant, and call a function
in the context that owns the work. Everything decidable is decided there, so
it can be tested without a broker -- a job whose logic sits inside a task
decorator is a job that only a running worker can exercise.

  queues.py             queue topology, routing, retry policy (no Celery import)
  context.py            correlation headers and idempotency keys (no Celery import)
  celery_app.py         the application factory                (imports Celery lazily)
  acquisition_tasks.py  acquire.collect.world_bank             (Mission 1.5)
  normalization_tasks.py normalize.raw_records                 (Mission 1.6)

Keeping the first two Celery-free is what lets the routing and retry rules be
tested without a broker.
"""

from .context import MissingContextError, TaskContext, idempotency_key
from .queues import (
    QUEUES,
    REQUIRED_HEADERS,
    RETRY_POLICIES,
    TASK_ROUTES,
    Queue,
    RetryPolicy,
    retry_policy_for,
    route_task,
)

__all__ = [
    "Queue",
    "QUEUES",
    "RetryPolicy",
    "RETRY_POLICIES",
    "TASK_ROUTES",
    "REQUIRED_HEADERS",
    "route_task",
    "retry_policy_for",
    "TaskContext",
    "MissingContextError",
    "idempotency_key",
]
