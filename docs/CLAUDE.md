# CLAUDE.md — Startup Research OS

Version: 1.96
Last amended: 2026-09-05 (Sprint 1 / Mission 1.62)

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
| 1.96 | 2026-09-05 | **ANCHOR_ENQUIRY_REQUIRED_PARTNER_PACKAGES_COMPLETE: three complete packages, three different failures, and no apparatus qualifies.** Mission 1.60 left all three candidates at a documentation wall, which told us nothing about any of them; each is now decided on its own merits and each fails somewhere different. **LeakIX fails B2 on DOCUMENTED TIMESTAMP SEMANTICS**: its three date fields are an indexing date, a first-detection date and a last-detection date, and none is an observation event -- so a window filter selects hosts whose LAST DETECTION fell inside it and a host present throughout is missing from the set, which is Mission 1.59's failure exactly. **Its B3 PASSES on a documented SSH banner field and the pass is recorded anyway**, because a gate is judged on its own question -- and §43 forbids letting a perfect banner compensate for a missing observation-window selector. **SHADOWSERVER FAILS ON A DISTINCTION THIS ARC HAD NOT YET NAMED**: it performs its own daily internet-wide scanning, and its reporting API states that a requester *only gets the data on the networks they are responsible for* and *will not be able to get data on other networks or systems*. **It scans everything and can show us only ours.** Its observation-window selector is the cleanest of the three and its retrievable frame is the requester's own networks, so two requesters retrieve two different populations and no proposition about the internet can be witnessed through it -- a **FAIL rather than an UNKNOWN**, because it is an affirmative documented statement rather than a silence. **ONYPHE IS UNRESOLVED WITH FOUR PARTIAL SLOTS AND ITS B3 NOW PASSES**: the data model documents a `data` field holding the raw application response, full-text searchable up to 1 MB, kept distinct from a normalised `summary` -- which closes the field-name gap Mission 1.61 recorded. **Its B2 turns on an ambiguity that was NOT resolved favourably**: the timestamp is documented as the moment the data was collected, and in the same sentence as tracking when a service was LAST OBSERVED. Those are two different temporal objects, and resolving an ambiguity in the direction that keeps a candidate alive is what this arc has refused four times. It also documents a scanner node id and country PER RECORD with weekly scans alternating origin country, so its vantage is **MULTI_VANTAGE_SEPARABLE**, which is more than the anchor publishes about itself. **THE ANCHOR'S A8 STAYS PARTIAL AND ONE ANSWER WAS DOWNGRADED, WHICH IS THE AUDIT WORKING**: ten topics, two answered, four partial, four unknown. **FRAME moved ANSWERED -> PARTIAL** once ELIGIBLE and ATTEMPTED frame were separated -- the range is declared and which addresses were actually probed is not. **RETRY moved PARTIAL -> UNKNOWN** once the API's throttling and retry parameters were correctly identified as governing the CLIENT retrying the API rather than the SCANNER retrying a probe; answering a measurement question with a transport-library setting was the easiest mistake available. Sampling, vantage and missingness remain unknown, and the most likely remaining document, the data collection policy, closes none of them. **TWO RETRIEVAL-SURFACE CONSTRAINTS WERE ESTABLISHED THAT NOBODY KNEW.** The API reference states that if the index parameter is not supplied *the search is conducted using the latest publicly available internet scan data* -- the verbatim confirmation of the Mission 1.61 A2 bound. And **the count endpoint returns an ESTIMATE with an error margin not exceeding three per cent above one thousand results**: the construct is a count of distinct addresses across public IPv4 and will exceed one thousand, so a threshold evaluated against it would compare a bound against an estimate whose error band could decide the direction -- **a SUPPORTS or CONTRADICTS produced by the estimator rather than by the world**, which is the artefact-recorded-as-a-finding failure this layer must not have. It bounds HOW the value must be obtained, not whether it can be. **THE FROZEN ENQUIRY WAS NOT EDITED AND NO DUPLICATE HASH WAS MANUFACTURED**: all seven questions compared against the updated matrix, all seven STILL_UNRESOLVED, so v1 remains current and Mission 1.61's exact hash stays authoritative. The count-estimate finding was deliberately NOT added, because it is documented rather than missing and adding it would ask the provider to restate its own documentation. **A CONTACT PAGE WAS FOUND AND NO ADDRESS WAS INVENTED**: the printed address is served through an obfuscation mechanism and the retrieval returned a placeholder, recorded as FIRST_PARTY_CONTACT_CHANNEL_NOT_ESTABLISHED beside the page that carries it, because a valid question and a valid channel are two different facts. **THE BRIEF'S OWN INSTRUCTION CAUGHT AN ATTRIBUTION ERROR IN THE BRIEF**: it assigned two blockers to the wrong candidates and told the mission to resolve each from the artifact, which assigns them the other way round. **TWO REQUIREMENTS JOIN THE REGISTRY, NOW THIRTEEN**: THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME and DEFAULT_DATA_SURFACE_MUST_NOT_OVERRIDE_QUALIFIED_EXPOSURE_PATH, the second governing IMPLEMENTATION where OBSERVATION_ADDRESSABLE_EXPOSURE governs SELECTION. Earlier missions' records were **not rewritten**. 24 of 24 first-party retrievals, five returning nothing usable and counted anyway, **0 measurement queries, 0 counts, 0 host records, 0 banners, 0 facets, 0 downloads, 0 trials, 0 purchases, 0 enquiries sent**. 0 canonical mutations, 0 sources registered, 0 governance reviews, 0 Claims, 0 Evidence, 0 reliability values, 0 independence groups, 0 model calls, 0 embeddings, the Mission 1.56 Claim untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **126 deliberate violations, 126 caught** -- three of which edited the frozen enquiry -- and **1656 bare-python tests run before commit** |
| 1.95 | 2026-09-05 | **ANCHOR_LINEAGE_CONFIRMED_OPERATIONAL_QUESTIONS_REMAIN: the sentence four missions said the documentation did not contain is in the documentation, and reading it took two retrievals of one page.** **A7 CLOSES AT LEVEL 2 AND THE STANDARD WAS NOT LOWERED TO CLOSE IT.** The apparatus states first-party and verbatim that *all the data is collected independently by Netlas itself*, that *we do not rely on third parties or aggregators*, and that *every record is obtained and indexed directly by the platform* -- followed by a clause naming **the only exceptions** as threat intelligence shown in one tool and geolocation supplied by partners. That is an affirmative claim with a **CLOSED** exception list, and each exception was then checked against the load-bearing predicate ONE BY ONE: a reputation annotation is not the presence of a service on a host, and where an address sits is not whether it answered on a port. **A LEVEL 1 STATEMENT WOULD NOT HAVE CLOSED IT**, and this mission supplies the contrast from the other side -- a partner candidate says its data comes from daily internet-wide scans, sinkholes, honeypot sensors, sandboxes, blocklists **and many other sources**, an affirmative claim whose list does not end and therefore cannot be checked against anything. **THE BLOCKER NARROWED RATHER THAN MOVED**: seven PASS, one PASS_WITH_STATED_BOUNDS, one PARTIAL, and `which_gates_block` goes from `[A7, A8]` to `[A8]` -- and the apparatus **still does not individually qualify**, because the gate set is conjunctive and one PARTIAL is one short. **A8 MOVED WITHOUT PASSING, AND THE MOVEMENT IS THAT THE QUESTIONS ARE NOW ENUMERATED**: eleven asked, four answered, four partial, three unanswered. Answered are the address frame, **port 22's inclusion in the current scanned list** which Mission 1.60 explicitly recorded as NOT established, the record identity -- which settles that one record is one service RESPONSE, so a count of addresses must be a DISTINCT count and never a row count -- and the scan-date semantics. Unanswered are **sampling**, failure semantics and vantage, and sampling is the load-bearing one because SAMPLING_IS_LOAD_BEARING says two apparatuses cannot be compared as one count unless both expose the same population definition. **A BOUND WAS FOUND ON A GATE A PREVIOUS MISSION PASSED, AND RECORDING IT IS THE AUDIT WORKING**: the apparatus's DEFAULT search surface is a maintained current-state view -- its own documentation says a fully scanned subnet *replaces* the previous version in the default output and recommends searching without specifying an index -- which is **MAINTAINED_CURRENT_STATE_LAST_CHANGE, the exact temporal object Mission 1.59 rejected**. A2 still passes, because the gate asks whether a window is selectable in the REQUEST and the dated index mechanism is documented and selectable, but the pass rests entirely on the NON-DEFAULT path and a collector using the default would be reading the rejected temporal object while a record elsewhere said the gate had passed. **VANTAGE MOVED FROM NOT_ESTABLISHED TO NOT_DOCUMENTED**, the Mission 1.35 distinction between empty because nobody looked and empty because somebody looked: three pages and the response schema consulted, no scanner count, no locations, and **no record field identifies a scanner node or probe origin**, so vantage could not be established after the fact even by inspecting retrieved data -- and it is asked before pairing because it is where FRAME_INSIDE_THE_DEFINITION would recur. **PORT-22 WINDOW COVERAGE GIVES TWO ANSWERS AND THE RECORD REFUSES TO COLLAPSE THEM**: current inclusion ESTABLISHED, window addressability `PORT_22_NOT_ESTABLISHED`, because the changelog dates the SIZE of the port list -- one entry doubling it, a later one taking it past a thousand -- and never its MEMBERSHIP. No removal is recorded anywhere, which is favourable evidence about direction and **is not a guarantee**. **ALL THREE PARTNER CANDIDATES HAD THEIR DOCUMENTATION RECOVERED, AND THE WALL WAS THE PATH RATHER THAN THE APPARATUS**, each failure with a named cause: documentation moved twice onto a wiki its own site redirects to; documentation kept on a search subdomain rather than the marketing domain both Mission 1.60 paths tried; a path one level too deep. Four of eighteen B-slots established, five partial, nine unread. **NO PARTNER IS QUALIFIED, RANKED OR SELECTED**, and the record NAMES the preference it declined to express -- one candidate emerged with a documented multi-continent vantage, a documented weekly frame and a published retention table, which is more than the anchor publishes about itself on two of those three, and treating that as a lead would be picking a partner from a first pass in which two rivals had pages that did not load. **AN ENQUIRY IS DRAFTED AND NOT SENT**: seven questions, nothing already documented asked -- the validator refuses a question whose topic the operational record marks ANSWERED -- no data, no access, no trial and no price requested, hashed to `310acf28...a049c4` with the hash recorded in the CLOSURE record rather than in the enquiry, because writing a hash into the document it is a hash of changes the bytes it was frozen at. **No recipient address is recorded**, because none was retrieved first-party and inventing one would fabricate a fact about the apparatus. **THE VALIDATOR CAUGHT THIS MISSION'S OWN RECORD**: the forbidden-ask scan refused the enquiry's own sentence saying it asks for no trial and no evaluation account, `testing-strategy.md` §23 for the sixth time, and the repair scopes the scan to the text that would actually be TRANSMITTED rather than weakening the rule -- which is also stricter. **TWO REQUIREMENTS JOIN THE REGISTRY, NOW ELEVEN**: ENUMERATED_EXCEPTIONS_MAKE_A_LINEAGE_CLAIM_CHECKABLE and LINEAGE_EXHAUSTIVENESS_IS_NOT_FRAME_EXHAUSTIVENESS, the second being the one most easily lost -- that every record was self-collected says nothing about which addresses were reached. Mission 1.60's records were **not rewritten** and still read ANCHOR_B_LINEAGE_PARTIAL blocking A7 and A8. 16 of 20 first-party retrievals, anchor 7 of 8 and partners 9 of 12, **0 queries executed, 0 counts, 0 host records, 0 facets, 0 trials, 0 purchases**. 0 canonical mutations, 0 sources registered, 0 governance reviews, 0 thresholds, 0 Claims, 0 Evidence, 0 reliability values, 0 independence groups, 0 model calls, 0 embeddings, the Mission 1.56 Claim untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **101 deliberate violations, 101 caught**, and **1592 bare-python tests run before commit** |
| 1.94 | 2026-09-05 | **APPARATUS_LINEAGE_NOT_AFFIRMATIVELY_ESTABLISHED: the anchor requalified on both gates that killed the last two pairs, and what blocks it is now a sentence its documentation does not contain.** Applying the gates BEFORE choosing -- which is the whole point of the new ordering -- the anchor passes **A2** on two independent mechanisms: an `indices` request parameter selecting a data-collection DATE, and date ranges over a per-record `scan_date` that documents when the scanning which GENERATED the response occurred, with daily scan volumes downloadable as dated JSON files on top. The window is chosen in the REQUEST, not discovered after retrieval. And it passes **A3 in the strongest exposure class available**, `RAW_IDENTIFICATION_STRING`: a queryable `*.banner` field with wildcard matching plus port filtering, so the RFC 4253 prefix predicate is expressible against the bytes the peer sent rather than against a vendor's service label. **SIX OF NINE GATES PASS, ONE PASSES WITH STATED BOUNDS, AND TWO ARE PARTIAL.** A7 stays PARTIAL because the documentation is not silent about its own scanning, it is silent about EXHAUSTIVENESS -- and inferring exhaustiveness from a list of enrichment sources would be reading a positive claim out of a negative space. **That is the same refusal for the fourth mission running, and it is the one most tempting to abandon now that everything else about this apparatus works.** A8 stays PARTIAL on operational questions nobody has asked: retries, duplicate handling within a window, address-identity counting, and what a missing record means -- **but its load-bearing classification is a standard-defined prefix on an exposed banner rather than a proprietary fingerprint**, so what remains unreviewed is operational rather than semantic, which is the difference from the dropped apparatus. **THE BLOCKERS CHANGED KIND**: they are no longer about what the apparatus measures or how it exposes it, and both close by reading or asking rather than by finding a different scanner. **NO PARTNER REACHED PAIR ANALYSIS, AND THE REASON IS RECORDED HONESTLY**: three candidates were probed and all three failed at **A6** -- their first-party technical documentation was not retrievable at the paths tried -- which is a fact about this mission's reach and not a finding about those apparatuses. The asymmetry is in documentation ACCESS, not in apparatus quality, and the record says what the search does NOT establish: that no qualifying partner exists. **THE OUTCOME FITS IMPERFECTLY AND THE RECORD SAYS SO** rather than choosing the label whose wording bends most easily: outcome G is defined for a promising PAIR and there is a promising ANCHOR, so the clause is half-satisfied. It was still chosen because it names the ESTABLISHED blocker rather than the merely unexplored one, and because no partner can rescue an anchor whose own lineage is unproven -- while `NO_OBSERVATION_ADDRESSABLE_PARTNER_IDENTIFIED` would assert the anchor qualifies and `ANCHOR_APPARATUS_INVALIDATED` would call an unproven negative a refutation. **THE REQUIREMENT REGISTRY IS THE REUSABLE OUTPUT**: nine rules from Missions 1.47 to 1.59 -- SOURCE_EXCLUSIVE_METRIC, RELIABILITY_REVIEWABILITY, FRAME_INSIDE_THE_DEFINITION, AFFIRMATIVE_LINEAGE_REQUIRED, PRODUCT_RELEVANCE, READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT, OBSERVATION_ADDRESSABLE_EXPOSURE, THE_TEMPORAL_OBJECT_TEST and SAMPLING_IS_LOAD_BEARING -- now sit in ONE record with the mission that paid for each, so route discovery reads a registry instead of a chain of reports. **Every one of them was learned AFTER a pair had been chosen**, which is exactly why they are now applied before. **TWO SMALL RULES WERE MADE STRUCTURAL**: a query returning only a count still returns a measurement value and is not metadata because only a number came back; and a zero-cost trial destroys preregistration exactly as a paid one would, because access cost is irrelevant to epistemic contamination. **THE FALSIFIABILITY TRAP WAS CAUGHT BEFORE IT MATTERED**: a windowed count makes host membership an existential within the window, which looks monotone -- and the CLAIM is a count against a bound, which a lower count contradicts. Host-level monotonicity is not Claim-level monotonicity, and conflating them would have invented a falsifiability problem or hidden one. 10 of 15 first-party documentation retrievals, **0 queries executed, 0 counts, 0 host records, 0 facets, 0 trials, 0 purchases**. 0 canonical mutations, 0 sources registered, 0 governance reviews, 0 thresholds, 0 Claims, 0 Evidence, 0 reliability values, 0 independence groups, 0 model calls, 0 embeddings, the Mission 1.56 Claim untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **85 deliberate violations, 85 caught**, and **1529 bare-python tests run before commit** with 3310 pytest tests after |
| 1.93 | 2026-09-05 | **SNAPSHOT_TIME_SEMANTICS_NOT_ALIGNABLE: the pair is dropped on a gate that is not about scanning at all, and the class survives.** The two scanners really do probe independently, really do measure the same construct, and **publish different KINDS OF TEMPORAL OBJECT**: one a stream of observations each carrying the time it was made, the other a maintained current state whose SEARCHABLE time field records when a record last CHANGED. **THE DECIDING SENTENCE IS THE VENDOR'S OWN WORKED EXAMPLE**: a host observed every day for five days WITHOUT CHANGE carries a searchable `last_updated_at` from five days ago, and its per-service `observed_at` is documented as not searchable because observation timestamps change too fast to publish. So a window filter selects hosts whose record CHANGED during the window on one side and hosts OBSERVED during it on the other -- **the same filter expression picks out two different populations**, and a host present and unchanged throughout is in one set and missing from the other. **A CONTRADICTION PRODUCED THAT WAY WOULD BE AN ARTEFACT RECORDED AS A FINDING**, which is the worst failure available to this layer, and it is why the gate is not negotiable. **FOUR ALIGNMENT RULES WERE EVALUATED AND ALL FOUR REFUSED**, including the two that would have salvaged the route: a pre-frozen tolerance was refused because §16 demands an operational basis and the merged side publishes NO BOUND on how stale a member of its current state may be, so any delta would be a round number chosen precisely because it rescues the route; and snapshot-inside-interval was refused because establishing it needs per-host timelines, which means retrieving the set and inspecting it afterwards -- **the exact procedure §18 fails the gate for**. **FAIL RATHER THAN UNKNOWN, AND THE DISTINCTION IS EARNED**: the named cadence document Mission 1.58 could not retrieve was pursued and ANSWERED -- one side documents a per-record `scan_date` recording when the scanning that generated the response occurred -- so this is an established mismatch on first-party documentation from both sides, not a document nobody found. **THREE GATES THAT PASSED A MISSION AGO NOW READ WORSE, AND THAT IS THE AUDIT WORKING** (§30): population reopened on a disclosure that was there to be read, that under high service density one side's service data represents a **SAMPLING** rather than a census, so a partial frame must not be called internet-wide; reliability reviewability reopened because the narrowed metric now turns on how each side decides a wire-level predicate and one side's fingerprinting is proprietary; and threshold-freezability fell as a consequence of gate 5, because a bound can only be frozen in advance if the observations it will meet can be identified in advance. **WHAT SURVIVES IS WORTH MORE THAN THE PAIR.** A PROTOCOL-NATIVE CONSTRUCT now exists, written source-free: hosts that answer with an identification string beginning `SSH-` before any negotiation, fixed by **RFC 4253 §4.2**, which also states that other server output MUST NOT begin with `SSH-`. No vendor taxonomy, no fingerprint, and **matching vendor labels are explicitly refused as metric equivalence** -- two vendors may both say PRODUCT-X while using different signatures, versions, banner fields and post-processing. **AND THE NARROWING REMOVES A SHARED UPSTREAM NOBODY HAD NOTICED**: a version- or vulnerability-flavoured metric would have pulled a common CVE database into the load-bearing path on BOTH sides, which is a shared upstream for the metric's MEANING even though the scanning stays independent. **A NEW APPARATUS REQUIREMENT IS ADDED: OBSERVATION_ADDRESSABLE_EXPOSURE** -- an apparatus qualifies only if a future observation can be attributed to a defined window FROM ITS PUBLISHED SURFACE, before any value is retrieved. That is not the same as scanning often, and Mission 1.58 could not have known to ask for it. **THE GENERALISABLE DIAGNOSTIC**: a dataset can be excellent and still be the wrong TEMPORAL OBJECT -- a maintained current-state view answers *what is running now* and a preregistered threshold proposition asks *what was observed during a window*, and only one of those can witness this kind of Claim. **GATE 10 WAS ADVANCED RATHER THAN CLOSED, AND ONLY FOR THE SIDE THAT SURVIVES**: apparatus B's provenance moved from an ABSENCE of any third-party reference to a POSITIVE statement about the load-bearing records, and it is still short of an affirmative denial, so it stays PARTIAL -- §22 applied rather than forgotten. Apparatus A's lineage was not pursued further because gate 5 had already dropped the pair, and saying so is better than reporting an unfinished check as a finished one. **0 measurement endpoints called, 0 measurement values fetched, 0 paid access, 0 trials** -- load-bearing, because PREREGISTERED is defined against RETRIEVAL. 8 of 12 first-party documentation requests used, every load-bearing one first-party. 0 canonical mutations, 0 sources registered, 0 governance reviews, 0 thresholds, 0 Claims, 0 Evidence, 0 reliability values, 0 independence groups, 0 model calls, 0 embeddings, the Mission 1.56 Claim untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **77 deliberate violations, 77 caught** -- one of which ESCAPED first, a sentence that conflated structural non-republication with apparatus lineage, and the validator was tightened rather than the record loosened. **1488 bare-python tests run before commit** with 3310 pytest tests after |
| 1.92 | 2026-09-05 | **PRODUCT_RELEVANT_INDEPENDENCE_CLASS_IDENTIFIED_GATES_OPEN: the operator withdrew the CO2 route, made product relevance a GATE, and the broadened search found the one class satisfying the whole conjunction.** **A WITHDRAWN SELECTION IS APPENDED TO, NEVER EDITED AWAY**: Mission 1.57's record still reads `selected_route: ROUTE-A` with the withdrawal appended beside it, because deleting the field would lose what the operator decided AGAINST -- which is the entire content of the decision -- and the validator refuses a supersession that removed it. **AND A RULE CHANGE IS NOT A CORRECTION**: Mission 1.57's reasoning was sound under the rule it was given, its brief listed relevance under preferences and omitted it from the selection rule, and it flagged this exact reservation before asking for approval. Filing a sound analysis as an error would misdescribe both the analysis and the decision. **GATE 16, PRODUCT_RELEVANCE, IS MANDATORY AND ITS COST IS STATED**: the construct must bear on a named Opportunity dimension, and this narrowing intersects Mission 1.57's own law directly -- product-relevant quantities are overwhelmingly platform-mediated and platform-mediated quantities are measured once -- so an empty conjunction was the honest possibility. **SEVEN CLASSES SURVEYED, ONE SURVIVES.** Package downloads, business registers and app-store catalogues are source-exclusive. Web-crawl technology surveys are `FRAME_INSIDE_THE_DEFINITION` again, each crawler defining its own site population, and one takes its origin list from a single platform's dataset so the FRAME has a common upstream even where the crawling is independent. Job postings against official vacancy statistics are genuinely independent producers of TWO DIFFERENT CONSTRUCTS -- a vacancy is not a posting. **A NEW TRAP WAS FOUND AND NAMED, BY CERTIFICATE TRANSPARENCY**: several independent log operators carrying the SAME certificate submitted to each. **READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT**, and it supplies the sharpest test this arc has had: *if the two apparatuses disagree, is that a fact about the world or a bug?* For two readers of one published number a disagreement is a bug; for two scanners probing the internet it is a real difference in coverage, timing or fingerprinting, which is exactly what independent corroboration is supposed to tolerate. **THE SURVIVING CLASS IS INTERNET-WIDE ACTIVE SCANNING, AND ITS INDEPENDENCE ARGUMENT IS STRUCTURAL RATHER THAN DOCUMENTARY**: population figures have an upstream PRODUCER so everyone else distributes; **host counts have none, because nobody publishes how many hosts run a service**. Each apparatus must generate the number by probing, so the failure mode that killed World Bank plus FRED, World Bank plus Eurostat and every platform pair is not merely absent here, it is **structurally unavailable** -- and that argument cannot be undone by one party changing its data-sourcing policy. **THE LAW IS REFINED RATHER THAN REFUTED**: a quantity is independently measurable exactly when NO party is in a position to publish it authoritatively, and the internet as a whole is such a quantity even though every host on it belongs to somebody. **NO ROUTE WAS SELECTED, AND THAT IS THE POINT**: twelve of sixteen gates pass and the set is conjunctive, so selecting the best route found is not selecting one that qualifies, and the operator asking for a broadened search is not a reason to lower the bar. Three gates are open and each names how to close it: **gate 3**, because vendor fingerprinting is proprietary and the construct must be narrowed to what the PROTOCOL defines or it becomes the CPI-basket failure in a new domain; **gate 5**, because two snapshot censuses of a continuously changing population need a shared *as of when* and one side's cadence article was not retrievable; **gate 10**, because one apparatus states its provenance affirmatively and the other only by omission -- **and an absence of a reference to third-party data is an absence rather than a statement**, which is Mission 1.57's own correction applied rather than forgotten. **THE NEXT MISSION IS EPISTEMICS BEFORE GOVERNANCE**, inverting Mission 1.57's recommendation for a reason: there the epistemics were closed and only a review remained, here gate 5 decides whether the two apparatuses measure one proposition at all, and buying a licence first would be paying to discover a semantic problem. 0 research-data requests, 8 first-party documentation requests, **0 measurement values fetched** -- load-bearing, because PREREGISTERED is defined against RETRIEVAL and one value would destroy it permanently. 0 canonical mutations, 0 sources registered, 0 reviews, 0 collectors, 0 thresholds, 0 Claims, 0 Evidence, 0 independence groups, 0 model calls, 0 embeddings, the Mission 1.56 Claim untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **103 deliberate violations, 103 caught**, and **1453 bare-python tests run before commit** with 3310 pytest tests after |
| 1.91 | 2026-09-05 | **INDEPENDENCE_CAPABLE_ROUTE_GOVERNANCE_PENDING: one apparatus pair passes every epistemic gate, and the reason 29 registered sources yield none is now a stated law rather than a run of bad luck.** **THE STRUCTURAL FINDING IS THE MISSION**: *a quantity that exists only because a platform recorded it can be measured only by that platform; a quantity that exists in the world independently of any measurer can be measured by more than one apparatus* -- and **every source in this portfolio measures the first kind**. Wikimedia's request counts exist because Wikimedia's servers logged them, Stack Overflow's question counts because Stack Overflow published them, GDELT's frequencies because GDELT crawled and counted, TED's totals because authorities filed notices there. Each is the SOLE possible apparatus for its own quantity, so a second API, dump, mirror or dashboard is a second COPY and never a second MEASUREMENT. **It generalises Mission 1.46 one domain over**: there the measurement happened once at Destatis and the international publishers were distribution layers; here it happens once at the platform and every interface is a distribution layer. **Two findings, one fact about where measurement actually occurs.** **10 held apparatuses inspected, exactly ONE shared subject** (`docker`, the same one Mission 1.47 found), and the one held pair is `COMPLEMENTARY_NOT_CORROBORATING` -- a content request is what a READER'S CLIENT makes of a server and a published question is what a PERSON writes about being stuck. **ADR-036 removed the identity blocker that stopped those two ever reaching one Claim; it did not make a request a question**, and saying so is the whole discipline of this mission. **THE NEGATIVE CONTROLS WERE RE-RUN AND STILL FAIL, WHICH IS THE ONE WAY THIS COULD HAVE GONE WRONG**: World Bank + FRED is still `DEPENDENT_REPUBLICATION` on FRED's own `Source Code SP.POP.TOTL`; World Bank + Eurostat is still `COMMON_UPSTREAM_SOURCE and SEMANTIC_MISMATCH`; and neither was promoted on the grounds that the architecture changed, because **the INFERRED layer fixes Claim IDENTITY and repairs neither provenance dependence nor a 1 January stock against a midyear estimate**. **THE SELECTED ROUTE IS AN ATMOSPHERIC MOLE-FRACTION PAIR AT ONE FIXED SITE, AND THE DECISIVE EVIDENCE IS A CALIBRATION SCALE RATHER THAN AN ORGANISATION CHART**: the two programmes report on DIFFERENT reference scales, and a republished series carries the originator's scale. Both sides state it first-party -- one says outright that it operates an independent sampling network rather than obtaining data from the other, and the other describes that data as independent and uses it for comparison, **and comparison for validation is not consumption**. Separate instruments, separate laboratories, separate scales. **AND THE LIMITATION IS RECORDED RATHER THAN SMOOTHED**: they share the SITE and one provides in-kind field support, so their ERRORS are not independent even though their provenance is -- **provenance independence is not error independence**, and a site-level artefact would move both. **THE SCALE DIFFERENCE BECOMES A THRESHOLD CONSTRAINT**, which is the practical half: a bound placed close enough for the documented offset to decide the comparison would manufacture a contradiction out of a calibration difference, so the next mission must place it clear of that offset and record the reasoning BEFORE any value is retrieved. **THE VALIDATOR CAUGHT MY OWN RECORD**: the rejected web-traffic route was first written `KNOWN_INDEPENDENT` with no basis, because the two really are separate systems -- and §15 requires affirmative documentation from BOTH sides before that word may be used. Corrected to **UNKNOWN**, which costs nothing since the route is rejected anyway and which is exactly the shortcut the standard exists to refuse. That route fails for a better reason: each apparatus measures share WITHIN ITS OWN NETWORK, both stating so first-party, so **the frame sits inside the metric definition** and any proposition admitting both must define its event class as a disjunction of the two networks -- **source attribution relocated from the subject of the sentence into its predicate**, which is Mission 1.47's finding recurring in a new place and now named as the `FRAME_INSIDE_THE_DEFINITION` trap. **NO VALUE WAS FETCHED, AND THAT IS LOAD-BEARING**: `PREREGISTERED` is defined against RETRIEVAL, so a single measurement fetched during feasibility work would have made an honest preregistration impossible for ever. **RESEARCH_DATA_REQUESTS = 0**, 6 first-party methodology requests, 0 measurement values. **THE RESERVATION IS STATED WHERE THE OPERATOR WILL READ IT**: atmospheric CO2 is not a quantity this product will research. §20 makes relevance a preference rather than a gate and §46's selection rule omits it, so selection is permitted -- and the honest reading is that the route is an APPARATUS route whose purpose is to make the aggregator stop being algebraically identical to B-2, with a **stated transferability limit**, because what it can establish is that the mechanism works on real independent data and not what its parameters should be for a request count. **The alternative inside this portfolio is none, and that is the finding rather than a gap in the search.** Governance is the sole blocker and it is an UNASKED QUESTION rather than a refusal: neither apparatus is registered, no review exists, and §29 forbids creating one here. 0 canonical mutations across every counter, 0 sources registered, 0 collectors, 0 thresholds, 0 Claims, 0 Evidence, 0 reliability assessments, 0 independence groups, 0 Scores, 0 Opportunity changes, 0 model calls, 0 embeddings, the Mission 1.56 Claim untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **79 deliberate violations, 79 caught**, and **1439 bare-python tests run before commit** with 3310 pytest tests after |
| 1.90 | 2026-09-05 | **FIRST_DETERMINISTIC_INFERRED_CLAIM_PERSISTED: one attended write, approved against a frozen hash, and the evaluator said CONTRADICTS.** Signal `064d12bf` measured **912** requests against a bound of **1000**, so the proposition is refuted by its own witness -- and **that is the pilot succeeding**, because the manifest declared all four results legitimate BEFORE the evaluation ran and §1 forbids defining success as SUPPORTS. **THE REPOSITORY'S FIRST `CONTRADICTS` EVIDENCE ROW**: Mission 1.48 measured 57 rows, found every one SUPPORTS, and established why -- `direction` is proposition identity at the OBSERVED layer, so an interpreter there cannot contradict a Claim it already restated. ADR-036 removes direction from identity, and the census now reads **SUPPORTS 57, CONTRADICTS 1**. **AND THE CONTRADICTION CASE IS STILL UNREACHED, REPORTED IN THE SAME BREATH**: contradiction enters the arithmetic when ONE Claim carries both directions, `claims_carrying_both_directions` is **0**, and this proposition can never acquire a second witness -- only Wikimedia's own logs can measure requests to a Wikipedia article, which is the `SOURCE_INDEPENDENCE_IS_PARTIAL` limitation the operator was asked to weigh before approving. Reporting the first half alone would overstate what changed. **THE APPROVAL IS A HASH, AND THAT IS WHAT MAKES IT NAME A DOCUMENT**: the runner recomputes it and refuses anything else, proven by a run against a wrong hash that wrote **0 rows**. **THE MANIFEST WAS NOT EDITED AFTERWARDS, DELIBERATELY** -- marking it APPROVED would change its bytes and therefore its hash, and a frozen document that no longer answers to the hash it was frozen at is not frozen; the validator now REFUSES any status but `AWAITING_OPERATOR_APPROVAL` for exactly that reason, and the CI gate re-checks the recorded hash against the manifest on disk so a later edit turns the gate **red** rather than leaving *approved* beside a document nobody approved. **PREREGISTERED WAS ARITHMETICALLY IMPOSSIBLE RATHER THAN MERELY UNAVAILABLE, AND IT IS EXECUTED RATHER THAN ARGUED**: the measurement was retrieved at `2026-09-01T21:03:47Z` (read from `acquisition.raw_records`, not recalled), the bound could not be recorded before today, and a test hands the REAL evaluator a PREREGISTERED registration with exactly these timings and gets **UNKNOWN / PREREGISTRATION_TIMING_INCONSISTENT**. POST_HOC is the only representable classification; the bound sits **ABOVE** the measurement so the pilot cannot be read as fitted; and the disclosure that 912 was visible when 1000 was chosen is written INTO the manifest rather than left out of it. **THE BOUND WAS COMMITTED BEFORE THE EVALUATOR WAS CONSTRUCTED**, because registering a threshold on the way past is the analyst choosing the number while the comparison runs. **IDEMPOTENCY IS DEMONSTRATED, NOT PROMISED**: the whole evaluation and persistence replayed to `REUSED` with **0 rows created** and every counter identical. Envelope checked before and after -- `threshold_registrations +1`, `claims +1`, `claim_revisions +1`, `evidence +1`, `claim_derivations +1`, refusals **+0**, every other counter unchanged. **THE STATEMENT IS COMPOSED FROM THE TARGET AND NOTHING ELSE**, as Mission 1.55 designed: it names no witness, no measurement and no source, so a second witness would append Evidence rather than a revision. **THE DERIVATION NAMES THE OBSERVATION IT REASONED FROM**, selected structurally rather than by a manifest field -- the Signal witnesses TWO OBSERVED Claims and the detailed restatement is the one whose proposition carries the same two day labels, because Mission 1.43's convergent existential deliberately carries none. **THE NEW SCOPE REACHES NO REVIEWED RELIABILITY, AND THE NEAR MISS IS THE TEST**: through the REAL resolver over all four current assessments and their real basis rows, `NO_APPLICABLE_ASSESSMENT`. The reviewed Wikimedia **0.65** shares source, resource and record kind and differs on `claim_type` **AND** `proposition_kind` -- both real, since a threshold proposition is a different question from a restatement of the count and an INFERRED derivation is a different question from an OBSERVED one. Evidence `NON_SCORABLE`, aggregation `UNAVAILABLE`, **no number invented**. **A PRE-EXISTING DEFECT SURFACED AND WAS REPAIRED RATHER THAN MASKED**: `test_ted_operator_acceptance.py` ran `fetchone()` with no `ORDER BY` over the two acceptance rows Mission 1.46 left and pinned review version 2, so it passed or failed on row order; it now asserts the property over every row plus that no two review versions share a `verifier_version`, which is what a replay of an older acknowledgement would look like. 0 network requests, 0 model calls, 0 embeddings, 0 acquisitions, 0 sources added, 0 ReliabilityAssessments, 0 independence groups, 0 Scores, 0 Opportunity changes, no migration, evaluator and orchestrator untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **76 deliberate violations, 76 caught** and each checked to have been refused by ITS OWN gate rather than by the hash check, and **1400 bare-python tests run before commit** with 3310 pytest tests after |
| 1.89 | 2026-09-05 | **DETERMINISTIC_EVALUATION_PERSISTENCE_ORCHESTRATION_READY: the already-built pieces are connected, and readiness is reported in TWO HALVES rather than collapsed.** One command routes an `EvaluationOutcome` to exactly one of two paths inside the CALLER's transaction -- directional writes Claim, ClaimRevision, derivation and Evidence together or not at all; a refusal writes one row and nothing else. **FOUNDATION_READY true, UNATTENDED_PRODUCTION_READY false**, and §27 forbids collapsing them. **THE TARGET IS PASSED ALONGSIDE THE OUTCOME, AND THAT IS A FINDING**: a refusal carries NO proposition key and NO Claim draft by the evaluator's own contract -- it declines to name a proposition it just declined to establish -- while migration 0035 requires the key AND its preimage. The caller supplies the target it already chose, because **the target is an INPUT, not something the evaluation concluded**; teaching the evaluator to carry it would have had the evaluator name a proposition it refused. **THE CLAIM STATEMENT IS COMPOSED FROM THE TARGET AND NOTHING ELSE, AND THAT IS WHERE THE MULTI-WITNESS ARCHITECTURE IS ACTUALLY DECIDED**: `_persist_one` appends a revision whenever the statement differs, so a statement naming the witness or the measurement would make **every additional Signal look like a reformulated Claim** -- revision churn saying the proposition changed when only the evidence grew. Proved on real rows: two witnesses at 110 and 105 give **one Claim, ONE revision, two Evidence, two derivations**, and a support plus a contradiction give **one Claim with opposite Evidence directions**. **IDEMPOTENT MEANS SAME IDENTITY AND SAME PAYLOAD**: a matching unique key with a different payload is a CONFLICT for the Claim, the derivation and the refusal alike -- and a unit mismatch and a time-bound mismatch share every refusal identity column and differ only on the reason code, which is exactly what a swallowed unique violation would have hidden. **`evaluator_version` IS EXCLUDED FROM THE DERIVATION COMPARISON DELIBERATELY**: the identity excludes it too, so rebuilding the software is not a new derivation, while reaching a DIFFERENT conclusion under the same rule version is a finding. **POLICY D SELECTED OPTION A**: persist the new derivation, leave Evidence untouched, return REVIEW_REQUIRED -- rolling the re-evaluation back would discard the very finding the reviewer is being asked about and leave a review request pointing at nothing. **DETECTION IS NOT RE-IMPLEMENTED**: Mission 1.41's `_persist_evidence` already refuses to overwrite a disagreeing relation, and the orchestrator turns that finding into a result rather than becoming a second authority for one question. Proved: rule v1 SUPPORTS then v2 CONTRADICTS gives REVIEW_REQUIRED, **one** Evidence row still reading SUPPORTS, **two** derivations. **THE CONFLICT IS RECONSTRUCTIBLE FROM DURABLE ROWS BY AN EXACT JOIN AND NO ROW DECLARES IT ONE**, which is precisely why unattended readiness is false. **EVERY ROLLBACK IS VERIFIED THROUGH A SEPARATE CONNECTION**, because a read inside the aborted transaction sees its own uncommitted work -- and the deferred evidence trigger is FORCED rather than assumed, which Mission 1.53 spent a build learning. **THE GUARD WAS NOT TOUCHED**: `validate_claims.py` is directory-scoped to `sros_nlp/interpreters`, so a sibling module may construct an INFERRED Claim and hosting the orchestrator one directory lower would have required weakening it. **TWO DEVIATIONS ARE STATED RATHER THAN BURIED**: the derivation lands AFTER Evidence because the canonical Claim API owns its internal ordering and §20 requires reusing it; and the aggregator was NOT re-run over the persisted rows, because the aggregation suite has no database and running it upstream would put it on the persistence suite's import path -- which §42 itself forbids -- while Mission 1.49 already drove the real aggregator over exactly these two shapes. **CONCURRENCY IS UNTESTED AND ITS BEHAVIOUR RECORDED**: the loser of a race hits the UNIQUE constraint and rolls back, so no duplicate can exist, but it surfaces as a driver error rather than as REUSED -- safe and not graceful. 0 requests of every kind, 0 model calls, 0 embeddings, every counter unchanged, **0 canonical INFERRED Claims and 0 production derivation, refusal or threshold rows**, no migration, evaluator untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **71 deliberate violations, 71 caught**, and **1354 bare-python tests run before commit** with 3308 pytest tests after |
| 1.88 | 2026-09-05 | **REFUSAL_PROVENANCE_SCHEMA_IMPLEMENTED: migration 0035 creates the one table ADR-038 froze, and the load-bearing proofs are DELETEs rather than sentences.** `research.proposition_evaluation_refusals`, additive only, no backfill, no data migration, **0 existing rows changed** and **0 production rows created**. **ALL THREE RETENTION PROPERTIES RUN AGAINST REAL ROWS.** A real interpretation run with a bounded expiry plus a real input row naming the same Signal, a refusal inserted independently, the run DELETED through the ordinary mechanism: inputs cascaded to **0**, the refusal **survived**. Deleting the cited Signal ALONE raises ForeignKeyViolation, and so does deleting a threshold registration a refusal judged. And a **real disposable workspace** holding a Signal, a threshold, an observed Claim and a refusal citing all three was deleted in one statement and **committed, with no deferred-constraint failure** -- both halves tested, because Mission 1.51 found that an undeferred NO ACTION fails during tenant cascade ordering and a design that traded one guarantee for the other would pass half a suite. **EVERY IDENTITY MEMBER IS NOT NULL, WHICH IS WHAT MAKES THE KEY REAL RATHER THAN NOMINAL** -- Mission 1.53 proved a UNIQUE containing a nullable column admits unlimited duplicates -- and **no COALESCE sentinel and no expression index were needed**, because the equivalence basis is NOT NULL on a MEASURED CONTRACT FACT: the decision constructor refuses a blank basis id for every verdict including UNKNOWN. **ONE STRICTER CHECK WAS CONSIDERED AND REJECTED ON A MEASUREMENT**: requiring every fact VALUE to be a string was enforceable and would have made the table unable to represent a refusal about the procurement family, whose `notice_ids` and `classification_codes` are arrays of strings -- **only 37 of 43 live Claims would have passed**, which also **corrects the Mission 1.53 design record's claim that values are flat strings on every live Claim**. Its first draft used lax jsonpath, which UNWRAPS arrays, so `["1"]` tested as a string and passed; `strict` was needed to see the case it was written for. **ONE CHECK IS DELIBERATELY STRICTER THAN `research.claims`**: the descriptor must carry the `proposition` discriminator, because a refusal's facts are the ONLY record of what was refused and there is no Claim row to recover the kind from -- measured first, 43 of 43. **THE SEVEN REASON CODES WERE READ FROM THE EVALUATOR'S OWN `_refuse` CALLS VIA THE AST AND COMPARED PAIR FOR PAIR AGAINST ADR-038 BEFORE THE MIGRATION WAS WRITTEN**, 0 invented and 0 renamed; the PAIRING check stops a row asserting a shape no gate produces, and the two vocabulary checks are kept beside it so a violation names the actual defect rather than leaving a reader comparing columns. **THE TABLE IS STRUCTURALLY INCAPABLE OF HOLDING A SYSTEM FAILURE**: no ERROR, FAILED, EXCEPTION or TIMEOUT, and no generic status column that could acquire one. **THE ENFORCEMENT BOUNDARY IS NAMED HONESTLY** -- the database stores key and preimage and does NOT reimplement the Python canonicalisation to check them against each other; what the test proves is that a JSONB round trip preserves the preimage well enough for the key to recompute, including from reversed input order. **TWO FALSE POSITIVES IN THE NEW VALIDATOR WERE REPAIRED STRUCTURALLY**: the identity check first matched the COMMENT quoting the other table's key, and the untouched-trigger check first matched the paragraph headed *WHAT IS NOT TOUCHED* -- `testing-strategy.md` §23 again, fixed by anchoring to the named constraint and scanning STATEMENTS rather than comments. **AND A DEFECT WRITTEN IN MISSION 1.53 SURFACED HERE**: that mission re-pointed a database test for pinning a migration HEAD, then wrote a head pin into its own validator AND its own suite; both went red the moment 0035 existed, and both are now the property they were protecting -- that 0034 is still present. Leak check **28 -> 29** tenant tables and `validate_schema` **46**, both picking the table up automatically; two pinned lists needed extending, which is what a new table costs. 0 requests of every kind, 0 model calls, 0 embeddings, every counter unchanged, 0 INFERRED Claims, 0 derivation rows, 0 threshold registrations, **0 production refusal rows**, evaluator untouched, `claim_derivations` untouched, trigger untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **70 deliberate violations, 70 caught**, and **1354 bare-python tests run before commit** with 3273 pytest tests after |
| 1.87 | 2026-09-05 | **INPUT_KEYED_REFUSAL_PROVENANCE_MODEL_SELECTED (ADR-038): a refusal is not a derivation of a Claim, and gets its own record.** Keyed on the input witness, the candidate target proposition, the derivation rule version and the reviewed equivalence basis. It names no ClaimRevision, creates no Claim, produces no Evidence, and needs **no change to `claim_derivations`, to the evidence-requirement trigger, or to any existing schema**. **OPTION B WAS MEASURED RATHER THAN DISMISSED, AND IT FAILS ON A FACT ONLY A LIVE PROBE PRODUCES**: a temp table mirroring `claim_derivations_identity_key` accepted **three identical rows** with a NULL `claim_revision_id` and refused the duplicate the moment the column was populated -- PostgreSQL treats NULLs as distinct, so **making that column nullable silently removes the table's only idempotency guarantee from exactly the rows the change exists to add**, and nothing reports it. Its second failure is quieter and worse: `claim_derivations` identifies its proposition **only through** `claim_revision_id`, so with that NULL the row cannot say what was refused -- repairing both means adding a key, a preimage, a reason code, a second partial unique index and three conditional CHECKs, which is **Option A inside a table whose name says otherwise**. So the choice is not one table against two; it is one honest table against one table meaning two things with two identity keys. **MIGRATION 0034 HAD ALREADY ANTICIPATED REFUSALS**: its threshold-required CHECK makes the registration optional *precisely* for NOT_APPLICABLE and UNKNOWN and its result CHECK admits all four -- **two constraints written in one migration that disagree**, which is the finding rather than a tie-breaker. **OPTION C WAS REFUTED FROM LIVE STATE**, not from a report: 12 of 12 interpretation runs carry an `expires_at` and the inputs FK is ON DELETE CASCADE, and retention was not redesigned to rescue it. **THE CANDIDATE TARGET IS A KEY PLUS ITS EXACT PREIMAGE, IN A VOCABULARY THAT ALREADY EXISTS**: all **43** live Claims carry both, the discriminator key is `proposition` on all 43, and the evaluator already emits it -- so a refusal and the Claim it may later become are **comparable by key**, which is what makes the UNKNOWN-then-SUPPORTS transition traceable at all. The key **recomputes** from the facts, so it is verifiable rather than trusted. A hash alone was refused because unlike a Claim there is no row elsewhere to recover the facts from; a candidate-proposition registry was refused as **Claims before Claims**; and the threshold registration was refused **on a measured fact** -- three of the seven live reason codes refuse at gate 1, before the registration is consulted. **THE SEVEN REASON CODES WERE READ FROM THE EVALUATOR'S OWN `_refuse` CALLS VIA THE AST**, because `__all__` entries look identical to a capitals scan, and **0 were invented or renamed**. **THE EQUIVALENCE BASIS IS NOT NULL ON A MEASURED CONTRACT FACT** -- the decision constructor refuses a blank basis id for EVERY verdict including UNKNOWN -- which needs no fake identifier and keeps the identity key **free of nullable columns**, the property probe C proved is not automatic. **AND THE BOUND IS STATED**: the evaluator only refuses pairs somebody already reviewed, so the store answers *what did we try and decline* and never *what did we never consider*. **A CHANGED BASIS IS A NEW HISTORICAL ROW**, decided explicitly with its cost stated, and **a later SUPPORTS leaves an earlier UNKNOWN entirely alone** -- no supersession column, because each row names its rule version and basis so *which reasoning stood when* is answerable without one. **ONE DEVIATION FROM THE BRIEF IS FLAGGED RATHER THAN BURIED**: the descriptor carries no schema version, because `derivation_rule_version` already pins which fact set was emitted and a second version field would be a second authority for one fact -- recorded as `OPERATOR_REVIEWABLE_DEVIATION` with its cost if wrong. **TWO TESTING TRAPS WERE CAUGHT BEFORE THEY MATTERED.** The evidence-requirement trigger is DEFERRABLE, so a rollback fixture never fires it and the first version of that test **reported a pass for a rule that never ran**; `SET CONSTRAINTS ALL IMMEDIATE` is what makes it a test, and it matters more for the HYPOTHESIS control, which would otherwise pass vacuously. And the new pytest classes were first named without a `Test` prefix, which **collected zero tests silently** -- renaming took collection from 0 to 15. **A PROBE THAT REFUSED FOR THE WRONG REASON WAS REPORTED RATHER THAN KEPT**: the first INFERRED-claim attempt used an `origin` value the CHECK does not admit, so it was refused by the wrong constraint while looking exactly like the result I wanted, and a HYPOTHESIS control was added so the refusal is attributable. 0 requests of every kind, 0 model calls, 0 embeddings, every counter unchanged, 0 INFERRED Claims, 0 derivation rows, 0 threshold registrations, **0 migrations and no table**, `validate_claims.py` untouched, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **66 deliberate violations, 66 caught**, and **1354 bare-python tests run before commit** with 3201 pytest tests after |
| 1.86 | 2026-09-05 | **REFUSAL_DERIVATION_BINDING_CONTRACT_GAP, with DETERMINISTIC_EVALUATOR_FOUNDATION_IMPLEMENTED beside it: the evaluator refuses correctly and cannot write the refusal down.** **THE CONFLICT WAS PROVEN IN A DISPOSABLE PROBE WORKSPACE RATHER THAN REASONED ABOUT**: an INFERRED claim with no Evidence is REFUSED (23514) by `research.require_evidence_for_generated_claim`, whose exemptions are read out of the live function definition as **HYPOTHESIS, MANUAL and WITHDRAWN and nothing else**; and a derivation with a NULL `claim_revision_id` is REFUSED by migration 0034. **Both refusals are individually correct and jointly they leave a NOT_APPLICABLE or UNKNOWN evaluation nowhere to store its provenance** without first fabricating the Claim the evaluation just declined to establish. **NOTHING WAS WIDENED TO GET PAST IT**: INFERRED was NOT added to the exemption list, `claim_revision_id` was NOT made nullable, no Claim was created to host a refusal, and no third table was invented -- each is a schema decision with an ADR behind it. **THE OTHER CONTRACT QUESTION RESOLVES BY POLICY, AND THAT DIFFERENCE DECIDES WHICH IS THE HEADLINE**: `scoring.evidence` has **no** revision, supersession or `is_current` column (measured, not recalled), so a rule-version change produces ANOTHER derivation record and may never automatically alter canonical Evidence, with a disagreement REPORTED for operator review -- **policy D, needing no schema change**, while the refusal gap needs a decision nobody has taken. Reporting §22 as the outcome would misattribute the blocker to a layer that is not blocking. **THE PACKAGE SITS WHERE ADR-037 Q3 NAMED IT AND THE GUARD WAS LEFT ALONE**: `validate_claims.py` is byte-identical, no interpreter imports the evaluator, and the validator reads Q3 out of the Mission 1.50 contract and COMPARES it rather than trusting the record. **ONE NAMED PACKAGE JOINED SHARED_PATHS, NOT THE MONOREPO** -- Mission 1.47's CI failure made that rule load-bearing, and widening the runner to make an import work would delete the property it exists to check. **FOUR GATES IN ORDER, EQUIVALENCE FIRST**, so the direction the arithmetic WOULD have produced cannot leak into a refusal -- tested with a mismatch that would have SUPPORTED, which proves the gate runs rather than relabels. **NO UNIT CONVERTED, NO TIME WINDOW ALIGNED, NO THRESHOLD SELECTED**: `evaluate` takes exactly one registration and never searches, so *whichever bound makes the Claim work* is not expressible. **A PREREGISTERED REGISTRATION RECORDED AFTER RETRIEVAL IS REFUSED RATHER THAN DOWNGRADED**, because a silent downgrade to POST_HOC would quietly repair somebody's claim about when they decided. **PROVENANCE CHANGES ELIGIBILITY AND NEVER ENTAILMENT**, and UNKNOWN is ineligible rather than assumed. **DECIMAL THROUGHOUT**: a float measurement is refused at construction, and `Decimal("100")` and `Decimal("100.0")` are ONE bound, because otherwise the same threshold written two ways forks the proposition -- Mission 1.48's defect one field along. **INDEPENDENCE AND RELIABILITY ARE NEITHER INPUTS NOR OUTPUTS**, and `interpretation_confidence` comes from the reviewed equivalence decision rather than from the arithmetic. **THE AGGREGATOR NEEDS NOTHING, PROVED FROM ITS SIGNATURE**: `aggregate()` takes no claim type and `EvidenceItem` carries none, so there is no parameter through which INFERRED Evidence could be treated differently. **A CORRECTION WAS MADE RATHER THAN ASSUMED AWAY**: `EvidenceDirection` DOES have a NEUTRAL member, so the guarantee that a refusal never becomes NEUTRAL is **producer-side, not type-side** -- a NEUTRAL row would be counted and weightless, invisible in the numbers and visible in the counts, which is the exact shape ADR-037 refuses. **TWO TESTS WERE REPAIRED RATHER THAN REMOVED**: Mission 1.50's `test_the_package_was_not_created` was re-pointed, because a test asserting 0 forever is a test asserting the contract is never implemented; and one of my own compared `id()` of two interned `"1.0.0"` constants and asserted that a string is not itself -- **it failed on the first bare-python run, which is what that gate is for**. 0 requests of every kind, 0 model calls, 0 embeddings, every counter unchanged, 0 INFERRED Claims, 0 derivation rows, 0 threshold registrations, 0 migrations, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **55 deliberate violations, 55 caught**, and **1313 bare-python tests run before commit** with 3186 pytest tests after |
| 1.85 | 2026-09-04 | **DETERMINISTIC_DERIVATION_PROVENANCE_SCHEMA_IMPLEMENTED: migration 0034 creates the two additive records ADR-037 froze, and the load-bearing proof is a DELETE rather than a sentence.** `research.threshold_registrations` and `research.claim_derivations`, additive only, no backfill, no data migration, **0 existing rows changed** and **0 production rows created**. **THE RETENTION PROOF RUNS AGAINST REAL ROWS**: a real interpretation run with a bounded expiry plus a real input row naming the same Signal, a durable derivation inserted independently, the run DELETED through the ordinary mechanism -- inputs cascaded to **0**, the derivation **survived**. ADR-037's entire schema verdict rests on that distinction, and it is now checked rather than asserted. The other direction is checked too: deleting a Signal cited by a derivation raises ForeignKeyViolation, so retention cannot silently take the reasoning with it. **THE DEFERRABLE FINDING WAS FOUND BY THE DATABASE, NOT BY REASONING.** The FKs were first plain `ON DELETE NO ACTION`, on the argument that NO ACTION is checked at end of statement while RESTRICT is immediate, so a workspace cascade would survive. Wrong: an UNDEFERRED NO ACTION is checked at the end of each **cascading** statement, and the cascade removing `claim_revisions` runs before the one removing the derivations citing them -- every committing test's teardown failed. `DEFERRABLE INITIALLY DEFERRED` moves the check to COMMIT, where a workspace deletion has removed both sides and a lone Signal purge has not. **Both guarantees hold and neither was traded for the other.** **THE STALE ROW IT LEFT WAS INSPECTED BEFORE ANYTHING WAS DELETED**: one committing test had written a derivation before its teardown failed, and the row was confined to a disposable `signal-probe` workspace with the canonical dev workspace untouched at 33 Signals, 43 Claims and 44 revisions. Removed through the mechanism the failed teardown would have used, then the migration was rolled back and re-applied so the deployment matches the file exactly. **THE TWO IDEMPOTENCY KEYS DIFFER, AND A TEST READS BOTH FROM THE LIVE SCHEMA TO PIN IT**: the derivation key CONTAINS `derivation_rule_version` and no Evidence key contains `extraction_method`, because Mission 1.41 removed it so a version bump could not INSERT a duplicate while replaying a different rule IS different reasoning about the same relation. **APPEND-ONLY, NO SUPERSESSION COLUMN AND NO `is_current` FLAG**: rule v2 over the same (revision, signal) creates a SECOND row and leaves the first intact, because two rule versions disagreeing is a finding worth seeing rather than a conflict to resolve by overwriting -- and it satisfies all four section 16 requirements with no machinery. **Bound to the CLAIM REVISION**, so a later derivation cannot rewrite the reasoning behind an earlier one. **No `evidence_id`**: Evidence is already identified by (workspace, claim, signal), and a pointer would suggest a single authoritative derivation exists when append-only deliberately permits several. **THRESHOLD PROVENANCE IS NOT CLAIM IDENTITY AND THE KEY PROVES IT**: the idempotency key INCLUDES `provenance_status`, so one logical bound may be registered once as PREREGISTERED and once as EXTERNAL_NORM without being merged, and the table declares no `proposition_key`, no `claim_id` and **no `calibration_eligible`** -- eligibility is DERIVED from status, because two authorities for one fact eventually disagree. **NEUTRAL is not an evaluation result**, deliberately. **`origin_detail`, `claims`, `evidence` and both interpretation tables are untouched**, and the single ALTER is a SEMANTICALLY VACUOUS `UNIQUE (workspace_id, id)` on `claim_revisions` that a composite tenant-safe FK requires and that both other referenced tables already carry. **SEMANTIC-EQUIVALENCE BASIS IS AN OPAQUE DURABLE IDENTIFIER AND NOT A THIRD TABLE**: section 13 asked only for a stable auditable basis, the canonical subject registry already establishes the pattern, and a table would be the broad equivalence subsystem the mission was told not to build. **NO REPOSITORY LAYER AND NO DOMAIN TYPES**: the constraints are SQL and the tests exercise them directly, so a Python mirror written before the evaluator exists would be a second authority with no consumer. The pytest leak check now reports the database unchanged across **28** tenant tables, up from 26, having picked both up automatically. 0 requests, 0 model calls, 0 embeddings, 0 INFERRED Claims, 0 Evidence, profile still UNCALIBRATED, Problem-Family still PARKED, validator probed with **25 deliberate violations, 25 caught**, and 1244 bare-python tests run before commit |
| 1.84 | 2026-09-04 | **DETERMINISTIC_INFERRED_CLAIM_CONTRACT_READY (ADR-037): the Claim and the Evidence need nothing new, and the REASONING has nowhere durable to live.** All four mandatory questions resolved; **`BOTH_REQUIRED`** on schema, fully specified, and **no migration created**. **THE SCHEMA VERDICT RESTS ON A MEASURED FACT RATHER THAN A PREFERENCE.** `research.claim_interpretation_inputs` is the closest existing structure -- one row per (run, signal) carrying role, claim_id, reason_code and detail, 64 rows live -- and it cannot hold derivation provenance because **ALL 12 rows of its parent `claim_interpretation_runs` carry a populated `expires_at` about ninety days out, and the inputs foreign key is ON DELETE CASCADE**. When a run expires every input row goes with it, so **a Claim would outlive the record of how it was derived**. A retention-bounded execution log is the right shape for *what did this run consider and refuse* and the wrong shape for *why is this Claim true*. `proposition_facts` was also rejected: it is the preimage of the KEY, so derivation facts placed there would become identity. **`origin_detail` KEEPS ONE RESPONSIBILITY.** It answers *where did this Claim come from* on all 43 live Claims, with sentences like *"Restated from signal `<id>`"*; a reasoning step answers *why does this measurement satisfy this proposition*. Putting both there is the Mission 1.15.4 shape -- one free-text field, two independent questions -- so for an INFERRED Claim it keeps naming the evaluator, exactly as it names the interpreter today. **EVIDENCE ATTACHES DIRECTLY, on existing architectural intent rather than on a fresh judgement**: `claim-epistemic-semantics-v1.md` §4 already says an INFERRED claim carries *"the Signals it reasoned from, as Evidence"*. No Claim-to-Claim relation: the aggregator consumes Evidence and not relations, so a relation would need proxy Evidence anyway. **BUT ATTACHMENT AND PROVENANCE ARE BOTH REQUIRED AND NEITHER SUBSTITUTES**: Evidence says WHICH observation bears and in which direction; the derivation record says HOW that direction was determined, under which rule, against which threshold, on what equivalence basis. **GRANULARITY IS ONE RULE AND MANY EVALUATIONS, BOUND TO THE CLAIM REVISION**: one prose rationale cannot explain both why A supports and why C contradicts, and binding to the Claim would let a later derivation silently rewrite the reasoning behind an earlier revision. **THE TWO IDEMPOTENCY KEYS DIFFER DELIBERATELY**: Evidence keys on `(workspace, claim, signal)` because Mission 1.41 removed `extraction_method` so a version bump cannot INSERT a duplicate; a derivation record keys on `(workspace, claim_revision, signal, rule_version)` and MUST be distinct per rule version, because replaying a different rule is different reasoning about the same relation. **THRESHOLD PROVENANCE IS NOT PROPOSITION IDENTITY**: `M >= 100` preregistered and `M >= 100` post-hoc are ONE proposition with one falsifier; what differs is calibration eligibility, and making provenance identity would fork one proposition into several. **AND PROVENANCE NEVER CHANGES ENTAILMENT** -- a post-hoc bound with a measurement of 110 genuinely supports the Claim; what hindsight costs is eligibility, not truth. **PREREGISTERED IS DEFINED AGAINST RETRIEVAL, NOT PUBLICATION**: `recorded_at < observation.retrieved_at`, because the bias guarded against is the ANALYST'S and an analyst can only be influenced by data that reached them -- a figure public for years before this system retrieved it was not known to the person who froze the bound. Not commit time either. **AND THE LIMIT IS STATED RATHER THAN HIDDEN**: the relation is necessary and machine-checkable and NOT sufficient to exclude human foreknowledge, so PREREGISTERED means *this system did not hold the measurement*, never *nobody knew*. **`interpretation_confidence` IS NOT A GAP, AND THE ANSWER IS C RATHER THAN THE OBVIOUS A.** Its column comment says *"Confidence that THIS WORDING faithfully states what the cited Signals showed"*, and `build_claim` refuses an automated claim without it. For an OBSERVED restatement reading the facts IS the whole job, which is why the interpreters set 1.0. A deterministic INFERRED threshold Claim has ONE step the OBSERVED case lacks -- asserting that the source-native measurement measures the Claim's quantity under its definition and unit -- so the field means **confidence in the SEMANTIC-EQUIVALENCE MAPPING, not in the arithmetic**, and setting 1.0 automatically would assert certainty about a real judgement. `INTERPRETATION_CONFIDENCE_SEMANTIC_GAP` deliberately NOT reported. **NO `derivation_confidence` FIELD, AND THERE MUST NOT BE ONE**: `110 >= 100` is exact, and a confidence on it would be a number nobody fitted invented because a numeric column exists elsewhere. **`NOT_APPLICABLE` AND `UNKNOWN` PRODUCE A DERIVATION RECORD AND NO EVIDENCE ROW**, so a refusal is auditable rather than invisible, and UNKNOWN never becomes NEUTRAL -- NEUTRAL asserts an observation bears without bearing either way, which is a positive finding. **THE EVALUATOR GOES IN A NEW PACKAGE THAT WAS NOT CREATED**: hosting it in the interpreters would require weakening `validate_claims.py`, and a guard removed to let new work through is a guard that never was. Allowed dependencies contracts + claim-model + signal-model, all already in the bare-python runner; forbidden `sros_acquisition` (could decide its own authorization) and the Gateway (cannot call a model it cannot import). §38 forbids creating production code merely to host tests, so the contract tests live in claim-model and evidence-aggregation. **PURELY ADDITIVE**: 43 Claims, 44 revisions, 57 Evidence untouched, `SourceBoundary`, `proposition_key` and the reliability scope unmodified, every INFERRED row will initially resolve NO_APPLICABLE_ASSESSMENT and that is correct. Fixtures through the real aggregator: 2 groups at 0.8 vs 0.6; contradiction 0.5 with masses summing to 1.0; republication one group at 0.6. 0 requests, 0 model calls, 0 embeddings, 17 counters unchanged, 0 INFERRED Claims, 0 migrations, Problem-Family PARKED, validator probed with **24 deliberate violations, 24 caught**, and 1244 bare-python tests run before commit |
| 1.83 | 2026-09-04 | **SOURCE_INDEPENDENT_PROPOSITIONS_BELONG_TO_INFERRED_LAYER (ADR-036): the layer already existed, it was defined for exactly this, and nobody had built it.** **THE REPOSITORY HAD ALREADY WRITTEN THE ANSWER**: `claim-epistemic-semantics-v1.md` §4 defines INFERRED as a claim that *"asserts something about the world that the measurement is evidence for, and that the source did not itself report"* -- the source-independent proposition, verbatim, written in Mission 1.13 several missions before anything needed it. **NO NEW ClaimType, NO SUBTYPE, NO MIGRATION.** **THE ASSUMPTION THE BRIEF WARNED AGAINST IS FALSE AND THE TAXONOMY REFUTES IT TWICE**: by TYPE, since INFERRED is *derived analytically from one or more observations* while **PREDICTED** is *a model-generated estimate*, so the model-associated type is PREDICTED; and by AXIS, since `claim_type` is the epistemic category while `interpretation_kind` is the procedure, and **migration 0016's CHECK constraint ties `interpretation_kind` to the presence of a `model_version` and NOT to `claim_type`** -- orthogonal in SQL rather than in prose. The semantics document states the consequence outright: *"A deterministic extractor can produce an INFERRED-type claim, and an LLM can produce an OBSERVED-type one."* So **`INFERRED` + `DETERMINISTIC` is representable TODAY with no migration**, and has simply never been written: 43 Claims all OBSERVED, all DETERMINISTIC, 0 carrying a model_version. **MODEL B WAS REFUTED BY THE PROJECT'S OWN SENTENCE**: *"An OBSERVED claim that should have been INFERRED is a fabrication with a citation attached."* A cross-source OBSERVED convergence Claim asserts what no single source observed while carrying every source's citation, which is worse than an honest inference rather than milder, because the citations make it look directly supported. **MODEL C IS UNNECESSARY RATHER THAN WRONG**: the deterministic-versus-model distinction is exactly what `interpretation_kind` carries, and a sixth ClaimType would put one distinction in two places -- the defect Mission 1.13 fixed by dropping `evidence.claim_type` and Mission 1.42a avoided by refusing a second confidence field. **MODEL D WAS TAKEN SERIOUSLY AND REJECTED FOR THE RIGHT REASON**: it is NOT the conservative option, because the layer is already defined in the ontology, the generated contract and the semantics document, so choosing absence leaves a defined capability permanently unbuilt -- and its cost must be stated rather than hidden: the system stays unable to say two sources disagree, which is the one signal telling an operator to go and look. **THREE EXCLUSIONS CARRY THE IDENTITY, AND EACH DOES REAL WORK.** The **measurement value is not identity** -- if it were, 110 from A and 105 from B would be two Claims, Mission 1.48's failure reproduced one layer up. **`source_id` is not identity here** and IS identity for OBSERVED, which is the whole two-layer distinction. **Direction is not identity**, the precise inversion of the OBSERVED layer where Mission 1.48 found it IS -- and that inversion is why the same measurement stream that cannot contradict at Layer 1 can at Layer 2. **SOURCE INDEPENDENCE OF THE PROPOSITION IS NEVER PROVENANCE LOSS**: every witness keeps `source_id` and the full chain to RawRecord. **RELIABILITY IS UNAFFECTED AND THE REASON RESOLVES THE APPARENT CONFLICT**: Claim IDENTITY and Evidence reliability SCOPE are different things, so a source-independent proposition can carry source-scoped reliability without contradiction -- and a new proposition_kind plus `claim_type = INFERRED` is a NEW scope, so **nothing is inherited by proposition similarity**. **MEASUREMENT RELIABILITY AND DERIVATION VALIDITY MUST NEVER BE MULTIPLIED**: whether 110 is dependable is a human judgement, whether 110 entails `>= 100` is exact, and no coefficient combines them. **THE THRESHOLD MUST BE PREREGISTERED TO BE CALIBRATION-ELIGIBLE**: PREREGISTERED, SOURCE_NATIVE and EXTERNAL_NORM qualify; POST_HOC and UNKNOWN do not, and UNKNOWN is ineligible rather than assumed, because uncertainty is never permission. **THE FIXTURES RAN THROUGH THE REAL AGGREGATOR**: two independent supports give **2 groups and strength 0.8 against a strongest member of 0.6**, the first shape that would differ from B-2; a support and a contradiction on ONE Claim give contradiction 0.5 and masses 0.3/0.2/0.3/0.2 summing to 1.0; and a republication stays **one group at 0.6**, so volume rises and strength does not. **`validate_claims.py` WAS LEFT UNTOUCHED** and the evaluator belongs OUTSIDE the interpreter package for that reason -- a guard removed to let new work through is a guard that never was. **PURELY ADDITIVE**: 43 Claims, 44 revisions and 57 Evidence keep their identities and meaning and become the INPUTS, 0 proposition identities rewritten, 0 migrations recommended. `SourceBoundary` not widened, `proposition_key` not altered, no ClaimType member added, no INFERRED Claim created. 0 requests of every kind, 0 model calls, 0 embeddings, all 16 counters unchanged, profile still UNCALIBRATED, Problem-Family still PARKED, and the validator probed with **22 deliberate violations, 22 caught** |
| 1.82 | 2026-09-04 | **CONTRADICTION_CLAIM_IDENTITY_ARCHITECTURE_GAP: the contradiction machinery is fully functional and structurally unreachable, and the fact that blocks it is the fact that blocked Mission 1.47.** **THE MACHINERY WORKS AND WAS PROVED WORKING**: one SUPPORTS and one CONTRADICTS on one claim id through the REAL aggregator gives support 0.6, contradiction 0.5, masses 0.3/0.2/0.3/0.2 summing to 1.0. **So the gap is not the arithmetic.** **NOTHING WAS QUOTED FROM A MISSION REPORT**: §0 re-derived the B-2 identity by running the real `aggregate()` over ALL 43 live Claims with reliability resolved through the real resolver, against a B-2 computed independently, and got `aggregator_differs_from_b2_cases = 0` with `max_support_groups_on_one_claim = 1`. **CONTRADICTION IS BLOCKED THREE TIMES AND THE THIRD IS THE DEEP ONE.** `direction` is written into `proposition_facts` by all three implemented templates, so an INCREASING and a DECREASING observation are TWO Claims. `EvidenceDirection.SUPPORTS` appears **EXACTLY ONCE** in the whole interpreters package as a hard-coded literal and `CONTRADICTS` appears nowhere, so no implemented interpreter could emit the contradicting row even if identity permitted it; all 57 live Evidence rows are SUPPORTS. And **all 43 Claims carry `source_id` in proposition identity**, so two publishers reporting incompatible values form two Claims before their values are ever compared. **THAT THIRD BLOCKER IS THE UNIFICATION**: corroboration needs two observations on ONE Claim and contradiction needs two observations on ONE Claim, so **source attribution in proposition identity closes BOTH roads out of the B-2 baseline with one decision** -- and Mission 1.47's architecture finding and this one are the same finding seen from two sides. **THE BINDING CONSTRAINT IS THEREFORE NOT A MISSING APPARATUS**: a new apparatus interprets to facts carrying its own `source_id`, produces its own `proposition_key` and lands on its own Claim, where it can neither join a support group nor contradict anything. **Acquiring one would add rows and change nothing**, so `BOTH_ROUTES_REQUIRE_NEW_MEASUREMENT_APPARATUS` was deliberately NOT the outcome. **THE LIVE CORPUS SUPPLIED ITS OWN DEMONSTRATION**: three Claim pairs differ ONLY in `direction` -- the Wikimedia witnessed existentials for Docker, Kubernetes and Podman -- and the most contradiction-looking pair in the repository is not one for **three independent reasons**: they are two Claims, they are both TRUE at once, and a counterexample cannot falsify a monotone existential anyway. **THE TRADE-OFF IS NOW AN OBSERVED FACT RATHER THAN A HYPOTHESIS**: the families easiest to make cross-apparatus are monotone and unfalsifiable, and the falsifiable families are the ones only one apparatus supports. Seven families evaluated on eight qualitative criteria with **no weighted numeric score**. **`THRESHOLD_STATE` selected**, and selected for a reason that serves BOTH routes: an EXACT_POINT_VALUE claim is contradicted by a rounding difference, which manufactures false contradictions and makes independent corroboration nearly impossible, while a threshold lets two honestly-disagreeing apparatuses both SUPPORT it and still admits a real falsifier. **Its cost is recorded rather than discounted**: X is OURS, so it must be frozen BEFORE the second measurement is retrieved or it becomes an arbitrary number wearing the costume of a rule. **`RELIABILITY_REVIEWABILITY` IS PROMOTED TO A FIRST-CLASS SEARCH CRITERION**, because Mission 1.47 paid for learning it late: one robots-blocked methodology page left independence UNKNOWN **and** was the reason the operator declined both Stack Exchange reliability scopes, so a single inaccessible document disqualified a strong apparatus on two separate gates. **NO SOURCE WAS SELECTED**: the two registered candidates whose SHAPE fits best are exactly the two Mission 1.46 already refuted on provenance, and the third observes a different jurisdiction. **A §23 TRAP WAS MET AND FIXED STRUCTURALLY**: the first draft of the no-named-source guard was a substring scan and it refused this mission's own record on the word *documented*, because `ted` is inside it -- repaired with token boundaries, the same fix Mission 1.13.1 made for `supermarket` and `market`. **§33 WAS HONOURED**: the zero-dependency runner was run with bare `python` BEFORE commit, 1124 tests across 8 packages, and the claim-identity proof lives in `claim-model` because that package owns `proposition_key`. 0 requests of every kind, 0 model calls, 0 embeddings, all 16 counters unchanged, profile still UNCALIBRATED, Problem-Family still PARKED, workspaces clean with 0 orchestration probes |
| 1.81 | 2026-09-04 | **FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK: the only proposition two different apparatuses BOTH entail is the one that throws away what each of them measures.** Docker is the ONLY cross-apparatus shared subject in the held corpus, and that was **MEASURED BEFORE ANY PAIR WAS CHOSEN** rather than assumed -- Wikimedia 12 Evidence / Stack Exchange 2, against kubernetes 12/0 and podman 12/0, with the reviewed registry having already recorded why the other two fail. **AN APPARATUS IS `(source, proposition_kind)` AND NOT A SOURCE**: four sources operate **NINE** apparatuses, two of them running two each over one corpus, so counting sources would have merged two reliability scopes the contract already holds apart. **THE ONE CANDIDATE THAT PASSES SEMANTICS IS AN EXISTENTIAL AND IT PASSES BY BEING WEAK**: *at least one public platform recorded an event of a defined class attributed to `docker` during March 2024*, where the ONLY definition admitting both members is a **DISJUNCTION** of the two publishers' own mechanisms -- so §8's conjunction is satisfied (A alone YES, B alone YES, jointly NO, latent NO) and the class is explicit and circular at once. **SOURCE ATTRIBUTION WAS NOT REMOVED, IT WAS RELOCATED**, which is the finding worth reading twice: the proposition's SUBJECT is genuinely source-independent while its PREDICATE enumerates both publishers, so attribution moves from the subject of the sentence into the definition of its predicate where it is harder to see -- **a proposition that looks source-independent and is not is worse than one that is openly attributed**. **STRENGTHEN IT ONCE AND IT DIES**: the first informative strengthening needs 88 questions compared against N content requests, which §11 forbids as a pseudo-metric, and needs exactly-aligned periods the grains do not provide. **THE TIME WINDOWS OVERLAP AND ARE NOT ALIGNED**: Stack Exchange runs `2024-03-01T08:06:03Z .. 2024-03-05T04:17:20Z` against whole UTC day buckets, so no aligned bounded period exists for ANY quantitative comparison; both sit inside March 2024 and **containment is weaker than alignment**, which is §5's warning arriving in the time column. **NO MONTHLY AGGREGATE WAS MANUFACTURED** -- not needed, since an existential needs no sum, AND not available, since 7 of 31 March days are held and §10 requires completeness; **both reported, because reporting only the first would leave a reader believing the aggregate was available and merely unused**. **FIVE GATES PASS AND THREE FAIL.** Independence is **UNKNOWN and NOT REFUTED**, which is materially different from Mission 1.46: there a documented common upstream CLOSED the direction, here what is missing is affirmative documentation of one side -- **an unknown can be resolved by a retrievable document, a documented common producer cannot**. **TWO INDEPENDENT GATES FAIL ON ONE ROOT CAUSE**: Stack Exchange's own methodology is unreachable because the site's robots policy blocks the crawler, which leaves its measurement lineage undocumented AND is the same insufficiency for which **the operator already answered NO to both Stack Exchange reliability scopes in Mission 1.36.1** -- so the route needs a judgement already declined for a reason no mission may clear. **0 requests of any kind were made, and none was attempted against the blocked documentation.** **THE CONVERGENCE CONTRACT STRUCTURALLY CANNOT EXPRESS IT**, proved through the REAL constructor: `source_id` is mandatory in `identity_fields` and `SourceBoundary` has exactly one member, with its own docstring saying the absence is deliberate. **THE IDENTITY/WITNESS EXERCISE FAILS ON `audience_class`**, required on the content-request kind precisely so one item over one period cannot carry two counts under one name, and absent on the other side. **COMPLEMENTARITY WAS RECORDED BY THE CODEBASE BEFORE THIS MISSION ASKED**: the Opportunity engine's own mapping rationale says PROBLEM_OR_NEED and AUDIENCE_OR_USAGE are different questions and *"neither implies the other"*. **`STRUCTURALLY_IDENTIFYING` YES, `SEMANTICALLY_USEFUL` NO**, reported apart. **NO ROUTE SELECTED**, §26 forbidding a least-bad fallback, and the three downstream blockers were deliberately NOT reported as the outcome because fixing either would unlock nothing. **THE STRUCTURAL OBSERVATION**: existentials converge easily and are MONOTONE, so they can never contradict; the propositions that CAN be contradicted are the ones only one apparatus supports -- **so one property of this corpus blocks BOTH roads out of the B-2 identity at once**. 0 model calls, 0 embeddings, 0 canonical mutations across 15 counters, 0 independence groups, 0 scores, profile still UNCALIBRATED, Problem-Family still PARKED, and the workspace leak check clean on an uninterrupted run with 0 orchestration probes |
| 1.80 | 2026-09-04 | **COMMON_UPSTREAM_SOURCE_PREVENTS_INDEPENDENCE: the international publishers are distribution layers over one national producer, so a second publisher is not a second provenance group.** Both candidate routes fail and **each fails on more than one gate**. **FRED REPUBLISHES THE EXACT SERIES ALREADY HELD**, by its own declaration: Source *World Bank*, Release *World Development Indicators*, **Source Code `SP.POP.TOTL`**, and a suggested citation reading *World Bank ... retrieved from FRED*. It is not a similar measurement, it is THE measurement, carrying the World Bank source note word for word -- so the pair that matches semantically matches **because it is one series**, which is the trap §13 names. **EUROSTAT FAILS BOTH GATES INDEPENDENTLY.** The World Bank's own indicator metadata lists **'Eurostat: Demographic Statistics'** among four `sourceOrganization` entries for SP.POP.TOTL, so for EU member states Eurostat is **UPSTREAM OF** the World Bank rather than beside it; and Eurostat's ESMS metadata states population data are **collected by Eurostat from National Statistical Institutes** under **Regulation (EU) No 1260/2013**, so Eurostat compiles what Destatis and INSEE transmit rather than enumerating anyone. **AND THE MEASUREMENTS ARE NOT THE SAME ANYWAY**: World Bank counts the **de facto** population at **midyear**, Eurostat the **usually resident** population on **1 January** -- a shared year label is not a shared reference date, §16 exactly. **NEITHER WAS REJECTED ON AN UNKNOWN**, which is the distinction that closes the direction: both were rejected on provenance the publishers THEMSELVES DOCUMENT, and an unknown could have been resolved by more reading. **THE STRUCTURAL FINDING**: the measurement of how many people live in Germany happens ONCE, at Destatis, and Eurostat, the World Bank and FRED are three routes to it -- so *add another statistical publisher* cannot ever yield a second group for a national aggregate, and independence over this family would need two genuinely different measurement APPARATUSES. **NO ROUTE WAS SELECTED AND NO SLOT WAS FILLED**: §25 forbids a least-bad fallback, and §14's qualified alternative is **NONE inside the eligible portfolio**, because the eligible `economic_data` family is exactly the three publishers just shown to share producers -- naming a fourth would mean reaching outside the eligible set or inventing one. **GOVERNANCE WAS NOT THE BLOCKER AND THE ENGINEERING GAP WAS NOT THE FINDING**: all three sources are eligible today with **0 unsatisfied conditions**, and Eurostat and FRED really do lack a resource, a collector and a normalizer -- but the routes died upstream of that, and reporting the second obstacle would have hidden the first. **THE MODEL IS READY AND IS NOT THE GAP**: `_group_key` puts a `KNOWN_INDEPENDENT` item in its OWN group, so two such rows form two groups and enter saturation as `1-(1-g_A)(1-g_B)` -- proven on non-empty fixtures for **all three** independence states so every branch executes, without rediscovering Mission 1.43's arithmetic. **What is missing is a real pair entitled to the shape.** **§10 WAS ANSWERED AND OUTCOME B WAS REFUSED**: the held Claims carry `source_id` as proposition identity, so two publishers cannot support one source-attributed OBSERVED proposition -- but `INDEPENDENT_ROUTE_REQUIRES_INFERRED_STATISTICAL_CLAIM` is deliberately NOT reported, because the blocker sits upstream of the Claim architecture and reporting B would misattribute the failure to a layer that never got to fail. Source attribution was not proposed for deletion. **THE PRECONDITION WAS COMPLETED FIRST**: the operator's TED local v3 acceptance recorded through `record_verifications` with `verifier_version` **`ted-v3-official-reuse-acknowledgement-v1`** -- NOT `acknowledgement-v1`, which names the materially different v2 text -- stored byte-for-byte and asserted against the supplied string, **17/17 post-write checks**, TED eligible again locally at v3 and commercial still REQUIRES_REVIEW. 0 research-data requests, 1 METADATA_ONLY call persisting no RawRecord, 5 documentation requests, 0 model calls, 0 embeddings, 0 independence groups, every research counter unchanged, profile still UNCALIBRATED, Problem-Family still PARKED |
| 1.79 | 2026-09-04 | **TED_OFFICIAL_REUSE_GUIDANCE_RECONCILED: the Publications Office answered, and the answer is bounded exactly where it stops.** A written reply of 2026-09-04 from the **Head of Sector -- Copyright and legal issues**, case **2026-COP-201**, answering a request that described this system BY NAME as *a commercial software-as-a-service application* and enumerated automated retrieval, repeated collection through bulk downloads OR the Search API, minimised storage, commercial analytical use, automated processing and derived aggregate signals. **TED notices and metadata may be reused for both commercial and non-commercial purposes, provided the source is acknowledged and according to the copyright notice; whether or not the EU asserts copyright over the database should not prevent reuse; and the way the data are retrieved is not relevant in this regard.** **H-36A IS SPLIT RATHER THAN ANSWERED, AND THE SPLIT IS THE FINDING**: database-right **EXISTENCE** stays `NOT_ESTABLISHED` -- the reply says **copyright** over the database while Directive 96/9/EC creates TWO rights, copyright in the arrangement (Art. 3) and the **sui generis** right of the maker (Art. 7), and *whether or not* is a refusal to say -- while whether such a right **BLOCKS REUSE** becomes `OFFICIAL_FIRST_PARTY_GUIDANCE_INDICATES_NOT_A_BLOCKER`. **The abstract legal ontology is unresolved and does not have to be resolved, because the body that would assert the right says it should not stand in the way.** `NOT_ESTABLISHED` was NOT changed to `NO_RIGHT_EXISTS`. **H-36B becomes `RETRIEVAL_METHOD_NEUTRALITY_FOR_REUSE`**, bounded twice: not a database-right grant, and not *any acquisition method is allowed* -- reuse rights and technical access are different questions, and no circumvention, rate-limit evasion or undocumented endpoint is authorised. **THE BULK ROUTE STAYS BLOCKED AND ITS BLOCKER CHANGED IDENTITY**: it was blocked for database-right exposure, which the reply weakens, and it stays blocked because bulk XML offers **no field selection**, so minimisation cannot happen AT acquisition -- re-grounded rather than relaxed. **QUESTIONS 4 AND 5 WERE NOT ANSWERED, AND THE SECOND IS LOAD-BEARING**: the scope of *SIMAP's system metadata* stays `UNRESOLVED`, so **no structured TED notice field is classified CC0** -- reading the reply's metadata sentence as covering notice fields would answer the operator's own question in the reuser's favour with a sentence not addressed to it. The COM_REUSE vs CC BY catalogue mapping stays `NOT_FULLY_RESOLVED` and is **non-blocking**, because reuse is authorised directly and does not depend on catalogue metadata. **ATTRIBUTION GOT STRICTER, NOT LOOSER**: the legal notice's procurement-notice sentence states no acknowledgement condition and the reply does, which is **Article 6(2)(a)** applied to the notice corpus itself -- three regimes stay apart, NOTICES acknowledge, EDITORIAL is CC BY credit plus indication of changes, CC0 owes nothing. **THE COMMERCIAL PROFILE'S BLOCKER CHANGED IDENTITY AND DID NOT CLEAR**: all six activities were already PERMITTED and H-36 was the blocker; what blocks it now is `raw_redistribution`, `raw_resale` and `customer_facing_source_access`, **which the operator's own question never described** -- a reply answers the question asked, and commercial purpose is not unrestricted redistribution. **APPENDING ORPHANS THE OPERATOR'S ACCEPTANCE BY DESIGN**: local v2 -> v3, commercial v5 -> v6, **255 insertions and 0 deletions**, three capability conditions re-verified mechanically and the HUMAN_CONFIRMATION one cannot be, so **TED is INELIGIBLE under the local profile until a named operator records it again**. Mission 1.29 withdrew an append to avoid exactly this and the precedent was weighed: there, recording an UNCLEAR verdict that refused anyway gained nothing, so breaking acquisition was pure loss; here the record gains the load-bearing answer of the whole TED arc, and **what the operator accepted has itself changed**. `record_ted_operator_acceptance.py` **refuses against v3 and was NOT repointed** -- its own guard says *the acceptance has to be made again by a person, not replayed*, and repointing it would turn a replay into a record of a decision nobody has taken. **THE FIRST OPERATOR_CORRESPONDENCE ROW FOUND A MODEL GAP**: the type has been permitted since migration 0004 and every evidence row was required to carry an `http(s)` URL, enforced in the schema, the model AND the validator -- **a letter has no URL**, so the enum permitted a class of evidence the URL rule refused, invisibly, because nobody had tried. The rule's own justification is about **published pages**, which change under a stable address; correspondence is fixed when sent. **Migration 0033** lets correspondence address itself by `mailto:` and requires a **fingerprint**, both halves or neither. **THE ARTIFACT IS NOT COMMITTED**: it carries a named official's direct phone and email and the operator's personal address, and this repository is public -- so the SHA-256, the operative text and the re-opening mailbox are preserved instead, because a governance record that breached the minimisation obligation it exists to check would be a poor record. **NO PERSONAL-DATA FIELD EXISTS IN ANY OF THE 188 TED RECORDS HELD**, measured over 97 raw and 34 normalized payload paths, and the collector retrieved LESS than authorised. 0 research-data requests, 6 governance document requests over 4 URLs, 0 model calls, **0 reliability changes and TED's 0.5 and 0.55 unchanged** -- a more permissive reuse position must never raise a reliability. **44 tests failed on the append and every one was repaired by keeping the property and dropping the incidental number**, including the two OPERATOR_CORRESPONDENCE tripwires Mission 1.15.4 installed for this exact moment, and a test whose own docstring had predicted it: *v1 owns its own row and stays FALSE. A future v3 would too.* Training, embeddings and external model egress all unchanged; H-39 untouched; Problem-Family still PARKED |
| 1.78 | 2026-09-04 | **WIKIMEDIA_CONVERGENT_OPERATOR_RELIABILITY_DECISION_PERSISTED: `max(members)` received FOUR real items, and the number still did not move.** The operator typed the confirmation, and **two counters moved while thirteen did not**: ReliabilityAssessments 3 -> **4**, basis rows 10 -> **12**. Assessment `19e0ce16` v1, `0.6`, HUMAN_REVIEW, thibchm, `human-reliability-assessment-rubric@1.0.0` -- the **second** assessment that can say which procedure produced it, while both pre-rubric rows keep NULL because backfilling would fabricate the provenance the column records. **ALL 18 CONVERGENT ROWS RESOLVE AND NOT ONE STORES THE NUMBER**: `scoring.evidence.reliability` is NULL on all 57 rows before and after. **36 leak checks, 0 leaks** -- a fourth current assessment is a fourth set of ways to leak, and the detailed Wikimedia `0.65` sharing FOUR of five scope fields still does not reach this scope. **ALL SIX MULTI-EVIDENCE CLAIMS BECAME SCORABLE, 2 -> 8 corpus-wide**, and the grouping arithmetic finally ran at cardinality above two: `max(members)` received **4, 3, 3, 3, 3, 2** real canonical items with `collapsed_member_count` 3, 2, 2, 2, 2, 1. **AND THE RESULT IS `IDENTICAL_TO_RELIABILITY_PASS_THROUGH` ON ALL SIX, WHICH MISSION 1.43 PREDICTED ALGEBRAICALLY**: one group per Claim, saturation over one group is that group's strength, group strength is `max()` over identical reliability-limited `q` values, and B-2 reports the same maximum. So §18's **`AGGREGATION_MECHANISM_STILL_UNIDENTIFIABLE_FROM_REAL_CORPUS`** is reported explicitly, and **calibration is NOT recommended merely because the scorable count increased**. `q = 0.6` with **`reliability` limiting on 34 of 34**, masses 0.6/0/0/0.4, EvidenceScore 60.0, **level 1 blocked on *2 supporting groups of established independence, found 0 (plus 1 unknown-provenance group, which does not count)*** -- reliability reaches none of the three blockers. **FOUR WITNESSES IS NOT CORROBORATION**: one publisher, one counting methodology, one classification mechanism, one pipeline, independence UNKNOWN on all 18 rows, **0 groups created**, and the reviewer wrote that sentence into the stated limitation themselves. Target variable `{0.5: 6, 0.55: 4, 0.6: 6, 0.65: 18}` -- a fourth value and not a fourth kind of thing. **THE MIDPOINT COINCIDENCE WAS NOT TREATED AS EVIDENCE**: `0.6` is exactly halfway between the detailed `0.65` and the convergent TED `0.55`, an averaging test was written, it failed, and **the test was removed rather than the operator's value questioned** -- software cannot prove a number's provenance from the number, so what is asserted is only that it equals none of the three it might have been copied from. **A PRE-PERSISTENCE TEST CLASS ASSERTED THE ABSENCE OF THE ASSESSMENT** and was re-pointed rather than deleted, and it caught a real omission: the rendered review page still said *Nothing yet*. 0 model calls, 0 network requests, 0 calibration labels, 0 parameters fitted, 0 scores, 0 Opportunity changes, 0 embeddings, profile still UNCALIBRATED, Problem-Family still PARKED |
| 1.77 | 2026-09-04 | **READY_FOR_WIKIMEDIA_CONVERGENT_RELIABILITY_REVIEW: the closest near miss yet, and the distinction between *nothing* and *not enough*.** 18 Evidence across 6 Claims, cardinalities **{4,3,3,3,3,2}**, collapsing to **exactly one** five-part scope resolving NO_APPLICABLE_ASSESSMENT. **THE ALMOST-MATCH IS TIGHTER THAN TED'S**: same publisher, same resource, same record kind, same claim type, and a reviewed **0.65 sitting one field away** -- the most inviting number in the repository to reach for. `proposition_kind` alone decides it, verified through the REAL resolver in both directions and by **30 leak checks, 0 leaks**, probing EVERY proposition kind in the corpus rather than a chosen few. **SOFTWARE ASSERTED EXACTLY ONE STATE AND DELIBERATELY NOT THE OBVIOUS ONE.** Mission 1.42 could assert `NOT_ESTABLISHED` for TED's mutability because the basis said NOTHING; here it says SOMETHING AND NOT ENOUGH -- a dated known-problems list records a 2016 user-agent classification incident and states no revision policy -- and *something and not enough* is a judgement about SUFFICIENCY, so `HISTORICAL_MUTABILITY` was left **blank**, which is precisely where a helpful generator would have filled it in. The one assertion is `SOURCE_SIDE_CHECKABILITY = NOT_ESTABLISHED`, because the basis is two documents and neither addresses what the source exposes for inspection. **THE NEW QUESTION CONVERGENCE INTRODUCES**: multiple witnesses of ONE METHODOLOGY do not insure against a METHODOLOGY-LEVEL failure -- a localised problem matters LESS to an existential, and a systematic reclassification matters MORE, because the witnesses share a counting rule and their independence is UNKNOWN. So the known-problems document is **PARTIALLY_APPLICABLE with its weight moving in two directions at once**, and the reviewer decides which governs. **NOTHING WAS FETCHED** -- the convergent proposition reads the same measurement through the same rules. **A THIRD DEFECT OF THE SAME SHAPE, FOUND BY §37 ON ITS FIRST RUN**: `ReliabilityBinding.to_json()` called `.isoformat()` on a field four generators already pass as `None`, and had never crashed because NO LIVE BINDING HAD EVER BEEN SERIALISED in this scope. 0 assessments, 0 basis rows, 0 network requests, 0 model calls, every counter unchanged, all 18 rows still NON_SCORABLE and all six Claims still UNAVAILABLE |
| 1.76 | 2026-09-04 | **CALIBRATION_REFERENCE_CORPUS_MEANINGFULLY_EXPANDED, and the measurement that reframes what expansion is FOR.** Measured over all 37 Claims before any work: **0 with more than one support group, 0 where the aggregator differs from the Mission 1.37 B-2 pass-through baseline** -- and with ONE group that identity is **ALGEBRAIC, not incidental**: saturation over a single group is that group's strength, which is `max(members)`, which is what B-2 reports. **So no quantity of additional single-group Evidence can ever make them differ**; the aggregation layer becomes measurable only through ESTABLISHED INDEPENDENCE or CONTRADICTION, and a §37 fixture proves the converse by giving two `KNOWN_INDEPENDENT` items and watching support strength EXCEED pass-through. **A SECOND CONVERGENCE CONTRACT, FROM DATA ALREADY HELD**: `platform-counted-content-request-change-witnessed@1.0.0` over the 18 Wikimedia Signals, **0 network requests** -- which was not merely cheaper but the only open door, because Wikimedia acquisition is currently blocked by three unsatisfied conditions in this deployment. Claims 37 -> **43**, Evidence 39 -> **57**, Claims with >1 Evidence 2 -> **8**, and **max Evidence per Claim 2 -> 4**: group cardinality varies for the first time `{1,2}` -> `{1,2,3,4}`. **THE SCORABLE OPTION WAS REFUSED**: another TED division would have been immediately scorable and, by the finding above, could not have taught anything -- choosing it because a number would appear is choosing the appearance of progress. **`audience_class` STAYS IDENTITY** because Mission 1.19 made it REQUIRED so one item over one period cannot carry two counts under one name. **NOTHING WAS MANUFACTURED**: no contradiction (a decrease does not contradict an increase, and an existential is not falsified by a counterexample), no independence (one publisher, one pipeline, one method), **no temporality -- and the reason is architectural: every OBSERVED restatement is a historical fact about what a source published, and a historical fact does not decay**, even where the source's timestamps are documented. Secondary **NEW_CORPUS_SHAPE_NON_SCORABLE_MISSING_RELIABILITY**: a new kind is a new scope and none was invented or copied. **Leakage-safe splits are still NOT plausible** -- six new Claims share one scope and one kind, so they are ONE group. 0 model calls, 0 embeddings, 0 assessments, 0 independence groups, 0 scores, profile still UNCALIBRATED |
| 1.75 | 2026-09-04 | **SECOND_PILOT_OPERATOR_RELIABILITY_DECISION_PERSISTED: `max(members)` received TWO REAL ITEMS for the first time, and the number did not move.** The operator typed the confirmation, and **two counters moved while thirteen did not**: ReliabilityAssessments 2 -> **3**, basis rows 6 -> **10**. Assessment `d1afa4be` v1, `0.55`, HUMAN_REVIEW, thibchm, `human-reliability-assessment-rubric@1.0.0` -- **the first assessment in this repository that can say which procedure produced it**, while both historical rows keep NULL because they predate the rubric and backfilling would fabricate provenance. **ALL SIX CONVERGENT ROWS RESOLVE and NOT ONE STORES THE NUMBER**: `scoring.evidence.reliability` is NULL on all 39 rows, because reliability binds late and a stale copy could outlive its assessment. **9 leak checks, 0 leaks** -- a third current assessment is a third set of ways to leak, and neither TED scope reaches the other on `proposition_kind` alone. **BOTH REAL MULTI-EVIDENCE CLAIMS BECAME SCORABLE, 0 -> 2**, `raw = 2`, `scorable = 2`, and the grouping arithmetic finally ran: **ONE support group of kind UNKNOWN with TWO members and `collapsed_member_count` 1**. Mission 1.41 had `raw = 2` with `scorable = 0`, so `max(members)` had never seen both. **AND THE RESULT IS `IDENTICAL_TO_RELIABILITY_PASS_THROUGH`, WHICH IS NOT A FAILURE**: both rows share one assessment, independence is UNKNOWN so they collapse into one group, and `max()` of two identical `q` values is that value -- the full aggregator and Mission 1.37's B-2 baseline agree **because the corpus gives them nothing to disagree about**. `q = 0.55` with **`reliability` limiting on 28 of 28**, masses 0.55/0/0/0.45, EvidenceScore 55.0, **level 1 blocked on *2 supporting groups of established independence, found 0*** -- reliability reaches none of the three blockers. **DISJOINT IS NOT INDEPENDENCE**, 0 groups created. Target variable `{0.5: 6, 0.55: 4, 0.65: 18}`, still all reviewed reliability. **A THIRD DEFECT OF THE SAME SHAPE**: the reporter read `group.members`, the attribute is `member_evidence_ids`, and `max(..., default=0)` never evaluated its generator while zero groups existed -- **a branch no data has ever entered is not tested by a passing suite**, found by the operator running it. 0 model calls, 0 acquisitions, 0 scores, profile still UNCALIBRATED |
| 1.74 | 2026-09-04 | **OPERATOR_CONFIRMATION_REQUIRED, for the second time and for the same reason: the value is authorised and the keystroke is not.** Everything a mission may legitimately do is done -- migration **0032** adds `review_rubric_id` and `review_rubric_version`, the operator's completed review is frozen as an artifact that conforms to the rubric it names, and the dry run validates at **version 1, HUMAN_REVIEW, thibchm, 0.55, human-reliability-assessment-rubric@1.0.0, 4 document-backed basis rows**. **0 assessments persisted, 0 model calls, 0 acquisitions, every counter unchanged.** The brief supplied the operator's VALUES and cannot supply the operator's KEYSTROKE: piping the confirmation, patching `isatty` or writing the row by hand would each produce an assessment whose `reviewed_by` names a person who did not type it. **THE SCOPE WAS NOT NARROWED, AND THAT WAS THE LIVE TEMPTATION** -- the second pilot produced the two multi-Evidence division-92 Claims and the assessment is NOT about them: the scope carries no division and no currency, so one judgement binds **divisions 90 AND 92, EUR AND SEK**, 6 rows across 4 Claims. **NOTHING IS BACKFILLED AND NULL IS THE TRUE ANSWER**: both historical rows read NULL after the migration, because writing a rubric id onto a review that did not use one fabricates the provenance the column was added to record -- and **the basis table was considered and REJECTED as the place for it**, since a basis row names a document ABOUT THE MEASUREMENT. **BOTH HALVES OR NEITHER**, enforced twice: a CHECK constraint and `__post_init__`. **`UNSURE` SURVIVES AS `UNSURE`** on retrievability -- not YES, not NO, not low confidence, not 0.5 -- and is carried into the stated limitation rather than quietly resolved. `0.55` is neither 0.5 nor 0.65 nor their mean, and a test asserts all three. **A PRE-EXISTING TEST PINNED THE BINDING'S KEY SET** and was re-pointed rather than deleted: which procedure produced a value IS part of reconstructing it, which is the property that test asserts. Pre-persistence baseline recorded honestly: **0/6 resolved, 0 scorable, `max(members)` receiving 0** |
| 1.73 | 2026-09-04 | **HUMAN_RELIABILITY_RUBRIC_READY: the architecture defined the question, the scope, the reviewer and the evidence, and then handed over a blank numeric field.** `human-reliability-assessment-rubric@1.0.0` is that missing middle, and it is a DECISION PROCEDURE rather than a scoring function -- **the module contains no arithmetic operator of any kind**, asserted over its AST, because the one failure to avoid was solving arbitrary numbers with different arbitrary numbers. **FIVE dimensions accepted and SIX rejected, and the rejections are the substance**: `MEASUREMENT_TO_PROPOSITION_FIT` **is `directness`** and scoring it here would make one weakness count twice -- its residue is not a gradient but a MIS-SPECIFIED SCOPE, so it became a hard stop; `CLASSIFICATION_DEPENDABILITY` folded in, because a dimension for it would be a rubric shaped around one publisher's taxonomy; `KNOWN_FAILURE_MODES` and `RESIDUAL_UNKNOWN` are the OUTPUT of the five, not a sixth question; and a separate **reviewer-confidence field was refused** because basis completeness is READ OFF the profile and two fields answering one question eventually disagree. **UNKNOWN IS NOT LOW, STRUCTURALLY**: `NOT_ESTABLISHED` and `CONTRADICTED` carry **no ordinal rank**, so neither can be interpolated, averaged or read as the bottom of a scale. **NO INTERMEDIATE ANCHORS**, deliberately -- nothing in this repository anchors the absolute scale, so one would have to be invented; the two anchors that exist are defined by what the value DOES in `q = min(components)` rather than by an adjective, and **`0.0` is a POSITIVE FINDING and not the absence of an assessment**. Recommendation **`KEEP_NUMERIC_FIELD_BUT_REQUIRE_ORDINAL_REVIEW_PROFILE_FIRST`**: no migration, no code change, both historical values kept, and the number becomes a summary of a RECORDED PROFILE which is what a second reviewer reproduces. **THE EXISTING ARCHITECTURE ALREADY ANSWERED HALF THE DISAGREEMENT QUESTION** -- the resolver refuses on >1 current assessment, so while a disagreement is open the honest state is ABSENCE; what is missing is disagreeing WITHOUT superseding. **THE WIKIMEDIA REVIEWER HAD ALREADY WRITTEN `HISTORICAL_MUTABILITY` DOWN UNPROMPTED**, months before this rubric derived it from TED's open question -- corroboration that the dimensions are real, bounded by both reviews sharing a reviewer. Both historical assessments are **PARTIALLY_REPRESENTABLE** and **unchanged**. Secondary: **`RELIABILITY_RUBRIC_PROVENANCE_MODEL_GAP`** -- no column records which procedure produced a value, and **the basis table is not the answer** because a basis row names a document about the MEASUREMENT. 0 assessments, 0 model calls, 0 acquisitions, every counter unchanged, and **the TED worksheet is prepared and UNANSWERED** |
| 1.72 | 2026-09-04 | **READY_FOR_SECOND_PILOT_RELIABILITY_REVIEW: the question is prepared for a scope that is BROADER than the mission that prompted it, and software supplied no answer.** The brief expected 4 Evidence rows on 2 Claims; the live scope holds **6 rows across 4 Claims**, resolving to **exactly one** scope which is exactly the expected five-part one. **That is not §30 C.** Drift would be Evidence rows failing to match the five-part scope; what differs is the COUNT INSIDE it, because **a reliability scope carries no classification division and no currency** -- so one judgement here binds the SEK claim and the **division-90** claim too, whose only witness is the Signal derived in Mission 1.15.10 **before the second pilot existed**. Mission 1.40 recorded the same property from the other side. **THE NEAR MISS IS THE WHOLE TEST**: the existing TED `0.5` shares source, resource, record kind AND `claim_type: OBSERVED` -- **four of five** -- and the single differing field is `proposition_kind`, exercised through the REAL resolver in both directions and confirmed by **6 leak checks, 0 leaks**. **NOTHING NEW WAS RETRIEVED, because nothing new was needed**: the convergent proposition reads the same BT-161 field of the same notices, so 3 of 4 existing basis rows are REUSED and BT-195-BT-198 is **PARTIALLY_APPLICABLE** -- the FACT is unchanged and its WEIGHT is not, since withholding bounds a named cohort and cannot falsify an existential. **FOUR RELIABILITY QUESTIONS ARE GENUINELY NEW** and none has a documentary answer: an existential is MONOTONE, and whether that makes it more dependable or merely **harder to falsify** is a judgement; it carries no period (H-37); it asserts about a CLASS; and **two cohorts are asserted to witness one proposition**, a step that does not exist for the detailed claim. **THE LARGEST RESIDUAL UNKNOWN HAS NO DOCUMENT AND NO MITIGATION**: whether a published notice can be corrected or superseded, which bears directly on whether a witnessing cohort still witnesses. **ENGINEERING VALIDATION IS RECORDED AND REFUSED AS BASIS** -- currency grain being correctly bounded does not imply reliability, `DISJOINT` overlap does not imply independence (UNKNOWN on all 6 rows, 0 groups), and rewarding the system numerically because its own tests pass is the error the separation exists to prevent. **0 assessments, 0 basis rows, 0 network requests, 0 model calls, every canonical counter unchanged**, `scoring.evidence.reliability` NULL on all 39 rows, profile still UNCALIBRATED, Problem-Family still PARKED. **The next action is a HUMAN decision and Mission 1.42.1 was NOT started** |
| 1.71 | 2026-09-03 | **PROCUREMENT_COHORT_GRAIN_REPAIRED_REAL_MULTI_EVIDENCE_CREATED: Claims with more than one Evidence row, 0 -> 2.** Two real canonical Claims, two genuinely distinct witnesses each, **revision 1 on both**, and the real aggregator receiving `raw_evidence_count = 2`. **ZERO network acquisitions**: the frozen windows were reconstructed from the 177 records Mission 1.40 already persisted. **TWO DEFECTS OF ONE SHAPE, both found by real data and both a docstring disagreeing with its code.** The cohort key called currency and amount scope load-bearing and contained neither; `derive` refuses unless each is single-valued, so **the implementation was wrong, not the documentation** -- a dimension the validation demands be equal is what makes a cohort comparable. And `_persist_evidence` said *idempotent on (workspace_id, claim_id, signal_id)* while the query added `AND extraction_method`, so a new interpreter version INSERTED a second row. **Evidence identity is epistemic; the procedure that produced it is provenance** -- `extraction_method` is still written and still read, it just no longer decides. **A CHANGED assessment is neither unchanged nor a second observation, and no third answer was invented**: a disagreeing row is REPORTED as a conflict and nothing is written, because representing a revision needs a model this architecture lacks. Extractor **1.0.1 -> 1.1.0**, MINOR because **adding a field to a grouping key can only SPLIT groups, never merge them** -- and §6 verified it rather than arguing it: division 90 re-derived with magnitude, currency, direction, amount types, scopes and codes **all identical**, its 3 inputs still one group. **Window A went from 0 derived cohorts to 2**; single-member PLN, DKK and CZK cohorts now refuse for the right reason. **§22/§23 enforced rather than assumed**: window B's unchanged EUR cohort was SKIPPED as an existing witness, because a new procedure version over identical membership is historical versioning and not a second observation. **NO FX CONVERSION** anywhere. Overlap DISJOINT and independence still UNKNOWN on all six rows with 0 groups -- disjoint records are not independent evidence. **The audit itself had a defect**: `multi_evidence_claims` was computed over SCORABLE units and reported 0 while two real ones existed. 0 model calls, 0 embeddings, 0 new assessments, Opportunity untouched |
| 1.70 | 2026-09-03 | **SECOND_PILOT_REAL_MULTI_EVIDENCE_NOT_OBSERVED: the convergence contract was never the blocker, and a currency guard was.** CPV division **92 'Recreational, cultural and sporting services'** selected under a frozen ordinal rule, every label verified ONE CONCEPT PER FETCH against the Publications Office authority register. **A bulk EUR-Lex extraction was retrieved and REFUSED**: it gave `90000000-8` where this repository's own division-90 data uses a different check digit, and labelled 92000000 *Miscellaneous services*, which the register contradicts -- a summarising model over a long annex produces plausible output, and plausible output carrying an official label is worse than none. Acquisition ran to the frozen plan: **177 notices across two frozen windows, both COMPLETE_BOUNDED_QUERY**. Then **three of four cohorts were REFUSED for mixed currencies** (EUR/PLN, DKK/EUR, CZK/EUR/SEK) and window A produced NO Signal at all, so division 92 has ONE witness and `claims with >1 Evidence` is still **0**. §37 forbids widening the window, switching category or regrouping, and none was done. **THE EXTRACTOR'S COHORT KEY DOES NOT CONTAIN WHAT ITS DOCSTRING SAYS**: it names notice class, amount scope, currency and CPV division as load-bearing, and the key holds `source_id | record_kind_id | resource_id | notice_class | cpv_division` -- currency and amount scope are validated AFTER grouping and refuse the WHOLE cohort rather than splitting it. Had currency been a grouping dimension, window A would very likely have yielded EUR cohorts and this mission would have succeeded. **NOT FIXED**, because changing a grouping key after seeing which data it rejected is the shape §37 and §41 both refuse. **A DUPLICATE EVIDENCE ROW WAS CREATED BY THIS RUN AND REMOVED**: re-interpreting the pre-existing division-90 Signal wrote a second Evidence row differing only by interpreter version (1.1.0 -> 1.4.1), which is §13's forbidden case verbatim and Mission 1.32's known idempotency defect, and which briefly made the corpus report a FALSE `claims with >1 evidence: 1`. **The existing TED assessment BINDS to the new division-92 DETAILED claim** -- its scope carries no classification division -- **and not to either convergent claim**, because proposition_kind differs. 0 model calls, 0 embeddings, 0 new assessments, 0 independence groups, no Opportunity |
| 1.69 | 2026-09-03 | **PROPOSITION_CONVERGENCE_CONTRACT_READY: `max(members)` finally receives more than one member.** ADR-035 introduces the distinction the Claim model did not make -- **PROPOSITION IDENTITY facts decide WHAT is asserted, WITNESS facts decide WHICH observation demonstrates it** -- with one test applied field by field: *if changing F changes what the Claim asserts it is identity; if it only changes which observation witnesses the same assertion it may be witness*. **A witness fact is not discarded**, it stops being an identity: `notice_ids` stays on the Signal and is recovered in a test from the persisted scope. **OBSERVED convergence is legitimate and narrow**: an existential over a publication passes §2's own question -- *can a person go and read it there* -- and the broader proposition is ENTAILED BY the detailed one rather than a weakened copy, which is why it is a new kind and `notice_ids` stays identity on the old one. **The constructor refuses a non-OBSERVED contract**, so the unbuilt INFERRED layer cannot be built here by accident, and it refuses one without `source_id` in identity, because attribution is part of an OBSERVED proposition. **The TED template's own objection was answered rather than ignored**: *a proposition that cannot say WHICH notices is not checkable* -- checkability MOVES to the witness, and the bound stays in the wording as *at least one bounded set*. **CONVERGENCE IS NOT INDEPENDENCE**: two disjoint cohorts collapse into ONE group because independence stays UNKNOWN, saturation still receives one group, and that is correct rather than a shortfall. **A test caught a vocabulary collision**: `ObservationOverlap` was drafted with `UNKNOWN`, which `EvidenceIndependenceState` already has, and sharing a member name is how a mapping gets written by accident -- renamed `UNESTABLISHED`. Proved through the REAL repository and REAL aggregator on synthetic fixtures in a disposable workspace: one Claim, two Evidence, **one revision**, idempotent replay, Docker/Podman/Kubernetes still three keys. **Not wired into the production job**, so no Signal here can witness two Claims. 0 acquisitions, 0 model calls, 0 embeddings, every live counter unchanged, feasibility audit byte-identical |
| 1.68 | 2026-09-03 | **MULTI_EVIDENCE_CLAIM_ARCHITECTURE_GAP: convergence is ONE proposition fact away, and that fact is the one that says WHAT WAS MEASURED.** Mission 1.37 found the symptom -- one Evidence per Claim -- and this is the cause. **The persistence layer already supports N Evidence on one Claim**: `_persist_one` looks a draft up by `proposition_key` and attaches evidence to the claim it finds, and the aggregation framework's own §1 asks *given several Evidence records bearing on one Claim*. **The interpreter can never produce two drafts with the same key**: all seven templates put `source_id` in their facts PLUS the measurement's own identity -- `content_id`, `metric_id`, `community_tag`, `term`, `notice_ids` -- plus the period labels. So two Signals converge only if they are the SAME measurement, which §13 forbids. **Measured: 28 Claims, 28 distinct keys, closest pairs differ by EXACTLY ONE fact, and in twelve pairs that fact is `content_id`** -- Docker, Podman and Kubernetes on the same day, which is exactly what removing the field would merge. **HALF THE BEHAVIOUR IS CORRECT AND MUST NOT BE REPAIRED**: for an OBSERVED claim attribution IS the claim, so *Wikimedia counted X* and *Stack Exchange published Y* are two propositions and deleting `source_id` is not the fix. **Six candidates, and the pattern is the finding**: the two that pass taxonomy and governance (TED CPV, a non-developer Stack Exchange tag) fail on the architecture; the two that pass the architecture vacuously fail on taxonomy (Wikimedia articles, GDELT terms); the best domain diversity (Steam, App Store, Google Play, Product Hunt) is BLOCKED AT THE ELIGIBILITY GATE and §4 is a hard stop. **Only four of 29 sources are eligible, resource-ready and collector-implemented.** Identity was NOT weakened to avoid the outcome: the concrete convergence that should work -- two DISJOINT TED cohorts in one division -- needs `notice_ids` and `classification_codes` removed, and §8 forbids that. 0 acquisitions, 0 model calls, 0 embeddings, every counter unchanged, audit byte-identical |
| 1.67 | 2026-09-03 | **CALIBRATION_STRATEGY_READY_REFERENCE_DATA_MISSING: the aggregation layer has never aggregated.** Measured against the live database, not quoted: **28 Claims, 28 Evidence rows, and the distinct evidence-count-per-claim is `[1]`**. So saturation has never combined two groups, independence collapse has never collapsed anything, `max(members)` has never had more than one member, contradiction accumulation has never run, and three of the four masses have only ever taken their `c = 0` values. **`min()` is currently indistinguishable from `return reliability`**, because relevance, directness and extraction confidence are 1.0 on every row and every Claim is EVERGREEN. **THE TARGET VARIABLE HAS TWO VALUES AND BOTH ARE REVIEWED RELIABILITY VALUES** (0.5 x1, 0.65 x18), `reliability` limits 19 of 19 scorable claims, and the leakage rule yields **2 groups among 19 units**, which cannot be split at all -- so the §29 echo hazard is not a risk here, it is the entire dataset. **THE MISSION 1.1 PLAN PROPOSES THE WRONG TARGET, and correcting it is the substantive finding**: its §5 asks *do claims scoring 70-80 resolve favourably more often* with a *Brier-style summary*, which is an OUTCOME-RESOLUTION target measuring the state of the WORLD, against a framework whose §1 says *Not a truth estimator ... every quantity describes the state of the evidence*. The plan states the counter-argument in the same section and keeps the metric anyway. **A SECOND GAP RESTRICTS RATHER THAN BLOCKS**: nothing anchors the ABSOLUTE scale, so calibration targets the ORDINAL construct -- which pair of evidence sets is better supported -- and absolute level is out of scope until the framework supplies an anchor. **Baseline B-2, the reliability pass-through, is the one that decides whether any of this is worth doing**, and today it is numerically identical to the full aggregator on 19 of 19. `TEMPORAL_CALIBRATION_DATA_MISSING` (0 temporal Claims, 0 claim features), `SAMPLE_REQUIREMENT_NOT_YET_QUANTIFIED`, and **3 of 14 gate conditions are recorded as BLOCKERS rather than given invented numbers**. 0 parameters changed, 0 profiles calibrated, 0 model calls, 0 acquisitions, D-03 unchanged |
| 1.66 | 2026-09-03 | **DOCKER_RELIABILITY_PARTIALLY_REVIEWED: the operator typed the confirmation, and the two counters that moved are the whole story.** ReliabilityAssessments 1 -> **2**, basis rows 4 -> **6**, and **fifteen other counters unchanged**. Six Wikimedia rows now RESOLVE `0.65` against assessment `e2419f13-...` v1, both Stack Exchange scopes stay NO_APPLICABLE_ASSESSMENT, and the TED assessment is untouched at v1 with `superseded_at` NULL, because **a different scope is a different question and not a revision of somebody else's answer**. **`scoring.evidence.reliability` IS STILL NULL ON ALL 28 ROWS** -- six rows resolve a number and not one stores it, because reliability binds LATE (ADR-026 Decision 2), so a score names the assessment and version it used and a stale copy cannot outlive the assessment it came from. **The negative checks went 3 to 6 and still found 0 leaks**, because a second assessment doubles the ways one could leak. **§15's diagnostic ran, and its shape is the argument for calibration**: EIGHT Evidence rows sit on EIGHT distinct Claims, so these are eight SINGLE-RECORD aggregations and reliability resolving does not turn six observations of one article into an aggregation. `q = 0.650` on all six with **`reliability` as the limiting component**, because `q = min(components)` and every other factor is 1.0 -- **the score is a restatement of one human judgement, not a corroboration of it**. Level stayed **1**, blocked by independence and by the MARKET_ACTIVITY gate, neither of which reliability touches; the two refused scopes report `UNAVAILABLE` with `uncertainty_mass` **1.0**. Profile still UNCALIBRATED, **0 scores persisted**, D-03 blocker 2 moves OPEN -> **PARTIAL** and the other four do not move. **A THIRD DEFECT SURFACED, AND ONLY BECAUSE A ROW FINALLY RESOLVED**: the resolution report read `binding.assessment_version`, which is not a field -- unreachable while every binding was None, the same shape as Mission 1.36's invalid basis types. **Code that could not have worked, unnoticed because the path was never taken** |
| 1.65 | 2026-09-03 | **OPERATOR_CONFIRMATION_REQUIRED: three human decisions carried faithfully, and the one assessment they authorise is NOT persisted.** The operator reviewed all three scopes and decided DIFFERENTLY about them -- **NO** on both Stack Exchange scopes, **0.65 / HUMAN_REVIEW / thibchm** on the Wikimedia one -- which is exactly what a per-scope judgement is for. **A NO IS NOT A NUMBER**: the refusal is recorded as PROSE, because a refusal recorded as data would be a value and the next reader would use it as one; it does not mean 0, 0.5, low reliability or an unreliable source, it means **no human reliability judgement exists**. **The TTY guard fired and was respected** -- *no terminal to confirm on. A reliability assessment is a human decision and this is not a step a pipeline runs* -- because piping the confirmation in would produce a row attributed to a person who did not type it, which is the failure the whole contract exists to prevent, so the mission STOPS and hands the operator the command. **0 assessments, 0 model calls, every one of the seventeen counters verified unchanged** against the live database, as §24 anticipates. **MISSION 1.36 SHIPPED A REAL DEFECT AND THIS MISSION FOUND IT**: the packet's `candidate_basis_rows` carried `basis_type` values that are not members of `ReliabilityBasisType`, so the rows it prepared **could not have recorded an assessment** -- the one thing candidate basis rows are for -- and nothing caught it because the packet is JSON and the enum lives in the contracts package. **D-03 blocker 2 is OPEN, not PARTIAL**: §19 anticipated PARTIAL, which describes the state AFTER confirmation, and reporting it now would be reporting a future. **§15's diagnostic was SKIPPED because it is conditional on a row becoming scorable and none did** -- running it anyway would produce a number computed from nothing, in an artifact later read as a result. No average, no *Docker 65%*, profile still UNCALIBRATED, independence still UNKNOWN with 0 groups |
| 1.64 | 2026-09-03 | **READY_FOR_OPERATOR_RELIABILITY_REVIEW: the question is prepared and software supplied no answer.** **THREE reliability scopes over the 8 Docker rows, not two** -- §0 forbids assuming two because two source families exist, and counting found three: the two Stack Exchange signal types persist **different proposition kinds**, so they share FOUR of five scope fields and are still two different reliability questions. 1 + 1 + 6 = 8, every row in exactly one scope. **NO NUMBER APPEARS ANYWHERE** -- no value, no range, no recommendation, no adjective ranking a source; `reliability: null` documented as NO ASSESSMENT EXISTS and never as 0.0 or 0.5; the scale stated with **no threshold labels** because the architecture defines none. **0 assessments created, all 14 counters unchanged, `scoring.evidence.reliability` NULL on every row** because reliability resolves late. **Wikimedia methodology RETRIEVED**: a pageview is a conjunction of HTTP/host/header tests with an enumerated exclusion list, and spider tagging is *ua-parser and additional custom regex* -- pattern matching, matching what the collector recorded as heuristic. Its largest gap: **revision and backfill practice is NOT DOCUMENTED**, which is an absence of documentation and not evidence of stability. **Stack Exchange documentation UNREACHABLE** (robots policy blocks the crawler); no retry, no mirror, no third-party summary -- so whether an accepted answer can later change is OPEN, and the operator supplying the documents is the route Mission 1.18 used. **The TED assessment shares `claim_type` with all three Docker scopes and differs on the other four** -- every row here is OBSERVED, so that field discriminates nothing and is exactly where a leak would start if matching were ever partial. **Four of five D-03 blockers remain open**, reported separately. A test caught a factual overstatement in my own packet and it was corrected rather than the test loosened |
| 1.63 | 2026-09-03 | **NO_AUTHORITATIVE_DOCKER_CATEGORY_RELATION_FOUND: the search happened and the registry is still empty.** Six candidates, six rejections, failing in **three distinct ways**: things that NAME Docker without classifying it (its own docs say *an open platform for developing, shipping, and running applications* and assign no category; the OCI defines three SPECIFICATIONS and uses *container engine* as a term with no register behind it -- **a term is not a category**, it has no identifier, no publisher deciding membership and no member list); things that CLASSIFY PRODUCTS without containing Docker; and things that classify **something else**. **The CNCF Landscape was refused on a countable fact**: its `landscape.yml` holds 1,138,659 bytes, 2,512 name fields and 15 categories, the word Docker occurs 53 times, and the five items named for it are Swarm (Orchestration), Compose (App Definition), Hub, a Wasm entry and **`Docker (member)`, the COMPANY** -- **the container platform is not an item at all**, and the three products sit in three DIFFERENT categories, so there is not even a single wrong answer to be tempted by. Independently: it calls itself *a map* that *attempts to categorize most of* the space with a **300-GitHub-star inclusion rule**, and a popularity threshold is not a classification rule. **CPV is `CPV_NOT_SUITABLE_FOR_DIRECT_PRODUCT_RELATION` on WHO ASSIGNS A CODE**: a contracting authority assigns one to ITS OWN CONTRACT, so a CPV class contains procurements and never products. UNSPSC returned HTTP 403 and stays UNRESOLVED rather than guessed. **The direction of reasoning was the methodology** -- ask what contains Docker, never what would reach the evidence we hold. 0 relations before and after, 0 model calls, all 13 counters unchanged. Next: **Reliability / Scoring Eligibility Foundation**, chosen explicitly over a second pilot |
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

