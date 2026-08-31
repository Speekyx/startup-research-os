# Claim Interpretation Runtime V1

**Authoritative.** Mission 1.13.1. How interpretation runs, what it records, and
where a REFUSED interpretation goes.

Implementation: `services/nlp/python/sros_nlp/claim_job.py`,
`claim_repositories.py`, `services/workers/python/sros_workers/claim_tasks.py`.
The interpreter itself: `deterministic-observed-claim-interpreter-v1.md`.

---

## 1. The stage

```
ACQUISITION → NORMALIZATION → SIGNAL_DERIVATION → CLAIM_INTERPRETATION
```

`CLAIM_INTERPRETATION` is a `Capability` in its own right, separated from
`SIGNAL_DERIVATION` because a Signal states a relation between its inputs and a
Claim asserts a proposition about the world, and separated from `NLP_EXTRACTION`
for the reason `SIGNAL_DERIVATION` was: D-12 is about embedding versioning,
which a format string over structured facts does not use.

`claim_interpretation_block` derives the gate from **five** conditions: a source
eligible, a collector, a normalizer, some extractor, and some interpreter.
`implemented_interpreters` defaults to empty, so a composition root that forgets
the wire gets a blocked stage rather than a permission. When derivation is
blocked, the interpretation block says so **in derivation's words** rather than
inventing a second explanation for one cause.

`PLANNER_VERSION` moved to `1.4.0`. The graph changed, and a plan read back
years later must be interpretable against the planner that produced it.

## 2. The task

`claim.interpret`, routing to the **acquisition** queue.

Not `nlp`. Rendering a format string over a Signal already read is bounded and
CPU-cheap, and no model is involved or permitted — so the `nlp` queue, sized for
LLM-backed budget-consuming work, would be the wrong home twice over. **No
parallel AI worker subsystem was created** (§45).

Every decision lives in `sros_nlp.claim_job`, which runs without a broker. A job
whose logic sits inside a task decorator can only be tested by starting a
worker, and a test that needs a worker is a test that gets skipped.

The workspace, session and correlation id come from the task **headers** and are
refused if absent (ADR-005). The context is rebuilt at execution; nothing
trusted travels through the broker.

## 3. What an interpreter is

Two questions, and nothing else:

```
supports(signal_type_id)   is there a template for this kind of Signal
interpret(signal, request) what proposition -- or what refusal -- comes out
```

**The interpreter computes; `sros_claim_model` checks.** The same division
`signal-derivation-runtime-v1.md` §3 draws one layer down. A template reads a
`SignalView` and renders a sentence and a fact set; `build_claim` decides
whether the result may be stored. `packages/claim-model` contains no template,
asserted over the AST.

`select_interpreter` returns the named interpreter or nothing. **There is no
default**: an interpreter decides what a proposition says, and a job that could
pick one could pick the wrong one.

## 4. Selection is bounded and explicit

At most **200 Signals** per job — our own operational bound, not an external
limit, configurable downwards only. A caller may narrow by signal id, by signal
type or to one research session.

By default the read is filtered to the types the interpreter can phrase. Reading
types nothing has a template for would inflate `signals_considered` with Signals
that were never candidates, and that number is the denominator GAP-5 exists to
keep honest.

**No sweep, no semantic search, no embedding** (§23). Hitting the bound sets
`truncated_by` and keeps what was interpreted; a silent truncation reads as
"covered everything".

## 5. Reading: Signals, plus attribution

`read_signal_views` returns each Signal with its `signal_inputs` and the
**payloads of the contributing normalized records**.

The interpreter consumes **Signals**: what is asserted comes from the Signal's
scope, window, magnitude and direction. It reads normalized records for one
thing only — the attribution facts the Signal's scope does not carry (published
resource, the source's own geography name, term and language schemes) — because
attribution is what separates OBSERVED from INFERRED and an interpreter that
guessed it would be asserting.

**It never reads `acquisition.raw_records`.** Lineage remains available through
Signal → normalized → raw for anyone who needs it; the interpreter does not.

`registry.sources` is joined for the canonical display name. The registry is
global and SELECT-only for the runtime role, so this is a read of reference data.

## 6. Writing: one transaction

Claim, revision and evidence are written **together**, in the caller's tenant
transaction.

Not a preference. `research.require_evidence_for_generated_claim` is a
`DEFERRABLE INITIALLY DEFERRED` constraint trigger that fires at COMMIT, so
evidence arriving in a second transaction is too late by construction. The run
record joins them, so its counts can never disagree with what was stored.

Three outcomes per claim:

| Outcome | Meaning |
|---------|---------|
| `NEW` | First time this proposition was stored |
| `UNCHANGED` | Stored, and its statement is byte-identical. Nothing is written |
| `REVISED` | Stored with a **different** statement. A revision is appended and the pointer moves |

`REVISED` is where this differs from `persist_signals`, deliberately. A Signal
whose fingerprint is stored with different content is a `CONFLICT` — the
extractor is not deterministic, and the stored row stands. A claim is not that:
the proposition key is over the facts and **not over the magnitude**, so a source
revising its figure is the same proposition worded differently, and appending a
revision is exactly the mechanism for it.

Revision 1 is never modified. An aggregation that evaluated revision N must
still be able to read revision N.

## 7. The run log

`research.claim_interpretation_runs`, one row per **execution**, written in the
same transaction as the claims it emitted (migration 0018, ADR-025).

