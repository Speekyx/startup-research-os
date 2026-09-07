"""Render and validate the V2 vantage-class decision.

The operator chose the semantic model. This asks whether it can be made truthful, and the
answer is half yes.

Four things this gate holds:

    THE CLASS IS DEFINED BEFORE THE RUN AND WITHOUT NAMING AN APPARATUS.
    A SINGLETON CLASS IS NOT A UNIVERSAL; IT IS THE MODEL THAT WAS REJECTED.
    ONE POSITIVE MEMBER DOES NOT SUPPORT A UNIVERSAL.
    MISSINGNESS IS NEVER REFUTATION.

The membership rules are scanned for the definitions section 4 forbids by name -- availability,
success, reachability, agreement, evaluability -- because a frame chosen from what answered is
the failure that closed the external pair in Mission 1.70, arriving one layer up.

`validate()` refuses: a class whose cardinality or membership is not decidable before the run;
a class defined by apparatus identity or availability; a singleton class, which collapses the
universal into the V1 the operator rejected; partial-positive support; a missingness state
admitted as refutation; a claimed support capability the apparatus reality does not carry; a
rewritten predecessor; and any measurement, target, corpus or canonical mutation.

    uv run python infrastructure/scripts/render_v2_vantage_class.py
    uv run python infrastructure/scripts/render_v2_vantage_class.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

DECISION = DATA / "v2-vantage-class-decision-v1.json"
CONSTRUCTS = DATA / "http-construct-candidate-evaluation-v1.json"
SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
SELECTED_CONSTRUCT = DATA / "selected-construct-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v4.json"
APPARATUS = DATA / "sros-bounded-http-apparatus-contract-v1.json"

RENDERED = DATA / "v2-vantage-class-decision-v1.md"

# Section 4, verbatim in spirit: a frame chosen from availability or from outcomes.
FORBIDDEN_MEMBERSHIP = (
    r"\bonline\b",
    r"\bavailable\b",
    r"success",
    r"\bresponded\b",
    r"\breachable\b",
    r"\bthat agree\b",
    r"\bevaluable\b",
    r"\bused by this run\b",
)

REQUIRED_CLASSES = (
    "VC_A_EXTERNAL_GEOGRAPHIC_TUPLE_SET",
    "VC_B_SINGLETON_OPERATOR_VANTAGE",
    "VC_C_EXTERNALLY_ENUMERATED_CONCRETE_VANTAGES",
)

SUPPORT_MODELS = (
    "U1_COMPLETE_CLASS_WITNESS",
    "U2_MEMBER_EVIDENCE_PLUS_DETERMINISTIC_DERIVATION",
    "U3_PARTIAL_POSITIVE_SUPPORT",
)

NOT_REFUTATION = (
    "NOT_OBSERVED",
    "APPARATUS_FAILURE",
    "VANTAGE_UNAVAILABLE",
    "REQUEST_FAILED_BEFORE_WORLD_STATE_OBSERVED",
    "PREDICATE_NOT_EVALUABLE",
)

HARD_ZERO = (
    "GLOBALPING_API_EXECUTIONS",
    "TARGET_HTTP_REQUESTS",
    "SROS_FETCHER_RUNS",
    "ROBOTS_REQUESTS",
    "DNS_PROBES",
    "MEASUREMENT_VALUES",
    "TARGETS_SELECTED",
    "CORPORA_FROZEN",
    "CONSTRUCTS_SELECTED",
    "VANTAGE_CLASSES_SELECTED",
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
    """The vantage-class decision says something this gate refuses."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _check_the_operator_decision_is_a_transition(decision: dict) -> None:
    operator = decision["operator_decision"]
    if operator["decision"] != "V2":
        raise ValidationError(f"the recorded decision is {operator['decision']!r}, not V2")
    if operator["what_the_decision_selects"] != "THE_SEMANTIC_MODEL_ONLY":
        raise ValidationError("the decision is recorded as selecting more than a semantic model")
    for refusal in ("v1_rejected_because", "v3_rejected_because"):
        if not str(operator[refusal]).strip():
            raise ValidationError(f"the record does not carry {refusal}")
    if operator["mission_1_76_6_rewritten"]:
        raise ValidationError("Mission 1.76.6 was rewritten as though it had chosen V2")

    # The predecessor still records that it chose nothing, which was true at its completion.
    constructs = _load(CONSTRUCTS)
    if constructs["vantage"]["which_was_chosen"] is not None:
        raise ValidationError(
            "Mission 1.76.6's record now names a chosen resolution; it chose none, and a later "
            "operator decision is a new fact rather than a correction"
        )
    if constructs["selected_construct"] is not None:
        raise ValidationError("a construct was selected in the predecessor record")


