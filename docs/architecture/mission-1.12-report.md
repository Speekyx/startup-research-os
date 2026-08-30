# Mission 1.12 — GDELT WEB-NGRAM Temporal Semantics Resolution

**Sprint:** 1
**Date:** 2026-08-30
**Status:** Complete. **H-32 CLOSED. H-29 OPEN. H-31 answered and refined.**
No extractor, no new Signal, no Claim, no Evidence, no embedding, no score.
**Specifications:** [`gdelt-web-ngram-temporal-evidence-v1.md`](../data/gdelt-web-ngram-temporal-evidence-v1.md),
[ADR-022](adr/ADR-022-web-ngram-source-relative-order.md).

---

## 1. Outcome

Mission 1.12 §22 offered two acceptable outcomes and told me not to force the
first. The evidence produced it anyway.

| §2 question | Verdict |
|---|---|
| **A** — equality of two labels | Established since Mission 1.10.1 |
| **B** — ordering within the WEB-NGRAM stream | **ESTABLISHED.** H-32 closed |
| **C** — globally comparable instants | **NOT established** |
| **D** — timezone / UTC | **NOT established.** H-29 open |

**Outcome A**: source-relative sequential WEB-NGRAM derivation may proceed;
global-instant comparison may not.

---

## 2. §23 — the questions, answered

### What exactly did H-32 ask?

Whether two WEB-NGRAM `DATE` labels from the same source stream can be placed in
source chronological order. **Not** what timezone they are in — that is H-29,
and Mission 1.11 separated them precisely so one could close without the other.

### What first-party evidence was reviewed?

Eight artifacts, all GDELT's own, retrieved 2026-08-30. No Stack Overflow, no
Reddit, no tutorial.

| | Artifact | Bearing |
|---|---|---|
| E1 | The WEB-NGRAM announcement | Format, resolution, cadence, filenames, coverage. **No timezone, no SQL** |
| E2 | "Charting Global English-Language Media Anxiety … BigQuery + WEB NGrams" | GDELT ordering this column, on this table |
| E3 | `MASTERFILELIST.TXT`, bounded reads at both ends of 61,683,006 bytes | The index is label-ordered at 15-minute resolution |
| E4 | `LASTUPDATE.TXT` | The newest publication is the maximal label |
| E5 | The Web News NGrams **3.0** announcement | Where the UTC sentence actually lives |
| E6 | "Using The New Web NGrams Dataset To Find Relevant Coverage" | Checked on its title; a **third** dataset |
| E7 | "Making NGrams At BigQuery Scale" | Checked on its title; Internet Archive books, irrelevant |
| E8 | `gdeltproject.org/data.html` | Links to E1; states no timezone for any dataset |

E6 and E7 are listed because §5 says not to rely on a title. Recording the ones
that were checked and discarded is what makes "we looked" mean anything.

### Does GDELT itself order WEB-NGRAM DATE chronologically in its published examples?

**Yes**, over this exact table:

```sql
SELECT SUBSTR(CAST(DATE AS STRING), 0, 8) DATE, SUM(COUNT) …
FROM `gdelt-bq.gdeltv2.web_1grams` WHERE LANG='ENGLISH' …
GROUP BY DATE ORDER BY DATE ASC
```

charted as a series "from January 1, 2019 through September 30, 2019". Two
things GDELT does there, neither of which is a fact about string sorting: it
**decomposes** the label, reading its first eight characters as a calendar day,
and it **orders by it** to produce a nine-month chart.

### Is that evidence sufficient to establish source-relative ordering?

**On its own, only at day resolution** — the query truncates the label before
ordering it. Saying otherwise would have been the over-reach §6 warns against.

What reaches bucket resolution is E3 and E4. GDELT publishes its own directory
index in ascending label order at 15-minute steps (`000000`, `001500`,
`003000` are consecutive lines) across 7.6 years, and its own "newest file"
pointer is the maximal label.

Mission 1.11 refused this conclusion because the argument available then — a
fixed-width stamp sorts, and a repeated filename would collide — was *an
inference about the publisher's mechanism*. **What changed is the evidence, not
the standard.** The mechanism is now observed: the publisher orders the column,
sequences the directory by it, and calls its maximum the newest.

The daylight-saving objection is answered by the same artifacts rather than
argued away. A wall-clock frame with a fall-back hour would repeat a label; the
label is the filename in one flat directory, and the index is strictly ascending
at both ends across the full dataset. It would also break the "newest = largest"
invariant `LASTUPDATE` is built on.

### Is H-32 closed?

**Yes.**

### What exact scope does the ordering guarantee have?

| | |
|---|---|
| source | `gdelt` |
| resources | `web-ngrams/1gram`, `web-ngrams/2gram` — **named, never a prefix** |
| label scheme | `gdelt-web-ngram-bucket` |
| review version | 3 |
| grants | `SOURCE_RELATIVE_ORDER` |
| grants **nothing else** | no timezone, no `COMPARABLE_INSTANT`, no `observed_at`, no cross-source comparison |

