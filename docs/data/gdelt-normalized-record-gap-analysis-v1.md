# GDELT Normalized Record Gap Analysis V1

**Status:** Analysis record. Produced by Mission 1.10 §3, **before** the
canonical model changed.
**Date:** 2026-08-30
**Reads:** `sros_acquisition.normalization.model` (`CanonicalPeriod`,
`CanonicalGeography`, `CanonicalValue`, `NumericObservation`, `RECORD_KINDS`,
`build_normalized`), [`normalized-record-v1.md`](normalized-record-v1.md), and
the two real GDELT RawRecords collected by Mission 1.9.3.
**Related:** [`gdelt-web-ngram-raw-record-v1.md`](gdelt-web-ngram-raw-record-v1.md),
[`gdelt-normalization-contract-v1.md`](gdelt-normalization-contract-v1.md),
[ADR-019](../architecture/adr/ADR-019-lexical-frequency-observation.md).

---

## 0. The question, and the two real records it is asked about

Can the canonical model represent a GDELT WEB-NGRAM observation **without
inventing anything**? The two records that exist are the test:

```json
{"source_id": "gdelt", "resource_id": "web-ngrams/1gram", "gram_kind": "1gram",
 "date": "20260830091500", "lang": "ENGLISH", "ngram": "climate", "count": "55"}
```

The answer field by field is **no for three of four**, and the three failures are
different in kind: one is a missing *state*, one is a missing *value object*, and
one is a missing *record kind*.

## 1. `DATE` → the period

**Source semantics.** A 15-minute bucket label, `YYYYMMDDHHMMSS`, identical to
the filename. **The timezone is not established** (H-29): neither GDELT's dataset
announcement nor its data index states one, and Mission 1.9.3 left `observed_at`
`NULL` rather than assert it.

**Canonical destination.** `CanonicalPeriod`.

**Is it exact?** **No**, and the obstruction is in the constructor:

```python
for name in ("start", "end"):
    if getattr(self, name).tzinfo is None:
        raise ValueError(f"period {name} must be timezone-aware")
```

A canonical period **cannot currently exist** without a timezone. Every route
into one therefore requires choosing a zone we do not have.

| Route | What it would invent |
|---|---|
| `CanonicalPeriod(..., tzinfo=UTC)` | an offset GDELT never published |
| omit the period | the observation loses its time entirely — a frequency with no window is not an observation |
| put the label in a string field only | the 15-minute duration becomes prose no consumer can compute over |

**Is information lost?** Yes, in every route above. The duration, the label and
the zone-status are three facts and no existing field holds all three.

**Would unsupported semantics be invented?** Yes — a UTC offset, in the field a
reader trusts most.

**Is a model change required?** **Yes.**

### 1.1 What the period type should be

`NormalizedPeriodType` already has `INTERVAL`: *"An arbitrary interval the source
stated explicitly, where no calendar unit describes it."* A 15-minute bucket is
exactly that. **No new period type is needed**, and adding a `MINUTE_15` member
would encode one source's cadence into a closed contract enum.

### 1.2 What is actually missing is a *state*, not a type

The gap is that `CanonicalPeriod` can say *when* and cannot say *whether the zone
is known*. Three shapes were considered:

| Option | Rejected because |
|---|---|
| make `start`/`end` nullable | a period with no bounds cannot be computed over, and it would weaken every existing period to accommodate one source — §4 forbids that without justification |
| a second period value object for this kind | two period concepts is worse than one honest one, and every consumer would have to branch on which it got |
| store an aware UTC datetime beside a flag saying it is not really UTC | a lie next to a disclaimer. Code reads the datetime |

**The chosen shape: a `timezone_state`, with naive bounds when it is not
established.** Python's naive `datetime` is *already* the correct representation
of a wall-clock reading with no zone — floating time, in the iCalendar sense.
Using it means:

- `ESTABLISHED` → bounds are timezone-**aware**, the existing rule, unchanged and
  still enforced;
- `NOT_ESTABLISHED` → bounds are timezone-**naive**, and any code that treats a
  naive datetime as UTC has made an error a type checker can see.

**This is not a weakening.** The aware requirement still holds wherever a zone is
established, which is every record written to date.

### 1.3 The consequence for `observed_at`

`build_normalized` currently sets `observed_at = observation.period.start`,
unconditionally. `observed_at` is a `TIMESTAMPTZ`, so a naive start cannot go
into it and an aware one would be the invention again.

**`observed_at` must become `NULL` when the period's zone is unestablished** —
the same answer Mission 1.9.3 reached for the RawRecord, for the same reason and
at the next layer. §4 asks that `observed_at` not be abused; leaving it empty is
how it is not.

**World Bank is unaffected**: `year_period` produces aware UTC bounds and
`ESTABLISHED`, so its six records keep the `observed_at` they have.