def _check_nothing_was_selected_or_run(decision: dict) -> None:
    if decision["exact_predicate_frozen"] or decision["corpus_frozen"]:
        raise ValidationError("a predicate or a corpus was frozen")
    if decision["measurements_executed"] != 0:
        raise ValidationError("a measurement was executed")
    if SELECTED_CONSTRUCT.exists():
        raise ValidationError("a construct artifact exists")

    selected = _load(SELECTED_CLASS)
    if selected["states_kept_apart"]["CONSTRUCT_SELECTED"]:
        raise ValidationError("the class selection now records a construct")
    if selected["states_kept_apart"]["RUN_AUTHORIZED"]:
        raise ValidationError("the class selection now authorises a run")

    example = decision["worked_semantic_test_case"]
    for flag in ("construct_selected", "target_named", "request_contract_frozen"):
        if example[flag]:
            raise ValidationError(f"the worked example {flag}, and it is a test case only")

    accounting = decision["mission_accounting"]
    for counter in HARD_ZERO:
        if counter not in accounting:
            raise ValidationError(f"the accounting does not report {counter}")
        if accounting[counter] != 0:
            raise ValidationError(f"{counter} is {accounting[counter]}, and it must be 0")

    if decision["target_level_preserved"]["reopened_corpus_aggregate"]:
        raise ValidationError("the corpus aggregate was reopened to make V2 easier")


def _check_the_classes_are_frame_independent(decision: dict) -> None:
    classes = {c["class_id"]: c for c in decision["candidate_classes"]}
    for required in REQUIRED_CLASSES:
        if required not in classes:
            raise ValidationError(f"the class {required} was not evaluated")
    if len(classes) < 3:
        raise ValidationError("fewer than three vantage-class shapes were evaluated")

    for class_id, candidate in classes.items():
        rule = str(candidate["membership_rule"])
        if not candidate["finite_before_run"]:
            raise ValidationError(f"{class_id} is not finite before the run")
        if not candidate["membership_decidable_before_run"]:
            raise ValidationError(f"{class_id}'s membership is not decidable before the run")

        # A frame chosen from availability or from outcomes is the failure this guards.
        for pattern in FORBIDDEN_MEMBERSHIP:
            if re.search(pattern, rule, re.IGNORECASE):
                raise ValidationError(
                    f"{class_id}'s membership rule is defined by {pattern!r}; that chooses the "
                    "frame from apparatus availability or from what was measured"
                )

        if not candidate["apparatus_independent_definition"]:
            if candidate["semantic_verdict"] not in ("REFUSED_TWICE_OVER", "REFUSED"):
                raise ValidationError(
                    f"{class_id} is defined by apparatus identity and is not refused"
                )
            if not candidate["frame_inside_definition"]:
                raise ValidationError(
                    f"{class_id} names an apparatus and does not record the frame problem"
                )

    singleton = classes["VC_B_SINGLETON_OPERATOR_VANTAGE"]
    if singleton["semantic_verdict"] != "REFUSED_TWICE_OVER":
        raise ValidationError(
            "the singleton class is not refused; a universal over one member is the "
            "proposition with a vantage qualifier, which is the V1 the operator rejected"
        )
    if "V1" not in singleton["why_refused"]:
        raise ValidationError("the singleton refusal does not record that it collapses into V1")


def _check_the_support_semantics_are_truthful(decision: dict) -> None:
    models = decision["support_models"]
    for required in SUPPORT_MODELS:
        if required not in models:
            raise ValidationError(f"the support model {required} was not evaluated")

    u3 = models["U3_PARTIAL_POSITIVE_SUPPORT"]
    if u3["selected"] or u3["logically_sound"]:
        raise ValidationError(
            "partial positive support was accepted; 'some evidence in favour of all' is not "
            "evidence for a universal"
        )
    u2 = models["U2_MEMBER_EVIDENCE_PLUS_DETERMINISTIC_DERIVATION"]
    if u2["solves_the_independence_goal"]:
        raise ValidationError(
            "pooling member observations across apparatuses is recorded as solving "
            "independence; one derivation over a pooled set is not two witnesses"
        )
    u1 = models["U1_COMPLETE_CLASS_WITNESS"]
    if not u1["selected"]:
        raise ValidationError("no support model was selected")
    if not u1["logically_sound"]:
        raise ValidationError("the selected support model is recorded as unsound")
    selected_count = sum(1 for m in models.values() if m["selected"])
    if selected_count != 1:
        raise ValidationError(f"{selected_count} support models are selected; exactly one may be")


