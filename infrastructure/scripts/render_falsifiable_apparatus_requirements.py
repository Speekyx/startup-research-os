"""Render and validate the Mission 1.48 apparatus-requirements record.

Reads the requirements record and the trade-off record, writes the Markdown
beside the first. `validate()` refuses the shapes this mission exists to avoid,
so a later edit cannot quietly turn a negative architecture finding into a
selected source, or a monotone proposition family into a falsifiable one.

Wired into CI: repository files into a repository file, deterministic from an
empty database. The section 0 BASELINE is a separate artifact and is
deliberately NOT checked in CI, because it measures a deployment (Mission 1.37).

    uv run python infrastructure/scripts/render_falsifiable_apparatus_requirements.py
    uv run python infrastructure/scripts/render_falsifiable_apparatus_requirements.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "data" / "falsifiable-evidence-apparatus-requirements-v1.json"
TRADEOFF = ROOT / "docs" / "data" / "falsifiability-vs-convergence-tradeoff-v1.json"
OUT = ROOT / "docs" / "data" / "falsifiable-evidence-apparatus-requirements-v1.md"

ALLOWED_OUTCOMES = frozenset(
    {
        "FALSIFIABLE_APPARATUS_REQUIREMENTS_DEFINED",
        "PREFERRED_INDEPENDENT_CORROBORATION_APPARATUS_SHAPE_DEFINED",
        "PREFERRED_CONTRADICTION_APPARATUS_SHAPE_DEFINED",
        "BOTH_ROUTES_REQUIRE_NEW_MEASUREMENT_APPARATUS",
        "CONTRADICTION_CLAIM_IDENTITY_ARCHITECTURE_GAP",
        "CONTRADICTION_ARCHITECTURE_REACHABILITY_GAP",
        "REGISTERED_PORTFOLIO_CONTAINS_PROMISING_APPARATUS_CLASS",
        "NO_REVIEWABLE_FALSIFIABLE_APPARATUS_ROUTE_IDENTIFIED",
        "MISSION_1_48_BASELINE_DRIFT",
        "MISSION_1_47_NOT_MERGED",
        "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
        "FALSIFIABLE_APPARATUS_GAP_DEFINITION_BLOCKED",
    }
)

QUALITATIVE = frozenset({"STRONG", "MEDIUM", "WEAK", "NOT_APPLICABLE", "NOT_ESTABLISHED"})
CRITERIA = (
    "FALSIFIABILITY",
    "SAME_PROPOSITION_MATCHABILITY",
    "INDEPENDENT_MEASUREMENT_PLAUSIBILITY",
    "CONTRADICTION_CAPABILITY",
    "RELIABILITY_REVIEWABILITY",
    "SOURCE_NATIVE_SEMANTICS",
    "CALIBRATION_INFORMATION_VALUE",
    "CURRENT_MODEL_FIT",
)
CANDIDATE_STATES = frozenset(
    {
        "PROMISING_FROM_EXISTING_DOCUMENTATION",
        "INSUFFICIENT_INFORMATION",
        "KNOWN_MISMATCH",
        "GOVERNANCE_BLOCKED",
        "NOT_RELEVANT",
    }
)
REQUIRED_APPARATUS_FIELDS = (
    "apparatus_observes",
    "apparatus_emits",
    "subject_granularity",
    "time_granularity",
    "unit_semantics",
    "population_or_geography_semantics",
    "methodology_documentation",
    "lineage_documentation",
    "upstream_producer",
    "revision_policy",
    "observation_recoverability",
    "measurement_definition",
    "missingness",
    "independence_comparability",
    "contradiction_comparability",
)


class ValidationError(Exception):
    """The record asserts something this mission is not permitted to assert."""


def validate(record: dict, tradeoff: dict) -> None:
    outcome = record.get("primary_outcome")
    if outcome not in ALLOWED_OUTCOMES:
        raise ValidationError(f"primary_outcome {outcome!r} is not a section 37 outcome")

    # Section 2 / section 11. A monotone family cannot be falsifiable and cannot
    # be contradiction-capable. This is the invariant the whole mission rests on.
    for family in tradeoff.get("proposition_families", []):
        name = family["id"]
        if family.get("monotone"):
            if family.get("falsifiable"):
                raise ValidationError(
                    f"{name} is marked monotone AND falsifiable. A monotone existential "
                    "has no falsifier: a counterexample does not refute it."
                )
            if family.get("CONTRADICTION_CAPABILITY") != "NOT_APPLICABLE":
                raise ValidationError(
                    f"{name} is monotone, so CONTRADICTION_CAPABILITY must be "
                    f"NOT_APPLICABLE, not {family.get('CONTRADICTION_CAPABILITY')!r}."
                )
            if not str(family.get("falsifier", "")).startswith("NONE"):
                raise ValidationError(f"{name} is monotone and names a falsifier")
        elif not family.get("falsifiable"):
            raise ValidationError(
                f"{name} is non-monotone and not falsifiable, which this record does "
                "not define a meaning for"
            )
        for criterion in CRITERIA:
            value = family.get(criterion)
            if value not in QUALITATIVE:
                raise ValidationError(
                    f"{name}.{criterion} is {value!r}; section 5 allows only {sorted(QUALITATIVE)}"
                )
        if isinstance(family.get(criterion), (int, float)):  # pragma: no cover - defensive
            raise ValidationError("section 5 forbids weighted numeric scores")

    # The preferred family must be one that was actually evaluated, and must be
    # capable of the thing it was preferred for.
    preferred = record.get("preferred_proposition_family", {})
    selected = preferred.get("selected")
    if selected is not None:
        families = {f["id"]: f for f in tradeoff.get("proposition_families", [])}
        if selected not in families:
            raise ValidationError(f"preferred family {selected!r} was never evaluated")
        chosen = families[selected]
        if chosen.get("monotone"):
            raise ValidationError(
                f"preferred family {selected} is monotone, so it can never be "
                "contradicted and cannot serve either route"
            )
        if not chosen.get("falsifiable"):
            raise ValidationError(f"preferred family {selected} is not falsifiable")

    # Section 18. A candidate is a candidate, never a selection.
    unheld = record.get("registered_but_unheld", {})
    candidates = unheld.get("candidates", [])
    if len(candidates) > 3:
        raise ValidationError(
            f"section 18 permits at most three future candidates; {len(candidates)} recorded"
        )
    for candidate in candidates:
        if candidate.get("state") not in CANDIDATE_STATES:
            raise ValidationError(
                f"{candidate.get('source_id')} state {candidate.get('state')!r} is not a "
                "section 18 state"
            )
    if unheld.get("no_source_was_selected") is not True:
        raise ValidationError(
            "section 18 candidates are not selected acquisition routes; the record must "
            "say so explicitly"
        )

    # Section 6. A specification with a blank field is not a search specification.
    apparatus = record.get("apparatus_requirements", {})
    for field in REQUIRED_APPARATUS_FIELDS:
        value = apparatus.get(field)
        if not value or not str(value).strip():
            raise ValidationError(f"apparatus_requirements.{field} is empty")

    # Central principle: the specification is written from the evidence
    # requirement backwards, so it may not name a source, vendor or product.
    #
    # Matched on TOKEN boundaries, never as substrings. A substring scan for
    # `ted` fires on "documented", "attributed" and "collected", which is
    # `testing-strategy.md` §23 in its purest form: the scan failing on the very
    # prose that does the work. Mission 1.13.1 met this and fixed it the same
    # way -- `supermarket` is not `market`. The first draft of this guard was
    # a substring scan and it refused this record on "documented".
    forbidden = (
        r"wikimedia",
        r"stack\s*overflow",
        r"stack\s*exchange",
        r"ted-eu",
        r"world\s+bank",
        r"docker",
        r"eurostat",
        r"fred",
        r"gdelt",
        r"usaspending",
    )
    spec_text = " ".join(str(apparatus.get(f, "")) for f in REQUIRED_APPARATUS_FIELDS).lower()
    for name in forbidden:
        if re.search(rf"(?<![a-z]){name}(?![a-z])", spec_text):
            raise ValidationError(
                f"apparatus_requirements names {name!r}. The specification must be "
                "written from the evidence requirement backwards, not around a source."
            )

    counters = record.get("counters", {})
    moved = [
        name
        for name, pair in counters.items()
        if isinstance(pair, dict) and pair.get("before") != pair.get("after")
    ]
    if moved:
        raise ValidationError(f"section 24 requires every counter unchanged; these moved: {moved}")

    budget = record.get("network_budget", {})
    for key in (
        "RESEARCH_DATA_REQUESTS",
        "APPARATUS_DOCUMENTATION_REQUESTS",
        "GOVERNANCE_DOCUMENT_REQUESTS",
    ):
        if budget.get(key) != 0:
            raise ValidationError(f"section 25 expects {key} = 0")

    model = record.get("model_use", {})
    if model.get("llm_calls") != 0 or model.get("embeddings") != 0:
        raise ValidationError("section 26 expects 0 model calls and 0 embeddings")
    if model.get("problem_family_status") != "PARKED":
        raise ValidationError("section 26 requires Problem-Family to remain PARKED")

    # Section 27. This mission defines reviewability criteria and never a value.
    if "reliability_value" in json.dumps(record).lower():
        raise ValidationError("section 27 forbids assigning or suggesting a reliability value")


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render(record: dict, tradeoff: dict) -> str:
    lines: list[str] = []
    add = lines.append

    add("# Falsifiable Evidence Apparatus Requirements V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit")
    add("> `falsifiable-evidence-apparatus-requirements-v1.json` and re-run")
    add("> `infrastructure/scripts/render_falsifiable_apparatus_requirements.py`.")
    add("")
    add(f"## Primary outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")

    unification = record["the_unification"]
    add("## The unification")
    add("")
    add(unification["statement"])
    add("")
    add(f"**Consequence.** {unification['consequence']}")
    add("")
    add(f"*Measured:* {unification['measured']}")
    add("")
    add(f"*Not a bug:* {unification['not_a_bug']}")
    add("")

    add("## §0 — Reconstructed from live code")
    add("")
    for key, block in record["structural_reconstruction"].items():
        if key.startswith("$"):
            continue
        add(f"**{key}** — established: **{block['established']}**")
        add("")
        add(f"- how: {block['how']}")
        add(f"- result: {block['result']}")
        for extra in ("why_algebraic", "conclusion"):
            if extra in block:
                add(f"- {extra.replace('_', ' ')}: {block[extra]}")
        add("")

    add("## §9 — Why contradiction is unreachable")
    add("")
    why = record["why_contradiction_is_unreachable"]
    add(f"**Verdict: `{why['verdict']}`.**")
    add("")
    for key in (
        "blocker_1_direction_is_identity",
        "blocker_2_no_interpreter_can_emit_contradicts",
        "blocker_3_source_id_is_identity",
    ):
        block = why[key]
        add(f"### {key.replace('_', ' ')}")
        add("")
        add(f"- **Fact.** {block['fact']}")
        if "quoted_reason" in block:
            add(f"- {block['quoted_reason']}")
        add(f"- **Consequence.** {block['consequence']}")
        if "live_evidence" in block:
            add(f"- *Live evidence:* {block['live_evidence']}")
        if "note" in block:
            add(f"- *Note:* {block['note']}")
        add("")
    add(f"*{why['is_it_repairable_here']}*")
    add("")

    add("## §10 — Source attribution and contradiction")
    add("")
    attribution = record["source_attribution_and_contradiction"]
    add(attribution["the_semantic_problem"])
    add("")
    add(
        f"**What a real cross-source contradiction requires: option {attribution['what_a_real_cross_source_contradiction_requires']}.**"
    )
    add("")
    add(_row(["option", "description", "status"]))
    add(_row(["---", "---", "---"]))
    for option in attribution["options_considered"]:
        add(_row([option["option"], option["description"], f"`{option['status']}`"]))
    add("")
    for option in attribution["options_considered"]:
        add(f"**{option['option']}.** {option['assessment']}")
        add("")
    add(f"*{attribution['source_id_was_not_removed']}*")
    add("")

    add("## §1 / §11 — Falsifiability, and the trade-off")
    add("")
    definition = tradeoff["falsifiability_definition"]
    add("A Claim is falsifiable here when it states:")
    add("")
    for item in definition["a_claim_is_falsifiable_here_when_it_states"]:
        add(f"- {item}")
    add("")
    add(f"**The decisive test.** {definition['and_the_decisive_test']}")
    add("")
    add(f"*{definition['why_that_test']}*")
    add("")
    add(
        _row(
            ["family", "monotone", "falsifiable", *[c.lower().replace("_", " ") for c in CRITERIA]]
        )
    )
    add(_row(["---"] * (3 + len(CRITERIA))))
    for family in tradeoff["proposition_families"]:
        add(
            _row(
                [
                    f"`{family['id']}`",
                    "**yes**" if family["monotone"] else "no",
                    "yes" if family["falsifiable"] else "**no**",
                    *[family[c] for c in CRITERIA],
                ]
            )
        )
    add("")
    trade = tradeoff["the_tradeoff"]
    add(f"**{trade['statement']}**")
    add("")
    add(f"*Why:* {trade['why']}")
    add("")
    add(f"*Observed, not predicted:* {trade['observed_not_predicted']}")
    add("")

    add("### The live demonstration")
    add("")
    demo = tradeoff["live_demonstration"]
    add(
        f"{demo['claim_pairs_differing_only_in_direction']} Claim pairs in the corpus differ "
        f"ONLY in `direction`, over {', '.join(f'`{s}`' for s in demo['subjects'])}:"
    )
    add("")
    for statement in demo["pair"]:
        add(f"> {statement}")
        add("")
    for key in ("reason_1_two_claims", "reason_2_jointly_true", "reason_3_monotone"):
        add(f"- {demo[key]}")
    add("")
    add(f"**{demo['conclusion']}**")
    add("")

    add("## §5 — Preferred proposition family")
    add("")
    preferred = record["preferred_proposition_family"]
    add(f"**`{preferred['selected']}`** — {preferred['shape']}")
    add("")
    add(f"**Why.** {preferred['why_selected']}")
    add("")
    for key in (
        "why_not_exact_point_value",
        "why_not_exact_direction",
        "why_not_the_existential_families",
    ):
        add(f"- {preferred[key]}")
    add("")
    add(f"**The cost of the choice.** {preferred['the_cost_of_the_choice']}")
    add("")
    add(
        f"Current model fit: **{preferred['current_model_fit']}** — {preferred['current_model_fit_reason']}"
    )
    add("")

    add("## §6 — Apparatus requirements")
    add("")
    add("*A search specification for a future mission. It names no source, vendor,")
    add("API or product, deliberately: the question is what an apparatus must")
    add("observe, before who publishes such data.*")
    add("")
    add(_row(["requirement", "must be"]))
    add(_row(["---", "---"]))
    for field in REQUIRED_APPARATUS_FIELDS:
        add(_row([f"`{field}`", record["apparatus_requirements"][field]]))
    add("")

    add("## §14 — Falsifier specification")
    add("")
    falsifier = record["falsifier_specification"]
    add(f"**Claim.** {falsifier['claim']}")
    add("")
    for key in (
        "SUPPORT_CONDITION",
        "CONTRADICT_CONDITION",
        "NON_EVIDENCE_CONDITION",
        "SEMANTIC_MISMATCH_CONDITION",
        "UNKNOWN_CONDITION",
    ):
        add(f"- **`{key}`** — {falsifier[key]}")
    add("")

    add("## §4 — What is not a contradiction")
    add("")
    add(_row(["case", "why not"]))
    add(_row(["---", "---"]))
    for case in record["not_a_contradiction"]["cases"]:
        add(_row([case["case"], case["why"]]))
    add("")

    add("## §7 / §8 — Pair templates")
    add("")
    independence = record["independence_capable_pair_template"]
    add("**Independence-capable pair.** Shared claim:")
    add("")
    add(f"> {independence['shared_claim']}")
    add("")
    add("Independence proof requires:")
    add("")
    for item in independence["independence_proof_requires"]:
        add(f"- {item}")
    add("")
    add(f"*Explicitly insufficient:* {independence['explicitly_insufficient']}")
    add("")
    contradiction = record["contradiction_capable_pair_template"]
    add("**Contradiction-capable pair.** Claim:")
    add("")
    add(f"> {contradiction['claim']}")
    add("")
    add(f"- Evidence A — {contradiction['evidence_A']}")
    add(f"- Evidence B — {contradiction['evidence_B']}")
    add(f"- Both must share: {', '.join(contradiction['both_must_share'])}, {contradiction['or']}")
    add("")
    add(f"**Blocked today by.** {contradiction['blocked_today_by']}")
    add("")

    add("## §15 — Reliability reviewability gate")
    add("")
    gate = record["reliability_reviewability_gate"]
    add(f"**{gate['rule']}**")
    add("")
    for item in gate["minimum"]:
        add(f"- {item}")
    add("")
    add(f"*Why first class:* {gate['why_first_class']}")
    add("")
    add(f"*Consequence for search:* {gate['consequence_for_search']}")
    add("")

    add("## §16 — Governance compatibility gate")
    add("")
    for item in record["governance_compatibility_gate"]["requirements"]:
        add(f"- {item}")
    add("")
    add(f"*{record['governance_compatibility_gate']['separate_gate']}*")
    add("")

    add("## §17 — Held apparatus matrix")
    add("")
    matrix = record["portfolio_matrix"]
    columns = [
        "FALSIFIABLE_POINT_CLAIM",
        "DOCUMENTED_LINEAGE",
        "POTENTIAL_SECOND_MEASUREMENT",
        "CONTRADICTION_CAPABLE",
        "SAME_SUBJECT_PARTNER",
        "RELIABILITY_REVIEWABLE",
        "CURRENTLY_ELIGIBLE",
        "CURRENTLY_HELD",
    ]
    add(_row(["apparatus"] + [c.lower().replace("_", " ") for c in columns]))
    add(_row(["---"] * (len(columns) + 1)))
    for row in matrix["held_apparatuses"]:
        add(_row([f"`{row['apparatus']}`"] + [row[c] for c in columns]))
    add("")
    add(f"**{matrix['finding']}**")
    add("")
    add(f"*{matrix['note_on_world_bank']}*")
    add("")

    add("## §18 — Registered but unheld")
    add("")
    unheld = record["registered_but_unheld"]
    eligibility = unheld["live_eligibility_measured"]
    add(
        f"Measured live: **{eligibility['eligible']}** eligible of "
        f"**{eligibility['total_registered']}** registered, "
        f"**{eligibility['eligible_with_collector']}** with a collector, "
        f"**{eligibility['blocked_at_the_eligibility_gate']}** blocked at the gate."
    )
    add("")
    for candidate in unheld["candidates"]:
        add(f"- **`{candidate['source_id']}`** — `{candidate['state']}`. {candidate['why']}")
    add("")
    add(f"**{unheld['conclusion']}**")
    add("")

    add("## §20 / §21 — Route comparison and calibration relevance")
    add("")
    route = record["route_comparison"]
    add(f"**Result: `{route['result']}`.** {route['why']}")
    add("")
    add(
        f"**Preferable once unblocked: {route['which_is_preferable_once_unblocked']}.** {route['why_preferable']}"
    )
    add("")
    add(f"*{route['and_the_asymmetry_worth_recording']}*")
    add("")
    calibration = record["calibration_relevance"]
    add(
        f"- `STRUCTURALLY_IDENTIFYING`: **{calibration['STRUCTURALLY_IDENTIFYING']}** — {calibration['structurally_identifying_why']}"
    )
    add(
        f"- `SEMANTICALLY_USEFUL`: **{calibration['SEMANTICALLY_USEFUL']}** — {calibration['semantically_useful_why']}"
    )
    add("")

    add("## §22 — Opportunity usefulness")
    add("")
    usefulness = record["opportunity_usefulness"]
    for item in usefulness["supports"]:
        add(f"- {item}")
    add("")
    add(f"**Does not support.** {usefulness['does_not_support']}")
    add("")
    add(f"*{usefulness['note']}*")
    add("")

    add("## Counters and budget")
    add("")
    add(_row(["counter", "before", "after"]))
    add(_row(["---", "---:", "---:"]))
    for name, pair in record["counters"].items():
        if isinstance(pair, dict):
            add(_row([name, str(pair["before"]), str(pair["after"])]))
    add("")
    budget = record["network_budget"]
    add(
        f"`RESEARCH_DATA_REQUESTS` **{budget['RESEARCH_DATA_REQUESTS']}**, "
        f"`APPARATUS_DOCUMENTATION_REQUESTS` **{budget['APPARATUS_DOCUMENTATION_REQUESTS']}**, "
        f"`GOVERNANCE_DOCUMENT_REQUESTS` **{budget['GOVERNANCE_DOCUMENT_REQUESTS']}**. "
        f"{budget['note']}"
    )
    add("")
    model = record["model_use"]
    add(
        f"Model calls **{model['llm_calls']}**, {model['usd']:.2f} USD, embeddings "
        f"**{model['embeddings']}**, Problem-Family **{model['problem_family_status']}**."
    )
    add("")

    add("## Next mission")
    add("")
    recommendation = record["next_mission_recommendation"]
    add(f"**Not candidate discovery.** {recommendation['not_candidate_discovery']}")
    add("")
    add(f"**Recommended.** {recommendation['recommended']}")
    add("")
    add(f"*{recommendation['the_specification_is_frozen_for_later']}*")
    add("")
    add(f"*{recommendation['explicitly_not_started']}*")
    add("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    record = json.loads(SRC.read_text(encoding="utf-8"))
    tradeoff = json.loads(TRADEOFF.read_text(encoding="utf-8"))
    try:
        validate(record, tradeoff)
    except ValidationError as error:
        print(f"REFUSED  {SRC.name}: {error}")
        return 1

    text = render(record, tradeoff)

    if args.check:
        if not OUT.exists():
            print(f"DRIFT    {OUT.name} does not exist")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {OUT.name} does not match {SRC.name}")
            return 1
        print(f"ok       {OUT.name} matches {SRC.name}")
        return 0

    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {OUT.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(f"family   {record['preferred_proposition_family']['selected']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
