# ADR-013 — Source governance as a gate, not a field

- **Status:** Accepted
- **Date:** 2026-08-29
- **Deciders:** Implemented in Mission 1.0 under brief §3–§32
- **Supersedes:** none. Resolves **D-07**, open since Mission 0.1.1
- **Related:** ADR-005, ADR-009, ADR-011, ADR-012;
  `docs/data/source-registry-v1.md`, `docs/data/data-principles.md` §13

---

## Context

`data-principles.md` §13 requires that, before integrating a source, the system
record its access method, API availability, usage restrictions, rate limits,
retention constraints, licensing and authentication requirements. Nothing
implemented that. D-07 recorded the gap and blocked `acquisition` outright:
until a registry existed, no source could lawfully be collected from, so the
Research Orchestrator marked the whole ACQUISITION capability BLOCKED with a
single sentence.

That block was correct and unusable. It could not say which source was missing,
nor what would have to change for one to become collectable.

The obvious shape — a `sources` table with an `is_approved` boolean — fails in
three specific ways, and each has been observed in systems like this one:

**A boolean cannot carry its basis.** Six months later nobody can say what
`is_approved = true` rested on, and when the platform revises its terms there is
nothing to re-check. The approval outlives the reasoning that produced it.

**A single verdict conflates independent questions.** The common real case is a
platform that permits automated API reads and forbids commercial use. One flag
forces a reviewer to answer both at once, and whichever answer they pick is
wrong for the other question.

**A technical fact drifts into a permission.** "A browser can load this page" and
"we may collect this page" are different statements. Stored in one field, the
first becomes the second, and *publicly visible* silently becomes *free to use*.

There is also a pressure the design has to survive: the number of approved
sources is the metric everyone naturally optimises, and it is the wrong one. A
registry where every platform came back approved would be evidence that the gate
does nothing.

## Decision

**Source governance is a derived gate over recorded evidence, not a stored
verdict.**

Six global tables, and one view that decides:

1. **Separate what from whether.** `source_access_profiles` records how a source
   could be reached and says nothing about permission. `source_policy_reviews`
   records what its documents permit and says nothing about how to reach it.
   They are different tables so that no reader can take one for the other.

2. **Assess eleven activities separately**, each with its own `PolicyAssessment`,
   scoped to one stated `assessed_use_case`. Silence is `NOT_ADDRESSED`;
   ambiguity is `UNCLEAR`; neither is permission.

3. **Approval requires retrieved, authoritative evidence.** The
   `PolicyEvidenceType` enum admits only first-party documents, operator
   correspondence and recorded legal reviews. There is no value for a blog post,
   so the type system refuses to record one as the basis of an approval. A
   `DEFERRABLE INITIALLY DEFERRED` constraint trigger enforces this at COMMIT,
   which lets a legitimate review be written atomically while still refusing an
   approval that never gets its evidence.

4. **Eligibility is a view, never a column.** `registry.source_eligibility`
   derives the verdict and returns `blocking_reasons TEXT[]`. A stored boolean
   can drift away from the reasons behind it; a derived one cannot.

5. **The database has the last word.** A `BEFORE UPDATE` trigger refuses to set
   `collector_enabled` on a source the view does not clear — whoever issues the
   statement, through whatever client.

6. **No write path over HTTP.** Authentication does not exist (ADR-005), so an
   endpoint able to approve a source would make the review optional for anyone
   who can reach the service. Review is administered by the `sros-source` CLI
   running as the migration role; the runtime role holds `SELECT` only on
   `registry.*`.

7. **Global, not tenant-scoped.** No registry table has a `workspace_id` and none
   has an RLS policy. A source assessed differently per workspace would make
   provenance incomparable across workspaces and would give one evidence record
   two meanings. ADR-012 governs tenant tables; these are not tenant tables.

8. **The orchestrator asks per source.** ACQUISITION's block is derived from the
   registry at plan time and names each refused source with its reasons. A
   planner with no registry wired blocks anyway: an unconsulted registry is a
   refusal, not an absence of objection.

## Consequences

### What this buys

An approval can be re-verified. Every one names the documents it rests on, who
read them, and when — so when a platform revises its terms, the check is
re-reading a named document rather than reconstructing a decision.

A refusal is actionable. The gate returns every failed condition rather than the
first, which is the difference between a reviewer fixing four things in one pass
and rediscovering them one at a time until they stop trusting the tool.

The prohibition is mechanical. "Do not collect from an unapproved source" is
enforced by a database trigger and a planner that cannot emit a dispatchable
job, not by remembering.

Approvals expire. Staleness blocks, per source, because an approval nobody has
re-checked is a statement about the past presented as a statement about now.

### What it costs

**The rules exist twice** — in Python for the CLI and the zero-dependency
validator, in SQL for the trigger. That is a real duplication risk, accepted
because each placement is load-bearing: the Python one must run with no database
(ADR-009's rationale), the SQL one must run under any client. It is managed by a
test asserting the two agree on every source rather than by trusting that they
do.

**Reviews are manual and they expire.** This is deliberate ongoing work, not a
one-time setup. A registry that never needed attention would be one whose
approvals had stopped meaning anything.

**Zero approved sources today, and acquisition stays blocked.** D-07 is resolved
— the registry exists and the mechanism works — but no source has passed the
gate. That is the correct first-pass outcome under this design, and the design
would be failing if it were not possible.

### Rejected alternatives

**A boolean `is_approved` field.** Rejected for the three failure modes in
Context.

**A numeric "legal confidence" score.** Rejected: no method produces such a
number, so it would be invented, and an invented number is trusted exactly like a
measured one. `UNCLEAR` and `open_questions` say the same thing honestly.

**Per-platform evidence reliability weights** (Reddit = 0.75, and so on).
Rejected: this is an evidence-aggregation decision blocked by **D-03**, and
assigning weights here would decide D-03 by the back door.

**Approving sources by default when their data is public.** Rejected outright.
This is the single failure this ADR exists to prevent.
