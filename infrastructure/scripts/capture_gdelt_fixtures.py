#!/usr/bin/env python3
"""Capture the two GDELT DOC API response contracts. NOT a collector.

Mission 1.9.1 §5, closing **H-27**.

    python infrastructure/scripts/capture_gdelt_fixtures.py
    python infrastructure/scripts/capture_gdelt_fixtures.py --dry-run

WHY THIS EXISTS AS A SCRIPT RATHER THAN A TEST

Mission 1.9 could not observe the timeline response envelopes: GDELT does not
publish its JSON field names, and the development environment could not reach
`api.gdeltproject.org` at all -- fourteen attempts across two routes gave
ConnectTimeout, ECONNRESET, 429 and finally ECONNREFUSED, while
`api.worldbank.org` returned HTTP 200 from the same client moments apart.

A parser was **not** written against invented field names, because it would have
been validated by fake responses composed from the same invention: a test
passing by checking a guess against itself.

So this runs wherever GDELT is reachable, writes two fixture files, and the
committed fixtures are what CI parses from then on. **CI never runs this.**

WHAT IT DELIBERATELY IS NOT

  * It is not a collector. It builds no RawRecord, opens no database connection
    and imports no persistence code. §25 -- fixtures are test artefacts
    establishing an external contract, not research observations.
  * It does not evade anything (§5). One host, two requests, conservative
    pacing, explicit timeouts. If GDELT refuses, it reports that and stops --
    no retries against a block, no alternate route, no second identity.
  * It never dereferences a URL found in a response. It issues exactly the two
    requests it composes and nothing else.

WHAT IT WRITES

Two `.json` files holding the response bytes verbatim, and two `.meta.json`
sidecars carrying the provenance §7 requires: endpoint, mode, parameters, the
capture time, HTTP status, content type, byte length and a sha256 of the bytes.

The hash is over **the captured bytes**, not over a re-serialised Python object
-- §7 is explicit, and a hash of a reconstruction would prove only that the
reconstruction is stable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import time
from datetime import UTC, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "services/acquisition/python/tests/fixtures/gdelt"

# The host the review approved and the only one this script may contact. Written
# here as a literal because this is not the collector -- the collector derives
# its allowlist from the registry, and must keep doing so.
HOST = "api.gdeltproject.org"
ENDPOINT = f"https://{HOST}/api/v2/doc/doc"

USER_AGENT = (
    "startup-research-os-fixture-capture/1.0 (+https://github.com/Speekyx/startup-research-os)"
)

# A deliberately dull query. §6: the goal is the envelope, not research data,
# and a person-targeting or market-research query would collect something under
# cover of establishing a contract.
QUERY = "weather"

# The smallest window that still returns a usable timeline. Under 72 hours GDELT
# uses a 15-minute step, so one day is a short series rather than a long one.
TIMESPAN = "1d"

CAPTURES = (
    ("timelinetone", "TimelineTone"),
    ("timelinevolraw", "TimelineVolRaw"),
)

# Two requests, spaced. GDELT publishes no rate limit and returned 429 to a
# Mission 1.9 probe, so the pause is our own caution and is not a claim about
# anyone's quota (§23).
PAUSE_SECONDS = 15.0


def _params(mode: str) -> dict[str, str]:
    return {"query": QUERY, "mode": mode, "format": "json", "timespan": TIMESPAN}


def _describe() -> str:
    lines = [
        f"host      {HOST}",
        f"endpoint  {ENDPOINT}",
        f"query     {QUERY!r}",
        f"timespan  {TIMESPAN}",
        f"pause     {PAUSE_SECONDS}s between requests",
        f"writes    {FIXTURES.relative_to(ROOT)}",
        "",
        "requests:",
    ]
    lines.extend(f"  {name:<16} mode={mode} format=json" for name, mode in CAPTURES)
    return "\n".join(lines)


def capture(name: str, mode: str) -> int:
    try:
        import httpx
    except ImportError:
        print("httpx is not installed; run `uv sync --all-packages`", file=sys.stderr)
        return 2

    try:
        response = httpx.get(
            ENDPOINT,
            params=_params(mode),
            timeout=httpx.Timeout(45.0, connect=15.0, read=30.0),
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            # Not followed, for the reason the collector's transport does not
            # follow them: a redirect is the documented way out of a host
            # allowlist.
            follow_redirects=False,
        )
    except Exception as exc:  # noqa: BLE001 - the type name is what an operator needs
        print(f"FAIL  {mode}: {type(exc).__name__}", file=sys.stderr)
        print(
            "      This environment cannot reach GDELT. Run this script from one that can;\n"
            "      do NOT work around the block (Mission 1.9.1 §5).",
            file=sys.stderr,
        )
        return 1

    if response.status_code != 200:
        print(f"FAIL  {mode}: HTTP {response.status_code}", file=sys.stderr)
        if response.status_code == 429:
            print(
                "      GDELT is throttling. Wait and retry; do not reduce the pause.",
                file=sys.stderr,
            )
        return 1

    body = response.content
    try:
        json.loads(body)
    except ValueError:
        print(f"FAIL  {mode}: the response is not JSON ({len(body)} bytes)", file=sys.stderr)
        return 1

    FIXTURES.mkdir(parents=True, exist_ok=True)
    fixture = FIXTURES / f"{name}.json"
    # Bytes verbatim. Re-serialising through Python would normalise key order
    # and float formatting, and the fixture would then be a Python artefact
    # rather than GDELT's response.
    fixture.write_bytes(body)
    (FIXTURES / f"{name}.meta.json").write_text(
        json.dumps(
            {
                "source_id": "gdelt",
                "access_profile": "gdelt-doc-api",
                "endpoint": ENDPOINT,
                "mode": mode,
                "params": _params(mode),
                "captured_at": datetime.now(UTC).isoformat(),
                "http_status": response.status_code,
                "content_type": response.headers.get("content-type"),
                "byte_length": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "captured_by": "infrastructure/scripts/capture_gdelt_fixtures.py",
                "note": (
                    "Response bytes verbatim. The hash is over the captured bytes, not over "
                    "a re-serialised representation. This is a test fixture establishing an "
                    "external contract, NOT a research observation: it is never persisted as "
                    "a RawRecord (Mission 1.9.1 §7, §25)."
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"ok    {mode:<16} {len(body):>7} bytes -> {fixture.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="capture_gdelt_fixtures",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print exactly what would be requested and write nothing",
    )
    args = parser.parse_args()

    print(_describe())
    print()
    if args.dry_run:
        print("dry run: nothing requested, nothing written")
        return 0

    failures = 0
    for index, (name, mode) in enumerate(CAPTURES):
        if index:
            time.sleep(PAUSE_SECONDS)
        failures += capture(name, mode)

    if failures:
        print(
            f"\n{failures} capture(s) failed. H-27 stays open.\n"
            "Do not hand-write the fixtures: Mission 1.9.1 §36 says stop instead.",
            file=sys.stderr,
        )
        return 1
    print("\nboth contracts captured. Commit the .json and .meta.json files together.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
