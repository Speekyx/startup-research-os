# Signal Contract V1

**Status:** Authoritative, and **implemented**. Mission 1.11.1 added the first
two extractors and **five real Signals**: four `numeric_period_change` and one
`lexical_frequency_contrast`. Two contract values were added while implementing
— see §21.
**Date:** 2026-08-30 (Sprint 1 / Mission 1.11)
**Code:** `sros_signal_model` (`packages/signal-model/python`)
**Schema:** `sros.signal/1`
**Related:** [`signal-model-gap-analysis-v1.md`](signal-model-gap-analysis-v1.md)
(written first, per §32), [`signal-taxonomy-v1.md`](signal-taxonomy-v1.md),
[`signal-temporal-semantics-v1.md`](signal-temporal-semantics-v1.md),
[`normalized-record-v1.md`](normalized-record-v1.md),
[`../domain/evidence-aggregation-framework-v1.md`](../domain/evidence-aggregation-framework-v1.md),
[`../domain/claim-model-v1.md`](../domain/claim-model-v1.md),
[ADR-020](../architecture/adr/ADR-020-signal-derivation-model.md).

---

## 1. The chain, and what each step adds

```text
RawRecord          what a source returned, byte for byte
    |   preserve
NormalizedRecord   what that observation structurally IS, in canonical form
    |   DERIVE      <- this layer
Signal             a reproducible statement about a RELATION between observations
    |   interpret
Claim / Evidence   a proposition, and records bearing on it with a direction
    |   synthesise
Opportunity        a product or business proposal
    |   evaluate
Score              a bounded judgment, with its four masses beside it
```

Each arrow is one semantic operation and no arrow may be skipped.

| Layer | Adds | Never does |
|---|---|---|
| **NormalizedRecord** | Renames and reshapes into canonical form. Source-preserving, deterministic, no market reading | Compare. Combine. Interpret |
| **Signal** | States a **relation between two or more observations**, with the transformation named, the parameters fingerprinted, the lineage machine-readable and a confidence in the derivation itself | Assert a proposition. Take a side. Weigh sources. Resolve disagreement |
| **Evidence** | Attaches a record to a **Claim**, with a direction, a relevance, a directness, a reliability and an independence state | Exist without a claim |
| **Claim** | The proposition evidence accumulates against, typed `OBSERVED / INFERRED / PREDICTED / RECOMMENDED / HYPOTHESIS` | Exist without a statement |
| **Opportunity** | Product and business synthesis over claims | Be derived from one signal |
| **Score** | `EvidenceScore` 0–100 with its four masses, under a **calibrated** profile | Exist today — D-03, no calibrated profile |

The distinction the whole mission turns on:

```text
"GDELT counted climate 55 times in bucket 20260830091500"   <- observation
"climate occurred 1.47x as often as weather in that bucket" <- Signal
"there is growing demand for climate-adaptation tooling"    <- Claim
"build a climate-risk dashboard for insurers"               <- Opportunity
```

Nothing in this contract can turn the first into the third.

---

## 2. What a Signal is

> A **Signal** is a reproducible statement about a relation between two or more
> canonical observations, produced by a named extractor at a named version over
> stated parameters, carrying its own lineage, its own scope, its own temporal
> basis, and a confidence in the derivation — and asserting nothing about what
> the relation means.

Five words in that sentence are load-bearing.

- **relation** — not a value. §3.
- **two or more** — §3 again, and it is the rule most likely to be argued with.
- **named extractor at a named version** — §8. A result nobody can reproduce is
  not a finding.
- **stated parameters** — §7. A hidden default makes the version meaningless.
- **asserting nothing about what it means** — §12, §13, §14.

---

## 3. Can one normalized observation be a Signal?

**No.** This is the mission's §37 and it has an answer rather than a preference.

### The contrast rule (S-1)

