# Deterministic Evaluation Persistence Orchestration V1

**Mission 1.55 — Deterministic Evaluation Persistence Orchestration V1 — recorded 2026-09-05. Governed by ADR-036, ADR-037, ADR-038; migrations 0034 and 0035.**

> **This document is GENERATED.** Edit
> `deterministic-evaluation-persistence-orchestration-v1.json` and re-run
> `infrastructure/scripts/render_persistence_orchestration.py`.

## Primary outcome — `DETERMINISTIC_EVALUATION_PERSISTENCE_ORCHESTRATION_READY`

One command routes an `EvaluationOutcome` to exactly one of two persistence paths, inside the caller's transaction. A directional outcome writes Claim, ClaimRevision, derivation and Evidence together or not at all; a refusal writes one refusal row and nothing else. Replay is idempotent by PAYLOAD rather than by key alone, and Policy D never updates or duplicates a standing Evidence direction. **0 canonical rows written: every end-to-end write lives in a disposable workspace and is removed with it.**

## Readiness, in two halves

Foundation ready **True**. Unattended production ready **False**.

Policy D returns a structured `REVIEW_REQUIRED` result and persists the disagreeing derivation, so an ATTENDED caller cannot miss a conflict. Nothing durable DECLARES the conflict, so an unattended batch that ignored the result would leave one detectable and unannounced. §27 asks for these to be reported apart, and collapsing them would claim a readiness this mission did not establish.

**What makes it detectable anyway.** The conflict is reconstructible from durable rows by an exact join, not a log scan: a `claim_derivations` row whose `evaluation_result` differs from the `scoring.evidence` direction for the same (workspace, claim, signal). A test runs that query and finds exactly one.

    SELECT ... FROM research.claim_derivations d JOIN research.claim_revisions r ON r.id = d.claim_revision_id JOIN scoring.evidence e ON e.claim_id = r.claim_id AND e.signal_id = d.input_signal_id WHERE d.evaluation_result <> e.direction

## The owner

`services/nlp/python/sros_nlp/inferred_persistence.py`

It is where Claim, revision and Evidence persistence already lives, and the transaction pattern already exists: `run_claim_interpretation_job` takes a `connection_factory` yielding a connection already inside a tenant transaction. Putting the orchestrator anywhere else would mean either duplicating `persist_claims` or importing it across a service boundary.

**Not the evaluator package.** It is deliberately pure and imports no database client. The dependency direction is persistence -> evaluator, and a test asserts the evaluator package still names neither `psycopg` nor `sros_nlp`.

**Not inside `interpreters/`.** `validate_claims.py` fails the build on any non-OBSERVED `ClaimType` access under `sros_nlp/interpreters`, and this module constructs an INFERRED Claim. The guard is DIRECTORY-scoped, so a sibling module is permitted and **the guard was not touched**. Hosting it one directory lower would have required weakening it.

Dependencies added: `sros-claim-model`, `sros-inferred-claim-evaluator`.

## The command

    persist_evaluation_outcome(conn, outcome, target)

Accepts an already-computed EvaluationOutcome. Evaluates: **False**.

A pure evaluation is repeatable and testable without touching a database. Calling `evaluate()` inside the command would make every persistence test also an evaluator test and hide which of the two failed.

**Transaction owner: the caller, through the connection it passes in.** The evidence requirement is a DEFERRED trigger firing at COMMIT, so Claim, revision, derivation and Evidence must be able to fail together. A command that opened its own transaction could not participate in a larger one, and the existing job already establishes the `connection_factory` pattern.

### Why the target is passed alongside the outcome

**The finding.** A refusal outcome carries NO proposition key and NO Claim draft, by the evaluator's own contract: it declines to name a proposition it just declined to establish. Migration 0035 requires the target key AND its preimage.

**The resolution.** The caller supplies the `TargetProposition` it already chose. The target is an INPUT, not something the evaluation concluded, so the caller is the right authority for it.

*Not resolved by* changing the evaluator to carry the target on a refusal, which would have been an evaluator semantic change this mission is forbidden to make -- and would have had the evaluator name a proposition it refused.

