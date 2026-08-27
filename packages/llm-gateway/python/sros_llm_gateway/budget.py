"""Budget accounting.

ADR-006: the gateway is the only place money is spent, which makes it the only
place budget can be enforced honestly.

Refusal is a **successful outcome** for the research run: the session completes
with reduced Research Completeness rather than overspending. It is never a
session failure (Ontology V2 §15).

In-memory here. Durable accounting lands with the orchestrator; this is the
enforcement point and the contract it must satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import BudgetLimits

__all__ = ["BudgetLedger", "SessionSpend"]


@dataclass
class SessionSpend:
    cost_units: float = 0.0
    calls: int = 0


@dataclass
class BudgetLedger:
    limits: BudgetLimits
    _sessions: dict[str, SessionSpend] = field(default_factory=dict, init=False)
    _workspace_day: dict[str, float] = field(default_factory=dict, init=False)

    def spend_for(self, session_id: str) -> SessionSpend:
        return self._sessions.setdefault(session_id, SessionSpend())

    def can_spend(self, workspace_id: str, session_id: str) -> bool:
        spend = self.spend_for(session_id)
        if spend.cost_units >= self.limits.max_cost_units_per_session:
            return False
        if spend.calls >= self.limits.max_llm_calls_per_session:
            return False
        cap = self.limits.max_cost_units_per_workspace_day
        return not (cap is not None and self._workspace_day.get(workspace_id, 0.0) >= cap)

    def record(self, workspace_id: str, session_id: str, cost_units: float) -> None:
        spend = self.spend_for(session_id)
        spend.cost_units += cost_units
        spend.calls += 1
        self._workspace_day[workspace_id] = self._workspace_day.get(workspace_id, 0.0) + cost_units
