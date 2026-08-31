"""Fixtures for the signal derivation suite.

Shaped after `services/acquisition/python/tests/conftest.py`, deliberately: the
two suites face the same problem -- persistence assertions count rows, and
counting rows in a workspace somebody else's real data lives in is a test that
passes or fails depending on what was collected that week.

**Every destructive fixture goes through `disposable()`.** The seeded
development workspaces hold the eight real records this mission derives from,
and a fixture that could create or destroy one could destroy those.
"""

from __future__ import annotations

import contextlib
import os
import pathlib
import sys
from collections.abc import Iterator

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "infrastructure"))
from testing.workspace_guard import disposable  # noqa: E402

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros"
)


def _postgres_available() -> bool:
    try:
        import psycopg
    except ImportError:
        return False
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
    except Exception:
        return False
    return True


needs_postgres = pytest.mark.skipif(
    not _postgres_available(),
    reason="PostgreSQL is not reachable; the derivation integration tests need one",
)

# The seeded development workspace, which holds the eight REAL normalized
# records. Read only -- never created, never destroyed, never written into.
WORKSPACE_A = "00000000-0000-4000-8000-000000000001"

# This suite's own disposable workspaces. S for its own writes, T so a
# cross-tenant assertion has a second workspace to be isolated from: proving
# that A cannot read B needs a B, and nothing about that requires B to be one
# somebody's real data lives in.
WORKSPACE_S = "00000000-0000-4000-8000-00000000000f"
WORKSPACE_T = "00000000-0000-4000-8000-000000000010"


def _make_workspace(workspace_id: str, slug: str) -> None:
    import psycopg

    disposable(workspace_id, what="_make_workspace")
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "INSERT INTO core.workspaces (id, name, slug) VALUES (%s,%s,%s) "
            "ON CONFLICT (id) DO NOTHING",
            (workspace_id, f"test {slug}", slug),
        )
        connection.commit()


def _drop_workspace(workspace_id: str) -> None:
    """Remove a workspace this suite created, and everything it wrote.

    Order matters: `signal_inputs` references `normalized_records` with
    ON DELETE RESTRICT, so the lineage goes before the records it cites --
    which is the constraint doing exactly what it was added for.
    """
    import psycopg

    disposable(workspace_id, what="_drop_workspace")
    with psycopg.connect(DATABASE_URL) as connection:
        for statement in (
            # Mission 1.13.1's tables come first: `claim_interpretation_inputs`
            # references BOTH nlp.signals and research.claims, and evidence
            # references a claim and a signal. Deleting a signal before them
            # would hit the composite foreign keys that exist to stop exactly
            # that -- the FK closure, read before deleting rather than after
            # (`testing-strategy.md` §16).
            "DELETE FROM research.claim_interpretation_inputs WHERE workspace_id = %s",
            "DELETE FROM research.claim_interpretation_runs WHERE workspace_id = %s",
            "DELETE FROM scoring.evidence WHERE workspace_id = %s",
            "DELETE FROM research.claim_revisions WHERE workspace_id = %s",
            "DELETE FROM research.claims WHERE workspace_id = %s",
            "DELETE FROM nlp.signal_inputs WHERE workspace_id = %s",
            "DELETE FROM nlp.signal_derivation_runs WHERE workspace_id = %s",
            "DELETE FROM nlp.signals WHERE workspace_id = %s",
            "DELETE FROM acquisition.normalized_records WHERE workspace_id = %s",
            "DELETE FROM acquisition.raw_records WHERE workspace_id = %s",
            "DELETE FROM research.research_sessions WHERE workspace_id = %s",
            "DELETE FROM research.research_projects WHERE workspace_id = %s",
            "DELETE FROM core.workspaces WHERE id = %s",
        ):
            connection.execute(statement, (workspace_id,))
        connection.commit()


