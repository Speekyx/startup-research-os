"""What measurement apparatuses this deployment holds (Mission 1.47 §0).

Measured from the live deployment BEFORE any candidate pair was considered,
because §2 forbids pre-selecting Wikimedia + Stack Exchange: a pair chosen first
and then justified against whatever happens to be held is a rationalisation.

An APPARATUS here is a `(source_id, proposition_kind)` pair. Not a source: one
publisher can operate two apparatuses over one corpus, and this deployment holds
two that do. `proposition_kind` is the `proposition` discriminator Mission
1.13.1 writes into `research.claims.proposition_facts`, which is the same field
`evidence-reliability-contract-v1.md` uses as the fifth reliability scope part.

Reads only. Writes `docs/data/cross-apparatus-holdings-baseline-v1.json`.

**NOT WIRED INTO CI, deliberately.** Mission 1.37 established that a generated
artifact measuring a DEPLOYMENT cannot be checked in CI, whose integration job
starts from an empty database: the step would be permanently red, or loosened
until it verified nothing. `--check` exists as an OPERATOR gate.

    uv run python infrastructure/scripts/measure_cross_apparatus_holdings.py
    uv run python infrastructure/scripts/measure_cross_apparatus_holdings.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "data" / "cross-apparatus-holdings-baseline-v1.json"
REGISTRY = ROOT / "docs" / "data" / "canonical-subject-registry-v1.json"

# An apparatus is (source, proposition kind). Counted, never assumed: Mission
# 1.36 §0 found three reliability scopes where two source families invited two.
APPARATUS = """
    SELECT c.proposition_facts ->> 'source_id'    AS source_id,
           c.proposition_facts ->> 'proposition'  AS proposition_kind,
           c.proposition_facts ->> 'resource_id'  AS resource_id,
           count(DISTINCT c.id)                   AS claims,
           count(e.id)                            AS evidence,
           count(DISTINCT e.observation_category) AS observation_categories,
           min(e.observation_category)            AS observation_category_min,
           max(e.observation_category)            AS observation_category_max,
           count(DISTINCT e.independence_state)   AS independence_states,
           max(e.independence_state)              AS independence_state_max,
           count(DISTINCT e.independence_group_id) AS independence_groups,
           count(DISTINCT c.interpreter_id) AS interpreters
      FROM research.claims c
      LEFT JOIN scoring.evidence e ON e.claim_id = c.id
     GROUP BY 1, 2, 3
     ORDER BY 1, 2
"""

# The source-native subject each Claim is about. Which fact names the subject
# differs per apparatus, so every candidate column is coalesced rather than one
# being assumed: a NULL here would silently merge two subjects into one row.
SUBJECTS = """
    SELECT c.proposition_facts ->> 'source_id'   AS source_id,
           c.proposition_facts ->> 'proposition' AS proposition_kind,
           coalesce(
               c.proposition_facts ->> 'content_id',
               c.proposition_facts ->> 'community_tag',
               c.proposition_facts ->> 'metric_id',
               c.proposition_facts ->> 'term',
               c.proposition_facts ->> 'term_a',
               c.proposition_facts ->> 'classification_division'
           )                                     AS subject_native,
           coalesce(
               c.proposition_facts ->> 'content_platform',
               c.proposition_facts ->> 'community_site',
               c.proposition_facts ->> 'geography_source_code',
               c.proposition_facts ->> 'classification_scheme'
           )                                     AS subject_qualifier,
           count(DISTINCT c.id)                  AS claims,
           count(e.id)                           AS evidence
      FROM research.claims c
      LEFT JOIN scoring.evidence e ON e.claim_id = c.id
     GROUP BY 1, 2, 3, 4
     ORDER BY 1, 2, 3
"""

# Period labels per (apparatus, subject). §16 asks whether two apparatuses cover
# an aligned period, and a label is what this repository holds -- never a clock.
PERIODS = """
    SELECT c.proposition_facts ->> 'source_id'   AS source_id,
           c.proposition_facts ->> 'proposition' AS proposition_kind,
           coalesce(
               c.proposition_facts ->> 'content_id',
               c.proposition_facts ->> 'community_tag',
               c.proposition_facts ->> 'metric_id',
               c.proposition_facts ->> 'term',
               c.proposition_facts ->> 'term_a',
               c.proposition_facts ->> 'classification_division'
           )                                     AS subject_native,
           c.proposition_facts ->> 'period_label'      AS period_label,
           c.proposition_facts ->> 'period_label_from' AS period_label_from,
           c.proposition_facts ->> 'period_label_to'   AS period_label_to,
           count(DISTINCT c.id)                        AS claims
      FROM research.claims c
     GROUP BY 1, 2, 3, 4, 5, 6
     ORDER BY 1, 2, 3, 4, 5, 6
