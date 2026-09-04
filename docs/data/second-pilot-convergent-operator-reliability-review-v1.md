# Second pilot — the completed convergent TED reliability review

**`second-pilot-convergent-operator-reliability-review@1.0.0`**, performed under **`human-reliability-assessment-rubric@1.0.0`**. Authored by the reviewer; this page is rendered from it.

**This is a completed review, not a preparation packet** — which is why it carries a number where the Mission 1.42 packet carried a blank.

It is none of these:

- NOT a calibration. REFERENCE_PROFILE_V1 remains UNCALIBRATED and this value fits no parameter.
- NOT a probability that any Claim is true.
- NOT a source-wide TED score. The scope is five fields; ted-eu alone matches nothing.
- NOT specific to CPV division 92, or to EUR, or to the second pilot. The scope carries no classification division and no currency, so this judgement binds every convergent Evidence row from this measurement.
- NOT a statement that TED's published amounts are correct. Source-side validation establishes conformance, not correctness.
- NOT independence. Observation overlap stays DISJOINT and independence stays UNKNOWN.

---

## The scope

```text
source_id         ted-eu
resource_id       notices/eforms-contract-and-award
record_kind_id    procurement_notice
claim_type        OBSERVED
proposition_kind  source_published_classification_value_contrast_witnessed
```

Exactly five fields, matched in full or not at all. The existing ted-eu assessment at 0.5 shares four of them and differs on proposition_kind, which is a different reliability question and not a baseline for this one.

It binds **6 Evidence rows across 4 Claims** — of which 2 carry more than one — spanning CPV divisions `90`, `92` and currencies `EUR`, `SEK`, because a reliability scope carries neither.

## The profile

| dimension | state |
|---|---|
| `MEASUREMENT_DEFINITION` | `PARTIALLY_DOCUMENTED` |
| `SOURCE_SIDE_VALIDATION` | `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` |
| `HISTORICAL_MUTABILITY` | `NOT_ESTABLISHED` |
| `COMPLETENESS_AND_MISSINGNESS` | `PARTIALLY_DOCUMENTED` |
| `SOURCE_SIDE_CHECKABILITY` | `DOCUMENTED_AND_BOUNDED` |

## Material unknowns

| dimension | not established | material? |
|---|---|---|
| `HISTORICAL_MUTABILITY` | whether a published BT-161 value may later be corrected, and whether a corrected notice supersedes an earlier one in the reviewed resource | **YES** |
| `MEASUREMENT_DEFINITION` | whether an assigned CPV classification may change after publication | **YES** |
| `COMPLETENESS_AND_MISSINGNESS` | how frequently notices in the reviewed classification withhold their result values | **NO** |
| `SOURCE_SIDE_CHECKABILITY` | how long a published notice remains retrievable at the source | **UNSURE** |

UNSURE is preserved as UNSURE. It is not YES, not NO, not low confidence, and not a number. The rubric permits it precisely because a reviewer who cannot yet tell whether an unknown matters has said something real, and converting it to anything else would discard that.

## Hard stops

**None triggered.** None. MEASUREMENT_DEFINITION is not NOT_ESTABLISHED, no dimension is CONTRADICTED, the proposition does not exceed the measurement, and the source observations are recoverable through lineage.

## The gate, and the judgement

**`NUMERIC_JUDGEMENT_PERMITTED`.** A human decision, taken against the profile above. The rubric defines the gate as judgement rather than an arithmetic function, and nothing here recomputes it from the ordinal states.

```text
reliability   0.55
origin        HUMAN_REVIEW
reviewer      thibchm
```

### Rationale

The reliability judgement is based on first-party TED/eForms documentation that establishes the meaning and source-side representation of the relevant reported amount, together with documented validation and withholding behaviour.

The measurement definition and completeness behaviour are only partially documented for this proposition, and source-side validation does not establish that a published amount is factually correct. The underlying source observations remain directly traceable and inspectable.

I consider the available documentary basis sufficient to permit a numeric reliability judgement, while treating the unresolved correction/supersession semantics and possible post-publication classification changes as material unknowns.

### Stated limitation

The held documentation does not establish whether a published BT-161 value or its CPV classification may later be corrected, amended, superseded, or otherwise changed in a way that affects whether an earlier cohort continues to witness the proposition. Source-side validation also establishes conformance rather than factual correctness of the reported amount. Long-term retrievability of published notices remains unresolved.

## Documentary basis

| type | document | finding |
|---|---|---|
| `MEASUREMENT_METHODOLOGY` | eForms SDK 1.15.1 business-term definitions (business-term_en.xml) (`business-term|description|BT-161`, retrieved 2026-09-01) | BT-161 is 'The value of all contracts awarded in this notice, including options and renewals'. |
| `SOURCE_DOCUMENTATION` | eForms SDK 1.15.1 field repository (fields.json) (`BT-161-NoticeResult`, retrieved 2026-09-01) | TOTAL_VALUE is BT-161, notice level, non-repeatable, at XPath efac:NoticeResult/cbc:TotalAmount, with a companion currency field. |
| `KNOWN_LIMITATION` | eForms SDK 1.15.1 business rules (rule_en.xml) (`BR-BT-00161-*`, retrieved 2026-09-01) | 60 published rules govern where BT-161 may appear. All are presence, absence or notice-type constraints; none concerns the amount's correctness. |
| `KNOWN_LIMITATION` | eForms SDK 1.15.1 business-term definitions, BT-195 to BT-198 (`business-term|description|BT-195`, retrieved 2026-09-01) | Result values, of which BT-161 is one, may be withheld from immediate publication with a justification and a later date. |

The four documents Mission 1.42 prepared, all first-party eForms SDK 1.15.1 and all already held. Nothing new was fetched, because the convergent proposition reads the same BT-161 field of the same notices and fetching to inflate a basis count is not review. Mission 1.42 classified three as REUSED and BT-195 to BT-198 as PARTIALLY_APPLICABLE -- that verdict is about how much WEIGHT the reviewer gives it under an existential proposition, not about whether the document belongs, so all four are persisted. SROS engineering validation is deliberately absent: passing tests establish that the implementation matches its specification and nothing about the dependability of TED's published amounts.

## Outcome

Persisted as assessment `d1afa4be-8462-4461-be20-112cdc55ee7e` version 1, recorded 2026-09-04T04:44:36.565929+00:00.

