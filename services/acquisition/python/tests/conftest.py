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
