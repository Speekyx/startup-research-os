# Mission 1.11 — Signal Model & Derivation Contract V1

**Sprint:** 1
**Date:** 2026-08-30
**Status:** Complete. **Model and contract only — no extractor exists and
`nlp.signals` holds 0 rows.**
**Specifications:** [`signal-model-gap-analysis-v1.md`](../data/signal-model-gap-analysis-v1.md)
(written first, per §32), [`signal-contract-v1.md`](../data/signal-contract-v1.md),
[`signal-taxonomy-v1.md`](../data/signal-taxonomy-v1.md),
[`signal-temporal-semantics-v1.md`](../data/signal-temporal-semantics-v1.md),
[ADR-020](adr/ADR-020-signal-derivation-model.md).

---

## 1. What was delivered

| | |
|---|---|
| Gap analysis | 16 gaps against `nlp.signals`, classified, **before** the migration |
| Contract | `sros.signal/1` — identity, lineage, scope, temporal basis, required facts, refusals |
| Taxonomy | `SignalQuantityFamily` (closed, 2) + `signal_type` (registry, 2 entries) |
| Temporal semantics | `SignalTemporalBasis` (4), the ORDER/INSTANT split, and **H-32** |
| Contracts | 9 closed enums, 2 registry names, `domain.v1.json` 1.5.0 → **1.6.0** |
| Model | `packages/signal-model/python/sros_signal_model` — 4 modules, no extractor |
| Migration | `0012_signal_derivation_model.sql`, forward-only, RLS, composite FKs |
| Tests | **65 synthetic** model tests + 13 live constraint probes, all rolled back |
| Signals created | **0** |

---

## 2. The audit, and what it found

`nlp.signals` has existed since Mission 0.1. §31 says not to assume it is
correct merely because it exists, so it was measured against the contract rather
than the contract being fitted to it. The table is **empty**, nothing writes to
it, and nothing reads it.

Read as a design, it encodes three assumptions made before any source existed —
and the two sources that now exist falsify all three:

| Assumption | Falsified by |
|---|---|
| A signal comes from exactly one normalized record | Every derivation that says something an observation does not already say |
| A signal is a demand signal | A GDELT term count and a World Bank population figure |
| A signal is produced by a language model | The first extractors, which are arithmetic |

Plus one arithmetic problem: `value DOUBLE PRECISION CHECK (value BETWEEN 0 AND
1)` cannot hold a change from 55 to 81, and is a float in a system that parses
source numbers with `parse_float=Decimal` so IEEE-754 never touches them.

Two of the sixteen gaps were **pre-existing defects in other people's tables**,
found while auditing the boundaries and named in the analysis before being
fixed:

- **GAP-12.** `scoring.evidence.signal_id` was a single-column foreign key.
  Migration 0005 made `claim_id` and `independence_group_id` composite for
  exactly this reason and left this one, because no signal existed to point at.
- **GAP-13.** `signal_type_registry` defaulted to `demand_signal_type`, whose
  only two entries are written by a **development seed**. So `nlp.signals`
  accepted an insert on a developer's machine and rejected every insert on the
  empty database CI and any real deployment start from. `validate_schema.py`
  catches a *migration* that depends on a seed; it did not catch a table whose
  *runtime writes* do.

---

## 3. §50 — the questions, answered

### What exactly is a Signal?

> A reproducible statement about a **relation between two or more canonical
> observations**, produced by a named extractor at a named version over stated
> parameters, carrying its own lineage, scope, temporal basis and a confidence
> in the derivation — and asserting nothing about what the relation means.

### How does it differ from a NormalizedRecord?

A NormalizedRecord **renames and reshapes** one source observation and stops. A
Signal **compares**. The record is source-preserving and single-origin; the
signal is derived, multi-origin, parameterised and versioned by its extractor.

### How does it differ from Evidence?

Evidence is **claim-scoped**. It adds `direction` (supports or contradicts
*what*), `relevance` (to *what*), `directness`, `reliability`,
`extraction_confidence`, `observation_category` and an independence state — none
of which is a property of a derivation, and all of which are properties of a
derivation *relative to a proposition*. A Signal has no claim, so it cannot have
any of them. `scoring.evidence.signal_id` is the link and it already existed.

### How does it differ from a Claim?

A Claim is a **proposition** with an epistemic type (`OBSERVED / INFERRED /
PREDICTED / RECOMMENDED / HYPOTHESIS`), a stable identity and append-only
revisions. "climate occurred 1.47× as often as weather in that bucket" is a
signal; "there is growing demand for climate-adaptation tooling" is a claim, and
nothing in this layer can turn the first into the second.

