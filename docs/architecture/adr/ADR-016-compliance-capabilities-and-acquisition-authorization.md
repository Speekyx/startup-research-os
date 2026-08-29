# ADR-016 — Compliance capabilities and acquisition authorization

**Status:** Accepted
**Date:** 2026-08-29
**Mission:** Sprint 1 / Mission 1.4
**Supersedes:** nothing. Extends [ADR-013](ADR-013-source-registry-governance.md)
**Related:** [`acquisition-authorization-v1.md`](../../data/acquisition-authorization-v1.md),
[`source-condition-gap-analysis-v1.md`](../../data/source-condition-gap-analysis-v1.md),
migration `0007_condition_verification`

---

## Context

ADR-013 built a gate that had never opened. Every source was blocked, so the
question *how does a condition get cleared* had never had to be answered.

Mission 1.3 made it urgent. Three sources reached `APPROVED_WITH_CONDITIONS`
with nine conditions between them, and migration 0006 gave each condition a row
with a `satisfied` boolean. The boolean could hold a state; nothing could
legitimately put a state in it.

That left a specific and dangerous shape. The one remaining step between a
reviewed approval and a collector was a boolean somebody could set. It could be
set by a migration, by an `UPDATE`, by a test fixture, or by a well-meaning
developer who had read the condition and decided it was fine — and none of those
would leave a trace saying what was actually checked.

Three further problems were visible in the condition records themselves:

- **Seven of the nine conditions are claims about a collector**, and no
  collector exists. "The collector requests only datasets whose recorded licence
  is CC-BY 4.0 or ODbL" cannot be observed when nothing requests anything.
- **All three sources require attribution, and each requires something
  different** — credit and change-indication, a DOI and an access date, one
  exact sentence. Attribution as a string in a template would have to be three
  templates, and would be lost by the first transformation that did not know to
  copy it.
- **All three republish material they do not own.** A source-level approval read
  as a resource-level one would authorise the World Bank Microdata Library, the
  Eurostat trade carve-outs and every copyrighted FRED series.

## Decision

### 1. A condition is cleared by a verifier, and by nothing else

`registry.source_condition_verifications` is an append-only log recording which
condition, which verifier, at which version, when, the result, why, and what was
inspected. `source_review_conditions.satisfied` remains the gate's input and is
synced from the latest verification.

A `BEFORE` trigger refuses to set `satisfied = TRUE` with no `SATISFIED`
verification record for that condition — whoever issues the `UPDATE`, from
whatever client. Clearing a condition back to false is deliberately unguarded:
failing closed must never need permission.

### 2. Four verification results, never a boolean

`SATISFIED` · `UNSATISFIED` · `UNKNOWN` · `NOT_APPLICABLE`. Only the first
clears a condition. `UNKNOWN` — the verifier could not run — blocks exactly as a
failure does, and is kept distinct because one is a bug and the other is missing
work.

### 3. Capabilities are checked, not registered

A capability's entry in the registry is not evidence that it exists. Its
conformance check runs the real gate against the source's real configuration and
asserts, for every case the review evidence names, that the gate answers
correctly — including denying the unknown case and **allowing its own control
case**, so a filter that denies everything fails rather than passing every
denial assertion.

### 4. Obligations are configuration; mechanisms are code

`docs/data/source-compliance-v1.json` holds the parameters — exact notices,
allowlists, enumerated exclusions, minimisation profiles. The compliance package
contains no branch on a source id.

Where terms prescribe wording, it is stored verbatim and rendered unmodified,
and a validator asserts that every exact notice appears in the evidence record
that established it. Where wording is *not* in the retrieved evidence — the
Eurostat modification disclaimer — it is a required **supplied** element and
rendering refuses without it. Composing it would have been the opposite of
preserving a required notice.

### 5. Attribution is an obligation that propagates

A first-class model with a closed `AttributionElement` enum, a renderer that
raises rather than dropping a required element, and an `AttributedArtifact`
whose `derive` carries obligations forward and has no parameter that removes
one. Combining artefacts unions their obligations.

