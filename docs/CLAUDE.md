# CLAUDE.md — Startup Research OS

Version: 1.17
Last amended: 2026-08-30 (Sprint 1 / Mission 1.11)

## Boot Sequence

Before performing any task, execute this reading order.

1. PROJECT_MANIFEST.md
2. docs/CLAUDE.md
3. docs/domain/opportunity-ontology-v2.1.md
4. docs/domain/scoring-framework-v1.1.md
5. docs/domain/evidence-confidence-framework-v1.md
6. docs/ai/llm-reasoning-rules.md
7. docs/data/data-principles.md
8. docs/data/data-retention-policy-v1.md
9. docs/data/source-registry-v1.md
10. docs/data/acquisition-authorization-v1.md
11. docs/data/world-bank-collector-v1.md
12. docs/data/normalized-record-v1.md
13. docs/data/world-bank-normalizer-v1.md
14. docs/domain/evidence-aggregation-framework-v1.md
15. docs/domain/claim-model-v1.md
16. docs/ai/evaluation-framework-v1.md
17. docs/data/signal-contract-v1.md
18. Relevant ADRs
19. Task-specific specifications

These documents are the authoritative source of truth.

**`opportunity-ontology-v1.md`, `opportunity-ontology-v1.1.md` and
`scoring-framework-v1.md` are superseded.** They remain in the repository as
historical records. Do not use them as the basis for implementation. See
`PROJECT_MANIFEST.md` §Superseded specifications.

Ontology V2 keeps V1.1's numbering for §1–§10, so an existing reference to
`opportunity-ontology-v1.1.md §N` with `N ≤ 10` resolves to the same rule in V2.

## Version history

| Version | Date | Change |
|---------|------|--------|
| 1.17 | 2026-08-30 | Signal defined as a DERIVATION over two or more observations, never a labelled one. `nlp.signals` reshaped; the family stops classifying demand; order and instant separated, and H-32 opened. Model and contract only -- no extractor, 0 signals |
| 1.16 | 2026-08-30 | Second normalizer recorded: GDELT WEB-NGRAM, deterministic and offline, with two real canonical records. Every one is PARTIAL because H-29 and H-30 stay open and are stated per record |
| 1.15 | 2026-08-30 | Second canonical record kind recorded: a lexical frequency observation with no geography. A period may declare its timezone unestablished and a language may stay unmapped, both visibly (ADR-019). No GDELT normalizer |
| 1.14 | 2026-08-30 | Second collector recorded: GDELT WEB-NGRAM, streamed and bounded, with real RawRecords. Bulk-file collection rules added; GDELT is collected and still not normalized |
| 1.13 | 2026-08-30 | Resource-ready separated from eligible: a source can pass the gate while every resource it could ask for fails closed. GDELT review 3 authorises two WEB-NGRAM resources; how much a job may take became a governance question alongside what it may reach |
| 1.12 | 2026-08-30 | Silence-is-not-permission made mechanical: an approving review must grant every materially required activity. Three Mission 1.7 approvals withdrawn on audit; GDELT became the fourth collector-eligible source and the first non-economic one |
| 1.11 | 2026-08-30 | Source universe expanded to 27 across 14 families; signal coverage added as a non-scoring source attribute (ADR-017); coverage-is-not-permission invariant added; global registry state watched by the post-suite check |
| 1.10 | 2026-08-30 | First normalizer recorded: the RawRecord to NormalizedRecord boundary, World Bank only; normalized_records is no longer empty; normalization invariant added; normalizable separated from eligible, enabled and implemented |
| 1.9 | 2026-08-30 | First collector recorded: World Bank only, gated by an AcquisitionAuthorizationContext; raw_records is no longer empty; collector boundary invariant added |
| 1.8 | 2026-08-29 | Compliance capabilities recorded: a condition is cleared by a verifier and by nothing else; two sources are collector-eligible; eligible / enabled / implemented separated (ADR-016) |
| 1.7 | 2026-08-29 | Source review round recorded: three sources APPROVED_WITH_CONDITIONS, none collector-eligible; conditional-eligibility rule added |
| 1.6 | 2026-08-29 | Boot sequence points to Ontology V2.1 and gains the Claim model; Claim invariant added; A-13 removed from blocked work (ADR-015) |
| 1.5 | 2026-08-29 | Boot sequence gains the evidence aggregation framework; evidence-aggregation invariant added; D-03 blocked-work entry rewritten as framework-resolved / parameters-uncalibrated (ADR-014) |
| 1.4 | 2026-08-29 | Boot sequence gains the source registry spec; source-governance invariant added; D-07 removed from blocked work (ADR-013) |
| 1.3 | 2026-08-29 | Boot sequence gains the evaluation framework; tenancy invariant records that row-level security is now enforced (ADR-012) |
| 1.2 | 2026-08-27 | Boot sequence points to ontology V2; research lifecycle and taxonomy-governance invariants added |
| 1.1 | 2026-08-27 | Boot sequence points to domain V1.1; canonical domain invariants added (§Canonical invariants); tenancy rule added |
| 1.0 | — | Initial operating contract (was unversioned; versioning added in 1.1 per `specification-audit.md` §4 recommendation 8) |
## Purpose

