# World Bank Normalizer V1

**Status:** Authoritative. Created in Mission 1.6, the first normalizer.
**Version:** `world-bank-indicators-numeric@1.0.0`, writing canonical schema
`sros.normalized-record/1`
**Date:** 2026-08-30
**Governs:** how a World Bank indicator observation becomes a canonical numeric
observation — and, by example, how every later adapter is built.
**Related:** [`normalized-record-v1.md`](normalized-record-v1.md),
[`normalized-record-gap-analysis-v1.md`](normalized-record-gap-analysis-v1.md),
[`world-bank-collector-v1.md`](world-bank-collector-v1.md),
[`geography-mapping-v1.json`](geography-mapping-v1.json),
[`data-retention-policy-v1.md`](data-retention-policy-v1.md).

---

## 0. What this normalizer may do, and how that was decided

Nothing here decides anything about World Bank policy or about what the data
means. Mission 1.3 reviewed the licensing, Mission 1.4 built the capabilities its
conditions require, Mission 1.5 collected six observations under an
authorization. This adapter reads those records and reshapes them.

    Mission 1.3   the review, and three conditions
    Mission 1.4   the capabilities, and an AcquisitionAuthorizationContext
    Mission 1.5   a collector that cannot run without one
    Mission 1.6   an adapter that reads what it wrote, and interprets nothing

---

## 1. The four rules

**It reaches nothing.** No socket, no metadata fetch, no model. Everything it
needs is already persisted or is reviewed local configuration, and CI asserts it
by parsing every import in the package rather than by trusting this sentence.
That guard was checked against fourteen deliberate violations before being
believed.

**It is selected, never assumed.** `(source_id, collector_id)` selects an
adapter and an unregistered pair is refused. The collector version is checked
too: this adapter declares `1.0.0` and refuses anything else, because a parse
that half-works on an unknown payload shape is worse than one that stops.

**It interprets nothing.** A unit the endpoint does not publish stays
`NOT_PUBLISHED`. A geography code with no reviewed entry stays `UNKNOWN`. A value
the source did not report stays `NOT_REPORTED` and is never zero. Each is a state
a consumer can branch on, which is strictly more useful than a plausible value
nobody can check.

**Retention and attribution come from governance.** `build_normalized` has no
parameter for either, so there is nothing to pass. A raw record carrying no
attribution obligation is refused rather than normalized into a row with no
credit attached.

---

## 2. Scope

One record kind: `numeric_observation`. One source: `world-bank`. One collector:
`world-bank-indicators@1.0.0`.

The three authorized indicator series are annual, so **the only period form this
adapter represents is a four-digit year**. A quarterly or monthly code is
reported as `PERIOD_NOT_SUPPORTED` and renders the record `INVALID` rather than
being approximated — inventing an exact date the source did not give is how
January 1 becomes an event time.

---

## 3. The mapping

| Source field (raw payload) | Canonical field | Rule |
|---|---|---|
| `indicator` | `metric.id` | Verbatim. Absent → `METRIC_MISSING`, `INVALID` |
| — | `metric.name` | **Always `null`.** The Indicators API response carries no label, and deriving one from the code would be inference |
| — | `metric.scheme` | `world-bank-indicator` |
| `value` | `observation.value` | Exact decimal, as a string. See §4 |
| `value` | `observation.value_state` | `REPORTED` / `NOT_REPORTED` / `UNREADABLE` |
| `unit` | `observation.unit` | Verbatim where present, which on this endpoint is never |
| — | `observation.unit_state` | `NOT_PUBLISHED`. Never inferred from the metric id |
| `decimals` | `observation.decimals` | Verbatim. This is where the source states precision |
| `period` | `period` | A four-digit year → `[Jan 1, next Jan 1)` with `type` and `label` |
| `geography` | `geography.source_code` | Verbatim, always |
| `geography_name` | `geography.source_name` | Verbatim where present |
| `geography` + reviewed map | `geography.kind`, `.canonical_code` | See §5 |
| `provenance.dataset_family` | `series.dataset` | From the raw record's provenance |
| `resource_id` | `series.resource_id` | Verbatim |
| — | `series.frequency` | `ANNUAL`, from the review, not read off the period |
| `source_last_updated` | `series.source_last_updated` | Verbatim |

---

## 4. Numeric precision, and a finding

The value is an exact `Decimal` in Python and an exact decimal **string** in the
canonical payload. It is parsed from the raw payload's JSON *text* with
`parse_float=Decimal`, never from an already-parsed float.

`(payload -> 'observation' ->> 'value')::numeric` casts it back to PostgreSQL
`NUMERIC` exactly, so nothing is given up by not storing a number — which is why
there is no separate numeric column.

### The finding: the raw layer is the real precision boundary

Running this against the six real records surfaced something reasoning about it
had not. The Mission 1.5 collector parses a value with `float(...)`, so the World
Bank integer `82905782` reaches the raw payload as `82905782.0`.

Two consequences, and they differ in severity:

- **The trailing `.0` is an artifact and is stripped.** `canonical_decimal_text`
  removes trailing fractional zeros, so the canonical form is `82905782`. Not
  cosmetic: the day a collector version stops using `float`, every
  re-normalization would otherwise produce a different fingerprint for identical
  source data — a revision that did not happen, which is what §22 exists to
  prevent. Precision is not lost, because the source states it separately in
  `decimals`.
