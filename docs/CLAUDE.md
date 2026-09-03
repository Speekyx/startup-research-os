# CLAUDE.md — Startup Research OS

Version: 1.62
Last amended: 2026-09-03 (Sprint 1 / Mission 1.34)

## Boot Sequence

Before performing any task, execute this reading order.

1. PROJECT_MANIFEST.md
2. docs/CLAUDE.md
3. docs/domain/opportunity-ontology-v2.2.md
4. docs/domain/scoring-framework-v1.1.md
5. docs/domain/evidence-confidence-framework-v1.md
6. docs/ai/llm-reasoning-rules.md
7. docs/data/data-principles.md
8. docs/data/data-retention-policy-v1.md
9. docs/data/source-registry-v1.md
10. docs/data/acquisition-authorization-v1.md
11. docs/data/world-bank-collector-v1.md
12. docs/data/normalized-record-v1.md
13. docs/data/world-bank-normalizer-v1.md
14. docs/domain/evidence-aggregation-framework-v1.md
15. docs/domain/claim-model-v1.md
16. docs/ai/evaluation-framework-v1.md
17. docs/data/signal-contract-v1.md
18. docs/data/signal-derivation-runtime-v1.md
19. docs/data/claim-evidence-interpretation-contract-v1.md
20. docs/data/claim-interpretation-runtime-v1.md
21. docs/data/evidence-reliability-contract-v1.md
22. Relevant ADRs
23. Task-specific specifications

These documents are the authoritative source of truth.

**`opportunity-ontology-v1.md`, `opportunity-ontology-v1.1.md` and
`scoring-framework-v1.md` are superseded.** They remain in the repository as
historical records. Do not use them as the basis for implementation. See
`PROJECT_MANIFEST.md` §Superseded specifications.

Ontology V2 keeps V1.1's numbering for §1–§10, so an existing reference to
`opportunity-ontology-v1.1.md §N` with `N ≤ 10` resolves to the same rule in V2.

**V2.2 inherits V2.1 in full and amends one sentence** (§17.3): a Claim belongs
to *at most one* Opportunity, and may belong to none. Every other reference to
V2.1 resolves unchanged in V2.2.

## Version history

