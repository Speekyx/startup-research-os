# CLAUDE.md — Startup Research OS

Version: 1.35
Last amended: 2026-09-01 (Sprint 1 / Mission 1.15.10)

## Boot Sequence

Before performing any task, execute this reading order.

1. PROJECT_MANIFEST.md
2. docs/CLAUDE.md
3. docs/domain/opportunity-ontology-v2.2.md
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
18. docs/data/signal-derivation-runtime-v1.md
19. docs/data/claim-evidence-interpretation-contract-v1.md
20. docs/data/claim-interpretation-runtime-v1.md
21. docs/data/evidence-reliability-contract-v1.md
22. Relevant ADRs
23. Task-specific specifications

These documents are the authoritative source of truth.

**`opportunity-ontology-v1.md`, `opportunity-ontology-v1.1.md` and
`scoring-framework-v1.md` are superseded.** They remain in the repository as
historical records. Do not use them as the basis for implementation. See
`PROJECT_MANIFEST.md` §Superseded specifications.

Ontology V2 keeps V1.1's numbering for §1–§10, so an existing reference to
`opportunity-ontology-v1.1.md §N` with `N ≤ 10` resolves to the same rule in V2.

**V2.2 inherits V2.1 in full and amends one sentence** (§17.3): a Claim belongs
to *at most one* Opportunity, and may belong to none. Every other reference to
V2.1 resolves unchanged in V2.2.

## Version history

| Version | Date | Change |
|---------|------|--------|
| 1.35 | 2026-09-01 | **Exact decimals, and the first real TED Signal.** `ted-search-api@1.1.0` parses with `parse_float=Decimal` and renders through `canonical_number`, so a fractional tender value reaches jsonb as an exact STRING; `parse_int` stays unset because a JSON integer was never at risk. **The normalizer is NOT bumped** -- its output is unchanged, and what changed is the inputs it accepts, declared in `supported_collector_versions`. One bounded acquisition on 2023-03-01 in CPV division 90 produced **1 TRANSACTION_VALUE Signal**: support 3, 686545.02 EUR, `ABSOLUTE_DIFFERENCE`, `NON_TEMPORAL`. Two defects real data exposed: `cpv_division` never reached the composed query, and the cohort scope carried only the FIRST member's codes -- `procurement-value-contrast@1.0.1`. **No Claim, no Evidence.** H-36A/B, H-37, H-38 untouched |
| 1.34 | 2026-09-01 | **A third Signal quantity family, and a derivation that correctly produced nothing.** `TRANSACTION_VALUE` (ADR-029): the `procurement_notice` kind mapped to neither existing family, and `MEASURED_SERIES` could not be widened without making `metric` optional for every series signal ever written. `procurement-value-contrast@1.0.0` is NON-TEMPORAL by construction -- basis `NONE`, no date read, members ordered by amount -- keeps four monetary semantics apart, converts no currency, and is **not** willingness-to-pay. **0 real Signals**: the two EUR award totals are CPV 90 and CPV 66, which are two markets. **H-37 and H-38 stay OPEN** |
| 1.33 | 2026-09-01 | **The third record kind, and the first canonical procurement notices.** `procurement_notice` holds what neither existing kind could without getting worse, and carries no `observation.value` because a notice has no single measurement. `ted-search-api-notice@1.0.0`: one notice one record with lots structured inside it, four monetary semantics kept apart, no `price_paid`, no currency converted, every language kept with no canonical display value. **A published DATE does not become a moment** -- `observed_at` NULL, naive bounds, **H-37** open with the source value preserved. Three real notices normalized, idempotent, all `PARTIAL`. **No TED Signal, Claim or Evidence** |
| 1.32 | 2026-09-01 | **The first TED acquisition, and the first concrete TED resource.** A source-level approval is not a resource-level one: TED authorised `"datasets": []` and every resource failed closed, which is why `AUTHORIZATION_READY` sat beside `resource_ready` NO for six missions. **One** resource authorised -- eForms contract and award notices from 2023-03-01 through the Search API -- then `ted-search-api@1.0.0`, the third collector: four gates before a socket, one route with **no fallback**, bounds with **no defaults**, **no exhaustion mode**, four monetary semantics kept apart, no currency converted. **3 real RawRecords**, idempotent on re-run. **H-36A NOT ESTABLISHED, H-36B NOT ADDRESSED, no normalizer, no Signal, no Claim** |
| 1.31 | 2026-08-31 | **The authorization carries only reviewed routes, and an objective property of configuration is verified rather than human-confirmed** (ADR-028). `context.access` used to hold every registered access profile, so TED's context would have handed a collector the bulk route its review refuses by name -- with the transport's host allowlist derived from it. A `(source, profile)` may now declare a `route_authorization`, and the context carries those routes and no others. Two TED conditions that described objective properties of a collector that does not exist -- its route, its field selection -- moved from `HUMAN_CONFIRMATION` to `CAPABILITY` on **appended local review v2**, changing no policy conclusion. **The residual database-right acceptance stays human, is unrecorded, and still blocks** |
| 1.30 | 2026-08-31 | **Source permission is use-profile-specific** (ADR-027). Every review already answered a question about a use -- the catalog said so in prose since Mission 1.0 -- but the answer had no IDENTITY, so it could not be required, compared or matched, and the gate never saw it. Now a review records its `assessed_use_profile`, currentness is per (source, profile), and `evaluate_eligibility` requires the profile with no default. **`ted-eu` is `REQUIRES_REVIEW` under the commercial profile and `APPROVED_WITH_CONDITIONS` under the local one, at the same time.** Approval never transfers; the runtime declares its profile and never infers it |
| 1.29 | 2026-08-31 | **The deployment model is recorded: LOCAL-FIRST / SINGLE-OPERATOR.** The application runs locally for its operator and is not offered as a public multi-tenant SaaS -- but the research it produces is used to launch **commercial** products, so **local deployment never implies `NON_COMMERCIAL_USE`** and commercial-use rights are still reviewed. Workspace and RLS stay. No billing, customer accounts, team collaboration or cloud scaling unless explicitly required |
| 1.28 | 2026-08-31 | **The routes are documented; the gate has no vocabulary for them.** TED's own docs say the Search API is *"for analysis and reuse"* and *"primarily targeted at data reusers"*, naming commercial organisations and researchers as users; the Open Data Service publishes data *"for analysis and re-use"* with a **Connect your app** button. That is intended-use evidence and **not** a database-right grant, and a condition now says so. The real blocker moved: **every approval in this registry is an answer to a use case the model never records**, so a source cannot be blocked broadly and authorised narrowly. `ted-eu` stays `REQUIRES_REVIEW` at v5 |
| 1.27 | 2026-08-31 | **The dataset licence found, and H-36 still open.** The Publications Office's own DCAT record attaches `dct:license = COM_REUSE` to **every** `ted-1` distribution including the bulk XML download, and `COM_REUSE` carries `skos:exactMatch` to Decision 2011/833/EU -- so the licence on the bulk route IS the instrument already known to be silent. The search API's own Terms of Usage resolve to the same TED legal notice. H-36 splits into **H-36A** (does the right subsist? not established -- nothing names a maker) and **H-36B** (is it granted? not addressed). The blocker is now a drafted, unsent message to a named address |
| 1.26 | 2026-08-31 | **H-34 CLOSED PERMITTED; H-36 did not close.** Commission Decision 2011/833/EU was retrieved from the Publications Office Cellar and read in full: reuse is defined by PURPOSE, not by METHOD, so machine processing falls inside the grant. The same text contains **zero** occurrences of *sui generis*, *extraction*, *re-utilisation* or Directive 96/9/EC. All six load-bearing activities are now granted and `ted-eu` is **still REQUIRES_REVIEW** -- the blocker is no longer an activity in the matrix |
| 1.25 | 2026-08-31 | **H-34 stays OPEN, and the question got precise.** TED's governing instrument is now NAMED and proven -- Commission Decision 2011/833/EU, cited by TED's own legal notice -- and its text returned an empty body at five first-party EUR-Lex addresses. The grant says notices may be *reused*, and 'reuse' is defined in the document nobody could read. A second question surfaced: does the grant reach the sui generis DATABASE right, given that the access route is bulk extraction (H-36) |
| 1.24 | 2026-08-31 | **Demand-side expansion: nine sources examined, zero approvals, and that is the result.** Pinterest and Hacker News moved to RESTRICTED on retrieved terms; Bluesky's developer guidelines are now known to exist and could not be fetched. Two procurement sources registered -- the first lawful route to WILLINGNESS_TO_PAY as a TRANSACTION rather than a listed price. `ted-eu` has five of six activities granted and is blocked by one |
| 1.23 | 2026-08-31 | **Reviewed reliability governed, and none reviewed.** A reliability applies to a MEASUREMENT x PURPOSE scope, rests on retrieved first-party documents, is attributed to a person and is superseded rather than updated (ADR-026). Zero assessments exist, so all seven Evidence rows stay NON_SCORABLE and aggregation stays UNAVAILABLE -- **outcome B, and it is the design working**. D-03 loses one blocker and keeps four |
| 1.22 | 2026-08-31 | The **first complete Signal -> Claim -> Evidence pipeline**: `observed-signal-restatement@1.0.0` produced **7 real OBSERVED Claims, 7 revisions and 7 Evidence rows** from the seven real Signals. Deterministic, source-attributed, no LLM. GAP-5 resolved; a refused interpretation gets a run record, never a Claim (ADR-025). Reliability stays NULL and every record is NON_SCORABLE, honestly |
| 1.21 | 2026-08-31 | The **interpretation boundary** defined before anything crosses it: a Claim may precede its Opportunity, and a machine may not store an assertion nothing supports (ADR-024, Ontology V2.2). Contract and model only -- **0 Claims, 0 Evidence** |
| 1.20 | 2026-08-30 | First **source-relative temporal** extractor: `lexical-frequency-change@1.0.0`, two real signals and two real gap refusals. A gap is never bridged and an absent term is not a zero (ADR-023). H-29 untouched: `ORDERED_PERIODS`, no bounds, no `observed_at` |
| 1.19 | 2026-08-30 | **H-32 closed** on first-party GDELT evidence: the WEB-NGRAM stream is ordered. **H-29 stays open** — GDELT documents UTC for a *different* dataset whose date means something else. H-31 answered and refined. No extractor, no new signal (ADR-022) |
| 1.18 | 2026-08-30 | First two deterministic extractors, and **five real Signals**. `PARTIAL` proved usable in production: both GDELT inputs contributed because neither missing fact was one the derivation needed. A refused derivation gets a run record, never a Signal (ADR-021) |
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

