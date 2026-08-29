"""Administrative CLI for the Source Registry.

Mission 1.0 §32. Review status is administered here rather than through the web
API, and the reason is §27: authentication does not exist, so an HTTP endpoint
that could approve a source would make the whole review process a formality
anyone could skip.

    sros-source list                  every source with its state and gate result
    sros-source show reddit           one source in full, including evidence
    sros-source validate              the catalog, with no database
    sros-source eligibility reddit    the gate's verdict and every blocking reason
    sros-source conditions world-bank each review condition and its verification
    sros-source verify world-bank     run the verifiers; --apply records the result
    sros-source authorization fred    the context a collector would receive, or the refusal
    sros-source stale                 approving reviews that are due
    sros-source load                  apply the catalog to PostgreSQL
    sros-source render                render the markdown catalog table
    sros-source enable reddit         attempt to enable a collector (usually refused)

**Two views, kept apart (Mission 1.4).** `render` writes the CATALOG view: what
the reviews say, with no condition verified, which is the only view a committed
file can hold without drifting with the machine it was generated on. Every other
command shows the LIVE view: the same reviews with the verifiers actually run
against this environment. A source can be blocked in one and clear in the other,
and each command says which it is showing.

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

from . import IMPLEMENTED_COLLECTORS
from .compliance import (
    AcquisitionNotAuthorizedError,
    ComplianceConfig,
    ConditionVerificationRecord,
    build_authorization,
    design_eligible,
    find_compliance_config,
    load_compliance,
    satisfied_condition_keys,
    verify_source,
)
from .registry import (
    SourceCatalog,
    SourceRecord,
    SourceRegistryError,
    evaluate_eligibility,
    find_catalog,
    load_catalog,
    resolve_retention,
)
from .registry.eligibility import EligibilityResult

__all__ = ["main"]


def _catalog(args: argparse.Namespace) -> SourceCatalog:
    return load_catalog(args.catalog or find_catalog())


def _compliance(args: argparse.Namespace) -> ComplianceConfig:
    return load_compliance(getattr(args, "compliance", None) or find_compliance_config())


def _live_eligibility(
    source: SourceRecord, config: ComplianceConfig, now: datetime | None = None
) -> tuple[EligibilityResult, tuple[ConditionVerificationRecord, ...]]:
    """The gate, with this environment's verifiers actually run.

    The records come back with the verdict rather than being discarded: a
    command that prints "blocked" without being able to say which condition
    failed is the sort of output people work around instead of using.
    """
    records = verify_source(source, config)
    result = evaluate_eligibility(source, now, satisfied_condition_keys(list(records)))
    return result, records


# The project's documented local configuration file. `.env.example` says "Copy
# to `.env` in this directory and adjust", and until now nothing read it back:
# every command took `DATABASE_URL` from the process environment, and Mission
# 1.4 added a credential check that takes `FRED_API_KEY` the same way. A
# developer who followed the documented convention got `NOT_CONFIGURED` and no
# indication why, which is the worst answer a governance tool can give -- it
# looks like a policy refusal and is a plumbing gap.
LOCAL_ENV_FILE = pathlib.Path("infrastructure/compose/.env")


def _load_local_env(start: pathlib.Path | None = None) -> pathlib.Path | None:
    """Fold the local `.env` into the process environment. Returns the file read.

    **An explicitly exported variable always wins.** A file left over from last
    month must never be able to override what an operator just set, and a
    verification that silently preferred a stale value would record a
    satisfaction about an environment nobody is running in.

    Values are never printed, and nothing is copied anywhere: the file is
    git-ignored and stays where it is. Absent in CI, where there is only
    `.env.example`, so this changes nothing there.
    """
    current = (start or pathlib.Path.cwd()).resolve()
    path = next(
        (c / LOCAL_ENV_FILE for c in (current, *current.parents) if (c / LOCAL_ENV_FILE).exists()),
        None,
    )
    if path is None:
        return None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip().removeprefix("export ").strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and value and not os.environ.get(name):
            os.environ[name] = value
    return path


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
    config = _compliance(args)
    now = datetime.now(UTC)
    verdicts = {s.source_id: _live_eligibility(s, config, now) for s in catalog}

    if args.json:
        print(
            json.dumps(
                [
                    {
                        **verdicts[source.source_id][0].to_json(),
                        "canonical_name": source.canonical_name,
                        "source_family": source.source_family,
                        "verifications": [r.to_json() for r in verdicts[source.source_id][1]],
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
        result, _ = verdicts[source.source_id]
        state = source.review.approval_state.value if source.review else "NO REVIEW"
        mark = "yes" if result.eligible else "no"
        print(
            f"{source.source_id:<18} {source.source_family:<18} {state:<26} "
            f"{result.evidence_count:>4}  {mark}"
        )
    eligible = sum(1 for result, _ in verdicts.values() if result.eligible)
    print(f"\n{len(catalog)} sources, {eligible} collector-eligible")
    print(
        "This is the LIVE view: conditions verified against this environment. "
        "Nothing is recorded until `sros-source verify --apply`, and eligible is "
        "not enabled -- no collector exists."
    )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    catalog = _catalog(args)
    source = catalog.get(args.source_id)
    review = source.review
    result, records = _live_eligibility(source, _compliance(args))
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

    if records:
        print(f"\n  CONDITION VERIFICATION ({len(records)}, live)")
        for record in records:
            print(f"    {record.condition_key:<28} {record.result.value}")
            print(f"      {record.verifier} v{record.verifier_version}")
            print(f"      {record.reason[:150]}")

    print(f"\n  COLLECTOR ELIGIBLE: {'yes' if result.eligible else 'NO'}")
    for reason in result.blocking_reasons:
        print(f"    - {reason}")
    print("  COLLECTOR ENABLED:  no. No collector exists for any source")
    return 0


def cmd_eligibility(args: argparse.Namespace) -> int:
    catalog = _catalog(args)
    config = _compliance(args)
    sources = [catalog.get(args.source_id)] if args.source_id else list(catalog)
    for source in sources:
        result, records = _live_eligibility(source, config)
        if args.json:
            print(
                json.dumps(
                    {
                        **result.to_json(),
                        "design_eligible": design_eligible(list(records)),
                        "verifications": [r.to_json() for r in records],
                    },
                    indent=2,
                )
            )
            continue
        print(f"{source.source_id}: {'ELIGIBLE' if result.eligible else 'BLOCKED'}")
        for reason in result.blocking_reasons:
            print(f"  - {reason}")
        # §24. A source can be design-complete and still not runnable, and a
        # reader deserves to be told which of the two is missing rather than
        # having to infer it from the blocking reason.
        if records and not result.eligible and design_eligible(list(records)):
            runtime = [r for r in records if r.runtime_dependent and not r.satisfied]
            print(
                "  (design-eligible: every policy capability is in place. What is "
                f"missing is runtime configuration: {', '.join(r.condition_key for r in runtime)})"
            )
    return 0


def cmd_conditions(args: argparse.Namespace) -> int:
    """Every condition on a source's current review, and where it stands.

    Reads the recorded state with `--recorded`, which needs a database. The
    default is the live verification, because the question an operator usually
    has is "would this pass now", not "what did somebody record".
    """
    catalog = _catalog(args)
    source = catalog.get(args.source_id)
    review = source.review
    if review is None or not review.required_conditions:
        print(f"{source.source_id}: the current review declares no condition")
        return 0

    if args.recorded:
        from .compliance.repositories import read_condition_states

        with _connect() as conn:
            states = read_condition_states(conn, source.source_id)
        if args.json:
            print(json.dumps(states, indent=2, default=str))
            return 0
        print(f"{source.source_id}: {len(states)} condition(s), as recorded in the registry")
        for state in states:
            latest = state["latest_verification"]
            mark = "satisfied" if state["satisfied"] else "NOT SATISFIED"
            print(f"\n  {state['condition_key']}  [{state['verification']}]  {mark}")
            print(f"    {state['description']}")
            if latest is None:
                print("    never verified")
            else:
                print(
                    f"    {latest['result']} by {latest['verifier']} "
                    f"v{latest['verifier_version']} at {latest['verified_at']}"
                )
                print(f"    {latest['reason']}")
        return 0

    records = verify_source(source, _compliance(args))
    if args.json:
        print(json.dumps([r.to_json() for r in records], indent=2))
        return 0
    print(f"{source.source_id}: {len(records)} condition(s), verified live")
    by_key = {c.key: c for c in review.required_conditions}
    for record in records:
        condition = by_key[record.condition_key]
        print(f"\n  {record.condition_key}  [{record.verification.value}]  {record.result.value}")
        print(f"    {condition.description}")
        print(f"    verifier: {record.verifier} v{record.verifier_version}")
        print(f"    {record.reason}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Run the verifiers, and with `--apply` record what they found.

    Without `--apply` this writes nothing, which is the default deliberately: a
    verification changes whether a source may be collected from, and that should
    be an act rather than a side effect of asking a question.
    """
    catalog = _catalog(args)
    config = _compliance(args)
    sources = [catalog.get(args.source_id)] if args.source_id else list(catalog)

    records: list[ConditionVerificationRecord] = []
    for source in sources:
        records.extend(verify_source(source, config))

    if not records:
        print("no source in scope declares a review condition; nothing to verify")
        return 0

    for record in records:
        print(
            f"{record.source_id:<14} {record.condition_key:<28} {record.result.value:<15} "
            f"{record.verifier}"
        )
        if not record.satisfied:
            print(f"    {record.reason}")

    satisfied = sum(1 for r in records if r.satisfied)
    print(f"\n{len(records)} condition(s) verified, {satisfied} satisfied")

    if not args.apply:
        print("nothing was recorded. Re-run with --apply to write these results")
        return 0

    from .compliance.repositories import record_verifications

    with _connect() as conn, conn.transaction():
        report = record_verifications(conn, records)
    print(f"recorded: {report.describe()}")
    if report.missing_conditions:
        print(
            "  the following conditions are not in the registry -- run `sros-source load` "
            f"first: {', '.join(report.missing_conditions)}",
            file=sys.stderr,
        )
        return 1
    print("collector_enabled was not changed: enablement is a separate decision")
    return 0


