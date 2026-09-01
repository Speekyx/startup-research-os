# TED-EU Normalization V1

**Authoritative.** Mission 1.15.8. How a TED Search API notice becomes a
canonical record, and the four things this layer refuses to decide.

**State: three real TED notices normalized.** `ted-search-api-notice@1.0.0`,
record kind `procurement_notice`, all three `PARTIAL`. **No Signal, no Claim, no
Evidence, no Opportunity, no embedding, no score.** H-36A and H-36B are
untouched.

---

## 1. Scope

| | |
|---|---|
| Normalizer | **`ted-search-api-notice@1.0.0`** |
| Source | `ted-eu` |
| Collector | `ted-search-api`, versions `{1.0.0}` |
| Resource | `notices/eforms-contract-and-award`, and no other |
| Dataset family | `ted-search-api-notices` |
| Record kind | **`procurement_notice`** (migration 0022) |
| Notice types | `cn-standard`, `can-standard` |

**Lineage is checked against the RECORD, not inferred from the registry key.**
The registry answers *which adapter serves this source and collector*; the
adapter answers *is this particular record the thing I parse*. A bulk XML
package, an ODS result or an unreviewed TED resource is refused here as well as
at acquisition, because a raw record can outlive the configuration that produced
it.

## 2. Cardinality

**One notice, one record. Lots are structured data on it.**

TED publishes one notice under one publication number. A per-lot record would
invent an identity the source does not have and make one publication read as
several — and a downstream count of "procurements" would be a count of lots
wearing a notice's name.

The lot-level facts survive as parallel sequences in source order:
classifications, places, tender values, selection statuses. **Position is the
only thing relating one lot entry to another**, so nothing sorts them.

## 3. Identity

`publication-number`, plus `notice-identifier` and `notice-version` **where the
source publishes them**. Never array position, page, result order, a buyer name
or an amount.

All three real notices published neither identifier nor version, so both are
`null` — a placeholder would make two different notices look alike.

Canonical identity is the model's own: `(workspace, raw_record_id, schema
version, normalizer id, normalizer version)`. Nothing TED-specific was invented.

## 4. Notice type — both, always

```json
"notice": {"class": "CONTRACT_AWARD_NOTICE", "source_type": "can-standard",
           "source_type_scheme": "ted-notice-type"}
```

| Source type | Class |
|---|---|
| `cn-standard` | `CONTRACT_NOTICE` |
| `can-standard` | `CONTRACT_AWARD_NOTICE` |

**A normalized class alone** loses which vocabulary produced it. **A source type
alone** makes every consumer learn TED's spelling. Both, and the mapping is a
table so a reader can check it rather than deduce it. A notice type outside the
resource is **refused**, not classified.

## 5. Temporal — the mission's hardest question

**The value:**

```text
publication-date = "2023-03-01+01:00"
```

A calendar **day**, carrying a UTC offset, with **no time of day**.

**The answer:**

| | |
|---|---|
| Period type | `DAY` |
| Bounds | `2023-03-01T00:00:00` → `2023-03-02T00:00:00`, **naive** |
| `timezone_state` | **`NOT_ESTABLISHED`** |
| `observed_at` | **NULL** |
| Source value | preserved verbatim, with its offset, in `publication` |

### 5.1 Why not `ESTABLISHED`

It was considered, and the case for it is real: the offset is *in the value*,
which is more than GDELT had (nothing) and more than a World Bank year label has
(no offset at all, and its period is `ESTABLISHED` with an invented `+00:00`).

It was refused for two reasons.

**The state's own definition is not satisfied.** `ESTABLISHED` means *"the
source states the timezone, or authoritative documentation does"*. Neither has.
An offset appearing inside one value is **data**; it is not a statement about
what that offset means — whether it is the authoritative publication zone or an
artefact of how the API renders a date. The Search API's OpenAPI document
describes `publication-date` with no temporal semantics at all. GDELT needed a
`TemporalOrderCertification` — **evidence** — to establish an ordering its
labels already implied, and the same standard applies here.

**And there is no time of day under any reading.** Even with the offset taken as
authoritative, an instant would still have to be chosen from within the day.
Midnight is the choice that looks like no choice.

### 5.2 What that costs, and what it preserves

Costs: TED notices cannot be placed on a shared timeline with other sources
until H-37 closes, so no cross-source temporal Signal can use them.

Preserves: the source value and its offset are on every record, so **closing
H-37 is a re-derivation over records already held, not a re-collection**.

> **H-37 — what does the offset in a TED publication date mean?** Is it the
> authoritative publication timezone for the OJ S, a fixed offset, or a
> rendering artefact? First-party documentation states nothing. Closing it needs
> evidence — the Publications Office's own statement, or a documented pattern
> across summer and winter publications — not inference.

### 5.3 Award and contract dates

Three date concepts, never merged:

| Concept | Source field | Representation |
|---|---|---|
| publication | `publication-date` | the canonical period |
| award decision | `winner-decision-date` | source strings, verbatim |
| contract conclusion | `contract-conclusion-date` | source strings, verbatim |

The last two are **not parsed into a canonical temporal shape**, because doing so
would imply semantics nobody has established for them either — the same question
as H-37, on fields no real record has yet carried. They are preserved as the
source wrote them, so the mission that establishes their semantics has the
material.

## 6. Multilingual values

TED returns organisation names keyed by language and the Search API request
carries **no language selector**, so there is no source-supported preference to
apply.

```json
"buyer": {"scheme": "ted-language-code",
          "by_language": {"eng": ["Example Public Buyer"], "fra": ["Acheteur Public"]},
          "language_tags": ["eng", "fra"]}
