"""Integration test fixtures.

These tests require the local stack (`infrastructure/compose`). They skip
cleanly when it is not running, so a contributor without Docker still gets a
green unit run and an explicit note about what was not covered — rather than a
red suite that teaches them to ignore failures.

**Two workspaces are always present.** A tenancy system tested with one tenant
is not meaningfully tested: every isolation assertion here needs a second
workspace to have something to be isolated *from*.

**A and B are SEEDED, and a suite that writes into them leaves its rows behind.**
`probe_workspaces` exists for the suites that write: a throwaway pair, created
and dropped per test. See its docstring for why counting rows in a seeded
workspace is a measurement of the environment rather than of the code.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest

# A and B are seeded by `0001_dev_workspace` and shared with every other suite.
# Read from them freely; write into them only when the rows are rolled back.
WORKSPACE_A = uuid.UUID("00000000-0000-4000-8000-000000000001")
WORKSPACE_B = uuid.UUID("00000000-0000-4000-8000-000000000003")

# P and Q belong to `probe_workspaces`: created per test, dropped per test, and
# never seeded. 0004 is the acquisition suite's probe workspace -- distinct ids
# per suite, so no suite can be looking at another one's leftovers.
WORKSPACE_P = uuid.UUID("00000000-0000-4000-8000-000000000005")
WORKSPACE_Q = uuid.UUID("00000000-0000-4000-8000-000000000006")

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:55379/0")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:55333")


def _postgres_available() -> bool:
    try:
        import psycopg

        with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def _redis_available() -> bool:
    try:
        import redis

        return bool(redis.Redis.from_url(REDIS_URL, socket_connect_timeout=3).ping())
    except Exception:
        return False


def _qdrant_available() -> bool:
    try:
        import urllib.request

        # Fixed local http URL from configuration, not user input.
        with urllib.request.urlopen(f"{QDRANT_URL}/healthz", timeout=3) as resp:  # noqa: S310
            return resp.status == 200
    except Exception:
        return False


needs_postgres = pytest.mark.skipif(
    not _postgres_available(), reason="PostgreSQL not reachable; start infrastructure/compose"
)
needs_redis = pytest.mark.skipif(
    not _redis_available(), reason="Redis not reachable; start infrastructure/compose"
)
needs_qdrant = pytest.mark.skipif(
    not _qdrant_available(), reason="Qdrant not reachable; start infrastructure/compose"
)


@pytest.fixture(scope="session")
def database() -> Iterator[object]:
    from sros_gateway.db.pool import Database

    db = Database(DATABASE_URL, min_size=1, max_size=4)
    db.open()
    yield db
    db.close()


@pytest.fixture(scope="session", autouse=True)
def registry_loaded() -> None:
    """Apply the source catalog before the registry-backed tests read it.

    The source-registry API and the orchestrator's acquisition gate both read
    `registry.*`, so the suite must not depend on someone having run
    `sros-source load` first. That dependency is invisible while it holds -- a
    developer's database usually carries the catalog from an earlier run -- and
    it fails only in a clean environment, which is CI and every new machine.

    Idempotent by construction (uuid5 row ids), and it grants nothing:
    `load_catalog_into` writes `collector_enabled = FALSE` unconditionally, so a
    fixture can never be the thing that makes a source collectable.
    """
    if not _postgres_available():
        return
    import pathlib

    import psycopg
    from sros_acquisition.registry import load_catalog
    from sros_acquisition.registry.repositories import load_catalog_into

    repo_root = pathlib.Path(__file__).resolve().parents[4]
    catalog = load_catalog(repo_root / "docs/data/source-catalog-v1.json")
    with psycopg.connect(DATABASE_URL) as connection:
        load_catalog_into(connection, catalog)
        connection.commit()


@pytest.fixture(scope="session")
def redis_client() -> Iterator[object]:
    import redis

    client = redis.Redis.from_url(REDIS_URL)
    yield client
    client.close()


@pytest.fixture(scope="session")
def qdrant() -> Iterator[object]:
    from qdrant_client import QdrantClient

    client = QdrantClient(url=QDRANT_URL, timeout=10)
    yield client
    client.close()


@pytest.fixture
def api_client() -> Iterator[object]:
    """A FastAPI TestClient with the real stack behind it."""
    from fastapi.testclient import TestClient
    from sros_gateway.app import create_app
    from sros_gateway.config import Settings

    settings = Settings(
        database_url=DATABASE_URL,
        redis_url=REDIS_URL,
        qdrant_url=QDRANT_URL,
        environment="development",
        dev_workspace_id=None,  # tests pass the workspace explicitly, always
    )
    with TestClient(create_app(settings)) as client:
        yield client


def header(workspace: uuid.UUID) -> dict[str, str]:
    return {"x-workspace-id": str(workspace)}


@pytest.fixture
def probe_workspaces() -> Iterator[tuple[uuid.UUID, uuid.UUID]]:
    """A throwaway pair of workspaces, created for one test and dropped after it.

    Mission 1.5 established this for the acquisition suite and Mission 1.6 found
    the cost of not having it here: a normalization test asserted
    `count(*) == 0` on `research.claims` and failed on 39 rows the claim suite
    had committed into the seeded development workspace across earlier runs.
    Counting rows in a workspace that also holds seeded and collected data
    measures the environment, not the behaviour under test -- and the assertion
    that catches the leak is the one that gets rewritten, because the leak looks
    like the assertion's fault.

    Both workspaces are removed in teardown, which is only safe because this
    fixture CREATED them. The seeded workspaces are never dropped: an earlier
    version of the acquisition fixture deleted WORKSPACE_B and broke this suite
    on a foreign key, and a fixture that removes what it did not create is a
    fixture that decides what other suites can test.

    Two, not one, because this suite's isolation assertions need a second
    workspace to be isolated *from* -- the same reason the seeded pair exists.

    Dropped before it is created, as well as after. Teardown is in a `finally`
    and so survives a failing test, but it does not survive the run being
    killed -- and the workspaces left behind by an interrupted run would be
    silently reused by the next one, which is the defect this fixture exists to
    remove, merely made rarer.
    """
    _drop_workspaces()
    _make_workspaces()
    try:
        yield WORKSPACE_P, WORKSPACE_Q
    finally:
        _drop_workspaces()


def _make_workspaces() -> None:
    import psycopg

    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(
            "INSERT INTO core.workspaces (id, name, slug) VALUES (%s,%s,%s), (%s,%s,%s) "
            "ON CONFLICT (id) DO NOTHING",
            (
                WORKSPACE_P,
                "gateway probe",
                "gateway-probe",
                WORKSPACE_Q,
                "gateway probe (isolation)",
                "gateway-probe-other",
            ),
        )
        connection.commit()


def _drop_workspaces() -> None:
    """Only ever called for the workspaces this fixture created."""
    import psycopg

    assert {WORKSPACE_P, WORKSPACE_Q}.isdisjoint({WORKSPACE_A, WORKSPACE_B}), (
        "seeded workspaces must not be dropped"
    )
    with psycopg.connect(DATABASE_URL) as connection:
        # `scoring.evidence` is deleted by name, before the cascade runs.
        # Its `independence_group_id` foreign key is ON DELETE RESTRICT, so a
        # dependent evidence record can refuse the deletion of the group it
        # belongs to. Both tables cascade from `core.workspaces`, and which of
        # the two cascades first is a property of PostgreSQL's trigger order
        # rather than anything this schema states -- so the teardown does not
        # depend on it.
        connection.execute(
            "DELETE FROM scoring.evidence WHERE workspace_id = ANY(%s)",
            ([WORKSPACE_P, WORKSPACE_Q],),
        )
        # Everything else goes with the workspace: every tenant table declares
        # `workspace_id ... REFERENCES core.workspaces (id) ON DELETE CASCADE`,
        # so claims, revisions, observations, independence groups, opportunities,
        # sessions and projects are all removed by these two rows.
        connection.execute(
            "DELETE FROM core.workspaces WHERE id = ANY(%s)", ([WORKSPACE_P, WORKSPACE_Q],)
        )
        connection.commit()
