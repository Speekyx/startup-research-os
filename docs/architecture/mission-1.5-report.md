# Mission 1.5 — Completion Report

**Mission:** First Production-Grade Collector — World Bank Indicators API End-to-End Acquisition
**Sprint:** 1
**Date:** 2026-08-30
**Branch:** `sprint-1/mission-1.5`
**Outcome:** one collector · **6 real World Bank observations collected** · 0 other sources · 0 normalization, claims, embeddings or scores
**Introduces:** `sros_acquisition.collection`, migration `0008_raw_record_provenance`, `AcquisitionErrorCode`, `sros-acquisition`, [`world-bank-collector-v1.md`](../data/world-bank-collector-v1.md), [`raw-record-gap-analysis-v1.md`](../data/raw-record-gap-analysis-v1.md)

---

## 0. Repository hygiene (§2)

The brief noted that the Mission 1.4 report records `sprint-1/mission-1.3`. It
did, and that was accurate rather than a typo — the bookkeeping error was
upstream. What was actually found:

| | |
|---|---|
| `sprint-1/mission-1.2` and `sprint-1/mission-1.3` | pointed at the **same commit**. No commit was ever made for 1.3 |
| Working tree | 51 uncommitted files spanning Missions 1.3 **and** 1.4 |

Corrected: both missions committed in one commit whose message says why they
share it — they were developed on one working tree and overlap in twelve files,
so splitting them afterwards would mean fabricating a Mission 1.3 commit that
never existed as a validated state. Branches `sprint-1/mission-1.3` and
`sprint-1/mission-1.4` now point at it, and this mission's work is on
`sprint-1/mission-1.5`. Nothing was pushed, and no historical report was
rewritten.

---

## 1. Collector architecture

```text
services/acquisition/python/sros_acquisition/collection/
    errors.py        the normalised error taxonomy
    transport.py     the HTTP boundary. The ONLY file that may reach a network
    pacing.py        our own request pacing. Not anyone's rate limit
    records.py       what an observation is, and what identifies it
    world_bank.py    the collector
    repositories.py  persistence: idempotent, revision-aware, tenant-scoped
    job.py           one acquisition job, testable without a broker
```

`services/workers/.../acquisition_tasks.py` is the Celery surface and holds no
decision: a job whose logic lives inside a task decorator can only be tested by
starting a worker, and a test that needs a worker is a test that gets skipped.

## 2. Authorization flow

```text
request collection
    → load the registry and the compliance configuration
    → verify conditions          ← environment state, re-checked every time
    → evaluate eligibility       ← the canonical gate
    → build AcquisitionAuthorizationContext   ← fails here, or not at all
    → check the operational switch
    → collector
```

**The context is the first positional parameter of `collect`, with no default.**
`build_authorization` produced it, which means the gate passed. There is no
overload that omits it, and a structural test asserts the signature rather than
trusting today's call site.

**The gate runs inside the job, not before it.** A payload carries no
authorization: a serialized permission outlives the state it came from, and a
source suspended between planning and execution would still be collected.

## 3. World Bank API scope

Only `indicators-api-v2` — the PUBLIC_API profile the review approved, at
`https://api.worldbank.org/v2/`. Not the Microdata Library, not DataBank, not
arbitrary pages, not browser automation, not undocumented endpoints.

**Three authorized indicator series**, in `source-compliance-v1.json`. A resource
with no entry has no recorded licence, family or content origin, so the gate has
nothing to clear it against. The licence on each entry rests on the Data Catalog
statement that CC-BY 4.0 is the *default* for World Bank-produced data — not on a
per-series licence page, because none was retrieved. Mission 1.3 recorded exactly
that as an open question, and it is why the list is three rather than three
hundred.

## 4. Request model

`WorldBankRequest(indicators, countries, start_year, end_year, per_page)` — five
fields, and a test asserts that set exactly. No path, no host, no query fragment,
so there is nothing through which one could be smuggled. Indicator and country
codes are validated because they become path segments.

## 5. HTTP transport

One file may import an HTTP client, and CI enforces it. Connect 5s, read 20s,
total 30s, 8 MiB response ceiling, an identifying user agent, no body logging.

**Redirects are not followed.** §10 requires that a redirect cannot be used to
escape a host allowlist, and the way to guarantee that is to treat a 3xx as a
response the collector must reason about rather than a hop the client silently
takes.

`httpx` is imported **inside** the function that needs it, so the registry,
the compliance layer and every zero-dependency validator still run with nothing
installed (ADR-009).

## 6. Pagination

Bounded `range`, never `while True`. Defaults: 10 pages, 5 000 records, optional
deadline. A source that answers "page 1" while page 2 was requested is reported
as `INVALID_RESPONSE` rather than looped over — otherwise a bound would stop it
and hide a real upstream fault behind a limit.

