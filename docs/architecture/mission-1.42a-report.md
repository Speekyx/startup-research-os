# Mission 1.42a — Human Reliability Assessment Rubric V1

**Primary outcome: `HUMAN_RELIABILITY_RUBRIC_READY`** (§37 A).

**Secondary finding: `RELIABILITY_RUBRIC_PROVENANCE_MODEL_GAP`** — recorded, with
the narrowest repair recommended and deliberately not performed (§25).

**0 ReliabilityAssessments created or modified. 0 network requests. 0 model
calls. Every canonical research counter unchanged. No TED reliability answered.**

Artifacts:
[human-reliability-assessment-rubric-v1.md](../data/human-reliability-assessment-rubric-v1.md),
[human-reliability-assessment-rubric-v1.json](../data/human-reliability-assessment-rubric-v1.json).
The rubric itself is code —
`packages/evidence-reliability/python/sros_evidence_reliability/rubric.py` —
rendered deterministically with a `--check` step now in CI.

---

## §0 — What already existed, and what did not

| already defined | where |
|---|---|
| what reliability means | `evidence-reliability-contract-v1.md` §1 |
| the exact scope a value binds to | ADR-026 Decision 1 |
| who may establish one | contract §5, three closed origins |
| what a value must rest on | contract §6, document-backed basis rows |
| that a value must state its limitation | contract §6 |
| that absence is legitimate | contract §9, resolver `NO_APPLICABLE_ASSESSMENT` |
| late binding and recorded provenance | ADR-026 Decision 2 |
| supersession and versioning | contract §7 |
| the operator tool that refuses to help with the number | `record_reliability_assessment.py` |

**Not defined anywhere: the step from documented facts to a number.** The review
guide comes closest — write the failure mode down first, then apply two
discipline checks — but those checks test whether a number is *about the right
thing*, not how to *arrive at* it. Nothing was duplicated; this mission adds only
the missing middle.

---

## §38 — Final report

### The gap

**1. What methodological gap existed after Mission 1.42?** A reviewer who had
read every document and written the failure mode down still had no procedure that
made `0.45` rather than `0.65` defensible. The architecture defined the question,
the scope, the reviewer and the evidence, and then handed over a blank numeric
field.

```text
DOCUMENTED FACTS  ->  [ nothing ]  ->  HUMAN JUDGEMENT  ->  Assessment
```

**2. Why would choosing a value directly be arbitrary?** Because nothing in the
repository anchors the absolute scale. `scoring-framework-v1.1.md` fixes 0–100
and says nothing about what makes 65 correct rather than 55; the reliability
contract forbids threshold labels for that reason; and Mission 1.37 found that
only the **ordinal** construct is defined. Two reviewers reading identical
documents had no shared referent, so the number carried a precision the reasoning
behind it did not have.

**3. Exact reliability definition?** Unchanged, and quoted rather than restated:
*"How dependable is this kind of measurement, for this kind of proposition?"* A
test asserts the string appears verbatim in the contract.

**4. Which concepts are excluded?** Ten, named in the rubric: the probability the
Claim is true; publisher reputation; legal permission; Opportunity quality;
market size or commercial value; whether SROS's downstream conclusions are right;
independence; extraction confidence; directness; freshness.

### The dimensions

**5. Which assessment dimensions were accepted?** Five.

| dimension | the question |
|---|---|
| `MEASUREMENT_DEFINITION` | Does first-party documentation define what is measured? |
| `SOURCE_SIDE_VALIDATION` | What does the source itself validate before publishing? |
| `HISTORICAL_MUTABILITY` | Can a published measurement later be corrected or superseded? |
| `COMPLETENESS_AND_MISSINGNESS` | Are omissions, withholding and censoring documented and bounded? |
| `SOURCE_SIDE_CHECKABILITY` | Can a person go to the source and inspect the observations? |

**6. Which candidate dimensions were rejected?** Six.

**7. Why?**

- **`MEASUREMENT_TO_PROPOSITION_FIT` → `BELONGS_TO_OTHER_COMPONENT`.** This is
  `directness`, already a component of `q = min(components)`; scoring it here
  would make one weakness count twice. Its reliability-native residue is not a
  gradient at all — the scope is measurement *crossed with* proposition, so a
  proposition asking more than the measurement observes is a **mis-specified
  scope**, and it was reclassified as a hard stop.
- **`CLASSIFICATION_DEPENDABILITY` → `FOLDED_INTO_ANOTHER_DIMENSION`.** Where a
  proposition names a source-native class, that classification *is* part of what
  is measured, so it is assessed on the five dimensions in its own right. A
  dimension of its own would have been a rubric shaped around one publisher's
  taxonomy — the TED-specific scoring table the mission forbids.
