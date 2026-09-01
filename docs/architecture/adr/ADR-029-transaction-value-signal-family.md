# ADR-029 — A Third Signal Quantity Family: `TRANSACTION_VALUE`

**Status:** Accepted · **Date:** 2026-09-01 · **Mission:** Sprint 1 / 1.15.9
**Supersedes:** nothing. **Amends:** the Signal taxonomy (Mission 1.11,
`signal-taxonomy-v1.md` §4) and the Signal contract (`signal-contract-v1.md` §4).

---

## Context

### The rule this ADR exists to satisfy

`signal-taxonomy-v1.md` §4 closes `SignalQuantityFamily` on two members and
states the condition for a third in one sentence:

> An unhandled third value would be a bug rather than a gap, which is Ontology
> V2 §14.2's test for a closed enum. **Adding a third is a contract change with
> an ADR.**

Mission 1.15.9 needs one. This is that ADR, written before the enum was
touched.

### The gap, stated precisely

Mission 1.15.8 added the third canonical record kind, `procurement_notice`. The
Signal contract binds the family to the record kind of every contributing input:

| Family | Record kind | Carries |
|---|---|---|
| `LEXICAL_FREQUENCY` | `lexical_frequency_observation` | a term and a source language label, **no geography** |
| `MEASURED_SERIES` | `numeric_observation` | a metric and a geography |
| — | **`procurement_notice`** | **nothing maps** |

So a derivation over TED notices is refused with `INCOMPATIBLE_INPUT_KINDS`
before it starts. The Signal layer cannot express anything about procurement at
all, and the failure is structural rather than a missing extractor.

### Why neither existing family can be widened

**`MEASURED_SERIES` is the tempting one**, and it is wrong for two reasons that
are the same reason twice.

A measured series is *a quantity a source measures or reports over a period*,
carrying a metric and a geography. A procurement value is neither measured nor
reported over a period: it is the value **one transaction settled at**, attached
to a document, with no metric it is an instance of and no series it belongs to.
There is no `SP.POP.TOTL` for "what a cleaning contract cost".

And the family determines scope shape, which the enum's own docstring says is
why it is closed: a series signal carries a metric and a geography; a
transaction signal carries an **amount semantic**, a **currency** and a
**procurement classification**, and the two sets do not overlap. Widening
`MEASURED_SERIES` to hold both would make `metric` optional for every World Bank
signal ever written, to accommodate a family that has no metric at all. That is
the existing model getting worse for a new source's sake, which is the failure
`normalized-record-v1.md` §5.1 already refuses one layer down.

`LEXICAL_FREQUENCY` is not a candidate. A contract value is not a count of
tokens.

## Decision

**Add `TRANSACTION_VALUE` to `SignalQuantityFamily`.**

> **`TRANSACTION_VALUE`** — the monetary value at which a transaction between
> named parties was recorded, as the source published it. Carries an amount
> semantic, a currency and a procurement classification, and **no metric**:
> there is no series it is an instance of. Not a price a product could charge,
> not a willingness to pay, and not a measurement.

Three consequences follow, and each is a constraint rather than a permission.

**1. The amount semantic travels with the family.** A `TRANSACTION_VALUE` signal
that could not say *which kind of amount* it aggregated would be the flattening
Mission 1.15.8 spent a whole design refusing, one layer up. The scope carries
`amount_type` and it is required.

**2. The currency is the unit, and it is `INHERITED`.** A magnitude over
amounts in EUR is in EUR. `magnitude_unit_state` is `INHERITED`, never
`DIMENSIONLESS`, and a derivation whose inputs disagree on currency is refused
rather than converted — there is no rate anybody reviewed, and
`SignalMagnitudeUnitState` has no member meaning *several currencies at once*.

**3. It says nothing about demand.** The demand families
(`PAIN`/`DESIRE`/`BEHAVIORAL`/`MARKET`) are a different axis and Ontology V2
§3.6 is not amended. A public body buying cleaning services is a transaction
that happened; whether it evidences a market anybody could sell into is an
inference this layer does not make.

### What is deliberately NOT decided here

**This is not `WILLINGNESS_TO_PAY`.** The demand-side portfolio has wanted a
willingness-to-pay source since Mission 1.15, and TED was registered as the
first candidate able to produce a **transaction** rather than a listed price.
That is the distinction this family preserves and does not collapse:

| | |
|---|---|
| **Established** | a named buyer paid a named supplier a stated amount for a stated procurement, and the source published it |
| **Not established** | that a market exists, that a comparable buyer would pay a comparable amount for a different product, or that anything about a SaaS follows |

A family named `WILLINGNESS_TO_PAY` would put the second reading in the field a
consumer branches on. `TRANSACTION_VALUE` names what the number is.

## Consequences

**Contract.** `SignalQuantityFamily` gains one member; `domain.v1.json` is the
source and the TypeScript, Python and JSON-Schema artefacts are regenerated.
Consumers branching exhaustively on the family gain a third arm — which is the
point of the enum being closed, and the reason this needed an ADR rather than an
edit.

**Database.** `signals_quantity_family_check` gains the value, and the
`signal_type` registry gains one row. Migration 0023.

**Existing signals are untouched.** The seven stored signals are
`LEXICAL_FREQUENCY` and `MEASURED_SERIES` and mean exactly what they meant.
`numeric_period_change`, `lexical_frequency_contrast` and
`lexical_frequency_change` are unchanged in semantics, identity and version.

**A family is not an extractor.** This ADR authorises the vocabulary. Whether
any real TED observation qualifies for a derivation is a separate question with
its own answer, and Mission 1.15.9's report gives it.

## Alternatives considered

**Widen `MEASURED_SERIES`.** Rejected above: it would make `metric` optional for
every existing series signal to accommodate a family that has none.

**Reuse `signal_family` (the ADR-017 registry) instead of the closed enum.**
Rejected. That registry says what a **source could expose**; this axis says what
a **derivation is about**. `signal-taxonomy-v1.md` §1 exists because those two
were once the same word, and merging them again would undo it.

**Add no family and produce no procurement signal.** Rejected as a permanent
answer and adopted as the interim one: the Signal layer would be structurally
unable to say anything about the only source in the portfolio that can produce
transaction evidence. The gap is real and this is the smallest change that
closes it.

**Name it `PROCUREMENT_VALUE`.** Rejected as too narrow for a closed enum. The
quantity is *the value a transaction settled at*; procurement is the mechanism
this source happens to publish. A future auction, tender or grant source would
be the same quantity under a different mechanism.
