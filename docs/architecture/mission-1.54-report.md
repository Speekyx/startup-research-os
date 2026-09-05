# Mission 1.54 — Refusal Provenance Schema V1

**Primary outcome: `REFUSAL_PROVENANCE_SCHEMA_IMPLEMENTED`.**

ADR-038's refusal record exists as exactly one additive table, and the three
properties the design rests on are proven against real rows rather than
inspected as DDL: a refusal outlives the interpretation run that produced it, a
Signal it cites cannot be silently purged, and deleting the whole tenant still
commits. **0 production refusal rows, 0 existing rows changed, and no evaluator,
Claim, Evidence or trigger was touched.**

---

## Setup

**1. Was Mission 1.53 merged?** Yes — PR
[#96](https://github.com/Speekyx/startup-research-os/pull/96), merged at
`cdbca46`, verified against Git.

**2. Exact main commit?** `cdbca46`, local and origin identical, tree clean.

**3. Dedicated branch?** `sprint-1/mission-1.54`, cut fresh from main.

**4. Baseline counters?** RawRecords 325, NormalizedRecords 325, Signals 33,
Claims 43, ClaimRevisions 44, Evidence 57, INFERRED **0**, assessments 4,
independence groups 0, thresholds **0**, derivations **0**, Opportunity 1 / 1 / 7,
embeddings 0, sources 29, `scoring.scores` ABSENT, workspaces `dev` and
`dev-other`, refusal table **ABSENT**. Every one matches the brief.

**5. Migration head before?** `0034_deterministic_derivation_provenance`.

**6. New migration number?** **0035**, `0035_refusal_provenance.sql`, creating
exactly one table.

---

## The table

**7. Exact name?** `research.proposition_evaluation_refusals`. §30 offered
`claim_evaluation_refusals` and said the name was not mandatory; `claim_` is
refused because no Claim is evaluated and none exists — this row is precisely
the case where there is none.

**8. Exact columns?** Seventeen: `id`, `workspace_id`, `input_signal_id`,
`input_observed_claim_id`, `target_proposition_key`, `target_proposition_facts`,
`derivation_rule_id`, `derivation_rule_version`, `evaluator_version`,
`semantic_equivalence_basis_id`, `threshold_registration_id`,
`evaluation_result`, `reason_code`, `interpretation_kind`, `model_version`,
`rationale`, `created_at`. Three are nullable: the observed Claim, the threshold
registration and the model version.

**9-10. Primary key and composite key?** `PRIMARY KEY (id)` plus
`UNIQUE (workspace_id, id)`. The second is semantically vacuous and added for the
reason 0034 added it to both of its tables: every workspace-scoped table here
carries it, so a future composite tenant-safe FK needs no migration that looks
like a schema change.

**11-14. Identity?** `(workspace_id, input_signal_id, target_proposition_key,
derivation_rule_version, semantic_equivalence_basis_id)` — the rule version and
the basis both included, and **every member NOT NULL**.

That last property is the one that matters. Mission 1.53 proved on PostgreSQL
16.4 that a UNIQUE containing a nullable column admits unlimited duplicates: it
accepted three identical rows with a NULL revision id and refused the duplicate
the moment the column was populated. Here no COALESCE sentinel and no expression
index were needed, because the basis is NOT NULL on a measured contract fact —
`SemanticEquivalenceDecision` refuses a blank basis id for **every** verdict,
including UNKNOWN.

---

## The descriptor

**15-18. Representation?** `target_proposition_key TEXT NOT NULL` plus
`target_proposition_facts JSONB NOT NULL` — key and exact preimage, in the
vocabulary `research.claims.proposition_facts` already uses, discriminator
`proposition`. The key recomputes: a test reads both halves back out of JSONB and
runs the real `proposition_key`.

**19. Enforcement boundary?** Named honestly: **the database stores both halves
and does not reimplement the Python canonicalisation to check them against each
other.** Consistency is the producer's, and the test proves the part that could
have silently failed — that a JSONB round trip preserves the preimage well enough
for the key to recompute. Reversed input order recomputes the same key, because
JSONB drops key order and `canonical_json` sorts keys, so the two cancel.

**20-22. Descriptor schema version?** **None**, and the operator's decision is
recorded with the narrowed rationale: the descriptor follows the canonical Claim
proposition-facts contract, which carries no version of its own, so creating one
only for refusals would establish a second representation convention for the same
semantic object. **`derivation_rule_version` is producer and rule provenance and
is not declared to be a descriptor schema version.** If the canonical
representation ever gains a global version, refusal descriptors adopt that same
mechanism; no refusal-only version namespace may be created.

### One stricter check was considered and rejected on a measurement

Requiring every fact **value** to be a JSON string was enforceable —
`NOT jsonb_path_exists(facts, 'strict $.* ? (@.type() != "string")')` — and it was
**rejected**, because only **37 of 43** live Claims would have passed. The six
that would not are the `source_reported_procurement_value_contrast` family, whose
`notice_ids` and `classification_codes` are arrays of strings: legitimate cohort
identity. Adding it would have made the table unable to represent a refusal about
a family the repository already holds, which is what Mission 1.53 §32 said a
schema must not do.

**This corrects the design record.**
`refusal-derivation-binding-design-v1.json` lists among its JSON safeguards
*"Values are flat strings, as on every live Claim"*. That is true of 37 of 43 and
not of all. Recorded here rather than edited in place, because the 1.53 record is
a historical artifact.

**And the first version of that expression silently missed the case it was written
for.** In the default lax jsonpath mode `$.*` unwraps arrays, so `["1"]` tested as
the string `"1"` and passed. `strict` was required to see it at all.

---

## Vocabularies

**23-26. Result, reason and pairing CHECKs?** All three. The result vocabulary is
`NOT_APPLICABLE` and `UNKNOWN` and nothing else — so `SUPPORTS`, `CONTRADICTS`,
`NEUTRAL`, and equally `ERROR`, `FAILED`, `EXCEPTION` and `TIMEOUT`, are
structurally unrepresentable, and there is no generic status column that could
acquire one. The reason vocabulary is the seven codes the evaluator raises, read
from its `_refuse` calls via the AST. **Zero invented, zero renamed, and the
drift check ran before the migration was written**: seven codes and seven
pairings, compared set-for-set and pair-for-pair.

The pairing CHECK is what stops a row asserting a shape no gate produces —
`UNKNOWN` with `UNIT_MISMATCH`, say. Constraining the two vocabularies separately
would admit all fourteen combinations.

**The pairing constraint subsumes the two vocabulary constraints and they are
kept anyway.** When only the reason code is wrong, a violation named
`..._reason_code_check` says so, where a pairing violation leaves a reader
comparing two columns to find which one was the typo.

**27. Basis nullable?** No. `NOT NULL`, on the measured contract fact above.

**28-30. Threshold conditionality?** Nullable, and required by CHECK for the four
post-gate-1 codes. A gate-1 refusal may carry one and is never required to: the
evaluator currently passes a registration to every refusal, and forbidding it
here would mean changing evaluator behaviour to satisfy a constraint. Its
presence never means gate 1 consulted it — the reason code says that.

---

## Foreign keys and retention

**31-33. FKs and delete actions?** Workspace **CASCADE**, immediate. Signal,
observed Claim and threshold registration all **NO ACTION DEFERRABLE INITIALLY
DEFERRED**, following 0034 exactly and for the same reason in both directions.

**34-36. Any FK to a run table, a ClaimRevision or Evidence?** None, and the
check is structural rather than by column name: even a nullable FK would make the
dependency available for somebody to rely on later.

**37-39. Isolated deletes?** Deleting the cited Signal alone raises
`ForeignKeyViolation`. So does deleting a threshold registration a refusal
judged. The optional observed Claim follows the same durable-provenance shape.

**40-42. Retention fixture?** Real rows: a real interpretation run with a
populated `expires_at`, a real input row naming the same Signal, and a refusal
inserted independently. The run was deleted through the ordinary mechanism.
**Interpretation inputs 1 → 0. The refusal survived.**

**43-45. Workspace deletion?** A real disposable workspace created and destroyed
inside the test, holding a Signal, a threshold registration, an observed Claim
and a refusal citing all three. `DELETE FROM core.workspaces` then COMMIT:
**committed, no deferred-constraint failure, refusal removed with the tenant.**

Both halves are tested because Mission 1.51 found that an undeferred NO ACTION
fails during tenant cascade ordering. A design that traded one guarantee for the
other would pass half a suite.

---

## Tenancy

**46. Cross-workspace?** `ForeignKeyViolation` for the Signal, the threshold
registration and the observed Claim. Structural, through composite
`(workspace_id, id)` foreign keys, so a cross-tenant reference is impossible
rather than merely filtered.

**47-50. RLS?** Enabled and forced, one `tenant_isolation` policy with
`USING (workspace_id = core.current_workspace_id())` and the same `WITH CHECK`,
matching 0034's convention exactly. Tenant A reads **0** of tenant B's refusals;
tenant A writing one raises `InsufficientPrivilege`.

---

## History

**51-56. Append-only?** Yes. No `superseded_at`, no `is_current`, no
`replaces_id`. An exact replay is refused as a duplicate; a different rule
version, a different reviewed basis and a different target each create a second
historical row. A later SUPPORTS under a new basis leaves an earlier UNKNOWN
entirely alone, which is the transition ADR-038 froze.

---

## What was not touched

**57-64.** `origin_detail`, `claim_derivations` (including its NOT NULL and its
identity key), `threshold_registrations`, the Claims schema, the Evidence schema,
the evidence-requirement trigger and `validate_claims.py` are all unchanged. **No
repository or evaluator integration was added** — §35 keeps that for the next
mission, and the constraint proofs go through direct SQL on the existing
fixtures.

**65-70. Anything created?** No INFERRED Claim, no Evidence, no threshold row,
no derivation row, **0 production refusal rows**. Re-measured after every test
run: claims 43, revisions 44, evidence 57, signals 33, derivations 0, thresholds
0, refusals 0, opportunities 1, assessments 4, runs 12, inputs 64, INFERRED 0,
workspaces `dev` and `dev-other`.

**71-78. Requests, models, reliability, calibration, Opportunity,
Problem-Family?** 0 research-data requests, 0 documentation requests, 0 metadata
requests, 0 model calls, 0 embeddings, 0 new assessments, no calibration,
Opportunity 1 / 1 / 7 unchanged, `REFERENCE_PROFILE_V1` still `UNCALIBRATED`,
Problem-Family still `PARKED`.

**79. Workspace state?** `dev` and `dev-other` before and after; the cascade
proof's own workspace was created and removed inside its test, and the leak check
reports the database unchanged.

---

## Tests

**80-82.** **1354** bare-`python` tests, **3273** pytest tests, all passing. The
migration applies forward on the existing deployment (0034 → 0035, verified) and
from empty in CI's integration job, which builds the database from every
migration in order.

**83-84. Table counts?** The leak check went **28 → 29** tenant tables and
`validate_schema` reports **46**, both picking the new table up automatically.
Neither number is a hard-coded CI invariant. Two pinned lists did need extending —
the gateway suite's expected-table set and its RLS policy coverage — and that is
what a new table costs: the schema is code, so pinning it is legitimate.

**85. Validator probes?** **70 deliberate violations, 70 caught**, and the real
record still validates.

**Two of them were false positives in my own validator, and both are the same
recurring shape.** The identity-key check first matched the **comment** quoting
the other table's key, and the untouched-trigger check first matched the
paragraph headed *WHAT IS NOT TOUCHED*. That is `testing-strategy.md` §23: a scan
failing on the prose that explains the rule. Repaired structurally — anchor to
the named constraint, and scan the statements rather than the comments — never by
loosening the rule.

### A defect I wrote in Mission 1.53 and hit in Mission 1.54

Mission 1.53 re-pointed a database test that pinned a migration **head**, with
the reasoning that pinning a head makes every later mission edit an unrelated
check. In the same mission I then wrote a head pin into 1.53's own validator
**and** into its own test suite. Both went red the moment 0035 existed.

Both are now the property they were protecting: **0034 is still present**,
because every claim ADR-038 makes about `claim_derivations` reasons about the
table 0034 created. Recorded rather than quietly fixed, because writing the same
defect in the same mission that corrected it is worth knowing about.

Two smaller ones, for completeness: a fixture created a Claim with no revision
and hit `claims_current_revision_fkey`, and a per-line `# noqa` landed **inside**
five multi-line SQL strings because ruff reports S608 on the line that opens the
f-string. The second corrupted five queries and was repaired with one module-level
suppression carrying its reason.

---

## Outcome

**86. Primary outcome?** `REFUSAL_PROVENANCE_SCHEMA_IMPLEMENTED`.

**87. Recommended next mission?** **Mission 1.55 — Deterministic Evaluation
Persistence Orchestration V1.** Implement the persistence split ADR-038 named: a
directional outcome writes Claim, ClaimRevision, claim_derivation and Evidence in
one transaction; a refusal writes one refusal row and nothing else. Synthetic and
disposable workspaces first.

It must prove that each path commits atomically and leaves nothing behind on
failure, that a refusal write cannot create a Claim, Evidence or a threshold
mutation as a side effect, that the evaluator's `EvaluationOutcome` maps onto
exactly one path with no third branch, that a replayed refusal is idempotent
through the command rather than only at the constraint, and that policy D's
conflict report exists or its persistence boundary is frozen.

Still open:

- Policy D is decided and still unimplemented: no conflict report exists.
- No threshold registration exists, so no proposition has a bound frozen before a
  measurement was retrieved.
- Whether a gate-1 refusal should carry the threshold registration it never
  consulted. The constraint permits it and never requires it.
- The first canonical INFERRED Claim waits until the orchestrator is proven
  transactionally.

**Mission 1.55 was not started.**

---

## Artifacts

- `infrastructure/db/migrations/0035_refusal_provenance.sql`
- `docs/data/refusal-provenance-schema-v1.json` — the record
- `docs/data/refusal-provenance-schema-v1.md` — generated
- `infrastructure/scripts/render_refusal_provenance_schema.py` — renderer and
  validator, wired into CI
- `services/nlp/python/tests/test_refusal_provenance_schema.py` — 72 database
  tests
