"""Render and validate the Mission 1.57 independence-route records.

Four documents: the live baseline, the apparatus search specification, the
candidates with their decision matrix, and the feasibility verdict.

`validate()` enforces the decision RULES rather than the answer. A later mission
may select a different route; it may not select one by weakening a rule. So the
refusals here are all of one shape -- an organisation chart is not a lineage
proof, a republication is not a second measurement, an unknown is not an
independence, and a metric that measures its own measurer's reach is not a
source-independent proposition.

    uv run python infrastructure/scripts/render_independence_route.py
    uv run python infrastructure/scripts/render_independence_route.py --check

Every input is a repository file, so this is deterministic from an empty
database and safe in CI (Mission 1.37 §68: a gate that measures a deployment
cannot live in CI).
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

BASELINE = DATA / "independence-capable-route-baseline-v1.json"
REQUIREMENTS = DATA / "independence-capable-apparatus-requirements-v1.json"
CANDIDATES = DATA / "independence-capable-route-candidates-v1.json"
FEASIBILITY = DATA / "independence-capable-route-feasibility-v1.json"

RENDERED = {
    BASELINE: DATA / "independence-capable-route-baseline-v1.md",
    REQUIREMENTS: DATA / "independence-capable-apparatus-requirements-v1.md",
    CANDIDATES: DATA / "independence-capable-route-candidates-v1.md",
    FEASIBILITY: DATA / "independence-capable-route-feasibility-v1.md",
}

MANDATORY_GATES = 15

# The vocabulary a provenance relation may take. `KNOWN_INDEPENDENT` is the only
# one that permits selection, and it is the only one this validator makes hard to
# reach.
INDEPENDENT = "KNOWN_INDEPENDENT"
DEPENDENT_RELATIONS = {"KNOWN_DEPENDENT", "COMMON_UPSTREAM", "UNKNOWN"}

# Verdicts a negative control may carry. None of them is independence.
CONTROL_VERDICTS = {
    "DEPENDENT_REPUBLICATION",
    "COMMON_UPSTREAM_SOURCE",
    "COMMON_UPSTREAM_SOURCE and SEMANTIC_MISMATCH",
    "SAME_MEASUREMENT_UPSTREAM",
}

PRIMARY_OUTCOMES = {
    "INDEPENDENCE_CAPABLE_EVIDENCE_ROUTE_IDENTIFIED",
    "INDEPENDENCE_CAPABLE_ROUTE_GOVERNANCE_PENDING",
    "INDEPENDENCE_CAPABLE_ROUTE_ENGINEERING_PENDING",
    "PROVENANCE_INDEPENDENCE_NOT_ESTABLISHED",
    "COMMON_UPSTREAM_MEASUREMENT_BLOCKS_CANDIDATES",
    "SEMANTIC_ALIGNMENT_BLOCKS_CANDIDATES",
    "RELIABILITY_REVIEWABILITY_BLOCKS_CANDIDATES",
    "GOVERNANCE_BLOCKS_ONLY_VALID_ROUTE",
    "NO_INDEPENDENCE_CAPABLE_APPARATUS_ROUTE_IDENTIFIED",
    "INFERRED_TARGET_CONTRACT_GAP",
    "MISSION_1_56_NOT_MERGED",
    "MISSION_1_57_BASELINE_DRIFT",
    "ORCHESTRATOR_TEST_ISOLATION_BLOCKER",
    "INDEPENDENCE_CAPABLE_ROUTE_FEASIBILITY_BLOCKED",
}

ACTIONABILITY = {
    "ACTIONABLE_NOW_FOR_GOVERNED_PREPARATION",
    "EPISTEMICALLY_VALID_GOVERNANCE_PENDING",
    "EPISTEMICALLY_VALID_ENGINEERING_PENDING",
}

SELECTING_OUTCOMES = {
    "INDEPENDENCE_CAPABLE_EVIDENCE_ROUTE_IDENTIFIED",
    "INDEPENDENCE_CAPABLE_ROUTE_GOVERNANCE_PENDING",
    "INDEPENDENCE_CAPABLE_ROUTE_ENGINEERING_PENDING",
}

MATRIX_COLUMNS = 20


class ValidationError(Exception):
    """A route record claims something the decision rules do not permit."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    return json.loads(path.read_text(encoding="utf-8"))


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def validate() -> tuple[dict, dict, dict, dict]:  # noqa: C901
    baseline = _load(BASELINE)
    requirements = _load(REQUIREMENTS)
    candidates = _load(CANDIDATES)
    feasibility = _load(FEASIBILITY)

    _validate_baseline(baseline)
    _validate_requirements(requirements)
    _validate_candidates(candidates)
    _validate_feasibility(feasibility, candidates)
    return baseline, requirements, candidates, feasibility


