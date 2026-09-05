# Refusal Derivation Binding Design V1

**Mission 1.53 — Refusal Derivation Binding Design V1 — recorded 2026-09-05. Governed by ADR-038; consumes ADR-036, ADR-037 and migration 0034.**

> **This document is GENERATED.** Edit
> `refusal-derivation-binding-design-v1.json` and re-run
> `infrastructure/scripts/render_refusal_provenance_design.py`.

## Primary outcome — `INPUT_KEYED_REFUSAL_PROVENANCE_MODEL_SELECTED`

A refusal is durably recorded in its own append-only record, keyed on the INPUT witness, the CANDIDATE TARGET proposition, the derivation rule version and the reviewed equivalence basis. It names no ClaimRevision, creates no Claim, produces no Evidence, and requires no change to `research.claim_derivations`, to `research.require_evidence_for_generated_claim`, or to any existing schema. **No migration was created.**

*Mission 1.52 preferred this shape, which is a reason to test it harder rather than to adopt it. Option B was analysed to the point where its exact cost could be measured, and it failed on two of the ten selection criteria for reasons that only a live probe could establish.*

## The conflict, re-proved

A disposable workspace `refusal-probe`, created and removed inside one script. Canonical state read before and after: claims 43, claim_derivations 0, evidence 57, workspaces dev and dev-other.

| probe | attempted | result | mechanism |
| --- | --- | --- | --- |
| **A** | INSERT an INFERRED claim plus revision with no Evidence | **REFUSED** | research.require_evidence_for_generated_claim |
| **A2 control** | the same INSERT with claim_type HYPOTHESIS | **ACCEPTED, then rolled back deliberately** |  |
| **B** | INSERT a claim_derivation with claim_revision_id NULL | **REFUSED** | migration 0034 declares claim_revision_id NOT NULL |
| **C** | three rows differing in nothing, on a TEMP table mirroring `claim_derivations_identity_key`, with claim_revision_id NULL | **ALL THREE ADMITTED** | the same table refused a duplicate when claim_revision_id was populated |

**A first attempt was wrong.** The first run used `origin = 'AUTOMATED'`, which is not a member of `claims_origin_check`, so it was refused by the WRONG constraint and proved nothing about the evidence requirement. Reported here because a refusal on an unrelated constraint reads exactly like the refusal you were hoping for.

**The control matters.** Without this control, probe A shows only that something refused. With it, the refusal is attributable to the exemption list rather than to anything incidental.

**Probe C decides Option B.** This is the measurement Mission 1.52 did not make, and it decides Option B. `claim_derivations_identity_key` is UNIQUE (workspace_id, claim_revision_id, input_signal_id, derivation_rule_version), and PostgreSQL treats NULLs as distinct by default — so the moment claim_revision_id is nullable, the table's only idempotency guarantee stops applying to exactly the rows Option B exists to add. Refusal idempotency would be nominal rather than real, and nothing would report it.

**Probe D refutes Option C.** Option C is refuted from live state rather than from Mission 1.50's report.

## What migration 0034 already anticipated

`claim_derivations_threshold_required_check`

    CHECK ((evaluation_result = ANY (ARRAY['NOT_APPLICABLE','UNKNOWN'])) OR (threshold_registration_id IS NOT NULL))

Migration 0034 already makes the threshold registration OPTIONAL exactly for the two refusal results, and its `evaluation_result` CHECK already admits all four. So the table was shaped in the expectation that refusals would live in it, and a different constraint — the NOT NULL on claim_revision_id — made that impossible.

*It establishes that the intent was reasonable, not that the table can carry it. The two constraints were written in one migration and they disagree, which is the finding rather than a tie-breaker. What Option B would need is not the removal of one NOT NULL but the addition of a proposition descriptor and a second idempotency key — at which point it is Option A inside a table whose name says otherwise.*

## What a refusal record is

A durable audit record of a deterministic attempt to determine whether source-native measurement M bears on candidate proposition P, where the result was NOT_APPLICABLE or UNKNOWN, and therefore no canonical Evidence relation was established and no canonical Claim needs to exist because of the attempt.

It is not: a Claim, Evidence, a reliability assessment, an Opportunity finding, an execution log, a system-error record.

**The bound worth stating.** The evaluator only refuses pairs somebody has ALREADY reviewed: `evaluate` requires a SemanticEquivalenceDecision, and its constructor requires a non-blank basis id. A pair nobody has reviewed produces no evaluation at all, and therefore no refusal. So the refusal store answers *what did we try and decline*, never *what did we never consider*.

