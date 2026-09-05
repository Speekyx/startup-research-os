# Mission 1.67 — Second Qualified Scanner Discovery V1

**Outcome: `NO_NEW_QUALIFYING_APPARATUS_IDENTIFIED_WITHIN_BOUNDED_SEARCH`.** Two
apparatuses nobody in this arc had evaluated were taken to complete packages. They
failed at two different gates, and **that pair of failures is worth more than either
one alone.**

---

## 0. The two halves of one conjunction

The construct needs two things at once: a temporal object that lets a window be
chosen before retrieval, and a retrievable surface carrying the bytes the peer sent.

Every apparatus this arc has examined has had at most one of them.

| apparatus | window chosen in the request | identification string retrievable |
|---|---|---|
| Censys (1.58–1.59) | no, merged current state | yes |
| Netlas (1.60–1.61) | yes, on the non-default path | yes |
| LeakIX (1.62) | no, last-detection dates | yes |
| Shadowserver (1.62) | yes | requester's own networks only |
| ONYPHE (1.62–1.66.2) | unresolved | yes |
| **Rapid7 Project Sonar** | **yes, dated immutable files** | **no** |
| **Shodan** | **no, real-time database** | not reached |

**Sonar is the first apparatus in this arc whose temporal object is right.** It fails
on the other half. That is a more useful result than a fifth candidate failing where
four already did.

## 1. Preconditions and budget

PR #111 merged at `6f9c901`, local main equal to origin, tree clean, migration head
`0035_refusal_provenance`. **Baseline measured live: every counter matched §0 exactly,
drift `none`** — and re-measured after the database-backed suites, still identical.

24 of 36 first-party requests, **12 carrying load-bearing content, 4 returning nothing
usable, and 8 failing outright. All 24 counted.** 12 navigation searches, used only to
locate exact first-party paths, because a guessed path that 404s spends document
budget. **2 serious candidates of a permitted 6.**

## 2. Rapid7 Project Sonar — the right temporal object, the wrong resource

Its addressing scheme is the strongest seen anywhere here: studies publish
individually named, individually addressed files —
`2018-06-15-1529049662-fdns_aaaa.json.gz`, reached at
`.../opendata/studies/{study_id}/{filename}/`, listed per study in `sonarfile_set`.
An artifact is selected **before** any measurement value is retrieved, which is §13's
own PASS example.

**A2 is PARTIAL rather than PASS**, because no retrieved document defines what the
date in a filename denotes — study start, completion or publication. A window maps
onto an artifact only if its date is defined, and the mechanism being right does not
make the semantics present.

What decides it is A3. The retrievable catalogue is eight datasets, and the only one
covering arbitrary TCP ports reads:

> SYN scan results for common TCP services across all of IPv4

with the provider's own wiki adding:

> Project Sonar runs numerous TCP studies every month. The output from these is a GZIP
> compressed CSV that contains the IP addresses that responded positively to the SYN
> for the port in question.

**A SYN response says a port answered and carries not one byte the peer sent.**
Meanwhile the about page states:

> Sonar scans a growing number of TCP and UDP services. TCP studies include SSH, SMB,
> Telnet, RDP, Mongo, Redis, CouchDB, and more.

So the identification string is **measured** and is **not in the published retrievable
catalogue**. That is `THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME`, recurring as a
catalogue-content restriction where Mission 1.62 met it as a per-requester one.

**It does not establish that Sonar cannot capture raw responses.** Its HTTP and HTTPS
datasets plainly do, and §16 forbids transferring their semantics to a TCP/22 resource.

## 3. Shodan — the other half

Own crawling is stated plainly: *"the crawlers work 24/7 and update the database in
real-time"*, *"Generate a random IPv4 address"*, *"The algorithm is designed to
randomly crawl the Internet once a week."*

**A2 fails on three independent first-party facts**, and the middle one is what makes
this a finding rather than an unexamined silence:

1. the database is documented as updated in real time — a maintained current state;
2. **the Filter Reference documents no time or date filter at all**, and it was
   fetched precisely to check, so the absence is an examined one;
3. the only historical surface is per-address — *"data going back up to 90 days"*, *"at
   most 1,000 banners"*.

**A per-address history requires already holding the address.** Obtaining the set for
a window means searching a real-time-updated database and inspecting timestamps
afterwards — retrieve-then-inspect, which Mission 1.59 rejected on a different
apparatus for the same reason.

**The honest answer is two-level and both halves are recorded.** At address level the
history parameter really is versioned observation history. At frame level, which a
count of distinct addresses needs, the object is a maintained current state.

**Shodan Trends was evaluated separately rather than failed by inheritance**, because
§16 makes that a rule. It fails three ways, any one sufficient: no date-range
parameter, counts rather than identification strings, and **documentation that does not
state what the count counts**. An undocumented count unit cannot witness a construct
requiring DISTINCT IPv4 and forbidding row, service-row and banner counts. It was not
executed, and both Shodan endpoints are recorded
`SECRET_BEARING_AND_MEASUREMENT_BEARING_DO_NOT_EXECUTE` — Mission 1.66.2's User API
lesson reaching a case where credential exposure and measurement contamination land at
once.

## 4. The frame-uniformity rule, adopted on a second instance

Mission 1.66.2 offered `APPARATUS_CONFIGURATION_MUST_BE_UNIFORM_ACROSS_THE_FRAME` and
declined to add it in passing. This mission found a second instance in a **different
shape**.

