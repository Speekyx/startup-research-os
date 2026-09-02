# ADR-034 — A fifth Signal quantity family: `COMMUNITY_QUESTION_VOLUME`

Status: Accepted
Date: 2026-09-02
Mission: 1.30
Supersedes: nothing. Extends ADR-020 (Signal contract) and follows ADR-029 and
ADR-032, which added the third and fourth families for the same class of reason.

---

## Context

The Opportunity Engine (Mission 1.28) grouped the 26 canonical Evidence rows into
nine packets and found none formable. The three Wikimedia packets —
`Docker_(software)`, `Kubernetes`, `Podman` — each hold six rows carrying exactly
one counting dimension, `AUDIENCE_OR_USAGE`. They need **one genuinely different
dimension**, not more rows of the same kind.

This deployment has held 104 `community_question` records since Missions 1.18 and
1.20, including **89 questions retrieved for `tagged=docker` on Stack Overflow
between 2024-03-01 and 2024-03-31**. Nothing has ever derived from that record
kind: Mission 1.18 correctly found no derivation available (a tag is a subject,
not a problem, and no two questions could be shown to share one), and Mission
1.20 closed the deterministic route to *repeated-problem identity*.

**Counting questions is a different question from identifying problems**, and it
is one the records can answer.

## Decision

Add `COMMUNITY_QUESTION_VOLUME` to `SignalQuantityFamily`, and the signal type
`community_question_volume` reading the `community_question` record kind.

> How many public questions carrying one identifier from a community site's own
> tag vocabulary were **created** on that site during a bounded window, as
> counted over records this deployment holds.

Scope carries a site, a tag scheme and a tag. It carries **no metric, no
geography, no term and no requester class**.

## Why not widen an existing family

Two candidates existed.

**`MEASURED_SERIES`** asks for a `metric` and a `geography`. A count of questions
filed under a tag is an instance of no series anybody publishes and belongs to no
place. Widening it would make `metric` optional for every World Bank signal ever
written — the objection that produced ADR-029 and ADR-032.

**`CONTENT_REQUEST_VOLUME` is the near miss, and rejecting it is the substance of
this ADR.** Both are counts over a bounded period, both carry an item-like
identifier and a platform, and neither has a metric or a geography. The fields
would have fitted without complaint.

**A request is something a READER makes of a server. A question is something a
PERSON publishes about being stuck.** Widening that family would not have cost a
FIELD its meaning the way a procurement value would have cost `metric` its
meaning — it would have cost the FAMILY its meaning. A pageview and a request for
help would have become the same kind of quantity, and every consumer branching
exhaustively on the family would have treated them alike without ever deciding
to.

That is the same argument ADR-032 made one source earlier, and it is the reason
these families are closed: an unhandled value is a bug, and a silently widened
one is worse, because nothing reports it.

## Why the name refuses the interesting words

`PROBLEM_VOLUME`, `PROBLEM_FREQUENCY`, `USER_PAIN_VOLUME`, `COMMUNITY_DEMAND` and
`UNMET_NEED_VOLUME` were all available. Each would have put an interpretation in
the vocabulary, where **a field name survives every later caveat** — the rule
Mission 1.19 established when it chose `content_request_count` over
`wikimedia_pageview` and over `content_view_count`.

`QUESTION` is what the source publishes. `PROBLEM` is what a reader wants it to
mean, and whether two questions express the same problem is precisely the
relation Mission 1.27 **parked**. A family named for problems would have made the
parked relation look answered by a count.

## What a signal of this family does NOT establish

- **Not how many PEOPLE.** Author identity is never acquired (Mission 1.18), so
  distinct askers cannot be counted and one person may have asked several times.
- **Not that the questions share a problem.** `SAME_PROBLEM_FAMILY` is parked and
  this family must operate without it.
- **Not recurrence or frequency in the world**, which would require the previous
  point.
- **Not severity, difficulty, or that anything is unsolved.** An accepted answer
  means only that the asker accepted one.
- **Not demand, market size, adoption, buyers or willingness to pay.**
- **Not a population count.** It counts what one bounded retrieval returned.

## Completeness is a precondition, not a caveat

A count is meaningless if the retrieval that produced it was truncated by **our
own** bound. So the derivation must establish non-truncation and **refuses
otherwise** — it does not emit a qualified number.

For the Mission 1.20 corpus the proof is structural: one page was fetched with
`page_size = 100` and returned 89 records, and a short page means the result set
was exhausted. Had it returned exactly 100, no signal would be derivable from it.

This is the ADR-021 rule applied to a new failure mode: **a blocked derivation
produces no Signal**, never a Signal with a warning attached.

## Consequences

- Migration `0030` widens the `quantity_family` CHECK and registers the type.
- `SignalScope` gains `community_sites`, `community_tags`, `community_tag_scheme`,
  absent from every other family's scope by the no-null-keys rule.
- `facts.py` gains `_TEMPORAL_KINDS`: the new kind supplies the temporal facts and
  **not** `EXACT_NUMERIC_VALUE`, because a question carries no measured value.
  Folding it into `_COUNTING_KINDS` would have granted it one by omission — the
  same trap Mission 1.19 avoided when it separated `_COUNTING_KINDS` from
  `_BOTH_KINDS`.
- The Stack Exchange record kind is reachable by a derivation for the first time
  since it was created.
- **Nothing downstream is unblocked.** A signal of this family produces
  NON_SCORABLE Evidence like every other, because no reviewed reliability applies
  to its measurement-by-purpose scope.
