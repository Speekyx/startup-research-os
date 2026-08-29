# `services/acquisition`

**Status:** the Source Registry, the compliance capability layer and the **first
collector** are implemented. One source can be collected from: World Bank.
**Runtime:** Python (ADR-004). Playwright's Python API covers browser
automation, so removing BullMQ removed the last reason for Node on the backend.
**Governed by:** [`source-registry-v1.md`](../../docs/data/source-registry-v1.md),
[`acquisition-authorization-v1.md`](../../docs/data/acquisition-authorization-v1.md),
[`world-bank-collector-v1.md`](../../docs/data/world-bank-collector-v1.md),
[ADR-013](../../docs/architecture/adr/ADR-013-source-registry-governance.md),
[ADR-016](../../docs/architecture/adr/ADR-016-compliance-capabilities-and-acquisition-authorization.md).

D-07 is resolved: the registry, its per-source review records and the collector
eligibility gate exist (Mission 1.0). Mission 1.4 built the compliance
capabilities that a conditional approval requires, so **two sources now pass the
gate** — `world-bank` and `eurostat`. `sros-source eligibility <id>` prints
exactly what each of the other eleven is missing.

Mission 1.5 built the **World Bank Indicators collector**, the reference every
later one follows. It cannot run without an `AcquisitionAuthorizationContext`,
every resource passes `authorize_resource` before a socket opens, and no public
signature in the package accepts a URL.

Eurostat is collector-eligible and has no collector. That pairing is what keeps
the distinction honest.

```text
sros_acquisition/
    registry/models.py           source, access profile, review, evidence, retention
    registry/eligibility.py      the gate. Fails closed, reports every reason
    registry/retention.py        baseline vs override. min(), never max()
    registry/catalog.py          loads docs/data/source-catalog-v1.json
    registry/repositories.py     applies the catalog to PostgreSQL, idempotently
    compliance/config.py         obligations as governance data, not branches
    compliance/attribution.py    what attribution follows the data, and survives
    compliance/resources.py      which resources the approval actually covers
    compliance/credentials.py    whether a key is configured, never what it is
    compliance/capabilities.py   named capabilities and the checks that make them real
    compliance/verification.py   running a verifier against a review condition
    compliance/authorization.py  what a collector must hold before it may run
    compliance/repositories.py   recording a verification, syncing the gate
    collection/transport.py      the HTTP boundary. The ONLY file that may reach a network
    collection/pacing.py         our own request pacing. Not anyone's rate limit
    collection/records.py        what an observation is, and what identifies it
    collection/world_bank.py     the collector
    collection/repositories.py   persistence: idempotent, revision-aware, tenant-scoped
    collection/job.py            one acquisition job, testable without a broker
    rendering.py                 generates the human-readable catalog
    cli.py                       sros-source: governance
    acquisition_cli.py           sros-acquisition: validate, smoke, collect
```

**Exactly one file may import a network client, and CI asserts it.** Mission
1.0's blanket ban was narrowed rather than deleted when the first collector
arrived: `collection/transport.py` is the boundary, and the registry and
compliance packages remain network-free because they *decide* whether collection
may happen.

## Eligible, enabled, implemented

Three facts. Collapsing any two of them is the mistake this section exists to
prevent.

| Fact | Now | Where it lives |
|---|---|---|
| collector-eligible | `world-bank`, `eurostat` | `registry.source_eligibility`, derived |
| collector implemented | `world-bank` | `sros_acquisition.IMPLEMENTED_COLLECTORS` |
| collector-enabled | `world-bank`, set deliberately | `registry.sources.collector_enabled` |

`sros-source enable` refuses a source with no implemented collector: a switch
that gets ahead of the thing it switches reads, to anyone looking at the
registry, as "this is running".

## Clearing a condition

A condition is cleared by a **verifier**, never by a boolean. `sros-source
verify --apply` runs them and records what each one checked; a database trigger
refuses `satisfied = TRUE` with no `SATISFIED` verification behind it. Results
are `SATISFIED | UNSATISFIED | UNKNOWN | NOT_APPLICABLE` and only the first
clears — `UNKNOWN` blocks exactly as a failure does.

Re-verification takes a source **out** of eligibility as readily as into it,
which is why CI re-verifies rather than trusting recorded state.

Full specification:
[`acquisition-authorization-v1.md`](../../docs/data/acquisition-authorization-v1.md).

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
- The source registry: per-source access method, secret **reference** (a
  configuration key name, never a value), rate limits, usage restrictions,
  retention constraints. A collector reads it; it never writes to it.

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

No source is hardcoded here. The catalog is
[`docs/data/source-catalog-v1.json`](../../docs/data/source-catalog-v1.json),
rendered for reading as
[`source-catalog-v1.md`](../../docs/data/source-catalog-v1.md).

## API surface

Implemented, read only:

```
GET  /api/v1/sources                    registered sources, states and gate verdicts
GET  /api/v1/sources/{id}               one source with evidence, review and retention
GET  /api/v1/sources/{id}/eligibility   every condition, its verification and the blockers
```

There is deliberately **no write endpoint**. Authentication does not exist
(ADR-005), so an endpoint able to approve a source or enable a collector would
make the review process optional for anyone who can reach the service. Review is
administered by `sros-source`, running as the migration role; the runtime role
holds `SELECT` only on `registry.*`.

The eligibility endpoint serves the **recorded** state, not a fresh
verification: running verifiers on an HTTP request would make the answer depend
on the web process's environment rather than on the deployment the registry
describes.

Future, once a collector exists:

```
POST /internal/acquire            execute one acquisition task
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
  (`data-retention-policy-v1.md` §2.1, §3). The stricter constraint always wins,
  and a collector receives the resolved rule rather than choosing one.
- A collector obtains an `AcquisitionAuthorizationContext` or it does not run,
  and reaches every dataset through `context.authorize_resource(...)`. It does
  not interpret a source's terms: doing so would be a second opinion about a
  decision the review already made.
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
| Robots/terms disallow | The review records `NOT_PERMITTED`, the gate refuses, and the source stays registered with its reason. Never worked around |
| Duplicate of an existing record | Link to the existing record, keep the new provenance, do not overwrite |
