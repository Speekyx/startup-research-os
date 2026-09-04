# Mission 1.42.1 — Second Pilot Operator Reliability Decision V1

**Primary outcome: `SECOND_PILOT_OPERATOR_RELIABILITY_DECISION_PERSISTED`**
(§33 A), reached by way of **`OPERATOR_CONFIRMATION_REQUIRED`**: the mission
stopped at the typed-confirmation guard, the operator ran the command, and
**`max(members)` received two real items for the first time in this project's
history.**

**Two counters moved and thirteen did not.** ReliabilityAssessments 2 → **3**,
basis rows 6 → **10**. Everything else — RawRecords, NormalizedRecords, Signals,
Claims, ClaimRevisions, Evidence, independence groups, Opportunities, Embeddings,
Scores, sources, scope relations, and `scoring.evidence.reliability` — unchanged.

Artifacts:
[operator review](../data/second-pilot-convergent-operator-reliability-review-v1.md)
·
[resolution and diagnostic](../data/second-pilot-convergent-reliability-resolution-v1.json)
· migration `0032_reliability_review_rubric_provenance.sql`.

---

## §34 — Final report

### Baseline and the schema repair

**1. Did the live baseline match Mission 1.42a?** **Yes**, every counter, checked
before any work.

**2. Was rubric provenance schema support added?** **Yes.**

**3. Exact migration?** `0032_reliability_review_rubric_provenance.sql`: two
nullable `TEXT` columns, `review_rubric_id` and `review_rubric_version`, plus
`reliability_assessments_rubric_provenance_check` requiring **both halves or
neither** — an id with no version names a moving target, and a version with no id
names nothing. No `NOT NULL`, no `DEFAULT`, and no `UPDATE`, `INSERT` or `DELETE`
anywhere in the file. The same rule is enforced a second time in
`ReliabilityAssessment.__post_init__`, so an object cannot be built
half-provenanced either.

**4. Were historical assessments backfilled?** **No.** Verified against the
deployment after applying: both existing rows read `review_rubric_id = NULL`,
`review_rubric_version = NULL`. **That is the true answer for them** — they were
reviewed before the rubric existed, and writing an id onto a review that did not
use one would fabricate the provenance this column was added to record.

**The basis table was considered and rejected as the place for this.** A basis
row names a retrieved document *about the measurement*; the rubric is the
procedure the reviewer followed. Filing it there would inflate every future
assessment's documentary basis with a document that says nothing about the
publisher.

**5. Exact rubric id/version?** `human-reliability-assessment-rubric` / `1.0.0`,
read from the rubric module rather than typed.

### The operator's review, carried verbatim

**6. Exact ordinal profile?**

| dimension | state |
|---|---|
| `MEASUREMENT_DEFINITION` | `PARTIALLY_DOCUMENTED` |
| `SOURCE_SIDE_VALIDATION` | `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` |
| `HISTORICAL_MUTABILITY` | `NOT_ESTABLISHED` |
| `COMPLETENESS_AND_MISSINGNESS` | `PARTIALLY_DOCUMENTED` |
| `SOURCE_SIDE_CHECKABILITY` | `DOCUMENTED_AND_BOUNDED` |

**7. Exact material-unknown answers?** `YES`, `YES`, `NO`, **`UNSURE`** — for
correction/supersession, post-publication classification change, withholding
frequency, and long-term retrievability. **`UNSURE` is preserved as `UNSURE`**:
not `YES`, not `NO`, not *low confidence*, not `0.5`, and it is carried into the
stated limitation rather than quietly resolved.

**8. Exact numeric gate?** `NUMERIC_JUDGEMENT_PERMITTED`, recorded as the
operator's decision and **not recomputed from the ordinal states**. No hard stop
was triggered.

**9. Exact human reliability value?** **`0.55`**. Not rounded, not rescaled, not
derived, not averaged. A test asserts it is neither `0.5` nor `0.65` nor their
mean — the three shapes a nudging bug would take.

**10. Exact reviewer?** `thibchm`.

