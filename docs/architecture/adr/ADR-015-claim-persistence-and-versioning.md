# ADR-015 — Claim persistence: stable identity, append-only revisions

- **Status:** Accepted
- **Date:** 2026-08-29
- **Deciders:** Implemented in Mission 1.2 under brief §24, §25, §29, §31
- **Supersedes:** none. Resolves **A-13**, opened by Mission 1.1
- **Related:** ADR-005 (tenancy), ADR-012 (row-level security), ADR-014
  (aggregation reference package);
  `docs/domain/opportunity-ontology-v2.1.md` §17, `docs/domain/claim-model-v1.md`

---

## Context

Mission 1.1 defined evidence aggregation around a Claim and then discovered the
system had none. `scoring.evidence` pointed at an Opportunity, the ontology
defined a claims *taxonomy* (`ClaimType`) and never a claim *entity*, and there
was no table, no id, and nothing for evidence to accumulate against.

That is A-13, and it is why the aggregation framework could be executable and
still unusable: the mathematics had no unit to operate on.

Three properties made the design non-obvious.

**Claims are edited.** A statement gets narrowed, clarified, split. The wording
is the thing a reader disputes, so it has to be improvable.

**Claims are evaluated.** An aggregation result is about a specific assertion.
If the assertion changes afterwards and nothing records that it did, the stored
result silently becomes a result about a different claim — and there is no way
to notice, because both the result and the claim look intact.

**Claims are tenant data, referenced from two directions.** A claim points at an
opportunity; evidence and independence groups point at the claim. Every one of
those edges is a chance for a cross-workspace reference, and the usual
protections — repository filters and RLS policies — both depend on the query
being written correctly.

## Decision

### 1. Stable `ClaimId`, append-only `claim_revisions`

`research.claims` holds identity, its opportunity, temporality, origin,
provenance and lifecycle. `research.claim_revisions` holds the statements, one
row per revision, **never updated**. `claims.current_revision` points at the
live one through a composite foreign key.

**The statement does not exist on `claims` at all.** A denormalised copy would
save one join and introduce a value that can drift from the history; keeping the
text in exactly one place makes the drift impossible rather than unlikely.

The pointer constraint is `DEFERRABLE INITIALLY DEFERRED`, because a claim and
its first revision reference each other and are written in one transaction. The
same pattern migration 0004 uses for a policy review and its evidence.

### 2. `research`, not `scoring`

A Claim is a domain assertion about an Opportunity. `scoring` evaluates
evidence; it does not own the assertions being evaluated
(`service-boundaries.md` §1). Independence groups go the other way — they are
part of the evidence model, so `scoring.evidence_independence_groups`.

### 3. Composite foreign keys carrying `workspace_id`

```sql
FOREIGN KEY (workspace_id, opportunity_id)
    REFERENCES research.opportunities (workspace_id, id)
FOREIGN KEY (workspace_id, claim_id, independence_group_id)
    REFERENCES scoring.evidence_independence_groups (workspace_id, claim_id, id)
```

This makes a cross-tenant reference a **structural impossibility** rather than a
rule somebody must remember. It cost two redundant `UNIQUE (workspace_id, id)`
constraints, and it buys a third isolation layer under the repository filter and
the RLS policy. The three fail differently, which is the point.

The group key carries `claim_id` as well, so an evidence record cannot join a
group belonging to a different claim — the failure that would silently collapse
unrelated evidence.

### 4. The scalar `independence` column is dropped, not reinterpreted

Mission 1.1 recorded it as incompatible. A number cannot say *which* records
share an origin, so grouping had nothing to group by. Worse, it invited
`q × independence` — discounting instead of grouping, which still lets ten
discounted duplicates outweigh one original.

Dropped rather than left beside `independence_state`: two answers to one
question, and the quantitative-looking one wins.

### 5. A three-state independence model, enforced by CHECK

```text
KNOWN_DEPENDENT    must name a group   -- dependent on WHAT?
KNOWN_INDEPENDENT  must not            -- or it claims both at once
UNKNOWN            must not            -- and stays unknown in storage
```

A nullable group id alone is **not** the model: it cannot distinguish "checked,
independent" from "never checked", and those call for different work. `UNKNOWN`
is the column default, because unestablished provenance is the honest starting
state for every record.

The aggregation engine builds its conservative single-bucket grouping for
unknown records **at runtime**, without writing anything. An unresolved question
must not look resolved in the database.

### 6. `ClaimLifecycle` is editorial, with two values

`ACTIVE` and `WITHDRAWN`. There is deliberately no `VALIDATED` and no
`REJECTED`.

A lifecycle state derived from evidence would freeze a conclusion that later
evidence could contradict, and it would be read as authoritative long after the
evidence moved. What a claim is worth is read from its aggregation, every time.
`WITHDRAWN` exists so a malformed or duplicated claim can leave circulation
without deleting the record of what was once believed.

### 7. `material_change` is recorded and acted on by nothing

Each revision carries an author-declared boolean: did the *meaning* change, or
only the wording?

Nothing consumes it in V1, on purpose. Deciding what a material change does to
already-attached evidence is part of **D-08**, which stays open. It is recorded
now because it cannot be reconstructed later — only the person making the edit
knows — and a future recomputation policy will need exactly this input.

## Consequences

### What this buys

A historical result stays readable. An aggregation naming `claim@r2` can always
recover what revision 2 said, however many times the claim has since been
rewritten.

Evidence survives a rewrite. Under an immutable-claim-plus-supersession model,
revising a claim would mint a new id and orphan every attached record — exactly
when the claim is being clarified.

Cross-tenant references are impossible rather than forbidden, at the level below
the one where mistakes are made.

Independence is finally representable, which unblocks the one part of the
aggregation model that a scalar could never have supported.

### What it costs

**A join on every claim read.** Deliberate, and the reason is in §1.

**Two redundant unique constraints** on `opportunities` and `research_sessions`,
purely so composite foreign keys have something to reference. Small, and they
buy the structural guarantee.

**A revision table that will mostly hold one row per claim.** Most claims are
never edited. The cost is one row and one index entry; the alternative is
discovering, after the first material edit, that no historical result can be
trusted.

**`material_change` is a field nothing reads.** It will look like dead weight
until D-08 is decided. The comment in the migration says why it exists so that
someone does not helpfully remove it.

### Rejected alternatives

**Immutable claims linked by supersession.** Rejected: identity would not
survive a rewrite, and the evidence set would fragment on every edit. Mission
1.2 §5 requires the opposite — text evolves, identity does not.

**A statement column on `claims`, with history alongside.** Rejected: one fact
in two places drifts, and the copy people read would be the one that drifted.

**Reinterpreting the scalar `independence` as a confidence-in-independence.**
Rejected, and it was the tempting option because it required no migration. It
still could not express which records share an origin, and it would have kept a
number in the schema that invites multiplication.

**Deriving `ClaimLifecycle` from `EvidenceLevel`.** Rejected outright (§38). It
conflates an editorial state with an epistemic verdict, and the verdict changes
when evidence does.

**A claim shared across opportunities.** Deferred, not rejected. If
deduplication later shows the same assertion recurring, that is a separate
decision with its own aggregation questions — whose evidence set, whose
workspace. The one-opportunity model is the one that can be reasoned about
first.

**Persisting an aggregation result now.** Rejected: storing one would be
scoring, scoring requires a `CALIBRATED` profile, and none exists (ADR-014). The
columns such a table would need are documented in `claim-model-v1.md` §11 so the
shape is known; the table is not created.
