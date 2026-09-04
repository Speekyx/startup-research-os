# Evidence Aggregation — Calibration Strategy V1

**Status:** Preregistered strategy. **Nothing in it has been executed.**
**Outcome:** `CALIBRATION_STRATEGY_READY_REFERENCE_DATA_MISSING`
**Date:** 2026-09-03 (Mission 1.37)
**Builds on:** `docs/domain/evidence-aggregation-calibration-plan-v1.md` (Mission 1.1),
which it corrects on one point and makes executable on several.

No parameter was fitted. No profile became `CALIBRATED`. No reference label
exists, and no table in this deployment could hold one.

---

## 0. The one-sentence result

**Every Claim in SROS has exactly one Evidence row, so the aggregation layer has
never aggregated** — and a calibration dataset built from the current corpus
could only ever measure the one component this mission is forbidden to fit.

Everything below follows from reading the implementation and measuring the live
database. The measurement is in
[calibration-feasibility-audit-v1.json](calibration-feasibility-audit-v1.json)
and regenerates with `--check`.

---

## 1. What the Evidence Score means

The framework answers one question, and states it in its own §1:

> Given several Evidence records bearing on one Claim, how strongly does the
> accumulated evidence support it, how strongly does it contradict it, and how
> much do we simply not know?

And it says what that is **not**, in the sentence that decides this whole
mission:

> Not a truth estimator. Nothing here estimates whether the claim is true. Every
> quantity describes the *state of the evidence*, which is a different kind of
> thing from the state of the world.

So the construct is **evidential support strength**: a property of the evidence,
not of the world. `EvidenceScore = 82` does not mean an 82% chance the claim is
true, and `support_strength = 0.65` does not mean a 65% chance of anything.

### The correction this forces

**The Mission 1.1 calibration plan proposes the wrong target**, and this is the
substantive finding of Mission 1.37 rather than a quibble. Its §5 asks:

> Do claims scoring 70–80 resolve favourably more often than those scoring
> 30–40? Reliability diagram plus a Brier-style summary

That is an **outcome-resolution** target. It measures the state of the world, it
fits the aggregator to a construct the framework explicitly disclaims, and a
Brier score is a probability scoring rule applied to a quantity the same document
says four separate times is not a probability.

The plan contains its own counter-argument — its §5 caution warns that producing
a calibration curve "does not license describing the Evidence Score as a
probability" — and keeps the metric anyway. **Mission 1.37 resolves the
contradiction in favour of the framework.** Outcome data is not worthless; it is
the right target for a layer that predicts, and the Opportunity layer is where
that question belongs.

### The second correction, and why it restricts rather than blocks

**Nothing in the repository anchors the absolute scale.**
`scoring-framework-v1.1.md` §4.1 defines a score as "an assessed magnitude on a
defined scale" and fixes the range at 0–100. Nothing states what makes 65 correct
rather than 55 for a given evidence set. A reviewer asked for an absolute
strength has no anchor either, so agreement between reviewer and model would be
agreement on an undefined scale.

The **ordinal** construct is defined and observable: whether evidence set A
supports its claim more strongly than evidence set B supports its claim. A
reviewer can answer that without an anchor, and the model's ordering is directly
testable against theirs.

**So calibration targets ordering, and absolute level is out of scope** until the
framework supplies an anchor. That is why the outcome is not
`CALIBRATION_TARGET_SEMANTICS_UNDERDEFINED`: the construct is defined, and what
is missing restricts the metrics rather than stopping the work.

---

## 2. What is structural and what is fittable

The full classification with a recorded basis per element is in
[evidence-aggregation-calibration-strategy-v1.json](evidence-aggregation-calibration-strategy-v1.json).
The shape of it:

| Classification | Elements |
|---|---|
| `STRUCTURAL_INVARIANT` | `min()` composition · `max()` within a group · separate support and contradiction · the four masses · `100 * supported_mass` · saturation form · `repeated_signal_min_groups` floor of 2 · `multi_source_min_families` floor of 2 · category and provenance gates on levels 4 and 5 · level not falling with contradiction · EVERGREEN freshness 1.0 · missing means non-scorable, never 0.0 |
| `HUMAN_ASSESSED_INPUT` | relevance · directness · extraction confidence · **reliability** |
| `EMPIRICALLY_CALIBRATABLE_PARAMETER` | half-life `H` per claim feature · saturation damping · unknown-independence strictness · `multi_source_min_groups` above its floor · which components are required |
| `DERIVED_VALUE` | freshness · source and family counts |
| `UNRESOLVED_SEMANTIC_CHOICE` | whether `min()` should become a soft minimum · the decay functional form · what an absolute level asserts |
| `NOT_APPLICABLE` | a flat contradiction penalty — **there is no such term to fit** |

