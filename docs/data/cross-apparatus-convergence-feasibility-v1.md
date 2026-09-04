# Cross-Apparatus Proposition Convergence Feasibility V1

**Mission 1.47 — recorded 2026-09-04.**

> **This document is GENERATED.** Edit
> `cross-apparatus-convergence-feasibility-v1.json` and re-run
> `infrastructure/scripts/render_cross_apparatus_convergence_feasibility.py`.

## Primary outcome — `FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK`

A narrow, source-faithful proposition over the Docker subject IS independently entailed by both held apparatuses. It is also so weak that it discards exactly what each apparatus measures. Strengthen it in any direction that carries information and only one apparatus supports it. So the convergence that is available is not worth building, and the convergence that would be worth building is not available.

**Selected route: NONE.** No pair passes all eight section 26 gates. Section 26 forbids a least-bad fallback and section 25 forbids a weighted score, so the slot is left empty rather than filled with the closest candidate.

### Findings recorded beside it

**`CROSS_APPARATUS_EVIDENCE_IS_COMPLEMENTARY_NOT_CORROBORATING`** — Above the existential floor the two apparatuses answer different questions. The repository recorded this before this mission asked: the Opportunity engine's own mapping rationale for community_question_volume says the PROBLEM_OR_NEED question is 'a genuinely different question from the one AUDIENCE_OR_USAGE answers: that one says something attended to a subject, this one says somebody said they were stuck on it, and neither implies the other.' That is complementarity stated by the codebase, not inferred by this mission.

*Why not the primary outcome:* Outcome C says the apparatuses 'do not independently support the same Claim'. For the existential floor they DO, so C as written would be false of the one candidate that passes semantics. D is true of it.

**`CONVERGENCE_CONTRACT_ARCHITECTURE_GAP`** — PropositionConvergenceContract structurally cannot express a cross-apparatus proposition. Two independent refusals: the constructor raises unless 'source_id' is in identity_fields, and SourceBoundary has exactly one member, SAME_SOURCE_AND_RESOURCE. Its docstring states the absence is deliberate -- 'A cross-source value is deliberately absent rather than present-and-unused. An enum member nobody may pass is an invitation.'

*Why not the primary outcome:* Reporting the architecture as the blocker would imply that widening the contract unlocks this route. It does not: the proposition would still be near-tautological and independence would still be UNKNOWN. Mission 1.46 refused outcome B for the same reason -- a blocker downstream of the real one misattributes the failure to a layer that never got to fail.

**`PROVENANCE_INDEPENDENCE_NOT_ESTABLISHED`** — Independence for the Docker pair is UNKNOWN, and it is NOT refuted. This is a different state from Mission 1.46's, and the difference decides what a future mission may attempt.

*Why not the primary outcome:* Same upstream argument. Independence is evaluated only after same-proposition semantics pass (section 12), and the semantics finding is what outcome D names.

**`SINGLE_ROOT_CAUSE_BLOCKS_TWO_INDEPENDENT_GATES`** — Gate 6 (established independence) and reliability readiness fail for ONE documented reason: Stack Exchange's own methodology documentation is unreachable because the site's robots policy blocks this environment's fetcher. No retry, no varied header, no mirror, no cached copy and no third-party summary was used, and none was attempted in this mission. The same absence that stopped Mission 1.36 from preparing a Stack Exchange reliability question stops this mission from documenting its measurement lineage.

## §1 — What an apparatus is

A measurement apparatus is a (source_id, proposition_kind) pair: one publisher operating one measurement contract that yields one kind of proposition.

*Why not a source:* A source is too coarse. wikimedia-pageviews operates two apparatuses over one corpus (a detailed adjacent-day change and a witnessed existential), and so does ted-eu. Counting sources would report four apparatuses where nine exist, and would merge two reliability scopes that the contract already holds apart.

*Why `proposition_kind`:* proposition_kind is the discriminator Mission 1.13.1 writes into research.claims.proposition_facts, and it is the fifth field of the five-part reliability scope in evidence-reliability-contract-v1.md. Using it here means the apparatus inventory and the reliability scope inventory are the same partition, so a new apparatus is a new reliability question by construction.

