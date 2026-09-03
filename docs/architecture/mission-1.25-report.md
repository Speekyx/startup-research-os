# Mission 1.25 — Recurring Problem Family Inference V1

**Outcome: `MODEL_EVALUATION_FAILED` on the frozen criterion — against both the
provisional reference AND, in the addendum below, against human ground truth for
the scored holdout.** The classifier
found **zero** of the four `SAME_FAMILY` references in the scored holdout. No
production inference, no Signal, no INFERRED Claim, no Evidence.

**And unlike Mission 1.24, this failure means something.** That evaluation
*passed* a criterion its holdout could not test. This one had four positives in
the split that decides, so the criterion could distinguish a working classifier
from a cautious one — and it did.

| | Before | After |
|---|---|---|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / ClaimRevisions / Evidence | 26 / 26 / 26 / 26 | **26 / 26 / 26 / 26** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 | **0** |
| Registered sources | 29 | **29** |
| **Family model calls / tokens / cost** | 0 | **20 / 128 590 in, 12 334 out / 0.38 USD** |

---

## The eight questions §15 asks

**1. Is exact problem equivalence production-ready?**
**No**, inherited from Mission 1.24 and untouched. Its relation was not weakened,
not redefined and not made more permissive; its evaluation history is unchanged.

**2. Is recurring problem-family inference technically implemented?**
**Yes.** `problem-family-rubric@1.0.0`, `docker-problem-family-candidates@1.0.0`,
`semantic-problem-family@1.0.0`, a classifier, a frozen criterion, and 74 tests
on the fake provider. The whole path ran end to end against the real route.

**3. Was a real scored evaluation performed?**
**Yes.** 20 pairs, both splits, through the SROS Gateway on the approved route,
0.38 USD.

**4. Did the scored holdout contain positive SAME_FAMILY references?**
**Yes.** 4 against the provisional reference, and **2 against human ground truth**
after the operator reviewed the split (see the addendum). Both clear the
criterion's minimum of 2. **This is the thing Mission 1.24 lacked**, and having it
is why this mission produced an answer.

**5. Can an always-DIFFERENT classifier pass?**
**No.** `min_true_same = 1` makes both constant classifiers fail by construction,
`defeats_a_constant_classifier` computes that from the numbers, and tests score a
constant-DIFFERENT and a constant-ABSTAIN classifier and watch them fail. The
clause then caught the real run.

**6. Were any production problem-family Signals created?**
**0.** Production is gated on evaluation success and the evaluation failed.

**7. Are any resulting Claims OBSERVED?**
**No** — none were created at all, of any type.

**8. Was cross-source convergence performed?**
**No.**

---

## The result

| | development | holdout |
|---|---|---|
| labelled and predicted | 10 | 10 |
| reference SAME / DIFFERENT / UNCERTAIN | 5 / 4 / 1 | 4 / 6 / 0 |
| model SAME_FAMILY / DIFFERENT / ABSTAIN | 1 / 8 / 1 | 0 / 9 / 1 |
| **true SAME_FAMILY** | 1 | **0** |
| false SAME_FAMILY | 0 | **0** |
| missed SAME_FAMILY | 4 | **4** |
| agreements | 6 / 10 | 5 / 10 |
| **outcome** | passed | **`MODEL_EVALUATION_FAILED`** |

Holdout confusion: `SAME→DIFFERENT_PROBLEM_FAMILY` 4, `DIFFERENT→DIFFERENT_PROBLEM_FAMILY` 5,
`DIFFERENT→ABSTAIN` 1.

**Across all 20 pairs the model said `SAME_PROBLEM_FAMILY` once.** That one was
`78089171::78098380` — **the rubric's own qualifying worked example, quoted in
its instructions by id**. It is pinned to development precisely because it is
in-sample, and it is the only positive the classifier ever produced. Development
"passed" on the strength of it, which is exactly why the split exists.

**Zero false positives, again, and again it is nearly free.** A classifier
answering DIFFERENT to everything scores the same zero. The difference from
Mission 1.24 is that this criterion asked a second question the constant
classifier cannot answer, and the answer was 0.

---

## What the reference set is, and is not

| | |
|---|---|
| reference origin | **`AI_ASSISTED_PROVISIONAL`** (GPT-5.6 Sol) |
| `human_ground_truth` | **NOT_ESTABLISHED** |
| labels | 20 — 9 SAME_FAMILY, 10 DIFFERENT_FAMILY, 1 UNCERTAIN |
| split | 10 development / 10 holdout |

**This is provisional AI-assisted reference agreement, not human semantic
validation.** The labels were written blind — no model had seen any pair under
this rubric and no prediction existed — and they were never sent to the
classifier, which is what makes them valid for scoring. What was measured is
**agreement between two assistants**, and every evaluation result carries
`human_ground_truth_established: false` plus a note saying so in its own output.

Had the criterion passed, the distinction would have mattered more than it does
here: a technical pass against a provisional reference would still leave human
semantic validation NOT_ESTABLISHED. It failed, so both are open.

