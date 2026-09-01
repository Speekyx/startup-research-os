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

---

## 27. The second time a CHECK caught the model, not the code (Mission 1.12.1)

`testing-strategy.md` §25 recorded the run log's arithmetic constraints catching
a double-counted contributor. Mission 1.12.1 hit the other one, and the lesson
is different enough to be worth its own entry.

```sql
CHECK (groups_derived + groups_refused <= groups_considered)   -- migration 0013
```

It looks like arithmetic and it is a **claim about the domain**: that a candidate
group either derives or refuses. That was true of the first two extractors,
because each group produced one outcome. The third pairs *within* a group, and
the first real derivation produced one signal and one refusal from one group.

### The difference from §25

In §25 the code was wrong and the constraint was right. Here **the code was right
and the constraint was wrong** — the counters already meant "groups that produced
at least one", which is the honest definition, and the constraint had encoded an
assumption nobody had noticed making.

### What that changes about writing them

A constraint over two counters is a model of how the counters relate, and a model
can be falsified by a feature. So:

- **Write the invariant you can defend, not the tightest one that passes today.**
  `derived <= considered AND refused <= considered` was always true;
  `derived + refused <= considered` was true by coincidence of having two
  extractors that behaved the same way.
- **When one fails, ask which side is wrong.** The reflex is to fix the code. In
  §25 that was right; here it would have made the counters lie to keep a
  constraint that was itself the error.
- **Fix it forward.** Migration 0015 replaces 0013's constraint and 0013 is not
  edited, so the record of what was believed and when survives.

Both incidents argue for the same practice from §25 — put arithmetic
relationships in a CHECK — and this one adds the caveat that makes it safe: the
CHECK is a hypothesis, and a failure is evidence about the hypothesis as much as
about the write.
## 28. A CHECK that evaluates to NULL is not a CHECK (Mission 1.13)

§25 and §27 both argue for putting invariants in database constraints. Mission
1.13 found the way that advice fails: a constraint can be syntactically fine,
semantically intended, applied to the database, and enforce **nothing**.

Migration 0016 added this to `research.claims`, meaning "all three of the
interpreter fields, or none of them":

```sql
CHECK (
    (interpreter_id IS NULL AND interpreter_version IS NULL
                            AND interpretation_kind IS NULL)
 OR (length(btrim(interpreter_id)) > 0
     AND length(btrim(interpreter_version)) > 0
     AND interpretation_kind IS NOT NULL)
)
```

With `interpreter_id = 'x'` and `interpreter_version = NULL`:

| Term | Value |
|------|-------|
| first branch | `false` — `interpreter_id` is not null |
| `length(btrim(NULL)) > 0` | **NULL** |
| second branch | `NULL` — `NULL AND anything` is `NULL` |
| whole expression | `false OR NULL` → **NULL** |

**A CHECK rejects a row only when its expression is FALSE.** NULL is accepted.
So half an interpreter identity — a version nobody could resolve — was written
without complaint, by a constraint whose name says it prevents exactly that.

### How it was found

Not by review. By a probe written to *disbelieve* the constraint: nine cases,
each stating the constraint name it expected, run inside a transaction that
rolls back. The half-identity case expected
`claims_interpreter_complete_check` and got `ACCEPTED`.

This is the §24 practice paying off a second time. A probe asserting only "the
insert failed" would have passed here too — because the insert did not fail, and
a test that tolerates either outcome tolerates this one.

### What to do about it

- **Any CHECK touching a nullable column needs a NULL row in its probe.** Not
  the all-null row, which usually works: the *partially* null row, which is
  where three-valued logic bites.
- **Prefer functions that cannot return NULL for the arity part.**
  `num_nonnulls(a, b, c) IN (0, 3)` returns an integer whatever the inputs are.
  Migration 0017 is that fix, forward-only — 0016 stays as written, because a
  migration is never edited after it has been applied.
- **Guard each nullable test so NULL short-circuits to TRUE**, explicitly:
  `(x IS NULL OR length(btrim(x)) > 0)`. The intent is then readable rather than
  reconstructible from the three-valued truth table.

The general form: **a guard that cannot fail is worse than no guard**, because
the absent guard is visible in review and the silent one is not.

## 29. Test a guard against the example that motivated it (Mission 1.13)

The interpretation contract forbids an `OBSERVED` claim from asserting a market
reading of a measurement. The guard is a vocabulary check, and the mission brief
supplied its own example of the failure: *"The German SaaS market is growing"*
derived from population arithmetic.

The vocabulary list contained `market for`. The example says `market is`. The
guard passed the sentence it exists to catch, and every other test in the suite
was green.

The test suite caught it because one test used the brief's sentence **verbatim**
rather than a sentence invented to exercise the list. Had the test been written
from the implementation — picking a phrase known to be in the list — the suite
would have reported a working guard.

### What that argues for

- **Write at least one case from the specification's own wording**, before or
  without looking at the implementation. A test derived from the code tests that
  the code does what it does.
- **A guard that misses its motivating example is worse than no guard**, for the
  §28 reason: it advertises a protection nobody re-checks.
- **When the guard is wrong, widen the guard.** The reflex is to adjust the test
  sentence until it matches the list. That is fixing the thermometer.
- **State the cost of widening in the code.** The bare word `market` now refuses
  a faithful restatement of a metric whose published title contains it
  (`CM.MKT.LCAP.CD`, "market capitalization of listed companies"), so a test
  records that case and the comment says what to do instead — restate by metric
  id. An unstated cost is rediscovered as a bug.

