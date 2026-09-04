# Mission 1.52 — Deterministic Inferred Claim Evaluator Foundation V1

**Primary outcome: `REFUSAL_DERIVATION_BINDING_CONTRACT_GAP`.**
**Secondary outcome: `DETERMINISTIC_EVALUATOR_FOUNDATION_IMPLEMENTED`.**

The evaluator exists, runs, and refuses correctly. What it cannot do is write a
refusal down: `research.claim_derivations.claim_revision_id` is `NOT NULL`, and
the evidence-requirement trigger exempts only `HYPOTHESIS`, `MANUAL` and
`WITHDRAWN` — so persisting a `NOT_APPLICABLE` or `UNKNOWN` evaluation's
provenance would require first fabricating the Claim the evaluation just
declined to establish. **No INFERRED Claim, no Evidence, no derivation row and
no threshold registration was created.**

Two outcomes are reported apart because one verdict would let either hide the
other. Reporting only the gap would suggest nothing was built; reporting only the
foundation would suggest the layer is ready to run.

---

## Setup

**1. Was Mission 1.51 merged?** Yes — PR
[#94](https://github.com/Speekyx/startup-research-os/pull/94), merged into `main`
at `1cde481`. `docs/CLAUDE.md` 1.85, `PROJECT_MANIFEST.md` 1.84, ADR-036 and
ADR-037 both Accepted, migration 0034 applied.

**2. Dedicated branch?** `sprint-1/mission-1.52`, cut from `1cde481` with a clean
tree.

**3. Baseline counters, measured against the live deployment?** RawRecords 325,
NormalizedRecords 325, Signals 33, Claims 43, ClaimRevisions 44, Evidence 57,
ReliabilityAssessments 4, Opportunities 1, independence groups 0,
`claim_derivations` **0**, `threshold_registrations` **0**, INFERRED Claims
**0** — all 43 live Claims are `OBSERVED`.

**4. Were they re-measured at the end?** Yes. Every counter is unchanged, and the
pytest leak check reports the database unchanged across 28 tenant tables and 17
global tables.

---

## The package

**5. Where does the evaluator live?** `packages/inferred-claim-evaluator`,
distribution `sros-inferred-claim-evaluator`. That is the exact path ADR-037 Q3
named, and the validator reads Q3 out of the Mission 1.50 contract and compares
it rather than trusting the record.

**6. Why not in the interpreters?** Because `validate_claims.py` fails the build
on any non-OBSERVED `ClaimType` access there, and hosting the INFERRED evaluator
would require weakening it. **A guard removed to let new work through is a guard
that never was.** The guard is byte-identical, and no interpreter module imports
the evaluator.

**7. Declared dependencies?** `sros-contracts` and `sros-claim-model`.

**8. ADR-037 allowed a third — why was `sros-signal-model` not taken?** Because
the evaluator consumes a `MeasurementWitness` value object rather than a Signal,
so importing the signal model would add a dependency nothing uses. **An allowance
is not an obligation**, and an unused dependency is a future import waiting to
happen.

**9. What can it structurally not do?** Four things, each enforced by an absent
import rather than by a rule somebody must remember: it cannot acquire (no
`sros_acquisition`, so a component able to read the source registry cannot decide
its own authorization); it cannot call a model (no Gateway, so `0 model calls` is
a property of the dependency graph); it cannot aggregate (no
`sros_evidence_aggregation`); and it cannot score reliability or adjudicate
independence — neither is an input and neither is an output.

**10. Does it write to a database?** No. Every result is a frozen value object,
and the package contains no database or network client at all.

---

## The zero-dependency runner

**11. Did the package join the runner?** Yes —
`packages/inferred-claim-evaluator/python` is a suite, and
`packages/claim-model/python` was added to `SHARED_PATHS`.

**12. Was the runner widened to expose the monorepo?** No, and that was the live
temptation. Mission 1.47's CI failure came from a test importing a package the
zero-dependency runner does not expose, masked locally by `uv run`; the repair
then was to move the proof rather than widen the runner. Here the evaluator
genuinely depends on claim-model per ADR-037, so **one named package** joins the
shared paths. Widening it to the monorepo would delete the property the runner
exists to check.

**13. Was the hard gate run before commit?** Yes. **1313 tests across nine
suites under bare `python`, all passing.** It caught two real defects on its
first run, both recorded below.

---

## The four gates

**14. What is the order, and why does it matter?**

1. **Semantic equivalence.** `NOT_EQUIVALENT` → `NOT_APPLICABLE`; `UNKNOWN` →
   `UNKNOWN`. It runs FIRST so the direction the arithmetic *would* have produced
   cannot leak into the refusal — and a test deliberately feeds a mismatch that
   would have SUPPORTED, to prove the gate runs rather than relabels.
2. **Registration and scope match.** The registration must describe this
   proposition, and unit and time bound must match exactly.
3. **Preregistration timing.** A `PREREGISTERED` registration requires
   `recorded_at < witness.retrieved_at`.
4. **The predicate.** Exact `Decimal` comparison against the registered bound.

**15. Does a semantic mismatch ever CONTRADICT?** Never. A measurement of another
quantity is not a disagreement about this one.

**16. Is any unit converted or any time window aligned?** No. A different unit is
`NOT_APPLICABLE`; a different time bound is `NOT_APPLICABLE`. A test asserts the
module exposes no helper whose name contains `convert`.

**17. Can the evaluator choose a threshold?** No. `evaluate` takes exactly one
registration and never searches a collection, so *whichever bound makes the Claim
work* is not expressible.

**18. What happens to a `PREREGISTERED` registration recorded after retrieval?**
`UNKNOWN` with `PREREGISTRATION_TIMING_INCONSISTENT`. It is **not** silently
downgraded to `POST_HOC`, because a downgrade would quietly repair somebody's
claim about when they decided.

**19. Is the comparison exact?** Yes. A float `measurement_value` is refused at
construction, with the reason stated: a binary artifact lands exactly at the
boundary the proposition is about, and migration 0034 stores `NUMERIC` for the
same reason. `0.3 >= 0.3` holds, and `99.999999999999999999 >= 100` does not.

**20. Does provenance change entailment?** No. A `POST_HOC` threshold with a
measurement of 110 still SUPPORTS `M >= 100`; what it loses is calibration
eligibility. `POST_HOC` and `UNKNOWN` are ineligible, and `UNKNOWN` is ineligible
rather than assumed — uncertainty is never permission.

---

## What the evaluator never decides

**21. Independence?** Not an input, not an output, and the string appears nowhere
in an outcome. A dependent republication still SUPPORTS the same proposition; it
simply stays one provenance group downstream, which is the aggregator's business.

**22. Reliability?** Not an input, not an output.

**23. `interpretation_confidence`?** Taken from the reviewed equivalence decision
and never invented. The arithmetic being exact says nothing about whether the
wording faithfully reads the Signal, and setting `1.0` automatically would assert
certainty about a real judgement (ADR-037 §17). An `EQUIVALENT` decision without
one is refused at construction.

**24. Equivalence itself?** Consumed as a reviewed decision, never derived. A
`NOT_EQUIVALENT` verdict is honoured even where every visible field matches,
because the reviewer knows something the fields do not show. `EQUIVALENT`
requires all eight frozen dimensions — establishing equivalence on the easy half
is how two different quantities become one.

---

## Proposition identity

**25. What is excluded?** `source_id`, `measurement_value`, `direction`,
threshold provenance status, and both version fields.

**26. What was proved rather than asserted?** 110 and 105 from different sources
share one proposition key; 110 and 90 — a support and a contradiction — share one
key; a different threshold is a different proposition; provenance status does not
change the key; and `Decimal("100")` and `Decimal("100.0")` are one bound.

**27. Why does that last one matter?** Otherwise the same threshold written two
ways forks the proposition, which is Mission 1.48's measurement-value defect one
field along.

---

## The two contract questions

**28. §20 — where does a refusal's derivation provenance go?** **Nowhere, today.
This is the mission's primary finding, and it was proven rather than reasoned
about.** In a disposable probe workspace created and removed inside one script:

| attempted | result | mechanism |
| --- | --- | --- |
| INFERRED claim with no Evidence | **REFUSED** (23514) | `research.require_evidence_for_generated_claim` |
| derivation with `claim_revision_id` NULL | **REFUSED** | migration 0034's `NOT NULL` |

The trigger's exemptions are `HYPOTHESIS` (claim_type), `MANUAL` (origin) and
`WITHDRAWN` (lifecycle) — read out of the live function definition, not recalled.
Both refusals are correct on their own terms, and jointly they leave a refusal
nowhere to live: a derivation must name a revision, a revision requires a Claim,
a generated INFERRED Claim requires Evidence, and a refusal produces no Evidence
by ADR-037's own rule.

**29. What was deliberately not done about it?** No INFERRED Claim was created to
host a refusal — a Claim asserting a proposition the evaluator declined to
establish is a fabrication with provenance attached. `INFERRED` was not added to
the trigger's exemption list. `claim_revision_id` was not made nullable. No third
table was invented. **Each of those is a schema decision with an ADR behind it,
and none belongs in a mission whose brief forbids a migration.**

**30. §22 — what happens to canonical Evidence when the rule version changes?**
Measured first: `scoring.evidence` has **no** revision, supersession or
`is_current` column. `model_version` and `prompt_version` are provenance of the
extraction procedure, not a revision model. So **policy D**: a rule-version change
produces another derivation record and may never automatically alter canonical
Evidence; a disagreement with the standing row is REPORTED for operator review
and nothing is written.

**31. Why not overwrite, or add a second Evidence row?** An overwrite would
destroy the earlier direction with no trace, and Mission 1.41 established that a
changed assessment is neither unchanged nor a second observation. A second row
would mean re-adding a version to the Evidence idempotency key — which Mission
1.41 **removed** precisely so a version bump could not INSERT a duplicate.

**32. Why is §20 the primary outcome and §22 not?** §22 is resolvable by policy
with no schema change, because `claim_derivations` is already append-only per rule
version. §20 is not resolvable by any policy: it is a mutual constraint between
two schema decisions, each individually right. Everything downstream of
persistence waits on it, so reporting §22 as the headline would misattribute the
blocker to a layer that is not blocking.

---

## Downstream

**33. What must the aggregator change to accept the new layer?** **Nothing**, and
that is proved from the signature rather than asserted: `aggregate()` takes a
claim id, a sequence of items and a profile, and **no claim type at all**.
`EvidenceItem` carries none either — Mission 1.13 dropped `claim_type` from
`scoring.evidence` because two answers to one question eventually disagree. There
is no parameter through which INFERRED Evidence could be treated differently.

**34. A correction this mission made.** The first draft of the downstream test
asserted that `EvidenceDirection` has no `NEUTRAL` member. **It does** — retained
for provenance and coverage, contributing to neither strength. So nothing in the
aggregation layer would refuse a refusal mapped onto NEUTRAL. **The guarantee is
producer-side**: `EvaluationResult` has no NEUTRAL, and a refusal carries no
`EvidenceDecision` at all, so the evaluator has nothing to hand over. Naming
where a guarantee actually lives matters, because a NEUTRAL row would be counted
and weightless — invisible in the numbers and visible in the counts, which is
exactly the shape ADR-037 refuses. The test now asserts the true fact and says
why it is not the protection.

**35. Any evaluator-to-aggregator dependency?** None, in either direction, and it
is structural rather than conventional: the aggregation suite runs with only its
own package plus `SHARED_PATHS`, so an import of the evaluator there would not
merely be against the rules, it would fail to resolve.

---

## Tests

**36. What was tested where?** 55 tests in the evaluator package covering the
predicate, exactness, determinism, all four gates, provenance eligibility,
proposition identity, the outcome shape and the package boundary. 14 in
`evidence-aggregation` covering downstream compatibility. Both suites run under
bare `python`.

**37. Fixtures?** A independent corroboration (110/105), B contradiction (110/90),
C exact boundary (100), D semantic mismatch, E unknown equivalence, F dependent
republication, G `POST_HOC`, H preregistration timing violation. **D, E and H
never reach an aggregator by construction**, so nothing pretends to run them
through one.

**38. A pre-existing test was re-pointed.** Mission 1.50's
`test_the_package_was_not_created` asserted this package does not exist — true of
a contract mission that wrote no code, and false the moment the contract is
implemented. **A test asserting 0 forever is a test asserting the contract is
never implemented**, the repair shape of Missions 1.31.1, 1.40, 1.41 and 1.44.1.
Re-pointed to the property that survives: the evaluator sits at the path Q3
named, and no interpreter imports it. Not deleted.

**39. One of my own tests was wrong and was replaced.**
`test_the_rule_version_and_the_evaluator_version_are_separate_facts` compared
`id()` of two constants that both read `"1.0.0"`, so CPython's interning made it
assert that one string is not itself. Replaced with the property that matters:
`DerivationDraft` declares both fields, because migration 0034's idempotency key
contains `derivation_rule_version` and **not** `evaluator_version` — replaying a
different rule is different reasoning and earns its own row, while rebuilding the
same rule under a new evaluator is not. **It failed on the first bare-`python`
run, which is what that gate is for.**

**40. Was the validator probed?** **55 deliberate violations, 55 caught**, and the
real record still validates. Each is a claim the record could plausibly have made
and must not: a package at a path the repository does not have, `INFERRED` added
to the trigger exemptions, a counter that moved, a source selected, the guard
reported as modified, the next mission reported as started.

**41. Anything the checks caught that was not a test?** Yes, twice. `ruff`
flagged an `open()` that should be `Path.open()`. And `mypy` found a real
narrowing gap: `interpretation_confidence` is `float | None` on the equivalence
decision and `float` on the claim draft. Gate 1 guarantees it is present, but a
type checker cannot see across a constructor invariant — so the narrowing is
explicit and says why it is safe, following the same `# pragma: no cover` shape
already used one function earlier in the file, rather than a silent
`type: ignore`.

---

## Budget and state

**42. Network?** 0 research-data requests, 0 documentation requests, 0 metadata
requests. Nothing was acquired and no source was selected.

**43. Model use?** 0 model calls, 0 embeddings, 0 calibration labels, 0
parameters fitted. `REFERENCE_PROFILE_V1` is still `UNCALIBRATED` and
Problem-Family is still `PARKED`.

**44. Anything written?** No migration, no INFERRED Claim, no Evidence, no
threshold registration, no derivation row, no Score, no Opportunity change.
`SourceBoundary` untouched, `validate_claims.py` untouched, the aggregator
untouched.

**45. Test totals?** 1313 bare-`python` tests and 3186 pytest tests, all passing,
with the leak check reporting the database unchanged.

**46. One environment finding worth recording.** A plain `uv sync` prunes
workspace members the root project does not depend on, which broke four nlp test
collections and seven other tests with `ModuleNotFoundError`. It was an artifact
of adding a workspace member, not a code defect — `uv sync --all-packages`, which
is what CI runs, restored them. Diagnosed rather than re-run blindly.

---

## §45 — Next

**47. Recommended next mission: Refusal Derivation Binding Design V1.** Decide
where a `NOT_APPLICABLE` or `UNKNOWN` evaluation's provenance lives, as a
semantics question with an ADR behind it — never as an edit to a trigger or a
nullability change made in passing.

**48. Options identified and not chosen:**

- A refusal record keyed on the INPUTS rather than on a claim revision, in its
  own table. No Claim needed, and no Claim implied.
- A nullable `claim_revision_id` with a CHECK requiring it exactly when
  `evaluation_result` is directional. Narrow, and it weakens the binding 1.51
  chose deliberately.
- Refusals kept only in the interpretation run log — rejected in advance by
  ADR-037's own measurement: those rows expire, and a refusal that vanishes is a
  refusal nobody can audit.

**49. Preference, on the evidence available:** the first. It needs no exemption in
the evidence-requirement trigger and no change to the derivation binding, so both
of Mission 1.51's guards stay exactly as strong as they are. **The decision is
not this mission's to make.**

**50. Why Mission 1.53 was not started.** The evaluator has nowhere to write a
refusal, so running it over canonical rows would produce directional results and
silently drop every refusal — which is the failure the whole derivation record
exists to prevent.

**51. Still open.** `REFUSAL_DERIVATION_BINDING_CONTRACT_GAP`; policy D decided
and not implemented; no threshold registration exists, so no proposition has a
bound frozen before a measurement was retrieved; the first INFERRED Evidence will
resolve `NO_APPLICABLE_ASSESSMENT` and be `NON_SCORABLE`, which is correct; and
Mission 1.43's finding still governs — with one provenance group the aggregator
is algebraically the pass-through baseline.

---

## Artifacts

- `packages/inferred-claim-evaluator/` — the package and its 55 tests
- `docs/data/deterministic-inferred-evaluator-foundation-v1.json` — the record
- `docs/data/deterministic-inferred-evaluator-foundation-v1.md` — generated
- `infrastructure/scripts/render_deterministic_inferred_evaluator.py` — renderer
  and validator, wired into CI
- `packages/evidence-aggregation/python/tests/test_deterministic_evaluator_downstream.py`
