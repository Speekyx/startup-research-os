# Mission 1.15.8 — TED-EU Raw → Normalized V1

**Sprint 1.** Three real TED notices are now canonical records. **Nothing
downstream of normalization exists for TED**, and that is the mission's stop
condition rather than an omission.

**H-36A remains `NOT ESTABLISHED`. H-36B remains `NOT ADDRESSED`.** Two new open
questions are recorded: **H-37** (what a TED publication-date offset means) and
**H-38** (whether monetary arrays are positionally aligned).

---

## 1. What the records actually contained

The three RawRecords were read before anything was designed, and two facts in
them were not in the 1.15.7 report:

- **`total-value` arrives as a JSON number and reaches normalization as a
  `Decimal`.** `read_raw_records` reads `payload::text` and parses with
  `parse_float=Decimal`, so the raw→normalized boundary was already lossless.
  `73415.22` survives the whole path exactly, verified on the real row;
- **`publication-date` is `2023-03-01+01:00`** — a calendar day carrying a UTC
  offset and **no time of day**. This is the mission's hardest question and §5
  below is the answer.

Also observed: `notice-identifier` and `notice-version` were requested and **not
returned** for any of the three; only 8 of 24 requested fields came back plus the
`links` block, because TED omits a field entirely when a notice has no value.

## 2. A finding, recorded and not fixed

**`ted-search-api@1.0.0` parses its response with plain `json.loads`**, not
`json.loads(..., parse_float=Decimal)` as the World Bank collector does and as
the manifest's own invariant states.

Its practical effect is bounded — `jsonb` stores the decimal literal and float64
round-trips it for the magnitudes TED publishes, and `73415.22` is intact — but
the invariant is categorical.

Not fixed here: it is a **collector** defect, changing it changes payload content
for the same source data and so requires a version bump and a re-collection,
and §36 says not to fetch more records. The raw→normalized path is exact
regardless, and the normalizer **refuses a raw float rather than rounding it**,
which is asserted by test.

## 3. The third record kind

`procurement_notice`, seeded by **migration 0022** — one vocabulary row, no
schema change, the mechanism migration 0011 established. Justified: the
`record_kind_id` foreign key refuses an unregistered kind, and
`validate_normalization.py` asserts code and migration cannot drift.

**Why a third kind rather than a wider existing one.** A procurement notice is
neither a measured metric nor a counted term. Widening `numeric_observation`
would give a World Bank population figure an award status and a currency;
widening `lexical_frequency_observation` would give a GDELT term a buyer.

**It has no `observation.value`, deliberately.** A notice has no single
measurement; its amounts are a LIST of typed entries. A required scalar would
have forced exactly the flattening the kind exists to avoid.

Three `NormalizationQualityReason` members were added to the closed contract
vocabulary — `MONETARY_PAIRING_NOT_ESTABLISHED`, `MONETARY_CURRENCY_ABSENT`,
`PERSONAL_DATA_FIELD_NOT_PROMOTED` — because each is a meaning a consumer
branches on rather than a message somebody may reword.

## 4. Cardinality, and lots

**One notice, one record.** Lots are parallel sequences in source order on that
record. A per-lot record would invent an identity the source does not have and
make one publication read as several — and a downstream count of procurements
would be a count of lots.

`["11000", "22000", "33000"]` stays three amounts.

## 5. Temporal — `observed_at` is NULL, and why

```text
value        2023-03-01+01:00     a DAY, an offset, and NO time of day
period       DAY, bounds NAIVE, timezone_state NOT_ESTABLISHED
observed_at  NULL
preserved    source value and offset, verbatim, on every record
```

**`ESTABLISHED` was considered and refused**, and the case for it was real: the
offset is *in the value*, which is more than GDELT had and more than a World Bank
year label has — that one is `ESTABLISHED` with an invented `+00:00`.

Refused for two reasons:

**The state's definition is not satisfied.** `ESTABLISHED` means *"the source
states the timezone, or authoritative documentation does"*. Neither has. An
offset inside one value is **data**; it is not a statement about whether it is
the authoritative publication zone or an artefact of how the API renders a date,
and the OpenAPI document describes the field with no temporal semantics. GDELT
needed a `TemporalOrderCertification` — evidence — to establish an ordering its
labels already implied.

