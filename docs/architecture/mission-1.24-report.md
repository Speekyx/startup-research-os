# Mission 1.24 — Semantic Problem Equivalence Evaluation & First INFERRED Evidence V1

**Outcome B — EVALUATION_INSUFFICIENT_FOR_PRODUCTION_EQUIVALENCE.**

The first model-mediated inference this repository has run. 40 real labelled
pairs, through the Gateway, on the approved route, for **0.61 USD**. Zero false
SAME, and **zero SAME of any kind** over a holdout containing no SAME label to
test against. **No production inference. No model-derived Signal, no INFERRED
Claim, no Evidence, no Opportunity.**

| | Before | After |
|---|---|---|
| RawRecords | 148 | **148** |
| NormalizedRecords | 148 | **148** |
| Signals / Claims / ClaimRevisions / Evidence | 26 / 26 / 26 / 26 | **26 / 26 / 26 / 26** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 | **0** |
| Registered sources | 29 | **29** |
| **Model calls / input tokens / output tokens / cost** | 0 / 0 / 0 / 0 | **40 / 225 207 / 15 986 / 0.61 USD** |

---

## CONFIGURATION

**Intended Gateway tier: `STRONG_MODEL`**, and the choice is decided on ADR-006's
own definitions rather than on preference. ADR-006 defines that tier as *complex
synthesis, planning, hard judgment*, and semantic problem equivalence is hard
judgment by construction: its canonical hard negatives share 106 characters of
exact runc diagnostic and then diverge into three unrelated failures, and V1
prioritises avoiding a false SAME. A test pins the choice so that moving to a
cheaper tier is a visible decision.

`sros-inference readiness` reports **ten** gates, all passing:

```
gateway-tier-bound                            LLM_TIER_STRONG_PROVIDER=anthropic
gateway-tier-provider-approved                LLM_TIER_STRONG_PROVIDER=anthropic
gateway-tier-model-named                      LLM_TIER_STRONG_MODEL=claude-sonnet-5
adapter-serves-this-tier                      supports(STRONG_MODEL)=True
provider-credential-present                   ANTHROPIC_API_KEY is set
source-model-processing-permitted             PERMITTED_WITH_CONDITIONS
source-external-model-transmission-permitted  PERMITTED_WITH_CONDITIONS
profile-external-model-egress-permitted       PERMITTED_TO_APPROVED_PROVIDERS
provider-policy-approved                      posture=APPROVED
adapter-is-on-the-assessed-route              https://api.anthropic.com/v1/messages
```

**Readiness is not one environment variable, which is the §0.A finding.** Mission
1.23 proved the governance gate refused on `PROVIDER_NOT_CONFIGURED`, derived
from a credential's presence. A reader could conclude that supplying the key
makes the system ready; it does not. Mission 1.22 had separately found every
inference tier bound to `null`, and a valid key with an unbound tier routes
nowhere. Every gate is evaluated even after one fails, because an operator shown
one failure fixes it and is refused again.

**No paid call was made to establish readiness.** The adapter validates no model
identifier against a list, so a wrong name is a provider-side error at call time
rather than a readiness failure. That limit is written into the gate rather than
papered over.

**Inference authorization result**: authorized, resolved once before the loop.
**Source text transmitted before authorization: none.** The check precedes prompt
construction, not the socket, and a test hands the refusal path a gateway double
that raises if it is reached.

**Pricing.** `LLM_PRICING_JSON` was configured from the publisher's own pricing
page, with the retrieval date in the version label. The cost unit is one US
dollar, stated rather than assumed. The table models neither prompt caching, nor
the Batch discount, nor data residency, nor a negotiated rate, and says so beside
itself. Budget ceilings were tightened as a consequence: a unit now means a
dollar, so the shipped defaults meant 100 USD per session, three orders of
magnitude above this experiment.

---

## HUMAN EVALUATION

| | |
|---|---|
| operator batch | 40 pairs |
| rubric version | `problem-equivalence-rubric@1.0.0` |
| labels | 36 DIFFERENT, 3 UNCERTAIN, **1 SAME** |
| development / holdout | 23 / 17 |
| positives in development | 1 |
| **positives in holdout** | **0** |
| hard negatives included | all three Mission 1.20 runc pairs |

**The batch was generated, never hand-picked**: ranks 1..20 in candidate order,
then every second thereafter, declared before the batch existed. Choosing pairs
by eye is how a reference set comes to contain the cases the classifier was going
to get right anyway.

