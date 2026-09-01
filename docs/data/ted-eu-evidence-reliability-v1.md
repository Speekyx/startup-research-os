# TED-EU Evidence Reliability V1

**Authoritative.** Mission 1.15.12. The first reliability review carried out
against real Evidence, and the first to reach the end of the framework and stop.

**Outcome B. No `ReliabilityAssessment` was created.** The source method was
reviewed against first-party specifications and the findings are recorded below;
what is missing is not evidence but a **named accountable reviewer**, which no
origin in the contract lets a document review or a model supply.

**The TED Evidence remains `NON_SCORABLE` with `MISSING_RELIABILITY`**, alongside
the other seven. **H-36A NOT ESTABLISHED. H-36B NOT ADDRESSED. H-37 OPEN. H-38
OPEN.**

---

## 1. The question, stated narrowly enough to answer

Not *is TED reputable*. That question has no answer because it has no subject.

The question is whether the measurement behind one Evidence row dependably
supports the exact proposition that row is cited for:

> TED reported that, within a bounded set of 3 `CONTRACT_AWARD_NOTICE` notices
> classified under `CPV` division `90`, the largest `TOTAL_VALUE` amount at
> `NOTICE` scope stated in `EUR` exceeded the smallest by 686545.02.

So the chain under review is:

```text
a contract award notice, filled in by a buyer
  -> BT-161, published by TED
    -> the Search API's `total-value` field
      -> deterministic normalization to TOTAL_VALUE at NOTICE scope
        -> deterministic max-minus-min over a cohort
```

It is **not** a question about market size, demand, future willingness to pay,
profitability or pricing, and no finding below may be read toward any of them.

## 2. The scope, and the inventory it belongs to

```json
{"source_id":"ted-eu","resource_id":"notices/eforms-contract-and-award",
 "record_kind_id":"procurement_notice","claim_type":"OBSERVED",
 "proposition_kind":"source_reported_procurement_value_contrast"}
```

**Mission 1.14's "7 Evidence rows collapse to 3 scopes" is now 8 to 4**, measured
rather than assumed:

| Rows | Source | Resource | Record kind | Proposition kind |
|---|---|---|---|---|
| 4 | `world-bank` | `indicator/SP.POP.TOTL` | `numeric_observation` | `source_reported_metric_period_change` |
| 2 | `gdelt` | `web-ngrams/1gram` | `lexical_frequency_observation` | `source_reported_term_frequency_change` |
| 1 | `gdelt` | `web-ngrams/1gram` | `lexical_frequency_observation` | `source_reported_term_frequency_contrast` |
| **1** | **`ted-eu`** | **`notices/eforms-contract-and-award`** | **`procurement_notice`** | **`source_reported_procurement_value_contrast`** |

TED creates the **fourth** scope and **overlaps none** of the existing three: it
differs from every one of them in all five parts. The ratio that justified the
design in Mission 1.14 still holds — scopes grow with kinds of question, not with
observations.

**The cohort is not in the scope.** Another TED contrast over different notices,
or in another currency, resolves to the same scope. Reliability is about a
measurement and a purpose; a scope that moved with the notice ids would demand a
fresh review per Signal, which is the per-record judgement the contract says is
unreachable.

## 3. First-party evidence

Retrieved from the Publications Office's own eForms SDK, release **1.15.1**
(`OP-TED/eForms-SDK`, metadata database 1.14.44), and from TED's developer
documentation. EUR-Lex returned an empty body for the eForms Regulation again,
exactly as Missions 1.15.2 and 1.15.3 recorded; the SDK is the publisher's own
machine-readable expression of the same annex and is what was used.

No blog, tutorial, aggregator or SEO article was consulted, and none would have
been admissible.

## 4. What `TOTAL_VALUE` actually is

Our `TOTAL_VALUE` is the Search API field `total-value` with companion
`total-value-cur`. In eForms it is **BT-161**:

| | |
|---|---|
| Business term | **BT-161**, `BT-161-NoticeResult` |
| Name | *"Value of all contracts awarded in this notice"* |
| **Definition, verbatim** | *"The value of all contracts awarded in this notice, including options and renewals."* |
| XPath | `efac:NoticeResult/cbc:TotalAmount` |
| Currency | `BT-161-NoticeResult-Currency`, `cbc:TotalAmount/@currencyID` |
| Level | **Notice**, on `ND-NoticeResult`, which is itself non-repeatable |
| Repeatable | **No** |
| Legal type | `VALUE` |

**Three findings follow, and the first is the one that matters most.**

### 4.1 It includes options and renewals

