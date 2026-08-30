# Mission 1.10.1 — two real GDELT observations, and two absences stated per record

**Sprint 1 / Mission 1.10.1** · 2026-08-30
**Status:** **Complete.** `gdelt-web-ngram-lexical@1.0.0` normalized the two real
GDELT RawRecords into canonical lexical frequency observations, both `PARTIAL`.
Six World Bank normalized records are byte-for-byte unchanged. **No signal, no
embedding, no claim, no evidence, no score.**

---

## 1. Normalizer architecture

The World Bank precedent, followed where it applies. Same `Normalizer` protocol,
same `NormalizerSpec`, same `build_normalized`, same job — **no parallel
subsystem and no "generic source normalizer framework"**, which §24 warned
against and which two adapters do not justify.

Where it differs is where the source differs:

| | World Bank | GDELT WEB-NGRAM |
|---|---|---|
| kind | `numeric_observation` | `lexical_frequency_observation` |
| constructed with | retention **and** the geography map | retention only |
| identity of the thing measured | a metric | a lexical term |
| geography | required | **absent** — not null |
| quality, in practice | `VALID` | **`PARTIAL`, always** |

It takes **no geography map**, deliberately. Constructing it with a
classification table it never consults would suggest it might.

## 2. Normalizer version

```text
gdelt-web-ngram-lexical@1.0.0   serves (gdelt, gdelt-web-ngram)
                                accepts collector versions {1.0.0}
                                schema sros.normalized-record/1
```

The id follows the World Bank convention — collector family plus payload kind —
so it reads as *the lexical adapter for the WEB-NGRAM collector*, not *the GDELT
adapter*. A DOC API collector, if H-27 is ever closed, gets its own.

**Registered last**, after the tests passed (§25), and only for the collector it
serves: a second collector for one source parses a different shape, and handing
it to this adapter would produce plausible nonsense rather than an error.

## 3. Accepted resources

`web-ngrams/1gram` and `web-ngrams/2gram`, and nothing else. Refused with
`UNSUPPORTED_SOURCE`: `web-ngrams/3gram`, Web News NGrams 3.0, the quadgram
files, the TOC, every DOC API mode, and an empty resource id. Also refused: a
record from another source, and one from another collector.

## 4. The offline boundary

No HTTP client, no language lookup, no model, no embedder — **asserted by walking
the module's imports**, not by grepping its text. Determinism is asserted the way
it has to be: the same record through a different clock and a different
correlation id yields a byte-identical payload, fingerprint and record id.

## 5. `DATE`

```python
CanonicalPeriod(type=INTERVAL, label=<exact source label>,
                start=<naive wall-clock>, end=start + 15 minutes,
                timezone_state=NOT_ESTABLISHED)
```

The adapter **re-validates the contract itself** rather than trusting the
collector's validation — fourteen digits, a real calendar date, a minute on the
published quarter-hour grid, zero seconds. A label failing any of those is
`PERIOD_NOT_SUPPORTED` and the record is `INVALID`, reported rather than
approximated.

## 6. H-29 preserved

**No timezone is assigned, and nothing can assign one.** `astimezone`, `utcnow`,
`now` and `localtime` appear as calls nowhere in the module and no `tzinfo=`
keyword is passed — asserted over the AST.

`observed_at` is **`NULL`**: a naive datetime cannot enter a `TIMESTAMPTZ` and an
aware one would carry an offset GDELT never published.

**The exact label survives** in `period.label`, which is what makes H-29 cheap to
answer later: a normalizer version bump re-derives from records already held. No
re-collection. That is the whole reason §7 asks for the source representation to
be kept alongside the parsed bounds.

## 7. `LANG`

`CanonicalLanguage.unmapped(label, "cld2-language-name")` — the label verbatim,
`mapping_state = NOT_ESTABLISHED`, `canonical_tag = null`.

`content_language` on the row stays `NULL`. That column's contract means a code.