## 30. A guard whose subject is arbitrary text needs an exemption (Mission 1.13.1)

§29 recorded a vocabulary guard that missed its own motivating example, and
widening it. Mission 1.13.1 built the interpreter that guard protects, and hit
the failure on the other side.

The guard forbids market vocabulary in an `OBSERVED` claim. One of the three
templates restates a **GDELT lexical term**, and a GDELT term is arbitrary text
from a news corpus. `market`, `demand`, `pain`, `opportunity` and `interest` are
all ordinary English words that appear in news. So:

> `The GDELT Project reported that the term "demand" appeared 12 more times…`

is the most faithful restatement available, and the guard refused it.

### The shape of the mistake

The guard was checking **the whole statement** when what it is about is **the
interpreter's own prose**. A quoted source value is data being reported; the
sentence around it is the claim being made. Conflating them meant the guard
policed the source's vocabulary instead of ours — and a source does not get a
say in what our claims may assert, in either direction.

### What that argues for

- **A guard over generated text needs to know which spans it generated.** Here
  every template puts source-supplied values in double quotes and its own prose
  outside them, and the guard strips quoted spans before tokenising. The
  convention is enforced by review of three template functions, which is small
  enough to hold.
- **Tokens, not substrings.** The same pass replaced `term in text.lower()` with
  whole-token matching. `supermarket` and `marketing` are not `market`; the
  metric id `SP.POP.TOTL` is three tokens, none of them vocabulary. A guard with
  false positives gets loosened until it stops guarding, which is §29's failure
  arriving by a slower route.
- **Test the exemption with words that are actually forbidden.** Three tests
  build Signals whose term is literally `demand`, `market` and `pain` and assert
  a claim is produced. Testing the exemption with a harmless word would prove
  nothing.

The general form: **a guard needs to distinguish what the system asserts from
what the system quotes**, and the distinction has to be structural, because the
source will eventually publish every word on the list.

## 31. Probe the validator, not only the code it validates (Mission 1.13.1)

`validate_claims.py` fails the build when the interpretation layer imports a
model, constructs a non-`OBSERVED` claim type, reads a canonical language tag,
converts a timezone, writes a later-stage table or names an unregistered signal
type. It printed eleven `ok` lines on the first run.

Eleven `ok` lines is what a validator that checks nothing also prints.

So a probe applies **eleven deliberate violations** — one per rule — to the real
files, runs the validator, and restores them. All eleven were caught. Without
it, the AST-walking checks would have been believed on the strength of passing,
which is the §28 failure applied to a script instead of a constraint.

Two details worth keeping:

- **Mutate the real file, not a copy.** A probe against a fixture proves the
  checker works on fixtures. The restore goes in a `finally`, and the run is
  verified clean before and after.
- **Assert the probe's own edit applied.** A `str.replace` that matches nothing
  returns the original string, the validator passes, and the case reports `ok`
  for having changed nothing. Each case compares mutated against original first
  and fails loudly when they are equal — the same "measuring nothing" failure
  §24 found in a constraint probe, in a different costume.

### The probe found its own bug first

The probe located the repository root by walking up from `__file__` looking for
`.git`. It lives in a scratch directory outside the repository, so it walked to
the filesystem root and spun there — `Path("C:/").parent` is `Path("C:/")`, so
the loop never terminated. It produced no output and looked like a slow test.

An ascent that can fail needs a stop condition, and "resolve the repo root" is
better answered by asserting the working directory is one.

## 32. A test that asserts a value can become the review it was testing (Mission 1.14)

Mission 1.14 built the machinery for reviewed reliability and deliberately
established **no assessment**: a reviewer is a person, and the mission forbids a
model being the epistemic source of one.

The suites still need assessments to exercise. Every one of them carries a
number, and every number is a fiction — `0.5`, `0.6`, `0.7` — chosen because the
resolver needs something to return.

The hazard is specific and slow: a number in a test fixture looks exactly like a
number somebody reviewed. Six months later, `reliability=0.6` beside
`source_id="world-bank"` in a test file is indistinguishable from a finding,
and the natural next step is to lift it into a seed.

### What the suites do about it

- **The fixture says so, at the point of the number.** `"A FIXTURE VALUE. Not a
  judgement about World Bank."` — on the line, not in the module docstring
  somebody skims past.
- **The live probes use a resource that does not exist.** `indicator/PROBE.ONLY`
  and `probe_only_proposition` cannot collide with a real scope, so a probe row
  that escaped its rollback still could not be resolved against real evidence.
  A probe using the real scope would be one committed transaction away from
  being a review.
- **A test asserts the production count is zero.** `test_no_assessment_exists_in_production`
  fails the moment an assessment appears without a mission behind it. It is the
  cheapest possible guard against a fixture becoming a fact.

### The general form

**When a test must supply a value that the system treats as authoritative, the
test has to say it is not.** The same applies to a calibration constant, a
half-life, a threshold — anything a reviewer would otherwise have to establish.
The failure is not that the test is wrong; it is that the test is *right* and
gets read as evidence.

## 33. Narrowing a guard's subject needs an exhaustiveness check (restated, Mission 1.14)

§19 covers what to do when a governance change moves a test's subject, and
Mission 1.13.1 applied it to `validate_signals.py`, which was scanning a package
that had grown a second layer: the subject was named rather than the rule
relaxed, with an exhaustiveness check so the narrowing could not grow by adding
files. Mission 1.14 hit the mirror image and did **not** need to narrow
anything, which is worth recording as the case that went right.

