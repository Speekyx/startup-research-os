"""Render and validate the Q1 quantity-class selection and the construct evaluation.

A class was selected. A construct was not, and no run is authorised.

Four things this gate holds:

    THREE STATES STAY APART: CLASS_SELECTED, CONSTRUCT_SELECTED, RUN_AUTHORIZED.
    THE POPULATION IS NEVER DEFINED BY WHAT ANSWERED.
    A CATEGORICAL PREDICATE MAY NOT BE SMUGGLED THROUGH A THRESHOLD.
    A QUALIFIED PAIR IS NOT AN INDEPENDENCE JUDGEMENT.

The selection's premise is asserted LIVE rather than quoted: the counterpart qualification
must still read twelve PASS and RESOLVED, and the residual closure must still read zero. An
edit that quietly reopened either fails here rather than leaving a selection standing on a
premise that has gone.

The construct evaluation records that vantage is unresolved and names three coherent
resolutions without choosing one. The gate refuses a record that chooses one silently, that
selects a construct anyway, or that reports the vantage difference as measurement noise.

    uv run python infrastructure/scripts/render_q1_class_selection.py
    uv run python infrastructure/scripts/render_q1_class_selection.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

SELECTED = DATA / "selected-quantity-class-v1.json"
DECISION_V5 = DATA / "quantity-class-selection-decision-v5.json"
DECISION_V6 = DATA / "quantity-class-selection-decision-v6.json"
PACKAGE_V1 = DATA / "quantity-class-package-q1-v1.json"
PACKAGE_V2 = DATA / "quantity-class-package-q1-v2.json"
CONSTRUCTS = DATA / "http-construct-candidate-evaluation-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v4.json"
CLOSURE = DATA / "globalping-residual-closure-v3.json"
PRIORITY = DATA / "evidence-completion-priority-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"

RENDERED = DATA / "selected-quantity-class-v1.md"

CANDIDATES = ("CANDIDATE_A", "CANDIDATE_B", "CANDIDATE_C")
VANTAGE_RESOLUTIONS = (
    "V1_VANTAGE_IN_PROPOSITION_IDENTITY",
    "V2_UNIVERSAL_OVER_A_DEFINED_VANTAGE_CLASS",
    "V3_EXPLICIT_TOLERANCE",
)
# Differ on any of these and the two apparatuses are not addressing one proposition.
MUST_MATCH_FIELDS = (
    "SCHEME",
    "HOST",
    "PORT",
    "PATH",
    "QUERY",
    "METHOD",
    "REDIRECT_FOLLOWING",
    "HOST_HEADER_OVERRIDE",
    "OBSERVATION_WINDOW",
    "TLS_SNI",
)

DELTA_CRITERIA = (
    "SCORABILITY_REPAIR",
    "NEW_EVIDENCE_DIMENSION",
    "ESTABLISHED_INDEPENDENCE_POTENTIAL",
    "CONTRADICTION_POTENTIAL",
    "EXECUTION_READINESS",
)
HARD_ZERO = (
    "GLOBALPING_API_EXECUTIONS",
    "TARGET_HTTP_REQUESTS",
    "SROS_FETCHER_RUNS",
    "ROBOTS_REQUESTS",
    "MEASUREMENT_VALUES",
    "COMMON_CRAWL_QUERIES",
    "HTTP_ARCHIVE_QUERIES",
    "RESEARCH_DATA_REQUESTS",
    "PROVIDER_CONTACTS",
    "MAILBOX_READS",
    "CORPORA_FROZEN",
    "CONSTRUCTS_SELECTED",
    "RAW_RECORDS_CREATED",
    "SIGNALS_CREATED",
    "CLAIMS_CREATED",
    "EVIDENCE_CREATED",
    "INDEPENDENCE_GROUPS_CREATED",
    "THRESHOLD_REGISTRATIONS",
    "CLAIM_DERIVATIONS",
    "EVALUATION_REFUSALS",
    "SCORES",
    "EMBEDDINGS",
    "MIGRATIONS",
)


class ValidationError(RuntimeError):
    """The selection or the construct evaluation says something this gate refuses."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _check_three_states_stay_apart(selected: dict, decision: dict) -> None:
    if selected["state"] != "CLASS_SELECTED":
        raise ValidationError(f"the selection is in state {selected['state']!r}")
    states = selected["states_kept_apart"]
    if not states["CLASS_SELECTED"]:
        raise ValidationError("the selection does not record that a class was selected")
    for forbidden in ("CONSTRUCT_SELECTED", "RUN_AUTHORIZED"):
        if states[forbidden]:
            raise ValidationError(
                f"the selection records {forbidden}; that is a different decision and this "
                "artifact may not carry it"
            )
    if not str(states["why_three_and_not_one"]).strip():
        raise ValidationError("the selection does not say why the three states are kept apart")
    if selected["corpus_frozen"] or selected["exact_predicate_frozen"]:
        raise ValidationError("the class selection freezes a corpus or a predicate")
    if selected["measurements_executed"] != 0:
        raise ValidationError("the class selection records a measurement")
    if not selected["what_selection_does_not_authorise"]:
        raise ValidationError("the selection does not say what it fails to authorise")
    if SELECTED_CONSTRUCT.exists():
        raise ValidationError("a construct artifact exists and no construct was selected")

    if decision["selected_quantity_class"] != selected["class_id"]:
        raise ValidationError("the decision and the artifact name different classes")
    if decision["selection_outcome"] != "CLASS_SELECTED":
        raise ValidationError("the decision's outcome is not a class selection")
    if not decision["selected_class_artifact_created"]:
        raise ValidationError("the artifact exists and the decision denies creating it")
    if decision["selected_construct_created"]:
        raise ValidationError("the decision claims a construct artifact that must not exist")
    three = decision["three_states_kept_apart"]
    if three["CONSTRUCT_SELECTED"] or three["RUN_AUTHORIZED"]:
        raise ValidationError("the decision collapses the three states")


