# Signal → Claim → Evidence Interpretation Contract V1

**Authoritative.** Mission 1.13.

Companion documents:

| Document | Answers |
|----------|---------|
| `claim-evidence-interpretation-gap-analysis-v1.md` | What the schema could not represent, written before the migration |
| `claim-epistemic-semantics-v1.md` | What each of the five claim types asserts, and how to tell them apart |
| `signal-to-evidence-semantics-v1.md` | How one Signal becomes Evidence *for a particular Claim*, and what it may not become |
| `deterministic-observed-claim-interpreter-v1.md` | The first interpreter to cross this boundary (Mission 1.13.1) |
| `claim-interpretation-runtime-v1.md` | How it runs, persists and refuses |
| `ADR-024-claim-precedes-opportunity.md` | Why a Claim no longer requires an Opportunity |
| `ADR-025-claim-interpretation-run-and-considered-inputs.md` | Why what a run considered is part of the record |
| `../domain/opportunity-ontology-v2.2.md` | The amended ontology sentence |

**Status of the system when this was written (Mission 1.13):** RawRecords 12,
NormalizedRecords 12, Signals 7 (4 `numeric_period_change`, 2
`lexical_frequency_change`, 1 `lexical_frequency_contrast`). Claims 0, Evidence
0, Opportunities 0. That mission created no production Claim and no production
Evidence, and the contract was written without one to look at deliberately: a
contract fitted to the first row it happens to see is a description, not a rule.

**Since Mission 1.13.1** there are 7 OBSERVED Claims, 7 revisions and 7 Evidence
rows, produced by `observed-signal-restatement@1.0.0` from those same seven
Signals. Nothing in this contract was weakened to let them exist; the two
changes the implementation forced were both additions (migration 0018) and both
are recorded in ADR-025.

---

## 1. What this contract is for

The system can now derive Signals from real data. A Signal is a *relation between
its own inputs* — `numeric_period_change` says one measured series moved between
two adjacent periods; `lexical_frequency_change` says one term's frequency
differed between two adjacent buckets in one publication stream. Neither says
anything about the world beyond the measurement.

Everything downstream — Opportunities, scores, recommendations — is about the
world. Something has to cross that line, and the crossing is where a research
system becomes either trustworthy or a machine for laundering arithmetic into
market conclusions.

**This contract is that crossing, written down before anything crosses.**

## 2. The layer sentence

Each layer is defined by the single verb it is allowed to perform.

| Layer | Verb | May assert |
|-------|------|-----------|
| RawRecord | **preserves** | Nothing. It is what arrived |
| NormalizedRecord | **reshapes** | Nothing new. Every field traces to the raw bytes or to a declared mapping |
| Signal | **relates** | A relation between two or more of its own inputs |
| **Claim** | **asserts** | A proposition about the world |
| Evidence | **bears on** | That this Signal supports or contradicts *this* Claim |
| Opportunity | **groups** | That these Claims describe one addressable thing |
| Score | **ranks** | An ordering over Opportunities |

A layer that performs the verb below it is redundant. A layer that performs the
verb above it is the bug this document exists to prevent.

## 3. The claim boundary (C-1)

> **A Signal states a relation between its inputs. A Claim states a proposition
> about the world — one that observations outside the derivation could support or
> contradict.**

The test is *falsifiability by something the derivation never saw*.

- "SP.POP.TOTL for DE was 82,905,782 in 2018 and 83,092,962 in 2019" is not a
  claim about the world in this sense. Nothing outside the two records bears on
  it; it is the records.
- "World Bank reported that Germany's population rose between 2018 and 2019" **is**
  a claim. A different World Bank vintage, an erratum, a revision could
  contradict it.
- "Germany's population rose between 2018 and 2019" is a *different* claim, about
  demography rather than about a publication. A census bears on it. The World
  Bank record is evidence for it, not identical to it.
- "There is growing demand for German-language SaaS" is a *third* claim, and no
  amount of population arithmetic supports it.

The three sentences are progressively further from the measurement, and each step
needs its own justification. **The failure this contract prevents is a system
that takes the first step and prints the third.**

## 4. No new database entity for the interpretation step

Mission 1.13 §4 asked whether an intermediate `ClaimCandidate` table is needed.
**It is not, and one was not created.**

The argument for one is that an interpretation may be refused, and a refused
interpretation is worth knowing about. The argument against is decisive: a
candidate table is a second place where an assertion can live, and an assertion
that lives somewhere other than `research.claims` is an assertion that escapes
every rule in this document — including the evidence requirement, which is the
whole point.

