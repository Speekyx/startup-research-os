# Mission 1.59 — Internet-Wide Service-Presence Route Gate Closure V1

**Outcome: `SNAPSHOT_TIME_SEMANTICS_NOT_ALIGNABLE`.** No route selected.

---

## 0. The finding

The two scanners really do probe independently. They really do measure the same
construct. And they **publish different kinds of temporal object**.

```
apparatus B   a stream of observations, each carrying a documented scan_date
apparatus A   a maintained current state, searchable by LAST-CHANGE time
```

**The deciding evidence is one vendor's own worked example.** A host observed by
its scanner every day for five days *without change* carries a searchable
last-updated timestamp from five days ago, and its per-service observation time
is documented as **not searchable**, because observation timestamps change too
fast to publish.

So the same window filter selects **hosts whose record changed** during the
window on one side, and **hosts observed** during it on the other. A host present
and unchanged throughout is in one set and missing from the other — and a
contradiction produced that way would be an **artefact recorded as a finding**,
which is the worst failure available to this layer.

## 1. Baseline

Verified live, no drift: 325 / 325 / 33 records, 44 Claims, 45 revisions, 58
Evidence, 1 INFERRED Claim, 1 threshold, 1 derivation, 0 refusals, `SUPPORTS 57 /
CONTRADICTS 1`, 0 Claims carrying both, head `0035`, main `7cfcd88`.

The pair Mission 1.58 froze was evaluated. **It was not substituted** — swapping
in something easier to document would answer a different question and call it
closure.

## 2. Gate 5 — the one that decided it

Four alignment rules were evaluated (§15) and **all four refused**, including the
two that would have salvaged the route:

| rule | verdict | why |
|---|---|---|
| exact timestamp equality | impossible | independent scanners do not probe at one instant, and one side's observation time is unsearchable |
| shared bounded observation interval | not available | exactly the right rule, and one side documents no aggregate window selector |
| pre-frozen tolerance Δ | **refused** | §16 demands an operational basis, and the merged side publishes **no bound on staleness**. Any Δ would be a round number chosen because it rescues the route |
| snapshot inside the other's interval | **refused** | establishing it needs per-host timelines, i.e. retrieve the set then inspect it — the procedure §18 fails the gate for |

**`FAIL` rather than `UNKNOWN`, and the distinction is earned.** The cadence
document Mission 1.58 could not retrieve was pursued and *answered*: one side
documents a per-record `scan_date` recording when the scanning that generated the
response occurred. This is an established mismatch on first-party documentation
from both sides, not a document nobody found.

## 3. Gate 3 — what survives

The construct is now defined **protocol-natively**, and written source-free so
any future pair can be asked for it:

> the number of distinct public IPv4 addresses from which, during a defined
> window, a TCP connection to port 22 was accepted and the peer sent an
> identification string beginning with the literal prefix `SSH-`, before any
> negotiation.

**RFC 4253 §4.2** fixes it: the server sends that string immediately on
connection and before key exchange, and other server output must not begin with
that prefix. No vendor taxonomy, no fingerprint database.

**Matching vendor labels are refused as metric equivalence.** Two vendors may both
say PRODUCT-X while using different signatures, versions, banner fields and
post-processing. Agreement between two proprietary opinions is not a definition.

**And the narrowing removes a shared upstream nobody had noticed.** A version- or
vulnerability-flavoured metric would have pulled one CVE database into the
load-bearing path on *both* sides — a common upstream for the metric's *meaning*
even though the scanning stays independent.

Gate 3 remains `UNKNOWN`: the construct is definable, and it is not established
that either apparatus exposes a query surface deciding that predicate rather than
its own assigned service label.

## 4. Gate 10 — advanced, not closed

Pursued only for the side that survives, because gate 5 had already dropped the
pair and further budget on the other side would have been spent on a dropped
route.

Apparatus B moved from **an absence of any third-party reference** to a
**positive statement about the load-bearing records**: each document is a single
service response *collected during scanning*, and `scan_date` records when the
scanning that *generated* it occurred. Auxiliary enrichment (registry, WHOIS,
certificates) is named separately.

Still `PARTIAL`. None of that is an affirmative statement that no external
measurement feed is load-bearing, and §22 forbids upgrading from omission.

A written enquiry is **drafted and not sent**. It asks for facts about lineage
rather than for the word *independent*, which invites interpretation rather than
information.

## 5. Three gates reopened

| gate | was | is | why |
|---|---|---|---|
| 6 population/frame | PASS | UNKNOWN | under high service density one side's service data is a **sampling**, not a census. §28 forbids calling a partial frame internet-wide |
| 11 reliability reviewability | PASS | UNKNOWN | the narrowed metric turns on a wire-level decision one side keeps proprietary |
| 13 threshold freezable | PASS | FAIL | a bound can only be frozen in advance if the observations it will meet can be identified in advance |

**That is the audit working, not the mission failing.** They were passing on less
evidence than they are now failing on.

Final matrix: **PASS 9, FAIL 2, UNKNOWN 4, PARTIAL 1.**

## 6. The generalisable diagnostic

> A dataset can be excellent and still be the wrong **temporal object**.

A maintained current-state view answers *what is running now*. A preregistered
threshold proposition asks *what was observed during a window*. Both are
legitimate products, and only one of them can witness this kind of Claim.

Hence the new apparatus requirement, to be applied **before** a pair is chosen:

> **`OBSERVATION_ADDRESSABLE_EXPOSURE`** — an apparatus qualifies only if a
> future observation can be attributed to a defined window from its published
> surface, before any value is retrieved.

That is not the same as scanning often, and Mission 1.58 could not have known to
ask for it.

## 7. What did not happen

```
measurement endpoints called   0
measurement values fetched     0
paid access purchased          0
trials started                 0
first-party doc requests       8 of 12
```

The zeroes are load-bearing: `PREREGISTERED` is defined against **retrieval**, so
one value fetched here would have destroyed it permanently for this metric.

0 canonical mutations, 0 sources registered, 0 governance reviews, 0 collectors,
0 threshold registrations, 0 Claims, 0 Evidence, 0 reliability values, 0
independence groups, 0 Scores, 0 Opportunity changes, 0 model calls, 0
embeddings. The Mission 1.56 Claim is untouched.

## 8. Verification

| | |
|---|---|
| CI gates | 27, all green |
| bare-python | 1488 tests |
| pytest | 3310 tests |
| validator probe | 77 deliberate violations, 77 caught |

One probe **escaped on the first run**: a sentence conflating structural
non-republication with apparatus lineage was accepted. The validator was
tightened to require both levels named and held apart, rather than the record
loosened.

## 9. Next

**Mission 1.60 — Observation-Addressable Scanner Pair Selection V1.** §67 drops
the pair on this outcome, not the class, and forbids paying for governance or
access.

Apply `OBSERVATION_ADDRESSABLE_EXPOSURE` and the vantage/frame questions
**before** selecting, carry the protocol-native construct forward unchanged, and
carry apparatus B forward as a candidate side — its exposure model is the one
that fits.

It must not fetch a measurement value, purchase access, accept a vendor product
label as the metric, or read an absence as a statement.