def cmd_authorization(args: argparse.Namespace) -> int:
    """Build the context a collector would receive, or print the refusal.

    Mission 1.4 §27. The refusal is the useful half: it shows that an ineligible
    source produces no authorization at all, rather than an authorization the
    collector is trusted to check.
    """
    catalog = _catalog(args)
    source = catalog.get(args.source_id)
    try:
        context = build_authorization(source, _compliance(args))
    except AcquisitionNotAuthorizedError as exc:
        print(f"REFUSED: no acquisition authorization for {source.source_id}", file=sys.stderr)
        for reason in exc.reasons:
            print(f"  - {reason}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(context.to_json(), indent=2))
        return 0

    print(f"AUTHORIZATION  {context.source_id}  ({context.canonical_name})")
    print(f"  review        v{context.review_version} {context.approval_state.value}")
    print(f"  next review   {context.next_review_at.date()}")
    print("\n  APPROVED ACCESS")
    for access in context.access:
        limit = (
            f"{access.rate_limit.requests}/{access.rate_limit.period_seconds}s "
            f"({access.rate_limit.origin})"
            if access.rate_limit.known
            else "UNKNOWN -- throttle conservatively; no limit is invented"
        )
        print(f"    {access.access_method:<16} {access.label}")
        print(f"      endpoint    {access.endpoint_url or '-'}")
        print(f"      credentials {list(access.credential_references) or '-'}  (key names only)")
        print(f"      rate limit  {limit}")

    scope = context.resource_scope
    print("\n  RESOURCE SCOPE (source approval is not resource approval)")
    print(
        f"    licences        {sorted(scope.licence_allowlist) if scope.licence_allowlist else 'no restriction'}"
    )
    print(
        f"    geographies     {sorted(scope.geography_allowlist) if scope.geography_allowlist else 'no restriction'}"
    )
    print(f"    excluded family {sorted(scope.excluded_dataset_families) or '-'}")
    print(f"    exclusions      {[e.key for e in scope.enumerated_exclusions] or '-'}")
    print(f"    note markers    {list(scope.excluded_note_markers) or '-'}")
    print(f"    third party     {'denied' if scope.third_party_denied else 'permitted'}")

    print("\n  ATTRIBUTION")
    for requirement in context.attribution.requirements:
        origin = "supplied per artefact" if requirement.supplied else f"fixed: {requirement.text!r}"
        when = " (only when modified)" if requirement.when_modified else ""
        print(f"    {requirement.element.value:<24} {origin}{when}")

    print(
        f"\n  RETENTION     raw {context.retention.raw_days}d, "
        f"normalized {context.retention.normalized_days}d ({context.retention.raw_source})"
    )
    print(f"  MINIMISATION  allowed {list(context.data_minimisation.allowed)}")
    print(f"                excluded {list(context.data_minimisation.excluded)}")
    print("\n  No collector exists. This context describes what one would be permitted to do.")
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

    **Two gates, since Mission 1.4.** Eligibility answers *may we*; an
    implemented collector answers *can we*. Two sources now clear the first and
    none clears the second, and switching on a collector that does not exist
    would put the operational flag ahead of the thing it operates -- a state
    that reads, to anyone looking at the registry, as "this is running".
    """
    catalog = _catalog(args)
    source = catalog.get(args.source_id)
    result, _ = _live_eligibility(source, _compliance(args))
    if not result.eligible:
        print(f"REFUSED: {source.source_id} is not collector-eligible", file=sys.stderr)
        for reason in result.blocking_reasons:
            print(f"  - {reason}", file=sys.stderr)
        return 1

    if source.source_id not in IMPLEMENTED_COLLECTORS:
        print(
            f"REFUSED: {source.source_id} passes the governance gate and no collector is "
            "implemented for it",
            file=sys.stderr,
        )
        print(
            "  - collector_enabled is the operational switch for a collector. There is "
            "none to switch on, and setting it would report a source as running",
            file=sys.stderr,
        )
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
    parser.add_argument("--compliance", help="path to source-compliance-v1.json")
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

    conditions = sub.add_parser("conditions", help="each review condition and its verification")
    conditions.add_argument("source_id")
    conditions.add_argument(
        "--recorded",
        action="store_true",
        help="read what the registry recorded instead of verifying now (needs a database)",
    )
    conditions.add_argument("--json", action="store_true")
    conditions.set_defaults(func=cmd_conditions)

    verify = sub.add_parser("verify", help="run the condition verifiers")
    verify.add_argument("source_id", nargs="?")
    verify.add_argument(
        "--apply",
        action="store_true",
        help="record the results in the registry, which is what can change eligibility",
    )
    verify.set_defaults(func=cmd_verify)

    authorization = sub.add_parser(
        "authorization", help="the context a collector would receive, or the refusal"
    )
    authorization.add_argument("source_id")
    authorization.add_argument("--json", action="store_true")
    authorization.set_defaults(func=cmd_authorization)

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
    # Named on stderr, so the provenance of a CONFIGURED answer is visible and
    # `--json` output stays clean. The file name only -- never a variable name,
    # and never a value.
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