**11. Exact rationale?** Persisted verbatim. It states that the measurement
definition and completeness behaviour are only partially documented, that
**source-side validation does not establish that a published amount is factually
correct**, and that correction/supersession semantics and possible classification
changes are treated as material unknowns. Not strengthened: a test asserts it
nowhere says the amounts are correct or the Claim probably true.

**12. Exact stated limitation?** Persisted verbatim, keeping all three unresolved
points, including **long-term retrievability remaining unresolved**.

### The scope

**13. Exact five-part reliability scope?**

```text
source_id         ted-eu
resource_id       notices/eforms-contract-and-award
record_kind_id    procurement_notice
claim_type        OBSERVED
proposition_kind  source_published_classification_value_contrast_witnessed
```

**14. Evidence rows covered?** **6.** **15. Claims?** **4.** **16.
Multi-Evidence Claims?** **2.**

**The scope was not narrowed, and that was the live temptation.** The second
pilot produced the two multi-Evidence division-92 Claims, so writing the
assessment as though it were about them would have felt natural and would have
been wrong. The scope carries no classification division and no currency, so this
one judgement binds **divisions 90 and 92** and **EUR and SEK**.

**17. How many basis rows were persisted?** **4** — measured from the workflow,
not predeclared. Total 6 → **10**.

**18. Which documents?** The four Mission 1.42 prepared, all first-party eForms
SDK 1.15.1 and all already held: the BT-161 definition
(`MEASUREMENT_METHODOLOGY`), the `fields.json` BT-161-NoticeResult entry
(`SOURCE_DOCUMENTATION`), the 60 business rules none of which concerns
correctness (`KNOWN_LIMITATION`), and BT-195–BT-198 on withholding
(`KNOWN_LIMITATION`).

Mission 1.42 called three `REUSED` and the withholding document
`PARTIALLY_APPLICABLE`. **All four were persisted**, because that verdict is
about how much *weight* a reviewer gives it under an existential proposition, not
about whether the document belongs. **Nothing new was fetched**, and **no SROS
engineering validation is among them**, which a test enforces.

### Persistence

**19. Exact new assessment id/version?** `d1afa4be-8462-4461-be20-112cdc55ee7e`,
**version 1**.

**20. Origin?** `HUMAN_REVIEW`.

**21. Did existing TED 0.5 change?** **No.** **22. Did Wikimedia 0.65 change?**
**No.** **23. Were either superseded?** **No** — `superseded_at` is NULL on both.
A different `proposition_kind` is a different reliability question, so
`_next_version` found no same-scope current row and produced version 1 rather
than a supersession.

**24. Did all six convergent Evidence rows resolve?** **Yes, 6 of 6.**

**25. Exact binding?** Every row: assessment `d1afa4be…` version 1, origin
`HUMAN_REVIEW`, reviewer `thibchm`, reliability `0.55`, rubric
`human-reliability-assessment-rubric@1.0.0`.

**26. Any leak to detailed TED Evidence?** **No.** **27. Any other reliability
leak?** **No — 9 leak checks, 0 leaks.** Three current assessments is a third
more ways to leak, and each probe varies only `proposition_kind` while holding
every other field byte-identical.

**28. Are persisted Evidence reliability columns still NULL?** **Yes, 0 of 39.**
Six rows resolve a number and **not one stores it** — reliability binds late
(ADR-026 Decision 2), so a score names the assessment and version it used rather
than carrying a copy that can outlive it.

### The first real scorable multi-Evidence aggregation

**29. Did both real multi-Evidence Claims become scorable?** **Yes.**

**30. `raw_evidence_count`?** **2** and **2**.
**31. `scorable_evidence_count`?** **2** and **2** — measured, not hard-coded.

**32. Did `max(members)` receive 2 items?** **Yes, for the first time on real
canonical data.** Mission 1.41 had `raw = 2` and `scorable = 0`, so the grouping
arithmetic never ran; it does now.

**33. How many runtime support groups?** **One per Claim**, kind `UNKNOWN`,
2 members, `collapsed_member_count` 1.

**34. Was independence still UNKNOWN?** **Yes**, on all six rows.
**35. Were independence groups created?** **No, 0.** `DISJOINT` observation
membership is temporal separation, **not epistemic independence**, so the
conservative rule collapses both witnesses into one unknown-provenance group.
That is correct, and it is why this must never be reported as corroboration.

