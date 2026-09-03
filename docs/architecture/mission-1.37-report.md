# Mission 1.37 — Evidence Aggregation Calibration Strategy V1

**Outcome: `CALIBRATION_STRATEGY_READY_REFERENCE_DATA_MISSING`** (§40 A).

No parameter was fitted, no profile became `CALIBRATED`, no reference label
exists, and no table in this deployment could hold one.

**The one-sentence result:** every Claim in SROS has exactly one Evidence row, so
**the aggregation layer has never aggregated** — and a reference set built from
the current corpus could only measure the one component this mission is forbidden
to fit.

---

## §-1 — Branch precondition: SATISFIED

Mission 1.37 runs on a branch containing every Mission 1.36.1 change. Verified
before anything else, against the working tree rather than against a PR:

| | |
|---|---|
| Wikimedia `ReliabilityAssessment` workflow | present |
| corrected `ReliabilityBasisType` values | present, 0 invented `basis_type` remain |
| corrected `binding.version` access | present |
| Docker diagnostic aggregation artifact | present |
| Mission 1.36.1 tests | present |
| `docs/CLAUDE.md` / `PROJECT_MANIFEST.md` | 1.66 / 1.65 |

PR #77 is open and unmerged, which §-1 anticipates: its STOP applies only when
*the current working branch does not contain* those changes. This one does, so
nothing was reimplemented and no calibration design rests on pre-1.36.1 state.

---

## §41 — The forty-five questions

**1. What exactly does Evidence Score mean?**
**Evidential support strength**: how strongly the accumulated evidence supports a
bounded Claim, how strongly it contradicts it, and how much is unknown. The
framework's §1 states it and the mass decomposition carries all three parts
separately. `EvidenceScore = 100 * supported_mass`.

**2. What does it explicitly NOT mean?**
Framework §1, in its own words: *"Not a truth estimator. Nothing here estimates
whether the claim is true. Every quantity describes the state of the evidence,
which is a different kind of thing from the state of the world."* Not a
probability, not a confidence, not popularity, not source voting, not an
Opportunity Score, and not a prediction of anything.

**3. What exact aggregation formula is active?**

```text
q_i  = min(relevance, directness, reliability, extraction_confidence, freshness)
freshness = 1.0 if EVERGREEN, else 2^(-age_days / H), MISSING_TEMPORAL_PARAMETER if H absent
g    = max(q_i within an independence group); unknown provenance is ONE group per direction
S    = 1 - prod(1 - g)              computed as -expm1(sum(log1p(-g))) over sorted inputs
supported = s(1-c)   contradicted = c(1-s)   conflict = sc   uncertainty = (1-s)(1-c)
EvidenceScore = 100 * supported_mass
```

**4. Which elements are `STRUCTURAL_INVARIANT`?**
`min()` composition · `max()` within a group · separate support and contradiction
aggregation · the four-mass decomposition · the saturation form · `100 *
supported_mass` · `repeated_signal_min_groups` floor of 2 ·
`multi_source_min_families` floor of 2 · the category and provenance gates on
levels 4 and 5 · level not falling with contradiction · EVERGREEN freshness 1.0 ·
missing means non-scorable and never 0.0.

**5. Which are `HUMAN_ASSESSED_INPUT`?**
relevance, directness, extraction confidence, and **reliability**.

**6. Which are `EMPIRICALLY_CALIBRATABLE_PARAMETER`?**
half-life `H` per claim feature · saturation damping · the strictness of the
unknown-independence rule · `multi_source_min_groups` above its floor · which
components are required.

**7. Which remain unresolved semantic choices?**
Whether `min()` should become a soft minimum (U-1) · the decay functional form,
since `recency.py` argues only against *linear* decay (U-2) · what an absolute
level asserts (U-3).

**8. Is `q_i = min(...)` structural or a calibration hypothesis?**
**`INTENDED_CONSERVATIVE_BOUND`, i.e. structural.** `items.py` argues it
epistemically: a weighted average lets a strong dimension pay for a weak one, and
the two cases that matters for are the two the system must not get wrong. It is
chosen so error runs in the recoverable direction. The Mission 1.36.1 behaviour —
four components at 1.0 and reliability 0.65 giving `q = 0.65` — is that operator
working exactly as specified.

**The consequence is still uncomfortable and must be recorded:** on the current
corpus `min()` is **indistinguishable from `return reliability`**, because the
other four components are 1.0 on every row.

**9. What is the calibration unit?**
A **`ClaimEvidenceSnapshot`**: one Claim revision, its *complete* eligible
Evidence set, every component value as aggregation saw it, the reliability
binding per row, the independence grouping, the temporality, the aggregation
output, and one reference judgement. Completeness is required — a unit built from
a subset is a unit about a different evidence set.