> A Signal asserts something that cannot be read off any one of its inputs. A
> derivation whose output is a function of exactly one observation, and whose
> assertion is recoverable from that observation's payload alone, is the
> observation renamed.

`LEXICAL_FREQUENCY_OBSERVED(climate, 55)` adds nothing to a normalized record
that already says `climate`, `55`, `ENGLISH`, `20260830091500`. Copying it into
a table called `signals` would make a downstream reader believe a derivation had
happened. That is worse than not having the row.

### Why it is stated as a count of observations

A contrast needs something to contrast *against*. There are exactly two
candidates:

1. **another observation** — available, and free of invented parameters;
2. **a reviewed reference baseline** — a threshold or a norm with a stated
   basis. **None exists.** Inventing one is the D-03 pattern that
   `evidence-aggregation-framework-v1.md` §9 forbids by name: no universal
   half-life, no per-source constant, no number nobody fitted.

So V1's rule is the mechanical one:

```text
at least TWO DISTINCT source observations must contribute
```

and the doorway is named rather than nailed shut: if a reviewed baseline is ever
authorised, with a basis recorded the way the geography map records one, S-1 is
revisited by an ADR and not by an extractor deciding for itself.

### Distinct by observation, never by row

Distinctness is over `observation_key`, **not** over `normalized_record_id`.

One observation can have several normalized rows — a revision, or a newer
normalizer version — and **D-08** has not decided which a consumer should read.
Counting rows would let a normalizer version bump manufacture a contrast out of
one observation, which is a fabricated finding produced by an upgrade.

A derivation whose contributing inputs contain two rows sharing an
`observation_key` is **refused** with `AMBIGUOUS_OBSERVATION_LINEAGE`. That
fails closed on precisely the case D-08 leaves open, and it does not decide it.

---

## 4. Family and type

Full reasoning in [`signal-taxonomy-v1.md`](signal-taxonomy-v1.md).

| | |
|---|---|
| `quantity_family` | **Closed enum** `SignalQuantityFamily`: `LEXICAL_FREQUENCY`, `MEASURED_SERIES`. What kind of quantity the signal is about |
| `signal_type` | **Registry** reference (`signal_type`). Two entries: `lexical_frequency_contrast`, `numeric_period_change` |

**The demand families are not this axis.** `PAIN / DESIRE / BEHAVIORAL /
MARKET` classify demand; neither V1 derivation is evidence of demand. Ontology
V2 §3.6 is unchanged.

The family must match the record kind of every contributing input —
`LEXICAL_FREQUENCY` from `lexical_frequency_observation`, `MEASURED_SERIES` from
`numeric_observation` — and a mismatch is `INCOMPATIBLE_INPUT_KINDS`.

---

## 5. Magnitude — exact, typed, and not a strength

```text
magnitude             Decimal, exact, never a float
magnitude_kind        ABSOLUTE_CHANGE | RATIO | OBSERVATION_COUNT
magnitude_unit        the unit string, or absent
magnitude_unit_state  INHERITED | DIMENSIONLESS | NOT_ESTABLISHED
```

| Kind | Meaning | Unit |
|---|---|---|
| `ABSOLUTE_CHANGE` | A difference in the inputs' own quantity **over time** | `INHERITED` where the inputs published one, `NOT_ESTABLISHED` where they did not |
| `ABSOLUTE_DIFFERENCE` | A difference between two quantities measured at the **same position** — two terms in one bucket | as `ABSOLUTE_CHANGE` |
| `RATIO` | One quantity relative to another | **must** be `DIMENSIONLESS` |
| `OBSERVATION_COUNT` | How many observations satisfied the derivation's condition | **must** be `DIMENSIONLESS` |

**No normalized 0–100 strength exists, and none is deferred pending a formula.**
Mission 1.11 §8 permits one only where a cross-signal comparison justifies it,
and §30 states the reason none does: a GDELT term frequency and a World Bank
population figure are not measurements of comparable things. A shared scale
would be a comparison manufactured by the act of storing them together.

