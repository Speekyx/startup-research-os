"""Integration test fixtures.

These tests require the local stack (`infrastructure/compose`). They skip
cleanly when it is not running, so a contributor without Docker still gets a
green unit run and an explicit note about what was not covered — rather than a
red suite that teaches them to ignore failures.

**Two workspaces are always present.** A tenancy system tested with one tenant
is not meaningfully tested: every isolation assertion here needs a second
workspace to have something to be isolated *from*.

**A and B are SEEDED, and a suite that writes into them leaves its rows behind.**
Every module that writes has a probe pair of its own -- `probe_workspaces` for
`test_claims.py`, `rls_workspaces` for `test_rls.py`, and so on -- created and
dropped per test. See `probe_workspaces` for why counting rows in a seeded
workspace is a measurement of the environment rather than of the code, and the
allocation table below for why the pairs are not shared.
"""

from __future__ import annotations

import contextlib
import os
import pathlib
import sys
import uuid
from collections.abc import Iterator

import pytest

# Mission 1.6.1 §17. One definition, shared with the acquisition suite rather
# than copied into each -- two copies of a safety rule drift, and the copy that
# drifts is the one nobody is looking at.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "infrastructure"))
from testing.workspace_guard import SEEDED_WORKSPACES, disposable  # noqa: E402

# A and B are seeded by `0001_dev_workspace` and shared with every other suite.
# Read from them freely; write into them only when the rows are rolled back.
WORKSPACE_A = uuid.UUID("00000000-0000-4000-8000-000000000001")
WORKSPACE_B = uuid.UUID("00000000-0000-4000-8000-000000000003")

# The probe workspaces: created per test, dropped per test, never seeded.
#
# One pair PER MODULE rather than one for the suite, so that the drop each
# fixture performs before it creates -- the step that lets an interrupted run
# self-heal -- can only ever reach rows its own tests wrote. Two overlapping
# runs are the case that makes the difference: on a shared id, one run's setup
# deletes the other run's live rows.
#
#   ...0004        the acquisition suite (services/acquisition/python/tests)
#   ...0005/0006   test_claims.py
#   ...0007/0008   test_rls.py
#   ...0009/000a   test_integration.py
#   ...000b/000c   test_orchestrator_integration.py
#   ...000d        test_security.py
WORKSPACE_P = uuid.UUID("00000000-0000-4000-8000-000000000005")
WORKSPACE_Q = uuid.UUID("00000000-0000-4000-8000-000000000006")
WORKSPACE_RLS_P = uuid.UUID("00000000-0000-4000-8000-000000000007")
WORKSPACE_RLS_Q = uuid.UUID("00000000-0000-4000-8000-000000000008")
WORKSPACE_INTEGRATION_P = uuid.UUID("00000000-0000-4000-8000-000000000009")
WORKSPACE_INTEGRATION_Q = uuid.UUID("00000000-0000-4000-8000-00000000000a")
WORKSPACE_ORCH_P = uuid.UUID("00000000-0000-4000-8000-00000000000b")
WORKSPACE_ORCH_Q = uuid.UUID("00000000-0000-4000-8000-00000000000c")
WORKSPACE_SECURITY_P = uuid.UUID("00000000-0000-4000-8000-00000000000d")

# Named, rather than written out at the one place it is checked, because the
# check is the thing standing between a teardown and the seeded data every
# other suite reads.
# Kept as an assertion rather than a second definition: if the shared guard and
# this suite ever disagreed about which workspaces are seeded, the guard would be
# protecting a different set from the one the suite believes in.
assert frozenset({WORKSPACE_A, WORKSPACE_B}) == SEEDED_WORKSPACES, (
    "the shared workspace guard and this suite disagree about the seeded set"
)

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


# Probed once, at import: the probe fixtures below consult it on every test,
# and a connection attempt per test would pay for the same answer each time.
_POSTGRES_AVAILABLE = _postgres_available()

