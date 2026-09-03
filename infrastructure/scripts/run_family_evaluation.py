"""Run the problem-family classifier over labelled pairs, once per split.

Mission 1.25. **This spends real credits.** Every call goes through the LLM
Gateway, which enforces the budget ceiling before dispatch.

    python infrastructure/scripts/run_family_evaluation.py --split DEVELOPMENT --run-id fam-dev-1
    python infrastructure/scripts/run_family_evaluation.py --split HOLDOUT --run-id fam-holdout-1

**The prompt is frozen.** This mission runs no prompt development: the
development split is scored to OBSERVE, never to tune, and the holdout is run
once against the same version. Running development after holdout, or holdout
twice, would make the split meaningless.

**The reference labels are never sent to the model.** Only the two questions are.

**A schema failure is retried ONCE against the same route, and counted.** The
Gateway refuses a malformed structured response rather than guessing, which is
correct and stays: ADR-006 treats a schema failure as a possible injection signal
and does not route around it. But a mis-emitted field name is a formatting
accident, not a semantic answer, and losing the other nineteen pairs to it would
be worse. Asking the same model the same question again is not the fallback
ADR-006 forbids -- that is routing to a DIFFERENT provider and comparing outputs
across models. The retry count is reported, because a route that needs retries is
a fact about the route.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
LABELS = ROOT / "docs" / "data" / "problem-family-reference-labels-v1.json"
BATCH = ROOT / "docs" / "data" / "problem-family-review-batch-v1.json"
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
    args = parser.parse_args(argv)

    _load_env()
    sys.path.insert(0, str(ROOT / "packages" / "semantic-equivalence" / "python"))

    from sros_semantic_equivalence import (
        FAMILY_CANDIDATE_GENERATOR_VERSION,
        FAMILY_PROMPT_VERSION,
        FAMILY_RUBRIC_VERSION,
        QuestionForPrompt,
        Split,
        classify_family_pair,
    )
    from sros_semantic_equivalence.candidates import CandidatePair

    split = Split(args.split)
    reference = json.loads(LABELS.read_text(encoding="utf-8"))
    batch = {i["pair_id"]: i for i in json.loads(BATCH.read_text(encoding="utf-8"))["items"]}
    observations = _observations()

    authorization = _authorization()
    if not authorization.authorized:
        print("REFUSED  external inference is not authorized:", file=sys.stderr)
        for reason in authorization.refusal_reasons:
            print(f"  {reason}", file=sys.stderr)
        return 1

    targets = [
        row
        for row in reference["labels"]
        if row["split"] == split.value and row["pair_id"] in batch
    ]

    gateway = _gateway()
    print(f"{split.value}: {len(targets)} labelled pairs, prompt {FAMILY_PROMPT_VERSION}")
    print(f"reference origin: {reference['reference_label_origin']} — NOT human ground truth")
    print("the reference labels are NOT sent to the model; only the two questions are\n")

    from sros_llm_gateway.types import SchemaValidationError

    results = []
    retried: list[str] = []
    failed: list[dict[str, str]] = []
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

        # Loop variables bound as defaults: a closure that captured them by
        # reference would be correct here only because it is called at once, and
        # correct-by-accident is what ruff's B023 exists to refuse.
        def _call(pair=pair, a=a, b=b) -> object:  # noqa: B008
            return classify_family_pair(
                gateway,
                authorization,
                pair,
                QuestionForPrompt(a.question_id, a.title_text(), a.body, a.tags),
                QuestionForPrompt(b.question_id, b.title_text(), b.body, b.tags),
                workspace_id=WORKSPACE_ID,
                inference_run_id=args.run_id,
                candidate_generator_version=FAMILY_CANDIDATE_GENERATOR_VERSION,
            )

        try:
            classification = _call()
        except SchemaValidationError as first:
            retried.append(row["pair_id"])
            try:
                classification = _call()
            except SchemaValidationError as second:
                failed.append({"pair_id": row["pair_id"], "error": str(second)})
                print(
                    f"{index:3d}/{len(targets)}  XX {row['pair_id']:22s} "
                    f"SCHEMA_FAILURE twice; no prediction recorded for this pair"
                )
                continue
            print(f"      retried {row['pair_id']} after a schema failure: {str(first)[:70]}")
        results.append(classification.to_json())
        expected = {
            "SAME": "SAME_PROBLEM_FAMILY",
            "DIFFERENT": "DIFFERENT_PROBLEM_FAMILY",
            "UNCERTAIN": "ABSTAIN",
        }[row["decision"]]
        agree = "  " if classification.decision.value == expected else "!!"
        print(
            f"{index:3d}/{len(targets)}  {agree} {row['pair_id']:22s} "
            f"ref={row['decision_as_supplied']:17s} model={classification.decision.value:25s} "
            f"{classification.reason_code.value}"
        )

    elapsed = time.monotonic() - started
    tokens_in = sum(r["usage"]["input_tokens"] for r in results)
    tokens_out = sum(r["usage"]["output_tokens"] for r in results)
    cost = sum(r["usage"]["cost_units"] for r in results)

    payload = {
        "run_id": args.run_id,
        "relation": "SAME_PROBLEM_FAMILY",
        "split": split.value,
        "reference_label_origin": reference["reference_label_origin"],
        "human_ground_truth": reference["human_ground_truth"],
        "rubric_version": FAMILY_RUBRIC_VERSION,
        "prompt_version": FAMILY_PROMPT_VERSION,
        "candidate_generator_version": FAMILY_CANDIDATE_GENERATOR_VERSION,
        "pairs": len(results),
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "cost_units": round(cost, 6),
        "cost_units_are_priced": all(r["usage"]["priced"] for r in results) if results else False,
        "wall_clock_seconds": round(elapsed, 1),
        "schema_retries": retried,
        "schema_failures": failed,
        "classifications": results,
    }
    out = ROOT / "docs" / "data" / f"problem-family-run-{args.run_id}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print()
    print(f"tokens  in {tokens_in:,}  out {tokens_out:,}")
    print(f"cost    {cost:.4f} units (USD)")
    print(f"wall    {elapsed:.1f}s")
    print(f"retries {len(retried)}  |  unrecoverable schema failures {len(failed)}")
    print(f"wrote   {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
