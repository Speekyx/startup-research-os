# The human reliability assessment rubric

**`human-reliability-assessment-rubric@1.0.0`.** Generated from `sros_evidence_reliability/rubric.py`; edit that, not this.

---

## 0. The gap this closes

Mission 1.14 defined what reliability means, ADR-026 defined the scope it binds to, and the review guide told a reviewer to write the failure mode down first. None of them defines the step from documented facts to a number. This rubric is that step.

```text
DOCUMENTED FACTS  ->  [ this rubric ]  ->  HUMAN JUDGEMENT  ->  Assessment
```

**The gap was never decimal precision.** A reviewer who has read every document and written the failure mode down still had no procedure that made one number rather than a neighbouring one defensible.

## 1. The question, unchanged

> **How dependable is this kind of measurement, for this kind of proposition?**

It is never any of these:

- the probability that the Claim is true
- the reputation or prominence of the publisher
- whether the source is legally permitted to be used
- the quality or attractiveness of an Opportunity
- market size, demand, or commercial value
- whether SROS's downstream business conclusions are correct
- whether two Evidence rows are independent
- whether our extractor read the Signal correctly
- how directly the Evidence bears on the Claim
- how recently the observation was made

## 2. Review states

One vocabulary across every dimension, so a reviewer learns it once. **Three are ordered and two are deliberately off the order** — that is the structural form of *UNKNOWN is not LOW*.

| state | rank |
|---|---|
| `DOCUMENTED_AND_BOUNDED` | 3 |
| `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` | 2 |
| `PARTIALLY_DOCUMENTED` | 1 |
| `NOT_ESTABLISHED` | **none** |
| `CONTRADICTED` | **none** |

A state with no rank cannot be interpolated, averaged, or read as the bottom of a scale. `NOT_ESTABLISHED` is the absence of an answer, not a worse one; `CONTRADICTED` is a blocker, not a weak position.

**The ranks order the three documented states and are never arithmetic.** Nothing sums them, averages them, weights them, or maps one to a reliability value — a rank that could be added up would be a points system with a vocabulary in front of it.

**Software may assert exactly one of them:** `NOT_ESTABLISHED` — because *no document in this review's basis addresses this question* is a checkable claim about the corpus. Every other state judges whether what is documented is *enough*, and that is the reviewer's.

## 3. The dimensions

### MEASUREMENT_DEFINITION

> Does first-party documentation define what is measured?

**Why this is reliability.** It is the precondition for the reliability question being answerable at all. If nobody has said what the number counts, there is nothing to be dependable ABOUT.

**Not to be confused with** extraction confidence, which asks whether we read the published value correctly. A perfectly read value of an undefined quantity is still an undefined quantity.

| state | what it looks like |
|---|---|
| `DOCUMENTED_AND_BOUNDED` | A retrieved first-party document defines the measurement and states what it includes and excludes. |
| `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` | The definition is documented and names an inclusion or exclusion whose extent the documents do not establish. |
| `PARTIALLY_DOCUMENTED` | The documents define part of the measurement and are silent on a part the reviewer can name. |
| `NOT_ESTABLISHED` | No document in this review's basis defines what is measured. |
| `CONTRADICTED` | Two retrieved documents define the measurement differently, and the difference is not reconciled by either. |

### SOURCE_SIDE_VALIDATION

> What does the source itself validate before publishing the value?

**Why this is reliability.** It is the difference between a value that passed a correctness check and one that only passed a format check, which is the single most load-bearing fact in every review this repository has performed.

**Not to be confused with** governance status. An APPROVED source does not validate its data more carefully than a RESTRICTED one; permission and correctness are decided by different people for different reasons.

| state | what it looks like |
|---|---|
| `DOCUMENTED_AND_BOUNDED` | The documents state what is validated, and the validation covers the correctness of the published value. |
| `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` | The documents state what is validated, the validation does NOT reach correctness, and how far the published values may depart from the underlying facts is not established. |
| `PARTIALLY_DOCUMENTED` | Some validation is documented and the reviewer can name a published field whose treatment is not covered. |
| `NOT_ESTABLISHED` | No document in this review's basis says what, if anything, the source validates. |
| `CONTRADICTED` | A documented validation rule is contradicted by another document or by observed published data. |

