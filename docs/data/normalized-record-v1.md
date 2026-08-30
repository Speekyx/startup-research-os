# NormalizedRecord V1

**Status:** Authoritative. Created in Mission 1.6, the first mission that
normalizes anything.
**Version:** canonical normalized schema **1**
**Date:** 2026-08-30
**Governs:** what a canonical source observation is, how it is identified, what
lineage it carries, and what may and may not be inferred while producing one.
**Related:** [`normalized-record-gap-analysis-v1.md`](normalized-record-gap-analysis-v1.md),
[`world-bank-normalizer-v1.md`](world-bank-normalizer-v1.md),
[`raw-record-gap-analysis-v1.md`](raw-record-gap-analysis-v1.md),
[`world-bank-collector-v1.md`](world-bank-collector-v1.md),
[`data-principles.md`](data-principles.md),
[`data-retention-policy-v1.md`](data-retention-policy-v1.md).

---

## 1. What a NormalizedRecord is

**One canonical source observation**, prepared for downstream processing and
still traceable to the RawRecord it came from.

It answers one question:

> What does this source observation structurally represent?

It does **not** answer:

> Is this a market opportunity?

That boundary is the whole point of the layer, and it is not a matter of taste.
The pipeline separates five things, and a value that crosses the line early can
never be un-crossed:

```text
COLLECTION          gets source-native data
NORMALIZATION       maps source-native structure to canonical structure   <- here
SIGNAL EXTRACTION   interprets meaning
CLAIM EXTRACTION    creates assertions
SCORING             evaluates evidence
```

A normalized field that encoded "this indicates growing demand" would put an
interpretation in a place that looks like a fact, and every stage downstream
would inherit it as one. Normalization renames and reshapes. It does not decide.

---

## 2. The three identities

The same discipline the raw layer uses (`world-bank-collector-v1.md` §7), one
level up. Confusing any two of these is the defect this section exists to
prevent.

| | Question | Value |
|---|---|---|
| **source observation identity** | WHICH observation | `observation_key` — inherited **verbatim** from the RawRecord. Stable across revisions and across normalizer versions |
| **raw version identity** | WHAT the source said, and when | `raw_record_id`. A revision is a different raw record, so it is a different value here |
| **normalized representation identity** | WHICH transformation of that | `(workspace_id, raw_record_id, normalization_schema_version, normalizer_id, normalizer_version)`, and the row `id` derived from it |

The row id is `uuid5` over the workspace and that tuple, so a re-run converges on
the row that exists instead of inserting a parallel copy — the same argument the
registry and the collector both make for deterministic ids.

**The normalization timestamp is in none of them** (§22). Including it would make
every re-normalization a new representation, which is how an idempotent stage
becomes one that grows a table forever. It is the identical trap the raw layer
avoided by keeping the retrieval time out of `content_hash`.

### The unique constraint, and the three requirements it satisfies at once

```sql
UNIQUE (workspace_id, raw_record_id,
        normalization_schema_version, normalizer_id, normalizer_version)
```

| Case | Result | Requirement |
|---|---|---|
| same raw record, same versions | collides → the row is updated in place | idempotency (§23) |
| same raw record, different normalizer or schema version | no collision → a second row | re-normalization (§24, §49) |
| revised raw record (new `raw_record_id`), same versions | no collision → a second row | revision (§7, §48) |

A constraint over the *observation* instead would have rejected every one of the
inserts that record a revision or a re-normalization. That is the trap
`raw-record-gap-analysis-v1.md` §3 documented at the raw layer, and it is worth
restating because it is not obvious from either end.

---

## 3. The content fingerprint

`content_hash` is `sha256` over the canonical JSON of the semantic payload:
sorted keys, no incidental whitespace.

**In it:** the record kind, the metric, the period, the geography, the value and
its state, the unit and its state — everything that *is* the observation.

**Not in it** (§22): the normalization timestamp, the correlation id, the job id,
the schema version, the normalizer version, the raw record id.