**Never geography.** No geography key, and no country, region or ISO code appears
anywhere in the payload.

## 8. H-30 preserved

**No mapping table exists in the module** — `"en"`, `"fr"`, `"es"`, `"ko"`,
`"de"`, `"ja"` and `"BCP-47"` appear in none of its string constants, asserted
over the AST.

`ENGLISH` is not `en`, and the resemblance is exactly why this is dangerous: the
mapping is obvious for the labels a reader thinks of and silently wrong for the
first one they do not.

## 9. `NGRAM`

Stored **exactly as the source published it**. This is where implementing the
contract found a real defect — see §26.1.

**Nothing classifies it.** No theme, topic, entity, keyword intent, sentiment,
market, problem or desire appears in the payload, asserted over the *serialised*
form so a new field carrying one would fail too.

## 10. `gram_size`

From the resource id, via a literal mapping, and from nowhere else. `.split(`
and `.count(` do not appear in the mapping code.

A single-word term in the bigram file keeps `gram_size` 2; a two-word term in the
unigram file keeps `gram_size` 1. **Counting spaces would silently correct a
contract violation instead of leaving it visible in the data.**

And when the payload's own `gram_kind` contradicts its resource id, the record is
**refused** — choosing a winner between two source facts is exactly the silent
correction §9 forbids.

## 11. `COUNT`

An arbitrary-precision `Decimal`, read from the canonical decimal string the
collector wrote, so it never passes through a float on either side of
persistence. `float(` does not appear in the module.

| Input | Result |
|---|---|
| `"55"`, `42` | `REPORTED`, exact |
| `"0"` | `REPORTED` — "none in this bucket" is a measurement |
| `"9007199254740993"` | exact; a float round-trip returns `…92` |
| `"-5"`, `"10.5"`, `"many"`, `1.5`, `True` | `UNREADABLE` + `MALFORMED_NUMERIC_VALUE`, `PARTIAL` |

## 12. The unit

`unit_state = NOT_PUBLISHED`, `unit = null` — the Mission 1.10 decision applied
unchanged. `"mentions"`, `"occurrences"` and `"articles"` appear nowhere in the
module: GDELT publishes four columns and none is a unit, so claiming one would
assert the source did something it did not.

## 13. Record kind

`lexical_frequency_observation`, registered by migration 0011. The serialised
payload has **no `geography` key at all** — absent, not null.

## 14. Quality — `PARTIAL`, by design

Every record carries both open-question reasons, so `VALID` is **unreachable for
this adapter by construction**. That is honest rather than defeatist: two
canonical facts a consumer would expect really are missing, and a state saying
nothing is missing would be false. `INVALID` would be the opposite error —
making a record unreadable for a condition that is universal and expected.

**Only `PERIOD_NOT_SUPPORTED` is fatal.** A known, representable absence is not a
reason to make a record unreadable.

Reasons come out in a **stated order** — period, language, value — because the
adapter builds them in that sequence and nothing sorts afterwards. A test runs it
three times. Each carries a canonical code, a field path and prose: the code is
what a consumer branches on, and recording only the sentence would make the
branch depend on a string somebody may reword.

## 15. Identity

`observation_key` is **inherited verbatim**, never reconstructed. The resource id
inside it is what keeps `1gram` and `2gram` distinct without a sixth field.

Row identity is the existing contract —
`(workspace_id, raw_record_id, schema_version, normalizer_id, normalizer_version)`.

## 16. Revision and supersession

`COUNT` is content, so a corrected count is a **revision of the same
observation**: same key, different fingerprint. The Mission 1.6 supersession
mechanism handles it unchanged, and **D-08 is not solved here** — normalizer
versions still coexist.

## 17. Lineage and provenance

The raw record id and hash, the acquisition facts **copied rather than joined**
(the raw record expires eleven months first), the attribution notice verbatim,
the retention decision and both version pairs. Everything §20 lists is
recoverable without parsing anything.

## 18. Attribution and rights

