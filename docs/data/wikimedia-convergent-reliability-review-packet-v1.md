# The Wikimedia convergent reliability question

**Status:** `READY_FOR_WIKIMEDIA_CONVERGENT_RELIABILITY_REVIEW`. Prepared by Mission 1.44 under **`human-reliability-assessment-rubric@1.0.0`**. **No value is supplied, suggested or implied.**

**Machine-readable:** [wikimedia-convergent-reliability-review-packet-v1.json](wikimedia-convergent-reliability-review-packet-v1.json)

---

## 1. The question

> **How dependable is THIS kind of measurement, for THIS kind of proposition?**

It is **not**: whether Wikimedia is a reputable organisation · whether Wikipedia is popular · the probability that any Claim is true · user interest, audience size, product adoption or demand · market size or commercial value · whether the source is governance-approved for use · whether our extractor read the Signal correctly · how directly the Evidence bears on a Claim · whether two Evidence rows are independent · how recently the observation was made.

**The scope, all five fields, matched in full or not at all:**

```text
source_id         wikimedia-pageviews
resource_id       metrics/pageviews/per-article/en.wikipedia.org
record_kind_id    content_request_count
claim_type        OBSERVED
proposition_kind  platform_counted_content_request_change_witnessed
```

It binds **18 Evidence rows across 6 Claims**, and the resolver currently returns **`NO_APPLICABLE_ASSESSMENT`**.

source_id, resource_id, record_kind_id, claim_type, proposition_kind. Matched in full or not at all. The scope carries no article, no direction, no requester class and no period, so one judgement would bind every Claim of this kind.

| Claim | article | direction | requester class | witnesses |
|---|---|---|---|---:|
| `e740d102` | Docker_(software) | INCREASING | `user` | **4** |
| `1324d79c` | Kubernetes | INCREASING | `user` | **3** |
| `9bda8081` | Kubernetes | DECREASING | `user` | **3** |
| `a4809b1a` | Podman | INCREASING | `user` | **3** |
| `dff657c2` | Podman | DECREASING | `user` | **3** |
| `39449935` | Docker_(software) | DECREASING | `user` | **2** |

**One judgement binds every row above.** The scope carries no article, no direction, no requester class, no period and no witness count, so there is one question here rather than six — and **a Claim with four witnesses is not thereby a more dependable measurement.** Cardinality belongs to aggregation; reliability belongs to measurement crossed with proposition.

## 2. Why the existing Wikimedia 0.65 does not answer this

There is a `HUMAN_REVIEW` assessment at **0.65** for `platform_counted_content_request_change`, reviewed by `thibchm`, predating the rubric and therefore recording no rubric provenance.

**It does not bind here, it must not be copied, and it is not a baseline, an anchor or a starting point.** Four of the five scope fields are identical; `proposition_kind` differs, and that is sufficient. There is no closest-match logic, no fallback and no source-wide coefficient.

**30 leak checks, 0 leaks** — run in both directions across every proposition kind in the corpus.

### What changed, and what did not

- **Detailed:** that the platform counted, for a NAMED pair of adjacent published day buckets, more or fewer requests for a named item under a named requester class in the later bucket than the earlier one.
- **Convergent:** that the platform counted, for that item under that requester class, AT LEAST ONE pair of adjacent published day buckets standing in the named direction.
- **What moved:** period_label_from and period_label_to moved from proposition identity to witness provenance. They are not discarded: they remain on the Signal and are recoverable through Evidence -> Signal -> signal_inputs -> normalized_records.
- **What did not change:** the underlying measurement. Both propositions read the same per-article daily request counts, produced by the same counting rules, under the same requester class, on the same project. The convergent claim reads no new field and applies no new arithmetic.

**What convergence newly raises:**

- MULTIPLE WITNESSES OF ONE METHODOLOGY DO NOT INSURE AGAINST A METHODOLOGY-LEVEL FAILURE. An existential survives the loss of one witness, which looks like robustness. But every witness of a convergent Claim here shares one counting rule, one tagging mechanism and one publication pipeline, and independence is UNKNOWN -- so a SYSTEMATIC change, such as a retroactive reclassification of a requester class, could remove every witness at once. Whether that makes the proposition more dependable than the detailed one, or merely differently exposed, is a judgement.
- AN EXISTENTIAL IS MONOTONE OVER PUBLICATION AND NOT OVER REVISION. Once a qualifying pair has been published, no later day can falsify the claim. But if a published value may itself be recomputed, the witness that established it can stop being a witness -- so the usual monotonicity argument for existentials depends on a revision policy this basis does not state.
- IT CARRIES NO PERIOD, so a reader cannot tell from the claim WHEN the qualifying pair fell, and the wording must carry that bound instead.
- SEVERAL DAY-PAIRS ARE ASSERTED TO WITNESS ONE PROPOSITION, which is an SROS interpretation step that does not exist for the detailed claim.

