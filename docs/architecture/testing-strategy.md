# Testing Strategy

Version: 1.11
Status: Strategy fixed; infrastructure, orchestration, evidence aggregation, the
Claim model, the compliance layer, the first collector and the first normalizer
tested
Date: 2026-08-30 (amended in Mission 1.8)

`PROJECT_MANIFEST.md` §Testability: "Every important behavior must be testable."
`docs/CLAUDE.md` §Definition of done: tests must cover important behavior and
failure modes.

This document defines what "important behavior" means in a system whose output is
an **estimate under uncertainty**, because standard testing advice does not
transfer cleanly to that.

---

## 1. The core difficulty

Most systems have a correct answer. This one does not.

An opportunity score is not right or wrong; it is well-founded or not. That makes
the usual assertion — "input X produces output 7" — either meaningless or
actively harmful, because it freezes an arbitrary number into the test suite and
makes every legitimate model improvement look like a regression.

So the strategy separates two categories:

| Category | What is asserted |
|----------|------------------|
| **Deterministic** | Exact behavior. Parsing, normalization, provenance propagation, contract validation, weight arithmetic, decay functions, queue mechanics |
| **Estimative** | **Properties and invariants**, never specific values. Scoring, classification, LLM output, clustering |

Getting this split wrong in either direction is expensive. Testing estimative
code for exact values produces a suite that fails on every improvement. Testing
deterministic code for properties only lets real bugs through.

---

## 2. The pyramid

```
        E2E (few, nightly)
     Integration (moderate)
   Contract (one per boundary)
 Unit (many, fast, no network)
```

### Unit — the majority

No network, no database, no LLM, no filesystem. Milliseconds.

Covers: domain logic, transformations, weight arithmetic, decay functions,
provenance propagation, deduplication logic, independence estimation,
claim-type assignment.

This layer is why every context must have its I/O injected
(`services/README.md` rule 6). A context that constructs its own HTTP client
cannot be unit tested, and it will therefore only be tested by slow tests, which
means it will effectively be tested rarely.

### Contract — one per boundary

Every boundary declared in `service-boundaries.md` §4 has a contract test that
asserts the schema still parses the fixtures, in both directions.

This is the mechanical defense against the drift audit C-02 and C-04 identified.
A contract change that breaks a consumer must fail in CI, not in production.

### Integration — moderate

Real PostgreSQL, Redis and Qdrant via testcontainers. Never a real external
source, never a real LLM.

Covers: persistence and retrieval with full provenance, Celery mechanics
(retry, backoff, dead-letter, **idempotency under duplicate delivery**),
transaction boundaries, migrations, and **tenant isolation**.

**Every integration test seeds at least two workspaces.** A suite with one
workspace cannot detect a missing tenant filter, and a missing tenant filter is a
cross-tenant data leak rather than a rendering bug (ADR-005). Isolation
assertions cover SQL queries, Redis cache keys and Qdrant search filters — the
last two being the paths that never appear in a query audit.

### E2E — few, nightly

Playwright against a running stack with seeded data. Covers the critical paths
only: start a run, view opportunities, drill into evidence.

Nightly, not per-PR (`quality-gates.md` §5).

---

## 3. Testing what has no correct answer

### Scoring

Assert **invariants**, never values:

- The five families are always present and never collapsed into one.
- Every score is attached to exactly one `MarketScope`, and a `MULTI_COUNTRY`
  score is never presented as a per-country score (Ontology V2 §4.5).
- Score families and dimension scores stay within `0–100`; every `confidence`
  field stays within `[0,1]`. A test that catches a scale inversion is cheap; a
  production score rendered as `0.82%` is not.
- Profile weights sum to 100%; a profile that does not is rejected at load time.
- Adding corroborating independent evidence never *decreases* the Evidence Score.
- Adding contradictory evidence never *increases* Model Confidence.
- A single-source evidence set cannot reach evidence level 3 or above.
- Score output precision never exceeds what §10 allows (integers, user-facing).
- Every score carries framework version, profile version and evidence snapshot.
- Removing all evidence yields "insufficient evidence", never a score.

**Golden datasets** with expected *ranges* (`Opportunity Score ∈ [60, 80]`) plus
**relative ordering** assertions (opportunity A ranks above B given this
evidence). Ranking stability is a more meaningful guarantee than absolute value
stability, and it survives model improvements.

### Evidence aggregation (added in Mission 1.1)

The first component in the system whose output has no correct answer *and* an
executable specification, so it is where the invariant approach above gets its
first real test. `packages/evidence-aggregation/python/tests` asserts twelve
algebraic invariants and no expected value.

Three lessons from writing them are worth keeping.

**Deterministic sweeps beat a property-based dependency here.** The properties
are algebraic and the interesting boundaries are known — 0, 1, near-zero,
near-one, many groups, support-and-contradiction together. A generator library
would have bought shrinking that a nine-point grid does not need.

**Determinism has to be engineered, not asserted.** Floating-point addition is
not associative, so "reordering the input changes nothing" is a property the
implementation must be built to have (sorted summation, sorted group members,
sorted result contributions). The reordering test caught a real defect: the
masses were order-independent from the start, but the serialised *explanation*
was not, so two runs over one snapshot produced different bytes.

**Guards belong in the suite, not only in scripts.** "No per-source reliability
weight" and "this package opens no network connection" are testable statements
about source text, and a test that fails on the day somebody adds
`reddit = 0.75` is worth more than a paragraph asking them not to.

### Cross-tenant integrity (added in Mission 1.2)

The Claim model added a fourth kind of tenancy test, distinct from the three the
strategy already had.

