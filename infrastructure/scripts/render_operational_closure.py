"""Render and validate the Mission 1.62 anchor closure and partner package records.

Ten records. `validate()` enforces this arc's accumulated refusals plus the two
this mission paid for:

  - what bounds a Claim is the frame the acquisition surface EXPOSES, not the
    frame the apparatus MEASURES;
  - where an apparatus qualifies only through a non-default surface, a collector
    must bind explicitly to that surface, because omitting the selector is silent.

and the ones a later mission would most easily bend: A7 is not evidence about
coverage, sampling silence is not no-sampling, an absent record is not a negative,
a row count is not a distinct-address count, a vendor label is not the raw prefix,
undocumented vantage is not global, a recovered documentation path is not a
qualified apparatus, public documentation is not accessible data, a partial is not
a pass, and a frozen enquiry that no longer answers to its hash is not frozen.

    uv run python infrastructure/scripts/render_operational_closure.py
    uv run python infrastructure/scripts/render_operational_closure.py --check

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

BASELINE = DATA / "anchor-operational-closure-baseline-v1.json"
METHODOLOGY = DATA / "anchor-operational-methodology-v1.json"
SAMPLING = DATA / "anchor-sampling-frame-review-v1.json"
VANTAGE = DATA / "anchor-vantage-review-v1.json"
PORTWINDOW = DATA / "anchor-port-window-review-v1.json"
SHADOWSERVER = DATA / "partner-shadowserver-package-v1.json"
ONYPHE = DATA / "partner-onyphe-package-v1.json"
LEAKIX = DATA / "partner-leakix-package-v1.json"
COMPLETION = DATA / "partner-package-completion-v1.json"
CLOSURE = DATA / "anchor-operational-closure-and-partner-packages-v1.json"

# Mission 1.61's frozen enquiry. Read, hashed, never written.
ENQUIRY_V1_MD = DATA / "anchor-technical-lineage-enquiry-v1.md"
ENQUIRY_V1_JSON = DATA / "anchor-technical-lineage-enquiry-v1.json"

ORDER = [
    BASELINE,
    METHODOLOGY,
    SAMPLING,
    VANTAGE,
    PORTWINDOW,
    SHADOWSERVER,
    ONYPHE,
    LEAKIX,
    COMPLETION,
    CLOSURE,
]
RENDERED = {p: p.with_suffix(".md") for p in ORDER}

GATES = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9")
QUALIFYING = ("PASS", "PASS_WITH_STATED_BOUNDS")
ALL_VERDICTS = QUALIFYING + ("PARTIAL", "UNKNOWN", "FAIL", "NOT_APPLICABLE", "NOT_ESTABLISHED")

B_SLOTS = ("B1", "B2", "B3", "B4", "B5", "B6")
SLOT_STATES = ("PASS", "FAIL", "PARTIAL", "UNKNOWN", "NOT_ESTABLISHED", "NOT_APPLICABLE")

MATRIX_STATES = ("ANSWERED", "PARTIAL", "UNKNOWN", "NOT_APPLICABLE")

SAMPLING_VERDICTS = (
    "NO_SAMPLING_ESTABLISHED",
    "CONDITIONAL_SAMPLING_ESTABLISHED",
    "SAMPLING_ESTABLISHED",
    "SAMPLING_STATUS_UNKNOWN",
)

VANTAGE_VERDICTS = (
    "SINGLE_VANTAGE",
    "MULTI_VANTAGE_MERGED",
    "MULTI_VANTAGE_SEPARABLE",
    "DISTRIBUTED_SCANNER_FLEET",
    "VANTAGE_NOT_DOCUMENTED",
)

PORT_STATES = (
    "PORT_22_CONTINUOUSLY_COVERED",
    "PORT_22_CONFIGURATION_VERSIONED",
    "PORT_22_WINDOW_COVERAGE_QUERYABLE_AS_METADATA",
    "PORT_22_WINDOW_COVERAGE_NOT_ESTABLISHED",
)

EXPOSURE_CLASSES = (
    "RAW_IDENTIFICATION_STRING",
    "STRUCTURED_PROTOCOL_FIELD",
    "DETERMINISTIC_EQUIVALENT",
    "PROPRIETARY_CLASSIFIER_ONLY",
    "NOT_EXPOSED",
    "UNKNOWN",
)
COMPATIBLE_EXPOSURE = EXPOSURE_CLASSES[:3]

LINEAGE_LEVELS = ("LEVEL_0", "LEVEL_1", "LEVEL_2")

INDIVIDUAL_STATES = (
    "INDIVIDUALLY_QUALIFIED",
    "INDIVIDUALLY_NOT_QUALIFIED",
    "INDIVIDUALLY_UNRESOLVED",
)

PARTNERS = ("The Shadowserver Foundation", "ONYPHE", "LeakIX")

PRIMARY_OUTCOMES = {
    "ANCHOR_OPERATIONALLY_REVIEWABLE_PARTNER_PACKAGES_COMPLETE",
    "ANCHOR_ENQUIRY_REQUIRED_PARTNER_PACKAGES_COMPLETE",
    "PARTNER_PACKAGES_COMPLETE_ANCHOR_REVIEWABILITY_GAP",
    "ANCHOR_OPERATIONALLY_REVIEWABLE_PARTNER_PACKAGE_INCOMPLETE",
    "PARTNER_DOCUMENTATION_PACKAGE_COMPLETION_INCOMPLETE",
    "ANCHOR_SAMPLING_FRAME_BLOCKER",
    "ANCHOR_VANTAGE_RELATIVE_POPULATION_BLOCKER",
    "ANCHOR_PROTOCOL_EXPOSURE_REOPENED",
    "PREREGISTRATION_POSSIBILITY_COMPROMISED",
    "MISSION_1_61_NOT_MERGED",
    "MISSION_1_62_BASELINE_DRIFT",
    "MISSION_1_62_CANONICAL_MUTATION",
    "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
    "ANCHOR_OPERATIONAL_AND_PARTNER_PACKAGE_COMPLETION_BLOCKED",
}

# A count of addresses answering on a port is not a market statement.
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

# Words that would name a preference the mission is forbidden to express.
PREFERENCE_WORDS = (
    "best candidate",
    "preferred candidate",
    "strongest partner",
    "lead route",
    "front-runner",
    "front runner",
)

# Addresses nobody published. Guessing one is fabricating a fact about a provider.
GUESSED_ADDRESSES = ("support@", "info@", "security@", "contact@", "abuse@", "hello@")


class ValidationError(Exception):
    """A Mission 1.62 record claims something the rules do not permit."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    return json.loads(path.read_text(encoding="utf-8"))


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _prose(node: object) -> list[str]:
    """Every string except under $-prefixed keys, which carry the rules.

    A rule may name the thing it forbids; a field may not.
    """
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


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def validate() -> tuple[dict, ...]:
    records = tuple(_load(p) for p in ORDER)
    (
        baseline,
        methodology,
        sampling,
        vantage,
        portwindow,
        shadowserver,
        onyphe,
        leakix,
        completion,
        closure,
    ) = records

    _validate_baseline(baseline)
    _validate_methodology(methodology)
    _validate_sampling(sampling)
    _validate_vantage(vantage)
    _validate_port_window(portwindow)
    for pkg in (shadowserver, onyphe, leakix):
        _validate_package(pkg)
    _validate_completion(completion, (shadowserver, onyphe, leakix))
    _validate_closure(closure, methodology, sampling, vantage, portwindow, completion)
    _validate_enquiry_v1_frozen(closure)
    _validate_no_overclaims(records)
    _validate_no_preference(records)
    return records


