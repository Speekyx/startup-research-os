# Mission 1.0 — Completion Report

**Mission:** Source Registry, Compliance Governance & Data Acquisition Contracts
**Sprint:** 1
**Date:** 2026-08-29
**Branch:** `sprint-1/mission-1.0`
**Resolves:** **D-07**
**Introduces:** [ADR-013](adr/ADR-013-source-registry-governance.md),
[`source-registry-v1.md`](../data/source-registry-v1.md),
[`source-review-guide.md`](../data/source-review-guide.md), migration
`0004_source_registry`, package `sros-acquisition`

---

## 1. What this mission added, in one paragraph

The system can now say, per source, whether it may be collected from, on what
recorded evidence, and — when it may not — exactly what is missing. Six global
tables hold source definitions, technical access profiles, per-activity policy
reviews, the retrieved documents those reviews rest on, retention overrides and
capabilities; a view derives collector eligibility from them; two database
triggers make the rule unbypassable; a CLI administers reviews; a read-only API
exposes the result; and the Research Orchestrator now derives its ACQUISITION
block from the registry per source instead of restating a sentence in code.
**Thirteen candidate sources are registered and zero are collector-eligible**,
which is the intended outcome of a first pass, not a shortfall.

---

## 2. The design decision that shaped everything else

The obvious implementation is a `sources` table with an `is_approved` boolean.
It fails three ways, and each failure was the reason for a specific structure
here.

**A boolean cannot carry its basis.** Six months later nobody can say what the
`true` rested on, and when a platform revises its terms there is nothing to
re-check. → Evidence is a table, approval cannot exist without a row in it, and a
deferred constraint trigger enforces that at COMMIT.

**One verdict conflates independent questions.** The common real case is a
platform that permits automated API reads and forbids commercial use. → Eleven
activities are assessed separately, each scoped to one stated
`assessed_use_case`.

**A technical fact drifts into a permission.** "A browser can load this page" and
"we may collect this page" are different statements; in one field the first
becomes the second. → Access profiles and policy reviews are different tables, so
no reader can take one for the other.

Full rationale and rejected alternatives: [ADR-013](adr/ADR-013-source-registry-governance.md).

---

## 3. Data model

Six tables plus one view, all in the `registry` schema, all **global**.

| Object | Holds |
|--------|-------|
| `registry.sources` | identity, family, coverage, lifecycle, `collector_enabled` |
| `registry.source_access_profiles` | how it could be reached. Says nothing about permission |
| `registry.source_policy_reviews` | eleven per-activity verdicts, conditions, open questions, personal-data classification, review cadence |
| `registry.source_policy_evidence` | the retrieved documents a review rests on |
| `registry.source_retention_policies` | a per-source override, with a mandatory `basis` |
| `registry.source_capabilities` | what data the source can supply |
| `registry.source_eligibility` (VIEW) | the verdict, plus `blocking_reasons TEXT[]` |

`source_family` is a **registry entry**, not an enum — adding a family must never
require a migration (Ontology V2 §14). The seven new closed enums
(`SourceApprovalState`, `SourceAccessMethod`, `PolicyAssessment`,
`PolicyEvidenceType`, `SourceLifecycle`, `SourceAcquisitionCost`,
`PersonalDataRisk`) are closed because each requires exhaustive branching.

### Why global rather than workspace-scoped

No registry table carries `workspace_id` and none has an RLS policy. A source
assessed as permitted in one workspace and prohibited in another would make
provenance incomparable across workspaces, and would give one evidence record two
meanings. ADR-012 governs tenant tables; these are not tenant tables. The
consequence is enforced rather than documented: the runtime role holds `SELECT`
only on `registry.*`.

### Eligibility is derived, never stored

`registry.source_eligibility` computes the verdict. A stored boolean can drift
away from the reasons behind it, and the drift is discovered by whoever trusted
it. `collector_enabled` is a different thing — the operational switch — and a
`BEFORE UPDATE` trigger refuses to set it on a source the view does not clear.

### Approval cannot outrun its evidence

Evidence rows reference their review, so both are written in one transaction.
`trg_source_policy_reviews_require_evidence` is therefore `DEFERRABLE INITIALLY
DEFERRED` and checks at COMMIT. Both halves are tested: an approval with no
evidence is refused, and an approval whose evidence lands in the same transaction
is accepted.

---

## 4. The eligibility gate

```text
collector_eligible(source) =
        lifecycle is ACTIVE
    AND source is not suspended
    AND a policy review exists
    AND the review is in an approving state
    AND the review has at least one AUTHORITATIVE evidence record
    AND the review is not stale (past next_review_at)
    AND at least one access profile is configured
    AND every profile requiring a credential names a configuration reference
    AND any retention override present records its basis
```