---

## Where the disagreement is, and it is one-directional

> **Revised by the addendum.** Human review of the holdout showed that three of
> these "missed positives" were the provisional reference being generous, not the
> classifier being tight. The pattern below survives at **half the size**. The
> section is kept as written because it is what the provisional scoring said.

**Every disagreement is the model refusing a family the reference asserted.**
Eight missed positives across both splits; zero cases of the model asserting a
family the reference denied. The classifier is not noisy — it is *strictly more
conservative than the reference*, and by a wide margin.

Two readings, and this evaluation cannot separate them:

- **the rubric is too strict**, and its insufficient-alone list — which forbids
  shared technology, shared tags, shared symptom and shared component category —
  rules out most of what the reference reviewer was willing to call a family;
- **the reference is too generous**, treating shared technology as shared goal in
  a way the rubric explicitly forbids.

**The most diagnostic single case is the rubric's own borderline example.**
`78093369::78105004` — psycopg failing to build on alpine, and a rails image
failing to install `libc-bin`. The rubric states DIFFERENT_PROBLEM_FAMILY, argues
that *my Docker build fails while installing a dependency* is too broad to be one
family, and the model agreed with it. **The reference said SAME_FAMILY.** So the
rubric's author and its reference reviewer disagree about a pair the rubric uses
to *define its own boundary*, and the model sided with the rubric. Three of the
four rubric-quoted examples agreed; this one did not.

That is a finding about the **granularity**, not about the model, and it cannot
be settled by rerunning anything. It needs a person.

---

## What was deliberately not done

**The rubric was not widened after seeing the results.** §10 anticipates exactly
this temptation: eight missed positives are eight Signals that a looser
insufficient-list would have produced. Widening now would be fitting the
definition to the outcome, and the resulting families would rest on nothing.

**The criterion was not altered.** It was frozen before any family prediction
existed and is the criterion this result is scored under, in the direction that
made the mission fail. Mission 1.24 established the discipline in the flattering
direction; this is the same rule in the costly one.

**No prompt development happened.** The prompt was authored once and frozen; the
development split was scored to observe and the holdout once against the same
version. No retry loop, no prompt rescue.

**No production run, no Signal, no Claim, no Evidence, no Opportunity.** No
transitive closure was available to invent, because there is nothing to close
over.

---

## Two findings worth carrying forward

**The Gateway's strictness caught a real defect, and it was not injection.** One
call in twenty returned a structured block whose first key was the literal string
`"parameter name"` instead of `"decision"`; the other four fields were correct.
The Gateway refused rather than guessing, which is right — ADR-006 treats a
schema failure as a possible injection signal and does not route around it.

The runner now **retries once against the same route and counts it**, which is
not the fallback ADR-006 forbids: that is routing to a *different* provider and
comparing outputs across models. One retry occurred, it succeeded, and the count
is in the run record because a route that needs retries is a fact about the
route.

**Candidate generation was inspected rather than assumed** (§6).
`docker-lexical-candidates@1.0.0` is **not** too narrow: it qualifies 731 of 3 916
pairs, reaches 84 of 89 observations, and had surfaced Mission 1.24's one SAME
pair by shared tags alone. Its **ordering** was wrong — it scores a shared
diagnostic by raw length, which put the runc trio at ranks 1–3 and the
family-shaped pair at 39. So the qualifying predicate is imported unchanged, with
a test asserting both relations consider the same pairs, and only the ordering is
versioned: the **rarest** shared tag rather than the sum (summing rewards sharing
a whole stack, which the rubric forbids; the summing variant ranked the
family-shaped pair 315th), and a shared diagnostic at **weight zero** rather than
a small constant, because a constant would claim it contributes a little and
Mission 1.20 refutes that.

And the honest limit, stated rather than hidden: **rarity measures specificity,
not concern.** `github` and `docker-desktop` are rare technologies;
`environment-variables` is a rare concern. Nothing lexical separates them without
a hand-written list nobody reviewed, so the ordering mixes both and the reviewer
separates them.

---

## Quality

Nine validators, six generated-doc `--check` steps, `ruff`, `mypy`, both CI
inline greps, `migrate --plan`, and both suites. **The zero-dependency boundary
was verified explicitly** (§14), since Mission 1.24 shipped a `pytest` import into
a suite that runs under stdlib `unittest`: every package in `run_python_tests.py`
was checked for a pytest import, and none has one.

Command matrix run locally:

```bash
python infrastructure/scripts/run_python_tests.py        # stdlib unittest, no pytest
python infrastructure/scripts/run_pytest_suites.py       # pytest, database-backed
python infrastructure/scripts/render_family_batch.py --check
python -m ruff check . && python -m ruff format --check .
python -m mypy <the CI target list>
```

---

## Architectural consequence

**The family relation is implemented, evaluated and did not pass**, which is a
better position than Mission 1.24 left: that mission could not tell whether its
classifier worked, and this one can — the answer is that under this rubric, on
this corpus, against this reference, it finds essentially nothing.

