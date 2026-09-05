"""Render and validate the Mission 1.60 scanner-pair selection records.

Five documents: the baseline and documentation ledger, the individual apparatus
contract with its requirement registry, the anchor requalification, the partner
candidates, and the selection verdict.

`validate()` enforces the rules a later mission would most easily bend. They are
the accumulated refusals of this whole arc: a current-state database is not
observation-addressable however good it is, a vendor label is not a protocol
predicate, a timestamp that exists but cannot be selected before retrieval is not
addressability, an absence is not an affirmative statement, two brand names are
not two apparatuses, a free trial is not harmless, a count is not documentation,
and a partial is not a pass.

    uv run python infrastructure/scripts/render_scanner_pair_selection.py
    uv run python infrastructure/scripts/render_scanner_pair_selection.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "observation-addressable-scanner-selection-baseline-v1.json"
CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"
ANCHOR = DATA / "anchor-scanner-requalification-v1.json"
PARTNERS = DATA / "observation-addressable-partner-candidates-v1.json"
SELECTION = DATA / "observation-addressable-scanner-pair-selection-v1.json"

RENDERED = {
    BASELINE: DATA / "observation-addressable-scanner-selection-baseline-v1.md",
    CONTRACT: DATA / "observation-addressable-apparatus-contract-v1.md",
    ANCHOR: DATA / "anchor-scanner-requalification-v1.md",
    PARTNERS: DATA / "observation-addressable-partner-candidates-v1.md",
    SELECTION: DATA / "observation-addressable-scanner-pair-selection-v1.md",
}

INDIVIDUAL_GATES = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9")
QUALIFYING_VERDICTS = ("PASS", "PASS_WITH_STATED_BOUNDS")
ALL_VERDICTS = QUALIFYING_VERDICTS + ("PARTIAL", "UNKNOWN", "FAIL", "NOT_APPLICABLE")

# Only these three exposure classes may carry a protocol predicate.
PERMITTED_EXPOSURE = (
    "RAW_IDENTIFICATION_STRING",
    "STRUCTURED_PROTOCOL_FIELD",
    "DETERMINISTIC_EQUIVALENT_FIELD",
)
REJECTED_EXPOSURE = ("PROPRIETARY_CLASSIFIER_ONLY", "NOT_EXPOSED", "UNKNOWN")

# Time objects. The rejected one is rejected however excellent the database.
ACCEPTABLE_TIME_OBJECTS = (
    "OBSERVATION_EVENT_STREAM",
    "IMMUTABLE_SCAN_SNAPSHOT_WITH_DEFINED_INTERVAL",
    "OBSERVATION_PARTITION_BY_WINDOW",
)
REJECTED_TIME_OBJECT = "MAINTAINED_CURRENT_STATE_LAST_CHANGE"

PRIMARY_OUTCOMES = {
    "OBSERVATION_ADDRESSABLE_INDEPENDENT_SCANNER_PAIR_SELECTED",
    "ANCHOR_APPARATUS_INVALIDATED",
    "NO_OBSERVATION_ADDRESSABLE_PARTNER_IDENTIFIED",
    "PROTOCOL_NATIVE_EXPOSURE_NOT_AVAILABLE",
    "SAMPLING_FRAME_ALIGNMENT_GAP",
    "VANTAGE_RELATIVE_POPULATION_GAP",
    "APPARATUS_LINEAGE_NOT_AFFIRMATIVELY_ESTABLISHED",
    "RELIABILITY_REVIEWABILITY_BLOCKS_PAIR",
    "PRODUCT_RELEVANCE_LOST_AFTER_PAIR_NARROWING",
    "PREREGISTRATION_POSSIBILITY_COMPROMISED",
    "MISSION_1_59_NOT_MERGED",
    "MISSION_1_60_BASELINE_DRIFT",
    "MISSION_1_60_CANONICAL_MUTATION",
    "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
    "OBSERVATION_ADDRESSABLE_SCANNER_PAIR_SELECTION_BLOCKED",
}

OVERCLAIMS = (
    "installation",
    "customer",
    "user",
    "subscription",
    "revenue",
    "market share",
    "adoption",
    "demand",
)


class ValidationError(Exception):
    """A selection record claims something the rules do not permit."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    return json.loads(path.read_text(encoding="utf-8"))


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def validate() -> tuple[dict, dict, dict, dict, dict]:
    baseline = _load(BASELINE)
    contract = _load(CONTRACT)
    anchor = _load(ANCHOR)
    partners = _load(PARTNERS)
    selection = _load(SELECTION)

    _validate_baseline(baseline)
    _validate_contract(contract)
    _validate_anchor(anchor)
    _validate_partners(partners)
    _validate_selection(selection, anchor, partners)
    return baseline, contract, anchor, partners, selection


