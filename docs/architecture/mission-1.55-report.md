# Mission 1.55 — Deterministic Evaluation Persistence Orchestration V1

**Primary outcome: `DETERMINISTIC_EVALUATION_PERSISTENCE_ORCHESTRATION_READY`.**

One command routes an `EvaluationOutcome` to exactly one of two persistence
paths, inside the caller's transaction. Replay is idempotent by **payload**
rather than by key alone, and Policy D never updates or duplicates a standing
Evidence direction.

**Readiness is reported in two halves and they are not the same.**
`FOUNDATION_READY = true`. `UNATTENDED_PRODUCTION_READY = false`. **0 canonical
rows written** — every end-to-end write lives in a disposable workspace and goes
with it.

---

## Setup

**1-5.** Mission 1.54 merged as PR
[#97](https://github.com/Speekyx/startup-research-os/pull/97) at `7f1f387`,
verified against Git; branch `sprint-1/mission-1.55`; migration head
`0035_refusal_provenance`. Baseline exactly as the brief: 325 / 325 / 33 Signals,
43 Claims, 44 revisions, 57 Evidence, INFERRED **0**, thresholds **0**,
derivations **0**, refusals **0**, Opportunity 1 / 1 / 7, sources 29,
`scoring.scores` ABSENT, workspaces `dev` and `dev-other`.

---

## The owner

**6-8.** `services/nlp/python/sros_nlp/inferred_persistence.py`.

That is where Claim, revision and Evidence persistence already lives, and where
the transaction pattern already exists — `run_claim_interpretation_job` takes a
`connection_factory` yielding a connection already inside a tenant transaction.
Anywhere else would have meant duplicating `persist_claims` or importing it
across a service boundary.

**Not inside `interpreters/`**, and that mattered: `validate_claims.py` fails the
build on any non-OBSERVED `ClaimType` access under that directory, and this
module constructs an INFERRED Claim. The guard is **directory-scoped**, so a
sibling module is permitted — **and the guard was not touched.** Hosting the
orchestrator one directory lower would have required weakening it.

**The evaluator still reaches no database.** Dependencies added to `sros-nlp`:
`sros-claim-model` and `sros-inferred-claim-evaluator`. The direction is
persistence → evaluator, and a test asserts the evaluator package names neither
`psycopg` nor `sros_nlp`.

---

## The command

**9-11.** `persist_evaluation_outcome(conn, outcome, target)` → `PersistenceResult`.

It accepts an already-computed outcome and **does not evaluate**. A pure
evaluation is repeatable without touching a database; calling `evaluate()` inside
would make every persistence test also an evaluator test and hide which failed.

**It does not own its transaction.** The connection arrives inside the caller's,
which is what lets the whole directional path be atomic — the evidence
requirement is a deferred trigger firing at COMMIT.

### Why the target is passed alongside the outcome

**A finding, not a signature preference.** A refusal outcome carries **no**
proposition key and **no** Claim draft, by the evaluator's own contract: it
declines to name a proposition it just declined to establish. Migration 0035
requires the target key **and** its preimage.

So the caller supplies the `TargetProposition` it already chose. The target is an
**input**, not something the evaluation concluded. The alternative — teaching the
evaluator to carry the target on a refusal — would have been an evaluator
semantic change this mission is forbidden to make, and would have had the
evaluator name a proposition it refused. For a directional outcome the two keys
are cross-checked, and a mismatch raises `TARGET_MISMATCH` before anything is
written.

---

## Routing

**12-17.** Exhaustive over `EvaluationResult`, read from the AST by the validator
because the module explains the routing in prose too.

| result | path |
| --- | --- |
| `SUPPORTS` | DIRECTIONAL |
| `CONTRADICTS` | DIRECTIONAL |
| `NOT_APPLICABLE` | REFUSAL |
| `UNKNOWN` | REFUSAL |

**No `else`.** A fifth member added later reaches a `raise`, not a default.
**No NEUTRAL path**, because there is nothing to route: `EvaluationResult` has no
such member, and the test records where that guarantee lives rather than
pretending a branch refuses it.

---

## The directional path

**18-19.** Threshold verified read-only → `build_claim` → `persist_claims`
(Claim, revision, Evidence) → stored key re-verified → current revision resolved
→ derivation inserted or reused. **The caller owns the transaction.**

**A stated deviation.** §5 lists the derivation *before* Evidence. `persist_claims`
writes Claim, revision and Evidence together, so the derivation lands after.
§20 and §37 require reusing the canonical Claim API rather than re-implementing
it, and that API owns its internal ordering. Ordering inside one transaction is
not epistemically load-bearing here — the trigger is deferred to COMMIT, so what
matters is that all four land together, which the atomicity tests prove.

**20-21.** The Claim is built by `sros_claim_model.build_claim`, not a hand-rolled
INSERT: it enforces the evidence requirement in the model as well as in the
trigger, and refuses an automated claim with no interpreter provenance or no
interpretation confidence. Claim idempotency stays `(workspace_id,
proposition_key)`, plus one extra check — the stored preimage must recompute to
the stored key, or `PROPOSITION_IDEMPOTENCY_CONFLICT`.

### The statement, which is where §9 and §10 are actually decided

**22-23.** `_persist_one` appends a new ClaimRevision whenever the statement
differs from the stored one. So a statement naming the witness, the measurement
or the source would make **every additional Signal supporting the same
proposition look like a reformulated Claim** — revision churn saying the
proposition changed when only the evidence grew.

The statement is therefore composed from the **target proposition and nothing
else**. Proved: two witnesses at 110 and 105 produce **one Claim, one revision,
two Evidence rows and two derivations**. A support at 110 and a contradiction at
90 produce **one Claim, one revision, two Evidence rows with opposite
directions**.

It lives in the persistence layer rather than the evaluator, because adding a
statement to the evaluator would be the semantic change this mission may not
make. The cost is stated: if the evaluator ever grows its own wording, the two
must be reconciled rather than allowed to disagree.

---

## Idempotency

**24-29.** **Idempotent means same identity AND same semantic payload.** A
matching unique key with a different payload is a conflict, not a replay.

| entity | identity | on divergence |
| --- | --- | --- |
| Claim | `(workspace_id, proposition_key)` | `PROPOSITION_IDEMPOTENCY_CONFLICT` |
| derivation | `(workspace, revision, signal, rule version)` | `DERIVATION_IDEMPOTENCY_CONFLICT` |
| refusal | `(workspace, signal, target key, rule version, basis)` | `REFUSAL_IDEMPOTENCY_CONFLICT` |
| Evidence | `(workspace_id, claim_id, signal_id)` | unchanged by this mission |

**`evaluator_version` is excluded from the derivation comparison, deliberately.**
The identity excludes it too, so rebuilding the software is not a new derivation.
Reaching a *different conclusion* under the same rule version is a finding, and
that is what the payload comparison catches.

**The refusal comparison matters for a concrete reason.** A unit mismatch and a
time-bound mismatch share every identity column and differ only on the reason
code — exactly what a swallowed unique violation would have hidden. A test drives
both through the real evaluator and expects a conflict.

---

## Policy D

**31-38. Option A: persist the new derivation, leave Evidence untouched, return
`REVIEW_REQUIRED`.**

Option B — rolling the whole re-evaluation back — was rejected because
derivations are append-only records of what a rule concluded. Rolling one back
would discard the very finding the reviewer is being asked about, and leave a
review request pointing at nothing. The two rows are not incoherent: the
derivation says what rule v2 concluded, the Evidence says what the standing
relation is, and Mission 1.41 already established that Evidence identity is
epistemic while the procedure is provenance.

**Detection is not re-implemented.** `_persist_evidence` already compares the
load-bearing factors of an existing relation and, on disagreement, records a
conflict and writes nothing. The orchestrator reads that finding and turns it
into a result a caller can branch on. Re-comparing here would be a second
authority for one question.

Proved on real rows: rule v1 SUPPORTS then rule v2 CONTRADICTS gives
`REVIEW_REQUIRED`, **one** Evidence row still reading `SUPPORTS`, and **two**
derivations.

**One detail worth naming.** The repository's conflict entry records which
relation conflicted and on what extraction method, and does not enumerate the
differing factors — so the standing direction is read from the Evidence row
rather than from the report. A placeholder there would have put an invented value
in front of a reviewer.

**37-38. Durable storage: none dedicated.** The disagreement is reconstructible
from durable rows by an exact join — a derivation whose `evaluation_result`
differs from the Evidence direction for the same (workspace, claim, signal) — and
a test runs that query and finds exactly one. **What no row does is declare it a
conflict.** That is the gap, and it is why unattended readiness is `false` while
foundation readiness is `true`.

---

## Refusals, thresholds, failures

**39-44.** The refusal path writes one row and nothing else: claims, revisions,
Evidence, derivations and threshold registrations are all unchanged. Replay
returns the same row as `REUSED`. Before insert the stored key is recomputed from
the stored facts, because migration 0035 stores both halves and checks neither
against the other — the producer is the only place that can be verified.

Thresholds are **read-only**: never created, selected, mutated or
provenance-upgraded. A missing one raises `THRESHOLD_NOT_FOUND` before any write,
because registering the bound on the way past would be the analyst choosing the
number after seeing the measurement. A `POST_HOC` threshold still persists a
directional SUPPORTS — provenance changes calibration eligibility, never
entailment.

**A system failure is never an epistemic finding.** Seven structured error codes,
raised so the caller's transaction unwinds. The command accepts an
`EvaluationOutcome` and nothing else, so an exception has no shape to be filed as
a refusal.

---

## Atomicity

**45-52.** Every rollback is verified through a **separate connection** — a read
inside the aborted transaction would see its own uncommitted writes, which is how
a rollback test passes without proving anything.

| failure | result |
| --- | --- |
| after the full directional write | Claim, revision, derivation, Evidence all absent |
| at the Evidence step (the Signal is deleted first, so the failure lands inside the command after Claim and revision are written) | nothing survives |
| missing threshold | fails before any write |
| refusal path | no refusal row survives |

**The deferred trigger is forced, not assumed.** One test commits a directional
transaction and calls `SET CONSTRAINTS ALL IMMEDIATE`; Mission 1.53 spent a build
learning that a rollback-only fixture never fires a deferred check.

**53. The ADR-038 transition, end to end.** An UNKNOWN under one basis persists a
refusal; a later EQUIVALENT under a different basis persists Claim, derivation
and Evidence. The historical refusal keeps its result, its reason code and its
**original** basis, and is neither rewritten nor removed.

---

## What did not change

**54-63.** Proposition facts with **array values** remain valid — Mission 1.54's
correction is honoured, and no all-values-are-strings assumption exists anywhere
in this layer. Cross-workspace references are refused. No migration; head stays
`0035`. Claim identity, Evidence identity, the evidence-requirement trigger and
`validate_claims.py` are all untouched. No canonical INFERRED Claim, no canonical
Evidence mutation, **0 production derivation, refusal or threshold rows**.

**64-72.** 0 research-data requests, 0 documentation requests, 0 metadata
requests, 0 model calls, 0 embeddings, 0 new reliability assessments, no
calibration, Opportunity 1 / 1 / 7 unchanged, `REFERENCE_PROFILE_V1` still
`UNCALIBRATED`, Problem-Family still `PARKED`, workspaces `dev` and `dev-other`.

---

## Tests

**73-75.** 1354 bare-`python` tests and **3308** pytest tests, all passing, with
the leak check reporting the database unchanged across 29 tenant tables. 35 new
transactional tests. Validator probed with **71 deliberate violations, 71
caught**.

### Two stated deviations and one limitation

**The aggregator was not re-run over the persisted rows.** §42 and §43 ask for
it. The aggregation suite is bare-`python` with no database, so it cannot read
persisted rows; and running the aggregator from the persistence suite would put
it on that suite's import path, which §42 itself forbids. What is tested is the
**shape** where it is produced — one Claim with a SUPPORTS and a CONTRADICTS row,
and one Claim with two SUPPORTS rows. Mission 1.49 already drove the real
aggregator over exactly those two shapes; what Mission 1.55 adds is that the
shape now arrives from persistence rather than from a hand-built fixture.

**Concurrency is untested.** The idempotency checks are SELECT-then-INSERT, so
under two genuinely concurrent attempts the loser hits the database UNIQUE
constraint and rolls back. No duplicate can exist — the database is the final
authority — but it surfaces as a driver error rather than as `REUSED`. Safe, not
graceful, and recorded so a later unattended mission knows which.

**One fixture fact worth recording.** `scoring.evidence.source_id` carries a
foreign key into `registry.sources`, so a synthetic source id cannot be used and
the fixtures name a registered one. The rows are still entirely synthetic; the
constraint simply refuses Evidence naming a publisher the registry has never
heard of.

---

## Outcome

**77-79. Primary outcome:**
`DETERMINISTIC_EVALUATION_PERSISTENCE_ORCHESTRATION_READY`, with readiness
reported in two halves rather than collapsed.

**Recommended next: Mission 1.56 — First Deterministic Inferred Claim Persistence
Pilot V1, ATTENDED.** Policy D reports a conflict through the command result and
nothing durable declares one, so a single-candidate operator-supervised pilot is
inside what this mission established and an unattended batch is not.

The pilot uses **already-held data with no acquisition**, one candidate, with the
threshold registration frozen **before** the evaluation and the
semantic-equivalence basis reviewed. The resulting Evidence will resolve
`NO_APPLICABLE_ASSESSMENT` and be `NON_SCORABLE`, which is correct and not a
defect to fix.

Still open:

- No durable row declares an Evidence direction conflict.
- Concurrent replay surfaces as a driver error rather than as `REUSED`.
- The Claim statement is composed in the persistence layer, not by the evaluator.
- No threshold registration exists for any held source, so no proposition has a
  bound frozen before a measurement was retrieved.

**Mission 1.56 was not started.**

---

## Artifacts

- `services/nlp/python/sros_nlp/inferred_persistence.py`
- `services/nlp/python/tests/test_inferred_persistence.py` — 35 transactional tests
- `docs/data/deterministic-evaluation-persistence-orchestration-v1.json` / `.md`
- `infrastructure/scripts/render_persistence_orchestration.py` — wired into CI