- A directional derivation answers: *Why does Signal S support or contradict existing ClaimRevision R?*
- A refusal answers: *Why was Signal S NOT attached to candidate proposition P?*

The subject of the first is a revision that exists. The subject of the second is a proposition that does not. They are not the same persistent entity, and the fact that both came out of one function call is not a reason to store them in one table.

## The twenty audit questions

|  | question | answered by |
| --- | --- | --- |
| 1 | Which workspace? | `workspace_id` |
| 2 | Which Signal? | `input_signal_id` |
| 3 | Which optional OBSERVED Claim? | `input_observed_claim_id` |
| 4 | Which candidate proposition? | `target_proposition_key + target_proposition_facts` |
| 5 | Which metric definition? | `target_proposition_facts.metric_definition_id` |
| 6 | Which subject? | `target_proposition_facts.canonical_subject_id` |
| 7 | Which time bound? | `target_proposition_facts.time_bound` |
| 8 | Which population or geography? | `target_proposition_facts.population_or_geography` |
| 9 | Which unit? | `target_proposition_facts.unit` |
| 10 | Which threshold and operator? | `target_proposition_facts.threshold_operator + threshold_value` |
| 11 | Which threshold registration, if any? | `threshold_registration_id (nullable, conditional)` |
| 12 | Which semantic-equivalence basis? | `semantic_equivalence_basis_id` |
| 13 | Which derivation rule? | `derivation_rule_id` |
| 14 | Which rule version? | `derivation_rule_version` |
| 15 | Which evaluator version? | `evaluator_version` |
| 16 | Which interpretation kind? | `interpretation_kind` |
| 17 | Which result? | `evaluation_result` |
| 18 | Why was it refused? | `reason_code` |
| 19 | When? | `created_at` |
| 20 | Repeated under another rule version? | `a second row; rule version is part of the identity key` |

## Option matrix

| criterion | A separate record | B nullable binding | C run logs |
| --- | --- | --- | --- |
| semantic coherence | **STRONG** | **WEAK** | **MEDIUM** |
| no fake claim | **STRONG** | **STRONG** | **STRONG** |
| target proposition auditability | **STRONG** | **FAIL** | **WEAK** |
| retention durability | **STRONG** | **STRONG** | **FAIL** |
| preserves claim derivation invariant | **STRONG** | **FAIL** | **STRONG** |
| no trigger weakening | **STRONG** | **STRONG** | **STRONG** |
| schema minimality | **MEDIUM** | **MEDIUM** | **STRONG** |
| queryability | **STRONG** | **MEDIUM** | **WEAK** |
| append only history | **STRONG** | **STRONG** | **WEAK** |
| idempotency clarity | **STRONG** | **FAIL** | **WEAK** |
| multi tenant safety | **STRONG** | **STRONG** | **STRONG** |
| future evaluator integration | **STRONG** | **MEDIUM** | **WEAK** |

*A: SCHEMA_MINIMALITY is MEDIUM and not WEAK: it adds one table and changes none.*

*B: SCHEMA_MINIMALITY is only MEDIUM because B is not actually smaller once it works: it needs target_proposition_key, target_proposition_facts, reason_code, a second partial unique index and three conditional CHECKs.*

*C: RETENTION_DURABILITY FAILs on live measurement: 12 of 12 runs carry expires_at and the inputs FK is ON DELETE CASCADE. Retention was not redesigned to rescue it.*

**Option A.** SELECTED. Passes all ten selection criteria.

**Option B.** REJECTED on TARGET_PROPOSITION_AUDITABILITY and IDEMPOTENCY_CLARITY. `claim_derivations` identifies its proposition only THROUGH claim_revision_id, so with that NULL the row cannot say what was refused; and probe C proved the existing identity key stops constraining the moment the column is nullable. Repairing both means adding a proposition descriptor, a reason code and a second idempotency key to a table whose name and stated meaning are about actual ClaimRevisions — Option A inside the wrong table.

**Option C.** REJECTED on RETENTION_DURABILITY, from live state rather than from a report.

## The selection criteria

