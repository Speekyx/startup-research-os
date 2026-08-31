# Mission 1.14 — Evidence Reliability Governance & Scoring Readiness V1

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.14` · **Scope:** a
governance and epistemic contract.

**The machinery for reviewed reliability exists. No assessment was written.**
All seven Evidence rows remain `NON_SCORABLE`, aggregation returns
`UNAVAILABLE`, and no score was produced. That is **outcome B** under §23, and
§8 and §43 make it the only honest one available to this mission.

---

## 0. The finding that shaped the mission

Reliability is purpose-relative, and the framework says so per Evidence *record*.
That is semantically right and operationally impossible: it asks for a human
judgement per row. Both obvious escapes are forbidden for the same reason —
`world-bank = 0.95` is a coefficient, `0.5 because unknown` is a measurement
claiming the middle.

**The missing piece was a middle term**, and it turned out to already exist.
Mission 1.13.1 put a `proposition` discriminator at the head of every
`proposition_facts` object so two proposition shapes could not collide in a hash.
That discriminator names what a claim asserts *in kind* — which is exactly what
"purpose" means in "purpose-relative".

So an assessment applies to a **measurement × purpose** scope:

```text
source_id | resource_id | record_kind_id     the MEASUREMENT
claim_type | proposition_kind                the PURPOSE
```

The seven Evidence rows collapse to **three** scopes, and stay three however many
observations arrive. Three reviews instead of seven per-row judgements is the
design's entire justification.

## 1. Deliverables

| Artifact | What it is |
|----------|-----------|
| `docs/data/evidence-reliability-gap-analysis-v1.md` | Twelve gaps, written **before** the migration |
| `docs/data/evidence-reliability-contract-v1.md` | What reliability means and who may establish one |
| `docs/data/evidence-reliability-review-guide-v1.md` | How a reviewer writes one, and when to write none |
| `ADR-026` | Scope, binding and tenancy, with the rejected alternatives |
| `infrastructure/db/migrations/0019_…` | `epistemic` schema: assessments + documentary basis |
| `packages/evidence-reliability/` | The fail-closed resolver. Names no source |
| Contract `1.10.0` → `1.11.0` | Three closed enums, one of them closed *so that* a model cannot be recorded as a source |
| 45 + 25 new tests | Synthetic model, live constraint probes |

---

# The questions (§49)

## What exactly does Evidence reliability mean?

> **How dependable is this kind of measurement, for this kind of proposition?**

Not how permitted the source is, not how well-known it is, not how carefully we
read it, not how much it bears on the claim.

## Is reliability a property of a source?

**No.** A platform carries a maintainer's release note and an anonymous rumour;
one number cannot be right for both. `world-bank` alone matches nothing — an
assessment applies only when **all five** scope parts agree.

The framework's own example resolves with no special case: a World Bank
population record used for `source_reported_metric_period_change` may have an
assessment; the same record used for a demand proposition has a different
`proposition_kind` and matches nothing at all. **The purpose-relativity is
structural, not documented.**

## Is source approval evidence of reliability?

**No, in both directions.** An `APPROVED` source does not produce more reliable
evidence; a `RESTRICTED` source does not produce less. Mission 1.0 answers *may
we collect this*; this answers *how does it bear on this claim*.

Enforced rather than stated: a separate `epistemic` schema, no policy column
anywhere in it, and an AST test asserting no approval-state literal appears in
the resolver — excluding docstrings, so the paragraph explaining the rule cannot
fail it.

## What entity/scope carries reliability assessments?

`epistemic.reliability_assessments`, scoped to
`(source_id, resource_id, record_kind_id, claim_type, proposition_kind)`.
Identity is `assessment_key` = sha256 over those five, and `(assessment_key,
version)` is the row.

`signal_type_id` is deliberately excluded: the derivation between measurement and
proposition is the interpreter's business, and whether it read the Signal
correctly is `extraction_confidence`.

## What basis is required?

At least one **document-backed** basis row naming a retrieved first-party
document, its section, when it was fetched and a short summarized finding.
Eight basis types; `REVIEWER_DOCUMENTED_JUDGEMENT` is permitted **alongside**
documents and refused alone — on its own it is an opinion with a citation field,
which is what `"World Bank is trustworthy"` amounts to. Enforced by a
`DEFERRABLE INITIALLY DEFERRED` trigger.

`stated_limitation` is also required: **a reliability with no stated failure mode
is a number nobody can argue with.**

Full documents are never stored — a reference, a section pointer, a finding, an
excerpt capped at 1000 characters, and a fingerprint. The same discipline
`registry.source_policy_evidence` uses, and for the same reason.

## Who/what may establish an assessment?

`HUMAN_REVIEW`, `DOCUMENTED_METHOD`, `CALIBRATED_EMPIRICALLY`. `reviewed_by`
names a person and may not be blank.

## Can an LLM establish reliability?

**No, and there is nowhere to record that it did.** The origin enum is closed and
has no `MODEL_GUESSED` member — closure is the mechanism, not the documentation.
A model may help a reviewer read a methodology page; it may not be the epistemic
source of the judgement.

**This is why this mission produced no assessment.** See §11 below.

## What scale is used?

`[0,1]`, the scale the aggregation framework already uses. **Out of range is
rejected, never clamped** — a value outside it means the reviewer is on a
different scale, and clamping hides that behind a plausible number. No threshold
labels: no `0.9 = authoritative`, no `0.7 = good`. A label would be a second
scale nobody calibrated, and reviewers would target the label.

## What does NULL mean?

**Unknown**, and unknown produces no number. There is no way to express "unknown"
as a *value*: an assessment that asserts nothing is not an assessment, and
unknown is the **absence of a row**. The record stays `NON_SCORABLE` with
`MISSING_RELIABILITY`, retained in the evidence set, named in
`missing_requirements`, counted towards coverage, and contributing nothing
numeric.

## Can unknown reliability default to 0.5?

**No.** Nor to 0.8 because reputable, 1.0 because official, 0.9 because
government, or 0.0 because we do not know. Every one of those is a *measurement*,
and `q_i = min(components)` would consume it as one. `0.0` is the worst of them:
it enters the arithmetic as a measured weakness, which is a different claim from
an absent measurement.

**The system must remain capable of producing no score**, and that capability is
what makes a score mean something when one appears.

## How are assessments versioned?

`(assessment_key, version)`. **Superseded, never updated**: a correction writes
version N+1 and marks version N with `superseded_at` and a `superseded_reason`.
Version N stays readable, because an aggregation that used it must still be able
to read it.

At most one **current** assessment per scope, enforced by a partial unique index.
Supersession is all-or-nothing, spelled with `num_nonnulls` — the obvious
spelling returns NULL on a half-filled row and a CHECK accepts NULL (migration
0017's lesson, applied before the bug rather than after it).

## How is applicability determined?

Exact match on all five scope parts, against **current** assessments only. The
purpose comes from the claim's own `proposition_facts` discriminator; a claim
that carries none cannot state its purpose, and no scope is guessed for it.

## What happens when no assessment matches?

`NO_APPLICABLE_ASSESSMENT`. Reliability stays `NULL`, the record is
`NON_SCORABLE`, and the outcome is recorded so the reason is legible rather than
inferred from an absence.

A distinct outcome exists for the case where assessments exist and all are
superseded: `SUPERSEDED_ONLY`. *Somebody reviewed this and withdrew it* is a
different fact from *nobody has looked*, and they call for different actions.

## What happens when multiple assessments match?

**Refused.** `AMBIGUOUS_ASSESSMENTS`, reliability `NULL`.

Never the closest — "closest" needs a distance nobody defined. Never the maximum
— optimism with a mechanism. Never the mean — averaging two competing reviewed
judgements produces a third that nobody made and nobody can defend.

A partial unique index makes this unreachable through the ordinary path. The
resolver refuses anyway: **a guard that trusts another guard is one schema change
away from trusting nothing.**

## Is reliability copied onto Evidence or resolved during aggregation?

**Resolved during aggregation, with the binding recorded** (ADR-026 Decision 2).

Copying loses *where the number came from*, and a bare `0.9` in a column is not
reconstructible. Binding to "latest" changes yesterday's score silently.
Resolving late and recording the binding does neither.

Precedence, so two answers cannot disagree:

```text
row.reliability IS NOT NULL  ->  DIRECTLY_SUPPLIED, no assessment consulted
row.reliability IS NULL      ->  resolution is attempted
```

A value on the row is a statement about *that record* and is more specific than
a class-level judgement. The second path only runs when the first is absent.

## How is historical reproducibility preserved?

Re-running against the recorded bindings reproduces the number exactly.
Re-running against current assessments produces a *different* result with a
different `evidence_snapshot_digest` — identifiable **as** a recomputation rather
than silently replacing the original. This does not resolve D-08; it refuses to
make it harder.

## What assessment version does an aggregation record?

Per contributing row: `assessment_id`, `assessment_key`, `version`, `origin`,
`reliability`, `reviewed_by`, `reviewed_at` — and for every row without one, the
resolution **outcome**, so a non-scorable row says precisely why.

## Are World Bank OBSERVED Evidence rows assessable today?

**Assessable in principle: yes. Assessed: no.**

The scope resolves cleanly —
`world-bank / indicator/SP.POP.TOTL / numeric_observation / OBSERVED /
source_reported_metric_period_change` — so the machinery admits an assessment.
No assessment exists.

The claim says *"World Bank Open Data reported that `SP.POP.TOTL` for
`"Germany"` increased between `"2018"` and `"2019"` by 187180."* The proposition
is about **the publication**, so the reliability question is *is the persisted
canonical observation a dependable representation of what the source published*
— not *was the population estimate correct*.

**That distinction does not make reliability 1.0, and treating it that way would
be exploiting the wording.** The residual failure mode is real and specific:
World Bank indicators are revised, and the claim carries a magnitude with **no
vintage**. The normalized record holds `series.source_last_updated`; the
*statement* does not. A figure revised after collection makes the claim false as
a statement about what the source currently reports, while remaining true about
what it reported on the collection date.

A reviewer would need World Bank's own indicator revision policy to decide
whether and how far that bounds the value. `evidence-reliability-review-guide-v1.md`
§9 lists what else they would need.

## Are GDELT OBSERVED Evidence rows assessable today?

**Same answer: in principle yes, in fact no.** Two scopes, both resolving
cleanly, both unassessed.

Reliability here concerns **the corpus output under the reviewed resource
contract** — not news truth, not public opinion, not market demand, not
attention, not user behaviour. A GDELT frequency measures its corpus, and the
claim says so.

A reviewer would need the corpus construction method (what is crawled, filtered,
de-duplicated — what the frequency is a frequency *over*), whether a bucket is
ever republished or backfilled, and whether the count is complete or sampled.

The change and contrast scopes are **separate assessments over one measurement**,
deliberately: unstable bucket boundaries would affect the change proposition and
not the contrast one, and a reviewer may reach different values. That two scopes
over one measurement can legitimately differ is the whole reason purpose is in
the scope.

## Did any of the seven existing Evidence rows become scorable?

**No. Zero of seven.**

## If yes, what reviewed basis justified each value?

Not applicable.

## If no, why not?

**Because I may not be the reviewer, and no other reviewer has looked.**

§8 says an LLM may assist a reviewer but cannot be the epistemic source of an
assessment. §43 says reliability cannot come from *"Claude thinks World Bank is
reliable."* Writing an assessment here would have meant recording a `reviewed_by`
that named nobody accountable — **fabricating a reviewer, which is worse than
producing no score.**

I also deliberately did **not** retrieve World Bank or GDELT methodology
documentation. §25 permits it *if authoritative methodology documentation is
needed*, and it would only be needed as the basis of an assessment I am not
permitted to make. Retrieving documents and then reasoning to a number is how one
quietly becomes the reviewer.

What the mission produced instead: the machinery, and a review guide naming the
three scopes, the failure mode to establish for each, and the document classes a
reviewer would need. That is the work that was available to do honestly.

## Did Evidence Aggregation produce a score?

**No.** Exercised over the real rows with the resolver in the loop:

```text
reliability assessments in the database: 0
evidence rows considered:                7
resolution outcomes:  NO_APPLICABLE_ASSESSMENT 7
assessment bindings recorded: none

