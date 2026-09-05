# Refusal Provenance Schema V1

**Mission 1.54 — Refusal Provenance Schema V1 — recorded 2026-09-05. Governed by ADR-038; implements the contract frozen in refusal-derivation-binding-design-v1.**

> **This document is GENERATED.** Edit
> `refusal-provenance-schema-v1.json` and re-run
> `infrastructure/scripts/render_refusal_provenance_schema.py`.

## Primary outcome — `REFUSAL_PROVENANCE_SCHEMA_IMPLEMENTED`

ADR-038's refusal record exists as exactly one additive table, constrained, tenant-safe and retention-safe. The three properties the design rests on are proven against real rows rather than inspected as DDL: a refusal outlives the interpretation run that produced it, a Signal it cites cannot be silently purged, and deleting the whole tenant still commits. **0 production refusal rows, 0 existing rows changed, and no evaluator, Claim, Evidence or trigger was touched.**

*This mission resolves SQL-level detail only. Every field, every vocabulary and the identity key come from ADR-038 unchanged; what is decided here is types, constraint expressions, FK actions, index shape and migration ordering.*

## Migration

Head before **0034_deterministic_derivation_provenance**, new migration **0035**, `infrastructure/db/migrations/0035_refusal_provenance.sql`, creating **1** table.

Additive only **True**, backfill **False**, data migration **False**, deletions **False**, existing rows changed **0**.

*The refusals that ephemeral run logs once held expired on schedule. Reconstructing them would be inventing history, and the table would open with rows nobody can trace to an evaluation.*

## The table

### `research.proposition_evaluation_refusals`

No Claim is evaluated and none exists; this row is precisely the case where there is none. Mission 1.10's rule that a kind is named for its shape, and that a name may not carry an interpretation, applies to a table as much as to a record kind.

Primary key `PRIMARY KEY (id)`, composite tenant key `UNIQUE (workspace_id, id)`. Semantically vacuous, since `id` is already unique alone. Added for the same reason 0034 added it to both of its tables: every workspace-scoped table in this schema carries it, so a future composite tenant-safe FK needs no migration that looks like a schema change.

| group | column | type | null | answers |
| --- | --- | --- | --- | --- |
|  | `id` | uuid | no | the row |
|  | `workspace_id` | uuid | no | which workspace |
|  | `input_signal_id` | uuid | no | which Signal |
|  | `input_observed_claim_id` | uuid | yes | which optional OBSERVED Claim |
|  | `target_proposition_key` | text | no | which candidate proposition, by identity |
|  | `target_proposition_facts` | jsonb | no | which candidate proposition, readably |
|  | `derivation_rule_id` | text | no | which rule |
|  | `derivation_rule_version` | text | no | which rule version |
|  | `evaluator_version` | text | no | which evaluator version |
|  | `semantic_equivalence_basis_id` | text | no | which reviewed basis |
|  | `threshold_registration_id` | uuid | yes | which threshold registration, if any |
|  | `evaluation_result` | text | no | what happened |
|  | `reason_code` | text | no | why |
|  | `interpretation_kind` | text | no | by which procedure |
|  | `model_version` | text | yes | which model, where one was used |
|  | `rationale` | text | no | the human-readable explanation, and the authority for nothing |
|  | `created_at` | timestamp with time zone | no | when |

**Deliberately absent:**

- `claim_revision_id` — There is no revision. Its absence is the entire point of the table.
- `claim_id` — `input_observed_claim_id` is an optional INPUT, not the target. A column called `claim_id` would read as the Claim this refusal is about, and there is none.
- `evidence_id` — A refusal produces no Evidence and is not aggregation input.
- `measurement_value` — Recoverable from the Signal, and not part of the proposition (ADR-036). Storing it would make this table a second authority for a number the Signal owns.
- `superseded_at / is_current / replaces_id` — Append-only. A later SUPPORTS under a new basis does not make an earlier UNKNOWN false.
- `any descriptor schema version` — The operator's accepted deviation, below.

## Identity

`workspace_id`, `input_signal_id`, `target_proposition_key`, `derivation_rule_version`, `semantic_equivalence_basis_id`

**Mission 1.53 proved on PostgreSQL 16.4 that a UNIQUE containing a nullable column admits unlimited duplicates: three identical rows were accepted with a NULL revision id, and the same table refused the duplicate the moment the column was populated. Every member here is NOT NULL, so the guarantee is real rather than nominal, and no COALESCE sentinel or expression index was needed.**