def _validate_baseline(baseline: dict) -> None:
    pre = baseline["repository_precondition"]
    if pre.get("mission_1_56_merged") is not True:
        raise ValidationError(
            "Mission 1.56 is not recorded as merged, so this mission has no baseline to rest on"
        )
    if not pre.get("merge_commit", "").strip():
        raise ValidationError("the precondition must name the commit it verified")

    census = baseline["evidence_direction_census"]
    if census.get("CONTRADICTS", 0) < 1:
        raise ValidationError(
            "the baseline records no CONTRADICTS row, which contradicts Mission 1.56"
        )
    if census.get("claims_carrying_both_directions") != 0:
        raise ValidationError(
            "a Claim already carries both directions, so the contradiction case is no longer "
            "the gap this mission is about and the record needs rewriting rather than editing"
        )

    first = baseline["first_inferred_claim"]
    if first.get("modified_by_this_mission") is not False:
        raise ValidationError(
            "§36: the Mission 1.56 Claim is a completed artifact and is untouched"
        )
    if first.get("evidence_count") != 1 or first.get("provenance_groups") != 1:
        raise ValidationError("the first INFERRED Claim has exactly one witness and one group")
    if first.get("reliability_resolution") != "NO_APPLICABLE_ASSESSMENT":
        raise ValidationError("no reliability applies to the new INFERRED scope")

    exclusive = baseline["first_claim_is_not_the_route"]
    if exclusive.get("second_independent_measurement_possible") != "NO":
        raise ValidationError(
            "§3: the first pilot Claim measures a quantity generated by one platform's own logs. "
            "A second publication of it is not a second measurement, and selecting it would be "
            "the SOURCE_EXCLUSIVE_METRIC error this mission exists to avoid"
        )
    if exclusive.get("flag") != "SOURCE_EXCLUSIVE_METRIC":
        raise ValidationError("the source-exclusive finding must be flagged by name")

    exits = baseline["structural_exits_from_b2"]
    for key in ("route_a_established_independent_corroboration", "route_b_real_contradiction"):
        if not exits.get(key, "").strip():
            raise ValidationError(f"both structural exits must be stated; {key} is empty")


def _validate_requirements(requirements: dict) -> None:
    gates = requirements["mandatory_gates"]
    if len(gates) != MANDATORY_GATES:
        raise ValidationError(f"§6 defines {MANDATORY_GATES} mandatory gates, found {len(gates)}")
    if [g["n"] for g in gates] != list(range(1, MANDATORY_GATES + 1)):
        raise ValidationError("the gates must be numbered 1..15 in order")
    for gate in gates:
        if not gate.get("rule", "").strip():
            raise ValidationError(f"gate {gate['n']} states no rule")

    standard = requirements["independence_proof_standard"]
    if standard.get("partial_evidence_verdict") != "UNKNOWN":
        raise ValidationError(
            "§15: partial lineage evidence yields UNKNOWN. Any other value would let an "
            "incomplete proof become an independence finding"
        )
    if len(standard.get("required", [])) < 4:
        raise ValidationError("the affirmative standard has four parts and needs all of them")
    if not any("separate organisations" in item for item in standard.get("insufficient", [])):
        raise ValidationError(
            "the standard must name 'separate organisations' as insufficient, because it is the "
            "reasoning most likely to be reached for"
        )

    traps = {trap["trap"] for trap in requirements["named_traps"]}
    for required in ("COMPLEMENTARITY", "SAME_APPARATUS_REVISION", "GEOGRAPHIC_INDEPENDENCE"):
        if required not in traps:
            raise ValidationError(f"the {required} trap must be named")

    rule = requirements["value_inspection_rule"]
    if not rule.get("rule", "").strip() or not rule.get("why", "").strip():
        raise ValidationError(
            "§18: the rule forbidding value inspection during feasibility must state itself and "
            "its reason, because the property it protects is destroyed silently"
        )