*Counted, not assumed:* Nine apparatuses over four sources, measured. Mission 1.36 section 0 found three reliability scopes where two source families invited two, and the same discipline applies here.

## §2 — Subject overlap, measured before any pair was chosen

*Method:* The reviewed canonical-subject registry (canonical-subject-registry-v1.json, exact equality, no distance, no token overlap, no stem, no synonym table, no embedding) crossed with which side actually carries Evidence.

**Wikimedia + Stack Exchange was NOT pre-selected. The overlap was measured first, across all nine apparatuses, and the pair fell out of the measurement.**

| subject | wikimedia Evidence | stack-exchange Evidence | cross-apparatus |
| --- | ---: | ---: | --- |
| `docker` | 12 | 2 | **YES** |
| `kubernetes` | 12 | 0 | no |
| `podman` | 12 | 0 | no |

Docker is the ONLY cross-apparatus shared subject in the held corpus, and that is a measured result rather than an assumption. The registry itself already recorded why the other two fail: kubernetes is mapped 'for completeness of the registry; NO Evidence reaches this identifier today, because the questions this deployment holds under it arrived through a tagged=docker query and are a biased subset rather than a count', and podman because 'this deployment holds no questions carrying it'.

*Everything else:* gdelt (climate, weather), ted-eu (CPV divisions 90 and 92) and world-bank (SP.POP.TOTL over DEU and FRA) share no subject with any other apparatus and with each other. No registry entry maps them, and inventing one would be the deterministic-but-unargued merge Mission 1.28 refused.

## §10 — Time alignment

**wikimedia_detailed** — grain: whole UTC day buckets, ESTABLISHED on the operator's own Research:Page view definition

- held: 2024-03-01 .. 2024-03-07, giving 6 adjacent-day changes
- note: 7 of the 31 days of March 2024

**wikimedia_witnessed** — grain: none

- held: period_label, period_label_from and period_label_to are ALL null on both witnessed Claims
- note: The witnessed apparatus asserts an unbounded existential. It carries no period in proposition identity at all, which is a stronger fact than a wide period.

**stack_exchange** — grain: Unix epoch seconds, the observed extent of the retrieved questions rather than a period the source defines

- held_tag: 1709280363 .. 1709612240 = 2024-03-01T08:06:03Z .. 2024-03-05T04:17:20Z
- held_unaccepted: 1709280363 .. 1709612094 = 2024-03-01T08:06:03Z .. 2024-03-05T04:14:54Z

**Aligned: NO.** The windows OVERLAP and are NOT ALIGNED. Stack Exchange starts 8h06m into 2024-03-01 and ends 4h17m into 2024-03-05; Wikimedia holds whole UTC days. Aligning them would require sub-daily Wikimedia counts, and the finest grain this deployment holds is a day. So no exactly-aligned bounded period exists for any quantitative comparison.

*Containment:* Both windows are contained in March 2024. Containment is weaker than alignment and is all an existential needs, which is precisely the section 5 warning arriving in the time column.

*Deterministic temporary aggregation* — needed: **NO**, available: **NO**.

- Not needed because: An existential over a containing period is entailed by a single qualifying observation inside it. No sum, mean or monthly aggregate is required to establish it, so section 10's diagnostic-aggregation permission is never invoked.
- Not available because: Even if it were wanted, it is refused. Section 10 permits summing held daily Wikimedia counts to an exact March 2024 window only 'if the complete required daily observations are actually held'. This deployment holds 7 of 31 March days. Completeness is NOT established, so no monthly aggregate was manufactured.
- Both reported because: Reporting only 'not needed' would leave a reader believing the aggregate was available and merely unused.

## §7 — Candidate propositions, narrowest first

### `P-A1` — class A, direct observable class abstraction

> At least one public platform recorded, during March 2024, an event of a defined class that it attributes to the subject `docker`.

*Event class:* The ONLY definition under which both apparatuses qualify is a disjunction: (a) a content request counted under Wikimedia's own Research:Page view definition for the article `Docker_(software)` on `en.wikipedia.org` under requester class `user`; OR (b) a question published on `stackoverflow` carrying the site's own tag `docker`.

Formal validity: **VALID**. Information value: **NEAR_TAUTOLOGICAL**. Verdict: **`FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK`**.

