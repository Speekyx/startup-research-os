# ADR-038 — A refusal is not a derivation of a Claim, and needs its own record

**Status:** Accepted
**Date:** 2026-09-05
**Mission:** 1.53
**Supersedes:** nothing. **Amends:** nothing. It closes the gap Mission 1.52
found in ADR-037's implementation, without altering ADR-037's decisions.

---

## Context

ADR-037 decided that a `NOT_APPLICABLE` or `UNKNOWN` evaluation produces a
derivation record and no Evidence row, so that a refusal is auditable rather
than invisible. Migration 0034 built the table meant to hold it.

Mission 1.52 built the evaluator and discovered the two halves cannot both be
satisfied. Re-proved here in a disposable workspace rather than quoted:

    INFERRED claim with no Evidence      REFUSED  23514  require_evidence_for_generated_claim
    HYPOTHESIS claim with no Evidence    ACCEPTED        (the control)
    derivation with NULL revision id     REFUSED  23502  migration 0034's NOT NULL

Both refusals are individually correct. The exemption list is what stops a
machine storing an assertion nothing supports; the `NOT NULL` is what stops a
later derivation rewriting the reasoning behind an earlier revision. Jointly they
leave a refusal nowhere to live, because a derivation must name a revision, a
revision requires a Claim, and a generated `INFERRED` Claim requires Evidence
that a refusal by definition does not produce.

**Migration 0034 already anticipated refusals.** Its
`claim_derivations_threshold_required_check` makes the threshold registration
optional *exactly* for `NOT_APPLICABLE` and `UNKNOWN`, and its result CHECK
admits all four values. Two constraints written in one migration disagree with
each other. That is the finding, not a tie-breaker.

## Decision

**A refusal is recorded in its own append-only entity, keyed on the INPUT
witness, the CANDIDATE TARGET proposition, the derivation rule version and the
reviewed equivalence basis.** It names no ClaimRevision, creates no Claim,
produces no Evidence, and requires no change to `research.claim_derivations`, to
`research.require_evidence_for_generated_claim`, or to any existing schema.

Proposed name `research.proposition_evaluation_refusals`. **No migration was
created**; the schema is frozen here and implemented by a later mission.

**The candidate target proposition is stored as a key and its exact preimage**,
in the vocabulary `research.claims.proposition_facts` already uses — measured:
all 43 live Claims carry both, and the discriminator key is `proposition`, which
is exactly what the evaluator already emits.

**Idempotency key:** `(workspace_id, input_signal_id, target_proposition_key,
derivation_rule_version, semantic_equivalence_basis_id)`, every column
`NOT NULL`.

## Why not a nullable `claim_revision_id`

This was the obvious repair, and it fails on a fact that only a live probe
produces.

`claim_derivations_identity_key` is `UNIQUE (workspace_id, claim_revision_id,
input_signal_id, derivation_rule_version)`, and PostgreSQL treats NULLs as
distinct. A probe on a temp table mirroring that constraint on PostgreSQL 16.4
**accepted three identical rows** with `claim_revision_id` NULL, and refused the
duplicate as soon as the column was populated. **Making the column nullable
silently removes the table's only idempotency guarantee from precisely the rows
the change exists to add**, and nothing reports it.

The second failure is quieter and worse. `claim_derivations` identifies its
proposition **only through** `claim_revision_id`; it carries no descriptor of its
own. With that column NULL, the row cannot say what was refused. Repairing that
means adding a proposition key, a preimage, a reason code, a second partial
unique index and three conditional CHECKs — Option A inside a table whose name
says it is about actual ClaimRevisions.

So the choice is not one table against two. It is one honest table against one
table meaning two things with two identity keys.

## Why not the interpretation-run logs

Measured, not recalled: all 12 `claim_interpretation_runs` carry a populated
`expires_at`, and `claim_interpretation_inputs` references them
`ON DELETE CASCADE`. A refusal filed there disappears on schedule. Retention was
not redesigned to rescue it, because an execution log expiring is correct
behaviour for an execution log.

## Why a hash alone will not do

A `proposition_key` with no preimage identifies a proposition nobody can read,
and unlike a Claim there is no row elsewhere to recover the facts from. Storing
both makes the key **verifiable rather than trusted**: a reader recomputes
`proposition_key(target_proposition_facts)` and compares.

This is also why a candidate-proposition registry was rejected. A durable
non-Claim target entity is Claims before Claims: it would need identity,
lifecycle and governance of its own, and the first question anyone would ask is
how it differs from a Claim.

## Why the threshold registration cannot identify the target

Three of the seven live reason codes refuse at gate 1, **before the registration
is consulted**. A representation resting on the registration would fail exactly
on the most common refusals.

