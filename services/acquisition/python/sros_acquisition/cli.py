"""Administrative CLI for the Source Registry.

Mission 1.0 §32. Review status is administered here rather than through the web
API, and the reason is §27: authentication does not exist, so an HTTP endpoint
that could approve a source would make the whole review process a formality
anyone could skip.

    sros-source list                  every source with its state and gate result
    sros-source show reddit           one source in full, including evidence
    sros-source validate              the catalog, with no database
    sros-source eligibility reddit    the gate's verdict and every blocking reason
    sros-source stale                 approving reviews that are due
    sros-source load                  apply the catalog to PostgreSQL
    sros-source render                render the markdown catalog table
    sros-source enable reddit         attempt to enable a collector (usually refused)

**This CLI never collects anything.** It reads governance metadata and writes
governance metadata. No command opens a connection to a source, and there is no
command that could.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from datetime import UTC, datetime
from typing import Any

from sros_contracts import SourceApprovalState

from .registry import (
    SourceCatalog,
    SourceRegistryError,
    evaluate_eligibility,
    find_catalog,
    load_catalog,
    resolve_retention,
)

__all__ = ["main"]


def _catalog(args: argparse.Namespace) -> SourceCatalog:
    return load_catalog(args.catalog or find_catalog())


def _connect() -> Any:
    """Open an administrative connection.

    psycopg is imported here rather than at module level so the registry model,
    the validator and every read command stay runnable with nothing installed
    (ADR-009). Only the commands that touch the database need the driver.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit(
            "DATABASE_URL is not set. Copy infrastructure/compose/.env.example and "
            "export it, or use a command that does not need the database "
            "(list, show, validate, eligibility, stale, render)."
        )
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise SystemExit(
            "psycopg is not installed. Install the workspace dependencies "
            "(uv sync --all-packages) or use a command that does not need the database."
        ) from exc
    return psycopg.connect(url)


# ------------------------------------------------------------------ commands