- **`KNOWN_FAILURE_MODES` → `REJECTED_AS_DUPLICATE_QUESTION`.** Every failure
  mode lands under one of the five, so a sixth slot would count the same finding
  twice. Kept as a required enumeration attached to its dimension.
- **`RESIDUAL_UNKNOWN` → `REJECTED_AS_DUPLICATE_QUESTION`.** This is the
  `NOT_ESTABLISHED` state plus the materiality test. As a dimension it would need
  its own states, and the state of an unknown is that it is unknown.
- **`REVIEWER_CONFIDENCE_FIELD` → `REJECTED_AS_DUPLICATE_QUESTION`** (§12). A
  separate field would be a second answer to a question the dimension profile
  already answers: basis completeness is **read off** the profile rather than
  asked again. Two fields answering one question eventually disagree.
- **`SOURCE_REPUTATION` → `BELONGS_TO_OTHER_COMPONENT`.** It belongs to no
  component. A publisher's standing is not a property of a measurement, and a
  value derived from it is the per-source coefficient ADR-026 exists to prevent.

**8. Exact ordinal states?** One vocabulary across all five dimensions, with an
observable definition per dimension:

| state | rank |
|---|---:|
| `DOCUMENTED_AND_BOUNDED` | 3 |
| `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` | 2 |
| `PARTIALLY_DOCUMENTED` | 1 |
| `NOT_ESTABLISHED` | **none** |
| `CONTRADICTED` | **none** |

**9. How is UNKNOWN represented?** As `NOT_ESTABLISHED`, **with no ordinal
rank**. That is the structural form of the rule rather than a warning in prose: a
state with no rank cannot be interpolated, averaged, or read as the bottom of a
scale. `CONTRADICTED` is likewise off the order — a contradiction is a blocker,
not a weak position on a line.

**10. Does UNKNOWN lower the value automatically?** **No.** Nothing maps any
state to any number. The module contains **no arithmetic at all** — a test parses
it and asserts there is no `BinOp`, no `sum`, no `min`, no `max`, no `round` —
and the ranks are declared never to be summed.

**11. What is a material unknown?** One whose *resolution could reasonably change
the reviewer's assessment of dependability for this proposition*. Explicitly not:
merely undocumented. Most things are undocumented, and a rubric that blocked on
every one of them would never permit a judgement about anything. The reviewer
answers `YES / NO / UNSURE` per unknown, and **`UNSURE` is a real answer** and a
legitimate reason for the gate not to be `PERMITTED`.

**12. Which conditions block numeric judgement?** Four hard stops, each because
the reliability question has *no answer* in that situation — never because the
answer would be low: `MEASUREMENT_SEMANTICS_NOT_ESTABLISHED`,
`PROPOSITION_EXCEEDS_MEASUREMENT`, `AUTHORITATIVE_DOCUMENTS_CONTRADICT`,
`SOURCE_OBSERVATIONS_NOT_RECOVERABLE`. **A material unknown is deliberately not
among them** (§13).

**13. What is the numeric-judgement gate?** Five outcomes —
`NUMERIC_JUDGEMENT_PERMITTED`, `NUMERIC_JUDGEMENT_NOT_JUSTIFIED`,
`DOCUMENTATION_INSUFFICIENT`, `REVIEW_BLOCKED_BY_CONTRADICTION`,
`REVIEWER_DISAGREEMENT_UNRESOLVED` — and **it is not computed**. Only the hard
stops are mechanical.

**14. Is a numeric value required for every review?** **No.** An outcome other
than `PERMITTED` is a *complete* review: the scope keeps no assessment, the
resolver keeps returning `NO_APPLICABLE_ASSESSMENT`, and the Evidence stays
`NON_SCORABLE`.

### The scale

**15. Which strategy was selected?**
**`KEEP_NUMERIC_FIELD_BUT_REQUIRE_ORDINAL_REVIEW_PROFILE_FIRST`** (§29 C).

**16. Why?**

- **Against A (continuous with semantic anchors):** reproducibility would need
  intermediate anchors, inventing them is forbidden by §8 and §9, and any
  adjective attached to one would be the threshold vocabulary the reliability
  contract refuses.
- **Against B (anchored discrete):** the grid would have to be invented today; it
  could not represent the existing `0.65`; and §11 forbids deriving anchors from
  historical values. It is also premature — with two data points there is no
  evidence about what granularity reviewers can actually resolve.
- **Against D (defer numeric entirely):** it would strand two legitimate existing
  assessments and block scoring for evidence already reviewed, while buying
  nothing the gate does not already provide — refusing a number is available
  under C too.
