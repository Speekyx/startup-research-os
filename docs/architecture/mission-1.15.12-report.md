# Mission 1.15.12 — TED-EU Evidence Reliability Assessment

**Sprint 1. Authorized by the Mission 1.15.12 brief §1-§44.**

**Outcome B. No `ReliabilityAssessment` was created, and that is the correct
result.** The source method was reviewed against first-party specifications and
the findings are recorded; what is missing is not evidence but a **named
accountable reviewer**, which no origin in the contract lets a document review or
a model supply.

**The TED Evidence remains `NON_SCORABLE` with `MISSING_RELIABILITY`.**

**H-36A NOT ESTABLISHED. H-36B NOT ADDRESSED. H-37 OPEN. H-38 OPEN.**

Full review: [`ted-eu-evidence-reliability-v1.md`](../data/ted-eu-evidence-reliability-v1.md).

---

## 1. The scope inventory

### How many distinct reliability scopes exist across the current 8 Evidence rows?

**Four.** Measured against the live database rather than carried forward from
Mission 1.14's "seven rows, three scopes".

| Rows | Source | Resource | Record kind | Proposition kind |
|---|---|---|---|---|
| 4 | `world-bank` | `indicator/SP.POP.TOTL` | `numeric_observation` | `source_reported_metric_period_change` |
| 2 | `gdelt` | `web-ngrams/1gram` | `lexical_frequency_observation` | `source_reported_term_frequency_change` |
| 1 | `gdelt` | `web-ngrams/1gram` | `lexical_frequency_observation` | `source_reported_term_frequency_contrast` |
| **1** | **`ted-eu`** | **`notices/eforms-contract-and-award`** | **`procurement_notice`** | **`source_reported_procurement_value_contrast`** |

### Does TED create a new scope? Does anything overlap?

**Yes, the fourth, and nothing overlaps.** The TED scope differs from every
existing one in all five parts, so no existing assessment could reach it and a
TED assessment could reach nothing else.

The ratio Mission 1.14 justified itself with survives, and how it grew is the
evidence for it: **the count rose when a new kind of question was asked, not when
observations arrived.** Mission 1.15.10 added eight raw records and 1.15.11 added
one Claim; the scope count moved by one, once.

### What exact TED reliability scope was reviewed?

```json
{"source_id":"ted-eu","resource_id":"notices/eforms-contract-and-award",
 "record_kind_id":"procurement_notice","claim_type":"OBSERVED",
 "proposition_kind":"source_reported_procurement_value_contrast"}
```

Not broadened to all TED, all procurement, all `OBSERVED` claims or all eForms
fields. The cohort is deliberately **not** in the scope: another TED contrast
over different notices resolves to the same scope, because a scope that moved
with the notice ids would demand a fresh review per Signal.

---

## 2. What reliability means here

### What does it mean for this scope? What does it explicitly not mean?

It means: **does the measurement behind this row dependably support the exact
proposition the row is cited for** — that TED reported a contrast between
`TOTAL_VALUE` figures in published award notices.

It does **not** mean market size, demand, willingness to pay, profitability,
pricing, or the truth of any commercial hypothesis. And it is not the question
*is TED reputable*, which has no answer because it has no subject.

### What first-party documents were used?

The Publications Office's own **eForms SDK, release 1.15.1** (`OP-TED/eForms-SDK`,
metadata database 1.14.44): the field repository, the English business-term
definitions, the notice-type definitions and the published business rules. Plus
TED's developer documentation for the business-term index.

**EUR-Lex returned an empty body** for the eForms Regulation, exactly as Missions
1.15.2 and 1.15.3 recorded. The SDK is the publisher's own machine-readable
expression of the same annex and is what was used. No blog, tutorial or
aggregator was consulted.

---

## 3. What `TOTAL_VALUE` is

### What business term, and what does it mean?

**BT-161**, `BT-161-NoticeResult`, name *"Value of all contracts awarded in this
notice"*, definition **verbatim**:

> *"The value of all contracts awarded in this notice, including options and
> renewals."*

### Is it notice-level?