### HISTORICAL_MUTABILITY

> Can a published measurement later be corrected, amended, superseded or withdrawn, and is that practice documented?

**Why this is reliability.** It decides whether re-reading the same observation would yield the same value. A measurement that can silently change underneath a Claim is less dependable for that Claim however well defined it is.

**Not to be confused with** freshness, which asks whether a Claim decays as the WORLD moves on. This asks whether the RECORD is stable. A permanently true statement about an unstable record is still resting on an unstable record.

| state | what it looks like |
|---|---|
| `DOCUMENTED_AND_BOUNDED` | The documents state the revision practice, and state how a consumer can tell that a value has been revised. |
| `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` | Revision is documented as possible, and how often or how far values move is not established. |
| `PARTIALLY_DOCUMENTED` | Some revision behaviour is documented and the reviewer can name a case the documents do not cover. |
| `NOT_ESTABLISHED` | No document in this review's basis states whether published values may later change. An absence of documented revision is not evidence of stability. |
| `CONTRADICTED` | A documented revision policy is contradicted by another document or by observed published data. |

### COMPLETENESS_AND_MISSINGNESS

> Are omissions, withholding, exclusions and censoring documented, and is their effect on the published subset bounded?

**Why this is reliability.** A published subset assembled by a documented rule and one assembled by an undocumented one are different measurements. Where missingness is not random, it can move a summary without moving any single value.

**Not to be confused with** relevance, which asks whether the evidence bears on the Claim at all. This asks what the source left out of what it did publish.

| state | what it looks like |
|---|---|
| `DOCUMENTED_AND_BOUNDED` | The documents state which observations are excluded and the reviewer can say what the exclusion does and does not affect. |
| `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` | Exclusion or withholding is documented as possible and its extent is not established. |
| `PARTIALLY_DOCUMENTED` | Some exclusions are documented and the reviewer can name a class of omission the documents do not address. |
| `NOT_ESTABLISHED` | No document in this review's basis addresses what is omitted from the published set. |
| `CONTRADICTED` | A documented exclusion rule is contradicted by another document or by observed published data. |

### SOURCE_SIDE_CHECKABILITY

> Can a person go to the source and inspect the published observations this proposition rests on?

**Why this is reliability.** `claim-epistemic-semantics-v1.md` §2 makes this the test of an OBSERVED proposition. A measurement nobody outside this deployment can re-inspect is one whose failures nobody outside this deployment can find.

**Not to be confused with** SROS-internal lineage. Whether OUR pipeline can recover which records fed a Signal is a precondition for reviewing at all -- its absence is a hard stop, not a low value -- while this asks what the SOURCE exposes.

| state | what it looks like |
|---|---|
| `DOCUMENTED_AND_BOUNDED` | The source publishes the individual observations, addressably, and the documents say for how long. |
| `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` | The observations are inspectable and how long they remain so is not established. |
| `PARTIALLY_DOCUMENTED` | The source exposes an aggregate that can be re-requested but not the individual observations behind it. |
| `NOT_ESTABLISHED` | No document in this review's basis establishes what the source exposes for inspection. |
| `CONTRADICTED` | Documented availability is contradicted by another document or by observed behaviour. |

## 4. What was rejected, and why

Reliability sits beside relevance, directness, extraction confidence and freshness in `q = min(components)`. A rubric that quietly re-scored one of them would make a single weakness count twice.