def _validate_baseline(baseline: dict) -> None:
    pre = baseline["repository_precondition"]
    if pre.get("mission_1_61_merged") is not True:
        raise ValidationError("Mission 1.61 is not recorded as merged")
    if not pre.get("merge_commit", "").strip():
        raise ValidationError("the precondition must name the commit it verified")
    if pre.get("verified_from_git_not_from_prompt") is not True:
        raise ValidationError(
            "the precondition must be verified from git rather than from a prompt"
        )

    scope = baseline["scope_freeze"]
    if tuple(scope["partners"]) != PARTNERS:
        raise ValidationError(f"§17 freezes the partner set to {PARTNERS}")
    if scope.get("new_candidates_evaluated") != 0:
        raise ValidationError("§17: no candidate four may be evaluated")
    if scope.get("candidate_substitutions") != 0:
        raise ValidationError("§17: no candidate may be replaced because it is inconvenient")
    if scope["dropped_apparatus"].get("reconsidered") is not False:
        raise ValidationError("the Mission 1.59 dropped apparatus stays dropped")

    ledger = baseline["documentation_ledger"]
    if ledger["used_total"] != len(ledger["requests"]):
        raise ValidationError("the ledger count and its entries disagree")
    if ledger["used_total"] > ledger["budget_total"]:
        raise ValidationError(
            f"§48 bounds retrieval at {ledger['budget_total']} and the ledger records "
            f"{ledger['used_total']}. Do not silently exceed"
        )
    per_subject = ledger["used_anchor"] + ledger["used_shadowserver"]
    per_subject += ledger["used_onyphe"] + ledger["used_leakix"]
    if per_subject != ledger["used_total"]:
        raise ValidationError("the per-subject retrieval counts do not sum to the total")

    acct = baseline["request_accounting"]
    for name in (
        "RESEARCH_DATA_REQUESTS",
        "MEASUREMENT_QUERIES_EXECUTED",
        "TARGET_COUNTS_FETCHED",
        "TARGET_HOST_RECORDS_FETCHED",
        "TARGET_IPS_FETCHED",
        "TARGET_BANNERS_FETCHED",
        "FACETS_FETCHED",
        "DOWNLOADS_OF_MEASUREMENT_DATA",
        "TRIALS_STARTED",
        "PURCHASES",
        "OUTBOUND_ENQUIRIES_SENT",
    ):
        if acct.get(name) != 0:
            raise ValidationError(f"§49: {name} must be 0 and reads {acct.get(name)!r}")
    if not acct.get("the_count_is_measurement", "").strip():
        raise ValidationError(
            "§39: a query returning only a number still returns a measurement value about the "
            "target population, and the record must refuse the reading that makes it metadata"
        )
    if not acct.get("the_trial_is_not_free", "").strip():
        raise ValidationError(
            "§39: a trial is epistemically contaminating even if free, and the record must say so"
        )

    for name, value in baseline["canonical_mutations"].items():
        if name.startswith("$"):
            continue
        if value not in (0, 0.0, False):
            raise ValidationError(
                f"§51: canonical mutation {name} reads {value!r} and must be zero"
            )


def _validate_methodology(methodology: dict) -> None:
    gate = methodology["what_this_gate_asks"]
    if gate.get("no_value_assigned") is not True:
        raise ValidationError("§16: A8 closure assigns no reliability value")
    if gate.get("reliability_assessments_created") != 0:
        raise ValidationError("§53: no ReliabilityAssessment may be created")
    if not gate.get("a8_reviewable_does_not_mean_reliable", "").strip():
        raise ValidationError(
            "§16: REVIEWABLE means a human can later review reliability. It does not mean reliable, "
            "and the record must say so"
        )

    matrix = methodology["closure_matrix"]
    topics = {row["topic"] for row in matrix}
    for required in (
        "SAMPLING",
        "FRAME",
        "MISSINGNESS",
        "RETRY",
        "DUPLICATION",
        "DISTINCT_ADDRESS_FIELD",
        "BANNER_FIDELITY",
        "SCAN_DATE_SEMANTICS",
        "VANTAGE",
        "PORT_22_WINDOW_COVERAGE",
    ):
        if required not in topics:
            raise ValidationError(f"§15: the closure matrix is missing {required}")
    for row in matrix:
        if row["status"] not in MATRIX_STATES:
            raise ValidationError(f"{row['topic']} carries status {row['status']!r}")
        if row["status"] != "UNKNOWN" and not row.get("first_party_evidence_held", "").strip():
            raise ValidationError(
                f"{row['topic']} is not UNKNOWN and cites no first-party evidence"
            )
        if row["status"] == "UNKNOWN" and not row.get("documents_inspected"):
            raise ValidationError(
                f"§47: {row['topic']} is UNKNOWN and names no documents inspected. An unknown "
                "must record what was read and what was sought"
            )

    tally = methodology["tally"]
    for key, state in (
        ("answered", "ANSWERED"),
        ("partial", "PARTIAL"),
        ("unknown", "UNKNOWN"),
        ("not_applicable", "NOT_APPLICABLE"),
    ):
        counted = sum(1 for r in matrix if r["status"] == state)
        if tally[key] != counted:
            raise ValidationError(
                f"the tally records {tally[key]} {state} and the matrix has {counted}"
            )
    if tally["total"] != len(matrix):
        raise ValidationError("the tally total does not match the matrix length")

    # Sampling silence is never no-sampling.
    sampling_row = next(r for r in matrix if r["topic"] == "SAMPLING")
    if (
        sampling_row["status"] == "ANSWERED"
        and sampling_row.get("verdict") == "NO_SAMPLING_ESTABLISHED"
        and not sampling_row.get("first_party_evidence_held", "").strip()
    ):
        raise ValidationError(
            "§5: NO_SAMPLING_ESTABLISHED requires an affirmative first-party statement. "
            "Silence is SAMPLING_STATUS_UNKNOWN"
        )

    # An absent record is never a definite negative.
    missing_row = next(r for r in matrix if r["topic"] == "MISSINGNESS")
    if (
        not missing_row.get("absence_is_not_a_negative", "").strip()
        and missing_row["status"] != "ANSWERED"
    ):
        raise ValidationError(
            "§7: the missingness row must state that a missing service record is not a definite "
            "negative"
        )

    # A row count is never a distinct-address count.
    distinct_row = next(r for r in matrix if r["topic"] == "DISTINCT_ADDRESS_FIELD")
    consequence = distinct_row.get("consequence", "")
    if "distinct" not in consequence.lower() or "record count" not in consequence.lower():
        raise ValidationError(
            "§9: the distinct-address row must state that the count is over distinct addresses and "
            "never a record count"
        )

    # Banner transformation may not be ignored.
    banner_row = next(r for r in matrix if r["topic"] == "BANNER_FIDELITY")
    if (
        banner_row["status"] in ("ANSWERED",)
        and not banner_row.get("first_party_evidence_held", "").strip()
    ):
        raise ValidationError("§11: banner fidelity cannot be ANSWERED with no evidence")
    if banner_row["status"] != "ANSWERED" and not banner_row.get("missing_fact", "").strip():
        raise ValidationError(
            "§11: an unresolved banner-fidelity row must name the transformation question it "
            "could not answer, rather than passing silently on the field being queryable"
        )

    verdict = methodology["gate_a8_verdict"]
    if verdict["verdict"] not in ALL_VERDICTS:
        raise ValidationError(f"A8 carries verdict {verdict['verdict']!r}")
    unknowns = sum(1 for r in matrix if r["status"] == "UNKNOWN")
    if verdict.get("reviewable") is True and unknowns:
        for tolerated in verdict.get("tolerated_unknowns", []):
            if not tolerated.get("why", "").strip():
                raise ValidationError("§15: every tolerated unknown must be justified")
    if verdict.get("reviewable") is False and not verdict.get("why_not_reviewable", "").strip():
        raise ValidationError("a non-reviewable A8 must say what blocks it")

    if methodology["no_reliability_assigned"].get("value_assigned") is not None:
        raise ValidationError("§53: no reliability value may be assigned")


def _validate_sampling(sampling: dict) -> None:
    verdict = sampling["sampling_verdict"]
    if verdict["result"] not in SAMPLING_VERDICTS:
        raise ValidationError(f"sampling verdict {verdict['result']!r} is not in the vocabulary")
    if verdict["result"] == "NO_SAMPLING_ESTABLISHED" and verdict.get("selected") == "E":
        raise ValidationError(
            "§5: option E is that documentation does not establish it, which is "
            "SAMPLING_STATUS_UNKNOWN. Silence is never mapped to NO_SAMPLING"
        )
    if (
        verdict["result"] == "SAMPLING_STATUS_UNKNOWN"
        and not verdict.get("the_refusal", "").strip()
    ):
        raise ValidationError("§5: the record must state that silence was not read as no-sampling")

    frames = sampling["two_frames"]
    for name in ("ELIGIBLE_FRAME", "ATTEMPTED_FRAME"):
        if name not in frames:
            raise ValidationError(f"§6: {name} must be recorded separately")
    if not frames.get("the_rule", "").strip():
        raise ValidationError(
            "§6: do not call the metric internet-wide merely because the provider does, and the "
            "record must say so"
        )
    if "LINEAGE_EXHAUSTIVENESS_IS_NOT_FRAME_EXHAUSTIVENESS" not in json.dumps(frames):
        raise ValidationError(
            "§6: the frame record must carry the Mission 1.61 rule separating who produced an "
            "observation from which addresses were reached, or A7 will be read as coverage"
        )

    missing = sampling["missingness_semantics"]
    if missing.get("does_this_destroy_the_construct") is not False:
        raise ValidationError(
            "§7: ambiguous negative semantics do not destroy a positive count, because the "
            "construct counts positively observed addresses"
        )
    if not missing.get("the_refusal", "").strip():
        raise ValidationError("§7: an absent record must never be turned into a definite negative")

    outcome = sampling["verdict"]
    if (
        outcome.get("is_this_a_sampling_frame_blocker") is True
        and outcome.get("sampling") == "SAMPLING_STATUS_UNKNOWN"
    ):
        raise ValidationError(
            "§60 outcome F requires documentation ESTABLISHING an incompatibility. An unknown "
            "is an open question, not a refutation"
        )


