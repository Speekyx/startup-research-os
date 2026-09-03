# ADR-035 — Proposition identity and witness identity are different things

**Status:** Accepted
**Date:** 2026-09-03
**Mission:** 1.39
**Supersedes:** nothing. **Amends:** nothing. It adds a distinction the Claim
model did not previously make.

---

## Context

Mission 1.37 measured that every Claim in the deployment has exactly one
Evidence row, so the aggregation layer had never aggregated. Mission 1.38 found
the cause: every implemented interpretation is a one-to-one restatement of one
Signal, because each template's proposition facts contain the measurement's own
identity. Two Signals could converge only by being the same measurement.

The persistence layer was never the blocker — `_persist_one` looks a draft up by
`proposition_key` and attaches Evidence to whatever Claim it finds, and the
aggregation framework's §1 asks *"Given several Evidence records bearing on one
Claim"*.

## Decision

**A fact that identifies a proposition and a fact that identifies the
observation witnessing it are different kinds of fact, and a convergence-enabled
proposition kind must say which is which.**

The test, applied field by field and recorded per field:

> If changing field F changes **what** the Claim asserts, F is proposition
> identity. If changing F only changes **which** observation witnesses the same
> assertion, F may be witness identity.

`PropositionConvergenceContract` declares both sets. `proposition_key` is
computed over the identity facts alone; the witness facts are retained on the
Signal, reachable through the Evidence, and hashed into a separate `witness_key`
that the duplicate-witness guard uses.

## Why multiple observations can support one Claim without changing what it means

Because the broader proposition is a **different proposition**, not a weakened
one. The detailed TED claim asserts something about notices `{N1,N2,N3}`; the
convergent claim asserts that the source published *at least one bounded set* of
notices in a classification division whose stated amounts differ. The second is
**entailed by** the first and asserts less.

Two disjoint cohorts each entail it, and neither is privileged. Adding the second
witness does not change the assertion — which is exactly why it does not create a
Claim revision.

## Why witness identifiers are not necessarily proposition identifiers

The existing TED template argues, correctly, that *"a proposition that cannot say
WHICH notices is not checkable"*. The answer is that **checkability moves rather
than disappearing**. A reader can still recover exactly which notices, through
Evidence → Signal → `signal_inputs` → `normalized_records`. What they cannot do
is read the cohort off the Claim's identity — and that is the point, because a
second cohort must be able to witness the same assertion.

Information is not discarded when it stops being an identity. It stops being an
identity.

## Why source attribution remains essential for OBSERVED claims

`claim-epistemic-semantics-v1.md` §3: an `OBSERVED` claim asserts what a source
reported, attributed. *"Wikimedia counted X"* and *"TED reported Z"* are
different propositions with different falsifiers, and rendering them into similar
English does not make them one.

So `source_id` is **always** proposition identity, enforced in the contract's
constructor rather than left to each author. The V1 source boundary is
`SAME_SOURCE_AND_RESOURCE` and no cross-source member exists in the enum — an
enum member nobody may pass is an invitation.

## Why convergence does not imply independence

Two witnesses of one proposition are two observations. They may still share a
publisher, a collection mechanism, a methodology and the population the records
were drawn from.

`ObservationOverlap` (`DISJOINT` / `OVERLAPPING` / `UNESTABLISHED`) and
`EvidenceIndependenceState` (`KNOWN_INDEPENDENT` / `KNOWN_DEPENDENT` /
`UNKNOWN`) are **different axes** and deliberately share no member name. The
first draft of `ObservationOverlap` used `UNKNOWN`; the test asserting the two
vocabularies are disjoint caught the collision, and the member was renamed. Two
vocabularies sharing a member name is how a mapping between them gets written by
accident.

`independence_state` stays `UNKNOWN` on convergent Evidence, and the
conservative unknown-provenance collapse remains authoritative: two witnesses
raise observed volume, not evidence strength.

## Why existential observation is different from population generalisation

The convergent proposition establishes that **at least one** bounded set exists.
It does not establish how many, what proportion of the division they are, whether
the relation is typical, any trend, or anything commercial. The contract requires
`does_not_establish` to be non-empty for exactly this reason: prevalence is what
a reader supplies when nobody said otherwise, and the statement's own wording
carries *"at least one bounded set"* so a summariser cannot drop the bound.

Multiple witnesses of an existential remain multiple witnesses of the same
existential. They do not turn it into a prevalence claim, and the aggregation
arithmetic agrees — with independence `UNKNOWN`, both collapse into one group.

## Consequences

- **Nothing historical moved.** No existing template changed, no existing
  proposition key changed, and no historical proposition kind gained a contract.
  Convergence is opt-in per kind.
- **The convergent interpreter is not wired into the production job.** No Signal
  in this deployment can witness two Claims, so §19's double-counting boundary is
  enforced by absence rather than by a rule. Running it against live records is a
  later mission's decision.
- **`max(members)` can now receive more than one member**, demonstrated through
  the real repository and the real aggregator against synthetic fixtures in a
  disposable workspace.
- **The live corpus is unchanged**, and the calibration feasibility audit still
  reports zero multi-Evidence Claims. The architecture is capable; the corpus has
  not used it.

## Alternatives rejected

**Remove `notice_ids` from the existing proposition kind.** Rejected: it would
change what 28 historical claims assert, and Mission 1.39 §2 forbids it. A
different proposition needs a different kind.

**Remove `source_id`.** Rejected on the epistemics, not on compatibility. See
above.

**Decide convergence by similarity.** Rejected by §13 and by D-12 being open. The
qualification predicate is deterministic over persisted bounded facts, and
`SAME_PROBLEM_FAMILY` answers a different question and stays PARKED.