def _validate_baseline(baseline: dict) -> None:
    pre = baseline["repository_precondition"]
    if pre.get("mission_1_59_merged") is not True:
        raise ValidationError("Mission 1.59 is not recorded as merged")
    if not pre.get("merge_commit", "").strip():
        raise ValidationError("the precondition must name the commit it verified")

    carried = baseline["carried_forward"]
    failed = carried["failed_apparatus_a"]
    if failed.get("status") != "DROPPED_FOR_THIS_ROUTE":
        raise ValidationError(
            "§4: the Mission 1.59 current-state apparatus is permanently dropped for this route. "
            "Its temporal mismatch is established, not unknown"
        )
    if failed.get("retained_as") != "NEGATIVE_CONTROL":
        raise ValidationError(
            "§50: the dropped apparatus is retained as a negative control, so a later mission does "
            "not rediscover it as a promising scanner with an excellent database"
        )
    anchor_state = carried["anchor_candidate_b"]
    if anchor_state.get("status_carried") != "ANCHOR_CANDIDATE_B":
        raise ValidationError(
            "the carried apparatus is a candidate, not a selected or approved one"
        )
    for forbidden in ("SELECTED_APPARATUS_B", "APPROVED_APPARATUS_B"):
        if forbidden not in anchor_state.get("not", []):
            raise ValidationError(f"the record must state that the anchor is not {forbidden}")

    ledger = baseline["documentation_ledger"]
    if ledger["used"] != len(ledger["requests"]):
        raise ValidationError("the ledger count and its entries disagree")
    if ledger["used"] > ledger["budget"]:
        raise ValidationError(f"§37 bounds documentation retrievals at {ledger['budget']}")
    for name in (
        "research_data_requests",
        "target_measurement_requests",
        "target_host_record_requests",
        "target_count_requests",
        "facets_fetched",
        "trials_started",
        "purchases",
    ):
        if ledger.get(name) != 0:
            raise ValidationError(f"§54: {name} must be 0 and reads {ledger.get(name)!r}")
    for entry in ledger["requests"]:
        if entry.get("load_bearing") and not entry.get("first_party"):
            raise ValidationError(
                f"request {entry['n']} closes a gate on a non-first-party source, which §8 forbids"
            )

    exposure = baseline["value_exposure"]
    if exposure.get("target_measurement_retrieved") is not False:
        raise ValidationError(
            "§33: a target measurement was retrieved, which is PREREGISTRATION_POSSIBILITY_"
            "COMPROMISED and a hard stop"
        )
    if exposure.get("queries_executed") != 0:
        raise ValidationError("§32: a query template may be constructed and never executed")


def _validate_contract(contract: dict) -> None:
    gates = contract["individual_hard_gates"]
    if [g["id"] for g in gates] != list(INDIVIDUAL_GATES):
        raise ValidationError(f"§3 defines gates {INDIVIDUAL_GATES} in order")
    for gate in gates:
        if not gate.get("rule", "").strip():
            raise ValidationError(f"gate {gate['id']} states no rule")

    addressability = contract["observation_addressability_is_about_the_boundary"]
    if REJECTED_TIME_OBJECT not in addressability.get("rejected_time_object", ""):
        raise ValidationError(
            "§20: a maintained current state indexed by last-change time is rejected however "
            "excellent its database, and the contract must say so by name"
        )
    for shape in ("current state plus last_changed", "retrieve the whole set"):
        if not any(shape in item for item in addressability["failing_shapes"]):
            raise ValidationError(f"§4: {shape!r} must be named as a failing shape")
    if not addressability.get("the_loophole_this_closes", "").strip():
        raise ValidationError(
            "§5: the record must say that per-row timestamps do not rescue a retrieve-then-filter "
            "procedure, because that is the loophole the gate exists to close"
        )
    for accepted in ACCEPTABLE_TIME_OBJECTS:
        if accepted not in addressability["acceptable_time_objects"]:
            raise ValidationError(f"the acceptable time object {accepted} is missing")

    classes = contract["protocol_predicate_exposure_classes"]
    for rejected in REJECTED_EXPOSURE:
        if classes.get(rejected) != "REJECTED":
            raise ValidationError(f"§11: exposure class {rejected} must be REJECTED")

    boundary = contract["metadata_versus_measurement"]
    for forbidden in ("counts", "facets"):
        if forbidden not in boundary["forbidden"]:
            raise ValidationError(f"§6: {forbidden!r} must be forbidden")
    if not boundary.get("the_count_is_not_metadata", "").strip():
        raise ValidationError(
            "§6: a query returning only a count still returns a measurement value, and the record "
            "must refuse the reading that makes it metadata"
        )
    if not boundary.get("the_trial_is_not_free", "").strip():
        raise ValidationError(
            "§34: a zero-cost trial destroys preregistration exactly as a paid one would, and "
            "access cost is irrelevant to epistemic contamination"
        )

    registry = contract["requirement_registry"]["requirements"]
    names = {item["name"] for item in registry}
    for required in (
        "OBSERVATION_ADDRESSABLE_EXPOSURE",
        "FRAME_INSIDE_THE_DEFINITION",
        "READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT",
        "SOURCE_EXCLUSIVE_METRIC",
        "AFFIRMATIVE_LINEAGE_REQUIRED",
        "RELIABILITY_REVIEWABILITY",
        "PRODUCT_RELEVANCE",
    ):
        if required not in names:
            raise ValidationError(f"§51: the registry must carry {required} forward")
    for item in registry:
        if not item.get("from", "").strip() or not item.get("rule", "").strip():
            raise ValidationError(
                f"registry entry {item['name']} names no source mission or no rule"
            )


