"""Cost model for a bounded DEVELOPMENT pilot run (Mission 1.85.7). Arithmetic only, no network.

Three different numbers, never confused:

- PLANNING ESTIMATE: what a one-pass run is expected to cost. An estimate, never a bound.
- CONSERVATIVE BOUND and RETRY WORST CASE: defensible upper estimates from the measured request bytes,
  the documented tool-use system prompt, an allowance for the undocumented strict-mode prompt, and the
  maximum output the runner permits. Still estimates, because no local tokenizer is published.
- PER-CALL DOCUMENTED MAXIMUM: the cost of one call at the full documented context window and the output
  bound. This is the only per-call figure resting on documented limits, so it is what the runner uses to
  decide, BEFORE every call, whether that call could cross the accepted ceiling. It is a guard for the next
  call, not a multiplier over the run.

Prices come from a provider verification artifact. Unknown prices make every figure unavailable: no
default price exists here.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

__all__ = [
    "COST_MODEL_ID",
    "PLANNING_OUTPUT_TOKENS_PER_CALL",
    "PLANNING_TOKENS_PER_BODY_BYTE",
    "STRICT_PROMPT_ALLOWANCE_TOKENS",
    "CeilingRefusalError",
    "CostLedger",
    "CostModel",
    "Prices",
    "RunCost",
    "call_cost",
    "conservative_input_tokens",
    "proposed_hard_ceiling",
]

COST_MODEL_ID = "semantic-extraction-pilot-cost-model@1.0.0"
MILLION = Decimal(1_000_000)
# The injected strict-mode prompt is documented to exist and to cost tokens; its size is not documented.
# A policy allowance, stated as such.
STRICT_PROMPT_ALLOWANCE_TOKENS = 2000
# Planning only. Two real strict forced-tool requests to claude-sonnet-5 in this repository reported
# 12493 and 13435 input tokens for ~31.3k and ~34.3k request characters (Missions 1.84.22 and 1.84.24),
# about 0.40 tokens per character with every provider-side prompt included.
PLANNING_TOKENS_PER_BODY_BYTE = Decimal("0.40")
# Planning only: two findings at the contract's maximal quote and subject lengths, with framing.
PLANNING_OUTPUT_TOKENS_PER_CALL = 1000


@dataclass(frozen=True)
class Prices:
    input_usd_per_mtok: Decimal
    output_usd_per_mtok: Decimal
    multiplier: Decimal

    def __post_init__(self) -> None:
        for value in (self.input_usd_per_mtok, self.output_usd_per_mtok, self.multiplier):
            if not isinstance(value, Decimal) or value <= 0:
                raise ValueError(
                    "prices must be positive Decimals; an unknown price has no default"
                )


def call_cost(prices: Prices, input_tokens: int, output_tokens: int) -> Decimal:
    return (
        (
            (Decimal(input_tokens) * prices.input_usd_per_mtok)
            + (Decimal(output_tokens) * prices.output_usd_per_mtok)
        )
        / MILLION
        * prices.multiplier
    )


def conservative_input_tokens(
    request_body_utf8_bytes: int, tool_use_system_prompt_tokens: int
) -> int:
    """Request bytes as tokens, plus the documented tool prompt and the strict-prompt allowance."""
    return request_body_utf8_bytes + tool_use_system_prompt_tokens + STRICT_PROMPT_ALLOWANCE_TOKENS


@dataclass(frozen=True)
class RunCost:
    expected_calls: int
    max_calls_with_retry: int
    planning_estimate_usd: Decimal
    conservative_bound_usd: Decimal
    retry_worst_case_usd: Decimal
    per_call_documented_maximum_usd: Decimal
    per_record_conservative_input_tokens: dict[str, int]


@dataclass(frozen=True)
class CostModel:
    prices: Prices
    context_window_tokens: int
    max_output_tokens: int
    tool_use_system_prompt_tokens: int
    schema_retries_per_record: int

    def run(self, bodies: Iterable[tuple[str, int]]) -> RunCost:
        rows = list(bodies)
        if not rows:
            raise ValueError("a run with no approved record has no cost to bound")
        conservative = {
            rid: conservative_input_tokens(size, self.tool_use_system_prompt_tokens)
            for rid, size in rows
        }
        planning = sum(
            (
                call_cost(
                    self.prices,
                    int(
                        (Decimal(size) * PLANNING_TOKENS_PER_BODY_BYTE).to_integral_value(
                            rounding=ROUND_CEILING
                        )
                    )
                    + self.tool_use_system_prompt_tokens,
                    PLANNING_OUTPUT_TOKENS_PER_CALL,
                )
                for _, size in rows
            ),
            Decimal(0),
        )
        one_pass = sum(
            (
                call_cost(self.prices, tokens, self.max_output_tokens)
                for tokens in conservative.values()
            ),
            Decimal(0),
        )
        calls_per_record = 1 + self.schema_retries_per_record
        return RunCost(
            expected_calls=len(rows),
            max_calls_with_retry=len(rows) * calls_per_record,
            planning_estimate_usd=planning,
            conservative_bound_usd=one_pass,
            retry_worst_case_usd=one_pass * calls_per_record,
            per_call_documented_maximum_usd=call_cost(
                self.prices, self.context_window_tokens, self.max_output_tokens
            ),
            per_record_conservative_input_tokens=conservative,
        )


def proposed_hard_ceiling(run: RunCost) -> Decimal:
    """The retry worst case plus one documented-maximum call, rounded up to a whole dollar.

    The runner starts a call only while spent + one documented-maximum call stays within the ceiling, so a
    ceiling below retry worst case + one documented maximum would stop a run that stays inside its own
    conservative bound. Rounding up is headroom, never a reduction.
    """
    floor = run.retry_worst_case_usd + run.per_call_documented_maximum_usd
    return floor.to_integral_value(rounding=ROUND_CEILING)


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


class CeilingRefusalError(Exception):
    """A call, or the run, would not stay inside the accepted hard ceiling. Raised before the call."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}{': ' + detail if detail else ''}")
        self.code = code