### How does it differ from an Opportunity?

An Opportunity is a product or business synthesis over many claims, with a
market scope, a monetisation model and a score. A signal is one arithmetic
relation between two observations.

### Can one NormalizedRecord alone produce a valid Signal?

**No.** §37 says there is no predetermined answer, and the answer is the
**contrast rule**: a derivation whose output is a function of exactly one
observation, and whose assertion is recoverable from that observation's payload
alone, is the observation renamed.

A contrast needs something to contrast against, and there are exactly two
candidates — another observation, or a reviewed reference baseline. **No
baseline exists**, and inventing one is the pattern the aggregation framework
forbids by name. So V1's rule is mechanical: **at least two distinct source
observations**, with the doorway named rather than nailed shut.

**Distinctness is over `observation_key`, never over `normalized_record_id`.**
One observation can have several normalized rows and D-08 has not decided which
to read; counting rows would let a normalizer upgrade manufacture a contrast out
of one observation. Two contributing rows sharing a key are refused as
`AMBIGUOUS_OBSERVATION_LINEAGE`.

### What are SignalFamily and SignalType?

`quantity_family` — **closed enum**, `LEXICAL_FREQUENCY | MEASURED_SERIES`. What
kind of quantity the signal is about. Closed because the two families have
different scope shapes and consumers branch exhaustively.

`signal_type` — **registry**, two entries: `lexical_frequency_contrast` and
`numeric_period_change`, each justified by records this repository holds.

**The demand families are not this axis**, and that is the mission's largest
finding. See §4 below.

### Is signal direction independent from sentiment?

Yes, and enforced by absence. `SignalDirection` is `INCREASING | DECREASING |
UNCHANGED | INDETERMINATE | NOT_APPLICABLE` — change only. `POSITIVE` and
`NEGATIVE` were on the candidate list and are **not in the enum**: a
complaint-frequency signal can be `INCREASING` while the sentiment of the
underlying text is negative, and one enum holding both makes that sentence
unrepresentable. **Sentiment is not modelled at all** — nothing measures it, and
a nullable column nothing can fill is an invitation to fill it by resemblance.

### Is signal magnitude independent from confidence?

Yes, and a test asserts it. A magnitude of 100,000,000 with a derivation
confidence of 0.2 is representable. Magnitude says how much; confidence says how
sure we are the derivation computed what it says.

### What confidence scale is used?

`derivation_confidence` on `[0,1]`, per the project rule that a field named
`confidence` is always the unit interval and a field named `*_score` is always
0–100. Out of range is **rejected, not clamped**.

**No 0–100 magnitude scale was introduced.** §8 permits one only where a
cross-signal comparison justifies it, and §30 states why none does.

### Does Signal duplicate EvidenceScore?

No. There is **one** number and it is narrow: confidence that the derivation
computed what it says it computed. §38 offers the option of a second
`evidence_strength`, and the existing architecture answers it — evidence
strength is claim-relative and a Signal has no claim, so a second number here
would be an `EvidenceScore` computed without the thing that gives it meaning.

A deterministic extractor's derivation confidence is **1.0**, and that is a
statement about arithmetic, not about the market. The coverage facts sit beside
it unweighted: how many observations contributed, how many were excluded and
why, how many distinct sources. Counts are diagnostics and never multipliers.

### How are derivation parameters versioned?

Serialised canonically — sorted keys, exact decimals as text, floats **refused**
because a parameter that round-trips through IEEE-754 cannot be fingerprinted
reproducibly — and hashed into `parameter_fingerprint`, which enters the
derivation identity.

The extractor **declares its parameter names** and the mapping's keys must equal
that declaration exactly. A declared name not supplied is
`PARAMETERS_INCOMPLETE`; a key supplied and not declared is the same refusal from
the other side. The model does not know what any extractor's parameters should
be and does not have to — it enforces that the extractor said.

### How is lineage represented?

`nlp.signal_inputs`, one row per record **considered** — contributing or
excluded — carrying `normalized_record_id`, `raw_record_id`, `source_id`,
`observation_key`, `record_kind_id`, `period_label`, `period_type`, the input's
quality and quality reasons, its role, its refusal reason and the facts it
withheld.

Denormalized on purpose: raw records expire eleven months before the rows that
reference them. **No independence state, no group id, no reliability and no
weight** — this layer preserves the facts and Evidence Aggregation makes the
judgement with them.

