# Mission 1.84.3 — The schema has no maximum, so no ceiling can be derived from it

**Outcome: `OUTPUT_SCHEMA_HAS_UNBOUNDED_SERIALIZED_SIZE`.**

The question was what output-token ceiling the frozen schema justifies. It justifies **none**.
Eight required paths are unbounded, so there is no maximum valid serialized size to derive one
from, and the 3000 Mission 1.84 froze was not merely too small — **it was underivable, and so is
every other number.**

**No execution packet V2.** No ceiling selected. Nothing changed in the contract.

---

## Report

```
BRANCH                        sprint-1/mission-1.84.3
START_COMMIT                  ecfeff2

SCHEMA                        second-opportunity-synthesis-output@1.0.0
FINITE_BOUND                  false
UNBOUNDED REQUIRED PATHS      8
SCHEMA_MAX_SERIALIZED_SIZE    UNBOUNDED

BOUNDED_SUBSET_FLOOR          27709 characters (a FLOOR, not a maximum)
FLOOR vs FROZEN CAP           27709 against 3000 — the floor alone is ~4x the cap
DOMINANT FIELD                statement_classifications, 16133 of 27709 (58%)

EXACT_MAX_OUTPUT_TOKEN_COUNT  NOT_ESTABLISHED
DERIVED_MIN_OUTPUT_TOKEN_CAPACITY  NOT_DERIVABLE
SELECTED_MAX_OUTPUT_TOKENS    NONE

REPRESENTATION_SHA256         2528a56a…  unchanged (3604 characters)
PROMPT_SHA256                 af528949…  unchanged
PROVIDER / ROUTE / POSTURE    anthropic / Commercial Terms / APPROVED
MODEL                         claude-sonnet-5, selection unchanged
PRICING                       anthropic-published-2026-09-02, unchanged
TED EGRESS                    PERMITTED_WITH_CONDITIONS, packet gate AVAILABLE

RETENTION_REPAIR_VERIFIED     true (7 synthetic paths, no network)
V1                            570657e1…  byte-identical, CONSUMED, cap still 3000
V2_CREATED                    false      V2_SHA256  none
V2_APPROVED                   false

MODEL_CALLS 0 · PROVIDER_REQUESTS 0 · REMOTE_TEST_CALLS 0 · TED_BYTES_SENT 0
NETWORK_REQUESTS 0 · DEPENDENCIES_INSTALLED 0 · CANONICAL_RESEARCH_MUTATION 0

RawRecords 325 · NormalizedRecords 325 · Signals 60 · Claims 91 · ClaimRevisions 92
Evidence 112 · ReliabilityAssessments 4 · IndependenceGroups 0
Opportunities 1 · OpportunityRevisions 2 · OpportunityEvidenceLinks 14
Embeddings 0 · Scores absent · SourceReviews 71

VIOLATIONS_CAUGHT / ESCAPED   73 / 0        positive controls 8 of 8
TESTS                         3831 bare-python; 3431 pytest
CI_GATES                      66 -> 67
CAPACITY_ARTIFACT             docs/data/second-opportunity-output-capacity-analysis-v1.json
NEXT                          OPERATOR_DECISION_ON_OUTPUT_SCHEMA_BOUNDEDNESS
```

---

## The gate that stopped the arithmetic

§6 is a gate placed before any computation: a finite maximum requires **every** variable-length
component to be bounded. A recursive walk of the executable schema — 33 nodes — found eight
required paths that are not:

| path | maxItems | item maxLength | introduced by |
|---|---|---|---|
| `supported_dimensions[]` | 14 | **none** | Mission 1.31 base schema |
| `unsupported_dimensions[]` | 14 | **none** | Mission 1.31 base schema |
| `supporting_evidence_ids[]` | 20 | **none** | Mission 1.31 base schema |
| `supporting_claim_ids[]` | 20 | **none** | Mission 1.31 base schema |
| `source_families[]` | 10 | **none** | Mission 1.31 base schema |
| `critical_uncertainties[]` | 12 | **none** | Mission 1.31 base schema |
| `commercial_claims_supported[]` | 8 | **none** | Mission 1.31 base schema |
| `commercial_claims_not_supported[]` | 14 | **none** | Mission 1.31 base schema |

Each array bounds how **many** strings it may contain and not how **long** any of them may be. A
single element could be a megabyte and still satisfy the contract.

So `SCHEMA_MAX_SERIALIZED_SIZE = UNBOUNDED`, and **inventing a practical maximum is exactly what
that gate exists to refuse.** No ceiling was selected, because any number would have been a guess
wearing the costume of a derivation — which is the defect this mission was called to repair.

---

## Whose schema this is

