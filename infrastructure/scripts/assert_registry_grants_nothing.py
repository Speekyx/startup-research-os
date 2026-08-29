#!/usr/bin/env python3
"""Assert that nothing was granted, enabled or collected that a gate did not clear.

Mission 1.0 §43, amended by Mission 1.4 §38 and Mission 1.5 §53.

**The file keeps its name, and its assertions have changed twice.** Both times
the previous version said what to do, and both times the change was a narrowing
rather than a relaxation:

    Mission 1.0   nothing is eligible, enabled or collected. True while no
                  source had passed a review
    Mission 1.4   two sources became eligible, so `eligible == 0` stopped being
                  a property. Replaced by: no condition is satisfied without a
                  verification record behind it
    Mission 1.5   one collector exists and one source was collected from, so
                  `enabled == 0` and `records == 0` stopped being properties too

What survives every version is the ORDERING, which is the thing that actually
protects anything:

    a condition is satisfied  only if a verifier said so
    a source is enabled       only if a collector exists for it
    a record exists           only for a source that has a collector

Each of those holds whether the deployment has collected anything or not, which
is what makes them properties rather than statements about one morning.

    uv run python infrastructure/scripts/assert_registry_grants_nothing.py
"""

from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in (
    ROOT / "packages" / "contracts" / "python",
    ROOT / "services" / "acquisition" / "python",
):
    if str(package) not in sys.path:
        sys.path.insert(0, str(package))

from sros_acquisition import IMPLEMENTED_COLLECTORS  # noqa: E402


def main() -> int:
    import psycopg

    url = os.environ.get("DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros")
    with psycopg.connect(url) as conn:
        registered = conn.execute("SELECT count(*) FROM registry.sources").fetchone()[0]

        eligible = [
            row[0]
            for row in conn.execute(
                "SELECT source_id FROM registry.source_eligibility "
                "WHERE cardinality(blocking_reasons) = 0 ORDER BY source_id"
            ).fetchall()
        ]
        enabled = {
            row[0]
            for row in conn.execute(
                "SELECT id FROM registry.sources WHERE collector_enabled"
            ).fetchall()
        }
        collected = {
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT source_id FROM acquisition.raw_records"
            ).fetchall()
        }
        records = conn.execute("SELECT count(*) FROM acquisition.raw_records").fetchone()[0]
        normalized = conn.execute("SELECT count(*) FROM acquisition.normalized_records").fetchone()[
            0
        ]

        # A satisfied condition with nothing behind it. Migration 0007 installs
        # a trigger that refuses exactly this, so a row here means the trigger
        # is gone -- which is worth a red build on its own.
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
    if unbacked:
        failures.append(
            f"condition(s) marked satisfied with no verification record: {unbacked}. "
            "A condition is cleared by a verifier that says what it checked, never by a "
            "boolean -- and migration 0007 refuses this, so its absence means the trigger "
            "is gone"
        )
    if inconsistent:
        failures.append(
            f"source(s) the eligibility view clears while a condition is unsatisfied: "
            f"{inconsistent}. The view and the condition table disagree"
        )
    if enabled - IMPLEMENTED_COLLECTORS:
        failures.append(
            f"source(s) enabled with no collector behind them: "
            f"{sorted(enabled - IMPLEMENTED_COLLECTORS)}. The operational switch must not "
            "get ahead of the thing it switches"
        )
    if collected - IMPLEMENTED_COLLECTORS:
        failures.append(
            f"raw records exist for source(s) this codebase cannot collect from: "
            f"{sorted(collected - IMPLEMENTED_COLLECTORS)}"
        )
    if normalized:
        failures.append(
            f"{normalized} normalized record(s) exist; normalization is Mission 1.6's and "
            "nothing should produce one yet"
        )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(
        f"source registry: {registered} registered, {len(eligible)} eligible "
        f"({', '.join(eligible) or 'none'}), {satisfied}/{total_conditions} conditions "
        f"satisfied and every one of them verified"
    )
    print(
        f"collection: {sorted(IMPLEMENTED_COLLECTORS) or 'no'} collector(s) implemented, "
        f"{sorted(enabled) or 'none'} enabled, {records} raw record(s) from "
        f"{sorted(collected) or 'no source'}, {normalized} normalized"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
