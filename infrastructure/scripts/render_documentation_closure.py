"""Render and validate the Mission 1.63 targeted documentation closure records.

Nine records. `validate()` enforces this arc's accumulated refusals plus the ones
this mission's four reads made concrete:

  - a current port list is not membership in an arbitrary window, list cardinality
    is not membership history, and no recorded removal is not continuity;
  - a configuration fact published for one data category does not establish it for
    another;
  - a configuration endpoint is not executed unless its response is PROVEN to
    carry no measurement, and proving it by calling it is circular;
  - an ambiguous timestamp is not resolved in the direction that keeps a candidate
    alive, and a retrieval summary is not a document;
  - a raw field named as TRUNCATED is not a raw field REMOVED, and finite retention
    is not automatic disqualification;
  - an estimated count endpoint may not feed a deterministic evaluator;
  - complete is not qualified, fewer than two qualified is not pair-ready, and a
    frozen enquiry that no longer answers to its hash is not frozen.

    uv run python infrastructure/scripts/render_documentation_closure.py
    uv run python infrastructure/scripts/render_documentation_closure.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "targeted-documentation-closure-baseline-v1.json"
INDICES = DATA / "netlas-indices-port-window-review-v1.json"
TEMPORAL = DATA / "onyphe-datascan-temporal-object-review-v1.json"
PORTS = DATA / "onyphe-scanned-port-review-v1.json"
RETENTION = DATA / "onyphe-full-fidelity-retention-review-v1.json"
A8 = DATA / "anchor-a8-recomputed-v1.json"
PACKAGE = DATA / "onyphe-package-recomputed-v1.json"
READINESS = DATA / "qualified-apparatus-readiness-v1.json"
ENQUIRY = DATA / "mission-1.61-enquiry-reassessment-v1.json"

ENQUIRY_V1_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"
ENQUIRY_V1_JSON = DATA / "anchor-technical-lineage-enquiry-v1.json"

ORDER = [BASELINE, INDICES, TEMPORAL, PORTS, RETENTION, A8, PACKAGE, READINESS, ENQUIRY]
RENDERED = {p: p.with_suffix(".md") for p in ORDER}

B_SLOTS = ("B1", "B2", "B3", "B4", "B5", "B6")
SLOT_STATES = ("PASS", "FAIL", "PARTIAL", "UNKNOWN", "NOT_ESTABLISHED", "NOT_APPLICABLE")
MATRIX_STATES = ("ANSWERED", "PARTIAL", "UNKNOWN", "NOT_APPLICABLE")

PORT_WINDOW_STATES = (
    "PORT_22_CONTINUOUSLY_COVERED",
    "PORT_22_MEMBERSHIP_VERSIONED_BY_INDEX",
    "PORT_22_MEMBERSHIP_VERSIONED_BY_DATE",
    "PORT_22_WINDOW_COVERAGE_QUERYABLE_AS_METADATA",
    "PORT_22_WINDOW_COVERAGE_NOT_ESTABLISHED",
)

ONYPHE_PORT_STATES = (
    "PORT_22_INCLUDED_CURRENTLY",
    "PORT_22_INCLUDED_IN_VERSIONED_SCAN_SET",
    "PORT_22_CONTINUOUSLY_INCLUDED",
    "PORT_22_NOT_INCLUDED",
    "PORT_22_STATUS_UNKNOWN",
)

RECORD_MODELS = (
    "OBSERVATION_EVENT",
    "MAINTAINED_SERVICE_STATE",
    "APPEND_WITH_VERSIONED_OBSERVATIONS",
    "AMBIGUOUS",
)

INDIVIDUAL_STATES = (
    "INDIVIDUALLY_QUALIFIED",
    "INDIVIDUALLY_NOT_QUALIFIED",
    "INDIVIDUALLY_UNRESOLVED",
)

APPARATUSES = ("LeakIX", "Netlas", "ONYPHE", "The Shadowserver Foundation")

ENQUIRY_CASES = ("CASE_A", "CASE_B", "CASE_C")

PRIMARY_OUTCOMES = {
    "TWO_QUALIFIED_APPARATUSES_READY_FOR_PAIR_ANALYSIS",
    "ANCHOR_ENQUIRY_STILL_REQUIRED_ONYPHE_QUALIFIED",
    "ANCHOR_OPERATIONALLY_REVIEWABLE_ONYPHE_UNRESOLVED",
    "ANCHOR_ENQUIRY_STILL_REQUIRED_ONYPHE_UNRESOLVED",
    "ONYPHE_TEMPORAL_OBJECT_NOT_ADDRESSABLE",
    "ONYPHE_PROTOCOL_FULL_FIDELITY_RETENTION_BLOCKER",
    "ANCHOR_PORT_WINDOW_CONFIGURATION_GAP",
    "PREREGISTRATION_POSSIBILITY_COMPROMISED",
    "MISSION_1_62_NOT_MERGED",
    "MISSION_1_63_BASELINE_DRIFT",
    "MISSION_1_63_CANONICAL_MUTATION",
    "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
    "TARGETED_DOCUMENTATION_CLOSURE_BLOCKED",
}

OVERCLAIMS = (
    "installation",
    "customer",
    "subscription",
    "revenue",
    "market share",
    "adoption",
    "demand",
    "user base",
)

PREFERENCE_WORDS = (
    "best candidate",
    "preferred candidate",
    "strongest partner",
    "lead route",
    "front-runner",
    "front runner",
)

GUESSED_ADDRESSES = ("support@", "info@", "security@", "contact@", "abuse@", "hello@")


class ValidationError(Exception):
    """A Mission 1.63 record claims something the rules do not permit."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    return json.loads(path.read_text(encoding="utf-8"))


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _prose(node: object) -> list[str]:
    out: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.startswith("$"):
                continue
            out.extend(_prose(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_prose(item))
    elif isinstance(node, str):
        out.append(node)
    return out


def validate() -> tuple[dict, ...]:
    records = tuple(_load(p) for p in ORDER)
    baseline, indices, temporal, ports, retention, a8, package, readiness, enquiry = records

    _validate_baseline(baseline)
    _validate_indices(indices)
    _validate_temporal(temporal)
    _validate_ports(ports)
    _validate_retention(retention)
    _validate_a8(a8, indices)
    _validate_package(package, temporal, ports, retention)
    _validate_readiness(readiness, a8, package)
    _validate_enquiry(enquiry)
    _validate_no_overclaims(records)
    _validate_no_preference(records)
    return records


def _validate_baseline(baseline: dict) -> None:
    pre = baseline["repository_precondition"]
    if pre.get("mission_1_62_merged") is not True:
        raise ValidationError("Mission 1.62 is not recorded as merged")
    if not pre.get("merge_commit", "").strip():
        raise ValidationError("the precondition must name the commit it verified")
    if pre.get("verified_from_git_not_from_prompt") is not True:
        raise ValidationError(
            "the precondition must be verified from git rather than from a prompt"
        )

    scope = baseline["frozen_scope"]
    if set(scope["investigated"]) != {"Netlas", "ONYPHE"}:
        raise ValidationError(
            "§1: only the anchor and the one unresolved candidate may be investigated"
        )
    if scope.get("new_candidates_searched") != 0:
        raise ValidationError("§1: no new scanner candidate may be searched")
    if scope.get("pair_selection_allowed") is not False:
        raise ValidationError("§1: pair selection is not allowed while no apparatus qualifies")
    for control in scope["frozen_negative_controls"]:
        if control.get("researched_this_mission") is not False:
            raise ValidationError(f"§26: {control['name']} was researched and must not be")
        if control.get("rescue_attempted") is not False:
            raise ValidationError(f"§26: a rescue was attempted for {control['name']}")
        if control.get("carried_verdict") != "INDIVIDUALLY_NOT_QUALIFIED":
            raise ValidationError(
                f"§26: {control['name']} must carry its established failure forward"
            )

    ledger = baseline["documentation_ledger"]
    if ledger["used"] != len(ledger["requests"]):
        raise ValidationError("the ledger count and its entries disagree")
    if ledger["used"] > ledger["budget"]:
        raise ValidationError(
            f"§35 bounds retrieval at {ledger['budget']} and the ledger records {ledger['used']}. "
            "Do not silently broaden"
        )
    named_targets = {t["n"] for t in baseline["the_four_targets"]["targets"]}
    for entry in ledger["requests"]:
        if entry.get("target") not in named_targets:
            raise ValidationError(
                f"§35: request {entry['n']} serves no named target. The four reads are the entire "
                "research scope"
            )

    acct = baseline["request_accounting"]
    for name in (
        "RESEARCH_DATA_REQUESTS",
        "MEASUREMENT_QUERIES_EXECUTED",
        "TARGET_COUNTS_FETCHED",
        "TARGET_HOST_RECORDS_FETCHED",
        "TARGET_IPS_FETCHED",
        "TARGET_BANNERS_FETCHED",
        "FACETS_FETCHED",
        "MEASUREMENT_DOWNLOADS",
        "TRIALS_STARTED",
        "PURCHASES",
        "OUTBOUND_ENQUIRIES_SENT",
    ):
        if acct.get(name) != 0:
            raise ValidationError(f"§36: {name} must be 0 and reads {acct.get(name)!r}")
    if acct.get("configuration_endpoints_executed") != 0:
        raise ValidationError(
            "§5: a configuration endpoint may be executed only where repository evidence proves "
            "its response carries no measurement. Fail closed"
        )
    if not acct.get("the_count_is_measurement", "").strip():
        raise ValidationError(
            "§6: the record must keep configuration metadata and measurement apart"
        )

    refuted = baseline["the_verbatim_re_read_that_changed_a_verdict"]
    for field in ("what_happened", "why_it_was_re_read", "what_the_re_read_found", "consequence"):
        if not refuted.get(field, "").strip():
            raise ValidationError(f"the verbatim re-read record states no {field}")

    for name, value in baseline["canonical_mutations"].items():
        if name.startswith("$"):
            continue
        if value not in (0, 0.0, False):
            raise ValidationError(
                f"§39: canonical mutation {name} reads {value!r} and must be zero"
            )


def _validate_indices(indices: dict) -> None:
    verdict = indices["verdict"]
    if verdict["result"] not in PORT_WINDOW_STATES:
        raise ValidationError(
            f"the port-window verdict {verdict['result']!r} is not in the vocabulary"
        )

    found = indices["what_was_found"]
    if (
        verdict["result"] != "PORT_22_WINDOW_COVERAGE_NOT_ESTABLISHED"
        and found.get("response_schema_available") is not True
    ):
        raise ValidationError(
            "§21: a port-window verdict other than NOT_ESTABLISHED requires the index schema. "
            "An endpoint existing is not documented semantics"
        )

    exec_block = indices["the_endpoint_was_not_executed"]
    if exec_block.get("executed") is not False:
        raise ValidationError(
            "§5: the configuration endpoint was executed without proof its response carries no "
            "measurement"
        )
    if not exec_block.get("the_circularity_that_was_refused", "").strip():
        raise ValidationError(
            "§5: the record must state why calling the endpoint to learn whether calling it is safe "
            "is circular"
        )

    refusals = indices["no_forbidden_inference_was_used"]
    for key in (
        "from_current_port_list",
        "from_list_cardinality",
        "from_absence_of_removals",
        "from_the_endpoint_existing",
    ):
        if not refusals.get(key, "").strip():
            raise ValidationError(f"§7/§21: the record must record the refusal {key}")

    consequence = indices["consequence_for_a8"]
    if consequence.get("a8_automatically_reviewable") is not False:
        raise ValidationError("§8: closing one topic does not close A8")


def _validate_temporal(temporal: dict) -> None:
    verdict = temporal["verdict"]
    if verdict["record_model"] not in RECORD_MODELS:
        raise ValidationError(f"record model {verdict['record_model']!r} is not in the vocabulary")
    if verdict["b2_result"] not in SLOT_STATES:
        raise ValidationError(f"B2 result {verdict['b2_result']!r} is not in the vocabulary")

    if verdict["b2_result"] == "PASS" and verdict["record_model"] not in (
        "OBSERVATION_EVENT",
        "APPEND_WITH_VERSIONED_OBSERVATIONS",
    ):
        raise ValidationError(
            "§10: B2 passes only on a record model where a window selects observations generated "
            "in it. An ambiguous or maintained-state model cannot pass"
        )
    if verdict["record_model"] == "AMBIGUOUS" and verdict["b2_result"] == "PASS":
        raise ValidationError(
            "§9: an ambiguous record model may not be resolved in the direction that preserves the "
            "candidate"
        )
    if verdict["record_model"] == "MAINTAINED_SERVICE_STATE" and verdict["b2_result"] != "FAIL":
        raise ValidationError(
            "§10: a maintained last-seen record model fails B2 for the same reason as the Mission "
            "1.59 apparatus"
        )
    if not verdict.get("the_interpretation_that_was_not_chosen", "").strip():
        raise ValidationError("§9: the record must name the interpretation it declined to choose")

    diagnostic = temporal["the_diagnostic"]
    if not diagnostic.get("answer", "").strip():
        raise ValidationError("§11: the temporal-object diagnostic must be answered")
    if diagnostic["answer"] not in (
        "NOT_DETERMINABLE_FROM_DOCUMENTATION",
        "INCLUDED_ON_OBSERVATION_EVENT",
        "GOVERNED_BY_LAST_DETECTION",
    ):
        raise ValidationError(
            f"the diagnostic answer {diagnostic['answer']!r} is not in the vocabulary"
        )

    empirical = temporal["no_empirical_resolution_was_attempted"]
    for name in ("records_queried", "hosts_queried", "timestamps_compared"):
        if empirical.get(name) != 0:
            raise ValidationError(
                f"§12: {name} reads {empirical.get(name)!r}. Documentation must establish the "
                "semantics; a sample query retrieves measurement and infers an architecture"
            )

    refuted = temporal["the_summary_that_was_refuted"]
    for field in (
        "what_the_first_read_reported",
        "why_it_was_checked",
        "what_the_verbatim_read_found",
    ):
        if not refuted.get(field, "").strip():
            raise ValidationError(f"the refuted-summary record states no {field}")


def _validate_ports(ports: dict) -> None:
    verdict = ports["verdict"]
    if verdict["result"] not in ONYPHE_PORT_STATES:
        raise ValidationError(f"the port verdict {verdict['result']!r} is not in the vocabulary")

    found = ports["what_was_found"]
    documented = found.get("the_category_this_documents")
    needed = found.get("the_category_the_construct_needs")
    if documented and needed and documented != needed:
        if verdict["result"] in (
            "PORT_22_INCLUDED_CURRENTLY",
            "PORT_22_INCLUDED_IN_VERSIONED_SCAN_SET",
            "PORT_22_CONTINUOUSLY_INCLUDED",
        ):
            raise ValidationError(
                f"§13: the published port list documents the {documented!r} category and the "
                f"construct needs {needed!r}. A configuration fact published for one resource does "
                "not establish it for another"
            )
        if not ports["the_category_mismatch"].get("statement", "").strip():
            raise ValidationError("the category mismatch must be stated where it exists")

    # startswith, not equality: the record states NONE and then says what it means,
    # and an equality check here would be a guard that can never fire.
    if str(found.get("temporal_binding", "")).startswith("NONE") and verdict["result"] in (
        "PORT_22_CONTINUOUSLY_INCLUDED",
        "PORT_22_INCLUDED_IN_VERSIONED_SCAN_SET",
    ):
        raise ValidationError(
            "§13: a list with no date, version or scan-configuration identifier cannot establish "
            "versioned or continuous inclusion"
        )

    if not ports["port_22_is_not_universally_ssh"].get("rule", "").strip():
        raise ValidationError("§14: the record must keep the construct pinned to TCP/22")
    if ports["port_22_is_not_universally_ssh"].get("construct_broadened") is not False:
        raise ValidationError("§14: the construct may not be broadened now")


def _validate_retention(retention: dict) -> None:
    settles = retention["what_the_sentence_settles"]
    if settles.get("the_data_field_is_named") is not True:
        raise ValidationError(
            "the raw field's survival rests on it being NAMED in the retention sentence. Without "
            "that this is an inference from silence"
        )
    if (
        settles.get("does_the_ssh_prefix_survive") == "YES"
        and "TRUNCAT" not in settles.get("truncation", "").upper()
    ):
        raise ValidationError(
            "§15: the prefix survives because the field is truncated rather than removed, and "
            "the record must say which operation applies to it"
        )

    unsettled = retention["what_the_sentence_does_not_settle"]
    for key in (
        "which_fields_are_removed",
        "does_the_observation_timestamp_survive",
        "does_the_ip_address_survive",
    ):
        if not str(unsettled.get(key, "")).strip():
            raise ValidationError(f"§15: {key} must be recorded rather than left out")
        if str(unsettled[key]).upper().startswith(("YES", "NO ")):
            raise ValidationError(
                f"§15: {key} is answered where the documentation names nothing. Do not guess "
                "unnamed removed fields"
            )
    if not unsettled.get("why_these_are_not_guessed", "").strip():
        raise ValidationError("§15: the record must say why the unnamed fields were not guessed")

    deadlines = retention["retrieval_deadlines"]
    if not deadlines.get("MAX_FULL_FIDELITY_RETRIEVAL_DELAY", "").strip():
        raise ValidationError("§17: the full-fidelity retrieval delay must be frozen as a duration")
    for flag in ("no_dates_chosen", "no_window_selected", "no_values_retrieved"):
        if deadlines.get(flag) is not True:
            raise ValidationError(f"§17: {flag} must hold")

    finite = retention["finite_retention_is_not_automatic_disqualification"]
    if finite.get("does_retention_block_this_apparatus") is True:
        raise ValidationError(
            "§16: finite retention is not automatic disqualification. The question is whether the "
            "load-bearing facts can be acquired within a known window"
        )

    b3 = retention["b3_is_not_reopened"]
    if b3.get("reopened_merely_because_retention_is_finite") is not False:
        raise ValidationError("§18: B3 is not reopened merely because retention is finite")
    if b3.get("verdict") == "ONYPHE_B3_PASS" and b3.get("retained") is not True:
        raise ValidationError("a B3 pass must record that it was retained rather than re-derived")


def _validate_a8(a8: dict, indices: dict) -> None:
    if a8["basis"].get("enquiry_answers_used") is not False:
        raise ValidationError(
            "§20: enquiry answers may not be used, because the enquiry is unsent. A drafted "
            "enquiry establishes nothing"
        )

    matrix = a8["matrix"]
    topics = {row["topic"] for row in matrix}
    for required in (
        "SAMPLING",
        "FRAME",
        "MISSINGNESS",
        "RETRY",
        "DUPLICATION",
        "DISTINCT_ADDRESS_SEMANTICS",
        "BANNER_FIDELITY",
        "SCAN_DATE_SEMANTICS",
        "VANTAGE",
        "PORT_22_WINDOW_COVERAGE",
    ):
        if required not in topics:
            raise ValidationError(f"§20: the recomputed matrix omits {required}")
    for row in matrix:
        for field in ("before", "after"):
            if row[field] not in MATRIX_STATES:
                raise ValidationError(f"{row['topic']} carries {field} = {row[field]!r}")
        if row["changed"] != (row["before"] != row["after"]):
            raise ValidationError(f"{row['topic']} disagrees with itself about whether it changed")
        if not row.get("basis", "").strip():
            raise ValidationError(f"{row['topic']} records no basis")

    tally = a8["tally"]
    for key, state in (("answered", "ANSWERED"), ("partial", "PARTIAL"), ("unknown", "UNKNOWN")):
        counted = sum(1 for r in matrix if r["after"] == state)
        if tally[key] != counted:
            raise ValidationError(
                f"the tally records {tally[key]} {state} and the matrix has {counted}"
            )
    if tally["changed_this_mission"] != sum(1 for r in matrix if r["changed"]):
        raise ValidationError("the changed count disagrees with the matrix")

    verdict = a8["verdict"]
    unknowns = sum(1 for r in matrix if r["after"] == "UNKNOWN" and r.get("load_bearing"))
    if verdict.get("reviewable") is True and unknowns:
        raise ValidationError(
            f"§20: A8 is recorded reviewable with {unknowns} load-bearing topics unknown"
        )
    if verdict.get("reviewable") is False and not verdict.get("why_not_reviewable", "").strip():
        raise ValidationError("a non-reviewable A8 must say what blocks it")

    progress = verdict["no_imaginary_progress"]
    for key in (
        "we_now_know_which_page_to_read_was_not_converted_into_pass",
        "endpoint_exists_was_not_converted_into_documented_semantics",
    ):
        if not progress.get(key, "").strip():
            raise ValidationError(f"§21: the record must state that {key}")

    port_row = next(r for r in matrix if r["topic"] == "PORT_22_WINDOW_COVERAGE")
    if (
        indices["verdict"]["result"] == "PORT_22_WINDOW_COVERAGE_NOT_ESTABLISHED"
        and port_row["after"] == "ANSWERED"
    ):
        raise ValidationError(
            "the port-window topic is ANSWERED while the indices review records it as not "
            "established"
        )


def _validate_package(package: dict, temporal: dict, ports: dict, retention: dict) -> None:
    pkg = package["package"]
    for slot in B_SLOTS:
        if slot not in pkg:
            raise ValidationError(f"§19: slot {slot} was not reported. Report every mandatory gate")
        entry = pkg[slot]
        for field in ("before", "after"):
            if entry[field] not in SLOT_STATES:
                raise ValidationError(f"{slot} carries {field} = {entry[field]!r}")
        if entry["changed"] != (entry["before"] != entry["after"]):
            raise ValidationError(f"{slot} disagrees with itself about whether it changed")
        if not entry.get("basis", "").strip():
            raise ValidationError(f"{slot} records no basis")
        if "binding_blocker" not in entry:
            raise ValidationError(f"§19: {slot} does not say whether it is a binding blocker")

    if pkg["B2"]["after"] != temporal["verdict"]["b2_result"]:
        raise ValidationError("the package and the temporal review disagree about B2")
    if (
        pkg["B3"]["after"] == "PASS"
        and retention["b3_is_not_reopened"]["verdict"] != "ONYPHE_B3_PASS"
    ):
        raise ValidationError("the package and the retention review disagree about B3")
    if ports["verdict"]["result"] == "PORT_22_STATUS_UNKNOWN" and pkg["B4"]["after"] == "PASS":
        raise ValidationError(
            "B4 passes while port-22 membership in the relevant scan set is unknown"
        )

    if package["slots_changed"] != sum(1 for s in B_SLOTS if pkg[s]["changed"]):
        raise ValidationError("the changed-slot count disagrees with the slots")

    qual = package["individual_qualification"]
    if qual["verdict"] not in INDIVIDUAL_STATES:
        raise ValidationError(f"individual verdict {qual['verdict']!r} is not in the vocabulary")
    hard_fails = [s for s in B_SLOTS if pkg[s]["after"] == "FAIL"]
    all_pass = all(pkg[s]["after"] == "PASS" for s in B_SLOTS)
    if hard_fails and qual["verdict"] != "INDIVIDUALLY_NOT_QUALIFIED":
        raise ValidationError(f"a hard FAIL at {hard_fails} must give INDIVIDUALLY_NOT_QUALIFIED")
    if qual["verdict"] == "INDIVIDUALLY_QUALIFIED" and not all_pass:
        raise ValidationError(
            "§19: qualification is conjunctive. A partial is not a pass and an unknown is not a pass"
        )
    blockers = qual.get("binding_blockers", [])
    declared = [s for s in B_SLOTS if pkg[s].get("binding_blocker")]
    if sorted(blockers) != sorted(declared):
        raise ValidationError("the declared binding blockers and the slots disagree")

    access = package["epistemic_and_access_recorded_separately"]
    for field in ("EPISTEMIC_DOCUMENTATION_STATUS", "FUTURE_ACCESS_STATUS"):
        if not access.get(field, "").strip():
            raise ValidationError(
                f"§19: {field} must be recorded. Documentation being public says nothing about "
                "whether retrieval is"
            )


def _validate_readiness(readiness: dict, a8: dict, package: dict) -> None:
    listed = {a["name"]: a for a in readiness["apparatuses"]}
    if set(listed) != set(APPARATUSES):
        raise ValidationError(f"§28: readiness must cover exactly {APPARATUSES}")
    for name, entry in listed.items():
        if entry["individual_status"] not in INDIVIDUAL_STATES:
            raise ValidationError(f"{name} carries status {entry['individual_status']!r}")

    if listed["ONYPHE"]["individual_status"] != package["individual_qualification"]["verdict"]:
        raise ValidationError("the readiness record and the ONYPHE package disagree")
    if (
        a8["verdict"].get("reviewable") is False
        and listed["Netlas"]["individual_status"] == "INDIVIDUALLY_QUALIFIED"
    ):
        raise ValidationError("the anchor cannot qualify while A8 is not reviewable")

    block = readiness["readiness"]
    counted = sum(1 for a in listed.values() if a["individual_status"] == "INDIVIDUALLY_QUALIFIED")
    if block["QUALIFIED_APPARATUS_COUNT"] != counted:
        raise ValidationError("the qualified count disagrees with the apparatus states")
    if block["PAIR_ANALYSIS_READY"] != (counted >= block["threshold_for_readiness"]):
        raise ValidationError(
            "§28: pair analysis is ready exactly when at least two apparatuses individually qualify"
        )
    if block.get("this_is_a_status_not_a_selection") is not True:
        raise ValidationError("§28: readiness is a status and never a selection")

    pair = readiness["no_pair_work_was_performed"]
    for flag in (
        "same_frame_evaluated",
        "same_observation_window_evaluated",
        "vantage_compatibility_evaluated",
        "lineage_independence_evaluated",
        "shared_measurement_upstream_evaluated",
        "same_target_proposition_evaluated",
        "threshold_preregistrability_evaluated",
    ):
        if pair.get(flag) is not False:
            raise ValidationError(f"§27: {flag} must be false")
    for counter in ("pairs_compared", "pairs_ranked", "pairs_selected"):
        if pair.get(counter) != 0:
            raise ValidationError(f"§27: {counter} must be 0")

    controls = readiness["the_negative_controls_were_left_alone"]
    if controls.get("researched") != 0 or controls.get("rescue_attempted") != 0:
        raise ValidationError("§26: the negative controls must be left alone")

    if readiness["primary_outcome"] not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {readiness['primary_outcome']!r}")
    if not readiness.get("primary_outcome_statement", "").strip():
        raise ValidationError("the outcome must be stated in a sentence, not only as a label")
    outcome = readiness["primary_outcome"]
    if outcome == "TWO_QUALIFIED_APPARATUSES_READY_FOR_PAIR_ANALYSIS" and counted < 2:
        raise ValidationError(
            "§45 outcome A requires at least two individually qualifying apparatuses. Do NOT force A"
        )
    if outcome == "ANCHOR_OPERATIONALLY_REVIEWABLE_ONYPHE_UNRESOLVED" and (
        a8["verdict"].get("reviewable") is not True
    ):
        raise ValidationError("§45 outcome C requires the anchor's A8 to have closed")
    if outcome == "ANCHOR_ENQUIRY_STILL_REQUIRED_ONYPHE_QUALIFIED" and (
        package["individual_qualification"]["verdict"] != "INDIVIDUALLY_QUALIFIED"
    ):
        raise ValidationError("§45 outcome B requires the candidate to have become qualified")

    secondary = readiness["secondary_outcomes"]
    if secondary["QUALIFIED_APPARATUS_COUNT"] != block["QUALIFIED_APPARATUS_COUNT"]:
        raise ValidationError("the secondary outcomes and the readiness block disagree")
    if secondary["ANCHOR_A8"] != a8["verdict"]["status_word"]:
        raise ValidationError("the secondary outcomes and the A8 record disagree")

    reg = readiness["registry_decision"]
    for item in reg["added"]:
        for field in ("name", "from", "rule", "demonstrated_by", "distinct_from"):
            if not item.get(field, "").strip():
                raise ValidationError(
                    f"§33: registry entry {item.get('name')!r} states no {field}. A rule is added "
                    "only where evidence demonstrates a distinct guard"
                )
    for item in reg["declined"]:
        if not item.get("why_declined", "").strip():
            raise ValidationError(
                f"§34: declining {item.get('name')!r} is a decision and must state its reason"
            )
    if reg["registry_size_after"] - reg["registry_size_before"] != len(reg["added"]):
        raise ValidationError("the registry size change does not match the rules added")

    for name, value in readiness["stop_condition"].items():
        if name.startswith("$") or name == "awaiting":
            continue
        if value is not False:
            raise ValidationError(
                f"the stop condition {name} reads {value!r} and every one must be false"
            )

    count_block = readiness["count_endpoint_constraint_carried_forward"]
    if (
        count_block.get("status_word")
        != "ESTIMATED_COUNT_ENDPOINT_PROHIBITED_FOR_DETERMINISTIC_THRESHOLD"
    ):
        raise ValidationError("§31: the count-endpoint prohibition must be carried forward by name")
    for flag in (
        "no_probabilistic_semantics_introduced",
        "no_confidence_interval_evaluator_introduced",
    ):
        if count_block.get(flag) is not True:
            raise ValidationError(f"§32: {flag} must hold")
    if count_block.get("executed_this_mission") is not False:
        raise ValidationError(
            "§31: the exact-count route was not executed and must not say otherwise"
        )


def _validate_enquiry(enquiry: dict) -> None:
    artifact = enquiry["artifact"]
    if artifact.get("edited") is not False:
        raise ValidationError("§22: enquiry v1 is never edited")
    if artifact.get("bytes_unchanged") is not True:
        raise ValidationError("§22: enquiry v1's bytes must be unchanged")
    if artifact.get("sent") is not False:
        raise ValidationError("the enquiry has not been sent and must not say otherwise")

    if not ENQUIRY_V1_MD.exists():
        raise ValidationError("the frozen Mission 1.61 enquiry is missing")
    digest = hashlib.sha256(ENQUIRY_V1_MD.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    if digest != artifact["sha256"]:
        raise ValidationError(
            f"§22: the frozen enquiry no longer answers to its hash. recorded {artifact['sha256']}, "
            f"computed {digest}"
        )
    v1 = _load(ENQUIRY_V1_JSON)
    if v1.get("status") != "AWAITING_OPERATOR_APPROVAL":
        raise ValidationError("§22: enquiry v1's status was changed")
    if v1["delivery"].get("sent") is not False or v1["delivery"].get("sent_at") is not None:
        raise ValidationError("§22: enquiry v1's delivery state was changed")

    disposition = enquiry["question_disposition"]
    if {d["topic"] for d in disposition} != {q["topic"] for q in v1["questions"]}:
        raise ValidationError("§22: every frozen question must receive a disposition, and no other")
    for d in disposition:
        if d["disposition"] not in (
            "ANSWERED_BY_PUBLIC_DOCS",
            "STILL_UNRESOLVED",
            "NO_LONGER_LOAD_BEARING",
        ):
            raise ValidationError(f"question {d['n']} carries disposition {d['disposition']!r}")

    tally = enquiry["tally"]
    for key, state in (
        ("answered_by_public_docs", "ANSWERED_BY_PUBLIC_DOCS"),
        ("still_unresolved", "STILL_UNRESOLVED"),
        ("no_longer_load_bearing", "NO_LONGER_LOAD_BEARING"),
    ):
        counted = sum(1 for d in disposition if d["disposition"] == state)
        if tally[key] != counted:
            raise ValidationError(
                f"the tally records {tally[key]} {state} and the questions give {counted}"
            )

    case = enquiry["case"]
    if case["selected"] not in ENQUIRY_CASES:
        raise ValidationError(f"enquiry case {case['selected']!r} is not in the vocabulary")
    unresolved = tally["still_unresolved"]
    total = tally["total"]
    if unresolved == total and case["selected"] != "CASE_A":
        raise ValidationError("§23: all seven unresolved is CASE A, and v1 remains current")
    if unresolved == 0 and case["selected"] != "CASE_C":
        raise ValidationError("§23: no question remaining is CASE C, and v1 becomes NOT_NEEDED")
    if 0 < unresolved < total and case["selected"] != "CASE_B":
        raise ValidationError("§23: some questions answered is CASE B, and a v2 is required")
    if case["selected"] == "CASE_A":
        # Two independent checks under one condition. They are deliberately NOT
        # collapsed into the guard above: a mechanical collapse folded the second
        # into the first's raise once already, which made it unreachable while
        # still looking like a check.
        if case.get("v2_created") is not False:
            raise ValidationError("§23: CASE A creates no v2")
        if artifact["sha256"] not in case.get("operative_approval_string", ""):
            raise ValidationError(
                "§23: CASE A keeps Mission 1.61's hash authoritative and computes no duplicate"
            )
    if case["selected"] == "CASE_B" and case.get("v2_created") is not True:
        raise ValidationError("§23: CASE B requires a v2 carrying only the remaining questions")

    if (
        enquiry["the_enquiry_is_not_evidence"].get("enquiry_answers_used_in_the_a8_recomputation")
        is not False
    ):
        raise ValidationError("a drafted enquiry establishes nothing and may not feed a verdict")

    contact = enquiry["contact_channel"]
    if (
        contact.get("address_invented") is not False
        or contact.get("address_decoded_by_guess") is not False
    ):
        raise ValidationError("§25: no contact address may be invented or guessed")
    if contact.get("conventional_mailboxes_inferred") is not False:
        raise ValidationError("§25: conventional mailboxes may not be inferred")
    blob = json.dumps(contact)
    for guess in GUESSED_ADDRESSES:
        if guess in blob:
            raise ValidationError(f"§25: the contact record names a guessed address form {guess!r}")
    if contact.get("outbound_messages_sent") != 0:
        raise ValidationError("§24: no outbound message is sent in this mission")


def _validate_no_overclaims(records: tuple[dict, ...]) -> None:
    for record in records:
        for sentence in _prose(record):
            tokens = re.findall(r"[a-z0-9]+", sentence.lower())
            for term in OVERCLAIMS:
                parts = term.split()
                if len(parts) == 1:
                    hit = parts[0] in tokens
                else:
                    hit = any(
                        tokens[i : i + len(parts)] == parts
                        for i in range(max(0, len(tokens) - len(parts) + 1))
                    )
                if hit:
                    raise ValidationError(
                        f"a record uses {term!r}. A count of addresses answering on a port is not a "
                        f"market statement. Offending sentence: {sentence[:110]!r}"
                    )


def _validate_no_preference(records: tuple[dict, ...]) -> None:
    for record in records:
        for sentence in _prose(record):
            lowered = sentence.lower()
            for word in PREFERENCE_WORDS:
                if word in lowered:
                    raise ValidationError(
                        f"§27: a record uses {word!r}. This mission ranks nothing. Offending "
                        f"sentence: {sentence[:110]!r}"
                    )


# --------------------------------------------------------------------------- render


def render_baseline(record: dict) -> str:
    pre = record["repository_precondition"]
    base = record["canonical_baseline"]
    ledger = record["documentation_ledger"]
    acct = record["request_accounting"]
    refuted = record["the_verbatim_re_read_that_changed_a_verdict"]

    lines = [
        "# Targeted documentation closure — baseline",
        "",
        "Generated by `infrastructure/scripts/render_documentation_closure.py`. Do not edit.",
        "",
        f"**Mission:** {record['mission']}  ",
        f"**Recorded:** {record['recorded_at']}",
        "",
        "## Precondition",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["Mission 1.62 merged", str(pre["mission_1_62_merged"])]),
        _row(["merge commit", f"`{pre['merge_commit']}`"]),
        _row(["branch", f"`{pre['branch']}`"]),
        _row(["migration head", f"`{pre['migration_head']}`"]),
        _row(["drift", f"**{base['drift_from_mission_1_62']}**"]),
        "",
        "## Frozen scope",
        "",
        f"Investigated: **{', '.join(record['frozen_scope']['investigated'])}**.",
        "",
        "Frozen negative controls, not researched and not rescued:",
        "",
    ]
    for c in record["frozen_scope"]["frozen_negative_controls"]:
        lines.append(f"- **{c['name']}** — `{c['carried_verdict']}`, {c['binding_failure']}")
    lines += ["", "## The four targets", "", _row(["#", "subject", "question"]), _row(["---"] * 3)]
    for t in record["the_four_targets"]["targets"]:
        lines.append(_row([str(t["n"]), t["subject"], t["question"]]))
    ft = record["the_four_targets"]
    lines += [
        "",
        f"Fully resolved `{ft['targets_fully_resolved']}`, partially "
        f"`{ft['targets_partially_resolved']}`, unresolved `{ft['targets_unresolved']}`.",
        "",
        "## Documentation ledger",
        "",
        f"{ledger['used']} of {ledger['budget']}.",
        "",
        _row(["#", "subject", "target", "sought", "usable"]),
        _row(["---"] * 5),
    ]
    for e in ledger["requests"]:
        lines.append(
            _row(
                [
                    str(e["n"]),
                    e["subject"],
                    str(e["target"]),
                    e["sought"],
                    "yes" if e["usable"] else f"no ({e.get('note', '')})",
                ]
            )
        )
    lines += [
        "",
        ledger["why_seven_and_not_four"],
        "",
        "## The verbatim re-read that changed a verdict",
        "",
        refuted["what_happened"],
        "",
        f"*Why it was re-read:* {refuted['why_it_was_re_read']}",
        "",
        f"*What the re-read found:* {refuted['what_the_re_read_found']}",
        "",
        f"**{refuted['consequence']}**",
        "",
        refuted["the_rule_this_confirms"],
        "",
        "## What did not happen",
        "",
        "```",
        f"measurement queries        {acct['MEASUREMENT_QUERIES_EXECUTED']}"
        f"    trials      {acct['TRIALS_STARTED']}",
        f"target counts              {acct['TARGET_COUNTS_FETCHED']}"
        f"    purchases   {acct['PURCHASES']}",
        f"host records               {acct['TARGET_HOST_RECORDS_FETCHED']}"
        f"    facets      {acct['FACETS_FETCHED']}",
        f"configuration endpoints    {acct['configuration_endpoints_executed']}"
        f"    enquiries   {acct['OUTBOUND_ENQUIRIES_SENT']}",
        "```",
        "",
        f"**The endpoint that was not executed.** "
        f"{acct['the_endpoint_that_was_not_executed']['why_not']}",
        "",
        acct["the_count_is_measurement"],
        "",
    ]
    return "\n".join(lines)


def render_indices(record: dict) -> str:
    verdict = record["verdict"]
    found = record["what_was_found"]
    ex = record["the_endpoint_was_not_executed"]
    lines = [
        "# Netlas indices — port-window review",
        "",
        "Generated by `infrastructure/scripts/render_documentation_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Verdict:** `{verdict['result']}`",
        "",
        record["what_was_sought"]["why_it_matters"],
        "",
        "## What was found",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["endpoint located", str(found["endpoint_located"])]),
        _row(["documented operation", f"`{found['documented_operation']}`"]),
        _row(["documented path", f"`{found['documented_path']}`"]),
        _row(["response schema available", f"**{found['response_schema_available']}**"]),
        "",
        found["why_not"],
        "",
        f"*What that establishes:* {found['what_that_establishes']}",
        "",
        f"*What it does not:* {found['what_that_does_not_establish']}",
        "",
        "## The endpoint was not executed",
        "",
        ex["the_rule"],
        "",
        ex["the_reasoning"],
        "",
        f"**{ex['the_circularity_that_was_refused']}**",
        "",
        "## No forbidden inference was used",
        "",
    ]
    for key, text in record["no_forbidden_inference_was_used"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines += [
        "",
        "## How this could still be closed",
        "",
        _row(["mechanism", "status", "cost"]),
        _row(["---"] * 3),
    ]
    for m in record["how_this_could_still_be_closed"]["mechanisms"]:
        lines.append(_row([m["mechanism"], m["status"], m["cost"]]))
    lines += [
        "",
        f"**Consequence for A8.** Topic `{record['consequence_for_a8']['topic_updated']}` stays "
        f"`{record['consequence_for_a8']['topic_status']}`. "
        f"{record['consequence_for_a8']['why']}",
        "",
    ]
    return "\n".join(lines)


def render_temporal(record: dict) -> str:
    verdict = record["verdict"]
    refuted = record["the_summary_that_was_refuted"]
    ql = record["what_the_query_language_page_adds"]
    lines = [
        "# ONYPHE datascan — temporal object review",
        "",
        "Generated by `infrastructure/scripts/render_documentation_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Record model:** `{verdict['record_model']}`  ",
        f"**B2:** `{verdict['b2_result']}`",
        "",
        record["what_was_sought"]["why_it_decides_b2"],
        "",
        "## The ambiguity carried in",
        "",
        f"> {record['the_ambiguity_carried_in']['verbatim_timestamp_definition']}",
        "",
        record["the_ambiguity_carried_in"]["why_it_is_ambiguous"],
        "",
        "## What the query-language page adds",
        "",
        f"> {ql['verbatim_section_description']}",
        "",
        _row(["function", "documented bucket boundary"]),
        _row(["---", "---"]),
    ]
    for fn, boundary in ql["verbatim_bucket_boundaries"].items():
        lines.append(_row([f"`{fn}`", boundary]))
    lines += [
        "",
        f"*Establishes:* {ql['what_this_establishes']}",
        "",
        f"*Does not establish:* {ql['what_this_does_not_establish']}",
        "",
        f"*Granularity bound:* {ql['granularity_bound']}",
        "",
        "## The summary that was refuted",
        "",
        refuted["what_the_first_read_reported"],
        "",
        f"*Why that would have been decisive:* {refuted['why_that_would_have_been_decisive']}",
        "",
        f"*Why it was checked:* {refuted['why_it_was_checked']}",
        "",
        f"**{refuted['what_the_verbatim_read_found']}**",
        "",
        refuted["outcome"],
        "",
        refuted["precedent"],
        "",
        "## The diagnostic",
        "",
        record["the_diagnostic"]["question"],
        "",
        f"**`{record['the_diagnostic']['answer']}`.** {record['the_diagnostic']['why']}",
        "",
        "## Verdict",
        "",
        f"`{verdict['record_model']}` / B2 `{verdict['b2_result']}`. {verdict['what_did_move']}",
        "",
        f"**The interpretation that was not chosen.** "
        f"{verdict['the_interpretation_that_was_not_chosen']}",
        "",
        f"*What would close it:* {verdict['what_would_close_it']}",
        "",
    ]
    return "\n".join(lines)


def render_ports(record: dict) -> str:
    verdict = record["verdict"]
    found = record["what_was_found"]
    mismatch = record["the_category_mismatch"]
    lines = [
        "# ONYPHE scanned-port review",
        "",
        "Generated by `infrastructure/scripts/render_documentation_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Verdict:** `{verdict['result']}`, scoped to {verdict['scope_of_the_verdict']}",
        "",
        record["what_was_sought"]["why_the_word_relevant_is_load_bearing"],
        "",
        "## What was found",
        "",
        f"> {found['verbatim_header']}",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["port 22 present", str(found["port_22_present"])]),
        _row(["listed as", f"`{found['how_port_22_is_listed']}`"]),
        _row(["category documented", f"**{found['the_category_this_documents']}**"]),
        _row(["category the construct needs", f"**{found['the_category_the_construct_needs']}**"]),
        _row(["temporal binding", found["temporal_binding"]]),
        _row(["update cadence", found["update_cadence_or_historical_versions"]]),
        "",
        "## The category mismatch",
        "",
        f"**{mismatch['statement']}**",
        "",
    ]
    lines += [f"- {r}" for r in mismatch["why_this_is_not_a_technicality"]]
    lines += [
        "",
        f"*The inference that was refused:* {mismatch['the_inference_that_was_refused']}",
        "",
        f"*What would resolve it:* {mismatch['what_would_resolve_it']}",
        "",
        "## Port 22 is not universally SSH",
        "",
        record["port_22_is_not_universally_ssh"]["rule"],
        "",
        record["port_22_is_not_universally_ssh"]["consequence"],
        "",
        "## Verdict",
        "",
        f"*Established:* {verdict['what_is_established']}",
        "",
        f"*Not established:* {verdict['what_is_not_established']}",
        "",
        f"*Why not INCLUDED_CURRENTLY:* {verdict['why_not_INCLUDED_CURRENTLY']}",
        "",
        f"*Why not NOT_INCLUDED:* {verdict['why_not_NOT_INCLUDED']}",
        "",
        record["a_new_gap_that_did_not_exist_before"]["statement"],
        "",
        record["a_new_gap_that_did_not_exist_before"]["why_this_is_progress"],
        "",
    ]
    return "\n".join(lines)


