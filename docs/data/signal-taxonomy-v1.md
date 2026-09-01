# Signal Taxonomy V1

**Status:** Authoritative for the Signal layer. **Both types are implemented as
of Mission 1.11.1**, and five real Signals exist.
**Date:** 2026-08-30 (Sprint 1 / Mission 1.11)
**Related:** [`signal-contract-v1.md`](signal-contract-v1.md),
[`signal-model-gap-analysis-v1.md`](signal-model-gap-analysis-v1.md),
[`signal-temporal-semantics-v1.md`](signal-temporal-semantics-v1.md),
[ADR-020](../architecture/adr/ADR-020-signal-derivation-model.md).

---

## 1. Three things were called "signal family". Now they have three names

This has to come first, because two of the three already existed and the
collision is what made the taxonomy question hard to see.

| Name | What it classifies | Kind | Where |
|---|---|---|---|
| `DemandSignalFamily` | **Demand**: `PAIN`, `DESIRE`, `BEHAVIORAL`, `MARKET`. A dimension of an Opportunity | Closed enum | Ontology V2 §3.6, `domain.v1.json` |
| `signal_family` (registry) | What a **source** could expose: `trend`, `curiosity`, `developer_activity`… sixteen entries | Registry rows | ADR-017, migration 0010, `registry.source_signal_coverage` |
| `SignalQuantityFamily` | What kind of **quantity a derived Signal is about** | Closed enum | This document, `nlp.signals.quantity_family` |

They are three different relations over three different subjects — an
opportunity, a platform, a derivation — and none determines another. A source
covering `trend` may yield a signal that is not about demand at all; a demand
family says nothing about what a number measures.

The third one is new. The first two are unchanged, and **Ontology V2 §3.6 is not
amended by this mission**: the demand families remain exactly four, exactly
closed, and exactly what they were. What stops being true is the *claim* that
`nlp.signals` carries one on every row.

---

## 2. Why the demand family is not the Signal family

`nlp.signals.signal_family` has carried `CHECK (... IN ('PAIN', 'DESIRE',
'BEHAVIORAL', 'MARKET'))` since Mission 0.1. That is a design decision, made
before any source existed, that **every Signal is evidence of demand**.

Two real sources now exist and neither produces one.

**GDELT.** A contrast between two term frequencies in one 15-minute bucket says
how often two tokens occurred in the text GDELT processed. Mission 1.11 §25
lists what that can also be: a news event, a crisis, a celebrity, weather,
politics, a disaster, a sports fixture. `climate` appearing 55 times is not a
complaint, not a wish, not a behaviour and not a market event. It is a count of
occurrences.

**World Bank.** A population figure moving between 2018 and 2019 is a
demographic measurement. Calling it `MARKET` would say a market changed, which
is a reading of the number rather than the number.

Forcing either into one of four demand buckets puts an interpretation in the
field a consumer branches on — the precise failure `normalized-record-v1.md`
guards against one layer down, where a field encoding "this indicates growing
demand" would be inherited as a fact by every stage downstream.

**So the demand family is not dropped. It is relocated.** It classifies an
assertion about demand, and an assertion about demand is a **Claim**, or at most
a signal type that genuinely extracts a demand statement from text — a future
`stated_complaint` over discussion content, which does not exist and is not
being designed here.

### Where it will attach when it is needed

Not as a per-row column. `registry.registry_entries` already carries
`maps_to_registry` / `maps_to_id` (migration 0010), whose whole purpose is an
entry projecting onto a canonical vocabulary. A future `signal_type` entry whose
derivation genuinely produces a demand statement points at the
`demand_signal_type` entry it corresponds to, **once**, reviewably, on the type
— rather than being set per row by an extractor.

Both V1 types map to nothing, and `NULL` is the finding rather than a gap
somebody forgot to fill in. Migration 0010 reached the same answer for `TREND`,
`COMMERCIAL`, `COMMUNITY` and `DEVELOPER_ACTIVITY`, and for the same reason.

---

## 3. `SignalQuantityFamily` — closed, and mechanical on purpose

```text
LEXICAL_FREQUENCY | MEASURED_SERIES
```

| Value | What the number is about | Scope shape |
|---|---|---|
| `LEXICAL_FREQUENCY` | How often language tokens occur in text a source processed | Carries a term and a source language label. **No geography key** |
| `MEASURED_SERIES` | A numeric quantity a source measures or reports over a period | Carries a metric and a geography |

**Closed, not a registry.** A consumer branches exhaustively on it because the
two families have different scope shapes and different magnitude units — code
reading a lexical signal's geography would be reading a key that is not there.
An unhandled third value would be a bug rather than a gap, which is Ontology V2
§14.2's test for a closed enum. Adding a third is a contract change with an ADR.

**A third was added in Mission 1.15.9, and this is the ADR it required:
ADR-029.** `TRANSACTION_VALUE` -- the value at which a transaction between named
parties was recorded. It exists because Mission 1.15.8 added the
`procurement_notice` record kind and neither existing family could read it, and
it carries no metric, which is precisely why `MEASURED_SERIES` could not be
widened to hold it. It is still not a demand family.

**Mechanical, not interpretive.** Each value says what kind of quantity the
derivation is about, and nothing about what it means for a market. That is the
whole point: `ATTENTION` was considered and rejected as the family for GDELT,
because attention is something people pay and what GDELT counts is how often a
token appeared in news text. The boundary Mission 1.11 restates in its opening —
GDELT `COUNT` is `source_measured_frequency`, not interest and not popularity —
is violated by a family name as surely as by a column.