This repository contains an evidence-driven AI Opportunity Research Engine for discovering, analyzing, scoring, validating, and planning digital product opportunities across B2B, B2C, entertainment, education, gaming, creator, hobby, utility, social, AI, and other markets.

This file is the top-level operating contract for Claude Code.

## Authoritative specifications

Before making architectural or implementation decisions, read the relevant documents in this order:

1. `docs/domain/opportunity-ontology-v2.md`
2. `docs/domain/scoring-framework-v1.1.md`
3. `docs/domain/evidence-confidence-framework-v1.md`
4. `docs/ai/llm-reasoning-rules.md`
5. `docs/data/data-principles.md`
6. `docs/data/data-retention-policy-v1.md`
7. Any relevant Architecture Decision Records (ADRs)
8. Any task-specific specification created later

These documents are authoritative unless a newer, explicitly versioned specification or ADR supersedes them.

## Canonical invariants

Added in 1.1. These are settled. Do not re-derive them, do not redefine them
locally, and do not resolve an apparent conflict with them by guessing.

### Claim taxonomy — exactly five values, UPPERCASE

```text
OBSERVED | INFERRED | PREDICTED | RECOMMENDED | HYPOTHESIS
```

`HYPOTHESIS` is mandatory and first-class. Definitions in
`opportunity-ontology-v2.md` §7. Closed enum: changing it requires a new
ontology version and an ADR.

### Confidence — unit interval

```text
0.0 <= confidence <= 1.0
```

Applies to `confidence`, `reliability`, `independence`, probability and signal
`value`, in the database, in API and domain contracts, and in ML calculations.
Presented to users as a percentage (`0.82` → `82%`).

**Scores are a different quantity** and keep 0–100 semantics. `evidence_level` is
an integer 0–5 and is never rescaled. Never conflate score, confidence,
probability and evidence strength — see `scoring-framework-v1.1.md` §4.1 and
`opportunity-ontology-v2.md` §9.

Naming rule: a field named `confidence` is always `[0,1]`; a field named
`*_score` is always `0–100`.

### Research lifecycle — canonical names

```text
Workspace → ResearchProject → ResearchSession → Evidence / Signals / Opportunities
                                    |
                                    +-- ResearchContext snapshot (immutable)
```

`ResearchSession` is the **only** persisted execution entity. `ResearchContext` is
an input specification (a value object), stored as an immutable snapshot on the
session. `ResearchProject` is the persistent grouping.

**`research run` is retired.** Use `ResearchSession` / `research_session_id`. In
historical documents and accepted ADRs, "research run" means `ResearchSession`
and `run_id` means `research_session_id`. See Ontology V2 §11.

### Market scope

`MarketScope` is a closed discriminated union on `type`:
`GLOBAL | REGION | COUNTRY | MULTI_COUNTRY`. Countries are ISO 3166-1 alpha-2;
regions come from a controlled registry. `COUNTRY` carries exactly one country,
`MULTI_COUNTRY` two or more. See Ontology V2 §4.

### Taxonomies — registries, not database enums

Product Type, Market Type, User Motivation, User Behavior, Value Proposition,
Retention Mechanism, Monetization Model, Distribution Channel, Risk and Region are
**extensible registries**. Adding an entry must never require a migration.

Closed enums are only: `ClaimType`, `MarketScope.type`, demand signal family,
`EvidenceLevel`, `ResearchSessionStatus`, and lifecycle values requiring
exhaustive branching. See Ontology V2 §14.