per claim: items 1 · scorable 0 · status UNAVAILABLE · score None
           support 0.0 · contradiction 0.0 · conflict 0.0 · uncertainty 1.0
           level 0 · reasons ['MISSING_RELIABILITY']

evidence scorable: 0 of 7 · claims with a score: 0 of 7
```

`uncertainty_mass = 1.0` is the honest decomposition: nothing is known either
way. **`UNAVAILABLE` has no Evidence Score — not a score of zero.**

## Is that profile CALIBRATED?

**No.** `reference-v1` v1.0.0, status `UNCALIBRATED`, run only with an explicit
`allow_uncalibrated=True`. **Reliability review is not calibration** and does not
become it by being careful: a `HUMAN_REVIEW` assessment may not name a
calibration dataset, and the database refuses one that tries.

## What parts of D-03 remain open?

One blocker closed, four standing.

| Blocker | State |
|---------|-------|
| No definition of what reliability means or who may set it | **RESOLVED** by this mission |
| No reviewed value for any scope in use | **OPEN.** Zero assessments |
| No `CALIBRATED` profile — parameters fitted to no outcome data | **OPEN**, untouched |
| No authorised half-life for temporally sensitive claims | **OPEN.** Not reached: all seven claims are `EVERGREEN` |
| Level thresholds are structural minimums, not fitted values | **OPEN** |

`services/scoring` remains unavailable for production research.

## Did source policy states change?

**No.** `APPROVED_WITH_CONDITIONS` 5, `RESTRICTED` 6, `PROHIBITED` 3,
`REQUIRES_REVIEW` 13 — identical before and after. Policy review and epistemic
assessment are separate concerns and neither's outcome may move the other's.

## Were any Claims changed?

**No.** 7 Claims, 7 ClaimRevisions, semantically unchanged. No revision was
appended.

## Were any INFERRED Claims produced?

**No.** Mission 1.14 implements no interpretation. The seven claims are the same
seven `OBSERVED` claims.

## Were Opportunities generated?

**No.** `research.opportunities` = 0.

## Were embeddings generated?

**No.** `nlp.embedding_provenance` = 0. D-12 stays open, and applicability is
deterministic and contract-based — no semantic matching anywhere.

## Were any arbitrary coefficients introduced?

**No.** Zero rows in `epistemic.reliability_assessments`; zero Evidence rows
carrying a reliability.

Every numeric literal in the test suites is a fixture, marked as one at the point
of use, and the live probes use a resource that **does not exist**
(`indicator/PROBE.ONLY`) so a probe row escaping its rollback still could not
resolve against real evidence. A test asserts production holds zero assessments,
so a fixture becoming a fact fails the build
(`testing-strategy.md` §32).

## Does current reliability work provide evidence of pain / desire / WTP / retention?

**No, and this is the distinction the mission asked to be stated plainly.**

Reliability decides **whether the evidence the system has can be scored.** It
says nothing about **whether that evidence bears on anything anybody wants to
know.**

Even a reviewed value for all seven rows would establish nothing about pain,
desire, willingness to pay, pricing power, competition gaps, distribution
feasibility, retention or revenue potential. Seven perfectly-assessed claims
about what two publications reported are still seven claims about two
publications.

**Reliability solves scorability. It does not solve missing evidence families.**

## Which should be the next mission?

**A. Source-family expansion**, and the reasoning is not close.

**Why not C (scoring hardening).** Scoring cannot be hardened past its current
state without values that only a reviewer can supply, and the reviewer's blocker
is not engineering. Building more scoring machinery against zero assessments
would be building for a state that does not exist. The one piece of C worth doing
is small and belongs with A: recording resolution outcomes on a persisted
aggregation result, when there is an aggregation result worth persisting.

**Why not B (INFERRED interpretation).** The machinery is ready — a reasoning
step, a rationale, a confidence — and this is exactly the danger. An `INFERRED`
interpreter over World Bank population and GDELT news frequency would produce
propositions about *demand* from measurements of *publication*, and the guard
standing between it and that failure is a vocabulary check. Deeper reasoning over
these two sources means reasoning further from anything a user wants, with more
machinery in between. **The evidence is not thin; it is about a different
subject.**

**Why A.** The portfolio is strong on published aggregate context and empty on
individual behaviour, and every demand-side family needs the second:

| Family | State |
|--------|-------|
| Pain | Nothing usable. `bluesky` promising, blocked by silence |
| Desire | Nothing usable. `pinterest` promising, terms unread |
| Willingness to pay | **Nothing.** No approved source carries a price or a transaction |
| Competition | `gdelt` sees what is *written about* products, never the products |
| Distribution | Nothing. Wikipedia views are attention, not acquisition |
| Retention | Nothing. No approved source observes the same user twice |

Every one of these is blocked by a source's terms rather than by engineering,
which means the work is **review**, not code — and the review chain (Mission 1.0,
1.3, 1.4, 1.8) already exists and works. `bluesky` and `pinterest` are the two
candidates blocked only by unread or silent terms.

**The product goal decides it.** The system's purpose is discovering
opportunities from evidence about people. It currently has no evidence about
people. Reliability governance made the existing evidence honestly scorable-in-
principle; adding a demand-side family would make it possible for a score to
mean something. The second is worth more than any amount of the first.

---

## 2. Two things worth recording

**The purpose vocabulary already existed.** `proposition_kind` was added in
Mission 1.13.1 to stop two proposition shapes colliding in a hash. It turned out
to be the unit of purpose that makes a reusable reliability scope possible at
all. A discriminator added for hash hygiene became the thing that keeps
reliability from being a source coefficient.

**A guard blocked correct code and the code moved, not the guard.**
`validate_evidence_aggregation.py` forbids any registered source id in
`packages/evidence-aggregation/` — that is what keeps source identity out of the
mathematics. A resolver necessarily matches on source. Rather than narrow the
guard, the resolver went into its own package on the same side of the seam as the
existing row adapter, and got its **own** no-source-id test. Recorded as
`testing-strategy.md` §33: when a guard blocks correct new code, first ask
whether the code is on the right side of the boundary the guard defends.

## 3. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | **515** tests, **8** packages, pass |
| Pytest suites | 7 packages, pass; database unchanged across 24 tenant and **16** global tables |
| `validate_schema` | pass — 9 invariant groups, **40** tables, three new enum sites |
| `validate_evidence_aggregation` | pass — the no-source-id guard **untouched** |
| `validate_claims` · `validate_signals` · `validate_normalization` | pass |
| `validate_source_registry` · `validate_compliance_capabilities` | pass |
| Contracts `--check` | pass — TS, Python and JSON Schema current at `1.11.0` |
| TS conformance | 21 tests, pass |
| Generated documents `--check` | 4 of 4 current |
| `ruff check` / `ruff format --check` | pass — 391 files |
| `mypy` | pass — **140** source files |

## 4. State after this mission

| Table | Count |
|-------|-------|
| `acquisition.raw_records` | 12 |
| `acquisition.normalized_records` | 12 |
| `nlp.signals` | 7 |
| `research.claims` | 7 |
| `research.claim_revisions` | 7 |
| `scoring.evidence` | 7 |
| `scoring.evidence` rows carrying a reliability | **0** |
| **`epistemic.reliability_assessments`** | **0** |
| **`epistemic.reliability_assessment_basis`** | **0** |
| `research.opportunities` | 0 |
| `nlp.embedding_provenance` | 0 |
| Scores of any kind | 0 |

## 5. Open questions after this mission

| Id | State |
|----|-------|
| **D-03** scoring parameters | One blocker closed, four open. Production scoring blocked |
| **D-08** recomputation policy | **OPEN**, and deliberately not made harder: bindings are recorded |
| **D-12** embedding versioning | **OPEN**, and nothing here depends on it |
| **H-29** GDELT bucket timezone | **OPEN**, untouched |
| **H-30** CLD2 language mapping | **OPEN**, untouched, and named as something a GDELT reviewer must not resolve by assessing reliability |
| Workspace-scoped assessments | **Not built.** ADR-026 Decision 3 records what adding one would take |
| Three unassessed scopes | Named in `evidence-reliability-review-guide-v1.md` §9, awaiting a reviewer |
