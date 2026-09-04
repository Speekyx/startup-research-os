"""The Wikimedia convergent reliability question, prepared (Mission 1.44).

Measures the live scope, runs the REAL resolver and the REAL leak checks, and
renders the question under `human-reliability-assessment-rubric@1.0.0` with
**every judgement field blank**.

    docs/data/wikimedia-convergent-reliability-review-packet-v1.json
    docs/data/wikimedia-convergent-reliability-review-packet-v1.md

**A PREPARATION PACKET RECORDS THE QUESTION BEFORE THE HUMAN ANSWERS IT.** Once
an assessment exists for the scope the packet is history: regenerating it then
would rewrite the record of what the operator was actually asked, so it refuses
(§32, the guard Mission 1.42.1 added to its own packet for the same reason).

    uv run python infrastructure/scripts/build_wikimedia_convergent_reliability_packet.py
    uv run python infrastructure/scripts/build_wikimedia_convergent_reliability_packet.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
for package in ("claim-model", "evidence-reliability", "contracts"):
    sys.path.insert(0, str(ROOT / "packages" / package / "python"))

DOCS = ROOT / "docs" / "data"
OUT_JSON = DOCS / "wikimedia-convergent-reliability-review-packet-v1.json"
OUT_MD = DOCS / "wikimedia-convergent-reliability-review-packet-v1.md"
FINDINGS = ROOT / "infrastructure" / "scripts" / "wikimedia_convergent_reliability_findings.json"

CONVERGENT_KIND = "platform_counted_content_request_change_witnessed"
DETAILED_KIND = "platform_counted_content_request_change"
SCOPE_FIELDS = ("source_id", "resource_id", "record_kind_id", "claim_type", "proposition_kind")

# Every other proposition kind in the corpus, so the leak checks probe the real
# neighbourhood rather than a chosen one.
OTHER_KINDS = (
    "source_reported_procurement_value_contrast",
    "source_published_classification_value_contrast_witnessed",
    "community_site_published_questions_carrying_tag",
    "community_site_questions_without_accepted_answer",
    "source_reported_metric_period_change",
    "source_reported_term_frequency_change",
    "source_reported_term_frequency_contrast",
)

BLANK_JUDGEMENT = {
    "dimension_states": {
        "MEASUREMENT_DEFINITION": None,
        "SOURCE_SIDE_VALIDATION": None,
        "HISTORICAL_MUTABILITY": None,
        "COMPLETENESS_AND_MISSINGNESS": None,
        # Filled below from the findings, where and only where the rubric
        # permits software to assert an absence.
        "SOURCE_SIDE_CHECKABILITY": None,
    },
    "hard_stops_triggered": None,
    "numeric_judgement_gate": "UNANSWERED",
    "reliability": None,
    "reviewed_by": None,
    "rationale": "",
    "stated_limitation": "",
    "review_timestamp": None,
}

ROWS = """
    SELECT e.id AS evidence_id, e.claim_id, e.signal_id, e.source_id, e.direction,
           e.relevance, e.directness, e.extraction_confidence, e.observation_category,
           e.independence_state, e.independence_group_id, e.reliability AS supplied,
           c.claim_type, c.proposition_facts, c.current_revision, c.temporality,
           (SELECT DISTINCT si.record_kind_id FROM nlp.signal_inputs si
             WHERE si.signal_id = e.signal_id LIMIT 1) AS record_kind_id,
           (SELECT DISTINCT r.provenance ->> 'resource_id'
              FROM nlp.signal_inputs si
              JOIN acquisition.normalized_records n ON n.id = si.normalized_record_id
              JOIN acquisition.raw_records r ON r.id = n.raw_record_id
             WHERE si.signal_id = e.signal_id LIMIT 1) AS resource_id
      FROM scoring.evidence e
      JOIN research.claims c ON c.id = e.claim_id
     WHERE c.proposition_facts ->> 'proposition' = %s
     ORDER BY e.claim_id, e.id
