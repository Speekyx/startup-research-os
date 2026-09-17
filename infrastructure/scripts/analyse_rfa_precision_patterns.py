"""Mission 1.85.11 (N08-B-PILOT). Offline, aggregate-only pattern analysis for REPORTED_FAILED_ATTEMPT precision.

Reads the frozen DEVELOPMENT surfaces (DATABASE_URL) and compares three evidence groups:

- OVERREAD: the model's accepted quotes on the 9 records the operator confirmed as model over-reads
  (Mission 1.85.10), rebuilt from the frozen surface and committed offsets, digest-verified;
- MODEL_AGREED: the model's accepted quotes on accepted records the blind reference marked PRESENT;
- HUMAN_PRESENT: the blind human reference spans of every approved record marked PRESENT.

For each quote it computes deterministic lexical and structural features, and writes COUNTS ONLY:

    docs/data/semantic-extraction-rfa-failure-mode-analysis-development-v1.json

No text, no quote, no record-level feature row is written or printed. No label is changed: the features
describe where the extraction instruction was too weak, never what a record "really" is. The features are
coarse English regular expressions and say so.

    uv run python infrastructure/scripts/analyse_rfa_precision_patterns.py --write
    uv run python infrastructure/scripts/analyse_rfa_precision_patterns.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
for _path in ("packages/semantic-extraction-contract/python", "packages/contracts/python"):
    sys.path.insert(0, str(ROOT / _path))
sys.path.insert(0, str(ROOT / "infrastructure/scripts"))

from sros_semantic_extraction_contract.surface import marker_regions  # noqa: E402

DATA = ROOT / "docs" / "data"
SUMMARY = DATA / "semantic-extraction-pilot-run-development-v1.json"
ANNOTATION = DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json"
REVIEW = DATA / "semantic-extraction-post-model-review-development-v1.json"
ELIGIBILITY = DATA / "stack-overflow-semantic-egress-eligibility-development-v1.json"
OUTPUT = DATA / "semantic-extraction-rfa-failure-mode-analysis-development-v1.json"
LABEL = "REPORTED_FAILED_ATTEMPT"
QUOTE_MAX = 400

FEATURES: dict[str, re.Pattern[str]] = {
    "explicit_try_verb": re.compile(r"\b(tried|try|trying|attempted|attempting|tested)\b", re.I),
    "first_person_action": re.compile(
        r"\b(i|we)\s+(?:have\s+|had\s+|'ve\s+|also\s+|then\s+|already\s+|even\s+)?"
        r"(tried|attempted|added|changed|set|installed|ran|run|used|updated|removed|reinstalled|followed|"
        r"switched|modified|configured|put|wrote|created|did|replaced|called|moved|deleted|restarted|"
        r"enabled|disabled|upgraded|downgraded|applied|checked|cleared|rebuilt|reset)\b",
        re.I,
    ),
    "first_person_state_or_usage": re.compile(
        r"\b(i\s+am\s+using|i'm\s+using|i\s+use|we\s+use|i\s+have\s+(a|an|the|my|this)|my\s+\w+\s+(is|has|are))\b",
        re.I,
    ),
    "failure_phrase": re.compile(
        r"(did\s?n[o']?t\s+work|does\s?n[o']?t\s+work|not\s+working|no\s+effect|no\s+luck|to\s+no\s+avail|"
        r"without\s+(success|luck)|still\s+(get|gets|getting|shows?|fails?|the\s+same|not)|"
        r"same\s+(error|result|problem|issue)|nothing\s+(changed|happens?|happened)|"
        r"(did|does|do|is|was)\s?n[o']?t\s+(help|fix|solve|change))",
        re.I,
    ),
    "contrast_marker": re.compile(r"\b(but|however|still|unfortunately|yet)\b", re.I),
    "error_token": re.compile(r"(error|exception|traceback|warning|fail(ed|s|ure)?)", re.I),
    "question_form": re.compile(r"(\?|^\s*(how|why|is\s+there|can\s+i|what)\b)", re.I),
    "desire_or_goal": re.compile(
        r"\b(i\s+want|i\s+need|i('d|\s+would)\s+like|i\s+am\s+trying\s+to|i'm\s+trying\s+to)\b",
        re.I,
    ),
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def features(surface: str, start: int, end: int) -> dict[str, bool]:
    text = surface[start:end]
    row = {name: bool(pattern.search(text)) for name, pattern in FEATURES.items()}
    regions = marker_regions(surface)
    row["inside_code_or_quoted_region"] = any(a <= start and end <= b for _, a, b in regions)
    row["overlaps_code_or_quoted_region"] = any(a < end and start < b for _, a, b in regions)
    attempt = row["explicit_try_verb"] or row["first_person_action"]
    failure = row["failure_phrase"] or row["contrast_marker"]
    row["attempt_and_failure_in_one_quote"] = attempt and failure
    row["error_without_attempt_language"] = row["error_token"] and not attempt
    row["state_or_goal_without_attempt_language"] = (
        row["first_person_state_or_usage"] or row["desire_or_goal"]
    ) and not attempt
    return row


def aggregate(rows: list[dict[str, bool]]) -> dict[str, Any]:
    names = sorted(rows[0]) if rows else []
    return {"quotes": len(rows), "features": {n: sum(1 for r in rows if r[n]) for n in names}}


def build(surfaces: dict[str, str]) -> dict[str, Any]:
    summary = load(SUMMARY)
    annotation = {r["normalized_record_id"]: r for r in load(ANNOTATION)["records"]}
    review = load(REVIEW)
    approved = set(load(ELIGIBILITY)["approved_record_ids"])
    overread = {
        d["normalized_record_id"]
        for d in review["decisions"]
        if d["decision"] == "HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD"
    }
    groups: dict[str, list[dict[str, bool]]] = {
        "OVERREAD": [],
        "MODEL_AGREED": [],
        "HUMAN_PRESENT": [],
    }
    for record in summary["records"]:
        extraction = record.get("extraction")
        if not record["accepted"] or not extraction:
            continue
        rid = record["normalized_record_id"]
        surface = surfaces[rid]
        blind = annotation[rid]["labels"][LABEL]["state"]
        for finding in extraction["findings"]:
            if finding["finding_type"] != LABEL:
                continue
            start, end = finding["evidence_start"], finding["evidence_end"]
            if sha(surface[start:end]) != finding["evidence_sha256"]:
                raise SystemExit(f"REFUSED  a model quote for {rid} no longer matches its digest")
            if rid in overread:
                groups["OVERREAD"].append(features(surface, start, end))
            elif blind == "PRESENT":
                groups["MODEL_AGREED"].append(features(surface, start, end))
    span_counts, windows, longest = [], [], []
    present_records = 0
    for rid in sorted(approved):
        label = annotation[rid]["labels"][LABEL]
        if label["state"] != "PRESENT":
            continue
        present_records += 1
        surface = surfaces[rid]
        spans = label["spans"]
        span_counts.append(len(spans))
        for span in spans:
            if sha(surface[span["start"] : span["end"]]) != span["quote_sha256"]:
                raise SystemExit(
                    f"REFUSED  a reference span for {rid} no longer matches its digest"
                )
            groups["HUMAN_PRESENT"].append(features(surface, span["start"], span["end"]))
            longest.append(span["end"] - span["start"])
        windows.append(max(s["end"] for s in spans) - min(s["start"] for s in spans))
    return {
        "$comment": "AGGREGATE PATTERN ANALYSIS for REPORTED_FAILED_ATTEMPT precision (Mission 1.85.11). Counts only: no text, no quote, no per-record feature row. Coarse English regular expressions over quotes rebuilt from frozen surfaces and committed offsets (digest-verified). Describes weaknesses of the extraction instruction; changes no label.",
        "analysis_id": "semantic-extraction-rfa-failure-mode-analysis-development",
        "version": "1.0.0",
        "inputs": {
            "run_summary_sha256": hashlib.sha256(SUMMARY.read_bytes()).hexdigest(),
            "annotation_sha256": hashlib.sha256(ANNOTATION.read_bytes()).hexdigest(),
            "post_model_review_sha256": hashlib.sha256(REVIEW.read_bytes()).hexdigest(),
        },
        "feature_definitions": {name: pattern.pattern for name, pattern in FEATURES.items()}
        | {
            "inside_code_or_quoted_region": "quote lies wholly inside a [CODE] or [QUOTE] region",
            "overlaps_code_or_quoted_region": "quote overlaps a [CODE] or [QUOTE] region",
            "attempt_and_failure_in_one_quote": "(explicit_try_verb or first_person_action) and (failure_phrase or contrast_marker)",
            "error_without_attempt_language": "error_token and no attempt language",
            "state_or_goal_without_attempt_language": "(first_person_state_or_usage or desire_or_goal) and no attempt language",
        },
        "groups": {
            "OVERREAD": {"records": len(overread), **aggregate(groups["OVERREAD"])},
            "MODEL_AGREED": aggregate(groups["MODEL_AGREED"]),
            "HUMAN_PRESENT": {"records": present_records, **aggregate(groups["HUMAN_PRESENT"])},
        },
        "evidence_representation_audit": {
            "reference_present_records": present_records,
            "records_by_span_count": {
                str(n): span_counts.count(n) for n in sorted(set(span_counts))
            },
            "spans_longer_than_quote_max": sum(1 for n in longest if n > QUOTE_MAX),
            "records_whose_spans_fit_one_window_of_quote_max": sum(
                1 for w in windows if w <= QUOTE_MAX
            ),
            "records_needing_a_window_over_quote_max": sum(1 for w in windows if w > QUOTE_MAX),
            "longest_span_characters": max(longest) if longest else None,
            "quote_max_characters": QUOTE_MAX,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    from build_semantic_egress_eligibility import development_surfaces

    doc = build(development_surfaces())
    content = (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    if args.write:
        OUTPUT.write_bytes(content)
        print(f"wrote {OUTPUT.name}")
        return 0
    if not OUTPUT.exists() or OUTPUT.read_bytes() != content:
        print(f"FAIL     {OUTPUT.name} is stale")
        return 1
    print(f"ok       {OUTPUT.name} matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
