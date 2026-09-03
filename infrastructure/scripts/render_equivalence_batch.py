"""Render the blind human review batch from the live corpus.

Mission 1.24 §8. Reads the normalized Docker `community_question` observations,
runs the deterministic candidate generator, applies the declared batch selection
rule, and writes the operator-facing markdown plus its JSON twin.

**No model is called and no prediction is computed.** The operator labels blind
because this script cannot produce anything to show them.

    python infrastructure/scripts/render_equivalence_batch.py
    python infrastructure/scripts/render_equivalence_batch.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MARKDOWN = ROOT / "docs" / "data" / "problem-equivalence-review-batch-v1.md"
JSON_TWIN = ROOT / "docs" / "data" / "problem-equivalence-review-batch-v1.json"

# The acquisition that produced the Docker corpus (Mission 1.20). Named rather
# than inferred: the other Stack Exchange acquisition is the Mission 1.18 python
# corpus, and mixing them would change what the evaluation is about.
DOCKER_CORRELATION_ID = "mission-1.20-normalize"


def _load_observations(url: str) -> dict:
    import psycopg
    from sros_semantic_equivalence import QuestionObservation

    observations: dict[str, QuestionObservation] = {}
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT observation_key, payload
                 FROM acquisition.normalized_records
                WHERE record_kind_id = 'community_question'
                  AND correlation_id = %s
                ORDER BY observation_key""",
            (DOCKER_CORRELATION_ID,),
        )
        for key, payload in cur.fetchall():
            question = payload["question"]
            observations[str(question["id"])] = QuestionObservation(
                observation_key=key,
                question_id=str(question["id"]),
                title=str(question.get("title") or ""),
                body=str(question.get("body") or ""),
                tags=tuple(payload["tags"]["values"]),
            )
    return observations


def _render(batch: object, corpus_size: int) -> str:
    from sros_semantic_equivalence import V1_ACCEPTANCE

    b = batch
    out: list[str] = [
        "# Problem-equivalence review batch V1 — blind reference labels",
        "",
        "**Mission 1.24 §8. Generated, never hand-picked.** Regenerate with",
        "`python infrastructure/scripts/render_equivalence_batch.py`.",
        "",
        f"- rubric: `{b.rubric_version}`",  # type: ignore[attr-defined]
        f"- candidate generator: `{b.candidate_generator_version}`",  # type: ignore[attr-defined]
        f"- batch selection: `{b.selection_version}`",  # type: ignore[attr-defined]
        f"- corpus: {corpus_size} Docker `community_question` observations "
        f"(`{DOCKER_CORRELATION_ID}`)",
        f"- pairs: **{len(b.items)}** — {len(b.development)} development, "  # type: ignore[attr-defined]
        f"{len(b.holdout)} holdout",  # type: ignore[attr-defined]
        "",
        "> **No model has seen any of these pairs and no prediction exists.** The labels",
        "> written here are the reference set, and the classifier is scored against them,",
        "> never the other way round.",
        "",
        "> **Record who or what produced them.** A reference label is not automatically",
        "> human, and Mission 1.24 learned this the expensive way: its 40 labels were",
        "> AI-assisted and provisional, and the repository described them as human ground",
        "> truth until Mission 1.25 corrected it. `ReferenceOrigin` is required on every",
        "> label, and `human_ground_truth` stays NOT_ESTABLISHED until a person reviews.",
        "",
        "## How to answer",
        "",
        "For each pair write `SAME`, `DIFFERENT` or `UNCERTAIN` on its **Your label** line.",
        "",
        "- **SAME** — a reader who had the working fix for one would, from that fix alone,",
        "  know what to change for the other, and the change is to the same component,",
        "  addressing the same class of misconfiguration or defect.",
        "- **DIFFERENT** — different actionable failure concepts, even where the tool, the",
        "  tags, the wrapper diagnostic or the generic error class are shared.",
        "- **UNCERTAIN** — the published text does not establish the concept on both sides.",
        "  This is a real answer, not a skipped one, and it is the counterpart of the",
        "  classifier's mandatory ABSTAIN.",
        "",
        "None of the following makes two questions the same problem, on its own or",
        "together: the same tool; the same tags; the same wrapper diagnostic however long",
        "the shared string; the same generic error class; the same broad symptom; the same",
        "language, framework or base image.",
        "",
        "## Why the split is already decided",
        "",
        "Each pair is marked `development` or `holdout`, computed from its id before any",
        "label existed. Five pairs are pinned to `development` because the rubric quotes",
        "them or describes their pattern, so the classifier is shown their answer in its",
        "own instructions -- counting those as holdout successes would inflate the result.",
        "",
        "## The acceptance criterion, stated before any of this is scored",
        "",
        f"> {V1_ACCEPTANCE.statement}",
        "",
        "## Scope, which every downstream statement inherits",
        "",
        f"> {b.recall_limitation}",  # type: ignore[attr-defined]
        "",
        "---",
        "",
    ]

    for item in b.items:  # type: ignore[attr-defined]
        out += [
            f"### {item.rank}. `{item.pair_id}` — {item.split.value.lower()}",
            "",
        ]
        if item.holdout_exclusion_reason:
            out += [f"*Pinned to development: {item.holdout_exclusion_reason}.*", ""]
        out += [
            f"**A · {item.a_question_id}** — {item.a_title}  ",
            f"tags: `{'`, `'.join(item.a_tags)}`",
            "",
            f"> {item.a_excerpt}",
            "",
            f"**B · {item.b_question_id}** — {item.b_title}  ",
            f"tags: `{'`, `'.join(item.b_tags)}`",
            "",
            f"> {item.b_excerpt}",
            "",
            f"*Surfaced because: {'; '.join(item.surfaced_because)}.*",
        ]
        if item.shared_diagnostic:
            out += [
                "",
                f"*Shared fragment, {len(item.shared_diagnostic)} characters:* "
                f"`{item.shared_diagnostic[:180]}`",
            ]
        out += ["", "**Your label:** `____________`", "", "---", ""]

    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args(argv)

    sys.path.insert(0, str(ROOT / "packages" / "semantic-equivalence" / "python"))
    from sros_semantic_equivalence import (
        RUBRIC_VERSION,
        generate_candidates,
        select_review_batch,
    )

    url = args.database_url or os.environ.get("DATABASE_URL", "")
    if not url:
        print("FAIL  DATABASE_URL is not set", file=sys.stderr)
        return 2

    observations = _load_observations(url)
    if not observations:
        print(f"FAIL  no observations for {DOCKER_CORRELATION_ID}", file=sys.stderr)
        return 1

    candidates = generate_candidates(list(observations.values()))
    batch = select_review_batch(candidates, observations, rubric_version=RUBRIC_VERSION)
    markdown = _render(batch, len(observations))
    payload = json.dumps(batch.to_json(), indent=2, ensure_ascii=False) + "\n"

    if args.check:
        for path, expected in ((MARKDOWN, markdown), (JSON_TWIN, payload)):
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                print(
                    f"FAIL  {path.relative_to(ROOT)} is out of date. Run "
                    "`python infrastructure/scripts/render_equivalence_batch.py`.",
                    file=sys.stderr,
                )
                return 1
        print(f"ok    review batch is in sync ({len(batch.items)} pairs)")
        return 0

    MARKDOWN.write_text(markdown, encoding="utf-8")
    JSON_TWIN.write_text(payload, encoding="utf-8")
    print(
        f"wrote {len(batch.items)} pairs "
        f"({len(batch.development)} development, {len(batch.holdout)} holdout)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
