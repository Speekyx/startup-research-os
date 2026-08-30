# Test Data Isolation Audit V1

**Status:** Audit record. Produced by Mission 1.6.1 §9.
**Date:** 2026-08-30
**Covers:** every test module that creates, updates or deletes a workspace,
project, session, opportunity, claim, evidence, raw record or normalized record.
**Related:** `docs/architecture/testing-strategy.md` §12–§16,
`infrastructure/testing/workspace_guard.py`,
`infrastructure/scripts/fk_closure.py`,
`docs/architecture/mission-1.6-report.md` §19–§20.

---

## 0. Why this audit exists

Three incidents in one afternoon, none of them careless:

| What happened | Cost |
|---|---|
| `test_claims.py` wrote into the seeded development workspace and never cleaned up | 39 claims and 36 evidence rows accumulated, then were destroyed by a cleanup that did not know they were in scope |
| `test_rls.py` proved an unscoped `DELETE FROM research.research_projects` cannot cross a tenant boundary — by running it in the seeded workspace | a real research session deleted; twelve records orphaned |
| an acquisition fixture deleted acquisition rows from seeded workspace B in teardown | nothing, because B happened to be empty |

Every one of those tests **passed**. Each was correct about the property it
asserted; each had reached for the workspace id already in scope. The third is
the most instructive: it was harmless purely by luck of timing, and would have
destroyed real data the day anything was collected there.

---

## 1. The three classes

| Class | Definition |
|---|---|
| **ISOLATED** | Touches no shared persistent state, or only state it created in a workspace of its own and removed afterwards |
| **SHARED-SEED-READ-ONLY** | Reads seeded reference data, or uses a seeded workspace id as a value without any database contact |
| **SHARED-SEED-MUTATING** | Creates, updates or deletes rows in a seeded workspace, or the workspace itself |

§9 requires **zero** in the third class at mission completion.

**"Uses the id" is not the same as "writes to it"**, and the distinction is where
most of the survey time went. A unit test that puts `WORKSPACE_A`'s uuid into a
task payload and asserts the payload is refused never opens a connection. It is
read-only in effect and a latent hazard in form — §5 covers what was done about
that.

---

## 2. The survey

Twenty modules. Counts are database-mutating statements found in each.

| Module | Tenant writes | Registry writes | Workspaces | Class |
|---|---|---|---|---|
| `acquisition/tests/conftest.py` | 7 | 4 | A, B, P, Q | **ISOLATED** (was mutating — §4) |
| `acquisition/tests/test_collector_conformance.py` | 0 | 0 | A (id only) | SHARED-SEED-READ-ONLY |
| `acquisition/tests/test_compliance.py` | 0 | 3 | — | ISOLATED (registry — §6) |
| `acquisition/tests/test_fk_closure.py` | 0 | 0 | — | ISOLATED |
| `acquisition/tests/test_normalization_model.py` | 0 | 0 | — | ISOLATED |
| `acquisition/tests/test_numeric_precision.py` | 0 | 0 | P | ISOLATED |
| `acquisition/tests/test_source_registry.py` | 0 | 4 | — | ISOLATED (registry — §6) |
| `acquisition/tests/test_source_review.py` | 0 | 4 | — | ISOLATED (registry — §6) |
| `acquisition/tests/test_world_bank_collector.py` | 0 | 0 | A (id only), P | SHARED-SEED-READ-ONLY |
| `acquisition/tests/test_world_bank_live.py` | 0 | 0 | A (id only) | SHARED-SEED-READ-ONLY, opt-in |
| `acquisition/tests/test_world_bank_normalizer.py` | 1 | 0 | P, Q | ISOLATED |
| `gateway/tests/conftest.py` | 3 | 0 | A, B, P, Q, RLS, INTEGRATION, ORCH, SECURITY | ISOLATED |
| `gateway/tests/test_claims.py` | 7 | 0 | P, Q | ISOLATED |
| `gateway/tests/test_integration.py` | 5 | 0 | INTEGRATION | ISOLATED |
| `gateway/tests/test_orchestrator_integration.py` | 5 | 0 | ORCH | ISOLATED |
| `gateway/tests/test_rls.py` | 4 | 0 | RLS | ISOLATED |
| `gateway/tests/test_security.py` | 0 | 0 | SECURITY | ISOLATED |
| `research-orchestrator/tests/test_orchestration.py` | 0 | 0 | A, B (ids only) | SHARED-SEED-READ-ONLY |
| `workers/tests/test_queue_infrastructure.py` | 0 | 0 | A (id only) | SHARED-SEED-READ-ONLY |
| `workers/tests/test_task_surfaces.py` | 0 | 0 | A (id only) | SHARED-SEED-READ-ONLY |

