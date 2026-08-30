# Claim / Evidence Interpretation Gap Analysis V1

**Status:** Written **before** any persistence change, per Mission 1.13 §41.
**Date:** 2026-08-30 (Sprint 1 / Mission 1.13)
**Compares:** the interpretation contract proposed in
[`claim-evidence-interpretation-contract-v1.md`](claim-evidence-interpretation-contract-v1.md)
against `research.claims`, `research.claim_revisions` and `scoring.evidence` as
migrations 0001 and 0005 left them.
**Related:** [`claim-epistemic-semantics-v1.md`](claim-epistemic-semantics-v1.md),
[`signal-to-evidence-semantics-v1.md`](signal-to-evidence-semantics-v1.md),
[ADR-024](../architecture/adr/ADR-024-claim-precedes-opportunity.md).

---

## 0. Method

The three tables were designed in Mission 0.1 and realigned in Mission 1.2, both
**before any Signal existed**. Mission 1.13 §41 says not to fit the contract
around historical schema mistakes, so the contract was written from the pipeline
that now exists and the schema measured against it.

```text
research.claims               0 rows
research.claim_revisions      0 rows
scoring.evidence              0 rows
writers in the repository     none
```

Same position `scoring.evidence` was in at Mission 1.2 and `nlp.signals` at
Mission 1.11: nothing has been written, so a correction costs nothing but the
thinking.

---

## 1. The finding that governs the rest

### GAP-1 — a Claim cannot exist without an Opportunity, and the pipeline runs the other way

**Class: ontology + contract + database. The one that blocks Mission 1.13.1.**

```sql
opportunity_id UUID NOT NULL
```

Ontology V2.1 §17.3: *"A Claim belongs to **exactly one** Opportunity."*

The pipeline this mission defines, and the one the system actually has, runs:

```text
Signal → Evidence → Claim → … → Opportunity
```

Claims come **before** opportunities, in dependency and in time. The schema
encodes the opposite: an Opportunity exists first and Claims are assertions
*about* it. That was a reasonable model in Mission 0.1, when the system had no
data and an opportunity was the thing being described. It is the wrong way round
now.

**This is not a preference, it is a contradiction the audit makes mechanical.**
Mission 1.13 §43 and §44 propose that Mission 1.13.1 begin with deterministic
`OBSERVED` claim generation. Against this schema that is impossible: there are
**zero** opportunities, and creating one would be generating a product idea from
nothing — which Mission 1.13 §51 forbids in the same breath.

An observed claim like

> World Bank reported that Germany's population rose by 187,180 between 2018 and
> 2019.

is not about a product. It is a fact a future opportunity may cite, and it has
to be able to exist before anybody has thought of the product.

**Resolution.** `opportunity_id` becomes **nullable**: `NULL` means *not yet part
of any opportunity's evaluation*. Everything §17.3 actually argued for survives —
aggregation stays per claim, one opportunity still carries many claims, and
cross-opportunity sharing is still not modelled. Only the *existence*
requirement is relaxed, from "exactly one" to "at most one".

That is an ontology change and gets one: **Opportunity Ontology V2.2**, inheriting
V2.1 in full and amending §17.3 alone, plus [ADR-024](../architecture/adr/ADR-024-claim-precedes-opportunity.md).

---

## 2. Provenance gaps

### GAP-2 — a Claim has nowhere to record how confident its interpretation was

**Class: contract + database.**

Neither `research.claims` nor `research.claim_revisions` has a confidence
column. `scoring.evidence.confidence` exists and means something else — how much
that evidence record can be relied on.

Mission 1.13 §16 and §38 require the two to be separable: *confidence that the
interpretation is correct* is not *strength of the underlying market evidence*,
and an interpreter can be very sure it read a Signal correctly while the Signal
is weak evidence for anything.

**Resolution.** `interpretation_confidence` on the **revision**, `[0,1]`, because
a rewording can change how confident the reader should be that the sentence says
what the Signals showed. Required for an automatically produced revision,
absent for a manual one.