| candidate | verdict | reason |
|---|---|---|
| `MEASUREMENT_TO_PROPOSITION_FIT` | **BELONGS_TO_OTHER_COMPONENT** | How directly a measurement supports a Claim is `directness`, which is already a component of `q = min(components)`. Scoring it here would make one weakness count twice. The reliability-native residue is not a gradient at all: the scope is measurement CROSSED WITH proposition, so a proposition asking more than the measurement observes is a mis-specified scope rather than a low value -- reclassified as a hard stop. |
| `CLASSIFICATION_DEPENDABILITY` | **FOLDED_INTO_ANOTHER_DIMENSION** | Where a proposition names a source-native class, that classification IS part of what is measured, so it is assessed on the existing dimensions in its own right rather than given a dimension of its own. A separate classification dimension would be a rubric shaped around one publisher's taxonomy, which is the TED-specific scoring table this rubric must not be. |
| `KNOWN_FAILURE_MODES` | **REJECTED_AS_DUPLICATE_QUESTION** | Every failure mode a reviewer finds lands under one of the accepted dimensions, so scoring it separately counts the same finding twice. It is kept as a required ENUMERATION the reviewer produces, attached to the dimension it belongs to. |
| `RESIDUAL_UNKNOWN` | **REJECTED_AS_DUPLICATE_QUESTION** | This is the `NOT_ESTABLISHED` state plus the materiality test, not a sixth question. Made a dimension, it would need its own states, and the state of an unknown is that it is unknown. |
| `REVIEWER_CONFIDENCE_FIELD` | **REJECTED_AS_DUPLICATE_QUESTION** | A separate reviewer-confidence field would be a second answer to a question the dimension profile already answers: basis completeness is READ OFF the profile rather than asked again. Two fields answering one question eventually disagree, and then a reader has to decide which is the real one. |
| `SOURCE_REPUTATION` | **BELONGS_TO_OTHER_COMPONENT** | It belongs to no component. A publisher's standing is not a property of a measurement, and a reliability derived from it is the per-source coefficient ADR-026 exists to prevent. |

## 5. Hard stops

Each of these makes a numeric judgement **unavailable**, however strong the rest — because the reliability question has no answer in that situation, not because the answer would be low.

- **`MEASUREMENT_SEMANTICS_NOT_ESTABLISHED`** — `MEASUREMENT_DEFINITION` is `NOT_ESTABLISHED`. If nothing establishes what is measured, there is no measurement for a value to be about. A low number here would assert that we know it is undependable, and we do not know anything.
- **`PROPOSITION_EXCEEDS_MEASUREMENT`** — The proposition asserts something the measurement does not observe. The scope is mis-specified, and the repair is to the proposition or the scope. A discounted reliability would let an over-reaching Claim keep standing with a smaller number attached.
- **`AUTHORITATIVE_DOCUMENTS_CONTRADICT`** — Any dimension is `CONTRADICTED` and the conflict is unreconciled. A value chosen across an unreconciled contradiction turns a conflict into a number, and the number is then the only thing anyone reads.
- **`SOURCE_OBSERVATIONS_NOT_RECOVERABLE`** — The Evidence rows in scope cannot be traced back to the observations the source published. The review would have no object. This is about OUR lineage, and it is a precondition rather than a dimension.

## 6. Material unknowns

An unknown is MATERIAL when its resolution could reasonably change the reviewer's assessment of how dependable this measurement is for this proposition. It is not material merely because something is undocumented: most things are undocumented, and a rubric that blocked on every one of them would never permit a judgement about anything.

For each thing the documents do not establish, the reviewer answers: *Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?* — `YES` / `NO` / `UNSURE`.

**A material unknown does not automatically refuse the review**, and an unknown is not material merely because something is undocumented. Most things are undocumented.

## 7. The numeric-judgement gate

- `NUMERIC_JUDGEMENT_PERMITTED`
- `NUMERIC_JUDGEMENT_NOT_JUSTIFIED`
- `DOCUMENTATION_INSUFFICIENT`
- `REVIEW_BLOCKED_BY_CONTRADICTION`
- `REVIEWER_DISAGREEMENT_UNRESOLVED`

**It is not computed.** Only the hard stops are mechanical. Everything else is the reviewer's, recorded against the profile they just filled in.