### `P-B1` — class B, cross-platform existence

> Subject-related activity attributed to `docker` occurred on more than one independently operated platform during March 2024.

Formal validity: **NOT_ORDINARY_CORROBORATION**. Information value: **HIGHER_THAN_P_A1**. Verdict: **`JOINT_CONJUNCTION_NOT_CORROBORATION`**.

No single apparatus entails it. Wikimedia alone establishes one platform; Stack Exchange alone establishes one platform; the claim that there were TWO is entailed only by their conjunction. That is a JOINT proposition, and putting two Evidence rows into two support groups on it would report a conjunction as independent corroboration -- the exact shape section 4 rejects.

### `P-C1` — class C, latent behavioural construct

> Developers showed interest in Docker during March 2024.

Formal validity: **NOT_OBSERVED**. Information value: **WOULD_BE_HIGH**. Verdict: **`LATENT_INFERENCE_REQUIRED`**.

Requires pageviews -> interest and questions -> pain, both named in section 6's forbidden list. No reviewed inference contract exists. This is the proposition a reader most wants and it is not OBSERVED. Not implemented, and not proposed.

### `P-A2` — class A, direct observable class abstraction, strengthened

> Public platform activity attributed to `docker` was higher in one bounded sub-period of March 2024 than in another.

Formal validity: **INVALID**. Information value: **WOULD_BE_USEFUL**. Verdict: **`SHARED_SUBJECT_NOT_SAME_PROPOSITION`**.

This is the first strengthening that would carry information, and it fails immediately on two counts. It requires comparing 88 questions against N content requests, which section 11 forbids -- they are not two measurements of one numeric quantity and may not be averaged, normalised or scaled into a shared pseudo-metric. And it requires exactly-aligned bounded sub-periods, which the measured grains do not provide. Recorded because the failure of the FIRST informative strengthening is the substance of the primary outcome.

## §8 — Entailment table

| candidate | A alone | B alone | both jointly | latent | source identity removed | standard corroboration |
| --- | --- | --- | --- | --- | --- | --- |
| `P-A1` | YES | YES | NO | NO | NO_BUT_RELOCATED | FORMALLY_YES |
| `P-B1` | NO | NO | YES | NO | NO | NO |
| `P-C1` | NO | NO | NO | YES | NO | NO |
| `P-A2` | NO | NO | YES | NO | NO | NO |

**On `P-A1` and source identity.** This is the finding worth reading twice. The proposition's SUBJECT is genuinely source-independent -- 'at least one public platform' names no publisher. But its PREDICATE is not: the only definition of the qualifying event class enumerates the two publishers' own mechanisms. So source attribution is not removed, it is relocated from the subject of the sentence into the definition of its predicate, where it is harder to see. A proposition that looks source-independent and is not is worse than one that is openly attributed.

## §16 — The Wikimedia + Stack Exchange diagnostic

Wikimedia `Docker_(software)` on `en.wikipedia.org` under requester class `user`; Stack Exchange tag `docker` on `stackoverflow`; canonical subject `docker`.

| # | question | answer |
| ---: | --- | --- |
| 1 | Is 'public platform activity' explicitly operationalised? | **ONLY_AS_A_DISJUNCTION** |
| 2 | Does a page request qualify by definition? | **YES_BY_STIPULATION** |
| 3 | Does a published tagged question qualify by definition? | **YES_BY_STIPULATION** |
| 4 | Does either one alone entail the entire claim? | **YES** |
| 5 | Is the period exactly aligned? | **NO** |
| 6 | Is subject identity exact? | **YES** |
| 7 | Does the abstraction silently imply humans? | **NO** |
| 8 | Does it silently imply attention? | **NO** |
| 9 | Does it silently imply problem severity? | **NO** |
| 10 | Does it silently imply demand? | **NO** |

