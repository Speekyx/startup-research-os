# TED-EU Transaction Signals V1

**Authoritative.** Mission 1.15.9 and Mission 1.15.10, ADR-029. The first
derivation over procurement notices, what it asserts, and the four things it
refuses to assert.

**State: ONE real Signal exists**, derived in Mission 1.15.10 from three award
notices acquired for comparability. Mission 1.15.9 produced zero from the
notices it had, and that stands as a correct answer rather than a failure; §11
records both runs, and §11.2 records what the real data corrected in the
extractor.

**H-37 OPEN. H-38 OPEN. H-36A NOT ESTABLISHED. H-36B NOT ADDRESSED.** The
blocking rule that Mission 1.15.9 placed on the next TED acquisition — repair
the collector's Decimal invariant with a version bump — was **satisfied by
Mission 1.15.10 Phase A** before any acquisition ran. See
`ted-eu-search-api-collector-v1.md` §5.1.

---

## 1. Why one notice is not a Signal

`signal-contract-v1.md` §3 states the rule and this mission does not bend it:

> A Signal asserts something that cannot be read off any one of its inputs. A
> derivation whose output is a function of exactly one observation, and whose
> assertion is recoverable from that observation's payload alone, is the
> observation renamed.

*"TED reported TOTAL_VALUE = 73,415.22 EUR"* adds nothing to a normalized record
that already says exactly that. Storing it in a table called `signals` would
make a reader believe a derivation had happened.

So the floor is **two distinct observations**, and the extractor returns
`INSUFFICIENT_INPUT_OBSERVATIONS` rather than lowering it.

## 2. The Signal

| | |
|---|---|
| Extractor | **`procurement-value-contrast@1.0.1`** |
| Signal type | `procurement_value_contrast` |
| Quantity family | **`TRANSACTION_VALUE`** (ADR-029) |
| Record kind read | `procurement_notice` |
| Temporal basis | **`NONE`** |
| Direction | **`NOT_APPLICABLE`** |
| Magnitude | `ABSOLUTE_DIFFERENCE` — max minus min, exact |
| Magnitude unit | the currency, `INHERITED` |

**The proposition, in full:** within one source, several procurement
transactions that share an amount semantic, an amount scope, a currency, a
notice class and a procurement classification settled at values whose spread is
exactly this much, across exactly this many contracts.

## 3. What it is not, and this is the load-bearing section

**Not willingness to pay.** The demand-side portfolio has wanted a
willingness-to-pay source since Mission 1.15, and TED was registered as the first
candidate able to produce a **transaction** rather than a listed price. That
distinction is preserved here rather than collapsed:

| | |
|---|---|
| **Established** | the source PUBLISHED a TOTAL_VALUE for the contracts a notice awarded — the value of ALL contracts awarded in the notice, options and renewals included -- not money paid, not necessarily one supplier, and not realised expenditure (Mission 1.15.12; corrected here in Mission 1.20 §0) |
| **Not established** | that a market exists; that a comparable buyer would pay a comparable amount for a *different* product; that anything about a SaaS follows |

A family or type named `WILLINGNESS_TO_PAY` would put the second reading in the
field a consumer branches on. Asserted by test: no scope, window or magnitude
field serialises the strings `willingness`, `wtp`, `demand`, `price`, `pricing`,
`arpu`, `purchase_intent` or `market_size`.

**Not demand.** `PAIN`/`DESIRE`/`BEHAVIORAL`/`MARKET` are a different axis and
Ontology V2 §3.6 is not amended. A public body buying cleaning services is a
transaction that happened.

**Not a price recommendation.** The spread is a fact about contracts already
signed.

**Not temporal.** See §5.

## 4. Eligibility

An observation contributes only if **all** of these hold:

- its record kind is `procurement_notice`;
- it carries a monetary entry of the **requested** `amount_type` — which is a
  required derivation parameter, because a default would pick the semantic for
  the caller and that is how an estimate becomes an amount somebody paid;
- that entry's `pairing` is **`ESTABLISHED`**, so exactly one amount and exactly
  one currency;
- the amount reads as an exact `Decimal`.

Anything else contributes nothing. There is no partial credit and no fallback.

**`PAIRED_MONETARY_AMOUNT`** is the declared required fact, and it is withheld
by exactly the two quality reasons Mission 1.15.8 introduced —
`MONETARY_PAIRING_NOT_ESTABLISHED` and `MONETARY_CURRENCY_ABSENT`. The check is
mechanical rather than a judgement.

## 5. H-37 — the temporal boundary

**H-37 is OPEN and this derivation does not touch it.**

