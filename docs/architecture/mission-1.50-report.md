# Mission 1.50 — Deterministic Inferred Claim Contract V1

**Primary outcome: `DETERMINISTIC_INFERRED_CLAIM_CONTRACT_READY`. Decision
recorded as ADR-037. Schema necessity: `BOTH_REQUIRED`. No migration created.**

The short version: **the Claim and the Evidence need nothing new, and the
reasoning has nowhere durable to live.**

---

## Setup

**1. Was Mission 1.49 merged?** Yes — PR #92, 12/12 SUCCESS, verified against Git.
**2. Exact main commit?** `c49abdb`, matching the brief. Tree clean, ADR-036
Accepted, `docs/CLAUDE.md` 1.83, `PROJECT_MANIFEST.md` 1.82.
**3. Dedicated branch?** `sprint-1/mission-1.50`.
**4. Exact baseline counters?** Verified by re-running Mission 1.48's generated
baseline against the live deployment — still matches, so drift is zero:
325 / 325 / 33 / 43 / 44 / 57, assessments 4, basis 12, groups 0, Opportunity
1 / 1 / 7, embeddings 0, sources 29, stored reliability 0, `scoring.scores`
ABSENT, profile UNCALIBRATED, Problem-Family PARKED. Aggregation shape unchanged.
**5. Existing INFERRED canonical rows?** **0.** All 43 Claims are OBSERVED.

---

## §0 / §1 — The existing path and the `origin_detail` collision

**6. Exact current `ClaimDraft.rationale` semantics?** A nullable field on the
draft, passed through `build_claim` and written by `_persist_one`.

**7. Exact current `origin_detail` semantics?** It is where `rationale` lands. All
43 Claims populate it, with **provenance** sentences: *"Restated from signal
`<id>` (content-request-change@1.0.0)."* and *"Witnessed by observation `<hash>`
under contract source-published-value-contrast-witnessed@1.0…"*.

**8. Current producers?** `_persist_one` in `claim_repositories.py`, fed by the
two interpreters. **9. Current consumers?** No production reader — it is a
narrative provenance field.

**10. Is `origin_detail` suitable for reasoning?** **No.** It already answers
*where did this Claim come from*. A derivation reasoning step answers *why does
this measurement satisfy this proposition*. Putting both there is the Mission
1.15.4 shape — one free-text field, two independent questions — and no reader or
query could tell which one a given sentence answers.

---

## Q1 — Derivation provenance

**11. Models considered?** All four. **12. Selected?** **Model B** — keep
`origin_detail` as origin, add explicit derivation provenance. **13. Why?**

- **A (reuse `origin_detail`)** — rejected as the dual-authority failure above.
- **C (an existing structure)** — rejected **on a measured fact**.
  `research.claim_interpretation_inputs` is the closest thing: one row per (run,
  signal) with `role`, `claim_id`, `reason_code` and `detail`, 64 rows live. But
  **all 12 rows of its parent `claim_interpretation_runs` carry a populated
  `expires_at`** roughly ninety days out, and the inputs foreign key is **`ON
  DELETE CASCADE`**. When a run expires, every input row goes with it — so **a
  Claim would outlive the record of how it was derived.** A retention-bounded
  execution log is the right shape for *what did this run consider and refuse*
  (GAP-5, ADR-025) and the wrong shape for *why is this Claim true*.
  `proposition_facts` was also rejected: it is the preimage of the KEY, so
  derivation facts placed there would become identity.
- **D (no persistent reasoning)** — rejected: ADR-036 invariant I13 requires
  derivation provenance, and a deterministic derivation that cannot be replayed
  is not deterministic in any useful sense.

**14. Exact structured derivation fields?** Fourteen, each answering a **named
audit question** — rule id and version, evaluator version, `claim_revision_id`,
input signal id, optional input OBSERVED claim id, measurement value, threshold
registration id, evaluation result, semantic-equivalence basis id,
interpretation kind, model version, rationale, created_at. A validator refuses a
field with a blank audit question.

**15. Human-readable rationale role?** An explanation generated deterministically
from the structured facts by the evaluator's own template. **16. Canonical
authority per fact?** The structured field, always. The rationale may restate a
structured fact; it may never carry one that appears nowhere else, and nothing
reads it back as data.

---

## Q4 — Threshold provenance