Instead the interpretation step produces an **unpersisted `ClaimDraft`**
(`packages/claim-model/python/sros_claim_model/model.py`). A draft is validated
in memory and then written as claim + revision + evidence **in one transaction**,
or it is not written at all. A refusal produces a `ClaimRefusal` carrying a
`ClaimEvidenceRefusalReason`, which belongs in the derivation/interpretation run
log alongside the refused Signal derivations — the same place, for the same
reason (`signal-derivation-runtime-v1.md`, ADR-021).

The run-log side of this was deliberately **not implemented in Mission 1.13**:
no interpreter ran yet, so a run log for it would have been a table with no
writer. **Mission 1.13.1 built it** —
`research.claim_interpretation_runs`, migration 0018, ADR-025 — because an
interpreter now writes one. No candidate table was invented.

## 5. Claim

A row in `research.claims`. It answers **which proposition**, and nothing about
wording.

| Column | Meaning |
|--------|---------|
| `id` | The row |
| `workspace_id` | Tenancy. Never defaulted |
| `opportunity_id` | **Nullable since migration 0016.** At most one, possibly none |
| `claim_type` | The epistemic type. See `claim-epistemic-semantics-v1.md` |
| `temporality` | How the claim ages |
| `origin` | Who asserted it |
| `proposition_key` | **Which proposition.** Unique per workspace |
| `interpreter_id` / `interpreter_version` / `interpretation_kind` | Interpretation provenance. All three or none |
| `model_version` / `prompt_version` | Model provenance, only for `MODEL_DERIVED` |
| `current_revision_id` | The wording in force |

### 5.1 `opportunity_id` is nullable, and this is the mission's central change

The schema before Mission 1.13 said `opportunity_id NOT NULL`: a Claim could not
exist without an Opportunity to be about. The pipeline runs
Signal → Claim → Opportunity. A Claim about a source fact exists **before**
anybody has conceived of the product it might justify.

The old constraint therefore made the intended pipeline unrepresentable —
GAP-1 in the gap analysis, decided in ADR-024, amended in ontology V2.2:

> A Claim belongs to **at most one** Opportunity, and may belong to none.

### 5.2 `proposition_key` — identity that survives rewording

Two interpreters wording the same fact differently have produced **one** claim.
A claim reworded in revision 3 is still the same claim.

The key is `sha256` over the canonical JSON of the **structured facts the claim
asserts**: source, metric, geography, period labels, term, direction. Sorted
keys, stable separators.

Three things it is deliberately not built from:

1. **Not the prose.** Prose is the revision's business.
2. **Not an embedding.** D-12 is open. An identity that depended on a vector
   would move when the model moved, and two claims whose prose is nearly
   identical while their facts differ — "…for DE" and "…for FR" — are different
   claims that no distance threshold reliably separates.
3. **Not the research question.** Two sessions asking different questions that
   both derive "World Bank reported Germany's population rose in 2019" have
   produced the same claim, and should. This resolves GAP-10 *against* putting
   the question in the identity; the session belongs on the revision as
   context, not on the proposition.

An empty fact set is refused (`PROPOSITION_NOT_IDENTIFIABLE`): it identifies
every proposition equally, which is no identity.

## 6. ClaimRevision

A row in `research.claim_revisions`. Append-only. It answers **which wording**.

| Column | Meaning |
|--------|---------|
| `statement` | The prose |
| `revision` | Monotonic per claim |
| `interpretation_confidence` | **Added in 0016.** `[0,1]`, nullable |
| `research_session_id` | Which question was being asked when this wording was formed |

The revision, not the claim, carries confidence — because confidence is a
property of *an act of interpretation*, and a re-interpretation with better
evidence is a new revision. An aggregation that evaluated revision N must still
be able to read revision N, which is why revisions are never rewritten.

## 7. Evidence

A row in `scoring.evidence`. It answers **how this Signal bears on this Claim**.

Two changes in migration 0016:

- `claim_id` is now `NOT NULL` (GAP-6). Evidence that names no Claim is evidence
  for nothing; the nullable column allowed a row that could never be read.
- `claim_type` was **dropped** (GAP-7). It was a second answer to a question
  `research.claims.claim_type` already answers, and two answers eventually
  disagree. `validate_schema.py`'s enum-site list was updated in the same
  mission.

Evidence carries no score. It carries the *factors* an aggregation reads —
relevance, directness, reliability, extraction confidence — each nullable,
because an absent factor is `NON_SCORABLE` at aggregation time and never `0.5`
and never `0.0` (`../domain/evidence-aggregation-framework-v1.md` §6).

## 8. The Signal → Evidence relation

Detailed in `signal-to-evidence-semantics-v1.md`. The contract-level rule:

> **Evidence is claim-relative. A Signal has never heard of the Claim.**

This is why direction, relevance and directness live on the Evidence row and not
on the Signal. One Signal may support Claim A strongly and contradict Claim B
weakly, and the Signal is unchanged by either.

