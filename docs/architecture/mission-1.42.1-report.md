# Mission 1.42.1 — Second Pilot Operator Reliability Decision V1

**Primary outcome: `OPERATOR_CONFIRMATION_REQUIRED`** (§33 B).

Everything the mission could legitimately do is done. The one step left is the
one that must not be automated: **a person typing the confirmation.**

**0 ReliabilityAssessments persisted. 0 model calls. 0 network requests. Every
canonical research counter unchanged.** The schema now *can* record which review
procedure produced a value; no value has been recorded.

Artifacts:
[second-pilot-convergent-operator-reliability-review-v1.md](../data/second-pilot-convergent-operator-reliability-review-v1.md)
·
[.json](../data/second-pilot-convergent-operator-reliability-review-v1.json)
·
[second-pilot-convergent-reliability-resolution-v1.json](../data/second-pilot-convergent-reliability-resolution-v1.json)
(pre-persistence baseline)
· migration
`0032_reliability_review_rubric_provenance.sql`.

---

## The command the operator runs

```bash
cd C:\Users\Hp\Documents\startup-research-os; $env:DATABASE_URL=(Select-String -Path infrastructure\compose\.env -Pattern '^DATABASE_URL=').Line.Split('=',2)[1]; uv run python infrastructure/scripts/record_reliability_assessment.py --review-file docs/data/second-pilot-convergent-operator-reliability-review-v1.json --apply
```

It prints the scope, the value, the rubric and the four basis rows, then asks for
a typed confirmation. Then:

```bash
cd C:\Users\Hp\Documents\startup-research-os; $env:DATABASE_URL=(Select-String -Path infrastructure\compose\.env -Pattern '^DATABASE_URL=').Line.Split('=',2)[1]; uv run python infrastructure/scripts/report_convergent_reliability_resolution.py --link-review
```

---

## Why the mission stops here

`record_reliability_assessment.py` asks for the confirmation through `input()`
and refuses on `EOFError` with *"no terminal to confirm on. A reliability
assessment is a human decision and this is not a step a pipeline runs"*.

The brief supplies the operator's **values**; it does not supply the operator's
**keystroke**, and §7 says so explicitly: *"the application-level confirmation
mechanism remains authoritative"*. Piping the string in, patching `isatty`, or
writing the row with hand-written SQL would each produce an assessment whose
`reviewed_by` names a person who did not type it — which is precisely the failure
the whole reliability contract exists to prevent. **A guard removed to make a
pipeline pass is a guard that never was**, and Mission 1.36.1 met this same wall
and stopped at it too.

The dry run has been executed and validates cleanly, so what remains is the
confirmation and nothing else:

```text
scope.proposition_kind   source_published_classification_value_contrast_witnessed
origin                   HUMAN_REVIEW
version                  1
reviewed_by              thibchm
reliability              0.55
review rubric            human-reliability-assessment-rubric@1.0.0
basis                    4 row(s), 4 document-backed
```

---

## §34 — Final report

Questions whose answers depend on persistence are marked **pending
confirmation**; each names the artifact that will carry the measured answer.

### Baseline and the schema repair

**1. Did the live baseline match Mission 1.42a?** **Yes**, every counter, checked
against the deployment before any work: 325/325, 33, 37, 38, 39, 2/6, 1/1/7,
0 independence groups, 0 Evidence with a reliability column set, 29 sources, and
`scoring.scores` absent.

**2. Was rubric provenance schema support added?** **Yes.**

**3. Exact migration?** `0032_reliability_review_rubric_provenance.sql`: two
nullable `TEXT` columns, `review_rubric_id` and `review_rubric_version`, plus
`reliability_assessments_rubric_provenance_check` requiring **both halves or
neither** — an id with no version names a moving target, and a version with no id
names nothing. No `NOT NULL`, no `DEFAULT`, and the file contains no `UPDATE`,
`INSERT` or `DELETE`. Applied; the same rule is enforced a second time in
`ReliabilityAssessment.__post_init__`, so an object cannot be built half-provenanced
either.