### Deployment model — local-first, single-operator

Added in 1.29. **Placed first because it frames the invariants that follow**: it
decides what every source review's assessed use case is about, and it is the
reason the tenancy rule below survives having one operator.

Startup Research OS is intended to **run locally for its developer/operator**. It
is **not** intended to be offered as a public multi-tenant SaaS.

**The research it produces is used to discover, evaluate and launch commercial
SaaS and web products.** So the deployment is local and the purpose is
commercial, and those are two independent facts.

- **Local deployment does NOT imply `NON_COMMERCIAL_USE`.** This is the rule most
  easily taken backwards, and taking it backwards would produce exactly the
  narrowed assessed use case §Source governance forbids: a permission obtained by
  describing a smaller product is a permission for a product we are not building.
  **Commercial-use rights are still reviewed wherever they apply.**
- **Public redistribution and customer-facing data rights are out of scope**
  unless the deployment model changes. A source review that grants them is not
  wrong; a review that *depends* on them is out of scope.
- **Do not build billing, customer accounts, team collaboration or cloud
  scaling** unless a mission explicitly requires it.
- **Preserve the workspace and row-level-security architecture.** Being a single
  operator today is not a concrete reason to remove a tenant boundary, and
  re-adding one later is far more expensive than keeping it.
- **Optimise application UX and deployment for one local operator.**

**If the deployment ever becomes public, customer-facing, sold,
subscription-based or multi-tenant, the commercial profile must be reviewed again
from the top.** It is unreviewed today, and it must not be reached by drift.

**The open governance consequence.** Every approval in the source registry is an
answer to a use case the model does not record (Mission 1.15.4). The
`LOCAL_PRIVATE_RESEARCH` profile in `route-scoped-source-authorization-gap-v1.md`
is **local, not non-commercial**, and must not be renamed or read as
non-commercial when `assessed_use_profile` is built. Nothing in the TED reviews
rests on non-commercial status: `commercial_use` is `PERMITTED` there on its own
evidence, from v1.

### Source permission — scoped to the use it was granted for

Added in 1.30 (Mission 1.15.5, ADR-027). Placed here because it is the mechanism
the deployment model above needs in order to mean anything.

**A verdict has a subject.** Every policy review records the
`assessed_use_profile` it answered about. Two are registered:
`commercial-multi-tenant-research-v1` (what every review before Mission 1.15.5
assessed, and what a future public deployment must satisfy) and
`local-private-research-v1` (the current runtime).

- **Currentness is per `(source, profile)`.** Each profile keeps its own
  append-only version line, and a source may hold different current verdicts
  under different profiles without contradiction. `ted-eu` does.
- **The gate requires the profile, with no default.**
  `evaluate_eligibility(source, use_profile_id, …)`,
  `build_authorization(source, use_profile_id, …)` and
  `verify_source(source, use_profile_id, …)` all take it second and positional.
- **Never transfer approval between profiles.** A missing profile raises, an
  unknown one is refused, and a profile with no review is refused. **Nothing
  falls back** -- not to another profile, and not to the source's legacy verdict.
- **Runtime authorization must declare the active profile.** `SROS_USE_PROFILE`,
  read at the entry point. Never inferred from an environment name, the host, a
  container, a user count or the absence of billing: a profile is a governance
  fact and those are infrastructural ones, and the same binary in the same
  container can be operated under either.
- **`SourceRecord.review` is the LEGACY-profile review and is not an
  authorization input.** It survives so that every document written before
  ADR-027 stays true; an AST test asserts the three gate modules never read it.
- **A profile never widens what a source permits.** It narrows what we claim to
  do. `commercial_purpose` is true on BOTH profiles, because local is not
  non-commercial and a commercial-use right still has to be granted by the
  source's own evidence.
- **Never report a naked verdict.** A source's standing is a table keyed by
  profile. Generated catalog documents present the legacy profile and say so.

