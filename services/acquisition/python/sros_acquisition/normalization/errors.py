"""The normalization error taxonomy.

Mission 1.6 §28. Two vocabularies, kept apart because they answer different
questions and collapsing them would lose both answers:

    NormalizationErrorCode        why NO record was produced
    NormalizationQualityReason    why a record that EXISTS is degraded

A raw record whose collector version is unsupported produces nothing, and the
orchestrator has to know that. A raw record whose value the source never
published produces a perfectly good record that simply carries no measurement,
and a downstream stage has to know *that*. Reporting the second as an error
would make an ordinary sparse series look like a broken pipeline; reporting the
first as a quality reason would hide a refusal inside a row nobody reads.

**Sanitising, as at the acquisition layer.** A failure carries a message this
codebase wrote. Never `str(exc)` from a library, never a payload, never a stack
trace. The correlation id and the raw record id survive, because an operator
still has to be able to find the record that failed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sros_contracts import NormalizationErrorCode
from sros_contracts.errors import ContractError

__all__ = [
    "RETRYABLE_NORMALIZATION_CODES",
    "NormalizationFailure",
    "NormalizationFailedError",
    "is_retryable",
]

# Only one code is worth trying again, and the asymmetry is the point: every
# other failure here is deterministic. The same raw record, the same normalizer
# and the same configuration produce the same refusal, so a retry spends a
# worker slot to reach the identical conclusion. Storage is the one thing that
# can fail transiently while the input stays valid.
RETRYABLE_NORMALIZATION_CODES: frozenset[NormalizationErrorCode] = frozenset(
    {NormalizationErrorCode.PERSISTENCE_FAILURE}
)


def is_retryable(code: NormalizationErrorCode) -> bool:
    return code in RETRYABLE_NORMALIZATION_CODES


@dataclass(frozen=True)
class NormalizationFailure:
    """Why one raw record produced no normalized record, safely.

    `context` is for safe diagnostics only -- an observation key, a collector
    version, a record kind. Never a payload, never a provenance blob, never a
    library's own exception text.
    """

    code: NormalizationErrorCode
    detail: str
    source_id: str
    raw_record_id: str | None = None
    correlation_id: str | None = None
    context: dict[str, object] = field(default_factory=dict)

    @property
    def retryable(self) -> bool:
        return is_retryable(self.code)

    def to_json(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "detail": self.detail,
            "source_id": self.source_id,
            "raw_record_id": self.raw_record_id,
            "correlation_id": self.correlation_id,
            "retryable": self.retryable,
            "context": dict(self.context),
        }

    def __str__(self) -> str:
        return f"{self.code.value}: {self.detail}"


class NormalizationFailedError(ContractError):
    """Raised where a caller expects an exception rather than a result.

    The failure travels on the exception, so `except NormalizationFailedError as
    exc: exc.failure.code` reads the normalised code instead of re-deriving it
    from a message.
    """

    def __init__(self, failure: NormalizationFailure) -> None:
        self.failure = failure
        super().__init__(f"normalization.{failure.source_id}", str(failure))
