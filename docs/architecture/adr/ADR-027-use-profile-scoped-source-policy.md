# ADR-027 — Use-Profile-Scoped Source Policy and Authorization

**Status:** Accepted · **Date:** 2026-08-31 · **Mission:** Sprint 1 / 1.15.5
**Supersedes:** nothing. **Amends:** the eligibility gate (Mission 1.0 §21,
ADR-013) and the authorization contract (Mission 1.4, ADR-016).

---

## Context

### The problem, stated precisely

Every policy review in this registry has always answered a question about a
**use**. The catalog said so at the top, in prose, and every review inherited it:

> *"Automated collection of public content by Startup Research OS, a
> **COMMERCIAL multi-tenant SaaS**, for storage, derived analytics and LLM
> processing to produce opportunity intelligence. Every assessment below is
> scoped to that use. An assessment does not transfer to non-commercial or
> academic use…"*

`PolicyReview.assessed_use_case` is a **required** field, and the model's own
error message says why: *"an approval that does not say what it approved cannot
be relied on for anything else."*

**So the use case was persisted. What it never had was an identity.** It was
prose — it could not be compared, required or matched, and the eligibility gate
never saw it. `evaluate_eligibility(source)` knew the source and nothing about
what was being done with it.

This corrects Mission 1.15.4's framing, which said the model "never records" the
use case. It records it; it could not *use* it.

### What made it visible

TED-EU. The Publications Office publishes explicit intended-use documentation
for two official query routes — analysis, reuse, application integration,
commercial organisations building added-value services — while the sui generis
database-right question over the corpus (H-36) remains open for extraction at
corpus scale.

That produces two honest answers at once:

```text
ted-eu + commercial multi-tenant SaaS + corpus mirroring   -> REQUIRES_REVIEW
ted-eu + local single-operator research + bounded queries  -> defensible
```

The registry could store one. Storing the second would have made the first
untrue for every consumer that reads `approval_state` — the eligibility view,
the validators, the portfolio, the coverage tables — and it is the first that
governs a future public deployment.

### What was rejected before this ADR was written

Mission 1.15.4 examined three ways to avoid the change and rejected all of them
(`route-scoped-source-authorization-gap-v1.md` §4):

| Rejected | Why |
|---|---|
| Flip the verdict, let conditions hold the line | Conditions are prose next to a boolean, and the boolean is what code reads. Every consumer would report TED approving for the unresolved commercial use — the silent migration to production authorization |
| Two current reviews with no discriminator | Two answers to one question; `source.review` becomes a coin-flip for every caller |
| Encode the profile as a verifiable condition | Conditions gate an approving source, they do not create approval. Still needs the flip |

## Decision

**A policy review's subject is a first-class, registered, versioned identity, and
the gate requires it.**

### 1. `AssessedUseProfile`

A registered entity — not a closed enum — carrying the facts a reviewer needs in
order to know what they are approving: deployment, operator scope, public
access, external customers, raw redistribution, raw resale, customer-facing
source access, derived internal analysis, commercial purpose, model inference,
model training, embeddings, personal-data posture.

A **registry** rather than an enum because nothing branches exhaustively on it;
it is compared. That is `docs/CLAUDE.md` §Taxonomies applied unchanged, and it
means adding a profile is a governance act rather than a migration.

Ids carry their semantic version — `local-private-research-v1` — so a changed
meaning is a changed identity and no existing review silently follows it.

### 2. Two profiles, and no more

| Id | What it is |
|---|---|
| `commercial-multi-tenant-research-v1` | What every review from Mission 1.0 to 1.15.4 **actually assessed**. Also the profile a future public commercial deployment must satisfy. The **widest** profile |
| `local-private-research-v1` | The system's actual current use: local, single operator, no public access, no redistribution, no resale, minimised storage, official routes only |

**`PUBLIC_COMMERCIAL_SERVICE` was not created as a third profile**, because it is
the first one under the name the historical prose already used. Two
near-identical profiles would be the premature proliferation §5 of the mission
warns against, and the cross-profile isolation property is demonstrated by the
two that exist.

**`commercial_purpose` is TRUE on both.** Running locally does not make the use
non-commercial — the research produced is used to launch commercial products —
so a commercial-use right still has to be granted by the source's own evidence.
This is the single easiest thing to get backwards and it is asserted by test.

### 3. Currentness is per `(source, profile)`

Each profile keeps its own append-only version line. Version 1 under a second
profile is a **first review of a new question**, not a duplicate of the first
review of the old one. The database constraint moved from
`UNIQUE (source_id, review_version)` to
`UNIQUE (source_id, assessed_use_profile, review_version)`, and the eligibility
view emits one row per `(source, profile)`.

### 4. The gate requires the profile, with no default

```python
evaluate_eligibility(source, use_profile_id, now, satisfied_conditions)
build_authorization(source, use_profile_id, config, ...)
verify_source(source, use_profile_id, config, ...)
```

Second positional, no default, in all three. **Fail closed:** a missing profile
raises, an unknown profile is refused, a profile with no review is refused, and
**none of them falls back** — not to another profile and not to the source's
historical verdict.

### 5. The runtime declares; it never infers

`SROS_USE_PROFILE=local-private-research-v1`, read at the entry point and passed
down. Never derived from an environment name, a host, a container, a user count
or the absence of billing.

