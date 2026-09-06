# Mission 1.71 — A bounded HTTP apparatus, designed and not authorised

Generated from `bounded-http-governance-feasibility-v1.json` and the contract records.
Do not edit by hand.

**Governance: `GOVERNANCE_NOT_YET_FEASIBLE_IN_PRINCIPLE_NAMED_DECISIONS_REQUIRED`.**
**Run authorization required: True. Authorised by this mission: False.**

## The governance rubric

| dimension | verdict |
|---|---|
| TARGET_SCOPE | `PASS_IN_PRINCIPLE` |
| NETWORK_SAFETY | `PASS_IN_PRINCIPLE` |
| REQUEST_SAFETY | `PASS_IN_PRINCIPLE` |
| LOAD_SAFETY | `PASS_IN_PRINCIPLE` |
| AUTHENTICATION_BOUNDARY | `PASS_IN_PRINCIPLE` |
| ANTI_BOT_BOUNDARY | `PASS_IN_PRINCIPLE` |
| DATA_MINIMIZATION | `REQUIRES_DEDICATED_POLICY` |
| SENSITIVE_CONTENT_HANDLING | `REQUIRES_DEDICATED_POLICY` |
| ROBOTS_POLICY | `REQUIRES_DEDICATED_POLICY` |
| TARGET_TERMS_HANDLING | `REQUIRES_DEDICATED_POLICY` |
| LOGGING | `PASS_IN_PRINCIPLE` |
| RETENTION | `REQUIRES_DEDICATED_POLICY` |
| OPERATOR_AUTHORIZATION | `PASS_IN_PRINCIPLE` |
| ABORTABILITY | `PASS_IN_PRINCIPLE` |
| AUDITABILITY | `PASS_IN_PRINCIPLE` |
| RUN_REPRODUCIBILITY | `PASS_IN_PRINCIPLE` |

**11 pass in principle, 5 require a dedicated policy, 0 blocked, 0 unknown.** No numerical score.

Why, for each:

- **TARGET_SCOPE** — the boundary is definable and checkable before a request: publicly routable, reachable over ordinary HTTP or HTTPS, and not authentication-protected for the requested resource. A target failing it is refused rather than attempted.
- **NETWORK_SAFETY** — corpus-induced SSRF is a solved engineering problem with a statable contract: resolve, classify every resolved address against the named registries, pin the connection to a validated address, and re-run the whole check after every redirect.
- **REQUEST_SAFETY** — a single deterministic request with no authentication, no cookies, no JavaScript, no form submission and no persistent state is the minimal act, and every capability beyond it is absent from the contract rather than disabled by a flag.
- **LOAD_SAFETY** — the SHAPE closes here: global concurrency, per-host concurrency, per-origin rate, retry count and backoff are all mandatory with no default, and UNBOUNDED is unrepresentable. The VALUES are a run-manifest input and are not invented here, exactly as acquisition-authorization-v1.md §7.3 refuses a job that does not state its size.
- **AUTHENTICATION_BOUNDARY** — no credential, no session, no bearer token and no cookie jar exists in the contract, so an authenticated request is not something the apparatus can be configured into.
- **ANTI_BOT_BOUNDARY** — a 403, a 429 or a challenge page is a TERMINAL OUTCOME and never a trigger to retry with a different header, a different address or a different identity. That is the standing project rule, and here it is also what keeps the measurement honest: a request that succeeded only after the identity changed is a different request.
- **DATA_MINIMIZATION** — what may be RETAINED cannot be settled without the construct, and this is not a side policy: it decides which governance regime applies. Retaining response bodies is the publisher's content; retaining a status line and named headers is closer to a fact about our own request. The two are not the same act and this mission may not choose between them.
- **SENSITIVE_CONTENT_HANDLING** — a public page can return personal data, so retention hooks and redaction are required before any body is stored. Downstream of DATA_MINIMIZATION and undecidable before it.
- **ROBOTS_POLICY** — and it is architectural rather than a setting. A robots-respecting apparatus needs a robots retrieval stage, its own terminal outcome, its own request budget and its own missingness class -- so the decision changes what the apparatus IS. No claim is made here that robots.txt defines permission, or that ignoring it is lawful.
- **TARGET_TERMS_HANDLING** — no corpus exists, so no target terms were inspected and none could be. What the contract supplies is the SLOT: a pre-run exclusion set with a recorded reason per entry.
- **LOGGING** — per-attempt provenance is required by the accounting invariant itself, so logging is not an optional addition.
- **RETENTION** — data-retention-policy-v1.md governs records acquired from a registered source, and these would not be. Which retention applies is part of the same unanswered question as DATA_MINIMIZATION.
- **OPERATOR_AUTHORIZATION** — the repository already has the shape: a frozen document, a content hash, an approval naming that hash, and an execution record kept separate from the approval (Missions 1.56, 1.65, 1.66, 1.66.1). A run manifest reuses it rather than inventing one.
- **ABORTABILITY** — abort is expressible without losing accounting, because every unattempted item takes a terminal state rather than disappearing.
- **AUDITABILITY** — a run binds three hashes and a commit, so what was requested, over what population, under what configuration, is reconstructible after the fact.
- **RUN_REPRODUCIBILITY** — with a distinction that must not be lost: the RUN is reconstructible and the OBSERVATION is not reproducible. Re-running later observes a different world state, and a contract claiming otherwise would be claiming the web is static.

