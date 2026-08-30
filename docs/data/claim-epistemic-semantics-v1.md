# Claim Epistemic Semantics V1

**Authoritative.** Mission 1.13. Companion to
`claim-evidence-interpretation-contract-v1.md`.

The five claim types were fixed in Ontology V2 §7 and are a **closed enum**:

```text
OBSERVED | INFERRED | PREDICTED | RECOMMENDED | HYPOTHESIS
```

**Mission 1.13 changed none of them, and did not add a sixth.** What was missing
was not a category — it was a rule for telling them apart when the input is a
Signal. That rule is this document.

---

## 1. Why this needs writing down

Every one of the seven real Signals can be truthfully restated as an `OBSERVED`
claim and can also be stretched into an `INFERRED` one, and the stretch is
invisible in the resulting row. Both carry an interpreter, both carry evidence,
both look identical to an aggregator. The difference lives entirely in whether
the statement asserts more than the Signal establishes — which is a judgement,
made once, at write time, by whoever wrote the interpreter.

A system that leaves that judgement implicit accumulates `OBSERVED` rows that are
not observations. Those rows then get aggregated with full weight, because
`OBSERVED` is the type an aggregator trusts most. **This is the single failure
mode this document exists to prevent.**

## 2. The distinguishing question

For each type, one question, and the answer must be available *before* the claim
is written:

| Type | The question |
|------|--------------|
| `OBSERVED` | Does a source **report** this, such that a person could go and read it there? |
| `INFERRED` | Does this follow from reported facts by a stated reasoning step? |
| `PREDICTED` | Is this about a time nobody has measured yet? |
| `RECOMMENDED` | Is this telling someone what to **do**? |
| `HYPOTHESIS` | Is this worth testing and not yet supported? |

The questions are ordered by how much they add to the record. A claim that
answers "yes" to more than one belongs to the **latest** type it answers yes to,
because that is the strongest thing it asserts.

## 3. `OBSERVED`

> **Asserts what a source reported, attributed to that source.**

An `OBSERVED` claim is a faithful restatement. Its truth condition is about the
publication, not about the phenomenon: it is false if the source did not say
that, and it stays true if the source was wrong.

Attribution is not optional. "Germany's population rose in 2019" and "World Bank
reported that Germany's population rose in 2019" are different propositions with
different falsifiers, and only the second is `OBSERVED` from a World Bank record.
The first is `INFERRED` — it asserts a demographic fact, and the record is
*evidence* for it rather than identical to it.

Three constraints follow, all enforced:

1. **Evidence is required.** An `OBSERVED` claim with nothing cited asserts that
   a source said something, with no record of the source saying it.
2. **Market and user vocabulary is refused** (`UNSUPPORTED_INTERPRETATION`). The
   moment the statement says demand, interest, popularity, attention, momentum,
   opportunity, willingness to pay, market, trending, product-market fit or
   revenue potential, it has asserted something no source reported as such.
3. **Nothing beyond what the temporal and language certifications allow.** See
   §8.

What may be `OBSERVED` from each real signal type:

| Signal type | May be restated as |
|-------------|--------------------|
| `numeric_period_change` | "World Bank reported that *metric* for *geography* rose/fell between *period A* and *period B*" |
| `lexical_frequency_contrast` | "Within GDELT's WEB-NGRAM stream, under language label *L*, term *A* appeared more often than term *B* in one bucket" |
| `lexical_frequency_change` | "Within GDELT's WEB-NGRAM stream, under language label *L*, term *T* appeared more often in the later of two adjacent buckets" |

Each names its source, its stream, its label and its bucket relation, and none
names a clock time, a language, a person or a market.

## 4. `INFERRED`

> **Asserts something about the world that the measurement is evidence for, and
> that the source did not itself report.**

This is the type that does interpretive work, and the type that must therefore
say what work it did. An `INFERRED` claim carries:

- the Signals it reasoned from, as Evidence,
- a `rationale`: the reasoning step, in a sentence,
- `interpretation_confidence`: how confident the interpreter is that the step is
  sound.

The reasoning step is the point. "Germany's population rose in 2019, inferred
from World Bank's reported figure, on the assumption that World Bank's estimate
tracks the underlying population" is an `INFERRED` claim whose assumption is
visible and arguable. Without the assumption written down, the same sentence is
an `OBSERVED` claim that quietly dropped its attribution.

**A model may propose an `INFERRED` claim.** That is what `MODEL_DERIVED`
interpretation is for. What the model may not do is *be* the evidence: a
`MODEL_DERIVED` claim citing no Signal is refused exactly as a deterministic one
is, and the model's contribution is recorded as provenance
(`interpreter_id`/`_version`/`model_version`/`prompt_version`), never as a row in
`scoring.evidence`.

## 5. `PREDICTED`

> **Asserts something about a period nobody has measured.**

Structurally an inference, distinguished because its falsifier does not exist
yet. Nothing in the system produces one: there is no forecaster, and the seven
real Signals are all retrospective. It is documented here so that a future
extrapolation is not filed as `INFERRED` — an inference about the measured past
and an extrapolation into the unmeasured future have very different failure
modes, and an aggregator that cannot tell them apart cannot weight them
differently.

