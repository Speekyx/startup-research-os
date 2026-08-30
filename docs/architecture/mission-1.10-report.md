# Mission 1.10 — the canonical model gained a second shape, and two honest absences

**Sprint 1 / Mission 1.10** · 2026-08-30
**Status:** **Complete.** The canonical model can represent a GDELT WEB-NGRAM
observation without inventing a timezone, a language code, a geography or a
classification. **No normalizer was written and no GDELT record was normalized.**
Six World Bank normalized records are byte-for-byte unchanged.

---

## 1. Can the current model represent GDELT truthfully?

**Before this mission: no, for three fields out of four.** And the three failures
were different in kind, which is why one fix would not have done.

| Field | Failure | Kind of gap |
|---|---|---|
| `DATE` | `CanonicalPeriod` **requires** timezone-aware bounds | a missing **state** |
| `LANG` | there is no canonical language concept at all | a missing **value object** |
| `NGRAM` | the only kind requires a `metric` and a `geography` | a missing **record kind** |
| `COUNT` | — | **none.** `CanonicalValue` fits exactly |

Each had an easy wrong answer available — assume UTC, put `ENGLISH` in
`content_language`, call the term a metric — and each would have produced records
that look right and are not.

Full working: [`gdelt-normalized-record-gap-analysis-v1.md`](../data/gdelt-normalized-record-gap-analysis-v1.md),
written **before** any model change, as §3 requires.

## 2. `DATE` — the period can now say the zone is unknown

The obstruction was three lines in a constructor:

```python
if getattr(self, name).tzinfo is None:
    raise ValueError(f"period {name} must be timezone-aware")
```

A canonical period could not exist without a timezone, so every route into one
required choosing a zone GDELT never published.

**The gap was a state, not a type.** `NormalizedPeriodType.INTERVAL` already
means *"an arbitrary interval the source stated explicitly, where no calendar
unit describes it"*, which is exactly a 15-minute bucket — **no new period type
was added**, and a `MINUTE_15` member would have encoded one source's cadence
into a closed enum.

```text
ESTABLISHED      bounds are timezone-AWARE   (the Mission 1.6 rule, unchanged)
NOT_ESTABLISHED  bounds are timezone-NAIVE   (a wall-clock reading — floating time)
```

**Python's naive `datetime` is already the right representation** of a
wall-clock reading with no zone, so this is not a new concept invented for the
occasion. Code that treats one as UTC has made an error a type checker can see.

Three alternatives were rejected, and the third is the interesting one:

| Rejected | Because |
|---|---|
| nullable bounds | a period with no bounds cannot be computed over, and every existing period would weaken for one source |
| a second period value object | two period concepts is worse than one honest one; every consumer would branch on which it got |
| **an aware UTC datetime beside a flag** | **a lie next to a disclaimer. Code reads the datetime** |

### 2.1 `observed_at`, and the change that must change nothing

`observed_at` is derived from `period.event_time`, which is `None` under
`NOT_ESTABLISHED`. A naive datetime cannot enter a `TIMESTAMPTZ` and an aware one
would be the invention again. §4 asks that `observed_at` not be abused; leaving it
empty is how it is not — the same answer Mission 1.9.3 reached one layer down.

**`timezone_state` is serialised only when it is not `ESTABLISHED`.** The payload
is inside the content fingerprint, so an unconditional key would have changed the
hash of every record ever written — for a fact those records already state, since
an ISO-8601 string discloses its own offset or its absence.

That asymmetry was made a deliberate design decision by a test that compares an
existing payload against a **literal**, not a round-trip:

```python
assert year_period("2018").to_json() == {
    "type": "YEAR",
    "label": "2018",
    "start": "2018-01-01T00:00:00+00:00",
    "end": "2019-01-01T00:00:00+00:00",
    "end_inclusive": False,
}
```

A round-trip through the code that changed would have agreed with itself.

## 3. `LANG` — a canonical language that can stay unmapped

