# ADR-017 — Model source signal coverage as a mapped projection of the canonical ontology

- **Status:** Accepted
- **Date:** 2026-08-30
- **Deciders:** Mission 1.7
- **Supersedes:** none
- **Related:** Mission 1.7 §4, §5, §22, §23, §34, §35, §36, §47;
  [`source-coverage-gap-analysis-v1.md`](../../data/source-coverage-gap-analysis-v1.md);
  Ontology V2 §3.3, §3.4, §3.6, §14;
  [ADR-013](ADR-013-source-registry-governance.md)

---

## Context

The source catalog can say where a source's data comes from
(`source_family`), what fields it returns (`source_capabilities`), and what its
own documents permit (`source_policy_reviews`). It cannot say what could be
*learned* from it.

That gap is not academic. Mission 1.7 §22 requires a matrix that makes it
obvious when the portfolio holds twenty economic sources and no entertainment
sources, and §23 requires the answer to count only reviewed, non-prohibited
capabilities. Asked of today's registry, "which sources could expose
entertainment signals" has no query at all; the nearest available filter,
`source_family = 'content_platform'`, returns YouTube — which is `PROHIBITED`,
so the closest available answer is also a wrong one.

**The decision was partly pre-constrained.** Mission 1.7 §5 states "Reuse the
canonical ontology when possible. Do not create overlapping vocabularies
unnecessarily", and Ontology V2 §14.3 already governs how a taxonomy of this
kind is introduced. What was left open is whether signal coverage is a *new*
taxonomy or an *existing* one applied to a new subject — and the gap analysis
found that eleven of the sixteen concepts §4 names already exist verbatim in
`user_motivation`, while all seventeen behaviours §5 names are `user_behavior`'s
canonical entry list unchanged.

So the forcing question is narrow: eleven names already exist with the same
meaning, attached to a different subject. Duplicate them, borrow them, or
something else.

## Decision

Signal coverage is recorded as a **new `signal_family` registry in which every
entry names the canonical ontology entry it projects**, via nullable
`maps_to_registry` / `maps_to_id` columns on `registry.registry_entries`;
behaviour coverage introduces **no new vocabulary and references `user_behavior`
directly**. The pointer can only reference a *registry*, so `DESIRE` — whose
counterpart is the CLOSED demand signal family of Ontology V2 §3.6 — is `NULL`
too, with the correspondence recorded in prose rather than by reclassifying a
closed enum as extensible. Both attach to a source through their own link tables in the
`registry` schema, each row carrying a mandatory `basis`, and neither carries a
number of any kind.

## Alternatives considered

### Alternative A — attach `user_motivation` rows to sources directly

No new vocabulary, maximum reuse, and it satisfies §5 on its face.

Rejected on two grounds. It is a **category error**: `user_motivation` describes
why a *person* wants something, inside an Opportunity, and a source does not
have a motivation. Recording `world-bank -> user_motivation:curiosity` asserts
something untrue about the World Bank rather than something true about its data.

And it **couples two vocabularies that must move independently**. Motivations
are added for opportunity modelling; the day someone adds one, every source's
coverage profile silently gains a category it was never reviewed for. Coverage
rows are review artefacts and must change only when somebody reviews.

### Alternative B — a fresh `signal_family` registry with sixteen unrelated entries

The straightforward reading of §4: sixteen names, own vocabulary, no
entanglement.

Rejected because eleven of the sixteen would duplicate `user_motivation` by name
*and* by meaning. That is precisely the "overlapping vocabularies" §5 forbids,
and the overlap would be invisible — two registries containing `entertainment`
with nothing recording that they mean the same thing. The first person to need
both would have to rediscover the correspondence and would get it slightly
wrong.

### Alternative C — extend `source_capabilities` with coverage strings

No migration at all: the table already holds per-source open strings with a
description.

Rejected because it merges two different relations into one column. A capability
is *what data comes back* (`reviews`); coverage is *what could be learned from
it* — and `reviews` maps to PROBLEM, DESIRE or ENTERTAINMENT depending entirely
on the source. One column with two meanings gets the second inferred from the
first by the next reader. `source_capabilities` is also uncontrolled free text,
correct for describing an API response and useless for a taxonomy §22 needs to
aggregate over.

### Alternative D — document only, no schema change

§47 explicitly prefers catalog/config additions, so this deserved a real look.

Rejected because §23 requires coverage to be counted only for sources that are
reviewed and not prohibited, which is a join against `registry.source_eligibility`.
A markdown table cannot be joined; it is correct on the day it is written and
drifts from the next review onward. That is the same drift
`source-registry-v1.md` §3 refuses when it makes eligibility a view rather than a
stored boolean.

## Pros

- **The overlap is written down instead of implied.** `signal_family:curiosity`
  carries `maps_to = user_motivation:curiosity` as data. Nothing has to
  rediscover it, and a query can traverse it.
- **The genuine gaps stay honest.** `TREND`, `COMMERCIAL`, `COMMUNITY` and
  `DEVELOPER_ACTIVITY` map to `NULL` rather than to a near-match. Forcing
  `DEVELOPER_ACTIVITY` into `user_motivation` would corrupt the vocabulary it
  was pushed into.
- **Behaviour coverage adds nothing at all**, which is the strongest possible
  compliance with §5.
- **§22 and §40 become queries** rather than prose that ages.
- Extensible without migration, per Ontology V2 §14.3.

## Cons

- **A sixteenth-entry registry is still a new vocabulary to maintain**, and it
  can drift from `user_motivation` if someone adds a motivation and forgets the
  projection. Nothing forces the mapping to stay complete; the mapping is
  optional by construction because five entries legitimately have none, so
  "unmapped" cannot be made an error.
- **The projection cannot reach a closed enum.** `registry_entries` holds
  registries, so a signal family whose canonical counterpart is a closed enum
  (`DESIRE`) records `NULL` and states the correspondence in its description.
  That is a real limit of the mechanism, not a modelling choice.
- **`maps_to_*` on `registry_entries` is a general facility introduced for one
  registry.** Every other registry will carry two columns it never uses. The
  alternative — a dedicated mapping table — was heavier for the same result.
- **Coverage is a judgment**, recorded by a reviewer from a source's documented
  capabilities. `basis` makes it re-checkable but does not make it objective,
  and two reviewers could differ on whether Steam reviews evidence `PROBLEM`.
- **It invites a weight.** A table of source-to-category links is one `numeric`
  column away from being the per-source reliability coefficient D-03 blocks.
  The gap analysis §5.1 and §35 both forbid it and neither is a mechanism; the
  only real defence is that the column does not exist and adding one would need
  a migration somebody has to write and justify.

## Consequences

- Migration 0010 adds `signal_family` (16 entries), the missing canonical
  `user_behavior` (16) and `user_motivation` (14) entries the ontology already
  specifies, three `source_family` entries, and two link tables.
- `SourceRecord` gains `signal_coverage` and `behavior_coverage`; the catalog
  JSON gains two arrays per source; `sros-source validate` checks both against
  the loaded vocabularies.
- Coverage is **never** consulted by the eligibility gate. A source may cover
  `ENTERTAINMENT` and be `PROHIBITED`, and the two facts live in different
  tables precisely so no view collapses them.
- Evidence aggregation is untouched and remains uncalibrated. Nothing in this
  ADR produces a number.
