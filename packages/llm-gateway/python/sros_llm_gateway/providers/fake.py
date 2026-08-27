"""Test doubles.

These exist so the gateway's routing, budget, retry and validation paths can be
exercised without a network, an API key or a bill. They are not a provider
implementation and must never be registered outside tests and local development.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..gateway import ProviderResult
from ..types import LlmRequest, LlmTier


@dataclass
class EchoProvider:
    """Returns deterministic output. Records what it was asked."""

    name: str = "fake-echo"
    supported: tuple[LlmTier, ...] = tuple(LlmTier)
    cost_units: float = 1.0
    structured: dict[str, object] | None = None
    calls: list[tuple[str, str]] = field(default_factory=list)

    def supports(self, tier: LlmTier) -> bool:
        return tier in self.supported

    def complete(self, request: LlmRequest, model: str) -> ProviderResult:
        self.calls.append((request.task, model))
        return ProviderResult(
            content=f"echo:{request.task}",
            structured=self.structured,
            input_tokens=10,
            output_tokens=5,
            cost_units=self.cost_units,
        )


@dataclass
class FailingProvider:
    """Fails a configurable number of times, then succeeds."""

    name: str = "fake-failing"
    failures_before_success: int = 1
    attempts: int = field(default=0, init=False)

    def supports(self, tier: LlmTier) -> bool:
        return True

    def complete(self, request: LlmRequest, model: str) -> ProviderResult:
        self.attempts += 1
        if self.attempts <= self.failures_before_success:
            raise TimeoutError("simulated provider timeout")
        return ProviderResult(content="recovered", cost_units=1.0)