**The split was computed from each pair id before any label existed**, with
sha256 rather than `hash()` because Python's string hash is salted per process.

**Five pairs are pinned to development, each with its reason recorded.** The
rubric quotes them or describes their pattern, so the classifier is shown the
answer in its own instructions. Classifying them correctly demonstrates that it
can read its own rubric; counting them as holdout successes would have inflated
the result.

---

## MODEL EVALUATION

**Provider and model**: the approved route, `claude-sonnet-5`, resolved from the
`STRONG_MODEL` tier. The component names no provider; a test asserts no vendor
string appears anywhere in the package.

**Gateway only.** No direct SDK, no domain-level HTTP. Tier, provider, model,
routing version, prompt version, rubric version, candidate-generator version,
run id, tokens, cost and latency are all recorded on every classification.

**Prompt version `1.0.0`, unchanged between the two runs.** §11 permits developing
against development labels; nothing was developed, so the holdout was run once
against the same artifact.

| | development | holdout |
|---|---|---|
| labelled and predicted | 23 | 17 |
| model SAME / DIFFERENT / ABSTAIN | 0 / 22 / 1 | 0 / 17 / 0 |
| **false SAME** | **0** | **0** |
| false DIFFERENT | 1 | 0 |
| agreements | 21 / 23 | 16 / 17 |

Confusion, holdout: `DIFFERENT→DIFFERENT_PROBLEM` 16, `UNCERTAIN→DIFFERENT_PROBLEM` 1.

**Precision on SAME: undefined** — there were no SAME predictions.
**Recall on SAME: 0/1** — the one positive was missed.
**Abstention: once in 40.**

**Predeclared criterion**: `v1-false-positive-avoidance` — zero false SAME, at
least 12 labelled holdout pairs, at least one SAME anywhere in the reference set.
**Scored outcome: `MODEL_EVALUATION_PASSED`.**

**Calibration status: NOT CALIBRATED, and nothing here may be described as such.**
No confidence number was requested from the model, so there is none to attach and
none to multiply by. No probability may be placed on any decision.

### Why the pass does not support production

The single SAME fell in DEVELOPMENT. On the holdout, a classifier hard-coded to
answer `DIFFERENT_PROBLEM` records the same zero false SAME. Production exists to
turn SAME predictions into a Signal, a Claim and Evidence, and a SAME emitted in
production would rest on **zero measured precision**.

**The criterion was wrong in a way only data could show.** V1 asked for a
positive *anywhere in the reference set*; it should have asked for one *in the
split being scored*. `v2-false-positive-avoidance-with-a-testable-split` changes
that one word, and scores the identical run and data as
`EVALUATION_INSUFFICIENT`.

**V1 is kept and this mission stays scored under it.** The temptation runs the
other way — V2 is stricter and retro-scoring under it looks more rigorous — and
it is still wrong. A rule rewritten after seeing the outcome was never binding,
and a rule tightened after a pass is the same defect as one loosened after a
failure. A test pins the failure mode rather than the wording: a
constant-`DIFFERENT` classifier passes V1 and is refused by V2.

---

## PRODUCTION

**Not performed.** Predeclared candidate count: none, because the phase was not
entered. Model calls: 0. SAME / DIFFERENT / ABSTAIN: not applicable. Cost: 0.

The evaluation formally passed, and §22 B's condition — *human labelled data
insufficient, especially no positive examples* — holds in substance for the split
that decides. Running production would have spent money to emit predictions whose
SAME arm has no measured precision behind it.

---

## SIGNALS, CLAIMS, EVIDENCE

**None, on all three counts.** No model-derived Signal was created, because no
production SAME exists to represent. No INFERRED Claim, because there is no
Signal for one to rest on. No Evidence, because Evidence is claim-relative and
there is no claim.

The mechanics exist and are tested on the fake provider: pairwise only, no
transitive clustering, provenance resolving both observations, the
candidate-generator version, rubric version, prompt version, model and provider
identity and the inference run. `ACCEPTANCE_CRITERIA` keeps both criteria
addressable by name so a historical result stays reproducible under the rule it
was actually scored against.

Reliability, scorability and independence are untouched: no ReliabilityAssessment
was invented, `NON_SCORABLE` remains the honest state for the 26 existing Evidence
rows, and independence stays `UNKNOWN`. Multiple Stack Exchange questions remain
one source family, and **no distinct-user claim is available now or ever** —
author identity was never acquired.

