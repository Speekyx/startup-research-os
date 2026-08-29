#!/usr/bin/env python3
"""Assert that the Source Registry, applied to a real database, grants nothing.

Mission 1.0 §43. Resolving D-07 built the mechanism; it approved no source. This
script is what makes that a build failure rather than a claim: if a source
quietly became collector-eligible, or a collector was enabled, or a raw record
appeared, CI goes red.

It deliberately checks three separate things rather than one, because they fail
for different reasons:

    eligible > 0    a review passed the gate that should not have
    enabled  > 0    a collector was switched on
    records  > 0    something was collected, which this mission forbids outright

A script, not an inline heredoc in the workflow: a check nobody can run locally
is a check nobody debugs.

    uv run python infrastructure/scripts/assert_registry_grants_nothing.py
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    import psycopg

    url = os.environ.get("DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros")
    with psycopg.connect(url) as conn:
        enabled = conn.execute(
            "SELECT count(*) FROM registry.sources WHERE collector_enabled"
        ).fetchone()[0]
        # The view's contract: an empty reason array is the pass. Asked the same
        # way the trigger asks, so this cannot disagree with the database.
        eligible = conn.execute(
            "SELECT count(*) FROM registry.source_eligibility "
            "WHERE cardinality(blocking_reasons) = 0"
        ).fetchone()[0]
        collected = conn.execute("SELECT count(*) FROM acquisition.raw_records").fetchone()[0]
        registered = conn.execute("SELECT count(*) FROM registry.sources").fetchone()[0]

    failures = []
    if registered == 0:
        # An empty registry would pass every check below while proving nothing.
        failures.append("the registry is empty; the catalog did not load")
    if enabled:
        failures.append(f"{enabled} source(s) have a collector enabled")
    if eligible:
        failures.append(f"{eligible} source(s) passed the eligibility gate")
    if collected:
        failures.append(f"{collected} raw record(s) exist; this mission collects nothing")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        print(
            "\nIf a source genuinely passed review, this script is the wrong place to "
            "change: update the catalog, and update this expectation deliberately.",
            file=sys.stderr,
        )
        return 1

    print(
        f"source registry: {registered} registered, 0 eligible, 0 collectors enabled, 0 raw records"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
