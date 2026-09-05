# Mission 1.57 — Independence-Capable Evidence Route Feasibility V1

**Outcome: `INDEPENDENCE_CAPABLE_ROUTE_GOVERNANCE_PENDING`.**
Actionability: `EPISTEMICALLY_VALID_GOVERNANCE_PENDING`.

---

## 0. The finding, before the route

A quantity that exists **only because a platform recorded it** can be measured
only by that platform. A quantity that exists **in the world independently of any
measurer** can be measured by more than one apparatus. **Every source in this
portfolio measures the first kind.**

Wikimedia's request counts exist because Wikimedia's servers logged them. Stack
Overflow's question counts exist because Stack Overflow published them. GDELT's
term frequencies exist because GDELT crawled a corpus and counted. TED's award
totals exist because contracting authorities filed notices there. Each is the sole
possible apparatus for its own quantity, so a second API, dump, mirror or
dashboard is a second **copy** and never a second **measurement**.

**It generalises Mission 1.46 one domain over.** There, the measurement of how
many people live in Germany happens once, at Destatis, and Eurostat, the World
Bank and FRED are three routes to it. Here, a platform's activity is measured
once, by the platform, and every interface is a distribution layer. Two findings,
one fact about where measurement actually occurs.

That is why 29 registered sources yield zero pairs, and it is a search
instruction rather than a counsel of despair: an independence-capable route must
be sought among quantities that exist independently of their measurer.

## 1. Baseline

Verified against the live deployment, no drift:

```
Claims 44 · ClaimRevisions 45 · Evidence 58 · INFERRED Claims 1
thresholds 1 · derivations 1 · refusals 0 · independence groups 0
SUPPORTS 57 · CONTRADICTS 1 · claims carrying both directions 0
migration head 0035_refusal_provenance · main 6b7c8f4 · PR #99 merged
```

The Mission 1.56 Claim was re-read and is untouched: one Evidence item,
`CONTRADICTS`, one provenance group, `NO_APPLICABLE_ASSESSMENT`, `NON_SCORABLE`.

## 2. Why the pilot Claim is not the route

`SOURCE_EXCLUSIVE_METRIC`. Its metric is generated from Wikimedia's own request
logs, so no second Wikimedia interface can be a second measurement. No
alternative interface was searched for, and the Claim was not touched.

## 3. Held pairs

Ten held apparatuses across five sources. **Exactly one shared subject**, and it
is the same one Mission 1.47 found: `docker`, observed by Wikimedia requests and
by Stack Exchange questions.

Verdict `COMPLEMENTARY_NOT_CORROBORATING`. A content request is what a reader's
client makes of a server; a published question is what a person writes about
being stuck. **ADR-036 removed the identity blocker that stopped those two ever
reaching one Claim. It did not make a request a question** — and the Opportunity
engine's own mapping rationale, written in Mission 1.30, had already said
`PROBLEM_OR_NEED` and `AUDIENCE_OR_USAGE` are different questions.

No held pair passed, so the POST_HOC-for-held-data branch never arose.

## 4. Negative controls, re-run

| control | verdict | basis |
|---|---|---|
| World Bank + FRED | `DEPENDENT_REPUBLICATION` | FRED's own `Source Code SP.POP.TOTL` |
| World Bank + Eurostat | `COMMON_UPSTREAM_SOURCE` + `SEMANTIC_MISMATCH` | both publishers' own metadata; de facto midyear vs usually-resident 1 January |
| Wikimedia alternative route | `SAME_MEASUREMENT_UPSTREAM` | one set of request logs |

**Neither World Bank pair was promoted**, and that was the one way this mission
could have gone wrong. The INFERRED layer fixes Claim **identity**. It repairs
neither provenance dependence nor a stock measured against an estimate.

## 5. The selected route

An atmospheric mole-fraction pair at one fixed site. Two programmes, two sets of
instruments, two laboratories.

**The decisive evidence is a calibration scale rather than an organisation
chart.** The two report on **different reference scales**, and a republished
series carries the originator's scale. Both sides state it first-party: one says
it operates an independent sampling network rather than obtaining data from the
other; the other describes that data as independent and uses it for comparison —
and **comparison for validation is not consumption**.

