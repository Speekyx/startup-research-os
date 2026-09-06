# ADR-039 — Bounded public HTTP observation is a distinct governed activity

**Status:** Accepted
**Date:** 2026-09-06
**Mission:** 1.72
**Supersedes:** nothing. **Amends:** nothing. It adds a track beside source
acquisition and changes no rule of it.

---

## Context

Mission 1.70 closed the Common Crawl / HTTP Archive pair: neither documents
whether a URL that was attempted and failed appears in what it publishes, so no
honest common denominator can be built from them. The route it left open was an
operator-run fetcher, which supplies directability and legible missingness by
construction.

Mission 1.71 designed that apparatus and could not clear it, for a reason it
located in this repository's own rules rather than in the design:

```
PUBLIC TARGET -> NOT REGISTERED -> NOT ADDRESSED -> ACQUISITION REFUSED
```

The acquisition gate governs collection **from a registered source**. Under
`source-registry-v1.md` §1 rule 8 an approving state needs a GRANT for six named
activities on retrieved authoritative evidence, and rule 2 forbids any path from
*we could not check* to *we may proceed*. For a website that has never published
terms addressing automated access there is no document to retrieve, so every
activity reads `NOT_ADDRESSED` and the target is refused.

**That is the gate working.** It was built for a question about reusing a
publisher's content, and it answers that question correctly.

The consequence is the problem. Restricting a measurement corpus to targets that
hold a review restricts it to the 29 registered sources, which destroys exactly
the directability that made the operator route worth designing.

## Decision

**Adopt `PUBLIC_HTTP_OBSERVATION_TRACK`**, a distinct governance track for
bounded observation of publicly accessible HTTP targets, **conditional on what is
retained**.

The condition is not decoration and it is what makes the decision defensible:

> The track is available only while the retained material is transport-level.
> The moment response bodies or a publisher's expressive content are retained,
> the retained thing IS the publisher's material, and source-collection
> governance applies instead.

GOV-3 satisfies that condition by setting `BODY_PERSISTENCE_DEFAULT = DISABLED`.
**Had GOV-3 chosen full-response retention, this ADR would not have been
adoptable at all** — which is why GOV-1 and GOV-3 are not independent decisions
and were not written as though they were.

## Why the two activities are different in kind

The obvious objection is that this is one activity wearing a smaller name. The
test is behavioural rather than definitional:

| question | answer |
|---|---|
| if the page's content were entirely different and the transport outcome identical, would the observation change? | **no** |
| if the transport outcome differed and the page content were identical, would it change? | **yes** |

The observation is a function of the transport interaction, not of the
publisher's expressive content. What is appropriated differs, and it differs in
kind rather than in degree.

**A second objection, and the honest answer.** A status code is still information
the publisher produced. True — and the six activities rule 8 governs (`storage`,
`derived_analytics`, `commercial_use`, and the rest) ask whether we are
appropriating a publisher's *content or database*, not who caused a fact to be
observable. A transport outcome sits closer to a measurement of the world than to
a copy of a work.

**This is a project-governance distinction and explicitly not a legal
conclusion** about any target, any jurisdiction or any body of rights.

## Alternatives considered

**Model A — source collection only.** Rejected, and not because it is laborious.
It is *structurally unavailable*: the evidentiary standard cannot be met for a
target that has never published terms, because there is nothing to retrieve. The
corpus collapses to the registered set.

**Model C — per-target operator review without registration.** Rejected as
*the wrong layer*. For a target publishing no terms, the operator would be
reviewing nothing, which reproduces Model A's evidentiary problem in a form that
**looks** like review while having no basis — worse than Model A, because it
manufactures the appearance of a judgement. The part of it that is real (is this
target public, safe, known to be excluded) is mechanical, and it survives as
GOV-4's preflight.

**Model D — leave it ungoverned.** Rejected. It would be the honest answer if the
two activities could not be distinguished; they can be, on material this
repository already holds. Leaving it undecided would repeat the move Mission 1.71
refused in the other direction — treating an absence of a decision as though it
were one.

## What this ADR does not do

- It does **not** weaken source acquisition. No rule, review, eligibility record
  or resource authorization changed. Registered sources: 29 before, 29 after.
- It does **not** make any target a source, automatically or otherwise.
- It does **not** make public visibility into permission. The rule under this
  track is `PUBLIC + TRACK_REQUIREMENTS_PASS => INTERNALLY_GOVERNED_OBSERVATION`,
  which is a statement about our own conduct.
- It does **not** authorize a run. Every one of the twelve eligibility
  requirements must pass, and a run additionally needs a specific corpus, request
  contract, construct and operator approval.
- It does **not** choose what will be measured. No header, status code, HTML
  token or technology is selected.

## Precedence, and why a caller cannot choose

The track is determined by the **declared retention profile**, never by the
caller's stated intent. If the profile retains a response body, publisher
expressive content, or any material whose value to us is what the publisher
wrote, source-collection governance applies. Where both could apply, source
collection wins.

This is enforced structurally rather than by a note: the observation track's own
retention contract has an allowlist of persisted data classes that contains no
body class, so a body-retaining configuration **is not expressible in it**.

The observation track may not be used for article ingestion, document corpus
acquisition, page-content research, scraping for ideation, news or forum
ingestion, dataset ingestion, commercial content harvesting, or general-purpose
site crawling.

## Consequences

**Load obligations do not get lighter.** The track answers a different *rights*
question and carries the same or stricter *conduct* obligations — one request in
flight per origin, one every five seconds, no retries, robots disallow respected.
A target bears the same cost whichever track a request travels under, so the
track is not a discount.

**Robots becomes architectural.** Respecting disallow requires a retrieval stage,
a terminal outcome, a request budget and a missingness class, so GOV-2 changes
what the apparatus *is* rather than how it is configured.

**Excluded targets stay in the population.** A robots exclusion or a policy
exclusion produces a terminal accounting record, not a smaller corpus. Deleting
excluded targets would shrink `N` and reproduce the defect that closed the
external routes.

**Nothing is authorized to run.** `RUN_AUTHORIZATION_REQUIRED = true`, the
fetcher is unimplemented, and a second independent route is still required before
any of this becomes evidence.
