# Deterministic Inferred Claim Evaluator Foundation V1

**Mission 1.52 — Deterministic Inferred Claim Evaluator Foundation V1 — recorded 2026-09-05. Governed by ADR-036, ADR-037, migration 0034.**

> **This document is GENERATED.** Edit
> `deterministic-inferred-evaluator-foundation-v1.json` and re-run
> `infrastructure/scripts/render_deterministic_inferred_evaluator.py`.

## Primary outcome — `REFUSAL_DERIVATION_BINDING_CONTRACT_GAP`

A NOT_APPLICABLE or UNKNOWN evaluation cannot store its own refusal. `research.claim_derivations.claim_revision_id` is NOT NULL, and the evidence-requirement trigger exempts only HYPOTHESIS, MANUAL and WITHDRAWN — so binding a refusal would require first creating an INFERRED Claim that asserts a proposition the evaluation just declined to establish, plus an Evidence row for a measurement that was found not to bear. ADR-037 says a refusal produces a derivation record and no Evidence row; the schema built to hold it cannot express the first half without the second. **The evaluator was still built and proven, and it refuses correctly in memory — what it cannot do is write the refusal down.**

## Secondary outcome — `DETERMINISTIC_EVALUATOR_FOUNDATION_IMPLEMENTED`

`packages/inferred-claim-evaluator` exists at the path ADR-037 Q3 named, joins the zero-dependency runner, and implements the four gates over frozen value objects. 55 tests, all passing under bare `python`. It is a pure function: no database, no network, no model, no clock inside the predicate.

*One verdict would let either hide the other. Reporting only the gap would suggest nothing was built; reporting only the foundation would suggest the layer is ready to run. Both are true and they have different consequences for the next mission.*

## The conflict

**§20. Where does a refusal's derivation provenance go?**

Proven empirically in a disposable probe workspace created and removed inside one script, not reasoned about. Re-verified read-only against the live schema before this record was written.

| attempted | result | mechanism |
| --- | --- | --- |
| INSERT an INFERRED claim with no Evidence row | **REFUSED** | `research.require_evidence_for_generated_claim` |
| INSERT a claim_derivation with claim_revision_id NULL | **REFUSED** | `migration 0034 declares claim_revision_id NOT NULL` |

Trigger exemptions: `HYPOTHESIS (claim_type)`, `MANUAL (origin)`, `WITHDRAWN (lifecycle)`.

*INFERRED is not among them, and must not be added: the exemption list is what stops a machine storing an assertion nothing supports.*

*Deliberate in 1.51: binding to the revision is what stops a later derivation rewriting the reasoning behind an earlier one.*

**The squeeze.** Both refusals are correct on their own terms and jointly they leave a refusal nowhere to live. A derivation must name a revision; a revision requires a Claim; a generated INFERRED Claim requires Evidence; and a refusal produces no Evidence by ADR-037's own rule.

**What was deliberately not done:**

- No INFERRED Claim was created to host a refusal. §20 and the STOP CONDITION both forbid it, and a Claim asserting a proposition the evaluator declined to establish is a fabrication with provenance attached.
- INFERRED was not added to the trigger's exemption list. A guard widened to let new work through is a guard that never was.
- claim_revision_id was not made nullable. A nullable binding would let a derivation float free of the revision it explains, which is the defect 1.51 chose the NOT NULL to prevent.
- No third table was invented for orphan refusals. That is a schema decision with an ADR behind it, and this mission's brief forbids a migration.

**Why this is the upstream blocker.** §22's Evidence re-evaluation question is resolvable by policy today. This one is not resolvable by any policy, because it is a mutual constraint between two schema decisions each of which is individually right. Everything downstream of persistence waits on it.

## The Evidence re-evaluation question

**§22. What happens to canonical Evidence when the derivation rule version changes?**

Revision or supersession columns on `scoring.evidence`: **0**. `model_version` and `prompt_version` are provenance of the extraction procedure, not a revision model for the Evidence row. There is no `superseded_at`, no `revision`, no `is_current`.

