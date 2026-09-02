"""Render the blind problem-family review batch from the live corpus.

Mission 1.25 §7. Reads the same 89 normalized Docker `community_question`
observations Mission 1.20 acquired, orders them for the FAMILY relation, and
writes the operator-facing markdown plus its JSON twin.

**No model is called and no prediction is computed.** The reviewer labels blind
because this script cannot produce anything to show them.

    python infrastructure/scripts/render_family_batch.py
    python infrastructure/scripts/render_family_batch.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MARKDOWN = ROOT / "docs" / "data" / "problem-family-review-batch-v1.md"
JSON_TWIN = ROOT / "docs" / "data" / "problem-family-review-batch-v1.json"
DOCKER_CORRELATION_ID = "mission-1.20-normalize"


def _observations(url: str) -> dict:
    import psycopg
    from sros_semantic_equivalence import QuestionObservation

    out: dict[str, QuestionObservation] = {}
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
            out[str(question["id"])] = QuestionObservation(
                observation_key=key,
                question_id=str(question["id"]),
                title=str(question.get("title") or ""),
                body=str(question.get("body") or ""),
                tags=tuple(payload["tags"]["values"]),
            )
    return out


def _render(batch, corpus_size: int, considered: int, possible: int) -> str:
    from sros_semantic_equivalence import (
        FAMILY_GRANULARITY,
        FAMILY_HOLDOUT_FRACTION,
        FAMILY_INSUFFICIENT_ALONE,
        FAMILY_V1_ACCEPTANCE,
    )

    out: list[str] = [
        "# Problem-family review batch V1 — blind reference labels",
        "",
        "**Mission 1.25 §7. Generated, never hand-picked.** Regenerate with",
        "`python infrastructure/scripts/render_family_batch.py`.",
        "",
        "- relation: **`SAME_PROBLEM_FAMILY`** — *not* the Mission 1.24 exact relation",
        f"- rubric: `{batch.rubric_version}`",
        f"- candidate ordering: `{batch.candidate_generator_version}`",
        f"- batch selection: `{batch.selection_version}`",
        f"- corpus: {corpus_size} Docker `community_question` observations, unchanged since",
        f"  Mission 1.20. {considered} of {possible} possible pairs qualify as candidates",
        f"- pairs: **{len(batch.items)}** — {len(batch.development)} development, "
        f"{len(batch.holdout)} holdout",
        "",
        "> **No model has seen any of these pairs and no prediction exists.** The labels",
        "> written here are the reference set, and the classifier is scored against them.",
        "> Record who or what produced them: `human_ground_truth` stays NOT_ESTABLISHED",
        "> unless a person actually judges.",
        "",
        "## The question, and it is not Mission 1.24's question",
        "",
        "Mission 1.24 asked whether the working FIX for one would tell you what to change",
        "for the other. That needed Docker expertise, and it is a different relation which",
        "stays intact and unweakened.",
        "",
        "**This one is answerable without knowing any fix.**",
        "",
        FAMILY_GRANULARITY,
        "",
        "For each pair write `SAME_FAMILY`, `DIFFERENT_FAMILY` or `UNCERTAIN` on its",
        "**Your label** line.",
        "",
        "- **SAME_FAMILY** — substantially the same user problem or blocked goal. One",
        "  product, tool, documentation change or workflow could reasonably help both",
        "  people, even though their causes and fixes may differ entirely.",
        "- **DIFFERENT_FAMILY** — different blocked goals. Helping both would take two",
        "  unrelated interventions.",
        "- **UNCERTAIN** — the text does not establish what one or both people were trying",
        "  to do. A real answer, not a skipped one.",
        "",
        "**You are not asked to diagnose anything.** If you cannot tell what either person",
        "was trying to do, that is `UNCERTAIN` and it is useful.",
        "",
        "## None of this makes two observations one family",
        "",
    ]
    out += [f"- {item}" for item in FAMILY_INSUFFICIENT_ALONE]
    out += [
        "",
        "## Why four pairs are already marked development",
        "",
        "The rubric quotes them and states their answers, so the classifier is shown them",
        "in its own instructions. Getting them right shows it can read its rubric and is",
        "not evidence of generalisation. **Please label them anyway** — where your answer",
        "differs from the rubric's stated one, that disagreement is the most useful thing",
        "in this batch.",
        "",
        "## The split, and why it leans to holdout",
        "",
        "Each pair is marked development or holdout, computed from its id before any label",
        f"existed, with **{int(FAMILY_HOLDOUT_FRACTION * 100)}% to holdout** rather than the",
        "half Mission 1.24 used. That mission planned prompt development and this one does",
        "not: the family prompt is written once and frozen, so a large development set buys",
        "nothing while a large holdout buys positive coverage in the split that decides.",
        "Mission 1.24's single positive fell in development and left its holdout unable to",
        "distinguish caution from correctness.",
        "",
        "## The acceptance criterion, frozen before any prediction",
        "",
        f"> {FAMILY_V1_ACCEPTANCE.statement}",
        "",
        "## Scope, which every downstream statement inherits",
        "",
        f"> {batch.recall_limitation}",
        "",
        "---",
        "",
    ]

    for item in batch.items:
        out += [f"### {item.rank}. `{item.pair_id}` — {item.split.value.lower()}", ""]
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
            "",
            "**Your label:** `____________`",
            "",
            "---",
            "",
        ]
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args(argv)

    sys.path.insert(0, str(ROOT / "packages" / "semantic-equivalence" / "python"))
    from sros_semantic_equivalence import (
        FAMILY_RUBRIC_VERSION,
        generate_family_candidates,
        select_family_review_batch,
    )

    url = args.database_url or os.environ.get("DATABASE_URL", "")
    if not url:
        print("FAIL  DATABASE_URL is not set", file=sys.stderr)
        return 2

    observations = _observations(url)
    if not observations:
        print(f"FAIL  no observations for {DOCKER_CORRELATION_ID}", file=sys.stderr)
        return 1

    candidates = generate_family_candidates(list(observations.values()), cap=10_000)
    batch = select_family_review_batch(
        candidates, observations, rubric_version=FAMILY_RUBRIC_VERSION
    )
    markdown = _render(
        batch, len(observations), candidates.considered_pairs, candidates.possible_pairs
    )
    payload = json.dumps(batch.to_json(), indent=2, ensure_ascii=False) + "\n"

    if args.check:
        for path, expected in ((MARKDOWN, markdown), (JSON_TWIN, payload)):
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                print(
                    f"FAIL  {path.relative_to(ROOT)} is out of date. Run "
                    "`python infrastructure/scripts/render_family_batch.py`.",
                    file=sys.stderr,
                )
                return 1
        print(f"ok    family review batch is in sync ({len(batch.items)} pairs)")
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
