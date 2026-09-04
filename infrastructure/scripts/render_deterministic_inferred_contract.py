"""Render and validate the Mission 1.50 deterministic inferred Claim contract.

`validate()` enforces the ADR-036 invariants this contract inherits and the
ADR-037 decisions it adds, so a later edit cannot quietly turn a semantic
mismatch into a contradiction, make a post-hoc threshold calibration-eligible,
promote UNKNOWN to support, or leave two models selected for one question.

Wired into CI: repository file into a repository file, deterministic from an
empty database.

    uv run python infrastructure/scripts/render_deterministic_inferred_contract.py
    uv run python infrastructure/scripts/render_deterministic_inferred_contract.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "data" / "deterministic-inferred-claim-contract-v1.json"
OUT = ROOT / "docs" / "data" / "deterministic-inferred-claim-contract-v1.md"
ADR = ROOT / "docs" / "architecture" / "adr" / "ADR-037-deterministic-inferred-claim-contract.md"

ALLOWED_OUTCOMES = frozenset(
    {
        "DETERMINISTIC_INFERRED_CLAIM_CONTRACT_READY",
        "DERIVATION_PROVENANCE_MODEL_GAP",
        "EVIDENCE_ATTACHMENT_SEMANTICS_GAP",
        "EVALUATOR_BOUNDARY_MODEL_GAP",
        "THRESHOLD_PROVENANCE_MODEL_GAP",
        "INTERPRETATION_CONFIDENCE_SEMANTIC_GAP",
        "DETERMINISTIC_INFERRED_CONTRACT_REQUIRES_SCHEMA_EXTENSION",
        "MISSION_1_49_NOT_MERGED",
        "MISSION_1_50_BASELINE_DRIFT",
        "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
        "DETERMINISTIC_INFERRED_CLAIM_CONTRACT_BLOCKED",
    }
)

SCHEMA_VERDICTS = frozenset(
    {
        "NO_SCHEMA_CHANGE_REQUIRED",
        "DERIVATION_PROVENANCE_SCHEMA_REQUIRED",
        "THRESHOLD_PROVENANCE_SCHEMA_REQUIRED",
        "BOTH_REQUIRED",
    }
)

CALIBRATION_INELIGIBLE = ("POST_HOC", "UNKNOWN")
CALIBRATION_ELIGIBLE = ("PREREGISTERED", "SOURCE_NATIVE", "EXTERNAL_NORM")

# The four questions §42 requires resolved before outcome A may be used.
MANDATORY_QUESTIONS = (
    "Q1_derivation_provenance",
    "Q2_evidence_attachment",
    "Q3_evaluator_boundary",
    "Q4_threshold_provenance",
)


class ValidationError(Exception):
    """The contract asserts something this mission is not permitted to assert."""


def validate(record: dict) -> None:  # noqa: C901
    outcome = record.get("primary_outcome")
    if outcome not in ALLOWED_OUTCOMES:
        raise ValidationError(f"primary_outcome {outcome!r} is not a section 42 outcome")

    # §42 A. Exactly one selection per mandatory question, and all four resolved.
    for question in MANDATORY_QUESTIONS:
        block = record.get(question)
        if not block:
            raise ValidationError(f"mandatory question {question} is missing")
        selected = block.get("selected_model")
        if not selected:
            raise ValidationError(f"{question} has no selected_model")
        considered = block.get("models_considered") or block.get("options_considered")
        if considered is not None:
            chosen = [
                m
                for m in considered
                if str(m.get("verdict", "")).upper() in ("SELECTED", "PREFERRED")
            ]
            if len(chosen) != 1:
                raise ValidationError(
                    f"{question} must select exactly one model; {len(chosen)} marked selected"
                )
            if chosen[0].get("id") != selected:
                raise ValidationError(
                    f"{question}.selected_model is {selected!r} but {chosen[0].get('id')!r} "
                    "is the one marked selected"
                )
    if outcome == "DETERMINISTIC_INFERRED_CLAIM_CONTRACT_READY":
        for question in MANDATORY_QUESTIONS:
            if not record[question].get("selected_model"):
                raise ValidationError(
                    f"outcome A requires all four mandatory questions resolved; {question} is open"
                )

    if record.get("schema_necessity") not in SCHEMA_VERDICTS:
        raise ValidationError(f"schema_necessity {record.get('schema_necessity')!r} is unknown")

    # §29. This mission defines the contract; it does not migrate.
    if record.get("migration_created") is not False:
        raise ValidationError("section 29 forbids creating a migration in this mission")

    # ADR-036 invariants this contract inherits.
    layers = record.get("layer_separation", {})
    if layers.get("claim_identity") != "SOURCE_INDEPENDENT":
        raise ValidationError("the INFERRED Claim's identity must be source-independent")
    if layers.get("evidence_witness") != "SOURCE_SPECIFIC":
        raise ValidationError("the Evidence witness must remain source-specific")
    if layers.get("reliability_scope") != "SOURCE_SPECIFIC":
        raise ValidationError("the reliability scope must remain source-specific")

    threshold = record.get("Q4_threshold_provenance", {})
    if threshold.get("threshold_provenance_is_not_claim_identity") is not True:
        raise ValidationError(
            "threshold provenance must NOT be Claim identity: the same proposition with a "
            "preregistered and a post-hoc bound is one proposition"
        )

    registration = record.get("threshold_registration_record", {})
    statuses = {s["status"]: s for s in registration.get("statuses", [])}
    for status in CALIBRATION_INELIGIBLE:
        if status not in statuses:
            raise ValidationError(f"threshold status {status} is not defined")
        if statuses[status].get("calibration_eligible"):
            raise ValidationError(f"{status} must never be calibration-eligible")
    for status in CALIBRATION_ELIGIBLE:
        if status not in statuses:
            raise ValidationError(f"threshold status {status} is not defined")

    temporal = registration.get("preregistration_temporal_rule", {})
    if "retrieved_at" not in str(temporal.get("rule", "")):
        raise ValidationError(
            "the preregistration rule must compare against retrieval, not publication"
        )
    if not temporal.get("the_limit_stated_rather_than_hidden"):
        raise ValidationError(
            "the preregistration rule must state that it cannot exclude human foreknowledge"
        )
    if temporal.get("a_measurement_already_held_is_post_hoc_by_construction") is not True:
        raise ValidationError("a measurement already held must be POST_HOC by construction")

    # §12. Result vocabulary and its mapping.
    vocabulary = record.get("evaluation_result_vocabulary", {})
    results = {r["result"]: r for r in vocabulary.get("results", [])}
    for required in ("SUPPORTS", "CONTRADICTS", "NOT_APPLICABLE", "UNKNOWN"):
        if required not in results:
            raise ValidationError(f"evaluation result {required} is not defined")
    if results["SUPPORTS"]["evidence"] != "EvidenceDirection.SUPPORTS":
        raise ValidationError("SUPPORTS must map to EvidenceDirection.SUPPORTS")
    if results["CONTRADICTS"]["evidence"] != "EvidenceDirection.CONTRADICTS":
        raise ValidationError("CONTRADICTS must map to EvidenceDirection.CONTRADICTS")
    for refusing in ("NOT_APPLICABLE", "UNKNOWN"):
        mapped = results[refusing]["evidence"].upper()
        if "EVIDENCEDIRECTION" in mapped.replace(" ", ""):
            raise ValidationError(
                f"{refusing} must not map to an EvidenceDirection; it produces no Evidence row"
            )
    if "NEUTRAL" not in vocabulary.get("unknown_is_not_neutral", "").upper():
        raise ValidationError("the contract must state that UNKNOWN does not become NEUTRAL")

    # §16. No confidence on an exact entailment, and no reliability in derivation.
    absent = {
        f["field"]
        for f in record.get("derivation_provenance_record", {}).get("deliberately_absent", [])
    }
    for forbidden in ("derivation_confidence", "reliability"):
        if forbidden not in absent:
            raise ValidationError(
                f"`{forbidden}` must be explicitly recorded as deliberately absent from the "
                "derivation record"
            )
    fields = {f["field"] for f in record.get("derivation_provenance_record", {}).get("fields", [])}
    for forbidden in ("derivation_confidence", "reliability", "independence"):
        if forbidden in fields:
            raise ValidationError(f"`{forbidden}` must not be a derivation provenance field")
    for entry in record.get("derivation_provenance_record", {}).get("fields", []):
        if not entry.get("audit_question", "").strip():
            raise ValidationError(
                f"derivation field `{entry['field']}` answers no named audit question (§2)"
            )

    # §17. If no gap is reported the record must say why, not merely omit it.
    confidence = record.get("reliability_and_derivation", {}).get("interpretation_confidence", {})
    if confidence.get("semantic_gap") is None:
        raise ValidationError("section 17 requires an explicit interpretation_confidence verdict")
    if (
        confidence.get("semantic_gap") is False
        and not confidence.get("semantic_gap_note", "").strip()
    ):
        raise ValidationError(
            "reporting no interpretation_confidence gap requires stating why the existing "
            "semantics accommodate deterministic INFERRED"
        )
    if (
        confidence.get("semantic_gap") is True
        and outcome != "INTERPRETATION_CONFIDENCE_SEMANTIC_GAP"
    ):
        raise ValidationError(
            "an interpretation_confidence gap is reported but is not the primary outcome"
        )

    # §26 fixtures.
    fixtures = record.get("fixtures", {})
    mismatch = fixtures.get("C_semantic_mismatch", {})
    if mismatch.get("evaluation_result") != "NOT_APPLICABLE" or mismatch.get("evidence_rows") != 0:
        raise ValidationError("a semantic mismatch is NOT_APPLICABLE with no Evidence row")
    unknown = fixtures.get("D_unknown_equivalence", {})
    if unknown.get("evaluation_result") != "UNKNOWN" or unknown.get("evidence_rows") != 0:
        raise ValidationError("unestablished equivalence is UNKNOWN with no Evidence row")
    republication = fixtures.get("E_dependent_republication", {})
    if republication.get("became_independent_corroboration") is not False:
        raise ValidationError("a dependent republication must not become independent corroboration")
    if republication.get("support_groups") != 1:
        raise ValidationError("a dependent republication must collapse into one support group")
    post_hoc = fixtures.get("F_post_hoc_threshold", {})
    if post_hoc.get("calibration_eligible") is not False:
        raise ValidationError("a post-hoc threshold must not be calibration-eligible")
    if post_hoc.get("logically_valid") is not True:
        raise ValidationError(
            "section 5: a post-hoc threshold still permits logical support. Provenance changes "
            "calibration eligibility, never entailment"
        )
    corroboration = fixtures.get("A_two_independent_supports", {})
    if corroboration.get("support_groups") != 2 or not corroboration.get("same_proposition_key"):
        raise ValidationError(
            "two independent supports must share one proposition key and form two groups"
        )
    contradiction = fixtures.get("B_contradiction", {})
    if contradiction.get("same_claim_identity") is not True:
        raise ValidationError("the contradiction fixture must place both witnesses on one Claim")
    masses = contradiction.get("masses", {})
    if masses and abs(sum(masses.values()) - 1.0) > 1e-9:
        raise ValidationError("the four masses must sum to 1.0")

    history = record.get("historical_compatibility", {})
    if history.get("observed_identity_changed") is not False:
        raise ValidationError("OBSERVED proposition identity must not change")
    if history.get("migrations_created") != 0 or history.get("inferred_claims_created") != 0:
        raise ValidationError("no migration and no INFERRED Claim may be created in this mission")
    for name, expected in (
        ("claims_unchanged", 43),
        ("revisions_unchanged", 44),
        ("evidence_unchanged", 57),
    ):
        if history.get(name) != expected:
            raise ValidationError(f"historical_compatibility.{name} must be {expected}")

    counters = record.get("counters", {})
    moved = [
        name
        for name, pair in counters.items()
        if isinstance(pair, dict) and pair.get("before") != pair.get("after")
    ]
    if moved:
        raise ValidationError(f"section 34 requires every counter unchanged; these moved: {moved}")

    if record.get("source_selected") is not None:
        raise ValidationError("section 33 forbids selecting a source")

    for key, value in record.get("network_budget", {}).items():
        if value != 0:
            raise ValidationError(f"section 33 expects {key} = 0")

    model_use = record.get("model_use", {})
    if model_use.get("llm_calls") != 0 or model_use.get("embeddings") != 0:
        raise ValidationError("section 32 expects 0 model calls and 0 embeddings")
    if model_use.get("problem_family_status") != "PARKED":
        raise ValidationError("section 32 requires Problem-Family to remain PARKED")

    boundary = record.get("Q3_evaluator_boundary", {})
    forbidden = {d["package"] for d in boundary.get("forbidden_dependencies", [])}
    for required in ("sros_llm_gateway", "sros_acquisition"):
        if required not in forbidden:
            raise ValidationError(f"`{required}` must be a forbidden evaluator dependency")
    if not boundary.get("zero_dependency_compatible"):
        raise ValidationError("the evaluator boundary must be zero-dependency compatible (§30)")

    if not ADR.exists():
        raise ValidationError(f"section 39 requires an ADR; {ADR.name} does not exist")


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render(record: dict) -> str:  # noqa: C901
    lines: list[str] = []
    add = lines.append

    add("# Deterministic Inferred Claim Contract V1")
    add("")
    add(
        f"**Mission {record['mission']} — recorded {record['recorded_at']}. "
        f"Decision: {record['adr']}, building on {record['builds_on']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit")
    add("> `deterministic-inferred-claim-contract-v1.json` and re-run")
    add("> `infrastructure/scripts/render_deterministic_inferred_contract.py`.")
    add("")
    add(f"## Primary outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")
    add(f"**Schema necessity: `{record['schema_necessity']}`.**")
    add("")
    add(_row(["area", "verdict"]))
    add(_row(["---", "---"]))
    for area, verdict in record["schema_necessity_detail"].items():
        add(_row([f"`{area}`", verdict]))
    add("")

    add("## The four mandatory questions")
    add("")
    for question in MANDATORY_QUESTIONS:
        block = record[question]
        add(f"### {question.split('_', 1)[0]} — {block['question']}")
        add("")
        name = block.get("selected_name", "")
        add(f"**Selected: model {block['selected_model']}{' — ' + name if name else ''}.**")
        add("")
        if "why" in block:
            add(block["why"])
            add("")
        considered = block.get("models_considered") or block.get("options_considered") or []
        if considered:
            add(_row(["model", "verdict", "why"]))
            add(_row(["---", "---", "---"]))
            for model in considered:
                label = model.get("name", "")
                add(
                    _row(
                        [
                            f"**{model['id']}**{' ' + label if label else ''}",
                            f"`{model['verdict']}`",
                            model.get("why") or model.get("note", ""),
                        ]
                    )
                )
            add("")
        for extra in (
            "why_not_claim_model",
            "why_not_evidence_aggregation",
            "why_not_opportunity_engine",
            "why_not_on_claim",
            "why_not_in_the_derivation_record",
            "why_both",
            "why_not_identity",
        ):
            if extra in block:
                add(f"*{extra.replace('_', ' ')}:* {block[extra]}")
                add("")
        if question == "Q3_evaluator_boundary":
            add(f"Proposed package: `{block['proposed_package']}` — **not created**.")
            add("")
            add(
                f"- allowed dependencies: {', '.join(f'`{d}`' for d in block['allowed_dependencies'])}"
            )
            add("- forbidden dependencies:")
            for dependency in block["forbidden_dependencies"]:
                add(f"  - `{dependency['package']}` — {dependency['why']}")
            add("")
            add(f"*{block['zero_dependency_note']}*")
            add("")
            add(f"*{block['not_created']}*")
            add("")

    add("## §2 — The derivation provenance record")
    add("")
    derivation = record["derivation_provenance_record"]
    add(f"Binds to **{derivation['binds_to']}**. {derivation['binds_to_why']}")
    add("")
    add(f"Granularity: **{derivation['granularity']}**. {derivation['granularity_why']}")
    add("")
    add(_row(["field", "audit question it answers"]))
    add(_row(["---", "---"]))
    for field in derivation["fields"]:
        add(_row([f"`{field['field']}`", field["audit_question"]]))
    add("")
    add("**Deliberately absent.**")
    add("")
    for field in derivation["deliberately_absent"]:
        add(f"- `{field['field']}` — {field['why']}")
    add("")

    add("## §4 / §25 — The threshold registration record")
    add("")
    registration = record["threshold_registration_record"]
    add(_row(["field", "audit question it answers"]))
    add(_row(["---", "---"]))
    for field in registration["fields"]:
        add(_row([f"`{field['field']}`", field["audit_question"]]))
    add("")
    add(_row(["status", "meaning", "calibration eligible"]))
    add(_row(["---", "---", "---"]))
    for status in registration["statuses"]:
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
    temporal = registration["preregistration_temporal_rule"]
    add("### §23 — What preregistered means, exactly")
    add("")
    add(f"    {temporal['rule']}")
    add("")
    add(f"**Retrieved, not published.** {temporal['why_retrieved_at_and_not_published_at']}")
    add("")
    add(f"*Not commit time either:* {temporal['why_not_repository_commit_time']}")
    add("")
    add(
        f"**The limit, stated rather than hidden.** {temporal['the_limit_stated_rather_than_hidden']}"
    )
    add("")

    add("## §3 — Structured facts versus prose")
    add("")
    prose = record["structured_versus_prose"]
    add(f"Machine-auditable: {', '.join(f'`{f}`' for f in prose['machine_auditable_facts'])}.")
    add("")
    add(f"Human-readable: `{prose['human_readable']}` — {prose['rationale_role']}")
    add("")
    add(f"**{prose['rule']}**")
    add("")
    add(f"*{prose['no_llm_rationale']}*")
    add("")

    add("## §12 — Evaluation results and their mapping")
    add("")
    vocabulary = record["evaluation_result_vocabulary"]
    add(_row(["result", "condition", "persisted Evidence"]))
    add(_row(["---", "---", "---"]))
    for result in vocabulary["results"]:
        add(_row([f"**{result['result']}**", result["condition"], result["evidence"]]))
    add("")
    add(f"**UNKNOWN is not neutral.** {vocabulary['unknown_is_not_neutral']}")
    add("")
    add(f"**A mismatch is not a contradiction.** {vocabulary['mismatch_is_not_contradiction']}")
    add("")
    add(f"*{vocabulary['both_non_directional_results_are_recorded']}*")
    add("")

    add("## §13 — Measurement equivalence")
    add("")
    equivalence = record["measurement_equivalence"]
    add(f"Required over: {', '.join(equivalence['required_over'])}.")
    add("")
    add(
        f"**Established: {equivalence['how_established']}.** {equivalence['how_established_detail']}"
    )
    add("")
    add(f"*{equivalence['never_inferred_from_strings']}*")
    add("")
    add(f"*{equivalence['unestablished_equivalence_is_unknown']}*")
    add("")

    add("## §14 — What is source-independent and what is not")
    add("")
    layers = record["layer_separation"]
    add(f"- Claim identity: **{layers['claim_identity']}**")
    add(f"- Evidence witness: **{layers['evidence_witness']}**")
    add(f"- Reliability scope: **{layers['reliability_scope']}**")
    add(f"- Independence: **{layers['independence']}**")
    add("")
    example = layers["worked_example"]
    add(f"> {example['claim']}")
    add("")
    add(_row(["source", "measurement", "direction", "reliability scope"]))
    add(_row(["---", "---:", "---", "---"]))
    for witness in example["witnesses"]:
        add(
            _row(
                [
                    witness["source"],
                    str(witness["measurement"]),
                    f"**{witness['direction']}**",
                    witness["reliability_scope"],
                ]
            )
        )
    add("")
    add(f"**{example['note']}**")
    add("")

    add("## §15 / §16 / §17 — Reliability, derivation validity, interpretation confidence")
    add("")
    reliability = record["reliability_and_derivation"]
    add(
        f"Reliability scope unchanged: {', '.join(f'`{s}`' for s in reliability['reliability_scope_unchanged'])}."
    )
    add("")
    add(reliability["initial_resolution"])
    add("")
    add(f"*{reliability['no_inheritance']}*")
    add("")
    add(f"**{reliability['derivation_validity_is_not_reliability']}**")
    add("")
    confidence = reliability["interpretation_confidence"]
    add("### `interpretation_confidence`")
    add("")
    add(f"> {confidence['documented_meaning']}")
    add("")
    add(
        f"Mandatory for automated claims: **{confidence['mandatory_for_automated_claims']}**. {confidence['mandatory_evidence']}"
    )
    add("")
    add(f"**Answer: {confidence['answer']}.** {confidence['answer_detail']}")
    add("")
    add(f"*{confidence['why_not_1_0_automatically']}*")
    add("")
    add(f"Semantic gap: **{confidence['semantic_gap']}**. {confidence['semantic_gap_note']}")
    add("")

    add("## §22 — Idempotency")
    add("")
    idempotency = record["idempotency"]
    add(_row(["entity", "key", "basis"]))
    add(_row(["---", "---", "---"]))
    for name in ("derived_claim", "evidence", "derivation_record"):
        entry = idempotency[name]
        add(_row([f"`{name}`", f"`{entry['key']}`", entry["basis"]]))
    add("")
    add(f"Must prevent: {', '.join(idempotency['must_prevent'])}.")
    add("")
    add(f"*{idempotency['must_not']}*")
    add("")

    add("## §11 — Evaluator responsibility")
    add("")
    responsibility = record["evaluator_responsibility"]
    add("**It must:**")
    add("")
    for item in responsibility["must"]:
        add(f"- {item}")
    add("")
    add("**It must not:**")
    add("")
    for item in responsibility["must_not"]:
        add(f"- {item}")
    add("")

    add("## §26 — Fixtures")
    add("")
    fixtures = record["fixtures"]
    a = fixtures["A_two_independent_supports"]
    add(
        f"**A — two independent supports.** `{a['claim']}`, threshold "
        f"`{a['threshold_status']}`, measurements 110 and 105. Same proposition key: "
        f"**{a['same_proposition_key']}**. **{a['support_groups']} support groups**, strength "
        f"**{a['support_strength']}** against a strongest member of {a['strongest_member']}."
    )
    add("")
    b = fixtures["B_contradiction"]
    masses = b["masses"]
    add(
        f"**B — contradiction.** Same Claim identity: **{b['same_claim_identity']}**. "
        f"Contradiction {b['contradiction_strength']}, masses {masses['supported']} / "
        f"{masses['contradicted']} / {masses['conflict']} / {masses['uncertainty']} summing to "
        f"**{b['sum']}**."
    )
    add("")
    for key, label in (
        ("C_semantic_mismatch", "C — semantic mismatch"),
        ("D_unknown_equivalence", "D — unknown equivalence"),
    ):
        entry = fixtures[key]
        add(
            f"**{label}.** Result **{entry['evaluation_result']}**, Evidence rows "
            f"**{entry['evidence_rows']}**, derivation record **{entry['derivation_record']}**. "
            f"{entry['note']}"
        )
        add("")
    e = fixtures["E_dependent_republication"]
    add(
        f"**E — dependent republication.** {e['support_groups']} support group at "
        f"{e['support_strength']}; became independent corroboration: "
        f"**{e['became_independent_corroboration']}**."
    )
    add("")
    f = fixtures["F_post_hoc_threshold"]
    add(
        f"**F — post-hoc threshold.** Result **{f['evaluation_result']}**, logically valid "
        f"**{f['logically_valid']}**, calibration eligible **{f['calibration_eligible']}**. {f['note']}"
    )
    add("")

    add("## Historical compatibility, counters and budget")
    add("")
    history = record["historical_compatibility"]
    add(
        f"Claims **{history['claims_unchanged']}**, revisions **{history['revisions_unchanged']}**, "
        f"Evidence **{history['evidence_unchanged']}** — unchanged. OBSERVED identity changed: "
        f"**{history['observed_identity_changed']}**. Migrations created: "
        f"**{history['migrations_created']}**. INFERRED Claims created: "
        f"**{history['inferred_claims_created']}**."
    )
    add("")
    add(history["statement"])
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
        f"source selected **{record['source_selected'] or 'NONE'}**, migration created "
        f"**{record['migration_created']}**."
    )
    add("")

    add("## Next mission")
    add("")
    recommendation = record["next_mission_recommendation"]
    add(f"**{recommendation['recommended']}**")
    add("")
    add(recommendation["why"])
    add("")
    add(f"Scope: {recommendation['scope']}")
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
    print(f"schema   {record['schema_necessity']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
