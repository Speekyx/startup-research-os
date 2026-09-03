#!/usr/bin/env python3
"""Run every pytest suite, one package per subprocess.

Each package has a top-level `tests` package, so a single interpreter would
collide on `sys.modules["tests"]`. Per-package subprocesses keep the suites
independent and the output readable.

This is the INSTALL-DEPENDENT runner. `run_python_tests.py` is the
zero-dependency one and must keep working (ADR-009): between them, a broken
environment can never silently reduce coverage to nothing.

    python infrastructure/scripts/run_pytest_suites.py

**It also asserts that the run left the database as it found it.** Every tenant
table is counted before and after, and any difference fails the run.

Mission 1.6 found four gateway modules writing into the SEEDED development
workspaces and never cleaning up -- 21 research projects, 47 opportunities and 3
sessions after one run -- plus an unscoped `DELETE FROM
research.research_projects` in `test_rls.py` that emptied a seeded workspace
every time, cascading its sessions away with it. Every one of those tests
passed. Nothing inside a suite could see it, because "the run changed nothing"
is a property of the RUN: a test observes the database only at the moment it
runs, and the leak is what is there afterwards.

It surfaced instead in a later mission's suite, as an assertion that counted
rows and found 39 it had not written -- where it looked like that assertion's
fault and was very nearly weakened to make it pass. The check lives here so the
next one fails where it was caused.

**Mission 1.7 §31 added the other half.** A `workspace_id` is what the query
above looks for, so `registry.*` -- global platform metadata, no `workspace_id`
anywhere in it -- was outside the check by construction, and
`test-data-isolation-audit-v1.md` §6 named that gap rather than closing it.
Three acquisition modules mutate the registry, one of them by turning a
collector on. `testing/registry_state.py` covers them, by content rather than by
count: flipping a boolean inside a row does not move a row count.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

# One definition of what global state is, shared with whatever else needs to
# assert over it, rather than a second copy that drifts from this one.
sys.path.insert(0, str(ROOT / "infrastructure"))
from testing import registry_state  # noqa: E402

SUITES = [
    "packages/contracts/python",
    "packages/llm-gateway/python",
    "packages/semantic-equivalence/python",
    "services/workers/python",
    "services/acquisition/python",
    "services/nlp/python",
    "services/research-orchestrator/python",
    "services/gateway/python",
]

# The schemas the application owns. Named so that a tenant table added to one of
# them is covered without anyone remembering this file -- the rows that started
# this were in tables nobody had thought to list.
TENANT_SCHEMAS = ("core", "registry", "research", "acquisition", "nlp", "scoring")

Snapshot = dict[tuple[str, str], int]


def _connect(url: str) -> object | None:
    """A connection, or None with an explicit note about what went unchecked.

    Never a silent skip. A contributor without Docker must still get a green
    run, but they must not get one that implies the database was inspected.
    """
    try:
        import psycopg
    except ImportError:
        print("NOTE: psycopg is not installed; leftover rows were NOT checked")
        return None
    try:
        return psycopg.connect(url, connect_timeout=5)
    except Exception:
        print("NOTE: PostgreSQL is not reachable; leftover rows were NOT checked")
        return None


def _reads_across_tenants(conn: object) -> bool:
    """Whether this connection can see every workspace's rows.

    The policies are ENABLE **and FORCE** (ADR-012), so they bind the table
    owner too. A role subject to them counts zero rows in every tenant table,
    and this check would then pass while measuring nothing -- a false negative
    in the one place that must not have one.
    """
    row = conn.execute(
        "SELECT current_setting('is_superuser') = 'on' "
        "OR COALESCE((SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user), false)"
    ).fetchone()
    return bool(row and row[0])


def _tenant_tables(conn: object) -> list[str]:
    """Every base table carrying a `workspace_id`, read from the catalog.

    Derived, not listed. `test_rls.py` keeps a hand-written list on purpose:
    there, a new table SHOULD fail a test until someone states whether it is
    tenant data. Here the opposite is wanted -- a new table must be watched from
    the moment it exists, including by whoever never opened this file.
    """
    rows = conn.execute(
        """SELECT n.nspname || '.' || c.relname
             FROM pg_class c
             JOIN pg_namespace n ON n.oid = c.relnamespace
             JOIN pg_attribute a ON a.attrelid = c.oid
            WHERE c.relkind = 'r' AND a.attname = 'workspace_id' AND NOT a.attisdropped
              AND n.nspname = ANY(%s)
            ORDER BY 1""",
        (list(TENANT_SCHEMAS),),
    ).fetchall()
    return [r[0] for r in rows]


def _snapshot(conn: object, tables: list[str]) -> Snapshot:
    """Row counts per (table, workspace).

    Per workspace rather than per table, because a suite that leaves a row in a
    throwaway workspace it then drops nets to zero -- and a leak into a SEEDED
    workspace is the failure. Keeping the workspace in the key also puts it in
    the report, which is the first thing anyone reading it needs.
    """
    counts: Snapshot = {}
    for table in tables:
        # `table` came from the system catalog, never from input, and an
        # identifier cannot be parameterised in SQL.
        sql = f"SELECT workspace_id::text, count(*) FROM {table} GROUP BY 1"  # noqa: S608
        rows = conn.execute(sql).fetchall()
        for workspace, count in rows:
            counts[(table, workspace)] = count
    return counts


def _labels(conn: object, table: str, workspace: str) -> str:
    """A few row labels, so the report names the culprit and not just a count.

    `rls-a-*` identifies the suite, the module and the fixture at a glance;
    "4 rows" sends the reader to write this query by hand, which is how the
    original leak stayed unexamined for two missions.
    """
    for column in ("name", "title", "statement", "observation_key", "source_id"):
        sql = (
            f"SELECT DISTINCT {column}::text FROM {table} "  # noqa: S608
            "WHERE workspace_id = %s ORDER BY 1 LIMIT 5"
        )
        try:
            rows = conn.execute(sql, (workspace,)).fetchall()
        except Exception:
            # No such column on this table. Rolling back is required before the
            # connection will accept the next statement.
            conn.rollback()
            continue
        if rows:
            return "      " + ", ".join(repr(r[0]) for r in rows)
    return ""


def _report(conn: object, tables: list[str], before: Snapshot, after: Snapshot) -> bool:
    """True when the run left the database as it found it."""
    # The watched COUNT, not the number of tables that happened to hold rows.
    # An empty derivation would make every comparison trivially equal, and this
    # check would report success having measured nothing -- so it is an error,
    # and the count is printed rather than implied so a drop in it is visible.
    if not tables:
        print(
            "NO TENANT TABLES FOUND: the catalog query is wrong, nothing was checked",
            file=sys.stderr,
        )
        return False

    changed = sorted(k for k in set(before) | set(after) if before.get(k, 0) != after.get(k, 0))
    if not changed:
        print(f"database unchanged by the run, across {len(tables)} tenant tables")
        return True

    out = sys.stderr
    print(f"\nTHE RUN CHANGED THE DATABASE: {len(changed)} table/workspace pair(s)", file=out)
    print("A suite that writes must clean up after itself. The pattern is the", file=out)
    print("probe-workspace fixtures in services/*/python/tests/conftest.py:", file=out)
    print("workspaces of the suite's own, created per test and dropped per test.\n", file=out)
    for table, workspace in changed:
        was, now = before.get((table, workspace), 0), after.get((table, workspace), 0)
        print(f"  {table:<44} {workspace}  {was} -> {now} ({now - was:+d})", file=out)
        if now > was:
            labels = _labels(conn, table, workspace)
            if labels:
                print(labels, file=out)
    return False


def main() -> int:
    env = dict(os.environ)
    env.setdefault("DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros")
    env.setdefault("REDIS_URL", "redis://127.0.0.1:55379/0")
    env.setdefault("QDRANT_URL", "http://127.0.0.1:55333")

    conn = _connect(env["DATABASE_URL"])
    if conn is not None and not _reads_across_tenants(conn):
        print(
            "NOTE: this role is bound by row-level security, so a per-tenant count would "
            "read zero everywhere; leftover rows were NOT checked",
            file=sys.stderr,
        )
        conn.close()
        conn = None
    tables = _tenant_tables(conn) if conn is not None else []
    before = _snapshot(conn, tables) if conn is not None else {}

    # The complement: everything in the owned schemas that carries no
    # `workspace_id`, which is the registry and nothing the tenant check sees.
    global_tables = registry_state.global_tables(conn) if conn is not None else []
    global_before = registry_state.snapshot(conn, global_tables) if conn is not None else {}

    failures: list[str] = []
    for suite in SUITES:
        print(f"=== {suite} " + "=" * max(0, 60 - len(suite)))
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q"],
            cwd=ROOT / suite,
            env=env,
            check=False,
        )
        if proc.returncode != 0:
            failures.append(suite)
        print()

    print("=" * 70)
    # Reported even when a suite failed. A failing run still leaves its rows
    # behind, and the leak is harder to find once someone has "fixed the tests".
    clean = True
    if conn is not None:
        clean = _report(conn, tables, before, _snapshot(conn, tables))
        differences = registry_state.compare(
            global_before, registry_state.snapshot(conn, global_tables)
        )
        global_clean, text = registry_state.format_report(global_tables, differences)
        print(text, file=sys.stdout if global_clean else sys.stderr)
        clean = clean and global_clean
        conn.close()

    if failures:
        print(f"FAILED suites: {', '.join(failures)}", file=sys.stderr)
        return 1
    if not clean:
        return 1
    print(f"all pytest suites passed across {len(SUITES)} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