`PREDICTED` is almost always `TEMPORALLY_SENSITIVE`, and a temporally sensitive
claim with no authorised half-life reports `MISSING_TEMPORAL_PARAMETER` and
produces no score (`../domain/evidence-aggregation-framework-v1.md`). That is the
designed behaviour.

## 6. `RECOMMENDED`

> **Asserts what someone should do.**

Not a fact about the world at all — a normative statement, whose support is a
chain of other claims plus a goal the system was given. Nothing produces one, and
nothing should until Opportunities exist, because a recommendation with no
addressable thing to recommend about is advice with no object.

The reason it is a `ClaimType` rather than a separate entity is that
recommendations must accumulate evidence and be withdrawn like anything else.

## 7. `HYPOTHESIS`

> **Asserts a proposition worth testing, and says on its face that it is not yet
> supported.**

The only type exempt from the evidence requirement, and exempt **by definition
rather than by exception**. A hypothesis that required evidence would not be a
hypothesis; and if the category were unusable, unsupported ideas would be filed
as `INFERRED` instead — which is precisely the failure the evidence rule exists
to prevent. The exemption is what makes the rule enforceable.

Two consequences:

- **A `HYPOTHESIS` may be generated by a machine.** `build_claim` permits it with
  no evidence. What it may not do is silently *become* `INFERRED` when evidence
  arrives: that is a new claim of a different type, sharing nothing but a
  proposition, and the `proposition_key` will make the relationship visible.
- **An aggregator must weight it as unsupported.** It is not a weak inference; it
  is a question.

## 8. The certifications constrain every type

Two open questions bound what any claim may say about GDELT-derived Signals,
whatever its epistemic type. A `HYPOTHESIS` is not exempt from these — the
exemption in §7 is from the *evidence* requirement, not from the *semantics*.

**H-29 (timezone unestablished).** ADR-022 certified `SOURCE_RELATIVE_ORDER` for
`web-ngrams/1gram` and `web-ngrams/2gram`, and explicitly not
`COMPARABLE_INSTANT`. So: "the later bucket" is available; "on 3 August", "at
14:00 UTC", "in the same week as the World Bank figure" are not. Cross-source
temporal alignment is refused with `INCOMPATIBLE_TEMPORAL_SEMANTICS`.

**H-30 (CLD2 mapping unestablished).** A GDELT language label is its own
identity. Comparing two terms under one label is available; saying "in French",
or comparing across labels as one language space, is refused with
`INCOMPATIBLE_LANGUAGE_SEMANTICS`.

## 9. Temporality is declared, never inferred

`ClaimTemporality` is `EVERGREEN | TEMPORALLY_SENSITIVE` and is a property of the
**proposition**, not of the source or of the claim type.

"World Bank reported that Germany's population rose between 2018 and 2019" is
`EVERGREEN`: it is about a fixed pair of periods and does not become less true in
2027. "German-language news coverage of climate is rising" is
`TEMPORALLY_SENSITIVE`: it is about an ongoing state, and the same sentence
decays.

The common mistake is reading temporality off the source's cadence — treating
everything from a 15-minute bucket stream as temporally sensitive and everything
from an annual series as evergreen. A claim about a specific past bucket is
evergreen no matter how fast the stream ticks.

## 10. Origin is who asserted, not how well

`ClaimOrigin` has six values, and the evidence rule turns on exactly one
distinction: whether a **machine** asserted the proposition.

| Origin | Automated | Note |
|--------|-----------|------|
| `DETERMINISTIC_EXTRACTION` | yes | |
| `LLM_EXTRACTION` | yes | |
| `INFERRED` | yes | The origin, distinct from the `INFERRED` claim *type* |
| `SYSTEM_GENERATED` | yes | |
| `MANUAL` | no | A person may assert and look for evidence afterwards |
| `IMPORTED` | no | Support, if any, came with it |

`ClaimOrigin.INFERRED` and `ClaimType.INFERRED` are different fields answering
different questions — who produced it, and what kind of assertion it is. A
deterministic extractor can produce an `INFERRED`-type claim, and an LLM can
produce an `OBSERVED`-type one.

Origin is **not** a quality ranking. A `MANUAL` claim is not more reliable than a
`DETERMINISTIC_EXTRACTION` one; it is differently accountable. Reliability lives
on Evidence, and confidence on the revision.

## 11. Choosing a type: the failure cases

Four mistakes, each with a symptom that shows up much later:

| Mistake | Why it is tempting | What it breaks |
|---------|--------------------|----------------|
| An interpretation filed as `OBSERVED` | The arithmetic is exact, so the claim feels factual | An aggregator weights an interpretation as a source fact |
| An unsupported idea filed as `INFERRED` | `HYPOTHESIS` feels weak, and someone wants it to count | Unsupported assertions enter scoring |
| An extrapolation filed as `INFERRED` | Both are reasoning steps | A forecast is never tested against what happened |
| A recommendation filed as `INFERRED` | It reads like a conclusion | The goal it assumes is never stated or challenged |

When two types are arguable, choose the **stronger** one — the one asserting
more. An `INFERRED` claim that could have been `OBSERVED` costs a little weight.
An `OBSERVED` claim that should have been `INFERRED` is a fabrication with a
citation attached.