`temporal_basis = NONE`. `direction = NOT_APPLICABLE`. The window carries no
bounds. The module reads no `observed_at`, no period start or end, and neither
`SOURCE_RELATIVE_ORDER` nor `COMPARABLE_INSTANT` — asserted over the AST.

Members are ordered for output **by amount, then by observation key**: a total
order over values and identities, never over time. A test changes one member's
publication date and asserts the derivation is identical.

**This is also why a PARTIAL input is usable.** Every TED normalized record
carries `PERIOD_TIMEZONE_NOT_ESTABLISHED`, which withholds the two temporal
facts — and this derivation requires neither. `signal-contract-v1.md` §10 exists
for exactly this: what matters is whether the **specific** missing fact matters
to the **specific** derivation. The limitation stays visible in every input's
quality reasons; nothing was converted to `VALID`.

**No temporal Signal is derivable from TED until H-37 closes with evidence** —
not from insertion order, not from `collected_at`, not from publication-number
ordering, not from the order the API returned rows in. None of those establishes
chronology.

## 6. H-38 — the pairing boundary

**H-38 is OPEN and this derivation excludes rather than resolves it.**

TED declares monetary amounts and currency codes as arrays and states **nothing**
about positional correspondence. So an entry with several amounts, several
currencies, or a count of one that does not match the other has `pairing =
NOT_ESTABLISHED`, supplies no `PAIRED_MONETARY_AMOUNT`, and **never enters a
numeric cohort**.

Both sequences remain in the normalized record as context. Neither becomes a
number here. Pairing by index would be a reading of the source presented as the
source's own statement.

## 7. Comparability — what makes two contracts one cohort

Five dimensions, and each is load-bearing:

| Dimension | Why |
|---|---|
| **source** | three TED notices are repeated within-source observations, never multi-source evidence |
| **notice class** | a call for competition and a report of an outcome are different procurement stages. An estimated value in a contract notice is what a buyer expected to spend; a total value in an award notice is what a contract settled at |
| **amount scope** | a per-lot value and a whole-notice value are not the same quantity |
| **currency** | two currencies are never one distribution, and no reviewed rate exists to make them one |
| **CPV division** | a cohort without a subject is a statement about a query rather than about the world |

The **amount semantic** is the derivation parameter rather than a grouping
dimension, so a run states which one it is about instead of silently emitting one
signal per semantic.

### 7.1 Why the CPV division, and why the division rather than the code

This is the decision most worth arguing with, and it is the reason the real run
produced nothing.

**Without it**, a cohort is *"EUR totals in this slice of TED"*. Two contracts —
one for cleaning services, one for insurance — would be summarised as one value
distribution, and the Signal would describe a query rather than a market.
`signal-contract-v1.md` prefers a smaller truthful cohort to a larger ambiguous
one.

**The division rather than the full code**, because `90911200` and `90911300`
are cleaning services twice: requiring exact equality would split a genuine
cohort into singletons. The division is the source's own coarsest subject
separation, so requiring it invents nothing.

**A notice classified across several divisions joins no cohort at all.** It has
no one subject, and reading `codes[0]` would make the cohort depend on the order
the source happened to publish the codes in.

## 8. Currency and precision

**No conversion.** No rate, no table, no arithmetic across currencies, no
normalisation to EUR — asserted over the AST. A cohort mixing currencies is
refused with `INCOMPATIBLE_SERIES`.

**Exact decimals end to end.** The normalized payload carries decimal strings,
the extractor reads them through the model's own converter, and the magnitude is
a `Decimal` subtraction. No `float` call appears in the module.

## 9. Provenance

Every contributing observation is in the lineage — not one representative. The
support count equals the lineage size, asserted by test. Through the existing
model each input carries its normalized record, its raw record, the source, the
resource, the collector version and the normalizer version; the signal carries
the extractor id and version, the parameter fingerprint and the derivation
fingerprint.

The scope names the amount semantic, the amount scope, the currency, the notice
class, the CPV codes and their scheme. **A consumer can tell exactly what numeric
concept was aggregated**, which is the whole point of not flattening it.

## 10. Quality and confidence

`derivation_confidence = 1.0`, and that is a statement about **arithmetic**: a
subtraction of two exact decimals either happened or raised. It is not an
evidence strength, not a probability and not a score, and nothing multiplies it.

The limitations that matter are not hidden in a number — they are structural and
readable:

- **support count** is on the window. `N = 2` says so;
- **one source.** The scope names `ted-eu` and nothing else. Cross-source
  independence is Evidence aggregation's question, later;