**Yes.** XPath `efac:NoticeResult/cbc:TotalAmount`, on `ND-NoticeResult`, which is
itself non-repeatable, and the field is non-repeatable. Our `NOTICE` scope is
correct.

### Estimated, awarded, concluded, maximum, or another value?

**Awarded**, at notice level, aggregated over all contracts in the notice — and
**including options and renewals**, which is the finding that matters most. The
figure is therefore **not what was paid**, and not necessarily what will be: it
includes contingent amounts that may never be exercised.

The Claim survives this — it says `TOTAL_VALUE`, quoted, and asserts only a
contrast — but any later reading of the number as revenue, spend or a price is
wrong **at the source**, before any interpretation layer is involved.

The other three amounts are genuinely different terms at different levels, which
vindicates Mission 1.15.8's refusal to flatten them:

| Ours | BT | Level |
|---|---|---|
| `TOTAL_VALUE` | BT-161 | notice result |
| `ESTIMATED_VALUE` | BT-27 | **lot** |
| `FRAMEWORK_MAXIMUM` | BT-118 | notice result |
| `TENDER_VALUE` | BT-720 | **tender** |

A fourth notice-level amount exists that we do not collect — **BT-1118**, *"Notice
Framework Approximate Value"* — so one notice can carry three notice-level
amounts meaning three different things. Only the amount-type-keyed cohort keeps
them apart.

### Who supplies it?

**The buyer.** A contract award notice is filled in and submitted by the
contracting authority through eNotices2; TED is the publication channel.

### What validation or publication guarantees are documented?

**Conformance only.** The SDK ships **60 published rules** naming BT-161 and every
one is a presence, absence or notice-type constraint. There is a rule that BT-161
must not appear in a prior information notice. **There is no rule, and no
documented procedure, that the amount is correct.**

Mandatory status: `can-standard` is eForms subtypes **29 to 32**, and BT-161 is
conditionally mandatory across subtypes 29 to 35, forbidden in 1 to 24.

### Is TED independently verifying the underlying contract fact? What limitation remains?

**No.** The authenticity boundary is unchanged: a reliability here may concern
whether TED faithfully publishes, in a structured and specified form, the value
the buyer submitted. It may never be read as whether the amount is an accurate
account of the procurement.

**And one further limitation, which is the sharpest finding of the mission.**
BT-161 carries a `privacy` block naming BT-195 to BT-198, and BT-195's own
definition confirms that *"Only fields concerning the Result value…can be
unpublished"* — BT-161 is precisely such a field. **The value can be lawfully
withheld from immediate publication and released later.**

A cohort built from published values is therefore a cohort over the **published
subset**, and its maximum and minimum are the extremes of what was published
rather than of what was awarded. The missingness is not random, and **an extreme
is exactly the statistic most exposed to non-random missingness**. Nothing in the
pipeline detects a deferred value: the Search API omits the key, which the
response contract already documents as indistinguishable from *no value exists*.

---

## 4. What reliability was kept separate from

### Were collector/normalizer correctness double-counted as reliability?

**No.** The row and its lineage carry five separate `1.0` values — `relevance`,
`directness`, `extraction_confidence`, the Signal's `derivation_confidence` and
the Claim's `interpretation_confidence` — and each answers a different question.
Reliability had to mean something none of them means, and it does.

### Was `derivation_confidence` used numerically? `interpretation_confidence`? Support count? Source compliance?

**None of them**, and the guarantee is structural rather than a promise:
`resolve_reliability` takes `scope`, `candidates` and `supplied`, and nothing
else. A test asserts the signature, and an **AST test** asserts that no
identifier named `derivation_confidence`, `interpretation_confidence`,
`extraction_confidence`, `relevance`, `directness`, `evidence_level`,
`support_count` or `approval_state` appears anywhere in the package — over
identifiers rather than text, so the docstrings explaining the rule cannot fail
it.

Support 3 raises the number of observations behind a contrast and says nothing
about what a published award value means. `APPROVED_WITH_CONDITIONS` says the
system may acquire and process, and nothing about dependability.

---

## 5. Why no assessment was created

### What origin applies?

**None that this mission can satisfy.**