| Version | Date | Change |
|---------|------|--------|
| 1.62 | 2026-09-03 | **MULTI_SCOPE_ARCHITECTURE_READY_SCOPE_RELATIONS_UNPOPULATED: the engine can now say WHAT LEVEL a row observes, and there are no edges.** `SubjectScopeType` = PRODUCT | CATEGORY | MARKET | GEOGRAPHY, each with a `means` and a `never_means`, and **MARKET's example is literally 'none'** because no registered source observes one. **The assumption broken**: `build_packet` unioned dimensions with NO SCOPE TERM, so membership WAS the claim of aboutness -- found in seven places and listed in the report. **The relation registry ships EMPTY and that is the result**: Mission 1.33 refused to say which category contains Docker and §33 forbids inventing one, so the capability exists holding zero edges and NO Evidence row can currently be contextual. **Real demonstration on 28 rows**: Docker resolves PRODUCT (8 rows, DIRECT), TED resolves CATEGORY on the publisher's own authority (CPV is a classification by its own name), and offering TED to Docker is REFUSED `NO_PERMITTED_RELATION` -- **the refusal is the demonstration**. 25 of 28 scopes resolved, **3 UNDETERMINED** (GDELT terms; a word names no level) and nothing mass-labelled. **NO MIGRATION**: scope is DERIVED at build time from identifiers already held, because persisting a derivation is what source-registry §3 refuses for eligibility. **Compatibility PROVEN not asserted**: regenerating the preparation artifact changed EXACTLY ONE FIELD, the registry version. **No union of direct and contextual dimensions exists on the packet** -- a test enumerates every public attribute -- because that union is the sentence *Docker supports MARKET_ACTIVITY*. No transitivity, no MODEL_INFERRED origin, WTP still unreachable, revision 1 and its 7 links untouched, all 13 counters verified unchanged |
| 1.61 | 2026-09-03 | **COMMERCIAL_SOURCE_GRAIN_MISMATCH: the sources that can name Docker carry no commercial semantics, and the sources that carry commercial semantics cannot name Docker.** A desk review of all 29 registered sources. **5 can identify Docker at grain** -- `github`, `product-hunt`, `reddit`, `stack-exchange`, `wikimedia-pageviews` -- 7 reach it only as a MENTION and 17 not at all. **3 could support a missing commercial dimension and all 3 are blocked.** 0 acquisitions, 0 model calls, **every one of the thirteen counters verified unchanged against the live database**. **21 of 29 have no `local-private-research-v1` review**, so ADR-027 refuses them whatever their terms say -- and that is NOT twenty-one opportunities: GitHub's and Product Hunt's findings are about the PURPOSE of the use, which the local profile does not change, because **local deployment never implies non-commercial use**. GitHub's AUP section 7 is an allowlist applying *regardless of whether the information was scraped, collected through our API, or obtained otherwise*, permitting research use **only if publications are open access**; Product Hunt's docs say twice that the API *must not be used for commercial purposes*. **GitHub has the best grain in the portfolio and the strongest unclaimed dimension (COMPETITIVE_SUPPLY), and is NOT_RECOMMENDED.** **No source supports SOLUTION_GAP and none supports WILLINGNESS_TO_PAY at any grain** -- the taxonomy's own never_means already refuses a listed price, a budget line and a contract total. **THE BINDING CONSTRAINT IS ARCHITECTURAL**: `CanonicalSubject` has no scope field and a packet holds one subject, so SROS models GEOGRAPHIC scope on an Opportunity and no SUBJECT scope at all -- while MARKET_ACTIVITY and ECONOMIC_VALUE already ask about *the bounded scope observed*. TED is authorized, collected, normalized, extracted and carries three commercial dimensions, and its subject key is `ted-eu:CPV-division:90`. Next: **Multi-Scope Opportunity Evidence Architecture V1**, before any acquisition |
| 1.60 | 2026-09-03 | **COMMERCIAL_EVIDENCE_CREATED_NO_OPPORTUNITY_DIMENSION: a real measurement that maps to nothing, on purpose.** 88 held Docker questions, **34 with an accepted answer and 54 without** -- 38 answered but unaccepted, 16 with zero answers, **0 missing the flag** -- and the Signal maps to `frozenset()`. **The assessment was FROZEN BEFORE the Signal existed**, which is the whole of §0: a dimension chosen after seeing that the packet needed one is a rationalisation. `SOLUTION_GAP` is settled by its own `never_means` -- *that absence of evidence of a solution is evidence of its absence* -- and `SOLUTION_DISSATISFACTION` by the fact that **the asker is not evaluating a product**. **Acceptance is ONE PERSON'S ACTION**: only the asker may accept, so `false` reports a non-action by one participant, and an asker who solved it elsewhere or never returned leaves it false whatever answers arrived. **The 16 zero-answer questions look like the sharpest possible gap evidence and isolating them does not rescue the inference**, it makes the same inference over a smaller set. **The state is OBSERVED LATE**: the questions carry creation instants and the flag is whatever it was at collection, so the claim says *at the source state observed* and never *during*. **A claim shaped like a numerator invites a rate**: revision 1 read *Of the questions ... 54 had no accepted answer* and named no denominator, so `1.4.1` asserts a SET; revision 1 is preserved. **Docker packet 7 -> 8 rows with counting dimensions UNCHANGED at 2** -- a zero-dimension row adds size and never diversity -- still HYPOTHESIS_FORMABLE, still AVAILABLE, independence UNKNOWN for 8 of 8 because it is a **second measurement over the same corpus**. **Two defects fixed**: an interpreter version bump re-INSERTED Evidence because the idempotency key embeds it, and the new row formed its own tenth packet because `subject_key` knew one signal type. RawRecords and NormalizedRecords unchanged at 148, 0 model calls, no Opportunity revision, problem-family still PARKED |
| 1.59 | 2026-09-03 | **FIRST_OPPORTUNITY_HYPOTHESIS_CREATED. SROS holds its first Opportunity.** Same packet, **byte-identical prompt hash**, corrected audit: one call, 0 retries, 0.0392 USD, decision FORM_HYPOTHESIS, every clause of the frozen gate passed. Opportunities 0 -> **1**, revisions 0 -> **1**, evidence links 0 -> **7**, and RawRecords, NormalizedRecords, Signals, Claims, ClaimRevisions, Evidence, ReliabilityAssessments, Embeddings and Scores ALL UNCHANGED. **Mission 1.31 is untouched** and keeps its rejection under audit@1.0.0. **§1's five required cases found that guard@1.1.0 handled four**: a denial whose marker FOLLOWS its term -- *competitors ARE NOT established* -- was still flagged, and 1.2.0 adds that one grammatical form, cancelled by an intervening comma so *buyers would pay, which is not established* still fails. Checking them also exposed an off-by-one in `_phrase_position` that had misaligned every term not at the start of a sentence. **The two runs agree on every structural judgement** -- same actor refusal, same 12 unsupported dimensions, same 7 citations, both asserting no commercial claim -- so what changed was the audit and not the answer. `market_scope` is GLOBAL because the column is NOT NULL and Ontology V2 §4 defines GLOBAL as the ABSENCE of a restriction, recorded as a limitation on the row. Four TED tests repaired: a global Opportunity count is now deployment state |
| 1.58 | 2026-09-02 | **The first real Opportunity synthesis ran, and my own gate refused a good answer.** `OPPORTUNITY_SYNTHESIS_OUTPUT_REJECTED`: one call, 0.0383 USD, model returned FORM_HYPOTHESIS with a careful bounded hypothesis, and the frozen gate refused it on ONE clause -- *\"No statement in the packet establishes ... whether anyone would pay, whether competitors already serve this space\"* -- which is an ENUMERATION OF ABSENCES and exactly what §6 required. **A token guard cannot see negation**, so it read a denial as an assertion (testing-strategy §67, the §23 failure in a new place). **The verdict was KEPT and the guard fixed for next time**: §12 forbids weakening a gate after seeing the answer, and this was called a defect only because it rejected an output I judged sound. **0 Opportunities persisted, every counter unchanged.** The model did the hard part well: actor UNKNOWN_NOT_SUPPORTED rather than an invented persona, intervention as a CLASS, pageviews restated as FLUCTUATION rather than growth, `commercial_claims_supported` EMPTY, and it independently said the 88 questions are *a count of questions, not of people* and *not evidence they share a single problem* -- reaching the parked boundary unprompted. Two earlier attempts were abandoned because MY output cap (1500) was smaller than the schema I asked for could serialise |
| 1.57 | 2026-09-02 | **TARGETED_EVIDENCE_COMPLETION_SUCCESS: the first FORMABLE packet, and NOTHING was acquired to get it.** The `docker` packet is HYPOTHESIS_FORMABLE and AVAILABLE_FOR_EXTERNAL_SYNTHESIS on 7 rows across two source families with two counting dimensions. Counters 26 -> 27 for Signals, Claims, ClaimRevisions and Evidence; RawRecords and NormalizedRecords UNCHANGED at 148. **The minimum needed was zero**: Mission 1.20's `tagged=docker` retrieval provably did not truncate -- one page of size 100 returned 89, and a short page means the set was exhausted -- so a complete count already existed. **A truncated count is not merely imprecise, it is ANTI-INFORMATIVE**: capped at 30 it would report the bound and read as LARGER than a complete 88, which is why the extractor refuses instead of qualifying, and why Kubernetes was not acquired. **89 returned, 88 counted**: one question came back from a `tagged=docker` query carrying no `docker` tag, so what the query asked and what the site says are different facts and the site's answer is the one a claim can rest on. ADR-034 adds COMMUNITY_QUESTION_VOLUME: **a request is what a READER makes of a server, a question is what a PERSON publishes about being stuck**, and widening CONTENT_REQUEST_VOLUME would have cost the FAMILY its meaning. New dimension PROBLEM_OR_NEED, with RECURRENCE_OR_FREQUENCY deliberately refused because it needs the PARKED relation. A canonical subject registry joins two vocabularies by EXACT equality with a stated basis. Sufficiency rule unchanged, reliability unchanged, independence still UNKNOWN, 0 model calls |
| 1.56 | 2026-09-02 | **OPPORTUNITY_SYNTHESIS_EGRESS_PARTIALLY_READY: three decisions recorded, and the fourth deliberately not.** `wikimedia-pageviews` **PERMITTED** on CC0 1.0, which waives database rights BY NAME and leaves no act for a licence to restrict -- and no attribution condition was written, because CC0 creates none. `world-bank` and `gdelt` **PERMITTED_WITH_CONDITIONS**. **8 of 9 packets are now egress-authorized and 0 became formable**, which is the design working: permission to send is not evidence. **CC BY 4.0 grants 'reproduce AND Share' as two acts**, so reproduction stands alone and a contracted processor is not 'the public' -- the transmission allowlist is CC-BY-4.0 ONLY, TIGHTER than acquisition's, because ODbL's Publicly Use is unanswered. **GDELT's grant runs to datasets it RELEASES**, so ngram aggregates are covered and third-party article text is a PROHIBITED representation; its citation obligation attaches to 'any use' and is live where CC BY's is not. **TED was assessed UNCLEAR and NOT recorded**: appending a review orphans the operator's HUMAN_CONFIRMATION acceptance, which no verifier may re-satisfy, so TED would have stopped being acquirable as a side effect of assessing egress -- §0 forbids exactly that. NOT_ASSESSED and UNCLEAR both refuse, so nothing operational was traded away. **A source whose approval rests on a human decision cannot be cheaply amended.** New refusal code UNRESOLVED, because an operator can close an open question and cannot argue with a decision. 0 model calls, 0.00 USD, counters unchanged, authorizable pairs 8 before and 8 after |
| 1.55 | 2026-09-02 | **OUTCOME B: the Opportunity Engine works and the current evidence cannot support a hypothesis -- blocked TWICE, for unrelated reasons.** 26 Evidence rows inspected, **26 ELIGIBLE_CONTEXT and 0 ELIGIBLE_SCORING**, 9 packets grouped by source-native subject, **0 formable, 0 opportunities, 0 model calls, 0.00 USD**, counters unchanged. **The failure is symmetric and that is the finding**: the one packet with commercial dimensions (TED, CPV division 90) has ONE row, and the packets with six rows (Wikimedia Docker / Podman / Kubernetes) have ONE dimension. Evidence is deep where it is narrow and broad where it is shallow. **The second blocker is independent of the evidence**: `external_model_transmission` is NOT_ASSESSED for all four sources that HAVE Evidence and PERMITTED only for `stack-exchange`, which has none -- **the one source cleared to leave the deployment is the one with nothing to send**. Three signal types map to NO dimension on purpose; a GDELT term count measures what media PUBLISHED, which is producer behaviour and not audience behaviour. **TREND_OR_CHANGE cannot satisfy a diversity requirement** because every Signal here is a derivation and so every row carries change. Docker, Podman and Kubernetes stay three packets: merging them deterministically would not make it deterministic, it would make it unargued. Migration 0029 makes the hypothesis/validated distinction a CHECK constraint. No score, rank or weight exists |
| 1.54 | 2026-09-02 | **EXPLORATORY_V2_NOT_PROMISING, and the classifier is PARKED.** Three V2 variants, one selected by a frozen rule, frozen, run once on the Mission 1.26 holdout: **0 provisional true SAME against 4 references** where the frozen criterion required 2. 88 evaluations, 1.53 USD, 0 retries, counters unchanged. **V1 was never failing to SEE the abstraction** -- its own rationale states the shared goal and then rejects it. **The most informative artifact was an empty field**: V2 required the model to name an abstraction covering both questions, and `shared_problem_if_any` came back empty 39 times in 40. More scaffolding made it MORE conservative. **A selection rule must defeat both collapses**, so the frozen rule demands a true positive and caps the SAME share. **A ceiling you might exceed is bounded, not argued away** -- output capped at 1200 tokens to make 3.00 USD real. **A split disjoint by PAIR is not disjoint by OBSERVATION**, so the brief's own suggested prompt example was a holdout leak and was refused. Production stays NOT_AUTHORISED |
| 1.53 | 2026-09-02 | **REFERENCE_SET_INSUFFICIENT, and the gate was allowed to fail.** The 40 labels came back **AI_ASSISTED_PROVISIONAL**, not human -- the operator chose to proceed with them rather than spend another labelling mission, which is a real decision recorded at document level and changes nothing about what they are. Development holds **2** SAME_FAMILY against a preregistered 4 (holdout passes at 4). **Two results reported apart**: the composition gate fails, and the human reference requirement is separately NOT_ESTABLISHED -- one verdict would let either hide the other. Nothing moved: no pair changed split, no label revised, no threshold lowered, no re-sampling. **A loader asked for HUMAN_OPERATOR refuses these files**, so the distinction is structural rather than prose. Mission 1.25's genuine human holdout is NOT merged in to help the threshold. 0 model calls, counters unchanged; production stays NOT_AUTHORISED |
| 1.52 | 2026-09-02 | **A dataset mission, and the reason it came before a V2 classifier.** Mission 1.25's ten human-scored pairs with two positives rejected a trivial classifier and cannot build one; and when the operator reviewed them, five labels changed with three moving TOWARD the model, so *V1 is far too conservative* was half an artifact of an AI-assisted reference. **40 new pairs, none shared with 1.25**, deterministic stratified sampling over five feature bands, **24/16 split frozen before any label**. **No model output entered the selection** -- a dataset chosen by a classifier's errors can only ever measure that classifier -- asserted by parsing the sampler's code with docstrings excluded, because it says *not a prediction* precisely because it reads none. **Strata are sampling mechanisms, never expected labels.** The sample is ENRICHED and may never state a prevalence. **Holdout isolation is structural**: separate files, so the development loader cannot reach a holdout label. `DATASET_PREPARATION_COMPLETE` is not a model evaluation, and 1.25's MODEL_EVALUATION_FAILED is untouched |
| 1.51 | 2026-09-02 | **The human operator reviewed the frozen holdout, and the criterion still fails -- but the reference was half the story.** Re-scored the SAME frozen predictions against HUMAN_OPERATOR labels: no model call, nothing frozen touched, the provisional scoring preserved as history. Every precondition now met against human ground truth -- 10 labelled, 2 human SAME, 0 false SAME -- and **0 true SAME**, so `MODEL_EVALUATION_FAILED` stands. **Zero false positives is still not a pass**, being what a constant-DIFFERENT classifier scores. **Five of ten labels changed and on three the human moved TOWARD the model**: the provisional reference had called two pairs a family the operator does not, and one decidable that the operator finds undecidable. Missed positives fall 4 -> 2. So *the model is far too conservative* was half an artifact of an AI-assisted reference -- a finding that generalises. **The full 20-pair set is MIXED provenance** and must never be reported as fully human |
| 1.50 | 2026-09-02 | **MODEL_EVALUATION_FAILED on a frozen criterion, and it is worth more than Mission 1.24's pass.** A SECOND relation -- `SAME_PROBLEM_FAMILY`, do two observations express substantially the same blocked goal -- **not a looser version of the exact one**, which stays intact and unweakened. The relation changed rather than a threshold: *would the fix transfer* needs the fix, and loosening it would have kept that requirement while answering more permissively. **The criterion was built so a constant classifier cannot pass** -- `min_true_same` demands a demonstrated positive in the scored split -- **and then it caught the real run**: 4 SAME_FAMILY references in the holdout, **zero found**, one SAME in twenty overall and that one the rubric's own quoted example. **Every disagreement is one-directional**, so either the rubric is too strict or the reference too generous, and this cannot separate them -- the rubric and its reference disagree about the rubric's own borderline example. **The rubric was NOT widened after seeing the results**; 1.24 kept a rule in the flattering direction and this keeps one in the costly one. Reference is AI_ASSISTED_PROVISIONAL, so what was measured is agreement between two assistants. 20 calls, 0.38 USD, no Signal, no Claim, no Evidence |
| 1.49 | 2026-09-02 | **Two corrections before Mission 1.25 proper, and the first is the most misleading thing this repository had said.** Mission 1.24's 40 reference labels were supplied `AI_ASSISTED_PROVISIONAL` by a different assistant, **not by a human**, and the claim was embedded in a filename, a section heading, two type names and a `reviewer` field naming a person who did not judge. `ReferenceOrigin` is now required and never defaulted; `human_ground_truth_established` is true only when EVERY label is human; the origin rides on the RESULT because a result is what gets quoted. **No history rewritten** -- every label, prediction and cost is unchanged, and 1.24 stays EVALUATION_INSUFFICIENT for the reason the correction does not touch. Second: **SROS does have Evidence** -- 26 rows from other source families -- so the gap is *no validated recurring-problem semantic evidence from Stack Exchange*, bounded to EXACT equivalence over one candidate set, and nothing establishes that problem-FAMILY evidence is unavailable |
| 1.48 | 2026-09-02 | **OUTCOME B: the first model-mediated inference ran, and produced no epistemic row.** 40 real labelled pairs through the Gateway on the approved route, 0.61 USD, **zero false SAME** -- and **zero SAME of any kind**, over a holdout containing no SAME label to test against, so a classifier hard-coded to answer DIFFERENT scores identically. Precision on SAME undefined, recall 0/1. **The predeclared criterion was wrong in a way only data could show**: V1 wanted a positive *anywhere in the reference set* and the only one fell in DEVELOPMENT; V2 wants it in the scored split and returns EVALUATION_INSUFFICIENT on the same run. V1 is KEPT, because rewriting a rule after the fact means it was never binding. **A structural guard decided the architecture**: validate_signals.py forbids a Gateway import anywhere in sros_nlp, so the classifier lives in its own package and the guard was left alone. Authorization is resolved BEFORE any source text is serialised, not before the socket. No confidence number is requested from the model at all. The three Mission 1.20 hard negatives were classified correctly and prove nothing -- the rubric quotes them, so they are in-sample by construction and pinned to development. **No production inference, no Signal, no INFERRED Claim, no Evidence**, and the blocker is a corpus that yielded one defensible SAME in 40 pairs |
| 1.47 | 2026-09-02 | **OUTCOME B: the inference execution boundary EXISTS, and it is closed on one named gate.** No model was called and no source content left this machine. ADR-033 separates three questions that were one or none: `model_processing` asks may a model READ, the new **`external_model_transmission`** asks may it LEAVE, and a **provider policy** asks what the processor DOES with what it receives -- decided on first-party contract text, so one route is APPROVED on a terms clause committing not to train on customer content and one is NOT_APPROVED because its **unpaid** route says it develops machine learning technologies from submitted input. The profile gained **`external_model_egress`**, the word Mission 1.22 found missing. **NOT_ASSESSED is a state, not a default that decides**: migration 0027 adds both columns nullable and writes no existing row, and 0028 writes only the two decisions actually made. **The activity is deliberately NOT one of rule 8's six** -- it gates ONE operation, so World Bank's collector never fails because nobody assessed egress for World Bank, and that is asserted over every source rather than assumed. Stack Exchange local review **v2 appended, v1 not rewritten**, PERMITTED_WITH_CONDITIONS on CC BY-SA §2, with conditions naming a PROPERTY and no vendor. **Appending v2 broke acquisition for the source** -- a compliance configuration is pinned to a review version -- and the repair was to PERFORM the re-check, provable because v2's `required_conditions` are byte-identical to v1's. Live gate: source PERMITTED, profile PERMITTED, provider APPROVED, configured **no** -> `PROVIDER_NOT_CONFIGURED`. Mission 1.22 may RESUME **after operator configuration**, and the blocker is finally one an operator can clear |
| 1.46 | 2026-09-02 | **OUTCOME A: the semantic-inference route is NOT AUTHORISED, and separately NOT CONFIGURED.** No model was called, no question text left this machine, no component was built. **The governance gate carries the structural finding**: the Stack Exchange review permits model INFERENCE and is silent on TRANSMISSION of licensed text to an external provider, and so is the profile -- `model_inference: true` says the ACTIVITY is in scope, `deployment: LOCAL` says where the SYSTEM runs, and **nothing says where inference RUNS**. No occurrence of *provider*, *third party*, *transmit* or *egress* in the profile, in any condition, or in any doc. **One field answering a question that is two** -- the Mission 1.15.4 shape again. The second gate is independent: every inference tier is `null`, every credential empty, and **no local inference provider exists**. A DESIGN was recorded and nothing built; §47's evaluation report was deliberately not created, because an empty one looks like an evaluation that returned nothing. **The blocker moved from the world to this deployment**, so the next mission is governance: ask where inference may happen, and give the profile a field for the answer |
| 1.45 | 2026-09-02 | **EXPLICIT ISSUE IDENTITY ROUTE = BLOCKED BY SOURCE GOVERNANCE, and the structure was never the problem.** Three public trackers document a publisher-declared canonical duplicate relation as issue state (Bugzilla `dupe_of`, Launchpad `duplicate_of_link` + `duplicates_collection_link`, Debian merges), so Mission 1.20's proposed route is real. **Every candidate with a usable data licence also disallows the API path in robots.txt, and the one deployment that permits it has no data licence.** The Document Foundation Bugzilla releases all contributions under CC BY-SA 4.0 and honours `include_fields` -- the best minimisation posture in the catalog -- and its robots file is `Disallow: /` with an allowlist of six CGI paths, none of them `/rest/`. **A content licence is not an access grant**: Mission 1.18 established that separation and this is the first time it blocked a source whose licence was perfect. Launchpad adds a second, durable blocker -- 41 fields including `owner_link` and no field allowlist. **0 acquisitions, 0 records, catalog unchanged at 29** -- registering a candidate turned out to require a LEGACY-profile review that neither has, so the registration was reverted rather than made to fit and the finding lives in an Authoritative document. Both deterministic routes are now exhausted, so Mission 1.22 should be semantic INFERENCE |
| 1.44 | 2026-09-02 | **The deterministic route to repeated-problem evidence is CLOSED, and it took two acquisitions to establish it.** A pre-registered narrow acquisition -- 89 real Stack Overflow questions tagged `docker`, one request, committed before any content was read -- produced **0 Signals, 0 Claims, 0 Evidence**. The finding is not that nothing repeated: three questions share **182 characters** of exact tool-specific Docker daemon diagnostic, and the shared string ends at `exec: "`, exactly where the wrapper stops and the failure begins. Support is 3 up to length 182 and 1 from 184, so **a rule needs a length and every length is either the envelope or the instance**. Mission 1.18's S0 could be blamed on selecting by a language tag; this one cannot. **A diagnostic names the ENVELOPE**, so no further mission should try another deterministic Stack Exchange query -- the choice is semantic INFERENCE or a source with explicit issue identity. Two overstatements corrected first: a TED notice publishes a TOTAL_VALUE rather than what a buyer PAID, and the portfolio lacks a stable REQUESTER IDENTITY rather than any person at all |
| 1.43 | 2026-09-02 | **A named open question answered by the operator's own page, and the first source whose obligations run the other way.** H-24 asked whether aggregate pageview counts are CC BY-SA Licensed Material; the Analytics API access policy answers under a heading called *Data licensing*: they are **CC0 1.0**. The first instrument in this catalog to waive the **sui generis database right BY NAME**. **CC0 imposes nothing on the OUTPUT**, so attribution here is a courtesy and no condition asserts one -- what Wikimedia imposes is a condition on the REQUEST, and the collector gained a fifth gate that refuses a socket when the transport would send an identity the review did not declare (ADR-028). **A fifth record kind** `content_request_count`, saying REQUEST rather than VIEW, with `audience.class` REQUIRED; **a fourth quantity family** `CONTENT_REQUEST_VOLUME` (ADR-032), because widening `MEASURED_SERIES` would have cost the FAMILY its meaning rather than `metric` its meaning. **Outcome S1: 18 Signals, 18 OBSERVED Claims, 18 Evidence, all NON_SCORABLE.** The calendar confounder is written into the type and every Claim; the cross-item contrast was considered and refused |
| 1.42 | 2026-09-02 | **Stack Exchange collected, normalized, and correctly producing NOTHING.** A fourth record kind -- `community_question`, the first named for a SHAPE rather than for the first source to reach it -- and `stack-exchange-question@1.0.0`. **15 NormalizedRecords, all `VALID`**, which no adapter here had managed: GDELT is `PARTIAL` for H-29/H-30 and TED for H-37, and nothing is open here. **The first adapter whose period is `ESTABLISHED` on the source's own evidence**, so `observed_at` is a real moment for the first time. **OUTCOME S0: 0 Signals, 0 Claims, 0 Evidence.** 35 distinct tags over 15 questions, three tags repeated, no two questions sharing a tag set, and one question in both non-trivial cohorts: **a tag is a subject, not a problem**. The cohort was not weakened and no second query was run. Two latent normalizer defects found by tests in paths the real data never took |
| 1.41 | 2026-09-01 | **Stack Exchange APPROVES under the local profile; no collector built.** The first approving review for a community-content source, and the first where the positive rights come from a CONTENT LICENCE rather than a platform's terms: the API Terms decide ACCESS and are silent on reuse, CC BY-SA 4.0 decides REUSE and grants commercial use. The API carve-out removes an obstacle and **grants nothing**. **ShareAlike is avoided by the profile, not answered** -- it attaches to Adapted Material that is SHARED and this profile shares nothing, so it must be re-reviewed before anything is published. `PLATFORM_LICENSED` argued, not set: `THIRD_PARTY` means *separate permission is required* and CC BY-SA already reaches us. Terms were **operator-supplied** after HTTP 403; **no 403 retried, no header varied**. Owner objects excluded at acquisition; the Data Dump registered so it could be refused by name |
| 1.40 | 2026-09-01 | **The registry and the runtime agree, and nothing was inherited to get there.** Five sources gained a `local-private-research-v1` review, each version 1 of its own line, evidence reused and decisions re-made. **ADR-027 unchanged, no fallback**: `ted-eu` is still approving locally and REFUSED commercially. Four ELIGIBLE; OpenAlex approves and stays blocked on two unsatisfied conditions, and is the one place the local profile is **stricter** (scholarly authorship, MINIMISED posture). **The named GDELT gap is closed for this profile**: `gdelt-doc-api` and `gdelt-bulk-files` are now blocked BY NAME, because a narrowing that exists only in the review text is not a narrowing. Loader bug fixed: condition and evidence row ids omitted the profile, so two reviews of one source sharing a condition key collided |
| 1.39 | 2026-09-01 | **No source added, and the blocker is the product.** Ten sources cover `problem` or `desire` and none approves. Stack Exchange won the selection and could not proceed: its two outstanding documents sit behind an anti-bot interstitial this environment cannot reach at all, and **no bypass was attempted**. **The larger finding: the runtime declares `local-private-research-v1` and exactly ONE review exists under it.** `world-bank`, `gdelt`, `eurostat`, `fred` and `openalex` are all REFUSED at the gate today -- the deployment holds 15 of 23 RawRecords it could not re-collect, gathered before ADR-027 existed and carrying no `use_profile` in their provenance. The gate is right; the review nobody wrote is what is missing. Next: local-profile reviews FIRST, then Stack Exchange |
| 1.38 | 2026-09-01 | **The first ReliabilityAssessment, and the first evidence score.** A generic operator tool with **no default for any judgement field** -- value, reviewer, rationale and limitation are all refused blank, and the packet is FACTS while the file is JUDGEMENT. Recorded: `HUMAN_REVIEW` **0.5** by a named person over the TED procurement scope, on 4 document-backed basis rows. **The Evidence is now SCORABLE and `q_i = min(components)` names RELIABILITY as the limiting component** -- score 50.0, support 0.5, uncertainty 0.5. **Level stayed 1**: the category gate and unknown independence both hold, so reliability alone cannot reach Level 4. Nothing persisted downstream, profile still `UNCALIBRATED`, D-03 untouched. `scoring.evidence.reliability` stays NULL -- resolved late from the assessment with the binding recorded (ADR-026) |
| 1.37 | 2026-09-01 | **The first reliability review against real Evidence, and the first to stop at the end of the framework. Outcome B: NO assessment created.** eForms **BT-161** read from the Publications Office's own SDK 1.15.1: *"the value of all contracts awarded in this notice, INCLUDING OPTIONS AND RENEWALS"* -- not what was paid, not necessarily what will be. It can also be **lawfully withheld** (BT-195 to BT-198), so a cohort covers the PUBLISHED subset and a max-minus-min is an extreme over non-random missingness. TED validates conformance, never truth: 60 rules name BT-161 and all are presence/absence. **No origin can supply the number** -- `DOCUMENTED_METHOD` needs the document to state it, `CALIBRATED_EMPIRICALLY` needs outcome data, `HUMAN_REVIEW` needs a named person and a model may not stand in. Inventory re-measured: **8 Evidence rows, 4 scopes**, TED the fourth. Category, independence and level untouched. **0 assessments, everything still NON_SCORABLE** |
| 1.36 | 2026-09-01 | **The TED Signal interpreted, and the sentence is the enforcement.** A fourth template on the existing interpreter -- **`observed-signal-restatement@1.1.0`**, not a TED-specific one, because a template is specific to a SIGNAL TYPE and never to a publisher. **1 OBSERVED Claim, 1 revision, 1 Evidence row**, through the production path, idempotent. The claim is bounded in its own wording -- *"within a bounded set of 3"* is what stops it becoming a statement about every division-90 contract -- source-attributed, and carries no date, no trend and no market vocabulary. **The cohort MEMBERSHIP is the identity and the amount is wording**: a revised amount appends a revision, a fourth notice is a different proposition, and the member values stay in provenance. `observation_category` stayed `UNCATEGORISED` because a spread is not a purchase, and `MARKET_ACTIVITY` is the only gate to Level 4. Support 3 is still ONE source; reliability NULL, `NON_SCORABLE`. **No Opportunity, no score, no LLM.** H-36A/B, H-37, H-38 untouched |
| 1.35 | 2026-09-01 | **Exact decimals, and the first real TED Signal.** `ted-search-api@1.1.0` parses with `parse_float=Decimal` and renders through `canonical_number`, so a fractional tender value reaches jsonb as an exact STRING; `parse_int` stays unset because a JSON integer was never at risk. **The normalizer is NOT bumped** -- its output is unchanged, and what changed is the inputs it accepts, declared in `supported_collector_versions`. One bounded acquisition on 2023-03-01 in CPV division 90 produced **1 TRANSACTION_VALUE Signal**: support 3, 686545.02 EUR, `ABSOLUTE_DIFFERENCE`, `NON_TEMPORAL`. Two defects real data exposed: `cpv_division` never reached the composed query, and the cohort scope carried only the FIRST member's codes -- `procurement-value-contrast@1.0.1`. **No Claim, no Evidence.** H-36A/B, H-37, H-38 untouched |
| 1.34 | 2026-09-01 | **A third Signal quantity family, and a derivation that correctly produced nothing.** `TRANSACTION_VALUE` (ADR-029): the `procurement_notice` kind mapped to neither existing family, and `MEASURED_SERIES` could not be widened without making `metric` optional for every series signal ever written. `procurement-value-contrast@1.0.0` is NON-TEMPORAL by construction -- basis `NONE`, no date read, members ordered by amount -- keeps four monetary semantics apart, converts no currency, and is **not** willingness-to-pay. **0 real Signals**: the two EUR award totals are CPV 90 and CPV 66, which are two markets. **H-37 and H-38 stay OPEN** |
| 1.33 | 2026-09-01 | **The third record kind, and the first canonical procurement notices.** `procurement_notice` holds what neither existing kind could without getting worse, and carries no `observation.value` because a notice has no single measurement. `ted-search-api-notice@1.0.0`: one notice one record with lots structured inside it, four monetary semantics kept apart, no `price_paid`, no currency converted, every language kept with no canonical display value. **A published DATE does not become a moment** -- `observed_at` NULL, naive bounds, **H-37** open with the source value preserved. Three real notices normalized, idempotent, all `PARTIAL`. **No TED Signal, Claim or Evidence** |
| 1.32 | 2026-09-01 | **The first TED acquisition, and the first concrete TED resource.** A source-level approval is not a resource-level one: TED authorised `"datasets": []` and every resource failed closed, which is why `AUTHORIZATION_READY` sat beside `resource_ready` NO for six missions. **One** resource authorised -- eForms contract and award notices from 2023-03-01 through the Search API -- then `ted-search-api@1.0.0`, the third collector: four gates before a socket, one route with **no fallback**, bounds with **no defaults**, **no exhaustion mode**, four monetary semantics kept apart, no currency converted. **3 real RawRecords**, idempotent on re-run. **H-36A NOT ESTABLISHED, H-36B NOT ADDRESSED, no normalizer, no Signal, no Claim** |
| 1.31 | 2026-08-31 | **The authorization carries only reviewed routes, and an objective property of configuration is verified rather than human-confirmed** (ADR-028). `context.access` used to hold every registered access profile, so TED's context would have handed a collector the bulk route its review refuses by name -- with the transport's host allowlist derived from it. A `(source, profile)` may now declare a `route_authorization`, and the context carries those routes and no others. Two TED conditions that described objective properties of a collector that does not exist -- its route, its field selection -- moved from `HUMAN_CONFIRMATION` to `CAPABILITY` on **appended local review v2**, changing no policy conclusion. **The residual database-right acceptance stays human, is unrecorded, and still blocks** |
| 1.30 | 2026-08-31 | **Source permission is use-profile-specific** (ADR-027). Every review already answered a question about a use -- the catalog said so in prose since Mission 1.0 -- but the answer had no IDENTITY, so it could not be required, compared or matched, and the gate never saw it. Now a review records its `assessed_use_profile`, currentness is per (source, profile), and `evaluate_eligibility` requires the profile with no default. **`ted-eu` is `REQUIRES_REVIEW` under the commercial profile and `APPROVED_WITH_CONDITIONS` under the local one, at the same time.** Approval never transfers; the runtime declares its profile and never infers it |
| 1.29 | 2026-08-31 | **The deployment model is recorded: LOCAL-FIRST / SINGLE-OPERATOR.** The application runs locally for its operator and is not offered as a public multi-tenant SaaS -- but the research it produces is used to launch **commercial** products, so **local deployment never implies `NON_COMMERCIAL_USE`** and commercial-use rights are still reviewed. Workspace and RLS stay. No billing, customer accounts, team collaboration or cloud scaling unless explicitly required |
| 1.28 | 2026-08-31 | **The routes are documented; the gate has no vocabulary for them.** TED's own docs say the Search API is *"for analysis and reuse"* and *"primarily targeted at data reusers"*, naming commercial organisations and researchers as users; the Open Data Service publishes data *"for analysis and re-use"* with a **Connect your app** button. That is intended-use evidence and **not** a database-right grant, and a condition now says so. The real blocker moved: **every approval in this registry is an answer to a use case the model never records**, so a source cannot be blocked broadly and authorised narrowly. `ted-eu` stays `REQUIRES_REVIEW` at v5 |
| 1.27 | 2026-08-31 | **The dataset licence found, and H-36 still open.** The Publications Office's own DCAT record attaches `dct:license = COM_REUSE` to **every** `ted-1` distribution including the bulk XML download, and `COM_REUSE` carries `skos:exactMatch` to Decision 2011/833/EU -- so the licence on the bulk route IS the instrument already known to be silent. The search API's own Terms of Usage resolve to the same TED legal notice. H-36 splits into **H-36A** (does the right subsist? not established -- nothing names a maker) and **H-36B** (is it granted? not addressed). The blocker is now a drafted, unsent message to a named address |
| 1.26 | 2026-08-31 | **H-34 CLOSED PERMITTED; H-36 did not close.** Commission Decision 2011/833/EU was retrieved from the Publications Office Cellar and read in full: reuse is defined by PURPOSE, not by METHOD, so machine processing falls inside the grant. The same text contains **zero** occurrences of *sui generis*, *extraction*, *re-utilisation* or Directive 96/9/EC. All six load-bearing activities are now granted and `ted-eu` is **still REQUIRES_REVIEW** -- the blocker is no longer an activity in the matrix |
| 1.25 | 2026-08-31 | **H-34 stays OPEN, and the question got precise.** TED's governing instrument is now NAMED and proven -- Commission Decision 2011/833/EU, cited by TED's own legal notice -- and its text returned an empty body at five first-party EUR-Lex addresses. The grant says notices may be *reused*, and 'reuse' is defined in the document nobody could read. A second question surfaced: does the grant reach the sui generis DATABASE right, given that the access route is bulk extraction (H-36) |
| 1.24 | 2026-08-31 | **Demand-side expansion: nine sources examined, zero approvals, and that is the result.** Pinterest and Hacker News moved to RESTRICTED on retrieved terms; Bluesky's developer guidelines are now known to exist and could not be fetched. Two procurement sources registered -- the first lawful route to WILLINGNESS_TO_PAY as a TRANSACTION rather than a listed price. `ted-eu` has five of six activities granted and is blocked by one |
| 1.23 | 2026-08-31 | **Reviewed reliability governed, and none reviewed.** A reliability applies to a MEASUREMENT x PURPOSE scope, rests on retrieved first-party documents, is attributed to a person and is superseded rather than updated (ADR-026). Zero assessments exist, so all seven Evidence rows stay NON_SCORABLE and aggregation stays UNAVAILABLE -- **outcome B, and it is the design working**. D-03 loses one blocker and keeps four |
| 1.22 | 2026-08-31 | The **first complete Signal -> Claim -> Evidence pipeline**: `observed-signal-restatement@1.0.0` produced **7 real OBSERVED Claims, 7 revisions and 7 Evidence rows** from the seven real Signals. Deterministic, source-attributed, no LLM. GAP-5 resolved; a refused interpretation gets a run record, never a Claim (ADR-025). Reliability stays NULL and every record is NON_SCORABLE, honestly |
| 1.21 | 2026-08-31 | The **interpretation boundary** defined before anything crosses it: a Claim may precede its Opportunity, and a machine may not store an assertion nothing supports (ADR-024, Ontology V2.2). Contract and model only -- **0 Claims, 0 Evidence** |
| 1.20 | 2026-08-30 | First **source-relative temporal** extractor: `lexical-frequency-change@1.0.0`, two real signals and two real gap refusals. A gap is never bridged and an absent term is not a zero (ADR-023). H-29 untouched: `ORDERED_PERIODS`, no bounds, no `observed_at` |
| 1.19 | 2026-08-30 | **H-32 closed** on first-party GDELT evidence: the WEB-NGRAM stream is ordered. **H-29 stays open** — GDELT documents UTC for a *different* dataset whose date means something else. H-31 answered and refined. No extractor, no new signal (ADR-022) |
| 1.18 | 2026-08-30 | First two deterministic extractors, and **five real Signals**. `PARTIAL` proved usable in production: both GDELT inputs contributed because neither missing fact was one the derivation needed. A refused derivation gets a run record, never a Signal (ADR-021) |
| 1.17 | 2026-08-30 | Signal defined as a DERIVATION over two or more observations, never a labelled one. `nlp.signals` reshaped; the family stops classifying demand; order and instant separated, and H-32 opened. Model and contract only -- no extractor, 0 signals |
| 1.16 | 2026-08-30 | Second normalizer recorded: GDELT WEB-NGRAM, deterministic and offline, with two real canonical records. Every one is PARTIAL because H-29 and H-30 stay open and are stated per record |
| 1.15 | 2026-08-30 | Second canonical record kind recorded: a lexical frequency observation with no geography. A period may declare its timezone unestablished and a language may stay unmapped, both visibly (ADR-019). No GDELT normalizer |
| 1.14 | 2026-08-30 | Second collector recorded: GDELT WEB-NGRAM, streamed and bounded, with real RawRecords. Bulk-file collection rules added; GDELT is collected and still not normalized |
| 1.13 | 2026-08-30 | Resource-ready separated from eligible: a source can pass the gate while every resource it could ask for fails closed. GDELT review 3 authorises two WEB-NGRAM resources; how much a job may take became a governance question alongside what it may reach |
| 1.12 | 2026-08-30 | Silence-is-not-permission made mechanical: an approving review must grant every materially required activity. Three Mission 1.7 approvals withdrawn on audit; GDELT became the fourth collector-eligible source and the first non-economic one |
| 1.11 | 2026-08-30 | Source universe expanded to 27 across 14 families; signal coverage added as a non-scoring source attribute (ADR-017); coverage-is-not-permission invariant added; global registry state watched by the post-suite check |
| 1.10 | 2026-08-30 | First normalizer recorded: the RawRecord to NormalizedRecord boundary, World Bank only; normalized_records is no longer empty; normalization invariant added; normalizable separated from eligible, enabled and implemented |
| 1.9 | 2026-08-30 | First collector recorded: World Bank only, gated by an AcquisitionAuthorizationContext; raw_records is no longer empty; collector boundary invariant added |
| 1.8 | 2026-08-29 | Compliance capabilities recorded: a condition is cleared by a verifier and by nothing else; two sources are collector-eligible; eligible / enabled / implemented separated (ADR-016) |
| 1.7 | 2026-08-29 | Source review round recorded: three sources APPROVED_WITH_CONDITIONS, none collector-eligible; conditional-eligibility rule added |
| 1.6 | 2026-08-29 | Boot sequence points to Ontology V2.1 and gains the Claim model; Claim invariant added; A-13 removed from blocked work (ADR-015) |
| 1.5 | 2026-08-29 | Boot sequence gains the evidence aggregation framework; evidence-aggregation invariant added; D-03 blocked-work entry rewritten as framework-resolved / parameters-uncalibrated (ADR-014) |
| 1.4 | 2026-08-29 | Boot sequence gains the source registry spec; source-governance invariant added; D-07 removed from blocked work (ADR-013) |
| 1.3 | 2026-08-29 | Boot sequence gains the evaluation framework; tenancy invariant records that row-level security is now enforced (ADR-012) |
| 1.2 | 2026-08-27 | Boot sequence points to ontology V2; research lifecycle and taxonomy-governance invariants added |
| 1.1 | 2026-08-27 | Boot sequence points to domain V1.1; canonical domain invariants added (§Canonical invariants); tenancy rule added |
| 1.0 | — | Initial operating contract (was unversioned; versioning added in 1.1 per `specification-audit.md` §4 recommendation 8) |
## Purpose

This repository contains an evidence-driven AI Opportunity Research Engine for discovering, analyzing, scoring, validating, and planning digital product opportunities across B2B, B2C, entertainment, education, gaming, creator, hobby, utility, social, AI, and other markets.

This file is the top-level operating contract for Claude Code.

## Authoritative specifications

Before making architectural or implementation decisions, read the relevant documents in this order:

