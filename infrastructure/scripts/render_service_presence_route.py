"""Render and validate the Mission 1.59 service-presence gate-closure records.

Five documents: the baseline and documentation ledger, the protocol-native metric
definition, the time contract, the lineage review, and the sixteen-gate verdict.

`validate()` enforces the rules a later mission could most easily bend to make a
route pass. They all have one shape: a vendor's opinion is not a standard, a
last-change time is not an observation time, an absence is not a statement, and
a route that fails one gate is not selected because it passed fifteen.

    uv run python infrastructure/scripts/render_service_presence_route.py
    uv run python infrastructure/scripts/render_service_presence_route.py --check

Every input is a repository file, so this is deterministic from an empty database
and safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "internet-wide-service-presence-gate-closure-baseline-v1.json"
METRIC = DATA / "internet-wide-service-presence-metric-definition-v1.json"
TIME = DATA / "internet-wide-service-presence-time-contract-v1.json"
LINEAGE = DATA / "internet-wide-service-presence-lineage-review-v1.json"
CLOSURE = DATA / "internet-wide-service-presence-route-gate-closure-v1.json"

RENDERED = {
    BASELINE: DATA / "internet-wide-service-presence-gate-closure-baseline-v1.md",
    METRIC: DATA / "internet-wide-service-presence-metric-definition-v1.md",
    TIME: DATA / "internet-wide-service-presence-time-contract-v1.md",
    LINEAGE: DATA / "internet-wide-service-presence-lineage-review-v1.md",
    CLOSURE: DATA / "internet-wide-service-presence-route-gate-closure-v1.md",
}

TOTAL_GATES = 16
GATE_VERDICTS = ("PASS", "FAIL", "UNKNOWN", "PARTIAL", "PASS_IF_NARROWED", "NOT_APPLICABLE")

PRIMARY_OUTCOMES = {
    "INTERNET_WIDE_SERVICE_PRESENCE_ROUTE_EPISTEMICALLY_CLOSED",
    "PROTOCOL_METRIC_DEFINITION_NOT_ALIGNABLE",
    "SNAPSHOT_TIME_SEMANTICS_NOT_ALIGNABLE",
    "SECOND_APPARATUS_LINEAGE_NOT_AFFIRMATIVELY_ESTABLISHED",
    "SAMPLING_FRAME_ALIGNMENT_GAP",
    "VANTAGE_RELATIVE_POPULATION_GAP",
    "RELIABILITY_REVIEWABILITY_REOPENED",
    "PRODUCT_RELEVANCE_LOST_AFTER_PROTOCOL_NARROWING",
    "PREREGISTRATION_POSSIBILITY_COMPROMISED",
    "MISSION_1_58_NOT_MERGED",
    "MISSION_1_59_BASELINE_DRIFT",
    "MISSION_1_59_CANONICAL_MUTATION",
    "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
    "INTERNET_WIDE_SERVICE_PRESENCE_GATE_CLOSURE_BLOCKED",
}

# Words that may never appear as the meaning of the metric. Adoption, users and
# customers are the three a reader supplies for free if the record does not
# refuse them by name.
OVERCLAIMS = ("installation", "user", "customer", "revenue", "demand", "adoption", "market share")

# Names a metric may not carry, because the name outlives every later caveat.
FORBIDDEN_METRIC_NAMES = (
    "product_installations",
    "service_users",
    "market_adoption",
    "customer_hosts",
)


class ValidationError(Exception):
    """A gate-closure record claims something the rules do not permit."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    return json.loads(path.read_text(encoding="utf-8"))


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def validate() -> tuple[dict, dict, dict, dict, dict]:
    baseline = _load(BASELINE)
    metric = _load(METRIC)
    time = _load(TIME)
    lineage = _load(LINEAGE)
    closure = _load(CLOSURE)

    _validate_baseline(baseline)
    _validate_metric(metric)
    _validate_time(time)
    _validate_lineage(lineage)
    _validate_closure(closure, metric, time, lineage)
    return baseline, metric, time, lineage, closure