Two entries deserve their reasoning in the open.

**`min()` is structural, and its revision question is not a parameter.**
`items.py` argues it epistemically: a weighted average lets a strong dimension pay
for a weak one, and the two cases that matters for are exactly the two the system
must not get wrong. It is a conservative bound chosen so that error runs in the
recoverable direction. The prior plan calls it "a *candidate* for revision" while
conceding its rationale is "epistemic rather than empirical" — so the revision
question is recorded as an unresolved semantic choice, not as a number to fit.

**The unknown-independence rule is calibratable in degree and not in direction.**
`independence.py` says so itself: the rule "is deliberately strict, it is stated
as strict, and it is the kind of parameter calibration can later relax with
evidence." Being conservative about unlabelled provenance is structural; *how*
conservative is not.

---

## 3. `q_i = min(...)` and the Mission 1.36.1 consequence

Mission 1.36.1 measured what happens when four components are `1.0` and
reliability is `0.65`: `q = 0.65`, with `reliability` as the limiting component,
on every row.

That is **`INTENDED_CONSERVATIVE_BOUND` behaving exactly as specified**, not a
defect and not evidence that `min()` is wrong. The operator is designed to report
the weakest component, and the weakest component was reliability.

But it has a consequence the strategy must face:

> **On the current corpus, `min()` is indistinguishable from `return reliability`.**

Relevance, directness and extraction confidence are `1.0` on every Evidence row in
the deployment, and every claim is EVERGREEN so freshness is `1.0` too. The
composition rule cannot be tested against data in which only one input ever
varies.

---

## 4. The calibration unit

One unit is a **`ClaimEvidenceSnapshot`**: one Claim revision, its *complete*
eligible Evidence set, every component value as aggregation saw it, the
reliability binding per row, the independence grouping, the temporality, the
aggregation output, and one reference judgement.

Completeness is a requirement rather than a nicety. A unit built from a subset is
a unit about a different evidence set, and the reference judgement would be about
material the model never saw.

The full field contract is in
[calibration-reference-dataset-schema-v1.json](calibration-reference-dataset-schema-v1.json),
whose `units` and `labels` arrays are **empty on purpose**: an example in a schema
is what a later reader copies, and a fabricated label is indistinguishable from a
real one once it has been copied.

---

## 5. The reference target

| Target | Verdict | Why |
|---|---|---|
| **A · accountable human ordinal judgement** | **RECOMMENDED** | asks exactly the question §1 says aggregation answers, in the form the scale supports |
| B · documented external outcome | REJECTED, wrong construct | measures the state of the world; this is the prior plan's target |
| C · source-native ground truth | REJECTED, does not exist | no registered source publishes support judgements; sources publish observations |
| D · model-generated labels | FORBIDDEN | measures agreement between two assistants, which is a different claim from accuracy |
| E · Problem-Family labels | FORBIDDEN | answers a semantic equivalence question about two observations, not a support question about a claim |

**Target A, concretely.** A reviewer is shown two `ClaimEvidenceSnapshot`s and
answers one question: which is better supported by its own evidence, or are they
not distinguishable? They never see the Evidence Score, the masses, the
reliability values or another reviewer's answer.

`NOT_DISTINGUISHABLE` is a first-class answer and is never scored against the
model. Forcing a preference on a genuinely indistinguishable pair manufactures a
label.

**The reviewer count is not stated**, and §8 forbids inventing one. It follows
from the agreement statistic the gate requires and from the disagreement rate,
which is unmeasured because no pair has ever been judged. Two reviewers is the
*floor* — one reviewer produces a model of that reviewer — not a justified target.

**Disagreement is retained, never averaged.** Majority vote is refused as a
default, and `IRRECONCILABLE` is a permitted terminal state: a pair two qualified
reviewers order differently after adjudication is evidence that the pair is
near-indistinguishable.

---

## 6. Leakage, splits, and the rule that the current corpus cannot satisfy

