"""ResearchSession lifecycle. The orchestrator owns transition policy.

Ontology V2 §15 defines the states. This module defines who may move between
them, and it is the **only** place that decision is made (Mission 0.4 §9).

Before this, `sros_gateway.db.repositories` held the transition table. That put
a policy decision inside a persistence layer, which meant any second caller
would either re-derive the rules or mutate `status` directly. The repository now
imports `ALLOWED_TRANSITIONS` from here; the table did not change, only its
owner.

**No state is invented, and none may be.** In particular there is no
`BUDGET_EXHAUSTED`: a session that spends its budget reaches `COMPLETED` with a
reduced Research Completeness and recorded gaps (Ontology V2 §15, ADR-006).
Partial coverage is a *result*, not a failure mode. The database CHECK
constraint and the contract enum both refuse the invented value, and a test
asserts it.
"""

from __future__ import annotations

from sros_contracts import ResearchSessionStatus

__all__ = [
    "ALLOWED_TRANSITIONS",
    "TERMINAL_STATUSES",
    "CANCELLABLE_STATUSES",
    "InvalidTransitionError",
    "can_transition",
    "require_transition",
    "is_terminal",
    "next_statuses",
    "cancellation_target",
]


class InvalidTransitionError(ValueError):
    """A ResearchSession status transition that Ontology V2 §15 does not allow."""


# Ontology V2 §15, verbatim. The happy path is linear; CANCELLED and FAILED are
# reachable from every non-terminal state because a session can be stopped or
# can break at any stage.
ALLOWED_TRANSITIONS: dict[ResearchSessionStatus, frozenset[ResearchSessionStatus]] = {
    ResearchSessionStatus.PENDING: frozenset(
        {
            ResearchSessionStatus.PLANNING,
            ResearchSessionStatus.CANCELLED,
            ResearchSessionStatus.FAILED,
        }
    ),
    ResearchSessionStatus.PLANNING: frozenset(
        {
            ResearchSessionStatus.COLLECTING,
            ResearchSessionStatus.CANCELLED,
            ResearchSessionStatus.FAILED,
        }
    ),
    ResearchSessionStatus.COLLECTING: frozenset(
        {
            ResearchSessionStatus.ANALYZING,
            ResearchSessionStatus.CANCELLED,
            ResearchSessionStatus.FAILED,
        }
    ),
    ResearchSessionStatus.ANALYZING: frozenset(
        {
            ResearchSessionStatus.SCORING,
            ResearchSessionStatus.CANCELLED,
            ResearchSessionStatus.FAILED,
        }
    ),
    # SCORING may reach COMPLETED even with partial coverage: budget exhaustion
    # is COMPLETED with reduced Research Completeness, never FAILED
    # (Ontology V2 §15, ADR-006).
    ResearchSessionStatus.SCORING: frozenset(
        {
            ResearchSessionStatus.COMPLETED,
            ResearchSessionStatus.CANCELLED,
            ResearchSessionStatus.FAILED,
        }
    ),
    # Terminal. A terminal state that could be left would make "completed"
    # unfalsifiable: any conclusion drawn from it could be revised afterwards
    # with nothing recording that it had been reached.
    ResearchSessionStatus.COMPLETED: frozenset(),
    ResearchSessionStatus.FAILED: frozenset(),
    ResearchSessionStatus.CANCELLED: frozenset(),
}

TERMINAL_STATUSES: frozenset[ResearchSessionStatus] = frozenset(
    status for status, targets in ALLOWED_TRANSITIONS.items() if not targets
)

CANCELLABLE_STATUSES: frozenset[ResearchSessionStatus] = frozenset(
    status
    for status, targets in ALLOWED_TRANSITIONS.items()
    if ResearchSessionStatus.CANCELLED in targets
)


def can_transition(current: ResearchSessionStatus, target: ResearchSessionStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def require_transition(current: ResearchSessionStatus, target: ResearchSessionStatus) -> None:
    """Raise unless the transition is authorized.

    The message names what *is* allowed, because the caller is usually a piece
    of code that believed it knew the lifecycle.
    """
    if not can_transition(current, target):
        allowed = sorted(s.value for s in ALLOWED_TRANSITIONS[current])
        raise InvalidTransitionError(
            f"{current.value} -> {target.value} is not a permitted transition. "
            f"Allowed from {current.value}: {allowed or 'none (terminal)'}"
        )


def is_terminal(status: ResearchSessionStatus) -> bool:
    return status in TERMINAL_STATUSES


def next_statuses(current: ResearchSessionStatus) -> frozenset[ResearchSessionStatus]:
    return ALLOWED_TRANSITIONS[current]


def cancellation_target(current: ResearchSessionStatus) -> ResearchSessionStatus | None:
    """The status a cancellation request should move a session to, or None.

    Returns None for a session that is already terminal. Cancelling a finished
    session is not an error the caller has to handle — it is a no-op, and
    modelling it as an exception would push every caller into a try/except
    around a race it cannot win.
    """
    if is_terminal(current):
        return None
    return ResearchSessionStatus.CANCELLED
