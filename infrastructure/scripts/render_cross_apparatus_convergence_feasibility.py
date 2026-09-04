"""Render and validate the Mission 1.47 cross-apparatus convergence record.

Reads `docs/data/cross-apparatus-convergence-feasibility-v1.json` and writes the
Markdown beside it. `validate()` refuses the shapes this mission exists to avoid,
so a later edit cannot quietly turn a negative feasibility finding into a route.

Wired into CI: unlike the section 0 holdings baseline, this renders a repository
file into a repository file, so it is deterministic from an empty database
(Mission 1.37).

    uv run python infrastructure/scripts/render_cross_apparatus_convergence_feasibility.py
    uv run python infrastructure/scripts/render_cross_apparatus_convergence_feasibility.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "data" / "cross-apparatus-convergence-feasibility-v1.json"
OUT = ROOT / "docs" / "data" / "cross-apparatus-convergence-feasibility-v1.md"

# Section 36. Exactly these, and the mission must use exactly one.
ALLOWED_OUTCOMES = frozenset(
    {
        "CROSS_APPARATUS_OBSERVED_CONVERGENCE_FEASIBLE",
        "CROSS_APPARATUS_CONVERGENCE_REQUIRES_INFERRED_BRIDGE",
        "CROSS_APPARATUS_EVIDENCE_IS_COMPLEMENTARY_NOT_CORROBORATING",
        "FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK",
        "SHARED_SUBJECT_NOT_SAME_PROPOSITION",
        "NO_CROSS_APPARATUS_OVERLAP_IN_HELD_CORPUS",
        "CONVERGENCE_CONTRACT_ARCHITECTURE_GAP",
        "PROVENANCE_INDEPENDENCE_NOT_ESTABLISHED",
        "TIME_GRAIN_MISMATCH",
        "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
        "CROSS_APPARATUS_CONVERGENCE_FEASIBILITY_BLOCKED",
    }
)

FEASIBLE = "CROSS_APPARATUS_OBSERVED_CONVERGENCE_FEASIBLE"

# Section 6's forbidden promotions. Scanned ONLY in the statement of a candidate
# offered as OBSERVED. A candidate recorded in order to be REFUSED may name the
# construct it is refused for -- P-C1's whole point is that it says "interest" --
# and a scan that could not tell those apart would forbid recording the refusal.
# This is `testing-strategy.md` section 23 handled structurally rather than by
# loosening the scan until it passes.
LATENT_TERMS = (
    "interest",
    "demand",
    "adoption",
    "popularity",
    "pain",
    "willingness to pay",
    "market validation",
)

OBSERVED_VALIDITIES = frozenset({"VALID"})


class ValidationError(Exception):
    """The record asserts something this mission is not permitted to assert."""


def validate(record: dict) -> None:
    outcome = record.get("primary_outcome")
    if outcome not in ALLOWED_OUTCOMES:
        raise ValidationError(f"primary_outcome {outcome!r} is not a section 36 outcome")

    route = record.get("selected_route")
    if outcome != FEASIBLE and route is not None:
        raise ValidationError(
            f"primary_outcome is {outcome} and selected_route is {route!r}. "
            "Section 26 forbids a least-bad fallback: if no pair passes all eight "
            "gates, select none."
        )

    gates = record.get("gate_evaluation", {})
    results = [g["result"] for g in gates.get("gates", [])]
    if len(results) != 8:
        raise ValidationError(f"section 26 has eight gates; {len(results)} recorded")
    all_pass = all(r == "PASS" for r in results)
    if gates.get("all_eight") is not all_pass:
        raise ValidationError("gate_evaluation.all_eight disagrees with the gate results")
    if all_pass and outcome != FEASIBLE:
        raise ValidationError(
            "every gate passes but the outcome is not "
            f"{FEASIBLE}. A pair passing all eight gates IS the feasible outcome."
        )
    if not all_pass and outcome == FEASIBLE:
        raise ValidationError(
            f"outcome is {FEASIBLE} while gates "
            f"{[g['n'] for g in gates['gates'] if g['result'] != 'PASS']} do not pass. "
            "Section 36 forbids forcing outcome A."
        )

    for candidate in record.get("candidate_propositions", []):
        if candidate.get("formal_validity") not in OBSERVED_VALIDITIES:
            continue
        statement = candidate["statement"].lower()
        for term in LATENT_TERMS:
            if term in statement:
                raise ValidationError(
                    f"candidate {candidate['id']} is offered as OBSERVED and its "
                    f"statement contains the latent construct {term!r}. Section 6 "
                    "forbids promoting a measurement into a construct that is not "
                    "directly measured."
                )

    # Section 8: a standard two-group corroboration candidate needs A alone YES,
    # B alone YES, jointly NO, latent NO. Anything else must not be recorded as
    # standard corroboration.
    for row in record.get("entailment_table", []):
        standard = row["standard_two_group_corroboration"]
        qualifies = (
            row["a_alone_entails_full_claim"] == "YES"
            and row["b_alone_entails_full_claim"] == "YES"
            and row["requires_both_jointly"] == "NO"
            and row["requires_latent_inference"] == "NO"
        )
        if standard.startswith("YES") or standard == "FORMALLY_YES":
            if not qualifies:
                raise ValidationError(
                    f"{row['candidate']} is recorded as standard two-group "
                    "corroboration without satisfying the section 8 conjunction."
                )
        elif qualifies and standard != "FORMALLY_YES":
            raise ValidationError(
                f"{row['candidate']} satisfies the section 8 conjunction but is not "
                "recorded as standard corroboration."
            )

    counters = record.get("counters", {})
    moved = [
        name
        for name, pair in counters.items()
        if isinstance(pair, dict) and pair.get("before") != pair.get("after")
    ]
    if moved:
        raise ValidationError(
            f"section 29 requires every research counter unchanged; these moved: {moved}"
        )

    budget = record.get("network_budget", {})
    if budget.get("RESEARCH_DATA_REQUESTS") != 0:
        raise ValidationError("section 28 expects RESEARCH_DATA_REQUESTS = 0")

    model = record.get("model_use", {})
    if model.get("llm_calls") != 0 or model.get("embeddings") != 0:
        raise ValidationError("section 30 expects 0 model calls and 0 embeddings")
    if model.get("problem_family_status") != "PARKED":
        raise ValidationError("section 30 requires Problem-Family to remain PARKED")

    # Section 13: KNOWN_INDEPENDENT needs positive documentary evidence of
    # distinct measurement lineages, never merely the absence of a found
    # dependency. An absence of documented dependency is exactly what this
    # record holds, and it is why the state here is UNKNOWN.
    independence = record.get("independence_analysis", {})
    if (
        independence.get("state") == "KNOWN_INDEPENDENT"
        and "documentary" not in json.dumps(independence).lower()
    ):
        raise ValidationError(
            "independence_state is KNOWN_INDEPENDENT with no documentary basis "
            "recorded; section 13 forbids converting 'no dependency found' into "
            "independence."
        )


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render(record: dict) -> str:
    lines: list[str] = []
    add = lines.append

    add("# Cross-Apparatus Proposition Convergence Feasibility V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit")
    add("> `cross-apparatus-convergence-feasibility-v1.json` and re-run")
    add("> `infrastructure/scripts/render_cross_apparatus_convergence_feasibility.py`.")
    add("")
    add(f"## Primary outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")
    add(
        f"**Selected route: {record['selected_route'] or 'NONE'}.** "
        + record["selected_route_reason"]
    )
    add("")

    add("### Findings recorded beside it")
    add("")
    for finding in record["secondary_findings"]:
        add(f"**`{finding['code']}`** — {finding['statement']}")
        if "why_not_primary" in finding:
            add("")
            add(f"*Why not the primary outcome:* {finding['why_not_primary']}")
        add("")

    add("## §1 — What an apparatus is")
    add("")
    definition = record["apparatus_definition"]
    add(definition["definition"])
    add("")
    add(f"*Why not a source:* {definition['why_not_source']}")
    add("")
    add(f"*Why `proposition_kind`:* {definition['why_proposition_kind']}")
    add("")
    add(f"*Counted, not assumed:* {definition['counted_not_assumed']}")
    add("")

    add("## §2 — Subject overlap, measured before any pair was chosen")
    add("")
    overlap = record["subject_overlap"]
    add(f"*Method:* {overlap['method']}")
    add("")
    add(f"**{overlap['pre_selection_refused']}**")
    add("")
    add(_row(["subject", "wikimedia Evidence", "stack-exchange Evidence", "cross-apparatus"]))
    add(_row(["---", "---:", "---:", "---"]))
    for row in overlap["measured"]:
        add(
            _row(
                [
                    f"`{row['subject_id']}`",
                    str(row["wikimedia_evidence"]),
                    str(row["stack_exchange_evidence"]),
                    "**YES**" if row["cross_apparatus"] else "no",
                ]
            )
        )
    add("")
    add(overlap["result"])
    add("")
    add(f"*Everything else:* {overlap['non_overlaps']}")
    add("")

    add("## §10 — Time alignment")
    add("")
    time = record["time_overlap"]
    for key in ("wikimedia_detailed", "wikimedia_witnessed", "stack_exchange"):
        block = time[key]
        add(f"**{key}** — grain: {block['grain']}")
        add("")
        for field, value in block.items():
            if field == "grain":
                continue
            add(f"- {field}: {value}")
        add("")
    add(f"**Aligned: {'yes' if time['aligned'] else 'NO'}.** {time['alignment_finding']}")
    add("")
    add(f"*Containment:* {time['containment']}")
    add("")
    aggregation = record["deterministic_temporary_aggregation"]
    add(
        f"*Deterministic temporary aggregation* — needed: "
        f"**{'yes' if aggregation['needed'] else 'NO'}**, available: "
        f"**{'yes' if aggregation['available'] else 'NO'}**."
    )
    add("")
    add(f"- Not needed because: {aggregation['needed_reason']}")
    add(f"- Not available because: {aggregation['available_reason']}")
    add(f"- Both reported because: {aggregation['both_reported_because']}")
    add("")

    add("## §7 — Candidate propositions, narrowest first")
    add("")
    for candidate in record["candidate_propositions"]:
        add(f"### `{candidate['id']}` — class {candidate['class']}, {candidate['class_name']}")
        add("")
        add(f"> {candidate['statement']}")
        add("")
        if "event_class_definition" in candidate:
            add(f"*Event class:* {candidate['event_class_definition']}")
            add("")
        add(
            f"Formal validity: **{candidate['formal_validity']}**. "
            f"Information value: **{candidate['information_value']}**. "
            f"Verdict: **`{candidate['verdict']}`**."
        )
        add("")
        if "why" in candidate:
            add(candidate["why"])
            add("")

    add("## §8 — Entailment table")
    add("")
    add(
        _row(
            [
                "candidate",
                "A alone",
                "B alone",
                "both jointly",
                "latent",
                "source identity removed",
                "standard corroboration",
            ]
        )
    )
    add(_row(["---"] * 7))
    for row in record["entailment_table"]:
        add(
            _row(
                [
                    f"`{row['candidate']}`",
                    row["a_alone_entails_full_claim"],
                    row["b_alone_entails_full_claim"],
                    row["requires_both_jointly"],
                    row["requires_latent_inference"],
                    row["source_identity_improperly_removed"],
                    row["standard_two_group_corroboration"],
                ]
            )
        )
    add("")
    for row in record["entailment_table"]:
        if "source_identity_note" in row:
            add(f"**On `{row['candidate']}` and source identity.** {row['source_identity_note']}")
            add("")

    add("## §16 — The Wikimedia + Stack Exchange diagnostic")
    add("")
    diagnostic = record["section_16_diagnostic"]
    add(
        f"Wikimedia `{diagnostic['wikimedia_content_id']}` on "
        f"`{diagnostic['wikimedia_platform']}` under requester class "
        f"`{diagnostic['wikimedia_requester_class']}`; Stack Exchange tag "
        f"`{diagnostic['stack_exchange_tag']}` on `{diagnostic['stack_exchange_site']}`; "
        f"canonical subject `{diagnostic['canonical_subject_id']}`."
    )
    add("")
    add(_row(["#", "question", "answer"]))
    add(_row(["---:", "---", "---"]))
    for question in diagnostic["questions"]:
        add(_row([str(question["n"]), question["question"], f"**{question['answer']}**"]))
    add("")
    for question in diagnostic["questions"]:
        if "note" in question:
            add(f"{question['n']}. {question['note']}")
    add("")
    add(diagnostic["verdict"])
    add("")

    add("## §12 / §13 — Independence")
    add("")
    independence = record["independence_analysis"]
    add(_row(["", "apparatus A", "apparatus B"]))
    add(_row(["---", "---", "---"]))
    add(_row(["publisher", independence["publisher_a"], independence["publisher_b"]]))
    add(
        _row(
            [
                "event generation",
                independence["event_generation_a"],
                independence["event_generation_b"],
            ]
        )
    )
    add(
        _row(
            [
                "collection pipeline",
                independence["collection_pipeline_a"],
                independence["collection_pipeline_b"],
            ]
        )
    )
    add(
        _row(["classification", independence["classification_a"], independence["classification_b"]])
    )
    add("")
    add(f"**State: `{independence['state']}`.** {independence['state_justification']}")
    add("")
    add(f"**Not refuted, and the difference matters.** {independence['not_refuted']}")
    add("")
    add(f"*{independence['no_bypass_attempted']}*")
    add("")

    add("## §14 — Complementarity versus corroboration")
    add("")
    complementarity = record["complementarity_analysis"]
    add(f"- **Corroborating:** {complementarity['corroborating_definition']}")
    add(f"- **Complementary:** {complementarity['complementary_definition']}")
    add("")
    add(
        f"Wikimedia dimensions: {', '.join(f'`{d}`' for d in complementarity['wikimedia_dimensions'])}. "
        f"Stack Exchange dimensions: "
        f"{', '.join(f'`{d}`' for d in complementarity['stack_exchange_dimensions'])}. "
        f"Overlap: **{complementarity['dimension_overlap'] or 'none'}**."
    )
    add("")
    add(f"**The codebase recorded this first.** {complementarity['codebase_already_recorded_it']}")
    add("")
    add(complementarity["observation_category_note"])
    add("")
    add(complementarity["no_fake_common_category"])
    add("")
    add(f"**Consequence.** {complementarity['consequence']}")
    add("")

    add("## §18 / §19 — Can the convergence contract express this?")
    add("")
    contract = record["convergence_contract_capability"]
    add(f"**{contract['question']} — {contract['answer']}.**")
    add("")
    for refusal in contract["refusals"]:
        add(f"- `{refusal['mechanism']}` ({refusal['location']}): {refusal['rule']}.")
        add(f"  > {refusal['quoted']}")
        add(f"  {refusal['consequence']}")
    add("")
    add(f"*Deliberate, not an oversight:* {contract['deliberate_not_oversight']}")
    add("")
    add(f"*{contract['not_implemented']}*")
    add("")
    fields = record["proposed_identity_and_witness_fields"]
    add("### The identity/witness exercise, and why it fails")
    add("")
    add(f"- identity: {', '.join(f'`{f}`' for f in fields['identity_fields'])}")
    add(f"- witness: {', '.join(f'`{f}`' for f in fields['witness_fields'])}")
    add(f"- disjoint: **{fields['disjoint']}**, complete: **{fields['complete']}**")
    add("")
    add(fields["complete_failure"])
    add("")
    add(fields["second_failure"])
    add("")
    add(f"**Verdict: {fields['verdict']}**")
    add("")

    add("## §21 — Reliability readiness")
    add("")
    add(_row(["apparatus", "resolves", "value", "origin"]))
    add(_row(["---", "---", "---:", "---"]))
    for row in record["reliability_readiness"]:
        add(
            _row(
                [
                    f"`{row['apparatus']}`",
                    row["current_scope_resolves"],
                    "—" if row["value"] is None else str(row["value"]),
                    row["origin"] or "—",
                ]
            )
        )
    add("")
    consequence = record["reliability_consequence"]
    add(consequence["new_proposition_kind_is_new_scope"])
    add("")
    add(f"**{consequence['stack_exchange_already_refused']}**")
    add("")
    add(f"*Why this matters:* {consequence['why_this_matters']}")
    add("")

    add("## §22 — Calibration information value")
    add("")
    calibration = record["calibration_information_value"]
    add(
        f"- `STRUCTURALLY_IDENTIFYING`: **{calibration['structurally_identifying']}** — "
        + calibration["structurally_identifying_why"]
    )
    add(
        f"- `SEMANTICALLY_USEFUL`: **{calibration['semantically_useful']}** — "
        + calibration["semantically_useful_why"]
    )
    add("")
    add(calibration["both_reported_because"])
    add("")

    add("## §25 — Decision matrix")
    add("")
    columns = [
        "SUBJECT_MATCH",
        "TIME_MATCH",
        "EACH_EVIDENCE_SUPPORTS_FULL_PROPOSITION",
        "LATENT_INFERENCE_REQUIRED",
        "COMPLEMENTARY_ONLY",
        "PROVENANCE_INDEPENDENCE",
        "CONVERGENCE_CONTRACT_FIT",
        "RELIABILITY_READINESS",
        "CALIBRATION_INFORMATION_VALUE",
        "VERDICT",
    ]
    add(_row(["candidate"] + [c.lower().replace("_", " ") for c in columns]))
    add(_row(["---"] * (len(columns) + 1)))
    for row in record["decision_matrix"]:
        add(_row([f"`{row['candidate']}`"] + [row[c] for c in columns]))
    add("")

    add("## §26 — The eight gates")
    add("")
    gates = record["gate_evaluation"]
    add(f"Evaluated for `{gates['candidate']}`, the only candidate that reaches them.")
    add("")
    add(_row(["#", "gate", "result", "why"]))
    add(_row(["---:", "---", "---", "---"]))
    for gate in gates["gates"]:
        add(_row([str(gate["n"]), gate["gate"], f"**{gate['result']}**", gate["why"]]))
    add("")
    add(
        f"**{gates['gates_passed']} pass, {gates['gates_failed']} fail. "
        f"All eight: {gates['all_eight']}.**"
    )
    add("")

    add("## §24 — Hypothetical aggregation, symbolic and not persisted")
    add("")
    aggregation = record["hypothetical_aggregation"]
    add(f"Fixture: {aggregation['fixture_shape']}. Persisted: **{aggregation['persisted']}**.")
    add("")
    add(
        f"- group A: {aggregation['group_a']['strength']}, key `{aggregation['group_a']['group_key']}`"
    )
    add(
        f"- group B: {aggregation['group_b']['strength']}, key `{aggregation['group_b']['group_key']}`"
    )
    add(f"- saturation: `{aggregation['saturation']}`")
    add(f"- baseline B-2: `{aggregation['baseline_b2']}`")
    add("")
    add(aggregation["differs"])
    add("")
    add(f"*{aggregation['q_unresolved']}*")
    add("")
    add(f"**What this shows.** {aggregation['what_this_shows']}")
    add("")
    add(f"**What it does not show.** {aggregation['what_this_does_not_show']}")
    add("")

    add("## Counters, budget and state")
    add("")
    add(_row(["counter", "before", "after"]))
    add(_row(["---", "---:", "---:"]))
    for name, pair in record["counters"].items():
        if not isinstance(pair, dict):
            continue
        add(_row([name, str(pair["before"]), str(pair["after"])]))
    add("")
    budget = record["network_budget"]
    add(
        f"`RESEARCH_DATA_REQUESTS` **{budget['RESEARCH_DATA_REQUESTS']}**, "
        f"`APPARATUS_DOCUMENTATION_REQUESTS` **{budget['APPARATUS_DOCUMENTATION_REQUESTS']}**, "
        f"`GOVERNANCE_DOCUMENT_REQUESTS` **{budget['GOVERNANCE_DOCUMENT_REQUESTS']}**."
    )
    add("")
    add(budget["note"])
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
    add(recommendation["do_not_implement_p_a1"])
    add("")
    add(f"**The structural observation.** {recommendation['the_structural_observation']}")
    add("")
    add(f"**Recommended.** {recommendation['recommended']}")
    add("")
    add(f"**Not recommended.** {recommendation['not_recommended']}")
    add("")
    add(f"*{recommendation['explicitly_not_started']}*")
    add("")

    add("## §34 — Deployment-local human confirmations")
    add("")
    checklist = record["deployment_local_human_confirmations_require_migration_checklist"]
    add("**`DEPLOYMENT_LOCAL_HUMAN_CONFIRMATIONS_REQUIRE_MIGRATION_CHECKLIST`**")
    add("")
    add(checklist["finding"])
    add("")
    add(checklist["not_made_portable"])
    add("")
    add(checklist["future_concern"])
    add("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    record = json.loads(SRC.read_text(encoding="utf-8"))
    try:
        validate(record)
    except ValidationError as error:
        print(f"REFUSED  {SRC.name}: {error}")
        return 1

    text = render(record)

    if args.check:
        if not OUT.exists():
            print(f"DRIFT    {OUT.name} does not exist")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {OUT.name} does not match {SRC.name}")
            return 1
        print(f"ok       {OUT.name} matches {SRC.name}")
        return 0

    OUT.write_text(text, encoding="utf-8")
    print(f"wrote    {OUT.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(f"route    {record['selected_route'] or 'NONE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