**4. Were historical assessments backfilled?** **No**, and the columns are
nullable so that they need not be. Verified against the deployment after
applying: both existing rows read `review_rubric_id = NULL`,
`review_rubric_version = NULL`. **That is the true answer for them** — they were
reviewed before the rubric existed, and writing an id onto a review that did not
use one would fabricate the provenance this column was added to record.

**The basis table was considered and rejected as the place for this.** A basis
row names a retrieved document *about the measurement*; the rubric is the
procedure the reviewer followed. Filing it there would inflate every future
assessment's documentary basis with a document that says nothing about the
publisher.

**5. Exact rubric id/version?** `human-reliability-assessment-rubric` / `1.0.0`,
read from the rubric module rather than typed — the review artifact declares it
and a validator refuses any other value.

### The operator's review, carried verbatim

**6. Exact ordinal profile?**

| dimension | state |
|---|---|
| `MEASUREMENT_DEFINITION` | `PARTIALLY_DOCUMENTED` |
| `SOURCE_SIDE_VALIDATION` | `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` |
| `HISTORICAL_MUTABILITY` | `NOT_ESTABLISHED` |
| `COMPLETENESS_AND_MISSINGNESS` | `PARTIALLY_DOCUMENTED` |
| `SOURCE_SIDE_CHECKABILITY` | `DOCUMENTED_AND_BOUNDED` |

**7. Exact material-unknown answers?** `YES`, `YES`, `NO`, **`UNSURE`** — in that
order, for correction/supersession, post-publication classification change,
withholding frequency, and long-term retrievability. **`UNSURE` is preserved as
`UNSURE`**: not `YES`, not `NO`, not *low confidence*, not `0.5`. The rubric
permits it because a reviewer who cannot yet tell whether an unknown matters has
said something real, and converting it would discard exactly that.

**8. Exact numeric gate?** `NUMERIC_JUDGEMENT_PERMITTED`. Recorded as the
operator's decision and **not recomputed from the ordinal states** — the rubric
defines the gate as judgement rather than an arithmetic function, and nothing in
this mission derives it. No hard stop was triggered.

**9. Exact human reliability value?** **`0.55`**. Not rounded, not rescaled, not
derived, not averaged. A test asserts it is neither `0.5` nor `0.65` nor their
mean — the three shapes a nudging bug would take.

**10. Exact reviewer?** `thibchm`.

**11. Exact rationale?** Persisted verbatim; three paragraphs resting on the
first-party TED/eForms documentation, stating that the measurement definition and
completeness behaviour are only partially documented, that **source-side
validation does not establish that a published amount is factually correct**, and
that the correction/supersession semantics and possible classification changes
are treated as material unknowns. Not strengthened: a test asserts it nowhere
says the amounts are correct or the Claim probably true.

**12. Exact stated limitation?** Persisted verbatim, keeping all three unresolved
points: correction/amendment/supersession of a published BT-161 or its CPV
classification; conformance rather than factual correctness; and **long-term
retrievability remaining unresolved** — the `UNSURE` answer is carried into the
limitation rather than quietly resolved.

### The scope

**13. Exact five-part reliability scope?**

```text
source_id         ted-eu
resource_id       notices/eforms-contract-and-award
record_kind_id    procurement_notice
claim_type        OBSERVED
proposition_kind  source_published_classification_value_contrast_witnessed
```

**14. How many Evidence rows does it cover?** **6.**
**15. How many Claims?** **4.**
**16. How many multi-Evidence Claims?** **2.**

**The scope was not narrowed**, and that was a live temptation: the second pilot
produced the two multi-Evidence division-92 Claims, and it would have been easy
to write the assessment as though it were about them. It is not. The scope
carries no classification division and no currency, so this one judgement binds
**divisions 90 and 92** and **EUR and SEK** alike. Narrowing it would have
changed the reliability architecture rather than the value.

