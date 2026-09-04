# Falsifiable Evidence Apparatus Requirements V1

**Mission 1.48 — recorded 2026-09-04.**

> **This document is GENERATED.** Edit
> `falsifiable-evidence-apparatus-requirements-v1.json` and re-run
> `infrastructure/scripts/render_falsifiable_apparatus_requirements.py`.

## Primary outcome — `CONTRADICTION_CLAIM_IDENTITY_ARCHITECTURE_GAP`

The contradiction machinery is fully functional and structurally unreachable. Incompatible observations cannot inhabit one Claim identity under current semantics, so no Claim this architecture can build is capable of being contradicted. And the identity fact responsible -- source attribution -- is the SAME one that blocked corroboration in Mission 1.47. Both roads out of the B-2 identity are closed by one architectural decision, and no new apparatus can open either.

## The unification

Mission 1.47 found that two apparatuses cannot share one Claim because `source_id` is proposition identity. This mission finds that two apparatuses cannot DISAGREE on one Claim for exactly the same reason. Corroboration and contradiction are the only two routes by which the real aggregator becomes distinguishable from the B-2 baseline, and both require two observations to inhabit ONE Claim. Source attribution in proposition identity forbids that.

**Consequence.** The binding constraint is NOT a missing apparatus. A new apparatus, however well chosen, would interpret to facts carrying its own `source_id`, produce its own `proposition_key`, and therefore its own Claim -- where it can neither join a support group nor contradict anything. Acquiring it would add rows and change nothing.

*Measured:* All 43 Claims carry `source_id` in proposition identity, and 0 would merge if it were dropped.

*Not a bug:* Source attribution is correct for an OBSERVED claim and Mission 1.38 established why: for an OBSERVED claim the attribution IS the claim. 'Wikimedia counted X' and 'Stack Exchange published Y' are two propositions. The gap is not that this is wrong; it is that the project has no OTHER claim layer, and the layer that would carry a source-independent proposition is the INFERRED one, which is deliberately unbuilt.

## §0 — Reconstructed from live code

**A_one_group_equals_b2** — established: **True**

- how: The REAL aggregate() was run over all 43 live Claims with reliability resolved through the REAL resolver, and B-2 was computed independently as max(q) over scorable supporting items.
- result: aggregator_differs_from_b2_cases = 0, max_support_groups_on_one_claim = 1
- why algebraic: Saturation over one group is that group's strength; group strength is max() over its members; B-2 reports the same maximum. Equal by algebra, not coincidence, so no quantity of additional single-group Evidence can separate them.

**B_two_independent_groups_can_differ** — established: **True**

- how: Non-persisted fixture, two KNOWN_INDEPENDENT SUPPORTS items through the real aggregator.
- result: 2 support groups, and S = 1 - (1-g_A)(1-g_B) exceeds max(g_A, g_B) for fixture-owned strengths in (0,1).

**C_contradiction_produces_non_zero_mass** — established: **True**

- how: Non-persisted fixture, one SUPPORTS and one CONTRADICTS on one claim_id, through the real aggregator.
- result: support_strength 0.6, contradiction_strength 0.5, supported_mass 0.3, contradicted_mass 0.2, conflict_mass 0.3, uncertainty_mass 0.2, summing to 1.0.
- conclusion: The machinery is NOT the gap. It works exactly as specified and has never been reached.

## §9 — Why contradiction is unreachable

**Verdict: `ARCHITECTURE_PREVENTION`.**

### blocker 1 direction is identity

- **Fact.** `direction` is written into `proposition_facts` by all three implemented restatement templates, and `proposition_key()` names direction among the facts a proposition is about.
- **Consequence.** An INCREASING and a DECREASING observation of the same metric over the same period produce two different proposition keys, hence two Claims. The contradicting observation cannot reach the Claim it would contradict.
- *Live evidence:* Three Claim pairs in the corpus differ ONLY in `direction` -- the Wikimedia witnessed existentials for Docker, Kubernetes and Podman.

