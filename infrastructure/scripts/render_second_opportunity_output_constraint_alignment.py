"""Mission 1.84.8, CI gate 72. The prompt states what the schema enforces, derived and not copied.

Two records, checked against the live schema, the live renderer, the frozen v1.1.0 prompt and the
execution V2 retained:

* the output-constraint ALIGNMENT record: the operator's decision, the V2 facts it rests on, every
  constraint of `second-opportunity-synthesis-output@1.1.0` classified, which ones prompt v1.1.0
  stated in words and which it left to the tool schema, and the drift property;
* the prompt v1.2.0 DOCUMENT: the system region the derived block produces, its digests, and the
  semantic diff from v1.1.0.

**What is re-derived rather than read.** The inventory and every class, from the live schema through
the live renderer. Which constraints v1.1.0 made explicit, from the frozen v1.1.0 text by the same
rule that decides v1.2.0. The drift property, by mutating a copy of the schema one constraint at a
time: a generation-relevant mutation must move the rendered prompt and any other must not. The V2
schema violation, by the live validator over the answer V2 retained. The system region, by
composing the live blocks, and its digest.

**What CI cannot re-derive.** The full prompt digest also covers the untrusted region, which is
rebuilt from the research database. The document records what the preparing machine found, and the
V3 runner recomputes it before any socket.
"""

from __future__ import annotations

import argparse
import ast
import copy
import difflib
import hashlib
import json
import pathlib
import re
from collections.abc import Iterator
from typing import Any

