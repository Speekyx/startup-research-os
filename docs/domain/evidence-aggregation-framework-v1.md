# Evidence Aggregation Framework V1

**Status:** Authoritative. Created in Mission 1.1, resolving **D-03 at the framework level**.
**Version:** 1.0
**Algorithm version:** 1.0.0
**Date:** 2026-08-29
**Required by:** `scoring-framework-v1.1.md` §13, which blocks `services/scoring` until this document exists and is authorised.
**Related:** `evidence-confidence-framework-v1.md`, `opportunity-ontology-v2.md` §7/§9/§14, [ADR-014](../architecture/adr/ADR-014-evidence-aggregation-reference-implementation.md).
**Reference implementation:** `packages/evidence-aggregation/`.

---

## 0. What this document resolves, and what it does not

`scoring-framework-v1.1.md` §13 lists four things as undefined and forbidden to
invent. This document defines all four:

| Open item | Resolved by |
|-----------|-------------|
| A-02 — the Evidence Score aggregation formula | §6–§8, §12 |
| A-03 — recency decay families and half-lives | §9. The **function** is defined; the **half-lives** deliberately are not |
| A-04 — the independence threshold gating evidence level 3 | §11 |
| Contradiction penalties | §8. There is no penalty; contradiction is continuous |

**It resolves the algorithm. It calibrates nothing.** Every equation here was
derived from stated requirements, not fitted to outcomes. No labelled dataset
exists. The two are separate gates and §14 keeps them separate: a defined
framework does not make production scoring available.

**Three things this framework refuses to contain**, and would be wrong to:

- a per-platform reliability coefficient (§3);
- a universal half-life (§9);
- a fixed contradiction penalty (§8).

Each would resolve an open question by choosing a number in a document nobody
would later be able to falsify.

---

## 1. What aggregation is for

Aggregation answers one question:

> Given several Evidence records bearing on one Claim, how strongly does the
> accumulated evidence support it, how strongly does it contradict it, and how
> much do we simply not know?

It is **claim-centric**. It does not produce an Opportunity Score, combine
claims, or rank anything. Its place in the chain:

```text
raw -> observation -> signal -> claim -> EVIDENCE AGGREGATION -> scored feature
                                                              -> Opportunity Score (later)
```

### What it is not

**Not a popularity counter.** `mentions == confidence` is the failure this whole
document exists to prevent.

**Not source voting.** Ten copies of one article are one observation. Ten social
posts about one announcement are one observation.

**Not a truth estimator.** Nothing here estimates whether the claim is true.
Every quantity describes the *state of the evidence*, which is a different kind
of thing from the state of the world.

---

## 2. The vocabulary

Six closed enums, declared once in `packages/contracts/schema/domain.v1.json`
and generated into TypeScript and Python (ADR-009). All are closed because each
drives exhaustive branching.

| Enum | Values |
|------|--------|
| `EvidenceDirection` | `SUPPORTS`, `CONTRADICTS`, `NEUTRAL` |
| `EvidenceIndependenceState` | `KNOWN_INDEPENDENT`, `KNOWN_DEPENDENT`, `UNKNOWN` |
| `EvidenceObservationCategory` | `STATED_OPINION`, `REPORTED_BEHAVIOUR`, `OBSERVED_BEHAVIOUR`, `MARKET_ACTIVITY`, `DIRECT_VALIDATION`, `UNCATEGORISED` |
| `ClaimTemporality` | `EVERGREEN`, `TEMPORALLY_SENSITIVE` |
| `AggregationProfileStatus` | `DRAFT`, `UNCALIBRATED`, `CALIBRATED`, `RETIRED` |
| `EvidenceAggregationStatus` | `COMPLETE`, `PARTIAL`, `UNAVAILABLE` |

`NEUTRAL` evidence is retained, explained and counted towards coverage, and
contributes to neither support nor contradiction strength.

---

