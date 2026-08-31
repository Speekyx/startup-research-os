# Mission 1.15.4.1 — Temporal Test Fixture Hardening

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.15.4.1` · **Scope:** time
in tests only.

**The repair itself already shipped.** It landed as commit `4b9661c`, the first
of two in [PR #30](https://github.com/Speekyx/startup-research-os/pull/30),
merged before this brief was written. The seven tests have been green since.

**What this mission adds is the part that was missing:** the regression guard
(§9), the bounded scan for equivalent time bombs (§10), and the rule stated in
the form §15 asks for.

---

## 0. What was already done, and what was not

| Brief section | State on arrival |
|---|---|
| §5 — the fixture repair | **done** in `4b9661c` |
| §15 — the lesson recorded | partly — `testing-strategy.md` §42 existed, without §15's exact formulation |
| **§9 — regression test** | **not done** |
| **§10 — scan for similar time bombs** | **not done** |
| §16 — this report | not done |

Redoing §5 would have been busywork against a green suite. The three outstanding
items are the ones with content.

---

# The §16 questions

## What caused the seven failures?

`normalization_fixtures.py` pins `NORMALIZED_AT = 2026-08-31 09:00 UTC`, while
the `seeded_raw` fixture runs the **real** World Bank collector, which stamps
`collected_at` from the wall clock. `TestPersistence` paired the two.

For months the constant sat in the future and everything passed. Once real time
passed 09:00 UTC, every seeded record was collected *after* the moment the tests
claimed to normalise it, and the database refused the write.

## Was the database constraint wrong?

**No.** `CHECK (normalized_at >= collected_at)` is correct and untouched. A
normalization cannot precede the collection it normalises.

## Was the World Bank collector wrong?

**No.** Stamping `collected_at` from the real clock is right, and using the real
collector in the fixture was a deliberate Mission 1.6 decision — a fixture that
inserted hand-written rows would test the normalizer against a shape nothing
produces.

## Was production normalization wrong?

**No.** No production semantics changed.

## What fixture was time-dependent?

`test_world_bank_normalizer.py::TestPersistence`, through
`normalization_fixtures.NORMALIZED_AT`. **The constant itself is not the bug** —
it is correct for the offline tests, which pair it with the fixed `COLLECTED_AT`.
The bug was pairing it with a real clock.

## What exact repair was made?

Inside `TestPersistence` only, the time is derived instead of pinned:

```python
def _persist_at(*records) -> datetime:
    return max([NORMALIZED_AT, datetime.now(UTC), *(r.collected_at for r in records)])
```

Computed **once per test** and reused, so nothing drifts between two calls in one
test. `_revise` moves `collected_at` a day forward on purpose, so that record is
passed in rather than assumed.

## Are fixture timestamps now deterministic?

**Deterministic in the sense that matters: the ordering is guaranteed by
construction.** `_persist_at` reads a clock, so it does not return a fixed value
— and the invariant the tests exercise is *ordering*, not an absolute instant.
Freezing the clock instead would have meant a clock abstraction for seven
fixtures, which §5 asks not to build.

The offline tests remain absolutely deterministic, and should: they pair
`NORMALIZED_AT` with the fixed `COLLECTED_AT`, where determinism is worth more
than clock-independence.

## Can wall-clock advancement recreate the failure?

**No**, and it is asserted rather than argued. `_persist_at` takes the maximum of
the constant, the current time and every record's collection time, so its result
is never earlier than any input by construction.

## Was a regression test added?

**Yes** — `TestTheFixtureCannotExpire`, four tests, and none of them waits.

The advancing clock is simulated by **moving the record forward**, which is the
same relationship seen from the other side and needs no patching, no freezing and
no sleep:

```python
@pytest.mark.parametrize("days_ahead", [0, 1, 365, 3650])
def test_normalization_never_precedes_collection_however_late_the_record(self, days_ahead):
    record = raw_view(collected_at=NORMALIZED_AT + timedelta(days=days_ahead, seconds=1))
    assert _persist_at(record) >= record.collected_at