def _validate_anchor(anchor: dict) -> None:
    results = anchor["gate_results"]
    for gate in INDIVIDUAL_GATES:
        key = next((k for k in results if k.startswith(gate + "_")), None)
        if key is None:
            raise ValidationError(f"§36: gate {gate} was not re-evaluated for the anchor")
        if results[key]["verdict"] not in ALL_VERDICTS:
            raise ValidationError(f"anchor gate {gate} carries verdict {results[key]['verdict']!r}")

    a2 = next(v for k, v in results.items() if k.startswith("A2_"))
    if a2["verdict"] in QUALIFYING_VERDICTS:
        if a2.get("time_object") not in ACCEPTABLE_TIME_OBJECTS:
            raise ValidationError(
                f"§20: A2 passes with time object {a2.get('time_object')!r}, which is not one of "
                "the acceptable shapes"
            )
        if a2.get("window_selectable_before_retrieval") is not True:
            raise ValidationError("§4: A2 passes only if the window is selectable before retrieval")
        if a2.get("requires_result_inspection") is not False:
            raise ValidationError(
                "§5: a procedure requiring result inspection is retrieve-then-filter, and a "
                "per-record timestamp does not rescue it"
            )
        if a2.get("timestamp_semantics") != "OBSERVATION_TIME":
            raise ValidationError(
                "§31: A2 passes only on OBSERVATION_TIME semantics, never on a last-change or "
                "ingestion timestamp"
            )

    a3 = next(v for k, v in results.items() if k.startswith("A3_"))
    if a3["verdict"] in QUALIFYING_VERDICTS:
        if a3.get("exposure_class") not in PERMITTED_EXPOSURE:
            raise ValidationError(
                f"§11: A3 passes with exposure class {a3.get('exposure_class')!r}, which may not "
                "carry a protocol predicate"
            )
        if a3.get("vendor_fingerprint_required") is not False:
            raise ValidationError("§12: a vendor product label is not a protocol predicate")

    a7 = next(v for k, v in results.items() if k.startswith("A7_"))
    if a7["verdict"] in QUALIFYING_VERDICTS:
        missing = a7.get("what_is_missing", "")
        if missing and missing.strip():
            raise ValidationError(
                "§26: A7 passes only on affirmative first-party evidence. A gate that records "
                "what is still missing has not passed"
            )
    else:
        if not a7.get("why_not_upgraded", "").strip():
            raise ValidationError(
                "§26: a PARTIAL lineage must say why it was not upgraded, because upgrading from "
                "absence is the failure this gate exists to prevent"
            )
        if not a7.get("how_it_could_close", "").strip():
            raise ValidationError("a blocking gate names how it could close")

    a5 = next(v for k, v in results.items() if k.startswith("A5_"))
    if not a5.get("frame", "").strip():
        raise ValidationError("§14: the frame must be stated rather than called internet-wide")

    blocked = anchor.get("which_gates_block", [])
    unqualified = [
        g
        for g in INDIVIDUAL_GATES
        if results[next(k for k in results if k.startswith(g + "_"))]["verdict"]
        not in QUALIFYING_VERDICTS
    ]
    if sorted(blocked) != sorted(unqualified):
        raise ValidationError(
            f"the blocking-gate list {sorted(blocked)} disagrees with the gate results "
            f"{sorted(unqualified)}"
        )
    if anchor.get("individually_qualifies") is not (not unqualified):
        raise ValidationError("the qualification flag disagrees with the gate results")
    if unqualified and anchor.get("requalification_result") == "ANCHOR_B_QUALIFIES":
        raise ValidationError("the anchor is recorded as qualifying with gates outstanding")

    vantage = anchor["vantage"]
    if vantage.get("status") not in ("NOT_ESTABLISHED", "ESTABLISHED", "UNKNOWN"):
        raise ValidationError(f"unrecognised vantage status {vantage.get('status')!r}")