## 7. Retry policy

Retried: `NETWORK_TIMEOUT`, `RATE_LIMITED`, `TEMPORARY_UPSTREAM`,
`PERSISTENCE_FAILURE`. Three attempts. Never retried: deterministic 4xx, invalid
response, parsing failure, authorization or resource refusal, cancellation. One
call, not three — repeating a rejection is how a rate limit becomes a ban.

**Pacing is ours and says so.** Mission 1.3 found no documented World Bank rate
limit and `rate_limit.known` stays `False`. What exists is a local floor of
250ms between requests and 50 per job, whose `basis` field records in words that
it was chosen by us because the source has not said what it tolerates.

## 8. RawRecord representation

**One record is one logical observation** — one indicator, one geography, one
period — not one HTTP response. A page carries fifty observations that revise
independently.

## 9. Idempotency and updates

Three identities, kept apart:

| | |
|---|---|
| `observation_key` | WHICH: `source\|resource\|geography\|period` |
| `content_hash` | WHAT the source said: the canonical payload, identity **and** value |
| record id | which row: uuid5 of workspace, key and hash |

```text
same key, same hash   →  UNCHANGED.  No new row; last_seen_at moves
same key, new hash    →  REVISED.    New row; the previous one is superseded
new key               →  NEW
```

The retrieval timestamp is deliberately outside the fingerprint. Hashing it
would make every retrieval a revision — the failure mode that turns an idempotent
collector into one that grows a table forever.

The gap analysis found the existing `UNIQUE (workspace_id, source_id,
content_hash)` was **already exactly right**, which was not obvious: an earlier
design replaced it with a constraint over the observation key, which would have
rejected the very insert that records a revision.

## 10. Provenance

Every §19 question is answerable without reading a URL string. Promoted to
columns because auditors filter by them: `review_version`, `correlation_id`,
`collector_id`, `collector_version`, `observation_key`, `observed_at`. In
`provenance` JSONB: access profile and method, approval state, resource, dataset
family, indicator, geography, period, licence and its basis, content origin, the
rendered attribution, request path, page, and **the condition snapshot** — which
review conditions were satisfied at the moment of collection.

`observed_at` is event time at the resolution the source gave: the start of the
stated period, with the period string preserved verbatim.

## 11. Attribution

Rendered by the Mission 1.4 capability from the obligation the review recorded.
`build_draft` has **no attribution parameter** — a collector has nothing to pass.
Rendering fails closed: a resource whose licence the obligation requires and
which the dataset entry does not carry raises rather than producing a record with
no credit.

## 12. Retention

`expires_at` is the resolved raw-retention window and there is **no parameter**
through which a collector could ask for longer. Verified on the real records: 30
days, the project baseline.

## 13. Tenant isolation

Two workspaces, both isolation layers entered (`SET LOCAL ROLE` plus the
transaction-local workspace). Proven: one workspace cannot read another's
records; a worker cannot write into another workspace (the policy's `WITH CHECK`
refuses it, asserted on `InsufficientPrivilege` rather than a blind exception);
a query with no tenant filter returns only its own rows; a connection with no
workspace set returns nothing.

## 14. Celery and orchestrator integration

`acquire.collect.world_bank` routes to the acquisition queue. The payload carries
workspace, session, correlation and the request; `TaskContext.from_headers`
refuses one that cannot say which workspace it belongs to.

The planner takes `implemented_collectors` from its **constructor**, not an
import — the orchestrator may not import the acquisition package
(`service-boundaries.md`) — and it defaults to empty, so an unwired planner
refuses. Verified against the real registry:

```text
eligible: ('eurostat', 'fred', 'world-bank')
  unwired  →  NO-COLLECTOR-IMPLEMENTED
  wired    →  DISPATCHABLE
```

## 15. Collector conformance test — Mission 1.4's debt, paid

24 tests. Structural as well as behavioural: behaviour proves the collector goes
through the gate today, structure proves there is no second door for it to start
using tomorrow.

The one worth naming is
`test_an_unauthorized_indicator_costs_zero_network_calls`. Not "is refused" —
**`transport.calls == []`**. A gate that refuses after the request has gone out
has prevented nothing, and only a counting fake can tell the two apart.

## 16. Fake-transport tests

56 tests across HTTP behaviour, pagination, record semantics, persistence, tenant
isolation and jobs. Every transport is a fake; the real one is exercised only for
refusals, which happen before a socket.

## 17. Live smoke test