## 3. What the held documents establish

| question | answer | open? |
|---|---|---|
| What is counted? | A pageview, defined by the platform as an explicit conjunction of HTTP-status, host and header conditions, with an enumerated exclusion list. | no |
| How is automated traffic separated? | By tagging: ua-parser plus custom regex pattern matching. The platform describes its own detection rather than asserting that the remainder is human. | no |
| What does the requester class `user` mean? | The platform's own class name for traffic NOT identified as automated by that tagging. It is a source-native label and does not mean human, person, reader or customer. | no |
| Are known problems documented? | Yes. A dated known-problems list exists and records a 2016 user-agent classification incident. | no |
| Is there a revision or backfill POLICY for published values? | NOT ESTABLISHED by the held basis. An incident list records that a classification problem occurred; it does not state whether published values are recomputed, corrected, or left as published, nor how a consumer would tell. | **OPEN** |
| Did the pageview definition or the tagging rules change across the witness periods? | NOT ESTABLISHED by the held basis. Neither document is versioned against the 2024-03 dates the witnesses fall in. | **OPEN** |
| How long does a published per-article daily value remain retrievable? | NOT ESTABLISHED by the held basis. Neither document addresses retention or long-term availability. | **OPEN** |

**Nothing was fetched.** Both documents were already attached to the detailed assessment, and the convergent proposition reads the same measurement through the same rules.

### Applicability of the held basis rows

- **Research:Page view** (`Definition; Tagging`, `MEASUREMENT_METHODOLOGY`) — **REUSED**. It defines what a pageview IS and how requester classes are tagged. The convergent proposition reads exactly the same measurement through exactly the same rules; what changed is which observation witnesses the assertion, not what was measured. It is if anything MORE load-bearing here, because the requester class is one of the six identity fields the contract keeps.
- **Data Platform / Data Lake / Traffic / Pageviews** (`Events and known problems since 2015-05-01`, `KNOWN_LIMITATION`) — **PARTIALLY_APPLICABLE**. The FACT is unchanged and remains a real limitation: a dated known-problems list exists, it records a classification incident, and revision practice is not stated. Its WEIGHT moves in two directions at once under an existential, and which dominates is a judgement. A LOCALISED problem matters LESS, because an existential needs only one surviving witness. A SYSTEMATIC reclassification matters MORE, because the several witnesses of one convergent Claim share a methodology and their independence is UNKNOWN, so they can all fail together. The reviewer decides which reading governs; software records both.

## 4. Failure modes

| failure mode | dimension | origin | documented | effect on the convergent proposition |
|---|---|---|---|---|
| traffic that a reader would call automated is tagged as the `user` class, or the reverse | `SOURCE_SIDE_VALIDATION` | `SOURCE_CLASSIFICATION` | yes | the same as on the detailed one, and NOT reduced by having several witnesses: every witness is tagged by the same mechanism |
| a published value is later recomputed, corrected or reclassified | `HISTORICAL_MUTABILITY` | `SOURCE_HISTORY` | **no** | SHARPER here than for the detailed claim. A revision that removes one qualifying pair leaves the existential standing if another survives; a SYSTEMATIC reclassification could remove every witness at once, because the witnesses share a methodology and their independence is UNKNOWN |
| a documented known problem covers one of the witnessing days | `COMPLETENESS_AND_MISSINGNESS` | `SOURCE_HISTORY` | yes | an existential needs one surviving witness, so a localised incident is less damaging than it is to a named-pair claim |
| requests are missing for an interval, through an outage or a pipeline gap | `COMPLETENESS_AND_MISSINGNESS` | `SOURCE` | yes | a spurious direction could qualify a pair that should not have qualified, and an existential does not require the pair to be typical |
| an absent term is treated as a zero rather than an absence | `COMPLETENESS_AND_MISSINGNESS` | `EXTRACTOR` | yes | none |
| two day-pairs that do not witness the same proposition are treated as if they do | `MEASUREMENT_DEFINITION` | `CONVERGENCE_CONTRACT` | yes | THIS FAILURE MODE DOES NOT EXIST FOR THE DETAILED CLAIM. It is created by convergence. |
| one witness counted twice | `MEASUREMENT_DEFINITION` | `CONVERGENCE_CONTRACT` | yes | would inflate apparent witness count without adding an observation |
| the acquisition window shaped which day-pairs exist to witness | `COMPLETENESS_AND_MISSINGNESS` | `COLLECTOR` | yes | the existential wording carries it, and the risk is entirely in how a reader summarises the claim |
| the per-article identity does not name the article a reader means | `MEASUREMENT_DEFINITION` | `NORMALIZER` | yes | none |

