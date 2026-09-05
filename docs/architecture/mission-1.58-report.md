# Mission 1.58 — Broadened Apparatus Search V1

**Outcome: `PRODUCT_RELEVANT_INDEPENDENCE_CLASS_IDENTIFIED_GATES_OPEN`.**
No route selected.

---

## 0. What the operator decided

`ROUTE-A-ATMOSPHERIC-CO2-FIXED-SITE` is withdrawn, on the stated reason that it
does not serve the product. Subject relevance, a **preference** in Mission 1.57's
brief, becomes a **mandatory gate**.

**That is a rule change, not a correction.** Mission 1.57's reasoning was sound
under the rule it was given: its brief listed relevance under preferences,
omitted it from the selection rule, and the mission flagged this exact
reservation before asking for approval. Filing a sound analysis as an error would
misdescribe both the analysis and the decision.

**The withdrawal is appended, not applied by editing.** The 1.57 record still
reads `selected_route: ROUTE-A`, with the supersession recorded beside it.
Deleting the field would lose what the operator decided *against*, which is the
entire content of the decision — so the validator refuses a supersession that
removed it.

What survives unchanged: the structural finding, the negative controls, the
independence proof standard, the `FRAME_INSIDE_THE_DEFINITION` trap, and the
value-inspection rule.

## 1. The conjunction

A quantity that **(a)** exists independently of any single measurer, **(b)** has
at least two documented independent measurement apparatuses, and **(c)** bears on
an Opportunity dimension.

Mission 1.57's law makes this hard on purpose: (a) rules out everything a
platform records, and (c) is mostly satisfied by exactly the things platforms
record. The two conditions pull in opposite directions. An empty intersection was
the honest possibility going in.

**It is not empty.**

## 2. Seven classes surveyed

| class | world quantity | two apparatuses | verdict |
|---|---|---|---|
| internet-wide active scanning | YES | YES | **PURSUED** |
| web-crawl technology surveys | YES | PARTIALLY | rejected |
| package and registry downloads | NO | NO | rejected |
| certificate transparency logs | YES | NO | rejected |
| job postings vs vacancy statistics | YES | YES | rejected |
| business registers | NO | NO | rejected |
| app-store catalogues | NO | NO | rejected |

- **Web crawls** are `FRAME_INSIDE_THE_DEFINITION` again: each crawler defines
  its own site population, and one takes its origin list from a single platform's
  dataset, so the *frame* has a common upstream even where the crawling does not.
- **Job postings vs vacancy statistics** are genuinely independent producers of
  **two different constructs**. A vacancy is not a posting. Independence without
  the same proposition is useless.

## 3. The new trap, found by certificate transparency

CT logs look like many independent witnesses. They are many operators carrying
**the same certificate submitted to each**.

> **`READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT`.** Measurement requires that
> the apparatus generate the value by interacting with the world, so that two
> apparatuses can legitimately disagree.

Its test is the sharpest this arc has produced: **if the two apparatuses
disagree, is that a fact about the world or a bug?** For two readers of one
published number, a disagreement is a bug. For two scanners probing the internet,
it is a real difference in coverage, timing or fingerprinting — which is exactly
what independent corroboration is supposed to tolerate.

## 4. The surviving class, and why its independence is structural

Internet-wide active scanning. The construct: publicly reachable IPv4 hosts
responding on a defined port with a protocol-defined service banner.

**The asymmetry with every earlier route.** Population figures have an upstream
**producer** — the national statistical institute measures once and everyone else
distributes. Host counts have none. **Nobody publishes how many hosts run a
service**, so there is no common upstream measurement available to be
republished, and each apparatus must generate its value by probing.

The failure mode that killed World Bank + FRED, World Bank + Eurostat and every
platform pair is not merely absent here. It is **structurally unavailable** — and
unlike a documentary argument, it cannot be undone by one party changing its
data-sourcing policy.

**The law is refined rather than refuted.** A quantity is independently
measurable exactly when *no party is in a position to publish it authoritatively*
— and the internet as a whole is such a quantity, even though every host on it
belongs to somebody.

**Product relevance:** `AUDIENCE_OR_USAGE` and `COMPETITIVE_SUPPLY`, with the
bound sentence that a reachable host is not an installation, a customer or a
user.

## 5. No route was selected

Twelve of sixteen gates pass. The set is conjunctive, so **selecting the best
route found is not selecting one that qualifies** — and the operator asking for a
broadened search is not a reason to lower the bar.

| open gate | what is missing | closable by |
|---|---|---|
| **3** metric definition | vendor fingerprinting is proprietary, so "hosts running product X" is two operational definitions | freezing the construct on what the **protocol** defines, not a vendor label |
| **5** time compatibility | two snapshot censuses of a moving population need a shared *as of when*; one side's cadence article was not retrievable | retrieving one named first-party document |
| **10** lineage documentation | one apparatus states its provenance affirmatively, the other only by omission | further first-party documentation, or written enquiry |

**Gate 10 reads `PARTIAL` rather than `PASS` deliberately.** An absence of a
reference to third-party data is an absence, not a statement. Mission 1.57
corrected exactly this error in its own record; the correction is applied here
rather than forgotten.

**Gate 3 is the one that could quietly go wrong.** Taking the vendor product
label instead of the protocol-defined service would be the CPI-basket failure in
a new domain: two indices of two baskets compared as one number.

## 6. What broadening bought

**Before:** the only qualifying route measured a quantity the product will never
research, and inside the portfolio there was no alternative.

**After:** there is an alternative, it is outside the portfolio, it is
product-relevant, its independence rests on a structural asymmetry rather than a
documentary coincidence, and what blocks it is a retrievable document, a policy
review and a purchase.

## 7. What did not happen

```
research-data requests              0
first-party documentation requests  8
measurement values fetched          0
```

That last figure is load-bearing: `PREREGISTERED` is defined against
**retrieval**, so one value fetched here would have destroyed it permanently.

0 canonical mutations, 0 sources registered, 0 reviews created, 0 collectors, 0
threshold registrations, 0 Claims, 0 Evidence, 0 reliability assessments, 0
independence groups, 0 Scores, 0 Opportunity changes, 0 model calls, 0
embeddings. The Mission 1.56 Claim is untouched, `REFERENCE_PROFILE_V1` still
`UNCALIBRATED`, Problem-Family still `PARKED`.

## 8. Verification

| | |
|---|---|
| CI gates | 26, all green |
| bare-python | 1453 tests |
| pytest | 3310 tests |
| validator probe | 103 deliberate violations, 103 caught |

## 9. Next

**Mission 1.59 — Internet-Wide Service-Presence Route Gate Closure V1.**
Epistemics before governance, **inverting Mission 1.57's recommendation for a
reason**: there the epistemics were closed and only a review remained. Here gate
5 decides whether the two apparatuses measure one proposition at all, and buying
a licence first would be paying to discover a semantic problem.

It must not fetch a measurement value, must not accept a vendor product label as
the metric definition, and must not read an absence of evidence as evidence.