| replay | result |
| --- | --- |
| same inputs | **REFUSED as a duplicate** |
| new rule version | **a second historical row** |
| new reviewed basis | **a second historical row** |
| new target proposition | **a second historical row** |

## Foreign keys

| columns | references | on delete | why |
| --- | --- | --- | --- |
| `workspace_id` | `core.workspaces (id)` | **CASCADE** | Deleting an entire tenant removes its refusal audit rows. That is a different act from purging one referenced Signal. |
| `(workspace_id, input_signal_id)` | `nlp.signals (workspace_id, id)` | **NO ACTION DEFERRABLE INITIALLY DEFERRED** | Every Signal row carries a populated expires_at, so CASCADE would let a retention purge take the audit with it. DEFERRABLE moves the check to COMMIT, where a tenant cascade has removed both sides and a lone purge has not. |
| `(workspace_id, input_observed_claim_id)` | `research.claims (workspace_id, id)` | **NO ACTION DEFERRABLE INITIALLY DEFERRED** | Same durable-provenance shape as 0034, and optional: the Signal is the load-bearing witness. |
| `(workspace_id, threshold_registration_id)` | `research.threshold_registrations (workspace_id, id)` | **NO ACTION DEFERRABLE INITIALLY DEFERRED** | Same. A registration a refusal judged cannot be deleted out from under it. |

No foreign key to `research.claim_interpretation_runs`, `research.claim_interpretation_inputs`, `research.claim_revisions`, `scoring.evidence`.

## Check constraints

| constraint | rule | why |
| --- | --- | --- |
| `proposition_evaluation_refusals_result_check` | `evaluation_result IN ('NOT_APPLICABLE','UNKNOWN')` | Structurally incapable of holding a directional decision, and equally incapable of holding ERROR, FAILED, EXCEPTION or TIMEOUT. There is no generic status column that could acquire one. |
| `proposition_evaluation_refusals_reason_code_check` | `the seven codes the evaluator raises` | Read from the evaluator's own `_refuse` calls. None invented, none renamed. |
| `proposition_evaluation_refusals_result_reason_pairing_check` | `(reason_code, evaluation_result) IN the seven frozen pairs` | Constraining the two vocabularies separately would admit all fourteen combinations, so a row could assert UNKNOWN with UNIT_MISMATCH, a shape no gate produces. |
| `proposition_evaluation_refusals_threshold_conditional_check` | `the four post-gate-1 reason codes require a registration` | A refusal that reached the registration gate names what it judged. The three equivalence refusals return before it. |
| `proposition_evaluation_refusals_interpretation_kind_check` | `DETERMINISTIC or MODEL_DERIVED` | Mirrors 0016 and 0034. |
| `proposition_evaluation_refusals_model_version_pairing_check` | `DETERMINISTIC implies no model version; MODEL_DERIVED requires one` | So a deterministic refusal cannot quietly acquire a model. |
| `proposition_evaluation_refusals_key_not_blank_check` | `length(btrim(target_proposition_key)) > 0` | Mirrors claims_proposition_key_not_blank_check. |
| `proposition_evaluation_refusals_facts_object_check` | `jsonb_typeof(target_proposition_facts) = 'object'` | Mirrors claims_proposition_facts_object_check. |
| `proposition_evaluation_refusals_facts_nonempty_check` | `target_proposition_facts <> '{}'` | Mirrors claims_proposition_facts_nonempty_check. |
| `proposition_evaluation_refusals_facts_discriminator_check` | `target_proposition_facts ? 'proposition'` | One check STRICTER than research.claims, deliberately: a refusal's facts are the ONLY record of what was refused, so the descriptor has to say which kind of proposition it describes. Measured before being required -- 43 of 43 live Claims carry it. |
| `proposition_evaluation_refusals_rationale_present_check` | `length(btrim(rationale)) > 0` | Mirrors claim_derivations_rationale_present_check. |

*The pairing constraint subsumes the two vocabulary constraints. They are kept anyway because when only the reason code is wrong, a violation named `..._reason_code_check` says so, where a pairing violation leaves a reader comparing two columns to find which one was the typo.*

### One stricter check was considered and rejected on a measurement

**require every value in target_proposition_facts to be a JSON string** — enforceable as `NOT jsonb_path_exists(facts, 'strict $.* ? (@.type() != "string")')`, and rejected.

Measured: **37 of 43** live Claims would have passed. The 6 that would not are the `source_reported_procurement_value_contrast` family, whose `notice_ids` and `classification_codes` are arrays of strings, which are legitimate cohort identity.

