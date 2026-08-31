# Signal → Evidence Semantics V1

**Authoritative.** Mission 1.13. Companion to
`claim-evidence-interpretation-contract-v1.md`.

How one Signal becomes Evidence **for a particular Claim** — and the several
things it never becomes.

---

## 1. The one sentence

> **Evidence is claim-relative. A Signal has never heard of the Claim.**

Every design decision below follows from it. A Signal is a completed derivation
over its own inputs; it exists before any claim does, and it is unchanged by
every claim that later cites it. What varies from claim to claim — whether it
supports or contradicts, how relevant it is, how directly it bears — is therefore
a property of the *pairing*, and lives on the Evidence row.

This is not a modelling preference. Put `relevance` on the Signal and the second
claim to cite it either overwrites the first claim's judgement or silently
inherits it.

## 2. The three things a Signal is not

| A Signal is not | Because |
|-----------------|---------|
| **Evidence** | Evidence is scoped to a claim and adds direction, relevance, directness, reliability and an independence state. A Signal has no claim to be relative to (`signal-contract-v1.md`) |
| **A Claim** | A Signal relates its own inputs; a Claim asserts a proposition about the world (`claim-evidence-interpretation-contract-v1.md` §3) |
| **A score** | `derivation_confidence` is about the arithmetic. It is not an `EvidenceScore`, not an evidence strength, and it is multiplied by nothing |

## 3. What one Evidence row means

A row in `scoring.evidence` asserts exactly:

> Signal *S* bears on Claim *C* in direction *D*, as judged by the interpreter
> that wrote this row.

`claim_id` is `NOT NULL` since migration 0016. `signal_id` remains nullable
because the table also holds human-entered and imported evidence that never came
from a derivation — but **a generated Evidence row must cite a Signal**, refused
in the model with `SIGNAL_NOT_CITED`.

## 4. Direction

`SUPPORTS | CONTRADICTS | NEUTRAL`.

**A generated row may not be `NEUTRAL`** (`UNSUPPORTED_INTERPRETATION`). A Signal
that bears on nothing produces **no row**: attaching it inflates the record
without changing what is supported, and an aggregator counting rows would read
the inflation as breadth.

The value survives in the enum because a human may legitimately record a null
result — "we looked, and it does not move either way" is a finding a person can
own. The restriction is therefore in the contract and in `build_claim`, not in
the schema. A CHECK would refuse the human case too.

One Signal may `SUPPORTS` claim A and `CONTRADICTS` claim B. That is the normal
case, not an anomaly.

## 5. The four factors

Each is `[0,1]`, each is **nullable**, and none is a score.

| Factor | Question |
|--------|----------|
| `relevance` | How much does what this Signal is about overlap what the Claim is about? |
| `directness` | Does it bear on the Claim itself, or on something adjacent? |
| `reliability` | How much can this kind of observation be trusted for this purpose? |
| `extraction_confidence` | How confident is the interpreter that it read the Signal correctly? |

**An absent factor is `NON_SCORABLE` at aggregation time — never `0.5`, and never
`0.0`** (`../domain/evidence-aggregation-framework-v1.md` §6). `0.5` is a
measurement claiming the middle; `0.0` is a measurement claiming the worst. Both
are inventions, and `q_i = min(components)` makes the second catastrophic. Absent
means the question was not answered.

Out of range is **rejected, never clamped**. Clamping turns a bug in an
interpreter into a plausible number.

### 5.1 Why `reliability` is not a per-source constant

The temptation is a lookup table: GDELT 0.6, World Bank 0.9. That table is a
per-source reliability coefficient, which is **D-03**, which is blocked. Source
policy status is also not epistemic reliability — an `APPROVED` source does not
produce better evidence; approval is about permission.

Reliability is per-pairing: a World Bank population figure is highly reliable
evidence about German population and nearly worthless evidence about German
software spending, from the same source with the same approval.

## 6. Independence travels; the judgement does not happen here

`independence_state` is `KNOWN_INDEPENDENT | KNOWN_DEPENDENT | UNKNOWN`, and
`UNKNOWN` is the default. `KNOWN_DEPENDENT` requires an `independence_group_id`;
`KNOWN_INDEPENDENT` must not carry one. Both enforced in `EvidenceDraft`.

Two Signals from one publication stream are **not** automatically independent.
Two `lexical_frequency_change` Signals over adjacent buckets of
`web-ngrams/1gram` share a corpus, a crawl and a selection process; counting them
as two independent observations doubles the apparent support for something
observed once.

Equally, they are not automatically dependent — that would be a judgement this
layer cannot make either. So `source_id` is carried on every Evidence row, and
aggregation groups by origin, where **records sharing an origin form one group
and the strongest member counts**, and unknown provenance forms **one** group per
claim and direction rather than being promoted to independent.