A generated Evidence row may not be `NEUTRAL` (GAP-8, contract-level rather than
schema-level because a human may legitimately record a null result). A Signal
that bears on nothing produces **no row**: attaching it inflates the record
without changing what is supported.

## 9. The Evidence → Claim relation, and the unsupported-claim rule

> **A machine may not store an assertion nothing supports.**

Enforced in two places, deliberately:

- **In the database** — a `DEFERRABLE INITIALLY DEFERRED` constraint trigger
  (`research.require_evidence_for_generated_claim`, migration 0016). Deferred
  because a claim and its evidence are written in one transaction and neither
  exists first. The precedent is migration 0007.
- **In the model** — `build_claim` refuses with `NO_SUPPORTING_SIGNAL`, so the
  failure is caught where it can be explained rather than as a SQLSTATE.

Three exemptions, each for a reason rather than for convenience:

| Exempt | Why |
|--------|-----|
| `claim_type = HYPOTHESIS` | **By definition, not by exception.** A hypothesis is a proposition worth testing and not yet supported. Requiring evidence would make the category unusable, which would push unsupported ideas into `INFERRED` — the exact failure the rule exists to prevent |
| `origin = MANUAL` | A person asserting something and looking for evidence afterwards is the ordinary research motion. The rule is about what a **machine** stores |
| `lifecycle = WITHDRAWN` | A withdrawn claim's evidence may have been removed. Requiring it would make withdrawal impossible |

## 10. Interpretation provenance

`interpreter_id`, `interpreter_version`, `interpretation_kind` — **all three or
none**. Half an identity is a version nobody can resolve.

The naive spelling of "all three or none" is a bug: `length(btrim(NULL)) > 0`
evaluates to NULL, `false OR NULL` is NULL, and **a CHECK constraint accepts
NULL**. Migration 0016 shipped that spelling; migration 0017 replaced it with
`num_nonnulls(...) IN (0, 3)`, which cannot itself be NULL. Found by a probe
written to disbelieve the constraint rather than by review.

### 10.1 The deterministic / model-derived boundary

`ClaimInterpretationKind` has exactly two values, and the boundary is enforced,
not documented:

| Kind | Requires | Forbids |
|------|----------|---------|
| `DETERMINISTIC` | Same inputs → same output, always | `model_version`, `prompt_version` |
| `MODEL_DERIVED` | `model_version` | — |

A `DETERMINISTIC` interpretation carrying a model version is refused
(`claims_interpretation_provenance_check`). This is not pedantry: "deterministic"
is a promise that the claim can be regenerated and compared, and a model in the
path silently voids it.

### 10.2 A model is a reasoning mechanism, never the evidence

Mission 1.13 §20. An LLM may propose an interpretation. Its output **cannot
satisfy the evidence requirement**: a `MODEL_DERIVED` claim citing no Signal is
refused exactly as a deterministic one is. The model's contribution is recorded
as `interpretation_kind`, `model_version` and `prompt_version` — provenance about
*how the reading was reached* — and never as a row in `scoring.evidence`.

### 10.3 What is not stored

A short `rationale` and the `cited_facts` are persisted. **A private reasoning
transcript is not**, and there is nowhere to put one — no `chain_of_thought`
field exists on the draft, the claim or the revision, and a test asserts it.

## 11. Confidence semantics

`interpretation_confidence` on the revision, `[0,1]`, and it means exactly one
thing:

> **How confident the interpreter is that this statement is a correct reading of
> the Signals it cites.**

It is **not** how strong the evidence is (that is aggregation's job, over the
Evidence factors), **not** how likely the proposition is to be true, and **not** a
score. A deterministic restatement can hold confidence 1.0 while the proposition
it restates is barely supported, and there is no contradiction: the interpreter
is certain about the reading, and the evidence is thin.

No universal thresholds are set. Mission 1.13 §46 is explicit that "3 Signals
required" or "5 sources required" would be arbitrary numbers wearing the costume
of a rule. What a *particular* claim type requires belongs to the interpreter
that produces it, stated and versioned with that interpreter.

## 12. H-29 and H-30 interaction

Two open questions constrain what may be claimed from GDELT-derived Signals.

**H-29 — the WEB-NGRAM bucket timezone is unestablished.** ADR-022 certified
`SOURCE_RELATIVE_ORDER` for the two WEB-NGRAM resources and explicitly **not**
`COMPARABLE_INSTANT`. Consequences for claims:

- A claim may say "earlier bucket" / "later bucket" within one certified stream.
- A claim may **not** state a clock time, a date, or a wall-clock alignment.
- A claim may **not** align a GDELT bucket with a World Bank period, because
  alignment requires both to be instants and one is not.
- Refusal reason: `INCOMPATIBLE_TEMPORAL_SEMANTICS`.

