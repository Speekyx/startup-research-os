"""Typed identifiers.

Python has no branded types, so identity safety is enforced by distinct classes
plus format validation at construction. A `WorkspaceId` accepted where an
`OpportunityId` was meant is a bug the type checker should catch, and in a
multi-tenant system that mix-up has a data-leak shape (ADR-005).
"""

from __future__ import annotations

import re
import uuid
from typing import ClassVar

from .errors import ContractError

_SLUG = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")

__all__ = [
    "UserId",
    "WorkspaceId",
    "ResearchProjectId",
    "ResearchSessionId",
    "OpportunityId",
    "EvidenceId",
    "SignalId",
    "SourceId",
]


class _UuidId(str):
    """A UUID-formatted identifier. Immutable, comparable, str-compatible.

    The class attribute is `id_format`, not `format`: `str.format` already
    exists, and shadowing a builtin method on a str subclass breaks every
    caller that formats one.
    """

    id_format: ClassVar[str] = "uuid"

    def __new__(cls, value: object) -> _UuidId:
        if isinstance(value, uuid.UUID):
            value = str(value)
        if not isinstance(value, str):
            raise ContractError(cls.__name__, f"expected a string, got {type(value).__name__}")
        try:
            canonical = str(uuid.UUID(value))
        except (ValueError, AttributeError, TypeError):
            raise ContractError(cls.__name__, f"not a valid UUID: {value!r}") from None
        return super().__new__(cls, canonical)

    @classmethod
    def generate(cls) -> _UuidId:
        return cls(str(uuid.uuid4()))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self)!r})"


class _SlugId(str):
    """A stable lowercase slug identifier."""

    id_format: ClassVar[str] = "slug"

    def __new__(cls, value: object) -> _SlugId:
        if not isinstance(value, str):
            raise ContractError(cls.__name__, f"expected a string, got {type(value).__name__}")
        if not _SLUG.match(value):
            raise ContractError(
                cls.__name__,
                f"must be a lowercase stable slug matching {_SLUG.pattern}, got {value!r}",
            )
        return super().__new__(cls, value)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self)!r})"


class UserId(_UuidId):
    """A principal. Not a tenant."""


class WorkspaceId(_UuidId):
    """The tenant boundary. Required on every tenant-scoped contract (ADR-005)."""


class ResearchProjectId(_UuidId):
    """Persistent workspace-scoped research objective (Ontology V2 §11.2)."""


class ResearchSessionId(_UuidId):
    """The only persisted execution entity (Ontology V2 §11.4).

    Replaces the retired `run_id`. There is no `ResearchRun`.
    """


class OpportunityId(_UuidId):
    """A domain hypothesis. Not owned by the session that found it (V2 §12)."""


class EvidenceId(_UuidId):
    """An evidence record with mandatory provenance."""


class SignalId(_UuidId):
    """An extracted demand signal."""


class SourceId(_SlugId):
    """A registered external source. Global, not tenant-scoped.

    Registry contents are D-07 and remain open.
    """