Two snapshots can differ in every id and still be the same measurement pattern.
Wikimedia pageviews for one article on day *N* and day *N+1* share a source, a
resource, a record kind, a proposition kind, a reliability assessment and a
subject. Splitting them across train and holdout would present memorisation as
generalisation.

**The grouping rule is `(reliability_scope, proposition_kind, subject_key)`**, and
every unit sharing that tuple goes to exactly one split — enforced, not
conventional.

Holdout isolation is **structural**, following Mission 1.26: development and
holdout labels live in separate *files*, so a development loader cannot reach a
holdout label by forgetting to filter. A split column places both a metre apart
and relies on every caller remembering a rule.

**Applied to the current corpus this rule yields 2 groups among 19 scorable
units**, which cannot be split into development and holdout at all. That is a
fact about the corpus, and not an argument for weakening the rule.

A forward-time holdout is required for any temporal claim and any fitted
half-life, and is **unrunnable today**: no Claim in the deployment is temporally
sensitive.

---

## 7. Metrics, and the ones that are forbidden

Permitted, each with the failure it detects: pairwise ordinal agreement against
reviewers · rank correlation within a leakage group · monotonicity under
controlled perturbation · duplicate robustness · source-concentration robustness ·
per-mechanism ablation loss · coverage and availability rates · stability under
re-run.

**Forbidden: Brier score, reliability diagrams against outcome frequency, log
loss, AUC read as discrimination of truth, and accuracy against a thresholded
score.** The first four presume a probability or an outcome; the last invents a
decision threshold the framework does not define and then measures against it.

A metric enters the permitted list only with a stated failure it detects. A metric
chosen because it is a standard name detects nothing in particular.

### The baseline that matters

Five baselines are required, and **B-2 is the one that decides whether any of this
is worth doing**:

> **B-2 — reliability pass-through.** Report the single reliability value and
> ignore every other mechanism.

On the current corpus, the full aggregator and B-2 are **numerically identical on
19 of 19 scorable claims**. If a fitted profile cannot beat B-2, the aggregation
layer adds nothing measurable and no calibration should be claimed.

The others: B-0 the incumbent profile, B-1 a constant output, B-3 evidence count
(the mentions-equal-confidence failure the framework exists to prevent), B-4 max
`q` with no saturation and no grouping.

---

## 8. Temporal decay

**`TEMPORAL_CALIBRATION_DATA_MISSING.`** Measured: 0 temporally sensitive Claims,
0 Claims carrying a `claim_feature`, 0 authorised half-lives.

`H` cannot be fitted. No universal half-life may be chosen and no Docker half-life
may be chosen — Docker's Claims are EVERGREEN and carry no information about decay
at all. The empty `half_life_days` map stays empty, and temporally sensitive
claims keep failing closed.

Fitting would require Claims declared temporally sensitive **with a feature**, the
same proposition re-observed at several ages so decay is separable from
between-claim variation, reference judgements at more than one age, and a
forward-time holdout. A feature with insufficient data gets **no** half-life and
keeps reporting `MISSING_TEMPORAL_PARAMETER`.

---

## 9. Evidence levels, independence, contradiction, missing evidence

**Levels.** The floors and the gates are structural: "repeated" cannot mean fewer
than two, "multi-source" cannot mean one family, levels 4 and 5 require an
observation category *and* established provenance, and level never falls with
contradiction. What is validatable is `multi_source_min_groups` above its floor of
2. Nothing here is loosened because current data stays at level 1 — Mission
1.36.1 recorded that reliability could not raise the Wikimedia diagnostic above
level 1, and that is the gates working.

**Independence** is established by tracing lineage and never inferred from
difference. Different ids, dates, source families and subjects are not
independence. What is calibratable is the *strictness* of the unknown-provenance
rule, not its direction — and the prerequisite is verified lineage, which D-12
blocks. **No independence group was created by this mission**; all rows remain
`UNKNOWN`.

**Contradiction** has no penalty coefficient to fit, because there is no penalty
term: it enters continuously through `c`. Calibration would need support-only,
contradiction-only, mixed-asymmetric and genuine-conflict cases. The corpus has
**zero** contradicting Evidence rows, so three of the four masses have only ever
taken their `c = 0` values.

**Missing evidence stays missing.** `UNAVAILABLE` is not a low score. Calibration
may never map it to 0 or to 50, may not impute a component, and may not silently
drop unavailable units — they are retained and reported, so that a parameter
change which buys ordering quality by making more records non-scorable is visible
as such.

