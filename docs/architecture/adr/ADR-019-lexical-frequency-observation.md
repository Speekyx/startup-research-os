# ADR-019 — A second record kind, and two canonical absences

**Status:** Accepted
**Date:** 2026-08-30
**Mission:** Sprint 1 / Mission 1.10
**Supersedes:** nothing. Extends
[ADR-009](ADR-009-contract-first-code-generation.md) (generated contracts) and
the Mission 1.6 normalized model.
**Related:** [`gdelt-normalized-record-gap-analysis-v1.md`](../../data/gdelt-normalized-record-gap-analysis-v1.md),
[`gdelt-normalization-contract-v1.md`](../../data/gdelt-normalization-contract-v1.md),
[`normalized-record-v1.md`](../../data/normalized-record-v1.md).

---

## Context

Mission 1.9.3 collected two real GDELT WEB-NGRAM observations:

```text
DATE 20260830091500 · LANG ENGLISH · NGRAM climate · COUNT 55
```

The canonical model built in Mission 1.6 could represent **one** of those four
fields. The gap analysis established why, field by field, and the failures are
different in kind:

| Field | Failure |
|---|---|
| `DATE` | `CanonicalPeriod` **requires** timezone-aware bounds, and GDELT documents no timezone (H-29) |
| `LANG` | there is **no canonical language concept at all**, and no CLD2-to-tag mapping is established (H-30) |
| `NGRAM` | the only record kind requires a `metric` and a `geography`; a term is neither |
| `COUNT` | fits `CanonicalValue` exactly |

Each failure had an easy wrong answer available — assume UTC, put `ENGLISH` in
`content_language`, call the term a metric — and each would have produced records
that look right and are not.

## Decision

Three changes, and each is the smallest that removes an invention.

### 1. `CanonicalPeriod` gains a `timezone_state`

```text
ESTABLISHED      bounds are timezone-AWARE     (the Mission 1.6 rule, unchanged)
NOT_ESTABLISHED  bounds are timezone-NAIVE     (floating time — a wall-clock reading)
```

`observed_at` is derived from `period.event_time`, which is `None` under
`NOT_ESTABLISHED`. A naive datetime cannot enter a `TIMESTAMPTZ` and an aware one
would carry an offset the source never published.

`to_json()` emits `timezone_state` **only when it is not `ESTABLISHED`**, so
every payload written before this change is byte-identical.

### 2. `CanonicalLanguage`, shaped after `CanonicalGeography`

```text
source_label   verbatim, always present
source_scheme  which vocabulary the label is from
mapping_state  ESTABLISHED | NOT_ESTABLISHED
canonical_tag  only under ESTABLISHED
```

`unmapped()` is the counterpart of `CanonicalGeography.unclassified`, and the
constructor refuses a tag without a mapping and a mapping without a tag.

### 3. A second record kind: `lexical_frequency_observation`

*One occurrence count the source measured for one lexical term, in one language,
over one period.* It has **no geography key at all** — absent, not null — and its
`term` is not a metric.

`build_normalized` now takes a three-member `CanonicalObservation` protocol
rather than `NumericObservation`.

## Alternatives considered

### For the period

| Option | Rejected because |
|---|---|
| assume UTC | GDELT publishes no offset. The assumption would land in the field a consumer trusts most, and it would be indistinguishable from an established one |
| nullable bounds | a period with no bounds cannot be computed over, and every existing period would weaken to accommodate one source |
| a second period value object | two period concepts is worse than one honest one; every consumer would branch on which it received |
| an aware UTC datetime beside a flag | a lie next to a disclaimer. Code reads the datetime |
| a `MINUTE_15` period type | `INTERVAL` already means "an arbitrary interval the source stated explicitly"; a new member would encode one source's cadence into a closed enum |

### For the language

| Option | Rejected because |
|---|---|
| `content_language = "ENGLISH"` | that column's contract means a **code**. A name in it is a guess wearing the clothes of a fact |
| derive `en` from `ENGLISH` | resemblance is not a mapping. The first CLD2 name that does not resemble its tag — or a distinction ISO 639 draws that CLD2 does not — would be silently wrong |
| reuse `CanonicalGeography` | **a language is not a place** |
| a bare `str` on the payload | loses the mapping status, which §5 requires to stay visible |

### For the term

| Option | Rejected because |
|---|---|
| `metric.id = "climate"` | a metric is a *definition* reused across geographies and periods. A term is an observed item, and the thing measured is how often it appeared |
| widen `numeric_observation` (optional geography) | a World Bank record could then exist with no geography. **The existing model must not get worse to fit a new source** |
| a `theme` or `entity` slot | asserts a classification no classifier made and a resolution no resolver ran |
| infer `gram_size` from spaces | a two-word entry in a unigram file is a contract violation, and counting spaces would hide it |

### For the unit

`NOT_PUBLISHED`. `"mentions"` was considered: GDELT describes the count in prose
and publishes no unit field, so `PUBLISHED` would assert the source did something
it did not. The record kind already says the number is an occurrence count over a
window, which is what a unit string would have said less reliably. `UNKNOWN` is
reserved for a source that *may* publish a unit and did not for one observation;
GDELT publishes none for any row, which is a settled fact about the access path.

## Consequences

### Good

- **Two open questions became statable rather than papered over.** A record can
  now say *the timezone is not established* and *this language is not mapped*,
  and downstream can branch on both.
- **The existing model did not weaken.** Aware bounds are still required where a
  zone is established; `numeric_observation` still requires a geography and a
  metric; every World Bank payload is byte-identical.
- **The record-kind registry had its first real use** and worked as
  `normalized-record-v1.md` §4 promised — a new shape without altering a table.

### Costs, stated plainly

- **A closed contract enum gained two members and a quality vocabulary gained
  two reasons.** Enum members are hard to remove once persisted records
  reference them, which is why this is an ADR.
- **`to_json()` is conditional.** A consumer reading `period.timezone_state`
  must default it to `ESTABLISHED`. The alternative was rewriting the
  fingerprint of every existing record, and the ISO string already discloses its
  offset or its absence.
- **`NOT_ESTABLISHED` periods carry naive datetimes**, which some tooling treats
  as local time. That is a real hazard, and it is also the point: a naive
  datetime is *visibly* not a moment, where an aware UTC one would have been
  invisibly wrong.

### Not decided here

- **H-29 and H-30 stay open.** These changes exist so a record can say so.
  Answering either later is a normalizer version bump over records already held,
  not a re-collection.
- **D-08 is untouched.** Which normalized version a consumer should read is
  still undecided, and nothing here decides it incidentally.
- **No adapter exists.** `NORMALIZER_REGISTRY` and `IMPLEMENTED_NORMALIZERS`
  gained nothing, no GDELT record was normalized, and the registry row inserted
  by migration 0011 is a **vocabulary** entry rather than a claim that code
  exists.