### Tenancy — workspace-scoped

The tenant boundary is the **Workspace**. Every primary domain resource carries
`workspace_id`, propagated explicitly through every service call, every Celery
task payload, every cache key, every vector-store filter and every log line.

`workspace_id` is never inferred, never defaulted in service code, never
reconstructed from another field. A missing `workspace_id` is an error in every
environment. See ADR-005.

**Two layers, since Mission 0.4 (ADR-012).** The explicit repository filter is
layer 1 and remains mandatory. PostgreSQL row-level security is layer 2, entered
through a transaction-local tenant context. Neither replaces the other: a
forgotten `WHERE` is caught by the policy, and a missing tenant context returns
no rows rather than wrong ones. Removing the explicit filter because RLS exists
is a regression, not a cleanup.

### Jobs — Celery over Redis

All asynchronous work runs through Celery with Redis as broker. There is no Node
worker tier. Delivery is at-least-once, so every job must be idempotent. See
ADR-004.

### LLM access — through the gateway only

No business service imports a provider SDK. Services request a logical tier
(`FAST_MODEL`, `BALANCED_MODEL`, `STRONG_MODEL`, `EMBEDDING_MODEL`), never a
provider or a model name. See ADR-006.

### Source governance — a gate, not a field

A source becomes collectable only by passing the eligibility gate in
`registry.source_eligibility`, never by any other route. Four rules follow, and
none of them is negotiable (`source-registry-v1.md` §1, ADR-013):

- **Public visibility is not permission.** Reachability is an access-profile
  fact; permission is a review fact; the gate requires the review.
- **Uncertainty is never permission.** Silent, unreachable or ambiguous terms
  produce `NOT_ADDRESSED` / `UNCLEAR` and leave the source `REQUIRES_REVIEW`.
  There is no path from *we could not check* to *we may proceed*.
- **An approval requires retrieved, authoritative evidence** — the source's own
  documents, operator correspondence or a recorded legal review. Never a blog
  post, a tutorial, a forum answer or model recall.
- **No credential is stored in the registry.** Access profiles carry
  configuration key names only.
- **`APPROVED_WITH_CONDITIONS` is not permission to run.** It says a collector
  MAY be designed. Every condition is a checkable row, and the gate blocks until
  all of them are satisfied — where satisfaction is environment state that a
  catalog can never assert about itself.
- **A condition is cleared by a verifier, and by nothing else** (Mission 1.4,
  ADR-016, `acquisition-authorization-v1.md`). A verification records which
  condition, which verifier, at which version, when, the result and why; a
  database trigger refuses `satisfied = TRUE` with no `SATISFIED` record behind
  it. There is no manual boolean, no catalog field and no migration that grants
  it. Results are `SATISFIED | UNSATISFIED | UNKNOWN | NOT_APPLICABLE`, only the
  first clears, and **`UNKNOWN` is never promoted**. No verifier can satisfy a
  `HUMAN_CONFIRMATION` condition, and none in this repository writes one.
- **Eligible, RESOURCE-READY, implemented and enabled are four facts.** After
  Mission 1.8 `world-bank`, `eurostat` and `gdelt` are collector-eligible in any
  environment where the capabilities are verified, and `fred` joins them wherever
  `FRED_API_KEY` is configured — it is design-eligible and blocked everywhere
  else, including CI. `sros-source enable` refuses a source with no collector,
  and the orchestrator blocks acquisition under `NO-COLLECTOR-IMPLEMENTED`
  rather than dispatching a job nothing can run.

  **`resource_ready` was separated in Mission 1.9.2**, because a source can pass
  the gate while every resource it could ask for is refused — GDELT was in that
  state for two missions and "eligible" was the most specific word available for
  it. Eurostat is in it today. `sros-source readiness` derives all four and
  stores none: a persisted copy of a derivation is what §3 of
  `source-registry-v1.md` refuses for eligibility.
- **A source-level approval is not a resource-level one.** Each dataset or
  series is authorised separately, and one whose licensing scope was never
  established is refused. A collector receives an
  `AcquisitionAuthorizationContext` or it receives nothing.

  **An unestablished rights basis is refused unconditionally** (Mission 1.9.2):
  every other rule answers a question a particular review may or may not have
  asked, and *what authorises this at all* is not one of those. Where a review
  named the families it assessed, a family outside that list is refused too —
  **"nobody rejected this" is not "a reviewer approved it"**, and
  `require_dataset_family` only ever asked whether a resource could say what it
  is.
