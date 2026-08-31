"""Operational CLI for acquisition.

Mission 1.5 §40. Separate from `sros-source`, which administers governance: this
one *runs* things, and keeping the two apart means a command that reviews a
source and a command that collects from it cannot be confused for each other.

    sros-acquisition world-bank validate   the authorization, without collecting
    sros-acquisition world-bank smoke      one tiny live request. Opt-in
    sros-acquisition world-bank collect    a bounded collection, persisted

**No command accepts a URL.** Every one takes indicators, countries and years,
and the collector composes the request. §40 forbids exposing arbitrary URL
input, and the way to forbid it is to have no argument that could carry one.

`smoke` and `collect` are the only commands that reach a network, both require
an explicit opt-in flag, and neither is reachable from CI.
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
from .collection import (
    CollectionBounds,
    HttpxTransport,
    RequestPacer,
    TransportConfig,
    WorldBankCollector,
    WorldBankRequest,
    collector_enabled,
    count_records,
    persist_drafts,
)
from .collection.pacing import WORLD_BANK_PACING
from .compliance import (
    AcquisitionNotAuthorizedError,
    build_authorization,
    find_compliance_config,
    load_compliance,
)
from .compliance.use_profile import declared_use_profile
from .registry import SourceRegistryError, find_catalog, load_catalog

__all__ = ["main"]

SMOKE_FLAG = "SROS_ENABLE_WORLD_BANK_SMOKE_TESTS"
_SOURCE_ID = "world-bank"


def _context(args: argparse.Namespace) -> Any:
    catalog = load_catalog(args.catalog or find_catalog())
    compliance = load_compliance(args.compliance or find_compliance_config())
    # The runtime declares its profile. There is no default and no flag that
    # could supply one, because an operator who can pass --use-profile to a
    # COLLECTION command can pick the permission they want.
    return build_authorization(catalog.get(_SOURCE_ID), declared_use_profile(), compliance)


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
        raise SystemExit("DATABASE_URL is not set; a collection has nowhere to persist")
    import psycopg

    role = os.environ.get("APP_DB_ROLE", "sros_app")
    with psycopg.connect(url) as conn, conn.transaction():
        conn.execute(f"SET LOCAL ROLE {role}")
        conn.execute("SELECT set_config('app.workspace_id', %s, true)", (workspace_id,))
        yield conn


def cmd_validate(args: argparse.Namespace) -> int:
    """Prove the authorization path without collecting anything.

    Reaches no network. It answers the question an operator actually has before
    running a collection: would this be permitted, and which of my indicators
    are authorized resources.
    """
    try:
        context = _context(args)
    except AcquisitionNotAuthorizedError as exc:
        print(f"REFUSED: no acquisition authorization for {_SOURCE_ID}", file=sys.stderr)
        for reason in exc.reasons:
            print(f"  - {reason}", file=sys.stderr)
        return 1

    print(f"AUTHORIZED  {context.source_id} review v{context.review_version}")
    print(f"  endpoint     {context.access[0].endpoint_url}")
    print(f"  retention    raw {context.retention.raw_days}d (from governance, not chosen here)")
    print(f"  attribution  {[r.element.value for r in context.attribution.requirements]}")
    print(f"\n  AUTHORIZED DATASETS ({len(context.datasets)})")
    for dataset in context.datasets:
        print(f"    {dataset.resource_id:<34} {dataset.licence:<12} {dataset.content_origin}")

    requested = tuple(args.indicator or ())
    if requested:
        print("\n  REQUESTED")
        refused = 0
        for indicator in requested:
            dataset = context.authorized_dataset(f"indicator/{indicator}")
            mark = "authorized" if dataset else "REFUSED (not an authorized dataset)"
            print(f"    {indicator:<24} {mark}")
            refused += 0 if dataset else 1
        if refused:
            return 1
    print("\nNothing was collected. This command reaches no network.")
    return 0


def _collect(args: argparse.Namespace, *, persist: bool, bounds: CollectionBounds) -> int:
    if os.environ.get(SMOKE_FLAG, "0") != "1":
        print(
            f"REFUSED: this command contacts the World Bank API and {SMOKE_FLAG} is not "
            "set to 1. Live collection is opt-in, and CI never sets it",
            file=sys.stderr,
        )
        return 2
    try:
        context = _context(args)
    except AcquisitionNotAuthorizedError as exc:
        print(f"REFUSED: {'; '.join(exc.reasons)}", file=sys.stderr)
        return 1

    collector = WorldBankCollector(
        HttpxTransport(TransportConfig()),
        pacer=RequestPacer(WORLD_BANK_PACING),
    )
    request = WorldBankRequest(
        indicators=tuple(args.indicator),
        countries=tuple(args.country or ("all",)),
        start_year=args.start_year,
        end_year=args.end_year,
        per_page=args.per_page,
    )
    correlation_id = args.correlation_id or f"cli-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
    result = collector.collect(
        context,
        request,
        workspace_id=args.workspace,
        correlation_id=correlation_id,
        research_session_id=args.session,
        bounds=bounds,
    )

    print(json.dumps(result.to_json(), indent=2))
    for draft in result.drafts[: args.show]:
        print(
            f"  {draft.observation_key:<52} value="
            f"{draft.payload.get('value')!r:>18}  expires {draft.expires_at.date()}"
        )
    if len(result.drafts) > args.show:
        print(f"  ... and {len(result.drafts) - args.show} more")
    if result.drafts:
        print(f"\n  attribution: {result.drafts[0].attribution_text}")

    if not persist:
        print("\nNOT PERSISTED. Pass --persist to write, which needs a workspace and session.")
        return 0 if result.succeeded else 1

    if not args.session:
        print("REFUSED: --persist requires --session", file=sys.stderr)
        return 1
    with _tenant_connection(args.workspace) as conn:
        # The operational switch governs every persisting path, not just the
        # Celery one (§27). Eligible says *may we*; enabled says *is it turned
        # on*, and an operator turning it on is a deliberate act the CLI must
        # not take on their behalf.
        if not collector_enabled(conn, _SOURCE_ID):
            print(
                f"REFUSED: {_SOURCE_ID} is not enabled. Records were collected and will "
                "NOT be stored. Enable it deliberately with `sros-source enable "
                f"{_SOURCE_ID}`",
                file=sys.stderr,
            )
            return 1
        report = persist_drafts(conn, result.drafts)
        total = count_records(conn, args.workspace, _SOURCE_ID)
    print(f"\npersisted: {report.describe()}")
    print(f"world-bank raw records in this workspace: {total}")
    return 0 if result.succeeded else 1


def cmd_smoke(args: argparse.Namespace) -> int:
    """One tiny live request. Non-persisting by default (§47)."""
    args.per_page = min(args.per_page, 5)
    return _collect(
        args,
        persist=bool(args.persist),
        # A smoke test proves connectivity and parsing. Bulk collection is a
        # different act and gets a different command.
        bounds=CollectionBounds(max_pages=1, max_records=5),
    )


def cmd_collect(args: argparse.Namespace) -> int:
    return _collect(
        args,
        persist=True,
        bounds=CollectionBounds(max_pages=args.max_pages, max_records=args.max_records),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sros-acquisition", description=__doc__)
    parser.add_argument("--catalog")
    parser.add_argument("--compliance")
    sub = parser.add_subparsers(dest="source", required=True)
    world_bank = sub.add_parser("world-bank", help="the World Bank Indicators collector")
    commands = world_bank.add_subparsers(dest="command", required=True)

    def shared(target: argparse.ArgumentParser) -> None:
        # `--indicator`, never `--url`. §40: the way to forbid arbitrary URL
        # input is to have no argument that could carry one.
        target.add_argument("--indicator", action="append", required=True)
        target.add_argument("--country", action="append")
        target.add_argument("--start-year", type=int, dest="start_year")
        target.add_argument("--end-year", type=int, dest="end_year")
        target.add_argument("--per-page", type=int, default=50, dest="per_page")
        target.add_argument("--workspace", required=True)
        target.add_argument("--session")
        target.add_argument("--correlation-id", dest="correlation_id")
        target.add_argument("--show", type=int, default=10)

    validate = commands.add_parser("validate", help="the authorization, without collecting")
    validate.add_argument("--indicator", action="append")
    validate.set_defaults(func=cmd_validate)

    smoke = commands.add_parser("smoke", help=f"one tiny live request. Needs {SMOKE_FLAG}=1")
    shared(smoke)
    smoke.add_argument("--persist", action="store_true")
    smoke.set_defaults(func=cmd_smoke)

    collect = commands.add_parser("collect", help=f"bounded collection. Needs {SMOKE_FLAG}=1")
    shared(collect)
    collect.add_argument("--max-pages", type=int, default=2, dest="max_pages")
    collect.add_argument("--max-records", type=int, default=200, dest="max_records")
    collect.set_defaults(func=cmd_collect)

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