def _validate_partners(partners: dict) -> None:
    identities = set()
    for candidate in partners["candidates"]:
        identity = candidate.get("identity", "")
        if not identity.strip():
            raise ValidationError("a candidate is unnamed")
        if identity in identities:
            raise ValidationError(
                f"{identity!r} appears twice. §52: two brand names are not two apparatuses, and "
                "one name twice is not two either"
            )
        identities.add(identity)
        if not candidate.get("first_failing_gate", "").strip():
            raise ValidationError(
                f"{identity} records no first failing gate, so §50 cannot reuse it"
            )
        if (
            candidate.get("verdict") == "DOCUMENTATION_NOT_RETRIEVABLE"
            and candidate.get("not_a_refusal") is not True
        ):
            raise ValidationError(
                f"{identity}: a documentation-retrieval failure is a fact about this mission's "
                "reach, not a finding about the apparatus, and the record must say so"
            )

    control = next(
        (c for c in partners["candidates"] if c.get("status") == "NEGATIVE_CONTROL"), None
    )
    if control is None:
        raise ValidationError("§50: the dropped apparatus must be retained as a negative control")
    if control.get("reconsidered") is not False:
        raise ValidationError("§4: the dropped apparatus is not reconsidered")

    result = partners["partner_search_result"]
    if result["reached_pair_analysis"] > result["candidates_inspected"]:
        raise ValidationError("more candidates reached pair analysis than were inspected")
    if result["qualifying_partners_found"] > result["reached_pair_analysis"]:
        raise ValidationError("a partner qualified without reaching pair analysis")
    establishes = result["what_this_does_and_does_not_establish"]
    if not establishes.get("does_not_establish", "").strip():
        raise ValidationError(
            "the record must say what the search does NOT establish. A documentation wall is not "
            "evidence that no qualifying partner exists"
        )

    pairs = partners["pairs_constructed"]
    if pairs["count"] > 0 and result["qualifying_partners_found"] == 0:
        raise ValidationError(
            "§39: pairs are generated only between individually qualifying apparatuses"
        )