| apparatus | how the frame becomes heterogeneous |
|---|---|
| ONYPHE | declared regional partitions: *"same list of 500 ports"* against *"TOP 25 ports"* |
| Shodan | per-step randomisation: *"Generate a random port to test from the list of ports that Shodan understands"* |

**A rule demonstrated once looks like a rule about one provider's habits.** Two shapes
show it is about whether an apparatus publishes enough structure to say which
configuration reached which part of the frame, however the heterogeneity arose.

Distinct from three neighbours, each checked:

- **sampling** asks which *eligible* targets were attempted; this asks whether the
  predicate was eligible at all. A complete census of a partition that never opens
  TCP/22 returns zero, and no sampling disclosure repairs it;
- **the retrievable frame** asks what a *requester* may retrieve; this asks what the
  apparatus *measured*;
- **time-addressability** asks *when* a configuration applied; this asks *where*
  within one window.

**Registry 14 to 15**, produced before final candidate selection, nothing renamed or
merged, **0 historical verdicts edited**. A Mission 1.62 test pinning the total was
re-pointed from 14 to 15, exactly as Mission 1.63 re-pointed it from 13.

## 5. Four candidates died at the pre-gate, and that is not a finding about them

BinaryEdge's documentation host 301-redirects every attempted path to one Coalition
customer notice that itself returns 403. ZoomEye failed on all three of its documented
hosts. Criminal IP returned 403 twice. FOFA served a client-side navigation shell
twice.

**None became a serious candidate**, and each records what that does not establish — a
fact about this mission's reach, in the shape Mission 1.60 recorded for three
candidates that later documented fully.

**Outcome J was available and refused.** Documentation is numerically the largest
group, and reporting it as *the* binding limitation would misdescribe the two
candidates that documented themselves thoroughly and failed on epistemics. Mission
1.60's rule governs: name the established blocker, not the merely unexplored one.

## 6. The retrieval-summary guard fired twice

A search summary reported BinaryEdge scanning-engine internals and six months of host
history. Another reported Criminal IP field-level detail with an example timestamp.

**Neither exists at the addresses the live hosts serve.** Nothing from either was used,
in either direction. Mission 1.63's nonexistent sentence remains the canonical negative
control, and this is the first mission to meet its shape twice in one run.

## 7. The probe found two of its own defects and one of the validator's

- **Mutators returned a sub-record rather than the root**, so 44 cases were writing a
  fragment to disk instead of the record. The Mission 1.66 shape, one level along.
- **The restore set omitted a file a case mutated.** A case that edits Mission 1.66.2's
  ONYPHE package left it edited on disk, and the next run captured the damage as its
  baseline. **The positive controls are what caught it** — all four failed with the
  same message, which is the argument for having them. The probe now refuses to start
  against a corrupted tree and restores on any mutator exception.
- **One case escaped, and the rule was added rather than the record loosened.** An
  append-model discriminator beside a maintained-state temporal object was only refused
  on the A2 PASS branch, so the contradiction could sit in a record whose gate read
  FAIL and a later mission reading the discriminator alone would inherit it.

Final: **119 deliberate violations, 119 caught** — 115 by rule, 4 by drift, the four
being exactly the hand-edited generated pages — plus **4 of 4 positive controls**,
including a fully evidenced qualified package, a two-qualified readiness state that
still selects no pair, and a valid DECLINE leaving the registry at 14.

`testing-strategy.md` §23 recurred for the ninth time: a guard refusing any number
under a reliability-named key fired on the baseline's `reliability_assessments: 4`, a
census of rows already in the deployment. **Re-scoped to the records where an
assignment could occur, rather than loosened about what it refuses when it gets there.**

## 8. Nothing moved

| | |
|---|---|
| research data requests, API executions, measurement and count executions | 0 |
| hosts, banners, facets, downloads | 0 |
| trials, purchases, accounts, credential reads | 0 |
| mailbox searches, enquiries sent, follow-ups | 0 |
| sources registered, governance reviews, thresholds | 0 |
| canonical mutations, reliability values, independence groups | 0 |
| model calls, embeddings, migrations | 0 |
| pairs selected, pairs ranked | 0 |

ONYPHE stays `NOT_CHECKED_AFTER_DISPATCH` — a sent question is still not an answer, and
it improves no gate. Netlas stays unresolved with nothing decoded or guessed. **Total
apparatuses 6, qualified 0, so `PAIR_ANALYSIS_NOT_READY`.**

## 9. Verification

- **119 probe violations, 119 caught**; **4 of 4 positive controls**.
- **70 new tests**; **2089 bare-python tests**; all pytest suites passed with the
  database unchanged; all **37** CI gates, up from 36.
- Baseline re-measured after the database-backed suites: every counter identical.

## 10. Next

**§61 forbids rerunning the identical search.** The choice is between broadening
discovery in the same class, changing the protocol-native construct while keeping
product relevance, or choosing a different independently measurable product-relevant
quantity — and that choice needs its own mission.

What it should start from is §0's table. **Raw protocol capture and dated immutable
snapshots have never yet appeared in one apparatus.** If that is a property of the
market rather than of this search, option B is the one worth pricing: whether a
product-relevant predicate exists that a SYN-level or HTTP-level retrievable surface
can decide.

The ONYPHE enquiry runs in parallel and is not waited on. Netlas still needs one
address. **Mission 1.68 was not started.**
