# Evaluation Framework V1

**Status:** Authoritative
**Version:** 1.0
**Date:** 2026-08-29
**Authorized by:** Sprint 0 / Mission 0.4, §24–§27
**Governs:** `llm-reasoning-rules.md` §10 (Evaluation), §9 (Reproducibility)
**Implemented in:** `packages/llm-gateway/python/sros_llm_gateway/evaluation/`

---

## 1. Purpose

`llm-reasoning-rules.md` §10 states the requirement and the reason in two
sentences: *"LLM components require explicit evaluation datasets. Do not assume
that a fluent answer is a correct answer."*

This framework is what makes the second sentence enforceable. Without it, the
only available measure of an LLM component is whether its output reads well,
which is precisely the property a language model optimises and precisely the
property that carries no information about correctness.

It exists **before** any LLM component does, and that ordering is deliberate. A
framework built after the first classifier is a framework shaped to make that
classifier look acceptable.

## 2. What an evaluation run records

Every run records all of the following. A run missing any of them cannot be
compared with another run, and `compare_runs` refuses rather than adjusting.

| Field | Why it is required |
|-------|--------------------|
| dataset id and **version** | A dataset change alters what the metric means |
| task | Determines which metrics are meaningful (§5) |
| `synthetic` flag | See §4 — this one is load-bearing |
| provider and **model**, pinned explicitly | A score attributed to the wrong model is worse than no score |
| prompt id and version | `llm-reasoning-rules.md` §9. A prompt change is a behaviour change |
| parameters | Temperature and the rest change outputs |
| `fallback_enabled`, always false | ADR-006: a silent fallback measures a different model |
| timestamp | When the provider's model was what it was |
| per-item latency and cost | Recorded, never quality (§6) |
| per-item expected, predicted, confidence, schema validity, error | The result, at the granularity a disagreement can be inspected at |

`RunConfig` **refuses to construct** without a provider and a model, and refuses
with `fallback_enabled=True`. Those are the two fields most likely to be left
unset by someone in a hurry, and each one silently invalidates the run.

## 3. Dataset format

Versioned JSON. `dataset_id` plus `version` is the identity; the version is part
of every comparison.

```json
{
  "dataset_id": "claim-classification-synthetic",
  "version": "1.0.0",
  "task": "CLAIM_CLASSIFICATION",
  "synthetic": true,
  "description": "what this measures, and what it does not",
  "output_schema": { "…": "for structured tasks" },
  "items": [
    { "item_id": "obs-1", "input": {}, "expected": "OBSERVED", "tags": ["clear"] }
  ]
}
```

`expected` is deliberately untyped. A classification expects a label, an
extraction expects an object, a synthesis task may expect a set of required
assertions. Forcing one shape would push every task toward classification, which
is the failure §5 exists to prevent.

An **empty dataset is refused**: it produces metrics that look like a perfect
score.

### Supported tasks

`CLAIM_CLASSIFICATION`, `PAIN_DESIRE_EXTRACTION`, `OPPORTUNITY_CLASSIFICATION`,
`STRUCTURED_EXTRACTION`, `CONTRADICTION_DETECTION`, `RESEARCH_SYNTHESIS`.

Closed, because adding a task changes which metrics are meaningful.

## 4. Synthetic versus real, and why the flag travels

**Every dataset declares whether it is synthetic, and the flag is carried into
the run and into the comparison report.**

A metric computed over invented examples measures whether the *machinery* works.
A metric computed over real labelled data measures whether the *model* works.
Reporting the first as if it were the second is the same error as reporting an
`ESTIMATED` Research Completeness as `MEASURED`, and it is made for the same
reason: the number is available and the distinction is inconvenient.

**Everything shipped in this repository today is synthetic.** The
`claim-classification-synthetic` fixture is eight invented statements written to
be unambiguous — the opposite of what a real evaluation set needs. It exists to
prove the runner, the metrics, the store and the comparison work end to end.

A production evaluation set requires labelled examples drawn from collected
sources. **D-07 blocks collection**, so it cannot be built yet, and building a
plausible-looking one instead would produce numbers that are worse than none:
they would be quoted.

## 5. Metrics are chosen by the task

`METRICS_FOR_TASK` maps each task to what is meaningful for it.

| Task | Metrics | Primary |
|------|---------|---------|
| `CLAIM_CLASSIFICATION` | accuracy, macro-F1, Brier | macro-F1 |
| `OPPORTUNITY_CLASSIFICATION` | accuracy, macro-F1, Brier | macro-F1 |
| `PAIN_DESIRE_EXTRACTION` | precision, recall, F1 | F1 |
| `STRUCTURED_EXTRACTION` | schema validity, exact match, F1 | schema validity |
| `CONTRADICTION_DETECTION` | precision, recall, F1 | F1 |
| `RESEARCH_SYNTHESIS` | schema validity | schema validity |

Three choices in that table are worth their reasoning:

**Accuracy is not computed for structured extraction.** It would measure
whole-output equality under a name that reads like partial credit. What matters
there is whether the output validates and whether the fields match.

