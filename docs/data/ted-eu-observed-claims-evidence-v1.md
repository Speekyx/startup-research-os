# TED-EU OBSERVED Claims and Evidence V1

**Authoritative.** Mission 1.15.11. The first interpretation of a procurement
Signal: what the Claim asserts, the ceiling it may not pass, and the Evidence it
produces.

**One real Claim, one revision, one Evidence row.** Produced by
`observed-signal-restatement@1.1.0` from the single real
`procurement_value_contrast` Signal, through the production interpretation path.

**H-36A NOT ESTABLISHED. H-36B NOT ADDRESSED. H-37 OPEN. H-38 OPEN.** None of
them is touched, and the Claim is built so that none of them has to close.

---

## 1. The proposition, in full

```text
Tenders Electronic Daily (EU public procurement) reported that, in its
"notices/eforms-contract-and-award" resource, within a bounded set of 3
"CONTRACT_AWARD_NOTICE" notices classified under "CPV" division "90", the
largest "TOTAL_VALUE" amount at "NOTICE" scope stated in "EUR" exceeded the
smallest by 686545.02.
```

| | |
|---|---|
| Claim type | `OBSERVED` |
| Temporality | `EVERGREEN` |
| Origin | `DETERMINISTIC_EXTRACTION` |
| Lifecycle | `ACTIVE` |
| Interpreter | `observed-signal-restatement@1.1.0`, `DETERMINISTIC` |
| `model_version` / `prompt_version` | **NULL**, and the database refuses a `DETERMINISTIC` interpretation carrying either |
| `opportunity_id` | **NULL** |
| `interpretation_confidence` | `1.0` |
| Revision | 1 |

## 2. The semantic ceiling

The Signal establishes one thing, and the Claim restates exactly that thing:

> Among the qualifying TED contract award notices in this bounded cohort, three
> division-90 notices reporting `TOTAL_VALUE` at `NOTICE` scope in EUR have a
> maximum-minus-minimum spread of 686545.02 EUR.

**Everything the sentence contains is a dimension the extractor grouped by.**
Nothing in it was added by the interpretation, and nothing the Signal carries
was dropped except the individual amounts, which §7 places in provenance.

## 3. What it does not claim, and why the wording is the enforcement

The Claim does **not** state or imply any of the following. Each was named in
the mission brief and each is asserted absent by
`TestWhatItRefusesToSay`:

- strong or growing market demand; a large, attractive or profitable market;
- that customers are willing to pay 686545.02 EUR, or that a SaaS could charge
  it;
- that 686545.02 EUR is a price, an average, a median, a contract value, a
  budget or revenue;
- that the market is growing, that demand is increasing, or any trend at all;
- that CPV division 90 is a good SaaS market, or that buyers would pay
  comparable amounts for a different product.

**The one shortening that would break it.** *"Division 90 contracts vary by
686545.02 EUR"* is a claim about every division-90 contract, and the three
words that stop it are **"within a bounded set of 3"**. The sentence also names
the notice class, the amount type, the amount scope, the currency and the
classification scheme, because a restatement that drops a cohort dimension has
widened its subject without saying so.

**The template is the protection; the guard is the backstop.** No template
contains a word from `INTERPRETIVE_VOCABULARY`, and `build_claim` refuses any
`OBSERVED` statement that does, so an edit reintroducing one never reaches the
database.

## 4. Attribution, and why it is not decoration

The statement begins with the source's canonical registry name and the words
*reported that*. It is a claim about a **publication**:

| Asserted | Not asserted |
|---|---|
| *TED reported that … the largest exceeded the smallest by 686545.02* | *Division 90 contracts differ by 686545.02* |

The first is false if TED did not publish those notices, and stays true if TED
published a wrong figure. The second is a claim about European procurement and
is not `OBSERVED` from a TED record (`claim-epistemic-semantics-v1.md` §3).

The display name comes from `registry.sources.canonical_name`, not from a map in
the interpreter.

## 5. The interpretation support question, answered explicitly

Two different questions, and the mission brief was right to separate them:

- **Derivation threshold — was support sufficient to build the Signal?** Yes.
  The contrast rule requires at least two distinct observations and this cohort
  has three.
- **Interpretation threshold — is support sufficient for this restatement?**
  **Yes, and no additional threshold applies.**

The reason is not leniency. This Claim adds **no inference** beyond the Signal:
every fact in it is a property of the Signal, and the interpretation step is a
format string over structured facts. A threshold would be answering *is three
enough to believe something about the market* — a question this Claim does not
ask.

`claim-evidence-interpretation-contract-v1.md` §11 already forbids inventing
one: *"No universal thresholds: '3 Signals required' is an arbitrary number
wearing the costume of a rule."* No threshold was lowered for TED, because none
exists to lower. What support is for lives one layer down, in Evidence
aggregation, where three rows from one publisher are **one** group.

## 6. Nothing temporal, and H-37 stays open

| | |
|---|---|
| Signal `temporal_basis` | `NONE` |
| Contributing `observed_at` | NULL on all three |
| Claim temporal semantics | **none** |