Leaving the versions out looked wrong and is right. If normalizer 1.0 and 1.1
produce byte-identical canonical content, their fingerprints *should* match,
because the content is the same — and that is exactly the question an operator
asks after an upgrade: *did this change anything?* Folding the version into the
hash would answer "yes" every time, which is the same as not answering.

Identity (§2) is what distinguishes the two rows. Content is what the hash
describes. They are different questions and they get different columns.

---

## 4. Record kinds — a registry, not an enum

`record_kind` is an **extensible registry** reference
(`registry.registry_entries`, registry `normalization_record_kind`), following
Ontology V2 §14.3 and the pattern `nlp.signals.signal_type_id` already uses.

**Two entries exist.**

| id | Meaning |
|---|---|
| `numeric_observation` | One measured or reported numeric value for one metric, one geography and one period |
| `lexical_frequency_observation` | One occurrence count the source measured for one lexical term, in one language, over one period. **No geography** |

The second arrived in Mission 1.10 and is the first real use of this registry.
A GDELT WEB-NGRAM row has no geography and its term is not a metric, so
`numeric_observation` could not hold it — and **widening that kind to fit would
have let a World Bank record exist with no geography**, which is the existing
model getting worse for a new source's sake.

The kind was added and **no adapter was**. A registry row is a *vocabulary*
entry: it lets the model describe a shape, and it lets the database refuse a row
naming a kind nobody registered. The claim that code exists is
`NORMALIZER_REGISTRY`, and for GDELT it is still empty.

Adding a kind is: insert the registry row, declare its canonical payload model
in `RECORD_KINDS`, and write the adapter that produces it.

**The row does need a migration**, and the original text here said it did not.
Two rules make it necessary and both are worth keeping:
`normalized_records.record_kind_id` has a foreign key to
`registry.registry_entries`, so a kind the registry does not know cannot be
persisted; and `validate_normalization.py` asserts that the kinds declared in
`RECORD_KINDS` are exactly those a migration inserts, so the two copies cannot
drift. What the registry buys is that **no table is altered** — migration 0011 is
one `INSERT`.

**No hypothetical kinds are declared.** §11 names ten shapes future sources might
have — documents, discussion posts, reviews, repositories, events. None is
created, and none will be until a source produces one.

Mission 1.10 sharpened what that rule is about. Its original form said a registry
entry with no adapter behind it is a promise the code does not keep — by analogy
with `IMPLEMENTED_COLLECTORS`, which gains a name as the *last* step of building a
collector. **The analogy holds for adapters and not for vocabulary.**

    a kind exists because DATA exists       -- two real GDELT records
    an adapter exists because CODE exists   -- NORMALIZER_REGISTRY says which

`lexical_frequency_observation` is not hypothetical: a real source publishes that
shape and two real RawRecords hold it. What would be a promise the code does not
keep is registering an *adapter*, and Mission 1.10 registered none.

Each kind declares which canonical fields are **required** and which are
**optional**. That declaration is what the quality state (§8) is computed
against, so "required" is a property of the kind rather than a judgment made per
record.

---

## 5. The canonical shapes

The payload for `record_kind = numeric_observation`.

```json
{
  "record_kind": "numeric_observation",
  "metric": {
    "id": "SP.POP.TOTL",
    "name": null,
    "scheme": "world-bank-indicator"
  },
  "observation": {
    "value": "67158348",
    "value_state": "REPORTED",
    "unit": null,
    "unit_state": "NOT_PUBLISHED",
    "decimals": 0
  },
  "period": {
    "type": "YEAR",
    "label": "2018",
    "start": "2018-01-01T00:00:00+00:00",
    "end": "2019-01-01T00:00:00+00:00",
    "end_inclusive": false
  },
  "geography": {
    "source_code": "FRA",
    "source_name": "France",
    "kind": "COUNTRY",
    "canonical_code": "FR",
    "canonical_scheme": "ISO-3166-1-ALPHA-2"
  },
  "series": {
    "dataset": "indicators",
    "resource_id": "indicator/SP.POP.TOTL",
    "frequency": "ANNUAL",
    "source_last_updated": "2025-01-28"
  }
}
```