def cmd_list(args: argparse.Namespace) -> int:
    catalog = _catalog(args)
    now = datetime.now(UTC)

    if args.json:
        print(
            json.dumps(
                [
                    {
                        **evaluate_eligibility(source, now).to_json(),
                        "canonical_name": source.canonical_name,
                        "source_family": source.source_family,
                    }
                    for source in catalog
                ],
                indent=2,
            )
        )
        return 0

    print(f"{'SOURCE':<18} {'FAMILY':<18} {'STATE':<26} {'EVID':>4}  ELIGIBLE")
    print("-" * 82)
    for source in catalog:
        result = evaluate_eligibility(source, now)
        state = source.review.approval_state.value if source.review else "NO REVIEW"
        mark = "yes" if result.eligible else "no"
        print(
            f"{source.source_id:<18} {source.source_family:<18} {state:<26} "
            f"{result.evidence_count:>4}  {mark}"
        )
    eligible = sum(1 for s in catalog if evaluate_eligibility(s, now).eligible)
    print(f"\n{len(catalog)} sources, {eligible} collector-eligible")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    catalog = _catalog(args)
    source = catalog.get(args.source_id)
    review = source.review
    result = evaluate_eligibility(source)
    retention = resolve_retention(source.retention_override)

    print(f"{source.canonical_name}  ({source.source_id})")
    print(f"  family        {source.source_family}")
    print(f"  lifecycle     {source.lifecycle.value}")
    print(f"  description   {source.description}")
    print(
        f"  coverage      {source.coverage.scope}"
        f"  countries={list(source.coverage.countries) or '-'}"
        f"  languages={list(source.coverage.languages) or '-'}"
    )

    print("\n  ACCESS PROFILES (how, not whether)")
    for profile in source.access_profiles:
        needs = [
            name
            for name, flag in (
                ("auth", profile.requires_authentication),
                ("api-key", profile.requires_api_key),
                ("oauth", profile.requires_oauth),
                ("account", profile.requires_account),
                ("dev-app", profile.requires_developer_app),
                ("approval", profile.requires_approval),
            )
            if flag
        ]
        limit = (
            f"{profile.rate_limit_requests}/{profile.rate_limit_period_seconds}s "
            f"({profile.rate_limit_origin})"
            if profile.rate_limit_known
            else "UNKNOWN"
        )
        print(f"    {profile.access_method.value:<20} {profile.label}")
        print(f"      requires    {', '.join(needs) or 'nothing'}")
        print(f"      secrets     {list(profile.secret_references) or '-'}  (key names only)")
        print(f"      rate limit  {limit}")
        print(f"      cost        {profile.acquisition_cost.value}")

    if review is None:
        print("\n  NO POLICY REVIEW")
    else:
        print(f"\n  POLICY REVIEW v{review.review_version}  {review.approval_state.value}")
        print(f"    scope       {review.assessed_use_case[:100]}...")
        print(f"    reviewed    {review.reviewed_at.date()} by {review.reviewed_by}")
        print(
            f"    next review {review.next_review_at.date()}"
            f"{'  STALE' if review.is_stale() else ''}"
        )
        print(f"    pd risk     {review.personal_data_risk.value}")
        print("\n    per-activity assessment")
        from .registry.models import ASSESSED_ACTIVITIES

        for activity in ASSESSED_ACTIVITIES:
            print(f"      {activity:<28} {review.assessment(activity).value}")
        if review.conditions:
            print("\n    conditions")
            for condition in review.conditions:
                print(f"      - {condition}")
        if review.open_questions:
            print("\n    open questions")
            for question in review.open_questions:
                print(f"      - {question}")
        if review.review_notes:
            print(f"\n    notes\n      {review.review_notes}")

        print(f"\n  EVIDENCE ({len(review.evidence)})")
        for item in review.evidence:
            print(f"    [{item.document_type.value}] {item.document_title}")
            print(f"      {item.document_url}")
            print(
                f"      retrieved {item.retrieved_at.date()}  section: {item.section_reference or '-'}"
            )
            print(f"      finding: {item.summarized_finding[:160]}...")
        if not review.evidence:
            print("    none")

    print(
        f"\n  RETENTION    raw {retention.raw_days}d ({retention.raw_source}), "
        f"normalized {retention.normalized_days}d ({retention.normalized_source})"
    )
    if retention.basis:
        print(f"    basis: {retention.basis[:180]}")

    print(f"\n  COLLECTOR ELIGIBLE: {'yes' if result.eligible else 'NO'}")
    for reason in result.blocking_reasons:
        print(f"    - {reason}")
    return 0


def cmd_eligibility(args: argparse.Namespace) -> int:
    catalog = _catalog(args)
    sources = [catalog.get(args.source_id)] if args.source_id else list(catalog)
    blocked = 0
    for source in sources:
        result = evaluate_eligibility(source)
        if args.json:
            print(json.dumps(result.to_json(), indent=2))
            continue
        print(f"{source.source_id}: {'ELIGIBLE' if result.eligible else 'BLOCKED'}")
        for reason in result.blocking_reasons:
            print(f"  - {reason}")
        blocked += 0 if result.eligible else 1
    return 0


