# Problem-Equivalence Evaluation V1 — what was measured, and what was not

**Authoritative for the EVALUATION.** Mission 1.24.

> **Outcome B — EVALUATION_INSUFFICIENT_FOR_PRODUCTION_EQUIVALENCE.** The
> classifier ran on 40 real labelled pairs and produced **zero false SAME**. It
> also produced **zero SAME of any kind**, and the holdout contained **no SAME
> label to test against** — so the passing number is one a classifier hard-coded
> to answer DIFFERENT would also have recorded. No production inference was run.
> No Signal, no INFERRED Claim and no Evidence exists.

---

## 1. What was run

| | |
|---|---|
| corpus | 89 Docker `community_question` observations (Mission 1.20, unchanged) |
| candidate generator | `docker-lexical-candidates@1.0.0`, 60 of 3 916 possible pairs |
| batch selection | `review-batch-selection@1.0.0`, 40 pairs |
| rubric | `problem-equivalence-rubric@1.0.0` |
| prompt | `semantic-problem-equivalence@1.0.0`, unchanged between the two runs |
| route | STRONG_MODEL tier → the approved provider, through the LLM Gateway |
| reference labels | 40, supplied **blind** before any model call |
| reference origin | **`AI_ASSISTED_PROVISIONAL`** (GPT-5.6 Sol) |
| human ground truth | **NOT_ESTABLISHED** |
| model calls | 40 |
| tokens | 225 207 in, 15 986 out |
| cost | **0.61 units (USD), priced** |

The prompt version was **not** changed between development and holdout. §11
permits developing against development labels; nothing was developed, so the
holdout was run once against the same artifact.

---

## 2. The result

| | development | holdout |
|---|---|---|
| labelled and predicted | 23 | 17 |
| reference SAME / DIFFERENT / UNCERTAIN | 1 / 20 / 2 | 0 / 16 / 1 |
| model SAME / DIFFERENT / ABSTAIN | 0 / 22 / 1 | 0 / 17 / 0 |
| **false SAME** | **0** | **0** |
| false DIFFERENT | 1 | 0 |
| agreements | 21 / 23 | 16 / 17 |

**The model never predicted SAME_PROBLEM.** Not once in 40 pairs.

### The three Mission 1.20 hard negatives

All three classified `DIFFERENT_PROBLEM` with
`SHARED_WRAPPER_DIVERGENT_TERMINAL_CAUSE`. That is the right answer and it is
**not evidence of generalisation**: the rubric quotes one of those pairs by id
and describes the pattern the other two share, so the classifier was shown the
answer in its own instructions. All three are pinned to development for exactly
this reason, and the reason is recorded per pair.

---

## 3. Why the pass does not support production

The predeclared criterion (`v1-false-positive-avoidance`) required zero false
SAME, at least 12 labelled holdout pairs, and at least one SAME **anywhere in the
reference set**. All three were met, and the scored outcome was
`MODEL_EVALUATION_PASSED`.

**The single SAME fell in DEVELOPMENT. The holdout had none.** So on the holdout:

- a classifier that answered `DIFFERENT_PROBLEM` to every pair scores zero false
  SAME, the same as this one;
- nothing was measured about whether a SAME prediction can be trusted, because
  none occurred;
- **precision on SAME is undefined** (no predictions) and **recall on SAME is
  0/1** (the one positive was missed).

Production exists to turn SAME predictions into a model-derived Signal, an
INFERRED Claim and Evidence. A SAME emitted in production would therefore rest on
**zero measured precision**. That is the exact risk V1 was written to avoid, so
production was not run.

### The criterion was wrong, and only data could show it

V1 said *anywhere in the reference set*. It should have said *in the split being
scored*. `v2-false-positive-avoidance-with-a-testable-split` changes that one
word and nothing else. Scored under V2, **the same run and the same data return
`EVALUATION_INSUFFICIENT`.**

**V1 is kept and Mission 1.24's result stays scored under it.** The rule was
binding when the run happened, and rewriting it would leave this document
describing a criterion that no longer exists. A test pins both, and pins the
constant-DIFFERENT classifier as the thing they must tell apart.

---

## 4. The disagreements, both of them worth reading

> **Corrected in Mission 1.25 §0.** Neither is human inter-rater disagreement.
> Both are disagreement between the rubric's stated expectation and an
> **AI-assisted provisional** reference label. No person has reviewed these
> pairs, so `human_ground_truth` is NOT_ESTABLISHED, and nothing below may be
> read as a human judging the rubric.

### The missed positive — `78089171::78098380`