- **How much is a governance question too** (Mission 1.9.2). A reviewed
  `max_files_per_job` bounds what one job may take from a published bulk
  dataset, refused at load time without a stated basis, and a job that does not
  state its size is refused. **Absent means no ceiling was reviewed, not that
  any size is fine.** A collector choosing its own bound would be setting its
  own permissions.
- **Coverage is potential, never permission** (Mission 1.7, ADR-017).
  `registry.source_signal_coverage` and `source_behavior_coverage` say what a
  source COULD expose. A source may cover `entertainment` and be `PROHIBITED`;
  the eligibility view reads neither table and must never start. They carry no
  weight, no score and no confidence — one would be a per-source reliability
  coefficient, which is D-03, which is blocked. Behaviour coverage reuses
  Ontology V2 §3.4's `user_behavior` rather than defining a second vocabulary.
- **Silence is the commonest blocker, and it is doing its job.** After Mission
  1.8 twenty-seven sources are registered, **five** are approving and **four**
  are eligible. Bluesky publishes an open firehose needing no API key, and
  Hugging Face publishes open endpoints with documented numeric rate limits;
  both are `REQUIRES_REVIEW`, because their terms address none of the assessed
  activities. Reachability was never the question.
- **An approving state requires a GRANT, not the absence of a prohibition**
  (Mission 1.8, `source-registry-v1.md` §1 rule 8). The assessed use names six
  load-bearing activities — `automated_access`, `api_use`, `commercial_use`,
  `storage`, `derived_analytics`, `model_processing` — and each must be
  positively permitted on authoritative evidence. `NOT_ADDRESSED` on any of them
  blocks, whatever the other five say.

  This was prose from Mission 1.0 that nothing read, until Mission 1.7 approved
  a source with four of the six unaddressed and wrote the reason down in the
  review's own notes. `validate_source_registry` enforces it now. **Do not
  narrow the assessed use case to rescue a source**: the use case describes the
  product, and a permission obtained by describing a smaller product is a
  permission for a product we are not building.

### Collection — two collectors, and what bounds them

Since Mission 1.5 the World Bank Indicators collector exists
(`world-bank-collector-v1.md`) and is the reference architecture. Since Mission
1.9.3 the GDELT WEB-NGRAM collector exists too
(`gdelt-web-ngram-collector-v1.md`), reading a published gzipped file rather than
a paginated API. Five rules apply to both and to every collector that follows:

- **No authorization, no collection.** `collect` takes an
  `AcquisitionAuthorizationContext` as its first positional parameter, with no
  default and no overload that omits it. A collector that could build its own
  could approve itself.
- **Every resource passes `authorize_resource` before a socket opens**, and a
  refusal costs **zero** network calls.
- **No public signature accepts a URL.** A request names indicators, countries
  and years; the collector composes the path, and the host comes from the access
  profile the review approved. There is no fallback domain and redirects are not
  followed.
- **Retention and attribution come from governance**, not from the collector.
  `build_draft` has no parameter for either, so there is nothing to pass.
- **Exactly one file may import a network client**
  (`collection/transport.py`). The registry and compliance packages decide
  whether collection may happen and stay network-free.

Identity is three separate things and confusing any two is a defect:
`observation_key` says WHICH observation, `content_hash` says WHAT the source
said, and the record id follows from both. The retrieval time is in neither — it
would make every re-retrieval look like an upstream revision. The key's parts are
**escaped**, not restricted: a source publishes what it publishes, and a key
format that refused real values would drop them (Mission 1.9.3).

Four more rules apply where a collector reads a **bulk file** (Mission 1.9.3):

- **The reviewed ceiling is the review's.** `context.authorize_job_size` decides
  how much one job may take; a collector that defined its own bound would be
  setting its own permissions, and a request one file over is refused whole
  rather than split into two permitted jobs.
- **Operational bounds are ours and say so.** Compressed bytes, decompressed
  bytes, line length, rows scanned and records kept are `INTERNAL_SAFETY_POLICY`,
  labelled as such in provenance. **Absent means unasked, never unlimited**, and
  none of them is a quota anybody published.
