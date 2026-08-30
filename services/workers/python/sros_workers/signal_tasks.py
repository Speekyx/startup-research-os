"""The signal derivation task: NormalizedRecords to persisted Signals.

Mission 1.11.1 §43. The Celery surface only. Every decision lives in
`sros_nlp.job`, which runs without a broker -- a job whose logic is inside a task
decorator can only be tested by starting a worker, and a test that needs a
worker is a test that gets skipped.

**`signal.` routes to the ACQUISITION queue**, exactly as `normalize.` does and
for the same reason: bounded, CPU-cheap arithmetic over records the deployment
already holds. The `nlp` queue is configured for LLM-backed, budget-consuming
work, and routing deterministic subtraction there would let it compete for slots
that were sized for something else.

**No embedding is scheduled** (§43, §49). This task derives signals and stops.

Three properties, all inherited rather than re-implemented here:

**No default context.** `TaskContext.from_headers` refuses a payload that cannot
say which workspace it belongs to (ADR-005).

**Delivery is at-least-once and this does not pretend otherwise** (ADR-004). A
redelivery re-reads the same records, produces byte-identical signals and finds
every derivation identity already stored, so it writes no signal. It DOES write
a second derivation run row, because a run is an execution and two executions
happened.

**The batch is bounded inside the job, every time.** The payload may ask for a
smaller batch and cannot ask for a larger one.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .context import TaskContext, idempotency_key

__all__ = [
    "DERIVE_SIGNALS",
    "register_signal_tasks",
    "signal_payload",
]

# `signal.` routes to the acquisition queue: prefetch 1, concurrency 4.
DERIVE_SIGNALS = "signal.derive"


def signal_payload(headers: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Merge the correlation headers into the job payload, refusing if incomplete.

    The headers are the authority for tenancy. A payload that also carried a
    `workspace_id` would give two answers to one question, so the header wins
    and the merge happens in one place.
    """
    context = TaskContext.from_headers(headers)
    return {**payload, **context.to_headers()}


def register_signal_tasks(
    app: Any,
    runner: Callable[..., Any] | None = None,
    connection_factory: Callable[[str], Any] | None = None,
) -> None:
    """Attach the signal derivation task to a Celery app.

    Registration is explicit, like the acquisition and normalization tasks: a
    process that should not derive signals simply does not call this.
    """

    @app.task(name=DERIVE_SIGNALS, bind=True)  # type: ignore[untyped-decorator]
    def derive_signals(
        self: Any, headers: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any]:
        merged = signal_payload(headers, payload)
        context = TaskContext.from_headers(headers)

        if connection_factory is None:
            # Fail closed rather than reaching for a default connection. A task
            # that could invent its own database handle could invent the wrong
            # one, and this is the process boundary where that matters most.
            raise RuntimeError(
                "no connection factory was registered for signal tasks; an extractor "
                "must not construct its own database access"
            )

        # Imported ONLY when no runner was injected, for the reason
        # `normalization_tasks` records: `runner or <import>` resolves the
        # import first, so an injected runner avoided the call while still
        # requiring the package -- and services/nlp/python is deliberately
        # absent from the zero-dependency test path (ADR-009).
        execute = runner
        if execute is None:
            from sros_nlp.job import run_signal_derivation_job

            execute = run_signal_derivation_job

        result = execute(merged, connection_factory)
        return {
            **result.to_json(),
            "task_id": self.request.id if self.request else None,
            "task_idempotency_key": idempotency_key(DERIVE_SIGNALS, context, payload),
        }
