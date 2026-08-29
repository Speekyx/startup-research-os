# `docs/data/` — Data specifications

**Authoritative.**

| Document | Defines |
|----------|---------|
| `data-principles.md` | Source strategy, acquisition, raw preservation, quality, deduplication, language and geography, privacy, temporal modeling, contradictions, lineage, cost control, legal review |
| `data-retention-policy-v1.md` | Retention tiers, the stricter-constraint rule, per-source overrides, deletion semantics |
| `source-registry-v1.md` | The source registry, per-activity policy assessment, evidence requirements and the collector eligibility gate (added in Mission 1.0) |
| `source-review-guide.md` | How a human conducts a source review, step by step |
| `source-catalog-v1.json` | The reviewed candidate catalog. **Source of truth**, edited by hand |
| `source-catalog-v1.md` | The same catalog, rendered. **Generated** by `sros-source render`, checked in CI |

## The rules that are hardest to retrofit

Everything here is cheap now and expensive later. Three in particular:

1. **Provenance and lineage** (§11). Adding lineage to a system that already has
   data means the old data has none, permanently. The recommendation in
   `specification-audit.md` A-10 is to make provenance fields non-nullable by
   default, so that an exemption is a reviewed decision rather than an accident.
2. **Event-time semantics** (§9). Prefer event time over ingestion time for market
   analysis. Trend analysis computed on ingestion timestamps produces artifacts
   that look exactly like real market movements — and once the ingestion-time
   column is the only one you kept, it cannot be recovered.
3. **Contradiction preservation** (§10). Overwriting conflicting evidence
   destroys information the analytical layer needs. A row that was overwritten
   cannot be un-overwritten.

## Legal review is a prerequisite, not a formality

§13 requires recording, **before** integrating a source: access method, API
availability, usage restrictions, rate limits, retention constraints, licensing,
authentication requirements.

"Publicly visible" does not mean "free to reuse commercially". This applies to
test fixtures as much as to production collection.

## Retention — resolved

**D-06 is resolved.** See `data-retention-policy-v1.md`:

| Tier | Default |
|------|---------|
| Raw collected content | 30 days |
| Normalized observations and evidence | 12 months maximum target |
| Aggregated signals and features | Longer where lawful and non-reconstructive |
| Scores | Versioned historical records, retained |

Two rules govern every conflict: **the stricter constraint always wins**, and
**derived non-personal aggregates are preferred over raw personal content**.

Per-source `retention_override` (with a recorded `basis`) overrides the defaults
in either direction, subject to the stricter-constraint rule.

Deletion semantics are defined; deletion logic is **not implemented**.

## Source governance — resolved

**D-07 is resolved.** See `source-registry-v1.md` and
[ADR-013](../architecture/adr/ADR-013-source-registry-governance.md). The
registry exists, the `retention_override` mechanism the retention policy depends
on now has a table behind it, and collector eligibility is a derived gate rather
than a stored flag.

Resolved does not mean open. **Thirteen candidate sources are registered and
zero are collector-eligible**, which is the expected outcome of a first pass:
§31 of the mission brief asks for correctness over the number of approvals, and
a registry where every platform came back approved would mean the gate was doing
nothing.

Two rules are worth repeating here because they are the ones under pressure:

- a source never becomes eligible because its data is publicly visible;
- uncertainty resolves to `REQUIRES_REVIEW`, never to permission.

## Still open

- Evidence reliability weighting per source — blocked by **D-03**. The registry
  deliberately assigns no per-platform reliability number.
- Jurisdiction analysis (GDPR applicability) — **requires human/legal input**,
  deliberately not guessed.
- Backup retention and how deletion interacts with backups — deferred to the
  production ADR (ADR-007).
