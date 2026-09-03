# Targeted Evidence Completion V1 — source selection

Version: 1.0
Status: Authoritative
Created: 2026-09-02 (Sprint 1 / Mission 1.30)
Use profile: `local-private-research-v1`

**This document was written before any Signal, Claim or Evidence was created, and
before any dimension mapping was added.** Mission 1.30 §20 requires the
source-selection decision to be recorded before acquisition; §16 forbids changing
a dimension mapping after inspecting whether a packet passes. Recording the
choice and its justification first is what makes both checkable.

---

## §0 The inspection matrix

Twenty-nine sources are registered. **Eight have a review under
`local-private-research-v1`**, and only those can be reached at all: approval
never transfers between profiles (ADR-027).

| source | family | collector | acquisition allowed (local) | model processing | external transmission | Docker/K8s/Podman subject match | potential new dimension | reliability | blocker |
|---|---|---|---|---|---|---|---|---|---|
| `stack-exchange` | forum | **yes** | **ELIGIBLE** | PERMITTED_WITH_CONDITIONS | PERMITTED_WITH_CONDITIONS | **yes — site tags `docker`, `kubernetes`, `podman`** | **PROBLEM_OR_NEED** | none | — |
| `wikimedia-pageviews` | knowledge | yes | eligible | PERMITTED_WITH_CONDITIONS | PERMITTED | yes — the three articles already held | none new (already AUDIENCE_OR_USAGE) | none | same dimension |
| `gdelt` | news | yes | eligible | PERMITTED | PERMITTED_WITH_CONDITIONS | terms could match, but | **none** — lexical frequency maps to no dimension | none | measures publisher behaviour |
| `world-bank` | economic_data | yes | eligible | PERMITTED | PERMITTED_WITH_CONDITIONS | no | none | none | no subject match |
| `ted-eu` | public_procurement | yes | eligible | PERMITTED | NOT_ASSESSED | no | — | none | §18 forbids touching it |
| `eurostat` | economic_data | **no** | eligible | PERMITTED | NOT_ASSESSED | no | — | none | no collector, no subject |
| `fred` | economic_data | **no** | eligible | PERMITTED | NOT_ASSESSED | no | — | none | no collector, no subject |
| `openalex` | knowledge | **no** | blocked | PERMITTED | NOT_ASSESSED | possible (scholarly works) | uncertain | none | **two unsatisfied conditions, no collector** |
| the other 21 | — | — | **no local review** | — | — | — | — | — | **`REQUIRES_REVIEW`; unreachable** |

**The candidate set is one.** Of the eight reviewed sources, five have a
collector; of those five, three cannot name Docker, Kubernetes or Podman at all;
one (`wikimedia-pageviews`) already supplies the packets' single dimension and
would add nothing; and one (`gdelt`) could match the terms but maps to **no
dimension** — Mission 1.28 established that a lexical frequency change measures
what media organisations published, which is producer behaviour and not an
opportunity dimension.

`github`, `npm-registry`, `pypi` and `hacker-news` are the sources a reader would
reach for first, and **all four are `REQUIRES_REVIEW` with no local-profile
review at all**. Reaching any of them is a source-review mission, not this one.

---

## §2 The selection

**Selected: `stack-exchange`, reused, with NO new acquisition.**

Against the priority rule in order: already registered (1); governance permits
acquisition under the local profile and the source is `ELIGIBLE` (2); the
collector exists (3); subject identity is a **site-assigned tag**, an exact
source-native identifier (4); it supports a dimension nothing else in the
portfolio can reach (5); its egress is already `PERMITTED_WITH_CONDITIONS`, so a
formable packet would also be synthesizable (6); the licence question is settled
CC BY-SA 4.0 with no open ambiguity (7); and reusing held records is the smallest
possible engineering step (8).

### Why no acquisition at all

**The minimum needed is zero, and that is a finding rather than a shortcut.**
Mission 1.20 already collected `tagged=docker` on `stackoverflow` over
2024-03-01 → 2024-03-31. That retrieval **provably did not truncate**: it ran one
page with `page_size=100` and returned **89** questions, and a short page means
the result set was exhausted. So the corpus already holds a *complete* set for
one canonical subject, in a window that overlaps the Wikimedia data (2024-03-01 →
2024-03-07) for the same three subjects.

§7 says to collect the minimum needed to test whether the new evidence type
works, and to prefer fewer. Fewer than zero is not available.