def _validate_baseline(baseline: dict) -> None:
    pre = baseline["repository_precondition"]
    if pre.get("mission_1_58_merged") is not True:
        raise ValidationError("Mission 1.58 is not recorded as merged")
    if not pre.get("merge_commit", "").strip():
        raise ValidationError("the precondition must name the commit it verified")

    route = baseline["route_under_evaluation"]
    if route.get("substituted") is not False:
        raise ValidationError(
            "§1: this mission evaluates the route Mission 1.58 froze. Swapping in a pair that is "
            "easier to document answers a different question and calls it closure"
        )
    if not route.get("why_not_substituted", "").strip():
        raise ValidationError("the record must say why the frozen pair was kept")
    for side in ("apparatus_a", "apparatus_b"):
        if not route[side].get("identity", "").strip():
            raise ValidationError(
                f"{side} is unnamed. A class survey may describe apparatuses; a route handed to a "
                "governance mission must name them"
            )

    ledger = baseline["documentation_ledger"]
    if ledger["used"] != len(ledger["requests"]):
        raise ValidationError("the ledger's count and its entries disagree")
    if ledger["used"] > ledger["budget"]:
        raise ValidationError(f"§43 bounds documentation requests at {ledger['budget']}")
    for name in (
        "measurement_endpoints_called",
        "measurement_values_fetched",
        "paid_access_purchased",
        "trials_started",
        "third_party_summaries_used_for_gate_closure",
    ):
        if ledger.get(name) != 0:
            raise ValidationError(f"§31/§33/§43: {name} must be 0 and reads {ledger.get(name)!r}")
    for entry in ledger["requests"]:
        if entry.get("load_bearing") and not entry.get("first_party"):
            raise ValidationError(
                f"request {entry['n']} is load-bearing and not first-party. §43 forbids closing a "
                "gate on a third-party summary"
            )

    exposure = baseline["value_exposure"]
    if exposure.get("target_measurement_retrieved") is not False:
        raise ValidationError(
            "§32: a target measurement was retrieved, which is PREREGISTRATION_POSSIBILITY_"
            "COMPROMISED and a hard stop rather than a note"
        )
    if exposure.get("preregistration_possibility_compromised") is not False:
        raise ValidationError("the two value-exposure flags disagree")


def _validate_metric(metric: dict) -> None:
    selected = metric["selected_construct"]
    if selected.get("vendor_fingerprint_required") is not False:
        raise ValidationError(
            "§9: a construct requiring a proprietary fingerprint fails gate 3. The route may not "
            "be rescued by choosing one vendor as the semantic authority"
        )
    if selected.get("classifier_inside_definition") is not False:
        raise ValidationError(
            "§9: a classifier inside the metric definition is FRAME_OR_CLASSIFIER_INSIDE_METRIC_"
            "DEFINITION, one layer down from Mission 1.57's frame trap"
        )
    name = selected["metric_name"]
    if name in FORBIDDEN_METRIC_NAMES:
        raise ValidationError(
            f"§37: the metric may not be named {name!r}. A name outlives every later caveat"
        )

    basis = selected["protocol_basis"]
    for field in ("standard", "section", "what_it_fixes", "why_this_is_unambiguous"):
        if not basis.get(field, "").strip():
            raise ValidationError(f"the protocol basis states no {field}")
    if basis.get("retrieved_first_party") is not True:
        raise ValidationError("§5: the protocol basis must be a retrieved standard, not a memory")

    classification = metric["fact_classification"]
    for family in ("PROTOCOL_NATIVE", "VENDOR_DERIVED", "LATENT_INFERENCE"):
        if not classification.get(family):
            raise ValidationError(f"§7 requires the {family} facts to be enumerated")
    for label in ("service or product name", "software version"):
        if not any(label in item for item in classification["VENDOR_DERIVED"]):
            raise ValidationError(
                f"§7: {label!r} is vendor-derived and must be named as such, because it is what a "
                "later mission will reach for"
            )

    meaning = metric["what_the_construct_does_and_does_not_mean"]
    if not meaning.get("bounded_meaning", "").strip():
        raise ValidationError(
            "§36: one bounded sentence, or the construct means whatever a reader supplies"
        )
    for word in OVERCLAIMS:
        if word not in " ".join(meaning["it_is_not"]).lower():
            raise ValidationError(
                f"§35: the record must refuse {word!r} by name. A reader supplies it for free "
                "otherwise, and a bounded sentence that does not say what it excludes is not bounded"
            )

    gate = metric["gate_3"]
    if gate["status"] not in GATE_VERDICTS:
        raise ValidationError(f"gate 3 carries verdict {gate['status']!r}")
    if gate["status"] == "PASS":
        for side in ("apparatus_A_mapping", "apparatus_B_mapping"):
            if "NOT_ESTABLISHED" in gate[side]:
                raise ValidationError(
                    "§8: gate 3 passes only if BOTH apparatuses would be evaluating the same "
                    f"predicate, and {side} says it is not established"
                )
    if gate.get("vendor_fingerprint_required") is not False:
        raise ValidationError("gate 3 records a vendor fingerprint requirement")