from sros_llm_gateway.pricing import ModelPrice
from sros_opportunity.output_constraints import (
    CLASSIFICATION_POLICY,
    CONSTRAINT_CLASS_LETTERS,
    MUST_BE_EXPLICIT_IN_PROMPT,
    OUTPUT_CONSTRAINT_RENDERER_VERSION,
    constraint_inventory,
    is_explicit,
    mutated_schema,
    render_output_constraints,
)
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity import (
    BOUNDED_OUTPUT_CONTRACT_RULES,
    OUTPUT_CONSTRAINT_NOTES_V1_2,
    OUTPUT_CONTRACT_CLOSING,
    OUTPUT_CONTRACT_OPENING,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_CONTRACT_BLOCK_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROCEDURE_VERSION,
    SECOND_OPPORTUNITY_PROMPT_ID,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
    SECOND_OPPORTUNITY_SYSTEM,
    SECOND_OPPORTUNITY_SYSTEM_V1_1,
    SECOND_OPPORTUNITY_SYSTEM_V1_2,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
PACKAGE = ROOT / "packages" / "opportunity-engine" / "python" / "sros_opportunity"

ALIGNMENT = DATA / "second-opportunity-output-constraint-alignment-v1.json"
ALIGNMENT_MD = DATA / "second-opportunity-output-constraint-alignment-v1.md"
PROMPT = DATA / "second-opportunity-synthesis-prompt-v3.json"
PROMPT_MD = DATA / "second-opportunity-synthesis-prompt-v3.md"
PROMPT_V2 = DATA / "second-opportunity-synthesis-prompt-v2.json"
PACKET_V2 = DATA / "second-opportunity-synthesis-execution-packet-v2.json"
RECORD_V2 = DATA / "second-opportunity-synthesis-execution-record-v2.json"
RESPONSE_V2 = DATA / "second-opportunity-synthesis-response-v2.json"
RENDERER_SOURCE = PACKAGE / "output_constraints.py"
CONTRACT_SOURCE = PACKAGE / "second_opportunity.py"

THIS_MISSION = "mission-1.84.8"
V2_SHA256 = "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e"
V2_OUTCOME = "EXECUTION_SCHEMA_REJECTED_NO_RETRY"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
FAILED_FIELD = "evidence_bound_reasoning_summary"

#: What Missions 1.84 to 1.84.7 left, byte for byte. Section 2 forbids rewriting any of it, and a
#: rewritten history is where a rejected answer would be promoted without anybody deciding it: marked
#: a candidate, given a human-review packet, or its violation restated against a raised bound.
HISTORY_SHA256 = {
    "second-opportunity-synthesis-prompt-v1.json": (
        "acd3c046b05eb3619d70dc0ca124c288fc988fc46933cffbf65f20cf67ae9a81"
    ),
    "second-opportunity-synthesis-execution-packet-v1.json": (
        "7132fc35ab263b86bbe89016f84fd10e9ed54bcc7fb8b30d072e86279b472241"
    ),
    "second-opportunity-synthesis-execution-record-v1.json": (
        "b769ddeb6ea4d4e773640c3ed83caeff52c52c857fd9125325140de4ab38c799"
    ),
    "second-opportunity-synthesis-prompt-v2.json": (
        "cf8edd4801ce8b3af6296d0490bab1a862870bd749f260be5105e6b88beb5086"
    ),
    "second-opportunity-synthesis-execution-packet-v2.json": (
        "5a2f5a7ea20c6de9d4f50498f304e59b6918db63e5ccc9814f988fd3d4f14871"
    ),
    "second-opportunity-synthesis-execution-approval-v2.json": (
        "1885358d0b7fde8e95a587f124cf9b85d41b1471ee0aeb4a21cd0a5e2712555c"
    ),
    "second-opportunity-synthesis-execution-record-v2.json": (
        "3fb8d5bae0cb2c64e165961518d9dfd3b1de98eef5244600ea0e5efc289001a7"
    ),
    "second-opportunity-synthesis-response-v2.json": (
        "8f98939afa049ab3089c41304bdc7b4f0ee86788d54425f764fc1375964dbb11"
    ),
}

DECISIONS = (
    "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED",
    "KEEP_OUTPUT_GATE_V1_1_0_UNCHANGED",
    "DO_NOT_RAISE_EVIDENCE_BOUND_REASONING_SUMMARY_MAX_LENGTH",
    "CORRECT_PROMPT_SCHEMA_CONSTRAINT_ALIGNMENT",
)
#: Lines the operator's recorded words must contain. The whole statement is hashed; these are the
#: sentences a recording that lost them would have lost the decision with.
STATEMENT_LINES_REQUIRED = (
    *DECISIONS,
    "The rejected V2 answer MUST NOT be rescued.",
    "Mission 1.84.8 must remove that drift in a GENERAL way.",
    "ZERO external model calls.",
)
NOT_USED_TO_CHOOSE = (
    "a new maxLength",
    "a new maxItems",
    "a new field order",
    "a new requiredness rule",
    "a new semantic allowance",
    "a new Evidence interpretation",
)
#: The one thing V2's answer may be used for, word for word. A list that can be extended is a list a
#: later reading uses to launder a choice through: "used to establish a maximum of 1200" is exactly
#: the sentence the operator forbade, and it would sit beside the refusals without contradicting them.
USED_TO_ESTABLISH = (
    "that a schema violation occurred, on one field, against a bound the v1.1.0 prompt did not "
    "state in words",
)
V2_OUTPUT_USE_KEYS = {"USED_TO_ESTABLISH", "NOT_USED_TO_CHOOSE", "note"}
POST_PROCESSING = (
    "TRUNCATION",
    "ITEM_DROPPING",
    "REWRITING",
    "AUTO_SUMMARY",
    "STATEMENT_SPLITTING",
    "SEMANTIC_NORMALISATION",
)
ACCOUNTING_ZERO = (
    "MODEL_CALLS",
    "PROVIDER_REQUESTS",
    "MESSAGES_API_REQUESTS",
    "TOKEN_COUNT_API_REQUESTS",
    "TED_BYTES_SENT",
    "CANONICAL_MUTATIONS",
    "DOCUMENTATION_FETCHES",
)
SEMANTIC_FLAGS = (
    "research_semantics_changed",
    "evidence_semantics_changed",
    "refusal_semantics_changed",
    "commercial_claim_restrictions_changed",
    "confidence_semantics_changed",
    "human_review_requirement_changed",
)
BOUND_KEYWORDS = ("minLength", "maxLength", "minItems", "maxItems")
#: A record that proposed a replacement bound would be designing the contract from V2's answer.
FORBIDDEN_KEY_FRAGMENTS = ("PROPOSED", "NEW_MAX", "RECOMMENDED_MAX", "CANDIDATE_MAX", "RAISED_MAX")
RENDERER_IMPORTS = frozenset(
    {"__future__", "re", "collections.abc", "copy", "dataclasses", "typing", ".schema_validation"}
)
RENDERER_FORBIDDEN_CALLS = frozenset({"open", "eval", "exec", "compile", "__import__", "input"})


class ValidationError(RuntimeError):
    """The records disagree with the live schema, the renderer, the frozen prompt or V2."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _file_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schema_sha(schema: object) -> str:
    return _sha(json.dumps(schema, sort_keys=True))


def statement_digest(block: dict[str, Any]) -> str:
    return _sha("\n".join(str(line) for line in block["OPERATOR_STATEMENT"]))


def _keys(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, sub in value.items():
            yield str(key)
            yield from _keys(sub)
    elif isinstance(value, list):
        for sub in value:
            yield from _keys(sub)


def _normalise(text: str) -> str:
    return " ".join(text.split())


def _fixed(block: dict[str, Any], expected: dict[str, object], where: str) -> None:
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


# ------------------------------------------------------------------------------ derivations


def frozen_v1_1_text() -> str:
    """The system region v1.1.0 sent, from the document that froze it, checked against the code."""
    prompt = _load(PROMPT_V2)
    text = str(prompt["SYSTEM_INSTRUCTION"])
    if _sha(text) != prompt["SYSTEM_SHA256"]:
        raise ValidationError("the frozen v1.1.0 system region no longer hashes to its digest")
    if text != SECOND_OPPORTUNITY_SYSTEM_V1_1:
        raise ValidationError(
            "the live v1.1.0 system region is not the one Mission 1.84.4 froze and Mission 1.84.7 "
            "sent. A historical prompt is never edited"
        )
    return text


def expected_inventory() -> list[dict[str, Any]]:
    """Every constraint, classified, with whether each prompt states it, by one rule for both."""
    before = frozen_v1_1_text()
    after = SECOND_OPPORTUNITY_SYSTEM_V1_2
    rows: list[dict[str, Any]] = []
    for constraint in constraint_inventory(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1):
        row = constraint.to_json()
        generation = constraint.constraint_class == MUST_BE_EXPLICIT_IN_PROMPT
        row["explicit_in_v1_1_0"] = is_explicit(constraint, before) if generation else None
        row["explicit_in_v1_2_0"] = is_explicit(constraint, after) if generation else None
        rows.append(row)
    return rows


def _label(row: dict[str, Any]) -> str:
    return f"{row['path']} {row['keyword']}"


def missing_lists(rows: list[dict[str, Any]]) -> dict[str, Any]:
    generation = [r for r in rows if r["class"] == MUST_BE_EXPLICIT_IN_PROMPT]
    failed = f"{FAILED_FIELD} maxLength"
    missing = [r for r in generation if not r["explicit_in_v1_1_0"]]
    other_bounds = [
        f"{r['path']} {r['keyword']} {r['value']}"
        for r in missing
        if r["keyword"] in BOUND_KEYWORDS and _label(r) != failed
    ]
    return {
        "EXPLICIT_IN_V1_1_0": [_label(r) for r in generation if r["explicit_in_v1_1_0"]],
        "MISSING_FROM_V1_1_0": [_label(r) for r in missing],
        "FAILED_FIELD_BOUND_MISSING_FROM_V1_1_0": failed in {_label(r) for r in missing},
        "WERE_OTHER_SCHEMA_BOUNDS_MISSING_FROM_PROMPT": bool(other_bounds),
        "OTHER_SCHEMA_BOUNDS_MISSING_FROM_V1_1_0": other_bounds,
        "OTHER_GENERATION_CONSTRAINTS_MISSING_FROM_V1_1_0": [
            _label(r) for r in missing if r["keyword"] not in BOUND_KEYWORDS
        ],
        "UNSTATED_IN_V1_2_0": [_label(r) for r in generation if not r["explicit_in_v1_2_0"]],
    }


def class_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        letter: sum(1 for r in rows if r["class"] == name)
        for letter, name in CONSTRAINT_CLASS_LETTERS.items()
    }


def _node(schema: dict[str, Any], path: str) -> dict[str, Any]:
    node = schema
    for segment in path.split("."):
        node = node["properties"][segment.removesuffix("[]")]
        if segment.endswith("[]"):
            node = node["items"]
    return node


def _reword_descriptions(node: dict[str, Any]) -> int:
    changed = 0
    description = node.get("description")
    if isinstance(description, str) and "the exact string" not in description:
        node["description"] = description + " Reworded for a test."
        changed += 1
    for sub in (node.get("properties") or {}).values():
        changed += _reword_descriptions(sub)
    if isinstance(node.get("items"), dict):
        changed += _reword_descriptions(node["items"])
    return changed


def drift_property() -> dict[str, int]:
    """Mutate a copy of the schema one constraint at a time and watch the rendered prompt.

    A generation-relevant constraint that moves must move the prompt; a constraint of any other
    class that moves and stays in its class must leave the prompt alone, because noise the model
    reads is not free. A vocabulary bound pushed below its vocabulary becomes binding and must then
    appear. Reworded descriptions, which are metadata, must change nothing.
    """
    schema = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
    notes = OUTPUT_CONSTRAINT_NOTES_V1_2
    base = render_output_constraints(schema, notes)
    counts = dict.fromkeys(
        (
            "A_MUTATIONS",
            "A_MUTATIONS_MOVING_THE_PROMPT",
            "OTHER_CLASS_MUTATIONS",
            "OTHER_CLASS_MUTATIONS_LEAVING_THE_PROMPT",
            "TYPE_CONSTRAINTS_NOT_MUTATED",
            "VOCABULARY_BOUNDS_MADE_BINDING",
            "VOCABULARY_BOUNDS_MADE_BINDING_MOVING_THE_PROMPT",
            "DESCRIPTIONS_REWORDED",
        ),
        0,
    )
    for constraint in constraint_inventory(schema):
        mutated = mutated_schema(schema, constraint)
        if mutated is None:
            counts["TYPE_CONSTRAINTS_NOT_MUTATED"] += 1
            continue
        moved = render_output_constraints(mutated, notes) != base
        if constraint.constraint_class == MUST_BE_EXPLICIT_IN_PROMPT:
            counts["A_MUTATIONS"] += 1
            if not moved:
                raise ValidationError(
                    f"{constraint.path} {constraint.keyword} changed and the rendered prompt did "
                    "not: a schema bound can move under an unchanged prompt"
                )
            counts["A_MUTATIONS_MOVING_THE_PROMPT"] += 1
        else:
            counts["OTHER_CLASS_MUTATIONS"] += 1
            if moved:
                raise ValidationError(
                    f"{constraint.path} {constraint.keyword} is {constraint.constraint_class}, and "
                    "moving it moved the prompt: drift the model would read as a new instruction"
                )
            counts["OTHER_CLASS_MUTATIONS_LEAVING_THE_PROMPT"] += 1
        if constraint.rule == "vocabulary_cardinality":
            binding = copy.deepcopy(schema)
            node = _node(binding, constraint.path)
            node["maxItems"] = len(node["items"]["enum"]) - 1
            counts["VOCABULARY_BOUNDS_MADE_BINDING"] += 1
            if render_output_constraints(binding, notes) == base:
                raise ValidationError(
                    f"{constraint.path} maxItems was made binding and the prompt does not say so"
                )
            counts["VOCABULARY_BOUNDS_MADE_BINDING_MOVING_THE_PROMPT"] += 1
    reworded = copy.deepcopy(schema)
    counts["DESCRIPTIONS_REWORDED"] = _reword_descriptions(reworded)
    if render_output_constraints(reworded, notes) != base:
        raise ValidationError("rewording a description moved the prompt; a description is metadata")
    return counts


def semantic_diff(before: str, after: str) -> dict[str, Any]:
    """The line diff from v1.1.0 to v1.2.0, and what it does and does not touch."""
    old, new = before.splitlines(), after.splitlines()
    removed: list[str] = []
    added: list[str] = []
    first: int | None = None
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        first = i1 if first is None else min(first, i1)
        removed.extend(old[i1:i2])
        added.extend(new[j1:j2])
    prefix = len(SECOND_OPPORTUNITY_SYSTEM.splitlines())
    rows = expected_inventory()
    still_explicit = all(
        r["explicit_in_v1_2_0"]
        for r in rows
        if r["class"] == MUST_BE_EXPLICIT_IN_PROMPT and r["explicit_in_v1_1_0"]
    )
    notes_kept = all(
        _normalise(note) in _normalise(before) and note in after
        for note in OUTPUT_CONSTRAINT_NOTES_V1_2.values()
    )
    framing = all(
        phrase in before and phrase in after
        for phrase in (OUTPUT_CONTRACT_OPENING, OUTPUT_CONTRACT_CLOSING)
    )
    confined = (
        first is not None
        and first > prefix
        and before.startswith(SECOND_OPPORTUNITY_SYSTEM)
        and after.startswith(SECOND_OPPORTUNITY_SYSTEM)
    )
    unchanged = still_explicit and notes_kept and framing and confined
    return {
        "REMOVED_LINES": removed,
        "ADDED_LINES": added,
        "UNCHANGED_V1_0_0_PREFIX_LINES": prefix,
        "FIRST_CHANGED_LINE": (first or 0) + 1,
        "CHANGE_CONFINED_TO_THE_OUTPUT_CONTRACT_BLOCK": confined,
        "EXPLICIT_IN_V1_1_0_STILL_EXPLICIT": still_explicit,
        "GUIDANCE_NOTES_PRESERVED": notes_kept,
        "FRAMING_PRESERVED": framing,
        **{flag: not unchanged for flag in SEMANTIC_FLAGS},
    }


def v2_facts() -> dict[str, Any]:
    """The V2 facts the operator's decision rests on, recomputed from what V2 retained."""
    record = _load(RECORD_V2)
    response = _load(RESPONSE_V2)
    packet = _load(PACKET_V2)
    body = response["RAW_PROVIDER_RESPONSE_BODY"]
    usage = body["usage"]
    details = usage.get("output_tokens_details") or {}
    price = packet["PRICE_PER_1K"]
    cost = ModelPrice(
        input_per_1k=float(price["input"]), output_per_1k=float(price["output"])
    ).cost_for(int(usage["input_tokens"]), int(usage["output_tokens"]))
    violations = schema_violations(response["parsed_output"], SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    stages = record["VALIDATION_STAGES"]
    discrepancies = []
    if body.get("stop_reason") != record["STOP_REASON"]:
        discrepancies.append("stop_reason")
    if round(cost, 6) != record["ACTUAL_COST"]["cost_units"]:
        discrepancies.append("cost")
    if violations != record["SCHEMA_VIOLATIONS"]:
        discrepancies.append("schema_violations")
    if int(details.get("thinking_tokens", 0)) != record["THINKING_TOKENS_REPORTED"]:
        discrepancies.append("thinking_tokens")
    return {
        "EXECUTION_PACKET_SHA256": record["execution_packet_sha256"],
        "OUTCOME": record["PRIMARY_OUTCOME"],
        "PROVIDER_REQUESTS": record["actual_provider_requests"],
        "MODEL_CALLS": record["actual_model_calls"],
        "RETRIES": record["retries"],
        "FALLBACKS": record["fallbacks"],
        "STOP_REASON": body.get("stop_reason"),
        "INPUT_TOKENS": usage["input_tokens"],
        "OUTPUT_TOKENS": usage["output_tokens"],
        "THINKING_TOKENS": int(details.get("thinking_tokens", 0)),
        "ACTUAL_COST": round(cost, 6),
        "FAILED_STAGE": record["FAILED_STAGE"],
        "SCHEMA_VIOLATIONS": violations,
        "STAGES_NOT_REACHED": [name for name, state in stages.items() if state == "NOT_REACHED"],
        "CANONICAL_PERSISTENCE": record["CANONICAL_PERSISTENCE"],
        "APPROVAL_CONSUMED": record["EXECUTION_APPROVAL_CONSUMED"],
        "DISCREPANCIES": discrepancies,
    }


# ------------------------------------------------------------------------------ checks


def _check_operator_decision(doc: dict[str, Any]) -> None:
    _fixed(doc, {"mission": "1.84.8", "recorded_by": THIS_MISSION}, "alignment")
    block = doc["OPERATOR_DECISION"]
    _fixed(
        block,
        {
            "DECISIONS": list(DECISIONS),
            "DECISION_OWNER": "OPERATOR",
            "V2_ANSWER_RESCUED": False,
            "V2_VALUE_USED_TO_CHOOSE_A_MAXIMUM": False,
            "AUTHORISES_A_SCHEMA_CHANGE": False,
            "AUTHORISES_AN_INFERENCE": False,
        },
        "OPERATOR_DECISION",
    )
    statement = block["OPERATOR_STATEMENT"]
    if not statement or not all(isinstance(line, str) and line.strip() for line in statement):
        raise ValidationError("the operator's statement is empty or has an empty line")
    missing = [line for line in STATEMENT_LINES_REQUIRED if line not in statement]
    if missing:
        raise ValidationError(f"the recorded statement lost the operator's words: {missing}")
    if block["OPERATOR_STATEMENT_SHA256"] != statement_digest(block):
        raise ValidationError("the operator's words changed after their digest was recorded")


def _check_v2(doc: dict[str, Any], prompt: dict[str, Any]) -> None:
    facts = v2_facts()
    recorded = doc["V2_FACTS"]
    moved = sorted(k for k in set(facts) | set(recorded) if facts.get(k) != recorded.get(k))
    if moved:
        raise ValidationError(f"the recorded V2 facts differ from what V2 retained: {moved}")
    record, response = _load(RECORD_V2), _load(RESPONSE_V2)
    if (
        record["HUMAN_REVIEW_PACKET"] != "NOT_PRODUCED"
        or record["OPPORTUNITY_PERSISTED"] is not False
        or response["PERSISTED"] != "NOTHING"
    ):
        raise ValidationError(
            "V2's rejected answer is recorded as something other than refused evidence: a "
            "human-review packet, a persisted Opportunity or a candidate. An answer the schema "
            "refused is never a candidate"
        )
    if facts["DISCREPANCIES"]:
        raise ValidationError(
            f"V2's record and its retained response disagree on {facts['DISCREPANCIES']}. A factual "
            "discrepancy is reported, never corrected on the way past"
        )
    _fixed(
        facts,
        {
            "EXECUTION_PACKET_SHA256": V2_SHA256,
            "OUTCOME": V2_OUTCOME,
            "PROVIDER_REQUESTS": 1,
            "MODEL_CALLS": 1,
            "RETRIES": 0,
            "FALLBACKS": 0,
            "STOP_REASON": "tool_use",
            "THINKING_TOKENS": 0,
            "FAILED_STAGE": "5_schema_validation_v1_1_0",
            "CANONICAL_PERSISTENCE": False,
            "APPROVAL_CONSUMED": True,
        },
        "V2_FACTS",
    )
    violations = facts["SCHEMA_VIOLATIONS"]
    if len(violations) != 1 or not str(violations[0]).startswith(f"{FAILED_FIELD}: "):
        raise ValidationError(f"V2 was refused on {violations}, not on one reasoning-summary bound")
    if facts["STAGES_NOT_REACHED"] != [
        "6_semantic_output_gate_v1_1_0",
        "7_evidence_boundary_and_no_distortion",
        "8_attribution_and_provenance",
        "9_persistence_eligibility",
        "10_human_review",
    ]:
        raise ValidationError("stages 6 to 10 are not all recorded NOT_REACHED")

    use = doc["V2_OUTPUT_USE"]
    if tuple(use["NOT_USED_TO_CHOOSE"]) != NOT_USED_TO_CHOOSE:
        raise ValidationError(
            "the record no longer refuses to design the contract from V2's answer"
        )
    if set(use) != V2_OUTPUT_USE_KEYS:
        raise ValidationError(
            f"V2_OUTPUT_USE records {sorted(use)}; it records what V2's answer established, what it "
            "did not choose, and a note, and nothing else"
        )
    if tuple(use["USED_TO_ESTABLISH"]) != USED_TO_ESTABLISH:
        raise ValidationError(
            "the record uses V2's answer for more than establishing that the violation happened. "
            "The rejected answer is not rescued, is not a candidate, and chooses no bound"
        )
    for name, record in (("alignment", doc), ("prompt", prompt)):
        bad = sorted(
            {k for k in _keys(record) if any(f in k.upper() for f in FORBIDDEN_KEY_FRAGMENTS)}
        )
        if bad:
            raise ValidationError(f"the {name} record proposes a replacement bound: {bad}")


def _cited_maximum(violation: str) -> int:
    match = re.search(r"exceeds maxLength (\d+)$", violation)
    if match is None:
        raise ValidationError(f"V2's violation {violation!r} cites no maximum")
    return int(match.group(1))


def _check_contract(doc: dict[str, Any]) -> None:
    live = schema_sha(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    for name, digest in (
        ("V2 execution packet", _load(PACKET_V2)["OUTPUT_SCHEMA_SHA256"]),
        ("frozen v1.1.0 prompt", _load(PROMPT_V2)["OUTPUT_SCHEMA_SHA256"]),
    ):
        if digest != live:
            raise ValidationError(
                f"the live schema hashes to {live}, and the {name} bound {digest}: the schema "
                "changed, and the operator kept it unchanged"
            )
    properties = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]
    kept = properties[FAILED_FIELD]["maxLength"]
    cited = _cited_maximum(_load(RECORD_V2)["SCHEMA_VIOLATIONS"][0])
    if kept != cited:
        raise ValidationError(
            f"{FAILED_FIELD}.maxLength is {kept} live and V2 was refused against {cited}: the "
            "operator decided not to raise it"
        )
    _fixed(
        doc["CONTRACT"],
        {
            "OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
            "OUTPUT_SCHEMA_SHA256": live,
            "OUTPUT_GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
            "SCHEMA_CHANGED": False,
            "GATE_CHANGED": False,
            "EVIDENCE_BOUND_REASONING_SUMMARY_MAX_LENGTH": kept,
            "CRITICAL_UNCERTAINTY_ITEM_MAX_LENGTH": properties["critical_uncertainties"]["items"][
                "maxLength"
            ],
            "COMMERCIAL_CLAIM_ITEM_MAX_LENGTH": properties["commercial_claims_supported"]["items"][
                "maxLength"
            ],
        },
        "CONTRACT",
    )
    if (
        properties["commercial_claims_not_supported"]["items"]["maxLength"]
        != doc["CONTRACT"]["COMMERCIAL_CLAIM_ITEM_MAX_LENGTH"]
    ):
        raise ValidationError("the two commercial-claim bounds no longer agree")
    if "Mission 1.31" not in str(
        doc["CONTRACT"]["EVIDENCE_BOUND_REASONING_SUMMARY_MAX_LENGTH_SOURCE"]
    ):
        raise ValidationError("the source of the 900 bound is not traced to Mission 1.31's base")


def _string_constants(tree: ast.AST) -> Iterator[ast.Constant]:
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr):
            value = body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                docstrings.add(id(value))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ):
            yield node