**A numeric value is not required.** An outcome other than `NUMERIC_JUDGEMENT_PERMITTED` is a *complete* review: the scope keeps no assessment, the resolver keeps returning `NO_APPLICABLE_ASSESSMENT`, and the Evidence stays `NON_SCORABLE`. That is the designed behaviour.

## 8. The scale

**Recommendation: `KEEP_NUMERIC_FIELD_BUT_REQUIRE_ORDINAL_REVIEW_PROFILE_FIRST`.**

The numeric field stays — no migration, no code change, and the two existing assessments keep their values — and the rubric requires the **ordinal profile to be completed before the number is offered**. The number then summarises a recorded profile, and the profile is what a second reviewer reproduces.

Two anchors, each defined by what the value *does*, never by an adjective:

- **`1.0`** — Reliability imposes no limit on this Evidence. In `q = min(components)`, this value can never be the limiting component, so the Evidence is bounded only by relevance, directness, extraction confidence and freshness.
  - Justified when: Every dimension is `DOCUMENTED_AND_BOUNDED` and no material unknown remains. Reviewers should expect this to be close to unreachable in practice, and that is the point rather than a defect.
- **`0.0`** — The measurement cannot dependably support this proposition. `q` becomes 0 and the Evidence contributes nothing.
  - Justified when: The reviewer has established a failure mode that defeats the proposition, and can name it. **This is a positive finding and is not the same as having no assessment**: absence means nobody judged, and 0.0 means somebody judged and found the measurement unable to bear the weight.

**There are no intermediate anchors.** Nothing in this repository anchors the absolute scale — the reliability contract forbids threshold labels for that reason, and Mission 1.37 found only the ordinal construct defined. An intermediate anchor would have to be invented, and inventing one is replacing arbitrary numbers with different arbitrary numbers.

## 9. Disagreement between reviewers

| state | |
|---|---|
| `AGREEMENT` | |
| `DISAGREEMENT_OPEN` | |
| `ADJUDICATED` | |
| `IRRECONCILABLE` | |

**Two reviews are never averaged.** The mean of two judgements is a judgement nobody made and nobody can be asked about.

Already answered by the existing architecture:

- The resolver refuses when more than one current assessment matches a scope, so two open answers cannot both be current. The architecture already says two answers are not an answer.
- Supersession is append-only and records who superseded what and why, so a later review replacing an earlier one is representable today and the earlier one is retained.

Not yet representable:

- A second reviewer disagreeing WITHOUT superseding. Today the choice is to supersede -- which asserts the new review is the right one -- or to record nothing, which loses the disagreement.

## 10. An LLM is not an accountable reviewer

**May:**

- retrieve and organise the first-party documents
- extract factual findings and quote them with their section references
- assert `NOT_ESTABLISHED` where no document in the basis addresses a question
- enumerate candidate failure modes for the reviewer to accept or reject
- prepare a worksheet with every judgement field blank

**May not:**

- assign any review state other than `NOT_ESTABLISHED`
- answer whether an unknown is material
- answer the numeric-judgement gate
- choose a reliability value, a range, or an anchored state
- supply or infer a reviewer identity
- adjudicate a disagreement between reviewers

## 11. The worksheet

| field | filled by |
|---|---|
| **scope** — The exact five-part reliability scope. | `SOFTWARE_FACT` |
| **measurement** — What the source publishes, as its documents define it. | `SOFTWARE_FACT` |
| **proposition** — What the Claim asserts, in its own wording. | `SOFTWARE_FACT` |
| **documentary_basis** — The retrieved documents and their findings. | `SOFTWARE_FACT` |
| **dimension_findings** — The factual findings under each dimension, quoted from those documents. | `SOFTWARE_FACT` |
| **dimension_states** — The review state you assign to each dimension. | `REVIEWER_JUDGEMENT` |
| **material_unknowns** — For each thing the documents do not establish: is it material? | `REVIEWER_JUDGEMENT` |
| **hard_stops_triggered** — Which hard stops, if any, you find to be triggered. | `REVIEWER_JUDGEMENT` |
| **numeric_judgement_gate** — Is a numeric reliability judgement justified for this scope? | `REVIEWER_JUDGEMENT` |
| **reliability** — Only if the gate is PERMITTED: the value on [0.0, 1.0]. | `REVIEWER_JUDGEMENT` |
| **rationale** — Why, against the profile above. | `REVIEWER_JUDGEMENT` |
| **stated_limitation** — What the value is discounted for. | `REVIEWER_JUDGEMENT` |
| **reviewed_by** — Who is accountable for this judgement. | `REVIEWER_JUDGEMENT` |
| **reviewed_at** — When the judgement was made. | `REVIEWER_JUDGEMENT` |

