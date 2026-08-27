"""Task correlation context and idempotency keys.

Two infrastructure concerns that every future business job depends on, kept
here so they are decided once rather than per job.

ADR-004 (at-least-once delivery), ADR-005 (tenant propagation).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .queues import REQUIRED_HEADERS

__all__ = ["TaskContext", "idempotency_key", "MissingContextError"]


class MissingContextError(ValueError):
    """Raised when a task payload lacks a required correlation header.

    Failing closed is the point: a task that cannot say which workspace it
    belongs to must not run, in any environment (ADR-005).
    """


@dataclass(frozen=True)
class TaskContext:
    """Correlation carried by every task payload.

    `research_session_id` is the canonical name. Accepted ADRs written before
    Ontology V2 call this field `run_id`; they are append-only, so the mapping
    lives in Ontology V2 §11.5 rather than being retrofitted into them.
    """

    workspace_id: str
    research_session_id: str
    correlation_id: str

    @classmethod
    def from_headers(cls, headers: object) -> TaskContext:
        if not isinstance(headers, dict):
            raise MissingContextError("task headers must be a mapping")
        missing = [name for name in REQUIRED_HEADERS if not headers.get(name)]
        if missing:
            raise MissingContextError(
                f"task payload is missing required headers: {missing}. "
                "A worker never resolves the workspace itself, and never falls "
                "back to a default (ADR-005)."
            )
        return cls(
            workspace_id=str(headers["workspace_id"]),
            research_session_id=str(headers["research_session_id"]),
            correlation_id=str(headers["correlation_id"]),
        )

    def to_headers(self) -> dict[str, str]:
        return {
            "workspace_id": self.workspace_id,
            "research_session_id": self.research_session_id,
            "correlation_id": self.correlation_id,
        }

    def log_fields(self) -> dict[str, str]:
        return self.to_headers()


def idempotency_key(task_name: str, context: TaskContext, payload: object) -> str:
    """A deterministic key for a unit of work.

    Celery over Redis gives **at-least-once** delivery. Exactly-once is not
    available, so every job must make duplicate execution harmless. The key is
    the first half of that: it goes into a unique constraint so the database
    absorbs the duplicate.

    An "already processed?" read-then-write without a unique constraint is not
    idempotency -- it is a race with a longer window.
    """
    material = json.dumps(
        {
            "task": task_name,
            "workspace_id": context.workspace_id,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