### blocker 2 no interpreter can emit contradicts

- **Fact.** `EvidenceDirection.SUPPORTS` appears exactly ONCE in the whole interpreters package, as a hard-coded literal. `EvidenceDirection.CONTRADICTS` appears nowhere in it.
- The template says why: 'The claim IS this Signal said back. It cannot bear against itself, and a NEUTRAL row would assert the Signal bears on nothing.'
- **Consequence.** Even if claim identity permitted it, no implemented interpreter could produce the contradicting row.
- *Live evidence:* All 57 Evidence rows in the corpus are SUPPORTS. Not one CONTRADICTS row has ever existed.

### blocker 3 source id is identity

- **Fact.** All 43 Claims carry `source_id` in proposition identity.
- **Consequence.** The cross-source case -- two apparatuses reporting incompatible values -- cannot arise, because the two observations form two Claims before their values are ever compared. This is the blocker that also closes corroboration, and it is the deepest of the three.
- *Note:* Blockers 1 and 2 are single-source blockers and could in principle be revisited per template. Blocker 3 is a decision about what an OBSERVED claim means.

*No, and it is deliberately not repaired. Section 9 forbids it, and the repair is a Claim-semantics design question with an ADR behind it rather than an edit.*

## §10 — Source attribution and contradiction

'Source A reported X' and 'Source B reported Y' are both TRUE simultaneously, whatever X and Y are. They are two facts about two publications, not a disagreement about the world. So differing values can never constitute a contradiction between source-attributed OBSERVED Claims.

**What a real cross-source contradiction requires: option A.**

| option | description | status |
| --- | --- | --- |
| A | a source-independent INFERRED Claim | `NOT_IMPLEMENTED_AND_NOT_IMPLEMENTED_HERE` |
| B | a reviewed convergence layer | `REFUSED_BY_CURRENT_CONTRACT` |
| C | a new deterministic measurement Claim type | `NOT_PROPOSED` |
| D | another existing mechanism | `NONE_AVAILABLE` |

**A.** This is what a cross-source contradiction actually needs. A proposition like 'Metric M for E at T is X' asserts about the WORLD, so two measurements of it can genuinely disagree. It is INFERRED by construction, because moving from 'a source reported X' to 'X is the case' is an inference step.

**B.** A governed cross-source OBSERVED convergence contract could let two attributed observations witness one proposition. Mission 1.47 proved the current contract structurally refuses this, on two independent guards. It would be a smaller change than the INFERRED layer and it inherits the near-tautology problem: the propositions such a contract can express faithfully are the weak ones.

**C.** A third claim type between OBSERVED and INFERRED would need its own epistemic semantics, its own reliability scope treatment and its own ADR. Recorded as an option and not preferred: the taxonomy is a closed enum of five and widening it is the largest of these changes.

**D.** None found. Claim revisions represent a CHANGED assertion rather than a disagreement, and Mission 1.41 already established that a disagreeing row is reported as a conflict and nothing is written.

*No change was made and none is proposed as a convenience. Section 10 forbids removing `source_id`, Mission 1.38 established that attribution IS the claim for an OBSERVED proposition, and Mission 1.47 refused the same shortcut from the corroboration side.*

## §1 / §11 — Falsifiability, and the trade-off

A Claim is falsifiable here when it states:

- an exact subject or entity
- an exact measured property
- an exact bounded period or point in time
- an exact geography or population where applicable
- an exact unit, category or state
- explicit truth conditions
- explicit falsifier conditions

**The decisive test.** There must exist an observation that would count as CONTRADICTS, and a different observation that would count as SUPPORTS, WITHOUT either changing proposition identity. If the contradicting observation would produce a different proposition_key, the Claim is not falsifiable in this architecture -- it is merely replaceable.

*This is the test that separates a genuine falsifier from a second Claim. It is architecture-aware on purpose: a proposition can be philosophically falsifiable and still unfalsifiable HERE, because identity decides which Claim an observation attaches to.*

