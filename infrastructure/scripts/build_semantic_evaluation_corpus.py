"""Mission 1.85.3 (roadmap N08-A). Freeze the Stack Overflow semantic-extraction evaluation corpus.

Reads the already-held `community_question` NormalizedRecords in a READ ONLY transaction and writes:

- `docs/data/stack-overflow-semantic-evaluation-corpus-v1.json`: the frozen manifest. Identifiers,
  digests of the stored fields and of the rendered text surface, the split, and the exclusions. No text.
- `docs/data/stack-overflow-semantic-label-pack-{development,holdout}-v1.json`: the blank human-label packs.
  References only, every label UNLABELLED, no origin, no annotator.

Question text is CC BY-SA 4.0 material and is not copied into committed files. An annotator renders a
local, uncommitted working copy with `--render-working-copy DIR`, and every surface there is checked
against the frozen digest.

No model, no network beyond the local database, no write to the database.

    uv run python infrastructure/scripts/build_semantic_evaluation_corpus.py --write
    uv run python infrastructure/scripts/build_semantic_evaluation_corpus.py --check
    uv run python infrastructure/scripts/build_semantic_evaluation_corpus.py --render-working-copy DIR
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "semantic-extraction-contract" / "python"))

from sros_semantic_extraction_contract import (  # noqa: E402
    LABELS,
    SURFACE_ID,
    SURFACE_VERSION,
    LabelStatus,
    marker_regions,
    render_question_surface,
    surface_sha256,
)

DATA = ROOT / "docs" / "data"
MANIFEST = DATA / "stack-overflow-semantic-evaluation-corpus-v1.json"
PACKS = {
    "DEVELOPMENT": DATA / "stack-overflow-semantic-label-pack-development-v1.json",
    "HOLDOUT": DATA / "stack-overflow-semantic-label-pack-holdout-v1.json",
}
SPLIT_SEED = "n08a-stack-overflow-semantic-split-v1"
SOURCE_ID = "stack-exchange"
RESOURCE_ID = "questions/stackoverflow"

QUERY = """
SELECT n.id, n.observation_key, n.raw_record_id, n.content_hash, n.review_version, n.superseded_at,
       n.quality, n.expires_at, n.payload, r.provenance
