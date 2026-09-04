"""Validate and render the completed operator reliability review (Mission 1.42.1 §3, §4).

The review file is AUTHORED — it records what a person decided — so this script
does not generate it. What it does is check it against the rubric it claims to
have been performed under, and render the human-readable half:

    docs/data/second-pilot-convergent-operator-reliability-review-v1.json  (authored)
            |
            v
    docs/data/second-pilot-convergent-operator-reliability-review-v1.md    (rendered)

**Every check here is structural.** It verifies that the states are states, the
materiality answers are permitted answers, the gate is a gate, the basis types
are real enum members, and the rubric id and version are the canonical ones. It
does **not** check whether the judgement is a good one — nothing here could, and
a script that tried would be the model reviewer the rubric forbids.

No database and no network, so `--check` runs in CI.

    python infrastructure/scripts/render_operator_reliability_review.py
    python infrastructure/scripts/render_operator_reliability_review.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "evidence-reliability" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "contracts" / "python"))

DOCS = ROOT / "docs" / "data"
REVIEW = DOCS / "second-pilot-convergent-operator-reliability-review-v1.json"
OUT_MD = DOCS / "second-pilot-convergent-operator-reliability-review-v1.md"

from sros_contracts import ReliabilityAssessmentOrigin, ReliabilityBasisType  # noqa: E402
from sros_evidence_reliability import rubric  # noqa: E402


def validate(review: dict) -> list[str]:
    """Structural conformance to the rubric. Returns the problems found."""
    problems: list[str] = []

    declared = review.get("review_rubric") or {}
    if declared.get("id") != rubric.RUBRIC_ID:
        problems.append(f"rubric id {declared.get('id')!r} is not {rubric.RUBRIC_ID!r}")
    if declared.get("version") != rubric.RUBRIC_VERSION:
        problems.append(
            f"rubric version {declared.get('version')!r} is not {rubric.RUBRIC_VERSION!r}"
        )

    # Every accepted dimension answered, with a state the rubric defines, and no
    # dimension invented. A profile missing a dimension is not a shorter review;
    # it is a review that skipped a question.
    profile = {k: v for k, v in (review.get("rubric_profile") or {}).items() if k != "$comment"}
    expected = {d.id for d in rubric.DIMENSIONS}
    if set(profile) != expected:
        problems.append(f"profile covers {sorted(profile)}, expected {sorted(expected)}")
    states = {s.value for s in rubric.ReviewState}
    for dimension, state in profile.items():
        if state not in states:
            problems.append(f"{dimension} state {state!r} is not a rubric review state")

    for unknown in review.get("material_unknowns") or ():
        answer = unknown.get("reviewer_materiality")
        if answer not in rubric.MATERIALITY_ANSWERS:
            problems.append(f"materiality {answer!r} is not one of {rubric.MATERIALITY_ANSWERS}")
        if unknown.get("dimension_id") not in expected:
            problems.append(f"unknown names {unknown.get('dimension_id')!r}, not a dimension")

    gate = review.get("numeric_judgement_gate")
    if gate not in {outcome.value for outcome in rubric.NumericJudgementGate}:
        problems.append(f"gate {gate!r} is not a rubric gate outcome")

    # A value exists if and only if the gate permitted one. A number under a
    # refusal would be a judgement the reviewer declined to make.
    permitted = gate == rubric.NumericJudgementGate.NUMERIC_JUDGEMENT_PERMITTED.value
    has_value = review.get("reliability") is not None
    if permitted != has_value:
        problems.append(f"gate is {gate} and reliability is {review.get('reliability')!r}")

    if has_value and not 0.0 <= float(review["reliability"]) <= 1.0:
        problems.append(f"reliability {review['reliability']} is outside [0, 1]")

    origin = review.get("origin")
    if origin not in {o.value for o in ReliabilityAssessmentOrigin}:
        problems.append(f"origin {origin!r} is not a ReliabilityAssessmentOrigin")

    for item in review.get("basis") or ():
        try:
            ReliabilityBasisType(item["basis_type"])
        except (KeyError, ValueError):
            problems.append(f"basis type {item.get('basis_type')!r} is not a member")
        if not item.get("document_url") or not item.get("retrieved_at"):
            problems.append(f"basis {item.get('document_title')!r} is not document-backed")

    for field in ("rationale", "stated_limitation", "reviewed_by"):
        if not str(review.get(field, "")).strip():
            problems.append(f"{field} is empty, and it is a field only the reviewer can fill")

    return problems


def render(review: dict) -> str:
    lines: list[str] = []
    scope = review["scope"]
    lines.append("# Second pilot — the completed convergent TED reliability review")
    lines.append("")
    lines.append(
        f"**`{review['artifact_version']}`**, performed under "
        f"**`{review['review_rubric']['id']}@{review['review_rubric']['version']}`**. "
        "Authored by the reviewer; this page is rendered from it."
    )
    lines.append("")
    lines.append(
        "**This is a completed review, not a preparation packet** — which is why it "
        "carries a number where the Mission 1.42 packet carried a blank."
    )
    lines.append("")
    lines.append("It is none of these:")
    lines.append("")
    for item in review["what_this_is_not"]:
        lines.append(f"- {item}")
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
    lines.append(review["scope_note"])
    lines.append("")
    covers = review["covers"]
    lines.append(
        f"It binds **{covers['evidence_rows']} Evidence rows across "
        f"{covers['claims']} Claims** — of which {covers['multi_evidence_claims']} carry "
        f"more than one — spanning CPV divisions "
        + ", ".join(f"`{d}`" for d in covers["classification_divisions"])
        + " and currencies "
        + ", ".join(f"`{c}`" for c in covers["currencies"])
        + ", because a reliability scope carries neither."
    )
    lines.append("")
    lines.append("## The profile")
    lines.append("")
    lines.append("| dimension | state |")
    lines.append("|---|---|")
    for dimension in rubric.DIMENSIONS:
        lines.append(f"| `{dimension.id}` | `{review['rubric_profile'][dimension.id]}` |")
    lines.append("")
    lines.append("## Material unknowns")
    lines.append("")
    lines.append("| dimension | not established | material? |")
    lines.append("|---|---|---|")
    for unknown in review["material_unknowns"]:
        lines.append(
            f"| `{unknown['dimension_id']}` | {unknown['what_is_not_established']} | "
            f"**{unknown['reviewer_materiality']}** |"
        )
    lines.append("")
    lines.append(review["material_unknowns_note"])
    lines.append("")
    lines.append("## Hard stops")
    lines.append("")
    triggered = review["hard_stops_triggered"]
    lines.append(
        "**None triggered.** " + review["hard_stops_note"]
        if not triggered
        else "Triggered: " + ", ".join(f"`{h}`" for h in triggered)
    )
    lines.append("")
    lines.append("## The gate, and the judgement")
    lines.append("")
    lines.append(f"**`{review['numeric_judgement_gate']}`.** {review['gate_note']}")
    lines.append("")
    lines.append("```text")
    lines.append(f"reliability   {review['reliability']}")
    lines.append(f"origin        {review['origin']}")
    lines.append(f"reviewer      {review['reviewed_by']}")
    lines.append("```")
    lines.append("")
    lines.append("### Rationale")
    lines.append("")
    for paragraph in review["rationale"].split("\n\n"):
        lines.append(paragraph.strip())
        lines.append("")
    lines.append("### Stated limitation")
    lines.append("")
    lines.append(review["stated_limitation"])
    lines.append("")
    lines.append("## Documentary basis")
    lines.append("")
    lines.append("| type | document | finding |")
    lines.append("|---|---|---|")
    for item in review["basis"]:
        lines.append(
            f"| `{item['basis_type']}` | {item['document_title']} "
            f"(`{item['section_reference']}`, retrieved {item['retrieved_at']}) | "
            f"{item['summarized_finding']} |"
        )
    lines.append("")
    lines.append(review["basis_note"])
    lines.append("")
    lines.append("## Outcome")
    lines.append("")
    persisted = review.get("persisted_assessment")
    if persisted:
        lines.append(
            f"Persisted as assessment `{persisted['id']}` version {persisted['version']}, "
            f"recorded {persisted['recorded_at']}."
        )
    else:
        lines.append(f"**Not yet persisted.** {review['persisted_assessment_note']}")
    lines.append("")
    return "\n".join(lines) + "\n"


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
    print(f"\nwrote {OUT_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