**No field is prefilled with a reliability value**, and there is no other slot on the worksheet where one could go.

## 12. Reproducibility

A second qualified reviewer, given the same scope, the same documentary basis and the same rubric version, must be able to follow the first reviewer's reasoning. **Perfect agreement is not required. Traceability is.** The minimum record:

- the exact five-part scope
- the rubric id and version the review was performed under
- the documentary basis, each document with its section reference and retrieval date
- the review state assigned to every dimension
- every material unknown, with the reviewer's materiality answer
- the numeric-judgement gate outcome
- the rationale and the stated limitation
- the reviewer's identity

## 13. The two existing assessments

Applied **structurally** and not re-reviewed. Neither value, rationale, limitation, version nor basis row is changed, and neither was used to derive an anchor.

| scope | verdict | dimensions reached | not addressed |
|---|---|---|---|
| `source_reported_procurement_value_contrast` | **PARTIALLY_REPRESENTABLE** | `MEASUREMENT_DEFINITION`, `SOURCE_SIDE_VALIDATION`, `COMPLETENESS_AND_MISSINGNESS` | `HISTORICAL_MUTABILITY`, `SOURCE_SIDE_CHECKABILITY` |
| `platform_counted_content_request_change` | **PARTIALLY_REPRESENTABLE** | `MEASUREMENT_DEFINITION`, `SOURCE_SIDE_VALIDATION`, `HISTORICAL_MUTABILITY`, `COMPLETENESS_AND_MISSINGNESS` | `SOURCE_SIDE_CHECKABILITY` |

- **`source_reported_procurement_value_contrast`** — Three of five dimensions are recoverable from what the reviewer wrote, in their own words and without interpretation. Two were not considered, which is not a criticism of the review: no rubric existed to ask about them. This is exactly the shape the rubric is meant to remove.
- **`platform_counted_content_request_change`** — Four of five, and the fourth is the interesting one. HISTORICAL_MUTABILITY was derived for this rubric from the open question in the TED convergent packet, and this reviewer had already written it down unprompted for a different source months earlier. That is corroboration that the dimension is real rather than invented -- bounded by the fact that both reviews have the same reviewer, so it is not independent in the strong sense.

**Combined: `HISTORICAL_REVIEW_MISSING_RUBRIC_FIELDS`.** Both reviews are PARTIALLY_REPRESENTABLE and neither can record which procedure produced it, because no column exists for that. Nothing was rewritten: the two values, their rationales, their limitations, their versions and their basis rows are untouched, and a review performed before a rubric existed is not made invalid by the rubric arriving.

## 14. Rubric provenance

**`RELIABILITY_RUBRIC_PROVENANCE_MODEL_GAP`.** epistemic.reliability_assessments has no column naming the review procedure that produced a value. A future assessment therefore cannot say, in queryable form, that it was made under this rubric at this version.

A reliability basis row names a retrieved document ABOUT THE MEASUREMENT. The rubric is the procedure the reviewer followed, not evidence about the source, and filing it as a basis row would inflate the documentary basis of every future assessment with a document that says nothing about the publisher.

**Narrowest repair, recommended and not performed:** Two nullable TEXT columns, review_rubric_id and review_rubric_version, written only by assessments created after adoption and never backfilled. Nullable because the two existing rows legitimately predate the rubric, and backfilling them would fabricate a provenance that does not exist.

