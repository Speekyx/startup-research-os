# Mission 1.1 — Completion Report

**Mission:** Evidence Aggregation Framework V1 — conservative, explainable, calibratable evidence mathematics
**Sprint:** 1
**Date:** 2026-08-29
**Branch:** `sprint-1/mission-1.1`
**Resolves:** **D-03 at the framework level.** Its parameters remain uncalibrated
**Introduces:** [ADR-014](adr/ADR-014-evidence-aggregation-reference-implementation.md), four domain documents, `packages/evidence-aggregation/`, six closed enums
**Opens:** **A-13** — aggregation is claim-centric and no Claim entity exists

---

## 1. Framework overview

Evidence Aggregation V1 answers one question: given several Evidence records
bearing on one Claim, how strongly does the accumulated evidence support it, how
strongly does it contradict it, and how much do we not know?

```text
evidence records
  -> q_i = min(components)                  the weakest dimension, per record
  -> collapse by provenance, max() wins     duplicates cannot multiply
  -> saturate across groups, per direction  support and contradiction separately
  -> four masses summing to 1               conflict stays visible
  -> EvidenceScore, EvidenceLevel           a score, and a maturity, kept apart
```

The design was shaped by refusing three things the mission brief forbids and the
system would otherwise have drifted into: a per-platform reliability
coefficient, a universal half-life, and a fixed contradiction penalty. Each
would have made the engine produce numbers today at the cost of resting every
future score on a value nobody could later falsify.

## 2. Mathematical definitions

```text
q_i = min(relevance, directness, reliability, extraction_confidence, freshness)

group_strength = max(q_i within one independence group)

S = 1 - PRODUCT(1 - g_i)          computed separately per direction
s = support_strength,  c = contradiction_strength

supported_mass    = s(1-c)     contradicted_mass = c(1-s)
conflict_mass     = s·c        uncertainty_mass  = (1-s)(1-c)      sum = 1

EvidenceScore = 100 · supported_mass                 0 <= score <= 100
freshness(age, H) = 2^(-age/H)                       TEMPORALLY_SENSITIVE only
```

None of these is a probability. `q`, `S` and the masses are bounded contribution
values describing the state of the evidence, which is a different kind of thing
from the state of the world.

## 3. Evidence item contribution

`min`, not a weighted average, because the two cases the system must not get
wrong are the two an average handles worst: a highly relevant record from a
source that cannot be relied on, and a highly reliable source discussing
something else. An average scores both middling and lets strength pay for
weakness.

The cost is stated rather than hidden: `min` discards information, so
`(0.9,0.9,0.9,0.9,0.3)` and `(0.3,0.3,0.3,0.3,0.3)` score identically. V1
accepts that because being wrong conservatively is recoverable and being wrong
permissively produces confident nonsense. Every component survives into the
explanation so a calibrated profile can revisit the operator with data.

**A missing component makes the record NON_SCORABLE** — not 0.5, not 1.0, and
not 0.0. A zero would enter the arithmetic as a measured weakness; this is an
absence of measurement.

## 4. Independence model

Independence is provenance, not source count. Records sharing an origin form one
`EvidenceIndependenceGroup` and the strongest member counts; every member is
preserved for the explanation and only the arithmetic collapses.

Two shapes are refused outright rather than handled conservatively:
`KNOWN_DEPENDENT` with no group id asserts a dependency on nothing, and
`KNOWN_INDEPENDENT` with a group id claims independence and membership at once.
Neither has a safe reading.

## 5. Duplicate handling

`group_strength = max(members)`. Not the sum — ten duplicates would overwhelm one
original. Not the mean — adding weak copies of a strong observation would
*weaken* it, and a duplicate is not counter-evidence.

Verified: ten records from one origin produce **exactly** the same score as the
single strongest one (80.00 in both cases), and a weak duplicate cannot drag a
strong original down.

## 6. Unknown-independence behaviour

`UNKNOWN` is a distinct third state, never silently promoted. All
unknown-provenance records for one claim and one direction form **at most one
group**; the strongest counts and the rest raise observed volume only.