---

## 10. The echo hazard, measured

Mission 1.36.1 showed that a reliability of `0.65` with four components at `1.0`
produces `q = 0.65`. A dataset dominated by such units would reward a model for
reproducing reliability judgements and call it calibration.

**On the current corpus this is not a risk. It is the entire dataset:**

- `reliability` is the limiting component on **19 of 19** scorable claims;
- the only two distinct support strengths are **0.5** and **0.65** — exactly the
  two reviewed reliability values.

Controls: B-2 is mandatory; the dataset must contain units whose limiting
component is *not* reliability, counted and reported; correlation between the
aggregation output and reliability values is reported as a diagnostic and never as
evidence of calibration.

---

## 11. Feasibility: the answer is NO

Measured against the live database, not quoted from a report.

| | |
|---|---:|
| Claims | 28 |
| Evidence rows | 28 |
| **Distinct evidence-count-per-claim** | **[1]** |
| Claims with scorable Evidence | 19 |
| Claims `UNAVAILABLE` | 9 |
| Claims with more than one Evidence row | **0** |
| Claims with any contradiction | **0** |
| Claims with non-zero conflict mass | **0** |
| Claims with established independence | **0** |
| Temporally sensitive Claims | **0** |
| Claims carrying a `claim_feature` | **0** |
| Claims categorised MARKET_ACTIVITY or DIRECT_VALIDATION | **0** |
| Distinct proposition kinds among scorable | 2 |
| Distinct source ids among scorable | 2 |
| Distinct support strengths | **2** (`0.5` ×1, `0.65` ×18) |
| Reference-label tables present | **none** |

**What that means mechanism by mechanism.** The saturation operator has never
combined two groups on real data. Independence collapse has never collapsed
anything. `group_strength = max(members)` has never had more than one member.
Contradiction accumulation has never run. `min()` is indistinguishable from
`return reliability`. The leakage rule yields two groups, which cannot be split.

**One scope note worth stating.** The Wikimedia assessment resolves for **18**
Evidence rows, not the 6 Docker ones. Its scope is a measurement crossed with a
proposition kind and carries no subject, so it reaches the Podman and Kubernetes
rows on the same measurement. That is the reliability contract working as
designed, and it is worth saying because a review performed during a Docker
mission is easily read as being about Docker.

---

## 12. The acceptance gate

Fourteen conditions, in the JSON artifact. Eleven are quantified today. **Three
are not, and they are recorded as blockers rather than filled in:**

- **G-3** — the acceptable inter-reviewer agreement level cannot be set before the
  disagreement rate is measured.
- **G-5** — coverage adequacy per dimension depends on how many parameters a
  candidate profile moves.
- **G-8** — the margin by which a candidate must beat the reliability pass-through
  cannot be set before any ordinal agreement has been measured.

§27 and §30 both forbid inventing those numbers, and a gate weak enough for
current data to pass would not be a gate.

**Sample size is `SAMPLE_REQUIREMENT_NOT_YET_QUANTIFIED`**, with the analysis that
would settle it specified: a reviewer pilot measuring the disagreement rate, a
decision about which parameters a candidate moves, the group count after the
leakage rule, and a power analysis for the chosen statistic at the target margin.
Four of those five inputs are unmeasured because no pair has ever been judged.

There is no partial calibration. `AggregationProfileStatus` has no value for it,
on purpose.

---

## 13. What the next mission should be

**Not a labelling mission.** The blocker underneath the missing labels is that
there is nothing with the required shape to label: a reference judgement about a
single-record claim tests reliability pass-through and nothing else.

The specific precondition is architectural and already permitted: **two Signals
must interpret to the same `proposition_key`**, which is what puts two Evidence
rows on one Claim. The interpretation layer supports it; no current data does it.

**A second pilot is required**, from a substantially different domain — not
developer tooling, exercising different Evidence families, sitting in a published
product or category taxonomy (which Mission 1.35 established Docker does not),
with a route to commercial evidence at the right grain. Selected for calibration
diversity, never for ease of fetching.

**D-03 is unchanged by this mission.** Blocker 1 RESOLVED, 2 PARTIAL, 3, 4 and 5
OPEN. A strategy is not a calibration, `REFERENCE_PROFILE_V1` is still
`UNCALIBRATED`, and `services/scoring` is still blocked.
