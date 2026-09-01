# `docs/data/` — Data specifications

**Authoritative.**

| Document | Defines |
|----------|---------|
| `data-principles.md` | Source strategy, acquisition, raw preservation, quality, deduplication, language and geography, privacy, temporal modeling, contradictions, lineage, cost control, legal review |
| `data-retention-policy-v1.md` | Retention tiers, the stricter-constraint rule, per-source overrides, deletion semantics |
| `source-registry-v1.md` | The source registry, per-activity policy assessment, evidence requirements and the collector eligibility gate (added in Mission 1.0) |
| `acquisition-authorization-v1.md` | How a review condition is cleared, and what a collector must hold before it may run (added in Mission 1.4) |
| `effective-condition-verification-v1.md` | How a persisted human decision and a live machine verification combine into the state the gate reads. A machine that cannot answer never counts as a no; a human decision never makes a machine condition sticky (added in Mission 1.15.6.2) |
| `world-bank-collector-v1.md` | The first real collector: scope, request model, transport, identity, provenance (added in Mission 1.5) |
| `source-review-guide.md` | How a human conducts a source review, step by step |
| `source-catalog-v1.json` | The reviewed candidate catalog. **Source of truth**, edited by hand |
| `source-catalog-v1.md` | The same catalog, rendered. **Generated** by `sros-source render`, checked in CI |
| `source-review-results-v1.md` | Review results as a diff: first verdict, current verdict, and the document that moved it. **Generated**, checked in CI |
| `source-signal-coverage-v1.md` | What each source COULD expose, the coverage gaps, and the portfolio's economic-versus-consumer balance. **Generated**, checked in CI |
| `source-coverage-gap-analysis-v1.md` | Why coverage needed its own tables rather than `source_capabilities` (written before migration 0010) |
| `source-expansion-consumer-social-v1.md` | The Mission 1.7 review round: fourteen new candidates, what each document said, and what could not be retrieved |
| `source-portfolio-v1.md` | Which sources future missions should build collectors for, grouped by need. Qualitative tiers, never scores |
| `source-human-review-queue-v1.md` | Unresolved items, each with the exact document, the exact question and the exact next action |
| `new-source-compliance-gap-analysis-v1.md` | The Mission 1.8 audit: why three Mission 1.7 approvals rested on silence, and what GDELT needed instead |
| `gdelt-compliance-v1.md` | GDELT's compliance configuration and why each rule is the only one its evidence supports |
| `gdelt-raw-record-gap-analysis-v1.md` | The Mission 1.9 audit: why the reviewed DOC API cannot serve the authorised data categories, and what would unblock it |
| `gdelt-response-contract-v1.md` | What is established about the DOC API's responses, which two contracts are still missing (H-27), and the WEB-NGRAM contract that was observed and then confirmed against GDELT's own documentation |
| `gdelt-resource-model-v1.md` | The DOC API resource entry, decided and still uncommitted; and the WEB-NGRAM path that superseded it |
| `gdelt-web-ngram-review-v1.md` | The reasoning behind GDELT review 3: what was assessed, the first-party evidence, and the DOC API deferral |
| `gdelt-web-ngram-minimisation-gap-analysis-v1.md` | The four observed columns against the committed categories, and why three of them needed a new one |
| `gdelt-web-ngram-resource-v1.md` | The two authorised WEB-NGRAM resources, the access route, and the reviewed acquisition ceiling |
| `gdelt-web-ngram-collector-v1.md` | The second collector: streaming, bounded, strict-parsing, and what it refuses |
| `gdelt-web-ngram-raw-record-v1.md` | What one WEB-NGRAM observation is, why `observed_at` and `content_language` are empty, and why the key separator is escaped |
| `gdelt-normalized-record-gap-analysis-v1.md` | The four fields against the canonical model, and which three of them it could not hold |
| `gdelt-normalization-contract-v1.md` | The canonical shape a GDELT normalizer must produce, decided in Mission 1.10 and implemented in 1.10.1 |
| `gdelt-web-ngram-normalizer-v1.md` | The second adapter: offline, deterministic, and what it refuses to invent |
| `signal-model-gap-analysis-v1.md` | What `nlp.signals` could not represent, sixteen gaps, written before the migration |
| `signal-contract-v1.md` | What a Signal IS: a relation between two or more observations, and everything it may not assert |
| `signal-taxonomy-v1.md` | Why the Signal family is not the demand family, and the two types real data justifies |
| `signal-temporal-semantics-v1.md` | ORDER and GLOBAL INSTANT kept apart; which derivations H-29 and H-32 block |
| `gdelt-web-ngram-temporal-evidence-v1.md` | The first-party evidence that closed H-32, left H-29 open and refined H-31 |
| `signal-derivation-runtime-v1.md` | How extraction runs, groups and persists, and where a REFUSED derivation goes |
| `numeric-period-change-extractor-v1.md` | The first extractor: adjacent-period change in one measured series |
| `lexical-frequency-contrast-extractor-v1.md` | The second: two terms, one bucket, one language label, and no ordering |
| `lexical-frequency-change-extractor-v1.md` | The third: one term, two adjacent buckets, and a gap that is never bridged |
| `claim-evidence-interpretation-gap-analysis-v1.md` | The Mission 1.13 audit: ten gaps between the claim schema and the pipeline that feeds it, written before the migration |
| `claim-evidence-interpretation-contract-v1.md` | Where arithmetic becomes an assertion: what a Claim is, what Evidence is, and what a machine may not store |
| `claim-epistemic-semantics-v1.md` | What each of the five claim types asserts, and the four ways of choosing the wrong one |
| `signal-to-evidence-semantics-v1.md` | How a Signal becomes Evidence FOR a particular Claim, and why news frequency is not weak demand evidence |
| `deterministic-observed-claim-interpreter-v1.md` | The first interpreter: three templates, a source named in every sentence, and nothing else asserted |
| `claim-interpretation-runtime-v1.md` | How interpretation runs and persists, where a REFUSED interpretation goes, and what the run remembers considering |
| `evidence-reliability-gap-analysis-v1.md` | The Mission 1.14 audit: twelve gaps between per-row reliability semantics and anything a reviewer could actually write |
| `evidence-reliability-contract-v1.md` | What reliability means, who may establish one, and why a scope nobody assessed produces no number |
| `evidence-reliability-review-guide-v1.md` | How a human writes a reliability assessment, and when to write none |
| `demand-side-source-expansion-v1.md` | The Mission 1.15 round: nine sources examined, two verdicts changed on retrieved evidence, and every retrieval that failed |
| `demand-side-source-coverage-v1.md` | The eight business evidence families against the registry. Seven have no approving source; two have no candidate at all |
| `demand-side-source-priority-v1.md` | Which source to pursue next, in ordinal buckets with stated reasoning. Never a numeric source score |
| `ted-eu-reuse-ml-review-v1.md` | The Mission 1.15.1 review of H-34: the governing instrument named and proven, its text unretrievable, and why that is worse than silence |
| `ted-eu-governing-decision-review-v1.md` | Commission Decision 2011/833/EU read in full. H-34 closes PERMITTED: reuse is defined by purpose, not by method |
| `ted-eu-database-right-review-v1.md` | H-36 does not close. The Decision governs documents and never reaches the collection they sit in |
| `ted-eu-database-right-clarification-v1.md` | The dataset-level licence, found and identified: `COM_REUSE` on every `ted-1` distribution including bulk XML, resolving by `skos:exactMatch` to the same Decision. H-36 splits into H-36A and H-36B and stays open |
| `ted-eu-database-right-clarification-request-v1.md` | The message to the Publications Office. **Prepared, not sent** — sending is an operator action |
| `ted-eu-h36-legal-review-packet-v1.md` | Established facts and five questions for a lawyer, with no legal conclusion attached |
| `ted-eu-local-private-research-review-v1.md` | The two OFFICIAL query routes reviewed against the system's actual local, private use. Their documented purpose covers analysis, reuse and application integration; that is intended-use evidence and not a database-right grant |
| `route-scoped-source-authorization-gap-v1.md` | Mission 1.15.4's gap analysis. **The extension it proposed was built in Mission 1.15.5** (ADR-027); kept as the record of why |
| `use-profile-aware-source-policy-v1.md` | How source permission is scoped to the use it was granted for: the two registered profiles, fail-closed behaviour, and why the runtime declares its profile rather than inferring it |
| `use-profile-migration-v1.md` | What 55 historical reviews were interpreted as having assessed, and everything the migration did not change |
| `ted-eu-local-official-route-readiness-v1.md` | TED under `local-private-research-v1`: authorised routes and fields, and the one human confirmation still outstanding. **Amended by Mission 1.15.6** |
| `ted-eu-authorization-bootstrap-v1.md` | How the pre-collector deadlock broke: two conditions were properties of CONFIGURATION rather than of code and are now verified against it; the third is a judgement and stays human. Carries the exact operator statement a later, explicit action must record — **recorded in Mission 1.15.6.1** |
| `ted-eu-operator-acceptance-pending-v1.md` | **Superseded.** The FIRST acceptance statement and why it was refused: three of seven acknowledgements absent, including the one that gives the acceptance a boundary. Kept because a refusal deleted once it is resolved teaches nobody why it happened |
| `ted-eu-operator-risk-acceptance-v1.md` | The recorded operator decision: one `HUMAN_CONFIRMATION` row, verbatim acknowledgement, `AUTHORIZATION_READY`. **H-36A and H-36B still open and no legal clearance**; `resource_ready` was still no here and became yes in Mission 1.15.7. §8 records the gap it exposed, which Mission 1.15.6.2 then closed: no shipped command produced a complete verification set for a source with a human condition, and `verify --apply` would have erased this one |
| `ted-eu-search-api-resource-v1.md` | **The first concrete TED resource.** eForms contract and award notices from 2023-03-01, through the Search API, under one profile. Why `PLATFORM_LICENSED` rather than `THIRD_PARTY`, and the five things this basis does NOT establish. `resource_ready` moves to YES; **H-36A and H-36B do not move** |
| `ted-eu-search-api-response-contract-v1.md` | What the Search API accepts and returns, established from its own OpenAPI document and its own `checkQuerySyntax` mode. One required field per notice and everything else optional; the documented 15k/250/10k limits; and `links`, which arrives unrequested and was inspected before anything was accepted |
| `ted-eu-transaction-signals-v1.md` | **The first derivation over procurement notices.** `procurement-value-contrast@1.0.1`: a non-temporal cohort spread, four monetary semantics never mixed, no currency converted, and explicitly NOT willingness-to-pay. Mission 1.15.9 formed two cohorts of one and wrote **0 Signals**, correctly, because the two EUR award totals were in different CPV divisions. Mission 1.15.10 acquired for comparability and derived **1 Signal** from three division-90 award notices, and the real data corrected the cohort scope from the first member's codes to the union of all members' |
| `ted-eu-normalization-v1.md` | **The TED Raw to Normalized mapping.** One notice, one record, lots structured inside it; four monetary semantics kept apart with no `price_paid` and no conversion; every language preserved with no canonical display value; and a published DATE that does not become a moment — `observed_at` stays NULL and **H-37** records why. Three real notices normalized, all `PARTIAL` |
| `ted-eu-search-api-collector-v1.md` | `ted-search-api@1.1.0`: four gates before a socket, one route with no fallback, bounds with no defaults, no exhaustion mode, four monetary semantics kept apart and no currency converted. `1.1.0` parses with `parse_float=Decimal` so a fractional tender value reaches jsonb as an exact string, and renders `cpv_division` into the query the source actually sees. Three real bounded acquisitions, one request each |
| `acquisition-rights-basis-gap-analysis-v1.md` | Why a resource records what KIND of thing authorises it, not only which licence (H-28, ADR-018) |
| `wikimedia-pageviews-compliance-v1.md` | What Wikimedia Pageviews would need, and the one question blocking it |
| `source-condition-gap-analysis-v1.md` | The nine Mission 1.3 conditions inventoried and classified, and the obligations deliberately left out of code |
| `source-compliance-v1.json` | Attribution texts, licence and geography allowlists, enumerated exclusions, authorized datasets and minimisation profiles. **Source of truth**, edited by hand |
| `raw-record-gap-analysis-v1.md` | What `acquisition.raw_records` could not represent before the first collector, and what migration 0008 added |

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
one **may be built**. Neither says one exists.