def _check_the_premise_still_holds(decision: dict) -> None:
    """The selection rests on a qualification, and a quoted premise is not a premise."""
    qualification = _load(QUALIFICATION)
    counted = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "UNKNOWN": 0}
    for row in qualification["gates"]:
        counted[row["status"]] += 1
    if counted != {"PASS": 12, "PARTIAL": 0, "FAIL": 0, "UNKNOWN": 0}:
        raise ValidationError(
            f"the counterpart qualification reads {counted}; a class was selected on twelve"
        )
    if qualification["verdict"] != "COUNTERPART_RESOLVED":
        raise ValidationError("the counterpart verdict moved and a selection rests on it")
    if _load(CLOSURE)["residuals_remaining"] != 0:
        raise ValidationError("a residual reopened and the selection rests on none remaining")
    if not decision["counterpart_qualified"] or not decision["q1_strategically_viable"]:
        raise ValidationError("the decision selects a class it records as unqualified")


def _check_the_supersessions(decision: dict, package: dict) -> None:
    v5 = _load(DECISION_V5)
    if v5["selected_quantity_class"] is not None or v5["selection_outcome"] != "NO_SELECTION":
        raise ValidationError(
            "the superseded decision was edited to agree; it recorded NO_SELECTION and that "
            "was true when it was written"
        )
    if v5["superseded_by"] != DECISION_V6.name:
        raise ValidationError("the superseded decision does not point at its successor")
    if decision["supersedes"] != DECISION_V5.name:
        raise ValidationError("the new decision does not name what it supersedes")

    v1 = _load(PACKAGE_V1)
    if v1["class_verdict"] == "STRATEGICALLY_VIABLE":
        raise ValidationError(
            "the superseded package was re-graded in place; it evaluated a different route "
            "pair and its verdict on that pair stands"
        )
    if v1["superseded_by"] != PACKAGE_V2.name:
        raise ValidationError("the superseded package does not point at its successor")
    if package["class_verdict"] != "STRATEGICALLY_VIABLE":
        raise ValidationError("a class was selected whose package is not strategically viable")
    if len(package["routes"]) != 2:
        raise ValidationError("a class was selected without exactly two routes")
    if {r["production"] for r in package["routes"]} != {"OWN_MEASUREMENT"}:
        raise ValidationError("a route does not produce its own measurement")
    if package["same_proposition"] == "ESTABLISHED":
        raise ValidationError(
            "the package claims the same proposition is established; that is the construct "
            "question and it did not close"
        )
    if not str(package["why_still_not_established"]).strip():
        raise ValidationError("the package does not say why the proposition is unestablished")