**H-30 — the CLD2 language mapping is unestablished.** GDELT's language labels
have not been mapped to a standard vocabulary with first-party evidence.
Consequences:

- A claim may compare terms **within one language label**, because the label is
  its own identity whatever it maps to.
- A claim may **not** say "in French" or "in German" of a GDELT label, and may
  not compare across labels as though they were the same language space.
- Refusal reason: `INCOMPATIBLE_LANGUAGE_SEMANTICS`.

Both are recorded as refusal reasons rather than as prose warnings so that a
future interpreter fails closed. Neither is closed by this mission.

## 13. What a GDELT lexical Signal may support, and may not

Mission 1.13 §46: *do not let GDELT lexical frequency alone satisfy a demand
Claim.*

A `lexical_frequency_change` Signal supports, at most:

> "Within GDELT's WEB-NGRAM stream, the term *T* appeared more often in the later
> of two adjacent buckets than in the earlier one, under language label *L*."

It does not support "interest in T is growing", "there is demand for T", or "T is
trending". Those are propositions about people, and the Signal is a proposition
about a publication corpus. The gap is not a matter of degree: no quantity of
news-corpus frequency establishes willingness to pay, and treating it as a weak
version of demand evidence is how a scoring system ends up ranking press cycles.

An `OBSERVED` claim using market or user vocabulary is refused
(`UNSUPPORTED_INTERPRETATION`). The guard is a blunt vocabulary check and is
documented as one: it catches the obvious failure — an arithmetic relation
rewritten as a market fact — and leaves the subtle cases to review and to
`INFERRED`.

The word `growth` is deliberately **absent** from that vocabulary: "population
growth" is the name of a quantity a source publishes, and banning it would refuse
a faithful restatement. The bare word `market` is deliberately **present**, at a
stated cost: a metric whose published title contains it (`CM.MKT.LCAP.CD`,
"market capitalization of listed companies") must be restated by metric id.

## 14. Refusal reasons

`ClaimEvidenceRefusalReason`, contract `1.9.0`. A refusal is a first-class
outcome, not an exception message.

| Reason | Raised when |
|--------|-------------|
| `NO_SUPPORTING_SIGNAL` | A generated non-hypothesis claim cites nothing |
| `UNSUPPORTED_INTERPRETATION` | The statement asserts more than the cited Signals establish |
| `SIGNAL_NOT_CITED` | An evidence draft names no Signal |
| `INCOMPATIBLE_TEMPORAL_SEMANTICS` | The claim needs an instant and the Signal has only order (H-29) |
| `INCOMPATIBLE_LANGUAGE_SEMANTICS` | The claim needs a language and the Signal has only a label (H-30) |
| `PROPOSITION_NOT_IDENTIFIABLE` | No facts to build a `proposition_key` from |
| `INTERPRETER_PROVENANCE_INCOMPLETE` | Half an identity, or a kind contradicting its model fields |

## 15. What this contract does not decide

- ~~**Which Signals were considered and rejected** (GAP-5).~~ **Resolved in
  Mission 1.13.1** by `research.claim_interpretation_inputs` (migration 0018,
  ADR-025): one row per considered Signal, with its role — `CITED`, `EXCLUDED`
  or `REFUSED` — and why. It hangs off the RUN rather than the Claim, because a
  Signal considered and not cited has no Claim to hang off.
- **Claim similarity and merging.** D-12 is open and stays open; nothing here
  depends on it.
- **Aggregation.** The Evidence factors are written; how they combine is
  `../domain/evidence-aggregation-framework-v1.md`'s question.
- **Any threshold.** See §11.

## 16. Where this is enforced

| Rule | Enforced in |
|------|-------------|
| Claim may exist without an Opportunity | migration 0016 |
| A proposition key is stored with its preimage | migration 0018, ADR-025 |
| A refused interpretation gets a run record, never a Claim | migration 0018, `claim_job.py` |
| What a run considered and did not cite is recorded | migration 0018 |
| No interpreter constructs a non-OBSERVED claim type | `validate_claims.py`, over the AST |
| No template reads a canonical language tag or converts a timezone | `validate_claims.py` |
| The interpretation layer reaches no model, network or embedder | `validate_claims.py` |
| All-or-nothing interpreter identity | migration 0017 |
| Deterministic implies no model | migration 0016, `ClaimInterpretation.__post_init__` |
| Generated claim needs evidence | migration 0016 trigger, `build_claim` |
| Evidence names a claim | migration 0016 |
| Proposition uniqueness per workspace | migration 0016 |
| Confidence in `[0,1]` | migration 0016, `ClaimDraft` |
| No `NEUTRAL` generated evidence | `build_claim` |
| No interpretive vocabulary in `OBSERVED` | `build_claim` |
| No chain-of-thought field exists | the absence of one, asserted by test |
