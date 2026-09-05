"""Render and validate the Mission 1.54 refusal-provenance schema record.

`validate()` reads MIGRATION 0035 and cross-checks what the record claims
against what the SQL actually says: the table it names must be created there,
the columns it lists must exist, the identity key must contain every member it
claims, the forbidden columns must be absent, no foreign key may reach a
retention-bounded run table, the provenance FKs must be deferrable, RLS must be
enabled and forced, and the reason codes must be the ones the evaluator raises.

Both the migration and the evaluator are repository files, so this is
deterministic from an empty database and safe in CI.

    uv run python infrastructure/scripts/render_refusal_provenance_schema.py
    uv run python infrastructure/scripts/render_refusal_provenance_schema.py --check
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "data" / "refusal-provenance-schema-v1.json"
OUT = ROOT / "docs" / "data" / "refusal-provenance-schema-v1.md"

MIGRATIONS = ROOT / "infrastructure" / "db" / "migrations"
MIGRATION = MIGRATIONS / "0035_refusal_provenance.sql"
MIGRATION_0034 = MIGRATIONS / "0034_deterministic_derivation_provenance.sql"
ADR = ROOT / "docs" / "architecture" / "adr" / "ADR-038-refusal-provenance-binding.md"
DESIGN = ROOT / "docs" / "data" / "refusal-derivation-binding-design-v1.json"
EVALUATOR = (
    ROOT
    / "packages"
    / "inferred-claim-evaluator"
    / "python"
    / "sros_inferred_claim_evaluator"
    / "threshold_state.py"
)
VALIDATE_CLAIMS = ROOT / "infrastructure" / "scripts" / "validate_claims.py"

ALLOWED_OUTCOMES = frozenset(
    {
        "REFUSAL_PROVENANCE_SCHEMA_IMPLEMENTED",
        "REFUSAL_TARGET_DESCRIPTOR_SCHEMA_CONFLICT",
        "REFUSAL_IDEMPOTENCY_SCHEMA_CONFLICT",
        "REFUSAL_RETENTION_INVARIANT_BLOCKER",
        "REFUSAL_WORKSPACE_CASCADE_BLOCKER",
        "REFUSAL_MULTI_TENANT_SCHEMA_BLOCKER",
        "REFUSAL_REASON_VOCABULARY_DRIFT",
        "MISSION_1_53_NOT_MERGED",
        "MISSION_1_54_BASELINE_DRIFT",
        "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
        "REFUSAL_PROVENANCE_SCHEMA_BLOCKED",
    }
)

REFUSAL_RESULTS = ("NOT_APPLICABLE", "UNKNOWN")
FORBIDDEN_RESULTS = ("SUPPORTS", "CONTRADICTS", "NEUTRAL")
# A refusal is an epistemic finding. An execution failure is not one, and the
# result vocabulary is what keeps it out.
FORBIDDEN_FAILURE_RESULTS = ("ERROR", "FAILED", "EXCEPTION", "TIMEOUT")

FORBIDDEN_COLUMNS = ("claim_revision_id", "evidence_id", "superseded_at", "is_current")
EXPIRING_TABLES = (
    "research.claim_interpretation_runs",
    "research.claim_interpretation_inputs",
)
IDENTITY_MEMBERS = (
    "workspace_id",
    "input_signal_id",
    "target_proposition_key",
    "derivation_rule_version",
    "semantic_equivalence_basis_id",
)


class ValidationError(Exception):
    """The record claims something the migration does not implement."""


def _statements(sql: str) -> str:
    """The migration with its `--` comments removed.

    A migration explains itself, so its prose NAMES the things it deliberately
    does not touch -- and a substring scan then reports the migration as touching
    them. That is `testing-strategy.md` §23, and the fix is to scan the
    STATEMENTS rather than to loosen the rule until the prose passes. This check
    first failed on the paragraph headed "WHAT IS NOT TOUCHED".
    """
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def _evaluator_reason_codes() -> set[str]:
    """The codes the evaluator raises, from the AST rather than a capitals scan:
    `__all__` entries and module constants are shaped identically."""
    tree = ast.parse(EVALUATOR.read_text(encoding="utf-8"))
    return {
        node.args[1].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_refuse"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and isinstance(node.args[1].value, str)
    }


def validate(record: dict) -> None:  # noqa: C901
    outcome = record.get("primary_outcome")
    if outcome not in ALLOWED_OUTCOMES:
        raise ValidationError(f"primary_outcome {outcome!r} is not a section 52 outcome")

    if not MIGRATION.exists():
        raise ValidationError(f"{MIGRATION.name} does not exist")
    sql = MIGRATION.read_text(encoding="utf-8")
    statements = _statements(sql)

    # ------------------------------------------------------------- the table
    table = record.get("table", {})
    name = table.get("name", "")
    if f"CREATE TABLE {name}" not in sql:
        raise ValidationError(f"the migration does not create {name!r}")
    if statements.count("CREATE TABLE ") != record.get("migration", {}).get("tables_created"):
        raise ValidationError("the record and the migration disagree on how many tables exist")
    if table.get("name_matches_the_frozen_design") is not True:
        raise ValidationError("the record must assert the table carries the frozen name")
    if DESIGN.exists():
        frozen = json.loads(DESIGN.read_text(encoding="utf-8"))["selected_entity"]["proposed_name"]
        if name != frozen:
            raise ValidationError(f"ADR-038 froze {frozen!r} and the migration built {name!r}")

    body = sql.split(f"CREATE TABLE {name} (", 1)[1].split("\n);", 1)[0]

    # ------------------------------------------------------------- columns
    declared = {column["column"] for column in table.get("columns", [])}
    if len(declared) != table.get("column_count"):
        raise ValidationError("the record's column list and column_count disagree")
    for column in table.get("columns", []):
        if not re.search(rf"^\s+{re.escape(column['column'])}\s", body, re.MULTILINE):
            raise ValidationError(f"the migration does not declare {column['column']!r}")
        pattern = rf"^\s+{re.escape(column['column'])}\s+\S+\s+NOT NULL"
        is_not_null = bool(re.search(pattern, body, re.MULTILINE))
        # `id` and `workspace_id` carry their NOT NULL differently (PRIMARY KEY,
        # and a REFERENCES clause on the next line), so they are exempt from the
        # textual form of the check rather than from the requirement.
        if column["column"] in ("id", "workspace_id"):
            continue
        if column["nullable"] == is_not_null:
            state = "NOT NULL" if is_not_null else "nullable"
            raise ValidationError(
                f"{column['column']!r} is {state} in the migration and the record disagrees"
            )

    for forbidden in FORBIDDEN_COLUMNS:
        if re.search(rf"^\s+{forbidden}\s", body, re.MULTILINE):
            raise ValidationError(
                f"the refusal table declares {forbidden!r}. A refusal has no ClaimRevision, no "
                "Evidence and no supersession -- those absences are why the table exists"
            )
    for column in record.get("table", {}).get("columns", []):
        for banned in ("schema_version", "descriptor_version"):
            if banned in column["column"]:
                raise ValidationError(
                    f"{column['column']!r} creates a refusal-only descriptor version namespace"
                )

    # --------------------------------------------------------- the identity
    identity = record.get("identity", {})
    if tuple(identity.get("members", ())) != IDENTITY_MEMBERS:
        raise ValidationError(f"the refusal identity must be exactly {IDENTITY_MEMBERS}")
    if identity.get("every_member_not_null") is not True:
        raise ValidationError(
            "a UNIQUE containing a nullable column does not constrain rows where it is NULL; "
            "every identity member must be NOT NULL or the guarantee is nominal"
        )
    # Anchored to the NAMED constraint. A bare search for a UNIQUE containing
    # `derivation_rule_version` matches the comment that quotes the OTHER table's
    # identity key, which is how this check first failed on a correct migration.
    unique_block = re.search(
        r"CONSTRAINT\s+proposition_evaluation_refusals_identity_key\s+UNIQUE\s*\(([^)]*)\)",
        sql,
        re.DOTALL,
    )
    if not unique_block:
        raise ValidationError("the migration declares no named refusal identity key")
    members = {
        part.strip()
        for part in unique_block.group(1).split(",")
        if part.strip() and not part.strip().startswith("--")
    }
    if members != set(IDENTITY_MEMBERS):
        raise ValidationError(f"the migration's identity key is {sorted(members)}")
    for member in IDENTITY_MEMBERS:
        if member in ("workspace_id",):
            continue
        if not re.search(rf"^\s+{member}\s+\S+\s+NOT NULL", body, re.MULTILINE):
            raise ValidationError(f"identity member {member!r} is not NOT NULL in the migration")

    # ------------------------------------------------------- foreign keys
    for entry in record.get("foreign_keys", []):
        if entry["columns"] == "workspace_id":
            if entry["on_delete"] != "CASCADE":
                raise ValidationError("the workspace FK must CASCADE: tenant deletion removes data")
            continue
        if "NO ACTION" not in entry["on_delete"]:
            raise ValidationError(
                f"{entry['columns']} uses {entry['on_delete']!r}; CASCADE would let a retention "
                "purge delete the audit with its input"
            )
        if not entry.get("deferrable"):
            raise ValidationError(
                f"{entry['columns']} is NO ACTION but not deferrable. An undeferred NO ACTION is "
                "checked at the end of each cascading statement, so a workspace deletion fails"
            )
    if statements.count("DEFERRABLE INITIALLY DEFERRED") < 3:
        raise ValidationError("the migration does not declare the three deferrable foreign keys")
    for expiring in EXPIRING_TABLES:
        if re.search(rf"REFERENCES\s+{re.escape(expiring)}\b", statements):
            raise ValidationError(
                f"the migration references {expiring}, which expires. A refusal would disappear on "
                "a retention schedule, which is the defect ADR-038 exists to prevent"
            )
    if re.search(r"REFERENCES\s+research\.claim_revisions\b", statements):
        raise ValidationError("a refusal must not reference a ClaimRevision")
    if re.search(r"REFERENCES\s+scoring\.evidence\b", statements):
        raise ValidationError("a refusal must not reference Evidence")

    # ------------------------------------------------------- vocabularies
    for result in REFUSAL_RESULTS:
        if f"'{result}'" not in sql:
            raise ValidationError(f"the migration does not admit {result}")
    for forbidden in FORBIDDEN_RESULTS + FORBIDDEN_FAILURE_RESULTS:
        if re.search(rf"evaluation_result\s+IN\s*\([^)]*'{forbidden}'", statements):
            raise ValidationError(f"the result vocabulary admits {forbidden}")

    reasons = record.get("reason_codes", {})
    recorded = {entry["code"] for entry in reasons.get("codes", [])}
    actual = _evaluator_reason_codes()
    if not actual:
        raise ValidationError("no reason codes could be read from the evaluator")
    if recorded != actual:
        raise ValidationError(
            f"reason-code drift. only in record: {sorted(recorded - actual)}; "
            f"only in evaluator: {sorted(actual - recorded)}"
        )
    if reasons.get("invented_here") != 0:
        raise ValidationError("no reason code may be invented or renamed")
    for entry in reasons["codes"]:
        if f"'{entry['code']}'" not in sql:
            raise ValidationError(f"the migration does not admit reason code {entry['code']}")
        if entry["result"] not in REFUSAL_RESULTS:
            raise ValidationError(f"{entry['code']} maps to a non-refusal result")
        if (entry["gate"] == 1) is entry["threshold_required"]:
            raise ValidationError(
                f"{entry['code']} is gate {entry['gate']} and threshold_required="
                f"{entry['threshold_required']}, which contradicts the gate ordering"
            )

    names = {constraint["name"] for constraint in record.get("check_constraints", [])}
    for required in ("result_reason_pairing_check", "threshold_conditional_check"):
        if not any(required in candidate for candidate in names):
            raise ValidationError(f"the record declares no {required}")
    for constraint in record.get("check_constraints", []):
        if f"CONSTRAINT {constraint['name']}" not in sql:
            raise ValidationError(f"the migration has no constraint {constraint['name']}")

    # ------------------------------------------------------------------ RLS
    rls = record.get("row_level_security", {})
    for flag, clause in (
        ("enabled", f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY"),
        ("forced", f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY"),
    ):
        if rls.get(flag) is not True or clause not in sql:
            raise ValidationError(f"{name} is missing `{clause}`")
    if f"CREATE POLICY tenant_isolation ON {name}" not in sql:
        raise ValidationError(f"{name} has no tenant_isolation policy")
    if "core.current_workspace_id()" not in sql:
        raise ValidationError("the policy does not use the repository's tenant function")

    # ------------------------------------------------------------- descriptor
    descriptor = record.get("descriptor", {})
    if descriptor.get("discriminator") != "proposition":
        raise ValidationError("the descriptor discriminator is `proposition`")
    if descriptor.get("key_recomputable") is not True:
        raise ValidationError("the key must be recomputable from the stored facts")
    if "does NOT reimplement" not in descriptor.get("enforcement_boundary", ""):
        raise ValidationError(
            "the enforcement boundary must be named honestly: claiming the database verifies the "
            "key would claim a guarantee nothing provides"
        )
    deviation = record.get("descriptor_version_operator_decision", {})
    if deviation.get("status") != "OPERATOR_ACCEPTED":
        raise ValidationError("the descriptor-version deviation must record the operator decision")
    if not deviation.get("future_rule", "").strip():
        raise ValidationError(
            "the deviation must state what happens if the global contract changes"
        )

    rejected = record.get("a_stricter_check_was_considered_and_rejected_on_a_measurement", {})
    if rejected:
        measured = rejected.get("measured", {})
        if measured.get("live_claims_passing") == measured.get("live_claims_total"):
            raise ValidationError(
                "a check rejected on a measurement must record a measurement that rejects it"
            )
        if not rejected.get("correction_to_the_design_record", "").strip():
            raise ValidationError(
                "if the design record overstated a fact, the correction must be recorded rather "
                "than left standing"
            )

    # ----------------------------------------------------------------- proofs
    proofs = record.get("proofs", {})
    retention = proofs.get("retention", {})
    if retention.get("interpretation_inputs_after") != 0:
        raise ValidationError("the interpretation inputs must cascade away")
    if retention.get("refusal_survived") is not True:
        raise ValidationError("the refusal must outlive the execution log")
    for key in ("signal_isolated_delete", "threshold_isolated_delete"):
        if "ForeignKeyViolation" not in proofs.get(key, {}).get("result", ""):
            raise ValidationError(f"{key} must be refused, not silently permitted")
    workspace = proofs.get("workspace_delete", {})
    if workspace.get("committed") is not True:
        raise ValidationError("tenant deletion must succeed at COMMIT")
    if workspace.get("deferred_constraint_failure") is not False:
        raise ValidationError("tenant deletion must not hit a deferred-constraint failure")
    if workspace.get("refusal_removed_with_the_workspace") is not True:
        raise ValidationError("a refusal is tenant-owned data and goes with its workspace")
    for entity in ("signal", "threshold_registration", "observed_claim"):
        if proofs.get("cross_workspace", {}).get(entity) != "ForeignKeyViolation":
            raise ValidationError(f"a cross-workspace {entity} reference must be refused")
    if proofs.get("row_level_security", {}).get("tenant_a_reads_tenant_b_refusal") != 0:
        raise ValidationError("RLS must hide another tenant's refusals")
    if proofs.get("key_recomputation", {}).get("matches") is not True:
        raise ValidationError("the stored key must recompute from the stored facts")

    # ------------------------------------------------------- nothing else moved
    migration = record.get("migration", {})
    for flag, expected in (
        ("additive_only", True),
        ("backfill", False),
        ("data_migration", False),
        ("deletions", False),
    ):
        if migration.get(flag) is not expected:
            raise ValidationError(f"migration.{flag} must be {expected}")
    if migration.get("existing_rows_changed") != 0:
        raise ValidationError("no existing row may be changed")
    for statement in ("DROP TABLE", "DELETE FROM", "TRUNCATE", "UPDATE ", "INSERT INTO"):
        if statement in statements:
            raise ValidationError(f"the migration contains `{statement}`; it must be additive only")
    heads = sorted(path.stem for path in MIGRATIONS.glob("00*.sql"))
    if heads[-1] != f"{migration.get('number')}_refusal_provenance":
        raise ValidationError(f"the migration head is {heads[-1]}, not the one recorded")
    if not MIGRATION_0034.exists():
        raise ValidationError("migration 0034 is missing; this table's FKs depend on it")

    unchanged = record.get("unchanged", {})
    for key in ("claim_derivations_schema", "require_evidence_for_generated_claim", "evaluator"):
        if "untouched" not in unchanged.get(key, ""):
            raise ValidationError(f"{key} must be untouched")
    if "ALTER TABLE research.claim_derivations" in statements:
        raise ValidationError("the migration alters claim_derivations")
    if "require_evidence_for_generated_claim" in statements:
        raise ValidationError("the migration touches the evidence-requirement trigger")
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
        raise ValidationError(f"every counter must be unchanged; these moved: {moved}")
    if record.get("production_refusal_rows") != 0:
        raise ValidationError("this mission creates no production refusal row")
    for flag in (
        "evaluator_modified",
        "repository_integration_added",
        "inferred_claim_created",
        "evidence_created",
        "opportunity_changed",
        "trigger_exemptions_changed",
        "claim_revision_id_made_nullable",
    ):
        if record.get(flag) is not False:
            raise ValidationError(f"the STOP CONDITION forbids `{flag}`")
    if record.get("source_selected") is not None:
        raise ValidationError("no source may be selected")
    for key, value in record.get("network_budget", {}).items():
        if value != 0:
            raise ValidationError(f"§43 expects {key} = 0")
    model_use = record.get("model_use", {})
    for key in ("llm_calls", "embeddings", "calibration_labels", "parameters_fitted"):
        if model_use.get(key) != 0:
            raise ValidationError(f"§44 expects {key} = 0")
    if model_use.get("problem_family_status") != "PARKED":
        raise ValidationError("Problem-Family must remain PARKED")
    if model_use.get("profile_status") != "UNCALIBRATED":
        raise ValidationError("§45 keeps the reference profile UNCALIBRATED")

    tables = record.get("table_counts", {})
    if tables.get("leak_check_tenant_tables_after") != tables.get(
        "leak_check_tenant_tables_before", 0
    ) + tables.get("tables_created_by_this_migration", 0):
        raise ValidationError("the tenant-table delta does not match the tables created")

    probe = record.get("validator_probe", {})
    if not probe.get("deliberate_violations"):
        raise ValidationError("the validator must be probed, or nothing establishes it checks")
    if probe.get("caught") != probe.get("deliberate_violations"):
        raise ValidationError("the probe reports uncaught violations; the record may not cite it")
    if probe.get("the_real_record_still_validates") is not True:
        raise ValidationError("the probe must confirm the real record still validates")

    if len(record.get("stop_conditions_honoured", [])) < 18:
        raise ValidationError("the STOP CONDITION list is incomplete")
    recommendation = record.get("next_mission_recommendation", {})
    if "not started" not in recommendation.get("explicitly_not_started", "").lower():
        raise ValidationError("the record must say the next mission was not started")

    if not ADR.exists():
        raise ValidationError(f"{ADR.name} does not exist")


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render(record: dict) -> str:  # noqa: C901
    lines: list[str] = []
    add = lines.append

    add("# Refusal Provenance Schema V1")
    add("")
    add(
        f"**Mission {record['mission']} — recorded {record['recorded_at']}. "
        f"Governed by {record['governs']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit")
    add("> `refusal-provenance-schema-v1.json` and re-run")
    add("> `infrastructure/scripts/render_refusal_provenance_schema.py`.")
    add("")
    add(f"## Primary outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")
    add(f"*{record['implementation_note_not_new_adr']}*")
    add("")

    add("## Migration")
    add("")
    migration = record["migration"]
    add(
        f"Head before **{migration['head_before']}**, new migration **{migration['number']}**, "
        f"`{migration['file']}`, creating **{migration['tables_created']}** table."
    )
    add("")
    add(
        f"Additive only **{migration['additive_only']}**, backfill "
        f"**{migration['backfill']}**, data migration **{migration['data_migration']}**, "
        f"deletions **{migration['deletions']}**, existing rows changed "
        f"**{migration['existing_rows_changed']}**."
    )
    add("")
    add(f"*{migration['why_no_backfill']}*")
    add("")

    add("## The table")
    add("")
    table = record["table"]
    add(f"### `{table['name']}`")
    add("")
    add(table["why_not_claim_evaluation_refusals"])
    add("")
    add(
        f"Primary key `{table['primary_key']}`, composite tenant key "
        f"`{table['composite_tenant_key']}`. {table['why_the_composite_key']}"
    )
    add("")
    add(_row(["group", "column", "type", "null", "answers"]))
    add(_row(["---", "---", "---", "---", "---"]))
    for column in table["columns"]:
        add(
            _row(
                [
                    "",
                    f"`{column['column']}`",
                    column["type"],
                    "yes" if column["nullable"] else "no",
                    column["answers"],
                ]
            )
        )
    add("")
    add("**Deliberately absent:**")
    add("")
    for column in table["columns_deliberately_absent"]:
        add(f"- `{column['column']}` — {column['why']}")
    add("")

    add("## Identity")
    add("")
    identity = record["identity"]
    add("`" + "`, `".join(identity["members"]) + "`")
    add("")
    add(f"**{identity['why_that_is_load_bearing']}**")
    add("")
    add(_row(["replay", "result"]))
    add(_row(["---", "---"]))
    for label, key in (
        ("same inputs", "replay_same_inputs"),
        ("new rule version", "replay_new_rule_version"),
        ("new reviewed basis", "replay_new_basis"),
        ("new target proposition", "replay_new_target"),
    ):
        add(_row([label, f"**{identity[key]}**"]))
    add("")

    add("## Foreign keys")
    add("")
    add(_row(["columns", "references", "on delete", "why"]))
    add(_row(["---", "---", "---", "---"]))
    for entry in record["foreign_keys"]:
        add(
            _row(
                [
                    f"`{entry['columns']}`",
                    f"`{entry['references']}`",
                    f"**{entry['on_delete']}**",
                    entry["why"],
                ]
            )
        )
    add("")
    add("No foreign key to " + ", ".join(f"`{t}`" for t in record["no_foreign_key_to"]) + ".")
    add("")

    add("## Check constraints")
    add("")
    add(_row(["constraint", "rule", "why"]))
    add(_row(["---", "---", "---"]))
    for constraint in record["check_constraints"]:
        add(_row([f"`{constraint['name']}`", f"`{constraint['rule']}`", constraint["why"]]))
    add("")
    add(f"*{record['why_the_redundant_vocabulary_checks_were_kept']}*")
    add("")

    add("### One stricter check was considered and rejected on a measurement")
    add("")
    rejected = record["a_stricter_check_was_considered_and_rejected_on_a_measurement"]
    measured = rejected["measured"]
    add(
        f"**{rejected['candidate']}** — enforceable as "
        f"`{rejected['expression_tested']}`, and rejected."
    )
    add("")
    add(
        f"Measured: **{measured['live_claims_passing']} of {measured['live_claims_total']}** live "
        f"Claims would have passed. The {measured['live_claims_total'] - measured['live_claims_passing']} "
        f"that would not are the `{measured['failing_kind']}` family, whose "
        + " and ".join(f"`{f}`" for f in measured["failing_facts"])
        + f" are {measured['shape']}."
    )
    add("")
    add(rejected["why"])
    add("")
    add(f"**A correction to the design record.** {rejected['correction_to_the_design_record']}")
    add("")
    add(f"*{rejected['lax_mode_trap']}*")
    add("")

    add("## Reason codes")
    add("")
    reasons = record["reason_codes"]
    add(
        f"Read from `{reasons['read_from']}` by {reasons['extraction']}. Invented here: "
        f"**{reasons['invented_here']}**. Drift against ADR-038: **{reasons['drift_against_adr_038']}**"
    )
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

    add("## The descriptor")
    add("")
    descriptor = record["descriptor"]
    add(f"    {descriptor['representation']}")
    add("")
    add(f"Vocabulary: {descriptor['vocabulary']}. Discriminator: `{descriptor['discriminator']}`.")
    add("")
    add(f"**Enforcement boundary.** {descriptor['enforcement_boundary']}")
    add("")
    add(f"*{descriptor['jsonb_round_trip_is_safe']}*")
    add("")
    deviation = record["descriptor_version_operator_decision"]
    add(f"### `{deviation['flag']}` — {deviation['status']}")
    add("")
    add(deviation["clarified_rationale"])
    add("")
    add(
        f"**`derivation_rule_version` is not a descriptor version.** "
        f"{deviation['derivation_rule_version_is_not_a_descriptor_version']}"
    )
    add("")
    add(f"**Future rule.** {deviation['future_rule']}")
    add("")

    add("## Row level security")
    add("")
    rls = record["row_level_security"]
    add(
        f"Enabled **{rls['enabled']}**, forced **{rls['forced']}**, policy "
        f"`{rls['policy']}` with `USING ({rls['using']})` and "
        f"`WITH CHECK ({rls['with_check']})`."
    )
    add("")

    add("## Proofs")
    add("")
    proofs = record["proofs"]
    retention = proofs["retention"]
    add(f"**Retention.** {retention['method']}")
    add("")
    add(
        f"Interpretation inputs **{retention['interpretation_inputs_before']} → "
        f"{retention['interpretation_inputs_after']}**; refusal survived "
        f"**{retention['refusal_survived']}**."
    )
    add("")
    for key, label in (
        ("signal_isolated_delete", "Signal, deleted alone"),
        ("threshold_isolated_delete", "Threshold registration, deleted alone"),
    ):
        entry = proofs[key]
        add(f"**{label}.** {entry['attempted']} → **{entry['result']}**.")
        if "why_it_matters" in entry:
            add("")
            add(entry["why_it_matters"])
        add("")
    workspace = proofs["workspace_delete"]
    add(f"**Workspace deletion.** {workspace['method']}")
    add("")
    add(
        f"Committed **{workspace['committed']}**, deferred-constraint failure "
        f"**{workspace['deferred_constraint_failure']}**, refusal removed "
        f"**{workspace['refusal_removed_with_the_workspace']}**."
    )
    add("")
    add(f"*{workspace['why_both_halves_are_tested']}*")
    add("")
    cross = proofs["cross_workspace"]
    add(
        "**Cross-workspace.** Signal **{signal}**, threshold "
        "**{threshold_registration}**, observed Claim **{observed_claim}**.".format(**cross)
    )
    add("")
    add(cross["structural"])
    add("")
    security = proofs["row_level_security"]
    add(
        f"**RLS.** Tenant A reads tenant B's refusals: "
        f"**{security['tenant_a_reads_tenant_b_refusal']}**. Tenant A writes one: "
        f"**{security['tenant_a_writes_tenant_b_refusal']}**."
    )
    add("")
    key_proof = proofs["key_recomputation"]
    add(
        f"**Key recomputation.** {key_proof['method']} — matches **{key_proof['matches']}**, "
        f"reversed input order matches **{key_proof['reversed_input_order_matches']}**, "
        f"mutating one fact changes it **{key_proof['mutating_one_fact_changes_the_key']}**."
    )
    add("")

    add("## Table counts")
    add("")
    counts = record["table_counts"]
    add(
        f"Leak-check tenant tables **{counts['leak_check_tenant_tables_before']} → "
        f"{counts['leak_check_tenant_tables_after']}**, `validate_schema` "
        f"**{counts['validate_schema_tables_after']}**, tables created "
        f"**{counts['tables_created_by_this_migration']}**."
    )
    add("")
    add(counts["note"])
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
    add(f"*{probe['two_false_positives_it_caught_in_itself']}*")
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
        f"**{model_use['problem_family_status']}**, production refusal rows "
        f"**{record['production_refusal_rows']}**, evaluator modified "
        f"**{record['evaluator_modified']}**."
    )
    add("")
    add("Untouched:")
    add("")
    for key, value in record["unchanged"].items():
        add(f"- `{key}` — {value}")
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
        print(f"ok       {OUT.name} matches {SRC.name}, migration 0035 and the evaluator")
        return 0

    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {OUT.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(f"table    {record['table']['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
