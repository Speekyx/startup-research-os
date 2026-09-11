#!/usr/bin/env python
"""Mission 1.84.4 gate: the bounded successor output contract, checked against live code.

Three records, one gate, because they are one decision recorded in three places and a gate that
checked them apart would let them disagree:

    second-opportunity-output-boundedness-decision-v1.json   what each of the eight became, and why
    second-opportunity-output-capacity-analysis-v2.json      the maximum that now exists
    second-opportunity-synthesis-prompt-v2.json              the prompt version that changed with it

**THE GATE RE-DERIVES RATHER THAN READS.** Mission 1.84.3's lesson: a gate that read `FINITE_BOUND`
out of the document it guards would be checking that somebody typed a boolean. So the walker runs
against the executable schemas, the maximum instance is rebuilt and revalidated here, the
dimension enum is compared against `EvidenceDimension` itself, and the source-family grammar is
read out of the migration that constrains it.

**AND IT GUARDS v1.0.0 IN BOTH DIRECTIONS.** v1.0.0 must still be unbounded -- if somebody
"fixed" it in place, the historical execution would no longer resolve against the contract it
actually used, and this gate fails rather than congratulating them.

What it does NOT do is recompute the rendered prompt digest or the TED representation: both need
the live packet, which needs the database, and CI has neither. Those are recomputed by
`run_second_opportunity_execution.verify()` before any socket exists, which is where they decide
something. Here the three documents are held to agreeing with each other and with the frozen
Mission 1.84 artifacts.

    uv run python infrastructure/scripts/render_second_opportunity_bounded_contract.py
    uv run python infrastructure/scripts/render_second_opportunity_bounded_contract.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import uuid

from sros_contracts.ids import ClaimId, EvidenceId
from sros_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA
from sros_opportunity.dimensions import EvidenceDimension
from sros_opportunity.schema_validation import schema_violations, unsupported_keywords
from sros_opportunity.second_opportunity import (
    BOUNDED_ITEM_TYPES,
    CANONICAL_UUID_PATTERN,
    REGISTRY_SLUG_MAX_LENGTH,
    REGISTRY_SLUG_PATTERN,
    SECOND_OPPORTUNITY_GATE_VERSION,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROMPT_VERSION,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
    SECOND_OPPORTUNITY_SYSTEM,
    SECOND_OPPORTUNITY_SYSTEM_V1_1,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
MIGRATIONS = ROOT / "infrastructure" / "db" / "migrations"

DECISION = DATA / "second-opportunity-output-boundedness-decision-v1.json"
DECISION_MD = DATA / "second-opportunity-output-boundedness-decision-v1.md"
CAPACITY = DATA / "second-opportunity-output-capacity-analysis-v2.json"
CAPACITY_MD = DATA / "second-opportunity-output-capacity-analysis-v2.md"
PROMPT = DATA / "second-opportunity-synthesis-prompt-v2.json"
PROMPT_MD = DATA / "second-opportunity-synthesis-prompt-v2.md"

CAPACITY_V1 = DATA / "second-opportunity-output-capacity-analysis-v1.json"
PROMPT_V1 = DATA / "second-opportunity-synthesis-prompt-v1.json"
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
PACKET_V2 = DATA / "second-opportunity-synthesis-execution-packet-v2.json"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
PROMPT_V1_SHA256 = "af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080"

#: The eight paths Mission 1.84.3 found unbounded in v1.0.0. Named here so that bounding a
#: DIFFERENT set, or bounding seven of them, fails rather than passes with a smaller number.
THE_EIGHT = tuple(field for field, _ in BOUNDED_ITEM_TYPES)

SEMANTIC_CLASSES = (
    "CLOSED_VOCABULARY",
    "CANONICAL_IDENTIFIER",
    "BOUNDED_IDENTIFIER",
    "BOUNDED_NARRATIVE",
)

ACCEPTABLE_OUTCOMES = (
    "SECOND_OPPORTUNITY_EXECUTION_PACKET_V2_READY_FOR_OPERATOR_APPROVAL",
    "BOUNDED_SCHEMA_READY_TOKEN_CEILING_REQUIRES_OPERATOR_DECISION",
    "SOURCE_FAMILY_OUTPUT_TYPE_REQUIRES_ARCHITECTURE_DECISION",
    "OUTPUT_SCHEMA_V1_1_REMAINS_UNBOUNDED",
    "BOUNDED_OUTPUT_CONTRACT_EXCEEDS_MODEL_CAPABILITY",
    "MODEL_COST_BASIS_REQUIRES_REFRESH",
    "RETENTION_PATH_NOT_READY_FOR_SECOND_EXECUTION",
    "APPROVED_TED_EGRESS_REPRESENTATION_CHANGED",
)

WORST_FILL = "\U0001f600"
ASCII_FILL = '"'


class ValidationError(RuntimeError):
    """A record disagrees with the live schema, with a frozen artifact, or with its siblings."""


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True)


def unbounded_paths(schema: dict) -> list[str]:
    """Mission 1.84.3's walker, re-derived here rather than imported from its gate.

    Imported, it would share a defect with the gate that produced the finding; written out, the
    two agree on eight unbounded paths in v1.0.0 independently, which is worth more than one
    function agreeing with itself.
    """
    found: list[str] = []

    def walk(node: dict, path: str) -> None:
        kind = node.get("type")
        if kind == "string":
            if "enum" not in node and node.get("maxLength") is None:
                found.append(path)
        elif kind == "array":
            if node.get("maxItems") is None:
                found.append(path)
            items = node.get("items")
            if isinstance(items, dict):
                walk(items, f"{path}[]")
            else:
                found.append(path)
        elif kind == "object":
            if node.get("additionalProperties") is not False:
                found.append(path)
            for name, sub in (node.get("properties") or {}).items():
                walk(sub, f"{path}.{name}" if path else name)
        elif kind in ("number", "integer"):
            if node.get("maximum") is None or node.get("minimum") is None:
                found.append(path)
        elif kind is None:
            found.append(path)

    walk(schema, "")
    return sorted(found)


def maximum_instance(node: dict, fill: str) -> object:
    """The largest instance the schema admits. Rebuilt here so the record's numbers are checked."""
    kind = node.get("type")
    if kind == "string":
        enum = node.get("enum")
        if enum:
            return max(sorted(enum), key=len)
        pattern = node.get("pattern")
        if pattern == CANONICAL_UUID_PATTERN:
            return "0" * 8 + "-" + "0" * 4 + "-" + "0" * 4 + "-" + "0" * 4 + "-" + "0" * 12
        if pattern == REGISTRY_SLUG_PATTERN:
            return "a" * int(node["maxLength"])
        return fill * int(node["maxLength"])
    if kind == "array":
        return [maximum_instance(node["items"], fill) for _ in range(int(node["maxItems"]))]
    if kind == "object":
        return {k: maximum_instance(v, fill) for k, v in node["properties"].items()}
    raise ValidationError(f"the maximum-instance builder does not handle type {kind!r}")