Opt-in behind `SROS_ENABLE_WORLD_BANK_SMOKE_TESTS=1`, five tests, skipped by
default and absent from CI. It proved the documented response envelope is the
actual one, which no fake can establish — and confirmed the two-element
`[metadata, rows]` shape the collector was built against.

## 18. Controlled real acquisition (§48)

Against a database **rebuilt from empty**, with the collector enabled through the
canonical mechanism (`sros-source enable world-bank`):

```text
SP.POP.TOTL · FR, DE · 2018–2020 · 1 page · max 10 records
→ 6 records, 1 request, 0 refusals, 0 failures
→ persisted: 6 new
```

Then the same acquisition again, to test §30 for real:

```text
→ persisted: 0 new, 6 unchanged
```

## 19. RawRecord verification (§49)

| Check | Result |
|---|---|
| raw record count | **6** — the first in the project's history |
| distinct sources | `['world-bank']` |
| other-source records | 0 |
| workspaces | one, the development workspace |
| records with no session | 0 |
| provenance complete | yes, all fourteen §19 fields |
| licence / content origin | `CC-BY-4.0` / `PLATFORM_LICENSED` |
| conditions at collection | all three `SATISFIED`, recorded on the row |
| retention | 30 days, from governance |
| attribution | *The World Bank CC-BY-4.0* |
| event time | 2018-01-01, from the period — not the retrieval |
| `last_seen_at > collected_at` | yes, moved by the duplicate delivery |
| personal data | none. Eleven payload fields, all economic-series |
| normalized / signals / vectors | 0 / 0 / 0 |

## 20. CI

| Job | Change |
|---|---|
| `source-registry` | the network-client ban **narrowed** to "only `collection/transport.py`"; a new check that no governance package holds a collector |
| `integration` | `sros-acquisition world-bank validate` — the authorization path against the real registry, reaching no network |
| `integration` | `SROS_ENABLE_WORLD_BANK_SMOKE_TESTS` added to the "no live suite is armed" assertion |

Normal CI makes **zero external requests**.

## 21. Issues found

**A test enabled a real collector as a side effect.** A Mission 1.4 test called
`sros-source enable world-bank` to assert a refusal. The moment World Bank gained
a collector the call stopped being refused and turned the switch on. Found by the
suite written after it. The refusal property now lives on Eurostat — eligible,
no collector — and a direct assertion was added that only a source with a
collector is ever enabled.

**A fixture reverted a deliberate operational decision.** Its teardown set
`collector_enabled = FALSE` for *every* source rather than restoring what it
found. Fixed to restore the previous value.

**A fixture deleted a seeded workspace.** `second_workspace` removed workspace B
in teardown; B is seeded by `0001_dev_workspace`, and the gateway suite — which
had every right to assume seeded data exists — failed on a foreign key. It now
removes only the rows it caused.

**Malformed pagination metadata crashed instead of being reported.**
`int(meta["pages"])` on a non-numeric value raised `ValueError` out of the
collector. Found by a test written for §43. Now `INVALID_RESPONSE`, because
guessing "one page" would silently truncate and guessing "keep going" would loop.

**`research_session_id` is a real foreign key**, which the first job test
discovered by failing on it. The right outcome: the alternative would have been a
nullable link that quietly lost the connection between a record and the research
that asked for it. The error path behaved correctly — `PERSISTENCE_FAILURE`,
sanitised, nothing committed.

**Eight assertions across four suites were narrowing debt.** `raw_records == 0`,
`collector_enabled == 0` and `IMPLEMENTED_COLLECTORS == frozenset()` were true of
every mission until one collected, then stopped being properties. Each was
rewritten as the rule that survives: *enabled ⊆ implemented*, *collected ⊆
implemented*. This is the third mission in a row to find that class of test, and
`testing-strategy.md` §12 now records the pattern.

**Test residue in the development database.** `research.claims` and
`scoring.evidence` hold ~200 rows committed by the Mission 1.2 suite. None
references World Bank data (`source_id` is null on all of them, and all predate
the acquisition). Pre-existing, not introduced here, and worth cleaning up — but
out of scope for this mission.

## 22. Remaining blockers

| Blocker | Status |
|---|---|
| **Normalization** | Mission 1.6. `normalized_records` is empty and §36 keeps parsing and normalization apart |
| **Eurostat / FRED collectors** | Not implemented, deliberately. Both are eligible; §57 limits this mission to World Bank |
| **The dataset allowlist is three series** | Widening it means closing Mission 1.3's per-dataset licence question, not editing a list |
| **A distributed rate limiter** | Pacing is per process. Real to want once several workers collect concurrently; not yet a measured problem |
| **Object storage (D-10)** | Payloads are inline because they are small. A large-payload source needs the decision |
| **Cancellation mid-request** | No new request starts after a cancellation; one in flight runs to its timeout. Nothing claims otherwise |
| **Calibration / D-08 / D-12 / A-12** | Open, untouched |
| **Jurisdiction / GDPR (H-12)** | Open. Requires legal input |

