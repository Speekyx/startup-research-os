# Data Retention Policy V1

**Status:** Authoritative
**Version:** 1.0
**Date:** 2026-08-27
**Authorized by:** Sprint 0 / Mission 0.1.1, §12
**Governs:** `data-principles.md` §8 (Privacy), §12 (Cost control), §13 (Legal)
**Resolves:** decision **D-06**

> **Implementation status:** this is a policy, not an implementation. Deletion
> logic, lifecycle jobs and enforcement mechanisms are **not** implemented and
> are out of scope for Mission 0.1.1. What this document establishes is the
> contract that the schema and the source registry must support.

---

## 1. Purpose and principles

The system collects public content from third-party sources in order to derive
structured research signals. That creates three obligations that pull in
different directions:

- **Reproducibility** — `data-principles.md` §4 wants enough raw data preserved
  to reproduce important transformations.
- **Legal and contractual compliance** — §13 makes source terms binding, and
  public visibility does not imply a right to retain indefinitely.
- **Privacy and minimization** — §8 requires avoiding unnecessary personal data.

This policy resolves the tension with one ordering rule:

> **Prefer retaining derived, non-personal aggregates over raw personal content.**
> When reproducibility and minimization conflict, minimization wins, and the loss
> of reproducibility is recorded rather than hidden.

A second rule governs conflicts with sources:

> **The stricter constraint always wins.** A source policy or legal requirement
> that mandates shorter retention overrides every default in this document. A
> source that permits longer retention does not automatically extend it —
> necessity must also be established.

---

## 2. Retention tiers

### 2.1 Raw collected content

**Default retention: 30 days.**

Covers `raw_record` — the verbatim payload as collected: page content, API
response bodies, rendered DOM, review text, post bodies.

Shorter retention applies when:

- the source's terms require it,
- a legal constraint requires it,
- the content contains personal data that is no longer necessary.

Longer retention applies **only** when both conditions hold:

- the source's terms and licensing permit it, **and**
- the research case establishes necessity, recorded in the source registry.

**Rationale.** Raw content is the highest-risk and lowest-reuse tier: it carries
the licensing exposure, the privacy exposure and the storage cost, and its
analytical value is mostly extracted within days of collection by the
normalization and NLP stages. Thirty days is long enough to re-run a failed or
buggy pipeline stage against the original input, which is the actual operational
need.

### 2.2 Normalized observations and evidence

**Default maximum target retention: 12 months.**

Covers `normalized_record`, `signal`, `classification`, `evidence`.

Subject to:

- source policy,
- licensing,
- legal requirements,
- user deletion requests,
- **necessity** — the default is a ceiling, not an entitlement.

**Rationale.** Twelve months is roughly the horizon over which market signals stay
analytically meaningful. `evidence-confidence-framework-v1.md` §5 already decays
evidence value over time; retaining evidence long past the point where decay has
reduced it to negligible weight adds risk and cost without adding analytical
value.

### 2.3 Aggregated signals and features

**May be retained longer**, where legally and contractually permitted.

Covers clusters, aggregate market estimates, momentum series, derived features,
and any statistic that no longer references identifiable individual content.

**Rationale.** These are the durable analytical asset, they carry the least
privacy and licensing risk, and they are what makes longitudinal market analysis
possible at all. Retaining an aggregate instead of the underlying raw content is
the preferred trade in every case where both would serve.

**Condition:** an aggregate qualifies for extended retention only if it is
genuinely non-personal and non-reconstructive. An "aggregate" computed over three
records from which the originals can be inferred is not an aggregate for the
purposes of this policy.

### 2.4 Scores

**Retained as versioned historical records.**

Scores must be:

- **versioned** — framework version, profile version, model version
  (`scoring-framework-v1.1.md` §11),
- **timestamped** — including the evidence snapshot time they were computed from,
- **historically traceable** — a past score remains inspectable after the
  evidence that produced it has expired.

**Rationale.** Scores are the system's output and its audit trail. Deleting score
history would destroy the ability to explain why a ranking changed, which is a
manifest-level requirement (§Explainability).

**Consequence that must be designed for:** when evidence expires under §2.2, a
score outlives its inputs. The score record must therefore carry enough
self-contained rationale and evidence *references* that its derivation remains
explicable, while accepting that the referenced content may no longer exist. A
dangling evidence reference must render as "evidence expired", never as an error
and never silently as "no evidence".

### 2.5 Operational data

| Data | Default retention | Note |
|------|-------------------|------|
| Job records, attempts | 90 days | Operational debugging |
| Dead-letter entries | 90 days, or until replayed and resolved | Replay payload needed |
| Structured logs | 30 days | Never contain raw content or personal data |
| Metrics | Aggregated indefinitely | Non-personal by construction |
| ResearchSession state, context snapshots and plans | Follows §2.2 | Part of the research record. The `ResearchContext` snapshot is what makes a past session reproducible, so it expires with the session, not before it |

---

## 3. Per-source override

The future **Source Registry** (decision **D-07**) must support:

```text
retention_override
```

A source-specific policy **overrides the generic default in both directions**,
subject to the stricter-constraint rule in §1.

Required fields per source, alongside the §13 legal review record:

| Field | Purpose |
|-------|---------|
| `retention_override.raw_days` | Overrides §2.1 |
| `retention_override.normalized_days` | Overrides §2.2 |
| `retention_override.aggregate_permitted` | Whether derived aggregates may be retained beyond the above |
| `retention_override.basis` | **Why** — the specific term, licence clause or legal requirement |
| `retention_override.reviewed_at` | When the basis was last verified |

`basis` is not optional. A retention override without a recorded justification is
indistinguishable from someone having wanted more data, and it cannot be
re-verified when the source's terms change.

**Default when a source has no override: the §2 defaults apply.** A source with
no registry entry may not be collected from at all (`data-principles.md` §13).

---

## 4. Provenance under retention

Where legally and technically permitted, derived records retain enough provenance
to explain how they were produced:

- source id
- observation timestamp
- content hash
- acquisition method
- extraction method / transformation version
- model and prompt versions where applicable

**Provenance survives the content it describes.** When a `raw_record` expires,
its metadata — source id, timestamp, hash, method — is retained on the derived
records. This preserves lineage (`data-principles.md` §11) at negligible privacy
cost, because the metadata is not the content.

**The overriding limit:** do **not** retain content merely because provenance is
desirable. If source terms or law require deletion, the content is deleted and
the derived record records that its source content has expired. A derived record
whose provenance cannot be lawfully retained records the fact of that gap rather
than the provenance itself.

This is the one place where the system's own reproducibility principle yields.
It yields visibly: an expired-provenance marker is part of the record, not an
absence.

---

## 5. Deletion semantics

Defined here, **implemented later**.

### 5.1 Deletion classes

| Class | Trigger | Behavior |
|-------|---------|----------|
| **Expiry** | Retention period elapsed | Scheduled lifecycle job; content removed, provenance metadata retained per §4 |
| **Source-mandated** | Source terms or a takedown notice | Immediate; overrides expiry schedule; may also remove provenance |
| **Legal** | Legal requirement or erasure request | Immediate; propagates to derived records where the law requires |
| **Tenant** | Workspace deletion (ADR-005) | All tenant-scoped data for that `workspace_id` |
| **User request** | Deletion of specific collected content | Scoped removal with lineage marking |

### 5.2 Required semantics

1. **Deletion is scoped by `workspace_id`** (ADR-005). Tenant-scoped raw and
   normalized records mean a workspace deletion is tractable rather than a
   cross-tenant untangling — this was one reason for that ownership choice.
2. **Deletion propagates to every store**: PostgreSQL, object storage, Qdrant,
   and any cache. A vector left in Qdrant after its source record is deleted is
   still that content, in embedded form — this is the most easily forgotten path.
3. **Soft delete is not deletion.** For legal and source-mandated deletion, the
   content is actually removed. A `deleted_at` column satisfies nothing.
4. **Deletion is recorded.** What class, when, what scope, on what basis. A
   deletion with no record is indistinguishable from data loss.
5. **Derived records survive where lawful**, carrying an explicit expired marker.
   Where the law requires propagation, derived records are deleted too.
6. **Contradiction preservation still applies** (`data-principles.md` §10). Data
   is never deleted because it disagrees with other data. Retention expiry is
   time-based and blind to whether a record was convenient.
7. **Deletion is idempotent** and safe to re-run — the same requirement ADR-004
   places on every job.

### 5.3 What must never happen

- Deleting a score's rationale while keeping the score.
- Deleting evidence because it lowered a score.
- Retaining raw content past its window because a pipeline stage might want it.
- Deleting from PostgreSQL without deleting the corresponding vectors.
- Treating a cache as exempt because it is "temporary".

---

## 6. Data lifecycle requirements (future work)

Not implemented. Recorded so the schema and the source registry are built to
support them.

| Requirement | Depends on |
|-------------|-----------|
| Scheduled expiry job per tier | Celery Beat (ADR-004) |
| `expires_at` computed at write time from the effective source policy | Schema v1 |
| Source registry with `retention_override` | D-07 |
| Cascade deletion across PostgreSQL, object storage and Qdrant | Schema v1, ADR-005 |
| Workspace deletion flow | ADR-005 |
| Deletion audit log | Schema v1 |
| Expired-provenance markers on derived records | Schema v1 |
| Retention metrics — volume by tier, age distribution, upcoming expiry | `packages/observability` |

**Schema requirement for Mission 0.2:** every retention-governed table carries
`collected_at` (or `observed_at`) and `expires_at`, both `NOT NULL`, from its
first migration. `expires_at` computed at write time — rather than derived at
read time from a policy that may since have changed — is what makes the
retention decision auditable after the fact.

---

## 7. Open items

| Item | Status |
|------|--------|
| Source registry format and `retention_override` schema | **Open — D-07** |
| Per-source legal review records | **Open — D-07** |
| Whether erasure requests must propagate to aggregates | Open; depends on jurisdiction and on whether aggregates are reconstructive |
| Backup retention and how deletion interacts with backups | Open; deferred to the production ADR (ADR-007 §Environments) |
| Concrete jurisdiction analysis (GDPR applicability given the operator is EU-based, in La Réunion) | **Open — requires human/legal input** |

The last item is genuinely outside what this document can settle. It is recorded
in the Mission 0.1.1 report as requiring human decision before any production
deployment, and it is deliberately **not** guessed here.