1. It can be given an explicit, checkable definition, and the only one that admits both members enumerates both members. A class whose definition is the list of the things it was built to contain is explicit and circular at once.
2. Only because clause (a) stipulates it.
3. Only because clause (b) stipulates it.
4. Under the disjunctive definition, each alone entails the existential.
5. Measured: Stack Exchange 2024-03-01T08:06:03Z .. 2024-03-05T04:17:20Z against whole UTC day buckets. Both are contained in March 2024, and containment is not alignment. The proposition survives this only because it is weak enough not to need alignment.
6. Reviewed registry, exact equality of rendered identifier keys, both sides carrying Evidence.
7. Held out deliberately. `user` is Wikimedia's own class name for traffic not identified as automated by ua-parser plus custom regex, and it does not mean human, person, reader or customer. A Stack Exchange question is not one unique person: author identity was never acquired, so distinct askers cannot be counted.
8. The wording is 'recorded an event of a defined class', not 'attended to'.

Questions 7 to 10 are all NO and 1 to 6 are defensible only in the qualified senses recorded above. So it IS a formal OBSERVED convergence candidate, and section 5's separate test is what decides it: FORMAL_CONVERGENCE_VALIDITY is VALID and PROPOSITION_INFORMATION_VALUE is NEAR_TAUTOLOGICAL.

## §12 / §13 — Independence

|  | apparatus A | apparatus B |
| --- | --- | --- |
| publisher | Wikimedia Foundation | Stack Exchange, Inc. |
| event generation | HTTP requests arriving at Wikimedia servers, counted under the operator's own pageview definition -- a conjunction of HTTP status, host and header conditions with an enumerated exclusion list. | Questions composed and published by people on stackoverflow.com. |
| collection pipeline | Wikimedia Analytics Pageviews API, first-party, documented. | Stack Exchange API questions endpoint, first-party. |
| classification | Requester class assigned by ua-parser plus additional custom regex, which the operator documents as heuristic pattern matching. | Tags assigned by askers and community curators from the site's own vocabulary. |

**State: `UNKNOWN`.** Section 13 permits KNOWN_INDEPENDENT only where documentary evidence establishes genuinely distinct measurement lineages, and forbids converting 'no dependency found' into independence. This deployment holds first-party documentation of Wikimedia's lineage (Research:Page view) and holds NONE for Stack Exchange: the publisher's methodology pages are unreachable because the site's robots policy blocks this environment's fetcher. So one lineage is documented and one is not, and half a documentary basis does not establish a distinction between two.

**Not refuted, and the difference matters.** This is materially different from Mission 1.46. There, independence was REFUTED by a documented common upstream -- FRED republishes the World Bank series by its own declaration, and the World Bank names Eurostat among its own sources -- which closed the direction permanently. Here nothing suggests a shared upstream and none is documented; what is missing is the affirmative documentation of one side. An unknown can be resolved by a retrievable document. A documented common producer cannot.

*No request was made to Stack Exchange documentation in this mission. Its robots policy blocks the crawler, and no retry, header variation, mirror, cached copy or third-party summary is permitted to stand in for a first-party document.*

## §14 — Complementarity versus corroboration

- **Corroborating:** Two Evidence items each bear on the same proposition.
- **Complementary:** Two Evidence items bear on different propositions or dimensions that together make an Opportunity hypothesis more informative.

Wikimedia dimensions: `AUDIENCE_OR_USAGE`, `TREND_OR_CHANGE`. Stack Exchange dimensions: `PROBLEM_OR_NEED`. Overlap: **none**.

**The codebase recorded this first.** packages/opportunity-engine/python/sros_opportunity/mapping.py, community_question_volume rationale: PROBLEM_OR_NEED is 'a genuinely different question from the one AUDIENCE_OR_USAGE answers: that one says something attended to a subject, this one says somebody said they were stuck on it, and neither implies the other.' Written before this mission and not for it.

The Evidence rows themselves do NOT record the distinction: observation_category is UNCATEGORISED on all 57 rows in the corpus, including all 14 Docker rows. The complementarity lives in the Opportunity engine's signal-type-to-dimension map, not on the Evidence row. So no existing category was coerced and none was invented, because the field that would have been coerced carries no distinction to coerce.

AUDIENCE_OR_USAGE and PROBLEM_OR_NEED were NOT collapsed into a shared category. Section 20 forbids it and nothing here needed it.

**Consequence.** These two Evidence items may both be valuable to the SAME Opportunity. That does not mean they belong on the SAME Claim. Opportunity-level evidence diversity is not Claim-level corroboration, and collapsing the first into the second is the error this mission exists to avoid.

