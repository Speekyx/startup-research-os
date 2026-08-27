# `services/execution`

**Status:** boundary defined, not implemented.

## Responsibility

Turn a scored opportunity into an **actionable plan**: MVP scope, go-to-market
strategy, monetization model, distribution plan, and the risks attached to each.

This is the last stage of the pipeline and the most speculative one. Everything
it produces is `RECOMMENDED` or `PREDICTED` — never `OBSERVED`
(`evidence-confidence-framework-v1.md` §8). The claim type is not a formality
here: it is the difference between "the market shows X" and "we suggest you try X".

## Inputs

- A scored opportunity (all five score families)
- Market context from `market-intelligence`
- Competition Gap from `competition`
- User constraints: budget, timeline, team, skills, risk tolerance

## Outputs

- **MVP plan** — smallest scope that tests the core hypothesis, with an explicit
  statement of which hypothesis it tests
- **Behavioral loop design** (`opportunity-ontology-v1.1.md` §5):
  `trigger → action → value → reward → reason to return`
- **Monetization recommendation** from the §3.8 models, with rationale
- **Distribution plan** from the §3.9 channels, ordered and justified
- **Retention mechanism** recommendation (§3.7)
- **Risk register** (§3.10): technical, data dependency, platform dependency,
  legal, competition, acquisition, monetization, retention
- **Validation plan** — what evidence would move this opportunity toward
  Level 5 (direct validation), and what would falsify it

## Dependencies

- `services/scoring`, `services/market-intelligence`, `services/competition`
- LLM Gateway (ADR-006), `STRONG_MODEL` tier — this is a legitimate LLM-heavy
  context: synthesis and planning are exactly what §1 of
  `llm-reasoning-rules.md` says LLMs are for. Never a provider SDK
- PostgreSQL, `packages/contracts`

## Future API surface

```
POST /internal/mvp-plan          opportunity + constraints -> MVP plan
POST /internal/gtm-strategy      opportunity + market -> go-to-market plan
POST /internal/monetization      opportunity -> monetization recommendation
POST /internal/risks             opportunity -> risk register
POST /internal/validation-plan   opportunity -> next research/validation steps
GET  /internal/plans/{id}        stored plan with its input snapshot
```

## Hard constraints

1. **Everything here is a recommendation.** No output from this context may be
   presented as observed market fact.
2. **Plans are traceable to their inputs.** A stored plan references the score
   snapshot, evidence snapshot and model version that produced it. A plan whose
   inputs have since changed must be identifiable as stale.
3. **A plan states what would falsify it.** `evidence-confidence-framework-v1.md`
   §2 makes Level 5 direct validation the goal; a plan that cannot be falsified
   cannot move an opportunity toward it.
4. **The behavioral loop is a signal, not a guarantee**
   (`opportunity-ontology-v1.1.md` §5). Do not present a designed loop as evidence
   of retention.
5. **Low input confidence propagates.** A plan built on a low Evidence Score is
   labeled as such at the top, not in a footnote.
6. **No fabricated market numbers in a plan.** The most tempting place in the
   entire system to invent a TAM figure is a go-to-market document. It is
   forbidden here exactly as everywhere else.

## Failure modes to design for

| Failure | Required behavior |
|---------|-------------------|
| Evidence Score too low to plan on | Return "insufficient evidence to plan", plus the validation steps that would fix it |
| Constraints make the opportunity infeasible | Say so explicitly; do not produce a plan that ignores the constraint |
| Conflicting monetization signals | Present alternatives with trade-offs, not a single confident answer |
| Inputs changed since plan creation | Mark the plan stale, do not silently serve it |
| Evidence expired under retention while the plan survives | Plan remains readable; expired references render as "evidence expired", never as an error and never silently as "no evidence" (`data-retention-policy-v1.md` §2.4) |
| LLM budget exhausted | Explicit state, no partial plan presented as complete (ADR-006) |