- **Our ceilings truncate; the source's contract discards.** Hitting a record cap
  keeps what was accepted and says which bound stopped it. A malformed row
  discards its whole file, because the contract is documented and a deviation
  means a person is needed rather than a filter.
- **The route is resolved by name.** A source with two access profiles has a
  first one, and taking it silently authorises whichever the JSON happened to
  list first — which for GDELT is the deferred DOC API.

The registry is **global**: no `workspace_id`, no RLS policy, `SELECT` only for
the runtime role. It is administered by `sros-source`, never over HTTP.

This system is not a legal decision engine and its output is not legal advice.

### Normalization — what a canonical observation is, and is not

Since Mission 1.6 the RawRecord to NormalizedRecord boundary exists
(`normalized-record-v1.md`, `world-bank-normalizer-v1.md`). One adapter, for
World Bank, and six real canonical observations.

**This layer renames and reshapes. It does not decide.** Normalization answers
*what does this source observation structurally represent*, and stops. A field
that encoded "this indicates growing demand" would put an interpretation
somewhere that looks like a fact, and every stage downstream would inherit it as
one. Signal extraction interprets, claim extraction asserts, scoring evaluates —
three later stages, none implemented.

Six rules, and none is negotiable:

- **Unknown stays unknown.** A unit the source does not publish is
  `NOT_PUBLISHED`, never inferred from a metric name. A geography code no
  reviewer classified is `UNKNOWN`, never promoted to a country. Each is a state
  a consumer branches on, which beats a plausible value nobody can check.
- **Missing is never zero.** Zero is a measurement and absence is not. A layer
  that mapped both to `0` would make them permanently indistinguishable, and the
  constructor refuses a number beside a `NOT_REPORTED` state.
- **An aggregate is never a country.** `World` and `High income` are real
  entities, preserved as aggregates with their source code. Classification comes
  from a reviewed map where every entry records its basis, and from nothing else
  — not from a code's shape and not from its label.
- **A year is an interval, not January 1.** The canonical period carries its
  type, its label and a half-open `[start, end)`, so nothing downstream can read
  the start bound as an exact event time.
- **An unestablished timezone is stated, never chosen** (Mission 1.10, ADR-019).
  A source may publish a period label and no offset. `timezone_state` says which
  situation a period is in: `ESTABLISHED` keeps timezone-aware bounds and an
  event time, `NOT_ESTABLISHED` carries **naive** wall-clock bounds and
  `observed_at` is `NULL`. Storing an aware UTC datetime beside a note saying it
  is not really UTC would be a lie next to a disclaimer, because code reads the
  datetime.
- **A language is stated, never resembled, and never a place** (Mission 1.10).
  `CanonicalLanguage` keeps the source label, the vocabulary it came from, the
  mapping status and — only where a reviewed mapping establishes one — a
  canonical tag. `unmapped()` is the counterpart of
  `CanonicalGeography.unclassified()`. `ENGLISH` looks like `en`, and the first
  name that does not resemble its tag would be silently wrong.
- **Numbers are exact decimals, never floats.** Parsed from JSON text with
  `parse_float=Decimal`, stored as decimal strings, and free of artifacts from
  an intermediate representation.
- **Quality is structural, never epistemic.** `VALID | PARTIAL | INVALID` says
  whether the record could be represented. It is not a confidence, not a
  reliability and not a weight; those belong to the evidence model and mean
  something else entirely.

Identity is again three separate things: `observation_key` says WHICH
observation (inherited verbatim), `raw_record_id` says WHAT the source said, and
the row id says WHICH transformation of it. The normalization timestamp is in
none of them.

**Record kinds are a registry and a kind exists because DATA exists** (Mission
1.10). Two now: `numeric_observation`, and `lexical_frequency_observation` — one
occurrence count for one lexical term, one language, one period, and **no
geography key at all**. Widening the first to fit the second would have let a
World Bank record exist without a geography, which is the existing model getting
worse for a new source's sake.

That is a different rule from the one governing adapters. A vocabulary row lets
the model describe a shape and lets the database refuse an unregistered one; the
claim that **code** exists is `NORMALIZER_REGISTRY` and `IMPLEMENTED_NORMALIZERS`,
and GDELT is in neither.