def _validate_vantage(vantage: dict) -> None:
    cls = vantage["anchor_classification"]
    if cls["verdict"] not in VANTAGE_VERDICTS:
        raise ValidationError(f"vantage verdict {cls['verdict']!r} is not in the vocabulary")
    if cls["verdict"] == "VANTAGE_NOT_DOCUMENTED":
        if not cls.get("documents_inspected_this_mission"):
            raise ValidationError("§12: NOT_DOCUMENTED means somebody looked, and must say where")
        if not cls.get("record_side_check", {}):
            raise ValidationError(
                "§12: the record schema must be checked too, because vantage recoverable from a "
                "retrieved record would be a different answer"
            )

    needs = vantage["does_the_proposition_need_scanner_identity"]
    if needs["answer"] not in ("YES", "NO", "NOT_ESTABLISHED"):
        raise ValidationError("the scanner-identity question must be answered from the vocabulary")
    if needs["answer"] == "NO" and cls["verdict"] == "VANTAGE_NOT_DOCUMENTED":
        raise ValidationError(
            "§12: undocumented vantage may not be silently treated as global. Answering NO asserts "
            "vantage-independence, which is a positive claim nothing documents"
        )
    if (
        needs.get("is_this_a_vantage_relative_population_blocker") is True
        and cls["verdict"] == "VANTAGE_NOT_DOCUMENTED"
    ):
        raise ValidationError(
            "§60 outcome G requires documentation ESTABLISHING that vantage must enter the "
            "proposition. An absence establishes nothing"
        )
    if "FRAME_INSIDE_THE_DEFINITION" not in json.dumps(vantage["the_trap_this_guards"]):
        raise ValidationError(
            "§12: the record must name the Mission 1.57 trap vantage would recreate"
        )


def _validate_port_window(portwindow: dict) -> None:
    verdict = portwindow["verdict"]
    if verdict["window_coverage_of_port_22"] not in PORT_STATES:
        raise ValidationError("the port-window verdict is not in the vocabulary")
    if not verdict.get("these_are_two_answers_and_not_one", "").strip():
        raise ValidationError(
            "§41: current inclusion and window coverage are two answers, and the record must "
            "refuse to promote the first into the second"
        )
    if verdict.get("no_absence_reasoning_used") is not True:
        raise ValidationError("§41: absence-of-removal reasoning is forbidden outright")

    findings = portwindow["findings"]
    removals = findings["removals"]
    if removals["status"] == "NONE_RECORDED" and not removals.get("what_this_is_not", "").strip():
        raise ValidationError(
            "§41: an absence of recorded removals does not prove continued inclusion, and the "
            "record must say so"
        )
    if (
        verdict["window_coverage_of_port_22"] == "PORT_22_CONTINUOUSLY_COVERED"
        and findings["current_inclusion"]["status"] == "ESTABLISHED"
        and findings["configuration_versioning"]["status"] != "ESTABLISHED"
    ):
        raise ValidationError(
            "§41: today's port list is not proof of coverage in an arbitrary window. "
            "CONTINUOUSLY_COVERED needs a documented invariant or a dated coverage record"
        )
    if not portwindow["how_future_window_coverage_could_be_established"].get(
        "admissible_mechanisms"
    ):
        raise ValidationError(
            "§14: the record must name how future window coverage could be established"
        )
    for flag in ("no_window_selected", "no_query_executed", "no_threshold_chosen"):
        if portwindow["how_future_window_coverage_could_be_established"].get(flag) is not True:
            raise ValidationError(f"§14: {flag} must hold")


def _validate_package(pkg: dict) -> None:
    name = pkg["apparatus"]
    if name not in PARTNERS:
        raise ValidationError(f"§17: {name!r} is not one of the three frozen candidates")
    if not pkg.get("documentation_paths_used"):
        raise ValidationError(f"{name}: a package must name the documentation it rests on")

    package = pkg["package"]
    for slot in B_SLOTS:
        if slot not in package:
            raise ValidationError(f"{name}: slot {slot} was not assessed")
        entry = package[slot]
        if entry.get("status") not in SLOT_STATES:
            raise ValidationError(f"{name}: slot {slot} carries status {entry.get('status')!r}")
        has_basis = bool(entry.get("basis", "").strip())
        has_absence_reason = bool(
            entry.get("not_pursued_further", "").strip() or entry.get("fact_sought", "").strip()
        )
        if not has_basis and not has_absence_reason:
            raise ValidationError(
                f"§46/§47: {name} slot {slot} has neither a first-party basis nor an explicit "
                "absence-of-proof reason. A blank slot is not a complete package"
            )
        if entry.get("classification") and entry["classification"] not in EXPOSURE_CLASSES:
            raise ValidationError(
                f"{name}: slot {slot} exposure class {entry['classification']!r} is not in the vocabulary"
            )
        if (
            slot == "B3"
            and entry.get("status") == "PASS"
            and entry.get("classification") not in COMPATIBLE_EXPOSURE
        ):
            raise ValidationError(
                f"§26: {name} B3 passes on exposure class {entry.get('classification')!r}. "
                "Only a raw identification string, a structured protocol field or a proven "
                "deterministic equivalent may carry the protocol metric"
            )
        if entry.get("lineage_level") and entry["lineage_level"] not in LINEAGE_LEVELS:
            raise ValidationError(f"{name}: slot {slot} lineage level is not in the vocabulary")
        if entry.get("lineage_level") == "LEVEL_2" and not entry.get("closed_exception_clause"):
            raise ValidationError(
                f"§25: {name} slot {slot} claims LEVEL 2 with no closed exception clause. An "
                "open-ended source list is not exhaustive lineage however confident it sounds"
            )

    completion = pkg["package_completion"]
    if completion["status"] == "PACKAGE_COMPLETE":
        if completion.get("unread_slots") != 0:
            raise ValidationError(f"§47: {name} is complete with unread slots")
        if completion.get("slots_with_explicit_status") != len(B_SLOTS):
            raise ValidationError(f"§46: {name} does not carry an explicit status in every slot")

    qual = pkg["individual_qualification"]
    if qual["verdict"] not in INDIVIDUAL_STATES:
        raise ValidationError(
            f"{name}: individual verdict {qual['verdict']!r} is not in the vocabulary"
        )

    hard_fails = [s for s in B_SLOTS if package[s]["status"] == "FAIL"]
    all_pass = all(package[s]["status"] == "PASS" for s in B_SLOTS)
    if hard_fails and qual["verdict"] != "INDIVIDUALLY_NOT_QUALIFIED":
        raise ValidationError(
            f"§30: {name} carries a hard FAIL at {hard_fails} and is not recorded "
            "INDIVIDUALLY_NOT_QUALIFIED. A single hard FAIL ends it"
        )
    if qual["verdict"] == "INDIVIDUALLY_QUALIFIED" and not all_pass:
        raise ValidationError(
            f"§30: {name} is recorded qualified without every slot passing. A partial is not a "
            "pass and an unknown is not a pass"
        )
    if not qual.get("reason", "").strip():
        raise ValidationError(f"{name}: the individual verdict states no reason")

    # Documentation being public is not data being accessible.
    if "epistemic_documentation_status" in qual or "future_access_status" in qual:
        for field in ("epistemic_documentation_status", "future_access_status"):
            if not qual.get(field, "").strip():
                raise ValidationError(
                    f"§21: {name} records one of the two access statuses and not the other. "
                    "Documentation being public says nothing about whether retrieval is"
                )

    # A recovered documentation path is not a qualified apparatus.
    if (
        completion["status"] == "PACKAGE_COMPLETE"
        and qual["verdict"] == "INDIVIDUALLY_QUALIFIED"
        and not all_pass
    ):
        raise ValidationError(
            f"§24: {name} treats a complete package as qualification. COMPLETE means every "
            "slot has an answer; QUALIFIED means every slot passes"
        )

    # Retention truncation may not be quietly dropped.
    retention = pkg.get("thirty_day_retention_and_truncation")
    if retention is not None:
        if retention.get("does_this_disqualify") is None:
            raise ValidationError(
                f"§42: {name} records a retention bound without deciding its effect"
            )
        if (
            retention.get("which_fields_are_removed") not in ("UNKNOWN",)
            and not retention.get("which_fields_are_removed", "").strip()
        ):
            raise ValidationError(
                f"§22: {name} must state which fields are removed or record UNKNOWN"
            )
        if not retention.get("MAX_FULL_FIDELITY_RETRIEVAL_DELAY", "").strip():
            raise ValidationError(f"§42: {name} must record MAX_FULL_FIDELITY_RETRIEVAL_DELAY")


