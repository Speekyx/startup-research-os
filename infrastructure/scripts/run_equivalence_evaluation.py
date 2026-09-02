"""Run the semantic-equivalence classifier over labelled pairs, once per split.

Mission 1.24 §6 and §21. **This spends real credits.** Every call goes through
the LLM Gateway, which enforces the budget ceiling before dispatch.

    python infrastructure/scripts/run_equivalence_evaluation.py --split DEVELOPMENT
    python infrastructure/scripts/run_equivalence_evaluation.py --split HOLDOUT

**The external-inference authorization is resolved before the loop**, and the
classifier refuses each pair before building a prompt if it does not hold. §11
requires the holdout to be run once against a fixed prompt version rather than
iterated against, so the split is an explicit argument and never a default.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
LABELS = ROOT / "docs" / "data" / "problem-equivalence-reference-labels-v1.json"
BATCH = ROOT / "docs" / "data" / "problem-equivalence-review-batch-v1.json"
RESULTS_DIR = ROOT / "docs" / "data"
CATALOG = ROOT / "docs" / "data" / "source-catalog-v1.json"
PROVIDER_POLICY = ROOT / "docs" / "data" / "model-provider-policy-v1.json"

WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"
LOCAL_PROFILE = "local-private-research-v1"
DOCKER_CORRELATION_ID = "mission-1.20-normalize"


def _load_env() -> None:
    env_file = ROOT / "infrastructure" / "compose" / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _observations() -> dict:
    import psycopg
    from sros_semantic_equivalence import QuestionObservation

    out = {}
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT observation_key, payload
                 FROM acquisition.normalized_records
                WHERE record_kind_id = 'community_question'
                  AND correlation_id = %s""",
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


def _authorization():
    """The production gate, resolved once, before any pair is serialised."""
    from sros_acquisition.compliance.inference import (
        authorize_external_inference,
        load_provider_policy,
    )
    from sros_acquisition.registry.catalog import load_catalog

    catalog = load_catalog(CATALOG)
    source = catalog.get("stack-exchange")
    profile = next(p for p in catalog.use_profiles if p.use_profile_id == LOCAL_PROFILE)
    policy = load_provider_policy(PROVIDER_POLICY)
    configured = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    return authorize_external_inference(
        source, profile, "anthropic", policy=policy, provider_configured=configured
    )


def _gateway():
    from sros_llm_gateway.config import load_config_from_env
    from sros_llm_gateway.gateway import LlmGateway
    from sros_llm_gateway.pricing import load_pricing_from_env
    from sros_llm_gateway.providers.anthropic import AnthropicProvider

    gateway = LlmGateway(config=load_config_from_env(), pricing=load_pricing_from_env())
    gateway.register(AnthropicProvider())
    return gateway


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", required=True, choices=["DEVELOPMENT", "HOLDOUT"])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--limit", type=int, default=0, help="0 means every labelled pair")
    args = parser.parse_args(argv)

    _load_env()
    sys.path.insert(0, str(ROOT / "packages" / "semantic-equivalence" / "python"))

    from sros_semantic_equivalence import (
        CANDIDATE_GENERATOR_VERSION,
        PROMPT_VERSION,
        RUBRIC_VERSION,
        QuestionForPrompt,
        ReferenceDecision,
        Split,
        classify_pair,
    )
    from sros_semantic_equivalence.candidates import CandidatePair

    split = Split(args.split)
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    batch = {i["pair_id"]: i for i in json.loads(BATCH.read_text(encoding="utf-8"))["items"]}
    observations = _observations()

    authorization = _authorization()
    if not authorization.authorized:
        print("REFUSED  external inference is not authorized:", file=sys.stderr)
        for reason, detail in zip(
            authorization.refusal_reasons, authorization.detail, strict=False
        ):
            print(f"  {reason}\n      {detail}", file=sys.stderr)
        return 1

    targets = [
        row for row in labels["labels"] if row["split"] == split.value and row["pair_id"] in batch
    ]
    if args.limit:
        targets = targets[: args.limit]

    gateway = _gateway()
    print(f"{split.value}: {len(targets)} labelled pairs, prompt {PROMPT_VERSION}")
    print("the reference labels are NOT sent to the model; only the two questions are\n")

    results = []
    started = time.monotonic()
    for index, row in enumerate(targets, start=1):
        item = batch[row["pair_id"]]
        a = observations[item["a"]["question_id"]]
        b = observations[item["b"]["question_id"]]
        pair = CandidatePair(
            a_key=a.observation_key,
            b_key=b.observation_key,
            a_question_id=a.question_id,
            b_question_id=b.question_id,
            score=0,
            reasons=tuple(item["surfaced_because"]),
            longest_shared_diagnostic=item.get("shared_diagnostic", ""),
        )
        classification = classify_pair(
            gateway,
            authorization,
            pair,
            QuestionForPrompt(a.question_id, a.title_text(), a.body, a.tags),
            QuestionForPrompt(b.question_id, b.title_text(), b.body, b.tags),
            workspace_id=WORKSPACE_ID,
            inference_run_id=args.run_id,
            candidate_generator_version=CANDIDATE_GENERATOR_VERSION,
        )
        results.append(classification.to_json())
        # Compared through the canonical mapping, not by a prefix: UNCERTAIN maps
        # to ABSTAIN, and a string comparison flags that agreement as a conflict.
        expected = ReferenceDecision(row["decision"]).as_model_decision()
        agree = "  " if classification.decision is expected else "!!"
        print(
            f"{index:3d}/{len(targets)}  {agree} {row['pair_id']:22s} "
            f"human={row['decision']:9s} model={classification.decision.value:17s} "
            f"{classification.reason_code.value}"
        )

    elapsed = time.monotonic() - started
    tokens_in = sum(r["usage"]["input_tokens"] for r in results)
    tokens_out = sum(r["usage"]["output_tokens"] for r in results)
    cost = sum(r["usage"]["cost_units"] for r in results)
    priced = all(r["usage"]["priced"] for r in results) if results else False

    payload = {
        "run_id": args.run_id,
        "split": split.value,
        "rubric_version": RUBRIC_VERSION,
        "prompt_version": PROMPT_VERSION,
        "candidate_generator_version": CANDIDATE_GENERATOR_VERSION,
        "pairs": len(results),
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "cost_units": round(cost, 6),
        "cost_units_are_priced": priced,
        "wall_clock_seconds": round(elapsed, 1),
        "classifications": results,
    }
    out = RESULTS_DIR / f"problem-equivalence-run-{args.run_id}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print()
    print(f"tokens  in {tokens_in:,}  out {tokens_out:,}")
    print(f"cost    {cost:.4f} units ({'priced' if priced else 'UNPRICED'})")
    print(f"wall    {elapsed:.1f}s")
    print(f"wrote   {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