The reasoning is worth recording, because the opposite reading is tempting:
unknown does not mean probably independent. The records most likely to share an
origin are exactly the ones that arrive together in bulk, so unknown correlates
*with* dependence.

**A deliberate asymmetry.** The unknown bucket contributes one group's worth of
*strength*, because it does represent at least one real observation. It
contributes **nothing** to the `EvidenceLevel` independence counts, because a
level asserts *repetition* and that requires knowing two observations are
distinct. One established record plus ten unlabelled ones is Level 1, not
Level 2.

## 7. Recency model

Temporality is a property of the claim, not the source. `EVERGREEN` claims have
`freshness = 1.0` and need no timestamp. `TEMPORALLY_SENSITIVE` claims decay by
half-life.

**No universal half-life was invented, and `REFERENCE_PROFILE_V1` ships with
none at all.** A temporally sensitive claim with no authorised half-life yields
`MISSING_TEMPORAL_PARAMETER`, the records become non-scorable, and the result is
`UNAVAILABLE` with no score. A guard asserts the empty table stays empty.

That is the mission's most consequential refusal. A placeholder would have
worked, would have been recorded nowhere as a guess, and would have propagated
into every downstream number.

## 8. Support aggregation

`S = 1 - Π(1 - g_i)`, over independent groups. Bounded, monotonic, with
diminishing marginal return, and it lets one strong observation carry its own
weight where a mean would dilute it.

Numerically it uses `-expm1(Σ log1p(-g))`, which stays accurate when every `g`
is small and the naive form cancels. Strengths are sorted before summation:
floating-point addition is not associative, so reproducibility under reordering
is engineered rather than assumed.

## 9. Contradiction model

Support and contradiction accumulate separately and are then decomposed. The
decomposition exists because `s - c` cannot distinguish the two states a research
system most needs to tell apart: **no evidence** and **overwhelming evidence
both ways** both net to zero. The first needs more research; the second needs a
human.

**There is no flat penalty.** Contradiction enters continuously through `c`, so a
weak contradiction moves the result a little and a strong one a lot, and
independent contradictions accumulate with the same saturation as support. That
resolves the contradiction-penalty part of D-03 without anyone choosing a magic
number.

## 10. Evidence Score

`EvidenceScore = 100 · supported_mass`, on the canonical 0–100 scale.

It is a **score**. It is not a confidence, not a probability, and not a
likelihood of truth. It is never published without `support_strength`,
`contradiction_strength`, `conflict_mass` and `uncertainty_mass` beside it — a
score of 4 means *contested* in one evidence set and *unsupported* in another,
and only the diagnostics tell them apart.

## 11. EvidenceLevel relationship

Not derived from the score, and no threshold such as "80 → level 4" exists. The
score says how strongly evidence supports the claim; the level says what kind of
evidence exists at all.

- **Independence gates 2 and 3.** Duplicates and unlabelled records cannot
  create a Repeated Signal.
- **Category gates 4 and 5.** No accumulation of `STATED_OPINION` becomes market
  activity. Both also require established provenance.
- **The ladder is not strictly nested at the top,** deliberately: one recorded
  preorder reaches Level 5 without three supporting groups, because the kind of
  evidence dominates its quantity.

Verified both ways: twenty strong opinions across five families score 100 and
reach Level 3; one weak direct-validation record scores 20 and reaches Level 5.

## 12. Aggregation profiles

`EvidenceAggregationProfile` carries `profile_id`, `version`, `status`,
`algorithm_version`, `applies_to`, `default_temporality`, `half_life_days`,
`required_item_fields`, `level_thresholds`, `calibration_dataset_ref`,
`calibrated_at` and `notes`.

Two versions because two things move independently: `algorithm_version` for the
equations, profile `version` for the parameters. A single version would hide
which one moved.

`DRAFT` and `RETIRED` refuse to run. `UNCALIBRATED` runs only with an explicit
`allow_uncalibrated=True` and warns in the result. `CALIBRATED` cannot be
constructed without a `calibration_dataset_ref` — a calibration nobody can re-run
is a claim, not a calibration.

## 13. Calibration requirements