*For a directional outcome the supplied target's key is compared against the outcome's own, and a mismatch raises TARGET_MISMATCH before anything is written.*

## Routing

| evaluation result | path |
| --- | --- |
| `SUPPORTS` | **DIRECTIONAL** |
| `CONTRADICTS` | **DIRECTIONAL** |
| `NOT_APPLICABLE` | **REFUSAL** |
| `UNKNOWN` | **REFUSAL** |

Exhaustive over `EvaluationResult`, with no `else`. A member added later reaches a raise rather than a default, so a new result cannot silently take either path.

**NEUTRAL.** There is nothing to route: `EvaluationResult` has no NEUTRAL member. The guarantee is producer-side, and a test records where it lives rather than pretending a branch refuses it.

## The directional path

1. verify the threshold registration exists in this workspace, read-only
2. build the Claim through the canonical `build_claim`
3. persist_claims: Claim, ClaimRevision and Evidence
4. verify the stored proposition key recomputes from the stored facts
5. resolve the current revision id
6. insert or reuse the derivation, bound to that revision
7. return, or return REVIEW_REQUIRED if the repository reported an Evidence conflict

**A stated deviation — `STATED_DEVIATION`.** §5 lists derivation BEFORE Evidence. `persist_claims` writes Claim, revision and Evidence together, so the derivation lands after. §20 and §37 require reusing the canonical Claim API rather than re-implementing it, and that API owns its internal ordering. Ordering inside one transaction is not epistemically load-bearing here: the evidence requirement is deferred to COMMIT, so what matters is that all four land together, which the atomicity tests prove.

The Claim: `INFERRED` / `DETERMINISTIC`, origin `DETERMINISTIC_EXTRACTION`, temporality `EVERGREEN`, built by `sros_claim_model.build_claim`.

It enforces the evidence requirement in the model as well as in the trigger, and refuses an automated claim with no interpreter provenance or no interpretation confidence. A hand-rolled INSERT would skip all three.

*Reliability stays NULL.* It is purpose-relative and resolved late from a reviewed assessment. The first INFERRED Evidence will resolve NO_APPLICABLE_ASSESSMENT and be NON_SCORABLE, which is correct and is not this layer's to repair.

## The statement

Composed from the target proposition and nothing else, excluding the source, the measurement value, the direction, the rule version, the signal id.

**`_persist_one` appends a new ClaimRevision whenever the statement differs from the stored one. A statement naming the witness or the measurement would make every additional Signal supporting the same proposition look like a reformulated Claim -- revision churn saying the proposition changed when only the evidence grew. ADR-036's whole point is that several witnesses reach ONE source-independent Claim, and that only holds if they all word it identically.**

*Proved:* Two witnesses at 110 and 105 produce one Claim, one revision, two Evidence rows and two derivations.

*Where it lives:* the persistence module. Adding a statement to the evaluator would be an evaluator semantic change, which this mission is forbidden to make. The cost is stated: if the evaluator ever grows its own wording, the two must be reconciled rather than allowed to disagree.

## Idempotency

**IDEMPOTENT means same identity AND same semantic payload. A matching unique key with a different payload is a CONFLICT, not a replay.**

| entity | identity | on divergence |
| --- | --- | --- |
| claim | `(workspace_id, proposition_key)` | **the stored preimage must recompute to the stored key, or PROPOSITION_IDEMPOTENCY_CONFLICT** |
| derivation | `(workspace_id, claim_revision_id, input_signal_id, derivation_rule_version)` | **DERIVATION_IDEMPOTENCY_CONFLICT** |
| refusal | `(workspace_id, input_signal_id, target_proposition_key, derivation_rule_version, semantic_equivalence_basis_id)` | **REFUSAL_IDEMPOTENCY_CONFLICT** |
| evidence | `(workspace_id, claim_id, signal_id)` | **unchanged** |

*Deliberately, and it matters: the key excludes it too, so rebuilding the software is not a new derivation. Reaching a DIFFERENT conclusion under the same rule version is a finding, and that is what the payload comparison catches.*

