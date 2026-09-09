"""Render and validate the Mission 1.76 evidence-breadth prioritization.

Three records, and one discipline underneath all of them:

    MORE ROWS IS NOT MORE INFORMATION.

`validate()` enforces the readings this mission was most tempted to make and did not:

  - a row count is not a breadth, and one dimension counted twice is still one;
  - two rows from one publisher are two rows, never two independent witnesses;
  - UNKNOWN independence is not independence, and "different company" is not
    evidence of it;
  - commercial relevance is not willingness to pay, and a procurement value is
    neither actual spend nor a framework maximum nor a price anybody would pay;
  - eligibility belongs to ONE use profile and is never borrowed from another;
  - an unregistered source cannot appear, and a PROHIBITED one cannot be called
    executable;
  - a subject relation that is UNDETERMINED cannot be read as DIRECT;
  - a priority is a tier and never a number, because a weighted sum of
    judgements nobody calibrated looks exactly like a measurement;
  - a dominated candidate cannot win, and a tie is reported as a tie;
  - and Globalping is a dependency, not a candidate, while C9 is PARTIAL.

The Markdown is generated here, so the three pages cannot drift from the records
they describe.

    uv run python infrastructure/scripts/render_evidence_breadth_priority.py
    uv run python infrastructure/scripts/render_evidence_breadth_priority.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

AUDIT = DATA / "opportunity-evidence-breadth-audit-v1.json"
MOVES = DATA / "evidence-completion-candidate-moves-v1.json"
PRIORITY = DATA / "evidence-completion-priority-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v3.json"

RENDERED = {
    AUDIT: DATA / "opportunity-evidence-breadth-audit-v1.md",
    MOVES: DATA / "evidence-completion-candidate-moves-v1.md",
    PRIORITY: DATA / "evidence-completion-priority-v1.md",
}

CONTRIBUTION_CLASSES = (
    "NEW_DECISION_RELEVANT_DIMENSION",
    "INDEPENDENT_CORROBORATION_OF_EXISTING_PROPOSITION",
    "CONTRADICTION_TEST",
    "RELIABILITY_OR_SCORABILITY_COMPLETION",
    "MORE_SAME_DIMENSION_SAME_LINEAGE",
    "CONTEXT_ONLY",
    "NOT_ESTABLISHED",
)
SELECTABLE_CLASSES = CONTRIBUTION_CLASSES[:4]

INFORMATION_GAIN = (
    "DECISION_CHANGING",
    "MAJOR_BREADTH_GAIN",
    "MODERATE_BREADTH_GAIN",
    "LOW_INCREMENTAL_GAIN",
    "UNKNOWN",
)

GOVERNANCE_STATES = (
    "READY_NOW",
    "READY_WITH_EXISTING_CONDITIONS",
    "BOUNDED_REVIEW_REQUIRED",
    "RESOURCE_NOT_READY",
    "REQUIRES_REVIEW",
    "RESTRICTED",
    "PROHIBITED",
    "UNKNOWN",
    "NOT_APPLICABLE_NO_ACQUISITION",
)
EXECUTABLE_GOVERNANCE = (
    "READY_NOW",
    "READY_WITH_EXISTING_CONDITIONS",
    "NOT_APPLICABLE_NO_ACQUISITION",
)

COLLECTOR_STATES = (
    "HELD_DATA_ALREADY_AVAILABLE",
    "COLLECTOR_IMPLEMENTED",
    "COLLECTOR_NOT_IMPLEMENTED_BUT_RESOURCE_READY",
    "RESOURCE_OR_CONTRACT_WORK_REQUIRED",
    "NO_CURRENT_ROUTE",
)
EXECUTABLE_COLLECTOR = ("HELD_DATA_ALREADY_AVAILABLE", "COLLECTOR_IMPLEMENTED")

INDEPENDENCE = (
    "ESTABLISHED_DISTINCT_LINEAGE_ALREADY_DOCUMENTED",
    "PLAUSIBLE_DISTINCT_LINEAGE_REVIEW_REQUIRED",
    "UNKNOWN",
    "KNOWN_DEPENDENT",
    "COMMON_UPSTREAM_REFUTED",
)

COMMERCIAL = (
    "DIRECT_COMMERCIAL_SIGNAL",
    "DIRECT_BUYER_OR_BUDGET_SIGNAL",
    "DIRECT_MARKET_ACTIVITY_SIGNAL",
    "DIRECT_PROBLEM_OR_NEED_SIGNAL",
    "DIRECT_AUDIENCE_OR_USAGE_SIGNAL",
    "DIRECT_TREND_SIGNAL",
    "DIRECT_VALIDATION_SIGNAL",
    "INDIRECT_PRODUCT_CONTEXT",
    "NOT_ESTABLISHED",
)
# A procurement or activity signal is not a price anybody would pay. §17.
WTP_CLASSES = ("DIRECT_COMMERCIAL_SIGNAL", "DIRECT_BUYER_OR_BUDGET_SIGNAL")

SUBJECT_RELATIONS = (
    "DIRECT",
    "CONTEXTUAL_WITH_ESTABLISHED_SCOPE",
    "UNDETERMINED",
    "NOT_THE_SAME_SUBJECT",
)

TIERS = (
    "TIER_1_EXECUTABLE_DECISION_CHANGING",
    "TIER_2_EXECUTABLE_MAJOR_BREADTH",
    "TIER_3_BOUNDED_UNBLOCKING_THEN_HIGH_VALUE",
    "TIER_4_USEFUL_BUT_INCREMENTAL",
    "TIER_5_NOT_CURRENTLY_ACTIONABLE",
)

PRIMARY_OUTCOMES = (
    "NEXT_BOUNDED_EVIDENCE_MOVE_SELECTED",
    "NO_SINGLE_NEXT_MOVE_DOMINATES",
    "REGISTERED_PORTFOLIO_CANNOT_CLOSE_CURRENT_BREADTH_GAP",
    "EVIDENCE_BREADTH_PRIORITIZATION_BLOCKED_BY_ARCHITECTURE",
)

# Any field name that would make a judgement look like a measurement.
FORBIDDEN_SCORE_FIELDS = (
    "priority_score",
    "opportunity_score",
    "market_score",
    "weighted_sum",
    "rank_score",
    "score",
    "weight",
    "probability",
    "confidence_percent",
)

HARD_ZERO = (
    "RESEARCH_API_CALLS",
    "EXTERNAL_PROVIDER_CONTACTS",
    "MODEL_CALLS",
    "EMBEDDINGS",
    "RAW_RECORDS_CREATED",
    "NORMALIZED_RECORDS_CREATED",
    "SIGNALS_CREATED",
    "CLAIMS_CREATED",
    "EVIDENCE_CREATED",
    "OPPORTUNITY_MUTATIONS",
    "INDEPENDENCE_GROUPS_CREATED",
    "RELIABILITY_ASSESSMENTS_CREATED",
    "SOURCES_REGISTERED",
    "SOURCE_GOVERNANCE_MUTATIONS",
    "SCORES",
    "CALIBRATIONS",
    "MIGRATIONS",
    "CANONICAL_MUTATIONS",
)


class ValidationError(RuntimeError):
    """A record says something this gate refuses."""


def _load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise ValidationError(f"{path.name} does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValidationError(f"{path.name} is not a JSON object")
    return record


def _walk_pairs(node: object):
    """Every (key, value) in the tree, so a NUMBER can be told from a sentence about one."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield key, value
            yield from _walk_pairs(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_pairs(item)


def _check_no_fabricated_precision(priority: dict, moves: dict) -> None:
    """A priority is a tier. A number here would be a weighted sum wearing a measurement."""
    if not priority["no_numeric_score_issued"]:
        raise ValidationError("the priority record admits issuing a numeric score")
    if not str(priority["why_no_score"]).strip():
        raise ValidationError("the record does not say why it issues no score")
    # The word is not what is forbidden; a NUMBER posing as a priority is. A field
    # named `why_no_score` holding a sentence is the record explaining itself, and a
    # check that refused it would be refusing the explanation rather than the practice.
    for record, name in ((priority, PRIORITY.name), (moves, MOVES.name)):
        for key, value in _walk_pairs(record):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            lowered = key.lower()
            for forbidden in FORBIDDEN_SCORE_FIELDS:
                if lowered == forbidden or lowered.endswith("_" + forbidden):
                    raise ValidationError(
                        f"{name} carries the numeric field {key!r} = {value}; a ranking "
                        "number here is a weighted sum of uncalibrated judgements that "
                        "reads as a measurement"
                    )


def _check_the_audit_is_measured(audit: dict) -> None:
    if audit["record_kind"] != "EVIDENCE_BREADTH_AUDIT":
        raise ValidationError("the audit record does not declare itself an audit")
    if audit["acquisition_performed"]:
        raise ValidationError("the audit record admits acquiring data")
    if audit["canonical_mutation"] != 0:
        raise ValidationError("the audit record admits a canonical mutation")

    lineages = audit["evidence_lineages"]
    if not lineages:
        raise ValidationError("the audit measured no evidence lineage")
    total = sum(lineage["evidence_rows"] for lineage in lineages)
    if total != audit["canonical_baseline"]["evidence"]:
        raise ValidationError(
            f"the lineages account for {total} evidence rows and the baseline counts "
            f"{audit['canonical_baseline']['evidence']}"
        )

    # A dimension is a KIND of fact. Two lineages differing only in source are not
    # two dimensions, and the audit must not present them as such.
    kinds = [lineage["proposition_kind"] for lineage in lineages]
    if len(kinds) != len(set(kinds)):
        duplicated = sorted({k for k in kinds if kinds.count(k) > 1})
        raise ValidationError(
            f"the audit lists {duplicated} more than once; the same proposition kind counted "
            "twice is one kind, not two"
        )

    if audit["canonical_baseline"]["evidence_independence_groups"] != 0:
        raise ValidationError("an independence group exists and this mission may not create one")

    # A row count is not a breadth. If the record states a breadth at all, it states
    # the number of KINDS -- the number a careless reading would use is the row count.
    stated = audit.get("distinct_evidence_dimensions")
    if stated is not None and stated != len(set(kinds)):
        raise ValidationError(
            f"the audit states {stated} distinct dimensions and measures {len(set(kinds))} "
            "distinct proposition kinds. A row count presented as a breadth is the one "
            "reading this mission exists to refuse"
        )

    # Two rows from one publisher are two rows. With no established group in the
    # corpus, no count of independent witnesses can be anything but zero.
    witnesses = audit.get("independent_witnesses")
    if witnesses:
        raise ValidationError(
            f"the audit counts {witnesses} independent witnesses while the corpus holds no "
            "established independence group. Source diversity is not independence"
        )


def _check_candidates(moves: dict, audit: dict) -> None:
    known_sources = {row["source_id"] for row in audit["local_governance"]}
    local_reviewed = {
        row["source_id"] for row in audit["local_governance"] if row["reviewed_under_local"]
    }
    seen = set()

    for candidate in moves["candidates"]:
        cid = candidate["candidate_id"]
        if cid in seen:
            raise ValidationError(f"{cid} appears twice")
        seen.add(cid)

        for field, vocabulary in (
            ("contribution_class", CONTRIBUTION_CLASSES),
            ("expected_information_gain", INFORMATION_GAIN),
            ("governance_state", GOVERNANCE_STATES),
            ("collector_state", COLLECTOR_STATES),
            ("independence_potential", INDEPENDENCE),
            ("commercial_relevance", COMMERCIAL),
            ("subject_relationship", SUBJECT_RELATIONS),
        ):
            if candidate[field] not in vocabulary:
                raise ValidationError(f"{cid} carries an undefined {field}: {candidate[field]!r}")

        # An unregistered source cannot appear, and this mission may not add one.
        for source in str(candidate["candidate_source"]).replace(" or ", ", ").split(", "):
            token = source.strip()
            if token and token not in known_sources:
                raise ValidationError(
                    f"{cid} names {token!r}, which is not a registered source. This mission "
                    "may not introduce one"
                )

        # Eligibility belongs to ONE profile and is never borrowed.
        if candidate["source_use_profile"] != "local-private-research-v1":
            raise ValidationError(
                f"{cid} is assessed under {candidate['source_use_profile']!r}; readiness is "
                "evaluated under local-private-research-v1 and never unioned"
            )
        if (
            candidate["governance_state"] == "PROHIBITED"
            and candidate["collector_state"] in EXECUTABLE_COLLECTOR
        ):
            raise ValidationError(f"{cid} is PROHIBITED and described as executable")
        primary = str(candidate["candidate_source"]).split(",")[0].split(" or ")[0].strip()
        if (
            candidate["governance_state"] in ("READY_NOW", "READY_WITH_EXISTING_CONDITIONS")
            and primary not in local_reviewed
        ):
            raise ValidationError(
                f"{cid} is called ready under LOCAL and {primary!r} has no LOCAL review. An "
                "absent review is a refusal, never a reason to consult another profile"
            )

        # UNKNOWN independence is not independence.
        if candidate["independence_potential"] == "ESTABLISHED_DISTINCT_LINEAGE_ALREADY_DOCUMENTED":
            raise ValidationError(
                f"{cid} claims documented distinct lineage; no independence group exists in "
                "the corpus, so nothing is documented"
            )

        # Commercial relevance is not willingness to pay.
        if candidate["commercial_relevance"] in WTP_CLASSES:
            raise ValidationError(
                f"{cid} claims {candidate['commercial_relevance']}, which asserts a buyer or "
                "a price. No held Claim supports willingness to pay, and market activity is "
                "not a price anybody would pay"
            )

        # A dimension claim needs a dimension; a scorability move must say it adds none.
        if candidate["contribution_class"] == "NEW_DECISION_RELEVANT_DIMENSION":
            if not candidate.get("target_missing_dimension"):
                raise ValidationError(f"{cid} claims a new dimension and names none")
        elif candidate.get("target_missing_dimension"):
            raise ValidationError(
                f"{cid} names a target dimension without claiming the dimension class"
            )
        if (
            candidate["contribution_class"] == "RELIABILITY_OR_SCORABILITY_COMPLETION"
            and not str(candidate.get("why_no_dimension") or "").strip()
        ):
            raise ValidationError(
                f"{cid} is a scorability move and does not say it adds no dimension"
            )

        for field in ("why_it_could_change_a_downstream_decision", "why_it_might_fail"):
            if not str(candidate[field]).strip():
                raise ValidationError(f"{cid} states no {field}")

    if not moves["registered_source_gap"]["gap_exists"]:
        raise ValidationError(
            "the record denies a registered-source gap while naming dimensions no reviewed "
            "source reaches"
        )


def _check_priority(priority: dict, moves: dict, audit: dict) -> None:
    candidates = {c["candidate_id"]: c for c in moves["candidates"]}
    eliminated = {c["candidate_id"] for c in moves["eliminated_before_ranking"]}

    tiered = [cid for tier in TIERS for cid in priority["tiers"][tier]]
    if sorted(tiered) != sorted(candidates):
        raise ValidationError("the tiers and the candidate list do not cover the same set")
    if len(tiered) != len(set(tiered)):
        raise ValidationError("a candidate appears in two tiers")
    for tier in priority["tiers"]:
        if tier not in TIERS:
            raise ValidationError(f"the tier {tier!r} is undefined")

    # A candidate eliminated before ranking may not reappear in a tier.
    if eliminated & set(tiered):
        raise ValidationError(f"{sorted(eliminated & set(tiered))} was eliminated and then ranked")

    # Tier 1 means executable AND decision-changing. Both, or it is not tier 1.
    for cid in priority["tiers"]["TIER_1_EXECUTABLE_DECISION_CHANGING"]:
        candidate = candidates[cid]
        if candidate["expected_information_gain"] != "DECISION_CHANGING":
            raise ValidationError(f"{cid} is in tier 1 without DECISION_CHANGING gain")
        if candidate["governance_state"] not in EXECUTABLE_GOVERNANCE:
            raise ValidationError(f"{cid} is in tier 1 and is not governance-executable")
        if candidate["collector_state"] not in EXECUTABLE_COLLECTOR:
            raise ValidationError(f"{cid} is in tier 1 with no route to the data")
        if candidate["external_action_required"]:
            raise ValidationError(f"{cid} is in tier 1 and needs an external action first")

    # A lower-gain candidate may not sit above a higher-gain one without saying why.
    #
    # UNKNOWN is excluded from the comparison rather than ranked last. It is not a
    # smaller gain than LOW_INCREMENTAL_GAIN; it is an UNBOUNDED one, and ordering it
    # below "a little" would assert exactly what UNKNOWN denies. A candidate placed
    # above another on an unbounded gain has to name the criterion that placed it.
    order = {gain: rank for rank, gain in enumerate(INFORMATION_GAIN) if gain != "UNKNOWN"}
    rationale = priority["tier_placements"]
    for index, tier in enumerate(TIERS[:-1]):
        for cid in priority["tiers"][tier]:
            gain = candidates[cid]["expected_information_gain"]
            for lower_tier in TIERS[index + 1 :]:
                for other in priority["tiers"][lower_tier]:
                    other_gain = candidates[other]["expected_information_gain"]
                    if gain == "UNKNOWN" or other_gain == "UNKNOWN":
                        if not str(rationale.get(cid) or "").strip():
                            raise ValidationError(
                                f"{cid} sits above {other} across an UNBOUNDED gain and the "
                                "record names no criterion that placed it"
                            )
                        continue
                    if order[gain] > order[other_gain]:
                        raise ValidationError(
                            f"{cid} outranks {other} with strictly lower information gain and "
                            "the record gives no higher-priority reason"
                        )

    selection = priority["selection"]
    if selection["primary_outcome"] not in PRIMARY_OUTCOMES:
        raise ValidationError(f"the outcome {selection['primary_outcome']!r} is undefined")

    if selection["primary_outcome"] == "NEXT_BOUNDED_EVIDENCE_MOVE_SELECTED":
        winner = selection["selected_candidate"]
        if winner not in candidates:
            raise ValidationError("the selected candidate is not a candidate")
        if candidates[winner]["contribution_class"] not in SELECTABLE_CLASSES:
            raise ValidationError(
                f"{winner} is selected on a contribution class that cannot be selected"
            )
        if candidates[winner]["subject_relationship"] == "NOT_THE_SAME_SUBJECT":
            raise ValidationError(f"{winner} is selected against a subject it does not share")
        if candidates[winner]["subject_relationship"] == "UNDETERMINED":
            raise ValidationError(
                f"{winner} is selected on an UNDETERMINED subject relation, which may not be "
                "promoted to DIRECT"
            )
        if selection["dominated_by_another"]:
            raise ValidationError("a dominated candidate was selected")
        for entry in priority["dominance"]:
            if entry["pair"].startswith("anything over") and entry["dominates"]:
                raise ValidationError("the record says the winner is dominated and selects it")
        if winner not in priority["tiers"]["TIER_1_EXECUTABLE_DECISION_CHANGING"]:
            raise ValidationError("the selected candidate is not in tier 1")

        nxt = priority["next_mission"]
        if not nxt["IT_IS_ONE_MOVE"]:
            raise ValidationError("the next mission is not one bounded move")
        for field in ("WHY_THIS_MOVE", "WHAT_IT_CAN_ESTABLISH", "WHAT_IT_CANNOT_ESTABLISH"):
            if not nxt[field]:
                raise ValidationError(f"the next mission states no {field}")

    # Globalping is a dependency, never a candidate, while C9 is PARTIAL.
    gates = {g["dimension"]: g["status"] for g in _load(QUALIFICATION)["gates"]}
    c9 = gates["C9_RIGHTS_FEASIBILITY"]
    dependency = priority["globalping_dependency"]
    if dependency["c9"] != c9:
        raise ValidationError(
            f"the record says C9 is {dependency['c9']!r} and the qualification says {c9!r}"
        )
    if c9 != "PASS" and dependency["selectable_now"]:
        raise ValidationError("Globalping is marked selectable while C9 is not PASS")
    if dependency["checked_externally_by_this_mission"]:
        raise ValidationError("this mission checked Globalping externally")
    if selection.get("selected_candidate") in {
        c["candidate_id"] for c in moves["eliminated_before_ranking"]
    }:
        raise ValidationError("an eliminated candidate was selected")

    accounting = priority["mission_accounting"]
    for counter in HARD_ZERO:
        if counter not in accounting:
            raise ValidationError(f"the accounting does not report {counter}")
        if accounting[counter] != 0:
            raise ValidationError(f"{counter} is {accounting[counter]}, and it must be 0")


def validate() -> tuple[dict, dict, dict]:
    audit = _load(AUDIT)
    moves = _load(MOVES)
    priority = _load(PRIORITY)
    try:
        _check_the_audit_is_measured(audit)
        _check_candidates(moves, audit)
        _check_no_fabricated_precision(priority, moves)
        _check_priority(priority, moves, audit)
    except (KeyError, TypeError, IndexError) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return audit, moves, priority


# ------------------------------------------------------------------------ renderers


def _pointer_lines(record: dict) -> list[str]:
    """Mission 1.66.1's shape: a later mission appends one forward pointer and edits nothing."""
    pointer = record.get("forward_pointer")
    if not pointer:
        return []
    return [
        "",
        "## Forward pointer",
        "",
        f"Appended by Mission {pointer['appended_by_mission']}; nothing above it changed. "
        f"See `{pointer['superseded_by']}`.",
        "",
        pointer["what_changed_in_the_successor"],
        "",
    ]


def render_audit(audit: dict) -> str:
    baseline = audit["canonical_baseline"]
    opportunity = audit["opportunity"]
    lines = [
        "# The current evidence surface, measured",
        "",
        f"Generated from `{AUDIT.name}`. Do not edit by hand.",
        "",
        "Measured from the live canonical deployment during Mission 1.76. Nothing was "
        "acquired and nothing was written.",
        "",
        "## The one Opportunity",
        "",
        f"**{opportunity['title']}** — target actor `{opportunity['target_actor']}`, "
        f"market scope `{opportunity['market_scope_key']}`.",
        "",
        f"- **supported dimensions ({len(opportunity['supported_dimensions'])}):** "
        + ", ".join(f"`{d}`" for d in opportunity["supported_dimensions"]),
        f"- **unsupported dimensions ({len(opportunity['unsupported_dimensions'])}):** "
        + ", ".join(f"`{d}`" for d in opportunity["unsupported_dimensions"]),
        "",
        "### Named limitations, in the record's own words",
        "",
    ]
    lines += [f"{n}. {text}" for n, text in enumerate(opportunity["epistemic_limitations"], 1)]
    lines += [
        "",
        "## Evidence lineages",
        "",
        "Breadth is a count of KINDS, not of rows. Ten lineages carry "
        f"{baseline['evidence']} rows.",
        "",
        "| source | proposition kind | rows | claims | reliability written | on the Opportunity |",
        "|---|---|---|---|---|---|",
    ]
    for lineage in audit["evidence_lineages"]:
        lines.append(
            f"| `{lineage['source_id']}` | `{lineage['proposition_kind']}` "
            f"| {lineage['evidence_rows']} | {lineage['claims']} "
            f"| {lineage['with_reliability']} | {lineage['on_the_opportunity']} |"
        )

    lines += [
        "",
        "## Reviewed reliability that exists",
        "",
        "| source | proposition kind | resource | reliability |",
        "|---|---|---|---|",
    ]
    for a in audit["reliability_assessments"]:
        lines.append(
            f"| `{a['source_id']}` | `{a['proposition_kind']}` | `{a['resource_id']}` "
            f"| {a['reliability']} |"
        )

    lines += [
        "",
        "## Held records that feed no signal",
        "",
        "| source | record kind | collector | normalized | feeding no signal |",
        "|---|---|---|---|---|",
    ]
    for held in audit["held_records"]:
        lines.append(
            f"| `{held['source_id']}` | `{held['record_kind_id']}` | `{held['collector_id']}` "
            f"| {held['normalized']} | {held['not_feeding_a_signal']} |"
        )

    reviewed = [g for g in audit["local_governance"] if g["reviewed_under_local"]]
    lines += [
        "",
        "## Governance under `local-private-research-v1`",
        "",
        f"**{len(reviewed)} of {len(audit['local_governance'])} registered sources have a "
        "review under this profile.** An absent review is a refusal and never a reason to "
        "consult another profile.",
        "",
        "| source | family | approval | blocking reasons | collector enabled |",
        "|---|---|---|---|---|",
    ]
    for row in reviewed:
        reasons = ", ".join(row["blocking_reasons"]) or "—"
        lines.append(
            f"| `{row['source_id']}` | {row['source_family']} | `{row['approval_state']}` "
            f"| {reasons} | {row['collector_enabled']} |"
        )

    lines += [
        "",
        "## Canonical baseline",
        "",
        "| | |",
        "|---|---|",
        f"| migration head | `{audit['migration_head']}` |",
    ]
    for label, value in baseline.items():
        lines.append(f"| {label} | {value} |")
    lines.append("")
    lines += _pointer_lines(audit)
    return "\n".join(lines)


def render_moves(moves: dict) -> str:
    lines = [
        "# Candidate evidence-completion moves",
        "",
        f"Generated from `{MOVES.name}`. Do not edit by hand.",
        "",
        "Generated only from facts the repository already holds. No source was discovered "
        "and nothing was acquired.",
        "",
        "| id | move | subject relation | contribution | gain | governance | collector |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in moves["candidates"]:
        lines.append(
            f"| **{c['candidate_id']}** | {c['title']} | `{c['subject_relationship']}` "
            f"| `{c['contribution_class']}` | `{c['expected_information_gain']}` "
            f"| `{c['governance_state']}` | `{c['collector_state']}` |"
        )

    for c in moves["candidates"]:
        lines += [
            "",
            f"## {c['candidate_id']} — {c['title']}",
            "",
            f"- **subject:** {c['subject_id']}",
            f"- **relevance to the Opportunity:** {c['opportunity_relevance']}",
            f"- **source:** `{c['candidate_source']}` ({c['source_family']}), assessed under "
            f"`{c['source_use_profile']}`",
            f"- **independence potential:** `{c['independence_potential']}`",
            f"- **commercial relevance:** `{c['commercial_relevance']}`",
            f"- **evidence value / scorability / reliability work:** `{c['evidence_value']}` / "
            f"`{c['scorability_state']}` / `{c['reliability_work_required']}`",
            f"- **external action required:** {c['external_action_required']}",
            "",
            f"**Why it could change a decision.** {c['why_it_could_change_a_downstream_decision']}",
            "",
            f"**Why it might fail.** {c['why_it_might_fail']}",
        ]
        if c["known_blockers"]:
            lines += ["", "**Blockers.**", ""]
            lines += [f"- {b}" for b in c["known_blockers"]]

    gap = moves["registered_source_gap"]
    lines += [
        "",
        "## The registered-source gap",
        "",
        gap["why"],
        "",
        "Dimensions no reviewed source currently reaches: "
        + ", ".join(f"`{d}`" for d in gap["unreachable_dimensions"])
        + ".",
        "",
        "## Eliminated before ranking",
        "",
    ]
    for entry in moves["eliminated_before_ranking"]:
        lines.append(f"- **{entry['candidate_id']}** — {entry['title']}. {entry['why']}")
    lines.append("")
    lines += _pointer_lines(moves)
    return "\n".join(lines)


def render_priority(priority: dict) -> str:
    selection = priority["selection"]
    nxt = priority["next_mission"]
    lines = [
        "# The priority decision",
        "",
        f"Generated from `{PRIORITY.name}`. Do not edit by hand.",
        "",
        f"**Outcome: `{selection['primary_outcome']}` — {selection['selected_candidate']}.**",
        "",
        f"No numeric score was issued. {priority['why_no_score']}",
        "",
        "## Tiers",
        "",
        "| tier | candidates |",
        "|---|---|",
    ]
    for tier in TIERS:
        members = ", ".join(f"`{c}`" for c in priority["tiers"][tier]) or "—"
        lines.append(f"| {tier} | {members} |")

    lines += [
        "",
        f"**Tier 2 is empty.** {priority['tier_2_is_empty_because']}",
        "",
        "## Lexicographic criteria, fixed before the candidates were read",
        "",
    ]
    lines += [f"{n}. {c}" for n, c in enumerate(priority["lexicographic_criteria"], 1)]

    lines += [
        "",
        "## Dominance",
        "",
        "| pair | dominates | why |",
        "|---|---|---|",
    ]
    for entry in priority["dominance"]:
        lines.append(f"| {entry['pair']} | {entry['dominates']} | {entry['why']} |")

    lines += [
        "",
        "## Selection",
        "",
        f"**Uniquely dominant: {selection['uniquely_dominant']}.** "
        f"{selection['why_selected_without_being_uniquely_dominant']}",
        "",
        selection["not_selected_because_it_is_the_only_opportunity"],
        "",
        f"## Next: Mission {nxt['NEXT_MISSION_ID']} — {nxt['NEXT_MISSION_TITLE']}",
        "",
        f"- **target subject:** {nxt['TARGET_SUBJECT']}",
        f"- **target property:** `{nxt['TARGET_PROPERTY']}`",
        f"- **target source:** {nxt['TARGET_SOURCE']}",
        f"- **external action required:** {nxt['EXTERNAL_ACTION_REQUIRED']}",
        f"- **canonical mutation expected:** {nxt['CANONICAL_MUTATION_EXPECTED']}",
        "",
        nxt["WHY_THIS_MOVE"],
        "",
        "**What it can establish.**",
        "",
    ]
    lines += [f"- {item}" for item in nxt["WHAT_IT_CAN_ESTABLISH"]]
    lines += ["", "**What it cannot establish.**", ""]
    lines += [f"- {item}" for item in nxt["WHAT_IT_CANNOT_ESTABLISH"]]

    dependency = priority["globalping_dependency"]
    lines += [
        "",
        "## Globalping, as a dependency",
        "",
        f"State `{dependency['state']}`, C9 `{dependency['c9']}`. Selectable now: "
        f"**{dependency['selectable_now']}**. {dependency['why']}.",
        "",
        f"What a future qualification could unlock: {dependency['what_a_future_qualification_could_unlock']}.",
        "",
        f"Checked externally by this mission: **{dependency['checked_externally_by_this_mission']}**.",
        "",
    ]
    return "\n".join(lines)


RENDERERS = {AUDIT: render_audit, MOVES: render_moves, PRIORITY: render_priority}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = dict(zip((AUDIT, MOVES, PRIORITY), validate(), strict=True))
    except ValidationError as error:
        print(f"REFUSED  evidence breadth prioritization: {error}")
        return 1

    rendered = {RENDERED[path]: RENDERERS[path](record) for path, record in records.items()}
    if args.check:
        for path, text in rendered.items():
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print(f"ok       {len(rendered)} evidence-breadth documents match their records")
        return 0

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    priority = records[PRIORITY]
    print(f"outcome  {priority['selection']['primary_outcome']}")
    print(f"selected {priority['selection']['selected_candidate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