| family | monotone | falsifiable | falsifiability | same proposition matchability | independent measurement plausibility | contradiction capability | reliability reviewability | source native semantics | calibration information value | current model fit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `EXACT_POINT_VALUE` | no | yes | STRONG | STRONG | MEDIUM | STRONG | STRONG | STRONG | STRONG | WEAK |
| `THRESHOLD_STATE` | no | yes | STRONG | STRONG | MEDIUM | STRONG | STRONG | MEDIUM | STRONG | WEAK |
| `EXACT_DIRECTION` | no | yes | STRONG | MEDIUM | MEDIUM | NOT_APPLICABLE | STRONG | STRONG | MEDIUM | WEAK |
| `BOUNDED_CATEGORY_STATE` | no | yes | MEDIUM | MEDIUM | MEDIUM | MEDIUM | MEDIUM | MEDIUM | MEDIUM | WEAK |
| `RATE_OR_PROPORTION` | no | yes | MEDIUM | WEAK | WEAK | MEDIUM | WEAK | WEAK | MEDIUM | WEAK |
| `SOURCE_ATTRIBUTED_EXISTENTIAL_WITNESS` | **yes** | **no** | WEAK | STRONG | STRONG | NOT_APPLICABLE | STRONG | STRONG | WEAK | STRONG |
| `SOURCE_ATTRIBUTED_HISTORICAL_RESTATEMENT` | **yes** | **no** | WEAK | WEAK | WEAK | NOT_APPLICABLE | STRONG | STRONG | WEAK | STRONG |

**The proposition shapes that are easiest to make cross-apparatus are exactly the ones that cannot be contradicted, and the shapes that can be contradicted are exactly the ones only one apparatus supports.**

*Why:* An existential is satisfied by ONE qualifying observation, so almost any apparatus that observes anything about the subject can entail it -- and for the same reason no observation can refute it. A point or threshold claim asserts something specific enough that a second measurement can disagree, and specific enough that the second apparatus must match on subject, period, unit, population and operational definition before its disagreement counts as disagreement rather than as a different question.

*Observed, not predicted:* Mission 1.47 reached the first half by trying to converge two apparatuses and finding only an existential worked. This mission reached the second half by finding that the contradiction machinery is fully functional and structurally unreachable. The trade-off is now an observed architectural fact of the project rather than a hypothesis.

### The live demonstration

3 Claim pairs in the corpus differ ONLY in `direction`, over `Docker_(software)`, `Kubernetes`, `Podman`:

> The source counted at least one pair of adjacent day buckets in which requests were HIGHER in the later bucket.

> The source counted at least one pair of adjacent day buckets in which requests were LOWER in the later bucket.

- They differ only in `direction`, and `direction` is proposition identity, so they are TWO Claims. A contradicting observation cannot reach the Claim it would contradict.
- Both are existentials over the same held series and BOTH ARE TRUE. Requests rose on some adjacent pairs and fell on others.
- Even if they inhabited one Claim, neither could falsify the other: a counterexample does not refute an existential.

**The pair that most looks like a contradiction is not one for three independent reasons, and only the first is architectural.**

## §5 — Preferred proposition family

**`THRESHOLD_STATE`** — Metric M for entity E at time T is >= X, under a named operational definition and unit.

**Why.** It is the only family that is falsifiable AND tolerant of the measurement noise that two genuinely independent apparatuses always produce. An EXACT_POINT_VALUE claim is contradicted by a rounding difference, which would manufacture false contradictions and make independent corroboration nearly impossible -- two honest apparatuses rarely publish the identical number. A threshold admits a real falsifier (a measurement below X) while letting two apparatuses that disagree slightly both SUPPORT it. It therefore serves BOTH routes, which no other family on the list does.

- Strongest source-native semantics and the worst noise behaviour. It is the family to prefer only if a future apparatus pair is known to publish to identical precision under an identical definition, which nothing in this portfolio does.
- `direction` is proposition identity today, so its CONTRADICTION_CAPABILITY is NOT_APPLICABLE rather than weak: the contradicting observation forms a different Claim.
- Monotone, hence not contradiction-capable at all, and Mission 1.47 established that the informative value of the cross-apparatus existential is near-tautological.

