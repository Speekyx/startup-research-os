"""Mission 1.84.16, CI gate 86. The reasoning-summary contract decision, and why V6 was not prepared.

The operator moved one hard bound: `evidence_bound_reasoning_summary.maxLength`, from 900 to 1500,
as a semantic budget they own. This gate rebuilds the mission's record from the live code and the
committed artifacts and compares it with the file:

* the decision is the operator's words, pinned, and says the bound was not derived, estimated or
  proven optimal, and that the three historical lengths decided nothing;
* V5 is re-read and its refusal replayed under schema v1.1.0, and V5 is not revalidated under v1.2.0;
* schema v1.1.0 still hashes to its digest, and v1.2.0 differs from it at exactly one leaf, is
  finite, and moves exactly one generation-headroom row, whose target is derived from 1500 at 4/5;
* the persistence path is inspected layer by layer: the model, the write paths, every migration,
  the generated contracts and the gateway, with every literal 900 accounted for;
* gate v1.3.0 is unchanged, and its coupling to schema v1.1.0 is shown on the synthetic answer: a
  summary over 900 that v1.2.0 admits is refused inside the gate by v1.1.0's bound.

That coupling is where section 10 of the brief stops the mission, so no prompt v1.5.0, V6 runner or
V6 packet may exist, and the gate refuses one that does.

    uv run python infrastructure/scripts/render_second_opportunity_reasoning_summary_contract.py --check
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import pathlib
import re
from typing import Any

from sros_opportunity.generation_headroom import (
    ARRAY_HEADROOM_POLICY,
    GENERATION_HEADROOM_POLICY,
    generation_target,
    headroom_table,
)
from sros_opportunity.output_constraints import constraint_inventory
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
)
from sros_opportunity.second_opportunity_gate_v1_3 import (
    COMPONENT_VERSIONS_V1_3,
    OPERATOR_DECISION_V1_3,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
)
from sros_opportunity.second_opportunity_schema_v1_2 import (
    EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX,
    REASONING_SUMMARY_DECISION_BASIS,
    REASONING_SUMMARY_FIELD,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
    output_schema_sha256,
    semantic_schema_diff,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
MIGRATIONS = ROOT / "infrastructure" / "db" / "migrations"
PACKAGE = ROOT / "packages" / "opportunity-engine" / "python" / "sros_opportunity"

DECISION = DATA / "second-opportunity-reasoning-summary-contract-decision-v1.json"
RECORD = DATA / "second-opportunity-reasoning-summary-contract-v1.json"
RECORD_MD = DATA / "second-opportunity-reasoning-summary-contract-v1.md"
V5_RECORD = DATA / "second-opportunity-synthesis-execution-record-v5.json"
V5_RESPONSE = DATA / "second-opportunity-synthesis-response-v5.json"
V5_REVIEW_PACKET = DATA / "second-opportunity-human-review-packet-v5.json"
GATE_77 = SCRIPTS / "render_second_opportunity_semantic_gate_v1_3.py"
BOUNDED_CONTRACT = SCRIPTS / "render_second_opportunity_bounded_contract.py"
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
GATE_MODULE = PACKAGE / "second_opportunity_gate_v1_3.py"
HYPOTHESIS_MODULE = PACKAGE / "hypothesis.py"
GUARDS_MODULE = PACKAGE / "guards.py"
RUNNER_V5 = SCRIPTS / "run_second_opportunity_execution_v5.py"
WRITE_PATHS = (
    SCRIPTS / "run_opportunity_synthesis.py",
    SCRIPTS / "reconcile_opportunity_reliability.py",
)
CONTRACTS = (
    ROOT / "packages" / "contracts" / "python" / "sros_contracts" / "generated" / "domain.py",
    ROOT / "packages" / "contracts" / "schema" / "domain.v1.schema.json",
    ROOT / "packages" / "contracts" / "src" / "generated" / "domain.ts",
)
GATEWAY = ROOT / "services" / "gateway" / "python" / "sros_gateway"

#: What section 10 stopped. None of these may exist while the coupling stands.
NOT_PREPARED = (
    PACKAGE / "second_opportunity_prompt_v1_5.py",
    SCRIPTS / "run_second_opportunity_execution_v6.py",
    SCRIPTS / "render_second_opportunity_execution_packet_v6.py",
    DATA / "second-opportunity-synthesis-prompt-v6.json",
    DATA / "second-opportunity-synthesis-execution-packet-v6.json",
    DATA / "second-opportunity-synthesis-execution-approval-v6.json",
)
#: The architecture decision section 10 asked for, once a LATER mission takes it: a successor gate
#: bound to schema v1.2.0, frozen by its own record. Mission 1.84.17 re-pointed the check above from
#: an absence to that decision, the precedent absence-pinned gates follow: this record, which says
#: what 1.84.16 did and did not prepare, is unchanged.
SUCCESSOR_FREEZE = DATA / "second-opportunity-output-gate-v1.4-freeze-v1.json"
THIS_MISSION = (1, 84, 16)

MISSION = "mission-1.84.16"
START_COMMIT = "f3ff867f7b83c32324f148860940cbfa6f26746a"
BRANCH = "sprint-1/mission-1.84.16"
DECISION_FILE_SHA256 = "f8aa8b525b87cf561b7a8eb181d6fb68ffe50da10a62cd153af37137ecee0886"
OPERATOR_STATEMENT_SHA256 = "84c83f92204dcb10dabff8a44a2c8cddc03f600fb5456e1616bd539b460691d3"
OPERATOR_MESSAGE_SHA256 = "c329e908aea6596782757469439614b5744574a19975736194feac61513518a4"
SCHEMA_V1_1_SHA256 = "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988"
SCHEMA_V1_2_SHA256 = "7d67bad3df06691ba46a4dcc65cbf186bc5825a87719e985637aec68640e1b66"
GATE_IMPLEMENTATION_SHA256 = "cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3"
V5_PACKET_SHA256 = "da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a"
#: V5's record and response, byte for byte as Mission 1.84.15 left them.
V5_RECORD_FILE_SHA256 = "42da9819c066e107d4539c1c4a857425e6809c4389ab69249bebec154b51ea7a"
V5_RESPONSE_FILE_SHA256 = "7eb7c3f47d15b353228ae5a44d77ee6d31d593080ac5cc6c4ae9934b1bcd79aa"

PRIMARY_OUTCOME = "DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY"
BLOCKER = "SEMANTIC_GATE_V1_3_0_BINDS_OUTPUT_SCHEMA_V1_1_0"
SUMMARY_PATH = f"properties.{REASONING_SUMMARY_FIELD}.maxLength"
BOUNDARY_LENGTHS = (1199, 1200, 1201, 1499, 1500, 1501)
#: The demonstration's summary: the synthetic answer's own summary, repeated, so no word is new.
REPETITIONS = 5

#: The deployment's catalog, read on 2026-09-13. CI cannot re-read a deployment, so this block is
#: the recorded observation, and the migration scan below is what CI re-derives.
OBSERVED_DATABASE: dict[str, object] = {
    "observed_on": "2026-09-13",
    "observed_by": MISSION,
    "server_version": "16.4",
    "column": "research.opportunity_hypothesis_revisions.reasoning_summary",
    "data_type": "text",
    "character_maximum_length": None,
    "atttypmod": -1,
    "is_nullable": "NO",
    "check_constraints_naming_the_column": [],
    "triggers_on_the_table": [],
    "existing_rows": 2,
    "existing_longest_value_characters": 1456,
    "note": (
        "read from information_schema.columns, pg_attribute, pg_constraint and pg_trigger. A text "
        "column with no type modifier has no declared length; the two revisions of Opportunity #1 "
        "already hold reasoning summaries, the longest 1456 characters"
    ),
}

#: Every literal 900 or 720 the audit found on the persistence and execution paths, and what each is.
EXPECTED_LITERALS: tuple[tuple[str, int, str], ...] = (
    (
        "packages/opportunity-engine/python/sros_opportunity/synthesis.py",
        200,
        "the summary bound of historical schema v1.0.0, which v1.2.0 does not read",
    ),
    (
        "infrastructure/scripts/run_opportunity_synthesis.py",
        549,
        "an output-token count in Mission 1.31's cost estimate, not a character bound",
    ),
)
LITERAL_SCAN = (
    *sorted(PACKAGE.glob("*.py")),
    RUNNER_V5,
    FIXTURES,
    SCRIPTS / "render_second_opportunity_stage_6_9_preflight.py",
    *WRITE_PATHS,
    *sorted(MIGRATIONS.glob("*.sql")),
    *sorted(GATEWAY.rglob("*.py")),
)

CANONICAL_COUNTERS: dict[str, object] = {
    "acquisition.raw_records": 325,
    "acquisition.normalized_records": 325,
    "nlp.signals": 60,
    "research.claims": 91,
    "research.claim_revisions": 92,
    "scoring.evidence": 112,
    "epistemic.reliability_assessments": 4,
    "scoring.evidence_independence_groups": 0,
    "research.opportunities": 1,
    "research.opportunity_hypothesis_revisions": 2,
    "research.opportunity_hypothesis_evidence": 14,
    "nlp.embedding_provenance": 0,
    "registry.source_policy_reviews": 71,
    "scoring.scores": "ABSENT",
}

ACCOUNTING: dict[str, int] = {
    "MODEL_CALLS": 0,
    "PROVIDER_REQUESTS": 0,
    "MESSAGES_API_REQUESTS": 0,
    "TOKEN_COUNT_API_REQUESTS": 0,
    "TED_BYTES_SENT": 0,
    "CANONICAL_MUTATIONS": 0,
}


class ValidationError(RuntimeError):
    """The record disagrees with the decision, the live code, the migrations or the gate."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