def render_retention(record: dict) -> str:
    settles = record["what_the_sentence_settles"]
    unsettled = record["what_the_sentence_does_not_settle"]
    deadlines = record["retrieval_deadlines"]
    b3 = record["b3_is_not_reopened"]
    lines = [
        "# ONYPHE full-fidelity retention review",
        "",
        "Generated by `infrastructure/scripts/render_documentation_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Verdict:** `{record['verdict']['result']}`",
        "",
        "## The verbatim rule",
        "",
        f"> {record['the_verbatim_rule']['sentence']}",
        "",
        record["the_verbatim_rule"]["the_thirty_day_window"],
        "",
        "## What the sentence settles",
        "",
        _row(["operation", "applies to"]),
        _row(["---", "---"]),
        _row(["removal", settles["removal"]]),
        _row(["truncation", settles["truncation"]]),
        "",
        f"**Does the SSH prefix survive? {settles['does_the_ssh_prefix_survive']}.** {settles['why']}",
        "",
        settles["this_is_a_deduction_from_a_documented_fact_not_an_inference_from_silence"],
        "",
        "## What it does not settle",
        "",
    ]
    for key, value in unsettled.items():
        if key.startswith("$") or key == "why_these_are_not_guessed":
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {value}")
    lines += [
        "",
        unsettled["why_these_are_not_guessed"],
        "",
        "## Retrieval deadlines",
        "",
        _row(["contract", "value"]),
        _row(["---", "---"]),
        _row(
            ["`MAX_FULL_FIDELITY_RETRIEVAL_DELAY`", deadlines["MAX_FULL_FIDELITY_RETRIEVAL_DELAY"]]
        ),
        _row(
            [
                "`MAX_PREDICATE_SUFFICIENT_RETRIEVAL_DELAY`",
                deadlines["MAX_PREDICATE_SUFFICIENT_RETRIEVAL_DELAY"],
            ]
        ),
        "",
        deadlines["why_not_established"],
        "",
        f"*The conservative contract:* {deadlines['the_conservative_contract']}",
        "",
        "## Finite retention is not disqualification",
        "",
        record["finite_retention_is_not_automatic_disqualification"]["rule"],
        "",
        record["finite_retention_is_not_automatic_disqualification"]["outcome_F_not_selected"],
        "",
        "## B3 is not reopened",
        "",
        f"`{b3['verdict']}`, retained **{b3['retained']}**.",
        "",
        _row(["condition that would have reopened it", "state"]),
        _row(["---", "---"]),
    ]
    for key, value in b3["the_three_conditions_that_would_have_reopened_it"].items():
        lines.append(_row([key.replace("_", " "), value]))
    lines += ["", f"*What improved:* {b3['what_did_improve']}", ""]
    return "\n".join(lines)


