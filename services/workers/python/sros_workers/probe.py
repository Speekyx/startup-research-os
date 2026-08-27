"""INFRASTRUCTURE PROBE TASKS -- NOT BUSINESS JOBS.

These exist for one purpose: to prove at runtime that a real Celery worker
connects to a real Redis broker, that the declared queues exist, that routing
works, that JSON serialization survives the round trip, and that correlation
metadata (`workspace_id`, `research_session_id`, `correlation_id`) arrives
intact at the worker.

They compute nothing about the domain. They are namespaced under `infra.` so
they route to the maintenance queue and are trivially greppable.

**Removal:** delete this module and the `infra.` prefix from `TASK_ROUTES`.
Nothing else references it. It must not survive into a production image once the
first real job exists.
"""

from __future__ import annotations

from typing import Any

from .context import TaskContext, idempotency_key

__all__ = ["register_probe_tasks", "PROBE_ECHO", "PROBE_IDEMPOTENCY"]

PROBE_ECHO = "infra.probe.echo"
PROBE_IDEMPOTENCY = "infra.probe.idempotency"


def _echo_body(headers: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Return the correlation context exactly as it arrived.

    Failing closed on a missing `workspace_id` is the behavior under test: a
    worker never resolves the workspace itself (ADR-005).
    """
    context = TaskContext.from_headers(headers)
    return {
        "received": context.to_headers(),
        "payload": payload,
        "idempotency_key": idempotency_key(PROBE_ECHO, context, payload),
    }


def register_probe_tasks(app: Any) -> None:
    """Attach the probe tasks to a Celery app.

    Registration is explicit rather than automatic, so a deployment that does
    not want probes simply does not call this.
    """

    @app.task(name=PROBE_ECHO, bind=True)  # type: ignore[untyped-decorator]
    def probe_echo(self: Any, headers: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        result = _echo_body(headers, payload)
        result["queue"] = self.request.delivery_info.get("routing_key") if self.request else None
        result["task_id"] = self.request.id if self.request else None
        return result

    @app.task(name=PROBE_IDEMPOTENCY, bind=True)  # type: ignore[untyped-decorator]
    def probe_idempotency(
        self: Any, headers: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Return the idempotency key for a unit of work.

        Delivery is at-least-once (ADR-004). Running this twice with the same
        inputs returns the same key, which is what a unique constraint would
        use to absorb the duplicate. It does NOT make delivery exactly-once,
        and nothing here pretends it does.
        """
        context = TaskContext.from_headers(headers)
        return {
            "idempotency_key": idempotency_key(PROBE_IDEMPOTENCY, context, payload),
            "task_id": self.request.id if self.request else None,
        }