#: Where these artifacts live in the repository, fixed when the module loads. The record names the
#: canonical location whatever copy the gate is pointed at, so a test or a probe reading a copy is
#: checked against the same record as the repository itself.
DECISION_REL = _rel(DECISION)
NOT_PREPARED_REL = tuple(_rel(path) for path in NOT_PREPARED)


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- the decision


def decision_block() -> dict[str, object]:
    if _sha_file(DECISION) != DECISION_FILE_SHA256:
        raise ValidationError("the operator's decision changed after it was recorded")
    decision = _load(DECISION)
    lines = decision["operator_statement_lines"]
    statement = "\n".join(lines)
    if decision["operator_statement"] != statement or _sha_text(statement) != (
        OPERATOR_STATEMENT_SHA256
    ):
        raise ValidationError("the operator's words and their digest disagree")
    if decision["OPERATOR_MESSAGE"]["sha256"] != OPERATOR_MESSAGE_SHA256:
        raise ValidationError("the decision names another message")
    expected = {
        "decision_owner": "OPERATOR",
        "decision_type": "OUTPUT_CONTRACT",
        "field": REASONING_SUMMARY_FIELD,
        "keyword": "maxLength",
        "old_hard_maximum": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"][
            REASONING_SUMMARY_FIELD
        ]["maxLength"],
        "new_hard_maximum": EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX,
        "DECISION_BASIS": REASONING_SUMMARY_DECISION_BASIS,
        "MATHEMATICALLY_DERIVED": False,
        "HISTORICAL_OUTPUT_LENGTH_DERIVED": False,
        "STATISTICALLY_ESTIMATED": False,
        "PROVEN_OPTIMAL": False,
        "historical_observations_used_to_derive_1500": False,
        "AUTHORISES_EXECUTION": False,
        "V5_HISTORICAL_VERDICT_UNCHANGED": True,
    }
    for key, value in expected.items():
        if decision.get(key) != value:
            raise ValidationError(f"the decision records {key}={decision.get(key)!r}")
    for line in (
        "1500",
        "OPERATOR_SEMANTIC_BUDGET",
        "Those values are historical observations only.",
    ):
        if line not in lines:
            raise ValidationError(f"the operator's words no longer say {line!r}")
    return {
        "file": DECISION_REL,
        "file_sha256": DECISION_FILE_SHA256,
        "operator_statement_sha256": OPERATOR_STATEMENT_SHA256,
        "operator_statement_lines": len(lines),
        "operator_message_sha256": OPERATOR_MESSAGE_SHA256,
        **expected,
        "historical_observations": decision["historical_observations"],
    }