**The unit is inherited, never named.** GDELT publishes four columns and none is
a unit, so a change over GDELT counts is `NOT_ESTABLISHED` — the same answer the
normalizer gives, carried up rather than resolved. `"mentions"`, `"occurrences"`
and `"articles"` appear nowhere in this layer either.

**Exact decimals, never floats.** The normalization layer parses source numbers
with `parse_float=Decimal` so IEEE-754 never touches them. A derivation that
rounded its result through a float would hand that guarantee back at the first
subtraction.

---

## 6. Direction — change only, and never sentiment

```text
INCREASING | DECREASING | UNCHANGED | INDETERMINATE | NOT_APPLICABLE
```

| Value | Meaning |
|---|---|
| `INCREASING` | The quantity is larger at the later position |
| `DECREASING` | Smaller at the later position |
| `UNCHANGED` | Equal. Not "stable" — stability is a claim about variance over a window, which two points cannot support |
| `INDETERMINATE` | The comparison ran and did not resolve to a direction |
| `NOT_APPLICABLE` | The derivation has no ordered relation, so direction is not a question it answers |

**`POSITIVE` and `NEGATIVE` are deliberately absent.** They are the sentiment
overload Mission 1.11 §7 warns about, and they were on the candidate list. A
complaint-frequency signal can be `INCREASING` while the sentiment of the
underlying text is negative; one enum holding both would make that sentence
unrepresentable.

**Sentiment is not modelled at all in V1.** Nothing measures it, no source
supplies it, and a nullable column nothing can fill is an invitation to fill it
by resemblance. When a source and an extractor for it exist, it is a separate
axis with its own confidence, and direction is not widened to hold it.

### Direction requires an order

```text
direction != NOT_APPLICABLE  =>  temporal basis is ORDERED_PERIODS or COMPARABLE_INSTANTS
```

Enforced in the constructor and in the database. "Increasing" is a statement
about before and after, so a derivation with no established order cannot make
it. While H-29 and H-32 are open this means **no GDELT signal can carry a
direction**, which is the correct consequence rather than an inconvenience.

---

## 7. Parameters, and why they are fingerprinted

Every value that affects the output is stated. Mission 1.11 §29: a signal is not
reproducible if its parameters are hidden defaults.

```text
parameters             a mapping, canonically serialised: sorted keys, exact
                       decimals as text, no incidental whitespace
parameter_fingerprint  sha256 over that serialisation
```

The extractor **declares its parameter names**, and the mapping's keys must
equal that declaration exactly. A name declared and not supplied is
`PARAMETERS_INCOMPLETE`; a key supplied and not declared is the same refusal
from the other side. The model does not know what any extractor's parameters
should be, and it does not have to — it only enforces that the extractor said.

The fingerprint enters the derivation identity, so the same inputs under
different parameters are two signals rather than one overwriting the other.

---

## 8. Extractor identity and versioning

```text
extractor_id            e.g. world-bank-numeric-change
extractor_version       semantic version of the DERIVATION
signal_schema_id        sros.signal
signal_schema_version   1
derivation_kind         DETERMINISTIC | MODEL_DERIVED
model_version           only when MODEL_DERIVED
prompt_version          only when MODEL_DERIVED
```

Three versions, independent on purpose, exactly as
`normalized-record-v1.md` §21 argued one layer down: the canonical schema
changes when what a Signal *means* changes; an extractor version changes when
its derivation changes; a model version changes when a provider ships a model.
One column could not carry three things that move separately.

**A change in derivation semantics produces coexistence, never a rewrite.** A
`1.1.0` extractor writes rows beside the `1.0.0` ones; neither supersedes the
other. **This does not solve D-08** — which of several derived rows a consumer
should read is the same unanswered question one layer up, and Mission 1.11 §18
says not to answer it incidentally.

