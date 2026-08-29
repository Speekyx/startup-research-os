"""Fixtures for the Source Registry suite.

**No tenant fixture, and no `sros_gateway` import.** Source definitions and
their reviews are global platform metadata with no `workspace_id` and no
row-level security policy (Mission 1.0 §25), so these tests connect plainly.
A tenant fixture here would imply an isolation the registry does not have.

The database-backed tests skip when the local stack is not running, the same
way the gateway suite does: a contributor without Docker gets a green unit run
and an explicit note about what was not covered, rather than a red suite that
teaches them to ignore failures.
"""

from __future__ import annotations

import os
import pathlib
from collections.abc import Iterator

import pytest

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros"
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]


def _postgres_available() -> bool:
    try:
        import psycopg

        with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


needs_postgres = pytest.mark.skipif(
    not _postgres_available(), reason="PostgreSQL not reachable; start infrastructure/compose"
)


@pytest.fixture(scope="session")
def catalog():
    """The real catalog. Deliberately not a fixture file.

    `docs/data/source-catalog-v1.json` is the artefact under review; testing a
    hand-made copy would leave the reviewed one unchecked, which is the failure
    mode these tests exist to prevent.
    """
    from sros_acquisition.registry import load_catalog

    return load_catalog(REPO_ROOT / "docs/data/source-catalog-v1.json")


@pytest.fixture(scope="session", autouse=True)
def registry_loaded(catalog) -> None:
    """Apply the catalog AND verify its conditions before any database test reads it.

    The suite must not depend on someone having run `sros-source load` first.
    That dependency is invisible while it holds -- a developer's database
    usually has the catalog in it from an earlier run -- and it fails only in a
    clean environment, which is to say in CI and on a new machine.

    **Verification is here for exactly the same reason, and it was added after
    the CI run that proved the point.** CI executes the suites before
    `sros-source verify --apply`, so on a fresh database no condition was
    satisfied, World Bank was not eligible, and
    `registry.require_eligibility_for_collector` correctly refused to let the
    enablement fixture turn its collector on. The database was right; the suite
    was assuming state somebody else had produced.

    Both steps grant nothing on their own. `load_catalog_into` writes
    `collector_enabled = FALSE` unconditionally, and a verification only records
    what a verifier found -- with no credential configured, FRED's condition
    stays unsatisfied here exactly as it does in production.
    """
    if not _postgres_available():
        return
    import psycopg
    from sros_acquisition.compliance import load_compliance, verify_source
    from sros_acquisition.compliance.repositories import record_verifications
    from sros_acquisition.registry.repositories import load_catalog_into

    compliance = load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")
    with psycopg.connect(DATABASE_URL) as connection:
        load_catalog_into(connection, catalog)
        records = [r for source in catalog for r in verify_source(source, compliance)]
        record_verifications(connection, records)
        connection.commit()


def recorded_satisfied_keys(conn, source_id: str) -> frozenset[str]:
    """The conditions the DATABASE currently considers satisfied.

    Needed by every Python-versus-SQL comparison since Mission 1.4. Condition
    satisfaction is environment state that lives in the database, so a Python
    gate evaluated without it is not a second implementation of the same rule --
    it is the same rule with different inputs, and comparing the two would
    report a divergence that is really a missing argument.
    """
    rows = conn.execute(
        """SELECT c.condition_key
             FROM registry.source_review_conditions c
             JOIN registry.source_policy_reviews r ON r.id = c.review_id
            WHERE c.source_id = %s AND c.satisfied AND r.superseded_at IS NULL""",
        (source_id,),
    ).fetchall()
    return frozenset(row[0] for row in rows)


# A is the seeded development workspace, and since Mission 1.5 it holds REAL
# collected data. Tests therefore write into their own workspaces: P for
# persistence, B for the other side of an isolation assertion.
#
# A test that shared a workspace with real records would pass or fail depending
# on what somebody had collected that morning -- the same class of defect
# Mission 1.4 found in six tests that asserted a moment rather than a property.
WORKSPACE_A = "00000000-0000-4000-8000-000000000001"
WORKSPACE_B = "00000000-0000-4000-8000-000000000003"
WORKSPACE_P = "00000000-0000-4000-8000-000000000004"


def _make_workspace(workspace_id: str, slug: str) -> None:
    import psycopg

    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "INSERT INTO core.workspaces (id, name, slug) VALUES (%s,%s,%s) "
            "ON CONFLICT (id) DO NOTHING",
            (workspace_id, f"test {slug}", slug),
        )
        connection.commit()


def _drop_workspace(workspace_id: str) -> None:
    """Only ever called for a workspace this suite created. Seeded workspaces
    are cleaned of their rows, never removed."""
    import psycopg

    assert workspace_id == WORKSPACE_P, "seeded workspaces must not be dropped"
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "DELETE FROM acquisition.raw_records WHERE workspace_id = %s", (workspace_id,)
        )
        connection.execute("DELETE FROM core.workspaces WHERE id = %s", (workspace_id,))
        connection.commit()


@pytest.fixture
def probe_workspace() -> Iterator[str]:
    """A workspace of this test's own, removed afterwards.

    Persistence assertions count rows, and counting rows in a workspace that
    also holds real collected data measures the environment rather than the
    behaviour under test.
    """
    _make_workspace(WORKSPACE_P, "acquisition-probe")
    yield WORKSPACE_P
    _drop_workspace(WORKSPACE_P)


