#!/usr/bin/env python3
"""Assert that the Source Registry, applied to a real database, grants nothing
that a verifier did not establish.

Mission 1.0 §43, amended by Mission 1.4 §38.

**What changed, and why the file kept its name.** Mission 1.0 built the gate and
approved nobody, so this script asserted a flat `eligible == 0`. Mission 1.4
implemented the compliance capabilities the Mission 1.3 conditions require, and
two sources now pass the gate legitimately. A script that still failed on that
would be asserting a fact about a moment rather than a property of the system --
and the previous version said as much: *"If a source genuinely passed review,
this script is the wrong place to change: update the catalog, and update this
expectation deliberately."* This is that deliberate update.

What it asserts now is stronger, not weaker. Three things stay absolute:

    enabled  > 0    a collector was switched on. None exists to switch on
    records  > 0    something was collected, which no mission so far permits
    empty registry  every other check would pass while proving nothing

And two are new, because eligibility became reachable:

    a condition marked satisfied with no SATISFIED verification record behind
    it. That is the manual boolean §2 forbids, and the database refuses it too --
    this catches the case where the trigger was dropped

    a source the view calls eligible while one of its conditions is unsatisfied.
    That would mean the view and the condition table disagree

    uv run python infrastructure/scripts/assert_registry_grants_nothing.py
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    import psycopg

    url = os.environ.get("DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros")
    with psycopg.connect(url) as conn:
        registered = conn.execute("SELECT count(*) FROM registry.sources").fetchone()[0]
        enabled = conn.execute(
            "SELECT count(*) FROM registry.sources WHERE collector_enabled"
        ).fetchone()[0]
        collected = conn.execute("SELECT count(*) FROM acquisition.raw_records").fetchone()[0]

        # The view's contract: an empty reason array is the pass. Asked the same
        # way the trigger asks, so this cannot disagree with the database.
        eligible = [
            row[0]
            for row in conn.execute(
                "SELECT source_id FROM registry.source_eligibility "
                "WHERE cardinality(blocking_reasons) = 0 ORDER BY source_id"
            ).fetchall()
        ]

        # A satisfied condition with nothing behind it. Migration 0007 installs a
        # trigger that refuses exactly this, so a row here means the trigger is
        # gone -- which is worth a red build on its own.
        unbacked = [
            f"{row[0]}/{row[1]}"
            for row in conn.execute(
                """SELECT c.source_id, c.condition_key
                     FROM registry.source_review_conditions c
                    WHERE c.satisfied
                      AND NOT EXISTS (
                          SELECT 1 FROM registry.source_condition_verifications v
                           WHERE v.condition_id = c.id AND v.result = 'SATISFIED')
                    ORDER BY 1, 2"""
            ).fetchall()
        ]

        # The view and the condition table have to tell the same story.
        inconsistent = [
            row[0]
            for row in conn.execute(
                """SELECT source_id FROM registry.source_eligibility
                    WHERE cardinality(blocking_reasons) = 0
                      AND unsatisfied_condition_count > 0
                    ORDER BY 1"""
            ).fetchall()
        ]

        satisfied, total_conditions = conn.execute(
            "SELECT count(*) FILTER (WHERE satisfied), count(*) "
            "FROM registry.source_review_conditions"
        ).fetchone()

    failures = []
    if registered == 0:
        failures.append("the registry is empty; the catalog did not load")
    if enabled:
        failures.append(f"{enabled} source(s) have a collector enabled, and none exists to enable")
    if collected:
        failures.append(f"{collected} raw record(s) exist; no mission so far collects anything")
    if unbacked:
        failures.append(
            f"condition(s) marked satisfied with no verification record: {unbacked}. "
            "A condition is cleared by a verifier that says what it checked, never by a "
            "boolean -- and migration 0007 installs a trigger that refuses this, so its "
            "absence means the trigger is gone"
        )
    if inconsistent:
        failures.append(
            f"source(s) the eligibility view clears while a condition is unsatisfied: "
            f"{inconsistent}. The view and the condition table disagree"
        )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(
        f"source registry: {registered} registered, {len(eligible)} eligible "
        f"({', '.join(eligible) or 'none'}), {satisfied}/{total_conditions} conditions "
        f"satisfied and every one of them verified, 0 collectors enabled, 0 raw records"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