### 1.4 The payload must stay byte-identical for World Bank

`period.to_json()` is inside the content fingerprint. Adding a key would change
the hash of every existing record, which §15 forbids.

**`timezone_state` is emitted only when it is not `ESTABLISHED`.** The
asymmetry is safe and is not a hidden default: an ISO-8601 string **already
discloses its offset or its absence**, so `"2018-01-01T00:00:00+00:00"` and
`"20260830T091500"` are self-describing to any reader. The explicit key is added
where the answer is the surprising one, which is also the direction §5's *"a
missing mapping must remain visible"* points.

A consumer reading the key should default it to `ESTABLISHED`, and
[`normalized-record-v1.md`](normalized-record-v1.md) §7.1 says so.

## 2. `LANG` → the language

**Source semantics.** `ENGLISH` — a CLD2 human-readable language **name**, mostly
uppercase, some titlecase, some with underscores. **No authoritative mapping to a
language tag has been established** (H-30).

**Canonical destination.** There are two candidates and both are wrong.

| Candidate | Why it fails |
|---|---|
| `content_language` (the row column) | its contract means a **code**. `ENGLISH` is not `en`, and a name sitting in a column readers take for a code is a guess wearing the clothes of a fact |
| `CanonicalGeography` | **language is not geography.** Spanish is not Spain; the row says nothing about where anything happened, and the registry model already keeps countries and languages apart |

**Is information lost?** Under `content_language`, the *mapping status* is lost:
a reader cannot tell `ENGLISH` from a tag somebody derived.

**Would unsupported semantics be invented?** Under either candidate, yes.

**Is a model change required?** **Yes** — there is no canonical language concept
at all.

### 2.1 The shape, by analogy with geography

§5 asks whether something analogous to `CanonicalGeography.unclassified` is
needed. It is, and the analogy is close enough to copy deliberately:

| Geography | Language |
|---|---|
| `source_code` — verbatim, always | `source_label` — verbatim, always |
| `source_name` | `source_scheme` — which vocabulary the label is from |
| `kind: COUNTRY/AGGREGATE/UNKNOWN` | `mapping_state: ESTABLISHED/NOT_ESTABLISHED` |
| `canonical_code` — only where the map establishes it | `canonical_tag` — only where a mapping establishes it |
| `canonical_scheme` | `canonical_scheme` |

The three facts §5 requires — **source label, canonical tag, mapping status** —
are three fields, and `unmapped()` is the constructor that produces the honest
state without a mapping.

`source_scheme` has no geography counterpart and earns its place: `ENGLISH` means
something only if a reader knows it came from CLD2 rather than from ISO 639's
English names, which overlap and are not identical.

**`content_language` stays `NULL`.** The canonical language lives in the payload,
where it can carry its own status.

## 3. `NGRAM` → the record kind

**This is the gap that decides the mission.**

**Source semantics.** One or two words, exactly as GDELT emitted them. Nothing
classified it: no theme, no entity, no topic.

**Canonical destination.** `NumericObservation` is the only kind that exists, and
it does not fit in two independent ways.

**Its required fields cannot be satisfied.**

```python
required = ("metric.id", "period", "geography.source_code", "observation.value_state")
```

A WEB-NGRAM row **has no geography**. Supplying one would be the invention §5 and
§16 both forbid, and omitting it makes every record `INVALID` — which would be
the model reporting a defect in itself.

**And the term is not a metric.** A metric is a *definition* — population, GDP —
reused across geographies and periods, and `metric.id` is what a value is a
measurement **of**. `climate` is not a definition; it is an **observed lexical
item**, and the thing measured is *how often it appeared*.

| Forcing it into | Would assert |
|---|---|
| `metric.id` | that a term is a reusable measurement definition |
| `metric.name` | the same, with the identity in the wrong field |
| `theme_identifier` semantics | a classification no classifier made |
| entity semantics | a resolution no resolver ran |
| `geography` | a place, where there is a language |
| `unit` | that the term is how the count is measured |
| `description` | that identity is prose |

Every one is on §6's forbidden list, and each is forbidden for a reason the model
can state rather than a stylistic preference.

**Is a model change required?** **Yes: a new record kind.**

### 3.1 Why a new kind rather than a widened one

Loosening `numeric_observation` — making `geography` optional, letting `metric`
hold a term — would make **World Bank's** kind able to express a record with no
geography and a term for a metric. §2 and §15 both refuse that: the existing
model must not get worse to fit a new source, and a kind's `required` list is
what its quality state is computed against.

The kinds registry exists for exactly this (`normalized-record-v1.md` §4), and
this is its first real use.

### 3.2 The name

The kind must describe **source data**, never a derived Signal (§6). Following
the existing `numeric_observation` convention:

**`lexical_frequency_observation`** — *one occurrence count the source measured
for one lexical term, in one language, over one period.*