**The cost of the choice.** X is OURS rather than the source's, so a threshold introduces a governance question the other families do not have: who chooses X, on what basis, and how is it prevented from being chosen after seeing the data. That is a real cost and it is recorded rather than discounted. This project already refuses 'an arbitrary number wearing the costume of a rule', and a threshold picked to make a case work would be exactly that. The threshold must be frozen BEFORE the second measurement is retrieved.

Current model fit: **WEAK** — Not because the family is wrong, but because of the architecture gap above: no threshold Claim can host two sources' Evidence while `source_id` is identity.

## §6 — Apparatus requirements

*A search specification for a future mission. It names no source, vendor,
API or product, deliberately: the question is what an apparatus must
observe, before who publishes such data.*

| requirement | must be |
| --- | --- |
| `apparatus_observes` | A quantity that some OTHER already-held apparatus also observes, about the same subject, over the same kind of period -- where 'the same quantity' means the same measured property of the same population, not merely a related one. |
| `apparatus_emits` | A numeric measurement with an explicit unit, an explicit population or geography, and an explicit bounded period, attributable to a named measurement definition. |
| `subject_granularity` | EXACT and externally identifiable: the apparatus must publish an identifier for the subject that an existing reviewed registry entry can be matched to by EXACT EQUALITY. No distance, no token overlap, no stem, no synonym table, no embedding. |
| `time_granularity` | The apparatus must publish a period whose boundaries are DEFINED by the source, not inferred from the extent of what was retrieved. It must be alignable to the partner apparatus's grain by exact equality of a defined interval, not by overlap or containment. |
| `unit_semantics` | An explicitly published unit, and either the SAME unit as the partner apparatus or a deterministic reviewed unit equivalence. No currency conversion, no normalisation, no rescaling. |
| `population_or_geography_semantics` | An explicitly published population or geography definition, and either identical to the partner's or connected by a reviewed equivalence. A shared label is not a shared population: Mission 1.46 found de facto midyear population and usually-resident 1 January population sharing a year label and measuring different things. |
| `methodology_documentation` | DOCUMENTED, first-party, and RETRIEVABLE by this deployment through a lawful route. This is the requirement Mission 1.47 found decisive and it is not negotiable. |
| `lineage_documentation` | DOCUMENTED. The upstream producer must be IDENTIFIED, so that independence can be established affirmatively rather than inferred from the absence of a found dependency. |
| `upstream_producer` | IDENTIFIED, and DIFFERENT from the partner apparatus's upstream producer. Mission 1.46 established that for official macro statistics the international publishers are distribution layers over one national producer, so a second publisher of the same series is not a second producer. |
| `revision_policy` | DOCUMENTED_OR_BOUNDED. A measurement that can be silently restated makes a contradiction indistinguishable from a revision, which is the exact ambiguity Mission 1.41 refused to resolve by inventing a third answer. |
| `observation_recoverability` | ESTABLISHED_ENOUGH_FOR_REVIEW: a reviewer must be able to check what the source said at the time, or the source must document that it cannot be checked. Either is reviewable; silence is not. |
| `measurement_definition` | BOUNDED and published. A reviewer must be able to identify the five-part reliability scope (source, resource, record kind, claim type, proposition kind) from the documentation. |
| `missingness` | DOCUMENTED_ENOUGH_FOR_REVIEW. Whether an absent value means zero, withheld or not-collected must be answerable, because a missing observation is not a contradiction and the two must be distinguishable. |
| `independence_comparability` | POSSIBLE: the documentation must be sufficient to establish that this apparatus's event-generation and collection do not share an upstream with the partner's. |
| `contradiction_comparability` | POSSIBLE: the apparatus must publish a value that could be compared against the partner's on the SAME proposition, once the architecture permits one proposition to hold both. |

