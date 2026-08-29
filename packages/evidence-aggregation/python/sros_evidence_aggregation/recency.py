"""Freshness.

Mission 1.1 §18–§19. Two rules carry this module.

**Recency is a property of the claim, not the source.** The same platform can
carry a pricing figure that is stale in a month and a workflow observation that
is still true in three years. A decay rate attached to a platform would be
wrong for one of them, and there is no way to tell which.

**No universal half-life is invented.** `evidence-confidence-framework-v1.md` §5
says decay "should depend on the domain" and gives no numbers, which is audit
finding A-03. Choosing 30 days here would resolve A-03 by fiat: the number would
become load-bearing, nothing would record that it was guessed, and it would be
unfalsifiable afterwards.

So a temporally sensitive claim with no authorised half-life does not decay
slowly, and does not decay at all. It produces `MISSING_TEMPORAL_PARAMETER` and
the evidence becomes non-scorable. Failing closed is the only honest option: any
number chosen here would silently propagate into every downstream score.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sros_contracts import ClaimTemporality

from .errors import InvalidFactorError

__all__ = [
    "MISSING_TEMPORAL_PARAMETER",
    "MISSING_OBSERVATION_TIME",
    "half_life_decay",
    "freshness",
]

# Reported rather than raised. The caller usually cannot fix it in the moment,
# and the useful behaviour is a result that says which parameter was absent.
MISSING_TEMPORAL_PARAMETER = "MISSING_TEMPORAL_PARAMETER"
MISSING_OBSERVATION_TIME = "MISSING_OBSERVATION_TIME"


def half_life_decay(age_days: float, half_life_days: float) -> float:
    """`2 ** (-age / H)`.

        age = 0    -> 1.0
        age = H    -> 0.5
        age = 2H   -> 0.25

    Half-life rather than linear decay because linear decay reaches exactly zero
    at a boundary somebody has to choose, and a two-year-old observation is
    weaker than a two-week-old one rather than worthless.

    Negative ages are clamped to 0. An observation timestamped slightly ahead of
    the aggregation clock is ordinary clock skew, not evidence from the future,
    and it must never produce a freshness above 1.
    """
    if not (half_life_days > 0) or half_life_days != half_life_days:
        raise InvalidFactorError(
            f"half-life must be a positive number of days, got {half_life_days!r}"
        )
    if age_days != age_days:
        raise InvalidFactorError("age must be a number")
    if age_days <= 0.0:
        return 1.0
    # 2 ** -x underflows gracefully to 0.0 for very old observations, which is
    # the right limit: nothing here needs a floor.
    return float(2.0 ** (-age_days / half_life_days))


def freshness(
    temporality: ClaimTemporality,
    observed_at: datetime | None,
    now: datetime,
    half_life_days: float | None,
) -> tuple[float | None, str | None]:
    """Return `(freshness, missing_reason)`. Exactly one of the two is set.

    Evergreen claims return 1.0 without needing a timestamp at all. That is not
    a default standing in for a missing value — an evergreen claim genuinely has
    no decay, and demanding a timestamp for one would make the absence of an
    irrelevant field block a perfectly scorable record.

    A fact that stopped being true is not modelled as decay. It is a new
    contradicting observation, and it enters through `contradiction_strength`
    where it is visible, rather than by quietly eroding a support figure.
    """
    if temporality is ClaimTemporality.EVERGREEN:
        return 1.0, None

    if half_life_days is None:
        return None, MISSING_TEMPORAL_PARAMETER
    if observed_at is None:
        return None, MISSING_OBSERVATION_TIME

    if observed_at.tzinfo is None or now.tzinfo is None:
        raise InvalidFactorError(
            "observation and aggregation times must be timezone-aware; a naive "
            "timestamp is a retention and correctness bug, not a formatting detail"
        )

    age: timedelta = now - observed_at
    return half_life_decay(age.total_seconds() / 86400.0, half_life_days), None