def _validate_completion(completion: dict, packages: tuple[dict, ...]) -> None:
    contract = completion["one_contract_for_all_four"]
    for flag in (
        "conjunctive",
        "partial_is_not_pass",
        "unknown_is_not_pass",
        "one_hard_fail_ends_it",
    ):
        if contract.get(flag) is not True:
            raise ValidationError(f"§30/§32: the contract must hold {flag}")
    for slot in B_SLOTS:
        if slot not in contract["slots"]:
            raise ValidationError(f"§32: the shared contract omits {slot}")

    listed = {p["apparatus"]: p for p in completion["packages"]}
    if set(listed) != set(PARTNERS):
        raise ValidationError("§17: the roll-up does not cover exactly the three frozen candidates")
    for pkg in packages:
        name = pkg["apparatus"]
        rolled = listed[name]
        if rolled["individual_status"] != pkg["individual_qualification"]["verdict"]:
            raise ValidationError(f"{name}: the roll-up and the package disagree on the verdict")
        if rolled["package_status"] != pkg["package_completion"]["status"]:
            raise ValidationError(f"{name}: the roll-up and the package disagree on completeness")
        for slot in B_SLOTS:
            if rolled["slots"][slot] != pkg["package"][slot]["status"]:
                raise ValidationError(f"{name}: the roll-up and the package disagree on {slot}")

    tally = completion["tally"]
    for key, state in (
        ("individually_qualified", "INDIVIDUALLY_QUALIFIED"),
        ("individually_unresolved", "INDIVIDUALLY_UNRESOLVED"),
        ("individually_not_qualified", "INDIVIDUALLY_NOT_QUALIFIED"),
    ):
        counted = sum(1 for p in completion["packages"] if p["individual_status"] == state)
        if tally[key] != counted:
            raise ValidationError(
                f"the tally records {tally[key]} {state} and the packages give {counted}"
            )
    counted_complete = sum(
        1 for p in completion["packages"] if p["package_status"] == "PACKAGE_COMPLETE"
    )
    if tally["packages_complete"] != counted_complete:
        raise ValidationError("the completeness tally disagrees with the packages")

    meaning = completion["what_complete_means_and_does_not"]
    if not meaning.get("complete_does_not_mean_qualified", "").strip():
        raise ValidationError(
            "§46: the record must state that a complete package may conclude NOT_QUALIFIED, and "
            "that this is success"
        )
    if not meaning.get("no_silent_unknown", "").strip():
        raise ValidationError("§47: the record must refuse a silent unknown")

    pair = completion["no_pair_work"]
    for flag in (
        "same_frame_evaluated",
        "vantage_compatibility_evaluated",
        "pair_independence_evaluated",
        "shared_measurement_upstream_evaluated",
        "pair_time_contract_evaluated",
        "same_proposition_key_evaluated",
        "tie_break_applied",
    ):
        if pair.get(flag) is not False:
            raise ValidationError(f"§31: {flag} must be false. Pair gates are Mission 1.63's work")
    for counter in ("pair_comparisons_performed", "pairs_ranked", "pairs_selected"):
        if pair.get(counter) != 0:
            raise ValidationError(f"§31/§45: {counter} must be 0")
    if not pair.get("no_preference_expressed", "").strip():
        raise ValidationError("§45: the record must state that no preference was expressed")


def _validate_closure(
    closure: dict,
    methodology: dict,
    sampling: dict,
    vantage: dict,
    portwindow: dict,
    completion: dict,
) -> None:
    if closure["primary_outcome"] not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {closure['primary_outcome']!r}")
    if not closure.get("primary_outcome_statement", "").strip():
        raise ValidationError("the outcome must be stated in a sentence, not only as a label")

    secondary = closure["secondary_outcomes"]
    if secondary["SAMPLING"] != sampling["sampling_verdict"]["result"]:
        raise ValidationError("the closure and the sampling record disagree")
    if secondary["ANCHOR_VANTAGE"] != vantage["anchor_classification"].get("status_word"):
        raise ValidationError("the closure and the vantage record disagree")
    if secondary["PORT_22"] != portwindow["verdict"].get("status_word"):
        raise ValidationError("the closure and the port-window record disagree")
    if secondary["ANCHOR_A8"] != methodology["gate_a8_verdict"].get("status_word"):
        raise ValidationError("the closure and the methodology record disagree about A8")
    for name in PARTNERS:
        if name not in secondary["partners"]:
            raise ValidationError(f"§59: the closure does not report {name} individually")

    outcome = closure["primary_outcome"]
    complete = completion["tally"]["packages_complete"] == completion["tally"]["packages_of"]
    reviewable = methodology["gate_a8_verdict"].get("reviewable") is True
    if outcome == "ANCHOR_OPERATIONALLY_REVIEWABLE_PARTNER_PACKAGES_COMPLETE" and not (
        reviewable and complete
    ):
        raise ValidationError(
            "§60 outcome A requires A8 REVIEWABLE and all three packages COMPLETE. Do NOT force A"
        )
    if outcome == "ANCHOR_ENQUIRY_REQUIRED_PARTNER_PACKAGES_COMPLETE":
        if not complete:
            raise ValidationError("§60 outcome B requires all three packages COMPLETE")
        if reviewable:
            raise ValidationError(
                "§60 outcome B requires the anchor to still need a provider answer"
            )
        if closure["enquiry_v1_disposition"]["verdict"] not in (
            "V1_REMAINS_CURRENT",
        ) and not closure["enquiry_v1_disposition"].get("v2_created"):
            raise ValidationError("§60 outcome B requires a current frozen enquiry to exist")

    table = closure["anchor_gate_table"]
    for gate in GATES:
        if table[gate]["verdict"] not in ALL_VERDICTS:
            raise ValidationError(f"anchor gate {gate} carries verdict {table[gate]['verdict']!r}")
    blocking = [g for g in GATES if table[g]["verdict"] not in QUALIFYING]
    if table["which_gates_block"] != blocking:
        raise ValidationError("which_gates_block disagrees with the gate verdicts")
    if table["individually_qualifies"] != (not blocking):
        raise ValidationError("§30: an apparatus qualifies exactly when nothing blocks it")
    if table["A7"]["verdict"] != "PASS":
        raise ValidationError(
            "A7 passed at LEVEL 2 in Mission 1.61. It may only be reopened on documentation that "
            "CONTRADICTS the closed exception clause"
        )
    if table["A2"]["verdict"] in QUALIFYING and not table["A2"].get("bound", "").strip():
        raise ValidationError(
            "§11: A2 passes on a non-default surface and the gate table must carry that bound"
        )

    a7 = closure["a7_was_not_reopened"]
    if a7.get("contradictory_lineage_evidence_found") is not False:
        raise ValidationError(
            "contradictory lineage evidence is recorded and A7 still reads PASS. Resolve it"
        )
    if not a7.get("a7_was_not_used_as_proof_of_anything_else", "").strip():
        raise ValidationError(
            "the record must state that A7 was not cited as evidence about sampling, coverage or "
            "the attempted frame"
        )

    bound = closure["the_a2_bound_restated_with_new_evidence"]
    for word in (
        "OBSERVATION_ADDRESSABLE_PATH_REQUIRED",
        "DEFAULT_CURRENT_STATE_PATH_PROHIBITED_FOR_THIS_CONTRACT",
    ):
        if word not in bound["status_words"]:
            raise ValidationError(f"§11: the A2 bound must carry {word}")
    if bound.get("not_weakened") is not True:
        raise ValidationError("§11: the A2 bound may not be weakened")

    contact = closure["contact_channel"]
    if contact.get("no_address_invented") is not True:
        raise ValidationError("§34/§38: no contact address may be invented")
    for guess in GUESSED_ADDRESSES:
        if guess in json.dumps(contact.get("what_was_found", "")):
            raise ValidationError(f"§34: the record names a guessed address form {guess!r}")
    if contact.get("TECHNICAL_ENQUIRY_REQUIRED") is True and not contact.get("status", "").strip():
        raise ValidationError(
            "§38: a valid question and a valid channel are two different facts, and both must be "
            "recorded"
        )

    registry = closure["new_requirements_for_the_registry"]
    for item in registry["requirements"]:
        for field in ("name", "from", "rule", "demonstrated_by", "distinct_from"):
            if not item.get(field, "").strip():
                raise ValidationError(
                    f"§55: registry entry {item.get('name')!r} states no {field}. A rule is added "
                    "only where the artifacts prove it adds a distinct guard"
                )
    if registry["registry_size_after"] - registry["registry_size_before"] != len(
        registry["requirements"]
    ):
        raise ValidationError("the registry size change does not match the entries added")

    counters = closure["counters"]
    for name in (
        "research_data_requests",
        "measurement_queries_executed",
        "target_counts_fetched",
        "target_host_records_fetched",
        "target_ips_fetched",
        "target_banners_fetched",
        "facets_fetched",
        "downloads_of_measurement_data",
        "trials_started",
        "purchases",
        "outbound_enquiries_sent",
        "model_calls",
        "embeddings",
        "canonical_mutations",
        "sources_registered",
        "governance_reviews_created",
        "threshold_registrations_created",
        "claims_created",
        "evidence_created",
        "reliability_assessments_created",
        "independence_groups_created",
        "scores_created",
        "opportunity_changes",
    ):
        if counters.get(name) != 0:
            raise ValidationError(f"§51: counter {name} reads {counters.get(name)!r} and must be 0")
    if counters.get("reference_profile") != "UNCALIBRATED":
        raise ValidationError("§54: the reference profile stays UNCALIBRATED")
    if counters.get("problem_family") != "PARKED":
        raise ValidationError("§54: Problem-Family stays PARKED")

    for name, value in closure["stop_condition"].items():
        if name.startswith("$") or name == "awaiting":
            continue
        if value is not False:
            raise ValidationError(
                f"the stop condition {name} reads {value!r} and every one must be false"
            )