## §14 — Falsifier specification

**Claim.** Metric M for entity E at time T is >= X, under operational definition D and unit U

- **`SUPPORT_CONDITION`** — a source-native measurement of M for E at T, under D and U, whose value is >= X
- **`CONTRADICT_CONDITION`** — a source-native measurement of M for E at T, under D and U, whose value is < X
- **`NON_EVIDENCE_CONDITION`** — no record of M for E at T -- contributes nothing, contradicts nothing
- **`SEMANTIC_MISMATCH_CONDITION`** — a measurement under a different population, unit, period or operational definition -- bears on a different proposition and must not be attached
- **`UNKNOWN_CONDITION`** — a measurement whose lineage or measurement-definition equivalence is not established -- attaches with independence UNKNOWN and must not be counted as a second provenance group

## §4 — What is not a contradiction

| case | why not |
| --- | --- |
| an INCREASING Claim beside a DECREASING Claim | direction is proposition identity, so these are two Claims and neither bears on the other |
| different periods | two measurements of different times are both true; a value changing over time is not a disagreement |
| different geography or population | different populations, different quantities |
| different units | not comparable without a reviewed equivalence |
| different measurement definitions | measuring different things; Mission 1.46's midyear de facto against 1 January usually-resident population |
| different requester classes | a count under one audience class is not a count under another; Mission 1.19 made the class REQUIRED for exactly this reason |
| a missing observation | absence of a record is not evidence against; a NON-SCORABLE or absent item contributes nothing and does not contradict |
| another source being silent | silence is not a counterexample, and for a monotone existential it could not be one even in principle |
| one source reporting a different but compatible statistic | a semantic mismatch, not a disagreement: the observations are about different propositions |

## §7 / §8 — Pair templates

**Independence-capable pair.** Shared claim:

> Metric M for entity E at time T is >= X, under operational definition D and unit U.

Independence proof requires:

- no direct republication of one apparatus's values by the other
- no shared upstream measurement producer
- neither consuming the other's values as an input
- genuinely distinct event-generation or measurement processes
- first-party documentary support for each lineage

*Explicitly insufficient:* Organisational separation. Two different companies, hostnames, databases or web pages establish nothing: Mission 1.46 found one publisher reproducing another's series verbatim, source code and all.

**Contradiction-capable pair.** Claim:

> Metric M for entity E at time T is >= X, under operational definition D and unit U.

- Evidence A — SUPPORTS -- a measurement of M for E at T under D and U that is >= X
- Evidence B — CONTRADICTS -- a measurement of M for E at T under D and U that is < X
- Both must share: proposition identity, subject, period, geography or population, unit, operational definition, an explicitly governed deterministic equivalence for any of the last four.

**Blocked today by.** Proposition identity. Under current semantics Evidence A and Evidence B would carry different `source_id` values, produce different proposition keys and land on two different Claims -- so the shape above cannot be built from real data, only from fixtures.

## §15 — Reliability reviewability gate

**A theoretically ideal apparatus whose methodology cannot be reviewed is not useful to this system, and must not be promoted because its observations are attractive.**

- first-party measurement definition available and retrievable
- first-party methodology or provenance documentation available and retrievable
- known limitations accessible
- a reviewer can identify the five-part reliability scope
- the documentation can be lawfully retained and cited

*Why first class:* Mission 1.47 proved the cost of learning this late. Stack Exchange's observations are excellent and its methodology documentation is unreachable because the site's robots policy blocks this environment's fetcher -- and no bypass, header variation, mirror or third-party summary may stand in for a first-party document. That single absence left independence UNKNOWN AND is the reason the operator declined both Stack Exchange reliability scopes in Mission 1.36.1. One inaccessible document disqualified an otherwise strong apparatus on two separate gates.

*Consequence for search:* Documentation retrievability must be checked BEFORE an apparatus is treated as a candidate, not after its data looks useful.

## §16 — Governance compatibility gate

