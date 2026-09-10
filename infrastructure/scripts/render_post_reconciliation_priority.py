"""Render and validate the post-reconciliation evidence priority (Mission 1.79).

A prioritization is a decision record over held data, and the gate holds it to the records
it claims to have read: the reconciliation record (revision 2 and its links), the current
preparation record (packets, eligibility, resolver outcomes), and the parked apparatus arc.
It refuses:

    SIX SCORABLE ROWS READ AS SIX OBSERVATIONS. The scorable shape is recomputed from the
    linked rows: sources, families, counting dimensions, and one provenance group while every
    linked row is UNKNOWN and the deployment holds zero independence groups.

    SCORING-READY READ AS CALIBRATED, AUTHORISED, INDEPENDENT OR VALIDATED. Packet readiness
    is recomputed from the preparation and the other four flags must be false while the
    profile is UNCALIBRATED and no scores table exists.

    A DIMENSION SUPPORTED BY NO ROW. SUPPORTED_* needs a linked row mapped to it, and
    SUPPORTED_SCORABLE needs that row to resolve; a question count cannot support recurrence.

    A CANDIDATE THAT WINS BY BEING EASY, OR BY BEING LEFT OVER. The winner is on the
    recomputed Pareto frontier and carries no veto; a candidate adding rows without a new
    dimension or a new source is vetoed; the Stack Exchange candidate cannot win while its
    bottleneck includes the proposition's weakness; TED is never attached to docker.

    A PARKED ARC MOVED. Globalping qualification is not independence; Q1 stays selected
    without a construct; nothing canonical moved.

    uv run python infrastructure/scripts/render_post_reconciliation_priority.py
    uv run python infrastructure/scripts/render_post_reconciliation_priority.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

PRIORITY = DATA / "post-reconciliation-evidence-priority-v1.json"
RECONCILIATION = DATA / "opportunity-reliability-reconciliation-v1.json"
PREPARATION = DATA / "opportunity-preparation-v2.json"
RENDERED = DATA / "post-reconciliation-evidence-priority-v1.md"

SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v4.json"
V2_DECISION = DATA / "v2-vantage-class-decision-v1.json"

REQUIRED_CANDIDATES = (
    "M1_STACK_EXCHANGE_RELIABILITY",
    "M2_PROBLEM_STRENGTH",
    "M3_COMMERCIAL_BUYER_WTP",
    "M4_HELD_UNUSED_EVIDENCE",
    "M5_Q1_INDEPENDENCE",
    "M6_SECOND_OPPORTUNITY",
)
OUTCOMES = (
    "STACK_EXCHANGE_SCORABILITY_IS_NEXT_BOUNDED_MOVE",
    "PROBLEM_STRENGTH_EVIDENCE_IS_NEXT_BOUNDED_MOVE",
    "COMMERCIAL_DIMENSION_IS_NEXT_BOUNDED_MOVE",
    "HELD_UNUSED_EVIDENCE_REVIEW_IS_NEXT_BOUNDED_MOVE",
    "SECOND_OPPORTUNITY_EXPLORATION_IS_NEXT_BOUNDED_MOVE",
    "Q1_REOPENED_BY_NEW_DETERMINISTIC_CONSTRUCT",
    "NO_HIGH_INFORMATION_BOUNDED_MOVE_AVAILABLE",
)
OUTCOME_OF_CANDIDATE = {
    "M1_STACK_EXCHANGE_RELIABILITY": "STACK_EXCHANGE_SCORABILITY_IS_NEXT_BOUNDED_MOVE",
    "M2_PROBLEM_STRENGTH": "PROBLEM_STRENGTH_EVIDENCE_IS_NEXT_BOUNDED_MOVE",
    "M3_COMMERCIAL_BUYER_WTP": "COMMERCIAL_DIMENSION_IS_NEXT_BOUNDED_MOVE",
    "M4_HELD_UNUSED_EVIDENCE": "HELD_UNUSED_EVIDENCE_REVIEW_IS_NEXT_BOUNDED_MOVE",
    "M5_Q1_INDEPENDENCE": "Q1_REOPENED_BY_NEW_DETERMINISTIC_CONSTRUCT",
    "M6_SECOND_OPPORTUNITY": "SECOND_OPPORTUNITY_EXPLORATION_IS_NEXT_BOUNDED_MOVE",
}
STATUSES = (
    "EXECUTABLE_NOW_HELD_DATA_ONLY",
    "EXECUTABLE_AFTER_OPERATOR_JUDGMENT",
    "EXECUTABLE_AFTER_GOVERNANCE_WORK",
    "EXECUTABLE_AFTER_NEW_ACQUISITION",
    "RESEARCH_REQUIRED_BEFORE_EXECUTION",
    "PARKED",
    "NOT_USEFUL",
)
GAIN_FIELDS = (
    "dimension_gain",
    "scorability_gain",
    "source_diversity_gain",
    "commercial_gain",
    "semantic_gain",
)
NON_COUNTING = {"TREND_OR_CHANGE"}
COMMERCIAL_DIMENSIONS = {
    "MARKET_ACTIVITY",
    "BUYER_OR_BUDGET_EXISTENCE",
    "ECONOMIC_VALUE",
    "WILLINGNESS_TO_PAY",
}
FORBIDDEN_NUMERIC_KEYS = ("score", "priority_score", "weighted", "points")


class ValidationError(Exception):
    pass


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rank(scale: list[str], value: str, label: str) -> int:
    if value not in scale:
        raise ValidationError(f"{label} carries {value!r}, not one of {scale}")
    return scale.index(value)


# ------------------------------------------------------------------------- checks


def _linked_rows(record: dict, reconciliation: dict, preparation: dict) -> list[dict]:
    """Revision 2's links, joined to the preparation rows; the record must describe exactly these."""
    written = {
        link["evidence_id"] for link in reconciliation["revision_2_applied"]["links_written"]
    }
    described = {row["evidence_id"] for row in record["current_linked_evidence"]}
    if described != written:
        raise ValidationError(
            f"the record describes {sorted(described - written)} beyond and "
            f"{sorted(written - described)} short of revision 2's links"
        )
    rows = {r["evidence_id"]: r for r in preparation["rows"]}
    out = []
    for entry in record["current_linked_evidence"]:
        row = rows[entry["evidence_id"]]
        resolved = row["reliability_resolution"]["outcome"] == "RESOLVED"
        if entry["scorable"] != resolved or entry["scorable"] != row["scorable"]:
            raise ValidationError(
                f"{entry['evidence_id'][:8]}: scorable disagrees with the resolver"
            )
        if (entry["resolved_reliability"] is not None) != resolved:
            raise ValidationError(
                f"{entry['evidence_id'][:8]}: a value without a resolution, or the reverse"
            )
        if entry["reliability_applicability"] != row["reliability_resolution"]["outcome"]:
            raise ValidationError(
                f"{entry['evidence_id'][:8]}: applicability disagrees with the resolver"
            )
        if entry["source_id"] != row["source_id"]:
            raise ValidationError(
                f"{entry['evidence_id'][:8]}: source disagrees with the preparation"
            )
        if sorted(entry["dimensions"]) != sorted(row["dimensions"]):
            raise ValidationError(
                f"{entry['evidence_id'][:8]}: dimensions disagree with the dimension map"
            )
        if sorted(entry["counting_dimensions"]) != sorted(
            d for d in row["dimensions"] if d not in NON_COUNTING
        ):
            raise ValidationError(
                f"{entry['evidence_id'][:8]}: counting dimensions include a non-counting one"
            )
        if entry["independence_state"] != row["independence_state"]:
            raise ValidationError(f"{entry['evidence_id'][:8]}: independence state disagrees")
        if resolved and entry["source_id"] != next(
            a["source_id"]
            for a in reconciliation["revision_1_audit"]["why_stale"]
            if a["assessment_id"] == row["reliability_resolution"]["assessment_id"]
        ):
            raise ValidationError(
                f"{entry['evidence_id'][:8]}: bound to another source's assessment"
            )
        if not str(entry["does_not_establish"]).strip():
            raise ValidationError(
                f"{entry['evidence_id'][:8]}: no statement of what it does not establish"
            )
        out.append({**entry, "_family": row["source_family"]})
    return out