**Deterministic is the default and is structurally enforced.**
`DETERMINISTIC` requires `model_version` and `prompt_version` to be **absent**;
`MODEL_DERIVED` requires a model version. Mission 1.11 §23's rule — a Signal is
not inherently LLM-generated — is a constraint rather than a sentence.

---

## 9. Lineage

Machine-readable and mandatory. Per input:

```text
normalized_record_id   which representation was read
raw_record_id          what the source said, and when
source_id              which source
observation_key        WHICH observation, stable across revisions and versions
record_kind_id         what shape it was
period_type            the resolution it carried
quality                VALID | PARTIAL | INVALID, as recorded
quality_reasons        the reasons it carried
role                   CONTRIBUTED | EXCLUDED
refusal_reason         why, when EXCLUDED
withheld_facts         which required facts it could not supply
```

**Excluded inputs are recorded, not dropped.** "We looked at ten and used six"
must be visible, and a Signal that quietly used six of ten is indistinguishable
from one that was offered six.

**The lineage is denormalized on purpose.** `source_id`, `raw_record_id` and
`observation_key` are copied onto the input row rather than joined, for the
reason migration 0009 copied provenance onto the normalized record: raw records
expire eleven months before the rows that reference them.

### What lineage deliberately does not carry

**No independence state, no group id, no reliability, no weight.** Mission 1.11
§22 is explicit: two signals are not independent merely because they came from
two records. This layer preserves the **facts** — which sources, which raw
records, which origins — and Evidence Aggregation makes the judgement with them
(`evidence-aggregation-framework-v1.md` §7). A judgement made here would be made
without the claim it is relative to.

---

## 10. Quality interaction — required facts, not a quality filter

Mission 1.11 §10 and §11. This is the part that would be easiest to get wrong by
being simple.

**`INVALID` is never derivable from.** A record that could not be represented
must not be read as an observation; that is `NormalizedRecordQuality`'s own
contract. An `INVALID` input is excluded with `INPUT_RECORD_INVALID`.

**`PARTIAL` does not mean unusable.** What matters is whether the *specific*
missing fact matters to the *specific* derivation. Every GDELT record is
`PARTIAL`, and a within-bucket contrast between two terms needs neither of the
two things it is missing.

### `SignalRequiredFact`

A closed vocabulary. Each value declares which record kinds can supply it and
which `NormalizationQualityReason` values withhold it.

| Fact | Supplied by | Withheld by |
|---|---|---|
| `EXACT_NUMERIC_VALUE` | both kinds | `VALUE_NOT_REPORTED`, `MALFORMED_NUMERIC_VALUE` |
| `LEXICAL_TERM` | `lexical_frequency_observation` | — |
| `SOURCE_PERIOD_LABEL` | both kinds | `PERIOD_NOT_SUPPORTED` |
| `SOURCE_RELATIVE_ORDER` | both kinds | `PERIOD_NOT_SUPPORTED`, `PERIOD_TIMEZONE_NOT_ESTABLISHED` † |
| `COMPARABLE_INSTANT` | both kinds | `PERIOD_NOT_SUPPORTED`, `PERIOD_TIMEZONE_NOT_ESTABLISHED` |
| `SOURCE_LANGUAGE_LABEL` | `lexical_frequency_observation` | — |
| `CANONICAL_LANGUAGE` | `lexical_frequency_observation` | `LANGUAGE_NOT_MAPPED` |
| `CLASSIFIED_GEOGRAPHY` | `numeric_observation` | `GEOGRAPHY_NOT_CLASSIFIED`, `GEOGRAPHY_MISSING` |

† **unless the source appears in the reviewed order certification.** That map is
`ORDER_ESTABLISHED_WITHOUT_TIMEZONE` and it is **empty**. An entry is a reviewed
finding and requires a stated basis, exactly as a geography map entry does; it
is the mechanism by which H-32 would be closed for GDELT without H-29 being
answered. See [`signal-temporal-semantics-v1.md`](signal-temporal-semantics-v1.md) §3.4.

