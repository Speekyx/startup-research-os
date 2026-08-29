#!/usr/bin/env python3
"""Run every Python test suite in the monorepo.

Stdlib `unittest`, no install required (ADR-009 rationale: a check that cannot
run is a check that gets skipped). pytest, once installed, collects the same
files unchanged.

Each suite runs in its OWN subprocess. They all contain a top-level `tests`
package, so a single interpreter would collide on `sys.modules["tests"]` and
silently drop suites -- which is worse than failing, because the run would look
green with two thirds of the tests missing.

    python infrastructure/scripts/run_python_tests.py
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

SUITES = [
    "packages/contracts/python",
    "packages/llm-gateway/python",
    "services/workers/python",
    "services/research-orchestrator/python",
]

# Packages every suite may import without an install. The orchestrator is here
# because its rules -- lifecycle, DAG, budget, completeness -- are pure Python
# over the contracts and the worker routing table, and they are exactly the
# rules that must stay checkable when a dependency environment is broken
# (ADR-009).
SHARED_PATHS = [
    "packages/contracts/python",
    "packages/llm-gateway/python",
    "services/workers/python",
    "services/research-orchestrator/python",
]


def main() -> int:
    env = dict(os.environ)
    extra = os.pathsep.join(str(ROOT / p) for p in SHARED_PATHS)
    env["PYTHONPATH"] = (
        f"{extra}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else extra
    )

    failures: list[str] = []
    total = 0

    for suite in SUITES:
        cwd = ROOT / suite
        print(f"=== {suite} " + "=" * max(0, 60 - len(suite)))
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-t",
                ".",
                "-p",
                "test_*.py",
            ],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
        )
        output = (proc.stdout + proc.stderr).strip()
        print(output)
        print()

        ran = 0
        for line in output.splitlines():
            if line.startswith("Ran ") and " test" in line:
                ran = int(line.split()[1])
                total += ran
        if proc.returncode != 0:
            failures.append(suite)
        elif ran == 0:
            # A suite that discovers nothing must not report success. Silent
            # zero-test runs are how a green pipeline stops meaning anything.
            print(f"  !! {suite} discovered 0 tests", file=sys.stderr)
            failures.append(f"{suite} (0 tests discovered)")

    print("=" * 70)
    if failures:
        print(f"FAILED suites: {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"all Python suites passed: {total} tests across {len(SUITES)} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