### Why Kubernetes and Podman are NOT acquired

**A truncated count is not a count.** §7 caps new acquisition at 30 RawRecords.
A complete count of `kubernetes` questions in a one-month window is far above
that bound — the held corpus already shows `kubernetes` appearing as a
co-occurring tag — so any retrieval within the cap would be censored by *our own*
bound and could support no volume statement at all.

`podman` is plausibly under 30 and was considered seriously. It was declined
because the outcome does not depend on it, the acquisition CLI has no
`stack-exchange` subcommand so it would require new live-acquisition machinery,
and a query that came back at exactly the cap would produce 30 records that
support nothing. **The precise follow-up is named in the report** rather than
attempted here.

### A source-native inconsistency, recorded because it decides the count

One of the 89 records — question `78089171` — was returned by a `tagged=docker`
query and its own stored tag list is
`["kubernetes", "next.js", "dockerfile", "environment-variables"]`, with no
`docker` in it.

So **"questions the query returned" (89) and "questions carrying the tag" (88)
are different quantities.** This mission counts the second: the Claim will say
*carrying the site's own tag*, and the tag list is the site's own vocabulary
recorded per record. Counting the first would count a question the site does not
label `docker`.

It also means **Kubernetes cannot borrow this evidence**: two `kubernetes`-tagged
questions sit in the corpus, but they arrived through a `docker` query and are a
biased subset, not a count.

---

## §1 The dimension, decided before the packet was inspected

**`community_question_volume` → `PROBLEM_OR_NEED`.**

### Why it is warranted

`PROBLEM_OR_NEED` asks: *is there evidence that some actor is blocked, burdened
or unserved?* A public question on a Q&A site is, by the site's own design, a
person stating they are stuck and asking for help. A count of such questions
carrying one site-assigned tag, over a bounded window, is direct evidence that
actors published requests for help in that subject area.

That is a genuinely different question from the one the existing evidence
answers. `AUDIENCE_OR_USAGE` says *something attended to this subject*; this says
*somebody said they were stuck on it*. Neither implies the other.

### What it explicitly does NOT establish

- **Not how many PEOPLE.** Author identity is never acquired (Mission 1.18), so
  the deployment cannot count distinct askers and one person may have asked
  several times.
- **Not that the questions share a problem.** Whether two questions express the
  same underlying problem is precisely the relation Mission 1.27 parked, and
  Missions 1.18 and 1.20 established that this deployment cannot decide it
  deterministically. The count is of questions, never of problems.
- **Not recurrence or frequency.** `RECURRENCE_OR_FREQUENCY` would require the
  previous point, so this mapping does not claim it.
- **Not severity, difficulty, or that anything is unsolved.** An accepted answer
  means only that the asker accepted one; its absence means only that they did
  not.
- **Not demand, market size, adoption, willingness to pay or a buyer.** None of
  those is measured by anybody publishing a question.
- **Not a population count.** It is a count over ONE site, ONE bounded window and
  ONE query, complete only because that retrieval demonstrably did not truncate.
- **The tag is a SUBJECT, not a problem** (Mission 1.18). `docker` identifies the
  subject area a question was filed under, in the site's own vocabulary, and
  nothing finer.

---

## §4 Deterministic subject identity across sources

The Wikimedia packets are keyed
`wikimedia-pageviews:content:en.wikipedia.org|Docker_(software)`. A Stack
Exchange signal would be keyed `stack-exchange:tag|docker`. **The subject key
includes the source id, so evidence from a second source family could never join
an existing packet** — the grouping introduced in Mission 1.28 is
source-scoped by construction.

That is the right default and it is what this mission has to extend, in the one
way §4 permits: an **explicit registry mapping reviewed in data**.

`canonical-subject-registry-v1.json` maps exact source-native identifiers onto a
canonical subject. Every entry names the source, the identifier scheme, the exact
identifier value, and a stated basis. There is no string distance, no token
overlap, no synonym table, no embedding and no threshold — an identifier either
appears in the registry or it does not, and an unmapped identifier keeps its
source-native key and its own packet.

**This is not `SAME_PROBLEM_FAMILY` under another name.** That relation asks
whether two OBSERVATIONS express the same problem, and is parked. This asserts
that two IDENTIFIERS, in two source vocabularies, name the same SUBJECT — a
question a person answers by reading two pages, not one a classifier decides.
