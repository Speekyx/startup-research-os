"""Render and validate the second-Opportunity execution record (Mission 1.84.2).

One approved provider request happened and its output was rejected. What a record of that invites
is a quiet upgrade: an unused approval, an estimated cost presented as measured, a reconstructed
response, a schema loosened until the failed answer fits. The gate refuses:

    AN APPROVAL RECOVERED FROM A FAILURE. A failed call spends an approval exactly as a
    successful one does. `EXECUTION_APPROVAL_CONSUMED` is true, further calls under V1 are false,
    and the consumed-approval entry names the digest with its request count.

    A FROZEN PACKET EDITED. V1 keeps its digest and its own approval flag stays false, because an
    approval and the fact that it was spent both live beside the document, never inside it.

    AN OUTPUT CONTRACT LOOSENED TO RESCUE THE RESPONSE. The schema keeps 20 required fields,
    `confidence_classification` stays required, `statement_classifications` keeps its maxItems,
    and the failed response stays invalid.

    A MEASUREMENT NOBODY MADE. The raw response is NOT_AVAILABLE rather than reconstructed, token
    usage and cost are NOT_ESTABLISHED rather than estimated, and the frozen worst case is never
    recorded as the actual cost.

    A CAUSE PROMOTED TO A FACT. The capacity hypothesis is STRONGLY_SUPPORTED and the root cause
    is NOT_PROVABLE_FROM_RETAINED_EXECUTION_ARTIFACTS. Claiming truncation is refused.

    A DEFECT ERASED. Both retention shortfalls stay recorded, with their reasons.

    A SECOND CALL. The closure itself made none, and the record's own counters say so.

    uv run python infrastructure/scripts/render_second_opportunity_execution_record.py
    uv run python infrastructure/scripts/render_second_opportunity_execution_record.py --check

Deterministic from repository files and the installed packages, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

from sros_opportunity import (
    SECOND_OPPORTUNITY_GATE_VERSION,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

RECORD = DATA / "second-opportunity-synthesis-execution-record-v1.json"
RECORD_MD = DATA / "second-opportunity-synthesis-execution-record-v1.md"
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
RUNNER = ROOT / "infrastructure" / "scripts" / "run_second_opportunity_execution.py"

V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
PROMPT_SHA256 = "af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080"

MISSING_FIELDS = ("confidence_classification", "statement_classifications")

#: Section 19. What the CLOSURE spent, which is different from what the consumed call spent.
ZERO_DURING_CLOSURE = (
    "ADDITIONAL_PROVIDER_REQUESTS_DURING_FAILURE_CLOSURE",
    "REMOTE_TEST_CALLS_DURING_CLOSURE",
    "MODEL_CALLS_DURING_CLOSURE",
    "TED_BYTES_SENT_DURING_CLOSURE",
    "CANONICAL_RESEARCH_MUTATION",
    "CREDENTIAL_VALUES_PRINTED_OR_PERSISTED",
)

#: Section 6 and 7. Absences that must stay absences.
NOT_ESTABLISHED_KEYS = (
    "ACTUAL_INPUT_TOKENS",
    "ACTUAL_OUTPUT_TOKENS",
    "ACTUAL_TOTAL_TOKENS",
    "ACTUAL_EXECUTION_COST",
)

SECRET_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"\bey[JI][A-Za-z0-9_\-]{20,}\."),
)


class ValidationError(RuntimeError):
    """The record disagrees with the frozen packet, with the code, or with itself."""


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_the_approval_is_spent(record: dict) -> None:
    if not record["EXECUTION_APPROVAL_CONSUMED"]:
        raise ValidationError(
            "the approval is recorded as unconsumed after a provider request was made. A failed "
            "call spends an approval exactly as a successful one does"
        )
    if record["FURTHER_CALLS_AUTHORIZED_BY_V1"]:
        raise ValidationError("V1 is recorded as still authorising calls")
    if record["future_retry_authorized"]:
        raise ValidationError("a retry is recorded as authorised")
    if int(record["actual_provider_requests"]) != 1:
        raise ValidationError(
            f"{record['actual_provider_requests']} provider requests recorded; the approval "
            "authorised exactly one"
        )
    if int(record["retries"]) != 0 or record["RETRY_OCCURRED"]:
        raise ValidationError("a retry is recorded")
    if (
        record["second_call_made"]
        or record["fallback_model_used"]
        or record["fallback_provider_used"]
    ):
        raise ValidationError("a second call, a fallback model or a fallback provider")

    consumed = record["CONSUMED_APPROVALS"]
    if not consumed:
        raise ValidationError(
            "no consumed-approval entry, so the one-call guard has nothing to read and the "
            "refusal would depend on somebody remembering"
        )
    entry = next((e for e in consumed if e["execution_packet_sha256"] == V1_SHA256), None)
    if entry is None:
        raise ValidationError("the consumed-approval list does not name V1's digest")
    if int(entry["provider_requests"]) < 1:
        raise ValidationError("a consumed approval with no request against it")
    if record["next_required_action"] != "NEW_EXECUTION_PACKET_AND_NEW_OPERATOR_APPROVAL":
        raise ValidationError("the next action does not require a new packet and a new approval")
    if "digest" not in record["why_a_new_packet_is_required"]:
        raise ValidationError(
            "the record does not say that MAX_OUTPUT_TOKENS is a digest-bound field, which is why "
            "the approved packet cannot simply be re-run with a larger cap"
        )


def _check_the_frozen_packet(record: dict, packet: dict) -> None:
    if record["execution_packet_sha256"] != V1_SHA256:
        raise ValidationError("the record names a digest that is not V1's")
    if packet["EXECUTION_PACKET_SHA256"] != V1_SHA256:
        raise ValidationError("the frozen V1 packet on disk has been edited")
    if packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"]:
        raise ValidationError(
            "the frozen packet was edited to record its own approval or its own use, so its bytes "
            "are no longer the bytes that were approved"
        )
    if not record["execution_packet_unchanged"]:
        raise ValidationError("the record says the frozen packet changed")
    if record["operator_approval"]["recorded_inside_the_packet"]:
        raise ValidationError("an approval recorded inside the document it approves")
    if packet["MAX_OUTPUT_TOKENS"] != 3000:
        raise ValidationError(
            "V1's MAX_OUTPUT_TOKENS moved. A new ceiling belongs in a NEW packet with a new "
            "digest, not in the one that was approved"
        )
    if record["representation_sha256"] != REPRESENTATION_SHA256:
        raise ValidationError("the representation digest moved")
    if record["prompt_sha256"] != PROMPT_SHA256:
        raise ValidationError("the prompt digest moved")
    if packet["REPRESENTATION_SHA256"] != REPRESENTATION_SHA256:
        raise ValidationError("the frozen packet's representation digest moved")
    if packet["PROMPT_SHA256"] != PROMPT_SHA256:
        raise ValidationError("the frozen packet's prompt digest moved")


def _check_the_output_contract(record: dict) -> None:
    unchanged = record["output_contract_unchanged"]
    if unchanged["output_schema_version"] != SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION:
        raise ValidationError("the record names a schema version the code does not carry")
    if unchanged["output_gate_version"] != SECOND_OPPORTUNITY_GATE_VERSION:
        raise ValidationError("the record names a gate version the code does not carry")
    for key in (
        "required_fields_changed",
        "statement_classifications_maxitems_changed",
        "confidence_classification_removed",
        "fields_reordered",
        "defaults_invented_for_missing_fields",
    ):
        if unchanged[key]:
            raise ValidationError(f"§10: {key} is true, which rescues the failed response")
    if not unchanged["failed_response_remains_invalid"]:
        raise ValidationError("the failed response is recorded as valid")

    required = list(SECOND_OPPORTUNITY_OUTPUT_SCHEMA["required"])
    if len(required) != int(record["required_field_count"]):
        raise ValidationError(
            f"the live schema requires {len(required)} fields and the record says "
            f"{record['required_field_count']}"
        )
    for field in MISSING_FIELDS:
        if field not in required:
            raise ValidationError(
                f"{field} is no longer required, so the failed response would now pass. The "
                "contract is not edited to rescue a rejected answer"
            )
    if list(record["missing_fields"]) != list(MISSING_FIELDS):
        raise ValidationError("the recorded missing fields are not the ones the validator named")
    if int(record["present_field_count"]) >= int(record["required_field_count"]):
        raise ValidationError("the record claims every required field was present")
    maxitems = SECOND_OPPORTUNITY_OUTPUT_SCHEMA["properties"]["statement_classifications"][
        "maxItems"
    ]
    if maxitems != 24:
        raise ValidationError(
            f"statement_classifications maxItems is {maxitems}; changing it is a contract change "
            "that belongs to a mission with an ADR behind it"
        )


def _check_the_validation_verdict(record: dict) -> None:
    if record["validation_result"] != "REJECTED":
        raise ValidationError("the output is not recorded as rejected")
    if record["failed_stage"] != "4_schema_validation":
        raise ValidationError(f"failed stage {record['failed_stage']!r}")
    stages = record["VALIDATION_STAGES"]
    if stages["4_schema_validation"] != "FAILED":
        raise ValidationError("stage 4 is not recorded as failed")
    for stage in (
        "5_semantic_output_gate",
        "6_evidence_boundary_gate",
        "7_attribution_and_no_distortion_gate",
        "8_canonical_persistence_eligibility",
    ):
        if stages[stage] != "NOT_REACHED":
            raise ValidationError(
                f"{stage} is recorded as {stages[stage]}; a stage that never ran is NOT_REACHED "
                "rather than passing"
            )
    if record["transport_result"] != "SUCCESS":
        raise ValidationError(
            "the transport is not recorded as having succeeded, which would misdescribe a "
            "rejected output as a provider failure"
        )


def _check_the_absences(record: dict) -> None:
    if record["RAW_PROVIDER_RESPONSE_RETAINED"]:
        raise ValidationError(
            "the raw response is recorded as retained. It was not, and recording otherwise would "
            "invite somebody to look for it"
        )
    if record["RAW_PROVIDER_RESPONSE_HASH"] != "NOT_AVAILABLE":
        raise ValidationError(
            "a hash for a response nobody kept. A reconstructed artifact reads exactly like a "
            "retained one"
        )
    if record["RAW_PROVIDER_RESPONSE_RECOVERABLE"]:
        raise ValidationError("the raw response is recorded as recoverable")
    if not record["raw_response_not_reconstructed"]:
        raise ValidationError("the raw response was reconstructed")
    if record["USAGE_RETAINED"]:
        raise ValidationError("usage is recorded as retained; it was not")
    for key in NOT_ESTABLISHED_KEYS:
        if record[key] != "NOT_ESTABLISHED":
            raise ValidationError(
                f"{key} is {record[key]!r}. An estimate labelled actual is the failure this field "
                "exists to prevent"
            )
    if record["APPROVED_WORST_CASE_CALL_COST"] != 0.04825:
        raise ValidationError("the frozen worst case moved")
    if record["ACTUAL_EXECUTION_COST"] == record["APPROVED_WORST_CASE_CALL_COST"]:
        raise ValidationError("the worst case is recorded as the actual cost")
    if "ACTUAL_COST_UNKNOWN" not in record["cost_statement"]:
        raise ValidationError("the cost statement does not say the actual cost is unknown")
    for key in ("raw_response_defect", "usage_defect"):
        if not str(record[key]).strip():
            raise ValidationError(f"§18: {key} was erased")


def _check_the_cause(record: dict) -> None:
    if record["OUTPUT_CAPACITY_FAILURE_HYPOTHESIS"] != "STRONGLY_SUPPORTED":
        raise ValidationError(
            f"the hypothesis is recorded as {record['OUTPUT_CAPACITY_FAILURE_HYPOTHESIS']!r}. "
            "ESTABLISHED needs the raw bytes and the output token count, and neither was kept"
        )
    if record["ROOT_CAUSE"] != "NOT_PROVABLE_FROM_RETAINED_EXECUTION_ARTIFACTS":
        raise ValidationError(f"root cause {record['ROOT_CAUSE']!r}")
    if not str(record["why_not_established"]).strip():
        raise ValidationError("a hypothesis with no statement of what would establish it")
    if len(record["hypothesis_evidence"]) < 3:
        raise ValidationError("a strongly-supported hypothesis resting on fewer than three facts")
    if not any("truncation" in claim for claim in record["not_claimed"]):
        raise ValidationError("§8: byte-level truncation is not disclaimed")
    if not record["OUTPUT_CAPACITY_BOUND_NOT_DERIVED_FROM_SCHEMA"]:
        raise ValidationError("§9: the Mission 1.84 defect is not recorded")
    if record["correct_new_output_ceiling_not_concluded_here"] is not True:
        raise ValidationError(
            "§9: this mission concluded a new ceiling. That belongs to Mission 1.84.3"
        )


def _check_nothing_persisted(record: dict) -> None:
    if record["canonical_persistence"]:
        raise ValidationError("canonical persistence is recorded")
    for key, value in record["PERSISTENCE"].items():
        if key == "note":
            continue
        if value != 0:
            raise ValidationError(f"{key} is {value}")
    if not record["HUMAN_OUTPUT_REVIEW_REQUIRED"]:
        raise ValidationError("human output review is recorded as not required")
    if record["human_review_packet_produced"]:
        raise ValidationError(
            "a human-review packet was produced from a response that failed validation"
        )
    accounting = record["ACCOUNTING"]
    if int(accounting["TOTAL_PROVIDER_REQUESTS_FOR_MISSION_1_84_2"]) != 1:
        raise ValidationError("the mission's total provider requests is not 1")
    for key in ZERO_DURING_CLOSURE:
        if accounting[key] != 0:
            raise ValidationError(f"{key} is {accounting[key]}, and the closure spends 0")
    if int(accounting["TED_BYTES_SENT_BY_THE_CONSUMED_CALL"]) != 3604:
        raise ValidationError("the transmitted byte count is not the approved representation's")


def _check_the_repair(record: dict) -> None:
    repaired = record["RUNNER_DEFECTS_REPAIRED"]
    if repaired["repair_exercised_against_a_provider"]:
        raise ValidationError(
            "the repair was tested against a provider; a test call is a second call"
        )
    if len(repaired["repaired"]) < 3:
        raise ValidationError("a repair list with fewer than three entries")
    guard = record["ONE_CALL_GUARD"]
    if guard["depends_on_human_discipline"]:
        raise ValidationError("§13: the guard depends on discipline")
    if guard["frozen_packet_modified_to_achieve_it"]:
        raise ValidationError("§13: the frozen packet was modified to achieve the guard")
    if guard["refusal_code"] != "EXECUTION_APPROVAL_ALREADY_CONSUMED":
        raise ValidationError("the guard's refusal code is not the named one")
    text = RUNNER.read_text(encoding="utf-8")
    if "EXECUTION_APPROVAL_ALREADY_CONSUMED" not in text:
        raise ValidationError("the runner does not carry the refusal the record names")
    if "def refuse_if_consumed" not in text:
        raise ValidationError("the runner has no consumed-approval guard")
    if text.count("gateway.complete(") != 1:
        raise ValidationError(
            f"the runner calls gateway.complete {text.count('gateway.complete(')} times; exactly "
            "one call site is what makes 'no retry' structural rather than careful"
        )


def _check_no_secret(record: dict) -> None:
    blob = json.dumps(record, ensure_ascii=False)
    for pattern in SECRET_PATTERNS:
        if pattern.search(blob):
            raise ValidationError(f"§19: a credential shape matching {pattern.pattern!r}")
    if int(record["ACCOUNTING"]["CREDENTIAL_VALUES_PRINTED_OR_PERSISTED"]) != 0:
        raise ValidationError("a credential value was printed or persisted")


def validate() -> dict:
    record = _load(RECORD)
    packet = _load(PACKET_V1)

    if record["PRIMARY_OUTCOME"] != "SECOND_OPPORTUNITY_EXECUTION_REJECTED_AND_CLOSED_NO_RETRY":
        raise ValidationError(f"outcome {record['PRIMARY_OUTCOME']!r}")
    if not str(record["outcome_basis"]).strip():
        raise ValidationError("an outcome with no stated basis")

    _check_the_approval_is_spent(record)
    _check_the_frozen_packet(record, packet)
    _check_the_output_contract(record)
    _check_the_validation_verdict(record)
    _check_the_absences(record)
    _check_the_cause(record)
    _check_nothing_persisted(record)
    _check_the_repair(record)
    _check_no_secret(record)

    verification = record["PRE_EXECUTION_VERIFICATION"]
    if not verification["not_current_permission"]:
        raise ValidationError(
            "§4: the pre-execution checks are recorded as current permission. They establish why "
            "the HISTORICAL call was authorised and nothing else"
        )
    if verification["3_representation_characters"] != 3604:
        raise ValidationError("the recorded representation size is not the approved one")
    return record


def _sentence(text: str) -> str:
    return str(text).rstrip().rstrip(".") + "."


def render(record: dict) -> str:
    stages = record["VALIDATION_STAGES"]
    accounting = record["ACCOUNTING"]
    guard = record["ONE_CALL_GUARD"]
    lines = [
        "# Second Opportunity synthesis execution record",
        "",
        "Generated from `second-opportunity-synthesis-execution-record-v1.json`. "
        "Do not edit by hand.",
        "",
        f"**{record['PRIMARY_OUTCOME']}**",
        "",
        record["$comment"],
        "",
        _sentence(record["outcome_basis"]),
        "",
        "## The approval, and that it is spent",
        "",
        f"- packet `{record['execution_packet_id']}` v{record['execution_packet_version']}",
        f"- digest `{record['execution_packet_sha256']}`",
        f"- **EXECUTION_APPROVAL_CONSUMED = {record['EXECUTION_APPROVAL_CONSUMED']}**",
        f"- **FURTHER_CALLS_AUTHORIZED_BY_V1 = {record['FURTHER_CALLS_AUTHORIZED_BY_V1']}**",
        f"- frozen packet unchanged: {record['execution_packet_unchanged']}",
        "",
        _sentence(record["approval_consumed_note"]),
        "",
        "## The eight pre-execution checks",
        "",
        "| check | result |",
        "|---|---|",
    ]
    for key, value in record["PRE_EXECUTION_VERIFICATION"].items():
        if key.startswith("$") or key in ("not_current_permission",):
            continue
        lines.append(f"| {key} | `{value}` |")
    lines += [
        "",
        "These establish why the **historical** call was authorised. They are not current "
        "permission for another one.",
        "",
        "## What happened",
        "",
        f"- provider `{record['provider']}`, model `{record['model']}`",
        f"- route {record['route']}",
        f"- provider requests **{record['actual_provider_requests']}**, retries "
        f"**{record['retries']}**",
        f"- transport **{record['transport_result']}**, provider answered "
        f"{record['provider_answered']}",
        f"- validation **{record['validation_result']}** at **{record['failed_stage']}**",
        f"- {record['present_field_count']} of {record['required_field_count']} required fields "
        f"present",
        "",
        "Missing: " + ", ".join(f"`{f}`" for f in record["missing_fields"]) + ".",
        "",
        _sentence(record["missing_field_positions_note"]),
        "",
        "| stage | result |",
        "|---|---|",
    ]
    for key, value in stages.items():
        if key.startswith("$"):
            continue
        lines.append(f"| {key} | **{value}** |")
    lines += [
        "",
        "## What was not retained",
        "",
        f"- `RAW_PROVIDER_RESPONSE_RETAINED` **{record['RAW_PROVIDER_RESPONSE_RETAINED']}**, hash "
        f"`{record['RAW_PROVIDER_RESPONSE_HASH']}`, recoverable "
        f"{record['RAW_PROVIDER_RESPONSE_RECOVERABLE']}",
        f"- `USAGE_RETAINED` **{record['USAGE_RETAINED']}**",
        f"- actual tokens and cost: **{record['ACTUAL_EXECUTION_COST']}**",
        "",
        _sentence(record["raw_response_defect"]),
        "",
        _sentence(record["usage_defect"]),
        "",
        f"`{record['cost_statement']}`. The approved worst case was "
        f"{record['APPROVED_WORST_CASE_CALL_COST']} cost units against a ceiling of "
        f"{record['EXECUTION_COST_CEILING']}. {_sentence(record['worst_case_is_not_actual'])}",
        "",
        "## The cause, and what it is not",
        "",
        f"**OUTPUT_CAPACITY_FAILURE_HYPOTHESIS = {record['OUTPUT_CAPACITY_FAILURE_HYPOTHESIS']}**",
        "",
        f"**ROOT_CAUSE = {record['ROOT_CAUSE']}**",
        "",
        _sentence(record["hypothesis_statement"]),
        "",
    ]
    lines.extend(f"- {_sentence(item)}" for item in record["hypothesis_evidence"])
    lines += [
        "",
        _sentence(record["why_not_established"]),
        "",
        "Not claimed:",
        "",
    ]
    lines.extend(f"- {item}" for item in record["not_claimed"])
    lines += [
        "",
        "## The defect in Mission 1.84",
        "",
        f"**OUTPUT_CAPACITY_BOUND_NOT_DERIVED_FROM_SCHEMA = "
        f"{record['OUTPUT_CAPACITY_BOUND_NOT_DERIVED_FROM_SCHEMA']}**",
        "",
        _sentence(record["historical_defect_in_mission_1_84"]),
        "",
        "## What was repaired, and what was not tested",
        "",
    ]
    lines.extend(f"- {_sentence(item)}" for item in record["RUNNER_DEFECTS_REPAIRED"]["repaired"])
    lines += [
        "",
        f"Exercised against a provider: "
        f"**{record['RUNNER_DEFECTS_REPAIRED']['repair_exercised_against_a_provider']}**. "
        f"Exercised by {record['RUNNER_DEFECTS_REPAIRED']['repair_exercised_by']}.",
        "",
        "## The one-call guard",
        "",
        f"- mechanism: {guard['mechanism']}",
        f"- refusal: `{guard['refusal_code']}`",
        f"- depends on human discipline: **{guard['depends_on_human_discipline']}**",
        f"- frozen packet modified to achieve it: "
        f"**{guard['frozen_packet_modified_to_achieve_it']}**",
        "",
        _sentence(guard["note"]),
        "",
        "## What was persisted",
        "",
        f"**{record['PERSISTENCE']['note']}**",
        "",
        f"`canonical_persistence` {record['canonical_persistence']}, "
        f"HUMAN_OUTPUT_REVIEW_REQUIRED {record['HUMAN_OUTPUT_REVIEW_REQUIRED']}, "
        f"review packet produced {record['human_review_packet_produced']}.",
        "",
        _sentence(record["human_review_packet_note"]),
        "",
        "## Accounting",
        "",
        "| counter | value |",
        "|---|---|",
    ]
    for key, value in accounting.items():
        if key.endswith("_NOTE"):
            continue
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        _sentence(accounting["TED_BYTES_SENT_NOTE"]),
        "",
        f"**Next: {record['next_required_action']}.** "
        f"{_sentence(record['why_a_new_packet_is_required'])}",
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
        print(f"REFUSED  second opportunity execution record: {error}")
        return 1
    text = render(record)
    if args.check:
        if not RECORD_MD.exists():
            print(f"DRIFT    {RECORD_MD.name} does not exist")
            return 1
        if RECORD_MD.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RECORD_MD.name} does not match its record")
            return 1
        print("ok       the second-opportunity execution record matches its own")
        return 0
    RECORD_MD.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RECORD_MD.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['PRIMARY_OUTCOME']}")
    print(
        f"approval CONSUMED={record['EXECUTION_APPROVAL_CONSUMED']}, "
        f"further calls={record['FURTHER_CALLS_AUTHORIZED_BY_V1']}"
    )
    print(
        f"calls    {record['actual_provider_requests']} made, {record['retries']} retries, "
        f"{record['ACCOUNTING']['ADDITIONAL_PROVIDER_REQUESTS_DURING_FAILURE_CLOSURE']} during "
        "closure"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