@pytest.fixture
def tenant_conn():
    """A factory for connections inside a tenant transaction, rolled back.

    Both isolation layers are entered, because neither replaces the other:
    `SET LOCAL ROLE` so the row-level policies apply at all, and the
    transaction-local workspace so they resolve to this tenant. A test that only
    set the workspace would run as the migration role, which BYPASSES RLS — and
    would report an isolation guarantee it never exercised.
    """
    import contextlib
    import os

    import psycopg

    role = os.environ.get("APP_DB_ROLE", "sros_app")
    connections: list[object] = []

    @contextlib.contextmanager
    def factory(workspace_id: str):
        connection = psycopg.connect(DATABASE_URL)
        connections.append(connection)
        try:
            with connection.transaction(force_rollback=True):
                connection.execute(f"SET LOCAL ROLE {role}")
                connection.execute(
                    "SELECT set_config('app.workspace_id', %s, true)", (workspace_id,)
                )
                yield connection
        finally:
            connection.close()

    yield factory
    for connection in connections:
        with contextlib.suppress(Exception):
            connection.close()


@pytest.fixture
def second_workspace() -> Iterator[str]:
    """The other side of an isolation assertion.

    Workspace B is **seeded** (`0001_dev_workspace`), so this fixture removes
    only the rows it caused and never the workspace itself. An earlier version
    deleted it in teardown and broke the gateway suite, which had every right to
    assume seeded reference data is still there -- a fixture that removes what it
    did not create is a fixture that decides what other suites can test.
    """
    yield WORKSPACE_B
    import psycopg

    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "DELETE FROM acquisition.raw_records WHERE workspace_id = %s", (WORKSPACE_B,)
        )
        connection.commit()


@pytest.fixture
def dev_session(probe_workspace: str) -> Iterator[str]:
    """A real research session in workspace A, removed afterwards.

    `raw_records.research_session_id` is a real foreign key, which the first job
    test discovered by failing on it. A random UUID is not a session, and the
    database is right to say so -- the alternative would have been a nullable
    link that quietly lost the connection between a record and the research that
    asked for it.
    """
    import json
    import uuid as _uuid

    import psycopg
    from sros_contracts import CONTRACT_VERSION, ONTOLOGY_VERSION

    project_id = _uuid.uuid4()
    session_id = _uuid.uuid4()
    context = {"market_scope": {"type": "COUNTRY", "countries": ["FR"]}}
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "INSERT INTO research.research_projects (id, workspace_id, name) VALUES (%s,%s,%s)",
            (project_id, probe_workspace, "mission-1.5 acquisition test"),
        )
        connection.execute(
            """INSERT INTO research.research_sessions
                   (id, workspace_id, project_id, research_context,
                    research_context_hash, research_context_schema_version,
                    contract_version, ontology_version)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                session_id,
                probe_workspace,
                project_id,
                json.dumps(context),
                "probe-hash",
                "1",
                CONTRACT_VERSION,
                ONTOLOGY_VERSION,
            ),
        )
        connection.commit()
    yield str(session_id)
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute("DELETE FROM research.research_projects WHERE id = %s", (project_id,))
        connection.commit()


@pytest.fixture
def enabled_world_bank() -> Iterator[str]:
    """Turn the operational switch on for one test, then turn it back off.

    Enabled through the DATABASE, which refuses it for an ineligible source via
    `registry.require_eligibility_for_collector` -- so this fixture cannot make
    a source collectable that the gate would not clear. It is reversed in
    teardown because a test that leaves a collector enabled has changed the
    deployment, and the suite that follows would be testing a different system.
    """
    import psycopg

    with psycopg.connect(DATABASE_URL) as connection:
        # RESTORE, not force-false. An earlier version of this fixture reset
        # every source to FALSE in teardown, which silently reverted an
        # operator's deliberate enablement -- a test that changes the deployment
        # and does not put it back is a test that decides what production does.
        previous = connection.execute(
            "SELECT collector_enabled FROM registry.sources WHERE id = 'world-bank'"
        ).fetchone()[0]
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = TRUE WHERE id = 'world-bank'"
        )
        connection.commit()
    yield "world-bank"
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = %s WHERE id = 'world-bank'",
            (previous,),
        )
        connection.commit()


@pytest.fixture
def disabled_world_bank() -> Iterator[str]:
    """Turn the operational switch OFF for one test, then restore it.

    The mirror of `enabled_world_bank`, and it exists for the same reason: a
    test that needs the deployment in a particular state must put it there and
    put it back, rather than depending on how somebody left it.
    """
    import psycopg

    with psycopg.connect(DATABASE_URL) as connection:
        previous = connection.execute(
            "SELECT collector_enabled FROM registry.sources WHERE id = 'world-bank'"
        ).fetchone()[0]
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = FALSE WHERE id = 'world-bank'"
        )
        connection.commit()
    yield "world-bank"
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "UPDATE registry.sources SET collector_enabled = %s WHERE id = 'world-bank'",
            (previous,),
        )
        connection.commit()


@pytest.fixture
def conn() -> Iterator[object]:
    """A plain connection, rolled back at the end of every test.

    Rollback rather than cleanup: these tests deliberately provoke constraint
    triggers, and a test that half-applied a load must leave nothing behind.
    """
    import psycopg

    connection = psycopg.connect(DATABASE_URL)
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()
