# Semantic Problem Equivalence V1 — architecture, and the gate it did not pass

**Authoritative for the DESIGN.** Mission 1.22 §48.

> **BUILT IN MISSION 1.24, and the design held.** Everything below was
> implemented in `packages/semantic-equivalence` without a structural change:
> deterministic bounded candidate generation, a versioned rubric with mandatory
> ABSTAIN, untrusted question text structurally separated, a classifier with no
> tools, uncalibrated confidence semantics, pairwise-only Signals, provenance
> outliving the configuration. What changed is one placement decision the design
> did not anticipate: `validate_signals.py` forbids a Gateway import anywhere in
> `sros_nlp`, so the classifier lives in its own package rather than in the
> signal layer, and the guard was left alone.
>
> **The evaluation did not pass in substance.** See
> `problem-equivalence-evaluation-v1.md`: 40 real labelled pairs, zero false
> SAME, and **zero SAME of any kind**, over a holdout containing no SAME label to
> test against. No production inference, no Signal, no INFERRED Claim, no
> Evidence.

> **No inference was performed and no model was called.** Two independent gates
> refused before any question text could be sent anywhere: the governance one
> (§2) and the configuration one (§3). This document records what the component
> would be, so a later mission starts from a design rather than a blank page —
> and it records precisely what would have to change first.

---

## 1. The semantic boundary this component would cross

Every inference layer in this repository so far has been **deterministic
restatement**: a Signal relates observations by arithmetic, and an OBSERVED Claim
says the source reported something. Nothing has ever asserted a proposition the
source did not state.

**Semantic problem equivalence would be the first.** The question is:

> Do two public Stack Overflow questions describe the same underlying problem?

**Stack Exchange does not answer it.** There is no `duplicate_of` in the acquired
fields, no canonical-question relation, nothing. So any answer is **inferential by
construction** — which is why the output would be an `INFERRED` Claim and never an
`OBSERVED` one, and why the word *inferred* has to survive every layer down to
the Evidence row.

**Missions 1.18 and 1.20 are the reason this is the remaining route, and they are
not contradicted by it.** They established that DETERMINISTIC identity is
unavailable over this corpus: a tag names a subject, and a shared 182-character
Docker diagnostic names an error envelope. *Deterministic identity unavailable*
is not *semantic equivalence impossible* — the two statements are about different
methods, and a later model inferring equivalence between records those missions
could not group would contradict neither.

---

## 2. Gate one — the governance question, and the vocabulary it has no word for

> **CLOSED by Mission 1.23** (ADR-033). `external_model_transmission` exists on a
> source review, `external_model_egress` exists on a use profile, and Stack
> Exchange's local review v2 answers the first. The section below is kept as the
> record of what was missing and why.

**The Stack Exchange local review permits model inference AS AN ACTIVITY and is
silent on third-party transmission** — and the silence is structural rather than
an omission: **the contract had no way to represent execution location**, so no
review could have scoped itself to one. Its own words:

> "MODEL INFERENCE IS PERMITTED; TRAINING IS NEITHER ASSESSED NOR AUTHORISED.
> Reading and classifying licensed text is use within the licence's own grant to
> reproduce and to produce Adapted Material."

That answers **may a model read this text**. It does not answer **may this text
leave the local deployment so that a third party's model can read it**, and the
two are different acts with different exposure.

**The profile is silent as well, and that is the structural finding.**
`local-private-research-v1` records thirteen fields; the ones that bear on this
say:

| Field | Value |
|---|---|
| `deployment` | `LOCAL` |
| `model_inference` | `true` |
| `model_training` | `false` |
| `embeddings` | `false` |
| `raw_redistribution` | `false` |
| `customer_facing_source_access` | `false` |

`model_inference: true` says the ACTIVITY is in scope. `deployment: LOCAL`
describes where the SYSTEM runs. **Neither says where inference runs**, and the
profile contains no occurrence of *provider*, *third party*, *external service*,
*transmit* or *egress*. Nor does any document under `docs/`.

**So the model has one field for a question that turns out to be two.** That is
the same shape Mission 1.15.4 found when every review had assessed a use case the
model never recorded: a distinction the system needs and has no slot for,
discovered by the first mission that needed it.

**Under rule 2 of the registry contract — uncertainty is never permission — an
unassessed activity blocks.** No review, profile field or policy document
authorises sending licensed Stack Exchange question text to an external provider,
so it is not authorised.

**What would resolve it** is a review act, not a code change: assess third-party
transmission explicitly for this source and this profile, and give the profile a
field that can carry the answer. Both belong to a governance mission.

---

## 3. Gate two — no inference route exists to prefer

> **CLOSED by operator configuration in Mission 1.24.** The STRONG_MODEL tier is
> bound to the approved provider with a named model and a present credential, and
> `sros-inference readiness` reports all ten gates passing. The env block below
> shows the state as Mission 1.22 found it.

Independent of governance, and it fails on its own:

```text
LLM_TIER_FAST_PROVIDER=null        LLM_TIER_FAST_MODEL=
LLM_TIER_BALANCED_PROVIDER=null    LLM_TIER_BALANCED_MODEL=
LLM_TIER_STRONG_PROVIDER=null      LLM_TIER_STRONG_MODEL=
LLM_TIER_EMBEDDING_PROVIDER=local  LLM_TIER_EMBEDDING_MODEL=bge-m3
ANTHROPIC_API_KEY=                 GEMINI_API_KEY=      OPENAI_API_KEY=
```