FROM acquisition.normalized_records n
JOIN acquisition.raw_records r ON r.id = n.raw_record_id
WHERE n.source_id = %s AND n.record_kind_id = 'community_question'
ORDER BY n.observation_key
"""

# Counts only, never the matched text: these flag records whose free text may carry an identifier that
# acquisition filtering could not remove, so a future egress packet can exclude or review them.
RESIDUAL_PATTERNS = {
    "email_like": r"[\w.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}",
    "user_home_path": r"(?:/home/|/Users/|[A-Za-z]:\\+Users\\+)[\w.-]+",
    "ipv4_like": r"\b\d{1,3}(?:\.\d{1,3}){3}\b",
    "at_handle": r"(?<![\w/@.])@[A-Za-z][\w-]{2,}",
    "long_token_like": r"\b(?=[A-Za-z0-9_\-]*\d)(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{32,}\b",
    "url": r"https?://",
}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_rows() -> list[dict[str, Any]]:
    import psycopg

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit(
            "FAIL     DATABASE_URL is required; the corpus is read from the held records"
        )
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        cur.execute(QUERY, (SOURCE_ID,))
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]
        conn.rollback()
    return rows


def build(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, str]]:
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    surfaces: dict[str, str] = {}
    for row in rows:
        payload, prov = row["payload"], row["provenance"]
        question = payload["question"]
        rid = str(row["id"])
        reasons = []
        if row["superseded_at"] is not None:
            reasons.append("SUPERSEDED")
        if row["quality"] != "VALID":
            reasons.append("NOT_VALID")
        if (
            question.get("site") != "stackoverflow"
            or prov.get("resource_id", RESOURCE_ID) != RESOURCE_ID
        ):
            reasons.append("OUTSIDE_AUTHORISED_RESOURCE")
        if question.get("content_licence") != "CC BY-SA 4.0":
            reasons.append("PER_ITEM_CONTENT_LICENCE_NOT_REPORTED")
        base = {
            "normalized_record_id": rid,
            "observation_key": row["observation_key"],
            "question_id": question["id"],
        }
        if reasons:
            excluded.append({**base, "reasons": reasons})
            continue
        surface = render_question_surface(question["title"], question.get("body"))
        surfaces[rid] = surface
        plain = question["title"] + "\n" + html.unescape(question.get("body") or "")
        regions = marker_regions(surface)
        included.append(
            {
                **base,
                "raw_record_id": str(row["raw_record_id"]),
                "question_url": question["url"],
                "cohort": f"query:tagged={prov['query']['tagged']}",
                "normalized_content_hash": row["content_hash"],
                "review_version": row["review_version"],
                "stored_title_sha256": sha256(question["title"]),
                "stored_body_sha256": sha256(question.get("body") or ""),
                "surface_sha256": surface_sha256(surface),
                "surface_length": len(surface),
                "code_regions": sum(1 for kind, _, _ in regions if kind == "CODE"),
                "quote_regions": sum(1 for kind, _, _ in regions if kind == "QUOTE"),
                "residual_identifier_flags": {
                    name: len(re.findall(pattern, plain))
                    for name, pattern in RESIDUAL_PATTERNS.items()
                },
                "normalized_expires_at": row["expires_at"].isoformat(),
            }
        )

    by_cohort: dict[str, list[dict[str, Any]]] = {}
    for record in included:
        by_cohort.setdefault(record["cohort"], []).append(record)
    for cohort in by_cohort.values():
        cohort.sort(key=lambda r: sha256(f"{SPLIT_SEED}|{r['normalized_record_id']}"))
        half = (len(cohort) + 1) // 2
        for index, record in enumerate(cohort):
            record["split"] = "DEVELOPMENT" if index < half else "HOLDOUT"
    included.sort(key=lambda r: r["observation_key"])

    manifest = {
        "$comment": "Mission 1.85.3 (N08-A). Frozen before any label exists and before any model has read any record. Contains identifiers and digests, never question text. Human labels live in the split packs; model output lives nowhere in this repository.",
        "corpus_id": "stack-overflow-semantic-evaluation-corpus",
        "corpus_version": "1.0.0",
        "source_id": SOURCE_ID,
        "resource_id": RESOURCE_ID,
        "use_profile_id": "local-private-research-v1",
        "record_kind_id": "community_question",
        "content_licence": "CC BY-SA 4.0 (per item); attribution: Stack Exchange Network, licence identifier, item link",
        "text_surface": f"{SURFACE_ID}@{SURFACE_VERSION}",
        "split_rule": f"within each acquisition cohort, order by sha256('{SPLIT_SEED}|' + normalized_record_id); first ceil(n/2) DEVELOPMENT, rest HOLDOUT",
        "enrichment_warning": "Selected by three bounded tag queries (docker over March 2024; python over one day). Label proportions describe these queries only, never Stack Overflow or any population.",
        "model_outputs_used_in_selection": False,
        "held_records": len(rows),
        "included_records": len(included),
        "excluded_records": len(excluded),
        "split_counts": {
            split: sum(1 for r in included if r["split"] == split)
            for split in ("DEVELOPMENT", "HOLDOUT")
        },
        "cohort_counts": {cohort: len(records) for cohort, records in sorted(by_cohort.items())},
        "records": included,
        "excluded": excluded,
    }

    packs = {}
    for split in ("DEVELOPMENT", "HOLDOUT"):
        records = [r for r in included if r["split"] == split]
        packs[split] = {
            "$comment": "BLANK HUMAN-LABEL PACK. Every state is UNLABELLED. Fill a copy, never this file in place. A label produced by a model is never a reference label and must not be entered here. Text is not inlined: render a local working copy with build_semantic_evaluation_corpus.py --render-working-copy and check each surface_sha256.",
            "dataset_id": "stack-overflow-semantic-extraction-reference",
            "dataset_version": "1.0.0",
            "split": split,
            "synthetic": False,
            "corpus": f"{manifest['corpus_id']}@{manifest['corpus_version']}",
            "label_set": "first-person-semantic-labels@1.0.0",
            "rubric": "docs/data/first-person-semantic-extraction-contract-v1.md#6-label-definitions-and-annotation-rules",
            "text_surface": manifest["text_surface"],
            "reference_origin": None,
            "reference_origin_allowed": ["HUMAN_OPERATOR", "HUMAN_EXPERT", "HUMAN_NON_EXPERT"],
            "annotator_id": None,
            "annotation_started_at": None,
            "annotation_completed_at": None,
            "records": [
                {
                    "normalized_record_id": r["normalized_record_id"],
                    "question_id": r["question_id"],
                    "question_url": r["question_url"],
                    "surface_sha256": r["surface_sha256"],
                    "surface_length": r["surface_length"],
                    "labels": {
                        label.label_id: (
                            {"state": "UNLABELLED", "evidence": [], "subject": None, "note": None}
                            if label.status is LabelStatus.EXTRACTABLE
                            else {"state": "UNLABELLED", "note": None}
                        )
                        for label in LABELS
                        if label.status is not LabelStatus.NOT_SAFE
                    },
                    "record_note": None,
                }
                for r in records
            ],
        }
    return manifest, packs, surfaces


def dump(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--render-working-copy", metavar="DIR")
    args = parser.parse_args(argv)
    manifest, packs, surfaces = build(read_rows())

    if args.render_working_copy:
        frozen = json.loads(MANIFEST.read_text("utf-8"))
        out = pathlib.Path(args.render_working_copy)
        if out.resolve().is_relative_to(ROOT.resolve()):
            print(
                "REFUSED  the working copy holds licensed text and must live outside the repository"
            )
            return 1
        out.mkdir(parents=True, exist_ok=True)
        bad = 0
        for record in frozen["records"]:
            surface = surfaces.get(record["normalized_record_id"])
            if surface is None or surface_sha256(surface) != record["surface_sha256"]:
                bad += 1
                continue
            (out / f"{record['split'].lower()}-{record['question_id']}.txt").write_bytes(
                surface.encode("utf-8")
            )
        print(
            f"rendered {len(frozen['records']) - bad} surfaces; {bad} did not match the frozen digest"
        )
        return 1 if bad else 0

    targets = {MANIFEST: dump(manifest), **{PACKS[s]: dump(p) for s, p in packs.items()}}
    if args.write:
        for path in targets:
            if path.exists():
                print(f"REFUSED  {path.name} exists; a frozen corpus is written once")
                return 1
        for path, content in targets.items():
            path.write_bytes(content)
        print(
            f"wrote {manifest['included_records']} records, {manifest['excluded_records']} excluded, {manifest['split_counts']}"
        )
        return 0
    stale = [path.name for path, content in targets.items() if path.read_bytes() != content]
    for name in stale:
        print(f"FAIL     {name} no longer matches the held records")
    if not stale:
        print(f"ok       corpus matches the held records ({manifest['included_records']} records)")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
