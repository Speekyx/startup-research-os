# Mission 1.72 — Public HTTP Observation Governance Policy V1

**Outcome: `PUBLIC_HTTP_OBSERVATION_GOVERNANCE_TRACK_READY`.** All five decisions
Mission 1.71 left open are resolved, ADR-039 adopts a distinct governance track, and
nothing is authorized to run.

---

## 0. The decision is conditional, and that is the load-bearing part

Mission 1.71 could not clear the apparatus because the acquisition gate governs
collection **from a registered source**, and a corpus of arbitrary public sites has
no shape in it. GOV-1 asks whether bounded HTTP observation is the same activity or
a distinct one.

**It is distinct, while the retained material is transport-level.**

> The moment response bodies or a publisher's expressive content are retained, the
> retained thing IS the publisher's material, and source-collection governance
> applies instead.

So **GOV-1 is not independent of GOV-3**. Had GOV-3 chosen full-response retention,
ADR-039 would not have been adoptable at all. The two were written as one decision
in two parts rather than presented as separate answers that happen to agree.

## 1. The distinction was tested, not asserted

| question | answer |
|---|---|
| if the page's content were entirely different and the transport outcome identical, would the observation change? | **no** |
| if the transport outcome differed and the page content were identical, would it change? | **yes** |

The observation is a function of the transport interaction rather than of the
publisher's expressive content, so what is appropriated differs **in kind rather than
in degree**.

**The obvious objection is answered in the record rather than left standing.** A status
code is still information the publisher produced — and the six activities rule 8 governs
(`storage`, `derived_analytics`, `commercial_use`, and the rest) ask whether we are
appropriating a publisher's **content or database**, not who caused a fact to be
observable. This is a project-governance distinction and **explicitly not a legal
conclusion**.

## 2. Why the other three models lost

**Model A — source collection only.** Refuted on structure rather than effort: the
evidentiary standard cannot be met for a target that has never published terms, because
there is nothing to retrieve.

**Model C — per-target operator review.** Refuted as **the wrong layer**. For such a
target the operator would be reviewing nothing, which reproduces Model A's problem in a
form that *looks* like review while having no basis — worse than Model A. The part of it
that is real (public, safe, known to be excluded) is mechanical, and it survives as
GOV-4's preflight.

**Model D — leave it ungoverned.** Refuted because the two activities *can* be
distinguished on material the repository already holds.

## 3. Precedence is a function, and the boundary is structural

The track is determined by the **declared retention profile**, never by the caller's
stated intent. Where both could apply, source collection wins.

**And that is enforced rather than noted.** The observation track's own retention
contract has no persistable body class, so a body-retaining configuration **is not
expressible in it**. A validator check proves that claim against the contract itself
rather than trusting the sentence that makes it.

## 4. GOV-2 — robots, read rather than recalled

`R1_RESPECT_DISALLOW`. RFC 9309 was retrieved — the single external request of a budget
of eight — because writing what a standard says from memory is the error Mission 1.71
avoided by deferring CIDR blocks to IANA. **Thirteen conditions, one outcome each**, and
every row states whether it follows the standard or is stricter than it.

| condition | outcome | ours or the standard's |
|---|---|---|
| 2xx parseable | evaluate rules | the standard's |
| 404 / 410 and other 4xx | **proceeds** | the standard's |
| 401 / 403 | excluded | **ours** |
| 5xx, network failure | excluded | the standard's |
| timeout | excluded | **ours** |

**`R0` was refused on the project's own rule** — `source-registry-v1.md` §1 rule 6 says
robots directives are limits, not obstacles.

**`R2` was refused for a reason worth keeping.** Excluding every target whose robots.txt
is merely *absent* would make the measured population a function of whether a site
publishes one — **a coverage bias we would be introducing**, in the arc whose subject is
population honesty. So fail-closed is adopted for the *unreachable* cases, where the
standard itself requires complete disallow, and refused for the *absent* case, where the
standard permits access.

**401 and 403 exclude, and the record says that is ours**: a robots.txt refusing an
unauthenticated client contradicts the track's own public-accessibility precondition. The
exclusion follows from the track rather than from caution.

## 5. GOV-3 — what is retained

`D2_ALLOWLISTED_HEADERS_AND_STATUS`, with `BODY_PERSISTENCE_DEFAULT = DISABLED`.

**The trap it closes: not persisting a body is not the same as not receiving bytes.** A
body-disabled apparatus still reads off the socket, so the read cap is required either
way. Treating the two as one would leave unset the single bound that protects the
operator machine.