@dataclass
class CostLedger:
    """What a run has spent, and whether the next call may start.

    A call may start only if what has been spent plus one call at the documented maximum stays within the
    accepted ceiling. A call with reported usage is charged that usage; a call without it is charged the
    documented maximum, because nothing smaller can be shown.
    """

    prices: Prices
    ceiling_usd: Decimal
    per_call_maximum_usd: Decimal
    spent_usd: Decimal = Decimal(0)
    charges: list[dict[str, str]] = field(default_factory=list)

    def preflight(self, retry_worst_case_usd: Decimal) -> None:
        if self.per_call_maximum_usd > self.ceiling_usd:
            raise CeilingRefusalError(
                "CEILING_BELOW_ONE_DOCUMENTED_MAXIMUM_CALL", money(self.per_call_maximum_usd)
            )
        if retry_worst_case_usd + self.per_call_maximum_usd > self.ceiling_usd:
            raise CeilingRefusalError(
                "CEILING_BELOW_BOUNDED_RUN_COST",
                f"retry worst case {money(retry_worst_case_usd)} + one documented maximum "
                f"{money(self.per_call_maximum_usd)} > ceiling {money(self.ceiling_usd)}",
            )

    def authorise_next_call(self) -> None:
        if self.spent_usd + self.per_call_maximum_usd > self.ceiling_usd:
            raise CeilingRefusalError(
                "COST_CEILING_WOULD_BE_CROSSED",
                f"spent {money(self.spent_usd)} + one documented maximum "
                f"{money(self.per_call_maximum_usd)} > ceiling {money(self.ceiling_usd)}",
            )

    def charge_usage(self, input_tokens: int, output_tokens: int) -> Decimal:
        amount = call_cost(self.prices, input_tokens, output_tokens)
        return self._charge(amount, "REPORTED_USAGE")

    def charge_unknown(self) -> Decimal:
        return self._charge(
            self.per_call_maximum_usd, "NO_REPORTED_USAGE_CHARGED_AT_DOCUMENTED_MAXIMUM"
        )

    def _charge(self, amount: Decimal, basis: str) -> Decimal:
        self.spent_usd += amount
        self.charges.append(
            {"basis": basis, "usd": money(amount), "spent_usd": money(self.spent_usd)}
        )
        return amount
