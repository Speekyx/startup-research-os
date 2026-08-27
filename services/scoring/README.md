# `services/scoring`

**Status:** boundary defined, not implemented.
**BLOCKED — hard blocker.** D-03: no evidence aggregation formula exists (audit
A-02, A-03, A-04). This is now recorded normatively in
`scoring-framework-v1.1.md` §13: `services/scoring` must not be implemented until
`docs/domain/evidence-aggregation-framework-v1.md` exists and is authorized.
Implementing it first means someone chooses the constants, they become
load-bearing, and they are unfalsifiable afterwards because nothing records that
they were guessed.

## Responsibility

Compute the **five score families** from evidence, and explain every one of them.

```
Opportunity Score      how attractive, given the research context
Evidence Score         how strong and diverse the supporting evidence is
Execution Score        how feasible under the requested constraints
Research Completeness  how much of the relevant space was examined
Model Confidence       how confident the model is in its interpretation
```

These are **never** collapsed into a single number
(`scoring-framework-v1.1.md` §2). Not in the API, not in a sort key, not in a
badge. This is the single most likely accidental violation in the system.

## Inputs

- Signals and classifications from `nlp`
- Evidence objects with reliability, independence, recency, evidence level
- Market context from `market-intelligence`
- Competition Gap from `competition`
- The active scoring profile and its versioned weight vector

## Outputs

For each opportunity, for each market scope, a score record containing
(`scoring-framework-v1.1.md` §4):

- value
- rationale
- supporting evidence references
- confidence
- timestamp and version

Plus the **component dimension scores**, always retained so ranking is
explainable (§6).

## Dependencies

- PostgreSQL — evidence in, scores out
- `services/nlp`, `services/market-intelligence`, `services/competition`
- `packages/contracts` — dimension registry, profile registry

## Dimensions (`scoring-framework-v1.1.md` §3)

Problem · Desire · Utility · Engagement · Retention · Virality · Market ·
Momentum · Competition Gap · Monetization · Distribution · Feasibility
(+ Learning Value for education profiles)

Profile weights are explicit, versioned, and sum to 100% per profile (§6).
Score families and dimension scores are on **0–100**; the `confidence` field on
each is on **`[0,1]`** (`scoring-framework-v1.1.md` §4.1). `Model Confidence` is
a score family on 0–100, not a confidence field — this name collision is the
single most likely source of a silent numeric bug in the system.
Whether a profile weights every dimension or only a subset is open (audit A-01);
the recommendation is a sparse map validated to sum to 1.0.

## Future API surface

```
POST /internal/score                        opportunity + context -> five families
GET  /internal/scores/{opportunity_id}      all scopes
GET  /internal/profiles                     available scoring profiles + versions
GET  /internal/profiles/{id}/weights        the versioned weight vector
POST /internal/evidence-sufficiency         evidence set -> sufficiency report
GET  /internal/explain/{score_id}           full derivation chain
```

`/internal/explain` is not a nice-to-have. Explainability is a manifest-level
engineering principle, and an unexplainable score is not shippable.

## Hard constraints

1. **Weak evidence must not create false precision** (§7). Low Evidence Score
   must visibly constrain how the Opportunity Score is presented.
2. **No output beyond justified precision** (§10). `82`, never `82.37`.
   Confidence renders as `82%`, never `82.37%`.
3. **Per-market scores carry their own evidence and confidence** (§9). A country
   score computed from global evidence is a fabrication.
4. **Full version traceability** (§11): framework version, profile version, model
   version, evidence snapshot time.
5. **Competition is not a penalty** (§8). Competitors can indicate validated
   demand. The scored quantity is the Competition Gap.
6. **Contradictory evidence is preserved, not dropped because it lowers a score**
   (`evidence-confidence-framework-v1.md` §11).

## Failure modes to design for

| Failure | Required behavior |
|---------|-------------------|
| Evidence below threshold | Return "insufficient evidence" with a low Evidence Score. Do not emit an Opportunity Score that looks authoritative |
| Single-source evidence | Cap the achievable evidence level at 1 (`evidence-confidence-framework-v1.md` §2) |
| All evidence is stale | Apply decay (§5), report reduced confidence explicitly |
| Contradictory evidence | Score with a contradiction flag and reduced Model Confidence |
| Unknown scoring profile | Reject. Never silently fall back to a default profile — a wrong profile silently produces a wrong ranking |
| Profile weights do not sum to 100% | Reject at load time, not at score time |
