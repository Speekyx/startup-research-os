"""Render and validate the second-Opportunity output-capacity analysis (Mission 1.84.3).

The question was what output-token ceiling the frozen schema justifies. It justifies none: eight
required paths are unbounded, so no maximum exists to derive one from. The temptation a record of
that invites is a number anyway, so the gate **re-derives boundedness from the live schema** rather
than believing the record, and refuses:

    A CEILING THAT WAS NOT DERIVED. While the schema is unbounded, `SELECTED_MAX_OUTPUT_TOKENS` is
    NONE and `DERIVED_MIN_OUTPUT_TOKEN_CAPACITY` is NOT_DERIVABLE. A number in either is refused.

    A FINITE CLAIM THE SCHEMA DOES NOT SUPPORT. The gate walks the executable schema itself. A
    record claiming a finite bound while an unbounded path exists is refused, and so is one
    claiming unboundedness the schema does not have.

    A SCHEMA EDITED TO RESCUE CAPACITY. Twenty required fields, `confidence_classification` still
    required, `statement_classifications` still maxItems 24 with statement maxLength 300, and the
    record's own not-done flags all false.

    A FLOOR PRESENTED AS A MAXIMUM. The bounded-subset floor is labelled a floor, holds the
    unbounded arrays empty, and is never called the schema maximum.

    AN EMPIRICAL RATIO TREATED AS A TOKENIZER. The exact count stays NOT_ESTABLISHED and the
    direction warning stays recorded, because a characters-per-token ratio that is too high
    underestimates tokens.

    A V2 PACKET. None may exist while the schema is unbounded, and V1 stays consumed and
    byte-identical.

    A CALL. Model calls, provider requests, network requests and TED bytes are all zero.

    uv run python infrastructure/scripts/render_second_opportunity_output_capacity.py
    uv run python infrastructure/scripts/render_second_opportunity_output_capacity.py --check

Deterministic from repository files and the installed packages, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

from sros_opportunity import (
    SECOND_OPPORTUNITY_GATE_VERSION,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION,
    SYNTHESIS_OUTPUT_SCHEMA,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

ANALYSIS = DATA / "second-opportunity-output-capacity-analysis-v1.json"
ANALYSIS_MD = DATA / "second-opportunity-output-capacity-analysis-v1.md"
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
PACKET_V2 = DATA / "second-opportunity-synthesis-execution-packet-v2.json"
EXECUTION_RECORD = DATA / "second-opportunity-synthesis-execution-record-v1.json"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
PROMPT_SHA256 = "af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080"

ZERO_ACCOUNTING = (
    "MODEL_CALLS",
    "PROVIDER_REQUESTS",
    "REMOTE_TEST_CALLS",
    "TED_BYTES_SENT",
    "CANONICAL_RESEARCH_MUTATION",
    "OPPORTUNITIES_CREATED",
    "SCORES_PERSISTED",
    "EMBEDDINGS_CREATED",
    "SCHEMA_CHANGES",
    "NETWORK_REQUESTS",
)

ACCEPTABLE_OUTCOMES = (
    "SECOND_OPPORTUNITY_EXECUTION_PACKET_V2_READY_FOR_OPERATOR_APPROVAL",
    "OUTPUT_SCHEMA_HAS_UNBOUNDED_SERIALIZED_SIZE",
    "OUTPUT_CONTRACT_CAPACITY_REQUIRES_ARCHITECTURE_DECISION",
    "RETENTION_PATH_NOT_READY_FOR_SECOND_EXECUTION",
    "APPROVED_TED_EGRESS_REPRESENTATION_CHANGED",
    "SECOND_OPPORTUNITY_PROMPT_CHANGED",
    "MODEL_SELECTION_CHANGED_REQUIRES_OPERATOR_REVIEW",
    "MODEL_COST_BASIS_REQUIRES_REFRESH",
    "PROVIDER_ROUTE_NO_LONGER_APPROVED",
    "TED_EGRESS_NO_LONGER_AVAILABLE",
)


class ValidationError(RuntimeError):
    """The record disagrees with the live schema, with the frozen packet, or with itself."""


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def unbounded_paths(schema: dict) -> list[str]:
    """Re-derive the unbounded paths from the EXECUTABLE schema.

    The record is not believed about the one fact that decides the mission. A gate that read
    `FINITE_BOUND` out of the document it guards would be checking that somebody typed a boolean.
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