### GAP-3 — nothing prevents an unsupported generated Claim

**Class: database.**

Mission 1.13 §22 asks for a **machine-enforceable** rule: every persisted,
automatically generated Claim must have at least one Evidence item.

Nothing enforces it today, and it is the single rule that stops a future
interpreter storing a market assertion nothing backs.

**Resolution.** A `DEFERRABLE INITIALLY DEFERRED` constraint trigger, following
the precedent of migration 0007's verification trigger. It fires at COMMIT so a
claim, its revision and its evidence can be written in one transaction.

`HYPOTHESIS` is exempt, and the exemption is the point rather than a loophole: a
hypothesis is *by definition* a proposition that is not yet supported, and
requiring evidence for one would make the category unusable. It remains visibly
and machine-readably `HYPOTHESIS`.

`MANUAL` origin is exempt too. A person asserting something and looking for
evidence afterwards is the ordinary research motion; the rule is about what a
**machine** may store unsupported.

### GAP-4 — the claim's producer is described as a model, not as an interpreter

**Class: contract + database.** The same defect `nlp.signals` carried before
Mission 1.11.

```sql
origin          TEXT NOT NULL   -- MANUAL | DETERMINISTIC_EXTRACTION | LLM_EXTRACTION | …
model_version   TEXT
prompt_version  TEXT
```

`origin` mixes *who* with *how* (`MANUAL` and `IMPORTED` are agents;
`DETERMINISTIC_EXTRACTION` and `LLM_EXTRACTION` are methods), and a deterministic
interpreter has no identity at all — it would name itself by writing a string
into `origin_detail`, which is free text, in the field that decides whether a
result is reproducible.

**Resolution.** `interpreter_id` and `interpreter_version` become the identity,
and a closed `ClaimInterpretationKind` (`DETERMINISTIC` | `MODEL_DERIVED`)
governs the model columns with a CHECK — exactly the pattern
`nlp.signals.derivation_kind` follows. `origin` is kept: it still answers *who
asserted this*, which is a different and useful question.

### GAP-5 — an interpretation cannot say what it considered and did not use

**Class: future interpreter, deliberately not resolved here.**

ADR-021 established where a refused derivation goes: a run record, never a
signal row. An interpretation has the same shape — *N signals considered, M
cited, K excluded and why* — and there is nowhere to put it.

**Resolution: deferred to Mission 1.13.1**, on the same split Mission 1.11 and
1.11.1 used. The model mission defines what a Claim is; the run log arrives with
the runtime that produces one, because its columns depend on what the
interpreter actually does. Recorded here so it is a known gap rather than a
later surprise.

---

## 3. Evidence gaps

### GAP-6 — Evidence may be written with no Claim

**Class: database.**

```sql
claim_id UUID          -- nullable
```

Migration 0005 made it nullable *"ONLY so this migration can apply to a table
that already has rows in some future environment; there are none today, and the
repository refuses to write evidence without a claim."*

Evidence is **claim-relative by definition** — direction, relevance and
directness are all *relative to a proposition* — so a row without one is not
evidence, it is a dangling measurement. There are still no rows.

**Resolution.** `NOT NULL`. The comment that justified the nullability said the
condition was temporary; the condition never arose.

### GAP-7 — `evidence.claim_type` is a second answer to a question the Claim answers

**Class: database.**

```sql
claim_type TEXT NOT NULL   -- OBSERVED | INFERRED | PREDICTED | RECOMMENDED | HYPOTHESIS
```

It predates `claim_id`. In migration 0001 evidence pointed at an *opportunity*
and this column was how a row said what epistemic weight it carried. A-13 gave
evidence a claim, and the claim carries the type.

Two columns now answer *what kind of assertion is this*, they can disagree, and
the aggregation framework reads **neither** — its evidence item inputs are
relevance, directness, reliability, extraction confidence, freshness, direction,
observation category and independence, and `claim_type` is not among them.

**Resolution.** Dropped. `validate_schema.py` loses that enum site and keeps the
one on `research.opportunity_session_observations`.