**A revision is not an overwrite and an upgrade is not a replacement.** A revised
RawRecord produces a new normalized row with the previous one superseded; a newer
normalizer or schema version produces an additional row with the old one intact.
Which one downstream should read is **D-08**, open, and Mission 1.6 deliberately
did not invent it. Output may only change with a version bump: the same identity
producing different content is reported as `NON_DETERMINISTIC_OUTPUT`, never
written over.

**Eligible, enabled, implemented and normalizable are FOUR facts.** The fourth
was separated in Mission 1.6 because the planner's normalization block read "no
collector is implemented" — which Mission 1.5 made false while leaving
normalization exactly as unavailable. `normalization_block` now derives it from
what exists, and a future Eurostat collector with no normalizer stays blocked.

**Two adapters exist** (Mission 1.10.1): `world-bank-indicators-numeric` and
`gdelt-web-ngram-lexical`. Both are offline and deterministic, and both are
asserted so over the **AST** rather than over the file's text — a substring scan
fails on the docstring that explains the rule, and weakening it until it passes
is how a structural check stops checking (`testing-strategy.md` §23).

**A known absence is stated, never filled in.** Every GDELT normalized record is
`PARTIAL`, carrying `PERIOD_TIMEZONE_NOT_ESTABLISHED` and `LANGUAGE_NOT_MAPPED`,
because H-29 and H-30 are open. `VALID` would say nothing is missing when two
canonical facts are, and `INVALID` would make a record unreadable for a condition
that is universal and expected. The exact source label survives either way, so
answering an open question later is a normalizer version bump over records
already held — not a re-collection.

Normalization reaches **no network, no model and no embedding library**, not even
through `collection/transport.py`. `validate_normalization.py` asserts it by
parsing every import, and was probed against fourteen deliberate violations
before being believed.

### Signal — a derivation, never a labelled observation

Since Mission 1.11 the Signal contract exists (`signal-contract-v1.md`,
`signal-taxonomy-v1.md`, `signal-temporal-semantics-v1.md`, ADR-020). **The model
exists and no extractor does**: `SIGNAL_EXTRACTORS` is empty and `nlp.signals`
holds 0 rows.

```text
RawRecord -> NormalizedRecord -> SIGNAL -> Claim / Evidence -> Opportunity -> Score
```

Eight rules, and none is negotiable:

- **One observation is not a Signal.** A derivation whose assertion is
  recoverable from a single input's payload is that observation renamed. At
  least **two distinct source observations** must contribute, and distinctness is
  over `observation_key` — never over `normalized_record_id`, because one
  observation can have several normalized rows and counting rows would let a
  normalizer upgrade manufacture a contrast out of one observation. Two rows
  sharing a key are refused as `AMBIGUOUS_OBSERVATION_LINEAGE`. **D-08 is failed
  closed on, not solved.**
- **The Signal family is not the demand family.** `quantity_family` is
  `LEXICAL_FREQUENCY | MEASURED_SERIES` and says what kind of QUANTITY the signal
  is about. `PAIN / DESIRE / BEHAVIORAL / MARKET` classify demand, and neither
  derivation the two real sources support is evidence of demand — a GDELT term
  count may equally be a news event, a crisis, a celebrity or the weather.
  **Ontology V2 §3.6 is unchanged**; what stops being true is the claim that
  every row of that table carries a demand family. Three things were called
  "signal family" and now have three names (`signal-taxonomy-v1.md` §1).
- **Order and global instant are different facts.** `SOURCE_RELATIVE_ORDER` says
  which of two observations came first within one source stream;
  `COMPARABLE_INSTANT` places them on a shared timeline. **Neither is granted to
  GDELT**: H-29 blocks the second and the new **H-32** blocks the first. Label
  EQUALITY needs no timezone and is available, so a contrast between two terms
  inside one bucket is derivable today and a frequency change is not. A direction
  other than `NOT_APPLICABLE` requires an ordered basis, so no GDELT signal can
  carry one — enforced by the database.
- **`PARTIAL` does not mean unusable and `INVALID` is never derivable from.** A
  derivation declares the `SignalRequiredFact` values it needs and the model
  computes what each input withholds from that record's own quality reasons.
  Every GDELT record is `PARTIAL` and a within-bucket contrast needs neither
  thing it is missing.
