# Mission 1.73 — Independent HTTP Counterpart Qualification V1

**Outcome: `COUNTERPART_FOUND_REQUEST_CONTRACT_UNRESOLVED`.** An independent HTTP
producer exists, it was identified on first-party evidence, and it is two narrow
questions short of qualifying. **Ten of twelve mandatory dimensions PASS. Zero FAIL.**

---

## 0. The shift that dissolves the problem rather than solving it

Every apparatus this arc examined since Mission 1.58 died on the same thing: the temporal
object. A maintained current-state view answers *what is running now*; a historical
snapshot answers *what we happened to capture*; neither answers *what was observed during
a window we defined*.

A counterpart that measures **on demand** needs no history at all.

```
T0  corpus, apparatus and request contracts frozen
T1  operator authorizes
T2  both apparatuses independently receive their targets
T3  both observe inside a governed window W
```

The window becomes prospective by construction, and `createdAt` and `updatedAt` are
**required** fields on the provider's own measurement response. That is not a workaround;
it removes the question the last five missions kept failing.

## 1. What passes, and why it matters

| dimension | status |
|---|---|
| C1 directable target | **PASS** |
| C2 own measurement production | **PASS** |
| C3 terminal submission accounting | **PASS** |
| C4 transport-level result surface | **PASS** |
| C5 prospective temporal addressability | **PASS** |
| C6 request contract reconstructability | **PARTIAL** |
| C7 vantage reviewability | **PASS** |
| C8 result minimization | **PASS** |
| C9 rights feasibility | **PARTIAL** |
| C10 independence plausibility | **PASS** |
| C11 bounded pilot feasibility | **PASS** |
| C12 same HTTP world-state family | **PASS** |

The operator supplies the exact target — *"A publicly reachable measurement target."* —
with `path`, `query` and an optional `host` override, so the provider selects no sample
and runs no discovery. The probes perform the request themselves: *"a globally
distributed network of community-hosted probes, allowing anyone to run network testing
commands like ping or traceroute from any location"*, dispatching through undici in the
provider's own source.

**And the provider names apparatus missingness itself.** Per-result statuses are
`in-progress`, `finished`, **`failed`** and **`offline`** — the last defined as a test
*"where the requested probe was not available to run the test"*. The distinction Mission
1.71 built its whole accounting invariant around exists on the other side too, without us
having to infer it.

## 2. Minimization by the request, not by a filter

The default method is **HEAD**. A HEAD response has no body, and `rawBody` is documented
as *"The raw HTTP response body or `null` if there was no body in response."*

So ADR-039's transport-level condition is satisfied by **choosing what to ask** rather
than by trusting the provider to omit a field. Under GET it would not be — up to 10 kb of
the publisher's body would arrive — and that is recorded as a constraint on the future
request contract rather than smoothed away.

## 3. The first residual is one word absent from a 124,793-byte specification

**`redirect`.** Zero occurrences. The result schema carries one `statusCode` and one
header set, with no hop array.

The probe dispatches through `undici.Client.dispatch()`, which does not follow redirects
— **and that is an observed implementation, not a documented contract.**

That distinction is not pedantry. An undocumented default can change without notice, and
if the counterpart began following redirects while SROS did not, **both routes would
still report *a* status and the divergence would be invisible in the data.** Mission 1.70
closed the external pair on a redirect semantic that *was* documented; this one is not,
and §25 names *undocumented redirects* as exactly the case where equivalence may not be
assumed.

## 4. The second residual, and the clause that looks decisive but is not

The Terms of Use say:

> You agree not to use the Services for any commercial or business purposes

That sits under the heading **"If you are a consumer user:"**, with a separate liability
clause addressing business users immediately above. **Prohibited Use prohibits neither
commercial use nor automated access.** Reading a consumer-scoped liability clause as a
blanket prohibition would be the mirror of the over-read this project refused in Mission
1.45, where a recommendation to seek legal advice was not treated as a grant.

**What does bite is §2 Permitted Use**: the platform *"allows you to monitor, debug, and
benchmark **your** internet infrastructure"*, while §3 reserves *"all rights that are not
expressly granted"*. Measuring a frozen corpus of third-party sites is not our own
infrastructure, and a reservation clause makes the absence of an express grant weigh
**more** rather than less.

`DEDICATED_GOVERNANCE_REVIEW_REQUIRED` — neither clearly blocked nor clearly permitted.

**And the terms were behind three navigation shells.** Three retrievals of the published
pages returned navigation only; the same document is committed as markdown in the
provider's public repository and reads in full there. **A document automated retrieval
cannot reach is not necessarily a document that does not exist**, which is worth carrying
after Missions 1.67 and 1.72 both recorded terms as unreachable.