# --------------------------------------------------------------------------- V5, as it was


def v5_block() -> dict[str, object]:
    if _sha_file(V5_RECORD) != V5_RECORD_FILE_SHA256 or _sha_file(V5_RESPONSE) != (
        V5_RESPONSE_FILE_SHA256
    ):
        raise ValidationError("V5's record or response was edited")
    if V5_REVIEW_PACKET.exists():
        raise ValidationError(
            "a human-review packet exists for V5, whose answer the schema refused"
        )
    record = _load(V5_RECORD)
    parsed = _load(V5_RESPONSE)["parsed_output"]
    replayed = list(schema_violations(dict(parsed), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1))
    if replayed != record["SCHEMA_VIOLATIONS"]:
        raise ValidationError(f"V5's refusal does not replay under schema v1.1.0: {replayed}")
    usage = record["ACTUAL_USAGE"]
    block = {
        "execution_packet_sha256": record["execution_packet_sha256"],
        "PRIMARY_OUTCOME": record["PRIMARY_OUTCOME"],
        "provider_requests": record["actual_provider_requests"],
        "model_calls": record["actual_model_calls"],
        "retries": record["retries"],
        "fallbacks": record["fallbacks"],
        "continuations": record["continuation_requests"],
        "repair_calls": record["repair_calls"],
        "stop_reason": record["STOP_REASON"],
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "thinking_tokens": usage["thinking_tokens"],
        "total_tokens": usage["total_tokens"],
        "cost_units": record["ACTUAL_COST"]["cost_units"],
        "stages": record["VALIDATION_STAGES"],
        "violations_replayed_under_v1_1_0": replayed,
        "canonical_persistence": record["CANONICAL_PERSISTENCE"],
        "canonical_mutations": record["CANONICAL_MUTATIONS"],
        "approval_consumed": record["EXECUTION_APPROVAL_CONSUMED"],
        "human_review_packet": record["HUMAN_REVIEW_PACKET"],
        "record_file_sha256": V5_RECORD_FILE_SHA256,
        "response_file_sha256": V5_RESPONSE_FILE_SHA256,
        "V5_HISTORICAL_VERDICT_UNCHANGED": True,
        "REVALIDATED_UNDER_V1_2_0": False,
        "CANDIDATE": False,
        "PERSISTABLE": False,
        "note": (
            "V5 stays judged against schema v1.1.0. Its answer is not run through v1.2.0 anywhere "
            "in this mission, and no verdict under v1.2.0 exists for it"
        ),
    }
    fixed = {
        "execution_packet_sha256": V5_PACKET_SHA256,
        "PRIMARY_OUTCOME": "EXECUTION_SCHEMA_REJECTED_NO_RETRY",
        "provider_requests": 1,
        "model_calls": 1,
        "retries": 0,
        "fallbacks": 0,
        "continuations": 0,
        "repair_calls": 0,
        "stop_reason": "tool_use",
        "input_tokens": 12899,
        "output_tokens": 3797,
        "thinking_tokens": 0,
        "total_tokens": 16696,
        "cost_units": 0.063768,
        "violations_replayed_under_v1_1_0": [
            f"{REASONING_SUMMARY_FIELD}: 1031 characters exceeds maxLength 900"
        ],
        "canonical_persistence": False,
        "canonical_mutations": 0,
        "approval_consumed": True,
        "human_review_packet": "NOT_PRODUCED",
    }
    for key, value in fixed.items():
        if block[key] != value:
            raise ValidationError(f"V5's {key} is {block[key]!r}, and it was {value!r}")
    stages = list(record["VALIDATION_STAGES"].values())
    if stages[:4] != ["PASSED"] * 4 or stages[4] != "FAILED" or set(stages[5:]) != {"NOT_REACHED"}:
        raise ValidationError("V5's stage table is not the one it recorded")
    return block


# --------------------------------------------------------------------------- schema v1.2.0


def _by_keyword(schema: dict[str, Any]) -> dict[tuple[str, str], object]:
    return {(c.path, c.keyword): c.value for c in constraint_inventory(schema)}