### Route binding — the authorization carries only what the review authorised

Added in 1.31 (Mission 1.15.6, ADR-028). Placed here because it is what stops
the profile above from being a label on an authorization that still hands a
collector everything.

**An access profile is a fact about the source; a route authorization is a fact
about us.** `AccessRestriction` verifies that the registry records exactly the
approved access profiles -- which TED cannot satisfy, because TED really is
reachable by bulk XML and deleting that row would be falsifying a fact about a
source in order to obtain a permission.

- **`context.access` carries the reviewed routes and no others**, where a
  `(source, profile)` declares a `route_authorization`. A blocked label has no
  endpoint to read, so there is no host to allowlist and nothing for the
  transport to be pointed at. That is the enforcement; `authorize_route` only
  makes the refusal say *refused by name* instead of *not found*.
- **An authorised route the registry does not record is refused**, not skipped.
- **`None` means unasked, not unrestricted.** Every entry before 1.15.6 is in
  that state -- and `source-route-binding` reports *unimplemented* rather than
  *satisfied* when it is absent, so a condition never rests on a restriction
  that does not exist. **GDELT is the named gap**: it carries a second, deferred
  DOC API profile that no review assessed, and its context still hands a
  collector both. Restricting it is a review act.
- **Field minimisation is asked before a request is composed.**
  `context.authorize_fields` refuses an excluded field by name, an unreviewed
  field and an unstated selection. Where a source supports field selection --
  TED's `fields` parameter does -- **collect-then-filter is not available as an
  excuse**, because a request that discarded the contact block afterwards
  retrieved the contact block. No method removes fields from a collected record.

### A condition is verified where it can be, and confirmed where it cannot

Added in 1.31. **An objective property of what a collector is CONFIGURED to do
belongs to a mechanical verification kind, not to a person.**

Writing one as `HUMAN_CONFIRMATION` creates a **bootstrap**: nothing can be
authorised until somebody confirms behaviour, and nobody can confirm behaviour
until the thing exists. TED sat in that loop for a mission with two such
conditions, and the loop's natural break is the wrong one -- write the collector
first, confirm it after.

**The boundary is unchanged and load-bearing.** A judgement, a risk acceptance,
a legal conclusion or a promise about future conduct stays `HUMAN_CONFIRMATION`,
and `source-review-guide.md` §9 still applies: *do not reword a legal obligation
until it sounds checkable -- that produces a verifier that checks something
else.* The new rule is upstream of it: **ask first whether the condition was
ever about a legal obligation at all.**

**What a configuration-verified condition establishes** is stated precisely,
because the distinction is the whole point: not *the collector follows the
rules*, which nothing here can establish, but *the configuration supplied to
authorization satisfies the policy constraints, and the authorization hands a
collector nothing else*. The remaining obligation is on the collector mission --
it must be built so it cannot execute without an authorized configuration.

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

**Single-operator deployment is not a reason to drop either layer** (§Deployment
model). The tenant boundary costs little to keep and a great deal to re-add.

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

### Collection — three collectors, and what bounds them

Since Mission 1.5 the World Bank Indicators collector exists
(`world-bank-collector-v1.md`) and is the reference architecture. Since Mission
1.9.3 the GDELT WEB-NGRAM collector exists too
(`gdelt-web-ngram-collector-v1.md`), reading a published gzipped file rather than
a paginated API. Since Mission 1.15.7 the TED Search API collector exists
(`ted-eu-search-api-collector-v1.md`), posting a composed JSON body to a
documented search endpoint. Five rules apply to all three and to every collector
that follows:

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

**Three adapters exist** (Missions 1.10.1 and 1.15.8): `world-bank-indicators-numeric` and
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

### Signal derivation — two extractors, and what bounds them

Since Mission 1.11.1 two deterministic extractors exist
(`signal-derivation-runtime-v1.md`, ADR-021) and **five real Signals** do:
`numeric-period-change@1.0.0` produced four from the six World Bank
observations, `lexical-frequency-contrast@1.0.0` one from the two GDELT ones.

- **The extractor computes; the model checks.** `ObservationInput` carries no
  payload, so the model cannot interpret; the extractor reads the payload to
  subtract. Neither does the other's job, and `packages/signal-model` still
  contains no extractor — asserted over the AST.
- **Grouping is what keeps it tractable.** Records are bucketed by a canonical
  key and only records sharing one can meet. A caller handing an explicit
  incompatible pair is refused with `INCOMPATIBLE_SERIES`, naming the field that
  disagreed.
- **`terms` is a required parameter for the lexical contrast.** One WEB-NGRAM
  file holds 223,342 rows and an unselected all-pairs sweep is ~2.5 x 10^10
  pairs; every bounded default would be a threshold nobody reviewed.
- **Ordering never comes from the database.** Numeric by canonical period start,
  lexical by term text verbatim. Input order enters the derivation identity, so
  an order chosen by the query optimiser would choose the identity.
- **`PARTIAL` is usable, and now proven so.** Both GDELT records carry
  `PERIOD_TIMEZONE_NOT_ESTABLISHED` and `LANGUAGE_NOT_MAPPED`, neither is a fact
  the contrast requires, and both contributed with no withheld facts. No quality
  string is branched on anywhere in either extractor.
- **Order and instant stay separate, and one closed without the other**
  (Mission 1.12, ADR-022). `ORDER_ESTABLISHED_WITHOUT_TIMEZONE` holds one
  `TemporalOrderCertification`: `gdelt`, resources `web-ngrams/1gram` and
  `web-ngrams/2gram`, with its basis and its scope recorded. It is scoped to a
  publication **stream**, which is why `ObservationInput` carries `resource_id`
  — `source_id` alone would let another GDELT dataset inherit the finding, and
  the same directory publishes an unreviewed `chargram` file a prefix match
  would have covered. An observation that cannot name its resource is refused.
- **An extractor never reads a clock or converts a timezone** (Mission 1.12.1).
  `astimezone`, `now`, `utcnow`, `localtime` and `tzinfo=` are absent from every
  module under `sros_nlp/extractors`, asserted over the AST. The adjacency step
  is computed in **label space** — the earlier label's own components advanced by
  one published bucket and formatted back into a label — so nothing becomes an
  instant. That arithmetic is licensed by the certification, not by the format.
- **A refused derivation gets a run record, never a Signal** (ADR-021).
  `nlp.signal_derivation_runs` holds one row per **execution**, written in the
  same transaction as the signals: N considered, M derived, K refused and why. A
  redelivery writes a second run row and zero new signals, which is the honest
  record — the signals are what is idempotent.
- **`signal.derive` routes to the acquisition queue**, like `normalize.`:
  bounded, CPU-cheap work over records already held. The `nlp` queue is sized
  for LLM-backed work.
- **`SIGNAL_DERIVATION` is its own capability**, between normalization and NLP
  extraction, with a derived block. `NLP_EXTRACTION` stays blocked by D-12 —
  whose reason is embedding versioning, true of classification and clustering
  and **false** of deterministic arithmetic.

### Claim — the unit evidence accumulates against

Since Mission 1.2 a **Claim** is a persisted entity (Ontology V2.2 §17,
`claim-model-v1.md`, ADR-015). Five rules follow:

```text
Signal -> Claim -> Evidence -> Aggregation
             |
             +-- at most one Opportunity, possibly none
```

**The arrow changed direction in Mission 1.13.** It read
`Workspace -> Opportunity -> Claim` while the schema said
`opportunity_id NOT NULL`, and the pipeline has always run the other way: a Claim
about a source fact exists before anybody has conceived of the product it might
justify. ADR-024 and migration 0016 made the column nullable; Ontology V2.2 §17.3
is the amended sentence.

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

### Interpretation — where arithmetic becomes an assertion

Since Mission 1.13 the interpretation boundary is defined
(`claim-evidence-interpretation-contract-v1.md`, `claim-epistemic-semantics-v1.md`,
`signal-to-evidence-semantics-v1.md`, ADR-024). Since Mission 1.13.1 **one
interpreter crosses it**: `observed-signal-restatement@1.0.0`
(`deterministic-observed-claim-interpreter-v1.md`,
`claim-interpretation-runtime-v1.md`, ADR-025), which produced **7 real OBSERVED
Claims, 7 revisions and 7 Evidence rows** from the seven real Signals.

Each layer is defined by the one verb it may perform: a RawRecord **preserves**, a
NormalizedRecord **reshapes**, a Signal **relates**, a Claim **asserts**, Evidence
**bears on**. A layer performing the verb above it is the bug this contract
prevents.

- **The claim boundary (C-1).** A Signal states a relation between its inputs; a
  Claim states a proposition about the world that observations outside the
  derivation could support or contradict. "SP.POP.TOTL rose from 82,905,782 to
  83,092,962" is the records. "World Bank reported Germany's population rose" is a
  claim about a publication. "Germany's population rose" is a claim about
  demography. "There is growing demand for German-language SaaS" is supported by
  none of it. **The failure prevented is a system that takes the first step and
  prints the third.**
- **A machine may not store an assertion nothing supports.** Enforced twice: a
  `DEFERRABLE INITIALLY DEFERRED` constraint trigger (migration 0016) and
  `NO_SUPPORTING_SIGNAL` in `build_claim`. Three exemptions, each for a reason —
  `HYPOTHESIS` **by definition** (requiring evidence would make the category
  unusable and push unsupported ideas into `INFERRED`, the exact failure), `MANUAL`
  because a person asserting and then looking is the ordinary research motion, and
  `WITHDRAWN` because a withdrawn claim's evidence may be gone.
- **No new entity for the interpretation step.** A candidate table is a second
  place an assertion can live, and one that lives outside `research.claims`
  escapes every rule here. The step produces an unpersisted `ClaimDraft`, written
  as claim + revision + evidence in one transaction or not at all.
- **A model is a reasoning mechanism, never the evidence.** An LLM may propose an
  interpretation; a `MODEL_DERIVED` claim citing no Signal is refused exactly as a
  deterministic one is. Its contribution is provenance
  (`interpretation_kind`, `model_version`, `prompt_version`), never a row in
  `scoring.evidence`. **`DETERMINISTIC` forbids a model version** — "deterministic"
  promises the claim can be regenerated, and a model in the path voids it.
  **No chain-of-thought is stored**, and there is nowhere to put one.
- **Identity is the proposition, not the prose and not a vector.**
  `proposition_key` is sha256 over the canonical facts asserted, unique per
  workspace. Two interpreters wording one fact differently produced **one** claim;
  a claim reworded in revision 3 is the same claim. **D-12 stays open** and nothing
  here depends on it. The research session is lineage, never identity.
- **Confidence is about the reading, not about the world.**
  `interpretation_confidence` on the revision is how confident the interpreter is
  that the statement correctly reads the Signals it cites. It is not evidence
  strength, not a probability and not a score — a deterministic restatement can be
  1.0 while the proposition is barely supported. **No universal thresholds**: "3
  Signals required" is an arbitrary number wearing the costume of a rule.
- **Evidence is claim-relative.** Direction, relevance and directness live on the
  Evidence row because a Signal has never heard of the Claim; one Signal may
  support A and contradict B unchanged. A generated row may not be `NEUTRAL` — a
  Signal bearing on nothing produces no row. An absent factor is `NON_SCORABLE`,
  never `0.5` and never `0.0`. `claim_id` is now `NOT NULL` and `claim_type` was
  dropped from `scoring.evidence`: two answers to one question eventually disagree.
- **Independence travels; the judgement does not happen here.** Two Signals from
  one publication stream are not automatically independent, nor automatically
  dependent. `source_id` is recorded and aggregation groups by origin. Record what
  you know, promote nothing.
- **GDELT lexical frequency alone never satisfies a demand claim.** Not weakly,
  not with low relevance, not with a caveat. News coverage is journalists
  publishing; demand is people wanting and paying. A low score would model it as a
  little bit of the right thing, and it is none of the right thing. An `OBSERVED`
  claim using market or user vocabulary is refused
  (`UNSUPPORTED_INTERPRETATION`).
- **H-29 and H-30 fail closed at this boundary too.** A Signal certified only for
  `SOURCE_RELATIVE_ORDER` cannot support a claim needing an instant
  (`INCOMPATIBLE_TEMPORAL_SEMANTICS`); a GDELT language label is its own identity
  and cannot become a named language (`INCOMPATIBLE_LANGUAGE_SEMANTICS`). A
  `HYPOTHESIS` is exempt from the evidence requirement, never from these.

### Claim interpretation — one interpreter, and what bounds it

Since Mission 1.13.1 `observed-signal-restatement@1.0.0` exists and is the only
thing that crosses the interpretation boundary. Three templates, one per
implemented Signal type, and **no fallback**.

- **Structurally OBSERVED, not defaulted.** `_CLAIM_TYPE` is a module constant,
  `interpret()` takes no claim-type parameter, and `validate_claims.py` fails the
  build on any `ClaimType.X` attribute access in the package where X is not
  `OBSERVED` — over the AST. There is no low-confidence-inferred escape hatch.
- **A Signal type with no template is `UNSUPPORTED_SIGNAL_TYPE`.** Generic prose
  over an unknown Signal would be a proposition nobody specified and nobody
  reviewed.
- **Attribution is the claim.** Every statement names the source and says
  "reported that". `Germany's population increased` is not OBSERVED from a World
  Bank record; `World Bank Open Data reported that "SP.POP.TOTL" for "Germany"
  increased…` is. The geography is the SOURCE's own name, never our canonical
  code — the code is what a reviewed mapping decided.
- **Three attribution facts come from the contributing normalized records** —
  resource, geography name, term and language schemes — because the Signal's
  scope does not carry them. Disagreement is `AMBIGUOUS_SIGNAL_LINEAGE` and
  absence is `SIGNAL_LINEAGE_UNAVAILABLE`; the interpreter refuses rather than
  picks. It never reads a RawRecord.
- **H-29 in the wording.** "source bucket" and "the preceding source bucket",
  never a clock, a date or an alignment. `observed_at` is written NULL. Each
  template accepts only the temporal bases it can phrase and refuses the rest.
- **H-30 in the wording.** "under source language label ENGLISH", never "in
  English". `canonical_tag` is never read, asserted over call arguments and
  subscripts.