### Two persistence paths, and the statement that keeps them apart

Added in 1.89 (Mission 1.55,
`deterministic-evaluation-persistence-orchestration-v1.md`,
`mission-1.55-report.md`).
**`DETERMINISTIC_EVALUATION_PERSISTENCE_ORCHESTRATION_READY`**, with readiness
reported in two halves.

    EvaluationOutcome
      +-- SUPPORTS / CONTRADICTS  -> Claim, ClaimRevision, derivation, Evidence
      +-- NOT_APPLICABLE / UNKNOWN -> one refusal row, and nothing else
    exhaustive over the four results, no else, no NEUTRAL

- **THE COMMAND DOES NOT OWN ITS TRANSACTION.** The connection arrives inside the
  caller's, which is what lets the directional path be atomic: the evidence
  requirement is a deferred trigger firing at COMMIT.
- **THE TARGET IS PASSED ALONGSIDE THE OUTCOME.** A refusal carries no
  proposition key and no Claim draft, deliberately -- the evaluator declines to
  name a proposition it declined to establish -- and migration 0035 requires
  both. The caller supplies the target it chose, because **a target is an input,
  not a conclusion.**
- **THE STATEMENT IS COMPOSED FROM THE TARGET AND NOTHING ELSE**, and it is where
  ADR-036's multi-witness architecture is actually decided. A statement naming
  the witness or the measurement would append a ClaimRevision per Signal, saying
  the proposition was reformulated when only the evidence grew.
