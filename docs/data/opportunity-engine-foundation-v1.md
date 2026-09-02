# Opportunity Engine Foundation V1

Version: 1.0
Status: Authoritative
Created: 2026-09-02 (Sprint 1 / Mission 1.28)
Package: `packages/opportunity-engine/python/sros_opportunity`
Migration: `0029_opportunity_hypothesis_persistence.sql`

---

## §1 What an Opportunity is here

An **opportunity hypothesis** says: *a product or intervention serving actor X
with need Y through value proposition Z may be worth investigating, because
evidence A, B and C bears on specific dimensions of that idea.* It records a
question worth asking, together with what supports it and — required, never
optional — what does not.

It is **not** a market-size claim, a prediction, a recommendation to build, a
Claim copied into another table, a Signal, or an LLM brainstorm. Nothing this
engine produces guarantees demand, revenue, willingness to pay, market size,
adoption or product-market fit.

```text
Evidence -> facets -> dimension mapping -> eligibility -> subject grouping
         -> packet -> sufficiency -> [ external synthesis gate ] -> hypothesis
```

Everything before the gate is deterministic, reproducible, needs no model and
reaches no network. The gate is where a model would be reached, and §7 below is
why one is not reached today.

`OPPORTUNITY_HYPOTHESIS` and `SCORED_OPPORTUNITY` are separate concepts. This
version implements the first. **No score, rank, weight or ordering exists**, in
the package or in the schema.

---

## §2 The evidence dimensions

`opportunity-evidence-dimensions@1.0.0`. Fourteen questions an opportunity
hypothesis needs answered:

`PROBLEM_OR_NEED`, `RECURRENCE_OR_FREQUENCY`, `ECONOMIC_VALUE`,
`WILLINGNESS_TO_PAY`, `BUYER_OR_BUDGET_EXISTENCE`, `MARKET_ACTIVITY`,
`TREND_OR_CHANGE`, `SOLUTION_GAP`, `SOLUTION_DISSATISFACTION`,
`COMPETITIVE_SUPPLY`, `AUDIENCE_OR_USAGE`, `DISTRIBUTION_SIGNAL`,
`REGULATORY_OR_STRUCTURAL_DRIVER`, `FEASIBILITY_SIGNAL`.

**A dimension is not a score and carries no weight.** `WILLINGNESS_TO_PAY` is not
worth more than `AUDIENCE_OR_USAGE`; it is a different question.

**Every dimension states what it never means**, and `never_means` is a required
non-empty field. That is why the module is more than an enum: the repository's
recurring failure is an interpretation acquiring the status of a fact one layer
at a time, and the refusal belongs beside the definition where whoever adds a
mapping has to read it.

---

## §3 The mapping, and its bounds

`signal-type-dimension-map@1.0.0`. Mapping is from the **signal type**, because
that is what fixes a measurement's meaning. Not from the source: one publisher
can emit a series that maps somewhere and one that maps nowhere.

| signal type | dimensions | why |
|---|---|---|
| `content_request_change` | `AUDIENCE_OR_USAGE`, `TREND_OR_CHANGE` | requests for a named item are attention to a subject |
| `procurement_value_contrast` | `MARKET_ACTIVITY`, `BUYER_OR_BUDGET_EXISTENCE`, `ECONOMIC_VALUE` | a body ran a procedure, awarded a contract, and a figure was published |
| `numeric_period_change` | — | depends on WHICH indicator moved, and no reviewed indicator map exists |
| `lexical_frequency_change` | — | measures what media published, which is producer behaviour |
| `lexical_frequency_contrast` | — | same reason |

**Zero is a real answer and is the answer three times.** The brief permits it and
this map treats it as the default, requiring a positive argument for every member
added.

**Each mapping that assigns dimensions must state a `bound`**, refused at
construction if absent. The bounds preserve the source-bounded meaning:

- A Wikimedia request count is a count of HTTP requests for one article on one
  wiki in one day under the platform's own requester class. **A request is not a
  reader** — the operator documents its own automated-traffic classification as
  heuristic — and adjacent days do not cancel the calendar.