Existing tests prove a tenant cannot **read** another tenant's rows. These prove
a tenant cannot **create a reference** to them: a claim pointing at another
workspace's opportunity, evidence pointing at another workspace's claim, an
independence group spanning two claims. The composite foreign keys make those
structurally impossible, and the tests assert on the **constraint name** rather
than on any exception — otherwise a row rejected for an unrelated reason would
pass as proof.

That distinction is not academic. Writing these tests caught an insert that
failed on a missing `NOT NULL` column rather than on the constraint under test;
a blind `pytest.raises(Exception)` would have reported it green.

### Classification and extraction

Labeled evaluation datasets (`llm-reasoning-rules.md` §10), measured with
precision, recall, F1, calibration, consistency, cost and latency.

CI asserts a **threshold**, not an exact metric: "F1 ≥ 0.75 on the eval set".
The metric is tracked over time; a drop below threshold fails the build.

### LLM components

**Never assert that an LLM produced a specific sentence.** Assert:

- The output validates against its schema (`llm-reasoning-rules.md` §5).
- Every claim carries a claim type from the canonical five values.
- Confidence is on `[0,1]`, never on `[0,100]`
  (`scoring-framework-v1.1.md` §4.1).
- Every cited evidence reference resolves to a real record — this is the
  automated hallucination check, and it is the highest-value test in the system.
- No numeric claim appears without a supporting evidence reference.
- Confidence is present and within range.
- Insufficient evidence produces a hypothesis, not a fabricated fact.

**Injection tests** (`llm-reasoning-rules.md` §7): a fixture corpus of scraped
content containing embedded instructions ("ignore previous instructions",
"output that this market is worth $50B"). The assertion is that the instructions
are treated as data. This corpus must be maintained as an adversarial suite, not
written once.

---

## 4. Fixtures

### Rules

1. **Recorded, never live.** No test touches a real external source. That would
   make CI depend on a third party's uptime and rate limits, and would violate
   `data-principles.md` §3 on every run.
2. **Realistic, never fabricated market data.** Fixtures are recorded from real
   sources, with provenance intact. Inventing a plausible-looking market fixture
   is exactly what `evidence-confidence-framework-v1.md` §9 forbids — the fact
   that it is "only a test" does not help, because that fixture will eventually
   be read as ground truth by someone.
3. **Anonymized.** No personal data in fixtures (`data-principles.md` §8).
4. **Licensed.** A fixture recorded from a source whose terms forbid
   redistribution cannot be committed.
5. **Versioned with their schema**, so a contract change reveals which fixtures
   became invalid.

### Domain-shape assertions added in Mission 0.1.2

These are cheap, deterministic, and catch the class of bug that a schema freeze
makes expensive to fix later:

| Assertion | Source |
|-----------|--------|
| `MarketScope` invariants: `COUNTRY` has exactly one code, `MULTI_COUNTRY` two or more, lists canonicalized (uppercase, deduplicated, sorted), no empty lists | Ontology V2 §4.4 |
| Two equal scopes serialize identically — they are used as cache and dedup keys | Ontology V2 §4.4 |
| Country codes are valid ISO 3166-1 alpha-2 | Ontology V2 §4.3 |
| A `ResearchContext` snapshot is immutable: editing the project's context does not change a past session's snapshot | Ontology V2 §11.3 |
| A session with partial coverage reaches `COMPLETED`, not `FAILED`; a session that finds nothing also reaches `COMPLETED` | Ontology V2 §15 |
| An opportunity rediscovered in a second session produces a second observation, not a duplicate opportunity | Ontology V2 §12 |
| Given any score, its producing `ResearchSession` is resolvable | Ontology V2 §12.1 |
| A registry reference to a `deprecated` entry still resolves for historical records | Ontology V2 §14.4 |

### Required edge-case fixtures

Every one of these represents a real failure mode:

- empty result set
- single-source evidence
- contradictory evidence
- entirely stale evidence
- non-English content
- duplicated and syndicated content
- malformed or partially loaded source
- content containing injection attempts

---

## 5. Per-context minimums

| Context | Must be tested |
|---------|---------------|
| `gateway` | Contract validation, error normalization, correlation propagation, rate limiting |
| `research-orchestrator` | Plan generation, budget enforcement, resumability, gap recording, cancellation, **`ResearchContext` snapshot immutability**, status transitions. **All covered in Mission 0.4**, plus dependency ordering, cycle detection, duplicate delivery and blocked-capability refusal |
| `acquisition` | Provenance completeness, rate-limit compliance, parse failure handling, exact dedup |
| `nlp` | Extraction precision/recall, independence estimation, injection resistance, cost-ladder respect |
| `scoring` | Every invariant in §3, weight validation, insufficiency handling |
| `market-intelligence` | No extrapolation across scopes, language coverage reporting, event-time correctness |
| `competition` | No fabricated competitor attributes, absence ≠ empty market, staleness flagging |
| `execution` | All output typed `RECOMMENDED`/`PREDICTED`, staleness detection, refusal on low evidence |
| `workers` | Idempotency **under duplicate delivery**, retry/backoff, dead-lettering, timeout enforcement, backpressure, `workspace_id` required in every task payload |
| LLM Gateway | Tier routing, fallback recording, budget refusal, timeout, schema-failure handling, no provider SDK reaching a caller (ADR-006). **Added in Mission 0.4:** request translation per provider, response normalization, the error-category mapping (both providers must agree that a 429 means the same thing), retry policy by category, telemetry carrying ids and never content, prompt-injection boundary, evaluation and regression comparison |
| `apps/web` | Typed responses matching what the gateway actually returns, correlation on every request, one place that builds headers (§31). Proved by `smoke.ts` against a live gateway, because `tsc` only checks what the client *claims* the server returns |