A fact whose `withheld_by` set is empty is not decorative: it is checked against
the **record kind**, so a derivation requiring `LEXICAL_TERM` over a numeric
observation is refused rather than silently reading a field that is not there.

**The extractor states what it requires. The model computes what is withheld.**
Neither guesses.

---

## 11. Lifecycle — there is none, and that is the decision

Mission 1.11 §27 asks whether a blocked derivation should leave an artifact.

**A Signal exists only when its derivation completed.** There is no `DRAFT`
(nothing drafts), no `INVALID` (a failed derivation produces no row), no
`BLOCKED` and no `INSUFFICIENT_DATA`. A row in a table of signals says a signal
exists, and a row meaning "no signal exists" is a misleading signal — which is
the brief's own stated preference, and reason enough on its own.

`NormalizedRecordQuality` is **not** reused. It states whether a source
observation could be structurally represented; a Signal's inputs may be
`PARTIAL` for reasons that do not touch the derivation, so propagating the state
would carry a word that means something else.

What exists instead is `SignalDerivationRefusal` — a **returned value object**,
never a row:

```text
INPUT_RECORD_INVALID              an input is INVALID
REQUIRED_FACT_WITHHELD            a required canonical fact is absent
AMBIGUOUS_OBSERVATION_LINEAGE     two contributing rows are one observation (D-08)
INCOMPATIBLE_INPUT_KINDS          inputs disagree on record kind or resolution
INCOMPATIBLE_SERIES               same kind, different thing: metric, geography,
                                  unit, dataset, bucket, language label, gram size
INSUFFICIENT_INPUT_OBSERVATIONS   fewer than two distinct observations remain
UNSUPPORTED_SIGNAL_TYPE           no registered type
PARAMETERS_INCOMPLETE             a parameter affecting output was not stated
```

The same vocabulary explains a single excluded input and a whole refused
derivation, because the second is usually the first having happened often
enough. Where a refusal should be **logged** is a derivation-run concern for the
extractor mission, not a shape this table needs.

---

## 12. Confidence — one number, about the derivation

```text
derivation_confidence   [0,1], required
```

> Confidence that this derivation computed what it says it computed, given the
> inputs it used.

It is **not**: confidence that the phenomenon is real; confidence that the
sources are reliable; an evidence strength; a probability; an `EvidenceScore`
input.

**A deterministic extractor's derivation confidence is 1.0, and that is not a
claim about the market.** The subtraction is exact. Mission 1.11 §38 names this
trap precisely — high derivation confidence over weak coverage — and the model
answers it by keeping the number narrow and putting the coverage facts beside
it, unweighted: how many observations contributed, how many were excluded and
why, how many distinct sources, over what window. Counts are diagnostics and
never multipliers, exactly as `evidence-aggregation-framework-v1.md` §11
requires.

**`derivation_confidence` is not split into a second `evidence_strength`.**
Mission 1.11 §38 offers the option and the existing architecture answers it:
evidence strength is claim-relative, and a Signal has no claim. A second number
here would be an `EvidenceScore` under another name, computed without the thing
that gives it meaning.

Magnitude and confidence are independent. A large change computed from two
observations has a large magnitude and says nothing about whether two
observations were enough.

---

## 13. Scope

A Signal states what it is about. **A dimension no input carries has no key at
all** — never a null — the same rule the lexical record kind follows for
geography.

| Dimension | Present when |
|---|---|
| `source_ids` | Always. Must equal the distinct sources of the contributing inputs |
| `terms` | `LEXICAL_FREQUENCY`. The source text verbatim, in derivation order |
| `metric_ids` | `MEASURED_SERIES` |
| `source_language_labels` + `source_language_scheme` | Where the inputs carry a language label |
| `canonical_language_tags` | Only where `CANONICAL_LANGUAGE` was required and available. **Refused while H-30 is open** |
| `geography_codes` | `MEASURED_SERIES`, where classified |