Mission 1.13 made this a precondition for 1.13.1 and did not build it, because
there was no interpreter to write one. It records: interpreter id, version and
kind; signals considered, cited, excluded and refused; claims new and unchanged;
revisions created; evidence new and unchanged; the refusal list; `truncated_by`;
correlation, session, workspace and both timestamps.

**A refusal never becomes a Claim.** A row in a table of claims says a claim
exists — the same argument ADR-021 makes for `nlp.signals`.

Retention is 90 days, deliberately shorter than a Claim's twelve months: a
record of an attempt is not an artifact.

### 7.1 The arithmetic the run does NOT assert

```sql
CHECK (signals_cited     <= signals_considered
   AND signals_excluded  <= signals_considered
   AND signals_refused   <= signals_considered)
```

and **not** `cited + excluded + refused <= considered`.

That tighter sum would be true of this interpreter, and it is a *model of how the
counters relate* rather than arithmetic. Migration 0013 asserted exactly that
shape one layer down and migration 0015 had to undo it, because the third
extractor derived one pair and refused another from a single group. An
interpreter that cited a Signal for one proposition and excluded it from another
would falsify the sum the same way, and the counters would be right. Write the
invariant you can defend (`../architecture/testing-strategy.md` §27).

## 8. GAP-5: what was considered and not cited

`research.claim_interpretation_inputs`, one row per **(run, Signal considered)**.

> "Three supporting Signals exist" and "three of forty considered were
> supporting" are different facts, and an aggregator that cannot tell them apart
> reads a selection as a census.

| Column | Meaning |
|--------|---------|
| `signal_id`, `signal_type_id` | Which Signal. Ids and types, never a copy of the Signal |
| `role` | `CITED` / `EXCLUDED` / `REFUSED` |
| `claim_id` | The Claim, for `CITED` only |
| `reason_code` | A `ClaimEvidenceRefusalReason`, required for the other two |
| `detail` | The sentence naming what disagreed |

**`EXCLUDED` and `REFUSED` are kept apart.** `EXCLUDED` was never attempted — no
template for its type, or its lineage could not be read. `REFUSED` was attempted
and the model rejected the draft. Collapsing them loses which of the two
happened, and they call for different fixes.

Rows are written for `CITED` Signals too. A table holding only exclusions could
say what was skipped and not what the denominator was, and the denominator is
the finding.

**Why the run and not the claim.** A Signal considered and not cited has no
claim to hang off, so a per-claim record would keep only the half that needs it
least. And a Signal excluded by version 1.0.0 and cited by 1.1.0 is two facts
about two executions, which a per-run row says and a per-claim row cannot.

## 9. Refusal reasons

Contract `1.10.0`. Three were added for this layer; the rest are Mission 1.13's,
reused rather than duplicated.

| Reason | Raised when |
|--------|-------------|
| `UNSUPPORTED_SIGNAL_TYPE` | No template for this Signal type |
| `SIGNAL_LINEAGE_UNAVAILABLE` | Contributing records unreadable, or one does not publish a fact the proposition names |
| `AMBIGUOUS_SIGNAL_LINEAGE` | Contributing records disagree — two resources, two sources, two language labels |
| `INCOMPATIBLE_TEMPORAL_SEMANTICS` | A basis this template cannot phrase; a contrast whose labels differ (H-29) |
| `INCOMPATIBLE_LANGUAGE_SEMANTICS` | A claim would need a named language (H-30) |
| `UNSUPPORTED_INTERPRETATION` | Market vocabulary in an OBSERVED statement; an `INDETERMINATE` direction with no faithful restatement |
| `NO_SUPPORTING_SIGNAL` | A generated non-hypothesis claim cites nothing |
| `SIGNAL_NOT_CITED` | An evidence draft names no Signal |
| `PROPOSITION_NOT_IDENTIFIABLE` | No facts to build a key from |
| `INTERPRETER_PROVENANCE_INCOMPLETE` | Half an identity, or a kind contradicting its model fields |

## 10. Idempotency, and what it is not

Delivery is at-least-once (ADR-004) and this does not pretend otherwise.

A second execution re-reads the same Signals, renders byte-identical statements,
finds every proposition stored and writes **no claim, no revision and no
evidence**. It writes a **second run row** and a second set of considered-input
rows, because a run is an execution and two executions happened.

Proven on the real data: run 1 wrote 7 claims, 7 revisions, 7 evidence rows; run
2 wrote 0, 0, 0 and reported 7 unchanged. Two run rows, fourteen considered rows.

**This is not exactly-once.** The CLAIMS are what is idempotent.

## 11. Tenancy

Three layers, none replacing another (ADR-012):

1. The explicit `workspace_id` filter in every query.
2. Row-level security, `ENABLE` plus `FORCE` on both new tables. An
   interpretation run names which Signals a workspace considered and which
   propositions it drew from them.
3. Composite foreign keys — `(workspace_id, signal_id)`, `(workspace_id,
   claim_id)`, `(workspace_id, run_id)` — so a run in workspace A can never name
   a Signal or a Claim in B.

A job whose payload names workspace A while the tenant context is B gets nothing
from the read **and** cannot write its run record: A's own policy refuses the
insert from inside B. Both layers are asserted by test.

## 12. What this runtime does not do

- **No Opportunity.** A Claim precedes one (ADR-024); grouping claims into one is
  a later decision and a separate mission.
- **No score.** D-03 is blocked and no `CALIBRATED` profile exists.
- **No embedding.** D-12 is open.
- **No LLM.** `MODEL_DERIVED` remains unused, and `validate_claims.py` fails the
  build on a model, network or embedder import anywhere in the layer.
