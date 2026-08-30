"""The normalization task: RawRecord to canonical observation.

Mission 1.6 §32. The Celery surface only. Every decision lives in
`sros_acquisition.normalization.job`, which runs without a broker -- a job whose
logic is inside a task decorator can only be tested by starting a worker, and a
test that needs a worker is a test that gets skipped.

**No second scheduler** (§32). `normalize.` already routes to the acquisition
queue through `TASK_ROUTES`, and it stays there: normalization is bounded,
CPU-cheap work over records the deployment already holds, and giving it a queue
of its own would split a pool for no measured reason. If it ever competes with
collection for slots, that is a routing change with evidence behind it.

Three properties, all inherited rather than re-implemented here:

**No default context.** `TaskContext.from_headers` refuses a payload that cannot
say which workspace it belongs to. A worker never resolves that itself and never
falls back (ADR-005).

**Delivery is at-least-once and this does not pretend otherwise** (ADR-004). A
redelivery re-reads the same raw records, produces byte-identical canonical
content, finds every identity already stored and writes nothing. That is
idempotent persistence, not exactly-once delivery, and the difference matters
when someone later reasons about what a duplicate costs.

**The batch is bounded inside the job, every time.** The payload may ask for a
smaller batch and cannot ask for a larger one: an unbounded normalization batch
is exactly what §34 forbids, and a ceiling a caller could raise is not a ceiling.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .context import TaskContext, idempotency_key

__all__ = [
    "NORMALIZE_RAW_RECORDS",
    "normalization_payload",
    "register_normalization_tasks",
]

# `normalize.` routes to the acquisition queue: prefetch 1, concurrency 4.
NORMALIZE_RAW_RECORDS = "normalize.raw_records"


def normalization_payload(headers: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Merge the correlation headers into the job payload, refusing if incomplete.

    The headers are the authority for tenancy. A payload that also carried a
    `workspace_id` would give two answers to one question, so the header wins
    and the merge happens in one place.
    """
    context = TaskContext.from_headers(headers)
    return {**payload, **context.to_headers()}


def register_normalization_tasks(
    app: Any,
    runner: Callable[..., Any] | None = None,
    connection_factory: Callable[[str], Any] | None = None,
) -> None:
    """Attach the normalization tasks to a Celery app.

    `runner` and `connection_factory` are injected so a deployment supplies its
    own pool and a test supplies a rolled-back connection. Registration is
    explicit, like the acquisition tasks: a process that should not normalize
    simply does not call this.
    """

    @app.task(name=NORMALIZE_RAW_RECORDS, bind=True)  # type: ignore[untyped-decorator]
    def normalize_raw_records(
        self: Any, headers: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any]:
        merged = normalization_payload(headers, payload)
        context = TaskContext.from_headers(headers)

        if connection_factory is None:
            # Fail closed rather than reaching for a default connection. A task
            # that could invent its own database handle could invent the wrong
            # one, and this is the process boundary where that matters most.
            raise RuntimeError(
                "no connection factory was registered for normalization tasks; a "
                "normalizer must not construct its own database access"
            )

        from sros_acquisition.normalization.job import run_normalization_job

        execute = runner or run_normalization_job
        result = execute(merged, connection_factory)
        return {
            **result.to_json(),
            "task_id": self.request.id if self.request else None,
            "task_idempotency_key": idempotency_key(NORMALIZE_RAW_RECORDS, context, payload),
        }