**A `LEXICAL_FREQUENCY` signal may not carry a geography**, and the constructor
refuses one. A language is not a place — `CanonicalLanguage`'s rule, enforced a
layer up where the temptation to fill the field is stronger.

**No market, category, topic or motivation dimension exists.** A lexical term is
not a topic; turning `climate` into a category is classification, which is a
later stage with its own confidence and its own failure modes.

---

## 14. Temporal semantics

Summarised here; the argument is in
[`signal-temporal-semantics-v1.md`](signal-temporal-semantics-v1.md).

```text
basis              NONE | SAME_PERIOD_LABEL | ORDERED_PERIODS | COMPARABLE_INSTANTS
period_labels      the source labels, verbatim, in derivation order
resolution         the period type every input shares
observation_count  how many contributed
start / end        aware datetimes, ONLY under COMPARABLE_INSTANTS
```

- **`start` and `end` exist only under `COMPARABLE_INSTANTS`.** No other basis
  may carry bounds, and none may carry naive ones.
- **`observed_at` is `NULL` unless the basis is `COMPARABLE_INSTANTS`**,
  enforced by a database CHECK.
- **Every input must share the window's resolution.** Mixing a `YEAR` and an
  `INTERVAL` is `INCOMPATIBLE_INPUT_KINDS`, never silently coarsened.

---

## 15. Identity

```text
derivation_fingerprint = sha256(canonical_json({
    schema:            {id, version},
    workspace_id,
    signal_type:       {registry, id},
    quantity_family,
    extractor:         {id, version},
    inputs:            [{observation_key, normalized_record_id}, ... contributed, in order],
    parameter_fingerprint,
    window:            {basis, period_labels, resolution},
}))

id = uuid5(SIGNAL_NAMESPACE, derivation_fingerprint)
```

**In the identity:** workspace, type, family, extractor and version, schema
version, the ordered contributing inputs, the parameter fingerprint, the window.

**Not in the identity, and each for a reason:**

| Excluded | Why |
|---|---|
| `derived_at`, `correlation_id` | Volatile. Including either would make every re-run a new signal — the trap the raw layer avoided by keeping retrieval time out of `content_hash` |
| `magnitude`, `direction`, `derivation_confidence` | **Outputs.** A changed magnitude under an unchanged identity means the extractor is not deterministic or an input changed, and that must be *reportable* rather than absorbed into a new row |
| `research_session_id` | §16 |
| excluded inputs | The same signal is reached whether or not an unusable record was offered |

---

## 16. Research sessions and tenancy

**`workspace_id` is in the identity. `research_session_id` is not.**

Mission 1.11 §39 asks whether the same observations may contribute to signals
across sessions. They may, and they converge on **one** signal.

Making the session part of identity would give each session its own row for the
same derivation, and the aggregation layer would be entitled to read two rows as
two findings — manufacturing independence out of scheduling. Ontology V2 §12
already settled the same question for Opportunity and Mission 1.2 applied it to
Claim: sessions produce observations; the artifact is not owned by the session
that first met it.

The session that derived a signal is recorded as lineage. If per-session
attribution of a shared signal is ever needed,
`research.claim_session_observations` is the existing shape for exactly that
problem and is available unchanged.

**Tenancy** is the Workspace, two layers as always: explicit repository filters
and PostgreSQL RLS. Cross-tenant links are refused by **composite foreign
keys**, not by convention — a signal input in workspace A cannot reference a
normalized record in workspace B, and evidence in A cannot reference a signal in
B.

---

## 17. Relation to Evidence

**A Signal is not Evidence, and it does not become Evidence by being cited.**

```text
NormalizedRecords --derive--> Signal --cited by--> Evidence --bears on--> Claim
```