**36. Exact q components?** relevance `1.0`, directness `1.0`, reliability
`0.55`, extraction confidence `1.0`, freshness `1.0` (every Claim `EVERGREEN`).

**37. Exact q?** **`0.55`** on every scorable row.
**38. Limiting component?** **`reliability`**, on all of them — `q =
min(components)` and every other factor is `1.0`, so the score is a restatement
of one human judgement.

**39. Support strength?** `0.55`. **40. Contradiction strength?** `0.0`.

**41. Four masses?** supported `0.55`, contradicted `0.0`, conflict `0.0`,
uncertainty `0.45`.

**42. Evidence Score?** `100 × supported_mass` = **55.0**, and it is not a
probability.

**43. EvidenceLevel?** **1, "Weak Signal"**, on `2 scorable supporting record(s)`.

**44. Level blockers?** Three, and the first is the one that matters: *"Repeated
Signal needs 2 supporting groups of established independence, found 0 (plus 1
unknown-provenance group, which does not count)"*. Then the `MARKET_ACTIVITY`
gate and the `DIRECT_VALIDATION` gate. **Reliability reaches none of them.**

**45. Is the diagnostic explicitly UNCALIBRATED?** **Yes** — a four-part banner,
`UNCALIBRATED | DIAGNOSTIC ONLY | NOT AN OPPORTUNITY SCORE | NOT A PROBABILITY`,
on the artifact and on every Claim inside it. **46. Explicitly NOT AN OPPORTUNITY
SCORE?** **Yes**, and **0 scores were persisted**; `scoring.scores` still does not
exist.

**47. Comparison to reliability pass-through?**
**`IDENTICAL_TO_RELIABILITY_PASS_THROUGH`** on both Claims — support strength
`0.55`, baseline `0.55`.

**And that is not a failure.** Both Evidence rows share one reliability
assessment, independence is UNKNOWN so they collapse into one group, and
`group_strength = max(members)` of two identical `q` values is that value. The
full aggregator and Mission 1.37's B-2 baseline agree **because the corpus gives
them nothing to disagree about.** What is new is not a bigger number: it is that
**the real grouping logic ran on real data at all**. Claiming an evidence-strength
gain here would be claiming corroboration from two witnesses of unestablished
provenance.

### Calibration and D-03

**48. Did calibration feasibility move 0 → 2 scorable multi-Evidence Claims?**
**Yes.** And the structural corpus did not move — Claims 37, Evidence 39, Claims
with more than one Evidence 2 — because reliability review creates no research
rows.

**The target variable gained a third value.** Distinct support strengths went
from `{0.5, 0.65}` to **`{0.5: 6, 0.55: 4, 0.65: 18}`** across 28 scorable
claims. All three are still reviewed reliability values and `reliability` is
still the limiting component on **28 of 28**, so Mission 1.37's finding stands:
the target is reviewed reliability, and the leakage rule still cannot split this
corpus usefully.

**49. Contradiction cases?** **`NO_REAL_CONTRADICTION_CASE_YET`** — 0, and none
was manufactured. **50. Established-independence cases?** **0.** **51. Temporal
cases?** **0**; every Claim is `EVERGREEN` and none carries a `claim_feature`.

**52. D-03 state?** Reported separately, not collapsed:

| blocker | state |
|---|---|
| 1. reliability definition and authority | **RESOLVED** |
| 2. reviewed reliability for scopes in use | **PARTIAL**, improved — three scopes reviewed, others in use still unreviewed |
| 3. a `CALIBRATED` aggregation profile | **OPEN** |
| 4. an authorised temporal half-life | **OPEN** |
| 5. fitted EvidenceLevel thresholds | **OPEN** |

**53. Were calibration labels created?** **No.** **54. Were parameters fitted?**
**No.** **55. Did any profile become CALIBRATED?** **No.**
`REFERENCE_PROFILE_V1` is still `UNCALIBRATED`. **This mission supplied one
reliability input**, and a value arriving does not make the equations that consume
it fitted.

### What did not move