# A session inside the probe workspace. The signal and run tables carry
# COMPOSITE foreign keys to `research_sessions`, so a made-up session id is
# refused -- which is the constraint working, and the reason this fixture exists
# rather than a random uuid in a payload.
PROBE_PROJECT = "00000000-0000-4000-8000-000000000011"
PROBE_SESSION = "00000000-0000-4000-8000-000000000012"


def _make_session(
    workspace_id: str,
    project_id: str = PROBE_PROJECT,
    session_id: str = PROBE_SESSION,
) -> None:
    import json

    import psycopg

    disposable(workspace_id, what="_make_session")
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "INSERT INTO research.research_projects (id, workspace_id, name) "
            "VALUES (%s,%s,'signal derivation probe') ON CONFLICT (id) DO NOTHING",
            (project_id, workspace_id),
        )
        connection.execute(
            """INSERT INTO research.research_sessions (
                   id, workspace_id, project_id, research_context,
                   research_context_hash, research_context_schema_version,
                   contract_version, ontology_version)
               VALUES (%s,%s,%s,%s,'probe','1.0.0','1.7.0','2')
               ON CONFLICT (id) DO NOTHING""",
            (session_id, workspace_id, project_id, json.dumps({})),
        )
        connection.commit()


@pytest.fixture
def probe_workspace() -> Iterator[str]:
    _make_workspace(disposable(WORKSPACE_S, what="probe_workspace"), "signal-probe")
    _make_session(WORKSPACE_S)
    yield WORKSPACE_S
    _drop_workspace(WORKSPACE_S)


OTHER_PROJECT = "00000000-0000-4000-8000-000000000013"
OTHER_SESSION = "00000000-0000-4000-8000-000000000014"


@pytest.fixture
def other_workspace() -> Iterator[str]:
    _make_workspace(disposable(WORKSPACE_T, what="other_workspace"), "signal-other")
    _make_session(WORKSPACE_T, OTHER_PROJECT, OTHER_SESSION)
    yield WORKSPACE_T
    _drop_workspace(WORKSPACE_T)


def _factory(commit: bool):
    role = os.environ.get("APP_DB_ROLE", "sros_app")
    connections: list[object] = []

    @contextlib.contextmanager
    def make(workspace_id: str):
        import psycopg

        connection = psycopg.connect(DATABASE_URL)
        connections.append(connection)
        try:
            with connection.transaction(force_rollback=not commit):
                # BOTH isolation layers. `SET LOCAL ROLE` so the row-level
                # policies apply at all -- the migration role BYPASSES them --
                # and the transaction-local workspace so they resolve to this
                # tenant. A factory that set only the second would report an
                # isolation guarantee it never exercised.
                connection.execute(f"SET LOCAL ROLE {role}")
                connection.execute(
                    "SELECT set_config('app.workspace_id', %s, true)", (workspace_id,)
                )
                yield connection
        finally:
            connection.close()

    return make, connections


@pytest.fixture
def tenant_conn():
    """A tenant connection factory that ROLLS BACK. Right for a persistence
    assertion, wrong for an idempotency one."""
    make, connections = _factory(commit=False)
    yield make
    for connection in connections:
        with contextlib.suppress(Exception):
            connection.close()


@pytest.fixture
def committing_tenant_conn(probe_workspace: str):
    """A tenant connection factory that COMMITS, cleaned up with the workspace.

    "The second delivery finds the work already done" cannot be observed if the
    first delivery was undone.
    """
    make, connections = _factory(commit=True)
    yield make
    for connection in connections:
        with contextlib.suppress(Exception):
            connection.close()


@pytest.fixture
def privileged_conn():
    """A connection that BYPASSES row-level security.

    For arranging fixtures and for reading back what a tenant transaction wrote.
    Never for asserting isolation: a check made through this connection would
    prove nothing about the policies.
    """
    import psycopg

    connection = psycopg.connect(DATABASE_URL)
    try:
        yield connection
    finally:
        connection.close()
