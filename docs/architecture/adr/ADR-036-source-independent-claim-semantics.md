# ADR-036 — A source-independent proposition is an INFERRED Claim

**Status:** Accepted
**Date:** 2026-09-04
**Mission:** 1.49
**Supersedes:** nothing. **Amends:** nothing. It decides where a proposition
about the world, rather than about a publisher, belongs — and the answer is a
layer the ontology already defines and nobody has built.

---

## Context

Missions 1.47 and 1.48 found the same wall from opposite sides.

Mission 1.47 tried to make two measurement apparatuses support one Claim and
could not: `PropositionConvergenceContract` requires `source_id` in identity, and
`SourceBoundary` has one member. Mission 1.48 tried to make two observations
disagree on one Claim and could not, for three reasons — `direction` is
proposition identity, the only implemented interpreter hard-codes
`EvidenceDirection.SUPPORTS`, and **all 43 Claims carry `source_id` in
proposition identity**.

The third reason is the same one. Corroboration needs two Evidence rows on one
Claim; contradiction needs two Evidence rows on one Claim; source attribution in
proposition identity forbids both. **One identity decision closes both roads out
of the B-2 baseline.**

Mission 1.48 also established, on non-persisted fixtures through the real
aggregator, that none of this is an arithmetic problem: a SUPPORTS row and a
CONTRADICTS row on one claim id produce contradiction strength 0.5 and conflict
mass 0.3, with all four masses summing to 1.0. The machinery works and has never
been reached.

The question this ADR answers is therefore not *how do we make the aggregator
produce a different number*. It is: **when the system wishes to assert that a
metric satisfies a condition, rather than that a source reported it, what kind of
Claim is that?**

## Decision

**A source-independent proposition is an `INFERRED` Claim.** Existing `OBSERVED`
Claims are unchanged and become its inputs.

No new `ClaimType` member. No subtype. No schema migration. No change to
`proposition_key`, to `SourceBoundary`, or to any existing Claim.

The decision was available all along, and the repository had already written it
down. `claim-epistemic-semantics-v1.md` §4 defines `INFERRED` as a claim that

> **asserts something about the world that the measurement is evidence for, and
> that the source did not itself report.**

That is the source-independent proposition, verbatim, written in Mission 1.13
several missions before anything needed it.

## Why this is not a model-generated claim

The obvious objection is that `INFERRED` sounds like something an LLM produces.
It does not, and the taxonomy separates the two ideas twice over.

**By type.** `INFERRED` is *derived analytically from one or more observations*.
`PREDICTED` is *a model-generated estimate*. The model-associated type is
`PREDICTED`.

**By axis.** `claim_type` is the epistemic category; `interpretation_kind` is the
procedure, `DETERMINISTIC` or `MODEL_DERIVED`. Migration 0016's CHECK constraint
ties `interpretation_kind` to the presence of a `model_version` — **not** to
`claim_type`. The axes are orthogonal by construction, and the constraint says so
in SQL rather than in prose.

And the semantics document states the consequence outright: *"A deterministic
extractor can produce an `INFERRED`-type claim, and an LLM can produce an
`OBSERVED`-type one."*

So `INFERRED` + `interpretation_kind = DETERMINISTIC` is representable in the
current schema **today**, with no migration. It has simply never been written:
all 43 live Claims are `OBSERVED`, all 43 are `DETERMINISTIC`, and none carries a
`model_version`.

## Why it is not an OBSERVED Claim

This is the alternative that would have been most convenient, and the repository
refutes it in one sentence written long before the question arose:

> **An `OBSERVED` claim that should have been `INFERRED` is a fabrication with a
> citation attached.**

A cross-source OBSERVED convergence Claim would assert a proposition that no
single source observed, while carrying every source's citation. That is not a
milder version of an inference; it is worse than one, because the citations make
it look directly supported. §4 names the same failure from the other end: without
the assumption written down, *"the same sentence is an `OBSERVED` claim that
quietly dropped its attribution."*

The test §2 set was whether something can be `OBSERVED` if no single source
observed that exact proposition. The answer is no, and it must not be answered by
implementation convenience.

**`source_id` therefore stays proposition identity for `OBSERVED`.** For an
OBSERVED claim the attribution *is* the claim (Mission 1.38). Removing it would
not merge two Claims about one fact — it would rewrite what all 43 existing
Claims mean.

