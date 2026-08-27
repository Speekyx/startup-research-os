"""Celery infrastructure for Startup Research OS.

INFRASTRUCTURE ONLY. No business job body lives here, and none may be added
until the context that owns the work is implemented.

  queues.py     queue topology, routing, retry policy   (no Celery import)
  context.py    correlation headers and idempotency keys (no Celery import)
  celery_app.py the application factory                  (imports Celery lazily)

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