The definition says so in its own words. The figure is therefore **not what was
paid**, and not even necessarily what will be paid: it includes contingent
amounts that may never be exercised.

This does not make the Claim wrong — the Claim says `TOTAL_VALUE`, quoted, and
asserts only a contrast between two such figures. It does mean any later reading
of that number as *revenue*, *spend* or *a price* is wrong at the source, before
any interpretation layer is involved.

### 4.2 It is an award-stage, notice-level aggregate, and the other three amounts are genuinely different things

Mission 1.15.8 kept four monetary semantics apart under their own names. The
specification confirms they are different terms at different levels, not
synonyms:

| Ours | BT | Verbatim definition | Level |
|---|---|---|---|
| `TOTAL_VALUE` | BT-161 | *"The value of all contracts awarded in this notice, including options and renewals."* | Notice result |
| `ESTIMATED_VALUE` | BT-27 | *"The estimated value of the procurement procedure or lot, over its whole duration, including options and renewals."* | **Lot** |
| `FRAMEWORK_MAXIMUM` | BT-118 | *"The maximum value which can be spent within the framework agreement(s) announced in this notice… as calculated on the basis of the winner's tender or winners' tenders."* | Notice result |
| `TENDER_VALUE` | BT-720 | *"The value of the tender or another result, including options and renewals."* | **Tender** |

Mixing any two would compare an award with an estimate, or a notice with a lot.
The refusal to flatten them was right, and is now first-party evidenced rather
than argued.

**A fourth notice-level amount exists that we do not collect:** BT-1118, *"Notice
Framework Approximate Value"*, also on `ND-NoticeResult`. So one notice can carry
BT-161, BT-118 and BT-1118 side by side — three notice-level amounts meaning
three different things. Reading any of them as *the* value of the notice would be
wrong, and only the amount-type-keyed cohort prevents it.

### 4.3 It is conditionally mandatory, and can be lawfully withheld

`can-standard`, the only notice type this collector requests, is eForms notice
subtypes **29, 30, 31 and 32**. BT-161 is `forbidden` in subtypes 1 to 24 —
contract notices carry no award value — and its `mandatory` constraint covers
subtypes **29 to 35** under a condition on whether a winner was selected and a
contract exists.

**And it may be legally deferred.** BT-161 carries a `privacy` block naming
BT-195 *"Field to publish later"*, BT-196, BT-197 and BT-198 *"Date of when this
will be published"*. BT-195's own definition states that *"Only fields concerning
the Result value and groups of fields concerning the Tender and Procedure Lot
Result can be unpublished"* — BT-161 is precisely such a field.

**This is the finding with the sharpest bearing on a contrast.** A cohort built
from published values is a cohort over the **published subset**, and the values
absent from it are absent for a stated legal reason rather than at random. A
maximum and a minimum computed over that subset are the extremes of what was
published, not of what was awarded. Nothing in the current pipeline detects a
deferred value: the Search API simply omits the key, which the response contract
already documents as indistinguishable from *no value exists*.

## 5. Who supplies it, and what TED guarantees

**The buyer supplies it.** A contract award notice is filled in and submitted by
the contracting authority through eNotices2; TED is the publication channel.

**TED validates conformance, not truth.** The SDK ships 60 published rules naming
BT-161, and every one is a presence, absence or notice-type constraint —
*"'Value of all contracts awarded in this notice' (BT-161-NoticeResult) is not
allowed (in '1 – Notice of the publication of a prior information notice…')"* and
similar. There is a rule that BT-161 must not appear in a prior information
notice. There is no rule, and no documented procedure, that the amount is
correct.

## 6. The authenticity boundary, stated as a limit on any future value

A reliability for this scope may concern:

> whether TED faithfully publishes, in a structured and specified form, the value
> the buyer submitted.

It may **not** be read as:

> whether the amount is an accurate account of the procurement, independently
> verified by TED or anyone else.

The Claim already respects this — it says *TED reported* — and a reliability
value must not quietly upgrade it. A high reliability here would mean *the
publication pipeline is dependable*, never *the contract really was worth that*.

## 7. What reliability is not, on this row

The real Evidence row and its lineage carry **five separate 1.0 values**, and not
one of them is a reliability:

| Value | What it says |
|---|---|
| `relevance` 1.0 | the Signal is about the same subject as the Claim |
| `directness` 1.0 | it bears on the Claim itself, not on something adjacent |
| `extraction_confidence` 1.0 | the interpreter read the Signal correctly |
| Signal `derivation_confidence` 1.0 | the arithmetic is mechanically established |
| Claim `interpretation_confidence` 1.0 | the restatement is a faithful reading |