Every field is either present in the source response or derived from it by an
explicit, reviewed rule. **Nothing is defaulted from an indicator name, and
nothing is fetched** (§17, §18, §41).

`metric.name` is `null` for the World Bank adapter because the Indicators API
response carries no indicator label — an absence, faithfully recorded, not a gap
to fill from recall.

### 5.1 The LexicalFrequencyObservation canonical shape

The payload for `record_kind = lexical_frequency_observation`, added in Mission
1.10. Full derivation in
[`gdelt-normalization-contract-v1.md`](gdelt-normalization-contract-v1.md).

```json
{
  "record_kind": "lexical_frequency_observation",
  "term": {"text": "climate", "gram_size": 1, "scheme": "gdelt-web-ngram"},
  "language": {
    "source_label": "ENGLISH",
    "source_scheme": "cld2-language-name",
    "mapping_state": "NOT_ESTABLISHED",
    "canonical_tag": null,
    "canonical_scheme": null
  },
  "observation": {"value": "55", "value_state": "REPORTED",
                  "unit": null, "unit_state": "NOT_PUBLISHED", "decimals": null},
  "period": {"type": "INTERVAL", "label": "20260830091500",
             "start": "2026-08-30T09:15:00", "end": "2026-08-30T09:30:00",
             "end_inclusive": false, "timezone_state": "NOT_ESTABLISHED"},
  "series": {"dataset": "web-ngrams", "resource_id": "web-ngrams/1gram",
             "source_last_updated": null}
}
```

Four things about it are decisions rather than mechanics:

- **There is no `geography` key.** Absent, not null — a null would invite a
  reader to think one was looked for and not found. A row stating a language says
  nothing about where anything happened.
- **The term is not a metric.** A metric is a *definition* reused across
  geographies and periods; a term is an observed item, and the thing measured is
  how often it appeared.
- **`gram_size` comes from the resource id**, never from counting spaces in the
  term: a two-word entry in a unigram file is a contract violation, and counting
  would hide it.
- **The count carries no unit.** `NOT_PUBLISHED`, because the source publishes
  four columns and none is a unit — and the record kind already says the number
  is an occurrence count over a window.

---

## 6. Numeric semantics

### 6.1 The value is an exact decimal string

`observation.value` is a **string** holding the decimal exactly as the source
expressed it, or `null`. It is never a JSON float.

Three reasons, and the third is the one that settles it:

1. **No binary rounding** (§13). A value parsed into an IEEE-754 double and
   re-serialized can differ from what the source sent. For population counts it
   would not; for a rate, a ratio or a price it would, and the canonical layer
   must not have a rule that is right for some indicators and wrong for others.
2. **A stable fingerprint.** JSON float formatting is a property of whichever
   library serializes it. A content hash that depended on that would report
   revisions nobody made.
3. **No loss of query ability.** `JSONB` keeps the string, and
   `(payload -> 'observation' ->> 'value')::numeric` casts it to PostgreSQL
   `NUMERIC` — arbitrary precision, exact. Nothing is given up by not storing a
   number, which is why no separate numeric column exists.

In Python the value is a `decimal.Decimal` throughout. It is parsed from the raw
payload's **JSON text** with `parse_float=Decimal`, never from an already-parsed
float — parsing twice would bake in the rounding this section exists to avoid.

### 6.2 Missing is not zero

`value_state` is an explicit field, and this is not a formality (§14):

| `value_state` | Meaning |
|---|---|
| `REPORTED` | The source published a figure. `value` holds it |
| `NOT_REPORTED` | The source published no figure for this metric, geography and period. `value` is `null` |
| `UNREADABLE` | The source published something that could not be read as a decimal. `value` is `null`, and the quality state records it |