**17. Vocabulary?** `PREREGISTERED`, `SOURCE_NATIVE`, `EXTERNAL_NORM`,
`POST_HOC`, `UNKNOWN`.

**18–22. Semantics.** PREREGISTERED: frozen and recorded by this system before
the measurements became available to it. SOURCE_NATIVE: supplied by the source as
part of its own measurement contract, so not chosen by this project at all.
EXTERNAL_NORM: from a separately authoritative external rule, identified by
issuer, document, version, section, scope and retrieval provenance. POST_HOC:
selected after candidate measurements were available. UNKNOWN: timing or origin
not establishable.

**23. Which are calibration-eligible?** The first three. **POST_HOC and UNKNOWN
are not**, and UNKNOWN is ineligible rather than assumed — uncertainty is never
permission.

**24. Does threshold provenance alter Claim identity?** **No.** `M >= 100` with a
preregistered bound and `M >= 100` with a post-hoc bound are **one proposition**
with one falsifier. What differs is calibration eligibility, a fact about how the
bound was chosen rather than about what is claimed. Making provenance identity
would fork one proposition into several.

**§5 preserved:** a post-hoc bound with a measurement of 110 **genuinely
supports** the Claim. Hindsight costs eligibility, never entailment.

**50. Preregistration temporal rule?** `threshold_registration.recorded_at <
observation.retrieved_at`.

**51. Exact timestamp semantics?** **Retrieval, not publication.** The bias
preregistration guards against is the analyst's, and an analyst can only be
influenced by data that reached them; a figure public for years before this
system retrieved it was not known to whoever froze the bound, and using
`published_at` would mark such a bound POST_HOC for a hindsight that did not
occur. Not repository commit time either — a commit records when a file changed,
not when a measurement became available.

**And the limit is stated rather than hidden.** The relation is necessary and
machine-checkable; it is **not sufficient** to exclude human foreknowledge, since
a person could have read a public figure outside this system. `PREREGISTERED`
means *this system did not hold the measurement when the bound was frozen*, not
*nobody knew*. A measurement already held is POST_HOC by construction.

**52. External norm requirements?** Issuer, document or rule id, version or date,
section, operator and value as stated there, applicability scope, retrieval
provenance.

---

## Q2 — Evidence attachment

**25. Options considered?** All four. **26. Selected?** **Option A** — direct
Signal → INFERRED Claim Evidence, with derivation provenance recorded separately.

**27. Why?** Existing architectural intent already says so:
`claim-epistemic-semantics-v1.md` §4 states an INFERRED claim carries *"the
Signals it reasoned from, as Evidence"*. Exact and unambiguous, so treated as
intent rather than reopened. It also reuses the Evidence contract unchanged,
preserves the chain to RawRecord, and feeds the aggregator that already consumes
Evidence.

**28. Are Signals directly attached as Evidence?** Yes. **29. Is a ClaimRelation
required?** **No** — the aggregator consumes Evidence and not relations, so a
relation would need proxy Evidence anyway: more machinery, and a second place the
epistemic chain lives.

**30. Is separate derivation provenance required?** **Yes.** Evidence says WHICH
observation bears on this Claim and in which direction; the derivation record
says HOW that direction was determined. Collapsing them would either put an audit
trail into the aggregator's input or leave it unrecorded.

**31. Multiple derivations per Claim?** One rule, **many evaluation records**.
**32. Evaluation granularity?** One per (revision, signal, rule version), bound to
the **ClaimRevision**. A single Claim-level rationale is insufficient the moment
two sources take different directions — one sentence cannot explain both why A
supports and why C contradicts. Binding to the Claim rather than the revision
would let a later derivation silently rewrite the reasoning behind an earlier one.

---

## Q3 — Evaluator boundary

**33. Options?** All six. **34. Selected?** **A — a new package**,
`packages/inferred-claim-evaluator`, **specified and not created**.

**35. Allowed dependencies?** `sros-contracts`, `sros-claim-model`,
`sros-signal-model` — all already in the bare-python runner, so the package would
join it without a workspace-wide install. Forbidden: `sros_acquisition` (a
component able to read the source registry could decide its own authorization),
the Gateway (a package that cannot import a provider cannot call one by
accident), `sros_evidence_aggregation` (it emits Evidence; it must not also
aggregate it) and `sros_opportunity`.