def _validate_time(time: dict) -> None:
    for side in ("apparatus_a_time_semantics", "apparatus_b_time_semantics"):
        block = time[side]
        if block.get("dataset_shape") not in (
            "MERGED_CURRENT_STATE",
            "DISCRETE_POINT_IN_TIME_OBSERVATIONS",
        ):
            raise ValidationError(f"{side} declares no recognised dataset shape")
        if not block.get("basis", "").strip():
            raise ValidationError(f"{side} rests on nothing stated")

    rules = time["alignment_rules_evaluated"]
    if len(rules) < 4:
        raise ValidationError("§15 requires at least four alignment rules to be evaluated")
    for name, rule in rules.items():
        if name.startswith("$"):
            continue
        if not rule.get("why", "").strip():
            raise ValidationError(f"alignment rule {name} carries a verdict and no reason")
    tolerance = rules.get("C_pre_frozen_maximum_timestamp_distance", {})
    if tolerance.get("verdict") == "SELECTED" and "basis" not in tolerance:
        raise ValidationError(
            "§16: a tolerance needs an operational basis. A round number chosen because it "
            "salvages the route is the analyst measuring themselves"
        )

    gate = time["gate_5"]
    if gate["status"] not in GATE_VERDICTS:
        raise ValidationError(f"gate 5 carries verdict {gate['status']!r}")
    if gate["status"] == "PASS":
        if gate.get("rule_freezable_before_values") is not True:
            raise ValidationError("§17: gate 5 passes only if the pairing rule is freezable first")
        if gate.get("retrospective_value_based_pairing_required") is not False:
            raise ValidationError(
                "§18: a rule applied after the values are in hand is not a preregistrable rule"
            )
        if (
            not gate.get("future_pairing_rule", "").strip()
            or gate["future_pairing_rule"] == "none available"
        ):
            raise ValidationError("a passing gate 5 names its pairing rule")
    else:
        if not gate.get("exact_blocker", "").strip():
            raise ValidationError("a failing gate 5 names its blocker")

    separation = time["separating_measurement_difference_from_world_change"]
    if not separation.get("requirement", "").strip():
        raise ValidationError(
            "§14: the record must state that the time rule is what lets a disagreement be "
            "attributed to measurement or to the world"
        )


