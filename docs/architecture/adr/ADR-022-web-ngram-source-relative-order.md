# ADR-022 — WEB-NGRAM labels are ordered; they still have no timezone

**Status:** Accepted
**Date:** 2026-08-30
**Mission:** Sprint 1 / Mission 1.12
**Amends:** [ADR-020](ADR-020-signal-derivation-model.md) Decision 3, which
recorded H-32 as open and the certification map as empty. That text stands as
written; this ADR records what closed it.
**Extends:** [ADR-019](ADR-019-lexical-frequency-observation.md) (a canonical
absence is stated, never filled in).
**Related:** [`gdelt-web-ngram-temporal-evidence-v1.md`](../../data/gdelt-web-ngram-temporal-evidence-v1.md),
[`signal-temporal-semantics-v1.md`](../../data/signal-temporal-semantics-v1.md).

---

## Context

ADR-020 separated two facts that a single timezone flag had been conflating:

```text
SOURCE_RELATIVE_ORDER   which of two observations came first, within one stream
COMPARABLE_INSTANT      what moment each corresponds to, on a shared timeline
```

Neither was granted to GDELT. `COMPARABLE_INSTANT` was withheld by **H-29**, the
undocumented timezone. `SOURCE_RELATIVE_ORDER` was withheld by **H-32**, and
ADR-020 was explicit about why the available argument was not good enough:

> The argument is an *inference about the publisher's mechanism*, not a
> retrieved statement about the data … That is the same class of reasoning
> `geography-mapping-v1.json` exists to replace.

It also said what would change that: *"a page stating only that the stamps are
monotonic and non-repeating answers H-32 alone, and unblocks every within-stream
sequential derivation without anyone asserting UTC."*

Mission 1.12 went and looked.

---

## Decision 1 — H-32 is closed for the WEB-NGRAM 1gram/2gram stream

Three first-party artifacts, retrieved 2026-08-30 and set out in full in
`gdelt-web-ngram-temporal-evidence-v1.md` §2:

- **GDELT orders this column itself.** Its published analysis over
  `gdelt-bq.gdeltv2.web_1grams` reads `SUBSTR(CAST(DATE AS STRING), 0, 8)` as a
  calendar day and `ORDER BY DATE ASC` to chart a nine-month series. That is the
  publisher decomposing and ordering the column, on this exact table.
- **GDELT sequences its own directory by the label.** `MASTERFILELIST.TXT` is
  published in ascending label order at **15-minute resolution**, from
  `20190101000000` to the current bucket — 61.7 MB of entries, read bounded at
  both ends.
- **GDELT calls the maximal label the newest.** `LASTUPDATE.TXT`, retrieved in
  the same minute, names exactly the last entry of `MASTERFILELIST`.

The daylight-saving objection ADR-020 raised is answered by those artifacts
rather than argued away: a wall-clock frame with a fall-back hour would repeat a
label, the label is the filename in one flat directory, and the index is
strictly ascending across 7.6 years. It would also break the "newest = largest"
invariant `LASTUPDATE` is built on.

**This is not a rule about `YYYYMMDDHHMMSS` strings.** It is a finding about one
publisher's one stream, and §Decision 3 is what keeps it that way.

### Cost accepted

The evidence is GDELT's own *usage and index structure* rather than a sentence
saying "these are monotonic". Mission 1.12 §6 authorises that evidence class
explicitly, and it is the strongest form available: a publisher's own ordering of
its own directory is a stronger statement about the data than a sentence about
it would be. If GDELT ever republished the directory in a non-monotonic frame,
every artifact above would have to change with it.

---

## Decision 2 — closing H-32 grants no timezone, and H-29 stays open

`SOURCE_RELATIVE_ORDER` is granted. `COMPARABLE_INSTANT` is not. Nothing
retrieved says which clock the labels are on.

**GDELT does document UTC — for a different dataset.** Web News NGrams 3.0
(`gdeltv3/webngrams/`, table `gdelt-bq.gdeltv2.webngrams`) states "the date
represented as 'YYYYMMDDHHMMSS' in the UTC timezone", and its `date` means "the
JSON timestamp **when the article was seen**". Ours (`gdeltv3/web/ngrams/`, table
`gdelt-bq.gdeltv2.web_1grams`) is the **15-minute bucket the counts aggregate**.
Different path, different table, different format, different cadence, different
meaning. A timezone documented for one says nothing about the other, and the 3.0
announcement never mentions `gdeltv3/web/ngrams` at all.

A single timing observation against the CDN's `last-modified` header was
available and was **refused**: it measures a Google Cloud Storage object's write
time against this machine's clock, it is one sample, and "equal to UTC on 30
August" is not "UTC".

So the two GDELT normalized records keep `timezone_state = NOT_ESTABLISHED` and
`observed_at = NULL`, and no ordered window may carry bounds.

### Cost accepted

Cross-source temporal alignment stays blocked, and `observed_at` stays null for
every GDELT record. That is the same cost ADR-019 accepted and it has not moved.

---

## Decision 3 — a certification names its stream, and never a label shape

`ORDER_ESTABLISHED_WITHOUT_TIMEZONE` stops being a map keyed on `source_id` and
becomes a tuple of `TemporalOrderCertification` records. Each states:

```text
source_id · resource_ids · label_scheme · review_version · basis · scope
```

**`resource_ids` is a named set, never a prefix.** The WEB-NGRAM directory also
publishes a `chargram` file per bucket that the announcement never documents and
no review has assessed — a prefix match on `web-ngrams/` would have covered it
silently. Naming the two reviewed resources is what stops that.

This required one model change: `ObservationInput` now carries `resource_id`.
`source_id` alone could not express the scope §11 requires, so a future GDELT
dataset would have inherited the WEB-NGRAM finding. The default is `None` and
that default is a **refusal** — an observation that cannot say which stream it
came from claims no stream's certification.

`resource_id` is lineage, not identity: it is recorded per input and enters no
fingerprint. All five stored signals reproduce their identity byte-for-byte
under the changed model, verified by recomputation.

### Cost accepted

A certification is more work to add than a dictionary entry, deliberately. Every
field is one a reviewer has to fill in, and `basis` and `resource_ids` are
refused empty by the constructor.

---

## Consequences

**Positive**

- Sequential WEB-NGRAM derivation becomes *temporally permitted*: pairwise
  frequency comparison, `INCREASING`/`DECREASING`, adjacent buckets, rolling
  windows, within-source momentum.
- The ORDER/INSTANT split proved to be the right shape. It cost nothing to
  carry and it is what let one question close without the other.
- H-31 was answered and refined on the way past: dataset coverage (2019-01-01,
  documented) is a different question from current directory extent
  (`20190101000000`, observed), and the second is an observation rather than a
  retention guarantee.

**Negative, and accepted**

- **Temporally permitted is not extractor specified.** Nothing was implemented.
  A sequential extractor still needs window sizes, gap handling and a decision
  about missing buckets, and none of those is decided here.
- The finding rests on artifacts that could change. It is dated, its retrieval
  method is recorded, and it names review version 3.

**Neutral**

- No production signal was created and no existing row changed. The lexical
  extractor requires `SOURCE_PERIOD_LABEL`, not ordering, so the one real
  GDELT signal is bit-identical and stays `SAME_PERIOD_LABEL` /
  `NOT_APPLICABLE`.
- H-30 is untouched. Exact source-language equality remains the permitted scope.
