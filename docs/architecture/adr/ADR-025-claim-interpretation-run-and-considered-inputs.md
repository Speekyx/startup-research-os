# ADR-025 — What an interpretation considered is part of the record

**Status:** Accepted
**Date:** 2026-08-31
**Mission:** Sprint 1 / Mission 1.13.1
**Extends:** [ADR-021](ADR-021-signal-derivation-run-log.md) (where a refused
derivation goes), [ADR-024](ADR-024-claim-precedes-opportunity.md) (a Claim may
precede its Opportunity).
**Related:** [`claim-interpretation-runtime-v1.md`](../../data/claim-interpretation-runtime-v1.md),
[`deterministic-observed-claim-interpreter-v1.md`](../../data/deterministic-observed-claim-interpreter-v1.md),
[`claim-evidence-interpretation-gap-analysis-v1.md`](../../data/claim-evidence-interpretation-gap-analysis-v1.md)
(GAP-5).

---

## Context

Mission 1.13 defined the interpretation boundary and built no interpreter. Its
report named two things a first interpreter would need before it could run, and
both are decisions about what gets **persisted**, which is why they are here
rather than in a document:

1. **A refused interpretation must land somewhere.** `NO_SUPPORTING_SIGNAL`
   returned into a void is the observability gap Mission 1.11.1 §4 made a
   precondition one layer down. ADR-021 answered the same question for signal
   derivation; the answer here has to be its own, because a claim run is not a
   derivation run and putting both in one table would mean a column that is
   always null for half the rows.

2. **GAP-5, deferred deliberately in Mission 1.13**, because a schema designed
   against an imagined writer is a schema fitted to a guess:

   > "Three supporting Signals exist" and "three of forty considered were
   > supporting" are different facts, and an aggregator that cannot tell them
   > apart reads a selection as a census.

Both are hard to reverse. A claim written without a run row cannot be given one
retrospectively; a run written without its considered set cannot recover what it
looked at. Whatever is not recorded on the first pass is permanently absent for
every claim produced before the decision changes — the same argument
`data-principles.md` §11 makes about provenance.

A third decision surfaced during implementation and belongs with them: migration
0016 gave a claim a `proposition_key` and nowhere to keep the facts it hashes.

---

## Decision 1 — one row per interpreter EXECUTION, in the claims' transaction

`research.claim_interpretation_runs` records what one execution considered, what
came out of it, and why the rest did not. Written inside the **same transaction**
as the claims it emitted.

Same shape and same reasons as `nlp.signal_derivation_runs` (ADR-021):

- **Not one row per logical job.** Delivery is at-least-once (ADR-004), so a
  redelivery writes a second run row while writing zero new claims. That is the
  honest record of what happened; the CLAIMS are what is idempotent, and nothing
  here claims exactly-once.
- **Same transaction, so the numbers cannot disagree.** A run row written
  separately could say "7 emitted" beside 6 stored claims.
- **A refusal never becomes a Claim.** A row in a table of claims says a claim
  exists. There is no `lifecycle = REFUSED` and no null-statement placeholder.
- **Operational retention, 90 days.** A Claim is a twelve-month artifact; a
  record of an attempt is not.

### What the run does not assert

The outcome counters are bounded **individually** and their sum is not:

```sql
CHECK (signals_cited    <= signals_considered
   AND signals_excluded <= signals_considered
   AND signals_refused  <= signals_considered)
```

`cited + excluded + refused <= considered` would hold for this interpreter, and
it is a model of how the counters relate rather than arithmetic. Migration 0013
asserted that shape one layer down and migration 0015 had to undo it, because
one candidate group derived a pair and refused another. An interpreter citing a
Signal for one proposition and excluding it from another would falsify the sum
identically, and the counters would be right. Write the invariant you can
defend (`../testing-strategy.md` §27).

---

## Decision 2 — GAP-5 is a child table of the RUN, not of the Claim

`research.claim_interpretation_inputs` holds one row per Signal a run
**considered**: its id, its type, its role, and why.

```text
CITED      a Claim was emitted and an Evidence row cites it; the row names it
EXCLUDED   never attempted -- no template for its type, lineage unreadable
REFUSED    attempted, and the model rejected the resulting draft
```

**`EXCLUDED` and `REFUSED` stay apart.** Never-attempted and
attempted-and-rejected are different facts calling for different fixes, and one
value for both would lose which happened. A coherence CHECK enforces the shape,
written so every branch tests with `IS NULL` / `IS NOT NULL` — never NULL, so it
cannot be the third thing a CHECK silently accepts (migration 0017's lesson).

**Rows are written for `CITED` Signals too.** A table holding only exclusions
could say what was skipped and not what the denominator was, and the denominator
is the finding.

### Why the run and not the claim

Three reasons, and the first is decisive:

1. **A Signal considered and not cited has no Claim to hang off.** A per-claim
   record would keep only the half that needs recording least.
2. **Exclusion is a property of an execution, not of a proposition.** A Signal
   excluded by version 1.0.0 and cited by 1.1.0 is two facts about two runs. A
   per-claim row would have to overwrite one with the other.
3. **It joins.** "Which claims came from Signals this run also excluded" is the
   GAP-5 question, and it is a join rather than a read-alongside — which is why
   this is a child table while `refusals` on the run stays JSONB (the
   distinction migration 0009 drew for provenance).

**Ids, roles and reasons only.** No copy of the Signal: the Signal is one join
away and duplicating its payload would create a second version of it that
nothing keeps current.

---

## Decision 3 — a proposition key is stored with its preimage

`research.claims.proposition_facts` holds the canonical fact object
`proposition_key` is the sha256 of, paired by a `num_nonnulls(...) IN (0, 2)`
CHECK, constrained to a non-empty JSON object.

Migration 0016 stored the hash alone. A hash with no preimage:

- cannot be verified — nobody can check that the key matches what it claims to
  identify;
- cannot be explained — "why are these two the same claim?" has no answer a
  person can read;
- cannot be recomputed — a future interpreter cannot confirm it would produce
  the same key without re-deriving the whole Signal.

The facts are the claim's identity in readable form, and an identity nobody can
inspect is one nobody can dispute. Storing them costs a JSONB column and buys
every one of those.

It is deliberately **not** the statement, the research session or an embedding.
D-12 stays open and nothing here depends on it.

---

## Consequences

**What this makes possible.** An operator can ask, of any execution: what did
the interpreter look at, what did it emit, what did it pass over, and for what
reason. Before migration 0018 the same seven claims could have come from seven
Signals or from four hundred, and nothing recorded which.

**What it costs.** Two tables, one column, and a write per considered Signal.
The considered set grows with executions rather than with claims — bounded by
the 90-day retention and by the job's own 200-Signal ceiling.

**What stays open.** Whether an aggregator should *read* the considered set, and
how a selection ratio would enter a score, is not decided here. D-03 is blocked
and this ADR only makes the fact available.

**What would reverse it.** Nothing cheaply, which is why it is an ADR. A claim
written without a run row cannot be given one afterwards.
