"""Integration test fixtures.

These tests require the local stack (`infrastructure/compose`). They skip
cleanly when it is not running, so a contributor without Docker still gets a
green unit run and an explicit note about what was not covered — rather than a
red suite that teaches them to ignore failures.

**Two workspaces are always present.** A tenancy system tested with one tenant
is not meaningfully tested: every isolation assertion here needs a second
workspace to have something to be isolated *from*.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest

WORKSPACE_A = uuid.UUID("00000000-0000-4000-8000-000000000001")
WORKSPACE_B = uuid.UUID("00000000-0000-4000-8000-000000000003")

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