`build_normalized` has **no attribution parameter**, so the adapter has nothing to
pass and nothing to omit; a raw record with no rendered notice is refused rather
than normalized into a row with no credit attached.

`DIRECT_GRANT` with no licence travels from the RawRecord's provenance. The
normalizer re-authorizes nothing: **normalization is not acquisition
authorization.**

## 19. Retention

365 days from normalization, governance-resolved, `basis: baseline`. There is no
expiry parameter, and the raw record's 30-day window is deliberately not copied —
the two tiers have different authoritative baselines.

## 20. Tenant isolation

Unchanged and re-exercised: the normalization job runs inside a transaction-local
workspace context, the repository filters explicitly, RLS is the second layer and
the composite foreign key the third. The existing suite covers cross-tenant read,
cross-tenant write and a query with no tenant filter; disposable workspaces
throughout.

## 21. Synthetic tests

**89 tests** in `test_gdelt_web_ngram_normalizer.py`, every record synthetic and
built to the documented contract — and the module says so in its first paragraph
rather than letting anyone mistake one for a capture.

Covered: both resources, Unicode, a pipe and a backslash in the term, edge
whitespace, zero, above 2⁵³, negative, decimal, non-numeric, a float, a bool,
five source-native language labels, six malformed dates, a wrong resource, a
wrong collector, a wrong source, an empty payload, a missing term, a missing
language, and a payload contradicting its own resource.

## 22. Real normalization

```json
{"records_input": 2, "records_normalized": 2, "records_partial": 2,
 "records_created": 2, "records_failed": 0,
 "quality_reasons": {"LANGUAGE_NOT_MAPPED": 2,
                     "PERIOD_TIMEZONE_NOT_ESTABLISHED": 2}}
```

Through the same job World Bank uses, with `source_id: gdelt` and
`only_unnormalized`. Every §28 fact verified against the database — the record
kind, the exact label, the naive bounds, `NOT_ESTABLISHED`, `observed_at NULL`,
the exact CLD2 label, `canonical_tag null`, `content_language NULL`, the exact
term, `gram_size` from the resource, the exact count, `NOT_PUBLISHED`, `PARTIAL`
with both reasons, no geography key, and no derived semantics anywhere.

## 23. Repeat normalization

**`records_input: 0`.** The second pass read nothing, because the records are
already normalized under this lineage. No duplicate, no accidental revision.

That zero is also the proof of §26.2: before the fix the pass would have re-read
both records and reported `unchanged: 2`.

## 24. World Bank regression

Snapshotted before implementation and re-checked after the full suite, the real
normalization and the repeat. Every row serialised whole and compared.

| | before | after |
|---|---|---|
| World Bank raw | 6 | 6 — **byte-for-byte identical** |
| World Bank normalized | 6 | 6 — **byte-for-byte identical** |

Mission 1.10 changed shared period serialisation, so this mattered more than
usual. It is also pinned in the suite as a **literal** sha256 rather than a
round-trip — a round-trip through the changed code would agree with itself.

## 25. CI

| | |
|---|---|
| full suite | **1,247 tests + 233 subtests across 6 packages**, green |
| new | 89 normalizer tests |
| external network in CI | **zero** |
| validators | all five green |
| contracts | `--check` clean; TypeScript conformance 21/21 |
| ruff · ruff format · mypy strict | clean, 317 files, 116 source files |
| post-suite | 20 tenant and 14 global tables unchanged |

## 26. Issues found

### 26.1 The adapter was stripping source text

The first draft read the term through `_text()`, which returns
`str(value).strip()`. That helper is right for reading **our own** provenance
strings and wrong for reading a source value: a term GDELT published with an edge
space would have been stored as a *different term*, and the difference would have
been invisible — in the payload, in the fingerprint and in the observation's
identity.

A parametrised case with `"  spaced  "` caught it. There are now two helpers and
the split is the point:

| Helper | For | Behaviour |
|---|---|---|
| `_text` | our own provenance and configuration | trimmed |
| `_source_text` | anything the source published | **verbatim** |