**Resolution — POLICY_D.** A rule-version change produces ANOTHER derivation record and may never automatically alter canonical Evidence. Where the new derivation's direction disagrees with the standing Evidence row, the conflict is REPORTED for operator review and nothing is written.

*Why not overwrite.* Evidence has no supersession model, so an overwrite would destroy the earlier direction with no trace — and Mission 1.41 established that a changed assessment is neither unchanged nor a second observation.

*Why not a second Evidence row.* Evidence keys on (workspace, claim, signal). Mission 1.41 REMOVED extraction_method from that key precisely so a version bump could not INSERT a duplicate. Re-adding a version to the key here would undo that decision from the other end.

*Why this one is resolvable and the other is not.* Append-only derivations plus a reported conflict needs no schema change at all, because claim_derivations is already append-only per rule version. The refusal gap needs a schema decision nobody has taken.

Status: **RESOLVED_BY_POLICY_NOT_IMPLEMENTED**.

## The package

`packages/inferred-claim-evaluator`, distribution `sros-inferred-claim-evaluator`, depending on `sros-contracts`, `sros-claim-model`.

*ADR-037 allowed sros-signal-model as a third dependency. It was not taken: the evaluator consumes a MeasurementWitness value object rather than a Signal, so importing the signal model would add a dependency nothing uses. An allowance is not an obligation.*

**Four things it deliberately cannot do:**

- It cannot acquire — no sros_acquisition, so a component able to read the source registry cannot decide its own authorization.
- It cannot call a model — no Gateway, so 0 model calls is a property of the dependency graph rather than a promise.
- It cannot aggregate — no sros_evidence_aggregation. It emits an Evidence direction; deciding what that direction is worth is another layer.
- It cannot score reliability or adjudicate independence — neither is an input and neither is an output.

**How that is enforced.** By absent imports, asserted over the package's own modules, and structurally by the zero-dependency runner: the suite runs with only its own package plus SHARED_PATHS, so a forbidden import would not merely be against the rules, it would fail to resolve.

### Joining the zero-dependency runner

Suite `packages/inferred-claim-evaluator/python`; shared paths gained `packages/claim-model/python`.

**Mission 1.47's CI failure came from a test importing a package the zero-dependency runner does not expose, masked locally by `uv run`. The repair then was to move the proof, not to widen the runner. Here the evaluator genuinely depends on claim-model per ADR-037, so ONE named package joins SHARED_PATHS — the monorepo does not, and widening it to make an import work would delete the property the runner exists to check.**

Bare-`python` tests run before commit: **1313**.

## The four gates

**1. semantic equivalence** — NOT_EQUIVALENT -> NOT_APPLICABLE; UNKNOWN -> UNKNOWN

  - *why first*: A measurement of another quantity is not a disagreement about this one. Running the arithmetic first and relabelling afterwards would let the direction the comparison WOULD have produced leak into the refusal.
  - *never*: NOT_EQUIVALENT never produces CONTRADICTS.

**2. registration and scope match** — the registration must describe this proposition; unit and time bound must match exactly

  - *no conversion*: There is no unit conversion and no time alignment. A different unit is NOT_APPLICABLE, not a converted value; a different time bound is NOT_APPLICABLE, not an aligned one.
  - *no selection*: `evaluate` takes exactly one registration and never searches a collection, so 'whichever bound makes the Claim work' is not expressible.

**3. preregistration timing** — a PREREGISTERED registration requires recorded_at < witness.retrieved_at

  - *why not downgrade to post hoc*: A silent downgrade would quietly repair somebody's claim about when they decided. An inconsistent record is refused and reported, not corrected.
  - *on violation*: UNKNOWN with PREREGISTRATION_TIMING_INCONSISTENT

**4. the predicate** — exact Decimal comparison against the registered bound

  - *exactness*: A float measurement is refused at construction. 0.1 + 0.2 is not 0.3 in binary, and the boundary is exactly where a threshold proposition lives.

## What the evaluator never decides

