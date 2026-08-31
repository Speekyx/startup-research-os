# Mission 1.13.1 — Deterministic OBSERVED Claim + Evidence Generation V1

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.13.1` · **Scope:** the
first complete Signal → Claim → Evidence pipeline.

```
RawRecords 12 → NormalizedRecords 12 → Signals 7 → OBSERVED Claims 7 → Evidence 7
```

**Seven real Claims exist.** No LLM, no embedding, no Opportunity, no score. The
12 RawRecords, 12 NormalizedRecords, 7 Signals and 14 signal-input rows are
byte-for-byte unchanged.

---

## 0. What was built

| Artifact | What it is |
|----------|-----------|
| `services/nlp/python/sros_nlp/interpreters/` | `observed-signal-restatement@1.0.0`: three templates, no fallback |
| `services/nlp/python/sros_nlp/claim_job.py` | The job, runnable without a broker |
| `services/nlp/python/sros_nlp/claim_repositories.py` | Reads Signals with lineage; writes claim + revision + evidence in one transaction |
| `services/workers/python/sros_workers/claim_tasks.py` | `claim.interpret`, on the acquisition queue |
| `infrastructure/db/migrations/0018_claim_interpretation_runs.sql` | `proposition_facts`, the run log, the considered set |
| `infrastructure/scripts/validate_claims.py` | Eleven boundary gates, probed against eleven deliberate violations |
| `docs/data/deterministic-observed-claim-interpreter-v1.md` | The interpreter |
| `docs/data/claim-interpretation-runtime-v1.md` | How it runs, persists and refuses |
| `docs/architecture/adr/ADR-025-…` | Why what a run considered is part of the record |
| Contract `1.9.0` → `1.10.0` | 3 refusal reasons, `ClaimInterpretationInputRole` |
| 53 + 29 + 8 new tests | Synthetic interpreter, live persistence, task surface |

---

# The questions (§49)

## Is deterministic OBSERVED Claim interpretation implemented?

**Yes.** Seven real Claims, seven revisions, seven Evidence rows, from the seven
real Signals.

## What interpreter/version?

`observed-signal-restatement@1.0.0`. `interpretation_kind = DETERMINISTIC`,
`model_version = NULL`, `prompt_version = NULL` — and the database refuses a
`DETERMINISTIC` interpretation that carries either.

## Which Signal types does it support?

Exactly three: `numeric_period_change`, `lexical_frequency_change`,
`lexical_frequency_contrast`. **Anything else is `UNSUPPORTED_SIGNAL_TYPE`** —
there is no generic prose path, because a sentence nobody specified is a
proposition nobody reviewed.

## Does it use an LLM?

**No.** A template is a format string applied to structured facts.
`validate_claims.py` walks every import in the interpreters, the job, the
repositories and `packages/claim-model`, and fails the build on any network
client, model SDK, gateway or embedder. Probed against three deliberate imports.

## Can it create INFERRED Claims?

**No, and not by configuration either.** `_CLAIM_TYPE` is a module constant;
`interpret(signal, request)` has no claim-type parameter; no module in the
package references `ClaimType` other than `OBSERVED`. The validator asserts that
over the **AST**, so a docstring naming `INFERRED` cannot fail it and a rename
cannot slip past it. Probed by flipping the constant — caught.

## How is OBSERVED source attribution preserved?

Every statement names the source and says "reported that". The name comes from
`registry.sources.canonical_name` — the authoritative registry, not a map in the
interpreter — falling back to the source id.

Three attribution facts come from the **contributing normalized records**,
because the Signal's scope does not carry them: `series.resource_id`,
`geography.source_name`, and the term/language schemes. Each must be agreed by
every contributing record; disagreement is `AMBIGUOUS_SIGNAL_LINEAGE` and
absence is `SIGNAL_LINEAGE_UNAVAILABLE`. **The interpreter refuses rather than
picks.**

The geography is the source's own name (`Germany`), never our canonical code
(`DE`). The code is what a reviewed mapping decided; the name is what World Bank
published, and OBSERVED reports the second.

## What proposition templates exist?

```
{Source} reported that "{metric}" for "{geography}" increased/decreased/was
    unchanged between "{period A}" and "{period B}" by {magnitude}.

