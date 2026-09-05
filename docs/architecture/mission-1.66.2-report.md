# Mission 1.66.2 — ONYPHE Public Documentation Reconciliation & Configuration-Metadata Closure V1

**Outcome: `ONYPHE_PUBLIC_DOCUMENTATION_RECONCILED_RESIDUALS_REMAIN`.** Twelve
first-party documents retrieved and re-read verbatim against the three residual
questions. **No load-bearing gate moved**, and establishing that is the result.

---

## 0. What a spent budget buys when it changes nothing

This mission used its whole documentation budget and moved nothing. That is worth
stating as the finding rather than apologising for.

**A budget that returns no gate change buys the difference between an unanswered
question and an unpublished answer.** An unanswered question might be closed by
reading more. An unpublished answer can only be closed by asking, by measuring, or
by choosing a different apparatus — and knowing which of the three you face is
what decides the next mission.

For ONYPHE, this mission decides it: **further public reading is exhausted.**

## 1. Preconditions and budget

PR #110 merged at `61fb5fb`, local main equal to origin, tree clean, migration head
`0035_refusal_provenance`. Both frozen hashes recomputed and matching. **Baseline
measured live: every counter matched, drift `none`.**

Twelve of twelve first-party requests, all ledgered. One 404'd on a guessed
data-model path — the index had been fetched first precisely to avoid that, and the
guess was made anyway. **It is counted, because a budget that only counts successes
is not a budget.** The brief's suggested target set also names a *Retrospective
2025 / Roadmap 2026*; the index carries no such page and none was invented.

One web search was used to locate pages. Its summary reported datascan as both a
bi-monthly and a weekly refresh **in the same paragraph** — which is why §1 exists,
and why nothing in this mission rests on a summary.

## 2. Four true statements that do not close B2

The discriminator was fixed before any page was read: *service S at address A on
port P is observed during window W, the SAME service is observed again AFTER W, and
can a query restricted to W still retrieve the observation inside it?*

The documentation supplies four things that sound like an answer:

| documented, verbatim | why it does not close the case |
|---|---|
| seven months of history for datascan | retention is not a storage model |
| *"Query data collected some hours ago"* | a maintained record whose timestamp advanced into that hour also matches |
| *"By default, latest result is displayed first on output"* | a default ordering presupposes several results, not two for one service |
| `-sort:0` reaching an older result | compatible with older results for *different* services |

Assembling those four into a case was the temptation, and each one is equally true
of the model that would **fail** the gate.

**The page most likely to settle it was fetched for exactly that reason** — the
write-up whose title names historical queries — and it states nothing about whether
a repeated scan creates a document or updates one.

And the data model still carries the sentence Mission 1.62 found, verbatim:

> timestamp of when the data was collected. Allows tracking when a given service or
> vulnerability was last observed.

One sentence, two temporal objects. **B2 stays PARTIAL** — now resting on a
directed search rather than on documents read for other purposes.

## 3. A new fact: the port set is region-dependent

From the Data Refresh Rate page, same category, same table:

> Once per week: a week from US, the other one from FR, same list of 500 ports
>
> Once per week: a week from SG, the other one from CN, TOP 25 ports

**One apparatus applies at least two configurations to different parts of its own
population.** If port 22 sits inside the 500 and outside the TOP 25, an address
reached only by the SG/CN rotation is not eligible to appear at all — and a count
would mix two populations selected under two different rules, **with the difference
living inside the apparatus rather than between apparatuses**.

Recorded as a **named risk rather than a defect**: whether 22 is in either list is
exactly what nobody has published.

## 4. And the configuration is documented as having moved

From the official retrospective, verbatim:

> From 200+ ports scanned to more than 400 ports;
>
> Bi-monthly refresh rate from FR and US countries, instead of once per month previously;
>
> More scanning from HK and SG locations (86 ports for SG & 42 for HK);
>
> Number of scanned ports: from 200+ to 1300+ per month

Port counts, cadence, scanner regions and category coverage all changed. That makes
`APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE` **demonstrated rather than
anticipated** — and it makes B4 **harder**: before, the port set was undated and
might have been constant; it is now known to move, and its value at a past window
is published nowhere.

The retrospective names **HK and SG**; the current page names **SG and CN**. Both
are first-party and they describe different moments. **That is drift, not
contradiction**, and reading it as contradiction would have been the error.

## 5. TCP/22, and the transfer refused again

The published port list carries exactly one section heading:

> TCP ports - ctiscan category (5,054 ports)

Port 22 appears under it. **There is no datascan TCP section.**
`DATASCAN_TCP22_UNKNOWN` — a configuration fact published for one resource does not
establish it for another, and **the absence of a section is not a statement that
datascan scans no TCP ports**, since the refresh page says it scans 500 of them.

## 6. The User API looked like a safe route and is not

Its appeal was real: it returns a port list, which is configuration rather than
measurement, so it would answer a question while fetching no hosts, no banners and
no counts.

Its own documentation says it lets you *"View name, API key, remaining credit count,
expiry date"* alongside *"List of scanned ports, both TCP & UDP"*.

