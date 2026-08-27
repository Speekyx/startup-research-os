"""PostgreSQL connection pooling and transactions.

psycopg 3 directly, no ORM. See ADR-011.

**Transaction semantics.** `transaction()` yields a connection inside an
explicit transaction: it commits on clean exit and rolls back on any exception.
Nothing here uses autocommit, because a record and its provenance must be
written together — a row observable without its provenance, even transiently,
violates `evidence-confidence-framework-v1.md` §10.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

__all__ = ["Database", "DatabaseUnavailableError"]


class DatabaseUnavailableError(RuntimeError):
    """The database cannot be reached. Surfaced by /ready, never swallowed."""


class Database:
    """A thin wrapper over a psycopg connection pool.

    Deliberately thin: it owns connection lifecycle and transactions, and
    nothing else. Query construction belongs in the repositories, where it stays
    visible — an accidental cross-tenant join is a security issue, and a query
    builder makes query shape harder to review.
    """

    def __init__(self, dsn: str, min_size: int = 1, max_size: int = 10) -> None:
        from psycopg_pool import ConnectionPool

        self._dsn = dsn
        self._pool = ConnectionPool(
            dsn,
            min_size=min_size,
            max_size=max_size,
            open=False,
            # Fail fast rather than queue forever behind a dead database.
            timeout=5.0,
        )

    def open(self) -> None:
        self._pool.open(wait=True, timeout=10.0)

    def close(self) -> None:
        self._pool.close()

    @contextmanager
    def connection(self) -> Iterator[Any]:
        """A pooled connection in autocommit-off mode, committed by psycopg."""
        with self._pool.connection() as conn:
            yield conn

    @contextmanager
    def transaction(self) -> Iterator[Any]:
        """An explicit transaction: commit on success, rollback on exception."""
        with self._pool.connection() as conn, conn.transaction():
            yield conn

    def ping(self) -> bool:
        """Cheap liveness probe used by /ready.

        Returns False rather than raising: readiness reports dependency state,
        it does not crash on a dependency being down.
        """
        try:
            with self._pool.connection(timeout=3.0) as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False