## 5. Producer identity, decided on architecture rather than branding

`PROVIDER_OPERATED_OPEN_SOURCE_ENGINE`: the provider authors the code and coordinates the
network, volunteers host the hardware and the network position.

- no third-party measurement upstream
- no shared observation upstream with SROS, Common Crawl or HTTP Archive
- the auxiliary sharing that does exist — DNS, trust stores, the internet — is recorded
  as **not** defeating independence
- SROS initiating the job does **not** make the measurement SROS-produced
- running our own fetcher on another cloud would **not** create a second apparatus

**The registry's own frame-uniformity rule is met explicitly**, by a provider statement:
*"You may not modify the probe's code or behavior in any way."* Every probe in the frame
runs the same code.

## 6. Why this outcome and not another

Outcome D names request semantics, and there are **two independent** unresolved mandatory
gates. Reporting D alone would let a reader conclude one sentence about redirects unlocks
the route, so the imperfect fit is recorded rather than smoothed — the same move Mission
1.60 made rather than choosing the label whose wording bends most easily.

- **A and B** — refused: two mandatory dimensions are PARTIAL, and §45 makes that block.
- **C** — refused: it claims the epistemic requirements all pass. The request contract is
  an epistemic gate and it is open.
- **F** — refused: a transport-only path *was* established.
- **G** — refused: the producer *was* established.
- **H** — refused: it requires an *otherwise viable* route, and this one is not.
- **I** — refused as a serious understatement. An independent, directable,
  transport-level producer with legible missingness and prospective temporal semantics
  **was** identified. Reporting *none found* would send the next mission hunting for what
  it already holds, which is the mistake Mission 1.69 refused.

## 7. Q1, and what did not move

Three of §48's four viability conditions hold. The fourth is a qualified counterpart, so
**Q1 stays `PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`**, no class was selected, and
`selected-quantity-class-v1.json` does not exist. No construct, no counterpart selected,
**0 independence groups**, `PAIR_ANALYSIS_NOT_READY`.

**The candidate registry rule was reviewed and not added, for a reason that is new.**
Missions 1.71 and 1.72 declined it because designing or legislating around a failure mode
is not observing one. Here the counterpart simply **does not exhibit** the failure: its
statuses distinguish apparatus trouble from target observation. A candidate that *avoids*
a failure mode is not a second empirical instance of it. **Registry unchanged at 15**, on
a third distinct reason in three missions.

## 8. Nothing moved

| | |
|---|---|
| counterpart API executions, target HTTP requests, SROS fetcher runs | 0 |
| external measurement jobs, Common Crawl queries, BigQuery, HAR/WARC | 0 |
| target-value exposures, accounts, trials, purchases, credential reads | 0 |
| mailbox searches, enquiries sent, provider contacts | 0 |
| sources registered, canonical mutations, thresholds, Claims, Evidence | 0 |
| independence groups, reliability values, scores, model calls, embeddings | 0 |

26 of 30 documentation requests, **11 of which returned nothing usable and are counted**.
ADR-039 untouched, the source-collection gate unchanged, ONYPHE still
`NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, the scanner arc still parked.

## 9. Verification

- Validator probed with **153 deliberate violations, 153 caught** — 150 by rule, 3 by
  drift — plus **7 of 7 positive controls, all variants** rather than the shipped bytes.
- **Two defects in my own control models were found by the validator refusing them**, and
  both were fixed on my side rather than by loosening a rule: a serious-candidate count
  that excluded a candidate which had been seriously evaluated and then qualified, and a
  control asserting a state §48 makes unrepresentable — all four viability conditions met
  with Q1 not viable.
- **The specification was read from the saved bytes rather than from a summary.** The
  fetch tool's summary was correct where I checked it, and I checked it: `rawBody`'s "only
  the first 10 kb" phrasing was verified against the file rather than quoted from the
  answer.
- **§66 honoured**: `ruff format --check`, `ruff check` and mypy all run through `uv`.
- **90 new tests**; **2622 bare-python tests**; all pytest suites passed with the database
  unchanged across 29 tenant tables; all **43** CI gates.

## 10. Next

**Mission 1.74 — Counterpart Residual Closure V1.** Close R1 and R2 on this candidate
only:

- **R1** — one documented sentence on redirect behaviour, or one question through the
  enquiry channel this project has already used once.
- **R2** — a dedicated governance review of measuring third-party targets under a
  Permitted Use section scoped to the user's own infrastructure.

**Do not resume broad counterpart search, do not restart quantity-class discovery, and do
not select a construct over a route whose request contract is unresolved.**

**Mission 1.74 was not started.**
