# GDELT WEB-NGRAM Normalization Contract V1

**Status:** **Specified, not implemented.** The canonical model can represent a
WEB-NGRAM observation; no normalizer exists and no GDELT record has been
normalized.
**Date:** 2026-08-30 (Mission 1.10)
**Related:** [`gdelt-normalized-record-gap-analysis-v1.md`](gdelt-normalized-record-gap-analysis-v1.md)
(the working that produced this),
[`normalized-record-v1.md`](normalized-record-v1.md),
[`gdelt-web-ngram-raw-record-v1.md`](gdelt-web-ngram-raw-record-v1.md),
[ADR-019](../architecture/adr/ADR-019-lexical-frequency-observation.md).

---

## 0. What a normalizer would have to produce

This document is the contract the Mission 1.10.1 adapter is written against.
Everything in it is decided; nothing in it is code.

## 1. The payload

`record_kind = lexical_frequency_observation`

```json
{
  "record_kind": "lexical_frequency_observation",
  "term": {
    "text": "climate",
    "gram_size": 1,
    "scheme": "gdelt-web-ngram"
  },
  "language": {
    "source_label": "ENGLISH",
    "source_scheme": "cld2-language-name",
    "mapping_state": "NOT_ESTABLISHED",
    "canonical_tag": null,
    "canonical_scheme": null
  },
  "observation": {
    "value": "55",
    "value_state": "REPORTED",
    "unit": null,
    "unit_state": "NOT_PUBLISHED",
    "decimals": null
  },
  "period": {
    "type": "INTERVAL",
    "label": "20260830091500",
    "start": "2026-08-30T09:15:00",
    "end": "2026-08-30T09:30:00",
    "end_inclusive": false,
    "timezone_state": "NOT_ESTABLISHED"
  },
  "series": {
    "dataset": "web-ngrams",
    "resource_id": "web-ngrams/1gram",
    "source_last_updated": null
  }
}
```

**There is no `geography` key.** Absent, not null: a null would invite a reader
to think one was looked for and not found. A WEB-NGRAM row states a language, and
a language is not a place.

## 2. Field by field

### 2.1 `term`

| Key | From | Rule |
|---|---|---|
| `text` | `NGRAM`, verbatim | strict UTF-8, never normalised, never classified |
| `gram_size` | the **resource id** | `web-ngrams/1gram` → 1. **Never from counting spaces** |
| `scheme` | fixed | `gdelt-web-ngram` — which vocabulary the term is from |

A term is not a theme, an entity, a topic or a keyword intent. Nothing classified
it and the normalizer must not.

**`gram_size` comes from the resource** because a two-word entry in a unigram file
would be a contract violation; inferring from the text would hide it where the
resource surfaces it.

### 2.2 `language`

`CanonicalLanguage.unmapped("ENGLISH", "cld2-language-name")`.

**H-30 is open**, so `mapping_state` is `NOT_ESTABLISHED` and `canonical_tag` is
`null` for every record. The label is preserved verbatim.

`content_language` on the **row** stays `NULL`. That column's contract means a
code; a name in it would be a guess wearing the clothes of a fact.

**If H-30 is answered later**, the fix is a normalizer version bump that
re-derives from records already held. No re-collection.

### 2.3 `period`

| Key | Value |
|---|---|
| `type` | `INTERVAL` — the contract already means "an arbitrary interval the source stated explicitly" |
| `label` | the source bucket stamp, verbatim |
| `start` / `end` | **naive** wall-clock bounds, 15 minutes apart |
| `timezone_state` | `NOT_ESTABLISHED` |

**H-29 is open.** `observed_at` on the row is therefore `NULL`: a naive datetime
cannot enter a `TIMESTAMPTZ` and an aware one would carry an offset GDELT never
published.

### 2.4 `observation`

`CanonicalValue` with `value = Decimal(COUNT)`, `state = REPORTED`.

- **`unit_state = NOT_PUBLISHED`, `unit = null`.** The file has four columns and
  none is a unit. `"mentions"` would assert the source did something it did not,
  and the record kind already says the number is an occurrence count over a
  window.
- **`decimals = null`.** GDELT publishes no decimal metadata; World Bank's comes
  from a field its API sends.
- **Zero is `REPORTED`, never `NOT_REPORTED`.** A zero-count row is the source
  saying "none in this bucket", which is a measurement.
- **Never a float.** Arbitrary-precision integers, stored as decimal strings.

### 2.5 `series`