1. `docs/domain/opportunity-ontology-v2.md`
2. `docs/domain/scoring-framework-v1.1.md`
3. `docs/domain/evidence-confidence-framework-v1.md`
4. `docs/ai/llm-reasoning-rules.md`
5. `docs/data/data-principles.md`
6. `docs/data/data-retention-policy-v1.md`
7. Any relevant Architecture Decision Records (ADRs)
8. Any task-specific specification created later

These documents are authoritative unless a newer, explicitly versioned specification or ADR supersedes them.

## Canonical invariants

Added in 1.1. These are settled. Do not re-derive them, do not redefine them
locally, and do not resolve an apparent conflict with them by guessing.

### Deployment model — local-first, single-operator

Added in 1.29. **Placed first because it frames the invariants that follow**: it
decides what every source review's assessed use case is about, and it is the
reason the tenancy rule below survives having one operator.

Startup Research OS is intended to **run locally for its developer/operator**. It
is **not** intended to be offered as a public multi-tenant SaaS.

**The research it produces is used to discover, evaluate and launch commercial
SaaS and web products.** So the deployment is local and the purpose is
commercial, and those are two independent facts.

- **Local deployment does NOT imply `NON_COMMERCIAL_USE`.** This is the rule most
  easily taken backwards, and taking it backwards would produce exactly the
  narrowed assessed use case §Source governance forbids: a permission obtained by
  describing a smaller product is a permission for a product we are not building.
  **Commercial-use rights are still reviewed wherever they apply.**
- **Public redistribution and customer-facing data rights are out of scope**
  unless the deployment model changes. A source review that grants them is not
  wrong; a review that *depends* on them is out of scope.
- **Do not build billing, customer accounts, team collaboration or cloud
  scaling** unless a mission explicitly requires it.
- **Preserve the workspace and row-level-security architecture.** Being a single
  operator today is not a concrete reason to remove a tenant boundary, and
  re-adding one later is far more expensive than keeping it.
- **Optimise application UX and deployment for one local operator.**

**If the deployment ever becomes public, customer-facing, sold,
subscription-based or multi-tenant, the commercial profile must be reviewed again
from the top.** It is unreviewed today, and it must not be reached by drift.

**The open governance consequence.** Every approval in the source registry is an
answer to a use case the model does not record (Mission 1.15.4). The
`LOCAL_PRIVATE_RESEARCH` profile in `route-scoped-source-authorization-gap-v1.md`
is **local, not non-commercial**, and must not be renamed or read as
non-commercial when `assessed_use_profile` is built. Nothing in the TED reviews
rests on non-commercial status: `commercial_use` is `PERMITTED` there on its own
evidence, from v1.

### Source permission — scoped to the use it was granted for

Added in 1.30 (Mission 1.15.5, ADR-027). Placed here because it is the mechanism
the deployment model above needs in order to mean anything.

**A verdict has a subject.** Every policy review records the
`assessed_use_profile` it answered about. Two are registered:
`commercial-multi-tenant-research-v1` (what every review before Mission 1.15.5
assessed, and what a future public deployment must satisfy) and
`local-private-research-v1` (the current runtime).

- **Currentness is per `(source, profile)`.** Each profile keeps its own
  append-only version line, and a source may hold different current verdicts
  under different profiles without contradiction. `ted-eu` does.
- **The gate requires the profile, with no default.**
  `evaluate_eligibility(source, use_profile_id, …)`,
  `build_authorization(source, use_profile_id, …)` and
  `verify_source(source, use_profile_id, …)` all take it second and positional.
- **Never transfer approval between profiles.** A missing profile raises, an
  unknown one is refused, and a profile with no review is refused. **Nothing
  falls back** -- not to another profile, and not to the source's legacy verdict.
- **Runtime authorization must declare the active profile.** `SROS_USE_PROFILE`,
  read at the entry point. Never inferred from an environment name, the host, a
  container, a user count or the absence of billing: a profile is a governance
  fact and those are infrastructural ones, and the same binary in the same
  container can be operated under either.
- **`SourceRecord.review` is the LEGACY-profile review and is not an
  authorization input.** It survives so that every document written before
  ADR-027 stays true; an AST test asserts the three gate modules never read it.
- **A profile never widens what a source permits.** It narrows what we claim to
  do. `commercial_purpose` is true on BOTH profiles, because local is not
  non-commercial and a commercial-use right still has to be granted by the
  source's own evidence.
- **Never report a naked verdict.** A source's standing is a table keyed by
  profile. Generated catalog documents present the legacy profile and say so.

### Route binding — the authorization carries only what the review authorised

Added in 1.31 (Mission 1.15.6, ADR-028). Placed here because it is what stops
the profile above from being a label on an authorization that still hands a
collector everything.

**An access profile is a fact about the source; a route authorization is a fact
about us.** `AccessRestriction` verifies that the registry records exactly the
approved access profiles -- which TED cannot satisfy, because TED really is
reachable by bulk XML and deleting that row would be falsifying a fact about a
source in order to obtain a permission.

- **`context.access` carries the reviewed routes and no others**, where a
  `(source, profile)` declares a `route_authorization`. A blocked label has no
  endpoint to read, so there is no host to allowlist and nothing for the
  transport to be pointed at. That is the enforcement; `authorize_route` only
  makes the refusal say *refused by name* instead of *not found*.
- **An authorised route the registry does not record is refused**, not skipped.
- **`None` means unasked, not unrestricted.** Every entry before 1.15.6 is in
  that state -- and `source-route-binding` reports *unimplemented* rather than
  *satisfied* when it is absent, so a condition never rests on a restriction
  that does not exist. **GDELT was the named gap and is now half-closed.**
  Mission 1.17's local-profile review declares a `route_authorization` blocking
  `gdelt-doc-api` and `gdelt-bulk-files` by name, so the LOCAL context carries
  only `gdelt-web-ngram-files`. **The commercial context still hands a collector
  all three**, and closing it there is a commercial-profile review act that has
  not happened.
- **Field minimisation is asked before a request is composed.**
  `context.authorize_fields` refuses an excluded field by name, an unreviewed
  field and an unstated selection. Where a source supports field selection --
  TED's `fields` parameter does -- **collect-then-filter is not available as an
  excuse**, because a request that discarded the contact block afterwards
  retrieved the contact block. No method removes fields from a collected record.

### Semantic problem equivalence — built, evaluated, and not in production

Added in 1.48 (Mission 1.24, `problem-equivalence-evaluation-v1.md`). The first
model-mediated inference this repository has run, and it produced no epistemic
row at all.

**The classifier exists and lives in its own package.**
`validate_signals.py` forbids a Gateway import anywhere in `sros_nlp` and
requires every module there to be classified, so a model-calling component
cannot live in the signal layer. The guard was left untouched and
`packages/semantic-equivalence` carries the work, depending on contracts and the
Gateway and on nothing else -- in particular not on `sros_acquisition`, because
a classifier able to read the source registry could decide its own authorization.

- **Authorization is resolved before any source text is serialised**, not before
  the socket. `classify_pair` refuses on an unauthorized decision before
  `render_equivalence_prompt` is called, so a refused pair leaves no string
  containing question text for a later bug to send. A test hands it a gateway
  double that raises if reached.
- **A candidate is not a prediction.** The generator is deterministic, versioned
  and capped after a total ordering, and its output means *worth asking about*.
  Its recall limit is carried on the result object: a pair it did not surface is
  UNCONSIDERED, never different, and no statement derived from the set may be
  worded as describing all repeated problems.
- **Granularity is fixed by the rubric, once, and never per pair.** The question
  is what a reader would CHANGE, not what the true root cause is -- question text
  usually cannot establish one, because the asker does not know it. Same tool,
  same tags, same wrapper diagnostic however long, same generic error class and
  same broad symptom are each insufficient BY CONSTRUCTION rather than below a
  threshold.
- **ABSTAIN is mandatory and is never counted against the model.** The
  alternative to an abstention on this corpus is a guess, and a wrong SAME is the
  costly error.
- **No confidence number is requested from the model.** A self-reported certainty
  is not a probability, and the only safe handling is to mark it uncalibrated and
  never do arithmetic on it -- at which point asking for it buys nothing and
  invites a later reader to multiply by it.
- **Question text is `UntrustedText` and can occupy no other region.** The
  classifier is given no tools, no browsing and no execution, so an instruction
  inside a body has nothing to reach even if obeyed.
- **A price rests on a retrieved document**, like every other value here. The
  cost unit is one US dollar, stated rather than assumed, and the table models
  neither caching nor batch nor a negotiated rate.

**THE EVALUATION PASSED ITS PREDECLARED CRITERION AND ESTABLISHED NOTHING.** 40
real labelled pairs, zero false SAME -- and **zero SAME of any kind**, over a
holdout containing no SAME label. A classifier hard-coded to answer DIFFERENT
records the same score. Precision on SAME is undefined and recall is 0/1.

**The criterion was wrong in a way only data could show.** V1 required a positive
*anywhere in the reference set*; the only one fell in DEVELOPMENT. V2 requires it
in the split being scored, and returns EVALUATION_INSUFFICIENT on the same run.
**V1 is kept**, because Mission 1.24 was scored under it and rewriting a rule
after the fact means it was never binding.

**So no production inference ran**, and there is no model-derived Signal, no
INFERRED Claim and no Evidence. The blocker is a reference set with real
positives in the scored split, which this 89-question corpus did not supply: one
defensible SAME in 40 candidate pairs is a finding about the corpus, not about
the classifier. **No synthetic positive may substitute** -- a constructed pair
can test a parser and can never establish semantic accuracy against real data.

### An observation says what LEVEL it is about, or it says nothing

Added in 1.62 (Mission 1.34, `mission-1.34-report.md`,
`scope-architecture-demonstration-v1.json`).
**`MULTI_SCOPE_ARCHITECTURE_READY_SCOPE_RELATIONS_UNPOPULATED`.**

    Evidence row  ->  ObservationScope  ->  [ reviewed ScopeRelation ]  ->  role
    subject:docker      PRODUCT              (none exist)                 DIRECT
    ted-eu:CPV-division:90  CATEGORY         (none exist)                 REFUSED

- **THE ASSUMPTION THAT WAS THERE.** `build_packet` unioned its rows' dimensions
  with **no scope term in the expression**, so membership in a packet WAS the
  claim that the row was about that packet's subject. Fine while every row
  observes the subject; exactly wrong the moment a procurement notice about a
  purchasing CATEGORY sits beside a question about a PRODUCT.
- **Four levels, each defined by what it IS.** §1 forbids defining PRODUCT as
  *narrower than CATEGORY*, because a vocabulary whose members are defined by
  their neighbours cannot refuse a new case. Each carries a `never_means`, and
  **`MARKET`'s example in this repository is "none"** -- no registered source
  observes one and nothing was invented so the vocabulary would look complete.
- **SUBJECT SCOPE IS NOT MARKET SCOPE.** `MarketScope` says WHERE an Opportunity
  applies; `SubjectScopeType` says what level of thing an observation is about.
  Both contain the word GEOGRAPHY and they answer different questions -- a World
  Bank series is ABOUT Germany, which is a subject, and where an Opportunity
  applies is a separate field nobody touched. Merging them would be the Mission
  1.15.4 shape again: one field answering a question that is two.
- **UNDETERMINED is a STATUS, never a fifth type.** A level saying *nobody
  classified this* would give every consumer branching exhaustively over levels a
  branch for an absence. 3 of 28 rows are UNDETERMINED -- the GDELT lexical terms,
  because a word names no level of thing -- and **nothing was mass-labelled
  PRODUCT to make the corpus tidy** (§12).
- **THE RELATION REGISTRY SHIPS EMPTY, AND THAT IS THE RESULT.** Mission 1.33
  refused to assert which commercial category contains Docker; §33 forbids
  inventing one here. So the capability exists and holds zero edges, and **no
  Evidence row in this deployment can currently be contextual** -- contextual
  requires an edge. The registry records what it did NOT write and why.
- **NO TRANSITIVE EXPANSION.** Product-in-category plus category-in-market does
  not yield product-in-market. Transitivity looks free and silently multiplies
  what one reviewed edge licenses, and the review that authorised the first never
  saw the third.
- **There is no `MODEL_INFERRED` origin**, in the enum or anywhere in the
  mission. Scope identity and containment are exact equality or a reviewed
  registry entry: no distance, no token overlap, no stem, no synonym table, no
  embedding, no model.
- **NO FACTUAL DIMENSION PROPAGATION** (§25). A broader observation is retained
  AT ITS OWN SCOPE. `CATEGORY:X has MARKET_ACTIVITY` stays
  `context(CATEGORY:X).MARKET_ACTIVITY` and never becomes
  `product(docker).MARKET_ACTIVITY` -- no inheritance, no promotion, no
  lower-confidence variant, no parameter that would enable one.
- **The packet offers NO UNION of direct and contextual dimensions**, and a test
  enumerates every public attribute to prove it, because that union is the
  sentence *Docker supports MARKET_ACTIVITY* and it must not be one attribute
  access away. Sufficiency reads the DIRECT half alone, so a future category row
  cannot satisfy a rule written for direct product evidence. **That is a
  structural no, not a policy no**: a policy no is relaxed by editing a
  threshold.
- **The wording carries the scope in the SUBJECT of the sentence**, not in a
  trailing qualifier, because a qualifier is what a summariser drops.

**NO MIGRATION, AND THAT WAS A DECISION.** The scope is DERIVED at packet-build
time from identifiers already held, by the same `subject_key` procedure grouping
uses. Persisting it would freeze a derivation in a column, which
`source-registry-v1.md` §3 refuses for eligibility and for the same reason. So no
new tenant table, no RLS change, no historical backfill, and the ledger stays at
0031.

**COMPATIBILITY WAS PROVEN RATHER THAN ASSERTED.** Regenerating
`opportunity-preparation-v1.json` after every change in the mission produced
**exactly one differing field across the whole artifact** -- the recorded
`subject_registry` version, 1.0.0 -> 1.1.0. Every packet id, dimension set,
eligibility count and sufficiency verdict identical. The Docker packet is still
8 rows and HYPOTHESIS_FORMABLE, and the scoped packet's direct half reproduces
it.

**Two things the tests found and one clause that was removed rather than
written.** The first gate applied §15's dimension clause to DIRECT rows, which
refused Mission 1.32's deliberately dimensionless row -- §15 states its
conditions for broader-scope INCLUSION, and a direct row is not included on the
strength of anything. And §15's *provenance is preserved* is already enforced by
`EvidenceFacets` and `ObservationScope`, so a duplicate check could never fire:
**an unreachable guard reads as protection while protecting nothing**, and the
tests assert the two upstream constructors instead.

**Opportunity revision 1 and its 7 links are untouched**, no revision 2 exists,
reliability is still one assessment, independence is still UNKNOWN everywhere, 0
model calls, 0.00 USD, and problem-family inference stays **PARKED**.

### Commercial evidence lives at a broader scope than a product subject

Added in 1.61 (Mission 1.33, `commercial-dimension-source-feasibility-v1.md`,
`mission-1.33-report.md`). **`COMMERCIAL_SOURCE_GRAIN_MISMATCH`**, over all 29
registered sources, with no acquisition and no model call.

    can name Docker          5   ->  0 carry a usable commercial dimension today
    reach it as a MENTION    7
    cannot reach it         17
    carry real commercial semantics at CATEGORY scope: ted-eu, usaspending,
                                                       world-bank, fred, eurostat

- **THE TWO HALVES DO NOT OVERLAP.** The sources that can name Docker carry no
  commercial semantics; the sources that carry commercial semantics cannot name
  Docker. That is the finding, and it is not fixed by acquiring anything.
- **21 of 29 have no `local-private-research-v1` review**, so ADR-027 refuses
  them at the gate whatever their terms say. **That is not twenty-one
  opportunities.** For the right-grain candidates the commercial finding is about
  the PURPOSE of the use, and **local deployment never implies non-commercial
  use** -- so a local review would meet the same clause and fail on it.
- **GitHub has the best grain in the portfolio and is NOT_RECOMMENDED.** A
  repository full name is exact and publisher-assigned, and a public repository
  IS a supplied solution -- `COMPETITIVE_SUPPLY` is the strongest unclaimed
  commercial dimension available anywhere here. The Acceptable Use Policies
  section 7 is an ALLOWLIST that applies *"regardless of whether the information
  was scraped, collected through our API, or obtained otherwise"* and permits
  research use **only if resulting publications are open access**. The one thing
  that would move it is a commitment to publish open access, which is a product
  decision and not a review.
- **A GitHub issue is a defect report, not an evaluation.** It names an artifact
  and says it is broken; `SOLUTION_DISSATISFACTION` needs a statement that the
  artifact is inadequate for the reporter's need, and separating the two means
  reading prose -- an INFERRED step that does not exist.
- **NO SOURCE SUPPORTS `SOLUTION_GAP`, at any grain.** Every candidate route --
  unanswered questions, empty results, a thin ecosystem -- is an absence of
  evidence, which the dimension's own `never_means` refuses by name.
- **NO SOURCE SUPPORTS `WILLINGNESS_TO_PAY`, at any grain**, and the taxonomy had
  already committed to that before the mission asked: not *a listed price, which
  is an ask and not a transaction*, not *a budget line, which is a capacity and
  not a decision*, not *a public contract total, which includes options and
  renewals*.
- **A near-miss identifier is still a miss.** PyPI's `docker` package is the
  official Docker SDK for Python, published by the platform's own vendor -- and a
  client library is a DIFFERENT ARTIFACT from the platform, so its downloads
  measure adoption of the SDK. *All packages that integrate with Docker* is a
  coherent set and it is a CATEGORY, not the subject.
- **A vendor is not the subject.** USAspending could match `Docker, Inc.` as a
  recipient, and the canonical registry says in its own words that
  `subject:docker` is the container platform and NOT the company.
- **`WRONG_DOMAIN` is a different verdict from `WRONG_GRAIN`.** An App Store id
  is beautifully precise; it names a different class of thing. Forcing
  product-shaped identifiers into a container-tooling Opportunity because the
  shape matches is the error, and product-grain was exactly the property the
  mission was hunting for.

**THE BINDING CONSTRAINT IS ARCHITECTURAL, NOT A SOURCE LIMITATION.**
`CanonicalSubject` carries `subject_id`, `display_name`, `description` and
`identifiers` and **no scope field**; `subject_for()` returns one subject per key;
a packet holds one `subject`. So an Evidence row belongs to exactly one subject
and an Opportunity's subject is the subject of every row supporting it.

Two facts make it concrete. **SROS already models GEOGRAPHIC scope on an
Opportunity and models no SUBJECT scope at all** -- `MarketScope` is
`GLOBAL | REGION | COUNTRY | MULTI_COUNTRY` and the first Opportunity carries
GLOBAL as a recorded limitation. And **the dimension vocabulary already assumes
an answer**: `MARKET_ACTIVITY` asks about *"the bounded scope observed"* and
`ECONOMIC_VALUE` about *"the bounded activity observed"*, so those questions were
written expecting an observation to carry its own scope. The packet model has
nowhere to put it, and the only way to keep a claim honest is to keep the
observation out entirely.

**TED is the case that proves it.** Authorized locally, collector implemented,
normalizer implemented, extractor implemented, one Signal derived, Evidence
already mapping to `MARKET_ACTIVITY`, `BUYER_OR_BUDGET_EXISTENCE` and
`ECONOMIC_VALUE`. Its subject key is `ted-eu:CPV-division:90`. Every piece exists
and the vocabulary cannot name a product.

**A feasibility verdict is not a permission, and the three questions stay apart**
-- grain, epistemic warrant and governance are separate columns, and a source can
be right-grain and refused or authorized and useless. **Nothing was acquired, no
model was called, the canonical subject registry gained no identifier, and all
thirteen counters were verified unchanged against the live database.**

**The recommendation is `NO_CURRENT_SOURCE_CAN_CLOSE_DOCKER_COMMERCIAL_DIMENSION`
and a Multi-Scope Opportunity Evidence Architecture mission**, because acquiring
first produces Evidence in its own packet that can never join `subject:docker`.

### An unaccepted answer is one person's non-action, and nothing more

Added in 1.60 (Mission 1.32, `answer-acceptance-semantics-v1.md`,
`mission-1.32-report.md`). **`COMMERCIAL_EVIDENCE_CREATED_NO_OPPORTUNITY_DIMENSION`**:
a valid bounded Signal, Claim and Evidence row that maps to **no Opportunity
dimension at all**, and §9 named that in advance as a legitimate outcome.

    88 eligible  ->  34 accepted  |  38 answered-unaccepted  +  16 zero-answer  =  54
    community_question_without_accepted_answer_volume  ->  frozenset()

- **THE ASSESSMENT WAS FROZEN BEFORE THE SIGNAL EXISTED.** The semantics document
  was written and committed before any derivation ran, and it records
  `NO_EXISTING_DIMENSION` against both candidates. **A dimension chosen after
  seeing that the packet needed one is not a finding, it is a rationalisation**,
  and the ordering is the only thing that distinguishes them afterwards.
- **`has_accepted_answer` means the ASKER clicked accept.** Only the asker may,
  so `false` reports a non-action by exactly one participant. An asker who solved
  the problem elsewhere, lost interest or never returned leaves it `false`
  whatever answers arrived. The normalizer carries the source's own sentence in
  the payload beside the value: *"the asker marked an answer accepted; not a
  statement that the problem is objectively resolved"*.
- **`SOLUTION_GAP` is settled by its own `never_means`**, which reads *that
  absence of evidence of a solution is evidence of its absence*. An unaccepted
  question is exactly that absence, so mapping it there would require rewriting
  the dimension -- and §20 forbids changing a taxonomy definition to obtain a
  better outcome.
- **`SOLUTION_DISSATISFACTION` fails for a simpler reason: the asker is not
  evaluating a product.** There is no object of dissatisfaction anywhere in the
  record. A question is a request for help, never a verdict on a tool.
- **The 16 zero-answer questions are the strongest case and still fail.** Nobody
  could even answer looks like the sharpest possible gap evidence. A question can
  go unanswered because it is unclear, duplicated, too specific or badly timed,
  and a community's non-answer is not a statement that no solution exists.
  **Isolating the sharper subset does not rescue the inference; it makes the same
  inference over a smaller set.**
- **Zero dimensions is a REGISTERED DECISION, not an unknown type.**
  `map_signal_type` returns `None` where nobody has decided and a mapping with
  `frozenset()` where somebody decided none applies -- the Mission 1.28
  distinction, reached for the first time by a type somebody argued about.
- **A zero-dimension row adds SIZE and never DIVERSITY**, which is the arithmetic
  that makes this outcome honest: the packet went 7 -> 8 rows with counting
  dimensions unchanged at 2, so nothing moved sufficiency by existing.
- **The state is OBSERVED LATE and the wording must say so.** The questions carry
  their own creation instants; the flag is whatever it was at collection, which
  may be years after. A claim saying *N had no accepted answer during March* would
  be false, so the window and the observation are named as two different things.
- **A sentence shaped like a numerator invites a rate.** Revision 1 read *"Of the
  questions ... created between T1 and T2, 54 had no answer marked accepted"* --
  true, and still wrong, because it presents the number as a fraction of a
  population it never states and a reader would supply 88, which is not the
  population in that span. `1.4.1` asserts a SET and its bounds. **Revision 1 is
  preserved**: the claim history is append-only and the wrong wording is part of
  it.
