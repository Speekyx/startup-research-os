# Mission 1.15.9 — TED-EU Transaction Signal Extraction V1

**Sprint 1.** The Signal layer can now describe procurement, and the three real
TED observations correctly produced **zero Signals**.

**H-37 OPEN. H-38 OPEN. H-36A NOT ESTABLISHED. H-36B NOT ADDRESSED.** No Claim,
no Evidence, no Opportunity, no embedding, no score.

---

## 1. The modeling gap, found before anything was written

§10 asked for the semantics first and for a stop if the contract could not hold
them. It could not, and the reason was structural rather than a missing
extractor.

`SignalQuantityFamily` is a **closed enum** on two members, and the Signal
contract binds the family to the record kind of every contributing input:

| Family | Record kind |
|---|---|
| `LEXICAL_FREQUENCY` | `lexical_frequency_observation` |
| `MEASURED_SERIES` | `numeric_observation` |
| — | **`procurement_notice`** — nothing mapped |

So a derivation over TED notices was refused with `INCOMPATIBLE_INPUT_KINDS`
before it began. `signal-taxonomy-v1.md` §4 states the condition for a third
member in one sentence — *"Adding a third is a contract change with an ADR"* — so
**ADR-029** was written before the enum was touched.

**`MEASURED_SERIES` was the tempting reuse and is wrong.** A measured series is a
quantity a source reports over a period, carrying a metric and a geography. A
procurement value is the amount **one transaction settled at**, with no metric it
is an instance of. Widening that family would have made `metric` optional for
every World Bank signal ever written, to accommodate a family that has none.

## 2. What was added

| | |
|---|---|
| Family | **`TRANSACTION_VALUE`** — contract enum, ADR-029 |
| Required fact | **`PAIRED_MONETARY_AMOUNT`** — withheld by exactly the two reasons Mission 1.15.8 added |
| Signal type | `procurement_value_contrast` — registry row, migration 0023 |
| Extractor | **`procurement-value-contrast@1.0.0`** |
| Scope fields | amount types, amount scopes, currencies, notice classes, classification codes and scheme |

The `TRANSACTION_VALUE` scope is validated in the model: it **must** carry an
amount semantic and a currency, and it **must not** carry a metric or a term.
The prohibition is the point — the absence of a metric is why the family exists.

## 3. The semantic, and why it is not willingness-to-pay

**The proposition:** within one source, several procurement transactions sharing
an amount semantic, an amount scope, a currency, a notice class and a procurement
classification settled at values whose spread is exactly this much, across
exactly this many contracts.

| | |
|---|---|
| **Established** | a named buyer paid a named supplier a stated amount, and the source published it |
| **Not established** | that a market exists; that a comparable buyer would pay a comparable amount for a *different* product; that anything about a SaaS follows |

A family or type named `WILLINGNESS_TO_PAY` would put the second reading in the
field a consumer branches on. Enforced rather than described: a test asserts no
serialised scope, window or magnitude field contains `willingness`, `wtp`,
`demand`, `price`, `pricing`, `arpu`, `purchase_intent` or `market_size`.

## 4. Comparability, and the decision that produced zero

Five cohort dimensions: source, notice class, amount scope, currency and **CPV
division**. The amount semantic is a required derivation parameter rather than a
grouping dimension.

**The CPV division is the decision worth arguing with.** Without it, a cohort is
*"EUR totals in this slice of TED"* — a statement about a query, in which a
cleaning contract and an insurance contract become one value distribution. With
it, the two real award notices are CPV `90` and CPV `66`: two markets, two
cohorts of one, no Signal.

Both groupings were available over the same three records and one of them made
the mission look productive. `testing-strategy.md` §57 records why the honest one
was chosen and what makes that choice fragile.

**The division rather than the full code**, because `90911200` and `90911300` are
cleaning services twice and exact equality would split a genuine cohort into
singletons. A notice spanning several divisions joins **no** cohort: it has no one
subject, and reading `codes[0]` would make the cohort depend on publication order.

## 5. The real execution

`run_signal_derivation_job`, the production path, once per monetary semantic over
the three normalized TED records.

| | |
|---|---|
| Normalized observations inspected | **3** |
| Carrying an eligible paired amount | **2** — both `TOTAL_VALUE` / `NOTICE` / `EUR` / `ESTABLISHED` |
| Excluded, and why | **1** — a contract notice with no monetary entry, whose CPV codes span divisions 33 and 34 so it has no single subject |
| Cohorts formed | **2** |
| Cohorts meeting minimum support | **0** |
| **Signals created** | **0** |
| Derivation runs recorded | **8** (4 semantics × 2 runs) |

```text
cpv_division=66  CONTRACT_AWARD_NOTICE  1 member  INSUFFICIENT_INPUT_OBSERVATIONS
cpv_division=90  CONTRACT_AWARD_NOTICE  1 member  INSUFFICIENT_INPUT_OBSERVATIONS
```

A refused derivation gets a run record, never a row in a table of signals
(ADR-021).

## 6. Answers