- **IDEMPOTENT MEANS SAME IDENTITY AND SAME PAYLOAD.** A matching unique key with
  a different payload is a conflict. `evaluator_version` is excluded from the
  derivation comparison because the identity excludes it: rebuilding the software
  is not a new derivation, and a different conclusion under one rule version is.
- **POLICY D IS OPTION A**: persist the disagreeing derivation, leave Evidence
  untouched, return `REVIEW_REQUIRED`. Detection is read from
  `_persist_evidence`'s existing refusal rather than re-implemented.
- **THE CONFLICT IS DURABLY DETECTABLE AND NOT DECLARED.** An exact join finds
  it; no row says a human should look. That distinction is the whole reason
  unattended readiness is `false` while the foundation is ready, and the two must
  not be collapsed.
- **THE ORCHESTRATOR DECIDES NOTHING EPISTEMIC** -- no evaluation, no threshold
  selection, no equivalence, no independence, no reliability, no aggregation, no
  model -- and the imports say so. Thresholds are read-only: a missing one fails
  before any write, because registering the bound on the way past would be the
  analyst choosing the number after seeing the measurement.

**Mission 1.56 -- First Deterministic Inferred Claim Persistence Pilot V1 is
ATTENDED**, one candidate, from data already held, with the threshold frozen
before the evaluation. The resulting Evidence will resolve
`NO_APPLICABLE_ASSESSMENT` and be `NON_SCORABLE`, which is correct.
**Mission 1.56 was not started.**