def _validate_enquiry_v1_frozen(closure: dict) -> None:
    """Mission 1.61's enquiry is read and hashed here, and never written."""
    disposition = closure["enquiry_v1_disposition"]
    if disposition.get("edited") is not False:
        raise ValidationError("§35: enquiry v1 is never edited")
    if disposition.get("bytes_unchanged") is not True:
        raise ValidationError("§35: enquiry v1's bytes must be unchanged")

    if not ENQUIRY_V1_MD.exists():
        raise ValidationError("the frozen Mission 1.61 enquiry is missing")
    digest = hashlib.sha256(ENQUIRY_V1_MD.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    if digest != disposition["sha256"]:
        raise ValidationError(
            f"§35: the frozen enquiry v1 no longer answers to its hash. recorded "
            f"{disposition['sha256']}, computed {digest}. A frozen document that no longer answers "
            "to the hash it was frozen at is not frozen"
        )

    v1 = _load(ENQUIRY_V1_JSON)
    if v1.get("status") != "AWAITING_OPERATOR_APPROVAL":
        raise ValidationError("§35: enquiry v1's status was changed")
    if v1["delivery"].get("sent") is not False or v1["delivery"].get("sent_at") is not None:
        raise ValidationError("§37: the enquiry has not been sent and must not say otherwise")

    questions = {q["topic"] for q in v1["questions"]}
    disposed = {d["topic"] for d in disposition["question_disposition"]}
    if questions != disposed:
        raise ValidationError(
            "§35: every question in the frozen enquiry must receive a disposition, and no other"
        )
    for d in disposition["question_disposition"]:
        if d["disposition"] not in (
            "STILL_UNRESOLVED",
            "ANSWERED_BY_PUBLIC_DOCS",
            "NO_LONGER_LOAD_BEARING",
        ):
            raise ValidationError(f"question {d['n']} carries disposition {d['disposition']!r}")

    unresolved = sum(
        1 for d in disposition["question_disposition"] if d["disposition"] == "STILL_UNRESOLVED"
    )
    if disposition["still_unresolved"] != unresolved:
        raise ValidationError("the disposition tally disagrees with the questions")

    if unresolved == len(disposition["question_disposition"]):
        if disposition["verdict"] != "V1_REMAINS_CURRENT":
            raise ValidationError("§35: if no question disappears, v1 remains current")
        if disposition.get("v2_created") is not False:
            raise ValidationError(
                "§35: a v2 is created only when SOME questions disappear. None did"
            )
        if disposition["sha256"] not in disposition.get("operative_approval_string", ""):
            raise ValidationError(
                "§37: if v1 remains current, Mission 1.61's exact hash stays authoritative and no "
                "duplicate is manufactured"
            )
    elif unresolved == 0:
        if disposition["verdict"] != "NOT_NEEDED":
            raise ValidationError("§35: if all questions disappear, v1 is marked NOT_NEEDED")
    else:
        if disposition["verdict"] != "SUPERSEDED_BEFORE_SEND":
            raise ValidationError("§35: if some questions disappear, v1 is SUPERSEDED_BEFORE_SEND")
        if disposition.get("v2_created") is not True:
            raise ValidationError("§35: a supersession requires a v2 carrying only the remainder")


def _validate_no_overclaims(records: tuple[dict, ...]) -> None:
    for record in records:
        for sentence in _prose(record):
            tokens = _tokens(sentence)
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
                        f"§33: a record uses {term!r}. A count of addresses answering on a port is "
                        f"not a market statement. Offending sentence: {sentence[:110]!r}"
                    )


def _validate_no_preference(records: tuple[dict, ...]) -> None:
    for record in records:
        for sentence in _prose(record):
            lowered = sentence.lower()
            for word in PREFERENCE_WORDS:
                if word in lowered:
                    raise ValidationError(
                        f"§45: a record uses {word!r}. Mission 1.62 completes individual packages "
                        f"and expresses no preference. Offending sentence: {sentence[:110]!r}"
                    )


# --------------------------------------------------------------------------- render


def render_baseline(record: dict) -> str:
    pre = record["repository_precondition"]
    base = record["canonical_baseline"]
    ledger = record["documentation_ledger"]
    acct = record["request_accounting"]

    lines = [
        "# Anchor operational closure — baseline",
        "",
        "Generated by `infrastructure/scripts/render_operational_closure.py`. Do not edit.",
        "",
        f"**Mission:** {record['mission']}  ",
        f"**Recorded:** {record['recorded_at']}",
        "",
        "## Precondition",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["Mission 1.61 merged", str(pre["mission_1_61_merged"])]),
        _row(["merge commit", f"`{pre['merge_commit']}`"]),
        _row(["local main == origin/main", str(pre["local_main_equals_origin_main"])]),
        _row(["branch", f"`{pre['branch']}`"]),
        _row(["migration head", f"`{pre['migration_head']}`"]),
        _row(["ADR-036 / 037 / 038", f"{pre['adr_036']} / {pre['adr_037']} / {pre['adr_038']}"]),
        "",
        "## Canonical baseline",
        "",
        _row(["counter", "value"]),
        _row(["---", "---"]),
    ]
    for key in (
        "raw_records",
        "normalized_records",
        "signals",
        "claims",
        "claim_revisions",
        "evidence",
        "inferred_claims",
        "threshold_registrations",
        "claim_derivations",
        "proposition_evaluation_refusals",
        "reliability_assessments_current",
        "independence_groups",
        "claims_carrying_both_directions",
        "opportunity_evidence_links",
        "registered_sources",
        "embeddings",
    ):
        lines.append(_row([f"`{key}`", str(base[key])]))
    directions = ", ".join(f"{k} {v}" for k, v in base["evidence_directions"].items())
    lines += [
        _row(["evidence directions", directions]),
        _row(["`scoring.scores` exists", str(base["scoring_scores_table_exists"])]),
        _row(["drift from Mission 1.61", f"**{base['drift_from_mission_1_61']}**"]),
        "",
        "## Frozen scope",
        "",
        f"Anchor **{record['scope_freeze']['anchor']}**, and the exact three carried candidates:",
        "",
    ]
    lines += [f"- {n}" for n in record["scope_freeze"]["partners"]]

    corr = record["brief_attribution_correction"]
    lines += [
        "",
        "## A correction the artifact forced",
        "",
        corr["resolution"],
        "",
        _row(["blocker", "brief said", "artifact says"]),
        _row(["---", "---", "---"]),
        _row(
            [
                "vetted / private API",
                corr["brief_said"]["vetted_private_api_blocker"],
                f"**{corr['artifact_says']['vetted_private_api_blocker']}**",
            ]
        ),
        _row(
            [
                "30-day field removal",
                corr["brief_said"]["thirty_day_field_removal_blocker"],
                f"**{corr['artifact_says']['thirty_day_field_removal_blocker']}**",
            ]
        ),
        "",
        corr["why_this_is_recorded"],
        "",
        "## Documentation ledger",
        "",
        f"{ledger['used_total']} of {ledger['budget_total']} retrievals — anchor "
        f"{ledger['used_anchor']}, Shadowserver {ledger['used_shadowserver']}, "
        f"ONYPHE {ledger['used_onyphe']}, LeakIX {ledger['used_leakix']}. "
        f"{ledger['unusable_responses']} returned nothing usable and are counted anyway.",
        "",
        _row(["#", "subject", "sought", "usable"]),
        _row(["---", "---", "---", "---"]),
    ]
    for entry in ledger["requests"]:
        lines.append(
            _row(
                [
                    str(entry["n"]),
                    entry["subject"],
                    entry["sought"],
                    "yes" if entry["usable"] else f"no ({entry.get('note', '')})",
                ]
            )
        )
    lines += [
        "",
        "## What did not happen",
        "",
        "```",
        f"measurement queries   {acct['MEASUREMENT_QUERIES_EXECUTED']}"
        f"        trials       {acct['TRIALS_STARTED']}",
        f"target counts         {acct['TARGET_COUNTS_FETCHED']}"
        f"        purchases    {acct['PURCHASES']}",
        f"host records          {acct['TARGET_HOST_RECORDS_FETCHED']}"
        f"        facets       {acct['FACETS_FETCHED']}",
        f"banners               {acct['TARGET_BANNERS_FETCHED']}"
        f"        enquiries    {acct['OUTBOUND_ENQUIRIES_SENT']}",
        "```",
        "",
        acct["the_count_is_measurement"],
        "",
        acct["the_trial_is_not_free"],
        "",
    ]
    return "\n".join(lines)