[`evidence-aggregation-calibration-plan-v1.md`](../domain/evidence-aggregation-calibration-plan-v1.md)
separates structural choices (derived from meaning) from six genuinely empirical
parameters, and specifies temporal holdout, cross-market validation, calibration
curves, rank correlation, ablation, and duplicate/source-concentration
robustness. §6 makes bias evaluation mandatory — language, geography, platform
demographics, survivorship, moderation, popularity, syndication — and §7 lists
nine conditions for promoting a profile to `CALIBRATED`.

**Nothing in it has been executed.** It is written in the future tense
throughout, deliberately.

## 14. Sensitivity analysis

Thirteen synthetic scenarios, generated from the implementation and checked in
CI so the report cannot describe behaviour the code does not have. Everything is
synthetic: no platform was contacted and every provenance relationship is stated
by the scenario.

Behaviour matching the specification: duplicates collapse exactly; unknown
provenance yields one group from ten records; conflict stays visible
(`conflict_mass` 0.92 with a score of 4); one market record reaches Level 4 where
twenty opinions cannot; missing inputs and missing half-lives fail closed.

**Two findings recorded rather than tuned away:**

**S-1 — the score saturates towards 100.** Twenty independent strong groups
present as `100`, which reads as certainty. The operator behaves as defined; the
problem is how the output reads. No damping constant was added, because choosing
its value in a synthetic harness with no data would be the exact failure D-03
exists to prevent, committed while resolving it. First-priority calibration
target.

**S-2 — group count dominates group quality.** Twelve weak independent groups
outscore one strong group. Defensible in itself, but it places the model's whole
weight on the independence judgement: twelve records wrongly labelled independent
produce the same number as twelve real ones. The conservative unknown rule
mitigates unlabelled records and cannot mitigate mislabelled ones — a data
quality problem for `nlp` (D-12).

## 15. Reference implementation

`packages/evidence-aggregation/` — a package, not a service. Standard library
plus `sros_contracts`, so it runs in the zero-dependency CI job. It reads no
database, opens no network connection, and is wired into no request path.

Ten modules mirroring the specification section by section, plus the sensitivity
harness. `services/scoring` remains a boundary README with no implementation, and
a guard asserts it.

## 16. Schema gap analysis

[`evidence-schema-gap-analysis-v1.md`](../domain/evidence-schema-gap-analysis-v1.md)
audits `scoring.evidence` and **writes no migration**.

| Classification | Count |
|---|---|
| Already supported | 6 |
| Additive | 5 (`direction`, `relevance`, `directness`, `observation_category`, `independence_group_id`) |
| **Incompatible** | 2 |
| Deferred | 3 |

**I-1 — `independence DOUBLE PRECISION` cannot express independence.** The column
stores a scalar; the framework needs a relation. "Record B is 0.3 independent"
does not say what it depends *on*, so grouping has nothing to group by. Worse, a
scalar invites `q × independence`, which is discounting instead of grouping and
lets ten discounted duplicates still outweigh one original.

**I-2 — there is no Claim.** Aggregation is claim-centric; there is no `claim`
table, no `claim_id`, and no Claim entity in the ontology. `opportunity_id` is
not a substitute: one opportunity carries many claims, some contradicted while
others are well supported, and aggregating at the opportunity level would average
away exactly what the four masses preserve.

Both are cheap to fix today — the tables are empty and nothing writes to them —
and neither was changed, because both require authorisation.

## 17. Tests

| Suite | Count | Covers |
|---|---|---|
| `packages/evidence-aggregation/python/tests` | 73 | the twelve invariants, the level ladder, reproducibility, and the guards |
| Zero-dependency suites overall | 304 across 5 packages | up from 231 |
| Every other suite | unchanged | 6 packages, all green |

The twelve required invariants are all asserted, as deterministic parameterised
sweeps over the known boundaries rather than via a property-testing dependency.

Two tests earn their keep beyond box-ticking. `test_no_registered_source_appears_in_the_package`
fails the day somebody writes `reddit = 0.75`. And
`test_evidence_ordering_does_not_change_the_result` **caught a real defect**: the
masses were order-independent from the start, but the serialised explanation was
not, so two runs over one snapshot produced different bytes.