def _check_renderer() -> None:
    """The renderer reads a schema and a policy, and cannot read anything else or carry a bound."""
    tree = ast.parse(RENDERER_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = ["." * node.level + (node.module or "")]
        else:
            names = []
        for name in names:
            if name not in RENDERER_IMPORTS:
                raise ValidationError(
                    f"the renderer imports {name!r}. It may read the schema it is handed and "
                    "nothing else: no file, no record, no response, no model"
                )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in RENDERER_FORBIDDEN_CALLS
        ):
            raise ValidationError(f"the renderer calls {node.func.id}()")
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
            and node.value not in (0, 1)
        ):
            raise ValidationError(
                f"the renderer carries the number {node.value!r}. Every number the model is "
                "told comes from the schema, so a bound written here is a second copy"
            )
    for constant in _string_constants(tree):
        if re.search(r"\d\d", constant.value):
            raise ValidationError(
                f"the renderer carries a string with a number in it: {constant.value[:60]!r}"
            )

    contract = ast.parse(CONTRACT_SOURCE.read_text(encoding="utf-8"))
    assignments = {
        target.id: node
        for node in contract.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    call = assignments.get("SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2")
    value = call.value if call is not None else None
    if not (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "render_output_constraints"
        and [a.id for a in value.args if isinstance(a, ast.Name)]
        == ["SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1", "OUTPUT_CONSTRAINT_NOTES_V1_2"]
        and len(value.args) == 2
        and not value.keywords
    ):
        raise ValidationError(
            "the v1.2.0 constraint block is not rendered from the live v1.1.0 schema. A block "
            "written by hand, or rendered from anything else, is the drift this prompt removes"
        )
    start = assignments["SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2"].lineno
    for node in ast.walk(contract):
        if (
            getattr(node, "lineno", 0) > start
            and isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
        ):
            raise ValidationError(
                f"the v1.2.0 section carries the number {node.value!r} on line {node.lineno}; a "
                "bound there is a second copy of the schema"
            )


def _check_composition() -> None:
    rendered = render_output_constraints(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, OUTPUT_CONSTRAINT_NOTES_V1_2
    )
    if rendered != SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2:
        raise ValidationError(
            "the prompt's constraint block is not the rendering of the live schema: a schema bound "
            "changed and the prompt did not, or the prompt was edited by hand"
        )
    if rendered != render_output_constraints(
        copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1), dict(OUTPUT_CONSTRAINT_NOTES_V1_2)
    ):
        raise ValidationError("the renderer is not deterministic over an equal schema")
    for name, phrase in (
        ("opening", OUTPUT_CONTRACT_OPENING),
        ("closing", OUTPUT_CONTRACT_CLOSING),
    ):
        if re.search(r"\d", phrase):
            raise ValidationError(f"the {name} sentence carries a number")
        if phrase not in BOUNDED_OUTPUT_CONTRACT_RULES:
            raise ValidationError(f"the {name} sentence is not v1.1.0's, word for word")
    block = OUTPUT_CONTRACT_OPENING + "\n\n" + rendered + "\n\n" + OUTPUT_CONTRACT_CLOSING
    if block != SECOND_OPPORTUNITY_OUTPUT_CONTRACT_BLOCK_V1_2:
        raise ValidationError(
            "the output-contract block is not its opening, derivation and closing"
        )
    composed = SECOND_OPPORTUNITY_SYSTEM + "\n" + block + "\n"
    if composed != SECOND_OPPORTUNITY_SYSTEM_V1_2:
        raise ValidationError(
            "the v1.2.0 system region is not v1.0.0's, verbatim, followed by the derived block"
        )


