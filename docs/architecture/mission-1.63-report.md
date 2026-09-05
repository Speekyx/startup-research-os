# Mission 1.63 — Anchor & ONYPHE Documentation Closure V1

**Outcome: `ANCHOR_ENQUIRY_STILL_REQUIRED_ONYPHE_UNRESOLVED`.** Four named reads,
seven retrievals of a budget of eight, and **zero gate verdicts changed**.

---

## 0. A retrieval summary is not a document

The first read of the candidate's query-language page reported, in analytical
prose, that its time-range functions filter *on time of data collection, not
record modification dates*, and *by observation period, not record state*.

That is exactly the distinction `THE_TEMPORAL_OBJECT_TEST` turns on, phrased as a
contrast between the two candidate readings. It would have moved B2 from `PARTIAL`
to `PASS`.

It arrived **without quotation marks**, unlike the timestamp definition on the
data-model page, which came back quoted. So it was re-read verbatim.

**The page does not contain that sentence.** What it contains is a section
described as allowing search through historical data, and four calendar-bucket
boundary definitions.

Mission 1.61 re-read the anchor's lineage sentence for the same reason and the
re-read **confirmed** it. Same procedure, opposite answer. A `PASS` resting on a
sentence that does not exist was not recorded.

## 1. Baseline

Verified live, no drift: 325 / 325 / 33 records, 44 Claims, 45 revisions, 58
Evidence, 1 INFERRED Claim, 1 threshold, 1 derivation, 0 refusals, `SUPPORTS 57 /
CONTRADICTS 1`, 4 reliability assessments, 0 independence groups, `scoring.scores`
absent, head `0035`, main `d08a765`.

## 2. The four reads

| # | subject | question | result |
|---|---|---|---|
| 1 | Netlas | can port-22 membership be bound to a window? | not established |
| 2 | ONYPHE | observation event or maintained state? | ambiguous |
| 3 | ONYPHE | is TCP/22 in the relevant scan set? | unknown, wrong category |
| 4 | ONYPHE | which fields survive 30 days? | **resolved** |

## 3. A port list for the wrong category

The candidate's published scanned-port list is headed for the **ctiscan**
category — 5,054 TCP ports, port 22 among them.

The construct's protocol-native evidence lives in **datascan**, whose refresh
documentation describes a 500-port cycle whose membership is published nowhere,
and whose retention is seven months against ctiscan's one.

**A configuration fact published for one resource does not establish it for
another.** That is `RESOURCE_SPECIFIC_LINEAGE` applied to configuration rather
than lineage. Verdict `PORT_22_STATUS_UNKNOWN`.

The gap is new. Before this read the question was an unread page; it is now a
named category mismatch answerable by one document.

## 4. A field named as truncated is not a field removed

> For data older than 30 days, we remove some fields as they are less useful, and
> we truncate data field to 4KB

The sentence distinguishes two operations and **names the raw response field as
the one truncated**, placing it outside the set removed. A four-kilobyte
truncation does not touch the beginning of an identification string of tens of
bytes, so the predicate survives.

**B3 is not reopened.** Mission 1.62 flagged this as the risk that could end
protocol-native exposure at thirty days. It does not.

Which other fields are removed is still unnamed. Whether the observation timestamp
and the address survive is `UNKNOWN` — and those are the fields that *locate* an
observation, so the residual matters and was not guessed in either direction.

`MAX_FULL_FIDELITY_RETRIEVAL_DELAY` = 30 days, frozen as a duration. No dates
chosen.

## 5. Calling an endpoint to learn whether calling it is safe is circular

The anchor's indices operation is located and its path recorded. The rendered API
reference truncates before the response schema, at the operation's own anchor.

**It was not executed.** A configuration endpoint may be called only where
evidence proves its response carries no measurement — and the evidence that would
prove it is the schema that could not be read.

No inference was drawn from the current port list, from list cardinality, from the
absence of recorded removals, or from the endpoint merely existing.

## 6. Zero topics changed is the honest count

A8 recomputed over all ten topics: **2 answered, 4 partial, 4 unknown, 0 changed.**

*We now know which page to read* is not progress. An endpoint existing is not
documented semantics. Both are written into the record as refusals rather than
left for a reader to notice.