Three properties matter as much as the conditions:

**It fails closed.** Anything missing blocks. There is no path from *we could not
check* to *we may proceed*.

**It reports every failed condition, not the first.** A gate that surfaces one
blocker at a time teaches a reviewer to distrust it. A refusal reading *"policy
review is REQUIRES_REVIEW; policy review has no evidence"* ends the conversation
instead of starting a new one each pass.

**It exists twice, and the two are compared.** The Python implementation runs
with no database (CLI, zero-dependency validator); the SQL view backs the trigger
so no client can bypass it. `test_the_python_gate_and_the_sql_view_agree`
compares them on all thirteen sources rather than assuming they match. Accepted
duplication, managed by a test — see ADR-013 §Consequences.

---

## 5. Orchestrator integration

Before this mission, ACQUISITION was blocked by a constant:

```text
D-07: the source registry and its per-source legal review records do not exist
```

That sentence is now false, and a false blocking reason is worse than a vague
one: it invites someone to conclude the block no longer applies. The block is
therefore derived at plan time (`sros_orchestrator.sources`):

| Registry says | Plan |
|---------------|------|
| ≥ 1 eligible source | ACQUISITION is planned |
| sources exist, none eligible | blocked, naming **each** source and its reasons |
| registry not consulted | blocked — an unconsulted registry is a refusal |

The third row is the one that matters for correctness. A planner with no registry
wired must behave identically to one that found nothing; otherwise a missing
integration reads as a permission. `UnconsultedRegistry` is the default provider,
so failing to wire the registry fails closed.

The per-source reasons reach the persisted plan (`research_plans.blocked_reasons`
JSONB) and are asserted there, because reasons that live only in memory cannot be
audited after the process exits.

`PLANNER_VERSION` moves to `1.0.0`; `NORMALIZATION`'s reason was restated (it is
blocked because no collector exists, which stays true regardless of how many
sources pass review).

---

## 6. The catalog: thirteen sources, zero eligible

Assessed use case, stated once and applying to every verdict:

> Automated collection of public content by Startup Research OS, a **commercial**
> multi-tenant SaaS, for storage, derived analytics and LLM processing.

| Source | Family | State | Evidence |
|--------|--------|-------|----------|
| `reddit` | community | `REQUIRES_REVIEW` | 0 |
| `hacker-news` | community | `REQUIRES_REVIEW` | 1 |
| `stack-exchange` | forum | `REQUIRES_REVIEW` | 0 |
| `product-hunt` | product_discovery | `RESTRICTED` | 1 |
| `github` | developer | `REQUIRES_REVIEW` | 2 |
| `apple-app-store` | app_store | `RESTRICTED` | 1 |
| `google-play` | app_store | `REQUIRES_REVIEW` | 0 |
| `youtube` | content_platform | `REQUIRES_REVIEW` | 1 |
| `tiktok` | social | `PROHIBITED` | 1 |
| `google-trends` | search_trends | `REQUIRES_REVIEW` | 1 |
| `world-bank` | economic_data | `REQUIRES_REVIEW` | 1 |
| `eurostat` | economic_data | `REQUIRES_REVIEW` | 1 |
| `fred` | economic_data | `REQUIRES_REVIEW` | 0 |

**0 APPROVED. 0 collector-eligible. 0 collectors enabled. 0 raw records.**

### Why zero is the right answer

§31 sets the standard explicitly: optimise for correctness and traceability, not
for the number of approvals. A registry in which every platform came back
approved would be evidence that the gate is not doing anything. Reaching zero
required refusing four specific temptations:

- **Not treating public visibility as permission.** Every source here is publicly
  reachable. None is eligible.
- **Not converting an unreachable document into an assumption.** Reddit's and
  Stack Exchange's terms were not retrievable from this environment, and the FRED
  API terms of use returned HTTP 403. Every such source is `REQUIRES_REVIEW` with
  the **exact outstanding documents named by URL** in `open_questions`, per §39 —
  "retrieve the Reddit Data API Terms at …", not "check the terms".
- **Not upgrading a partial permission.** Product Hunt and the Apple App Store are
  `RESTRICTED`: some assessed activities are permitted and others are not, and
  `RESTRICTED` says so instead of averaging it into an approval.
- **Not routing around an inconvenient API.** Google Trends has no published
  general API; the widely used approach is to call the undocumented endpoints
  behind the web interface. The review records that as **not an option**, and no
  access profile describes it.

### The one retention override

