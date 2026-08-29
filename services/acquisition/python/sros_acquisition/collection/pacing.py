"""Our own request pacing. Not a claim about anybody's rate limit.

Mission 1.5 §13, and the distinction it insists on:

    provider-documented rate limit   UNKNOWN for World Bank, and it stays UNKNOWN
    our operational pacing           a local safety measure we chose

Mission 1.3 read the World Bank documentation and found no stated limit. Mission
1.4 therefore reports `rate_limit.known == False` on the authorization context,
and §29 of that brief forbids inventing a number a collector would then trust.

Nothing here changes that. A `RequestPacer` is a self-imposed floor on the
interval between requests, chosen conservatively because we do not know what the
source tolerates — which is a different statement from "the source permits N per
second", and the two must never be written down as if they were the same. The
absence of a documented limit is a reason to be *more* careful, not less.

Deliberately simple: a monotonic clock and a sleep. No token bucket, no shared
state, no Redis. A distributed limiter is a real thing to want once several
workers collect from one source concurrently, and building it now would be
building it against a load nobody has measured.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

__all__ = ["PacingPolicy", "RequestPacer"]


@dataclass(frozen=True)
class PacingPolicy:
    """How gently we choose to behave towards a source.

    `basis` is mandatory and is not decoration. A number with no recorded reason
    reads, six months later, as something the source told us — which is exactly
    the confusion §13 exists to prevent.
    """

    min_interval_seconds: float
    max_requests_per_job: int
    basis: str

    def __post_init__(self) -> None:
        if self.min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must not be negative")
        if self.max_requests_per_job < 1:
            raise ValueError("max_requests_per_job must be at least 1")
        if not self.basis.strip():
            raise ValueError(
                "a pacing policy must record why its numbers were chosen, or it will be "
                "read as a limit the source published"
            )


# The World Bank documentation states no rate limit. This is ours, and it is
# deliberately slow: one request every 250ms and at most 50 in a single job.
# Nothing about it is derived from anything the World Bank said.
WORLD_BANK_PACING = PacingPolicy(
    min_interval_seconds=0.25,
    max_requests_per_job=50,
    basis=(
        "Chosen locally. The World Bank documents no rate limit, and Mission 1.3 "
        "recorded that absence as UNKNOWN rather than as permission. A source that "
        "has not said what it tolerates is a reason to go slower, so this paces at "
        "four requests per second and caps a single job at 50 requests."
    ),
)


@dataclass
class RequestPacer:
    """Enforces a minimum interval between requests, and a per-job ceiling.

    The clock is injectable so tests assert the pacing without spending the
    wall-clock time it describes — a test that really slept would be slow enough
    that someone would eventually delete it.
    """

    policy: PacingPolicy
    monotonic: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    _last_request_at: float | None = field(default=None, init=False, repr=False)
    _requests_made: int = field(default=0, init=False)

    @property
    def requests_made(self) -> int:
        return self._requests_made

    @property
    def exhausted(self) -> bool:
        return self._requests_made >= self.policy.max_requests_per_job

    def acquire(self) -> float:
        """Wait if the last request was too recent. Returns the wait taken.

        Raises when the per-job ceiling is reached: a job that has made fifty
        requests and still wants more is a job whose bounds were wrong, and
        continuing quietly is how a malformed query collects indefinitely (§16).
        """
        if self.exhausted:
            raise RuntimeError(
                f"the per-job request ceiling of {self.policy.max_requests_per_job} is "
                "reached. This is our own bound, not the source's"
            )
        waited = 0.0
        now = self.monotonic()
        if self._last_request_at is not None:
            elapsed = now - self._last_request_at
            remaining = self.policy.min_interval_seconds - elapsed
            if remaining > 0:
                self.sleep(remaining)
                waited = remaining
                now = self.monotonic()
        self._last_request_at = now
        self._requests_made += 1
        return waited