- **A missing flag is not `false`** (ADR-023, one field along from an absent
  lexical term). A record omitting `has_accepted_answer` withholds the fact and
  the derivation refuses rather than counting it as unaccepted -- **even when two
  good records remain**, because the population would then be *the records that
  happened to carry the field*, which is not the population the claim names. All
  88 carried it, so the path is exercised by tests rather than by data.
- **The same family, a different type.** `COMMUNITY_QUESTION_VOLUME` is reused
  because this is a different MEASUREMENT over the same kind of QUANTITY, and a
  second family would assert the two counts are incommensurable when they are
  directly comparable. It is a separate signal TYPE rather than a parameter,
  because a parameter that silently changes what a Signal asserts is a hidden
  behaviour with a name.
- **A second measurement over one corpus is not a second finding.** Independence
  is `UNKNOWN` for 8 of 8, and the new row is the least independent in the packet:
  it counts a subset of the very records the existing `community_question_volume`
  row counted.

**Two defects, both general mechanisms rather than typos.** An interpreter
version bump re-INSERTED Evidence, because the idempotency key embeds
`extraction_method` and that embeds the version -- so a re-derivation after any
version change is an INSERT, not a no-op, and `scoring.evidence` has no
`superseded_at` to record a supersession with. And the new row formed its own
tenth packet, because `subject_key` recognised one signal type: **which
measurement was taken over a subject is not part of the subject's identity**, and
nothing else in the pipeline signals that a grouping key needs updating.

**No commercial dimension is reachable from the reviewed portfolio, and the
reason is GRAIN rather than permission.** The two `public_procurement` sources
are collector-capable and publish subject vocabularies that do not name products
-- TED's own packet key is literally `ted-eu:CPV-division:90` -- while every
product-grain source (`github`, `product-hunt`, `apple-app-store`, `google-play`,
`steam`) is `RESTRICTED`. So the next step is a desk review of what the registry
can express, not an acquisition: acquiring first produces Evidence in its own
packet that can never join `subject:docker`.

**RawRecords and NormalizedRecords unchanged at 148**, 0 model calls, 0.00 USD,
no Opportunity revision (`OPPORTUNITY_REVISION_NOT_YET_WARRANTED`), no score, no
rank, and problem-family inference stays **PARKED** -- 54 unaccepted Docker
questions invite *how many are the same problem?*, which is exactly the parked
relation.

### The first Opportunity exists, and it is a hypothesis that says what it lacks

Added in 1.59 (Mission 1.31.1, `mission-1.31.1-report.md`,
`opportunity-synthesis-run-v1.1.json`). **`FIRST_OPPORTUNITY_HYPOTHESIS_CREATED`**:
one Opportunity, one revision, seven Evidence links, all at `ELIGIBLE_CONTEXT`.

    Opportunity 06113a8b  ->  revision 1  ->  7 Evidence links
    status OPPORTUNITY_HYPOTHESIS, packet c25451c5, use profile local-private-research-v1

- **A re-run is legitimate when the PROCEDURE changed and the question did not.**
  The packet, the evidence, the schema and the prompt were byte-identical --
  `synthesis_prompt_hash()` still returns the hash Mission 1.31 recorded -- and
  only the audit differed. Mission 1.31's verdict stands under `audit@1.0.0` in
  its own artifact; this run wrote a new one. **Neither rewrites the other.**
- **A term can be the SUBJECT of its own denial.** `guard@1.1.0` cleared a denial
  marker appearing BEFORE a term, which left *competitors are not established by
  the evidence* flagged. `@1.2.0` adds `<term> (is|are|was|were|has|have|had)
  (not|never|no)`, cancelled by an intervening comma or contrastive word -- so
  *buyers would pay, which is not established* still fails. Order alone was not
  enough; grammar was.
- **A guard that matches on a token boundary must not confuse the boundary with
  the token.** `_phrase_position` returned `match.start()`, which pointed at the
  character captured before the word so that `supermarket` cannot match `market`.
  Every term not at the start of a sentence had its tail misaligned by one byte.
- **The two runs agree on every structural judgement**, which is the strongest
  available evidence that the earlier rejection was a guard defect rather than a
  model failure: same `UNKNOWN_NOT_SUPPORTED` actor, same twelve unsupported
  dimensions, same seven citations, `commercial_claims_supported` empty in both.
- **`market_scope` is GLOBAL and that is not a market claim.** The column is NOT
  NULL and the packet establishes no geography; Ontology V2 §4 defines GLOBAL as
  the ABSENCE of a geographic restriction. The limitation is persisted on the
  revision so a reader cannot take it for the other thing.
- **The hypothesis says what it lacks, in the row.** Twelve unsupported
  dimensions and five limitations are stored as arrays, not prose: NON_SCORABLE
  and MISSING_RELIABILITY on every row; independence UNKNOWN and two families is
  not two independent sources; the question count is of questions and not of
  people and not evidence any two share a problem; two of six Wikimedia rows are
  DECREASES and the calendar does not cancel.
- **A global row count becomes deployment state the moment it can legitimately be
  non-zero** (`testing-strategy.md` §68). Four TED tests asserted
  `research.opportunities == 0`; they now assert that no Opportunity hypothesis
  cites TED Evidence, which is deployment-independent and catches more.

**Nothing was scored or ranked**, `scoring.scores` still does not exist, every
supporting row is still `NON_SCORABLE`, D-03 is untouched, and problem-family
inference stays PARKED.

### The synthesis path works, and a guard that cannot see negation does not

Added in 1.58 (Mission 1.31, `mission-1.31-report.md`,
`opportunity-synthesis-run-v1.json`). The first bounded Opportunity synthesis ran
against the real `docker` packet through the approved route.
**`OPPORTUNITY_SYNTHESIS_OUTPUT_REJECTED`**, and the rejection was mine.

- **A forbidden term under a DENIAL is not an assertion.** The model wrote *"No
  statement in the packet establishes ... whether anyone would pay, whether
  competitors already serve this space"*, which is the enumeration of absences
  §6 and §16 require. `opportunity-claim-guard@1.0.0` flagged `would pay` and
  `competitors` and refused the output. `@1.1.0` clears a term when a denial
  marker precedes it **in the same sentence**, and only then: scope is one
  sentence, a marker after the term does not clear it, and the marker list is
  narrow.
- **When a guard rejects something you believe is correct, fix the guard and KEEP
  the verdict.** The run keeps `audit@1.0.0`, no Opportunity was persisted, and
  the corrected guard reaches the next mission. §12 forbids weakening a gate
  after seeing the answer, and this was identified as a defect *because* it
  rejected an answer that looked good -- which is exactly the reasoning that rule
  distrusts. Doing both is what makes the fix credible.
- **Bounding an output below what the requested schema can serialise is a defect,
  not a discipline.** Two attempts were abandoned because the cap was 1500 and
  the 17-field schema admits about 1800 tokens. Mission 1.27's lesson stands; the
  arithmetic is now done against the schema. Raising a transport bound and
  re-running is not retry-shopping, because no answer existed to reject -- and
  both wasted attempts are counted in the artifact.
- **The synthesis itself did the hard part.** `target_actor_if_supported` came
  back `UNKNOWN_NOT_SUPPORTED` rather than an invented persona; the intervention
  is a CLASS, "not a defined product or feature set"; the pageview evidence is
  restated as day-to-day FLUCTUATION rather than growth, which is right because
  two of the six rows are decreases; `commercial_claims_supported` is EMPTY; and
  the model independently wrote that the question count is *a count of questions,
  not of people* and *not evidence the questions share a single problem* --
  arriving at the boundary Mission 1.27 parked without being told.
- **Authorization resolved before serialization**, the transmitted payload was
  the nine-key Mission 1.29 allowlist and nothing else, and the prompt kept its
  regions apart with every claim statement as `UntrustedText` labelled by its
  Evidence and Claim ids.
- **The whole frozen gate ran and only one clause failed.** Ids all belonged to
  the packet, every Evidence was cited with its Claim, no dimension was
  over-claimed, all eleven mandatory unsupported dimensions were reported,
  independence stayed UNKNOWN and reliability stayed NON_SCORABLE.

**0 Opportunities, 0 scores, counters unchanged, problem-family still PARKED.**
A persisted hypothesis would still contribute to no score: every row is
`NON_SCORABLE` with `MISSING_RELIABILITY`, and D-03 is untouched.

### A count is complete or it is refused, and a subject may span two vocabularies

Added in 1.57 (Mission 1.30, ADR-034, `targeted-evidence-completion-v1.md`,
`canonical-subject-registry-v1.json`). **`TARGETED_EVIDENCE_COMPLETION_SUCCESS`**:
the `docker` packet is HYPOTHESIS_FORMABLE and AVAILABLE_FOR_EXTERNAL_SYNTHESIS,
on 7 Evidence rows across two source families carrying two counting dimensions.

- **A TRUNCATED COUNT IS NOT MERELY IMPRECISE, IT IS ANTI-INFORMATIVE.** If a
  retrieval capped at 100 returns 100, the magnitude is OUR BOUND and says
  nothing about the world -- and it reads as a LARGER number than a complete
  count of 88. So completeness is a PRECONDITION and never a caveat: the
  extractor refuses rather than qualifying, which is ADR-021's rule applied to a
  failure mode counting introduces and change never had.
- **A short page is the proof.** Mission 1.20 ran one page with `page_size = 100`
  and got 89, so the result set was exhausted. The caller supplies the page size
  as a PARAMETER and the extractor does the reasoning: a caller handing over a
  number is doing something a caller handing over a verdict is not, and the
  number enters the derivation fingerprint.
- **What the query asked and what the source says are different facts.** One of
  the 89 records came back from `tagged=docker` carrying no `docker` tag at all.
  The count is of questions **carrying the tag** (88), because the Claim says
  *carrying the site's own tag* and the tag list is the site's own vocabulary. It
  also means Kubernetes cannot borrow that evidence: its two held questions
  arrived through a Docker query and are a biased subset, not a count.
- **The minimum needed was ZERO, and that is a result rather than a shortcut.**
  §7 says collect the minimum and prefer fewer. A complete set already existed
  for one subject, so no acquisition happened -- RawRecords and NormalizedRecords
  are unchanged at 148 while Signals, Claims and Evidence went 26 -> 27.
- **A fifth quantity family, because the near miss was the danger** (ADR-034).
  `CONTENT_REQUEST_VOLUME` would have fitted field for field. **A request is
  something a READER makes of a server; a question is something a PERSON
  publishes about being stuck.** Widening it would not have cost a FIELD its
  meaning, it would have cost the FAMILY its meaning, and every consumer
  branching exhaustively on it would have treated the two alike without deciding
  to. `PROBLEM_VOLUME`, `USER_PAIN_VOLUME` and `COMMUNITY_DEMAND` were available
  names and all are wrong: a family named for problems would make the PARKED
  relation look answered by a count.
- **The new kind supplies the temporal facts and NOT `EXACT_NUMERIC_VALUE`.** A
  question carries no measured value, so `_TEMPORAL_KINDS` is separate from
  `_COUNTING_KINDS` -- the same subset-becoming-equality trap Mission 1.19
  avoided one family earlier.
- **`PROBLEM_OR_NEED`, and `RECURRENCE_OR_FREQUENCY` REFUSED.** A published
  question is a person saying they are stuck, which is what the first dimension
  asks. The second is the mapping a reader most wants and it needs to know the
  questions concern the same problem -- the PARKED relation -- so claiming it
  would recreate `SAME_PROBLEM_FAMILY` under another name.
- **A canonical subject registry may join two vocabularies; a classifier may
  not.** `SubjectKey` starts with the source id, so packets were source-scoped by
  construction. The registry maps EXACT rendered keys with a stated basis per
  entry, matched by equality and nothing else -- no distance, no token overlap,
  no stem, no synonym table, no threshold. **It asserts that two IDENTIFIERS name
  the same SUBJECT**, decided once by a person reading two pages; it does not
  assert that two OBSERVATIONS express the same problem. It records what it
  refuses too: nothing unites Docker, Podman and Kubernetes, and `docker-compose`
  is not folded into `docker`.
- **Nothing else moved.** The sufficiency rule is still
  `opportunity-sufficiency@1.0.0`, `TREND_OR_CHANGE` still does not count, the
  new row is `ELIGIBLE_CONTEXT` with reliability NULL, `eligible_scoring` is
  still 0, and independence is still `UNKNOWN` on all seven rows -- **two source
  families is diversity, not established independence.**

**Formable is not scoring-ready and not an Opportunity.** 0 Opportunities, 0
model calls, 0.00 USD, and problem-family inference stays PARKED.

### Opportunity synthesis egress — three sources open, one unrecorded

Added in 1.56 (Mission 1.29, `opportunity-synthesis-egress-governance-v1.md`).
**`OPPORTUNITY_SYNTHESIS_EGRESS_PARTIALLY_READY`.** The processing purpose
assessed is **bounded external inference for Opportunity hypothesis synthesis**,
under `local-private-research-v1`, and a different purpose is a different
assessment.

| source | decision | why |
|---|---|---|
| `wikimedia-pageviews` | **PERMITTED** | CC0 1.0 waives everything, database rights by name |
| `world-bank` | **PERMITTED_WITH_CONDITIONS** | CC BY 4.0 §2(a)(1); **CC-BY-4.0 only**, not ODbL |
| `gdelt` | **PERMITTED_WITH_CONDITIONS** | its grant covers datasets it RELEASES, not article text |
| `ted-eu` | assessed UNCLEAR, **not recorded** | recording it would have broken acquisition |

- **`reproduce` and `Share` are two granted acts, and only one is limited.**
  CC BY 4.0 §2(a)(1) grants *"reproduce and Share the Licensed Material"*; §1
  defines Share as providing material *"to the public"*; §3(a)(1) triggers
  attribution only *"If You Share"*. A contracted processor performing inference
  for one operator is not the public, so a transmission is reproduction, which is
  granted outright and carries no credit obligation. Attribution still happens,
  because every Claim statement names its source in its own wording -- a property
  the data has, not a mitigation applied at transmission.
- **A transmission allowlist may be TIGHTER than an acquisition allowlist**, and
  here it is. Acquisition permits CC-BY-4.0 or ODbL-1.0; transmission permits
  CC-BY-4.0 alone, because ODbL's share-alike attaches to Derivative Databases
  and its *Publicly Use* definition is unanswered. No ODbL resource is held, so
  the narrowing costs nothing now and stops a later dataset inheriting a
  permission nobody assessed.
- **A grant's SUBJECT bounds it.** GDELT permits *"unlimited and unrestricted
  use ... of any kind"* over *"all datasets released by the GDELT Project"* --
  which are ngram aggregates. **Third-party news article text is not a
  GDELT-released dataset**, so it is a prohibited representation. No article text
  is held, so the bound constrains a future collector, which is exactly when a
  scope limit is worth writing down.
- **An obligation attached to USE is live where one attached to SHARING is not.**
  GDELT requires citation on *"any use or redistribution"*; CC BY 4.0 requires it
  only on Sharing. Two licences, two different answers to the same transmission.
- **RECORDING A DECISION IS NOT FREE.** TED's `UNCLEAR` required appending a
  review version, and appending one orphans the operator's acceptance of
  `ted-database-right-residual-exposure-accepted` -- a `HUMAN_CONFIRMATION`
  condition **no verifier may satisfy, by design**. Verified against the real
  deployment: with the new version in place, `build_authorization('ted-eu')`
  refused and TED stopped being acquirable. Mission 1.29 §0 forbids letting a
  transmission assessment rewrite acquisition eligibility, so the append was
  **withdrawn**. `NOT_ASSESSED` and `UNCLEAR` both refuse at the gate, so nothing
  operational was traded away; the distinction lives in the governance document,
  with **H-39** named and the operator's acceptance sentence written down.
  **Writing it down is not recording it**, exactly as in Mission 1.15.6.
- **A source whose approval rests on a HUMAN decision cannot be cheaply
  amended.** The other three sources' conditions are CAPABILITY-verified, so a
  version bump costs a re-check and nothing else. That asymmetry is invisible
  until a mission tries to amend one.
- **UNRESOLVED is not REFUSED.** `UNCLEAR` and `NOT_ADDRESSED` had no refusal code
  of their own and reported as a decision against. An operator can close an open
  question and cannot argue with a decision, so
  `SOURCE_EXTERNAL_MODEL_TRANSMISSION_UNRESOLVED` now names them -- the argument
  ADR-033 made for `NOT_ASSESSED`, one state further along.
- **The permitted representation is an ALLOWLIST enforced in the serializer.**
  `opportunity-transmission-representation@1.0.0`: nine permitted top-level keys,
  named prohibited representations, personal-data markers checked at every depth.
  An unrecognised key refuses, because a denylist is a list somebody must remember
  to extend. A payload exceeding it is **refused rather than trimmed** -- a
  trimmed payload is a different packet from the one the decision authorised.
- **No raw source payload is transmitted at all.** The packet carries internal
  ids, procedure versions, source-native subject keys, dimension names, this
  repository's own bound sentences, and Claim STATEMENTS it composed. No collected
  record, no API response body, no article text, no notice payload, no personal
  data.
- **Governance authorization never changes epistemic meaning.** A permitted
  Wikimedia request count is still not a reader, a customer, demand or adoption;
  a permitted World Bank population change is still not market demand; a permitted
  GDELT term count still never satisfies a demand claim.

**8 of 9 packets are egress-authorized and 0 are formable.** Permission to send is
not evidence, the two gates stay separate, and a test asserts it.

### The Opportunity Engine exists, and it correctly forms nothing yet

Added in 1.55 (Mission 1.28, `opportunity-engine-foundation-v1.md`,
`mission-1.28-report.md`). **`OPPORTUNITY_ENGINE_READY_BUT_CURRENT_EVIDENCE_INSUFFICIENT`.**

```text
Evidence -> facets -> dimension mapping -> eligibility -> subject grouping
         -> packet -> sufficiency -> [ external synthesis gate ] -> hypothesis
```

Everything before the gate is deterministic, versioned and reaches no network and
no model. `packages/opportunity-engine` depends on `sros-contracts` and nothing
else -- not on `sros_acquisition`, because an engine able to read the source
registry could decide its own authorization; not on the Gateway, because a
package that cannot import a provider cannot call one by accident; not on
`sros_semantic_equivalence`, asserted over the AST.

- **An Opportunity here is a HYPOTHESIS, enforced by a CHECK constraint.**
  Migration 0029's `status` admits `OPPORTUNITY_HYPOTHESIS`,
  `HYPOTHESIS_WITHDRAWN` and `HYPOTHESIS_SUPERSEDED`. `VALIDATED_OPPORTUNITY`,
  `PROVEN_MARKET`, `WINNING_IDEA`, `PRODUCT_MARKET_FIT` and
  `HIGH_CONFIDENCE_BUSINESS` are not members, in the enum or in the database: a
  state that does not exist cannot be reached by a caller passing a string.
  `unsupported_dimensions` is required non-empty, because a record listing only
  its support is a sales document.
- **A dimension travels with the sentence that bounds it.** A mapping that
  assigns dimensions and states no `bound` is refused at construction. A
  Wikimedia request is not a reader, a TED BT-161 total includes options and
  renewals and is never willingness to pay, and GDELT lexical frequency maps to
  **nothing at all** -- it measures what media organisations PUBLISHED, which is
  producer behaviour and not audience behaviour, so it is not even
  `AUDIENCE_OR_USAGE`.
- **Zero dimensions is a real answer, and `None` is a different one.** A
  registered signal type mapping to `frozenset()` is a decision with a rationale;
  an unregistered type returns `None` and lands in `REQUIRES_REVIEW`, because
  nobody has decided what it bears on.
- **`TREND_OR_CHANGE` never counts toward evidence diversity.** A Signal in this
  repository IS a derivation over two or more observations, so every Evidence row
  carries change by construction, and a dimension the whole corpus has separates
  nothing. Counting it would let one measurement repeated six times look like two
  kinds of evidence. The qualifier was chosen with the corpus visible, so both
  counts are reported and it decides a label rather than the outcome.
- **`ELIGIBLE_CONTEXT` is not a weaker `ELIGIBLE_SCORING`.** Nothing promotes
  across the line: no threshold, no override, no `force_scoring` parameter, and
  the only route to scoring is a reliability a reviewed assessment resolved. All
  26 rows are context-only today.
- **Grouping is by exact source-native subject and by nothing else.** Docker,
  Podman and Kubernetes are three packets. Merging them would be a
  `SAME_PROBLEM_FAMILY`-shaped judgement reached by hand instead of by the
  classifier Mission 1.27 parked -- and **doing it deterministically would not
  make it deterministic, it would make it unargued.** No string distance, no
  token overlap, no stem, no synonym table, no threshold.
- **A packet holds references, never copied truth**, and `packet_id` is sha256
  over the procedure versions and the ordered evidence ids -- reproducible, and
  excluding the construction time for the reason `observation_key` excludes the
  retrieval time.
- **A packet never says "multiple independent sources".** Every row here is
  `UNKNOWN`, six rows about one article are six observations of one stream, and
  the phrase is structurally unreachable.
- **A packet is authorised whole or not at all.** One untransmittable source
  makes it `UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS`; it is never silently trimmed,
  because a packet that dropped a source and still called itself the packet would
  let a model reason over a corpus a report described differently. Authorization
  is resolved BEFORE serialization, so a refused packet leaves no string
  containing source-derived text.
- **Each forbidden commercial term names the dimension that would license it**,
  so a refusal says which evidence is missing rather than which word was typed.
  `TAM`, `market size`, `MRR` and `product-market fit` are licensed by nothing at
  all. Matching is over tokens: `supermarket` is not `market`.

**THE CORPUS FAILS SYMMETRICALLY, AND THAT IS THE FINDING.** Nine packets, none
formable. The one with commercial dimensions -- TED, CPV division 90, carrying
`MARKET_ACTIVITY`, `BUYER_OR_BUDGET_EXISTENCE` and `ECONOMIC_VALUE` -- holds ONE
row. The three with six rows each hold ONE counting dimension. **SROS's evidence
is deep where it is narrow and broad where it is shallow**, and nine of fourteen
dimensions are answered by nothing.

**THE SECOND BLOCKER HAS NOTHING TO DO WITH THE EVIDENCE.** Under
`local-private-research-v1`, `external_model_transmission` is **NOT_ASSESSED** for
`wikimedia-pageviews`, `world-bank`, `gdelt` and `ted-eu` -- every source that
contributes Evidence -- and `PERMITTED_WITH_CONDITIONS` for `stack-exchange`
alone, which contributes none. **The one source cleared to leave this deployment
is the one source with nothing to send.** Mission 1.23 assessed egress for the
source Mission 1.24 was about, and the Opportunity Engine needs the other four.
No coherent packet could have reached a model whatever the evidence looked like,
which is why the run cost nothing.

**No ranking, no score, no weight, no leaderboard** (§15), asserted over the AST.
Scoring stays blocked by D-03 and is a different blocker from this one:
formability never required scoring-eligibility.

### Problem-family classification is PARKED, and production stays closed

Added in 1.54 (Mission 1.27, `mission-1.27-report.md`). Three V2 variants were
built, one was selected by a rule frozen beforehand, frozen, and run once on the
Mission 1.26 holdout. **`EXPLORATORY_V2_NOT_PROMISING`**: 0 provisional true SAME
against 4 provisional SAME references, where the frozen criterion required 2.

