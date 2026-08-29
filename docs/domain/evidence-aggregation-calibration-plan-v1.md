# Evidence Aggregation — Calibration Plan V1

**Status:** Plan. **Nothing in it has been executed.**
**Version:** 1.0
**Date:** 2026-08-29
**Governs:** how the parameters in `evidence-aggregation-framework-v1.md` will be
fitted and evaluated once labelled data exists.

---

## 0. What this document is, and what it is not

This is a **plan**. No method described here has been run, no dataset described
here exists, and no parameter has been fitted to anything.

Saying so plainly matters more than it might appear. A calibration plan that
reads as though it had been carried out is how a system acquires the language of
statistical validation without the substance of it. Every method below is
written in the future tense on purpose.

**The current state, stated once:**

```text
Algorithm       DEFINED       Mission 1.1
Parameters      NOT FITTED    no labelled dataset exists
Profile         UNCALIBRATED  reference-v1
Production      BLOCKED       services/scoring requires a CALIBRATED profile
```

---

## 1. What actually needs calibrating

Not everything in the framework is a free parameter. Distinguishing the two
keeps calibration honest about its own scope.

### Structural — derived from meaning, not from data

These follow from what the words mean and would not change if data disagreed.
They are not calibration targets.

- `q = min(components)` — the conservative operator (a *candidate* for revision,
  see §2, but its rationale is epistemic rather than empirical)
- `group_strength = max(members)` — duplicates must not multiply
- separate support and contradiction aggregation
- the four-mass decomposition
- `EvidenceScore = 100 * supported_mass`
- levels 4 and 5 requiring an observation category
- "repeated" needing at least two, "multi-source" needing at least two families

### Empirical — genuinely open, and currently unset

| # | Parameter | Current | Why it needs data |
|---|-----------|---------|-------------------|
| **P-1** | Half-life per claim feature | **none** | Nothing is known about how fast any claim category decays. `MISSING_TEMPORAL_PARAMETER` until measured |
| **P-2** | Saturation damping | none | Finding S-1: the score reaches 100. Whether that needs correcting, and by how much, is an empirical question |
| **P-3** | Unknown-independence rule | all-in-one-group | Deliberately strict. Data may show it is too strict — or not strict enough |
| **P-4** | `multi_source_min_groups` | 3 | The definitional floor is 2; whether 3 predicts better is measurable |
| **P-5** | `multi_source_min_families` | 2 | As above |
| **P-6** | Required item fields | all five | Whether `directness` earns its place, or whether a sixth dimension is needed |

**P-1 and P-2 are the priorities.** P-1 blocks every temporally sensitive claim
today. P-2 is the framework's most visible weakness.

---

## 2. Open questions the plan must answer, not assume

Two design choices are defensible and unproven. Calibration is where they get
tested rather than defended.

**Is `min` right?** It is conservative by construction, which is the reason it
was chosen. But it discards information — five components at 0.9 with one at 0.3
score identically to all six at 0.3. A candidate alternative is a soft-minimum
that still refuses to let strength pay for weakness while retaining some
gradient. The ablation in §5 tests `min` against alternatives on ranking quality.

**Is noisy-OR saturation right?** It has the required shape but no probabilistic
derivation. If calibration finds it systematically overconfident, the remedy is a
fitted correction with a recorded dataset behind it — never a constant chosen to
make the numbers look better.

---

## 3. The calibration dataset

### Required contents

Per claim:

| Field | Why |
|-------|-----|
| claim text and type | The unit of aggregation |
| `ClaimTemporality` | P-1 cannot be fitted without knowing which claims decay |
| claim feature/category | Half-lives are per feature |
| market, geography, language | Bias evaluation (§6) |
| ground-truth outcome | The label. What actually happened |
| outcome observation date | Temporal holdout depends on it |
| label provenance and annotator | An unattributable label cannot be audited |

Per evidence record: every field in `evidence-aggregation-framework-v1.md` §4,
plus `observed_at`, `collected_at`, source id and family, and — critically —
**the true provenance relationships**. Independence is the model's most
load-bearing input, so a dataset without verified lineage cannot calibrate it.

### The hard part

**Ground truth is expensive and mostly absent.** For most claims about a market
there is no clean later fact that settles them. The dataset will be small,
biased towards claims that happened to become resolvable, and that bias is itself
a finding to record rather than a nuisance to work around.

**Verified provenance is harder still.** It requires knowing that record B was
derived from record A, which is exactly what `nlp` deduplication (D-12) does not
yet do. Until then, provenance must be annotated by hand, which bounds the
dataset size further.

Both are reasons the plan is a plan.

---

## 4. Method

### 4.1 Labelling

Combine, and record which produced each label:

- **Historical resolution** — claims whose outcome later became observable.
  Cheapest and least biased, but limited to claims that resolve.
- **Expert annotation** — domain reviewers labelling claim/evidence pairs.
  Requires ≥2 independent annotators and a reported agreement statistic; a
  single annotator produces a model of that annotator.
