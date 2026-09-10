"""Reconcile the canonical Opportunity with current scorability, by supersession (Mission 1.78).

A historical revision may remain true about what the system believed then. A new revision
must be true about what the system can establish now. Revision 1 of the docker Opportunity
was written on 2026-09-02 over a packet whose every row read NON_SCORABLE from a NULL column;
the reviewed Wikimedia assessments arrived on 2026-09-03 and 2026-09-04, and Mission 1.77
made the Opportunity path resolve reliability late from lineage. So one sentence of revision 1
is stale, and the reconciliation is exactly this:

    revision 1   UNCHANGED, byte for byte, still readable by number
    revision 2   the same hypothesis, the same seven cited rows, the stale sentences replaced
                 by sentences computed from the current resolver, and nothing stronger

What this script refuses to do, structurally: it takes the hypothesis text from revision 1
and never composes one; it takes the cited Evidence set from revision 1's links and never
widens it; it takes eligibility from the CURRENT preparation record, which the canonical
runner produced through the late-resolution path; it calls no model; it writes no score; it
creates no independence group; it never UPDATEs a revision. Reliability changes whether a row
may enter quantitative aggregation, not what the row establishes.

    uv run python infrastructure/scripts/reconcile_opportunity_reliability.py           # dry run
    uv run python infrastructure/scripts/reconcile_opportunity_reliability.py --apply   # ONE revision

Reads a deployment, so it is an OPERATOR gate and not a CI gate.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "data"
PREPARATION_V1 = DOCS / "opportunity-preparation-v1.json"
PREPARATION_V2 = DOCS / "opportunity-preparation-v2.json"
OUT = DOCS / "opportunity-reliability-reconciliation-v1.json"
WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"

PROCEDURE = "opportunity-reliability-reconciliation@1.0.0"
REASON = "RELIABILITY_APPLICABILITY_RECONCILIATION"
MISSION = "1.78"
PRIOR_MISSION_FINDING = "docs/data/wikimedia-measurement-scope-binding-v1.json"

# The statement fields a reconciliation carries over verbatim. A change to any of them is a
# resynthesis, which this script cannot perform and must not imitate.
CARRIED_VERBATIM = (
    "target_actor",
    "observed_need_or_change",
    "candidate_intervention",
    "hypothesis_statement",
    "supported_dimensions",
    "unsupported_dimensions",
    "uncertainties",
)

STALE_MARKERS = ("MISSING_RELIABILITY", "no reviewed reliability applies", "NON_SCORABLE")


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(value):
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def _fetch(cur, query, params=()):
    cur.execute(query, params)
    columns = [d[0] for d in cur.description]
    return [dict(zip(columns, row, strict=True)) for row in cur.fetchall()]


def _classify_limitation(text: str) -> str:
    """Which revision-1 sentences Mission 1.77 made false. Judged on markers, then read."""
    if any(marker in text for marker in STALE_MARKERS):
        return "STALE_DUE_TO_RELIABILITY_RESOLUTION_FIX"
    return "NOT_RELATED_TO_1_77"


def _current_limitations(rows: list[dict], previous: list[str]) -> tuple[list[str], list[dict]]:
    """Replace only what is proven stale, and derive the replacement from the rows."""
    scorable = [r for r in rows if r["scorable"]]
    non_scorable = [r for r in rows if not r["scorable"]]
    by_source_unresolved = sorted({r["source_id"] for r in non_scorable})
    reliabilities = sorted({r["resolved_reliability"] for r in scorable})
    kept: list[str] = []
    audit: list[dict] = []
    for sentence in previous:
        verdict = _classify_limitation(sentence)
        audit.append({"revision_1_sentence": sentence, "classification": verdict})
        if verdict == "NOT_RELATED_TO_1_77":
            kept.append(sentence)
    replacement = (
        f"{len(scorable)} of {len(rows)} supporting Evidence rows carry a reviewed reliability "
        f"({', '.join(str(v) for v in reliabilities)}), resolved late from their acquisition "
        "lineage and bound to the assessment that produced it (ADR-026, Mission 1.77); "
        f"{len(non_scorable)} {'remains' if len(non_scorable) == 1 else 'remain'} NON_SCORABLE "
        "with no applicable assessment "
        f"({', '.join(by_source_unresolved)}). Scorable is not scored: REFERENCE_PROFILE_V1 is "
        "UNCALIBRATED, no Score exists in this repository, none is persisted, and no ranking "
        "exists."
    )
    return [replacement, *kept], audit


def _reasoning_summary(previous: str, rows: list[dict]) -> tuple[str, dict]:
    """The one sentence of the reasoning that Mission 1.77 made false, replaced by a count.

    Revision 1's last sentence says both source families carry MISSING_RELIABILITY across
    all seven rows. The independence half is still true and stays; the reliability half is
    replaced by what the resolver returns now. Nothing else in the reasoning is touched.
    """
    sentences = previous.split(". ")
    stale = [s for s in sentences if "MISSING_RELIABILITY" in s]
    if len(stale) != 1:
        raise SystemExit(
            f"REFUSED: expected exactly one stale reasoning sentence, found {len(stale)}; "
            "a reconciliation that cannot locate the sentence it replaces must not guess"
        )
    scorable = sum(1 for r in rows if r["scorable"])
    replacement = (
        f"Both source families (forum, knowledge) carry UNKNOWN independence across all "
        f"{len(rows)} rows; {scorable} of the {len(rows)} rows now resolve a reviewed reliability "
        f"late from lineage and {len(rows) - scorable} "
        f"{'does' if len(rows) - scorable == 1 else 'do'} not, so quantitative aggregation is "
        "possible for part of this evidence and no scoring or confidence claim is attached to "
        "any of it here"
    )
    if stale[0].endswith("."):
        replacement += "."
    rebuilt = ". ".join(replacement if s is stale[0] else s for s in sentences)
    return rebuilt, {"revision_1_sentence": stale[0], "replacement": replacement}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="persist exactly one revision")
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("REFUSED: DATABASE_URL is not set. This reads a deployment, not the tree.")
        return 1
    if not PREPARATION_V2.exists():
        print(
            "REFUSED: the current preparation record does not exist; run the canonical runner first"
        )
        return 1

    import psycopg

    preparation = json.loads(PREPARATION_V2.read_text(encoding="utf-8"))
    if preparation.get("supersedes") != f"docs/data/{PREPARATION_V1.name}":
        print("REFUSED: the preparation record does not supersede v1")
        return 1
    rows_by_id = {r["evidence_id"]: r for r in preparation["rows"]}

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        counters_before = _counters(cur)
        opportunities = _fetch(cur, "SELECT * FROM research.opportunities ORDER BY created_at")
        if len(opportunities) != 1:
            print(f"REFUSED: {len(opportunities)} Opportunities; this reconciliation expects one")
            return 1
        opportunity = opportunities[0]
        revisions = _fetch(
            cur,
            "SELECT * FROM research.opportunity_hypothesis_revisions WHERE opportunity_id = %s"
            " ORDER BY revision",
            (opportunity["id"],),
        )
        # A reconciliation revision already written is DESCRIBED, never written again: the
        # record is rebuilt from the deployment, and --apply is refused. One revision, once.
        existing = [r for r in revisions if str(r["procedure_version"]).startswith(PROCEDURE)]
        if len(existing) > 1:
            print(f"REFUSED: {len(existing)} reconciliation revisions exist; expected at most one")
            return 1
        current = revisions[-1] if not existing else revisions[revisions.index(existing[0]) - 1]
        links = _fetch(
            cur,
            "SELECT * FROM research.opportunity_hypothesis_evidence WHERE revision_id = %s"
            " ORDER BY evidence_id",
            (current["id"],),
        )
        assessments = _fetch(
            cur,
            "SELECT id, source_id, proposition_kind, reliability, created_at"
            " FROM epistemic.reliability_assessments WHERE superseded_at IS NULL"
            " ORDER BY created_at",
        )

    # --------------------------------------------------- audit of the current revision
    stale_limitations = [
        s
        for s in current["epistemic_limitations"]
        if _classify_limitation(s) != "NOT_RELATED_TO_1_77"
    ]
    if not stale_limitations:
        record = {
            "primary_outcome": "OPPORTUNITY_LIMITATION_NOT_STALE_UNDER_CANONICAL_SEMANTICS",
            "current_revision": current["revision"],
        }
        OUT.write_text(json.dumps(record, indent=2, default=_json) + "\n", encoding="utf-8")
        print("nothing stale; no revision written")
        return 0

    linked_rows = []
    for link in links:
        eid = str(link["evidence_id"])
        row = rows_by_id.get(eid)
        if row is None:
            print(f"REFUSED: linked Evidence {eid} is absent from the current preparation")
            return 1
        resolution = row["reliability_resolution"]
        linked_rows.append(
            {
                "evidence_id": eid,
                "claim_id": str(link["claim_id"]),
                "source_id": row["source_id"],
                "source_family": row["source_family"],
                "signal_type_id": row["signal_type_id"],
                "dimensions": row["dimensions"],
                "eligibility_at_revision_1": link["eligibility_at_citation"],
                "eligibility_now": row["eligibility"],
                "relevance": "CITED_BY_REVISION_1",
                "reliability_outcome": resolution["outcome"],
                "resource_basis": resolution["resource_basis"],
                "resource_id": resolution["resource_id"],
                "assessment_id": resolution["assessment_id"],
                "resolved_reliability": _resolved_value(resolution, assessments),
                "scorable": bool(row["scorable"]),
                "independence_state": row["independence_state"],
                "missing_factors": row["missing_factors"],
                "reason": (
                    "the current resolver binds this row to a current assessment on all five "
                    "scope parts"
                    if resolution["outcome"] == "RESOLVED"
                    else "no current assessment covers this row's measurement-and-purpose scope"
                ),
            }
        )

    limitations, limitation_audit = _current_limitations(
        linked_rows, current["epistemic_limitations"]
    )
    reasoning, reasoning_audit = _reasoning_summary(current["reasoning_summary"], linked_rows)

    # ------------------------------------------ the current packet, for the census only
    docker = next(
        p for p in preparation["packets"] if p["packet_id"] == _packet_for(preparation, links)
    )
    packet_rows = {r["evidence_id"]: r for r in preparation["rows"]}
    linked_ids = {r["evidence_id"] for r in linked_rows}
    not_linked = []
    for eid in _packet_evidence_ids(preparation, docker):
        if eid in linked_ids:
            continue
        row = packet_rows[eid]
        not_linked.append(
            {
                "evidence_id": eid,
                "source_id": row["source_id"],
                "signal_type_id": row["signal_type_id"],
                "eligibility_now": row["eligibility"],
                "scorable": bool(row["scorable"]),
                "classification": "REQUIRES_NEW_SEMANTIC_JUDGEMENT_BEFORE_INCLUSION",
                "why": (
                    "in the current packet and not cited by revision 1; whether it bears on the "
                    "hypothesis is a synthesis judgement this reconciliation does not make"
                ),
            }
        )

    scoring_ready = docker["sufficiency"]["scoring_ready"]
    plan = {
        "opportunity_id": str(opportunity["id"]),
        "prior_revision_id": str(current["id"]),
        "prior_revision": current["revision"],
        "revision": current["revision"] + 1,
        "procedure_version": (
            f"{PROCEDURE}|reason={REASON}|prior_revision={current['id']}|mission_finding="
            f"{PRIOR_MISSION_FINDING}|resolver=sros_evidence_reliability.lineage|preparation="
            f"{preparation['artifact_version']}|preparation_record=docs/data/{PREPARATION_V2.name}"
            f"|census=rows:{preparation['totals']['evidence_rows_inspected']},scoring:"
            f"{preparation['totals']['eligible_scoring']}|linked={len(linked_rows)}"
        ),
        "model_version": None,
        "prompt_version": None,
        "created_by": f"mission-{MISSION}",
        "carried_verbatim": list(CARRIED_VERBATIM),
        "epistemic_limitations": limitations,
        "reasoning_summary": reasoning,
        "links": [
            {
                "evidence_id": r["evidence_id"],
                "claim_id": r["claim_id"],
                "eligibility_at_citation": r["eligibility_now"],
                "dimensions": current["supported_dimensions"],
            }
            for r in linked_rows
        ],
    }

    applied = None
    if existing and args.apply:
        print(
            f"REFUSED: revision {existing[0]['revision']} already reconciles revision {current['revision']}"
        )
        return 1
    if args.apply or existing:
        revision_id = str(existing[0]["id"]) if existing else str(uuid.uuid4())
    if args.apply:
        with psycopg.connect(url) as conn:
            role = os.environ.get("APP_DB_ROLE", "sros_app")
            with conn.transaction():
                conn.execute(f"SET LOCAL ROLE {role}")
                conn.execute("SELECT set_config('app.workspace_id', %s, true)", (WORKSPACE_ID,))
                conn.execute(
                    """INSERT INTO research.opportunity_hypothesis_revisions
                           (id, workspace_id, opportunity_id, revision, target_actor,
                            observed_need_or_change, candidate_intervention,
                            hypothesis_statement, reasoning_summary,
                            supported_dimensions, unsupported_dimensions,
                            epistemic_limitations, uncertainties,
                            procedure_version, model_version, prompt_version, created_by)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, %s)""",
                    (
                        revision_id,
                        WORKSPACE_ID,
                        str(opportunity["id"]),
                        plan["revision"],
                        current["target_actor"],
                        current["observed_need_or_change"],
                        current["candidate_intervention"],
                        current["hypothesis_statement"],
                        reasoning,
                        list(current["supported_dimensions"]),
                        list(current["unsupported_dimensions"]),
                        limitations,
                        list(current["uncertainties"]),
                        plan["procedure_version"],
                        plan["created_by"],
                    ),
                )
                for link in plan["links"]:
                    conn.execute(
                        """INSERT INTO research.opportunity_hypothesis_evidence
                               (id, workspace_id, revision_id, evidence_id, claim_id,
                                eligibility_at_citation, dimensions)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (
                            str(uuid.uuid4()),
                            WORKSPACE_ID,
                            revision_id,
                            link["evidence_id"],
                            link["claim_id"],
                            link["eligibility_at_citation"],
                            list(link["dimensions"]),
                        ),
                    )
    if args.apply or existing:
        with psycopg.connect(url) as conn, conn.cursor() as cur:
            counters_after = _counters(cur)
            written = _fetch(
                cur,
                "SELECT * FROM research.opportunity_hypothesis_revisions WHERE id = %s",
                (revision_id,),
            )[0]
            still_first = _fetch(
                cur,
                "SELECT * FROM research.opportunity_hypothesis_revisions WHERE id = %s",
                (current["id"],),
            )[0]
            newest = _fetch(
                cur,
                "SELECT id, revision FROM research.opportunity_hypothesis_revisions"
                " WHERE opportunity_id = %s ORDER BY revision DESC LIMIT 1",
                (opportunity["id"],),
            )[0]
            written_links = _fetch(
                cur,
                "SELECT evidence_id, eligibility_at_citation FROM"
                " research.opportunity_hypothesis_evidence WHERE revision_id = %s ORDER BY evidence_id",
                (revision_id,),
            )
        applied = {
            "revision_2_id": revision_id,
            "revision_2_number": written["revision"],
            "revision_2_created_at": written["created_at"].isoformat(),
            "revision_2_row": {k: _json(v) for k, v in written.items()},
            "written_by_this_invocation": bool(args.apply),
            "revision_1_after": {k: _json(v) for k, v in still_first.items()},
            "revision_1_byte_identical_after": {k: _json(v) for k, v in still_first.items()}
            == {k: _json(v) for k, v in current.items()},
            "newest_revision_by_index": {"id": str(newest["id"]), "revision": newest["revision"]},
            "links_written": [
                {
                    "evidence_id": str(w["evidence_id"]),
                    "eligibility_at_citation": w["eligibility_at_citation"],
                }
                for w in written_links
            ],
            "counters_after": counters_after,
        }
    else:
        counters_after = counters_before

    record = {
        "$comment": (
            "Mission 1.78. Revision 2 of the docker Opportunity, by supersession: the same "
            "hypothesis, the same seven cited rows, the stale reliability sentences replaced by "
            "sentences computed from the current resolver. Revision 1 is untouched."
        ),
        "record_version": "1.0.0",
        "mission": MISSION,
        "procedure_version": PROCEDURE,
        "revision_reason": REASON,
        "measured_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "applied": bool(args.apply),
        "historical_artifacts": {
            "preparation_v1": {
                "path": f"docs/data/{PREPARATION_V1.name}",
                "sha256": _sha256(PREPARATION_V1),
            },
            "preparation_v2": {
                "path": f"docs/data/{PREPARATION_V2.name}",
                "artifact_version": preparation["artifact_version"],
            },
        },
        "opportunity": {k: _json(v) for k, v in opportunity.items()},
        "revision_1": {k: _json(v) for k, v in current.items()},
        "revision_1_links": [{k: _json(v) for k, v in link.items()} for link in links],
        "revision_1_audit": {
            "limitations": limitation_audit,
            "reasoning_summary": {
                **reasoning_audit,
                "classification": "STALE_DUE_TO_RELIABILITY_RESOLUTION_FIX",
            },
            "carried_verbatim": list(CARRIED_VERBATIM),
            "hypothesis_statement_changed": False,
            "why_stale": [
                {
                    "assessment_id": str(a["id"]),
                    "source_id": a["source_id"],
                    "proposition_kind": a["proposition_kind"],
                    "reliability": float(a["reliability"]),
                    "created_at": a["created_at"].isoformat(),
                    "after_revision_1": a["created_at"] > current["created_at"],
                }
                for a in assessments
            ],
        },
        "current_evidence": {
            "linked_by_revision_1_and_carried": linked_rows,
            "in_current_packet_not_linked": not_linked,
            "packet_id_now": docker["packet_id"],
            "packet_id_at_revision_1": opportunity["packet_id"],
            "packet_size_now": docker["size"],
            "packet_eligibility_now": docker["eligibility_counts"],
            "scoring_ready_now_per_contract": scoring_ready,
            "scoring_ready_contract": (
                "SufficiencyResult.scoring_ready = scoring_eligible_rows >= 2, a property of the "
                "PACKET; it authorises nothing, REFERENCE_PROFILE_V1 is UNCALIBRATED and no score "
                "is persisted"
            ),
        },
        "census": {
            "total_evidence": preparation["totals"]["evidence_rows_inspected"],
            "scorable_evidence": preparation["totals"]["eligible_scoring"],
            "non_scorable_evidence": preparation["totals"]["evidence_rows_inspected"]
            - preparation["totals"]["eligible_scoring"],
            "linked_evidence": len(linked_rows),
            "scorable_linked_evidence": sum(1 for r in linked_rows if r["scorable"]),
            "non_scorable_linked_evidence": sum(1 for r in linked_rows if not r["scorable"]),
            "linked_dimensions": sorted({d for r in linked_rows for d in r["dimensions"]}),
            "linked_source_families": sorted({r["source_family"] for r in linked_rows}),
            "linked_reliability_distribution": _distribution(linked_rows),
            "linked_independence_states": sorted({r["independence_state"] for r in linked_rows}),
        },
        "revision_2_plan": plan,
        "reconciled": applied is not None,
        "revision_2_applied": applied,
        "counters": {
            "before_this_invocation": counters_before,
            "after": counters_after,
            # What revision 2 wrote is exactly one revision row and its link rows, so the
            # state before the reconciliation is the state after, less those. Derived rather
            # than remembered, because a describing run has no memory of the applying one.
            "before_reconciliation": (
                {
                    **counters_after,
                    "opportunity_revisions": counters_after["opportunity_revisions"] - 1,
                    "opportunity_evidence_links": counters_after["opportunity_evidence_links"]
                    - len(applied["links_written"]),
                }
                if applied
                else counters_before
            ),
        },
    }
    OUT.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, default=_json) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote     {OUT.relative_to(ROOT)}  applied={bool(args.apply)}")
    print(f"linked    {len(linked_rows)}  scorable {record['census']['scorable_linked_evidence']}")
    print(
        f"revisions {counters_before['opportunity_revisions']} -> {counters_after['opportunity_revisions']}"
    )
    return 0