The registration is therefore nullable, and conditionally required: a refusal
whose reason code shows it reached the registration gate must name the
registration it judged. A gate-1 refusal may carry one — the evaluator currently
passes it — and is never required to.

## Why the equivalence basis can be `NOT NULL`

`SemanticEquivalenceDecision` refuses a blank `basis_id` for **every** verdict,
including `UNKNOWN`. So no evaluation can occur without one, no fake identifier
needs inventing, and the identity key avoids the NULL trap above by construction.

**The bound this puts on the store is worth stating.** The evaluator only refuses
pairs somebody has already reviewed. A pair nobody reviewed produces no decision
object, so `evaluate` is never called and no refusal exists. The store answers
*what did we try and decline*; it can never answer *what did we never consider*.

## Why a changed basis is a new row

The reviewed basis is an input to gate 1 and the first thing the evaluator reads.
Changing it changes what was evaluated, so it is a new historical evaluation
rather than an update to an old one. Recording it as the same refusal would mean
overwriting the reasoning that stood while the old basis stood.

The cost is stated rather than hidden: one Signal-target pair can accumulate
several refusal rows over time. That is what an append-only audit is, and the
number of rows measures nothing epistemic.

## Append-only, and what happens when UNKNOWN later becomes SUPPORTS

Nothing happens to the refusal.

    T0  basis B1  ->  UNKNOWN     ->  refusal row U
    T1  basis B2  ->  SUPPORTS    ->  Claim, ClaimRevision, claim_derivation, Evidence
        U is untouched

`U` is a true historical statement: under basis B1, this system could not
establish that the Signal bears on the proposition. A later basis does not make
that false. There is **no supersession column**, because no consumer needs one —
each row names its rule version and basis, so *which reasoning stood when* is
answerable from the rows and their timestamps, and a supersession flag would
require somebody to decide what supersedes what.

## A refusal is not a failure

`NOT_APPLICABLE` and `UNKNOWN` are domain findings. A database error, a missing
contract object or an unexpected exception is not, and must never be filed here.
`nlp.signal_derivation_runs` and `research.claim_interpretation_runs` already
hold execution records. The result CHECK is a partial guard; the real enforcement
is that the persistence command accepts an `EvaluationOutcome` and nothing else,
so an exception has no shape to be written as.

## Consequences

- **`research.claim_derivations` keeps one clean meaning**: every row names a
  real ClaimRevision. The invariant is preserved rather than weakened.
- **The evidence-requirement trigger needs no exemption**, because no Claim is
  created. This is the decisive practical advantage: the alternative designs all
  end at a request to exempt `INFERRED`.
- **One question becomes directly queryable** — *show me every evaluation attempt
  that did not become Evidence* is one SELECT, not a diff of two tables.
- **The design is generic**, because the descriptor is the fact vocabulary all
  seven live proposition kinds already use. Only the optional threshold
  registration is family-specific, and another family simply never uses it.
- **The evaluator is unchanged.** The directional and refusal paths commit
  independently, and a refusal write cannot create a Claim, Evidence or a
  threshold mutation, because it has no foreign key to any of them.
- **Nothing was created.** No migration, no table, no Claim, no Evidence, no
  derivation row. Every counter is unchanged.

## Alternatives rejected

- **Nullable `claim_revision_id`** — refuted above on idempotency and on target
  auditability, both measured.
- **Interpretation-run logs** — refuted on live retention.
- **A candidate-proposition registry** — Claims before Claims.
- **Threshold registration as the target identity** — fails on gate-1 refusals.
- **A NEUTRAL Evidence row** — `EvidenceDirection.NEUTRAL` exists, and means the
  observation bears on the Claim without bearing either way. A refusal says we
  could not establish that it bears at all. Mapping one onto the other would make
  a refusal counted and weightless: visible in the counts, invisible in the
  numbers.

## Open questions

- **`TARGET_DESCRIPTOR_VERSION_DELIBERATELY_ABSENT`.** Mission 1.53's brief asked
  for a canonical schema version on the descriptor. It is not included, because
  `derivation_rule_version` already pins which fact set was emitted —
  `target_proposition_facts()` lives in the rule module, so a change to the fact
  vocabulary *is* a rule-version change, and a second version field would be a
  second authority for one fact. If the vocabulary ever changed without a
  rule-version bump, a reader could not tell which shape a descriptor uses; the
  implementation mission should assert that coupling with a test rather than add
  the column. **Recorded as an operator-reviewable deviation rather than settled.**
- **Whether a gate-1 refusal should carry the threshold registration it never
  consulted.** The constraint permits it and never requires it. Deciding it would
  have meant changing the evaluator, which Mission 1.53 was told not to do.
- **Policy D remains decided and unimplemented.** A rule-version disagreement with
  standing Evidence is reported for operator review, and no reporter exists.