- **A blocked derivation produces no Signal.** There is no lifecycle enum, no
  `BLOCKED` and no `INSUFFICIENT_DATA`: a row in a table of signals says a signal
  exists. A refusal is a returned value object with a closed reason code.
- **Magnitude is exact, typed and not a strength.** A `Decimal`, never a float,
  never bounded to `[0,1]`, and **no 0–100 cross-signal scale** — a GDELT term
  frequency and a World Bank population figure are not comparable measurements.
  The unit is inherited from the inputs or does not exist.
- **`derivation_confidence` is about the derivation.** A deterministic
  extractor's is `1.0`, and that is a statement about arithmetic, not about the
  market. It is not an `EvidenceScore`, not an evidence strength, and it is
  multiplied by nothing.
- **A Signal is not Evidence and resolves no contradiction.** Evidence is
  claim-scoped and adds direction, relevance, directness, reliability and an
  independence state; a Signal has no claim to be relative to. Lineage preserves
  the source and raw-record facts so aggregation can judge independence later,
  and **judges nothing here**.

Identity is deterministic over workspace, type, extractor and version, schema
version, the ordered contributing inputs, the parameter fingerprint and the
window — and excludes the OUTPUTS, so a changed magnitude under an unchanged
identity is reportable rather than absorbed into a new row. The research session
is **lineage, never identity**: two sessions deriving the same thing converge on
one signal, because two rows would read as two independent findings.

### Claim — the unit evidence accumulates against

Since Mission 1.2 a **Claim** is a persisted entity (Ontology V2.1 §17,
`claim-model-v1.md`, ADR-015). Five rules follow:

```text
Workspace -> Opportunity -> Claim -> Evidence -> Aggregation
```

- **A Claim is not a `ClaimType`.** `ClaimType` is an epistemic category a claim
  carries; there are exactly five of them and none is an identity. A Claim is an
  assertion with a `ClaimId`.
- **A Claim is not an Opportunity.** One opportunity carries several assertions
  that do not stand or fall together; aggregating at the opportunity level
  averages away what the four masses preserve.
- **Identity is stable; statements are revised append-only.** An aggregation that
  evaluated revision 2 must still be able to read revision 2. The previous
  revision is never modified.
- **Temporality is declared on the Claim, never inferred from the source.** The
  claim names a `claim_feature`; the half-life lives in the profile.
- **`ClaimLifecycle` is editorial, never epistemic.** `ACTIVE` and `WITHDRAWN`
  only. There is no `VALIDATED`: evidence changes, and a lifecycle derived from
  it would freeze a conclusion the evidence no longer supports.

A claim is not owned by the session that first met it (Ontology V2 §12, applied
to Claim). Sessions produce observations; the same claim accumulates evidence
across many of them.

### Evidence aggregation — defined, and not calibrated

Since Mission 1.1 the aggregation algorithm is defined
(`evidence-aggregation-framework-v1.md`, ADR-014). Five rules follow, and none is
negotiable:

- **`q_i = min(components)`.** The weakest required dimension, never a weighted
  average. A high value must not compensate for a critical weak one.
- **Duplicates cannot multiply.** Records sharing an origin form one group and
  the strongest member counts. Unknown provenance forms **one** group per claim
  and direction — it is never promoted to independent.
- **Support and contradiction are aggregated separately** and decomposed into
  four masses that sum to 1. There is no flat contradiction penalty.
- **No invented parameters.** No per-platform reliability coefficient, no
  universal half-life. A temporally sensitive claim with no authorised half-life
  reports `MISSING_TEMPORAL_PARAMETER` and produces no score.
- **`EvidenceScore` is a score, not a probability.** `82` does not mean an 82%
  chance the claim is true, and it is never published without
  `support_strength`, `contradiction_strength`, `conflict_mass` and
  `uncertainty_mass`.

Source POLICY status (Mission 1.0) is not epistemic reliability. An `APPROVED`
source does not produce better evidence.

### Blocked work

**`services/scoring` must not be implemented for production research.** D-03 is
resolved at the *framework* level only: the equations exist, their parameters
were never fitted, and no `CALIBRATED` profile exists. Framework Defined and
Profile Calibrated are separate gates (ADR-014, framework §14). An
`UNCALIBRATED` profile may be run only for synthetic or experimental work, and
only when explicitly labelled as such.