**The open question is now sharply posed and is a question for a person.** Every
disagreement is one-directional, and the rubric and its reference disagree about
the rubric's own boundary example. Either the granularity is drawn too tight for
opportunity research, or the reference is calling shared technology a shared
goal. **A model cannot settle that**, and neither can a larger batch of the same
provisional labels: it needs a human judgement about how wide a problem family
should be before one intervention stops being describable.

**SROS still has no validated recurring-problem semantic evidence from Stack
Exchange** — bounded, as always, to this relation, this rubric and this candidate
set. It does have 26 canonical Evidence rows from other source families, so
cross-source convergence is not blocked by an absence of Evidence in general; it
is blocked by the absence of *this* evidence, which is a narrower and more useful
statement.


---

# ADDENDUM — the holdout re-scored against human labels

**Added after the frozen holdout was independently reviewed by the human
operator.** Nothing frozen was touched: the rubric, prompt, candidate set, split,
model predictions and acceptance criterion are unchanged, **no model call was
made**, and the original scoring against the provisional reference is preserved
unmodified as historical data. This is an additional provenance-aware result.

## Provenance, and it is MIXED

| | |
|---|---|
| scored holdout reference | **`HUMAN_OPERATOR`** — human ground truth **established for this split** |
| development reference | still `AI_ASSISTED_PROVISIONAL` |
| **full 20-pair reference set** | **MIXED — must not be reported as fully human ground truth** |

## The result, against the same frozen criterion

| clause | required | actual | |
|---|---|---|---|
| labelled scored pairs | ≥ 8 | **10** | pass |
| human `SAME_FAMILY` in the scored split | ≥ 2 | **2** | pass, at the minimum |
| false `SAME_PROBLEM_FAMILY` | 0 | **0** | pass |
| **true `SAME_PROBLEM_FAMILY`** | **≥ 1** | **0** | **FAIL** |

**`MODEL_EVALUATION_FAILED`, unchanged.** Every precondition the criterion sets
for being *able* to test is now met against human ground truth, and the model
still never produced a single `SAME_PROBLEM_FAMILY` on the holdout.

**Zero false positives is not a pass here and must not be read as one.** That is
the number a classifier hard-coded to answer DIFFERENT also achieves, which is
exactly why the criterion asks a second question. The answer to it is 0.

Confusion, human reference: `DIFFERENT→DIFFERENT_PROBLEM_FAMILY` 5,
`SAME→DIFFERENT_PROBLEM_FAMILY` 2, `UNCERTAIN→ABSTAIN` 1,
`UNCERTAIN→DIFFERENT_PROBLEM_FAMILY` 2. Agreements 6/10.

## What the human review changed, and it is the most interesting part

**Five of the ten labels changed**, and the direction is not what the provisional
scoring implied.

| pair | provisional | human | |
|---|---|---|---|
| `78086323::78097216` | SAME_FAMILY | DIFFERENT_FAMILY | **the model was right** |
| `78096486::78097886` | SAME_FAMILY | DIFFERENT_FAMILY | **the model was right** |
| `78095639::78105296` | DIFFERENT_FAMILY | UNCERTAIN | **the model was right** (it abstained) |
| `78096355::78097579` | DIFFERENT_FAMILY | UNCERTAIN | model still off |
| `78096355::78103879` | DIFFERENT_FAMILY | UNCERTAIN | model still off |

**On three of the five changes the human moved TOWARD the model.** The
provisional reference had called two pairs a family that the operator does not,
and had called one pair decidable that the operator finds undecidable — and the
classifier had already answered DIFFERENT, DIFFERENT and ABSTAIN on those three.

So the Mission 1.25 reading that *the model is strictly more conservative than
the reference* was **half an artifact of the reference**. Against human labels:

- **missed positives fall from 4 to 2**;
- agreements rise from 5/10 to 6/10;
- and the model's single abstention turns out to be correct.

**The one-directional pattern survives, at half the size.** Two genuine
human-confirmed families were still called DIFFERENT: `78086387::78097071` and
`78089075::78089578`. The classifier is more conservative than a person, and by
less than it looked.

## What this does and does not settle

**Settled**: the earlier reading that the rubric might be far too strict is
weakened. Three of the four "missed positives" that motivated it were the
provisional reference being generous, not the rubric being tight. That is a
finding about **AI-assisted references**, and it generalises beyond this mission:
a provisional reference agreed with a second assistant's looser instinct, and a
person disagreed with both.

**Not settled**: two real families remain unfound, so the classifier still cannot
demonstrate it can identify one. And with exactly two positives in the scored
split — the bare minimum the criterion accepts — this holdout can distinguish a
working classifier from a constant one, and little more. A larger human-labelled
holdout is what would make the next answer worth more than this one.

**Unchanged**: no production inference, no Signal, no INFERRED Claim, no
Evidence, no Opportunity, and no rubric or criterion was altered after seeing
either scoring.