## 3. Reliability is not source identity

**The framework contains no per-platform coefficient.** There is no
`reddit = 0.75`, no `github = 0.85`, and there never will be under V1.

A platform is not a reliability. The same platform carries a maintainer's
release note and an anonymous rumour; a single number cannot be right for both.
Reliability is a property of **this evidence record, against this claim, given
how it was collected**.

Source Registry metadata is legitimate *context* for a reviewer forming that
judgement — official documentation, sampling limitations, moderation, spam
exposure, API truncation, provenance — but it is context, not a coefficient.

### Policy status is not epistemic reliability

Mission 1.0 answers "may we collect this?". This framework answers "how does
this evidence bear on this claim?". They are unrelated, and connecting them
would be a category error in both directions:

- an `APPROVED` source does not produce more reliable evidence;
- a `RESTRICTED` source does not produce less reliable evidence.

**Guard.** No registered source id appears anywhere in
`packages/evidence-aggregation/`, and a test asserts it. Two evidence sets
differing only in `source_id` must produce identical numbers, and a test asserts
that too.

---

## 4. Evidence item inputs

Where available, an evidence record carries:

| Input | Range | Meaning |
|-------|-------|---------|
| `relevance` | `[0,1]` | How much this record bears on **this** claim |
| `directness` | `[0,1]` | First-hand observation versus report about a report |
| `reliability` | `[0,1]` | How much this record can be relied on, given the claim and the collection method |
| `extraction_confidence` | `[0,1]` | How confident the extraction was that the record says what we recorded |
| `freshness` | `[0,1]` | **Derived** (§9), never supplied |

Plus `direction`, `observation_category`, `independence_state`,
`independence_group_id`, `observed_at`, and provenance.

These are none of: Evidence Score, Opportunity Score, probability,
`EvidenceLevel`. `scoring-framework-v1.1.md` §4.1 governs all four scales and
this framework does not vary them.

An out-of-range factor is **rejected, not clamped**. A relevance of 1.4 means
the producer is on a different scale, and clamping would hide that behind a
plausible result.

---

## 5. Item contribution — the weakest component

```text
q_i = min(relevance_i, directness_i, reliability_i, extraction_confidence_i, freshness_i)
```

Not a weighted average. The two cases the system must not get wrong are exactly
the two an average handles worst:

- a highly relevant record from a source that cannot be relied on;
- a highly reliable source discussing something else.

An average scores both middling and lets the strong dimensions pay for the weak
one. The minimum scores both weak, which is what they are.

**The cost, stated.** `min` discards information: `(0.9, 0.9, 0.9, 0.9, 0.3)`
and `(0.3, 0.3, 0.3, 0.3, 0.3)` both give 0.3. V1 accepts this because being
wrong conservatively is recoverable and being wrong permissively produces
confident nonsense. Every component is retained in the explanation, so a
calibrated profile can revisit the operator with data behind it.

**`q` is not a probability.** It is a bounded contribution strength. No event
has this likelihood.

---

## 6. Missing inputs — non-scorable, never defaulted

If a required component is absent, the record is **NON_SCORABLE**.

It is not given `0.5`, not `1.0`, and — importantly — **not `0.0`**. A zero
would enter the arithmetic as a measured weakness; this is an absence of
measurement. An unknown number stays unknown.

A non-scorable record is still evidence. It is:

- retained in the evidence set,
- named in `missing_requirements` with the specific field that was absent,
- counted towards research completeness and coverage,
- shown in the explanation,

and contributes nothing numeric.

`aggregation_status` reports the consequence: `COMPLETE` when every record was
scorable, `PARTIAL` when some were not, `UNAVAILABLE` when none were. **An
`UNAVAILABLE` result has no Evidence Score — not a score of zero.**

---

## 7. Independence

### The model

Independence is about **provenance**, not source count.

```text
Original product announcement
  -> blog article repeating it
    -> forum post linking the article
```