| question | why it is not the evaluator's |
| --- | --- |
| `independence` | Not an input, not an output, and the string does not appear in an outcome. A dependent republication still SUPPORTS the same proposition; it simply stays one provenance group downstream. |
| `reliability` | Not an input, not an output. It is resolved late from a reviewed assessment against a five-part scope. |
| `interpretation_confidence` | Taken from the equivalence decision and never invented. The arithmetic being exact says nothing about whether the wording faithfully reads the Signal, and setting 1.0 automatically would assert certainty about a real judgement. |
| `equivalence` | Consumed as a reviewed decision. A NOT_EQUIVALENT verdict is honoured even where every visible field matches, because the reviewer knows something the fields do not show. |
| `the_threshold` | Consumed as a registration. The evaluator selects no bound of its own. |

## Proposition identity

Excluded: `source_id`, `measurement_value`, `direction`, `threshold_provenance_status`, `derivation_rule_version`, `evaluator_version`.

Included: `proposition_kind`, `canonical_subject_id`, `metric_definition_id`, `time_bound`, `population_or_geography`, `unit`, `threshold_operator`, `threshold_value`, `claim_type`.

Proved:

- 110 and 105 from different sources share one proposition key
- 110 and 90 — a support and a contradiction — share one proposition key
- a different threshold value is a different proposition
- threshold provenance status does not change the key
- Decimal('100') and Decimal('100.0') are one bound

*Otherwise the same threshold written two ways forks the proposition, which is the measurement-value defect of Mission 1.48 one field along.*

## Fixtures

|  | fixture | witnesses | result |
| --- | --- | --- | --- |
| **A** | independent corroboration | `110`, `105` | both SUPPORT one proposition |
| **B** | contradiction | `110`, `90` | one SUPPORTS and one CONTRADICTS one proposition |
| **C** | exact boundary | `100` | SUPPORTS under GTE, CONTRADICTS under GT |
| **D** | semantic mismatch | `110` | NOT_APPLICABLE, never CONTRADICTS |
| **E** | unknown equivalence | `110` | UNKNOWN, never SUPPORTS |
| **F** | dependent republication | `110`, `110` | both SUPPORT; one provenance group downstream |
| **G** | post-hoc threshold | `110` | SUPPORTS and calibration-INELIGIBLE |
| **H** | preregistration timing violation | `110` | UNKNOWN, PREREGISTRATION_TIMING_INCONSISTENT |

*D, E and H never reach an aggregator by construction — they produce no Evidence decision — so nothing pretends to run them through one.*

## Downstream compatibility

**§32. What must the aggregator change to accept the new layer?** Nothing.

`aggregate()` takes a claim id, a sequence of items and a profile, and no claim type at all. `EvidenceItem` carries no claim_type either — Mission 1.13 dropped it from `scoring.evidence` because two answers to one question eventually disagree. There is no parameter through which an INFERRED Claim's Evidence could be treated differently.

**A correction this mission made.** The first draft of the downstream test asserted that `EvidenceDirection` has no NEUTRAL member. It does. NEUTRAL is retained for provenance and coverage and contributes to neither strength, so nothing in the aggregation layer would refuse a refusal mapped onto it. **The guarantee is producer-side**: `EvaluationResult` has no NEUTRAL, and a refusal carries no EvidenceDecision at all, so the evaluator has nothing to hand over. Naming where a guarantee actually lives matters, because a NEUTRAL row would be counted and weightless — invisible in the numbers and visible in the counts, which is the exact shape ADR-037 refuses.

## The guard was not touched

`infrastructure/scripts/validate_claims.py` modified: **False**. It fails the build on any non-OBSERVED ClaimType access inside the OBSERVED interpretation package. Hosting the INFERRED evaluator there would require weakening it, and a guard removed to let new work through is a guard that never was. The evaluator lives in its own package for that reason and no other.

## Two tests, repaired rather than removed

**Re-pointed.** `packages/evidence-aggregation/python/tests/test_deterministic_inferred_contract.py::InterpreterGuardRemainsUntouched::test_the_package_was_not_created` asserted the evaluator package does not exist, which was true of Mission 1.50, a contract mission that wrote no code. A test asserting 0 forever is a test asserting the contract is never implemented — the repair shape of Missions 1.31.1, 1.40, 1.41 and 1.44.1. What survives is the boundary: the evaluator sits at the path Q3 named, and NOT inside the interpretation package the guard protects.

