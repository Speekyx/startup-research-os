"""Render and validate the procurement subject-grain narrowing (Mission 1.81).

A narrowing is a decision record over held records, and the gate holds it to the records
it claims to have read: the per-notice audit of the held division-92 corpus, the derivation
run and re-run records, the v3 preparation, the reconciliation record, the reviewed scope
rules and the extractor's own source. It refuses:

    A CENSUS THAT IS NOT THE AUDIT'S. Held notices, notice classes, windows, code
    cardinality, value presence, currencies and per-group membership are recomputed from
    the audit; a primary/additional status the held record does not carry is not invented,
    and a membership model that needs one is refused.

    A COHORT CHOSEN AFTER SEEING A VALUE, OR DROPPED FOR BEING SMALL. Every group with a
    held member appears; value-missing notices stay in the membership; every derived cohort
    is the run record's, at or above the procedure's own floor, in one currency and one
    notice class; refused cohorts are the re-run record's.

    DIVISION EVIDENCE REASSIGNED TO A CHILD. Every division Signal spans several groups; the
    derivation model is a re-derivation from held normalized records, and no division claim
    is copied onto a child.

    A RELIABILITY COPIED ONTO A SCOPE IT DOES NOT MATCH. Every new row's resolution is the
    preparation's, bound to an assessment the reconciliation names, and no scope was
    broadened, narrowed or created.

    A NARROWER CATEGORY READ AS ACTIONABLE. The re-selection runs under the Mission 1.80
    gate's own checks over the v3 preparation: a bare code with no held label is not at a
    selectable grain, a category is not a product, and no candidate is selected because it
    moved one level down.

    ANYTHING ELSE MOVED. RawRecords, NormalizedRecords, assessments, independence groups,
    Opportunities, revisions, links, source reviews, scores and embeddings unchanged; v1 and
    v2 preparations byte-identical; the second run persisted nothing; the parked arc intact.

    uv run python infrastructure/scripts/render_procurement_subject_grain_narrowing.py
    uv run python infrastructure/scripts/render_procurement_subject_grain_narrowing.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
SCRIPTS = ROOT / "infrastructure" / "scripts"

RECORD = DATA / "procurement-subject-grain-narrowing-v1.json"
RENDERED = DATA / "procurement-subject-grain-narrowing-v1.md"
AUDIT = DATA / "procurement-division-92-notice-audit-v1.json"
RUN = DATA / "procurement-grain-derivation-run-v1.json"
RERUN = DATA / "procurement-grain-derivation-rerun-v1.json"
PREPARATION_V1 = DATA / "opportunity-preparation-v1.json"
PREPARATION_V2 = DATA / "opportunity-preparation-v2.json"
PREPARATION_V3 = DATA / "opportunity-preparation-v3.json"
RECONCILIATION = DATA / "opportunity-reliability-reconciliation-v1.json"
SCOPE_RULES = DATA / "observation-scope-rules-v1.json"
SUBJECT_REGISTRY = DATA / "canonical-subject-registry-v1.json"
SELECTION_V1 = DATA / "second-opportunity-candidate-selection-v1.json"
EXTRACTOR = (
    ROOT
    / "services"
    / "nlp"
    / "python"
    / "sros_nlp"
    / "extractors"
    / "procurement_value_contrast.py"
)
SELECTION_GATE = SCRIPTS / "render_second_opportunity_candidate_selection.py"

OUTCOMES = (
    "PROCUREMENT_NARROW_SUBJECT_CANDIDATE_SELECTED",
    "PROCUREMENT_NARROWING_REQUIRES_DEEPER_CPV_GRAIN",
    "PROCUREMENT_NARROWING_PRODUCED_NO_FORMABLE_PACKET",
    "PROCUREMENT_NARROWING_RELIABILITY_SCOPE_GAP",
    "PROCUREMENT_NARROWING_REQUIRES_DERIVATION_ARCHITECTURE_DECISION",
    "PROCUREMENT_SUBJECT_MEMBERSHIP_AMBIGUOUS",
)
RESELECTION_OF = {
    "PROCUREMENT_NARROW_SUBJECT_CANDIDATE_SELECTED": "SECOND_OPPORTUNITY_CANDIDATE_SELECTED",
    "PROCUREMENT_NARROWING_REQUIRES_DEEPER_CPV_GRAIN": "SECOND_OPPORTUNITY_REQUIRES_SUBJECT_NARROWING",
    "PROCUREMENT_NARROWING_PRODUCED_NO_FORMABLE_PACKET": "NO_HELD_SUBJECT_AT_ACTIONABLE_OPPORTUNITY_GRAIN",
    "PROCUREMENT_NARROWING_RELIABILITY_SCOPE_GAP": "NO_HELD_SUBJECT_AT_ACTIONABLE_OPPORTUNITY_GRAIN",
    "PROCUREMENT_NARROWING_REQUIRES_DERIVATION_ARCHITECTURE_DECISION": (
        "SECOND_OPPORTUNITY_CANDIDATE_SELECTION_REQUIRES_SEMANTIC_DECISION"
    ),
    "PROCUREMENT_SUBJECT_MEMBERSHIP_AMBIGUOUS": (
        "SECOND_OPPORTUNITY_CANDIDATE_SELECTION_REQUIRES_SEMANTIC_DECISION"
    ),
}
DIVISION = "92"
DETAILED = "source_reported_procurement_value_contrast"
WITNESSED = "source_published_classification_value_contrast_witnessed"
FORBIDDEN_IN_STATEMENTS = ("market", "demand", "willingness", "spend", "buyer", "customer", "need")


class ValidationError(Exception):
    pass


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _selection_gate():
    spec = importlib.util.spec_from_file_location("selection_gate", SELECTION_GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None  # noqa: S101 - importlib contract
    spec.loader.exec_module(module)
    return module


def _depth(code: str) -> int:
    return len(code.rstrip("0"))


def _extractor_constants() -> tuple[dict[int, str], int]:
    """CPV_LEVELS and MINIMUM_COHORT_MEMBERS, read off the extractor's AST."""
    tree = ast.parse(EXTRACTOR.read_text(encoding="utf-8"))
    levels: dict[int, str] | None = None
    minimum: int | None = None
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target, value = node.target.id, node.value
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            target, value = node.targets[0].id, node.value
        if target == "CPV_LEVELS" and isinstance(value, ast.Dict):
            levels = {
                int(k.value): str(v.value)
                for k, v in zip(value.keys, value.values, strict=True)
                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)
            }
        if target == "MINIMUM_COHORT_MEMBERS" and isinstance(value, ast.Constant):
            minimum = int(value.value)
    if levels is None or minimum is None:
        raise ValidationError("the extractor no longer states CPV_LEVELS or MINIMUM_COHORT_MEMBERS")
    return levels, minimum