`CanonicalLanguage`, shaped after `CanonicalGeography` because the analogy is
close enough to copy on purpose:

| Geography | Language |
|---|---|
| `source_code` — verbatim | `source_label` — verbatim |
| `source_name` | `source_scheme` — which vocabulary the label is from |
| `kind: COUNTRY/AGGREGATE/UNKNOWN` | `mapping_state: ESTABLISHED/NOT_ESTABLISHED` |
| `canonical_code` — only where the map establishes it | `canonical_tag` — only where a mapping establishes it |

`unmapped()` is the counterpart of `unclassified()`, and the constructor refuses
a tag without a mapping **and** a mapping without a tag — both directions, because
one alone leaves the other fabrication writable.

**`source_scheme` has no geography counterpart and earns its place.** `ENGLISH`
means something only once a reader knows it came from CLD2 rather than from ISO
639's English names, which overlap and are not identical.

**`content_language` on the row stays `NULL`.** That column's contract means a
code, and a name in it would be a guess wearing the clothes of a fact.

## 4. `NGRAM` — a second record kind

**`lexical_frequency_observation`** — *one occurrence count the source measured
for one lexical term, in one language, over one period.*

`numeric_observation` could not hold it for two independent reasons, and both
matter:

**Its required fields cannot be satisfied.** `geography.source_code` is required
and a WEB-NGRAM row has none. Supplying one would be an invention; omitting it
would make every record `INVALID` — the model reporting a defect in itself.

**And a term is not a metric.** A metric is a *definition* — population, GDP —
reused across geographies and periods. `climate` is an observed item, and the
thing measured is how often it appeared.

**Widening the existing kind was rejected**, and this is §2 and §15 doing real
work: making `geography` optional would let a **World Bank** record exist with no
geography. The existing model must not get worse to fit a new source.

The payload has **no `geography` key at all** — absent, not null. A null would
invite a reader to think one was looked for and not found.

### 4.1 `gram_size` — §10

From the **resource id**, never from counting spaces in the term: a two-word entry
in a unigram file is a contract violation, and counting would hide it where the
resource surfaces it. A test asserts the payload class's source contains no
`.split(` or `.count(`.

It lives in **content** (a bigram is a different kind of observation from a
unigram) and in **provenance** (`series.resource_id`), and **not in identity** —
because `observation_key` is inherited verbatim from the RawRecord and already
contains the resource id. `.../1gram/...climate` and `.../2gram/...climate` are
already two observations.

## 5. `COUNT` — no change needed

`CanonicalValue` fits exactly: an exact `Decimal` serialised as a decimal string,
never a float, with `value_state` distinguishing a reported zero from an absence.
The 2⁵³-exceeding count survives unchanged.

### 5.1 The unit — §8

**`NOT_PUBLISHED`, `unit = null`.**

GDELT's file has four columns and none is a unit. `NOT_PUBLISHED` means exactly
*"the authorized access path does not carry a unit for this observation"*, which
is true and checkable.

**`"mentions"` was considered and rejected.** GDELT describes the count in prose
and publishes no unit field, so `PUBLISHED: "mentions"` would assert the source
did something it did not. §8 forbids inventing an SI-like unit to satisfy a
required field.

**And the record kind carries what a unit would have carried.**
`lexical_frequency_observation` already says the number is an occurrence count
over a stated window — more reliably than a string would.

`UNKNOWN` was also rejected: it is reserved for a source that *may* publish a
unit and did not for one observation. GDELT publishes none for any row, which is
a settled fact about the access path, and the contract keeps those two
distinguishable on purpose.

## 6. Identity — unchanged, and it already worked

```text
observation_key  gdelt|web-ngrams/1gram|20260830091500|ENGLISH|climate
                 inherited VERBATIM from the RawRecord

row identity     (workspace_id, raw_record_id, schema_version,
                  normalizer_id, normalizer_version)
```

