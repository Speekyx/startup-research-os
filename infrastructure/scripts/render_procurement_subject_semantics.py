"""Render and validate the procurement subject semantics and class grain (Mission 1.82).

A semantic narrowing is a decision record over a frozen universe, a bounded first-party
retrieval and held records, and the gate holds it to all three: the lookup universe and its
digest, the vocabulary slice, the class derivation run and re-run records, the v4
preparation, the reconciliation record and the reviewed scope rules. It refuses:

    A UNIVERSE THAT MOVED. The frozen artifact must hash to the digest the record names,
    carry no labels, and be exactly the codes the production membership rule forms from held
    records. Every frozen code must have a semantic record and no concept may be recorded
    that the freeze does not name.

    A LABEL THAT IS NOT THE AUTHORITY'S. Every label comes from the recorded first-party
    register with a raw-response hash; a label inferred from a neighbouring code, recalled
    from Mission 1.80, or taken from a third party is refused, and so is a label used as
    subject identity.

    A DERIVATION SELECTED BY SEMANTICS. Every frozen class the procedure admits has its
    cohorts; a cohort below the procedure's own floor is refused rather than weakened;
    parent Signals are not copied into children; membership is the codes' and not the
    values'.

    A RELIABILITY OR A SCOPE THAT MOVED. Each new row's resolution is the preparation's,
    bound to an assessment the reconciliation names; no scope was widened and no assessment
    created.

    A NARROWER SUBJECT READ AS BETTER. Semantic coherence is a stated judgement over the
    official label and the held children, never attractiveness; a class defeats its group
    only where the recomputed dominance says so; a category is not a product; a selected
    subject is on the recomputed frontier, unvetoed, formable and at a selectable grain.

    ANYTHING ELSE MOVED. RawRecords, NormalizedRecords, assessments, independence groups,
    Opportunities, revisions, links, source reviews, scores and embeddings unchanged; v1, v2
    and v3 preparations byte-identical; the second run persisted nothing; egress undecided;
    the parked arc intact.

    uv run python infrastructure/scripts/render_procurement_subject_semantics.py
    uv run python infrastructure/scripts/render_procurement_subject_semantics.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

RECORD = DATA / "procurement-subject-semantics-class-grain-v1.json"
RENDERED = DATA / "procurement-subject-semantics-class-grain-v1.md"
UNIVERSE = DATA / "cpv-semantic-lookup-universe-v1.json"
VOCABULARY = DATA / "cpv-held-subject-vocabulary-v1.json"
VOCABULARY_MD = DATA / "cpv-held-subject-vocabulary-v1.md"
RUN = DATA / "procurement-class-grain-derivation-run-v1.json"
RERUN = DATA / "procurement-class-grain-derivation-rerun-v1.json"
GROUP_RUN = DATA / "procurement-grain-derivation-run-v1.json"
PREPARATION = {
    1: DATA / "opportunity-preparation-v1.json",
    2: DATA / "opportunity-preparation-v2.json",
    3: DATA / "opportunity-preparation-v3.json",
    4: DATA / "opportunity-preparation-v4.json",
}
RECONCILIATION = DATA / "opportunity-reliability-reconciliation-v1.json"
SCOPE_RULES = DATA / "observation-scope-rules-v1.json"
NARROWING = DATA / "procurement-subject-grain-narrowing-v1.json"
SELECTED_CLASS = DATA / "selected-quantity-class-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v4.json"
V2_DECISION = DATA / "v2-vantage-class-decision-v1.json"

OUTCOMES = (
    "PROCUREMENT_SEMANTIC_SUBJECT_CANDIDATE_SELECTED",
    "PROCUREMENT_CLASS_GRAIN_FORMABLE_BUT_NOT_ACTIONABLE",
    "PROCUREMENT_LABELS_SHOW_GROUP_GRAIN_IS_ACTIONABLE",
    "PROCUREMENT_NARROWING_REQUIRES_CATEGORY_GRAIN",
    "PROCUREMENT_SEMANTICS_DO_NOT_JUSTIFY_FURTHER_NARROWING",
    "CPV_VOCABULARY_LABELS_NOT_RETRIEVABLE_FROM_FIRST_PARTY_SOURCE",
    "PROCUREMENT_CLASS_DERIVATION_ARCHITECTURE_GAP",
)
SELECTING = "PROCUREMENT_SEMANTIC_SUBJECT_CANDIDATE_SELECTED"
COHERENCE_SCALE = ["UNRELATED_ACTIVITIES", "RELATED_ACTIVITIES", "SINGLE_DOMAIN"]
NOT_A_CLASSIFICATION = "NOT_A_CLASSIFICATION_SUBJECT"
INFORMATION = ["NONE", "LOW", "MEDIUM", "HIGH"]
FORMABILITY = ["NO", "YES"]
SELECTABLE_GRAINS = (
    "ACTIONABLE_AT_CURRENT_GRAIN",
    "ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS",
)
ACTIONABLE_GRAINS = (
    *SELECTABLE_GRAINS,
    "REQUIRES_NARROWER_SUBJECT_DISCOVERY",
    "NOT_ACTIONABLE",
    "UNDETERMINED",
)
PRODUCT_RELEVANCE = (
    "CLEAR_EXPLORATION_TARGET",
    "BOUNDED_CATEGORY_EXPLORATION",
    "SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN",
    "TOO_BROAD",
    "TOO_THIN",
    "NOT_PRODUCT_RELEVANT",
    "UNDETERMINED",
)
DETAILED = "source_reported_procurement_value_contrast"
WITNESSED = "source_published_classification_value_contrast_witnessed"
AUTHORITY_HOST = "publications.europa.eu"
CONCEPT_HOST = "data.europa.eu"
FORBIDDEN_IN_STATEMENTS = ("market", "demand", "willingness", "spend", "buyer", "customer", "need")
ATTRACTIVENESS = (
    "profitable",
    "lucrative",
    "attractive",
    "booming",
    "growing market",
    "opportunity-rich",
    "trendy",
)
FORBIDDEN_NUMERIC_KEYS = ("score", "priority_score", "weighted", "points", "rank")

DOMINANCE_FIELDS = (
    "EVIDENCE_BREADTH",
    "SCORABLE_BREADTH",
    "COUNTING_DIMENSION_DIVERSITY",
    "SOURCE_DIVERSITY",
    "COMMERCIAL_INFORMATION",
    "PROBLEM_INFORMATION",
    "SEMANTIC_SPECIFICITY",
    "SEMANTIC_COHERENCE",
    "PROVENANCE_DIVERSITY",
    "HYPOTHESIS_FORMABILITY",
)


class ValidationError(Exception):
    pass


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _content_sha(path: pathlib.Path) -> str:
    """The digest a self-hashing artifact carries: sha256 of its bytes without that key."""
    body = _load(path)
    stated = body.pop("CONTENT_SHA256")
    rendered = json.dumps(body, indent=2, ensure_ascii=False) + "\n"
    if hashlib.sha256(rendered.encode("utf-8")).hexdigest() != stated:
        raise ValidationError(f"{path.name} does not hash to the CONTENT_SHA256 it carries")
    return stated


def _breadth(n: int) -> str:
    return "LOW" if n <= 2 else ("MEDIUM" if n <= 9 else "HIGH")


def _scorable_breadth(n: int) -> str:
    return "LOW" if n == 0 else ("MEDIUM" if n <= 9 else "HIGH")


def _diversity(n: int) -> str:
    return "LOW" if n <= 1 else ("MEDIUM" if n == 2 else "HIGH")


def _rank(field: str, value: object) -> int | None:
    if field == "SEMANTIC_COHERENCE":
        if value == NOT_A_CLASSIFICATION:
            return None
        scale = COHERENCE_SCALE
    elif field == "HYPOTHESIS_FORMABILITY":
        scale = FORMABILITY
    else:
        scale = INFORMATION
    if value not in scale:
        raise ValidationError(f"{field} carries {value!r}, not one of {scale}")
    return scale.index(value)


def _dominates(x: dict, y: dict) -> bool:
    better = False
    for field in DOMINANCE_FIELDS:
        rx, ry = _rank(field, x["ordinal"][field]), _rank(field, y["ordinal"][field])
        if rx is None or ry is None:
            continue
        if rx < ry:
            return False
        better |= rx > ry
    return better


# ------------------------------------------------------------------------- checks


def _check_the_freeze(record: dict, universe: dict, vocabulary: dict) -> None:
    freeze = record["freeze"]
    digest = _content_sha(UNIVERSE)
    if freeze["LOOKUP_UNIVERSE_SHA256"] != digest:
        raise ValidationError(
            "the record names a lookup-universe digest the artifact does not have"
        )
    if vocabulary["LOOKUP_UNIVERSE_SHA256"] != digest:
        raise ValidationError("the vocabulary was written against a different lookup universe")
    if universe.get("labels_present") or any(
        "label" in key.lower() for key in universe if key != "labels_present"
    ):
        raise ValidationError("the frozen universe carries labels; it was written after retrieval")
    if not freeze["frozen_before_retrieval"] or not freeze["committed_before_retrieval"]:
        raise ValidationError(
            "the universe is not recorded as frozen and committed before retrieval"
        )
    if (
        freeze["codes_added_after_labels_were_read"]
        or freeze["codes_removed_after_labels_were_read"]
    ):
        raise ValidationError("the universe moved after labels were read")
    for key, field in (
        ("FROZEN_GROUP_CODES", "GROUP_CODES"),
        ("FROZEN_CLASS_CODES", "CLASS_CODES"),
    ):
        if freeze[key] != universe[field]:
            raise ValidationError(f"{key} is not the frozen artifact's {field}")
    if freeze["CODE_COUNT_GROUP"] != len(universe["GROUP_CODES"]):
        raise ValidationError("the group code count is not the frozen artifact's")
    if freeze["CODE_COUNT_CLASS"] != len(universe["CLASS_CODES"]):
        raise ValidationError("the class code count is not the frozen artifact's")
    outside = freeze["present_but_not_frozen"]
    if outside["labels_retrieved"]:
        raise ValidationError("a code outside the frozen universe had its label retrieved")
    if set(outside["codes"]) & set(universe["CLASS_CODES"]):
        raise ValidationError("a code is recorded both inside and outside the freeze")


def _check_the_vocabulary(record: dict, universe: dict, vocabulary: dict) -> dict[str, dict]:
    retrieval = record["retrieval"]
    _content_sha(VOCABULARY)
    concepts = {c["cpv_prefix"]: c for c in vocabulary["concepts"]}
    frozen = set(universe["GROUP_CODES"]) | set(universe["CLASS_CODES"])
    if set(concepts) != frozen:
        raise ValidationError(
            f"the vocabulary records {sorted(set(concepts) - frozen)} beyond and "
            f"{sorted(frozen - set(concepts))} short of the frozen universe"
        )
    if vocabulary.get("raw_responses_stored"):
        raise ValidationError("raw vocabulary responses were copied into the repository")
    for prefix, entry in concepts.items():
        level = "group" if prefix in universe["GROUP_CODES"] else "class"
        if entry["level"] != level:
            raise ValidationError(
                f"{prefix}: recorded at level {entry['level']}, frozen as {level}"
            )
        if entry["CPV_CODE"] != prefix.ljust(8, "0"):
            raise ValidationError(
                f"{prefix}: the concept code is not the prefix padded to eight digits"
            )
        if AUTHORITY_HOST not in entry["retrieved_from"]:
            raise ValidationError(
                f"{prefix}: retrieved from a host that is not the first-party authority"
            )
        if not entry["CONCEPT_URI"].startswith(f"http://{CONCEPT_HOST}/cpv/cpv/"):
            raise ValidationError(f"{prefix}: the concept URI is not the register's")
        if entry["retrieval_status"] != "RESOLVED_FROM_FIRST_PARTY_AUTHORITY":
            if entry.get("PREFERRED_LABEL"):
                raise ValidationError(f"{prefix}: a label recorded on an unresolved concept")
            continue
        if not str(entry.get("PREFERRED_LABEL", "")).strip():
            raise ValidationError(f"{prefix}: resolved with no label")
        if entry["LANGUAGE"] != vocabulary["VOCABULARY_LANGUAGE"]:
            raise ValidationError(f"{prefix}: a language other than the canonical one")
        if len(entry.get("RAW_RESPONSE_SHA256", "")) != 64:
            raise ValidationError(
                f"{prefix}: no raw-response digest, so the label rests on nothing checkable"
            )
        if entry["http_status"] != 200:
            raise ValidationError(f"{prefix}: recorded as resolved on a non-200 response")
        if not entry["broader_matches_code_hierarchy"]:
            raise ValidationError(
                f"{prefix}: the retrieved broader concept disagrees with the code hierarchy"
            )
    digests = [c["RAW_RESPONSE_SHA256"] for c in concepts.values()]
    if len(set(digests)) != len(digests):
        raise ValidationError(
            "two concepts share a raw-response digest; one label came from another's document"
        )
    labels = {c["PREFERRED_LABEL"] for c in concepts.values()}
    if len(labels) != len(concepts):
        raise ValidationError("two frozen concepts share a label; one was inferred from the other")
    if retrieval["THIRD_PARTY_FALLBACKS"] or retrieval["labels_inferred_from_neighbouring_codes"]:
        raise ValidationError("a third-party fallback or an inferred label")
    if retrieval["mission_1_80_labels_used"]:
        raise ValidationError("a recalled Mission 1.80 label was used as a source")
    if retrieval["RESEARCH_DATA_FETCHES"] != 0:
        raise ValidationError("research data was acquired under a documentation budget")
    for key, field in (
        ("GROUP_LABELS_RESOLVED", "group"),
        ("CLASS_LABELS_RESOLVED", "class"),
    ):
        measured = sum(
            1
            for c in concepts.values()
            if c["level"] == field
            and c["retrieval_status"] == "RESOLVED_FROM_FIRST_PARTY_AUTHORITY"
        )
        if retrieval[key] != measured:
            raise ValidationError(f"{key} is {retrieval[key]}, measured {measured}")
    unresolved = sum(
        1
        for c in concepts.values()
        if c["retrieval_status"] != "RESOLVED_FROM_FIRST_PARTY_AUTHORITY"
    )
    if retrieval["GROUP_LABELS_UNRESOLVED"] + retrieval["CLASS_LABELS_UNRESOLVED"] != unresolved:
        raise ValidationError("the unresolved counts are not the vocabulary's")
    if unresolved and record["primary_outcome"] == SELECTING:
        selected = record["selection"]["SELECTED_CODE"]
        if concepts[selected]["retrieval_status"] != "RESOLVED_FROM_FIRST_PARTY_AUTHORITY":
            raise ValidationError("a subject was selected whose own label is unresolved")
    return concepts


def _check_the_derivation(record: dict, run: dict, rerun: dict, universe: dict) -> None:
    d = record["derivation"]
    if d["DERIVATION_MODEL"] != "C_RE_DERIVE_FROM_HELD_NORMALIZED_RECORDS":
        raise ValidationError("group or division evidence reused instead of a re-derivation")
    if d["parent_signals_copied"] or d["group_evidence_copied_to_class"]:
        raise ValidationError("a parent Signal or a group Evidence row was copied onto a child")
    if d["NEW_SIGNAL_TYPE_CREATED"]:
        raise ValidationError("a new signal type invented to make a candidate formable")
    if d["EXISTING_SIGNAL_TYPES_REUSED"] != ["procurement_value_contrast"]:
        raise ValidationError("the reused signal type is not the procurement contrast")
    if d["selective_derivation"]:
        raise ValidationError("cohorts were derived selectively")
    if d["MEMBERSHIP_MODEL"] != "C4_REFUSE_AMBIGUOUS_NOTICE" or d["membership_model_changed"]:
        raise ValidationError("the membership model changed without evidence that it was wrong")
    if d["CPV_GRAIN"] != 4 or d["parameters"].get("cpv_grain") != 4:
        raise ValidationError("the derivation is not at class grain")
    if run["network_acquisitions"] or rerun["network_acquisitions"]:
        raise ValidationError("an acquisition inside the derivation")
    floor = d["MINIMUM_REQUIRED_BY_PROCEDURE"]
    derived = Counter()
    refused = Counter()
    for w in rerun["windows"]:
        for c in w["cohorts"]:
            if c["status"] == "REFUSED":
                refused[c["cpv_prefix"]] += 1
                if c["members"] >= floor or c["refusals"] != ["INSUFFICIENT_INPUT_OBSERVATIONS"]:
                    raise ValidationError(
                        f"{c['cpv_prefix']}: a refusal that is not the procedure's floor"
                    )
            else:
                derived[c["cpv_prefix"]] += 1
    keyed = sum(len(w["cohorts"]) for w in rerun["windows"])
    if d["CLASS_COHORTS_KEYED"] != keyed:
        raise ValidationError("the keyed cohort count is not the re-run record's")
    if d["CLASS_COHORTS_DERIVED"] != sum(derived.values()) or d["CLASS_COHORTS_DERIVED"] != len(
        run["signals"]
    ):
        raise ValidationError("the derived cohort count is not the run record's")
    if d["CLASS_COHORTS_REFUSED"] != sum(refused.values()):
        raise ValidationError("the refused cohort count is not the re-run record's")
    frozen = set(universe["CLASS_CODES"])
    seen = set(derived) | set(refused)
    if not seen <= frozen:
        raise ValidationError(
            f"cohorts keyed on codes outside the frozen universe: {sorted(seen - frozen)}"
        )
    for s in run["signals"]:
        if s["classification_level"] != "class":
            raise ValidationError(f"signal {s['signal_id'][:8]} is not at class grain")
        if s["classification_level_code"] not in frozen:
            raise ValidationError(
                f"signal {s['signal_id'][:8]} is keyed outside the frozen universe"
            )
        if s["contributing_records"] < floor:
            raise ValidationError(f"signal {s['signal_id'][:8]} is below the procedure's floor")
        if s["magnitude_unit"] != s["currency"]:
            raise ValidationError(f"signal {s['signal_id'][:8]}: unit is not its currency")
        kinds = Counter(e["proposition_kind"] for e in s["evidence"])
        if kinds != Counter({DETAILED: 1, WITNESSED: 1}):
            raise ValidationError(
                f"signal {s['signal_id'][:8]} witnesses {dict(kinds)}, not one detailed and one broader claim"
            )
        for e in s["evidence"]:
            statement = e["statement"].lower()
            if f'class "{s["classification_level_code"]}"' not in e["statement"]:
                raise ValidationError("a statement that does not name the class it is about")
            if any(w in statement for w in FORBIDDEN_IN_STATEMENTS):
                raise ValidationError("a statement carrying market vocabulary")
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
    if not d["grain_3_records_reproduce_byte_identically"]:
        raise ValidationError("the group-grain records are recorded as having moved")


def _check_semantics(record: dict, run: dict, rerun: dict) -> None:
    """Currency and notice class, checked against the cohorts rather than against a boolean."""
    currency = record["currency_semantics"]
    if currency["cross_currency_contrast_performed"] or currency["fx_conversion_performed"]:
        raise ValidationError("a cross-currency contrast or an FX conversion")
    notice = record["notice_type_semantics"]
    if notice["CONTRACT_NOTICE_and_CONTRACT_AWARD_NOTICE_combined"]:
        raise ValidationError("notice classes combined without a contract basis")
    if not notice["bt_161_limitations_preserved"] or notice["realised_spend_inferred"]:
        raise ValidationError("the BT-161 limitations were dropped, or realised spend inferred")
    # every non-EUR cohort the derivation met was refused, and the record names each one
    measured = [
        {
            "window": w["witness"],
            "cpv_prefix": c["cpv_prefix"],
            "currency": c["currency"],
            "members": c["members"],
        }
        for w in rerun["windows"]
        for c in w["cohorts"]
        if c["currency"] != "EUR"
    ]
    for entry in measured:
        matching = [
            c
            for w in rerun["windows"]
            for c in w["cohorts"]
            if c["cpv_prefix"] == entry["cpv_prefix"] and c["currency"] == entry["currency"]
        ]
        if any(c["status"] != "REFUSED" for c in matching):
            raise ValidationError(
                f"{entry['cpv_prefix']}: a non-EUR cohort was derived rather than refused"
            )
    recorded = currency["non_eur_cohorts_refused_at_class_grain"]
    if sorted(
        map(
            json.dumps,
            recorded,
        ),
        key=str,
    ) != sorted(map(json.dumps, measured), key=str):
        raise ValidationError("the non-EUR refusals are not the ones the derivation met")
    # one currency and one notice class per persisted cohort, from the run record itself
    for s in run["signals"]:
        if not isinstance(s["currency"], str) or not isinstance(s["notice_class"], str):
            raise ValidationError(
                f"signal {s['signal_id'][:8]}: more than one currency or notice class"
            )


def _check_the_reliability(record: dict, v4: dict, reconciliation: dict) -> None:
    r = record["reliability"]
    if r["scope_modified"] or r["assessments_created"]:
        raise ValidationError("a reliability scope moved or an assessment was created")
    assessments = {a["assessment_id"]: a for a in reconciliation["revision_1_audit"]["why_stale"]}
    rows = {x["evidence_id"]: x for x in v4["rows"]}
    class_rows = [
        rows[e] for p in v4["packets"] if ":CPV-class:" in p["subject"] for e in p["evidence_ids"]
    ]
    scorable = sum(1 for x in class_rows if x["scorable"])
    if r["NEW_EVIDENCE_SCORABLE"] != scorable:
        raise ValidationError("scorable new evidence is not the preparation's")
    if r["NEW_EVIDENCE_NONSCORABLE"] != len(class_rows) - scorable:
        raise ValidationError("non-scorable new evidence is not the preparation's")
    measured = Counter()
    for row in class_rows:
        res = row["reliability_resolution"]
        if res["outcome"] != "RESOLVED":
            continue
        entry = assessments.get(res["assessment_id"])
        if entry is None:
            raise ValidationError(
                f"{row['evidence_id'][:8]}: bound to an assessment the reconciliation does not name"
            )
        measured[res["assessment_id"]] += 1
    for assessment_id, stated in r["assessments_applied"].items():
        entry = assessments.get(assessment_id)
        if entry is None:
            raise ValidationError(f"{assessment_id[:8]}: applied and not in the reconciliation")
        if (
            stated["reliability"] != entry["reliability"]
            or stated["proposition_kind"] != entry["proposition_kind"]
        ):
            raise ValidationError(
                f"{assessment_id[:8]}: a reliability copied onto a non-matching scope"
            )
        if stated["rows"] != measured.get(assessment_id, 0):
            raise ValidationError(
                f"{assessment_id[:8]}: {stated['rows']} rows stated, {measured.get(assessment_id, 0)} measured"
            )
    if set(r["assessments_applied"]) != set(measured):
        raise ValidationError("the assessments applied are not the ones the resolver bound")


def _check_the_candidates(
    record: dict, v4: dict, universe: dict, concepts: dict, rules: dict
) -> dict[str, dict]:
    packets = {p["subject"]: p for p in v4["packets"]}
    schemes = {(r["source_id"], r["scheme"]): r for r in rules["rules"]}
    candidates = {c["subject_key"]: c for c in record["candidates"]}

    expected = {s for s in packets if s != "subject:docker"}
    expected |= {f"ted-eu:CPV-group:{c}" for c in universe["GROUP_CODES"]}
    expected |= {f"ted-eu:CPV-class:{c}" for c in universe["CLASS_CODES"]}
    if set(candidates) != expected:
        raise ValidationError(
            f"the candidate universe carries {sorted(set(candidates) - expected)} beyond and "
            f"{sorted(expected - set(candidates))} short of the packets and the frozen codes"
        )
    if record["candidate_universe"]["count"] != len(expected):
        raise ValidationError("the recorded universe count disagrees with the candidates")

    for subject, c in candidates.items():
        for key in c:
            if any(k in key.lower() for k in FORBIDDEN_NUMERIC_KEYS) and isinstance(
                c[key], int | float
            ):
                raise ValidationError(
                    f"{subject}: a numeric {key}; a priority is a tier, never a number"
                )
        blob = json.dumps(c).lower()
        if any(w in blob for w in ATTRACTIVENESS):
            raise ValidationError(
                f"{subject}: market-attractiveness vocabulary in a candidate record"
            )
        level = c.get("CPV_LEVEL")
        if level not in ("group", "class"):
            continue
        prefix = c["CPV_CODE"]
        concept = concepts[prefix]
        if c["OFFICIAL_LABEL"] != concept["PREFERRED_LABEL"]:
            raise ValidationError(f"{subject}: a label that is not the retrieved one")
        if c["cpv_concept_code"] != concept["CPV_CODE"]:
            raise ValidationError(f"{subject}: the concept code is not the vocabulary's")
        if not c["label_is_display_metadata_not_identity"]:
            raise ValidationError(f"{subject}: the label is used as identity")
        if c["OFFICIAL_LABEL"] is not None and c["OFFICIAL_LABEL"] in subject:
            raise ValidationError(f"{subject}: the label is used as identity")
        # §10. An unresolved concept is a first-class state: the subject keeps its code and its
        # Evidence, and it may not pass a gate that turns on what the subject MEANS.
        resolved = concept["retrieval_status"] == "RESOLVED_FROM_FIRST_PARTY_AUTHORITY"
        if not resolved:
            if c["OFFICIAL_LABEL"] is not None:
                raise ValidationError(
                    f"{subject}: a label on a candidate whose concept is unresolved"
                )
            if c["exploratory_category_hypothesis"]["adopted"]:
                raise ValidationError(
                    f"{subject}: an exploratory hypothesis adopted over a subject whose meaning "
                    "the register did not establish"
                )
        rule = schemes.get(("ted-eu", f"CPV-{level}"))
        if rule is None:
            raise ValidationError(f"{subject}: no reviewed scope rule for CPV-{level}")
        if c["subject_scope"] != rule["scope_type"] or c["subject_type"] != "CATEGORY":
            raise ValidationError(
                f"{subject}: scope is not the reviewed one, or a category typed otherwise"
            )
        if c["SEMANTIC_COHERENCE"] not in COHERENCE_SCALE:
            raise ValidationError(f"{subject}: semantic coherence {c['SEMANTIC_COHERENCE']!r}")
        if not str(c["semantic_coherence_basis"]).strip():
            raise ValidationError(f"{subject}: a coherence judgement with no stated basis")
        if c["PRODUCT_RELEVANCE"] not in PRODUCT_RELEVANCE:
            raise ValidationError(f"{subject}: product relevance {c['PRODUCT_RELEVANCE']!r}")
        if c["ACTIONABLE_GRAIN"] not in ACTIONABLE_GRAINS:
            raise ValidationError(f"{subject}: actionable grain {c['ACTIONABLE_GRAIN']!r}")
        if (
            c["establishes_product_demand"]
            or c["buyer_semantics"]["BUYER_FOR_PROPOSED_INTERVENTION"]
        ):
            raise ValidationError(
                f"{subject}: a classification read as demand, or an authority as a buyer for a product"
            )
        sem = c["procurement_semantics"]
        if (
            sem["value_is_realised_spend"]
            or sem["value_is_willingness_to_pay"]
            or sem["authority_is_buyer_for_unspecified_product"]
        ):
            raise ValidationError(f"{subject}: a notice value read as spend or willingness to pay")
        if c["product_intervention_grain"] == "DIRECTLY_SUPPORTED":
            raise ValidationError(f"{subject}: a category is not a product")

        packet = packets.get(subject)
        ev = packet["size"] if packet else 0
        scorable = packet["eligibility_counts"].get("ELIGIBLE_SCORING", 0) if packet else 0
        key = "notices_per_group_code" if level == "group" else "notices_per_class_code"
        if c["NOTICE_COUNT"] != universe[key][prefix]:
            raise ValidationError(f"{subject}: notice count is not the frozen universe's")
        if c["evidence_rows"] != ev or c["EVIDENCE"] != ev:
            raise ValidationError(f"{subject}: evidence rows are not the preparation's")
        if c["scorable_rows"] != scorable or c["SCORABLE_EVIDENCE"] != scorable:
            raise ValidationError(f"{subject}: scorable rows are not the preparation's")
        formable = bool(packet) and packet["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
        if c["FORMABLE"] != formable or c["hypothesis_formable"] != formable:
            raise ValidationError(f"{subject}: formability is not the preparation's")
        if packet and sorted(c["counting_dimensions"]) != sorted(packet["counting_dimensions"]):
            raise ValidationError(f"{subject}: counting dimensions are not the preparation's")
        if packet and c["packet_id"] != packet["packet_id"]:
            raise ValidationError(f"{subject}: the packet id is not the held packet's")
        if packet and c["egress_state"] != packet["external_synthesis"]["availability"]:
            raise ValidationError(f"{subject}: egress is not the preparation's")
        if c["egress_eligible"] or not c["egress_review_required_before_synthesis"]:
            raise ValidationError(
                f"{subject}: egress read as eligible while ted-eu is NOT_ASSESSED"
            )
        if c["INDEPENDENCE"] != "UNKNOWN" or c["PROVENANCE_SHAPES"] > 1:
            raise ValidationError(f"{subject}: independence or provenance manufactured")
        if packet:
            rows = {r["evidence_id"]: r for r in v4["rows"]}
            measured = Counter()
            for evidence_id in packet["evidence_ids"]:
                resolution = rows[evidence_id]["reliability_resolution"]
                measured[(resolution.get("assessment_id") or "NONE")] += 1
            stated = Counter()
            for kind in c["proposition_kinds"].values():
                stated[kind["assessment_id"]] += kind["rows"]
            if measured != stated:
                raise ValidationError(
                    f"{subject}: the reliability distribution is not the resolver's"
                )

        # ordinal fields, recomputed
        o = c["ordinal"]
        expected_ordinal = {
            "EVIDENCE_BREADTH": _breadth(ev),
            "SCORABLE_BREADTH": _scorable_breadth(scorable),
            "COUNTING_DIMENSION_DIVERSITY": _diversity(
                len(packet["counting_dimensions"]) if packet else 0
            ),
            "SOURCE_DIVERSITY": "LOW",
            "HYPOTHESIS_FORMABILITY": "YES" if formable else "NO",
            "SEMANTIC_SPECIFICITY": "HIGH" if level == "class" else "MEDIUM",
            "SEMANTIC_COHERENCE": c["SEMANTIC_COHERENCE"],
            "PROVENANCE_DIVERSITY": "LOW",
        }
        for field, value in expected_ordinal.items():
            if o[field] != value:
                raise ValidationError(f"{subject}: {field} is {o[field]}, the counts say {value}")
        if o["PROBLEM_INFORMATION"] != "NONE":
            raise ValidationError(
                f"{subject}: problem information from a procurement classification"
            )

        # the §13 gate
        gate = c["exploratory_category_hypothesis"]
        adoptable = gate["adopted"]
        if adoptable and not formable:
            raise ValidationError(f"{subject}: an exploratory hypothesis adopted with no Evidence")
        if adoptable and c["SEMANTIC_COHERENCE"] == "UNRELATED_ACTIVITIES":
            raise ValidationError(
                f"{subject}: an exploratory hypothesis over a disjunction of unrelated markets"
            )
        if adoptable and not str(gate.get("statement", "")).strip():
            raise ValidationError(f"{subject}: an adopted hypothesis with no statement")
        if adoptable != (c["ACTIONABLE_GRAIN"] in SELECTABLE_GRAINS):
            raise ValidationError(
                f"{subject}: the hypothesis gate and the actionable grain disagree"
            )
        if adoptable != (c["veto_state"] == "NOT_VETOED"):
            raise ValidationError(f"{subject}: the veto and the hypothesis gate disagree")
        if c["veto_state"] == "VETOED" and not str(c["veto_reason"]).strip():
            raise ValidationError(f"{subject}: vetoed with no reason")
        if c["veto_state"] == "NOT_VETOED" and str(c["veto_reason"]).strip():
            raise ValidationError(f"{subject}: not vetoed and carrying a veto reason")
        if not formable and c["ACTIONABLE_GRAIN"] != "NOT_ACTIONABLE":
            raise ValidationError(f"{subject}: not formable and still actionable")
    return candidates


def _check_dominance_and_selection(
    record: dict, candidates: dict[str, dict], concepts: dict
) -> None:
    dominance = record["dominance"]
    if tuple(dominance["fields"]) != DOMINANCE_FIELDS:
        raise ValidationError("the dominance fields are not the recorded model's")
    if "SEMANTIC_COHERENCE" not in dominance["fields"]:
        raise ValidationError("dominance ignores the field this mission's retrieval bought")
    computed: dict[str, str] = {}
    for s, c in candidates.items():
        for t, o in candidates.items():
            if t != s and _dominates(o, c):
                computed.setdefault(s, t)
    frontier = sorted(s for s in candidates if s not in computed)
    if sorted(dominance["PARETO_FRONTIER"]) != frontier:
        raise ValidationError(f"the recorded frontier is not the computed {frontier}")
    if sorted(dominance["DOMINATED_CANDIDATES"]) != sorted(computed):
        raise ValidationError(f"the recorded dominated set is not the computed {sorted(computed)}")
    for s, by in dominance["dominated_by"].items():
        if not _dominates(candidates[by], candidates[s]):
            raise ValidationError(
                f"{s} is recorded as dominated by {by}, which does not dominate it"
            )
    for s, c in candidates.items():
        state = "DOMINATED" if s in computed else "FRONTIER"
        if c["dominance_state"] != state:
            raise ValidationError(f"{s}: dominance state {c['dominance_state']}, computed {state}")
    vetoed = sorted(s for s, c in candidates.items() if c["veto_state"] == "VETOED")
    if sorted(dominance["VETOED_CANDIDATES"]) != vetoed:
        raise ValidationError("the vetoed list disagrees with the candidates")
    selectable = sorted(s for s in frontier if candidates[s]["veto_state"] == "NOT_VETOED")
    if sorted(dominance["unvetoed_frontier"]) != selectable:
        raise ValidationError(f"the unvetoed frontier is not the computed {selectable}")

    outcome = record["primary_outcome"]
    if outcome not in OUTCOMES:
        raise ValidationError(f"primary outcome {outcome!r} is not one of the seven")
    selection = record["selection"]
    selected = selection["SELECTED_SUBJECT"]
    if outcome == SELECTING:
        if selected not in candidates:
            raise ValidationError("the selected subject is not a candidate")
        if len(selectable) != 1 or selectable[0] != selected:
            raise ValidationError(
                f"the selected subject is not the one unvetoed frontier candidate {selectable}"
            )
        c = candidates[selected]
        if c["dominance_state"] != "FRONTIER" or c["veto_state"] != "NOT_VETOED":
            raise ValidationError("the selected candidate is dominated or vetoed")
        if not c["FORMABLE"] or c["ACTIONABLE_GRAIN"] not in SELECTABLE_GRAINS:
            raise ValidationError(
                "the selected candidate is not formable, or not at a selectable grain"
            )
        if (
            selection["SELECTED_CODE"] != c["CPV_CODE"]
            or selection["SELECTED_LEVEL"] != c["CPV_LEVEL"]
        ):
            raise ValidationError("the selected code or level is not the candidate's")
        if selection["SELECTED_LABEL"] != concepts[c["CPV_CODE"]]["PREFERRED_LABEL"]:
            raise ValidationError("the selected label is not the retrieved one")
        if selection["SELECTED_PACKET"] != c["packet_id"]:
            raise ValidationError("the selected packet is not the candidate's")
        if selection["value_used_to_select"] or selection["attractiveness_used_to_select"]:
            raise ValidationError("a value or an attractiveness judgement selected the subject")
        for gate, passed in selection["gates"].items():
            if gate == "egress_permission_required_for_selection":
                if passed:
                    raise ValidationError("egress permission was made a condition of selection")
            elif not passed:
                raise ValidationError(f"the selected subject fails gate {gate}")
        title = record["recommended_next_mission"]["title"].lower()
        if "egress review" not in title:
            raise ValidationError(
                "a subject was selected with egress unassessed and no egress review next"
            )
    else:
        if selected is not None:
            raise ValidationError("a subject selected under a non-selecting outcome")
        if selectable:
            raise ValidationError(
                f"an unvetoed frontier candidate exists and none was selected: {selectable}"
            )
    if selection["BEST_SECOND_OPPORTUNITY_CANDIDATE"] != selected:
        raise ValidationError("the best second-Opportunity candidate is not the selected subject")
    for key in ("BEST_GROUP_PACKET", "BEST_CLASS_PACKET", "BEST_HELD_PACKET"):
        if selection[key] not in candidates:
            raise ValidationError(f"{key} is not a candidate")

    # a class defeats its group only where dominance says so
    for pair in record["group_versus_class"]["pairs"]:
        group, klass = candidates[pair["group"]], candidates[pair["class"]]
        lost = group["evidence_rows"] - klass["evidence_rows"]
        if pair["evidence_lost_by_narrowing"] != lost:
            raise ValidationError(
                f"{pair['class']}: the evidence lost by narrowing is not the measured {lost}"
            )
        if pair["verdict"] == "CLASS_WINS":
            if not _dominates(klass, group):
                raise ValidationError(
                    f"{pair['class']} is recorded as beating {pair['group']} and does not dominate it"
                )
            if lost > 0:
                raise ValidationError(
                    f"{pair['class']} wins while narrowing destroyed {lost} Evidence rows"
                )
    if record["group_versus_class"]["class_automatically_beats_group"]:
        raise ValidationError("a class is recorded as automatically beating its group")


def _check_preparation_and_counters(
    record: dict, v4: dict, reconciliation: dict, run: dict, rerun: dict
) -> None:
    p = record["preparation"]
    for version in (1, 2, 3):
        if p[f"v{version}_untouched_sha256"] != _sha(PREPARATION[version]):
            raise ValidationError(f"the historical preparation v{version} was rewritten")
    v3 = _load(PREPARATION[3])
    if v3.get("mission") != "1.81" or v4.get("supersedes") != f"docs/data/{PREPARATION[3].name}":
        raise ValidationError("v4 does not supersede v3, or v3 was rewritten as current")
    if (
        p["PREPARATION_AFTER"] != v4["artifact_version"]
        or p["PREPARATION_BEFORE"] != v3["artifact_version"]
    ):
        raise ValidationError("the preparation versions are not the records'")
    if p["packets"] != {
        "before": v3["totals"]["packets_built"],
        "after": v4["totals"]["packets_built"],
    }:
        raise ValidationError("packet counts are not the records'")
    subjects = {x["subject"] for x in v4["packets"]}
    for retained in ("ted-eu:CPV-division:92", "ted-eu:CPV-group:926"):
        if retained not in subjects:
            raise ValidationError(f"{retained} was deleted from the current preparation")
    if not p["division_and_group_packets_retained"]:
        raise ValidationError("the parent packets are recorded as not retained")
    if sorted(p["new_packets"]) != sorted(x for x in subjects if ":CPV-class:" in x):
        raise ValidationError("the new packets are not v4's class packets")
    for subject in ("ted-eu:CPV-division:92", "ted-eu:CPV-group:926"):
        old = next(x for x in v3["packets"] if x["subject"] == subject)
        new = next(x for x in v4["packets"] if x["subject"] == subject)
        if sorted(old["evidence_ids"]) != sorted(new["evidence_ids"]):
            raise ValidationError(f"{subject}: the parent packet's rows changed")

    counters = record["counters"]
    before, after, deltas = counters["before"], counters["after"], counters["deltas"]
    recon_after = reconciliation["counters"]["after"]
    narrowing = _load(NARROWING)
    if before != narrowing["counters"]["after"]:
        raise ValidationError("the before counters are not Mission 1.81's after counters")
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
        if (
            before[key]
            != recon_after[
                key if key != "opportunity_evidence_links" else "opportunity_evidence_links"
            ]
        ):
            raise ValidationError(f"{key} disagrees with the reconciled deployment")
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
    if after["evidence"] != v4["totals"]["evidence_rows_inspected"]:
        raise ValidationError("the Evidence count is not v4's")
    if counters["SECOND_RUN_NEW_ROWS"] != 0:
        raise ValidationError("the second run is recorded as having created rows")
    if (
        rerun["signals_persisted"]
        or rerun["interpretation"]["claims_new"]
        or rerun["interpretation"]["evidence_new"]
    ):
        raise ValidationError("the second run created rows")
    if len(rerun["skipped_as_existing_witness"]) != len(run["signals"]):
        raise ValidationError("the second run did not meet every persisted witness")

    acc = record["mission_accounting"]
    for key in (
        "research_data_fetches",
        "ted_api_calls",
        "dataset_downloads",
        "raw_records_created",
        "normalized_records_created",
        "mailbox_reads",
        "outbound_messages",
        "globalping_calls",
        "globalping_measurements",
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
    if (acc["signals_created"], acc["claims_created"], acc["evidence_created"]) != (
        expected["signals"],
        expected["claims"],
        expected["evidence"],
    ):
        raise ValidationError("canonical creations are not the derivation's")

    immutable = record["immutable"]
    if (
        immutable["opportunities"] != 1
        or immutable["docker_current_revision"] != 2
        or immutable["opportunity_links"] != 14
    ):
        raise ValidationError("the docker Opportunity moved")
    egress = record["egress"]
    if (
        egress["TED_EGRESS_STATE"] != "NOT_ASSESSED"
        or egress["decided_here"]
        or egress["granted"]
        or egress["denied"]
    ):
        raise ValidationError("the ted-eu egress question was decided or moved")
    if egress["source_review_appended"] or egress["externally_serialized"]:
        raise ValidationError("a source review was appended, or something was serialized outward")
    if not egress["EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS"]:
        raise ValidationError("egress review is not recorded as required before synthesis")
    rep = record["representation_check"]
    if rep["transmitted"] or rep["model_called"]:
        raise ValidationError("the representation check transmitted something")
    for subject, entry in rep["packets"].items():
        if entry["violations"] != 0 or subject not in subjects:
            raise ValidationError(
                f"representation recorded with violations or for a non-packet {subject}"
            )
    if record["no_automatic_descent"]["grain_5_persisted"]:
        raise ValidationError("grain 5 was persisted")


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


def validate() -> dict:
    record = _load(RECORD)
    universe = _load(UNIVERSE)
    vocabulary = _load(VOCABULARY)
    run = _load(RUN)
    rerun = _load(RERUN)
    v4 = _load(PREPARATION[4])
    reconciliation = _load(RECONCILIATION)
    rules = _load(SCOPE_RULES)
    try:
        _check_the_freeze(record, universe, vocabulary)
        concepts = _check_the_vocabulary(record, universe, vocabulary)
        _check_the_derivation(record, run, rerun, universe)
        _check_semantics(record, run, rerun)
        _check_the_reliability(record, v4, reconciliation)
        candidates = _check_the_candidates(record, v4, universe, concepts, rules)
        _check_dominance_and_selection(record, candidates, concepts)
        _check_preparation_and_counters(record, v4, reconciliation, run, rerun)
        _check_the_parked_arc(record)
    except (KeyError, TypeError, IndexError, StopIteration, AttributeError) as error:
        raise ValidationError(f"the records do not carry {error!r}") from error
    return record


# ------------------------------------------------------------------------- render


def render(record: dict) -> str:
    freeze, retrieval, d = record["freeze"], record["retrieval"], record["derivation"]
    selection = record["selection"]
    lines = [
        "# What the CPV codes mean, and which subject that makes selectable",
        "",
        f"Generated from `{RECORD.name}`. Do not edit by hand.",
        "",
        f"**{record['primary_outcome']}** — selected `{selection['SELECTED_SUBJECT']}`, "
        f'"{selection["SELECTED_LABEL"]}"; next {record["recommended_next_mission"]["id"]} '
        f"{record['recommended_next_mission']['title']}.",
        "",
        record["outcome_basis"],
        "",
        "## The freeze",
        "",
        f"{freeze['CODE_COUNT_GROUP']} group codes and {freeze['CODE_COUNT_CLASS']} class codes, from "
        f"{freeze['SOURCE_RECORD_COUNT']} held notices, digest `{freeze['LOOKUP_UNIVERSE_SHA256'][:16]}…`, "
        f"committed before retrieval. Codes added after labels were read: "
        f"{freeze['codes_added_after_labels_were_read']}; removed: {freeze['codes_removed_after_labels_were_read']}.",
        "",
        freeze["why_a_freeze"],
        "",
        "## The vocabulary",
        "",
        f"{retrieval['FIRST_PARTY_AUTHORITY']}, `{retrieval['endpoint_pattern']}`, version "
        f"{retrieval['VOCABULARY_VERSION']}, language `{retrieval['VOCABULARY_LANGUAGE']}`. "
        f"{retrieval['DOCUMENTATION_FETCHES']} documentation fetches, "
        f"{retrieval['RESEARCH_DATA_FETCHES']} research-data fetches, "
        f"{retrieval['THIRD_PARTY_FALLBACKS']} third-party fallbacks. "
        f"Group labels resolved {retrieval['GROUP_LABELS_RESOLVED']}/"
        f"{retrieval['GROUP_LABELS_RESOLVED'] + retrieval['GROUP_LABELS_UNRESOLVED']}, class labels "
        f"{retrieval['CLASS_LABELS_RESOLVED']}/"
        f"{retrieval['CLASS_LABELS_RESOLVED'] + retrieval['CLASS_LABELS_UNRESOLVED']}.",
        "",
        retrieval["a_retrieval_summary_is_not_a_document"],
        "",
        "## The groups, re-evaluated with their labels",
        "",
        "| group | official label | notices | evidence | coherence | actionable grain | veto |",
        "|---|---|---|---|---|---|---|",
    ]
    for g in record["group_reassessment"]["groups"]:
        lines.append(
            f"| `{g['GROUP_CODE']}` | {g['OFFICIAL_LABEL']} | {g['NOTICE_COUNT']} | {g['SCORABLE']} "
            f"| {g['SEMANTIC_COHERENCE']} | `{g['ACTIONABLE_GRAIN']}` | **{g['VETO']}** |"
        )
    lines += [
        "",
        record["group_reassessment"]["finding"],
        "",
        "## The classes",
        "",
        "| class | official label | notices | signals | evidence | scorable | coherence | actionable grain | veto |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for c in record["candidates"]:
        if c.get("CPV_LEVEL") != "class":
            continue
        lines.append(
            f"| `{c['CPV_CODE']}` | {c['OFFICIAL_LABEL']} | {c['NOTICE_COUNT']} | {c['SIGNALS']} "
            f"| {c['EVIDENCE']} | {c['SCORABLE_EVIDENCE']} | {c['SEMANTIC_COHERENCE']} "
            f"| `{c['ACTIONABLE_GRAIN']}` | **{c['VETO_STATE']}** |"
        )
    dominance = record["dominance"]
    lines += [
        "",
        f"Derivation: {d['CLASS_COHORTS_KEYED']} cohorts keyed at grain {d['CPV_GRAIN']}, "
        f"{d['CLASS_COHORTS_DERIVED']} derived, {d['CLASS_COHORTS_REFUSED']} refused at the procedure's "
        f"floor of {d['MINIMUM_REQUIRED_BY_PROCEDURE']}. {d['NEW_SIGNALS']} Signals, {d['NEW_CLAIMS']} Claims, "
        f"{d['NEW_EVIDENCE']} Evidence, {record['reliability']['NEW_EVIDENCE_SCORABLE']} scorable.",
        "",
        d["selective_derivation_note"],
        "",
        "## Selection",
        "",
        f"Frontier {dominance['PARETO_FRONTIER']}; unvetoed {dominance['unvetoed_frontier']}.",
        "",
        dominance["frontier_note"],
        "",
        selection["SELECTION_BASIS"],
        "",
        f"**What was not claimed.** {selection['what_was_not_claimed']}",
        "",
        f"Egress: {record['egress']['TED_EGRESS_STATE']}, review required before synthesis "
        f"{record['egress']['EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS']}, decided here "
        f"{record['egress']['decided_here']}.",
        "",
        f"Counters: signals {record['counters']['before']['signals']} to {record['counters']['after']['signals']}, "
        f"claims {record['counters']['before']['claims']} to {record['counters']['after']['claims']}, evidence "
        f"{record['counters']['before']['evidence']} to {record['counters']['after']['evidence']}; every other "
        f"counter unchanged; second run created {record['counters']['SECOND_RUN_NEW_ROWS']} rows.",
        "",
        f"**Next: {record['recommended_next_mission']['title']}.** {record['recommended_next_mission']['shape']}",
        "",
    ]
    return "\n".join(lines)


def render_vocabulary(vocabulary: dict) -> str:
    lines = [
        "# The CPV concepts this repository holds a subject for",
        "",
        f"Generated from `{VOCABULARY.name}`. Do not edit by hand.",
        "",
        f"Authority: {vocabulary['FIRST_PARTY_AUTHORITY']}. Scheme `{vocabulary['VOCABULARY_SCHEME']}`, "
        f"version {vocabulary['VOCABULARY_VERSION']}, language `{vocabulary['VOCABULARY_LANGUAGE']}`, "
        f"retrieved {vocabulary['RETRIEVAL_TIME']}.",
        "",
        "The label is display metadata and never identity: a subject is keyed on its code.",
        "",
        "| level | code | concept | official label | status |",
        "|---|---|---|---|---|",
    ]
    for entry in vocabulary["concepts"]:
        lines.append(
            f"| {entry['level']} | `{entry['cpv_prefix']}` | `{entry['CPV_CODE']}` "
            f"| {entry['PREFERRED_LABEL']} | {entry['retrieval_status']} |"
        )
    outside = vocabulary["present_in_held_population_but_outside_the_frozen_universe"]
    lines += [
        "",
        "## Present in the held population and outside the frozen universe",
        "",
        f"`{'`, `'.join(sorted(outside['codes']))}` — {outside['why']} {outside['why_not_retrieved']}",
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
        print(f"REFUSED  procurement subject semantics: {error}")
        return 1
    vocabulary = _load(VOCABULARY)
    pages = ((RENDERED, render(record)), (VOCABULARY_MD, render_vocabulary(vocabulary)))
    if args.check:
        for path, text in pages:
            if not path.exists():
                print(f"DRIFT    {path.name} does not exist")
                return 1
            if path.read_text(encoding="utf-8") != text:
                print(f"DRIFT    {path.name} does not match its record")
                return 1
        print("ok       the procurement subject semantics match their records")
        return 0
    for path, text in pages:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote    {path.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['primary_outcome']}")
    print(
        f"selected {record['selection']['SELECTED_SUBJECT']}  {record['selection']['SELECTED_LABEL']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
