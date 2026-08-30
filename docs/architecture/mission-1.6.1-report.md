# Mission 1.6.1 Report — Data Integrity, Raw Precision & Test Workspace Isolation

**Sprint:** 1
**Date:** 2026-08-30
**Scope:** hardening. Two correctness risks Mission 1.6 recorded, and one
cascade-safety lesson it learned the expensive way.
**Outcome:** collector `1.1.0` · **0 of 12 measured values corrupted** ·
0 shared-seed-mutating tests · 6 raw + 6 normalized records survive the full
suite byte-for-byte

---

## 1. The raw precision gap

Full audit, written before any code changed:
[`raw-numeric-precision-gap-analysis-v1.md`](../data/raw-numeric-precision-gap-analysis-v1.md).

**It was measured, not reasoned about**, by driving the real collector against a
fake transport — and that earned its keep immediately. The expectation going in
was "float destroys decimals". That is **wrong** for most values, and what float
actually destroys is narrower, stranger, and in one case worse than losing a
decimal place.

| Loss | What happens |
|---|---|
| **1 — type** | `1` and `1.0` both become `1.0`. The source distinguished them; the record cannot |
| **2 — magnitude** | `9007199254740993` → `9007199254740992`. Past 2^53 a double moves to the nearest representable integer |
| **3 — significant digits** | `1.23456789012345678` → `1.2345678901234567`. Anything past 17 digits |
| **4 — identity** | Distinct source values produce the **same** `content_hash` |
| **5 — serialization** | `json.dumps` emits `1.2345678901234568e+17`; JSONB stores `123456789012345680`. Hashed text ≠ stored text |

### Why most decimals survived, and why that is not reassuring

`0.1`, `2.675`, `82.4560975609756` and `2715518274119.71` all round-tripped
intact. Python's `repr` has produced the shortest decimal string that parses back
to the same double since 3.1, so `json.dumps(float("0.1"))` writes `0.1`.

**The serialization round-trips. The value never did.** `float("0.1")` is
0.1000000000000000055511151231257827, and every arithmetic consumer gets the
double. What shortest-repr guarantees is that the *text* survives, up to 17
significant digits — which is exactly why this defect stayed invisible.

### LOSS 4 is the one that is a bug rather than a fidelity complaint

`content_hash` covers the collapsed value, so two genuinely different upstream
figures hash identically. `_persist_one` then finds the existing row, moves
`last_seen_at`, and returns `UNCHANGED`.

**A real upstream revision is recorded as "we checked and it had not changed."**
That is the failure Mission 1.5 §24 built the revision machinery to prevent,
defeated one layer below it. Nothing raises, nothing logs, and the change is
simply absent from the history.

### Exposure of the authorized data: none, and that is not the point

All three authorized indicators are integral or few-digit and below 2^53, so the
six real records were never corrupted. This was a mechanism that was wrong while
the data happened to sit inside its safe range — and LOSS 4 means the failure,
when it arrives, is silent.

---

## 2. The collector versioning decision

**`world-bank-indicators@1.0.0` → `@1.1.0`.** A bump, not a fix, and §5 is right
to insist.

The change alters the canonical payload, which alters `content_hash`, which
alters the record id. A collector that silently produced different hashes for
identical source data would make every existing record look revised on its next
collection — the same guarantee `world-bank-collector-v1.md` §7 protects by
keeping the retrieval time *out* of the fingerprint, broken from the other
direction.

So 1.0.0 records stay 1.0.0 records. `collector_version` is on every row, which
is what Mission 1.5 §50 put it there for.

**Coexistence was demonstrated offline**, deliberately: the same observation
under the two versions hashes to `835d0bae…` and `5f4827f5…`. Proving it needed
no second live request, and §18 asks for *one* controlled acquisition.

**The normalizer accepts both** (`{"1.0.0", "1.1.0"}`). Dropping 1.0.0 would
strand every record collected before the bump; they are still true statements
about what the source said, and §8 forbids rewriting them.

---

## 3. Numeric representation

```text
json.loads(body, parse_float=Decimal)     ← and deliberately NOT parse_int
  └─ CollectedObservation.value: Decimal | None
      └─ payload {"value": canonical_number(v)}   ← a decimal STRING
```