- a lawful acquisition route exists
- eligible under the target use profile, with the profile named
- field minimisation is possible AT acquisition rather than after it
- retention compatible with the retention policy
- derived analytical use permitted
- no circumvention of any kind is required: no anti-bot bypass, no rate-limit evasion, no undocumented endpoint, no authentication bypass
- provenance documentation is retrievable through a permitted route

*Governance is a separate gate from epistemic usefulness, in both directions. An apparatus can be perfectly reviewable and refused, or fully authorised and useless.*

## §17 — Held apparatus matrix

| apparatus | falsifiable point claim | documented lineage | potential second measurement | contradiction capable | same subject partner | reliability reviewable | currently eligible | currently held |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `wikimedia-pageviews | platform_counted_content_request_change` | NO | YES | NO | NO | YES | YES | YES | YES |
| `wikimedia-pageviews | platform_counted_content_request_change_witnessed` | NO | YES | NO | NO | YES | YES | YES | YES |
| `stack-exchange | community_site_published_questions_carrying_tag` | NO | NO | NO | NO | YES | NO | YES | YES |
| `stack-exchange | community_site_questions_without_accepted_answer` | NO | NO | NO | NO | YES | NO | YES | YES |
| `ted-eu | source_reported_procurement_value_contrast` | NO | YES | NO | NO | NO | YES | YES | YES |
| `ted-eu | source_published_classification_value_contrast_witnessed` | NO | YES | NO | NO | NO | YES | YES | YES |
| `world-bank | source_reported_metric_period_change` | NO | YES | YES | NO | NO | YES | YES | YES |
| `gdelt | source_reported_term_frequency_change` | NO | NO | NO | NO | NO | NO | YES | YES |
| `gdelt | source_reported_term_frequency_contrast` | NO | NO | NO | NO | NO | NO | YES | YES |

**FALSIFIABLE_POINT_CLAIM is NO for all nine, and CONTRADICTION_CAPABLE is NO for all nine. Every implemented proposition kind is either a source-attributed historical restatement or a monotone existential, which are precisely the two families the trade-off record marks unfalsifiable. This is not a coincidence of the corpus: it is what the only implemented interpreter produces.**

*`world-bank` is the single apparatus marked POTENTIAL_SECOND_MEASUREMENT, because a national statistical aggregate is a quantity other publishers also publish. Mission 1.46 established that those publishers are distribution layers over the same national producer, so the potential is real in shape and refuted in fact for this series.*

## §18 — Registered but unheld

Measured live: **7** eligible of **29** registered, **5** with a collector, **22** blocked at the gate.

- **`eurostat`** — `KNOWN_MISMATCH`. Eligible under the local profile with no resource and no collector, and it publishes exact point values with documented ESMS methodology, so on apparatus SHAPE it fits well. It is a KNOWN_MISMATCH rather than promising because Mission 1.46 established on the publishers' own documentation that Eurostat is UPSTREAM OF the World Bank for the series this deployment holds, and that Eurostat itself compiles what National Statistical Institutes transmit. It would be a second publisher, not a second producer.
- **`fred`** — `KNOWN_MISMATCH`. Same eligibility shape. Refuted more sharply: FRED's own page names Source 'World Bank', Release 'World Development Indicators' and Source Code SP.POP.TOTL. It republishes the exact series already held.
- **`usaspending`** — `INSUFFICIENT_INFORMATION`. A second public-procurement apparatus beside TED, blocked at the eligibility gate today. It is recorded as INSUFFICIENT_INFORMATION rather than promising because it observes a DIFFERENT jurisdiction's contracts, so it is not a second measurement of the same phenomenon -- it would produce complementary evidence, which Mission 1.47 established is not Claim-level corroboration. Establishing otherwise would need a governance review this mission may not perform.

**No registered source is PROMISING_FROM_EXISTING_DOCUMENTATION for the required apparatus type. The two whose SHAPE fits best are the two Mission 1.46 already refuted on provenance, which is the same answer arriving from a different direction.**