# --------------------------------------------------------------------------- the checks


def _check_v1_0_0_was_not_edited() -> None:
    """v1.0.0 keeps its defect, because the historical execution used it.

    This is the check most likely to be read as backwards. Repairing v1.0.0 in place would make
    the frozen prompt document's OUTPUT_SCHEMA_SHA256 name a schema nobody sent, and Mission
    1.84.3's finding would become unreproducible from the repository that recorded it.
    """
    live = unbounded_paths(SECOND_OPPORTUNITY_OUTPUT_SCHEMA)
    if len(live) != 8:
        raise ValidationError(
            f"v1.0.0 now has {len(live)} unbounded required paths, not 8. It was edited in place, "
            "and a historical execution must keep resolving against the contract it actually used"
        )
    if sorted(live) != sorted(f"{field}[]" for field in THE_EIGHT):
        raise ValidationError(f"v1.0.0's unbounded paths are not the eight 1.84.3 named: {live}")
    required = list(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"])
    if len(required) != 20:
        raise ValidationError(f"v1.0.0 requires {len(required)} fields, not 20")


def _check_the_successor_is_finite(record: dict) -> None:
    live = unbounded_paths(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    if live:
        raise ValidationError(
            f"OUTPUT_SCHEMA_V1_1_REMAINS_UNBOUNDED: {live}. No ceiling may be chosen while an "
            "unbounded path survives"
        )
    if not record["FINITE_BOUND"]:
        raise ValidationError("the walker finds no unbounded path and the record says not finite")
    if record["unbounded_path_count"] != 0 or record["unbounded_paths"]:
        raise ValidationError("the record claims an unbounded path the live schema does not have")
    if record["predecessor_unbounded_path_count"] != 8:
        raise ValidationError("the record misstates how many paths v1.0.0 had")
    unsupported = unsupported_keywords(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    if unsupported:
        raise ValidationError(
            f"the successor uses keywords the validator ignores: {unsupported}. A bound nothing "
            "checks is a sentence in a document"
        )


def _check_nothing_was_reduced() -> None:
    """Section 32. maxItems is the one number a capacity-driven edit would reach for first."""
    old = SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"]
    new = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]
    if sorted(old) != sorted(new):
        raise ValidationError("the successor added or removed a top-level field")
    if list(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]) != list(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["required"]
    ):
        raise ValidationError("the successor changed which fields are required, or their order")
    for name, node in old.items():
        if node.get("maxItems") != new[name].get("maxItems"):
            raise ValidationError(
                f"{name}: maxItems moved from {node.get('maxItems')} to "
                f"{new[name].get('maxItems')}. Reducing a cardinality to rescue capacity is the "
                "move section 32 forbids"
            )
        if name not in THE_EIGHT and _canonical(node) != _canonical(new[name]):
            raise ValidationError(f"{name} changed, and it is not one of the eight")


def _check_each_bound_matches_its_semantics(record: dict) -> None:
    """Section 5: the bound must match the field, not a number applied eight times."""
    properties = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]
    methods = dict(BOUNDED_ITEM_TYPES)

    dimension_values = [d.value for d in EvidenceDimension]
    for name in ("supported_dimensions", "unsupported_dimensions"):
        items = properties[name]["items"]
        if items.get("enum") != dimension_values:
            raise ValidationError(
                f"{name} does not carry the canonical EvidenceDimension vocabulary. Section 6 "
                "forbids a manually-maintained second dimension list"
            )
        if "maxLength" in items:
            raise ValidationError(
                f"{name} carries a maxLength beside its enum; a length would suggest a short "
                "unknown dimension might pass"
            )

    for name in ("supporting_evidence_ids", "supporting_claim_ids"):
        items = properties[name]["items"]
        if items.get("pattern") != CANONICAL_UUID_PATTERN:
            raise ValidationError(f"{name} is not bound to the canonical identifier grammar")

    # The identity grammar is asserted against the identity CLASSES rather than trusted.
    pattern = re.compile(CANONICAL_UUID_PATTERN)
    for identity in (ClaimId, EvidenceId):
        generated = identity.generate()
        if not pattern.match(str(generated)):
            raise ValidationError(f"{identity.__name__} produces ids the schema pattern refuses")
    raw = uuid.uuid4()
    if pattern.match(str(raw).upper()):
        raise ValidationError("the identifier pattern accepts a non-canonical uppercase spelling")

    families = properties["source_families"]["items"]
    if families.get("pattern") != REGISTRY_SLUG_PATTERN:
        raise ValidationError("source_families is not bound to the registry slug grammar")
    if families.get("maxLength") != REGISTRY_SLUG_MAX_LENGTH:
        raise ValidationError("source_families does not carry the registry's own maximum")
    if "enum" in families:
        raise ValidationError(
            "source_families carries an enum. source_family is a REGISTRY in domain.v1.json and "
            "not a closed enum, so freezing today's members would make the schema refuse a true "
            "answer the moment a new family is registered"
        )
    _check_the_slug_grammar_is_the_registrys()

    uncertainties = properties["critical_uncertainties"]["items"]
    if uncertainties.get("maxLength") != 500 or uncertainties.get("minLength") != 1:
        raise ValidationError(
            "critical_uncertainties does not carry the operator's section 10 bound"
        )
    for name in ("commercial_claims_supported", "commercial_claims_not_supported"):
        if properties[name]["items"].get("maxLength") != 300:
            raise ValidationError(f"{name} does not carry the operator's section 11 bound")
        if "enum" in properties[name]["items"]:
            raise ValidationError(
                f"{name} carries an enum. Section 11 required the semantics to be inspected, and "
                "the Mission 1.31.1 output plus the prose audit in the persistence gate settle it "
                "as narrative"
            )

    recorded = {row["path"]: row for row in record["BOUNDED_PATHS"]}
    if sorted(recorded) != sorted(f"{field}[]" for field in THE_EIGHT):
        raise ValidationError("the decision record does not cover exactly the eight paths")
    for field, method in methods.items():
        row = recorded[f"{field}[]"]
        if row["semantic_class"] != method:
            raise ValidationError(f"{field}: the record and the code disagree about the method")
        if row["semantic_class"] not in SEMANTIC_CLASSES:
            raise ValidationError(f"{field}: {row['semantic_class']} is not one of the four")
        if row["maxItems_unchanged"] != SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"][field].get(
            "maxItems"
        ):
            raise ValidationError(f"{field}: the record misstates the unchanged maxItems")
        for key in ("canonical_source_of_constraint", "reason", "historical_compatibility_impact"):
            if not str(row.get(key) or "").strip():
                raise ValidationError(f"{field}: {key} is empty")