`validate_evidence_aggregation.py` asserts that **no registered source id appears
anywhere in `packages/evidence-aggregation/`** — the guard that keeps source
identity out of the mathematics. A reliability resolver necessarily matches on
source and resource.

The tempting move was to relax the guard for one new file. Instead the resolver
went into its own package, `packages/evidence-reliability`, on the same side of
the seam as the existing row adapter. The aggregation guard is untouched, and
the resolver got its **own** no-source-id test — asserting that no *literal*
source id appears in it either, since it matches data against data.

The rule this suggests: **when a guard blocks correct new code, first ask
whether the code is on the right side of the boundary the guard defends.**
Narrowing the guard is the second option, not the first, and it costs an
exhaustiveness check to stay honest. Moving the code costs neither.

## 34. A review is tested against its record, never against the source (Mission 1.15)

Mission 1.15 reviewed nine sources by retrieving their governing documents.
Two of those retrievals failed because the host would not serve to the review
environment at all — Reddit and Stack Exchange, both high-value, both left
exactly where they were.

That failure mode is the argument for a rule the registry suites have followed
since Mission 1.0 and which had not been written down: **a source-review test
asserts properties of the recorded review, and never contacts the platform.**

If `test_demand_side_expansion.py` fetched Y Combinator's terms to check that
Hacker News is `RESTRICTED`, the suite would fail whenever YC was slow, whenever
CI ran from a blocked network, and whenever the document moved — none of which is
a defect in the catalog. Worse, it would *pass* while the recorded review said
something else entirely, because it would be testing the world rather than the
record.

**Retrieving the document is the review. The test checks that the review says
what the reviewer found.**

### What that makes testable

Properties the record must have, none of which needs a network:

- a verdict that changed carries evidence with a URL, a finding and a retrieval
  time;
- a `RESTRICTED` verdict names at least one activity as `NOT_PERMITTED` — it
  rests on a finding rather than an absence;
- an unreachable source gained **no** review version, because a failed retrieval
  is not evidence;
- superseded versions still say what they said: Pinterest v1's `NOT_ASSESSED` and
  v2's `NOT_PERMITTED` are different claims and both survive;
- a blocked source records coverage and is still not counted as usable.

### The assertion that had to get stricter

One test checked that Pinterest's evidence mentioned storage, by looking for
`"store"` in the finding. The finding says *"storing"*, so it failed — and the
tempting fix was to match the stem `"stor"`.

That would have made the test pass on any prose that *mentioned* storage,
including a finding that said storage was permitted. It now matches the verbatim
clause the verdict turns on: *"call the API on each access"*. A test over
evidence text should match what the document actually said, not the topic it was
about.

## 35. An unread document must stay visibly unread (Mission 1.15.1)

§34 established that a source-review test asserts properties of the recorded
review rather than contacting the platform. Mission 1.15.1 found the case that
makes the rule sharper: **the document the whole review turned on could not be
read at all.**

TED's legal notice names its governing instrument — Commission Decision
2011/833/EU — and links its canonical EUR-Lex address. Five first-party URL forms
for that Decision each returned an empty body. So the review recorded a grant
whose *scope* is defined in a document nobody has opened.

That is a specific hazard. Six months on, a reader sees a review citing a named
legal instrument with a canonical URL and reasonably assumes somebody read it.

### What the suite does about it

- **The failure is stored as evidence**, with `section_reference` set to
  `"Retrieval failure"` and the finding stating "empty body". A test asserts both.
  The document appears in the evidence list *because* it could not be read, which
  is the opposite of the usual reason and needs to be unmistakable.
- **A test asserts no evidence URL is a search engine.** A search restricted to
  EU domains returned a summary describing the Decision's articles, and it was
  the one thing in the mission that would have closed the question if treated as
  evidence. The assertion is over the recorded URLs, so the temptation cannot be
  yielded to silently later either.
- **A test asserts the activity assessments are byte-identical between versions.**
  A re-review that could not close its question must not quietly move findings it
  did not re-establish. `v1.assessments == v2.assessments` is one line and it
  catches the whole class.

### The general form

**When a review depends on a document that could not be retrieved, the record has
to say so at the point where the document is cited** — not only in prose that a
later reader may skim. A citation is normally a claim that somebody read the
thing; here it must carry the opposite claim, and only a structured field can do
that reliably.

The corollary is a rule about direction: a mission whose stated goal is to *close*
a question needs its strongest tests on the path where the question stays open.
The failure mode is not writing a false finding — it is letting an unresolved
question quietly acquire the appearance of resolution.

## 36. A local snapshot is not an invariant (Mission 1.15.1)

§32 recorded that a number in a test fixture becomes indistinguishable from a
reviewed finding. This is the same failure with the direction reversed: **a
number that IS a finding, written into a test as though it were a rule.**

Mission 1.15.1's brief asked that the production rows be unchanged — 12
RawRecords, 12 NormalizedRecords, 7 Signals, 7 Claims, 7 Evidence. The obvious
way to check that is to assert those counts, so that is what the suite did.

It passed locally and failed on the first CI run, on `assert 0 == 12`.

### Why it was wrong even where it passed

Those counts describe **one developer's database**. A fresh CI database holds
none of them; a second developer's holds whatever they collected. Encoding them
as assertions makes the suite pass or fail on *how much data the runner happens
to have*, which is not a property of the code under test.

Worse, it would have been read later as an invariant. A test asserting
`raw_records == 12` looks like the system guarantees twelve.

### What replaced it