- **The vocabulary guard exempts QUOTED source data** (Mission 1.13.1 §10). A
  GDELT term is arbitrary text: `market`, `demand` and `pain` are ordinary
  English words a news corpus contains, and refusing them would refuse the most
  faithful restatement available. Matching is over TOKENS of the interpreter's
  own prose — `supermarket` is not `market`. **The template is the primary
  protection**; no template contains the word `demand`.
- **Identity is the proposition and excludes the magnitude.** A source revising
  187,180 to 187,200 restated the SAME proposition, so a re-interpretation
  appends revision 2 rather than creating a second claim. Revision 1 is never
  modified. For a contrast, where `direction` is NOT_APPLICABLE, the relation
  comes from the SIGN of the magnitude and is part of identity while the value
  is not. `proposition_facts` stores the preimage, so the key can be verified
  rather than trusted (ADR-025).
- **Every evidence factor is a decision with a reason, and the absent one is the
  important one.** `SUPPORTS`; relevance and directness 1.0 because the claim
  restates that Signal and nothing else; extraction confidence 1.0 because a
  format string either read the facts or raised; `UNCATEGORISED` for both sources
  because a population count is not market activity and a news frequency is
  nobody's behaviour; independence `UNKNOWN`; evidence level 1. **Reliability is
  NULL** — purpose-relative, D-03 blocked — so every record is `NON_SCORABLE`
  with `MISSING_RELIABILITY` and the seven real claims aggregate to no score.
  That is the honest answer, not a gap to fill.
- **Claim, revision and evidence are written in ONE transaction.** The evidence
  requirement is a deferred trigger firing at COMMIT; evidence in a second
  transaction is too late by construction.
- **A refused interpretation gets a run record, never a Claim** (ADR-025).
  `research.claim_interpretation_runs` holds one row per EXECUTION. A redelivery
  writes a second run row and zero new claims, which is the honest record — the
  CLAIMS are what is idempotent, and this is not exactly-once.
- **GAP-5 is resolved.** `research.claim_interpretation_inputs` records every
  Signal a run CONSIDERED with its role — `CITED`, `EXCLUDED`, `REFUSED` — and
  why. `EXCLUDED` was never attempted; `REFUSED` was attempted and rejected, and
  collapsing them loses which happened. It hangs off the RUN, because a Signal
  considered and not cited has no Claim to hang off.
- **`claim.interpret` routes to the acquisition queue**, like `signal.` and
  `normalize.`. No parallel AI worker subsystem was created.
- **`CLAIM_INTERPRETATION` is its own capability**, after `SIGNAL_DERIVATION`,
  with a derived block. `PLANNER_VERSION` is `1.4.0`.


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

### Evidence reliability — reviewed, never inferred

Since Mission 1.14 reliability has a governance contract
(`evidence-reliability-contract-v1.md`, `evidence-reliability-review-guide-v1.md`,
ADR-026). **The machinery exists and no assessment does**: zero rows in
`epistemic.reliability_assessments`, so all seven Evidence rows remain
`NON_SCORABLE` with `MISSING_RELIABILITY`.

- **Reliability answers one question**: how dependable is this kind of
  measurement, for this kind of proposition. Not how permitted the source is,
  not how well-known, not how carefully we read it, not how much it bears on the
  claim.
- **The scope is measurement × purpose**, matched in full or not at all:
  `source_id`, `resource_id`, `record_kind_id` name the measurement;
  `claim_type` and `proposition_kind` name the purpose. `world-bank` alone
  matches nothing, so the framework's own example resolves with no special case
  — a population record used for a demand proposition has a different kind and
  matches nothing at all. `proposition_kind` is the `proposition_facts`
  discriminator Mission 1.13.1 already writes.
- **Seven Evidence rows collapse to three scopes**, and stay three however many
  observations arrive. That ratio is the design's whole justification: a scope
  narrow enough to stay purpose-relative and broad enough for a person to
  review.
- **Compliance is not reliability, in both directions.** An `APPROVED` source
  does not produce better evidence and a `RESTRICTED` one does not produce
  worse. Enforced by a separate schema with no policy column, and by an AST test
  that excludes docstrings so the paragraph explaining the rule cannot fail it.
- **A value rests on retrieved first-party documents.** `"The publisher is
  reputable"` is a sentence, not a basis; `REVIEWER_DOCUMENTED_JUDGEMENT` is
  permitted alongside documents and refused alone, by a deferred trigger. Full
  documents are never stored — a reference, a section, a short finding, an
  excerpt capped at 1000 characters, the same discipline
  `registry.source_policy_evidence` uses.
- **A value states what bounds it.** `stated_limitation` is required: a
  reliability with no stated failure mode is a number nobody can argue with.
- **There is no `MODEL_GUESSED` origin, and closure is the point.** A model may
  help a reviewer read documentation and may not be the epistemic source. The
  three origins are `HUMAN_REVIEW`, `DOCUMENTED_METHOD`, `CALIBRATED_EMPIRICALLY`.
- **Human review is not calibration.** A `HUMAN_REVIEW` assessment may not name
  a calibration dataset and a `CALIBRATED_EMPIRICALLY` one must — refused both
  ways. `REFERENCE_PROFILE_V1` stays `UNCALIBRATED` however many assessments
  exist.
- **Unknown is the absence of a row, not a value.** `0.5 because unknown`,
  `0.8 because reputable`, `1.0 because official`, `0.9 because government` and
  `0.0 because we do not know` are all measurements, and `q_i = min(components)`
  must never see one nobody made. **The system stays capable of producing no
  score**, which is what makes a score mean something when one appears.
- **Zero, one, many are all defined.** Zero → `NO_APPLICABLE_ASSESSMENT`; all
  superseded → `SUPERSEDED_ONLY`, deliberately distinct because *reviewed and
  withdrawn* is a different fact from *nobody looked*; one → `RESOLVED`; more
  than one → **refused**. Never the closest, never the maximum, never the mean.
- **Resolved late, bound explicitly** (ADR-026 Decision 2). The result records
  which assessment id and version produced each number, so a score's
  coefficients can be reconstructed. A value already on the Evidence row wins
  and consults nothing — one answer per question, by construction.
- **No factor implies another.** `resolve_reliability` takes scope, candidates
  and supplied, and nothing else. Relevance, directness, extraction confidence
  and claim interpretation confidence are all `1.0` on the real rows and none of
  them is an argument.
- **Assessments are GLOBAL.** A statement about a published dataset's
  measurement contract is not a statement about a tenant, and per-workspace
  review would give one question several answers. No `workspace_id`, no RLS
  policy, `SELECT` only for the runtime role — **no tenant data, so no leakage
  path**, which is stronger than a correct policy.
- **The resolver lives outside `packages/evidence-aggregation`**, whose guard
  forbids naming a source at all. The guard was left untouched rather than
  narrowed, and the resolver carries its own no-source-id test.

**Reliability does not solve missing evidence families.** Even a reviewed value
for all seven rows would establish nothing about pain, desire, willingness to
pay, pricing power, competition, distribution, retention or revenue potential.
It decides whether the evidence the system HAS can be scored, not whether it is
evidence of the thing anybody wants to know.

### Demand-side sources — nine examined, none usable