# ------------------------------------------------------------------------- checks


def _check_token_and_level(record: dict) -> None:
    levels, minimum = _extractor_constants()
    token = record["cpv_token"]
    grain = token["CPV_NARROWING_LEVEL"]
    if grain not in levels or levels[grain] != token["CPV_NARROWING_LEVEL_NAME"]:
        raise ValidationError(
            f"level {grain} is named {token['CPV_NARROWING_LEVEL_NAME']!r}; the extractor names it "
            f"{levels.get(grain)!r}"
        )
    if grain <= 2:
        raise ValidationError("narrowing at or above the division is not a narrowing")
    if token["check_digit_present"] or token["label_held"]:
        raise ValidationError("the token carries a check digit or a label the held records do not")
    if not token["CPV_IDENTITY_STABLE"]:
        raise ValidationError("an unstable identity is not a subject")
    if record["derivation"]["grains_accepted"] != {str(k): v for k, v in levels.items()}:
        raise ValidationError("the grains the record says are accepted are not the extractor's")
    if record["derivation"]["MINIMUM_REQUIRED_BY_PROCEDURE"] != minimum:
        raise ValidationError(
            f"the record's minimum {record['derivation']['MINIMUM_REQUIRED_BY_PROCEDURE']} is not the "
            f"procedure's {minimum}"
        )
    if record["derivation"]["parameters"].get("cpv_grain") != grain:
        raise ValidationError("the derivation parameters do not name the narrowing level")


def _check_census(record: dict, audit: dict) -> list[dict]:
    notices = audit["notices"]
    census = record["census"]
    if audit["division"] != DIVISION or census["DIVISION_92_HELD_NOTICES"] != len(notices):
        raise ValidationError("the held-notice count is not the audit's")
    classes = Counter(n["notice_type"] for n in notices)
    if census["CONTRACT_NOTICE_COUNT"] != classes.get("CONTRACT_NOTICE", 0):
        raise ValidationError("CONTRACT_NOTICE_COUNT is not the audit's")
    if census["CONTRACT_AWARD_NOTICE_COUNT"] != classes.get("CONTRACT_AWARD_NOTICE", 0):
        raise ValidationError("CONTRACT_AWARD_NOTICE_COUNT is not the audit's")
    if census["acquisition_windows"] != dict(
        sorted(Counter(n["acquisition_window"] for n in notices).items())
    ):
        raise ValidationError("the window split is not the audit's")
    cardinality = Counter(len(n["cpv_codes"]) for n in notices)
    if census["NOTICE_CPV_CARDINALITY_DISTRIBUTION"] != {
        str(k): v for k, v in sorted(cardinality.items())
    }:
        raise ValidationError("the CPV cardinality distribution is not the audit's")
    if census["MULTI_CPV_NOTICES"] != sum(v for k, v in cardinality.items() if k > 1):
        raise ValidationError("the multi-CPV notice count is not the audit's")
    if census["single_division_notices"] != sum(1 for n in notices if n["single_division"]):
        raise ValidationError("the single-division count is not the audit's")
    if census["TOTAL_VALUE_present"] != sum(1 for n in notices if n["total_value_present"]):
        raise ValidationError("the value-present count is not the audit's")
    if census["TOTAL_VALUE_missing"] != sum(1 for n in notices if not n["total_value_present"]):
        raise ValidationError("the value-missing count is not the audit's")
    if any(n["primary_or_additional_status"] != "NOT_ESTABLISHED_BY_HELD_RECORD" for n in notices):
        raise ValidationError(
            "the audit claims a primary/additional status the record does not carry"
        )
    if census["PRIMARY_OR_ADDITIONAL_CPV_STATUS"] != "UNAVAILABLE":
        raise ValidationError("a primary/additional status was invented")
    return notices


def _check_membership(record: dict, notices: list[dict]) -> dict[str, int]:
    membership = record["membership"]
    tally = Counter(n["group_membership"] for n in notices)
    if membership["MEMBERSHIP_MODEL_SELECTED"] != "C4_REFUSE_AMBIGUOUS_NOTICE":
        raise ValidationError(
            "a membership model that assigns a multi-CPV notice to a cohort was selected while the "
            "held record establishes no primary status"
        )
    if membership["models_evaluated"]["C1_PRIMARY_CPV_ONLY"]["verdict"] == "SELECTED":
        raise ValidationError("primary CPV status invented")
    if membership["multi_membership_allowed"] or membership["deduplicated_to_sum_to_177"]:
        raise ValidationError("multi-membership or a deduplication to make the counts sum")
    groups = membership["tally_at_group_grain"]["group_specified"]
    for prefix, count in groups.items():
        if tally.get(prefix, 0) != count:
            raise ValidationError(
                f"group {prefix}: the record says {count} members, the audit {tally.get(prefix, 0)}"
            )
    for key in ("AMBIGUOUS_ACROSS_DIVISIONS", "AMBIGUOUS_ACROSS_GROUPS", "UNSPECIFIED_AT_GROUP"):
        if membership["tally_at_group_grain"][key] != tally.get(key, 0):
            raise ValidationError(f"{key} is not the audit's")
    if membership["AMBIGUOUS_MEMBERSHIP_NOTICES"] != tally.get(
        "AMBIGUOUS_ACROSS_DIVISIONS", 0
    ) + tally.get("AMBIGUOUS_ACROSS_GROUPS", 0):
        raise ValidationError("the ambiguous count is not the audit's")
    audited_groups = {k for k in tally if k[:2] == DIVISION and k.isdigit()}
    if set(groups) < audited_groups:
        raise ValidationError(
            f"groups with held members are missing from the tally: {sorted(audited_groups - set(groups))}"
        )
    return {k: v for k, v in tally.items() if k in audited_groups}