def _check_the_boundedness(record: dict) -> list[str]:
    live = unbounded_paths(SECOND_OPPORTUNITY_OUTPUT_SCHEMA)
    finite = not live
    if bool(record["FINITE_BOUND"]) != finite:
        raise ValidationError(
            f"the record says FINITE_BOUND={record['FINITE_BOUND']} and the live schema has "
            f"{len(live)} unbounded path(s): {live}"
        )
    recorded = sorted(item["path"] for item in record["unbounded_paths"])
    if recorded != live:
        raise ValidationError(
            f"the recorded unbounded paths {recorded} are not the live schema's {live}"
        )
    if int(record["unbounded_path_count"]) != len(live):
        raise ValidationError("the recorded count is not the number of paths listed")
    return live


def _check_no_ceiling_was_invented(record: dict, finite: bool) -> None:
    if finite:
        return
    if record["SCHEMA_MAX_SERIALIZED_SIZE"] != "UNBOUNDED":
        raise ValidationError(
            f"a maximum serialized size of {record['SCHEMA_MAX_SERIALIZED_SIZE']!r} for a schema "
            "that has none"
        )
    # noqa S105: the flagged "token" is a model output-token count, not a credential.
    if record["DERIVED_MIN_OUTPUT_TOKEN_CAPACITY"] != "NOT_DERIVABLE":  # noqa: S105
        raise ValidationError(
            f"a derived capacity of {record['DERIVED_MIN_OUTPUT_TOKEN_CAPACITY']!r} from an "
            "unbounded schema"
        )
    if record["SELECTED_MAX_OUTPUT_TOKENS"] != "NONE":
        raise ValidationError(
            f"MAX_OUTPUT_TOKENS {record['SELECTED_MAX_OUTPUT_TOKENS']!r} was selected from an "
            "unbounded schema, which means it was invented rather than derived"
        )
    tokens = record["TOKENIZATION"]
    if tokens["EXACT_MAX_OUTPUT_TOKEN_COUNT"] != "NOT_ESTABLISHED":  # noqa: S105
        raise ValidationError("an exact token count for a schema with no maximum")
    if tokens["exact_tokenizer_available"]:
        raise ValidationError("an exact tokenizer is claimed; then the count must be exact")
    if tokens["empirical_ratio_classification"] != "EMPIRICAL_LOWER_INFORMATION_BOUND":
        raise ValidationError("the empirical ratio is not classified as one")
    if "UNDERESTIMATES" not in tokens["empirical_ratio_direction_warning"].upper():
        raise ValidationError(
            "the direction warning does not say that too high a ratio underestimates tokens, "
            "which is the unsafe direction for a capacity ceiling"
        )
    if not tokens["no_ceiling_derived"]:
        raise ValidationError("a ceiling is recorded as derived")
    if record["PROVIDER_OUTPUT_TOKEN_LIMIT"] not in ("NOT_READ", "NOT_ESTABLISHED"):
        raise ValidationError(
            "a provider output limit is recorded while the schema is unbounded, which invites it "
            "being read as a schema bound"
        )


def _check_the_floor_is_a_floor(record: dict) -> None:
    floor = record["BOUNDED_SUBSET_FLOOR"]
    if floor["FLOOR_SERIALIZED_CHARACTERS"] <= 0:
        raise ValidationError("a floor of zero characters")
    if not floor["worst_case_escaping_applied"]:
        raise ValidationError(
            "the floor ignores JSON escaping, which understates it: a quotation mark serialises "
            "to two characters"
        )
    if "NOT the schema maximum" not in floor["$comment"]:
        raise ValidationError("the floor does not say it is not the maximum")
    if not floor["floor_exceeds_frozen_cap"]:
        raise ValidationError("the floor is recorded as fitting inside the frozen cap")
    if floor["frozen_cap_it_is_compared_against"] != 3000:
        raise ValidationError("the floor is compared against a cap that is not the frozen one")
    if "NOT an output tokenizer" not in floor["directional_token_note"]:
        raise ValidationError(
            "the floor's token note does not disclaim the input-measured ratio as a tokenizer"
        )
    dominant = record["DOMINANT_FIELDS_BY_SERIALIZED_SIZE"]
    if not dominant or dominant[0]["serialized_characters"] <= 0:
        raise ValidationError("no dominant field recorded")
    if dominant != sorted(dominant, key=lambda c: -c["serialized_characters"]):
        raise ValidationError("the dominant fields are not ordered by size")