def _check_no_construct_was_selected_and_vantage_is_open(constructs: dict) -> None:
    if constructs["selected_construct"] is not None:
        raise ValidationError("a construct was selected and this mission selects none")
    if constructs["exact_predicate_frozen"]:
        raise ValidationError("a predicate was frozen")
    if constructs["measurements_executed"] != 0 or constructs["target_values_retrieved"] != 0:
        raise ValidationError("the construct evaluation records a measurement")

    ids = [c["id"] for c in constructs["candidates"]]
    for required in CANDIDATES:
        if required not in ids:
            raise ValidationError(f"{required} was not evaluated")
    for candidate in constructs["candidates"]:
        if candidate["verdict"].startswith("SELECTED"):
            raise ValidationError(f"{candidate['id']} is recorded as selected")
        for field in ("predicate", "e_rule", "p_rule", "verdict"):
            if not str(candidate[field]).strip():
                raise ValidationError(f"{candidate['id']} states no {field}")

    vantage = constructs["vantage"]
    if vantage["which_was_chosen"] is not None:
        raise ValidationError(
            "a vantage semantics was chosen; each has a different real cost and choosing the "
            "one that makes a construct appear is choosing a semantics for its convenience"
        )
    named = [r["id"] for r in vantage["three_coherent_resolutions"]]
    for resolution in VANTAGE_RESOLUTIONS:
        if resolution not in named:
            raise ValidationError(f"the vantage resolution {resolution} is not recorded")
    for resolution in vantage["three_coherent_resolutions"]:
        if not str(resolution["cost"]).strip():
            raise ValidationError(f"{resolution['id']} is recorded with no cost")
    if vantage["the_finding"] != "VANTAGE_IS_PROPOSITION_UNDERSPECIFICATION_NOT_MEASUREMENT_NOISE":
        raise ValidationError(
            "the record treats vantage divergence as measurement noise; a target that answers "
            "differently by geography makes the proposition undefined rather than the "
            "witnesses noisy"
        )
    if not vantage["both_vantages_are_stated"]:
        raise ValidationError("the record claims a vantage is unstated; both apparatuses state one")
    if not str(vantage["why_none_was_chosen_here"]).strip():
        raise ValidationError("the record does not say why no resolution was chosen")


def _check_the_denominator_is_never_outcome_selected(constructs: dict) -> None:
    shape = constructs["proposition_shape"]
    if shape["preferred"] != "TARGET_LEVEL":
        raise ValidationError(
            "a corpus aggregate is preferred; the two apparatuses evaluate different subsets "
            "and restricting to the common one selects on the measurement's own outcome"
        )
    for option in ("corpus_count_or_rate", "corpus_existential"):
        if not str(shape["why_corpus_level_is_worse_here"][option]).strip():
            raise ValidationError(f"the record does not say why {option} is worse")

    missing = constructs["missingness"]
    if missing["targets_removed_from_N_for_any_outcome"] != 0:
        raise ValidationError("a target was removed from N for an outcome")
    if not missing["excluded_targets_remain_terminal_records"]:
        raise ValidationError(
            "an excluded target leaves the population instead of terminating in it"
        )
    if missing["outcome_selected_denominator"]:
        raise ValidationError("the denominator is selected on the measurement's own outcome")
    if not missing["apparatus_failure_is_not_a_world_fact"]:
        raise ValidationError("apparatus failure is recorded as a fact about the target")
    if "manifest" not in missing["denominator_rule"]:
        raise ValidationError("N is not the frozen manifest")