Three records, one origin. Records sharing an origin belong to one
`EvidenceIndependenceGroup`.

Evidence should share a group where there is evidence of: exact duplication,
repost, quote or copy, the same original document, the same underlying dataset,
explicit derivation, syndication, or known causal lineage.

### Within a group

```text
group_strength = max(q_1 ... q_n)
```

Not the sum: ten duplicates would overwhelm one original. Not the mean: adding
weak copies of a strong observation would *weaken* it, and a duplicate is not
counter-evidence.

Every member is preserved for provenance and explanation. Only the arithmetic
collapses. The explanation records which member represented the group and how
many collapsed behind it.

### Unknown independence

`UNKNOWN` is a distinct third state and is **never silently promoted** to
`KNOWN_INDEPENDENT`.

Most evidence will be `UNKNOWN` for some time: tracing lineage is `nlp`'s job
and D-12 is open. The tempting reading is that unknown means probably
independent. It does not — records most likely to share an origin are exactly
the ones that arrive together in bulk, so unknown correlates *with* dependence.

**V1 rule.** All records whose independence cannot be established, for one claim
and one direction, form **at most one contribution group**. The strongest
counts. The rest raise observed volume and research coverage, and nothing else.

This is deliberately conservative, it is stated as conservative, and it is a
prime candidate for calibration to relax with evidence.

### Two shapes that are refused outright

- `KNOWN_DEPENDENT` with no group id asserts a dependency on nothing.
- `KNOWN_INDEPENDENT` with a group id claims independence and membership at once.

Neither is an incomplete record that conservative handling can cover, because
there is no safe reading of either. Both raise.

---

## 8. Accumulation, contradiction and the Evidence Score

### Saturation across independent groups

For independent group strengths `g_1 ... g_n`, computed **separately** for each
direction:

```text
S = 1 - PRODUCT(1 - g_i)

support_strength       = 1 - PROD(1 - support_group_strength)
contradiction_strength = 1 - PROD(1 - contradiction_group_strength)
```

Properties, all of which a plain sum fails: the result stays in `[0,1]`; one
strong observation carries its own weight; additional independent evidence
helps; marginal gain falls.

**`S` is not a probability.** The form resembles combining independent
probabilities and the resemblance is a trap — it was chosen for its shape, not
derived from a probabilistic model, and `S = 0.82` licenses no statement about
82% of anything.

### The four masses

```text
s = support_strength
c = contradiction_strength

supported_mass    = s * (1 - c)
contradicted_mass = c * (1 - s)
conflict_mass     = s * c
uncertainty_mass  = (1 - s) * (1 - c)
```

They sum to 1 algebraically, not by normalisation.

The decomposition exists because `s - c` cannot distinguish the two states a
research system most needs to tell apart. **No evidence** and **overwhelming
evidence on both sides** both net to zero. The first needs more research; the
second needs a human, because something in the market is genuinely contested.

### Contradiction is continuous, never a penalty

There is no `score -= 20 if contradicted`. Contradiction enters through `c`, so:

- a weak contradiction moves the result a little;
- a strong contradiction moves it a lot;
- several independent contradictions accumulate with the same saturation as
  support;
- duplicated contradictions cannot inflate, for the same reason support cannot.

This resolves the contradiction-penalty part of D-03 without anyone choosing a
magic number.

### Evidence Score

```text
EvidenceScore = 100 * supported_mass       0 <= EvidenceScore <= 100
```

A **score** on the canonical 0–100 scale (`scoring-framework-v1.1.md` §4.1). It
is not a confidence, not a probability, not a likelihood of truth.
`EvidenceScore = 82` does **not** mean an 82% chance the claim is true.

**Never publish it alone.** Every presentation must carry `support_strength`,
`contradiction_strength`, `conflict_mass` and `uncertainty_mass` beside it. A
score of 4 means *contested* in one evidence set and *unsupported* in another,
and only the diagnostics tell them apart.

