"""Render the human reliability assessment rubric (Mission 1.42a §26, §27).

Reads two inputs and writes two artifacts:

    sros_evidence_reliability.rubric      the rubric itself, as code
    reliability_rubric_findings.json      the readings of existing material
            |
            v
    docs/data/human-reliability-assessment-rubric-v1.json
    docs/data/human-reliability-assessment-rubric-v1.md

**No database and no network**, deliberately: the rubric is generic and the
worked example reads the Mission 1.42 packet that is already checked in, so
`--check` can run in CI. The packet builder cannot, because it measures a
deployment (`testing-strategy.md` §68).

    python infrastructure/scripts/render_reliability_rubric.py
    python infrastructure/scripts/render_reliability_rubric.py --check
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
OUT_JSON = DOCS / "human-reliability-assessment-rubric-v1.json"
OUT_MD = DOCS / "human-reliability-assessment-rubric-v1.md"
FINDINGS = ROOT / "infrastructure" / "scripts" / "reliability_rubric_findings.json"
PACKET = DOCS / "second-pilot-convergent-reliability-review-packet-v1.json"

from sros_evidence_reliability import rubric  # noqa: E402


def build() -> tuple[dict, str]:
    findings = json.loads(FINDINGS.read_text(encoding="utf-8"))
    packet = json.loads(PACKET.read_text(encoding="utf-8"))
    scope = packet["measured_scopes"][0]["scope"]

    worked = findings["ted_worked_example"]

    document = {
        "$comment": (
            "Mission 1.42a. A decision procedure for converting documented facts into "
            "an accountable human reliability judgement -- and for refusing to, when "
            "the documents do not support one. GENERATED: edit "
            "sros_evidence_reliability/rubric.py or reliability_rubric_findings.json "
            "and re-render. Every judgement field in the worked example is blank and "
            "this generator has no code path that could fill one."
        ),
        "rubric_id": rubric.RUBRIC_ID,
        "rubric_version": rubric.RUBRIC_VERSION,
        "purpose": (
            "Mission 1.14 defined what reliability means, ADR-026 defined the scope it "
            "binds to, and the review guide told a reviewer to write the failure mode "
            "down first. None of them defines the step from documented facts to a "
            "number. This rubric is that step."
        ),
        "reliability_question": rubric.RELIABILITY_QUESTION,
        "excluded_concepts": list(rubric.EXCLUDED_CONCEPTS),
        "review_states": [
            {
                "state": state.value,
                "ordinal_rank": rubric.ORDINAL_RANK[state],
                "$note": (
                    "No rank. A state with no rank cannot be interpolated, averaged, "
                    "or read as the bottom of the scale -- which is how UNKNOWN is "
                    "kept from becoming LOW."
                )
                if rubric.ORDINAL_RANK[state] is None
                else None,
            }
            for state in rubric.ReviewState
        ],
        "ordinal_ranks_are_never_summed": rubric.ORDINAL_RANKS_ARE_NEVER_SUMMED,
        "software_assignable_states": [s.value for s in rubric.SOFTWARE_ASSIGNABLE_STATES],
        "dimensions": [
            {
                "id": d.id,
                "question": d.question,
                "why_reliability_native": d.why_reliability_native,
                "not_to_be_confused_with": d.not_to_be_confused_with,
                "observable_definitions": {
                    state.value: text for state, text in d.observable.items()
                },
            }
            for d in rubric.DIMENSIONS
        ],
        "rejected_dimensions": [
            {"id": r.id, "verdict": r.verdict, "reason": r.reason}
            for r in rubric.REJECTED_DIMENSIONS
        ],
        "hard_stops": [
            {"id": h.id, "condition": h.condition, "why": h.why} for h in rubric.HARD_STOPS
        ],
        "material_unknowns": {
            "definition": rubric.MATERIAL_UNKNOWN_DEFINITION,
            "question_put_to_the_reviewer": rubric.MATERIALITY_QUESTION,
            "permitted_answers": list(rubric.MATERIALITY_ANSWERS),
            "$note": (
                "Software prepares the question and never the answer. UNSURE is a real "
                "answer and is a legitimate reason for the gate not to be PERMITTED."
            ),
        },
        "numeric_judgement_gate": {
            "outcomes": [g.value for g in rubric.NumericJudgementGate],
            "is_computed": False,
            "numeric_value_required_for_every_review": not rubric.NUMERIC_JUDGEMENT_IS_NEVER_REQUIRED,
            "$note": (
                "The gate is a reviewer decision. Only the hard stops are mechanical, "
                "and they make a value UNAVAILABLE rather than low. An outcome other "
                "than PERMITTED is a COMPLETE review: the scope keeps no assessment, "
                "the resolver keeps returning NO_APPLICABLE_ASSESSMENT, and the "
                "Evidence stays NON_SCORABLE."
            ),
        },
        "scale": {
            "range": "[0.0, 1.0]",
            "strategy": rubric.SCALE_STRATEGY,
            "threshold_labels": None,
            "anchors": [
                {"value": a.value, "means": a.means, "justified_when": a.justified_when}
                for a in rubric.ANCHORS
            ],
            "intermediate_anchors": list(rubric.INTERMEDIATE_ANCHORS),
            "$note": (
                "There are no intermediate anchors, deliberately. Nothing in the "
                "repository anchors the absolute scale, so an intermediate anchor "
                "would have to be invented -- which is replacing arbitrary numbers "
                "with different arbitrary numbers. The two anchors that exist are "
                "defined by what the value DOES in q = min(components), not by an "
                "adjective, because the contract forbids threshold vocabulary."
            ),
        },
        "worksheet_schema": [
            {"id": f.id, "prompt": f.prompt, "filled_by": f.filled_by.value}
            for f in rubric.WORKSHEET_SCHEMA
        ],
        "reproducibility_requirements": list(rubric.REPRODUCIBILITY_REQUIREMENTS),
        "disagreement": {
            "states": [s.value for s in rubric.ReviewAgreement],
            "averaging_permitted": not rubric.DISAGREEMENT_IS_NEVER_AVERAGED,
            "already_answered_by_the_existing_architecture": [
                "The resolver refuses when more than one current assessment matches a "
                "scope, so two open answers cannot both be current. The architecture "
                "already says two answers are not an answer.",
                "Supersession is append-only and records who superseded what and why, "
                "so a later review replacing an earlier one is representable today "
                "and the earlier one is retained.",
            ],
            "not_yet_representable": [
                "A second reviewer disagreeing WITHOUT superseding. Today the choice is "
                "to supersede -- which asserts the new review is the right one -- or to "
                "record nothing, which loses the disagreement.",
            ],
            "$note": (
                "Semantics only. Multi-review persistence is not implemented here. "
                "While a disagreement is open the honest state is the absence of an "
                "assessment, which is what the resolver already produces."
            ),
        },
        "model_use_boundary": {
            "an_llm_is_not_an_accountable_reviewer": True,
            "may": list(rubric.MODEL_MAY),
            "may_not": list(rubric.MODEL_MAY_NOT),
            "$note": (
                "There is no MODEL_GUESSED origin in ReliabilityAssessmentOrigin, and "
                "closure is what makes this enforceable rather than merely stated."
            ),
        },
        "historical_compatibility": findings["historical_compatibility"],
        "provenance_gap": findings["provenance_gap"],
        "worked_example": {
            "$comment": (
                "§20-§23. The rubric was frozen before it was applied, and the "
                "application stops at the first judgement. Every reviewer field below "
                "is blank."
            ),
            "scope": scope,
            "affected": {
                "evidence_rows": len(packet["affected_rows"]),
                "claims": len({r["claim_id"] for r in packet["affected_rows"]}),
                "resolver_outcome": packet["measured_scopes"][0]["outcome"],
            },
            "dimension_findings": worked["dimension_findings"],
            "material_unknown_candidates": [
                {
                    **candidate,
                    "materiality_question": rubric.MATERIALITY_QUESTION,
                    "reviewer_answer": None,
                }
                for candidate in worked["material_unknown_candidates"]
            ],
            "not_a_rubric_input": worked["not_a_rubric_input"],
            "reviewer_fields": rubric.blank_reviewer_fields(),
            "sufficient_for_numeric_judgement": "UNANSWERED",
        },
    }
    return document, render_markdown(document)


def _states_table(dimension: dict) -> list[str]:
    lines = ["| state | what it looks like |", "|---|---|"]
    for state, text in dimension["observable_definitions"].items():
        lines.append(f"| `{state}` | {text} |")
    return lines


def render_markdown(doc: dict) -> str:
    lines: list[str] = []
    lines.append("# The human reliability assessment rubric")
    lines.append("")
    lines.append(
        f"**`{doc['rubric_id']}@{doc['rubric_version']}`.** Generated from "
        "`sros_evidence_reliability/rubric.py`; edit that, not this."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 0. The gap this closes")
    lines.append("")
    lines.append(doc["purpose"])
    lines.append("")
    lines.append("```text")
    lines.append("DOCUMENTED FACTS  ->  [ this rubric ]  ->  HUMAN JUDGEMENT  ->  Assessment")
    lines.append("```")
    lines.append("")
    lines.append(
        "**The gap was never decimal precision.** A reviewer who has read every "
        "document and written the failure mode down still had no procedure that made "
        "one number rather than a neighbouring one defensible."
    )
    lines.append("")
    lines.append("## 1. The question, unchanged")
    lines.append("")
    lines.append(f"> **{doc['reliability_question']}**")
    lines.append("")
    lines.append("It is never any of these:")
    lines.append("")
    for item in doc["excluded_concepts"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 2. Review states")
    lines.append("")
    lines.append(
        "One vocabulary across every dimension, so a reviewer learns it once. **Three "
        "are ordered and two are deliberately off the order** — that is the structural "
        "form of *UNKNOWN is not LOW*."
    )
    lines.append("")
    lines.append("| state | rank |")
    lines.append("|---|---|")
    for entry in doc["review_states"]:
        rank = entry["ordinal_rank"]
        lines.append(f"| `{entry['state']}` | {rank if rank is not None else '**none**'} |")
    lines.append("")
    lines.append(
        "A state with no rank cannot be interpolated, averaged, or read as the bottom "
        "of a scale. `NOT_ESTABLISHED` is the absence of an answer, not a worse one; "
        "`CONTRADICTED` is a blocker, not a weak position."
    )
    lines.append("")
    lines.append(
        "**The ranks order the three documented states and are never arithmetic.** "
        "Nothing sums them, averages them, weights them, or maps one to a reliability "
        "value — a rank that could be added up would be a points system with a "
        "vocabulary in front of it."
    )
    lines.append("")
    lines.append(
        "**Software may assert exactly one of them:** "
        + ", ".join(f"`{s}`" for s in doc["software_assignable_states"])
        + " — because *no document in this review's basis addresses this question* is a "
        "checkable claim about the corpus. Every other state judges whether what is "
        "documented is *enough*, and that is the reviewer's."
    )
    lines.append("")
    lines.append("## 3. The dimensions")
    lines.append("")
    for dimension in doc["dimensions"]:
        lines.append(f"### {dimension['id']}")
        lines.append("")
        lines.append(f"> {dimension['question']}")
        lines.append("")
        lines.append(f"**Why this is reliability.** {dimension['why_reliability_native']}")
        lines.append("")
        lines.append(f"**Not to be confused with** {dimension['not_to_be_confused_with']}")
        lines.append("")
        lines.extend(_states_table(dimension))
        lines.append("")
    lines.append("## 4. What was rejected, and why")
    lines.append("")
    lines.append(
        "Reliability sits beside relevance, directness, extraction confidence and "
        "freshness in `q = min(components)`. A rubric that quietly re-scored one of "
        "them would make a single weakness count twice."
    )
    lines.append("")
    lines.append("| candidate | verdict | reason |")
    lines.append("|---|---|---|")
    for rejected in doc["rejected_dimensions"]:
        lines.append(f"| `{rejected['id']}` | **{rejected['verdict']}** | {rejected['reason']} |")
    lines.append("")
    lines.append("## 5. Hard stops")
    lines.append("")
    lines.append(
        "Each of these makes a numeric judgement **unavailable**, however strong the "
        "rest — because the reliability question has no answer in that situation, not "
        "because the answer would be low."
    )
    lines.append("")
    for stop in doc["hard_stops"]:
        lines.append(f"- **`{stop['id']}`** — {stop['condition']} {stop['why']}")
    lines.append("")
    lines.append("## 6. Material unknowns")
    lines.append("")
    lines.append(doc["material_unknowns"]["definition"])
    lines.append("")
    lines.append(
        f"For each thing the documents do not establish, the reviewer answers: "
        f"*{doc['material_unknowns']['question_put_to_the_reviewer']}* — "
        + " / ".join(f"`{a}`" for a in doc["material_unknowns"]["permitted_answers"])
        + "."
    )
    lines.append("")
    lines.append(
        "**A material unknown does not automatically refuse the review**, and an "
        "unknown is not material merely because something is undocumented. Most things "
        "are undocumented."
    )
    lines.append("")
    lines.append("## 7. The numeric-judgement gate")
    lines.append("")
    for outcome in doc["numeric_judgement_gate"]["outcomes"]:
        lines.append(f"- `{outcome}`")
    lines.append("")
    lines.append(
        "**It is not computed.** Only the hard stops are mechanical. Everything else "
        "is the reviewer's, recorded against the profile they just filled in."
    )
    lines.append("")
    lines.append(
        "**A numeric value is not required.** An outcome other than "
        "`NUMERIC_JUDGEMENT_PERMITTED` is a *complete* review: the scope keeps no "
        "assessment, the resolver keeps returning `NO_APPLICABLE_ASSESSMENT`, and the "
        "Evidence stays `NON_SCORABLE`. That is the designed behaviour."
    )
    lines.append("")
    lines.append("## 8. The scale")
    lines.append("")
    lines.append(f"**Recommendation: `{doc['scale']['strategy']}`.**")
    lines.append("")
    lines.append(
        "The numeric field stays — no migration, no code change, and the two existing "
        "assessments keep their values — and the rubric requires the **ordinal profile "
        "to be completed before the number is offered**. The number then summarises a "
        "recorded profile, and the profile is what a second reviewer reproduces."
    )
    lines.append("")
    lines.append("Two anchors, each defined by what the value *does*, never by an adjective:")
    lines.append("")
    for anchor in doc["scale"]["anchors"]:
        lines.append(f"- **`{anchor['value']}`** — {anchor['means']}")
        lines.append(f"  - Justified when: {anchor['justified_when']}")
    lines.append("")
    lines.append(
        "**There are no intermediate anchors.** Nothing in this repository anchors the "
        "absolute scale — the reliability contract forbids threshold labels for that "
        "reason, and Mission 1.37 found only the ordinal construct defined. An "
        "intermediate anchor would have to be invented, and inventing one is replacing "
        "arbitrary numbers with different arbitrary numbers."
    )
    lines.append("")
    lines.append("## 9. Disagreement between reviewers")
    lines.append("")
    lines.append("| state | |")
    lines.append("|---|---|")
    for state in doc["disagreement"]["states"]:
        lines.append(f"| `{state}` | |")
    lines.append("")
    lines.append(
        "**Two reviews are never averaged.** The mean of two judgements is a "
        "judgement nobody made and nobody can be asked about."
    )
    lines.append("")
    lines.append("Already answered by the existing architecture:")
    lines.append("")
    for item in doc["disagreement"]["already_answered_by_the_existing_architecture"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Not yet representable:")
    lines.append("")
    for item in doc["disagreement"]["not_yet_representable"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 10. An LLM is not an accountable reviewer")
    lines.append("")
    lines.append("**May:**")
    lines.append("")
    for item in doc["model_use_boundary"]["may"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("**May not:**")
    lines.append("")
    for item in doc["model_use_boundary"]["may_not"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 11. The worksheet")
    lines.append("")
    lines.append("| field | filled by |")
    lines.append("|---|---|")
    for field in doc["worksheet_schema"]:
        lines.append(f"| **{field['id']}** — {field['prompt']} | `{field['filled_by']}` |")
    lines.append("")
    lines.append(
        "**No field is prefilled with a reliability value**, and there is no other slot "
        "on the worksheet where one could go."
    )
    lines.append("")
    lines.append("## 12. Reproducibility")
    lines.append("")
    lines.append(
        "A second qualified reviewer, given the same scope, the same documentary basis "
        "and the same rubric version, must be able to follow the first reviewer's "
        "reasoning. **Perfect agreement is not required. Traceability is.** The minimum "
        "record:"
    )
    lines.append("")
    for item in doc["reproducibility_requirements"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 13. The two existing assessments")
    lines.append("")
    hist = doc["historical_compatibility"]
    lines.append(
        "Applied **structurally** and not re-reviewed. Neither value, rationale, "
        "limitation, version nor basis row is changed, and neither was used to derive "
        "an anchor."
    )
    lines.append("")
    lines.append("| scope | verdict | dimensions reached | not addressed |")
    lines.append("|---|---|---|---|")
    for entry in hist["assessments"]:
        reached = ", ".join(f"`{d['dimension_id']}`" for d in entry["dimensions_addressed"])
        missing = ", ".join(f"`{d}`" for d in entry["dimensions_not_addressed"])
        lines.append(
            f"| `{entry['scope_proposition_kind']}` | **{entry['verdict']}** | "
            f"{reached} | {missing} |"
        )
    lines.append("")
    for entry in hist["assessments"]:
        lines.append(f"- **`{entry['scope_proposition_kind']}`** — {entry['note']}")
    lines.append("")
    lines.append(f"**Combined: `{hist['combined_finding']}`.** {hist['combined_note']}")
    lines.append("")
    lines.append("## 14. Rubric provenance")
    lines.append("")
    gap = doc["provenance_gap"]
    lines.append(f"**`{gap['finding']}`.** {gap['what_is_missing']}")
    lines.append("")
    lines.append(f"{gap['why_the_basis_table_is_not_the_answer']}")
    lines.append("")
    lines.append(f"**Narrowest repair, recommended and not performed:** {gap['narrowest_repair']}")
    lines.append("")
    lines.append(f"**Materiality.** {gap['materiality']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 15. Worked example — the TED convergent scope")
    lines.append("")
    example = doc["worked_example"]
    lines.append(
        "The rubric was frozen before it met this scope, and the application stops at "
        "the first judgement."
    )
    lines.append("")
    lines.append("```text")
    for key, value in example["scope"].items():
        lines.append(f"{key:18}{value}")
    lines.append("```")
    lines.append("")
    lines.append(
        f"**{example['affected']['evidence_rows']} Evidence rows across "
        f"{example['affected']['claims']} Claims**, resolver "
        f"`{example['affected']['resolver_outcome']}`."
    )
    lines.append("")
    lines.append("### Factual findings, by dimension")
    lines.append("")
    for finding in example["dimension_findings"]:
        state = finding["software_assigned_state"]
        suffix = f" — state `{state}`" if state else ""
        lines.append(f"**`{finding['dimension_id']}`**{suffix}")
        lines.append("")
        for fact in finding["facts"]:
            lines.append(f"- {fact}")
        lines.append("")
    lines.append(
        "Only `NOT_ESTABLISHED` is filled in above, and only where the claim is about "
        "what this review's basis contains. **Every other state is yours.**"
    )
    lines.append("")
    lines.append("### Material unknowns — materiality is the reviewer's")
    lines.append("")
    for candidate in example["material_unknown_candidates"]:
        lines.append(f"**`{candidate['dimension_id']}`** — {candidate['what_is_not_established']}")
        lines.append("")
        lines.append(f"> {candidate['materiality_question']}")
        lines.append("")
        lines.append("```text")
        lines.append("YES / NO / UNSURE   ______")
        lines.append("```")
        lines.append("")
    lines.append("### Not a rubric input")
    lines.append("")
    for item in example["not_a_rubric_input"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### Your judgement")
    lines.append("")
    lines.append("```text")
    lines.append(
        f"SUFFICIENT_FOR_NUMERIC_JUDGEMENT   {example['sufficient_for_numeric_judgement']}"
    )
    for key in example["reviewer_fields"]:
        lines.append(f"{key:34} ______________________________")
    lines.append("```")
    lines.append("")
    lines.append(
        "**No value is supplied, suggested or implied**, and no reviewer is inferred "
        "from a git author, a PR author, an OS username, an existing assessment or a "
        "conversation."
    )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare and write nothing")
    args = parser.parse_args()

    document, markdown = build()
    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        drift = []
        for path, expected in ((OUT_JSON, rendered), (OUT_MD, markdown)):
            if not path.exists():
                print(f"REFUSED: {path.name} does not exist; run without --check first")
                return 1
            if path.read_text(encoding="utf-8") != expected:
                drift.append(path.name)
        if drift:
            for name in drift:
                print(f"DRIFT    {name} does not match the rubric")
            return 1
        print(f"ok       {OUT_JSON.name} and {OUT_MD.name} match the rubric")
        return 0

    OUT_JSON.write_text(rendered, encoding="utf-8")
    OUT_MD.write_text(markdown, encoding="utf-8")

    print(f"rubric              : {rubric.RUBRIC_ID}@{rubric.RUBRIC_VERSION}")
    print(f"dimensions accepted : {len(rubric.DIMENSIONS)}")
    print(f"dimensions rejected : {len(rubric.REJECTED_DIMENSIONS)}")
    print(f"hard stops          : {len(rubric.HARD_STOPS)}")
    print(
        f"anchors             : {len(rubric.ANCHORS)} (intermediate: {len(rubric.INTERMEDIATE_ANCHORS)})"
    )
    print(f"scale strategy      : {rubric.SCALE_STRATEGY}")
    print(f"reviewer fields     : {sorted(rubric.blank_reviewer_fields())} -- all blank")
    print()
    print(f"wrote {OUT_JSON.name}")
    print(f"wrote {OUT_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