def _resolved_value(resolution: dict, assessments: list[dict]):
    if resolution["outcome"] != "RESOLVED":
        return None
    match = next(a for a in assessments if str(a["id"]) == resolution["assessment_id"])
    return float(match["reliability"])


def _distribution(rows: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        key = str(r["resolved_reliability"]) if r["scorable"] else "NONE"
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def _packet_for(preparation: dict, links: list[dict]) -> str:
    """The current packet holding revision 1's cited rows. Refuse if they straddle two."""
    wanted = {str(link["evidence_id"]) for link in links}
    holding = [
        p["packet_id"]
        for p in preparation["packets"]
        if wanted & set(_packet_evidence_ids(preparation, p))
    ]
    if len(holding) != 1:
        raise SystemExit(f"REFUSED: the cited rows sit in {len(holding)} current packets")
    return holding[0]


def _packet_evidence_ids(preparation: dict, packet: dict) -> list[str]:
    return list(packet["evidence_ids"])


def _counters(cur) -> dict[str, object]:
    out: dict[str, object] = {}
    for name, query in (
        ("opportunities", "SELECT count(*) FROM research.opportunities"),
        ("opportunity_revisions", "SELECT count(*) FROM research.opportunity_hypothesis_revisions"),
        (
            "opportunity_evidence_links",
            "SELECT count(*) FROM research.opportunity_hypothesis_evidence",
        ),
        ("raw_records", "SELECT count(*) FROM acquisition.raw_records"),
        ("normalized_records", "SELECT count(*) FROM acquisition.normalized_records"),
        ("signals", "SELECT count(*) FROM nlp.signals"),
        ("claims", "SELECT count(*) FROM research.claims"),
        ("claim_revisions", "SELECT count(*) FROM research.claim_revisions"),
        ("evidence", "SELECT count(*) FROM scoring.evidence"),
        (
            "evidence_reliability_written",
            "SELECT count(*) FROM scoring.evidence WHERE reliability IS NOT NULL",
        ),
        ("reliability_assessments", "SELECT count(*) FROM epistemic.reliability_assessments"),
        (
            "reliability_assessment_basis_rows",
            "SELECT count(*) FROM epistemic.reliability_assessment_basis",
        ),
        (
            "independence_groups",
            "SELECT count(DISTINCT independence_group_id) FROM scoring.evidence WHERE independence_group_id IS NOT NULL",
        ),
        ("threshold_registrations", "SELECT count(*) FROM research.threshold_registrations"),
        ("claim_derivations", "SELECT count(*) FROM research.claim_derivations"),
        (
            "proposition_evaluation_refusals",
            "SELECT count(*) FROM research.proposition_evaluation_refusals",
        ),
        ("embeddings", "SELECT count(*) FROM nlp.embedding_provenance"),
        ("sources", "SELECT count(*) FROM registry.sources"),
        ("source_reviews", "SELECT count(*) FROM registry.source_policy_reviews"),
    ):
        cur.execute(query)
        out[name] = cur.fetchone()[0]
    cur.execute("SELECT to_regclass('scoring.scores') IS NOT NULL")
    out["scores_table"] = "PRESENT" if cur.fetchone()[0] else "ABSENT"
    return out


if __name__ == "__main__":
    raise SystemExit(main())