Language and gram kind are **not** part of the ordering scope: ordering is a
property of the publication stream, and the same directory publishes every
language and both gram sizes on one bucket grid. Whether two observations may be
*compared* across a language or a gram size is a different question the
extractor's grouping already answers `no`.

### Does H-32 closure assign a timezone? Is WEB-NGRAM DATE established as UTC?

**No** and **no**. Ordering says which came first. It says nothing about which
clock.

### Is H-29 closed?

**No.** The words UTC, GMT, timezone and "time zone" appear nowhere on the
announcement, and the data page states none for any dataset.

### Why do other GDELT datasets' UTC documentation not automatically close H-29?

Because they are other datasets, and the trap is real rather than hypothetical:
a search for "GDELT ngram DATE timezone" returns the sentence *"the date
represented as 'YYYYMMDDHHMMSS' in the UTC timezone"*, which belongs to **Web
News NGrams 3.0**.

| | WEB-NGRAM (ours) | Web News NGrams 3.0 |
|---|---|---|
| path | `gdeltv3/web/ngrams/` | `gdeltv3/webngrams/` |
| BigQuery | `web_1grams` / `web_2grams` | `webngrams` |
| format | tab-delimited, 4 columns | JSON |
| cadence | every 15 minutes | every minute |
| what `date` MEANS | the **15-minute bucket** the counts aggregate | "the JSON timestamp **when the article was seen**" |
| timezone | **unstated** | **UTC, stated** |

The two `date` fields do not denote the same kind of thing — one is an
aggregation window, the other an observation instant for a single article — and
the 3.0 announcement never mentions `gdeltv3/web/ngrams`. A **third** family,
`gdeltv5/weblegacy/ngrams/`, states none either. Four confusable names; three
are not ours.

**A timing observation was available and was refused.** `LASTUPDATE` named
bucket `20260830184500` while the response carried `last-modified: Sun, 30 Aug
2026 18:50:30 GMT`. That compares a Google Cloud Storage object's write time
against this machine's clock, from one sample, through a CDN — precisely what
H-29's own register entry rules out — and even a clean result would not
distinguish UTC from a fixed-offset zone that equals it today.

### Can `observed_at` now be populated?

**No.** It requires `COMPARABLE_INSTANT`, which requires a timezone. An
`ORDERED_PERIODS` window carries no bounds, and the model refuses one that tries.

### Can existing GDELT NormalizedRecords be rewritten?

**No**, and none were. They keep `timezone_state = NOT_ESTABLISHED` and
`observed_at = NULL`. H-32 is about ordering semantics for derivation; it
establishes nothing retroactively about a zone.

### Is lexical frequency change temporally permitted now? Are rolling windows?

**Yes to both — temporally.** Pairwise bucket comparison, `INCREASING` /
`DECREASING` / `UNCHANGED`, adjacent-bucket sequences, moving averages, rolling
windows and within-source momentum are all no longer blocked by an unestablished
ordering.

**None of them is specified.** Window size, gap handling, what a missing bucket
means, whether a rolling average over a sparse stream is honest — none is
decided here, and §13's distinction is the one to hold onto: **temporally
permitted is not extractor specified.**

### Are cross-source timestamp comparisons permitted?

**No.** Aligning a GDELT bucket with a World Bank year, any "as of" wall-clock
claim, any daylight-saving interpretation, any global instant comparison and any
`TIMESTAMPTZ` conversion all still require H-29.

### What did H-31 mean? Is it closed?

It conflated two questions with different answers and different kinds of
authority. **Refined and answered:**

| | Question | Answer |
|---|---|---|
| H-31a | Dataset **semantic coverage** | **2019-01-01**, documented in the announcement |
| H-31b | Current **download directory extent** | **`20190101000000`** — the current index begins at the dataset's first bucket |

**Closed, with the distinction recorded.** H-31b is an *observation*: GDELT
publishes no retention commitment, so "it reaches back to 2019 today" is a fact
about today and no backfill plan may assume otherwise.

### Were any production Signals created? Were any existing Signals modified?

**None**, and **none**. All five stored signal identities were **recomputed from
their stored lineage** under the changed model and reproduce byte-for-byte:

```text
5/5 stored signal identities reproduce under the changed model
```

No derivation job was run. The one real lexical signal is still
`SAME_PERIOD_LABEL`, `NOT_APPLICABLE`, magnitude `19`.

### Did all 8 RawRecords and 8 NormalizedRecords remain unchanged?

**Yes**, digest identical to the Mission 1.11 baseline:

```text
d8cf83214a930be67f42f018224a657cdb0fdb8028f9f5414eccbd507e55140c
```