*The unique key is narrower than the row. A unit mismatch and a time-bound mismatch share every identity column and differ only on the reason code, which is exactly what a swallowed unique violation would have hidden.*

## Policy D

**Option A** — Persist the new derivation, leave Evidence untouched, return REVIEW_REQUIRED.

Rejected: Roll the whole re-evaluation back with no new derivation.

Derivations are append-only records of what a rule concluded. Rolling one back would discard the very finding the reviewer is being asked about, and leave a review request pointing at nothing. The two rows are not incoherent: the derivation says what rule v2 concluded, the Evidence says what the standing relation is, and Mission 1.41 already established that Evidence identity is epistemic while the procedure is provenance.

**Detection is not re-implemented.** `_persist_evidence` already compares the load-bearing factors of an existing relation and, on disagreement, records a conflict and writes NOTHING. The orchestrator reads that finding and turns it into a result a caller can branch on. Re-comparing here would be a second authority for one question.

Evidence updated **False**, duplicated **False**, deleted **False**, silent success **False**.

Conflict report fields: `workspace_id`, `claim_id`, `signal_id`, `evidence_id`, `existing_direction`, `evaluated_direction`, `derivation_rule_id`, `derivation_rule_version`, `evaluator_version`, `target_proposition_key`, `semantic_equivalence_basis_id`, `reason`.

*The repository's conflict entry records which relation conflicted and on what extraction method, and does not enumerate the differing factors. So the standing direction is read from the Evidence row rather than from the report -- a placeholder would have put an invented value in front of a reviewer.*

**Durable storage: NONE dedicated. The disagreement is reconstructible by an exact join; no row declares it a conflict.**

## A system failure is not a refusal

Error codes: `INVALID_OUTCOME`, `WORKSPACE_MISMATCH`, `TARGET_MISMATCH`, `THRESHOLD_NOT_FOUND`, `PROPOSITION_IDEMPOTENCY_CONFLICT`, `DERIVATION_IDEMPOTENCY_CONFLICT`, `REFUSAL_IDEMPOTENCY_CONFLICT`.

A database error is not an UNKNOWN evaluation and a missing threshold is not a NOT_APPLICABLE one. The command accepts an EvaluationOutcome and nothing else, so an exception has no shape to be filed as a refusal.

## Thresholds

Read-only **True**; created **False**, selected **False**, mutated **False**, provenance upgraded **False**.

The bound an evaluation compared against must be the one that was frozen. Registering it on the way past would be the analyst choosing the number after seeing the measurement.

*A POST_HOC threshold produces a directional SUPPORTS that persists normally. Provenance changes calibration eligibility, never entailment.*

## Proofs

| proof | result |
| --- | --- |
| directional commit | 1 Claim, 1 revision, 1 derivation, 1 Evidence, 0 refusals, all in one workspace, committed |
| refusal commit | 1 refusal and nothing else; claims, revisions, evidence, derivations and thresholds all unchanged |
| rollback after the full directional write | everything absent, verified through a SEPARATE connection |
| rollback at the evidence step | the Signal the Evidence must reference is deleted first, so the failure lands inside the command after Claim and revision are written; nothing survives |
| missing threshold | fails before any write |
| refusal rollback | no refusal row survives |
| deferred trigger | a committed directional transaction satisfies it; the test forces SET CONSTRAINTS ALL IMMEDIATE rather than relying on a rollback |
| two supports | one Claim, one revision, two Evidence, two derivations |
| support and contradiction | one Claim, one revision, Evidence directions SUPPORTS and CONTRADICTS, two derivations |
| rule bump same direction | derivation created, Evidence reused, Claim and revision unchanged |
| rule bump opposite direction | REVIEW_REQUIRED; Evidence neither updated nor duplicated; the disagreeing derivation IS recorded |
| unknown then supports | the historical UNKNOWN refusal keeps its result, reason code and original basis; the new Claim, derivation and Evidence exist alongside it |
| cross workspace signal | refused |
| reliability untouched | the persisted Evidence carries NULL reliability, UNKNOWN independence and no group |

## Two stated deviations, and one limitation

