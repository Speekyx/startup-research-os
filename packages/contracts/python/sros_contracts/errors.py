"""Contract validation errors.

One error type, carrying the field path and the reason. A contract violation is
a bug at a boundary, not a user error, so the message is written for whoever has
to fix it.
"""

from __future__ import annotations


class ContractError(ValueError):
    """Raised when a value violates a domain contract."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")