## 23. Readiness for Mission 1.6

Ready. Six real records exist with complete provenance, a stable observation
identity and a content fingerprint — which is exactly what a normalization
pipeline needs and what it could not have had before.

What Mission 1.6 must not assume: that a raw record's payload is normalized (it
mirrors what the source returned), that `observation_key` is a domain identity
(it is a source identity), or that attribution can be dropped once data is
transformed — `AttributedArtifact.derive` carries obligations forward and has no
parameter that removes one.

---

## Explicit answers

| Question | Answer |
|---|---|
| Is the World Bank collector implemented? | **Yes.** `world-bank-indicators@1.0.0`, and it is the only one |
| Is World Bank still collector-eligible? | **Yes**, through the unchanged canonical gate |
| Is it enabled? | **Yes**, set deliberately via `sros-source enable`. Eligible, implemented and enabled are three separate facts and all three are true only for World Bank |
| Can it make a request without an authorization context? | **No.** The context is `collect`'s first positional parameter with no default, asserted structurally |
| Can it access a URL without `authorize_resource`? | **No.** No public signature accepts a URL, a path cannot be a URL, an indicator cannot reshape a path, and the transport refuses any host outside the registry's allowlist |
| Can it collect Microdata? | **No.** No microdata resource is an authorized dataset, and the request costs zero network calls |
| Can it collect an unknown or unlicensed dataset? | **No.** An unrecorded licence, family or content origin is refused by the resource gate |
| Are attribution obligations attached to collected records? | **Yes**, rendered from the review's obligation and stored on every row. `build_draft` has no attribution parameter |
| Is retention determined by governance? | **Yes.** 30 days on the real records, and no parameter exists through which a collector could ask for more |
| Is duplicate Celery delivery safe? | **Yes** — proven twice, in a test and with a real second acquisition: 0 new, 6 unchanged. At-least-once, not exactly-once, and nothing claims otherwise |
| Can upstream revisions be distinguished from duplicate retrievals? | **Yes.** Same key + same hash is a re-sighting; same key + new hash is a revision, and the previous row is superseded rather than overwritten |
| Are RawRecords tenant isolated? | **Yes**, both layers, proven with two workspaces |
| Did the live smoke test succeed? | **Yes**, opt-in. It confirmed the documented response envelope |
| Did a controlled real acquisition succeed? | **Yes.** 6 observations, 1 request, 0 failures |
| How many real RawRecords now exist? | **6**, all World Bank |
| Was any other source collected? | **No.** Zero records from the other twelve |
| Was any NLP, embedding or scoring performed? | **No.** 0 normalized records, 0 signals, 0 vectors |
| Is production scoring still blocked? | **Yes.** No `CALIBRATED` profile, `services/scoring` still a boundary |
| Is Mission 1.6 safe to begin? | **Yes** |

## Validation

Against a database **rebuilt from empty**, then re-run after the controlled
acquisition so both states are covered.

| Check | Result |
|---|---|
| `migrate --apply --seed` from empty | **8 migrations**, 2 seeds; idempotent on a second run |
| `run_python_tests.py` (zero-dependency) | 314 tests, 5 packages |
| `run_pytest_suites.py` | 6 packages, green |
| `services/acquisition` suite | **211 tests**, up from 130. 5 live tests skipped by default |
| `validate_schema.py` | 8 invariant groups, 32 tables |
| `validate_source_registry.py` | 13 sources, 14 evidence records, 0 warnings |
| `validate_compliance_capabilities.py` | 9 conditions, 5 capabilities, network boundary is one file |
| `validate_evidence_aggregation.py` | clean; unchanged and uncalibrated |
| `assert_registry_grants_nothing.py` | 13 registered, 3 eligible, 9/9 conditions verified, 1 collector implemented and enabled, 6 records from world-bank, 0 normalized |
| Python ↔ SQL eligibility | 0 divergences |
| `ruff`, `ruff format`, `mypy --strict` | clean; **103 source files** |
| `tsc` ×2, `eslint`, `next build`, TS conformance | clean; 21 + 18 tests |
| Live suite with the flag unset | **5 skipped** |

## Mission boundary

Stopped here, as §57 requires. **Mission 1.6 was not begun.** No Eurostat
collector, no FRED collector, no other collector, no generalized normalization,
no NLP and no embeddings.

The honest one-line summary: one source can now be collected from, six real
observations exist, and every one of them can say which review authorised it,
which conditions held when it was taken, what attribution it owes and when it
expires.
