#!/usr/bin/env python3
"""Mechanically enforce the ADR-008 schema invariants.

Runs without a database. It parses the migration SQL and fails when an
architectural invariant is violated, so the rules live in CI rather than in
someone's memory of a review.

Checked:
  1. Migration files are numbered, ordered and gap-free.
  2. Every tenant-scoped table carries workspace_id UUID NOT NULL.
  3. Every tenant-scoped table has an index leading with workspace_id.
  4. No PostgreSQL ENUM type is created (Ontology V2 §14.3).
  5. No forbidden evidence-aggregation column exists (D-03 blocked).
  6. Retention-governed tables carry collected_at and expires_at NOT NULL.
  7. Closed-enum columns are constrained by CHECK, and their value sets match
     the contract source of truth.
  8. No `confidence`-named column escapes a unit-interval CHECK, and no
     `*_score` column escapes a 0-100 CHECK.

Stdlib only. Usage: python infrastructure/scripts/validate_schema.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "infrastructure" / "db" / "migrations"
CONTRACT_SOURCE = ROOT / "packages" / "contracts" / "schema" / "domain.v1.json"
CONFORMANCE = ROOT / "packages" / "contracts" / "conformance" / "cases.json"

# Global reference data is deliberately NOT tenant-scoped (ADR-008).
GLOBAL_TABLES = {
    "core.schema_migrations",
    "core.users",
    "core.workspaces",
    "core.workspace_memberships",  # composite PK already leads with workspace_id
    "registry.registry_entries",
    # The source registry is global on purpose (ADR-012 §4, Mission 1.0 §24).
    # A source review that differed per workspace would make provenance
    # incomparable across workspaces, and every tenant would have to
    # re-establish that the same platform's terms say the same thing. Future
    # per-workspace source CONFIGURATION -- credentials, quotas, an
    # organisation's own account -- is a separate tenant-scoped table and is not
    # part of source identity.
    "registry.sources",
    "registry.source_access_profiles",
    "registry.source_policy_reviews",
    "registry.source_policy_evidence",
    "registry.source_retention_policies",
    "registry.source_capabilities",
    # Added in Mission 1.3. Conditions belong to a source review, and source
    # reviews are global platform metadata: a condition assessed differently
    # per workspace would make one review mean two things.
    "registry.source_review_conditions",
    # Added in Mission 1.4. A verification is a statement about a global
    # condition, made by a program, about a deployment. Nothing about it is
    # tenant-scoped, and a per-workspace verification would mean one review
    # condition held in one workspace and not in another.
    "registry.source_condition_verifications",
    # Added in Mission 1.7 (ADR-017). Coverage describes a PLATFORM, not a
    # tenant. A source that exposed entertainment signals in one workspace and
    # not in another would make provenance incomparable across workspaces --
    # the same argument that makes every table above global.
    "registry.source_signal_coverage",
    "registry.source_behavior_coverage",
    # Added in Mission 1.14 (ADR-026 Decision 3). An assessment is a statement
    # about a PUBLISHED DATASET's measurement contract, evidenced by the
    # publisher's own documentation -- not a statement about a tenant. Making it
    # tenant-scoped would mean every workspace re-reviewing the same
    # methodology, producing several answers to one question with nothing to say
    # which is right. Deliberately a separate SCHEMA from `registry`: legal
    # permission and measurement quality are different concerns, and no formula
    # converts one into the other.
    "epistemic.reliability_assessments",
    "epistemic.reliability_assessment_basis",
}

# Tables governed by data-retention-policy-v1.md, each with the column its
# retention clock STARTS from.
#
# Not always `collected_at`. A Signal is not collected: its inputs were, at
# various times, from possibly several sources, so a single collection time on
# the derived row has no referent (Mission 1.11, GAP-15). Assuming one column
# name for every table would have this check verifying a column that no longer
# exists, which passes and measures nothing.
RETENTION_TABLES = {
    "acquisition.raw_records": "collected_at",
    "acquisition.normalized_records": "collected_at",
    "nlp.signals": "derived_at",
    "scoring.evidence": "collected_at",
}

CREATE_TABLE = re.compile(
    r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+([a-z_]+\.[a-z_]+)\s*\((.*?)\n\);",
    re.DOTALL | re.IGNORECASE,
)
CREATE_INDEX = re.compile(
    r"CREATE(?:\s+UNIQUE)?\s+INDEX\s+\S+\s+ON\s+([a-z_]+\.[a-z_]+)\s*"
    r"(?:USING\s+\w+\s*)?\(\s*([a-z_]+)",
    re.IGNORECASE,
)
# A column or a CHECK introduced by a later ALTER belongs to the table it
# alters. Without folding these in, a closed enum added by a forward migration
# would go unverified against the contract -- which is the one drift this check
# exists to catch.
ALTER_TABLE = re.compile(r"ALTER TABLE\s+([a-z_]+\.[a-z_]+)(.*?);", re.DOTALL | re.IGNORECASE)

# A column renamed by a later migration keeps its ORIGINAL name in the CREATE
# TABLE text this script reads, so every check below would go on asserting about
# a name the database no longer has -- and pass, while measuring nothing. Applied
# to the folded body so `derived_at TIMESTAMPTZ NOT NULL` is found where
# migration 0001 wrote `collected_at` and migration 0012 renamed it.
RENAME_COLUMN = re.compile(r"RENAME\s+COLUMN\s+([a-z_]+)\s+TO\s+([a-z_]+)", re.IGNORECASE)

# A constraint dropped by a later migration is still in the CREATE TABLE text.
# Left in, it is compared against the contract alongside the constraint that
# REPLACED it -- so a value set that was deliberately changed reads as drift.
# Both live cases pair a drop with a rename (`sources.status` -> `lifecycle` in
# 0004, `signals.signal_family` -> `quantity_family` in 0012), which is exactly
# when the old definition is most misleading.
DROP_CONSTRAINT = re.compile(r"DROP\s+CONSTRAINT\s+([a-z_]+)", re.IGNORECASE)


def strip_constraint(body: str, name: str) -> str:
    """The table body without the named constraint's earliest DEFINITION.

    Scans forward from the definition tracking parenthesis depth, so a comma
    inside `CHECK (x IN ('a', 'b'))` does not end it early.

    A `DROP CONSTRAINT <name>` statement mentions the name too, and skipping
    those is load-bearing rather than tidy. With one drop it did not matter;
    Mission 1.12.1 added a second migration that drops and re-adds the same
    constraint, and stripping a DROP's text instead of the older definition left
    a SUPERSEDED value set in the body -- which then failed against the contract
    as drift that did not exist.
    """
    match = next(
        (
            m
            for m in re.finditer(rf"CONSTRAINT\s+{re.escape(name)}\b", body, re.IGNORECASE)
            if not re.search(r"DROP\s+$", body[max(0, m.start() - 8) : m.start()], re.IGNORECASE)
        ),
        None,
    )
    if match is None:
        return body
    start, depth, index = match.start(), 0, match.end()
    while index < len(body):
        char = body[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            index += 1
            break
        index += 1
    return body[:start] + body[index:]


# Every `INSERT INTO registry.registry_entries (cols) VALUES (...), (...);`
# with its column list, so values can be read BY COLUMN NAME rather than by
# position. A looser regex over the whole file matches quoted pairs inside CHECK
# constraints and enum lists and reports them as registry entries, which is how
# the first version of this check failed on its own baseline.
REGISTRY_ENTRY_INSERT = re.compile(
    r"INSERT\s+INTO\s+registry\.registry_entries\s*\(([^)]*)\)\s*VALUES(.*?);",
    re.DOTALL | re.IGNORECASE,
)


def _tuples(body: str) -> list[list[str]]:
    """Split a VALUES body into rows of raw column values.

    Hand-rolled because the alternative is a SQL parser for four INSERTs.
    Tracks quote state so a comma or parenthesis inside a description -- and
    there are several -- does not split a row.
    """
    rows: list[list[str]] = []
    current: list[str] = []
    field: list[str] = []
    depth, in_quote = 0, False
    for index, char in enumerate(body):
        if in_quote:
            field.append(char)
            # '' is an escaped quote inside a SQL string, not the end of one.
            if char == "'" and body[index + 1 : index + 2] != "'":
                in_quote = False
            continue
        if char == "'":
            in_quote = True
            field.append(char)
        elif char == "(":
            depth += 1
            if depth == 1:
                current, field = [], []
            else:
                field.append(char)
        elif char == ")" and depth == 1:
            depth = 0
            current.append("".join(field).strip())
            rows.append(current)
            current, field = [], []
        elif char == "," and depth == 1:
            current.append("".join(field).strip())
            field = []
        elif depth == 1:
            field.append(char)
    return rows


def registry_entries_in(sql: str) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """`(entries inserted, maps_to targets referenced)` across every migration.

    Read BY COLUMN NAME, so a future INSERT that lists its columns in another
    order is still understood.
    """
    inserted: set[tuple[str, str]] = set()
    targets: set[tuple[str, str]] = set()
    for columns, body in REGISTRY_ENTRY_INSERT.findall(sql):
        names = [c.strip().lower() for c in columns.split(",")]
        try:
            key = (names.index("registry"), names.index("id"))
        except ValueError:
            continue
        maps = (
            (names.index("maps_to_registry"), names.index("maps_to_id"))
            if "maps_to_registry" in names and "maps_to_id" in names
            else None
        )
        for row in _tuples(body):
            if len(row) != len(names):
                continue
            unquote = lambda v: v.strip().strip("'").lower()  # noqa: E731
            inserted.add((unquote(row[key[0]]), unquote(row[key[1]])))
            if maps and row[maps[0]].strip().upper() != "NULL":
                targets.add((unquote(row[maps[0]]), unquote(row[maps[1]])))
    return inserted, targets


class MigrationLayoutError(Exception):
    pass


def load_migrations() -> list[tuple[str, str]]:
    files = sorted(MIGRATIONS.glob("*.sql"))
    if not files:
        raise MigrationLayoutError(f"no migrations found in {MIGRATIONS}")
    out = []
    for index, path in enumerate(files, start=1):
        prefix = path.name.split("_", 1)[0]
        if not prefix.isdigit():
            raise MigrationLayoutError(f"{path.name}: migrations must start with a numeric version")
        if int(prefix) != index:
            raise MigrationLayoutError(
                f"{path.name}: expected version {index:04d}, got {prefix}. "
                "Migration versions must be contiguous and forward-only."
            )
        out.append((path.name, path.read_text(encoding="utf-8")))
    return out


def main() -> int:
    errors: list[str] = []
    checks_run = 0

    try:
        migrations = load_migrations()
    except MigrationLayoutError as exc:
        print(f"FAIL  migration ordering: {exc}")
        return 1
    print(f"ok    migration ordering ({len(migrations)} file(s), contiguous, forward-only)")
    checks_run += 1

    sql = "\n".join(body for _, body in migrations)
    tables = {name.lower(): body for name, body in CREATE_TABLE.findall(sql)}
    if not tables:
        print("FAIL  no CREATE TABLE statements parsed")
        return 1

    renames: dict[str, list[tuple[str, str]]] = {}
    dropped: dict[str, list[str]] = {}
    for table, altered in ALTER_TABLE.findall(sql):
        key = table.lower()
        if key in tables:
            tables[key] = tables[key] + "\n" + altered
            renames.setdefault(key, []).extend(RENAME_COLUMN.findall(altered))
            dropped.setdefault(key, []).extend(DROP_CONSTRAINT.findall(altered))

    # Drops first: a dropped constraint must not be renamed into looking current.
    for key, names in dropped.items():
        for name in names:
            tables[key] = strip_constraint(tables[key], name)
    # In migration order, so a column renamed twice ends on its current name.
    for key, pairs in renames.items():
        for old, new in pairs:
            tables[key] = re.sub(rf"\b{re.escape(old)}\b", new, tables[key])

    leading_index_cols: dict[str, set[str]] = {}
    for table, first_col in CREATE_INDEX.findall(sql):
        leading_index_cols.setdefault(table.lower(), set()).add(first_col.lower())

    # -- 2 & 3: tenancy -----------------------------------------------------
    tenant_tables = [t for t in sorted(tables) if t not in GLOBAL_TABLES]
    for table in tenant_tables:
        body = tables[table]
        if not re.search(r"workspace_id\s+UUID\s+NOT NULL", body, re.IGNORECASE):
            errors.append(
                f"{table}: tenant-scoped table must declare `workspace_id UUID NOT NULL` (ADR-005)"
            )
        pk_leads = re.search(r"PRIMARY KEY \(\s*workspace_id", body, re.IGNORECASE)
        if not pk_leads and "workspace_id" not in leading_index_cols.get(table, set()):
            errors.append(
                f"{table}: needs an index leading with workspace_id "
                "(ADR-008; retrofitting index order later is expensive)"
            )
    print(f"ok    tenancy columns and index order ({len(tenant_tables)} tenant-scoped tables)")
    checks_run += 2

    # -- 4: no ENUM types ---------------------------------------------------
    enum_types = re.findall(r"CREATE TYPE\s+\S+\s+AS ENUM", sql, re.IGNORECASE)
    if enum_types:
        errors.append(
            f"{len(enum_types)} PostgreSQL ENUM type(s) created. Evolving taxonomies are "
            "registry rows (Ontology V2 §14.3); closed types use TEXT + CHECK (ADR-008)."
        )
    else:
        print("ok    no PostgreSQL ENUM types (taxonomies stay migration-free)")
    checks_run += 1

    # -- 5: D-03 leakage ----------------------------------------------------
    forbidden = json.loads(CONFORMANCE.read_text(encoding="utf-8"))["forbidden_fields"]["names"]
    leaked = [name for name in forbidden if re.search(rf"\b{name}\b", sql, re.IGNORECASE)]
    if leaked:
        errors.append(
            f"evidence-aggregation leakage: {leaked}. D-03 is unresolved; no schema may "
            "assume an aggregation formula (scoring-framework-v1.1.md §13)."
        )
    else:
        print(
            f"ok    no evidence-aggregation columns (D-03 stays blocked, {len(forbidden)} names checked)"
        )
    checks_run += 1

    # -- 6: retention fields ------------------------------------------------
    for table, start_column in sorted(RETENTION_TABLES.items()):
        body = tables.get(table)
        if body is None:
            errors.append(f"{table}: retention-governed table is missing from the schema")
            continue
        for column in (start_column, "expires_at"):
            if not re.search(rf"{column}\s+TIMESTAMPTZ\s+NOT NULL", body, re.IGNORECASE):
                errors.append(
                    f"{table}: retention-governed table must declare "
                    f"`{column} TIMESTAMPTZ NOT NULL` (data-retention-policy-v1.md §6)"
                )
    print(f"ok    retention fields ({len(RETENTION_TABLES)} retention-governed tables)")
    checks_run += 1

    # -- 7: closed enums match the contract ---------------------------------
    contract = json.loads(CONTRACT_SOURCE.read_text(encoding="utf-8"))
    enums = {e["name"]: [v["value"] for v in e["values"]] for e in contract["closed_enums"]}

    # Scoped per table: a column called `status` means different closed enums on
    # different tables, so a name-only match would compare unrelated value sets.
    enum_sites = [
        ("ClaimType", "research.opportunity_session_observations", "claim_type"),
        # scoring.evidence.claim_type was DROPPED in Mission 1.13: it predates
        # claim_id, duplicated the claim's own type, and the aggregation
        # framework reads neither. The site on
        # research.opportunity_session_observations stays.
        ("ResearchSessionStatus", "research.research_sessions", "status"),
        ("RegistryStatus", "registry.registry_entries", "status"),
        # Source Registry (Mission 1.0). A value that drifted from the contract
        # here would let a source of unknown standing read as reviewed.
        ("SourceLifecycle", "registry.sources", "lifecycle"),
        ("SourceApprovalState", "registry.source_policy_reviews", "approval_state"),
        ("PersonalDataRisk", "registry.source_policy_reviews", "personal_data_risk"),
        ("PolicyAssessment", "registry.source_policy_reviews", "automated_access"),
        ("SourceAccessMethod", "registry.source_access_profiles", "access_method"),
        ("SourceAcquisitionCost", "registry.source_access_profiles", "acquisition_cost"),
        ("PolicyEvidenceType", "registry.source_policy_evidence", "document_type"),
        # Mission 1.3 and 1.4. These two carry the gate between an approving
        # review and a collector, so a value drifting from the contract here
        # would let a condition be recorded as checked in a way nothing reads.
        ("ConditionVerification", "registry.source_review_conditions", "verification"),
        (
            "ConditionVerificationResult",
            "registry.source_condition_verifications",
            "result",
        ),
        # Mission 1.6. The quality state is what a downstream stage filters on
        # before reading a normalized record as an observation, so a value
        # drifting from the contract here would let a record that could not be
        # represented read as one that could.
        (
            "NormalizedRecordQuality",
            "acquisition.normalized_records",
            "quality",
        ),
        # Mission 1.11. Every one of these decides how a derived signal is READ:
        # a family says what kind of quantity it is about, a direction asserts
        # change, a magnitude kind says whether 2 means a difference or a ratio,
        # and a temporal basis decides whether the row may carry an event time at
        # all. A value drifting from the contract here would let a signal be read
        # as something it is not.
        ("SignalQuantityFamily", "nlp.signals", "quantity_family"),
        ("SignalDirection", "nlp.signals", "direction"),
        ("SignalMagnitudeKind", "nlp.signals", "magnitude_kind"),
        ("SignalMagnitudeUnitState", "nlp.signals", "magnitude_unit_state"),
        ("SignalTemporalBasis", "nlp.signals", "temporal_basis"),
        ("SignalDerivationKind", "nlp.signals", "derivation_kind"),
        ("SignalInputRole", "nlp.signal_inputs", "role"),
        ("SignalRefusalReason", "nlp.signal_inputs", "refusal_reason"),
        ("NormalizedRecordQuality", "nlp.signal_inputs", "input_quality"),
        # Mission 1.14. The origin vocabulary is the one that matters most: it is
        # closed precisely so there is nowhere to record a model's guess, and a
        # value drifting from the contract here would reopen the hole the closure
        # exists to shut (evidence-reliability-contract-v1.md §5).
        ("ReliabilityAssessmentOrigin", "epistemic.reliability_assessments", "origin"),
        ("ClaimType", "epistemic.reliability_assessments", "claim_type"),
        (
            "ReliabilityBasisType",
            "epistemic.reliability_assessment_basis",
            "basis_type",
        ),
    ]
    for enum_name, table, column in enum_sites:
        expected = set(enums[enum_name])
        body = tables.get(table)
        if body is None:
            errors.append(f"{table}: expected table is missing from the schema")
            continue
        # `\s+` around IN rather than a single space: columns are aligned in the
        # migrations, and a validator that fails on whitespace teaches people to
        # format around the checker instead of reading it.
        checks = re.findall(
            rf"CHECK \(\s*{column}\s+IN\s*\(([^)]*)\)", body, re.IGNORECASE | re.DOTALL
        )
        if not checks:
            errors.append(
                f"{table}.{column}: no CHECK constraint found for closed enum {enum_name}"
            )
            continue
        for check in checks:
            values = set(re.findall(r"'([A-Z_]+)'", check))
            if values != expected:
                errors.append(
                    f"{table}.{column}: CHECK values {sorted(values)} do not match "
                    f"{enum_name} {sorted(expected)} from the contract source of truth"
                )
    print("ok    closed-enum CHECK constraints match the contract source of truth")
    checks_run += 1

    # -- 8: numeric naming rule --------------------------------------------
    for table, body in tables.items():
        for column in re.findall(
            r"^\s+(\w*confidence)\s+DOUBLE PRECISION", body, re.MULTILINE | re.IGNORECASE
        ):
            if not re.search(rf"{column} BETWEEN 0 AND 1", body, re.IGNORECASE):
                errors.append(
                    f"{table}.{column}: a `confidence` column must carry a "
                    "BETWEEN 0 AND 1 CHECK (scoring-framework-v1.1.md §4.1)"
                )
        for column in re.findall(r"^\s+(\w+_score)\s+INTEGER", body, re.MULTILINE | re.IGNORECASE):
            if not re.search(rf"{column} BETWEEN 0 AND 100", body, re.IGNORECASE):
                errors.append(
                    f"{table}.{column}: a `*_score` column must carry a "
                    "BETWEEN 0 AND 100 CHECK (scoring-framework-v1.1.md §4.1)"
                )
    print("ok    numeric naming rule (confidence [0,1] vs *_score 0-100)")
    checks_run += 1

    # -- migrations must not depend on seed data ------------------------------
    #
    # Seeds are development-only and run AFTER every migration
    # (`infrastructure/db/seed/`). A migration whose foreign key resolves only
    # because a seed had run is correct on a developer's machine -- where the
    # rows are already there from an earlier run -- and fails on the empty
    # database CI and every real deployment start from.
    #
    # Mission 1.7 shipped exactly that: migration 0010 pointed `signal_family`
    # entries at `user_motivation:problem`, which only
    # `seed/0002_registry_seed.sql` wrote. It applied cleanly on a machine that
    # had been seeded months earlier and failed on the first empty database it
    # met. This check runs with no database, so it fails where it is caused.
    inserted, targets = registry_entries_in(sql)
    if not inserted:
        errors.append("no registry_entries INSERT parsed: this check measured nothing")
    unmet = sorted(t for t in targets if t not in inserted)
    for registry, entry_id in unmet:
        errors.append(
            f"a migration maps a registry entry to {registry}:{entry_id}, which no migration "
            "inserts. If a seed provides it, the foreign key resolves only on an "
            "already-seeded database and fails on the empty one CI starts from"
        )
    if not unmet and inserted:
        print(
            "ok    migrations do not depend on seed data "
            f"({len(inserted)} entries inserted, {len(targets)} mapped)"
        )
    checks_run += 1

    print()
    if errors:
        print(f"SCHEMA VALIDATION FAILED ({len(errors)} problem(s)):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"schema validation passed: {checks_run} invariant groups, {len(tables)} tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