def schema_block(old: dict[str, Any], new: dict[str, Any]) -> dict[str, object]:
    if output_schema_sha256(old) != SCHEMA_V1_1_SHA256:
        raise ValidationError("schema v1.1.0 moved: it is historical and may not be edited")
    diff = semantic_schema_diff(old, new)
    approved = [(SUMMARY_PATH, old["properties"][REASONING_SUMMARY_FIELD]["maxLength"], 1500)]
    if diff != approved:
        raise ValidationError(f"OUTPUT_SCHEMA_V1_2_CONTAINS_UNAPPROVED_CHANGE: {diff}")
    if output_schema_sha256(new) != SCHEMA_V1_2_SHA256:
        raise ValidationError("schema v1.2.0 does not hash to the digest this mission recorded")
    before, after = _by_keyword(old), _by_keyword(new)
    if set(before) != set(after):
        raise ValidationError("the constraint inventory gained or lost a constraint")
    moved = sorted({key for key in before if before[key] != after[key]})

    def changed(keyword: str) -> int:
        return sum(1 for path, kw in moved if kw == keyword)

    return {
        "old_identity": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
        "old_sha256": SCHEMA_V1_1_SHA256,
        "new_identity": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
        "new_sha256": SCHEMA_V1_2_SHA256,
        "SEMANTIC_DIFF": [{"path": p, "old": o, "new": n} for p, o, n in diff],
        "field_path": f"{REASONING_SUMMARY_FIELD}.maxLength",
        "SCHEMA_FIELDS_ADDED": len(set(new["properties"]) - set(old["properties"])),
        "SCHEMA_FIELDS_REMOVED": len(set(old["properties"]) - set(new["properties"])),
        "REQUIREDNESS_CHANGED": old.get("required") != new.get("required"),
        "ENUMS_CHANGED": changed("enum") > 0,
        "MAX_ITEMS_CHANGED": changed("maxItems") > 0,
        "MIN_ITEMS_CHANGED": changed("minItems") > 0,
        "PATTERNS_CHANGED": changed("pattern") > 0,
        "ADDITIONAL_PROPERTIES_CHANGED": old.get("additionalProperties")
        != new.get("additionalProperties"),
        "ALL_OTHER_MAX_LENGTHS_CHANGED": changed("maxLength") - 1,
        "CONSTRAINTS": len(after),
        "CONSTRAINTS_CHANGED": [f"{path} {keyword}" for path, keyword in moved],
        "METADATA_DIFFERENCES": 0,
        "v1_1_0_edited": False,
    }


def finite_block(old: dict[str, Any], new: dict[str, Any]) -> dict[str, object]:
    walker = _module("bounded_contract_for_gate_86", BOUNDED_CONTRACT).unbounded_paths
    # A walker that finds nothing proves nothing unless it can find something: it is first shown
    # a copy of v1.2.0 with one bound removed, and must name exactly that path.
    opened = json.loads(json.dumps(new))
    opened["properties"]["observed_need"].pop("maxLength", None)
    if walker(opened) != ["observed_need"]:
        raise ValidationError(
            "the finite-bound walker no longer finds an unbounded path it is shown"
        )
    unbounded = walker(new)
    if unbounded:
        raise ValidationError(f"OUTPUT_SCHEMA_V1_2_NOT_FINITE: {unbounded}")
    return {
        "walker_control": "shown v1.2.0 with observed_need's bound removed, it names observed_need",
        "walker": f"{_rel(BOUNDED_CONTRACT)}: unbounded_paths, Mission 1.84.4's re-derivation",
        "FINITE_BOUND": True,
        "UNBOUNDED_REQUIRED_PATHS": 0,
        "UNBOUNDED_REACHABLE_PATHS": 0,
        "unbounded_paths_v1_1_0": walker(old),
        "unbounded_paths_v1_2_0": unbounded,
    }


def headroom_block(old: dict[str, Any], new: dict[str, Any]) -> dict[str, object]:
    def table(schema: dict[str, Any]) -> dict[str, list[object]]:
        return {
            row.path: [row.hard_maximum, row.generation_target, row.constraint_rule]
            for row in headroom_table(schema)
        }

    before, after = table(old), table(new)
    changed = sorted(
        path for path in set(before) | set(after) if before.get(path) != after.get(path)
    )
    if changed != [REASONING_SUMMARY_FIELD]:
        raise ValidationError(f"HEADROOM_SUCCESSOR_HAS_UNAPPROVED_DRIFT: {changed}")
    target = after[REASONING_SUMMARY_FIELD][1]
    if target != generation_target(EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX):
        raise ValidationError("the summary's target is not floor(1500 * 4/5) of the live bound")
    return {
        "GENERATION_HEADROOM_POLICY": GENERATION_HEADROOM_POLICY.name,
        "GENERATION_TARGET_RATIO": GENERATION_HEADROOM_POLICY.ratio_text,
        "ARRAY_HEADROOM_POLICY": ARRAY_HEADROOM_POLICY,
        "rows_v1_1_0": len(before),
        "rows_v1_2_0": len(after),
        "rows_changed": changed,
        "summary_v1_1_0": {
            "hard_maximum": before[REASONING_SUMMARY_FIELD][0],
            "target": before[REASONING_SUMMARY_FIELD][1],
        },
        "summary_v1_2_0": {"hard_maximum": after[REASONING_SUMMARY_FIELD][0], "target": target},
        "target_source": "the live schema v1.2.0 maxLength and the existing 4/5 policy, through headroom_table",
        "every_other_row_identical": all(
            before[p] == after[p] for p in before if p != REASONING_SUMMARY_FIELD
        ),
    }