**Every inference tier is `null`** — which `config.py` treats as *not configured*
— **and every credential is empty.** The only implemented providers are
`anthropic` and `gemini`, both external, plus the `fake` test doubles.

**There is no local inference provider in the repository.** `local` appears once,
as the EMBEDDING tier, and embeddings are forbidden by D-12 and by §7 of this
mission. So §6's instruction to *prefer an already-supported local inference
provider if one exists* has no candidate to prefer.

**The two gates are independent.** Configuring a provider would not answer the
governance question, and answering the governance question would not configure a
provider.

---

## 4. What the component would be

Recorded as a design so the next mission argues with something concrete.

```text
normalized community_question observations
        │
        ▼
deterministic candidate generation          bounded, no model, no embeddings
        │   "worth asking about" — never "probably the same"
        ▼
semantic classifier via the LLM Gateway     schema-constrained, no tools
        │   SAME_PROBLEM / DIFFERENT_PROBLEM / ABSTAIN
        ▼
model-derived Signal                        pairwise, uncalibrated
        │
        ▼
INFERRED Claim  ──▶  Evidence               never OBSERVED, never source-native
```

### 4.1 Candidate generation is not evidence

A deterministic generator over structured fields and lexical overlap — no
embeddings, no model. Its output means exactly *this pair is worth asking the
classifier about*, and **never** *these are probably the same problem*.

**Its recall limit becomes part of every downstream scope.** A generator that
misses a pair makes that pair unconsidered, not different, so the strongest
permitted claim is bounded to the pairs actually considered under a named
generator version — never *"these are all the repeated Docker problems"*.

### 4.2 The rubric, and the granularity decided once

Three outcomes, with `ABSTAIN` mandatory so the classifier is never forced to
choose between SAME and DIFFERENT on text that cannot support either.

**Granularity is fixed by the rubric and never chosen per pair.** Mission 1.20's
three Docker questions are the canonical hard negatives: they share 182
characters of exact runc diagnostic and then diverge into `permission denied`,
`no such file or directory` and `executable file not found in $PATH`. A rubric
that collapses them has failed, whatever its accuracy elsewhere.

Same tool, same tag, same wrapper, same generic error class, same HTTP status and
same broad symptom are each **insufficient alone**, by construction rather than by
threshold.

### 4.3 Untrusted content, structurally separated

Question text is **untrusted data and never instruction context**. The prompt
would separate system instructions, the controlled task, and each question as
labelled untrusted evidence — and the classifier would be given **no tools, no
browsing and no execution**, so an instruction inside a question has nothing to
reach even if it is obeyed.

### 4.4 Confidence, told the truth

**An LLM self-reported number is not a probability.** `derivation_confidence = 1.0`
would be wrong twice over: inference is not deterministic even at temperature
zero, and transport success is not semantic confidence.

If the existing contract cannot represent an uncalibrated judgement truthfully,
**the contract gets fixed generically before anything is persisted** — a fake
probability in a field a consumer branches on is worse than a missing one.

### 4.5 Provenance that outlives the configuration

Every artefact would have to resolve: both question observations and their raw
lineage, the candidate-generator version, the rubric version, the prompt version,
the model and provider identity, the inference run, and the evaluation binding.
**Current configuration will not be remembered later**, so none of it may be
implied.

### 4.6 What a Signal would and would not mean

> Under semantic-equivalence procedure V, these distinct question observations
> were classified as describing the same problem.

Not that the source says they are duplicates. Not that the equivalence is
objectively true. Not that distinct people encountered it — **author identity was
never acquired**, so no count of people can be stated, then or ever.

**Pairwise in V1.** `A~B` and `B~C` would not imply `A~C`: transitivity is a
property somebody would have to establish, and inventing it is how a clustering
step turns two cautious judgements into one confident wrong one.

---

## 5. Reproducibility, stated as a limitation

**A model-derived Signal is not reproducible the way every existing Signal is.**
Re-running a deterministic extractor over the same inputs yields the same output;
re-running a classifier may not, and the repository's `DETERMINISTIC` derivation
kind promises regeneration that a model in the path voids.

That is not an argument against building this. It is an argument for never
describing it in the vocabulary the deterministic path uses.

---

## 6. What would have to be true before this is built

1. **A review act** assessing transmission of licensed source content to an
   external provider, for this source and this profile.
2. **A profile field** able to carry the answer, so the distinction is not
   recorded only in prose.
3. **An authorised inference route** — a configured provider whose use is covered
   by (1), or a local inference provider that does not raise the question.
4. **A human-labelled evaluation set** with real positives, collected blind to
   model output, before any production run.

**None of the four may be silently inferred from the current configuration**
(corrected in Mission 1.23 §0; the original sentence claimed none was a code
change, which is untrue of (2) and (3)). Items 1 and 4 are governance and
operator work; **item 2 is a contract and schema change with an ADR behind it**,
and item 3 is either configuration covered by item 1 or a real piece of
engineering. That is why this mission produced a design and no component.