def _check_missingness_is_never_refutation(decision: dict) -> None:
    refutation = decision["refutation_semantics"]
    if not refutation["sound"]:
        raise ValidationError("refutation is recorded as unsound and the outcome rests on it")
    for state in NOT_REFUTATION:
        if state not in refutation["states_that_are_not_refutation"]:
            raise ValidationError(
                f"{state} is not kept apart from refutation; turning missingness into a "
                "contradiction is the failure this arc has refused since Mission 1.71"
            )
    if not str(refutation["why_they_are_kept_apart"]).strip():
        raise ValidationError("the record does not say why missingness is not refutation")
    if not refutation["both_apparatuses_can_refute"]:
        raise ValidationError("the record denies a refutation capability its own analysis shows")
    if not str(refutation["but"]).strip():
        raise ValidationError(
            "the record does not say that two refutations agree and exercise no disagreement"
        )


def _check_the_apparatus_reality_was_read_not_assumed(decision: dict) -> None:
    reality = decision["apparatus_vantage_reality"]
    sros = reality["sros"]
    if sros["capability"] != "SINGLE_DEPLOYMENT_VANTAGE":
        raise ValidationError(
            "the fetcher is credited with more than one vantage; the apparatus contract records "
            "one machine, one network and one resolver"
        )
    if sros["multi_vantage_today"] or sros["redesigned_by_this_mission"]:
        raise ValidationError("the fetcher was redesigned into a probe network")
    if sros["cardinality_of_vantages_it_can_occupy_in_one_run"] != 1:
        raise ValidationError("the fetcher is credited with occupying more than one vantage")
    if not str(sros["basis"]).strip():
        raise ValidationError("the fetcher's vantage capability is asserted with no basis")

    globalping = reality["globalping"]
    if globalping["capability"] != "MULTIPLE_SELECTABLE_VANTAGES":
        raise ValidationError("the provider's established selection semantics were downgraded")
    if globalping["current_availability_checked"]:
        raise ValidationError(
            "current probe availability was checked; that is an external call and it would make "
            "the class depend on availability"
        )
    qualification = _load(QUALIFICATION)
    if qualification["verdict"] != "COUNTERPART_RESOLVED":
        raise ValidationError("the counterpart verdict moved and this analysis rests on it")


def _check_the_independence_finding_is_not_hidden(decision: dict) -> None:
    independence = decision["dual_apparatus_independence"]
    for flag in (
        "sros_can_independently_support_v2",
        "globalping_can_independently_support_v2",
        "dual_independent_support_reachable",
        "contradiction_reachable",
    ):
        if flag not in independence:
            raise ValidationError(f"the record does not report {flag}")
    if independence["dual_independent_support_reachable"] and not (
        independence["sros_can_independently_support_v2"]
        and independence["globalping_can_independently_support_v2"]
    ):
        raise ValidationError(
            "dual independent support is claimed while an apparatus cannot produce it"
        )
    if (
        independence["contradiction_reachable"]
        and not independence["dual_independent_support_reachable"]
    ):
        raise ValidationError(
            "the contradiction case is claimed with no admissible SUPPORTS item; it needs one "
            "apparatus to legitimately support while the other contradicts"
        )
    if not str(independence["what_it_does_not_deliver"]).strip():
        raise ValidationError(
            "the record does not state plainly what V2 fails to deliver, and section 11 forbids "
            "hiding that distinction"
        )

    contract = decision["evidence_direction_contract"]
    if contract["new_evidence_direction_member_required"]:
        raise ValidationError(
            "a new EvidenceDirection member is proposed; the incomplete state belongs in the "
            "existing refusal store"
        )
    if not str(contract["smallest_required_extension"]).strip():
        raise ValidationError("the record does not name the smallest required extension")

    dilemma = decision["the_dilemma"]
    if dilemma["is_this_a_topology_problem"]:
        raise ValidationError(
            "the limit is recorded as a topology problem; it survives any fleet size, and "
            "recording it otherwise sends the next mission to build the wrong thing"
        )