## Why a new Claim type is unnecessary

A `DETERMINISTIC_MEASUREMENT` type is semantically sound and solves a solved
problem. The distinction it would encode — deterministic derivation versus model
inference — is exactly what `interpretation_kind` already carries, on an axis
orthogonal to `claim_type`.

Adding a sixth member would put one distinction in two places, and `ClaimType` is
a closed enum whose amendment requires a new ontology version and its own ADR.
**Two fields answering one question eventually disagree** — the defect Mission
1.13 fixed by dropping `evidence.claim_type`, and the one Mission 1.42a avoided
by refusing a second reviewer-confidence field.

## Why "leave it unimplemented" was rejected

This alternative was taken seriously, because epistemic conservatism is a real
virtue here and §2 forbade dismissing it merely because the aggregator could not
otherwise be calibrated.

It is rejected for a different reason: **it is not actually the conservative
option.** The `INFERRED` layer is already defined in the ontology, in the
generated contract, and in the epistemic semantics document. Choosing absence
does not decline to build something new; it leaves a defined capability
permanently unbuilt while the system keeps producing propositions that can
neither corroborate nor contradict.

And it has a cost that must be stated rather than hidden: the system would remain
unable to say that two sources disagree — the one signal that tells an operator
to go and look.

## The two-layer model

    Layer 1  SOURCE-ATTRIBUTED OBSERVED FACTS
             "Source A reported 110."   "Source B reported 90."
             source_id IS proposition identity
                            |
                   deterministic evaluation
                            |
    Layer 2  SOURCE-INDEPENDENT INFERRED PROPOSITIONS
             "M >= 100 at T, under definition D and unit U."
             source_id is WITNESS PROVENANCE
             A SUPPORTS · B CONTRADICTS

Layer 1 is untouched and is what the system already has. Layer 2 is additive.

## Identity, for the source-independent layer only

Nothing below applies retroactively to `OBSERVED` Claims.

**Proposition identity:** `claim_type`, `proposition`, `canonical_subject_id`,
`metric_definition_id`, `time_bound`, `population_or_geography`, `unit`,
`threshold_operator`, `threshold_value`.

**Witness provenance:** `source_id`, `resource_id`, `source_native_metric_id`,
`source_native_subject_id`, `measurement_value`, `measurement_timestamp`,
`methodology_version`, `record_locator`.

Three exclusions carry the weight.

**The measurement value is not identity.** If it were, 110 from source A and 105
from source B would produce two different Claims — Mission 1.48's failure
reproduced one layer up. The value is what a witness reports; the threshold is
what the Claim asserts.

**`source_id` is not identity here.** A proposition about the phenomenon cannot
be keyed by publisher, or two sources could never share it.

**Direction is not identity.** `SUPPORTS` and `CONTRADICTS` are Evidence
direction relative to a fixed proposition. This is the precise inversion of the
OBSERVED layer, where Mission 1.48 found `direction` *is* identity — and it is
why the same measurement stream that cannot contradict at Layer 1 can contradict
at Layer 2.

**Source independence of the proposition is never provenance loss.** Every
witness keeps `source_id`, and the full chain Evidence → Signal → signal_inputs →
NormalizedRecord → RawRecord → Source remains intact. A rendered Claim may read
*"M >= 100"*, and inspection must still show *supported by source A's measurement
110, contradicted by source B's measurement 90*.

## Two gates, and neither implies the other

**Measurement equivalence** must be established over metric definition, subject,
time, population, geography, unit, adjustment and methodology semantics *before*
a measurement may attach to a Claim.

**Independence** is a separate question, evaluated on Evidence provenance.