Rounding happens at presentation (`82`, never `82.37`), never at the source —
rounding early would make a recomputation disagree with a stored result over
nothing.

---

## 9. Recency

### Temporality belongs to the claim

Not to the source. The same platform carries a pricing figure stale in a month
and a workflow observation still true in three years; a decay rate attached to
the platform would be wrong for one of them with no way to tell which.

**`EVERGREEN`** — `freshness = 1.0`. No timestamp is required, because an
evergreen claim genuinely has no decay. A fact that *stopped being true* is not
modelled as decay: it is a new contradicting observation, and it enters through
`contradiction_strength` where it is visible.

**`TEMPORALLY_SENSITIVE`** — half-life decay:

```text
freshness(age, H) = 2 ^ (-age / H)

age = 0   -> 1.00
age = H   -> 0.50
age = 2H  -> 0.25
```

Half-life rather than linear decay, because linear decay hits exactly zero at a
boundary somebody has to choose, and an old observation is weaker than a recent
one rather than worthless. Negative ages clamp to 0: an observation timestamped
slightly ahead of the clock is skew, not evidence from the future.

### No universal half-life is defined, and none may be invented

`H` belongs to a versioned aggregation profile, keyed by claim feature.
Categories that may eventually receive **different calibrated** half-lives
include pricing, trend momentum, product availability, regulation, user pain and
long-lived workflow behaviour. **No value is assigned to any of them here.**

If a temporally sensitive claim has no authorised half-life:

```text
MISSING_TEMPORAL_PARAMETER  ->  the record is NON_SCORABLE
```

Fail closed. Any number chosen here would work, would be recorded nowhere as a
guess, and would silently propagate into every downstream score — which is
precisely the failure D-03 was raised to prevent.

`REFERENCE_PROFILE_V1` therefore ships with **no half-lives at all**, and a test
asserts that it stays that way.

---

## 10. Evidence Level

`EvidenceLevel` (0–5, `evidence-confidence-framework-v1.md` §2) is preserved
unchanged in meaning. It is **not derived from EvidenceScore**, and no threshold
such as "80 = level 4" exists.

They answer different questions. The score says how strongly the accumulated
evidence supports the claim; the level says **what kind of evidence exists at
all**. One recorded payment is Level 5 with a modest score; ten thousand
enthusiastic comments are Level 1 with a high one. Deriving one from the other
erases exactly that.

### Advancement rules

| Level | Requires |
|-------|----------|
| 0 Hypothesis | no scorable supporting evidence |
| 1 Weak Signal | ≥1 scorable supporting record |
| 2 Repeated Signal | ≥ `repeated_signal_min_groups` supporting groups **of established independence** |
| 3 Strong Multi-Source | ≥ `multi_source_min_groups` groups of established independence **and** ≥ `multi_source_min_families` source families |
| 4 Market Evidence | ≥1 supporting record categorised `MARKET_ACTIVITY` or `DIRECT_VALIDATION`, **with established provenance** |
| 5 Direct Validation | ≥1 supporting record categorised `DIRECT_VALIDATION`, **with established provenance** |

The level is the highest whose own conditions hold.

**Independence gates 2 and 3.** *Repeated* means separate observations, not
separate copies.

The unknown-provenance bucket is **excluded from these counts entirely** — not
counted as one group. One record of established provenance plus ten unlabelled
ones is not two observations, because the ten may all derive from the one.
Unlabelled evidence therefore cannot reach Level 2 alone *or* in combination
with established evidence; it can only reach Level 1.

Note this is stricter than the rule for `support_strength`, where the unknown
bucket does contribute one group's worth of strength. The asymmetry is
deliberate: strength is a magnitude and the bucket genuinely represents at least
one real observation, whereas the level asserts *repetition*, which requires
knowing that two observations are distinct.