## The dominant finding is not any single row

every arbitrary public target is refused, target by target -- not because a publisher objected, but because nobody asked. That is the gate working, and it is why the corpus directability Mission 1.70 wanted cannot simply be bought inside the current model.

The rules that produce it:

- source-registry-v1.md §1 rule 1: public visibility is not permission
- source-registry-v1.md §1 rule 2: uncertainty is never permission, and silence produces NOT_ADDRESSED rather than a path forward
- source-registry-v1.md §1 rule 8: an approving state needs a GRANT for six named activities on authoritative evidence, and NOT_ADDRESSED on any one blocks
- acquisition-authorization-v1.md §1 rule 5: a source-level approval is not a resource-level one, so each target would be authorised separately

**And the collapse that would follow.** restricting the corpus to targets that DO hold a review means restricting it to the 29 registered sources, which destroys exactly the directability that made the operator route worth designing.

### The mechanism is not novel, and here is the evidence

this repository already performs bounded, identified, one-off HTTP GETs against third parties that hold no source review at all, routinely, under each mission's documentation budget -- Common Crawl's and HTTP Archive's own pages in Mission 1.70, and every apparatus candidate's documentation from Missions 1.59 to 1.68.

*And the distinction that survives it:* the REQUEST is identical and the DESTINATION OF THE RESULT is not. A documentation read informs a human judgement recorded in a mission document. A measurement becomes Evidence under a Claim, at corpus scale. Governance attaches to the second in a way it does not to the first, so the precedent establishes that the act is ordinary and does not establish that the use is governed.

## The named decisions

| id | decision | settled here |
|---|---|---|
| GOV-1 | whether bounded public-HTTP observation over an unreviewed corpus is a governed activity DISTINCT from source collection, and if so under what track | False |
| GOV-2 | ROBOTS_POLICY, chosen from the contract's enumerated values | False |
| GOV-3 | BODY_CAPTURE_POLICY and the retention regime that follows | False |
| GOV-4 | the procedure by which a target enters TARGET_POLICY_EXCLUSION_SET | False |
| GOV-5 | the numeric load bounds | False |

## What the apparatus is, and is not

| | |
|---|---|
| status | `DESIGNED_NOT_ADOPTED` |
| implemented | False |
| adopted into governance | False |
| predicate selected | False |
| independence | `INDEPENDENCE_ARCHITECTURE_PLAUSIBLE` |
| self-operation establishes independence | False |
| independence groups created | 0 |
| second independent route still required | True |

*Two local processes are two independence groups:* **False**. two processes on one machine share code, configuration, vantage, resolver and network path. They are one apparatus run twice, and counting them as two groups would manufacture corroboration out of repetition -- the exact error the aggregator's unknown-provenance collapse exists to prevent.

## The bounded pilot

**`BOUNDED_PILOT_DIMENSIONS_CLOSED_GOVERNANCE_PENDING`.** every dimension that must be bounded is named and mandatory, so the ENGINEERING side closes. What is not closed is the governance shape the run would need, and reporting BOUNDED_PILOT_FEASIBLE_IN_PRINCIPLE would let a reader take a bounded design for an approved one.

| dimension | must be bounded | value chosen |
|---|---|---|
| number_of_targets | True | None |
| requests_per_target | True | None |
| redirect_count | True | None |
| retries | True | None |
| global_concurrency | True | None |
| per_host_concurrency | True | None |
| per_origin_rate | True | None |
| total_run_duration | True | None |
| maximum_bytes | True | None |

## What a counterpart would have to be

| id | requirement |
|---|---|
| C1 | produces its own HTTP observations |
| C2 | the same frozen population, or a population-equivalence contract that is stated rather than assumed |
| C3 | attempt and missingness semantics sufficient to state the same proposition's denominator |
| C4 | a compatible observation window, with a stated temporal object |
| C5 | a compatible deterministic request contract, or documented equivalence |
| C6 | a known measurement lineage, affirmatively stated by the counterpart itself |
| C7 | no shared HTTP observation upstream with the operator apparatus |
| C8 | rights and access feasible for a commercial-purpose local deployment |
| C9 | its values remain unseen until the proposition and threshold are preregistered |

**Counterpart selected: False. Candidates evaluated: 0.**

## The candidate registry rule

`COVERAGE_SEMANTICS_MUST_DISTINGUISH_ATTEMPT_FROM_SUCCESS` — **NOT_ADDED**, registry 15 to 15.

the rule is genuinely useful and this mission's whole missingness contract is built on it. Adding it on that basis would make the registry a list of good ideas rather than a record of failure modes observed twice, which is the property that lets a later mission trust an entry without re-deriving it.