**COMPLETED IN 1.90 (Mission 1.56). Every prediction above held, and the
evaluator refuted the proposition it was asked about.**

    threshold registered  0 -> 1        INFERRED Claims  0 -> 1
    claim_derivations     0 -> 1        refusals         0 -> 0
    Evidence  57 -> 58, and the 58th is the first CONTRADICTS row in the repository
    replayed: REUSED, 0 rows created, every counter identical

- **THE PILOT SUCCEEDED BY PRODUCING A REFUTATION.** 912 requests against a bound
  of 1000 is `CONTRADICTS`. The manifest declared all four results legitimate
  before the evaluation ran, so there was no path by which SUPPORTS would have
  been a better outcome -- and a pilot that could only have succeeded one way
  would have been measuring the threshold rather than the measurement.
- **THE FIRST `CONTRADICTS` EVIDENCE ROW, AND THE CONTRADICTION CASE IS STILL
  UNREACHED.** Both halves, together. ADR-036 removes `direction` from
  proposition identity, which is what makes the row expressible at all. But
  contradiction enters the ARITHMETIC only when one Claim carries evidence in
  both directions, and `claims_carrying_both_directions` is **0** -- this Claim
  has one witness and can never have another, because only Wikimedia's own logs
  can measure requests to a Wikipedia article. That is
  `SOURCE_INDEPENDENCE_IS_PARTIAL`, disclosed to the operator BEFORE approval
  rather than explained afterwards.
- **THE APPROVAL IS A HASH, AND THE MANIFEST WAS NOT EDITED AFTERWARDS.** Marking
  it APPROVED would change its bytes and therefore its hash, and **a frozen
  document that no longer answers to the hash it was frozen at is not frozen.**
  So the status still reads `AWAITING_OPERATOR_APPROVAL`, the validator refuses
  any other value, and the approval lives in the execution record -- which the CI
  gate re-checks against the manifest on disk, so a later edit turns the gate red
  rather than leaving *approved* beside a document nobody approved.
- **PREREGISTERED WAS IMPOSSIBLE, NOT UNCHOSEN, AND IT IS EXECUTED RATHER THAN
  ARGUED.** The measurement was retrieved at `2026-09-01T21:03:47Z`, read from
  the rows; the bound could not be recorded before today. A test hands the real
  evaluator a PREREGISTERED registration with those timings and gets
  `UNKNOWN / PREREGISTRATION_TIMING_INCONSISTENT`. The bound sits ABOVE the
  measurement, so the pilot cannot be read as fitted -- and the fact that 912 was
  visible when 1000 was chosen is written INTO the manifest, because for held
  data it always is and hiding it would be the outcome-chasing POST_HOC exists to
  name.
- **THE BOUND WAS COMMITTED BEFORE THE EVALUATOR WAS CONSTRUCTED.** Registering a
  threshold on the way past is the analyst choosing the number while the
  comparison runs.
- **THE DERIVATION NAMES THE OBSERVATION IT REASONED FROM, SELECTED
  STRUCTURALLY.** The Signal witnesses TWO OBSERVED Claims, and the detailed
  restatement is the one whose proposition carries the same two day labels the
  target does -- Mission 1.43's convergent existential deliberately carries none,
  because there the labels are witness rather than identity. No manifest field
  was added to encode a fact the rows already state.
- **NO RELIABILITY WAS INVENTED, AND THE NEAR MISS IS THE TEST.** Through the real
  resolver over all four current assessments: `NO_APPLICABLE_ASSESSMENT`. The
  reviewed Wikimedia `0.65` shares source, resource and record kind and differs
  on `claim_type` AND `proposition_kind`. Evidence `NON_SCORABLE`, aggregation
  `UNAVAILABLE`, no score, no rank.

**The next mission is NOT a second pilot, and not calibration.** A second
candidate from the same family would repeat this one exactly; calibration is
still blocked by the arithmetic Mission 1.43 established. What this run makes
newly answerable is the question Mission 1.48 could not ask: **the contradiction
case now needs only a second witness disagreeing about ONE threshold
proposition**, and the INFERRED layer is the first place in this repository where
two witnesses can reach one Claim at all. That is an
**independence-capable evidence route**, unchanged as the target since 1.78, and
it is now worth strictly more than it was before this pilot ran.


**COMPLETED IN 1.91 (Mission 1.57). The route exists, it is not in this
portfolio, and the reason is now a law rather than a run of bad luck.**

    a platform-recorded quantity   -> measurable ONLY by that platform
    a world quantity               -> measurable by more than one apparatus
    every registered source        -> measures the first kind

- **`INDEPENDENCE_CAPABLE_ROUTE_GOVERNANCE_PENDING`.** One apparatus pair passes
  every mandatory epistemic gate on first-party documentation from BOTH sides.
  Neither apparatus is registered, so governance is the sole blocker -- and it is
  an unasked question rather than a refusal.
- **THE STRUCTURAL FINDING GENERALISES MISSION 1.46 ONE DOMAIN OVER.** There, the
  measurement of how many people live in Germany happens once, at Destatis, and
  Eurostat, the World Bank and FRED are three routes to it. Here, a platform's
  activity is measured once, by the platform, and every API, dump, mirror and
  dashboard is a distribution layer. **Two findings, one fact about where
  measurement actually occurs** -- and it is why acquiring more sources cannot
  produce corroboration for platform-mediated evidence.
- **10 HELD APPARATUSES, ONE SHARED SUBJECT, AND IT IS THE SAME ONE.** `docker`,
  observed by Wikimedia requests and by Stack Exchange questions, exactly as
  Mission 1.47 found. `COMPLEMENTARY_NOT_CORROBORATING`: a content request is
  what a reader's client makes of a server; a published question is what a person
  writes about being stuck. **ADR-036 removed the identity blocker that stopped
  those two ever reaching one Claim. It did not make a request a question.**
- **THE NEGATIVE CONTROLS WERE RE-RUN AND STILL FAIL**, which is the one way this
  mission could have gone wrong. The INFERRED layer fixes Claim IDENTITY; it
  repairs neither provenance dependence nor a 1 January stock measured against a
  midyear estimate. Neither World Bank pair was promoted.
- **THE DECISIVE EVIDENCE IS A CALIBRATION SCALE, NOT AN ORGANISATION CHART.**
  The selected pair reports on two DIFFERENT reference scales, and a republished
  series carries the originator's scale. Both sides say it first-party: one
  states it operates an independent sampling network rather than obtaining data
  from the other; the other describes that data as independent and uses it for
  comparison, **and comparison for validation is not consumption.**
- **PROVENANCE INDEPENDENCE IS NOT ERROR INDEPENDENCE.** The two share a site and
  one provides in-kind field support there, so a site-level artefact would move
  both. That is recorded as a limitation of the eventual Claim rather than folded
  into the independence verdict, and the scale offset becomes a constraint on
  where the threshold may be placed: a bound close enough for a calibration
  difference to decide the comparison would manufacture a contradiction.
- **THE VALIDATOR CAUGHT THIS MISSION'S OWN RECORD.** The rejected web-traffic
  route was first written `KNOWN_INDEPENDENT` with no documentary basis, because
  the two systems really are separate. §15 requires the proof from both sides
  before that word may be used, so it became **UNKNOWN** -- which costs nothing,
  since that route fails for a better reason: each apparatus measures share
  WITHIN ITS OWN NETWORK, so **the frame sits inside the metric definition** and
  any proposition admitting both relocates source attribution into its predicate.
  Mission 1.47's finding, recurring, and now named as a trap.
- **NO VALUE WAS FETCHED, AND THAT IS LOAD-BEARING.** `PREREGISTERED` is defined
  against RETRIEVAL, so one measurement fetched during feasibility work would
  have made an honest preregistration impossible for ever afterwards.
- **THE RESERVATION IS STATED RATHER THAN BURIED.** The selected construct is not
  a quantity this product will research. Relevance is a preference in the brief
  and not a gate, so selection is permitted -- and what the route can establish is
  that the aggregation mechanism WORKS on real independent data, not what its
  parameters should be for a request count. **Inside this portfolio there is no
  alternative, and that is the finding rather than a gap in the search.**

**The next mission is governance, not acquisition and not a threshold.**
Registering a bound against a source nobody has reviewed would freeze a contract
for an acquisition that may never be permitted. **Mission 1.58 was not
started.**


**SUPERSEDED IN 1.92 (Mission 1.58). The operator withdrew the selected route
and made product relevance a GATE, and the broadened search changed the answer.**

    withdrawn   ROUTE-A, because it does not serve the product
    added       gate 16 PRODUCT_RELEVANCE, mandatory
    surveyed    7 apparatus classes
    surviving   1, and no route in it qualifies yet

- **A WITHDRAWN SELECTION IS APPENDED TO, NEVER EDITED AWAY.** The 1.57 record
  still reads `selected_route: ROUTE-A` with the withdrawal beside it, because
  deleting the field would lose what the operator decided AGAINST. **And a rule
  change is not a correction**: the 1.57 reasoning was sound under the rule it
  was given, and it flagged this exact reservation before asking for approval.
- **THE SURVIVING CLASS IS INTERNET-WIDE ACTIVE SCANNING, AND ITS INDEPENDENCE
  IS STRUCTURAL.** Population figures have an upstream producer, so everyone else
  distributes. **Host counts have none, because nobody publishes how many hosts
  run a service** -- each apparatus must generate the number by probing. The
  failure mode that killed every earlier candidate is structurally unavailable
  here, and that argument survives one party changing its sourcing policy.
- **THE LAW IS REFINED RATHER THAN REFUTED.** A quantity is independently
  measurable exactly when NO party is in a position to publish it
  authoritatively. The internet as a whole is such a quantity, even though every
  host on it belongs to somebody.
- **A NEW TRAP, FOUND BY CERTIFICATE TRANSPARENCY:**
  `READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT`. Several independent log
  operators carrying one submitted certificate are many copies, not many
  witnesses. Its test is the sharpest this arc has: **if the two apparatuses
  disagree, is that a fact about the world or a bug?**
- **NO ROUTE WAS SELECTED.** Twelve of sixteen gates pass, the set is
  conjunctive, and the operator asking for a broadened search is not a reason to
  lower the bar. Three gates are open, each with a named way to close it -- and
  gate 10 reads PARTIAL because **an absence of a reference to third-party data
  is an absence rather than a statement**, which is 1.57's own correction applied
  rather than forgotten.

**The next mission is epistemics before governance**, inverting 1.57's
recommendation: gate 5 decides whether the two apparatuses measure one
proposition at all, and buying a licence first would be paying to discover a
semantic problem. **Mission 1.59 was not started.**


**ANSWERED IN 1.93 (Mission 1.59). Gate 5 decided it, and it decided against the
pair rather than against the class.**

    apparatus B   a stream of observations, each carrying a documented scan_date
    apparatus A   a maintained current state, searchable by LAST-CHANGE time
    the same window filter selects two different populations

- **THE DECIDING EVIDENCE IS THE VENDOR'S OWN WORKED EXAMPLE.** A host observed
  every day for five days WITHOUT CHANGE carries a searchable last-updated
  timestamp from five days ago, and the per-service observation time is
  documented as unsearchable. So a host present and unchanged throughout a window
  is in one side's set and missing from the other's, **and a contradiction
  produced that way would be an artefact recorded as a finding.**
- **FAIL RATHER THAN UNKNOWN.** The cadence document Mission 1.58 could not
  retrieve was pursued and answered. This is an established mismatch on
  first-party documentation from both sides, not a document nobody found.
- **ALL FOUR ALIGNMENT RULES REFUSED**, including the two that would have
  salvaged the route. A tolerance needs an operational basis and the merged side
  publishes no staleness bound; snapshot-inside-interval needs per-host timelines,
  which means retrieving the set and inspecting it afterwards.
- **THREE GATES REOPENED, AND THAT IS THE AUDIT WORKING.** Population, on a
  disclosure that under high density one side's service data is a **sampling**
  rather than a census. Reliability reviewability, because the narrowed metric
  turns on a wire-level decision one side keeps proprietary. And threshold
  freezability, as a consequence of gate 5.
- **A PROTOCOL-NATIVE CONSTRUCT SURVIVES, WRITTEN SOURCE-FREE.** Hosts answering
  with an identification string beginning `SSH-` before any negotiation, fixed by
  RFC 4253 §4.2. No vendor taxonomy — and **matching vendor labels are refused as
  metric equivalence**, because two vendors may both say PRODUCT-X on different
  signatures. The narrowing also removes a shared upstream nobody had noticed: a
  version- or vulnerability-flavoured metric would have pulled one CVE database
  into the load-bearing path on both sides.
- **A NEW APPARATUS REQUIREMENT: `OBSERVATION_ADDRESSABLE_EXPOSURE`.** An
  apparatus qualifies only if a future observation can be attributed to a defined
  window from its published surface, before any value is retrieved. **That is not
  the same as scanning often**, and Mission 1.58 could not have known to ask.