def boundary_block(fixtures: Any, new: dict[str, Any]) -> dict[str, object]:
    target = generation_target(EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX)
    rows = []
    for length in BOUNDARY_LENGTHS:
        answer = fixtures.good_output(**{REASONING_SUMMARY_FIELD: "y" * length})
        violations = list(schema_violations(answer, new))
        rows.append(
            {
                "characters": length,
                "schema_v1_2_0": "FAIL" if violations else "PASS",
                "above_generation_target": length > target,
                "violations": violations,
            }
        )
    verdicts = [row["schema_v1_2_0"] for row in rows]
    if verdicts != ["PASS"] * 5 + ["FAIL"]:
        raise ValidationError(f"the new bound does not sit at 1500: {verdicts}")
    return {
        "answer": "the synthetic fixture's valid answer, with its summary replaced by synthetic text",
        "rows": rows,
        "target_diagnostics_authoritative": False,
    }


# --------------------------------------------------------------------------- persistence


def _literals(pattern: str) -> list[tuple[str, int]]:
    found = []
    regex = re.compile(pattern)
    for path in LITERAL_SCAN:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if regex.search(line):
                found.append((_rel(path), number))
    return found


def _model_bound() -> str:
    tree = ast.parse(HYPOTHESIS_MODULE.read_text(encoding="utf-8"))
    cls = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "OpportunityHypothesis"
    )
    annotated = {
        n.target.id: ast.unparse(n.annotation)
        for n in cls.body
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
    }
    if annotated.get("reasoning_summary") != "str":
        raise ValidationError("OpportunityHypothesis.reasoning_summary is no longer a plain str")
    for node in ast.walk(cls):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "len":
            raise ValidationError(
                "PERSISTENCE_MODEL_CONTRACT_REQUIRES_OPERATOR_DECISION: OpportunityHypothesis now "
                "measures a length"
            )
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            raise ValidationError("OpportunityHypothesis now slices a value")
    return "NONE"


def _migration_column() -> dict[str, object]:
    mentions = [
        (path.name, line.strip())
        for path in sorted(MIGRATIONS.glob("*.sql"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if "reasoning_summary" in line
    ]
    if len(mentions) != 1 or mentions[0][0] != "0029_opportunity_hypothesis_persistence.sql":
        raise ValidationError(
            f"a migration other than 0029 now names reasoning_summary: {mentions}"
        )
    if not re.fullmatch(r"reasoning_summary\s+TEXT\s+NOT NULL,", mentions[0][1]):
        raise ValidationError(
            f"DATABASE_STORAGE_CONTRACT_REQUIRES_OPERATOR_DECISION: the column reads {mentions[0][1]!r}"
        )
    return {
        "migration": mentions[0][0],
        "definition": mentions[0][1],
        "later_migrations_naming_it": 0,
    }


def _write_paths() -> list[dict[str, object]]:
    out = []
    for path in WRITE_PATHS:
        text = path.read_text(encoding="utf-8")
        if "sqlalchemy" in text:
            raise ValidationError(
                f"{path.name} now writes through an ORM this audit did not inspect"
            )
        inserts = "INSERT INTO research.opportunity_hypothesis_revisions" in text
        sliced = [
            line.strip()
            for line in text.splitlines()
            if "reasoning_summary" in line and re.search(r"\[\s*:?\s*\d*\s*:\s*\d+\s*\]", line)
        ]
        if not inserts or sliced:
            raise ValidationError(f"{path.name} does not write the summary as it is: {sliced}")
        out.append({"path": _rel(path), "inserts_the_revision": True, "slices_the_summary": False})
    runner = RUNNER_V5.read_text(encoding="utf-8")
    line = 'reasoning_summary=str(output.get("evidence_bound_reasoning_summary") or ""),'
    if runner.count(line) != 1:
        raise ValidationError(
            "stage 9 no longer passes the summary to OpportunityHypothesis as it is"
        )
    out.append(
        {
            "path": _rel(RUNNER_V5),
            "stage_9_constructs_the_hypothesis": True,
            "slices_the_summary": False,
        }
    )
    return out


def persistence_block() -> dict[str, object]:
    model = _model_bound()
    column = _migration_column()
    writes = _write_paths()
    contracts = [
        p
        for p in (*CONTRACTS, *GATEWAY.rglob("*.py"))
        if "reasoning_summary" in p.read_text(encoding="utf-8")
    ]
    if contracts:
        raise ValidationError(f"a contract or the gateway now carries the summary: {contracts}")
    guards = ast.parse(GUARDS_MODULE.read_text(encoding="utf-8"))
    large = sorted(
        {
            n.value
            for n in ast.walk(guards)
            if isinstance(n, ast.Constant) and type(n.value) is int and n.value >= 100
        }
    )
    if large:
        raise ValidationError(f"the prose guard now carries a length-sized number: {large}")
    literals = _literals(r"\b(900|720)\b")
    expected = [(path, line) for path, line, _why in EXPECTED_LITERALS]
    if literals != expected:
        raise ValidationError(f"a 900 or 720 appeared or moved on the audited paths: {literals}")
    return {
        "A_model": {
            "object": "OpportunityHypothesis.reasoning_summary",
            "source": _rel(HYPOTHESIS_MODULE),
            "type": "str",
            "length_bound": model,
        },
        "B_orm": {
            "orm": "NONE",
            "note": "persistence is SQL through psycopg on the write paths below",
        },
        "C_database_column": {**column, "type": "TEXT", "declared_length": None},
        "D_database_checks": {"migrations_checking_the_column": 0, "observed": OBSERVED_DATABASE},
        "E_serialization": writes,
        "F_api_and_domain": {
            "generated_contracts_carrying_the_summary": 0,
            "gateway_modules_carrying_the_summary": 0,
        },
        "G_prose_guard": {"source": _rel(GUARDS_MODULE), "length_sized_numbers": []},
        "H_literal_900_and_720": [
            {"path": path, "line": line, "what": why} for path, line, why in EXPECTED_LITERALS
        ],
        "H_hidden_coupling": BLOCKER,
        "PERSISTENCE_MAXIMUM_FOR_REASONING_SUMMARY": "NONE_BELOW_THE_POSTGRESQL_TEXT_LIMIT",
        "source": "the model field, both write paths, stage 9, migration 0029 and the observed catalog",
        "PERSISTENCE_COMPATIBILITY": "COMPATIBLE",
        "DATABASE_STORAGE_COMPATIBILITY": "COMPATIBLE",
        "PERSISTENCE_MODEL_CHANGED": False,
    }


# --------------------------------------------------------------------------- the gate and its coupling


def _coupling_line() -> int:
    tree = ast.parse(GATE_MODULE.read_text(encoding="utf-8"))
    func = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "evaluate_second_opportunity_output_v1_3"
    )
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == "schema_violations"
            and len(node.args) == 2
            and getattr(node.args[1], "id", None) == "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1"
        ):
            return int(node.lineno)
    raise ValidationError("gate v1.3.0 no longer validates against schema v1.1.0 inside the gate")