**Provenance independence is not error independence.** The two share the site and
one provides in-kind field support there, so a site-level artefact would move
both. That is recorded as a limitation of the eventual Claim, not folded into the
independence verdict.

**The scale difference becomes a threshold constraint.** A bound placed close
enough for the documented offset to decide the comparison would manufacture a
contradiction out of a calibration difference. The next mission must place it
clear of that offset and record the reasoning **before** any value is retrieved.

## 6. The validator caught my own record

The rejected web-traffic route was first written `KNOWN_INDEPENDENT` with no
documentary basis — because the two systems really are separate. §15 requires the
proof from **both** sides before that word may be used, so it became `UNKNOWN`.
That costs nothing, because the route fails for a better reason: each apparatus
measures share **within its own network**, both stating so first-party, so **the
frame sits inside the metric definition**. Any proposition admitting both would
define its event class as a disjunction of the two networks, relocating source
attribution from the subject of the sentence into its predicate.

Mission 1.47 found that shape once. It is now named as the
`FRAME_INSIDE_THE_DEFINITION` trap so the next mission meets it earlier.

That route also fails governance independently: one apparatus publishes under a
non-commercial licence, and local deployment never implies non-commercial use.

## 7. No value was fetched, and that is load-bearing

`PREREGISTERED` is defined against **retrieval**. One measurement fetched during
feasibility research would have made an honest preregistration impossible for
ever afterwards.

```
RESEARCH_DATA_REQUESTS            0
FIRST_PARTY_METHOD_DOC_REQUESTS   6
GOVERNANCE_DOC_REQUESTS           0
measurement values fetched        0
```

## 8. The reservation

The selected construct is **not a quantity this product will research**. §20
makes relevance a preference rather than a mandatory gate and §46's selection
rule omits it, so selection is permitted — and the honest reading is that this is
an **apparatus** route, not a research topic. Its purpose is to put two
independent witnesses on one Claim so the aggregator stops being algebraically
identical to the B-2 pass-through.

**Transferability limit, stated.** A calibration reference built on a
physical-science quantity may not transfer to platform-mediated evidence:
reliability, revision behaviour and independence characteristics all differ. What
the route can establish is that the mechanism **works** on real independent data,
not what its parameters should be for a request count.

**Inside this portfolio there is no alternative**, and that is §0's finding
rather than a gap in the search.

## 9. Symbolic proofs

Driven through the real grouping primitive on non-empty fixtures whose
reliability values (`0.42`, `0.71`) match nothing any reviewer has recorded:

- two `KNOWN_INDEPENDENT` supports → **two groups**;
- two `UNKNOWN` supports → **one group** (the control);
- `S = 1 - (1-gA)(1-gB) > max(gA, gB)`, which is exactly the inequality that
  makes the full aggregator differ from B-2;
- one Claim carrying `SUPPORTS` and `CONTRADICTS` → one group per direction.

The INFERRED contract needs **no schema change**: `TargetProposition` already
carries the seven identity facts and excludes source, measurement and direction.
The cross-source OBSERVED convergence approach was **not** reopened.

## 10. What did not happen

0 canonical mutations, 0 sources registered, 0 reviews created, 0 collectors, 0
normalizers, 0 threshold registrations, 0 Claims, 0 Evidence, 0 reliability
assessments, 0 independence groups, 0 Scores, 0 Opportunity changes, 0 model
calls, 0 embeddings. The Mission 1.56 Claim is untouched.
`REFERENCE_PROFILE_V1` still `UNCALIBRATED`, Problem-Family still `PARKED`.

## 11. Verification

| | |
|---|---|
| CI gates | 26, all green |
| bare-python | 1439 tests, 9 packages |
| pytest | 3310 tests, 9 packages |
| validator probe | 79 deliberate violations, 79 caught |

## 12. Next

**Mission 1.58 — governance, not acquisition and not a threshold.** Registering a
bound against a source nobody has reviewed would freeze a contract for an
acquisition that may never be permitted. The next mission retrieves both
producers' data-use terms first-party, registers both apparatuses without
approving anything, performs the local-private-research-v1 review for each,
records the commercial position separately, and stops before any acquisition and
before any threshold registration.

**It must not fetch a measurement value.** That is the one irreversible mistake
available to it.