{Source} reported that, in its "{stream}" stream under source language label
    "{label}", the term "{term}" appeared {n} more/fewer times in source bucket
    "{later}" than in the preceding source bucket "{earlier}".

{Source} reported that, in its "{stream}" stream under source language label
    "{label}", within source bucket "{label}", the term "{A}" appeared {n}
    more/fewer times than the term "{B}".
```

## How is proposition identity computed?

`sha256` over the canonical JSON of the facts the proposition asserts, with a
`proposition` discriminator so two shapes cannot collide. `proposition_facts`
stores the **preimage** (migration 0018), so the identity can be verified and
explained rather than merely trusted — a hash nobody can inspect is an identity
nobody can dispute.

## Is wording identity or semantic identity?

**Semantic.** Two interpreters wording one fact differently produced one claim,
and a claim reworded in revision 3 is the same claim.

The load-bearing consequence: **the magnitude is not part of the key.** A source
revising 187,180 to 187,200 restated the *same proposition*, so a
re-interpretation appends **revision 2** rather than creating a second claim.
Revision 1 is never modified. Proven on live data by rewriting a Signal's
magnitude and re-running.

For a **contrast**, where `direction` is `NOT_APPLICABLE` by construction, the
relation between the two terms comes from the **sign** of the magnitude and *is*
part of identity while the value is not. A revised count that keeps the ordering
is the same proposition; one that flips it is a different one.

Never the prose, never the Signal id, never the research session, never an
embedding. **D-12 stays open and nothing here depends on it.**

## How is interpretation confidence determined?

`1.0`, and it says exactly one thing: **the interpreter correctly restated the
Signal.** A format string over structured facts either read them or raised.

## Is interpretation confidence EvidenceScore?

**No.** `EvidenceScore` is `0–100` and is aggregation's output over the Evidence
factors; this is `[0,1]` and is about the reading. A deterministic restatement
holds `1.0` while every Evidence row behind it is `NON_SCORABLE` — both true at
once, and the pair is exactly why they are different fields.

`derivation_confidence` from the Signal is **not** reused. No code multiplies,
copies or defaults one from the other.

## How are Claim revisions created?

`persist_claims` looks up the proposition key. Three outcomes:

| | |
|---|---|
| `NEW` | Claim + revision 1 + evidence |
| `UNCHANGED` | Statement byte-identical. Nothing written |
| `REVISED` | Statement differs. Revision N+1 appended, `current_revision` moved |

`REVISED` is where this differs from `persist_signals`, deliberately: a Signal
whose fingerprint carries different content is a `CONFLICT` and the stored row
stands, because the extractor is not deterministic. A claim is not that — the key
is over the facts, not the magnitude.

## Are Claims append-only?

**Revisions are.** Revision 1 is never modified: an aggregation that evaluated
revision N must still be able to read revision N. The statement lives only in
`research.claim_revisions`, so the current text and the history cannot disagree —
asserted by a test that reads `information_schema`.

## How are Claims and Evidence persisted atomically?

One transaction, always. Not a preference:
`research.require_evidence_for_generated_claim` is a `DEFERRABLE INITIALLY
DEFERRED` constraint trigger firing at COMMIT, so evidence in a second
transaction is too late by construction. A test writes a generated claim with no
evidence, forces `SET CONSTRAINTS ALL IMMEDIATE`, and asserts SQLSTATE `23514`.

## How does Evidence link Signal and Claim?

`scoring.evidence.claim_id` (`NOT NULL` since 0016) and `signal_id`. A generated
row must cite a Signal — `SIGNAL_NOT_CITED` otherwise. Composite foreign keys on
`(workspace_id, signal_id)` and `(workspace_id, claim_id)` make a cross-tenant
citation impossible.

## What Evidence direction is generated?

`SUPPORTS`, always. The claim *is* the Signal said back; it cannot bear against
itself, and a generated `NEUTRAL` row is refused by the contract.

## What relevance value is used, and why?

**`1.0`.** Relevance asks how much what the Signal is about overlaps what the
Claim is about. They are the same subject **by construction** — the claim
restates that Signal and nothing else — so any lower value would describe a gap
that does not exist.

## What directness value is used, and why?

**`1.0`.** The Signal bears on the Claim itself, not on something adjacent: the
claim asserts exactly what the Signal measured. Directness is not source
truthfulness, and this value says nothing about whether World Bank is right.

## What reliability value is used, and why?

**None. It is written `NULL`**, and this is the deliberate one.

Reliability is **purpose-relative** and **D-03 is blocked**. There is no reviewed
value for "World Bank population data, for a claim about what World Bank
reported", and a constant would be the per-source coefficient the framework
refuses. Source approval status is not epistemic reliability either.

## What extraction confidence is used, and why?

**`1.0`.** The interpreter read the Signal correctly. It says nothing about
whether the source captured reality.

## What independence state is used?

**`UNKNOWN`**, always, with no group. Two Signals from one publication stream are
not independent because they are two, and declaring them dependent is a
judgement this layer cannot make either. `source_id` travels so aggregation can
group by origin later. Record what you know, promote nothing.

`observation_category` is `UNCATEGORISED` for **both** sources: a population
count is not `MARKET_ACTIVITY` (it is context) and a news-corpus frequency is
nobody's behaviour. `evidence_level` is `1`, which is where the ladder's own
gates leave a single `UNCATEGORISED` record of `UNKNOWN` independence.

## How are interpretation refusals persisted?

`research.claim_interpretation_runs` — one row per **execution**, written in the
same transaction as the claims, carrying the refusal list as JSONB. **A refusal
never becomes a Claim**: a row in a table of claims says a claim exists (the
ADR-021 argument, one layer up).

## How was GAP-5 resolved?

`research.claim_interpretation_inputs`: one row per Signal a run **considered**,
with its role and why.

| Role | Meaning |
|------|---------|
| `CITED` | A Claim was emitted; the row names it |
| `EXCLUDED` | **Never attempted** — no template, or lineage unreadable |
| `REFUSED` | **Attempted, and the model rejected the draft** |

`EXCLUDED` and `REFUSED` are kept apart because never-attempted and
attempted-and-rejected call for different fixes. Rows are written for `CITED`
Signals too — a table holding only exclusions could say what was skipped and not
what the denominator was, and the denominator is the finding.

It hangs off the **run**, not the claim, because a Signal considered and not
cited has no claim to hang off, and exclusion is a property of an execution
rather than of a proposition (ADR-025).

## Can the system say which Signals were considered but not cited?

**Yes**, as one indexed query per run. The current answer is *7 considered, 7
cited, 0 excluded, 0 refused* — and before migration 0018 the same seven claims
could have come from seven Signals or from four hundred, with nothing recording
which.

## How is H-29 enforced?

Four ways, none of them prose:

1. **The wording.** "source bucket" and "the preceding source bucket". No clock,
   no date, no timezone, no cross-source alignment.
2. **`observed_at` is written `NULL`** on every Evidence row.
3. **Accepted bases per template.** A `lexical_frequency_change` Signal on
   `COMPARABLE_INSTANTS` is refused with `INCOMPATIBLE_TEMPORAL_SEMANTICS`
   rather than described with wording chosen for a different basis.
4. **The AST.** `validate_claims.py` fails the build on `astimezone`, `now`,
   `utcnow`, `today`, `localtime`, `fromtimestamp` or a `tzinfo=` keyword
   anywhere in the package. Probed twice.

**H-29 remains open.**

## How is H-30 enforced?

The templates say *under source language label "ENGLISH"* and the fact set
carries `language_source_scheme: cld2-language-name`. `canonical_tag` is
**never read** — asserted over call arguments and subscripts, so the prose
explaining the rule cannot fail it. Probed. **H-30 remains open.**

## Can a World Bank population Signal produce a demand Claim?

**No.** The four numeric Signals are over `SP.POP.TOTL`. A population change says
how many people exist, not what any of them want or would pay for; there is no
reasoning step to demand that does not smuggle in a premise nothing supplies.
The template cannot express one, and the vocabulary guard refuses one.

## Can a GDELT frequency Signal produce an interest/demand Claim?

**No — not weakly, not with a low relevance, not with a caveat.** The quantity is
about a different subject: journalists publishing, not people wanting. A low
relevance would model it as *a little bit of the right thing* when it is none of
it, and a system that admits it weakly ranks press cycles with a number attached
that looks considered.

## How many production Claims were created?

**7**, all `OBSERVED` / `DETERMINISTIC_EXTRACTION` / `EVERGREEN` / `ACTIVE`, none
attached to an Opportunity. One per Signal — the canonical identity produced no
merges, and the count was read from the data rather than asserted in advance.

## How many ClaimRevisions?

**7.** All revision 1, `material_change = false`, `interpretation_confidence = 1.0`.

## How many Evidence rows?

**7.** One per claim, each citing its originating Signal.

## Did a second execution create duplicates?

**No.** Run 2 over the same seven Signals: 0 new claims, 0 revisions, 0 evidence,
7 reported unchanged. Totals stayed 7 / 7 / 7.

It wrote a **second run row** and a second set of seven considered-input rows,
because a run is an execution and two executions happened. **This is not
exactly-once** — Celery does not provide it, and the CLAIMS are what is
idempotent.

## Are Evidence items scorable today?

**No.** All seven are `NON_SCORABLE` with `MISSING_RELIABILITY`, because
reliability is `NULL` for the reason above.

## Was Evidence Aggregation exercised?

**Yes**, against the real rows, with `allow_uncalibrated=True` — the framework's
own switch for synthetic and experimental work.

```
7 claims · 7 items · 0 scorable · 7 non-scorable
status UNAVAILABLE · calibrated False · score None
reasons ['MISSING_RELIABILITY']
```

The framework accepts the rows and returns no score. **Nothing was persisted, and
no reliability was invented to make a number appear** — which is the failure
`evidence-aggregation-framework-v1.md` §6 exists to prevent.

## Did all 12 RawRecords, 12 NormalizedRecords and 7 Signals remain unchanged?

**Yes**, verified by a content digest over ids, hashes, keys, payloads,
magnitudes, directions, scopes and windows, taken before and after each run:

| Table | Digest |
|-------|--------|
| `acquisition.raw_records` | 12 rows, unchanged |
| `acquisition.normalized_records` | 12 rows, unchanged |
| `nlp.signals` | 7 rows, unchanged |
| `nlp.signal_inputs` | 14 rows, unchanged |

The pytest post-suite check independently reports the database unchanged across
24 tenant tables and 14 global tables.

## Were any Opportunities generated?

**No.** `research.opportunities` = 0, and `validate_claims.py` fails the build on
a write to it.

## Were embeddings generated?

**No.** `nlp.embedding_provenance` = 0. No Qdrant, no BGE-M3, no embedder import.
**D-12 remains open.**

## Was scoring performed?

**No.** No `EvidenceScore`, `OpportunityScore` or any other score was persisted.
**D-03 remains calibration-blocked** and no `CALIBRATED` profile exists.

## What should Mission 1.14 implement next?

Three candidates, in the order the evidence supports:

**1. The reliability question, before anything consumes these Claims.** Every
Evidence row is non-scorable for one missing factor, and that is not an accident
to fix by filling it in. Reliability is purpose-relative, which means the
mission is *what a reviewed reliability assessment is and who may write one* —
governance, in the shape Mission 1.4 gave to acquisition conditions. Until then
nothing downstream can score, and that is the system working.

**2. Source families, not more interpretation.** The seven Claims are strong on
*published aggregate context* and empty on *individual behaviour*. Pain, desire,
willingness to pay, competition, distribution and retention all need the second,
and every one of them is blocked by a source's terms rather than by engineering.
A second interpreter over the same two sources would produce more claims about
publications and no more evidence about people.

**3. `INFERRED` interpretation — but only with GAP-5 read.** The machinery is
ready: a reasoning step, a rationale, a confidence. What is missing is that
nothing yet *reads* the considered set, so an inference citing three of forty
Signals would look identical to one citing three of three. Making the selection
visible to whatever consumes claims should precede making the claims harder to
check.

**Not Opportunity discovery.** A Claim may precede an Opportunity (ADR-024), which
made grouping a separate decision rather than a precondition. It is still a
decision nobody has taken, and taking it on seven source-level claims would be
deciding it on the thinnest evidence the system will ever have.

---

## 1. Two guards that had to change, and why it was not weakening

**`validate_signals.py` scanned all of `sros_nlp` for later-stage table writes.**
`claim_repositories.py` writes claims and evidence, because writing them is what
it is for — so the check failed on correct code.

The rule's *subject* had moved: `sros_nlp` held one layer when the check was
written and holds two now. The fix names the subject rather than relaxing the
rule, and adds an **exhaustiveness check** so the narrowing stays honest: every
module under `sros_nlp` must be classified as signal-layer or claim-layer, and
an unclassified module fails the build. An exclusion that grows by adding a file
is not an exclusion.

Probed: a `research.claims` write planted in a *signal* module is still caught,
and an unclassified module is caught.

**The vocabulary guard refused its own subject.** One template restates a GDELT
lexical term, and a GDELT term is arbitrary text. `market`, `demand` and `pain`
are ordinary English words a news corpus contains, so
*`GDELT reported that the term "demand" appeared 12 more times`* — the most
faithful restatement available — was refused.

The guard was checking the whole statement when what it is about is the
interpreter's own prose. Quoted spans are now exempt, and matching is over
**tokens** rather than substrings (`supermarket` is not `market`). Three tests
build Signals whose term is literally `demand`, `market` and `pain`.

Both are recorded as `testing-strategy.md` §30 and §31.

## 2. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | **470** tests, 7 packages, pass |
| Pytest suites | 7 packages, pass; database unchanged across 24 tenant and 14 global tables |
| `validate_claims` (new) | pass — 11 boundary groups, **probed against 11 deliberate violations** |
| `validate_signals` | pass — 7 boundary groups, re-probed after narrowing |
| `validate_schema` · `validate_source_registry` · `validate_normalization` | pass |
| `validate_compliance_capabilities` · `validate_evidence_aggregation` | pass; production scoring still blocked |
| Contracts `--check` | pass — TS, Python and JSON Schema current at `1.10.0` |
| TS conformance | 21 tests, pass |
| Generated documents `--check` | 4 of 4 current |
| `ruff check` / `ruff format --check` | pass |
| `mypy` | pass — **138** source files |

## 3. State after this mission

| Table | Count |
|-------|-------|
| `acquisition.raw_records` | 12 |
| `acquisition.normalized_records` | 12 |
| `nlp.signals` | 7 |
| `nlp.signal_inputs` | 14 |
| `nlp.signal_derivation_runs` | 6 |
| **`research.claims`** | **7** |
| **`research.claim_revisions`** | **7** |
| **`scoring.evidence`** | **7** |
| **`research.claim_interpretation_runs`** | **2** |
| **`research.claim_interpretation_inputs`** | **14** |
| `research.opportunities` | 0 |
| `nlp.embedding_provenance` | 0 |

## 4. What these Claims still do not establish

**No pain. No desire. No willingness to pay. No pricing power. No competition
gap. No distribution feasibility. No retention. No revenue potential.**

They are factual, source-level claims about two publications: what World Bank
reported about a population figure, and what GDELT reported about how often a
term appeared in a news corpus. Every one of them is supported by a single
Evidence record that no aggregation can score today.

The first Claims existing does not make Opportunity discovery ready. What it
makes ready is the layer above having something honest to read.

## 5. Open questions after this mission

| Id | State |
|----|-------|
| **H-29** GDELT bucket timezone | **OPEN**, and now enforced in the claim wording and over the AST |
| **H-30** CLD2 language mapping | **OPEN**, same |
| **D-03** scoring parameters | Framework-resolved, uncalibrated. Every Evidence row is non-scorable for want of a reviewed reliability |
| **D-08** which normalized row to read | Failed closed. Untouched |
| **D-12** embedding versioning | **OPEN**, and nothing in this mission depends on it |
| **GAP-5** considered but not cited | **RESOLVED** (ADR-025). Whether an aggregator should *read* it is D-03's question |