**A profile is not a deployment environment.** `development` and `production`
say where code runs; a profile says what is being done with somebody else's
data. The same binary in the same container can be operated under either, and
Startup Research OS may run in development while evaluating what a public
commercial deployment would be permitted to do — deriving one from the other
would make that evaluation answer the wrong question.

There is **no default**, because the convenient default is the narrow local
profile, which is exactly the one an operator running a public service would
most want assumed for them.

### 6. `SourceRecord.review` survives, scoped and fenced

It keeps its meaning as **the current review under the legacy profile** — which
is what every document, validator and rendered catalog written before this ADR
was about, so every existing statement stays true.

It is **not an authorization input**, and an AST test asserts that
`eligibility.py`, `authorization.py` and `verification.py` never read it.
Reading it would be exactly the silent fallback to a global verdict this ADR
removes, and it is the easiest mistake to make here because `.review` reads more
naturally than `.review_for(profile)`.

### 7. The operational switch names its use

`registry.sources.collector_use_profile`, required whenever `collector_enabled`
is true. A switch with no stated scope is a switch that grants the widest one.

### 8. Compliance configuration is keyed by `(source, profile)`

A resource scope, an attribution obligation and a minimisation profile are
answers to *what may we do with this, for what*. Two profiles can legitimately
have different answers, and one must not borrow the other's.

## Historical migration

**Every existing review was attached to `commercial-multi-tenant-research-v1`.**

This is a **migration interpretation of the historical review scope, not a new
policy conclusion**, and it is not a guess: the catalog's own `assessed_use_case`
prose has said "a COMMERCIAL multi-tenant SaaS" on every review since Mission
1.0. The migration **canonicalises a sentence that was already there**.

No verdict, assessment, condition, open question, evidence row or review version
changed. The legacy distribution is asserted unchanged at
`APPROVED_WITH_CONDITIONS` 5, `REQUIRES_REVIEW` 13, `RESTRICTED` 8,
`PROHIBITED` 3.

**Review row ids keep the historical derivation for the legacy profile.** Ids
are deterministic surrogates, but rows hang off them — conditions, and the
condition *verifications* that record who checked what and when. Re-deriving
every id would orphan them, and deleting them to make the load tidy would
destroy the record the registry exists to keep. Only profiles that did not exist
before this ADR carry the profile in the key, and only to stop their version 1
colliding with the legacy one.

## Provenance

**No new provenance column was added, and no ADR-level decision was needed for
one.** The profile is carried on `AcquisitionAuthorizationContext`, which a
collection job holds while it runs, and `registry.source_policy_reviews` records
which review each verification was made against. *Under which profile was this
data collected* is answerable from the authorization the job held and the review
it was built from.

If retention ever removes the job record before the raw records it produced, that
answer becomes unreconstructible and a durable column on `RawRecord` becomes
necessary. **That is a real future decision and it is recorded here as one** —
adding a column later is cheap; adding it speculatively creates a second place
the profile can be wrong.

## Consequences

**Good.**

- A source can be blocked broadly and authorised narrowly, truthfully. TED is
  `REQUIRES_REVIEW` under the commercial profile and `APPROVED_WITH_CONDITIONS`
  under the local one, at the same time, without either being a lie.
- Twenty-nine approvals stopped answering an unrecorded question.
- Deploying publicly cannot silently inherit a local permission: it requests a
  profile nothing has approved, and the gate refuses **by name**.
- The rule that a permission obtained by describing a smaller product is a
  permission for a product we are not building is now **mechanical** rather than
  a sentence in a guide.

**Costs, and they are real.**

- It touches `evaluate_eligibility`, the most safety-critical function in the
  repository, and threads a required argument through the CLI, the collection
  job, the readiness reporter and every test that builds an authorization.
- The review surface multiplies per source. Two profiles is two reviews to keep
  current where there was one, and staleness now has to be tracked per profile.
- `SourceRecord.review` remaining legacy-scoped is a compromise. It is fenced by
  a structural test, and the fence is the only thing that makes it safe.

**Neutral.** Adding a profile is a governance act with an ADR, not a migration.
That friction is intended: a third profile should be hard enough to add that
somebody has to justify it.

## Alternatives rejected

| Alternative | Why not |
|---|---|
| Leave the gap; keep documenting it | Mission 1.15.4 did exactly that, and the second source needing two answers would have hit the same wall |
| Closed enum instead of a registry | Nothing branches exhaustively on a profile. `docs/CLAUDE.md` §Taxonomies says registries for extensible vocabularies, and an enum would force a migration for a governance decision |
| Free-text profile on the review | What the system already had. Prose cannot be required, compared or matched |
| Profile inferred from deployment environment | A governance fact derived from an infrastructural one. The same container can be operated under either profile, and the inference would be wrong exactly when it mattered |
| A "best verdict" rollup across profiles | §11. `RESTRICTED` under one profile and `APPROVED_WITH_CONDITIONS` under another does not make a source approved. Any summary must name the profile or say the answer is profile-dependent |
| Resource/route encoded in the profile id | §19. A profile answers *how and why*, a resource answers *which data*. `authorize_resource` already handles the second, correctly, below the gate |