- **THE GENERALISABLE DIAGNOSTIC.** A dataset can be excellent and still be the
  wrong TEMPORAL OBJECT. A maintained current-state view answers what is running
  now; a preregistered threshold proposition asks what was observed during a
  window. Both are good products and only one can witness this Claim.

**Next is a pair-selection mission that applies the new requirement BEFORE
choosing, not after.** Do not pay for governance or access on a dropped pair, and
do not abandon the class. **Mission 1.60 was not started.**


**ANSWERED IN 1.94 (Mission 1.60). Applying the gates before choosing worked,
and it moved the blocker somewhere new.**

    A2 observation-addressable   PASS on two independent mechanisms
    A3 protocol-native exposure  PASS, RAW_IDENTIFICATION_STRING
    A7 affirmative lineage       PARTIAL
    A8 reliability reviewable    PARTIAL

- **THE ANCHOR PASSES BOTH GATES THAT KILLED THE LAST TWO PAIRS.** Its window is
  chosen in the REQUEST -- a dated index parameter, plus date ranges over a
  per-record `scan_date` that documents when the scanning which generated the
  response occurred. Its predicate is expressible against a queryable raw banner
  rather than a vendor service label.
- **THE BLOCKERS CHANGED KIND.** They are no longer about what the apparatus
  measures or how it exposes it. A7 is a sentence its documentation does not
  contain; A8 is a set of operational questions nobody has asked. Both close by
  reading or asking, not by finding a different scanner.
- **AND A7 STAYED PARTIAL FOR THE FOURTH MISSION RUNNING.** The documentation is
  not silent about its own scanning; it is silent about EXHAUSTIVENESS, and
  inferring exhaustiveness from a list of enrichment sources would be reading a
  positive claim out of a negative space. It is the most tempting refusal to
  abandon now that everything else about this apparatus works.
- **NO PARTNER REACHED PAIR ANALYSIS, AND THE REASON IS DOCUMENTATION ACCESS.**
  Three candidates all failed at A6 -- their first-party documentation was not
  retrievable at the paths tried. That is a fact about this mission's reach, and
  the record says what the search does NOT establish: that no partner exists.
- **THE OUTCOME FITS IMPERFECTLY AND THE RECORD SAYS SO**, rather than choosing
  the label whose wording bends most easily. One alternative would assert the
  anchor qualifies; the other would call an unproven negative a refutation.
- **THE REQUIREMENT REGISTRY IS THE REUSABLE OUTPUT.** Nine rules from Missions
  1.47 to 1.59 now sit in one record with the mission that paid for each. **Every
  one was learned AFTER a pair had been chosen**, which is why they are now
  applied before.
- **TWO SMALL RULES WERE MADE STRUCTURAL.** A query returning only a count still
  returns a measurement value. And a zero-cost trial destroys preregistration
  exactly as a paid one would, because access cost is irrelevant to epistemic
  contamination.
- **A FALSIFIABILITY TRAP WAS CAUGHT BEFORE IT MATTERED.** A windowed count makes
  host membership existential within the window, which looks monotone. The CLAIM
  is a count against a bound, which a lower count contradicts. Host-level
  monotonicity is not Claim-level monotonicity.

**Next is lineage confirmation and documentation retrieval, not acquisition.**
Both blockers are documentation problems and neither needs a new apparatus class.
**Mission 1.61 was not started.**


**ANSWERED IN 1.95 (Mission 1.61). One blocker closed by reading. The other is
what asking is for.**

    A7 affirmative lineage       PASS at LEVEL 2   (was PARTIAL)
    A8 reliability reviewable    PARTIAL, 4 answered / 4 partial / 3 not
    vantage                      NOT_DOCUMENTED    (was NOT_ESTABLISHED)
    port 22 window               NOT_ESTABLISHED, current inclusion ESTABLISHED
    partner documentation        3 of 3 recovered, 0 qualified

- **THE STANDARD WAS NOT LOWERED TO CLOSE A7.** The apparatus states first-party
  that every record is obtained and indexed by itself, then names **the only
  exceptions** as threat intelligence and geolocation from partners. A closed
  list is what makes the claim checkable, and each exception was checked against
  the load-bearing predicate one by one before the gate was allowed to pass.
- **THE CONTRAST ARRIVED IN THE SAME MISSION.** A partner candidate says its data
  comes from scans, sinkholes, sensors, sandboxes, blocklists **and many other
  sources**. That is affirmative, confident, and LEVEL 1: a list that does not
  end cannot be checked against anything.
- **LINEAGE EXHAUSTIVENESS IS NOT FRAME EXHAUSTIVENESS.** That every record was
  self-collected says nothing about which addresses were reached. A7 asks who
  produced the observation; A5 asks which addresses were probed. The strongest
  lineage clause in this arc sits beside a frame whose sampling is undocumented.
- **A BOUND WAS FOUND ON A GATE A PREVIOUS MISSION PASSED.** The default search
  surface is a maintained current-state view -- the temporal object Mission 1.59
  rejected. A2 still passes, on the dated index mechanism, which is not the
  default. A collector using the default would read the rejected object while a
  record elsewhere said the gate had passed.
- **PORT 22 GIVES TWO ANSWERS.** It is on the current list, and the list as of
  any past date is not reconstructable, because the changelog dates the SIZE of
  the port list and never its MEMBERSHIP. No removal is recorded, which is
  evidence about direction and not a guarantee.
- **THE PARTNER WALL WAS THE PATH, NOT THE APPARATUS.** All three candidates have
  working first-party documentation now, each earlier failure with a named cause.
  **None is qualified, ranked or selected**, and the record names the preference
  it declined to express rather than leaving it for a reader to detect.
- **THE ENQUIRY IS DRAFTED AND NOT SENT**, hashed, with the hash recorded
  elsewhere so the document it names is not the document it changes. It asks
  nothing the documentation already answers, and no recipient address was
  invented.

**Next is operational closure and partner package completion, not acquisition and
not pair selection.** One gate blocks the anchor and one written enquiry answers
it; fourteen of eighteen partner B-slots are unread. **Mission 1.62 was not
started.**


**ANSWERED IN 1.96 (Mission 1.62). Three complete packages, three different
failures, and no apparatus qualifies.**

    LeakIX        PACKAGE_COMPLETE  INDIVIDUALLY_NOT_QUALIFIED   B2 last-seen timestamps
    ONYPHE        PACKAGE_COMPLETE  INDIVIDUALLY_UNRESOLVED      4 partial slots
    Shadowserver  PACKAGE_COMPLETE  INDIVIDUALLY_NOT_QUALIFIED   B4 per-requester frame
    anchor        A7 PASS           A8 PARTIAL                   blocks ["A8"]

- **COMPLETE IS NOT QUALIFIED, AND TWO COMPLETE PACKAGES CONCLUDING NOT_QUALIFIED
  IS THE MISSION SUCCEEDING.** Mission 1.60's three candidates all failed at
  documentation retrieval, which said nothing about them. Failing at three
  different gates says something about each.
- **THE RETRIEVABLE FRAME IS NOT THE MEASURED FRAME.** One candidate scans the
  whole internet daily and its API states that a requester only gets data on the
  networks they are responsible for. It scans everything and can show us only
  ours, so two requesters retrieve two different populations.
- **B2 HAS NOW DECIDED THREE APPARATUSES ACROSS 1.59, 1.60 AND 1.62**, and for
  the same reason each time: a maintained current-state view is a good product
  and the wrong temporal object. A passing raw-banner slot does not offset it.
- **AN AMBIGUITY WAS NOT RESOLVED FAVOURABLY.** The surviving candidate's
  timestamp is documented both as a collection moment and as tracking when a
  service was last observed. Those are two different temporal objects, and
  choosing the reading that keeps a candidate alive is the refusal this arc has
  made four times.
- **ONE ANSWER WAS DOWNGRADED AND ONE WAS RECLASSIFIED.** FRAME went ANSWERED to
  PARTIAL once eligible and attempted frame were separated. RETRY went PARTIAL to
  UNKNOWN once the API's retry parameters were seen to govern the client retrying
  the API rather than the scanner retrying a probe.
- **THE COUNT ENDPOINT IS AN ESTIMATE ABOVE A THOUSAND RESULTS.** A threshold
  evaluated against it would compare a bound against an error band that could
  decide the direction, which is an artefact recorded as a finding. It bounds how
  the value must be obtained, not whether it can be.
- **THE FROZEN ENQUIRY WAS NOT EDITED AND NO DUPLICATE HASH WAS MANUFACTURED.**
  All seven questions are still unresolved, so v1 remains current on Mission
  1.61's exact hash.

**Next is the operator's decision on the enquiry, plus four precisely named
documentation reads.** Pairing needs two qualified apparatuses and there are
none, so §62's checkpoint governs and A8 was not weakened to get past it.
**Mission 1.63 was not started.**

### A refusal is not a derivation of a Claim, and gets its own record

Added in 1.87 (Mission 1.53, **ADR-038**,
`refusal-derivation-binding-design-v1.md`, `mission-1.53-report.md`).
**`INPUT_KEYED_REFUSAL_PROVENANCE_MODEL_SELECTED`**, and **no migration was
created**.

    directional   why does Signal S support or contradict existing revision R?
                  -> research.claim_derivations, bound to a revision that EXISTS
    refusal       why was Signal S NOT attached to candidate proposition P?
                  -> its own record, bound to a proposition that does NOT exist

- **THE TWO ARE NOT THE SAME PERSISTENT ENTITY**, and the fact that both come out
  of one function call is not a reason to store them in one table. The subject of
  the first is a ClaimRevision; the subject of the second is a proposition that
  never became one.
- **OPTION B WAS MEASURED, NOT DISMISSED, AND IT FAILS ON A LIVE FACT.** A temp
  table mirroring `claim_derivations_identity_key` accepted **three identical
  rows** with a NULL `claim_revision_id`, and refused the duplicate the moment
  the column was populated. PostgreSQL treats NULLs as distinct, so **making that
  column nullable silently removes the table's only idempotency guarantee from
  exactly the rows the change exists to add.** Its second failure is quieter:
  `claim_derivations` identifies its proposition **only through**
  `claim_revision_id`, so with that NULL the row cannot say what was refused.
  Repairing both means adding a key, a preimage, a reason code, a second partial
  unique index and three conditional CHECKs -- **Option A inside a table whose
  name says otherwise.** The choice is not one table against two; it is one
  honest table against one table meaning two things with two identity keys.
- **MIGRATION 0034 HAD ALREADY ANTICIPATED REFUSALS.** Its threshold-required
  CHECK makes the registration optional *precisely* for `NOT_APPLICABLE` and
  `UNKNOWN`, and its result CHECK admits all four values. **Two constraints
  written in one migration that disagree with each other** -- which is the
  finding rather than a tie-breaker for the table that holds them.
- **THE CANDIDATE TARGET IS A KEY PLUS ITS EXACT PREIMAGE, IN A VOCABULARY THAT
  ALREADY EXISTS.** All **43** live Claims carry both `proposition_key` and
  `proposition_facts`; the discriminator key is **`proposition`** on all 43, and
  the evaluator already emits it. So a refusal and the Claim it may later become
  are **comparable by key**, which is what makes the UNKNOWN-then-SUPPORTS
  transition traceable at all -- and it was checked, because a descriptor keyed
  on `proposition_kind` would have silently broken it. The key **recomputes** from
  the facts, so it is verifiable rather than trusted.
- **A HASH ALONE WOULD NOT DO**, because unlike a Claim there is no row elsewhere
  to recover the facts from. **A candidate-proposition registry is Claims before
  Claims.** And **the threshold registration cannot identify the target**, on a
  measured fact: three of the seven live reason codes refuse at gate 1, before
  the registration is consulted, so it fails exactly on the commonest refusals.
- **THE SEVEN REASON CODES WERE READ FROM THE EVALUATOR'S OWN `_refuse` CALLS**,
  via the AST rather than a capitals scan, because `__all__` entries are shaped
  identically. **0 invented, 0 renamed.** Result answers WHAT and drives the
  contract; reason code answers WHY and drives the audit; rationale is the
  authority for nothing.
- **THE EQUIVALENCE BASIS IS `NOT NULL` ON A MEASURED CONTRACT FACT** -- the
  decision constructor refuses a blank basis id for EVERY verdict including
  `UNKNOWN` -- so no fake identifier is invented and the identity key stays
  **free of nullable columns**, which the probe above proved is not automatic.
  **And the bound is stated**: the evaluator only refuses pairs somebody already
  reviewed, so the store answers *what did we try and decline* and never *what
  did we never consider*.
- **A CHANGED BASIS IS A NEW HISTORICAL ROW**, decided explicitly with its cost
  stated, because the basis is an input to gate 1 and changing it changes what was
  evaluated. **A later SUPPORTS leaves an earlier UNKNOWN entirely alone**: no
  supersession column, because each row names its rule version and basis, so
  *which reasoning stood when* is answerable without one.
- **THE TRIGGER NEEDS NO EXEMPTION**, which is the decisive practical advantage:
  no Claim is created, so nothing has to be added to `HYPOTHESIS, MANUAL,
  WITHDRAWN`. Every alternative design ends at a request to exempt `INFERRED`.
- **`research.claim_derivations` KEEPS ONE CLEAN MEANING**: every row names a real
  ClaimRevision. The invariant is preserved rather than weakened.
- **ONE DEVIATION FROM THE BRIEF IS FLAGGED RATHER THAN BURIED.** The descriptor
  carries no schema version, because `derivation_rule_version` already pins which
  fact set was emitted -- `target_proposition_facts()` lives in the rule module --
  and a second version field would be a second authority for one fact. Recorded as
  **`OPERATOR_REVIEWABLE_DEVIATION`** with its cost if the reasoning is wrong.
- **TWO TESTING TRAPS WERE CAUGHT BEFORE THEY MATTERED.** The evidence-requirement
  trigger is `DEFERRABLE INITIALLY DEFERRED`, so a rollback fixture never fires it
  and the first version of that test **reported a pass for a rule that never ran**;
  `SET CONSTRAINTS ALL IMMEDIATE` is what makes it a test, and it matters more for
  the HYPOTHESIS control, which would otherwise pass vacuously. And the new pytest
  classes were first named without a `Test` prefix, which **collected zero tests
  silently** -- renaming took collection from 0 to 15.
- **A PROBE THAT REFUSED FOR THE WRONG REASON WAS REPORTED RATHER THAN KEPT.** The
  first INFERRED-claim attempt used an `origin` value the CHECK does not admit, so
  it was refused by the wrong constraint **while looking exactly like the result I
  wanted**. Fixed, and a HYPOTHESIS control added so the refusal is attributable to
  the exemption list rather than to anything incidental.

**Mission 1.54 -- Refusal Provenance Schema V1** implements only the frozen
contract: one additive table, its constraints, its identity key and its RLS, with
a real DELETE fixture proving a refusal survives interpretation-run expiry, and a
workspace deletion proving it does not hit the deferred-constraint trap migration
0034 found by running it. **Mission 1.54 was not started.**


**COMPLETED IN 1.88 (Mission 1.54).** Migration 0035 created
`research.proposition_evaluation_refusals`, and the design's three load-bearing
properties are now DELETEs rather than arguments.

    interpretation run DELETED   inputs 1 -> 0, refusal SURVIVED
    Signal DELETED alone         ForeignKeyViolation
    whole workspace DELETED      committed, refusal gone with its tenant

- **Every identity member is NOT NULL**, so no sentinel and no expression index
  were needed. The equivalence basis could be `NOT NULL` because the decision
  constructor refuses a blank basis id for every verdict.
- **One stricter check was rejected on a measurement.** Requiring every fact
  value to be a string would have made the table unable to hold a refusal about
  the procurement family: **37 of 43** live Claims would have passed. That also
  corrects this design's own claim that values are flat strings on every live
  Claim.
- **One check IS stricter than `research.claims`**: the descriptor must carry the
  `proposition` discriminator, because a refusal's facts are the only record of
  what was refused.
- **The trigger needed no exemption**, as predicted, and `claim_derivations` kept
  its NOT NULL and its identity key untouched.

### The reasoning needs somewhere durable, and the run log expires

Added in 1.84 (Mission 1.50, **ADR-037**,
`deterministic-inferred-claim-contract-v1.md`, `mission-1.50-report.md`).
**`DETERMINISTIC_INFERRED_CLAIM_CONTRACT_READY`**, schema necessity
**`BOTH_REQUIRED`**, and **no migration created**.

    Q1 derivation provenance  a new structured record   Q2 Evidence  attaches directly
    Q3 evaluator              a new package, NOT built  Q4 threshold  its own registration

- **THE CLAIM AND THE EVIDENCE NEED NOTHING NEW. THE REASONING HAS NOWHERE
  DURABLE TO LIVE.** `research.claims` already carries what an INFERRED Claim
  needs and `scoring.evidence` already carries the attachment. What is missing is
  a place for *why*.
- **THE SCHEMA VERDICT RESTS ON A MEASURED FACT.**
  `research.claim_interpretation_inputs` is the closest existing structure -- one
  row per (run, signal) with role, claim_id and reason_code, 64 rows live -- and
  it cannot be the canonical authority because **all 12 rows of its parent
  `claim_interpretation_runs` carry a populated `expires_at` about ninety days
  out, and the inputs foreign key is `ON DELETE CASCADE`.** When a run expires
  every input row goes with it, so **a Claim would outlive the record of how it
  was derived.** A retention-bounded execution log is the right shape for *what
  did this run consider and refuse* and the wrong shape for *why is this Claim
  true*. `proposition_facts` was rejected too: it is the preimage of the KEY, so
  derivation facts placed there would become identity.
- **`origin_detail` KEEPS ONE RESPONSIBILITY.** It answers *where did this Claim
  come from*, on all 43 live Claims, with sentences like *"Restated from signal
  `<id>`"*. A reasoning step answers a different question, and putting both there
  is the Mission 1.15.4 shape: one free-text field, two independent questions,
  and no reader able to tell which one a sentence answers.
- **EVIDENCE ATTACHES DIRECTLY, ON EXISTING INTENT RATHER THAN A FRESH
  JUDGEMENT.** `claim-epistemic-semantics-v1.md` §4 already says an INFERRED
  claim carries *"the Signals it reasoned from, as Evidence"*. No Claim-to-Claim
  relation: the aggregator consumes Evidence and not relations, so a relation
  would need proxy Evidence anyway. **Attachment and provenance are both required
  and neither substitutes**: Evidence says WHICH observation bears and in which
  direction, the derivation record says HOW that was determined.
- **ONE RULE, MANY EVALUATIONS, BOUND TO THE REVISION.** One prose rationale
  cannot explain both why A supports and why C contradicts. Binding to the Claim
  rather than the revision would let a later derivation silently rewrite the
  reasoning behind an earlier one.
- **THE TWO IDEMPOTENCY KEYS DIFFER DELIBERATELY.** Evidence keys on
  `(workspace, claim, signal)`, because Mission 1.41 removed `extraction_method`
  so a version bump cannot INSERT a duplicate. A derivation record keys on
  `(workspace, claim_revision, signal, rule_version)` and **must** be distinct per
  rule version, because replaying a different rule is different reasoning about
  the same relation.
- **THRESHOLD PROVENANCE IS NOT PROPOSITION IDENTITY.** `M >= 100` preregistered
  and `M >= 100` post-hoc are ONE proposition with one falsifier; what differs is
  calibration eligibility. Making provenance identity would fork one proposition
  into several. **And provenance never changes entailment** -- a post-hoc bound
  with a measurement of 110 genuinely supports the Claim. Hindsight costs
  eligibility, not truth.
- **PREREGISTERED IS DEFINED AGAINST RETRIEVAL, NOT PUBLICATION.**
  `recorded_at < observation.retrieved_at`, because the bias guarded against is
  the ANALYST'S and an analyst can only be influenced by data that reached them:
  a figure public for years before this system retrieved it was not known to
  whoever froze the bound. Not commit time either. **And the limit is stated
  rather than hidden** -- the relation is necessary, machine-checkable, and NOT
  sufficient to exclude human foreknowledge, so `PREREGISTERED` means *this system
  did not hold the measurement*, never *nobody knew*.
- **`interpretation_confidence` IS NOT A GAP, AND THE ANSWER IS NOT THE OBVIOUS
  ONE.** Its column comment says *"Confidence that THIS WORDING faithfully states
  what the cited Signals showed"*, and `build_claim` refuses an automated claim
  without it. For an OBSERVED restatement, reading the facts IS the whole job,
  which is why the interpreters set `1.0`. A deterministic INFERRED threshold
  Claim has **one step the OBSERVED case lacks** -- asserting that the
  source-native measurement measures the Claim's quantity under its definition and
  unit. So the field means **confidence in the semantic-equivalence mapping, not
  in the arithmetic**, and setting `1.0` automatically would assert certainty
  about a real judgement.
- **NO `derivation_confidence` FIELD, AND THERE MUST NOT BE ONE.** `110 >= 100`
  is exact. A confidence on it would be a number nobody fitted, invented because a
  numeric column exists elsewhere.
- **A REFUSAL IS RECORDED RATHER THAN INVISIBLE.** `NOT_APPLICABLE` and `UNKNOWN`
  produce a derivation record and NO Evidence row -- the shape ADR-021 and ADR-025
  already use. **UNKNOWN never becomes NEUTRAL**: NEUTRAL asserts that an
  observation bears on the Claim without bearing either way, which is a positive
  finding, while UNKNOWN says we could not establish that it bears at all.
- **THE EVALUATOR GOES IN A NEW PACKAGE THAT WAS NOT CREATED.** Hosting it in the
  interpreters would require weakening `validate_claims.py`, and **a guard removed
  to let new work through is a guard that never was**. Allowed dependencies are
  contracts, claim-model and signal-model -- all already in the bare-python runner;
  forbidden are `sros_acquisition`, because a component able to read the source
  registry could decide its own authorization, and the Gateway, because a package
  that cannot import a provider cannot call one by accident. §38 forbids creating
  production code merely to host tests, so the contract tests live in `claim-model`
  and `evidence-aggregation`.

**Mission 1.51 -- Deterministic Derivation Provenance Schema V1** implements only
the frozen schema: the two additive tables, their constraints and their
idempotency keys. Not the evaluator, because it would have nowhere to write.
**Mission 1.51 was not started.**

**COMPLETED IN 1.85 (Mission 1.51) AND 1.86 (Mission 1.52), and the second half
found what the first half could not have.** Migration 0034 created both tables.
The evaluator was then built against them and immediately hit a wall the schema
could only reveal once something tried to use it.

    INFERRED claim with no Evidence      REFUSED  23514, require_evidence_for_generated_claim
    derivation with NULL revision id     REFUSED  migration 0034's NOT NULL
    -> a refusal has nowhere to live

- **`REFUSAL_DERIVATION_BINDING_CONTRACT_GAP`.** ADR-037 says a `NOT_APPLICABLE`
  or `UNKNOWN` evaluation produces a derivation record and no Evidence row. The
  schema built to hold it cannot express the first half without the second: a
  derivation must name a revision, a revision requires a Claim, and a generated
  INFERRED Claim requires Evidence. **Both refusals are individually correct**
  -- the exemption list is what stops a machine storing an assertion nothing
  supports, and the NOT NULL is what stops a later derivation rewriting the
  reasoning behind an earlier one -- **and jointly they leave a refusal
  unrecordable.**
- **NOTHING WAS WIDENED TO GET PAST IT.** `INFERRED` was not added to the
  trigger's exemptions, `claim_revision_id` was not made nullable, no Claim was
  created to host a refusal, and no third table was invented. Each is a schema
  decision with an ADR behind it, and a Claim asserting a proposition the
  evaluator just declined to establish is a fabrication with provenance attached.
- **THE EVIDENCE RE-EVALUATION QUESTION RESOLVES BY POLICY, AND THE DIFFERENCE IS
  WHY IT IS NOT THE HEADLINE.** `scoring.evidence` has **no** revision,
  supersession or `is_current` column -- measured, not recalled. So **policy D**:
  a rule-version change produces ANOTHER derivation record and may never
  automatically alter canonical Evidence; a disagreement is REPORTED for operator
  review and nothing is written. That needs no schema change, because
  `claim_derivations` is already append-only per rule version. **The refusal gap
  needs a decision nobody has taken**, so reporting the resolvable one as the
  outcome would misattribute the blocker to a layer that is not blocking.
- **THE EVALUATOR ITSELF IS BUILT AND PROVEN**, at the path Q3 named, joining the
  zero-dependency runner with **one named shared package rather than the
  monorepo** -- Mission 1.47 made that rule load-bearing. Four gates run in order
  with **equivalence first**, so the direction the arithmetic WOULD have produced
  cannot leak into a refusal; no unit is converted, no window aligned, and
  `evaluate` takes exactly one registration and never searches, so *whichever
  bound makes the Claim work* is not expressible.
- **THE AGGREGATOR NEEDS NOTHING, PROVED FROM ITS SIGNATURE.** `aggregate()`
  takes no claim type and `EvidenceItem` carries none, so there is no parameter
  through which INFERRED Evidence could be treated differently.
- **AND A CORRECTION WAS MADE RATHER THAN ASSUMED AWAY.** `EvidenceDirection`
  DOES have a `NEUTRAL` member. So the guarantee that a refusal never becomes
  NEUTRAL is **producer-side, not type-side**: `EvaluationResult` has no NEUTRAL
  and a refusal carries no `EvidenceDecision`, so the evaluator has nothing to
  hand over. A NEUTRAL row would be counted and weightless -- invisible in the
  numbers and visible in the counts.

**The next mission is Refusal Derivation Binding Design V1**, and it is a
semantics question with an ADR behind it, never an edit to a trigger or a
nullability change made in passing. Three options are identified and none is
chosen; the preference on current evidence is a refusal record keyed on the
INPUTS in its own table, because it needs no exemption and no change to the
binding, so both of Mission 1.51's guards stay exactly as strong as they are.
**Do not run the evaluator over canonical rows first**: it would produce
directional results and silently drop every refusal, which is the failure the
derivation record exists to prevent. **Mission 1.53 was not started.**

### A proposition about the world is an INFERRED Claim, and INFERRED is not a model

Added in 1.83 (Mission 1.49, **ADR-036**,
`source-independent-claim-semantics-v1.md`, `mission-1.49-report.md`).
**`SOURCE_INDEPENDENT_PROPOSITIONS_BELONG_TO_INFERRED_LAYER`**, with
`INFERRED_IS_SEMANTICALLY_CORRECT` as the naming verdict.

    Layer 1  "Source A reported 110."  "Source B reported 90."   source_id IS identity
                            |  deterministic evaluation
    Layer 2  "M >= 100 at T."          A SUPPORTS · B CONTRADICTS  source_id is WITNESS

- **THE ANSWER WAS ALREADY WRITTEN DOWN, SEVERAL MISSIONS EARLY.**
  `claim-epistemic-semantics-v1.md` §4 defines `INFERRED` as a claim that
  *"asserts something about the world that the measurement is evidence for, and
  that the source did not itself report."* That is the source-independent
  proposition, verbatim. **No new `ClaimType`, no subtype, no migration.**
- **`INFERRED` DOES NOT MEAN MODEL-GENERATED, AND THE TAXONOMY SAYS SO TWICE.**
  By TYPE: `INFERRED` is *derived analytically*, while **`PREDICTED`** is *a
  model-generated estimate*. By AXIS: `claim_type` is the epistemic category and
  `interpretation_kind` is the procedure, and **migration 0016's CHECK constraint
  ties `interpretation_kind` to the presence of a `model_version`, not to
  `claim_type`** -- orthogonal in SQL rather than in prose. The semantics
  document states it outright: *"A deterministic extractor can produce an
  INFERRED-type claim, and an LLM can produce an OBSERVED-type one."* So
  **`INFERRED` + `DETERMINISTIC` is representable today**, and has never been
  written.
- **A CROSS-SOURCE OBSERVED CLAIM IS REFUTED BY THE PROJECT'S OWN SENTENCE**:
  *"An OBSERVED claim that should have been INFERRED is a fabrication with a
  citation attached."* It would assert what no single source observed while
  carrying every source's citation -- **worse than an honest inference rather
  than milder**, because the citations make it look directly supported.
- **A NEW CLAIM TYPE IS UNNECESSARY RATHER THAN WRONG.** The
  deterministic-versus-model distinction is what `interpretation_kind` already
  carries. A sixth member would put one distinction in two places, and **two
  fields answering one question eventually disagree**.
- **"LEAVE IT UNIMPLEMENTED" IS NOT THE CONSERVATIVE OPTION.** It was evaluated
  seriously and rejected because the layer is already defined in the ontology,
  the generated contract and the semantics document -- so absence does not
  decline to build something, it leaves a defined capability unbuilt. Its cost is
  stated rather than hidden: the system stays unable to say two sources disagree,
  **the one signal that tells an operator to go and look.**
- **THREE EXCLUSIONS CARRY THE NEW IDENTITY.** The **measurement value is not
  identity** -- if it were, 110 from A and 105 from B would be two Claims, which
  is Mission 1.48's failure reproduced one layer up. **`source_id` is not
  identity here and remains identity for OBSERVED**, which is the entire two-layer
  distinction. **Direction is not identity**, the exact inversion of the OBSERVED
  layer -- and that inversion is why the same measurement stream that cannot
  contradict at Layer 1 can at Layer 2.
- **SOURCE INDEPENDENCE OF THE PROPOSITION IS NEVER PROVENANCE LOSS.** Every
  witness keeps `source_id` and the full chain to RawRecord. A Claim may read
  *"M >= 100"*, and inspection must still show which source supported and which
  contradicted it.
- **RELIABILITY IS UNAFFECTED, AND THE REASON RESOLVES THE APPARENT CONFLICT.**
  Claim IDENTITY and Evidence reliability SCOPE are different things: the
  proposition is source-independent, the Evidence is still one source's
  measurement, and *how dependably does THIS source support THIS kind of
  proposition* stays source-relative. A new `proposition_kind` with
  `claim_type = INFERRED` is a NEW scope, so **nothing is inherited by
  proposition similarity**.
- **MEASUREMENT RELIABILITY AND DERIVATION VALIDITY MUST NEVER BE MULTIPLIED.**
  Whether 110 is dependable is a human judgement against documentary basis;
  whether 110 entails `>= 100` is exact. No coefficient combines them, and
  inventing one would let a sound derivation look doubtful because its input is
  uncertain -- which uncertainty mass already represents correctly.
- **A THRESHOLD MUST BE PREREGISTERED TO BE CALIBRATION-ELIGIBLE.**
  `PREREGISTERED`, `SOURCE_NATIVE` and `EXTERNAL_NORM` qualify; `POST_HOC` and
  `UNKNOWN` do not. A post-hoc threshold may still produce a Claim -- the
  proposition is not false because its bound was chosen late -- but **a threshold
  picked to make a case work measures the analyst**. `UNKNOWN` is ineligible
  rather than assumed preregistered: uncertainty is never permission.
- **THE FIXTURES RAN THROUGH THE REAL AGGREGATOR.** Two independent supports:
  **2 groups, strength 0.8** against a strongest member of 0.6 -- the first shape
  in this repository that would differ from B-2. A support and a contradiction on
  **ONE** Claim: contradiction 0.5, masses 0.3 / 0.2 / 0.3 / 0.2 summing to 1.0.
  A republication: **one group at 0.6**, so volume rises and strength does not.
  A semantic mismatch and a post-hoc threshold never reach the aggregator at all,
  and the tests say so rather than pretending to execute them.
- **`validate_claims.py` WAS LEFT UNTOUCHED**, and the evaluator therefore belongs
  OUTSIDE the interpretation package. That guard is what keeps the OBSERVED
  contract narrow, and **a guard removed to let new work through is a guard that
  never was.**
- **PURELY ADDITIVE.** 43 Claims, 44 revisions and 57 Evidence keep their
  proposition identities and their meaning, and become the INPUTS to the new
  layer. **0 identities rewritten, 0 migrations recommended.** `SourceBoundary`
  not widened, `proposition_key` not altered, no `ClaimType` member added, and no
  INFERRED Claim created.
- **CROSS-SOURCE OBSERVED CONVERGENCE IS NO LONGER NEEDED** for world-level
  propositions, so Mission 1.47's finding that the contract structurally refuses
  them becomes a **feature rather than a gap**: it is the mechanism keeping
  OBSERVED honest.

**The next mission is Mission 1.50 -- Deterministic Inferred Claim Contract V1**,
the minimum ADDITIVE implementation contract for OBSERVED inputs → deterministic
derivation → source-independent INFERRED Claim, with derivation provenance and no
model use. It must decide where the reasoning step lives -- `ClaimDraft.rationale`
exists and lands in `origin_detail`, which currently holds a PROVENANCE sentence
rather than a reasoning step, the Mission 1.15.4 shape of one field answering a
question that is two -- whether Evidence attaches directly or a derivation
relation is required, where the evaluator lives, and how a threshold's
preregistration status is recorded. **Mission 1.50 was not started.**

### One identity decision closes both roads out of the baseline

Added in 1.82 (Mission 1.48, `falsifiable-evidence-apparatus-requirements-v1.md`,
`falsifiability-vs-convergence-tradeoff-v1.json`,
`falsifiable-evidence-apparatus-gap-baseline-v1.json`, `mission-1.48-report.md`).
**`CONTRADICTION_CLAIM_IDENTITY_ARCHITECTURE_GAP`**: the contradiction machinery
works perfectly and no Claim this architecture can build is able to reach it.

    real aggregator, one SUPPORTS + one CONTRADICTS on one claim id
      support 0.6  contradiction 0.5  masses 0.3 / 0.2 / 0.3 / 0.2  = 1.0
    real aggregator over all 43 live Claims
      aggregator_differs_from_b2_cases  0     max support groups  1

- **THE MACHINERY IS NOT THE GAP, AND THAT WAS PROVED BEFORE ANYTHING ELSE.** A
  non-persisted fixture drives the real `aggregate()` to non-zero contradiction
  strength and non-zero conflict mass, with all four masses summing to one. It
  has simply never been reached: **all 57 live Evidence rows are `SUPPORTS`.**
- **NOTHING WAS QUOTED FROM A MISSION REPORT.** §0 forbade it, so the B-2
  identity was RE-DERIVED by running the real aggregator over all 43 Claims with
  reliability resolved through the real resolver, against a B-2 computed
  independently. Mission 1.43's algebra survived contact with its own data.
- **CONTRADICTION IS BLOCKED THREE TIMES, AND THE THIRD IS THE ONE THAT
  MATTERS.** `direction` is a proposition fact in all three implemented
  templates, so an increase and a decrease are two Claims.
  `EvidenceDirection.SUPPORTS` appears **exactly once** in the whole interpreters
  package as a hard-coded literal and `CONTRADICTS` appears nowhere, so no
  interpreter could emit the contradicting row even if identity permitted it.
  And **all 43 Claims carry `source_id` in proposition identity**, so two
  publishers reporting incompatible values form two Claims before their values
  are ever compared.