It would have made this table unable to represent a refusal about a proposition family the repository already holds, which is exactly what Mission 1.53 §32 said a schema must not do. The genericity is inherited from the Claim fact vocabulary and must not be narrowed here.

**A correction to the design record.** `refusal-derivation-binding-design-v1.json` lists among its JSON safeguards `Values are flat strings, as on every live Claim`. That is TRUE OF 37 OF 43 AND NOT OF ALL. The safeguard the schema actually enforces is the discriminator, the object type and non-emptiness; flatness was never enforceable without excluding a real family. Recorded here rather than corrected in place, because the 1.53 record is a historical artifact.

*The first expression used the default lax jsonpath mode, which UNWRAPS arrays, so `["1"]` tested as the string `"1"` and passed. `strict` was required to see it at all. Recorded because a guard that silently misses the case it was written for is worse than none.*

## Reason codes

Read from `packages/inferred-claim-evaluator/python/sros_inferred_claim_evaluator/threshold_state.py` by the second positional argument of every `_refuse(...)` call, read from the AST. Invented here: **0**. Drift against ADR-038: **NONE. Seven codes and seven pairings, compared set-for-set and pair-for-pair before the migration was written.**

| reason code | result | gate | registration required |
| --- | --- | --- | --- |
| `SEMANTIC_MISMATCH` | NOT_APPLICABLE | 1 | no |
| `EQUIVALENCE_NOT_ESTABLISHED` | UNKNOWN | 1 | no |
| `EQUIVALENCE_DIMENSIONS_INCOMPLETE` | UNKNOWN | 1 | no |
| `THRESHOLD_REGISTRATION_MISMATCH` | NOT_APPLICABLE | 2 | **yes** |
| `UNIT_MISMATCH` | NOT_APPLICABLE | 2 | **yes** |
| `TIME_BOUND_MISMATCH` | NOT_APPLICABLE | 2 | **yes** |
| `PREREGISTRATION_TIMING_INCONSISTENT` | UNKNOWN | 3 | **yes** |

## The descriptor

    target_proposition_key TEXT NOT NULL plus target_proposition_facts JSONB NOT NULL

Vocabulary: the same as research.claims.proposition_facts. Discriminator: `proposition`.

**Enforcement boundary.** The database stores both halves and does NOT reimplement the Python canonicalisation to check them against each other. Consistency is enforced by the producer and proven by a test that reads both back from JSONB and recomputes `proposition_key(facts)`. Naming that boundary matters: claiming the database verifies the key would be claiming a guarantee nothing provides.

*JSONB does not preserve key order, and `canonical_json` sorts keys, so the two facts cancel rather than compound. Proven by inserting the facts in reversed order and recomputing the same key.*

### `TARGET_DESCRIPTOR_VERSION_DELIBERATELY_ABSENT` — OPERATOR_ACCEPTED

The descriptor follows the canonical Claim proposition-facts contract, which carries no schema version of its own. Creating one only for refusals would establish a second representation convention for the same semantic object.

**`derivation_rule_version` is not a descriptor version.** It is producer and rule provenance. Mission 1.53 reasoned that it also pins the emitted fact set; the operator accepted the outcome and narrowed the reasoning, and this record carries the narrowed version.

**Future rule.** If the canonical proposition-facts representation gains an explicit global schema version, refusal descriptors adopt that SAME mechanism. No refusal-only version namespace may be created.

## Row level security

Enabled **True**, forced **True**, policy `tenant_isolation` with `USING (workspace_id = core.current_workspace_id())` and `WITH CHECK (workspace_id = core.current_workspace_id())`.

## Proofs

**Retention.** REAL rows in a disposable workspace: a real interpretation run with a populated expires_at, a real input row naming the same Signal, and a refusal inserted independently. The run was deleted through the ordinary mechanism and both were re-read.

Interpretation inputs **1 → 0**; refusal survived **True**.

**Signal, deleted alone.** DELETE the Signal a refusal cites, on its own → **ForeignKeyViolation**.

Every Signal carries a populated expires_at. A retention purge must fail loudly rather than take the audit with it.

**Threshold registration, deleted alone.** DELETE a threshold registration a refusal judged, on its own → **ForeignKeyViolation**.

**Workspace deletion.** A REAL disposable workspace created and destroyed inside the test, holding a Signal, a threshold registration, an observed Claim and a refusal citing all three. `DELETE FROM core.workspaces` then COMMIT.

Committed **True**, deferred-constraint failure **False**, refusal removed **True**.