**`COUNT` is content, not identity.** A corrected count produces a new RawRecord
with the same `observation_key`, whose normalization supersedes the previous row
**within the same lineage** and leaves it readable. That is the Mission 1.6
mechanism working unchanged — **no model change was required for identity at
all**, which is worth stating because it was the one thing §9 asked about that
turned out already to be right.

## 7. Historical coexistence — D-08 untouched

A future `1.1.0` normalizer emitting established timezones would write
**additional** rows. The `1.0.0` rows stay, unsuperseded, because superseding
across lineages would be the selection policy D-08 forbids inventing.

So after H-29 is answered a single observation may have two normalized rows — one
saying the zone was unestablished, one saying what it is. **Which a consumer
should read is D-08**, still open, and nothing here decided it incidentally.

## 8. Schema and ADR decisions

**One migration, and no table was altered.** Migration 0011 inserts one registry
row. §14 asks that a migration exist only where genuinely required, and it is:
`normalized_records.record_kind_id` has a foreign key to
`registry.registry_entries`, so a kind the registry does not know cannot be
persisted, and `validate_normalization.py` asserts that the kinds declared in
`RECORD_KINDS` are exactly those a migration inserts.

**An ADR, because closed contract enums are hard to reverse.** Two new enums and
two quality reasons enter a generated contract, and an enum member is hard to
remove once persisted records reference it. [ADR-019](adr/ADR-019-lexical-frequency-observation.md).

### 8.1 An inconsistency found and recorded rather than papered over

Migration 0009's comment says a new adapter does **not** need a migration. The FK
and the validator together make that false. Both rules are good; the comment was
written before either was exercised.

0009 is history and the row it inserted is correct, so it was not rewritten.
Migration 0011 and `normalized-record-v1.md` §4 state the rule as it actually is.

### 8.2 A validator that would have stopped checking

`validate_normalization.py` compared `RECORD_KINDS` against **migration 0009 by
filename**. That was right while one kind existed and would have silently covered
a smaller set the moment a second arrived in a second file — still passing, over
less than it claimed. It reads every migration now.

## 9. Tests

**46 new tests** in `test_lexical_frequency_model.py`, and the shape of them is
recorded as `testing-strategy.md` §22:

- **the two real RawRecords as a specimen**, copied as a literal rather than
  queried — a model test that needed PostgreSQL would be skipped exactly where
  the model is least exercised;
- **every refusal paired with its representation**. A constructor that only ever
  refused would pass every negative test while being unusable;
- **absences asserted over the serialised payload**, because a field-by-field
  check passes while a *new* field carries the thing forbidden.

Two superseded assertions were rewritten in place with docstrings naming what
moved: `test_exactly_one_kind_is_declared` and the one that read migration 0009
by name.

## 10. What did not happen

| | |
|---|---|
| GDELT normalizer | **not written.** No module, nothing in `NORMALIZER_REGISTRY` |
| GDELT normalized records | **0** |
| `IMPLEMENTED_NORMALIZERS` | `{world-bank}`, unchanged |
| signals · embeddings · claims · evidence · scores | **0 · 0 · 0 · 0 · 0** |
| model, embedder or classifier called | **none** |

**A vocabulary entry is not an adapter**, and Mission 1.10 sharpened the standing
rule rather than breaking it:

```text
a kind exists because DATA exists       -- two real GDELT records
an adapter exists because CODE exists   -- NORMALIZER_REGISTRY says which
```

`lexical_frequency_observation` is not hypothetical: a real source publishes that
shape and two real RawRecords hold it. What would be a promise the code does not
keep is registering an *adapter*, and none was.

## 11. Validation

| | |
|---|---|
| full suite | **1,158 tests + 233 subtests across 6 packages**, green |
| zero-dependency suites | 340 tests across 5 packages, run with the **system** interpreter |
| validators | all five green |
| generated contracts | `--check` clean; TypeScript conformance 21/21 |
| ruff · ruff format · mypy strict | clean, 314 files, 115 source files |
| post-suite | 20 tenant and 14 global tables unchanged |