- **V1 was not failing to SEE the abstraction.** Its own rationale on a pair a
  human called SAME reads *"both involve a client failing to reach a service
  running inside a Docker container, but the specific blocked goals differ"*. It
  wrote the shared abstraction down and rejected it, and that is demonstrated
  behaviour rather than a hypothesis about a prompt.
- **The most informative artifact was an empty field.** V2 required the model to
  name an abstraction covering both questions before deciding.
  `shared_problem_if_any` came back empty on 39 of 40 evaluations. The model is
  not rejecting candidate abstractions; it is not generating them.
- **More scaffolding made it more conservative.** Adding the shared-abstraction
  requirement dropped true positives to zero; adding a permissive reminder on top
  restored the baseline and no further.
- **A selection rule must defeat BOTH collapses.** One that only demands a
  positive is passed by a classifier saying SAME to everything; one that only
  forbids false positives is passed by a classifier that never says SAME. The
  frozen rule demands a true positive AND caps the SAME share, and tests score
  both degenerate classifiers.
- **A ceiling you might exceed is bounded, not argued away.** The first hard
  maximum was 4.44 USD against a 3.00 ceiling, because the estimate assumed the
  adapter's 4096-token output default. Capping output at 1200 -- the schema
  allows 1080 characters -- made the bound real at 1.89 USD.
- **A split disjoint by PAIR is not disjoint by OBSERVATION.** Over a fixed
  corpus it cannot be, so a prompt example drawn from development can still carry
  holdout content. Mission 1.27's suggested illustration was the exact
  abstraction of a holdout pair and was refused; a test asserts no prompt names
  any corpus question id.

**PARK_PROBLEM_FAMILY_CLASSIFIER.** No V3. The project moves toward the
Opportunity Engine over evidence paths already valid -- SROS holds 26 canonical
Evidence rows from other source families -- while this relation stays
NOT_AUTHORISED. Genuinely human reference labels remain required before any
production claim, and are now the second condition rather than the first: on this
evidence a classifier worth validating does not yet exist.

### A reference set is built before the classifier that will be scored on it

Added in 1.52 (Mission 1.26, `problem-family-human-reference-v1.md`). A DATASET
mission with no model call, no classifier and no evaluation.

**Ten human-scored pairs with two positives can reject a trivial classifier and
cannot build one.** Mission 1.25's did reject one. Developing against two
positives is fitting to two examples, and evaluating against two is measuring
nothing with an interval.

- **A dataset selected by a classifier's errors can only ever measure that
  classifier.** The obvious way to build a second reference set is to show the
  reviewer the pairs V1 got wrong; the result can never score anything again.
  So the sampler reads frozen candidate features and NOTHING from any run --
  enforced by parsing its code with docstrings excluded, because the module says
  *not a prediction, not a confidence* precisely because it reads neither.
- **Strata are sampling mechanisms, never expected labels.** They name what two
  questions share lexically, which is exactly what a reviewer is needed to look
  past. A band called SAME-ish would be a label leaking into a sampler.
- **An enriched sample may develop and evaluate; it may never state a
  prevalence.** Bands are drawn at deliberately unequal rates, so the proportion
  of any label in the set estimates nothing. The warning rides on the dataset
  object so a report cannot omit it by forgetting.
- **The split is frozen before any label exists, and assigned WITHIN each band**
  so neither partition is short of a question shape. A split decided later --
  however honestly -- is one that could have been decided to help.
- **Holdout isolation is structural, not conventional.** The two splits' labels
  live in separate FILES; `load_development_labels` cannot reach a holdout label
  because it does not open that file. A `split` column would place both a metre
  apart and rely on every caller filtering correctly, which is a rule, and rules
  get forgotten by whoever is in a hurry.
- **Provenance is mandatory on load with no default.** A label file without a
  declared origin is refused rather than assumed human.
- **`HUMAN_OPERATOR` is human ground truth and is not expert ground truth.** The
  system does not establish expertise and it is not ours to assert on someone's
  behalf. Wording is *human operator reference*, never *expert review*.

**The set was labelled, and the gate failed** (Mission 1.26 close). The 40 labels
came back `AI_ASSISTED_PROVISIONAL` rather than human, and the development split
holds 2 positives against a preregistered threshold of 4:
**`REFERENCE_SET_INSUFFICIENT`**, with the human reference requirement separately
**NOT_ESTABLISHED**. Nothing was moved to make either pass. The provisional set
is usable for EXPLORATORY development work and is not validated holdout evidence,
so **production problem-family inference stays NOT_AUTHORISED** and a backlog
item blocks the word *validated* until genuinely human labels exist.

**A complete dataset is not an answer.** `DATASET_PREPARATION_COMPLETE` says the
next question can be asked well; it says nothing about whether any classifier can
find a problem family.

### Problem-family inference — implemented, evaluated, and it did not pass

Added in 1.50 (Mission 1.25, `problem-family-rubric-v1.md`,
`mission-1.25-report.md`). A SECOND relation, never a looser first one.

**`EXACT_ACTIONABLE_EQUIVALENCE` and `SAME_PROBLEM_FAMILY` are different
questions**, held apart by `relations.py`: different rubrics, reason codes,
prompts, criteria and propositions, and a `relation` field on every artifact
because two pairwise judgements with different meanings and the same shape are
indistinguishable in storage without one.

    SAME_PROBLEM_FAMILY  =/=>  EXACT_ACTIONABLE_EQUIVALENCE
    SAME_PROBLEM_FAMILY  =/=>  same root cause, same fix, the same bug
    SAME_PROBLEM_FAMILY  =/=>  permission to merge records
    EXACT_ACTIONABLE_EQUIVALENCE  =/=>  a source-native duplicate

- **The relation changed rather than a threshold.** Mission 1.24 found its own
  question hard to label for a structural reason -- *would the fix transfer?*
  needs the fix -- and loosening it would have kept that requirement while
  answering more permissively. The family question asks what each person was
  trying to do and what stopped them, which is answerable from published text.
- **A criterion must be unpassable by a constant classifier.** `min_true_same`
  requires a demonstrated positive in the SCORED split, so answering DIFFERENT to
  everything -- or ABSTAIN to everything -- fails by construction.
  `defeats_a_constant_classifier` computes the property from the numbers rather
  than asserting it in prose, and tests score both constant classifiers.
- **A provenance-aware re-scoring is an ADDITION, never a rewrite.** When the
  operator reviewed Mission 1.25's frozen holdout, the frozen predictions were
  re-scored with no model call and nothing frozen touched, and the provisional
  result was preserved beside the new one. **A split may reach human ground truth
  while its siblings have not**, so a reference set can be MIXED -- and a mixed set
  is never reported as human.
- **An AI-assisted reference can be wrong in the generous direction.** On that
  holdout the human moved TOWARD the model on three of five changed labels, halving
  the apparent miss rate. A conclusion drawn about a classifier from a provisional
  reference is partly a conclusion about the reference.
- **A reference label carries its ORIGIN.** `AI_ASSISTED_PROVISIONAL` labels are
  usable for scoring and are not ground truth; `human_ground_truth_established`
  is true only when EVERY label is human, and the origin rides on the RESULT
  because a result is what gets quoted.
- **Candidate recall is shared and only ORDERING is versioned.** The qualifying
  predicate is imported rather than restated, with a test asserting both
  relations consider the same pairs. For the family ordering a shared diagnostic
  weighs ZERO -- not a small constant, which would claim it contributes a little
  when Mission 1.20 refutes that -- and tags are weighted by the RAREST shared
  one, because summing rewards sharing a whole stack. **Rarity measures
  specificity, not concern**, and that limit is stated rather than hidden.

**THE EVALUATION FAILED, AND THE FAILURE IS INFORMATIVE.** 20 pairs, 0.38 USD, 4
`SAME_FAMILY` references in the scored holdout -- and **zero** of them found. The
model said SAME once in twenty, on the rubric's own quoted example. Zero false
positives again, and again nearly free.

**Every disagreement is one-directional**: the model refusing a family the
reference asserted, never the reverse. Either the rubric is too strict or the
reference too generous, and **this evaluation cannot separate them** -- the
rubric and its reference even disagree about the rubric's own borderline example,
with the model siding with the rubric. That is a question for a person, and no
rerun answers it.

**The rubric was NOT widened after seeing the results**, and the criterion was
not altered. Mission 1.24 kept a rule in the flattering direction; this is the
same discipline in the costly one.

### Reference labels are not automatically human, and the contract says which

Added in 1.49 (Mission 1.25 §0). Placed immediately after the semantic-equivalence
invariant because it corrects a claim that invariant made.

**Mission 1.24's 40 reference labels were supplied `AI_ASSISTED_PROVISIONAL` by a
different assistant, not by an independent human domain expert.** The repository
described them as human labels, in a filename, a section heading, a type name and
a `reviewer` field naming a person who did not make the judgements. Every label,
prediction, cost and outcome is unchanged -- the error was in the DESCRIPTION,
and it was the most misleading thing this repository had said.

- **`ReferenceOrigin` is required on every label and never defaulted.**
  `HUMAN_EXPERT`, `HUMAN_NON_EXPERT`, `AI_ASSISTED_PROVISIONAL`. Only the first
  two establish ground truth, and `human_ground_truth_established` is true only
  when EVERY label in a set came from a human -- all, not any, because a mixed
  set told a reader `True` would be read as unmixed.
- **The origin is recorded on the RESULT, not only on the labels.** A result is
  what gets quoted, and an outcome read without its reference origin is an
  outcome read as truth. Every evaluation scored against a non-human reference
  carries a note saying so in its own output.
- **A provisional reference is still useful and still not truth.** Mission 1.24's
  was written blind, before any model call, and was never sent to the classifier.
  That is what makes it valid for scoring. What it measured is **agreement
  between two assistants**, which is a real finding and a different claim from
  accuracy.
- **`human_ground_truth = NOT_ESTABLISHED`** for that set, and stays so until a
  person reviews those pairs. Disagreements between the rubric and that reference
  are **not human inter-rater disagreement** and must never be described as such.

**Mission 1.24 remains EVALUATION_INSUFFICIENT either way**, for a reason this
correction does not touch: the holdout contained no SAME label at all, so nothing
could have been measured about a SAME prediction whoever wrote the references.

### SROS has Evidence; what it lacks is validated recurring-problem evidence

Added in 1.49 (Mission 1.25 §1), correcting a second overstatement.

Mission 1.24 concluded that *SROS is not ready for cross-source convergence*
because *this mission produced no evidence*. The first clause does not follow
from the second. **SROS holds 26 canonical Evidence rows** from other source
families, so the blocker is not an absence of Evidence in general.

**The precise gap is: no validated recurring-problem semantic evidence from Stack
Exchange.** And even that is bounded twice over -- to EXACT actionable problem
equivalence, and to one candidate set. **Nothing in Mission 1.24 establishes that
Stack Exchange cannot contribute recurring problem-FAMILY evidence**, which is a
looser relation nobody has evaluated.

The general rule this is an instance of: **a finding about one relation over one
bounded set is not a finding about a source, and a finding about a source is not
a finding about the system.** Each widening needs its own evidence.

### Model inference execution — where it may run, and when content may leave

Added in 1.47 (Mission 1.23, ADR-033,
`model-inference-execution-governance-v1.md`). Placed after route binding because
it is the same shape one layer out: a permission to USE is not a permission to
SEND.

**`model_processing` and `external_model_transmission` are different questions.**
The first asks whether a model may READ the material; the second asks whether the
material may LEAVE this deployment so that a THIRD PARTY's model can read it.
Different exposure, different counterparty, different instrument deciding it.
Reinterpreting the first to cover the second would grant every registered source
a permission nobody assessed.

- **Four gates, all required, evaluated before any source text is serialised.**
  The source's review must permit the transmission for that profile; the profile's
  `external_model_egress` must permit the class of egress; the provider's reviewed
  posture must be `APPROVED`; and that provider must actually be configured.
  `authorize_external_inference` is the single place the source domain and the
  provider domain meet.
- **Every gate reports even after one refuses**, with its own reason code. An
  operator told only the first failure fixes it and is refused again, once per
  remaining gate — and four gates collapsed into one boolean is how a governance
  decision comes to look like an outage.
- **`NOT_ASSESSED` is a state and not a default that decides.** Both new fields
  distinguish *nobody looked* from *somebody looked and said no*. Both refuse; one
  is a decision that can be cited and the other is an open question, and the
  registry exists to keep them apart. Every review written before ADR-033 reads
  `NOT_ASSESSED`, truthfully.
- **This is NOT one of rule 8's six materially required activities.** It gates one
  operation. A deterministic acquisition never fails because nobody assessed model
  egress for its source, and that property is asserted over every registered
  source rather than assumed.
- **A provider is approved on its own contract text**, never on preference, and
  the ROUTE is what is assessed: a vendor's paid and unpaid routes are different
  assessments, and one being reviewed says nothing about the other. Postures live
  in `model-provider-policy-v1.json`, so a provider changing its terms changes a
  data file rather than code.
- **No source review names a vendor.** A review states the PROPERTY a provider
  must have — no training on submitted content, documented bounded retention.
  Naming a company would put provider governance inside the source registry and
  force a re-version every time a provider list changed.
- **Appending a review version invalidates its verifications, and that is
  correct.** A compliance configuration is pinned to a review version, because a
  re-review can change what a condition means. Bumping the number is honest only
  when the `required_conditions` set is unchanged — assert that equality, do not
  assume it. A review version is not free, and a mission that bumps one owes the
  re-check.
- **The boundary is CLOSED today.** No provider is configured, so nothing can be
  sent, and the refusal says `PROVIDER_NOT_CONFIGURED` by name rather than by
  silence. Configuring one is an operator act performed outside this repository:
  **no credential is committed, fabricated, or pasted into a tracked file.**

### A condition is verified where it can be, and confirmed where it cannot

Added in 1.31. **An objective property of what a collector is CONFIGURED to do
belongs to a mechanical verification kind, not to a person.**

Writing one as `HUMAN_CONFIRMATION` creates a **bootstrap**: nothing can be
authorised until somebody confirms behaviour, and nobody can confirm behaviour
until the thing exists. TED sat in that loop for a mission with two such
conditions, and the loop's natural break is the wrong one -- write the collector
first, confirm it after.

**The boundary is unchanged and load-bearing.** A judgement, a risk acceptance,
a legal conclusion or a promise about future conduct stays `HUMAN_CONFIRMATION`,
and `source-review-guide.md` §9 still applies: *do not reword a legal obligation
until it sounds checkable -- that produces a verifier that checks something
else.* The new rule is upstream of it: **ask first whether the condition was
ever about a legal obligation at all.**

**What a configuration-verified condition establishes** is stated precisely,
because the distinction is the whole point: not *the collector follows the
rules*, which nothing here can establish, but *the configuration supplied to
authorization satisfies the policy constraints, and the authorization hands a
collector nothing else*. The remaining obligation is on the collector mission --
it must be built so it cannot execute without an authorized configuration.

### Claim taxonomy — exactly five values, UPPERCASE

```text
OBSERVED | INFERRED | PREDICTED | RECOMMENDED | HYPOTHESIS
```

`HYPOTHESIS` is mandatory and first-class. Definitions in
`opportunity-ontology-v2.md` §7. Closed enum: changing it requires a new
ontology version and an ADR.

### Confidence — unit interval

```text
0.0 <= confidence <= 1.0
```

Applies to `confidence`, `reliability`, `independence`, probability and signal
`value`, in the database, in API and domain contracts, and in ML calculations.
Presented to users as a percentage (`0.82` → `82%`).

**Scores are a different quantity** and keep 0–100 semantics. `evidence_level` is
an integer 0–5 and is never rescaled. Never conflate score, confidence,
probability and evidence strength — see `scoring-framework-v1.1.md` §4.1 and
`opportunity-ontology-v2.md` §9.

Naming rule: a field named `confidence` is always `[0,1]`; a field named
`*_score` is always `0–100`.

### Research lifecycle — canonical names

```text
Workspace → ResearchProject → ResearchSession → Evidence / Signals / Opportunities
                                    |
                                    +-- ResearchContext snapshot (immutable)
```

`ResearchSession` is the **only** persisted execution entity. `ResearchContext` is
an input specification (a value object), stored as an immutable snapshot on the
session. `ResearchProject` is the persistent grouping.

**`research run` is retired.** Use `ResearchSession` / `research_session_id`. In
historical documents and accepted ADRs, "research run" means `ResearchSession`
and `run_id` means `research_session_id`. See Ontology V2 §11.

### Market scope

`MarketScope` is a closed discriminated union on `type`:
`GLOBAL | REGION | COUNTRY | MULTI_COUNTRY`. Countries are ISO 3166-1 alpha-2;
regions come from a controlled registry. `COUNTRY` carries exactly one country,
`MULTI_COUNTRY` two or more. See Ontology V2 §4.

### Taxonomies — registries, not database enums

Product Type, Market Type, User Motivation, User Behavior, Value Proposition,
Retention Mechanism, Monetization Model, Distribution Channel, Risk and Region are
**extensible registries**. Adding an entry must never require a migration.

Closed enums are only: `ClaimType`, `MarketScope.type`, demand signal family,
`EvidenceLevel`, `ResearchSessionStatus`, and lifecycle values requiring
exhaustive branching. See Ontology V2 §14.

### Tenancy — workspace-scoped

The tenant boundary is the **Workspace**. Every primary domain resource carries
`workspace_id`, propagated explicitly through every service call, every Celery
task payload, every cache key, every vector-store filter and every log line.

`workspace_id` is never inferred, never defaulted in service code, never
reconstructed from another field. A missing `workspace_id` is an error in every
environment. See ADR-005.

**Two layers, since Mission 0.4 (ADR-012).** The explicit repository filter is
layer 1 and remains mandatory. PostgreSQL row-level security is layer 2, entered
through a transaction-local tenant context. Neither replaces the other: a
forgotten `WHERE` is caught by the policy, and a missing tenant context returns
no rows rather than wrong ones. Removing the explicit filter because RLS exists
is a regression, not a cleanup.

**Single-operator deployment is not a reason to drop either layer** (§Deployment
model). The tenant boundary costs little to keep and a great deal to re-add.

### Jobs — Celery over Redis

All asynchronous work runs through Celery with Redis as broker. There is no Node
worker tier. Delivery is at-least-once, so every job must be idempotent. See
ADR-004.

### LLM access — through the gateway only

No business service imports a provider SDK. Services request a logical tier
(`FAST_MODEL`, `BALANCED_MODEL`, `STRONG_MODEL`, `EMBEDDING_MODEL`), never a
provider or a model name. See ADR-006.

### Source governance — a gate, not a field

A source becomes collectable only by passing the eligibility gate in
`registry.source_eligibility`, never by any other route. Four rules follow, and
none of them is negotiable (`source-registry-v1.md` §1, ADR-013):

- **Public visibility is not permission.** Reachability is an access-profile
  fact; permission is a review fact; the gate requires the review.
- **Uncertainty is never permission.** Silent, unreachable or ambiguous terms
  produce `NOT_ADDRESSED` / `UNCLEAR` and leave the source `REQUIRES_REVIEW`.
  There is no path from *we could not check* to *we may proceed*.
- **An approval requires retrieved, authoritative evidence** — the source's own
  documents, operator correspondence or a recorded legal review. Never a blog
  post, a tutorial, a forum answer or model recall.
- **No credential is stored in the registry.** Access profiles carry
  configuration key names only.
- **`APPROVED_WITH_CONDITIONS` is not permission to run.** It says a collector
  MAY be designed. Every condition is a checkable row, and the gate blocks until
  all of them are satisfied — where satisfaction is environment state that a
  catalog can never assert about itself.
- **A condition is cleared by a verifier, and by nothing else** (Mission 1.4,
  ADR-016, `acquisition-authorization-v1.md`). A verification records which
  condition, which verifier, at which version, when, the result and why; a
  database trigger refuses `satisfied = TRUE` with no `SATISFIED` record behind
  it. There is no manual boolean, no catalog field and no migration that grants
  it. Results are `SATISFIED | UNSATISFIED | UNKNOWN | NOT_APPLICABLE`, only the
  first clears, and **`UNKNOWN` is never promoted**. No verifier can satisfy a
  `HUMAN_CONFIRMATION` condition, and none in this repository writes one.
- **Eligible, RESOURCE-READY, implemented and enabled are four facts.** After
  Mission 1.8 `world-bank`, `eurostat` and `gdelt` are collector-eligible in any
  environment where the capabilities are verified, and `fred` joins them wherever
  `FRED_API_KEY` is configured — it is design-eligible and blocked everywhere
  else, including CI. `sros-source enable` refuses a source with no collector,
  and the orchestrator blocks acquisition under `NO-COLLECTOR-IMPLEMENTED`
  rather than dispatching a job nothing can run.

  **`resource_ready` was separated in Mission 1.9.2**, because a source can pass
  the gate while every resource it could ask for is refused — GDELT was in that
  state for two missions and "eligible" was the most specific word available for
  it. Eurostat is in it today. `sros-source readiness` derives all four and
  stores none: a persisted copy of a derivation is what §3 of
  `source-registry-v1.md` refuses for eligibility.
- **A source-level approval is not a resource-level one.** Each dataset or
  series is authorised separately, and one whose licensing scope was never
  established is refused. A collector receives an
  `AcquisitionAuthorizationContext` or it receives nothing.

  **An unestablished rights basis is refused unconditionally** (Mission 1.9.2):
  every other rule answers a question a particular review may or may not have
  asked, and *what authorises this at all* is not one of those. Where a review
  named the families it assessed, a family outside that list is refused too —
  **"nobody rejected this" is not "a reviewer approved it"**, and
  `require_dataset_family` only ever asked whether a resource could say what it
  is.
- **How much is a governance question too** (Mission 1.9.2). A reviewed
  `max_files_per_job` bounds what one job may take from a published bulk
  dataset, refused at load time without a stated basis, and a job that does not
  state its size is refused. **Absent means no ceiling was reviewed, not that
  any size is fine.** A collector choosing its own bound would be setting its
  own permissions.
- **Coverage is potential, never permission** (Mission 1.7, ADR-017).
  `registry.source_signal_coverage` and `source_behavior_coverage` say what a
  source COULD expose. A source may cover `entertainment` and be `PROHIBITED`;
  the eligibility view reads neither table and must never start. They carry no
  weight, no score and no confidence — one would be a per-source reliability
  coefficient, which is D-03, which is blocked. Behaviour coverage reuses
  Ontology V2 §3.4's `user_behavior` rather than defining a second vocabulary.
- **Silence is the commonest blocker, and it is doing its job.** After Mission
  1.8 twenty-seven sources are registered, **five** are approving and **four**
  are eligible. Bluesky publishes an open firehose needing no API key, and
  Hugging Face publishes open endpoints with documented numeric rate limits;
  both are `REQUIRES_REVIEW`, because their terms address none of the assessed
  activities. Reachability was never the question.
- **An approving state requires a GRANT, not the absence of a prohibition**
  (Mission 1.8, `source-registry-v1.md` §1 rule 8). The assessed use names six
  load-bearing activities — `automated_access`, `api_use`, `commercial_use`,
  `storage`, `derived_analytics`, `model_processing` — and each must be
  positively permitted on authoritative evidence. `NOT_ADDRESSED` on any of them
  blocks, whatever the other five say.

  This was prose from Mission 1.0 that nothing read, until Mission 1.7 approved
  a source with four of the six unaddressed and wrote the reason down in the
  review's own notes. `validate_source_registry` enforces it now. **Do not
  narrow the assessed use case to rescue a source**: the use case describes the
  product, and a permission obtained by describing a smaller product is a
  permission for a product we are not building.

