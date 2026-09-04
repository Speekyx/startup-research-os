"""Render and validate the Mission 1.52 deterministic-evaluator record.

`validate()` does more than check the record against itself. It reads the
evaluator package, migration 0034, the zero-dependency runner and
`validate_claims.py`, and refuses a record that claims something the repository
does not implement -- a package at a path that does not exist, a forbidden
import that is actually present, a guard the record says was untouched, a
NOT NULL the record's central finding rests on. Every input is a repository
file, so this is deterministic from an empty database and safe in CI.

    uv run python infrastructure/scripts/render_deterministic_inferred_evaluator.py
    uv run python infrastructure/scripts/render_deterministic_inferred_evaluator.py --check
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "data" / "deterministic-inferred-evaluator-foundation-v1.json"
OUT = ROOT / "docs" / "data" / "deterministic-inferred-evaluator-foundation-v1.md"

EVALUATOR = ROOT / "packages" / "inferred-claim-evaluator" / "python"
PACKAGE = EVALUATOR / "sros_inferred_claim_evaluator"
RUNNER = ROOT / "infrastructure" / "scripts" / "run_python_tests.py"
VALIDATE_CLAIMS = ROOT / "infrastructure" / "scripts" / "validate_claims.py"
INTERPRETERS = ROOT / "services" / "nlp" / "python" / "sros_nlp" / "interpreters"
MIGRATION = (
    ROOT / "infrastructure" / "db" / "migrations" / "0034_deterministic_derivation_provenance.sql"
)
CONTRACT = ROOT / "docs" / "data" / "deterministic-inferred-claim-contract-v1.json"
ADR_036 = ROOT / "docs" / "architecture" / "adr" / "ADR-036-source-independent-claim-semantics.md"
ADR_037 = (
    ROOT / "docs" / "architecture" / "adr" / "ADR-037-deterministic-inferred-claim-contract.md"
)

ALLOWED_OUTCOMES = frozenset(
    {
        "DETERMINISTIC_INFERRED_EVALUATOR_FOUNDATION_READY",
        "REFUSAL_DERIVATION_BINDING_CONTRACT_GAP",
        "EVIDENCE_RE_EVALUATION_CONTRACT_GAP",
        "EVALUATOR_PACKAGE_DEPENDENCY_BOUNDARY_GAP",
        "THRESHOLD_REGISTRATION_CONTRACT_GAP",
        "SEMANTIC_EQUIVALENCE_INPUT_UNAVAILABLE",
        "MISSION_1_51_NOT_MERGED",
        "DETERMINISTIC_EVALUATOR_FOUNDATION_BLOCKED",
    }
)

ALLOWED_SECONDARY = frozenset(
    {
        "DETERMINISTIC_EVALUATOR_FOUNDATION_IMPLEMENTED",
        "EVALUATOR_FOUNDATION_NOT_IMPLEMENTED",
    }
)

EVALUATION_RESULTS = ("SUPPORTS", "CONTRADICTS", "NOT_APPLICABLE", "UNKNOWN")

# Absent imports are the enforcement, so the record's list is checked against
# the package rather than believed.
FORBIDDEN_IMPORTS = (
    "sros_acquisition",
    "sros_llm_gateway",
    "sros_evidence_aggregation",
    "sros_opportunity",
    "sros_nlp",
)

# A pure predicate reads no clock and no randomness. Same reasoning as the
# extractor rule: an evaluation whose answer depends on when it ran is not
# deterministic, whatever its docstring says.
FORBIDDEN_RUNTIME = ("datetime.now", "utcnow", "random.", "time.time", "astimezone")

REQUIRED_FIXTURES = ("A", "B", "C", "D", "E", "F", "G", "H")


class ValidationError(Exception):
    """The record claims something this repository does not implement."""


def _package_sources() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(PACKAGE.glob("*.py"))}


def validate(record: dict) -> None:  # noqa: C901
    outcome = record.get("primary_outcome")
    if outcome not in ALLOWED_OUTCOMES:
        raise ValidationError(f"primary_outcome {outcome!r} is not a section 44 outcome")
    if record.get("secondary_outcome") not in ALLOWED_SECONDARY:
        raise ValidationError(f"secondary_outcome {record.get('secondary_outcome')!r} is unknown")
    if not record.get("why_two_outcomes_reported_apart", "").strip():
        raise ValidationError("two outcomes are reported, so the record must say why they are two")

    # ------------------------------------------------------------- the package
    package = record.get("package", {})
    declared = ROOT / package.get("path", "")
    if not declared.is_dir():
        raise ValidationError(
            f"the record names package path {package.get('path')!r}, which is not a directory"
        )
    if declared != EVALUATOR.parent:
        raise ValidationError("the record's package path is not the evaluator package")
    if not CONTRACT.exists():
        raise ValidationError(f"{CONTRACT.name} does not exist; Mission 1.50 is not merged")
    proposed = json.loads(CONTRACT.read_text(encoding="utf-8"))["Q3_evaluator_boundary"][
        "proposed_package"
    ]
    if package.get("path") != proposed:
        raise ValidationError(
            f"ADR-037 Q3 named {proposed!r} and the package was built at {package.get('path')!r}"
        )
    if package.get("matches_adr_037_q3_proposed_package") is not True:
        raise ValidationError("the record must assert the package sits where the contract named it")

    sources = _package_sources()
    if not sources:
        raise ValidationError("the evaluator package contains no modules")
    for module in record.get("package", {}).get("modules", []):
        if module not in sources:
            raise ValidationError(f"the record names module {module!r}, which does not exist")

    for name, text in sources.items():
        for forbidden in FORBIDDEN_IMPORTS:
            if re.search(rf"^\s*(from|import)\s+{re.escape(forbidden)}\b", text, re.MULTILINE):
                raise ValidationError(f"{name} imports {forbidden}, which the boundary forbids")
        for forbidden in FORBIDDEN_RUNTIME:
            if forbidden in text:
                raise ValidationError(
                    f"{name} references {forbidden!r}; a deterministic evaluator reads no clock"
                )
        if re.search(r"\bpsycopg\b|\bhttpx\b|\brequests\b|\bsqlalchemy\b", text):
            raise ValidationError(f"{name} reaches a database or a network client")

    if package.get("writes_to_no_database") is not True:
        raise ValidationError("the record must assert the package writes to no database")
    for forbidden in FORBIDDEN_IMPORTS:
        if forbidden not in package.get("forbidden_dependencies_absent", []):
            raise ValidationError(f"{forbidden} is not recorded among the forbidden dependencies")
    if len(package.get("four_things_it_cannot_do", [])) != 4:
        raise ValidationError("the four structural refusals must all be recorded")

    manifest = (EVALUATOR / "pyproject.toml").read_text(encoding="utf-8")
    for dependency in package.get("dependencies", []):
        if dependency not in manifest:
            raise ValidationError(f"the record declares {dependency}, absent from pyproject.toml")

    # ------------------------------------------------------------- the runner
    registration = record.get("runner_registration", {})
    runner = RUNNER.read_text(encoding="utf-8")
    suite = registration.get("suite_added", "")
    if suite not in runner:
        raise ValidationError(f"{suite!r} is not registered in the zero-dependency runner")
    for shared in registration.get("shared_paths_added", []):
        if shared not in runner:
            raise ValidationError(f"{shared!r} is not on the runner's shared paths")
    if registration.get("bare_python_run_before_commit") is not True:
        raise ValidationError("§34's hard gate requires the bare-python runner before commit")
    if not isinstance(registration.get("bare_python_tests_total"), int):
        raise ValidationError("the bare-python test total must be recorded as a number")

    # -------------------------------------------------------------- the gates
    gates = record.get("the_four_gates", [])
    if [gate.get("order") for gate in gates] != [1, 2, 3, 4]:
        raise ValidationError("the four gates must be recorded in order")
    equivalence = gates[0]
    if "NOT_APPLICABLE" not in equivalence.get("rule", ""):
        raise ValidationError("a semantic mismatch must produce NOT_APPLICABLE")
    if "never produces CONTRADICTS" not in equivalence.get("never", ""):
        raise ValidationError("the record must state that a mismatch never contradicts")

    # ------------------------------------------------- what it never decides
    never = record.get("what_the_evaluator_never_decides", {})
    for required in ("independence", "reliability", "interpretation_confidence", "equivalence"):
        if not never.get(required, "").strip():
            raise ValidationError(
                f"the record must state that the evaluator never decides {required}"
            )

    # -------------------------------------------------- proposition identity
    identity = record.get("proposition_identity", {})
    excluded = set(identity.get("excluded_from_identity", []))
    for required in ("source_id", "measurement_value", "direction"):
        if required not in excluded:
            raise ValidationError(
                f"{required} must be excluded from proposition identity (ADR-036)"
            )
    included = set(identity.get("included_in_identity", []))
    if excluded & included:
        raise ValidationError(
            f"these facts are both identity and not: {sorted(excluded & included)}"
        )
    if "threshold_value" not in included:
        raise ValidationError("the threshold is part of the proposition and must be in identity")

    # -------------------------------------------------------------- fixtures
    fixtures = record.get("fixtures", {})
    for name in REQUIRED_FIXTURES:
        if name not in fixtures:
            raise ValidationError(f"fixture {name} is missing")
    if "never CONTRADICTS" not in fixtures["D"].get("result", ""):
        raise ValidationError("fixture D must record that a mismatch never contradicts")
    if "never SUPPORTS" not in fixtures["E"].get("result", ""):
        raise ValidationError("fixture E must record that an unknown never supports")
    if "INELIGIBLE" not in fixtures["G"].get("result", ""):
        raise ValidationError("fixture G must record that a post-hoc threshold is ineligible")

    # ---------------------------------------------------- the central finding
    conflict = record.get("the_conflict", {})
    sql = MIGRATION.read_text(encoding="utf-8") if MIGRATION.exists() else ""
    if not sql:
        raise ValidationError(f"{MIGRATION.name} does not exist; Mission 1.51 is not merged")
    if not re.search(r"claim_revision_id\s+UUID\s+NOT NULL", sql, re.IGNORECASE):
        raise ValidationError(
            "the finding rests on claim_revision_id being NOT NULL, and the migration does not "
            "declare it so"
        )
    if conflict.get("observation_2", {}).get("result") != "REFUSED":
        raise ValidationError("the record must record that a NULL claim_revision_id was refused")
    exemptions = conflict.get("observation_1", {}).get("exemptions_in_the_function", [])
    if any("INFERRED" in item for item in exemptions):
        raise ValidationError(
            "INFERRED must not appear among the trigger's exemptions: adding it is exactly what "
            "this mission refused to do"
        )
    if len(conflict.get("what_was_not_done", [])) < 4:
        raise ValidationError("the record must enumerate what was deliberately not done")

    # ----------------------------------------------- the guard stays untouched
    guard = record.get("the_guard_was_not_touched", {})
    if guard.get("modified") is not False or record.get("validate_claims_weakened") is not False:
        raise ValidationError("validate_claims.py must be untouched")
    guard_text = VALIDATE_CLAIMS.read_text(encoding="utf-8")
    if "OBSERVED" not in guard_text or "ClaimType" not in guard_text:
        raise ValidationError("validate_claims.py no longer restricts the interpreter to OBSERVED")
    for module in INTERPRETERS.glob("*.py"):
        if "sros_inferred_claim_evaluator" in module.read_text(encoding="utf-8"):
            raise ValidationError(
                f"{module.name} imports the evaluator; it must stay outside the interpreters"
            )

    # ----------------------------------------------- downstream compatibility
    downstream = record.get("downstream_compatibility", {})
    if downstream.get("no_dependency_in_either_direction") is not True:
        raise ValidationError("§32 requires no evaluator-to-aggregator dependency")
    if "producer-side" not in downstream.get("the_correction_this_mission_made", ""):
        raise ValidationError(
            "the NEUTRAL correction must say where the guarantee actually lives, or the record "
            "repeats the mistake it is describing"
        )

    # --------------------------------------------------- §22 stays a policy
    reevaluation = record.get("the_evidence_re_evaluation_question", {})
    if reevaluation.get("resolution") != "POLICY_D":
        raise ValidationError("§22 resolves to policy D")
    if reevaluation.get("measured", {}).get("revision_or_supersession_columns"):
        raise ValidationError(
            "policy D rests on scoring.evidence having no supersession column; the record lists one"
        )
    if reevaluation.get("status") != "RESOLVED_BY_POLICY_NOT_IMPLEMENTED":
        raise ValidationError("a policy decided is not a policy implemented, and must say so")

    # ------------------------------------------------------ nothing else moved
    counters = record.get("counters", {})
    if not counters:
        raise ValidationError("the counters must be recorded")
    moved = [
        name
        for name, pair in counters.items()
        if isinstance(pair, dict) and pair.get("before") != pair.get("after")
    ]
    if moved:
        raise ValidationError(f"every counter must be unchanged; these moved: {moved}")
    for required in ("claims", "evidence", "claim_derivations", "inferred_claims"):
        if required not in counters:
            raise ValidationError(f"counter {required!r} is missing")
    if counters["inferred_claims"]["after"] != 0:
        raise ValidationError("no INFERRED Claim may exist after this mission")
    if counters["claim_derivations"]["after"] != 0:
        raise ValidationError("no derivation row may be written by this mission")

    for flag in (
        "migration_created",
        "inferred_claim_created",
        "evidence_created",
        "threshold_registration_created",
        "claim_derivation_created",
        "source_boundary_modified",
        "aggregator_modified",
        "opportunity_changed",
    ):
        if record.get(flag) is not False:
            raise ValidationError(f"the STOP CONDITION forbids `{flag}`")
    if record.get("source_selected") is not None:
        raise ValidationError("no source may be selected")

    for key, value in record.get("network_budget", {}).items():
        if value != 0:
            raise ValidationError(f"§36 expects {key} = 0")
    model_use = record.get("model_use", {})
    for key in ("llm_calls", "embeddings", "calibration_labels", "parameters_fitted"):
        if model_use.get(key) != 0:
            raise ValidationError(f"§37 expects {key} = 0")
    if model_use.get("problem_family_status") != "PARKED":
        raise ValidationError("Problem-Family must remain PARKED")
    if model_use.get("profile_status") != "UNCALIBRATED":
        raise ValidationError("the reference profile must remain UNCALIBRATED")

    if len(record.get("stop_conditions_honoured", [])) < 15:
        raise ValidationError("the STOP CONDITION list is incomplete")

    probe = record.get("validator_probe", {})
    if probe.get("caught") != probe.get("deliberate_violations"):
        raise ValidationError(
            "the validator probe reports uncaught violations; a guard that misses one is a guard "
            "the record may not cite"
        )
    if not probe.get("deliberate_violations"):
        raise ValidationError("the validator must be probed, or nothing establishes it checks")
    if probe.get("the_real_record_still_validates") is not True:
        raise ValidationError("the probe must confirm the real record still validates")

    recommendation = record.get("next_mission_recommendation", {})
    if "not started" not in recommendation.get("explicitly_not_started", "").lower():
        raise ValidationError("the record must say the next mission was not started")
    if len(recommendation.get("options_identified_and_not_chosen", [])) < 3:
        raise ValidationError("the design options must be enumerated rather than pre-decided")

    for adr in (ADR_036, ADR_037):
        if not adr.exists():
            raise ValidationError(f"{adr.name} does not exist")

    # A last structural check on the package itself: the four-member result
    # vocabulary, read from the source rather than from the record.
    threshold_state = sources.get("contracts.py", "")
    tree = ast.parse(threshold_state)
    members: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "EvaluationResult":
            for statement in node.body:
                if isinstance(statement, ast.Assign) and isinstance(statement.targets[0], ast.Name):
                    members.append(statement.targets[0].id)
    if tuple(members) != EVALUATION_RESULTS:
        raise ValidationError(
            f"EvaluationResult must be exactly {EVALUATION_RESULTS}; found {tuple(members)}"
        )


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render(record: dict) -> str:  # noqa: C901
    lines: list[str] = []
    add = lines.append

    add("# Deterministic Inferred Claim Evaluator Foundation V1")
    add("")
    add(
        f"**Mission {record['mission']} — recorded {record['recorded_at']}. "
        f"Governed by {record['governs']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit")
    add("> `deterministic-inferred-evaluator-foundation-v1.json` and re-run")
    add("> `infrastructure/scripts/render_deterministic_inferred_evaluator.py`.")
    add("")

    add(f"## Primary outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")
    add(f"## Secondary outcome — `{record['secondary_outcome']}`")
    add("")
    add(record["secondary_outcome_statement"])
    add("")
    add(f"*{record['why_two_outcomes_reported_apart']}*")
    add("")

    add("## The conflict")
    add("")
    conflict = record["the_conflict"]
    add(f"**{conflict['question']}**")
    add("")
    add(conflict["method"])
    add("")
    add(_row(["attempted", "result", "mechanism"]))
    add(_row(["---", "---", "---"]))
    for key in ("observation_1", "observation_2"):
        entry = conflict[key]
        add(
            _row(
                [
                    entry["attempted"],
                    f"**{entry['result']}**",
                    f"`{entry['mechanism']}`",
                ]
            )
        )
    add("")
    add(
        "Trigger exemptions: "
        + ", ".join(f"`{e}`" for e in conflict["observation_1"]["exemptions_in_the_function"])
        + "."
    )
    add("")
    add(f"*{conflict['observation_1']['note']}*")
    add("")
    add(f"*{conflict['observation_2']['note']}*")
    add("")
    add(f"**The squeeze.** {conflict['the_squeeze']}")
    add("")
    add("**What was deliberately not done:**")
    add("")
    for item in conflict["what_was_not_done"]:
        add(f"- {item}")
    add("")
    add(f"**Why this is the upstream blocker.** {conflict['why_it_is_the_upstream_blocker']}")
    add("")

    add("## The Evidence re-evaluation question")
    add("")
    reevaluation = record["the_evidence_re_evaluation_question"]
    add(f"**{reevaluation['question']}**")
    add("")
    add(
        f"Revision or supersession columns on `scoring.evidence`: "
        f"**{len(reevaluation['measured']['revision_or_supersession_columns'])}**. "
        f"{reevaluation['measured']['note']}"
    )
    add("")
    add(f"**Resolution — {reevaluation['resolution']}.** {reevaluation['policy_d']}")
    add("")
    add(f"*Why not overwrite.* {reevaluation['why_not_overwrite']}")
    add("")
    add(f"*Why not a second Evidence row.* {reevaluation['why_not_a_second_evidence_row']}")
    add("")
    add(
        f"*Why this one is resolvable and the other is not.* "
        f"{reevaluation['why_this_one_is_resolvable_and_the_other_is_not']}"
    )
    add("")
    add(f"Status: **{reevaluation['status']}**.")
    add("")

    add("## The package")
    add("")
    package = record["package"]
    add(
        f"`{package['path']}`, distribution `{package['distribution']}`, depending on "
        + ", ".join(f"`{d}`" for d in package["dependencies"])
        + "."
    )
    add("")
    add(f"*{package['signal_model_declared_but_not_needed']}*")
    add("")
    add("**Four things it deliberately cannot do:**")
    add("")
    for item in package["four_things_it_cannot_do"]:
        add(f"- {item}")
    add("")
    add(f"**How that is enforced.** {package['enforcement']}")
    add("")

    add("### Joining the zero-dependency runner")
    add("")
    registration = record["runner_registration"]
    add(
        f"Suite `{registration['suite_added']}`; shared paths gained "
        + ", ".join(f"`{p}`" for p in registration["shared_paths_added"])
        + "."
    )
    add("")
    add(f"**{registration['why_one_named_package_and_not_the_monorepo']}**")
    add("")
    add(f"Bare-`python` tests run before commit: **{registration['bare_python_tests_total']}**.")
    add("")

    add("## The four gates")
    add("")
    for gate in record["the_four_gates"]:
        add(f"**{gate['order']}. {gate['gate']}** — {gate['rule']}")
        add("")
        for key in (
            "why_first",
            "no_conversion",
            "no_selection",
            "why_not_downgrade_to_post_hoc",
            "exactness",
            "never",
            "on_violation",
        ):
            if key in gate:
                add(f"  - *{key.replace('_', ' ')}*: {gate[key]}")
        add("")

    add("## What the evaluator never decides")
    add("")
    add(_row(["question", "why it is not the evaluator's"]))
    add(_row(["---", "---"]))
    for question, why in record["what_the_evaluator_never_decides"].items():
        add(_row([f"`{question}`", why]))
    add("")

    add("## Proposition identity")
    add("")
    identity = record["proposition_identity"]
    add("Excluded: " + ", ".join(f"`{f}`" for f in identity["excluded_from_identity"]) + ".")
    add("")
    add("Included: " + ", ".join(f"`{f}`" for f in identity["included_in_identity"]) + ".")
    add("")
    add("Proved:")
    add("")
    for item in identity["proved"]:
        add(f"- {item}")
    add("")
    add(f"*{identity['why_the_decimal_normalisation_matters']}*")
    add("")

    add("## Fixtures")
    add("")
    add(_row(["", "fixture", "witnesses", "result"]))
    add(_row(["---", "---", "---", "---"]))
    for name in REQUIRED_FIXTURES:
        entry = record["fixtures"][name]
        add(
            _row(
                [
                    f"**{name}**",
                    entry["name"],
                    ", ".join(f"`{w}`" for w in entry["witnesses"]),
                    entry["result"],
                ]
            )
        )
    add("")
    add(f"*{record['fixtures']['note']}*")
    add("")

    add("## Downstream compatibility")
    add("")
    downstream = record["downstream_compatibility"]
    add(f"**{downstream['question']}** {downstream['answer']}")
    add("")
    add(downstream["proof"])
    add("")
    add(f"**A correction this mission made.** {downstream['the_correction_this_mission_made']}")
    add("")

    add("## The guard was not touched")
    add("")
    guard = record["the_guard_was_not_touched"]
    add(f"`{guard['guard']}` modified: **{guard['modified']}**. {guard['why']}")
    add("")

    add("## Two tests, repaired rather than removed")
    add("")
    repointed = record["a_test_was_repointed_rather_than_deleted"]
    add(
        f"**Re-pointed.** `{repointed['test']}` asserted {repointed['asserted']}, which "
        f"was true of {repointed['was_true_of']}. {repointed['why_repointed']}"
    )
    add("")
    mine = record["a_test_of_my_own_was_wrong_and_was_replaced"]
    add(f"**Replaced.** `{mine['test']}` — {mine['defect']} {mine['repair']}")
    add("")
    add(f"*{mine['note']}*")
    add("")

    add("## The validator was probed")
    add("")
    probe = record["validator_probe"]
    add(
        f"**{probe['caught']} of {probe['deliberate_violations']} deliberate violations caught**, "
        f"and the real record still validates."
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
        f"calibration labels **{model_use['calibration_labels']}**, parameters fitted "
        f"**{model_use['parameters_fitted']}**, profile **{model_use['profile_status']}**, "
        f"Problem-Family **{model_use['problem_family_status']}**, source selected "
        f"**{record['source_selected'] or 'NONE'}**."
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
    add("Options identified and NOT chosen:")
    add("")
    for item in recommendation["options_identified_and_not_chosen"]:
        add(f"- {item}")
    add("")
    add(f"**Prefer:** {recommendation['prefer']}")
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
        print(f"ok       {OUT.name} matches {SRC.name}, the evaluator package and migration 0034")
        return 0

    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {OUT.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(f"also     {record['secondary_outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