def _check_the_scorable_shape(record: dict, rows: list[dict], reconciliation: dict) -> None:
    shape = record["scorable_shape"]
    scorable = [r for r in rows if r["scorable"]]
    expected = {
        "SCORABLE_ROWS": len(scorable),
        "SCORABLE_SOURCES": len({r["source_id"] for r in scorable}),
        "SCORABLE_SOURCE_FAMILIES": len({r["_family"] for r in scorable}),
        "SCORABLE_COUNTING_DIMENSIONS": len(
            {d for r in scorable for d in r["counting_dimensions"]}
        ),
    }
    for key, value in expected.items():
        if shape[key] != value:
            raise ValidationError(f"scorable_shape.{key} is {shape[key]}, measured {value}")
    groups = reconciliation["counters"]["after"]["independence_groups"]
    if (
        groups == 0
        and all(r["independence_state"] == "UNKNOWN" for r in rows)
        and shape["SCORABLE_PROVENANCE_GROUPS"] != 1
    ):
        raise ValidationError(
            "six UNKNOWN rows with zero independence groups are one provenance shape, not "
            f"{shape['SCORABLE_PROVENANCE_GROUPS']}"
        )
    if shape["SCORABLE_DIMENSION_DIVERSITY"] != (expected["SCORABLE_COUNTING_DIMENSIONS"] >= 2):
        raise ValidationError("SCORABLE_DIMENSION_DIVERSITY disagrees with the counting dimensions")
    flags = record["scoring_ready_is_not_production_scoring"]
    if flags["INDEPENDENCE_ESTABLISHED"] and groups == 0:
        raise ValidationError("independence recorded as established with zero independence groups")