**`SECRET_BEARING_DO_NOT_EXECUTE`.** Avoiding measurement contamination is one
property; not exposing a credential is a different one, and the second is not
implied by the first. It was **not executed**, and **no credential was read** to
check whether the documentation was loose — determining that would itself have meant
reading a credential store, which is a strange way to establish that credentials
must not be exposed.

**And it would not have answered the question anyway.** The port list carries no
category and no region mapping, and this mission established that the set differs by
both. A generic *scanned ports* list cannot be attributed to datascan. **Two
independent reasons, either of which alone stops the call.**

## 7. Retention: silence recorded as silence

> We keep the last 30 days of data will all the fields and up-to 16KB of raw
> application responses. For data older than 30 days, we remove some fields as they
> are less useful, and we truncate data field to 4KB.

The sentence **names the field it truncates and does not name the fields it
removes.** So `data` truncation is not removal, B3 is not reopened, and the address,
the observation timestamp and the three scanner-node fields stay **UNKNOWN in both
directions**.

Two arguments were available and refused: that an archive would be useless without
addresses (an argument from what a sensible provider would do), and that historical
querying proves timestamps survive (it proves records are reachable, not which
fields they still carry).

## 8. A support channel, and a mission not rewritten

From the official blog, three times on the page:

> Do you have any questions? Contact us at support[at]onyphe{dot}io

**Cited, not inferred from spelling** — which matters, because a conventional
support mailbox is exactly the kind of address a system could guess.

**Mission 1.65 is not rewritten.** It recorded that the pages *it* inspected publish
no dedicated support route. That was accurate then and is still a true statement
about that moment. A document found later extends the evidence; it does not falsify
the earlier reading.

The enquiry is **not resent**, no second envelope exists, and the one send stands.
The address is recorded **as printed** rather than normalised into a usable mailbox:
nothing is being sent, so nothing needs normalising. That is also why this is not
the Netlas case — there the address is served through a mechanism that returns a
placeholder to automated retrieval, and obtaining it would mean defeating that
mechanism. Here the page's literal text contains it.

## 9. A registry rule offered and not added

`APPARATUS_CONFIGURATION_MUST_BE_UNIFORM_ACROSS_THE_FRAME` — where one apparatus
applies different configurations to different parts of its own population, a single
count mixes populations, and the apparatus must publish which configuration reached
which part of the frame.

It is distinct: `SAMPLING_IS_LOAD_BEARING` compares population definitions
**between** apparatuses, `THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME` governs
what a requester may retrieve, and the time-addressability rule governs **when** a
configuration applied. None governs heterogeneity **within** one apparatus at one
time.

**It was not added.** A documentation-reconciliation mission editing a frozen
apparatus contract in passing is the change-control shape `docs/CLAUDE.md` §Change
control refuses. It is recorded with its justification for **Mission 1.67**, which
selects apparatuses and would apply it before choosing rather than after.
**Registry unchanged at 14.**

## 10. The validator refused this mission's own record

A guard asserting that Mission 1.65's *no dedicated support channel* sentence
survives was written against a phrase in the **rendered prose**. The page renders it
as *What it is not:* rather than *not a dedicated*, so the guard fired on a record
that was completely intact.

`testing-strategy.md` §23 for the eighth time. Re-anchored to the **record's own
field** and to the sentence whose deletion would *be* the rewrite — structural,
rather than loosened until it passed.

## 11. Why outcome C and not B

Outcome B needs a previously unresolved load-bearing question definitively closed.
The closest candidate is configuration mutability, which moved from unknown to
established.

**But establishing that a configuration CHANGES moves no gate toward PASS.** It
makes the time-addressability question more necessary, not less. Reporting B would
let that read as progress toward qualification when it is the opposite.

## 12. Nothing moved

| | |
|---|---|
| API executions of any kind, credentials read | 0 |
| mailbox searches, enquiries sent, follow-ups | 0 |
| measurement queries, counts, hosts, banners | 0 |
| trials, purchases, sources registered | 0 |
| canonical mutations, reliability values, pairs selected | 0 |
| model calls, embeddings, migrations | 0 |

ONYPHE stays `INDIVIDUALLY_UNRESOLVED`. Netlas, LeakIX and Shadowserver are
untouched. **Qualified 0 of 4, so `PAIR_ANALYSIS_NOT_READY`.**

## 13. Verification

- Validator probed with **214 deliberate violations, 214 caught** — **209 by rule,
  5 by drift**, the five being exactly the hand-edited generated pages. Record
  mutations go through `validate()` directly, so drift can never stand in for a
  rule (Mission 1.66.1's methodology).
- Two probe defects found and fixed: a dotted-path helper that could not address a
  key containing a dot (`node.id`), and a case with a dead conditional that
  **mutated nothing**.
- **84 tests**; **2019 bare-python tests**; all **36** CI gates.

## 14. Next

**Mission 1.67 — Second Qualified Scanner Discovery V1.** What is missing is a
fifth candidate, not a fifth document. It should carry the offered requirement
forward to adopt or decline, apply gates before choosing, and check documentation
retrievability before treating an apparatus as a candidate.

The ONYPHE enquiry runs **in parallel** and is not waited on. Netlas still needs one
address, readable in a browser. **Mission 1.67 was not started.**