### Is Mission 1.12.1 safe to design/implement GDELT sequential lexical-frequency signals?

**Yes, and the temporal question is no longer the hard part.** What is left is
extractor design, and it is genuinely undecided — see §5.

---

## 3. The one model change, and why it was needed

`ORDER_ESTABLISHED_WITHOUT_TIMEZONE` was a `Mapping[str, str]` keyed on
`source_id`. That shape could not express §11's requirement.

A certification keyed on the source alone would grant WEB-NGRAM's ordering to
**every** GDELT dataset — including Web News NGrams 3.0, the quadgram legacy
set, and a `chargram` file the same directory publishes that the announcement
never documents and no review has assessed. §11 forbids exactly that
generalisation.

So the certification became a record naming its `source_id`, its `resource_ids`
**exactly**, its `label_scheme`, its `review_version`, its `basis` and its
`scope`; the constructor refuses one with no basis or no resources; and
`ObservationInput` gained `resource_id` so an observation can say which stream
it came from. The default is `None` and **the default is a refusal**.

`resource_id` is lineage, not identity — it is recorded per input and enters no
fingerprint. That is why all five stored signals reproduce.

**§12 was satisfied without a second temporal concept.** `ORDERED_PERIODS`
already existed; Mission 1.11's escape hatch was used rather than widened.

---

## 4. What the index also showed

`MASTERFILELIST` lists **three** files per bucket:

```text
20190101000000.1gram.txt.gz
20190101000000.2gram.txt.gz
20190101000000.chargram.txt.gz
```

`chargram` is undocumented in the announcement and unreviewed. It is recorded so
its existence is a known fact rather than a future surprise, it is not
authorised, and the certification's named-resource design is what keeps it
uncovered. Had the entry matched a `web-ngrams/` prefix, an unreviewed dataset
would have inherited an ordering guarantee on the day somebody added a
collector for it.

---

## 5. Scope discipline, and what Mission 1.12.1 has to decide

| Forbidden by the brief | State |
|---|---|
| A new extractor | Not written |
| New production Signals | 0 created |
| Existing Signals modified | 0; all five identities recomputed and identical |
| Existing NormalizedRecords rewritten | 0; both GDELT records still `NOT_ESTABLISHED` / `NULL` |
| Claims, Evidence, Opportunities, embeddings, scores | All 0 |
| H-30 solved incidentally | Untouched; exact source-language equality remains the scope |

### What is actually undecided for a sequential extractor

The temporal permission exists. These do not:

1. **Gaps.** GDELT publishes a bucket every 15 minutes; the directory index does
   not promise none is ever missing. Is a change across a gap a change, or a
   refusal? An extractor that silently bridged one would be inventing continuity.
2. **Window size and shape.** Adjacent buckets, N-bucket rolling, a baseline
   period — each is a different assertion, and each is a parameter someone has
   to justify rather than default.
3. **Sparsity.** A term absent from a bucket is **absent**, not zero — the
   normalization layer's rule, and it makes a moving average over a sparse term
   a question about what the denominator is.
4. **Volume.** A bucket holds ~223,000 terms. The same reason
   `lexical-frequency-contrast` requires its `terms` parameter applies with more
   force to a sequence over many buckets.

None of these is a temporal question, and that is the point: closing H-32 moved
the problem from *may we* to *how*.

---

## 6. Validation

```text
zero-dependency suites   417 tests across 6 packages  (12 new)
pytest suites            294 tests across 7 packages  (6 new)
schema validation        9 invariant groups, 36 tables
signal boundary guard    5 boundary groups
normalization guard      9 boundary groups
evidence aggregation     8 checks; production scoring still blocked
contracts --check        3 generated artifacts current
TypeScript conformance   21/21
mypy strict              129 source files
ruff + ruff format       clean
```

Data, before and after: **8 raw · 8 normalized · 5 signals · 10 signal inputs ·
0 embeddings · 0 claims · 0 evidence · 0 opportunities.**

---

## 7. Risks left open

- **The finding rests on artifacts, not on a sentence.** GDELT never wrote "these
  labels are monotonic"; it ordered them, indexed them and pointed at their
  maximum. That is stronger in one sense and more fragile in another — if the
  publication scheme changed, the evidence would have to be re-taken. It is
  dated, its retrieval method is recorded, and it names review version 3.
- **H-29 is now the only temporal blocker, and it is unchanged.** Everything
  cross-source still waits on one first-party sentence or an operator answer.
- **`chargram` exists and nobody has looked at it.** Not a risk today; a known
  unknown in the same directory the collector reads.
- **The certification is one entry and easy to add a second to.** The constructor
  refuses an empty basis, and nothing refuses a *bad* one. That is a review
  discipline, not a mechanism.
- D-03, D-08, D-10, D-12, H-12, H-13, H-22 to H-27, H-29, H-30,
  PROFILE-NOT-CALIBRATED unchanged.
