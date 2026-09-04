"""Render and validate the Mission 1.53 refusal-provenance design record.

`validate()` checks the record against the REPOSITORY rather than against
itself. The reason codes it lists must be the ones the evaluator actually
raises; the NOT NULL its central argument rests on must still be in migration
0034; the identity key whose NULL behaviour decides Option B must still be the
one 0034 declares; the guard it says was untouched must still restrict the
interpreters to OBSERVED; and no migration may have been added. Every input is a
repository file, so this is deterministic from an empty database and safe in CI.

    uv run python infrastructure/scripts/render_refusal_provenance_design.py
    uv run python infrastructure/scripts/render_refusal_provenance_design.py --check
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "data" / "refusal-derivation-binding-design-v1.json"
OUT = ROOT / "docs" / "data" / "refusal-derivation-binding-design-v1.md"
BASELINE = ROOT / "docs" / "data" / "refusal-derivation-binding-baseline-v1.json"

ADR = ROOT / "docs" / "architecture" / "adr" / "ADR-038-refusal-provenance-binding.md"
MIGRATIONS = ROOT / "infrastructure" / "db" / "migrations"
MIGRATION_0034 = MIGRATIONS / "0034_deterministic_derivation_provenance.sql"
EVALUATOR = (
    ROOT
    / "packages"
    / "inferred-claim-evaluator"
    / "python"
    / "sros_inferred_claim_evaluator"
    / "threshold_state.py"
)
VALIDATE_CLAIMS = ROOT / "infrastructure" / "scripts" / "validate_claims.py"
CLAIM_MODEL = ROOT / "packages" / "claim-model" / "python" / "sros_claim_model" / "model.py"

ALLOWED_OUTCOMES = frozenset(
    {
        "INPUT_KEYED_REFUSAL_PROVENANCE_MODEL_SELECTED",
        "CONDITIONAL_NULL_DERIVATION_BINDING_SELECTED",
        "REFUSAL_PROVENANCE_MODEL_READY",
        "TARGET_PROPOSITION_DESCRIPTOR_MODEL_GAP",
        "REFUSAL_IDEMPOTENCY_SEMANTICS_GAP",
        "REFUSAL_PROVENANCE_DESIGN_BLOCKED",
        "MISSION_1_52_NOT_MERGED",
        "MISSION_1_53_BASELINE_DRIFT",
        "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
    }
)

SELECTING_OUTCOMES = frozenset(
    {
        "INPUT_KEYED_REFUSAL_PROVENANCE_MODEL_SELECTED",
        "CONDITIONAL_NULL_DERIVATION_BINDING_SELECTED",
        "REFUSAL_PROVENANCE_MODEL_READY",
    }
)

REFUSAL_RESULTS = ("NOT_APPLICABLE", "UNKNOWN")
FORBIDDEN_RESULTS = ("SUPPORTS", "CONTRADICTS", "NEUTRAL")
RATINGS = frozenset({"STRONG", "MEDIUM", "WEAK", "FAIL"})
MIGRATION_HEAD = "0034_deterministic_derivation_provenance"

# The twenty audit questions §2 requires a design to answer from fields.
AUDIT_QUESTION_COUNT = 20


class ValidationError(Exception):
    """The record claims something this repository does not support."""


def _evaluator_reason_codes() -> set[str]:
    """The codes the evaluator actually raises.

    Read from the AST rather than by scanning for capitals: `__all__` entries and
    module constants are shaped exactly like reason codes, and a scan that picks
    them up would refuse an accurate record. Only the SECOND positional argument
    of a `_refuse(...)` call is a reason code.
    """
    tree = ast.parse(EVALUATOR.read_text(encoding="utf-8"))
    codes: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_refuse"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            codes.add(node.args[1].value)
    return codes


def validate(record: dict) -> None:  # noqa: C901
    outcome = record.get("primary_outcome")
    if outcome not in ALLOWED_OUTCOMES:
        raise ValidationError(f"primary_outcome {outcome!r} is not a section 47 outcome")

    # ------------------------------------------------------ exactly one design
    verdicts = record.get("option_verdicts", {})
    selected = [k for k, v in verdicts.items() if v.startswith("SELECTED")]
    if outcome in SELECTING_OUTCOMES:
        if len(selected) != 1:
            raise ValidationError(
                f"§29 requires exactly one selected design; {len(selected)} are marked SELECTED"
            )
        for name in ("A", "B", "C"):
            if name not in verdicts:
                raise ValidationError(f"option {name} was not evaluated")
    elif selected:
        raise ValidationError("a blocker outcome may not also select a design")

    # ------------------------------------------------------ the matrix is real
    matrix = record.get("option_matrix", {})
    criteria = matrix.get("criteria", [])
    if len(criteria) != 12:
        raise ValidationError(f"§28 lists twelve criteria; the matrix carries {len(criteria)}")
    for name in ("A", "B", "C"):
        column = matrix.get(name, {})
        for criterion in criteria:
            rating = column.get(criterion)
            if rating not in RATINGS:
                raise ValidationError(
                    f"option {name} rates {criterion} as {rating!r}; §28 allows only {sorted(RATINGS)}"
                )
    if any(v == "FAIL" for k, v in matrix.get("A", {}).items() if k in criteria) and selected == [
        "A"
    ]:
        raise ValidationError("a design with a FAIL rating may not be selected")

    # ------------------------------------- ephemeral logs may never be selected
    if verdicts.get("C", "").startswith("SELECTED"):
        raise ValidationError(
            "the interpretation-run logs expire; they cannot be durable refusal provenance"
        )
    if matrix.get("C", {}).get("RETENTION_DURABILITY") != "FAIL":
        raise ValidationError(
            "option C must be rated FAIL on retention: its parent runs carry expires_at and its "
            "inputs cascade"
        )

    # ------------------------------------------------------------ no fake Claim
    entity = record.get("selected_entity", {})
    absent = {f["field"] for f in entity.get("fields_deliberately_absent", [])}
    for forbidden in ("claim_revision_id", "claim_id", "evidence_id"):
        if forbidden not in absent:
            raise ValidationError(
                f"the refusal entity must deliberately omit {forbidden}, and the record does not "
                "say so"
            )
    present = {f["field"] for f in entity.get("fields", [])}
    for forbidden in ("claim_revision_id", "claim_id", "evidence_id"):
        if forbidden in present:
            raise ValidationError(f"the refusal entity declares {forbidden}; it must not")
    for flag in ("inferred_claim_created", "evidence_created", "refusal_table_created"):
        if record.get(flag) is not False:
            raise ValidationError(f"the STOP CONDITION forbids `{flag}`")

    # -------------------------------------------------- refusal-only vocabulary
    if tuple(record.get("refusal_result_vocabulary", ())) != REFUSAL_RESULTS:
        raise ValidationError(f"a refusal store accepts exactly {REFUSAL_RESULTS}")
    for forbidden in FORBIDDEN_RESULTS:
        if forbidden not in record.get("refusal_result_vocabulary_excludes", []):
            raise ValidationError(f"{forbidden} must be excluded from the refusal vocabulary")
        if forbidden in record.get("refusal_result_vocabulary", []):
            raise ValidationError(f"{forbidden} is not a refusal")

    # ------------------------------- reason codes match the evaluator's source
    reasons = record.get("reason_codes", {})
    recorded = {entry["code"] for entry in reasons.get("codes", [])}
    actual = _evaluator_reason_codes()
    if not actual:
        raise ValidationError("no reason codes could be read from the evaluator source")
    if recorded != actual:
        raise ValidationError(
            f"the record's reason codes do not match the evaluator's. "
            f"only in record: {sorted(recorded - actual)}; only in evaluator: {sorted(actual - recorded)}"
        )
    if reasons.get("invented_here") != 0:
        raise ValidationError("§12 forbids inventing or renaming reason-code vocabulary")
    for entry in reasons["codes"]:
        if entry["result"] not in REFUSAL_RESULTS:
            raise ValidationError(
                f"{entry['code']} maps to {entry['result']}, which is not a refusal"
            )
        if entry["gate"] == 1 and entry["threshold_required"]:
            raise ValidationError(
                f"{entry['code']} refuses before the registration gate, so a registration must "
                "never be required for it"
            )
        if entry["gate"] > 1 and not entry["threshold_required"]:
            raise ValidationError(
                f"{entry['code']} reached the registration gate, so the registration it judged "
                "must be named"
            )

    # --------------------------------------------- the target is reconstructible
    target = record.get("candidate_target_representation", {})
    if "T2 alone" in target.get("selected", ""):
        raise ValidationError("a key with no preimage identifies a proposition nobody can read")
    if "target_proposition_key" not in entity_field_names(entity):
        raise ValidationError("the entity must store the candidate proposition key")
    if "target_proposition_facts" not in entity_field_names(entity):
        raise ValidationError("the entity must store the key's preimage")
    if not target.get("the_key_is_recomputable"):
        raise ValidationError("§31 requires the key to be recomputable from the stored facts")
    if "def proposition_key" not in CLAIM_MODEL.read_text(encoding="utf-8"):
        raise ValidationError("claim-model no longer exposes proposition_key")
    precedent = target.get("measured_precedent", {})
    if precedent.get("discriminator_key") != "proposition":
        raise ValidationError(
            "the live discriminator is `proposition`; a descriptor using another key could never "
            "produce the same proposition_key as the Claim it may become"
        )
    if precedent.get("live_claims_with_key_and_preimage") != precedent.get("claims_carrying_it"):
        raise ValidationError("the measured precedent is internally inconsistent")
    if len(record.get("audit_questions", {}).get("answers", [])) != AUDIT_QUESTION_COUNT:
        raise ValidationError(f"§2 asks {AUDIT_QUESTION_COUNT} questions; each needs a field")
    for answer in record["audit_questions"]["answers"]:
        if not answer.get("field", "").strip():
            raise ValidationError(f"audit question {answer['n']} is answered by no field")

    # ------------------------------------------- the JSON deviation is declared
    safeguards = record.get("json_safeguards", {})
    deviation = safeguards.get("target_descriptor_version_deliberately_absent", {})
    if deviation and deviation.get("status") != "OPERATOR_REVIEWABLE_DEVIATION":
        raise ValidationError(
            "a deliberate deviation from the brief must be labelled for review, not buried"
        )
    if deviation and not deviation.get("cost_if_wrong", "").strip():
        raise ValidationError("a deviation must state what it costs if the reasoning is wrong")
    if len(safeguards.get("why_it_is_not_an_untyped_dump", [])) < 5:
        raise ValidationError("§31 requires the JSON safeguards to be enumerated")

    # -------------------------------------------------------------- idempotency
    idempotency = record.get("idempotency", {})
    key = idempotency.get("key", [])
    for required in (
        "workspace_id",
        "input_signal_id",
        "target_proposition_key",
        "derivation_rule_version",
    ):
        if required not in key:
            raise ValidationError(f"the refusal identity key must contain {required}")
    if idempotency.get("every_column_not_null") is not True:
        raise ValidationError(
            "a UNIQUE containing a nullable column does not constrain rows where it is NULL; the "
            "identity key must be entirely NOT NULL or the guarantee is nominal"
        )
    if "new" not in idempotency.get("different_rule_version", "").lower():
        raise ValidationError("a different rule version must create a new historical row")
    if not idempotency.get("different_basis", {}).get("why", "").strip():
        raise ValidationError("§35 requires the basis-change behaviour to be decided explicitly")

    # ------------------------------------------------------------- append-only
    history = record.get("append_only_and_history", {})
    if history.get("supersession_column") is not False:
        raise ValidationError("§16 requires append-only history with no supersession column")
    transition = history.get("unknown_then_supports", {})
    if "NOTHING" not in transition.get("what_happens_to_U", ""):
        raise ValidationError(
            "§17: a later SUPPORTS must not rewrite, supersede or falsify the earlier refusal"
        )

    # -------------------------------------------------- basis and conditionality
    basis = record.get("semantic_equivalence_basis", {})
    if basis.get("no_fake_identifier_invented") is not True:
        raise ValidationError("§13 forbids inventing a basis identifier")
    if basis.get("nullable") is True and "semantic_equivalence_basis_id" in key:
        raise ValidationError(
            "a nullable basis cannot sit in the identity key without reintroducing the NULL trap"
        )

    # ------------------------------------- nothing existing was weakened
    unchanged = record.get("unchanged", {})
    for flag in (
        "migration_created",
        "claim_revision_id_made_nullable",
        "trigger_exemptions_changed",
        "evaluator_modified",
        "opportunity_changed",
    ):
        if record.get(flag) is not False:
            raise ValidationError(f"the STOP CONDITION forbids `{flag}`")
    if unchanged.get("evidence_reevaluation_policy") != "REPORT_NO_AUTOMATIC_WRITE":
        raise ValidationError("§27 carries policy D forward unchanged")
    if unchanged.get("source_id_absent_from_inferred_proposition_identity") is not True:
        raise ValidationError("ADR-036 keeps source_id out of INFERRED proposition identity")

    sql = MIGRATION_0034.read_text(encoding="utf-8")
    if not re.search(r"claim_revision_id\s+UUID\s+NOT NULL", sql, re.IGNORECASE):
        raise ValidationError(
            "the whole argument rests on claim_revision_id being NOT NULL, and migration 0034 no "
            "longer declares it so"
        )
    if (
        "UNIQUE (workspace_id, claim_revision_id, input_signal_id, derivation_rule_version)"
        not in sql
    ):
        raise ValidationError(
            "the identity key whose NULL behaviour decides Option B is no longer the one 0034 "
            "declares"
        )
    heads = sorted(p.stem for p in MIGRATIONS.glob("00*.sql"))
    if heads[-1] != MIGRATION_HEAD:
        raise ValidationError(f"migration head moved to {heads[-1]}; this mission creates none")

    guard = VALIDATE_CLAIMS.read_text(encoding="utf-8")
    if "OBSERVED" not in guard or "ClaimType" not in guard:
        raise ValidationError("validate_claims.py no longer restricts the interpreters to OBSERVED")

    # --------------------------------------------------- budget and end state
    counters = record.get("counters", {})
    moved = [
        name
        for name, pair in counters.items()
        if isinstance(pair, dict) and pair.get("before") != pair.get("after")
    ]
    if moved:
        raise ValidationError(f"every counter must be unchanged; these moved: {moved}")
    if counters.get("inferred_claims", {}).get("after") != 0:
        raise ValidationError("no INFERRED Claim may exist")
    if counters.get("claim_derivations", {}).get("after") != 0:
        raise ValidationError("no derivation row may be written")
    for key_, value in record.get("network_budget", {}).items():
        if value != 0:
            raise ValidationError(f"§37 expects {key_} = 0")
    model_use = record.get("model_use", {})
    for key_ in ("llm_calls", "embeddings", "calibration_labels", "parameters_fitted"):
        if model_use.get(key_) != 0:
            raise ValidationError(f"§38 expects {key_} = 0")
    if model_use.get("problem_family_status") != "PARKED":
        raise ValidationError("Problem-Family must remain PARKED")
    if model_use.get("profile_status") != "UNCALIBRATED":
        raise ValidationError("§39 keeps the reference profile UNCALIBRATED")
    if record.get("source_selected") is not None:
        raise ValidationError("no source may be selected")
    if len(record.get("stop_conditions_honoured", [])) < 15:
        raise ValidationError("the STOP CONDITION list is incomplete")
    if len(record.get("selection_criteria_check", [])) != 10:
        raise ValidationError("§29 lists ten selection criteria; each needs an explicit check")
    for entry in record["selection_criteria_check"]:
        if entry.get("met") is not True:
            raise ValidationError(
                f"selection criterion {entry['n']} is not met, so no design may be selected"
            )

    probe = record.get("validator_probe", {})
    if not probe.get("deliberate_violations"):
        raise ValidationError("the validator must be probed, or nothing establishes it checks")
    if probe.get("caught") != probe.get("deliberate_violations"):
        raise ValidationError("the probe reports uncaught violations; the record may not cite it")
    if probe.get("the_real_record_still_validates") is not True:
        raise ValidationError("the probe must confirm the real record still validates")

    recommendation = record.get("next_mission_recommendation", {})
    if "not started" not in recommendation.get("explicitly_not_started", "").lower():
        raise ValidationError("the record must say the next mission was not started")

    if not ADR.exists():
        raise ValidationError(f"{ADR.name} does not exist")
    adr = ADR.read_text(encoding="utf-8")
    if "**Status:** Accepted" not in adr:
        raise ValidationError("ADR-038 is not Accepted")
    if not BASELINE.exists():
        raise ValidationError(f"{BASELINE.name} does not exist; §0 requires a frozen baseline")


def entity_field_names(entity: dict) -> set[str]:
    return {f["field"] for f in entity.get("fields", [])}


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render(record: dict) -> str:  # noqa: C901
    lines: list[str] = []
    add = lines.append

    add("# Refusal Derivation Binding Design V1")
    add("")
    add(
        f"**Mission {record['mission']} — recorded {record['recorded_at']}. "
        f"Governed by {record['governs']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit")
    add("> `refusal-derivation-binding-design-v1.json` and re-run")
    add("> `infrastructure/scripts/render_refusal_provenance_design.py`.")
    add("")
    add(f"## Primary outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")
    add(f"*{record['why_not_forced']}*")
    add("")

    add("## The conflict, re-proved")
    add("")
    conflict = record["the_conflict_reproved"]
    add(conflict["method"])
    add("")
    add(_row(["probe", "attempted", "result", "mechanism"]))
    add(_row(["---", "---", "---", "---"]))
    for label in ("probe_A", "probe_A2_control", "probe_B", "probe_C"):
        entry = conflict[label]
        add(
            _row(
                [
                    f"**{label.replace('probe_', '').replace('_', ' ')}**",
                    entry.get("attempted", ""),
                    f"**{entry.get('result', '')}**",
                    entry.get("mechanism", entry.get("control", "")),
                ]
            )
        )
    add("")
    add(
        f"**A first attempt was wrong.** {conflict['probe_A_first_attempt_was_wrong_and_was_fixed']}"
    )
    add("")
    add(f"**The control matters.** {conflict['probe_A2_control']['why_it_matters']}")
    add("")
    add(f"**Probe C decides Option B.** {conflict['probe_C']['why_it_matters']}")
    add("")
    add(f"**Probe D refutes Option C.** {conflict['probe_D']['why_it_matters']}")
    add("")

    add("## What migration 0034 already anticipated")
    add("")
    anticipated = record["what_0034_already_anticipated"]
    add(f"`{anticipated['constraint']}`")
    add("")
    add(f"    {anticipated['definition']}")
    add("")
    add(anticipated["reading"])
    add("")
    add(f"*{anticipated['why_this_is_not_an_argument_for_option_B']}*")
    add("")

    add("## What a refusal record is")
    add("")
    definition = record["definition_of_refusal_provenance"]
    add(definition["is"])
    add("")
    add("It is not: " + ", ".join(definition["is_not"]) + ".")
    add("")
    add(f"**The bound worth stating.** {definition['the_bound_worth_stating']}")
    add("")
    distinction = record["central_distinction"]
    add(f"- A directional derivation answers: *{distinction['directional_derivation_answers']}*")
    add(f"- A refusal answers: *{distinction['refusal_answers']}*")
    add("")
    add(distinction["consequence"])
    add("")

    add("## The twenty audit questions")
    add("")
    add(_row(["", "question", "answered by"]))
    add(_row(["---", "---", "---"]))
    for answer in record["audit_questions"]["answers"]:
        add(_row([str(answer["n"]), answer["question"], f"`{answer['field']}`"]))
    add("")

    add("## Option matrix")
    add("")
    matrix = record["option_matrix"]
    add(_row(["criterion", "A separate record", "B nullable binding", "C run logs"]))
    add(_row(["---", "---", "---", "---"]))
    for criterion in matrix["criteria"]:
        add(
            _row(
                [
                    criterion.replace("_", " ").lower(),
                    f"**{matrix['A'][criterion]}**",
                    f"**{matrix['B'][criterion]}**",
                    f"**{matrix['C'][criterion]}**",
                ]
            )
        )
    add("")
    for name in ("A", "B", "C"):
        add(f"*{name}: {matrix[name]['note']}*")
        add("")
    for name in ("A", "B", "C"):
        add(f"**Option {name}.** {record['option_verdicts'][name]}")
        add("")

    add("## The selection criteria")
    add("")
    add(_row(["", "criterion", "met", "how"]))
    add(_row(["---", "---", "---", "---"]))
    for entry in record["selection_criteria_check"]:
        add(_row([str(entry["n"]), entry["criterion"], "**yes**", entry["how"]]))
    add("")

    add("## The candidate target proposition")
    add("")
    target = record["candidate_target_representation"]
    add(f"**{target['selected']} — {target['name']}.**")
    add("")
    add(f"    {target['shape']}")
    add("")
    add(target["why"])
    add("")
    add(f"**The key is verifiable rather than trusted.** {target['the_key_is_recomputable']}")
    add("")
    precedent = target["measured_precedent"]
    add(
        f"Measured: **{precedent['live_claims_with_key_and_preimage']}** live Claims carry both a "
        f"key and its preimage, and the discriminator key is `{precedent['discriminator_key']}` on "
        f"**{precedent['claims_carrying_it']}** of them. {precedent['note']}"
    )
    add("")
    add("Rejected:")
    add("")
    for entry in target["rejected"]:
        add(f"- **{entry['model']}** — {entry['why']}")
    add("")

    add("### Why this is not an untyped dump")
    add("")
    for item in record["json_safeguards"]["why_it_is_not_an_untyped_dump"]:
        add(f"- {item}")
    add("")
    deviation = record["json_safeguards"]["target_descriptor_version_deliberately_absent"]
    add(
        f"**A declared deviation — `{deviation['status']}`.** {deviation['brief_requested']} "
        f"{deviation['decision']} {deviation['why']}"
    )
    add("")
    add(f"*Cost if that reasoning is wrong:* {deviation['cost_if_wrong']}")
    add("")

    add("## The frozen entity")
    add("")
    entity = record["selected_entity"]
    add(f"Proposed name **`{entity['proposed_name']}`**. {entity['name_reasoning']}")
    add("")
    add(_row(["group", "field", "type", "null", "answers"]))
    add(_row(["---", "---", "---", "---", "---"]))
    for field in entity["fields"]:
        add(
            _row(
                [
                    field["group"],
                    f"`{field['field']}`",
                    field["type"],
                    "yes" if field["nullable"] else "no",
                    field["answers"],
                ]
            )
        )
    add("")
    add("**Deliberately absent:**")
    add("")
    for field in entity["fields_deliberately_absent"]:
        add(f"- `{field['field']}` — {field['why']}")
    add("")
    add("**Constraints:**")
    add("")
    add(_row(["constraint", "rule", "why"]))
    add(_row(["---", "---", "---"]))
    for constraint in entity["constraints"]:
        add(_row([f"`{constraint['name']}`", f"`{constraint['rule']}`", constraint["why"]]))
    add("")
    add("**Foreign keys:**")
    add("")
    add(_row(["column", "references", "on delete"]))
    add(_row(["---", "---", "---"]))
    for fk in entity["foreign_keys"]:
        add(_row([f"`{fk['column']}`", f"`{fk['references']}`", f"**{fk['on_delete']}**"]))
    add("")
    add("No foreign key to " + ", ".join(f"`{t}`" for t in entity["no_foreign_key_to"]) + ".")
    add("")
    add(entity["row_level_security"])
    add("")

    add("## Reason codes")
    add("")
    reasons = record["reason_codes"]
    add(f"Read from `{reasons['read_from']}`. Invented here: **{reasons['invented_here']}**.")
    add("")
    add(_row(["reason code", "result", "gate", "registration required"]))
    add(_row(["---", "---", "---", "---"]))
    for entry in reasons["codes"]:
        add(
            _row(
                [
                    f"`{entry['code']}`",
                    entry["result"],
                    str(entry["gate"]),
                    "**yes**" if entry["threshold_required"] else "no",
                ]
            )
        )
    add("")
    add(reasons["result_versus_reason"])
    add("")

    add("## The equivalence basis")
    add("")
    basis = record["semantic_equivalence_basis"]
    add(f"Nullable: **{basis['nullable']}**. {basis['why_it_can_be_NOT_NULL']}")
    add("")
    add(f"**{basis['the_consequence_worth_stating']}**")
    add("")

    add("## Idempotency")
    add("")
    idempotency = record["idempotency"]
    add("Key: " + ", ".join(f"`{c}`" for c in idempotency["key"]) + ".")
    add("")
    add(f"**{idempotency['why_that_matters']}**")
    add("")
    add(f"- Same inputs replayed: {idempotency['same_inputs_replayed']}")
    add(f"- Different rule version: {idempotency['different_rule_version']}")
    add(
        f"- Different basis: {idempotency['different_basis']['decision']} "
        f"{idempotency['different_basis']['why']}"
    )
    add("")
    add(f"*Cost stated:* {idempotency['different_basis']['cost_stated']}")
    add("")
    add(f"*{idempotency['measurement_value_deliberately_not_in_the_key']}*")
    add("")

    add("## Append-only, and the UNKNOWN-then-SUPPORTS transition")
    add("")
    history = record["append_only_and_history"]
    add(
        f"Supersession column: **{history['supersession_column']}**. {history['why_no_supersession']}"
    )
    add("")
    transition = history["unknown_then_supports"]
    add(f"- **T0** — {transition['T0']}")
    add(f"- **T1** — {transition['T1']}")
    add(f"- T1 writes: {', '.join(f'`{t}`' for t in transition['T1_writes'])}")
    add(f"- **What happens to the refusal: {transition['what_happens_to_U']}**")
    add("")
    add(transition["why"])
    add("")

    add("## A refusal is not a failure")
    add("")
    failure = record["domain_refusal_versus_system_failure"]
    add(
        f"Domain refusal: {', '.join(f'`{r}`' for r in failure['domain_refusal'])}. "
        f"System failure: {', '.join(failure['system_failure'])}."
    )
    add("")
    add(failure["rule"])
    add("")
    add(f"*{failure['precedent']}*")
    add("")

    add("## Evaluator integration")
    add("")
    integration = record["evaluator_integration"]
    add(f"Evaluator modified: **{integration['evaluator_modified']}**.")
    add("")
    add(f"    {integration['the_split']}")
    add("")
    add(integration["transactionality"])
    add("")
    add(f"*{integration['one_observation_about_the_current_evaluator']}*")
    add("")

    add("## Generic or family-specific")
    add("")
    generic = record["generic_or_family_specific"]
    add(f"**{generic['decision']}** {generic['why']}")
    add("")
    add(f"*{generic['not_over_generalised']}*")
    add("")

    add("## Queryability")
    add("")
    query = record["queryability"]
    add(f"*{query['question']}*")
    add("")
    add(f"    {query['answer']}")
    add("")
    add(query["why_this_is_a_criterion"])
    add("")

    add("## The validator was probed")
    add("")
    probe = record["validator_probe"]
    add(
        f"**{probe['caught']} of {probe['deliberate_violations']} deliberate violations caught**, "
        "and the real record still validates."
    )
    add("")
    add(probe["why"])
    add("")

    add("## Nothing moved")
    add("")
    add(_row(["counter", "before", "after"]))
    add(_row(["---", "---", "---"]))
    for name, pair in record["counters"].items():
        add(_row([f"`{name}`", str(pair["before"]), str(pair["after"])]))
    add("")
    budget = record["network_budget"]
    model_use = record["model_use"]
    add(
        "Research-data requests **{research_data_requests}**, documentation requests "
        "**{documentation_requests}**, metadata requests **{metadata_requests}**.".format(**budget)
    )
    add("")
    add(
        f"Model calls **{model_use['llm_calls']}**, embeddings **{model_use['embeddings']}**, "
        f"profile **{model_use['profile_status']}**, Problem-Family "
        f"**{model_use['problem_family_status']}**, migration created "
        f"**{record['migration_created']}**, refusal table created "
        f"**{record['refusal_table_created']}**."
    )
    add("")
    add("STOP conditions honoured:")
    add("")
    for item in record["stop_conditions_honoured"]:
        add(f"- {item}")
    add("")

    add("## Next mission")
    add("")
    recommendation = record["next_mission_recommendation"]
    add(f"**{recommendation['recommended']}** — {recommendation['scope']}")
    add("")
    add("It must prove:")
    add("")
    for item in recommendation["must_prove"]:
        add(f"- {item}")
    add("")
    add("Still open:")
    add("")
    for item in recommendation["still_open"]:
        add(f"- {item}")
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
        print(f"ok       {OUT.name} matches {SRC.name}, the evaluator and migration 0034")
        return 0

    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {OUT.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(f"adr      {record['adr']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