**10. What reference target is recommended?**
**A — accountable human ordinal judgement.** A reviewer is shown two snapshots
and answers which is better supported by its own evidence, or that the two are
not distinguishable.

**11. Why does that target measure the intended construct?**
Because it asks the question framework §1 says aggregation answers, in the form
the scale supports. **The absolute scale has no anchor** — `scoring-framework-v1.1.md`
§4.1 fixes 0–100 and nothing states what makes 65 correct rather than 55 — so a
reviewer asked for an absolute strength has no anchor either. The *ordinal*
construct is defined and observable, and the model's ordering is directly
testable against a reviewer's.

**12. Which target alternatives were rejected?**

| Target | Verdict |
|---|---|
| documented external outcome | **REJECTED_WRONG_CONSTRUCT** — measures the state of the world |
| source-native ground truth | REJECTED, does not exist; sources publish observations, not support judgements |
| model-generated labels | FORBIDDEN (§8, §35) |
| Problem-Family labels | FORBIDDEN (§9) |

**This is where Mission 1.37 corrects the Mission 1.1 plan.** That plan's §5 asks
*"Do claims scoring 70–80 resolve favourably more often than those scoring
30–40? Reliability diagram plus a Brier-style summary"* — an outcome-resolution
target with a probability scoring rule, applied to a quantity the framework says
four times is not a probability. The plan contains its own counter-argument in
the same section and keeps the metric anyway. The contradiction is resolved in
favour of the framework.

**13. May an LLM create reference labels?**
**No.** §8 and §35, and the Mission 1.25 correction: an AI-assisted reference
measures agreement between two assistants, which is a real finding and a
different claim from accuracy. A model may prepare material for a reviewer and
may never be the reference.

**14. How is reviewer disagreement represented?**
Retained per pair, never averaged. Majority vote is refused as the default
because disagreement is often information about the pair. `IRRECONCILABLE` is a
permitted terminal state. `NOT_DISTINGUISHABLE` is a first-class answer and is
never scored against the model.

**15. What leakage boundaries are required?**
Grouping by `(reliability_scope, proposition_kind, subject_key)`, with
`source_id` implied by the first, `opportunity_id` where present, and
`time_period` for temporal claims. Every unit sharing the tuple goes to exactly
one split. The leakage the rule prevents is concrete: Wikimedia pageviews for one
article on day *N* and day *N+1* share a source, a resource, a record kind, a
proposition kind, a reliability assessment and a subject.

**16. What split design is required?**
Frozen dataset version → frozen and hashed split manifest → development →
parameters frozen → holdout evaluated **once**. Holdout isolation is
**structural**: development and holdout labels live in separate files, following
Mission 1.26, because a split column relies on every caller remembering a rule.
Mission 1.26's split *sizes* are deliberately not copied.

**17. Is a forward-time holdout required?**
Yes, for any claim of temporal generalisation and for any fitted half-life. It is
**unrunnable today**: 0 of 28 Claims are temporally sensitive.

**18. Which metrics are appropriate?**
Pairwise ordinal agreement · rank correlation within a leakage group ·
monotonicity under controlled perturbation · duplicate robustness ·
source-concentration robustness · per-mechanism ablation loss · coverage and
availability rates · stability under re-run. Each is listed with the failure it
detects, because a metric chosen for being a standard name detects nothing in
particular.

**19. Which metrics are inappropriate because Evidence Score is not a
probability?**
**Brier score, reliability diagrams against outcome frequency, log loss**, AUC
read as discrimination of truth, and accuracy against a thresholded score. The
first four presume a probability or an outcome; the last invents a decision
threshold the framework does not define.

**20. What baseline is used?**
Five, with improvement defined before results are seen. **B-2, the reliability
pass-through, is the one that decides whether any of this is worth doing**:
report the reliability value and ignore every other mechanism. On the current
corpus the full aggregator and B-2 are numerically identical on **19 of 19**
scorable claims. Also B-0 the incumbent, B-1 a constant, B-3 evidence count, B-4
max `q` with no saturation or grouping.

**21. How would temporal half-life eventually be fitted?**
Per claim feature, never universally, from Claims declared temporally sensitive
*with a feature*, the same proposition re-observed at several ages so decay
separates from between-claim variation, reference judgements at more than one
age, and a forward-time holdout. **A feature with insufficient data gets no
half-life** and keeps reporting `MISSING_TEMPORAL_PARAMETER`.

**22. Is current Docker data useful for half-life calibration?**
**No, and not merely insufficient.** Every Docker Claim is `EVERGREEN`, so
freshness is 1.0 by definition and the data carries **zero** information about
decay. `TEMPORAL_CALIBRATION_DATA_MISSING`.