## 18. CI and quality gates

New zero-dependency job **`evidence-aggregation`**, running
`validate_evidence_aggregation.py` (7 checks). Added to existing jobs: mypy over
the new package, and `sensitivity --check` so the report cannot drift.

`quality-gates.md` §1 records all nine new gates.

### The D-03 guard was rewritten, not deleted

This was the subtlest part of the mission. The old guard banned all aggregation
vocabulary, which was right while nothing was defined and wrong the moment V1
was authorised. The tempting correction — delete it — would have given back
everything it protected.

| Tier | Rule |
|---|---|
| **Rejected designs** — `contradiction_penalty`, `decay_weight`, `aggregated_evidence_score`, `independence_threshold_result`, `evidence_aggregate` | Forbidden **everywhere, permanently**. Each names a design V1 considered and rejected, with the reason recorded in `cases.json` |
| **Authorised V1 vocabulary** | Allowed in the reference package and the contracts. Forbidden in migrations and under `services/` |
| **Universal half-life constants** | Forbidden everywhere |
| **Registered source ids** | Forbidden in the aggregation package |

The rejected names are now blocked *by a decision* rather than *pending one*,
which is a stronger guarantee than before.

## 19. New issues

**A-13 — the Claim entity (new, open).** Aggregation is defined around a Claim
that Ontology V2 §7 defines as a taxonomy and never as an entity. Resolving it
needs an ontology version and an ADR; it is not an implementer's decision.

**S-1 and S-2** (§14) — recorded as calibration targets, not defects to fix by
choosing constants.

**One defect found and fixed during the mission.** Ruff's `F841` surfaced a
variable computed and never used in `levels.py`: the independence filter for the
level ladder was written and then not applied, so the unknown-provenance bucket
was silently counting towards Repeated Signal. Fixed to the stricter intended
behaviour, with a test for the mixed known-plus-unknown case that had no coverage.

**ADR numbering.** The production-deployment placeholder moves from ADR-014 to
ADR-015, by the rule already recorded in the repository. It has now moved three
times; if it moves again the answer is to stop reserving the number.

## 20. Remaining blockers

| Blocker | Status |
|---|---|
| **D-03** | **Framework RESOLVED. Parameters NOT calibrated.** `services/scoring` stays unavailable for production research |
| **A-13** | **New.** No Claim entity. Blocks any persisted aggregation |
| **D-12** | Open. Embeddings and re-embedding. Independence detection ultimately depends on it |
| **D-08** | Open. Score recomputation policy. The framework records what a resolution would need |
| **A-12** | Open. Non-geographic scoping. Untouched |
| **A-01** | Open. Scoring-profile weight vector shape |
| **D-11** | Open. Observability stack |
| Jurisdiction / GDPR | Requires human or legal input |
| Source review | Thirteen candidates, zero collector-eligible. Review work, not a decision |

## 21. D-03 resolution status

Against the fifteen criteria in §40 of the brief:

| # | Criterion | Status |
|---|---|---|
| 1 | Contribution semantics explicit | ✅ framework §5 |
| 2 | Independence handling explicit | ✅ §7 |
| 3 | Duplicate handling explicit | ✅ §7 |
| 4 | Unknown independence explicit | ✅ §7 |
| 5 | Recency function explicit | ✅ §9 |
| 6 | Missing temporal parameters fail closed | ✅ §9, tested |
| 7 | Support aggregation explicit | ✅ §8 |
| 8 | Contradiction aggregation explicit | ✅ §8 |
| 9 | Evidence Score mathematics explicit | ✅ §8 |
| 10 | Evidence Level relationship explicit | ✅ §10 |
| 11 | Parameter/version ownership explicit | ✅ §12 |
| 12 | Calibration requirements explicit | ✅ calibration plan |
| 13 | Reference implementation reproduces the spec | ✅ 73 tests |
| 14 | Synthetic sensitivity tests pass | ✅ 13 scenarios |
| 15 | No per-source arbitrary reliability weights | ✅ guarded twice |

**D-03 is RESOLVED at the framework level.** All fifteen hold.

## 22. Production-scoring readiness