The rule this layer follows is: **record what you know, promote nothing.**

## 7. `observation_category`

`STATED_OPINION | REPORTED_BEHAVIOUR | OBSERVED_BEHAVIOUR | MARKET_ACTIVITY |
DIRECT_VALIDATION | UNCATEGORISED`

It says what *kind of thing was observed*, which is what lets an aggregator
notice that ten opinions are not one behaviour.

The two real source families and what they are **not**:

- A World Bank series is `MARKET_ACTIVITY` at most, and often less. A population
  count is not market activity; it is context.
- A GDELT WEB-NGRAM frequency is **not** `REPORTED_BEHAVIOUR` and not
  `OBSERVED_BEHAVIOUR`. Nobody's behaviour was observed. It is a property of a
  news corpus — journalists writing, not users acting. `UNCATEGORISED` is the
  honest value until a category for *publication activity* exists, and inventing
  one here would be a taxonomy change made in passing.

`DIRECT_VALIDATION` is unreachable from any current Signal. It means someone
tried the thing.

## 8. What GDELT lexical frequency may and may not support

Mission 1.13 §46, stated as a rule because it is the failure most likely to ship.

A `lexical_frequency_change` Signal may be Evidence for:

> "Within GDELT's WEB-NGRAM stream, under language label *L*, term *T* appeared
> more often in the later of two adjacent buckets."

It may **not**, alone, be Evidence for a demand claim — not weakly, not with a
low `relevance`, not with a caveat in the rationale.

The reason is not that the evidence is thin. It is that the quantity is about a
**different subject**: news coverage is journalists publishing, and demand is
people wanting and paying. A low relevance score would model it as *a little bit
of the right thing*, and it is none of the right thing. A system that admits it
weakly ranks press cycles, and does so with a number attached that looks
considered.

What would change this is a Signal relating the lexical stream to something
people did — a search volume series, a marketplace listing count, a survey.
Nothing in the system produces one, and the correct behaviour meanwhile is
refusal with `UNSUPPORTED_INTERPRETATION`.

**Since Mission 1.13.1 this is what the only interpreter does.** The two real
`lexical_frequency_change` Signals produced claims saying a term appeared more
often in one source bucket than in the preceding one, attributed to GDELT, and
nothing further. The protection is the template, not the guard: no template
contains the word `demand`.

## 9. What the certifications forbid at this layer

The refusal reasons are raised when constructing the Claim, but the constraint is
about the *pairing*, so it belongs here too.

**H-29.** A Signal certified for `SOURCE_RELATIVE_ORDER` only may not be Evidence
for a Claim needing an instant. Concretely: a GDELT bucket-change Signal cannot
be Evidence for "coverage rose during the week the World Bank figure was
published", because that claim requires both to sit on one timeline and one of
them does not. `INCOMPATIBLE_TEMPORAL_SEMANTICS`.

**H-30.** A Signal derived under a GDELT language label may not be Evidence for a
Claim about a named language. `INCOMPATIBLE_LANGUAGE_SEMANTICS`.

Both fail closed. Neither is closed by this mission.

## 10. What is deliberately not recorded

~~**Which Signals were considered and rejected** (GAP-5).~~ **Recorded since
Mission 1.13.1.** An interpreter that examined forty Signals and cited three has
made a selection, and the selection is information — an aggregator cannot
distinguish "three supporting Signals exist" from "three of forty were
supporting".

`research.claim_interpretation_inputs` holds one row per considered Signal with
its role (`CITED` / `EXCLUDED` / `REFUSED`) and a reason code, hanging off the
RUN rather than the Claim because a Signal considered and not cited has no Claim
to hang off (migration 0018, ADR-025).

**Whether an aggregator should read it is still open.** This layer makes the
fact available; how a selection ratio would enter a score is D-03's question,
and D-03 is blocked.

## 11. Where this is enforced

| Rule | Enforced in |
|------|-------------|
| Evidence names a Claim | migration 0016, `claim_id NOT NULL` |
| Generated evidence names a Signal | `EvidenceDraft`, `SIGNAL_NOT_CITED` |
| No generated `NEUTRAL` | `build_claim` |
| Factors in `[0,1]`, rejected not clamped | `EvidenceDraft` |
| Absent factor stays absent | `EvidenceDraft.to_json` omits it |
| `KNOWN_DEPENDENT` names a group | `EvidenceDraft` |
| `KNOWN_INDEPENDENT` names none | `EvidenceDraft` |
| No score on an Evidence row | the absence of a column, asserted by test |
| `claim_type` no longer duplicated | migration 0016 dropped it; `validate_schema.py` updated |
| Considered-but-not-cited Signals are recorded | migration 0018, `persist_considered` |
| A generated row's factors are the interpreter's decisions, each with a reason | `deterministic-observed-claim-interpreter-v1.md` §7 |