**23. How will EvidenceLevel thresholds be validated or fitted?**
Against reviewer judgements of evidence **maturity**, elicited separately from
support strength — a level and a score answer different questions, and one target
cannot validate both. Only `multi_source_min_groups` above its floor of 2 is
open.

**24. Which current level rules remain structural?**
The floors of 2 for groups and families · levels 4 and 5 requiring an observation
category · levels 4 and 5 requiring established provenance · level not falling
with contradiction. **Nothing was loosened because current data stays at level
1.** Mission 1.36.1 recorded that reliability could not raise the Wikimedia
diagnostic above level 1, and that is the gates working.

**25. How does independence enter calibration?**
As the model's most load-bearing input. It affects group formation, the
saturation input count, levels 2 and 3, and levels 4 and 5 through the provenance
condition. What is calibratable is the **strictness** of the unknown-provenance
rule, not its direction — `independence.py` says so itself. The prerequisite is
verified lineage, which D-12 blocks. **No independence group was created**; all
rows remain `UNKNOWN`.

**26. How are contradictions tested?**
There is **no penalty coefficient to fit** — contradiction enters continuously
through `c`, and `masses.py` states there is no `score -= 20 if contradicted`
anywhere. Calibration would need support-only, contradiction-only,
mixed-asymmetric and genuine-conflict cases. The corpus has **zero** contradicting
Evidence rows, so three of the four masses have only ever taken their `c = 0`
values.

**27. How is missing Evidence treated?**
`UNAVAILABLE` is not a low score. Calibration may not map it to 0 or 50, may not
impute a component, and may not silently drop unavailable units — they are
retained and reported, so a parameter change that buys ordering quality by making
more records non-scorable is visible as such.

**28. How is a calibrated profile versioned?**
`reference-v1@1.0.0` is never mutated. A calibrated profile is a **new versioned
object**, and `profile.py` already refuses `CALIBRATED` without a
`calibration_dataset_ref`. `applies_to` scopes it to where its calibration holds;
claims outside keep failing closed.

**29. What exact provenance must a calibrated profile retain?**
Profile id, version, status, algorithm version, calibration procedure version,
dataset id and version, split manifest hash, fitted parameters **with
uncertainty**, objective, metrics and values, development results, holdout
results, baseline comparisons, creation timestamp, code revision, `applies_to`
scope, stated limitations. A point estimate with no interval is a guess with a
decimal point.

**30. What does the current real-data feasibility audit show?**

| | |
|---|---:|
| Claims / Evidence rows | 28 / 28 |
| **Distinct evidence-count-per-claim** | **[1]** |
| Claims with scorable Evidence | 19 |
| Claims `UNAVAILABLE` | 9 |
| Claims with >1 Evidence row | **0** |
| Claims with any contradiction | **0** |
| Non-zero conflict mass | **0** |
| Established independence | **0** |
| Temporally sensitive | **0** |
| Carrying a `claim_feature` | **0** |
| MARKET_ACTIVITY / DIRECT_VALIDATION | **0** |
| Distinct proposition kinds (scorable) | 2 |
| Distinct source ids (scorable) | 2 |
| Distinct support strengths | **2** (`0.5` ×1, `0.65` ×18) |
| Limiting component | `reliability` ×19 |
| Reference-label tables | **none** |

**31. How many current cases are actually usable for calibration?**
**Zero.** 19 have scorable evidence, and none exercises an aggregation mechanism:
no unit has two Evidence rows, so saturation has never combined groups,
independence collapse has never collapsed anything, `max(members)` has never had
more than one member, and contradiction has never run.

**32. Is source/domain/target variation adequate?**
**No, and the target variation is the worst of it.** Two distinct support
strengths, and both are exactly the two reviewed reliability values. Applying the
leakage rule yields **2 groups among 19 units**, which cannot be split into
development and holdout at all.

**33. Does a reference dataset currently exist?**
No. No labels, no units, no manifest, and none of the six candidate tables
exists in the database.

**34. Is a sample-size requirement justified yet?**
No. **`SAMPLE_REQUIREMENT_NOT_YET_QUANTIFIED`**, and §27 forbids a round number
without a derivation. It depends on the parameter count a candidate moves, the
reviewer disagreement rate, the group count after the leakage rule, coverage per
dimension and holdout size — four of those five unmeasured because no pair has
ever been judged.

**35. What preregistered gate would permit `CALIBRATED` status?**
Fourteen conditions, in the strategy artifact. **Eleven are quantified. Three are
not, and are recorded as blockers rather than filled in:** G-3 the acceptable
inter-reviewer agreement, G-5 coverage adequacy per dimension, G-8 the margin by
which a candidate must beat the reliability pass-through. A gate weak enough for
current data to pass would not be a gate.

