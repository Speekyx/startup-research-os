# Mission 1.68 — Product-Relevant Measurement Construct Selection V1

**Outcome: `NO_PRODUCT_RELEVANT_CONSTRUCT_WITH_TWO_ROUTES_IDENTIFIED`.** Five
constructs, seven apparatuses, and **every construct has exactly one plausible route —
a different apparatus each time.**

---

## 0. The finding, which needed five constructs to become visible

| construct | product relevance | its one plausible route |
|---|---|---|
| C0 SSH identification (control) | moderate | Netlas |
| C1 TCP/22 SYN responsiveness | moderate | Rapid7 Sonar, `sonar.tcp` |
| C2 HTTP response to an IP-addressed GET | moderate | Rapid7 Sonar, HTTP study |
| C3 TLS certificate observation | weak | Rapid7 Sonar, certificate studies |
| C4 DNS record configuration | weak | Rapid7 Sonar, FDNS/RDNS |

**The apparatuses are individually capable and pairwise disjoint.** They are not
failing to measure. They are failing to measure the same thing as each other, on the
same population, with the same temporal object.

**And there is a reason, which is commercial rather than technical.** A scanner product
publishes SERVICES — what is running where — because that is what its customers buy,
and a service record presupposes a response. The discovery stage, which port answered,
is an internal step these products do not publish as a separately addressable artifact.
Sonar publishes it because `sonar.tcp` is a research dataset rather than a search
product.

Pursuing one construct would have produced a fifth mission ending the same way, without
the explanation.

## 1. Preconditions and budget

PR #112 merged at `c4049cd`, main synced, tree clean, migration head
`0035_refusal_provenance`, registry at 15. **Baseline measured live: every counter
matched §0 exactly**, and re-measured after the database-backed suites, identical.

11 of 18 first-party requests, 3 navigation searches, 5 serious constructs of a
permitted 6. **A sixth was deliberately not invented** — §6 says not to fill the slot.

## 2. Why a pivot was allowed, and why it is not a relaxation

The SSH identification predicate is not something this product promises anybody. It was
chosen to prove that two independently produced observations can witness one
source-independent proposition, so the aggregator stops being algebraically identical
to baseline B-2.

**The control was evaluated through the same matrix rather than exempted**, and its
status stays `NO_TWO_QUALIFIED_APPARATUS_ROUTE_IDENTIFIED` — never FAILED,
BAD_CONSTRUCT or INVALID. Its problem is reachability under the apparatus market as
documented. It has one plausible route, Netlas, which is recorded rather than hidden.

## 3. C1 came closest, and not selecting it is the whole of §30

`sonar.tcp` publishes *"regular snapshots of the responses to zmap probes against
common TCP services"* as dated immutable per-port files:

    2026-09-05-1788609721-tcp_dns_53.csv.gz
    2026-09-04-1788552721-redis_9051.csv.gz

**The filename carries the date and the port**, so a file is selected by both before any
value is retrieved. That is the strongest single route the arc has produced.

Its second route is UNRESOLVED rather than blocked, on two apparatuses. **The decisive
question is one sentence wide:**

> Does any apparatus publish, as a separately addressable artifact, a record that a port
> ACCEPTED A TCP CONNECTION WITHOUT PRODUCING AN APPLICATION RESPONSE?

Netlas's collection is named Responses; its documented fallback field stores *"the
unparsed network response"*, which presupposes the peer sent something; and no retrieved
page says whether a document exists otherwise. If it does not, Netlas counts a strict
subset and the same-proposition gate fails.

**Selecting C1 on the expectation that the missing sentence exists would preregister an
experiment on a route nobody has established.**

## 4. A SYN response is never an SSH server

Enforced structurally as well as lexically: a SYN predicate may not carry an SSH
subject, must state why the two differ, and must refuse the reading in its explicit
non-claims.

A SYN response is a transport-layer fact produced by the operating system's TCP stack.
Nothing about it identifies the application listening, and a port may be forwarded,
honeypotted, firewalled-open or answered by something unrelated. The whole content of
RFC 4253 §4.2's discriminator is absent from it.

This is the promotion the C1 family invites, and taking it would have quietly restored
the construct the arc could not reach.

## 5. Blockers are global or construct-specific, and it matters in both directions

**One correctly disappeared.** Mission 1.67 blocked Sonar because its arbitrary-TCP
resource carries no response bytes. That is construct-specific, and a transport-level
predicate does not ask for response bytes. Carrying it forward would have repeated
Mission 1.67's answer without repeating its work.

**Three correctly survived.** Shodan's and LeakIX's temporal architectures and
Shadowserver's per-requester frame are global. No change of predicate repairs where a
timestamp points or which networks a requester may retrieve.

**And one appeared where it had never applied.** On ports 80 and 443 Netlas queries
*"not only by IP address but also by domain names"*, limits *"the number of virtual
sites per IP to 100,000"*, and saves *"each response as a separate document"* across up
to five redirects — with the Host header it sends undocumented. On every other port it
sends requests by IP address without domain names, so the blocker is genuinely specific
to a web-port construct.