def _check_the_evaluator_gap_is_reported_not_routed_around(constructs: dict) -> None:
    evaluator = constructs["evaluator_compatibility"]
    if evaluator["fits_a_target_level_http_predicate"]:
        raise ValidationError(
            "a categorical class-membership predicate is recorded as fitting the threshold "
            "evaluator; the evaluator accepting an integer is not evidence that the quantity "
            "is a magnitude"
        )
    if evaluator["what_would_be_required"] != "CATEGORICAL_MEMBERSHIP_EVALUATOR":
        raise ValidationError("the record does not name what a target-level predicate needs")
    if evaluator["inferred_claim_compatibility"]["source_id_in_identity"]:
        raise ValidationError("source_id is in a source-independent proposition's identity")
    if evaluator["inferred_claim_compatibility"]["measurement_value_in_identity"]:
        raise ValidationError("the measurement value is in the proposition's identity")
    if evaluator["inferred_claim_compatibility"]["threshold_registration"] != (
        "NOT_APPLICABLE for a categorical predicate"
    ):
        raise ValidationError(
            "a threshold registration is contemplated for a categorical predicate"
        )

    comparability = constructs["request_comparability"]
    fields = {f["field"]: f["classification"] for f in comparability["fields"]}
    # A different path or a different query is a different proposition, whatever else matches.
    for pinned in MUST_MATCH_FIELDS:
        if fields.get(pinned) != "MUST_MATCH":
            raise ValidationError(
                f"{pinned} is classified {fields.get(pinned)!r}; two apparatuses that differ "
                "on it are not asking the same question of the same thing"
            )
    for row in comparability["fields"]:
        if row["field"] == "METHOD" and row.get("value") != "HEAD":
            raise ValidationError("the method is not HEAD, which is what the permission covers")
        if row["field"] == "REDIRECT_FOLLOWING" and row.get("value") != "DISABLED":
            raise ValidationError("redirect following is not pinned DISABLED on both apparatuses")
    if fields.get("GEOGRAPHY_AND_ASN_VANTAGE") != "UNRESOLVED":
        raise ValidationError("the vantage field is not recorded as unresolved")


def _check_the_priority_delta_is_honest(decision: dict) -> None:
    delta = decision["priority_delta"]
    recorded = {row["criterion"] for row in delta["comparison"]}
    for criterion in DELTA_CRITERIA:
        if criterion not in recorded:
            raise ValidationError(f"the delta does not compare {criterion}")
    if delta["mission_1_76_priority_overturned"]:
        raise ValidationError(
            "the delta claims Mission 1.76's priority was overturned; the criterion that "
            "placed M1 in TIER 1 was executability, and that is untouched"
        )
    if delta["broad_portfolio_research_rerun"]:
        raise ValidationError("broad portfolio research was re-run and the brief forbids it")
    prior = _load(PRIORITY)
    if prior["selection"]["selected_candidate"] != delta["what_mission_1_76_recorded"]["selected"]:
        raise ValidationError("the delta misquotes what Mission 1.76 selected")
    if prior["globalping_dependency"]["selectable_now"] is not False:
        raise ValidationError("Mission 1.76's record was edited to say the route was selectable")


def _check_nothing_ran(decision: dict, selected: dict, constructs: dict) -> None:
    accounting = decision["mission_accounting"]
    for counter in HARD_ZERO:
        if counter not in accounting:
            raise ValidationError(f"the accounting does not report {counter}")
        if accounting[counter] != 0:
            raise ValidationError(f"{counter} is {accounting[counter]}, and it must be 0")

    independence = constructs["independence"]
    if independence["state"] != "INDEPENDENCE_ARCHITECTURALLY_CAPABLE":
        raise ValidationError(
            f"independence is recorded as {independence['state']!r}; a qualified pair is not a "
            "persisted independence judgement"
        )
    if independence["groups_created"] != 0:
        raise ValidationError("an independence group was created")

    relevance = constructs["product_relevance"]
    if "MODERATE" not in relevance["honest_bound"]:
        raise ValidationError("the product relevance is not bounded")
    if not str(relevance["promotion_refused"]).strip():
        raise ValidationError("the record does not name the promotion it refuses")

    action = decision["recommended_next_action"]
    if action["corpus_freeze_authorized"] or action["run_authorized"]:
        raise ValidationError("the next action authorises a corpus freeze or a run")
    if not action["mission_1_77_not_started"]:
        raise ValidationError("a later mission was started")
    if not selected["limitations_carried_from_the_provider_declaration"]:
        raise ValidationError("the selection drops the provider's stated limitations")