### What is the deterministic Signal identity?

```text
sha256(canonical_json({schema, workspace_id, signal_type, quantity_family,
                       extractor{id,version},
                       inputs[{observation_key, normalized_record_id}] in order,
                       parameter_fingerprint,
                       window{basis, period_labels, resolution}}))
```

with the row id a UUIDv5 over that fingerprint, and
`UNIQUE (workspace_id, derivation_fingerprint)` in the database.

**The outputs are excluded** — magnitude, direction, confidence. A changed
magnitude under an unchanged identity means the extractor is not deterministic
or an input changed, and that must be *reportable* rather than absorbed into a
new row. So are `derived_at`, `correlation_id`, the excluded inputs, and the
research session.

### How does PARTIAL normalized quality affect signal derivation?

It does not, unless the **specific** missing fact matters to the **specific**
derivation.

`INVALID` is never derivable from — a record that could not be represented must
not be read as an observation. `PARTIAL` is assessed per fact: a derivation
declares its `SignalRequiredFact` set, and the model computes what each input
withholds from that record's own quality reasons and its record kind.

Every GDELT record is `PARTIAL` and a within-bucket contrast between two terms
needs neither of the two things it is missing. That case is the reason the
mechanism exists rather than a quality filter.

### Which operations are safe while H-29 remains open?

| Operation | Status |
|---|---|
| Contrast two terms' frequencies within one bucket, one language label | ✅ `SAME_PERIOD_LABEL` |
| Count the distinct buckets a term appears in | ✅ `NONE` — set cardinality, no order |
| Any derivation whose temporal semantics are label EQUALITY | ✅ |

### Which are blocked by H-29?

Everything needing a **shared timeline**: aligning a GDELT bucket with a World
Bank year or any other source, comparing against a differently zoned source, and
anything reported "as of" a wall-clock time. Enforced by a database CHECK —
`observed_at` is `NULL` unless the basis is `COMPARABLE_INSTANTS`.

**And separately, H-32.** §13 asks whether same-source bucket ordering is safe
without a timezone. It is a *different question* and it is now open as **H-32**.
The argument for granting it is good — a fixed-width stamp orders
lexicographically inside any fixed offset, and the stamp is the published
filename, which cannot repeat inside a directory — but it is an inference about
the publisher's mechanism, not a retrieved statement about the data. If the
stamps were local time in a DST zone, one hour a year would repeat and order
would invert inside it.

So **sequential frequency comparison, growth, decline, moving averages and
rolling windows are blocked by H-32**, and a direction other than
`NOT_APPLICABLE` requires an ordered basis — enforced by a second CHECK.

H-32 is **strictly weaker and separately answerable**: a page stating the zone
closes both; a page stating only that the stamps are monotonic closes H-32 alone
and unblocks six operations without anyone asserting UTC. The escape hatch is
`ORDER_ESTABLISHED_WITHOUT_TIMEZONE`, which is **empty**, and whose entries
require a stated basis the way a geography map entry does.

### Which are safe while H-30 remains open?

Equality of the **exact source label within one source and one scheme**.
`ENGLISH` from `cld2-language-name` equals `ENGLISH` from `cld2-language-name`,
and that asserts nothing about what either maps to.

### Which are blocked by H-30?

Aggregating `ENGLISH` with BCP-47 `en`; any cross-source language synthesis; any
canonical language tag on a signal at all. The constructor refuses
`canonical_language_tags` unless the derivation required `CANONICAL_LANGUAGE`
and every input supplied it, which no GDELT record does.

### Can GDELT COUNT itself become a Signal?

**No.** A count is one observation. `LEXICAL_FREQUENCY_OBSERVED` was evaluated
and rejected — it is the normalized record with a new table name.

### Can rising GDELT COUNT automatically mean demand?

**No**, twice over. Today it cannot even be computed — a rising count needs two
buckets in a known order, which H-32 blocks. And if it could, the derivation
would say a count rose. A term frequency may reflect a news event, a crisis, a
celebrity, weather, politics, a disaster or a sports fixture; deciding which is
a Claim, with its own evidence.

### Can a GDELT lexical term automatically become a topic?

**No.** The scope carries the term verbatim and no market, category, topic or
motivation dimension exists — asserted over the serialised scope, so a *new*
field carrying one would fail too. Classification is a later stage with its own
confidence and its own failure modes.

### Can a World Bank numeric value itself automatically become a market Signal?

