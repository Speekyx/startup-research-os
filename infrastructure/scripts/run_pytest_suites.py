#!/usr/bin/env python3
"""Run every pytest suite, one package per subprocess.

Each package has a top-level `tests` package, so a single interpreter would
collide on `sys.modules["tests"]`. Per-package subprocesses keep the suites
independent and the output readable.

This is the INSTALL-DEPENDENT runner. `run_python_tests.py` is the
zero-dependency one and must keep working (ADR-009): between them, a broken
environment can never silently reduce coverage to nothing.

    python infrastructure/scripts/run_pytest_suites.py
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
    "services/acquisition/python",
    "services/research-orchestrator/python",
    "services/gateway/python",
]


def main() -> int:
    env = dict(os.environ)
    env.setdefault("DATABASE_URL", "postgresql://sros:sros_dev_password@127.0.0.1:55432/sros")
    env.setdefault("REDIS_URL", "redis://127.0.0.1:55379/0")
    env.setdefault("QDRANT_URL", "http://127.0.0.1:55333")

    failures: list[str] = []
    for suite in SUITES:
        print(f"=== {suite} " + "=" * max(0, 60 - len(suite)))
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q"],
            cwd=ROOT / suite,
            env=env,
            check=False,
        )
        if proc.returncode != 0:
            failures.append(suite)
        print()

    print("=" * 70)
    if failures:
        print(f"FAILED suites: {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"all pytest suites passed across {len(SUITES)} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