The secret-bearing headers are **always excluded and a run may not widen the allowlist
into them** — an allowlist a caller can extend into `Set-Cookie` is not an allowlist. A
`Location` is transient in raw form and minimized when persisted, with the record stating
that the query component was dropped, so a reader knows the representation is minimized
rather than complete.

Every retention number carries `decision_kind = PROJECT_POLICY_DEFAULT`.

## 6. GOV-4 — exclusions that do not shrink the population

An excluded target is **not removed from the corpus**. It becomes a terminal accounting
record in a `NOT_ATTEMPTED` family. Deleting it would shrink `N`, which is precisely the
defect that closed the external routes in Mission 1.70.

Unknown terms are `TARGET_TERMS_NOT_INDIVIDUALLY_REVIEWED` — **neither a favourable
fiction nor an impossible per-item human review**, which would have reinstated Model C
silently, as a side effect of a target policy.

The preflight is ordered and first-match-wins, so two runs over one corpus classify
identically **and give the same reason** — and the reason is what a later reader uses to
understand the population.

## 7. GOV-5 — the numbers are ours and say so

Fifteen bounds, all finite or explicitly `DISABLED`, all carrying
`value_source = PROJECT_POLICY_DEFAULT`.

| | | | | |
|---|---|---|---|---|
| 500 targets | concurrency 4 | **per-origin 1** | **1 req / 5 s** | 10 s connect |
| 20 s read | 5 redirects | **0 retries** | 64 KiB headers | 1 MiB read |
| 2 MiB / target | 6 h run | 1 robots / origin | 6 req / target | backoff `DISABLED` |

**Retries are zero** because a retry can observe a different world state and Mission 1.71
left the which-attempt-counts rule to the construct — a non-zero value would create
records under a selection rule that does not exist.

**One target is not one request.** Redirects and robots retrievals both count toward the
origin budget, and a run must report requests per target, per origin and in total.

## 8. Nothing was weakened, and nothing was authorized

Registered sources **29 before and 29 after**. No review touched, no target registered, no
eligibility record changed. Twelve eligibility requirements, **none defaulting to approval
when unknown**, and a run additionally needs a specific corpus, request contract, construct
and operator approval.

Common Crawl and HTTP Archive keep Mission 1.70's verdicts verbatim, and the new track is
recorded as **not** repairing their missingness. The scanner arc stays parked. Q1 stays
`PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`. **`PAIR_ANALYSIS_NOT_READY`.**

**The candidate registry rule was reviewed again and still not added.** Mission 1.71
refused to count its own designed solution as an empirical instance; writing a **policy**
that respects a rule is not observing an apparatus fail without it either. Registry
unchanged at **15**.

## 9. Nothing moved

| | |
|---|---|
| target HTTP requests, robots target requests, crawls, browser runs | 0 |
| curl/wget executions, Common Crawl queries, BigQuery, dataset downloads | 0 |
| target-value exposures, accounts, trials, purchases, credential reads | 0 |
| mailbox searches, enquiries sent | 0 |
| corpora, exclusion entries, runs, crawlers implemented | 0 |
| sources registered, canonical mutations, thresholds, Claims, Evidence | 0 |
| independence groups, reliability values, scores, model calls, embeddings, migrations | 0 |

1 of 8 documentation requests, and it was a standards document rather than a target.

## 10. Verification

- Validator probed with **186 deliberate violations, 186 caught** — 183 by rule, 3 by
  drift — plus **7 of 7 positive controls, all variants rather than the shipped bytes**:
  source collection still governed, a legitimate observation shape, a scraping attempt
  routed to the source gate, a robots disallow becoming a policy exclusion, a stricter
  retention variant, a different finite load profile, and governance-ready with the run
  still unauthorized.
- **A malformed guard in this mission's own validator was found and removed.** A
  conditional expression sitting beside the check that does the work, which would have
  raised with an empty message had it ever fired — the guard-that-cannot-speak shape this
  repository keeps finding, caught by reading rather than by a failure.
- **§59 was honoured in full**: `ruff format --check`, `ruff check` and mypy all run
  through `uv`, and every environment-dependent gate run with `uv run` rather than bare
  `python`.
- **101 new tests**; **2532 bare-python tests**; all pytest suites passed with the database
  unchanged across 29 tenant tables; all **42** CI gates.

## 11. Next

**Mission 1.73 — Independent HTTP Counterpart Qualification V1.** It searches only for one
external apparatus compatible with the operator-controlled frozen population, its attempt
and missingness semantics, the request-contract family, the temporal window, independent
measurement production and rights feasibility.

**Do not restart broad quantity-class discovery.**

**Mission 1.73 was not started.**