**36. Did any parameter change?** No.

**37. Did any profile become `CALIBRATED`?** No. `reference-v1@1.0.0` is still
`UNCALIBRATED`, and `aggregate()` still refuses it without an explicit override.

**38. Were any `ReliabilityAssessment`s changed?** No. Two, unchanged, and no
third. Stack Exchange documentation was not searched again.

**39. Were any model calls made?** **0 calls, 0.00 USD.**

**40. Were any research records acquired?** None. RawRecords, NormalizedRecords,
Signals, Claims, ClaimRevisions and Evidence all unchanged.

**41. Was an Opportunity Score created?** No. `scoring.scores` does not exist as a
table.

**42. Was ranking performed?** No.

**43. Is Problem-Family still PARKED?** Yes, and §9 forbids its labels as
calibration targets: they answer a semantic equivalence question about two
observations, not a support question about a claim and its evidence.

**44. What is D-03 state after Mission 1.37?**

| # | blocker | state |
|---|---|---|
| 1 | reliability definition / authority | RESOLVED |
| 2 | reviewed reliability for scopes in use | PARTIAL |
| 3 | `CALIBRATED` aggregation profile | **OPEN** |
| 4 | temporal half-life | **OPEN** |
| 5 | fitted Evidence-level thresholds | **OPEN** |

**Unchanged by this mission. A strategy is not a calibration.**

**45. What is the exact recommended next mission?**
**Not a labelling mission.** The blocker underneath the missing labels is that
there is nothing with the required shape to label — a reference judgement about a
single-record claim tests reliability pass-through and nothing else.

The precondition is architectural and already permitted: **two Signals must
interpret to the same `proposition_key`**, which is what puts two Evidence rows on
one Claim. The interpretation layer supports it; no current data does it.

So the next mission is the narrowest one that produces **multi-record Claims**,
and it should introduce a **second pilot** from a substantially different domain —
not developer tooling, exercising different Evidence families, sitting in a
published product or category taxonomy (which Mission 1.35 established Docker does
not), with a route to commercial evidence at the right grain. Chosen for
calibration diversity, never for ease of fetching.

---

## §37 — Reproducibility, and a distinction the backlog item needs

The audit ships with a deterministic `--check` from the beginning, and it passes.

**It is an operator gate and not a CI step, and that is a real distinction rather
than an omission.** The four `--check` steps CI already runs render repository
files into other repository files. This artifact **measures a deployment**: CI's
integration job applies migrations to an empty database and seeds it, so the
corpus the audit describes does not exist there. A check step in that job would
compare an empty measurement against a committed full one and be permanently red,
or be loosened until it verified nothing.

**The same constraint applies to the Mission 1.36.1 backlog item.**
`build_reliability_review_packet.py` reads the database too, so "add a `--check`
step" for it is not a mechanical change — it needs this decision made first.
Recorded here rather than expanded into general CI cleanup, which §37 forbids.

---

## §32 — D-08

Not solved, and not touched. One calibration decision does depend on it and is
recorded rather than resolved: **a calibrated score must remain reproducible
against the exact dataset revision that produced it**, which means a stored score
must carry its profile version, dataset version and split manifest hash. Whether
existing scores are recomputed when a profile changes is D-08 proper and belongs
to a separate mission. Nothing here requires it to be answered now, because no
score is stored at all.

---

## Artifacts

| | |
|---|---|
| [evidence-aggregation-calibration-strategy-v1.md](../data/evidence-aggregation-calibration-strategy-v1.md) | the strategy in prose |
| [evidence-aggregation-calibration-strategy-v1.json](../data/evidence-aggregation-calibration-strategy-v1.json) | machine-readable, with the per-element basis |
| [calibration-reference-dataset-schema-v1.json](../data/calibration-reference-dataset-schema-v1.json) | the dataset contract, **empty by design** |
| [calibration-feasibility-audit-v1.json](../data/calibration-feasibility-audit-v1.json) | the measurement, regenerable with `--check` |
| [audit_calibration_feasibility.py](../../infrastructure/scripts/audit_calibration_feasibility.py) | read-only, writes one JSON and no database row |
| [test_calibration_strategy.py](../../packages/evidence-aggregation/python/tests/test_calibration_strategy.py) | 52 tests |

The tests live in `packages/evidence-aggregation` rather than beside the
mission's other artifacts, because that package owns the aggregation contract and
already depends on it. `sros-opportunity` declares only `sros-contracts`, and a
test importing `sros_evidence_aggregation` from there would quietly widen that
boundary. They are `unittest` with no third-party import, matching the sibling
suite so they run in the zero-dependency CI job (ADR-009).
