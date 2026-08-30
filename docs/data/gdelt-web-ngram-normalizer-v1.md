# GDELT WEB-NGRAM Normalizer V1

**Status:** **Implemented.** `gdelt-web-ngram-lexical@1.0.0`, the second adapter,
and the first that produces a canonical shape other than a numeric observation.
Two real records normalized.
**Date:** 2026-08-30 (Mission 1.10.1)
**Code:** `sros_acquisition.normalization.gdelt_web_ngram`
**Related:** [`world-bank-normalizer-v1.md`](world-bank-normalizer-v1.md) (the
reference adapter), [`gdelt-normalization-contract-v1.md`](gdelt-normalization-contract-v1.md)
(the contract this implements), [`normalized-record-v1.md`](normalized-record-v1.md),
[ADR-019](../architecture/adr/ADR-019-lexical-frequency-observation.md).

---

## 0. What it produces

```text
gdelt|web-ngrams/1gram|20260830091500|ENGLISH|climate
    ↓
record_kind  lexical_frequency_observation
term         {"text": "climate", "gram_size": 1, "scheme": "gdelt-web-ngram"}
language     {"source_label": "ENGLISH", "source_scheme": "cld2-language-name",
              "mapping_state": "NOT_ESTABLISHED", "canonical_tag": null}
observation  {"value": "55", "value_state": "REPORTED",
              "unit": null, "unit_state": "NOT_PUBLISHED"}
period       {"type": "INTERVAL", "label": "20260830091500",
              "start": "2026-08-30T09:15:00", "end": "2026-08-30T09:30:00",
              "timezone_state": "NOT_ESTABLISHED"}
quality      PARTIAL — PERIOD_TIMEZONE_NOT_ESTABLISHED, LANGUAGE_NOT_MAPPED
observed_at  NULL
```

**No `geography` key.** Absent, not null.

## 1. Identity and versioning

| | |
|---|---|
| normalizer | `gdelt-web-ngram-lexical@1.0.0` |
| serves | `(gdelt, gdelt-web-ngram)` |
| accepts collector versions | `{1.0.0}` |
| resources | `web-ngrams/1gram`, `web-ngrams/2gram` |
| schema | `sros.normalized-record/1` |

The id follows the World Bank convention — collector family plus payload kind —
so `gdelt-web-ngram-lexical` reads as *the lexical adapter for the WEB-NGRAM
collector* rather than as *the GDELT adapter*. A DOC API collector, if H-27 is
ever closed, gets its own.

**What requires a version bump:** answering H-29 and emitting established
timezones; answering H-30 and emitting canonical tags; any change to the payload
shape, a field's meaning or the fingerprint; a change to how the term is
preserved or the gram size derived. **Not** a reworded message, a refactor or a
new test.

## 2. It is offline, and that is asserted on the code

No HTTP client, no language lookup, no model, no embedder — checked by **walking
the module's imports**, not by grepping its text. A substring scan fails on the
docstring that explains the rule, which teaches the next person to weaken the
assertion rather than to trust it.

Determinism is asserted the way it has to be: the same record through a
different clock and a different correlation id produces a byte-identical
payload, fingerprint and record id.

## 3. `DATE` — H-29 preserved

```python
CanonicalPeriod(
    type=INTERVAL, label=<exact source label>,
    start=<naive wall-clock>, end=start + 15 minutes,
    timezone_state=NOT_ESTABLISHED,
)
```

**Nothing converts a timezone.** `astimezone`, `utcnow`, `now` and `localtime`
do not appear as calls anywhere in the module, and no `tzinfo=` keyword is
passed — asserted over the AST rather than the file's text, for the reason
above.

`observed_at` is **`NULL`**: a naive datetime cannot enter a `TIMESTAMPTZ` and an
aware one would carry an offset GDELT never published.

**The exact label survives** in `period.label`, so answering H-29 later is a
normalizer version bump over records already held — not a re-collection. That is
the whole reason §7 asks for the source representation to be kept alongside the
parsed bounds.

The adapter re-validates the label itself rather than trusting the collector's
validation: fourteen digits, a real calendar date, a minute on the published
quarter-hour grid, zero seconds. A label failing any of those is
`PERIOD_NOT_SUPPORTED` and the record is `INVALID` — reported rather than
approximated.

## 4. `LANG` — H-30 preserved

`CanonicalLanguage.unmapped(label, "cld2-language-name")`. The label verbatim,
`mapping_state = NOT_ESTABLISHED`, `canonical_tag = null`.

**No mapping table exists in the module**, asserted over its string constants:
`"en"`, `"fr"`, `"es"`, `"ko"`, `"de"`, `"ja"` and `"BCP-47"` appear nowhere.

`ENGLISH` is not `en`, and the resemblance is exactly why this is dangerous: the
mapping is obvious for the labels a reader thinks of and silently wrong for the
first one they do not — a CLD2 name with an underscore, or a distinction ISO 639
draws that CLD2 does not.