def gate_block(fixtures: Any, new: dict[str, Any]) -> dict[str, object]:
    implementation = _module("gate_77_for_gate_86", GATE_77).implementation_sha256()
    if implementation != GATE_IMPLEMENTATION_SHA256:
        raise ValidationError("gate v1.3.0 changed, and this mission may not change it")
    gate77 = _module("gate_77_pins_for_gate_86", GATE_77)
    good = fixtures.good_output()
    base = str(good[REASONING_SUMMARY_FIELD])
    longer = fixtures.good_output(**{REASONING_SUMMARY_FIELD: " ".join([base] * REPETITIONS)})
    length = len(str(longer[REASONING_SUMMARY_FIELD]))
    control = list(fixtures.gate(good).refusal_reasons)
    refused = list(fixtures.gate(longer).refusal_reasons)
    expected = [
        f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1}: {REASONING_SUMMARY_FIELD}: {length} "
        "characters exceeds maxLength 900"
    ]
    if control or schema_violations(longer, new) or refused != expected:
        raise ValidationError(
            f"the coupling is no longer what this record says: control {control}, "
            f"v1.2.0 {schema_violations(longer, new)}, gate {refused}"
        )
    return {
        "identity": SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
        "implementation_sha256": implementation,
        "SEMANTIC_GATE_CHANGED": False,
        "coupling": {
            "code": BLOCKER,
            "brief_section": 10,
            "evaluator": "evaluate_second_opportunity_output_v1_3",
            "module": _rel(GATE_MODULE),
            "structural_check_line": _coupling_line(),
            "structural_check": "schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)",
            "component_output_schema": COMPONENT_VERSIONS_V1_3["output_schema"],
            "operator_decision_keeps_v1_1_0": "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED"
            in OPERATOR_DECISION_V1_3,
            "gate_77_pins_output_schema_sha256": gate77.OUTPUT_SCHEMA_SHA256,
            "requires_a_successor_identity": True,
            "semantic_behaviour_would_change": False,
            "note": (
                "gate v1.3.0 validates the answer's structure against schema v1.1.0 inside its own "
                "evaluator, so the 900 is enforced again at stage 6 whatever stage 5 admits. Admitting "
                "a longer summary through stage 6 needs a gate with another identity; v1.3.0 is not "
                "mutated in place"
            ),
        },
        "demonstration": {
            "answer": "the synthetic fixture's valid answer; no historical answer is used",
            "control_refusal_reasons": control,
            "summary": f"the fixture's own summary repeated {REPETITIONS} times, so no word is new",
            "summary_characters": length,
            "schema_v1_2_0_violations": [],
            "gate_v1_3_0_refusal_reasons": refused,
        },
    }


# --------------------------------------------------------------------------- the record


def _later(value: object) -> bool:
    """Whether a mission label names a mission after this one."""
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", str(value or ""))
    return match is not None and tuple(int(part) for part in match.groups()) > THIS_MISSION


def _successor_prepared(present: list[pathlib.Path]) -> bool:
    """Whether a later mission took the decision section 10 asked for, and authored what exists.

    A successor gate bound to schema v1.2.0 must be frozen by its own record naming another mission,
    and every V6 artifact present must name a later mission as its author: a record through
    `recorded_by`, `prepared_by` or `mission`, a module through its docstring. Anything short of that
    is the state section 10 stopped, and is refused as before.
    """
    if not SUCCESSOR_FREEZE.exists():
        return False
    freeze = _load(SUCCESSOR_FREEZE)
    if not (
        _later(freeze.get("mission"))
        and freeze.get("GATE_V1_4_FROZEN") is True
        and freeze.get("PREDECESSOR_GATE_VERSION") == SECOND_OPPORTUNITY_GATE_VERSION_V1_3
        and (freeze.get("OUTPUT_SCHEMA") or {}).get("sha256") == SCHEMA_V1_2_SHA256
    ):
        return False
    for path in present:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            try:
                record = json.loads(text)
            except ValueError:
                return False
            authors = (
                [record.get(k) for k in ("recorded_by", "prepared_by", "mission")]
                if isinstance(record, dict)
                else []
            )
        else:
            authors = re.findall(r"Mission (\d+\.\d+\.\d+)", text[:600])
        if not any(_later(author) for author in authors):
            return False
    return True