def _check_scoring_ready_is_not_scoring(
    record: dict, reconciliation: dict, preparation: dict
) -> None:
    flags = record["scoring_ready_is_not_production_scoring"]
    packet = next(
        p
        for p in preparation["packets"]
        if p["packet_id"] == reconciliation["current_evidence"]["packet_id_now"]
    )
    if flags["PACKET_SCORING_READY"] != packet["sufficiency"]["scoring_ready"]:
        raise ValidationError("PACKET_SCORING_READY disagrees with the preparation")
    after = reconciliation["counters"]["after"]
    if after["scores_table"] != "ABSENT":
        raise ValidationError("a scores table exists")
    if "UNCALIBRATED" not in flags["aggregation_profile"]:
        raise ValidationError("the aggregation profile is not recorded UNCALIBRATED")
    for key in (
        "AGGREGATION_PROFILE_CALIBRATED",
        "PERSISTED_SCORING_AUTHORIZED",
        "COMMERCIAL_VALIDATION_ESTABLISHED",
    ):
        if flags[key]:
            raise ValidationError(f"{key} is true; packet readiness is none of these")


def _check_the_dimension_matrix(record: dict, rows: list[dict]) -> None:
    matrix = record["dimension_matrix"]
    supported = {}
    for row in rows:
        for dimension in row["dimensions"]:
            supported.setdefault(dimension, set()).add(row["scorable"])
    for entry in matrix["rows"]:
        name = entry["dimension"].split("->")[-1].strip().split(" ")[0]
        cls = entry["classification"]
        if cls.startswith("SUPPORTED") and name not in supported:
            raise ValidationError(f"{entry['dimension']} is {cls} and no linked row maps to it")
        if cls == "SUPPORTED_SCORABLE" and True not in supported.get(name, set()):
            raise ValidationError(
                f"{entry['dimension']} is SUPPORTED_SCORABLE and no scorable linked row maps to it"
            )
        if cls == "SUPPORTED_CONTEXT_ONLY" and True in supported.get(name, set()):
            raise ValidationError(
                f"{entry['dimension']} is SUPPORTED_CONTEXT_ONLY and a scorable linked row maps to it"
            )
    listed_scorable = set(matrix["supported_scorable"])
    if listed_scorable != {d for d, s in supported.items() if True in s}:
        raise ValidationError("supported_scorable disagrees with the linked rows")
    listed_context = set(matrix["supported_context_only"])
    if listed_context != {d for d, s in supported.items() if True not in s}:
        raise ValidationError("supported_context_only disagrees with the linked rows")
    if "RECURRENCE_OR_FREQUENCY" in listed_scorable | listed_context:
        raise ValidationError("a question count was read as recurrence")