**No.** One value is one observation. A change between two years is a Signal —
`numeric_period_change` — and it says a measurement moved. `SP.POP.TOTL` is
demographic, and whether a population change is a *market* event is exactly the
interpretation this layer refuses. One type over the metric, rather than
`population_growth` and `internet_penetration_change` as separate types: the
metric is scope.

### Are contradictory Signals resolved at this layer?

**No.** Each remains independently derived and independently stored.
Contradiction is information about the world, and competing observations are
preserved rather than overwritten. Resolution belongs to evidence aggregation,
which decomposes agreement and disagreement into four masses — claim-relative,
and a Signal has no claim to disagree *about* yet.

### Can Signal extraction be deterministic?

**Yes, and V1 is designed so the first ones are.** Every field can be produced
by arithmetic over canonical values: exact decimals, label equality, set
cardinality.

### Is Signal intrinsically LLM-based?

**No**, and this is now a constraint rather than a sentence.
`derivation_kind = DETERMINISTIC` requires `model_version` and `prompt_version`
to be **absent**; `MODEL_DERIVED` requires a model version. The database refuses
both violations. No LLM was called in this mission.

### Was a schema migration required?

**Yes** — `0012_signal_derivation_model.sql`, forward-only, written **after**
the gap analysis. It reshapes `nlp.signals`, adds `nlp.signal_inputs` with RLS
and composite tenant-safe foreign keys, registers two `signal_type` entries, and
closes GAP-12 and GAP-13.

### Were any production Signals created?

**No.** `nlp.signals` = 0 and `nlp.signal_inputs` = 0, verified after the
migration and again after the constraint probe. Every model test uses synthetic
objects; every live probe ran inside a rolled-back transaction.

### Did all existing Raw/Normalized records remain byte-for-byte unchanged?

**Yes.** 8 raw and 8 normalized records, `(source_id, observation_key,
content_hash)` digest identical before and after:

```text
BEFORE  d8cf83214a930be67f42f018224a657cdb0fdb8028f9f5414eccbd507e55140c
AFTER   d8cf83214a930be67f42f018224a657cdb0fdb8028f9f5414eccbd507e55140c
```

World Bank 6 / 6, GDELT 2 / 2. Embeddings 0, claims 0, evidence 0,
opportunities 0, scores 0.

### Is Mission 1.11.1 safe to implement the first deterministic signal extractors?

**Yes**, with one thing to plan around and one thing to decide.

**Plan around:** the derivations available today are not the obvious ones.
`numeric_period_change` over World Bank is fully derivable — `COMPARABLE_INSTANTS`,
`VALID` inputs, six real records spanning three years and two countries.
`lexical_frequency_contrast` over GDELT is derivable **within one bucket** and
nowhere else. A frequency *change* is blocked by H-32. The source with two
`PARTIAL` records supports fewer temporal derivations than the source with six
`VALID` ones, and the whole difference is two open questions.

**Decide:** where a refused derivation should be logged. The contract is
deliberate that no Signal row records a refusal, and a derivation run that
refuses everything currently leaves no trace outside its own logs.

---

## 4. The finding worth arguing with

**`nlp.signals.signal_family` presupposed that every signal is a demand
signal**, and both real sources produce signals that are not.

A contrast between two GDELT term frequencies says how often two tokens occurred
in text GDELT processed. §25 lists what else that can be. A World Bank
population delta is a demographic measurement. Forcing either into `MARKET`
would assert a demand reading the data does not carry, in the one field a
consumer branches on — the failure the normalization layer refuses one level
down, where a field encoding "this indicates growing demand" would be inherited
as a fact by every stage downstream.

`ATTENTION` was considered as the GDELT family and rejected for the same reason
in weaker form: attention is something people *pay*, and what GDELT counts is
how often a token *appeared*. The mission's own opening boundary — GDELT `COUNT`
is `source_measured_frequency`, not interest and not popularity — is violated by
a family name as surely as by a column.

So the demand families are **relocated, not dropped**. They classify an
assertion about demand, which is a Claim, or at most a future signal type that
genuinely extracts a demand statement from text. When one exists, it projects
onto `demand_signal_type` through the `maps_to` mechanism migration 0010 already
added — recorded once on the reviewable type, never set per row by an extractor.
Both V1 types map to nothing, and `NULL` is the finding rather than a gap
somebody forgot to fill in.

**Ontology V2 §3.6 is not amended and no ontology version was created.** The
demand families remain four and closed. Three things were called "signal family"
— the demand enum, the ADR-017 source-coverage registry, and this — and they now
have three names.

