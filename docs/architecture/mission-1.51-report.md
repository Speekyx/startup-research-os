# Mission 1.51 — Deterministic Derivation Provenance Schema V1

**Primary outcome: `DETERMINISTIC_DERIVATION_PROVENANCE_SCHEMA_IMPLEMENTED`.**

Both additive records exist, are constrained, are migrated and are tested —
including the retention proof the whole ADR-037 verdict rests on. **No evaluator
was built, no INFERRED Claim exists, and no production row was created.**

---

## Setup

**1. Was Mission 1.50 merged?** Yes — PR #93, 12/12 SUCCESS, verified against
Git. ADR-036 and ADR-037 both Accepted; `docs/CLAUDE.md` 1.84,
`PROJECT_MANIFEST.md` 1.83.
**2. Exact main commit?** `c1e807d`, matching the brief. Tree clean.
**3. Dedicated branch?** `sprint-1/mission-1.51`.
**4. Exact baseline counters?** 325 / 325 / 33 / 43 / 44 / 57, INFERRED Claims
**0**, assessments 4, basis 12, groups 0, Opportunity 1 / 1 / 7, embeddings 0,
sources 29, `scoring.scores` ABSENT, profile UNCALIBRATED, Problem-Family PARKED.
Interpretation runs **12** and inputs **64**, measured and not modified.
**5. Migration head before?** `0033_correspondence_evidence_locator`.
**6. New migration number?** **0034**.

---

## The schema

**7. Exact table names?** `research.threshold_registrations` and
`research.claim_derivations`, following the repository's `research.` plural
snake_case convention.

**8. Threshold-registration columns?** `id`, `workspace_id`,
`threshold_operator`, `threshold_value` (NUMERIC, never float), `unit`,
`metric_definition_id`, `scope_subject_id`, `scope_population`,
`scope_time_bound`, `provenance_status`, `recorded_at`, `recorded_by`,
`provenance_reference`, `norm_issuer`, `norm_document_id`, `norm_version`,
`norm_section`, `created_at`.

**9. Derivation columns?** `id`, `workspace_id`, `claim_revision_id`,
`input_signal_id`, `input_observed_claim_id`, `derivation_rule_id`,
`derivation_rule_version`, `evaluator_version`, `measurement_value`,
`threshold_registration_id`, `evaluation_result`,
`semantic_equivalence_basis_id`, `interpretation_kind`, `model_version`,
`rationale`, `created_at`.

**10. Primary keys?** `id` on both, with `UNIQUE (workspace_id, id)` as the
composite target.

**11. Foreign keys?** Workspace on both; and from the derivation to
`claim_revisions`, `nlp.signals`, `research.claims` (optional) and
`threshold_registrations` — all **composite on `(workspace_id, …)`**, so a
cross-workspace reference is structurally impossible rather than merely filtered.

**12. FK delete actions?** Workspace **CASCADE**; every other
**`NO ACTION DEFERRABLE INITIALLY DEFERRED`**.

**13. Any CASCADE from expiring interpretation runs?** **None**, and neither new
table references `claim_interpretation_runs` or `claim_interpretation_inputs` at
all. A test reads `pg_constraint` to assert it structurally, and the validator
greps the migration for the same thing.

### The deferrable finding

The FKs were first written as plain `ON DELETE NO ACTION`, on the reasoning that
NO ACTION is checked at end of statement while RESTRICT is checked immediately,
so a workspace cascade would survive. **That was wrong in a way only the database
could show:** an undeferred NO ACTION is checked at the end of each *cascading*
statement, and the cascade removing `claim_revisions` runs before the one
removing the derivations citing them. Every committing test's teardown failed.

`DEFERRABLE INITIALLY DEFERRED` moves the check to COMMIT. At COMMIT a workspace
deletion has removed both sides, so tenant deletion works; a lone Signal purge
still has a derivation pointing at it, so it still fails. **Both guarantees hold
and neither was traded for the other.**

One committing test had already written a row before its teardown failed, leaving
a disposable `signal-probe` workspace behind. It was inspected before anything
was deleted: **the row was confined to that test workspace and the canonical dev
workspace was untouched at 33 Signals, 43 Claims and 44 revisions.** It was
removed through the mechanism the failed teardown would have used, and the
migration was then rolled back and re-applied so the deployment matches the file
exactly.

---

## Constraints

**14. Threshold status constraint?** Exactly five —
`threshold_registrations_provenance_status_check`. A sixth is refused.
**15. Evaluation result constraint?** Exactly four —
`claim_derivations_evaluation_result_check`. **NEUTRAL is deliberately absent**:
it would assert that an observation bears on the Claim without bearing either
way, which is a positive finding and a different thing from not knowing.
**16. `interpretation_kind`/`model_version` constraint?**
`claim_derivations_model_version_pairing_check` — DETERMINISTIC requires a NULL
model version, MODEL_DERIVED requires one. The same pairing migration 0016
enforces on claims, so one distinction stays in one place.