def _validate_lineage(lineage: dict) -> None:
    gate = lineage["gate_10"]
    if gate["status"] not in GATE_VERDICTS:
        raise ValidationError(f"gate 10 carries verdict {gate['status']!r}")
    if gate.get("absence_of_evidence_treated_as_proof") is not False:
        raise ValidationError("§22: an absence is never upgraded to independence")
    if gate["status"] == "PASS":
        if not (gate.get("affirmative_A") and gate.get("affirmative_B")):
            raise ValidationError(
                "§47: gate 10 passes only with affirmative lineage on BOTH sides. One side "
                "documented and the other silent is PARTIAL"
            )
        if gate.get("common_measurement_upstream") not in (None, "none found", "none"):
            raise ValidationError("a load-bearing common upstream blocks gate 10")
    if len(gate.get("exact_basis", [])) < 2:
        raise ValidationError("gate 10 names the documentary basis for each side")

    shared = lineage["shared_auxiliary_inputs"]
    permitted = {
        "MEASUREMENT_UPSTREAM",
        "MEASUREMENT_UPSTREAM_IF_USED",
        "SAMPLING_FRAME_INPUT",
        "AUXILIARY_METADATA",
        "FINGERPRINT_DEFINITION",
        "NON_LOAD_BEARING",
    }
    for entry in shared["inputs"]:
        if entry["classification"] not in permitted:
            raise ValidationError(
                f"§25: {entry['input']!r} carries classification {entry['classification']!r}. Shared "
                "inputs are classified before their impact is decided, not treated alike"
            )
    frame_inputs = [e for e in shared["inputs"] if e["classification"] == "SAMPLING_FRAME_INPUT"]
    for entry in frame_inputs:
        if "which addresses" not in entry["impact"].lower():
            raise ValidationError(
                "§26: a sampling-frame input tells an apparatus WHICH ADDRESSES may exist, not "
                "which hosts run the service, and the record must say so rather than treating it "
                "as a measurement upstream"
            )
    if shared.get("load_bearing_common_measurement_upstream_found") is None:
        raise ValidationError(
            "the record must say whether a load-bearing common upstream was found"
        )
    kept_apart = shared.get("the_structural_point_that_still_holds", "")
    for level in ("STRUCTURAL_NON_REPUBLICATION", "APPARATUS_LINEAGE_ESTABLISHED"):
        if level not in kept_apart:
            raise ValidationError(
                f"§24: the record must name {level} and hold it apart from the other. Saying "
                "something about independence is not the same as distinguishing the two levels, "
                "and collapsing them is how a class-level fact becomes a pair-level proof"
            )

    enquiry = lineage["written_enquiry"]
    if enquiry.get("sent") is not False:
        raise ValidationError(
            "§23: this repository may prepare a message and may never imply it was delivered"
        )
    if "independent" in enquiry.get("draft_question", "").lower():
        raise ValidationError(
            "§23: the enquiry asks for facts about lineage, not for the word independent, which "
            "invites interpretation rather than information"
        )