def render_methodology(record: dict) -> str:
    verdict = record["gate_a8_verdict"]
    tally = record["tally"]
    lines = [
        "# Anchor operational methodology — gate A8",
        "",
        "Generated by `infrastructure/scripts/render_operational_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Verdict:** `{verdict['status_word']}`, reviewable **{verdict['reviewable']}**",
        "",
        f"`{tally['answered']}` answered, `{tally['partial']}` partial, `{tally['unknown']}` "
        f"unknown, of `{tally['total']}`.",
        "",
        record["what_this_gate_asks"]["a8_reviewable_does_not_mean_reliable"],
        "",
        "## Closure matrix",
        "",
        _row(["topic", "was", "now", "in enquiry v1"]),
        _row(["---", "---", "---", "---"]),
    ]
    for row in record["closure_matrix"]:
        lines.append(
            _row(
                [
                    row["topic"],
                    f"`{row['previous_status']}`",
                    f"`{row['status']}`",
                    "yes" if row.get("in_enquiry_v1") else "no",
                ]
            )
        )
    lines += ["", "## Findings", ""]
    for row in record["closure_matrix"]:
        lines += [f"### {row['topic']} — `{row['status']}`", ""]
        if row.get("first_party_evidence_held"):
            lines += [row["first_party_evidence_held"], ""]
        if row.get("missing_fact"):
            lines += [f"*Missing:* {row['missing_fact']}", ""]
        for key in (
            "why_load_bearing",
            "consequence",
            "the_distinction_that_must_not_be_lost",
            "silence_is_not_an_answer",
            "absence_is_not_a_negative",
            "downgraded_from_answered",
            "why_not_promoted",
        ):
            if row.get(key):
                lines += [f"*{key.replace('_', ' ')}:* {row[key]}", ""]

    lines += ["## Retrieval-surface facts established this mission", ""]
    for key, item in record["retrieval_surface_facts_established_this_mission"].items():
        if key.startswith("$"):
            continue
        lines += [f"### {key.replace('_', ' ')} — `{item['status']}`", "", item["finding"], ""]
        for sub in ("why_this_is_load_bearing", "consequence", "not_a_disqualification"):
            if item.get(sub):
                lines += [f"*{sub.replace('_', ' ')}:* {item[sub]}", ""]

    lines += [
        "## Verdict",
        "",
        f"**Why not reviewable.** {verdict['why_not_reviewable']}",
        "",
        f"**Why not NOT_REVIEWABLE.** {verdict['why_not_NOT_REVIEWABLE']}",
        "",
        f"**What moved.** {verdict['what_moved_this_mission']}",
        "",
        "### Tolerated unknowns",
        "",
        _row(["topic", "tolerated", "why"]),
        _row(["---", "---", "---"]),
    ]
    for item in verdict["tolerated_unknowns"]:
        lines.append(_row([item["topic"], str(item["tolerated"]), item["why"]]))
    lines += ["", record["no_reliability_assigned"]["statement"], ""]
    return "\n".join(lines)


def render_sampling(record: dict) -> str:
    verdict = record["sampling_verdict"]
    frames = record["two_frames"]
    missing = record["missingness_semantics"]
    final = record["verdict"]
    lines = [
        "# Anchor sampling and frame review",
        "",
        "Generated by `infrastructure/scripts/render_operational_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Sampling:** `{verdict['result']}`",
        "",
        record["why_sampling_is_the_first_question"]["rule"],
        "",
        "## Sampling",
        "",
        _row(["option", "meaning"]),
        _row(["---", "---"]),
    ]
    for key, text in verdict["options_considered"].items():
        marker = " **(selected)**" if key == verdict["selected"] else ""
        lines.append(_row([f"`{key}`{marker}", text]))
    lines += [
        "",
        verdict["first_party_evidence_held"],
        "",
        f"*What that does not say:* {verdict['what_that_evidence_does_not_say']}",
        "",
        f"**The refusal.** {verdict['the_refusal']}",
        "",
        "## Two frames",
        "",
        _row(["frame", "status", "definition"]),
        _row(["---", "---", "---"]),
        _row(
            [
                "eligible",
                f"`{frames['ELIGIBLE_FRAME']['status']}`",
                frames["ELIGIBLE_FRAME"]["definition"],
            ]
        ),
        _row(
            [
                "attempted",
                f"`{frames['ATTEMPTED_FRAME']['status']}`",
                frames["ATTEMPTED_FRAME"]["definition_sought"],
            ]
        ),
        "",
        frames["the_rule"],
        "",
        frames["relation_to_A7"],
        "",
        "## Missingness",
        "",
        f"`{missing['status']}`. {missing.get('why_not_inferred', '')}",
        "",
        "Candidate meanings, none of which is documented:",
        "",
    ]
    lines += [f"- `{m}`" for m in missing["candidate_meanings_none_of_which_is_documented"]]
    lines += [
        "",
        f"**Does this destroy the construct?** {missing['does_this_destroy_the_construct']}. "
        f"{missing['why_not']}",
        "",
        f"**The refusal.** {missing['the_refusal']}",
        "",
        "## Exclusions and opt-out",
        "",
        f"`{record['exclusions_and_opt_out']['status']}`. {record['exclusions_and_opt_out']['finding']}",
        "",
        record["exclusions_and_opt_out"]["why_it_matters"],
        "",
        "## Verdict",
        "",
        _row(["question", "state"]),
        _row(["---", "---"]),
        _row(["sampling", f"`{final['sampling']}`"]),
        _row(["eligible frame", f"`{final['eligible_frame']}`"]),
        _row(["attempted frame", f"`{final['attempted_frame']}`"]),
        _row(["missingness", f"`{final['missingness']}`"]),
        _row(["exclusions", f"`{final['exclusions']}`"]),
        "",
        f"**Is this a sampling/frame blocker?** {final['is_this_a_sampling_frame_blocker']}. "
        f"{final['why_not']}",
        "",
        f"*What would make it one:* {final['what_would_make_it_a_blocker']}",
        "",
    ]
    return "\n".join(lines)