```

**Every language is kept. There is no `display` field, and its absence is the
design** — a canonical display value would be read as *the* name by everything
downstream, and the rule that produced it would live in code rather than where a
reader can see it. A consumer that needs one language asks for it by tag.

Ordering is by language tag, so serialisation is deterministic and the content
fingerprint does not depend on dictionary order. **Nothing is translated.** A
shape the schema does not declare is **drift**, not a string.

## 7. Buyers and suppliers

Buyer and tenderer are **distinct roles**, both organisation-level, both
multilingual, both allowed to carry several entries. Nothing is concatenated.

**A tenderer is never read as an awarded supplier.** Only
`award.selection_status` speaks to an outcome, and it is the source's own value —
never inferred from the presence of an amount or an organisation. A contract
notice legitimately has no tenderer, and the absence is valid rather than
missing.

The payload contains no `supplier`, `winner` or `awarded_supplier` key, asserted
by test.

## 8. Classification, country and region

CPV codes are **identifiers with their scheme**, and nothing more:

```json
{"code": "90911200", "scheme": "CPV", "label": null}
```

No market category, no sector, no SaaS/IT inference, no roll-up. A taxonomy
mapping is a reviewed act and belongs to the mission that does it.

Countries and NUTS subdivisions are kept as the source's codes under
`scheme: "ted-source-code"`. **No geocoding**, no inference from an organisation
name, no external call.

## 9. Money — the highest-priority invariant

**Four source fields, four meanings, four typed entries. Never one number.**

| `amount_type` | Source field | Scope | What it is |
|---|---|---|---|
| `TOTAL_VALUE` | `total-value` | NOTICE | eForms **BT-161**: *"the value of all contracts awarded in this notice, **including options and renewals**"*. Not what was paid, and not necessarily what will be (Mission 1.15.12) |
| `TENDER_VALUE` | `tender-value` | LOT | the value of a tender |
| `ESTIMATED_VALUE` | `estimated-value-lot` | LOT | an estimate, **not** what anybody paid |
| `FRAMEWORK_MAXIMUM` | `framework-maximum-value-lot` | LOT | a ceiling, **not** a transaction |

```json
{"amount_type": "TOTAL_VALUE", "source_field": "total-value", "scope": "NOTICE",
 "amounts": ["73415.22"], "currencies": ["EUR"],
 "currency_source_field": "total-value-cur", "pairing": "ESTABLISHED"}
