# Deterministic OBSERVED Claim Interpreter V1

**Authoritative.** Mission 1.13.1, fourth template added in Mission 1.15.11.
`observed-signal-restatement@1.1.0`.

Implementation: `services/nlp/python/sros_nlp/interpreters/`.
Runtime: `claim-interpretation-runtime-v1.md`.
Contract it obeys: `claim-evidence-interpretation-contract-v1.md`.

The first thing in the system that crosses the interpretation boundary. It
crosses it in the smallest possible way: it says a Signal back, with the source
named.

---

## 1. What it is

One interpreter, four templates, no fallback.

| Signal type | Proposition shape |
|-------------|-------------------|
| `numeric_period_change` | *{Source} reported that "{metric}" for "{geography}" increased/decreased/was unchanged between "{period A}" and "{period B}" by {magnitude}.* |
| `lexical_frequency_change` | *{Source} reported that, in its "{stream}" stream under source language label "{label}", the term "{term}" appeared {n} more/fewer times in source bucket "{later}" than in the preceding source bucket "{earlier}".* |
| `lexical_frequency_contrast` | *{Source} reported that, in its "{stream}" stream under source language label "{label}", within source bucket "{label}", the term "{A}" appeared {n} more/fewer times than the term "{B}".* |
| `procurement_value_contrast` | *{Source} reported that, in its "{resource}" resource, within a bounded set of {n} "{notice class}" notices classified under "{scheme}" division "{division}", the largest "{amount type}" amount at "{scope}" scope stated in "{currency}" exceeded the smallest by {magnitude}.* |

`interpretation_kind` is `DETERMINISTIC`. `model_version` and `prompt_version`
are `NULL`, and the database refuses a `DETERMINISTIC` interpretation that
carries either.

**A Signal type with no template is `UNSUPPORTED_SIGNAL_TYPE`.** There is no
generic prose path. A sentence nobody specified is a proposition nobody
reviewed, and a deterministic interpreter that improvised would be neither.

## 2. Structurally OBSERVED

`_CLAIM_TYPE = ClaimType.OBSERVED` is a module constant read by every template.
`interpret(signal, request)` takes no claim-type parameter, and none of
`INFERRED`, `PREDICTED`, `RECOMMENDED` or `HYPOTHESIS` appears in any code path.

This is not "it defaults to OBSERVED". `validate_claims.py` walks the AST of
every module in the package and fails the build on any `ClaimType.X` attribute
access where `X` is not `OBSERVED` — over the syntax tree, not the text, so a
docstring naming `INFERRED` cannot fail it and a rename cannot slip past it.

There is no low-confidence-inferred escape hatch. Adding `INFERRED` is a version
bump with a document behind it, because an inference needs a stated reasoning
step and this interpreter has none to state.

## 3. Attribution is the whole point

> `OBSERVED` asserts what a source **reported**, attributed to that source.

Every statement begins with the source's canonical name and the words
"reported that". None of them asserts the fact without the attribution:

| Produced | Not produced |
|----------|--------------|
| "World Bank Open Data reported that "SP.POP.TOTL" for "Germany" increased…" | "Germany's population increased…" |

The second is a claim about demography; the first is a claim about a
publication. They have different falsifiers, and only the first is `OBSERVED`
from a World Bank record (`claim-epistemic-semantics-v1.md` §3).

Three attribution details come from the **contributing normalized records**
rather than from the Signal's scope, which does not carry them:

- `series.resource_id` — which published stream
- `geography.source_name` — what the source itself called the entity
- `term.scheme` / `language.source_scheme` — which vocabulary

Every one must be **agreed by all contributing records**; disagreement is
`AMBIGUOUS_SIGNAL_LINEAGE` and absence is `SIGNAL_LINEAGE_UNAVAILABLE`. The
interpreter refuses rather than picks.

The geography is deliberately the source's own name (`Germany`), not our
canonical code (`DE`). The code is what a reviewed mapping decided; the name is
what the source published, and OBSERVED reports the second.

The source's display name comes from `registry.sources.canonical_name` — the
authoritative registry, not a map in the interpreter — and falls back to the
source id when the registry has not named one. Terser, never wrong.

## 4. H-29 and H-30, in the wording