"""

ASSESSMENTS = """
    SELECT id, version, source_id, resource_id, record_kind_id, claim_type,
           proposition_kind, reliability, origin, reviewed_by, reviewed_at,
           stated_limitation, review_rubric_id, review_rubric_version
      FROM epistemic.reliability_assessments
     WHERE superseded_at IS NULL
     ORDER BY source_id, proposition_kind
"""

BASIS = """
    SELECT basis_type, document_title, summarized_finding, document_url,
           section_reference, retrieved_at
      FROM epistemic.reliability_assessment_basis
     WHERE assessment_id = %s
     ORDER BY basis_type, document_title
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare and write nothing")
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("REFUSED: DATABASE_URL is not set. This measures a deployment, not the tree.")
        return 1

    import psycopg
    from sros_claim_model import contract_for
    from sros_contracts import ClaimType, ReliabilityAssessmentOrigin, ReliabilityBasisType
    from sros_evidence_reliability import (
        ReliabilityAssessment,
        ReliabilityBasis,
        ReliabilityScope,
        resolve_reliability,
        rubric,
    )

    findings = json.loads(FINDINGS.read_text(encoding="utf-8"))

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(ROWS, (CONVERGENT_KIND,))
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, r, strict=True)) for r in cur.fetchall()]

        cur.execute(ASSESSMENTS)
        acols = [d[0] for d in cur.description]
        raw = [dict(zip(acols, r, strict=True)) for r in cur.fetchall()]
        for entry in raw:
            cur.execute(BASIS, (entry["id"],))
            bcols = [d[0] for d in cur.description]
            entry["_basis"] = [dict(zip(bcols, b, strict=True)) for b in cur.fetchall()]

        for row in rows:
            cur.execute(
                """SELECT o.observation_key
                     FROM nlp.signal_inputs i
                     JOIN acquisition.normalized_records n ON n.id = i.normalized_record_id
                     JOIN acquisition.raw_records o ON o.id = n.raw_record_id
                    WHERE i.signal_id = %s AND i.role = 'CONTRIBUTED'
                    ORDER BY o.observation_key""",
                (row["signal_id"],),
            )
            row["_witness"] = [r[0] for r in cur.fetchall()]

    # -- §0: group on the exact five-part key, measured rather than assumed ----
    scopes: dict[tuple, list[dict]] = {}
    for row in rows:
        facts = row["proposition_facts"] or {}
        key = (
            row["source_id"],
            row["resource_id"],
            row["record_kind_id"],
            row["claim_type"],
            facts.get("proposition", ""),
        )
        scopes.setdefault(key, []).append(row)

    live = [
        ReliabilityAssessment(
            id=str(a["id"]),
            scope=ReliabilityScope(
                source_id=a["source_id"],
                resource_id=a["resource_id"],
                record_kind_id=a["record_kind_id"],
                claim_type=ClaimType(a["claim_type"]),
                proposition_kind=a["proposition_kind"],
            ),
            version=int(a["version"]),
            reliability=float(a["reliability"]),
            origin=ReliabilityAssessmentOrigin(a["origin"]),
            rationale="(not reproduced here)",
            stated_limitation=a["stated_limitation"],
            reviewed_by=a["reviewed_by"],
            reviewed_at=a["reviewed_at"],
            basis=tuple(
                ReliabilityBasis(
                    basis_type=ReliabilityBasisType(b["basis_type"]),
                    document_title=b["document_title"],
                    summarized_finding=b["summarized_finding"],
                    document_url=b["document_url"],
                    section_reference=b["section_reference"],
                    retrieved_at=b["retrieved_at"],
                )
                for b in a["_basis"]
            ),
            calibration_dataset_ref=None,
            review_rubric_id=a["review_rubric_id"],
            review_rubric_version=a["review_rubric_version"],
        )
        for a in raw
    ]

    resolutions = []
    for key, members in scopes.items():
        scope = ReliabilityScope(
            source_id=key[0],
            resource_id=key[1],
            record_kind_id=key[2],
            claim_type=ClaimType(key[3]),
            proposition_kind=key[4],
        )
        resolution = resolve_reliability(scope=scope, candidates=live, supplied=None)
        resolutions.append(
            {
                "scope": dict(zip(SCOPE_FIELDS, key, strict=True)),
                "evidence_count": len(members),
                "claim_count": len({str(m["claim_id"]) for m in members}),
                "outcome": resolution.outcome.value,
                "reliability": resolution.reliability,
                "detail": resolution.detail,
            }
        )

    answered = [r for r in resolutions if r["outcome"] != "NO_APPLICABLE_ASSESSMENT"]
    if answered and OUT_JSON.exists():
        print(
            f"FROZEN   {OUT_JSON.name} is a preparation record and its question has been "
            "answered. Regenerating it would rewrite what the operator was asked."
        )
        return 0

    # -- §3: bidirectional leak checks over the real neighbourhood ------------
    probes = sorted({*OTHER_KINDS, DETAILED_KIND, CONVERGENT_KIND})
    leak_checks = []
    for assessment in live:
        for kind in probes:
            probe = ReliabilityScope(
                source_id=assessment.scope.source_id,
                resource_id=assessment.scope.resource_id,
                record_kind_id=assessment.scope.record_kind_id,
                claim_type=assessment.scope.claim_type,
                proposition_kind=kind,
            )
            outcome = resolve_reliability(scope=probe, candidates=[assessment], supplied=None)
            leak_checks.append(
                {
                    "assessment_id": assessment.id,
                    "assessment_source_id": assessment.scope.source_id,
                    "assessment_proposition_kind": assessment.scope.proposition_kind,
                    "probed_proposition_kind": kind,
                    "only_field_differing": "proposition_kind",
                    "scopes_identical": assessment.scope.proposition_kind == kind,
                    "resolved": outcome.reliability is not None,
                    "outcome": outcome.outcome.value,
                }
            )
    # And the other direction: every live assessment against the scope in review.
    convergent_scope = ReliabilityScope(
        source_id="wikimedia-pageviews",
        resource_id="metrics/pageviews/per-article/en.wikipedia.org",
        record_kind_id="content_request_count",
        claim_type=ClaimType.OBSERVED,
        proposition_kind=CONVERGENT_KIND,
    )
    for assessment in live:
        outcome = resolve_reliability(
            scope=convergent_scope, candidates=[assessment], supplied=None
        )
        leak_checks.append(
            {
                "assessment_id": assessment.id,
                "assessment_source_id": assessment.scope.source_id,
                "assessment_proposition_kind": assessment.scope.proposition_kind,
                "probed_proposition_kind": CONVERGENT_KIND,
                "only_field_differing": "the whole five-part key",
                "scopes_identical": False,
                "resolved": outcome.reliability is not None,
                "outcome": outcome.outcome.value,
            }
        )
    leaks = [c for c in leak_checks if c["resolved"] and not c["scopes_identical"]]

    judgement = json.loads(json.dumps(BLANK_JUDGEMENT))
    assignable = findings["software_assignable_states"]
    for dimension, entry in assignable.items():
        if dimension.startswith("$") or dimension == "not_assigned_and_why":
            continue
        judgement["dimension_states"][dimension] = entry["state"]

    contract = contract_for(CONVERGENT_KIND)
    by_claim: dict[str, list[dict]] = {}
    for row in rows:
        by_claim.setdefault(str(row["claim_id"]), []).append(row)

    document = {
        "$comment": (
            "Mission 1.44 §32, §33. The reliability question for ONE exact scope, prepared "
            "and NOT answered, under human-reliability-assessment-rubric@1.0.0. Every "
            "judgement field is blank except the one absence the rubric permits software to "
            "assert. The existing Wikimedia 0.65 appears only as HISTORICAL_OTHER_SCOPE_CONTEXT: "
            "it belongs to a different proposition kind, it is not a baseline, an anchor or a "
            "starting point, and it may not be copied. GENERATED -- edit "
            "wikimedia_convergent_reliability_findings.json and re-render."
        ),
        "artifact_version": "wikimedia-convergent-reliability-review-packet@1.0.0",
        "generated_by": "mission-1.44",
        "outcome": "READY_FOR_WIKIMEDIA_CONVERGENT_RELIABILITY_REVIEW",
        "review_rubric": {"id": rubric.RUBRIC_ID, "version": rubric.RUBRIC_VERSION},
        "reliability_scale": {
            "range": "[0.0, 1.0]",
            "threshold_labels": None,
            "$note": (
                "The architecture defines no meaning for any particular value and no "
                "threshold vocabulary. The rubric's two anchors are defined by what a value "
                "DOES in q = min(components), and it has no intermediate anchors."
            ),
        },
        "what_reliability_means": findings["what_reliability_means"],
        "measured_scopes": resolutions,
        "convergence_contract": {
            "contract_id": contract.contract_id if contract else None,
            "version": contract.version if contract else None,
            "identity_fields": list(contract.identity_fields) if contract else [],
            "witness_fields": list(contract.witness_fields) if contract else [],
            "establishes": contract.establishes if contract else None,
            "does_not_establish": list(contract.does_not_establish) if contract else [],
            "$note": (
                "Inspected, not modified. `audience_class` and `direction` remain proposition "
                "identity: one item over one period carries a different count per requester "
                "class, and an increase and a decrease are two assertions rather than a "
                "disagreement."
            ),
        },
        "affected_claims": [
            {
                "claim_id": claim_id,
                "claim_revision": members[0]["current_revision"],
                "content_id": (members[0]["proposition_facts"] or {}).get("content_id"),
                "direction": (members[0]["proposition_facts"] or {}).get("direction"),
                "audience_class": (members[0]["proposition_facts"] or {}).get("audience_class"),
                "content_platform": (members[0]["proposition_facts"] or {}).get("content_platform"),
                "witness_count": len(members),
                "evidence_ids": sorted(str(m["evidence_id"]) for m in members),
                "signal_ids": sorted(str(m["signal_id"]) for m in members),
            }
            for claim_id, members in sorted(by_claim.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        ],
        "affected_rows": [
            {
                "claim_id": str(row["claim_id"]),
                "evidence_id": str(row["evidence_id"]),
                "signal_id": str(row["signal_id"]),
                "witness_observation_keys": row["_witness"],
                "period_label_from": (row["proposition_facts"] or {}).get("period_label_from"),
                "period_label_to": (row["proposition_facts"] or {}).get("period_label_to"),
                "direction": row["direction"],
                "relevance": row["relevance"],
                "directness": row["directness"],
                "extraction_confidence": row["extraction_confidence"],
                "observation_category": row["observation_category"],
                "independence_state": row["independence_state"],
                "independence_group_id": row["independence_group_id"],
                "evidence_reliability_column": row["supplied"],
            }
            for row in rows
        ],
        "detailed_versus_convergent": findings["detailed_versus_convergent"],
        "documentary_review_matrix": findings["documentary_review_matrix"],
        "failure_modes": findings["failure_modes"],
        "existing_basis_applicability": findings["existing_basis_applicability"],
        "engineering_validation_inputs": findings["engineering_validation_inputs"],
        "what_a_value_would_not_do": findings["what_a_value_would_not_do"],
        "historical_other_scope_context": [
            {
                "$note": (
                    "An ACTUAL PERSISTED FACT about a DIFFERENT scope, recorded so a reviewer "
                    "can see what documentation was already accepted and which questions a "
                    "reviewer previously found material. It is NOT a baseline, an anchor, a "
                    "starting point, a prior or a range, and it may not be copied."
                ),
                "assessment_id": str(a["id"]),
                "version": a["version"],
                "scope": {field: a[field] for field in SCOPE_FIELDS},
                "origin": a["origin"],
                "reviewed_by": a["reviewed_by"],
                "reliability": float(a["reliability"]),
                "review_rubric": (
                    f"{a['review_rubric_id']}@{a['review_rubric_version']}"
                    if a["review_rubric_id"]
                    else None
                ),
                "predates_the_rubric": a["review_rubric_id"] is None,
                "is_the_scope_under_review": a["proposition_kind"] == CONVERGENT_KIND,
                "basis_rows": [
                    {
                        "basis_type": b["basis_type"],
                        "document_title": b["document_title"],
                        "section_reference": b["section_reference"],
                        "document_url": b["document_url"],
                        "retrieved_at": b["retrieved_at"].isoformat()
                        if b["retrieved_at"]
                        else None,
                        "summarized_finding": b["summarized_finding"],
                    }
                    for b in a["_basis"]
                ],
            }
            for a in raw
        ],
        "leak_checks": {
            "run": len(leak_checks),
            "leaks_found": len(leaks),
            "checks": leak_checks,
        },
        "software_assignable_states": findings["software_assignable_states"],
        "operator_worksheet": {
            "$note": (
                "§25-§29. Every field below is the reviewer's, except the one absence the "
                "rubric permits software to assert about what this review's basis CONTAINS."
            ),
            "scope": dict(
                zip(
                    SCOPE_FIELDS,
                    (
                        "wikimedia-pageviews",
                        "metrics/pageviews/per-article/en.wikipedia.org",
                        "content_request_count",
                        "OBSERVED",
                        CONVERGENT_KIND,
                    ),
                    strict=True,
                )
            ),
            "review_rubric": {"id": rubric.RUBRIC_ID, "version": rubric.RUBRIC_VERSION},
            "dimension_state_options": [state.value for state in rubric.ReviewState],
            "hard_stops": [
                {
                    "id": stop.id,
                    "condition": stop.condition,
                    "factual_trigger_present": None,
                    "reviewer_decision": None,
                }
                for stop in rubric.HARD_STOPS
            ],
            "material_unknowns": [
                {
                    **candidate,
                    "materiality_question": rubric.MATERIALITY_QUESTION,
                    "permitted_answers": list(rubric.MATERIALITY_ANSWERS),
                    "reviewer_answer": None,
                }
                for candidate in findings["material_unknown_candidates"]
            ],
            "numeric_judgement_gate_options": [
                outcome.value for outcome in rubric.NumericJudgementGate
            ],
            "judgement": judgement,
            "if_the_gate_is_not_permitted": (
                f"Leave the assessment absent. All {len(rows)} Evidence rows across "
                f"{len(by_claim)} Claims stay NON_SCORABLE, the resolver keeps returning "
                "NO_APPLICABLE_ASSESSMENT, and the six Claims remain UNAVAILABLE. That is the "
                "designed behaviour rather than a gap, and it is a complete review."
            ),
            "rubric_provenance_for_a_future_assessment": {
                "review_rubric_id": rubric.RUBRIC_ID,
                "review_rubric_version": rubric.RUBRIC_VERSION,
                "$note": (
                    "Migration 0032 added these columns, so an assessment for this scope CAN "
                    "record which procedure produced it. The two pre-rubric assessments keep "
                    "NULL, which is true rather than missing."
                ),
            },
        },
        "what_this_packet_is_not": findings["what_this_packet_is_not"],
    }

    rendered = json.dumps(document, indent=2, ensure_ascii=False, default=str) + "\n"
    markdown = render(document)

    if args.check:
        drift = []
        for path, expected in ((OUT_JSON, rendered), (OUT_MD, markdown)):
            if not path.exists():
                print(f"REFUSED: {path.name} does not exist; run without --check first")
                return 1
            if path.read_text(encoding="utf-8") != expected:
                drift.append(path.name)
        if drift:
            for name in drift:
                print(f"DRIFT    {name} does not match the live canonical state")
            return 1
        print(f"ok       {OUT_JSON.name} and {OUT_MD.name} match the live canonical state")
        return 0

    OUT_JSON.write_text(rendered, encoding="utf-8")
    OUT_MD.write_text(markdown, encoding="utf-8")

    print(f"convergent Evidence rows   : {len(rows)}")
    print(f"distinct Claims            : {len(by_claim)}")
    print(
        f"witness cardinalities      : {sorted((len(m) for m in by_claim.values()), reverse=True)}"
    )
    print(f"distinct reliability scopes: {len(scopes)}")
    for entry in resolutions:
        print(
            f"  {entry['scope']['proposition_kind'][:52]:54} rows={entry['evidence_count']} "
            f"{entry['outcome']}"
        )
    print(f"\nleak checks: {len(leak_checks)} run, {len(leaks)} leak(s)")
    states = judgement["dimension_states"]
    print(
        f"dimension states: {sum(1 for v in states.values() if v is None)} blank, "
        f"{[k for k, v in states.items() if v is not None]} software-assigned"
    )
    print(
        f"reliability={judgement['reliability']} reviewer={judgement['reviewed_by']} "
        f"gate={judgement['numeric_judgement_gate']}"
    )
    print(f"\nwrote {OUT_JSON.name}")
    print(f"wrote {OUT_MD.name}")
    return 0


def render(doc: dict) -> str:
    lines: list[str] = []
    scope = doc["operator_worksheet"]["scope"]
    measured = doc["measured_scopes"][0]

    lines.append("# The Wikimedia convergent reliability question")
    lines.append("")
    lines.append(
        f"**Status:** `{doc['outcome']}`. Prepared by Mission 1.44 under "
        f"**`{doc['review_rubric']['id']}@{doc['review_rubric']['version']}`**. "
        "**No value is supplied, suggested or implied.**"
    )
    lines.append("")
    lines.append(f"**Machine-readable:** [{OUT_JSON.name}]({OUT_JSON.name})")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. The question")
    lines.append("")
    lines.append(f"> **{doc['what_reliability_means']['the_question']}**")
    lines.append("")
    lines.append("It is **not**: " + " · ".join(doc["what_reliability_means"]["it_is_not"]) + ".")
    lines.append("")
    lines.append("**The scope, all five fields, matched in full or not at all:**")
    lines.append("")
    lines.append("```text")
    for key, value in scope.items():
        lines.append(f"{key:18}{value}")
    lines.append("```")
    lines.append("")
    lines.append(
        f"It binds **{measured['evidence_count']} Evidence rows across "
        f"{measured['claim_count']} Claims**, and the resolver currently returns "
        f"**`{measured['outcome']}`**."
    )
    lines.append("")
    lines.append(doc["what_reliability_means"]["scope_is_five_fields"])
    lines.append("")
    lines.append("| Claim | article | direction | requester class | witnesses |")
    lines.append("|---|---|---|---|---:|")
    for claim in doc["affected_claims"]:
        lines.append(
            f"| `{claim['claim_id'][:8]}` | {claim['content_id']} | {claim['direction']} "
            f"| `{claim['audience_class']}` | **{claim['witness_count']}** |"
        )
    lines.append("")
    lines.append(
        "**One judgement binds every row above.** The scope carries no article, no "
        "direction, no requester class, no period and no witness count, so there is one "
        "question here rather than six — and **a Claim with four witnesses is not thereby a "
        "more dependable measurement.** Cardinality belongs to aggregation; reliability "
        "belongs to measurement crossed with proposition."
    )
    lines.append("")
    lines.append("## 2. Why the existing Wikimedia 0.65 does not answer this")
    lines.append("")
    historical = [
        entry
        for entry in doc["historical_other_scope_context"]
        if entry["scope"]["source_id"] == "wikimedia-pageviews"
    ]
    for entry in historical:
        lines.append(
            f"There is a `{entry['origin']}` assessment at **{entry['reliability']}** for "
            f"`{entry['scope']['proposition_kind']}`, reviewed by `{entry['reviewed_by']}`"
            + (
                ", predating the rubric and therefore recording no rubric provenance"
                if entry["predates_the_rubric"]
                else ""
            )
            + "."
        )
    lines.append("")
    lines.append(
        "**It does not bind here, it must not be copied, and it is not a baseline, an anchor "
        "or a starting point.** Four of the five scope fields are identical; "
        "`proposition_kind` differs, and that is sufficient. There is no closest-match "
        "logic, no fallback and no source-wide coefficient."
    )
    lines.append("")
    lines.append(
        f"**{doc['leak_checks']['run']} leak checks, {doc['leak_checks']['leaks_found']} "
        "leaks** — run in both directions across every proposition kind in the corpus."
    )
    lines.append("")
    lines.append("### What changed, and what did not")
    lines.append("")
    delta = doc["detailed_versus_convergent"]
    lines.append(f"- **Detailed:** {delta['detailed_asserts']}.")
    lines.append(f"- **Convergent:** {delta['convergent_asserts']}.")
    lines.append(f"- **What moved:** {delta['what_moved']}")
    lines.append(f"- **What did not change:** {delta['what_did_not_change']}")
    lines.append("")
    lines.append("**What convergence newly raises:**")
    lines.append("")
    for item in delta["reliability_questions_that_are_NEW"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 3. What the held documents establish")
    lines.append("")
    lines.append("| question | answer | open? |")
    lines.append("|---|---|---|")
    for entry in doc["documentary_review_matrix"]:
        mark = "**OPEN**" if entry["open"] else "no"
        lines.append(f"| {entry['question']} | {entry['answer']} | {mark} |")
    lines.append("")
    lines.append(
        "**Nothing was fetched.** Both documents were already attached to the detailed "
        "assessment, and the convergent proposition reads the same measurement through the "
        "same rules."
    )
    lines.append("")
    lines.append("### Applicability of the held basis rows")
    lines.append("")
    for entry in doc["existing_basis_applicability"]:
        lines.append(
            f"- **{entry['document_title']}** (`{entry['section_reference']}`, "
            f"`{entry['basis_type']}`) — **{entry['verdict']}**. {entry['why']}"
        )
    lines.append("")
    lines.append("## 4. Failure modes")
    lines.append("")
    lines.append(
        "| failure mode | dimension | origin | documented | effect on the convergent proposition |"
    )
    lines.append("|---|---|---|---|---|")
    for mode in doc["failure_modes"]:
        lines.append(
            f"| {mode['failure_mode']} | `{mode['rubric_dimension']}` | `{mode['origin']}` "
            f"| {'yes' if mode['documented'] else '**no**'} "
            f"| {mode['effect_on_convergent_proposition']} |"
        )
    lines.append("")
    lines.append("## 5. Engineering validation is recorded separately, and is not basis")
    lines.append("")
    validation = doc["engineering_validation_inputs"]
    for item in validation["inputs"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append(
        f"**`{validation['classification']}` — "
        f"`may_be_used_as_reliability_basis: {validation['may_be_used_as_reliability_basis']}`.** "
        f"{validation['what_they_establish'].capitalize()} It establishes "
        f"**{validation['what_they_do_not_establish']}**"
    )
    lines.append("")
    lines.append(
        "**Independence stays `UNKNOWN` on all "
        f"{len(doc['affected_rows'])} rows with 0 groups.** Different days, different "
        "articles and different directions do not establish independence: one publisher, one "
        "collection method and one counting methodology remain shared provenance."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 6. Operator worksheet")
    lines.append("")
    worksheet = doc["operator_worksheet"]
    lines.append("**Scope**")
    lines.append("")
    lines.append("```text")
    for key, value in worksheet["scope"].items():
        lines.append(f"{key:18}{value}")
    lines.append("```")
    lines.append("")
    lines.append("### 6.1 The dimension profile")
    lines.append("")
    lines.append("States: " + " · ".join(f"`{s}`" for s in worksheet["dimension_state_options"]))
    lines.append("")
    lines.append("```text")
    for dimension, state in worksheet["judgement"]["dimension_states"].items():
        shown = state if state else "______________________________"
        lines.append(f"{dimension:32} {shown}")
    lines.append("```")
    lines.append("")
    assignable = doc["software_assignable_states"]
    assigned = [k for k in assignable if not k.startswith("$") and k != "not_assigned_and_why"]
    for dimension in assigned:
        lines.append(
            f"**`{dimension}` is pre-filled `{assignable[dimension]['state']}`**, and it is "
            "the only one. " + assignable[dimension]["justification"]
        )
        lines.append("")
    lines.append("**Deliberately left blank, and why:**")
    lines.append("")
    for dimension, reason in assignable["not_assigned_and_why"].items():
        lines.append(f"- **`{dimension}`** — {reason}")
    lines.append("")
    lines.append("### 6.2 Material unknowns")
    lines.append("")
    for unknown in worksheet["material_unknowns"]:
        lines.append(
            f"**`{unknown['rubric_dimension']}`** — {unknown['unknown']}  "
            f"(documentary status: `{unknown['documentary_status']}`)"
        )
        lines.append("")
        lines.append(f"> {unknown['materiality_question']}")
        lines.append("")
        lines.append("```text")
        lines.append("YES / NO / UNSURE   ______")
        lines.append("```")
        lines.append("")
    lines.append("### 6.3 Hard stops")
    lines.append("")
    lines.append("| hard stop | condition | triggered? |")
    lines.append("|---|---|---|")
    for stop in worksheet["hard_stops"]:
        lines.append(f"| `{stop['id']}` | {stop['condition']} | ______ |")
    lines.append("")
    lines.append(
        "**A limitation is not a hard stop.** Each of these makes a numeric judgement "
        "*unavailable* because the reliability question has no answer in that situation, "
        "never because the answer would be low."
    )
    lines.append("")
    lines.append("### 6.4 The gate, and the judgement")
    lines.append("")
    lines.append(
        "Options: " + " · ".join(f"`{o}`" for o in worksheet["numeric_judgement_gate_options"])
    )
    lines.append("")
    lines.append("```text")
    lines.append(
        f"NUMERIC_JUDGEMENT_GATE           {worksheet['judgement']['numeric_judgement_gate']}"
    )
    lines.append("")
    lines.append("Only if the gate is PERMITTED:")
    lines.append("")
    lines.append("Reliability [0.0, 1.0]           ______________________________")
    lines.append("Rationale                        ______________________________")
    lines.append("Stated limitation                ______________________________")
    lines.append("Reviewer                         ______________________________")
    lines.append("Review timestamp                 ______________________________")
    lines.append("```")
    lines.append("")
    lines.append(
        f"**If the gate is not `NUMERIC_JUDGEMENT_PERMITTED`** — {worksheet['if_the_gate_is_not_permitted']}"
    )
    lines.append("")
    provenance = worksheet["rubric_provenance_for_a_future_assessment"]
    lines.append(
        f"A future assessment for this scope would record "
        f"`{provenance['review_rubric_id']}@{provenance['review_rubric_version']}`. "
        f"{provenance['$note']}"
    )
    lines.append("")
    lines.append("## 7. What a value here would not do")
    lines.append("")
    for item in doc["what_a_value_would_not_do"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**This packet is:** " + " ".join(doc["what_this_packet_is_not"]))
    lines.append("")
    lines.append(
        "**Nothing above is pre-filled with a judgement**, and the reviewer is not inferred "
        "from a git author, a PR author, an OS username, the existing assessment or any "
        "conversation."
    )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