def _dominates(x: dict, y: dict, scales: dict) -> bool:
    better = False
    for field in GAIN_FIELDS:
        rx, ry = _rank(scales["gain"], x[field], field), _rank(scales["gain"], y[field], field)
        if rx < ry:
            return False
        better |= rx > ry
    rx, ry = (
        _rank(scales["independence"], x["independence_gain"], "independence_gain"),
        _rank(scales["independence"], y["independence_gain"], "independence_gain"),
    )
    if rx < ry:
        return False
    better |= rx > ry
    rx, ry = (
        _rank(scales["impact"], x["decision_impact"], "decision_impact"),
        _rank(scales["impact"], y["decision_impact"], "decision_impact"),
    )
    if rx < ry:
        return False
    better |= rx > ry
    for field, scale in (
        ("execution_cost", "cost"),
        ("overinterpretation_risk", "risk"),
        ("external_dependency", "dependency_rank"),
    ):
        rx, ry = _rank(scales[scale], x[field], field), _rank(scales[scale], y[field], field)
        if rx > ry:
            return False
        better |= rx < ry
    return better


def _check_the_candidates(record: dict, rows: list[dict], preparation: dict) -> None:
    candidates = {c["candidate_id"]: c for c in record["candidates"]}
    missing = [c for c in REQUIRED_CANDIDATES if c not in candidates]
    if missing:
        raise ValidationError(f"candidates not evaluated: {missing}")
    for cid, c in candidates.items():
        if c["status"] not in STATUSES:
            raise ValidationError(f"{cid}: status {c['status']!r}")
        for key in c:
            if any(k in key.lower() for k in FORBIDDEN_NUMERIC_KEYS) and isinstance(
                c[key], int | float
            ):
                raise ValidationError(
                    f"{cid}: a numeric {key}; a priority is a tier, never a number"
                )
        # Section 10: a move that adds rows and nothing else -- no dimension, no source, no
        # scorability -- cannot stand. A scorability move on a supported dimension is judged
        # on its bottleneck below, not here.
        if (
            c["dimension_gain"] == "NONE"
            and c["source_diversity_gain"] == "NONE"
            and c["scorability_gain"] == "NONE"
            and c["dominance_result"] not in ("VETOED", "DOMINATED")
        ):
            raise ValidationError(f"{cid}: adds neither a dimension nor a source and is not vetoed")
        if c["dominance_result"] == "VETOED" and not str(c["veto_reason"]).strip():
            raise ValidationError(f"{cid}: vetoed with no reason")
        if c["dominance_result"] in ("FRONTIER", "SELECTED") and str(c["veto_reason"]).strip():
            raise ValidationError(f"{cid}: on the frontier with a veto reason")
        if c["status"] == "EXECUTABLE_NOW_HELD_DATA_ONLY" and c["external_dependency"] != "NONE":
            raise ValidationError(f"{cid}: executable now with an external dependency")
        if (
            c["status"] in ("EXECUTABLE_AFTER_OPERATOR_JUDGMENT",)
            and c["external_dependency"] == "NONE"
        ):
            raise ValidationError(f"{cid}: needs a judgement and records no dependency")

    # Stack Exchange: a weak proposition made scorable does not win, and the leftover row is not next.
    m1 = candidates["M1_STACK_EXCHANGE_RELIABILITY"]
    test = record["special_tests"]["stack_exchange"]
    if test["D_bottleneck"] not in ("MISSING_RELIABILITY", "WEAK_PROPOSITION_INFORMATION", "BOTH"):
        raise ValidationError("the Stack Exchange bottleneck is not one of the three")
    if test["remaining_non_scorable_row_implies_next_fix"]:
        raise ValidationError("the leftover non-scorable row was read as the next fix")
    if m1["bottleneck"] != test["D_bottleneck"]:
        raise ValidationError("M1's bottleneck disagrees with the special test")
    if m1["dimension_gain"] != "NONE":
        raise ValidationError(
            "M1 records a new dimension; scorability of an existing one adds none"
        )
    if test["D_bottleneck"] != "MISSING_RELIABILITY" and m1["dominance_result"] in (
        "SELECTED",
        "FRONTIER",
    ):
        raise ValidationError("M1 wins while its proposition's weakness is part of the bottleneck")
    if (
        m1["new_human_review_required"] is not True
        or m1["status"] == "EXECUTABLE_NOW_HELD_DATA_ONLY"
    ):
        raise ValidationError("a reliability review is recorded as executable by code alone")
    if any(
        k in json.dumps(m1).lower()
        for k in ("recommended reliability", "reliability = 0.", "reliability of 0.")
    ):
        raise ValidationError("M1 recommends a reliability value")

    # Commercial: TED is never attached to docker, and held subject-matched evidence is measured.
    m3 = candidates["M3_COMMERCIAL_BUYER_WTP"]
    held = any(set(r["dimensions"]) & COMMERCIAL_DIMENSIONS for r in rows)
    if m3["held_subject_matched_commercial_evidence"] != held:
        raise ValidationError("M3's held-evidence claim disagrees with the linked rows")
    if m3["cross_subject_transfer_used"] or m3["ted_attached_to_docker"]:
        raise ValidationError("commercial evidence was transferred across subjects")

    # Held-unused: rows without a new dimension or provenance are dominated, not admitted.
    m4 = candidates["M4_HELD_UNUSED_EVIDENCE"]
    if any(r["new_dimension"] or r["new_provenance"] for r in m4["rows"]):
        raise ValidationError(
            "an uncited row is recorded as adding a dimension or provenance it does not"
        )
    if not record["special_tests"]["wikimedia_saturation"]["more_wikimedia_dominated"]:
        raise ValidationError("more Wikimedia is recorded as improving the decision")

    # Q1: qualification is not independence, and the arc stays parked without a deciding construct.
    m5 = candidates["M5_Q1_INDEPENDENCE"]
    if m5["globalping_qualification_solves_independence"]:
        raise ValidationError("Globalping qualification was read as solving independence")
    if m5["independence_gain"] == "ESTABLISHED_IF_EXECUTED":
        raise ValidationError("Q1 promises established independence with no deciding construct")
    if not m5["deciding_predicate_emerged"] and m5["status"] != "PARKED":
        raise ValidationError("Q1 is not parked although no deciding predicate emerged")
    if m5["preserved"]["CONSTRUCT_SELECTED"] or m5["preserved"]["RUN_AUTHORIZED"]:
        raise ValidationError("Q1 records a construct or a run")

    # Second opportunity: evaluated, from held packets, and not by row count.
    m6 = candidates["M6_SECOND_OPPORTUNITY"]
    if not m6["not_selected_for_row_count"]:
        raise ValidationError("M6 selected a subject for its row count")
    packets = {p["subject"]: p for p in preparation["packets"]}
    for held_candidate in m6["held_candidates"]:
        subject = held_candidate["subject"]
        if subject in packets:
            packet = packets[subject]
            if held_candidate["rows"] != packet["size"]:
                raise ValidationError(f"{subject}: rows disagree with the preparation")
            if sorted(held_candidate["counting_dimensions"]) != sorted(
                packet["counting_dimensions"]
            ):
                raise ValidationError(
                    f"{subject}: counting dimensions disagree with the preparation"
                )
            if held_candidate.get("scorable") is not None and held_candidate["scorable"] != packet[
                "eligibility_counts"
            ].get("ELIGIBLE_SCORING", 0):
                raise ValidationError(f"{subject}: scorable count disagrees with the preparation")
    leading = [c for c in m6["held_candidates"] if c["verdict"] == "LEADING"]
    if len(leading) != 1:
        raise ValidationError("M6 names other than one leading held candidate")
    lead_packet = packets[leading[0]["subject"]]
    docker_dims = {d for r in rows for d in r["counting_dimensions"]}
    if not (set(lead_packet["counting_dimensions"]) - docker_dims):
        raise ValidationError(
            "the leading second candidate adds no dimension the first Opportunity lacks"
        )

    # Dominance, recomputed.
    scales = record["ordinal_scales"]
    dominance = record["dominance"]
    computed_dominated = {}
    for cid, c in candidates.items():
        for oid, o in candidates.items():
            if oid != cid and _dominates(o, c, scales):
                computed_dominated.setdefault(cid, oid)
    frontier = [cid for cid in candidates if cid not in computed_dominated]
    if sorted(dominance["PARETO_FRONTIER"]) != sorted(frontier):
        raise ValidationError(
            f"the recorded frontier {dominance['PARETO_FRONTIER']} is not the computed {frontier}"
        )
    if sorted(dominance["DOMINATED_CANDIDATES"]) != sorted(computed_dominated):
        raise ValidationError(
            f"the recorded dominated set is not the computed {sorted(computed_dominated)}"
        )
    for cid, by in dominance["dominated_by"].items():
        if not _dominates(candidates[by], candidates[cid], scales):
            raise ValidationError(
                f"{cid} is recorded as dominated by {by}, which does not dominate it"
            )
    vetoed = sorted(cid for cid, c in candidates.items() if c["dominance_result"] == "VETOED")
    if sorted(dominance["VETOED_CANDIDATES"]) != vetoed:
        raise ValidationError("the vetoed list disagrees with the candidates")

    # Selection.
    selected = record["selected_next_move"]
    if selected is not None:
        if selected not in candidates:
            raise ValidationError("the selected move is not a candidate")
        winner = candidates[selected]
        if winner["dominance_result"] != "SELECTED":
            raise ValidationError("the selected candidate is not marked SELECTED")
        if selected in computed_dominated or selected in vetoed:
            raise ValidationError("the selected candidate is dominated or vetoed")
        if winner["status"] in ("PARKED", "NOT_USEFUL", "RESEARCH_REQUIRED_BEFORE_EXECUTION"):
            raise ValidationError("the selected candidate is not executable")
        if record["primary_outcome"] != OUTCOME_OF_CANDIDATE[selected]:
            raise ValidationError("the primary outcome does not name the selected candidate")
        if sum(1 for c in candidates.values() if c["dominance_result"] == "SELECTED") != 1:
            raise ValidationError("more than one candidate is marked SELECTED")
    else:
        if record["primary_outcome"] != "NO_HIGH_INFORMATION_BOUNDED_MOVE_AVAILABLE":
            raise ValidationError("no move selected and the outcome says one was")
        if any(c["dominance_result"] == "SELECTED" for c in candidates.values()):
            raise ValidationError("a candidate is marked SELECTED while no move was selected")
    if record["primary_outcome"] not in OUTCOMES:
        raise ValidationError(
            f"primary outcome {record['primary_outcome']!r} is not one of the seven"
        )
    second = record["special_tests"]["second_opportunity"]
    if second["sunk_effort_counted_as_value"]:
        raise ValidationError("sunk effort was counted as future information value")
    if (
        selected == "M6_SECOND_OPPORTUNITY"
        and second["CURRENT_OPPORTUNITY_MARGINAL_INFORMATION_VALUE"] == "HIGH"
    ):
        raise ValidationError(
            "a second Opportunity selected while the first still has HIGH marginal value"
        )