---

## BOUNDARIES

Raw and normalized record counts unchanged at 148/148. No re-acquisition, no
change to the Docker window, no second tag, no new source. Missions 1.18 and 1.20
keep their deterministic S0 findings: a model-derived inference is a **new
epistemic layer**, never a correction of those. No embeddings, no training, no
fine-tuning, no vector similarity. No Opportunity. No market, willingness-to-pay,
pricing, severity, prevalence, user-count or MRR inference of any kind. No
cross-source convergence and no Wikimedia combination — recorded as a future
possibility only.

The migration checksum backlog is preserved and unchanged: 0026 was not touched,
the Mission 1.23 reconciliation is documented in `infrastructure/db/README.md` as
**deployment-local**, another already-migrated database must perform an explicit
schema-equivalence check before any ledger reconciliation, and no automatic
global checksum rewrite exists.

---

## QUALITY

**Two §0 precision points resolved before anything was built.**

Mission 1.23's summary wrote *"1 session"* in the slot every earlier report gives
to **ReliabilityAssessments**. The live database holds 1 of each, so no number
was wrong — the label was, and a canonical count line whose rows drift is one
nobody can compare across missions. Replaced with the canonical table.

The 0026 ledger reconciliation is now recorded as deployment-local, with the
procedure another deployment must follow and an explicit statement that no
tooling exists for it: a one-line escape hatch for an immutability guard gets
used the next time the guard is inconvenient.

**A structural guard decided the architecture.** `validate_signals.py` forbids a
Gateway import anywhere under `sros_nlp` and requires every module there to be
classified as signal or claim, so a model-calling component cannot live in the
signal layer. The guard was left untouched and `packages/semantic-equivalence`
carries the work, registered explicitly in the workspace, the pytest suite list
and the CI mypy targets.

**Gates.** Nine validators, four generated-doc `--check` steps plus the new
review-batch check, `ruff check`, `ruff format --check`, `mypy` across 159 source
files, both CI inline greps, `migrate --plan`, and both suites — 571 tests across
8 packages plus all pytest suites across 8 packages, with 0 failures and 0 errors.
49 tests in the new package, including six adversarial question bodies.

**A gate passed locally and failed in CI, for the second time in this
sequence.** The new orchestrator test module imported `pytest`, which is
invisible on a development machine and fatal in the zero-dependency suite that
package belongs to. Repaired by rewriting the module for stdlib `unittest` --
`subTest` instead of `parametrize` -- rather than by adding pytest to a
zero-dependency package. Mission 1.19's `urllib` import had the same root cause:
the gate was run, but not under the conditions CI uses. Recorded as
`testing-strategy.md` §64.

**A correction to the operator.** I stated that `infrastructure/compose/.env` is
tracked by git and that the credential must not go there. It is **git-ignored**
and is the correct place for local configuration. The warning was wrong and could
have changed where the key was put.

---

## ARCHITECTURAL CONSEQUENCE

**The blocker is a corpus, and it is not a tooling problem.** Every gate that
Missions 1.22, 1.23 and 1.24 §0 identified is now open: the governance question
is answered, the route is configured, the classifier exists, the boundary holds,
and the money was spent on a real evaluation rather than on a projection.

What stopped it is that **89 Docker questions yielded one defensible SAME across
40 candidate pairs**, and that one landed on the wrong side of a split computed
before anyone knew it existed. That is a finding about public Q&A rather than
about the classifier: people ask about their own configuration, and two people's
configurations are rarely the same problem at the granularity a fix would share.

**SROS is NOT ready for a cross-source convergence mission.** Convergence
combines evidence, and this mission produced none. The honest next question is
not *how do we make the classifier say SAME more often* — the direction V1 exists
to resist — but **whether a corpus exists in which repeated problems are common
enough to be worth detecting**, which is an acquisition question with its own
review.

Three routes, none free: label the 20 remaining candidate pairs (cheap, likely
the same rate); acquire a corpus where repetition is plausible — a narrower tool,
a longer window, or a source that links reports itself; or accept that pairwise
SAME is rare in public Q&A and ask whether the product needs it. **No synthetic
positive may answer this.** A constructed pair can test a parser and can never
establish semantic accuracy against real data, and manufacturing one here would
fabricate the exact evidence the evaluation exists to require.