**`parse_int` was set at first and removed**, which is worth recording because
the reasoning that added it was wrong in a way that looked right. Python's `int`
is arbitrary-precision, so `9007199254740993` already parses exactly; the
corruption came from `float()` downstream. Setting `parse_int` as well turned
`pages` and `page` into `Decimal`s, `_as_int` rejected them as non-integers, and
**the collector stopped after page one reporting unusable metadata.** The
existing pagination tests caught it, which is what they are for.

`_as_int` now also accepts an integral `Decimal`, because `parse_float=Decimal`
means a source writing `"pages": 3.0` legitimately delivers one.

### Why the value is a string

JSON has one numeric type, so `1` and `1.0` are the same number in it. A JSON
number cannot carry the distinction LOSS 1 destroys. A decimal string can, and it
is what the normalized layer already uses for the same reason.

All five §4 distinctions hold: `1` → `"1"`, `1.0` → `"1.0"`, `1.25` → `"1.25"`,
`0` → `"0"`, `null` → JSON `null`.

---

## 4. Raw content hashing

`canonical_number(d) = format(d, "f")`. Four properties, each load-bearing:

| Property | Without it |
|---|---|
| plain, never scientific | Python hashes `1.2…e+17` and JSONB stores `123456789012345680` — LOSS 5 |
| exact | the digits the source sent, unrounded and unpadded |
| type-preserving | `1` and `1.0` collapse — LOSS 1, and through it LOSS 4 |
| deterministic | a hash that depends on a float repr reports revisions nobody made |

Verified across integer, decimal, large integer, small decimal, zero, negative
and null, and asserted stable across repeated runs.

---

## 5. Precision regression tests

`test_numeric_precision.py`, 31 tests, every case driven through the **real
collector**. Asserting on `canonical_number` alone would test the serializer and
miss both places the old defect lived.

**They were verified to fail against 1.0.0 semantics** rather than assumed to
be meaningful:

| Assertion | 1.0.0 | 1.1.0 |
|---|---|---|
| integer beyond 2^53 not rounded | FAIL | pass |
| 18 significant digits not truncated | FAIL | pass |
| no scientific notation | FAIL | pass |
| `1` and `1.0` do not collide | collide | distinct |
| `…993` and `…992` do not collide | collide | distinct |

Also asserted: a population integer normalizes **identically** under both
versions (`67158348.0` and `67158348` both → `67158348`), so the bump is not a
data change to anything downstream.

---

## 6. Test workspace isolation audit

Full classification: [`test-data-isolation-audit-v1.md`](../testing/test-data-isolation-audit-v1.md).
Twenty modules surveyed.

**SHARED-SEED-MUTATING: 0.**

Most of the work had already landed between missions — PR #4 (claims), PR #6
(RLS, integration, orchestrator, security) and PR #8 (a post-suite leak check).
The audit records that rather than repeating it.

**This mission fixed the last one.** `second_workspace` yielded the seeded
workspace B and deleted acquisition rows from it in teardown. It was harmless
only because B happened to be empty — a passing test that would have destroyed
real data the day anything was collected there. It now creates and drops
`WORKSPACE_Q` (`…000e`).

**"Uses the id" is not "writes to it."** Seven modules put a seeded workspace's
uuid into a payload with no database contact. They were left alone: renaming a
constant across seven modules to remove a hazard the fixture guard already covers
is churn that touches more than it protects.

---

## 7. RLS test fixes

Already done by PR #6, and §11 is satisfied in the way it asks: the unscoped
`DELETE FROM research.research_projects` **still asserts the same thing**, in
`WORKSPACE_RLS_P`. The security guarantee was not weakened to protect
development data; the setup moved.

Its blast radius is now measurable, and it is larger than anyone had reasoned
about: **17 tables.**

---

## 8. Claim and evidence test fixes

Done by PR #4: dedicated workspaces P and Q, deterministic cleanup. Verified
here — after a full run against a freshly rebuilt database, `research.claims` and
`scoring.evidence` are **0**, not 39 and 36.

---

## 9. FK cascade safety

`infrastructure/scripts/fk_closure.py` — reads `pg_constraint`, walks the graph,
prints what a delete may reach. It deletes nothing and its own test asserts the
module contains no write statement.

It reproduces all three Sprint 1 incidents:

| Delete from | Reaches | The incident |
|---|---|---|
| `research.opportunities` | 6 tables | 156 opportunities also took 39 claims, their revisions, observations, 36 evidence rows and their independence groups |
| `acquisition.raw_records` | 5 tables | delete-and-recollect destroyed six normalized records |
| `research.research_projects` | **17 tables** | `test_rls.py` orphaned twelve records through the session |

**`SET NULL` is reported alongside `CASCADE`**, and that is not decoration: a row
that survives with a nulled foreign key is still a row the delete changed, which
is exactly how twelve records lost their session link while every count stayed
the same.

13 tests, asserted as **relations rather than counts** — "the closure has 6
entries" breaks on the next migration and teaches whoever hits it to edit the
number.

Two of my own assertions in that suite were wrong and had to be corrected
against the catalog: composite FKs do **not** all lead with `workspace_id` (the
registry taxonomy keys are `(registry, id)`), and they are **not** all two
columns (`claims_current_revision_fkey` has three). The test now asks
`pg_constraint` for the column count instead of guessing.

---

## 10. Development-data protection

`infrastructure/testing/workspace_guard.py` — `disposable(workspace_id)` raises
on the two seeded workspaces. One definition, imported by both suites that own
destructive fixtures. Stdlib only.

**It replaced a correct assertion that was about to go stale.**
`_drop_workspace` asserted `workspace_id == WORKSPACE_P`, which was true and
became wrong the moment §10 added a second disposable workspace.

### Why the leak check does not make it redundant