**17. How many basis rows were persisted?** **Pending confirmation — 4 will be**,
determined from the prepared packet rather than hard-coded, and all four
document-backed.

**18. Which documents?** The four Mission 1.42 prepared, all first-party eForms
SDK 1.15.1 and all already held: the BT-161 business-term definition
(`MEASUREMENT_METHODOLOGY`), the `fields.json` BT-161-NoticeResult entry
(`SOURCE_DOCUMENTATION`), the 60 business rules none of which concerns
correctness (`KNOWN_LIMITATION`), and BT-195–BT-198 on withholding
(`KNOWN_LIMITATION`).

Mission 1.42 classified three as `REUSED` and the withholding document as
`PARTIALLY_APPLICABLE`. **All four are persisted**, because that verdict is about
how much *weight* the reviewer gives it under an existential proposition, not
about whether the document belongs. **Nothing new was fetched** — fetching to
inflate a basis count is not review — and **no SROS engineering validation appears
among them**, which a test enforces.

### Persistence

**19–20, 24–29, 32–44, 47.** **Pending confirmation.** The dry run establishes
version `1` with no supersession, origin `HUMAN_REVIEW`, and the rubric
provenance recorded. The measured answers land in
`second-pilot-convergent-reliability-resolution-v1.json`, which is already
written and running: the pre-persistence baseline records **0 of 6 rows resolved,
0 scorable, `max(members)` receiving 0**, which is precisely what the assessment
will change.

**21. Did existing TED 0.5 change?** **No.**
**22. Did Wikimedia 0.65 change?** **No.**
**23. Were either superseded?** **No**, and they cannot be by this: a different
`proposition_kind` is a different reliability question, so `_next_version` finds
no same-scope current row and produces version 1 rather than a supersession. The
dry run confirms it.

**26–27. Any leak?** The pre-persistence run reports **6 leak checks, 0 leaks**,
and a unit test exercises the near miss through the **real resolver in both
directions**: the new scope and the detailed scope share `source_id`,
`resource_id`, `record_kind_id` and `claim_type`, differ only on
`proposition_kind`, and neither reaches the other. **No source-level fallback and
no nearest-match logic exists to reach for.**

**28. Are persisted Evidence reliability columns still NULL?** **Yes, 0 of 39**,
and they will stay NULL: the resolution script feeds the *resolved* value into the
aggregator and writes nothing to `scoring.evidence`. Reliability binds late
(ADR-026 Decision 2) so that a score names the assessment and version it used
rather than carrying a copy that can outlive it.

**30. `raw_evidence_count` for each?** **2 and 2**, measured now.
**31. `scorable_evidence_count` for each?** **0 and 0** today, for the reason
this mission exists. Expected 2 and 2 after confirmation — **measured, not
hard-coded**; the reporter computes it from the real aggregator.

**34. Was independence still UNKNOWN?** **Yes**, on all six rows.
**35. Were independence groups created?** **No, 0** — and none will be. Both
witnesses of each Claim have `DISJOINT` observation membership, which is temporal
separation and **not epistemic independence**, so the conservative rule collapses
them into one unknown-provenance group. That is correct, and it means the
diagnostic must never be reported as corroboration.

### What did not move

**45. Is the diagnostic explicitly UNCALIBRATED?** **Yes** — a four-part banner,
`UNCALIBRATED | DIAGNOSTIC ONLY | NOT AN OPPORTUNITY SCORE | NOT A PROBABILITY`,
on the artifact and on every Claim inside it.

**46. Explicitly NOT AN OPPORTUNITY SCORE?** **Yes**, same banner, and nothing is
persisted.

**48. Did calibration feasibility move 0 → 2 scorable multi-Evidence Claims?**
**Pending confirmation**; the audit is rerun after persistence. The structural
corpus will not move — reliability review creates no research rows.