"""

COUNTERS = """
    SELECT (SELECT count(*) FROM acquisition.raw_records)          AS raw_records,
           (SELECT count(*) FROM acquisition.normalized_records)   AS normalized_records,
           (SELECT count(*) FROM nlp.signals)                      AS signals,
           (SELECT count(*) FROM research.claims)                  AS claims,
           (SELECT count(*) FROM research.claim_revisions)         AS claim_revisions,
           (SELECT count(*) FROM scoring.evidence)                 AS evidence,
           (SELECT count(*) FROM epistemic.reliability_assessments) AS reliability_assessments,
           (SELECT count(*) FROM scoring.evidence
             WHERE independence_group_id IS NOT NULL)              AS evidence_in_groups,
           (SELECT count(*) FROM scoring.evidence
             WHERE reliability IS NOT NULL)                        AS evidence_with_stored_reliability
"""


def _rows(cur, sql):
    cur.execute(sql)
    names = [d.name for d in cur.description]
    return [dict(zip(names, row, strict=True)) for row in cur.fetchall()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("REFUSED: DATABASE_URL is not set")
        return 1

    import psycopg

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    document: dict[str, object] = {
        "$comment": (
            "Mission 1.47 section 0. The apparatus inventory of this deployment, "
            "measured before any candidate pair was considered. An apparatus is "
            "(source, proposition kind), NOT a source. Generated by "
            "infrastructure/scripts/measure_cross_apparatus_holdings.py. "
            "Deliberately not verified in CI -- it measures a deployment, and CI "
            "starts from an empty database (Mission 1.37)."
        ),
        "generated_by": "mission-1.47",
        "subject_registry_version": registry["registry_version"],
        "counters": {},
        "apparatus_inventory": [],
        "subjects_by_apparatus": [],
        "periods": [],
        "cross_apparatus_subject_overlap": [],
    }

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        document["counters"] = _rows(cur, COUNTERS)[0]
        document["apparatus_inventory"] = _rows(cur, APPARATUS)
        subjects = _rows(cur, SUBJECTS)
        document["subjects_by_apparatus"] = subjects
        document["periods"] = _rows(cur, PERIODS)

    # A subject is cross-apparatus only where the REVIEWED registry maps it and
    # BOTH sides carry Evidence. A mapped identifier reaching no Evidence is
    # mapped and unusable, which the registry itself says of kubernetes/podman.
    evidence_by_source: dict[str, dict[str, int]] = {}
    for row in subjects:
        if row["subject_native"] is None:
            continue
        bucket = evidence_by_source.setdefault(row["source_id"], {})
        key = row["subject_native"]
        bucket[key] = bucket.get(key, 0) + (row["evidence"] or 0)

    overlap = []
    for subject in registry["subjects"]:
        sides = []
        for identifier in subject["identifiers"]:
            source_id = identifier["source_id"]
            native = identifier["key"].rsplit("|", 1)[-1]
            sides.append(
                {
                    "source_id": source_id,
                    "identifier_key": identifier["key"],
                    "subject_native": native,
                    "evidence": evidence_by_source.get(source_id, {}).get(native, 0),
                }
            )
        with_evidence = [s for s in sides if s["evidence"] > 0]
        overlap.append(
            {
                "subject_id": subject["subject_id"],
                "sides": sides,
                "apparatus_sources_with_evidence": len(with_evidence),
                "cross_apparatus_evidence_available": len(with_evidence) >= 2,
            }
        )
    document["cross_apparatus_subject_overlap"] = overlap

    text = json.dumps(document, indent=2, ensure_ascii=False, default=str) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"REFUSED: {OUT.name} does not exist; run without --check first")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {OUT.name} does not match the live deployment")
            return 1
        print(f"ok       {OUT.name} matches the live apparatus holdings")
        return 0

    OUT.write_text(text, encoding="utf-8")
    for row in document["apparatus_inventory"]:
        print(
            f"{row['source_id']:20} {row['proposition_kind']:58} "
            f"cl={row['claims']:>2} ev={row['evidence']:>2}"
        )
    print()
    for row in overlap:
        mark = "BOTH" if row["cross_apparatus_evidence_available"] else "one "
        counts = " / ".join(f"{s['source_id']}={s['evidence']}" for s in row["sides"])
        print(f"  {mark}  {row['subject_id']:12} {counts}")
    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
