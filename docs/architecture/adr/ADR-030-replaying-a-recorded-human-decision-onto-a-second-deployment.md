# ADR-030 — Replaying a Recorded Human Decision Onto a Second Deployment

**Status:** Accepted · **Date:** 2026-09-01 · **Mission:** Sprint 1 / operational
**Supersedes:** nothing. **Amends:** nothing. **Narrows:** Mission 1.15.6's
refusal to ship a human-decision CLI verb, by naming one thing that refusal does
not cover.

---

## Context

### The refusal this ADR must not reopen

Mission 1.15.6 refused to build a CLI verb for recording a human decision, and
Mission 1.15.6.1 recorded that the refusal held even while a decision was being
recorded:

> **No CLI verb was built** — Mission 1.15.6 refused to build one and that
> decision stands; the row came from a one-off act that is not part of the
> repository.

The reasoning is in `docs/CLAUDE.md` §A condition is verified where it can be,
and confirmed where it cannot: a judgement, a risk acceptance, a legal
conclusion or a promise about future conduct stays `HUMAN_CONFIRMATION`. A verb
that records such a thing makes recording it routine, and **a decision that is
routine to record is not a decision**.

That reasoning is correct and this ADR does not touch it.

### The operational fact that forced the question

The operator runs Startup Research OS on **two machines**, which
`context/CONTEXT.md` has recorded since Mission 1.15.8 and which
`README.md` §Research data does not travel either states as a property of the
system:

- the **catalog** travels by git, and `sros-source load` reproduces it exactly;
- **research data** does not travel, and is regenerable by re-running the
  pipeline;
- the **human decision** travels by nothing, and is regenerable by nothing.

`registry.source_condition_verifications` holds one row recording the operator's
acceptance of the residual TED database-right exposure. On the second machine
that row does not exist, TED is not eligible, and no shipped command can change
that.

### What the alternative actually is

Not "do without". The operator would retype a **1683-character** legal
acknowledgement, in French, by hand, on the second machine — and the row exists
precisely to preserve that **the words accepted are exactly the words
reviewed**. Retyping is the option that most endangers the property the row is
for.

This is the shape of the problem: the refusal protects the *deciding*, and the
cost is falling on the *transcribing*.

## Decision

**A single-purpose replay script may exist for one already-made, already
documented human decision. A general verb still may not.**

`infrastructure/scripts/record_ted_operator_acceptance.py` records exactly one
row and can record no other. The distinction it rests on:

| | a `decide` verb | this script |
|---|---|---|
| Whose decision | any the caller supplies | one, already made and documented |
| Subject | any source, condition, profile | literals in the module |
| Wording | typed by the caller | a literal, byte-identical to the recorded row |
| Verdict | a parameter | `SATISFIED`, a literal |
| Can record a NEW decision | **yes** | **no** |

**It has no parameters**, and that is the load-bearing property rather than a
convenience: a parameter is precisely how a replay becomes a verb.

### Four refusals, each protecting a different failure

1. **The condition is looked up, never trusted from a constant.** The script
   resolves `(source_id, condition_key, assessed_use_profile)` against the live
   database and refuses unless it finds exactly one current condition.
2. **The review version must match.** An acceptance written about review v2
   attached to a v1 condition would record a decision about a document nobody
   read. `context/CONTEXT.md` already warns that `git pull` does not load the
   catalog and that a machine can carry an older review with no visible sign;
   this is that warning made mechanical.
3. **The condition must be `HUMAN_CONFIRMATION`.** A condition a machine can
   verify must be cleared by `sros-source verify --apply`, and this script
   refuses to substitute for a verifier.
4. **Exactly one row, ever.** A second acceptance of one decision reads either
   as two people accepting or as one person accepting twice after something
   changed. Neither happened.

### The act stays human

The script **prints the full acknowledgement** and requires the operator to type
a confirmation phrase before writing. Reading it is the act; the script is the
transcription. It refuses when there is no terminal to confirm on, so it is not
a step a pipeline can run.

## Consequences

**What this permits.** The operator can bring a second local deployment to the
same governance state as the first, without retyping a legal acknowledgement and
without the possibility of retyping it differently.

**What this still forbids.** Recording a decision nobody made. Recording a
different decision. Clearing another condition. Clearing this condition under
another profile or another review version. Any of those needs a person and a
document, exactly as before.

**What it does not do.** It does not make the acceptance travel. Each deployment
still records its own row, deliberately: the acceptance is about a **deployment**
and its conditions — bounded queries, field minimisation at acquisition, no
redistribution — and a second machine is a second deployment where those must
hold independently.

**The identity is derived, and one row is an exception.** The row id is a
`uuid5` over the condition and the verifier, so every machine that replays
converges on one identity instead of inventing a fresh `uuid4`. The machine
where the acceptance was **first** recorded, in Mission 1.15.6.1, keeps its own
historical id and is not rewritten to match. Two ids for one decision is the
honest record of how each row got there.

**The boundary is now written down rather than remembered.** The cost of not
writing this ADR would be a shipped script that appears to contradict a mission
report — and a later reader having to reconstruct which of the two was current.

## Alternatives considered

**Build the general `decide` verb.** Rejected. It is the thing Mission 1.15.6
refused, and none of the reasoning against it has weakened. The operational
problem is narrow and does not need a general answer.

**Keep the script outside the repository.** Rejected, and this was the closest
call. It matches the Mission 1.15.6.1 precedent exactly, and the one-off act is
genuinely how the first row was written. It fails on the practical point: the
repository is the only thing that travels between the operator's two machines,
so a script kept outside it is a script that is not there when needed. A rule
that is correct and unavailable produces the hand-retyping it was meant to
prevent.

**Store the acknowledgement in the catalog so `sros-source load` writes it.**
Rejected, and firmly. It would make a human acceptance a property of a file in
git, so pulling a branch would grant a permission. That is the silent migration
the source-governance rules exist to prevent, and it is a worse outcome than
either of the above.

**Export and import the row between databases.** Rejected. A general
governance-row import is a broader capability than a single replay, with no
subject-specific refusals available to it, and it would carry the first
machine's `verified_at` onto a machine where nobody confirmed anything.