```

- **`price_paid` does not exist**, and neither does `contract_value`,
  `generic_amount` or `amount_eur`. Asserted over the AST by the test suite and
  again by `validate_normalization.py`.
- **An amount whose semantic is not in the vocabulary cannot be constructed.**
  `CanonicalMonetaryAmount` raises. An amount whose meaning is unknown is the
  flattening this design exists to prevent, wearing a different name.
- **An absent monetary block produces no entry.** Absent is not zero: a contract
  notice has no total value because no award has happened.
- **The vocabulary is not a domain enum**, deliberately. These are SOURCE
  semantics for one field set. A cross-source `AmountType` would have to claim a
  TED framework maximum and some future source's budget ceiling are the same
  concept, and nothing has established that.

### 9.1 Arrays, and why they are not paired

TED declares amounts and currencies as **arrays** and states **nothing** about
positional correspondence.

| Shape | `pairing` |
|---|---|
| one amount, one currency | **`ESTABLISHED`** — there is nothing to decide |
| anything else | **`NOT_ESTABLISHED`** — both sequences preserved whole, unpaired |

Pairing by index would be a reading of the source presented as the source's own
statement. A three-lot notice keeps `["11000", "22000", "33000"]` and
`["EUR", "EUR", "SEK"]` side by side, and a `MONETARY_PAIRING_NOT_ESTABLISHED`
reason says why they are not zipped.

> **H-38 — does index *i* of a TED monetary array correspond to index *i* of its
> currency array?** The schema does not say. Closing it needs a first-party
> statement, not an inspection of records that happen to agree.

### 9.2 Currency and precision

**No conversion. No EUR normalisation.** No rate, no table, no arithmetic on an
amount — asserted over the AST.

Amounts are **exact decimals**, end to end: the raw payload is read back from
`jsonb` as text and parsed with `parse_float=Decimal`, the model's `decimal_from`
never routes through a binary float, and the canonical form is a decimal
**string**. A raw Python float reaching the adapter is **refused rather than
rounded** — silently accepting one would put a binary approximation into the
figure that says what a public contract was worth. `73415.22` survives the whole
path unchanged, on real data.

## 10. Missing fields versus drift

**Exactly one field per notice is required by the source contract**
(`publication-number`), and TED **omits a field entirely** when a notice has no
value for it. So:

| Situation | Outcome |
|---|---|
| no monetary block, no supplier, no award date | **normal**, no entry, no reason |
| `publication-number` absent | **refused** — no identity may be invented |
| `publication-date` absent | **refused** — dating it by collection time would date the notice by when we fetched it |
| a known field's shape changed | **refused as drift**, named as a contract change |
| notice type outside the resource | **refused** |

## 11. `links`

TED attaches a `links` object to every notice regardless of the field selection —
~94% of a raw record's bytes, in 24 languages and five formats.

**It is not copied.** Two references are kept (`html`, `xml`, English where
published) and the RawRecord remains the source of truth for the whole block.
A normalized record is ~1.4 KB against a ~4.8 KB raw one.

## 12. Personal data

No natural-person field was requested and none has been received.

**Nothing here can promote one**: every field the adapter reads is named
explicitly, so there is no branch that could. If one ever arrives, the record
carries `PERSONAL_DATA_FIELD_NOT_PROMOTED` naming the keys — a refusal a reader
can see beats an absence nobody can distinguish from the source never sending it.

## 13. Authenticity

A normalized notice supports **"TED reported that ..."** and nothing stronger. It
is not independent verification that the procurement occurred as described. The
rendered attribution travels on every record, read from the raw record's own
provenance; a raw record carrying none is refused rather than normalized into a
row with no credit attached.

## 14. Provenance

Raw record id, source, resource, dataset family, collector id and version,
normalizer id and version, schema id and version, review version, correlation
id, `collected_at`, `normalized_at`, `expires_at`, content hash, quality state
and reasons. Nothing is duplicated that the relationship already provides.

**Retention** is the platform baseline resolved by governance — there is no
retention parameter in this adapter to pass, so nothing here can widen it.

## 15. Quality

**Every TED record is `PARTIAL`, by construction**, because every one carries
`PERIOD_TIMEZONE_NOT_ESTABLISHED` — H-37 is open for all of them rather than for
unlucky ones. That is honest rather than unfortunate: the alternative is a record
that reads as complete with an open question inside its period. `VALID` becomes
reachable when H-37 closes.

`INVALID` is unreachable here: a record missing something the kind requires
raises instead, so a draft that exists has its required fields.

## 16. Idempotency

Re-running over unchanged raw records produces **0 new, 0 revised**. A changed
raw record follows the existing revision semantics; nothing TED-specific was
invented.

## 17. Open questions

| | |
|---|---|
| **H-37** | what the offset in a TED publication date means (§5.2) |
| **H-38** | whether TED monetary arrays are positionally aligned with their currency arrays (§9.1) |
| H-36A | still `NOT ESTABLISHED` — untouched here |
| H-36B | still `NOT ADDRESSED` — untouched here |

## 18. What does not exist

No TED Signal, Claim, ClaimRevision, Evidence, ReliabilityAssessment,
Opportunity, embedding or score. **Normalization is the last stage this mission
built**, and a normalized procurement notice is not a transaction, a price or a
demand signal — it is what a public body published.