**Zero is a real measurement.** A source saying "0" and a source saying nothing
are different statements about the world, and a layer that mapped both to `0`
would make them permanently indistinguishable — no downstream stage could
recover the difference, because the information would be gone.

`NOT_REPORTED` is the ordinary case for an indicator series with sparse coverage,
not a failure.

### 6.3 Units are not inferred

`unit_state` is `PUBLISHED`, `NOT_PUBLISHED` or `UNKNOWN`. When the source
publishes no unit, `unit` is `null` and the state says why (§17).

Deriving "US$" from an indicator id that ends in `.CD` would be a guess dressed
as a fact, and the first indicator whose naming convention differs would make it
silently wrong. Future metadata enrichment can resolve units from an authorized
metadata resource; until then `NOT_PUBLISHED` is the correct answer.

---

## 7. Period, geography and time

### 7.1 Period

`PeriodType` is a closed enum: `YEAR`, `QUARTER`, `MONTH`, `DAY`, `INSTANT`,
`INTERVAL`. The canonical model can represent all six (§16). **An adapter
supports only the forms its real records use**, and reports anything else rather
than approximating it.

A period is a half-open interval plus a label:

```json
{"type": "YEAR", "label": "2018",
 "start": "2018-01-01T00:00:00+00:00", "end": "2019-01-01T00:00:00+00:00",
 "end_inclusive": false}
```

`observed_at` on the row is `start`, which is what the column has meant since
Mission 0.1 and what the raw layer already stores. **`type` and `label` sit
beside it precisely so nothing can read January 1 as an exact event time**
(§16) — the interval says the observation covers a year, and the label preserves
what the source actually wrote.

#### The timezone can be unestablished (Mission 1.10)

A source can publish a period label and no offset. GDELT's WEB-NGRAM `DATE` is a
15-minute bucket stamp and nothing in its documentation states a zone (**H-29**),
so every route into a period would have had to choose one.

`timezone_state` says which situation a period is in, and the two carry different
kinds of bound:

| State | Bounds | `observed_at` |
|---|---|---|
| `ESTABLISHED` | timezone-**aware** — the rule since Mission 1.6, unchanged and still enforced | the period start |
| `NOT_ESTABLISHED` | timezone-**naive** — a wall-clock reading, which is what Python's naive `datetime` means and what iCalendar calls floating time | **`NULL`** |

A naive datetime cannot enter a `TIMESTAMPTZ`, and an aware one would carry an
offset the source never published. Leaving `observed_at` empty is how the field
is not abused.

**`timezone_state` is serialised only when it is not `ESTABLISHED`.** The payload
is inside the content fingerprint, so an unconditional key would have changed the
hash of every record ever written — for a fact those records already state, since
an ISO-8601 string discloses its own offset or its absence. **A consumer reading
the key should default it to `ESTABLISHED`.**

Nothing here weakens period semantics: aware bounds are still required wherever a
zone is established, which is every record written to date. See
[ADR-019](../architecture/adr/ADR-019-lexical-frequency-observation.md) for the
alternatives and why each was rejected.

### 7.2 Geography

Four fields, and the split is the point (§15):

| Field | Meaning |
|---|---|
| `source_code` | Verbatim from the source. Always present, never rewritten |
| `source_name` | Verbatim from the source, where it gave one |
| `kind` | `COUNTRY`, `AGGREGATE` or `UNKNOWN` |
| `canonical_code` | ISO 3166-1 alpha-2, **only** where an entry in the reviewed geography map establishes it |

Classification comes from
[`geography-mapping-v1.json`](geography-mapping-v1.json) — a reviewed file where
every entry carries a `basis`, exactly like the authorized dataset list. A code
with no entry is `UNKNOWN`: no canonical code, and the quality state says so.

Three rules, none negotiable:

- **An unclassified code never becomes a country.** `UNKNOWN` is the failure
  mode, and it is a safe one.
- **An aggregate is preserved as an aggregate.** `World` and `High income` are
  real entities and are recorded as `AGGREGATE` with their source code — never
  mapped to a country, and never dropped.