*Mission 1.51 found that an undeferred NO ACTION fails during tenant cascade ordering. A design that traded tenant deletion for referent protection would pass half a suite, so both are exercised.*

**Cross-workspace.** Signal **ForeignKeyViolation**, threshold **ForeignKeyViolation**, observed Claim **ForeignKeyViolation**.

composite (workspace_id, id) foreign keys, so a cross-tenant reference is impossible rather than merely filtered

**RLS.** Tenant A reads tenant B's refusals: **0**. Tenant A writes one: **InsufficientPrivilege**.

**Key recomputation.** read target_proposition_key and target_proposition_facts back from the row and recompute through the real claim-model — matches **True**, reversed input order matches **True**, mutating one fact changes it **True**.

## Table counts

Leak-check tenant tables **28 → 29**, `validate_schema` **46**, tables created **1**.

The leak check and validate_schema both pick the new table up automatically; neither number is hard-coded in a CI invariant. The two pinned lists that DID need extending are the gateway suite's expected-table set and its RLS policy coverage, and extending them is what a new table costs -- the schema is code, so pinning it is legitimate.

## The validator was probed

**70 of 70 deliberate violations caught**, and the real record still validates.

Each violation is a claim this record could plausibly have made and must not: a table name the migration does not create, a nullable identity member, a provenance FK that cascades or is not deferrable, a reason code the evaluator never raises, a descriptor schema version, a workspace deletion that did not commit, a counter that moved, the next mission reported as started.

*The identity-key check first matched the COMMENT quoting the other table's key, and the untouched-trigger check first matched the paragraph headed WHAT IS NOT TOUCHED. Both are `testing-strategy.md` §23: a scan failing on the prose that explains the rule. Repaired structurally -- anchor to the named constraint, and scan the statements rather than the comments -- never by loosening the rule.*

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
| `claim_interpretation_runs` | 12 | 12 |
| `claim_interpretation_inputs` | 64 | 64 |

Research-data requests **0**, documentation requests **0**, metadata requests **0**.

Model calls **0**, embeddings **0**, profile **UNCALIBRATED**, Problem-Family **PARKED**, production refusal rows **0**, evaluator modified **False**.

Untouched:

- `claims_schema` — untouched
- `claim_revisions_schema` — untouched
- `evidence_schema` — untouched
- `claim_derivations_schema` — untouched, including its NOT NULL and its identity key
- `threshold_registrations_schema` — untouched
- `interpretation_run_tables` — untouched
- `require_evidence_for_generated_claim` — untouched, and no INFERRED exemption added
- `validate_claims_py` — untouched
- `origin_detail` — untouched
- `evaluator` — untouched
- `evidence_reevaluation_policy` — REPORT_NO_AUTOMATIC_WRITE

STOP conditions honoured:

- no evaluator orchestration implemented
- no canonical EvaluationOutcome persistence
- no INFERRED Claim created
- no Evidence created
- no production refusal row created
- claim_derivations unchanged
- claim_revision_id not made nullable
- evidence-requirement trigger unchanged
- no INFERRED trigger exemption
- no NEUTRAL refusal representable
- evaluator semantics unchanged
- gate ordering unchanged
- policy D conflict reports not implemented
- no source selected
- no observations acquired
- no reliability assigned
- no calibration
- no Scores created
- Opportunity unchanged
- no model called
- no embeddings created
- Problem-Family still PARKED
- Mission 1.55 not started

## Next mission

**Mission 1.55 — Deterministic Evaluation Persistence Orchestration V1** — Implement the persistence split ADR-038 named: a directional outcome writes Claim, ClaimRevision, claim_derivation and Evidence in one transaction; a refusal writes one refusal row and nothing else. Synthetic and disposable workspaces first.

It must prove:

- each path commits atomically, and a failure on either leaves nothing behind
- a refusal write cannot create a Claim, Evidence or a threshold mutation as a side effect
- the evaluator's EvaluationOutcome maps onto exactly one path with no third branch
- a replayed refusal is idempotent through the command rather than only at the constraint
- policy D's conflict report exists, or its exact persistence boundary is frozen

Still open:

- policy D is decided and still unimplemented: no conflict report exists
- no threshold registration exists, so no proposition has a bound frozen before a measurement was retrieved
- whether a gate-1 refusal should carry the threshold registration it never consulted; the constraint permits and never requires it
- the first canonical INFERRED Claim must wait until the orchestrator is proven transactionally

*Mission 1.55 was not started.*