**Category gates 4 and 5, and quantity cannot substitute.** No accumulation of
`STATED_OPINION` becomes market activity, however large. The provenance
requirement matters here too: a record whose origin was never traced may be a
syndicated copy, and "Market Evidence" resting on one would be the same failure
wearing a better label.

**The ladder is not strictly nested at the top,** deliberately. A single
recorded preorder reaches Level 5 without three independent supporting groups,
because the kind of evidence dominates its quantity — `evidence-confidence-framework-v1.md`
§2 lists "user interviews" as a Level 5 example in the singular.

### V1 thresholds

`repeated_signal_min_groups = 2`, `multi_source_min_groups = 3`,
`multi_source_min_families = 2`.

These are **structural minimums, not fitted values**: "repeated" cannot mean
fewer than two and "multi-source" cannot mean one source. They live in the
profile, so a calibrated profile may raise them; the model refuses values below
the definitional floor.

### Level does not fall with contradiction

A contested claim still has whatever evidence it has. `EvidenceLevel` describes
supporting evidence maturity only, which is why it must never be read alone —
`contradiction_strength` and `conflict_mass` accompany it in every result.

---

## 11. Source diversity — diagnostic, never a multiplier

Tracked and reported: `source_count`, `source_family_count`,
`independence_group_count`, `support_group_count`,
`contradiction_group_count`, `unknown_independence_count`.

**No diversity bonus is added to the Evidence Score in V1.** Diversity is
diagnostic, it is relevant to `EvidenceLevel` (§10) and to research
completeness, and it is not a hidden multiplier. A bonus would require a
coefficient nobody has data for.

### Counts must not be presented as sample size

`raw_evidence_count` is not an independent sample size and must never be
displayed as one. `scorable_evidence_count`, `independence_group_count` and
`unknown_independence_count` are reported separately so a reader can see the
difference between records collected and observations obtained.

V1 introduces **no effective-N statistic**. Calling anything here a statistical
`N` would assert sampling assumptions this model does not make.

---

## 12. Aggregation profiles

An `EvidenceAggregationProfile` carries: `profile_id`, `version`, `status`,
`algorithm_version`, `applies_to`, `default_temporality`, `half_life_days`,
`required_item_fields`, `level_thresholds`, `calibration_dataset_ref`,
`calibrated_at`, `notes`.

**Two versions, because two things move independently.** `algorithm_version`
changes when the equations change; the profile `version` changes when a
parameter does. A single version would hide which one moved.

### Status gates

| Status | Runnable |
|--------|----------|
| `DRAFT` | No |
| `UNCALIBRATED` | Only with an explicit `allow_uncalibrated=True`, and the result carries a warning |
| `CALIBRATED` | Yes. Requires a `calibration_dataset_ref` — a calibration nobody can re-run is a claim, not a calibration |
| `RETIRED` | No. Kept so historical results stay readable |

**Production research requires `CALIBRATED`.** See §14.

`REFERENCE_PROFILE_V1` is `UNCALIBRATED` with empty `half_life_days`. That is
the honest state of the system, and the mechanism that makes it visible.

---

## 13. Result, reproducibility and explanation

### The result

`EvidenceAggregationResult` carries at minimum: `claim_id`, the profile id,
version and status, `algorithm_version`, `evidence_score`, the two strengths,
the four masses, `evidence_level`, all six counts, `missing_requirements`,
`aggregation_status`, `computed_at`, and `evidence_snapshot_digest`.

### Reproducibility

**Same snapshot + same profile → byte-identical canonical output.** Guaranteed
by construction, not hoped for:

- group strengths are sorted before summation, because floating-point addition
  is not associative;
- group members and result contributions are sorted by id;
- `computed_at` is excluded from the canonical form, since a wall-clock field
  would make byte-equality untestable.