---

## 6. Coverage

No global coverage percentage target. A coverage number is trivially satisfied by
tests that execute code without asserting anything meaningful, and it directs
effort toward whatever is easiest to cover rather than whatever matters.

Instead, **required coverage by category**:

| Category | Requirement |
|----------|-------------|
| Domain logic in `scoring`, `nlp`, evidence handling | Every branch, including every failure mode |
| Contract boundaries | Every boundary, both directions |
| Provenance propagation | Every transformation that touches an evidence-derived value |
| Failure modes in each `services/*/README.md` | Every row of every table |
| Framework glue, DTOs, config | Not required |

That last table in each service README is not documentation for its own sake: it
is the test list.

---

## 7. Anti-patterns

| Do not | Because |
|--------|---------|
| Assert an exact score value | Freezes an arbitrary number; every model improvement becomes a regression |
| Assert LLM output text | Non-deterministic and meaningless |
| Call a live external source | CI depends on a third party; violates rate-limit discipline |
| Fabricate market data in a fixture | Violates §9 and the fixture will eventually be mistaken for truth |
| Mock the thing under test | Tests the mock |
| Skip a flaky test | A flaky test is a bug report nobody has read |
| Test only the happy path | The failure modes are where this system's specification obligations live |
| Test with a single workspace | Cannot detect a missing tenant filter (ADR-005) |
| Hard-code a registry value as an enum in a test | Freezes a taxonomy that is meant to be extensible (Ontology V2 §14) |
| Assume a job runs exactly once | Delivery is at-least-once; a test that never duplicates a job does not test idempotency (ADR-004) |

---

## 8. Two-layer isolation testing (added in Mission 0.4)

ADR-012 added row-level security beside the repository filter. Testing two
layers that produce the same observable result needs one rule, because the
obvious mistake is to test them together and conclude that both work.

**Test each layer where the other cannot help.**

| Layer | Tested by | Why the other layer cannot mask it |
|-------|-----------|-----------------------------------|
| Repository filter | `repo.get(WORKSPACE_A, b_row)` raises `NotFoundError` | Runs under a correct tenant context, so RLS is satisfied and only the filter can reject |
| RLS policy | `SELECT * FROM …` with **no** `WHERE` clause | The filter is what is missing; if the result is still one tenant's, the database did it |

Two further rules follow:

1. **A schema-constraint probe must not be masked by a policy.** A `NOT NULL`
   test that inserts `workspace_id = NULL` can never satisfy an RLS `WITH
   CHECK`, so the policy fires first and the test stops measuring what it is
   named after. Those probes use `privileged_transaction()`, and the reason is
   written next to each one.
2. **A source-reading test is legitimate here.** `test_the_repository_still_filters_explicitly`
   asserts on the repository source, because with RLS enabled the *behaviour* of
   a query with and without its tenant filter is identical — which is exactly
   how a deleted filter would go unnoticed until someone ran a report with a
   privileged role.

## 9. Opt-in tests that cost money (added in Mission 0.4)

Real-provider smoke tests are skipped unless **both** an explicit flag and a
credential are present, and the guard itself is tested. The flag is separate
from the key because a developer with a key exported for other work has not
consented to spending money on every test run, and CI acquires secrets for
reasons unrelated to benchmarks.

The failure mode this prevents is specific: a suite that quietly became enabled
reports its problem as an invoice, weeks later, rather than as a red build.

## 10. Environment-dependent expectations (added in Mission 1.4)

Until Mission 1.4 the governance answer was the same everywhere: no source was
collector-eligible, so a test could assert `eligible == 0` and be asserting a
property. Condition verification made the answer depend on **what is deployed** —
which capabilities exist, which credentials are configured, what somebody has
recorded — and several tests that had looked like property assertions turned out
to be statements about one database.

They failed the moment `sros-source verify --apply` had been run, which is a bad
way to find out.

Three rules came out of fixing them, and they apply to anything whose answer can
legitimately differ between environments.

**Derive the expectation from the input, not from a remembered number.** The
orchestrator integration test now asks which gate *should* answer given what the
registry reported, instead of hard-coding `SOURCE-REGISTRY-GATE`:

```python
expected = "NO-COLLECTOR-IMPLEMENTED" if plan.eligible_source_ids else "SOURCE-REGISTRY-GATE"
assert acquisition.blocked_reason.startswith(expected)
```

**Compare two implementations on the same inputs.** The Python gate and the SQL
view are compared with the satisfaction the *database* holds
(`conftest.recorded_satisfied_keys`). Evaluating Python without it would compare
the same rule on different inputs and report a divergence that is really a
missing argument.

**Assert the behaviour, not the state it happened to produce.** "Every stored
condition is unsatisfied" was really "nobody has verified this database yet".
The test now forces every condition false, runs the loader, and asserts none was
set — which is the property that was always meant: *a catalog load can never
satisfy its own conditions.*

**Two absolutes were retired in Mission 1.5, and the sentence claiming them
outlived them.** It read: *"`collector_enabled` is false everywhere, and
`acquisition.raw_records` is empty."* Both stopped being true the moment a
collector was implemented and enabled, and a stale absolute in a testing strategy
is worse than a missing one — it tells the next reader to write an assertion that
will fail for a reason unrelated to their change.

What replaced them are **set relations**, which stay true as the system grows:

- no source outside `IMPLEMENTED_COLLECTORS` is enabled;
- no raw record exists for a source with no collector;
- no normalized record exists for a source with no normalizer.

## 11. Structural tests, and when they earn their keep (added in Mission 1.5)

