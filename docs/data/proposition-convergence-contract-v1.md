# Proposition Convergence Contract V1

**Status:** Implemented. **Outcome:** `PROPOSITION_CONVERGENCE_CONTRACT_READY`
**Date:** 2026-09-03 (Mission 1.39) · **ADR:** [ADR-035](../architecture/adr/ADR-035-proposition-identity-and-witness-identity.md)
**Machine-readable:** [proposition-convergence-contract-v1.json](proposition-convergence-contract-v1.json),
generated from the registry and checked in CI.

Two genuinely distinct observations can now support one Claim. **No live research
row changed**, and the live corpus still has zero multi-Evidence Claims: the
architecture is capable and the corpus has not used it.

---

## 1. The distinction

```text
PROPOSITION IDENTITY FACTS   what exact assertion is this Claim?
WITNESS OBSERVATION FACTS    which observation demonstrates that assertion?
```

> **The test.** If changing field F changes **what** the Claim asserts, F is
> proposition identity. If changing F only changes **which** observation
> witnesses the same assertion, F may be witness identity.

`proposition_key` is computed over the identity facts alone. **A witness fact is
not discarded** — it stays on the Signal, on the Evidence and in provenance, and
is hashed into a separate `witness_key` that the duplicate guard uses.

A fact the contract classifies as *neither* is refused. The key is built from
whatever is in the mapping, so a fact nobody placed is a fact that decides.

---

## 2. Why the persistence layer was never the blocker

`_persist_one` looks a draft up by `proposition_key` and, when a Claim exists,
attaches the Evidence to it. The database, the repository and the aggregation
framework are all written for N. Only the interpreter could not produce two
drafts with one key, because every template carried the measurement's own
identity.

---

## 3. `OBSERVED`, and why

`claim-epistemic-semantics-v1.md` §2 asks: *does a source report this, such that
a person could go and read it there?* For the convergent proposition — *the
source published at least one bounded set of notices in division X whose stated
amounts differ* — yes. A reader opens the notices and sees it.

§3 asks whether the truth condition is about the publication. It is: the claim
stays true if TED's figures were wrong, because it asserts what TED **stated**.
No sample is generalised, no prevalence estimated, no latent phenomenon inferred.

**The constructor refuses a non-`OBSERVED` contract**, so the `INFERRED` layer
that `docs/CLAUDE.md` records as deliberately unbuilt cannot be built here by
accident.

### The objection this had to answer

The existing TED template's own docstring says *"a proposition that cannot say
WHICH notices is not checkable"*. It is right, and the answer is that
**checkability moves rather than disappearing**: the notice ids are witness
facts, reachable through Evidence → Signal → `signal_inputs` →
`normalized_records`. What a reader cannot do is read the cohort off the Claim's
identity — which is the point, because a second cohort must be able to witness
the same assertion.

---

## 4. The one registered contract

`source-published-value-contrast-witnessed@1.0.0`, proposition kind
`source_published_classification_value_contrast_witnessed`. Generic machinery,
one narrow proposition to prove it — not a TED branch, and not a universal
ontology of convergence.

| | fields |
|---|---|
| **identity** | `proposition` · `source_id` · `resource_id` · `notice_class` · `amount_type` · `amount_scope` · `currency` · `classification_scheme` · `classification_division` · `relation` |
| **witness** | `notice_ids` · `classification_codes` |

`EVERGREEN`, because **H-37 is open**: a TED notice publishes an offset without a
time, so the source establishes no instant this claim could be bounded by. An
existential over a publication needs none — once witnessed, it stays witnessed.

**It establishes** that the named source published, in the named resource, at
least one bounded set of notices of the named class under the named division
whose stated amounts of the named type, scope and currency stand in the named
relation.

**It does not establish** how many such sets exist · what proportion of the
division they are · that the relation is typical or representative · any trend or
growth · demand, market size, buyer preference or willingness to pay · that the
amounts are prices or that anybody paid them · that the witnesses are independent.

The statement's own wording carries **"at least one bounded set"**, so a
summariser cannot drop the bound.

---

## 5. Source boundary

`SAME_SOURCE_AND_RESOURCE`, the only member of the enum. **`source_id` is always
identity**, enforced in the constructor rather than left to each author.

*"Wikimedia counted X"* and *"TED reported Z"* are different propositions with
different falsifiers, and rendering them into similar English does not make them
one. A cross-source member is absent rather than present-and-unused: a member
nobody may pass is an invitation.

---

## 6. Overlap is not independence

| axis | values |
|---|---|
| `ObservationOverlap` | `DISJOINT` · `OVERLAPPING` · `UNESTABLISHED` |
| `EvidenceIndependenceState` | `KNOWN_INDEPENDENT` · `KNOWN_DEPENDENT` · `UNKNOWN` |

`DISJOINT` says two witnesses read different records. It does **not** say the two
Evidence rows are independent corroboration: they can still share the publisher,
the collection mechanism, the methodology and the population.

**The first draft used `UNKNOWN` for both**, and the test asserting the two
vocabularies share no member caught it. Two vocabularies sharing a member name is
how a mapping between them gets written by accident, so the overlap member is
`UNESTABLISHED`.

`independence_state` stays `UNKNOWN` on convergent Evidence, and no independence
group is created.

---

## 7. Proved through the real path

Synthetic fixtures, disposable workspace, real repository, real aggregator:

| | |
|---|---|
| proposition key | **equal** across two cohorts |
| Claim id | **one** |
| Evidence rows | **two** |
| Signal ids | different |
| witness keys | different |
| Claim revisions | **1** — a revision is a changed assertion, not additional support |
| replay of one Signal | adds nothing |
| detailed Claim | still a separate Claim, unchanged |

### The mechanism that finally saw two inputs

```text
raw_evidence_count        2
scorable_evidence_count   2
support_group_count       1      <- independence UNKNOWN collapses them, correctly
group.member_evidence_ids 2      <- max(members) HAS A CHOICE, for the first time
group.strength            max(fixtures)
```

Mission 1.37 measured that `max(members)` had never had more than one member.
**It does now.**

Saturation still receives **one** group, and that is correct rather than a
shortfall: two witnesses of unestablished provenance raise observed volume, not
evidence strength. **This is not independent corroboration and must never be
reported as such.**

The reliability values in that test are **fixtures** (`0.4`, `0.7`), chosen to be
different so the within-group maximum has something to choose between, and
deliberately not `0.5` or `0.65` so nobody can mistake them for the two reviewed
assessments. **Synthetic data tests architecture. Only real research rows can
change calibration feasibility.**

---

## 8. What did not change

- **No historical proposition kind gained a contract.** Convergence is opt-in per
  kind, and the seven existing kinds are in the same state they were.
- **`proposition_key` was not touched.** Convergence computes the same hash over
  a smaller mapping, which is what a different fact set has always produced.
- **No existing template changed.** `notice_ids` is still identity on
  `source_reported_procurement_value_contrast`, and Docker, Podman and Kubernetes
  still have three distinct keys.
- **Not wired into the production job.** No Signal in this deployment can witness
  two Claims, so the double-counting boundary is enforced by absence rather than
  by a rule. Running it against live records is a later mission's decision.
- **The live corpus is unchanged**, and the calibration feasibility audit is
  byte-identical: still zero multi-Evidence Claims, still `UNCALIBRATED`.
