# Mission 1.22 — Semantic Problem Equivalence / INFERRED Claims

**Sprint 1. Authorized by the Mission 1.22 brief §0-§51.**

> ## OUTCOME A — THE MODEL ROUTE IS NOT AUTHORISED, AND SEPARATELY NOT CONFIGURED
>
> **No model was called. No question text left this machine. No component was
> built.**
>
> Two gates refused, independently, before any inference work could begin:
>
> **Governance.** The Stack Exchange review permits model INFERENCE and is silent
> on TRANSMISSION of licensed text to an external provider. So is the profile,
> which has no field for where inference happens. Under rule 2 — uncertainty is
> never permission — an unassessed activity blocks.
>
> **Configuration.** Every inference tier is `null`, every credential is empty,
> and no local inference provider exists in the repository. §6's instruction to
> prefer a local route has no candidate to prefer.
>
> `INFERENCE_ARCHITECTURE_READY_BUT_MODEL_ROUTE_NOT_AUTHORISED` — with one
> honest qualification: the architecture is **designed and not built**, because
> building half a machine whose other half is unauthorised would be the unused
> abstraction this repository refuses elsewhere.

Design: [`semantic-problem-equivalence-v1.md`](../data/semantic-problem-equivalence-v1.md).

---

## 1. PRE-FLIGHT — were both Mission 1.21 corrections made?

**Yes, both.**

**A. Pre-registration wording.** Mission 1.21 said its pre-registration was
committed *"before any issue content was inspected"*. Too absolute: two minimal
metadata-only reachability probes had already occurred, and the report disclosed
them elsewhere while that sentence implied otherwise.

Corrected in the pre-registration document and in the 1.21 report to: committed
**before any substantive issue content, duplicate-bearing corpus or
duplicate-density result was inspected**, with the two probes named at the point
of the claim rather than only further down. **The probes themselves are
unchanged** — no history was rewritten.

**B. Policy decision versus legal conclusion.** The fail-closed outcome stands
and its basis is now stated as ours. What is established is that **no sufficient
positive access basis for the intended automated route exists under this
repository's rules**, and that **the published robots directive disallows that
route**.

**Nothing claims that robots.txt by itself makes REST access unlawful.** That is
a legal question this system does not decide (`source-registry-v1.md` §0). A
different posture or an answer from TDF could change the SROS decision with
nothing about the law having changed. Corrected in the 1.21 report and in the
candidate landscape document.

**No acquisition became authorised by either correction.** TDF and Launchpad
remain blocked.

---

## 2. GOVERNANCE — the question the model has no word for

### Is Stack Exchange model inference authorised?

**Yes, as an activity.** `model_processing: PERMITTED_WITH_CONDITIONS`, and the
review states its basis in its own words:

> "MODEL INFERENCE IS PERMITTED; TRAINING IS NEITHER ASSESSED NOR AUTHORISED.
> Reading and classifying licensed text is use within the licence's own grant to
> reproduce and to produce Adapted Material."

### Is external-provider transfer authorised?

**No — and the honest answer is that it was never assessed.**

§5 asked whether the review covers (A) local inference only, (B) transmission to
an external third-party provider, or (C) both.

**None of the three, as stated — and the correction matters** (Mission 1.23 §0).
The review authorises **MODEL INFERENCE AS AN ACTIVITY**. It does not say
"locally"; **the model had no way to represent execution location at all**, so
the review could not have scoped itself to a location even if its author had
wanted to.

**Two different things were being confused**, and separating them is what Mission
1.23 exists to do:

- **inference permission** — may a model read this material? *Answered: yes.*
- **execution-location representation** — where may that reading happen, and does
  the material leave this deployment to get there? *Not represented anywhere in
  the contract, so never assessed.*

**Local inference introduces no third-party content transmission**, so it does not
trigger the newly discovered activity and is covered by the existing permission.
Transmission to an external provider is the act that was never assessed, because
the model had no word for it.

**The profile is silent too, and that is the finding worth keeping.**

| Field | Value | What it settles |
|---|---|---|
| `model_inference` | `true` | the ACTIVITY is in scope |
| `deployment` | `LOCAL` | where the SYSTEM runs |
| `model_training` / `embeddings` | `false` | both forbidden |
| `raw_redistribution` | `false` | no publishing of source data |

