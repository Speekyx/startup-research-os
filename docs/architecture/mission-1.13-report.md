# Mission 1.13 — Signal → Claim → Evidence Interpretation Contract V1

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.3` · **Scope:** contract and
model only.

**Nothing was interpreted.** Claims 0, Evidence 0, Opportunities 0. RawRecords
12, NormalizedRecords 12, Signals 7 — unchanged. No LLM call, no embedding, no
score, no network.

---

## 0. What the mission found

The schema said `research.claims.opportunity_id NOT NULL`. The pipeline runs
Signal → Claim → Opportunity. **The intended pipeline was unrepresentable**: a
claim about a source fact cannot be written until somebody has already invented
the product it might justify.

That single finding reordered the mission. The gap analysis was written first
(§41), the ontology was amended rather than worked around (§43), and the contract
was written to the pipeline rather than to the historical schema (§45).

## 1. The deliverables

| Artifact | What it is |
|----------|-----------|
| `docs/data/claim-evidence-interpretation-gap-analysis-v1.md` | Ten gaps, written **before** the migration |
| `docs/domain/opportunity-ontology-v2.2.md` | Inherits V2.1 in full; amends §17.3 only |
| `docs/architecture/adr/ADR-024-claim-precedes-opportunity.md` | Three decisions |
| `docs/data/claim-evidence-interpretation-contract-v1.md` | The boundary |
| `docs/data/claim-epistemic-semantics-v1.md` | The five types, and how to choose |
| `docs/data/signal-to-evidence-semantics-v1.md` | Signal → Evidence, claim-relative |
| `infrastructure/db/migrations/0016_claim_interpretation_alignment.sql` | The alignment |
| `infrastructure/db/migrations/0017_interpreter_identity_null_safety.sql` | A defect in 0016, fixed forward |
| `packages/claim-model/python/` | The unpersisted draft and its refusals; 42 tests |
| Contract `1.8.0` → `1.9.0` | `ClaimInterpretationKind`, `ClaimEvidenceRefusalReason` |

---

# The questions (§56)

## What exactly is a Claim?

**A persisted assertion of a proposition about the world**, carrying an epistemic
type, a temporality, an origin, an interpreter identity, and a stable identity
over the proposition rather than over its wording. It is the first artifact in
the pipeline that can be wrong in a way arithmetic cannot catch.

It is not a `ClaimType` (that is a category it carries), not an Opportunity, and
not a Signal renamed.

## What exactly is Evidence?

**One row asserting that Signal *S* bears on Claim *C* in direction *D*, as
judged by the interpreter that wrote the row.** It carries the factors an
aggregation reads — relevance, directness, reliability, extraction confidence,
observation category, independence state — and no score.

## Why is a Signal not automatically Evidence?

Because **evidence is claim-relative and a Signal has never heard of the Claim**.
Direction, relevance and directness are properties of the *pairing*: one Signal
may support Claim A strongly and contradict Claim B weakly, unchanged by either.
Put those fields on the Signal and the second claim to cite it either overwrites
the first claim's judgement or silently inherits it.

## Why is a Signal not automatically a Claim?

Because a Signal states a relation **between its own inputs**, and a Claim states
a proposition **about the world** — one that observations outside the derivation
could support or contradict. "SP.POP.TOTL for DE was 82,905,782 in 2018 and
83,092,962 in 2019" is not falsifiable by anything the derivation never saw; it
*is* the records.

## Can one Signal create an OBSERVED Claim?

**Yes.** A faithful, attributed restatement of what the Signal's source reported
is exactly what `OBSERVED` is for, and the Signal is its evidence. The Signal
already satisfies the contrast rule internally (two or more distinct
observations), so an `OBSERVED` claim over one Signal is not a single-observation
assertion.

## Can one Signal create an INFERRED market Claim?

**Not from any of the seven that exist.** `INFERRED` is permitted structurally —
it needs a stated reasoning step, a confidence, and cited Signals. What is
refused is the specific inference from a *measurement of publication or
population* to a *proposition about market demand*, because the reasoning step
would have no premise. See "Can current GDELT Signals support demand Claims?".

## What separates OBSERVED from INFERRED?

**Attribution, and the falsifier that follows from it.**

- `OBSERVED` asserts what a source *reported*. It is false if the source did not
  say that, and stays true if the source was wrong.
- `INFERRED` asserts something about the world the source did not itself report,
  reached by a stated reasoning step whose assumption is written down.

"World Bank reported that Germany's population rose in 2019" is `OBSERVED`.
"Germany's population rose in 2019" is `INFERRED` — the record is evidence for
it, not identical to it.

Enforced: an `OBSERVED` claim using market or user vocabulary is refused with
`UNSUPPORTED_INTERPRETATION`.

## When is HYPOTHESIS used?

For **a proposition worth testing that is not yet supported**, and that says so
on its face. It is the only type exempt from the evidence requirement, and it is
exempt **by definition rather than by exception**: a hypothesis that required
evidence would not be a hypothesis, and an unusable `HYPOTHESIS` would push
unsupported ideas into `INFERRED` — which is precisely the failure the evidence
rule exists to prevent. The exemption is what makes the rule enforceable.

## What qualifies as PREDICTED?

A proposition about **a period nobody has measured**. Structurally an inference,
separated because its falsifier does not exist yet and its failure mode is
different. **Nothing in the system produces one** — there is no forecaster and
all seven Signals are retrospective. Documented so a future extrapolation is not
filed as `INFERRED`.

## What qualifies as RECOMMENDED?

A statement of **what someone should do** — normative, not factual, supported by
a chain of other claims plus a goal the system was given. Nothing produces one,
and nothing should until Opportunities exist: a recommendation with no
addressable thing to recommend about is advice with no object.

## Does every persisted Claim require Evidence?

**Every claim a machine asserts does, except a HYPOTHESIS.** Three exemptions,
each reasoned rather than convenient:

| Exempt | Why |
|--------|-----|
| `claim_type = HYPOTHESIS` | By definition (above) |
| `origin = MANUAL` | A person asserting and then looking for evidence is the ordinary research motion. The rule is about what a **machine** stores |
| `lifecycle = WITHDRAWN` | A withdrawn claim's evidence may have been removed; requiring it would make withdrawal impossible |

Enforced twice: a `DEFERRABLE INITIALLY DEFERRED` constraint trigger
(`research.require_evidence_for_generated_claim`, migration 0016) and
`NO_SUPPORTING_SIGNAL` in `build_claim`. Deferred because a claim and its
evidence are written in one transaction and neither exists first — the precedent
is migration 0007.

## Can a HYPOTHESIS exist without supporting Evidence?

**Yes**, including one a machine generated. What it may not do is silently become
`INFERRED` when evidence arrives: that is a new claim of a different type, and
the shared `proposition_key` makes the relationship visible rather than implicit.

## How does Evidence link Signal and Claim?

`scoring.evidence` carries `claim_id` (now `NOT NULL`, GAP-6) and `signal_id`.
`signal_id` stays nullable because the table also holds human and imported
evidence that never came from a derivation — but a **generated** row must cite a
Signal, refused with `SIGNAL_NOT_CITED`.

`claim_type` was **dropped** from the table (GAP-7). It was a second answer to a
question `research.claims.claim_type` already answers, and two answers eventually
disagree.

## What does Evidence direction mean?

`SUPPORTS | CONTRADICTS | NEUTRAL` — whether this Signal makes this Claim more or
less credible.

**A generated row may not be `NEUTRAL`.** A Signal bearing on nothing produces
**no row**: attaching it inflates the record without changing what is supported,
and an aggregator counting rows reads the inflation as breadth. The value stays
in the enum because a human may legitimately record a null result, so the
restriction is in the contract and not in a CHECK.

## What does Evidence relevance mean?

How much what the Signal is *about* overlaps what the Claim is *about*. `[0,1]`,
nullable.

## What does directness mean?

Whether the Signal bears on the Claim **itself** or on something adjacent to it.
A population count bears directly on a population claim and indirectly, at best,
on a claim about software spending.

## What does reliability mean?

How much this kind of observation can be trusted **for this purpose**. It is
per-pairing, not per-source: a World Bank population figure is highly reliable
evidence about German population and nearly worthless evidence about German
software spending, from the same source with the same approval.

A per-source constant would be a reliability coefficient, which is **D-03**,
which is blocked. Source policy status is also not epistemic reliability — an
`APPROVED` source does not produce better evidence.

## What does extraction confidence mean?

How confident the interpreter is that it **read the Signal correctly** — a
statement about the extraction step, not about the world.

All four factors are nullable. **An absent factor is `NON_SCORABLE` at
aggregation time, never `0.5` and never `0.0`**: `0.5` is a measurement claiming
the middle, `0.0` is a measurement claiming the worst, and `q_i =
min(components)` makes the second catastrophic. Out of range is **rejected, never
clamped**.

## How are contradictory Evidence items handled?

They are stored as themselves and aggregated **separately** — support and
contradiction are decomposed into four masses summing to 1, with no flat
contradiction penalty
(`../domain/evidence-aggregation-framework-v1.md`). Nothing at this layer
resolves a contradiction, silences one side, or nets them off. A Claim with
strong evidence both ways is a Claim with high conflict mass, which is
information rather than a problem to be averaged away.

## How is source independence preserved?

`independence_state` is `KNOWN_INDEPENDENT | KNOWN_DEPENDENT | UNKNOWN`, default
`UNKNOWN`. `KNOWN_DEPENDENT` requires a group id; `KNOWN_INDEPENDENT` must not
carry one. `source_id` travels on every row so aggregation can group by origin,
where records sharing an origin form one group and the strongest member counts,
and unknown provenance forms **one** group per claim and direction rather than
being promoted to independent.

The rule at this layer: **record what you know, promote nothing.**

## Are repeated Signals independent evidence?

**No, and not automatically dependent either.** Two `lexical_frequency_change`
Signals over adjacent buckets of `web-ngrams/1gram` share a corpus, a crawl and a
selection process; counting them as two independent observations doubles the
apparent support for something observed once. Declaring them dependent would also
be a judgement this layer cannot make. So the origin is recorded and the
judgement happens at aggregation.

## What is Claim confidence?

`interpretation_confidence`, on the **revision**, `[0,1]`:

> How confident the interpreter is that this statement is a correct reading of
> the Signals it cites.

It lives on the revision because confidence is a property of *an act of
interpretation*, and a re-interpretation with better evidence is a new revision.

## Is Claim confidence the same as EvidenceScore?

**No.** `EvidenceScore` is `0–100` and is aggregation's output over the Evidence
factors. `interpretation_confidence` is `[0,1]` and is about the reading. A
deterministic restatement can hold confidence `1.0` while the proposition it
restates is barely supported — the interpreter is certain about the reading and
the evidence is thin, and there is no contradiction between those.

## Is Signal derivation confidence reused as Claim confidence?

**No.** `derivation_confidence` is a statement about arithmetic — a deterministic
extractor's is `1.0`, which says the subtraction is right, not that the reading
is. They are different quantities about different acts, and no code multiplies,
copies or defaults one from the other.

## How are Claim revisions handled?

Append-only, in `research.claim_revisions`, with a monotonic `revision` per
claim. The previous revision is never modified, because an aggregation that
evaluated revision N must still be able to read revision N. The statement lives
**only** in the revision table, so the current text and the history cannot
disagree. The `proposition_key` does not move when the wording does.

## What interpreter provenance is required?

`interpreter_id`, `interpreter_version`, `interpretation_kind` — **all three or
none**. Half an identity is a version nobody can resolve. Plus `model_version`
and `prompt_version` where the kind is `MODEL_DERIVED`.

A short `rationale` and the `cited_facts` are persisted. **A private reasoning
transcript is not**, and there is nowhere to put one — no such field exists on
the draft, the claim or the revision, and a test asserts the absence.

## Can interpretation be deterministic?

**Yes, and it is the default.** `ClaimInterpretationKind.DETERMINISTIC` asserts
that the same inputs produce the same output, and it **forbids** `model_version`
and `prompt_version` — enforced by `claims_interpretation_provenance_check` and
by `ClaimInterpretation.__post_init__`. "Deterministic" is a promise that the
claim can be regenerated and compared; a model in the path silently voids it.

## Can interpretation use an LLM later?

**Yes.** `MODEL_DERIVED` exists, requires `model_version`, and is a first-class
kind rather than an escape hatch. Nothing in this mission calls one.

## Is the LLM considered market evidence?

**No.** A model is a reasoning mechanism. Its output cannot satisfy the evidence
requirement, and there is no route for it to become a row in `scoring.evidence`.
Its contribution is recorded as provenance about *how the reading was reached*.

## How are unsupported LLM claims prevented?

The evidence requirement applies **identically** to `MODEL_DERIVED` claims: one
citing no Signal is refused exactly as a deterministic one is, in the database
trigger and in `build_claim`. A model cannot cite itself, because the only thing
`scoring.evidence` accepts from a generated interpreter is a `signal_id`. And an
unsupported proposition has a legitimate home — `HYPOTHESIS` — which is why the
rule does not push anybody toward mislabelling.

## How does H-29 restrict Claim generation?

ADR-022 certified `SOURCE_RELATIVE_ORDER` for `web-ngrams/1gram` and
`web-ngrams/2gram`, and explicitly **not** `COMPARABLE_INSTANT`. Therefore:

- "the later bucket" is available;
- a clock time, a date, or a wall-clock alignment is not;
- aligning a GDELT bucket with a World Bank period is not, because alignment
  requires both to be instants and one is not.

Refusal reason: `INCOMPATIBLE_TEMPORAL_SEMANTICS`. **H-29 remains open.**

## How does H-30 restrict Claim generation?

A GDELT language label is its own identity, whatever it maps to. Comparing terms
**within one label** is available. Saying "in French", or comparing across labels
as one language space, is not. Refusal reason:
`INCOMPATIBLE_LANGUAGE_SEMANTICS`. **H-30 remains open.**

A `HYPOTHESIS` is exempt from the *evidence* requirement, never from these.

## Can current World Bank Signals support market-demand Claims?

**No.** The four `numeric_period_change` Signals are over `SP.POP.TOTL` —
population. A population change is context, not demand: it says how many people
exist, not what any of them want or would pay for. There is no reasoning step
from a demographic count to willingness to pay that does not smuggle in a premise
nothing here supplies.

They support claims about **the reported series**, and about German population as
an `INFERRED` claim with the estimate-tracks-reality assumption stated.

## Can current GDELT Signals support demand Claims?

**No — and not weakly, not with a low relevance score, and not with a caveat.**

The reason is not that the evidence is thin. It is that the quantity is about a
**different subject**: a WEB-NGRAM frequency measures journalists publishing, and
demand is people wanting and paying. A low relevance would model it as *a little
bit of the right thing*, and it is none of the right thing. A system that admits
it weakly ranks press cycles, with a number attached that looks considered.

## What CAN the current seven Signals truthfully support?

| Signals | Truthfully supports (`OBSERVED`) |
|---------|----------------------------------|
| 4 × `numeric_period_change` (World Bank) | "World Bank reported that SP.POP.TOTL for *geography* rose/fell between *period A* and *period B*" |
| 1 × `lexical_frequency_contrast` (GDELT) | "Within GDELT's WEB-NGRAM stream, under language label *L*, term *A* appeared more often than term *B* in one bucket" |
| 2 × `lexical_frequency_change` (GDELT) | "Within GDELT's WEB-NGRAM stream, under language label *L*, term *T* appeared more often in the later of two adjacent buckets" |

Each names its source, its stream, its label and its bucket relation. **None**
names a clock time, a language, a person, a market, or a want.

As `INFERRED`, with the assumption stated: a claim about German population
itself, and a claim about the volume of news coverage of a term. Nothing further.

## Which additional source families are needed?

From `source-portfolio-v1.md` §2 — none of these is a new idea, and each is
blocked for a recorded reason:

| Claim family | What is needed | State today |
|--------------|----------------|-------------|
| **Pain** | People describing problems in their own words | **Nothing usable.** `bluesky` promising (silent terms); `reddit`, `stack-exchange`, `hacker-news`, `discord`, `x-twitter` blocked |
| **Desire** | Wishlist, save, pre-order behaviour | **Nothing usable.** `pinterest` promising (terms unread); app stores, `product-hunt`, `steam` all `RESTRICTED` |
| **Willingness to pay** | Prices paid, conversion, purchase intent | **Nothing.** No approved source carries a transaction or a price. This is the largest single gap |
| **Competition** | Pricing, ratings, launch data | `gdelt` sees what is *written about* products, never the products. App stores and `product-hunt` blocked |
| **Distribution** | Channel reach and acquisition cost | **Nothing.** `wikimedia-pageviews` is attention, not acquisition |
| **Retention** | Repeat use over time | **Nothing.** No approved source observes the same user twice |

The pattern is consistent: the portfolio is strong on *published aggregate
context* and empty on *individual behaviour*, and every demand-side family needs
the second. This is a governance outcome, not an engineering one — the blockers
are silent or restrictive terms, and no extractor closes them.

## Was a schema migration required?

**Yes — two.**

`0016_claim_interpretation_alignment.sql`:

- `claims.opportunity_id` → nullable (GAP-1)
- `claims` gains `interpreter_id`, `interpreter_version`, `interpretation_kind`,
  `proposition_key` (unique per workspace), with the provenance and completeness
  CHECKs
- `claim_revisions` gains `interpretation_confidence` `[0,1]` (GAP-2)
- `evidence.claim_id` → `NOT NULL` (GAP-6)
- `evidence.claim_type` → **dropped** (GAP-7)
- `research.require_evidence_for_generated_claim`, a deferred constraint trigger
  (GAP-3)
- three indexes, including `idx_claims_unattached`

`0017_interpreter_identity_null_safety.sql` — **a defect in 0016, fixed
forward.** The completeness CHECK was written as `(all NULL) OR (all non-blank)`,
which evaluates to **NULL** on a half-filled row (`length(btrim(NULL)) > 0` is
NULL), and **a CHECK accepts NULL**. Half an interpreter identity was written
without complaint. Replaced with `num_nonnulls(...) IN (0, 3)`, which cannot
itself be NULL. 0016 is not edited: a migration is never rewritten after it has
been applied.

Found by the probe, not by review — the probe asserts the **constraint name** it
expects, so a case that was accepted rather than rejected showed up as `ACCEPTED`
where a name was expected. Recorded as `testing-strategy.md` §28.

## Were any production Claims or Evidence rows created?

**No.** `research.claims` 0, `research.claim_revisions` 0, `scoring.evidence` 0,
`research.opportunities` 0, `nlp.embedding_provenance` 0.

The constraint probe wrote 4 claims and 2 evidence rows **inside a transaction
that rolled back**, and asserts 0 rows afterwards. All 9 probe cases behaved as
specified. `packages/claim-model` reaches no network, no model, no embedder and
no database; its 42 tests are over synthetic objects only.

## Did all existing 12 Raw, 12 Normalized and 7 Signals remain unchanged?

**Yes.**

| Table | Count |
|-------|-------|
| `acquisition.raw_records` | 12 |
| `acquisition.normalized_records` | 12 |
| `nlp.signals` | 7 (4 `numeric_period_change`, 2 `lexical_frequency_change`, 1 `lexical_frequency_contrast`) |
| `nlp.signal_inputs` | 14 |
| `nlp.signal_derivation_runs` | 6 |

Latest write times are unchanged from before this mission (raw `19:32:53`,
normalized `19:33:02`, signals `19:33:51` on 2026-08-30; migrations 0016 and 0017
applied at `20:01` and `20:02`). No migration in this mission touches those
tables. The pytest post-suite check reports the database unchanged across 22
tenant tables and 14 global tables.

## Is Mission 1.13.1 safe to implement deterministic OBSERVED Claim + Evidence generation?

**Yes, with four conditions.**

Safe because the boundary is now enforced rather than described: the evidence
requirement is a trigger, the interpreter identity is complete-or-absent, the
determinism promise forbids a model, the proposition identity exists, and the two
open questions fail closed as refusal reasons. A deterministic `OBSERVED`
interpreter over the seven Signals restates what a source reported and asserts
nothing further, which is the smallest possible first crossing.

The conditions:

1. **The interpreter writes claim + revision + evidence in one transaction.** The
   evidence requirement is a `DEFERRABLE INITIALLY DEFERRED` trigger firing at
   COMMIT, so evidence attached in a second transaction is too late by
   construction. `ClaimRepository.create` gained an `evidence=` parameter in this
   mission for exactly that.
2. **An interpretation run log is needed** (ADR-021's shape, for interpretation).
   It does not exist, because there was no writer. A refused interpretation must
   land somewhere, and `NO_SUPPORTING_SIGNAL` returned into a void is an
   observability gap of the kind Mission 1.11.1 §4 made a precondition.
3. **GAP-5 should be designed with it, not after.** What the interpreter
   *considered and did not cite* is information an aggregator needs — three of
   forty supporting is not three supporting — and it has no writer until 1.13.1
   has one.
4. **No `INFERRED` in 1.13.1.** `OBSERVED` restates; `INFERRED` reasons, and each
   reasoning step needs its own justification. Mixing them in the first
   interpreter is how the market-vocabulary guard becomes the only thing standing
   between a measurement and a conclusion.

---

## 2. What this mission deliberately did not do

- **No `ClaimCandidate` table** (§4). A second place an assertion can live is a
  place that escapes every rule in the contract.
- **No universal thresholds** (§46). "3 Signals required", "5 sources required"
  are arbitrary numbers wearing the costume of a rule. What a particular claim
  type requires belongs to the interpreter that produces it.
- **No embedding-based identity** (§17). D-12 stays open and nothing here depends
  on it.
- **No new epistemic vocabulary.** The five claim types are unchanged and a sixth
  was not added; what was missing was a rule for telling them apart, not a
  category.
- **GAP-5 deferred**, named rather than designed around.

## 3. Incidental corrections

Two stale statements were fixed because the migration made them false, not as
opportunistic edits:

- `claim-model-v1.md` §3 said "exactly one opportunity". Amended, with a note
  saying what changed and under whose authority.
- The gateway's `scoring.evidence` writer and reader still named `claim_type`,
  and two tests asserted only a substring of an error message — so both kept
  passing on an `UndefinedColumn` that never reached the constraint under test.
  Both now assert `diag.constraint_name` (`testing-strategy.md` §24).

One guard was widened: the interpretive-vocabulary list held `market for`, which
does not match Mission 1.13 §3's own example, *"the German SaaS market is
growing"*. The guard passed the sentence it exists to catch. Widened to the bare
word with the cost stated in the code (`testing-strategy.md` §29).

## 4. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | 459 tests, 7 packages, pass |
| Pytest suites | 7 packages, pass; database unchanged across 22 tenant and 14 global tables |
| `validate_schema` | pass — 9 invariant groups, 36 tables |
| `validate_source_registry` | pass — 27 sources, 33 evidence records |
| `validate_normalization` | pass — 9 boundary groups |
| `validate_signals` | pass — 6 boundary groups |
| `validate_compliance_capabilities` | pass — 12 conditions, 5 approving sources |
| `validate_evidence_aggregation` | pass — 8 checks; production scoring still blocked |
| Contracts `--check` | pass — TS, Python and JSON Schema all current at `1.9.0` |
| TS conformance | 21 tests, pass |
| Generated documents `--check` | 4 of 4 current |
| `ruff check` / `ruff format --check` | pass — 368 files |
| `mypy` | pass — 132 source files, `sros_claim_model` included |
| Claim constraint probe | 9 of 9 as specified; 0 rows after rollback |

## 5. Open questions after this mission

| Id | State |
|----|-------|
| **H-29** GDELT bucket timezone | **OPEN.** Now also a claim-level refusal reason |
| **H-30** CLD2 language mapping | **OPEN.** Now also a claim-level refusal reason |
| **D-03** scoring parameters | Framework-resolved, uncalibrated. Untouched |
| **D-08** which normalized row to read | Failed closed. Untouched |
| **D-12** embedding versioning | **OPEN**, and nothing in this mission depends on it |
| **GAP-5** considered-but-excluded Signals | Deferred to the mission that has an interpreter |