Only the assertions that hold in **every** environment, because they follow from
the code rather than from history:

```text
zero raw records with source_id = 'ted-eu'     -- no TED collector exists
zero normalized records for TED                -- same
zero reliability assessments                   -- this mission is not that process
zero opportunities, zero embeddings
```

"Unchanged" is a property of a **run**, not of a row count, and the pytest
post-suite watcher already asserts it properly: it digests every tenant and
global table before and after and reports any difference. The suite did not need
a second, worse implementation of a check that already existed.

### The general form

**When a brief states expected numbers, ask whether they are facts about the
system or facts about the environment.** Facts about the environment belong in
the report, where they are findings. Facts about the system belong in tests. A
count of collected rows is almost always the first kind, and the giveaway is
that it would change if somebody ran a collector — which is not a regression.

## 37. A review test must name the version it is testing (Mission 1.15.2)

Mission 1.15.2 appended TED review v3 and **seven tests failed** — five from
Mission 1.15.1's suite and two from Mission 1.15's. Every one of them was
correct when written and every one of them was wrong by then.

The cause is one habit:

```python
review(catalog, "ted-eu")  # "the current review" -- moves under you
review(catalog, "ted-eu", 2)  # the review that mission established
```

Mission 1.15.1's suite asserted that `model_processing` was `NOT_ADDRESSED` and
that five granted activities did not make six. Both were true of v2 and both
became false when v3 read the governing Decision and granted the sixth.

### Why the fix is pinning, not deleting

The failing assertions record what a specific review *found*, and an append-only
history is worth nothing if nothing checks that superseded versions still say
what they said. Deleting them would remove the only mechanical guard against v2
being quietly edited later; pinning them to v2 keeps the guard and lets the
current state move.

So the rule has two halves:

- **A finding is asserted against its version.** *"v2 recorded
  `NOT_ADDRESSED`"* stays true forever and is worth protecting.
- **A durable property is asserted against the current review.** *"a blocked
  source names what is missing"* must hold at every version, and pinning it to
  one would stop it protecting anything.

Each of the seven was re-read and sorted into one of the two. Two acquired a
companion test on the current review, because the property was durable and the
original assertion had merely happened to be specific.

### The failure this prevents

Without the split, the pressure at every re-review is to relax the old
assertion until it passes — and the easiest relaxation is to stop asserting the
old finding at all. That is how an append-only history becomes an append-only
history that nobody checks.

The tell is a test whose name describes a *state* rather than a *version*:
`test_five_activities_granted_still_does_not_make_six` is a claim about a moment.
Renaming it `..._at_v2` was most of the fix.

---

## 38. A structural guard must not match its own source (Mission 1.15.3)

`test_ted_database_right.py` needed one assertion: **no test in this file
reaches the network**, because the retrieval *was* the review and a suite that
re-fetched `data.europa.eu` would go red on the Publications Office's uptime
rather than on the catalog.

The first spelling was a substring scan:

```python
for forbidden in ("requests.", "httpx.", "urllib.request", "urlopen", "socket."):
    assert forbidden not in source, forbidden
```

**It failed on its own list.** The file contains the string `"requests."`
because the check contains the string `"requests."`.

This is §23's lesson arriving a third time — after the normalization guard and
after Mission 1.13's interpretive-vocabulary guard, which refused the example
`§3` used to explain itself. The pattern is stable enough to state as a rule:

> **A guard expressed over a file's TEXT eventually matches the text that
> explains the guard.** Express it over the AST instead.

The fix walks `ast.Import` and `ast.ImportFrom` and checks module names. That
version cannot match its own literals, and it is also *stricter*: it catches
`import httpx as h`, which the substring scan for `"httpx."` would have missed.

### Why the tempting fix is the wrong one

The obvious repair is to obfuscate the list — split the strings, or add an
exclusion for the line the check lives on. Both make the guard weaker in the
same way: they teach the next person that the way past a structural check is to
edit the check. **The check was right and the mechanism was wrong.**

### The tell

A guard is text-based and needs replacing when you cannot write a comment
explaining it inside the file it guards.

---

## 39. Assert against normalised text, not against line breaks (Mission 1.15.3)

The same suite asserts that the prepared clarification request contains no legal
conclusion:

```python
assert "contains no legal conclusion" in PACKET.read_text().lower()
```

It failed, and the document said exactly that. Markdown wraps at 80 columns, so
the phrase was split across a newline between `no` and `legal`.

A raw-text assertion over prose finds a sentence only when the author happened
to fit it between two newlines. That makes it a **reformatting detector**: it
goes red when somebody rewraps a paragraph and green when they do not, and
neither outcome says anything about the content it claims to check.

The suite routes every document assertion through one helper:

```python
def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split()).lower()
```

**Cheap, and it removes a whole class of false failure** that would otherwise
train contributors to treat a red documentation test as noise.

---

## 40. A summary must not be able to become evidence (Mission 1.15.4)

Mission 1.15.4 arrived with a file describing a written reply from the
Publications Office that would have closed H-36. The file was a user
transcription and said so in its own second paragraph.

Excluding it was easy. **Making the exclusion durable was the test problem**,
because nothing in the suite could tell the difference between a real operator
response and a paraphrase of one — both would arrive as an
`OPERATOR_CORRESPONDENCE` evidence row with a title and a finding.

The guard chosen is blunt and it is right:

```python
def test_no_source_at_all_carries_operator_correspondence_yet(catalog):
    for source in catalog.sources:
        for past in source.review_history:
            for item in past.evidence:
                assert item.document_type is not PolicyEvidenceType.OPERATOR_CORRESPONDENCE
```