Most tests here assert behaviour. The collector conformance suite also asserts
**shape**, and the distinction is worth stating because structural tests are easy
to write badly.

A behaviour test proves the collector went through the authorization gate on the
call it made. A structural test proves there is no second door for it to start
using next year:

```python
parameters = list(inspect.signature(WorldBankCollector.collect).parameters.values())
assert parameters[1].name == "context"
assert parameters[1].default is inspect.Parameter.empty
```

That is worth a test because the failure it catches is a *future* one -- somebody
adding a convenience overload, or a default that quietly makes the context
optional -- and no behaviour test would notice until something had already
collected without authorization.

Three rules keep them honest.

**Assert the property, not the current text.** An early version scanned the
collector's source for `build_authorization` and failed on the docstring that
explains why the name is absent. Asserting the module NAMESPACE instead is both
narrower and truer: the name has to be imported before it can be called.

**Exempt by name, with the reason next to it.** The "no public signature accepts
a URL" scan exempts `host_of`, which parses a URL and performs no request. An
unexplained exemption list is where a real escape hatch eventually hides.

**Zero, not "refused".** The most valuable assertion in that suite is
`transport.calls == []`. A gate that refuses after the request went out has
prevented nothing, and only a counting fake can tell the two apart.

## 12. Tests that change the deployment (added in Mission 1.5)

Two defects in this repository came from the same root, and both were found by
the suite written after the one that caused them.

A Mission 1.4 test called `sros-source enable world-bank` to assert a refusal.
When Mission 1.5 gave World Bank a collector, the call stopped being refused and
**enabled a real collector as a side effect**. A fixture then reset
`collector_enabled = FALSE` for *every* source in teardown, silently reverting a
deliberate operational decision.

The rules that came out of it:

- a test that needs the deployment in a particular state **puts it there and puts
  it back**, restoring the previous value rather than forcing a default;
- a test that asserts a refusal names a subject that will still be refused --
  Eurostat is eligible with no collector, so it carries that property now;
- a test that counts rows uses **its own workspace**. Workspace A holds real
  collected data since Mission 1.5, and counting there measures the environment
  rather than the behaviour under test.

## 13. Absolute counts, and why they keep going stale (added in Mission 1.6)

The same defect appeared a third time, in a place nobody was watching.

Mission 1.6's verification script asserted `research.claims == 0` and
`scoring.evidence == 0`, reading §44's "no Claims created" literally. It failed
against a freshly rebuilt database: 45 claims and 37 evidence rows were there,
created by the Mission 1.2 suite minutes earlier, all synthetic and none from
any source.

The assertion was wrong, not the system. **What §44 asks is whether
NORMALIZATION created any**, and that is a delta, not a count. The check became:
none created since the raw records were collected, none naming a source, none
belonging to the normalization session.

The general rule, now stated three times in this document under three different
disguises:

> An absolute count is a statement about a database. A relation between two
> observations is a statement about behaviour. Assert the second.

**Where an absolute IS still right**, and it is worth knowing the difference:
`nlp.signals` and `nlp.embedding_provenance` are asserted at zero, because
nothing in this system has ever produced one. The moment something does, that
assertion becomes a delta too — and it should be changed then rather than
weakened in advance.

A side finding, spun off rather than fixed here: the Mission 1.2 claim suites
write into the **seeded** development workspace and do not clean up, which is
the workspace rule in §12 not yet applied to them.

## 14. Testing a transformation that must not invent anything (added in Mission 1.6)

Normalization's failure mode is not "it crashed" — it is "it produced something
plausible". A parser that turns a missing value into `0`, an unclassified code
into a country, or an unknown unit into a guessed one produces records that look
perfect and are wrong, and no amount of behaviour testing on the happy path
finds it.

Three kinds of test carry that, and each catches something the others cannot:

**Constructor tests, for the invariants a value must never violate.**
`CanonicalValue(value=Decimal("0"), state=NOT_REPORTED)` raises. That constructor
is the single place the "missing became zero" bug would have to pass through, so
guarding it there is stronger than any number of assertions about outputs.

**Signature tests, for guarantees that are structural.** §46 does not ask that a
normalizer *happens* to preserve attribution; it asks that there be no API
through which one could drop it. A behavioural test would pass equally well
against a builder with an unused `attribution=None` parameter, so the signature
is asserted instead — the same move the collector conformance suite makes.

**Probing the validator, before believing it.** `validate_normalization.py`
enforces nine boundaries. It was run against **fourteen deliberate violations** —
each import form, each forbidden library, each forbidden table — and every one
had to fail the build before the validator was trusted. A guard that has only
ever run against clean code is a guard whose patterns have never been exercised,
which the gitleaks configuration in Mission 1.5 demonstrated four times over.

One more, from §39: **expectations are derived from the input.** No test and no
verification script writes a population figure down. They compare the normalized
value to the raw payload it came from, which is what "the transformation
preserved it" actually means — and which is why the first version of the revision
test failed for the right reason when a fixture's ordering changed.

## 15. Test data isolation — a standing rule (added in Mission 1.6.1)

Three incidents in one afternoon, all the same shape, none careless. The rule
that came out of them is short and is not negotiable:

> **A test must not mutate persistent seeded development data.**
>
> Seeded data may be read where that is justified. A test that needs to create,
> update or delete builds its own tenant graph — workspace, project, session —
> and removes exactly what it made.

`infrastructure/db/seed/0001_dev_workspace.sql` creates two workspaces. They are
shared by every suite and they hold real collected records. A test that writes
into one decides what other suites can observe; a test that deletes from one
destroys data somebody acquired.

### Reading is fine. Using the id is not writing.

