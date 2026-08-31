# Use-Profile Migration V1 — what was interpreted, and what was not

**Authoritative.** Mission 1.15.5 §8, §9, §29. How 55 existing reviews acquired a
subject without acquiring a new conclusion.

**Nothing was rewritten.** No verdict, assessment, condition, open question,
evidence row or review version changed. The migration attached an identity to a
scope those reviews already stated in prose.

---

## 1. The interpretation, and why it is not a guess

Every historical review was attached to
**`commercial-multi-tenant-research-v1`**.

§8 warns against retroactively pretending a review assessed a profile that did
not exist. It did not have to be pretended, because the catalog has said it since
Mission 1.0, at the top, inherited by every review:

> *"Automated collection of public content by Startup Research OS, a
> **COMMERCIAL multi-tenant SaaS**, for storage, derived analytics and LLM
> processing to produce opportunity intelligence. **Every assessment below is
> scoped to that use.** An assessment does not transfer to non-commercial or
> academic use, and a permission granted for a narrower purpose does not widen
> to this one."*

**The migration canonicalises a sentence that was already there.** The profile's
recorded facts — public multi-tenant deployment, external customers,
redistribution and resale in scope, commercial purpose, model inference, no
training — are that sentence made checkable.

**Recorded as an interpretation, not a conclusion.** The profile's own `notes`
field says so, and so does the migration's header comment. A future reader who
disagrees with the interpretation can see exactly what it was based on.

## 2. What did not change

| | Before | After |
|---|---:|---:|
| Sources | 29 | 29 |
| Reviews (legacy line) | 55 | 55 |
| `APPROVED_WITH_CONDITIONS` | 5 | **5** |
| `REQUIRES_REVIEW` | 13 | **13** |
| `RESTRICTED` | 8 | **8** |
| `PROHIBITED` | 3 | **3** |
| Evidence rows | unchanged | unchanged |
| Collector-eligible sources | 0 | 0 |

Asserted by test, not by inspection.

## 3. Per-source profiles were not invented

§9 permits one canonical legacy profile "only if justified" and warns against
inventing one per source. One was justified and one was created: every review
inherited the same catalog-level scope, so there is exactly one historical
assessed use and no evidence of a second.

## 4. Review row ids keep the historical derivation

Review ids are deterministic surrogates derived from `(source, version)`. The
obvious move — re-derive every id as `(source, profile, version)` — would have
**orphaned the rows that hang off them**: `source_review_conditions`, and through
them `source_condition_verifications`, which records who checked what, when, with
which verifier version.

Those verifications are real history. Deleting them to make a reload tidy would
destroy the record the registry exists to keep, so:

- **legacy-profile reviews** keep `_row_id("review", source, version)`;
- **profiles that did not exist before this migration** use
  `_row_id("review", source, profile, version)`, and only to stop their version 1
  colliding with the legacy version 1.

An asymmetry, deliberately, with the reason written at the call site.

## 5. Schema changes

```text
registry.use_profiles                    new table, two rows
source_policy_reviews.assessed_use_profile   NOT NULL, FK, DEFAULT dropped
                                             immediately after backfill
UNIQUE (source_id, review_version)       ->  (source_id, assessed_use_profile,
                                              review_version)
idx_..._current                          ->  (source_id, assessed_use_profile)
sources.collector_use_profile            new, required when collector_enabled
registry.source_eligibility              one row per (source, profile)
```

**The default was dropped in the statement after the backfill.** It existed only
to fill history; leaving it would mean a future review that failed to say what it
assessed would silently inherit an answer nobody gave.

**The view was rebuilt from migration 0006's definition, not 0004's.** The first
attempt rebuilt from 0004 and silently lost the `condition_count` columns *and*
the `review conditions not satisfied` blocking reason — the rule that makes
`APPROVED_WITH_CONDITIONS` mean something. It was caught by a test that asserts
the SQL view and the Python gate agree, which is why that test exists.

The `GRANT SELECT ... TO sros_app` was also re-issued: `DROP VIEW` discards
privileges with the view, and migration 0006 recorded that this failed exactly
that way once.

## 6. What a future migration must do

**Adding a profile** is an INSERT into `registry.use_profiles` plus an entry in
the catalog's `use_profiles` block. No schema change, because it is a registry
rather than an enum — and an ADR, because a third profile should be hard enough
to add that somebody justifies it.

**Changing a profile's meaning** is a new id with a new version suffix. Editing
one in place would silently move every review that names it into answering a
different question.

**Retiring a profile** sets `status = 'RETIRED'`. Its reviews stay: they are the
record of what was concluded while it was live.