- **A name is not evidence.** Classifying a code because its label reads like a
  country would be inference, and §41 forbids reaching for a model to do it. The
  map is the only authority.

### 7.3 Language

Five fields, and the split is the same one geography makes (Mission 1.10 §5):

| Field | Meaning |
|---|---|
| `source_label` | Verbatim from the source. Always present, never rewritten |
| `source_scheme` | Which vocabulary the label is from — `cld2-language-name`, not the same as ISO 639's English names |
| `mapping_state` | `ESTABLISHED` or `NOT_ESTABLISHED` |
| `canonical_tag` | A language tag, **only** where a reviewed mapping establishes it |
| `canonical_scheme` | `BCP-47`, where a tag exists |

Three rules, none negotiable:

- **A language is never a geography.** Spanish is not Spain and Arabic is not one
  country. The registry model already keeps countries and languages apart, and
  this is the same separation at the canonical layer.
- **Resemblance is not a mapping.** `ENGLISH` looks like `en`; the first CLD2
  name that does not resemble its tag would be silently wrong with nothing to
  catch it. `CanonicalLanguage.unmapped()` is the counterpart of
  `CanonicalGeography.unclassified`, reached for the same reason.
- **The absence stays visible.** `mapping_state` is what makes an unmapped label
  readable rather than inferable, and the constructor refuses a tag without a
  mapping and a mapping without a tag.

**`content_language` on the row stays `NULL`** where no tag is established. That
column's contract means a code, and a name in it would be a guess wearing the
clothes of a fact.

### 7.4 The three timestamps

| Column | Fact |
|---|---|
| `observed_at` | when the source observation happened — the period start, or **`NULL`** when the period's timezone is unestablished (§7.1) |
| `collected_at` | when it was collected — inherited verbatim from the RawRecord |
| `normalized_at` | when this representation was produced |

Three columns because they answer three of §8's questions, and because
`data-principles.md` §9 is explicit that ingestion time must never stand in for
event time: trend analysis computed on ingestion timestamps produces artifacts
that look exactly like real market movements.

---

## 8. Quality — structural, never epistemic

`NormalizationQuality` is a closed enum with three values, and it describes the
**structure** of the record, not how much anyone should believe it.

| State | Meaning |
|---|---|
| `VALID` | Every field the record kind declares required is present and well-formed |
| `PARTIAL` | Required fields are present; something the source supplied could not be fully represented, or something a consumer would expect is absent |
| `INVALID` | A required canonical field is missing or cannot be safely represented. The record is kept for audit and must not be read as an observation |

**It is not a confidence score** (§25). Reliability and confidence are epistemic
judgments that belong to the evidence model, are numbers on `[0,1]`, and mean
something entirely different. Putting one here would invite a downstream stage to
multiply a parsing outcome by an evidence weight.

Reasons are recorded for anything below `VALID` (§26), from a closed vocabulary:

| Reason | State |
|---|---|
| `VALUE_NOT_REPORTED` | `PARTIAL` |
| `MALFORMED_NUMERIC_VALUE` | `PARTIAL` |
| `GEOGRAPHY_NOT_CLASSIFIED` | `PARTIAL` |
| `GEOGRAPHY_MISSING` | `INVALID` |
| `METRIC_MISSING` | `INVALID` |
| `PERIOD_NOT_SUPPORTED` | `INVALID` |

### Two decisions worth stating, because both could reasonably have gone the other way

**A value the source did not report makes the record `PARTIAL`, not `VALID`.**
The record is a well-formed statement, but it carries no measurement, and a
downstream stage filtering on `VALID` would otherwise pick up rows with nothing
in them. §25's own wording for `PARTIAL` — *"remains useful but source
information is missing"* — describes this exactly. `PARTIAL` here means *the
source reported no figure*, never *we failed to read it*; that case is
`MALFORMED_NUMERIC_VALUE`, and the two are separate reasons so they never get
confused.