The template accepts basis `NONE` **and nothing else**. A
`procurement_value_contrast` Signal arriving on any other basis is refused with
`INCOMPATIBLE_TEMPORAL_SEMANTICS` rather than phrased with wording chosen for a
different basis.

**The acquisition window is not a temporal fact about the proposition.** The
collector bounded `publication-date` to one day in order to bound *retrieval*;
the notices' own published date carries an offset whose meaning is exactly what
H-37 leaves unestablished. The label reaches the Signal's window and the
contributing records, and reaches the Claim nowhere:
`test_the_period_label_reaches_the_signal_and_not_the_claim` asserts both halves.

No "during March 2023", no "over three days", no "recently", no "increased", no
"trend". `EVERGREEN` is correct precisely because the claim is about a fixed set
of publications: it is as true in 2030 as today.

## 7. Monetary semantics, and where the member values live

| Preserved verbatim | |
|---|---|
| Amount type | `TOTAL_VALUE` |
| Amount scope | `NOTICE` |
| Currency | `EUR` |
| Magnitude kind | `ABSOLUTE_DIFFERENCE` |
| Magnitude | `686545.02`, exact |

The wording is **"the largest … exceeded the smallest by"**, which is what
max-minus-min means in a sentence. It is never called a price, an average, a
median, a contract value or a willingness to pay, because none of those is what
was computed.

**The three member amounts — 73415.22, 440000, 759960.24 — are not copied into
the Claim.** They are reachable through the existing graph:

```text
Claim -> Evidence.signal_id -> nlp.signal_inputs (role CONTRIBUTED)
      -> acquisition.normalized_records.payload.amounts
```

All three remain reachable, verified against the real rows. Copying them into
`proposition_facts` would put one fact in two places, and the one that is not
the source of truth eventually disagrees.

**What IS in the Claim is the cohort membership** — `notice_ids`, all three,
sorted. That is not convenience: it is identity (§8), and a support of three
whose proposition named one notice would read as if two observations had been
found and lost.

## 8. Claim identity

`proposition_key` = sha256 over the canonical JSON of `proposition_facts`:

```json
{"proposition":"source_reported_procurement_value_contrast",
 "source_id":"ted-eu","resource_id":"notices/eforms-contract-and-award",
 "notice_class":"CONTRACT_AWARD_NOTICE","amount_type":"TOTAL_VALUE",
 "amount_scope":"NOTICE","currency":"EUR","classification_scheme":"CPV",
 "classification_division":"90",
 "classification_codes":["90715200","90911200","90911300","90919300"],
 "notice_ids":["125972-2023","126676-2023","127668-2023"],
 "relation":"DIFFERS"}
```

Two consequences, and they pull in opposite directions on purpose:

- **A revised amount is the same proposition.** TED correcting 759960.24
  appends **revision 2** to this claim; revision 1 is never modified, because an
  aggregation that read it must still be able to. The magnitude is wording, as
  it is for every template (§6.1 of the interpreter contract).
- **A fourth qualifying notice is a DIFFERENT proposition.** The cohort is the
  subject, so its membership is its identity. This is where the procurement
  template differs from the lexical ones: there the periods are fixed by the
  query, here the members **are** the claim.

`relation` is `DIFFERS | EQUAL`, recovered from whether the magnitude is above
zero. Direction is `NOT_APPLICABLE` by construction, so without it a cohort
whose amounts are all identical would be indistinguishable from one whose
amounts differ.

**Not built from:** the prose, an embedding (D-12 open), the Signal id, the
research session, the correlation id or a clock.

## 9. Provenance

- The Claim cites the **exact Signal revision** it interprets, through its
  Evidence row's `signal_id`.
- `research.claim_interpretation_inputs` records the Signal the run considered
  with role `CITED`.
- All **three** contributing observations stay reachable, and the support
  cardinality is visible in the statement, in `notice_ids` and in the Signal's
  inputs. It is not reduced to one anywhere.

## 10. The Evidence row

| Field | Value | Why |
|---|---|---|
| `direction` | `SUPPORTS` | The Claim is this Signal said back; it cannot bear against itself |
| `source_id` | `ted-eu` | **One** source, whatever the support count |
| `relevance` | `1.0` | Same subject by construction |
| `directness` | `1.0` | Bears on the Claim itself, not on something adjacent |
| `extraction_confidence` | `1.0` | The interpreter read the Signal correctly |
| `reliability` | **NULL** | No reviewed assessment applies. D-03 |
| `observation_category` | `UNCATEGORISED` | §11 |
| `independence_state` | `UNKNOWN` | §12 |
| `independence_group_id` | NULL | Required absent for anything but `KNOWN_DEPENDENT` |
| `evidence_level` | `1` | Where the ladder's own gates leave this row |
| `observed_at` | **NULL** | H-37 |

## 11. `observation_category` — the closest call in this mission

**It is `UNCATEGORISED`, and the alternative deserves stating because it is
genuinely arguable.**