**All eight unbounded fields come from Mission 1.31's base schema, byte-identically.** The three
fields Mission 1.84 added — `recommended_next_evidence`, `confidence_classification`,
`statement_classifications` — are the **only properly bounded ones** in the whole schema.

That corrects Mission 1.84.2's attribution without excusing anything. 1.84.2 recorded the defect as
Mission 1.84's, which is right about the **failure to derive** and wrong about the **cause**:
Mission 1.84 could not have derived a ceiling from this schema even if it had tried, because there
was none to derive. What it did wrong was freeze a number anyway and call the budget reasoned.

The defect is therefore older and wider than the second-Opportunity work. It reaches a schema
Mission 1.31 froze and Mission 1.31.1 executed against — and it explains why *that* mission also
found its cap by trial and error, raising 1500 to 3000 until the answer fit, rather than by
computing anything.

---

## A floor, which is not a maximum

§6 forbids inventing a practical maximum. It does not forbid stating a **lower bound**, which is
arithmetic rather than invention: whatever the true maximum is, it is at least this, because the
unbounded arrays can only add to it.

Holding the eight unbounded arrays **empty**, every bounded field at its maximum legal length,
every enum at its longest member, worst-case JSON escaping applied, serialized through the
repository's own canonical path:

**FLOOR = 27709 characters.** Against a frozen cap of **3000**.

| field | serialized characters | bounded |
|---|---|---|
| `statement_classifications` | 16133 | yes |
| `recommended_next_evidence` | 4861 | yes |
| `evidence_bound_reasoning_summary` | 1838 | yes |
| `hypothesis_statement` | 1226 | yes |
| `observed_need` | 819 | yes |

The escaping matters and is applied rather than assumed away: a quotation mark serialises to two
characters, so a `maxLength` of 300 can occupy 600 serialized characters plus its quotes. Counting
visible characters would understate the floor.

At the deployment's one measured ratio the floor is roughly **12849 tokens** against a cap of 3000.
**That ratio is an input measurement and is not an output tokenizer**; it appears only to establish
the direction of the comparison, and no ceiling is derived from it.

---

## Tokens: the direction matters, and it is the unsafe one

`EXACT_MAX_OUTPUT_TOKEN_COUNT = NOT_ESTABLISHED`. No tokenizer for `claude-sonnet-5` is installed
or held, §15 forbids a network request to tokenize, and it forbids installing an unreviewed
dependency to obtain a convenient number. Neither was done.

The 2.1565 characters-per-token figure is classified `EMPIRICAL_LOWER_INFORMATION_BOUND`, and §16's
warning is the substantive one: **a characters-per-token ratio that is too HIGH divides by too much
and UNDERESTIMATES tokens**, which is the unsafe direction for a capacity ceiling. It came from one
**input** measurement of a prompt whose composition differs from this output. So it is not
multiplied by a safety margin as though it were a tokenizer.

---

## What was deliberately not done

No ceiling copied from 3000. No round number. No provider limit read and used as though it bounded
the schema — §7 keeps the three bounds apart, and a provider capability is not evidence a schema
fits inside it.

And **the failed 18-of-20 response did not influence which fields are kept.** `maxItems` was not
reduced, `maxLength` was not reduced, `confidence_classification` was not removed, nothing was
reordered, no default was introduced, no required field was made optional. Reducing
`statement_classifications` because field 20 went missing would be shaping a contract around one
rejected answer — and it would not even make the schema finite.

---

## Options, offered and not taken

| option | makes the schema finite | cost |
|---|---|---|
| **Bound the eight item strings** | **yes** | a schema and gate version bump, and a judgement about each field's longest legitimate value — an id, a dimension name and a free-text uncertainty do not share one sensible bound. It reaches Mission 1.31's base schema, so it is not local to this work. |
| Reduce `statement_classifications` | no | changes the contract and the gate version, and leaves the unboundedness untouched |
| Reference statement ids rather than repeat text | no | a different output representation; the ids still need bounding |
| Split synthesis from classification | no | a second call, which this arc's whole discipline exists to avoid |
| An operator-declared ceiling | no | the packet would record a ceiling that is **declared, not derived**, and must say so in those words |

**None implemented. None recommended.** Exactly one of them makes a ceiling derivable, and choosing
among them is an architecture decision rather than capacity arithmetic. The last one is listed
because refusing to name it would hide a real option: it is honest, and it is not what this mission
was asked to produce.

---

## Nothing else moved