**A unit the source does not publish is not a quality reason at all.** The
Indicators API publishes no unit on this endpoint, so treating its absence as a
degradation would mark every World Bank record `PARTIAL` — and a state that every
record shares carries no information. `unit_state = NOT_PUBLISHED` records the
fact where it belongs, in the payload, and the quality state stays able to
distinguish something.

**An `INVALID` record is stored, not discarded** (§26, §27). A raw record that
cannot be normalized is a fact about the pipeline that someone has to be able to
find. Dropping it would make a normalizer bug look like a source that returned
nothing.

---

## 9. Lineage

Every NormalizedRecord answers §8's nine questions without reading a URL, and
without joining to anything that might have expired.

Promoted to columns, because an auditor filters **by** them:

`observation_key`, `raw_record_id`, `source_id`, `collector_id`,
`collector_version`, `normalizer_id`, `normalizer_version`,
`normalization_schema_id`, `normalization_schema_version`, `review_version`,
`correlation_id`, `observed_at`, `collected_at`, `normalized_at`.

In `provenance` JSONB, because it is read **with** a record and differs per
source: the access profile and method, the approval state, the resource and
dataset family, the licence and its basis, the content origin, the **rendered
attribution**, the **condition snapshot** at collection time, the raw content
hash, and the raw record's own expiry.

### Why lineage is copied rather than joined

A raw record is retained for **30 days**; a normalized record for **12 months**
(`data-retention-policy-v1.md` §2.1, §2.2). From day 31 a join to `raw_records`
returns nothing.

§4 of that policy legislates for exactly this: *"provenance survives the content
it describes. When a `raw_record` expires, its metadata — source id, timestamp,
hash, method — is retained on the derived records."* Copying is not
denormalization for speed; it is the mechanism the retention policy requires.

`raw_record_id` is still a real foreign key with `ON DELETE CASCADE`. When the
raw record is deleted the normalized record goes with it — which is the *deletion*
path (§5 of the policy), a different thing from expiry, and the two must not be
confused. Lifecycle jobs are still unimplemented, and this document does not
pretend otherwise.

---

## 10. Attribution survives, and cannot be dropped

An attribution obligation on a RawRecord is on the NormalizedRecord. There is no
route by which it is not (§9, §46).

Enforced by construction rather than by review:

- the builder has **no attribution parameter**, so a normalizer has nothing to
  pass and nothing to omit — the same move `build_draft` made for the raw layer;
- the notice is read from the raw record's own `provenance.attribution`, which
  the Mission 1.4 capability rendered at collection time from the obligation the
  review recorded;
- a raw record carrying **no** attribution is refused with `INVALID_RAW_RECORD`
  rather than normalized into a row with no credit attached. Failing closed, like
  the rendering it inherits from.

A structural test asserts the signature, so the guarantee is observed rather than
architectural.

---

## 11. Retention

`expires_at = normalized_at + retention.normalized_days`, where the window comes
from `resolve_retention` — the same governance resolver Mission 1.0 built, which
already takes the stricter of the project baseline and any source override, in
that direction only.

**The RawRecord's `expires_at` is not copied** (§10). The two tiers have
different authoritative baselines — 30 days and 12 months
(`data-retention-policy-v1.md` §2.1, §2.2) — and copying the raw expiry would
delete normalized observations eleven months early, silently, for a reason no
policy states.

**A source override shortens, never lengthens.** `resolve_retention` is `min()`
against the baseline: a source permitting longer retention does not get it,
because §3 of the policy requires necessity to be established and recorded, which
is a reviewed decision rather than an arithmetic one. The builder has **no
retention parameter**, so a normalizer cannot ask for more even if it wanted to.

The resolved basis — which number applied and where it came from — is recorded in
`provenance.retention`, so the decision stays auditable after the policy changes.

---

## 12. Tenancy

Three layers, and each exists because the previous one can be forgotten.

1. **The explicit `workspace_id` filter** in every repository query. ADR-012
   layer one. Not removed because RLS exists.