def _validate_candidates(candidates: dict) -> None:  # noqa: C901
    discovery = candidates["external_discovery"]
    if discovery.get("research_data_requests") != 0:
        raise ValidationError("§40: RESEARCH_DATA_REQUESTS must be 0 in a feasibility mission")
    if discovery.get("measurement_values_fetched") != 0:
        raise ValidationError(
            "§18: a measurement value was fetched, which makes an honest PREREGISTERED "
            "classification impossible for this route for ever afterwards"
        )
    if discovery.get("apparatus_classes_considered", 0) > 5:
        raise ValidationError("§12 bounds external discovery at five apparatus classes")
    if discovery.get("pairs_seriously_evaluated", 0) > 3:
        raise ValidationError("§12 prefers at most three pairs for serious evaluation")
    if len(discovery["classes"]) != discovery["apparatus_classes_considered"]:
        raise ValidationError("the class list and the class count disagree")

    # A held pair that failed must say which gate it failed. "It did not work" is
    # not a finding a later mission can act on.
    held = candidates["held_pair_analysis"]
    if held.get("held_pair_passed") is not False and held["pair"].get("verdict") != "PASS":
        raise ValidationError("the held-pair verdict and the pass flag disagree")
    if (
        held["pair"]["verdict"] == "COMPLEMENTARY_NOT_CORROBORATING"
        and held["pair"].get("gate_1_same_external_construct") != "FAIL"
    ):
        raise ValidationError(
            "§21: a complementary pair fails the same-construct gate, and recording the verdict "
            "without the gate leaves it looking like a preference"
        )

    controls = candidates["negative_controls"]
    for name in (
        "world_bank_plus_fred",
        "world_bank_plus_eurostat",
        "wikimedia_alternative_publication_route",
    ):
        if name not in controls:
            raise ValidationError(f"negative control {name} is missing")
        control = controls[name]
        if control["verdict"] not in CONTROL_VERDICTS:
            raise ValidationError(
                f"negative control {name} carries verdict {control['verdict']!r}, which is not a "
                "dependence verdict. §7 requires these to keep failing under the new gates"
            )
        if not control.get("basis", "").strip():
            raise ValidationError(f"negative control {name} rests on nothing stated")
    if controls["world_bank_plus_eurostat"].get("promoted_by_the_inferred_layer") is not False:
        raise ValidationError(
            "the INFERRED layer fixes Claim identity and does not repair provenance dependence "
            "or semantic mismatch. Promoting this control would need new first-party evidence"
        )

    seen = set()
    for route in candidates["candidate_routes"]:
        rid = route["route_id"]
        if rid in seen:
            raise ValidationError(f"duplicate route id {rid}")
        seen.add(rid)
        if route["proposition_family"] != "THRESHOLD_STATE":
            raise ValidationError(f"{rid} is not a THRESHOLD_STATE route")
        relation = route["provenance_relation"]
        if relation not in {INDEPENDENT} | DEPENDENT_RELATIONS:
            raise ValidationError(f"{rid} carries unknown provenance relation {relation!r}")
        if relation == INDEPENDENT:
            basis = route.get("independence_basis", [])
            if len(basis) < 2:
                raise ValidationError(
                    f"{rid} claims KNOWN_INDEPENDENT on fewer than two pieces of documentary "
                    "basis. §15 requires the proof from BOTH sides"
                )
            for item in basis:
                if "separate organisation" in item or "different compan" in item:
                    raise ValidationError(
                        f"{rid} rests part of its independence on organisational separateness, "
                        "which §15 names as insufficient"
                    )

    matrix = candidates["decision_matrix"]
    if len(matrix["columns"]) != MATRIX_COLUMNS:
        raise ValidationError(f"§32 defines {MATRIX_COLUMNS} matrix columns")
    for rid, row in matrix["rows"].items():
        if rid not in seen:
            raise ValidationError(f"the matrix scores {rid}, which is not a candidate route")
        if len(row) != MATRIX_COLUMNS:
            raise ValidationError(f"{rid} has {len(row)} verdicts for {MATRIX_COLUMNS} columns")
        for cell in row:
            if cell not in ("PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE"):
                raise ValidationError(
                    f"{rid} carries matrix value {cell!r}. §32 admits four values and no score"
                )
    for rid in seen:
        if rid not in matrix["rows"]:
            raise ValidationError(f"{rid} is not scored in the decision matrix")