A term empty *after stripping* is still refused, because whitespace is not a term
— a different question from what to store when there is content.

### 26.2 `only_unnormalized` stopped filtering when the second adapter arrived

`_select_records` applied the filter **only when exactly one normalizer was
registered** and dropped it otherwise. The reasoning in its comment was right —
"already normalized" is a property of a raw record *under a given normalizer*,
and guessing a lineage from a two-entry registry would be wrong — but the
conclusion was too coarse.

Correct per record: idempotent persistence classifies a re-read as `UNCHANGED`.
**Silently wrong in bulk:** with the filter dropped and a 500-record batch bound,
a workspace holding 600 raw records would re-read the same first page every pass
and **never reach the last hundred**.

The lineage is knowable per record, because `select_normalizer` keys on
`(source_id, collector_id)`. The filter now carries one lineage per registered
adapter, matched on the collector that wrote the record. A record whose collector
no adapter serves matches no branch, is therefore read, and is reported as
unsupported — which is where that belongs.

Found by a World Bank test asserting `records_input == 0` on a redelivery.

### 26.3 Two structural tests failed on the prose that explains them

`assert "astimezone" not in source` and `assert "ISO 639" not in source` both
failed — on the module docstring saying *"nothing here calls `astimezone`"* and
the comment explaining *"a distinction ISO 639 draws that CLD2 does not"*.

The tempting fix is to weaken the assertion until it passes, and after two or
three rounds of that nobody trusts it enough to add a term to. Both now walk the
AST — imports, attribute names, string constants — which is **stricter**, not
looser: it catches `getattr(dt, "astimezone")` written to dodge a grep.

Recorded as `testing-strategy.md` §23, because Mission 1.9.3 had already recorded
a version of it and this mission walked into it twice in one afternoon.

## 27. Remaining blockers

**Unchanged:** D-03, D-08, D-10, D-12, H-12, H-13, H-22 to H-27, H-31,
PROFILE-NOT-CALIBRATED.

**H-29 — open, and now visible in the data.** Every GDELT normalized record says
`timezone_state: NOT_ESTABLISHED` and has `observed_at NULL`. Any temporal
analysis has to answer it first.

**H-30 — open, and visible the same way.** `mapping_state: NOT_ESTABLISHED`,
`canonical_tag: null`.

**D-08 matters more now than it did.** When H-29 is answered, a `1.1.0`
normalizer will write **additional** rows beside the `1.0.0` ones rather than
superseding them — superseding across lineages would be the selection policy D-08
forbids inventing. A single observation will then have two normalized rows, one
saying the zone was unestablished and one saying what it is, and **which a
consumer should read is still undecided**.

**Eurostat and FRED** are eligible with no authorised resource, no collector and
no normalizer.

## 28. Next-mission readiness

**Signal modelling is safe to begin, with one thing to settle first.**

The pipeline boundary is intact: normalization renamed and reshaped, and decided
nothing. `COUNT` is `source_measured_frequency` and is not a trend, an interest
level or a demand indicator — the record says what GDELT counted and stops there.

What a signal mission must confront on day one is that **the only GDELT
observations available are `PARTIAL` with no event time**. A trend is a shape over
time, and these records deliberately decline to say when they happened in any
comparable frame. Two 15-minute buckets can be ordered by their labels; whether
they can be compared to a World Bank annual observation, or to each other across
a daylight-saving boundary, is exactly what H-29 leaves open.

That is not a reason to delay signal *modelling*. It is a reason for the model to
carry the question rather than assume it away — the same discipline that produced
`timezone_state` in the first place.

---

## Explicit answers

