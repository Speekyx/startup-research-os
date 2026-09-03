# Mission 1.27 — Exploratory Problem-Family Classifier V2

**Outcome: `EXPLORATORY_V2_NOT_PROMISING`.**

A candidate was selected on DEVELOPMENT by a rule frozen beforehand, frozen, and
run once on the Mission 1.26 holdout. It produced **0 provisional true SAME
against 4 provisional SAME references**, where the criterion — also frozen
beforehand — required 2.

**Recommendation: `PARK_PROBLEM_FAMILY_CLASSIFIER`.** Production problem-family
inference remains **NOT_AUTHORISED**.

| | |
|---|---|
| logical model evaluations | **88** (72 development + 16 holdout) |
| schema retries | **0** |
| tokens | 622 664 in, 43 486 out |
| **cost** | **1.53 USD** (§8 ceiling 3.00, session ceiling 5.00) |
| canonical research counters | **unchanged** |
| Signals / Claims / Evidence / Opportunities created | **0** |

---

## §0 — Why V1 appeared conservative

### A. Behaviour demonstrated by V1's own outputs

- **17 of 20** decisions were `DIFFERENT_PROBLEM_FAMILY`; 1 SAME, 2 ABSTAIN.
- **15 of 20** carried one reason code: `SAME_TECHNOLOGY_DIFFERENT_GOAL`.
- Its `blocked_goal` fields ran to the 240-character cap and named frameworks,
  ports, package managers and mechanisms.
- Its rationales repeatedly took the form *"Both involve X, **but** the blocked
  goals differ"*, where the difference named was implementation-level: direction
  of traffic, which client, first-deploy versus under-load.
- **On two pairs a human later called SAME, V1's own rationale states the shared
  abstraction and then rejects it.** For `78089075::78089578`: *"both involve a
  client failing to reach a service running inside a Docker container, but the
  specific blocked goals differ substantially."*

That last item is the strongest thing in the record: the model was not failing to
see the abstraction. It saw it, wrote it down, and did not accept it.

### B. Hypotheses, which are not established causes

- **H1** — the comparison happened at the level V1 itself wrote the goals at. An
  unbounded goal field invites implementation detail, and two implementation
  details always differ.
- **H2** — a named reason code for *same technology, different goal* may make
  that an available and comfortable reading.
- **H3** — the rubric's insufficient-alone list is long and emphatic; its
  permissive side (*root causes and fixes may differ*) is present but far less
  prominent.

**None of these is demonstrated**, and no variant below is claimed to have fixed
a cause. They are the reasons the three variants differ in the way they do.

**Confirmed at §0**: production problem-family inference = NOT_AUTHORISED;
Mission 1.25 = `MODEL_EVALUATION_FAILED`; Mission 1.26 =
`REFERENCE_SET_INSUFFICIENT`. None rewritten.

---

## §1–§4 — What V2 changed, and what it did not

**The relation is unchanged.** `problem-family-rubric@1.0.0` was not modified, not
versioned and not widened. All three variants carry it verbatim as trusted
context, and a test asserts it.

The output schema changed: `goal` and `blocker` are **separate** fields, and the
goal is capped at **120 characters** against V1's 240 — the direct counter to the
demonstrated behaviour. A `shared_problem_if_any` field was added so the model
must attempt an abstraction covering both before deciding.

**No numeric confidence is requested.** §3 offers it as one option among several;
the repository's standing invariant is that a self-reported certainty is not a
probability and the only safe handling is to mark it uncalibrated and never do
arithmetic on it — at which point asking buys nothing. That invariant is not this
mission's to change, and the three-way decision with mandatory ABSTAIN already
carries the uncertainty this task can honestly express.

### A leakage channel §4 would have opened

§4 suggests a positive illustration: two clients unable to reach a service hosted
in Docker. **That is the exact abstraction of holdout pair
`78089075::78089578`.** The obvious alternative — the one development SAME pair
of that shape, `78089075::78097003` — shares question **78097003** with holdout
pair `78086387::78097003`.

**The Mission 1.26 split is disjoint by PAIR and not by OBSERVATION.** Over a
fixed 89-question corpus it cannot be otherwise, and it means prompt examples
drawn from development can still carry holdout content. Both candidate examples
were therefore refused; the V2-C illustrations are abstract shapes naming no
corpus question, and a test asserts no variant prompt contains a question id.

---

## §5–§7 — Three variants, one frozen rule

| variant | version | change |
|---|---|---|
| V2-A | 2.0.0 | goal and blocker separated, goal field short |
| V2-B | 2.1.0 | A + required shared-abstraction attempt + one-intervention test |
| V2-C | 2.2.0 | B + explicit *different cause and fix are allowed* reminder |

### Provisional development agreement

**Against an `AI_ASSISTED_PROVISIONAL` reference — not accuracy, not validated
accuracy, not a human benchmark.** The development split holds **2** provisional
SAME examples, so **every positive-performance figure below is extremely
unstable** and no proportion computed from them means anything.

| variant | SAME | DIFF | ABSTAIN | true SAME | false SAME | missed | agreement | cost |
|---|---|---|---|---|---|---|---|---|
| V2-A | 1 | 22 | 1 | **1** | 0 | 1 | 18/24 | $0.413 |
| V2-B | 0 | 23 | 1 | **0** | 0 | 2 | 17/24 | $0.418 |
| V2-C | 1 | 22 | 1 | **1** | 0 | 1 | 18/24 | $0.438 |

**V2-B was ineligible**: zero provisional true SAME. V2-A and V2-C tied on 1 true
and 0 false, tied on unnecessary abstention, and the frozen rule broke the tie on
the simpler procedure. **Selected: V2-A.**