def _validate_feasibility(feasibility: dict, candidates: dict) -> None:  # noqa: C901
    outcome = feasibility["primary_outcome"]
    if outcome not in PRIMARY_OUTCOMES:
        raise ValidationError(f"unknown primary outcome {outcome!r}")

    selected = feasibility.get("selected_route")
    routes = {r["route_id"]: r for r in candidates["candidate_routes"]}
    matrix = candidates["decision_matrix"]

    if outcome in SELECTING_OUTCOMES:
        if selected not in routes:
            raise ValidationError(f"{outcome} selects {selected!r}, which is not a candidate")
        if feasibility.get("actionability") not in ACTIONABILITY:
            raise ValidationError("§47: a positive route carries exactly one actionability level")

        route = routes[selected]
        if route["provenance_relation"] != INDEPENDENT:
            raise ValidationError(
                f"§46 forbids selecting a route whose independence is {route['provenance_relation']}"
            )
        if route.get("falsifiability_verdict") != "PASS":
            raise ValidationError("§46: a selected route is falsifiable in both directions")
        for side in ("apparatus_a", "apparatus_b"):
            if route[side].get("reliability_reviewability") != "YES":
                raise ValidationError(
                    f"§46: {side} of the selected route is not reliability-reviewable, which is "
                    "the Mission 1.47 dead end repeating"
                )
        row = matrix["rows"][selected]
        blocking = {
            column: cell
            for column, cell in zip(matrix["columns"], row, strict=True)
            if cell == "FAIL"
        }
        if blocking:
            raise ValidationError(
                f"the selected route FAILS {sorted(blocking)}, so it did not pass every gate"
            )
        if not feasibility.get("why_selected"):
            raise ValidationError("a selection states its reasons")
        if not feasibility.get("not_selected_by_elimination", "").strip():
            raise ValidationError(
                "§46 forbids selecting a route merely because the alternatives are worse, and the "
                "record has to say why that is not what happened"
            )
    elif selected is not None:
        raise ValidationError(
            f"{outcome} is a negative outcome and must select nothing, not {selected!r}"
        )

    threshold = feasibility["threshold_strategy"]
    if threshold["classification"] not in (
        "PREREGISTRABLE_BEFORE_BOTH_MEASUREMENTS",
        "SOURCE_NATIVE_THRESHOLD",
        "EXTERNAL_NORM_THRESHOLD",
        "POST_HOC_FOR_HELD_MEASUREMENTS",
    ):
        raise ValidationError(f"unknown threshold strategy {threshold['classification']!r}")
    if threshold.get("registration_created_by_this_mission") is not False:
        raise ValidationError("§17: this mission creates no threshold registration")
    if threshold["classification"] == "PREREGISTRABLE_BEFORE_BOTH_MEASUREMENTS":
        conditions = threshold.get("conditions", [])
        if not any("no measurement value" in c for c in conditions):
            raise ValidationError(
                "a PREREGISTRABLE claim must state that no value may be fetched first, because "
                "PREREGISTERED is defined against RETRIEVAL"
            )

    fit = feasibility["inferred_contract_fit"]
    for excluded in ("source A", "measurement values", "evidence direction"):
        if excluded not in fit["excluded_from_identity"]:
            raise ValidationError(f"ADR-036 excludes {excluded!r} from proposition identity")
    if fit["verdict"] == "SUFFICIENT" and fit.get("schema_gap") != "none":
        raise ValidationError("a sufficient contract has no schema gap")
    if fit.get("cross_source_observed_revival") != "NOT_ATTEMPTED":
        raise ValidationError("§35: the cross-source OBSERVED convergence approach is not reopened")

    grouping = feasibility["future_independence_grouping_proof"]
    if grouping.get("groups_persisted") != 0:
        raise ValidationError(
            "§16: no EvidenceIndependenceGroup exists, because no Evidence pair does"
        )
    if len(grouping.get("basis_references", [])) < 2:
        raise ValidationError("a future grouping expectation names the documents it would rest on")

    scopes = feasibility["reliability_scopes_prepared_not_assigned"]
    if scopes.get("reliability_values_assigned") != 0:
        raise ValidationError("§28: this mission prepares scopes and assigns no reliability")
    for side in ("apparatus_a_scope", "apparatus_b_scope"):
        scope = scopes[side]
        if set(scope) != {
            "source_id",
            "resource_id",
            "record_kind_id",
            "claim_type",
            "proposition_kind",
        }:
            raise ValidationError(f"{side} is not the five-field reliability scope")
        if scope["claim_type"] != "INFERRED":
            raise ValidationError(f"{side} must be an INFERRED scope")

    governance = feasibility["governance"]
    if governance.get("sources_registered_by_this_mission") != 0:
        raise ValidationError("§29: no source is registered by a feasibility mission")
    if governance.get("reviews_created") != 0:
        raise ValidationError("§29: no review is created by a feasibility mission")

    counters = feasibility["counters"]
    zero = (
        "research_data_requests",
        "measurement_values_fetched",
        "model_calls",
        "embeddings",
        "canonical_mutations",
        "sources_registered",
        "collectors_implemented",
        "normalizers_implemented",
        "threshold_registrations_created",
        "claims_created",
        "evidence_created",
        "reliability_assessments_created",
        "independence_groups_created",
        "scores_created",
        "opportunity_changes",
    )
    for name in zero:
        if counters.get(name) != 0:
            raise ValidationError(f"§39/§41: {name} must be 0 and reads {counters.get(name)!r}")
    if counters.get("model_cost_usd") != 0.0:
        raise ValidationError("§41: no model was called, so the cost is zero")
    if counters.get("mission_1_56_claim_modified") is not False:
        raise ValidationError("§36: the Mission 1.56 Claim is untouched")
    if counters.get("reference_profile") != "UNCALIBRATED":
        raise ValidationError("§38: no calibration happens here")
    if counters.get("problem_family") != "PARKED":
        raise ValidationError("Problem-Family stays parked")

    if not feasibility["the_structural_finding"].get("statement", "").strip():
        raise ValidationError("the structural finding must be stated rather than named")

    nxt = feasibility["next_mission_recommendation"]
    if not nxt.get("name", "").strip() or not nxt.get("it_should"):
        raise ValidationError("the recommendation names a mission and says what it does")
    if not nxt.get("it_must_not"):
        raise ValidationError(
            "the recommendation must say what the next mission may NOT do, because the property "
            "most easily destroyed next is the one that makes PREREGISTERED honest"
        )