**Nothing says where inference runs.** The profile contains no occurrence of
*provider*, *third party*, *external service*, *transmit* or *egress*; neither
does any condition on the review; neither does any document under `docs/`. Each
absence was searched for rather than assumed, and each is asserted by a test.

**So `model_processing` is one field answering a question that turns out to be
two.** That is the same shape Mission 1.15.4 found when every review had assessed
a use case the model never recorded — a distinction the system needs, with no slot
to record it, discovered by the first mission that needed it.

Under rule 2 of the registry contract, an unassessed activity blocks. **This is a
review act away from being answerable, and a review act is not a code change.**

### Which inference route was used?

**None.** See §3.

### Training? Embeddings?

**Neither, and neither was approached.** `model_training: false` and
`embeddings: false` on the profile; D-12 blocks embeddings independently; no
module, prompt or configuration touching either was added.

---

## 3. The second gate — no route exists to prefer

```text
LLM_TIER_FAST_PROVIDER=null        LLM_TIER_BALANCED_PROVIDER=null
LLM_TIER_STRONG_PROVIDER=null      LLM_TIER_EMBEDDING_PROVIDER=local
ANTHROPIC_API_KEY=                 GEMINI_API_KEY=      OPENAI_API_KEY=
```

**Every inference tier is `null`** — which `config.py` treats as not configured,
by the predicate `bool(self.provider) and self.provider != "null"` — **and every
credential is empty.**

The implemented providers are `anthropic`, `gemini` and `fake`. Both real ones
are external services; `fake` is a test double. **There is no local inference
provider in the repository**: `local` appears once, as the EMBEDDING tier, and
embeddings are forbidden.

**The two gates are independent.** Configuring a provider would not answer the
governance question, and answering the governance question would not configure a
provider. Either alone leaves the mission where it is.

---

## 4. What was designed, and why nothing was built

[`semantic-problem-equivalence-v1.md`](../data/semantic-problem-equivalence-v1.md)
records the component: deterministic bounded candidate generation, a versioned
three-outcome rubric with mandatory `ABSTAIN`, structural separation of untrusted
question text from instructions, a classifier with no tools, uncalibrated
confidence semantics, pairwise-only Signals, and provenance that outlives the
current configuration.

**It is a design and not a component**, deliberately. Building a candidate
generator, a rubric implementation and a prompt while the classifier they feed is
unauthorised would be the unused abstraction §7 of the compliance rules refuses —
and Mission 1.8 has a precedent for what happens when a capability is registered
before a condition names it.

**Three design decisions are worth stating here** because they would be the first
things a later mission is tempted to soften:

- **Candidate generation is not evidence.** Its output means *this pair is worth
  asking about*, never *these are probably the same*. Its recall limit becomes
  part of every downstream scope, so the strongest permitted claim is bounded to
  the pairs actually considered under a named generator version.
- **`derivation_confidence = 1.0` would be wrong twice.** Inference is not
  deterministic even at temperature zero, and transport success is not semantic
  confidence. If the contract cannot represent an uncalibrated judgement, the
  contract gets fixed before anything is persisted.
- **Pairwise only.** `A~B` and `B~C` do not imply `A~C`; transitivity is a
  property somebody would have to establish, and assuming it is how two cautious
  judgements become one confident wrong one.

**The Mission 1.20 hard negatives are carried into the design** rather than left
to be rediscovered: the three Docker questions sharing 182 characters of runc
diagnostic and then diverging into `permission denied`, `no such file or
directory` and `executable file not found in $PATH`. A rubric that collapses them
has failed whatever its accuracy elsewhere.

---

## 5. Everything the mission did not reach

Each of these was gated behind §5/§6 and is reported as not-done rather than as
zero:

| §  | Item | State |
|---|---|---|
| 11 | Equivalence rubric implementation | designed, not built |
| 14–15 | Candidate generator | designed, not built |
| 16–19 | Evaluation set, human labels, dev/holdout split | **not started** — an evaluation with no classifier to evaluate is not an evaluation |
| 20 | Predeclared precision criterion | not set — setting one now would be choosing a number with nothing to measure |
| 28–30 | Model-derived Signal | none |
| 31–32 | INFERRED Claim | none |
| 33–35 | Evidence, reliability | none |
| 36 | Bounded production run | none |
| 47 | `problem-equivalence-evaluation-v1.md` | **deliberately not created** |

**§47's evaluation report was not written, and that is the honest choice.** A
document with a rubric section, an empty confusion matrix and a "not evaluated"
in every row would look like an evaluation that returned nothing, when what
happened is that none was performed. The design document says what an evaluation
would have to establish; this report says why there is none.