def render_vantage(record: dict) -> str:
    cls = record["anchor_classification"]
    needs = record["does_the_proposition_need_scanner_identity"]
    lines = [
        "# Anchor vantage review",
        "",
        "Generated by `infrastructure/scripts/render_operational_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Verdict:** `{cls['verdict']}`, moved **{cls['moved']}**",
        "",
        cls["why_it_did_not_move"] if not cls["moved"] else "",
        "",
        "## Vocabulary",
        "",
        _row(["term", "meaning"]),
        _row(["---", "---"]),
    ]
    for term in VANTAGE_VERDICTS:
        lines.append(_row([f"`{term}`", record["classification_vocabulary"][term]]))
    check = cls["record_side_check"]
    lines += [
        "",
        "## Record-side check",
        "",
        check["finding"],
        "",
        f"**The near miss that was refused.** {check['the_near_miss_that_was_refused']}",
        "",
        f"*Consequence:* {check['consequence']}",
        "",
        "## Does the proposition need scanner identity?",
        "",
        f"**`{needs['answer']}`**",
        "",
        f"*Why not YES:* {needs['why_not_YES']}",
        "",
        f"*Why not NO:* {needs['why_not_NO']}",
        "",
        needs["consequence"],
        "",
        f"**Vantage-relative population blocker?** "
        f"{needs['is_this_a_vantage_relative_population_blocker']}. {needs['why_not_blocker']}",
        "",
        "## The trap this guards",
        "",
        f"`{record['the_trap_this_guards']['name']}`, from "
        f"{record['the_trap_this_guards']['from']}. {record['the_trap_this_guards']['rule']}",
        "",
        record["the_trap_this_guards"]["how_it_would_recur_here"],
        "",
        "## A contrast, recorded without preference",
        "",
        record["the_contrast_recorded_without_preference"]["finding"],
        "",
        f"*What this is not:* {record['the_contrast_recorded_without_preference']['what_this_is_not']}",
        "",
    ]
    return "\n".join(lines)


def render_port_window(record: dict) -> str:
    verdict = record["verdict"]
    lines = [
        "# Anchor port-window review — port 22",
        "",
        "Generated by `infrastructure/scripts/render_operational_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Current inclusion:** `{verdict['current_inclusion_of_port_22']}`  ",
        f"**Window coverage:** `{verdict['window_coverage_of_port_22']}`",
        "",
        verdict["these_are_two_answers_and_not_one"],
        "",
        "## Findings",
        "",
        _row(["question", "status", "finding"]),
        _row(["---", "---", "---"]),
    ]
    for key, item in record["findings"].items():
        lines.append(_row([key.replace("_", " "), f"`{item['status']}`", item["finding"]]))
    removals = record["findings"]["removals"]
    lines += [
        "",
        f"**On removals.** {removals['what_this_is']} {removals['what_this_is_not']}",
        "",
        "## How future window coverage could be established",
        "",
        _row(["mechanism", "status", "cost"]),
        _row(["---", "---", "---"]),
    ]
    for m in record["how_future_window_coverage_could_be_established"]["admissible_mechanisms"]:
        lines.append(_row([m["mechanism"], m["status"], m["cost"]]))
    cost = record["what_this_costs_the_route"]
    lines += [
        "",
        "## What this costs the route",
        "",
        f"- **blocks a threshold** — {cost['does_it_block_a_threshold']}. {cost['why_not']}",
        f"- **what it costs** — {cost['what_it_costs']}",
        f"- **bound carried** — {cost['the_bound_that_must_be_carried']}",
        f"- **forward risk** — `{cost['forward_risk']}`. {cost['why_low']} {cost['why_uncommitted']}",
        "",
    ]
    return "\n".join(lines)


def render_package(record: dict) -> str:
    name = record["apparatus"]
    completion = record["package_completion"]
    qual = record["individual_qualification"]
    lines = [
        f"# Partner package — {name}",
        "",
        "Generated by `infrastructure/scripts/render_operational_closure.py`. Do not edit.",
        "",
        f"**`{completion['status']}`** → **`{qual['verdict']}`**",
        "",
        qual["reason"],
        "",
        "## Documentation used",
        "",
    ]
    lines += [f"- <{p}>" for p in record["documentation_paths_used"]]
    lines += [
        "",
        "## Package",
        "",
        _row(["slot", "requirement", "status"]),
        _row(["---", "---", "---"]),
    ]
    slot_names = {
        "B1": "ACTIVE_MEASUREMENT_PRODUCER",
        "B2": "OBSERVATION_ADDRESSABLE_EXPOSURE",
        "B3": "PROTOCOL_NATIVE_EXPOSURE",
        "B4": "FRAME",
        "B5": "LINEAGE",
        "B6": "RELIABILITY_REVIEWABILITY",
    }
    for slot in B_SLOTS:
        entry = record["package"][slot]
        lines.append(_row([slot, slot_names[slot], f"`{entry['status']}`"]))
    lines += ["", "## Slot findings", ""]
    for slot in B_SLOTS:
        entry = record["package"][slot]
        lines += [f"### {slot} {slot_names[slot]} — `{entry['status']}`", ""]
        if entry.get("basis"):
            lines += [entry["basis"], ""]
        for key in (
            "classification",
            "lineage_level",
            "temporal_object",
            "missing_fact",
            "why_this_is_a_FAIL",
            "why_this_is_a_FAIL_and_not_an_UNKNOWN",
            "why_not_promoted",
            "why_not_LEVEL_2",
            "resource_specific_lineage",
            "the_ambiguity_that_decides_it",
            "not_resolved_favourably",
            "the_failure_reproduced",
            "why_a_range_query_does_not_rescue_it",
            "not_recorded_as_UNKNOWN",
            "what_it_means_for_the_construct",
            "not_pursued_further",
            "fact_sought",
            "note_recorded_honestly",
            "recorded_even_though_the_package_fails",
            "the_caution_that_survives",
            "why_this_qualifies",
            "resolves_the_mission_1_61_risk_partly",
            "sampling",
            "exclusions",
            "port_22_membership",
        ):
            if entry.get(key):
                value = entry[key]
                if isinstance(value, list):
                    value = "; ".join(value)
                lines += [f"*{key.replace('_', ' ')}:* {value}", ""]
        if entry.get("missing_facts"):
            lines += ["*missing facts:* " + "; ".join(entry["missing_facts"]), ""]

    for extra_key, heading in (
        ("port_22_relevance", "Port 22 relevance"),
        ("vantage", "Vantage"),
        ("thirty_day_retention_and_truncation", "Retention and truncation"),
        ("scope_concern", "Scope concern"),
        ("the_reusable_rule_this_paid_for", "The reusable rule this paid for"),
    ):
        block = record.get(extra_key)
        if not block:
            continue
        lines += [f"## {heading}", ""]
        for key, value in block.items():
            if key.startswith("$"):
                continue
            if isinstance(value, list):
                value = "; ".join(str(v) for v in value)
            lines.append(f"- **{key.replace('_', ' ')}** — {value}")
        lines.append("")

    lines += [
        "## Qualification",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["package", f"`{completion['status']}`"]),
        _row(
            [
                "slots with an explicit status",
                f"{completion['slots_with_explicit_status']} of {completion['slots_total']}",
            ]
        ),
        _row(["unread slots", str(completion["unread_slots"])]),
        _row(["individual", f"`{qual['verdict']}`"]),
        "",
    ]
    for key in (
        "the_shape_of_the_failure",
        "not_a_documentation_gap",
        "not_a_judgement_on_the_organisation",
        "governance_not_invoked",
        "epistemic_documentation_status",
        "future_access_status",
        "these_two_are_recorded_separately",
    ):
        if qual.get(key):
            lines += [f"**{key.replace('_', ' ')}.** {qual[key]}", ""]
    if qual.get("what_would_resolve_it"):
        lines += ["**What would resolve it:**", ""]
        lines += [f"- {item}" for item in qual["what_would_resolve_it"]]
        lines.append("")
    return "\n".join(lines)