|  | criterion | met | how |
| --- | --- | --- | --- |
| 1 | no fabricated Claim | **yes** | the entity has no claim_id and no claim_revision_id |
| 2 | full candidate target auditable | **yes** | key plus recomputable preimage in the Claim fact vocabulary |
| 3 | durable after run expiry | **yes** | no foreign key to either interpretation-run table |
| 4 | no Evidence for refusal | **yes** | no evidence_id, and the result CHECK admits no direction |
| 5 | append-only historical audit | **yes** | no supersession column, insert-only |
| 6 | workspace-safe | **yes** | workspace_id, composite tenant FKs, RLS enabled and forced |
| 7 | idempotent | **yes** | five-column UNIQUE with every column NOT NULL |
| 8 | evaluator integration clear | **yes** | the directional/refusal split is explicit and needs no evaluator change |
| 9 | existing OBSERVED/INFERRED semantics preserved | **yes** | nothing existing is altered |
| 10 | no silent trigger weakening | **yes** | the trigger is untouched and needs no exemption, because no Claim is created |

## The candidate target proposition

**T1_PLUS_T2 — key plus its exact preimage, in the vocabulary research.claims already uses.**

    target_proposition_key TEXT NOT NULL, target_proposition_facts JSONB NOT NULL

This is not a new representation. All 43 live Claims carry `proposition_key` AND `proposition_facts`, paired by `claims_proposition_facts_paired_check`, and `proposition_key()` is sha256 over `canonical_json(facts)`. The refusal record stores the same pair, produced by the same function over the same fact vocabulary — so a refused candidate and the Claim it may later become are comparable by key, which is what makes the UNKNOWN-then-SUPPORTS transition traceable at all.

**The key is verifiable rather than trusted.** A reader recomputes proposition_key(target_proposition_facts) and compares. The stored key is therefore verifiable rather than trusted — the property Mission 1.51 gave `proposition_facts` when it called it the preimage of the key.

Measured: **43** live Claims carry both a key and its preimage, and the discriminator key is `proposition` on **43** of them. The discriminator is `proposition`, not `proposition_kind`. The evaluator already emits `"proposition": target.proposition_kind`, so no vocabulary divergence exists. This was checked because a divergence here would silently prevent a refusal key from ever equalling its eventual Claim key.

Rejected:

- **T2 alone** — A key without its preimage identifies a proposition nobody can read. §3 says a hash alone is insufficient unless the preimage is durably recoverable, and for a refusal there is no Claim row to recover it from.
- **T3 candidate-proposition registry** — A durable non-Claim target entity is Claims before Claims. It would need identity, lifecycle and governance of its own, and the first question anyone would ask is how it differs from a Claim. Strong presumption against, and nothing here requires it.
- **T4 threshold registration plus partial fields** — REJECTED ON A MEASURED FACT rather than on taste. Three of the seven live reason codes — SEMANTIC_MISMATCH, EQUIVALENCE_NOT_ESTABLISHED, EQUIVALENCE_DIMENSIONS_INCOMPLETE — refuse at gate 1, BEFORE the registration is consulted. T4 therefore fails exactly on the refusals that are most common and most informative.

### Why this is not an untyped dump

- The vocabulary is the one `research.claims.proposition_facts` already uses, not a new one.
- Serialization is `canonical_json`, which is deterministic and already governs the Claim key.
- The key is recomputed from the facts and compared, so a mismatched pair is detectable.
- Constraints mirror the Claim table: object-typed, non-empty, and key-and-facts present together.
- Values are flat strings, as on every live Claim; no nested structure and no prose.
- No field inside the descriptor is load-bearing for anything except identity.

**A declared deviation — `OPERATOR_REVIEWABLE_DEVIATION`.** §31 lists a canonical schema version among the safeguards. NOT included, and flagged rather than quietly dropped. `derivation_rule_version` already pins which fact set was emitted: `target_proposition_facts()` lives in the rule module, so any change to the fact vocabulary IS a rule-version change. A separate descriptor version would be a second authority for one fact, which is the pattern this repository refuses — calibration eligibility is derived rather than stored for the same reason, and Mission 1.42a refused a second confidence field on the same argument.

*Cost if that reasoning is wrong:* If the fact vocabulary ever changes WITHOUT a rule-version change, a reader could not tell which shape a descriptor uses. That would be a rule-versioning defect rather than a descriptor defect, and the implementation mission should assert the coupling with a test rather than add the column.

## The frozen entity

Proposed name **`research.proposition_evaluation_refusals`**. §30 suggested `claim_evaluation_refusals` and said the name is not mandatory. `claim_` is refused here because no Claim is evaluated and none exists — the row is precisely the case where there is no Claim. Mission 1.10's rule that a kind is named for its shape, and that a name may not carry an interpretation, applies to a table as much as to a record kind.