A source can be independent and measure something different, in which case its
disagreement is not disagreement (Mission 1.46's midyear *de facto* against
1 January *usually resident* population). A source can measure exactly the same
thing and be a republication, in which case its agreement is not corroboration
(Mission 1.46's FRED). **Both gates are required.**

Independence stays out of Claim identity: a proposition must not become a
different proposition because a reviewer learned something about provenance,
which is a fact about our knowledge rather than about the world.

## Reliability is unaffected, and the reason resolves an apparent conflict

Claim **identity** and Evidence reliability **scope** are different things.

The Claim's proposition is source-independent. The Evidence attached to it is
still a particular source's measurement, and reliability still asks *how
dependably does this source's measurement support this kind of proposition*. That
question remains source-relative, so the five-part scope — `source_id`,
`resource_id`, `record_kind_id`, `claim_type`, `proposition_kind` — is unchanged.

A source-independent `proposition_kind` and `claim_type = INFERRED` differ from
every existing scope, so every such Evidence row resolves
`NO_APPLICABLE_ASSESSMENT` until a human reviews it. **No value is inherited by
proposition similarity.**

**Measurement reliability and derivation validity must never be multiplied.**
Whether the source's 110 is dependable is a human judgement against documentary
basis; whether 110 entails `>= 100` is exact. There is no coefficient combining
them, and inventing one would let a sound derivation look doubtful because its
input is uncertain — which the four-mass decomposition already represents
correctly through uncertainty mass.

## Thresholds must be preregistered to be calibration-eligible

The threshold is *ours*, not the source's, which is the cost Mission 1.48
recorded when it selected `THRESHOLD_STATE`.

`PREREGISTERED`, `SOURCE_NATIVE` and `EXTERNAL_NORM` are calibration-eligible.
`POST_HOC` and `UNKNOWN` are not. A post-hoc threshold may still produce a Claim
— the proposition is not false because its bound was chosen late — but it may not
serve as a calibration case, because a threshold picked to make a case work
measures the analyst. `UNKNOWN` is ineligible rather than assumed preregistered:
uncertainty is never permission.

## Consequences

- **Purely additive.** All 43 Claims, 44 revisions and 57 Evidence rows keep
  their proposition identities and their meaning. Zero migrations are
  recommended, now or later, that would change what a historical Claim says.
- **`validate_claims.py` stays untouched.** It fails the build on any non-OBSERVED
  `ClaimType` access in the interpretation package, and that guard is what keeps
  the OBSERVED contract narrow. Source-independent evaluation therefore belongs in
  a **separate evaluator**, not in the interpreter framework. A guard removed to
  let new work through is a guard that never was.
- **Cross-source OBSERVED convergence is no longer needed** for world-level
  propositions. Mission 1.47's finding that the contract structurally refuses
  them becomes a feature rather than a gap. `SourceBoundary` is not widened.
- **Contradiction becomes reachable**, on fixtures today and on real data once
  Layer 2 exists: one Claim, `M >= 100`, with 110 supporting and 90
  contradicting, produces contradiction strength 0.5 and conflict mass 0.3
  through the real aggregator.
- **Two independent supports become reachable**: 110 and 105 from independent
  lineages form two support groups with strength 0.8 against a strongest member
  of 0.6 — the first shape in this repository that would make the full aggregator
  differ from the B-2 baseline.
- **Nothing is implemented.** No INFERRED Claim exists, no evaluator is written,
  and no Claim, Evidence or ClaimType member was created or modified.

## Alternatives rejected

| Alternative | Verdict | Why |
|---|---|---|
| Cross-source OBSERVED convergence | Rejected | Would assert what no source observed while carrying every source's citation — *a fabrication with a citation attached* |
| A new deterministic-measurement `ClaimType` | Unnecessary | `interpretation_kind` already carries the deterministic/model axis, orthogonally |
| Leave source-independent propositions unimplemented | Rejected | Not the conservative option: the layer is already defined, and absence has an unstated cost |
| Remove `source_id` from OBSERVED identity | Refused outright | Would rewrite the meaning of all 43 existing Claims |

## Open questions

These belong to the implementation contract, not to this decision.

- **Where does the reasoning step live?** `ClaimDraft.rationale` exists, is wired
  through `_persist_one`, and lands in `research.claims.origin_detail`. It is
  populated on all 43 Claims — with a *provenance* sentence such as *"Restated
  from signal `<id>` (content-request-change@1.0.0)."*, because an OBSERVED
  restatement has no reasoning step. Whether a reasoning step may share a column
  named `origin_detail` is the Mission 1.15.4 shape: one field answering a
  question that is two.
- **Does Evidence attach directly, or is a derivation relation required?** The
  preferred shape links the Signal and its OBSERVED provenance to the
  source-independent Claim; a `ClaimRelation` is more machinery than the case
  needs today.
- **How is a threshold's preregistration status recorded and enforced?**
- **Does the derivation rule need its own registry and versioning**, as
  interpreters and extractors have?