**Macro-F1, not micro, for classification.** The classes are deliberately
imbalanced: `HYPOTHESIS` is rarer than `OBSERVED` and matters more — it is the
label that stops a plausible idea from reading as a finding
(`evidence-confidence-framework-v1.md` §9). A micro average lets a model that
never predicts the rare class score well.

**Research synthesis is barely scored automatically.** It has no single correct
answer. Only the mechanical property is measured; the rest needs human review
(`llm-reasoning-rules.md` §11). Assigning it an accuracy would be the "fluent
answer is a correct answer" assumption wearing a number.

### Calibration

The Brier score, over items where the model expressed a confidence. **Lower is
better** — it is a loss, and the only inverted metric here, which is why
`HIGHER_IS_BETTER` states the direction of every metric explicitly rather than
leaving it to convention. A comparison that assumed otherwise would report every
calibration improvement as a regression.

Items with no expressed confidence are **excluded** rather than defaulted to
0.5. Defaulting would manufacture the very quantity being measured.

## 6. Cost and latency are recorded, never quality

They are computed on every run and reported next to the quality metrics. They
are **not** in `QUALITY_METRICS`, and only quality metrics can produce a
regression verdict.

That exclusion is what makes §7 enforceable rather than aspirational. Any scheme
that let cost and quality trade against each other would be tuned, eventually
and reasonably, until every upgrade passed.

## 7. Regression comparison

```text
compare_runs(baseline, candidate, tolerance) -> IMPROVED | UNCHANGED | REGRESSED | INCOMPARABLE
```

**A quality drop beyond the tolerance is a regression, and a cheaper candidate
is still rejected.** When the candidate is cheaper *and* worse, the report says
so in a note rather than leaving a reader to notice: *"the candidate is cheaper
by N cost units and is still rejected: cost does not offset quality."*

**The tolerance is configurable and defaults to 0.01.** The right value depends
on the sample size; a single tolerance for every task would be wrong for most.

**Runs over different datasets, different dataset versions or different tasks
are `INCOMPARABLE`.** Refusing beats adjusting: a delta across different data is
wrong in a way that looks precise.

### Nothing is rolled out

§27: *"Do not automate production rollout yet."*

`compare_runs` returns a verdict. It does not promote a model, edit routing
configuration or touch a tier binding, and `ComparisonReport` has no `promote`
or `deploy` — a test asserts their absence. `report.accepted` means *may be
considered for promotion by a human*, and is the input to a decision rather than
the decision.

## 8. Storage

One JSON file per run, named by run id, under a directory chosen by the caller.

**Not a database table.** Evaluation results describe the system, not a
workspace: giving them a `workspace_id` would attach a meaning they do not have,
and tying a developer-facing benchmark to a running PostgreSQL makes it
something that cannot be run when it is most needed.

**Overwriting a stored run is refused.** A result is the record of what a
configuration scored on a date; overwriting one destroys the evidence that every
comparison built on it was valid.

## 9. Running a model under evaluation

The evaluated model is a callable:

```python
EvaluatedModel = Callable[[EvaluationItem, EvaluationDataset], Prediction]
```

A fake model, a recorded fixture and a real gateway call are therefore all
evaluable through one path. That is what lets the framework be proved without a
provider key, and it is the same reasoning ADR-009 gives for the zero-dependency
contract checks.

**A model that raises does not abort the run.** The item is recorded with its
error and counted as incorrect, and `error_rate` is a reported metric. A
benchmark that stops on the first failure reports nothing about the other
ninety-nine items, and "it crashed on item three" is itself a result.

## 10. What this framework does not do

Recorded so the gaps are visible rather than assumed filled.

| Not done | Why |
|----------|-----|
| Real evaluation datasets | Needs labelled examples from collected sources. **Blocked on D-07** |
| Evaluation of any production component | No LLM component exists: `nlp` is out of scope, `scoring` is blocked on D-03 |
| Human review workflow | `llm-reasoning-rules.md` §11 requires low-confidence conclusions to be reviewable. The framework records what a reviewer would need; the workflow is not built |
| Inter-annotator agreement | A labelling process does not exist yet, so there is nothing to measure agreement over |
| Statistical significance | With eight synthetic items it would be theatre. It becomes necessary with a real dataset, and it is the first thing to add then |
| Automated rollout | Forbidden by §27 |
| Cross-provider replay | ADR-006 makes it possible (a task can be replayed across providers because callers request a tier). No component exists to replay |

## 11. Versioning

This document is V1. A material change — a new task, a changed metric mapping, a
changed comparison rule — creates V2 and, where architectural, an ADR.

Datasets version independently, and a dataset version change makes runs
incomparable by design (§7).

## 12. Open items

| Item | Status |
|------|--------|
| Real datasets for every task | **Blocked on D-07** |
| Statistical significance testing | Open. Required before any real dataset is trusted |
| Human review workflow and its interface | Open (`llm-reasoning-rules.md` §11) |
| Whether evaluation runs belong in CI, and at what cadence | Open. They cost money against a real provider, and §20 keeps that opt-in |
| Calibration targets — what Brier score is acceptable | Open. Requires a real dataset to be answerable at all |