## Collection — the first one

Mission 1.5 implemented the World Bank Indicators collector and performed one
controlled real acquisition. It is the only collector, and the three facts stay
separate:

| Fact | World Bank | Eurostat | FRED |
|---|---|---|---|
| collector-eligible | yes | yes | only where `FRED_API_KEY` is configured |
| collector implemented | **yes** | no | no |
| collector enabled | yes, deliberately | no | no |

Eurostat is eligible and has no collector, which is the pairing that keeps the
distinction honest: eligibility says a collector may be built, never that one
exists. `acquisition.raw_records` holds World Bank observations and nothing else.

See [`world-bank-collector-v1.md`](world-bank-collector-v1.md).

## Normalization — the first adapter

Mission 1.6 built the RawRecord to NormalizedRecord boundary and normalized
those six observations. **Normalizable is a fourth fact**, and the mission that
added it is the one that proved the separation was not academic: until then the
planner blocked normalization under "no collector is implemented", a reason
Mission 1.5 made false while normalization stayed just as impossible.

| Fact | World Bank | Eurostat | FRED |
|---|---|---|---|
| collector-eligible | yes | yes | only where `FRED_API_KEY` is configured |
| collector implemented | yes | no | no |
| collector enabled | yes, deliberately | no | no |
| **normalizer implemented** | **yes** | no | no |