def _validate_closure(closure: dict, metric: dict, time: dict, lineage: dict) -> None:  # noqa: C901
    outcome = closure["primary_outcome"]
    if outcome not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {outcome!r}")

    gates = closure["gate_matrix"]["gates"]
    if len(gates) != TOTAL_GATES:
        raise ValidationError(f"§48 recomputes all {TOTAL_GATES} gates, found {len(gates)}")
    if [g["n"] for g in gates] != list(range(1, TOTAL_GATES + 1)):
        raise ValidationError("the gates must be numbered 1..16 in order")
    for gate in gates:
        for field in ("old", "new"):
            if gate[field] not in GATE_VERDICTS:
                raise ValidationError(f"gate {gate['n']} carries {field} verdict {gate[field]!r}")
        if (gate["old"] != gate["new"]) != gate["changed"]:
            raise ValidationError(f"gate {gate['n']} misreports whether it changed")
        if not gate.get("reason", "").strip():
            raise ValidationError(f"gate {gate['n']} states no reason")

    by_n = {g["n"]: g["new"] for g in gates}
    for source, n in (
        (metric["gate_3"]["status"], 3),
        (time["gate_5"]["status"], 5),
        (lineage["gate_10"]["status"], 10),
    ):
        if by_n[n] != source:
            raise ValidationError(
                f"the matrix records gate {n} as {by_n[n]!r} and its own record says {source!r}"
            )

    passing = [n for n, v in by_n.items() if v == "PASS"]
    selected = closure.get("selected_route")
    if selected is not None:
        if len(passing) != TOTAL_GATES:
            raise ValidationError(
                f"§49: a route is selected with {TOTAL_GATES - len(passing)} gates not passing. "
                "No PARTIAL, no UNKNOWN, no good enough"
            )
        if closure.get("actionability") != "EPISTEMICALLY_VALID_GOVERNANCE_PENDING":
            raise ValidationError(
                "§50: this mission performs no governance review, so a closed route is "
                "EPISTEMICALLY_VALID_GOVERNANCE_PENDING and never ACTIONABLE_NOW"
            )
    else:
        if len(passing) == TOTAL_GATES:
            raise ValidationError("every gate passes and no route is selected")
        if closure.get("actionability") is not None:
            raise ValidationError("§50: an unselected route carries no actionability level")

    counts = closure["gate_matrix"]
    for label, verdict in (
        ("pass_count", "PASS"),
        ("fail_count", "FAIL"),
        ("unknown_count", "UNKNOWN"),
        ("partial_count", "PARTIAL"),
    ):
        actual = sum(1 for v in by_n.values() if v == verdict)
        if counts.get(label) != actual:
            raise ValidationError(f"{label} reads {counts.get(label)} and the matrix has {actual}")
    reopened = sorted(g["n"] for g in gates if g["old"] == "PASS" and g["new"] != "PASS")
    if sorted(counts.get("gates_reopened", [])) != reopened:
        raise ValidationError(
            f"the reopened list {counts.get('gates_reopened')} disagrees with the matrix {reopened}"
        )

    fixtures = closure["structural_fixtures"]
    if fixtures["independent_support"].get("persisted") is not False:
        raise ValidationError("§54: structural fixtures are never persisted")
    diagnostic = fixtures["disagreement_diagnostic"]
    if diagnostic["answer"] not in (
        "POTENTIALLY_A_REAL_MEASUREMENT_DIFFERENCE",
        "NECESSARILY_A_BUG",
    ):
        raise ValidationError(f"§55: unrecognised diagnostic answer {diagnostic['answer']!r}")

    target = closure["future_target_proposition"]
    for excluded in ("scanner name", "vendor name", "measurement value", "evidence direction"):
        if excluded not in target["excluded"]:
            raise ValidationError(
                f"§38: {excluded!r} may not enter the target proposition identity"
            )
    if target.get("scanner_identity_required_in_identity") is not False:
        raise ValidationError(
            "§38: if scanner identity must enter the proposition to make it true, the route fails"
        )

    threshold = closure["threshold"]
    if threshold.get("selected") is not False or threshold.get("value_chosen") is not None:
        raise ValidationError("§40: this mission chooses no threshold value")

    counters = closure["counters"]
    for name in (
        "measurement_endpoints_called",
        "measurement_values_fetched",
        "paid_access_purchased",
        "trials_started",
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
            raise ValidationError(f"§58/§59/§60: {name} must be 0 and reads {counters.get(name)!r}")
    if counters.get("mission_1_56_claim_modified") is not False:
        raise ValidationError("the Mission 1.56 Claim is untouched")
    if counters.get("reference_profile") != "UNCALIBRATED":
        raise ValidationError("§60: no calibration happens here")

    nxt = closure["next_mission_recommendation"]
    if not nxt.get("it_should") or not nxt.get("it_must_not"):
        raise ValidationError("the recommendation says what the next mission does and does not do")
    if not any("fetch a measurement value" in item for item in nxt["it_must_not"]):
        raise ValidationError("the recommendation must forbid fetching a value")
    if not any("purchase" in item or "trial" in item for item in nxt["it_must_not"]):
        raise ValidationError(
            "§67: on a time-semantics failure the instruction is not to pay for governance or "
            "access, and the recommendation must carry it"
        )


# ----------------------------------------------------------------- rendering


def render_baseline(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Internet-Wide Service Presence — Gate Closure Baseline V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_service_presence_route.py`.")
    add("")
    pre = record["repository_precondition"]
    add(
        f"Mission 1.58 merged as PR #{pre['pull_request']} at `{pre['merge_commit']}`, "
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
    census = record["evidence_direction_census"]
    add(
        f"`SUPPORTS` **{census['SUPPORTS']}**, `CONTRADICTS` **{census['CONTRADICTS']}**, "
        f"Claims carrying both **{census['claims_carrying_both_directions']}**."
    )
    add("")

    route = record["route_under_evaluation"]
    add(f"## The route under evaluation — `{route['route_id']}`")
    add("")
    add(f"*{route['why_not_substituted']}*")
    add("")
    for side in ("apparatus_a", "apparatus_b"):
        a = route[side]
        add(f"**{a['identity']}** ({a['producer']}) — {a['interface']}.")
        add("")
        add(f"- construct: {a['claimed_construct']}")
        add(f"- scan model: {a['scan_model']}")
        add("")
    add(f"Product relevance: {route['product_relevance']}.")
    add("")

    add("## Starting gate state")
    add("")
    add(_row(["gate", "state"]))
    add(_row(["---", "---"]))
    for key, value in record["starting_gate_state"].items():
        if key.startswith("$"):
            continue
        add(_row([f"`{key}`", f"**{value}**"]))
    add("")
    add(f"Gates targeted: {record['gates_this_mission_targeted']}.")
    add("")
    add(record["gate_12_was_not_targeted"])
    add("")

    ledger = record["documentation_ledger"]
    add("## Documentation ledger")
    add("")
    add(
        f"**{ledger['used']} of {ledger['budget']} requests used.** Measurement endpoints called "
        f"**{ledger['measurement_endpoints_called']}**, measurement values fetched "
        f"**{ledger['measurement_values_fetched']}**, paid access purchased "
        f"**{ledger['paid_access_purchased']}**."
    )
    add("")
    add(_row(["", "kind", "target", "sought", "established"]))
    add(_row(["---", "---", "---", "---", "---"]))
    for entry in ledger["requests"]:
        target = entry.get("url") or entry.get("target", "")
        add(
            _row(
                [
                    str(entry["n"]),
                    entry["kind"],
                    f"`{target}`",
                    entry["sought"],
                    entry.get("established") or entry.get("result", ""),
                ]
            )
        )
    add("")
    exposure = record["value_exposure"]
    add(
        f"**Target measurement retrieved: {exposure['target_measurement_retrieved']}.** "
        f"{exposure['incidental_non_target_examples_seen']}"
    )
    add("")
    return "\n".join(lines) + "\n"


def render_metric(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Internet-Wide Service Presence — Metric Definition V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}. Gate 3.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_service_presence_route.py`.")
    add("")
    why = record["why_a_protocol_native_construct_is_required"]
    add(f"**The problem.** {why['the_problem']}")
    add("")
    add(f"**The refusal.** {why['the_refusal']}")
    add("")
    add(f"**And the alternative that was refused.** {why['the_alternative_that_was_refused']}")
    add("")

    add("## Fact classification")
    add("")
    classification = record["fact_classification"]
    for family in ("PROTOCOL_NATIVE", "VENDOR_DERIVED", "LATENT_INFERENCE"):
        add(f"**{family}**")
        add("")
        for item in classification[family]:
            add(f"- {item}")
        add("")
    add(classification["rule"])
    add("")

    selected = record["selected_construct"]
    add(f"## The construct — `{selected['metric_name']}`")
    add("")
    add(f"> {selected['definition']}")
    add("")
    basis = selected["protocol_basis"]
    add(f"**Protocol basis: {basis['standard']}, section {basis['section']}.**")
    add("")
    add(basis["what_it_fixes"])
    add("")
    add(basis["why_this_is_unambiguous"])
    add("")
    add(f"*Falsifier.* {selected['falsifier']}")
    add("")
    add(
        f"Vendor fingerprint required: **{selected['vendor_fingerprint_required']}**. "
        f"Classifier inside the definition: **{selected['classifier_inside_definition']}**."
    )
    add("")

    meaning = record["what_the_construct_does_and_does_not_mean"]
    add("## What it means, and what it does not")
    add("")
    add(f"> {meaning['bounded_meaning']}")
    add("")
    add("It is **not**:")
    add("")
    for item in meaning["it_is_not"]:
        add(f"- {item}")
    add("")
    add(meaning["product_relevance_after_narrowing"])
    add("")

    add("## Apparatus mapping")
    add("")
    for side in ("apparatus_a_censys", "apparatus_b_netlas"):
        block = record["apparatus_mapping"][side]
        add(f"**{side}**")
        add("")
        for key, value in block.items():
            add(f"- `{key}`: {value}")
        add("")

    gate = record["gate_3"]
    add(f"## Gate 3 — `{gate['status']}`")
    add("")
    add(f"**Blocker.** {gate['exact_blocker']}")
    add("")
    add(f"*Why not FAIL.* {gate['why_not_FAIL']}")
    add("")
    add(f"*Why not PASS.* {gate['why_not_PASS']}")
    add("")

    reusable = record["the_reusable_result"]
    add("## What is reusable")
    add("")
    add(f"**{reusable['statement']}**")
    add("")
    add(f"Requirement on a future pair: {reusable['requirement_on_a_future_pair']}")
    add("")
    add(reusable["a_second_benefit_worth_recording"])
    add("")
    return "\n".join(lines) + "\n"


def render_time(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Internet-Wide Service Presence — Time Contract V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}. Gate 5.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_service_presence_route.py`.")
    add("")
    why = record["why_cadence_is_not_the_question"]
    add(f"**{why['statement']}**")
    add("")
    add(why["consequence"])
    add("")

    for side, title in (
        ("apparatus_a_time_semantics", "Apparatus A"),
        ("apparatus_b_time_semantics", "Apparatus B"),
    ):
        block = record[side]
        add(f"## {title} — {block['identity']} — `{block['dataset_shape']}`")
        add("")
        for key, value in block.items():
            if key in ("identity", "dataset_shape"):
                continue
            add(f"- `{key}`: {value}")
        add("")

    mismatch = record["the_mismatch"]
    add("## The mismatch")
    add("")
    add(f"**{mismatch['statement']}**")
    add("")
    add(mismatch["why_a_window_filter_does_not_bridge_them"])
    add("")
    add(mismatch["why_current_state_does_not_bridge_them_either"])
    add("")

    add("## Alignment rules evaluated")
    add("")
    add(_row(["rule", "verdict", "why"]))
    add(_row(["---", "---", "---"]))
    for name, rule in record["alignment_rules_evaluated"].items():
        if name.startswith("$"):
            continue
        add(_row([f"`{name}`", f"**{rule['verdict']}**", rule["why"]]))
    add("")

    separation = record["separating_measurement_difference_from_world_change"]
    add("## Measurement difference against world change")
    add("")
    add(separation["requirement"])
    add("")
    add(f"**Under this pair.** {separation['under_this_pair']}")
    add("")

    gate = record["gate_5"]
    add(f"## Gate 5 — `{gate['status']}`")
    add("")
    add(
        f"Rule freezable before values: **{gate['rule_freezable_before_values']}**. "
        f"Retrospective pairing required: **{gate['retrospective_value_based_pairing_required']}**."
    )
    add("")
    add(f"**Blocker.** {gate['exact_blocker']}")
    add("")
    add(f"*Why FAIL rather than UNKNOWN.* {gate['why_FAIL_rather_than_UNKNOWN']}")
    add("")
    add(f"*What would change it.* {gate['what_would_change_it']}")
    add("")

    asymmetry = record["the_asymmetry_worth_carrying_forward"]
    add("## The asymmetry worth carrying forward")
    add("")
    add(f"**{asymmetry['statement']}**")
    add("")
    add(asymmetry["detail"])
    add("")
    add(f"**{asymmetry['the_requirement_this_mission_adds']}**")
    add("")
    return "\n".join(lines) + "\n"


def render_lineage(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Internet-Wide Service Presence — Lineage Review V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}. Gate 10.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_service_presence_route.py`.")
    add("")
    scope = record["how_far_this_was_pursued_and_why"]
    add(scope["statement"])
    add("")
    add(f"**Still worth doing.** {scope['what_was_still_worth_doing']}")
    add("")
    add(f"*{scope['what_this_record_is_not']}*")
    add("")

    add("## Evidence hierarchy")
    add("")
    add(_row(["level", "meaning"]))
    add(_row(["---", "---"]))
    for level, meaning in record["evidence_hierarchy_applied"].items():
        if level.startswith("$"):
            continue
        add(_row([f"`{level}`", meaning]))
    add("")

    for side, title in (
        ("apparatus_a_censys", "Apparatus A"),
        ("apparatus_b_netlas", "Apparatus B"),
    ):
        block = record[side]
        add(f"## {title}")
        add("")
        for key, value in block.items():
            if isinstance(value, list):
                add(f"- `{key}`:")
                for item in value:
                    add(f"  - {item}")
            else:
                add(f"- `{key}`: {value}")
        add("")

    shared = record["shared_auxiliary_inputs"]
    add("## Shared auxiliary inputs")
    add("")
    add(_row(["input", "classification", "impact"]))
    add(_row(["---", "---", "---"]))
    for entry in shared["inputs"]:
        add(_row([entry["input"], f"`{entry['classification']}`", entry["impact"]]))
    add("")
    add(shared["the_structural_point_that_still_holds"])
    add("")

    vantage = record["vantage_and_frame"]
    add("## Vantage and frame")
    add("")
    add(f"**Status `{vantage['status']}`.** {vantage['issue']}")
    add("")
    add(f"*Why it was not pursued.* {vantage['why_it_was_not_pursued']}")
    add("")
    add(f"**For the next pair.** {vantage['what_it_means_for_the_next_pair']}")
    add("")
    add(vantage["related_finding_already_in_hand"])
    add("")

    gate = record["gate_10"]
    add(f"## Gate 10 — `{gate['status']}`")
    add("")
    add(
        f"Affirmative A **{gate['affirmative_A']}**, affirmative B **{gate['affirmative_B']}**, "
        f"common measurement upstream **{gate['common_measurement_upstream']}**."
    )
    add("")
    for item in gate["exact_basis"]:
        add(f"- {item}")
    add("")

    enquiry = record["written_enquiry"]
    add("## Written enquiry")
    add("")
    add(f"Prepared **{enquiry['prepared']}**, sent **{enquiry['sent']}**.")
    add("")
    add(f"> {enquiry['draft_question']}")
    add("")
    add(enquiry["why_it_is_worded_that_way"])
    add("")
    return "\n".join(lines) + "\n"


def render_closure(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Internet-Wide Service Presence — Route Gate Closure V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_service_presence_route.py`.")
    add("")
    add(f"## Outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")
    add(f"Selected route: **{record['selected_route']}**. {record['why_no_actionability']}")
    add("")

    matrix = record["gate_matrix"]
    add("## The sixteen gates, recomputed")
    add("")
    add(_row(["", "gate", "was", "is", "reason"]))
    add(_row(["---", "---", "---", "---", "---"]))
    for gate in matrix["gates"]:
        marker = "**" if gate["changed"] else ""
        add(
            _row(
                [
                    str(gate["n"]),
                    f"`{gate['gate']}`",
                    gate["old"],
                    f"{marker}{gate['new']}{marker}",
                    gate["reason"],
                ]
            )
        )
    add("")
    add(
        f"PASS **{matrix['pass_count']}**, FAIL **{matrix['fail_count']}**, UNKNOWN "
        f"**{matrix['unknown_count']}**, PARTIAL **{matrix['partial_count']}**. "
        f"Reopened: {matrix['gates_reopened']}."
    )
    add("")
    add(matrix["reopening_is_success_of_the_audit"])
    add("")

    fixtures = record["structural_fixtures"]
    add("## Structural fixtures")
    add("")
    identity = fixtures["same_claim_identity"]
    add(f"**Same Claim identity.** {identity['setup']} → {identity['result']}.")
    add("")
    add(identity["what_it_proves"])
    add("")
    support = fixtures["independent_support"]
    add(
        f"**Independent support.** {support['setup']} → {support['result']}; control: {support['control']}."
    )
    add("")
    diagnostic = fixtures["disagreement_diagnostic"]
    add(f"**The diagnostic.** *{diagnostic['question']}*")
    add("")
    add(f"`{diagnostic['answer']}` — {diagnostic['why']}")
    add("")
    add(f"**And the caveat this mission adds.** {diagnostic['the_caveat_this_mission_adds']}")
    add("")

    threshold = record["threshold"]
    add("## Threshold")
    add("")
    add(f"Selected **{threshold['selected']}**. {threshold['why_not']}")
    add("")
    add(
        f"Preregistrable for this pair: **{threshold['can_a_threshold_later_be_preregistered_for_this_pair']}**. "
        f"For the class: **{threshold['can_it_for_the_class']}**."
    )
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
        if key.startswith("$"):
            continue
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
        baseline, metric, time, lineage, closure = validate()
    except ValidationError as error:
        print(f"REFUSED  service-presence route: {error}")
        return 1

    rendered = {
        RENDERED[BASELINE]: render_baseline(baseline),
        RENDERED[METRIC]: render_metric(metric),
        RENDERED[TIME]: render_time(time),
        RENDERED[LINEAGE]: render_lineage(lineage),
        RENDERED[CLOSURE]: render_closure(closure),
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
            f"ok       {len(rendered)} gate-closure documents match their records; "
            f"outcome {closure['primary_outcome']}"
        )
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    matrix = closure["gate_matrix"]
    print(f"outcome  {closure['primary_outcome']}")
    print(
        f"gates    PASS {matrix['pass_count']}, FAIL {matrix['fail_count']}, "
        f"UNKNOWN {matrix['unknown_count']}, PARTIAL {matrix['partial_count']}; "
        f"reopened {matrix['gates_reopened']}"
    )
    print(f"selected {closure['selected_route']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