Since Mission 1.15 the portfolio has been reviewed against the eight business
evidence families the product needs (`demand-side-source-expansion-v1.md`,
`demand-side-source-coverage-v1.md`, `demand-side-source-priority-v1.md`).
**29 sources registered, 5 approving, 0 collector-eligible for any demand-side
family.**

- **Six of eight families have no approving source**, and two — Pricing and
  Retention — have no registered candidate at all. The two families that DO have
  an approving source have a weak one: `openalex` for distribution is
  scholarly-record discovery rather than a marketing channel, and `gdelt` for
  user behaviour is news-corpus activity. **No approving source observes an
  individual doing anything.** Retention's obstacle is
  structural rather than legal: it needs the same subject observed twice, and
  everything in the portfolio is an aggregate or a one-shot public record. **No
  proxy is proposed**, because a proxy nobody can validate is worse than an
  acknowledged gap.
- **WILLINGNESS_TO_PAY gained its first candidates.** `ted-eu` and `usaspending`
  record contract awards: what a buyer paid a named supplier. `LISTED_PRICE` and
  `TRANSACTION` are different evidence classes and a pricing page is only ever
  the first — the distinction the portfolio had no source able to make.
- **`ted-eu` is the closest any blocked source has come.** One retrieved sentence
  grants five of six load-bearing activities: *"the procurement notices ... can
  be freely reused, for commercial or non-commercial purposes"* — a GRANT, not
  an absence of prohibition. `model_processing` is `NOT_ADDRESSED` and rule 8
  blocks whatever the other five say. Recording it otherwise would be the
  narrowing of the assessed use case Mission 1.8 forbids: this product includes
  LLM processing, and a permission obtained by describing a smaller product is a
  permission for a product we are not building.
- **Two hopeful maybes became definite noes.** Pinterest — the catalog's best
  DESIRE hypothesis since Mission 1.7 — prohibits storing API information at all
  (*"call the API each time"*), prohibits automated extraction and ML training,
  and requires explicit written authorization for competitor-research features,
  which names this product. Hacker News publishes an API stating *"There is
  currently no rate limit"* while Y Combinator's Terms prohibit *"data mining,
  robots, scraping"* and commercial derivative works over Site content. Both are
  RESTRICTED on retrieved evidence.
- **Bluesky's question got smaller.** Its developer guidelines exist — named by
  Bluesky's own documentation domain — and returned an empty body. The user
  Terms, re-retrieved at the version effective 15 September 2025, remain silent
  on all ten activities. H-33.
- **A failed retrieval changes nothing.** Reddit and Stack Exchange were
  unreachable from the review environment and gained **no review version** in
  either direction. No mirror, cached copy, alternative page or community summary
  was used to infer terms, and no bot protection was bypassed. An unresolved
  question stays visibly unresolved.
- **Coverage is still potential, never permission.** Both new sources record
  signal coverage and neither is approving. Both facts hold at once, and the
  registry exists to keep them apart.

**Reliability solved scorability; source expansion is what would solve
relevance — and it has not yet.** Even a perfect reliability review of all seven
existing Evidence rows would establish nothing about pain, desire, willingness to
pay, competition, distribution or retention.

### TED-EU — official routes documented, and a gap in our own model

Mission 1.15.4 re-reviewed TED against the system's **actual** use -- local,
private, one developer, no redistribution, no resale, no training
(`ted-eu-local-private-research-review-v1.md`,
`route-scoped-source-authorization-gap-v1.md`). Review v5. **Verdict unchanged.**

**A user summary was excluded before anything else** (§32). A file describing a
written Publications Office reply exists outside the repository and is a
transcription that says so itself. Classified `USER_SUPPLIED / NON_AUTHORITATIVE`,
not cited, not entered as evidence, not deleted. **No source in the catalog
carries an `OPERATOR_CORRESPONDENCE` row**, asserted as a tripwire so the first
one is a visible diff. H-36 is exactly where Mission 1.15.3 left it.

**Local use creates no permission.** *"It is local, therefore anything is
allowed"* is not an argument and nothing rests on it. What the narrower use
changes is which question is worth asking: not *may we mirror the corpus
commercially*, but *do the official query routes document a purpose that covers
narrow local research*.

**They do, in the operator's own words.** The Search API *"allows access to
published procurement notices for analysis and reuse"*, is *"primarily targeted at
data reusers"*, requires no authentication, and names *"Commercial Organisations:
Integrating TED data into platforms to provide added-value services"* and
*"Researchers: Analysing public procurement trends and patterns"*. The TED Open
Data Service publishes the data *"for analysis and re-use"*, invites use *"in your
research and applications"*, and offers a **Connect your app** button to
*"retrieve live results directly into Excel, Power BI, or any application that can
get data from the web"*. Analysis, reuse, integration, commercial use, repeated
access and automated access are each named by the operator about its own route.

**And that is intended-use evidence, not a rights grant.** Nothing on either route
mentions the sui generis database right. **Condition 11** records the distinction
so a later reader cannot collapse them, and the Search API is nowhere framed as a
way around H-36 -- the argument rests on documented purpose, never on the route
transferring smaller chunks. The Open Data Service's own invitation to *"extract
custom datasets across many notices"* uses the Directive's verb and is recorded
as striking and load-bearing for nothing.

**Two practical findings.** The Search API request body carries a **`fields`**
parameter, so minimisation happens AT acquisition rather than after it. And
coverage is recent and partial: eForms from **1 March 2023**, Standard Forms only
28 August 2023 to 26 January 2024 as a *"proof of concept"* slice of six form
types -- a bound on what research the route could support, recorded so a collector
does not discover it from an empty result set.

**THE REAL BLOCKER MOVED, and it is ours.** The system's use is local and a narrow
official-route profile would be defensible; the registry cannot express it.
`build_authorization('ted-eu')` returns exactly one reason -- *"policy review is
REQUIRES_REVIEW"* -- and there is no route, resource or profile argument that
could change it. Searching the contracts and acquisition packages for
`use_profile`, `deployment_profile`, `LOCAL_PRIVATE` or `MULTI_TENANT` returns
**zero matches**.

The finding underneath is not about TED: **every review in this registry already
assessed a use case, and the model never recorded which one.** Twenty-eight
sources cost nothing for it because one product was being assessed. TED is the
first source whose product has two shapes at once, and the model has one slot.

**Three ways to hack it, all worse than the gap.** Flipping the verdict makes
every consumer report TED approving for the commercial use case that is still
unresolved -- the silent migration §8 exists to prevent. Two current reviews means
two answers to one question. A use-profile condition still needs the flip to get
past the gate.

**The minimal extension is proposed and not built**: record
`assessed_use_profile` on a review (every existing one is
`COMMERCIAL_MULTI_TENANT`, which is what they DID assess), allow one current
review per profile, thread the profile through `evaluate_eligibility` and
`build_authorization`, and have the runtime **declare** its profile from
configuration rather than infer it. A profile the review does not name is
refused. It needs an ADR and a mission of its own -- doing it as a side effect of
a TED mission would be the change-control violation §Change control describes.

**Unchanged:** H-34 `CLOSED PERMITTED` and not reopened; every activity assessment
byte-identical between v4 and v5; all ten v4 conditions carried forward verbatim;
personal-data minimisation intact; model training **not authorised**; embeddings
blocked by D-12; bulk XML **still blocked**; `ted-csv` still a separate review.

