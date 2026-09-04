"""Render the completed Wikimedia convergent reliability review (Mission 1.44.1).

    docs/data/wikimedia-convergent-operator-reliability-review-v1.json
            |
            v
    docs/data/wikimedia-convergent-operator-reliability-review-v1.md

**The conformance rule is imported, not copied.** `validate` lives in
`render_operator_reliability_review.py` and is shared: two copies of a rule drift,
and a drifted copy of a rule is worse than no copy. What is written twice is the
PROSE, which is genuinely different for a different measurement and would be
worse if it were generalised into a template with holes.

No database and no network, so `--check` runs in CI.

    python infrastructure/scripts/render_wikimedia_operator_reliability_review.py
    python infrastructure/scripts/render_wikimedia_operator_reliability_review.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "packages" / "evidence-reliability" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))

DOCS = ROOT / "docs" / "data"
REVIEW = DOCS / "wikimedia-convergent-operator-reliability-review-v1.json"
OUT_MD = DOCS / "wikimedia-convergent-operator-reliability-review-v1.md"

from render_operator_reliability_review import validate  # noqa: E402


def render(review: dict) -> str:
    lines: list[str] = []
    scope = review["scope"]
    covers = review["covers"]
    profile = {k: v for k, v in review["rubric_profile"].items() if k != "$comment"}

    lines.append("# The completed Wikimedia convergent reliability review")
    lines.append("")
    lines.append(
        f"**`{review['artifact_version']}`**, performed under "
        f"**`{review['review_rubric']['id']}@{review['review_rubric']['version']}`**. "
        "Authored by the reviewer; this page is rendered from it."
    )
    lines.append("")
    lines.append(
        "**This is a completed review, not a preparation packet** — which is why it "
        "carries a number where the Mission 1.44 packet carried a blank. That packet "
        "records the question as it stood and is not rewritten by this answer."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## The scope")
    lines.append("")
    lines.append("```text")
    for key, value in scope.items():
        lines.append(f"{key:18}{value}")
    lines.append("```")
    lines.append("")
    lines.append(
        f"It binds **{covers['evidence_rows']} Evidence rows across "
        f"{covers['claims']} Claims**, with witness cardinalities "
        + ", ".join(f"`{c}`" for c in covers["witness_cardinalities"])
        + " — spanning articles "
        + ", ".join(f"`{a}`" for a in covers["articles"])
        + ", directions "
        + ", ".join(f"`{d}`" for d in covers["directions"])
        + " and requester classes "
        + ", ".join(f"`{c}`" for c in covers["audience_classes"])
        + ", because a reliability scope carries none of them."
    )
    lines.append("")
    lines.append(review["scope_note"])
    lines.append("")
    lines.append("## The judgement")
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| **Reliability** | **{review['reliability']}** |")
    lines.append(f"| Origin | `{review['origin']}` |")
    lines.append(f"| Reviewer | `{review['reviewed_by']}` |")
    lines.append(f"| Gate | `{review['numeric_judgement_gate']}` |")
    lines.append(
        f"| Rubric | `{review['review_rubric']['id']}@{review['review_rubric']['version']}` |"
    )
    lines.append("")
    lines.append(review["reliability_note"])
    lines.append("")
    lines.append("## The ordinal profile the number summarises")
    lines.append("")
    lines.append("| dimension | state |")
    lines.append("|---|---|")
    for dimension, state in profile.items():
        lines.append(f"| `{dimension}` | `{state}` |")
    lines.append("")
    lines.append(review["rubric_profile_note"])
    lines.append("")
    lines.append("## Material unknowns")
    lines.append("")
    lines.append("| dimension | unknown | documented | material? |")
    lines.append("|---|---|---|---|")
    for unknown in review["material_unknowns"]:
        lines.append(
            f"| `{unknown['dimension_id']}` | {unknown['what_is_not_established']} "
            f"| `{unknown['documentary_status']}` "
            f"| **{unknown['reviewer_materiality']}** |"
        )
    lines.append("")
    lines.append(review["material_unknowns_note"])
    lines.append("")
    lines.append("## Hard stops")
    lines.append("")
    lines.append("| hard stop | triggered |")
    lines.append("|---|---|")
    for stop, answer in review["hard_stops_answered"].items():
        lines.append(f"| `{stop}` | **{answer}** |")
    lines.append("")
    lines.append(review["hard_stops_note"])
    lines.append("")
    lines.append(review["gate_note"])
    lines.append("")
    lines.append("## Rationale")
    lines.append("")
    for paragraph in review["rationale"].split("\n\n"):
        lines.append(paragraph.strip())
        lines.append("")
    lines.append("## Stated limitation")
    lines.append("")
    for paragraph in review["stated_limitation"].split("\n\n"):
        lines.append(paragraph.strip())
        lines.append("")
    lines.append(review["rationale_and_limitation_note"])
    lines.append("")
    lines.append("## Documentary basis")
    lines.append("")
    for item in review["basis"]:
        lines.append(
            f"- **{item['document_title']}** (`{item['section_reference']}`, "
            f"`{item['basis_type']}`, retrieved {item['retrieved_at']}) — "
            f"**{item['applicability_to_this_scope']}**. {item['why']}"
        )
        lines.append(f"  - *Finding:* {item['summarized_finding']}")
    lines.append("")
    lines.append(review["basis_note"])
    lines.append("")
    lines.append("## What this is not")
    lines.append("")
    for item in review["what_this_is_not"]:
        lines.append(f"- {item}")
    lines.append("")
    persisted = review.get("persisted_assessment")
    lines.append("## What it produced")
    lines.append("")
    if persisted:
        lines.append(
            f"Assessment `{persisted['id']}`, version **{persisted['version']}**, recorded "
            f"{persisted['recorded_at']}."
        )
    else:
        lines.append(
            "**Nothing yet.** `persisted_assessment` is `null`: the accountable workflow "
            "has not recorded this review, so the scope still resolves "
            "`NO_APPLICABLE_ASSESSMENT` and every affected Evidence row is still "
            "`NON_SCORABLE`."
        )
    lines.append("")
    lines.append(review["persisted_assessment_note"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare and write nothing")
    args = parser.parse_args()

    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    problems = validate(review)
    if problems:
        print("REFUSED: the review does not conform to the rubric it names")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    markdown = render(review)

    if args.check:
        if not OUT_MD.exists():
            print(f"REFUSED: {OUT_MD.name} does not exist; run without --check first")
            return 1
        if OUT_MD.read_text(encoding="utf-8") != markdown:
            print(f"DRIFT    {OUT_MD.name} does not match the review")
            return 1
        print(f"ok       {OUT_MD.name} matches the review, and the review conforms")
        return 0

    OUT_MD.write_text(markdown, encoding="utf-8")

    print(f"rubric      : {review['review_rubric']['id']}@{review['review_rubric']['version']}")
    print(f"gate        : {review['numeric_judgement_gate']}")
    print(f"reliability : {review['reliability']}  ({review['origin']}, {review['reviewed_by']})")
    print(f"basis rows  : {len(review['basis'])}")
    print(
        "materiality : "
        + ", ".join(
            f"{u['dimension_id']}={u['reviewer_materiality']}" for u in review["material_unknowns"]
        )
    )
    print(f"persisted   : {review.get('persisted_assessment') or 'not yet'}")
    print(f"\nwrote {OUT_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
