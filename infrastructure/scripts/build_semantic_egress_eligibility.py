"""Mission 1.85.4 (N08-B). Residual-identifier scan and egress eligibility for the DEVELOPMENT split.

Policy REVIEW_OR_EXCLUDE_NO_REDACTION. Reads the held records read-only, renders the exact surfaces,
scans them, and derives eligibility from the human decision file. Writes:

- `stack-overflow-semantic-egress-scan-development-v1.json`: per-record trigger COUNTS and transmission
  problems, the scan and pattern-table digests. Never matched text, never offsets.
- `stack-overflow-semantic-egress-decisions-development-v1.json`: the human decision file. Created BLANK
  once; only a human operator fills it. This script never writes a decision.
- `stack-overflow-semantic-egress-eligibility-development-v1.json`: derived, never hand-edited.

`--local-review DIR` writes, OUTSIDE the repository, each record's triggers with offsets and the matched
text, for the human reviewer. HOLDOUT is not scanned in N08-B.

    uv run python infrastructure/scripts/build_semantic_egress_eligibility.py --write
    uv run python infrastructure/scripts/build_semantic_egress_eligibility.py --check
    uv run python infrastructure/scripts/build_semantic_egress_eligibility.py --local-review DIR
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
for path in ("packages/semantic-extraction-contract/python",):
    sys.path.insert(0, str(ROOT / path))

from sros_semantic_extraction_contract import (  # noqa: E402
    SURFACE_ID,
    SURFACE_VERSION,
    surface_sha256,
)
from sros_semantic_extraction_contract.egress import (  # noqa: E402
    SCAN_ID,
    SCAN_VERSION,
    derive_egress_eligibility,
    load_decisions,
    pattern_table_sha256,
    scan_surface,
    transmission_integrity_problems,
)

DATA = ROOT / "docs" / "data"
CORPUS = DATA / "stack-overflow-semantic-evaluation-corpus-v1.json"
SCAN = DATA / "stack-overflow-semantic-egress-scan-development-v1.json"
DECISIONS = DATA / "stack-overflow-semantic-egress-decisions-development-v1.json"
ELIGIBILITY = DATA / "stack-overflow-semantic-egress-eligibility-development-v1.json"


def _corpus_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "semantic_corpus", ROOT / "infrastructure/scripts/build_semantic_evaluation_corpus.py"
    )
    if spec is None or spec.loader is None:
        raise SystemExit("FAIL     cannot load the corpus builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def development_surfaces() -> dict[str, str]:
    corpus = json.loads(CORPUS.read_text("utf-8"))
    wanted = {
        r["normalized_record_id"]: r for r in corpus["records"] if r["split"] == "DEVELOPMENT"
    }
    _, _, surfaces = _corpus_module().build(_corpus_module().read_rows())
    out = {}
    for rid, record in wanted.items():
        surface = surfaces.get(rid)
        if surface is None or surface_sha256(surface) != record["surface_sha256"]:
            raise SystemExit(f"FAIL     held record {rid} no longer matches the frozen corpus")
        out[rid] = surface
    return out


def dump(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def blank_decisions() -> dict[str, Any]:
    return {
        "$comment": "HUMAN EGRESS DECISIONS for the DEVELOPMENT split. Filled only by a human operator after local review; never by a model, a script or a regex. REVIEW_REQUIRED is derived, never recorded. A bulk decision may only accept records with zero triggers and must list them with their surface digests and the sha256 of the sorted id list.",
        "scan": f"{SCAN_ID}@{SCAN_VERSION}",
        "pattern_table_sha256": pattern_table_sha256(),
        "surface": f"{SURFACE_ID}@{SURFACE_VERSION}",
        "policy": "REVIEW_OR_EXCLUDE_NO_REDACTION",
        "decisions": [],
        "bulk_decisions": [],
    }


def build(
    surfaces: dict[str, str], decisions_doc: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    records = []
    for rid in sorted(surfaces):
        surface = surfaces[rid]
        matches = scan_surface(surface)
        records.append(
            {
                "normalized_record_id": rid,
                "surface_sha256": surface_sha256(surface),
                "trigger_counts": {name: len(found) for name, found in matches.items()},
                "transmission_problems": sorted(
                    {p.split(":")[0] for p in transmission_integrity_problems(surface)}
                ),
            }
        )
    scan = {
        "$comment": "Residual-identifier scan on the exact transmitted surface (N08-B). Counts only: no matched text and no offsets are committed. A trigger is a reason to look, not a finding that anything is personal data.",
        "scan": f"{SCAN_ID}@{SCAN_VERSION}",
        "pattern_table_sha256": pattern_table_sha256(),
        "surface": f"{SURFACE_ID}@{SURFACE_VERSION}",
        "split": "DEVELOPMENT",
        "records": records,
    }
    scan["scan_sha256"] = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    decisions = load_decisions(
        decisions_doc, scan_id=SCAN_ID, pattern_digest=pattern_table_sha256()
    )
    derived = derive_egress_eligibility(records, decisions)
    counts: dict[str, int] = {}
    for row in derived:
        counts[row["state"]] = counts.get(row["state"], 0) + 1
    eligibility = {
        "$comment": "Egress eligibility for the DEVELOPMENT split, DERIVED from the scan and the human decision file. Never edited by hand. No record is approved without a recorded human decision; a machine may only exclude.",
        "policy": "REVIEW_OR_EXCLUDE_NO_REDACTION",
        "scan_sha256": scan["scan_sha256"],
        "decisions_sha256": hashlib.sha256(
            json.dumps(decisions_doc, sort_keys=True).encode()
        ).hexdigest(),
        "state_counts": dict(sorted(counts.items())),
        "approved_record_ids": [
            r["normalized_record_id"] for r in derived if r["state"] == "EGRESS_APPROVED"
        ],
        "records": derived,
    }
    return scan, eligibility


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--local-review", metavar="DIR")
    args = parser.parse_args(argv)
    surfaces = development_surfaces()

    if args.local_review:
        out = pathlib.Path(args.local_review)
        if out.resolve().is_relative_to(ROOT.resolve()):
            print(
                "REFUSED  local review material holds licensed text and must live outside the repository"
            )
            return 1
        out.mkdir(parents=True, exist_ok=True)
        for rid, surface in sorted(surfaces.items()):
            found = [
                {"pattern": name, "start": a, "end": b, "text": surface[a:b]}
                for name, spans in scan_surface(surface).items()
                for a, b in spans
            ]
            (out / f"{rid}.json").write_bytes(
                dump(
                    {
                        "normalized_record_id": rid,
                        "surface_sha256": surface_sha256(surface),
                        "transmission_problems": transmission_integrity_problems(surface),
                        "triggers": found,
                    }
                )
            )
        print(f"wrote local review material for {len(surfaces)} records")
        return 0

    if not DECISIONS.exists():
        if args.check:
            print(f"FAIL     {DECISIONS.name} is missing")
            return 1
        DECISIONS.write_bytes(dump(blank_decisions()))
    scan, eligibility = build(surfaces, json.loads(DECISIONS.read_text("utf-8")))
    targets = {SCAN: dump(scan), ELIGIBILITY: dump(eligibility)}
    if args.write:
        for path, content in targets.items():
            path.write_bytes(content)
        print(f"scan {len(scan['records'])} records; eligibility {eligibility['state_counts']}")
        return 0
    stale = [p.name for p, c in targets.items() if not p.exists() or p.read_bytes() != c]
    for name in stale:
        print(f"FAIL     {name} is stale")
    if not stale:
        print(f"ok       egress eligibility matches ({eligibility['state_counts']})")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