**56. Was another Opportunity created?** **No.** 1 / 1 / 7, untouched.
**57. Was ranking performed?** **No.**
**58. Were model calls made?** **0.** 0.00 USD.
**59. Was research data acquired?** **No. 0 network requests.**
**60. Is Problem-Family still PARKED?** **Yes.**

**61. Exact canonical counters before/after?**

| counter | before | after |
|---|---:|---:|
| RawRecords / NormalizedRecords | 325 / 325 | 325 / 325 |
| Signals / Claims / ClaimRevisions | 33 / 37 / 38 | 33 / 37 / 38 |
| Evidence | 39 | 39 |
| Evidence with reliability written | 0 | **0** |
| ReliabilityAssessments | 2 | **3** |
| Reliability basis rows | 6 | **10** |
| EvidenceIndependenceGroups | 0 | 0 |
| Opportunities / revisions / links | 1 / 1 / 7 | 1 / 1 / 7 |
| Embeddings / Scores | 0 / 0 | 0 / 0 |
| Sources / Scope relations | 29 / 0 | 29 / 0 |

**62. Recommended next mission?** **Mission 1.43 — Calibration Reference Corpus
Expansion V1**, and **not** calibration. The diagnostic above is the argument for
it: two Claims sharing one assessment, agreeing exactly with a pass-through
baseline, with independence UNKNOWN, no contradiction case, no established
corroboration, no temporal Claim and one source family, is not a dataset. Those
shapes have to exist before human pairwise calibration labels are worth creating.
**Not started automatically.**

---

## A defect this mission found by running its own output

`report_convergent_reliability_resolution.py` read `group.members`; the attribute
is **`member_evidence_ids`**. The pre-persistence run passed because
`max(..., default=0)` never evaluated its generator over an empty group list, so
the wrong name sat there looking fine until the first Claim became scorable and
the operator hit it.

**That is the third time this repository has met the same shape** — Mission
1.36's invalid basis types, Mission 1.36.1's `binding.assessment_version`, and
now this. **A branch no data has ever entered is not tested by a passing suite**,
and each of these was found by trying to use the output rather than by running
the tests. Fixed, and the corrected run also reports `collapsed_member_count`.

## Tests

**68 in this mission's suite**, 828 across 8 packages,, `unittest.TestCase` (the package is discovered with
`unittest discover`), of which 32 assert the measured post-persistence state from
the checked-in resolution artifact rather than from a database — CI's integration
job starts from an empty one.

**Four pre-existing tests were re-pointed rather than deleted**, and the pattern
is by now the most repeated one in this repository — *a count that can
legitimately grow is deployment state* (`testing-strategy.md` §68), repaired the
same way in Missions 1.31.1, 1.32, 1.38, 1.40 and 1.41.

- `test_the_binding_records_everything_needed_to_reconstruct_the_number` pinned
  the exact key set of `ReliabilityBinding.to_json()`. The property it asserts —
  *the binding names everything needed to reconstruct the number* — is exactly
  why the two provenance keys were added.
- Mission 1.37's `test_the_target_variable_has_two_values…` pinned
  `{0.5, 0.65}`. What that mission established survives a third reviewed scope:
  the target variable is **reviewed reliability and nothing else**, because
  reliability limits every scorable claim. It now asserts that, over any number
  of values.
- Mission 1.37's `test_the_assessments_themselves_were_not_touched` pinned two
  assessments. The property is that calibration **consumes** reviewed reliability
  and may not refit it, and that the profile stays `UNCALIBRATED` however many
  exist.
- Mission 1.38's `test_no_reliability_assessment_was_created` pinned the global
  total. **What belongs to that mission is its own record of having created
  none**; the live total belongs to whichever mission last changed it.

**A test asserting a count forever is a test asserting the project never
progresses**, and this mission is the one that made three of them false.

**And one new test needed the `testing-strategy.md` §23 fix on its first run.** A
scan asserting the migration declares no `NOT NULL` column failed on the `CHECK`
constraint that necessarily contains `IS NOT NULL` — the constraint doing the
work. It now scans the `ADD COLUMN` lines, which is what the rule was about.