## 5. Engineering validation is recorded separately, and is not basis

- The convergence contract is deterministic, has six fixed identity fields and refuses any fact it does not classify.
- witness_key over the witness facts prevents one day-pair being counted as two witnesses.
- The Mission 1.41 Evidence identity repair means re-interpreting an unchanged Signal cannot insert a second row.
- Witness day-pairs remain recoverable through Evidence to Signal to signal_inputs to normalized_records.
- Mission 1.43 added a non-empty-fixture test class so reporting branches the live corpus never enters are executed.
- The canonical cardinalities were measured rather than asserted: 18 Evidence across 6 Claims.

**`ENGINEERING_VALIDATION_INPUT` — `may_be_used_as_reliability_basis: False`.** That the implementation does what its specification says. It establishes **anything about how dependable the platform's request counting is for this proposition.**

**Independence stays `UNKNOWN` on all 18 rows with 0 groups.** Different days, different articles and different directions do not establish independence: one publisher, one collection method and one counting methodology remain shared provenance.

---

## 6. Operator worksheet

**Scope**

```text
source_id         wikimedia-pageviews
resource_id       metrics/pageviews/per-article/en.wikipedia.org
record_kind_id    content_request_count
claim_type        OBSERVED
proposition_kind  platform_counted_content_request_change_witnessed
```

### 6.1 The dimension profile

States: `DOCUMENTED_AND_BOUNDED` · `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` · `PARTIALLY_DOCUMENTED` · `NOT_ESTABLISHED` · `CONTRADICTED`

```text
MEASUREMENT_DEFINITION           ______________________________
SOURCE_SIDE_VALIDATION           ______________________________
HISTORICAL_MUTABILITY            ______________________________
COMPLETENESS_AND_MISSINGNESS     ______________________________
SOURCE_SIDE_CHECKABILITY         NOT_ESTABLISHED
```

**`SOURCE_SIDE_CHECKABILITY` is pre-filled `NOT_ESTABLISHED`**, and it is the only one. The review's basis is two documents. One defines the pageview and its tagging; the other lists known problems. Neither addresses what the source exposes for inspection, or for how long. That is a checkable statement about the corpus rather than a judgement about sufficiency.

**Deliberately left blank, and why:**

- **`HISTORICAL_MUTABILITY`** — NOT assigned, although it is the dimension a reader would expect. The basis is not silent: it records that a classification incident happened. Whether an incident list without a revision policy is PARTIALLY_DOCUMENTED or NOT_ESTABLISHED is a judgement about whether what IS documented is enough, and that is the reviewer's. This is where this scope differs from the TED convergent one, whose basis contained nothing at all on the equivalent question.
- **`MEASUREMENT_DEFINITION`** — NOT assigned. The definition is documented; whether it is documented ENOUGH for this proposition is a judgement.
- **`SOURCE_SIDE_VALIDATION`** — NOT assigned. The tagging mechanism is documented and is heuristic; how much that bounds the measurement is a judgement.
- **`COMPLETENESS_AND_MISSINGNESS`** — NOT assigned. A known-problems list exists; whether it bounds the missingness is a judgement.

### 6.2 Material unknowns

**`HISTORICAL_MUTABILITY`** — whether a published per-article daily value may later be revised, recomputed or corrected, and whether a consumer could tell that it had been  (documentary status: `PARTIAL`)

> Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?

```text
YES / NO / UNSURE   ______
```

**`SOURCE_SIDE_VALIDATION`** — whether requester-class tagging may be re-applied retroactively to values already published  (documentary status: `PARTIAL`)

> Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?

