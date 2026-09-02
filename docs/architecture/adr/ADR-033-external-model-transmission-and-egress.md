# ADR-033 — Model inference and external model transmission are two activities

**Status:** Accepted — Mission 1.23. Amends the source-activity vocabulary
(ADR-013) and the use-profile contract (ADR-027). Extends ADR-006's separation of
business services from providers.

---

## Context

Mission 1.22 tried to run the first semantic inference in this repository and
stopped at a gate it could not open. The Stack Exchange review says:

> "MODEL INFERENCE IS PERMITTED; TRAINING IS NEITHER ASSESSED NOR AUTHORISED.
> Reading and classifying licensed text is use within the licence's own grant to
> reproduce and to produce Adapted Material."

That answers **may a model read this material**. It does not answer **may this
material leave the deployment so that a third party's model can read it**.

**The silence was structural rather than an omission.** `ASSESSED_ACTIVITIES` had
one slot — `model_processing` — and `AssessedUseProfile` had one boolean —
`model_inference`. Neither could express where inference executes, so **no review
could have scoped itself to a location even if its author had wanted to.** The
profile's `deployment: LOCAL` says where SROS runs, not where inference runs.

This is the same shape Mission 1.15.4 found when every review had assessed a use
case the model never recorded: a distinction the system needs, discovered by the
first operation that needed it.

## Decision

**Represent three questions where there was one.**

### 1. A new source activity: `external_model_transmission`

Added to `ASSESSED_ACTIVITIES`. It asks: **may material derived from this source
be transmitted outside the local SROS deployment to a third-party model
processor?**

`model_processing` keeps its meaning unchanged — *may a model read this material*
— and every existing review keeps its answer. Nothing is reinterpreted.

**Historical reviews are not rewritten.** `PolicyReview.assessment()` already
returns `NOT_ASSESSED` for an activity a review does not carry, so every review
written before this ADR reads as *nobody looked* — which is true, and is
distinguishable from both `PERMITTED` and `NOT_PERMITTED`.

**It is NOT one of rule 8's materially required activities.** Rule 8's six gate
whether a source may be collected from at all. This one gates one operation:
external inference. A World Bank deterministic acquisition must not fail because
nobody assessed LLM egress for it, and it does not.

### 2. A new profile field: `external_model_egress`

Three states, and the default fails closed:

| State | Meaning |
|---|---|
| `NOT_ASSESSED` | this deployment has not decided. **Default.** Refuses external inference |
| `DENIED` | this deployment does not permit source-derived content to leave for model processing |
| `PERMITTED_TO_APPROVED_PROVIDERS` | permitted, and only to a provider whose posture is approved |

**A boolean could not carry this.** `false` would conflate *decided against* with
*never asked*, and those are the two states this repository spends most of its
care keeping apart.

**`model_inference` stays a boolean and keeps its meaning.** It says the activity
is in scope for the deployment. Egress is a separate axis, and a local inference
provider would need the first and not the second — which is the clearest
statement of why they are two fields.

### 3. Provider processing posture, outside the source registry

A provider's data handling is a fact about the provider, not about a source
(§7 of the mission brief). It lives in `model-provider-policy-v1.json` with its
own first-party evidence and retrieval dates, and the source registry never
names a vendor.

## The runtime decision

Four layers, all required, checked **before any source text is serialised**:

```text
source review    external_model_transmission is PERMITTED*      for (source, profile)
     AND
use profile      external_model_egress is PERMITTED_TO_APPROVED_PROVIDERS
     AND
provider policy  the provider's posture is APPROVED for this class of content
     AND
runtime          the configured provider IS that provider, and is configured
     → authorized
```

Any missing answer refuses, and **each layer refuses with its own reason code**
rather than a shared `MODEL_NOT_AVAILABLE`. An operator who cannot tell a
governance refusal from a missing credential will change the wrong thing.

## Consequences

- `ASSESSED_ACTIVITIES` grows from eleven to twelve. No catalog row changes.
- `AssessedUseProfile` grows one field, defaulting to the closed state. Both
  registered profiles state it **explicitly** in this mission rather than
  inheriting the default silently.
- A new refusal vocabulary names each gate.
- Deterministic acquisition is untouched: no collector, normalizer, extractor or
  interpreter consults any of this.

## What this does not decide

**It does not authorise anything.** It gives the model a place to record an
answer; the answers are review acts, and Mission 1.23 performs one of them for
one source and one profile.

**It does not make a provider safe.** An approved posture records what a provider
contractually commits to, on retrieved evidence with a date. It is not a
guarantee, and it is not a legal opinion — `source-registry-v1.md` §0 applies
here exactly as it does to sources.

**It does not decide copyright.** Whether a licence permits transmission to a
processor and whether a provider's terms handle it acceptably are two questions
answered by two instruments. Neither substitutes for the other.