def _validate_selection(selection: dict, anchor: dict, partners: dict) -> None:  # noqa: C901
    outcome = selection["primary_outcome"]
    if outcome not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {outcome!r}")

    selected = selection.get("selected_pair")
    if outcome == "OBSERVATION_ADDRESSABLE_INDEPENDENT_SCANNER_PAIR_SELECTED":
        if selected is None:
            raise ValidationError("a selecting outcome selects a pair")
        if anchor.get("individually_qualifies") is not True:
            raise ValidationError(
                "§47: a pair cannot be selected while an apparatus does not individually qualify. "
                "Conjunctive means conjunctive"
            )
        if selection.get("actionability") != "EPISTEMICALLY_VALID_GOVERNANCE_PENDING":
            raise ValidationError(
                "§42: this mission performs no governance review, so a selected pair is "
                "EPISTEMICALLY_VALID_GOVERNANCE_PENDING"
            )
    else:
        if selected is not None:
            raise ValidationError(f"{outcome} is not a selecting outcome and must select nothing")
        if selection.get("actionability") is not None:
            raise ValidationError("an unselected route carries no actionability")

    summary = selection["gate_summary"]
    for gate, verdict in summary["anchor"].items():
        key = next(k for k in anchor["gate_results"] if k.startswith(gate + "_"))
        if anchor["gate_results"][key]["verdict"] != verdict:
            raise ValidationError(
                f"the selection summary records anchor {gate} as {verdict!r} and the "
                f"requalification says {anchor['gate_results'][key]['verdict']!r}"
            )
    if summary.get("individually_qualifies") is not anchor.get("individually_qualifies"):
        raise ValidationError("the two records disagree about whether the anchor qualifies")
    if summary.get("pair_gates_evaluated") and partners["pairs_constructed"]["count"] == 0:
        raise ValidationError("pair gates were evaluated with no pair constructed")

    if (
        not selection.get("why_this_outcome_and_not_another", {})
        .get("the_imperfect_fit", "")
        .strip()
    ):
        raise ValidationError(
            "where an outcome fits imperfectly the record must say so, rather than choosing the "
            "one whose wording bends most easily"
        )

    target = selection["future_target_proposition"]
    for excluded in ("scanner name", "vendor name", "measurement value", "evidence direction"):
        if excluded not in target["excluded_from_identity"]:
            raise ValidationError(f"§29: {excluded!r} may not enter target identity")
    if target.get("scanner_identity_required_in_identity") is not False:
        raise ValidationError(
            "§18: if scanner identity must enter the proposition to make it true, the route fails "
            "on vantage relativity"
        )

    window = selection["window_and_threshold"]
    if window.get("window_width_selected") is not False:
        raise ValidationError("§23: no final window width is chosen in this mission")
    if window.get("threshold_selected") is not False or window.get("threshold_value") is not None:
        raise ValidationError("§40: this mission creates and chooses no threshold")
    if not window.get("why_that_does_not_make_the_claim_unfalsifiable", "").strip():
        raise ValidationError(
            "§22: a within-window existential at host level is not Claim-level monotonicity, and "
            "the record must distinguish them"
        )

    fixtures = selection["structural_fixtures"]
    for name in ("same_target_identity", "independent_support", "contradiction"):
        if fixtures[name].get("persisted") is not False:
            raise ValidationError(f"§44/§45: the {name} fixture must never be persisted")
        if fixtures[name].get("executed") is not True:
            raise ValidationError(
                f"the {name} fixture is recorded as a result and must actually have been run"
            )
    diagnostic = fixtures["disagreement_diagnostic"]
    if diagnostic["answer"] not in (
        "LEGITIMATE_INDEPENDENT_MEASUREMENT_DIFFERENCE_POSSIBLE",
        "NECESSARILY_A_BUG",
    ):
        raise ValidationError(f"§46: unrecognised diagnostic answer {diagnostic['answer']!r}")
    if not diagnostic.get("the_distinction_that_must_survive", "").strip():
        raise ValidationError(
            "§46: an acceptable measurement difference must be distinguished from different "
            "population or time definitions, which is what the last two missions failed on"
        )

    asymmetry = selection["positive_negative_asymmetry"]
    if not asymmetry.get("consequence", "").strip():
        raise ValidationError(
            "§19: non-observation is ambiguous and must never be read as the host being absent"
        )

    governance = selection["governance"]
    for name in ("sources_registered", "reviews_created", "purchases", "trials_started"):
        if governance.get(name) != 0:
            raise ValidationError(f"§9: {name} must be 0 in an epistemic selection mission")

    counters = selection["counters"]
    for name in (
        "research_data_requests",
        "target_measurement_requests",
        "target_host_record_requests",
        "target_count_requests",
        "facets_fetched",
        "trials_started",
        "purchases",
        "queries_executed",
        "model_calls",
        "embeddings",
        "canonical_mutations",
        "sources_registered",
        "governance_reviews_created",
        "collectors_implemented",
        "normalizers_implemented",
        "threshold_registrations_created",
        "claims_created",
        "evidence_created",
        "reliability_assessments_created",
        "reliability_values_assigned",
        "independence_groups_created",
        "scores_created",
        "opportunity_changes",
    ):
        if counters.get(name) != 0:
            raise ValidationError(
                f"§53/§54/§55/§56: {name} must be 0 and reads {counters.get(name)!r}"
            )
    if counters.get("mission_1_56_claim_modified") is not False:
        raise ValidationError("the Mission 1.56 Claim is untouched")
    if counters.get("reference_profile") != "UNCALIBRATED":
        raise ValidationError("§56: no calibration happens here")

    nxt = selection["next_mission_recommendation"]
    forbidden = " ".join(nxt.get("it_must_not", [])).lower()
    for rule in ("fetch a measurement value", "trial", "purchase"):
        if rule not in forbidden:
            raise ValidationError(f"the recommendation must forbid {rule!r}")
    if not nxt.get("it_should"):
        raise ValidationError("the recommendation says what the next mission does")