- **THE THIRD BLOCKER IS THE UNIFICATION WITH MISSION 1.47.** Corroboration
  needs two observations on ONE Claim; contradiction needs two observations on
  ONE Claim. **Source attribution in proposition identity forbids both, so one
  identity decision closes both roads out of the B-2 baseline.** Mission 1.47's
  `CONVERGENCE_CONTRACT_ARCHITECTURE_GAP` and this mission's finding are the
  same fact seen from two sides.
- **SO THE BINDING CONSTRAINT IS NOT A MISSING APPARATUS.** A new apparatus
  interprets to facts carrying its own `source_id`, produces its own
  `proposition_key`, and lands on its own Claim -- where it can neither join a
  support group nor contradict anything. **Acquiring one would add rows and
  change nothing**, which is why `BOTH_ROUTES_REQUIRE_NEW_MEASUREMENT_APPARATUS`
  is deliberately NOT the outcome: it would send the next mission looking for a
  candidate that could not be used.
- **THE CORPUS SUPPLIED ITS OWN DEMONSTRATION.** Three Claim pairs differ ONLY
  in `direction` -- the Wikimedia witnessed existentials for Docker, Kubernetes
  and Podman. The most contradiction-looking pair in the repository is not one
  for **three independent reasons**: they are two Claims, they are both TRUE at
  once, and a counterexample cannot falsify a monotone existential anyway.
- **THE TRADE-OFF IS NOW OBSERVED RATHER THAN HYPOTHESISED.** The proposition
  families easiest to make cross-apparatus are **monotone** and therefore
  unfalsifiable; the falsifiable families are exactly the ones only one
  apparatus supports. Seven families, eight qualitative criteria, **no weighted
  numeric score** -- §5 allows `STRONG | MEDIUM | WEAK | NOT_APPLICABLE |
  NOT_ESTABLISHED` and nothing else.
- **`THRESHOLD_STATE` IS PREFERRED, AND FOR A REASON THAT SERVES BOTH ROUTES.**
  An `EXACT_POINT_VALUE` claim is contradicted by a rounding difference, which
  manufactures false contradictions and makes independent corroboration nearly
  impossible -- two honest apparatuses rarely publish the identical number. A
  threshold lets both SUPPORT it while still admitting a real falsifier.
  **Its cost is recorded rather than discounted**: X is OURS rather than the
  source's, so it must be frozen BEFORE the second measurement is retrieved, or
  it is an arbitrary number wearing the costume of a rule.
- **`RELIABILITY_REVIEWABILITY` BECOMES A FIRST-CLASS SEARCH CRITERION.** Mission
  1.47 paid for learning it late: one robots-blocked methodology page left
  independence `UNKNOWN` **and** was the reason the operator declined both Stack
  Exchange reliability scopes. **A single inaccessible document disqualified an
  otherwise strong apparatus on two separate gates**, so documentation
  retrievability is checked BEFORE an apparatus is treated as a candidate.
- **NO SOURCE WAS SELECTED, AND THE SPECIFICATION NAMES NONE.** The apparatus
  requirements are written from the evidence requirement backwards and a
  validator refuses any source, vendor or product name inside them. The two
  registered candidates whose shape fits best are exactly the two Mission 1.46
  refuted on provenance; the third observes a different jurisdiction, which is
  complementary rather than corroborating.
- **A §23 TRAP WAS MET AND FIXED STRUCTURALLY.** The first draft of that
  no-named-source guard was a substring scan, and it refused this mission's own
  record on the word *documented* -- because `ted` is inside it. Repaired with
  token boundaries, the same fix Mission 1.13.1 made for `supermarket` and
  `market`. **A scan that fails on the prose doing the work is the recurring
  shape, and loosening it until it passes is how a structural check stops
  checking.**
- **§33 WAS HONOURED BEFORE COMMIT.** The zero-dependency runner was run with
  bare `python` -- 1124 tests across 8 packages -- and the claim-identity proof
  lives in `claim-model` because that package owns `proposition_key`. Mission
  1.47's CI failure made the package-boundary rule load-bearing and it was
  followed here rather than rediscovered.

**The next mission is NOT candidate discovery, even though this record freezes
the specification one would use.** No apparatus can exercise either route while
source attribution is proposition identity, so a discovery mission would end by
finding a good candidate that cannot be used. What is needed first is a **narrow
Claim-semantics and contradiction-reachability design mission**, deciding whether
a source-independent proposition belongs in the INFERRED layer, in a governed
cross-source OBSERVED convergence contract, or in neither -- as a semantics
question with an ADR behind it, never as an edit to a template. **The apparatus
specification is not wasted: it is the second half of the work, and it becomes
actionable the moment the first half is decided.** Mission 1.49 was not started.

### The proposition two apparatuses share is the one that discards what they measure

Added in 1.81 (Mission 1.47, `cross-apparatus-convergence-feasibility-v1.md`,
`cross-apparatus-holdings-baseline-v1.json`, `mission-1.47-report.md`).
**`FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK`**: a narrow source-faithful
proposition over Docker IS independently entailed by both held apparatuses, and
it is worth nothing.

    apparatuses  9 over 4 sources      cross-apparatus subjects  1 of 3 (docker)
    §26 gates    5 pass, 3 fail        selected route  NONE
    requests     0 of every kind       counters moved  0 of 15

- **AN APPARATUS IS `(source, proposition_kind)`, NOT A SOURCE.** Four sources
  operate **nine** apparatuses; `wikimedia-pageviews` and `ted-eu` each run two
  over one corpus. Using `proposition_kind` makes the apparatus inventory and the
  reliability-scope inventory the same partition, so **a new apparatus is a new
  reliability question by construction**. Counting sources would have reported
  four and merged two scopes the contract already holds apart.
- **THE OVERLAP WAS MEASURED BEFORE ANY PAIR WAS CHOSEN**, because a pair chosen
  first and justified afterwards is a rationalisation. Docker is the **only**
  cross-apparatus shared subject: Wikimedia 12 Evidence against Stack Exchange 2,
  with kubernetes 12/0 and podman 12/0. The reviewed registry had already
  recorded why the other two fail, in Mission 1.30 and not for this mission.
- **THE ONE CANDIDATE THAT PASSES SEMANTICS PASSES BY BEING WEAK.** *At least one
  public platform recorded, during March 2024, an event of a defined class
  attributed to `docker`* satisfies §8's conjunction exactly -- A alone YES, B
  alone YES, jointly NO, latent NO. But the **only** definition of the event class
  that admits both members is a **disjunction of the two publishers' own
  mechanisms**, so the class is explicit and circular at once: its definition is
  the list of the things it was built to contain.
- **SOURCE ATTRIBUTION WAS NOT REMOVED. IT WAS RELOCATED, AND THAT IS WORSE.**
  The proposition's SUBJECT is genuinely source-independent -- *"at least one
  public platform"* names no publisher. Its PREDICATE is not. So attribution moves
  from the subject of the sentence into the definition of its predicate, where it
  is harder to see. **A proposition that looks source-independent and is not is
  worse than one that is openly attributed**, and §9 was honoured by refusing the
  merge rather than by deleting `source_id`.
- **STRENGTHEN IT ONCE AND IT DIES, WHICH IS THE WHOLE FINDING.** The first
  strengthening that would carry information needs 88 questions compared against N
  content requests -- forbidden by §11, which are not two measurements of one
  quantity -- and needs exactly-aligned periods the grains do not provide. Above
  the existential floor the two apparatuses split into `AUDIENCE_OR_USAGE` and
  `PROBLEM_OR_NEED` and are **complementary**. So the convergence that is
  available is not worth building and the convergence worth building is not
  available.
- **THE WINDOWS OVERLAP AND ARE NOT ALIGNED.** Stack Exchange holds
  `2024-03-01T08:06:03Z .. 2024-03-05T04:17:20Z` against Wikimedia's whole UTC
  day buckets, and the finest grain held is a day -- so **no aligned bounded
  period exists for any quantitative comparison**. Both sit inside March 2024, and
  **containment is weaker than alignment**: the proposition survives this only
  because it is weak enough not to need alignment.
- **NO MONTHLY AGGREGATE WAS MANUFACTURED, FOR TWO REASONS, AND BOTH ARE
  REPORTED.** Not needed, because an existential is entailed by one qualifying
  observation and requires no sum. Not available either, because §10 permits the
  diagnostic aggregate only where the complete daily observations are held and
  this deployment holds **7 of 31** March days. **Reporting only the first would
  leave a reader believing the aggregate was available and merely unused.**
- **INDEPENDENCE IS `UNKNOWN` AND NOT REFUTED, AND THE DIFFERENCE DECIDES WHAT MAY
  BE ATTEMPTED NEXT.** Mission 1.46 REFUTED independence on a documented common
  upstream, which closed that direction permanently. Here no shared upstream is
  documented or plausible; what is missing is affirmative documentation of ONE
  side. **An unknown can be resolved by a retrievable document. A documented
  common producer cannot.** §13 still forbids converting *"no dependency found"*
  into independence, so `KNOWN_INDEPENDENT` was not recorded.
- **TWO INDEPENDENT GATES FAIL ON ONE ROOT CAUSE.** Stack Exchange's own
  methodology is unreachable because the site's robots policy blocks this
  environment's fetcher. That leaves its measurement lineage undocumented (gate 6)
  AND is the same insufficiency for which **the operator already answered NO to
  both Stack Exchange reliability scopes in Mission 1.36.1**. So the route needs a
  reliability judgement already declined, for a reason no mission may clear: it is
  a publisher's access policy, and **no retry, header variation, mirror, cached
  copy or third-party summary may stand in for a first-party document**. Zero
  requests of any kind were made in this mission, and none was attempted against
  the blocked documentation.
- **THE CONVERGENCE CONTRACT STRUCTURALLY CANNOT EXPRESS IT**, proved through the
  REAL constructor rather than asserted: `PropositionConvergenceContract` raises
  unless `source_id` is in `identity_fields`, and `SourceBoundary` has exactly one
  member whose docstring says a cross-source value is *"deliberately absent rather
  than present-and-unused"*. Nothing was implemented and no guard relaxed.
- **THE IDENTITY/WITNESS EXERCISE FAILS ON A REAL FACT.** `audience_class` is
  REQUIRED on `content_request_count` precisely so one item over one period cannot
  carry two counts under one name (Mission 1.19), and it has no counterpart on the
  other side. **A fact load-bearing for one witness and absent for the other
  cannot be demoted to witness without the proposition losing the ability to say
  what it is about.**
- **THE CODEBASE HAD ALREADY RECORDED THE COMPLEMENTARITY, UNPROMPTED.** The
  Opportunity engine's mapping rationale for `community_question_volume` says
  `PROBLEM_OR_NEED` is *"a genuinely different question from the one
  `AUDIENCE_OR_USAGE` answers ... and neither implies the other"* -- written in
  Mission 1.30. Meanwhile `observation_category` is `UNCATEGORISED` on all 57
  Evidence rows, so **no category was coerced and none invented**: the field that
  would have been coerced carries no distinction to coerce.
- **`STRUCTURALLY_IDENTIFYING` YES AND `SEMANTICALLY_USEFUL` NO, REPORTED APART.**
  Two `KNOWN_INDEPENDENT` items would form two groups and saturation would exceed
  `max(g_A, g_B)` -- the first divergence from B-2 in this repository. It would be
  achieved by a near-tautology, and **reporting only the first would present a
  structural exercise as an epistemic gain**.
- **NO ROUTE WAS SELECTED, AND THE THREE DOWNSTREAM BLOCKERS WERE DELIBERATELY NOT
  REPORTED AS THE OUTCOME.** `CONVERGENCE_CONTRACT_ARCHITECTURE_GAP` and
  `PROVENANCE_INDEPENDENCE_NOT_ESTABLISHED` are both true and both sit downstream:
  widening the contract or retrieving one document would leave the proposition
  just as near-tautological. And `COMPLEMENTARY_NOT_CORROBORATING` as written says
  the apparatuses *do not independently support the same Claim*, which is **false**
  of the one candidate that passes. Mission 1.46 refused outcome B on the same
  reasoning, and the rule it set governs here.

**THE STRUCTURAL OBSERVATION FOR THE NEXT MISSION.** Mission 1.43 established
that only ESTABLISHED INDEPENDENCE or CONTRADICTION can make the full aggregator
differ from B-2. This mission found that the propositions easiest to converge
across apparatuses are **existentials**, and an existential is **MONOTONE**: a
counterexample cannot falsify it, so it can never produce a contradiction case.
The propositions that CAN be contradicted are point or universal claims, and
those are exactly the ones only one apparatus supports. **So one property of this
corpus blocks both roads out of the B-2 identity at once.**

**The next mission asks what TYPE of apparatus is needed, not which held pair can
be made to fit**: one observing the same phenomenon as an apparatus already held,
with a **documented measurement lineage**, capable of producing a **falsifiable
point claim** rather than an existential. Do not add sources at random, do not
widen the convergence contract, and do not implement the weak proposition to make
the aggregator produce a different number. **Mission 1.48 was not started.**

### A second publisher is not a second provenance group

Added in 1.80 (Mission 1.46, `independent-statistical-route-feasibility-v1.md`,
`mission-1.46-report.md`). **`COMMON_UPSTREAM_SOURCE_PREVENTS_INDEPENDENCE`**:
neither World Bank + Eurostat nor World Bank + FRED can produce the first Claim
with two ESTABLISHED independent provenance groups.

    Destatis / INSEE        the measurement happens ONCE, here
        |
        +-- Regulation (EU) 1260/2013 --> Eurostat
        |                                     |
        +-- via NSOs -------------------------+--> World Bank WDI --> FRED

- **DIFFERENT PUBLISHERS ARE NOT INDEPENDENT EVIDENCE, and both rejections rest
  on the publishers' own words.** FRED names Source *World Bank*, Release *World
  Development Indicators* and **Source Code `SP.POP.TOTL`** -- the exact series
  this repository already holds -- with a suggested citation reading *"World Bank
  ... retrieved from FRED"*. The World Bank's indicator metadata names **"Eurostat:
  Demographic Statistics"** among its four `sourceOrganization` entries, and
  Eurostat's ESMS metadata says population data are **collected by Eurostat from
  National Statistical Institutes**. Independence is a fact about MEASUREMENT
  LINEAGE, never about the hostname, the organisation, the database or the page.
- **THE PAIR THAT MATCHES PERFECTLY MATCHES BECAUSE IT IS ONE SERIES.** FRED
  reproduces the World Bank source note word for word. Semantic equivalence on its
  own is not evidence of anything, and a mission hunting for a same-proposition
  partner will find its cleanest match in a republication. That is why §7 is TWO
  gates and why YES on one is not progress.
- **THE OTHER PAIR FAILS BOTH GATES INDEPENDENTLY.** Beyond the shared upstream,
  the World Bank counts the **de facto** population at **midyear** while Eurostat
  counts the **usually resident** population on **1 January**. A shared year label
  is not a shared reference date.
- **NEITHER WAS REJECTED ON AN UNKNOWN, WHICH IS WHAT CLOSES THE DIRECTION.** An
  unknown can be resolved by more reading; a documented common producer cannot.
  §6 requires the ABSENCE of a documented common upstream before
  `KNOWN_INDEPENDENT` may be recorded, and here it is present and published.
- **THE STRUCTURAL FINDING IS WORTH MORE THAN A ROUTE WOULD HAVE BEEN.** For
  official macro statistics the international publishers are DISTRIBUTION LAYERS
  over national producers. The measurement of how many people live in Germany
  happens once, at Destatis. So **"add another statistical publisher" can never
  yield a second provenance group for a national aggregate**, however many are
  added. Independence over this family would need two genuinely different
  measurement APPARATUSES observing the same phenomenon.
- **NO ROUTE WAS SELECTED AND NO SLOT WAS FILLED.** §25 forbids a least-bad
  fallback, and §14's qualified alternative is **NONE inside the eligible
  portfolio**: the eligible `economic_data` family is exactly
  `{world-bank, eurostat, fred}`, the three publishers just shown to share
  producers. Naming a fourth would mean reaching outside the eligible set or
  inventing a candidate, so the slot was left empty.
- **GOVERNANCE WAS NOT THE BLOCKER, AND THE ENGINEERING GAP WAS NOT THE FINDING.**
  All three sources are `APPROVED_WITH_CONDITIONS` under
  `local-private-research-v1` with **0 unsatisfied conditions**. Eurostat and FRED
  genuinely lack a registered resource, a collector and a normalizer -- and the
  routes died upstream of that, so `STATISTICAL_RESOURCE_OR_COLLECTOR_GAP` is not
  the outcome. **Reporting the second obstacle would have hidden the first.**
- **THE MODEL IS READY AND IS NOT THE GAP.** `_group_key` puts a
  `KNOWN_INDEPENDENT` item in its OWN group keyed by `evidence_id`, so two such
  rows on one Claim form two groups and enter saturation as
  `S = 1 - (1 - g_A)(1 - g_B)`, which can differ from `max(g_A, g_B)`. Asserted on
  non-empty fixtures for **all three** independence states so every branch
  executes, without rediscovering Mission 1.43's arithmetic. **What is missing is
  a real source pair entitled to inhabit the shape**, and 0 independence groups
  exist before and after.
- **§10 WAS ANSWERED AND OUTCOME B WAS REFUSED.** The held World Bank Claims carry
  `source_id` as PROPOSITION IDENTITY, so two publishers cannot both support one
  source-attributed OBSERVED proposition; a second source forms its own Claim.
  Both routes out -- a multi-source OBSERVED convergence contract in the ADR-035
  line, or an INFERRED Claim -- were identified and neither was built.
  **`INDEPENDENT_ROUTE_REQUIRES_INFERRED_STATISTICAL_CLAIM` is deliberately NOT
  the outcome**, because the blocker sits UPSTREAM of the Claim architecture and
  reporting B would misattribute the failure to a layer that never got to fail.
  Source attribution was not proposed for deletion (Mission 1.38).
- **NOTHING WAS ACQUIRED TO ANSWER A FEASIBILITY QUESTION.**
  `RESEARCH_DATA_REQUESTS = 0`. One `METADATA_ONLY` call -- the World Bank
  indicator metadata endpoint, which returns a description and a source list and
  **no observations** -- persisted no RawRecord. Five documentation requests, all
  first-party; the one web search was navigational and established nothing.
- **NO SIMILARITY MACHINERY DECIDED ANYTHING.** Every equivalence and every
  dependence judgement is document-backed and auditable (§11). 0 model calls, 0
  embeddings, Problem-Family still PARKED.

**The next mission is NOT an acquisition and NOT calibration.** Acquiring Eurostat
or FRED population would add rows that cannot become a second group, which is the
expansion Mission 1.43 proved cannot help; and with one group the aggregator is
still algebraically the pass-through baseline, so labelling would ask a person to
compare cases the aggregator cannot distinguish. **The question worth a mission is
upstream of any acquisition**: whether a bounded proposition can be defined that
two genuinely different measurement apparatuses ALREADY IN THIS CORPUS both bear
on, without weakening proposition identity. That is a proposition-design question
in the ADR-035 line, and it may conclude that the INFERRED layer is required -- a
decision this mission does not make.

### A reply answers the question that was asked

Added in 1.79 (Mission 1.45, `ted-eu-official-reuse-response-v1.md`,
`mission-1.45-report.md`). **`TED_OFFICIAL_REUSE_GUIDANCE_RECONCILED`**: the
Publications Office answered the clarification request this repository has
carried as an unsent draft since Mission 1.15.3.

    reviews appended   local v2 -> v3   commercial v5 -> v6   255 ins / 0 del
    research data requests  0     governance document requests  6 over 4 URLs
    reliability changes     0     personal-data fields found    0 of 188 records

- **A REPLY IS AN ANSWER TO THE QUESTION THAT WAS ASKED, AND THAT CUTS BOTH
  WAYS.** The request described this system BY NAME as *a commercial
  software-as-a-service application*, so the commercial half of the answer rests
  on the widest honest description of the product rather than on a narrowed one --
  which is the Source governance rule read forwards. And the request never
  described **raw redistribution, resale or customer-facing source access**, so
  the reply cannot authorise them. **Commercial purpose is not unrestricted
  redistribution**, and the commercial profile stays `REQUIRES_REVIEW` with its
  blocker changed from H-36 to the part of the profile nobody asked about.
- **H-36A WAS SPLIT RATHER THAN ANSWERED.** Database-right **EXISTENCE** stays
  `NOT_ESTABLISHED`: the reply says **copyright** over the database, and Directive
  96/9/EC creates two rights -- copyright in the arrangement (Art. 3) and the
  **sui generis** right of the maker (Art. 7) -- so it does not name the right the
  question named, and *"whether or not"* is a refusal to say. Whether such a right
  **BLOCKS REUSE** becomes `OFFICIAL_FIRST_PARTY_GUIDANCE_INDICATES_NOT_A_BLOCKER`.
  **The abstract legal ontology is unresolved and does not have to be resolved for
  this purpose**, because the body that would assert the right says it should not
  stand in the way. `NOT_ESTABLISHED` was not changed to `NO_RIGHT_EXISTS` and on
  this evidence never may be.
- **H-36B IS `RETRIEVAL_METHOD_NEUTRALITY_FOR_REUSE`, AND IT IS NOT AN ACCESS
  PERMISSION.** *"The way in which the data are retrieved is not relevant in this
  regard"* answers a question that named both routes. It is not a database-right
  grant, and it is not *any acquisition method is allowed*: **reuse rights and
  technical access rules are different questions**, and no circumvention,
  anti-bot bypass, authentication bypass, rate-limit evasion or undocumented
  endpoint is authorised.
- **THE BULK ROUTE STAYS BLOCKED AND ITS BLOCKER CHANGED IDENTITY.** It was
  blocked because Mission 1.15.3 placed the highest database-right exposure
  there, and the reply weakens exactly that. It stays blocked because the bulk
  packages offer **no field selection**, so minimisation cannot happen AT
  acquisition -- and a bulk package delivers the whole notice including the
  contact block. **Re-grounded, not relaxed.**
- **THE TWO QUESTIONS THAT WERE NOT ANSWERED ARE RECORDED AS NOT ANSWERED.** The
  scope of *"SIMAP's system metadata"* stays `UNRESOLVED`, so **no structured TED
  notice field is classified CC0** -- reading the reply's metadata sentence as
  covering notice fields would answer the operator's own question in the reuser's
  favour with a sentence not addressed to it. The COM_REUSE versus CC BY
  catalogue mapping stays `NOT_FULLY_RESOLVED` and is **non-blocking**, because
  reuse is authorised directly and does not depend on catalogue metadata:
  **legal authorisation and catalogue metadata consistency are separate
  questions.**
- **ATTRIBUTION GOT STRICTER, WHICH IS NOT THE DIRECTION GOOD NEWS USUALLY
  MOVES.** The legal notice's procurement-notice sentence states no
  acknowledgement condition; the reply does, and that is **Article 6(2)(a)** of
  the Re-use Decision applied to the notice corpus itself rather than only to the
  CC BY editorial content. **Where two first-party statements differ in
  strictness the stricter governs.** Three regimes stay apart and no universal
  rule is invented: notices acknowledge, editorial content is CC BY credit plus
  indication of changes, CC0 material owes nothing.
- **APPENDING A REVIEW ORPHANS THE OPERATOR'S ACCEPTANCE, BY DESIGN, AND THAT WAS
  THE DECISION.** Verifications are pinned to condition rows, so a new version
  creates new ones. Mission 1.29 WITHDREW an append rather than pay this, and the
  precedent was weighed: there, recording an `UNCLEAR` verdict that refused at the
  gate anyway gained nothing operational, so breaking acquisition was pure loss.
  Here the record gains the load-bearing answer of the whole TED arc and an
  attribution obligation the reply IMPOSES -- and **the thing the operator
  accepted has itself changed.** A residual that is smaller is still a residual,
  and the honest way to say *what you accepted is now different* is to ask for the
  acceptance again. **TED is INELIGIBLE under the local profile until a named
  operator records it**, and `record_ted_operator_acceptance.py` **was not
  repointed**: its own guard says *"the acceptance has to be made again by a
  person, not replayed"*, and repointing it would turn a replay of a decision
  already made into a record of one nobody has taken.
- **THE FIRST `OPERATOR_CORRESPONDENCE` ROW FOUND A MODEL GAP THAT HAD BEEN THERE
  SINCE MIGRATION 0004.** The type was permitted and every evidence row was
  required to carry an absolute `http(s)` URL -- enforced in the schema, in
  `PolicyEvidence.__post_init__` and in `validate_source_registry.py`. **A letter
  has no URL**, so the enum permitted a class of evidence the URL rule refused,
  and the refusal was invisible because nobody had tried. **The rule's own
  justification does not reach it**: *"an assessment that cannot be re-opened
  cannot be re-verified when the platform changes its terms"* is an argument about
  PUBLISHED PAGES, which change under a stable address, while correspondence is
  fixed when it is sent and is re-verified by producing the message. Migration
  0033 lets correspondence and legal review address themselves by `mailto:` and
  requires a `document_fingerprint` -- **both halves or neither**. Every other
  type still requires `http(s)`, and a fingerprint is still not demanded of a
  published page.
- **THE ARTIFACT IS FINGERPRINTED AND NOT COMMITTED.** It carries a named
  official's direct telephone number and email and the operator's personal
  address, and this repository is public. **A governance record that had to
  breach the minimisation obligation it exists to check would be a poor record**,
  so what is preserved is the SHA-256, the operative text in full, and the
  first-party mailbox the matter is re-opened through.
- **NOTHING DOWNSTREAM MOVED, AND ONE SEPARATION IS NOW ENFORCED BY A TEST.**
  Reuse asks *may this system use the data*; reliability asks *how dependably does
  this measurement support this proposition*. **A more permissive reuse position
  must never raise a reliability**, and TED's `0.5` and `0.55` are unchanged. The
  legal notice's ten-year public window and its accuracy disclaimer are recorded
  as `POTENTIAL_FUTURE_RELIABILITY_BASIS` and as nothing else. **Public
  retrievability is not internal preservation**, and neither withdraws reuse
  permission for data lawfully obtained earlier.
- **HISTORY WAS NOT REWRITTEN.** 255 insertions and 0 deletions; every review
  written before 2026-09-04 still records that no authoritative reply was held,
  and the unsent request still records that nothing was sent. **A reply arriving
  does not retroactively make this repository the sender.**
- **44 TESTS FAILED ON THE APPEND AND EVERY ONE KEPT ITS PROPERTY.** Version
  lines pinned to their length, fixtures hard-coding `review_version=2`, and
  tests reading *the current review* to check what an EARLIER mission recorded --
  the last of which is the subtle one: a test that follows `current` to assert
  what Mission 1.15.1 said is a test asserting that no later mission may ever
  answer an open question. The two tripwires Mission 1.15.4 installed for this
  exact moment fired and were re-pointed rather than deleted, and one test's own
  docstring had already predicted it: *"v1 owns its own row and stays FALSE. **A
  future v3 would too.**"*

**The next action is the operator recording the acceptance for review v3**, whose
exact statement is written out in the reconciliation document 12.2 -- and writing
it down is not recording it. After that the roadmap is unchanged: **an
independence-capable evidence route**, Eurostat or FRED beside World Bank.
**Mission 1.43's finding is arithmetic and a governance answer does not touch
it.**

### Nothing is a fact; not enough is a judgement

Added in 1.77 (Mission 1.44, `wikimedia-convergent-reliability-review-packet-v1.md`,
`mission-1.44-report.md`). **`READY_FOR_WIKIMEDIA_CONVERGENT_RELIABILITY_REVIEW`**:
the question prepared, no judgement supplied, **0 assessments created**.

    18 Evidence / 6 Claims / cardinalities {4,3,3,3,3,2}  ->  ONE five-part scope
    resolver  NO_APPLICABLE_ASSESSMENT     leak checks  30 run, 0 leaks
    dimension states  4 blank, 1 asserted  reliability  null   gate  UNANSWERED

- **THE ALMOST-MATCH IS TIGHTER THAN TED'S, AND THE NUMBER IS MORE INVITING.**
  The existing Wikimedia `0.65` shares source, resource, record kind AND claim
  type with the scope under review, and differs only on `proposition_kind`. That
  is sufficient, and it was proved rather than asserted: the real resolver in
  both directions, plus 30 leak checks over every proposition kind in the corpus.
  There is no closest-match logic, no fallback, and **a scope naming only the
  publisher matches nothing by construction**.
- **SOFTWARE ASSERTED ONE STATE, AND NOT THE ONE A READER WOULD EXPECT.** Mission
  1.42 could assert `NOT_ESTABLISHED` for TED's mutability because the held basis
  said **nothing**. Here the basis says **something and not enough**: a dated
  known-problems list records that a 2016 user-agent classification incident
  occurred, and states no revision policy. **Whether an incident list without a
  policy is `PARTIALLY_DOCUMENTED` or `NOT_ESTABLISHED` is a judgement about
  sufficiency**, so `HISTORICAL_MUTABILITY` was left blank -- exactly where a
  generator trying to be useful would have filled it in. The single assertion is
  `SOURCE_SIDE_CHECKABILITY = NOT_ESTABLISHED`, which is a checkable claim about
  what the corpus contains.
- **MULTIPLE WITNESSES OF ONE METHODOLOGY DO NOT INSURE AGAINST A
  METHODOLOGY-LEVEL FAILURE.** This is the question convergence introduces here
  and does not inherit. An existential survives losing one witness, which looks
  like robustness -- but every witness shares one counting rule, one tagging
  mechanism and one pipeline, and independence is UNKNOWN, so a **systematic**
  reclassification could remove them all at once. A **localised** problem
  therefore matters LESS than it does to a named-pair claim, and a systematic one
  matters MORE. The known-problems document is `PARTIALLY_APPLICABLE` with its
  weight moving in **two directions at once**, and which reading governs is the
  reviewer's.
- **AN EXISTENTIAL IS MONOTONE OVER PUBLICATION AND NOT OVER REVISION.** Once a
  qualifying pair is published nothing later falsifies it -- unless the published
  value itself can be recomputed, in which case the witness that established it
  can stop being one. The usual monotonicity argument depends on a revision
  policy this basis does not state.
- **NOTHING WAS FETCHED.** The convergent proposition reads the same BT-equivalent
  measurement through the same rules, so both held documents still describe it:
  `Research:Page view` is **REUSED** and more load-bearing than before, because
  `audience_class` is one of the six identity fields the contract keeps.
- **`user` IS NEVER TRANSLATED.** It is the platform's own class name for traffic
  not identified as automated by ua-parser plus custom regex, and it does not mean
  human, person, reader or customer. A test scans for the translation.
- **WITNESS CARDINALITY IS NOT RELIABILITY.** One Claim has four witnesses and
  another has two, and the four-witness measurement is not thereby more
  dependable. Cardinality belongs to aggregation; reliability belongs to
  measurement crossed with proposition. **Four witnesses is also not four
  independent sources**: independence stays `UNKNOWN` on all 18 rows with 0
  groups.
- **THE SCOPE CARRIES NO ARTICLE, DIRECTION, REQUESTER CLASS, PERIOD OR WITNESS
  COUNT**, so this is ONE question rather than six, and Docker, Kubernetes and
  Podman do not get separate reviews.
- **THE HISTORICAL ASSESSMENT KEEPS ITS NULL RUBRIC PROVENANCE**, which is true
  rather than missing: it predates the rubric, and backfilling would fabricate
  the provenance the column exists to record. A future assessment for the new
  scope CAN record `human-reliability-assessment-rubric@1.0.0`, because migration
  0032 added the columns.
- **A THIRD DEFECT OF THE SAME SHAPE, AND §37 CAUGHT IT ON ITS FIRST RUN.**
  `ReliabilityBinding.to_json()` called `.isoformat()` on a field four generators
  already pass as `None`, and had never crashed because **no live binding had
  ever been serialised** -- every row in this scope resolves to no assessment, so
  the resolved branch is unreachable from the corpus. The type said `datetime`
  while the codebase treated it as optional in four places. After Mission 1.36.1's
  `binding.assessment_version` and Mission 1.42.1's `group.members`: **a branch no
  data has ever entered is not tested by a passing suite**, and the fixture
  requirement exists because of them.

**The next action is a HUMAN REVIEW of this scope, and nothing else
automatically.** If the gate returns `NUMERIC_JUDGEMENT_PERMITTED` with a value,
reviewer, rationale and limitation, a later mission may persist exactly one
assessment, and **six real multi-Evidence Claims become scorable including the
first with four witnesses**. After that, **do not proceed to calibration**:
Mission 1.43's finding still governs, these six Claims each have one provenance
group, and with one group the full aggregator is algebraically the pass-through
baseline. The next strategic mission remains an **independence-capable evidence
route**.


**COMPLETED IN 1.78 (Mission 1.44.1, `mission-1.44.1-report.md`,
`wikimedia-convergent-operator-reliability-review-v1.md`,
`wikimedia-convergent-reliability-resolution-v1.json`). The operator typed it,
`max(members)` received FOUR real items, and the prediction held.**

    ReliabilityAssessments  3 -> 4        basis rows  10 -> 12
    convergent rows RESOLVED  18/18       evidence.reliability written  0
    scorable multi-Evidence Claims  2 -> 8   max(members) received  4,3,3,3,3,2
    leak checks  36 run, 0 leaks          independence groups  0

- **`WIKIMEDIA_CONVERGENT_OPERATOR_RELIABILITY_DECISION_PERSISTED`**, with
  **`AGGREGATION_MECHANISM_STILL_UNIDENTIFIABLE_FROM_REAL_CORPUS`** reported
  beside it, because §18 requires saying so when support groups per Claim is 1
  everywhere and contradiction cases are 0.
- **THE OPERATOR SUPPLIED THE FOUR DIMENSIONS SOFTWARE REFUSED TO FILL IN.**
  Mission 1.44 asserted only `SOURCE_SIDE_CHECKABILITY = NOT_ESTABLISHED` and
  left `HISTORICAL_MUTABILITY` **blank** because *something and not enough* is a
  judgement about sufficiency. It came back `PARTIALLY_DOCUMENTED` -- the answer a
  helpful generator would have guessed, supplied by the person entitled to guess
  it. Assessment `19e0ce16` v1, `0.6`, `HUMAN_REVIEW`, `thibchm`,
  `human-reliability-assessment-rubric@1.0.0`.
- **TWO `UNSURE` MATERIALITY ANSWERS SURVIVED AS `UNSURE`**, and both hard-stop
  answers that look inconsistent are not: `SOURCE_SIDE_CHECKABILITY` is
  `NOT_ESTABLISHED` while `SOURCE_OBSERVATIONS_NOT_RECOVERABLE` is `NO`, because
  the first is a fact about the basis and the second would be the stronger claim
  that the observations are KNOWN to be unrecoverable. **Software derived neither
  from the other.**
- **`max(members)` FINALLY RECEIVED MORE THAN TWO.** Four real canonical items
  once, three four times, two once, with `collapsed_member_count` one lower each
  time. Mission 1.42.1 was the first time it received two; group cardinality above
  two had never occurred in this repository.