`evidence_snapshot_digest` is a SHA-256 over the canonical form of the
contributions actually used. If evidence appeared, expired, or an extraction
confidence was revised, the digest changes — so a recomputation is *identifiable
as* a recomputation rather than silently replacing the original.

D-08 (score recomputation policy) is **not resolved here**. Nothing in this
design makes resolving it harder: the ingredients for distinguishing an original
result from a recomputed one are recorded.

### Explanation — no score without lineage

Every result supports an explanation showing which records were considered;
which were non-scorable and precisely why; which shared an independence group;
which member represented each group and how many collapsed; every `q` and every
component behind it; the freshness calculation; support and contradiction
aggregation separately; the final mass decomposition; and the profile version.

---

## 14. Calibration — the second gate

**A defined framework is not a calibrated one.** Mission 1.1 defines the
algorithm. It fits no parameter to any outcome, because no labelled dataset
exists.

The two gates are independent:

```text
Framework Defined     <- Mission 1.1 does this
Profile Calibrated    <- requires labelled data. NOT DONE
```

Until a `CALIBRATED` profile exists, `services/scoring` remains **unavailable
for production research**. Synthetic and experimental evaluation may use an
`UNCALIBRATED` profile only when explicitly labelled as such, and the engine
refuses to run one unless the caller says so.

This framework must never be described as statistically validated. It has not
been evaluated against outcomes at all. See
[`evidence-aggregation-calibration-plan-v1.md`](evidence-aggregation-calibration-plan-v1.md).

---

## 15. Numerical behaviour

All factors are validated on `[0,1]`; out-of-range values raise. Clamping is
applied **only** to floating-point noise of order 1e-16 after an operation whose
inputs were already validated — never to an invalid input.

The saturation operator uses the log form `-expm1(Σ log1p(-g))`, which stays
accurate when every `g` is tiny and the naive `1 - Π(1-g)` would cancel. A group
strength of exactly 1.0 is special-cased, since `log1p(-1)` is a domain error
rather than the `-inf` the limit wants.

The mass decomposition asserts its own sum-to-one identity as a guard against a
future "simplification" of one of the four lines.

---

## 16. Known limitations

Recorded rather than smoothed over. Both are calibration targets, and neither is
fixed by choosing a constant now.

**The score saturates towards 100.** Twenty independent strong groups present as
`100`, which reads as certainty, and no evidence set justifies certainty. The
operator is behaving as defined; the problem is how the output reads.
`EvidenceLevel` does not move with the score and `uncertainty_mass` goes
honestly to zero, which limits the damage without fixing it. **First-priority
calibration target.** Adding a damping constant now would mean choosing its
value with no data — the exact failure D-03 exists to prevent, committed while
resolving it.

**Group count dominates group quality.** Twelve weak independent groups outscore
one strong group. That is defensible in itself, but it places the entire weight
of the model on the independence judgement: twelve records wrongly labelled
independent produce the same number as twelve real ones. The conservative
unknown-provenance rule mitigates unlabelled records; it cannot mitigate
*incorrectly* labelled ones, which is a data-quality problem for `nlp`
deduplication (D-12).

See [`evidence-aggregation-sensitivity-v1.md`](evidence-aggregation-sensitivity-v1.md)
for the full analysis and the numbers behind both.

---

## 17. Boundaries

**Not implemented by this framework, and not to be inferred from it:**
Opportunity Score, Market Score, Momentum, Competition Gap, Monetization,
Feasibility, or any cross-claim combination. Mission 1.1 concerns evidence
aggregation only.

**`services/scoring` remains unbuilt.** The reference implementation in
`packages/evidence-aggregation/` exists to test this specification, run
synthetic cases, prove reproducibility and serve as an implementation oracle. It
reads no database, opens no network connection, and is wired into no request
path.

**Still open:** D-08 (recomputation policy), D-12 (embeddings and
deduplication, which independence detection ultimately depends on), A-01
(scoring-profile weight vector shape), A-12 (non-geographic scoping).