- **Adjudication** — a documented procedure for disagreements. Not majority
  vote by default; disagreement is often information about the claim.

### 4.2 Splitting

**Temporal holdout, not random split.** Fit on claims resolved before a cut
date, evaluate after it. A random split leaks the future into the past through
correlated claims and will overstate performance.

**Cross-market validation.** Fit on one market, evaluate on another. This is the
test the engine most needs to pass: it is meant to work across markets, and a
model that only works where it was fitted is a model of that market.

### 4.3 Fitting

- **P-1 half-lives** — for each claim feature, fit `H` by maximising the
  agreement between freshness-weighted evidence and observed outcomes. Report a
  confidence interval per feature. **A feature with too little data gets no
  half-life**, and continues to report `MISSING_TEMPORAL_PARAMETER`. Fitting a
  number to eight examples and shipping it would defeat the point of §19.
- **P-2 damping** — fit any correction against calibration curves (§5), not
  against how the scores look.
- **P-3 to P-5** — grid search over small integer/rule spaces, scored on ranking
  quality with the ablation in §5.

---

## 5. Evaluation

| Method | Question |
|--------|----------|
| **Calibration curve** | Do claims scoring 70–80 resolve favourably more often than those scoring 30–40? Reliability diagram plus a Brier-style summary |
| **Rank correlation** | Spearman between Evidence Score and outcome, per market and language |
| **Ablation** | Remove one mechanism at a time — independence collapse, freshness, the `min` operator, the category gate — and measure the loss. A mechanism that costs nothing to remove is not earning its complexity |
| **Duplicate robustness** | Inject verified duplicates. Score must not move. This holds by construction and is re-verified against real data |
| **Source concentration robustness** | Re-score with evidence concentrated on one platform. A large move means source identity is leaking in |
| **Temporal stability** | Re-score historical claims with a later clock. Movement should come from decay alone |
| **Sensitivity re-run** | The synthetic harness, against every candidate profile |

**A caution about calibration curves.** Producing one does not license
describing the Evidence Score as a probability. A well-calibrated score is
*correlated* with outcomes; the framework still makes no claim that
`EvidenceScore = 82` means 82% of anything, and `evidence-aggregation-framework-v1.md`
§8 does not change if the curve looks good.

---

## 6. Bias evaluation — mandatory, not optional

Evidence popularity must not silently become truth. Each of these is evaluated
and **reported even when the result is unflattering**.

| Bias | What to measure |
|------|-----------------|
| **English-language dominance** | Score distribution and rank correlation per language. If the model only works in English, say so rather than reporting the aggregate |
| **Geographic concentration** | Same, per market. The engine targets global markets; a US-only calibration is a US-only model |
| **Platform demographics** | Whether score correlates with platforms whose user base skews young, technical or Anglophone |
| **Source-family concentration** | Whether one family dominates high-scoring claims |
| **Survivorship** | Claims only enter the dataset if they became resolvable. Quantify what that excludes |
| **Moderation effects** | Removed or downranked content is missing evidence, not absent evidence |
| **Popularity bias** | Whether volume predicts the label better than the model does. If it does, the model is a mention counter with extra steps |
| **Syndication** | Whether syndicated content survives the independence rules in real data as it does in synthetic data |

**Do not calibrate only on English-US examples.** A calibration report without a
per-language and per-market breakdown is incomplete and must not be used to
promote a profile to `CALIBRATED`.

---

## 7. Promotion to CALIBRATED

A profile may become `CALIBRATED` only when all of the following hold:

1. A calibration dataset exists, is versioned, and is referenced by
   `calibration_dataset_ref`.
2. Labels have recorded provenance and, for expert labels, an inter-annotator
   agreement statistic.
3. Fitting used a temporal holdout, and cross-market validation was run.
4. The calibration curve, rank correlations and ablations are published.
5. The bias evaluation in §6 is complete, including the unflattering parts.
6. Duplicate and source-concentration robustness were re-verified on real data.
7. The synthetic sensitivity harness passes against the candidate profile.
8. Every fitted parameter has a stated uncertainty. A point estimate with no
   interval is a guess with a decimal point.
9. Any claim feature with insufficient data has **no** half-life, and continues
   to fail closed.

Falling short of any of these means the profile stays `UNCALIBRATED`. Partial
calibration is not calibration, and the status enum has no value for it on
purpose.

---

## 8. What happens if calibration fails

A real possibility, and worth planning for rather than discovering.

If evidence aggregation shows no useful correlation with outcomes, the correct
response is to say so and to keep `services/scoring` unavailable — not to adjust
parameters until something correlates. Fitting until a metric moves, on a small
biased dataset, produces a model of the dataset.

Intermediate outcomes are likelier than either extreme: the model may work for
some claim categories and not others, or in some markets and not others. The
profile mechanism supports exactly that — `applies_to` scopes a calibrated
profile to where its calibration holds, and claims outside it keep failing
closed.
