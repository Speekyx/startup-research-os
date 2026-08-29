# ADR-014 — Evidence aggregation as a reference package, gated on calibration

- **Status:** Accepted
- **Date:** 2026-08-29
- **Deciders:** Implemented in Mission 1.1 under brief §35, §36, §39, §41
- **Supersedes:** none. Resolves **D-03 at the framework level**
- **Related:** ADR-009 (contract-first generation), ADR-013;
  `docs/domain/evidence-aggregation-framework-v1.md`,
  `docs/domain/scoring-framework-v1.1.md` §13

---

## Context

`scoring-framework-v1.1.md` §13 blocks `services/scoring` until an evidence
aggregation framework exists. Mission 1.1 writes that framework. The question
this ADR settles is what to *build* alongside it, and — more importantly — what
building it must not silently unlock.

Three forces pull in different directions.

**A specification nobody can execute drifts.** Prose equations acquire
plausible-looking implementations that do not match them, and the mismatch is
found late, in a score somebody already trusted. The mathematics needs to be
runnable.

**A runnable implementation looks like permission to use it.** The moment
aggregation code exists in the repository, the distance between "we have the
equations" and "let us score something" is one import. That distance is the only
thing standing between the project and scores produced by parameters nobody
fitted.

**The old guard becomes wrong the moment D-03 resolves.** A blanket ban on
aggregation vocabulary was correct while nothing was defined. Once V1 is
authorised the ban blocks the authorised work — and the tempting correction,
deleting it, gives back everything it was protecting.

There is also a subtler risk specific to this mission. D-03 exists because
inventing constants is dangerous. Resolving D-03 involves writing equations, and
the failure mode is committing the original sin while curing it: shipping a
half-life, a damping factor or a source weight because the code needs *something*
to run.

## Decision

**Evidence aggregation V1 is implemented as a reference package with two
independent gates between it and production scoring.**

### 1. `packages/evidence-aggregation/`, not `services/scoring/`

A package, deliberately, and under `packages/` rather than `services/`. It
computes; it does not serve. It reads no database, opens no network connection,
imports no provider SDK, and appears in no request path. `services/scoring`
remains a boundary README with no implementation, and a guard asserts it.

The package depends only on the standard library and `sros_contracts`, so it
runs in the zero-dependency CI job — ADR-009's argument applied to the
mathematics: a broken dependency environment must not be able to reduce these
checks to nothing.

### 2. Two gates, not one

```text
Framework Defined     <- Mission 1.1 does this
Profile Calibrated    <- requires labelled data. NOT DONE
```

Mechanically enforced: `aggregate()` refuses an `UNCALIBRATED` profile unless the
caller passes `allow_uncalibrated=True`, every result from one carries a warning,
and a `CALIBRATED` profile without a `calibration_dataset_ref` cannot be
constructed. The shipped `REFERENCE_PROFILE_V1` is `UNCALIBRATED` with an **empty
half-life table**, and a guard asserts both.

The empty table is load-bearing. It means every temporally sensitive claim
reports `MISSING_TEMPORAL_PARAMETER` and produces no score — which is visible,
whereas a placeholder would have worked.

### 3. The guard is rewritten, not removed

Two tiers replace the blanket ban:

| Tier | Rule |
|------|------|
| **Rejected designs** — `contradiction_penalty`, `decay_weight`, `aggregated_evidence_score`, `independence_threshold_result`, `evidence_aggregate` | Forbidden **everywhere, permanently**. Each names a design V1 considered and rejected with a stated reason |
| **Authorised V1 vocabulary** — `support_strength`, the four masses, `independence_group_id`, … | Allowed in the reference package and the canonical contracts. Forbidden in migrations and in `services/` |
| **Universal half-life constants** | Forbidden everywhere. A half-life lives in a versioned profile, never at module scope |
| **Registered source ids** | Forbidden in the aggregation package, so a per-platform coefficient cannot be written |

The rejected names stay forbidden *because the framework decided against them*,
not because D-03 is open. That is a stronger guarantee than before: previously
they were blocked pending a decision, now they are blocked by one.

### 4. Contracts get the enums; the result type does not cross the boundary yet

Six closed enums are declared once in `domain.v1.json` and generated to
TypeScript and Python per ADR-009. `EvidenceAggregationResult` is **not** added
to the canonical contracts: nothing crosses the language boundary until an API
exposes a result, and no such API exists in this mission. Declaring the type now
would be speculative, and the frontend has nothing to render.

## Consequences

### What this buys

The specification is executable, so its claims are tested rather than asserted.
The invariants — duplicates cannot inflate, unknown provenance cannot stack,
missing inputs are never defaulted — are unit tests, not paragraphs.

Production scoring cannot start by accident. Two gates, both mechanical, and
neither satisfiable by editing a document.

The sensitivity analysis is generated from the implementation and checked in CI,
so it cannot describe behaviour the code does not have.

### What it costs

**A package with no production consumer.** It will sit unused until a Claim
entity exists (A-13) and a profile is calibrated. That is the intended state, and
it will look like dead code to anyone who has not read this ADR — which is part
of why the ADR exists.

**A guard that needs judgement to extend.** The old rule was a single list. The
new one requires deciding, per name, whether it is a rejected design or
authorised vocabulary. The `cases.json` entry records the reason for every
rejected name so that judgement is not re-derived from scratch.

**The framework is uncalibrated and stays that way.** D-03 moves from *undefined*
to *defined but unfitted*. That is progress, not completion, and the sensitivity
report names two limitations that only data can resolve.

### Rejected alternatives

**Implement `services/scoring` directly.** Rejected: it would have needed
parameters, and the parameters are the thing D-03 protects. The service would
have shipped with fitted-looking constants nobody fitted.

**Ship a default half-life so the engine runs end to end.** Rejected, and this
was the most tempting option, because the current state produces no score for
temporally sensitive claims. A default would work, would be recorded nowhere as
a guess, and would propagate into every downstream number — the exact failure
D-03 was raised to prevent, committed while resolving it. Failing closed is
visible; a plausible default is not.

**Add a damping constant to fix the score saturating towards 100**
(sensitivity Finding S-1). Rejected for the same reason: choosing its value in a
synthetic harness with no data is the same act, differently dressed. Recorded as
the first-priority calibration target instead.

**Delete the D-03 leakage guard now that D-03 is resolved.** Rejected. Resolving
D-03 authorised one specific design; it did not authorise every alternative
design somebody might write next week.

**Put the reference implementation in `services/scoring/` and mark it
experimental.** Rejected: a marker in a docstring is not a gate, and the
directory name would eventually be read as permission by someone who never saw
the marker.