- **For C:** no migration, no code change, the resolver and `q = min(components)`
  untouched, both historical values kept. The reviewer completes the **ordinal
  profile before the numeric field is offered**, so the number summarises a
  recorded profile and the profile is what a second reviewer reproduces.

**17. Are semantic anchors used?** Two, and each is defined by **what the value
does in the arithmetic** rather than by an adjective — which is what keeps them
out of the threshold vocabulary the contract forbids.

**18. Exact anchors?**

- **`1.0`** — reliability imposes no limit: in `q = min(components)` it can never
  be the limiting component. Justified only when every dimension is
  `DOCUMENTED_AND_BOUNDED` and no material unknown remains. **Reviewers should
  expect this to be close to unreachable, and that is the point.**
- **`0.0`** — the measurement cannot dependably support this proposition; `q`
  becomes 0. **This is a positive finding and is not the same as having no
  assessment**: absence means nobody judged; `0.0` means somebody judged and
  found the measurement unable to bear the proposition.

**There are no intermediate anchors**, deliberately.

**19. Were arbitrary weights introduced?** **No.**
**20. Is a weighted sum used?** **No.** Asserted three ways: no scoring
identifier in the module's AST, no arithmetic operator of any kind, and no key
anywhere in the rendered artifact whose name contains *weight*, *points*,
*score*, *total* or *coefficient*.

**21. Are reviewer confidence and reliability separate?** They are not two
fields, on purpose. Basis completeness is derivable from the dimension profile,
so a separate reviewer-confidence field would be a second answer to one question.
The number is never overloaded with it.

### Reviewers

**22. How is reviewer disagreement represented?** Four states — `AGREEMENT`,
`DISAGREEMENT_OPEN`, `ADJUDICATED`, `IRRECONCILABLE` — and **two reviews are
never averaged**: the mean of two judgements is a judgement nobody made and
nobody can be asked about.

**The existing architecture already answers two of the questions**, and the
rubric records that rather than reinventing it. The resolver **refuses** when
more than one current assessment matches a scope, so two open answers cannot both
be current — the architecture already says two answers are not an answer, and
while a disagreement is open the honest state is the *absence* of an assessment.
Supersession is append-only with `superseded_by` and `superseded_reason`, so a
later review replacing an earlier one is representable today and the earlier one
is retained.

**What is not representable:** a second reviewer disagreeing *without*
superseding. Today the choice is to supersede — which asserts the new review is
the right one — or to record nothing, which loses the disagreement. Multi-review
persistence is not implemented here; only the semantics are defined.

**23. Can an LLM be the reviewer?** **No.** There is no `MODEL_GUESSED` origin,
and closure is what makes that enforceable rather than merely stated.

**24. Can an LLM prepare factual material?** Yes: retrieve and organise
documents, extract and quote findings, enumerate candidate failure modes, prepare
a blank worksheet, and assert **`NOT_ESTABLISHED`** — the one state that is a
checkable claim about what the review's basis *contains* rather than a judgement
about whether what is documented is *enough*. It may not assign any other state,
answer materiality, answer the gate, choose a value or a range, supply a
reviewer, or adjudicate.

### Provenance

**25. Is rubric provenance storable?** **No — `RELIABILITY_RUBRIC_PROVENANCE_MODEL_GAP`.**
`epistemic.reliability_assessments` has no column naming the procedure that
produced a value.

**The basis table is not the answer.** A basis row names a retrieved document
*about the measurement*; the rubric is the procedure the reviewer followed. Filing
it there would inflate the documentary basis of every future assessment with a
document that says nothing about the publisher.

**Narrowest repair, recommended and not performed:** two nullable `TEXT` columns,
`review_rubric_id` and `review_rubric_version`, written only by assessments
created after adoption and **never backfilled** — the two existing rows
legitimately predate the rubric, and backfilling them would fabricate a
provenance that does not exist.

**Why this is a secondary finding and not outcome C:** it *restricts* rather than
breaks reproducibility. A completed worksheet plus the rationale still lets a
second reviewer follow the first one's reasoning, which is what §17 requires.
What cannot be done today is **ask the database** which assessments were made
under which procedure.

**26. Exact rubric id/version?** `human-reliability-assessment-rubric@1.0.0`.

### The two existing assessments

**27. Are they changed?** **No.** Both values, rationales, limitations, versions
and all six basis rows are untouched, and neither was used to derive an anchor.

**28. Can their rationale be represented?** Both are **`PARTIALLY_REPRESENTABLE`**.

| scope | dimensions reached | silent on |
|---|---|---|
| `source_reported_procurement_value_contrast` (0.5) | definition, source-side validation, completeness | mutability, checkability |
| `platform_counted_content_request_change` (0.65) | definition, source-side validation, **mutability**, completeness | checkability |