### TED-EU — the licence found, and the question externalised

Mission 1.15.3 exhausted the first-party dataset-level material
(`ted-eu-database-right-clarification-v1.md`,
`ted-eu-database-right-clarification-request-v1.md`,
`ted-eu-h36-legal-review-packet-v1.md`). Review v4. Verdict unchanged.

**The question Mission 1.15.2 did not ask.** Is a licence attached to the
assembled DATASET, as opposed to the individual documents? **Yes.** The
Publications Office publishes TED in its own open-data catalogue, and the DCAT-AP
record for `ted-1` declares `dct:license = COM_REUSE` on **every** distribution
-- including *"Last daily editions of procurement notices in bulk download"*. The
dataset node itself carries no licence, no `dct:rights` and **no `dct:creator`**;
`dct:publisher` is the Publications Office.

**And the licence IS the Decision.** The `COM_REUSE` authority concept carries
`skos:exactMatch` to `http://data.europa.eu/eli/dec/2011/833/oj`. The
machine-readable licence on the bulk route resolves, by the publisher's own
assertion, to the instrument Mission 1.15.2 read in full and found silent on
database rights. The TED Search API's OpenAPI document has a "Terms of Usage"
section whose entire content is a link to the same TED legal notice. **Both
routes are governed by the same silence, and the silence is now known to be
complete**: the TED notice, the Publications Office notice, the europa.eu notice,
the 20,015-character data.europa.eu notice, the bulk page, the package HTTP
headers and the API specification contain **zero** occurrences of *sui generis*,
*database right*, *extraction*, *re-utilisation* or Directive 96/9/EC.

**`appliesTo licence-domain/DATA` is not a database-right grant.** The tempting
over-read. `DATA` is defined in the same authority table as a *"set of values of
qualitative or quantitative variables"* -- a subject class, not a class of right
-- and the whole `licence-domain` scheme is `CODE`, `DATA`, `METADATA`,
`W_LIT_ART` and a placeholder. **There is no `DATABASE` domain**, so the absence
is not a deliberate choice either. `CC_BY_4_0` carries the same two values.

**H-36 split, because the halves have different addressees.**

- **H-36A -- does the right subsist?** **NOT ESTABLISHED, either way.** Directive
  96/9/EC Article 7(1) gives the right to a **maker** showing **substantial
  investment**; nothing retrieved names one. The catalogue names a *publisher*
  and no creator, notices are filed by contracting authorities across the Union,
  and Article 11 makes subsistence turn on facts about that maker. A legal
  question about facts nobody has published.
- **H-36B -- is it granted or waived?** **NOT ADDRESSED for both routes.**
  Article 7(3) confirms the right *can* be granted by contractual licence.
  `COM_REUSE` does not.

**The sharpest fact, recorded and not relied on.** The same portal declares
**CC BY 4.0** -- whose Section 4 expressly grants the right *"to extract, reuse,
reproduce, and Share all or a substantial portion of the contents of the
database"* -- on **12 of 48** distributions of the separate `ted-csv` dataset,
published by **DG GROW**, including contract award notices for 2020, 2021 and
2022. The other 36 are `COM_REUSE`, and the two **overlap**:
`ted-contract-award-notices-2017-2021.zip` is CC BY 4.0 while
`ted-contract-award-notices-2018-2023.zip` is `COM_REUSE`. Nothing on `ted-1`
carries CC BY 4.0. **Selecting the favourable licence would be selecting a
licence by selecting a filename**, so it is asked about rather than used --
condition 10 forbids carrying a licence across resources.

**A correction to Mission 1.15.2.** That review reasoned the search API was a
smaller taking than bulk. The API's own specification documents a **scroll mode
with no limit on the number of retrievable notices**, and Article 7(5) reaches
repeated and systematic extraction of insubstantial parts regardless. Both routes
stay unresolved and **no route is preferred**.

**No PSI chain exists** (§12). Directive (EU) 2019/1024 appears nowhere; the one
occurrence of Directive 2003/98/EC is inside the data.europa.eu **privacy**
statement as a personal-data processing basis. Recorded as separate legal
context, never as controlling evidence.

**The blocker is now a message.** `ted-eu-database-right-clarification-request-v1.md`
is written and **unsent** -- addressed to `op-copyright@publications.europa.eu`,
the route TED's own legal notice publishes for SIMAP copyright issues, with
`GROW-D2@ec.europa.eu` for the CSV question. The repository may PREPARE a message
and may never imply it was delivered: there is no `sent_at` anywhere, and a test
asserts it. Legal review is step two, and
`ted-eu-h36-legal-review-packet-v1.md` exists so it starts from established facts.

**Verdict `REQUIRES_REVIEW` at v4.** H-34 untouched, six activities still
`PERMITTED`, all nine v3 conditions carried forward verbatim plus a tenth.

### TED-EU — every activity granted, and still blocked

Mission 1.15.2 retrieved and read the governing instrument
(`ted-eu-governing-decision-review-v1.md`,
`ted-eu-database-right-review-v1.md`). Review v3.

**The retrieval.** EUR-Lex failed again — six representations across two
missions, including the Official Journal full-issue HTML. The text came from the
**Publications Office's own Cellar repository**, addressed by the Cellar
identifier the Publications Office publication record itself publishes. Four
pages, Articles 1–13, 16,748 characters. A first-party representation reached by
following the publisher's own identifiers; not a mirror.

**H-34 — CLOSED PERMITTED.** Article 3(2): reuse *"means the use of documents by
persons or legal entities of documents, for commercial or non-commercial
purposes other than the initial purpose for which the documents were
produced"*. The definition is framed by **purpose** and enumerates no acts —
method does not enter. Article 4 makes all in-scope documents available on that
footing; Article 6(2) says conditions *"shall not unnecessarily restrict
possibilities for reuse"* and lists three, none about method; the Article 2(2)
exclusions are classes of **document**; and the only manner-of-use prohibition in
the whole instrument is Article 2(4)'s reuse *"calculated to deceive or to
defraud"*.

**This is not silence about machine learning.** It is a grant whose operative
term is defined broadly enough that method does not enter — a different thing,
and the thing that permits closing without the literal words.

**Scope of what closed.** Inference, extraction, classification, structured
analysis. **Model training was not assessed and is not authorised** — the
Decision does not distinguish methods, but training raises Article 2(2)(b)'s
third-party-rights exclusion in a materially different form and the engine does
not need it. Embeddings are unassessed for implementation and blocked
independently by D-12. Both recorded as a **condition** on v3, because a single
`PERMITTED` field cannot carry a boundary.

**Three new conditions from the Decision.** Article 6(2)(b) obliges the reuser
**not to distort the original meaning or message** — the condition with the most
direct bearing on the claim layer, making an epistemic requirement a legal one
too. Article 2(4) forbids deceptive or fraudulent reuse. Article 6(2)(c) records
the Commission's non-liability.

**H-36 — NOT CLOSED, and the unknown became an established absence.** The full
text contains **zero** occurrences of *sui generis*, *extraction*,
*re-utilisation* or Directive 96/9/EC; its two occurrences of *database* are an
exclusion for unpublished research and an example inside the definition of
structured data. The Decision is framed throughout around **documents**
(Articles 1, 2(1), 3(1)); the collection they sit in is never mentioned. Article
2(2)(a) excludes industrial property by name and the database right is not in
that list — the instrument neither grants over it nor excludes it, it **does not
reach it**.