## 6. Censys, re-examined resource by resource

A search summary reported that Censys *publishes an updated daily snapshot of the state
of the public address space*. The Platform historical-data page says instead:

> Every time that Censys performs a scan against a host, Censys preserves a snapshot of
> that host during that point in time.

reached through Service History and Scan History tabs **after a host is found**. And its
host dataset documents `host.services.scan_time` as *"When the service was last observed
by a Censys scan"* — **the exact temporal object Missions 1.58 and 1.59 rejected,
re-confirmed on current documentation rather than carried over from a report.**

**This is the third time the retrieval-summary guard has fired, and the first time on a
summary that was FAVOURABLE to a candidate.** That is the harder direction, and it is
why the rule is not about caution.

The Universal Internet Dataset is genuinely different — snapshots with *"a unique ID
based on the date it was taken"*, addressed individually, the second dated immutable
artifact in this arc alongside Sonar. It stays UNRESOLVED because raw banners are not
mentioned, the schema is directed to a page inside the authenticated console, and its
contents are described as *"enriched with third-party data"*, an open-ended clause
`ENUMERATED_EXCEPTIONS_MAKE_A_LINEAGE_CLAIM_CHECKABLE` refuses.

Its research route is non-commercial-only, which this product's stated commercial
purpose cannot accept; an Enterprise route exists and would need its own governance
review. **Recorded, and not used as an epistemic disqualifier.**

## 7. Outcome F was available and refused

F asserts the apparatus class itself is the dominant limitation. The evidence points
that way and does not establish it: several cells are UNRESOLVED rather than BLOCKED,
and one documented sentence would give C1 two routes.

Reporting F would convert *this mission could not establish it* into *it cannot be
done*, which is the conversion this repository has refused since Mission 1.60.

## 8. Held evidence paid for itself, measurably

Eleven retrievals answered a seven-apparatus, five-construct matrix. Mission 1.67 spent
twenty-four on two apparatuses.

The difference is the records already in the repository: Netlas's gate verdicts and its
ten-topic A8 matrix, ONYPHE's five gate verdicts and category list, LeakIX's and
Shadowserver's blockers, Shodan's filter-reference absence, Sonar's SYN-only output and
eligible frame. New retrieval was spent only on construct-specific questions no record
answered.

## 9. A reusable rule was offered and not added

`A_PUBLISHED_SURFACE_IS_THE_SALEABLE_OBSERVATION_NOT_THE_MEASUREMENT_PIPELINE` — where
an apparatus performs a multi-stage measurement and publishes only the stage its
customers buy, the earlier stages are not retrievable however thoroughly performed.

It is real and it has **one shape so far**. Mission 1.66.2 offered the frame-uniformity
rule and Mission 1.67 adopted it only after finding a second independent instance in a
different shape. The same standard applies here. **Registry unchanged at 15.**

## 10. Nothing moved

| | |
|---|---|
| measurement values retrieved, target-value exposures | 0 |
| API executions, count endpoints, hosts, banners | 0 |
| dataset downloads, trials, purchases, accounts | 0 |
| credential reads, mailbox searches, enquiries sent | 0 |
| sources registered, governance mutations, thresholds | 0 |
| canonical mutations, Claims, Evidence, reliability values | 0 |
| model calls, embeddings, migrations | 0 |
| pairs selected, apparatus pairs compared | 0 |

ONYPHE stays `NOT_CHECKED_AFTER_DISPATCH` and its outstanding enquiry improves no gate.
Netlas stays unresolved with nothing decoded or guessed. **Qualified apparatuses 0, so
`PAIR_ANALYSIS_NOT_READY`** — and a plausible route is not a qualified apparatus.

## 11. Verification

- Validator probed with **109 deliberate violations, 109 caught** — 106 by rule, 3 by
  drift — plus **4 of 4 positive controls**: a valid non-viable set, a two-route viable
  construct, a properly evidenced selection with its artifact, and an alternative
  no-selection outcome.
- One probe defect fixed, the Mission 1.67 shape again: mutators returning a sub-record
  rather than the root. The restore set covered every file a case touches from the
  start, which was 1.67's other lesson.
- **62 new tests**; **2151 bare-python tests**; all pytest suites passed with the
  database unchanged across 29 tenant tables; all **38** CI gates.
- A mid-run baseline measurement showed four counters at +1. That was pytest fixtures in
  flight, confirmed by re-measuring after the run and by the runner's own
  database-unchanged check. **Recorded here because it looked exactly like drift.**

## 12. Next

**§52's branch: a strategic pivot mission, not a sixth construct in the same class.**
Mission 1.69 — Independent Product-Relevant Quantity Class Selection V1 may leave the
internet-scanner apparatus class entirely.

Before or alongside it, one narrow question is worth asking because it is cheap and
would change C1's verdict: whether any apparatus publishes a record that a port accepted
a TCP connection without producing an application response. It needs no discovery sweep,
and this project has an enquiry channel it has used once.

**Mission 1.69 was not started.**
