"""Mission 1.85.11 (N08-B-PILOT). The offline REPORTED_FAILED_ATTEMPT regression specification for the next
DEVELOPMENT pilot.

Ids and digests only, from committed artifacts (no database, no model):

- KNOWN_OVERREAD: the records the operator confirmed, after seeing the Mission 1.85.9 model output, as model
  over-reads (Mission 1.85.10). Desired next-run behaviour: REPORTED_FAILED_ATTEMPT is not PRESENT.
- POSITIVE_SENSITIVITY: every approved DEVELOPMENT record the blind single-human reference marks PRESENT.
  Purpose: show the revision did not buy precision by answering ABSENT everywhere.

This is a targeted, post-model development diagnostic. It is NOT a threshold, NOT certification and NOT a
rewrite of the Mission 1.85.9 result. It is never sent to a provider: the prompt carries none of these ids,
texts, outputs or digests.

    uv run python infrastructure/scripts/render_rfa_regression_spec.py --write
    uv run python infrastructure/scripts/render_rfa_regression_spec.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
REVIEW = DATA / "semantic-extraction-post-model-review-development-v1.json"
ANNOTATION = DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json"
ELIGIBILITY = DATA / "stack-overflow-semantic-egress-eligibility-development-v1.json"
CORPUS = DATA / "stack-overflow-semantic-evaluation-corpus-v1.json"
OUTPUT = DATA / "semantic-extraction-rfa-regression-spec-development-v1.json"
LABEL = "REPORTED_FAILED_ATTEMPT"


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def build() -> dict[str, Any]:
    review = load(REVIEW)
    if review["analysis"]["status"] != "COMPLETE":
        raise SystemExit("REFUSED  the post-model review is not complete")
    surfaces = {
        r["normalized_record_id"]: r["surface_sha256"]
        for r in load(CORPUS)["records"]
        if r["split"] == "DEVELOPMENT"
    }
    approved = set(load(ELIGIBILITY)["approved_record_ids"])
    annotation = {r["normalized_record_id"]: r for r in load(ANNOTATION)["records"]}
    overread = sorted(
        d["normalized_record_id"]
        for d in review["decisions"]
        if d["decision"] == "HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD"
    )
    positives = sorted(
        rid for rid in approved if annotation[rid]["labels"][LABEL]["state"] == "PRESENT"
    )
    if set(overread) & set(positives):
        raise SystemExit("REFUSED  a known over-read is a reference PRESENT")
    return {
        "$comment": "OFFLINE REGRESSION SPECIFICATION for REPORTED_FAILED_ATTEMPT (Mission 1.85.11). Ids and digests only. A targeted post-model development diagnostic for the next DEVELOPMENT pilot: not a threshold, not certification, not a rewrite of the Mission 1.85.9 result. Never part of any provider prompt.",
        "spec_id": "semantic-extraction-rfa-regression-spec-development",
        "version": "1.0.0",
        "label": LABEL,
        "split": "DEVELOPMENT",
        "inputs": {
            "post_model_review_sha256": sha(REVIEW),
            "annotation_sha256": sha(ANNOTATION),
            "eligibility_sha256": sha(ELIGIBILITY),
            "corpus_sha256": sha(CORPUS),
        },
        "sets": {
            "KNOWN_OVERREAD": {
                "source": "Mission 1.85.10 POST_MODEL_OPERATOR_REVIEW, HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD",
                "desired_next_run_behaviour": "REPORTED_FAILED_ATTEMPT is not PRESENT",
                "report": "count of records still PRESENT, and records without valid output, reported apart from every preregistered reading",
                "records": [
                    {"normalized_record_id": rid, "surface_sha256": surfaces[rid]}
                    for rid in overread
                ],
            },
            "POSITIVE_SENSITIVITY": {
                "source": "blind SINGLE_HUMAN_REFERENCE, REPORTED_FAILED_ATTEMPT = PRESENT, EGRESS_APPROVED",
                "desired_next_run_behaviour": "the revision keeps finding reference positives; precision is not bought by answering ABSENT everywhere",
                "report": "true PRESENT, missed reference PRESENT and recall over this set, descriptive, with no threshold",
                "records": [
                    {"normalized_record_id": rid, "surface_sha256": surfaces[rid]}
                    for rid in positives
                ],
            },
        },
        "is_threshold": False,
        "is_certification": False,
        "rewrites_mission_1_85_9": False,
        "sent_to_provider": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    content = (json.dumps(build(), indent=1, ensure_ascii=False) + "\n").encode("utf-8")
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