def cmd_stale(args: argparse.Namespace) -> int:
    """Approving reviews that are due, and reviews that never concluded.

    Both matter. A stale approval is a statement about the past presented as a
    statement about now; a review stuck in REQUIRES_REVIEW is work nobody
    scheduled.
    """
    catalog = _catalog(args)
    now = datetime.now(UTC)
    stale = [s for s in catalog if s.review and s.review.is_stale(now)]
    pending = [
        s
        for s in catalog
        if s.review and s.review.approval_state is SourceApprovalState.REQUIRES_REVIEW
    ]

    print(f"STALE REVIEWS ({len(stale)})")
    for source in stale:
        assert source.review is not None  # noqa: S101 - guarded by the comprehension
        print(f"  {source.source_id:<18} due {source.review.next_review_at.date()}")
    if not stale:
        print("  none")

    print(f"\nAWAITING REVIEW ({len(pending)})")
    for source in pending:
        assert source.review is not None  # noqa: S101 - guarded by the comprehension
        questions = len(source.review.open_questions)
        print(f"  {source.source_id:<18} {questions} open question(s)")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Delegate to the zero-dependency validator, so there is one implementation."""
    root = pathlib.Path(__file__).resolve().parents[4]
    script = root / "infrastructure" / "scripts" / "validate_source_registry.py"
    if not script.exists():
        print(f"validator not found at {script}", file=sys.stderr)
        return 1
    import subprocess

    return subprocess.run(  # noqa: S603 - fixed path, no shell, no user input
        [sys.executable, str(script), str(args.catalog or find_catalog())], check=False
    ).returncode


def cmd_load(args: argparse.Namespace) -> int:
    from .registry.repositories import load_catalog_into

    catalog = _catalog(args)
    with _connect() as conn, conn.transaction():
        report = load_catalog_into(conn, catalog)
    print(f"loaded: {report.describe()}")
    print("collector_enabled was not set for any source: enablement is a separate decision")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    """Render the markdown catalog table from the JSON.

    `--check` compares against the committed file and fails on a difference,
    the same contract `generate.py --check` enforces for the domain vocabulary:
    a governance table that has drifted from its data is worse than no table,
    because it is the one a reader trusts.
    """
    from .rendering import render_catalog_markdown

    catalog = _catalog(args)
    rendered = render_catalog_markdown(catalog)
    target = pathlib.Path(args.output) if args.output else find_catalog().with_suffix(".md")

    if args.check:
        if not target.exists():
            print(f"FAIL  {target} does not exist", file=sys.stderr)
            return 1
        if target.read_text(encoding="utf-8") != rendered:
            print(
                f"FAIL  {target} is out of date. Run `sros-source render` to regenerate.",
                file=sys.stderr,
            )
            return 1
        print(f"ok    {target.name} matches the catalog")
        return 0

    target.write_text(rendered, encoding="utf-8")
    print(f"wrote {target}")
    return 0


def cmd_enable(args: argparse.Namespace) -> int:
    """Attempt to enable a collector. Expected to fail for every source today.

    The command exists so the refusal is reachable and readable, rather than
    something an operator discovers by editing the table by hand.
    """
    catalog = _catalog(args)
    source = catalog.get(args.source_id)
    result = evaluate_eligibility(source)
    if not result.eligible:
        print(f"REFUSED: {source.source_id} is not collector-eligible", file=sys.stderr)
        for reason in result.blocking_reasons:
            print(f"  - {reason}", file=sys.stderr)
        return 1

    with _connect() as conn, conn.transaction():
        conn.execute(
            "UPDATE registry.sources SET collector_enabled = TRUE WHERE id = %s",
            (source.source_id,),
        )
    print(f"collector enabled for {source.source_id}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sros-source", description=__doc__)
    parser.add_argument("--catalog", help="path to source-catalog-v1.json")
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("list", help="every source with its state and gate result")
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(func=cmd_list)

    show = sub.add_parser("show", help="one source in full, including evidence")
    show.add_argument("source_id")
    show.set_defaults(func=cmd_show)

    validate = sub.add_parser("validate", help="validate the catalog, no database needed")
    validate.set_defaults(func=cmd_validate)

    eligibility = sub.add_parser("eligibility", help="the gate's verdict and blocking reasons")
    eligibility.add_argument("source_id", nargs="?")
    eligibility.add_argument("--json", action="store_true")
    eligibility.set_defaults(func=cmd_eligibility)

    stale = sub.add_parser("stale", help="reviews that are due or never concluded")
    stale.set_defaults(func=cmd_stale)

    load = sub.add_parser("load", help="apply the catalog to PostgreSQL")
    load.set_defaults(func=cmd_load)

    render = sub.add_parser("render", help="render the markdown catalog table")
    render.add_argument("--check", action="store_true", help="fail if the file is out of date")
    render.add_argument("--output")
    render.set_defaults(func=cmd_render)

    enable = sub.add_parser("enable", help="attempt to enable a collector")
    enable.add_argument("source_id")
    enable.set_defaults(func=cmd_enable)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result: int = args.func(args)
        return result
    except SourceRegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