**Not ready, and nothing here made it readier.**

```text
Framework Defined     ✅  Mission 1.1
Profile Calibrated    ❌  no labelled dataset exists
Claim entity          ❌  A-13
services/scoring      ❌  correctly unimplemented
```

Three independent things must happen first: A-13 resolved so aggregation has a
persisted unit; the calibration plan executed so a `CALIBRATED` profile exists;
and `services/scoring` then implemented against both.

## 23. Mission 1.2 readiness

Safe to begin. Nothing was left half-applied: no migration was written, no
production surface changed, no external data collected, and every gate is green.

The three open questions a next mission would trip over are recorded rather than
latent — A-13, the uncalibrated parameters, and the two sensitivity findings.

---

## Explicit answers

| Question | Answer |
|---|---|
| Is the Evidence Aggregation formula defined? | **Yes.** Framework §5–§8, with a reference implementation and 73 tests |
| Does duplicate evidence increase the score? | **No.** Ten records from one origin give exactly the score of the strongest one |
| Is unknown independence treated conservatively? | **Yes.** One group per claim and direction for strength; excluded entirely from the level counts |
| Is recency mathematically defined? | **Yes.** `2^(-age/H)`, per claim, `freshness = 1.0` for evergreen |
| Was a universal half-life invented? | **No.** `REFERENCE_PROFILE_V1` ships none. A missing half-life yields `MISSING_TEMPORAL_PARAMETER` and no score. Guarded |
| Are contradictions preserved separately? | **Yes.** Aggregated separately, decomposed into four masses. No flat penalty |
| Is Evidence Score distinguishable from probability? | **Yes**, and stated everywhere it appears. `82` does not mean 82% likely true |
| Are source-specific reliability weights absent? | **Yes.** No registered source id appears in the package; asserted by a test and a CI guard |
| Is the framework reproducible? | **Yes.** Same snapshot and profile give byte-identical canonical output, with a SHA-256 snapshot digest |
| Is the framework calibrated? | **No.** No parameter was fitted to anything, and no labelled dataset exists |
| Can uncalibrated profiles run in production? | **No.** `aggregate()` refuses one unless the caller passes `allow_uncalibrated=True`, and the result warns |
| Is D-03 resolved at framework level? | **Yes.** All fifteen criteria in §40 hold |
| Is `services/scoring` still blocked from production? | **Yes.** A boundary README with no implementation, asserted in CI |
| Is D-12 still open? | **Yes.** Untouched. No NLP, no embeddings, no clustering |
| Was any external source data collected? | **No.** Every scenario is synthetic. `acquisition.raw_records` is empty, asserted in CI |
| Is Mission 1.2 safe to begin? | **Yes**, with A-13 and the uncalibrated parameters carried forward as known state |

---

## Validation

Every command below was run and passed.

| Check | Result |
|---|---|
| `generate.py --check` | 3 generated artefacts current, contract 1.1.0 |
| `run_python_tests.py` (zero-dep) | **304 tests across 5 packages** |
| `run_pytest_suites.py` | all 6 packages pass |
| `validate_schema.py` | 8 invariant groups, 26 tables |
| `validate_source_registry.py` | 13 sources, 0 warnings — unchanged |
| `validate_evidence_aggregation.py` | 7 checks, 0 warnings |
| `assert_registry_grants_nothing.py` | 13 registered, 0 eligible, 0 enabled, **0 raw records** |
| `sensitivity --check` | report matches the implementation |
| `migrate.py --apply` | 0 applied — schema untouched |
| `ruff check` / `format --check` | clean, 200 files |
| `mypy` (7 packages) | no issues in 81 source files |
| `tsc` contracts + web, `eslint`, `next build` | clean |
| TS conformance + web API client | 19 + 18 tests |

## Mission boundary

Stopped here, as §50 requires. **Mission 1.2 was not begun.** No production
scoring was implemented, no Opportunity Score exists, no collector was written,
no NLP or embeddings were executed, and no external data was collected.

The honest one-line summary: the mathematics of evidence aggregation is now
defined, executable and tested, and it is not calibrated — which is why nothing
in production may use it yet.