## §18 / §19 — Can the convergence contract express this?

**CAN_CURRENT_CONVERGENCE_CONTRACT_EXPRESS_CROSS_APPARATUS_PROPOSITION? — NO.**

- `PropositionConvergenceContract.__post_init__` (packages/claim-model/python/sros_claim_model/convergence.py:138): raises ValueError unless 'source_id' is in identity_fields.
  > `source_id` is always identity for an OBSERVED proposition
  Two publishers cannot share one proposition key. A second source forms its own Claim.
- `SourceBoundary` (packages/claim-model/python/sros_claim_model/convergence.py:57): exactly one member, SAME_SOURCE_AND_RESOURCE.
  > A cross-source value is deliberately absent rather than present-and-unused. An enum member nobody may pass is an invitation.
  There is no value a caller could pass to widen the boundary, so the refusal is structural rather than a policy check.

*Deliberate, not an oversight:* The docstring states the reasoning: an OBSERVED claim asserts what a named source reported, so 'Wikimedia counted X' and 'TED reported Z' are different propositions with different falsifiers, and rendering them into similar English does not make them one.

*No contract was written, no enum member was added and no constructor guard was relaxed. Section 18 says do not implement one yet, and section 9 forbids removing source_id from proposition identity merely to let two sources merge.*

### The identity/witness exercise, and why it fails

- identity: `canonical_subject_id`, `event_class_definition_id`, `period_bound`, `claim_type`
- witness: `source_id`, `resource_id`, `source_native_subject_id`, `source_platform`, `period_label_from`, `period_label_to`, `audience_class`
- disjoint: **True**, complete: **False**

`audience_class` is REQUIRED on the content_request_count kind precisely so that one item over one period cannot carry two different counts under one name (Mission 1.19). It has no counterpart on the Stack Exchange side, so it can only be a witness fact here -- which means the identity set cannot say which requester class the proposition is about, while the Wikimedia apparatus cannot state a count without one. A fact that is load-bearing for one witness and absent for the other cannot be demoted to witness without the proposition losing the ability to say what it is about.

`event_class_definition_id` is the disjunction. It is an identity fact that names both publishers' mechanisms, so moving `source_id` to witness does not make the proposition source-independent -- it moves the attribution one level down. No fact disappears, and one becomes much harder to see.

**Verdict: REJECTED under section 19. The merge is only available by dropping a fact that is defensible for neither apparatus.**

## §21 — Reliability readiness

| apparatus | resolves | value | origin |
| --- | --- | ---: | --- |
| `wikimedia-pageviews | platform_counted_content_request_change` | RESOLVED | 0.65 | HUMAN_REVIEW |
| `wikimedia-pageviews | platform_counted_content_request_change_witnessed` | RESOLVED | 0.6 | HUMAN_REVIEW |
| `stack-exchange | community_site_published_questions_carrying_tag` | NO_APPLICABLE_ASSESSMENT | — | — |
| `stack-exchange | community_site_questions_without_accepted_answer` | NO_APPLICABLE_ASSESSMENT | — | — |
| `ted-eu | source_reported_procurement_value_contrast` | RESOLVED | 0.5 | HUMAN_REVIEW |
| `ted-eu | source_published_classification_value_contrast_witnessed` | RESOLVED | 0.55 | HUMAN_REVIEW |
| `world-bank | source_reported_metric_period_change` | NO_APPLICABLE_ASSESSMENT | — | — |
| `gdelt | source_reported_term_frequency_change` | NO_APPLICABLE_ASSESSMENT | — | — |
| `gdelt | source_reported_term_frequency_contrast` | NO_APPLICABLE_ASSESSMENT | — | — |

A cross-apparatus proposition would carry a NEW proposition_kind, so it would be a NEW five-part reliability scope on BOTH sides. Neither Wikimedia's 0.65 nor its 0.6 transfers, and no value is inherited by proposition similarity.

**The Stack Exchange side needs exactly the judgement the operator has already declined. In Mission 1.36.1 the operator answered NO on BOTH Stack Exchange scopes and the refusal was recorded as prose rather than as a value, because a refusal recorded as data would be a number the next reader would use. The reason was that the available documentation is insufficient -- the same robots-blocked documentation that leaves independence UNKNOWN here.**