**Reliability was not derived from any of them**, and the guarantee is
structural rather than a promise: `resolve_reliability` takes `scope`,
`candidates` and `supplied`, and nothing else. An AST test asserts that no
identifier named `derivation_confidence`, `interpretation_confidence`,
`extraction_confidence`, `relevance`, `directness`, `evidence_level`,
`support_count` or `approval_state` appears anywhere in the package.

**Support 3 is not a reliability either.** Three notices raise the number of
observations behind a contrast; they say nothing about whether a published award
value means what it appears to mean.

**Compliance is not reliability.** `ted-eu` is `APPROVED_WITH_CONDITIONS` under
`local-private-research-v1`. That says the system may acquire and process, and
nothing about dependability. The reliability schema has no column for a policy
state and the package contains no approval-state literal, both asserted.

## 8. Why no assessment was created

The framework offers exactly three origins, and each is closed against the
others:

| Origin | What it requires | Available here |
|---|---|---|
| `DOCUMENTED_METHOD` | *"The document supplies the number; the reviewer locates it"* — a documented sampling error, a stated completeness bound | **No.** eForms specifies what the field means, where it goes and when it is required. It states no error rate, no completeness bound, no accuracy claim. There is no number to locate |
| `CALIBRATED_EMPIRICALLY` | a `calibration_dataset_ref` of labelled outcomes | **No.** No outcome data exists, for this scope or any other |
| `HUMAN_REVIEW` | *"A named reviewer's judgement… The reviewer is accountable and identified"* | **Not by this mission.** `reviewed_by` is required and non-blank, and the model states that a model may not stand in for a reviewer |

And the contract closes the remaining door explicitly (§4):

> **No threshold labels.** There is no `0.9 = authoritative`, no `0.7 = good`.
> **No categorical mapping.** Not from source type, not from evidence level, not
> from anything.

So there is no rubric that turns §4's findings into a number. Inventing `0.8`
because the publication pipeline looks solid would be exactly the arbitrary
decimal the framework was built to refuse, and it would be worse here than
elsewhere because it would look considered.

**This is the same shape as the TED database-right acceptance.** The framework
deliberately reserves one act to an accountable person, and a mission that
performed it anyway would be defeating the design rather than completing it.

## 9. What a reviewer would need, and what is now ready for them

The documentary half is done. A `HUMAN_REVIEW` assessment for this scope would
rest on basis rows that already exist in evidence terms:

| Basis type | Document | Finding |
|---|---|---|
| `SOURCE_DOCUMENTATION` | eForms SDK 1.15.1 field repository | BT-161 is notice-level, non-repeatable, `cbc:TotalAmount` on `ND-NoticeResult` |
| `MEASUREMENT_METHODOLOGY` | eForms SDK 1.15.1 business-term definitions | *"The value of all contracts awarded in this notice, including options and renewals"* |
| `KNOWN_LIMITATION` | eForms SDK 1.15.1, BT-195 to BT-198 | the value may be lawfully withheld from immediate publication, so a cohort covers the published subset only |
| `KNOWN_LIMITATION` | eForms SDK 1.15.1 business rules | 60 rules govern where BT-161 may appear; none governs whether the amount is correct |

What only a person can add is the **number**, and the `stated_limitation` that
bounds it. The two questions they would have to answer, neither of which a
document settles:

1. **How much does "including options and renewals" cost this measurement** for a
   proposition that only compares two such figures? Arguably little, since both
   sides include them; arguably a lot, if the option share differs between
   contracts.
2. **How much does the lawful-withholding mechanism cost a max-minus-min?** The
   missingness is not random, and an extreme is exactly the statistic most
   exposed to non-random missingness.

## 10. State at mission end

| | |
|---|---|
| `ReliabilityAssessment` rows | **0**, unchanged |
| TED Evidence `reliability` | **NULL**, unchanged |
| Resolution outcome | `NO_APPLICABLE_ASSESSMENT`, through the production resolver |
| Scorability | **`NON_SCORABLE`**, `MISSING_RELIABILITY` |
| `observation_category` | `UNCATEGORISED`, untouched |
| `independence_state` | `UNKNOWN`, untouched |
| `evidence_level` | **1**, untouched |
| Aggregation profile | `UNCALIBRATED`, and unaffected by this mission |
| Opportunities, scores, embeddings | 0 |

All eight Evidence rows resolve to `NO_APPLICABLE_ASSESSMENT` against the real
candidate set, which is empty. **The system stays capable of producing no score,
which is what will make a score mean something when one appears.**
