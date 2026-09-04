# Deterministic Derivation Provenance Schema V1

**Mission 1.51 — recorded 2026-09-04. Governed by ADR-037.**

> **This document is GENERATED.** Edit
> `deterministic-derivation-provenance-schema-v1.json` and re-run
> `infrastructure/scripts/render_derivation_provenance_schema.py`.

## Primary outcome — `DETERMINISTIC_DERIVATION_PROVENANCE_SCHEMA_IMPLEMENTED`

Both additive records exist, are constrained, are migrated and are tested, including the retention proof the whole verdict rests on. No evaluator was built and no INFERRED Claim exists.

*ADR-037 already governs the semantics. This mission resolved only the schema-level details it deliberately left open -- table names, SQL types, FK actions, constraints, supersession semantics and the equivalence-basis representation -- so it ships an implementation record rather than a second ADR that would restate a decision already made.*

## Migration

Head before **0033_correspondence_evidence_locator**, new migration **0034**, `infrastructure/db/migrations/0034_deterministic_derivation_provenance.sql`.

Additive only **True**, backfill **False**, data migration **False**, deletions **False**, existing rows changed **0**.

*The repository has no down migrations and none was invented (ADR-008: plain numbered SQL with a core.schema_migrations ledger).*

## The two tables

### `research.threshold_registrations`

A bound, frozen with its provenance.

- primary key: `id`
- tenant key: `UNIQUE (workspace_id, id)`
- columns: `id`, `workspace_id`, `threshold_operator`, `threshold_value`, `unit`, `metric_definition_id`, `scope_subject_id`, `scope_population`, `scope_time_bound`, `provenance_status`, `recorded_at`, `recorded_by`, `provenance_reference`, `norm_issuer`, `norm_document_id`, `norm_version`, `norm_section`, `created_at`
- idempotency: `(workspace_id, metric_definition_id, scope_subject_id, scope_population, scope_time_bound, threshold_operator, threshold_value, provenance_status)`

It INCLUDES provenance_status deliberately, so one logical bound may be registered once as PREREGISTERED and once as EXTERNAL_NORM without being merged. ADR-037 §3 forbids equating threshold provenance with Claim identity, and a key that omitted the status would do exactly that.

*The table has no proposition_key, no claim_id and no calibration_eligible column, and a test asserts all three absences.*

### `research.claim_derivations`

One deterministic evaluation: one rule, one Signal, one ClaimRevision, one result.

- primary key: `id`
- tenant key: `UNIQUE (workspace_id, id)`
- columns: `id`, `workspace_id`, `claim_revision_id`, `input_signal_id`, `input_observed_claim_id`, `derivation_rule_id`, `derivation_rule_version`, `evaluator_version`, `measurement_value`, `threshold_registration_id`, `evaluation_result`, `semantic_equivalence_basis_id`, `interpretation_kind`, `model_version`, `rationale`, `created_at`
- idempotency: `(workspace_id, claim_revision_id, input_signal_id, derivation_rule_version)`

It INCLUDES derivation_rule_version and must. Evidence keys on (workspace, claim, signal) because Mission 1.41 REMOVED the procedure version so a bump could not INSERT a duplicate; a derivation record MUST be distinct per rule version, because replaying a different rule is different reasoning about the same relation.

## Foreign keys

| column | references | on delete | why |
| --- | --- | --- | --- |
| `workspace_id` | `core.workspaces (id)` | **CASCADE** | Deleting a tenant removes its data. That is tenant deletion, not retention. |
| `(workspace_id, claim_revision_id)` | `research.claim_revisions (workspace_id, id)` | **NO ACTION DEFERRABLE INITIALLY DEFERRED** | Composite so a derivation can never cite a revision in another workspace. |
| `(workspace_id, input_signal_id)` | `nlp.signals (workspace_id, id)` | **NO ACTION DEFERRABLE INITIALLY DEFERRED** | Every row of nlp.signals carries a populated expires_at, so CASCADE would let a future retention purge delete the reasoning along with its input -- the exact defect ADR-037 found in the interpretation-run tables. |
| `(workspace_id, input_observed_claim_id)` | `research.claims (workspace_id, id)` | **NO ACTION DEFERRABLE INITIALLY DEFERRED** | Optional context; the Signal is the load-bearing input. |
| `(workspace_id, threshold_registration_id)` | `research.threshold_registrations (workspace_id, id)` | **NO ACTION DEFERRABLE INITIALLY DEFERRED** | A directional result names what it compared against, and that bound must not vanish under it. |

**Neither new table references research.claim_interpretation_runs or research.claim_interpretation_inputs, and a test reads pg_constraint to assert it structurally rather than by inspection. Those two tables are unmodified.**

### The deferrable finding

**What happened.** The FKs were first written as plain ON DELETE NO ACTION, on the reasoning that NO ACTION is checked at the end of the statement while RESTRICT is checked immediately, so a workspace cascade would still succeed. That was wrong in a way only the database could show: an UNDEFERRED NO ACTION is checked at the end of each CASCADING statement, and the cascade that removes claim_revisions runs before the one that removes the derivations citing them. Every committing test's teardown failed.