- A TED award figure is eForms BT-161: the value of all contracts awarded in the
  notice **including options and renewals**, lawfully withholdable under BT-195
  to BT-198. Not money paid, not a price, and **never willingness to pay**.
- GDELT lexical frequency maps nowhere at all. The standing invariant is not a
  caution but a refusal: it never satisfies a demand claim, *not weakly, not with
  low relevance and not with a caveat*.

### `TREND_OR_CHANGE` never counts toward diversity

In this repository a Signal **is** a derivation over two or more observations, so
every Evidence row describes a change by construction. A dimension the whole
corpus carries separates nothing, and letting it satisfy a two-dimension
requirement would let one measurement repeated six times look like two kinds of
evidence. `COUNTING_DIMENSIONS` excludes it, and a mapping consisting only of it
is refused at construction.

**This qualifier was chosen with the 26 real rows already inspected**, as §3 of
the mission brief instructed. `SufficiencyResult` therefore reports the dimension
count under **both** readings, so the qualifier's effect stays visible and can be
overruled.

---

## §4 Facets — twelve facts, no aggregate

`EvidenceFacets` exposes source family, use profile, claim type, lifecycle,
temporality, origin, direction, observation category, evidence level, relevance,
directness, extraction confidence, reliability and its status, independence
state and group, observation instant, signal type and dimensions — **separately**.

**Missing stays missing.** No optional field has a default. A reliability value
with no assessment behind it is refused, and so is a `RESOLVED` status with no
value: `0.5 because unknown` and `0.0 because we do not know` are measurements
nobody made, and `q_i = min(components)` must never be handed one.

---

## §5 Eligibility

`opportunity-input-eligibility@1.0.0`. Four states:

| state | meaning |
|---|---|
| `ELIGIBLE_SCORING` | may contribute to a future score |
| `ELIGIBLE_CONTEXT` | may be shown and cited, and may **never** be scored |
| `REQUIRES_REVIEW` | a question nobody has answered |
| `INELIGIBLE` | a decision somebody made, or a structural defect |

**`ELIGIBLE_CONTEXT` is not a weaker `ELIGIBLE_SCORING`.** Nothing promotes across
the line: there is no threshold, no override, no `force_scoring` parameter, and
the only route to `ELIGIBLE_SCORING` is a reliability a reviewed assessment
actually resolved.

**`REQUIRES_REVIEW` is never permission** — the source-registry rule one layer
out. **Policy is passed in, never looked up**: this package does not import
`sros_acquisition`, because an engine that could read the source registry could
decide its own authorization. Every blocking reason is returned, not the first.

---

## §6 Packets and grouping

`source-native-subject-grouping@1.0.0` and `opportunity-evidence-packet@1.0.0`.

Two rows share a packet only when they name the **same source-native subject**,
built from identifiers the source published and the Signal already carries in its
scope. Nothing is parsed out of a claim statement.

**No semantic grouping, in either direction.** `Docker_(software)`, `Podman` and
`Kubernetes` are three subjects and stay three packets. Merging them would be a
`SAME_PROBLEM_FAMILY`-shaped judgement — the relation Mission 1.27 parked —
reached by hand rather than by a classifier. Doing it deterministically would not
make it deterministic; it would make it unargued. The module has no string
distance, no token overlap, no stem, no synonym table and no threshold.

A packet holds **references, never copied truth**: ids and facts about ids, no
statements, no source text, no magnitudes. `packet_id` is sha256 over the
procedure versions and the ordered evidence ids, so identity is reproducible and
excludes the construction time.

**A packet never says "multiple independent sources".** `independence_summary`
emits that phrasing only when every row is `KNOWN_INDEPENDENT` across more than
one source family, which no packet in this deployment satisfies.

---

## §7 The external-synthesis gate

`opportunity-external-synthesis-gate@1.0.0`, resting on ADR-033. **A permission
to PROCESS is not a permission to SEND.**

- **Authorization is resolved before serialization**, not before the socket, so a
  refused packet leaves no string containing source-derived text.