| Origin | Requires | Available |
|---|---|---|
| `DOCUMENTED_METHOD` | *"The document supplies the number; the reviewer locates it"* | **No.** eForms specifies meaning, placement and conditional necessity. It states no error rate, no completeness bound, no accuracy claim. There is no number to locate |
| `CALIBRATED_EMPIRICALLY` | a calibration dataset of labelled outcomes | **No.** None exists, for this scope or any other |
| `HUMAN_REVIEW` | *"A named reviewer's judgement… accountable and identified"* | **Not by this mission.** `reviewed_by` is required, and the model states a model may not stand in for a reviewer |

### Was a numeric reliability created? What exact requirement prevents it?

**No.** And the contract closes the remaining door outright (§4):

> **No threshold labels.** There is no `0.9 = authoritative`, no `0.7 = good`.
> **No categorical mapping.** Not from source type, not from evidence level, not
> from anything.

There is no rubric that turns the §3 findings into a number. Inventing `0.8`
because the publication pipeline looks solid is precisely the arbitrary decimal
the framework was built to refuse — and it would be worse here than elsewhere
because it would look considered.

**This is the same shape as the TED database-right acceptance.** The framework
deliberately reserves one act to an accountable person, and a mission that
performed it anyway would defeat the design rather than complete it.

### What reliability profile/state applies?

The aggregation profile stays **`UNCALIBRATED`**, and this mission does not move
it. The contract is explicit that it *"stays `UNCALIBRATED` regardless of how many
assessments exist"* — reviewing reliability and fitting parameters to outcomes
are different acts, and no assessment exists in any case.

### Was a `ReliabilityAssessment` row created? Does anything leak?

**No row was created.** `epistemic.reliability_assessments` holds **0** rows and
`epistemic.reliability_assessment_basis` holds 0.

Leakage is tested against synthetic assessments rather than left untested: a TED
assessment applies to the TED scope and does **not** reach a second TED resource,
another record kind, an `INFERRED` claim, another proposition kind, World Bank or
GDELT. Scope matching does the work; there is no TED special case in the matcher.

---

## 6. What stayed orthogonal

| | |
|---|---|
| `observation_category` | **`UNCATEGORISED`**, unchanged |
| `independence_state` | **`UNKNOWN`**, group NULL, unchanged |
| `evidence_level` | **1**, unchanged |

### Can reliability alone produce Level 4?

**No, and it is prevented twice.** `MARKET_ACTIVITY` or `DIRECT_VALIDATION` is the
only gate to Level 4 and this row is `UNCATEGORISED`; the level ladder
additionally excludes any row whose independence is `UNKNOWN`. A reliability value
would satisfy neither gate.

The structural reason is stronger than the arithmetic one and is what the tests
pin: **an assessment has no field in which to declare a category or an
independence**, and `resolve_reliability` returns a resolution rather than a
mutated row. There is nothing for reliability to promote with.

### Is the Evidence now scorable?

**No. `NON_SCORABLE` with `MISSING_RELIABILITY`**, together with the other seven.
Resolved through the production resolver against the real candidate set:

```text
candidate assessments in the database: 0

    gdelt       source_reported_term_frequency_change      -> NO_APPLICABLE_ASSESSMENT
    gdelt       source_reported_term_frequency_change      -> NO_APPLICABLE_ASSESSMENT
    gdelt       source_reported_term_frequency_contrast    -> NO_APPLICABLE_ASSESSMENT
TED ted-eu      source_reported_procurement_value_contrast -> NO_APPLICABLE_ASSESSMENT
    world-bank  source_reported_metric_period_change       -> NO_APPLICABLE_ASSESSMENT  (x4)
```

### What remains missing?

One thing: **a named person willing to be accountable for a number**, plus the
`stated_limitation` that bounds it. The documentary half is done and is recorded
as basis-ready findings in `ted-eu-evidence-reliability-v1.md` §9.

The two questions only a person can settle, neither of which a document answers:

1. how much *"including options and renewals"* costs a proposition that only
   compares two such figures — arguably little, since both sides include them;
   arguably a lot, if the option share differs between contracts;
2. how much the lawful-withholding mechanism costs a max-minus-min, given that an
   extreme is the statistic most exposed to non-random missingness.

---