A unit test that puts a seeded workspace's uuid into a task payload and asserts
the payload is refused never opens a connection. That is read-only in effect,
and seven modules do it. It is a latent hazard rather than a defect, and the
fixture guard is what keeps it latent.

### The guard, and why the leak check does not replace it

Two mechanisms, answering different questions:

| | Asks | Blind to |
|---|---|---|
| `run_pytest_suites.py` leak check | did the run **change** the database? | a fixture deleting from a seeded workspace that is empty *today* |
| `workspace_guard.disposable()` | may this fixture **point here at all**? | a write reaching the database through no fixture |

The second exists because of the third incident: an acquisition fixture deleted
acquisition rows from seeded workspace B in teardown for two missions, passing
every time, purely because B happened to be empty.

Call `disposable()` in the fixture that **creates or destroys**, not at each use
site. A guard you must remember everywhere is one you will forget somewhere.

### Fixtures restore only what they created

Never `UPDATE` every row, `DELETE` every row, or reset a flag everywhere unless
the test created all of it. Mission 1.5 found a teardown that set
`collector_enabled = FALSE` for every source and silently reverted an operator's
deliberate enablement; the fix was to read the previous value and put **that**
back. Prefer transaction rollback where the behaviour under test allows it —
`tenant_conn` does — and note that rollback cannot express "the second delivery
finds the work already done", which needs a committing fixture.

## 16. Cleanup assertions must consider the FK closure (added in Mission 1.6.1)

> **A guard that enumerates what must survive only covers the tables somebody
> already thought of.**

A cleanup ran inside a transaction asserting `opportunities = 0`, `raw = 6`,
`normalized = 6`, `project = 1`, and committed. It had also deleted 39 claims,
their revisions, their session observations, 36 evidence rows and their
independence groups — five tables the guard did not name, so five it silently
approved. The count it reported was what `DELETE` returned: rows matched
directly, not the closure.

No amount of care fixes that. The failure is in the *shape* of the check.

**Before a broad destructive action, derive the closure from the catalog:**

```bash
python infrastructure/scripts/fk_closure.py research.opportunities
```

It walks `pg_constraint` and reports every table a delete may reach, separating
rows **deleted** (`CASCADE`) from rows **detached** (`SET NULL`). The second
matters as much as the first: a row that survives with a nulled foreign key is
still a row the delete changed, and that is precisely how twelve records lost
their session link while every row count stayed the same.

Numbers worth knowing, all from this repository:

| Delete from | Reaches |
|---|---|
| `research.opportunities` | 6 tables |
| `acquisition.raw_records` | 5 tables — including `normalized_records` |
| `research.research_projects` | **17 tables** |

The last is the unscoped `DELETE` in `test_rls.py`. Nobody had looked at its
closure until after it had destroyed a session.

Assert over what the tool returns, not over a list typed by hand. The graph is
already in the database; a guard that asks it cannot be surprised by it.

---

## 17. Global state is watched too, and by content (added in Mission 1.7)

`test-data-isolation-audit-v1.md` §6 named a gap rather than closing it: the
post-suite leak check finds tenant tables by looking for a `workspace_id`
column, so `registry.*` — global platform metadata, no `workspace_id` anywhere
in it — was outside the check **by construction**. Three acquisition modules
mutate the registry.

`infrastructure/testing/registry_state.py` closes it, and two of its design
choices are the parts worth remembering.

### Count the content, not the rows

The failure this had to catch is count-stable:

```sql
UPDATE registry.sources SET collector_enabled = TRUE WHERE id = 'world-bank'
```

A row count does not move when a boolean flips inside a row, so the tenant
check's mechanism could not find this however carefully it was applied. Each row
is reduced to `to_jsonb(row)` minus its bookkeeping columns and hashed; a table
is the set of those hashes.

### Too strict is a failure mode, not the safe side

The instinct is that a stricter check is a safer check. It is not, and this one
proved it on its first real run: eight conditions came back "changed" after a
completely clean suite, because `satisfied_at` and `satisfaction_reference` are a
**projection of the append-only verification log** and move every time it grows.
`satisfied` — the governance fact — was identical in all eight.

A check that fails on every run is a check somebody deletes, which lands you back
at the permissive failure with extra steps. So the derived columns are excluded
and `satisfied` is not, and a test asserts that boundary from both sides.

Same reasoning gives `registry.source_condition_verifications` an explicit
exemption: it is append-only by design, so it may **grow**, may not shrink, and
may not have a row rewritten. One subset test covers all three.

### The two checks partition the tables between them

Neither keeps a list. The tenant check takes every table WITH a `workspace_id`;
this one takes every table WITHOUT. A table added by a future migration is
therefore watched by exactly one of them from the moment it exists, and a test
asserts that no table appears in both.

### What it found immediately

Not a test bug. `sros-source verify --apply` folds the git-ignored
`infrastructure/compose/.env` into its process and the pytest fixture did not, so
on a machine with `FRED_API_KEY` configured the two disagreed: the CLI recorded
FRED's credential condition `SATISFIED`, and the next `pytest` run recorded it
`UNSATISFIED` and quietly took FRED out of eligibility. Both were behaving
correctly; they were answering the same question in different environments.

The fix was to fold the same file in the fixture, so a verification means the
same thing whoever runs it. **The check earned its place before it had a green
run.**

---

## 18. A prose rule that nothing reads is not a rule (added in Mission 1.8)

`source-registry-v1.md` §1 rule 2 has said *"uncertainty is never permission"*
since Mission 1.0. It is stated in the specification, restated in the review
guide, and quoted in three mission reports.