**H-29 (bucket timezone unestablished).** ADR-022 certified
`SOURCE_RELATIVE_ORDER` for the WEB-NGRAM stream and explicitly not
`COMPARABLE_INSTANT`. So the templates say **"source bucket"** and
**"the preceding source bucket"**, and never a clock time, a date, a timezone or
an alignment with another source.

The bucket labels *are* named — `"20260830190000"` — because a claim that cannot
say which buckets is not checkable. They are named as quoted source labels, in a
sentence that says "source bucket" twice. Nothing converts one, and
`validate_claims.py` fails the build on `astimezone`, `now`, `utcnow`,
`localtime`, `fromtimestamp` or a `tzinfo=` keyword anywhere in the package.

`scoring.evidence.observed_at` is written `NULL`. It is a globally comparable
instant, and setting it from the claim's creation time would date the evidence
to when we looked.

**H-30 (CLD2 mapping unestablished).** The templates say **"under source
language label "ENGLISH""** and the fact set carries
`language_source_scheme: cld2-language-name`. They never say "in English", and
`language.canonical_tag` is **never read** — asserted over call arguments and
subscripts by `validate_claims.py`, so the prose explaining the rule cannot fail
it.

**Each template accepts only the temporal bases it can phrase**, and refuses the
rest with `INCOMPATIBLE_TEMPORAL_SEMANTICS`:

| Template | Accepts |
|----------|---------|
| `numeric_period_change` | `COMPARABLE_INSTANTS`, `ORDERED_PERIODS` |
| `lexical_frequency_change` | `ORDERED_PERIODS` |
| `lexical_frequency_contrast` | `SAME_PERIOD_LABEL` |
| `procurement_value_contrast` | `NONE` |

A lexical change Signal arriving on `COMPARABLE_INSTANTS` would mean H-29 had
closed, and the sentence to write for it is a decision rather than a default.

## 5. The vocabulary guard, upgraded

Mission 1.13's guard was `term in statement.lower()`. Mission 1.13.1 replaced it
with **token matching over unquoted prose**, for two reasons that both showed up
immediately:

1. **Substrings produce false positives.** `supermarket` and `marketing` contain
   `market`; so does the metric id `CM.MKT.LCAP.CD` under a looser reading. A
   guard that refuses honest text gets loosened until it stops guarding.
2. **Quoted spans are source data.** A GDELT term is arbitrary text. `market`,
   `demand` and `pain` are all real English words a news corpus contains, and
   refusing *`GDELT reported that the term "demand" appeared 12 more times`*
   would refuse the most faithful restatement available — the exact thing the
   guard exists to protect.

So the guard strips double-quoted spans, tokenises what remains on
`[a-z0-9]+`, and matches whole tokens plus multi-word phrases over the token
sequence. Every template puts source-supplied values in double quotes and its
own prose outside them.

The vocabulary was widened per §10: `attention`, `demand(s)`, `desire(s)`,
`interest(s)`, `market(s)`, `momentum`, `monetisation`/`monetization`, `mrr`,
`arr`, `opportunity`/`opportunities`, `pain(s)`, `popular`, `popularity`,
`revenue(s)`, `traction`, `trending`; and the phrases `willingness to pay`,
`customers want`, `users want`, `product market fit`, `growth opportunity`.

`growth` stays deliberately absent: "population growth" is the name of a
quantity a source publishes.

**The template is the primary protection.** The guard is a backstop that catches
the obvious failure; the reason no generated statement says "demand" is that no
template contains the word.

## 6. Proposition identity

`proposition_key` = sha256 over the canonical JSON of the facts the proposition
asserts, and `proposition_facts` stores the preimage (migration 0018) so the
identity can be verified rather than merely trusted.

| Template | Facts |
|----------|-------|
| numeric | `proposition`, `source_id`, `resource_id`, `metric_scheme`, `metric_id`, `geography_source_code`, `period_label_from`, `period_label_to`, `direction` |
| lexical change | `proposition`, `source_id`, `resource_id`, `term_scheme`, `term`, `gram_size`, `language_source_scheme`, `language_source_label`, `period_label_from`, `period_label_to`, `direction` |
| lexical contrast | `proposition`, `source_id`, `resource_id`, `term_scheme`, `term_a`, `term_b`, `gram_size`, `language_source_scheme`, `language_source_label`, `period_label`, `relation` |