### Collection — five collectors, and what bounds them

Since Mission 1.5 the World Bank Indicators collector exists
(`world-bank-collector-v1.md`) and is the reference architecture. Since Mission
1.9.3 the GDELT WEB-NGRAM collector exists too
(`gdelt-web-ngram-collector-v1.md`), reading a published gzipped file rather than
a paginated API. Since Mission 1.15.7 the TED Search API collector exists
(`ted-eu-search-api-collector-v1.md`), posting a composed JSON body to a
documented search endpoint. Since Mission 1.18 the Stack Exchange questions
collector exists (`stack-exchange-questions-v1.md` §12), the first that reaches a
source whose positive rights come from a CONTENT LICENCE rather than a platform's
terms, and the first to perform **field minimisation through the source's own
filter mechanism** rather than after the fact. Since Mission 1.19 the Wikimedia
Analytics pageviews collector exists (`wikimedia-pageviews-v1.md` §9), the first
whose rights come from a WAIVER rather than a licence with conditions, and the
first with a **fifth gate: identity**. Five rules apply to all five and to every
collector that follows:

- **No authorization, no collection.** `collect` takes an
  `AcquisitionAuthorizationContext` as its first positional parameter, with no
  default and no overload that omits it. A collector that could build its own
  could approve itself.
- **Every resource passes `authorize_resource` before a socket opens**, and a
  refusal costs **zero** network calls.
- **No public signature accepts a URL.** A request names indicators, countries
  and years; the collector composes the path, and the host comes from the access
  profile the review approved. There is no fallback domain and redirects are not
  followed.
- **Retention and attribution come from governance**, not from the collector.
  `build_draft` has no parameter for either, so there is nothing to pass.
- **Exactly one file may import a network client**
  (`collection/transport.py`). The registry and compliance packages decide
  whether collection may happen and stay network-free.

**A source may impose its obligation on the REQUEST rather than on the output**
(Mission 1.19). Every source before Wikimedia conditioned what we may DO with the
data: attribute the material, name the licence, do not distort the meaning. CC0
imposes none of those. What the Analytics API access policy imposes is that *"The
API requires an HTTP User-Agent header for all requests"* and that clients sending
none *"may be blocked without notice"*, with the Foundation's User-Agent Policy
refusing non-descriptive defaults **by name**.

That is an objective property of collector CONFIGURATION, so it is verified by a
capability rather than confirmed by a person (ADR-028), and
`context.client_identification` carries it. **The collector asks the context
whether the identity the transport will SEND is the identity the review DECLARED,
before a socket opens.** A declaration nobody sends verifies against a document
instead of against behaviour. `None` means unasked, never unrestricted, and the
capability reports *unimplemented* rather than *satisfied* when it is absent --
the same shape `route_authorization` uses.

**Attribution can be a courtesy rather than a condition, and the two must stay
distinguishable** (Mission 1.19). CC0 1.0 contains no attribution requirement and
Section 2 surrenders the rights that would let one be imposed. A credit is still
rendered onto every record -- a derived surface should say where its numbers came
from, and `build_normalized` refuses a record with no notice attached -- but **no
condition asserts an obligation the licence does not create**. Writing one would
leave a later reader unable to tell a duty from a habit.

Identity is three separate things and confusing any two is a defect:
`observation_key` says WHICH observation, `content_hash` says WHAT the source
said, and the record id follows from both. The retrieval time is in neither — it
would make every re-retrieval look like an upstream revision. The key's parts are
**escaped**, not restricted: a source publishes what it publishes, and a key
format that refused real values would drop them (Mission 1.9.3).

Four more rules apply where a collector reads a **bulk file** (Mission 1.9.3):

- **The reviewed ceiling is the review's.** `context.authorize_job_size` decides
  how much one job may take; a collector that defined its own bound would be
  setting its own permissions, and a request one file over is refused whole
  rather than split into two permitted jobs.
- **Operational bounds are ours and say so.** Compressed bytes, decompressed
  bytes, line length, rows scanned and records kept are `INTERNAL_SAFETY_POLICY`,
  labelled as such in provenance. **Absent means unasked, never unlimited**, and
  none of them is a quota anybody published.
- **Our ceilings truncate; the source's contract discards.** Hitting a record cap
  keeps what was accepted and says which bound stopped it. A malformed row
  discards its whole file, because the contract is documented and a deviation
  means a person is needed rather than a filter.
- **The route is resolved by name.** A source with two access profiles has a
  first one, and taking it silently authorises whichever the JSON happened to
  list first — which for GDELT is the deferred DOC API.

The registry is **global**: no `workspace_id`, no RLS policy, `SELECT` only for
the runtime role. It is administered by `sros-source`, never over HTTP.

This system is not a legal decision engine and its output is not legal advice.

### Normalization — what a canonical observation is, and is not

Since Mission 1.6 the RawRecord to NormalizedRecord boundary exists
(`normalized-record-v1.md`, `world-bank-normalizer-v1.md`). One adapter, for
World Bank, and six real canonical observations.

**This layer renames and reshapes. It does not decide.** Normalization answers
*what does this source observation structurally represent*, and stops. A field
that encoded "this indicates growing demand" would put an interpretation
somewhere that looks like a fact, and every stage downstream would inherit it as
one. Signal extraction interprets, claim extraction asserts, scoring evaluates —
three later stages, none implemented.

Six rules, and none is negotiable:

- **Unknown stays unknown.** A unit the source does not publish is
  `NOT_PUBLISHED`, never inferred from a metric name. A geography code no
  reviewer classified is `UNKNOWN`, never promoted to a country. Each is a state
  a consumer branches on, which beats a plausible value nobody can check.
- **Missing is never zero.** Zero is a measurement and absence is not. A layer
  that mapped both to `0` would make them permanently indistinguishable, and the
  constructor refuses a number beside a `NOT_REPORTED` state.
- **An aggregate is never a country.** `World` and `High income` are real
  entities, preserved as aggregates with their source code. Classification comes
  from a reviewed map where every entry records its basis, and from nothing else
  — not from a code's shape and not from its label.
- **A year is an interval, not January 1.** The canonical period carries its
  type, its label and a half-open `[start, end)`, so nothing downstream can read
  the start bound as an exact event time.
- **An unestablished timezone is stated, never chosen** (Mission 1.10, ADR-019).
  A source may publish a period label and no offset. `timezone_state` says which
  situation a period is in: `ESTABLISHED` keeps timezone-aware bounds and an
  event time, `NOT_ESTABLISHED` carries **naive** wall-clock bounds and
  `observed_at` is `NULL`. Storing an aware UTC datetime beside a note saying it
  is not really UTC would be a lie next to a disclaimer, because code reads the
  datetime.
- **A language is stated, never resembled, and never a place** (Mission 1.10).
  `CanonicalLanguage` keeps the source label, the vocabulary it came from, the
  mapping status and — only where a reviewed mapping establishes one — a
  canonical tag. `unmapped()` is the counterpart of
  `CanonicalGeography.unclassified()`. `ENGLISH` looks like `en`, and the first
  name that does not resemble its tag would be silently wrong.
- **Numbers are exact decimals, never floats.** Parsed from JSON text with
  `parse_float=Decimal`, stored as decimal strings, and free of artifacts from
  an intermediate representation.
- **Quality is structural, never epistemic.** `VALID | PARTIAL | INVALID` says
  whether the record could be represented. It is not a confidence, not a
  reliability and not a weight; those belong to the evidence model and mean
  something else entirely.

Identity is again three separate things: `observation_key` says WHICH
observation (inherited verbatim), `raw_record_id` says WHAT the source said, and
the row id says WHICH transformation of it. The normalization timestamp is in
none of them.

**Record kinds are a registry and a kind exists because DATA exists** (Mission
1.10). **Five now**: `numeric_observation`; `lexical_frequency_observation` — one
occurrence count for one lexical term, one language, one period, and **no
geography key at all**; `procurement_notice` (Mission 1.15.8);
`community_question` (Mission 1.18); and `content_request_count` (Mission 1.19). Widening the first to fit the second would
have let a World Bank record exist without a geography, which is the existing
model getting worse for a new source's sake, and the same argument produced the
third and the fourth.

**A kind is named for a SHAPE, never for the first source to reach it** (Mission
1.18). `community_question` is one public question a person asked on a community
Q&A site: a title, the text, the SITE's own tags, a creation instant and the
answer metadata. `stack_exchange_question` would have made the vocabulary a list
of vendors — the site is a FIELD and the source is PROVENANCE. Three things it
must never be read as saying, each written into the payload rather than left to a
reader: the tags are the site's vocabulary and are never translated into a
taxonomy of ours; an accepted answer means only that the ASKER accepted one, never
that the problem is solved; and the score and view count are source counters, not
importance, not demand and not market size. Author identity is `null` because it
was never acquired, and a raw record that carries `owner`, `last_editor` or
`comments` is REFUSED at normalization rather than stripped.

**A kind's NAME may not carry an interpretation** (Mission 1.19).
`content_request_count` is how many times a named item was REQUESTED on a
platform in a period, by one class of requester. Not `wikimedia_pageview`, by the
rule above — and not `content_view_count` either, because the operator's own
definition is *"a request for content of a page that receives a response of 200 OK
or 304 Not Modified"* and "view" implies a person looked. A field name survives
every later caveat, so an implication put in the vocabulary is one nothing
downstream can unmake.

**`audience.class` is REQUIRED on that kind**, which is the design decision worth
arguing rather than assuming. The same item over the same period carries a
different count for human-attributed traffic than for all traffic; a record that
could not say which one it held would be two measurements wearing one name, and
every comparison built on it would silently mix them.

That is a different rule from the one governing adapters. A vocabulary row lets
the model describe a shape and lets the database refuse an unregistered one; the
claim that **code** exists is `NORMALIZER_REGISTRY` and `IMPLEMENTED_NORMALIZERS`.
When Mission 1.10 wrote this, GDELT was in neither; all four sources are in both
now, and the distinction is the same one — a registered kind with no adapter
behind it would still be a promise the code does not keep.

**A revision is not an overwrite and an upgrade is not a replacement.** A revised
RawRecord produces a new normalized row with the previous one superseded; a newer
normalizer or schema version produces an additional row with the old one intact.
Which one downstream should read is **D-08**, open, and Mission 1.6 deliberately
did not invent it. Output may only change with a version bump: the same identity
producing different content is reported as `NON_DETERMINISTIC_OUTPUT`, never
written over.

**Eligible, enabled, implemented and normalizable are FOUR facts.** The fourth
was separated in Mission 1.6 because the planner's normalization block read "no
collector is implemented" — which Mission 1.5 made false while leaving
normalization exactly as unavailable. `normalization_block` now derives it from
what exists, and a future Eurostat collector with no normalizer stays blocked.

**Five adapters exist** (Missions 1.10.1, 1.15.8, 1.18 and 1.19):
`world-bank-indicators-numeric`, `gdelt-web-ngram-lexical`,
`ted-search-api-notice`, `stack-exchange-question` and `wikimedia-pageview`. All are offline and
deterministic, and asserted so over the **AST** rather than over the file's text —
a substring scan fails on the docstring that explains the rule, and weakening it
until it passes is how a structural check stops checking
(`testing-strategy.md` §23).

**An `ESTABLISHED` period is possible, and Mission 1.18 is the first to earn
one.** Stack Exchange's `creation_date` is a Unix epoch second, which is an
unambiguous instant — unlike TED's offset-without-a-time (H-37) or GDELT's unzoned
bucket (H-29) — so `observed_at` is a real moment there and NULL everywhere else.
This does not weaken the rule above it: the timezone is still stated rather than
chosen, and what changed is that one source finally states it.

**Mission 1.19 earned one a different way, and the difference matters.** A
Wikimedia day bucket is `ESTABLISHED` **on documentation rather than on shape**:
the Analytics API's concepts page designates `Research:Page view` as the complete
definition, and that page states a *"UTC timestamp of the request"* and *"daily
partitioning 0:00 UTC - 23:59 UTC"*. GDELT's H-29 stays open for the opposite
reason — nothing there states the zone at all, and a bucket that merely LOOKS like
a day is not a bucket somebody documented. That the API REFERENCE does not restate
it is recorded as an open question rather than smoothed over. **A DAY is still an
interval**: half-open `[start, start + 1 day)`, and `observed_at` is the
interval's start, which is never the instant a request happened.

**Every `community_question` record is `VALID`, and that is not an oversight.**
The adapter has **no `PARTIAL` branch at all**: a record either carries the four
facts the kind requires or it is refused. A missing question body leaves the
record `VALID` with `question.body: null`, because `NormalizationQualityReason`
has no member that would truthfully name that absence and reaching for the nearest
one would put a wrong code where a consumer branches. Adding a member to a
generated closed enum is a contract change with an ADR behind it, and no record in
the real sample calls for one.

**A known absence is stated, never filled in.** Every GDELT normalized record is
`PARTIAL`, carrying `PERIOD_TIMEZONE_NOT_ESTABLISHED` and `LANGUAGE_NOT_MAPPED`,
because H-29 and H-30 are open. `VALID` would say nothing is missing when two
canonical facts are, and `INVALID` would make a record unreadable for a condition
that is universal and expected. The exact source label survives either way, so
answering an open question later is a normalizer version bump over records
already held — not a re-collection.

Normalization reaches **no network, no model and no embedding library**, not even
through `collection/transport.py`. `validate_normalization.py` asserts it by
parsing every import, and was probed against fourteen deliberate violations
before being believed.

### Signal — a derivation, never a labelled observation

Since Mission 1.11 the Signal contract exists (`signal-contract-v1.md`,
`signal-taxonomy-v1.md`, `signal-temporal-semantics-v1.md`, ADR-020). **The model
exists and no extractor does**: `SIGNAL_EXTRACTORS` is empty and `nlp.signals`
holds 0 rows.

```text
RawRecord -> NormalizedRecord -> SIGNAL -> Claim / Evidence -> Opportunity -> Score
```

Eight rules, and none is negotiable:

- **One observation is not a Signal.** A derivation whose assertion is
  recoverable from a single input's payload is that observation renamed. At
  least **two distinct source observations** must contribute, and distinctness is
  over `observation_key` — never over `normalized_record_id`, because one
  observation can have several normalized rows and counting rows would let a
  normalizer upgrade manufacture a contrast out of one observation. Two rows
  sharing a key are refused as `AMBIGUOUS_OBSERVATION_LINEAGE`. **D-08 is failed
  closed on, not solved.**
- **The Signal family is not the demand family.** `quantity_family` is
  `LEXICAL_FREQUENCY | MEASURED_SERIES | TRANSACTION_VALUE | CONTENT_REQUEST_VOLUME`
  and says what kind of QUANTITY the signal is about. `PAIN / DESIRE / BEHAVIORAL / MARKET` classify demand, and neither
  derivation the two real sources support is evidence of demand — a GDELT term
  count may equally be a news event, a crisis, a celebrity or the weather.
  **Ontology V2 §3.6 is unchanged**; what stops being true is the claim that
  every row of that table carries a demand family. Three things were called
  "signal family" and now have three names (`signal-taxonomy-v1.md` §1).
- **Order and global instant are different facts.** `SOURCE_RELATIVE_ORDER` says
  which of two observations came first within one source stream;
  `COMPARABLE_INSTANT` places them on a shared timeline. **Neither is granted to
  GDELT**: H-29 blocks the second and the new **H-32** blocks the first. Label
  EQUALITY needs no timezone and is available, so a contrast between two terms
  inside one bucket is derivable today and a frequency change is not. A direction
  other than `NOT_APPLICABLE` requires an ordered basis, so no GDELT signal can
  carry one — enforced by the database.
- **`PARTIAL` does not mean unusable and `INVALID` is never derivable from.** A
  derivation declares the `SignalRequiredFact` values it needs and the model
  computes what each input withholds from that record's own quality reasons.
  Every GDELT record is `PARTIAL` and a within-bucket contrast needs neither
  thing it is missing.
- **A blocked derivation produces no Signal.** There is no lifecycle enum, no
  `BLOCKED` and no `INSUFFICIENT_DATA`: a row in a table of signals says a signal
  exists. A refusal is a returned value object with a closed reason code.
- **Magnitude is exact, typed and not a strength.** A `Decimal`, never a float,
  never bounded to `[0,1]`, and **no 0–100 cross-signal scale** — a GDELT term
  frequency and a World Bank population figure are not comparable measurements.
  The unit is inherited from the inputs or does not exist.
- **`derivation_confidence` is about the derivation.** A deterministic
  extractor's is `1.0`, and that is a statement about arithmetic, not about the
  market. It is not an `EvidenceScore`, not an evidence strength, and it is
  multiplied by nothing.
- **A Signal is not Evidence and resolves no contradiction.** Evidence is
  claim-scoped and adds direction, relevance, directness, reliability and an
  independence state; a Signal has no claim to be relative to. Lineage preserves
  the source and raw-record facts so aggregation can judge independence later,
  and **judges nothing here**.

Identity is deterministic over workspace, type, extractor and version, schema
version, the ordered contributing inputs, the parameter fingerprint and the
window — and excludes the OUTPUTS, so a changed magnitude under an unchanged
identity is reportable rather than absorbed into a new row. The research session
is **lineage, never identity**: two sessions deriving the same thing converge on
one signal, because two rows would read as two independent findings.

### Signal derivation — two extractors, and what bounds them

Since Mission 1.11.1 two deterministic extractors exist
(`signal-derivation-runtime-v1.md`, ADR-021) and **five real Signals** do:
`numeric-period-change@1.0.0` produced four from the six World Bank
observations, `lexical-frequency-contrast@1.0.0` one from the two GDELT ones.

- **The extractor computes; the model checks.** `ObservationInput` carries no
  payload, so the model cannot interpret; the extractor reads the payload to
  subtract. Neither does the other's job, and `packages/signal-model` still
  contains no extractor — asserted over the AST.
- **Grouping is what keeps it tractable.** Records are bucketed by a canonical
  key and only records sharing one can meet. A caller handing an explicit
  incompatible pair is refused with `INCOMPATIBLE_SERIES`, naming the field that
  disagreed.
- **`terms` is a required parameter for the lexical contrast.** One WEB-NGRAM
  file holds 223,342 rows and an unselected all-pairs sweep is ~2.5 x 10^10
  pairs; every bounded default would be a threshold nobody reviewed.
- **Ordering never comes from the database.** Numeric by canonical period start,
  lexical by term text verbatim. Input order enters the derivation identity, so
  an order chosen by the query optimiser would choose the identity.
- **`PARTIAL` is usable, and now proven so.** Both GDELT records carry
  `PERIOD_TIMEZONE_NOT_ESTABLISHED` and `LANGUAGE_NOT_MAPPED`, neither is a fact
  the contrast requires, and both contributed with no withheld facts. No quality
  string is branched on anywhere in either extractor.
- **Order and instant stay separate, and one closed without the other**
  (Mission 1.12, ADR-022). `ORDER_ESTABLISHED_WITHOUT_TIMEZONE` holds one
  `TemporalOrderCertification`: `gdelt`, resources `web-ngrams/1gram` and
  `web-ngrams/2gram`, with its basis and its scope recorded. It is scoped to a
  publication **stream**, which is why `ObservationInput` carries `resource_id`
  — `source_id` alone would let another GDELT dataset inherit the finding, and
  the same directory publishes an unreviewed `chargram` file a prefix match
  would have covered. An observation that cannot name its resource is refused.
- **An extractor never reads a clock or converts a timezone** (Mission 1.12.1).
  `astimezone`, `now`, `utcnow`, `localtime` and `tzinfo=` are absent from every
  module under `sros_nlp/extractors`, asserted over the AST. The adjacency step
  is computed in **label space** — the earlier label's own components advanced by
  one published bucket and formatted back into a label — so nothing becomes an
  instant. That arithmetic is licensed by the certification, not by the format.
- **A refused derivation gets a run record, never a Signal** (ADR-021).
  `nlp.signal_derivation_runs` holds one row per **execution**, written in the
  same transaction as the signals: N considered, M derived, K refused and why. A
  redelivery writes a second run row and zero new signals, which is the honest
  record — the signals are what is idempotent.
- **`signal.derive` routes to the acquisition queue**, like `normalize.`:
  bounded, CPU-cheap work over records already held. The `nlp` queue is sized
  for LLM-backed work.
- **`SIGNAL_DERIVATION` is its own capability**, between normalization and NLP
  extraction, with a derived block. `NLP_EXTRACTION` stays blocked by D-12 —
  whose reason is embedding versioning, true of classification and clustering
  and **false** of deterministic arithmetic.

### Claim — the unit evidence accumulates against

Since Mission 1.2 a **Claim** is a persisted entity (Ontology V2.2 §17,
`claim-model-v1.md`, ADR-015). Five rules follow:

```text
Signal -> Claim -> Evidence -> Aggregation
             |
             +-- at most one Opportunity, possibly none
```

**The arrow changed direction in Mission 1.13.** It read
`Workspace -> Opportunity -> Claim` while the schema said
`opportunity_id NOT NULL`, and the pipeline has always run the other way: a Claim
about a source fact exists before anybody has conceived of the product it might
justify. ADR-024 and migration 0016 made the column nullable; Ontology V2.2 §17.3
is the amended sentence.

- **A Claim is not a `ClaimType`.** `ClaimType` is an epistemic category a claim
  carries; there are exactly five of them and none is an identity. A Claim is an
  assertion with a `ClaimId`.
- **A Claim is not an Opportunity.** One opportunity carries several assertions
  that do not stand or fall together; aggregating at the opportunity level
  averages away what the four masses preserve.
- **Identity is stable; statements are revised append-only.** An aggregation that
  evaluated revision 2 must still be able to read revision 2. The previous
  revision is never modified.
- **Temporality is declared on the Claim, never inferred from the source.** The
  claim names a `claim_feature`; the half-life lives in the profile.
- **`ClaimLifecycle` is editorial, never epistemic.** `ACTIVE` and `WITHDRAWN`
  only. There is no `VALIDATED`: evidence changes, and a lifecycle derived from
  it would freeze a conclusion the evidence no longer supports.

A claim is not owned by the session that first met it (Ontology V2 §12, applied
to Claim). Sessions produce observations; the same claim accumulates evidence
across many of them.

### Interpretation — where arithmetic becomes an assertion

Since Mission 1.13 the interpretation boundary is defined
(`claim-evidence-interpretation-contract-v1.md`, `claim-epistemic-semantics-v1.md`,
`signal-to-evidence-semantics-v1.md`, ADR-024). Since Mission 1.13.1 **one
interpreter crosses it**: `observed-signal-restatement@1.0.0`
(`deterministic-observed-claim-interpreter-v1.md`,
`claim-interpretation-runtime-v1.md`, ADR-025), which produced **7 real OBSERVED
Claims, 7 revisions and 7 Evidence rows** from the seven real Signals.

Each layer is defined by the one verb it may perform: a RawRecord **preserves**, a
NormalizedRecord **reshapes**, a Signal **relates**, a Claim **asserts**, Evidence
**bears on**. A layer performing the verb above it is the bug this contract
prevents.