**36. Does `validate_claims.py` remain untouched?** **Yes.** It fails the build on
any non-OBSERVED `ClaimType` access in the interpretation package. Hosting the
evaluator there would require weakening it, and **a guard removed to let new work
through is a guard that never was**. A test asserts the guard still restricts the
interpreter, and another asserts the proposed package does not exist.

---

## §12 / §13 — Results and equivalence

**37. Vocabulary?** `SUPPORTS`, `CONTRADICTS`, `NOT_APPLICABLE`, `UNKNOWN`.
**38. SUPPORT mapping?** `EvidenceDirection.SUPPORTS`. **39. CONTRADICT?**
`EvidenceDirection.CONTRADICTS`.

**40. NOT_APPLICABLE behaviour?** A derivation record and **no Evidence row** —
the measurement bears on a different proposition. **41. UNKNOWN?** The same, and
**never a NEUTRAL row**: NEUTRAL asserts an observation bears without bearing
either way, which is a positive finding, while UNKNOWN says we could not
establish that it bears at all. Both refusals are recorded so they are auditable,
the shape ADR-021 and ADR-025 already use.

**42. Measurement-equivalence gate?** Required over canonical subject, metric
definition, time bound, population, geography, unit, adjustment and methodology
semantics, established **BOTH** ways: a reviewed basis registered once per
(metric definition, source-native measurement) pair, because judging that two
publishers measure the same quantity is a documentary judgement; plus a
deterministic per-measurement check that this record matches it. **Never inferred
from matching strings** — Mission 1.46 found a shared year label covering two
different reference dates.

**43. Independence remains separate?** Yes, an Evidence provenance property.

---

## §14–§17 — Reliability and derivation

**44. Reliability scope unchanged?** Yes — the same five fields.
**45. Derivation validity separate from reliability?** Yes, and **never
multiplied**. Whether the source's 110 is dependable is a human judgement;
whether 110 satisfies `>= 100` is exact.

**46. `interpretation_confidence` semantics?** Documented as *"Confidence that
THIS WORDING faithfully states what the cited Signals showed. Never a market
confidence and never an EvidenceScore."* It is **mandatory for automated claims**
— `build_claim` refuses one without it, citing
`INTERPRETER_PROVENANCE_INCOMPLETE`.

The answer is **C, not the obvious A**. For an OBSERVED restatement, reading the
facts correctly is the whole job, which is why the interpreters set `1.0`
(*"a template applied to structured facts is certain it read them correctly"*).
A deterministic INFERRED threshold Claim has **one step the OBSERVED case does
not have**: asserting that the source-native measurement is a measurement of the
Claim's quantity under its definition and unit. That is exactly what the field's
documented meaning covers, and it is a real judgement rather than an exact one.
**Setting `1.0` automatically would assert certainty about the equivalence
mapping**, which the arithmetic being exact does not establish.

**47. Any semantic gap there?** **No.**
`INTERPRETATION_CONFIDENCE_SEMANTIC_GAP` is deliberately not reported: the field
accommodates deterministic INFERRED without strain, and it lands on the one
genuinely uncertain step. No change to the field or its constraint is proposed.

**There is no `derivation_confidence` field and there must not be one.**
`110 >= 100` is exact; a confidence on it would be a number nobody fitted,
invented because a numeric column exists elsewhere.

---

## §19 / §22 — Versioning and idempotency

**48. Revision binding?** The **ClaimRevision**, so a later derivation cannot
rewrite the reasoning behind an earlier revision.

**49. Idempotency contract?**

| entity | key | basis |
|---|---|---|
| derived Claim | `workspace + proposition_key` | the existing convention — `_persist_one` looks a draft up by key |
| Evidence | `workspace + claim_id + signal_id` | Mission 1.41's repair: `extraction_method` was **removed** so a version bump cannot INSERT a duplicate |
| derivation record | `workspace + claim_revision_id + input_signal_id + derivation_rule_version` | **deliberately different** — Evidence must not duplicate on a rule bump, and a derivation record **must**, because replaying a different rule is different reasoning about the same relation |

---

## §28 — Schema

**53. Current schema sufficient?** **Partly.** Claim storage and Evidence storage
need **no change**. Derivation provenance and threshold provenance each need an
additive table: **`BOTH_REQUIRED`**.

