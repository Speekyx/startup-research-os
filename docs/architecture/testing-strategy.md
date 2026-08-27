# Testing Strategy

Version: 1.2
Status: Strategy fixed, no tests implemented (Sprint 0 forbids business logic)
Date: 2026-08-27 (amended in Mission 0.1.2)

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
| `research-orchestrator` | Plan generation, budget enforcement, resumability, gap recording, cancellation, **`ResearchContext` snapshot immutability**, status transitions |
| `acquisition` | Provenance completeness, rate-limit compliance, parse failure handling, exact dedup |
| `nlp` | Extraction precision/recall, independence estimation, injection resistance, cost-ladder respect |
| `scoring` | Every invariant in §3, weight validation, insufficiency handling |
| `market-intelligence` | No extrapolation across scopes, language coverage reporting, event-time correctness |
| `competition` | No fabricated competitor attributes, absence ≠ empty market, staleness flagging |
| `execution` | All output typed `RECOMMENDED`/`PREDICTED`, staleness detection, refusal on low evidence |
| `workers` | Idempotency **under duplicate delivery**, retry/backoff, dead-lettering, timeout enforcement, backpressure, `workspace_id` required in every task payload |
| LLM Gateway | Tier routing, fallback recording, budget refusal, timeout, schema-failure handling, no provider SDK reaching a caller (ADR-006) |

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