def not_prepared_block() -> dict[str, object]:
    present = [path for path in NOT_PREPARED if path.exists()]
    if present and not _successor_prepared(present):
        raise ValidationError(
            f"section 10 stopped V6, and these exist: {[path.name for path in present]}"
        )
    return {
        "stopped_at": "section 10, the semantic-gate audit",
        "sections_not_executed": [
            "13 to 15 prompt v1.5.0",
            "17 exact maximum serialized size under v1.2.0",
            "18 execution envelope restated",
            "21 and 22 stages 6 to 9 through a V6 runner",
            "28 cost recomputation",
            "29 to 32 execution packet V6 and its runner",
        ],
        "files_that_must_not_exist": list(NOT_PREPARED_REL),
        "V6_CREATED": False,
        "EXECUTION_PACKET_V6_SHA256": None,
        "OPERATOR_EXECUTION_APPROVAL_RECORDED": False,
        "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6": False,
    }


def build(
    old: dict[str, Any] | None = None, new: dict[str, Any] | None = None
) -> dict[str, object]:
    old = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1 if old is None else old
    new = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2 if new is None else new
    fixtures = _module("fixtures_for_gate_86", FIXTURES)
    return {
        "$comment": (
            "Mission 1.84.16. Rebuilt by CI gate 86 from the live code and the committed artifacts; "
            "the file must equal the rebuild. Nothing here was sent anywhere."
        ),
        "record_version": "second-opportunity-reasoning-summary-contract@1.0.0",
        "mission": "1.84.16",
        "recorded_by": MISSION,
        "START_COMMIT": START_COMMIT,
        "BRANCH": BRANCH,
        "PRIMARY_OUTCOME": PRIMARY_OUTCOME,
        "BLOCKER": BLOCKER,
        "outcome_note": (
            "Section 10 stops the mission: gate v1.3.0 re-validates every answer against schema "
            "v1.1.0, so a summary the operator's new bound admits is refused at stage 6. The stage 6 "
            "to 9 path is therefore not ready under schema v1.2.0, and no V6 was prepared"
        ),
        "DECISION": decision_block(),
        "V5": v5_block(),
        "SCHEMA": schema_block(old, new),
        "FINITE": finite_block(old, new),
        "HEADROOM": headroom_block(old, new),
        "BOUNDARIES": boundary_block(fixtures, new),
        "PERSISTENCE": persistence_block(),
        "SEMANTIC_GATE": gate_block(fixtures, new),
        "NOT_PREPARED": not_prepared_block(),
        "OPTIONS": [
            {
                "option": "A gate successor whose only change is the schema it validates against",
                "what_it_takes": (
                    "a new gate identity bound to schema v1.2.0, frozen with its own implementation "
                    "digest, and shown to judge every case of v1.3.0's test matrix exactly as v1.3.0 "
                    "does; then prompt v1.5.0 and packet V6 as the brief describes"
                ),
            },
            {
                "option": "Keep schema v1.1.0 as the execution contract",
                "what_it_takes": (
                    "nothing changes; the 900 stays, and schema v1.2.0 stays recorded and unused"
                ),
            },
        ],
        "RECOMMENDATION": "NONE",
        "CANONICAL_COUNTERS_BEFORE": CANONICAL_COUNTERS,
        "CANONICAL_COUNTERS_AFTER": CANONICAL_COUNTERS,
        "ACCOUNTING": ACCOUNTING,
    }


def validate() -> dict[str, object]:
    record = build()
    if not RECORD.exists() or _load(RECORD) != json.loads(json.dumps(record)):
        raise ValidationError(f"{RECORD.name} is not the rebuild of the live code and artifacts")
    return record