**The second row is the mission's best evidence that the dimensions are not
invented.** `HISTORICAL_MUTABILITY` was derived here from the open question in
the TED convergent packet — and the Wikimedia reviewer had already written it
down unprompted, months earlier, for a different source: *"does not establish a
complete revision/backfill policy"*. Bounded honestly: both reviews have the same
reviewer, so this is corroboration and not independent replication.

Combined: **`HISTORICAL_REVIEW_MISSING_RUBRIC_FIELDS`**. Neither can record which
procedure produced it. **A review performed before a rubric existed is not made
invalid by the rubric arriving**, and nothing was rewritten.

### The TED worked example

**29. What factual states were populated?** The **factual findings** under all
five dimensions, carried over from Mission 1.42 and quoted from the four held
eForms SDK documents. **One state** was assigned by software —
`HISTORICAL_MUTABILITY = NOT_ESTABLISHED` — and only because it is a claim about
what this review's basis contains.

**30. Which TED fields remain human judgement?** Four dimension states, every
materiality answer, the hard stops triggered, the gate, the reliability, the
rationale, the stated limitation, the reviewer and the timestamp.

**31. Which material unknowns remain?** Four: whether a published BT-161 may be
corrected and whether a corrected notice supersedes an earlier one; whether an
assigned classification code may change after publication; how often notices in
the reviewed classification withhold their result values; how long a published
notice remains retrievable.

**32. Was the correction/supersession unknown preserved?** **Yes**, as the first
entry, under `HISTORICAL_MUTABILITY`.

**33. Did software answer its materiality?** **No.** The question is printed with
`YES / NO / UNSURE` blank.

**34. Did software recommend a TED reliability value?** **No.**
**35. A range?** **No.**
**36. Was a reviewer inferred?** **No** — not from a git author, a PR author, an
OS username, an existing assessment, or this conversation.

### What did not move

**37. Was any ReliabilityAssessment persisted?** **No.** 2 before, 2 after; 6
basis rows before and after.

**38. Did any canonical counter change?** **No.** RawRecords and
NormalizedRecords 325/325, Signals 33, Claims 37, ClaimRevisions 38, Evidence 39,
EvidenceIndependenceGroups 0, Opportunities 1 with 1 revision and 7 links,
Embeddings 0, Scores 0, sources 29, scope relations 0.

**39. Were any model calls made?** **0.** 0.00 USD.
**40. Was any research data acquired?** **No.** The renderer reads the rubric
module and the checked-in review packet, and touches no network and no database
— which is why its `--check` can run in CI at all.

**41. Is `REFERENCE_PROFILE_V1` still `UNCALIBRATED`?** **Yes.** A rubric governs
how a human assesses a reliability **input**; calibration governs how aggregation
parameters are fitted (§30). They are different acts and this is not one of them.

**42. Is Problem-Family still PARKED?** **Yes.**

**43. Is the new TED operator worksheet ready?** **Yes** — §15 of the rubric
document, covering the operator's A–I, kept in the rubric artifact rather than as
a third file so the two cannot drift.

**44. Recommended next action?** **A human review of the TED convergent scope
under this rubric.** Per §39 the mission stops here and Mission 1.42.1 is not
started.

---

## §31 — Room for a future empirical origin

`CALIBRATED_EMPIRICALLY` already exists as an origin and requires a named
calibration dataset. Nothing in this rubric closes that door: a future empirical
assessment for a scope would **supersede** a `HUMAN_REVIEW` one through the
existing versioning, rather than coexist as a second current row — which the
resolver would refuse anyway.

And the recommendation is what makes that future measurable. Once several reviews
exist with **recorded ordinal profiles**, it becomes possible to ask whether the
same profile yields the same number across reviewers. That is the evidence that
would justify moving to anchored discrete values, and it does not exist yet. The
prospect of empirical calibration is not a reason to skip the human rubric today:
there is no outcome data to calibrate against, and two data points is not a
dataset.

## Tests

**56 new tests**, `unittest.TestCase` because `run_python_tests.py` discovers
this package with `unittest discover`. 777 across 8 packages now.

The load-bearing ones are structural over the module's AST: no scoring
identifier, **no arithmetic operator of any kind**, no aggregating builtin, no
source id, and no key in the rendered artifact whose name scores anything. One
test had to be repaired for the `testing-strategy.md` §23 shape — a scan for
*weight* failed on the sentence saying a measurement cannot *bear the weight* of
a proposition — and the fix was to scan **field names** rather than prose, which
is what the rule was always about.