### GAP-8 — `NEUTRAL` invites evidence rows that assert nothing

**Class: contract only.**

`direction` allows `SUPPORTS | CONTRADICTS | NEUTRAL`. Mission 1.13 §12 says not
to convert irrelevant Signals into Evidence rows merely to attach them to a
Claim.

`NEUTRAL` is not removed — a human may legitimately record that a source
examined a question and settled nothing, and the aggregation framework already
aggregates the two directions **separately**, so a neutral row contributes to
neither mass.

**Resolution: contract, not schema.** An *automatically generated* Evidence row
may not be `NEUTRAL`. An interpreter that finds a Signal irrelevant records that
in its run diagnostics and writes no row.

---

## 4. Identity and scope

### GAP-9 — a Claim has no identity beyond a random UUID

**Class: contract + future interpreter.**

Mission 1.13 §17: two semantically identical propositions from different
sessions should not necessarily become two unrelated Claims. Nothing normalizes a
proposition today, so they would.

**Resolution: a contract rule, and no database change.** A claim carries a
`proposition_key` — a canonical, **deterministic, embedding-free** key built from
the structured facts the proposition is about, never from its prose. For a
`numeric_period_change` observed claim that is source, metric, geography, both
period labels and the direction; the sentence may be rewritten without the key
moving.

**D-12 stays open and identity never depends on an embedding.** Two claims whose
prose differs and whose structured facts match are the same claim; two whose
prose matches and whose facts differ are not. Prose similarity is not identity.

### GAP-10 — a Claim cannot say which research question it was formed under

**Class: contract + database.**

Mission 1.13 §39: a claim generated during *"AI tools for solo creators in
France"* must not silently become identical in scope to one from *"enterprise
cybersecurity worldwide"*.

`origin_session_id` records **which session first met it**, which is not the same
as **what scope it was formed under** — and Ontology §17.4 is explicit that a
claim is not owned by that session.

**Resolution.** The `proposition_key` carries the scope facts the proposition
itself asserts (a geography, a metric, a term), and **not** the research
question. Two sessions asking different questions that both produce *"World Bank
reported Germany's population rose in 2019"* have produced the same claim, and
should. A claim whose proposition genuinely differs in scope has different facts
and therefore a different key.

**A-12 is not solved here** and is not touched.

---

## 5. What is already right, and stays

| | |
|---|---|
| Evidence attaches to a **Claim**, not an Opportunity | The A-13 correction. Unchanged and load-bearing |
| Append-only `claim_revisions`, never updated | An aggregation that evaluated revision N must still read revision N |
| `material_change` declared by the author | Only the person editing knows, and it cannot be reconstructed later |
| `lifecycle` is editorial, `ACTIVE | WITHDRAWN`, no `VALIDATED` | Evidence changes; a lifecycle derived from it would freeze a conclusion |
| `temporality` + `claim_feature` declared on the Claim | The claim names the key; the profile owns the half-life |
| `claim_session_observations` | A claim is not owned by the session that met it |
| Composite tenant FKs throughout, RLS `ENABLE` + `FORCE` | Unchanged, and extended to nothing new |
| `independence_state` / `independence_group_id` on evidence | Provenance grouping, not a scalar discount. Untouched |
| The five `ClaimType` values | **Not changed.** §5 says not to without strong justification, and none was found |

---

## 6. What this analysis does not decide

- **D-03 is untouched.** No aggregation runs, no profile is calibrated, and no
  score is produced or stored.
- **D-08 is untouched.** What a material revision does to evidence already
  attached is still open; `material_change` is recorded and nothing acts on it.
- **D-12 is untouched.** No embedding is read or written, and claim identity is
  defined so that it never could depend on one.
- **A-12 is untouched.** Non-geographic scoping is not addressed.
- **H-29 and H-30 stay open**, and the contract states which claim classes they
  block rather than working around either.
- **No interpreter is specified.** Minimum evidence counts, wording templates and
  refusal diagnostics belong to Mission 1.13.1, and picking them here would be
  choosing production thresholds in a model document.