Do not invent a half-life, a damping constant, a per-source weight or a
contradiction penalty to make the engine produce a number. Failing closed is the
designed behaviour, not a gap to fill.

**No normalizer may be implemented for a source with no collector**, and no
normalization job may be dispatched for a source with no normalizer. The
orchestrator reports the second under `NO-NORMALIZER-IMPLEMENTED`, distinct from
the two acquisition gates because different work clears each.

**No signal extractor may be implemented before Mission 1.11.1**, and none
may derive a temporal GDELT signal while H-29 and H-32 are open. The model
refuses it; an extractor that worked around the refusal would be granting itself
a fact no source established.

**No collector may be implemented for a source that is not collector-eligible.**
D-07 is resolved and the registry exists. Two sources pass the gate; one has a
collector. The block is per source, and the orchestrator reports each by name
under one of two gates — `SOURCE-REGISTRY-GATE` when nothing is eligible,
`NO-COLLECTOR-IMPLEMENTED` when something is and nothing implements it.

Mission 1.4's debt is paid: `test_collector_conformance.py` asserts structurally
that the collector has no path to a URL outside `authorize_resource`, so the
guarantee is observed rather than architectural.

## Core principles

- Evidence before conclusions.
- Problem-first is valid, but not mandatory.
- Desire, curiosity, entertainment, creativity, learning, competition, social interaction, and other motivations are first-class opportunity drivers.
- Never treat an LLM opinion as observed market evidence.
- Distinguish observed facts, inferred signals, predictions, and recommendations.
- Preserve provenance for important data.
- Preserve uncertainty and confidence.
- Do not silently redefine domain concepts.
- Do not silently change architecture.
- Prefer small, testable, reversible changes.
- Avoid unnecessary complexity and premature microservices.
- Security, privacy, legal constraints, cost, and data quality are first-class concerns.

## Before implementation

For every non-trivial task:

1. Inspect the repository.
2. Read the relevant specifications and ADRs.
3. Identify dependencies and existing contracts.
4. State any ambiguity or contradiction before implementing.
5. Define acceptance criteria.
6. Implement the smallest coherent change.
7. Add or update tests.
8. Run relevant checks.
9. Update documentation when behavior or contracts change.
10. Summarize assumptions, evidence, tests, and remaining risks.

## Change control

If a requested change conflicts with an authoritative specification:

- Do not silently override the specification.
- Explain the conflict.
- Propose the smallest specification or ADR change needed.
- Wait for explicit authorization before changing foundational behavior.

If a concept must evolve, create a new version rather than mutating history without traceability.

## Evidence discipline

Any research claim presented by the product should, where technically possible, retain:

- source
- source type
- observation time
- extraction method
- provenance
- evidence level
- reliability
- independence
- confidence
- relevant raw/reference identifier

Copied, duplicated, or derivative content must not be counted as independent evidence.

## LLM discipline

LLMs are reasoning and synthesis components, not sources of truth.

When evidence is insufficient, output a hypothesis or uncertainty state rather than inventing a fact.

Never fabricate:

- sources
- metrics
- users
- prices
- market sizes
- competitor facts
- API results
- citations
- research outcomes

## Data collection

Use lawful, permitted, and technically appropriate acquisition methods. Respect source terms, robots directives where applicable, rate limits, authentication requirements, privacy constraints, and platform policies. Do not bypass access controls.

API keys and secrets must never be committed to the repository.

## Versioning

Foundational specifications use explicit versions in the filename, for example:

- `opportunity-ontology-v2.md` (current) — supersedes `opportunity-ontology-v1.1.md`
- `scoring-framework-v1.1.md` (current) — supersedes `scoring-framework-v1.md`
- `evidence-confidence-framework-v1.md` (current)
- `data-retention-policy-v1.md` (current)
- `evaluation-framework-v1.md` (current)

Material changes should create a new version and, when architectural, an ADR.

A superseded version is **never deleted**. It is retained as a historical record,
marked as superseded in `PROJECT_MANIFEST.md`, and its successor states in its
own §0 exactly what changed and under whose authority.

## Definition of done

A task is not complete merely because code exists.

It is complete when:

- behavior matches the specification,
- tests cover important behavior,
- failure modes are considered,
- observability is adequate,
- documentation/contracts are current,
- relevant quality checks pass,
- no known critical regression remains.