Worth noting: adding the shared-abstraction requirement (B) made the classifier
*more* conservative, not less. Adding the permissive reminder on top (C) restored
it to A's level and no further.

---

## §8 — Cost, and a ceiling made real

Predeclared before any call: provider `anthropic`, model `claude-sonnet-5`,
88 maximum logical evaluations, expected **$1.23**.

**The first hard-maximum estimate was $4.44, above the §8 ceiling of $3.00.** It
assumed every call ran to the adapter's default 4096-token output cap. The
response was to bound the thing rather than argue the bound away:
`max_output_tokens` was set to **1200** for this mission — the V2 schema caps its
fields at 1080 characters and V1 measured about 630 output tokens on the same
shape — which brings the hard maximum to **$1.89**, genuinely under the ceiling.

Actual: **$1.53**, 0 retries, 0 schema failures. Gateway authorization was
resolved before any question text was serialised and was never bypassed.

---

## §9–§11 — Frozen, then run once

`EXPLORATORY_V2_CANDIDATE_FROZEN`: V2-A, prompt `2.0.0`, sha256
`f314a3ad…4eea52` over system text, task text and output schema. A later run
producing a different hash is running a different classifier, whatever its
version string says, and a test asserts the hash still matches the code.

The holdout criterion was recorded **before** the holdout call. Applied:

| clause | required | actual | |
|---|---|---|---|
| non-UNCERTAIN references | ≥ 12 | 15 | ✅ |
| provisional SAME references | ≥ 4 | 4 | ✅ |
| **provisional true SAME** | **≥ 2** | **0** | **❌** |
| provisional false SAME | ≤ 1 | 0 | ✅ |
| not collapsed to one decision | — | 0/15/1 | ✅ |

**`EXPLORATORY_V2_NOT_PROMISING`.** Run once, one variant, no second attempt.

---

## §12 — V1 against V2, descriptively

**A caution first: these are different holdouts.** V1 was scored on Mission
1.25's 10-pair holdout; V2 on Mission 1.26's 16-pair holdout. V1 was never run on
the latter. Nothing below is a controlled comparison.

- **Did V2 begin detecting positive families?** On the holdout, no: 0 of 4. On
  development it found 1 of 2 — the same count V1 managed, though on a different
  pair and for a visibly better reason.
- **Did false SAME assertions appear?** No. Zero across all 88 evaluations.
- **Did ABSTAIN usage change?** No. One abstention in each holdout run.
- **Is any improvement merely general permissiveness?** There is no improvement
  to attribute. V2-A called SAME once in 40 evaluations, V1 once in 20.
- **Do the rationales show the intended abstraction?** Only where it fires. The
  one development SAME reads *"Both involve confusion over how 'localhost'
  resolves across Docker networking boundaries"* — which is the level the rubric
  asks for. But **`shared_problem_if_any` was left empty on 1 of 24 development
  rows and 0 of 16 holdout rows**: the model almost never proposed an abstraction
  at all. It is not rejecting candidate abstractions; it is not generating them.
- **Are failures caused by thin source text?** Not visibly. The four missed
  holdout positives are questions with substantial bodies.

No claim of statistical significance, no calibrated probability, no prevalence.

---

## §13 — No production epistemic rows

| | Before | After |
|---|---|---|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / ClaimRevisions / Evidence | 26 / 26 / 26 / 26 | **26 / 26 / 26 / 26** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 | **0** |
| Registered sources | 29 | **29** |

No recurring-problem Signal, no INFERRED Claim, no Evidence, no
ReliabilityAssessment for this relation, no Opportunity, no Score.

## §15 — Tests

**132 tests** in `packages/semantic-equivalence`, **571** across the
zero-dependency suites, all pytest suites across 8 packages, 0 failures. New
regression tests cover: the three-variant cap, the untouched rubric, ABSTAIN
survival, the absence of a numeric confidence field, the shortened goal field, no
corpus question id in any prompt, a constant-DIFFERENT variant being refused, a
collapse-toward-SAME variant being refused, a total tie-break order, the holdout
criterion's inability to yield a validation word, provisional wording on every
run artifact, the frozen prompt hash, retry and cost accounting, the single
holdout pass, and the preservation of both earlier mission statuses.

---

## Limitations

- Both references are `AI_ASSISTED_PROVISIONAL`. Everything measured is
  provisional agreement between assistants.
- The Mission 1.26 holdout is **not** a pristine independent holdout: the label
  import exposed it to the surrounding development process. It was used here as a
  provisional exploratory check only.
- Two provisional positives in development is a base too small to develop
  against; a variant that found one found half of them.
- The split is pair-disjoint, not observation-disjoint.
- V1 and V2 were never scored on the same pairs.

---

## §14 — Recommendation

**`PARK_PROBLEM_FAMILY_CLASSIFIER`.** Do not start a V3.

Three variants moved the classifier's positive detection from 1-in-20 to 1-in-40,
in the wrong direction, and the most informative signal is not the decision
counts but the empty field: **`shared_problem_if_any` was almost never filled.**
Asked to name an abstraction covering both questions, the model declined 39 times
out of 40. That is not a prompt that needs another turn of tuning; it is a
question that either has no good answer over this corpus, or needs a different
kind of instrument than a per-pair classifier.

**The project should move toward the Opportunity Engine, scoring and ranking over
evidence paths that are already valid** — SROS holds 26 canonical Evidence rows
from other source families — while this relation stays NOT_AUTHORISED.

The standing backlog item from Mission 1.26 remains, and is now the *second*
condition rather than the first: genuinely human reference labels would be
required before any production claim, and on this evidence a classifier worth
validating does not yet exist.
