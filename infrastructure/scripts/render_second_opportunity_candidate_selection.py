"""Render and validate the second-Opportunity candidate selection (Mission 1.80).

A candidate selection is a decision record over held packets, and the gate holds it to the
records it claims to have read: the current preparation record (packets, rows, eligibility,
resolver outcomes, egress), the reconciliation record (counters and the current revision),
the reviewed scope rules and subject registry, and the parked apparatus arc. It refuses:

    A CANDIDATE THAT IS NOT A HELD PACKET, OR IS TWO OF THEM. The universe is exactly the
    non-docker packets of the current preparation, each with the size, scorable count,
    dimensions, sources, reliabilities, independence, formability and egress the
    preparation gives it. Kubernetes is not merged with docker; a CPV division is not
    narrowed on the way past; a category is not a product.

    PROCUREMENT READ AS COMMERCE. A notice value is not willingness to pay, not realised
    spend, not market size and not demand; a contracting authority is not a buyer for an
    unspecified product. Population change is not demand. Publication is not audience.

    ORDINAL FIELDS THAT DISAGREE WITH THE COUNTS. Breadth is a count of rows, diversity a
    count of dimensions, and more rows never becomes more dimensions. Scorable is not
    independent: with zero groups and every row UNKNOWN, independence is UNKNOWN.

    EGRESS DECIDED, OR MISTAKEN FOR COLLECTION. A source whose transmission is NOT_ASSESSED
    is not egress eligible, is not vetoed for it alone, and is neither granted nor denied
    here.

    A SELECTION THAT IS NOT EARNED. A selected subject is on the recomputed frontier,
    carries no veto, is formable, and sits at an actionable grain; a category may be
    selected only as an exploratory category hypothesis, never as a product. The four
    outcomes each require their own evidence, and none of them creates an Opportunity,
    calls a model, acquires data, creates an assessment, persists a score, changes the
    docker revision or moves the parked arc.

    uv run python infrastructure/scripts/render_second_opportunity_candidate_selection.py
    uv run python infrastructure/scripts/render_second_opportunity_candidate_selection.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

SELECTION = DATA / "second-opportunity-candidate-selection-v1.json"
RENDERED = DATA / "second-opportunity-candidate-selection-v1.md"
PREPARATION = DATA / "opportunity-preparation-v2.json"
RECONCILIATION = DATA / "opportunity-reliability-reconciliation-v1.json"
SCOPE_RULES = DATA / "observation-scope-rules-v1.json"
SUBJECT_REGISTRY = DATA / "canonical-subject-registry-v1.json"

SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v4.json"
V2_DECISION = DATA / "v2-vantage-class-decision-v1.json"

OUTCOMES = (
    "SECOND_OPPORTUNITY_CANDIDATE_SELECTED",
    "NO_HELD_SUBJECT_AT_ACTIONABLE_OPPORTUNITY_GRAIN",
    "SECOND_OPPORTUNITY_REQUIRES_SUBJECT_NARROWING",
    "SECOND_OPPORTUNITY_CANDIDATE_SELECTION_REQUIRES_SEMANTIC_DECISION",
)
SUBJECT_TYPES = (
    "PRODUCT",
    "TOOL",
    "SERVICE",
    "PROBLEM",
    "MARKET_SEGMENT",
    "CATEGORY",
    "METRIC",
    "TOPIC",
)
PRODUCT_LIKE = {"PRODUCT", "TOOL", "SERVICE", "PROBLEM"}
INTERVENTION_GRAINS = (
    "DIRECTLY_SUPPORTED",
    "PLAUSIBLE_BUT_REQUIRES_SYNTHESIS",
    "TOO_BROAD_TO_BE_ACTIONABLE",
    "NOT_ESTABLISHED",
)
ACTIONABLE_GRAINS = (
    "ACTIONABLE_AT_CURRENT_GRAIN",
    "ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS",
    "REQUIRES_NARROWER_SUBJECT_DISCOVERY",
    "NOT_ACTIONABLE",
)
SELECTABLE_GRAINS = ACTIONABLE_GRAINS[:2]
INFORMATION = ["NONE", "LOW", "MEDIUM", "HIGH"]
FORMABILITY = ["NO", "YES"]
YES_NO = ["NO", "YES"]
SCOPES = ("PRODUCT", "CATEGORY", "MARKET", "GEOGRAPHY", "UNDETERMINED")
NON_COUNTING = {"TREND_OR_CHANGE"}
COMMERCIAL = {
    "MARKET_ACTIVITY",
    "BUYER_OR_BUDGET_EXISTENCE",
    "ECONOMIC_VALUE",
    "WILLINGNESS_TO_PAY",
}
PROBLEM = {"PROBLEM_OR_NEED", "SOLUTION_GAP", "SOLUTION_DISSATISFACTION"}
ORDINAL_FIELDS = (
    "EVIDENCE_BREADTH",
    "SCORABLE_BREADTH",
    "COUNTING_DIMENSION_DIVERSITY",
    "SOURCE_DIVERSITY",
    "COMMERCIAL_INFORMATION",
    "PROBLEM_INFORMATION",
    "PRODUCT_RELEVANCE",
    "SEMANTIC_SPECIFICITY",
    "PROVENANCE_DIVERSITY",
    "INDEPENDENCE",
    "HYPOTHESIS_FORMABILITY",
    "GOVERNANCE_DISTANCE_TO_SYNTHESIS",
    "NEW_ACQUISITION_REQUIRED",
    "OPERATOR_JUDGMENT_REQUIRED",
    "ARCHITECTURE_WORK_REQUIRED",
    "OVERINTERPRETATION_RISK",
)
FORBIDDEN_NUMERIC_KEYS = ("score", "priority_score", "weighted", "points", "rank")


class ValidationError(Exception):
    pass


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rank(scale: list[str], value: object, label: str) -> int:
    if value not in scale:
        raise ValidationError(f"{label} carries {value!r}, not one of {scale}")
    return scale.index(value)


def _breadth(n: int) -> str:
    return "LOW" if n <= 2 else ("MEDIUM" if n <= 9 else "HIGH")


def _scorable_breadth(n: int) -> str:
    return "LOW" if n == 0 else ("MEDIUM" if n <= 9 else "HIGH")


def _diversity(n: int) -> str:
    return "LOW" if n <= 1 else ("MEDIUM" if n == 2 else "HIGH")


# ------------------------------------------------------------------------- scope


def _scope_of(subject_key: str, rules: dict, registry: dict) -> tuple[str, str]:
    """(scope, basis) from the reviewed rules and the registry, and UNDETERMINED otherwise."""
    if subject_key.startswith("subject:"):
        subject_id = subject_key.split(":", 1)[1]
        for entry in registry["subjects"]:
            if entry["subject_id"] == subject_id:
                return entry["scope_type"], "REGISTRY"
        raise ValidationError(f"{subject_key}: not a registered canonical subject")
    parts = subject_key.split(":")
    if len(parts) < 3:
        raise ValidationError(f"{subject_key}: not a source-native subject key")
    for rule in rules["rules"]:
        if rule["source_id"] == parts[0] and rule["scheme"] == parts[1]:
            return rule["scope_type"], "SOURCE_NATIVE"
    return "UNDETERMINED", "NO_RULE"


# ------------------------------------------------------------------------- checks


def _universe(record: dict, preparation: dict, reconciliation: dict) -> dict[str, dict]:
    """Every non-docker packet, once, and nothing that is not a packet."""
    docker_packet = reconciliation["current_evidence"]["packet_id_now"]
    packets = {p["subject"]: p for p in preparation["packets"]}
    expected = {s for s, p in packets.items() if p["packet_id"] != docker_packet}
    universe = record["candidate_universe"]
    listed = universe["subjects"]
    if len(listed) != len(set(listed)):
        raise ValidationError("a subject is listed twice in the universe")
    if set(listed) != expected:
        raise ValidationError(
            f"the universe lists {sorted(set(listed) - expected)} that are not held packets "
            f"and omits {sorted(expected - set(listed))}"
        )
    if universe["count"] != len(expected):
        raise ValidationError("the universe count disagrees with the packets")
    for excluded in universe["excluded"]:
        if packets[excluded["subject"]]["packet_id"] != docker_packet:
            raise ValidationError(f"{excluded['subject']} excluded without being the docker packet")
    candidates = {c["subject_key"]: c for c in record["candidates"]}
    if set(candidates) != expected:
        raise ValidationError("the candidates are not exactly the universe")
    for subject, c in candidates.items():
        if "+" in subject or subject in ("subject:docker",):
            raise ValidationError(f"{subject}: a merged or docker subject as a candidate")
        if c["packet_id"] != packets[subject]["packet_id"]:
            raise ValidationError(f"{subject}: packet id is not the held packet's")
    return {s: packets[s] for s in expected}


def _check_candidate_facts(
    c: dict, packet: dict, rows: dict, assessments: dict, rules: dict, registry: dict
) -> None:
    s = c["subject_key"]
    packet_rows = [rows[e] for e in packet["evidence_ids"]]
    scorable = [r for r in packet_rows if r["scorable"]]
    if c["evidence_rows"] != packet["size"] or len(packet_rows) != packet["size"]:
        raise ValidationError(f"{s}: evidence rows disagree with the packet")
    if c["scorable_rows"] != len(scorable):
        raise ValidationError(f"{s}: scorable rows disagree with the resolver")
    if c["non_scorable_rows"] != packet["size"] - len(scorable):
        raise ValidationError(f"{s}: non-scorable rows do not complete the packet")
    if sorted(c["counting_dimensions"]) != sorted(packet["counting_dimensions"]):
        raise ValidationError(f"{s}: counting dimensions disagree with the preparation")
    if sorted(c["noncounting_dimensions"]) != sorted(
        d for d in packet["dimensions"] if d in NON_COUNTING
    ):
        raise ValidationError(f"{s}: non-counting dimensions disagree with the preparation")
    if set(c["counting_dimensions"]) & NON_COUNTING:
        raise ValidationError(f"{s}: a non-counting dimension counted")
    if sorted(c["source_ids"]) != sorted(packet["source_ids"]):
        raise ValidationError(f"{s}: sources disagree with the packet")
    if sorted(c["source_families"]) != sorted(packet["source_families"]):
        raise ValidationError(f"{s}: source families disagree with the packet")
    # reliabilities, from the resolver outcome and the assessments the reconciliation names
    distribution: dict[str, int] = {}
    for r in packet_rows:
        res = r["reliability_resolution"]
        if res["outcome"] == "RESOLVED":
            value = assessments[res["assessment_id"]]["reliability"]
            key = json.dumps(value)
        else:
            key = "NONE"
        distribution[key] = distribution.get(key, 0) + 1
    recorded = {str(k): v for k, v in c["reliability_distribution"].items()}
    if recorded != {str(k): v for k, v in distribution.items()}:
        raise ValidationError(
            f"{s}: reliability distribution {recorded} is not the resolver's {distribution}"
        )
    for kind, entry in c["proposition_kinds"].items():
        if entry.get("assessment_id"):
            a = assessments.get(entry["assessment_id"])
            if a is None or a["proposition_kind"] != kind:
                raise ValidationError(f"{s}: {kind} bound to an assessment of another kind")
            if a["source_id"] not in packet["source_ids"]:
                raise ValidationError(f"{s}: {kind} bound to another source's assessment")
            bound = sum(
                1
                for r in packet_rows
                if r["reliability_resolution"].get("assessment_id") == entry["assessment_id"]
            )
            if entry["rows"] != bound or entry["reliability"] != a["reliability"]:
                raise ValidationError(f"{s}: {kind} rows or reliability disagree with the resolver")
    if sum(e["rows"] for e in c["proposition_kinds"].values()) != packet["size"]:
        raise ValidationError(f"{s}: proposition kinds do not account for every row")
    # independence
    states = {r["independence_state"] for r in packet_rows}
    if c["independence_state"] != (states.pop() if len(states) == 1 else "MIXED"):
        raise ValidationError(f"{s}: independence state disagrees with the rows")
    # formability and readiness, from the sufficiency
    if c["hypothesis_formable"] != (packet["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"):
        raise ValidationError(f"{s}: formability disagrees with the sufficiency rule")
    if c["scoring_ready_packet_property"] != packet["sufficiency"]["scoring_ready"]:
        raise ValidationError(f"{s}: scoring-ready disagrees with the packet property")
    # egress, from the gate the preparation already ran
    egress = packet["external_synthesis"]["availability"]
    if c["egress_state"] != egress:
        raise ValidationError(f"{s}: egress state is not the preparation's {egress}")
    eligible = egress == "AVAILABLE"
    if c["egress_eligible"] != eligible:
        raise ValidationError(f"{s}: egress eligibility disagrees with the availability")
    if c["egress_review_required_before_synthesis"] != (not eligible):
        raise ValidationError(f"{s}: egress review requirement disagrees with eligibility")
    # scope, from the reviewed rules
    scope, _ = _scope_of(s, rules, registry)
    if c["subject_scope"] != scope:
        raise ValidationError(
            f"{s}: subject scope {c['subject_scope']} is not the reviewed {scope}"
        )
    if c["subject_type"] not in SUBJECT_TYPES:
        raise ValidationError(f"{s}: subject type {c['subject_type']!r}")
    if scope == "CATEGORY" and c["subject_type"] != "CATEGORY":
        raise ValidationError(f"{s}: a CATEGORY scope typed as {c['subject_type']}")
    if scope == "PRODUCT" and c["subject_type"] not in PRODUCT_LIKE:
        raise ValidationError(f"{s}: a PRODUCT scope typed as {c['subject_type']}")
    if scope in ("GEOGRAPHY", "UNDETERMINED") and c["subject_type"] in PRODUCT_LIKE | {"CATEGORY"}:
        raise ValidationError(f"{s}: a {scope} scope typed as {c['subject_type']}")
    # provenance shapes: one publisher and every row UNKNOWN is one shape
    if len(packet["source_ids"]) == 1 and states == set() and c["provenance_shapes"] != 1:
        raise ValidationError(f"{s}: one publisher with UNKNOWN rows is one provenance shape")
    # what it establishes
    if c["establishes_product_demand"]:
        raise ValidationError(f"{s}: recorded as establishing product demand")
    if not str(c["does_not_establish"]).strip() or not str(c["establishes"]).strip():
        raise ValidationError(f"{s}: what it establishes or does not is blank")
    if "ted-eu" in packet["source_ids"]:
        sem = c["procurement_semantics"]
        if sem["value_is_realised_spend"] or sem["value_is_willingness_to_pay"]:
            raise ValidationError(f"{s}: a notice value read as spend or willingness to pay")
        if sem["authority_is_buyer_for_unspecified_product"]:
            raise ValidationError(f"{s}: a contracting authority read as a SaaS buyer")
        if "WILLINGNESS_TO_PAY" in c["counting_dimensions"]:
            raise ValidationError(f"{s}: willingness to pay counted from a notice")
    if "gdelt" in packet["source_ids"] and c["counting_dimensions"]:
        raise ValidationError(f"{s}: publication read as audience")
    if "world-bank" in packet["source_ids"] and c["counting_dimensions"]:
        raise ValidationError(f"{s}: population read as demand")


def _check_ordinals(c: dict, packet: dict, rows: dict, groups: int) -> None:
    s = c["subject_key"]
    o = c["ordinal"]
    for field in ORDINAL_FIELDS:
        if field not in o:
            raise ValidationError(f"{s}: ordinal {field} missing")
    for key in c:
        if any(k in key.lower() for k in FORBIDDEN_NUMERIC_KEYS) and isinstance(
            c[key], int | float
        ):
            raise ValidationError(f"{s}: a numeric {key}; a priority is a tier, never a number")
    packet_rows = [rows[e] for e in packet["evidence_ids"]]
    scorable = sum(1 for r in packet_rows if r["scorable"])
    expected = {
        "EVIDENCE_BREADTH": _breadth(packet["size"]),
        "SCORABLE_BREADTH": _scorable_breadth(scorable),
        "COUNTING_DIMENSION_DIVERSITY": _diversity(len(packet["counting_dimensions"])),
        "SOURCE_DIVERSITY": _diversity(len(packet["source_ids"])),
        "HYPOTHESIS_FORMABILITY": "YES" if c["hypothesis_formable"] else "NO",
        "NEW_ACQUISITION_REQUIRED": "NO" if c["hypothesis_formable"] else "YES",
        "PROVENANCE_DIVERSITY": "LOW" if c["provenance_shapes"] == 1 else "MEDIUM",
        "SEMANTIC_SPECIFICITY": "HIGH" if c["subject_scope"] in ("PRODUCT", "GEOGRAPHY") else "LOW",
    }
    for field, value in expected.items():
        if o[field] != value:
            raise ValidationError(f"{s}: {field} is {o[field]}, the counts say {value}")
    if not set(c["counting_dimensions"]) & COMMERCIAL and o["COMMERCIAL_INFORMATION"] != "NONE":
        raise ValidationError(f"{s}: commercial information without a commercial dimension")
    if set(c["counting_dimensions"]) & COMMERCIAL and o["COMMERCIAL_INFORMATION"] == "NONE":
        raise ValidationError(f"{s}: a commercial dimension recorded as no commercial information")
    if (
        "WILLINGNESS_TO_PAY" not in c["counting_dimensions"]
        and o["COMMERCIAL_INFORMATION"] == "HIGH"
    ):
        raise ValidationError(f"{s}: HIGH commercial information without willingness to pay")
    if not set(c["counting_dimensions"]) & PROBLEM and o["PROBLEM_INFORMATION"] != "NONE":
        raise ValidationError(f"{s}: problem information without a problem dimension")
    if (
        groups == 0
        and all(r["independence_state"] == "UNKNOWN" for r in packet_rows)
        and o["INDEPENDENCE"] != "UNKNOWN"
    ):
        raise ValidationError(f"{s}: scorable read as independent with zero groups")
    if c["egress_eligible"] and o["GOVERNANCE_DISTANCE_TO_SYNTHESIS"] != "NONE":
        raise ValidationError(f"{s}: governance distance with every source egress eligible")
    if not c["egress_eligible"] and o["GOVERNANCE_DISTANCE_TO_SYNTHESIS"] == "NONE":
        raise ValidationError(f"{s}: no governance distance while egress is not eligible")
    for field in ("OPERATOR_JUDGMENT_REQUIRED", "ARCHITECTURE_WORK_REQUIRED"):
        _rank(YES_NO, o[field], f"{s}.{field}")
    _rank(INFORMATION, o["OVERINTERPRETATION_RISK"], f"{s}.OVERINTERPRETATION_RISK")
    _rank(INFORMATION + ["UNKNOWN"], o["PRODUCT_RELEVANCE"], f"{s}.PRODUCT_RELEVANCE")
    if c["product_relevance"] != o["PRODUCT_RELEVANCE"]:
        raise ValidationError(f"{s}: product relevance stated twice, differently")


def _check_grain(c: dict) -> None:
    s = c["subject_key"]
    if c["product_intervention_grain"] not in INTERVENTION_GRAINS:
        raise ValidationError(f"{s}: intervention grain {c['product_intervention_grain']!r}")
    if c["actionable_grain"] not in ACTIONABLE_GRAINS:
        raise ValidationError(f"{s}: actionable grain {c['actionable_grain']!r}")
    grain, act, kind = c["product_intervention_grain"], c["actionable_grain"], c["subject_type"]
    if kind == "CATEGORY" and grain == "DIRECTLY_SUPPORTED":
        raise ValidationError(f"{s}: a category is not a product")
    if kind == "CATEGORY" and act == "ACTIONABLE_AT_CURRENT_GRAIN":
        raise ValidationError(f"{s}: a category actionable at its own grain")
    if not c["hypothesis_formable"] and act in SELECTABLE_GRAINS:
        raise ValidationError(f"{s}: actionable while not formable")
    if act == "ACTIONABLE_AT_CURRENT_GRAIN" and (
        kind not in PRODUCT_LIKE or grain != "DIRECTLY_SUPPORTED"
    ):
        raise ValidationError(
            f"{s}: actionable at current grain without a directly supported product"
        )
    if act == "ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS":
        if kind != "CATEGORY" or grain != "PLAUSIBLE_BUT_REQUIRES_SYNTHESIS":
            raise ValidationError(
                f"{s}: an exploratory category hypothesis needs a category and synthesis"
            )
        ex = c.get("exploratory_category_hypothesis", {})
        if not ex.get("adopted") or not str(ex.get("statement", "")).strip():
            raise ValidationError(f"{s}: exploratory hypothesis with no adopted statement")
    if act == "REQUIRES_NARROWER_SUBJECT_DISCOVERY" and (
        kind in PRODUCT_LIKE or grain != "TOO_BROAD_TO_BE_ACTIONABLE"
    ):
        raise ValidationError(f"{s}: narrowing required without a too-broad category")
    if grain == "TOO_BROAD_TO_BE_ACTIONABLE" and act in SELECTABLE_GRAINS:
        raise ValidationError(f"{s}: too broad and selectable at once")
    if grain == "NOT_ESTABLISHED" and act != "NOT_ACTIONABLE":
        raise ValidationError(f"{s}: no established intervention and still actionable")
    if c["product_relevance"] == "UNKNOWN" and act == "ACTIONABLE_AT_CURRENT_GRAIN":
        raise ValidationError(f"{s}: actionable with unknown product relevance")


def _dominates(x: dict, y: dict, fields: list[str]) -> bool:
    better = False
    for field in fields:
        scale = FORMABILITY if field == "HYPOTHESIS_FORMABILITY" else INFORMATION
        rx, ry = _rank(scale, x["ordinal"][field], field), _rank(scale, y["ordinal"][field], field)
        if rx < ry:
            return False
        better |= rx > ry
    return better


def _check_dominance_and_vetoes(record: dict, candidates: dict[str, dict]) -> None:
    dominance = record["dominance"]
    fields = dominance["fields"]
    for required in (
        "EVIDENCE_BREADTH",
        "SCORABLE_BREADTH",
        "COUNTING_DIMENSION_DIVERSITY",
        "SOURCE_DIVERSITY",
        "COMMERCIAL_INFORMATION",
        "PROBLEM_INFORMATION",
        "SEMANTIC_SPECIFICITY",
        "HYPOTHESIS_FORMABILITY",
    ):
        if required not in fields:
            raise ValidationError(f"dominance ignores {required}")
    computed: dict[str, str] = {}
    for s, c in candidates.items():
        for t, o in candidates.items():
            if t != s and _dominates(o, c, fields):
                computed.setdefault(s, t)
    frontier = sorted(s for s in candidates if s not in computed)
    if sorted(dominance["PARETO_FRONTIER"]) != frontier:
        raise ValidationError(f"the recorded frontier is not the computed {frontier}")
    if sorted(dominance["DOMINATED_CANDIDATES"]) != sorted(computed):
        raise ValidationError(f"the recorded dominated set is not the computed {sorted(computed)}")
    for s, by in dominance["dominated_by"].items():
        if not _dominates(candidates[by], candidates[s], fields):
            raise ValidationError(f"{s} recorded as dominated by {by}, which does not dominate it")
    for s, c in candidates.items():
        state = "DOMINATED" if s in computed else "FRONTIER"
        if c["dominance_state"] != state:
            raise ValidationError(f"{s}: dominance state {c['dominance_state']}, computed {state}")
        if (
            state == "DOMINATED"
            and c.get("dominated_by") != computed.get(s)
            and not _dominates(candidates[c.get("dominated_by", s)], c, fields)
        ):
            raise ValidationError(f"{s}: dominated_by names a non-dominator")
        if c["veto_state"] not in ("VETOED", "NOT_VETOED"):
            raise ValidationError(f"{s}: veto state {c['veto_state']!r}")
        if c["veto_state"] == "VETOED" and not str(c.get("veto_reason", "")).strip():
            raise ValidationError(f"{s}: vetoed with no reason")
        if c["veto_state"] == "NOT_VETOED" and str(c.get("veto_reason", "")).strip():
            raise ValidationError(f"{s}: not vetoed with a veto reason")
        # section 19: what MUST be vetoed, and what must not be vetoed for.
        if not c["hypothesis_formable"] and c["veto_state"] != "VETOED":
            raise ValidationError(f"{s}: not formable and not vetoed")
        if not c["counting_dimensions"] and c["veto_state"] != "VETOED":
            raise ValidationError(f"{s}: no decision-relevant dimension and not vetoed")
        if c["actionable_grain"] not in SELECTABLE_GRAINS and c["veto_state"] != "VETOED":
            raise ValidationError(f"{s}: not at a selectable grain and not vetoed")
        reason = str(c.get("veto_reason", "")).lower()
        if (
            c["veto_state"] == "VETOED"
            and c["hypothesis_formable"]
            and c["counting_dimensions"]
            and c["actionable_grain"] in SELECTABLE_GRAINS
            and "egress" in reason
        ):
            raise ValidationError(f"{s}: vetoed solely for an egress that is not assessed")
    vetoed = sorted(s for s, c in candidates.items() if c["veto_state"] == "VETOED")
    if sorted(dominance["VETOED_CANDIDATES"]) != vetoed:
        raise ValidationError("the vetoed list disagrees with the candidates")


def _check_outcome(record: dict, candidates: dict[str, dict]) -> None:
    outcome = record["primary_outcome"]
    if outcome not in OUTCOMES:
        raise ValidationError(f"primary outcome {outcome!r} is not one of the four")
    selected = record["selected_subject"]
    best_packet = record["best_held_evidence_packet"]
    best_candidate = record["best_second_opportunity_candidate"]
    if best_packet not in candidates:
        raise ValidationError("the best held evidence packet is not a candidate")
    if candidates[best_packet]["dominance_state"] != "FRONTIER":
        raise ValidationError("the best held evidence packet is dominated")
    if best_packet != best_candidate and not str(record["why_they_differ"]).strip():
        raise ValidationError("best packet and best candidate differ with no reason")
    if best_candidate != selected:
        raise ValidationError("the best second-Opportunity candidate is not the selected subject")
    egress = record["egress"]
    for key in ("decided_here", "granted", "denied", "source_review_appended"):
        if egress[key]:
            raise ValidationError(f"egress {key}: the operator's question was answered here")
    needs_review = not candidates[best_packet]["egress_eligible"] or (
        selected is not None and not candidates[selected]["egress_eligible"]
    )
    if egress["EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS"] != needs_review:
        raise ValidationError("EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS disagrees with eligibility")
    next_title = str(record["recommended_next_mission"]["title"]).lower()
    if outcome == "SECOND_OPPORTUNITY_CANDIDATE_SELECTED":
        if selected is None or selected not in candidates:
            raise ValidationError("selected outcome with no selected candidate")
        c = candidates[selected]
        if record["selected_subject_scope"] != c["subject_scope"]:
            raise ValidationError("the selected scope is not the candidate's")
        if record["selected_packet_id"] != c["packet_id"]:
            raise ValidationError("the selected packet id is not the candidate's")
        if c["dominance_state"] != "FRONTIER" or c["veto_state"] != "NOT_VETOED":
            raise ValidationError("the selected candidate is dominated or vetoed")
        if not c["hypothesis_formable"] or not c["counting_dimensions"]:
            raise ValidationError("the selected candidate is not formable")
        if c["actionable_grain"] not in SELECTABLE_GRAINS:
            raise ValidationError("the selected candidate is not at an actionable grain")
        basis = str(record["selection_basis"]).lower()
        if "1.79" in basis or "mission 1.79" in basis or "1.76" in basis:
            raise ValidationError("selected because an earlier mission mentioned it")
        if not c["egress_eligible"] and "egress review" not in next_title:
            raise ValidationError("selected with egress unassessed and no egress review next")
        if c["egress_eligible"] and "egress review" in next_title:
            raise ValidationError("an egress review recommended for an eligible packet")
    else:
        if selected is not None or record["selected_packet_id"] is not None:
            raise ValidationError("a subject selected under a non-selecting outcome")
        if any(
            c["veto_state"] == "NOT_VETOED" and c["dominance_state"] == "FRONTIER"
            for c in candidates.values()
        ):
            raise ValidationError("an unvetoed frontier candidate exists and none was selected")
    narrowing = record.get("narrowing")
    needs_narrowing = [
        s
        for s, c in candidates.items()
        if c["actionable_grain"] == "REQUIRES_NARROWER_SUBJECT_DISCOVERY"
    ]
    if outcome == "SECOND_OPPORTUNITY_REQUIRES_SUBJECT_NARROWING":
        if not needs_narrowing:
            raise ValidationError("narrowing outcome with no candidate requiring narrowing")
        if not narrowing or narrowing["dominant_category"] not in needs_narrowing:
            raise ValidationError("the narrowing target does not require narrowing")
        if narrowing["acquisition_required"]:
            raise ValidationError("narrowing recorded as needing acquisition; held data only")
        dist = candidates[narrowing["dominant_category"]].get("held_class_distribution", {})
        if len(dist.get("top_cpv_classes", {})) < 2:
            raise ValidationError("narrowing proposed over a category with one held class")
        if "egress review" in next_title:
            raise ValidationError("egress review recommended before the subject exists")
    if outcome == "NO_HELD_SUBJECT_AT_ACTIONABLE_OPPORTUNITY_GRAIN":
        if needs_narrowing:
            raise ValidationError("no-subject outcome while a category could be narrowed")
        if not any(w in next_title for w in ("source", "market", "strategic")):
            raise ValidationError(
                "no-subject outcome without a return to source or market planning"
            )
    if outcome == "SECOND_OPPORTUNITY_CANDIDATE_SELECTION_REQUIRES_SEMANTIC_DECISION":
        sd = record.get("semantic_decision") or {}
        if sd.get("candidate") not in candidates or not str(sd.get("question", "")).strip():
            raise ValidationError("semantic decision outcome names no candidate or no question")
    for c in candidates.values():
        dist = c.get("held_class_distribution")
        if dist:
            if sum(dist["notice_classes"].values()) != dist["notices_held"]:
                raise ValidationError(
                    f"{c['subject_key']}: notice classes do not sum to the held count"
                )
            if any(v > dist["notices_held"] for v in dist.get("top_cpv_classes", {}).values()):
                raise ValidationError(f"{c['subject_key']}: a class larger than the corpus")
    rep = record["representation_check"]
    if rep["transmitted"] or rep["model_called"]:
        raise ValidationError("the representation check transmitted something")
    for s, r in rep["packets"].items():
        if s not in candidates or r["violations"] != 0:
            raise ValidationError(
                f"representation recorded with violations or for a non-candidate {s}"
            )
        if candidates[s]["representation_constructible_without_egress"] is not True:
            raise ValidationError(f"{s}: representation checked and not recorded constructible")


def _check_nothing_moved(record: dict, reconciliation: dict) -> None:
    after = reconciliation["counters"]["after"]
    state = record["current_state"]
    for key in (
        "opportunities",
        "opportunity_revisions",
        "opportunity_evidence_links",
        "reliability_assessments",
        "independence_groups",
        "embeddings",
        "scores_table",
    ):
        if state[key] != after[key]:
            raise ValidationError(
                f"current_state.{key} is {state[key]}, the reconciled deployment says {after[key]}"
            )
    if state["total_evidence"] != after["evidence"]:
        raise ValidationError("the Evidence count moved")
    if (
        state["current_revision_number"]
        != reconciliation["revision_2_applied"]["revision_2_number"]
    ):
        raise ValidationError("the current revision is not revision 2")
    if state["current_revision_id"] != reconciliation["revision_2_applied"]["revision_2_id"]:
        raise ValidationError("the current revision id is not revision 2's")
    if state["opportunities"] != 1:
        raise ValidationError("a second Opportunity exists")
    hot = sorted(k for k, v in record["mission_accounting"].items() if v != 0)
    if hot:
        raise ValidationError(f"mission accounting is not zero on {hot}")
    for key in (
        "api_calls",
        "raw_records_created",
        "model_calls",
        "opportunities_created",
        "opportunity_revisions_created",
        "reliability_assessments_created",
        "scores_persisted",
        "source_reviews_appended",
        "canonical_research_mutations",
    ):
        if key not in record["mission_accounting"]:
            raise ValidationError(f"mission accounting does not name {key}")


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
    record = _load(SELECTION)
    preparation = _load(PREPARATION)
    reconciliation = _load(RECONCILIATION)
    rules = _load(SCOPE_RULES)
    registry = _load(SUBJECT_REGISTRY)
    try:
        if record["measured_from"]["preparation_record"] != f"docs/data/{PREPARATION.name}":
            raise ValidationError("the record does not name the current preparation")
        packets = _universe(record, preparation, reconciliation)
        rows = {r["evidence_id"]: r for r in preparation["rows"]}
        assessments = {
            a["assessment_id"]: a for a in reconciliation["revision_1_audit"]["why_stale"]
        }
        groups = reconciliation["counters"]["after"]["independence_groups"]
        candidates = {c["subject_key"]: c for c in record["candidates"]}
        for s, c in candidates.items():
            _check_candidate_facts(c, packets[s], rows, assessments, rules, registry)
            _check_ordinals(c, packets[s], rows, groups)
            _check_grain(c)
        _check_dominance_and_vetoes(record, candidates)
        _check_outcome(record, candidates)
        _check_nothing_moved(record, reconciliation)
        _check_the_parked_arc(record)
    except (KeyError, TypeError, IndexError, StopIteration, AttributeError) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return record, preparation, reconciliation


# ------------------------------------------------------------------------- render


def render(record: dict) -> str:
    lines = [
        "# Which held subject is the second-Opportunity candidate?",
        "",
        f"Generated from `{SELECTION.name}`. Do not edit by hand.",
        "",
        f"**{record['primary_outcome']}** — selected `{record['selected_subject']}`; best held evidence "
        f"packet `{record['best_held_evidence_packet']}`; best second-Opportunity candidate "
        f"`{record['best_second_opportunity_candidate']}`; next "
        f"{record['recommended_next_mission']['id']} {record['recommended_next_mission']['title']}.",
        "",
        record["selection_basis"],
        "",
        "## Candidates",
        "",
        "| subject | scope | rows | scorable | counting dimensions | reliabilities | formable | egress | intervention grain | actionable grain | dominance | veto |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in record["candidates"]:
        rel = ", ".join(f"{k}: {v}" for k, v in c["reliability_distribution"].items())
        lines.append(
            f"| `{c['subject_key']}` | {c['subject_scope']} | {c['evidence_rows']} | {c['scorable_rows']} "
            f"| {', '.join(c['counting_dimensions']) or 'none'} | {rel} | {c['hypothesis_formable']} "
            f"| {c['egress_state']} | `{c['product_intervention_grain']}` | `{c['actionable_grain']}` "
            f"| {c['dominance_state']} | **{c['veto_state']}** |"
        )
    lines += [
        "",
        "## Ordinal fields",
        "",
        "| subject | " + " | ".join(ORDINAL_FIELDS) + " |",
        "|---|" + "---|" * len(ORDINAL_FIELDS),
    ]
    for c in record["candidates"]:
        lines.append(
            f"| `{c['subject_key']}` | "
            + " | ".join(c["ordinal"][f] for f in ORDINAL_FIELDS)
            + " |"
        )
    dominance = record["dominance"]
    lines += [
        "",
        f"Frontier {dominance['PARETO_FRONTIER']}; dominated {dominance['DOMINATED_CANDIDATES']}; vetoed "
        f"{dominance['VETOED_CANDIDATES']}.",
        "",
        dominance["frontier_note"],
        "",
        "## What division 92 establishes, and does not",
        "",
    ]
    ted = next(c for c in record["candidates"] if c["subject_key"] == "ted-eu:CPV-division:92")
    lines += [
        f"- **Establishes.** {ted['establishes']}",
        f"- **Does not establish.** {ted['does_not_establish']}",
        f"- **A synthesis could say.** {ted['what_a_synthesis_could_say']}",
        f"- **It could not say.** {ted['what_it_could_not_say']}",
        "",
        "## Egress",
        "",
        f"EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS: **{record['egress']['EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS']}**. "
        f"{record['egress']['ted_eu_state']}. Decided here: {record['egress']['decided_here']}. "
        f"{record['egress']['why_selection_does_not_need_it']}",
        "",
        "## Narrowing",
        "",
        f"{record['narrowing']['why_narrowing_is_possible_from_held_data']} {record['narrowing']['what_narrowing_requires']}"
        if record.get("narrowing")
        else "No narrowing proposed.",
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
        print(f"REFUSED  second-Opportunity candidate selection: {error}")
        return 1

    text = render(record)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its record")
            return 1
        print("ok       the second-Opportunity candidate selection matches its record")
        return 0

    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(f"selected {record['selected_subject']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