`scoring.evidence.signal_id` already exists and is the intended link. What
Evidence adds is everything that requires a claim: `direction` (supports or
contradicts *what*), `relevance` (to *what*), `directness`, `reliability`,
`extraction_confidence`, `observation_category`, `independence_state` and an
independence group. None of those is a property of a derivation; all of them are
properties of a derivation **relative to a proposition**.

**No aggregation happens in this layer.** No `q_i`, no group strength, no
saturation, no masses, no `EvidenceScore`. The framework stays where it is and
its parameters stay uncalibrated (D-03).

---

## 18. Contradiction, and why it is not resolved here

Two signals may disagree — one source's quantity rising while another's falls.
**Each remains independently derived and independently stored.**

Contradiction is not a defect in a signal; it is information about the world,
and `data-principles.md` §10 requires competing observations to be preserved
rather than overwritten. Resolution belongs to evidence aggregation, which
decomposes agreement and disagreement into four masses that sum to 1 —
deliberately **not** a flat penalty, and deliberately claim-relative.

A Signal has no claim, so it has nothing to disagree *about* yet. Resolving here
would mean discarding one derivation on the basis of another, with no
proposition to judge either against.

---

## 19. Deterministic and model-derived extraction

**V1 is designed so the first extractors are purely deterministic.** Every field
above can be produced by arithmetic over canonical values: exact decimals, label
equality, set cardinality. No model is required to produce a Signal, and none is
called anywhere in this mission.

A model-derived extractor may exist later. If it does, `derivation_kind =
MODEL_DERIVED` obliges it to carry model provenance, and four rules from
`llm-reasoning-rules.md` apply unchanged: provider and model version recorded
(§9), source content placed in a delimited data region and never read as
instructions (§7), outputs validated against a schema before use, and a
validation failure treated as a possible injection attempt rather than retried
blindly.

**The cost ladder still applies** (§8): rules before classical NLP before
embeddings before an LLM. A model call per observation, at the volume this layer
sits at, is a design error.

---

## 20. What this layer must never do

- Assert demand, interest, popularity, attention or momentum. A rising count is
  a rising count.
- Turn a lexical term into a topic, a category, a market or a product.
- Compare quantities across sources on a shared scale.
- Invent a threshold, a baseline, a half-life, a weight or a reliability.
- Assign a timezone, or place an unzoned observation on a shared timeline.
- Map a source language label to a canonical tag.
- Resolve a contradiction, estimate independence, or produce a score.
- Store a row that means no signal exists.

---

## 21. What implementing it changed (Mission 1.11.1)

Two values, both because the contract could not say something true. Contract
`1.6.0` → `1.7.0`; nothing else in this document was revised.

### `SignalMagnitudeKind.ABSOLUTE_DIFFERENCE`

`ABSOLUTE_CHANGE` asserts that something **changed**, which is a statement about
time. A same-bucket contrast between two lexical terms is a difference between
two quantities measured at the same position: nothing changed, and using the
temporal value would have asserted a temporality H-32 says is not established.

A consumer branching on magnitude kind has to be able to tell a contrast from a
movement, which is the test §5 already applies to a ratio and a difference.

### `SignalRefusalReason.INCOMPATIBLE_SERIES`

`INCOMPATIBLE_INPUT_KINDS` means *the inputs disagree on record kind or period
resolution*. Two World Bank observations of **different countries** disagree on
neither — same kind, same `YEAR` resolution — and are still not observations of
the same measured series. The same holds for two GDELT terms from different
buckets, different language labels or different gram sizes.

One value covers every case and the `detail` names the field that disagreed.
Mission 1.11.1 §34 offered four separate codes for it; four codes for one
question would make a consumer branch on which field happened to differ.

### What did NOT change

Nothing about identity, lineage, scope, confidence, quality interaction or the
two-observation rule needed revision. The extractors were written against §1–§20
as shipped, and the required-fact machinery worked unchanged on the first real
`PARTIAL` inputs.