A `CONTRACT_AWARD_NOTICE` records a purchase that actually happened, and the
`MARKET_ACTIVITY` definition's own first example is *purchases*. TED was pursued
across nine missions precisely because it is the first source in the portfolio
that could evidence a **transaction** rather than a listed price. On that
reading, `MARKET_ACTIVITY` is the honest value and `UNCATEGORISED` under-records
what is known.

**What decided it against:** this Evidence row does not carry a purchase. It
carries a **maximum minus a minimum over a set of published notices**, and a
spread is a property of records rather than economic activity. The category says
what kind of thing was observed *for this Claim*, and what was observed for this
Claim is a contrast.

**The consequence is real and is why it is written down here.**
`MARKET_ACTIVITY` is the **only** gate to `EvidenceLevel` 4, "Market Evidence",
and the gate is reached independently of every count above it. Setting it here
would pre-authorise Market Evidence for a spread between three cleaning
contracts, and it would do so silently — the level would appear the moment a
later mission supplied a reliability and an independence state.

**What is left open, deliberately:** the individual notices underneath may well
support `MARKET_ACTIVITY` for a claim about a **purchase**. No such claim exists,
no template produces one, and creating one is a proposition nobody has specified.
A mission that wants Level 4 from TED should write that claim rather than
recategorise this one.

## 12. Independence — three notices are one source

The Signal has support **3** and the Evidence is **one row** naming **one**
`source_id`. Three TED notices are three records from one publisher, sharing a
publication process and a selection process; counting them as three independent
sources would triple the apparent support for something observed once.

`independence_state` is `UNKNOWN`, not `KNOWN_DEPENDENT`: declaring them
dependent is a judgement this layer cannot make either. Aggregation groups by
origin, and unknown provenance forms **one** group per claim and direction.

**Record what you know, promote nothing.**

## 13. Scorability

**The row is `NON_SCORABLE` with `MISSING_RELIABILITY`, exactly like the other
seven.**

No reliability was invented. In particular it was not inferred from any of:

- that TED is an official EU publication;
- that the support count is 3;
- that `derivation_confidence` is `1.0`;
- that the source's policy verdict is approving under this profile.

`derivation_confidence = 1.0` says the **arithmetic** is mechanically
established under the extractor contract. It is not a probability that the
proposition is true, not source reliability, not evidence strength and not a
business confidence. Nothing multiplies, copies or defaults one from the other,
and `test_derivation_confidence_does_not_become_reliability` asserts it.

**The Evidence may remain non-scorable, and that is the design working.** A
system that stays capable of producing no score is what makes a score mean
something when one appears.

## 14. The interpreter decision

**Outcome B of the mission brief §15: the existing generic interpreter was
extended and versioned, `1.0.0` → `1.1.0`.**

- **Not a new interpreter.** The proposition is a Signal restated with its
  source named, which is what `observed-signal-restatement` is. A TED-specific
  interpreter would have been source-specific, and a template is specific to a
  **Signal type**, not to a publisher — as all three existing ones are.
- **Not an unversioned extension.** The interpreter can now make a proposition
  it could not make before. That is a version-worthy fact even though nothing
  existing moved.
- **Minor, because the addition is purely additive.** The three existing
  templates render byte-identical statements, fact sets and evidence.
  `TestTheExistingThreeTemplatesDidNotMove` pins the numeric statement, the
  numeric proposition key and the lexical statement, so "additive" is checked
  rather than asserted.

The seven existing Claims keep `interpreter_version = 1.0.0`, which is the
version that created them, and none gained a revision.

## 15. The real execution

Run through `run_claim_interpretation_job` — the same function the Celery task
calls — scoped by `signal_type_ids = ["procurement_value_contrast"]`, so the
seven existing claims were not read.

```text
first run    claims new 1   revised 0   unchanged 0   revisions 1   evidence 1
second run   claims new 0   revised 0   unchanged 1   revisions 0   evidence 0
```

**Idempotent.** A redelivery finds the statement unchanged and writes nothing.

| | Before | After |
|---|---|---|
| RawRecords | 23 | 23 |
| NormalizedRecords | 23 | 23 |
| Signals | 8 | 8 |
| Claims | 7 | **8** |
| ClaimRevisions | 7 | **8** |
| Evidence | 7 | **8** |
| Opportunities | 0 | 0 |
| ReliabilityAssessments | 0 | 0 |
| Embeddings | 0 | 0 |

No row was inserted by hand. No LLM was called; no module in the interpretation
layer can reach one, asserted over the AST by `validate_claims.py`.

## 16. What does not exist

No Opportunity — `opportunity_id` is NULL and a Claim may precede one (ADR-024),
so no placeholder was created to attach this Claim to. No ReliabilityAssessment,
no embedding, no score, no `EvidenceScore`, no research completeness, no revenue
or MRR estimate.

**This Claim establishes no pain, no desire, no willingness to pay, no pricing
power, no competition gap, no distribution feasibility, no retention and no
revenue potential.** It is a factual, source-level claim about one publication's
report of three contract awards.