**49. Contradiction cases?** **`NO_REAL_CONTRADICTION_CASE_YET`**, and none was
manufactured.
**50. Established-independence cases?** **0.**
**51. Temporal cases?** **0.** Every Claim in the corpus is `EVERGREEN`.

**52. D-03 state?** Reported separately, not collapsed:

| blocker | state |
|---|---|
| 1. reliability definition and authority | **RESOLVED** |
| 2. reviewed reliability for scopes in use | **improves on confirmation** — the convergent scope gains one; other in-use scopes remain unreviewed |
| 3. a `CALIBRATED` aggregation profile | **OPEN** |
| 4. an authorised temporal half-life | **OPEN** |
| 5. fitted EvidenceLevel thresholds | **OPEN** |

**53. Were calibration labels created?** **No.**
**54. Were parameters fitted?** **No.**
**55. Did any profile become CALIBRATED?** **No.** `REFERENCE_PROFILE_V1` is
still `UNCALIBRATED`. **This mission supplies one reliability input; it does not
calibrate the framework**, and a value arriving does not make the equations that
consume it fitted.

**56. Was another Opportunity created?** **No.** 1 / 1 / 7, untouched.
**57. Was ranking performed?** **No.**
**58. Were model calls made?** **0.** 0.00 USD. The reliability decision was
supplied by a person and there was nothing for a model to do.
**59. Was research data acquired?** **No. 0 network requests.** TED was not
queried, CPV was not queried, and no witness was created.
**60. Is Problem-Family still PARKED?** **Yes.**

**61. Exact canonical counters before/after?**

| counter | before | now | after confirmation |
|---|---:|---:|---|
| RawRecords / NormalizedRecords | 325 / 325 | 325 / 325 | unchanged |
| Signals / Claims / ClaimRevisions | 33 / 37 / 38 | 33 / 37 / 38 | unchanged |
| Evidence | 39 | 39 | unchanged |
| Evidence with reliability written | 0 | 0 | **0** (late binding) |
| ReliabilityAssessments | 2 | **2** | **3** |
| Reliability basis rows | 6 | **6** | **10** |
| EvidenceIndependenceGroups | 0 | 0 | unchanged |
| Opportunities / revisions / links | 1 / 1 / 7 | 1 / 1 / 7 | unchanged |
| Embeddings / Scores | 0 / 0 | 0 / 0 | unchanged |
| Sources / Scope relations | 29 / 0 | 29 / 0 | unchanged |

**62. Recommended next mission?** After the operator confirms and the resolution
report is run: **Mission 1.43 — Calibration Reference Corpus Expansion V1**, and
**not** calibration. Two multi-Evidence Claims sharing one reliability assessment,
with independence UNKNOWN, no contradiction case, no established independent
corroboration, no temporal Claim and one source family is not a dataset. The
corpus needs those shapes to exist before human pairwise calibration labels are
worth creating. **Not started automatically.**

---

## Tests

**36 new tests**, `unittest.TestCase` (this package is discovered with `unittest
discover`). 813 across 8 packages now.

**One pre-existing test was re-pointed rather than deleted.**
`test_the_binding_records_everything_needed_to_reconstruct_the_number` pinned the
exact key set of `ReliabilityBinding.to_json()`, and the binding gained the two
provenance keys. The property it asserts — *the binding names everything needed
to reconstruct the number* — is exactly why the keys were added: **which
procedure produced a value is part of reconstructing it.** Same repair shape as
Missions 1.31.1, 1.32, 1.38, 1.40 and 1.41.

**And one new test needed the `testing-strategy.md` §23 fix on its first run.** A
scan asserting the migration declares no `NOT NULL` column failed on the `CHECK`
constraint that necessarily contains `IS NOT NULL` — the constraint doing the
work. It now scans the `ADD COLUMN` lines, which is what the rule was about.