def render_completion(record: dict) -> str:
    tally = record["tally"]
    lines = [
        "# Partner package completion",
        "",
        "Generated by `infrastructure/scripts/render_operational_closure.py`. Do not edit.",
        "",
        f"**{tally['packages_complete']} of {tally['packages_of']} packages complete.** "
        f"Qualified `{tally['individually_qualified']}`, unresolved "
        f"`{tally['individually_unresolved']}`, not qualified "
        f"`{tally['individually_not_qualified']}`.",
        "",
        "## One contract for all four",
        "",
        record["one_contract_for_all_four"]["rule"],
        "",
        _row(["slot", "requirement"]),
        _row(["---", "---"]),
    ]
    for slot in B_SLOTS:
        lines.append(_row([f"`{slot}`", record["one_contract_for_all_four"]["slots"][slot]]))
    lines += [
        "",
        "## Packages",
        "",
        _row(["apparatus", *B_SLOTS, "package", "individual"]),
        _row(["---"] * 9),
    ]
    for p in record["packages"]:
        lines.append(
            _row(
                [p["apparatus"]]
                + [f"`{p['slots'][s]}`" for s in B_SLOTS]
                + [f"`{p['package_status']}`", f"`{p['individual_status']}`"]
            )
        )
    lines += ["", "### Decided by", ""]
    for p in record["packages"]:
        lines.append(f"- **{p['apparatus']}** — {p['decided_by']}")
    meaning = record["what_complete_means_and_does_not"]
    shape = record["the_shape_of_the_result"]
    lines += [
        "",
        "## What complete means",
        "",
        meaning["complete_means"],
        "",
        f"**{meaning['complete_does_not_mean_qualified']}**",
        "",
        meaning["no_silent_unknown"],
        "",
        "## The shape of the result",
        "",
        shape["the_three_failed_differently"],
        "",
        shape["two_failures_are_permanent_and_one_is_not"],
        "",
        f"**{shape['the_recurring_gate']}**",
        "",
        "## No pair work",
        "",
        record["no_pair_work"]["why"],
        "",
        record["no_pair_work"]["no_preference_expressed"],
        "",
        "## Product relevance",
        "",
        f"Construct: *{record['product_relevance']['construct']}*",
        "",
    ]
    for name, text in record["product_relevance"]["per_apparatus"].items():
        lines.append(f"- **{name}** — {text}")
    lines.append("")
    return "\n".join(lines)


def render_closure(record: dict) -> str:
    table = record["anchor_gate_table"]
    disposition = record["enquiry_v1_disposition"]
    contact = record["contact_channel"]
    counters = record["counters"]
    lines = [
        "# Anchor operational closure and partner packages",
        "",
        "Generated by `infrastructure/scripts/render_operational_closure.py`. Do not edit.",
        "",
        f"**Outcome: `{record['primary_outcome']}`**",
        "",
        record["primary_outcome_statement"],
        "",
        "## Secondary outcomes",
        "",
        _row(["subject", "state"]),
        _row(["---", "---"]),
        _row(["anchor A7", f"`{record['secondary_outcomes']['ANCHOR_A7']}`"]),
        _row(["anchor A8", f"`{record['secondary_outcomes']['ANCHOR_A8']}`"]),
        _row(["anchor vantage", f"`{record['secondary_outcomes']['ANCHOR_VANTAGE']}`"]),
        _row(["port 22", f"`{record['secondary_outcomes']['PORT_22']}`"]),
        _row(["sampling", f"`{record['secondary_outcomes']['SAMPLING']}`"]),
    ]
    for name, states in record["secondary_outcomes"]["partners"].items():
        lines.append(_row([name, " → ".join(f"`{s}`" for s in states)]))
    lines += ["", "## Why this outcome and not another", ""]
    for key, text in record["why_this_outcome_and_not_another"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines += [
        "",
        "## Anchor gate table",
        "",
        _row(["gate", "verdict", "note"]),
        _row(["---", "---", "---"]),
    ]
    for gate in GATES:
        item = table[gate]
        note = item.get("bound") or item.get("level") or item.get("exposure_class") or ""
        lines.append(_row([gate, f"`{item['verdict']}`", note]))
    lines += [
        "",
        f"Blocks **{table['which_gates_block']}**. Individually qualifies: "
        f"**{table['individually_qualifies']}**.",
        "",
        "## A7 was not reopened",
        "",
        record["a7_was_not_reopened"]["verdict"],
        "",
        record["a7_was_not_reopened"]["a7_was_not_used_as_proof_of_anything_else"],
        "",
        "## The A2 bound, restated with new evidence",
        "",
        record["the_a2_bound_restated_with_new_evidence"]["new_evidence"],
        "",
        f"Admissible: {record['the_a2_bound_restated_with_new_evidence']['admissible_path']}.  ",
        f"Prohibited: {record['the_a2_bound_restated_with_new_evidence']['prohibited_path']}.",
        "",
        "## Enquiry v1",
        "",
        f"`{disposition['artifact']}`, bytes unchanged **{disposition['bytes_unchanged']}**, "
        f"edited **{disposition['edited']}**.",
        "",
        f"    sha256  {disposition['sha256']}",
        "",
        _row(["#", "topic", "disposition"]),
        _row(["---", "---", "---"]),
    ]
    for d in disposition["question_disposition"]:
        lines.append(_row([str(d["n"]), d["topic"], f"`{d['disposition']}`"]))
    lines += [
        "",
        f"**Verdict: `{disposition['verdict']}`.** {disposition['why_no_v2']}",
        "",
        disposition["hash_authority"],
        "",
        f"Operative approval string: `{disposition['operative_approval_string']}`",
        "",
        "## Contact channel",
        "",
        f"`{contact['status']}`. Technical enquiry required: "
        f"**{contact['TECHNICAL_ENQUIRY_REQUIRED']}**.",
        "",
        contact["what_was_found"],
        "",
        f"*Why not established:* {contact['why_not_established']}",
        "",
        f"*What the operator can do:* {contact['what_the_operator_can_do']}",
        "",
        "## New requirements for the registry",
        "",
    ]
    for item in record["new_requirements_for_the_registry"]["requirements"]:
        lines += [
            f"### `{item['name']}`",
            "",
            f"*From {item['from']}.* {item['rule']}",
            "",
            f"*Demonstrated by:* {item['demonstrated_by']}",
            "",
            f"*Distinct from:* {item['distinct_from']}",
            "",
        ]
    lines += [
        "## Counters",
        "",
        "```",
        f"first-party document requests  {counters['first_party_document_requests']} of {counters['budget']}",
        f"measurement queries            {counters['measurement_queries_executed']}"
        f"        trials      {counters['trials_started']}",
        f"target counts                  {counters['target_counts_fetched']}"
        f"        purchases   {counters['purchases']}",
        f"host records                   {counters['target_host_records_fetched']}"
        f"        facets      {counters['facets_fetched']}",
        f"enquiries sent                 {counters['outbound_enquiries_sent']}"
        f"        created     {counters['enquiries_created']}",
        "```",
        "",
        "0 canonical mutations, 0 sources registered, 0 governance reviews, 0 threshold "
        "registrations, 0 Claims, 0 Evidence, 0 reliability values, 0 independence groups, "
        "0 Scores, 0 model calls, 0 embeddings. The Mission 1.56 Claim is untouched, the profile "
        f"is still {counters['reference_profile']}, Problem-Family is still "
        f"{counters['problem_family']}.",
        "",
        "## Next",
        "",
        f"**`{record['next_mission_recommendation']['checkpoint']}`.** "
        f"{record['next_mission_recommendation']['why']}",
        "",
        record["next_mission_recommendation"]["a8_was_not_weakened"],
        "",
        f"**{record['next_mission_recommendation']['name']}** should:",
        "",
    ]
    lines += [f"- {item}" for item in record["next_mission_recommendation"]["it_should"]]
    lines += ["", "It must not:", ""]
    lines += [f"- {item}" for item in record["next_mission_recommendation"]["it_must_not"]]
    lines += ["", f"Awaiting: **{record['stop_condition']['awaiting']}**.", ""]
    return "\n".join(lines)


RENDERERS = {
    BASELINE: render_baseline,
    METHODOLOGY: render_methodology,
    SAMPLING: render_sampling,
    VANTAGE: render_vantage,
    PORTWINDOW: render_port_window,
    SHADOWSERVER: render_package,
    ONYPHE: render_package,
    LEAKIX: render_package,
    COMPLETION: render_completion,
    CLOSURE: render_closure,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = validate()
    except ValidationError as error:
        print(f"REFUSED  operational closure: {error}")
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
        closure = records[-1]
        print(
            f"ok       {len(rendered)} closure documents match their records; "
            f"outcome {closure['primary_outcome']}"
        )
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")

    closure = records[-1]
    completion = records[8]
    methodology = records[1]
    print(f"outcome  {closure['primary_outcome']}")
    print(
        f"anchor   A7 {closure['anchor_gate_table']['A7']['verdict']}, "
        f"A8 {methodology['gate_a8_verdict']['status_word']}, "
        f"blocks {closure['anchor_gate_table']['which_gates_block']}"
    )
    print(
        f"partners {completion['tally']['packages_complete']} complete, "
        f"{completion['tally']['individually_qualified']} qualified, "
        f"{completion['tally']['individually_unresolved']} unresolved, "
        f"{completion['tally']['individually_not_qualified']} not qualified"
    )
    print(f"enquiry  {closure['enquiry_v1_disposition']['verdict']}, unsent, v1 hash authoritative")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
