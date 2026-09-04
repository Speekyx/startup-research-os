# ADR-037 — Deterministic inferred Claims need two additive records, and neither exists

**Status:** Accepted
**Date:** 2026-09-04
**Mission:** 1.50
**Supersedes:** nothing. **Amends:** nothing. It implements the decision ADR-036
made, by specifying what must exist before an evaluator can be written.

---

## Context

ADR-036 decided that a source-independent proposition is an `INFERRED` Claim, and
established that `ClaimType.INFERRED` with `interpretation_kind = DETERMINISTIC`
is representable in the current schema today. It deliberately left four questions
open.

This ADR answers them. The short version: the Claim and the Evidence need nothing
new, and the **reasoning** needs somewhere to live that does not currently exist.

## Decision

**Q1 — Derivation provenance lives in a new structured record, and
`origin_detail` keeps its existing single responsibility.**

**Q2 — Evidence attaches directly: Signal → INFERRED Claim, with `SUPPORTS` or
`CONTRADICTS`.** No Claim-to-Claim relation. Derivation provenance is recorded
separately, because attachment and reasoning answer different questions.

**Q3 — The evaluator belongs in a new package**, specified here and deliberately
not created, depending on `sros-contracts`, `sros-claim-model` and
`sros-signal-model` and on nothing else.

**Q4 — Threshold provenance lives in a dedicated parameter-registration record**
referenced by the derivation, never on the Claim.

**Schema necessity: `BOTH_REQUIRED`.** Claim storage and Evidence storage need no
change. Derivation provenance and threshold provenance each need an additive
table. **No migration was created**; §29 requires the contract first.

## Why `origin_detail` cannot carry the reasoning

It is the Mission 1.15.4 failure shape: one free-text field answering two
independent questions.

`origin_detail` answers *where did this Claim come from*, and it does so on all
43 live Claims with sentences like *"Restated from signal `<id>`
(content-request-change@1.0.0)."* A derivation reasoning step answers *why does
this measurement satisfy this proposition*. Put both there and no reader and no
query can tell which question a given sentence is answering.

For an INFERRED Claim `origin_detail` keeps its job: it names the evaluator that
produced the Claim, exactly as it names the interpreter that restated a Signal
today.

## Why the existing run tables cannot carry it either

This is the finding that decides the schema question, and it is measured rather
than argued.

`research.claim_interpretation_inputs` is the closest existing structure: one row
per (run, signal), carrying `role`, `claim_id`, `reason_code` and `detail`, with
64 rows live. It looks like an evaluation record.

It cannot be the canonical derivation authority because **it expires**. All 12
rows of its parent `research.claim_interpretation_runs` carry a populated
`expires_at` roughly ninety days out, and the foreign key from inputs to runs is
**`ON DELETE CASCADE`**. When a run is removed, every input row goes with it.

**A Claim would outlive the record of how it was derived.** A retention-bounded
execution log is the right shape for *what did this run consider and refuse*
(GAP-5, ADR-025) and the wrong shape for *why is this Claim true*.

`proposition_facts` was also considered and rejected: it is the preimage of the
proposition KEY, so putting derivation facts there would make them identity — the
opposite of what ADR-036 decided.

## Why Evidence attaches directly

`claim-epistemic-semantics-v1.md` §4 already says an INFERRED claim carries *"the
Signals it reasoned from, as Evidence"*. That is exact and unambiguous, so it is
treated as existing architectural intent rather than reopened.

It also reuses the Evidence contract unchanged, preserves the full chain to
RawRecord, and feeds the aggregator that already consumes Evidence rows. A
Claim-to-Claim relation would need proxy Evidence anyway, because the aggregator
aggregates Evidence and not relations — more machinery for the same result, and a
second place the epistemic chain lives.

**Attachment and derivation provenance are both required and neither substitutes
for the other.** Evidence says *which observation bears on this Claim, and in
which direction*. The derivation record says *how that direction was determined,
under which rule, against which threshold, on what equivalence basis*.

## Granularity: one rule, many evaluations

A single Claim-level rationale is insufficient the moment two sources take
different directions: one sentence cannot explain both why A supports and why C
contradicts. So the rule is registered once and **each evaluation is its own
record**, bound to the **ClaimRevision** rather than the Claim.

Binding to the revision matters. A threshold proposition can stay the same while
the rule version, the inputs or the rationale change; binding to the Claim would
let a later derivation silently rewrite the reasoning behind an earlier revision,
and the claim model's append-only guarantee exists precisely to prevent that
class of rewrite.

## Threshold provenance is not proposition identity

`M >= 100` with a `PREREGISTERED` threshold and `M >= 100` with a `POST_HOC`
threshold are **the same proposition**. They assert the same thing about the
world and have the same falsifier. What differs is calibration eligibility, which
is a fact about how the bound was chosen rather than about what is claimed.

Making provenance identity would fork one proposition into several.

**And provenance never changes logical entailment.** A `POST_HOC` threshold with
a measurement of 110 genuinely supports `M >= 100`. What hindsight costs is
eligibility as a calibration case, not truth.

## What "preregistered" means, exactly

    threshold_registration.recorded_at  <  observation.retrieved_at

**`retrieved_at`, not `published_at`.** The bias preregistration guards against is
the analyst's, and an analyst can only be influenced by data that reached them. A
figure may have been public for years before this system retrieved it, and a
bound frozen in that window was not chosen with knowledge of it. Using
`published_at` would mark such a bound `POST_HOC` for a hindsight that did not
occur.