```text
YES / NO / UNSURE   ______
```

**`HISTORICAL_MUTABILITY`** — whether a systematic reclassification would remove EVERY witness of one convergent Claim at once, given that the witnesses share one methodology and their independence is UNKNOWN  (documentary status: `NOT_ESTABLISHED`)

> Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?

```text
YES / NO / UNSURE   ______
```

**`MEASUREMENT_DEFINITION`** — whether the pageview definition or the tagging rules changed across the 2024-03 witness periods  (documentary status: `NOT_ESTABLISHED`)

> Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?

```text
YES / NO / UNSURE   ______
```

**`SOURCE_SIDE_CHECKABILITY`** — how long a published per-article daily value remains retrievable at the source  (documentary status: `NOT_ESTABLISHED`)

> Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?

```text
YES / NO / UNSURE   ______
```

**`COMPLETENESS_AND_MISSINGNESS`** — whether any of the six witness dates in 2024-03 falls inside an entry on the known-problems list  (documentary status: `NOT_ESTABLISHED`)

> Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?

```text
YES / NO / UNSURE   ______
```

### 6.3 Hard stops

| hard stop | condition | triggered? |
|---|---|---|
| `MEASUREMENT_SEMANTICS_NOT_ESTABLISHED` | `MEASUREMENT_DEFINITION` is `NOT_ESTABLISHED`. | ______ |
| `PROPOSITION_EXCEEDS_MEASUREMENT` | The proposition asserts something the measurement does not observe. | ______ |
| `AUTHORITATIVE_DOCUMENTS_CONTRADICT` | Any dimension is `CONTRADICTED` and the conflict is unreconciled. | ______ |
| `SOURCE_OBSERVATIONS_NOT_RECOVERABLE` | The Evidence rows in scope cannot be traced back to the observations the source published. | ______ |

**A limitation is not a hard stop.** Each of these makes a numeric judgement *unavailable* because the reliability question has no answer in that situation, never because the answer would be low.

### 6.4 The gate, and the judgement

Options: `NUMERIC_JUDGEMENT_PERMITTED` · `NUMERIC_JUDGEMENT_NOT_JUSTIFIED` · `DOCUMENTATION_INSUFFICIENT` · `REVIEW_BLOCKED_BY_CONTRADICTION` · `REVIEWER_DISAGREEMENT_UNRESOLVED`

```text
NUMERIC_JUDGEMENT_GATE           UNANSWERED

Only if the gate is PERMITTED:

Reliability [0.0, 1.0]           ______________________________
Rationale                        ______________________________
Stated limitation                ______________________________
Reviewer                         ______________________________
Review timestamp                 ______________________________
```

**If the gate is not `NUMERIC_JUDGEMENT_PERMITTED`** — Leave the assessment absent. All 18 Evidence rows across 6 Claims stay NON_SCORABLE, the resolver keeps returning NO_APPLICABLE_ASSESSMENT, and the six Claims remain UNAVAILABLE. That is the designed behaviour rather than a gap, and it is a complete review.

A future assessment for this scope would record `human-reliability-assessment-rubric@1.0.0`. Migration 0032 added these columns, so an assessment for this scope CAN record which procedure produced it. The two pre-rubric assessments keep NULL, which is true rather than missing.

## 7. What a value here would not do

- It would not calibrate anything. REFERENCE_PROFILE_V1 stays UNCALIBRATED and reliability review is not calibration.
- It would not establish independence. All 18 rows stay UNKNOWN with 0 groups.
- It would not become a Wikimedia-wide coefficient. The scope is five fields; wikimedia-pageviews alone matches nothing.
- It would not apply to Docker, Kubernetes or Podman separately. The scope carries no article.
- It would not differ by direction or by witness count. The scope carries neither.
- It would not make the Claims true, and it would not make any aggregation output a probability.
- It would not, on its own, make the full aggregator differ from the reliability pass-through baseline. Mission 1.43 established that with one provenance group those are algebraically the same number, and these six Claims each have one.

---

**This packet is:** NOT a reliability judgement. Every judgement field is blank. NOT a recommendation, a range, an anchor or a starting point. NOT a re-review of the detailed Wikimedia assessment, which is untouched. NOT an assertion that the existing 0.65 is near the right answer for this scope.

**Nothing above is pre-filled with a judgement**, and the reviewer is not inferred from a git author, a PR author, an OS username, the existing assessment or any conversation.