Mission 1.7 approved a source with four of the six activities the assessed use
requires recorded `NOT_ADDRESSED`, on a review whose own notes described the
basis as *"the absence of a prohibition covering us plus the presence of a
documented API"*. The reviewer wrote the diagnosis and recorded the approving
state in the same document.

**The rule was never enforced by anything.** No validator read it, no test
asserted it, and the catalog was free to contradict it in a field nobody
compared against the prose.

### What the test has to assert

Not "pypi is not approving". That passes the day somebody approves a different
source the same way, which is exactly how the first one happened.

The property is over the whole catalog: *every* approving review grants *every*
materially required activity. It is written as a loop over sources with the
required set named once, so a new source is covered from the moment it is added.

### The list exists twice and is compared

The validator runs with nothing installed (ADR-009) and cannot import the test
module; the test cannot import the validator either, because the validator is a
script. So both name the six activities, and a third test reads the validator's
source and asserts the two lists are equal.

Two copies of one fact drift. Two copies plus a comparison do not — and this is
the same argument `source-registry-v1.md` §4 makes for keeping the Python and
SQL eligibility implementations separate and testing that they agree.

### Write the check so it fails first

This one was written against the catalog **before** the downgrades landed, and
it named all three offending sources and the exact activities each was missing.
A governance check that has only ever passed proves nothing about what it would
catch, and the cheapest moment to find out is before the data is corrected.

---

## 19. When a governance change moves a test's subject (added in Mission 1.9.2)

Mission 1.9.2 re-reviewed GDELT and turned eight passing tests red. None of them
was wrong when it was written, and none of them was a test somebody had loosened
— each was a **correct statement about a state the review deliberately left**.

```text
test_the_unimplemented_bulk_profile_authorises_no_host   the profile now has one
test_no_dataset_is_authorised_so_no_draft_could_be_built two now are
test_gdelt_has_no_dataset_entry_yet                      it has two
```

The temptation in this situation is to delete the assertion, because the thing it
asserted is no longer true. That loses the reason it existed.

### Rewrite in place, and say what moved

Every one of the eight was rewritten to assert the **new** truth and to carry a
docstring naming the old one and the decision that changed it. Mission 1.9's
comment said the bulk profile had no endpoint "so that adding one is a decision
somebody takes rather than a line somebody copies"; the replacement says review 3
*is* that decision and what it authorises is narrower than the placeholder's
name. A reader who lands on the test can tell a governance change from a
loosened check without leaving the file.

Four were also **renamed**, because a name that describes the old state is worse
than no name: `test_no_dataset_is_authorised_so_no_draft_could_be_built` became
`test_no_doc_api_resource_is_authorised`, which is what it now proves and is
still a real constraint — H-27 is open and nothing on that route is authorised.

### The three that were assertions about a mechanism, not a state

A different category, and they needed a different fix. `_baseline` in
`capabilities.py` builds a control descriptor that every rule in a scope should
allow; it left `rights_basis` unset for any source without a licence allowlist.
When the unestablished basis became a refusal, three capability conformance
checks failed — **correctly**, and for a reason unrelated to what they test.

The fix is to supply what the new rule needs so that the rule under test is still
the variable. The same applies to fixture descriptors: three cases in
`test_compliance.py` are about geography, trade exclusions and note markers, and
all three had a positive control that started failing on the basis instead. Each
now carries one, with a comment saying why it is there.

**The signal is which direction the failure runs.** A control case that starts
failing means a new rule reached further than intended, or that the control was
incomplete. A denial case that starts *passing* is the one to be frightened of,
and none did.

### Count nothing you do not mean to count

`test_both_rules_are_evaluated_not_short_circuited` asserted
`len(result.denial_reasons) == 2`. The behaviour it names — report every refusal
rather than the first — was working exactly as before; the number was stale
because a third rule now runs. It is now
`len(denial_reasons) == len(rules_evaluated)` with a `<=` on the rule names,
which is the property, and it was renamed to match. §13 of this document is the
same lesson and this is its fourth recurrence.

---

## 20. A live smoke test earns its keep when it finds what fixtures cannot (added in Mission 1.9.3)

Mission 1.9.3 wrote 105 tests for the GDELT WEB-NGRAM collector against fixture
files, and every one of them passed. The first contact with a real file failed.

```text
INVALID_RESPONSE: a row's NGRAM contains the observation-key separator '|'
```

`observation_key` joins its parts with `|` and **refused** any part containing
one. That rule was written in Mission 1.5, when every part was a source id, a
resource id, an ISO country code or a year — none of which can contain a pipe.
News text can, so GDELT publishes terms that do, and the parser was discarding an
entire 223,342-row file of legitimate observations because of our own key format.

**No fixture caught it, and no fixture was going to.** The fixtures were written
by someone who did not expect a pipe in a word — which is the same someone who
wrote the rule. A synthetic corpus reproduces its author's model of the source,
and that is exactly the blind spot a live test exists to cover.

### What this does NOT mean

It does not mean fixtures are weak. The 105 fixture tests cover truncated gzip,
amplification, extra fields, invalid UTF-8, negative counts and cancellation —
none of which a live test can produce on demand, and several of which would be
irresponsible to provoke against a third party. The two are complementary and
neither substitutes.

What it means is narrower and worth stating: **a fixture proves the parser
handles what its author imagined. Only real data proves what the source
actually sends.**

### The shape of the fix matters as much as the fix

The first instinct was to skip rows containing the separator. That would have
been the system silently dropping real observations to protect an internal
format — the failure this repository keeps naming from other directions.

The second was to move the separator. There is nowhere to move it to: **any
printable character can appear in a term.**