`LEXICAL_FREQUENCY`, `TERM_FREQUENCY` and `NGRAM_FREQUENCY` were the brief's
examples. The chosen name keeps the `_observation` suffix that says what layer
this is, and keeps `lexical`, which is the word Mission 1.9.2's minimisation
category already uses (`lexical_ngram`). *Frequency* rather than *count* because
it is a count **per bucket per language** — a rate over a stated window — and
saying so removes any reading in which it is a running total.

### 3.3 `gram_size` — §10

Not inferred from spaces in the term, ever: a two-word entry in a unigram file
would be a contract violation and counting spaces would hide it.

§10 asks where it belongs. **Both content and provenance, and not identity:**

| Place | Why |
|---|---|
| **payload** — `term.gram_size` | a bigram is a different *kind* of observation from a unigram, and a consumer comparing frequencies must not mix them |
| **provenance** — `series.resource_id` | which authorized resource it came from, which is where the value is derived from |
| **not identity** — nothing extra needed | `observation_key` is inherited verbatim from the RawRecord and **already contains the resource id**, so `.../1gram/...climate` and `.../2gram/...climate` are already distinct |

## 4. `COUNT` → the value

**Source semantics.** *"The number of times the word/phrase was mentioned in
articles of that language published in that given 15 minute interval"* — GDELT's
own words, and a non-negative integer.

**Canonical destination.** `CanonicalValue`. **This one fits exactly.**

| Requirement | `CanonicalValue` |
|---|---|
| exact, arbitrary precision | `Decimal`, serialised as a decimal string |
| never a float | already the rule (§6.1), for the fingerprint's sake |
| zero is a measurement | `value_state` exists precisely for this |
| not a score | it is a value with a state, not a rank |

**No model change is required for `COUNT`.** The 2⁵³-exceeding count in the
Mission 1.9.3 fixtures survives unchanged.

### 4.1 The unit — §8

`unit_state` must be `PUBLISHED`, `NOT_PUBLISHED` or `UNKNOWN`.

**The answer is `NOT_PUBLISHED`**, with `unit = null`.

The file has four columns and none of them is a unit. `NOT_PUBLISHED` means
exactly *"the authorized access path does not carry a unit for this
observation"*, which is true and checkable.

**"mentions" was considered and rejected.** GDELT describes the count in prose;
it does not publish a unit field, so recording `PUBLISHED: "mentions"` would
assert the source did something it did not. §8 is explicit that an SI-like unit
must not be invented to satisfy a required field.

**The record kind carries what a unit would have carried.**
`lexical_frequency_observation` already says the number is an occurrence count
over a stated window. A unit string would restate that less reliably.

`UNKNOWN` was also rejected: it is reserved for a source that *may* publish a
unit and did not for this observation. GDELT publishes none for any WEB-NGRAM
row, which is a settled fact about the access path rather than a gap in one
record — and the contract keeps those two distinguishable on purpose.

## 5. Summary

| Field | Destination | Exact today? | Change required |
|---|---|---|---|
| `DATE` | `CanonicalPeriod`, type `INTERVAL` | **no** — cannot say the zone is unknown | **`timezone_state`**, and `observed_at` becomes conditional |
| `LANG` | — | **no** — nothing canonical exists | **`CanonicalLanguage`** + a mapping-state enum |
| `NGRAM` | — | **no** — no kind can hold it | **a new record kind** |
| `COUNT` | `CanonicalValue` | **yes** | none |

**Three changes, and each is the smallest that removes an invention.** Nothing
here loosens a rule the existing model enforces, and every World Bank payload is
byte-identical afterwards.

## 6. Two things this analysis deliberately does not do

**It does not close H-29 or H-30.** Both stay open, and the model changes exist
so that a record can *say* they are open rather than paper over them. When either
is answered, the fix is a normalizer version bump over records already held —
not a re-collection.

**It does not register an adapter.** `RECORD_KINDS` gains the declaration and the
registry gains the vocabulary row, because the model is what this mission is
about and the validator requires the two to agree. `NORMALIZER_REGISTRY` and
`IMPLEMENTED_NORMALIZERS` gain **nothing** — those say *code exists that can
normalize this*, and none does.

### 6.1 An inconsistency worth recording

Migration 0009's comment reads:

> A registry ROW, not a CHECK list: Ontology V2 §14.3 makes evolving taxonomies
> rows precisely so a new adapter does not need a migration.

In practice a new kind **does** need one: `normalized_records.record_kind_id` has
a foreign key to `registry.registry_entries`, and `validate_normalization.py`
asserts that the kinds declared in `RECORD_KINDS` are exactly those the migration
inserts. Both rules are good and together they make the comment's claim false.

Recorded rather than fixed: 0009 is history and the row it inserted is correct.
Migration 0011 states the rule as it actually is.
