# Mission 1.39 — Proposition Convergence Contract V1

**Outcome: `PROPOSITION_CONVERGENCE_CONTRACT_READY`** (§39 A).

Two genuinely distinct observations can now support one Claim. **`max(members)`
receives more than one member for the first time**, proved through the real
repository and the real aggregator against synthetic fixtures in a disposable
workspace.

Every live canonical counter is unchanged, and the calibration feasibility audit
is byte-identical. The architecture is capable; the corpus has not used it.

---

## §40 — The forty-seven questions

**1. Why can current persistence support multiple Evidence but current
interpretation cannot produce them?**
`_persist_one` looks a draft up by `proposition_key` and, when a Claim exists,
calls `_persist_evidence` against that Claim id — so the database, the repository
and the aggregation framework are all written for N. The interpreter could never
produce two drafts with one key, because all seven templates carry `source_id`
**plus the measurement's own identity** plus the period labels. Two Signals
converged only by being the same measurement.

**2. Which current fields are proposition identity?**
For the new contract: `proposition`, `source_id`, `resource_id`, `notice_class`,
`amount_type`, `amount_scope`, `currency`, `classification_scheme`,
`classification_division`, `relation`.

**3. Which are witness identity?** `notice_ids`, `classification_codes`.

**4. Was a formal distinction introduced?**
Yes — `PropositionConvergenceContract` in `sros_claim_model.convergence`, with
`identity_fields` and `witness_fields` required, disjoint, and covering every
declared fact. A fact classified as neither is **refused**, because the key is
built from whatever is in the mapping and a fact nobody placed is a fact that
decides.

**5. Exact convergence contract id/version?**
`source-published-value-contrast-witnessed@1.0.0`.

**6. Is convergence generic or TED-hard-coded?**
**Generic machinery, one narrow proposition to prove it** (§15). The contract
type, the qualification predicate, the identity/witness split, the witness key
and the overlap function are source-agnostic; the registry holds one entry.

**7. Can OBSERVED Claims converge?** **Yes**, narrowly.

**8. Exact semantic justification?**
`claim-epistemic-semantics-v1.md` §2 asks *does a source report this, such that a
person could go and read it there?* — yes, a reader opens the notices and sees
the differing totals. §3 asks whether the truth condition is about the
publication — it is, and the claim stays true if TED's figures were wrong,
because it asserts what TED **stated**. The broader proposition is **entailed by**
the detailed one and asserts less. No sample is generalised, no prevalence
estimated, no latent phenomenon inferred.

**9. What would require INFERRED instead?**
Any of §5's list: generalising from samples, estimating prevalence, asserting the
class usually behaves this way, combining source meanings, inferring a latent
phenomenon. **The constructor refuses a non-`OBSERVED` contract**, so that layer
cannot be built here by accident.

**10. Does `source_id` remain part of OBSERVED identity?**
**Yes, and the constructor enforces it** rather than leaving it to each author.

**11. Can two sources converge under this V1 contract?**
**No.** `SourceBoundary` has one member, `SAME_SOURCE_AND_RESOURCE`, and a
cross-source member is absent rather than present-and-unused — a member nobody
may pass is an invitation.

**12–13. What must match, what may differ?** See questions 2 and 3.

**14. How is temporality handled?**
Declared on the contract, never inferred. This one is `EVERGREEN` because
**H-37 is open**: a TED notice publishes an offset without a time, so the source
establishes no instant the claim could be bounded by. An existential over a
publication needs none.

**15. How is scope handled?**
Unchanged. A convergent proposition carries its own `ObservationScope`, derived
at packet-build time exactly as Mission 1.34 specified. Different scopes do not
converge because a statement template matches.

**16. How is population overlap represented?**
`ObservationOverlap`: `DISJOINT` · `OVERLAPPING` · `UNESTABLISHED`, computed from
declared cohort membership. Unstated membership is `UNESTABLISHED`, never
`DISJOINT` — a cohort that did not say which records it read has not established
that it read different ones.