One fact cuts the other way and is recorded: SIMAP *system metadata* is CC0 1.0,
and CC0 waives sui generis rights where the dedicator holds them. That shows the
Publications Office addresses this right when it means to — and it applies to
metadata, not to the notice corpus a collector would extract.

**The verdict.** Permitted plus unresolved gives `REQUIRES_REVIEW`. **All six
load-bearing activities are granted and the source is still blocked**, which is
uncomfortable and correct: the remaining question is not an activity in the
matrix, it is whether a different body of rights sits over the same data.

**The blocker changed kind.** It was *"retrieve a document"*. It is now *"decide
a legal question the documents do not answer"* — the first item in the queue a
further document search cannot settle, because the documents have been read.
Bulk XML and the search API are analysed separately and both are unresolved,
with different exposure; **no collector route was forced**.

### TED-EU — one human decision left, and it is the right one

Mission 1.15.6 (`ted-eu-authorization-bootstrap-v1.md`, ADR-028). Local review
**v2**, appended.

Three of TED's four conditions under `local-private-research-v1` now verify
`SATISFIED` against configuration: `ted-attribution`,
`ted-official-route-only` (`source-route-binding`) and
`ted-personal-data-minimisation` (`source-field-minimisation`). The routes are
`ted-search-api` and `ted-open-data-sparql`, the Search API is the **preferred
first implementation route**, and `ted-bulk-xml` is refused by name and absent
from the context. `ted-open-data-sparql` was registered as an access profile in
the same mission, because the review authorised a route the registry had never
recorded.

**`ted-database-right-residual-exposure-accepted` is OUTSTANDING and stays
`HUMAN_CONFIRMATION`.** Nothing in this repository can satisfy it: the human
branch is reached before any configuration is consulted, and the database
refuses a hand-set boolean with no verification behind it.

**No acceptance has been recorded.** The exact statement an operator would have
to record is written down in the bootstrap document §6.2, and **writing it down
is not recording it**. The existence of that mission is not acceptance, and
neither is the fact that the deployment is local.

**Nothing else moved.** H-36A NOT ESTABLISHED and H-36B NOT ADDRESSED under both
profiles. Commercial profile still `REQUIRES_REVIEW`. Model training not
authorised, embeddings blocked by D-12, redistribution not permitted, bulk XML
and `ted-csv` blocked at the route gate and again at the resource gate. Local
review v1 was not rewritten: v2 carries every assessment, condition, open
question and evidence row unchanged and differs in exactly two condition
classifications.

### Blocked work

**`services/scoring` must not be implemented for production research.** D-03 is
resolved at the *framework* level only: the equations exist, their parameters
were never fitted, and no `CALIBRATED` profile exists.

**Mission 1.14 closed one of D-03's blockers and left four standing.** What is
resolved is the *definition* of reliability and who may establish one. What
remains open: no reviewed value exists for any scope in use, no `CALIBRATED`
profile exists, no authorised half-life exists for temporally sensitive claims,
and the level thresholds are structural minimums rather than fitted values.
Reliability governance is not calibration and does not become it by being
careful. Framework Defined and
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

**Sequential WEB-NGRAM derivation is implemented since Mission 1.12.1**, by
`lexical-frequency-change@1.0.0` and by nothing else. It asks the Mission 1.12
certification for its stream and its label scheme before comparing anything;
order is never inferred from a label that happens to sort.

**Two rules bound it, and both are ADR-023.** A pair derives only when its labels
are **exactly one published bucket apart** — anything else is
`NON_CONTIGUOUS_SOURCE_BUCKETS`, because a change computed across a bucket
nobody read is indistinguishable from one that happened. And **a term absent
from a bucket is absent, never a frequency of zero**: zero-filling is the most
natural thing to do to sparse lexical data and is wrong in a way nothing
downstream can detect.

**Rolling windows, moving averages and momentum are still not implemented.**
Temporally permitted is not extractor specified, and each needs its own decision
about what a gap means for *that* operation.

**Cross-source temporal alignment stays blocked by H-29**, along with any
`observed_at`, any `TIMESTAMPTZ` conversion and any "as of" wall-clock claim.
GDELT documents UTC for **Web News NGrams 3.0**, a different dataset whose `date`
is when an article was seen rather than a 15-minute aggregation bucket; that
sentence establishes nothing about ours.

**Only DETERMINISTIC OBSERVED interpretation is implemented**, by
`observed-signal-restatement@1.0.0` and by nothing else. **`INFERRED`,
`PREDICTED` and `RECOMMENDED` generation is not written and is not partially
written**: there is no module for it, no branch to reach and no parameter that
would select one. An inference needs a stated reasoning step, and adding one is
a version bump with a document behind it — not a flag.

`MODEL_DERIVED` remains unused. `validate_claims.py` fails the build on a model,
network or embedder import anywhere in the interpretation layer, and on a write
to any later-stage table.

**Opportunities and scoring stay blocked.** A Claim may exist without an
Opportunity, which is what makes Opportunity formation a separate decision
rather than a precondition — and Mission 1.13.1 created none. Nothing unblocks
`services/scoring`: D-03 is resolved at the framework level only, no
`CALIBRATED` profile exists, and every one of the seven real Evidence rows is
`NON_SCORABLE` for want of a reviewed reliability.

**The seven Claims establish no pain, desire, willingness to pay, pricing power,
competition gap, distribution feasibility, retention or revenue potential.** They
are factual, source-level claims about two publications. The first Claims
existing does not make Opportunity discovery ready.

**`ted-eu` is eligible, resource-ready, collected, normalized and derived from,
under ONE profile and through ONE route.** The operator recorded the acceptance
in Mission 1.15.6.1; Mission 1.15.7 authorised one concrete resource and wrote
`ted-search-api@1.0.0`; Mission 1.15.8 added the `procurement_notice` kind and
`ted-search-api-notice@1.0.0`; Mission 1.15.9 added `TRANSACTION_VALUE` and
correctly derived nothing; Mission 1.15.10 repaired the Decimal invariant as
`ted-search-api@1.1.0` and derived **one** Signal from an acquisition designed
for comparability. **11 RawRecords, 11 NormalizedRecords all `PARTIAL`, 1
Signal.** Nothing downstream of it: no Claim cites the TED Signal and no
Evidence references it. `ted-bulk-xml`, the historical CSV and
`commercial-multi-tenant-research-v1` are refused exactly as before, and H-36A,
H-36B, H-37 and H-38 are untouched.

**Four rules bound that collector, and each is enforced rather than promised**
(`ted-eu-search-api-collector-v1.md`): every bound is required with no default,
because TED's rate limit is UNKNOWN and the acceptance is conditioned on bounded
queries; there is **no exhaustion mode**, because the API's `ITERATION` scroll
would retrieve the corpus; there is **no fallback** to `ted-open-data-sparql`,
which is authorised and unimplemented, because a fallback turns a reviewed route
into a runtime choice; and the four monetary semantics stay under their own
names, with no `price_paid` and no currency conversion.

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
