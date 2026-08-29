# `docs/data/` — Data specifications

**Authoritative.**

| Document | Defines |
|----------|---------|
| `data-principles.md` | Source strategy, acquisition, raw preservation, quality, deduplication, language and geography, privacy, temporal modeling, contradictions, lineage, cost control, legal review |
| `data-retention-policy-v1.md` | Retention tiers, the stricter-constraint rule, per-source overrides, deletion semantics |
| `source-registry-v1.md` | The source registry, per-activity policy assessment, evidence requirements and the collector eligibility gate (added in Mission 1.0) |
| `acquisition-authorization-v1.md` | How a review condition is cleared, and what a collector must hold before it may run (added in Mission 1.4) |
| `source-review-guide.md` | How a human conducts a source review, step by step |
| `source-catalog-v1.json` | The reviewed candidate catalog. **Source of truth**, edited by hand |
| `source-catalog-v1.md` | The same catalog, rendered. **Generated** by `sros-source render`, checked in CI |
| `source-review-results-v1.md` | Mission 1.3 review results as a diff: previous verdict, new verdict, and the document that moved it. **Generated**, checked in CI |
| `source-human-review-queue-v1.md` | Twelve unresolved items, each with the exact document, the exact question and the exact next action |
| `source-condition-gap-analysis-v1.md` | The nine Mission 1.3 conditions inventoried and classified, and the obligations deliberately left out of code |
| `source-compliance-v1.json` | Attribution texts, licence and geography allowlists, enumerated exclusions and minimisation profiles. **Source of truth**, edited by hand |

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

Resolved does not mean open. The Mission 1.3 review round left **thirteen
sources registered and zero collector-eligible**: three reached
`APPROVED_WITH_CONDITIONS` — World Bank, Eurostat and FRED — and every condition
they carried was unsatisfied. Three verdicts moved *down* on current evidence
(YouTube to `PROHIBITED`, GitHub and Google Play to `RESTRICTED`), which is the
clearest sign the review was not optimising for approvals.

Mission 1.4 built the compliance capabilities those conditions require and
cleared eight of the nine. **World Bank and Eurostat are now collector-eligible**
in an environment where the capabilities are present and verified; **FRED is
design-eligible and not runnable**, because its API key is not configured.

Three things did not change, and they are the ones under pressure:

- a source never becomes eligible because its data is publicly visible;
- uncertainty resolves to `REQUIRES_REVIEW`, never to permission;
- **a condition is cleared by a verifier and by nothing else.** Not a manual
  boolean, not a catalog field, not a migration — the database refuses the
  boolean with no verification record behind it
  ([`acquisition-authorization-v1.md`](acquisition-authorization-v1.md),
  [ADR-016](../architecture/adr/ADR-016-compliance-capabilities-and-acquisition-authorization.md)).

`APPROVED_WITH_CONDITIONS` says a collector **may be designed**. Eligible says
one **may be built**. Neither says one exists: `collector_enabled` is false for
all thirteen sources, no collector is implemented, and
`acquisition.raw_records` is empty.

## Still open

- Evidence reliability weighting per source — blocked by **D-03**. The registry
  deliberately assigns no per-platform reliability number.
- Jurisdiction analysis (GDPR applicability) — **requires human/legal input**,
  deliberately not guessed.
- Backup retention and how deletion interacts with backups — deferred to the
  production ADR (ADR-007).