def _check_nothing_moved(record: dict, reconciliation: dict) -> None:
    after = reconciliation["counters"]["after"]
    state = record["current_state"]
    for key in (
        "reliability_assessments",
        "independence_groups",
        "opportunities",
        "opportunity_revisions",
        "opportunity_evidence_links",
        "embeddings",
        "scores_table",
    ):
        if state[key] != after[key]:
            raise ValidationError(
                f"current_state.{key} is {state[key]}, the reconciled deployment says {after[key]}"
            )
    if state["total_evidence"] != after["evidence"]:
        raise ValidationError("the Evidence count moved")
    hot = sorted(k for k, v in record["mission_accounting"].items() if v != 0)
    if hot:
        raise ValidationError(f"mission accounting is not zero on {hot}")
    if (
        record["current_revision_number"]
        if "current_revision_number" in record
        else state["current_revision_number"] != 2
    ):
        raise ValidationError("the current revision is not revision 2")


def _check_the_parked_arc(record: dict) -> None:
    parked = record["parked_states_preserved"]
    if parked["changed_by_this_mission"]:
        raise ValidationError("the parked arc was changed")
    states = _load(SELECTED_CLASS)["states_kept_apart"]
    for key in ("CLASS_SELECTED", "CONSTRUCT_SELECTED", "RUN_AUTHORIZED"):
        if states[key] != parked["q1"][key]:
            raise ValidationError(
                f"Q1 {key} reads {states[key]} and the record says {parked['q1'][key]}"
            )
    if not states["CLASS_SELECTED"] or states["CONSTRUCT_SELECTED"] or states["RUN_AUTHORIZED"]:
        raise ValidationError("Q1 is no longer selected-without-construct-or-run")
    qualification = _load(QUALIFICATION)
    if {k: qualification["tally"][k] for k in ("PASS", "PARTIAL", "FAIL")} != {
        k: parked["globalping"][k] for k in ("PASS", "PARTIAL", "FAIL")
    }:
        raise ValidationError("the Globalping tally moved")
    v2 = _load(V2_DECISION)
    if (
        v2["primary_outcome"] != parked["v2"]["primary_outcome"]
        or v2["corpus_frozen"]
        or v2["measurements_executed"]
    ):
        raise ValidationError("the V2 decision moved, or a corpus or measurement exists")
    if (DATA / "selected-construct-v1.json").exists():
        raise ValidationError("a construct artifact exists")


