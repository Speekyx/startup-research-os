"""The first real business task: World Bank acquisition.

Mission 1.5 §29. This is the Celery surface only. Every decision lives in
`sros_acquisition.collection.job`, which runs without a broker — a job whose
logic is inside a task decorator can only be tested by starting a worker, and a
test that needs a worker is a test that gets skipped.

Three properties, all of them inherited rather than re-implemented here:

**No default context.** `TaskContext.from_headers` refuses a payload that cannot
say which workspace it belongs to. A worker never resolves that itself and never
falls back (ADR-005).

**Delivery is at-least-once and this does not pretend otherwise** (ADR-004).
A redelivery re-collects, finds every observation unchanged and moves a
timestamp instead of writing a row. That is idempotent persistence, not
exactly-once delivery, and the difference matters when someone later reasons
about what a duplicate costs.

**The governance gate runs inside the job, every time.** The payload carries no
authorization: a serialized permission outlives the state it came from, and a
source suspended between planning and execution would still be collected.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .context import TaskContext, idempotency_key

__all__ = ["WORLD_BANK_COLLECT", "register_acquisition_tasks", "world_bank_payload"]

# `acquire.` routes to the acquisition queue: prefetch 1, concurrency 4, so a
# slow collector cannot reserve work its siblings could be doing.
WORLD_BANK_COLLECT = "acquire.collect.world_bank"


def world_bank_payload(headers: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Merge the correlation headers into the job payload, refusing if incomplete.

    The headers are the authority for tenancy. A payload that also carried a
    `workspace_id` would give two answers to one question, so the header wins
    and the merge happens in one place.
    """
    context = TaskContext.from_headers(headers)
    return {**payload, **context.to_headers()}


def register_acquisition_tasks(
    app: Any,
    runner: Callable[..., Any] | None = None,
    connection_factory: Callable[[str], Any] | None = None,
) -> None:
    """Attach the acquisition tasks to a Celery app.

    `runner` and `connection_factory` are injected so a deployment supplies its
    own pool and a test supplies a rolled-back connection. Registration is
    explicit, like the probe tasks: a process that should not collect simply
    does not call this.
    """

    @app.task(name=WORLD_BANK_COLLECT, bind=True)  # type: ignore[untyped-decorator]
    def collect_world_bank(
        self: Any, headers: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any]:
        merged = world_bank_payload(headers, payload)
        context = TaskContext.from_headers(headers)

        if connection_factory is None:
            # Fail closed rather than reaching for a default connection. A task
            # that could invent its own database handle could invent the wrong
            # one, and this is the process boundary where that matters most.
            raise RuntimeError(
                "no connection factory was registered for acquisition tasks; a collector "
                "must not construct its own database access"
            )

        from sros_acquisition.collection.job import run_world_bank_job

        execute = runner or run_world_bank_job
        result = execute(merged, connection_factory)
        return {
            **result.to_json(),
            "task_id": self.request.id if self.request else None,
            "task_idempotency_key": idempotency_key(WORLD_BANK_COLLECT, context, payload),
        }