def _check_the_slug_grammar_is_the_registrys() -> None:
    """The source-family grammar is read out of the migration, not copied into the code and hoped.

    `registry.sources.source_family` has a foreign key to `registry.registry_entries`, and that
    table's CHECK is what actually decides which family ids can exist. If the two ever disagree,
    the schema would be enforcing a grammar the database does not.
    """
    sql = (MIGRATIONS / "0001_foundation.sql").read_text(encoding="utf-8")
    match = re.search(r"registry_entries_id_slug_check\s*\n\s*CHECK \(id ~ '([^']+)'\)", sql)
    if match is None:
        raise ValidationError(
            "registry_entries_id_slug_check was not found in 0001_foundation.sql, so the "
            "source-family grammar cannot be derived from the contract that owns it"
        )
    if match.group(1) != REGISTRY_SLUG_PATTERN:
        raise ValidationError(
            f"the registry enforces {match.group(1)!r} and the schema carries "
            f"{REGISTRY_SLUG_PATTERN!r}"
        )


def _check_the_maximum(record: dict) -> None:
    """Section 19: rebuild it, revalidate it, and compare every number."""
    block = record["MAXIMUM_VALID_INSTANCE"]
    instance = maximum_instance(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, WORST_FILL)
    violations = schema_violations(instance, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    if violations:
        raise ValidationError(f"the maximum instance does not validate: {violations[:2]}")
    if not block["MAX_INSTANCE_SCHEMA_VALID"]:
        raise ValidationError("the record says the maximum instance is invalid and it validates")
    text = _canonical(instance)
    if block["MAX_VALID_OUTPUT_CHARACTERS"] != len(text):
        raise ValidationError(
            f"MAX_VALID_OUTPUT_CHARACTERS is {block['MAX_VALID_OUTPUT_CHARACTERS']} and the "
            f"rebuilt maximum is {len(text)}"
        )
    if block["MAX_VALID_OUTPUT_UTF8_BYTES"] != len(text.encode("utf-8")):
        raise ValidationError("MAX_VALID_OUTPUT_UTF8_BYTES does not match the rebuilt maximum")
    if block["MAX_VALID_OUTPUT_SHA256"] != _sha(text):
        raise ValidationError("MAX_VALID_OUTPUT_SHA256 does not match the rebuilt maximum")

    ascii_text = _canonical(maximum_instance(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, ASCII_FILL))
    if block["ASCII_FILL_MAXIMUM_CHARACTERS"] != len(ascii_text):
        raise ValidationError("ASCII_FILL_MAXIMUM_CHARACTERS does not match the rebuilt instance")
    if block["ASCII_FILL_MAXIMUM_CHARACTERS"] >= block["MAX_VALID_OUTPUT_CHARACTERS"]:
        raise ValidationError(
            "the ASCII-fill diagnostic is not smaller than the maximum, so one of them is not "
            "what it says it is"
        )

    contributions = record["FIELD_CONTRIBUTIONS"]
    if sorted(row["field"] for row in contributions) != sorted(instance):
        raise ValidationError("the field contributions do not cover every top-level field")
    for row in contributions:
        expected = len(_canonical({row["field"]: instance[row["field"]]})) - 2
        if row["max_serialized_characters"] != expected:
            raise ValidationError(f"{row['field']}: contribution is not the rebuilt one")


def _check_no_ceiling_was_invented(record: dict) -> None:
    """Section 22. The whole point of the mission's honest half."""
    tokens = record["TOKENIZATION"]
    # ruff's S105 reads these comparisons as a hardcoded password because the field names contain
    # "TOKEN". They are counts of OUTPUT TOKENS, which is a unit of text and not a credential; the
    # repository has no secret anywhere in this file. Suppressed with the reason stated, following
    # the existing S608 and S105 precedent rather than loosening the rule globally.
    established = "NOT_ESTABLISHED"  # noqa: S105
    if tokens["EXACT_TOKENIZER_AVAILABLE"]:
        if tokens["EXACT_MAX_OUTPUT_TOKEN_COUNT"] == established:
            raise ValidationError("a tokenizer is claimed available and no count was computed")
    elif tokens["EXACT_MAX_OUTPUT_TOKEN_COUNT"] != established:
        raise ValidationError(
            "an exact token count is recorded and no exact tokenizer is available"
        )
    if not tokens["SAFE_TOKEN_BOUND_AVAILABLE"]:
        for key in ("DERIVED_MIN_OUTPUT_TOKEN_CAPACITY", "SELECTED_MAX_OUTPUT_TOKENS"):
            value = record[key]
            if isinstance(value, (int, float)):
                raise ValidationError(
                    f"{key} is a number and no safe token conversion is established. A ceiling "
                    "that cannot be derived must not be chosen"
                )
        if record["SELECTED_MAX_OUTPUT_TOKENS"] != "NONE":
            raise ValidationError("a ceiling was selected without a safe conversion")
        if record["DERIVED_MIN_OUTPUT_TOKEN_CAPACITY"] != "NOT_DERIVABLE":  # noqa: S105
            raise ValidationError("a capacity was derived without a safe conversion")
    if tokens["empirical_ratio_use_here"] != "NONE":
        raise ValidationError(
            "the empirical characters-per-token ratio was used. It is an INPUT measurement and a "
            "ratio too high underestimates tokens, which is the unsafe direction"
        )
    capability = record["PROVIDER_MODEL_CAPABILITY"]
    if isinstance(capability["CONFIGURED_OUTPUT_TOKEN_CAPABILITY"], (int, float)):
        raise ValidationError(
            "an adapter default was recorded as a provider capability. Section 23: a provider "
            "maximum is a capability ceiling and never a schema size proof"
        )


def _check_no_v2(record: dict) -> None:
    if record["EXECUTION_PACKET_V2_CREATED"]:
        raise ValidationError("the record claims a V2 packet")
    if PACKET_V2.exists():
        raise ValidationError(
            f"{PACKET_V2.name} exists while the record says no V2 was created. Section 24 permits "
            "one only when a defensible capacity is established"
        )
    if record["PRICING"]["recomputed"]:
        raise ValidationError("pricing was recomputed without a defensible MAX_OUTPUT_TOKENS")
    v1 = record["V1_STATE"]
    if v1["execution_packet_sha256"] != V1_SHA256:
        raise ValidationError("the record names a V1 digest that is not V1's")
    for key in ("unchanged", "EXECUTION_APPROVAL_CONSUMED", "guard_still_refuses_v1"):
        if not v1[key]:
            raise ValidationError(f"V1_STATE.{key} is false")
    if v1["consumption_record_reset"] or v1["PREVIOUS_APPROVAL_REUSABLE"]:
        raise ValidationError("the consumption record was reset, or V1's approval reused")
    if not v1["guard_permits_a_new_digest"]:
        raise ValidationError(
            "the guard refuses an unseen digest too, so a genuinely new packet would be blocked "
            "merely because V1 was consumed"
        )
    packet = _load(PACKET_V1)
    if packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"]:
        raise ValidationError(
            "the frozen V1 packet has been edited to record an approval inside it"
        )


def _check_the_prompt(record: dict, prompt: dict, decision: dict) -> None:
    """Section 13 and 14. A changed schema is a changed execution, and the digest says so."""
    if prompt["PROMPT_VERSION"] != SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1:
        raise ValidationError("the prompt document names a version the code does not carry")
    if prompt["PREDECESSOR_PROMPT_VERSION"] != SECOND_OPPORTUNITY_PROMPT_VERSION:
        raise ValidationError("the prompt document misnames its predecessor")
    if prompt["PREDECESSOR_PROMPT_SHA256"] != PROMPT_V1_SHA256:
        raise ValidationError("the prompt document misstates the frozen v1.0.0 digest")
    if prompt["PROMPT_SHA256"] == PROMPT_V1_SHA256:
        raise ValidationError(
            "the successor prompt carries the predecessor's digest. The hash covers the output "
            "schema, so a bounded contract cannot leave it unchanged"
        )
    frozen = _load(PROMPT_V1)
    if frozen["PROMPT_SHA256"] != PROMPT_V1_SHA256 or frozen["PROMPT_VERSION"] != "1.0.0":
        raise ValidationError("the frozen v1.0.0 prompt document was edited")
    if frozen["OUTPUT_SCHEMA_SHA256"] != _sha(_canonical(SECOND_OPPORTUNITY_OUTPUT_SCHEMA)):
        raise ValidationError(
            "the frozen prompt document no longer names the live v1.0.0 schema digest, so v1.0.0 "
            "was edited underneath it"
        )
    if prompt["SYSTEM_SHA256"] != _sha(SECOND_OPPORTUNITY_SYSTEM_V1_1):
        raise ValidationError("the prompt document's SYSTEM_SHA256 is not the live one")
    if prompt["PREDECESSOR_SYSTEM_SHA256"] != _sha(SECOND_OPPORTUNITY_SYSTEM):
        raise ValidationError("the prompt document's predecessor system digest is not the live one")
    if not SECOND_OPPORTUNITY_SYSTEM_V1_1.startswith(SECOND_OPPORTUNITY_SYSTEM):
        raise ValidationError(
            "the v1.1.0 system region does not extend v1.0.0 verbatim, so a research or refusal "
            "sentence may have been reworded while nobody was looking"
        )
    if prompt["OUTPUT_SCHEMA_SHA256"] != _sha(_canonical(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)):
        raise ValidationError("the prompt document names a schema digest the code does not carry")
    if prompt["SENT"]:
        raise ValidationError("the prompt document records a transmission")
    if prompt["SEMANTIC_DIFF"]["research_semantics_changed"]:
        raise ValidationError("section 14 permits only output-contract instructions to change")
    if decision["PROMPT"]["SUCCESSOR_SHA256"] != prompt["PROMPT_SHA256"]:
        raise ValidationError("the decision record and the prompt document disagree on the digest")
    if record.get("TED_REPRESENTATION_SHA256") != REPRESENTATION_SHA256:
        raise ValidationError("APPROVED_TED_EGRESS_REPRESENTATION_CHANGED")
    for doc in (prompt, decision):
        if doc["TED_REPRESENTATION_SHA256"] != REPRESENTATION_SHA256:
            raise ValidationError("APPROVED_TED_EGRESS_REPRESENTATION_CHANGED")


def _check_the_decision(decision: dict) -> None:
    if decision["OPERATOR_DECISION"] != "BOUND_THE_EIGHT_UNBOUNDED_ITEM_TYPES":
        raise ValidationError("the decision record names a decision the operator did not take")
    if decision["OPERATOR_REJECTED"] != "OPERATOR_DECLARED_ARBITRARY_OUTPUT_TOKEN_CEILING":
        raise ValidationError("the decision record drops what the operator rejected")
    if decision["V1_0_0_MUTATED_IN_PLACE"]:
        raise ValidationError("the record admits v1.0.0 was mutated in place")
    if not decision["V1_0_0_STILL_READABLE"]:
        raise ValidationError("v1.0.0 must remain readable")
    if decision["HISTORICAL_OUTPUTS_REVALIDATED_UNDER_V1_1_0"]:
        raise ValidationError("section 17 forbids revalidating a historical output under v1.1.0")
    for key, value in decision["THINGS_NOT_DONE"].items():
        if key.startswith("$"):
            continue
        if value:
            raise ValidationError(f"THINGS_NOT_DONE.{key} is true")
    if decision["PREDECESSOR_SCHEMA"] != SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION:
        raise ValidationError("the record misnames the predecessor schema")
    if decision["SUCCESSOR_SCHEMA"] != SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1:
        raise ValidationError("the record misnames the successor schema")
    if decision["PREDECESSOR_GATE"] != SECOND_OPPORTUNITY_GATE_VERSION:
        raise ValidationError("the record misnames the predecessor gate")
    if decision["SUCCESSOR_GATE"] != SECOND_OPPORTUNITY_GATE_VERSION_V1_1:
        raise ValidationError("the record misnames the successor gate")
    if decision["SUCCESSOR_GATE"] == decision["PREDECESSOR_GATE"]:
        raise ValidationError(
            "the accepted output language changed and the gate version did not. Section 16"
        )
    if decision["PREDECESSOR_SCHEMA_SHA256"] != _sha(_canonical(SECOND_OPPORTUNITY_OUTPUT_SCHEMA)):
        raise ValidationError("the record's predecessor schema digest is not the live one")
    if decision["SUCCESSOR_SCHEMA_SHA256"] != _sha(
        _canonical(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    ):
        raise ValidationError("the record's successor schema digest is not the live one")


def _check_the_accounting(record: dict) -> None:
    for key, value in record["ACCOUNTING"].items():
        if value != 0:
            raise ValidationError(f"ACCOUNTING.{key} is {value}, and this mission performs none")
    if not record["RETENTION_REPAIR_VERIFIED"]:
        raise ValidationError("RETENTION_PATH_NOT_READY_FOR_SECOND_EXECUTION")
    if record["PRIMARY_OUTCOME"] not in ACCEPTABLE_OUTCOMES:
        raise ValidationError(f"{record['PRIMARY_OUTCOME']} is not an acceptable outcome")
    predecessor = _load(CAPACITY_V1)
    if predecessor["FINITE_BOUND"] or predecessor["unbounded_path_count"] != 8:
        raise ValidationError(
            "capacity-analysis-v1 was rewritten. It truthfully recorded that v1.0.0 has no finite "
            "maximum, and v1.0.0 still does not"
        )
    if record["predecessor_rewritten"]:
        raise ValidationError("the record admits rewriting its predecessor")


def validate() -> tuple[dict, dict, dict]:
    decision = _load(DECISION)
    capacity = _load(CAPACITY)
    prompt = _load(PROMPT)

    _check_v1_0_0_was_not_edited()
    _check_the_successor_is_finite(capacity)
    _check_nothing_was_reduced()
    _check_each_bound_matches_its_semantics(decision)
    _check_the_maximum(capacity)
    _check_no_ceiling_was_invented(capacity)
    _check_no_v2(capacity)
    _check_the_prompt(capacity, prompt, decision)
    _check_the_decision(decision)
    _check_the_accounting(capacity)
    return decision, capacity, prompt


# --------------------------------------------------------------------------- rendering


def _sentence(text: str) -> str:
    return " ".join(str(text).split())


def render_decision(record: dict) -> str:
    lines = [
        "<!-- generated by infrastructure/scripts/render_second_opportunity_bounded_contract.py"
        " -- do not edit -->",
        "",
        "# Second-Opportunity output boundedness decision",
        "",
        f"Mission {record['mission']}, recorded {record['recorded_at']}.",
        "",
        f"**OPERATOR_DECISION: `{record['OPERATOR_DECISION']}`.** The operator explicitly rejected "
        f"`{record['OPERATOR_REJECTED']}` as the fix. {_sentence(record['operator_rejection_note'])}",
        "",
        "```",
        f"predecessor  {record['PREDECESSOR_SCHEMA']}  {record['PREDECESSOR_UNBOUNDED_PATHS']} "
        "unbounded required paths",
        f"successor    {record['SUCCESSOR_SCHEMA']}  0",
        f"gate         {record['PREDECESSOR_GATE']}",
        f"          -> {record['SUCCESSOR_GATE']}",
        f"v1.0.0 mutated in place   {record['V1_0_0_MUTATED_IN_PLACE']}",
        f"v1.0.0 still readable     {record['V1_0_0_STILL_READABLE']}",
        "```",
        "",
        _sentence(record["gate_bump_reason"]),
        "",
        "## The eight, and what each became",
        "",
        "| path | semantic class | new constraint | authority |",
        "|---|---|---|---|",
    ]
    for row in record["BOUNDED_PATHS"]:
        constraint = ", ".join(f"{k} {v}" for k, v in row["new_constraint"].items() if k != "type")
        authority = _sentence(row["canonical_source_of_constraint"])
        if len(authority) > 120:
            authority = authority[:117] + "..."
        lines.append(f"| `{row['path']}` | {row['semantic_class']} | {constraint} | {authority} |")
    lines += ["", "## Why each bound is the one it is", ""]
    for row in record["BOUNDED_PATHS"]:
        lines.append(f"**`{row['path']}`** ({row['semantic_class']}). {_sentence(row['reason'])}")
        if row["operator_judgement"] != "none; derived from a canonical repository contract":
            lines.append(f"Operator judgement: {row['operator_judgement']}.")
        lines.append(
            f"Historical compatibility: {_sentence(row['historical_compatibility_impact'])}"
        )
        lines.append("")
    lines += [
        "## Why a structural validator had to be written",
        "",
        _sentence(record["WHY_A_STRUCTURAL_VALIDATOR_WAS_NEEDED"]),
        "",
        f"Dependencies added: {0 if record['NO_DEPENDENCY_ADDED'] else 'some'}.",
        "",
        "## The prompt moved with the schema",
        "",
        "```",
        f"predecessor  {record['PROMPT']['PREDECESSOR_VERSION']}  "
        f"{record['PROMPT']['PREDECESSOR_SHA256']}",
        f"successor    {record['PROMPT']['SUCCESSOR_VERSION']}  "
        f"{record['PROMPT']['SUCCESSOR_SHA256']}",
        f"regions identical  {', '.join(record['PROMPT']['regions_identical'])}",
        f"regions changed    {', '.join(record['PROMPT']['regions_changed'])}",
        f"system lines       -{record['PROMPT']['system_lines_removed']} "
        f"+{record['PROMPT']['system_lines_added']}",
        "```",
        "",
        _sentence(record["PROMPT"]["why_the_digest_moved"]),
        "",
        "## What did not move",
        "",
        f"**TED representation `{record['TED_REPRESENTATION_SHA256']}`, "
        f"{record['TED_REPRESENTATION_CHARACTERS']} characters, unchanged.** "
        + _sentence(record["ted_note"]),
        "",
        _sentence(record["narrative_character_class_note"]),
        "",
    ]
    return "\n".join(lines)


def render_capacity(record: dict) -> str:
    block = record["MAXIMUM_VALID_INSTANCE"]
    lines = [
        "<!-- generated by infrastructure/scripts/render_second_opportunity_bounded_contract.py"
        " -- do not edit -->",
        "",
        "# Second-Opportunity output capacity analysis v2",
        "",
        f"Mission {record['mission']}, recorded {record['recorded_at']}. Against "
        f"`{record['schema_id']}`.",
        "",
        f"**{record['PRIMARY_OUTCOME']}**",
        "",
        _sentence(record["outcome_basis"]),
        "",
        "```",
        f"FINITE_BOUND                       {record['FINITE_BOUND']}",
        f"UNBOUNDED REQUIRED PATHS           {record['unbounded_path_count']}  "
        f"(v1.0.0: {record['predecessor_unbounded_path_count']})",
        f"MAX_VALID_OUTPUT_CHARACTERS        {block['MAX_VALID_OUTPUT_CHARACTERS']}",
        f"MAX_VALID_OUTPUT_UTF8_BYTES        {block['MAX_VALID_OUTPUT_UTF8_BYTES']}",
        f"MAX_INSTANCE_SCHEMA_VALID          {block['MAX_INSTANCE_SCHEMA_VALID']}",
        f"ASCII-fill diagnostic              {block['ASCII_FILL_MAXIMUM_CHARACTERS']}",
        f"EXACT_TOKENIZER_AVAILABLE          {record['TOKENIZATION']['EXACT_TOKENIZER_AVAILABLE']}",
        f"EXACT_MAX_OUTPUT_TOKEN_COUNT       "
        f"{record['TOKENIZATION']['EXACT_MAX_OUTPUT_TOKEN_COUNT']}",
        f"SAFE_TOKEN_BOUND_AVAILABLE         "
        f"{record['TOKENIZATION']['SAFE_TOKEN_BOUND_AVAILABLE']}",
        f"DERIVED_MIN_OUTPUT_TOKEN_CAPACITY  {record['DERIVED_MIN_OUTPUT_TOKEN_CAPACITY']}",
        f"SELECTED_MAX_OUTPUT_TOKENS         {record['SELECTED_MAX_OUTPUT_TOKENS']}",
        f"EXECUTION_PACKET_V2_CREATED        {record['EXECUTION_PACKET_V2_CREATED']}",
        "```",
        "",
        "## The maximum valid instance",
        "",
        _sentence(block["method"]),
        "",
        f"Fill character `{block['fill_character']}`. " + _sentence(block["fill_rationale"]),
        "",
        f"`MAX_VALID_OUTPUT_SHA256` `{block['MAX_VALID_OUTPUT_SHA256']}`. "
        + _sentence(block["bytes_equal_characters_because"]),
        "",
        _sentence(block["ascii_fill_note"]),
        "",
        "## What consumes the capacity",
        "",
        "| field | max characters | share |",
        "|---|---:|---:|",
    ]
    for row in record["FIELD_CONTRIBUTIONS"]:
        lines.append(
            f"| `{row['field']}` | {row['max_serialized_characters']} | "
            f"{row['percentage_of_total']}% |"
        )
    lines += [
        "",
        _sentence(record["field_contribution_note"]),
        "",
        "## Tokenization",
        "",
        _sentence(record["TOKENIZATION"]["why"]),
        "",
        _sentence(record["TOKENIZATION"]["safe_bound_investigation"]),
        "",
        _sentence(record["TOKENIZATION"]["empirical_ratio_direction_warning"]),
        "",
        "## The model capability",
        "",
        f"`CONFIGURED_OUTPUT_TOKEN_CAPABILITY` is "
        f"`{record['PROVIDER_MODEL_CAPABILITY']['CONFIGURED_OUTPUT_TOKEN_CAPABILITY']}`. "
        + _sentence(record["PROVIDER_MODEL_CAPABILITY"]["what_is_held"]),
        "",
        _sentence(record["PROVIDER_MODEL_CAPABILITY"]["why_that_is_not_the_capability"]),
        "",
        _sentence(record["PROVIDER_MODEL_CAPABILITY"]["provider_limit_is_not_a_schema_proof"]),
        "",
        "## No V2",
        "",
        _sentence(record["why_no_v2"]),
        "",
        _sentence(record["PRICING"]["why"]),
        "",
        "## What was verified rather than assumed",
        "",
        _sentence(record["retention_repair_evidence"]),
        "",
        f"V1 `{record['V1_STATE']['execution_packet_sha256']}` is unchanged and still consumed; "
        f"the guard refuses it with `{record['V1_STATE']['guard_refusal_code']}` and permits an "
        "unseen digest.",
        "",
        "```",
    ]
    for key, value in record["ACCOUNTING"].items():
        lines.append(f"{key:32s} {value}")
    lines += [
        "```",
        "",
        f"**Next: {record['NEXT_REQUIRED_ACTION']}.** " + _sentence(record["next_action_note"]),
        "",
    ]
    return "\n".join(lines)


def render_prompt(record: dict) -> str:
    lines = [
        "<!-- generated by infrastructure/scripts/render_second_opportunity_bounded_contract.py"
        " -- do not edit -->",
        "",
        f"# {record['PROMPT_ID']} {record['PROMPT_VERSION']}",
        "",
        f"Mission {record['mission']}, recorded {record['recorded_at']}. Frozen and **not sent**.",
        "",
        "```",
        f"PROMPT_SHA256              {record['PROMPT_SHA256']}",
        f"predecessor {record['PREDECESSOR_PROMPT_VERSION']}              "
        f"{record['PREDECESSOR_PROMPT_SHA256']}",
        f"SYSTEM_SHA256              {record['SYSTEM_SHA256']}",
        f"TRUSTED_CONTEXT_SHA256     {record['TRUSTED_CONTEXT_SHA256']}",
        f"TASK_SHA256                {record['TASK_SHA256']}",
        f"output schema              {record['OUTPUT_SCHEMA_VERSION']}",
        f"                           {record['OUTPUT_SCHEMA_SHA256']}",
        f"output gate                {record['OUTPUT_GATE_VERSION']}",
        f"subject                    {record['SUBJECT']}",
        f"packet                     {record['PACKET_ID']}",
        "```",
        "",
        f"Regions byte-identical to v1.0.0: {', '.join(record['REGIONS_IDENTICAL_TO_V1_0_0'])}.",
        "",
        "## Semantic diff",
        "",
        f"**Added.** {_sentence(record['SEMANTIC_DIFF']['added'])}",
        "",
        f"**Removed.** {record['SEMANTIC_DIFF']['removed']}.",
        "",
        _sentence(record["SEMANTIC_DIFF"]["note"]),
        "",
        f"Research semantics changed: {record['SEMANTIC_DIFF']['research_semantics_changed']}. "
        f"Evidence semantics changed: {record['SEMANTIC_DIFF']['evidence_semantics_changed']}. "
        f"Refusal semantics changed: {record['SEMANTIC_DIFF']['refusal_semantics_changed']}.",
        "",
        "## The untrusted region",
        "",
        f"{record['INPUT_PLACEHOLDER']['count']} pairs, "
        f"{_sentence(record['INPUT_PLACEHOLDER']['note'])}",
        "",
        f"**TED representation `{record['TED_REPRESENTATION_SHA256']}`, unchanged.**",
        "",
        f"**SENT: {record['SENT']}.** {_sentence(record['sent_note'])}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        decision, capacity, prompt = validate()
    except ValidationError as error:
        print(f"REFUSED  second opportunity bounded contract: {error}")
        return 1

    rendered = (
        (DECISION_MD, render_decision(decision)),
        (CAPACITY_MD, render_capacity(capacity)),
        (PROMPT_MD, render_prompt(prompt)),
    )
    if args.check:
        for path, text in rendered:
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print("ok       the bounded output contract matches the live schema and its own records")
        return 0
    for path, text in rendered:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {capacity['PRIMARY_OUTCOME']}")
    print(
        f"schema   {capacity['schema_id']} FINITE_BOUND={capacity['FINITE_BOUND']}, "
        f"{capacity['unbounded_path_count']} unbounded"
    )
    print(
        f"maximum  {capacity['MAXIMUM_VALID_INSTANCE']['MAX_VALID_OUTPUT_CHARACTERS']} characters, "
        f"{capacity['MAXIMUM_VALID_INSTANCE']['MAX_VALID_OUTPUT_UTF8_BYTES']} bytes"
    )
    print(
        f"ceiling  DERIVED={capacity['DERIVED_MIN_OUTPUT_TOKEN_CAPACITY']}, "
        f"SELECTED={capacity['SELECTED_MAX_OUTPUT_TOKENS']}, "
        f"V2={capacity['EXECUTION_PACKET_V2_CREATED']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