| | Asks | Blind to |
|---|---|---|
| leak check (PR #8) | did the run **change** the database? | a fixture deleting from a seeded workspace that is empty *today* |
| `disposable` | may this fixture **point here at all**? | a write reaching the database through no fixture |

The second is exactly what `second_workspace` needed.

---

## 11. Real acquisition regression

Against a database **rebuilt from empty**, nine migrations, idempotent on a
second run.

**§8's controlled reset, stated explicitly:** the rebuild destroyed six 1.0.0 raw
records and — through `normalized_records.raw_record_id ON DELETE CASCADE` — six
normalized records. Their values were captured first and are in §1 of this
report. Nothing was rewritten in place, and no record claims to have been
produced by a version that did not produce it.

```text
SP.POP.TOTL · FR, DE · 2018–2020 · 1 request
→ 6 records, 0 refusals, 0 failures
→ persisted: 6 new

values stored: 82905782  83092962  83160871  67158348  67382061  67601110
               all canonical decimal strings, no ".0" artifact
collector:     world-bank-indicators@1.1.0
```

Second identical acquisition: **0 new, 6 unchanged.** Idempotent.

---

## 12. Real normalization regression

```text
records_input 6 · normalized 6 · valid 6 · new 6 · failures 0
```

Values preserved exactly from the canonical raw representation. Signals 0,
claims 0, evidence 0, embeddings 0, scores 0.

---

## 13. Full-suite-after-real-data verification

§20's mandatory regression, and the one that makes the isolation work permanent.

```text
before:  6 raw, 6 normalized, all six session-linked on both layers
run:     all suites pass — 337 zero-dependency + 350 acquisition + 214 gateway
         + 76 orchestrator + 34 workers + 125 llm-gateway + 27 contracts
         database unchanged by the run, across 20 tenant tables
after:   6 raw, 6 normalized — byte-for-byte identical, ids, hashes,
         payloads, timestamps and session links all unchanged
```

Compared field by field, not by row count: a count would not have noticed a
nulled session link, which is precisely how the Mission 1.6 damage went
unnoticed.

---

## 14. CI

Two gates added to `validate_normalization.py` (now nine boundary groups),
zero-dependency like the rest:

- **no `float(` on the acquisition numeric path** — AST, not grep. `float | None`
  in an annotation is a different token, and a comment explaining why float is
  avoided would trip a grep, which is how a check gets disabled by whoever
  documents the rule it enforces.
- **destructive fixtures import and call the workspace guard** — an unused guard
  is a comment.

**Both were probed against real violations before being believed** — a `float()`
injected into each numeric-path module, and the guard call removed. All three
caught, baseline restored.

`testing-strategy.md` → 1.9, with §15 (test data isolation) and §16 (cleanup
assertions must consider the FK closure) as standing rules.

---

## 15. Remaining blockers

| Item | Status |
|---|---|
| **Registry mutations are unguarded** | Named, not closed. Three modules mutate `registry.*`, which has no `workspace_id` and is outside the leak check by construction. They restore what they found; nothing enforces it. Closing this means extending the leak check to non-tenant tables |
| **D-08** — which normalized version downstream reads | Open. §49 of Mission 1.6 forbids resolving it |
| **D-12** — embeddings | Open. NLP, signals and vectors remain blocked |
| **PROFILE-NOT-CALIBRATED** | Unchanged. `services/scoring` unavailable |
| **D-10** — object storage | Unchanged |
| Retention lifecycle jobs | Still unimplemented; `expires_at` is written and nothing acts on it |
| The 1.0.0 records | Gone, by the documented §8 reset. The *mechanism* for coexistence is tested; no 1.0.0 row now exists to point at |

---

## 16. Mission 1.7 readiness

Ready. Source numbers survive acquisition exactly, the collector version is
honest about the change, no test mutates persistent development data, and the
blast radius of a destructive action is derivable rather than remembered.

Three things a next mission should know:

- **the normalizer canonicalises away trailing zeros** (`1.0` → `1`), which is
  correct at that layer — a quantity, with precision carried separately in
  `decimals` — and means the raw layer is the only place the `1` / `1.0`
  distinction survives;
- **`parse_int=Decimal` is a trap**, documented in the collector, and the
  pagination tests are what caught it;
- **the FK closure tool exists and nothing calls it automatically.** It informs a
  human before a destructive action; wiring it into a guard is available work.

---

## 17. The questions §24 asks

| Question | Answer |
|---|---|
| Does any World Bank numeric value pass through `float` before RawRecord persistence? | **No.** Parsed with `parse_float=Decimal`, held as `Decimal`, serialized by `canonical_number`. A CI gate fails the build on a `float(` call in either module of that path |
| Was the collector version bumped? | **Yes**, `1.0.0` → `1.1.0`, because the change alters every `content_hash` |
| Can non-binary-exact decimal values survive collection unchanged? | **Yes.** 0 of 12 measured values corrupted, including `0.1`, 18 significant digits, and an integer beyond 2^53 |
| Are old collector records still distinguishable? | **Yes**, by `collector_version` on every row, and their payloads hash differently — demonstrated offline. No 1.0.0 record exists now, by the documented §8 reset |
| Do any tests mutate the seeded development workspace? | **No.** Zero shared-seed-mutating modules, and a guard refuses the ids in the fixtures that create or destroy |
| Do claim/evidence tests leave synthetic data behind? | **No.** 0 claims and 0 evidence after a full run |
| Can FK cascade impact be determined mechanically? | **Yes.** `fk_closure.py` derives it from `pg_constraint`; 13 tests, no hard-coded graph |
| Did the complete suite run after real records existed? | **Yes** |
| Did those records survive unchanged? | **Yes** — byte-for-byte, compared field by field rather than by count |
| Are six World Bank RawRecords present? | **Yes**, all `world-bank-indicators@1.1.0` |
| Are six World Bank NormalizedRecords present? | **Yes**, all `VALID` |
| Were any signals/claims/evidence/embeddings/scores generated by this mission? | **No.** All zero |
| Is Mission 1.7 safe to begin? | **Yes** |

---

## 18. Validation

| Gate | Result |
|---|---|
| Database rebuilt from empty, 9 migrations, idempotent re-run | pass |
| RLS, two-workspace suites | pass |
| Zero-dependency Python suites | 337 tests, pass |
| pytest, 6 packages | 826 tests, pass |
| ruff check / format | pass |
| mypy strict, 100 files | pass |
| contract generation `--check` | pass |
| `validate_schema` / `source_registry` / `compliance_capabilities` / `evidence_aggregation` | pass |
| **`validate_normalization`** — 9 groups, incl. 2 new | pass, probed against 3 violations |
| `assert_registry_grants_nothing` | pass |
| tsc, eslint, contract conformance | pass |
| Real acquisition, idempotent re-acquisition, normalization | pass |
| Full suite **after** real data, records unchanged | pass |

---

## 19. Stop condition

Stopped here, per §25. No sources added, no Eurostat or FRED collector, no
social/consumer review, no signal extraction.