Re-read from live state rather than assumed from Mission 1.84: the representation still hashes to
`2528a56a…` at 3604 characters, the prompt still hashes to `af528949…`, the provider posture is
still APPROVED, the subscription route is still NOT_APPROVED and unused, the model is still
`claude-sonnet-5` with FAST and BALANCED still binding the literal string `"null"`, the pricing
basis is still `anthropic-published-2026-09-02`, TED transmission is still
PERMITTED_WITH_CONDITIONS and the packet gate still AVAILABLE with no refusal reasons.

**`RETENTION_REPAIR_VERIFIED = true.`** The Mission 1.84.2 closure suite drives seven synthetic
terminal paths through the real Gateway with scripted transports and asserts each retains what it
can — raw response and its digest, parsed output and its digest, usage, terminal outcome — with a
tripwire asserting no fixture constructs the real transport. 31 tests, no network.

**V1 is byte-identical**, its cap is still 3000, its approval flag is still false, and the guard
still refuses its digest with `EXECUTION_APPROVAL_ALREADY_CONSUMED` while permitting an unseen one.

---

## Adversarial probe

**73 deliberate violations, 73 caught, 0 escaped. 8 positive controls, 8 accepted.**

The theme is one temptation: producing a number. 3000 copied forward, 4096, 8192, 16384, a derived
capacity from an unbounded schema, an exact token count with no tokenizer, the empirical ratio
reclassified as exact, the direction warning deleted, a provider limit standing in for a schema
bound.

**Several cases attack the derivation rather than the document**: they mutate the live schema and
check the gate follows the schema rather than the record — bounding everything while the record
still says unbounded, deleting a `maxItems`, opening `additionalProperties`. The gate walks the
executable schema, so a record that merely *claims* a finite bound is refused.

The controls prove the honest alternatives stay representable: a finitely bounded schema, a bounded
schema then carrying a derived ceiling, a larger floor, a fourth option, stricter accounting, a
different refusing outcome, more retention evidence, and the V1 guard staying active. Every case
restores the documents **and** the live schema, and the probe asserts no V2 file was left behind.

---

## Verification

`ruff format --check` and `ruff check` clean over 988 files — with two `S105` false positives
suppressed and the reason stated, because the flagged "token" is a model output-token count and not
a credential. `mypy` clean over 199 files. Contracts, catalog and registry checks clean. **All 67 CI
gates green locally**, the new one included. 3831 bare-python tests; 3431 pytest, database unchanged
across 29 tenant tables.

**Every canonical counter matches §33 exactly.** No canonical research mutation, no governance
change, no schema change.

---

## The 22 questions

1. **Finitely bounded?** No. Eight required paths are unbounded.
2. **Dominant fields?** `statement_classifications` (16133 of the 27709 floor), then
   `recommended_next_evidence` (4861) — both bounded and both added by Mission 1.84.
3. **Maximum valid serialized size?** UNBOUNDED. The bounded-subset floor is 27709 characters.
4. **Exact token counting available?** No. `NOT_ESTABLISHED`.
5. **Conversion method?** None used to derive anything; the empirical ratio appears only
   directionally, classified and disclaimed.
6. **Uncertainty remaining?** The whole ceiling. Nothing about it is derivable from this schema.
7. **Minimum output capacity derived?** `NOT_DERIVABLE`.
8. **MAX_OUTPUT_TOKENS selected?** `NONE`, because any value would be invented.
9. **New worst-case cost?** Not derived; it depends on a ceiling that does not exist.
10. **New execution ceiling?** Not derived, for the same reason.
11. **Output schema changed?** No.
12. **Prompt changed?** No, `af528949…`.
13. **TED representation changed?** No, `2528a56a…` at 3604 characters.
14. **Provider or model selection changed?** No.
15. **Retention repair verified?** Yes, synthetically, with no network.
16. **V1 still consumed?** Yes, and byte-identical.
17. **V2 created?** No.
18. **V2 SHA256?** None.
19. **V2 approved?** No — there is nothing to approve.
20. **Model calls?** Zero. Provider requests zero, network requests zero, TED bytes zero.
21. **Canonical research state changed?** No.
22. **Operator decision required?** Below.

---

## What is needed from the operator

**`OPERATOR_DECISION_ON_OUTPUT_SCHEMA_BOUNDEDNESS`.**

No execution packet can be prepared until either the schema has a finite maximum, or a ceiling is
declared as the operator's own judgement rather than as a derived bound. Both are decisions; neither
is arithmetic, and neither is taken here.

The narrowest change that answers the question asked is bounding the eight item strings — and it
reaches Mission 1.31's base schema, which Mission 1.31.1 already executed against, so it is a
contract decision rather than a local fix.

**Do not execute V2 — there is none. Do not call the provider. Do not retry V1. Do not change the
output contract to make a number come out. Mission 1.84.4 was not started.**