def render_a8(record: dict) -> str:
    verdict = record["verdict"]
    tally = record["tally"]
    lines = [
        "# Anchor A8 — recomputed",
        "",
        "Generated by `infrastructure/scripts/render_documentation_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Verdict:** `{verdict['status_word']}`, reviewable **{verdict['reviewable']}**",
        "",
        f"`{tally['answered']}` answered, `{tally['partial']}` partial, `{tally['unknown']}` "
        f"unknown, of `{tally['total']}`. **`{tally['changed_this_mission']}` changed this mission.**",
        "",
        f"Enquiry answers used: **{record['basis']['enquiry_answers_used']}**. "
        f"{record['basis']['why']}",
        "",
        "## Matrix",
        "",
        _row(["topic", "before", "after", "changed", "load bearing"]),
        _row(["---"] * 5),
    ]
    for row in record["matrix"]:
        lines.append(
            _row(
                [
                    row["topic"],
                    f"`{row['before']}`",
                    f"`{row['after']}`",
                    "yes" if row["changed"] else "",
                    "yes" if row.get("load_bearing") else "",
                ]
            )
        )
    lines += ["", "### Basis", ""]
    for row in record["matrix"]:
        line = f"- **{row['topic']}** — {row['basis']}"
        if row.get("what_improved"):
            line += f" *({row['what_improved']})*"
        lines.append(line)
    lines += [
        "",
        "## Verdict",
        "",
        f"**Why not reviewable.** {verdict['why_not_reviewable']}",
        "",
        f"**Why not NOT_REVIEWABLE.** {verdict['why_not_NOT_REVIEWABLE']}",
        "",
        "### No imaginary progress",
        "",
    ]
    for key, text in verdict["no_imaginary_progress"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- {text}")
    close = record["what_would_close_a8"]
    lines += [
        "",
        "## What would close A8",
        "",
        f"- **by reading** — {'; '.join(close['by_reading'])}",
        f"- **by asking** — {'; '.join(close['by_asking'])}",
        "",
        close["the_arithmetic"],
        "",
    ]
    return "\n".join(lines)


def render_package(record: dict) -> str:
    qual = record["individual_qualification"]
    lines = [
        "# ONYPHE package — recomputed",
        "",
        "Generated by `infrastructure/scripts/render_documentation_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Verdict:** `{qual['verdict']}`, binding blockers **{qual['binding_blockers']}**",
        "",
        f"`{record['slots_changed']}` slots changed, `{record['slots_better_evidenced']}` better "
        f"evidenced ({', '.join(record['which_better_evidenced'])}).",
        "",
        "## Package",
        "",
        _row(["slot", "requirement", "before", "after", "blocker"]),
        _row(["---"] * 5),
    ]
    for slot in B_SLOTS:
        e = record["package"][slot]
        lines.append(
            _row(
                [
                    slot,
                    e["slot"],
                    f"`{e['before']}`",
                    f"`{e['after']}`",
                    "**yes**" if e["binding_blocker"] else "",
                ]
            )
        )
    lines += ["", "## Slot findings", ""]
    for slot in B_SLOTS:
        e = record["package"][slot]
        lines += [f"### {slot} {e['slot']} — `{e['after']}`", "", e["basis"], ""]
        for key in (
            "what_improved",
            "what_changed_inside_it",
            "what_was_refused",
            "note",
            "classification",
            "lineage_level",
        ):
            if e.get(key):
                lines += [f"*{key.replace('_', ' ')}:* {e[key]}", ""]
        if e.get("missing_facts"):
            lines += ["*missing facts:* " + "; ".join(e["missing_facts"]), ""]
    lines += [
        "## Vantage",
        "",
        f"`{record['vantage']['verdict']}`. {record['vantage']['basis']}",
        "",
        "## Qualification",
        "",
        qual["reason"],
        "",
        f"**{qual['why_this_is_not_stagnation']}**",
        "",
        "*What would resolve it:*",
        "",
    ]
    lines += [f"- {item}" for item in qual["what_would_resolve_it"]]
    access = record["epistemic_and_access_recorded_separately"]
    lines += [
        "",
        "## Documentation versus access",
        "",
        f"- **epistemic** — {access['EPISTEMIC_DOCUMENTATION_STATUS']}",
        f"- **future access** — {access['FUTURE_ACCESS_STATUS']}",
        "",
    ]
    return "\n".join(lines)


def render_readiness(record: dict) -> str:
    block = record["readiness"]
    count = record["count_endpoint_constraint_carried_forward"]
    lines = [
        "# Qualified apparatus readiness",
        "",
        "Generated by `infrastructure/scripts/render_documentation_closure.py`. Do not edit.",
        "",
        f"**`{block['status_word']}`.** Qualified `{block['QUALIFIED_APPARATUS_COUNT']}` of a "
        f"threshold of `{block['threshold_for_readiness']}`.",
        "",
        block["why"],
        "",
        "## Apparatuses",
        "",
        _row(["apparatus", "status", "binding failure", "researched"]),
        _row(["---"] * 4),
    ]
    for a in record["apparatuses"]:
        lines.append(
            _row(
                [
                    a["name"],
                    f"`{a['individual_status']}`",
                    a["binding_failure"],
                    "yes" if a["researched_this_mission"] else "",
                ]
            )
        )
    lines += [
        "",
        "## Outcome",
        "",
        f"**`{record['primary_outcome']}`**",
        "",
        record["primary_outcome_statement"],
        "",
        "### Why this outcome and not another",
        "",
    ]
    for key, text in record["why_this_outcome_and_not_another"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines += ["", "### Secondary outcomes", "", _row(["subject", "state"]), _row(["---", "---"])]
    for key, value in record["secondary_outcomes"].items():
        if key.startswith("$"):
            continue
        lines.append(_row([key.replace("_", " "), f"`{value}`"]))
    reg = record["registry_decision"]
    lines += [
        "",
        "## Registry decision",
        "",
        f"{reg['registry_size_before']} → {reg['registry_size_after']}.",
        "",
    ]
    for item in reg["added"]:
        lines += [
            f"### Added `{item['name']}`",
            "",
            item["rule"],
            "",
            f"*Demonstrated by:* {item['demonstrated_by']}",
            "",
            f"*Distinct from:* {item['distinct_from']}",
            "",
        ]
    for item in reg["declined"]:
        lines += [
            f"### Declined `{item['name']}`",
            "",
            item["why_declined"],
            "",
            f"*Recorded instead:* {item['what_was_recorded_instead']}",
            "",
        ]
    nxt = record["next_mission_recommendation"]
    lines += [
        "## Next",
        "",
        f"**`{nxt['checkpoint']}`.** {nxt['the_rule_that_applies']}",
        "",
        nxt["why_contact_rather_than_more_reading"],
        "",
        f"Operative approval string: `{nxt['operative_approval_string']}`",
        "",
        f"*The operator action that unblocks the channel:* "
        f"{nxt['the_operator_action_that_unblocks_the_channel']}",
        "",
        "Three cheap reads that would move the candidate:",
        "",
    ]
    lines += [f"- {i}" for i in nxt["three_cheap_reads_that_would_move_ONYPHE"]]
    lines += [
        "",
        "## No pair work was performed",
        "",
        record["no_pair_work_was_performed"]["why"],
        "",
        "## The negative controls were left alone",
        "",
        record["the_negative_controls_were_left_alone"]["why"],
        "",
        "## Count endpoint constraint",
        "",
        f"`{count['status_word']}`",
        "",
        count["finding"],
        "",
        count["consequence"],
        "",
        f"*Potential future exact route:* {count['potential_future_exact_route']}. Executed this "
        f"mission: **{count['executed_this_mission']}**.",
        "",
        f"Awaiting: **{record['stop_condition']['awaiting']}**.",
        "",
    ]
    return "\n".join(lines)


def render_enquiry(record: dict) -> str:
    artifact = record["artifact"]
    case = record["case"]
    contact = record["contact_channel"]
    lines = [
        "# Mission 1.61 enquiry — reassessment",
        "",
        "Generated by `infrastructure/scripts/render_documentation_closure.py`. Do not edit.",
        "",
        f"**`{case['verdict']}`** — {case['selected']}, {case['definition']}.",
        "",
        f"`{artifact['document']}`, bytes unchanged **{artifact['bytes_unchanged']}**, edited "
        f"**{artifact['edited']}**, sent **{artifact['sent']}**.",
        "",
        f"    sha256  {artifact['sha256']}",
        "",
        "## Question disposition",
        "",
        _row(["#", "topic", "disposition", "note"]),
        _row(["---"] * 4),
    ]
    for d in record["question_disposition"]:
        lines.append(_row([str(d["n"]), d["topic"], f"`{d['disposition']}`", d.get("note", "")]))
    tally = record["tally"]
    lines += [
        "",
        f"Answered by public docs `{tally['answered_by_public_docs']}`, still unresolved "
        f"`{tally['still_unresolved']}`, no longer load bearing "
        f"`{tally['no_longer_load_bearing']}`, of `{tally['total']}`.",
        "",
        f"**{case['consequence']}.** {case['hash_authority']}",
        "",
        f"Operative approval string: `{case['operative_approval_string']}`",
        "",
        "## Why the reads did not touch the enquiry",
        "",
        record["why_the_reads_did_not_touch_the_enquiry"]["explanation"],
        "",
        record["why_the_reads_did_not_touch_the_enquiry"]["what_this_means_for_the_next_step"],
        "",
        "## Contact channel",
        "",
        f"`{contact['status']}`. A contact page exists: <{contact['page']}>.",
        "",
        contact["why_the_address_is_not_recorded"],
        "",
        f"*How it becomes established:* {contact['how_it_becomes_established']}",
        "",
        "## Next action",
        "",
        f"**{record['next_action']['recommended']}.** "
        f"{record['next_action']['why_this_rather_than_more_documentation_search']}",
        "",
        f"Sent automatically: **{record['next_action']['sent_automatically']}**.",
        "",
    ]
    return "\n".join(lines)


RENDERERS = {
    BASELINE: render_baseline,
    INDICES: render_indices,
    TEMPORAL: render_temporal,
    PORTS: render_ports,
    RETENTION: render_retention,
    A8: render_a8,
    PACKAGE: render_package,
    READINESS: render_readiness,
    ENQUIRY: render_enquiry,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  documentation closure: {error}")
        return 1

    rendered = {
        RENDERED[path]: RENDERERS[path](record) for path, record in zip(ORDER, records, strict=True)
    }

    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print(f"ok       {len(rendered)} closure documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    _, indices, temporal, ports, retention, a8, package, readiness, enquiry = records
    print(f"anchor   A8 {a8['verdict']['status_word']}, port window {indices['verdict']['result']}")
    print(
        f"onyphe   B2 {temporal['verdict']['b2_result']} ({temporal['verdict']['record_model']}), "
        f"port 22 {ports['verdict']['result']}, "
        f"retention {retention['verdict']['result']}"
    )
    print(f"package  {package['individual_qualification']['verdict']}")
    print(
        f"ready    {readiness['readiness']['status_word']}, qualified "
        f"{readiness['readiness']['QUALIFIED_APPARATUS_COUNT']}"
    )
    print(f"enquiry  {enquiry['case']['verdict']}, {enquiry['case']['selected']}, unsent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