- **A value that float64 cannot represent exactly is already damaged before this
  adapter sees it.** For population counts it is not: integers below 2^53 survive
  a float round-trip exactly, so the six real records are unaffected. For a rate
  or a ratio it would be, and **normalization cannot recover what the raw layer
  lost.** This is recorded in §9 as open work belonging to the collector.

---

## 5. Geography

Classification comes from [`geography-mapping-v1.json`](geography-mapping-v1.json)
and from nothing else.

The problem is that a code does not say what it is: the Indicators API returns
`FRA` for France and `WLD` for the world in the same field, both three uppercase
letters. Any rule based on the string's shape is wrong for one of them, and
mapping the wrong one produces "the population of the country World". Classifying
from the accompanying label is inference, which §41 forbids reaching for a model
to do and which a hand-written string match does no better.

So it is reviewed data, one entry per code, each carrying a `basis` — the same
discipline the authorized dataset list is under.

| | |
|---|---|
| Entries today | **two**: `FRA → FR`, `DEU → DE`, on the ISO 3166-1 alpha-3/alpha-2 assignment |
| An unmapped code | `kind: UNKNOWN`, no canonical code, record `PARTIAL` with `GEOGRAPHY_NOT_CLASSIFIED` |
| An aggregate | `kind: AGGREGATE`, source code preserved, **never** a canonical country code |

**No aggregate entry is seeded**, and that is deliberate rather than an
oversight. The `AGGREGATE` kind exists, is reachable and is exercised by the test
suite against a fixture map — but classifying a real World Bank aggregate
requires evidence this mission did not retrieve, and writing one down from recall
is exactly what the file exists to prevent. Until a reviewer establishes them,
aggregates land in `UNKNOWN`, which preserves the property §15 actually protects:
**an aggregate is never mistaken for a country.**

---

## 6. Quality

| Outcome | State | Reason |
|---|---|---|
| Everything present and well-formed | `VALID` | — |
| The source published no figure | `PARTIAL` | `VALUE_NOT_REPORTED` |
| The value could not be read as a decimal | `PARTIAL` | `MALFORMED_NUMERIC_VALUE` |
| The geography code is not in the reviewed map | `PARTIAL` | `GEOGRAPHY_NOT_CLASSIFIED` |
| No geography at all | `INVALID` | `GEOGRAPHY_MISSING` |
| No indicator | `INVALID` | `METRIC_MISSING` |
| A period this adapter does not represent | `INVALID` | `PERIOD_NOT_SUPPORTED` |

A unit the endpoint does not publish is **not** a quality reason. It would apply
to every record this adapter produces, and a state every record shares carries no
information.

An `INVALID` record is **stored**, not discarded (§26, §27). A raw record that
cannot be normalized is a fact someone has to be able to find, and dropping it
would make a normalizer defect look like a source that returned nothing.

---

## 7. Identity, revision and re-normalization

Full rules: [`normalized-record-v1.md`](normalized-record-v1.md) §2. In short:

```text
same raw record, same versions        UNCHANGED. Nothing is written
same raw record, other versions       a second row. Both coexist
revised raw record, same versions     a new row; the previous one is superseded
same identity, different content      CONFLICT. The stored row stands
```

The last one is the mechanism that makes a version bump necessary rather than
polite. If the same raw record under the same normalizer and schema version
produces different canonical content, either the adapter is not deterministic or
a reviewed input it reads changed without the version being bumped. Overwriting
would destroy the stored representation; inserting would need an identity that
distinguishes the two, and that identity *is* the version. So the mismatch is
reported as `NON_DETERMINISTIC_OUTPUT` and nothing is written.

**The geography map is an input to the transformation.** Changing it changes
output, so it changes the normalizer version.

---

## 8. Operating it

```bash
sros-normalize validate
```

Which sources can be normalized and by what. Reaches no network **and no
database**: selection is a property of the code and the reviewed configuration,
not of the deployment.

```bash
sros-normalize run --workspace <id> --session <id>
```

A bounded batch — at most 500 raw records, our own limit, applied whatever is
passed. Reads only records not yet normalized under this lineage.

```bash
sros-normalize run --workspace <id> --session <id> --renormalize
```

Includes records already normalized under this lineage. Existing rows still
stand; this is how a re-run is proven to write nothing.

```bash
sros-normalize history --workspace <id> --observation '<key>'
```

Every representation of one observation, newest first, across all normalizer and
schema versions. Deliberately unfiltered: the point is that several coexist and
can all be seen. Which one downstream should read is **D-08**, open.

No command accepts a payload, a URL or a document.

---

## 9. Still open

- **The raw layer's float conversion (§4).** The collector parses values with
  `float(...)`, which is exact for the integers the three authorized series carry
  and would not be for a rate. Fixing it belongs to a collector version bump and
  would change every raw `content_hash`, so it is recorded here rather than done
  quietly in a normalization mission.
- **Two geography entries.** Widening the map requires evidence per entry.
- **One record kind.** Text, document and discussion kinds arrive with the
  adapters that produce them.
- **Re-normalization selection (D-08).** Coexistence works; choosing does not
  exist, and §49 forbids inventing it.
- **One period form.** Quarterly and monthly are representable in the canonical
  model and are not implemented here, because no real record uses them.
