"""`sros-inference readiness` — can a semantic-equivalence call be made at all?

Mission 1.24 §0.A. Reports every gate and reaches no model.

The output is deliberately shaped for the operator's next action rather than for
a machine: a readiness tool whose failure mode is *not ready* teaches nobody
anything, and the whole reason this exists is that Mission 1.23's refusal named
one gate when four were closed.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from .inference_readiness import (
    CREDENTIAL_ENV,
    SEMANTIC_EQUIVALENCE_TIER,
    evaluate_inference_readiness,
)

__all__ = ["main"]

DEFAULT_SOURCE = "stack-exchange"
DEFAULT_PROFILE = "local-private-research-v1"


def _load_local_env() -> None:
    """Read `infrastructure/compose/.env` if present, without overriding a real
    environment variable.

    The same precedence `sros-source` uses. A readiness check that disagreed with
    the CLI next to it about where configuration comes from would send an
    operator to edit a file the running system does not read.
    """
    root = pathlib.Path(__file__).resolve().parents[4]
    env_file = root / "infrastructure" / "compose" / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


class _Database:
    """A minimal `RegistryDatabase`. psycopg is imported here and nowhere else
    in this package, so the readiness module stays a pure function of its
    inputs and is testable with no database at all."""

    def __init__(self, url: str) -> None:
        self._url = url

    @contextmanager
    def connection(self) -> Iterator[Any]:
        import psycopg

        with psycopg.connect(self._url) as conn:
            yield conn


def cmd_readiness(args: argparse.Namespace) -> int:
    _load_local_env()
    url = args.database_url or os.environ.get("DATABASE_URL", "")
    if not url:
        print("REFUSED  DATABASE_URL is not set", file=sys.stderr)
        return 2

    result = evaluate_inference_readiness(_Database(url), args.source_id, args.use_profile)

    if args.json:
        print(json.dumps(result.to_json(), indent=2))
        return 0 if result.ready else 1

    print(f"source        {result.source_id}")
    print(f"use profile   {result.use_profile_id}")
    print(f"gateway tier  {result.tier}")
    print()
    width = max(len(g.name) for g in result.gates)
    for gate in result.gates:
        mark = "pass" if gate.passed else "FAIL"
        print(f"  {mark}  {gate.name:<{width}}  {gate.observed}")
    print()

    if result.ready:
        print("READY  every gate passes. Nothing has been sent: this command reports")
        print("       configuration and permissions, and a caller must still hold an")
        print("       authorization decision before it builds a request.")
        return 0

    print("NOT READY")
    for gate in result.failed:
        print(f"  {gate.name}")
        print(f"      {gate.detail}")
    print()
    print("To configure, set these NON-SECRET variables in the local environment:")
    for action in result.operator_actions:
        print(f"  - {action}")
    print()
    print(f"  {CREDENTIAL_ENV} is read for PRESENCE only. Its value is never printed by")
    print("  this command and must not be written into any tracked file.")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sros-inference",
        description=(
            "Report whether external model inference is configured and permitted. "
            f"The semantic classifier requests the {SEMANTIC_EQUIVALENCE_TIER.value} tier."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    readiness = sub.add_parser(
        "readiness", help="every gate between a semantic-equivalence request and a provider"
    )
    readiness.add_argument("--source-id", default=DEFAULT_SOURCE)
    readiness.add_argument("--use-profile", default=DEFAULT_PROFILE)
    readiness.add_argument("--database-url", default=None)
    readiness.add_argument("--json", action="store_true")
    readiness.set_defaults(func=cmd_readiness)

    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