# ----------------------------------------------------------------- rendering


def render_baseline(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Independence-Capable Route — Baseline V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_independence_route.py`.")
    add("")

    pre = record["repository_precondition"]
    add("## Precondition")
    add("")
    add(
        f"Mission 1.56 merged as PR #{pre['pull_request']} at `{pre['merge_commit']}`, "
        f"migration head `{pre['migration_head']}`, branch `{pre['branch']}`. "
        f"ADR-036 / ADR-037 / ADR-038 all {pre['adr_036']}."
    )
    add("")
    add(f"*Verified from {pre['verified_from']}.*")
    add("")

    add("## Counters")
    add("")
    add(_row(["counter", "value"]))
    add(_row(["---", "---"]))
    for key, value in record["counters"].items():
        add(_row([f"`{key}`", f"**{value}**"]))
    add("")

    census = record["evidence_direction_census"]
    add("## Evidence direction census")
    add("")
    add(
        f"`SUPPORTS` **{census['SUPPORTS']}**, `CONTRADICTS` **{census['CONTRADICTS']}**, "
        f"Claims carrying both directions **{census['claims_carrying_both_directions']}**."
    )
    add("")
    add(census["what_the_zero_means"])
    add("")

    add("## The first INFERRED Claim")
    add("")
    first = record["first_inferred_claim"]
    add(f"> {first['statement']}")
    add("")
    for key in (
        "claim_id",
        "claim_revision_id",
        "proposition_key",
        "evidence_id",
        "evidence_direction",
        "signal_id",
        "threshold",
        "derivation_id",
        "input_observed_claim_id",
        "measurement_value",
        "reliability_resolution",
        "scorability",
        "provenance_groups",
    ):
        add(f"- `{key}`: {first[key]}")
    add("")

    add("## Why it is not the route")
    add("")
    exclusive = record["first_claim_is_not_the_route"]
    add(f"**`{exclusive['flag']}`.** {exclusive['reason']}")
    add("")
    add(f"*{exclusive['consequence']}*")
    add("")

    add("## What Mission 1.56 did and did not establish")
    add("")
    add("Established:")
    add("")
    for item in record["what_mission_1_56_established"]:
        add(f"- {item}")
    add("")
    add("Not established:")
    add("")
    for item in record["what_mission_1_56_did_not_establish"]:
        add(f"- {item}")
    add("")

    exits = record["structural_exits_from_b2"]
    add("## The two exits from the B-2 identity")
    add("")
    add(f"**Corroboration.** {exits['route_a_established_independent_corroboration']}")
    add("")
    add(f"**Contradiction.** {exits['route_b_real_contradiction']}")
    add("")
    add(exits["why_one_apparatus_pair_serves_both"])
    add("")
    return "\n".join(lines) + "\n"


def render_requirements(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Independence-Capable Apparatus — Requirements V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_independence_route.py`.")
    add("")
    add(f"Folds forward `{record['folds_forward']}`.")
    add("")

    changed = record["what_changed_since_mission_1_48"]
    add("## What changed, and what did not")
    add("")
    add(f"**Then.** {changed['then']}")
    add("")
    add(f"**Now.** {changed['now']}")
    add("")
    add(f"**Unchanged.** {changed['what_did_not_change']}")
    add("")
    add(f"*{changed['why_that_sentence_matters']}*")
    add("")

    definition = record["apparatus_definition"]
    add("## What an apparatus is")
    add("")
    add("Not: " + ", ".join(definition["an_apparatus_is_not"]) + ".")
    add("")
    add("But: " + ", ".join(f"`{f}`" for f in definition["an_apparatus_is"]) + ".")
    add("")
    add(definition["rule"])
    add("")

    add("## The fifteen mandatory gates")
    add("")
    add(_row(["", "gate", "rule"]))
    add(_row(["---", "---", "---"]))
    for gate in record["mandatory_gates"]:
        add(_row([str(gate["n"]), f"`{gate['gate']}`", gate["rule"]]))
    add("")

    standard = record["independence_proof_standard"]
    add("## The independence proof standard")
    add("")
    add("Insufficient:")
    add("")
    for item in standard["insufficient"]:
        add(f"- {item}")
    add("")
    add("Required, all four:")
    add("")
    for item in standard["required"]:
        add(f"- {item}")
    add("")
    add(
        f"Partial evidence yields **{standard['partial_evidence_verdict']}**. "
        f"{standard['unknown_is_not_a_failure_of_the_source']}"
    )
    add("")

    add("## Named traps")
    add("")
    add(_row(["trap", "rule"]))
    add(_row(["---", "---"]))
    for trap in record["named_traps"]:
        add(_row([f"`{trap['trap']}`", trap["rule"]]))
    add("")

    rule = record["value_inspection_rule"]
    add("## No value may be fetched during feasibility")
    add("")
    add(f"**{rule['rule']}**")
    add("")
    add(rule["why"])
    add("")
    add(f"*{rule['consequence_if_broken']}*")
    add("")
    return "\n".join(lines) + "\n"


def render_candidates(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Independence-Capable Route — Candidates V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_independence_route.py`.")
    add("")

    scan = record["portfolio_scan"]
    add("## The registered portfolio")
    add("")
    add(
        f"**{scan['sources_registered']} sources registered**, "
        f"{scan['with_a_local_private_research_v1_review']} with a local review, "
        f"{scan['without_any_local_review']} without one. "
        f"Eligible with no outstanding condition: "
        + ", ".join(f"`{s}`" for s in scan["eligible_locally_with_zero_unsatisfied_conditions"])
        + "."
    )
    add("")
    add(f"*{scan['note']}*")
    add("")

    held = record["held_apparatuses"]
    add(f"## The {held['count']} held apparatuses")
    add("")
    add(_row(["source", "record kind", "proposition kind", "measures"]))
    add(_row(["---", "---", "---", "---"]))
    for a in held["inventory"]:
        add(
            _row(
                [
                    f"`{a['source']}`",
                    f"`{a['record_kind']}`",
                    f"`{a['proposition_kind']}`",
                    a["measures"],
                ]
            )
        )
    add("")
    add(f"**{held['shared_subjects_across_apparatuses']['finding']}**")
    add("")

    pair = record["held_pair_analysis"]["pair"]
    add("## The one held pair")
    add("")
    add(f"`{pair['apparatus_a']}` against `{pair['apparatus_b']}`, on `{pair['shared_subject']}`.")
    add("")
    add(f"**Verdict `{pair['verdict']}`.** {pair['why']}")
    add("")
    add(f"*{pair['corroborated_by_the_codebase']}*")
    add("")
    add(pair["what_the_new_architecture_did_and_did_not_change"])
    add("")

    add("## Negative controls")
    add("")
    add(_row(["control", "verdict", "gates failed", "basis"]))
    add(_row(["---", "---", "---", "---"]))
    for name, control in record["negative_controls"].items():
        if name.startswith("$"):
            continue
        gates = control.get("gate_failed") or control.get("gates_failed")
        add(_row([f"`{name}`", f"**{control['verdict']}**", str(gates), control["basis"]]))
    add("")

    discovery = record["external_discovery"]
    add("## Bounded external discovery")
    add("")
    add(
        f"Required **{discovery['was_required']}**. Research-data requests "
        f"**{discovery['research_data_requests']}**, methodology-document requests "
        f"**{discovery['first_party_method_doc_requests']}**, measurement values fetched "
        f"**{discovery['measurement_values_fetched']}**."
    )
    add("")
    add(_row(["apparatus class", "two independent processes plausible", "why"]))
    add(_row(["---", "---", "---"]))
    for cls in discovery["classes"]:
        add(
            _row(
                [
                    f"`{cls['class']}`",
                    f"**{cls['two_independent_processes_plausible']}**",
                    cls["why"],
                ]
            )
        )
    add("")

    add("## Candidate routes")
    add("")
    for route in record["candidate_routes"]:
        add(f"### `{route['route_id']}`")
        add("")
        add(
            f"Metric: {route['metric_definition']}. Unit `{route['unit']}`. "
            f"Provenance relation **{route['provenance_relation']}**. "
            f"Semantic verdict **{route['semantic_equivalence_verdict']}**."
        )
        add("")
        if route["provenance_relation"] == INDEPENDENT:
            add("**Independence basis.**")
            add("")
            for item in route.get("independence_basis", []):
                add(f"- {item}")
            add("")
            if route.get("independence_limitation_recorded"):
                add(f"*Limitation.* {route['independence_limitation_recorded']}")
                add("")
        for key in ("why_independence_does_not_rescue_it", "why_rejected"):
            if route.get(key):
                add(f"**Why rejected.** {route[key]}")
                add("")
        if route.get("second_independent_failure"):
            add(f"*A second, independent failure.* {route['second_independent_failure']}")
            add("")
        if route.get("exact_blockers"):
            add("**Blockers.**")
            add("")
            for item in route["exact_blockers"]:
                add(f"- {item}")
            add("")

    matrix = record["decision_matrix"]
    add("## Decision matrix")
    add("")
    add(_row(["criterion"] + [f"`{r.split('-')[1]}`" for r in matrix["rows"]]))
    add(_row(["---"] + ["---"] * len(matrix["rows"])))
    for index, column in enumerate(matrix["columns"]):
        add(_row([f"`{column}`"] + [matrix["rows"][r][index] for r in matrix["rows"]]))
    add("")
    add(matrix["governance_unknown_note"])
    add("")
    return "\n".join(lines) + "\n"


def render_feasibility(record: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Independence-Capable Route — Feasibility V1")
    add("")
    add(f"**Mission {record['mission']} — recorded {record['recorded_at']}.**")
    add("")
    add("> **This document is GENERATED.** Edit the JSON and re-run")
    add("> `infrastructure/scripts/render_independence_route.py`.")
    add("")
    add(f"## Outcome — `{record['primary_outcome']}`")
    add("")
    add(record["primary_outcome_statement"])
    add("")
    add(
        f"Actionability: **`{record['actionability']}`**. Selected route: **`{record['selected_route']}`**."
    )
    add("")
    add("**Why selected.**")
    add("")
    for item in record["why_selected"]:
        add(f"- {item}")
    add("")
    add(f"*{record['not_selected_by_elimination']}*")
    add("")

    reservation = record["the_reservation_the_operator_should_weigh"]
    add(f"## The reservation — `{reservation['flag']}`")
    add("")
    add(reservation["detail"])
    add("")
    add(f"**What the route is for.** {reservation['what_the_route_is_actually_for']}")
    add("")
    add(f"**Transferability.** {reservation['the_transferability_limitation']}")
    add("")
    add(f"*{reservation['the_honest_alternative']}*")
    add("")

    finding = record["the_structural_finding"]
    add("## The structural finding")
    add("")
    add(f"**{finding['statement']}**")
    add("")
    add(finding["worked_through"])
    add("")
    add(f"**It generalises.** {finding['generalises']}")
    add("")
    add(f"**Consequence.** {finding['consequence_for_the_product']}")
    add("")
    add(f"*{finding['why_this_is_not_a_counsel_of_despair']}*")
    add("")

    proofs = record["symbolic_proofs"]
    add("## Symbolic proofs")
    add("")
    corroboration = proofs["corroboration_case"]
    add("**Corroboration.** " + corroboration["setup"])
    add("")
    add(f"    {corroboration['saturation']}")
    add(f"    {corroboration['result']}")
    add("")
    add(corroboration["why_that_matters"])
    add("")
    contradiction = proofs["contradiction_case"]
    add("**Contradiction.** " + contradiction["setup"])
    add("")
    add(f"{contradiction['result']}. {contradiction['current_state']}")
    add("")
    add(contradiction["what_this_route_would_change"])
    add("")

    fit = record["inferred_contract_fit"]
    add(f"## Contract fit — `{fit['verdict']}`")
    add("")
    add(fit["detail"])
    add("")
    add("Identity: " + ", ".join(f"`{f}`" for f in fit["target_identity_fields"]) + ".")
    add("")
    add("Excluded: " + ", ".join(f"`{f}`" for f in fit["excluded_from_identity"]) + ".")
    add("")

    threshold = record["threshold_strategy"]
    add(f"## Threshold strategy — `{threshold['classification']}`")
    add("")
    for condition in threshold["conditions"]:
        add(f"- {condition}")
    add("")
    add(
        f"**Source-native or external norm.** {threshold['source_native_or_external_norm_available']}"
    )
    add("")
    add(f"**The scale caveat.** {threshold['the_scale_caveat_that_bears_on_the_threshold']}")
    add("")

    scopes = record["reliability_scopes_prepared_not_assigned"]
    add("## Reliability scopes, prepared and not assigned")
    add("")
    add(_row(["field", "apparatus A", "apparatus B"]))
    add(_row(["---", "---", "---"]))
    for field in ("source_id", "resource_id", "record_kind_id", "claim_type", "proposition_kind"):
        add(
            _row(
                [
                    f"`{field}`",
                    scopes["apparatus_a_scope"][field],
                    scopes["apparatus_b_scope"][field],
                ]
            )
        )
    add("")
    add(f"Values assigned: **{scopes['reliability_values_assigned']}**. {scopes['note']}")
    add("")

    governance = record["governance"]
    add("## Governance")
    add("")
    add(
        f"Apparatus A **{governance['apparatus_a']}**, apparatus B "
        f"**{governance['apparatus_b']}**. Sources registered "
        f"**{governance['sources_registered_by_this_mission']}**, reviews created "
        f"**{governance['reviews_created']}**."
    )
    add("")
    add(governance["why_this_is_pending_rather_than_blocked"])
    add("")
    add(f"*Commercial, separately.* {governance['commercial_position_recorded_separately']}")
    add("")

    add("## Counters")
    add("")
    add(_row(["counter", "value"]))
    add(_row(["---", "---"]))
    for key, value in record["counters"].items():
        add(_row([f"`{key}`", f"**{value}**"]))
    add("")

    nxt = record["next_mission_recommendation"]
    add(f"## Next — {nxt['name']}")
    add("")
    add(nxt["why_governance_first"])
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
    add(nxt["after_that"])
    add("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        baseline, requirements, candidates, feasibility = validate()
    except ValidationError as error:
        print(f"REFUSED  independence route: {error}")
        return 1

    rendered = {
        RENDERED[BASELINE]: render_baseline(baseline),
        RENDERED[REQUIREMENTS]: render_requirements(requirements),
        RENDERED[CANDIDATES]: render_candidates(candidates),
        RENDERED[FEASIBILITY]: render_feasibility(feasibility),
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
            f"ok       {len(rendered)} route documents match their records; "
            f"outcome {feasibility['primary_outcome']}"
        )
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {feasibility['primary_outcome']}")
    print(f"selected {feasibility['selected_route']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
