"""Celery application factory.

Infrastructure only. There is no business job body in this package, and there
will not be one until the contexts that own the work are implemented.

The configuration below is deliberate rather than default -- several Celery
defaults are wrong for this workload, and getting them wrong produces silent
job loss, which is the worst failure mode available here (ADR-004).

Celery is imported lazily so that `queues` and `context` stay testable without
the dependency installed.
"""

from __future__ import annotations

import os
from typing import Any

from .queues import QUEUES, celery_task_routes

__all__ = ["build_celery_config", "create_celery_app"]


def build_celery_config() -> dict[str, Any]:
    """Celery settings as a plain dict, so they can be asserted in tests."""
    broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:56379/0")
    backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:56379/1")

    return {
        "broker_url": broker,
        "result_backend": backend,
        # --- serialization -------------------------------------------------
        # JSON only. Pickle would accept arbitrary objects off a broker, which
        # is a remote-code-execution shape, and it makes payloads unreadable in
        # any tool that is not Python.
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        # --- delivery semantics --------------------------------------------
        # acks_late: a worker that dies mid-job must not have acknowledged the
        # work. Combined with at-least-once delivery this is why every job must
        # be idempotent.
        "task_acks_late": True,
        "task_reject_on_worker_lost": True,
        # Never prefetch a batch of slow jobs into one worker.
        "worker_prefetch_multiplier": 1,
        # --- routing ---------------------------------------------------------
        "task_routes": celery_task_routes(),
        "task_default_queue": "analysis",
        # NOTE: `task_queues` is deliberately NOT set here. Celery expects
        # kombu.Queue objects, and this function must stay importable without
        # Celery installed so the routing rules can be tested without a broker.
        # create_celery_app() declares the queues.
        # --- retries ---------------------------------------------------------
        # Per-task policies live in queues.RETRY_POLICIES. These are the floor.
        "task_default_retry_delay": 5,
        "task_acks_on_failure_or_timeout": False,
        # --- results ----------------------------------------------------------
        # Results expire: Redis is not canonical (ADR-008), and an unbounded
        # result set is a slow memory leak.
        "result_expires": 3600,
        # --- visibility -------------------------------------------------------
        "task_send_sent_event": True,
        "worker_send_task_events": True,
        "task_track_started": True,
        "timezone": "UTC",
        "enable_utc": True,
    }


def create_celery_app(name: str = "sros") -> Any:
    """Build the Celery app. Requires the `celery` package at runtime."""
    try:
        from celery import Celery
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise RuntimeError(
            "celery is not installed. Install the worker dependencies "
            "(services/workers/requirements.txt) or run inside the worker container."
        ) from exc

    from kombu import Queue

    app = Celery(name)
    app.conf.update(build_celery_config())
    # Declared explicitly rather than auto-created from routes, so a worker
    # started with -Q on a queue nobody declared fails loudly instead of
    # sitting idle on a queue that will never receive anything.
    app.conf.task_queues = [Queue(config.name) for config in QUEUES.values()]
    return app
