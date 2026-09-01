# TED-EU Transaction Signals V1

**Authoritative.** Mission 1.15.9, ADR-029. The first derivation over
procurement notices, what it asserts, and the four things it refuses to assert.

**State: the extractor exists and produced ZERO real Signals.** Three normalized
TED notices were inspected, two carried an eligible amount, two cohorts formed,
and neither reached the minimum support. That is the correct answer for the
observations held, not a failure, and §11 gives the exact reason.

**H-37 OPEN. H-38 OPEN. H-36A NOT ESTABLISHED. H-36B NOT ADDRESSED.**

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
| Extractor | **`procurement-value-contrast@1.0.0`** |
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
| **Established** | a named buyer paid a named supplier a stated amount for a stated procurement, and the source published it |
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

## 11. The real execution

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

## 12. What would produce one

Two or more award notices, in the **same CPV division**, with a total value in
the **same currency**, paired. Nothing about the extractor needs to change; the
observations do.

That is a bounded acquisition designed for comparability rather than a larger
one — and it is blocked behind the collector repair recorded in §13.

## 13. Blocking rule for the next TED acquisition

> **Before the next TED acquisition mission**, the collector's Decimal invariant
> must be repaired with an appropriate version bump and compatibility treatment.
> `ted-search-api@1.0.0` parses its response with plain `json.loads` rather than
> `json.loads(..., parse_float=Decimal)`, which contradicts the manifest's own
> rule. The three records already held are exact at the raw-to-normalized
> boundary and remain valid inputs; the rule is about what is collected **next**.

## 14. Open questions

| | |
|---|---|
| **H-37** | what the offset in a TED publication date means. **OPEN** — this derivation avoids depending on it and does not close it |
| **H-38** | whether TED monetary arrays align positionally with their currency arrays. **OPEN** — this derivation excludes unpaired entries and does not close it |
| H-36A | **NOT ESTABLISHED**, untouched |
| H-36B | **NOT ADDRESSED**, untouched |

Neither H-37 nor H-38 is closed by an extractor being able to avoid it. Closing
either needs first-party evidence.

## 15. What does not exist

No Claim, no ClaimRevision, no Evidence, no ReliabilityAssessment, no
Opportunity, no embedding, no score — for TED or for anything else. A Signal
describing a repeated transaction-value pattern would still not say that a market
exists or that anyone will buy anything, and those are later questions with their
own missions.