needs_postgres = pytest.mark.skipif(
    not _POSTGRES_AVAILABLE, reason="PostgreSQL not reachable; start infrastructure/compose"
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

    This one belongs to `test_claims.py`. The four below are the same fixture
    on ids of their own, for the four other modules that write.
    """
    with _probe_workspaces("claims", WORKSPACE_P, WORKSPACE_Q):
        yield WORKSPACE_P, WORKSPACE_Q


@pytest.fixture
def rls_workspaces() -> Iterator[tuple[uuid.UUID, uuid.UUID]]:
    """`probe_workspaces` for `test_rls.py`.

    Before this existed the suite left an `rls-a-*` project in the seeded
    development workspace and an `rls-b-*` project in the seeded second one on
    every run -- and did worse than litter.
    `test_a_delete_cannot_reach_another_workspace` issues a DELETE with no
    WHERE, which is the point of the test: the policy, not the query, is what
    must confine it. Confined to the seeded development workspace, it emptied
    `research.research_projects` there on every run, and
    `research_sessions.project_id` cascades, so every session in that workspace
    went with the projects.
    """
    with _probe_workspaces("rls", WORKSPACE_RLS_P, WORKSPACE_RLS_Q):
        yield WORKSPACE_RLS_P, WORKSPACE_RLS_Q


@pytest.fixture
def integration_workspaces() -> Iterator[tuple[uuid.UUID, uuid.UUID]]:
    """`probe_workspaces` for `test_integration.py`."""
    with _probe_workspaces("integration", WORKSPACE_INTEGRATION_P, WORKSPACE_INTEGRATION_Q):
        yield WORKSPACE_INTEGRATION_P, WORKSPACE_INTEGRATION_Q


@pytest.fixture
def orchestration_workspaces() -> Iterator[tuple[uuid.UUID, uuid.UUID]]:
    """`probe_workspaces` for `test_orchestrator_integration.py`."""
    with _probe_workspaces("orchestration", WORKSPACE_ORCH_P, WORKSPACE_ORCH_Q):
        yield WORKSPACE_ORCH_P, WORKSPACE_ORCH_Q


@pytest.fixture
def security_workspace() -> Iterator[uuid.UUID]:
    """`probe_workspaces` for `test_security.py`, which needs only one.

    Nothing in that module asserts isolation; it asserts that errors, logs and
    readiness payloads carry no tenant content. One workspace is what it uses,
    so one is what it gets -- a second would be a workspace no test writes to,
    which is a fixture pretending to a coverage it does not have.
    """
    with _probe_workspaces("security", WORKSPACE_SECURITY_P):
        yield WORKSPACE_SECURITY_P


@contextlib.contextmanager
def _probe_workspaces(label: str, *workspaces: uuid.UUID) -> Iterator[None]:
    """Hold the given workspaces open for one test, then remove them.

    Dropped before they are created, as well as after. Teardown is in a
    `finally` and so survives a failing test, but it does not survive the run
    being killed -- and the workspaces left behind by an interrupted run would
    be silently reused by the next one, which is the defect these fixtures
    exist to remove, merely made rarer.

    A no-op without PostgreSQL, so that a module can bind one of these autouse
    and still let its Redis-only and Qdrant-only tests run on a machine with no
    database. Those tests use a workspace id as an opaque tenant key and never
    store a row against it.
    """
    if not _POSTGRES_AVAILABLE:
        yield
        return
    _drop_workspaces(workspaces)
    _make_workspaces(label, workspaces)
    try:
        yield
    finally:
        _drop_workspaces(workspaces)


def _make_workspaces(label: str, workspaces: tuple[uuid.UUID, ...]) -> None:
    for workspace in workspaces:
        disposable(workspace, what=f"the {label} fixture")
    import psycopg

    with psycopg.connect(DATABASE_URL) as connection:
        for index, workspace in enumerate(workspaces):
            connection.execute(
                "INSERT INTO core.workspaces (id, name, slug) VALUES (%s,%s,%s) "
                "ON CONFLICT (id) DO NOTHING",
                (workspace, f"{label} probe {index}", f"{label}-probe-{index}"),
            )
        connection.commit()


def _drop_workspaces(workspaces: tuple[uuid.UUID, ...]) -> None:
    for workspace in workspaces:
        disposable(workspace, what="_drop_workspaces")
    """Only ever called for the workspaces a probe fixture created."""
    import psycopg

    ids = list(workspaces)
    with psycopg.connect(DATABASE_URL) as connection:
        # `scoring.evidence` is deleted by name, before the cascade runs.
        # Its `independence_group_id` foreign key is ON DELETE RESTRICT, so a
        # dependent evidence record can refuse the deletion of the group it
        # belongs to. Both tables cascade from `core.workspaces`, and which of
        # the two cascades first is a property of PostgreSQL's trigger order
        # rather than anything this schema states -- so the teardown does not
        # depend on it.
        connection.execute("DELETE FROM scoring.evidence WHERE workspace_id = ANY(%s)", (ids,))
        # Everything else goes with the workspace: every tenant table declares
        # `workspace_id ... REFERENCES core.workspaces (id) ON DELETE CASCADE`,
        # so claims, revisions, observations, independence groups, opportunities,
        # sessions, plans, jobs and projects are all removed by these rows.
        connection.execute("DELETE FROM core.workspaces WHERE id = ANY(%s)", (ids,))
        connection.commit()