Normalization answers *what does this source observation structurally
represent*, and stops. It does not answer whether anything is a market
opportunity: signal extraction interprets meaning, claim extraction makes
assertions, and scoring evaluates them — three later stages, none of them
implemented.

Three rules carry over from collection, and one is new:

- **It reaches nothing.** No network, no model, no NLP. CI parses every import
  in the package rather than trusting a comment, and the guard was checked
  against fourteen deliberate violations before being believed.
- **Unknown stays unknown.** A unit the endpoint does not publish, a geography
  code no reviewer classified, a value the source never reported — each gets a
  state a consumer can branch on rather than a plausible value nobody can check.
- **Missing is never zero.** Zero is a measurement; absence is not; a layer that
  mapped both to `0` would make them permanently indistinguishable.
- **Versions coexist.** A revised RawRecord produces a revised NormalizedRecord
  with the earlier one intact, and a newer normalizer version produces an
  additional row rather than replacing one. Which version downstream should read
  is **D-08**, open and deliberately unresolved.

See [`normalized-record-v1.md`](normalized-record-v1.md) and
[`world-bank-normalizer-v1.md`](world-bank-normalizer-v1.md).

## Still open

- Evidence reliability weighting per source — blocked by **D-03**. The registry
  deliberately assigns no per-platform reliability number.
- Jurisdiction analysis (GDPR applicability) — **requires human/legal input**,
  deliberately not guessed.
- Backup retention and how deletion interacts with backups — deferred to the
  production ADR (ADR-007).
- Which normalized representation downstream should read when several
  normalizer or schema versions exist — **D-08**. Coexistence works; selection
  does not exist and was deliberately not invented.
- The raw layer converts numeric values with `float(...)`, which is exact for
  the integers the authorized series carry and would not be for a rate.
  Normalization cannot recover what that lost; fixing it belongs to a collector
  version bump (`world-bank-normalizer-v1.md` §4).