## §20 / §21 — Route comparison and calibration relevance

**Result: `NEITHER_CURRENTLY_ACTIONABLE`.** Both routes require two observations to inhabit ONE Claim, and source attribution in proposition identity forbids that. Neither is blocked by a missing apparatus, so neither becomes actionable by acquiring one.

**Preferable once unblocked: INDEPENDENT_CORROBORATION.** Corroboration is strictly easier than contradiction. It requires exact subject, period, unit, population and definition alignment plus established independence. Contradiction requires ALL of that AND an actual disagreement between two apparatuses that agree on everything else -- which is a fact about the world that cannot be arranged in advance. A mission can plan for corroboration; it can only hope for contradiction.

*A contradiction is also the more informative outcome when it occurs, because it is the only case that tells the operator something is WRONG rather than merely supported. The recommendation prefers corroboration on tractability, not on value.*

- `STRUCTURALLY_IDENTIFYING`: **YES** — A THRESHOLD_STATE Claim with two independent supporting measurements produces two support groups, and saturation exceeds max(g_A, g_B) -- the first case where the full aggregator differs from B-2. With one supporting and one contradicting measurement it produces non-zero contradiction and conflict mass, which no real Claim has ever produced.
- `SEMANTICALLY_USEFUL`: **YES** — Unlike Mission 1.47's existential, a threshold claim carries information a person would act on: whether a measured quantity is above a bound, and whether two independent measurements agree about that. A reviewer comparing two such evidence sets is comparing something real, which is what a calibration reference judgement requires.

## §22 — Opportunity usefulness

- presence or absence of a real phenomenon, at a stated bound
- measurable change, where two bounded periods are each observed
- independent confirmation, where two lineages are established
- disagreement requiring investigation, which is the only signal that tells an operator to go and look

**Does not support.** Nothing here is promoted to market demand, willingness to pay or product-market fit. A threshold claim about a measured quantity is a threshold claim about a measured quantity.

*This is why the preferred family is worth having beyond aggregator diagnostics: the fourth item is a research capability the system does not currently have at all, because no Claim can currently disagree with anything.*

## Counters and budget

| counter | before | after |
| --- | ---: | ---: |
| raw_records | 325 | 325 |
| normalized_records | 325 | 325 |
| signals | 33 | 33 |
| claims | 43 | 43 |
| claim_revisions | 44 | 44 |
| evidence | 57 | 57 |
| reliability_assessments | 4 | 4 |
| reliability_basis_rows | 12 | 12 |
| independence_groups | 0 | 0 |
| opportunities | 1 | 1 |
| opportunity_revisions | 1 | 1 |
| opportunity_evidence_links | 7 | 7 |
| embeddings | 0 | 0 |
| registered_sources | 29 | 29 |
| evidence_with_stored_reliability | 0 | 0 |
| scores | ABSENT | ABSENT |

`RESEARCH_DATA_REQUESTS` **0**, `APPARATUS_DOCUMENTATION_REQUESTS` **0**, `GOVERNANCE_DOCUMENT_REQUESTS` **0**. Zero requests of every kind. Every apparatus and governance fact used here was already held in the repository or measurable from the live deployment.

Model calls **0**, 0.00 USD, embeddings **0**, Problem-Family **PARKED**.

## Next mission

**Not candidate discovery.** A constrained source search is the WRONG next mission, even though this record freezes the specification it would use. No apparatus can exercise either route while source attribution is proposition identity, so a discovery mission would end by finding a good candidate that cannot be used.

**Recommended.** A narrow Claim-semantics and contradiction-reachability DESIGN mission, before any data search. It must decide whether a source-independent proposition belongs in the INFERRED layer, in a governed cross-source OBSERVED convergence contract, or in neither -- and it must decide it as a semantics question with an ADR, not as an edit to a template.

*The apparatus requirements in this record are deliberately reusable as a search specification. They are not wasted: they are the second half of the work, and they become actionable the moment the first half is decided.*

*Mission 1.49 was not started.*

