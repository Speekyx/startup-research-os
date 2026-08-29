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
}

# Tables governed by data-retention-policy-v1.md.
RETENTION_TABLES = {
    "acquisition.raw_records",
    "acquisition.normalized_records",
    "nlp.signals",
    "scoring.evidence",
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

    for table, altered in ALTER_TABLE.findall(sql):
        key = table.lower()
        if key in tables:
            tables[key] = tables[key] + "\n" + altered

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
    for table in sorted(RETENTION_TABLES):
        body = tables.get(table)
        if body is None:
            errors.append(f"{table}: retention-governed table is missing from the schema")
            continue
        for column in ("collected_at", "expires_at"):
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
        ("ClaimType", "scoring.evidence", "claim_type"),
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