| Question | Answer |
|---|---|
| Why is one notice not a Signal? | its assertion is recoverable from its own payload; that is the observation renamed (`signal-contract-v1.md` §3) |
| Signal semantic selected? | a non-temporal cohort spread of comparable settled procurement values |
| Why not generic WTP? | §3 — what a buyer paid is established; what anyone would pay for a different product is not |
| Extractor id/version? | **`procurement-value-contrast@1.0.0`** |
| Eligible records? | `procurement_notice`, requested `amount_type`, `pairing = ESTABLISHED`, exact decimal |
| Minimum support? | **2**, and the extractor refuses rather than lowering it |
| Comparability dimensions? | source, notice class, amount scope, currency, CPV division |
| Different amount types mixed? | **No** — the semantic is a required parameter |
| Different currencies mixed? | **No** — `INCOMPATIBLE_SERIES` |
| Currency converted? | **No** — asserted over the AST |
| Does H-37 affect the extractor? | it is the reason the basis is `NONE`; the derivation depends on nothing temporal |
| Any temporal ordering used? | **No** — members ordered by amount, then observation key |
| Does H-38 affect eligibility? | yes — unpaired entries supply no required fact |
| Unestablished pairs excluded? | **Yes**, entirely |
| PARTIAL inputs? | usable here, mechanically: `PERIOD_TIMEZONE_NOT_ESTABLISHED` withholds the two temporal facts and neither is required. Nothing was converted to `VALID` |
| Quality limitations retained? | support count on the window, single source in the scope, PARTIAL reasons on every input, basis `NONE` |
| Every supporting observation in provenance? | **Yes** — lineage size equals support count, asserted |
| Idempotent? | **Yes** — identity is deterministic over extractor, parameters and member set; member order does not change it |
| Existing Signal semantics changed? | **No** |
| More TED records fetched? | **None** |
| Collector Decimal defect changed? | **No** |
| Recorded as blocking the next TED acquisition? | **Yes** — `ted-eu-transaction-signals-v1.md` §13 |
| Observations inspected / eligible? | **3 / 2** |
| Cohorts formed / meeting support? | **2 / 0** |
| Real TED Signals created? | **0** |
| Amount types and currencies? | none created; the two eligible observations were `TOTAL_VALUE` in `EUR` |
| H-37 / H-38 at mission end? | **OPEN / OPEN** |
| Claims created? | **No** |
| Evidence created? | **No** |
| Opportunities / embeddings / scores? | **No** |
| All gates pass? | **Yes** — §8 |

## 7. Two defects found and fixed, both outside the mission's subject

**A fixture that expired.** `test_world_bank_normalizer.py::TestTheFixtureCannotExpire`
failed on the wall clock: `_revise` advanced a fixed day from a constant while
the batch time included `datetime.now(UTC)`, so once the clock passed the
constant plus a day the "later" collection was in the past. That is
`testing-strategy.md` §42's defect **reappearing inside the class written to
prevent it**. `_revise` now advances from `max(record, after)`, which makes
"later" relative to what the batch actually used.

**A validator regex that misparsed standard SQL.** `DROP_CONSTRAINT` in
`validate_schema.py` did not skip `IF EXISTS`, so it captured `if` as the
constraint name. Migration 0023 uses that form, the drop went unrecognised, the
superseded two-value CHECK stayed in the parsed body, and a **deliberately
widened** value set was reported as drift against the contract. A silent misparse
rather than an error, so it was fixed at the pattern rather than at the
migration — and the migration was not edited, because the ledger stores its
checksum and an applied migration is history.

## 8. Validation

| Check | Result |
|---|---|
| zero-dependency suites | 515 tests across 8 packages |
| pytest suites | 7 packages; nlp 256, acquisition 1 385 + 11 skipped |
| seven validators | all OK |
| all five generator `--check` steps | current |
| `ruff check` / `format --check` | clean |
| `mypy` | no issues |
| env-template secret check · `assert_registry_grants_nothing` | OK |

47 new tests in `test_procurement_value_contrast.py`, no network and no database.
Fixtures that **do** qualify prove the extractor derives correctly; the real data
proves it refuses correctly.

Counts unchanged: **15 raw, 15 normalized, 7 signals (0 `TRANSACTION_VALUE`), 7
claims, 7 evidence, 0 opportunities, 0 reliability assessments, 0 embeddings.**

## 9. Next mission

**Not Claims.** §39 is explicit and the result is unambiguous: with zero Signals
there is nothing to interpret, and jumping to a Claim layer would mean building
it against fixtures.

**Sprint 1 — Mission 1.15.10, TED Collector V1.1 and a comparability-designed
acquisition.** Two things in one mission, in this order:

1. **Repair the Decimal invariant** in `ted-search-api`, with a version bump and
   a compatibility treatment for the three records already collected. This is the
   blocking rule recorded in §13 of the signals document, and it must land before
   anything else is collected.
2. **A bounded acquisition designed for comparability** rather than for volume:
   award notices, one CPV division, one currency, a short window. The extractor
   needs no change — the observations do, and the requirement is now precise
   enough to state as a query.

What must **not** happen in that mission is a widening of the cohort key to make
the existing three records produce a Signal. The key is a semantic decision and
the data is what is missing.