2. **PostgreSQL row-level security**, entered through a transaction-local tenant
   context. ADR-012 layer two. A missing context returns no rows rather than
   wrong ones.
3. **Composite foreign keys carrying `workspace_id`** (§31). A NormalizedRecord
   in workspace A referencing a RawRecord in workspace B is not rejected at
   runtime — it cannot be written.

`workspace_id` is never inferred, never defaulted and never reconstructed from
another field, in a normalization job exactly as in a collection job (ADR-005).

---

## 13. What a normalizer may not do

| Forbidden | Why |
|---|---|
| open a network connection | §18, §40. Everything needed is already persisted. CI asserts it mechanically |
| call an LLM | §41. Normalization is deterministic and reproducible; a model deciding a geography would make it neither |
| tokenize, embed, classify or cluster | §42. D-12 is open |
| create a Signal | §43 |
| create or update a Claim, or Evidence | §44 |
| compute any score | §45. No `CALIBRATED` profile exists |
| modify a RawRecord | §27. The raw layer records what the source returned; a correction that made normalization pass would destroy the evidence that it did not |
| choose its own retention or attribution | §10, §9. Neither has a parameter |
| run against a source it was not selected for | §20. Selection is `(source_id, collector_id)` and fails closed |

The first three are enforced in CI by `validate_normalization.py` rather than by
review, because a rule that depends on a reviewer noticing is a rule with a
half-life.

---

## 14. Versioning

Two versions, deliberately independent (§21).

| | Changes when | Effect |
|---|---|---|
| `normalization_schema_version` | the canonical representation's **meaning** changes — a field added, a semantic redefined | Old records keep their version and keep meaning what they meant |
| `normalizer_version` | the **implementation** changes — a parsing fix, a new source form handled | Same schema, possibly different output |

Both are on every row. Neither is in the content fingerprint (§3).

A record written under schema 1 is never reinterpreted under schema 2. Re-running
a newer normalizer produces an **additional** row; the older one is not modified
and not deleted (§24, §49).

**Which version downstream should read is not decided here.** That is **D-08**,
open, and §49 forbids resolving it. What this schema guarantees is that the
question remains answerable — every representation is identifiable, versioned and
intact — so whoever resolves D-08 has something to choose between.

---

## 15. Batch bounds

A normalization job processes at most **500** raw records, configurable
downwards, defaulted rather than left to the caller.

This is **our own** operational bound, and the distinction matters as much as it
did for request pacing (`world-bank-collector-v1.md` §5): it is not derived from
any external limit, it protects a worker slot and a transaction from a job
nobody sized, and "the operator will pass a limit" is not a bound — the default
is.

---

## 16. Still open

- **Re-normalization selection (D-08).** Coexistence works; choosing does not
  exist. §49 is explicit that Mission 1.6 must not invent it.
- **Two record kinds, and one adapter.** `numeric_observation` has one;
  `lexical_frequency_observation` has none, because Mission 1.10 defined the
  model and stopped there. Document and discussion kinds arrive with the adapters
  that produce them.
- **H-29 — the GDELT bucket timezone is unestablished**, so those periods will be
  `NOT_ESTABLISHED` and their `observed_at` `NULL`. Answering it is a normalizer
  version bump over records already held, not a re-collection.
- **H-30 — no CLD2-to-language-tag mapping is established**, so those records
  will carry a source label and no canonical tag. Same shape of fix.
- **The geography map holds two entries.** Widening it requires evidence per
  entry, the same discipline as the authorized dataset list.
- **Retention lifecycle jobs are still unimplemented** (`data-retention-policy-v1.md`
  §6). `expires_at` is written correctly and nothing yet acts on it.
- **Object storage (D-10).** Canonical payloads are inline because they are a few
  hundred bytes.
- **No language detection, and none is planned.** `content_language` is `NULL`
  for numeric observations, which is correct rather than deferred. Mission 1.10
  added `CanonicalLanguage` for a source that **states** its language; detecting
  one from text is a different act and remains undecided.
