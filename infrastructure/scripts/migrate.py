#!/usr/bin/env python3
"""Apply forward-only SQL migrations.

ADR-008: plain numbered SQL with a `core.schema_migrations` ledger. No ORM
models exist yet, so autogeneration would have nothing to generate from, and
reviewable SQL is worth more at foundation than a migration DSL.

Every migration is applied in a transaction together with its ledger row, so a
half-applied migration is not a reachable state.

    python infrastructure/scripts/migrate.py --plan      # no DB needed
    python infrastructure/scripts/migrate.py --apply     # needs psycopg
    python infrastructure/scripts/migrate.py --apply --seed

`--plan` deliberately works with no database driver installed: it is the check
CI can run, and it is how you inspect what would happen before it happens.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "infrastructure" / "db" / "migrations"
SEEDS = ROOT / "infrastructure" / "db" / "seed"

LEDGER = "core.schema_migrations"


def discover(directory: pathlib.Path) -> list[tuple[str, pathlib.Path, str]]:
    out = []
    for path in sorted(directory.glob("*.sql")):
        body = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(body.encode("utf-8")).hexdigest()
        out.append((path.stem, path, checksum))
    return out


def plan() -> int:
    migrations = discover(MIGRATIONS)
    if not migrations:
        print(f"no migrations in {MIGRATIONS}", file=sys.stderr)
        return 1
    print(f"migrations directory: {MIGRATIONS.relative_to(ROOT)}")
    for version, path, checksum in migrations:
        lines = len(path.read_text(encoding="utf-8").splitlines())
        print(f"  {version:<28} {checksum[:12]}  {lines:>4} lines")
    seeds = discover(SEEDS) if SEEDS.exists() else []
    if seeds:
        print("\nseed files (idempotent, development only):")
        for version, _path, checksum in seeds:
            print(f"  {version:<28} {checksum[:12]}")
    print(f"\nledger table: {LEDGER}")
    print("apply with: python infrastructure/scripts/migrate.py --apply")
    return 0


def apply(include_seed: bool) -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print(
            "DATABASE_URL is not set. Copy infrastructure/compose/.env.example "
            "and export it, or run with --plan.",
            file=sys.stderr,
        )
        return 2

    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError:
        print(
            "psycopg is not installed. Install it (pip install 'psycopg[binary]') "
            "or run migrations from the api container.",
            file=sys.stderr,
        )
        return 2

    applied = 0
    with psycopg.connect(url, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS core")
            # LEDGER is a module constant, never user input. noqa is narrower
            # than disabling the rule, and keeps the reason next to the code.
            cur.execute(  # noqa: S608
                f"""CREATE TABLE IF NOT EXISTS {LEDGER} (
                        version    TEXT PRIMARY KEY,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        checksum   TEXT NOT NULL
                    )"""
            )
            conn.commit()

            cur.execute(f"SELECT version, checksum FROM {LEDGER}")  # noqa: S608
            known = dict(cur.fetchall())

        for version, path, checksum in discover(MIGRATIONS):
            if version in known:
                if known[version] != checksum:
                    print(
                        f"FAIL {version}: checksum changed after it was applied. "
                        "Migrations are forward-only and immutable once applied; "
                        "write a new migration instead.",
                        file=sys.stderr,
                    )
                    return 1
                print(f"skip  {version} (already applied)")
                continue

            # Migration and ledger row commit together: a half-applied
            # migration is not a reachable state.
            with conn.cursor() as cur:
                cur.execute(path.read_text(encoding="utf-8"))
                cur.execute(
                    # LEDGER is a module constant, never user input.
                    f"INSERT INTO {LEDGER} (version, checksum) VALUES (%s, %s)",  # noqa: S608
                    (version, checksum),
                )
            conn.commit()
            print(f"apply {version}")
            applied += 1

        if include_seed and SEEDS.exists():
            for version, path, _ in discover(SEEDS):
                with conn.cursor() as cur:
                    cur.execute(path.read_text(encoding="utf-8"))
                conn.commit()
                print(f"seed  {version}")

    print(f"\n{applied} migration(s) applied")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true", help="list migrations, no database needed")
    group.add_argument("--apply", action="store_true", help="apply pending migrations")
    parser.add_argument("--seed", action="store_true", help="also run development seed files")
    args = parser.parse_args()

    return plan() if args.plan else apply(args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