- **A packet is authorised whole or not at all.** If one contributing source may
  not be transmitted the packet is `UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS`; it is
  never quietly trimmed, because a packet that dropped a source and still called
  itself the packet would let a model reason over a corpus a report described
  differently.
- **`NOT_ASSESSED` refuses and says so by name**, distinguishing an open question
  from a decision. An operator can act on the first.

**The gate is closed today, and the reason is exact.** Under
`local-private-research-v1`, `external_model_transmission` is `NOT_ASSESSED` for
`wikimedia-pageviews`, `world-bank`, `gdelt` and `ted-eu` — every source that
contributes Evidence. It is `PERMITTED_WITH_CONDITIONS` for `stack-exchange`
alone, which contributes none. **The one source cleared to leave the deployment
is the one source with nothing to send.**

---

## §8 Sufficiency

`opportunity-sufficiency@1.0.0`, pre-registered:

> at least **2** eligible Evidence rows **and** at least **2** distinct counting
> dimensions.

Statuses: `HYPOTHESIS_FORMABLE`, `HYPOTHESIS_INSUFFICIENT_EVIDENCE`,
`HYPOTHESIS_REQUIRES_REVIEW`.

**Formable is not scoring-ready and is not validated.** It says only that a
question can be asked without manufacturing its answer. `scoring_ready` is a
separate property, because two things that must not imply each other should not
share a field.

**No dimension is individually required.** A rule demanding
`WILLINGNESS_TO_PAY` on every hypothesis would make the engine unable to record
anything this portfolio can observe, which is a gate designed to produce a
predetermined answer.

---

## §9 Anti-hallucination

`opportunity-claim-guard@1.0.0`. Each forbidden term names **the dimension that
would license it**, so a refusal says which evidence is missing rather than which
word was typed. `tam`, `sam`, `som`, `market size`, `mrr`, `arr`, `growth rate`
and `product-market fit` are licensed by nothing: no registered source measures
them, and no dimension may be invented so that they can be asserted.

Matching is over **tokens**, never substrings — `supermarket` is not `market`.

`VALIDATION_WORDS` are refused unconditionally. No amount of evidence turns an
`OPPORTUNITY_HYPOTHESIS` into a `VALIDATED_OPPORTUNITY`.

---

## §10 Persistence

Migration `0029`, forward-only and non-destructive.

`research.opportunities` gains `status`, `creation_procedure`, `packet_id` and
`use_profile_id`. The `status` CHECK admits exactly `OPPORTUNITY_HYPOTHESIS`,
`HYPOTHESIS_WITHDRAWN` and `HYPOTHESIS_SUPERSEDED`. **`VALIDATED_OPPORTUNITY`,
`PROVEN_MARKET`, `WINNING_IDEA`, `PRODUCT_MARKET_FIT` and
`HIGH_CONFIDENCE_BUSINESS` are not members** — a state that does not exist cannot
be reached by a caller passing a string, which is what §18 of the brief means by
enforcing the distinction in code rather than prose.

`research.opportunity_hypothesis_revisions` is append-only, mirroring
`research.claim_revisions`. `unsupported_dimensions` and `epistemic_limitations`
are both constrained non-empty.

`research.opportunity_hypothesis_evidence` links a revision to real Evidence and
Claim rows by foreign key, and stores the **eligibility held at citation time** —
a hypothesis formed over context-only evidence must keep saying so even after
that evidence becomes scorable.

Both new tables carry `workspace_id` and row-level security.

---

## §11 What this version does not do

- **No score, rank, weight, priority or leaderboard**, asserted over the AST.
- **No model call.** The synthesis prompt is designed and not implemented,
  because §10 of the brief conditions it on coherent packets existing and none
  do.
- **No dependency on problem-family inference.** `SAME_PROBLEM_FAMILY` is not
  imported and not referenced in executable code. Recurring-problem Evidence can
  be added later as another entry in `mapping.py`, which is a data change.
- **No new epistemic rows.** The engine creates no Signal, Claim, Evidence or
  ReliabilityAssessment, and an Opportunity only where evidence supports one.