| group | field | type | null | answers |
| --- | --- | --- | --- | --- |
| IDENTITY | `id` | UUID | no | the row |
| IDENTITY | `workspace_id` | UUID | no | Q1 |
| INPUT | `input_signal_id` | UUID | no | Q2 |
| INPUT | `input_observed_claim_id` | UUID | yes | Q3 |
| TARGET | `target_proposition_key` | TEXT | no | Q4 |
| TARGET | `target_proposition_facts` | JSONB | no | Q4-Q10 |
| RULE | `derivation_rule_id` | TEXT | no | Q13 |
| RULE | `derivation_rule_version` | TEXT | no | Q14 |
| RULE | `evaluator_version` | TEXT | no | Q15 |
| EQUIVALENCE | `semantic_equivalence_basis_id` | TEXT | no | Q12 |
| THRESHOLD | `threshold_registration_id` | UUID | yes | Q11 |
| OUTCOME | `evaluation_result` | TEXT | no | Q17 |
| OUTCOME | `reason_code` | TEXT | no | Q18 |
| PROCEDURE | `interpretation_kind` | TEXT | no | Q16 |
| PROCEDURE | `model_version` | TEXT | yes | pairs with interpretation_kind, as on claim_derivations |
| EXPLANATION | `rationale` | TEXT | no | human-readable only, never the authority for a structured fact |
| TIME | `created_at` | TIMESTAMPTZ | no | Q19 |

**Deliberately absent:**

- `claim_revision_id` — There is no revision. Its absence is the entire point of the entity.
- `claim_id` — Same, one level up. A refusal that named a Claim would imply the Claim exists.
- `evidence_id` — A refusal produces no Evidence. Mission 1.51 refused an evidence pointer on claim_derivations for a related reason.
- `measurement_value` — Deliberated and REJECTED. The measurement is recoverable from input_signal_id, and storing it would make the refusal record a second authority for a number the Signal already owns. It also is not part of the proposition, by ADR-036.
- `superseded_at / is_current` — Append-only. §16 and §17: a later SUPPORTS does not make an earlier UNKNOWN false.
- `interpretation_confidence` — It describes how faithfully a WORDING states what Signals showed. A refusal produces no wording and no Claim, so the field would have no referent.

**Constraints:**

| constraint | rule | why |
| --- | --- | --- |
| `refusal_result_check` | `evaluation_result IN ('NOT_APPLICABLE','UNKNOWN')` | §11. SUPPORTS, CONTRADICTS and NEUTRAL are structurally unrepresentable here, so a directional result cannot be filed as a refusal by a caller passing a string. |
| `refusal_reason_code_check` | `reason_code IN the seven frozen codes` | Result says WHAT, reason code says WHY, and a free-text reason would put the why back into prose. |
| `refusal_threshold_conditionality_check` | `reason_code IN ('THRESHOLD_REGISTRATION_MISMATCH','UNIT_MISMATCH','TIME_BOUND_MISMATCH','PREREGISTRATION_TIMING_INCONSISTENT') implies threshold_registration_id IS NOT NULL` | §14. A refusal that reached the registration gate must name the registration it judged. A gate-1 refusal MAY carry one — the evaluator currently passes it — but is not required to, because it never consulted it. |
| `refusal_facts_object_check` | `jsonb_typeof(target_proposition_facts) = 'object' AND target_proposition_facts <> '{}'` | Mirrors claims_proposition_facts_object_check and claims_proposition_facts_nonempty_check. |
| `refusal_model_version_pairing_check` | `DETERMINISTIC implies model_version IS NULL; MODEL_DERIVED implies NOT NULL` | Mirrors claim_derivations_model_version_pairing_check exactly. |
| `refusal_rationale_present_check` | `length(btrim(rationale)) > 0` | Mirrors claim_derivations_rationale_present_check. |
| `refusal_identity_key` | `UNIQUE (workspace_id, input_signal_id, target_proposition_key, derivation_rule_version, semantic_equivalence_basis_id)` | Every column is NOT NULL, so the constraint actually constrains — which probe C proved is not automatic. |

**Foreign keys:**

| column | references | on delete |
| --- | --- | --- |
| `workspace_id` | `core.workspaces(id)` | **CASCADE** |
| `(workspace_id, input_signal_id)` | `nlp.signals(workspace_id, id)` | **NO ACTION DEFERRABLE INITIALLY DEFERRED** |
| `(workspace_id, input_observed_claim_id)` | `research.claims(workspace_id, id)` | **NO ACTION DEFERRABLE INITIALLY DEFERRED** |
| `(workspace_id, threshold_registration_id)` | `research.threshold_registrations(workspace_id, id)` | **NO ACTION DEFERRABLE INITIALLY DEFERRED** |