**17. Threshold idempotency key?** `(workspace_id, metric_definition_id,
scope_subject_id, scope_population, scope_time_bound, threshold_operator,
threshold_value, provenance_status)`.

**18. Derivation idempotency key?** `(workspace_id, claim_revision_id,
input_signal_id, derivation_rule_version)`.

**19. Why do the Evidence and derivation keys differ?** Evidence keys on
`(workspace, claim, signal)` because **Mission 1.41 removed** the procedure
version so a version bump could not INSERT a duplicate — Evidence identity is
epistemic. A derivation record **must** be distinct per rule version, because
replaying a different rule is *different reasoning about the same relation*. A
test reads both from the live schema and asserts the derivation key contains
`derivation_rule_version` while no Evidence key contains `extraction_method`, so
a future evaluator cannot collapse the two.

**20. Is rule version included?** Yes, in the derivation key only.
**21. Is ClaimRevision binding mandatory?** Yes, NOT NULL.
**22. Signal binding mandatory?** Yes, NOT NULL.
**23. Optional OBSERVED Claim behaviour?** Nullable. The Signal is the
load-bearing input because Evidence attaches Signal to Claim, and a derivation
must not become impossible because no source-attributed Claim happens to exist.
**24. Threshold registration relationship?** Nullable column with a CHECK
requiring it for `SUPPORTS` and `CONTRADICTS`; `NOT_APPLICABLE` and `UNKNOWN`
stop before the comparison and need none.

**25. Semantic-equivalence basis representation?** **Option B** — an opaque
durable identifier (`semantic_equivalence_basis_id TEXT NOT NULL`).
**26. Third table required?** **No.** **27. Why not?** ADR-037 §13 required only
a stable, auditable basis. Judging that two publishers measure the same quantity
is a documentary judgement a person makes, and the canonical subject registry
already establishes the pattern of a reviewed artifact referenced by exact
identifier. A table would be the broad equivalence subsystem this mission was
told not to build, and §13 says prefer minimum schema. The column does not
prejudge the later choice: an identifier resolves against either.

---

## Versioning

**28. Append-only or supersession?** **APPEND_ONLY.** **29. Exact semantics?** No
supersession column and no `is_current` flag. Rule v2 re-evaluating the same
Signal against the same revision creates a **second** row and leaves the first
intact. That satisfies §16's four requirements with no machinery: old reasoning
never disappears, the latest never rewrites history, contradictory outcomes
across versions stay inspectable side by side, and rows are ordered by
`created_at`.

**30. Can old derivations disappear?** **No.** **31. Can a Claim outlive its
derivation?** **No** — that is the property the whole table exists to guarantee.

**32. Retention proof result?** **Passes.** **33. Interpretation-run deletion
test?** A real run with a bounded expiry and a real input row naming the same
Signal are inserted, a durable derivation is inserted independently, the run is
**deleted**, and both are re-read: the interpretation inputs cascaded to **0**,
the derivation **survived**. Real rows and a real DELETE, not mocks.

A companion test proves the other direction: deleting a Signal cited by a
derivation raises `ForeignKeyViolation`, so retention cannot silently take the
reasoning with it.

---

## Preregistration

**34. PREREGISTERED semantics preserved?** Yes.
**35. `recorded_at` retained?** Yes — the timestamp the rule compares.
**36. `published_at` avoided?** Yes. The bias guarded against is the analyst's,
and an analyst can only be influenced by data that reached them.
**37. Human-foreknowledge limitation retained?** Yes, in the column comment: the
database proves *this system did not yet hold the measurement*, never *no human
knew it*.
**38. EXTERNAL_NORM required fields?** Issuer, document, version and section, all
enforced; and norm fields are permitted **only** for EXTERNAL_NORM, so a POST_HOC
bound cannot borrow an issuer's authority.
**39. POST_HOC represented?** Yes, distinctly. **40. UNKNOWN represented?** Yes,
distinctly.
**41. Calibration eligibility stored or derived?** **Derived.**
**42. Why?** It is fully determined by `provenance_status`, and two authorities
for one fact eventually disagree. There is no `calibration_eligible` column and
the validator refuses one.

---

## What was not touched

**43. `origin_detail` changed?** **No** — not in schema, not in semantics, not in
any of the 43 existing values.
**44. `claim_interpretation_runs` changed?** **No.**
**45. `claim_interpretation_inputs` changed?** **No.**
**46. Claims schema changed?** **No.**
**47. Evidence schema changed?** **No.**