- **PARTIAL inputs.** Every member's quality reasons travel with it;
- **no temporal basis.** `NONE` says the members are related by comparability
  and by nothing else.

## 11. The real executions

### 11.1 Mission 1.15.9 — zero, and why that was right

Run through `run_signal_derivation_job` over the three normalized TED records,
once per monetary semantic.

| | |
|---|---|
| Normalized observations inspected | **3** |
| Carrying an eligible paired amount | **2** (both `TOTAL_VALUE`, `NOTICE`, `EUR`) |
| Cohorts formed | **2** |
| Cohorts meeting minimum support | **0** |
| **Signals created** | **0** |

**Why.** The two award notices carrying a EUR total value are classified in
**different CPV divisions** — `90` (cleaning services) and `66` (insurance
services). They are two markets, so they form two cohorts of one, and one
contract stating an amount is an observation rather than a derivation.

The third notice contributed to no cohort at all: it is a contract notice with no
monetary entry, and its CPV codes span divisions `33` and `34`, so it has no
single subject.

```text
group  cpv_division=66  CONTRACT_AWARD_NOTICE   1 member   INSUFFICIENT_INPUT_OBSERVATIONS
group  cpv_division=90  CONTRACT_AWARD_NOTICE   1 member   INSUFFICIENT_INPUT_OBSERVATIONS
```

**Eight derivation runs are recorded and zero signals were written.** A refused
derivation gets a run record, never a row in a table of signals (ADR-021).

### 11.2 Mission 1.15.10 — one Signal, and what the data corrected

The acquisition was designed for comparability first: one CPV division, one day
(2023-03-01, the day that already held the system's only division-90 EUR award
total), award notices only, chosen before execution. Four more notices
arrived, three of them award notices with a EUR total value in division 90.

| | |
|---|---|
| Members | `125972-2023`, `126676-2023`, `127668-2023` |
| Amounts | 73 415.22, 440 000, 759 960.24 EUR |
| Magnitude | **686 545.02** |
| Magnitude kind | `ABSOLUTE_DIFFERENCE`, max minus min |
| Unit | `EUR`, `INHERITED` |
| Direction | `NOT_APPLICABLE` |
| Temporal basis | `NON_TEMPORAL` |
| Extractor | `procurement-value-contrast@1.0.1` |

Re-derived identically: **0 new, 1 unchanged**.

**What the real data corrected.** The scope carried only the **first** member's
CPV codes. With one member per cohort in 1.15.9 that was invisible; with three
members carrying four different codes it was plainly wrong, because the scope is
what tells a reader which market the contrast is about. The scope is now the
**union** of every member's codes, and the extractor is `1.0.1` because the same
inputs now produce a different scope. The `1.0.0` row was deleted and the signal
re-derived rather than left standing beside its successor.

**Two notices in the window were correctly excluded**, and they are worth naming
because they show the cohort rule doing real work rather than nominal work:
`127009-2023` spans divisions 77 and 90 and is denominated in PLN, and
`127459-2023` spans 45 and 90. A cohort mixing currencies would compare numbers
that are not comparable, and that is exactly what §7 exists to prevent.

## 12. What this one Signal supports, and what it does not

It supports: *within division 90 award notices published in this window, the
largest EUR total value exceeded the smallest by 686 545.02 EUR.*

It does **not** support any of the following, and §3 is the section to re-read
before anyone tries:

- that the market is growing, shrinking or moving — three notices in one window
  are `NON_TEMPORAL`, and H-37 blocks any temporal reading regardless;
- that buyers are willing to pay 686 545.02 for anything — the magnitude is a
  spread between two contracts, not a price;
- that 90 is a representative sample of anything — the cohort is every
  qualifying notice **in this bounded query**, not in the market.

## 13. Open questions

| | |
|---|---|
| **H-37** | what the offset in a TED publication date means. **OPEN** — this derivation avoids depending on it and does not close it |
| **H-38** | whether TED monetary arrays align positionally with their currency arrays. **OPEN** — this derivation excludes unpaired entries and does not close it |
| H-36A | **NOT ESTABLISHED**, untouched |
| H-36B | **NOT ADDRESSED**, untouched |

Neither H-37 nor H-38 is closed by an extractor being able to avoid it. Closing
either needs first-party evidence.

## 14. What does not exist

Nothing interprets this Signal. No Claim cites it, no ClaimRevision, no
Evidence, no ReliabilityAssessment, no Opportunity, no embedding, no score —
and no Opportunity or ReliabilityAssessment exists for any source at all. A
Signal describing a transaction-value contrast still does not say that a market
exists or that anyone will buy anything, and those are later questions with
their own missions.