**Zero, across the whole catalog, at every version.** Not "TED has none", and not
a heuristic about what a real response looks like.

### Why the blunt version is the good one

A test that tried to *validate* an operator response — checking for a sender, a
date, a quoted excerpt — would be a spec for forging one. This test makes no such
claim. It says the registry contains none today, so **the first one is a diff**:
somebody adds it deliberately, a reviewer sees this test go red, and the red is
the conversation.

It is a **tripwire, not a validator**, and tripwires are the right shape when the
thing you are guarding against is a person in a hurry rather than a bug.

### The tell

Reach for this shape when a category of evidence is powerful, rare, and
impossible to verify mechanically. Deleting the assertion has to be the cheapest
way past it, and it has to be visible when someone does.

---

## 41. A finding pins to its version — the third time (Mission 1.15.4)

Ten assertions in `test_ted_database_right.py` failed when review v5 landed.
Every one had been written against `review(catalog, "ted-eu")` and every one was
recording something Mission **1.15.3** established.

This is §37 exactly, and it has now happened at v3, at v4 and at v5. The fix was
the same each time — pin the finding, leave durable properties on the current
review — and the repetition is itself the finding:

> **A review-backed test defaults to the wrong thing.** `review(catalog, id)`
> reads naturally and is almost always the mistake, because most assertions in a
> review suite are about what a particular review FOUND.

The habit worth forming is to write the version first and drop it only when the
property is genuinely durable — the opposite of what the API's convenience
suggests. Mission 1.15.4's own suite was written that way and needed no repinning
for the version it introduced.

---

## 42. A fixed timestamp compared against a real clock is a snapshot

Seven database tests in `test_world_bank_normalizer.py::TestPersistence` began
failing at **09:00 UTC on 2026-08-31** and would have failed for ever after:

```text
psycopg.errors.CheckViolation: new row for relation "normalized_records"
violates check constraint "normalized_records_normalized_after_collection_check"
```

The constraint is `CHECK (normalized_at >= collected_at)` and it is correct. What
was wrong is the pair either side of it:

| | |
|---|---|
| `NORMALIZED_AT` | a fixed `2026-08-31 09:00 UTC` in `normalization_fixtures.py` |
| `seeded_raw` | runs the **real** collector, which stamps `collected_at` from the real clock |

For eight months the constant was in the future and everything passed. The wall
clock reached it, and from that instant every `seeded_raw` record was collected
*after* the moment the tests claimed to normalise it.

### Why it hid for so long, and why CI did not catch it

CI seeds a **fresh** database on every run, so it exercises the same code — but
the failure is not about database state, it is about the clock, and CI's clock
crossed the threshold in the same hour a local run did. It went red on the next
run. **A test whose failure date is in the future is invisible to every run
before that date**, which is what makes this class worth naming rather than just
fixing.

### The fix

Inside `TestPersistence`, derive the time instead of pinning it:

```python
def _persist_at(*records) -> datetime:
    return max([NORMALIZED_AT, datetime.now(UTC), *(r.collected_at for r in records)])
```

Computed **once per test** and reused, so nothing drifts between two calls in one
test — `_revise` moves `collected_at` a day forward on purpose, and that record
has to be passed in rather than assumed.

**The offline tests keep the constant**, and should: they pair `NORMALIZED_AT`
with the fixed `COLLECTED_AT`, and determinism is worth more there than
clock-independence. The rule is not "never use a fixed timestamp".

### The rule

> **A test timestamp may be absolute only when absolute time is the subject of
> the test. Where temporal ORDERING is the invariant, fixture timestamps must be
> derived from one another or from a deterministic test clock.**

Or, shorter: **a fixed timestamp compared against a real clock is a snapshot, not
an invariant.**

This is §36's lesson — *a local snapshot is not a test invariant* — in the time
dimension. There it was row counts from one database; here it is an instant from
one afternoon. Both read as facts about the world and are facts about the moment
the test was written.

### The tell

A constant that must be *later than* something the test does not control. If a
fixture calls real code that reads a clock, no literal on the other side of the
comparison is safe.

### The guard, and how it was believed (Mission 1.15.4.1)

Four tests in `TestTheFixtureCannotExpire`. None waits for real time: the
advancing clock is simulated by moving the RECORD forward, which is the same
relationship seen from the other side and needs no patching, no freezing and no
sleep. None needs a database either — the invariant is a property of fixture
construction, and asserting it against Postgres would only prove the constraint
still exists.

**Probed both ways.** With `_persist_at` reverted to the bare constant, six of
the seven cases go red. The seventh — the AST check that no call inside
`TestPersistence` passes `NORMALIZED_AT` as `normalized_at` — stays green, and
correctly: the old defect was the *value* the helper returned, not a constant at
a call site. It guards a different regression, which is the one a value test
cannot see: **a new test written later that reintroduces the constant.**

One of them states the defect rather than only its absence:

```python
record = raw_view(collected_at=NORMALIZED_AT + timedelta(seconds=1))
assert NORMALIZED_AT < record.collected_at  # the old behaviour, true on purpose
assert _persist_at(record) >= record.collected_at  # the repair
```

A revert turns the second line red while the first stays green, so the failure
output names the cause instead of only the symptom.

### The bounded scan, and its result

