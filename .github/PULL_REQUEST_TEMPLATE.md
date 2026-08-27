## What and why

<!-- What changes, and why. The diff already shows what; explain why. -->

## Specification reference

<!-- Which authoritative document and section governs this change?
     If none applies, say so explicitly. -->

Governed by:

## Assumptions made

<!-- docs/CLAUDE.md §Before implementation step 4: state ambiguities rather than
     resolving them silently. If you guessed at something, it goes here. -->

## Checklist

### Definition of done (`docs/CLAUDE.md`)

- [ ] Behavior matches the specification (named above)
- [ ] Tests cover the important behavior, including at least one failure mode
- [ ] Failure modes considered: timeout, empty result, malformed source, rate limit, partial data
- [ ] Observability adequate — the output can be explained from logs alone
- [ ] Documentation and contracts current
- [ ] `lint`, `typecheck`, `test` pass locally

### Specification compliance (only what applies)

- [ ] No secret in the diff, in a fixture, or in history
- [ ] No fabricated source, metric, price, market size or competitor fact
- [ ] Provenance preserved through every transformation
- [ ] Claim types (`OBSERVED` / `INFERRED` / `PREDICTED` / `RECOMMENDED` / `HYPOTHESIS`) not conflated
- [ ] Version stamps attached to every derived value
- [ ] Contradictory evidence preserved, not discarded
- [ ] No new domain enum declared outside `packages/contracts`
- [ ] No cross-context import that bypasses a declared contract
- [ ] External content treated as data, never as instructions
- [ ] The cheapest reliable method used (no LLM where a rule or embedding suffices)

### If this changes architecture

- [ ] ADR written or updated (an accepted ADR is superseded, never edited)
- [ ] Diagrams updated in this PR
- [ ] `service-boundaries.md` updated

## Risks left open

<!-- What could still go wrong. "None" is rarely true. -->