**Materiality.** It restricts rather than breaks reproducibility. A completed worksheet plus the rationale still lets a second reviewer follow the first one's reasoning, which is what §17 requires; what cannot be done today is ASK the database which assessments were made under which procedure.

---

## 15. Worked example — the TED convergent scope

The rubric was frozen before it met this scope, and the application stops at the first judgement.

```text
source_id         ted-eu
resource_id       notices/eforms-contract-and-award
record_kind_id    procurement_notice
claim_type        OBSERVED
proposition_kind  source_published_classification_value_contrast_witnessed
```

**6 Evidence rows across 4 Claims**, resolver `NO_APPLICABLE_ASSESSMENT`.

### Factual findings, by dimension

**`MEASUREMENT_DEFINITION`**

- The eForms SDK 1.15.1 business-term definition defines BT-161 as the value of all contracts awarded in the notice, including options and renewals.
- The field repository records BT-161 at notice level, non-repeatable, with a companion currency field.
- The proposition names a source-native classification division, and the classification is assigned by the contracting authority to its own contract.

**`SOURCE_SIDE_VALIDATION`**

- Sixty business rules in the SDK govern where BT-161 may appear.
- All sixty are presence, absence or notice-type constraints; none concerns whether the stated amount is correct.
- The amount is supplied by the contracting authority.

**`HISTORICAL_MUTABILITY`** — state `NOT_ESTABLISHED`

- No document in this review's basis states whether a published notice may later be corrected, amended or superseded in this resource.
- No document in this review's basis states whether an assigned classification code may change after publication.

**`COMPLETENESS_AND_MISSINGNESS`**

- BT-195 to BT-198 document that a result value may be lawfully withheld, with a justification and a later publication date.
- How often notices in the reviewed classification withhold their result values is not measurable from the source's own documentation.
- Under the convergent existential proposition, withholding cannot falsify the claim, which is a different relationship from the one it has to a claim about a named cohort.

**`SOURCE_SIDE_CHECKABILITY`**

- The individual notices behind each witness are recoverable through SROS lineage and are addressable at the source.
- No document in this review's basis states how long a published notice remains retrievable.

Only `NOT_ESTABLISHED` is filled in above, and only where the claim is about what this review's basis contains. **Every other state is yours.**

### Material unknowns — materiality is the reviewer's

**`HISTORICAL_MUTABILITY`** — whether the source permits a published BT-161 value to be corrected, and whether a corrected notice supersedes an earlier one in the reviewed resource

> Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?

```text
YES / NO / UNSURE   ______
```

**`MEASUREMENT_DEFINITION`** — whether an assigned classification code may change after publication

> Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?

```text
YES / NO / UNSURE   ______
```

**`COMPLETENESS_AND_MISSINGNESS`** — how often notices in the reviewed classification withhold their result values

> Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?

```text
YES / NO / UNSURE   ______
```

**`SOURCE_SIDE_CHECKABILITY`** — how long a published notice remains retrievable at the source

> Could resolution of this unknown reasonably alter how dependable this measurement is for this proposition?

```text
YES / NO / UNSURE   ______
```

### Not a rubric input

- Engineering validation. The currency and amount-scope cohort guards, the semantic reproduction of the historical division-90 Signal, and the determinism of the convergence contract establish that the implementation does what its specification says, and nothing about how dependable the source's published amounts are.
- Observation overlap. DISJOINT witnesses are temporally separated, not epistemically independent, and independence is a different Evidence component.
- The existing assessment at another proposition kind. It belongs to a different scope, it is not a baseline, and it may not be copied.

### Your judgement

```text
SUFFICIENT_FOR_NUMERIC_JUDGEMENT   UNANSWERED
dimension_states                   ______________________________
material_unknowns                  ______________________________
hard_stops_triggered               ______________________________
numeric_judgement_gate             ______________________________
reliability                        ______________________________
rationale                          ______________________________
stated_limitation                  ______________________________
reviewed_by                        ______________________________
reviewed_at                        ______________________________
```

**No value is supplied, suggested or implied**, and no reviewer is inferred from a git author, a PR author, an OS username, an existing assessment or a conversation.

