"""Operational CLI for normalization.

Mission 1.6 §50. Separate from `sros-source`, which administers governance, and
from `sros-acquisition`, which collects. Three commands that cannot be confused
for one another is worth more than one command with a mode flag.

    sros-normalize validate                    what can be normalized, and by what
    sros-normalize run --raw-record <id>       one record, or several
    sros-normalize run --session <id>          a bounded batch for one session
    sros-normalize history --observation <key> every representation of one observation

**No command reaches a network**, including `run`. Normalization reads records
this deployment already holds; there is no flag that would make it fetch
anything, because there is no code path that could.

**No command accepts a payload.** `run` takes record ids and a session id, never
a document, a URL or a JSON blob. §50 prefers internal tooling to an endpoint
that accepts arbitrary source payloads, and the way to prefer it is to have no
argument that could carry one.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from .cli import _load_local_env
from .normalization import (
    MAX_NORMALIZATION_BATCH,
    NORMALIZER_REGISTRY,
    count_normalized,
    find_geography_map,
    load_geography_map,
    read_normalized_history,
    run_normalization_job,
)
from .registry import SourceRegistryError, find_catalog, load_catalog

__all__ = ["main"]


@contextmanager
def _tenant_connection(workspace_id: str) -> Any:
    """A connection inside a tenant transaction (ADR-012).

    Both isolation layers are entered: `SET LOCAL ROLE` so the row-level
    policies apply at all, and the transaction-local workspace so they resolve
    to this tenant. The explicit `workspace_id` filter in the repository is the
    other layer and is not removed because this exists.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set; normalization has nothing to read")
    import psycopg

    role = os.environ.get("APP_DB_ROLE", "sros_app")
    with psycopg.connect(url) as conn, conn.transaction():
        conn.execute(f"SET LOCAL ROLE {role}")
        conn.execute("SELECT set_config('app.workspace_id', %s, true)", (workspace_id,))
        yield conn


def cmd_validate(args: argparse.Namespace) -> int:
    """What this deployment can normalize, and under what versions.

    Reaches no network and no database. It answers the question an operator
    actually has before running a batch: is there an adapter for the records I
    have, and which collector versions does it accept.
    """
    catalog = load_catalog(args.catalog or find_catalog())
    geography = load_geography_map(args.geography or find_geography_map())

    print(f"REGISTERED NORMALIZERS ({len(NORMALIZER_REGISTRY)})")
    for (source_id, collector_id), spec in sorted(NORMALIZER_REGISTRY.items()):
        print(f"  {source_id:<16} <- {collector_id}")
        print(f"    normalizer  {spec.normalizer_id}@{spec.normalizer_version}")
        print(f"    schema      {spec.schema_id}/{spec.schema_version}")
        print(f"    accepts     collector {sorted(spec.supported_collector_versions)}")

    normalizable = {source_id for source_id, _ in NORMALIZER_REGISTRY}
    unhandled = sorted({s.source_id for s in catalog} - normalizable)
    print(f"\n  NO NORMALIZER ({len(unhandled)})")
    print(f"    {', '.join(unhandled)}")
    print("    A source here is not normalizable, whatever its eligibility says.")

    print(f"\n  GEOGRAPHY MAP ({geography.canonical_scheme})")
    for source_id in sorted(geography.entries):
        codes = geography.codes_for(source_id)
        print(f"    {source_id:<16} {len(codes)} classified: {', '.join(codes)}")
    print("    An unclassified code stays UNKNOWN and never becomes a country.")

    print("\nNothing was normalized. This command reaches no network and no database.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if not args.raw_record and not args.session:
        print("REFUSED: pass --raw-record or --session", file=sys.stderr)
        return 2

    payload = {
        "workspace_id": args.workspace,
        # A session is required even when normalizing explicit record ids: it is
        # the research context the work belongs to, and a job with no session
        # cannot be attributed to anything (§33).
        "research_session_id": args.session or "",
        "correlation_id": args.correlation_id or f"normalize-{datetime.now(UTC):%Y%m%dT%H%M%SZ}",
        "raw_record_ids": list(args.raw_record or ()),
        "source_id": args.source,
        "max_records": args.max_records,
        "only_unnormalized": not args.renormalize,
    }

    try:
        result = run_normalization_job(payload, _tenant_connection)
    except ValueError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_json(), indent=2))
    with _tenant_connection(args.workspace) as conn:
        total = count_normalized(conn, args.workspace)
    print(f"\nnormalized records in this workspace: {total}")
    return 0 if result.succeeded else 1


def cmd_history(args: argparse.Namespace) -> int:
    """Every representation of one observation, newest first.

    Deliberately unfiltered by normalizer version: the point is that several
    coexist and can all be seen. Which one downstream should read is D-08, open,
    and this command takes no position on it.
    """
    with _tenant_connection(args.workspace) as conn:
        rows = read_normalized_history(conn, args.workspace, args.observation)
    if not rows:
        print(f"no normalized record for {args.observation!r} in this workspace")
        return 1
    for row in rows:
        marker = "current " if row["current"] else "SUPERSEDED"
        payload = row["payload"] or {}
        observation = payload.get("observation", {}) if isinstance(payload, dict) else {}
        print(
            f"  {marker} {row['normalizer']} schema {row['schema_version']} "
            f"quality={row['quality']:<8} value={observation.get('value')!r} "
            f"collected {row['collected_at']}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sros-normalize", description=__doc__)
    parser.add_argument("--catalog")
    parser.add_argument("--geography")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="what can be normalized, and by what")
    validate.set_defaults(func=cmd_validate)

    run = commands.add_parser("run", help="normalize a bounded batch")
    run.add_argument("--workspace", required=True)
    run.add_argument("--session")
    # `--raw-record`, never `--payload`. §50: the way to keep arbitrary source
    # payloads out is to have no argument that could carry one.
    run.add_argument("--raw-record", action="append")
    run.add_argument("--source")
    run.add_argument(
        "--max-records",
        type=int,
        default=MAX_NORMALIZATION_BATCH,
        dest="max_records",
        help=f"our own bound; capped at {MAX_NORMALIZATION_BATCH} whatever is passed",
    )
    run.add_argument(
        "--renormalize",
        action="store_true",
        help="include records already normalized under this lineage; existing rows stand",
    )
    run.add_argument("--correlation-id", dest="correlation_id")
    run.set_defaults(func=cmd_run)

    history = commands.add_parser("history", help="every representation of one observation")
    history.add_argument("--workspace", required=True)
    history.add_argument("--observation", required=True)
    history.set_defaults(func=cmd_history)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    loaded = _load_local_env()
    if loaded is not None:
        print(f"read local configuration from {loaded}", file=sys.stderr)
    try:
        result: int = args.func(args)
        return result
    except SourceRegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