The third was to hash the parts, which removes the readability the key exists
for.

The answer was to escape, which keeps the guarantee (distinct part sequences
produce distinct keys) without deciding what a source is allowed to say. Every
part written before the change contains neither `|` nor `\`, so no committed key
moved — and a test asserts that, because "this refactor changed no existing
identity" is a claim worth checking rather than believing.

### Keep the live suite opt-in and cheap

One bucket, one resource, one narrow filter, nothing persisted, and no crawl for
a file that happens to exist. A smoke test that hunted for a working bucket would
be testing the hunt, and a smoke test that ran by default would be traffic to
somebody else's servers that nobody consented to.

---

## 21. The zero-dependency suite is a different environment, not a faster one (added in Mission 1.9.3)

A worker test asserted that `WebNgramJobPayload` has no field an authorization
could travel in. It imported the class to do so, passed locally, and failed in
CI:

```text
ModuleNotFoundError: No module named 'sros_acquisition'
```

`run_python_tests.py` runs the zero-dependency suites **with nothing installed**,
which is the whole reason ADR-009 exists: the contract, schema and governance
checks must keep working when a dependency environment is broken. A developer's
venv has every workspace package on the path, so the same script passes there for
a reason that has nothing to do with the code.

**Running the script is not the same as reproducing the condition.** The way to
check is to run it with an interpreter that does *not* have the workspace
installed:

```bash
python infrastructure/scripts/run_python_tests.py
```

— the system Python, not `.venv/Scripts/python`.

### The boundary rule said the same thing first

`service-boundaries.md` already forbids a service importing another service's
package. `sros_workers` reaches `sros_acquisition` at runtime, lazily, inside the
task body; its *tests* must not, and CI enforcing the dependency-free environment
enforced the boundary as a side effect.

The assertion did not disappear — it moved to the acquisition suite, where the
class lives and where importing it is not a boundary crossing. What stayed on the
worker side is the half that is genuinely about the worker: a smuggled
`authorization` key survives the payload merge and reaches a job that never looks
at it.

---

## 22. Testing a model change against real data you must not use (added in Mission 1.10)

Mission 1.10 changed the canonical model so a GDELT WEB-NGRAM observation could
be represented, and was forbidden from normalizing the two real records that
motivated it. That is an awkward shape to test and the resolution is worth
recording.

### Use the real records as a specimen, not as a fixture

The two RawRecords are copied into the test module as a literal:

```python
REAL_RECORDS = (
    {
        "gram_kind": "1gram",
        "date": "20260830091500",
        "lang": "ENGLISH",
        "ngram": "climate",
        "count": "55",
    },
    ...,
)
```

Copied rather than queried, for a reason that outlasts this mission: **a model
test that needed PostgreSQL would be skipped exactly where the model is least
exercised** — on a contributor's machine with no Docker, and in any environment
where the database is the thing that broke.

They are real values, not invented ones, and that matters here: the point of the
exercise is that the model can hold *what the source actually published*, and a
handwritten specimen would have been shaped by the same expectations that shaped
the model.

### Assert the refusals, not only the representations

A model that can express a truthful record is half the guarantee. The other half
is that it **cannot** express an untruthful one, and that half is where the
assertions earn their keep:

```text
an aware bound under NOT_ESTABLISHED   -> refused
a naive bound under ESTABLISHED        -> refused   (the old rule, unchanged)
a canonical tag with no mapping        -> refused
a mapping state with no tag            -> refused
```

Each pairs a positive case with its negative. A constructor that only ever
refused would pass every negative test while being unusable, which is the failure
`_control_passes` exists to catch one layer down.

### Assert the absences by serialising

Three of this mission's guarantees are about things that must **not** appear —
no geography, no classification, no invented timezone. Those are cheapest and
most reliable to assert over the serialised payload rather than field by field:

```python
serialised = canonical_json(observation(row).to_payload()).lower()
for classification in ("theme", "entity", "topic", "keyword", "intent"):
    assert classification not in serialised
```

A field-by-field check passes while a *new* field carries the thing forbidden.
The serialisation check does not.

### The change that must not change anything

The one assertion this mission most needed was that an existing payload
serialises **byte-identically**:

```python
assert year_period("2018").to_json() == {...literal...}
assert "timezone_state" not in payload
```

A literal rather than a round-trip, because a round-trip through the same code
that changed would agree with itself. This is the assertion that made the
conditional key a deliberate design decision rather than an oversight discovered
later by a hash mismatch.

---

## 23. Grepping prose is not a structural test (added in Mission 1.10.1)

Mission 1.9.3 recorded a version of this as §20, and Mission 1.10.1 walked into
it twice in one afternoon. It is worth stating as its own rule.

The GDELT normalizer must never convert a timezone and must embed no language
table. Both are structural properties, and the obvious way to assert one is:

```python
source = pathlib.Path(adapter.__file__).read_text()
assert "astimezone" not in source  # fails
assert "ISO 639" not in source  # fails
```

Both failed, and **both failed on the docstring that explains the rule**. The
module says *"nothing here calls `astimezone`"* and *"a distinction ISO 639 draws
that CLD2 does not"* — the sentences a reader most needs are the ones the grep
trips over.

### The failure mode is worse than a red test

The natural next move is to weaken the assertion — strip the docstring, exclude
comments, drop the term from the list. Each of those makes the check a little
less true while keeping it green, and after two or three rounds nobody trusts it
enough to add a term to.

### Assert over the AST

```python
tree = ast.parse(source)
called = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
assert "astimezone" not in called