```

`days_ahead=3650` is the wall clock a decade past the constant.

They need no database either: the invariant is a property of fixture
construction, and asserting it against Postgres would only prove the constraint
still exists.

**Probed both ways.** With `_persist_at` reverted to the bare constant, **six of
the seven cases go red**. The seventh — an AST check that no call inside
`TestPersistence` passes `NORMALIZED_AT` as `normalized_at` — stays green, and
correctly: the old defect was the *value* the helper returned, not a constant at
a call site. It guards the regression a value test cannot see, which is **a new
test written later that reintroduces the constant**.

One test states the defect rather than only its absence, so a revert names its
own cause in the failure output:

```python
record = raw_view(collected_at=NORMALIZED_AT + timedelta(seconds=1))
assert record.collected_at > NORMALIZED_AT  # true on purpose
assert _persist_at(record) >= record.collected_at  # the repair
```

## Were similar fixture risks found?

**No, and the search was mechanical rather than impressionistic.**

The schema carries **nine** ordering CHECKs between two timestamps:

| Table | Constraints |
|---|---|
| `acquisition.raw_records` | `expires_at > collected_at`, `last_seen_at >= collected_at` |
| `acquisition.normalized_records` | `expires_at > normalized_at`, **`normalized_at >= collected_at`** |
| `nlp.signals` | `expires_at > derived_at` |
| `nlp.signal_derivation_runs` | `finished_at >= started_at`, `expires_at > finished_at` |
| `research.claim_interpretation_runs` | `finished_at >= started_at`, `expires_at > finished_at` |

The dangerous shape is a fixed constant on one side and a runtime clock on the
other, so the search was for test modules holding **both**. Of the fifteen test
modules carrying a hard-coded `datetime(20xx, …)`, **two** also read a runtime
clock, and neither is defective:

| Module | Why it is safe |
|---|---|
| `test_compliance.py` | Its `datetime(2026, 8, 29, 10, 0)` is a verification time compared only with `first + timedelta(hours=1)`. Both sides derive from the same constant; the `datetime.now(UTC)` uses are in unrelated assertions |
| `test_signal_persistence.py` | One `now = datetime.now(UTC)` supplies `last_seen_at`, `collected_at` and `expires_at = now + 30 days` together, so every ordering holds by construction. Its `datetime(2018, 1, 1)` is an `observed_at` in a constraint-violation case — observation semantics, not ordering against a clock |

Everything else pairs fixed with fixed or runtime with runtime.

**Exactly one instance existed, and the reason is worth keeping:** `seeded_raw`
is the only fixture that runs a **real collector**, so it was the only place a
real clock could meet a literal. Nothing was fixed speculatively, and no
repository-wide clock abstraction was introduced (§10, §5).

## Were production collector semantics changed?

**No.**

## Were normalized numeric semantics changed?

**No.** Decimal parsing, canonicalization, collector version semantics,
idempotency, retention and provenance are all untouched (§7).

## Was any production research data modified?

**No.**

## Did the existing 12 / 12 / 7 / 7 / 7 remain unchanged?

**Yes.** RawRecords 12, NormalizedRecords 12, Signals 7, Claims 7,
ClaimRevisions 7, Evidence 7, Reliability 0, Opportunities 0, Embeddings 0,
Scores 0. The post-suite digest watcher reports the database unchanged across 24
tenant and 16 global tables.

## Did TED remain unchanged?

**Yes** (§12, §13). Review v5, `REQUIRES_REVIEW`, H-34 and H-36 untouched, no
`assessed_use_profile`, no eligibility or authorization change. Nothing in this
mission touched the registry.

## Are all seven previously failing tests now green?

**Yes**, and have been since `4b9661c`.

## Is the complete test suite green?

**Yes.**

```text
run_python_tests     515 tests, 8 packages          pass
run_pytest_suites    7 packages                     pass
                     966 passed, 9 skipped (acquisition)
                     24 tenant tables unchanged, 16 global tables unchanged
```

No other pre-existing failure appeared.

## Is the repository ready for Mission 1.15.5?

**Yes.** The suite is green, the time bomb is gone with a guard behind it, and
the use-profile work is untouched and waiting —
`route-scoped-source-authorization-gap-v1.md` carries the proposed extension.

---

## 1. The one thing worth keeping

**The constant was never the bug, and that is why the fix is narrow.**

The tempting repair is to delete `NORMALIZED_AT` and derive every timestamp
everywhere. It would have been wrong: the offline tests pair it with the fixed
`COLLECTED_AT`, where an absolute constant is exactly right and determinism beats
clock-independence.

What was wrong was one *pairing* — a literal on one side of an ordering
constraint whose other side came from a real clock. So the rule is not "never use
a fixed timestamp", it is:

> **A test timestamp may be absolute only when absolute time is the subject of
> the test. Where temporal ordering is the invariant, fixture timestamps must be
> derived from one another or from a deterministic test clock.**

And the tell, for the next person: **a constant that must be later than something
the test does not control.** If a fixture calls real code that reads a clock, no
literal on the other side of the comparison is safe.

## 2. Changes

| File | |
|---|---|
| `services/acquisition/python/tests/test_world_bank_normalizer.py` | `TestTheFixtureCannotExpire` — 4 regression tests (7 cases) |
| `docs/architecture/testing-strategy.md` | §42 extended: §15's formulation of the rule, how the guard was probed, and the bounded scan's result |
| `docs/architecture/mission-1.15.4.1-report.md` | this report |

No production code. No fixture constants removed. No governance state.