**17. Does disjoint population mean independent Evidence?**
**No, and the two vocabularies deliberately share no member name.** `DISJOINT`
says two witnesses read different records; they can still share the publisher,
the collection mechanism, the methodology and the population. The first draft used
`UNKNOWN` for both and **the test asserting the vocabularies are disjoint caught
the collision** — the overlap member is now `UNESTABLISHED`.

**18. How is duplicate-witness detection implemented?**
`witness_key` — `proposition_key` over the witness facts, namespaced by
proposition kind — and `distinct_witnesses`. Not uuids: a guard comparing
generated ids would agree that the same cohort inserted twice is two witnesses.

**19. Can replaying one Signal create another Evidence?**
**No**, asserted against the real repository: persist, count, persist again,
count — 1 and 1.

**20–23. Did existing proposition keys, Claim ids, revisions or Evidence
change?** **None of them.** `proposition_key` was not touched; convergence
computes the same hash over a smaller mapping, which is what a different fact set
has always produced. No historical template changed and **no historical
proposition kind gained a contract** — convergence is opt-in per kind.

**24. Did Docker/Podman/Kubernetes remain distinct?**
**Yes**, and it is a named regression test: three distinct keys, and their
proposition kind has no contract at all.

**25–26. Was a convergence-enabled TED proposition defined? Exact kind?**
Yes: `source_published_classification_value_contrast_witnessed`.

**27. What does it establish?**
That the named source published, in the named resource, **at least one bounded
set** of notices of the named class under the named classification division whose
stated amounts of the named type, scope and currency stand in the named relation.

**28. What does it explicitly NOT establish?**
How many such sets exist · what proportion of the division they are · that the
relation is typical or representative · any trend or growth · demand, market
size, buyer preference or willingness to pay · that the amounts are prices or
that anybody paid them · **that the witnesses are independent**. The contract
refuses to be constructed with an empty `does_not_establish`, and the statement's
own wording carries *"at least one bounded set"* so a summariser cannot drop the
bound.

**29–32. Same proposition key? Same Claim id? How many Evidence rows? Distinct
witnesses?**
Yes · yes, **one Claim** · **two** · yes, different witness keys and different
Signals. Claim revisions: **1** — a revision is a changed assertion, not
additional support (§22).

**33. Did the real aggregator receive >1 Evidence?**
**Yes:** `raw_evidence_count == 2`, `scorable_evidence_count == 2`.

**34. Which aggregation mechanism actually processed >1 input?**
**`max(members)`, within one independence group.** Independence is `UNKNOWN` on
both rows, so the conservative rule collapses them into one group — and that
group has **two members** with `collapsed_member_count == 1`, and its strength is
the maximum of the two. Mission 1.37 measured that this had never happened.

**35. Was independence manufactured?**
**No.** Both rows are `UNKNOWN` with a null group id, and
`scoring.evidence_independence_groups` holds zero rows for the Claim.

**36. Did support saturation receive >1 group?**
**No — one group, correctly.** Two witnesses of unestablished provenance raise
observed volume, not evidence strength. **This is not independent corroboration
and must not be reported as such.**

**37. Were fixture reliability values production assessments?**
**No.** `0.4` and `0.7`, chosen different so the within-group maximum has
something to choose between, and deliberately not `0.5` or `0.65` so nobody can
mistake them for the two reviewed assessments.

**38. Did the real deployment gain multi-record Claims?**
**No, and that is correct.** Every fixture went into a disposable workspace.

**39. Did calibration feasibility counts change?**
**No.** `calibration-feasibility-audit-v1.json` is byte-identical (`--check`
passes): still 28 Claims, 28 Evidence, zero with more than one row. Synthetic data
tests architecture; only real research rows can change calibration feasibility
(§26).

**40. Were research records acquired?** None. §27: zero acquisitions.

**41. Were ReliabilityAssessments changed?** No. Two, six basis rows, unchanged.

**42. Model calls?** **0.** **43. Embeddings?** **0**, and forbidden by the
qualification predicate's own contract.

**44. Scoring or ranking?** None. `scoring.scores` does not exist.

**45. Problem-Family still PARKED?** Yes, and §14 refuses it by name as a
convergence mechanism: it asks whether two observations concern the same user
problem, which is a different question from whether they witness the same bounded
proposition.