- **The claim boundary (C-1).** A Signal states a relation between its inputs; a
  Claim states a proposition about the world that observations outside the
  derivation could support or contradict. "SP.POP.TOTL rose from 82,905,782 to
  83,092,962" is the records. "World Bank reported Germany's population rose" is a
  claim about a publication. "Germany's population rose" is a claim about
  demography. "There is growing demand for German-language SaaS" is supported by
  none of it. **The failure prevented is a system that takes the first step and
  prints the third.**
- **A machine may not store an assertion nothing supports.** Enforced twice: a
  `DEFERRABLE INITIALLY DEFERRED` constraint trigger (migration 0016) and
  `NO_SUPPORTING_SIGNAL` in `build_claim`. Three exemptions, each for a reason —
  `HYPOTHESIS` **by definition** (requiring evidence would make the category
  unusable and push unsupported ideas into `INFERRED`, the exact failure), `MANUAL`
  because a person asserting and then looking is the ordinary research motion, and
  `WITHDRAWN` because a withdrawn claim's evidence may be gone.
- **No new entity for the interpretation step.** A candidate table is a second
  place an assertion can live, and one that lives outside `research.claims`
  escapes every rule here. The step produces an unpersisted `ClaimDraft`, written
  as claim + revision + evidence in one transaction or not at all.
- **A model is a reasoning mechanism, never the evidence.** An LLM may propose an
  interpretation; a `MODEL_DERIVED` claim citing no Signal is refused exactly as a
  deterministic one is. Its contribution is provenance
  (`interpretation_kind`, `model_version`, `prompt_version`), never a row in
  `scoring.evidence`. **`DETERMINISTIC` forbids a model version** — "deterministic"
  promises the claim can be regenerated, and a model in the path voids it.
  **No chain-of-thought is stored**, and there is nowhere to put one.
- **Identity is the proposition, not the prose and not a vector.**
  `proposition_key` is sha256 over the canonical facts asserted, unique per
  workspace. Two interpreters wording one fact differently produced **one** claim;
  a claim reworded in revision 3 is the same claim. **D-12 stays open** and nothing
  here depends on it. The research session is lineage, never identity.
- **Confidence is about the reading, not about the world.**
  `interpretation_confidence` on the revision is how confident the interpreter is
  that the statement correctly reads the Signals it cites. It is not evidence
  strength, not a probability and not a score — a deterministic restatement can be
  1.0 while the proposition is barely supported. **No universal thresholds**: "3
  Signals required" is an arbitrary number wearing the costume of a rule.
- **Evidence is claim-relative.** Direction, relevance and directness live on the
  Evidence row because a Signal has never heard of the Claim; one Signal may
  support A and contradict B unchanged. A generated row may not be `NEUTRAL` — a
  Signal bearing on nothing produces no row. An absent factor is `NON_SCORABLE`,
  never `0.5` and never `0.0`. `claim_id` is now `NOT NULL` and `claim_type` was
  dropped from `scoring.evidence`: two answers to one question eventually disagree.
- **Independence travels; the judgement does not happen here.** Two Signals from
  one publication stream are not automatically independent, nor automatically
  dependent. `source_id` is recorded and aggregation groups by origin. Record what
  you know, promote nothing.
- **GDELT lexical frequency alone never satisfies a demand claim.** Not weakly,
  not with low relevance, not with a caveat. News coverage is journalists
  publishing; demand is people wanting and paying. A low score would model it as a
  little bit of the right thing, and it is none of the right thing. An `OBSERVED`
  claim using market or user vocabulary is refused
  (`UNSUPPORTED_INTERPRETATION`).
- **H-29 and H-30 fail closed at this boundary too.** A Signal certified only for
  `SOURCE_RELATIVE_ORDER` cannot support a claim needing an instant
  (`INCOMPATIBLE_TEMPORAL_SEMANTICS`); a GDELT language label is its own identity
  and cannot become a named language (`INCOMPATIBLE_LANGUAGE_SEMANTICS`). A
  `HYPOTHESIS` is exempt from the evidence requirement, never from these.

### Claim interpretation — one interpreter, and what bounds it

Since Mission 1.13.1 `observed-signal-restatement@1.0.0` exists and is the only
thing that crosses the interpretation boundary. Three templates, one per
implemented Signal type, and **no fallback**.

- **Structurally OBSERVED, not defaulted.** `_CLAIM_TYPE` is a module constant,
  `interpret()` takes no claim-type parameter, and `validate_claims.py` fails the
  build on any `ClaimType.X` attribute access in the package where X is not
  `OBSERVED` — over the AST. There is no low-confidence-inferred escape hatch.
- **A Signal type with no template is `UNSUPPORTED_SIGNAL_TYPE`.** Generic prose
  over an unknown Signal would be a proposition nobody specified and nobody
  reviewed.
- **Attribution is the claim.** Every statement names the source and says
  "reported that". `Germany's population increased` is not OBSERVED from a World
  Bank record; `World Bank Open Data reported that "SP.POP.TOTL" for "Germany"
  increased…` is. The geography is the SOURCE's own name, never our canonical
  code — the code is what a reviewed mapping decided.
- **Three attribution facts come from the contributing normalized records** —
  resource, geography name, term and language schemes — because the Signal's
  scope does not carry them. Disagreement is `AMBIGUOUS_SIGNAL_LINEAGE` and
  absence is `SIGNAL_LINEAGE_UNAVAILABLE`; the interpreter refuses rather than
  picks. It never reads a RawRecord.
- **H-29 in the wording.** "source bucket" and "the preceding source bucket",
  never a clock, a date or an alignment. `observed_at` is written NULL. Each
  template accepts only the temporal bases it can phrase and refuses the rest.
- **H-30 in the wording.** "under source language label ENGLISH", never "in
  English". `canonical_tag` is never read, asserted over call arguments and
  subscripts.
- **The vocabulary guard exempts QUOTED source data** (Mission 1.13.1 §10). A
  GDELT term is arbitrary text: `market`, `demand` and `pain` are ordinary
  English words a news corpus contains, and refusing them would refuse the most
  faithful restatement available. Matching is over TOKENS of the interpreter's
  own prose — `supermarket` is not `market`. **The template is the primary
  protection**; no template contains the word `demand`.
- **Identity is the proposition and excludes the magnitude.** A source revising
  187,180 to 187,200 restated the SAME proposition, so a re-interpretation
  appends revision 2 rather than creating a second claim. Revision 1 is never
  modified. For a contrast, where `direction` is NOT_APPLICABLE, the relation
  comes from the SIGN of the magnitude and is part of identity while the value
  is not. `proposition_facts` stores the preimage, so the key can be verified
  rather than trusted (ADR-025).
- **Every evidence factor is a decision with a reason, and the absent one is the
  important one.** `SUPPORTS`; relevance and directness 1.0 because the claim
  restates that Signal and nothing else; extraction confidence 1.0 because a
  format string either read the facts or raised; `UNCATEGORISED` for both sources
  because a population count is not market activity and a news frequency is
  nobody's behaviour; independence `UNKNOWN`; evidence level 1. **Reliability is
  NULL** — purpose-relative, D-03 blocked — so every record is `NON_SCORABLE`
  with `MISSING_RELIABILITY` and the seven real claims aggregate to no score.
  That is the honest answer, not a gap to fill.
- **Claim, revision and evidence are written in ONE transaction.** The evidence
  requirement is a deferred trigger firing at COMMIT; evidence in a second
  transaction is too late by construction.
- **A refused interpretation gets a run record, never a Claim** (ADR-025).
  `research.claim_interpretation_runs` holds one row per EXECUTION. A redelivery
  writes a second run row and zero new claims, which is the honest record — the
  CLAIMS are what is idempotent, and this is not exactly-once.
- **GAP-5 is resolved.** `research.claim_interpretation_inputs` records every
  Signal a run CONSIDERED with its role — `CITED`, `EXCLUDED`, `REFUSED` — and
  why. `EXCLUDED` was never attempted; `REFUSED` was attempted and rejected, and
  collapsing them loses which happened. It hangs off the RUN, because a Signal
  considered and not cited has no Claim to hang off.
- **`claim.interpret` routes to the acquisition queue**, like `signal.` and
  `normalize.`. No parallel AI worker subsystem was created.
- **`CLAIM_INTERPRETATION` is its own capability**, after `SIGNAL_DERIVATION`,
  with a derived block. `PLANNER_VERSION` is `1.4.0`.


### Evidence aggregation — defined, and not calibrated

Since Mission 1.1 the aggregation algorithm is defined
(`evidence-aggregation-framework-v1.md`, ADR-014). Five rules follow, and none is
negotiable:

- **`q_i = min(components)`.** The weakest required dimension, never a weighted
  average. A high value must not compensate for a critical weak one.
- **Duplicates cannot multiply.** Records sharing an origin form one group and
  the strongest member counts. Unknown provenance forms **one** group per claim
  and direction — it is never promoted to independent.
- **Support and contradiction are aggregated separately** and decomposed into
  four masses that sum to 1. There is no flat contradiction penalty.
- **No invented parameters.** No per-platform reliability coefficient, no
  universal half-life. A temporally sensitive claim with no authorised half-life
  reports `MISSING_TEMPORAL_PARAMETER` and produces no score.
- **`EvidenceScore` is a score, not a probability.** `82` does not mean an 82%
  chance the claim is true, and it is never published without
  `support_strength`, `contradiction_strength`, `conflict_mass` and
  `uncertainty_mass`.

Source POLICY status (Mission 1.0) is not epistemic reliability. An `APPROVED`
source does not produce better evidence.

### Evidence reliability — reviewed, never inferred

Since Mission 1.14 reliability has a governance contract
(`evidence-reliability-contract-v1.md`, `evidence-reliability-review-guide-v1.md`,
ADR-026). **The machinery exists and no assessment does**: zero rows in
`epistemic.reliability_assessments`, so all seven Evidence rows remain
`NON_SCORABLE` with `MISSING_RELIABILITY`.

- **Reliability answers one question**: how dependable is this kind of
  measurement, for this kind of proposition. Not how permitted the source is,
  not how well-known, not how carefully we read it, not how much it bears on the
  claim.
- **The scope is measurement × purpose**, matched in full or not at all:
  `source_id`, `resource_id`, `record_kind_id` name the measurement;
  `claim_type` and `proposition_kind` name the purpose. `world-bank` alone
  matches nothing, so the framework's own example resolves with no special case
  — a population record used for a demand proposition has a different kind and
  matches nothing at all. `proposition_kind` is the `proposition_facts`
  discriminator Mission 1.13.1 already writes.
- **Seven Evidence rows collapse to three scopes**, and stay three however many
  observations arrive. That ratio is the design's whole justification: a scope
  narrow enough to stay purpose-relative and broad enough for a person to
  review.
- **Compliance is not reliability, in both directions.** An `APPROVED` source
  does not produce better evidence and a `RESTRICTED` one does not produce
  worse. Enforced by a separate schema with no policy column, and by an AST test
  that excludes docstrings so the paragraph explaining the rule cannot fail it.
- **A value rests on retrieved first-party documents.** `"The publisher is
  reputable"` is a sentence, not a basis; `REVIEWER_DOCUMENTED_JUDGEMENT` is
  permitted alongside documents and refused alone, by a deferred trigger. Full
  documents are never stored — a reference, a section, a short finding, an
  excerpt capped at 1000 characters, the same discipline
  `registry.source_policy_evidence` uses.
- **A value states what bounds it.** `stated_limitation` is required: a
  reliability with no stated failure mode is a number nobody can argue with.
- **There is no `MODEL_GUESSED` origin, and closure is the point.** A model may
  help a reviewer read documentation and may not be the epistemic source. The
  three origins are `HUMAN_REVIEW`, `DOCUMENTED_METHOD`, `CALIBRATED_EMPIRICALLY`.
- **Human review is not calibration.** A `HUMAN_REVIEW` assessment may not name
  a calibration dataset and a `CALIBRATED_EMPIRICALLY` one must — refused both
  ways. `REFERENCE_PROFILE_V1` stays `UNCALIBRATED` however many assessments
  exist.
- **Unknown is the absence of a row, not a value.** `0.5 because unknown`,
  `0.8 because reputable`, `1.0 because official`, `0.9 because government` and
  `0.0 because we do not know` are all measurements, and `q_i = min(components)`
  must never see one nobody made. **The system stays capable of producing no
  score**, which is what makes a score mean something when one appears.
- **Zero, one, many are all defined.** Zero → `NO_APPLICABLE_ASSESSMENT`; all
  superseded → `SUPERSEDED_ONLY`, deliberately distinct because *reviewed and
  withdrawn* is a different fact from *nobody looked*; one → `RESOLVED`; more
  than one → **refused**. Never the closest, never the maximum, never the mean.
- **Resolved late, bound explicitly** (ADR-026 Decision 2). The result records
  which assessment id and version produced each number, so a score's
  coefficients can be reconstructed. A value already on the Evidence row wins
  and consults nothing — one answer per question, by construction.
- **No factor implies another.** `resolve_reliability` takes scope, candidates
  and supplied, and nothing else. Relevance, directness, extraction confidence
  and claim interpretation confidence are all `1.0` on the real rows and none of
  them is an argument.
- **Assessments are GLOBAL.** A statement about a published dataset's
  measurement contract is not a statement about a tenant, and per-workspace
  review would give one question several answers. No `workspace_id`, no RLS
  policy, `SELECT` only for the runtime role — **no tenant data, so no leakage
  path**, which is stronger than a correct policy.
- **The resolver lives outside `packages/evidence-aggregation`**, whose guard
  forbids naming a source at all. The guard was left untouched rather than
  narrowed, and the resolver carries its own no-source-id test.

**Reliability does not solve missing evidence families.** Even a reviewed value
for all seven rows would establish nothing about pain, desire, willingness to
pay, pricing power, competition, distribution, retention or revenue potential.
It decides whether the evidence the system HAS can be scored, not whether it is
evidence of the thing anybody wants to know.

### Demand-side sources — nine examined, none usable

Since Mission 1.15 the portfolio has been reviewed against the eight business
evidence families the product needs (`demand-side-source-expansion-v1.md`,
`demand-side-source-coverage-v1.md`, `demand-side-source-priority-v1.md`).
**29 sources registered, 5 approving, 0 collector-eligible for any demand-side
family.**

- **Six of eight families have no approving source**, and two — Pricing and
  Retention — have no registered candidate at all. The two families that DO have
  an approving source have a weak one: `openalex` for distribution is
  scholarly-record discovery rather than a marketing channel, and `gdelt` for
  user behaviour is news-corpus activity. **No approving source observes an
  individual doing anything.** Retention's obstacle is
  structural rather than legal: it needs the same subject observed twice, and
  everything in the portfolio is an aggregate or a one-shot public record. **No
  proxy is proposed**, because a proxy nobody can validate is worse than an
  acknowledged gap.
- **WILLINGNESS_TO_PAY gained its first candidates.** `ted-eu` and `usaspending`
  record contract awards, which is a `TRANSACTION` class of evidence rather than
  a `LISTED_PRICE`, and a pricing page is only ever the first — the distinction
  the portfolio had no source able to make.

  **What a TED award notice states is narrower than "what a buyer paid", and
  this bullet said the wrong thing until Mission 1.20 §0.** Mission 1.15.12
  established from the Publications Office's own SDK 1.15.1 that BT-161 is *"the
  value of all contracts awarded in this notice, INCLUDING OPTIONS AND
  RENEWALS"*. It is a PUBLISHED value, not money paid, not necessarily one
  supplier, not realised expenditure and not a price — and it may be lawfully
  withheld (BT-195 to BT-198), so any cohort covers the published subset only.
  The candidate is still the portfolio's only lawful route toward transaction
  evidence; what it evidences is just less than the earlier wording implied.
- **`ted-eu` is the closest any blocked source has come.** One retrieved sentence
  grants five of six load-bearing activities: *"the procurement notices ... can
  be freely reused, for commercial or non-commercial purposes"* — a GRANT, not
  an absence of prohibition. `model_processing` is `NOT_ADDRESSED` and rule 8
  blocks whatever the other five say. Recording it otherwise would be the
  narrowing of the assessed use case Mission 1.8 forbids: this product includes
  LLM processing, and a permission obtained by describing a smaller product is a
  permission for a product we are not building.
- **Two hopeful maybes became definite noes.** Pinterest — the catalog's best
  DESIRE hypothesis since Mission 1.7 — prohibits storing API information at all
  (*"call the API each time"*), prohibits automated extraction and ML training,
  and requires explicit written authorization for competitor-research features,
  which names this product. Hacker News publishes an API stating *"There is
  currently no rate limit"* while Y Combinator's Terms prohibit *"data mining,
  robots, scraping"* and commercial derivative works over Site content. Both are
  RESTRICTED on retrieved evidence.
- **Bluesky's question got smaller.** Its developer guidelines exist — named by
  Bluesky's own documentation domain — and returned an empty body. The user
  Terms, re-retrieved at the version effective 15 September 2025, remain silent
  on all ten activities. H-33.
- **A failed retrieval changes nothing.** Reddit and Stack Exchange were
  unreachable from the review environment and gained **no review version** in
  either direction. No mirror, cached copy, alternative page or community summary
  was used to infer terms, and no bot protection was bypassed. An unresolved
  question stays visibly unresolved.
- **Coverage is still potential, never permission.** Both new sources record
  signal coverage and neither is approving. Both facts hold at once, and the
  registry exists to keep them apart.

**Reliability solved scorability; source expansion is what would solve
relevance — and it has not yet.** Even a perfect reliability review of all seven
existing Evidence rows would establish nothing about pain, desire, willingness to
pay, competition, distribution or retention.

### TED-EU — official routes documented, and a gap in our own model

Mission 1.15.4 re-reviewed TED against the system's **actual** use -- local,
private, one developer, no redistribution, no resale, no training
(`ted-eu-local-private-research-review-v1.md`,
`route-scoped-source-authorization-gap-v1.md`). Review v5. **Verdict unchanged.**

**A user summary was excluded before anything else** (§32). A file describing a
written Publications Office reply exists outside the repository and is a
transcription that says so itself. Classified `USER_SUPPLIED / NON_AUTHORITATIVE`,
not cited, not entered as evidence, not deleted. **No source in the catalog
carries an `OPERATOR_CORRESPONDENCE` row**, asserted as a tripwire so the first
one is a visible diff. H-36 is exactly where Mission 1.15.3 left it.

**Local use creates no permission.** *"It is local, therefore anything is
allowed"* is not an argument and nothing rests on it. What the narrower use
changes is which question is worth asking: not *may we mirror the corpus
commercially*, but *do the official query routes document a purpose that covers
narrow local research*.

**They do, in the operator's own words.** The Search API *"allows access to
published procurement notices for analysis and reuse"*, is *"primarily targeted at
data reusers"*, requires no authentication, and names *"Commercial Organisations:
Integrating TED data into platforms to provide added-value services"* and
*"Researchers: Analysing public procurement trends and patterns"*. The TED Open
Data Service publishes the data *"for analysis and re-use"*, invites use *"in your
research and applications"*, and offers a **Connect your app** button to
*"retrieve live results directly into Excel, Power BI, or any application that can
get data from the web"*. Analysis, reuse, integration, commercial use, repeated
access and automated access are each named by the operator about its own route.

**And that is intended-use evidence, not a rights grant.** Nothing on either route
mentions the sui generis database right. **Condition 11** records the distinction
so a later reader cannot collapse them, and the Search API is nowhere framed as a
way around H-36 -- the argument rests on documented purpose, never on the route
transferring smaller chunks. The Open Data Service's own invitation to *"extract
custom datasets across many notices"* uses the Directive's verb and is recorded
as striking and load-bearing for nothing.

**Two practical findings.** The Search API request body carries a **`fields`**
parameter, so minimisation happens AT acquisition rather than after it. And
coverage is recent and partial: eForms from **1 March 2023**, Standard Forms only
28 August 2023 to 26 January 2024 as a *"proof of concept"* slice of six form
types -- a bound on what research the route could support, recorded so a collector
does not discover it from an empty result set.

**THE REAL BLOCKER MOVED, and it is ours.** The system's use is local and a narrow
official-route profile would be defensible; the registry cannot express it.
`build_authorization('ted-eu')` returns exactly one reason -- *"policy review is
REQUIRES_REVIEW"* -- and there is no route, resource or profile argument that
could change it. Searching the contracts and acquisition packages for
`use_profile`, `deployment_profile`, `LOCAL_PRIVATE` or `MULTI_TENANT` returns
**zero matches**.

The finding underneath is not about TED: **every review in this registry already
assessed a use case, and the model never recorded which one.** Twenty-eight
sources cost nothing for it because one product was being assessed. TED is the
first source whose product has two shapes at once, and the model has one slot.

**Three ways to hack it, all worse than the gap.** Flipping the verdict makes
every consumer report TED approving for the commercial use case that is still
unresolved -- the silent migration §8 exists to prevent. Two current reviews means
two answers to one question. A use-profile condition still needs the flip to get
past the gate.

**The minimal extension is proposed and not built**: record
`assessed_use_profile` on a review (every existing one is
`COMMERCIAL_MULTI_TENANT`, which is what they DID assess), allow one current
review per profile, thread the profile through `evaluate_eligibility` and
`build_authorization`, and have the runtime **declare** its profile from
configuration rather than infer it. A profile the review does not name is
refused. It needs an ADR and a mission of its own -- doing it as a side effect of
a TED mission would be the change-control violation §Change control describes.

**Unchanged:** H-34 `CLOSED PERMITTED` and not reopened; every activity assessment
byte-identical between v4 and v5; all ten v4 conditions carried forward verbatim;
personal-data minimisation intact; model training **not authorised**; embeddings
blocked by D-12; bulk XML **still blocked**; `ted-csv` still a separate review.

### TED-EU — the licence found, and the question externalised

Mission 1.15.3 exhausted the first-party dataset-level material
(`ted-eu-database-right-clarification-v1.md`,
`ted-eu-database-right-clarification-request-v1.md`,
`ted-eu-h36-legal-review-packet-v1.md`). Review v4. Verdict unchanged.

**The question Mission 1.15.2 did not ask.** Is a licence attached to the
assembled DATASET, as opposed to the individual documents? **Yes.** The
Publications Office publishes TED in its own open-data catalogue, and the DCAT-AP
record for `ted-1` declares `dct:license = COM_REUSE` on **every** distribution
-- including *"Last daily editions of procurement notices in bulk download"*. The
dataset node itself carries no licence, no `dct:rights` and **no `dct:creator`**;
`dct:publisher` is the Publications Office.

**And the licence IS the Decision.** The `COM_REUSE` authority concept carries
`skos:exactMatch` to `http://data.europa.eu/eli/dec/2011/833/oj`. The
machine-readable licence on the bulk route resolves, by the publisher's own
assertion, to the instrument Mission 1.15.2 read in full and found silent on
database rights. The TED Search API's OpenAPI document has a "Terms of Usage"
section whose entire content is a link to the same TED legal notice. **Both
routes are governed by the same silence, and the silence is now known to be
complete**: the TED notice, the Publications Office notice, the europa.eu notice,
the 20,015-character data.europa.eu notice, the bulk page, the package HTTP
headers and the API specification contain **zero** occurrences of *sui generis*,
*database right*, *extraction*, *re-utilisation* or Directive 96/9/EC.