No foreign key to `research.claim_interpretation_runs`, `research.claim_interpretation_inputs`, `research.claim_revisions`, `scoring.evidence`.

ENABLE and FORCE, with a tenant_isolation policy, exactly as migration 0034 does for both of its tables.

## Reason codes

Read from `packages/inferred-claim-evaluator/python/sros_inferred_claim_evaluator/threshold_state.py`. Invented here: **0**.

| reason code | result | gate | registration required |
| --- | --- | --- | --- |
| `SEMANTIC_MISMATCH` | NOT_APPLICABLE | 1 | no |
| `EQUIVALENCE_NOT_ESTABLISHED` | UNKNOWN | 1 | no |
| `EQUIVALENCE_DIMENSIONS_INCOMPLETE` | UNKNOWN | 1 | no |
| `THRESHOLD_REGISTRATION_MISMATCH` | NOT_APPLICABLE | 2 | **yes** |
| `UNIT_MISMATCH` | NOT_APPLICABLE | 2 | **yes** |
| `TIME_BOUND_MISMATCH` | NOT_APPLICABLE | 2 | **yes** |
| `PREREGISTRATION_TIMING_INCONSISTENT` | UNKNOWN | 3 | **yes** |

The result answers WHAT happened and drives the contract — no Evidence, no Claim. The reason code answers WHY and drives the audit. The rationale is human-readable and is the authority for nothing.

## The equivalence basis

Nullable: **False**. MEASURED from the contract rather than assumed: `SemanticEquivalenceDecision.__post_init__` refuses a blank `basis_id` for EVERY verdict, including UNKNOWN. So no evaluation can occur without one, and no honest representation of an absent basis is needed.

**An unreviewed pair produces no decision object, so `evaluate` is never called and no refusal exists. The store therefore cannot answer *what did we never look at*, and must not be read as if it could.**

## Idempotency

Key: `workspace_id`, `input_signal_id`, `target_proposition_key`, `derivation_rule_version`, `semantic_equivalence_basis_id`.

**Probe C proved that a UNIQUE containing a nullable column admits unlimited duplicates on PostgreSQL 16.4. Every column here is NOT NULL, so the guarantee is real rather than nominal, and no expression index or sentinel value is required.**

- Same inputs replayed: IDEMPOTENT — one row.
- Different rule version: A NEW row. Replaying a different rule is different reasoning, exactly as for claim_derivations.
- Different basis: A NEW row. The reviewed basis is an INPUT to gate 1, and the evaluator's first act is to read its verdict. Changing it changes what was evaluated, so it is a new historical evaluation and not an update to an old one. Recording it as the same refusal would mean overwriting the reasoning that stood while the old basis stood.

*Cost stated:* One Signal-target pair can accumulate several refusal rows over time. That is the intended behaviour of an append-only audit, and the count of rows is never a measure of anything epistemic.

*The Signal is in the key and owns its value. Including the value would fork the identity when a source revised a figure, which is the defect ADR-036 keeps out of proposition identity.*

## Append-only, and the UNKNOWN-then-SUPPORTS transition

Supersession column: **False**. No consumer needs one. A reader orders refusals by created_at, and each row names the rule version and basis that produced it, so *which reasoning stood when* is answerable without a marker. A supersession flag would additionally require somebody to decide what supersedes what, which is a judgement nothing here is entitled to make.

- **T0** — Signal S evaluated against candidate P under basis B1 → UNKNOWN → refusal row U persisted.
- **T1** — A new reviewed basis B2 establishes EQUIVALENT. Re-evaluation → SUPPORTS.
- T1 writes: `research.claims (INFERRED)`, `research.claim_revisions`, `research.claim_derivations`, `scoring.evidence`
- **What happens to the refusal: NOTHING. It is not marked false, not superseded, not deleted, and not rewritten into a SUPPORTS.**

U is a true historical statement: under basis B1, this system could not establish that S bears on P. A later basis does not make that false; it makes it superseded in practice, which is a different thing and is legible from the two rows and their timestamps.

## A refusal is not a failure

Domain refusal: `NOT_APPLICABLE`, `UNKNOWN`. System failure: database error, missing contract object, programming error, unexpected exception.

