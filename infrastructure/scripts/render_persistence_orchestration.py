"""Render and validate the Mission 1.55 persistence-orchestration record.

`validate()` reads the orchestrator's SOURCE and checks the record against it:
the routing must be exhaustive over the four evaluation results, the module must
import none of the forbidden packages, the evaluator must still reach no
database, and the two idempotency comparisons must compare a payload rather than
trust a key. Every input is a repository file, so this is deterministic from an
empty database and safe in CI.

    uv run python infrastructure/scripts/render_persistence_orchestration.py
    uv run python infrastructure/scripts/render_persistence_orchestration.py --check
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "data" / "deterministic-evaluation-persistence-orchestration-v1.json"
OUT = ROOT / "docs" / "data" / "deterministic-evaluation-persistence-orchestration-v1.md"

ORCHESTRATOR = ROOT / "services" / "nlp" / "python" / "sros_nlp" / "inferred_persistence.py"
EVALUATOR_PACKAGE = (
    ROOT / "packages" / "inferred-claim-evaluator" / "python" / "sros_inferred_claim_evaluator"
)
INTERPRETERS = ROOT / "services" / "nlp" / "python" / "sros_nlp" / "interpreters"
VALIDATE_CLAIMS = ROOT / "infrastructure" / "scripts" / "validate_claims.py"
MIGRATIONS = ROOT / "infrastructure" / "db" / "migrations"

ALLOWED_OUTCOMES = frozenset(
    {
        "DETERMINISTIC_EVALUATION_PERSISTENCE_ORCHESTRATION_READY",
        "EVIDENCE_DIRECTION_CONFLICT_REPORT_PERSISTENCE_GAP",
        "CLAIM_REVISION_REUSE_SEMANTICS_GAP",
        "DIRECTIONAL_TRANSACTION_ATOMICITY_BLOCKER",
        "PERSISTENCE_IDEMPOTENCY_CONFLICT_MODEL_GAP",
        "UNEXPECTED_PERSISTENCE_SCHEMA_GAP",
        "PERSISTENCE_PACKAGE_BOUNDARY_GAP",
        "MISSION_1_54_NOT_MERGED",
        "MISSION_1_55_BASELINE_DRIFT",
        "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
        "DETERMINISTIC_EVALUATION_PERSISTENCE_BLOCKED",
    }
)

DIRECTIONAL = ("SUPPORTS", "CONTRADICTS")
REFUSALS = ("NOT_APPLICABLE", "UNKNOWN")
FORBIDDEN_IMPORTS = (
    "sros_evidence_aggregation",
    "sros_llm_gateway",
    "sros_acquisition",
    "sros_opportunity",
)
MIGRATION_HEAD_EXPECTED = "0035_refusal_provenance"


class ValidationError(Exception):
    """The record claims something the orchestrator does not do."""


def _source() -> str:
    return ORCHESTRATOR.read_text(encoding="utf-8")


def _routed_results() -> set[str]:
    """The `EvaluationResult` members the router actually names.

    Read from the AST: the module explains the routing in prose too, and a text
    scan would find the members in a docstring and report a router that routes
    nothing (`testing-strategy.md` §23).
    """
    tree = ast.parse(_source())
    return {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "EvaluationResult"
    }


def validate(record: dict) -> None:  # noqa: C901
    outcome = record.get("primary_outcome")
    if outcome not in ALLOWED_OUTCOMES:
        raise ValidationError(f"primary_outcome {outcome!r} is not a section 71 outcome")

    if not ORCHESTRATOR.exists():
        raise ValidationError(f"{ORCHESTRATOR.name} does not exist")
    source = _source()

    # ------------------------------------------------------- the two readiness halves
    readiness = record.get("readiness_is_reported_in_two_halves", {})
    if readiness.get("foundation_ready") is not True:
        raise ValidationError("a READY outcome must state that the foundation is ready")
    if not isinstance(readiness.get("unattended_production_ready"), bool):
        raise ValidationError("§27 requires unattended readiness to be reported, not omitted")
    if readiness.get("unattended_production_ready") is True and not record.get("policy_d", {}).get(
        "durable_storage", ""
    ).strip().upper().startswith(("A ", "RESEARCH", "SCORING")):
        raise ValidationError(
            "unattended readiness claims a durable conflict declaration; the record says there "
            "is none"
        )
    if not readiness.get("why_they_are_not_the_same", "").strip():
        raise ValidationError("§27 forbids collapsing the two readiness statements")

    # ---------------------------------------------------------------- the owner
    owner = record.get("owner", {})
    module = ROOT / owner.get("module", "")
    if not module.is_file():
        raise ValidationError(
            f"the record names module {owner.get('module')!r}, which is not a file"
        )
    if module != ORCHESTRATOR:
        raise ValidationError("the record's module is not the orchestrator this validator reads")
    if INTERPRETERS in module.parents:
        raise ValidationError(
            "the orchestrator sits inside the interpreters directory, where validate_claims.py "
            "forbids a non-OBSERVED ClaimType"
        )
    for forbidden in FORBIDDEN_IMPORTS:
        if forbidden not in owner.get("forbidden_imports_absent", []):
            raise ValidationError(f"{forbidden} is not recorded among the forbidden imports")
        if f"import {forbidden}" in source or f"from {forbidden}" in source:
            raise ValidationError(f"the orchestrator imports {forbidden}")

    # The dependency direction, from the evaluator's side.
    for evaluator_module in EVALUATOR_PACKAGE.glob("*.py"):
        text = evaluator_module.read_text(encoding="utf-8")
        for forbidden in ("psycopg", "sros_nlp"):
            if forbidden in text:
                raise ValidationError(
                    f"{evaluator_module.name} names {forbidden}; the evaluator must stay pure and "
                    "the dependency direction is persistence -> evaluator"
                )
    if record.get("evaluator_modified") is not False:
        raise ValidationError("the STOP CONDITION forbids an evaluator change")

    # --------------------------------------------------------------- the routing
    routing = record.get("routing", {})
    if routing.get("paths") != 2:
        raise ValidationError("there are exactly two persistence paths")
    mapping = {entry["result"]: entry["path"] for entry in routing.get("mapping", [])}
    expected = {name: "DIRECTIONAL" for name in DIRECTIONAL}
    expected.update({name: "REFUSAL" for name in REFUSALS})
    if mapping != expected:
        raise ValidationError(f"the routing must be exactly {expected}; the record says {mapping}")
    if routing.get("no_else_branch") is not True:
        raise ValidationError("a default branch would route a future result by accident")
    if "NEUTRAL" in mapping:
        raise ValidationError("NEUTRAL is not an evaluation result and routes nowhere")

    routed = _routed_results()
    for name in DIRECTIONAL + REFUSALS:
        if name not in routed:
            raise ValidationError(f"the orchestrator never names EvaluationResult.{name}")
    if "NEUTRAL" in routed:
        raise ValidationError("the orchestrator names a NEUTRAL evaluation result")

    # ------------------------------------------------- the directional guarantees
    directional = record.get("directional_path", {})
    claim = directional.get("claim", {})
    if claim.get("claim_type") != "INFERRED":
        raise ValidationError("a directional outcome creates an INFERRED Claim")
    if (
        claim.get("interpretation_kind") != "DETERMINISTIC"
        or claim.get("model_version") is not None
    ):
        raise ValidationError("a deterministic Claim names no model version")
    if "build_claim" not in claim.get("built_by", ""):
        raise ValidationError("§20 requires the canonical Claim builder")
    if "build_claim" not in source:
        raise ValidationError("the orchestrator does not call the canonical Claim builder")
    if directional.get("evidence_factors", {}).get("reliability") is not None:
        raise ValidationError("§57 forbids assigning reliability here")

    for deviation_key in ("ordering_deviation",):
        deviation = directional.get(deviation_key, {})
        if deviation and deviation.get("status") != "STATED_DEVIATION":
            raise ValidationError(f"{deviation_key} must be labelled as a stated deviation")

    # ------------------------------------------------------------- the statement
    statement = record.get("the_statement", {})
    for excluded in ("source", "measurement value", "direction"):
        if excluded not in statement.get("excludes", []):
            raise ValidationError(
                f"the Claim statement must exclude the {excluded}, or a second witness creates a "
                "ClaimRevision and one proposition becomes many"
            )
    if not statement.get("proved", "").strip():
        raise ValidationError("the statement rule must be proved, not asserted")

    revisions = record.get("claim_revision_semantics", {})
    if "no new revision" not in revisions.get("second_witness_same_proposition", ""):
        raise ValidationError(
            "§10: a second witness for one source-independent proposition must not create a "
            "ClaimRevision"
        )

    # ---------------------------------------------------------------- idempotency
    idempotency = record.get("idempotency", {})
    if "payload" not in idempotency.get("principle", "").lower():
        raise ValidationError(
            "§51: idempotent means same identity AND same payload, and the record must say so"
        )
    for entity in ("derivation", "refusal"):
        block = idempotency.get(entity, {})
        if not block.get("payload_compared"):
            raise ValidationError(f"the {entity} replay must compare a payload, not just a key")
        if "CONFLICT" not in block.get("on_divergence", ""):
            raise ValidationError(f"a divergent {entity} payload must raise a conflict")
    if "evaluator_version" in idempotency.get("derivation", {}).get("payload_compared", []):
        raise ValidationError(
            "comparing evaluator_version would make rebuilding the software a conflict; the "
            "identity excludes it and so must the comparison"
        )
    evidence = idempotency.get("evidence", {})
    if evidence.get("unchanged_by_this_mission") is not True:
        raise ValidationError("Evidence identity must not change")
    if "version" in evidence.get("key", ""):
        raise ValidationError(
            "Mission 1.41 removed procedural versioning from Evidence identity; it must stay out"
        )

    # ------------------------------------------------------------------ policy D
    policy = record.get("policy_d", {})
    if policy.get("policy") != "REPORT_NO_AUTOMATIC_WRITE":
        raise ValidationError("§24 carries policy D forward unchanged")
    for flag in ("evidence_updated", "evidence_duplicated", "evidence_deleted", "silent_success"):
        if policy.get(flag) is not False:
            raise ValidationError(f"policy D forbids `{flag}`")
    if policy.get("selected_option") not in ("A", "B"):
        raise ValidationError("§25 requires one of the two candidate policies to be selected")
    if not policy.get("why_a", "").strip() and not policy.get("why_b", "").strip():
        raise ValidationError("the policy choice must be argued, not asserted")
    required_fields = {
        "workspace_id",
        "claim_id",
        "signal_id",
        "evidence_id",
        "existing_direction",
        "evaluated_direction",
        "target_proposition_key",
        "semantic_equivalence_basis_id",
    }
    missing = required_fields - set(policy.get("conflict_report_fields", []))
    if missing:
        raise ValidationError(f"§56: the conflict report omits {sorted(missing)}")
    if "REVIEW_REQUIRED" not in source:
        raise ValidationError("the orchestrator produces no REVIEW_REQUIRED state")

    # ---------------------------------------------------- failures are not refusals
    failure = record.get("system_failure_is_not_a_refusal", {})
    if not failure.get("error_codes"):
        raise ValidationError("§38 requires a structured error taxonomy")
    for code in ("THRESHOLD_NOT_FOUND", "DERIVATION_IDEMPOTENCY_CONFLICT"):
        if code not in failure["error_codes"]:
            raise ValidationError(f"{code} is not in the error taxonomy")
        if code not in source:
            raise ValidationError(f"the orchestrator never raises {code}")

    # --------------------------------------------------------------- thresholds
    threshold = record.get("threshold_handling", {})
    for flag in ("created", "selected", "mutated", "provenance_upgraded"):
        if threshold.get(flag) is not False:
            raise ValidationError(f"§34 forbids the orchestrator from having `{flag}` a threshold")
    if threshold.get("read_only") is not True:
        raise ValidationError("the threshold registration is read, never written")

    # ------------------------------------------------------------------- proofs
    proofs = record.get("proofs", {})
    for required in (
        "directional_commit",
        "refusal_commit",
        "rollback_after_the_full_directional_write",
        "rollback_at_the_evidence_step",
        "deferred_trigger",
        "unknown_then_supports",
        "rule_bump_opposite_direction",
    ):
        if not proofs.get(required, "").strip():
            raise ValidationError(f"the {required} proof is missing")
    if "nothing survives" not in proofs["rollback_at_the_evidence_step"]:
        raise ValidationError("a failure at the Evidence step must leave nothing behind")

    # -------------------------------------------------------- stated deviations
    aggregator = record.get("why_the_aggregator_was_not_re_run", {})
    if aggregator and aggregator.get("status") != "STATED_DEVIATION":
        raise ValidationError("a deviation from the brief must be labelled for review")
    concurrency = record.get("concurrency_limitation", {})
    if concurrency.get("tested") is True and not concurrency.get("behaviour", "").strip():
        raise ValidationError("a tested concurrency claim needs a described behaviour")
    if concurrency.get("database_is_the_final_authority") is not True:
        raise ValidationError("§36: the database uniqueness is the final authority")

    # ------------------------------------------------------- nothing else moved
    for flag in (
        "migration_created",
        "claim_identity_changed",
        "evidence_identity_changed",
        "trigger_changed",
        "validate_claims_changed",
        "canonical_pilot_run",
        "opportunity_changed",
    ):
        if record.get(flag) is not False:
            raise ValidationError(f"the STOP CONDITION forbids `{flag}`")
    heads = sorted(path.stem for path in MIGRATIONS.glob("00*.sql"))
    if heads[-1] != MIGRATION_HEAD_EXPECTED or record.get("migration_head") != heads[-1]:
        raise ValidationError(f"the migration head is {heads[-1]}; this mission creates none")
    guard = VALIDATE_CLAIMS.read_text(encoding="utf-8")
    if "OBSERVED" not in guard or "ClaimType" not in guard:
        raise ValidationError("validate_claims.py no longer restricts the interpreters to OBSERVED")

    counters = record.get("counters", {})
    moved = [
        key
        for key, pair in counters.items()
        if isinstance(pair, dict) and pair.get("before") != pair.get("after")
    ]
    if moved:
        raise ValidationError(f"every canonical counter must be unchanged; these moved: {moved}")
    for required in ("inferred_claims", "claim_derivations", "proposition_evaluation_refusals"):
        if counters.get(required, {}).get("after") != 0:
            raise ValidationError(f"{required} must be 0 in canonical data after this mission")
    if record.get("source_selected") is not None:
        raise ValidationError("no source may be selected")
    for key, value in record.get("network_budget", {}).items():
        if value != 0:
            raise ValidationError(f"§59 expects {key} = 0")
    model_use = record.get("model_use", {})
    for key in ("llm_calls", "embeddings", "calibration_labels", "parameters_fitted"):
        if model_use.get(key) != 0:
            raise ValidationError(f"§60 expects {key} = 0")
    if model_use.get("problem_family_status") != "PARKED":
        raise ValidationError("Problem-Family must remain PARKED")
    if model_use.get("profile_status") != "UNCALIBRATED":
        raise ValidationError("§61 keeps the reference profile UNCALIBRATED")

    probe = record.get("validator_probe", {})
    if not probe.get("deliberate_violations"):
        raise ValidationError("the validator must be probed, or nothing establishes it checks")
    if probe.get("caught") != probe.get("deliberate_violations"):
        raise ValidationError("the probe reports uncaught violations; the record may not cite it")

    if len(record.get("stop_conditions_honoured", [])) < 15:
        raise ValidationError("the STOP CONDITION list is incomplete")
    recommendation = record.get("next_mission_recommendation", {})
    if "not started" not in recommendation.get("explicitly_not_started", "").lower():
        raise ValidationError("the record must say the next mission was not started")
    if (
        recommendation.get("attended") is not True
        and readiness.get("unattended_production_ready") is False
    ):
        raise ValidationError(
            "an unattended pilot cannot be recommended while unattended readiness is false"
        )


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render(record: dict) -> str:  # noqa: C901
    lines: list[str] = []
    add = lines.append

    add("# Deterministic Evaluation Persistence Orchestration V1")
    add("")
    add(
        f"**Mission {record['mission']} — recorded {record['recorded_at']}. "
        f"Governed by {record['governs']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit")
    add("> `deterministic-evaluation-persistence-orchestration-v1.json` and re-run")
    add("> `infrastructure/scripts/render_persistence_orchestration.py`.")
    add("")
    add(f"## Primary outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")

    add("## Readiness, in two halves")
    add("")
    readiness = record["readiness_is_reported_in_two_halves"]
    add(
        f"Foundation ready **{readiness['foundation_ready']}**. Unattended production ready "
        f"**{readiness['unattended_production_ready']}**."
    )
    add("")
    add(readiness["why_they_are_not_the_same"])
    add("")
    add(f"**What makes it detectable anyway.** {readiness['what_makes_it_detectable_anyway']}")
    add("")
    add(f"    {readiness['the_query']}")
    add("")

    add("## The owner")
    add("")
    owner = record["owner"]
    add(f"`{owner['module']}`")
    add("")
    add(owner["why_here"])
    add("")
    add(f"**Not the evaluator package.** {owner['why_not_the_evaluator_package']}")
    add("")
    add(
        f"**Not inside `interpreters/`.** {owner['why_it_is_not_inside_the_interpreters_directory']}"
    )
    add("")
    add("Dependencies added: " + ", ".join(f"`{d}`" for d in owner["dependencies_added"]) + ".")
    add("")

    add("## The command")
    add("")
    command = record["command"]
    add(f"    {command['name']}")
    add("")
    add(f"Accepts {command['accepts']}. Evaluates: **{command['does_not_evaluate'] is False}**.")
    add("")
    add(command["why_evaluation_stays_separate"])
    add("")
    add(f"**Transaction owner: {command['transaction_owner']}.** {command['why']}")
    add("")

    add("### Why the target is passed alongside the outcome")
    add("")
    target = record["why_the_target_is_passed_alongside_the_outcome"]
    add(f"**The finding.** {target['finding']}")
    add("")
    add(f"**The resolution.** {target['resolution']}")
    add("")
    add(f"*Not resolved by* {target['not_resolved_by']}")
    add("")
    add(f"*{target['cross_check']}*")
    add("")

    add("## Routing")
    add("")
    routing = record["routing"]
    add(_row(["evaluation result", "path"]))
    add(_row(["---", "---"]))
    for entry in routing["mapping"]:
        add(_row([f"`{entry['result']}`", f"**{entry['path']}**"]))
    add("")
    add(f"Exhaustive over `{routing['exhaustive_over']}`, with no `else`. {routing['fail_closed']}")
    add("")
    add(f"**NEUTRAL.** {routing['neutral']}")
    add("")

    add("## The directional path")
    add("")
    directional = record["directional_path"]
    for index, step in enumerate(directional["steps"], start=1):
        add(f"{index}. {step}")
    add("")
    deviation = directional["ordering_deviation"]
    add(
        f"**A stated deviation — `{deviation['status']}`.** {deviation['brief_asked']} "
        f"{deviation['actual']} {deviation['why']}"
    )
    add("")
    claim = directional["claim"]
    add(
        f"The Claim: `{claim['claim_type']}` / `{claim['interpretation_kind']}`, origin "
        f"`{claim['origin']}`, temporality `{claim['temporality']}`, built by "
        f"`{claim['built_by']}`."
    )
    add("")
    add(claim["why_the_canonical_builder"])
    add("")
    factors = directional["evidence_factors"]
    add(f"*Reliability stays NULL.* {factors['why_reliability_is_null']}")
    add("")

    add("## The statement")
    add("")
    statement = record["the_statement"]
    add(
        f"Composed from {statement['composed_from']}, excluding "
        + ", ".join(f"the {e}" for e in statement["excludes"])
        + "."
    )
    add("")
    add(f"**{statement['why_it_is_load_bearing']}**")
    add("")
    add(f"*Proved:* {statement['proved']}")
    add("")
    add(f"*Where it lives:* {statement['where_it_lives']}. {statement['why_not_the_evaluator']}")
    add("")

    add("## Idempotency")
    add("")
    idempotency = record["idempotency"]
    add(f"**{idempotency['principle']}**")
    add("")
    add(_row(["entity", "identity", "on divergence"]))
    add(_row(["---", "---", "---"]))
    for name in ("claim", "derivation", "refusal", "evidence"):
        block = idempotency[name]
        add(
            _row(
                [
                    name,
                    f"`{block['key']}`",
                    f"**{block.get('on_divergence', block.get('extra_check', 'unchanged'))}**",
                ]
            )
        )
    add("")
    add(f"*{idempotency['derivation']['evaluator_version_excluded']}*")
    add("")
    add(f"*{idempotency['refusal']['why_it_matters']}*")
    add("")

    add("## Policy D")
    add("")
    policy = record["policy_d"]
    add(f"**Option {policy['selected_option']}** — {policy['option_a']}")
    add("")
    add(f"Rejected: {policy['option_b_rejected']}")
    add("")
    add(policy["why_a"])
    add("")
    add(f"**Detection is not re-implemented.** {policy['detection_is_not_re_implemented']}")
    add("")
    add(
        f"Evidence updated **{policy['evidence_updated']}**, duplicated "
        f"**{policy['evidence_duplicated']}**, deleted **{policy['evidence_deleted']}**, silent "
        f"success **{policy['silent_success']}**."
    )
    add("")
    add(
        "Conflict report fields: "
        + ", ".join(f"`{f}`" for f in policy["conflict_report_fields"])
        + "."
    )
    add("")
    add(f"*{policy['existing_direction_is_read_from_the_row']}*")
    add("")
    add(f"**Durable storage: {policy['durable_storage']}**")
    add("")

    add("## A system failure is not a refusal")
    add("")
    failure = record["system_failure_is_not_a_refusal"]
    add("Error codes: " + ", ".join(f"`{c}`" for c in failure["error_codes"]) + ".")
    add("")
    add(failure["why"])
    add("")

    add("## Thresholds")
    add("")
    threshold = record["threshold_handling"]
    add(
        f"Read-only **{threshold['read_only']}**; created **{threshold['created']}**, selected "
        f"**{threshold['selected']}**, mutated **{threshold['mutated']}**, provenance upgraded "
        f"**{threshold['provenance_upgraded']}**."
    )
    add("")
    add(threshold["why"])
    add("")
    add(f"*{threshold['post_hoc_still_persists']}*")
    add("")

    add("## Proofs")
    add("")
    add(_row(["proof", "result"]))
    add(_row(["---", "---"]))
    for name, value in record["proofs"].items():
        add(_row([name.replace("_", " "), value]))
    add("")

    add("## Two stated deviations, and one limitation")
    add("")
    aggregator = record["why_the_aggregator_was_not_re_run"]
    add(
        f"**The aggregator was not re-run — `{aggregator['status']}`.** {aggregator['brief_asked']} "
        f"{aggregator['what_was_done']} {aggregator['why_not_the_aggregator_itself']}"
    )
    add("")
    concurrency = record["concurrency_limitation"]
    add(f"**Concurrency is untested.** {concurrency['behaviour']}")
    add("")
    add(f"*{concurrency['why_recorded']}*")
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
        f"**{record['migration_created']}**, canonical pilot run "
        f"**{record['canonical_pilot_run']}**."
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
    add(f"**{recommendation['recommended']}**, attended: **{recommendation['attended']}**.")
    add("")
    add(recommendation["why_attended"])
    add("")
    add(recommendation["scope"])
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
        print(f"ok       {OUT.name} matches {SRC.name} and the orchestrator")
        return 0

    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {OUT.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(
        f"ready    foundation="
        f"{record['readiness_is_reported_in_two_halves']['foundation_ready']} "
        f"unattended="
        f"{record['readiness_is_reported_in_two_halves']['unattended_production_ready']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