Each carries a `proposition` discriminator, so two shapes cannot collide by
having coincidentally equal fields.

### 6.1 The magnitude is not part of the identity, and the relation is

The contract's §5.2 list — source, metric, geography, period labels, term,
direction — does **not** include the magnitude, and that is load-bearing:

> A source revising 187,180 to 187,200 has restated the **same proposition**.
> The amount is wording, and wording is what revisions are for.

So a re-interpretation after a source revision appends **revision 2** to the
existing claim rather than creating a second one. Revision 1 is never modified:
an aggregation that evaluated it must still be able to read it. That is §29's
question answered by the data model rather than by a policy.

For a **contrast**, `direction` is `NOT_APPLICABLE` by construction — nothing
changed — so the relation between the two terms would be lost. It is recovered
from the **sign** of the magnitude (`terms[0] - terms[1]`, over terms sorted by
text) and stored as `relation: GREATER | FEWER | EQUAL`. A revised count that
keeps the ordering is the same proposition; one that flips it is a different
one, and both are right.

### 6.2 What identity is never built from

- **Not the prose.** Two interpreters wording one fact differently produced one
  claim.
- **Not an embedding.** D-12 is open, and an identity that moved when the model
  moved would split and merge claims silently.
- **Not the Signal id.** Two derivations of one proposition converge on one
  claim; the Signal is cited as *evidence*, which is where lineage belongs.
- **Not the research session, correlation id or clock.** §27: a different
  session, correlation and clock produce the same key, the same statement, the
  same confidence and the same evidence relation. Asserted by test.

## 7. The Evidence it produces

One row per cited Signal. Every value is a decision, and the absent one is the
important one.

| Field | Value | Why |
|-------|-------|-----|
| `direction` | `SUPPORTS` | The claim *is* this Signal said back. It cannot bear against itself, and a generated `NEUTRAL` row is refused by the contract |
| `relevance` | `1.0` | How much what the Signal is about overlaps what the Claim is about. The same subject **by construction** — any lower value would describe a gap that does not exist |
| `directness` | `1.0` | The Signal bears on the Claim itself, not on something adjacent. Directness is not source truthfulness |
| `reliability` | **`NULL`** | Purpose-relative, and **D-03 is blocked**. There is no reviewed value for "World Bank population data, for a claim about what World Bank reported", and a constant would be the per-source coefficient the framework refuses. Approval status is not reliability either |
| `extraction_confidence` | `1.0` | The interpreter read the Signal correctly. A format string over structured facts either read them or raised. Says nothing about whether the source captured reality |
| `observation_category` | `UNCATEGORISED` | A population count is not `MARKET_ACTIVITY` — it is context. A news-corpus frequency is not `REPORTED_` or `OBSERVED_BEHAVIOUR` — nobody's behaviour was observed. Inventing a category for publication activity would be a taxonomy change made in passing |
| `independence_state` | `UNKNOWN` | Two Signals from one stream are not independent because they are two, and not dependent either. Record what you know, promote nothing |
| `evidence_level` | `1` | "Weak Signal", a small or isolated indication. Not invented here: it is where the ladder's own gates leave a single `UNCATEGORISED` record of `UNKNOWN` independence. Levels 2–3 need established independent groups; 4–5 are category-gated |
| `observed_at` | `NULL` | H-29 |

### 7.1 The consequence, stated rather than worked around

With `reliability` absent, **every one of these records is `NON_SCORABLE` with
`MISSING_RELIABILITY`.** Exercised against the real rows: seven claims, seven
items, zero scorable, status `UNAVAILABLE`, no score, nothing persisted.

That is the honest answer. Filling reliability in to make a number appear is the
failure `../domain/evidence-aggregation-framework-v1.md` §6 exists to prevent.

## 7.2 The fourth template, and why 1.1.0

Mission 1.15.11 added `procurement_value_contrast` and bumped the interpreter to
**1.1.0**. Full semantics in `ted-eu-observed-claims-evidence-v1.md`; three
things belong here because they are about the interpreter rather than about TED.