def _check_cohorts(
    record: dict, notices: list[dict], run: dict, rerun: dict, v3: dict, held_groups: dict[str, int]
) -> None:
    minimum = record["derivation"]["MINIMUM_REQUIRED_BY_PROCEDURE"]
    cohorts = {c["CPV_ID"]: c for c in record["cohorts"]}
    if set(cohorts) != set(held_groups):
        raise ValidationError(
            f"cohorts {sorted(set(cohorts) ^ set(held_groups))} are dropped or invented against the audit's groups"
        )
    signals_by_group: dict[str, list[dict]] = {}
    for s in run["signals"]:
        if s["classification_level"] != record["cpv_token"]["CPV_NARROWING_LEVEL_NAME"]:
            raise ValidationError(f"signal {s['signal_id'][:8]} is not at the narrowing level")
        signals_by_group.setdefault(s["classification_level_code"], []).append(s)
    refused_by_group: dict[str, list[dict]] = {}
    for w in rerun["windows"]:
        for c in w["cohorts"]:
            if c["status"] == "REFUSED":
                refused_by_group.setdefault(c["cpv_prefix"], []).append(c)
    packets = {p["subject"]: p for p in v3["packets"]}
    for prefix, c in cohorts.items():
        ns = [n for n in notices if n["group_membership"] == prefix]
        if c["HELD_NOTICE_COUNT"] != len(ns):
            raise ValidationError(f"{prefix}: held notice count is not the audit's")
        if c["NOTICE_TYPES"] != dict(Counter(n["notice_type"] for n in ns)):
            raise ValidationError(f"{prefix}: notice types are not the audit's")
        present = sum(1 for n in ns if n["total_value_present"])
        if c["VALUE_PRESENT_COUNT"] != present or c["VALUE_MISSING_COUNT"] != len(ns) - present:
            raise ValidationError(f"{prefix}: value counts are not the audit's")
        if (
            not c["value_missing_notices_kept_in_membership"]
            or not c["MEMBERSHIP_COMPLETE_WITHIN_HELD_CORPUS"]
        ):
            raise ValidationError(
                f"{prefix}: value-missing notices removed, or membership incomplete"
            )
        if c["AMBIGUOUS_MEMBERSHIP_COUNT"] != 0:
            raise ValidationError(f"{prefix}: an ambiguous notice was assigned to the cohort")
        # notices per class prefix, not codes: one notice may carry several codes of one class
        classes = Counter(
            p
            for n in ns
            for p in {k[:4] for k in n["cpv_codes"] if k.startswith(prefix) and _depth(k) >= 4}
        )
        if c["held_class_prefixes"] != {k: v for k, v in classes.most_common()}:
            raise ValidationError(f"{prefix}: held class prefixes are not the audit's")
        held_labels = [
            label
            for n in ns
            for code, label in zip(
                n["cpv_codes"], n.get("cpv_labels", [None] * len(n["cpv_codes"])), strict=True
            )
            if label and code.startswith(prefix)
        ]
        if c["LABEL_IF_HELD"] is not None and c["LABEL_IF_HELD"] not in held_labels:
            raise ValidationError(f"{prefix}: a label recorded as held that no held record carries")
        derived = signals_by_group.get(prefix, [])
        if c["SIGNALS_DERIVED"] != len(derived) or len(c["derived_cohorts"]) != len(derived):
            raise ValidationError(f"{prefix}: derived cohorts are not the run record's")
        by_id = {s["signal_id"]: s for s in derived}
        for d in c["derived_cohorts"]:
            s = by_id.get(d["signal_id"])
            if s is None:
                raise ValidationError(
                    f"{prefix}: cohort {d['signal_id'][:8]} is not a persisted signal"
                )
            if d["members"] != s["contributing_records"] or d["magnitude"] != s["magnitude"]:
                raise ValidationError(
                    f"{prefix}: cohort {d['signal_id'][:8]} members or magnitude differ"
                )
            if d["members"] < minimum:
                raise ValidationError(f"{prefix}: a cohort below the procedure's floor")
            if d["currency"] != s["currency"] or d["notice_class"] != s["notice_class"]:
                raise ValidationError(
                    f"{prefix}: cohort {d['signal_id'][:8]} currency or class differ"
                )
            if not all(
                k.startswith(prefix) or prefix.startswith(k.rstrip("0"))
                for k in s["classification_codes"]
            ):
                raise ValidationError(f"{prefix}: a signal whose codes are not under the group")
        refused = refused_by_group.get(prefix, [])
        if len(c["refused_cohorts"]) != len(refused):
            raise ValidationError(f"{prefix}: refused cohorts are not the re-run record's")
        for r in c["refused_cohorts"]:
            if r["members"] >= minimum or r["reason"] != "INSUFFICIENT_INPUT_OBSERVATIONS":
                raise ValidationError(f"{prefix}: a refusal that is not the procedure's floor")
        evidence = [e for s in derived for e in s["evidence"]]
        if c["EVIDENCE_DERIVED"] != len(evidence) or c["CLAIMS_DERIVED"] != len(
            {e["claim_id"] for e in evidence}
        ):
            raise ValidationError(f"{prefix}: claims or evidence derived are not the run record's")
        for e in evidence:
            statement = e["statement"].lower()
            if (
                f'{record["cpv_token"]["CPV_NARROWING_LEVEL_NAME"]} "{prefix}" (division "{DIVISION}")'
                not in e["statement"]
            ):
                raise ValidationError(
                    f"{prefix}: a statement that does not name the level and its division"
                )
            if any(w in statement for w in FORBIDDEN_IN_STATEMENTS):
                raise ValidationError(f"{prefix}: a statement carrying market vocabulary")
        packet = packets.get(c["COHORT_SUBJECT_KEY"])
        if derived and packet is None:
            raise ValidationError(f"{prefix}: signals derived and no v3 packet")
        if packet is not None:
            if c["packet_id"] != packet["packet_id"] or c["EVIDENCE_DERIVED"] != packet["size"]:
                raise ValidationError(f"{prefix}: the v3 packet is not the cohort's")
            if c["SCORABLE_EVIDENCE"] != packet["eligibility_counts"].get("ELIGIBLE_SCORING", 0):
                raise ValidationError(f"{prefix}: scorable evidence is not the preparation's")
            if sorted(c["COUNTING_DIMENSIONS"]) != sorted(packet["counting_dimensions"]):
                raise ValidationError(f"{prefix}: counting dimensions are not the preparation's")
            if c["formable"] != (packet["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"):
                raise ValidationError(f"{prefix}: formability is not the preparation's")
            if c["egress_state"] != packet["external_synthesis"]["availability"]:
                raise ValidationError(f"{prefix}: egress is not the preparation's")
        if c["INDEPENDENCE_STATE"] != "UNKNOWN" or c["PROVENANCE_SHAPES"] > 1:
            raise ValidationError(f"{prefix}: independence or provenance manufactured")
    if record["NARROW_COHORT_COUNT"] != sum(1 for c in cohorts.values() if c["SIGNALS_DERIVED"]):
        raise ValidationError("NARROW_COHORT_COUNT is not the number of groups with signals")


def _check_derivation(record: dict, run: dict, rerun: dict) -> None:
    d = record["derivation"]
    if d["DERIVATION_MODEL"] != "C_RE_DERIVE_FROM_HELD_NORMALIZED_RECORDS":
        raise ValidationError("division evidence reused or filtered onto a child subject")
    for key in ("A_REUSE_EXISTING_DIVISION_EVIDENCE", "B_FILTER_EXISTING_EVIDENCE"):
        if d["models_evaluated"][key]["verdict"] != "REFUSED":
            raise ValidationError(f"{key} not refused")
    if d["division_claims_copied_onto_children"] != 0:
        raise ValidationError("a division claim was copied onto a child")
    for sid, span in d["division_92_signals_span_several_groups"].items():
        if len(span["groups_spanned"]) < 2:
            raise ValidationError(
                f"division signal {sid} spans one group; reuse would have been possible and was not examined"
            )
    if d["NEW_SIGNAL_TYPE_CREATED"] or d["NEW_SIGNAL_TYPE_REQUIRED"]:
        raise ValidationError("a new signal type invented to make a candidate formable")
    if d["EXISTING_SIGNAL_TYPES_REUSED"] != ["procurement_value_contrast"]:
        raise ValidationError("the reused signal type is not the procurement contrast")
    if d["NEW_SIGNALS"] != len(run["signals"]) or d["NEW_EVIDENCE"] != run["evidence_rows"]:
        raise ValidationError("new signals or evidence are not the run record's")
    if d["NEW_CLAIMS"] != len(run["claims"]) or d["NEW_CLAIM_REVISIONS"] != len(run["claims"]):
        raise ValidationError("new claims or revisions are not the run record's")
    detailed = sum(
        1 for s in run["signals"] for e in s["evidence"] if e["proposition_kind"] == DETAILED
    )
    if (
        d["new_claims_detailed"] != detailed
        or d["new_claims_witnessed"] != len(run["claims"]) - detailed
    ):
        raise ValidationError("the detailed/witnessed split is not the run record's")
    if d["COHORTS_REFUSED_FOR_INSUFFICIENT_INPUT"] != sum(
        1 for w in rerun["windows"] for c in w["cohorts"] if c["status"] == "REFUSED"
    ):
        raise ValidationError("refused cohorts are not the re-run record's")
    if not d["membership_frozen_before_values"] or not d["generic_across_grains"]:
        raise ValidationError("membership after values, or a grain-specific procedure")
    if run["network_acquisitions"] != 0 or rerun["network_acquisitions"] != 0:
        raise ValidationError("an acquisition inside the derivation")
    for s in run["signals"]:
        if s["contributing_records"] < d["MINIMUM_REQUIRED_BY_PROCEDURE"]:
            raise ValidationError("a persisted signal below the floor")
        kinds = Counter(e["proposition_kind"] for e in s["evidence"])
        if kinds != Counter({DETAILED: 1, WITNESSED: 1}):
            raise ValidationError(
                f"signal {s['signal_id'][:8]} witnesses {dict(kinds)}, not one detailed and one broader claim"
            )


def _check_reliability(record: dict, v3: dict, reconciliation: dict) -> None:
    r = record["reliability"]
    assessments = {a["assessment_id"]: a for a in reconciliation["revision_1_audit"]["why_stale"]}
    rows = {x["evidence_id"]: x for x in v3["rows"]}
    group_keys = {c["COHORT_SUBJECT_KEY"] for c in record["cohorts"] if c["SIGNALS_DERIVED"]}
    packet_rows = [
        rows[e] for p in v3["packets"] if p["subject"] in group_keys for e in p["evidence_ids"]
    ]
    if r["new_evidence_rows"] != len(packet_rows) or len(r["rows"]) != len(packet_rows):
        raise ValidationError("the reliability rows are not the new packets' rows")
    for entry in r["rows"]:
        row = rows.get(entry["evidence_id"])
        if row is None:
            raise ValidationError(
                f"reliability row {entry['evidence_id'][:8]} is not a preparation row"
            )
        res = row["reliability_resolution"]
        if entry["RESOLVER_RESULT"] != res["outcome"]:
            raise ValidationError(
                f"{entry['evidence_id'][:8]}: resolver result is not the preparation's"
            )
        if res["outcome"] == "RESOLVED":
            a = assessments.get(res["assessment_id"])
            if a is None:
                raise ValidationError(
                    f"{entry['evidence_id'][:8]}: bound to an assessment the reconciliation does not name"
                )
            if (
                entry["RELIABILITY"] != a["reliability"]
                or entry["PROPOSITION_KIND"] != a["proposition_kind"]
            ):
                raise ValidationError(
                    f"{entry['evidence_id'][:8]}: a reliability copied onto a non-matching scope"
                )
            if (
                entry["assessment_id"] != res["assessment_id"]
                or a["source_id"] != entry["SOURCE_ID"]
            ):
                raise ValidationError(f"{entry['evidence_id'][:8]}: assessment or source disagree")
        elif entry["RELIABILITY"] is not None:
            raise ValidationError(f"{entry['evidence_id'][:8]}: a value without a resolution")
    if r["SCORABLE_NEW_EVIDENCE"] != sum(1 for x in packet_rows if x["scorable"]):
        raise ValidationError("scorable new evidence is not the preparation's")
    if r["NONSCORABLE_NEW_EVIDENCE"] != sum(1 for x in packet_rows if not x["scorable"]):
        raise ValidationError("non-scorable new evidence is not the preparation's")
    if r["scope_broadened"] or r["scope_narrowed"] or r["assessments_created"]:
        raise ValidationError("a reliability scope moved or an assessment was created")
    if r["assessments_applied"].keys() - assessments.keys():
        raise ValidationError("an assessment applied that the reconciliation does not name")


def _check_semantics(record: dict, run: dict) -> None:
    cur = record["currency_semantics"]
    if cur["cross_currency_contrast_performed"] or cur["fx_conversion_performed"]:
        raise ValidationError("a cross-currency contrast or an FX conversion")
    nt = record["notice_type_semantics"]
    if nt["CONTRACT_NOTICE_and_CONTRACT_AWARD_NOTICE_combined"]:
        raise ValidationError("notice classes combined without a contract basis")
    if not nt["contract_cited"].strip():
        raise ValidationError("notice-class separation cited to nothing")
    for s in run["signals"]:
        if s["magnitude_unit"] != s["currency"]:
            raise ValidationError(f"signal {s['signal_id'][:8]}: unit is not its currency")


def _check_preparation(record: dict, v2: dict, v3: dict) -> None:
    p = record["preparation"]
    if p["v2_untouched_sha256"] != _sha(PREPARATION_V2) or p["v1_untouched_sha256"] != _sha(
        PREPARATION_V1
    ):
        raise ValidationError("a historical preparation record was rewritten")
    if v2.get("mission") != "1.78" or v3.get("supersedes") != f"docs/data/{PREPARATION_V2.name}":
        raise ValidationError("v3 does not supersede v2, or v2 was rewritten as current")
    if (
        p["PREPARATION_VERSION_BEFORE"] != v2["artifact_version"]
        or p["PREPARATION_VERSION_AFTER"] != v3["artifact_version"]
    ):
        raise ValidationError("the preparation versions are not the records'")
    if p["packets"] != {
        "before": v2["totals"]["packets_built"],
        "after": v3["totals"]["packets_built"],
    }:
        raise ValidationError("packet counts are not the records'")
    if p["formable_packets"] != {
        "before": v2["totals"]["packets_formable"],
        "after": v3["totals"]["packets_formable"],
    }:
        raise ValidationError("formable counts are not the records'")
    division = next(
        (x for x in v3["packets"] if x["subject"] == f"ted-eu:CPV-division:{DIVISION}"), None
    )
    if division is None or not p["division_92_packet_retained"]:
        raise ValidationError("the parent division packet was deleted")
    v2_division = next(
        x for x in v2["packets"] if x["subject"] == f"ted-eu:CPV-division:{DIVISION}"
    )
    if division["size"] != v2_division["size"] or sorted(division["evidence_ids"]) != sorted(
        v2_division["evidence_ids"]
    ):
        raise ValidationError("the parent division packet's rows changed")
    if p["division_92_packet"]["size_after"] != division["size"]:
        raise ValidationError("the recorded division size is not v3's")
    group_subjects = sorted(x["subject"] for x in v3["packets"] if ":CPV-group:" in x["subject"])
    if sorted(p["new_packets"]) != group_subjects:
        raise ValidationError("the new packets are not v3's group packets")


def _check_reselection(
    record: dict, v3: dict, reconciliation: dict, rules: dict, registry: dict, notices: list[dict]
) -> None:
    gate = _selection_gate()
    sel = record["reselection"]
    if sel["measured_from"]["preparation_record"] != f"docs/data/{PREPARATION_V3.name}":
        raise ValidationError("the re-selection does not read the v3 preparation")
    packets = {p["subject"]: p for p in v3["packets"]}
    expected = {s for s in packets if s != "subject:docker"}
    universe = sel["candidate_universe"]
    if set(universe["subjects"]) != expected or universe["count"] != len(expected):
        raise ValidationError(
            f"the re-selection universe is not v3's non-docker packets: {sorted(set(universe['subjects']) ^ expected)}"
        )
    candidates = {c["subject_key"]: c for c in sel["candidates"]}
    if set(candidates) != expected:
        raise ValidationError("the re-selection candidates are not the universe")
    rows = {r["evidence_id"]: r for r in v3["rows"]}
    assessments = {a["assessment_id"]: a for a in reconciliation["revision_1_audit"]["why_stale"]}
    groups = reconciliation["counters"]["after"]["independence_groups"]
    cohorts = {c["COHORT_SUBJECT_KEY"]: c for c in record["cohorts"]}
    for s, c in candidates.items():
        if "+" in s or c["packet_id"] != packets[s]["packet_id"]:
            raise ValidationError(f"{s}: merged, or not the held packet")
        try:
            gate._check_candidate_facts(c, packets[s], rows, assessments, rules, registry)
            _check_ordinals(gate, c, packets[s], rows, groups)
            gate._check_grain(c)
        except gate.ValidationError as error:
            raise ValidationError(f"re-selection: {error}") from error
        if ":CPV-group:" in s:
            coh = cohorts.get(s)
            if coh is None:
                raise ValidationError(f"{s}: a group candidate with no cohort record")
            if (
                c["subject_type"] != "CATEGORY"
                or c.get("parent_subject") != f"ted-eu:CPV-division:{DIVISION}"
            ):
                raise ValidationError(f"{s}: a group is a CATEGORY within its division")
            if coh["LABEL_IF_HELD"] is None and c["actionable_grain"] in gate.SELECTABLE_GRAINS:
                raise ValidationError(f"{s}: a bare code with no held label read as actionable")
            if c["product_intervention_grain"] == "DIRECTLY_SUPPORTED":
                raise ValidationError(f"{s}: a category is not a product")
            dist = c["held_class_distribution"]
            ns = [n for n in notices if n["group_membership"] == s.rsplit(":", 1)[1]]
            if dist["notices_held"] != len(ns) or dist["notice_classes"] != dict(
                Counter(n["notice_type"] for n in ns)
            ):
                raise ValidationError(f"{s}: held class distribution is not the audit's")
            if dist["top_cpv_classes"] != coh["held_class_prefixes"]:
                raise ValidationError(f"{s}: top classes are not the cohort's held prefixes")
            if c["buyer_semantics"]["BUYER_FOR_PROPOSED_INTERVENTION"]:
                raise ValidationError(
                    f"{s}: a contracting authority read as a buyer for a future product"
                )
    try:
        gate._check_dominance_and_vetoes(sel, candidates)
        gate._check_outcome(sel, candidates)
        gate._check_the_parked_arc(sel)
    except gate.ValidationError as error:
        raise ValidationError(f"re-selection: {error}") from error
    # nothing moved, in this mission's own terms: the reconciled counters plus exactly the derivation
    after = reconciliation["counters"]["after"]
    state = sel["current_state"]
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
    if state["total_evidence"] != after["evidence"] + record["derivation"]["NEW_EVIDENCE"]:
        raise ValidationError("the Evidence count is not the reconciled count plus the derivation")
    if state["total_evidence"] != v3["totals"]["evidence_rows_inspected"]:
        raise ValidationError("the Evidence count is not v3's")
    if (
        state["current_revision_number"] != 2
        or state["current_revision_id"] != reconciliation["revision_2_applied"]["revision_2_id"]
    ):
        raise ValidationError("the docker revision moved")
    if state["opportunities"] != 1:
        raise ValidationError("a second Opportunity exists")
    if sel["primary_outcome"] != RESELECTION_OF[record["primary_outcome"]]:
        raise ValidationError(
            f"outcome {record['primary_outcome']} does not correspond to re-selection outcome {sel['primary_outcome']}"
        )
    if (
        sel["best_narrow_held_packet"] not in candidates
        or ":CPV-group:" not in sel["best_narrow_held_packet"]
    ):
        raise ValidationError("the best narrow packet is not a group candidate")
    if candidates[sel["best_narrow_held_packet"]]["dominance_state"] != "FRONTIER":
        raise ValidationError("the best narrow packet is dominated")
    if (
        record["selection"]["SELECTED_SUBJECT"] != sel["selected_subject"]
        or record["selection"]["value_used_to_select"]
    ):
        raise ValidationError(
            "the selection block disagrees with the re-selection, or a value selected it"
        )
    if sel["primary_outcome"] == "SECOND_OPPORTUNITY_REQUIRES_SUBJECT_NARROWING":
        targets = sel["narrowing"]["narrowing_targets"]
        if not targets or any(
            candidates[t]["actionable_grain"] != "REQUIRES_NARROWER_SUBJECT_DISCOVERY"
            for t in targets
        ):
            raise ValidationError("a narrowing target that does not require narrowing")
        if sel["narrowing"]["dominant_category"] not in targets:
            raise ValidationError("the dominant category is not a narrowing target")
        title = record["recommended_next_mission"]["title"].lower()
        if not any(w in title for w in ("semantic", "label")):
            raise ValidationError(
                "a deeper grain recommended without the semantic input the record says it needs"
            )
        if not record["information_gain_test"][
            "structural_splitting_terminates_only_at_leaf_codes"
        ]:
            raise ValidationError("the structural test recorded as terminating")


def _check_ordinals(gate, c: dict, packet: dict, rows: dict, groups: int) -> None:
    """Mission 1.80's ordinal recomputation, with the one refined rule: a CATEGORY one level
    below the scheme's coarsest reads MEDIUM specificity."""
    s = c["subject_key"]
    o = c["ordinal"]
    for field in gate.ORDINAL_FIELDS:
        if field not in o:
            raise ValidationError(f"{s}: ordinal {field} missing")
    for key in c:
        if any(k in key.lower() for k in gate.FORBIDDEN_NUMERIC_KEYS) and isinstance(
            c[key], int | float
        ):
            raise ValidationError(f"{s}: a numeric {key}; a priority is a tier, never a number")
    packet_rows = [rows[e] for e in packet["evidence_ids"]]
    scorable = sum(1 for r in packet_rows if r["scorable"])
    if c["subject_scope"] in ("PRODUCT", "GEOGRAPHY"):
        specificity = "HIGH"
    elif c["subject_scope"] == "CATEGORY" and c.get("cpv_level") not in (None, "division"):
        specificity = "MEDIUM"
    else:
        specificity = "LOW"
    expected = {
        "EVIDENCE_BREADTH": gate._breadth(packet["size"]),
        "SCORABLE_BREADTH": gate._scorable_breadth(scorable),
        "COUNTING_DIMENSION_DIVERSITY": gate._diversity(len(packet["counting_dimensions"])),
        "SOURCE_DIVERSITY": gate._diversity(len(packet["source_ids"])),
        "HYPOTHESIS_FORMABILITY": "YES" if c["hypothesis_formable"] else "NO",
        "NEW_ACQUISITION_REQUIRED": "NO" if c["hypothesis_formable"] else "YES",
        "PROVENANCE_DIVERSITY": "LOW" if c["provenance_shapes"] == 1 else "MEDIUM",
        "SEMANTIC_SPECIFICITY": specificity,
    }
    for field, value in expected.items():
        if o[field] != value:
            raise ValidationError(f"{s}: {field} is {o[field]}, the counts say {value}")
    commercial = set(c["counting_dimensions"]) & gate.COMMERCIAL
    if (not commercial and o["COMMERCIAL_INFORMATION"] != "NONE") or (
        commercial and o["COMMERCIAL_INFORMATION"] == "NONE"
    ):
        raise ValidationError(f"{s}: commercial information disagrees with the dimensions")
    if (
        "WILLINGNESS_TO_PAY" not in c["counting_dimensions"]
        and o["COMMERCIAL_INFORMATION"] == "HIGH"
    ):
        raise ValidationError(f"{s}: HIGH commercial information without willingness to pay")
    if not set(c["counting_dimensions"]) & gate.PROBLEM and o["PROBLEM_INFORMATION"] != "NONE":
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
        gate._rank(gate.YES_NO, o[field], f"{s}.{field}")
    gate._rank(gate.INFORMATION, o["OVERINTERPRETATION_RISK"], f"{s}.OVERINTERPRETATION_RISK")
    gate._rank(gate.INFORMATION + ["UNKNOWN"], o["PRODUCT_RELEVANCE"], f"{s}.PRODUCT_RELEVANCE")
    if c["product_relevance"] != o["PRODUCT_RELEVANCE"]:
        raise ValidationError(f"{s}: product relevance stated twice, differently")


def _check_counters(record: dict, reconciliation: dict, run: dict, rerun: dict) -> None:
    after_recon = reconciliation["counters"]["after"]
    counters = record["counters"]
    before, after, deltas = counters["before"], counters["after"], counters["deltas"]
    for key, recon_key in (
        ("raw_records", "raw_records"),
        ("normalized_records", "normalized_records"),
        ("signals", "signals"),
        ("claims", "claims"),
        ("claim_revisions", "claim_revisions"),
        ("evidence", "evidence"),
        ("reliability_assessments", "reliability_assessments"),
        ("independence_groups", "independence_groups"),
        ("opportunities", "opportunities"),
        ("opportunity_revisions", "opportunity_revisions"),
        ("opportunity_evidence_links", "opportunity_evidence_links"),
        ("source_reviews", "source_reviews"),
        ("scores_table", "scores_table"),
        ("embeddings", "embeddings"),
    ):
        if before[key] != after_recon[recon_key]:
            raise ValidationError(f"counters.before.{key} is not the reconciled deployment's")
    for key in (
        "raw_records",
        "normalized_records",
        "reliability_assessments",
        "independence_groups",
        "opportunities",
        "opportunity_revisions",
        "opportunity_evidence_links",
        "source_reviews",
        "embeddings",
    ):
        if after[key] != before[key] or deltas[key] != 0:
            raise ValidationError(f"{key} moved")
    if after["scores_table"] != "ABSENT":
        raise ValidationError("a scores table exists")
    expected = {
        "signals": len(run["signals"]),
        "claims": len(run["claims"]),
        "claim_revisions": len(run["claims"]),
        "evidence": run["evidence_rows"],
    }
    for key, delta in expected.items():
        if after[key] - before[key] != delta or deltas[key] != delta:
            raise ValidationError(
                f"{key} delta {after[key] - before[key]} is not the derivation's {delta}"
            )
    if not counters["IDEMPOTENT_SECOND_RUN"]:
        raise ValidationError("the second run is recorded as not idempotent")
    if (
        rerun["signals_persisted"] != 0
        or rerun["interpretation"]["claims_new"] != 0
        or rerun["interpretation"]["evidence_new"] != 0
    ):
        raise ValidationError("the second run created rows")
    if counters["second_run"] != {
        "signals_persisted": 0,
        "skipped_existing_witness": len(rerun["skipped_as_existing_witness"]),
        "claims_new": 0,
        "evidence_new": 0,
    }:
        raise ValidationError("the second-run figures are not the re-run record's")
    if len(rerun["skipped_as_existing_witness"]) != len(run["signals"]):
        raise ValidationError("the second run did not meet every persisted witness")
    acc = record["mission_accounting"]
    for key in (
        "api_calls",
        "ted_api_calls",
        "web_requests",
        "dataset_downloads",
        "raw_records_created",
        "normalized_records_created",
        "mailbox_reads",
        "outbound_messages",
        "globalping_calls",
        "model_calls",
        "embeddings",
        "reliability_assessments_created",
        "independence_groups_created",
        "opportunities_created",
        "opportunity_revisions_created",
        "opportunity_links_created",
        "source_reviews_appended",
        "scores_persisted",
    ):
        if acc[key] != 0:
            raise ValidationError(f"mission accounting is not zero on {key}")
    if (
        acc["signals_created"],
        acc["claims_created"],
        acc["claim_revisions_created"],
        acc["evidence_created"],
    ) != (
        expected["signals"],
        expected["claims"],
        expected["claim_revisions"],
        expected["evidence"],
    ):
        raise ValidationError("canonical creations are not the derivation's")
    imm = record["immutable"]
    if (
        imm["opportunities"] != 1
        or imm["docker_current_revision"] != 2
        or imm["opportunity_links"] != 14
    ):
        raise ValidationError("the docker Opportunity moved")
    if (
        imm["q1"]["CONSTRUCT_SELECTED"]
        or imm["q1"]["RUN_AUTHORIZED"]
        or not imm["q1"]["CLASS_SELECTED"]
    ):
        raise ValidationError("Q1 moved")
    egress = record["egress"]
    if (
        egress["decided_here"]
        or egress["source_review_appended"]
        or egress["TED_EGRESS_STATE"] != "NOT_ASSESSED"
    ):
        raise ValidationError("the ted-eu egress question was decided or moved")
    if record["primary_outcome"] not in OUTCOMES:
        raise ValidationError(
            f"primary outcome {record['primary_outcome']!r} is not one of the six"
        )
    if record["reselection_outcome"] != record["reselection"]["primary_outcome"]:
        raise ValidationError("the reselection outcome is stated twice, differently")


def validate() -> dict:
    record = _load(RECORD)
    audit = _load(AUDIT)
    run = _load(RUN)
    rerun = _load(RERUN)
    v2 = _load(PREPARATION_V2)
    v3 = _load(PREPARATION_V3)
    reconciliation = _load(RECONCILIATION)
    rules = _load(SCOPE_RULES)
    registry = _load(SUBJECT_REGISTRY)
    try:
        _check_token_and_level(record)
        notices = _check_census(record, audit)
        held_groups = _check_membership(record, notices)
        _check_cohorts(record, notices, run, rerun, v3, held_groups)
        _check_derivation(record, run, rerun)
        _check_reliability(record, v3, reconciliation)
        _check_semantics(record, run)
        _check_preparation(record, v2, v3)
        _check_reselection(record, v3, reconciliation, rules, registry, notices)
        _check_counters(record, reconciliation, run, rerun)
    except (KeyError, TypeError, IndexError, StopIteration, AttributeError) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return record


# ------------------------------------------------------------------------- render


def render(record: dict) -> str:
    census = record["census"]
    lines = [
        "# Narrowing the procurement subject from the division to the group",
        "",
        f"Generated from `{RECORD.name}`. Do not edit by hand.",
        "",
        f"**{record['primary_outcome']}** — re-selection `{record['reselection_outcome']}`; best narrow held "
        f"packet `{record['selection']['BEST_NARROW_HELD_PACKET']}`; selected `{record['selection']['SELECTED_SUBJECT']}`; "
        f"next {record['recommended_next_mission']['id']} {record['recommended_next_mission']['title']}.",
        "",
        record["outcome_fit"],
        "",
        "## The grain",
        "",
        f"Held token: {record['cpv_token']['CPV_HELD_TOKEN_FORMAT']}. Narrowing level {record['cpv_token']['CPV_NARROWING_LEVEL']} "
        f"({record['cpv_token']['CPV_NARROWING_LEVEL_NAME']}). {record['cpv_token']['naming_basis']}",
        "",
        "## The held corpus",
        "",
        f"{census['DIVISION_92_HELD_NOTICES']} held notices ({census['CONTRACT_NOTICE_COUNT']} CONTRACT_NOTICE, "
        f"{census['CONTRACT_AWARD_NOTICE_COUNT']} CONTRACT_AWARD_NOTICE), {census['MULTI_CPV_NOTICES']} carrying more than one CPV code, "
        f"{census['single_division_notices']} in one division, {census['TOTAL_VALUE_present']} with a paired TOTAL_VALUE. "
        f"Primary/additional status: {census['PRIMARY_OR_ADDITIONAL_CPV_STATUS']}. Membership model "
        f"{record['membership']['MEMBERSHIP_MODEL_SELECTED']}: {record['membership']['rule']}",
        "",
        "| group | held notices | notice types | values | derived cohorts | refused | signals | claims | evidence | scorable | formable | egress |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in record["cohorts"]:
        lines.append(
            f"| `{c['COHORT_SUBJECT_KEY']}` | {c['HELD_NOTICE_COUNT']} | {c['NOTICE_TYPES']} | {c['VALUE_PRESENT_COUNT']} "
            f"| {len(c['derived_cohorts'])} | {len(c['refused_cohorts'])} | {c['SIGNALS_DERIVED']} | {c['CLAIMS_DERIVED']} "
            f"| {c['EVIDENCE_DERIVED']} | {c['SCORABLE_EVIDENCE']} | {c['formable']} | {c['egress_state']} |"
        )
    d = record["derivation"]
    lines += [
        "",
        "## The derivation",
        "",
        f"{d['DERIVATION_MODEL']} through `{d['extractor']}` with parameters {d['parameters']}; floor "
        f"{d['MINIMUM_REQUIRED_BY_PROCEDURE']} from the procedure; {d['cohorts_derived']} cohorts derived, "
        f"{d['COHORTS_REFUSED_FOR_INSUFFICIENT_INPUT']} refused; {d['NEW_SIGNALS']} Signals, {d['NEW_CLAIMS']} Claims "
        f"({d['new_claims_detailed']} detailed, {d['new_claims_witnessed']} witnessed), {d['NEW_EVIDENCE']} Evidence, "
        f"{record['reliability']['SCORABLE_NEW_EVIDENCE']} scorable. {record['reliability']['why_the_existing_scopes_apply']}",
        "",
        "## Information gain",
        "",
        record["information_gain_test"]["finding"],
        "",
        "## Re-selection",
        "",
        f"{record['reselection']['selection_basis']}",
        "",
        f"Frontier {record['reselection']['dominance']['PARETO_FRONTIER']}; vetoed {record['reselection']['dominance']['VETOED_CANDIDATES']}.",
        "",
        f"Counters: signals {record['counters']['before']['signals']} to {record['counters']['after']['signals']}, claims "
        f"{record['counters']['before']['claims']} to {record['counters']['after']['claims']}, evidence "
        f"{record['counters']['before']['evidence']} to {record['counters']['after']['evidence']}; every other counter unchanged; "
        f"second run persisted {record['counters']['second_run']['signals_persisted']}.",
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
        record = validate()
    except ValidationError as error:
        print(f"REFUSED  procurement subject-grain narrowing: {error}")
        return 1
    text = render(record)
    if args.check:
        if not RENDERED.exists():
            print(f"DRIFT    {RENDERED.name} does not exist")
            return 1
        if RENDERED.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RENDERED.name} does not match its record")
            return 1
        print("ok       the procurement subject-grain narrowing matches its record")
        return 0
    RENDERED.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RENDERED.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
