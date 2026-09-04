# Mission 1.53 — Refusal Derivation Binding Design V1

**Primary outcome: `INPUT_KEYED_REFUSAL_PROVENANCE_MODEL_SELECTED`.**

A refusal gets its own append-only record, keyed on the input witness, the
candidate target proposition, the derivation rule version and the reviewed
equivalence basis. It names no ClaimRevision, creates no Claim, produces no
Evidence, and needs no change to `claim_derivations`, to the evidence-requirement
trigger, or to any existing schema. **ADR-038 is Accepted. No migration was
created and no table exists.**

Option B was not rejected on taste. It was measured, and it fails on two of the
ten selection criteria.

---

## Setup

**1. Was Mission 1.52 merged?** Yes — PR
[#95](https://github.com/Speekyx/startup-research-os/pull/95), merged at
`78e322c`, verified against Git rather than taken from the brief.

**2. Exact main commit?** `78e322c`, local and origin identical, tree clean.

**3. Dedicated branch?** `sprint-1/mission-1.53`.

**4. Baseline counters?** RawRecords 325, NormalizedRecords 325, Signals 33,
Claims 43, ClaimRevisions 44, Evidence 57, INFERRED Claims **0**, assessments 4,
independence groups 0, threshold registrations **0**, claim_derivations **0**,
Opportunity 1 / 1 / 7, embeddings 0, sources 29, `scoring.scores` ABSENT,
workspaces `dev` and `dev-other`. Every one matches the brief. Frozen in
`refusal-derivation-binding-baseline-v1.json`.

**5. Migration head?** `0034_deterministic_derivation_provenance`, unmoved.

**6. Evaluator present?** Yes, `packages/inferred-claim-evaluator`, unmodified.

**7. Live trigger exemptions?** Read from the installed function:
`HYPOTHESIS` (claim_type), `MANUAL` (origin), `WITHDRAWN` (lifecycle).
**`INFERRED` does not appear anywhere in it.**

**8. Live `claim_revision_id` nullability?** `NO`.

---

## The conflict, re-proved

**9. Conflict re-proven?** Yes, in a disposable workspace, and the first attempt
was wrong in a way worth recording.

| probe | attempted | result | mechanism |
| --- | --- | --- | --- |
| A | INFERRED claim, no Evidence | **REFUSED** 23514 | `require_evidence_for_generated_claim` |
| A2 | HYPOTHESIS claim, no Evidence | **ACCEPTED**, rolled back | the exemption list |
| B | derivation, NULL revision | **REFUSED** 23502 | 0034's `NOT NULL` |
| C | three identical rows, NULL revision | **ALL THREE ADMITTED** | PostgreSQL 16.4 NULL semantics |

**Probe A's first run used `origin = 'AUTOMATED'`**, which is not a member of
`claims_origin_check`. It was refused by the wrong constraint and proved nothing
about the evidence requirement — while looking exactly like the result I wanted.
Fixed, and **A2 was added as a control**: without it, probe A shows only that
something refused.

**Probe C is the measurement Mission 1.52 did not make, and it decides Option B.**
`claim_derivations_identity_key` is `UNIQUE (workspace_id, claim_revision_id,
input_signal_id, derivation_rule_version)`, and PostgreSQL treats NULLs as
distinct. Making the column nullable **silently removes the table's only
idempotency guarantee from exactly the rows the change exists to add**, and
nothing reports it. The same temp table refused a duplicate the moment the
column was populated.

**One thing 0034 already did.** Its
`claim_derivations_threshold_required_check` makes the threshold registration
optional *precisely* for `NOT_APPLICABLE` and `UNKNOWN`, and its result CHECK
admits all four values. The table was shaped expecting refusals, and a different
constraint in the same migration made them impossible. That is the finding, not
a tie-breaker for Option B.

---

## The design

**10. Definition of refusal provenance?** A durable audit record of a
deterministic attempt to determine whether measurement M bears on candidate
proposition P, where the result was `NOT_APPLICABLE` or `UNKNOWN`. It is not a
Claim, not Evidence, not a reliability assessment, not an Opportunity finding,
not an execution log and not a system-error record.

**11. Exact audit questions?** All twenty of §2, each mapped to the field that
answers it. A design answering one from prose is rejected, and the validator
enforces that every question names a field.

**12-15. Options evaluated?** All three, on the twelve criteria, with
`STRONG | MEDIUM | WEAK | FAIL` and no weighted score.

- **A — SELECTED.** Passes all ten selection criteria.
- **B — REJECTED** on `TARGET_PROPOSITION_AUDITABILITY` and
  `IDEMPOTENCY_CLARITY`. `claim_derivations` identifies its proposition **only
  through** `claim_revision_id`, so with that NULL the row cannot say what was
  refused; and probe C proved the identity key stops constraining. Repairing both
  means adding a proposition key, a preimage, a reason code, a second partial
  unique index and three conditional CHECKs — Option A inside a table whose name
  says it is about actual ClaimRevisions. **The choice is not one table against
  two; it is one honest table against one table meaning two things with two
  identity keys.**
- **C — REJECTED** on `RETENTION_DURABILITY`, from live state: 12 of 12
  interpretation runs carry an `expires_at`, and the inputs foreign key is
  `ON DELETE CASCADE`. Retention was not redesigned to rescue it.

**16-17. Selected design and why?** Option A, because it is the only one that
answers all twenty audit questions while leaving every existing guarantee
untouched. **`claim_derivations` keeps one clean meaning**, and the
evidence-requirement trigger needs no exemption because no Claim is created —
every alternative ends at a request to exempt `INFERRED`.

**18. Does it fabricate a Claim?** No. The entity has no `claim_id` and no
`claim_revision_id`, and their absence is the point.

**19. Any Evidence for a refusal?** None. No `evidence_id`, and the result CHECK
admits no direction.

**20. Survives run expiry?** Yes — no foreign key to either interpretation-run
table.

**21. Preserves the claim_derivations invariant?** Yes. Every row there still
names a real ClaimRevision.

**22. Trigger change required?** **No.** This is Option A's decisive practical
advantage.

---

## The candidate target

**23-27. Representation?** `target_proposition_key TEXT NOT NULL` plus
`target_proposition_facts JSONB NOT NULL` — the key **and** its exact preimage,
in the vocabulary `research.claims.proposition_facts` already uses.

**Why sufficient:** measured, not assumed. All **43** live Claims carry both, the
discriminator key is `proposition` on all 43, and the evaluator already emits
`"proposition"`. A descriptor keyed on `proposition_kind` could never produce the
same key as the Claim it may later become — which is exactly what §34's
traceability needs, so it was checked.

The key is **recomputable**: a reader runs `proposition_key(facts)` and compares,
so the stored key is verifiable rather than trusted. A test does exactly that.

**A hash alone was rejected** because unlike a Claim there is no row elsewhere to
recover the facts from. **A candidate-proposition registry was rejected** as
Claims before Claims. **The threshold registration was rejected on a measured
fact**: three of the seven live reason codes refuse at gate 1, before the
registration is consulted, so it fails exactly on the most common refusals.

**28-29. Any generic JSON?** Yes, and its safeguards are enumerated: the existing
Claim vocabulary, `canonical_json` serialization, key recomputation, constraints
mirroring the Claim table, flat string values, no load-bearing prose.

**One deviation from the brief, flagged rather than buried.** §31 asked for a
canonical schema version on the descriptor. **It is not included.**
`derivation_rule_version` already pins which fact set was emitted, because
`target_proposition_facts()` lives in the rule module — so a second version field
would be a second authority for one fact, the pattern this repository refuses.
The cost if that reasoning is wrong is stated in the record, and the status is
`OPERATOR_REVIEWABLE_DEVIATION`.

**30. Generic or family-specific?** Generic, with one family-specific optional
foreign key. The descriptor is the vocabulary all seven live proposition kinds
already use; only `threshold_registration_id` is THRESHOLD_STATE-shaped, and it
is nullable, so another family never trips it.

---

## Vocabulary and constraints

**31. Refusal result vocabulary?** `NOT_APPLICABLE` and `UNKNOWN`, enforced by a
CHECK. `SUPPORTS`, `CONTRADICTS` and `NEUTRAL` are structurally unrepresentable.

**32. Reason codes?** The seven the evaluator actually raises, read from its
`_refuse` calls via the AST. **Zero invented, zero renamed.** The validator
compares the record against the source and refuses a mismatch in either
direction.

| reason code | result | gate | registration required |
| --- | --- | --- | --- |
| `SEMANTIC_MISMATCH` | NOT_APPLICABLE | 1 | no |
| `EQUIVALENCE_NOT_ESTABLISHED` | UNKNOWN | 1 | no |
| `EQUIVALENCE_DIMENSIONS_INCOMPLETE` | UNKNOWN | 1 | no |
| `THRESHOLD_REGISTRATION_MISMATCH` | NOT_APPLICABLE | 2 | **yes** |
| `UNIT_MISMATCH` | NOT_APPLICABLE | 2 | **yes** |
| `TIME_BOUND_MISMATCH` | NOT_APPLICABLE | 2 | **yes** |
| `PREREGISTRATION_TIMING_INCONSISTENT` | UNKNOWN | 3 | **yes** |

Result answers WHAT and drives the contract; reason code answers WHY and drives
the audit; rationale is human-readable and the authority for nothing.

**33-34. Semantic-equivalence basis?** `NOT NULL`, and that is a measured fact
rather than a convenience: `SemanticEquivalenceDecision` refuses a blank
`basis_id` for **every** verdict including `UNKNOWN`, so no evaluation can occur
without one and no fake identifier needs inventing.

**The bound this puts on the store is stated.** The evaluator only refuses pairs
somebody has already reviewed. An unreviewed pair produces no decision object,
so `evaluate` is never called and no refusal exists. The store answers *what did
we try and decline*, never *what did we never consider*.

**35. Threshold conditionality?** Nullable, required by CHECK for the four
post-gate-1 reason codes. A gate-1 refusal may carry one — the evaluator
currently passes it — and is never required to, because it never consulted it.

---

## Identity and history

**36. Idempotency key?** `(workspace_id, input_signal_id,
target_proposition_key, derivation_rule_version, semantic_equivalence_basis_id)`.

**Every column is `NOT NULL`**, which is the whole point after probe C: the
constraint actually constrains, with no expression index and no sentinel value.

**37. Rule-version behaviour?** A new row. Replaying a different rule is
different reasoning, exactly as for `claim_derivations`.

**38. Basis-version behaviour?** A new row, decided explicitly rather than
defaulted. The basis is an input to gate 1 and the first thing the evaluator
reads, so changing it changes what was evaluated. The cost is stated: one
Signal-target pair can accumulate several refusal rows, which is what an
append-only audit is.

**39-40. Append-only? Supersession?** Append-only, **no supersession column**. No
consumer needs one: each row names its rule version and basis, so *which
reasoning stood when* is answerable from the rows and their timestamps, and a
supersession flag would require somebody to decide what supersedes what.

**41-42. UNKNOWN then later SUPPORTS?** **Nothing happens to the refusal.** It is
not marked false, superseded, deleted or rewritten. It is a true historical
statement: under that basis, this system could not establish that the Signal
bears on the proposition. The later SUPPORTS writes a Claim, a revision, a
derivation and Evidence, and leaves the refusal alone.

**43. Duplicate replay?** One row. The evaluator is deterministic, and a test
replays a real refusal and compares the whole derivation draft.

**44. System error versus domain refusal?** Only `NOT_APPLICABLE` and `UNKNOWN`
are refusals. A database error, a missing contract object or an unexpected
exception belongs with `signal_derivation_runs` and `claim_interpretation_runs`.
The result CHECK is a partial guard; the real enforcement is that the persistence
command accepts an `EvaluationOutcome` and nothing else, so an exception has no
shape to be filed as.

---

## What was not touched

**45. Multi-tenant?** `workspace_id`, composite tenant foreign keys, RLS enabled
and forced with a `tenant_isolation` policy — exactly what migration 0034 does.

**46. Retention?** No foreign key to any expiring table.

**47-51. Changes to `origin_detail`, `claim_derivations`, the Claim schema, the
Evidence schema, the trigger?** **None.** All five untouched, and the validator
re-reads migration 0034 and `validate_claims.py` to confirm the facts the design
rests on are still true.

**52. Evidence re-evaluation policy?** `REPORT_NO_AUTOMATIC_WRITE`, carried
forward from Mission 1.52 unchanged.

**53-54. Migration? Canonical rows?** None, and none. Re-measured after every
test run: claims 43, revisions 44, evidence 57, derivations 0, thresholds 0,
INFERRED 0, opportunities 1, assessments 4, workspaces `dev` and `dev-other`, and
`research.proposition_evaluation_refusals` does not exist.

**55-62. Requests, models, reliability, calibration, Opportunity,
Problem-Family?** 0 research-data requests, 0 documentation requests, 0 metadata
requests, 0 model calls, 0 embeddings, 0 new assessments, no calibration,
Opportunity 1 / 1 / 7 unchanged, `REFERENCE_PROFILE_V1` still `UNCALIBRATED`,
Problem-Family still `PARKED`.

**63. Workspace isolation?** `dev` and `dev-other` before and after; the probe
workspace was created and removed inside its own script, and the pytest leak
check reports the database unchanged across 28 tenant tables and 17 global ones.

---

## Tests

**64. Bare-python?** **1354**, all passing, nine suites. 41 new design tests live
in the evaluator package, because that package owns the outcomes and reason codes
being proved and already has `sros_claim_model` on its path for
`proposition_key`.

**65. Pytest?** **3201**, all passing. 15 new live-database tests in
`services/nlp/python`.

**One of them needed a fix that is worth recording.** The evidence-requirement
trigger is `DEFERRABLE INITIALLY DEFERRED`, so it fires at COMMIT — and the
rollback fixture never commits. The first version of the test passed the INSERT
and reported a pass for a rule that never ran. `SET CONSTRAINTS ALL IMMEDIATE`
is what makes it a test, and it matters even more for the HYPOTHESIS control,
which would otherwise pass vacuously: an unforced deferred check never fires, so
an exempt claim and a forbidden one look identical.

**A second collection trap was caught before it mattered.** The new pytest
classes were first named `TheEvidenceRequirement…`, and pytest collected **zero
tests** without saying so. The repository's convention is a `Test` prefix;
renaming took collection from 0 to 15.

**66. Validator probes?** **66 deliberate violations, 66 caught**, and the real
record still validates. Each is a claim the record could plausibly have made and
must not: a hash-only target, a nullable column inside the identity key, a reason
code the evaluator never raises, the expiring run log selected, a supersession
column, a counter that moved, the next mission reported as started.

**67. Counters after?** Unchanged, listed above.

---

## Outcome

**68. ADR number?** **ADR-038 — A refusal is not a derivation of a Claim, and
needs its own record.** Accepted.

**69. Primary outcome?** `INPUT_KEYED_REFUSAL_PROVENANCE_MODEL_SELECTED`.

**70. Recommended next mission?** **Mission 1.54 — Refusal Provenance Schema V1.**
Implement only the frozen contract: one additive table, its constraints, its
identity key and its RLS, with a real DELETE fixture proving a refusal survives
interpretation-run expiry. It must also prove that a workspace deletion removes
refusals without a deferred-constraint failure — the trap migration 0034 hit and
found only by running it.

Still open:

- `TARGET_DESCRIPTOR_VERSION_DELIBERATELY_ABSENT` is an operator-reviewable
  deviation from the brief's §31.
- Whether a gate-1 refusal should carry the threshold registration it never
  consulted. The constraint permits it and never requires it; deciding it would
  have meant changing the evaluator, which §24 forbade.
- Policy D is decided and still unimplemented: no conflict report exists.
- No threshold registration exists, so no proposition has a bound frozen before a
  measurement was retrieved.

**Mission 1.54 was not started.**

---

## Artifacts

- `docs/architecture/adr/ADR-038-refusal-provenance-binding.md`
- `docs/data/refusal-derivation-binding-baseline-v1.json` — the frozen §0 baseline
- `docs/data/refusal-derivation-binding-design-v1.json` — the record
- `docs/data/refusal-derivation-binding-design-v1.md` — generated
- `infrastructure/scripts/render_refusal_provenance_design.py` — renderer and
  validator, wired into CI
- `packages/inferred-claim-evaluator/python/tests/test_refusal_provenance_design.py`
- `services/nlp/python/tests/test_refusal_binding_schema_facts.py`
