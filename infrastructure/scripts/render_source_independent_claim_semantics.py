"""Render and validate the Mission 1.49 source-independent Claim semantics record.

`validate()` enforces the semantic invariants the decision rests on, so a later
edit cannot quietly put `source_id` back into a source-independent proposition's
identity, promote a post-hoc threshold to calibration-eligible, or turn a
semantic mismatch into a contradiction.

Wired into CI: repository file into a repository file, deterministic from an
empty database.

    uv run python infrastructure/scripts/render_source_independent_claim_semantics.py
    uv run python infrastructure/scripts/render_source_independent_claim_semantics.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "data" / "source-independent-claim-semantics-v1.json"
OUT = ROOT / "docs" / "data" / "source-independent-claim-semantics-v1.md"
ADR = ROOT / "docs" / "architecture" / "adr" / "ADR-036-source-independent-claim-semantics.md"

ALLOWED_OUTCOMES = frozenset(
    {
        "SOURCE_INDEPENDENT_PROPOSITIONS_BELONG_TO_INFERRED_LAYER",
        "SOURCE_INDEPENDENT_PROPOSITIONS_REQUIRE_DETERMINISTIC_INFERENCE_SUBTYPE",
        "GOVERNED_CROSS_SOURCE_OBSERVED_CONVERGENCE_IS_SEMANTICALLY_VALID",
        "SOURCE_INDEPENDENT_CLAIM_TYPE_REQUIRED",
        "SOURCE_INDEPENDENT_PROPOSITIONS_SHOULD_REMAIN_UNIMPLEMENTED",
        "CLAIM_SEMANTICS_DECISION_BLOCKED",
        "MISSION_1_48_NOT_MERGED",
        "MISSION_1_49_BASELINE_DRIFT",
        "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
    }
)

QUALITATIVE = frozenset({"STRONG", "MEDIUM", "WEAK", "NONE", "NOT_APPLICABLE", "NOT_ESTABLISHED"})
MODEL_VERDICTS = frozenset({"PREFERRED", "REJECTED", "UNNECESSARY", "NOT_EVALUATED"})
REQUIRED_INVARIANTS = tuple(f"I{n}" for n in range(1, 16))


class ValidationError(Exception):
    """The record asserts something this mission is not permitted to assert."""


def validate(record: dict) -> None:  # noqa: C901
    outcome = record.get("primary_outcome")
    if outcome not in ALLOWED_OUTCOMES:
        raise ValidationError(f"primary_outcome {outcome!r} is not a section 38 outcome")

    # §27. Exactly one preferred model, never a least-bad fallback.
    models = record.get("model_comparison", {}).get("models", [])
    preferred = [m for m in models if m.get("verdict") == "PREFERRED"]
    if len(preferred) != 1:
        raise ValidationError(
            f"section 27 requires exactly ONE preferred semantic model; {len(preferred)} marked"
        )
    for model in models:
        if model.get("verdict") not in MODEL_VERDICTS:
            raise ValidationError(
                f"model {model.get('id')} verdict {model.get('verdict')!r} unknown"
            )
        for dimension in record["model_comparison"]["dimensions"]:
            value = model.get(dimension)
            if value not in QUALITATIVE:
                raise ValidationError(
                    f"model {model.get('id')}.{dimension} is {value!r}; qualitative states only"
                )

    definitions = record.get("semantic_definitions", {})
    observed = definitions.get("OBSERVED_SOURCE_ATTRIBUTED_PROPOSITION", {})
    independent = definitions.get("SOURCE_INDEPENDENT_PROPOSITION", {})

    # I2. OBSERVED keeps source_id as proposition identity.
    if observed.get("source_id") != "PROPOSITION IDENTITY":
        raise ValidationError(
            "invariant I2: `source_id` must remain proposition identity for OBSERVED"
        )
    # I3/I4. The source-independent layer moves it to witness and keeps it.
    if "PROPOSITION IDENTITY" in str(independent.get("source_id", "")).upper().replace(
        "NEVER PROPOSITION IDENTITY", ""
    ):
        raise ValidationError(
            "invariant I3: a source-independent proposition must not carry `source_id` in identity"
        )

    identity = record.get("threshold_state_identity", {})
    identity_fields = identity.get("proposition_identity_fields", [])
    witness_fields = identity.get("witness_provenance_fields", [])

    if "source_id" in identity_fields:
        raise ValidationError("invariant I3: `source_id` is in the source-independent identity")
    if "source_id" not in witness_fields:
        raise ValidationError("invariant I4: provenance must still carry `source_id` per witness")
    if "measurement_value" in identity_fields:
        raise ValidationError(
            "invariant I5: the observed measurement value must not be proposition identity, or "
            "110 and 105 become two Claims"
        )
    for field in ("threshold_operator", "threshold_value"):
        if field not in identity_fields:
            raise ValidationError(f"invariant I6: `{field}` must be proposition identity")
    if identity.get("direction_in_identity") is not False:
        raise ValidationError("invariant I7: Evidence direction must not be proposition identity")
    if set(identity_fields) & set(witness_fields):
        raise ValidationError("identity and witness fields must be disjoint")

    # §17. A post-hoc or unknown threshold is never calibration-eligible.
    for status in record.get("threshold_preregistration", {}).get("statuses", []):
        if status["status"] in ("POST_HOC", "UNKNOWN") and status.get("calibration_eligible"):
            raise ValidationError(
                f"threshold status {status['status']} must not be calibration-eligible"
            )

    fixtures = record.get("fixtures", {})
    mismatch = fixtures.get("C_semantic_mismatch", {})
    if mismatch.get("expected") != "NOT_APPLICABLE":
        raise ValidationError(
            "a semantic mismatch must be NOT_APPLICABLE, never CONTRADICTS: the measurement "
            "bears on a different proposition"
        )
    republication = fixtures.get("D_dependent_republication", {})
    if republication.get("became_corroboration") is not False:
        raise ValidationError("a dependent republication must not become independent corroboration")
    if republication.get("support_groups") != 1:
        raise ValidationError("a dependent republication must collapse into one support group")
    post_hoc = fixtures.get("E_post_hoc_threshold", {})
    if post_hoc.get("calibration_eligible") is not False:
        raise ValidationError("the post-hoc threshold fixture must be calibration-ineligible")
    corroboration = fixtures.get("A_independent_corroboration", {})
    if corroboration.get("support_groups") != 2:
        raise ValidationError("two independent supports must form two groups")
    contradiction = fixtures.get("B_contradiction", {})
    if contradiction.get("same_claim_identity") is not True:
        raise ValidationError(
            "the contradiction fixture must place both witnesses on ONE Claim identity"
        )
    masses = contradiction.get("masses", {})
    if masses and abs(sum(masses.values()) - 1.0) > 1e-9:
        raise ValidationError("the four masses must sum to 1.0")
    if not masses.get("conflict"):
        raise ValidationError("the contradiction fixture must produce non-zero conflict mass")

    # §21. Historical Claims keep their meaning.
    history = record.get("historical_compatibility", {})
    if history.get("proposition_identities_rewritten") != 0:
        raise ValidationError("invariant I15: no historical proposition identity may be rewritten")
    if history.get("migrations_recommended") != 0:
        raise ValidationError("no migration changing historical Claim meaning may be recommended")
    for name, expected in (
        ("claims_unchanged", 43),
        ("revisions_unchanged", 44),
        ("evidence_unchanged", 57),
    ):
        if history.get(name) != expected:
            raise ValidationError(f"historical_compatibility.{name} must be {expected}")

    recorded = {i["id"] for i in record.get("semantic_invariants", [])}
    missing = [i for i in REQUIRED_INVARIANTS if i not in recorded]
    if missing:
        raise ValidationError(f"section 24 invariants missing: {missing}")

    counters = record.get("counters", {})
    moved = [
        name
        for name, pair in counters.items()
        if isinstance(pair, dict) and pair.get("before") != pair.get("after")
    ]
    if moved:
        raise ValidationError(f"section 30 requires every counter unchanged; these moved: {moved}")

    if record.get("source_selected") is not None:
        raise ValidationError("section 32 forbids selecting a source in this mission")

    budget = record.get("network_budget", {})
    for key in (
        "RESEARCH_DATA_REQUESTS",
        "APPARATUS_DOCUMENTATION_REQUESTS",
        "GOVERNANCE_DOCUMENT_REQUESTS",
    ):
        if budget.get(key) != 0:
            raise ValidationError(f"section 32 expects {key} = 0")

    model_use = record.get("model_use", {})
    if model_use.get("llm_calls") != 0 or model_use.get("embeddings") != 0:
        raise ValidationError("section 29 expects 0 model calls and 0 embeddings")
    if model_use.get("problem_family_status") != "PARKED":
        raise ValidationError("section 29 requires Problem-Family to remain PARKED")

    if not ADR.exists():
        raise ValidationError(f"section 23 requires an ADR; {ADR.name} does not exist")


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render(record: dict) -> str:
    lines: list[str] = []
    add = lines.append

    add("# Source-Independent Claim Semantics V1")
    add("")
    add(
        f"**Mission {record['mission']} — recorded {record['recorded_at']}. Decision: {record['adr']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit")
    add("> `source-independent-claim-semantics-v1.json` and re-run")
    add("> `infrastructure/scripts/render_source_independent_claim_semantics.py`.")
    add("")
    add(f"## Primary outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")
    add(f"Claim-type naming verdict: **`{record['claim_type_naming_verdict']}`**.")
    add("")

    correction = record["the_central_correction"]
    add("## The correction that decides it")
    add("")
    add(f"*Assumption refused:* **{correction['assumption_refused']}**")
    add("")
    for reason in correction["why_it_is_false"]:
        add(f"- {reason}")
    add("")
    add(f"**Consequence.** {correction['consequence']}")
    add("")
    measured = correction["measured"]
    add(
        f"*Measured:* live claim types {measured['live_claim_types']}, "
        f"interpretation kinds {measured['live_interpretation_kinds']}, "
        f"claims with a model version **{measured['claims_with_model_version']}**."
    )
    add("")

    add("## §1 — The two propositions")
    add("")
    for name, block in record["semantic_definitions"].items():
        add(f"### `{name}`")
        add("")
        add(f"- **Truth condition.** {block['truth_condition']}")
        add(f"- **Falsifier.** {block['falsifier']}")
        add(f"- **`source_id`.** {block['source_id']}")
        for extra in ("why_source_id_must_stay", "the_reasoning_step_is_mandatory"):
            if extra in block:
                add(f"- {block[extra]}")
        add("")

    add("## §26 — Model comparison")
    add("")
    dimensions = record["model_comparison"]["dimensions"]
    add(_row(["model", "verdict"] + [d.lower().replace("_", " ") for d in dimensions]))
    add(_row(["---"] * (len(dimensions) + 2)))
    for model in record["model_comparison"]["models"]:
        add(
            _row(
                [f"**{model['id']}** {model['name']}", f"**{model['verdict']}**"]
                + [model[d] for d in dimensions]
            )
        )
    add("")
    for model in record["model_comparison"]["models"]:
        add(f"**{model['id']} — {model['name']}: {model['verdict']}.** {model['why']}")
        add("")

    add("## §4 — Which inferences may create a source-independent proposition")
    add("")
    add(_row(["kind", "can create one", "note"]))
    add(_row(["---", "---", "---"]))
    for kind in record["inference_taxonomy"]["kinds"]:
        add(
            _row(
                [
                    f"`{kind['kind']}`",
                    f"**{kind['can_create_source_independent_proposition']}**",
                    kind["note"],
                ]
            )
        )
    add("")
    add(f"**{record['inference_taxonomy']['the_distinction_that_matters']}**")
    add("")

    add("## §8 / §9 / §10 — Identity for the source-independent layer")
    add("")
    identity = record["threshold_state_identity"]
    add("*Nothing here applies retroactively to OBSERVED Claims.*")
    add("")
    add(
        f"**Proposition identity:** {', '.join(f'`{f}`' for f in identity['proposition_identity_fields'])}"
    )
    add("")
    add(
        f"**Witness provenance:** {', '.join(f'`{f}`' for f in identity['witness_provenance_fields'])}"
    )
    add("")
    add(_row(["fact", "in identity?", "why"]))
    add(_row(["---", "---", "---"]))
    add(
        _row(
            [
                "threshold",
                f"**{identity['threshold_in_identity']}**",
                identity["threshold_in_identity_why"],
            ]
        )
    )
    add(
        _row(
            [
                "measurement value",
                f"**{identity['measurement_value_in_identity']}**",
                identity["measurement_value_in_identity_why"],
            ]
        )
    )
    add(
        _row(
            [
                "`source_id`",
                f"**{identity['source_id_in_identity']}**",
                identity["source_id_in_identity_why"],
            ]
        )
    )
    add(
        _row(
            [
                "direction",
                f"**{identity['direction_in_identity']}**",
                identity["direction_in_identity_why"],
            ]
        )
    )
    add("")
    add(f"**Provenance is preserved.** {identity['source_id_preserved_where']}")
    add("")

    add("## §18 — The evaluation function")
    add("")
    evaluation = record["evaluation_function"]
    add(f"`{evaluation['signature']}`")
    add("")
    add(_row(["outcome", "condition"]))
    add(_row(["---", "---"]))
    for rule in evaluation["rules"]:
        add(_row([f"**{rule['outcome']}**", rule["condition"]]))
    add("")
    add(f"*{evaluation['why_deterministic']}*")
    add("")

    add("## §12 / §13 — Two gates, and neither implies the other")
    add("")
    gate = record["measurement_equivalence_gate"]
    add(f"**Measurement equivalence** over: {', '.join(gate['required_over'])}.")
    add("")
    add(gate["why_separate_from_independence"])
    add("")
    independence = record["independence_stays_separate"]
    add(f"**{independence['rule']}** {independence['consequence']}")
    add("")
    add(f"*{independence['why_not_in_identity']}*")
    add("")

    add("## §14 / §15 — Reliability")
    add("")
    reliability = record["reliability_semantics"]
    add(
        f"Scope is unchanged and stays source-relative: {', '.join(f'`{s}`' for s in reliability['scope'])}."
    )
    add("")
    add(f"**Why that is compatible.** {reliability['why_compatible']}")
    add("")
    add(reliability["new_proposition_kind_is_a_new_scope"])
    add("")
    split = reliability["measurement_reliability_vs_derivation_validity"]
    add(f"- **MEASUREMENT_RELIABILITY** — {split['MEASUREMENT_RELIABILITY']}")
    add(f"- **DERIVATION_VALIDITY** — {split['DERIVATION_VALIDITY']}")
    add("")
    add(f"**They must never be multiplied.** {split['must_not_be_multiplied']}")
    add("")

    add("## §16 / §17 — Derivation provenance and preregistration")
    add("")
    provenance = record["derivation_provenance"]
    for field in provenance["minimum_fields"]:
        add(f"- `{field}`")
    add("")
    add(f"*{provenance['an_existing_field_and_its_limit']}*")
    add("")
    add(_row(["threshold provenance", "meaning", "calibration eligible"]))
    add(_row(["---", "---", "---"]))
    for status in record["threshold_preregistration"]["statuses"]:
        add(
            _row(
                [
                    f"`{status['status']}`",
                    status["meaning"],
                    "**yes**" if status["calibration_eligible"] else "**no**",
                ]
            )
        )
    add("")
    add(record["threshold_preregistration"]["the_rule"])
    add("")
    add(f"*{record['threshold_preregistration']['unknown_is_not_permitted_to_default']}*")
    add("")

    add("## §19 / §28 — Where the evaluation lives")
    add("")
    boundary = record["architecture_boundary"]
    add(f"**Option {boundary['evaluation_belongs_in']}.**")
    add("")
    for option, verdict in boundary["options"].items():
        add(f"- {option}: {verdict}")
    add("")
    add(f"**Why separate.** {boundary['why_separate']}")
    add("")
    add(f"Future boundary: `{boundary['future_boundary']}`")
    add("")
    add(f"Evidence attachment: {boundary['evidence_attachment']}")
    add("")

    add("## §20 — Cross-source OBSERVED convergence, reconsidered")
    add("")
    reconsidered = record["cross_source_observed_convergence_reconsidered"]
    add(f"**`{reconsidered['verdict']}`.** {reconsidered['reasoning']}")
    add("")
    add(f"*{reconsidered['source_boundary_not_widened']}*")
    add("")

    add("## §24 — Semantic invariants")
    add("")
    for invariant in record["semantic_invariants"]:
        add(f"- **{invariant['id']}.** {invariant['statement']}")
    add("")

    add("## §25 — Fixtures")
    add("")
    fixtures = record["fixtures"]
    corroboration = fixtures["A_independent_corroboration"]
    add(
        f"**A — independent corroboration.** `{corroboration['claim']}`, witnesses 110 and 105, "
        f"both KNOWN_INDEPENDENT → **{corroboration['support_groups']} support groups**, strength "
        f"**{corroboration['support_strength']}** against a strongest member of "
        f"{corroboration['strongest_member']}. {corroboration['note']}"
    )
    add("")
    contradiction = fixtures["B_contradiction"]
    masses = contradiction["masses"]
    add(
        f"**B — contradiction.** Same Claim identity: **{contradiction['same_claim_identity']}**. "
        f"Support {contradiction['support_strength']}, contradiction "
        f"{contradiction['contradiction_strength']}, masses "
        f"{masses['supported']} / {masses['contradicted']} / {masses['conflict']} / "
        f"{masses['uncertainty']} summing to **{contradiction['sum']}**. {contradiction['note']}"
    )
    add("")
    mismatch = fixtures["C_semantic_mismatch"]
    add(
        f"**C — semantic mismatch.** Expected **{mismatch['expected']}**, not {mismatch['not']}. {mismatch['note']}"
    )
    add("")
    republication = fixtures["D_dependent_republication"]
    add(
        f"**D — dependent republication.** {republication['support_groups']} support group, strength "
        f"{republication['support_strength']}, became corroboration: "
        f"**{republication['became_corroboration']}**. {republication['note']}"
    )
    add("")
    post_hoc = fixtures["E_post_hoc_threshold"]
    add(
        f"**E — post-hoc threshold.** `{post_hoc['threshold_provenance_status']}`, "
        f"calibration eligible: **{post_hoc['calibration_eligible']}**. {post_hoc['note']}"
    )
    add("")

    add("## §21 — Historical compatibility")
    add("")
    history = record["historical_compatibility"]
    add(
        f"Claims **{history['claims_unchanged']}**, revisions **{history['revisions_unchanged']}**, "
        f"Evidence **{history['evidence_unchanged']}** — all unchanged. Proposition identities "
        f"rewritten: **{history['proposition_identities_rewritten']}**. Migrations recommended: "
        f"**{history['migrations_recommended']}**."
    )
    add("")
    add(history["statement"])
    add("")

    add("## Counters and budget")
    add("")
    add(_row(["counter", "before", "after"]))
    add(_row(["---", "---:", "---:"]))
    for name, pair in record["counters"].items():
        if isinstance(pair, dict):
            add(_row([name, str(pair["before"]), str(pair["after"])]))
    add("")
    model_use = record["model_use"]
    add(
        f"Model calls **{model_use['llm_calls']}**, {model_use['usd']:.2f} USD, embeddings "
        f"**{model_use['embeddings']}**, Problem-Family **{model_use['problem_family_status']}**, "
        f"source selected **{record['source_selected'] or 'NONE'}**."
    )
    add("")

    add("## Next mission")
    add("")
    recommendation = record["next_mission_recommendation"]
    add(f"**{recommendation['recommended']}** — {recommendation['scope']}")
    add("")
    add("It must decide:")
    add("")
    for item in recommendation["must_decide"]:
        add(f"- {item}")
    add("")
    add(f"It must not: {', '.join(recommendation['must_not'])}.")
    add("")
    add(f"*{recommendation['explicitly_not_started']}*")
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

    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {OUT.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(f"adr      {record['adr']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