Mission 1.15.4.1 §10 asked for a search for equivalent time bombs, scoped to test
fixtures rather than turned into a repository-wide clock project. Done
mechanically: the schema carries **nine** ordering CHECKs between two timestamps,
across `raw_records`, `normalized_records`, `signals`, `signal_derivation_runs`
and `claim_interpretation_runs`. The dangerous shape is a fixed constant on one
side and a runtime clock on the other, so the search was for test modules holding
**both**.

**Two modules hold both, and neither is defective:**

| Module | Why it is safe |
|---|---|
| `test_compliance.py` | Its fixed `datetime(2026, 8, 29, 10, 0)` is a verification time compared only with `first + timedelta(hours=1)`. Both sides derive from the same constant; the `datetime.now(UTC)` uses sit in unrelated assertions |
| `test_signal_persistence.py` | One `now = datetime.now(UTC)` supplies `last_seen_at`, `collected_at` and `expires_at = now + 30 days` together, so every ordering holds by construction. Its fixed `datetime(2018, 1, 1)` is an `observed_at` in a constraint-violation case — observation semantics, not ordering against a clock |

Everything else pairs fixed with fixed (`normalization_fixtures.py`'s
`COLLECTED_AT`/`NORMALIZED_AT` for the offline tests,
`test_gdelt_web_ngram_normalizer.py`'s pair) or runtime with runtime.

**Exactly one instance of the defect existed**, and the reason is worth keeping:
`seeded_raw` is the only fixture that runs a **real collector** — chosen
deliberately in Mission 1.6 so the normalizer meets the shape production
produces — and it was the only place a real clock met a literal.

---

## 43. Invert a guard rather than delete it (Mission 1.15.5)

Mission 1.15.4 wrote two tests asserting that a thing did **not** exist:

```python
def test_the_gate_has_no_use_profile_parameter(): ...
def test_no_use_profile_concept_exists_anywhere_in_the_packages(): ...
```

Their docstrings said, in advance, what a failure would mean: *"If this test ever
fails, the extension proposed in the gap document is being built — which is fine,
and it should happen in a mission that says so."*

Mission 1.15.5 said so, and both went red. **They were inverted, not deleted:**

```python
def test_the_gate_now_requires_a_use_profile(): ...
def test_the_use_profile_concept_now_exists(): ...
```

### Why inverting is the right move

The property worth protecting did not disappear — **it flipped**. Before, the
risk was building a governance concept as a side effect of a source review;
after, the risk is losing it. Deleting the tests would have left the second risk
unguarded and erased the record that the first one was ever taken seriously.

An absence-assertion is a **dated claim about the codebase**, and the honest way
to retire one is to replace it with the claim that superseded it, in the same
place, so a reader sees the transition rather than a gap.

### The tell

Write the docstring of an absence-assertion as if somebody will one day make it
fail. If you cannot say what their failure means and what they should do, the
test is a lock rather than a guard, and it will be deleted rather than inverted.

---

## 44. A required argument is a better guard than an assertion (Mission 1.15.5)

The gate had to stop answering questions about a source without knowing what the
source was being used for. Two mechanisms were available:

```python
# assert
def evaluate_eligibility(source, use_profile_id=None, ...):
    if use_profile_id is None:
        raise ...

# require
def evaluate_eligibility(source, use_profile_id, ...):
```

**The second was chosen, and the difference is not style.** A defaulted argument
with a runtime check is discovered by whoever runs the code; a required
positional argument is discovered by **mypy, across 40 modules, before anything
runs** — and it made the migration mechanical: every one of 68 call sites had to
be visited, and none could be missed by being on a branch nobody exercised.

It also removes the shape that would have been most dangerous:
`use_profile_id=None` meaning "whatever the source's current review is" is
exactly one careless edit away from a silent fallback to a global verdict.

The tests then assert the *signature* rather than the behaviour:

```python
parameters = inspect.signature(evaluate_eligibility).parameters
assert list(parameters)[1] == "use_profile_id"
assert parameters["use_profile_id"].default is inspect.Parameter.empty
```

**A test on the signature survives a rewrite of the body.** A test that only
checked "raises when None" would pass against a function that had quietly
acquired a default of `LEGACY_USE_PROFILE`.

### The related guard

`SourceRecord.review` survives as the legacy-profile accessor, so an AST test
asserts that the three gate modules never read it. That fence exists because
`.review` reads more naturally than `.review_for(profile)` — which is precisely
how the mistake would be made, by someone writing what sounds right.


---

## 45. A gate test needs its control case, or it passes against a refusal (Mission 1.15.6)

Two new capabilities check gates that permit some things and refuse others:
`source-route-binding` and `source-field-minimisation`. The obvious tests are
the refusals — bulk XML is rejected, the contact block is rejected, an
unreviewed field is rejected — and every one of them passes against a gate that
**refuses everything**.

A filter that allows nothing is a refusal, not a filter. So each check asserts
its control first:

```python
for label in sorted(routes.allowed_labels):
    if routes.refusals(label):
        failures.append("authorised route ... is refused by the gate that is supposed to permit it")
```

This is not new — `_control_passes` has done it for the resource-gate
capabilities since Mission 1.4 — and it is restated because the mistake is
easiest to make on a **fresh** gate, where the refusal cases are the interesting
ones and the permit case looks too obvious to assert.

### The same rule, one level up

`_check_route_binding` reports **unimplemented** when no route authorization is
configured, rather than passing. A capability that returned no failures for a
source with nothing configured would satisfy its condition by having no rules —
the shape §31 already warns about for validators, arriving through the
capability door.

---

## 46. Test the reclassification from both sides of the version line (Mission 1.15.6)

Two conditions moved from `HUMAN_CONFIRMATION` to `CAPABILITY`, by appending
local review **v2** rather than editing v1. Three assertions, and the middle one
is the one a reviewer would forget:

```python
assert v1.assessments == v2.assessments  # the conclusion did not move
assert kinds_in_v1[ROUTE_ONLY] is HUMAN_CONFIRMATION  # v1 still says what it said
assert changed == {ROUTE_ONLY, MINIMISATION}  # and NOTHING ELSE changed
```

The first protects the policy conclusion. The second protects the append-only
guarantee **from the other side**: a test that only checked v2 would pass
against a migration that had quietly rewritten v1 to match.

The third is the one that earns its place. Asserting that two conditions changed
says nothing about the other two, and a diff of a JSON review is exactly the
place where an unintended edit survives review by being surrounded by intended
ones. Computing the changed set and comparing it to an expected set catches the
edit nobody meant to make.

---

## 47. Assert that a new mechanism cannot reach the thing it must not (Mission 1.15.6)

Mission 1.15.6 built a way for configuration to satisfy conditions. The risk it
introduced is not that the mechanism fails; it is that the mechanism **reaches
one condition too many** — specifically TED's residual database-right
acceptance, which must stay unsatisfiable.

So the suite asserts the absence directly rather than trusting the dispatch:

- the condition still declares `HUMAN_CONFIRMATION`;
- verifying it with the full compliance configuration in hand returns `UNKNOWN`
  from the `human-confirmation` verifier;
- rewriting it as a `CAPABILITY` naming either new capability does not make it
  answer *this* question — it answers a different one;
- the database still refuses a hand-set `satisfied` boolean.

**A guard is worth most when it is tested against the thing that would most
plausibly defeat it**, which here is the mission's own new code rather than a
hypothetical attacker.

---

## 48. A fence protects the modules it names, and nothing else (Mission 1.15.6 follow-up)

Mission 1.15.5 put an AST fence on `SourceRecord.review`, the legacy-profile
accessor, asserting that `eligibility.py`, `authorization.py` and
`verification.py` never read it. The reasoning was exact and is still right:
`.review` reads more naturally than `.review_for(profile)`, which is precisely
how the mistake would be made.

**It was made four times, in the module the fence did not name.** `cli.py` read
`source.review` in `list`, `show`, `conditions` and `stale`, while passing the
requested profile to the gate whose result it printed alongside. The worst of
the four returned *"the current review declares no condition"* for a review
carrying four.

Two things generalise.

**A guard's scope is a claim, and it should be as wide as the risk.** The fence
covered the modules that *decide*, because a wrong decision is worse than a
wrong report. That reasoning is sound and the conclusion was too narrow: an
operator who reads "declares no condition" stops looking, and the decision that
follows is theirs rather than the gate's.

**The default hid it.** Under the legacy profile — the default, and what 28 of
29 sources have — the old output was correct. The command was right everywhere
except the one source anybody needed it for, which is the shape a defect keeps
for longest.

The fence now covers `cli.py` too, exempting the single sanctioned reader by
name:

```python
offenders = [
    f"{fn.name}:{node.lineno}"
    for fn in functions(tree)
    if fn.name != "_profile_review"
    for node in ast.walk(fn)
    if isinstance(node, ast.Attribute) and node.attr == "review"
]
assert offenders == []
```

**Exempting one named function is what makes the fence survivable.** A fence
with no legitimate way through gets deleted the first time somebody needs one.

---

## 49. Deployment state is not repository state, and a test must not confuse them (Mission 1.15.6.1)

A `HUMAN_CONFIRMATION` is satisfied by a row in the operator's database. The
catalog travels through git; **that row does not**. `source-registry-v1.md` §3
and Mission 1.3 §24 already say why — satisfaction depends on what is deployed,
and a catalog that could assert its own conditions satisfied would make
`APPROVED_WITH_CONDITIONS` meaningless.

The first version of `test_ted_operator_acceptance.py` asserted the recorded
acceptance **unconditionally**. It passed on the operator's machine and went red
in CI, which starts from an empty database and has no operator — where TED is
correctly ineligible.

**This is the same mistake as quoting one database's research counts as a
property of the repository**, which Mission 1.15.6 had flagged two missions
earlier. It is easy to make twice because local state is the state you can see.

The shape that works:

- gate the deployment-dependent assertions on whether the row is present;
- and assert, **unconditionally**, the invariant that holds either way —
  *if* an acceptance exists it came from a person and carries the right scope,
  and *if* it does not, the gate refuses for exactly that condition.

The second half is what stops the gate from becoming a test that skips itself
into vacuity.

### Ask at test time, not at import time

The first attempt used a module-level `pytest.mark.skipif(not _recorded(), …)`.
It skipped **everything**, on the machine where the row exists.

A `skipif` argument is evaluated while the module is being imported: before the
session has started, before fixtures, and — because the helper caught `Exception`
and returned `False` — any hiccup was indistinguishable from a real absence. The
file then skipped silently **while looking like it had run**, which is worse than
failing.

A fixture calling `pytest.skip()` asks at test time, and narrowing the `except`
to the one error that genuinely means *absent* (`UndefinedTable`) makes a failure
to ask visible instead of silently negative.

**A guard that cannot tell "no" from "I could not check" is the same defect as
`UNKNOWN` being promoted to `UNSATISFIED`** — the distinction this repository
enforces everywhere else, arriving through the test harness.


---

## 50. Assert both directions of a rule that trades one risk for another (Mission 1.15.6.2)

The effective-verification rule has two halves, and each exists to stop the
other from going too far:

- a machine verifier must **never revoke** a human decision;
- a human decision must **never make a machine condition sticky**.

A suite that tested only the first would pass against an implementation that
persisted everything and stopped checking — which is the failure the separation
exists to prevent, reached by satisfying its headline requirement.

So each capability is broken in turn, with the operator's acceptance supplied
intact, and the authorization must still refuse **naming the capability**:

```python
@pytest.mark.parametrize(("field", "condition"), [...])
def test_a_broken_capability_blocks_even_with_the_acceptance_recorded(...):
    assert resolved[RESIDUAL].result is SATISFIED          # the human half held
    assert resolved[condition].result is not SATISFIED     # the machine half did too
```

**A rule stated as a trade-off needs a test per side.** The one you remember to
write is the side that motivated the change.

### The probe that proves a filter is a filter

`decisions` is an argument a caller supplies, so the assertion that matters is
not that a legitimate decision works — it is that an illegitimate one does
nothing. A forged `CAPABILITY` record supplied alongside a passing capability
proves nothing, because the capability passes anyway. It is proved against a
configuration where the capability **fails**: if supplied records could satisfy
machine conditions, that test would go green.

**Test an allowlist against the case it must refuse, in a world where refusing
is the only thing that could produce the answer.**

---

## 51. `except Exception` does not catch `SystemExit` (Mission 1.15.6.2)

A CLI helper read operator decisions from the database and degraded to "none"
when it could not, so the commands documented to run without a database would
keep working. The guard was `except Exception`.

`_connect()` raises **`SystemExit`** for an unset `DATABASE_URL` or a missing
driver, and `SystemExit` inherits from `BaseException`, not `Exception`. The
guard did not catch the case it was written for.

The second half was subtler: `psycopg.connect` raises for an unreachable host
**inside `_connect()`**, before the `with` body the `try` was wrapped around. Two
different failures, both landing outside the handler, and both discovered only
by pointing `DATABASE_URL` at a closed port and at nothing.

```python
try:
    with _connect() as conn:
        return read_human_decisions(...)
except SystemExit as exc:  # unset URL, missing driver
    ...
except Exception as exc:  # unreachable host, driver error
    ...
```

**And it says which happened.** Returning "no decisions" silently would be
§49's defect again — a guard that cannot tell *no* from *I could not check*. The
refusal is identical either way; the reader's understanding of it is not.

---

## 52. A default that is also a real state cannot be omitted (Mission 1.15.6.3)

`evaluate_readiness(source, profile, config, decisions=())` has a default that
reads as *nothing supplied*. It is not. `()` is a real, load-bearing state
meaning **this deployment holds no operator decision**, and the function is
right to treat it as one.

So a call site that omits the argument is not accepting a default. It is
**asserting an absence it never checked**, in a signature where the assertion is
invisible: the wrong call is shorter than the right one, type-checks, runs, and
returns a plausible answer.

Three CLI call sites omitted it. `readiness` reported the source blocked by the
one condition an operator had recorded, and `authorization` printed a built
context followed by *pass the eligibility gate*.

**The generalisation.** When a parameter's default is a legitimate value of the
domain rather than a sentinel, omission is unreviewable. Two ways out, and both
are used here:

- **make the two states distinguishable** — `_live_eligibility` takes
  `decisions: Sequence[...] | None = None`, where `None` means *the caller has
  not read them, go read* and `()` means *the caller read them and found none*;
- **fence the omission** when the signature cannot change, because
  `evaluate_readiness`'s `()` default is correct for every caller that genuinely
  has no database:

```python
offenders = [
    f"line {node.lineno}"
    for node in ast.walk(tree)
    if isinstance(node, ast.Call)
    and getattr(node.func, "id", None) == "evaluate_readiness"
    and not any(kw.arg == "decisions" for kw in node.keywords)
]
assert offenders == []
```

**A fence on a keyword rather than on an attribute**, which is the new shape.
§48's fence catches reading the wrong thing; this one catches *not passing* the
right thing, and an omission leaves no token to grep for.

**And the test that made this checkable at all injects at the seam.** The
persisted half is supplied by replacing `cli._recorded_decisions`, so the cases
describe a deployment holding an operator decision without requiring the machine
running them to hold one — §49, applied to a whole file rather than one
assertion.

---

## 53. Assert the words, not where the editor wrapped them (Mission 1.15.6.3)

A test read an operator's recorded acknowledgement out of PostgreSQL and
asserted three phrases appeared in it, verbatim, including the newlines that
happened to fall inside two of them.

A second deployment recorded **the same acknowledgement, character for
character**, wrapped at different columns. Two assertions failed on a row that
was correct, and the only lawful repairs were to rewrite a governance row nobody
had withdrawn or to fix the test.

**The evidence is the words.** Where a person's editor broke the lines is not a
property of the decision, so it is not something a test may depend on:

```python
reason = re.sub(r"\s+", " ", stored)
assert "review version 2, et pour rien d’autre" in reason
```

The phrase is still asserted whole and in order. Only the thing carrying no
meaning is dropped.

**The general rule: an assertion over human-authored free text should depend on
the text and on nothing the text was transported through.** Line wrapping,
trailing whitespace and the width of somebody's terminal all belong to the
transport. This is §42's lesson in another medium — a test that pins an
incidental of the environment it was written in reports a failure about the
environment and looks like a failure about the subject.
