# ADR-028 — Reviewed Route Binding, and Configuration-Verified Conditions

**Status:** Accepted · **Date:** 2026-08-31 · **Mission:** Sprint 1 / 1.15.6
**Supersedes:** nothing. **Amends:** the authorization contract (Mission 1.4,
ADR-016) and the use-profile-scoped gate (Mission 1.15.5, ADR-027).

---

## Context

### The problem, stated precisely

`AcquisitionAuthorizationContext.access` carried **every access profile the
registry recorded for a source**. An access profile is a fact about how a source
*can* be reached and has never said anything about permission
(`source-registry-v1.md` §8), so the context had nothing to filter it with — and
a collector selects its route by label from that tuple.

The existing collector already knew this was a hazard.
`GdeltWebNgramCollector._route` says so in its own docstring:

> GDELT carries a second, deferred profile for the DOC API; taking
> `context.access[0]` would work today and would silently authorise
> `api.gdeltproject.org` the day the profile order changed.

The mitigation was a comment and a careful collector. That holds only while
every registered route of every approving source is one its review would
tolerate.

### What made it visible

TED-EU under `local-private-research-v1`. The review authorises two official
query routes and **refuses the bulk XML packages by name**, because Mission
1.15.3 established the highest database-right exposure on that route and H-36A
and H-36B are open. The packages are published, documented and downloadable
without signing in, so `ted-bulk-xml` is in the registry, because it is true.

Had an authorization been buildable, the context would have handed a collector
the refused route with its endpoint — and the transport's host allowlist is
derived from `context.access`, so the blocked host would have been allowlisted
with it. The restriction that carries the whole local approval would have been
advisory.

### The second problem, which is the same problem

TED carried two `HUMAN_CONFIRMATION` conditions describing objective properties:
*collection uses the official routes and never the bulk packages*, and *the
deployed minimisation profile requests only the authorised fields*. Both were
written as claims about a collector, and no collector existed — so the readiness
document recorded them as outstanding *because there is nothing whose route or
field selection a person could confirm*.

That is a **bootstrap**, and it breaks in the wrong direction. A collector may
only run with an authorization; the authorization waits on a human confirmation
about the collector; the confirmation waits on the collector. The path of least
resistance is to write the collector first and confirm it afterwards, which
inverts the order the whole authorization layer exists to impose.

### What was rejected before this ADR was written

**Reusing `ACCESS_METHOD` / `AccessRestriction`.** It is the obvious candidate
and it answers a different question. `_verify_access_method` passes when the
registry holds *exactly* the approved access profiles and no others — a
statement about **the source**. Making it pass for TED would have required
deleting `ted-bulk-xml` from the registry: falsifying a fact about a source in
order to obtain a permission, which is the worst habit this layer could acquire.

**Adding a `ConditionVerification` value.** `CONFIGURATION_INVARIANT` as a sixth
enum member would be new taxonomy in a closed enum, a contract version bump, and
a second vocabulary for something `CAPABILITY` already means: *a named product
capability is implemented and enabled, checked against this source's real
configuration.*

**Leaving both conditions human and writing the collector first.** The order
`policy → configuration → verification → authorization → network` is the one
thing Mission 1.4 built. Suspending it for the first source that made it
inconvenient would have retired it.

---

## Decision

### 1. A review may restrict which registered routes acquisition binds to

`RouteAuthorization`, per `(source, use profile)`, in
`source-compliance-v1.json`: `allowed_labels`, `blocked_labels`,
`preferred_label`, `basis`.

It is a statement about **us**, not about the source. `AccessRestriction`
remains, unchanged, for the question it answers.

### 2. The context carries the authorised routes and nothing else

Where a route authorization exists, `build_authorization` filters
`context.access` to the authorised labels. **This is the enforcement**, and it
is the same shape as everything else here: not a flag the collector is asked to
check, but the absence of the object it would need. A blocked label has no
endpoint to read, so there is no host to allowlist and nothing for the transport
to be pointed at.

`context.authorize_route(label)` exists so a refusal reads as *refused by name*
rather than as *not found*. It is the diagnostic; the filter is the guarantee.

### 3. An authorised route the registry does not record is refused

Not skipped. A route with no access profile has no endpoint and nothing to check
a host against, and skipping it would quietly narrow the authorisation to
whatever happened to exist.

### 4. `None` means unasked, not unrestricted