`content_language` on the row stays `NULL`. That column's contract means a code.

**A language is never a geography.** There is no geography key, and no country,
region or ISO code appears anywhere in the payload.

## 5. `NGRAM` — verbatim, and unclassified

The term is stored **exactly as the source published it**: not trimmed, not
case-folded, not normalised. That last point was a real defect during
implementation — the first draft used a helper that stripped whitespace, so a
term GDELT published with an edge space would have been stored as a different
term, invisibly, in the payload, the fingerprint and the identity. A test with
`"  spaced  "` caught it.

There are now two helpers and the split is the point:

| Helper | For | Behaviour |
|---|---|---|
| `_text` | **our own** provenance and configuration strings | trimmed |
| `_source_text` | anything the **source** published | verbatim |

A term that is empty *after stripping* is refused, because whitespace is not a
term — a different question from what to store when there is content.

**Nothing classifies it.** No theme, topic, entity, keyword intent, sentiment,
market, problem or desire appears in the payload, asserted over the serialised
form so a *new* field carrying one would fail too.

### 5.1 `gram_size` comes from the resource

`web-ngrams/1gram` → 1, `web-ngrams/2gram` → 2, from a literal mapping and from
nowhere else. `.split(` and `.count(` do not appear in the mapping code.

A single-word term in the bigram file keeps `gram_size` 2, and a two-word term in
the unigram file keeps `gram_size` 1. **Counting spaces would silently correct a
contract violation instead of leaving it visible in the data.**

And when the payload's own `gram_kind` contradicts its resource id, the record is
**refused**: choosing a winner between two source facts would be exactly the
silent correction §9 forbids.

## 6. `COUNT` — exact, and not a signal

An arbitrary-precision `Decimal`, read from the canonical decimal string the
collector wrote, so it never passes through a float on either side of
persistence. `float(` does not appear in the module.

| Input | Result |
|---|---|
| `"55"`, `42` | `REPORTED`, exact |
| `"0"` | `REPORTED` — the source saying "none in this bucket" is a measurement |
| `"9007199254740993"` | exact. A float round-trip returns `…92` |
| `"-5"`, `"10.5"`, `"many"`, `1.5`, `True` | `UNREADABLE`, `MALFORMED_NUMERIC_VALUE`, `PARTIAL` |

**`unit_state = NOT_PUBLISHED`, `unit = null`.** `"mentions"`, `"occurrences"`
and `"articles"` appear nowhere in the module: GDELT publishes four columns and
none is a unit, so claiming one would assert the source did something it did not.
The record kind already says the number is an occurrence count over a window.

## 7. Quality — `PARTIAL`, by design

Every record carries both open-question reasons, so `VALID` is **unreachable for
this adapter by construction**. That is honest rather than defeatist: two
canonical facts a consumer would expect really are missing, and a state saying
nothing is missing would be false.

The reasons come out in a **stated order** — period, then language, then value —
because the adapter builds them in that order and nothing sorts afterwards. The
order is the collection sequence, and a test runs it three times to prove it.

**Neither open question is in the fatal set.** A known, representable absence is
not a reason to make a record unreadable. Only `PERIOD_NOT_SUPPORTED` is fatal.

Every reason carries a canonical code, a field path and prose. The code is what a
consumer branches on; recording only the sentence would make the branch depend on
a string somebody may reword.

## 8. Identity, revision and lineage

`observation_key` is **inherited verbatim** — never reconstructed. The RawRecord
already carries the source, the resource, the date, the language and the term,
and the resource id in the key is what keeps `1gram` and `2gram` distinct without
a sixth field.

`COUNT` is content, so a corrected count is a **revision of the same
observation**: same key, different fingerprint, and the Mission 1.6 supersession
mechanism handles the rest unchanged.

Row identity is the existing contract —
`(workspace_id, raw_record_id, schema_version, normalizer_id, normalizer_version)`
— and **D-08 is not solved here**. Normalizer versions still coexist.

Provenance carries the raw record id and hash, the acquisition facts copied
rather than joined (the raw record expires eleven months first), the attribution
notice verbatim, the retention decision and the normalization versions.

## 9. Attribution and retention are not the adapter's to choose

`build_normalized` has **no parameter** for either. A raw record with no rendered
attribution is refused rather than normalized into a row with no credit
attached, and `expires_at` is the resolved **normalized** window — 365 days from
normalization, never the raw record's 30-day expiry copied across.

Rights are lineage, not a decision: `DIRECT_GRANT` with no licence travels from
the RawRecord's provenance, and the normalizer re-authorizes nothing.
**Normalization is not acquisition authorization.**

## 10. Personal data

No detection, no resolution, no classification. A term may happen to be a
person's name; the adapter does not look, and the payload carries no URL, title,
author, image or profile. **H-12 stays open.**

## 11. What it does not do

Interpret, classify, embed, cluster, score, or produce a signal, claim or
evidence. It maps one source-native observation into one canonical observation
and stops.