*Why this matters:* The cross-apparatus route does not merely need new reliability reviews. It needs a Stack Exchange reliability review whose blocker a mission cannot clear, because the blocker is a publisher's access policy and bypassing it is out of bounds.

## §22 — Calibration information value

- `STRUCTURALLY_IDENTIFYING`: **YES** — Two KNOWN_INDEPENDENT items on one Claim form two groups under _group_key, and saturation over two groups is 1 - (1 - g_A)(1 - g_B), which can exceed max(g_A, g_B). That would be the first case in this repository where the full aggregator differs from the B-2 pass-through baseline.
- `SEMANTICALLY_USEFUL`: **NO** — The proposition that achieves it is 'at least one platform recorded something about Docker in March 2024', in a corpus assembled by going looking for Docker data. A calibration case asks a reviewer which of two evidence sets is better supported. Asking that about a near-tautology measures the reviewer's patience rather than the aggregator.

Section 22 requires both, and reporting only the first would present a structural exercise as an epistemic gain. A proposition can identify a mechanism and teach nothing about evidence strength, and this one does.

## §25 — Decision matrix

| candidate | subject match | time match | each evidence supports full proposition | latent inference required | complementary only | provenance independence | convergence contract fit | reliability readiness | calibration information value | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P-A1` | YES | CONTAINMENT_ONLY | YES | NO | NO_AT_THIS_PROPOSITION_STRENGTH | UNKNOWN | NO | BOTH_SIDES_WOULD_NEED_NEW_REVIEW | STRUCTURALLY_IDENTIFYING_NOT_SEMANTICALLY_USEFUL | FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK |
| `P-A2` | YES | NO | NO | NO | YES | NOT_REACHED | NOT_REACHED | NOT_REACHED | NOT_REACHED | SHARED_SUBJECT_NOT_SAME_PROPOSITION |
| `P-B1` | YES | CONTAINMENT_ONLY | NO | NO | NO_IT_IS_CONJUNCTIVE | NOT_REACHED | NOT_REACHED | NOT_REACHED | NOT_REACHED | JOINT_CONJUNCTION_NOT_CORROBORATION |
| `P-C1` | YES | CONTAINMENT_ONLY | NO | YES | NOT_REACHED | NOT_REACHED | NOT_REACHED | NOT_REACHED | NOT_REACHED | CROSS_APPARATUS_CONVERGENCE_REQUIRES_INFERRED_BRIDGE |

## §26 — The eight gates

Evaluated for `P-A1`, the only candidate that reaches them.

| # | gate | result | why |
| ---: | --- | --- | --- |
| 1 | exact subject identity | **PASS** | Reviewed registry, exact equality, Evidence on both sides (12 and 2). |
| 2 | compatible period | **PASS_BY_WEAKNESS** | Both windows are contained in March 2024. They are not aligned, and the proposition is weak enough not to need alignment. For any proposition that needs alignment this gate is a hard FAIL. |
| 3 | each source alone supports full same proposition | **PASS** | Under the disjunctive event-class definition. |
| 4 | no latent inference | **PASS** | Each side is a directly observed publication or counting event. No promotion to interest, demand, adoption, popularity, pain or willingness to pay. |
| 5 | no complementary-only structure | **PASS_AT_THIS_STRENGTH_ONLY** | At the existential floor both bear on one proposition. One step above it they split into AUDIENCE_OR_USAGE and PROBLEM_OR_NEED and become complementary. The gate passes only where the proposition has discarded the distinction. |
| 6 | established independence | **FAIL** | UNKNOWN. Stack Exchange's measurement lineage is not documented in the held basis, and its publisher documentation is robots-blocked. |
| 7 | convergence contract representable | **FAIL** | Two structural refusals in code: source_id mandatory in identity, and SourceBoundary has one member. |
| 8 | proposition is not merely a misleading pseudo-market construct | **FAIL** | 'Public platform activity related to Docker was observed during March 2024' reads as though it says something about Docker's standing. It says that two platforms published something about Docker in a month chosen because this corpus holds Docker data. That is the near-tautological abstraction section 5 warns against presenting as market corroboration. |

**5 pass, 3 fail. All eight: False.**

## §24 — Hypothetical aggregation, symbolic and not persisted

Fixture: one Claim, two Evidence items, both KNOWN_INDEPENDENT. Persisted: **False**.

- group A: g_A = r_A, key `(INDEPENDENT, evidence_id)`
- group B: g_B = r_B, key `(INDEPENDENT, evidence_id)`
- saturation: `S = 1 - (1 - g_A)(1 - g_B)`
- baseline B-2: `max(g_A, g_B)`

S - max(g_A, g_B) = min(g_A, g_B) * (1 - max(g_A, g_B)), which is strictly positive whenever both g are in (0, 1). So the full aggregator differs from the B-2 pass-through baseline for ANY pair of non-zero independent strengths.

*q is left unresolved on both sides. r_A and r_B are symbolic and no number is supplied, because neither apparatus has a reviewed reliability for a cross-apparatus proposition_kind.*

**What this shows.** The mechanism is ready and has been ready since Mission 1.43 proved it on fixtures. What is missing has never been the arithmetic. It is a real pair entitled to inhabit the shape, and this mission establishes that the held corpus does not contain one.

**What it does not show.** That the shape is worth reaching. The same fixture would differ from B-2 for a proposition of no value, which is exactly the P-A1 case, and section 23 forbids designing a proposition to make the number move.

## Counters, budget and state

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
| scores | table absent | table absent |
| registered_sources | 29 | 29 |
| evidence_with_stored_reliability | 0 | 0 |

`RESEARCH_DATA_REQUESTS` **0**, `APPARATUS_DOCUMENTATION_REQUESTS` **0**, `GOVERNANCE_DOCUMENT_REQUESTS` **0**.

Zero requests of every kind. Every apparatus fact used here was already held: Wikimedia's Research:Page view definition from Mission 1.19, the Stack Exchange documentation gap recorded in Mission 1.36's packet, and the provenance statements in the source catalog. No Stack Exchange documentation request was attempted, because its robots policy blocks this environment's fetcher and no bypass, header variation, mirror or third-party summary may stand in for a first-party document.

Model calls **0**, 0.00 USD, embeddings **0**, Problem-Family **PARKED**.

## Next mission

Section 38 is explicit for outcome D: do not implement it merely to make the aggregator produce a different number. Look for a better proposition family or a contradiction-capable route.

**The structural observation.** The two routes to making the aggregator differ from B-2 are ESTABLISHED INDEPENDENCE and CONTRADICTION (Mission 1.43). This mission found that the propositions easiest to converge are existentials, and an existential is MONOTONE: a counterexample does not falsify it, so an existential can never produce a contradiction case. The propositions that CAN be contradicted are point or universal claims, and those are exactly the ones only one apparatus supports. So the same weakness that makes cross-apparatus convergence available makes contradiction unavailable, and both roads out of the B-2 identity are blocked by one property of this corpus.

**Recommended.** A mission that asks what TYPE of measurement apparatus would be needed, rather than which held pair can be made to fit. Specifically: an apparatus observing the same phenomenon as one already held, with a documented measurement lineage, capable of producing a FALSIFIABLE point claim rather than an existential -- because that is the only shape that can yield either an independent second group or a contradiction.

**Not recommended.** Adding sources at random; widening the convergence contract; implementing P-A1; acquiring more Wikimedia or Stack Exchange data. None of them touches the finding.

*Mission 1.48 was not started. Section 38 says do not start automatically, and the outcome is D rather than A, so the Mission 1.48 described there is not the right next mission anyway.*

## §34 — Deployment-local human confirmations

**`DEPLOYMENT_LOCAL_HUMAN_CONFIRMATIONS_REQUIRE_MIGRATION_CHECKLIST`**

TED's local review v3 acceptance is a HUMAN_CONFIRMATION verification recorded in this deployment's database. It is not portable through git: a clone of this repository does not carry it, and TED would be INELIGIBLE under local-private-research-v1 in a fresh deployment until a named operator recorded it again.

No replay mechanism was created and none is proposed here. record_ted_operator_acceptance.py still refuses against v3, and its own guard says the acceptance has to be made again by a person rather than replayed.

A deployment or migration checklist is required whenever this system is stood up elsewhere. That is a future deployment concern and not a Mission 1.47 repair.

