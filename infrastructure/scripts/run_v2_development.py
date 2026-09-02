"""Evaluate V2 candidate prompts on Mission 1.26 DEVELOPMENT only.

Mission 1.27 §6 to §8. **This spends real credits.**

    python infrastructure/scripts/run_v2_development.py
    python infrastructure/scripts/run_v2_development.py --split HOLDOUT --variant V2-B

**DEVELOPMENT is the default and the holdout needs an explicit flag**, because
reaching the holdout should be a decision visible in a command line and in a
diff. The loader enforces the rest: the two splits' labels live in separate
files, so development work cannot read a holdout label by accident.

**Every count this produces is agreement against an `AI_ASSISTED_PROVISIONAL`
reference.** Not accuracy, not validated accuracy, not a human benchmark.

**Output tokens are capped at 1200 per call.** The V2 schema caps its fields at
1080 characters of content, and V1 measured about 630 output tokens on the same
shape, so 1200 is generous. It is set because the §8 ceiling of 3.00 USD must be
a real bound: at the adapter's default of 4096 the mission's hard maximum was
4.44 USD, and the honest response to a ceiling you might exceed is to bound the
thing, not to argue the bound away.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "data"
CATALOG = DOCS / "source-catalog-v1.json"
PROVIDER_POLICY = DOCS / "model-provider-policy-v1.json"

WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"
LOCAL_PROFILE = "local-private-research-v1"
DOCKER_CORRELATION_ID = "mission-1.20-normalize"
MAX_OUTPUT_TOKENS = 1200


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
    """The production gate, resolved once, before any question text is built."""
    from sros_acquisition.compliance.inference import (
        authorize_external_inference,
        load_provider_policy,
    )
    from sros_acquisition.registry.catalog import load_catalog

    catalog = load_catalog(CATALOG)
    source = catalog.get("stack-exchange")
    profile = next(p for p in catalog.use_profiles if p.use_profile_id == LOCAL_PROFILE)
    return authorize_external_inference(
        source,
        profile,
        "anthropic",
        policy=load_provider_policy(PROVIDER_POLICY),
        provider_configured=bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
    )


def _gateway():
    from sros_llm_gateway.config import load_config_from_env
    from sros_llm_gateway.gateway import LlmGateway
    from sros_llm_gateway.pricing import load_pricing_from_env
    from sros_llm_gateway.providers.anthropic import AnthropicProvider

    gateway = LlmGateway(config=load_config_from_env(), pricing=load_pricing_from_env())
    gateway.register(AnthropicProvider(max_output_tokens=MAX_OUTPUT_TOKENS))
    return gateway


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="DEVELOPMENT", choices=["DEVELOPMENT", "HOLDOUT"])
    parser.add_argument("--variant", default=None, help="run one variant only")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)

    _load_env()
    sys.path.insert(0, str(ROOT / "packages" / "semantic-equivalence" / "python"))

    from sros_llm_gateway.types import LlmRequest, SchemaValidationError
    from sros_semantic_equivalence import (
        SEMANTIC_TIER,
        V2_OUTPUT_SCHEMA,
        V2_PROMPT_ID,
        V2_VARIANTS,
        QuestionForPrompt,
        ReferenceDatasetPaths,
        ReferenceOrigin,
        Split,
        VariantResult,
        load_development_labels,
        load_holdout_labels,
        render_v2_prompt,
    )
    from sros_semantic_equivalence.classifier import ClassificationRefusedError

    split = Split(args.split)
    paths = ReferenceDatasetPaths(directory=DOCS)
    loader = load_development_labels if split is Split.DEVELOPMENT else load_holdout_labels
    labels = loader(paths, expected_origin=ReferenceOrigin.AI_ASSISTED_PROVISIONAL)
    reference = {label.pair_id: label.decision.value for label in labels.labels}

    variants = [v for v in V2_VARIANTS if args.variant is None or v.name == args.variant]
    if not variants:
        print(f"FAIL  no variant named {args.variant!r}", file=sys.stderr)
        return 2

    observations = _observations()
    authorization = _authorization()
    if not authorization.authorized:
        print("REFUSED  external inference is not authorized:", file=sys.stderr)
        for reason in authorization.refusal_reasons:
            print(f"  {reason}", file=sys.stderr)
        return 1

    gateway = _gateway()
    expected_map = {
        "SAME": "SAME_PROBLEM_FAMILY",
        "DIFFERENT": "DIFFERENT_PROBLEM_FAMILY",
        "UNCERTAIN": "ABSTAIN",
    }

    print(
        f"{split.value}: {len(labels.labels)} pairs   variants: "
        f"{', '.join(v.name for v in variants)}"
    )
    print(f"reference origin: {sorted(o.value for o in labels.origins)} — provisional, not truth")
    print("the reference labels are NOT sent to the model; only the two questions are\n")

    payload_variants = []
    for variant in variants:
        print(f"--- {variant.name} ({variant.version})")
        rows, retries, failures = [], [], []
        started = time.monotonic()
        for index, label in enumerate(labels.labels, start=1):
            a = observations[label.a_question_id]
            b = observations[label.b_question_id]
            prompt = render_v2_prompt(
                variant,
                QuestionForPrompt(a.question_id, a.title_text(), a.body, a.tags),
                QuestionForPrompt(b.question_id, b.title_text(), b.body, b.tags),
            )
            request = LlmRequest(
                tier=SEMANTIC_TIER,
                task=V2_PROMPT_ID,
                prompt_template_id=V2_PROMPT_ID,
                prompt_template_version=variant.version,
                response_schema=V2_OUTPUT_SCHEMA,
                prompt=prompt,
                workspace_id=WORKSPACE_ID,
                correlation_id=args.run_id,
                timeout_seconds=90,
                requires_structured_output=True,
            )
            if not authorization.authorized:  # pragma: no cover - defensive
                raise ClassificationRefusedError(tuple(authorization.refusal_reasons))
            try:
                response = gateway.complete(request)
            except SchemaValidationError:
                retries.append(label.pair_id)
                try:
                    response = gateway.complete(request)
                except SchemaValidationError as second:
                    failures.append({"pair_id": label.pair_id, "error": str(second)})
                    print(f"{index:3d}  XX {label.pair_id:22s} schema failure twice")
                    continue
            body = response.structured or {}
            decision = str(body["decision"])
            rows.append(
                {
                    "pair_id": label.pair_id,
                    "decision": decision,
                    "goal_a": str(body.get("goal_a", "")),
                    "blocker_a": str(body.get("blocker_a", "")),
                    "goal_b": str(body.get("goal_b", "")),
                    "blocker_b": str(body.get("blocker_b", "")),
                    "shared_problem_if_any": str(body.get("shared_problem_if_any", "")),
                    "brief_rationale": str(body.get("brief_rationale", "")),
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "cost_units": response.usage.cost_units,
                    },
                }
            )
            expected = expected_map[reference[label.pair_id]]
            mark = "  " if decision == expected else "!!"
            print(
                f"{index:3d}  {mark} {label.pair_id:22s} ref={reference[label.pair_id]:9s} "
                f"model={decision:25s} shared={body.get('shared_problem_if_any', '')[:38]!r}"
            )

        scored = [r for r in rows if reference[r["pair_id"]] != "UNCERTAIN"]
        same = [r for r in rows if r["decision"] == "SAME_PROBLEM_FAMILY"]
        result = VariantResult(
            variant=variant.name,
            version=variant.version,
            complexity_rank=[v.name for v in V2_VARIANTS].index(variant.name),
            scored=len(scored),
            same_predictions=len(same),
            different_predictions=sum(
                1 for r in rows if r["decision"] == "DIFFERENT_PROBLEM_FAMILY"
            ),
            abstentions=sum(1 for r in rows if r["decision"] == "ABSTAIN"),
            true_same=sum(1 for r in same if reference[r["pair_id"]] == "SAME"),
            false_same=sum(1 for r in same if reference[r["pair_id"]] != "SAME"),
            missed_same=sum(
                1
                for r in rows
                if reference[r["pair_id"]] == "SAME" and r["decision"] != "SAME_PROBLEM_FAMILY"
            ),
            agreements=sum(
                1 for r in rows if r["decision"] == expected_map[reference[r["pair_id"]]]
            ),
            abstain_on_scored=sum(1 for r in scored if r["decision"] == "ABSTAIN"),
            schema_valid=not failures,
            schema_retries=len(retries),
            input_tokens=sum(r["usage"]["input_tokens"] for r in rows),
            output_tokens=sum(r["usage"]["output_tokens"] for r in rows),
            cost_units=sum(r["usage"]["cost_units"] for r in rows),
        )
        elapsed = time.monotonic() - started
        print(
            f"    true SAME {result.true_same}  false SAME {result.false_same}  "
            f"missed {result.missed_same}  abstain {result.abstentions}  "
            f"agree {result.agreements}/{len(rows)}  "
            f"${result.cost_units:.3f}  retries {len(retries)}  {elapsed:.0f}s\n"
        )
        payload_variants.append(
            {
                "result": result.to_json(),
                "schema_retries": retries,
                "schema_failures": failures,
                "classifications": rows,
            }
        )

    out = DOCS / f"problem-family-v2-{args.run_id}.json"
    out.write_text(
        json.dumps(
            {
                "run_id": args.run_id,
                "mission": "1.27",
                "split": split.value,
                "relation": "SAME_PROBLEM_FAMILY",
                "rubric_version": "problem-family-rubric@1.0.0",
                "reference_origin": "AI_ASSISTED_PROVISIONAL",
                "human_ground_truth_established": False,
                "epistemic_note": (
                    "PROVISIONAL AGREEMENT against an AI_ASSISTED_PROVISIONAL reference. "
                    "Never accuracy, validated accuracy, or a human benchmark."
                ),
                "max_output_tokens": MAX_OUTPUT_TOKENS,
                "variants": payload_variants,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