**It mirrors the record kinds, and that is not an accident.** Two canonical
record kinds exist and each supports one family. A future derivation over both
kinds at once would have no single family, and that is the case that would force
this enum to be revisited rather than quietly widened.

---

## 4. `signal_type` — a registry, two entries

`REGISTRY`, per Ontology V2 §14.3, for the same reason `demand_signal_type` is
one: the individual types are expected to grow as sources and extraction methods
appear, and adding one must never require a migration.

| id | Family | Derivation | Justified by |
|---|---|---|---|
| `lexical_frequency_contrast` | `LEXICAL_FREQUENCY` | The relation between the frequencies of two or more lexical terms observed under one identical source period label and one identical source language label | The two real GDELT records: bucket `20260830091500`, `ENGLISH`, `climate` and `weather` |
| `lexical_frequency_change` | `LEXICAL_FREQUENCY` | The change in one term's frequency between two **adjacent** source buckets of one stream. Added in Mission 1.12.1, once H-32 closed | Four real GDELT records across buckets `20260830184500` and `20260830190000` |
| `numeric_period_change` | `MEASURED_SERIES` | The change in one metric, for one geography, between two periods on a common timeline | The six real World Bank records: `SP.POP.TOTL`, `DEU` and `FRA`, 2018 to 2020 |

**Two, because two data shapes exist.** Mission 1.11 §35 asks for a small
extensible V1 and forbids eighty speculative types. Each of these is justified
by records this repository currently holds, and neither was invented to round
out a taxonomy.

### A registered type is vocabulary, not code

Exactly the distinction Mission 1.10 drew for record kinds and Mission 1.10.1
kept:

| | |
|---|---|
| the two type entries | registered by migration 0012 |
| the families | declared in the contract, generated to both surfaces |
| the model | `sros_signal_model`, with tests over synthetic objects |
| an extractor | **three**: `numeric-period-change@1.0.0`, `lexical-frequency-contrast@1.0.0`, `lexical-frequency-change@1.0.0` |
| `IMPLEMENTED_EXTRACTORS` | **all three** |
| `nlp.signals` | **7 real rows** |

Mission 1.11 registered the **vocabulary** and no extractor; Mission 1.11.1
added the extractors. The two remained separate claims throughout, which is what
made it possible to design the taxonomy in one mission and implement against it
in the next without either pretending to be the other.

`SIGNAL_EXTRACTORS` in `sros_signal_model` stays **empty** and always will: that
package says what a Signal IS, and `validate_signals.py` fails the build if an
extractor appears in it. `IMPLEMENTED_EXTRACTORS` in `sros_nlp` is the claim
that code exists.

---

## 5. Names that were evaluated and not adopted

Mission 1.11 §25 says not to approve its example names automatically. They were
not.

| Candidate | Verdict |
|---|---|
| `LEXICAL_FREQUENCY_OBSERVED` | **Rejected.** It is the normalized record with a new table name. Contract §3's contrast rule exists to forbid exactly this |
| `LEXICAL_FREQUENCY_CHANGE` | **Implemented in Mission 1.12.1** as `lexical_frequency_change`, once Mission 1.12 closed H-32 on GDELT's own evidence. It was deferred rather than rejected for three missions, which is what the distinction was for |
| `LEXICAL_ATTENTION_GROWTH` | **Rejected.** "Attention" is an interpretation of a count, "growth" is an interpretation of a difference, and one name asserts both |
| `LEXICAL_ATTENTION_DECLINE` | **Rejected**, same reason. Direction is a field, not a type: two types differing only in sign would make a decline unfindable when looking for the term |
| `NUMERIC_LEVEL` | **Rejected.** A level is one observation |
| `population_growth`, `economic_trend`, `internet_penetration_change` | **Rejected as types.** Each names a *metric*, and the metric is scope. One `numeric_period_change` type over `SP.POP.TOTL` says everything three metric-specific types would, without a new type per indicator (Mission 1.11 §26) |
| `ATTENTION`, `ECONOMIC`, `ACTIVITY` as families | **Not adopted.** All three are readings. `ECONOMIC` is the closest to defensible and still fails: `SP.POP.TOTL` is demographic, and an economic family would classify it by what somebody hopes to conclude from it |

The pattern in the rejections is one rule: **a name must not assert what a
consumer is supposed to conclude.** `contrast` and `change` are operations;
`growth`, `attention`, `momentum`, `interest` and `demand` are conclusions.

---

## 6. What the taxonomy deliberately does not carry

- **No sentiment and no valence.** Nothing measures either, no source supplies
  one, and a nullable column nothing can fill is an invitation to fill it by
  resemblance — the H-30 failure mode one layer up.
- **No market, category or topic dimension.** A lexical term is not a topic
  (Mission 1.11 §50). Turning `climate` into a category is classification, and
  classification is a later stage with its own confidence.
- **No motivation.** `CURIOSITY` is why a person acts (Ontology V2 §3.3); a
  signal says what the data shows. Mission 1.11 §6 draws the line and this
  taxonomy holds it: a signal may one day *support* a hypothesis that curiosity
  is present, and it may not encode it.
- **No strength band, no tier, no rank.** Those are cross-signal comparisons and
  §30 forbids the scale they would need.
- **No lifecycle enum.** A derivation that cannot run produces no Signal
  (contract §11).