**The fix.** DEFERRABLE INITIALLY DEFERRED, which moves the check to COMMIT.

**Why it is correct rather than convenient.** At COMMIT a workspace deletion has removed both sides, so tenant deletion works. A lone Signal purge still has a derivation pointing at it, so it still fails. Both guarantees hold, and neither was traded for the other.

*One committing test had already written a derivation before its teardown failed, leaving a disposable `signal-probe` workspace behind. It was inspected before anything was deleted: the row was confined to that test workspace and the canonical dev workspace was untouched at 33 Signals, 43 Claims and 44 revisions. It was removed through the same mechanism the failed teardown would have used, and the migration was then rolled back and re-applied so the deployment matches the migration file exactly.*

## Vocabularies

| threshold provenance status | calibration eligible |
| --- | --- |
| `PREREGISTERED` | **yes** |
| `SOURCE_NATIVE` | **yes** |
| `EXTERNAL_NORM` | **yes** |
| `POST_HOC` | **no** |
| `UNKNOWN` | **no** |

*There is no calibration_eligible column. It is fully determined by provenance_status, and two authorities for one fact eventually disagree.*

Evaluation results: `SUPPORTS`, `CONTRADICTS`, `NOT_APPLICABLE`, `UNKNOWN`.

**NEUTRAL is deliberately absent.** A NEUTRAL row would assert that an observation bears on the Claim without bearing either way, which is a positive finding and a different thing from not knowing. UNKNOWN must never become it.

*DETERMINISTIC requires model_version NULL; MODEL_DERIVED requires one. The same pairing migration 0016 enforces on claims, so a deterministic derivation cannot quietly acquire a model.*

## Status-specific constraints

| constraint | rule |
| --- | --- |
| `threshold_registrations_reference_required_check` | PREREGISTERED, SOURCE_NATIVE and EXTERNAL_NORM must carry a non-empty provenance_reference. POST_HOC and UNKNOWN need none, because their whole content is that the origin is late or unestablished, and demanding a citation would invite a fabricated one. |
| `threshold_registrations_external_norm_check` | EXTERNAL_NORM must identify issuer, document, version and section. A norm that cannot be identified is not a norm. |
| `threshold_registrations_norm_fields_scoped_check` | Norm fields may be present ONLY for EXTERNAL_NORM, so a POST_HOC bound cannot borrow an issuer's authority by filling one in. |
| `claim_derivations_threshold_required_check` | SUPPORTS and CONTRADICTS must name a threshold registration. NOT_APPLICABLE and UNKNOWN stop before the comparison and need none. |
| `claim_derivations_rationale_present_check` | A blank rationale is refused. It is an explanation for a reader, and an empty one is not. |

## Preregistration

    threshold_registrations.recorded_at < observation.retrieved_at

**Not `published_at`.** The bias preregistration guards against is the analyst's, and an analyst can only be influenced by data that reached them. A figure public for years before this system retrieved it was not known to whoever froze the bound.

**Not commit time.** A commit records when a file changed, not when a measurement became available to the decision process.

**The limit is retained.** The database proves that this system did not yet hold the measurement. It does not prove that no human knew it, and the column comment says so, so a future calibration mission cannot read PREREGISTERED as the stronger claim.

*This mission stores the timestamp and does not compare it. The comparison belongs to the evaluator.*

## Binding and versioning

Binds to **CLAIM_REVISION**. A threshold proposition can stay the same while the rule version, the inputs or the rationale change. Binding to the Claim would let a later derivation silently rewrite the reasoning behind an earlier revision.

Supersession model: **APPEND_ONLY**. There is no supersession column and no is_current flag. Rule v2 re-evaluating the same Signal against the same revision creates a SECOND row and leaves the first intact, because two rule versions disagreeing is a finding worth seeing rather than a conflict to resolve by overwriting. It satisfies §16's four requirements with no machinery: old reasoning never disappears, the latest never rewrites history, contradictory outcomes across versions stay inspectable side by side, and the rows are ordered by created_at.

*No `evidence_id`.* No evidence_id column. Evidence is already uniquely identified by (workspace, claim, signal), so a pointer would be a second authority -- and adding one would suggest a single authoritative derivation exists when append-only deliberately permits several. Whether a re-evaluation under a new rule version may CHANGE an existing Evidence row is evaluator behaviour, and the schema supports either answer without prejudging it.

## Semantic-equivalence basis

**Option B**: an opaque durable identifier stored on the derivation row (semantic_equivalence_basis_id TEXT NOT NULL). Third table created: **False**.

ADR-037 §13 required only that a future derivation point to a stable, auditable basis. Judging that two publishers measure the same quantity is a documentary judgement a person makes, and the canonical subject registry already establishes the pattern of a reviewed artifact referenced by exact identifier. A table would be a broad equivalence subsystem this mission was told not to build, and §13 says prefer minimum schema.

*Whether the authoritative basis becomes a table or stays a reviewed document is still open, and the column does not prejudge it: an identifier resolves against either.*