**The aggregator was not re-run — `STATED_DEVIATION`.** §42 and §43 ask for a downstream aggregator diagnostic over the persisted rows. The SHAPE is asserted where it is produced: one Claim with a SUPPORTS and a CONTRADICTS Evidence row, and one Claim with two SUPPORTS rows. The aggregation suite is bare-python with no database, so it cannot read persisted rows; and running the aggregator from the persistence suite would put it on that suite's import path, which §42 itself forbids. Mission 1.49 already drove the REAL aggregator over exactly these two shapes -- contradiction with masses summing to one, and two independent supports exceeding the strongest member. What Mission 1.55 adds is that the shape now arrives from persistence rather than from a hand-built fixture, and that is what is tested here.

**Concurrency is untested.** The idempotency checks are SELECT-then-INSERT. Under two genuinely concurrent attempts the loser hits the database UNIQUE constraint and its transaction rolls back, so no duplicate can exist -- but it surfaces as a driver error rather than as REUSED.

*It is safe and it is not graceful, and a later mission running this unattended should know which it is. No distributed locking was added: §36 forbids it in V1.*

## The validator was probed

**71 of 71 deliberate violations caught**, and the real record still validates.

Each violation is a claim this record could plausibly have made and must not: a NEUTRAL route, an else branch, idempotency by key alone, a derivation comparison that would make rebuilding the software a conflict, Evidence updated on a Policy D conflict, a statement naming its witness, a threshold mutated in passing, a canonical pilot run, an unattended pilot recommended while unattended readiness is false.

## Nothing moved

| counter | before | after |
| --- | --- | --- |
| `raw_records` | 325 | 325 |
| `normalized_records` | 325 | 325 |
| `signals` | 33 | 33 |
| `claims` | 43 | 43 |
| `claim_revisions` | 44 | 44 |
| `evidence` | 57 | 57 |
| `inferred_claims` | 0 | 0 |
| `claim_derivations` | 0 | 0 |
| `threshold_registrations` | 0 | 0 |
| `proposition_evaluation_refusals` | 0 | 0 |
| `reliability_assessments` | 4 | 4 |
| `independence_groups` | 0 | 0 |
| `opportunities` | 1 | 1 |
| `opportunity_revisions` | 1 | 1 |
| `opportunity_evidence_links` | 7 | 7 |
| `embeddings` | 0 | 0 |
| `sources` | 29 | 29 |

Research-data requests **0**, documentation requests **0**, metadata requests **0**.

Model calls **0**, embeddings **0**, profile **UNCALIBRATED**, Problem-Family **PARKED**, migration created **False**, canonical pilot run **False**.

STOP conditions honoured:

- persistence was not run over canonical dev research rows
- no first canonical INFERRED Claim created
- no canonical INFERRED Evidence created
- no threshold registration added for a held source
- no sources discovered
- no observations acquired
- evaluator semantics unchanged
- Claim identity unchanged
- Evidence identity unchanged
- no automatic Evidence direction mutation
- no broad operator workflow implemented
- no reliability assigned
- no calibration
- no Scores fitted
- Opportunity unchanged
- no model called
- no embeddings created
- Problem-Family still PARKED
- Mission 1.56 not started

## Next mission

**Mission 1.56 — First Deterministic Inferred Claim Persistence Pilot V1**, attended: **True**.

Policy D reports a conflict through the command result, and nothing durable declares one. A single-candidate operator-supervised pilot is inside what this mission established; an unattended batch is not.

ONE candidate, from data already held, with no acquisition. The threshold registration must be frozen BEFORE the evaluation, the semantic-equivalence basis must be reviewed, and the resulting Evidence will resolve NO_APPLICABLE_ASSESSMENT and be NON_SCORABLE, which is the correct outcome and not a defect to fix.

Still open:

- no durable row declares an Evidence direction conflict; it is detectable by join and announced only through the command result
- concurrent replay surfaces as a driver error rather than as REUSED
- the Claim statement is composed in the persistence layer, not by the evaluator; if the evaluator ever grows its own wording the two must be reconciled
- no threshold registration exists for any held source, so no proposition has a bound frozen before a measurement was retrieved

*Mission 1.56 was not started.*