**SHARED-SEED-MUTATING: 0.**

---

## 3. What was already fixed before this mission

Most of the work was done by two branches that landed between Mission 1.6 and
this one, and this audit records rather than repeats it.

- **PR #4** gave the claim and evidence suite disposable workspaces P and Q.
- **PR #6** did the same for `test_rls.py`, `test_integration.py`,
  `test_orchestrator_integration.py` and `test_security.py` — including the
  unscoped `DELETE`, which now runs in `WORKSPACE_RLS_P` and **still asserts the
  same thing**. §11 is satisfied: the security guarantee was not weakened to
  protect development data; the setup was moved.
- **PR #8** added a post-suite leak check to `run_pytest_suites.py` that
  snapshots every `workspace_id`-carrying table before and after the run.

---

## 4. What this mission fixed

**`acquisition/tests/conftest.py::second_workspace`** was the last
shared-seed-mutating fixture. It yielded the seeded workspace B and deleted
`normalized_records` and `raw_records` from it in teardown.

Nothing about the assertion needed a seeded workspace. "A workspace cannot read
another workspace's rows" needs *another workspace*; it now creates
`WORKSPACE_Q` (`…000e`), uses it, and drops it.

---

## 5. The guard, and why the leak check is not enough

`infrastructure/testing/workspace_guard.py` — `disposable(workspace_id)` raises
if the id is one of the two seeded workspaces. It is called by the fixtures that
**create or destroy**, in both suites, from one shared definition.

The runner's leak check and this guard answer different questions, and neither
subsumes the other:

| | Question | Blind to |
|---|---|---|
| leak check (PR #8) | did the run **change** the database? | a fixture that deletes from a seeded workspace that is currently empty — nets to zero, destroys real data later |
| `disposable` | is this fixture **allowed to point here**? | a test that writes through a path no fixture guards |

The second is what the third incident needed. It was harmless in August and
would not have been in September.

**It replaced a correct assertion that was about to go stale.**
`_drop_workspace` asserted `workspace_id == WORKSPACE_P`, which was true and
became wrong the moment §4 added a second disposable workspace. `disposable`
states the rule rather than one instance of it.

### The latent hazard that was left alone, deliberately

Seven modules use `WORKSPACE_A`'s uuid as a *value* — in a task payload, in an
in-memory collector call — with no database contact. They are read-only in
effect.

They were not changed. Renaming a constant across seven modules to remove a
hazard that the fixture guard already covers is churn that touches more code
than it protects. What makes them safe is that no path from those tests reaches
a write without going through a guarded fixture, and the leak check would catch
it if one ever did.

---

## 6. Registry writes: a different class, deliberately excluded

Three acquisition modules mutate `registry.*`. That is **global platform
metadata**, not tenant data: no `workspace_id`, no RLS policy, and outside the
leak check's scope by construction.

They are ISOLATED in the sense that matters — each restores the previous value
rather than forcing a default. `enabled_world_bank` reads `collector_enabled`,
sets it, and puts back **what it found**, which is the pattern Mission 1.5
arrived at after a fixture reset every source to `FALSE` in teardown and
silently reverted an operator's deliberate enablement.

**This is a real gap and it is named rather than closed.** A registry mutation
that failed to restore would not be caught by anything today. Closing it means
extending the leak check to tables with no `workspace_id`, which is a larger
change than this mission's scope; §21's gates cover the tenant side only.

---

## 7. Verification

Run against a database holding six real raw records and six real normalized
records:

```text
337 acquisition + 214 gateway + 76 orchestrator + 34 workers + ... = all suites pass
database unchanged by the run, across 20 tenant tables
```

The six records and their session links survived the full suite unchanged
(§20). That is the regression this audit exists to make permanent.