## Tenancy

- RLS enabled **True**, forced **True**
- policy: `tenant_isolation FOR ALL USING/WITH CHECK workspace_id = core.current_workspace_id()`, style copied from migration 0029, unchanged
- Every FK is composite on (workspace_id, ...), so a cross-workspace reference is structurally impossible rather than merely filtered.
- The repository filter is layer one, RLS is layer two, the composite FK is layer three, and none replaces another (ADR-005, ADR-012).

*The pytest suite's global leak check reports 28 tenant tables where it reported 26, having picked both up automatically.*

## What was not touched

- `research_claims` — **unchanged**
- `scoring_evidence` — **unchanged**
- `origin_detail` — **unchanged in schema, semantics and every existing value**
- `claim_interpretation_runs` — **unchanged**
- `claim_interpretation_inputs` — **unchanged**

**One addition to an existing table.** `ALTER TABLE research.claim_revisions ADD CONSTRAINT claim_revisions_workspace_id_key UNIQUE (workspace_id, id)`

A composite FK needs a matching unique constraint in its target, and claim_revisions had PRIMARY KEY (id) and UNIQUE (workspace_id, claim_id, revision) but not this one. SEMANTICALLY VACUOUS: id is already unique on its own, so (workspace_id, id) cannot constrain anything new, and no existing row can violate it. Both other referenced tables (nlp.signals, research.claims) already carry the identical constraint, so this brings claim_revisions into line rather than inventing a pattern. Columns changed: **0**.

## What was deliberately not built

- **repository layer** — created: **False**. §27 permits one only if required to test inserts, uniqueness and constraints. The constraints are SQL, so the tests exercise them directly through the existing tenant-connection fixtures. A repository would be evaluator scaffolding, and the evaluator is the next mission's.
- **domain types** — created: **False**. §28 warns against duplicate semantic vocabularies in multiple packages. The vocabularies live in the CHECK constraints today, and a Python mirror written before the evaluator exists would be a second authority with no consumer. The owning package is decided when the evaluator is.

## Tests

`services/nlp/python/tests/test_derivation_provenance_schema.py` — **28** tests, owned by `services/nlp/python`.

*That package owns Claim persistence and already has the tenant-connection, probe-workspace and privileged-connection fixtures these need. §29 puts SQL-constraint tests with the package owning the research schema abstractions, and §40 forbids moving imports until tests happen to pass.*

**The retention proof.** Inserts a real interpretation run with a bounded expiry and a real input row naming the same Signal, inserts a durable derivation independently, DELETES the run through the ordinary mechanism, then re-reads both.

Result: The interpretation inputs cascaded to 0; the derivation survived. Asserted against real rows and a real DELETE, not against mocks.

*ADR-037's entire schema verdict rests on this distinction. If it ever fails, a Claim can again outlive the record of how it was derived.*

**The idempotency contrast.** Rule v1 and v2 over one (revision, signal) produce TWO derivation rows; the same rule version twice is refused by claim_derivations_identity_key. A companion test reads the live schema and asserts that the derivation key CONTAINS derivation_rule_version while no Evidence key contains extraction_method -- the deliberate difference Mission 1.41 created, pinned so a future evaluator cannot collapse it.

**Signal purge refused.** Deleting a Signal cited by a derivation raises ForeignKeyViolation, so retention cannot silently take the reasoning with it.

## Counters

| counter | before | after |
| --- | ---: | ---: |
| raw_records | 325 | 325 |
| normalized_records | 325 | 325 |
| signals | 33 | 33 |
| claims | 43 | 43 |
| claim_revisions | 44 | 44 |
| evidence | 57 | 57 |
| inferred_claims | 0 | 0 |
| reliability_assessments | 4 | 4 |
| reliability_basis_rows | 12 | 12 |
| independence_groups | 0 | 0 |
| opportunities | 1 | 1 |
| opportunity_revisions | 1 | 1 |
| opportunity_evidence_links | 7 | 7 |
| embeddings | 0 | 0 |
| registered_sources | 29 | 29 |
| claim_interpretation_runs | 12 | 12 |
| claim_interpretation_inputs | 64 | 64 |
| threshold_registrations | 0 | 0 |
| claim_derivations | 0 | 0 |
| scores | ABSENT | ABSENT |

Model calls **0**, embeddings **0**, Problem-Family **PARKED**, source selected **NONE**, evaluator implemented **False**, INFERRED Claim created **False**.

## Next mission

**Mission 1.52 -- Deterministic Inferred Claim Evaluator Foundation V1** — The evaluator package ADR-037 specified and this mission did not create: measurement witness, threshold lookup, equivalence gate, deterministic result, INFERRED Claim draft, derivation row, Evidence direction.

Prefer: Synthetic or already-held diagnostic data until the evaluator itself is proven.

Still open:

- whether the semantic-equivalence basis becomes a table or stays a reviewed document
- whether a re-evaluation under a new rule version may change an existing Evidence row

*Mission 1.52 was not started.*