def _check_the_outcome(decision: dict) -> None:
    outcome = decision["primary_outcome"]
    independence = decision["dual_apparatus_independence"]
    if (
        outcome == "V2_VANTAGE_CLASS_CONTRACT_READY_FOR_CONSTRUCT_SELECTION"
        and not independence["dual_independent_support_reachable"]
    ):
        raise ValidationError(
            "the ready outcome is claimed while dual independent support is unreachable"
        )
    if outcome == "V2_VALID_FOR_REFUTATION_BUT_NOT_INDEPENDENT_SUPPORT":
        if not decision["refutation_semantics"]["sound"]:
            raise ValidationError("the outcome claims refutation validity and records it unsound")
        if independence["dual_independent_support_reachable"]:
            raise ValidationError("the outcome denies a support capability its own fields grant")

    refused = {entry["outcome"] for entry in decision["outcomes_considered_and_refused"]}
    for required in (
        "V2_VANTAGE_CLASS_CONTRACT_READY_FOR_CONSTRUCT_SELECTION",
        "V2_FRAME_CANNOT_BE_DEFINED_WITHOUT_APPARATUS_DEPENDENCE",
        "V2_REQUIRES_MULTI_VANTAGE_OPERATOR_APPARATUS",
    ):
        if required not in refused:
            raise ValidationError(f"the outcome {required} was not considered and refused")
    for entry in decision["outcomes_considered_and_refused"]:
        if not str(entry["refused_because"]).strip():
            raise ValidationError(f"{entry['outcome']} is refused with no reason")

    action = decision["recommended_next_action"]
    if action["corpus_freeze_authorized"] or action["run_authorized"]:
        raise ValidationError("the next action authorises a corpus freeze or a run")
    if not action["mission_1_77_not_started"]:
        raise ValidationError("a later mission was started")
    if not str(action["state_plainly"]).strip():
        raise ValidationError("the record does not state the finding plainly")


def validate() -> dict:
    decision = _load(DECISION)
    try:
        _check_the_operator_decision_is_a_transition(decision)
        _check_nothing_was_selected_or_run(decision)
        _check_the_classes_are_frame_independent(decision)
        _check_the_support_semantics_are_truthful(decision)
        _check_missingness_is_never_refutation(decision)
        _check_the_apparatus_reality_was_read_not_assumed(decision)
        _check_the_independence_finding_is_not_hidden(decision)
        _check_the_outcome(decision)
    except (KeyError, TypeError, IndexError, StopIteration) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return decision


def render(decision: dict) -> str:
    independence = decision["dual_apparatus_independence"]
    reality = decision["apparatus_vantage_reality"]
    lines = [
        "# V2 — sound for refutation, out of reach for support",
        "",
        f"Generated from `{DECISION.name}`. Do not edit by hand.",
        "",
        f"**{decision['primary_outcome']}**",
        "",
        "The operator selected V2 after Mission 1.76.6 chose nothing. That record still reads "
        "`which_was_chosen: null`, which was true at its completion.",
        "",
        "## FOR ALL v IN V",
        "",
        f"`{decision['semantic_form']['shape']}`, where V must be "
        f"{decision['semantic_form']['V_must_be']}.",
        "",
        "## The dilemma",
        "",
        decision["the_dilemma"]["statement"],
        "",
        f"**Is this a topology problem? {decision['the_dilemma']['is_this_a_topology_problem']}.** "
        + decision["the_dilemma"]["why_not"],
        "",
        "## Three classes, and the hole between them",
        "",
        "| class | apparatus-independent | support | verdict |",
        "|---|---|---|---|",
    ]
    for candidate in decision["candidate_classes"]:
        lines.append(
            f"| `{candidate['class_id']}` | {candidate['apparatus_independent_definition']} "
            f"| `{candidate['support_semantics']}` | `{candidate['semantic_verdict']}` |"
        )
    lines += [
        "",
        "## What each apparatus actually is",
        "",
        "| | capability | full class coverage |",
        "|---|---|---|",
        f"| SROS fetcher | `{reality['sros']['capability']}` | no |",
        f"| Globalping | `{reality['globalping']['capability']}` | attemptable, not guaranteed |",
        "",
        reality["the_asymmetry"],
        "",
        "## Support and refutation",
        "",
        "| | |",
        "|---|---|",
        f"| SROS can independently support | {independence['sros_can_independently_support_v2']} |",
        f"| Globalping can independently support | "
        f"{independence['globalping_can_independently_support_v2']} |",
        f"| dual independent support reachable | "
        f"{independence['dual_independent_support_reachable']} |",
        f"| contradiction reachable | {independence['contradiction_reachable']} |",
        "",
        independence["why_contradiction_is_not_reachable"],
        "",
        "**What V2 does deliver:**",
        "",
    ]
    lines += [f"- {item}" for item in independence["what_v2_does_deliver"]]
    lines += [
        "",
        f"**What it does not: {independence['what_it_does_not_deliver']}**",
        "",
        f"**Next: {decision['recommended_next_action']['action']}.** "
        f"{decision['recommended_next_action']['state_plainly']}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        decision = validate()
    except ValidationError as error:
        print(f"REFUSED  V2 vantage class: {error}")
        return 1

    text = render(decision)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its record")
            return 1
        print("ok       the V2 vantage-class decision matches its record")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {decision['primary_outcome']}")
    print(
        f"support  {decision['dual_apparatus_independence']['dual_independent_support_reachable']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
