# `docs/data/` — Data specifications

**Authoritative.**

| Document | Defines |
|----------|---------|
| `data-principles.md` | Source strategy, acquisition, raw preservation, quality, deduplication, language and geography, privacy, temporal modeling, contradictions, lineage, cost control, legal review |

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

## Still open

- **D-07** — the source registry does not exist. Blocks `acquisition`, and blocks
  the `retention_override` mechanism that the retention policy depends on.
- Jurisdiction analysis (GDPR applicability) — **requires human/legal input**,
  deliberately not guessed.
- Backup retention and how deletion interacts with backups — deferred to the
  production ADR (ADR-007).