**46. Canonical counters before/after?** Read from the live deployment.

| counter | before | after |
|---|---:|---:|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / ClaimRevisions / Evidence | 28 / 28 / 29 / 28 | **28 / 28 / 29 / 28** |
| EvidenceIndependenceGroups | 0 | **0** |
| ReliabilityAssessments / basis rows | 2 / 6 | **2 / 6** |
| Opportunities / revisions / links | 1 / 1 / 7 | **1 / 1 / 7** |
| Embeddings / Scores | 0 / 0 | **0 / 0** |
| Registered sources / Scope relations | 29 / 0 | **29 / 0** |

**47. Recommended next mission?** See §41 below.

---

## The objection the design had to answer

The existing TED template's own docstring says:

> a proposition that cannot say WHICH notices is not checkable, and one that
> omits its bound reads as a fact about a market

It is right on both counts, and the answers are different.

**Checkability moves rather than disappearing.** The notice ids are witness
facts, carried on the Signal and reachable through Evidence → Signal →
`signal_inputs` → `normalized_records`. A reader can still recover exactly which
notices. What they cannot do is read the cohort off the Claim's identity — which
is the point, because a second cohort must be able to witness the same assertion.
A test recovers both cohorts from the persisted signal scopes.

**The bound stays in the wording.** *"at least one bounded set"* is in the
statement itself, and the contract's `does_not_establish` names prevalence,
typicality, trend and every commercial reading explicitly.

---

## What the tests caught

**A vocabulary collision.** `ObservationOverlap` was drafted with `UNKNOWN`,
which `EvidenceIndependenceState` already has. The test asserting the two share no
member failed, and the member was renamed `UNESTABLISHED`. Two vocabularies
sharing a member name is precisely how a mapping between them gets written by
accident — which is the one thing §11 forbids.

---

## §41 — Recommended next mission

**Mission 1.40 — Second Pilot TED Category Multi-Evidence Acquisition V1.**
The convergence contract is settled, so the second-pilot path reopens **without
returning to Docker**. That mission should retrieve the authoritative official CPV
taxonomy, select a non-developer category under a preregistered rule, freeze the
category and bounded period before acquisition, collect the minimum real
observations, construct two genuinely distinct witness cohorts, use this
contract, create the **first real** Claim with two or more Evidence rows, run the
uncalibrated diagnostic aggregator, and rerun the feasibility audit.

**Mission 1.39 did not choose the CPV category**, as §16 requires. Mission 1.33
recorded that the collector deliberately expands no CPV code into a label, so the
choice needs the official table retrieved first.

Two decisions that mission inherits rather than re-opens: the convergent
interpreter is **not wired into the production job**, so wiring it is an explicit
act with the double-counting boundary in §19 to satisfy; and one Signal
legitimately witnessing both a detailed and a broader Claim is permitted **across
Claims** and never **within one** — the duplicate-witness guard enforces the
second.

---

## Artifacts

| | |
|---|---|
| [ADR-035](adr/ADR-035-proposition-identity-and-witness-identity.md) | why identity and witness are different kinds of fact |
| [proposition-convergence-contract-v1.md](../data/proposition-convergence-contract-v1.md) | the contract in prose |
| [proposition-convergence-contract-v1.json](../data/proposition-convergence-contract-v1.json) | generated from the registry, `--check` wired into CI |
| `sros_claim_model/convergence.py` | the generic machinery and the one registered contract |
| `sros_nlp/interpreters/convergent_witness.py` | the projection, deliberately not wired into the job |
| [test_proposition_convergence.py](../../packages/claim-model/python/tests/test_proposition_convergence.py) | 35 tests: contract, near misses, byte-stability |
| [test_proposition_convergence_persistence.py](../../services/nlp/python/tests/test_proposition_convergence_persistence.py) | 7 tests: real repository, real aggregator, synthetic fixtures |

**Verification:** `generate.py --check`, `run_python_tests.py` (**687 tests**, up
from 652), the 7 structural validators, ruff, mypy (192 files), the 4 existing
generated-document checks **plus the new convergence render check**, TypeScript,
and `run_pytest_suites.py`.