| Question | Answer |
|---|---|
| Is the GDELT normalizer implemented? | **Yes** |
| What version? | **`gdelt-web-ngram-lexical@1.0.0`** |
| Which resources are supported? | `web-ngrams/1gram` and `web-ngrams/2gram`, and nothing else |
| Does normalization make network calls? | **No.** Asserted over the module's imports |
| How is DATE represented? | A 15-minute `INTERVAL` with the exact source label and **naive** bounds |
| Is DATE treated as UTC? | **No.** No conversion call and no `tzinfo=` exists in the module |
| Is H-29 still open? | **Yes**, and every record says so |
| How is LANG represented? | `CanonicalLanguage` with the exact CLD2 label, `source_scheme`, and `mapping_state = NOT_ESTABLISHED` |
| Is a BCP-47 tag invented? | **No.** No language tag appears in the module's string constants |
| Is H-30 still open? | **Yes**, and every record says so |
| Is LANG geography? | **No.** No geography key exists at all |
| How is NGRAM represented? | `term.text`, **verbatim** — not trimmed, case-folded or normalised |
| Is NGRAM classified? | **No.** No theme, topic, entity, intent or sentiment anywhere |
| How is gram_size derived? | From the **resource id**, via a literal mapping. Never from the text |
| How is COUNT represented? | An exact `Decimal`, serialised as a decimal string |
| Is any float used? | **No.** `float(` does not appear, and a float input is `UNREADABLE` |
| What is the unit state? | **`NOT_PUBLISHED`**, `unit = null` |
| Is COUNT a Signal? | **No.** `nlp.signals` is empty and no derived vocabulary appears in the payload |
| What RecordKind is emitted? | `lexical_frequency_observation` |
| Why are real records PARTIAL? | Two canonical facts a consumer would expect are absent, both named: `PERIOD_TIMEZONE_NOT_ESTABLISHED` and `LANGUAGE_NOT_MAPPED` |
| What is the normalized observation identity? | `(workspace_id, raw_record_id, schema_version, normalizer_id, normalizer_version)`, with `observation_key` inherited verbatim |
| Does changed COUNT preserve semantic identity? | **Yes.** COUNT is content; the key excludes it |
| How many real GDELT RawRecords exist? | **2** |
| How many real GDELT NormalizedRecords now exist? | **2** |
| Did repeat normalization create duplicates? | **No.** The second pass read **zero** records |
| Did World Bank remain byte-for-byte unchanged? | **Yes**, 6 raw and 6 normalized |
| Were signals created? | **No.** Zero |
| Were embeddings generated? | **No.** Zero |
| Were Claims or Evidence created? | **No.** Zero |
| Was scoring performed? | **No.** Still blocked on D-03 |
| Is the next mission safe to begin Signal modelling? | **Yes**, with §28's caveat: the only GDELT observations available are `PARTIAL` with no event time, and a trend model must carry that question rather than assume it away |

---

## What was hard, and what I would flag to a reviewer

**The stripping defect is the one I would want re-checked.** It was three
characters of helper reuse, it produced a payload that looked completely correct,
and the only thing that caught it was a parametrised case with leading spaces
that I nearly did not write. `_source_text` exists now, but the general risk —
a convenience helper applied to a source value — is not something a test can
prevent in the abstract.

**The `only_unnormalized` bug was activated, not introduced, by this mission.**
It had been latent since Mission 1.6 and correct-looking the whole time, because
per-record idempotency masked it. It only becomes a data-loss bug at a workspace
size nobody has reached yet, which is exactly the kind that stays hidden.

**Two structural tests failed on their own explanations**, and the fix that
suggests itself first is the one that quietly guts the check. `testing-strategy.md`
§23 exists so the next person reaches for the AST instead.

**Every GDELT record being `PARTIAL` is a design choice worth disagreeing with
out loud if you do.** The alternative readings are `VALID` (which would say
nothing is missing when two known things are) and `INVALID` (which would make the
records unreadable for a condition that is universal and expected). I think
`PARTIAL` is right, and it does mean the quality state carries no per-record
information for this source until H-29 or H-30 is answered.

**What I did not do:** no signal, no embedding, no claim, no evidence, no score,
no third collector, no answer to D-08, and no GDELT data acquired.