`dataset` and `resource_id` from the RawRecord's provenance.
`source_last_updated` is `null` — GDELT publishes no revision stamp for a bucket
file.

## 3. Quality

The kind declares:

```text
required   term.text, term.gram_size, language.source_label, period,
           observation.value_state
optional   language.canonical_tag, observation.value, observation.unit,
           series.resource_id, series.source_last_updated
```

**Every GDELT record will be `PARTIAL`, and deliberately so.** Two things a
consumer would reasonably expect are absent, and both have a reason code:

| Reason | Why |
|---|---|
| `PERIOD_TIMEZONE_NOT_ESTABLISHED` | H-29 |
| `LANGUAGE_NOT_MAPPED` | H-30 |

`PARTIAL` means *usable, and something a consumer would expect is absent* —
exactly the situation. Marking these `VALID` would say nothing is missing when
two known things are; marking them `INVALID` would make them unreadable for a
condition that is universal and expected.

**Neither is an error.** The source published what it published; this system has
not established the rest.

## 4. Identity

**Unchanged, and it already works.**

```text
observation_key  gdelt|web-ngrams/1gram|20260830091500|ENGLISH|climate
                 inherited VERBATIM from the RawRecord

row identity     (workspace_id, raw_record_id, schema_version,
                  normalizer_id, normalizer_version)

content_hash     over the payload, which includes COUNT
```

**`COUNT` is content, not identity** (§9). GDELT correcting a count produces a
new RawRecord with the same `observation_key`, whose normalization supersedes the
previous row **within the same lineage** and leaves it readable. That is the
Mission 1.6 mechanism working unchanged, and it is why no model change was needed
for identity.

**The gram kind is already in the identity**, because the resource id is in the
inherited key. `.../1gram/...climate` and `.../2gram/...climate` are two
observations, not a collision — no extra field required.

## 5. The normalizer, when it is written

```text
normalizer_id       gdelt-web-ngram-lexical
normalizer_version  1.0.0
source_id           gdelt
collector_id        gdelt-web-ngram
supported_collector_versions  {"1.0.0"}
schema              sros.normalized-record / 1
```

The id follows the World Bank convention
(`world-bank-indicators-numeric` = collector family + payload kind).

**`supported_collector_versions` is not decoration**: a collector version this
adapter has never seen may have changed the payload shape, and a parse that
half-works on an unknown shape is worse than one that stops.

### 5.1 What would require a version bump

A **version bump**, because the canonical output changes and existing rows must
stay readable as what they were:

- answering **H-29** and emitting `ESTABLISHED` periods with a real zone;
- answering **H-30** and emitting a `canonical_tag`;
- any change to the payload shape, a field's meaning, or the fingerprint;
- a change to `gram_size` derivation, or to how the term is preserved.

**Not** a version bump: a reworded message, a refactor, a new test, a
performance change. The rule is `normalized-record-v1.md` §14's — the version
tracks what a record *means*, not how it was produced.

### 5.2 Historical coexistence — D-08

**Unchanged and not decided here.** A `1.1.0` normalizer emitting established
timezones would write **additional** rows; the `1.0.0` rows stay, unsuperseded,
because superseding across lineages would be the selection policy D-08 forbids
inventing.

So after H-29 is answered a single observation may have two normalized rows —
one saying the zone was unestablished, one saying what it is. **Which a consumer
should read is D-08**, still open, and this contract deliberately does not answer
it.

## 6. What the normalizer may not do

- assume a timezone, or map a language name to a tag;
- write a geography key, of any value;
- classify the term as a theme, entity or topic;
- treat the count as a signal, score, rank or trend;
- pass the count through a float;
- choose its own retention or compose its own attribution — `build_normalized`
  has no parameter for either;
- call a model, an embedder or a classifier.

## 7. What exists today

| | |
|---|---|
| the record kind | **declared** in `RECORD_KINDS` and **registered** by migration 0011 |
| the payload class | `LexicalFrequencyObservation` |
| `CanonicalLanguage`, `timezone_state` | in the model, with tests |
| the adapter | **none** |
| `NORMALIZER_REGISTRY` for gdelt | **empty** |
| `IMPLEMENTED_NORMALIZERS` | `{world-bank}` |
| GDELT normalized records | **0** |

The registry row is a **vocabulary** entry — it lets the model describe the
shape, and the database refuse a row naming a kind nobody registered. It is not a
claim that code exists; that claim is `NORMALIZER_REGISTRY`, and it is still
empty.