Not repository commit time either: a commit records when a file changed, not when
a measurement became available to the decision process.

**The limit is stated rather than hidden.** This relation is necessary and
machine-checkable. It is **not sufficient** to exclude human foreknowledge — a
person could have read a public figure outside this system before registering the
bound, and no timestamp here can detect that. So `PREREGISTERED` means *this
system did not hold the measurement when the bound was frozen*. It does not mean
*nobody knew*, and a future calibration mission must not read it as the stronger
claim.

A measurement already held when the bound is registered is `POST_HOC` by
construction.

## `interpretation_confidence` is not a gap

§17 required this to be investigated rather than guessed, and the answer comes
from the column comment and the constructor guard.

The documented meaning: *"Confidence that THIS WORDING faithfully states what the
cited Signals showed. Never a market confidence and never an EvidenceScore."* It
is mandatory for automated claims — `build_claim` refuses one without it.

For an OBSERVED restatement, reading the facts correctly is the whole job, and
the interpreters set `1.0` because *"a template applied to structured facts is
certain it read them correctly"*.

A deterministic INFERRED threshold Claim has **one step the OBSERVED case does
not**: asserting that the source-native measurement is a measurement of the
Claim's quantity, under its definition and unit. That assertion is exactly what
the field's documented meaning covers.

So `interpretation_confidence` here is **confidence in the semantic-equivalence
mapping, not in the arithmetic** — and it must not be set to `1.0`
automatically, because the derivation being exact says nothing about whether the
wording faithfully reads the Signal. The field accommodates deterministic
INFERRED without strain, and it lands on the one genuinely uncertain step.
`INTERPRETATION_CONFIDENCE_SEMANTIC_GAP` is deliberately not reported.

## No confidence on an exact entailment

There is no `derivation_confidence` field, and there must not be. `110 >= 100` is
exact. A confidence on it would be a number nobody fitted, invented because a
numeric column exists elsewhere.

Measurement reliability and derivation validity stay separate and are never
multiplied (ADR-036).

## Where the evaluator goes, and why not in the interpreters

`validate_claims.py` fails the build on any non-OBSERVED `ClaimType` access in the
interpretation package, over the AST. Hosting the INFERRED evaluator there would
require weakening that guard, and **a guard removed to let new work through is a
guard that never was**.

A new package keeps the OBSERVED interpreter exactly as narrow as it is. It may
depend on `sros-contracts`, `sros-claim-model` and `sros-signal-model` — all
already in the bare-python runner — and on nothing else. In particular not on
`sros_acquisition`, because a component able to read the source registry could
decide its own authorization; and not on the Gateway, because a package that
cannot import a provider cannot call one by accident.

**The package was not created.** §38 forbids creating production code merely to
host tests, so this mission's contract tests live in `claim-model` and
`evidence-aggregation`, the packages that already own the rules being proved.

## Consequences

- **Two additive tables are required** and fully specified: a derivation
  provenance record and a threshold registration record. **No migration was
  created.**
- **Nothing existing changes.** 43 Claims, 44 revisions and 57 Evidence rows are
  untouched; `validate_claims.py`, `SourceBoundary`, `proposition_key` and the
  reliability scope are all unmodified.
- **Every INFERRED Evidence row will initially resolve
  `NO_APPLICABLE_ASSESSMENT`**, because a new proposition kind with
  `claim_type = INFERRED` matches no existing reliability assessment. That is
  correct, and no reliability work was done.
- **`NOT_APPLICABLE` and `UNKNOWN` produce a derivation record and no Evidence
  row**, so a refusal is auditable rather than invisible — the shape ADR-021 and
  ADR-025 already use for refused derivations and interpretations.
- **Evidence idempotency and derivation idempotency use deliberately different
  keys.** Evidence is keyed on `(workspace, claim, signal)` — Mission 1.41
  removed `extraction_method` from it because a version bump must not INSERT a
  duplicate. A derivation record keys on `(workspace, claim_revision, signal,
  rule_version)` and **must** be distinct per rule version, because replaying a
  different rule is different reasoning about the same relation.

## Alternatives rejected

| Alternative | Verdict | Why |
|---|---|---|
| Reuse `origin_detail` for reasoning | Rejected | One field, two questions — the Mission 1.15.4 shape |
| Use `claim_interpretation_inputs` | Rejected on a measured fact | Cascades on an expiring run; a Claim would outlive its reasoning |
| Put derivation facts in `proposition_facts` | Rejected | That is the key preimage, so they would become identity |
| Claim-to-Claim derivation relation | Rejected | The aggregator consumes Evidence, not relations; needs proxy Evidence anyway |
| A new Evidence subtype | Rejected | Current Evidence semantics represent it exactly; direction is already claim-relative |
| Evaluator inside the interpreter package | Refused outright | Would require weakening `validate_claims.py` |
| A `derivation_confidence` field | Rejected | An exact entailment does not take a confidence |
| Threshold provenance on the Claim | Rejected | Would tie a parameter's registration to a Claim that does not exist yet, and invites it into identity |

## Open questions

- Whether the semantic-equivalence basis registry is a table or a reviewed
  document like the canonical subject registry. Both are defensible; the contract
  requires only that it exist and be referenced by id.
- Whether a derivation record should be superseded or appended when a rule
  version changes. The idempotency key makes them distinct rows; whether the
  earlier one is marked superseded is a storage decision for Mission 1.51.
