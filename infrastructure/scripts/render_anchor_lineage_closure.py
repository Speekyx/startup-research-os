"""Render and validate the Mission 1.61 anchor lineage and partner recovery records.

Seven records plus one drafted enquiry. `validate()` enforces the rules a later
mission would most easily bend, and they are this arc's accumulated refusals with
two new ones this mission paid for:

  - an affirmative lineage statement is exhaustive only if its exceptions are
    ENUMERATED and closed, and each enumerated exception has been checked against
    the load-bearing predicate one by one;
  - lineage exhaustiveness is not frame exhaustiveness, so a lineage sentence may
    never be cited for coverage;
  - a DEFAULT surface can be the rejected temporal object while the apparatus
    passes the gate on a non-default mechanism, and the record must say which;
  - a partial is not a pass, an absence is not a statement, and a recovered
    documentation path is not a qualified apparatus;
  - a drafted enquiry is not evidence, and a frozen document that no longer
    answers to its hash is not frozen.

    uv run python infrastructure/scripts/render_anchor_lineage_closure.py
    uv run python infrastructure/scripts/render_anchor_lineage_closure.py --check

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

BASELINE = DATA / "anchor-documentation-confirmation-baseline-v1.json"
LINEAGE = DATA / "anchor-lineage-review-v1.json"
OPERATIONAL = DATA / "anchor-operational-reviewability-v1.json"
VANTAGE = DATA / "anchor-vantage-model-v1.json"
PORTWINDOW = DATA / "anchor-port-window-coverage-v1.json"
PARTNERS = DATA / "partner-documentation-recovery-v1.json"
CLOSURE = DATA / "anchor-lineage-and-documentation-closure-v1.json"
ENQUIRY = DATA / "anchor-technical-lineage-enquiry-v1.json"

RENDERED = {
    BASELINE: DATA / "anchor-documentation-confirmation-baseline-v1.md",
    LINEAGE: DATA / "anchor-lineage-review-v1.md",
    OPERATIONAL: DATA / "anchor-operational-reviewability-v1.md",
    VANTAGE: DATA / "anchor-vantage-model-v1.md",
    PORTWINDOW: DATA / "anchor-port-window-coverage-v1.md",
    PARTNERS: DATA / "partner-documentation-recovery-v1.md",
    CLOSURE: DATA / "anchor-lineage-and-documentation-closure-v1.md",
    ENQUIRY: DATA / "anchor-technical-lineage-enquiry-v1.md",
}

INDIVIDUAL_GATES = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9")
QUALIFYING_VERDICTS = ("PASS", "PASS_WITH_STATED_BOUNDS")
ALL_VERDICTS = QUALIFYING_VERDICTS + ("PARTIAL", "UNKNOWN", "FAIL", "NOT_APPLICABLE")

LINEAGE_LEVELS = ("LEVEL_0", "LEVEL_1", "LEVEL_2")
ANSWER_STATES = ("ANSWERED", "PARTIALLY_ANSWERED", "NOT_ANSWERED")

VANTAGE_VERDICTS = (
    "MULTI_VANTAGE_DOCUMENTED",
    "SINGLE_VANTAGE_DOCUMENTED",
    "VANTAGE_NOT_DOCUMENTED",
    "VANTAGE_NOT_ESTABLISHED",
)

PORT_STATES = (
    "PORT_22_CONTINUOUSLY_COVERED",
    "PORT_22_VERSIONED_BY_DATE",
    "PORT_22_QUERYABLE_AS_METADATA",
    "PORT_22_NOT_ESTABLISHED",
)

REJECTED_TIME_OBJECT = "MAINTAINED_CURRENT_STATE_LAST_CHANGE"

B_SLOTS = ("B1", "B2", "B3", "B4", "B5", "B6")

# The exact three candidates Mission 1.60 left at a documentation wall. Section 1
# freezes the scope, so a fourth name appearing here is a scope breach.
MISSION_1_60_PARTNERS = ("The Shadowserver Foundation", "ONYPHE", "LeakIX")

PRIMARY_OUTCOMES = {
    "ANCHOR_LINEAGE_CONFIRMED_OPERATIONAL_QUESTIONS_REMAIN",
    "ANCHOR_LINEAGE_CONFIRMED_AND_APPARATUS_QUALIFIED",
    "ANCHOR_LINEAGE_NOT_CONFIRMED",
    "ANCHOR_LINEAGE_REFUTED",
    "ANCHOR_APPARATUS_INVALIDATED",
    "PARTNER_DOCUMENTATION_NOT_RECOVERABLE",
    "MISSION_1_60_NOT_MERGED",
    "MISSION_1_61_BASELINE_DRIFT",
    "MISSION_1_61_CANONICAL_MUTATION",
}

# Vocabulary that would turn a scan record into a market statement.
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

# An enquiry may ask about method. It may not ask for the thing itself.
FORBIDDEN_ASKS = (
    "how many hosts",
    "send us a sample",
    "provide a count",
    "free trial",
    "trial account",
    "evaluation account",
    "pricing",
    "a quote",
    "api key",
)


class ValidationError(Exception):
    """A Mission 1.61 record claims something the rules do not permit."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    return json.loads(path.read_text(encoding="utf-8"))


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _prose(node: object) -> list[str]:
    """Every string in a record except the $comment keys, which carry the rules.

    A rule may name the thing it forbids; a field may not. Mission 1.36 met this
    four times before the fix was generalised, so it is generalised here too.
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


def enquiry_hash() -> str:
    """sha256 of the RENDERED enquiry, which is the document that would be sent."""
    return hashlib.sha256(render_enquiry(_load(ENQUIRY)).encode("utf-8")).hexdigest()


def validate() -> tuple[dict, ...]:
    records = (
        _load(BASELINE),
        _load(LINEAGE),
        _load(OPERATIONAL),
        _load(VANTAGE),
        _load(PORTWINDOW),
        _load(PARTNERS),
        _load(CLOSURE),
        _load(ENQUIRY),
    )
    baseline, lineage, operational, vantage, portwindow, partners, closure, enquiry = records

    _validate_baseline(baseline)
    _validate_lineage(lineage)
    _validate_operational(operational)
    _validate_vantage(vantage)
    _validate_port_window(portwindow)
    _validate_partners(partners)
    _validate_closure(closure, lineage, operational)
    _validate_enquiry(enquiry, operational)
    _validate_no_overclaims(records)
    return records


def _validate_baseline(baseline: dict) -> None:
    pre = baseline["repository_precondition"]
    if pre.get("mission_1_60_merged") is not True:
        raise ValidationError("Mission 1.60 is not recorded as merged")
    if not pre.get("merge_commit", "").strip():
        raise ValidationError("the precondition must name the commit it verified")

    scope = baseline["scope_freeze"]
    if scope.get("subject_count") != 1 + len(scope.get("partners", [])):
        raise ValidationError("§1: the subject count and the named subjects disagree")
    if tuple(scope["partners"]) != MISSION_1_60_PARTNERS:
        raise ValidationError(
            "§1 freezes the scope to the anchor and the exact three Mission 1.60 partners. "
            f"expected {MISSION_1_60_PARTNERS}, found {tuple(scope['partners'])}"
        )
    if scope.get("new_candidates_evaluated") != 0:
        raise ValidationError("§1: no new candidate may be evaluated in this mission")

    dropped = scope["dropped_apparatus"]
    if dropped.get("status") != "DROPPED_FOR_THIS_ROUTE":
        raise ValidationError("§1: the Mission 1.59 current-state apparatus stays dropped")
    if dropped.get("reconsidered") is not False:
        raise ValidationError(
            "§1 forbids reviving the dropped apparatus, whose temporal mismatch is an established "
            "fact rather than an unknown a new document could resolve"
        )

    ledger = baseline["documentation_ledger"]
    if ledger["used_total"] != len(ledger["requests"]):
        raise ValidationError("the ledger count and its entries disagree")
    for subject, used_key, budget_key in (
        ("anchor", "used_anchor", "budget_anchor"),
        ("partner", "used_partners", "budget_partners"),
        ("overall", "used_total", "budget_total"),
    ):
        if ledger[used_key] > ledger[budget_key]:
            raise ValidationError(
                f"§27 bounds {subject} retrievals at {ledger[budget_key]}, "
                f"and the ledger records {ledger[used_key]}"
            )
    counted_anchor = sum(1 for e in ledger["requests"] if e["subject"] == "anchor")
    if counted_anchor != ledger["used_anchor"]:
        raise ValidationError("the anchor retrieval count and its entries disagree")
    if counted_anchor + ledger["used_partners"] != ledger["used_total"]:
        raise ValidationError("the per-subject counts do not sum to the total")

    for name in (
        "research_data_requests",
        "target_measurement_requests",
        "target_host_record_requests",
        "target_count_requests",
        "facets_fetched",
        "queries_executed",
        "trials_started",
        "purchases",
    ):
        if ledger.get(name) != 0:
            raise ValidationError(f"§60: {name} must be 0 and reads {ledger.get(name)!r}")

    for entry in ledger["requests"]:
        if entry.get("load_bearing") and not entry.get("first_party"):
            raise ValidationError(
                f"request {entry['n']} closes a gate on a non-first-party source. "
                "No mirror, cached copy or third-party summary may stand in for a first-party "
                "document"
            )

    exposure = baseline["value_exposure"]
    if exposure.get("target_measurement_retrieved") is not False:
        raise ValidationError(
            "§33: a target measurement was retrieved. PREREGISTERED is defined against RETRIEVAL, "
            "so one value fetched here makes an honest preregistration impossible for ever"
        )
    if exposure.get("trials_started") != 0:
        raise ValidationError(
            "a zero-cost trial destroys preregistration exactly as a paid one would, because "
            "access cost is irrelevant to epistemic contamination"
        )
    if not exposure.get("the_count_is_not_metadata", "").strip():
        raise ValidationError(
            "§6: a query returning only a count still returns a measurement value, and the record "
            "must refuse the reading that makes it metadata"
        )

    mutations = baseline["canonical_mutations"]
    for name, value in mutations.items():
        if name.startswith("$"):
            continue
        if value not in (0, 0.0, False):
            raise ValidationError(
                f"§60: canonical mutation {name} reads {value!r} and must be zero"
            )


def _validate_lineage(lineage: dict) -> None:
    two = lineage["two_exhaustiveness_questions_that_are_not_one"]
    if two["LINEAGE_EXHAUSTIVENESS"].get("answered_here") is not True:
        raise ValidationError("§3: the lineage question is this record's subject")
    if two["SCAN_OR_FRAME_EXHAUSTIVENESS"].get("answered_here") is not False:
        raise ValidationError(
            "§3: frame exhaustiveness is gate A5 and is NOT answered here. A lineage sentence "
            "cited for coverage is the overstatement this arc keeps refusing"
        )
    if not two.get("the_distinction_that_must_survive", "").strip():
        raise ValidationError(
            "§3: the record must state that A7 asks WHO produced the observation and A5 asks "
            "WHICH addresses were reached"
        )

    levels = lineage["evidence_levels"]
    for level in LINEAGE_LEVELS:
        if not levels.get(level, "").strip():
            raise ValidationError(f"§4: evidence level {level} is undefined")
    if "ABSENCE" not in levels["LEVEL_0"].upper():
        raise ValidationError(
            "§4: LEVEL 0 must name itself an absence. An absence of a reference to third-party "
            "data is an absence, not a statement"
        )

    verdict = lineage["gate_a7_verdict"]
    if verdict["verdict"] not in ALL_VERDICTS:
        raise ValidationError(f"A7 carries verdict {verdict['verdict']!r}")
    if verdict.get("level_reached") not in LINEAGE_LEVELS:
        raise ValidationError("A7 must record which evidence level it reached")

    level2 = lineage["level_2_evidence"]
    if verdict["verdict"] in QUALIFYING_VERDICTS:
        if verdict["level_reached"] != "LEVEL_2":
            raise ValidationError(
                "§4: A7 may only pass at LEVEL 2. A LEVEL 1 statement asserts own scanning "
                "without excluding an external measurement feed, which is what "
                "AFFIRMATIVE_LINEAGE_REQUIRED asks about"
            )
        if level2.get("achieved") is not True:
            raise ValidationError("A7 passes at LEVEL 2 while the LEVEL 2 evidence is not achieved")
        for field in ("verbatim_affirmative_statement", "verbatim_exception_clause"):
            if not level2.get(field, "").strip():
                raise ValidationError(
                    f"§5: LEVEL 2 rests on {field}, quoted verbatim rather than paraphrased"
                )
        if level2.get("exception_list_is_closed") is not True:
            raise ValidationError(
                "§5: an exception list that does not end cannot establish exhaustiveness. "
                "ENUMERATED_EXCEPTIONS_MAKE_A_LINEAGE_CLAIM_CHECKABLE"
            )
        if not level2.get("why_closed", "").strip():
            raise ValidationError("the record must say what makes the exception list closed")
        if verdict.get("affirmative_not_inferred") is not True:
            raise ValidationError(
                "§5: A7 may not pass on an inference. The apparatus states the positive claim, "
                "or the gate stays PARTIAL"
            )

    check = lineage["do_the_exceptions_touch_the_load_bearing_predicate"]
    if not check.get("load_bearing_predicate", "").strip():
        raise ValidationError("§6: the check must name the predicate it checked against")
    exceptions = check["exceptions"]
    if not exceptions:
        raise ValidationError(
            "§6: a closed exception list with no exceptions listed cannot have been checked"
        )
    for item in exceptions:
        if "bears_on_predicate" not in item:
            raise ValidationError(
                f"exception {item.get('name')!r} was not checked against the predicate. "
                "An enumerated exception is only harmless once somebody has looked at what it names"
            )
        if item["bears_on_predicate"] and verdict["verdict"] in QUALIFYING_VERDICTS:
            raise ValidationError(
                f"exception {item['name']!r} bears on the load-bearing predicate, so A7 cannot pass"
            )
        if not item.get("why", "").strip():
            raise ValidationError(f"exception {item['name']!r} states no reasoning")

    bounds = lineage["bounds_on_this_finding"]
    for required in (
        "it_is_not_an_independent_verification",
        "it_is_not_a_coverage_claim",
        "it_is_not_a_reliability_value",
        "it_is_not_independence_from_a_partner",
    ):
        if not bounds.get(required, "").strip():
            raise ValidationError(f"§7: the record must state that {required}")


def _validate_operational(operational: dict) -> None:
    if operational.get("what_this_gate_is_and_is_not", {}).get("no_value_assigned") is not True:
        raise ValidationError(
            "§9: A8 decides whether a reliability review COULD be performed. No value is assigned "
            "here, and none may be"
        )
    if operational["what_this_gate_is_and_is_not"].get("reliability_assessments_created") != 0:
        raise ValidationError("§60: no reliability assessment may be created")

    questions = operational["eleven_questions"]
    if len(questions) != 11:
        raise ValidationError(f"§9 asks eleven operational questions, found {len(questions)}")
    if [q["n"] for q in questions] != list(range(1, 12)):
        raise ValidationError("the eleven questions must be numbered 1 to 11 in order")

    topics = {q["question"].split(".")[0].strip().upper() for q in questions}
    for required in ("SAMPLING", "VANTAGE", "RETRIES", "FRAME", "PORT COVERAGE"):
        if required not in topics:
            raise ValidationError(f"§9: the {required} question is missing")

    seen = {"ANSWERED": 0, "PARTIALLY_ANSWERED": 0, "NOT_ANSWERED": 0}
    for q in questions:
        if q["status"] not in ANSWER_STATES:
            raise ValidationError(f"question {q['n']} carries status {q['status']!r}")
        seen[q["status"]] += 1
        if q["status"] != "NOT_ANSWERED" and not q.get("source_url", "").strip():
            raise ValidationError(
                f"question {q['n']} is answered and names no document. An answer with no source "
                "is a recollection"
            )
        if not q.get("finding", "").strip():
            raise ValidationError(f"question {q['n']} records no finding")

    tally = operational["tally"]
    if tally["total"] != 11:
        raise ValidationError("the tally must cover all eleven questions")
    for key, state in (
        ("answered", "ANSWERED"),
        ("partially_answered", "PARTIALLY_ANSWERED"),
        ("not_answered", "NOT_ANSWERED"),
    ):
        if tally[key] != seen[state]:
            raise ValidationError(
                f"the tally records {tally[key]} {state} and the questions record {seen[state]}"
            )
    if sum(seen.values()) != tally["total"]:
        raise ValidationError("the tally does not sum to its total")

    sampling = next(q for q in questions if q["question"].upper().startswith("SAMPLING"))
    if sampling["status"] != "NOT_ANSWERED" and "SAMPLING_IS_LOAD_BEARING" not in json.dumps(
        sampling
    ):
        raise ValidationError(
            "§9: if sampling is recorded as answered the record must carry the Mission 1.59 "
            "requirement it satisfies, because a sampled population is not a census"
        )

    verdict = operational["gate_a8_verdict"]
    if verdict["verdict"] not in ALL_VERDICTS:
        raise ValidationError(f"A8 carries verdict {verdict['verdict']!r}")
    if verdict["verdict"] in QUALIFYING_VERDICTS and seen["NOT_ANSWERED"]:
        raise ValidationError(
            f"§10: A8 cannot pass while {seen['NOT_ANSWERED']} of the eleven questions are "
            "unanswered. A partial is not a pass"
        )
    if verdict["verdict"] == "PARTIAL" and not verdict.get("why_not_FAIL", "").strip():
        raise ValidationError(
            "§10: a PARTIAL must say why it is not a FAIL. Nothing retrieved contradicting "
            "reviewability is a different state from documentation refusing it"
        )

    bound = operational["a2_bound_discovered_this_mission"]
    if REJECTED_TIME_OBJECT not in json.dumps(bound):
        raise ValidationError(
            "§14: the default-surface finding must name MAINTAINED_CURRENT_STATE_LAST_CHANGE, "
            "because that is the temporal object Mission 1.59 rejected and the default surface "
            "is one"
        )
    if (
        bound.get("does_a2_still_pass") is True
        and not bound.get("the_bound_that_must_be_carried", "").strip()
    ):
        raise ValidationError(
            "§14: if A2 still passes, the record must carry the bound forward. A collector using "
            "the default surface would read the rejected temporal object while a record elsewhere "
            "said the gate had passed"
        )


def _validate_vantage(vantage: dict) -> None:
    vocab = vantage["classification_vocabulary"]
    for term in VANTAGE_VERDICTS:
        if not vocab.get(term, "").strip():
            raise ValidationError(f"§15: the vantage term {term} is undefined")

    classification = vantage["anchor_classification"]
    if classification["verdict"] not in VANTAGE_VERDICTS:
        raise ValidationError(
            f"vantage verdict {classification['verdict']!r} is not in the vocabulary"
        )
    if classification["verdict"] == "VANTAGE_NOT_DOCUMENTED":
        if not classification.get("documents_consulted"):
            raise ValidationError(
                "§16: NOT_DOCUMENTED means somebody looked. Without the documents consulted it is "
                "NOT_ESTABLISHED, which is a different fact"
            )
        if not classification.get("record_side_check", "").strip():
            raise ValidationError(
                "§16: the record schema must be checked too, because vantage recoverable from a "
                "retrieved record would be a different answer"
            )
    if (
        classification["verdict"]
        in (
            "MULTI_VANTAGE_DOCUMENTED",
            "SINGLE_VANTAGE_DOCUMENTED",
        )
        and not classification.get("what_the_documentation_says", "").strip()
    ):
        raise ValidationError("a documented vantage must quote what documents it")

    why = vantage["why_vantage_is_asked_before_pairing"]
    if "FRAME_INSIDE_THE_DEFINITION" not in json.dumps(why):
        raise ValidationError(
            "§15: the record must name the Mission 1.57 trap vantage would recreate, where each "
            "apparatus measures the hosts reachable from its own network"
        )


def _validate_port_window(portwindow: dict) -> None:
    vocab = portwindow["classification_vocabulary"]
    for state in PORT_STATES:
        if not vocab.get(state, "").strip():
            raise ValidationError(f"§40: the port coverage state {state} is undefined")

    verdict = portwindow["verdict"]
    if verdict["window_addressability_of_port_22"] not in PORT_STATES:
        raise ValidationError("the port-window verdict is not in the vocabulary")
    if not verdict.get("these_are_two_answers_and_not_one", "").strip():
        raise ValidationError(
            "§41: current inclusion and window addressability are two answers. Reporting only the "
            "first would let a windowed count be read as instrument-stable"
        )

    findings = portwindow["findings"]
    removals = findings["removals"]
    if removals["status"] == "NONE_RECORDED" and not removals.get("what_this_is_not", "").strip():
        raise ValidationError(
            "§41: an absence of recorded removals is an absence. It is evidence about the past "
            "and never a guarantee about the future, and the record must say so"
        )
    if (
        verdict["window_addressability_of_port_22"] == "PORT_22_QUERYABLE_AS_METADATA"
        and findings["queryable_scan_metadata"]["status"] != "ESTABLISHED"
    ):
        raise ValidationError(
            "the verdict claims queryable scan metadata and the finding does not establish it"
        )
    if (
        verdict["window_addressability_of_port_22"] == "PORT_22_VERSIONED_BY_DATE"
        and findings["dated_expansion_record"]["status"] != "ESTABLISHED"
    ):
        raise ValidationError(
            "the verdict claims a dated port record and the finding records it as partial. "
            "A dated SIZE is not a dated MEMBERSHIP"
        )


def _validate_partners(partners: dict) -> None:
    entries = partners["partners"]
    if tuple(p["name"] for p in entries) != MISSION_1_60_PARTNERS:
        raise ValidationError(
            "§18 freezes the partner set to the exact three Mission 1.60 candidates. "
            f"expected {MISSION_1_60_PARTNERS}"
        )

    package = partners["the_minimum_package"]
    for slot in B_SLOTS:
        if not package.get(slot, "").strip():
            raise ValidationError(f"§20: minimum package slot {slot} is undefined")

    for entry in entries:
        name = entry["name"]
        if entry.get("b6_previous") != "DOCUMENTATION_NOT_RETRIEVABLE":
            raise ValidationError(f"{name}: Mission 1.60 recorded B6 as not retrievable")
        for slot in B_SLOTS:
            if slot not in entry["package"]:
                raise ValidationError(f"{name}: minimum package slot {slot} was not assessed")
            if not entry["package"][slot].get("status", "").strip():
                raise ValidationError(f"{name}: slot {slot} carries no status")
        if entry["b6_now"] == "RETRIEVED" and not entry.get("working_paths"):
            raise ValidationError(
                f"{name}: B6 is recorded as recovered and no working path is named"
            )
        if (
            entry["b6_now"] == "RETRIEVED"
            and not entry.get("why_the_earlier_path_failed", "").strip()
        ):
            raise ValidationError(
                f"{name}: a recovered path must say why the earlier one failed, or the next "
                "mission cannot tell a moved document from a refused one"
            )
        lineage_levels = [
            slot.get("lineage_level")
            for slot in entry["package"].values()
            if isinstance(slot, dict) and slot.get("lineage_level")
        ]
        for level in lineage_levels:
            if level not in LINEAGE_LEVELS:
                raise ValidationError(f"{name}: lineage level {level!r} is not in the vocabulary")
            if level == "LEVEL_2":
                raise ValidationError(
                    f"{name}: no partner reached LEVEL 2 in this mission, and recording one "
                    "would be qualifying a partner the mission did not evaluate"
                )

    verdict = partners["verdict"]
    if verdict["b6_recovered_of"] != len(entries):
        raise ValidationError("the recovery tally does not cover every partner")
    counted = sum(1 for e in entries if e["b6_now"] == "RETRIEVED")
    if verdict["b6_recovered_for"] != counted:
        raise ValidationError("the recovery tally and the partner entries disagree")
    for name in ("partners_qualified", "partners_disqualified", "partners_ranked"):
        if verdict.get(name) != 0:
            raise ValidationError(
                f"§25: {name} must be 0. This mission answers whether the NEXT one can evaluate "
                "these candidates, never which to pick"
            )
    if verdict.get("pair_selected") is not None:
        raise ValidationError("§62: no pair may be selected")
    if not verdict.get("what_this_does_not_establish", "").strip():
        raise ValidationError(
            "§24: a recovered documentation path is not a qualified apparatus, and the record "
            "must say what it does not establish"
        )
    if not partners.get("why_no_preference_is_expressed", {}).get("the_temptation", "").strip():
        raise ValidationError(
            "§25: the record must name the preference it declined to express, because an "
            "unnamed temptation is one a later reader cannot audit"
        )


def _validate_closure(closure: dict, lineage: dict, operational: dict) -> None:
    if closure["primary_outcome"] not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {closure['primary_outcome']!r}")
    if not closure.get("primary_outcome_statement", "").strip():
        raise ValidationError("the outcome must be stated in a sentence, not only as a label")
    if closure.get("selected_pair") is not None:
        raise ValidationError("§62: no pair may be selected")
    if closure.get("pair_gates_evaluated") is not False:
        raise ValidationError("§62: pair gates are the next mission's work")

    table = closure["anchor_gate_table"]
    for gate in INDIVIDUAL_GATES:
        if gate not in table:
            raise ValidationError(f"§43: gate {gate} is missing from the anchor gate table")
        if table[gate]["verdict"] not in ALL_VERDICTS:
            raise ValidationError(f"anchor gate {gate} carries verdict {table[gate]['verdict']!r}")

    counted_pass = sum(1 for g in INDIVIDUAL_GATES if table[g]["verdict"] == "PASS")
    counted_bounds = sum(
        1 for g in INDIVIDUAL_GATES if table[g]["verdict"] == "PASS_WITH_STATED_BOUNDS"
    )
    counted_partial = sum(1 for g in INDIVIDUAL_GATES if table[g]["verdict"] == "PARTIAL")
    if (table["pass_count"], table["pass_with_bounds_count"], table["partial_count"]) != (
        counted_pass,
        counted_bounds,
        counted_partial,
    ):
        raise ValidationError("the gate table counts disagree with the gate verdicts")

    blocking = [g for g in INDIVIDUAL_GATES if table[g]["verdict"] not in QUALIFYING_VERDICTS]
    if table["which_gates_block"] != blocking:
        raise ValidationError(
            f"which_gates_block reads {table['which_gates_block']} and the verdicts give {blocking}"
        )
    if table["individually_qualifies"] != (not blocking):
        raise ValidationError(
            "§43: the gate set is conjunctive, so an apparatus qualifies exactly when nothing "
            "blocks it"
        )
    if blocking and not table.get("why_not", "").strip():
        raise ValidationError("a blocked apparatus must say what blocks it and why that matters")

    if table["A7"]["verdict"] != lineage["gate_a7_verdict"]["verdict"]:
        raise ValidationError("the closure record and the lineage record disagree about A7")
    if table["A8"]["verdict"] != operational["gate_a8_verdict"]["verdict"]:
        raise ValidationError("the closure record and the operational record disagree about A8")

    if (
        table["A2"]["verdict"] in QUALIFYING_VERDICTS
        and not table["A2"].get("bound_added", "").strip()
    ):
        raise ValidationError(
            "§14: A2 passes on a non-default mechanism, and the gate table must carry that bound "
            "or a reader will take the default surface for the addressable one"
        )

    registry = closure["new_requirements_for_the_registry"]["requirements"]
    for item in registry:
        for field in ("name", "from", "rule", "discovered_how"):
            if not item.get(field, "").strip():
                raise ValidationError(f"registry entry {item.get('name')!r} states no {field}")

    counters = closure["counters"]
    for name in (
        "research_data_requests",
        "target_measurement_requests",
        "target_host_record_requests",
        "target_count_requests",
        "facets_fetched",
        "queries_executed",
        "trials_started",
        "purchases",
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
        "enquiries_sent",
    ):
        if counters.get(name) != 0:
            raise ValidationError(f"§60: counter {name} reads {counters.get(name)!r} and must be 0")
    if counters.get("mission_1_56_claim_modified") is not False:
        raise ValidationError("§62: the Mission 1.56 Claim is untouched")

    stop = closure["stop_condition"]
    for name, value in stop.items():
        if name.startswith("$") or name == "awaiting":
            continue
        if value is not False:
            raise ValidationError(
                f"§62: the stop condition {name} reads {value!r} and every one must be false"
            )


def _validate_enquiry(enquiry: dict, operational: dict) -> None:
    if enquiry.get("status") != "AWAITING_OPERATOR_APPROVAL":
        raise ValidationError(
            "§38: the enquiry's status must read AWAITING_OPERATOR_APPROVAL. Marking it approved "
            "would change its bytes and therefore its hash, and a frozen document that no longer "
            "answers to the hash it was frozen at is not frozen"
        )

    delivery = enquiry["delivery"]
    if delivery.get("sent") is not False:
        raise ValidationError("§37: the enquiry is drafted and not sent")
    if delivery.get("sent_at") is not None:
        raise ValidationError(
            "§37: this repository may prepare a message and may never imply it was delivered"
        )
    if delivery.get("recipient_address") != "TO_BE_SUPPLIED_BY_OPERATOR":
        address = delivery.get("recipient_address", "")
        if "@" in address and not delivery.get("address_retrieved_first_party"):
            raise ValidationError(
                "an address that was not retrieved first-party is a fabricated fact about the "
                "apparatus"
            )

    approval = enquiry["operator_approval"]
    if approval.get("approval_recorded") is not False:
        raise ValidationError(
            "§38: no approval has been recorded, and writing one is not recording it"
        )
    if "<sha256" not in approval.get("approval_string_form", ""):
        raise ValidationError(
            "§38: the approval string must name the hash of the rendered document, so the "
            "approval names a document rather than an intention"
        )

    questions = enquiry["questions"]
    if not questions:
        raise ValidationError("an enquiry with no questions is not an enquiry")
    answered_topics = {
        q["question"].split(".")[0].strip().upper()
        for q in operational["eleven_questions"]
        if q["status"] == "ANSWERED"
    }
    for q in questions:
        for field in ("topic", "question", "why_we_ask", "unanswered_by"):
            if not q.get(field, "").strip():
                raise ValidationError(f"enquiry question {q['n']} states no {field}")
        if q["topic"].strip().upper() in answered_topics:
            raise ValidationError(
                f"§26: enquiry question {q['n']} asks about {q['topic']!r}, which the "
                "documentation already answers. Do not contact the provider for facts already "
                "clearly documented"
            )

    # Scan the text that would actually be TRANSMITTED, not the repository's
    # commentary about it. `what_this_enquiry_is_not` says in so many words that
    # the enquiry asks for no trial and no evaluation account, and a scan over the
    # whole record refuses the sentence doing the work — the testing-strategy §23
    # shape, met for the sixth time in this repository. The fix is to check what
    # the check is actually about rather than to weaken it, which also makes it
    # stricter: the sendable body is the only place these phrases would do harm.
    sendable = [enquiry["subject"], enquiry["preamble"], enquiry["closing"]]
    for q in questions:
        sendable += [q["topic"], q["question"], q["why_we_ask"]]
    text = " ".join(sendable).lower()
    for ask in FORBIDDEN_ASKS:
        if ask in text:
            raise ValidationError(
                f"§31: the enquiry body contains {ask!r}. It asks about METHOD and never for the "
                "data, for access, for a trial or for a price"
            )

    for required in ("not_a_request_for_data", "not_a_request_for_access", "not_evidence"):
        if not enquiry["what_this_enquiry_is_not"].get(required, "").strip():
            raise ValidationError(f"§30: the enquiry must state that it is {required}")


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
                        f"§45: a record uses {term!r}. A count of addresses answering on a port is "
                        f"not a market statement. Offending sentence: {sentence[:120]!r}"
                    )


# --------------------------------------------------------------------------- render


def render_baseline(record: dict) -> str:
    pre = record["repository_precondition"]
    base = record["canonical_baseline"]
    scope = record["scope_freeze"]
    ledger = record["documentation_ledger"]

    lines = [
        "# Anchor documentation confirmation — baseline",
        "",
        "Generated by `infrastructure/scripts/render_anchor_lineage_closure.py`. Do not edit.",
        "",
        f"**Mission:** {record['mission']}  ",
        f"**Recorded:** {record['recorded_at']}",
        "",
        "## Precondition",
        "",
        _row(["fact", "value"]),
        _row(["---", "---"]),
        _row(["Mission 1.60 merged", str(pre["mission_1_60_merged"])]),
        _row(["merge commit", f"`{pre['merge_commit']}`"]),
        _row(["branch", f"`{pre['branch']}`"]),
        _row(["migration head", f"`{pre['migration_head']}`"]),
        "",
        "## Canonical baseline",
        "",
        "Measured live against the deployment before any work.",
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
        "reliability_assessments",
        "independence_groups",
        "claims_carrying_both_directions",
        "embeddings",
        "registered_sources",
    ):
        lines.append(_row([f"`{key}`", str(base[key])]))
    directions = ", ".join(f"{k} {v}" for k, v in base["evidence_directions"].items())
    lines += [
        _row(["evidence directions", directions]),
        _row(["drift from Mission 1.60", f"**{base['drift_from_mission_1_60']}**"]),
        "",
        "## Frozen scope",
        "",
        f"Anchor **{scope['anchor']}**, and exactly {len(scope['partners'])} partner candidates:",
        "",
    ]
    lines += [f"- {name}" for name in scope["partners"]]
    dropped = scope["dropped_apparatus"]
    lines += [
        "",
        f"**{dropped['name']}** stays `{dropped['status']}`, retained as "
        f"`{dropped['retained_as']}`, reconsidered **{dropped['reconsidered']}**.",
        "",
        dropped["why_not_reconsidered"],
        "",
        "## Documentation ledger",
        "",
        f"{ledger['used_total']} of {ledger['budget_total']} retrievals — anchor "
        f"{ledger['used_anchor']} of {ledger['budget_anchor']}, partners "
        f"{ledger['used_partners']} of {ledger['budget_partners']}.",
        "",
        _row(["#", "subject", "purpose", "first party", "load bearing"]),
        _row(["---", "---", "---", "---", "---"]),
    ]
    for entry in ledger["requests"]:
        lines.append(
            _row(
                [
                    str(entry["n"]),
                    entry["subject"],
                    entry["purpose"],
                    "yes" if entry["first_party"] else "no",
                    "yes" if entry["load_bearing"] else "no",
                ]
            )
        )
    lines += [
        "",
        "## What did not happen",
        "",
        "```",
        f"queries executed        {ledger['queries_executed']}"
        f"        trials started    {ledger['trials_started']}",
        f"target counts           {ledger['target_count_requests']}"
        f"        purchases         {ledger['purchases']}",
        f"host records            {ledger['target_host_record_requests']}"
        f"        facets            {ledger['facets_fetched']}",
        "```",
        "",
        record["value_exposure"]["the_count_is_not_metadata"],
        "",
        record["value_exposure"]["the_trial_is_not_free"],
        "",
    ]
    return "\n".join(lines)


def render_lineage(record: dict) -> str:
    two = record["two_exhaustiveness_questions_that_are_not_one"]
    level2 = record["level_2_evidence"]
    check = record["do_the_exceptions_touch_the_load_bearing_predicate"]
    verdict = record["gate_a7_verdict"]

    lines = [
        "# Anchor lineage review — gate A7",
        "",
        "Generated by `infrastructure/scripts/render_anchor_lineage_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Gate:** {record['gate']}  ",
        f"**Verdict:** `{verdict['verdict']}` at `{verdict['level_reached']}`, "
        f"was `{verdict['previous_verdict']}` in Mission {verdict['previous_verdict_mission']}",
        "",
        "## Two exhaustiveness questions that are not one",
        "",
        _row(["question", "gate", "answered here"]),
        _row(["---", "---", "---"]),
        _row(
            [
                "lineage exhaustiveness",
                two["LINEAGE_EXHAUSTIVENESS"]["gate"],
                str(two["LINEAGE_EXHAUSTIVENESS"]["answered_here"]),
            ]
        ),
        _row(
            [
                "scan / frame exhaustiveness",
                two["SCAN_OR_FRAME_EXHAUSTIVENESS"]["gate"],
                str(two["SCAN_OR_FRAME_EXHAUSTIVENESS"]["answered_here"]),
            ]
        ),
        "",
        two["the_distinction_that_must_survive"],
        "",
        "## The evidence ladder",
        "",
    ]
    for level in LINEAGE_LEVELS:
        lines.append(f"- **{level}** — {record['evidence_levels'][level]}")
    lines += [
        "",
        "## The statement",
        "",
        f"Source: <{level2['source_url']}>, retrieved twice.",
        "",
        f"> {level2['verbatim_affirmative_statement']}",
        "",
        f"> {level2['verbatim_exception_clause']}",
        "",
        level2["why_closed"],
        "",
        "## Do the exceptions touch the predicate?",
        "",
        f"Predicate: *{check['load_bearing_predicate']}*",
        "",
        _row(["exception", "bears on predicate", "why"]),
        _row(["---", "---", "---"]),
    ]
    for item in check["exceptions"]:
        lines.append(
            _row([item["name"], "**yes**" if item["bears_on_predicate"] else "no", item["why"]])
        )
    lines += [
        "",
        check["conclusion"],
        "",
        check["the_reasoning_that_was_refused"],
        "",
        "## What this closes, and what it does not",
        "",
        f"**Closes:** {verdict['what_this_closes']}",
        "",
        "**Does not close:**",
        "",
    ]
    lines += [f"- {item}" for item in verdict["what_this_does_not_close"]]
    lines += ["", "## Bounds on this finding", ""]
    for key, text in record["bounds_on_this_finding"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines.append("")
    return "\n".join(lines)


def render_operational(record: dict) -> str:
    verdict = record["gate_a8_verdict"]
    tally = record["tally"]
    bound = record["a2_bound_discovered_this_mission"]

    lines = [
        "# Anchor operational reviewability — gate A8",
        "",
        "Generated by `infrastructure/scripts/render_anchor_lineage_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Gate:** {record['gate']}  ",
        f"**Verdict:** `{verdict['verdict']}`, was `{verdict['previous_verdict']}` in Mission "
        f"{verdict['previous_verdict_mission']}",
        "",
        f"`{tally['answered']}` answered, `{tally['partially_answered']}` partial, "
        f"`{tally['not_answered']}` unanswered, of `{tally['total']}`.",
        "",
        "No reliability value is assigned here. "
        + record["what_this_gate_is_and_is_not"]["it_asks"],
        "",
        "## The eleven questions",
        "",
        _row(["#", "question", "status", "in enquiry"]),
        _row(["---", "---", "---", "---"]),
    ]
    for q in record["eleven_questions"]:
        lines.append(
            _row(
                [
                    str(q["n"]),
                    q["question"],
                    f"`{q['status']}`",
                    "yes" if q.get("in_enquiry") else "no",
                ]
            )
        )
    lines += ["", "## Findings", ""]
    for q in record["eleven_questions"]:
        lines += [f"### {q['n']}. {q['question']}", "", f"`{q['status']}`. {q['finding']}"]
        if q.get("why_this_matters"):
            lines += ["", f"*Why this matters:* {q['why_this_matters']}"]
        if q.get("consequence"):
            lines += ["", f"*Consequence:* {q['consequence']}"]
        lines.append("")
    lines += [
        "## Verdict",
        "",
        verdict["how_it_moved"],
        "",
        f"**Why not PASS.** {verdict['why_not_PASS']}",
        "",
        f"**Why not FAIL.** {verdict['why_not_FAIL']}",
        "",
        verdict["what_remains_is_operational_not_semantic"],
        "",
        "## A bound discovered on a gate a previous mission passed",
        "",
        bound["finding"],
        "",
        f"> {bound['verbatim_replacement_sentence']}",
        "",
        f"> {bound['verbatim_default_sentence']}",
        "",
        bound["why_this_matters"],
        "",
        f"**Does A2 still pass?** {bound['does_a2_still_pass']}. {bound['why']}",
        "",
        f"**The bound that must be carried.** {bound['the_bound_that_must_be_carried']}",
        "",
    ]
    return "\n".join(lines)


def render_vantage(record: dict) -> str:
    why = record["why_vantage_is_asked_before_pairing"]
    cls = record["anchor_classification"]

    lines = [
        "# Anchor vantage model",
        "",
        "Generated by `infrastructure/scripts/render_anchor_lineage_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Verdict:** `{cls['verdict']}`, was `{cls['previous_verdict']}` in Mission "
        f"{cls['previous_verdict_mission']}",
        "",
        "## Why vantage is asked before pairing",
        "",
        why["the_quantity_is_vantage_relative"],
        "",
        f"**The trap it would recreate.** {why['the_trap_it_would_recreate']}",
        "",
        why["why_it_is_not_fatal_by_itself"],
        "",
        f"**The asymmetry with A7.** {why['the_asymmetry_with_A7']}",
        "",
        "## Classification",
        "",
        _row(["term", "meaning"]),
        _row(["---", "---"]),
    ]
    for term in VANTAGE_VERDICTS:
        lines.append(_row([f"`{term}`", record["classification_vocabulary"][term]]))
    lines += [
        "",
        cls["how_it_moved"],
        "",
        f"**What the documentation says.** {cls['what_the_documentation_says']}",
        "",
        "**What it does not say:**",
        "",
    ]
    lines += [f"- {item}" for item in cls["what_it_does_not_say"]]
    lines += [
        "",
        f"**Record-side check.** {cls['record_side_check']}",
        "",
        "## Consequences",
        "",
    ]
    for key, text in record["consequences_for_the_next_mission"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines.append("")
    return "\n".join(lines)


def render_port_window(record: dict) -> str:
    verdict = record["verdict"]
    lines = [
        "# Anchor port-window coverage — port 22",
        "",
        "Generated by `infrastructure/scripts/render_anchor_lineage_closure.py`. Do not edit.",
        "",
        f"**Apparatus:** {record['apparatus']}  ",
        f"**Window addressability:** `{verdict['window_addressability_of_port_22']}`  ",
        f"**Current inclusion:** `{verdict['current_inclusion_of_port_22']}`",
        "",
        "## Why this is asked",
        "",
        record["why_this_is_asked_at_all"]["the_problem"],
        "",
        record["why_this_is_asked_at_all"]["why_it_is_not_hypothetical"],
        "",
        record["why_this_is_asked_at_all"]["the_direction_that_matters"],
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
        "## Verdict",
        "",
        verdict["these_are_two_answers_and_not_one"],
        "",
        f"Forward risk `{verdict['forward_risk']}`. {verdict['why_low']} "
        f"{verdict['why_uncommitted']}",
        "",
        "## What this costs the route",
        "",
    ]
    cost = record["what_this_costs_the_route"]
    lines += [
        f"- **blocks a threshold** — {cost['does_it_block_a_threshold']}. {cost['why_not']}",
        f"- **bound carried** — {cost['the_bound_that_must_be_carried']}",
        f"- **the closing question** — {cost['the_question_that_would_close_it']}",
        "",
    ]
    return "\n".join(lines)


def render_partners(record: dict) -> str:
    verdict = record["verdict"]
    lines = [
        "# Partner documentation recovery",
        "",
        "Generated by `infrastructure/scripts/render_anchor_lineage_closure.py`. Do not edit.",
        "",
        f"**B6 recovered for {verdict['b6_recovered_for']} of {verdict['b6_recovered_of']}.** "
        f"Qualified `{verdict['partners_qualified']}`, ranked `{verdict['partners_ranked']}`, "
        f"pair selected `{verdict['pair_selected']}`.",
        "",
        "## What Mission 1.60 recorded",
        "",
        record["what_mission_1_60_recorded"]["the_sentence_that_governs"],
        "",
        f"*{record['what_mission_1_60_recorded']['what_this_mission_tests']}*",
        "",
        "## The minimum package",
        "",
        _row(["slot", "requirement"]),
        _row(["---", "---"]),
    ]
    for slot in B_SLOTS:
        lines.append(_row([f"`{slot}`", record["the_minimum_package"][slot]]))
    lines += ["", "## Package status", "", _row(["candidate"] + list(B_SLOTS)), _row(["---"] * 7)]
    for entry in record["partners"]:
        lines.append(
            _row([entry["name"]] + [f"`{entry['package'][s]['status']}`" for s in B_SLOTS])
        )
    lines += ["", "## Candidates", ""]
    for entry in record["partners"]:
        lines += [
            f"### {entry['name']}",
            "",
            f"B6 `{entry['b6_previous']}` → `{entry['b6_now']}`.",
            "",
            f"*Why the earlier path failed:* {entry['why_the_earlier_path_failed']}",
            "",
            "Working paths:",
            "",
        ]
        lines += [f"- <{path}>" for path in entry["working_paths"]]
        lines.append("")
        for slot in B_SLOTS:
            item = entry["package"][slot]
            text = f"- **{slot}** `{item['status']}`"
            if item.get("finding"):
                text += f" — {item['finding']}"
            lines.append(text)
        for key in (
            "port_22_relevance",
            "vantage",
            "scope_concern",
            "the_question_that_must_be_answered_first",
        ):
            if key in entry:
                block = entry[key]
                lines += [
                    "",
                    f"**{key.replace('_', ' ')}** — `{block.get('status', '')}`. "
                    f"{block.get('finding', block.get('why_first', ''))}",
                ]
        lines.append("")
    lines += [
        "## Verdict",
        "",
        verdict["what_this_establishes"],
        "",
        verdict["what_this_does_not_establish"],
        "",
        f"**{verdict['the_honest_summary']}**",
        "",
        "## Why no preference is expressed",
        "",
        record["why_no_preference_is_expressed"]["the_temptation"],
        "",
        record["why_no_preference_is_expressed"]["what_is_recorded_instead"],
        "",
    ]
    return "\n".join(lines)


def render_closure(record: dict) -> str:
    table = record["anchor_gate_table"]
    counters = record["counters"]
    lines = [
        "# Anchor lineage and documentation closure",
        "",
        "Generated by `infrastructure/scripts/render_anchor_lineage_closure.py`. Do not edit.",
        "",
        f"**Outcome: `{record['primary_outcome']}`**, with "
        f"`{record['secondary_outcome']}` beside it.",
        "",
        record["primary_outcome_statement"],
        "",
        "## The anchor gate table",
        "",
        _row(["gate", "verdict", "moved", "note"]),
        _row(["---", "---", "---", "---"]),
    ]
    for gate in INDIVIDUAL_GATES:
        item = table[gate]
        note = (
            item.get("bound_added") or item.get("what_changed") or item.get("exposure_class") or ""
        )
        if item.get("level"):
            note = f"{item['level']}"
        lines.append(_row([gate, f"`{item['verdict']}`", "**yes**" if item["moved"] else "", note]))
    lines += [
        "",
        f"`{table['pass_count']}` pass, `{table['pass_with_bounds_count']}` pass with bounds, "
        f"`{table['partial_count']}` partial. Blocks **{table['which_gates_block']}**, "
        f"previously **{table['blocking_gates_previously']}**.",
        "",
        f"Individually qualifies: **{table['individually_qualifies']}**. {table['why_not']}",
        "",
        "## What changed, and what did not",
        "",
    ]
    for key, text in record["what_changed_and_what_did_not"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    drafted = record["drafted_enquiry"]
    lines += [
        "## The drafted enquiry",
        "",
        f"`{drafted['document']}`, {drafted['questions']} questions, "
        f"status `{drafted['status']}`, sent **{drafted['sent']}**.",
        "",
        f"    sha256  {drafted['sha256']}",
        "",
        f"Approval string: `{drafted['approval_string']}`",
        "",
        drafted["the_gate_rechecks_it"],
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
            f"*Discovered how:* {item['discovered_how']}",
            "",
        ]
    lines += [
        "## Counters",
        "",
        "```",
        f"first-party doc requests  {counters['first_party_doc_requests']} of {counters['budget']}"
        f"   anchor {counters['anchor_requests']} of {counters['anchor_budget']}"
        f"   partners {counters['partner_requests']} of {counters['partner_budget']}",
        f"queries executed          {counters['queries_executed']}"
        f"        trials     {counters['trials_started']}",
        f"target counts             {counters['target_count_requests']}"
        f"        purchases  {counters['purchases']}",
        f"host records              {counters['target_host_record_requests']}"
        f"        facets     {counters['facets_fetched']}",
        f"enquiries drafted         {counters['enquiries_drafted']}"
        f"        sent       {counters['enquiries_sent']}",
        "```",
        "",
        "0 canonical mutations, 0 sources registered, 0 governance reviews, 0 collectors, "
        "0 threshold registrations, 0 Claims, 0 Evidence, 0 reliability values, 0 independence "
        "groups, 0 Scores, 0 model calls, 0 embeddings. The Mission 1.56 Claim is untouched, the "
        f"profile is still {counters['reference_profile']}, Problem-Family is still "
        f"{counters['problem_family']}.",
        "",
        "## Next",
        "",
        f"**{record['next_mission_recommendation']['name']}.** "
        f"{record['next_mission_recommendation']['why_this']}",
        "",
        "It should:",
        "",
    ]
    lines += [f"- {item}" for item in record["next_mission_recommendation"]["it_should"]]
    lines += ["", "It must not:", ""]
    lines += [f"- {item}" for item in record["next_mission_recommendation"]["it_must_not"]]
    lines += ["", f"Awaiting: **{record['stop_condition']['awaiting']}**.", ""]
    return "\n".join(lines)


def render_enquiry(record: dict) -> str:
    delivery = record["delivery"]
    approval = record["operator_approval"]
    lines = [
        "# Anchor technical lineage enquiry — DRAFTED, NOT SENT",
        "",
        "Generated by `infrastructure/scripts/render_anchor_lineage_closure.py`. Do not edit.",
        "",
        f"**Status:** `{record['status']}`  ",
        f"**Sent:** {delivery['sent']}  ",
        f"**Recipient:** `{delivery['recipient_address']}`",
        "",
        delivery["why_no_address_is_recorded"],
        "",
        "## Why an enquiry at all",
        "",
        record["why_an_enquiry_at_all"]["the_rule_followed"],
        "",
        record["why_an_enquiry_at_all"]["what_is_not_asked"],
        "",
        "## What this enquiry is not",
        "",
    ]
    for key, text in record["what_this_enquiry_is_not"].items():
        if key.startswith("$"):
            continue
        lines.append(f"- **{key.replace('_', ' ')}** — {text}")
    lines += [
        "",
        "---",
        "",
        f"## Subject: {record['subject']}",
        "",
        record["preamble"],
        "",
    ]
    for q in record["questions"]:
        lines += [
            f"**{q['n']}. {q['topic']}.** {q['question']}",
            "",
            f"> *Why we ask:* {q['why_we_ask']}",
            "",
        ]
    lines += [
        record["closing"],
        "",
        "---",
        "",
        "## Operator approval",
        "",
        f"Required: **{approval['required']}**. Recorded: **{approval['approval_recorded']}**.",
        "",
        f"Approval string: `{approval['approval_string_form']}`",
        "",
        approval["why_the_status_field_is_never_edited"],
        "",
        f"**What approval authorises.** {approval['what_approval_authorises']}",
        "",
        f"**What a reply would be.** {approval['what_a_reply_would_be']}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        (
            baseline,
            lineage,
            operational,
            vantage,
            portwindow,
            partners,
            closure,
            enquiry,
        ) = validate()
    except ValidationError as error:
        print(f"REFUSED  anchor lineage closure: {error}")
        return 1

    rendered = {
        RENDERED[BASELINE]: render_baseline(baseline),
        RENDERED[LINEAGE]: render_lineage(lineage),
        RENDERED[OPERATIONAL]: render_operational(operational),
        RENDERED[VANTAGE]: render_vantage(vantage),
        RENDERED[PORTWINDOW]: render_port_window(portwindow),
        RENDERED[PARTNERS]: render_partners(partners),
        RENDERED[CLOSURE]: render_closure(closure),
        RENDERED[ENQUIRY]: render_enquiry(enquiry),
    }

    digest = hashlib.sha256(rendered[RENDERED[ENQUIRY]].encode("utf-8")).hexdigest()
    recorded = closure.get("drafted_enquiry", {}).get("sha256")
    if recorded and recorded != digest:
        print(
            f"DRIFT    the enquiry hash recorded in the closure record is {recorded} "
            f"and the rendered enquiry hashes to {digest}"
        )
        return 1

    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print(
            f"ok       {len(rendered)} lineage documents match their records; "
            f"outcome {closure['primary_outcome']}"
        )
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {closure['primary_outcome']}")
    print(
        f"anchor   A7 {lineage['gate_a7_verdict']['verdict']} at "
        f"{lineage['gate_a7_verdict']['level_reached']}, "
        f"A8 {operational['gate_a8_verdict']['verdict']}, "
        f"blocks {closure['anchor_gate_table']['which_gates_block']}"
    )
    print(f"vantage  {vantage['anchor_classification']['verdict']}")
    print(f"port 22  {portwindow['verdict']['window_addressability_of_port_22']}")
    print(
        f"partners B6 recovered {partners['verdict']['b6_recovered_for']}"
        f" of {partners['verdict']['b6_recovered_of']}, "
        f"qualified {partners['verdict']['partners_qualified']}"
    )
    print(f"enquiry  drafted, not sent, sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
