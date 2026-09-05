# Mission 1.60 — Observation-Addressable Scanner Pair Selection V1

**Outcome: `APPARATUS_LINEAGE_NOT_AFFIRMATIVELY_ESTABLISHED`.** No pair selected.

---

## 0. Applying the gates before choosing worked

That was the point of the new ordering, and it changed what the mission found.

```
A2 observation-addressable   PASS on two independent mechanisms
A3 protocol-native exposure  PASS, RAW_IDENTIFICATION_STRING
A7 affirmative lineage       PARTIAL
A8 reliability reviewable    PARTIAL
```

**The anchor passes both gates that killed the previous two pairs.** Its
observation window is chosen in the *request* — a parameter selecting a
data-collection date, plus date ranges over a per-record `scan_date` documented
as recording when the scanning that *generated* the response occurred, with daily
scan volumes downloadable as dated files on top. Nothing is discovered after
retrieval.

And it passes A3 in the strongest exposure class available: a queryable raw
banner field with wildcard matching plus port filtering, so the RFC 4253 prefix
predicate is expressible against **the bytes the peer sent** rather than against
a vendor's service label.

## 1. Baseline

Verified live, no drift: 325 / 325 / 33 records, 44 Claims, 45 revisions, 58
Evidence, 1 INFERRED Claim, 1 threshold, 1 derivation, 0 refusals, `SUPPORTS 57 /
CONTRADICTS 1`, 0 Claims carrying both, head `0035`, main `b7fac0a`.

## 2. What blocks, and what kind of thing it is

**A7 stays PARTIAL** because the documentation is not silent about the
apparatus's own scanning — it is silent about **exhaustiveness**. Inferring
exhaustiveness from a list of enrichment sources would be reading a positive
claim out of a negative space.

That is the same refusal for the fourth mission running, and it is the one most
tempting to abandon now that everything else about this apparatus works.

**A8 stays PARTIAL** on operational questions nobody has asked: retries,
duplicate handling within a window, address-identity counting, and what a missing
record means. But its load-bearing classification is a **standard-defined prefix
on an exposed banner**, not a proprietary fingerprint — so what remains
unreviewed is operational rather than semantic. That is the difference from the
dropped apparatus, whose black box *was* the classification.

**The blockers changed kind.** They are no longer about what the apparatus
measures or how it exposes it. Both close by reading or asking.

## 3. No partner reached pair analysis

Three candidates probed, all three failed at **A6**: their first-party technical
documentation was not retrievable at the paths tried. One had moved its docs to a
wiki whose pages did not load; one redirected then 404'd; one 404'd.

**That is a fact about this mission's reach, not a finding about those
apparatuses**, and the record says what the search does *not* establish — that no
qualifying partner exists. The asymmetry is in documentation access, not
apparatus quality: the anchor was qualified from four first-party documents, and
the partners were left at a wall rather than at a verdict.

## 4. The outcome fits imperfectly, and the record says so

Outcome G is defined for a promising **pair**; there is a promising **anchor**.
The clause is half-satisfied.

It was chosen because it names the **established** blocker rather than the merely
unexplored one, and because no partner can rescue an anchor whose own lineage is
unproven. The alternatives were worse in specific ways:
`NO_OBSERVATION_ADDRESSABLE_PARTNER_IDENTIFIED` asserts the anchor qualifies, and
`ANCHOR_APPARATUS_INVALIDATED` calls an unproven negative a refutation.

Saying that out loud beats picking the label whose wording bends most easily.

## 5. The requirement registry

Nine rules from Missions 1.47 to 1.59, in one record, each with the mission that
paid for it:

| requirement | from |
|---|---|
| `SOURCE_EXCLUSIVE_METRIC` | 1.56 |
| `RELIABILITY_REVIEWABILITY` | 1.47 |
| `FRAME_INSIDE_THE_DEFINITION` | 1.57 |
| `AFFIRMATIVE_LINEAGE_REQUIRED` | 1.57 |
| `PRODUCT_RELEVANCE` | 1.58 |
| `READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT` | 1.58 |
| `OBSERVATION_ADDRESSABLE_EXPOSURE` | 1.59 |
| `THE_TEMPORAL_OBJECT_TEST` | 1.59 |
| `SAMPLING_IS_LOAD_BEARING` | 1.59 |

**Every one was learned *after* a pair had been chosen.** That is exactly why
they are now applied before, and why the registry exists rather than a chain of
reports.

## 6. Two small rules made structural

- **A count is not metadata.** A query returning only a number still returns a
  measurement value about the target population.
- **A free trial is not harmless.** A zero-cost trial, demo console or search
  preview destroys preregistration exactly as a paid one would. Access cost is
  irrelevant to epistemic contamination.

## 7. A falsifiability trap, caught before it mattered

A windowed count makes host membership an **existential within the window** — a
host observed once qualifies even if it later stops responding. That looks
monotone, and a monotone proposition cannot be contradicted.

It is not. The **Claim** is a count against a bound, and a lower count
contradicts it. Host-level monotonicity is not Claim-level monotonicity, and
conflating them would have invented a falsifiability problem or hidden one.

## 8. Fixtures, executed

Synthetic values only (`4242` and `1717` against a bound of `3000`), never
persisted:

- two witnesses annotated with different scanner ids → **one proposition key**;
- two `KNOWN_INDEPENDENT` supports → **two provenance groups**;
- the `UNKNOWN` control → **one group**;
- one supporting and one contradicting witness → **one Claim, both directions**.

Diagnostic answer: `LEGITIMATE_INDEPENDENT_MEASUREMENT_DIFFERENCE_POSSIBLE` — but
only for a pair sharing one population and one window. A difference caused by
different frames or time semantics is not a measurement difference at all; it is
two propositions being compared, which is what the last two missions failed on.

## 9. What did not happen

```
queries executed        0        trials started    0
target counts           0        purchases         0
host records            0        facets            0
first-party retrievals  10 of 15
```

0 canonical mutations, 0 sources registered, 0 governance reviews, 0 collectors,
0 threshold registrations, 0 Claims, 0 Evidence, 0 reliability values, 0
independence groups, 0 Scores, 0 Opportunity changes, 0 model calls, 0
embeddings. The Mission 1.56 Claim is untouched.

## 10. Verification

| | |
|---|---|
| CI gates | 28, all green |
| bare-python | 1529 tests |
| pytest | 3310 tests |
| validator probe | 85 deliberate violations, 85 caught |

## 11. Next

**Mission 1.61 — Anchor Lineage Confirmation and Partner Documentation Retrieval
V1.** Both blockers are documentation problems and neither needs a new apparatus
class.

It should prepare an operator-approved enquiry asking whether host-level
observations are produced by the anchor's own probes and whether any external
measurement dataset is load-bearing; ask the operational questions a reliability
reviewer would; pin port coverage to the window, since the port list is
documented as expanding; retrieve working documentation paths for the three
partner candidates; and establish the anchor's vantage model, recorded here as
`NOT_ESTABLISHED` *before* pairing rather than after.

It must not fetch a value, execute a query, start a trial, purchase access,
revive the dropped apparatus, accept a vendor label as the metric, or read an
absence as a statement.
