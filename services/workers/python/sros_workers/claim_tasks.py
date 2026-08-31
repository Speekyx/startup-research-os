"""The claim interpretation task: Signals to persisted OBSERVED Claims.

Mission 1.13.1 §45. The Celery surface only. Every decision lives in
`sros_nlp.claim_job`, which runs without a broker -- a job whose logic is inside
a task decorator can only be tested by starting a worker, and a test that needs
a worker is a test that gets skipped.

**`claim.` routes to the ACQUISITION queue**, exactly as `signal.` and
`normalize.` do and for the same reason: bounded, CPU-cheap work over rows the
deployment already holds. Rendering a format string is not what the `nlp` queue
was sized for, and routing it there would let it compete for slots reserved for
LLM-backed work. **No parallel AI worker subsystem was created** (§45).

**No LLM, no embedding, no scoring is scheduled** (§39, §40, §43). This task
interprets Signals into OBSERVED claims and stops.

Three properties, all inherited rather than re-implemented here:

**No default context.** `TaskContext.from_headers` refuses a payload that cannot
say which workspace it belongs to (ADR-005), and the context is rebuilt at
execution rather than serialised into the message -- nothing trusted travels
through the broker.

**Delivery is at-least-once and this does not pretend otherwise** (ADR-004). A
redelivery re-reads the same Signals, renders byte-identical statements and
finds every proposition already stored, so it writes no claim, no revision and
no evidence. It DOES write a second interpretation run row, because a run is an
execution and two executions happened.

**The batch is bounded inside the job, every time.** The payload may ask for a
smaller batch and cannot ask for a larger one.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .context import TaskContext, idempotency_key

__all__ = [
    "INTERPRET_CLAIMS",
    "claim_payload",
    "register_claim_tasks",
]

# `claim.` routes to the acquisition queue: prefetch 1, concurrency 4.
INTERPRET_CLAIMS = "claim.interpret"


def claim_payload(headers: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Merge the correlation headers into the job payload, refusing if incomplete.

    The headers are the authority for tenancy. A payload that also carried a
    `workspace_id` would give two answers to one question, so the header wins
    and the merge happens in one place.
    """
    context = TaskContext.from_headers(headers)
    return {**payload, **context.to_headers()}


def register_claim_tasks(
    app: Any,
    runner: Callable[..., Any] | None = None,
    connection_factory: Callable[[str], Any] | None = None,
) -> None:
    """Attach the claim interpretation task to a Celery app.

    Registration is explicit, like every task before it: a process that should
    not interpret claims simply does not call this.
    """

    @app.task(name=INTERPRET_CLAIMS, bind=True)  # type: ignore[untyped-decorator]
    def interpret_claims(
        self: Any, headers: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any]:
        merged = claim_payload(headers, payload)
        context = TaskContext.from_headers(headers)

        if connection_factory is None:
            # Fail closed rather than reaching for a default connection. A task
            # that could invent its own database handle could invent the wrong
            # one, and this is the process boundary where that matters most.
            raise RuntimeError(
                "no connection factory was registered for claim tasks; an interpreter "
                "must not construct its own database access"
            )

        # Imported ONLY when no runner was injected, for the reason
        # `signal_tasks` records: `runner or <import>` resolves the import
        # first, so an injected runner avoided the call while still requiring
        # the package -- and services/nlp/python is deliberately absent from the
        # zero-dependency test path (ADR-009).
        execute = runner
        if execute is None:
            from sros_nlp.claim_job import run_claim_interpretation_job

            execute = run_claim_interpretation_job

        result = execute(merged, connection_factory)
        return {
            **result.to_json(),
            "task_id": self.request.id if self.request else None,
            "task_idempotency_key": idempotency_key(INTERPRET_CLAIMS, context, payload),
        }