# --------------------------------------------------------------------------- rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_reasoning_summary_contract.py "
    "from {source}. Do not edit by hand; re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def render(record: dict[str, Any]) -> str:
    decision = record["DECISION"]
    v5 = record["V5"]
    schema = record["SCHEMA"]
    headroom = record["HEADROOM"]
    persistence = record["PERSISTENCE"]
    gate = record["SEMANTIC_GATE"]
    coupling = gate["coupling"]
    demo = gate["demonstration"]
    out = [
        HEADER.format(source=RECORD.name),
        "# Second opportunity: reasoning-summary contract v1.2",
        "",
        f"Recorded by {record['recorded_by']}. **{record['PRIMARY_OUTCOME']}**, blocker "
        f"`{record['BLOCKER']}`.",
        "",
        record["outcome_note"] + ".",
        "",
        "## The operator's decision",
        "",
        *_code(
            [
                f"field                  {decision['field']}.{decision['keyword']}",
                f"hard maximum           {decision['old_hard_maximum']} -> {decision['new_hard_maximum']}",
                f"basis                  {decision['DECISION_BASIS']}",
                f"mathematically derived {str(decision['MATHEMATICALLY_DERIVED']).lower()}",
                f"from historical length {str(decision['HISTORICAL_OUTPUT_LENGTH_DERIVED']).lower()}",
                f"statement              {decision['operator_statement_lines']} lines, "
                f"{decision['operator_statement_sha256']}",
            ]
        ),
        "V3's 868, V4's 1078 and V5's 1031 are recorded as observations only; they derived nothing.",
        "",
        "## V5, as it was",
        "",
        f"`{v5['PRIMARY_OUTCOME']}`: one request, `{v5['stop_reason']}`, "
        f"{v5['input_tokens']} / {v5['output_tokens']} / {v5['thinking_tokens']} tokens, cost "
        f"{v5['cost_units']}; approval consumed, nothing persisted. Replayed under schema v1.1.0:",
        "",
        *[f"- `{v}`" for v in v5["violations_replayed_under_v1_1_0"]],
        "",
        v5["note"] + ".",
        "",
        "## Schema v1.2.0",
        "",
        *_code(
            [
                f"old  {schema['old_identity']}  {schema['old_sha256']}",
                f"new  {schema['new_identity']}  {schema['new_sha256']}",
                *[f"diff {d['path']}: {d['old']} -> {d['new']}" for d in schema["SEMANTIC_DIFF"]],
                f"fields added / removed      {schema['SCHEMA_FIELDS_ADDED']} / {schema['SCHEMA_FIELDS_REMOVED']}",
                f"other maxLength changed     {schema['ALL_OTHER_MAX_LENGTHS_CHANGED']}",
                f"constraints                 {schema['CONSTRAINTS']}, changed: "
                + ", ".join(schema["CONSTRAINTS_CHANGED"]),
                f"finite                      {str(record['FINITE']['FINITE_BOUND']).lower()}, "
                f"unbounded paths {record['FINITE']['UNBOUNDED_REACHABLE_PATHS']}",
            ]
        ),
        "## Generation headroom",
        "",
        f"`{headroom['GENERATION_HEADROOM_POLICY']}`, ratio {headroom['GENERATION_TARGET_RATIO']}, "
        f"arrays `{headroom['ARRAY_HEADROOM_POLICY']}`. Of {headroom['rows_v1_2_0']} rows one moves: "
        f"the summary, hard {headroom['summary_v1_1_0']['hard_maximum']} -> "
        f"{headroom['summary_v1_2_0']['hard_maximum']}, target {headroom['summary_v1_1_0']['target']} "
        f"-> {headroom['summary_v1_2_0']['target']}, derived from {headroom['target_source']}.",
        "",
        "| summary characters | schema v1.2.0 | above the target |",
        "|---|---|---|",
        *[
            f"| {row['characters']} | {row['schema_v1_2_0']} | {'yes' if row['above_generation_target'] else 'no'} |"
            for row in record["BOUNDARIES"]["rows"]
        ],
        "",
        "## Persistence",
        "",
        f"**{persistence['PERSISTENCE_COMPATIBILITY']}**: maximum "
        f"`{persistence['PERSISTENCE_MAXIMUM_FOR_REASONING_SUMMARY']}`.",
        "",
        f"- model: `{persistence['A_model']['object']}` is `{persistence['A_model']['type']}`, with no "
        "length bound;",
        "- ORM: none; the write paths are SQL through psycopg and pass the summary as it is;",
        f"- database: `{persistence['C_database_column']['definition']}` in "
        f"{persistence['C_database_column']['migration']}, no later migration, no CHECK; observed "
        f"`{persistence['D_database_checks']['observed']['data_type']}` with type modifier "
        f"{persistence['D_database_checks']['observed']['atttypmod']}, longest stored value "
        f"{persistence['D_database_checks']['observed']['existing_longest_value_characters']} characters;",
        "- contracts and gateway: the summary appears in neither;",
        "- every literal 900 or 720 on these paths:",
        *[
            f"  - `{row['path']}:{row['line']}`: {row['what']}"
            for row in persistence["H_literal_900_and_720"]
        ],
        "",
        "## The coupling that stopped V6",
        "",
        f"`{gate['identity']}` is unchanged (`{gate['implementation_sha256']}`). Its evaluator, in "
        f"`{coupling['module']}` line {coupling['structural_check_line']}, runs "
        f"`{coupling['structural_check']}`; its component versions name "
        f"`{coupling['component_output_schema']}`, and gate 77 pins that schema's digest.",
        "",
        coupling["note"] + ".",
        "",
        f"Shown on the synthetic answer: the fixture passes the gate with no reason; with its summary "
        f"repeated to {demo['summary_characters']} characters, schema v1.2.0 admits it and the gate "
        "refuses it with exactly:",
        "",
        *[f"- `{reason}`" for reason in demo["gate_v1_3_0_refusal_reasons"]],
        "",
        "## Not prepared",
        "",
        "V6 was not created, no approval is recorded, and the residual semantic limitation is not "
        "accepted for V6. Not executed: "
        + "; ".join(record["NOT_PREPARED"]["sections_not_executed"])
        + ".",
        "",
        "## Options, with none recommended",
        "",
        *[f"- **{o['option']}**: {o['what_it_takes']}." for o in record["OPTIONS"]],
        "",
        "Accounting: " + ", ".join(f"{k} {v}" for k, v in record["ACCOUNTING"].items()) + ".",
        "",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            record = build()
            RECORD.write_bytes(
                (json.dumps(record, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            )
            RECORD_MD.write_bytes(render(record).encode("utf-8"))
            print(f"wrote    {RECORD.name}, {RECORD_MD.name}")
            return 0
        record = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    if not RECORD_MD.exists() or RECORD_MD.read_text(encoding="utf-8") != render(record):
        print(f"FAIL     {RECORD_MD.name} is not the rendering of its record")
        return 1
    print(
        "ok       the reasoning-summary contract record matches the decision, the code and the gate"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
