"""Render and validate the Mission 1.51 derivation-provenance schema record.

`validate()` does more than check the record against itself: it reads MIGRATION
0034 and cross-checks what the record claims against what the SQL actually says.
A record that described a constraint the migration does not contain, or a FK
action the migration does not use, is refused. Both are repository files, so
this is deterministic from an empty database and safe in CI.

    uv run python infrastructure/scripts/render_derivation_provenance_schema.py
    uv run python infrastructure/scripts/render_derivation_provenance_schema.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "data" / "deterministic-derivation-provenance-schema-v1.json"
OUT = ROOT / "docs" / "data" / "deterministic-derivation-provenance-schema-v1.md"
MIGRATION = (
    ROOT / "infrastructure" / "db" / "migrations" / "0034_deterministic_derivation_provenance.sql"
)
ADR = ROOT / "docs" / "architecture" / "adr" / "ADR-037-deterministic-inferred-claim-contract.md"

ALLOWED_OUTCOMES = frozenset(
    {
        "DETERMINISTIC_DERIVATION_PROVENANCE_SCHEMA_IMPLEMENTED",
        "DERIVATION_SCHEMA_CONTRACT_CONFLICT",
        "THRESHOLD_SCHEMA_CONTRACT_CONFLICT",
        "SEMANTIC_EQUIVALENCE_BASIS_SCHEMA_GAP",
        "DERIVATION_RETENTION_INVARIANT_BLOCKER",
        "MULTI_TENANT_SCHEMA_ISOLATION_BLOCKER",
        "MISSION_1_50_NOT_MERGED",
        "MISSION_1_51_BASELINE_DRIFT",
        "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
        "DETERMINISTIC_DERIVATION_SCHEMA_BLOCKED",
    }
)

THRESHOLD_STATUSES = ("PREREGISTERED", "SOURCE_NATIVE", "EXTERNAL_NORM", "POST_HOC", "UNKNOWN")
EVALUATION_RESULTS = ("SUPPORTS", "CONTRADICTS", "NOT_APPLICABLE", "UNKNOWN")
INELIGIBLE = ("POST_HOC", "UNKNOWN")

# Tables whose retention is bounded. A durable derivation must never depend on
# one of them, which is the finding ADR-037 rests on.
EXPIRING_TABLES = (
    "research.claim_interpretation_runs",
    "research.claim_interpretation_inputs",
)


class ValidationError(Exception):
    """The record claims something the migration does not implement."""


def validate(record: dict) -> None:  # noqa: C901
    outcome = record.get("primary_outcome")
    if outcome not in ALLOWED_OUTCOMES:
        raise ValidationError(f"primary_outcome {outcome!r} is not a section 43 outcome")

    if not MIGRATION.exists():
        raise ValidationError(f"{MIGRATION.name} does not exist")
    sql = MIGRATION.read_text(encoding="utf-8")

    # ---------------------------------------------------------------- tables
    names = {table["name"] for table in record.get("tables", [])}
    if len(names) != 2:
        raise ValidationError(f"exactly two additive records were frozen; {len(names)} recorded")
    for name in names:
        bare = name.split(".", 1)[1]
        if f"CREATE TABLE {name}" not in sql:
            raise ValidationError(f"the migration does not create {name}")
        if f"ALTER TABLE {name}" in sql and "ENABLE ROW LEVEL SECURITY" not in sql:
            raise ValidationError(f"{name} is altered without row level security")
        for clause in ("ENABLE ROW LEVEL SECURITY", "FORCE ROW LEVEL SECURITY"):
            if f"ALTER TABLE {name} {clause}" not in sql:
                raise ValidationError(f"{name} is missing `{clause}`")
        if f"CREATE POLICY tenant_isolation ON {name}" not in sql:
            raise ValidationError(f"{name} has no tenant_isolation policy")
        if bare not in sql:
            raise ValidationError(f"{bare} is not mentioned in the migration")

    # -------------------------------------------------- no dependency on expiry
    if record.get("no_foreign_key_to_expiring_runs") is not True:
        raise ValidationError(
            "the record must assert that neither table references a retention-bounded run"
        )
    for table in EXPIRING_TABLES:
        if re.search(rf"REFERENCES\s+{re.escape(table)}\b", sql):
            raise ValidationError(
                f"the migration references {table}, which expires. A Claim would outlive the "
                "record of how it was derived -- the exact defect ADR-037 exists to prevent."
            )

    # -------------------------------------------------------------- FK actions
    for entry in record.get("foreign_keys", []):
        action = entry.get("on_delete", "")
        if entry["column"] == "workspace_id":
            if action != "CASCADE":
                raise ValidationError("the workspace FK must CASCADE: tenant deletion removes data")
            continue
        if "NO ACTION" not in action:
            raise ValidationError(
                f"{entry['column']} uses {action!r}. CASCADE would let a retention purge delete "
                "the reasoning with its input."
            )
        if "DEFERRABLE INITIALLY DEFERRED" not in action:
            raise ValidationError(
                f"{entry['column']} is NO ACTION but not deferrable. An undeferred NO ACTION is "
                "checked at the end of each cascading statement, so a workspace deletion fails."
            )
    if sql.count("DEFERRABLE INITIALLY DEFERRED") < 4:
        raise ValidationError("the migration does not declare the four deferrable foreign keys")

    # ----------------------------------------------------------- vocabularies
    vocabularies = record.get("vocabularies", {})
    threshold = vocabularies.get("threshold_provenance_status", {})
    if tuple(threshold.get("values", ())) != THRESHOLD_STATUSES:
        raise ValidationError(f"threshold statuses must be exactly {THRESHOLD_STATUSES}")
    for status in THRESHOLD_STATUSES:
        if f"'{status}'" not in sql:
            raise ValidationError(f"the migration does not admit threshold status {status}")
    for status in INELIGIBLE:
        if status in threshold.get("calibration_eligible", []):
            raise ValidationError(f"{status} must never be calibration-eligible")
    if threshold.get("eligibility_is_derived_not_stored") is not True:
        raise ValidationError("calibration eligibility must be derived from status, never stored")
    if "calibration_eligible" in sql:
        raise ValidationError(
            "the migration stores a calibration_eligible column; it must be derived from status"
        )

    results = vocabularies.get("evaluation_result", {})
    if tuple(results.get("values", ())) != EVALUATION_RESULTS:
        raise ValidationError(f"evaluation results must be exactly {EVALUATION_RESULTS}")
    if "'NEUTRAL'" in sql:
        raise ValidationError(
            "NEUTRAL must not be an evaluation result: it asserts an observation bears on the "
            "Claim without bearing either way, which is not the same as not knowing"
        )
    kind = vocabularies.get("interpretation_kind", {})
    if tuple(kind.get("values", ())) != ("DETERMINISTIC", "MODEL_DERIVED"):
        raise ValidationError("interpretation_kind must mirror the existing global vocabulary")

    # ------------------------------------------------------------ constraints
    for entry in record.get("status_specific_constraints", []):
        if f"CONSTRAINT {entry['constraint']}" not in sql:
            raise ValidationError(f"the migration has no constraint {entry['constraint']}")

    # ------------------------------------------------------- idempotency keys
    tables = {table["name"]: table for table in record["tables"]}
    derivation_key = tables["research.claim_derivations"]["idempotency_key"]
    threshold_key = tables["research.threshold_registrations"]["idempotency_key"]
    if "derivation_rule_version" not in derivation_key:
        raise ValidationError(
            "the derivation idempotency key must include the rule version: replaying a different "
            "rule is different reasoning about the same relation"
        )
    if "provenance_status" not in threshold_key:
        raise ValidationError(
            "the threshold idempotency key must include provenance_status, or one logical bound "
            "registered under two provenances would be merged"
        )
    if tables["research.threshold_registrations"].get("stores_no_claim_identity") is not True:
        raise ValidationError("threshold provenance must not become Claim identity")
    for forbidden in ("proposition_key", "claim_id"):
        if re.search(
            rf"CREATE TABLE research\.threshold_registrations.*?\b{forbidden}\b",
            sql,
            re.DOTALL,
        ):
            block = sql.split("CREATE TABLE research.threshold_registrations", 1)[1]
            block = block.split("CREATE TABLE", 1)[0]
            if re.search(rf"^\s+{forbidden}\b", block, re.MULTILINE):
                raise ValidationError(
                    f"threshold_registrations declares `{forbidden}`; it stores no Claim identity"
                )

    # ------------------------------------------------------------ preregistration
    prereg = record.get("preregistration", {})
    if "retrieved_at" not in prereg.get("rule", ""):
        raise ValidationError("preregistration must compare against retrieval, not publication")
    if not prereg.get("human_foreknowledge_limit_retained"):
        raise ValidationError("the human-foreknowledge limitation must be retained, not hidden")

    # --------------------------------------------------------- append-only model
    binding = record.get("binding_and_versioning", {})
    if binding.get("binds_to") != "CLAIM_REVISION":
        raise ValidationError("derivation provenance must bind to the ClaimRevision")
    if binding.get("old_derivations_can_disappear") is not False:
        raise ValidationError("old reasoning must never disappear")
    if binding.get("a_claim_can_outlive_its_derivation") is not False:
        raise ValidationError("a Claim must not outlive its derivation")

    # ------------------------------------------------------------- migration
    migration = record.get("migration", {})
    for flag, message in (
        ("additive_only", "the migration must be additive only"),
        ("backfill", "no backfill"),
        ("data_migration", "no data migration"),
        ("deletions", "no deletions"),
    ):
        expected = flag == "additive_only"
        if migration.get(flag) is not expected:
            raise ValidationError(message)
    if migration.get("existing_rows_changed") != 0:
        raise ValidationError("no existing row may be changed")
    for statement in ("DROP TABLE", "DELETE FROM", "TRUNCATE", "UPDATE "):
        if statement in sql:
            raise ValidationError(f"the migration contains `{statement}`; it must be additive only")

    # ------------------------------------------------------ nothing else moved
    counters = record.get("counters", {})
    moved = [
        name
        for name, pair in counters.items()
        if isinstance(pair, dict) and pair.get("before") != pair.get("after")
    ]
    if moved:
        raise ValidationError(f"section 35 requires every counter unchanged; these moved: {moved}")

    for flag in ("evaluator_implemented", "inferred_claim_created", "evidence_created"):
        if record.get(flag) is not False:
            raise ValidationError(f"section 43 forbids `{flag}` in this mission")
    if record.get("source_selected") is not None:
        raise ValidationError("no source may be selected")
    for key, value in record.get("network_budget", {}).items():
        if value != 0:
            raise ValidationError(f"section 36 expects {key} = 0")
    model_use = record.get("model_use", {})
    if model_use.get("llm_calls") != 0 or model_use.get("embeddings") != 0:
        raise ValidationError("section 37 expects 0 model calls and 0 embeddings")
    if model_use.get("problem_family_status") != "PARKED":
        raise ValidationError("Problem-Family must remain PARKED")

    if not ADR.exists():
        raise ValidationError(f"{ADR.name} does not exist")


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render(record: dict) -> str:
    lines: list[str] = []
    add = lines.append

    add("# Deterministic Derivation Provenance Schema V1")
    add("")
    add(
        f"**Mission {record['mission']} — recorded {record['recorded_at']}. Governed by {record['governs']}.**"
    )
    add("")
    add("> **This document is GENERATED.** Edit")
    add("> `deterministic-derivation-provenance-schema-v1.json` and re-run")
    add("> `infrastructure/scripts/render_derivation_provenance_schema.py`.")
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
        f"`{migration['file']}`."
    )
    add("")
    add(
        f"Additive only **{migration['additive_only']}**, backfill **{migration['backfill']}**, "
        f"data migration **{migration['data_migration']}**, deletions "
        f"**{migration['deletions']}**, existing rows changed **{migration['existing_rows_changed']}**."
    )
    add("")
    add(f"*{migration['forward_only']}*")
    add("")

    add("## The two tables")
    add("")
    for table in record["tables"]:
        add(f"### `{table['name']}`")
        add("")
        add(table["purpose"])
        add("")
        add(f"- primary key: `{table['primary_key']}`")
        add(f"- tenant key: `{table['tenant_key']}`")
        add(f"- columns: {', '.join(f'`{c}`' for c in table['columns'])}")
        add(f"- idempotency: `{table['idempotency_key']}`")
        add("")
        add(table["idempotency_note"])
        add("")
        if "stores_no_claim_identity_evidence" in table:
            add(f"*{table['stores_no_claim_identity_evidence']}*")
            add("")

    add("## Foreign keys")
    add("")
    add(_row(["column", "references", "on delete", "why"]))
    add(_row(["---", "---", "---", "---"]))
    for entry in record["foreign_keys"]:
        add(
            _row(
                [
                    f"`{entry['column']}`",
                    f"`{entry['references']}`",
                    f"**{entry['on_delete']}**",
                    entry["why"],
                ]
            )
        )
    add("")
    add(f"**{record['no_foreign_key_to_expiring_runs_evidence']}**")
    add("")

    add("### The deferrable finding")
    add("")
    finding = record["the_deferrable_finding"]
    add(f"**What happened.** {finding['what_happened']}")
    add("")
    add(f"**The fix.** {finding['the_fix']}")
    add("")
    add(
        f"**Why it is correct rather than convenient.** {finding['why_it_is_correct_rather_than_convenient']}"
    )
    add("")
    add(f"*{finding['the_stale_row_it_left']}*")
    add("")

    add("## Vocabularies")
    add("")
    vocabularies = record["vocabularies"]
    threshold = vocabularies["threshold_provenance_status"]
    add(_row(["threshold provenance status", "calibration eligible"]))
    add(_row(["---", "---"]))
    for status in threshold["values"]:
        eligible = status in threshold["calibration_eligible"]
        add(_row([f"`{status}`", "**yes**" if eligible else "**no**"]))
    add("")
    add(f"*{threshold['eligibility_is_derived_not_stored_why']}*")
    add("")
    results = vocabularies["evaluation_result"]
    add(f"Evaluation results: {', '.join(f'`{v}`' for v in results['values'])}.")
    add("")
    add(f"**NEUTRAL is deliberately absent.** {results['neutral_deliberately_absent']}")
    add("")
    kind = vocabularies["interpretation_kind"]
    add(f"*{kind['pairing_rule']}*")
    add("")

    add("## Status-specific constraints")
    add("")
    add(_row(["constraint", "rule"]))
    add(_row(["---", "---"]))
    for entry in record["status_specific_constraints"]:
        add(_row([f"`{entry['constraint']}`", entry["rule"]]))
    add("")

    add("## Preregistration")
    add("")
    prereg = record["preregistration"]
    add(f"    {prereg['rule']}")
    add("")
    add(f"**Not `published_at`.** {prereg['published_at_deliberately_not_used']}")
    add("")
    add(f"**Not commit time.** {prereg['commit_time_deliberately_not_used']}")
    add("")
    add(f"**The limit is retained.** {prereg['human_foreknowledge_limit_retained']}")
    add("")
    add(f"*{prereg['evaluator_not_implemented']}*")
    add("")

    add("## Binding and versioning")
    add("")
    binding = record["binding_and_versioning"]
    add(f"Binds to **{binding['binds_to']}**. {binding['binds_to_why']}")
    add("")
    add(
        f"Supersession model: **{binding['supersession_model']}**. {binding['supersession_model_why']}"
    )
    add("")
    add(f"*No `evidence_id`.* {binding['evidence_id_deliberately_absent']}")
    add("")

    add("## Semantic-equivalence basis")
    add("")
    basis = record["semantic_equivalence_basis"]
    add(
        f"**Option {basis['option_selected']}**: {basis['representation']}. Third table created: "
        f"**{basis['third_table_created']}**."
    )
    add("")
    add(basis["why"])
    add("")
    add(f"*{basis['open_for_later']}*")
    add("")

    add("## Tenancy")
    add("")
    tenancy = record["tenancy"]
    add(f"- RLS enabled **{tenancy['rls_enabled']}**, forced **{tenancy['rls_forced']}**")
    add(f"- policy: `{tenancy['policy']}`, style copied from {tenancy['policy_style_copied_from']}")
    add(f"- {tenancy['composite_fks']}")
    add(f"- {tenancy['three_layers']}")
    add("")
    add(f"*{tenancy['leak_check_now_covers_them']}*")
    add("")

    add("## What was not touched")
    add("")
    untouched = record["what_was_not_touched"]
    for key, value in untouched.items():
        if key == "one_addition_to_an_existing_table":
            continue
        add(f"- `{key}` — **{value}**")
    add("")
    addition = untouched["one_addition_to_an_existing_table"]
    add(f"**One addition to an existing table.** `{addition['what']}`")
    add("")
    add(
        f"{addition['why']} {addition['why_it_is_safe']} Columns changed: **{addition['columns_changed']}**."
    )
    add("")

    add("## What was deliberately not built")
    add("")
    for key in ("repository_layer", "domain_types"):
        block = record[key]
        add(f"- **{key.replace('_', ' ')}** — created: **{block['created']}**. {block['why']}")
    add("")

    add("## Tests")
    add("")
    tests = record["tests"]
    add(f"`{tests['file']}` — **{tests['count']}** tests, owned by `{tests['owner_package']}`.")
    add("")
    add(f"*{tests['owner_why']}*")
    add("")
    proof = tests["retention_proof"]
    add(f"**The retention proof.** {proof['method']}")
    add("")
    add(f"Result: {proof['result']}")
    add("")
    add(f"*{proof['why_it_matters']}*")
    add("")
    add(f"**The idempotency contrast.** {tests['idempotency_contrast']['result']}")
    add("")
    add(f"**Signal purge refused.** {tests['signal_purge_refused']}")
    add("")

    add("## Counters")
    add("")
    add(_row(["counter", "before", "after"]))
    add(_row(["---", "---:", "---:"]))
    for name, pair in record["counters"].items():
        if isinstance(pair, dict):
            add(_row([name, str(pair["before"]), str(pair["after"])]))
    add("")
    model_use = record["model_use"]
    add(
        f"Model calls **{model_use['llm_calls']}**, embeddings **{model_use['embeddings']}**, "
        f"Problem-Family **{model_use['problem_family_status']}**, source selected "
        f"**{record['source_selected'] or 'NONE'}**, evaluator implemented "
        f"**{record['evaluator_implemented']}**, INFERRED Claim created "
        f"**{record['inferred_claim_created']}**."
    )
    add("")

    add("## Next mission")
    add("")
    recommendation = record["next_mission_recommendation"]
    add(f"**{recommendation['recommended']}** — {recommendation['scope']}")
    add("")
    add(f"Prefer: {recommendation['prefer']}")
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
        print(f"ok       {OUT.name} matches {SRC.name} and migration 0034")
        return 0

    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {OUT.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(f"migration {record['migration']['number']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