**`appliesTo licence-domain/DATA` is not a database-right grant.** The tempting
over-read. `DATA` is defined in the same authority table as a *"set of values of
qualitative or quantitative variables"* -- a subject class, not a class of right
-- and the whole `licence-domain` scheme is `CODE`, `DATA`, `METADATA`,
`W_LIT_ART` and a placeholder. **There is no `DATABASE` domain**, so the absence
is not a deliberate choice either. `CC_BY_4_0` carries the same two values.

**H-36 split, because the halves have different addressees.**

- **H-36A -- does the right subsist?** **NOT ESTABLISHED, either way.** Directive
  96/9/EC Article 7(1) gives the right to a **maker** showing **substantial
  investment**; nothing retrieved names one. The catalogue names a *publisher*
  and no creator, notices are filed by contracting authorities across the Union,
  and Article 11 makes subsistence turn on facts about that maker. A legal
  question about facts nobody has published.
- **H-36B -- is it granted or waived?** **NOT ADDRESSED for both routes.**
  Article 7(3) confirms the right *can* be granted by contractual licence.
  `COM_REUSE` does not.

**The sharpest fact, recorded and not relied on.** The same portal declares
**CC BY 4.0** -- whose Section 4 expressly grants the right *"to extract, reuse,
reproduce, and Share all or a substantial portion of the contents of the
database"* -- on **12 of 48** distributions of the separate `ted-csv` dataset,
published by **DG GROW**, including contract award notices for 2020, 2021 and
2022. The other 36 are `COM_REUSE`, and the two **overlap**:
`ted-contract-award-notices-2017-2021.zip` is CC BY 4.0 while
`ted-contract-award-notices-2018-2023.zip` is `COM_REUSE`. Nothing on `ted-1`
carries CC BY 4.0. **Selecting the favourable licence would be selecting a
licence by selecting a filename**, so it is asked about rather than used --
condition 10 forbids carrying a licence across resources.

**A correction to Mission 1.15.2.** That review reasoned the search API was a
smaller taking than bulk. The API's own specification documents a **scroll mode
with no limit on the number of retrievable notices**, and Article 7(5) reaches
repeated and systematic extraction of insubstantial parts regardless. Both routes
stay unresolved and **no route is preferred**.

**No PSI chain exists** (§12). Directive (EU) 2019/1024 appears nowhere; the one
occurrence of Directive 2003/98/EC is inside the data.europa.eu **privacy**
statement as a personal-data processing basis. Recorded as separate legal
context, never as controlling evidence.

**The blocker is now a message.** `ted-eu-database-right-clarification-request-v1.md`
is written and **unsent** -- addressed to `op-copyright@publications.europa.eu`,
the route TED's own legal notice publishes for SIMAP copyright issues, with
`GROW-D2@ec.europa.eu` for the CSV question. The repository may PREPARE a message
and may never imply it was delivered: there is no `sent_at` anywhere, and a test
asserts it. Legal review is step two, and
`ted-eu-h36-legal-review-packet-v1.md` exists so it starts from established facts.

**Verdict `REQUIRES_REVIEW` at v4.** H-34 untouched, six activities still
`PERMITTED`, all nine v3 conditions carried forward verbatim plus a tenth.

### TED-EU — every activity granted, and still blocked

Mission 1.15.2 retrieved and read the governing instrument
(`ted-eu-governing-decision-review-v1.md`,
`ted-eu-database-right-review-v1.md`). Review v3.

**The retrieval.** EUR-Lex failed again — six representations across two
missions, including the Official Journal full-issue HTML. The text came from the
**Publications Office's own Cellar repository**, addressed by the Cellar
identifier the Publications Office publication record itself publishes. Four
pages, Articles 1–13, 16,748 characters. A first-party representation reached by
following the publisher's own identifiers; not a mirror.

**H-34 — CLOSED PERMITTED.** Article 3(2): reuse *"means the use of documents by
persons or legal entities of documents, for commercial or non-commercial
purposes other than the initial purpose for which the documents were
produced"*. The definition is framed by **purpose** and enumerates no acts —
method does not enter. Article 4 makes all in-scope documents available on that
footing; Article 6(2) says conditions *"shall not unnecessarily restrict
possibilities for reuse"* and lists three, none about method; the Article 2(2)
exclusions are classes of **document**; and the only manner-of-use prohibition in
the whole instrument is Article 2(4)'s reuse *"calculated to deceive or to
defraud"*.

**This is not silence about machine learning.** It is a grant whose operative
term is defined broadly enough that method does not enter — a different thing,
and the thing that permits closing without the literal words.

**Scope of what closed.** Inference, extraction, classification, structured
analysis. **Model training was not assessed and is not authorised** — the
Decision does not distinguish methods, but training raises Article 2(2)(b)'s
third-party-rights exclusion in a materially different form and the engine does
not need it. Embeddings are unassessed for implementation and blocked
independently by D-12. Both recorded as a **condition** on v3, because a single
`PERMITTED` field cannot carry a boundary.

**Three new conditions from the Decision.** Article 6(2)(b) obliges the reuser
**not to distort the original meaning or message** — the condition with the most
direct bearing on the claim layer, making an epistemic requirement a legal one
too. Article 2(4) forbids deceptive or fraudulent reuse. Article 6(2)(c) records
the Commission's non-liability.

**H-36 — NOT CLOSED, and the unknown became an established absence.** The full
text contains **zero** occurrences of *sui generis*, *extraction*,
*re-utilisation* or Directive 96/9/EC; its two occurrences of *database* are an
exclusion for unpublished research and an example inside the definition of
structured data. The Decision is framed throughout around **documents**
(Articles 1, 2(1), 3(1)); the collection they sit in is never mentioned. Article
2(2)(a) excludes industrial property by name and the database right is not in
that list — the instrument neither grants over it nor excludes it, it **does not
reach it**.

One fact cuts the other way and is recorded: SIMAP *system metadata* is CC0 1.0,
and CC0 waives sui generis rights where the dedicator holds them. That shows the
Publications Office addresses this right when it means to — and it applies to
metadata, not to the notice corpus a collector would extract.

**The verdict.** Permitted plus unresolved gives `REQUIRES_REVIEW`. **All six
load-bearing activities are granted and the source is still blocked**, which is
uncomfortable and correct: the remaining question is not an activity in the
matrix, it is whether a different body of rights sits over the same data.

**The blocker changed kind.** It was *"retrieve a document"*. It is now *"decide
a legal question the documents do not answer"* — the first item in the queue a
further document search cannot settle, because the documents have been read.
Bulk XML and the search API are analysed separately and both are unresolved,
with different exposure; **no collector route was forced**.

### TED-EU — one human decision left, and it is the right one

Mission 1.15.6 (`ted-eu-authorization-bootstrap-v1.md`, ADR-028). Local review
**v2**, appended.

Three of TED's four conditions under `local-private-research-v1` now verify
`SATISFIED` against configuration: `ted-attribution`,
`ted-official-route-only` (`source-route-binding`) and
`ted-personal-data-minimisation` (`source-field-minimisation`). The routes are
`ted-search-api` and `ted-open-data-sparql`, the Search API is the **preferred
first implementation route**, and `ted-bulk-xml` is refused by name and absent
from the context. `ted-open-data-sparql` was registered as an access profile in
the same mission, because the review authorised a route the registry had never
recorded.

**`ted-database-right-residual-exposure-accepted` is OUTSTANDING and stays
`HUMAN_CONFIRMATION`.** Nothing in this repository can satisfy it: the human
branch is reached before any configuration is consulted, and the database
refuses a hand-set boolean with no verification behind it.

**No acceptance has been recorded.** The exact statement an operator would have
to record is written down in the bootstrap document §6.2, and **writing it down
is not recording it**. The existence of that mission is not acceptance, and
neither is the fact that the deployment is local.

**Nothing else moved.** H-36A NOT ESTABLISHED and H-36B NOT ADDRESSED under both
profiles. Commercial profile still `REQUIRES_REVIEW`. Model training not
authorised, embeddings blocked by D-12, redistribution not permitted, bulk XML
and `ted-csv` blocked at the route gate and again at the resource gate. Local
review v1 was not rewritten: v2 carries every assessment, condition, open
question and evidence row unchanged and differs in exactly two condition
classifications.

### Blocked work

**`services/scoring` must not be implemented for production research.** D-03 is
resolved at the *framework* level only: the equations exist, their parameters
were never fitted, and no `CALIBRATED` profile exists.

**Mission 1.14 closed one of D-03's blockers and left four standing.** What is
resolved is the *definition* of reliability and who may establish one. What
remains open: no reviewed value exists for any scope in use, no `CALIBRATED`
profile exists, no authorised half-life exists for temporally sensitive claims,
and the level thresholds are structural minimums rather than fitted values.
Reliability governance is not calibration and does not become it by being
careful. Framework Defined and
Profile Calibrated are separate gates (ADR-014, framework §14). An
`UNCALIBRATED` profile may be run only for synthetic or experimental work, and
only when explicitly labelled as such.

Do not invent a half-life, a damping constant, a per-source weight or a
contradiction penalty to make the engine produce a number. Failing closed is the
designed behaviour, not a gap to fill.

**No normalizer may be implemented for a source with no collector**, and no
normalization job may be dispatched for a source with no normalizer. The
orchestrator reports the second under `NO-NORMALIZER-IMPLEMENTED`, distinct from
the two acquisition gates because different work clears each.

**Sequential WEB-NGRAM derivation is implemented since Mission 1.12.1**, by
`lexical-frequency-change@1.0.0` and by nothing else. It asks the Mission 1.12
certification for its stream and its label scheme before comparing anything;
order is never inferred from a label that happens to sort.

**Two rules bound it, and both are ADR-023.** A pair derives only when its labels
are **exactly one published bucket apart** — anything else is
`NON_CONTIGUOUS_SOURCE_BUCKETS`, because a change computed across a bucket
nobody read is indistinguishable from one that happened. And **a term absent
from a bucket is absent, never a frequency of zero**: zero-filling is the most
natural thing to do to sparse lexical data and is wrong in a way nothing
downstream can detect.

**Rolling windows, moving averages and momentum are still not implemented.**
Temporally permitted is not extractor specified, and each needs its own decision
about what a gap means for *that* operation.

**Cross-source temporal alignment stays blocked by H-29**, along with any
`observed_at`, any `TIMESTAMPTZ` conversion and any "as of" wall-clock claim.
GDELT documents UTC for **Web News NGrams 3.0**, a different dataset whose `date`
is when an article was seen rather than a 15-minute aggregation bucket; that
sentence establishes nothing about ours.

**Only DETERMINISTIC OBSERVED interpretation is implemented**, by
`observed-signal-restatement@1.0.0` and by nothing else. **`INFERRED`,
`PREDICTED` and `RECOMMENDED` generation is not written and is not partially
written**: there is no module for it, no branch to reach and no parameter that
would select one. An inference needs a stated reasoning step, and adding one is
a version bump with a document behind it — not a flag.

`MODEL_DERIVED` remains unused. `validate_claims.py` fails the build on a model,
network or embedder import anywhere in the interpretation layer, and on a write
to any later-stage table.

**Opportunities and scoring stay blocked.** A Claim may exist without an
Opportunity, which is what makes Opportunity formation a separate decision
rather than a precondition — and Mission 1.13.1 created none. Nothing unblocks
`services/scoring`: D-03 is resolved at the framework level only, no
`CALIBRATED` profile exists, and every one of the seven real Evidence rows is
`NON_SCORABLE` for want of a reviewed reliability.

**The seven Claims establish no pain, desire, willingness to pay, pricing power,
competition gap, distribution feasibility, retention or revenue potential.** They
are factual, source-level claims about two publications. The first Claims
existing does not make Opportunity discovery ready.

**`ted-eu` is eligible, resource-ready, collected, normalized and derived from,
under ONE profile and through ONE route.** The operator recorded the acceptance
in Mission 1.15.6.1; Mission 1.15.7 authorised one concrete resource and wrote
`ted-search-api@1.0.0`; Mission 1.15.8 added the `procurement_notice` kind and
`ted-search-api-notice@1.0.0`; Mission 1.15.9 added `TRANSACTION_VALUE` and
correctly derived nothing; Mission 1.15.10 repaired the Decimal invariant as
`ted-search-api@1.1.0` and derived **one** Signal from an acquisition designed
for comparability. Mission 1.15.11 interpreted that Signal into one `OBSERVED` Claim and one
Evidence row through `observed-signal-restatement@1.1.0`. **11 RawRecords, 11
NormalizedRecords all `PARTIAL`, 1 Signal, 1 Claim, 1 Evidence.** Nothing
downstream of THAT: no ReliabilityAssessment applies to it, so it is
`NON_SCORABLE`, and no Opportunity consumes it. `ted-bulk-xml`, the historical CSV and
`commercial-multi-tenant-research-v1` are refused exactly as before, and H-36A,
H-36B, H-37 and H-38 are untouched.

**Four rules bound that collector, and each is enforced rather than promised**
(`ted-eu-search-api-collector-v1.md`): every bound is required with no default,
because TED's rate limit is UNKNOWN and the acceptance is conditioned on bounded
queries; there is **no exhaustion mode**, because the API's `ITERATION` scroll
would retrieve the corpus; there is **no fallback** to `ted-open-data-sparql`,
which is authorised and unimplemented, because a fallback turns a reviewed route
into a runtime choice; and the four monetary semantics stay under their own
names, with no `price_paid` and no currency conversion.

**Wikimedia Analytics pageviews is eligible, collected, normalized, derived
from, claimed and evidenced** (Mission 1.19, `wikimedia-pageviews-v1.md`). **21
RawRecords, 21 NormalizedRecords all `VALID`, 18 Signals, 18 OBSERVED Claims, 18
Evidence rows, every one `NON_SCORABLE`.** Outcome S1, and the contrast with
Mission 1.18 is the point: S0 there because a truthful derivation did not exist,
S1 here because one does.

**The blocker was a NAMED QUESTION and the answer was one page away.** Mission
1.8 downgraded this source on H-24 -- are aggregate pageview counts Licensed
Material under CC BY-SA? -- and that framing had one possibility it did not
consider. The Analytics API access policy answers under a heading called *Data
licensing*: the data is **CC0 1.0**, not CC BY-SA at all. **H-24 is answered for
the LOCAL profile only**; applying it commercially is a review act nobody has
performed, and approval never transfers (ADR-027).

**The first instrument in this catalog to waive the sui generis database right BY
NAME.** CC0 §1 defines Copyright and Related Rights to include *"database rights
(such as those arising under Directive 96/9/EC)"* and §2 waives them *"overtly,
fully, permanently, irrevocably and unconditionally"*. It resolves nothing about
TED's H-36A/H-36B. It shows what a resolution looks like.

**A confounder that is written into the record rather than into a caveat.** Both
members of a `content-request-change` are the SAME item, so prominence, title,
age and link structure cancel exactly -- which is why the cross-item contrast was
considered and REFUSED, since none of those cancel there and nothing in the
record can measure them. **The calendar does not cancel**: 2024-03-02 and 03-03
are a weekend and both larger articles fall about 40 per cent. That makes an
INFERENCE from the signal unsound rather than the subtraction untrue, and the
signal type, the migration and every Claim say so in their own words.

**A request is not a reader.** The claims say *counted*, name the platform's own
requester class in the sentence, and `user` means *not identified as automated*
rather than *human* -- the operator documents its own detection as heuristic. No
reliability was invented and no reliability mission was started: eighteen
`NON_SCORABLE` rows are the design working.

**The deterministic route to repeated-problem evidence is CLOSED, and it took
two acquisitions to establish it** (Mission 1.20). A second Stack Exchange
acquisition — pre-registered before any content was read, `tagged=docker` over
one month, 89 questions, one request — produced **0 Signals, 0 Claims, 0
Evidence**, and it failed differently from Mission 1.18.

**The narrow corpus delivered what a signature rule wants.** Three questions
share 182 characters of exact, stable, tool-specific Docker daemon diagnostic —
and the shared string ends at `exec: "`, exactly where the wrapper stops and the
failure begins. After it the source's own bytes read `permission denied`, `no
such file or directory` and `executable file not found in $PATH` — three
unrelated failures. **Calling those a file mode, a missing path and a `$PATH`
lookup is an ANALYST reading and not a source-native fact** (Mission 1.21 §0);
the deterministic finding is that the suffixes diverge and that no approved
normalization rule can collapse them into one problem identity. Support is 3 at every prefix length up to 182 and 1 from 184. **A
rule needs a length, and every length is either the envelope or the instance.**
Across all 89 questions, no error line of 40 characters or more repeats verbatim
in two of them.

**A diagnostic names the ENVELOPE; what makes two failures the same is underneath
it, and deciding that is a judgement about meaning.**

**What follows is a PROJECT DECISION, not a proof** (Mission 1.21 §0). An
experiment over 89 questions cannot establish that no narrower Stack Exchange
corpus could ever expose a source-native identifier. What Missions 1.18 and 1.20
establish is that the current approach has reached a **semantic boundary**. The
decision taken on that evidence: **the project will not spend another mission
trying to obtain repeated-problem identity by deterministic Stack Exchange query
narrowing.** The two remaining directions are semantic
INFERENCE — forbidden today, and an `INFERRED` claim by construction — or a
source carrying **explicit issue identity**, where the publisher links two
reports of one fault and the judgement sits with somebody who has the context.
The second is the smaller and more honest step, and every registered candidate of
that shape is `RESTRICTED` on retrieved terms.

**Stack Exchange is eligible, collected, normalized — and produced NOTHING
downstream, correctly** (Mission 1.18, `stack-exchange-questions-v1.md` §14).
**15 RawRecords, 15 NormalizedRecords all `VALID`, 0 Signals, 0 Claims, 0
Evidence, 0 ReliabilityAssessments.** Not blocked and not deferred: a derivation
was considered against the real questions and there was nothing to derive.

**A tag identifies a SUBJECT and never a PROBLEM**, and the sample is the
evidence rather than the argument. 15 questions carry 35 distinct tags; exactly
three appear more than once; no two questions share a complete tag set; no quoted
identifier repeats in any title. `python` is on all 15 because it is what the
query asked for, so a cohort built on it is a property of the retrieval.
`google-cloud-platform` groups duplicate Eventarc processing, a `setup.py` type
error and Google Docs text extraction. `deep-learning` groups the same `setup.py`
error and a backpropagation question. **One question is in both cohorts**, which
one repeated problem cannot be.

Getting past that would take semantic inference over question text, which is an
INFERRED step no Signal may rest on. **The cohort was not weakened to produce
output and no second query was run to find a friendlier sample** — a support
threshold lowered until something appears is a threshold that measures the
analyst. What would change the answer is a different ACQUISITION SHAPE, not a
different rule: many questions about one narrow tool, where a concrete failure
could actually recur. That is a mission with its own bounded acquisition and its
own review of what the query selects for.

**The consequence for the portfolio is the uncomfortable one.** `problem` now has
an approving, collected, normalized source and still no evidence, because what a
public Q&A site publishes is a published question, once each. **Not fifteen
people**: author identity is never acquired, so the deployment cannot count
distinct askers and no document may word itself as though it could (Mission 1.19
§0).

**The gap is narrower than Mission 1.18 first wrote it, and the correction
matters** (Mission 1.19 §0). It said *"no source in the portfolio observes the
same subject twice"*, which contradicts semantics already implemented here:
`lexical-frequency-change@1.0.0` re-observes one lexical stream across adjacent
buckets and `numeric-period-change@1.0.0` re-observes one metric across periods.
Repeated observation of an ENTITY is not missing. What is missing is **Evidence
establishing repeated comparable USER-PROBLEM instances for one narrowly defined
problem** — a series re-observes a stream, and neither re-observes a user meeting
the same difficulty. No proxy is proposed, because a proxy nobody can validate is
worse than an acknowledged gap.

**No collector may be implemented for a source that is not collector-eligible.**
D-07 is resolved and the registry exists. Two sources pass the gate; one has a
collector. The block is per source, and the orchestrator reports each by name
under one of two gates — `SOURCE-REGISTRY-GATE` when nothing is eligible,
`NO-COLLECTOR-IMPLEMENTED` when something is and nothing implements it.

Mission 1.4's debt is paid: `test_collector_conformance.py` asserts structurally
that the collector has no path to a URL outside `authorize_resource`, so the
guarantee is observed rather than architectural.

## Core principles

- Evidence before conclusions.
- Problem-first is valid, but not mandatory.
- Desire, curiosity, entertainment, creativity, learning, competition, social interaction, and other motivations are first-class opportunity drivers.
- Never treat an LLM opinion as observed market evidence.
- Distinguish observed facts, inferred signals, predictions, and recommendations.
- Preserve provenance for important data.
- Preserve uncertainty and confidence.
- Do not silently redefine domain concepts.
- Do not silently change architecture.
- Prefer small, testable, reversible changes.
- Avoid unnecessary complexity and premature microservices.
- Security, privacy, legal constraints, cost, and data quality are first-class concerns.

## Before implementation

For every non-trivial task:

1. Inspect the repository.
2. Read the relevant specifications and ADRs.
3. Identify dependencies and existing contracts.
4. State any ambiguity or contradiction before implementing.
5. Define acceptance criteria.
6. Implement the smallest coherent change.
7. Add or update tests.
8. Run relevant checks.
9. Update documentation when behavior or contracts change.
10. Summarize assumptions, evidence, tests, and remaining risks.

## Change control

If a requested change conflicts with an authoritative specification:

- Do not silently override the specification.
- Explain the conflict.
- Propose the smallest specification or ADR change needed.
- Wait for explicit authorization before changing foundational behavior.

If a concept must evolve, create a new version rather than mutating history without traceability.

## Evidence discipline

Any research claim presented by the product should, where technically possible, retain:

- source
- source type
- observation time
- extraction method
- provenance
- evidence level
- reliability
- independence
- confidence
- relevant raw/reference identifier

Copied, duplicated, or derivative content must not be counted as independent evidence.

## LLM discipline

LLMs are reasoning and synthesis components, not sources of truth.

When evidence is insufficient, output a hypothesis or uncertainty state rather than inventing a fact.

Never fabricate:

- sources
- metrics
- users
- prices
- market sizes
- competitor facts
- API results
- citations
- research outcomes

## Data collection

Use lawful, permitted, and technically appropriate acquisition methods. Respect source terms, robots directives where applicable, rate limits, authentication requirements, privacy constraints, and platform policies. Do not bypass access controls.

API keys and secrets must never be committed to the repository.

## Versioning

Foundational specifications use explicit versions in the filename, for example:

- `opportunity-ontology-v2.md` (current) — supersedes `opportunity-ontology-v1.1.md`
- `scoring-framework-v1.1.md` (current) — supersedes `scoring-framework-v1.md`
- `evidence-confidence-framework-v1.md` (current)
- `data-retention-policy-v1.md` (current)
- `evaluation-framework-v1.md` (current)

Material changes should create a new version and, when architectural, an ADR.

A superseded version is **never deleted**. It is retained as a historical record,
marked as superseded in `PROJECT_MANIFEST.md`, and its successor states in its
own §0 exactly what changed and under whose authority.

## Definition of done

A task is not complete merely because code exists.

It is complete when:

- behavior matches the specification,
- tests cover important behavior,
- failure modes are considered,
- observability is adequate,
- documentation/contracts are current,
- relevant quality checks pass,
- no known critical regression remains.