System failures are NOT refusal provenance and must never be written here. The result CHECK is a partial guard; the real enforcement is that the persistence command accepts an EvaluationOutcome and nothing else, so an exception has no shape to be filed as.

*nlp.signal_derivation_runs and research.claim_interpretation_runs already hold execution records, and a failure belongs with them.*

## Evaluator integration

Evaluator modified: **False**.

    EvaluationOutcome → SUPPORTS/CONTRADICTS → Claim, ClaimRevision, claim_derivation, Evidence (one transaction). NOT_APPLICABLE/UNKNOWN → refusal provenance only (one transaction).

Each path commits atomically and independently. A refusal write must never create a Claim, Evidence or a threshold mutation as a side effect, and it cannot: the refusal entity has no foreign key to any of them except the optional registration it only reads.

*Gate-1 refusals pass the threshold registration to `_refuse`, so `DerivationDraft.threshold_registration_id` is populated even for refusals that never consulted it. The conditional constraint above permits that and never requires it, so no evaluator change is needed. Whether a gate-1 refusal SHOULD carry it is a small question for the implementation mission, and it was not decided here by changing code §24 says not to change.*

## Generic or family-specific

**GENERIC, with one family-specific optional foreign key.** The descriptor is `proposition_facts` in the vocabulary all 43 live Claims already use across seven proposition kinds, so nothing about the entity is THRESHOLD_STATE-shaped. The only family-specific field is `threshold_registration_id`, which is nullable and conditionally required by reason code — so another proposition family simply never uses it and never trips the constraint.

*No abstraction was added for families that do not exist. The generality is inherited from a representation the repository already had rather than designed for hypothetical futures.*

## Queryability

*Show me every evaluation attempt that did not become Evidence.*

    SELECT * FROM research.proposition_evaluation_refusals — one table, no text scanning, no heuristic comparison of two tables.

§23. If the answer required diffing claim_derivations against scoring.evidence, refusals would be inferred rather than recorded, and an inference is not an audit.

## The validator was probed

**66 of 66 deliberate violations caught**, and the real record still validates.

Each violation is a claim this record could plausibly have made and must not: a hash-only target, a nullable column inside the identity key, a reason code the evaluator never raises, the ephemeral run log selected, a supersession column, a counter that moved, the next mission reported as started.

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
| `reliability_assessments` | 4 | 4 |
| `independence_groups` | 0 | 0 |
| `opportunities` | 1 | 1 |
| `opportunity_revisions` | 1 | 1 |
| `opportunity_evidence_links` | 7 | 7 |
| `embeddings` | 0 | 0 |
| `sources` | 29 | 29 |

Research-data requests **0**, documentation requests **0**, metadata requests **0**.

Model calls **0**, embeddings **0**, profile **UNCALIBRATED**, Problem-Family **PARKED**, migration created **False**, refusal table created **False**.

STOP conditions honoured:

- no migration created
- no refusal table created
- claim_revision_id not made nullable
- trigger exemptions unchanged
- INFERRED not exempted from the evidence requirement
- no INFERRED Claim created
- no Evidence created
- no evaluator output persisted canonically
- no standing Evidence direction modified
- no data acquired
- no sources discovered
- no ReliabilityAssessment created
- no calibration
- no Scores created
- Opportunity unchanged
- no model called
- no embeddings created
- Problem-Family still PARKED
- Mission 1.54 not started

## Next mission

**Mission 1.54 — Refusal Provenance Schema V1** — Implement ONLY the frozen refusal persistence contract: one additive table, its constraints, its identity key and its RLS, with a real DELETE fixture proving a refusal survives interpretation-run expiry. No evaluator-to-canonical persistence yet.

It must prove:

- a refusal row survives deletion of every interpretation run in its workspace
- the identity key actually constrains, replayed with identical inputs
- a different rule version and a different basis each create a new row
- the result CHECK refuses SUPPORTS, CONTRADICTS and NEUTRAL
- proposition_key recomputed from the stored facts equals the stored key
- a workspace deletion removes refusals without a deferred-constraint failure, which is the trap migration 0034 hit

Still open:

- TARGET_DESCRIPTOR_VERSION_DELIBERATELY_ABSENT is an operator-reviewable deviation from §31
- whether a gate-1 refusal should carry the threshold registration it never consulted
- policy D is decided and still not implemented: no conflict report exists
- no threshold registration exists, so no proposition has a bound frozen before a measurement was retrieved

*Mission 1.54 was not started. The design is frozen and no migration was written.*

