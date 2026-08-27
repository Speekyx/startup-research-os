# `services/competition`

**Status:** boundary defined, not implemented.

## Responsibility

Map the competitive landscape of an opportunity and compute the
**Competition Gap** (`scoring-framework-v1.1.md` §8).

The framing is deliberate and inverted from the usual one: competition is **not
inherently negative**. Existing competitors are frequently the strongest
available evidence that demand is real. What matters is the gap.

## Inputs

- Opportunity candidates from `nlp`
- Product launches, app store data, public product pages from `acquisition`
- Market context from `market-intelligence`

## Outputs

- **Competitor set** — identified products, each with provenance
- **Positioning map** — how competitors cover the opportunity space
- **Competition Gap** decomposed into the §8 components:
  unmet needs · weak UX · underserved segments · poor localization ·
  pricing gaps · distribution gaps · missing capabilities ·
  emerging technology shifts
- **Saturation signal** — distinct from the gap; a crowded market can still have
  a large gap
- **Demand validation signal** — competitors as Level 4 market evidence
  (`evidence-confidence-framework-v1.md` §2)

## Dependencies

- PostgreSQL, Qdrant (semantic competitor matching)
- `services/nlp`, `services/market-intelligence`
- `packages/contracts`

## Future API surface

```
POST /internal/competitors            opportunity -> competitor set + provenance
POST /internal/competition-gap        opportunity + competitors -> gap decomposition
GET  /internal/competitors/{id}       competitor record with sources
POST /internal/positioning            opportunity -> positioning map
```

## Hard constraints

1. **No invented competitor facts.** Pricing, user counts, funding, feature sets
   are collected and cited, or they are not stated
   (`evidence-confidence-framework-v1.md` §9). This is the single highest
   hallucination-risk surface in the system: an LLM asked about competitors will
   confidently produce plausible pricing tiers that do not exist.
2. **Every competitor attribute carries its source and observation time.**
   Competitor data ages fast; a two-year-old pricing page is not current pricing.
3. **Absence of a competitor is not evidence of absence.** "No competitors found"
   reports search coverage, not an empty market.
4. **Competition is scored per market scope.** A category saturated in the US may
   be empty in Japan (`scoring-framework-v1.1.md` §9).

## Failure modes to design for

| Failure | Required behavior |
|---------|-------------------|
| No competitors found | Report as low research coverage, not as a green field |
| Competitor identity ambiguous | Keep as a candidate with low confidence, do not merge records |
| Stale competitor data | Apply recency decay, flag the age explicitly |
| Adjacent-but-not-competing product | Classify as adjacent, do not inflate the competitor count |
| Pricing page not accessible | Record "unknown", never estimate |