YouTube. Its API terms cap stored API data at 30 days, which is stricter than the
project's 365-day normalized baseline, so the override is raw 30 / normalized 30
with the cap recorded as its `basis`. Resolution uses `min()`, so an override can
only shorten — an override asking for longer would be a platform's terms being
used to weaken our own policy.

---

## 7. What was deliberately not built

| Not built | Why |
|-----------|-----|
| Any collector | §5. No source has passed the gate, so there is nothing a collector could lawfully run against |
| Any HTTP write path | §27. Authentication does not exist (ADR-005), so an endpoint able to approve a source would make this whole process optional for anyone who can reach the service |
| Per-source evidence reliability weights | **D-03.** Assigning "Reddit = 0.75" would decide the evidence-aggregation blocker by the back door |
| A legal-confidence percentage | No method produces such a number, so it would be invented — and an invented number is trusted exactly like a measured one. `UNCLEAR` plus `open_questions` says the same thing honestly |
| Jurisdiction determination | Requires human or legal input (`data-retention-policy-v1.md` §7). `jurisdiction_review_required` defaults true and no code sets it false |
| Any circumvention path | §21. No profile describes getting around a login wall, a rate limit, a robots directive or an anti-automation measure; CI asserts the package imports no network client at all |

No platform was contacted for data. Only official documentation *about* the
sources was read.

---

## 8. Tests

| Suite | Count | Covers |
|-------|-------|--------|
| `services/acquisition/python/tests` | 40 | identity, review and evidence, eligibility, retention, access metadata and secrets, the two database triggers, gate-vs-view agreement, load idempotence, contract agreement, CLI |
| `services/gateway/python/tests` | 158 | includes 8 new source-registry API tests, and 3 that replace the old single "the block names D-07" assertion |
| `services/research-orchestrator/python/tests` | 62 | 7 tests cover registry-derived acquisition blocking |
| Zero-dependency suites | 231 | unchanged, still install-free |

The tests assert on the **real** catalog rather than a fixture. The artefact
under review is `source-catalog-v1.json`; a suite checking a hand-made copy would
leave the reviewed file unchecked, which is the failure the suite exists to
prevent.

Six assertions are worth naming because they guard rules rather than behaviour:

1. `test_no_source_is_collector_eligible` — the gate result is a build-visible
   fact, so a source that quietly passed would go red.
2. `test_public_visibility_is_never_a_reason_to_be_eligible` — a source reachable
   only over the open web must still be blocked.
3. `test_the_database_refuses_an_approval_with_no_evidence` — and its companion
   proving the deferral is not a loophole.
4. `test_the_database_refuses_a_collector_on_an_ineligible_source` — even a direct
   `UPDATE` by the migration role.
5. `test_the_python_gate_and_the_sql_view_agree` — the accepted duplication,
   checked rather than trusted.
6. `test_no_raw_record_was_collected` — evidence that §5 held, not an assumption
   that it did.

---

## 9. CI

New job **`source-registry`** (zero-dependency, so a broken environment cannot
reduce it to nothing):

- `validate_source_registry.py` — states, evidence, secrets, aggregation language
- a grep asserting `sros_acquisition` imports no network client. §43 requires CI
  to contact no external platform; fetching a source's terms in CI would itself
  be collection, and would make the build depend on a third party's uptime

Added to existing jobs:

- `python-quality`: mypy now covers `sros_acquisition` and `sros_orchestrator`;
  `sros-source render --check` catches drift between the JSON catalog and its
  rendered markdown
- `integration`: `sros-source load` followed by
  `assert_registry_grants_nothing.py`, which fails the build if any source became
  eligible, any collector was enabled, or any raw record appeared

`quality-gates.md` §1 records all eight new gates.

---

## 10. Validation

Every command below was run, in this order, and passed.

| Check | Result |
|-------|--------|
| `generate.py --check` | 3 generated artefacts current |
| `run_python_tests.py` (zero-dep) | 231 tests, 4 packages |
| `validate_schema.py` | 8 invariant groups, 26 tables |
| `validate_source_registry.py` | 13 sources, 10 evidence records, 0 warnings |
| `migrate.py --plan` | 4 migrations, 2 seeds, well formed |
| `migrate.py --apply` on the existing database | 0 applied (idempotent) |
| `migrate.py --apply --seed` on an **empty** database | 4 applied, 2 seeded |
| `run_pytest_suites.py` against that fresh database | all 6 packages pass |
| `assert_registry_grants_nothing.py` | 13 registered, 0 eligible, 0 enabled, 0 raw records |
| `ruff check` / `ruff format --check` | clean, 179 files |
| `mypy` (6 packages) | no issues in 69 source files |
| `sros-source render --check` | rendered catalog matches |
| `tsc` contracts + web, `eslint` | clean |
| TS conformance + web API client | 19 + 18 tests |
| `next build` | 5 routes |