**World Bank: 6 raw and 6 normalized, byte-for-byte identical**, every row
serialised whole and compared.

---

## Explicit answers

| Question | Answer |
|---|---|
| Can the current NormalizedRecord model represent GDELT WEB-NGRAM truthfully? | **Not before this mission** — three of four fields had no truthful destination. **It can now** |
| Is a new RecordKind required? | **Yes**, and it exists: `lexical_frequency_observation` |
| What canonical concept represents NGRAM? | `term` — `{text, gram_size, scheme}`. Not a metric, not a theme, not an entity |
| What canonical concept represents COUNT? | `CanonicalValue`, unchanged. An exact `Decimal` serialised as a decimal string |
| What is COUNT's `unit_of_measure`? | **`NOT_PUBLISHED`**, `unit = null`. `"mentions"` was considered and rejected — the record kind already says what the number is |
| Is DATE treated as UTC? | **No.** No timezone is assigned anywhere |
| Can DATE remain timezone-unestablished? | **Yes** — `timezone_state = NOT_ESTABLISHED` with naive bounds, and `observed_at` `NULL` |
| Is H-29 closed or still open? | **Open.** The model change exists so a record can say so |
| Is LANG mapped to BCP-47? | **No.** No mapping was invented |
| Is H-30 closed or still open? | **Open**, and visible per record through `mapping_state` |
| Can an unmapped source language be represented canonically? | **Yes** — `CanonicalLanguage.unmapped()`, the counterpart of `CanonicalGeography.unclassified()` |
| Is LANG ever geography? | **No.** The two value objects share one field name, asserted structurally |
| Is NGRAM ever a topic, theme or entity? | **No.** Asserted over the serialised payload, not field by field |
| Is COUNT ever a Signal? | **No.** `nlp.signals` is empty and no derived vocabulary appears in the payload |
| Is gram kind preserved explicitly? | **Yes**, from the resource id — in content and in provenance, never inferred from spaces |
| What is the normalized observation identity? | `(workspace_id, raw_record_id, schema_version, normalizer_id, normalizer_version)`, with `observation_key` inherited verbatim |
| Does a changed COUNT produce a revision rather than a new semantic identity? | **Yes**, and no model change was needed — `COUNT` is content and the key excludes it |
| Were any GDELT records normalized? | **No. Zero** |
| Did World Bank data remain byte-for-byte unchanged? | **Yes**, 6 raw and 6 normalized |
| Is Mission 1.10.1 safe to implement the GDELT normalizer? | **Yes.** The contract is decided in [`gdelt-normalization-contract-v1.md`](../data/gdelt-normalization-contract-v1.md) and every value object it needs exists and is tested |

---

## What was hard, and what I would flag to a reviewer

**The period was the difficult one, and the tempting fix was the worst.** Storing
an aware UTC datetime beside a flag saying it is not really UTC would have passed
every test and satisfied every type — and code reads the datetime, not the flag.
The naive-bounds answer is uncomfortable (some tooling treats naive datetimes as
local time) and that discomfort is the point: a naive datetime is *visibly* not a
moment, where an aware UTC one would have been invisibly wrong.

**The conditional serialisation deserves a reviewer's attention.** A consumer
reading `period.timezone_state` must default it to `ESTABLISHED`. The alternative
was changing the fingerprint of every record ever written, and the ISO string
already discloses what the key says — but it is a real ergonomic cost and it is
in ADR-019's consequences rather than buried.

**Two documents said things that had stopped being true**: migration 0009's
comment about migrations, and a validator reading one migration by name. Both
were correct when written. Neither was rewritten out of history; both are recorded
with the rule as it actually is.

**Every GDELT normalized record will be `PARTIAL`, and that is the design.** Two
things a consumer would expect are absent and both now have a reason code.
Marking them `VALID` would say nothing is missing when two known things are.

**What I did not do:** no normalizer, no normalized record, no signal, no
embedding, no claim, no evidence, no score, and no answer to D-08.
