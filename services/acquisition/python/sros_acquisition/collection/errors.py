"""The acquisition error taxonomy.

Mission 1.5 §32 and §33. Two jobs, and they are separable on purpose.

**Normalising.** A collector fails in a third party's vocabulary — an httpx
timeout, a JSON decode error, a 429. The orchestrator must branch on a *meaning*,
because an upstream library reorganising its exception hierarchy must not change
how this system retries. So every failure becomes one of ten codes, and each
code carries whether it is worth retrying: that is the decision that costs money
when it is wrong, and it belongs next to the code rather than in whoever catches
it.

**Sanitising.** §33: no secret, no environment variable, no raw stack trace and
no unnecessary response body may reach a job result or an API. The rule here is
narrow and mechanical — a failure carries a message this codebase wrote, never
`str(exc)` from a library, and never a response body. The correlation id and the
safe diagnostic fields survive, because an operator still has to be able to find
the request.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sros_contracts import AcquisitionErrorCode
from sros_contracts.errors import ContractError

__all__ = [
    "RETRYABLE_CODES",
    "AcquisitionFailure",
    "AcquisitionFailedError",
    "code_for_status",
    "is_retryable",
]

# Whether a code is worth trying again. Held here rather than at each call site,
# because the expensive mistakes are asymmetric: retrying a deterministic 4xx is
# how a rate limit becomes a ban, and NOT retrying a timeout throws away a job
# that would have succeeded.
RETRYABLE_CODES: frozenset[AcquisitionErrorCode] = frozenset(
    {
        AcquisitionErrorCode.NETWORK_TIMEOUT,
        AcquisitionErrorCode.RATE_LIMITED,
        AcquisitionErrorCode.TEMPORARY_UPSTREAM,
        AcquisitionErrorCode.PERSISTENCE_FAILURE,
    }
)


def is_retryable(code: AcquisitionErrorCode) -> bool:
    return code in RETRYABLE_CODES


def code_for_status(status: int) -> tuple[AcquisitionErrorCode, str] | None:
    """Map an HTTP status to a normalised code and a message we wrote.

    `None` for a success. Extracted in Mission 1.9.3 because a second collector
    needed exactly this mapping and two copies of a retry classification is how
    one of them quietly starts retrying a 404.

    **The body never enters the detail** (§33). A status number is a safe
    diagnostic; a response body is a third party's text, which may contain
    anything.
    """
    if 200 <= status < 300:
        return None
    if status == 429:
        return AcquisitionErrorCode.RATE_LIMITED, "the source signalled too many requests"
    if status >= 500:
        return (
            AcquisitionErrorCode.TEMPORARY_UPSTREAM,
            "the source reported a server-side failure",
        )
    return (
        AcquisitionErrorCode.UPSTREAM_CLIENT_ERROR,
        "the source rejected the request deterministically",
    )


@dataclass(frozen=True)
class AcquisitionFailure:
    """Why an acquisition attempt produced no records, safely.

    `detail` is written by this codebase. A library's exception text is not
    copied into it: a driver has no obligation to keep secrets out of its own
    messages, and a connection string with a password in it has reached a log
    that way in more than one project.

    `context` is for safe diagnostics only — a status code, a page number, a
    resource id. Never a response body, never a header, never an environment
    value.
    """

    code: AcquisitionErrorCode
    detail: str
    source_id: str
    correlation_id: str | None = None
    resource_id: str | None = None
    context: dict[str, object] = field(default_factory=dict)

    @property
    def retryable(self) -> bool:
        return is_retryable(self.code)

    def to_json(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "detail": self.detail,
            "source_id": self.source_id,
            "correlation_id": self.correlation_id,
            "resource_id": self.resource_id,
            "retryable": self.retryable,
            "context": dict(self.context),
        }

    def __str__(self) -> str:
        return f"{self.code.value}: {self.detail}"


class AcquisitionFailedError(ContractError):
    """Raised where a caller expects an exception rather than a result.

    The failure travels on the exception so a `except AcquisitionFailedError as
    exc: exc.failure.code` reads the normalised code rather than re-deriving it
    from a message.
    """

    def __init__(self, failure: AcquisitionFailure) -> None:
        self.failure = failure
        super().__init__(f"acquisition.{failure.source_id}", str(failure))