- **AND THE NUMBER STILL DID NOT MOVE.**
  `IDENTICAL_TO_RELIABILITY_PASS_THROUGH` on all six, and Mission 1.43 predicted
  it before this data existed: one group per Claim, saturation over one group is
  that group's strength, group strength is `max()` over identical
  reliability-limited `q` values, and B-2 reports the same maximum. **What is new
  is that the mechanism ran at cardinality four, not that it produced more.**
  `q = 0.6` limited by `reliability` on **34 of 34**, masses 0.6 / 0 / 0 / 0.4,
  EvidenceScore **60.0**, level **1**, blocked on *"2 supporting groups of
  established independence, found 0 (plus 1 unknown-provenance group, which does
  not count)"*.
- **FOUR WITNESSES IS NOT CORROBORATION, AND THE REVIEWER WROTE THAT SENTENCE
  THEMSELVES.** The stated limitation says witness cardinality does not establish
  independent corroboration -- one publisher, one counting methodology, one
  requester-classification mechanism, one pipeline, independence `UNKNOWN` on all
  18 rows, **0 groups created**.
- **THE MIDPOINT COINCIDENCE WAS NOT TREATED AS EVIDENCE.** `0.6` is exactly
  halfway between the detailed Wikimedia `0.65` and the convergent TED `0.55`. An
  averaging check was written, it failed, and **the test was removed rather than
  the operator's value questioned**: the value was supplied against a recorded
  ordinal profile, the two historical values belong to different scopes, and
  **software cannot prove the provenance of a number from the number**. What is
  asserted is only the checkable thing -- that it equals none of the three values
  it might have been copied from.
- **A PRE-PERSISTENCE TEST CLASS ASSERTED THE ABSENCE OF THE ASSESSMENT, AND
  RE-POINTING IT CAUGHT A REAL OMISSION.** The rendered review page still read
  *"Nothing yet"* because it had not been re-rendered after the link was written.
  Same repair shape as Missions 1.36.1, 1.40 and 1.41: **a test asserting that
  nothing was ever persisted is a test asserting the review is never answered.**
- **NOTHING ELSE MOVED.** 0 network requests, 0 model calls, 0 calibration labels,
  0 parameters fitted, 0 Scores, 0 Opportunity changes, 0 rankings, 0 embeddings.
  The three historical assessments are unchanged and unsuperseded, both pre-rubric
  rows keep NULL provenance, and `REFERENCE_PROFILE_V1` is still `UNCALIBRATED`.

**The next mission is NOT calibration**, and the reason is arithmetic rather than
caution: labelling this corpus would ask a person to compare cases the aggregator
itself cannot distinguish. The target is **ESTABLISHED INDEPENDENCE** --
**Mission 1.45 -- Independent Statistical Evidence Route Feasibility V1**, over
Eurostat or FRED beside World Bank, both eligible under
`local-private-research-v1` today. **It was not started.**

### One provenance group makes the aggregator and the baseline the same number

Added in 1.76 (Mission 1.43, `mission-1.43-report.md`,
`calibration-corpus-expansion-plan-v1.json`).
**`CALIBRATION_REFERENCE_CORPUS_MEANINGFULLY_EXPANDED`**, with
**`NEW_CORPUS_SHAPE_NON_SCORABLE_MISSING_RELIABILITY`** beside it.

    Claims 37 -> 43     Evidence 39 -> 57     Claims with >1 Evidence 2 -> 8
    max Evidence per Claim 2 -> 4    group cardinality {1,2} -> {1,2,3,4}
    network requests 0    new Signals 0    new assessments 0    scores 0

- **THE MEASUREMENT CAME FIRST AND IT REFRAMED THE MISSION.** Across all 37
  Claims: **0 with more than one support group, and 0 where the aggregator
  differs from the B-2 reliability pass-through baseline.** With exactly one
  group that identity is **ALGEBRAIC**: `S = 1 - prod(1 - g)` over one group is
  that group's strength, group strength is `max(members)`, and B-2 is the
  reliability-limited strongest item -- the same maximum over the same `q`
  values. **No quantity of additional single-group Evidence can ever make them
  differ**, so corpus expansion measured in rows is expansion that cannot help.
- **THE MECHANISM WORKS; THIS CORPUS GIVES IT NOTHING TO WORK ON.** A §37 fixture
  hands the aggregator two `KNOWN_INDEPENDENT` items and support strength
  **exceeds** the pass-through value. What is missing is not the code but
  provenance facts: ESTABLISHED INDEPENDENCE or CONTRADICTION, and both are
  blocked by what the portfolio observes rather than by effort.
- **THE SCORABLE OPTION WAS REFUSED, AND THAT WAS THE DECISION.** Another TED
  division would have been immediately scorable, which is exactly what made it
  tempting, and it repeats the same proposition kind, reliability scope,
  unknown-provenance grouping, `q` limiter and EVERGREEN semantics. **Choosing it
  because a number would appear is choosing the appearance of progress.**
- **ZERO NETWORK REQUESTS, AND THAT WAS NOT MERELY THE CHEAPER CHOICE.** Live
  governance under `local-private-research-v1` was re-read from the DEPLOYMENT
  rather than from an old report: only `eurostat`, `fred`, `ted-eu` and
  `world-bank` are eligible now, and **Wikimedia is blocked by three unsatisfied
  conditions**. Re-derivation from Signals already lawfully collected was the
  only open door to the highest-information route.
- **A SECOND CONVERGENCE CONTRACT, AND THE SAME ADR-035 TEST.**
  `platform-counted-content-request-change-witnessed@1.0.0`: the day labels are
  WITNESS, everything else is identity. **`audience_class` stays identity**
  because Mission 1.19 made it REQUIRED precisely so that one item over one
  period cannot carry two different counts under one name -- dropping it here
  would undo that decision from the other end. `direction` stays identity for the
  reason the procurement contract's `relation` does.
- **THE PROJECTION IS A TABLE NOW, NOT A PAIR, AND STILL HAS NO FALLBACK.**
  Mission 1.39 wrote one hard-wired pair *"so a reader can see that exactly one
  route exists"*; a reader can still see every route at once, and five historical
  kinds have no contract and do not converge.
- **NOTHING WAS MANUFACTURED.** No contradiction: a decrease does not contradict
  an increase, because under the detailed kind direction is proposition identity
  and under an existential a counterexample does not falsify. No independence:
  every witness shares publisher, pipeline and method, and different days are
  temporal separation. **No temporality, and the reason is architectural** --
  every OBSERVED restatement is a historical fact about what a source published,
  and a historical fact does not decay. Wikimedia's buckets ARE documented UTC,
  and **a source with established timestamps still does not make a Claim
  temporal**; what would is a proposition whose truth decays, which belongs to
  the INFERRED layer nobody has built.
- **A NEW KIND IS A NEW RELIABILITY SCOPE.** The six new Claims are
  `NON_SCORABLE` with no applicable assessment, the existing Wikimedia `0.65`
  binds the DETAILED kind only, and §15 forbids widening it. Structure created,
  numeric path deliberately left closed.
- **LEAKAGE-SAFE CALIBRATION SPLITS ARE STILL NOT PLAUSIBLE.** The six new Claims
  share one reliability scope and one proposition kind, so under Mission 1.37's
  rule they are **one** group, and entirely non-scorable. More Claims did not
  become more independent units.
- **§37 EARNED ITS PLACE ON THE FIRST RUN.** This mission's own script read
  `result.level.evidence_level`, where the attribute is `result.level.level`. It
  failed immediately because the data was not empty -- the same class as Mission
  1.42.1's `group.members`, caught before it shipped. Every new reporting
  expression now executes against non-empty fixtures the live corpus does not
  contain, and none of them is persisted.

**The next mission is NOT a human calibration reference set.** Labelling this
corpus would ask a person to compare cases the aggregator itself cannot
distinguish. Two narrower missions come first: a **reliability review preparation
for the new Wikimedia scope**, which would make six real multi-Evidence Claims
scorable including one with **four** witnesses; and an **independence-capable
route**, which the gap matrix identifies as Eurostat or FRED beside World Bank --
a second statistical agency publishing about the same subject is the only visible
path to a second provenance group.

### The value is authorised; the keystroke is not

Added in 1.74 (Mission 1.42.1, `mission-1.42.1-report.md`,
`second-pilot-convergent-operator-reliability-review-v1.md`).
**`OPERATOR_CONFIRMATION_REQUIRED`**, reached with everything else complete.

    migration 0032   review_rubric_id, review_rubric_version -- both nullable
    dry run          version 1, HUMAN_REVIEW, thibchm, 0.55, 4 basis rows
    persisted        NOTHING. ReliabilityAssessments 2 -> 2

- **A MISSION BRIEF CAN SUPPLY A REVIEWER'S VALUES AND CANNOT SUPPLY THEIR
  KEYSTROKE.** `record_reliability_assessment.py` asks through `input()` and
  refuses on `EOFError`. Piping the confirmation, patching `isatty`, or writing
  the row with hand-written SQL would each produce an assessment whose
  `reviewed_by` names a person who did not type it -- the exact failure the
  reliability contract exists to prevent. **A guard removed to make a pipeline
  pass is a guard that never was**, and this is the second mission to stop at it.
- **THE SCOPE WAS NOT NARROWED, AND THAT WAS THE LIVE TEMPTATION.** The second
  pilot produced the two multi-Evidence division-92 Claims, so writing the
  assessment as though it were about them would have felt natural and would have
  been wrong. A reliability scope carries **no classification division and no
  currency**, so this one judgement binds divisions **90 and 92** and **EUR and
  SEK** -- six rows across four Claims. Narrowing it would have changed the
  architecture rather than the value.
- **NULL IS THE TRUE ANSWER FOR A REVIEW THAT PREDATES THE RUBRIC.** Migration
  0032 adds two NULLABLE columns with no `DEFAULT`, writes no row, and both
  historical assessments read NULL afterwards -- verified against the deployment.
  Backfilling them would fabricate the provenance the column was added to record.
- **THE BASIS TABLE WAS CONSIDERED AND REJECTED AS THE PLACE FOR IT.** A basis
  row names a retrieved document **about the measurement**. The rubric is the
  procedure the reviewer followed, and filing it there would inflate every future
  assessment's documentary basis with a document that says nothing about the
  publisher.
- **BOTH HALVES OR NEITHER, ENFORCED TWICE.** A CHECK constraint in the database
  and a guard in `__post_init__`: an id with no version names a moving target,
  and a version with no id names nothing at all.
- **`UNSURE` SURVIVES AS `UNSURE`.** Long-term retrievability is answered
  `UNSURE`, and it is not YES, not NO, not *low confidence* and not `0.5`. It is
  carried into the stated limitation rather than quietly resolved, because a
  reviewer who cannot yet tell whether an unknown matters has said something
  real.
- **THE GATE WAS RECORDED, NOT RECOMPUTED.** `NUMERIC_JUDGEMENT_PERMITTED` is the
  operator's decision; nothing derives it from the five ordinal states, because
  the rubric defines the gate as judgement rather than an arithmetic function.
- **`0.55` IS NEITHER 0.5 NOR 0.65 NOR THEIR MEAN**, and a test asserts all
  three -- the shapes a nudging or averaging bug would take. Neither historical
  assessment is superseded, because a different `proposition_kind` is a different
  question and `_next_version` correctly finds no same-scope row.
- **NOTHING NEW WAS FETCHED FOR THE BASIS.** The four held eForms SDK documents,
  including the one Mission 1.42 called `PARTIALLY_APPLICABLE` -- that verdict is
  about how much WEIGHT a reviewer gives it under an existential proposition, not
  about whether the document belongs. **No SROS engineering validation is among
  them**, and a test enforces it.
- **A PRE-EXISTING TEST PINNED THE BINDING'S KEY SET, AND WAS RE-POINTED RATHER
  THAN DELETED.** `ReliabilityBinding.to_json()` gained the two provenance keys,
  and the test asserts that the binding names everything needed to reconstruct
  the number -- which is exactly WHY they were added. Same repair shape as
  Missions 1.31.1, 1.32, 1.38, 1.40 and 1.41.
- **THE PRE-PERSISTENCE BASELINE IS RECORDED HONESTLY**: 0 of 6 rows resolved, 0
  scorable, `max(members)` receiving 0 members, 6 leak checks and 0 leaks. That
  is what the assessment will change, and reporting it now means the change can
  be measured rather than asserted.

**The next action is the operator typing the confirmation.** After that,
`report_convergent_reliability_resolution.py --link-review` measures the six
bindings, reruns the aggregator with the RESOLVED reliability, and records
whether `max(members)` finally received two real items -- and **two witnesses of
UNKNOWN provenance will still collapse into ONE group, which is correct and is
not corroboration.** Then **Mission 1.43 -- Calibration Reference Corpus
Expansion V1**, not calibration: two Claims sharing one assessment, with no
contradiction case, no established independence and no temporal Claim, is not a
dataset.


**COMPLETED IN 1.75. The operator typed it, and the two counters that moved are
the whole story.**

    ReliabilityAssessments  2 -> 3      basis rows  6 -> 10
    convergent rows RESOLVED  6/6       evidence.reliability written  0
    scorable multi-Evidence Claims  0 -> 2    max(members) received  2

- **THE FIRST ASSESSMENT THAT CAN SAY WHICH PROCEDURE PRODUCED IT.**
  `d1afa4be` v1, `0.55`, `HUMAN_REVIEW`, `thibchm`,
  `human-reliability-assessment-rubric@1.0.0`. Both historical assessments keep
  `NULL` rubric provenance and neither is superseded, because a different
  `proposition_kind` is a different question.
- **SIX ROWS RESOLVE A NUMBER AND NOT ONE STORES IT.**
  `scoring.evidence.reliability` is NULL on all 39 rows before and after. **9
  leak checks, 0 leaks.**
- **`max(members)` FINALLY RECEIVED TWO REAL ITEMS.** Mission 1.41 had `raw = 2`
  and `scorable = 0`, so the grouping arithmetic had never run on real canonical
  data. It ran: **one support group, kind UNKNOWN, two members,
  `collapsed_member_count` 1** -- because `DISJOINT` observation membership is
  temporal separation and not epistemic independence. **0 independence groups
  created**, and this must never be reported as corroboration.
- **AND THE NUMBER DID NOT MOVE, WHICH IS THE HONEST HEADLINE.**
  `IDENTICAL_TO_RELIABILITY_PASS_THROUGH` on both Claims. Two rows sharing one
  assessment, collapsed into one group, put `max()` over two identical `q`
  values -- so the full aggregator and Mission 1.37's B-2 baseline agree
  **because the corpus gives them nothing to disagree about**. What is new is
  that the mechanism ran, not that it produced more.
- **`q = 0.55`, LIMITED BY RELIABILITY ON 28 OF 28.** Relevance, directness,
  extraction confidence and freshness are all `1.0`, so the score is a
  restatement of one human judgement. Masses 0.55 / 0 / 0 / 0.45, EvidenceScore
  **55.0**, **level 1**, blocked on *"2 supporting groups of established
  independence, found 0 (plus 1 unknown-provenance group, which does not
  count)"*, the `MARKET_ACTIVITY` gate and the `DIRECT_VALIDATION` gate.
  Reliability reaches none of the three.
- **THE TARGET VARIABLE GAINED A THIRD VALUE AND NOT A THIRD KIND OF THING**:
  `{0.5: 6, 0.55: 4, 0.65: 18}`, all reviewed reliability. Mission 1.37's finding
  stands.
- **A THIRD DEFECT OF THE SAME SHAPE, AND THE OPERATOR FOUND IT BY RUNNING THE
  OUTPUT.** The reporter read `group.members`; the attribute is
  `member_evidence_ids`. `max(..., default=0)` never evaluated its generator
  while zero groups existed, so the wrong name sat there looking fine until the
  first Claim became scorable. After Mission 1.36's invalid basis types and
  1.36.1's `binding.assessment_version`: **a branch no data has ever entered is
  not tested by a passing suite.**

**D-03 blocker 2 moves to PARTIAL and the other four do not move.** Next is
**Mission 1.43 -- Calibration Reference Corpus Expansion V1**, and the diagnostic
is the argument for it: two Claims agreeing exactly with a pass-through baseline,
with no contradiction case, no established independence and no temporal Claim, is
not a dataset.

### A number is a summary of a profile, or it is an impression

Added in 1.73 (Mission 1.42a, `human-reliability-assessment-rubric-v1.md`,
`mission-1.42a-report.md`). **`HUMAN_RELIABILITY_RUBRIC_READY`**, with
`RELIABILITY_RUBRIC_PROVENANCE_MODEL_GAP` recorded beside it.

    DOCUMENTED FACTS  ->  [ the rubric ]  ->  HUMAN JUDGEMENT  ->  Assessment
    dimensions accepted 5    rejected 6    hard stops 4    anchors 2 (0 intermediate)

- **THE GAP WAS NEVER DECIMAL PRECISION.** Mission 1.14 defined what reliability
  means, ADR-026 the scope it binds to, and the review guide said to write the
  failure mode down first. A reviewer who had done all of it still had no
  procedure making `0.45` rather than `0.65` defensible, because **nothing in
  this repository anchors the absolute scale** -- which is exactly why the
  contract forbids threshold labels and why Mission 1.37 found only the ORDINAL
  construct defined.
- **A DECISION PROCEDURE, NOT A SCORING FUNCTION.** The rubric module contains
  **no arithmetic operator at all** -- no `BinOp`, no `sum`, `min`, `max` or
  `round` -- asserted over its AST. The ordinal ranks order three states and are
  never summed. Replacing arbitrary numbers with a weighted average of invented
  sub-scores is the one failure this mission existed to avoid.
- **THE REJECTIONS ARE THE SUBSTANCE.** `MEASUREMENT_TO_PROPOSITION_FIT` **is
  `directness`**, already a component of `q = min(components)`, and scoring it
  again would make one weakness count twice -- while its reliability-native
  residue is not a gradient at all: a proposition asking more than the
  measurement observes is a **mis-specified scope**, so it became a HARD STOP.
  `CLASSIFICATION_DEPENDABILITY` folded into the five, because a dimension of its
  own would be a rubric shaped around one publisher's taxonomy.
  `KNOWN_FAILURE_MODES` and `RESIDUAL_UNKNOWN` are the OUTPUT of the five rather
  than a sixth question. And **a separate reviewer-confidence field was refused**:
  basis completeness is READ OFF the dimension profile, and two fields answering
  one question eventually disagree.
- **UNKNOWN IS NOT LOW, AND THE ENFORCEMENT IS STRUCTURAL RATHER THAN A WARNING.**
  `NOT_ESTABLISHED` and `CONTRADICTED` carry **no ordinal rank**, so neither can
  be interpolated, averaged, or quietly read as the bottom of the scale. An
  absence of documented revision is still not evidence of stability.
- **NO INTERMEDIATE ANCHORS.** The two that exist are defined by what the value
  DOES -- `1.0` can never be the limiting component in `q = min(components)`,
  `0.0` makes the Evidence contribute nothing -- never by an adjective, because
  an adjective is the threshold vocabulary the contract refuses. **`0.0` is a
  POSITIVE FINDING and is not the absence of an assessment**: absence means
  nobody judged.
- **`KEEP_NUMERIC_FIELD_BUT_REQUIRE_ORDINAL_REVIEW_PROFILE_FIRST`.** The numeric
  field stays -- no migration, no code change, the resolver and the aggregator
  untouched, both historical values kept -- and the ordinal profile must be
  completed **before the number is offered**. The number then summarises a
  recorded profile, and **the profile is what a second reviewer reproduces**.
  Anchored discrete values were refused as premature: the grid would have to be
  invented today, it could not represent the existing `0.65`, and with two data
  points there is no evidence about what granularity reviewers can resolve.
- **A NUMERIC JUDGEMENT MAY BE REFUSED, AND REFUSING IS A COMPLETE REVIEW.** Four
  hard stops make one unavailable, each because the question has **no answer**
  rather than a low one. A material unknown is deliberately NOT among them, and
  `UNSURE` is a real materiality answer.
- **THE EXISTING ARCHITECTURE ALREADY ANSWERED HALF THE DISAGREEMENT QUESTION,
  AND THE RUBRIC RECORDS THAT RATHER THAN REINVENTING IT.** The resolver refuses
  when more than one current assessment matches a scope, so two open answers
  cannot both be current and **while a disagreement is open the honest state is
  the ABSENCE of an assessment**. Supersession already retains the earlier
  review. What is not representable is disagreeing **without** superseding. Two
  reviews are never averaged.
- **SOFTWARE MAY ASSERT EXACTLY ONE STATE.** `NOT_ESTABLISHED`, because *no
  document in this review's basis addresses this question* is a checkable claim
  about the corpus. Every other state judges whether what IS documented is
  ENOUGH, and that is the reviewer's.
- **THE WIKIMEDIA REVIEWER HAD ALREADY WRITTEN `HISTORICAL_MUTABILITY` DOWN,
  UNPROMPTED.** The dimension was derived here from TED's open correction
  question, and the 0.65 review's stated limitation had named the same property
  months earlier for a different source. That is corroboration the dimensions are
  real rather than invented -- **bounded honestly**, since both reviews share a
  reviewer and it is not independent replication.
- **BOTH HISTORICAL ASSESSMENTS ARE `PARTIALLY_REPRESENTABLE` AND UNCHANGED.**
  TED's rationale reaches three of five dimensions, Wikimedia's four. Neither was
  re-reviewed, re-scored or used to derive an anchor, and **a review performed
  before a rubric existed is not made invalid by the rubric arriving.**
- **`RELIABILITY_RUBRIC_PROVENANCE_MODEL_GAP`, recorded and not repaired.** No
  column names the procedure that produced a value, and **the basis table is not
  the answer** -- a basis row names a retrieved document ABOUT THE MEASUREMENT,
  and filing the rubric there would inflate every future assessment's documentary
  basis with a document that says nothing about the publisher. The narrowest
  repair is two nullable columns written only by new assessments and **never
  backfilled**. It restricts rather than breaks reproducibility, which is why it
  is a secondary finding: a completed worksheet still lets a second reviewer
  follow the reasoning, and what is lost is the ability to ASK THE DATABASE.
- **A RUBRIC IS NOT A CALIBRATION.** `REFERENCE_PROFILE_V1` stays `UNCALIBRATED`.
  The rubric governs how a human assesses a reliability INPUT; Mission 1.37's
  strategy governs how aggregation parameters would be fitted.

**The next action is a HUMAN REVIEW of the TED convergent scope under this
rubric, and Mission 1.42.1 was deliberately not started.** The worked example
ships with factual findings under all five dimensions, one software-assigned
`NOT_ESTABLISHED`, four material-unknown questions, and **every judgement field
blank**. If the completed rubric concludes `NUMERIC_JUDGEMENT_NOT_JUSTIFIED`, the
scope keeps no assessment and the six Evidence rows stay `NON_SCORABLE`.

### A scope broader than the mission that prompted it

Added in 1.72 (Mission 1.42, `mission-1.42-report.md`,
`second-pilot-convergent-reliability-review-packet-v1.md`).
**`READY_FOR_SECOND_PILOT_RELIABILITY_REVIEW`**: the question prepared, no
judgement supplied, **0 assessments created**.

    expected  4 Evidence rows / 2 Claims        live  6 rows / 4 Claims
    reliability scopes  1, and it is the expected five-part one
    resolver  NO_APPLICABLE_ASSESSMENT          leak checks  6 run, 0 leaks

- **A COUNT DIFFERENCE IS NOT A SCOPE DIFFERENCE, and the distinction decides the
  outcome.** §30 C is drift *if the live Evidence rows do not match the expected
  five-part scope*. They match it exactly. What differs is how many rows sit
  INSIDE that one scope, because **a reliability scope carries no classification
  division and no currency** -- so it reaches the SEK claim and the
  **division-90** claim as well as the two multi-Evidence division-92 ones.
  Mission 1.40 recorded the same property from the other side, when the existing
  TED assessment bound to the new division-92 DETAILED claim.
- **THE OPERATOR IS THEREFORE BEING ASKED A WIDER QUESTION THAN THE BRIEF
  DESCRIBED, AND IT IS SAID WHERE THEY WILL READ IT.** One judgement binds six
  rows across four Claims and two CPV divisions, and the division-90 Claim's only
  witness is the Signal derived in Mission 1.15.10, **before the second pilot
  existed**. A mission that quietly delivers a wider corpus than its brief
  described has changed the question without saying so.
- **THE NEAR MISS IS THE WHOLE TEST.** The existing TED `0.5` shares
  `source_id`, `resource_id`, `record_kind_id` **and** `claim_type: OBSERVED`
  with the scope under review -- four of five, and the fourth discriminates
  nothing because every Evidence row here is OBSERVED. The single differing field
  is `proposition_kind`, and that alone is sufficient: exercised through the REAL
  resolver in both directions, and confirmed by six leak checks that vary only
  that field and hold every other byte identical.
- **NOTHING NEW WAS RETRIEVED, BECAUSE NOTHING NEW WAS NEEDED.** The convergent
  proposition reads the same BT-161 field of the same notices through the same
  route. Three of the four held basis rows are **REUSED**, and the field
  repository is MORE load-bearing than before: the companion currency field is
  what makes a currency-pure cohort expressible at all.
- **BT-195-BT-198 IS `PARTIALLY_APPLICABLE`, WHICH IS A REAL THIRD ANSWER.** The
  FACT that a result value may be lawfully withheld is unchanged; its **weight**
  is not. Under the detailed claim withholding bounds what a named cohort
  represents; under an existential it cannot falsify the claim at all. How much
  that matters is the reviewer's call, and the packet says so rather than
  deciding it.
- **FOUR RELIABILITY QUESTIONS ARE GENUINELY NEW, AND NONE HAS A DOCUMENTARY
  ANSWER.** An existential is **monotone** -- once a qualifying cohort is
  published, no later notice can falsify it -- and whether that makes the
  proposition more dependable or merely **harder to falsify** is a judgement, and
  they are not the same thing. It carries no period, because H-37 leaves TED's
  publication-date semantics unestablished. It asserts about a CLASS. And **two
  cohorts are asserted to witness one proposition**, an SROS step that does not
  exist for the detailed claim.
- **THE LARGEST RESIDUAL UNKNOWN HAS NO DOCUMENT AND NO MITIGATION**: whether TED
  permits a published BT-161 to be corrected or amended, and whether a corrected
  notice supersedes an earlier one. It bears directly on whether a witnessing
  cohort still witnesses, and it is recorded as OPEN rather than reasoned around.
- **ENGINEERING VALIDATION IS RECORDED SEPARATELY AND REFUSED AS BASIS.** Mission
  1.41 reproduced the division-90 Signal semantically, Mission 1.39 proved the
  convergence contract through the real repository, and the currency and scope
  guards are tested. All of it establishes that the implementation does what its
  specification says and **nothing** about how dependable TED's source-reported
  amounts are. **Currency grain being correctly bounded does not imply
  reliability**, and **`DISJOINT` observation overlap does not imply
  independence** -- UNKNOWN on all six rows with 0 groups. Rewarding the system
  numerically because its own tests pass is the error the separation exists to
  prevent, and a test asserts no candidate basis row is one of our own missions.
- **NO NUMBER APPEARS IN ANY JUDGEMENT POSITION.** Every judgement field is
  `null` or empty, seven confirmations are unchecked, the scale is `[0.0, 1.0]`
  with **no threshold labels**, and the reviewer is not inferred from a git
  author, a PR author, an OS username, the existing assessment or the
  conversation. The scan strips `$comment` and `$note` keys at any depth, because
  a rule may name the values it forbids and a field may not -- the
  `testing-strategy.md` §23 shape, met for a fifth time and handled structurally.
- **NOTHING MOVED.** 0 assessments, 0 basis rows, 0 network requests, 0 model
  calls, 0 independence groups. `scoring.evidence.reliability` is NULL on all 39
  rows before and after, because reliability binds late. `REFERENCE_PROFILE_V1`
  is still `UNCALIBRATED`, both multi-Evidence Claims are still `UNAVAILABLE`,
  and Problem-Family is still PARKED.

**The next action is a HUMAN decision, and Mission 1.42.1 was deliberately not
started.** If the operator answers **NO**, the scope keeps no assessment, the six
rows stay `NON_SCORABLE`, and corpus expansion continues without inventing a
value -- **NO is a real answer to *do I have enough information*.** If the
operator answers **YES** and supplies a reliability, a reviewer, a rationale and
a stated limitation, **Mission 1.42.1 -- Second Pilot Operator Reliability
Decision V1** may persist exactly one assessment and then run the first real
scorable multi-Evidence diagnostic.

### A key that does not contain what its docstring calls load-bearing

Added in 1.71 (Mission 1.41, `mission-1.41-report.md`).
**`PROCUREMENT_COHORT_GRAIN_REPAIRED_REAL_MULTI_EVIDENCE_CREATED`**, with
`REAL_MULTI_EVIDENCE_AGGREGATION_UNAVAILABLE_MISSING_RELIABILITY` beside it.

    Claims with >1 Evidence   0 -> 2        max Evidence per Claim   1 -> 2
    network acquisitions      0             new ReliabilityAssessments 0