Every compliance entry predating this ADR has no route authorization, and their
behaviour is unchanged. Absent means the question was not asked for that
`(source, profile)` — the same reading `AcquisitionBounds.max_files_per_job`
already has (ADR-016, Mission 1.9.2) — and the capability that checks a route
restriction reports **unimplemented** rather than **satisfied** when it is
absent. A condition can only ever rest on a restriction that exists.

### 5. Field minimisation is asked before a request is composed

`DataMinimisationProfile.refusals(requested)` and
`context.authorize_fields(requested)`. An excluded field is refused by name, a
field no review authorised is refused, and a request that states no selection is
refused.

**Where the source supports field selection, this is the primary control.** A
request that took everything and discarded the contact block afterwards would
have retrieved the contact block, and the obligation is about what is retrieved.
There is deliberately no method that removes fields from a collected record.

### 6. An objective property of configuration is verified, not confirmed

A condition describing something a reviewer can put in
`source-compliance-v1.json` gets a mechanical verification kind and a registered
capability. A condition describing a judgement, a risk acceptance, a legal view
or a promise about future conduct stays `HUMAN_CONFIRMATION`.

`source-review-guide.md` §9's older instruction is unchanged and still
load-bearing: *do not reword a legal obligation until it sounds checkable — that
produces a verifier that checks something else.* The new rule is upstream of it,
not against it: **ask first whether the condition was ever about a legal
obligation at all.**

### 7. Nothing here can reach a human confirmation

A `HUMAN_CONFIRMATION` condition dispatches to the human branch before any
configuration is consulted, so no route authorization, minimisation profile or
capability can answer one. TED's residual database-right acceptance is
untouched, unsatisfied and outstanding.

---

## What this establishes, and what it does not

**Not** *"the collector follows the rules."* No verification in this repository
can establish that, and a capability claiming to would be lying about its own
contract (`acquisition-authorization-v1.md` §6).

**This**: *the configuration supplied to authorization satisfies the policy
constraints, and the authorization hands a collector nothing else.*

The obligation that remains sits with the collector mission: it must be built so
that it **cannot execute without an authorized configuration**, the way
`test_collector_conformance.py` already asserts for resource access.

---

## Consequences

**Good.**

- A route a review refused cannot reach a collector, whatever the collector
  does. The guarantee stops depending on a docstring.
- Two conditions moved from *unverifiable until something exists* to *verified
  now*, with no network call, no collector and no weakening of TED policy.
- The bootstrap is gone in the right direction: configuration is authorised
  first, and the collector is built against an authorization that already
  refuses what it must.
- `DataMinimisationProfile` stopped being data nothing read.
- The rule generalises, and it is written down where a reviewer meets it.

**Costs, accepted.**

- A second concept next to `AccessRestriction` that a reader must tell apart.
  Mitigated by stating the difference in both docstrings and in
  `acquisition-authorization-v1.md` §7.1: one is about the source, the other is
  about us.
- Only TED has a route authorization, so the guarantee is per-source rather than
  global. **GDELT is the named gap** — its deferred DOC API profile is still
  carried into its context. Adding a restriction for it is a review act, and
  migrating it here would have been a review nobody performed.
- Adding a condition to a review means appending a review version, which is
  correct and is not free.

**Neutral.**

- No contract change. `ConditionVerification` still has five values.
- No schema change. `RouteAuthorization` lives in the compliance JSON, which is
  a governance record rather than runtime configuration.

---

## Alternatives rejected

| Alternative | Why not |
|---|---|
| Reuse `ACCESS_METHOD` | Answers a question about the source. Passing it for TED would mean deleting a real route from the registry |
| Add a sixth `ConditionVerification` value | New taxonomy in a closed enum for something `CAPABILITY` already means |
| Filter routes inside each collector | Puts the permission decision in the thing being permitted, which is the move the authorization layer exists to prevent |
| Keep both conditions human, write the collector first | Inverts the order Mission 1.4 built, for the first source that made it inconvenient |
| Delete `ted-bulk-xml` from the registry | Falsifies a fact about a source to obtain a permission |
| Filter personal fields after collection | The obligation is about what is **retrieved**. The source supports field selection, so collect-then-filter is not available as an excuse |
| Reclassify the residual database-right acceptance too | It is a judgement, not a property. Code that could satisfy it would be a judgement nobody made |
| Add a `route_authorization` to every source at once | A review act dressed as a configuration edit, for four sources nobody re-reviewed |