**Replaced.** `test_the_rule_version_and_the_evaluator_version_are_separate_facts` — It compared `id()` of two constants that both read "1.0.0", so CPython's interning made it assert that one string is not itself. Replaced with the property that matters: DerivationDraft declares both fields, because migration 0034's idempotency key contains derivation_rule_version and not evaluator_version — replaying a different RULE is different reasoning and earns its own row, while rebuilding the same rule under a new evaluator is not. One field could not carry both meanings.

*It failed on the first bare-python run, which is what that gate is for.*

## The validator was probed

**55 of 55 deliberate violations caught**, and the real record still validates.

A validator nobody probed is a validator nobody has tested. Each violation is a claim the record could plausibly have made and must not: a package at a path the repository does not have, INFERRED added to the trigger exemptions, a counter that moved, a source selected, the guard reported as modified, the next mission reported as started.

## Nothing moved

| counter | before | after |
| --- | --- | --- |
| `claims` | 43 | 43 |
| `claim_revisions` | 44 | 44 |
| `evidence` | 57 | 57 |
| `claim_derivations` | 0 | 0 |
| `threshold_registrations` | 0 | 0 |
| `inferred_claims` | 0 | 0 |
| `signals` | 33 | 33 |
| `raw_records` | 325 | 325 |
| `normalized_records` | 325 | 325 |
| `opportunities` | 1 | 1 |
| `reliability_assessments` | 4 | 4 |
| `independence_groups` | 0 | 0 |
| `scores` | 0 | 0 |

Research-data requests **0**, documentation requests **0**, metadata requests **0**.

Model calls **0**, embeddings **0**, calibration labels **0**, parameters fitted **0**, profile **UNCALIBRATED**, Problem-Family **PARKED**, source selected **NONE**.

STOP conditions honoured:

- no research observation acquired
- no source selected
- no production INFERRED Claim created
- no production Evidence created
- the evaluator was not run over canonical research rows for mutation
- no reliability assigned
- independence not decided automatically
- no aggregation inside the evaluator
- validate_claims.py not weakened
- SourceBoundary not modified
- no cross-source OBSERVED convergence added
- no model called
- no embeddings created
- no calibration
- no Scores created
- Opportunity unchanged
- Problem-Family still PARKED
- Mission 1.53 not started

## Next mission

**Refusal Derivation Binding Design V1** — Decide where a NOT_APPLICABLE or UNKNOWN evaluation's provenance lives, as a semantics question with an ADR behind it — never as an edit to a trigger or a nullability change made in passing.

Options identified and NOT chosen:

- A refusal record keyed on the INPUTS rather than on a claim revision, in its own table — no Claim needed, and no Claim implied.
- A nullable claim_revision_id with a CHECK requiring it exactly when evaluation_result is directional — narrow, and it weakens the binding 1.51 chose deliberately.
- Refusals kept only in the interpretation run log — rejected in advance by ADR-037's own measurement: those rows expire, and a refusal that vanishes is a refusal nobody can audit.

**Prefer:** The first, on the evidence available: it needs no exemption in the evidence-requirement trigger and no change to the derivation binding, so both guards of 1.51 stay exactly as strong as they are.

Still open:

- REFUSAL_DERIVATION_BINDING_CONTRACT_GAP — the blocker this mission found
- §22 policy D is decided and not implemented; it needs a conflict report nobody has written
- No threshold registration exists, so no proposition has a bound frozen before a measurement was retrieved
- The first INFERRED Evidence will resolve NO_APPLICABLE_ASSESSMENT, which is correct and means the first INFERRED rows are NON_SCORABLE
- Mission 1.43's finding still governs: with one provenance group the aggregator is algebraically the pass-through baseline

*Mission 1.53 was not started. The evaluator has nowhere to write a refusal, so running it over canonical rows would produce directional results and silently drop every refusal — which is the failure the whole derivation record exists to prevent.*