**54. Exact required extension?** Two records, fully specified in the contract —
a derivation provenance record (14 fields, each with its audit question) and a
threshold registration record (10 fields plus the five statuses).

**55. Any migration created?** **No.** §29 forbids it, and a validator enforces
`migration_created: false`.

---

## §26 — Fixtures

**56–59. Independent support.** Two witnesses, 110 and 105, same proposition key,
both SUPPORTS, `KNOWN_INDEPENDENT` → **2 support groups, strength 0.8** against a
strongest member of 0.6.

**60–62. Contradiction.** 110 SUPPORTS and 90 CONTRADICTS on **one Claim
identity** → contradiction strength 0.5, masses **0.3 / 0.2 / 0.3 / 0.2** summing
to **1.0**, through the real aggregator.

**63. Semantic mismatch.** `NOT_APPLICABLE`, 0 Evidence rows, derivation record
kept.
**64. UNKNOWN equivalence.** `UNKNOWN`, 0 Evidence rows, derivation record kept.
**65. Dependent republication.** One support group at 0.6; a companion test shows
the same two rows under established independence **do** exceed, so the contrast is
demonstrated rather than asserted.
**66. Post-hoc threshold.** `SUPPORTS`, logically valid **true**, calibration
eligible **false**.

---

## What did not happen

**67. Research data requests?** **0.** **68. Documentation requests?** **0** of
both kinds.
**69. Canonical mutations?** **None** — all 17 counters identical, and the pytest
leak check reports the database unchanged across 26 tenant tables.
**70. Reliability changes?** None. **71. Calibration changes?** None.
**72. Model calls?** **0**, 0.00 USD. **73. Embeddings?** **0.**
**74. Opportunity changes?** None — 1 / 1 / 7. **75. Problem-Family?** **PARKED.**
**76. Workspace isolation?** 2 seeded workspaces, **0 orchestration probes**,
clean run, both leak checks green.
**77. Bare-python tests?** **1244 across 8 packages**, run with the exact CI
runner **before commit** (§38).
**78. Pytest?** **245 across 9 packages.**
**79. Exact counters after?** Identical to question 4, plus INFERRED Claims **0**.
**80. ADR number?** **ADR-037**, Accepted.
**81. Primary outcome?** **`DETERMINISTIC_INFERRED_CLAIM_CONTRACT_READY`.**

---

## §44 — Next

**82. Recommended next mission?** **Mission 1.51 — Deterministic Derivation
Provenance Schema V1**, which is §44's branch for a ready contract requiring a
schema extension.

It implements **only** the frozen schema: the two additive tables, their
constraints and their idempotency keys. Not the evaluator — it would have nowhere
to write. Not a source, not an acquisition, not an INFERRED Claim.

**Mission 1.51 was not started.**

---

## Artifacts and gates

| file | what it is |
|---|---|
| `ADR-037-deterministic-inferred-claim-contract.md` | the decision, alternatives and open questions |
| `deterministic-inferred-claim-contract-v1.json` / `.md` | the contract and its rendering |
| `render_deterministic_inferred_contract.py` | renders and **validates**; wired into CI |
| `test_threshold_state_identity.py` (claim-model) | §41.1–8 against the real `proposition_key` |
| `test_deterministic_inferred_contract.py` (evidence-aggregation) | §41.9–29; fixtures A/B/E through the real aggregator |

**The validator was probed rather than trusted: 24 deliberate violations, 24
caught** — two models selected for one question, none selected, a semantic
mismatch marked CONTRADICTS or producing an Evidence row, UNKNOWN promoted to
SUPPORTS or mapped to an EvidenceDirection, POST_HOC made calibration-eligible,
POST_HOC denied logical validity, UNKNOWN made eligible, a republication marked
independent, threshold provenance made Claim identity, `derivation_confidence`
added, a field with no audit question, preregistration compared against
`published_at`, the foreknowledge limit hidden, the Gateway allowed as a
dependency, a migration created, OBSERVED identity changed, a counter moved, a
source selected, model calls, Problem-Family unparked, a confidence gap not made
the outcome, and an outcome outside §42.

Gates: `ruff check` and `ruff format --check` clean over 681 files; all eleven
generated-document `--check` steps in sync including the new one; the four
validators passing.

Governance: `docs/CLAUDE.md` 1.83 → 1.84, `PROJECT_MANIFEST.md` 1.82 → 1.83.