**And there is no time of day under any reading.** Even with the offset taken as
authoritative, an instant must still be chosen from within the day. Midnight is
the choice that looks like no choice.

> **H-37.** What the offset in a TED publication date means. The source value is
> on every record, so closing it is a re-derivation over records already held,
> not a re-collection.

**Award and contract dates** are kept as the source's own strings, not parsed
into a canonical temporal shape — the same open question, on fields no real
record has yet carried.

## 6. Money

| `amount_type` | Source field | Scope |
|---|---|---|
| `TOTAL_VALUE` | `total-value` | NOTICE |
| `TENDER_VALUE` | `tender-value` | LOT |
| `ESTIMATED_VALUE` | `estimated-value-lot` | LOT |
| `FRAMEWORK_MAXIMUM` | `framework-maximum-value-lot` | LOT |

**No `price_paid`, no `contract_value`, no `generic_amount`** — asserted over the
AST by the test suite and again by the validator. An amount whose semantic is not
in the vocabulary **cannot be constructed**: `CanonicalMonetaryAmount` raises.

**Arrays are not paired by index.** TED declares both amounts and currencies as
arrays and states nothing about correspondence, so `pairing` is `ESTABLISHED`
only where there is one of each; otherwise both sequences are preserved unpaired
with a reason saying so (**H-38**).

**No currency converted.** `["EUR", "EUR", "SEK"]` keeps SEK. Amounts are exact
decimal strings end to end.

## 7. Answers

| Question | Answer |
|---|---|
| TED RawRecords at start? | **3** |
| Normalizer id/version? | **`ted-search-api-notice@1.0.0`** |
| Lineage accepted? | source `ted-eu`, collector `ted-search-api` `{1.0.0}`, resource `notices/eforms-contract-and-award`, family `ted-search-api-notices` |
| Normalized identity? | `publication-number` (+ identifier/version where published); canonical id is the model's own tuple |
| Cardinality? | **1 notice → 1 record** |
| Lots exploded? | **No** — structured sequences on the record |
| Notice types preserved? | both `class` and `source_type`, always |
| What does `publication-date` mean? | a calendar **day** with an offset and no time of day |
| Promoted to `observed_at`? | **No** |
| What remains unresolved? | **H-37** — §5 |
| Award/contract dates? | source strings, verbatim, kept distinct from publication |
| Multilingual names? | every language, keyed by tag, deterministic order |
| One language selected? | **No**, and there is no `display` field |
| Buyers? | organisation-level, multilingual, multiplicity preserved |
| Suppliers/tenderers? | a distinct role, same representation |
| Tenderer read as awarded supplier? | **Never** — only `award.selection_status` speaks to an outcome |
| CPV? | code + scheme, no label invented, no sector inferred |
| Lots? | parallel sequences in source order; nothing sorted |
| Four monetary semantics? | four typed entries, own names, own scopes |
| Any flattened? | **No** |
| `price_paid` created? | **No** |
| Amount/currency arrays? | preserved; paired only at one-and-one (H-38) |
| Currency converted? | **No** |
| Numeric representation? | `Decimal`, canonical decimal **strings**; a raw float is refused |
| Amount type preserved? | required — an entry cannot exist without one |
| Award status? | the source's value, never inferred |
| Country/region? | source codes, `ted-source-code`, no geocoding |
| `links`? | **not copied**; two references kept, raw remains source of truth |
| Natural-person fields promoted? | **No**, and an arrival is recorded as a refusal |
| Authenticity claim? | *TED reported ...*, never independent verification |
| Provenance? | raw id, source, resource, collector, normalizer, schema, review, correlation, timestamps |
| Idempotent? | **Yes** — second run: 0 new, 0 revised |
| Changed raw revision? | existing revision semantics; nothing TED-specific invented |
| Optional absence vs drift? | one required field; absence is normal, a changed shape is refused |
| Migration required? | **Yes** — 0022, one vocabulary row, justified in §3 |
| World Bank / GDELT changed? | **No** |
| Gateway defect changed? | **No** — still recorded as backlog |
| Fixtures extended? | yes, a `links` fixture; the rest reused |
| Validation updated? | yes — a TED block in `validate_normalization.py` |
| All tests/gates pass? | **Yes** — §9 |
| Real records normalized? | **3** |
| TED NormalizedRecords now? | **3** |
| New RawRecords fetched? | **None** |
| Signals created? | **None** |
| Claims/Evidence created? | **None** |
| Opportunities/embeddings/scores? | **None** |

