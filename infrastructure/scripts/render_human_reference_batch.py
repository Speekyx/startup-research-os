"""Render the blind human problem-family reference batch.

Mission 1.26 §7 and §8. Draws 40 pairs by deterministic stratified sampling from
the frozen candidate universe, excludes every pair Mission 1.25 labelled, freezes
a 24/16 split, and writes the review markdown plus its JSON twin.

    python infrastructure/scripts/render_human_reference_batch.py
    python infrastructure/scripts/render_human_reference_batch.py --check

**No model is called and no model output is read.** Not a prediction, not a
confidence, not an explanation. The artifacts contain no label and no suggested
answer, because the operator must judge blind.

**§8 and why there are no plain-language summaries.** The brief allows a strictly
descriptive summary of each observation and forbids generating one with an LLM.
A deterministic extractor cannot write prose, and the only other author available
is this assistant -- which is an LLM, and whose phrasing would carry a reading of
the question into a review that exists to obtain an independent one. So the
brief's own fallback is taken: **the source text is shown**, in structured
verbatim excerpts chosen by fixed rules, with nothing written about it.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MARKDOWN = ROOT / "docs" / "data" / "problem-family-human-reference-batch-v1.md"
JSON_TWIN = ROOT / "docs" / "data" / "problem-family-human-reference-batch-v1.json"
PRIOR_LABELS = ROOT / "docs" / "data" / "problem-family-reference-labels-v1.json"
DOCKER_CORRELATION_ID = "mission-1.20-normalize"

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_SENTENCE = re.compile(r"(?<=[.?!])\s+")


def _observations(url: str) -> tuple[dict, dict]:
    """Return (QuestionObservation by id, raw payload by id).

    The raw payload is kept because the review artifact needs the canonical URL
    for attribution, and `QuestionObservation` deliberately carries only what the
    candidate generator may read.
    """
    import psycopg
    from sros_semantic_equivalence import QuestionObservation

    obs: dict = {}
    raw: dict = {}
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
            qid = str(question["id"])
            raw[qid] = payload
            obs[qid] = QuestionObservation(
                observation_key=key,
                question_id=qid,
                title=str(question.get("title") or ""),
                body=str(question.get("body") or ""),
                tags=tuple(payload["tags"]["values"]),
            )
    return obs, raw


def _plain(text: str) -> str:
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", text))).strip()


def _opening(observation, limit: int = 420) -> str:
    """The first sentences of the body, verbatim.

    Fixed rule, no judgement: take whole sentences from the start until the
    limit. What the asker says first is usually what they were trying to do,
    and choosing a passage on relevance would be an editorial act.
    """
    text = _plain(observation.body)
    out: list[str] = []
    for sentence in _SENTENCE.split(text):
        if sum(len(s) for s in out) + len(sentence) > limit:
            break
        out.append(sentence)
    return " ".join(out).strip() or text[:limit]


def _diagnostics(observation, limit: int = 2) -> list[str]:
    """The first diagnostic-looking fragments, verbatim and unranked."""
    return [f[:220] for f in observation.diagnostics()[:limit]]


def _render(batch, raw: dict, obs: dict) -> str:
    from sros_semantic_equivalence import (
        ENRICHMENT_WARNING,
        FAMILY_GRANULARITY,
        FAMILY_INSUFFICIENT_ALONE,
        STRATUM_QUOTAS,
    )

    counts = batch.to_json()["counts"]
    out: list[str] = [
        "# Problem-family human reference batch V1 — blind review",
        "",
        "**Mission 1.26. Generated, never hand-picked. No model was called and no model",
        "output was read.** Regenerate with",
        "`python infrastructure/scripts/render_human_reference_batch.py`.",
        "",
        "- dataset: `problem-family-human-reference-v1`",
        f"- relation: **`SAME_PROBLEM_FAMILY`** — rubric `{batch.rubric_version}`, unchanged",
        f"- sampling: `{batch.sampling_version}`  ·  split: `{batch.split_version}`",
        f"- eligibility: `{batch.candidate_generator_version}`, frozen from Mission 1.25",
        f"- corpus: {batch.corpus_size} Docker `community_question` observations, unchanged",
        f"  since Mission 1.20. {batch.eligible_pairs} pairs eligible; "
        f"{batch.excluded_prior_pairs} already labelled in Mission 1.25 and excluded; "
        f"{batch.available_pairs} available",
        f"- **{counts['total']} pairs — {counts['development']} development, "
        f"{counts['holdout']} holdout**, split frozen before any label exists",
        "",
        "> **Nothing here carries a prediction, a suggested label, or an expected answer.**",
        "> Mission 1.25's classifier output played no part in choosing these pairs, and no",
        "> model has seen them. Your judgement is the reference.",
        "",
        "## Why this batch exists",
        "",
        "Mission 1.25 evaluated a problem-family classifier against 10 human-labelled",
        "holdout pairs containing 2 positives. That was enough to reject a classifier that",
        "answers DIFFERENT to everything — and it did reject one — but it is not enough to",
        "*develop* or credibly evaluate a successor. Ten pairs with two positives can say",
        "*this does not work*; they cannot say *this works*.",
        "",
        "This batch is the reference set that would make the next answer worth having.",
        "",
        "## The question, for every pair",
        "",
        "> **Are these two observations substantially the same user problem, pain or",
        "> blocked goal, such that one product, tool, documentation intervention or",
        "> workflow could reasonably help both?**",
        "",
        FAMILY_GRANULARITY,
        "",
        "Answer each with `SAME_FAMILY`, `DIFFERENT_FAMILY` or `UNCERTAIN`.",
        "",
        "**`UNCERTAIN` is a real answer and is never coerced into a binary one.** If the",
        "published text does not establish what one or both people were trying to do, that",
        "is the correct answer and it is useful.",
        "",
        "**You are not asked to diagnose anything.** No Docker knowledge is required: the",
        "question is about what each person was trying to do and what stopped them, not",
        "about what would fix it.",
        "",
        "## None of this makes two observations one family",
        "",
    ]
    out += [f"- {item}" for item in FAMILY_INSUFFICIENT_ALONE]
    out += [
        "",
        "## How these 40 were chosen",
        "",
        "Deterministically, from the frozen eligibility rule, in five feature bands. **The",
        "bands are sampling mechanisms and carry no expected answer** — they describe what",
        "two questions share lexically, which is exactly what a reviewer is needed to look",
        "past.",
        "",
        "| band | what the pair shares | available | drawn |",
        "|---|---|---|---|",
        f"| A high specificity | a site tag carried by ~6 or fewer of {batch.corpus_size} | "
        f"{batch.stratum_populations['A_HIGH_SPECIFICITY']} | "
        f"{STRATUM_QUOTAS[type(batch.pairs[0].stratum).HIGH_SPECIFICITY]} |",
        f"| B medium specificity | a tag of middling frequency | "
        f"{batch.stratum_populations['B_MEDIUM_SPECIFICITY']} | "
        f"{STRATUM_QUOTAS[type(batch.pairs[0].stratum).MEDIUM_SPECIFICITY]} |",
        f"| C low specificity | a common tag; eligible and weak | "
        f"{batch.stratum_populations['C_LOW_SPECIFICITY']} | "
        f"{STRATUM_QUOTAS[type(batch.pairs[0].stratum).LOW_SPECIFICITY]} |",
        f"| D diagnostic wrapper | a shared error fragment | "
        f"{batch.stratum_populations['D_DIAGNOSTIC_WRAPPER']} | "
        f"{STRATUM_QUOTAS[type(batch.pairs[0].stratum).DIAGNOSTIC_WRAPPER]} |",
        f"| E different tags | no shared tag; overlapping title words only | "
        f"{batch.stratum_populations['E_DIFFERENT_TAGS_SHARED_TOKENS']} | "
        f"{STRATUM_QUOTAS[type(batch.pairs[0].stratum).DIFFERENT_TAGS_SHARED_TOKENS]} |",
        "",
        f"> **{ENRICHMENT_WARNING}**",
        "",
        "## The split is already frozen",
        "",
        "Each pair is marked `development` or `holdout`, assigned within its band before",
        "any label existed. Development may later be used to design a successor",
        "classifier; **holdout must stay untouched by that work**. Please label both: the",
        "split governs how the labels may be *used*, never how they should be *made*.",
        "",
        "## What is shown, and why there is no summary",
        "",
        "Each observation appears as **verbatim source excerpts** — the title, the site's",
        "own tags, the opening sentences, and any error output — selected by fixed rules.",
        "There is no plain-language summary. Writing one would mean an assistant phrasing",
        "the question for you, and a phrasing carries a reading; this review exists to",
        "obtain a reading that is yours. The canonical URL is given for each observation,",
        "both as CC BY-SA attribution and so you can open the original where the excerpt",
        "is not enough.",
        "",
        "---",
        "",
    ]

    for index, pair in enumerate(batch.pairs, start=1):
        out += [
            f"## PAIR {index}/{len(batch.pairs)} — `{pair.pair_id}`",
            "",
            f"split: **{pair.split.lower()}**  ·  band: `{pair.stratum.value}`  ·  "
            f"candidate rank {pair.candidate_rank}",
            "",
        ]
        for side, qid in (("A", pair.a_question_id), ("B", pair.b_question_id)):
            observation = obs[qid]
            question = raw[qid]["question"]
            out += [
                f"### Observation {side} · question {qid}",
                "",
                f"**{_plain(observation.title)}**",
                "",
                f"tags: `{'`, `'.join(observation.tags)}`  ",
                f"source: <{question.get('url', '')}>  ",
                "licence: CC BY-SA 4.0, Stack Exchange Network",
                "",
                "> " + _opening(observation),
                "",
            ]
            fragments = _diagnostics(observation)
            if fragments:
                out += ["Error output quoted in the question:", ""]
                out += [f"    {f}" for f in fragments]
                out += [""]
        shared = pair.to_json()["deterministic_features"]
        bits = []
        if shared["shared_tags"]:
            bits.append(f"tags {', '.join(shared['shared_tags'])}")
        if shared["shared_title_tokens"]:
            bits.append(f"title words {', '.join(shared['shared_title_tokens'])}")
        if shared["shared_diagnostic"]:
            bits.append(f"a {len(shared['shared_diagnostic'])}-character error fragment")
        out += [
            f"*Lexically these two share: {'; '.join(bits)}. That is why the pair was "
            "surfaced, and it is not an argument that they are one family.*",
            "",
            "**Are these substantially the same user problem, pain or blocked goal, such",
            "that one product, tool, documentation intervention or workflow could",
            "reasonably help both?**",
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
        sample_reference_batch,
        tag_rarity,
    )

    url = args.database_url or os.environ.get("DATABASE_URL", "")
    if not url:
        print("FAIL  DATABASE_URL is not set", file=sys.stderr)
        return 2

    obs, raw = _observations(url)
    if not obs:
        print(f"FAIL  no observations for {DOCKER_CORRELATION_ID}", file=sys.stderr)
        return 1

    corpus = list(obs.values())
    candidates = generate_family_candidates(corpus, cap=10_000)
    prior = frozenset(
        row["pair_id"] for row in json.loads(PRIOR_LABELS.read_text(encoding="utf-8"))["labels"]
    )
    batch = sample_reference_batch(
        candidates,
        tag_rarity(tuple(corpus)),
        excluded_pair_ids=prior,
        rubric_version=FAMILY_RUBRIC_VERSION,
    )

    markdown = _render(batch, raw, obs)
    payload = json.dumps(batch.to_json(), indent=2, ensure_ascii=False) + "\n"

    if args.check:
        for path, expected in ((MARKDOWN, markdown), (JSON_TWIN, payload)):
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                print(
                    f"FAIL  {path.relative_to(ROOT)} is out of date. Run "
                    "`python infrastructure/scripts/render_human_reference_batch.py`.",
                    file=sys.stderr,
                )
                return 1
        print(f"ok    human reference batch is in sync ({len(batch.pairs)} pairs)")
        return 0

    MARKDOWN.write_text(markdown, encoding="utf-8")
    JSON_TWIN.write_text(payload, encoding="utf-8")
    print(
        f"wrote {len(batch.pairs)} pairs "
        f"({len(batch.development)} development, {len(batch.holdout)} holdout), no labels"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
