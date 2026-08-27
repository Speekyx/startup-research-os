# `services/market-intelligence`

**Status:** boundary defined, not implemented.

## Responsibility

Answer questions about the **market context** an opportunity sits in: how large,
how fast-growing, where, in what language, under which constraints.

It analyzes markets. It does not judge opportunities — that is `scoring`.

## Inputs

- Signals and classifications from `nlp`
- Trend and search data from `acquisition`
- A `MarketScope` (global / region / country / segment — audit A-05)

## Outputs

Per `opportunity-ontology-v1.1.md` §4, each with evidence and confidence:

- market size estimate (with method and assumptions, never a bare number)
- interest level and growth
- purchasing power indicators
- local alternatives
- language and locale factors
- payment method availability
- viable distribution channels
- cultural and regulatory factors
- **momentum** — direction and rate of change, distinct from absolute size

## Dependencies

- PostgreSQL, Qdrant
- `services/nlp`
- `packages/contracts`

## Future API surface

```
POST /internal/market-context      opportunity + scope -> market intelligence
GET  /internal/markets/{scope}     cached market profile
POST /internal/momentum            signal series -> momentum estimate
POST /internal/geo-breakdown       opportunity -> per-country divergence
```

## Hard constraints

1. **A global score must not erase country-level differences**
   (`opportunity-ontology-v1.1.md` §4). Geographic aggregation is lossy and must
   report what it lost.
2. **Every market size is a derivation, not a fact.** It carries its method, its
   inputs, and its assumptions. A market size with no method is a fabrication
   (`evidence-confidence-framework-v1.md` §9).
3. **English data is not the global market** (`data-principles.md` §7).
   Language coverage is tracked and reported as a coverage limitation.
4. **Event-time over ingestion-time** for market analysis
   (`data-principles.md` §9). Trend analysis on ingestion timestamps produces
   artifacts that look like real market movements.
5. **Popularity is not willingness to pay** (`llm-reasoning-rules.md` §4).
   Engagement metrics and monetization potential are separate outputs.

## Failure modes to design for

| Failure | Required behavior |
|---------|-------------------|
| No data for a requested country | Return explicit "no coverage", never extrapolate from a neighbor |
| Sparse time series | Report momentum with wide uncertainty, or abstain |
| Seasonal signal read as growth | Requires a minimum observation window before momentum is emitted |
| Conflicting size estimates | Preserve both with their methods (`data-principles.md` §10) |
| Single-language coverage | Emit the estimate with an explicit language-coverage limitation |