### 6. Resources are authorised individually, and fail closed

Six rule kinds, each demanded by an actual condition, and every one of them
denies rather than permits. `ResourceContentOrigin.UNKNOWN` is refused wherever
licensing scope matters, because an unexamined resource is not one known to be
covered.

### 7. A collector receives an authorization or nothing

`AcquisitionAuthorizationContext` carries the approved access paths, the
resource scope, the resolved retention, the attribution obligation, the
minimisation profile and the verification snapshot. `build_authorization` runs
the canonical gate and raises when it does not pass.

That is the enforcement mechanism: **not a flag the collector is asked to check,
but the absence of the object it needs.**

### 8. Eligible, enabled and implemented are three facts

Making sources eligible exposed that the planner would have dispatched
`acquire.collect` with nothing behind it. Acquisition now has two gates —
`SOURCE-REGISTRY-GATE` and `NO-COLLECTOR-IMPLEMENTED` — cleared by different
work, and `sros-source enable` refuses a source with no implemented collector.

## Alternatives considered

**Let a migration or an operator set `satisfied`.** Rejected. It is the whole
attack surface of the governance model, and it leaves no record of what was
checked. The trigger costs fifteen lines.

**Collapse `UNKNOWN` into `UNSATISFIED`.** Rejected. "The verifier failed" and
"there is no verifier" are different problems with different fixes, and
collapsing them would hide the second behind the first — permanently, since both
block and nobody would look further.

**Write a rule DSL for resource exclusions.** Rejected. A general expression
grammar in configuration is exactly where a vague legal sentence gets encoded as
a boolean, which the whole review model exists to prevent. Six named rule kinds,
each traceable to a condition, keep the configuration checkable against the
document it came from.

**Make the capability verifier assert that a collector obeyed.** Not possible,
and pretending otherwise would have been the dishonest option. The contract
defines `CAPABILITY` as *implemented and enabled*; the collector guarantee is
structural and becomes observed only when Mission 1.5 adds a conformance test.
The limitation is written into the gap analysis, this ADR and the verification
reasons themselves rather than being quietly absorbed.

**Keep the rendered catalog showing live eligibility.** Rejected. A committed,
CI-checked file whose contents depend on whether the machine that generated it
had a credential configured would fail for reasons unrelated to the change under
review. The catalog shows the catalog view and says so.

**Widen the Eurostat geography allowlist to candidate countries.** Rejected.
The terms permit their data; the set changes and the copyright notice does not
enumerate it. The allowlist is EU-27 plus EFTA — stricter than required, never
more permissive — and the omission is recorded so nobody mistakes it for an
oversight.

## Consequences

**Good.**

- The last manual step between a review and a collector is gone, and the
  database enforces its absence.
- Two sources are collector-eligible with recorded, re-runnable reasons, and
  re-verification can take them back out.
- Attribution, licensing scope and credentials are enforced by objects rather
  than remembered by whoever writes the first collector.
- A collector cannot start without an authorization, and cannot obtain one for
  an ineligible source.
- The eligibility answer became environment-dependent, which surfaced a class of
  tests that were asserting a moment rather than a property. Those now derive
  their expectations.

**Costs and risks.**

- **A capability verification is weaker than its condition's wording.** The
  conditions talk about a collector; the verifications talk about a gate. The
  gap is documented in three places and closes in Mission 1.5, and until then a
  reader who skims could over-read a `SATISFIED`.
- **Two views of eligibility now exist** and can legitimately disagree. Each
  command says which it shows; a reader who ignores that will be confused.
- **A satisfied condition can go stale.** A capability removed after
  verification leaves the boolean true until something re-verifies, which is why
  CI runs `sros-source verify --apply` rather than trusting recorded state.
- The compliance configuration is another hand-edited governance file that can
  drift from the reviews it was derived from. The validator checks the review
  version and the exact notices; it cannot check judgement.