## 7. What was not done

| | |
|---|---|
| New RawRecords | **0.** No TED API call for procurement data |
| New NormalizedRecords, Signals, Claims, Evidence | **0** |
| `INFERRED` Claims | 0 |
| Opportunities | **0**, unchanged |
| Embeddings | 0 |
| Business/market/WTP/MRR scores | **0**, and no Evidence score either |
| Existing seven Evidence rows | **unchanged**, no assessment created for their scopes |
| LLM calls | **none** |
| Gateway defect | not fixed, still backlog |
| Acquisition-bounds provenance gap | recorded as backlog, not redesigned |

### Counts before and after

| | Before | After |
|---|---|---|
| RawRecords | 23 | 23 |
| NormalizedRecords | 23 | 23 |
| Signals | 8 | 8 |
| Claims / ClaimRevisions | 8 / 8 | 8 / 8 |
| Evidence | 8 | 8 |
| **ReliabilityAssessments** | **0** | **0** |
| Opportunities / Embeddings / Scores | 0 | 0 |

### One documentation correction the specification forced

The normalizer described `TOTAL_VALUE` as *"the total value the notice states for
the procurement it reports"*. BT-161's own definition says *"including options
and renewals"*, which is a materially different statement, and the omission was
exactly the kind that lets a later reader treat the figure as money spent. Both
the module constant and `ted-eu-normalization-v1.md` now carry the verbatim
definition.

---

## 8. Did all gates pass?

**Yes, every one, checked by exit code.**

```text
zero-dependency suites            538 tests, 8 packages      exit 0   (was 515)
all pytest suites                 7 packages                 exit 0
validate_schema                                              exit 0
validate_source_registry                                     exit 0
validate_compliance_capabilities                             exit 0
validate_normalization                                       exit 0
validate_signals                                             exit 0
validate_claims                                              exit 0
validate_evidence_aggregation                                exit 0
contract generation --check                                  exit 0
sros-source render --check                                   exit 0
render_review_results --check                                exit 0
render_signal_coverage --check                               exit 0
sensitivity --check                                          exit 0
ruff check / ruff format --check                             exit 0
mypy                              144 source files           exit 0
environment-template secret check                            exit 0
assert_registry_grants_nothing                               exit 0
```

23 new tests, all in `packages/evidence-reliability`. The scope they use is real;
every assessment is synthetic, with a deliberately implausible fixture value
(`0.42`) that no test asserts anything about — a fixture of `0.9` in a reliability
test is a number someone eventually copies into a real assessment, because it
looks like a judgement.

---

## 9. Next mission

The brief's §42 asks which blocker actually stands. Three candidates were on the
table, and the result narrows them to one.

**Recommendation: C, but scoped as a governance act rather than an engineering
one — "TED Evidence Reliability: the reviewer's half".**

Not A (independence and category treatment): both are working correctly and
neither blocks anything today. Category is a decision already recorded as an open
question in Mission 1.15.11, and it does not gate scorability — reliability does.

Not B (`INFERRED` Claims): building an inference layer over evidence that cannot
yet be weighed is how a plausible number acquires authority it never earned. The
same argument that deferred it in 1.15.11 is stronger now, because this mission
established two specific reasons the underlying figure is slipperier than it
looks.

**What actually stands is the reviewer's half of C**, and it is not code. The
framework works, the scope is right, the documents are read and the findings are
written down. What is missing is a person putting a number and a stated
limitation against them — which, like the database-right acceptance, is an act
the repository deliberately cannot perform.

So the next mission is either:

- **the operator writes the assessment**, using
  `evidence-reliability-review-guide-v1.md` and §9 of the review document, with a
  tooling task to record it the way ADR-030 records the other human decision; or
- **if that is not wanted yet**, a mission that is honest about the consequence:
  the pipeline is complete from acquisition to Evidence and will produce **no
  score at all** until someone reviews a reliability. That is not a defect, and
  it is worth stating plainly before any mission proposes to work around it.

**What should not happen next is an Opportunity.** No Opportunity exists, none is
needed to make the pipeline coherent, and the only evidence that would feed one
is currently non-scorable for a reason nobody has resolved.