## 8. Local counts

| | before | after |
|---|---|---|
| `raw_records` | 15 | **15** |
| — TED | 3 | **3** |
| `normalized_records` | 12 | **15** |
| — TED | 0 | **3** |
| `nlp.signals` | 7 | 7 |
| `research.claims` / `claim_revisions` | 7 / 7 | 7 / 7 |
| `scoring.evidence` | 7 | 7 |
| `research.opportunities` | 0 | 0 |
| `epistemic.reliability_assessments` | 0 | 0 |
| `nlp.embedding_provenance` | 0 | 0 |
| human decision rows | 1 | **1** |

All three TED records are `PARTIAL`, each carrying
`PERIOD_TIMEZONE_NOT_ESTABLISHED`. `VALID` is unreachable for this adapter until
H-37 closes, which is honest rather than unfortunate.

Run through `run_normalization_job` — the production path — so normalizer
selection, provenance, transaction semantics, idempotency and RLS all applied.
No one-off script bypassed any of it.

## 9. Validation

| Check | Result |
|---|---|
| zero-dependency suites | 515 tests across 8 packages |
| pytest suites | 7 packages; acquisition 1 385 + 11 skipped |
| seven validators | all OK, including the new TED block |
| contract generation `--check` | current |
| all five generator `--check` steps | current (see §9.1) |
| `ruff check` / `format --check` | clean, 446 files |
| `mypy` | no issues |
| env-template secret check · `assert_registry_grants_nothing` | OK |

**74 new tests** in `test_ted_normalization.py`, no network and no database.
**Nineteen existing guards were inverted across two passes** — first the
"no TED normalizer" claims, then the database-count ones — and §56 of
`testing-strategy.md` records what replaced the counts: an assertion about the
stage nobody has built, which does not expire when the pipeline advances.

## 9.1 A mistake CI caught, and where the fact belongs instead

`docs/data/source-signal-coverage-v1.md` was amended by hand to say that TED is
normalized and still produces no Signal. **It is a GENERATED file**, rendered
from the catalog by `render_signal_coverage.py`, and `--check` failed on CI while
every local gate passed — because the five generator checks are separate CI steps
and only one of them had been run locally.

The edit was reverted rather than regenerated around. Two hand-maintained copies
of one fact drift, and the drift is discovered by whoever trusted the wrong one
(ADR-009, applied to documentation).

**The fact still needed a home**, and it has two that are not generated:
`ted-eu-normalization-v1.md` §18 and §11 of this report. Coverage says what a
source COULD expose; it is derived from the catalog and says nothing about what
has been built, which is exactly why it could not carry this.

All five generator checks now run together locally:
`generate.py`, `sros-source render`, `render_review_results.py`,
`render_signal_coverage.py` and `sros_evidence_aggregation.sensitivity`.

## 10. Final state

| | |
|---|---|
| SOURCE AUTHORIZATION | **yes** |
| RESOURCE READY | **yes** |
| COLLECTOR IMPLEMENTED | **yes** |
| RAW DATA ACQUIRED | **yes — 3** |
| NORMALIZER READY | **yes** |
| NORMALIZED DATA AVAILABLE | **yes — 3, all PARTIAL** |
| SIGNALS READY | **no** |

## 11. Next

**Sprint 1 — Mission 1.15.9, TED Transaction Signal Extraction V1**, and it
starts against two constraints this mission recorded rather than resolved:

- a Signal is a **derivation over two or more observations**, and a normalized
  notice is one document. What two TED notices can be compared *for* is the
  design question, and "an award happened" is not a comparison;
- **H-37 blocks anything temporal.** TED periods carry naive bounds and no
  `observed_at`, so no two notices can be ordered on a shared timeline. A
  frequency, a trend or a change over time needs H-37 closed first — with
  evidence, the way Mission 1.12 closed H-32.

A `WILLINGNESS_TO_PAY` signal as a **transaction** is what the portfolio has been
missing since Mission 1.15, and the material for it now exists in canonical form
for the first time. It is still not a Signal.