**One addition to an existing table**, stated plainly:
`ALTER TABLE research.claim_revisions ADD CONSTRAINT
claim_revisions_workspace_id_key UNIQUE (workspace_id, id)`. A composite FK needs
a matching unique constraint in its target and that one was missing. It is
**semantically vacuous** — `id` is already unique, so `(workspace_id, id)`
constrains nothing new and no existing row can violate it — and both other
referenced tables already carry the identical constraint. **0 columns changed.**

**48. RLS policies?** `tenant_isolation FOR ALL` with `USING` and `WITH CHECK` on
`core.current_workspace_id()`, ENABLE **and** FORCE, copied unchanged from
migration 0029.
**49. Cross-workspace rejection?** Tested three ways: a derivation citing a
revision in another workspace raises `ForeignKeyViolation`; a tenant reads 0 rows
of another workspace's registrations; a tenant writing another workspace's
`workspace_id` raises `InsufficientPrivilege`.

**50. Repository/domain helpers added?** **None.** §27 permits one only if
required to test constraints, and the constraints are SQL, so the tests exercise
them directly through the existing fixtures. A repository would be evaluator
scaffolding.
**51. Any evaluator logic?** **None.**
**52. Any real INFERRED Claim?** **None.** **53. Any real Evidence?** **None.**
**54. New production rows in the new tables?** **0.**

**55. Existing row counts before/after?** All sixteen identical, verified against
a snapshot taken before the migration ran.

---

## Budget and state

**56. Research data requests?** **0.** **57. Documentation requests?** **0.**
**58. Model calls?** **0.** **59. Embeddings?** **0.**
**60. Reliability changes?** None. **61. Calibration changes?** None —
`REFERENCE_PROFILE_V1` still UNCALIBRATED.
**62. Opportunity changes?** None — 1 / 1 / 7. **63. Problem-Family?** **PARKED.**
**64. Workspace state?** 2 seeded workspaces, 0 orchestration probes. The one
stale probe workspace this mission created was documented above and removed.
**65. Zero-dependency tests?** **1244 across 8 packages**, bare `python`, run
before commit.
**66. Pytest?** **all suites passed across 9 packages**; the global leak check
reports the database unchanged across **28** tenant tables — up from 26, having
picked up both new tables automatically.
**67. Migration suite?** `validate_schema.py` passes (9 invariant groups, 45
tables); `migrate.py --plan` clean; the ledger test derives from disk and passes.

**68. Validator deliberate violations?** **25 fired, 25 caught** — a signal FK set
to CASCADE, a NO ACTION FK left undeferred, the workspace FK not cascading,
denying the expiry independence, a sixth threshold status, POST_HOC made
eligible, eligibility stored rather than derived, NEUTRAL added, the rule version
dropped from the derivation key, the provenance status dropped from the threshold
key, the threshold table storing Claim identity, preregistration compared to
`published_at`, the foreknowledge limit hidden, binding to Claim instead of
revision, old derivations allowed to disappear, a backfill declared, existing
rows changed, a third table added, an evaluator implemented, an INFERRED Claim
created, a counter moved, a source selected, model calls, Problem-Family
unparked, and an outcome outside §43.

**69. Exact canonical counters after?** Identical to question 4, plus
`threshold_registrations` **0** and `claim_derivations` **0**.
**70. Primary outcome?**
**`DETERMINISTIC_DERIVATION_PROVENANCE_SCHEMA_IMPLEMENTED`.**

---

## §45 — Next

**71. Recommended next mission?** **Mission 1.52 — Deterministic Inferred Claim
Evaluator Foundation V1.** The evaluator package ADR-037 specified and this
mission deliberately did not create: measurement witness → threshold lookup →
equivalence gate → deterministic result → INFERRED Claim draft → derivation row →
Evidence direction.

It should still prefer synthetic or already-held diagnostic data until the
evaluator itself is proven, and it must not acquire research data, select a
source, weaken `validate_claims.py` or call a model.

**Two questions remain open and are recorded as open**, not resolved in passing:
whether the semantic-equivalence basis becomes a table or stays a reviewed
document, and whether a re-evaluation under a new rule version may change an
existing Evidence row. The schema supports either answer to both.

**Mission 1.52 was not started.**

---

## Artifacts

| file | what it is |
|---|---|
| `0034_deterministic_derivation_provenance.sql` | the migration — additive, forward-only, no backfill |
| `deterministic-derivation-provenance-schema-v1.json` / `.md` | the implementation record and its rendering |
| `render_derivation_provenance_schema.py` | renders and **cross-checks the record against migration 0034 itself**; wired into CI |
| `test_derivation_provenance_schema.py` (services/nlp) | 28 DB tests including the retention proof and the idempotency contrast |

No new ADR: ADR-037 already governs the semantics, and this mission resolved only
the schema-level details it left open. A second ADR would restate a decision
already made.

Governance: `docs/CLAUDE.md` 1.84 → 1.85, `PROJECT_MANIFEST.md` 1.83 → 1.84.