def _check_the_schema_was_not_edited(record: dict) -> None:
    required = list(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"])
    if len(required) != 20:
        raise ValidationError(f"the live schema requires {len(required)} fields, not 20")
    for field in ("confidence_classification", "statement_classifications"):
        if field not in required:
            raise ValidationError(f"{field} is no longer required")
    sc = SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"]["statement_classifications"]
    if sc["maxItems"] != 24:
        raise ValidationError(
            f"statement_classifications maxItems is {sc['maxItems']}; reducing it to rescue "
            "capacity is the move section 19 forbids"
        )
    if sc["items"]["properties"]["statement"]["maxLength"] != 300:
        raise ValidationError("the statement maxLength moved")
    if record["schema_id"] != SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION:
        raise ValidationError("the record names a schema version the code does not carry")
    if record["output_gate"] != SECOND_OPPORTUNITY_GATE_VERSION:
        raise ValidationError("the record names a gate version the code does not carry")
    if record["schema_changed_by_this_mission"]:
        raise ValidationError("the schema was changed by a capacity-derivation mission")
    for key, value in record["THINGS_NOT_DONE"].items():
        if key.startswith("$") or key == "note":
            continue
        if value:
            raise ValidationError(f"§19: {key} is true")


def _check_the_provenance(record: dict) -> None:
    base = set(SYNTHESIS_OUTPUT_SCHEMA["required"])
    provenance = record["PROVENANCE"]
    added = sorted(set(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"]) - base)
    if sorted(provenance["fields_added_by_mission_1_84"]) != added:
        raise ValidationError(
            f"the record says 1.84 added {provenance['fields_added_by_mission_1_84']} and the "
            f"schemas say {added}"
        )
    for item in record["unbounded_paths"]:
        field = item["path"].split("[")[0]
        expected = "MISSION_1_31_BASE_SCHEMA" if field in base else "MISSION_1_84"
        if item["introduced_by"] != expected:
            raise ValidationError(
                f"{field} is attributed to {item['introduced_by']} and the base schema says "
                f"{expected}"
            )
    if not str(provenance["corrected_attribution"]).strip():
        raise ValidationError("a corrected attribution with nothing in it")


def _check_nothing_moved(record: dict) -> None:
    revalidation = record["REVALIDATION"]
    if revalidation["representation_sha256_recomputed"] != REPRESENTATION_SHA256:
        raise ValidationError("the representation digest moved")
    if revalidation["prompt_sha256_recomputed"] != PROMPT_SHA256:
        raise ValidationError("the prompt digest moved")
    if not revalidation["representation_unchanged"] or not revalidation["prompt_unchanged"]:
        raise ValidationError("the record says the payload changed")
    if revalidation["provider_posture"] != "APPROVED":
        raise ValidationError("the provider route is no longer APPROVED")
    if revalidation["subscription_route_used"]:
        raise ValidationError("the subscription route was used")
    if revalidation["ted_external_model_transmission"] != "PERMITTED_WITH_CONDITIONS":
        raise ValidationError("TED egress moved")
    if revalidation["selected_packet_gate"] != "AVAILABLE":
        raise ValidationError("the selected packet gate moved")
    if revalidation["model_selection_changed"]:
        raise ValidationError("§26: the model changed; that is an operator review, not a repair")
    if revalidation["pricing_changed"]:
        raise ValidationError("§27: the pricing basis changed")

    if not record["RETENTION_REPAIR_VERIFIED"]:
        raise ValidationError("§20: the retention repair is unverified")
    if not str(record["retention_repair_evidence"]).strip():
        raise ValidationError("a retention verification with no evidence")


def _check_v1_and_v2(record: dict) -> None:
    packet = _load(PACKET_V1)
    state = record["V1_STATE"]
    if packet["EXECUTION_PACKET_SHA256"] != V1_SHA256:
        raise ValidationError("the frozen V1 packet has been edited")
    if packet["MAX_OUTPUT_TOKENS"] != 3000:
        raise ValidationError("V1's MAX_OUTPUT_TOKENS was raised in place")
    if packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"]:
        raise ValidationError("V1 was marked approved")
    if state["execution_packet_sha256"] != V1_SHA256 or not state["unchanged"]:
        raise ValidationError("the record disagrees about V1")
    if not state["EXECUTION_APPROVAL_CONSUMED"] or state["FURTHER_CALLS_AUTHORIZED_BY_V1"]:
        raise ValidationError("the consumed approval was reset")
    if not state["guard_still_refuses_v1"]:
        raise ValidationError("§21: the guard no longer refuses V1")
    if not state["guard_permits_a_new_digest"]:
        raise ValidationError(
            "§21: the guard refuses every digest, which would block the successor packet too"
        )
    consumed = _load(EXECUTION_RECORD)
    if not consumed["EXECUTION_APPROVAL_CONSUMED"]:
        raise ValidationError("the historical execution record no longer says V1 was consumed")

    created = record["EXECUTION_PACKET_V2_CREATED"]
    if created and not PACKET_V2.exists():
        raise ValidationError("the record claims a V2 packet that is not on disk")
    if not created and PACKET_V2.exists():
        raise ValidationError("a V2 packet exists that the record says was not created")
    if created and record["PRIMARY_OUTCOME"] == "OUTPUT_SCHEMA_HAS_UNBOUNDED_SERIALIZED_SIZE":
        raise ValidationError(
            "a V2 packet was created from an unbounded schema, so its MAX_OUTPUT_TOKENS was "
            "invented"
        )
    if not created and not str(record["why_no_v2"]).strip():
        raise ValidationError("no V2 and no stated reason")


def _check_the_options(record: dict) -> None:
    options = record["OPTIONS_FOR_THE_OPERATOR"]
    if options["implemented_here"] != "NONE":
        raise ValidationError("§18: an architecture option was implemented")
    if options["recommended_here"] != "NONE":
        raise ValidationError(
            "§18: an option is recommended as though decided. Options are offered and the choice "
            "is the operator's"
        )
    if len(options["options"]) < 2:
        raise ValidationError("fewer than two options offered")
    for option in options["options"]:
        for key in ("id", "what", "cost"):
            if not str(option.get(key) or "").strip():
                raise ValidationError(f"an option missing {key}")
        if "makes_the_schema_finite" not in option:
            raise ValidationError(
                f"option {option['id']} does not say whether it makes the schema finite, which is "
                "the only question that decides whether a ceiling becomes derivable"
            )


def _check_the_accounting(record: dict) -> None:
    accounting = record["ACCOUNTING"]
    for key in ZERO_ACCOUNTING:
        if accounting[key] != 0:
            raise ValidationError(f"{key} is {accounting[key]}, and this mission spends 0")
    if accounting["DEPENDENCIES_INSTALLED"] != 0:
        raise ValidationError(
            "§15: a dependency was installed, which is how a convenient tokenizer number arrives"
        )


def validate() -> dict:
    record = _load(ANALYSIS)

    if record["PRIMARY_OUTCOME"] not in ACCEPTABLE_OUTCOMES:
        raise ValidationError(f"outcome {record['PRIMARY_OUTCOME']!r}")
    if not str(record["outcome_basis"]).strip():
        raise ValidationError("an outcome with no stated basis")

    live = _check_the_boundedness(record)
    _check_no_ceiling_was_invented(record, finite=not live)
    _check_the_floor_is_a_floor(record)
    _check_the_schema_was_not_edited(record)
    _check_the_provenance(record)
    _check_nothing_moved(record)
    _check_v1_and_v2(record)
    _check_the_options(record)
    _check_the_accounting(record)

    if live and record["PRIMARY_OUTCOME"] != "OUTPUT_SCHEMA_HAS_UNBOUNDED_SERIALIZED_SIZE":
        raise ValidationError(
            f"the schema has {len(live)} unbounded path(s) and the outcome is "
            f"{record['PRIMARY_OUTCOME']!r}; section 6 makes that a hard stop"
        )
    return record


def _sentence(text: str) -> str:
    return str(text).rstrip().rstrip(".") + "."


def render(record: dict) -> str:
    floor = record["BOUNDED_SUBSET_FLOOR"]
    tokens = record["TOKENIZATION"]
    provenance = record["PROVENANCE"]
    revalidation = record["REVALIDATION"]
    v1 = record["V1_STATE"]

    lines = [
        "# Second Opportunity output capacity analysis",
        "",
        "Generated from `second-opportunity-output-capacity-analysis-v1.json`. "
        "Do not edit by hand.",
        "",
        f"**{record['PRIMARY_OUTCOME']}**",
        "",
        record["$comment"],
        "",
        _sentence(record["outcome_basis"]),
        "",
        "## The gate that stops the arithmetic",
        "",
        f"- schema `{record['schema_id']}`, digest `{record['schema_sha256']}`",
        f"- **FINITE_BOUND = {record['FINITE_BOUND']}**",
        f"- unbounded required paths: **{record['unbounded_path_count']}**",
        f"- **SCHEMA_MAX_SERIALIZED_SIZE = {record['SCHEMA_MAX_SERIALIZED_SIZE']}**",
        "",
        "| path | maxItems | item maxLength | introduced by |",
        "|---|---|---|---|",
    ]
    for item in record["unbounded_paths"]:
        lines.append(
            f"| `{item['path']}` | {item['maxItems']} | **none** | {item['introduced_by']} |"
        )
    lines += [
        "",
        "## Whose schema this is",
        "",
        f"All eight unbounded fields come from **{provenance['all_eight_unbounded_fields_are_from']}**, "
        f"byte-identical: {provenance['byte_identical_to_base']}.",
        "",
        "Fields Mission 1.84 added: "
        + ", ".join(f"`{f}`" for f in provenance["fields_added_by_mission_1_84"])
        + f" — all bounded: **{provenance['fields_added_by_mission_1_84_are_all_bounded']}**.",
        "",
        _sentence(provenance["corrected_attribution"]),
        "",
        "## A floor, which is not a maximum",
        "",
        floor["$comment"],
        "",
        f"- **FLOOR_SERIALIZED_CHARACTERS = {floor['FLOOR_SERIALIZED_CHARACTERS']}**",
        f"- FLOOR_UTF8_BYTES = {floor['FLOOR_UTF8_BYTES']}",
        f"- digest `{floor['FLOOR_INSTANCE_SHA256']}`",
        f"- exceeds the frozen cap of {floor['frozen_cap_it_is_compared_against']}: "
        f"**{floor['floor_exceeds_frozen_cap']}**",
        "",
        _sentence(floor["method"]),
        "",
        _sentence(floor["escaping_note"]),
        "",
        _sentence(floor["directional_token_note"]),
        "",
        "### Dominant fields",
        "",
        "| field | serialized characters | bounded |",
        "|---|---|---|",
    ]
    for entry in record["DOMINANT_FIELDS_BY_SERIALIZED_SIZE"]:
        lines.append(
            f"| `{entry['field']}` | {entry['serialized_characters']} | {entry['bounded']} |"
        )
    lines += [
        "",
        _sentence(record["dominant_field_note"]),
        "",
        "## Tokens",
        "",
        f"- **EXACT_MAX_OUTPUT_TOKEN_COUNT = {tokens['EXACT_MAX_OUTPUT_TOKEN_COUNT']}**",
        f"- exact tokenizer available: {tokens['exact_tokenizer_available']}",
        f"- empirical ratio: {tokens['empirical_ratio_available']}, classified "
        f"`{tokens['empirical_ratio_classification']}`",
        "",
        _sentence(tokens["why"]),
        "",
        _sentence(tokens["empirical_ratio_direction_warning"]),
        "",
        f"**DERIVED_MIN_OUTPUT_TOKEN_CAPACITY = {record['DERIVED_MIN_OUTPUT_TOKEN_CAPACITY']}**. "
        f"**SELECTED_MAX_OUTPUT_TOKENS = {record['SELECTED_MAX_OUTPUT_TOKENS']}**.",
        "",
        "## What was not done",
        "",
        _sentence(record["THINGS_NOT_DONE"]["note"]),
        "",
        "## Options, none implemented and none recommended",
        "",
        record["OPTIONS_FOR_THE_OPERATOR"]["$comment"],
        "",
        "| option | what | makes the schema finite | cost |",
        "|---|---|---|---|",
    ]
    for option in record["OPTIONS_FOR_THE_OPERATOR"]["options"]:
        lines.append(
            f"| `{option['id']}` | {option['what']} | "
            f"**{option['makes_the_schema_finite']}** | {option['cost']} |"
        )
    lines += [
        "",
        "## Nothing else moved",
        "",
        f"- representation `{revalidation['representation_sha256_recomputed']}` "
        f"({revalidation['representation_characters']} characters), unchanged",
        f"- prompt `{revalidation['prompt_sha256_recomputed']}`, unchanged",
        f"- provider `{revalidation['provider_id']}`, posture "
        f"**{revalidation['provider_posture']}**",
        f"- subscription route posture {revalidation['subscription_route_posture']}, used "
        f"{revalidation['subscription_route_used']}",
        f"- model `{revalidation['model_selected_by_current_policy']}`, selection changed "
        f"{revalidation['model_selection_changed']}",
        f"- pricing `{revalidation['pricing_version']}`, changed {revalidation['pricing_changed']}",
        f"- TED transmission {revalidation['ted_external_model_transmission']}, packet gate "
        f"{revalidation['selected_packet_gate']}",
        "",
        _sentence(revalidation["model_selection_note"]),
        "",
        f"**RETENTION_REPAIR_VERIFIED = {record['RETENTION_REPAIR_VERIFIED']}.** "
        f"{_sentence(record['retention_repair_evidence'])}",
        "",
        "## V1 and V2",
        "",
        f"- V1 `{v1['execution_packet_sha256']}`, unchanged {v1['unchanged']}",
        f"- **EXECUTION_APPROVAL_CONSUMED = {v1['EXECUTION_APPROVAL_CONSUMED']}**, further calls "
        f"{v1['FURTHER_CALLS_AUTHORIZED_BY_V1']}",
        f"- guard refuses V1: {v1['guard_still_refuses_v1']} (`{v1['guard_refusal_code']}`), "
        f"permits a new digest: {v1['guard_permits_a_new_digest']}",
        f"- **EXECUTION_PACKET_V2_CREATED = {record['EXECUTION_PACKET_V2_CREATED']}**",
        "",
        _sentence(record["why_no_v2"]),
        "",
        "## Accounting",
        "",
        "| counter | value |",
        "|---|---|",
    ]
    for key, value in record["ACCOUNTING"].items():
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        f"**Next: {record['NEXT_REQUIRED_ACTION']}.** {_sentence(record['next_action_note'])}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        record = validate()
    except ValidationError as error:
        print(f"REFUSED  second opportunity output capacity: {error}")
        return 1
    text = render(record)
    if args.check:
        if not ANALYSIS_MD.exists():
            print(f"DRIFT    {ANALYSIS_MD.name} does not exist")
            return 1
        if ANALYSIS_MD.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {ANALYSIS_MD.name} does not match its record")
            return 1
        print("ok       the output-capacity analysis matches the live schema and its own record")
        return 0
    ANALYSIS_MD.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {ANALYSIS_MD.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['PRIMARY_OUTCOME']}")
    print(
        f"schema   FINITE_BOUND={record['FINITE_BOUND']}, "
        f"{record['unbounded_path_count']} unbounded required path(s)"
    )
    print(
        f"ceiling  DERIVED={record['DERIVED_MIN_OUTPUT_TOKEN_CAPACITY']}, "
        f"SELECTED={record['SELECTED_MAX_OUTPUT_TOKENS']}, V2="
        f"{record['EXECUTION_PACKET_V2_CREATED']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