---

## 5. Two defects found while working

### The refusal probe passed while measuring nothing

Twelve `INSERT`s inside rolled-back transactions, each expecting a constraint to
refuse it. Ten reported `ok` on the first run and all ten were wrong: the fixture
omitted `correlation_id`, which is `NOT NULL`, so every insert failed before
reaching any CHECK.

A test that only asks *did it fail* cannot tell a constraint working from a
fixture that never got there. What exposed it was the **two cases that expected
an insert to succeed** — a suite made only of refusals has no way to notice that
everything refuses.

The probe now asserts `exc.diag.constraint_name` against the constraint expected
to refuse, and the model tests assert `refusal.reason` rather than that an
exception was raised. Recorded as `testing-strategy.md` §24.

### The schema validator was checking columns that no longer exist

Adding `nlp.signals` to the retention check under its real column name made it
fail: the validator reads migration **text**, so a column renamed by a later
migration keeps its original name and every check goes on asserting about a name
the database does not have — passing, while measuring nothing.

Fixing that surfaced the second half. `validate_schema.py` now also strips
constraints a later migration **dropped**, because both live rename cases pair a
drop with a rename (`sources.status` → `lifecycle` in 0004,
`signals.signal_family` → `quantity_family` in 0012) and the dropped definition
was being compared against the contract alongside the one that replaced it — so
a value set that was deliberately changed read as drift.

Neither was introduced by this mission. Both were latent since Mission 1.0 and
became visible the moment a table renamed a column the validator cared about.

---

## 6. Scope discipline

**Delivered exactly what §33, §34 and §49 asked for, and nothing downstream.**

| Forbidden by the brief | State |
|---|---|
| Production signal extraction | Not implemented. `SIGNAL_EXTRACTORS` empty |
| Real Signals | 0 |
| Embeddings | 0. Nothing loads BGE-M3, writes a vector or touches Qdrant. D-12 untouched |
| Clustering | None |
| Opportunities | 0 |
| Scoring | None. D-03 untouched, no calibrated profile, no aggregation result stored |
| Claims / Evidence from the pipeline | 0 |
| LLM calls | None |

**One deliberate exception, named in the gap analysis before it was made.** §47
says the Claim/Evidence model stays untouched, and migration 0012 adds a
composite foreign key to `scoring.evidence.signal_id`. It changes no column, adds
no semantics and stores nothing — it closes a cross-tenant hole (GAP-12) that
§40 explicitly requires closing, on the one column that links Evidence to the
table this mission reshaped. Leaving it would have meant shipping a Signal table
whose only inbound reference could be written across tenants.

---

## 7. Validation

```text
zero-dependency suites   405 tests across 6 packages  (65 new, all synthetic)
pytest suites            215 tests across 6 packages
schema validation        9 invariant groups, 35 tables
normalization guard      9 boundary groups
evidence aggregation     8 checks, 0 warnings; production scoring still blocked
source registry          27 sources, 33 evidence records, 0 warnings
compliance               12 conditions, 5 capabilities, 3 authorizable
contracts --check        3 generated artifacts current
TypeScript conformance   21/21
mypy strict              120 source files
ruff + ruff format       clean, 330 files
constraint probe         13 constraints, each verified BY THE CONSTRAINT THAT REFUSED
```

Post-suite: **21 tenant and 14 global tables unchanged by the run.**

---

## 8. Risks left open

- **H-32 is new and it is the cheap one.** It blocks six GDELT operations and one
  first-party sentence would close it. If it is left open, the GDELT collector
  keeps producing data no temporal signal can read.
- **The two-observation rule is the decision to disagree with out loud.** It
  makes a genuinely single-observation indication unrepresentable. The doorway is
  named — a reviewed baseline, by ADR — and until one exists the rule is
  absolute.
- **D-08 matters at two layers now.** A normalizer version bump already produces
  a second row per observation; a signal derived from schema-1 rows and one from
  schema-2 rows are two derivations. The model refuses to conflate them and does
  not decide which to read.
- **Nothing records a refused derivation.** Deliberate (§27), and it means "we
  tried and there was nothing" is currently invisible outside a job log.
- **`nlp.embedding_provenance.normalized_record_id`** carries the same
  single-column FK weakness GAP-12 fixed on evidence. Left alone: D-12 is open
  and nothing writes it.
- D-03, D-10, D-12, H-12, H-13, H-22 to H-27, H-29, H-30, H-31,
  PROFILE-NOT-CALIBRATED unchanged.