**Why a template and not a second interpreter.** The proposition is a Signal
restated with its source named, which is what this interpreter is. A template is
specific to a **Signal type**, never to a publisher, and a TED-specific
interpreter would have made the boundary source-shaped for no reason the
semantics required.

**Why a version bump for a purely additive change.** The three existing
templates render byte-identical statements, fact sets and evidence, and the
seven stored Claims keep `1.0.0` and gained no revision. What changed is the set
of propositions this interpreter can make, and that is version-worthy even when
nothing existing moves. `TestTheExistingThreeTemplatesDidNotMove` pins the two
statements and one proposition key, so "additive" is checked rather than
promised.

**Where its identity rule DIFFERS from the other three.** Everywhere else the
magnitude is wording and the periods are fixed by the query. Here the **cohort
membership is the subject**, so the contributing notice identifiers enter
`proposition_facts`: a revised amount appends a revision, and a fourth
qualifying notice is a different proposition. The member *values* stay out,
reachable through Evidence -> Signal -> `signal_inputs` -> `normalized_records`.

## 8. Determinism

Same Signal + same interpreter version → same proposition key, same statement,
same cited facts, same evidence relation, same interpretation confidence.

`interpretation_confidence = 1.0`, and it says exactly one thing: **the
interpreter correctly restated the Signal.** It is not how strong the evidence
is, not how likely the source fact is to be true, and not an `EvidenceScore`. A
deterministic restatement can hold `1.0` while the proposition it restates is
supported by a single non-scorable record — and both are true at once.

`derivation_confidence` from the Signal is **not** reused as claim confidence.
They are different quantities about different acts, and no code multiplies,
copies or defaults one from the other.

## 9. What it cannot do

- **No demand claim from a World Bank population series.** A population change
  is context: it says how many people exist, not what any of them want or would
  pay for.
- **No demand or interest claim from a GDELT frequency.** Not weakly, not with a
  low relevance. News coverage is journalists publishing; the quantity is about
  a different subject, and a low score would model it as *a little bit of the
  right thing* when it is none of it.
- **No cross-source alignment.** H-29.
- **No named language.** H-30.
- **No Opportunity, no embedding, no score.** Enforced by `validate_claims.py`,
  which fails the build on a write to any later-stage table.

## 10. The eight real Claims

Seven were produced from the seven real Signals, one each, with the existing 12 RawRecords,
12 NormalizedRecords, 7 Signals and 14 signal-input rows **byte-for-byte
unchanged** (a content digest before and after).

```
World Bank Open Data reported that "SP.POP.TOTL" for "Germany" increased
    between "2018" and "2019" by 187180.
World Bank Open Data reported that "SP.POP.TOTL" for "Germany" increased
    between "2019" and "2020" by 67909.
World Bank Open Data reported that "SP.POP.TOTL" for "France" increased
    between "2018" and "2019" by 223713.
World Bank Open Data reported that "SP.POP.TOTL" for "France" increased
    between "2019" and "2020" by 219049.
The GDELT Project reported that, in its "web-ngrams/1gram" stream under source
    language label "ENGLISH", the term "climate" appeared 11 more times in
    source bucket "20260830190000" than in the preceding source bucket
    "20260830184500".
The GDELT Project reported that, in its "web-ngrams/1gram" stream under source
    language label "ENGLISH", the term "weather" appeared 9 more times in source
    bucket "20260830190000" than in the preceding source bucket
    "20260830184500".
The GDELT Project reported that, in its "web-ngrams/1gram" stream under source
    language label "ENGLISH", within source bucket "20260830091500", the term
    "climate" appeared 19 more times than the term "weather".
```

An eighth was added in Mission 1.15.11, from the one real TED Signal:

```
Tenders Electronic Daily (EU public procurement) reported that, in its
    "notices/eforms-contract-and-award" resource, within a bounded set of 3
    "CONTRACT_AWARD_NOTICE" notices classified under "CPV" division "90", the
    largest "TOTAL_VALUE" amount at "NOTICE" scope stated in "EUR" exceeded the
    smallest by 686545.02.
```

**These establish no pain, no desire, no willingness to pay, no pricing power,
no competition gap, no distribution feasibility, no retention and no revenue
potential.** They are factual, source-level claims about two publications. The
first Claims existing does not make Opportunity discovery ready; what it makes
ready is the layer above having something honest to read.
