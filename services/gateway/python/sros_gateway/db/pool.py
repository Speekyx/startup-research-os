"""PostgreSQL connection pooling, transactions and tenant context.

psycopg 3 directly, no ORM. See ADR-011 and ADR-012.

**Transaction semantics.** `transaction()` yields a connection inside an
explicit transaction: it commits on clean exit and rolls back on any exception.
Nothing here uses autocommit, because a record and its provenance must be
written together — a row observable without its provenance, even transiently,
violates `evidence-confidence-framework-v1.md` §10.

**Tenant semantics (added in Mission 0.4).** `tenant_transaction(workspace_id)`
additionally establishes the row-level-security context for the transaction:

    SET LOCAL ROLE <app role>            -- a role RLS can constrain
    set_config('app.workspace_id', …, true)  -- transaction-local tenant id

Both are **transaction-local**, which is the property that makes this safe with
a connection pool. A session-level `SET` would survive the connection's return
to the pool, and the next borrower would inherit the previous tenant's context —
a cross-tenant read with no bug in any query. `SET LOCAL` is discarded at commit
or rollback, so a pooled connection cannot carry a tenant across users.

The role matters for a reason worth stating plainly: PostgreSQL RLS is bypassed
by a superuser, and by the table owner unless the table also has
`FORCE ROW LEVEL SECURITY`. The local stack connects as the database superuser.
Without `SET LOCAL ROLE`, enabling policies would produce isolation tests that
pass while proving nothing.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

__all__ = [
    "Database",
    "DatabaseUnavailableError",
    "TenantScopeError",
    "DEFAULT_APP_ROLE",
    "WORKSPACE_GUC",
]

DEFAULT_APP_ROLE = "sros_app"
WORKSPACE_GUC = "app.workspace_id"

# A role name is an SQL identifier and cannot be a bound parameter. It comes
# from configuration rather than from a request, and it is still validated:
# configuration reaches production too, and `sql.Identifier` quoting protects
# the statement but not the intent.
_ROLE_NAME = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


class DatabaseUnavailableError(RuntimeError):
    """The database cannot be reached. Surfaced by /ready, never swallowed."""


class TenantScopeError(ValueError):
    """A tenant-scoped connection was requested without a usable workspace.

    A ValueError rather than a RuntimeError: what is wrong is the workspace
    value, and a caller validating input at a boundary should be able to catch
    it alongside every other malformed argument.
    """


class Database:
    """A thin wrapper over a psycopg connection pool.

    Deliberately thin: it owns connection lifecycle, transactions and tenant
    context, and nothing else. Query construction belongs in the repositories,
    where it stays visible — an accidental cross-tenant join is a security
    issue, and a query builder makes query shape harder to review.
    """

    def __init__(
        self,
        dsn: str,
        min_size: int = 1,
        max_size: int = 10,
        app_role: str | None = DEFAULT_APP_ROLE,
    ) -> None:
        from psycopg_pool import ConnectionPool

        if app_role is not None and not _ROLE_NAME.match(app_role):
            raise ValueError(
                f"invalid application role name {app_role!r}: expected a lowercase "
                "SQL identifier (ADR-012)"
            )

        self._dsn = dsn
        self._app_role = app_role or None
        self._pool = ConnectionPool(
            dsn,
            min_size=min_size,
            max_size=max_size,
            open=False,
            # Fail fast rather than queue forever behind a dead database.
            timeout=5.0,
        )

    @property
    def app_role(self) -> str | None:
        """The role assumed per transaction, or None when RLS is not enforced.

        `None` exists for one legitimate case: a database that predates
        migration 0003 and therefore has no `sros_app` role. It is not a way to
        opt out of RLS in a deployed environment.
        """
        return self._app_role

    def open(self) -> None:
        self._pool.open(wait=True, timeout=10.0)

    def close(self) -> None:
        self._pool.close()

    # -- role and tenant context -------------------------------------------

    def _assume_app_role(self, conn: Any) -> None:
        """Drop to the RLS-constrained role for the rest of the transaction.

        A side effect worth naming: `sros_app` holds DML privileges only, so a
        runtime connection cannot issue DDL. ADR-011 says migrations and runtime
        access are strictly separate; after this, the database enforces it
        rather than the code merely intending it.
        """
        if self._app_role is None:
            return
        from psycopg import sql

        conn.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(self._app_role)))

    @staticmethod
    def _set_workspace(conn: Any, workspace_id: uuid.UUID) -> None:
        """Bind the tenant context to THIS transaction.

        `set_config(..., is_local => true)` rather than `SET LOCAL …` because
        the value is a bound parameter here, and a tenant id interpolated into
        a statement is the one place this system must never take a shortcut.
        """
        conn.execute(
            "SELECT set_config(%s, %s, true)",
            (WORKSPACE_GUC, str(workspace_id)),
        )

    # -- connections --------------------------------------------------------

    @contextmanager
    def connection(self) -> Iterator[Any]:
        """A non-tenant connection: global reference data only.

        The application role is still assumed, so every tenant-scoped table is
        invisible through this connection. That is deliberate — the default
        state of a connection is "no tenant", and reaching tenant data requires
        asking for it explicitly.
        """
        with self._pool.connection() as conn, conn.transaction():
            self._assume_app_role(conn)
            yield conn

    @contextmanager
    def transaction(self) -> Iterator[Any]:
        """An explicit non-tenant transaction: commit on success, rollback on error."""
        with self._pool.connection() as conn, conn.transaction():
            self._assume_app_role(conn)
            yield conn

    @contextmanager
    def tenant_transaction(self, workspace_id: uuid.UUID | str) -> Iterator[Any]:
        """A transaction scoped to one workspace, at the database level.

        Reads use this too. A read needs a transaction here because the tenant
        context is transaction-local by design, and that is the correct trade:
        the alternative is a context that outlives the work it was set for.
        """
        resolved = _coerce_workspace(workspace_id)
        with self._pool.connection() as conn, conn.transaction():
            self._assume_app_role(conn)
            self._set_workspace(conn, resolved)
            yield conn

    @contextmanager
    def privileged_transaction(self) -> Iterator[Any]:
        """A transaction WITHOUT the application role. Not for request paths.

        It exists for the two jobs that legitimately need to see across
        workspaces or to touch schema-adjacent state: test fixtures asserting
        that RLS is what is doing the filtering, and administrative tooling.

        Named awkwardly on purpose. If this appears in a request path, that is
        the bug.
        """
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

    def rls_active(self) -> bool:
        """Whether the tenant policies are actually in force.

        Reported by /ready rather than assumed. RLS that was designed for and
        never enabled is the state Mission 0.3 ended in, and the only way to
        tell the difference from outside is to ask the database.
        """
        try:
            with self._pool.connection(timeout=3.0) as conn:
                row = conn.execute(
                    """SELECT count(*) FROM pg_policy p
                       JOIN pg_class c ON c.oid = p.polrelid
                       JOIN pg_namespace n ON n.oid = c.relnamespace
                       WHERE n.nspname IN ('research','acquisition','nlp','scoring')"""
                ).fetchone()
            return bool(row and row[0] > 0)
        except Exception:
            return False


def _coerce_workspace(workspace_id: uuid.UUID | str) -> uuid.UUID:
    """Fail closed before a statement is ever issued.

    A malformed workspace would produce a NULL tenant context and therefore an
    empty result set, which is safe but silent. Raising here turns a silent
    empty read into a stated error.
    """
    if workspace_id is None or workspace_id == "":
        raise TenantScopeError(
            "a tenant-scoped transaction requires an explicit workspace_id; "
            "there is no default (ADR-005)"
        )
    if isinstance(workspace_id, uuid.UUID):
        return workspace_id
    try:
        return uuid.UUID(str(workspace_id))
    except (ValueError, AttributeError, TypeError) as exc:
        raise TenantScopeError(f"workspace_id is not a UUID: {workspace_id!r}") from exc
