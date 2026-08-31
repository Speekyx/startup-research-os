#!/usr/bin/env python3
"""Did the run change the GLOBAL tables? The half the tenant leak check cannot see.

Mission 1.7 §31 and §32.

WHY THIS EXISTS

`run_pytest_suites.py` snapshots every table carrying a `workspace_id` and fails
the run if the counts moved. `test-data-isolation-audit-v1.md` §6 recorded, as a
named gap rather than a closed one, that this leaves `registry.*` completely
uncovered -- the registry is global platform metadata, so it has no
`workspace_id`, so the catalog query that finds tenant tables cannot find it *by
construction*.

Three acquisition modules mutate `registry.*` today. Each restores what it found
by convention, and nothing enforced it. One of them turns a collector on:

    UPDATE registry.sources SET collector_enabled = TRUE WHERE id = 'world-bank'

A restore that silently failed would leave a collector enabled -- the one switch
`source-registry-v1.md` §4 arranges three separate mechanisms to keep behind the
eligibility gate.

The tenant check would report nothing. It still would: the row count of
`registry.sources` does not move when a boolean flips inside it.

WHAT IS COMPARED, AND WHAT IS DELIBERATELY NOT

**Content, not counts.** The failure above is count-stable, so counting cannot
find it. Each row is reduced to `to_jsonb(row)` minus its bookkeeping timestamps
and hashed; a table is the set of those hashes.

**`created_at` and `updated_at` are excluded.** `load_catalog_into` upserts with
`updated_at = now()`, and the suites' own session fixture calls it. Including
them would make this check fail on every run -- and a check that always fails is
a check somebody deletes.

**The verification log is append-only, by design.** `record_verifications`
derives its primary key with `uuid5` over a tuple that includes `verified_at`,
so a re-run adds a row rather than rewriting an answer, and that history is part
of what makes a condition's current state trustworthy
(`acquisition-authorization-v1.md`). It is the one table allowed to GROW. It is
not allowed to shrink, and its existing rows are not allowed to change -- both
of which one subset test catches.

**Two columns of `source_review_conditions` are a projection of that log.**
`satisfied_at` and `satisfaction_reference` name the verification that cleared
the condition, so they move to the newest one every time the log grows -- which
is every suite run. The first real run of this check reported eight conditions
"changed" for exactly that reason, with `satisfied` identical in all eight. They
are excluded and `satisfied` is not: the boolean is the governance fact, and a
suite that clears or un-clears a condition is still caught.

**An empty table that becomes populated is a load, not a leak.** CI runs the
suites BEFORE `sros-source load` (`.github/workflows/ci.yml`), so on a fresh
database the registry is empty at snapshot time and the suites' `registry_loaded`
fixture is what fills it. This is safe by construction rather than by
convention: nothing can be lost from a table that had nothing in it.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "APPEND_ONLY",
    "GLOBAL_SCHEMAS",
    "Difference",
    "compare",
    "format_report",
    "global_tables",
    "snapshot",
]

# The schemas the application owns. Same list as the tenant check, so a global
# table added to any of them is watched from the moment it exists rather than
# from the moment somebody remembers this file.
GLOBAL_SCHEMAS = (
    "core",
    "registry",
    "research",
    "acquisition",
    "nlp",
    "scoring",
    # Added in Mission 1.14. `epistemic` holds reviewed reliability
    # assessments, which are global and administered through a review path --
    # never by a service and never by a suite. An assessment appearing during a
    # test run is exactly the failure `testing-strategy.md` §32 describes: a
    # fixture becoming a fact.
    "epistemic",
)

# Tables whose rows accumulate as a matter of design. NAMED rather than derived:
# append-only-ness is a property of what writes the table, and a rule inferred
# from the schema would be guessing. An error here in the permissive direction
# hides a leak, so the set stays small and each entry says why.
APPEND_ONLY = {
    # `record_verifications` writes one row per verifier run, keyed by uuid5
    # over (condition, verifier, version, verified_at). The session fixture
    # verifies every source, so this grows once per suite invocation.
    "registry.source_condition_verifications",
}

# Columns excluded from the row digest, and why. Two classes, both of them
# things that move without any governance fact having changed:
#
#   created_at / updated_at        row bookkeeping. `load_catalog_into` upserts
#                                  with `updated_at = now()` on every load.
#   satisfied_at                   on `source_review_conditions`: a projection
#   satisfaction_reference         of the append-only verification log, pointed
#                                  at whichever verification most recently
#                                  cleared the condition. `satisfied` -- the
#                                  governance fact -- is NOT excluded.
#
# `to_jsonb(x) - 'c'` is a no-op on a table with no column `c`, so one list
# serves every table.
IGNORED_COLUMNS = ("created_at", "updated_at", "satisfied_at", "satisfaction_reference")

# table -> {row_digest: row_text}
Snapshot = dict[str, dict[str, str]]


@dataclass(frozen=True)
class Difference:
    """One table that did not come back the way it went in."""

    table: str
    removed: tuple[str, ...]
    added: tuple[str, ...]

    @property
    def append_only(self) -> bool:
        return self.table in APPEND_ONLY

    @property
    def is_leak(self) -> bool:
        """Whether this difference is a failure rather than expected growth.

        For an append-only table only a removal is a leak: a row that vanished
        or was rewritten. Rows arriving there is the table working.
        """
        if self.append_only:
            return bool(self.removed)
        return bool(self.removed or self.added)


def global_tables(conn: object) -> list[str]:
    """Every base table in the owned schemas that carries NO `workspace_id`.

    The complement of `run_pytest_suites._tenant_tables`, so between the two
    every application table is watched by exactly one of them and neither has a
    list to maintain.
    """
    rows = conn.execute(  # type: ignore[attr-defined]
        """SELECT n.nspname || '.' || c.relname
             FROM pg_class c
             JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'r'
              AND n.nspname = ANY(%s)
              AND NOT EXISTS (
                    SELECT 1 FROM pg_attribute a
                     WHERE a.attrelid = c.oid
                       AND a.attname = 'workspace_id'
                       AND NOT a.attisdropped)
            ORDER BY 1""",
        (list(GLOBAL_SCHEMAS),),
    ).fetchall()
    return [r[0] for r in rows]


def snapshot(conn: object, tables: list[str]) -> Snapshot:
    """Each table as a set of row digests, with the row text kept for the report.

    `to_jsonb` normalises key order, so the text is stable across runs and
    across servers. These tables are small -- tens of rows -- so keeping the text
    costs nothing and means a failure prints the row that moved instead of a
    hash nobody can look up.
    """
    ignored = " ".join(f"- '{column}'" for column in IGNORED_COLUMNS)
    out: Snapshot = {}
    for table in tables:
        # `table` comes from the system catalog, never from input, and an
        # identifier cannot be parameterised in SQL.
        inner = f"SELECT (to_jsonb(x) {ignored})::text AS rt FROM {table} x"  # noqa: S608
        sql = f"SELECT md5(t.rt), t.rt FROM ({inner}) t"  # noqa: S608
        rows = conn.execute(sql).fetchall()  # type: ignore[attr-defined]
        out[table] = {digest: text for digest, text in rows}
    return out


def compare(before: Snapshot, after: Snapshot) -> list[Difference]:
    """Every table whose contents moved, in either direction."""
    differences: list[Difference] = []
    for table in sorted(set(before) | set(after)):
        was, now = before.get(table, {}), after.get(table, {})
        # A table that was empty cannot have lost anything, so filling it is a
        # load. Skipping it here rather than at the report keeps `is_leak`
        # honest for every caller.
        if not was:
            continue
        removed = tuple(sorted(was[d] for d in set(was) - set(now)))
        added = tuple(sorted(now[d] for d in set(now) - set(was)))
        if removed or added:
            differences.append(Difference(table=table, removed=removed, added=added))
    return differences


def _abbreviate(row: str, width: int = 160) -> str:
    return row if len(row) <= width else row[: width - 1] + "..."


def format_report(tables: list[str], differences: list[Difference]) -> tuple[bool, str]:
    """`(clean, text)`. Clean means no difference was a leak."""
    if not tables:
        return False, "NO GLOBAL TABLES FOUND: the catalog query is wrong, nothing was checked"

    leaks = [d for d in differences if d.is_leak]
    growth = [d for d in differences if not d.is_leak]

    if not leaks:
        note = ""
        if growth:
            appended = sum(len(d.added) for d in growth)
            note = f"; {appended} appended to {len(growth)} append-only table(s)"
        return True, f"global tables unchanged by the run, across {len(tables)} tables{note}"

    lines = [
        f"\nTHE RUN CHANGED GLOBAL STATE: {len(leaks)} table(s)",
        "registry.* is platform metadata with no workspace_id, so the tenant",
        "leak check cannot see it. A suite that mutates a global table must",
        "restore what it FOUND -- not a default, and not what it assumed.\n",
    ]
    for diff in leaks:
        lines.append(f"  {diff.table}  -{len(diff.removed)} +{len(diff.added)}")
        for row in diff.removed:
            lines.append(f"    GONE    {_abbreviate(row)}")
        for row in diff.added:
            lines.append(f"    LEFT    {_abbreviate(row)}")
    return False, "\n".join(lines)