# ----------------------------------------------------------------- rendering


def render_baseline(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Observation-Addressable Scanner Selection — Baseline V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_scanner_pair_selection.py`.")
    add("")
    pre = record["repository_precondition"]
    add(
        f"Mission 1.59 merged as PR #{pre['pull_request']} at `{pre['merge_commit']}`, "
        f"migration head `{pre['migration_head']}`, branch `{pre['branch']}`."
    )
    add("")

    add("## Counters")
    add("")
    add(_row(["counter", "value"]))
    add(_row(["---", "---"]))
    for key, value in record["counters"].items():
        add(_row([f"`{key}`", f"**{value}**"]))
    add("")

    carried = record["carried_forward"]
    add("## Carried forward")
    add("")
    failed = carried["failed_apparatus_a"]
    add(f"**Dropped:** {failed['identity']} — `{failed['status']}`.")
    add("")
    add(failed["reason"])
    add("")
    add(f"*{failed['permanently_dropped_because']}*")
    add("")
    anchor = carried["anchor_candidate_b"]
    add(
        f"**Anchor:** {anchor['identity']} — `{anchor['status_carried']}`, not "
        + ", ".join(f"`{n}`" for n in anchor["not"])
        + "."
    )
    add("")
    add(anchor["why_carried"])
    add("")
    construct = carried["protocol_native_construct"]
    add(f"**Construct** ({construct['basis']}):")
    add("")
    add(f"> {construct['definition']}")
    add("")
    add("Properties: " + ", ".join(f"`{p}`" for p in construct["properties"]) + ".")
    add("")
    addressable = carried["observation_addressable_exposure"]
    add(
        f"**`OBSERVATION_ADDRESSABLE_EXPOSURE`** — {addressable['status']}, from {addressable['introduced_by']}."
    )
    add("")
    add(addressable["definition"])
    add("")
    add("It is **not**: " + "; ".join(addressable["is_not"]) + ".")
    add("")

    ledger = record["documentation_ledger"]
    add("## Documentation ledger")
    add("")
    add(
        f"**{ledger['used']} of {ledger['budget']} retrievals.** Research-data requests "
        f"**{ledger['research_data_requests']}**, target measurement requests "
        f"**{ledger['target_measurement_requests']}**, counts **{ledger['target_count_requests']}**, "
        f"trials **{ledger['trials_started']}**, purchases **{ledger['purchases']}**."
    )
    add("")
    add(_row(["", "kind", "apparatus", "target", "established"]))
    add(_row(["---", "---", "---", "---", "---"]))
    for entry in ledger["requests"]:
        add(
            _row(
                [
                    str(entry["n"]),
                    entry["kind"],
                    entry["apparatus"],
                    f"`{entry.get('url') or entry.get('target', '')}`",
                    entry.get("established") or entry.get("result", ""),
                ]
            )
        )
    add("")
    exposure = record["value_exposure"]
    add(
        f"**Queries executed: {exposure['queries_executed']}. Target measurement retrieved: "
        f"{exposure['target_measurement_retrieved']}.** {exposure['incidental_exposure']}"
    )
    add("")
    return "\n".join(lines) + "\n"


def render_contract(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Observation-Addressable Apparatus Contract V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_scanner_pair_selection.py`.")
    add("")

    add("## Individual hard gates")
    add("")
    add(_row(["", "gate", "rule"]))
    add(_row(["---", "---", "---"]))
    for gate in record["individual_hard_gates"]:
        add(_row([gate["id"], f"`{gate['gate']}`", gate["rule"]]))
    add("")

    boundary = record["observation_addressability_is_about_the_boundary"]
    add("## Addressability is about the boundary")
    add("")
    add(f"**{boundary['requirement']}**")
    add("")
    add("Passing shapes:")
    add("")
    for shape in boundary["passing_shapes"]:
        add(f"- {shape}")
    add("")
    add("Failing shapes:")
    add("")
    for shape in boundary["failing_shapes"]:
        add(f"- {shape}")
    add("")
    add(f"**The loophole this closes.** {boundary['the_loophole_this_closes']}")
    add("")
    add(
        "Acceptable time objects: "
        + ", ".join(f"`{t}`" for t in boundary["acceptable_time_objects"])
        + f". Rejected: `{boundary['rejected_time_object']}`."
    )
    add("")

    add("## Protocol predicate exposure classes")
    add("")
    add(_row(["class", "meaning"]))
    add(_row(["---", "---"]))
    for name, meaning in record["protocol_predicate_exposure_classes"].items():
        if name.startswith("$"):
            continue
        add(_row([f"`{name}`", meaning]))
    add("")

    boundary2 = record["metadata_versus_measurement"]
    add("## Metadata against measurement")
    add("")
    add("Permitted: " + ", ".join(boundary2["permitted"]) + ".")
    add("")
    add("Forbidden: " + ", ".join(boundary2["forbidden"]) + ".")
    add("")
    add(f"**{boundary2['the_count_is_not_metadata']}**")
    add("")
    add(f"**{boundary2['the_trial_is_not_free']}**")
    add("")

    registry = record["requirement_registry"]
    add("## The requirement registry")
    add("")
    add(_row(["requirement", "from", "rule"]))
    add(_row(["---", "---", "---"]))
    for item in registry["requirements"]:
        add(_row([f"`{item['name']}`", item["from"], item["rule"]]))
    add("")
    add(f"*{registry['how_to_use_this']}*")
    add("")
    return "\n".join(lines) + "\n"


def render_anchor(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Anchor Scanner Requalification V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_scanner_pair_selection.py`.")
    add("")
    apparatus = record["apparatus"]
    add(f"**{apparatus['identity']}** (`{apparatus['id']}`) — {apparatus['published_surface']}.")
    add("")

    add("## Gate results")
    add("")
    add(_row(["gate", "verdict"]))
    add(_row(["---", "---"]))
    for name, result in record["gate_results"].items():
        add(_row([f"`{name}`", f"**{result['verdict']}**"]))
    add("")
    for name, result in record["gate_results"].items():
        add(f"### `{name}` — {result['verdict']}")
        add("")
        for key, value in result.items():
            if key == "verdict":
                continue
            if isinstance(value, list):
                add(f"- `{key}`:")
                for item in value:
                    add(f"  - {item}")
            else:
                add(f"- `{key}`: {value}")
        add("")

    vantage = record["vantage"]
    add(f"## Vantage — `{vantage['status']}`")
    add("")
    add(vantage["what_is_missing"])
    add("")
    add(vantage["why_it_is_recorded_now"])
    add("")

    add(f"## Result — `{record['requalification_result']}`")
    add("")
    add(
        f"Individually qualifies: **{record['individually_qualifies']}**. "
        f"Blocking gates: {record['which_gates_block']}."
    )
    add("")
    add(record["not_invalidated"])
    add("")
    bought = record["what_the_requalification_actually_bought"]
    add(f"**{bought['statement']}**")
    add("")
    add(bought["detail"])
    add("")
    add(bought["consequence"])
    add("")
    return "\n".join(lines) + "\n"


def render_partners(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Observation-Addressable Partner Candidates V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_scanner_pair_selection.py`.")
    add("")
    discipline = record["search_discipline"]
    add(f"Class frozen: `{discipline['class_frozen']}`.")
    add("")
    add(discipline["queried_by_requirement_not_brand"])
    add("")
    add("Pruning order: " + " → ".join(discipline["pruning_order"]) + ".")
    add("")
    add(f"*{discipline['why_that_order']}*")
    add("")

    add("## Candidates")
    add("")
    add(_row(["identity", "first failing gate", "verdict", "researched here"]))
    add(_row(["---", "---", "---", "---"]))
    for candidate in record["candidates"]:
        add(
            _row(
                [
                    candidate["identity"],
                    f"`{candidate['first_failing_gate']}`",
                    f"**{candidate['verdict']}**",
                    str(candidate["researched_this_mission"]),
                ]
            )
        )
    add("")
    for candidate in record["candidates"]:
        add(
            f"**{candidate['identity']}.** {candidate.get('detail') or candidate.get('reason', '')}"
        )
        add("")

    result = record["partner_search_result"]
    add("## Result")
    add("")
    add(
        f"Inspected **{result['candidates_inspected']}**, researched here "
        f"**{result['of_which_researched_this_mission']}**, reached pair analysis "
        f"**{result['reached_pair_analysis']}**, qualifying **{result['qualifying_partners_found']}**."
    )
    add("")
    add(result["why_none_reached_pair_analysis"])
    add("")
    establishes = result["what_this_does_and_does_not_establish"]
    add(f"**Establishes.** {establishes['establishes']}")
    add("")
    add(f"**Does not establish.** {establishes['does_not_establish']}")
    add("")
    add(f"*{result['the_honest_shape_of_the_gap']}*")
    add("")
    pairs = record["pairs_constructed"]
    add(f"Pairs constructed: **{pairs['count']}**. {pairs['why']}")
    add("")
    return "\n".join(lines) + "\n"


def render_selection(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Observation-Addressable Scanner Pair Selection V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_scanner_pair_selection.py`.")
    add("")
    add(f"## Outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")
    add(f"Selected pair: **{record['selected_pair']}**.")
    add("")

    why = record["why_this_outcome_and_not_another"]
    add("### Why this outcome")
    add("")
    add(f"**The imperfect fit.** {why['the_imperfect_fit']}")
    add("")
    add(why["why_it_was_still_chosen"])
    add("")
    add(f"*{why['why_not_C']}*")
    add("")
    add(f"*{why['why_not_B']}*")
    add("")
    add(why["the_second_blocker_is_recorded_not_hidden"])
    add("")

    summary = record["gate_summary"]
    add("## Gate summary")
    add("")
    add(_row(["gate", "verdict"]))
    add(_row(["---", "---"]))
    for gate, verdict in summary["anchor"].items():
        add(_row([f"`{gate}`", f"**{verdict}**"]))
    add("")
    add(
        f"PASS **{summary['pass_count']}**, with bounds **{summary['pass_with_bounds_count']}**, "
        f"PARTIAL **{summary['partial_count']}**. Individually qualifies: "
        f"**{summary['individually_qualifies']}**."
    )
    add("")
    add(summary["why_pair_gates_not_evaluated"])
    add("")

    window = record["window_and_threshold"]
    add("## Window and threshold")
    add("")
    add(f"Window width selected: **{window['window_width_selected']}**. {window['why_not']}")
    add("")
    add(f"Duplicate rule: {window['duplicate_rule_form']}.")
    add("")
    add(f"**{window['why_that_does_not_make_the_claim_unfalsifiable']}**")
    add("")
    add(
        f"Threshold selected: **{window['threshold_selected']}**. "
        f"Preregistrable: **{window['can_a_threshold_later_be_preregistered']}**."
    )
    add("")
    add(window["what_is_determinable"])
    add("")

    fixtures = record["structural_fixtures"]
    add("## Structural fixtures")
    add("")
    for name in ("same_target_identity", "independent_support", "contradiction"):
        fixture = fixtures[name]
        add(f"**{name.replace('_', ' ')}.** {fixture['setup']} → {fixture['result']}.")
        add("")
    diagnostic = fixtures["disagreement_diagnostic"]
    add(f"**The diagnostic.** *{diagnostic['question']}*")
    add("")
    add(f"`{diagnostic['answer']}` — {diagnostic['why']}")
    add("")
    add(f"**{diagnostic['the_distinction_that_must_survive']}**")
    add("")

    asymmetry = record["positive_negative_asymmetry"]
    add("## Positive against negative observation")
    add("")
    add(asymmetry["statement"])
    add("")
    add(asymmetry["consequence"])
    add("")

    add("## Counters")
    add("")
    add(_row(["counter", "value"]))
    add(_row(["---", "---"]))
    for key, value in record["counters"].items():
        add(_row([f"`{key}`", f"**{value}**"]))
    add("")

    survives = record["what_survives"]
    add("## What survives")
    add("")
    for key, value in survives.items():
        add(f"- **{key.replace('_', ' ')}.** {value}")
    add("")

    nxt = record["next_mission_recommendation"]
    add(f"## Next — {nxt['name']}")
    add("")
    add(nxt["why_this"])
    add("")
    add("It should:")
    add("")
    for item in nxt["it_should"]:
        add(f"- {item}")
    add("")
    add("It must not:")
    add("")
    for item in nxt["it_must_not"]:
        add(f"- {item}")
    add("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        baseline, contract, anchor, partners, selection = validate()
    except ValidationError as error:
        print(f"REFUSED  scanner pair selection: {error}")
        return 1

    rendered = {
        RENDERED[BASELINE]: render_baseline(baseline),
        RENDERED[CONTRACT]: render_contract(contract),
        RENDERED[ANCHOR]: render_anchor(anchor),
        RENDERED[PARTNERS]: render_partners(partners),
        RENDERED[SELECTION]: render_selection(selection),
    }

    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print(
            f"ok       {len(rendered)} selection documents match their records; "
            f"outcome {selection['primary_outcome']}"
        )
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {selection['primary_outcome']}")
    print(f"anchor   {anchor['requalification_result']}, blocks {anchor['which_gates_block']}")
    print(f"selected {selection['selected_pair']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