The from-scratch migration run matters more than the idempotence run:
`0004_source_registry` restructures tables created by `0001_foundation`, so a
migration that only works against a database that already has the old shape would
be a migration nobody could reproduce.

---

## 11. Issues found and fixed during the mission

| Issue | Resolution |
|-------|------------|
| `ALTER TABLE … ADD COLUMN …, FOREIGN KEY (…)` is invalid PostgreSQL | Split into `ADD CONSTRAINT … FOREIGN KEY` |
| A `CHECK` written as `coverage_countries <@ ARRAY(SELECT …)` — tautological, and `CHECK` forbids subqueries | Replaced with a regex over `array_to_string` |
| The view referenced `s.canonical_name` while the column was still `name` | Renamed the column in the migration |
| Generated `domain.py` had the seven new enums; hand-written `sros_contracts/__init__.py` did not re-export them | Added to imports and `__all__` |
| `validate_schema.py` required exactly one space before `IN` in a CHECK, which the aligned SQL does not use | Relaxed the regex rather than reformatting readable SQL |
| The validator flagged `github` and `world-bank` as GLOBAL-with-English-only coverage | **Fixed the data, not the warning**: `github` is `PARTIAL`, `world-bank` has no language (its indicators are numeric) |
| Two hardcoded schema tests (`21 tables`, three migrations) broke on `0004` | Rewritten to assert the **set** of tables. A count going 26 → 27 says the number changed; a set says which table appeared |
| `psycopg` could not infer the type of a parameter appearing only beside `NULL` | Explicit `::text` casts in the `/sources` family filter |
| A first draft of the circumvention test banned the substring "bypass" anywhere in the catalog — which would have forbidden *recording a refusal to bypass* | Scoped to access-profile fields; reviewer notes stay free to say the undocumented endpoint is not an option |

---

## 12. Decision resolution: D-07

**D-07 is resolved.**

> *D-07 — Source registry and per-source legal review records. Blocks
> `acquisition`, and blocks the `retention_override` mechanism the retention
> policy depends on.* — `mission-0.1.1-decisions.md` §3

Both halves are now built: the registry with its per-source review records
exists, and `registry.source_retention_policies` gives `retention_override` a
table with resolution semantics behind it.

**Resolution is not approval.** D-07 asked for a mechanism, and the mechanism
exists. It did not ask for sources to be approved, and none were. The block on
`acquisition` therefore remains — but it changed kind, from *there is no
registry* to *this specific source has not passed the gate, for these reasons*.
The orchestrator now reports the second, per source and by name.

Updated in this mission: `PROJECT_MANIFEST.md` → 1.4, `docs/CLAUDE.md` → 1.4,
`service-boundaries.md` §7, `docs/data/README.md`, `quality-gates.md` → 1.4.

**Numbering note.** The production-deployment ADR placeholder moved from ADR-013
to ADR-014, by the same rule applied in Mission 0.4: a reserved number with no
file and no decision is not an ADR, and the number goes to the first one actually
written. `mission-0.4-report.md` still refers to the placeholder as ADR-013; it
is a record of what was true when it was written and is not rewritten.

---

## 13. Remaining blockers

| Blocker | Status |
|---------|--------|
| **D-03** — evidence aggregation formula | **Open. Hard blocker.** `services/scoring` must not be implemented. This mission deliberately assigned no per-source reliability weight, which would have decided it implicitly |
| **D-12** — embedding versioning and re-embedding strategy | Open. Blocks `nlp` and opportunity discovery |
| **A-12** — non-geographic (audience/segment) scoping | Open. Untouched |
| **D-08** — score recomputation policy | Open |
| **D-11** — observability stack | Open |
| GDPR / jurisdiction analysis | **Requires human or legal input.** Deliberately not guessed |
| Production deployment target (now ADR-014) | Deferred by ADR-007 |

**New, and not a blocker in the decision-register sense:** no source is
collector-eligible. Unblocking it is review work — reading the named documents
and recording what they say — not a decision anyone needs to make.

---

## 14. Mission boundary

Stopped here, as §46 requires. **Mission 1.1 was not begun.** No collector was
implemented, no platform was contacted for data, nothing was scraped, and
`acquisition.raw_records` is empty — asserted in CI rather than claimed.

The honest one-line summary: the machinery for deciding whether a source may be
collected from now exists, works, and currently says *no* to all thirteen
candidates.