- **TWO DEFECTS OF ONE SHAPE, AND BOTH WERE A DOCSTRING DISAGREEING WITH ITS
  CODE.** The cohort key called currency and amount scope *load-bearing* and
  contained neither. `_persist_evidence` said *"Idempotent on `(workspace_id,
  claim_id, signal_id)`"* and the query added `AND extraction_method`. Real data
  found both; fixtures had not.
- **THE VALIDATION SETTLED THE SEMANTIC QUESTION.** `derive` refuses a cohort
  unless `len(currencies) == 1` and `len(scopes) == 1`. **A dimension the
  validation demands be equal is part of what makes a cohort comparable**, so the
  implementation was wrong rather than the documentation. The refusal was right;
  its GRANULARITY was not -- two currencies are never one distribution, which
  argues for two cohorts and not for discarding both.
- **ADDING A FIELD TO A GROUPING KEY CAN ONLY SPLIT, NEVER MERGE**, which is why
  the bump is MINOR. Every cohort that derived before had one currency and one
  scope by construction. **Verified rather than argued**: the historical
  division-90 Signal re-derived from its exact inputs with magnitude, currency,
  direction, amount types, amount scopes and classification codes **all
  identical**, and its three inputs still forming one group.
- **SIGNAL UUID EQUALITY WAS NOT REQUIRED, AND SAYING SO MATTERS.** The extractor
  version participates in deterministic identity, so a legitimate bump moves the
  id. What must not move is what the observation MEANS.
- **A NEW PROCEDURE VERSION OVER UNCHANGED MEMBERSHIP IS HISTORICAL VERSIONING,
  NOT A SECOND OBSERVATION.** Re-deriving window B's unchanged EUR cohort would
  have produced a new Signal for the same witness, so it was **skipped and
  reported**. Manufacturing witness multiplicity is the one thing a mission
  chasing a multi-record Claim must not do.
- **EVIDENCE IDENTITY IS EPISTEMIC; THE PROCEDURE IS PROVENANCE.**
  `extraction_method` is still written and still read; it no longer decides
  whether a relation is new. That is the same distinction ADR-035 drew between
  proposition identity and witness identity, one layer down.
- **A CHANGED ASSESSMENT IS NEITHER UNCHANGED NOR A SECOND OBSERVATION, AND NO
  THIRD ANSWER WAS INVENTED.** A row disagreeing on a load-bearing factor is
  reported as a conflict and **nothing is written**: the historical values
  survive, and representing a legitimate revision needs a model this architecture
  does not have. Inventing one while fixing a duplicate is how a fix becomes the
  next defect.
- **NO FX CONVERSION, ANYWHERE.** Currency stays source-native and different
  currencies became different cohorts. A test asserts the extractor contains no
  conversion helper.
- **DISJOINT RECORDS ARE NOT INDEPENDENT EVIDENCE.** Both Claims' witnesses have
  `DISJOINT` observation membership and `independence_state = UNKNOWN`, with **0
  independence groups**. Two publication windows are temporal separation, not
  epistemic independence.
- **THE AGGREGATOR RECEIVED TWO AND THE GROUPING ARITHMETIC DID NOT RUN.**
  `raw_evidence_count = 2`, `scorable = 0`: the convergent proposition kind has
  no applicable assessment, and non-scorable items are excluded before grouping.
  So `max(members)` did not see two members here. Reporting the structural path
  without a `q` is the honest reading.
- **THE AUDIT ITSELF HAD A DEFECT.** `multi_evidence_claims` was computed over
  SCORABLE units, so it reported **0** while the corpus held two real
  multi-Evidence Claims whose reliability is unresolved -- exactly the shape a
  second pilot produces, and exactly the counter this arc tracks. Scorability is
  now a separate counter.
- **THREE PRE-EXISTING TESTS ASSERTED THAT NO CLAIM HAS TWO EVIDENCE ROWS**, and
  this mission made that false, which is what it was for. Re-pointed rather than
  deleted: **a test asserting 0 forever is a test asserting the project never
  progresses.**

**Next is Mission 1.42 -- Second Pilot Convergent Evidence Reliability Review
Preparation V1**, for the exact new scope
`ted-eu | notices/eforms-contract-and-award | procurement_notice | OBSERVED |
source_published_classification_value_contrast_witnessed`. Both multi-Evidence
Claims are `UNAVAILABLE` for precisely that reason. **Prepare the question and
let a named person answer it.** Two multi-record Claims are two: still no
contradiction case, no established independence, no temporal claim, and no
scorable multi-record Claim at all.

### A cohort key that does not contain what its docstring says

Added in 1.70 (Mission 1.40, `second-pilot-ted-category-selection-v1.json`,
`mission-1.40-report.md`). **`SECOND_PILOT_REAL_MULTI_EVIDENCE_NOT_OBSERVED`**:
the second pilot exists, the acquisition ran to plan, and the corpus still has
**0 Claims with more than one Evidence row**.

    window A   CONTRACT_AWARD_NOTICE   REFUSED   mixes EUR, PLN
    window A   CONTRACT_NOTICE         REFUSED   mixes DKK, EUR
    window B   CONTRACT_AWARD_NOTICE   derived   14 records
    window B   CONTRACT_NOTICE         REFUSED   mixes CZK, EUR, SEK

- **THE CONVERGENCE CONTRACT WAS NEVER THE BLOCKER.** It was never reached with
  two witnesses to test it. Nothing about Mission 1.39's V1 was patched, and §41
  required testing it as frozen.
- **THE EXTRACTOR'S COHORT KEY DOES NOT CONTAIN WHAT ITS DOCSTRING SAYS.**
  `group_key`'s docstring names *notice class, amount scope, currency and CPV
  division*, each "load-bearing". The key actually built is
  `source_id | record_kind_id | resource_id | notice_class | cpv_division`.
  **Amount scope and currency are absent**, validated after grouping, and they
  refuse the WHOLE cohort: *"this cohort mixes ['EUR', 'PLN']. Two currencies are
  never one distribution."* The refusal is right; its GRANULARITY is what cost
  the mission. Division 92 across the EU is currency-heterogeneous, so three of
  four real cohorts died on it.
- **HAD CURRENCY BEEN A GROUPING DIMENSION, THIS MISSION WOULD VERY LIKELY HAVE
  SUCCEEDED** -- and that is precisely why it was NOT fixed here. Changing a
  grouping key after seeing which data it rejected is the shape §37 and §41 both
  refuse, and the repair belongs to a preregistered mission that also proves the
  historical division-90 Signal still derives identically.
- **A DUPLICATE EVIDENCE ROW WAS CREATED BY THIS RUN AND REMOVED.** Re-running
  interpretation over the pre-existing division-90 Signal wrote a SECOND Evidence
  row on its existing Claim, differing only by interpreter version
  (`@1.1.0` -> `@1.4.1`). Same Signal, same cohort, same witness. That is §13's
  forbidden case verbatim -- *same Signal/Claim relation, interpreter version
  bump* -- and Mission 1.32's known defect, the Evidence idempotency key embedding
  `extraction_method`. **It briefly made the corpus report a FALSE
  `claims with >1 evidence: 1`**, which a later calibration mission would have
  taken for real data. Removed after checking the FK closure; the original row
  was kept. **The duplicate-witness guard did not prevent it**, because it
  protects the convergent path and this was the detailed one.
- **AN OFFICIAL LABEL IS FETCHED ONE CONCEPT AT A TIME.** A division table
  extracted in one pass from the EUR-Lex HTML of Regulation 213/2008 was
  internally inconsistent -- `90000000-8` against this repository's own
  division-90 check digit, and `92000000` labelled *"Miscellaneous services"* --
  so it was refused and every candidate was verified individually against
  `publications.europa.eu/resource/authority/cpv/cpv/<code>`. **Plausible-looking
  output carrying an official label is worse than no output.**
- **THE RELIABILITY SCOPE CARRIES NO CLASSIFICATION DIVISION**, so the existing
  TED assessment **binds to the new division-92 DETAILED claim** exactly as it
  binds to division 90's. It does **not** bind to either convergent claim, because
  `proposition_kind` differs, and `NO_APPLICABLE_ASSESSMENT` is correct. No new
  assessment was created.
- **A COUNT THAT CAN LEGITIMATELY GROW IS DEPLOYMENT STATE.** Two Mission 1.37
  tests pinned `{'reliability': 19}` and `claims == 28`. The corpus legitimately
  grew, so both were repaired to assert the PROPERTY -- reliability limits EVERY
  scorable claim, and claims still equal evidence rows -- rather than the
  incidental number. Same repair as Missions 1.31.1, 1.32 and 1.38.

**Next is Mission 1.41 -- Procurement Cohort Currency Grain Repair V1**, narrow
and upstream of everything else. It must decide whether the key or the docstring
is wrong, prove the historical division-90 Signal still derives identically if
the key changes, and repair the interpreter-version duplicate, which has now
bitten twice. **Do not re-pick the category or the windows**: division 92 is
frozen and still correct, and what failed is a grain in the extractor.

### Proposition identity and witness identity are different kinds of fact

Added in 1.69 (Mission 1.39, ADR-035, `proposition-convergence-contract-v1.md`).
**`PROPOSITION_CONVERGENCE_CONTRACT_READY`**: two genuinely distinct observations
can support one Claim, **0 live rows changed**.

    PROPOSITION IDENTITY FACTS   what exact assertion is this Claim?
    WITNESS OBSERVATION FACTS    which observation demonstrates that assertion?

- **THE TEST, APPLIED FIELD BY FIELD.** If changing field F changes **what** the
  Claim asserts, F is proposition identity. If changing F only changes **which**
  observation witnesses the same assertion, F may be witness identity. A
  convergence-enabled proposition kind declares both sets, they must be disjoint,
  and a fact classified as **neither is refused** -- the key is built from
  whatever is in the mapping, so a fact nobody placed is a fact that decides.
- **A WITNESS FACT IS NOT DISCARDED. IT STOPS BEING AN IDENTITY.** `notice_ids`
  leaves the key and stays on the Signal, on the Evidence and in provenance; a
  test recovers both cohorts from the persisted signal scopes.
- **THE PERSISTENCE LAYER WAS NEVER THE BLOCKER**, which Mission 1.38 established
  and this confirms by using it unchanged.
- **OBSERVED CONVERGENCE IS LEGITIMATE, AND NARROW.** An existential over a
  publication passes `claim-epistemic-semantics-v1.md` §2's own question -- *does
  a source report this, such that a person could go and read it there?* -- and §3's
  truth condition, since the claim stays true if the source was wrong. The broader
  proposition is **entailed by** the detailed one and asserts less, which is why
  it is a NEW proposition kind and `notice_ids` remains identity on the old one.
- **THE CONSTRUCTOR ENFORCES THE TWO BOUNDARIES.** A non-`OBSERVED` contract is
  refused, so the INFERRED layer this contract records as deliberately unbuilt
  cannot be built by accident; and a contract without `source_id` in identity is
  refused, because attribution is part of an OBSERVED proposition. The source
  boundary enum has ONE member, `SAME_SOURCE_AND_RESOURCE` -- a cross-source
  member nobody may pass would be an invitation.
- **THE EXISTING TEMPLATE'S OBJECTION WAS ANSWERED, NOT IGNORED.** Its docstring
  says *"a proposition that cannot say WHICH notices is not checkable, and one
  that omits its bound reads as a fact about a market"*. Both are right.
  **Checkability MOVES** to the witness, reachable through Evidence -> Signal ->
  signal_inputs -> normalized_records. **The bound stays in the wording**: the
  statement carries *"at least one bounded set"*, and the contract refuses to be
  constructed with an empty `does_not_establish`.
- **CONVERGENCE IS NOT INDEPENDENCE, AND THE TWO VOCABULARIES SHARE NO MEMBER
  NAME.** `DISJOINT` says two witnesses read different records; they can still
  share the publisher, the collection mechanism, the methodology and the
  population. **A test caught the collision**: `ObservationOverlap` was drafted
  with `UNKNOWN`, which `EvidenceIndependenceState` already has, and two
  vocabularies sharing a member name is how a mapping between them gets written by
  accident. Renamed `UNESTABLISHED`.
- **`max(members)` FINALLY HAS A CHOICE TO MAKE.** Independence stays `UNKNOWN`,
  so the conservative rule collapses both witnesses into ONE group with TWO
  members, and saturation still receives one group. **That is correct rather than
  a shortfall**: two witnesses of unestablished provenance raise observed volume,
  not evidence strength, and it must never be reported as corroboration.
- **A REVISION IS A CHANGED ASSERTION, NOT ADDITIONAL SUPPORT.** Two Evidence
  rows, one Claim, **one revision**. Replaying a Signal adds nothing.
- **NOTHING HISTORICAL MOVED.** `proposition_key` was not touched -- convergence
  computes the same hash over a smaller mapping, which is what a different fact
  set has always produced. No historical template changed and **no historical
  proposition kind gained a contract**: convergence is opt-in per kind, which is
  why Docker, Podman and Kubernetes still have three distinct keys.
- **NOT WIRED INTO THE PRODUCTION JOB.** No Signal in this deployment can witness
  two Claims, so the double-counting boundary is enforced by absence rather than
  by a rule. One Signal witnessing both a detailed and a broader Claim is
  permitted ACROSS Claims and never WITHIN one.
- **SYNTHETIC DATA TESTS ARCHITECTURE.** Every fixture went into a disposable
  workspace, the reliability values were `0.4` and `0.7` precisely so nobody can
  mistake them for the reviewed `0.5` and `0.65`, and the calibration feasibility
  audit is **byte-identical**: still zero multi-Evidence Claims in the live corpus.
  **Only real research rows can change calibration feasibility.**

**Next is Mission 1.40 -- Second Pilot TED Category Multi-Evidence Acquisition
V1**, which reopens the second-pilot path without returning to Docker. It must
retrieve the official CPV taxonomy before selecting a category: Mission 1.33
recorded that the collector deliberately expands no CPV code into a label, and
Mission 1.39 deliberately did not choose one.

### A Claim is isomorphic to its Signal, and that is why nothing aggregates

Added in 1.68 (Mission 1.38, `second-pilot-selection-v1.json`,
`mission-1.38-report.md`). **`MULTI_EVIDENCE_CLAIM_ARCHITECTURE_GAP`**: no second
pilot selected, **0 acquisitions**, every canonical counter unchanged.

    persistence:  looks up by proposition_key, attaches evidence  ->  supports N
    interpreter:  source_id + measurement identity + period labels ->  always 1

- **MISSION 1.37 FOUND THE SYMPTOM; THIS IS THE CAUSE.** One Evidence per Claim
  is not an accident of the corpus. Every implemented interpretation is a
  ONE-TO-ONE RESTATEMENT of one Signal, so a Claim is isomorphic to its Signal by
  construction.
- **THE STORAGE LAYER IS NOT THE BLOCKER.** `_persist_one` in
  `claim_repositories.py` looks a draft up by `proposition_key` and, when a claim
  exists, calls `_persist_evidence` against that claim id. The database, the
  repository and the aggregation framework are all written for N -- framework §1
  asks *"Given several Evidence records bearing on one Claim"*.
- **CONVERGENCE IS ONE FACT AWAY, AND THAT FACT IS THE MEASUREMENT.** All seven
  templates carry `source_id` plus the measurement's own identity (`content_id`
  and `audience_class`; `metric_id` and `geography_source_code`; `community_site`
  and `community_tag`; `term` and `gram_size`; `notice_ids` and
  `classification_codes`) plus the period labels. Measured over the live corpus:
  **28 Claims, 28 distinct keys, the closest pairs differ by EXACTLY ONE fact,
  and in twelve pairs it is `content_id`** -- Docker, Podman and Kubernetes on
  the same day. Removing it would merge them.
- **HALF THE BEHAVIOUR IS CORRECT AND MUST NOT BE REPAIRED.** For an OBSERVED
  claim, **attribution IS the claim** (Mission 1.13.1). *"Wikimedia counted X"*
  and *"Stack Exchange published Y"* are two different propositions, and merging
  them across sources would be wrong rather than merely permissive. **Deleting
  `source_id` is not the fix.**
- **THE TWO STACK EXCHANGE TEMPLATES HAVE IDENTICAL KEY SHAPES** and differ only
  in the `proposition` value itself -- two propositions by deliberate design,
  which is the same fact Mission 1.36 recorded from the reliability side.
- **IDENTITY WAS NOT WEAKENED TO AVOID THE OUTCOME.** The concrete convergence
  that should be possible -- two DISJOINT TED notice cohorts in one CPV division
  and period, each independently establishing that division-X totals differ --
  needs `notice_ids` AND `classification_codes` removed from the facts. §8
  forbids that, and doing it while also acquiring would be designing the Claim
  after seeing which records would conveniently merge.
- **ONLY FOUR OF 29 SOURCES ARE COLLECTABLE**: `gdelt`, `stack-exchange`,
  `ted-eu`, `wikimedia-pageviews`. Twenty-two are blocked at the eligibility
  gate, **including every consumer, gaming, creator and app-store route** a
  domain-diversity preference would reach for. Governance is a hard stop: no
  scraping workaround, no unofficial mirror, no anti-bot circumvention.
- **THE CANDIDATE PATTERN IS THE FINDING.** The two candidates that pass taxonomy
  and governance fail on the architecture. The two that pass the architecture
  check fail on taxonomy -- Wikipedia categories are editorial and excluded by
  name, and a term is not a category (Mission 1.35). The candidate with the best
  diversity is governance-blocked. A second developer tool is refused by §1 and
  §6: it is already collected and contributes nothing.
- **A CPV DIVISION MAY NOT BE NAMED FROM MEMORY.** Mission 1.33 recorded that the
  collector deliberately expands no CPV code into a label, so selecting a
  division for its DOMAIN requires retrieving the official CPV table first.

**Next is the narrowest proposition-identity repair, before any acquisition.** It
must decide whether a bounded existence-or-contrast proposition over a
source-native class is a legitimate `OBSERVED` claim or needs the `INFERRED`
layer this contract records as deliberately unbuilt; which identity fields may be
omitted **without letting unrelated observations collapse**, as a rule rather
than per template; how two Evidence rows over an OVERLAPPING population are
marked, given that a second measurement over one corpus is not a second finding
(Mission 1.32); and whether the convergence rule can stay deterministic and
source-bounded, since embeddings, similarity and model equivalence are forbidden
for it. **Do not return to Docker, and do not re-run the pilot selection until
the contract exists** -- the matrix would come back identical.

### The aggregation layer has never aggregated, and that is the calibration blocker

Added in 1.67 (Mission 1.37, `evidence-aggregation-calibration-strategy-v1.md`,
`calibration-feasibility-audit-v1.json`, `mission-1.37-report.md`).
**`CALIBRATION_STRATEGY_READY_REFERENCE_DATA_MISSING`**: a preregistered
methodology, and no reference data to run it on. **0 parameters fitted, 0
profiles calibrated, 0 model calls, 0 acquisitions.**

    28 Claims  ->  28 Evidence rows  ->  distinct evidence-count-per-claim = [1]

- **EVERY CLAIM HAS EXACTLY ONE EVIDENCE ROW.** Measured, not assumed. So the
  saturation operator has never combined two groups on real data, independence
  collapse has never collapsed anything, `group_strength = max(members)` has
  never had more than one member, contradiction accumulation has never run, and
  three of the four masses have only ever taken their `c = 0` values. **The
  mechanisms calibration would fit have no real-data exercise at all.**
- **`min()` IS CURRENTLY INDISTINGUISHABLE FROM `return reliability`.** Relevance,
  directness and extraction confidence are `1.0` on every Evidence row, and every
  Claim is `EVERGREEN` so freshness is `1.0` too. A composition rule cannot be
  tested against data in which only one input ever varies.
- **THE TARGET VARIABLE HAS TWO VALUES AND BOTH ARE REVIEWED RELIABILITY
  VALUES** -- `0.5` once and `0.65` eighteen times -- and `reliability` is the
  limiting component on **19 of 19** scorable claims. Mission 1.36.1's echo
  hazard is therefore not a risk to guard against here; it is the entire dataset.
  Applying the leakage rule `(reliability_scope, proposition_kind, subject_key)`
  yields **2 groups among 19 units**, which cannot be split into development and
  holdout, and that is a fact about the corpus rather than an argument for
  weakening the rule.
- **THE MISSION 1.1 CALIBRATION PLAN PROPOSES THE WRONG TARGET.** Its §5 asks
  *"Do claims scoring 70-80 resolve favourably more often than those scoring
  30-40? Reliability diagram plus a Brier-style summary"*. That is an
  OUTCOME-RESOLUTION target: it measures the state of the WORLD, and applies a
  probability scoring rule to a quantity the framework calls not-a-probability
  four times. Framework §1: *"Not a truth estimator. Nothing here estimates
  whether the claim is true. Every quantity describes the state of the evidence,
  which is a different kind of thing from the state of the world."* **The plan
  contains its own counter-argument in the same section and keeps the metric
  anyway**, and Mission 1.37 resolves the contradiction in favour of the
  framework. Outcome data is not worthless -- it is the right target for a layer
  that PREDICTS, which is the Opportunity layer, not this one.
- **A SECOND GAP RESTRICTS RATHER THAN BLOCKS.** Nothing in the repository
  anchors the ABSOLUTE scale: `scoring-framework-v1.1.md` §4.1 fixes 0-100 and
  nothing says what makes 65 correct rather than 55. A reviewer has no anchor
  either. So calibration targets the **ORDINAL** construct, which is defined and
  observable -- which of two evidence sets is better supported by its own
  evidence -- and absolute-level calibration is out of scope until the framework
  supplies an anchor. That is why the outcome is not
  `CALIBRATION_TARGET_SEMANTICS_UNDERDEFINED`.
- **BASELINE B-2 DECIDES WHETHER ANY OF THIS IS WORTH DOING.** A reliability
  pass-through reports the reviewed value and ignores every other mechanism. On
  the current corpus it is **numerically identical to the full aggregator on 19
  of 19 scorable claims**. A fitted profile that cannot beat it means the
  aggregation layer adds nothing measurable, and no calibration should be
  claimed.
- **STRUCTURAL IS NOT THE SAME AS HARD-CODED, AND NUMERIC IS NOT THE SAME AS
  FITTABLE.** `min()` and `max(members)` are structural because their
  alternatives are refuted by MEANING; the `repeated_signal_min_groups` floor of
  2 is structural because "repeated" cannot mean one. `multi_source_min_groups =
  3` sits above its floor and IS fittable. **There is no flat contradiction
  penalty to calibrate**, because no such term exists -- contradiction enters
  continuously through `c`.
- **RELIABILITY IS AN INPUT, NEVER A LABEL.** Aggregation calibration consumes
  reviewed reliability and may not refit it. Wikimedia's `0.65` and TED's `0.5`
  are judgements for one measurement-crossed-with-proposition scope each.
- **THREE GATE CONDITIONS ARE BLOCKERS RATHER THAN NUMBERS.** The acceptable
  inter-reviewer agreement, coverage adequacy per dimension, and the margin by
  which a candidate must beat B-2 cannot be quantified before a reviewer pilot.
  §27 and §30 forbid inventing them, and **a gate weak enough for current data to
  pass would not be a gate**. Sample size is
  `SAMPLE_REQUIREMENT_NOT_YET_QUANTIFIED` for the same reason.
- **`TEMPORAL_CALIBRATION_DATA_MISSING`**: 0 temporally sensitive Claims and 0
  carrying a `claim_feature`, so `H` cannot be fitted at all. No universal
  half-life and no Docker half-life; Docker's Claims are `EVERGREEN` and carry
  **zero** information about decay.
- **A GENERATED ARTIFACT THAT MEASURES A DEPLOYMENT CANNOT BE CHECKED IN CI.**
  The four `--check` steps CI runs render repository files into repository files.
  The feasibility audit measures the live corpus, and CI's integration job starts
  from an empty database -- so a check step there would be permanently red or
  loosened until it verified nothing. It ships with a deterministic `--check` as
  an OPERATOR gate. **The same distinction blocks the Mission 1.36.1 backlog item**
  for `build_reliability_review_packet.py`, which reads the database too.

**The next mission is NOT a labelling mission.** The blocker underneath the
missing labels is that nothing has the required shape to label: a reference
judgement about a single-record claim tests reliability pass-through and nothing
else. The precondition is architectural and already permitted -- **two Signals
must interpret to the same `proposition_key`**, which is what puts two Evidence
rows on one Claim. It should arrive with a **second pilot from a substantially
different domain**: not developer tooling, different Evidence families, sitting
in a published product taxonomy (which Mission 1.35 established Docker does not),
with a route to commercial evidence at the right grain. **Chosen for calibration
diversity, never for ease of fetching.**

**D-03 is unchanged.** A strategy is not a calibration, `REFERENCE_PROFILE_V1` is
still `UNCALIBRATED`, and `services/scoring` is still blocked.

### A refusal is recorded as prose, a confirmation is typed, and a value binds late

Added in 1.65, completed in 1.66 (Mission 1.36.1,
`docker-reliability-operator-decisions-v1.md`, `mission-1.36.1-report.md`,
`docker-diagnostic-aggregation-v1.json`).
**`DOCKER_RELIABILITY_PARTIALLY_REVIEWED`**, reached by way of
`OPERATOR_CONFIRMATION_REQUIRED`: the mission stopped at the guard, the operator
typed the confirmation, and **two counters moved while fifteen did not**.

    scope 1  stack-exchange | ...published_questions_carrying_tag   NO  -> no row
    scope 2  stack-exchange | ...questions_without_accepted_answer  NO  -> no row
    scope 3  wikimedia-pageviews | platform_counted_..._change  0.65 HUMAN_REVIEW
                                    -> e2419f13-... v1, and 6 Evidence rows RESOLVE it

- **A NO IS NOT A NUMBER, AND IT IS NOT A ROW EITHER.** The refusal on scopes 1
  and 2 is recorded as **prose**. Not a numeric assessment, not a placeholder,
  not a documentary-only assessment: **a refusal recorded as data would be a
  value**, and the next reader would treat it as one. It does not mean
  `reliability = 0`, `0.5`, low reliability or an unreliable source. It means
  **no human reliability judgement exists**, the reliability stays `NULL`, the
  resolver returns `NO_APPLICABLE_ASSESSMENT`, and the Evidence stays
  `NON_SCORABLE` -- the designed behaviour rather than a gap.
- **THE TTY GUARD IS THE CONTRACT, NOT AN OBSTACLE TO IT.**
  `record_reliability_assessment.py` refuses with *"no terminal to confirm on. A
  reliability assessment is a human decision and this is not a step a pipeline
  runs"*. Supplying the confirmation string from a pipeline would produce a row
  whose `reviewed_by` names a person who did not type it, which is precisely the
  failure the whole reliability contract is built to prevent. **A guard removed
  to make a pipeline pass is a guard that never was**, so the mission stopped and
  printed the command; the operator ran it and typed `record it`. **That is the
  only way the condition is ever satisfied**, and a mission that satisfies it
  itself has not satisfied it.
- **A MISSION MUST NOT REPORT A FUTURE, AND THE PROOF IS HOW LITTLE CHANGED
  AFTERWARDS.** The tests asserted what was true before the confirmation -- that
  nothing resolved, that TED was the only assessment -- and **exactly two
  assertions** had to be re-pointed once it happened. Everything else really did
  stay put. For the same reason **D-03 blocker 2 was OPEN and is now PARTIAL**:
  §19 anticipated PARTIAL, PARTIAL describes the state after confirmation, and
  writing it early would have been writing a future.
- **RELIABILITY BINDS LATE, AND SIX ROWS RESOLVING A NUMBER STORE NONE OF IT.**
  `scoring.evidence.reliability` is `NULL` on all 28 rows before and after
  (ADR-026 Decision 2). The resolver produces the value **and the binding** at
  read time, so a score can name the assessment id and version it used, and a
  copy on the row could outlive the assessment it came from.
- **A CONDITIONAL DIAGNOSTIC IS SKIPPED UNTIL ITS CONDITION IS TRUE, NEVER
  APPROXIMATED.** §15's aggregation is conditional on at least one row becoming
  scorable. While none was, running it over eight `NON_SCORABLE` rows would have
  produced a number computed from nothing. Once six were, it ran --
  `allow_uncalibrated=True`, the real `aggregate()`, one JSON artifact and **no
  database row**.
- **EIGHT EVIDENCE ROWS SIT ON EIGHT DISTINCT CLAIMS**, so the diagnostic is
  eight SINGLE-RECORD aggregations. Reliability resolving does not turn six
  observations of one Wikipedia article into an aggregation, and summing them
  would invent a claim nobody made.
- **THE SCORE IS A RESTATEMENT OF ONE HUMAN JUDGEMENT, NOT A CORROBORATION OF
  IT.** `q = 0.650` on all six with **`reliability` as the limiting component**,
  because `q = min(components)` and relevance, directness, extraction confidence
  and freshness are all `1.0`. The same shape Mission 1.15.13 found for TED at a
  different number. **Level stayed 1**: the blocked reasons are *2 supporting
  groups of established independence, found 0* and the `MARKET_ACTIVITY` gate,
  and reliability reaches neither. The two refused scopes report `UNAVAILABLE`
  with `uncertainty_mass` **1.0**, which is the honest reading of *nobody
  judged*.
- **`0.65` BELONGS TO ONE SCOPE.** Six Evidence rows matching it do not make it a
  Docker coefficient: no average reliability, no overall Docker reliability, no
  mean Evidence Score, no *Docker confidence*, no *Docker 65%*. Scopes 1 and 2
  remain **unknown, and unknown is not a low number**. It carries **no label** --
  the contract defines no threshold vocabulary, so it is not *good*, *medium*,
  *high* or *65% confident*. It calibrates nothing (`REFERENCE_PROFILE_V1` stays
  `UNCALIBRATED`) and establishes no independence (`UNKNOWN` on all 8 rows, 0
  groups), which continues to cap evidence levels for reasons reliability cannot
  touch.
- **THE NEGATIVE CHECK WAS RUN RATHER THAN ASSUMED.** The real resolver was
  offered the TED assessment against each of the three Docker scopes: **3 checks,
  0 leaks.** Worth running because TED **shares `claim_type: OBSERVED` with all
  three** -- every Evidence row here is OBSERVED, so that field discriminates
  nothing and is exactly where a leak would start if matching were ever partial,
  nearest or fuzzy.

**MISSION 1.36 SHIPPED A REAL DEFECT AND THIS MISSION FOUND IT BY TRYING TO USE
ITS OUTPUT.** The packet's `candidate_basis_rows` carried `basis_type` values --
`OFFICIAL_METHODOLOGY`, `FIRST_PARTY_RESPONSE_AT_COLLECTION`,
`FIRST_PARTY_MODEL_SEMANTICS` -- that are **not members of
`ReliabilityBasisType`**, so the constructor raises on all three and the rows the
packet prepared **could not have recorded an assessment**, which is the one thing
candidate basis rows are for. Nothing caught it because the packet is a JSON
document and the enum lives in the contracts package. Repaired against the one
precedent, the TED assessment: a document defining **how** a measurement is
computed is `MEASUREMENT_METHODOLOGY`, one recording **what can go wrong** is
`KNOWN_LIMITATION`, one recording how a corpus was assembled is
`CORPUS_CONSTRUCTION_METHOD`. And `authoritative_documents[].basis_type` became
**`document_kind`**, because that field is a narrative list of what was read --
**including a document that was NOT read** -- and reusing the contract's field
name for it is what made an invalid value look valid. A test now checks every
candidate row against the enum.

**A THIRD DEFECT SURFACED, AND ONLY BECAUSE A ROW FINALLY RESOLVED.**
`report_docker_reliability_resolution.py` read `binding.assessment_version`; the
attribute is `version`. Every binding was `None` while nothing resolved, so the
branch was unreachable and the wrong name sat there looking fine -- **the same
shape as Mission 1.36's invalid basis types: code that could not have worked,
unnoticed because the path was never taken.** Two of this mission's three defects
were of that kind, which is the pattern worth carrying forward: **a branch no
data has ever entered is not tested by a passing suite.**

**Next is Mission 1.37 -- Evidence Aggregation Calibration Strategy V1, and its
premises now hold**: a functioning reliability framework, two `HUMAN_REVIEW`
assessments, real scorable Evidence, and an explicitly uncalibrated profile. The
diagnostic above is the argument for it rather than a substitute: six claims
score `0.650` through equations whose constants were never fitted. Calibration
must rest on reference or outcome data, never on guessed constants. Afterwards,
**pick a second pilot subject from a different domain** -- Docker must not be the
only long-term benchmark, and Mission 1.35 found the reason it is a poor one.
**Do not spend another mission forcing Stack Exchange reliability**: the operator
decided the available documentation is insufficient, and the publisher's pages
are unreachable because the site's robots policy blocks the crawler.

### A reliability scope is counted, never assumed, and the number is not software's

Added in 1.64 (Mission 1.36, `docker-evidence-reliability-review-packet-v1.md`).
**`READY_FOR_OPERATOR_RELIABILITY_REVIEW`**: the question prepared, no judgement
supplied, **0 assessments created**.

    8 Docker Evidence rows  ->  3 reliability scopes  ->  0 reviewed values
    stack-exchange | questions/stackoverflow | community_question | OBSERVED
        community_site_published_questions_carrying_tag        1 row
        community_site_questions_without_accepted_answer       1 row
    wikimedia-pageviews | metrics/pageviews/per-article/... | content_request_count
        platform_counted_content_request_change                6 rows

- **THREE SCOPES, NOT TWO, AND THAT IS THE SUBSTANTIVE RESULT.** Two source
  families invite the assumption of two scopes; §0 forbids it and counting
  refutes it. The two Stack Exchange signal types share `source_id`,
  `resource_id`, `record_kind_id` and `claim_type` -- **four of five** -- and
  persist DIFFERENT `proposition_kind` values, so *how many questions carry this
  tag* and *how many carry it without an accepted answer* are two reliability
  questions. Splitting them was not a choice: the persisted discriminators
  differ.
- **`signal_type_id` is not part of scope identity.** Whether the interpreter
  read the Signal correctly is `extraction_confidence`, a different field
  answering a different question, and a deterministic extractor reading a Signal
  perfectly says nothing about whether the underlying measurement is dependable.
- **SOFTWARE MAY PREPARE THE QUESTION AND MAY NOT ANSWER IT.** No value, no
  range, no recommendation, no adjective ranking a source appears anywhere in the
  packet, and a test enumerates it to prove that. `reliability: null` means NO
  ASSESSMENT EXISTS -- not 0.0, not 0.5, not *unknown so assume the middle*. The
  scale is `[0.0, 1.0]` with **no threshold labels**, because the architecture
  defines no meaning for 0.9 or 0.7 and a packet that invented one would be
  legislating.
- **AN ASSESSMENT SHARING FOUR FIELDS IS AS INAPPLICABLE AS ONE SHARING NONE.**
  The TED assessment shares `claim_type: OBSERVED` with all three Docker scopes,
  because every Evidence row in this repository is OBSERVED -- so that field
  discriminates nothing on its own and **is exactly where a leak would start if
  matching were ever partial, nearest-match or fuzzy**. All five must match.
- **§16's list of things that are NOT a review**: asking for the mission, having
  accepted a value for another scope before, approving the project, saying
  *continue*, or choosing the pilot subject. Each scope needs its own judgement
  from a named person.
- **A RETRIEVED METHODOLOGY AND AN UNREACHABLE ONE ARE DIFFERENT STATES.**
  Wikimedia's pageview definition was retrieved: a conjunction of HTTP-status,
  host and header conditions with an enumerated exclusion list, and spider
  tagging by *"ua-parser and additional custom regex based identification"* --
  pattern matching, which is what the collector already recorded as heuristic.
  Stack Exchange's is **unreachable** because the site's robots policy blocks the
  crawler; no retry with a varied header, no mirror, no cached copy, no
  third-party summary. **The operator supplying the documents is the route
  Mission 1.18 used and it remains open.**
- **AN ABSENCE OF DOCUMENTATION IS NOT EVIDENCE OF STABILITY.** Wikimedia's
  revision and backfill practice is not documented on the pages retrieved, and
  Mission 1.19's `revised: 0` is one observation rather than a policy. For Stack
  Exchange the central open question is whether an accepted answer can later be
  un-accepted -- which would make scope 2 a count of a moving state.
- **NO is a real answer to *do I have enough information*.** Worksheet question 1
  has a defined consequence: leave the reliability absent, and the Evidence stays
  `NON_SCORABLE`, which is the designed behaviour rather than a gap.
- **A VALUE WOULD NOT CALIBRATE ANYTHING.** Reliability review is not
  calibration. `REFERENCE_PROFILE_V1` stays `UNCALIBRATED`, no Opportunity score
  exists, no ranking happened, and independence stays `UNKNOWN` on all 8 rows
  with 0 groups -- which continues to cap evidence levels for reasons reliability
  cannot touch.
- **FOUR OF FIVE D-03 BLOCKERS REMAIN OPEN**, reported separately so *some
  Evidence became scorable* can never be read as *D-03 resolved*. Blocker 4 --
  an authorised half-life -- is not required by THESE rows because every claim in
  the corpus is `EVERGREEN`, which is a property of this corpus and not a
  resolution.

**A `$comment` is where a RULE is written and a rule may name the values it
forbids; a FIELD may not.** A scan asserting no number appears failed four times
across four missions on exactly the sentences doing the work
(`testing-strategy.md` §23), so the fix was generalised rather than patched again:
`$comment` keys are stripped at any depth before scanning. **A test also caught a
factual overstatement in this mission's own packet** -- it claimed the TED
assessment matched on zero fields when it shares one -- and the document was
corrected rather than the test loosened.

### A term is not a category, and a map is not a taxonomy

Added in 1.63 (Mission 1.35, `docker-commercial-scope-mapping-v1.md`).
**`NO_AUTHORITATIVE_DOCKER_CATEGORY_RELATION_FOUND`**: the capability Mission
1.34 built went looking for its first edge and found none. **0 relations before,
0 after.**

- **THREE DISTINCT FAILURE MODES, and only one could ever be fixed by looking
  harder.** Things that NAME Docker without classifying it; things that classify
  products without containing Docker; and things that classify **what is bought**
  rather than what a thing is.
- **A TERM IS NOT A CATEGORY.** The OCI calls Docker a *container engine* and
  Docker's own docs call it *an open platform for developing, shipping, and
  running applications*. Neither is a classification: a category needs an
  identifier, a publisher who decides membership, and other members. A widely
  used noun phrase has none of the three, so there is nothing to address as a
  broader scope.
- **A MAP IS NOT A TAXONOMY, and the CNCF Landscape says so itself** -- *"a map
  through the previously uncharted terrain"* that *"attempts to categorize most
  of the projects and product offerings"*, with an inclusion rule of **"at least
  300 GitHub stars"**. A popularity threshold tells you a project is well known,
  not what kind of thing it is.
- **AND IT WAS REFUSED ON A FACT BEFORE THE JUDGEMENT WAS NEEDED.** Its
  `landscape.yml` (1,138,659 bytes, 2,512 name fields, 15 categories) names five
  Docker items -- `Docker Swarm`, `Docker Compose`, `Docker Hub`, `Docker (Wasm)`
  and `Docker (member)`, which is the COMPANY -- and **the container platform is
  not an item in it at all**. The other 48 occurrences of the word sit in other
  products' descriptions and integration lists. **You cannot borrow a map's
  category for something the map does not contain**, and the three Docker
  products sit in three different categories, so there is not even a single wrong
  answer available.
- **CPV fails on WHO ASSIGNS A CODE, not on coarseness.** Division `48000000`
  *Software package and information systems* exists. But a contracting authority
  assigns a CPV code to **its own contract**; nobody assigns one to a product and
  no publisher maintains a product-to-CPV mapping. **A CPV class contains
  procurements and never products** -- a tender buying Docker licences is
  classified by what that buyer was buying.
- **The direction of reasoning was the methodology.** The question asked was
  *what authoritative category contains the Docker product?*, never *what
  category would connect Docker to the commercial evidence we already hold?* CPV
  was investigated only after the first question was answered. Reversing the
  order is how a bridge gets built to a destination somebody picked first.
- **The two vocabularies that actually IDENTIFY Docker are the two that carry no
  parent.** Stack Overflow tags are flat; Wikipedia categories are editorial and
  excluded by name. The highest-priority route -- a source-native taxonomy -- had
  nothing to offer.
- **An unreachable source stays UNRESOLVED.** `unspsc.org` returned HTTP 403; no
  retry with a varied header, no mirror, no cached copy, and no model recall
  substituted for a document. Uncertainty is never permission, and it is not a
  finding either.
- **An empty registry now says WHY it is empty.** *Empty because nobody looked*
  and *empty because somebody looked* are different facts, and the registry
  records the second with its reviewer and date.

**Docker was chosen as a pilot because SROS had evidence about it, not because it
was well classified, and those turn out to be different properties.** A future
pilot subject should be chosen partly for sitting in a published classification,
so the multi-scope architecture has something real to hold.

**Next is Reliability / Scoring Eligibility Foundation, chosen explicitly over a
second pilot**: it unblocks scoring for evidence already held, where a second
pilot spends acquisition effort before knowing whether anything can be scored at
all. Do not spend further missions on Docker taxonomy.

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