**No operator labelling batch was requested** (§18). Asking a person to label
pairs for a classifier that cannot run would spend their attention on a step that
cannot complete.

---

## 6. BOUNDARIES

| | |
|---|---|
| Model calls | **0** |
| Question text sent anywhere | **none** |
| Tokens, cost | **0** |
| New RawRecords / NormalizedRecords | **0** |
| New Signals / Claims / Evidence | **0** |
| INFERRED Claims | **0** |
| Embeddings, training, fine-tuning | **none, none, none** |
| Direct provider SDK use | **none** — no code was added at all |
| Opportunities, WTP, demand, pricing, market size | **0** |
| Mission 1.18 S0 / Mission 1.20 S0 | **untouched** |
| Cross-source convergence | **not begun** |
| Mission 1.21 backlog (TDF, kernel.org, Gateway bug, `SOURCE_ITEM_LINK`, TED H-questions, npm, modern-profile registration) | **not reopened** |

**The deterministic findings are not contradicted, and the distinction is written
into the design.** Missions 1.18 and 1.20 established that DETERMINISTIC identity
is unavailable over this corpus — a statement about a method. *Deterministic
identity unavailable* is not *semantic equivalence impossible*, and a later model
inferring equivalence between records those missions could not group would
contradict neither.

---

## 7. QUALITY

### Counts before and after

| | Before | After |
|---|---|---|
| RawRecords | 148 | **148** |
| NormalizedRecords | 148 | **148** |
| Signals / Claims / ClaimRevisions / Evidence | 26 / 26 / 26 / 26 | **26 / 26 / 26 / 26** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 | **0** |
| Registered sources | 29 | **29** |
| **Model calls / tokens / cost** | — | **0 / 0 / 0** |

The Stack Exchange corpus is 104 `community_question` observations — 89 `docker`
and 15 `python` — unchanged and unre-acquired.

### Gates

Zero-dependency suites, all pytest suites, the seven validators plus
`check_env_template` and `assert_registry_grants_nothing`, contract generation
`--check`, the four generated-document checks, ruff, ruff format, mypy, and the
two CI inline grep guards.

`test_semantic_inference_route_not_authorised.py` pins the finding: that the
review permits inference as an activity, that its basis is about reading rather
than transmitting, that no condition and no profile field mentions a provider,
that no repository document authorises the transfer, that every inference tier is
unconfigured, that no local provider module exists, and that no component,
interpreter or prompt was added.

---

## 8. The next architectural consequence

**The blocker moved from the data to the deployment's own governance**, and that
is a different kind of blocker from the three before it.

- Missions 1.18 and 1.20: the DATA could not support deterministic identity.
- Mission 1.21: the SOURCES that publish identity could not be reached.
- **Mission 1.22: the model route this system would use has not been assessed,
  and the profile cannot express the question.**

The first two were findings about the world. This one is a finding about SROS,
and it is therefore the one this project can actually resolve.

**Four things are required before production semantic inference can run. Some
are governance or operator decisions; others require explicit contract or
engineering work. None may be silently inferred from the current
configuration.**

*(Corrected in Mission 1.23 §0. The original sentence said none of the four was a
code change, which its own next lines contradicted: a profile field is a schema
and contract change with an ADR behind it, and a local inference provider is
engineering.)*

1. **A review act** assessing transmission of licensed source content to an
   external provider, for this source and this profile — the same shape as every
   activity assessment the registry already performs.
2. **A profile field** able to carry the answer, so the distinction lives in the
   model rather than in prose. Adding one is a contract change with an ADR, and
   it would apply to every source at once.
3. **An authorised inference route** — a configured provider covered by (1), or a
   local inference provider, which the repository does not have and which would
   be a real piece of engineering.
4. **A human-labelled evaluation set with real positives**, collected blind,
   before any production run — and Mission 1.20's corpus may contain none, which
   §27 already names as a valid outcome.

**The recommended next mission is (1) and (2) together**: a governance mission
that asks where inference may happen and gives the profile a word for the answer.
(1) is a review act; **(2) is a genuine cross-cutting contract change** with an
ADR, a migration and an effect on every profile at once. Until both happen, every
future inference mission stops exactly here.

**Nothing about this result makes inference safe or unsafe.** It says the question
was never asked, and that asking it is the next piece of work.