def validate() -> tuple[dict, dict, dict]:
    selected = _load(SELECTED)
    decision = _load(DECISION_V6)
    package = _load(PACKAGE_V2)
    constructs = _load(CONSTRUCTS)
    try:
        _check_three_states_stay_apart(selected, decision)
        _check_the_premise_still_holds(decision)
        _check_the_supersessions(decision, package)
        _check_no_construct_was_selected_and_vantage_is_open(constructs)
        _check_the_denominator_is_never_outcome_selected(constructs)
        _check_the_evaluator_gap_is_reported_not_routed_around(constructs)
        _check_the_priority_delta_is_honest(decision)
        _check_nothing_ran(decision, selected, constructs)
    except (KeyError, TypeError, IndexError, StopIteration) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return selected, decision, constructs


def render(selected: dict, decision: dict, constructs: dict) -> str:
    vantage = constructs["vantage"]
    lines = [
        "# Q1 selected, and no construct with it",
        "",
        f"Generated from `{SELECTED.name}`, `{DECISION_V6.name}` and `{CONSTRUCTS.name}`. "
        "Do not edit by hand.",
        "",
        f"**{decision['primary_outcome']}**",
        "",
        "| state | |",
        "|---|---|",
    ]
    for state, value in decision["three_states_kept_apart"].items():
        if state.startswith("$"):
            continue
        lines.append(f"| {state} | **{value}** |")
    lines += [
        "",
        decision["three_states_kept_apart"].get("$comment", ""),
        "",
        "## The class",
        "",
        f"`{selected['class_id']}` — {selected['class_name']}, on two routes:",
        "",
    ]
    lines += [f"- {name}" for name in selected["apparatuses"]]
    lines += [
        "",
        decision["why_a_class_may_be_selected_while_no_construct_is"],
        "",
        "## The three candidates",
        "",
        "| candidate | verdict |",
        "|---|---|",
    ]
    for candidate in constructs["candidates"]:
        lines.append(f"| {candidate['name']} | `{candidate['verdict']}` |")
    lines += [
        "",
        "## Vantage is what stops all three",
        "",
        f"**{vantage['the_finding']}**",
        "",
        vantage["why"],
        "",
        vantage["mission_1_58_test_applied"],
        "",
        "| resolution | cost |",
        "|---|---|",
    ]
    for resolution in vantage["three_coherent_resolutions"]:
        lines.append(f"| `{resolution['id']}` | {resolution['cost']} |")
    lines += [
        "",
        vantage["why_none_was_chosen_here"],
        "",
        "## What did not happen",
        "",
        "| | |",
        "|---|---|",
        f"| construct selected | {constructs['selected_construct']} |",
        f"| corpus frozen | {selected['corpus_frozen']} |",
        f"| measurements executed | {selected['measurements_executed']} |",
        f"| independence groups | {constructs['independence']['groups_created']} |",
        f"| independence state | `{constructs['independence']['state']}` |",
        "",
        f"**Next: {decision['recommended_next_action']['action']}.** "
        f"{decision['recommended_next_action']['the_decision']}",
        "",
    ]
    return "\n".join(line for line in lines if line is not None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        selected, decision, constructs = validate()
    except ValidationError as error:
        print(f"REFUSED  Q1 class selection: {error}")
        return 1

    text = render(selected, decision, constructs)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its records")
            return 1
        print("ok       the Q1 class selection matches its records")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"class    {selected['class_id']}")
    print(f"state    {selected['state']}")
    print(f"construct {constructs['selected_construct']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