Five load-bearing topics remain unresolved, and six of the seven frozen enquiry
questions target them.

## 7. The enquiry

All seven questions reassessed after the four reads. All seven `STILL_UNRESOLVED`
→ **CASE A**: v1 remains current, frozen and unsent on Mission 1.61's exact hash.
No v2, no duplicate hash.

```
APPROVE MISSION 1.61 ENQUIRY 310acf288244453cd0a928197386cbf8311ded278e4dcdd22b70412807a049c4
```

Three of the four reads were candidate questions and the enquiry is addressed to
the anchor. That is why four reads produced zero answered questions, and it is
stated rather than left looking like waste.

## 8. Registry: one added, one declined

**Added** `APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE`, demonstrated by both
apparatuses independently — each publishes a current port list and neither binds
it to a window. Distinct because `OBSERVATION_ADDRESSABLE_EXPOSURE` governs when
the **observation** happened and this governs when the **configuration** applied.

**Declined** `FULL_FIDELITY_RETENTION_IS_PART_OF_ACQUISITION_CONTRACT`. Retention
resolved favourably, so the evidence demonstrated the opposite of the failure the
rule anticipates. A duration was frozen on the apparatus record instead.

Registry 13 → 14. Declining is a recorded decision.

## 9. Two guards that could not fire, in my own validator

One compared a field to the literal `NONE` where the record states `NONE` and then
explains what it means — so the guard could never fire. Repaired to a prefix test
and proved firing.

One was worse. A mechanical collapse of nested `if` statements folded a sibling
check inside a `raise`, leaving it unreachable while still looking like a check.
It surfaced because the probe went from 123 caught to **122 caught and one
escaped**. Repaired by hand, then the whole module was audited over its AST for
any other statement after a `raise` or `return`.

**A guard that cannot fire is the recurring shape in this repository, and the
probe is what makes it visible.**

## 10. A Mission 1.62 test was re-pointed

It pinned the registry length at 13, which this mission's addition made false. A
test pinning a total is a test asserting the registry never grows. It now asserts
that no earlier requirement is dropped and that no name is duplicated.

## 11. Readiness

```
LeakIX        NOT_QUALIFIED    B2, last-detection timestamps
Netlas        NOT_QUALIFIED    A8, five load-bearing topics unresolved
ONYPHE        UNRESOLVED       B2 and B4
Shadowserver  NOT_QUALIFIED    B4, per-requester frame

qualified 0 of 4  →  PAIR_ANALYSIS_NOT_READY
```

No pair gate was evaluated. The two frozen negative controls were not researched
and no rescue was attempted.

## 12. What did not happen

```
measurement queries        0    trials      0
target counts              0    purchases   0
host records               0    facets      0
banners                    0    downloads   0
configuration endpoints    0    enquiries   0
first-party retrievals     7 of 8
```

0 canonical mutations, 0 sources registered, 0 governance reviews, 0 Claims, 0
Evidence, 0 reliability values, 0 independence groups, 0 Scores, 0 model calls, 0
embeddings. The Mission 1.56 Claim is untouched, the profile is still
`UNCALIBRATED`, Problem-Family is still `PARKED`.

## 13. Verification

| | |
|---|---|
| CI gates | 31, all green |
| bare-python | 1717 tests across 9 packages |
| pytest | 3310 tests, all suites passed, database unchanged |
| validator probe | 123 deliberate violations, 123 caught |

Three probe cases edited the frozen enquiry, and all three were caught.

## 14. Next

**`STOP_ON_ENQUIRY_CHECKPOINT`.** Pairing needs two qualified apparatuses and
there are none, so the enquiry checkpoint governs and A8 was not weakened to get
past it.

**The next action is provider contact, not more documentation search.** Two
missions have now exhausted the public route for the anchor's six operational
questions: Mission 1.62 read the most likely remaining policy document and it
addressed none of them, and this mission pursued the last named lead and its
schema is not published.

Three cheap reads would still move the candidate, each with a known URL and none
needing an enquiry: whether a datascan record is appended per scan or updated in
place, the membership of the datascan port set, and the identity of the fields
removed after thirty days.

To unblock the channel, the operator opens the anchor's legal page in a browser,
where the obfuscated contact address renders, and supplies the exact displayed
string.