def validate() -> tuple[dict, dict, dict]:
    record = _load(PRIORITY)
    reconciliation = _load(RECONCILIATION)
    preparation = _load(PREPARATION)
    try:
        rows = _linked_rows(record, reconciliation, preparation)
        _check_the_scorable_shape(record, rows, reconciliation)
        _check_scoring_ready_is_not_scoring(record, reconciliation, preparation)
        _check_the_dimension_matrix(record, rows)
        _check_the_candidates(record, rows, preparation)
        _check_nothing_moved(record, reconciliation)
        _check_the_parked_arc(record)
    except (KeyError, TypeError, IndexError, StopIteration) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return record, reconciliation, preparation


# ------------------------------------------------------------------------- render


def render(record: dict) -> str:
    shape = record["scorable_shape"]
    flags = record["scoring_ready_is_not_production_scoring"]
    lines = [
        "# After the reconciliation, what is the next bounded move?",
        "",
        f"Generated from `{PRIORITY.name}`. Do not edit by hand.",
        "",
        f"**{record['primary_outcome']}** — selected `{record['selected_next_move']}`, next "
        f"{record['recommended_next_mission']['id']} {record['recommended_next_mission']['title']}.",
        "",
        "## Scoring-ready is not scoring",
        "",
        "| | |",
        "|---|---|",
    ]
    for key in (
        "PACKET_SCORING_READY",
        "AGGREGATION_PROFILE_CALIBRATED",
        "PERSISTED_SCORING_AUTHORIZED",
        "INDEPENDENCE_ESTABLISHED",
        "COMMERCIAL_VALIDATION_ESTABLISHED",
    ):
        lines.append(f"| {key} | {flags[key]} |")
    lines += [
        "",
        "## The scorable shape",
        "",
        f"{shape['SCORABLE_ROWS']} scorable rows, {shape['SCORABLE_SOURCES']} source, "
        f"{shape['SCORABLE_SOURCE_FAMILIES']} family, {shape['SCORABLE_COUNTING_DIMENSIONS']} counting "
        f"dimension, {shape['SCORABLE_PROVENANCE_GROUPS']} provenance shape. Scorable dimension diversity: "
        f"**{shape['SCORABLE_DIMENSION_DIVERSITY']}**. {shape['why']}",
        "",
        "## Dimension matrix",
        "",
        "| dimension | classification |",
        "|---|---|",
    ]
    for entry in record["dimension_matrix"]["rows"]:
        lines.append(f"| {entry['dimension']} | `{entry['classification']}` |")
    lines += [
        "",
        "## Candidates",
        "",
        "| candidate | status | dimension | scorability | sources | independence | commercial | impact | cost | dependency | result |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in record["candidates"]:
        lines.append(
            f"| `{c['candidate_id']}` | `{c['status']}` | {c['dimension_gain']} | {c['scorability_gain']} "
            f"| {c['source_diversity_gain']} | {c['independence_gain']} | {c['commercial_gain']} "
            f"| {c['decision_impact']} | {c['execution_cost']} | {c['external_dependency']} | **{c['dominance_result']}** |"
        )
    dominance = record["dominance"]
    lines += [
        "",
        f"Frontier {dominance['PARETO_FRONTIER']}; dominated {dominance['DOMINATED_CANDIDATES']}; vetoed "
        f"{dominance['VETOED_CANDIDATES']}.",
        "",
        dominance["selection_trade_off"],
        "",
        "## Three tests",
        "",
    ]
    se = record["special_tests"]["stack_exchange"]
    second = record["special_tests"]["second_opportunity"]
    lines += [
        f"- **Stack Exchange.** Bottleneck `{se['D_bottleneck']}`: {se['why_both']}",
        f"- **Wikimedia saturation.** More same-shape rows dominated: "
        f"{record['special_tests']['wikimedia_saturation']['more_wikimedia_dominated']}. "
        f"{record['special_tests']['wikimedia_saturation']['why']}",
        f"- **Second Opportunity.** Marginal value of the first `{second['CURRENT_OPPORTUNITY_MARGINAL_INFORMATION_VALUE']}`, "
        f"exploration value `{second['SECOND_OPPORTUNITY_EXPLORATION_VALUE']}`. {second['why_low']} {second['why_medium_not_high']}",
        "",
        f"**Next: {record['recommended_next_mission']['title']}.** {record['recommended_next_mission']['shape']}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        record, _, _ = validate()
    except ValidationError as error:
        print(f"REFUSED  post-reconciliation priority: {error}")
        return 1

    text = render(record)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its record")
            return 1
        print("ok       the post-reconciliation priority matches its record")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(f"selected {record['selected_next_move']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
