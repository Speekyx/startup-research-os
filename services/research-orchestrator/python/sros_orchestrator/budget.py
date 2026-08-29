"""Session budget accounting and the dispatch guard.

Mission 0.4 §15 and §16. ADR-006 makes the LLM Gateway the only place money is
spent; this module is the only place a research session decides whether it may
be spent.

**Three quantities, deliberately not one.**

    configured   the ceiling from the ResearchContext, fixed at session creation
    reserved     claimed before dispatch and not yet consumed
    actual       really consumed, recorded after the work returns

A single `spent` column conflates the last two, and the conflation has a
specific failure: two jobs dispatched concurrently both check the same
`actual`, both fit, and together they overshoot. Reserving before dispatch is
what makes the check hold under concurrency.

**Refusal is a successful outcome.** A session that cannot afford its next job
does not fail and does not acquire a new status. It reaches `COMPLETED` with a
reduced Research Completeness and a recorded gap (Ontology V2 §15). There is no
`BUDGET_EXHAUSTED`, here or anywhere.

**Currency is explicit.** Cost units are provider-agnostic (ADR-006) and are not
a currency. Recording which is which is what stops a later report from adding
dollars to units.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "COST_UNIT",
    "BudgetEntryKind",
    "BudgetAccount",
    "BudgetDecision",
    "BudgetGuard",
    "BudgetRefusedError",
]

# The unit of the internal cost model. Not a currency, and named so that a
# column holding it cannot be mistaken for one.
COST_UNIT = "COST_UNIT"


class BudgetEntryKind(StrEnum):
    RESERVATION = "RESERVATION"
    ACTUAL = "ACTUAL"
    RELEASE = "RELEASE"


class BudgetRefusedError(RuntimeError):
    """Raised only where a caller asked to spend and cannot proceed without it.

    Most callers should use `BudgetGuard.evaluate` and handle the refusal as
    data: turning every refusal into an exception pushes callers toward
    catching it broadly, and a broadly caught budget refusal becomes a silently
    skipped stage instead of a recorded gap.
    """


@dataclass(frozen=True)
class BudgetAccount:
    """The state of one session's budget.

    `configured_cost_units` of None means no ceiling was set. That is permitted
    and is not the same as zero: a session with no ceiling is unbounded by
    configuration and still bounded by the gateway's per-workspace limits
    (ADR-006).
    """

    research_session_id: str
    configured_cost_units: float | None
    configured_llm_calls: int | None
    reserved_cost_units: float = 0.0
    actual_cost_units: float = 0.0
    llm_calls: int = 0
    currency: str = COST_UNIT

    def __post_init__(self) -> None:
        for name in ("reserved_cost_units", "actual_cost_units"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must not be negative")
        if self.llm_calls < 0:
            raise ValueError("llm_calls must not be negative")

    @property
    def committed_cost_units(self) -> float:
        """What the session has already promised: reserved plus consumed.

        This, not `actual`, is what a new job must fit alongside.
        """
        return self.reserved_cost_units + self.actual_cost_units

    @property
    def remaining_cost_units(self) -> float | None:
        if self.configured_cost_units is None:
            return None
        return max(0.0, self.configured_cost_units - self.committed_cost_units)

    @property
    def exhausted(self) -> bool:
        remaining = self.remaining_cost_units
        if remaining is not None and remaining <= 0:
            return True
        return self.configured_llm_calls is not None and self.llm_calls >= self.configured_llm_calls


@dataclass(frozen=True)
class BudgetDecision:
    """The answer to "may this job be dispatched?", with its reasoning.

    The reason is carried rather than logged and discarded, because it becomes
    the text of a research gap: "not dispatched" with no cause is exactly the
    silent partial coverage that inflates every downstream confidence
    (`services/research-orchestrator/README.md` §Core design constraints).
    """

    allowed: bool
    reason: str
    estimated_cost_units: float
    remaining_cost_units: float | None

    def __bool__(self) -> bool:
        return self.allowed


class BudgetGuard:
    """Decides whether a job may be dispatched, before it is dispatched.

    Checked before dispatch rather than after, because after is an invoice.
    """

    def __init__(self, account: BudgetAccount) -> None:
        self._account = account

    @property
    def account(self) -> BudgetAccount:
        return self._account

    def evaluate(self, estimated_cost_units: float, *, llm_backed: bool = True) -> BudgetDecision:
        if estimated_cost_units < 0:
            raise ValueError("estimated_cost_units must not be negative")

        account = self._account
        remaining = account.remaining_cost_units

        if (
            account.configured_llm_calls is not None
            and llm_backed
            and account.llm_calls >= account.configured_llm_calls
        ):
            return BudgetDecision(
                allowed=False,
                reason=(
                    f"session call budget exhausted: {account.llm_calls} of "
                    f"{account.configured_llm_calls} LLM calls used. The session "
                    "completes with reduced Research Completeness rather than overspending."
                ),
                estimated_cost_units=estimated_cost_units,
                remaining_cost_units=remaining,
            )

        if remaining is None:
            return BudgetDecision(
                allowed=True,
                reason="no session cost ceiling configured",
                estimated_cost_units=estimated_cost_units,
                remaining_cost_units=None,
            )

        # The §16 inequality, stated exactly: estimate + committed <= configured.
        if estimated_cost_units > remaining:
            return BudgetDecision(
                allowed=False,
                reason=(
                    f"estimated {estimated_cost_units:.6g} exceeds the remaining "
                    f"{remaining:.6g} of a {account.configured_cost_units:.6g} "
                    f"{account.currency} session budget "
                    f"(committed {account.committed_cost_units:.6g}). Not dispatched. "
                    "The session completes with reduced Research Completeness "
                    "rather than overspending."
                ),
                estimated_cost_units=estimated_cost_units,
                remaining_cost_units=remaining,
            )

        return BudgetDecision(
            allowed=True,
            reason=f"fits within the remaining {remaining:.6g} {account.currency}",
            estimated_cost_units=estimated_cost_units,
            remaining_cost_units=remaining,
        )

    def require(self, estimated_cost_units: float, *, llm_backed: bool = True) -> BudgetDecision:
        decision = self.evaluate(estimated_cost_units, llm_backed=llm_backed)
        if not decision.allowed:
            raise BudgetRefusedError(decision.reason)
        return decision