def _check_inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = expected_inventory()
    if doc["CONSTRAINT_INVENTORY"] != rows:
        recorded = {_label(r): r for r in doc["CONSTRAINT_INVENTORY"]}
        live = {_label(r): r for r in rows}
        moved = sorted(k for k in set(recorded) | set(live) if recorded.get(k) != live.get(k))
        raise ValidationError(f"the recorded inventory is not the live schema's: {moved[:6]}")
    if doc["CLASS_COUNTS"] != class_counts(rows):
        raise ValidationError("the class counts are not the inventory's")
    policy = {rule: {"class": c, "rationale": r} for rule, (c, r) in CLASSIFICATION_POLICY.items()}
    if doc["CLASSIFICATION_POLICY"] != policy:
        raise ValidationError("the recorded classification policy is not the renderer's")
    lists = missing_lists(rows)
    for key, value in lists.items():
        if doc.get(key) != value:
            raise ValidationError(f"{key} is {doc.get(key)!r}; the inventory gives {value!r}")
    if lists["UNSTATED_IN_V1_2_0"]:
        raise ValidationError(
            f"PROMPT_STILL_OMITS generation-relevant constraints: {lists['UNSTATED_IN_V1_2_0']}"
        )
    if not lists["FAILED_FIELD_BOUND_MISSING_FROM_V1_1_0"]:
        raise ValidationError("the audit no longer finds the bound V2 was refused on")
    _fixed(
        doc["RENDERER"],
        {
            "id": OUTPUT_CONSTRAINT_RENDERER_VERSION,
            "module": "packages/opportunity-engine/python/sros_opportunity/output_constraints.py",
            "INPUTS": ["the live output schema object", "the explicit rendering policy"],
            "DETERMINISTIC": True,
            "notes": dict(OUTPUT_CONSTRAINT_NOTES_V1_2),
        },
        "RENDERER",
    )
    for forbidden in ("model output", "execution history", "a response artifact"):
        if forbidden not in doc["RENDERER"]["NOT_INPUTS"]:
            raise ValidationError(f"the renderer's non-inputs no longer name {forbidden}")
    return rows