- **A**: a Next.js `NEXT_PUBLIC_` variable is undefined in a Kubernetes pod even
  though the environment is set on the pod.
- **B**: `docker-compose`'s `env_file` supplies variables at container runtime,
  and they are absent during the Dockerfile build.

The provisional reference called it SAME. The model called it `DIFFERENT_PROBLEM` /
`SAME_STACK_DIFFERENT_CONCERN`, reasoning that one is Next.js and Kubernetes and
the other is Compose, and that neither fix addresses the other.

**Both readings survive the rubric, and that is the finding.** The class of
misconfiguration is identical — a value needed at BUILD time is supplied only at
RUN time — and the fix has the same shape on both sides: pass it as a build
argument. The rubric's granularity clause says *the same component*, and whether
"the build stage" is one component or two is precisely what the two readings
disagree about.

**The rubric was NOT revised to capture it.** One example is `n=1`, the revision
would loosen the rubric in the direction of more SAMEs, and there is no positive
anywhere in the holdout against which the false-positive cost of loosening could
be measured. Tuning here would be fitting to the single data point that the
evaluation was least able to check.

### The rubric disagreeing with its own reference — `78088430::78090396`

This pair is the rubric's own **borderline worked example**, where the rubric
states `DIFFERENT_PROBLEM`. The model agreed with the rubric. **The provisional
reference said UNCERTAIN.** So the rubric's stated expectation and its reference
set disagree about a pair the rubric uses to define its boundary. Recorded rather than resolved: a
boundary example both parties do not read the same way is a defect in the
example, and fixing it is a rubric version bump with its own evaluation.

---

## 5. What the reason codes actually did

| code | development | holdout |
|---|---|---|
| `SAME_STACK_DIFFERENT_CONCERN` | 14 | 14 |
| `INSUFFICIENT_DETAIL` | 5 | 3 |
| `SHARED_WRAPPER_DIVERGENT_TERMINAL_CAUSE` | 3 | 0 |
| `SHARED_GENERIC_ERROR_ONLY` | 1 | 0 |
| `SAME_ACTIONABLE_FAILURE` | 0 | 0 |

Four of five codes were used. `SAME_ACTIONABLE_FAILURE` was never emitted,
because no SAME was ever decided.

**`INSUFFICIENT_DETAIL` appearing beside `DIFFERENT_PROBLEM` seven times is worth
noticing.** The rubric offers ABSTAIN for text that cannot support a decision,
and the model chose a decision anyway while citing the code for insufficiency. It
abstained exactly once in 40. Whether that is a prompt weakness or a correct
reading of pairs that are decidably different despite thin text is not
established here, and would need labels designed to separate the two.

---

## 6. The scope every statement here inherits

> Scope: the 60 pairs surfaced by `docker-lexical-candidates@1.0.0` out of 3 916
> possible pairs over 89 observations, of which 40 were labelled and classified.
> A pair this generator did not surface is UNCONSIDERED, not different. Nothing
> here describes all repeated problems in the corpus, and no wording may imply it
> does.

Two further limits, stated because they are easy to forget:

- **These are questions, not people.** Author identity was never acquired, so no
  count of distinct users is available now or ever.
- **A model judgement has no calibrated probability.** No confidence number was
  requested from the model, so there is none to attach and none to multiply by.

---

## 7. What was not done

No production inference. No model-derived Signal. No INFERRED Claim. No Evidence.
No Opportunity, and no market, willingness-to-pay, pricing or MRR inference of
any kind. No embeddings, no training, no fine-tuning. No new acquisition: raw and
normalized record counts are unchanged, and Missions 1.18 and 1.20 keep their
deterministic S0 findings — a model-derived inference is a new epistemic layer,
never a correction of those.

---

## 8. What would change the answer

**A reference set with real positives in the scored split, and ideally a human
one.** That is the whole blocker, and it is not a tooling problem. This 89-question corpus yielded one
defensible SAME out of 40 candidate pairs, which is itself a finding about the
corpus rather than about the classifier.

Three routes, none of them free:

1. **Label more pairs from the existing candidate set.** 20 of the 60 candidates
   are unlabelled. Cheap, and likely to yield few positives at the same rate.
2. **A corpus where repeated problems plausibly exist** — a narrower tool, a
   longer window, or a source that links reports itself. That is an acquisition
   mission with its own review, not a change here.
3. **Accept that pairwise SAME is rare in public Q&A** and ask whether the
   product needs it, which is a question about the product rather than about the
   model.

**No synthetic positive may be used to answer this.** A constructed SAME pair can
test a parser; it cannot establish semantic accuracy against real data, and using
one here would manufacture the very evidence the evaluation exists to require.
