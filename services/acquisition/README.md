# `services/acquisition`

**Status:** boundary defined, not implemented.
**Runtime:** Python (ADR-004). Playwright's Python API covers browser
automation, so removing BullMQ removed the last reason for Node on the backend.
**Blocked on:** D-07 — the source registry does not exist yet.

## Responsibility

Lawfully collect raw external data and preserve it with complete provenance.
Nothing more.

Acquisition **does not interpret**. It does not classify, extract signals, score
relevance, or decide what matters. It fetches, records, and hands off. Keeping
interpretation out of this layer is what makes raw data reproducible later
(`data-principles.md` §4).

## Inputs

- Acquisition tasks from `workers` (Celery), dispatched by
  `research-orchestrator`. Every task payload carries `workspace_id`.
- The source registry (D-07): per-source access method, credentials reference,
  rate limits, usage restrictions, retention constraints.

## Outputs

- **Raw records** with mandatory provenance
  (`evidence-confidence-framework-v1.md` §10):
  source identifier, URL/reference, collection timestamp, source type,
  acquisition method, extraction method, content hash, parent/derivative link,
  `workspace_id`, and `expires_at` computed at write time from the effective
  source retention policy (`data-retention-policy-v1.md` §6).
- **Normalized records** — a common shape across heterogeneous sources, with the
  raw record still reachable.
- Collection telemetry: coverage, rate-limit consumption, parse failures.

## Dependencies

- PostgreSQL — raw and normalized record storage
- Redis — rate-limit accounting, fetch deduplication cache
- Playwright — browser automation where no API exists
- Object storage (D-10) — large raw payloads
- `packages/contracts`

## Source families (from `data-principles.md` §2)

search/trend signals · communities · product launches · app stores ·
developer ecosystems · content platforms · public websites · structured
datasets · first-party sources

The concrete registry is Data Engineering phase work. No source is hardcoded here.

## Future API surface

```
POST /internal/acquire            execute one acquisition task
GET  /internal/sources            registered sources and their constraints
GET  /internal/sources/{id}/quota remaining rate-limit budget
GET  /internal/raw/{id}           retrieve a raw record by id
```

## Hard legal and ethical constraints

These are not guidelines. From `data-principles.md` §3 and §13, and
`docs/CLAUDE.md` §Data collection:

- Official APIs where available and appropriate.
- Comply with source terms and robots directives.
- Respect rate limits. Never engineer around them.
- **Never bypass authentication or technical protections.**
- Minimize collection — only what the research objective requires.
- No credentials in source control.
- Public visibility does not imply commercial reuse rights. Every new source gets
  a §13 legal review record **before** first collection.
- Retention is bounded: raw content defaults to **30 days**, overridable per
  source via `retention_override` with a recorded `basis`
  (`data-retention-policy-v1.md` §2.1, §3). The stricter constraint always wins.
- Avoid unnecessary personal data; aggregate or anonymize where possible
  (`data-principles.md` §8).

## Deduplication boundary

Acquisition performs **exact** deduplication only (content hash), and never
destroys provenance when it does (`data-principles.md` §6). Near-duplicate,
syndication and derivative detection require semantics and belong to `nlp`.

## Failure modes to design for

| Failure | Required behavior |
|---------|-------------------|
| Rate limited | Backoff and reschedule. Never retry aggressively, never rotate identity to evade |
| Source changed layout | Fail loudly with a parse-failure record. A silent empty result is worse than an error |
| Partial page load | Record partial with a quality flag; never present partial as complete |
| Content requires auth | Abort the task. Not an error to work around |
| Robots/terms disallow | Source is removed from the registry, not worked around |
| Duplicate of an existing record | Link to the existing record, keep the new provenance, do not overwrite |