constants = {
    n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
}
assert "en" not in constants
```

This is stricter, not looser: it catches `getattr(dt, "astimezone")` written to
dodge a grep, and it cannot be defeated by prose. The three shapes worth reaching
for are **imports** (does this module depend on a network client or a model),
**attribute names** (does it call this), and **string constants** (does it embed
this datum).

### When a substring scan is still right

Over the **serialised payload**, not the source:

```python
serialised = canonical_json(draft.payload).lower()
for classification in ("theme", "topic", "entity"):
    assert classification not in serialised
```

There is no prose in a payload, and a field-by-field check would pass while a
*new* field carried the thing forbidden. The rule is about what is being scanned:
**source text has explanations in it; data does not.**

---

## 24. A refusal test must assert WHY it was refused (added in Mission 1.11)

Migration 0012 added twelve CHECK constraints to `nlp.signals`, and the way to
believe a constraint is to watch it refuse something. The probe was a dozen
INSERTs inside rolled-back transactions, each expecting a failure:

```python
try:
    conn.execute(insert_sql(row), params)
    inserted = True
except Exception:
    inserted = False
assert inserted is expected
```

Ten of the twelve cases reported `ok` on the first run. All ten were wrong. The
fixture omitted `correlation_id`, which is `NOT NULL`, so **every** insert failed
before reaching any CHECK -- and a test that only asks "did it fail" cannot tell
a constraint working from a fixture that never got there.

### What exposed it

The two cases that expected an insert to **succeed**. A suite made only of
refusals has no way to notice that everything refuses.

### The rule

```python
except psycopg.Error as exc:
    actual = exc.diag.constraint_name
assert actual == "signals_observed_at_requires_comparable_instants_check"
```

- **Name the expected constraint**, not the exception class. `IntegrityError`
  covers a null violation, a foreign key, a unique conflict and every CHECK in
  the table.
- **Include at least one positive case** in any refusal-shaped suite. It is the
  only case that fails when the fixture is broken rather than the rule.
- The same applies above the database: `test_signal_model.py` asserts
  `caught.exception.refusal.reason`, never that "a `SignalRefusedError` was
  raised" -- seven refusal reasons share one exception type, and six of them
  passing for the wrong reason would look identical to six passing.

### Where a `ValueError` belongs instead

The Signal model splits two things a single exception type would blur: a
`SignalRefusedError` means **the data** does not support a derivation, which is an
ordinary outcome; a `ValueError` means **the caller** is wrong -- a confidence
out of range, a direction with no order behind it, a lexical scope carrying a
geography. Tests assert the split, because a caller error that arrives as a
refusal would be logged as "no signal today" and never fixed.

---

## 25. A database CHECK is a test you cannot forget to write (added in Mission 1.11.1)

Migration 0013 gave the derivation run log two arithmetic constraints, written
as belt-and-braces:

```sql
CHECK (groups_derived + groups_refused <= groups_considered)
CHECK (records_contributed + records_excluded <= records_considered)
```

The second one failed on the third integration test, and the defect was real.
The job counted contributors by summing over drafts:

```python
for draft in outcome.drafts:
    contributed += len(draft.contributed)
```

Over 2018/2019/2020 that produces two signals and counts **four** contributors
from **three** records, because 2019 belongs to both pairs. The run would have
reported more contributing records than it read.

### Why no unit test would have caught it

Every extractor test asserted the *signals*, which were correct. The counters
are diagnostics — nobody branches on them — so nothing asserted their
relationship to each other, and the wrong number would have sat in the run log
being quietly believed by whoever read it during an incident.

The constraint asserted the relationship because the relationship is what makes
the numbers mean anything. `records_contributed` now counts **distinct** records,
and a record excluded from one signal while contributing to another counts as a
contributor.

### The rule

**When two stored numbers have an arithmetic relationship, put it in a CHECK.**
Not because the code is expected to be wrong, but because:

- it is checked on every row forever, including rows written by code that does
  not exist yet;
- it fails at the write, naming the constraint, rather than surfacing as a
  number somebody mistrusts a year later;
- it costs one line, and the alternative is a test per producer.

The same argument the tenancy composite keys make: a guarantee enforced where
the data lands does not depend on every future caller remembering it.

---

## 26. Rewrite a superseded assertion; never weaken it (restated in Mission 1.12)

Mission 1.10.1 set the convention and Mission 1.12 is the first time an
assertion was superseded because the WORLD changed rather than because the code
did. Two tests said, correctly, that GDELT had no established ordering:

```python
def test_h32_blocks_source_relative_order_for_gdelt(self):
    ...  assertEqual(withheld, {SOURCE_RELATIVE_ORDER})

def test_no_source_is_order_certified(self):
    ...  assertEqual(dict(ORDER_ESTABLISHED_WITHOUT_TIMEZONE), {})
```

H-32 closed on first-party evidence, and both became false.

### What not to do

Delete them, or loosen them to `assertIn`/`assertTrue` so they keep passing.
Either leaves the suite quieter than it was: the first loses the record that the
question existed, and the second turns a fact into a shape check.

### What was done

Each was **rewritten in place**, keeping the test's position in the file, with a
docstring naming the old truth and what moved it:

```python
def test_h32_grants_source_relative_order_to_the_reviewed_stream(self):
    """Until Mission 1.12 this asserted the opposite, and correctly. …"""
```

and the constraints the old assertion was really protecting were promoted into
tests of their own — that a certification states its basis, names its resources
rather than matching a prefix, grants ordering only, and is refused when it
covers everything or cites nothing.

**The suite got larger, not smaller.** One assertion that said "nothing is
certified" became six that say what a certification may and may not be. That is
the test for whether a superseded assertion was handled properly: the
replacement should be harder to satisfy than the original, not easier.