def _check_enforcement(doc: dict[str, Any]) -> None:
    block = doc["ENFORCEMENT"]
    if block.get("LOCAL_VALIDATOR_AUTHORITATIVE") is not True:
        raise ValidationError("the local validator is no longer authoritative")
    if set(block.get("POST_PROCESSING", {})) != set(POST_PROCESSING):
        raise ValidationError("the post-processing prohibitions are not the six")
    for key in POST_PROCESSING:
        if block["POST_PROCESSING"][key] is not False:
            raise ValidationError(f"{key} is permitted, and no answer is changed to fit a bound")


def _check_prompt_document(prompt: dict[str, Any], doc: dict[str, Any]) -> None:
    predecessor = _load(PROMPT_V2)
    system = SECOND_OPPORTUNITY_SYSTEM_V1_2
    _fixed(
        prompt,
        {
            "mission": "1.84.8",
            "recorded_by": THIS_MISSION,
            "PROMPT_ID": SECOND_OPPORTUNITY_PROMPT_ID,
            "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
            "PROCEDURE": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
            "PREDECESSOR_PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
            "PREDECESSOR_PROMPT_SHA256": predecessor["PROMPT_SHA256"],
            "PREDECESSOR_UNCHANGED": True,
            "SUBJECT": predecessor["SUBJECT"],
            "PACKET_ID": predecessor["PACKET_ID"],
            "OUTPUT_CONSTRAINT_RENDERER": OUTPUT_CONSTRAINT_RENDERER_VERSION,
            "OUTPUT_CONTRACT_BLOCK_SHA256": _sha(SECOND_OPPORTUNITY_OUTPUT_CONTRACT_BLOCK_V1_2),
            "SYSTEM_INSTRUCTION": system,
            "SYSTEM_SHA256": _sha(system),
            "PREDECESSOR_SYSTEM_SHA256": predecessor["SYSTEM_SHA256"],
            "BASE_SYSTEM_SHA256": predecessor["PREDECESSOR_SYSTEM_SHA256"],
            "SYSTEM_EXTENDS_V1_0_0_VERBATIM": True,
            "TRUSTED_CONTEXT_SHA256": predecessor["TRUSTED_CONTEXT_SHA256"],
            "TASK_SHA256": predecessor["TASK_SHA256"],
            "REGIONS_IDENTICAL_TO_V1_1_0": ["trusted_context", "untrusted", "task"],
            "OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
            "OUTPUT_SCHEMA_SHA256": predecessor["OUTPUT_SCHEMA_SHA256"],
            "OUTPUT_GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
            "TED_REPRESENTATION_SHA256": REPRESENTATION_SHA256,
            "TED_REPRESENTATION_UNCHANGED": True,
            "SENT": False,
        },
        "prompt",
    )
    if _sha(SECOND_OPPORTUNITY_SYSTEM) != predecessor["PREDECESSOR_SYSTEM_SHA256"]:
        raise ValidationError("the v1.0.0 system region moved under both successors")
    if not system.startswith(SECOND_OPPORTUNITY_SYSTEM):
        raise ValidationError("v1.2.0 does not extend v1.0.0 verbatim")
    for digest in ("PROMPT_SHA256", "UNTRUSTED_SHA256", "PREDECESSOR_UNTRUSTED_SHA256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(prompt.get(digest))):
            raise ValidationError(f"the prompt document's {digest} is not a digest")
    if prompt["PROMPT_SHA256"] in (predecessor["PROMPT_SHA256"], _load(PACKET_V2)["PROMPT_SHA256"]):
        raise ValidationError("the successor carries the predecessor's digest")
    if prompt["UNTRUSTED_SHA256"] != prompt["PREDECESSOR_UNTRUSTED_SHA256"]:
        raise ValidationError("the untrusted TED region differs between v1.1.0 and v1.2.0")
    placeholder = prompt["INPUT_PLACEHOLDER"]
    before = predecessor["INPUT_PLACEHOLDER"]
    if placeholder["labels"] != before["labels"] or placeholder["count"] != before["count"]:
        raise ValidationError("the untrusted statements are not the ones v1.1.0 carried")
    diff = semantic_diff(frozen_v1_1_text(), system)
    recorded = {k: v for k, v in prompt["SEMANTIC_DIFF"].items() if not k.endswith("note")}
    if recorded != diff:
        moved = sorted(k for k in set(recorded) | set(diff) if recorded.get(k) != diff.get(k))
        raise ValidationError(f"the recorded semantic diff is not the recomputed one: {moved}")
    for flag in SEMANTIC_FLAGS:
        if diff[flag] is not False:
            raise ValidationError(f"{flag}: the change reaches beyond the output contract")
    block = doc["PROMPT"]
    _fixed(
        block,
        {
            "PREDECESSOR_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
            "PREDECESSOR_SHA256": predecessor["PROMPT_SHA256"],
            "SUCCESSOR_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
            "SUCCESSOR_SHA256": prompt["PROMPT_SHA256"],
            "document": "docs/data/second-opportunity-synthesis-prompt-v3.json",
        },
        "PROMPT",
    )


def _check_accounting(doc: dict[str, Any]) -> None:
    for key in ACCOUNTING_ZERO:
        if doc["ACCOUNTING"].get(key) != 0:
            raise ValidationError(
                f"ACCOUNTING.{key} is {doc['ACCOUNTING'].get(key)}, and this is 0"
            )


def _check_history() -> None:
    """Section 2: the history the operator decided on is the history on disk, byte for byte.

    Run last, so that an edit a content check was written for is refused by that check and names
    its own defect; this one catches whatever no content check reads.
    """
    for name, expected in HISTORY_SHA256.items():
        actual = _file_sha(DATA / name)
        if actual != expected:
            raise ValidationError(
                f"{name} hashes to {actual} and Mission 1.84.7 left {expected}. A historical "
                "record is never rewritten, and a rewritten one is where a rejected answer gets "
                "promoted"
            )


def validate() -> tuple[dict[str, Any], dict[str, Any]]:
    doc = _load(ALIGNMENT)
    prompt = _load(PROMPT)
    _check_operator_decision(doc)
    _check_v2(doc, prompt)
    _check_contract(doc)
    _check_renderer()
    _check_composition()
    _check_inventory(doc)
    if doc["DRIFT_PROPERTY"] != drift_property():
        raise ValidationError("the recorded drift property is not the recomputed one")
    _check_enforcement(doc)
    _check_prompt_document(prompt, doc)
    _check_accounting(doc)
    _check_history()
    return doc, prompt


# ------------------------------------------------------------------------------ rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_output_constraint_"
    "alignment.py from {source}. Do not edit by hand; edit the JSON and re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def _sentence(text: object) -> str:
    value = str(text).strip()
    return value if value.endswith((".", "!", "?")) else value + "."


def _value(row: dict[str, Any]) -> str:
    value = row["value"]
    if isinstance(value, list):
        return f"{len(value)} members" if row["keyword"] == "enum" else f"{len(value)} fields"
    if row["keyword"] == "pattern":
        return "a canonical grammar"
    return json.dumps(value) if isinstance(value, bool) else str(value)


def _flag(value: object) -> str:
    return "n/a" if value is None else ("yes" if value else "**no**")


def render_alignment(doc: dict[str, Any]) -> str:
    decision = doc["OPERATOR_DECISION"]
    facts = doc["V2_FACTS"]
    contract = doc["CONTRACT"]
    letters = {name: letter for letter, name in CONSTRAINT_CLASS_LETTERS.items()}
    out = [
        HEADER.format(source=ALIGNMENT.name),
        "# Second opportunity: output-constraint alignment v1",
        "",
        f"Mission {doc['mission']}, recorded {doc['recorded_on']}. **{doc['ALIGNMENT_OUTCOME']}.**",
        "",
        _sentence(doc["summary"]),
        "",
        "## The operator's decision",
        "",
        *[f"> {line}" for line in decision["OPERATOR_STATEMENT"]],
        "",
        f"SHA-256 of the statement: `{decision['OPERATOR_STATEMENT_SHA256']}`. Decisions: "
        + ", ".join(f"`{d}`" for d in decision["DECISIONS"])
        + ". The V2 answer is not rescued, no maximum is chosen from it, and nothing here "
        "authorises a schema change or an inference.",
        "",
        "## What V2 retained, recomputed",
        "",
        *_code(
            [
                f"packet        {facts['EXECUTION_PACKET_SHA256']}",
                f"outcome       {facts['OUTCOME']}",
                f"requests      {facts['PROVIDER_REQUESTS']} provider, {facts['MODEL_CALLS']} "
                f"model call, {facts['RETRIES']} retries, {facts['FALLBACKS']} fallbacks",
                f"stop reason   {facts['STOP_REASON']}",
                f"usage         {facts['INPUT_TOKENS']} in, {facts['OUTPUT_TOKENS']} out, "
                f"{facts['THINKING_TOKENS']} thinking; cost {facts['ACTUAL_COST']}",
                f"failed stage  {facts['FAILED_STAGE']}",
                *[f"violation     {v}" for v in facts["SCHEMA_VIOLATIONS"]],
                f"not reached   {', '.join(s.split('_')[0] for s in facts['STAGES_NOT_REACHED'])}",
                f"persisted     {str(facts['CANONICAL_PERSISTENCE']).lower()}; approval consumed "
                f"{str(facts['APPROVAL_CONSUMED']).lower()}",
            ]
        ),
        "The violation is recomputed by the live v1.1.0 validator over the answer V2 retained. "
        f"{_sentence(doc['V2_OUTPUT_USE']['note'])}",
        "",
        "## The contract, unchanged",
        "",
        f"`{contract['OUTPUT_SCHEMA_VERSION']}` `{contract['OUTPUT_SCHEMA_SHA256']}` and "
        f"`{contract['OUTPUT_GATE_VERSION']}`; schema changed `false`, gate changed `false`. "
        f"`{FAILED_FIELD}.maxLength` is {contract['EVIDENCE_BOUND_REASONING_SUMMARY_MAX_LENGTH']}: "
        f"{contract['EVIDENCE_BOUND_REASONING_SUMMARY_MAX_LENGTH_SOURCE']}. The critical-uncertainty "
        f"and commercial-claim item bounds stay {contract['CRITICAL_UNCERTAINTY_ITEM_MAX_LENGTH']} "
        f"and {contract['COMMERCIAL_CLAIM_ITEM_MAX_LENGTH']}.",
        "",
        "## The renderer",
        "",
        f"`{doc['RENDERER']['id']}`, in `{doc['RENDERER']['module']}`. It reads "
        f"{' and '.join(doc['RENDERER']['INPUTS'])}; it never reads "
        f"{', '.join(doc['RENDERER']['NOT_INPUTS'])}. {_sentence(doc['RENDERER']['note'])}",
        "",
        "| rule | class | why |",
        "|---|---|---|",
        *[
            f"| `{rule}` | {letters[entry['class']]} `{entry['class']}` | {entry['rationale']} |"
            for rule, entry in doc["CLASSIFICATION_POLICY"].items()
        ],
        "",
        "## Every constraint of the schema",
        "",
        "Class counts: "
        + ", ".join(f"{letter} {count}" for letter, count in doc["CLASS_COUNTS"].items())
        + ". A constraint of class A is generation-relevant; the last two columns say whether each "
        "prompt states it in words, decided by one rule for both.",
        "",
        "| path | keyword | value | class | v1.1.0 | v1.2.0 |",
        "|---|---|---|---|---|---|",
        *[
            f"| `{row['path']}` | `{row['keyword']}` | {_value(row)} | {letters[row['class']]} | "
            f"{_flag(row['explicit_in_v1_1_0'])} | {_flag(row['explicit_in_v1_2_0'])} |"
            for row in doc["CONSTRAINT_INVENTORY"]
        ],
        "",
        "## What v1.1.0 left to the tool schema",
        "",
        f"`WERE_OTHER_SCHEMA_BOUNDS_MISSING_FROM_PROMPT = "
        f"{str(doc['WERE_OTHER_SCHEMA_BOUNDS_MISSING_FROM_PROMPT']).lower()}`. Besides "
        f"`{FAILED_FIELD} maxLength`, the bound V2 was refused on, v1.1.0 did not state:",
        "",
        *[f"- `{item}`" for item in doc["OTHER_SCHEMA_BOUNDS_MISSING_FROM_V1_1_0"]],
        "",
        "Nor these generation-relevant constraints that are not bounds:",
        "",
        *[f"- `{item}`" for item in doc["OTHER_GENERATION_CONSTRAINTS_MISSING_FROM_V1_1_0"]],
        "",
        f"v1.1.0 did state: {', '.join(f'`{i}`' for i in doc['EXPLICIT_IN_V1_1_0'])}. "
        f"v1.2.0 leaves {len(doc['UNSTATED_IN_V1_2_0'])} unstated.",
        "",
        f"{_sentence(doc['CARDINALITY_POLICY'])}",
        "",
        "## The drift property",
        "",
        *_code([f"{key.lower():50s} {value}" for key, value in doc["DRIFT_PROPERTY"].items()]),
        _sentence(doc["drift_note"]),
        "",
        "## The validator still decides",
        "",
        "Local validator authoritative: `true`. "
        + ", ".join(f"`{k}`" for k in doc["ENFORCEMENT"]["POST_PROCESSING"])
        + ": all `false`. "
        + _sentence(doc["ENFORCEMENT"]["note"]),
        "",
        "## Accounting",
        "",
        *_code([f"{key.lower():28s} {value}" for key, value in doc["ACCOUNTING"].items()]),
    ]
    return "\n".join(out)


def render_prompt(prompt: dict[str, Any]) -> str:
    diff = prompt["SEMANTIC_DIFF"]
    block = prompt["SYSTEM_INSTRUCTION"][len(SECOND_OPPORTUNITY_SYSTEM) + 1 :].rstrip("\n")
    out = [
        HEADER.format(source=PROMPT.name),
        "# Second opportunity synthesis prompt v1.2.0",
        "",
        f"Mission {prompt['mission']}, recorded {prompt['recorded_at']}. Frozen and not sent: "
        f"{_sentence(prompt['sent_note'])}",
        "",
        *_code(
            [
                f"PROMPT_SHA256                 {prompt['PROMPT_SHA256']}",
                f"predecessor v1.1.0            {prompt['PREDECESSOR_PROMPT_SHA256']}",
                f"system region                 {prompt['SYSTEM_SHA256']}",
                f"predecessor system (v1.1.0)   {prompt['PREDECESSOR_SYSTEM_SHA256']}",
                f"base system (v1.0.0)          {prompt['BASE_SYSTEM_SHA256']}",
                f"output-contract block         {prompt['OUTPUT_CONTRACT_BLOCK_SHA256']}",
                f"trusted context               {prompt['TRUSTED_CONTEXT_SHA256']}",
                f"task                          {prompt['TASK_SHA256']}",
                f"untrusted (v1.2.0 = v1.1.0)   {prompt['UNTRUSTED_SHA256']}",
                f"schema / gate                 {prompt['OUTPUT_SCHEMA_VERSION']} / "
                f"{prompt['OUTPUT_GATE_VERSION']}",
                f"renderer                      {prompt['OUTPUT_CONSTRAINT_RENDERER']}",
                f"TED representation            {prompt['TED_REPRESENTATION_SHA256']}",
            ]
        ),
        "The trusted context, the untrusted TED statements and the task are byte-identical to "
        "v1.1.0. The system region is v1.0.0's, verbatim, followed by the output-contract block "
        "below, which is rendered from the live schema.",
        "",
        "## The output-contract block",
        "",
        *_code(block.splitlines()),
        "## The semantic diff from v1.1.0",
        "",
        f"Change confined to the output-contract block after the {diff['UNCHANGED_V1_0_0_PREFIX_LINES']}"
        f" lines of v1.0.0: `{str(diff['CHANGE_CONFINED_TO_THE_OUTPUT_CONTRACT_BLOCK']).lower()}`. "
        "Everything v1.1.0 stated is still stated: "
        f"`{str(diff['EXPLICIT_IN_V1_1_0_STILL_EXPLICIT']).lower()}`. Guidance notes and framing "
        f"preserved: `{str(diff['GUIDANCE_NOTES_PRESERVED']).lower()}`, "
        f"`{str(diff['FRAMING_PRESERVED']).lower()}`.",
        "",
        "Removed lines:",
        "",
        *_code(diff["REMOVED_LINES"]),
        "Added lines:",
        "",
        *_code(diff["ADDED_LINES"]),
        ", ".join(f"`{flag}`" for flag in SEMANTIC_FLAGS) + ": all `false`. "
        f"{_sentence(diff['note'])}",
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
        doc, prompt = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    rendered = {ALIGNMENT_MD: render_alignment(doc), PROMPT_MD: render_prompt(prompt)}
    if args.write:
        for path, text in rendered.items():
            path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {', '.join(p.name for p in rendered)}")
    stale = [p for p, text in rendered.items() if p.read_text(encoding="utf-8") != text]
    for path in stale:
        print(f"FAIL     {path.name} is not the rendering of its record")
    if stale:
        return 1
    print("ok       prompt v1.2.0 states every generation-relevant bound the live schema enforces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
