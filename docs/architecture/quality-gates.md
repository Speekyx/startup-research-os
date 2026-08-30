# Quality Gates

Version: 1.9
Status: Active. Every gate in §1 runs in CI
Date: 2026-08-30 (amended in Mission 1.5)

What must be true for a change to reach `main`. `docs/CLAUDE.md` §Definition of
done is the requirement; this document is the mechanism.

The organising principle: **a rule that is only in a document is a rule that will
be broken.** Every specification obligation that can be moved into a type, a lint
rule, a schema, or a test should be.

---

## 1. Gate summary

| Gate | Tool | Status | Blocking |
|------|------|--------|----------|
| Formatting | Prettier (TS/MD/JSON/YAML), ruff format (Python) | Scaffolded | Yes |
| Lint | ESLint, ruff | Strategy fixed, config pending | Yes |
| Types | `tsc --noEmit`, `mypy --strict` | Config scaffolded | Yes |
| Unit tests | Vitest, pytest | Pending | Yes |
| Contract tests | Schema validation against fixtures | Pending | Yes |
| Integration tests | pytest + testcontainers | Pending | Yes |
| E2E | Playwright | Pending | Nightly, not per-PR |
| Secret scan | gitleaks | Pending | Yes |
| Dependency audit | `pnpm audit`, `pip-audit` | Pending | Warn, then block |
| Diagram/doc sync | Manual (review checklist) | Active | Review |
| Spec compliance | Manual (PR checklist) | Active | Review |

"Pending" means the strategy below is decided and the tool is installed in
Mission 0.2. Nothing in this table is undecided.

### Status as of Mission 0.4

Every gate above now runs. What changed since the table was written:

| Gate | Now |
|------|-----|
| Lint | **Active.** ruff (11 rule families) and ESLint 9 with type-aware rules over `**/*.ts` **and `**/*.tsx`** — the React components are the newest code in the repository and would otherwise be the only code exempt from the architectural rules |
| Types | **Active.** `mypy --strict` over 58 source files; `tsc` over two projects (contracts, web) plus `next build`, which typechecks generated route types the project-level check cannot see |
| Unit / integration tests | **Active.** 225 zero-dependency tests, 370 pytest tests across five packages, 19 TypeScript conformance tests |
| E2E | Still not implemented. There is no user workflow to walk through |

### Gates added in Mission 0.4

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Tenant isolation, two workspaces** | `services/gateway/python/tests/test_rls.py` | A query with no `WHERE workspace_id` returns only the current tenant's rows. This is the one gate that catches a *forgotten* filter rather than a wrong one (ADR-012) |
| **Pooled-connection tenant leak** | Same suite, single-connection pool | A session-level `SET` would leak a tenant between borrowers with no bug in any query |
| **No hard-coded provider tariff** | `test_pricing_and_telemetry.py` | A price constant in a module is a decision nobody recorded making (§15). Fails the build if one appears outside `pricing.py` |
| **No content in telemetry** | Same suite | A secret placed in a request variable must not appear in the serialized log fields (`data-principles.md` §8) |
| **Prompt-injection boundary** | `test_prompts.py`, adversarial payloads | No arrangement of attacker-controlled text escapes its region or reaches the system field (`llm-reasoning-rules.md` §7) |
| **No provider credential in CI** | `ci.yml`, integration job | A smoke suite that quietly became enabled would show up as an invoice rather than as a red build (§20) |
| **Retry policy by category** | `test_providers.py` | An authentication error or an invalid request is never retried: it costs the same twice and trips abuse detection (§22) |
| **Blocked work cannot be dispatched** | `test_orchestrator_integration.py` | A `BLOCKED` job has no transition to `READY`, so the source gate and D-03 hold mechanically rather than by memory (§32, §33) |

### Gates added in Mission 1.0

Every one of these guards a rule that would otherwise depend on a reviewer
remembering it under pressure to ship a collector.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **No approval without authoritative evidence** | `registry.require_evidence_for_approval` (deferred constraint trigger) + `test_source_registry.py` | An approving review with no first-party document is refused at COMMIT, whoever writes it. A blog post cannot be recorded as the basis of an approval, because the evidence-type enum has no value for one |
| **No collector on an ineligible source** | `registry.require_eligibility_for_collector` (BEFORE UPDATE trigger) | Even a direct `UPDATE` by the migration role cannot turn a collector on. The database, not the application, has the last word |
| **The Python gate and the SQL view agree** | `test_source_registry.py` | The eligibility rules exist twice by necessity. Two implementations of one rule drift; this compares them on every source rather than trusting they match |
| **No credential in the registry** | `sros_acquisition.registry.models` + `validate_source_registry.py` + `test_source_registry.py` | `secret_references` holds configuration key names. A value that looks like a credential is refused, so a secret cannot reach a file every reader of the repository can open |
| **No source silently approved** | `validate_source_registry.py` (zero dependency) | Runs with no database and no packages installed. A broken environment cannot reduce this check to nothing (ADR-009 rationale) |
| **Silence is not permission** | `validate_source_registry.py` check 12; `test_new_source_compliance.py` | An approving review must GRANT every activity the assessed use requires. Mission 1.7 approved a source with four of six unaddressed; the prose rule had existed since Mission 1.0 and nothing read it |
| **An approved API profile can actually be reached** | `test_gdelt_readiness.py` | The host allowlist is DERIVED from `access_profiles[].endpoint_url` so revoking a profile revokes the host. Both GDELT profiles recorded no endpoint, so the derived allowlist was empty and no request could ever have been made — asserted on the derived value, which is what the transport is handed |
| **A direct grant is not a way past a licence allowlist** | `test_rights_basis.py`; `compliance/resources.py` | A resource records what KIND of thing authorises it. World Bank's allowlist now requires `NAMED_LICENCE` *and* a matching identifier, where it previously required only the identifier — a descriptor with no basis used to pass (ADR-018) |
| **No fabricated licence identifier** | `AuthorizedDataset.__post_init__`; `test_rights_basis.py` | `DIRECT_GRANT` refuses a licence string in both directions. GDELT names no licence, and "OTHER"/"NONE"/"GDELT Terms Licence" would each land an invented fact in every authorised record's provenance |
| **CI never needs GDELT** | committed fixtures; `capture_gdelt_fixtures.py` is not run in CI | The capture tool runs wherever GDELT is reachable and writes fixtures; CI parses what is committed. Availability of a third party must not decide whether the build passes |
| **The rendered catalog matches the JSON** | `sros-source render --check` | Two hand-maintained copies of one fact drift, and the drift is found by whoever trusted the wrong one |
| **CI calls no external platform** | `ci.yml` | A registry job that fetched a platform's terms would be collection, and would make the build depend on a third party's uptime (§43) |
| **Acquisition blocking is registry-derived** | `test_orchestrator_integration.py` | The orchestrator must read its refusal from `registry.source_eligibility`, not restate it in code. A hardcoded reason is a reason nobody notices going false |

### Gates added in Mission 1.1

D-03 is resolved at the framework level, so the old blanket ban on aggregation
vocabulary was replaced rather than deleted. These gates draw the line that
replaces it.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Rejected designs stay rejected** | `validate_evidence_aggregation.py` | `contradiction_penalty`, `decay_weight`, `aggregated_evidence_score`, `independence_threshold_result`, `evidence_aggregate` are forbidden everywhere, permanently. Each names a design the framework considered and rejected, so its return is a regression rather than an unblocked feature |
| **V1 vocabulary stays out of production surfaces** | Same script | The authorised names are allowed in the reference package and the contracts, never in a migration or under `services/`. Defining the framework and enabling production scoring are separate gates |
| **No universal half-life** | Same script | A module-level half-life constant is refused anywhere. §9 puts half-lives in versioned profiles; a constant would be the invented universal value, and it would *work*, which is what makes it dangerous |
| **No per-source reliability weight** | Same script + `test_evidence_aggregation.py` | No registered source id appears in the aggregation package. Two evidence sets differing only in `source_id` must produce identical numbers |
| **The shipped profile stays UNCALIBRATED** | Same script | Promotion to `CALIBRATED` requires the calibration plan to have been executed and published. A profile cannot even be constructed as `CALIBRATED` without a `calibration_dataset_ref` |
| **`services/scoring` has no implementation** | Same script | The directory is a boundary README. Code appearing in it means production scoring started without a calibrated profile |
| **The twelve mathematical invariants** | `test_evidence_aggregation.py` | Masses sum to 1; the score stays on 0–100; duplicates cannot inflate; unknown independence cannot stack; adding contradiction cannot raise the score; reordering changes nothing; evergreen evidence does not decay; missing inputs are never defaulted |
| **Aggregation is order-independent end to end** | Same suite | Byte-identical canonical output under reordering. Floating-point addition is not associative, so this is engineered by sorting rather than assumed — and it caught a real defect in the explanation serialisation |
| **The sensitivity report matches the code** | `sensitivity --check` | The report is generated from the implementation, so it cannot describe behaviour the code does not have |

### Gates added in Mission 1.2

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Cross-tenant references are impossible, not merely forbidden** | Composite foreign keys carrying `workspace_id` (migration 0005) + `test_claims.py` | A claim cannot reference an opportunity in another workspace, evidence cannot reference a claim in another workspace, and an independence group cannot span claims or workspaces. A third layer under the repository filter and the RLS policy, failing differently from both |
| **The independence shape holds without the repository** | `evidence_independence_shape_check` | `KNOWN_DEPENDENT` must name a group, the other two must not. A future writer that bypasses the repository still cannot store an incoherent record |
| **Unknown independence stays unknown in storage** | Same CHECK + `test_claims.py` | The engine builds its conservative runtime bucket without writing one. An unresolved question must not look resolved in the database |
| **The claim revision pointer names a real revision** | Deferred composite foreign key | A pointer to a nonexistent revision would make the current statement unreadable |
| **RLS on every new tenant table** | Migration 0005 + `test_rls.py` + `test_claims.py` | Four new tables, all ENABLE and FORCE, all policy-bearing. A claim visible across workspaces would leak what another tenant is researching, in their own words |
| **No service imports the reference aggregation engine** | `validate_evidence_aggregation.py` | Tests may import it; production modules may not. This is what makes the vocabulary narrowing below safe (ADR-014) |
| **Computed aggregation values stay out of production** | Same script | The guard was NARROWED, not weakened: evidence INPUT fields became legitimate schema columns in Mission 1.2, while the strengths, masses and score remain forbidden in migrations and under `services/` |
| **No aggregation result is persisted** | `test_claims.py` | Storing a result would be scoring, and scoring requires a `CALIBRATED` profile that does not exist |

### Gates added in Mission 1.3

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **An approving review is still blocked by unsatisfied conditions** | `evidence_independence`-style CHECK plus the eligibility view and `evaluate_eligibility` | `APPROVED_WITH_CONDITIONS` must never quietly mean "a collector may run". Three sources are approving and none is eligible |
| **A catalog load cannot satisfy its own conditions** | `load_catalog_into` never writes `satisfied`; `test_source_review.py` forces every condition false, re-loads, and asserts none was set | A catalog that could declare its own conditions met would make the state meaningless |
| **A satisfied condition must name who and when** | `source_review_conditions_satisfaction_provenance_check` | "Satisfied by nobody, at no time" is the shape an accidental UPDATE leaves behind |
| **Review history is preserved, not overwritten** | Append-only review versions; `test_source_review.py` | The record that matters is "Mission 1.0 concluded X, Mission 1.3 found Y, because document Z became available" |
| **A changed verdict cites evidence retrieved for it** | `test_source_review.py` | A status change with no document behind it is an opinion |
| **Duplicate review versions are refused** | `load_catalog` | Two reviews sharing a version cannot be told apart, and the later would shadow the earlier |
| **The review-results document matches the catalog** | `render_review_results.py --check` | Generated diff view; two hand-maintained copies of one fact drift |
| **The coverage matrix matches the catalog** | `render_signal_coverage.py --check` | Answers "twenty economic sources and no entertainment sources?" from the registry. An answer nobody regenerates is an answer about last month |
| **A suite cannot silently change the registry** | `testing/registry_state.py`, run by `run_pytest_suites.py` | `registry.*` carries no `workspace_id`, so the tenant leak check cannot see it *by construction*. Compared by CONTENT: flipping `collector_enabled` inside a row moves no row count |
| **No collector exists** | `test_source_review.py` | No data-fetching client, no collector module. The day somebody adds one, this fails |

### Gates added in Mission 1.4

Conditions became clearable, which turned the last step between a review and a
collector from "nothing can set this" into "something must". These gates decide
what that something is allowed to be.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A condition cannot be satisfied without a verification** | `registry.require_verification_for_satisfied_condition` (BEFORE trigger, migration 0007) | The SQL bypass, closed. A boolean set by hand — by a migration, an `UPDATE`, a fixture or a developer in a hurry — leaves no record of what was checked. Clearing back to false stays unguarded: failing closed must never need permission |
| **`UNKNOWN` is never promoted to `SATISFIED`** | `satisfied_condition_keys` + `test_compliance.py` | "The verifier failed" and "there is no verifier" are different problems. Both block, and collapsing them would hide the second behind the first permanently |
| **No verifier can satisfy a human condition** | `verification._find` + `validate_compliance_capabilities.py` + `test_compliance.py` | Probed on every source: a `HUMAN_CONFIRMATION` condition must resolve `UNKNOWN` whatever the arguments. A program that could decide one would be the system granting itself permission |
| **A capability is checked, not merely registered** | `capability_failures` conformance checks, asserted per source | Each check runs the real gate against the real configuration, asserts every denial the evidence names, **and asserts its own control case passes** — a filter that denies everything would otherwise satisfy every denial assertion |
| **Every condition resolves to a real verifier** | `validate_compliance_capabilities.py` (zero dependency) | A condition naming a capability nobody built is `UNKNOWN`, and the validator fails rather than letting it sit unnoticed. Also fails on a registered capability no condition names (§5: no unused abstractions) |
| **An exact required notice is traceable to its evidence** | Same script | The FRED sentence must appear in the review evidence that prescribed it. A notice nobody can trace to a document is our wording, not the source's |
| **Attribution cannot be silently omitted** | `render_attribution` raises; `AttributedArtifact.derive` cannot drop an obligation; `test_compliance.py` | A notice missing half its obligation looks like attribution and is not, and the loss would happen at whichever transformation forgot to copy it |
| **Unknown resource scope fails closed** | `authorize_resource`; six rule kinds, all denying | An unrecorded licence, an unstated geography, unread series notes and `UNKNOWN` content origin are all refused. An unexamined resource is not one known to be covered |
| **A source-level approval cannot override a dataset exclusion** | Same, plus `test_compliance.py` | World Bank passes the gate; the Microdata Library still does not |
| **No credential value reaches a log, a response or an exception** | `CredentialStatus` has no field for one; `source_condition_verifications_no_secret_value_check`; sentinel test | Structural rather than conventional: leaking it would require going and reading the environment, which is a visible change |
| **No credential is present in CI, and none is in `.env.example`** | `ci.yml` | A source that became runnable because a build secret was added would be one nobody decided to make runnable |
| **An ineligible source produces no authorization** | `build_authorization` raises; asserted for all 13 sources in two places | The §27 property. Not a flag the collector checks — the absence of the object it needs |
| **Python and SQL agree with conditions verified on both sides** | `test_compliance.py`, `test_source_review.py`, `conftest.recorded_satisfied_keys` | The two implementations are compared on the *same inputs*. Satisfaction is environment state, so a Python gate evaluated without it would report a divergence that is really a missing argument |
| **Eligible is not enabled, and neither is implemented** | `sros-source enable` refuses; `IMPLEMENTED_COLLECTORS` is empty; `assert_registry_grants_nothing.py` | Three facts. A switch ahead of the thing it switches reads as "this is running" |
| **The planner does not dispatch a job nothing can run** | `acquisition_block(report, implemented_collectors)`, fail-closed default | Found by making sources eligible: the planner would have emitted `acquire.collect` with no collector behind it. The two acquisition gates are named separately because different work clears them |
| **CI verifies rather than trusting recorded state** | `sros-source verify --apply` in the integration job | A capability removed after verification would leave a stale `satisfied` true. Re-verification takes a source out of eligibility as readily as into it |

### Gates added in Mission 1.5

The first collector exists, so three Mission 1.0-1.4 guards were **narrowed**
rather than deleted -- the same discipline applied to the D-03 guard in 1.2 and
the enablement guard in 1.4. A guard that becomes false stops protecting
anything; a guard that names its boundary keeps working after the boundary
moves.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A collector cannot run without an authorization** | `collect`'s signature; `test_collector_conformance.py` | Structural, not behavioural: the context is the first positional parameter with no default, so nobody can add an overload that omits it. Mission 1.4's recorded debt, paid |
| **The collector cannot build its own authorization** | Module-namespace assertion | `build_authorization`, `load_catalog` and `load_compliance` are not importable names in the collector module. A collector that could authorise itself could approve itself |
| **A refused resource costs zero network calls** | `RecordingTransport` call count | Not "is refused" -- **zero calls**. A gate that refuses after the request went out has prevented nothing |
| **No public signature accepts a URL** | Parameter-name scan over `collection.__all__` | The shape an escape hatch takes when someone adds one "just for testing". `host_of` is exempted by name, with the reason recorded |
| **A path cannot be a URL, and cannot traverse** | `HttpRequest.__post_init__` | The transport takes a path. Handing it an absolute URL is a construction error |
| **An indicator cannot reshape the request** | `WorldBankRequest.__post_init__` | It becomes a path segment; a slash or a query character would change what is fetched |
| **An unauthorized host is refused at the transport** | `HttpxTransport._compose` | Checked at the last place before a socket as well as at the collector: a guard that exists only further up is one a future caller routes around |
| **Redirects are not followed** | `follow_redirects=False`, and a 3xx is an error | A redirect is the documented way out of a host allowlist |
| **Only one file may reach a network** | `ci.yml`, `test_collector_conformance.py` | Mission 1.0's blanket ban, narrowed to `collection/transport.py`. Naming where the network IS says more than asserting it is absent |
| **Collectors live only in the collection package** | `ci.yml`, both suites | The registry and compliance packages decide whether collection may happen. A collector inside either would put the decision and its execution in one place |
| **The switch never gets ahead of an implementation** | `sros-source enable`; `IMPLEMENTED_COLLECTORS` | Eurostat is eligible and has no collector, and cannot be enabled. Found the hard way: a Mission 1.4 test enabled a real collector as a side effect the moment World Bank gained one |
| **Nothing is collected from a source with no collector** | Both suites, asserted as a set relation | Replaces `raw_records == 0`, which was true of every mission until one collected and then stopped being a property |
| **Retention cannot be chosen by a collector** | `build_draft` has no expiry parameter | Enforced by construction: there is nothing to pass |
| **Attribution cannot be composed by a collector** | Same -- no attribution parameter | It is rendered from the obligation the review recorded, and rendering fails closed |
| **The fingerprint ignores retrieval time** | `test_world_bank_collector.py` | Hashing it would make every retrieval a revision, which is how an idempotent collector grows a table forever |
| **Pagination cannot loop** | Bounded `range`; page-advance check | A source repeating page 1 is reported as a fault rather than absorbed until a limit hides it |
| **A deterministic 4xx is never retried** | `_status_failure` + `RETRYABLE_CODES` | One call, not three. Repeating a rejection is how a rate limit becomes a ban |
| **No response body reaches a job result** | `AcquisitionFailure`; sentinel test | §33. A driver has no obligation to keep secrets out of its own messages |
| **Duplicate delivery writes no second row** | Shared-connection job test | At-least-once delivery honoured without claiming exactly-once |
| **Raw records are tenant-isolated** | Two workspaces, RLS, `test_world_bank_collector.py` | A worker cannot write into another workspace, and a query with no tenant filter still returns only its own |
| **The live suite is opt-in and absent from CI** | `SROS_ENABLE_WORLD_BANK_SMOKE_TESTS`, `ci.yml` | A suite that quietly became enabled would show up as traffic to somebody else's servers rather than as a red build |

### Normalization (Mission 1.6)

The first stage that reads what a collector wrote. Its guards protect a
different property from collection's: not *may we fetch this*, but *did the
transformation invent anything*.

`validate_normalization.py` is zero-dependency and was **probed against fourteen
deliberate violations before being believed** — the same discipline the gitleaks
configuration needed, and for the same reason: a validator that has only ever
run against clean code is a validator whose patterns have never been exercised.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Normalization reaches no network** | `validate_normalization.py` parses every import in the package | Not a grep for `httpx`: an AST walk, so `from urllib.request import urlopen` and `import socket` are caught too |
| **Not even the sanctioned transport** | Same, on relative imports | The blanket ban would be satisfied by importing `collection/transport.py`, the one file allowed to hold a client. Reaching the network through the door left open for a collector is still reaching the network |
| **No LLM and no embedding library** | Same | Normalization is deterministic and reproducible. A model deciding a geography would make it neither, and D-12 is still open |
| **No signal, claim or evidence table** | Same, on SQL string literals | A mention in prose is how the rule gets explained; a mention inside a query is the thing forbidden |
| **The vocabulary matches the contract** | Same, against `domain.v1.json` and migration 0009 | Seven closed enums and one registry. A vocabulary living only in Python drifts from the schema `CHECK` and the TypeScript side at once |
| **Record kinds in code match the ones seeded** | Same | Two hand-maintained copies of one fact drift, and the drift is found by whoever trusted the wrong one |
| **Every geography entry records its basis** | Same, over `geography-mapping-v1.json` | A classification that cannot be re-verified is indistinguishable from a guess |
| **No aggregate carries a country code** | Same, plus `CanonicalGeography.__post_init__` | The "World is a country" error, refused at the data and at the constructor |
| **Attribution cannot be dropped** | `build_normalized` has no attribution parameter; signature test | Structural. A behavioural test would pass equally well against a builder with an `attribution=None` nobody had used yet |
| **Retention cannot be chosen** | Same — no expiry parameter | The window is the resolved normalized tier, anchored on normalization, and the raw expiry is deliberately not copied |
| **Missing is never zero** | `CanonicalValue.__post_init__` | Constructing a `NOT_REPORTED` value carrying a number raises. That constructor is where the bug would have to pass |
| **Floats are refused as input** | `decimal_from` | A value that has been through IEEE-754 may already differ from the source's; re-reading it would bake that in |
| **Re-running writes nothing** | Identity unique constraint; job test; the real six records | Idempotency without claiming exactly-once delivery, which Celery does not provide |
| **Output cannot change without a version bump** | `NON_DETERMINISTIC_OUTPUT` on an identity collision with different content | Overwriting would destroy the stored representation; the version *is* the identity that would distinguish them |
| **A revision does not overwrite its predecessor** | `superseded_at`, scoped to one lineage | Crossing lineages would make writing schema 2 retire schema 1 — the selection policy D-08 forbids inventing |
| **A cross-tenant reference cannot be written** | Composite FK on `(workspace_id, raw_record_id)` | Layer three. RLS and the repository filter can be forgotten; a structural impossibility cannot |
| **The planner does not dispatch normalization for a source with no normalizer** | `normalization_block(report, collectors, normalizers)`, fail-closed default | The gap Mission 1.5 opened: the old reason said "no collector is implemented", which stopped being true while the capability stayed unavailable |

### Acquisition authorization (Mission 1.9.2)

No new CI job. These are rules inside gates that already run — the source-registry
job and the acquisition suite — and they are listed because each closed a hole
that a passing suite had been reporting as fine.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **An unestablished rights basis is refused** | `authorize_resource`, unconditional rule | It had been checked only inside the licence-allowlist rule, so a descriptor with **no basis at all** passed for every source enumerating no licences — including GDELT, the one source authorised by a direct grant rather than a licence |
| **An unreviewed dataset family is refused** | `allowed_dataset_families` on the scope | `require_dataset_family` refused a resource that could not say what it is, and admitted one that said something nobody had reviewed. A family no reviewer had rejected was indistinguishable from one a reviewer had approved |
| **A job that exceeds the reviewed ceiling is refused** | `AcquisitionBounds.refusals`, via `context.authorize_job_size` | GDELT publishes two files every fifteen minutes since 2019 and its terms limit none of it. The ceiling is the review's; a collector choosing its own would be setting its own permissions |
| **A ceiling with no basis is refused at load time** | `AcquisitionBounds.__post_init__` | A number nobody can re-check survives every later review by looking deliberate |
| **A job that does not state its size is refused** | Same | The asymmetry `ResourceDescriptor` is built on: not saying how much you intend to take is not a size known to fall under a bound |
| **The reviewed path is the endpoint, not the site root** | `endpoint_url` on the access profile, plus `HttpRequest`'s refusal of `..` and of absolute URLs | Fail-closed **by construction** rather than by a new rule: a base of `.../gdeltv3/web/ngrams/` cannot reach `.../gdeltv3/webngrams/`, the sibling dataset this review rejected |
| **Four facts stay four** | `evaluate_readiness`, derived and never stored | Eligible, resource-ready, implemented, enabled. GDELT spent two missions eligible with every resource failing closed, and "eligible" was the most specific word available |

### The second collector (Mission 1.9.3)

No new CI job, and no new queue. What the second collector added are rules inside
the acquisition suite, and they are listed because each one guards a boundary the
first collector never had to cross.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **The reviewed ceiling cannot be redefined in code** | `authorize_job_size` on the context; the string `max_files_per_job` is absent from the collector, asserted | A collector that set its own volume bound would be setting its own permissions |
| **A nine-file job is refused whole** | The check runs once for the request, not per file | Splitting it into two permitted jobs would grant a ceiling the review did not |
| **The route is resolved by LABEL** | `_route` selects `gdelt-web-ngram-files`; `build_raw_record` requires the access label | `access[0]` is GDELT's **deferred** DOC API. Taking it would have authorised the wrong host and recorded `PUBLIC_API` on every file download |
| **Decompression is bounded three ways** | `NgramBounds` — compressed, decompressed, line length | The decompressed ceiling is the one the compressed ceiling cannot give: kilobytes on the wire becoming megabytes |
| **Gzip framing is required** | `zlib.decompressobj(31)` | An HTML error page returned with HTTP 200 fails immediately instead of parsing into plausible rubbish |
| **A truncated stream is not a short file** | `decompressor.eof` checked at the end | Rows already read from an incomplete download are not a complete file |
| **A malformed row discards its file** | Strict four-field parse, fatal | No column shifting: a five-field row is a contract change, and both a change and a wrong file need a person |
| **Our ceilings truncate; the source's contract discards** | `truncated_by_bound` on the file report | The two failures mean opposite things and must not report the same way |
| **Retry cannot duplicate** | `_read_file` returns a list, not a generator | A mid-stream failure would otherwise have already released rows that the retry re-reads |
| **No timezone is invented** | `validate_bucket_label` returns a string; `observed_at` is `None` | H-29 is open, and an assumption stored in a `TIMESTAMPTZ` is the one a reader trusts most |
| **No language code is guessed** | `content_language` stays `NULL` | H-30 is open, and that column is read as a code |
| **CI reaches no GDELT host** | The live suite is opt-in behind `SROS_ENABLE_GDELT_WEB_NGRAM_SMOKE_TESTS` | A developer with a network has not consented to third-party traffic on every run |

### The canonical model gained a second shape (Mission 1.10)

No new CI job. These are rules inside the normalization guard and the model
itself, and each closes a way the model could have been made to lie.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **A period cannot claim a zone it does not have** | `CanonicalPeriod.__post_init__`, both directions | `NOT_ESTABLISHED` refuses aware bounds and `ESTABLISHED` refuses naive ones. An aware bound under an unestablished zone carries an offset the source never published |
| **`observed_at` is empty when there is no event time** | `period.event_time`, `None` under `NOT_ESTABLISHED` | A `TIMESTAMPTZ` filled from a wall-clock reading would be an assumption in the column a consumer trusts most |
| **An existing payload cannot change shape** | `timezone_state` serialised only when not `ESTABLISHED` | The payload is inside the content fingerprint; an unconditional key would have reported a revision on every record ever written |
| **A language tag cannot appear without a mapping** | `CanonicalLanguage.__post_init__`, both directions | Resemblance is not a mapping. `ENGLISH` looks like `en`, and the first CLD2 name that does not would be silently wrong |
| **A language cannot be assigned where a geography is expected** | The two value objects share one field name | Asserted structurally rather than by convention |
| **A record kind cannot be declared without being registered** | `validate_normalization.py`, now reading **every** migration | A single filename was right while one kind existed and would have silently stopped covering the second |
| **The term's gram size is never inferred from its text** | Asserted over the payload class's source | A two-word entry in a unigram file is a contract violation, and counting spaces would hide it |
| **A vocabulary entry is not an adapter** | `NORMALIZER_REGISTRY` and `IMPLEMENTED_NORMALIZERS` asserted empty of GDELT | The registry row lets the model describe a shape; it does not claim code exists |

### The second normalizer (Mission 1.10.1)

No new CI job. Rules inside the normalization guard and the adapter itself.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **The adapter reaches no network, model or lookup** | AST walk over its imports | A substring scan fails on the docstring explaining the rule, and teaches the next person to weaken the assertion |
| **No timezone is ever converted** | AST: no `astimezone` / `utcnow` / `now` / `localtime` call, no `tzinfo=` keyword | H-29. The one place a UTC offset could enter the field a consumer trusts most |
| **No language table is embedded** | AST over string constants: `en`, `fr`, `es`, `ko`, `de`, `ja`, `BCP-47` appear nowhere | H-30. A mapping cannot be applied that does not exist |
| **Source text is preserved verbatim** | `_source_text` (unstripped) is separate from `_text` (trimmed) | A term published with an edge space would otherwise be stored as a different term — invisibly, in the payload, the fingerprint and the identity |
| **`gram_size` is never inferred from the term** | Asserted over the mapping code: no `.split(`, no `.count(` | Counting spaces would silently correct a contract violation instead of leaving it visible |
| **A self-contradictory payload is refused** | `gram_kind` checked against `resource_id` | Choosing a winner between two source facts is the silent correction |
| **Quality reasons come out in a stated order** | Built in sequence, never sorted afterwards; asserted over three runs | A consumer branching on the first reason must get the same one every time |
| **An existing payload still hashes to its historical value** | A **literal** sha256, not a round-trip | The assertion that catches `timezone_state` leaking into an `ESTABLISHED` payload and reporting a revision on every record ever written |
| **`only_unnormalized` stays meaningful with two adapters** | One lineage per registered adapter, matched on the collector | Dropping the filter is correct per record and silently wrong in bulk: a workspace larger than the batch bound would re-read its first page forever |

---

## 2. Turborepo task graph

Defined in `turbo.json`.

| Task | Depends on | Cached | Notes |
|------|-----------|--------|-------|
| `build` | `^build` | Yes | Excludes test files from the input hash |
| `lint` | `^build` | Yes | |
| `typecheck` | `^build` | Yes | Needs upstream declarations |
| `test` | `build` | Yes | Own package's build, not just upstream |
| `test:unit` | `^build` | Yes | Fast path, no local build |
| `test:e2e` | `build` | **No** | Real browser, real time |
| `dev` | — | No | Persistent |

Caching rules that matter:

- **`test:e2e` is never cached.** An E2E result is a statement about a running
  system at a moment in time, not a pure function of the source.
- **`build` excludes test files from its inputs.** Editing a test must not
  invalidate the build cache.
- **`globalDependencies`** includes `.editorconfig`, `.nvmrc` and
  `packages/typescript-config/base.json` — changing a toolchain-wide file
  correctly busts everything.

### Python and Turborepo

Turborepo does not understand Python imports (ADR-001, Cons). Each Python service
exposes its tasks through a thin `package.json` script layer:

```jsonc
// services/scoring/package.json
{
  "name": "@sros/scoring",
  "scripts": {
    "lint": "ruff check .",
    "typecheck": "mypy --strict src",
    "test": "pytest",
    "build": "python -m build"
  }
}
```

Turborepo hashes the whole service directory rather than a precise import graph,
so Python caching is coarse. It errs toward cache misses, never stale hits.

---

## 3. Lint strategy

### Principles

1. **Lint catches correctness, not style.** Prettier and ruff format own style.
   Overlapping the two produces conflicts that get resolved by disabling rules.
2. **Every rule blocks something real.** A rule that produces noise gets disabled
   in bulk, taking the useful rules with it.
3. **No blanket `eslint-disable` at file scope.** A disable is one line, one
   rule, with a reason.

### TypeScript — rules with specification weight

These are not preferences. Each blocks a specific specification violation.

| Rule | Blocks |
|------|--------|
| `no-restricted-imports` (cross-service paths) | A context importing another's internals instead of its contract (`service-boundaries.md` §4) |
| `no-restricted-syntax` (local domain enums) | The C-02 drift: a domain enum declared outside `packages/contracts` |
| `no-restricted-imports` (LLM provider SDKs) | A business service importing a provider SDK instead of using the LLM Gateway (ADR-006) |
| `@typescript-eslint/switch-exhaustiveness-check` | An unhandled claim type or score family — the conflation §8 forbids |
| `@typescript-eslint/no-floating-promises` | Silently dropped async work; in a pipeline, a lost job is lost evidence |
| `@typescript-eslint/no-explicit-any` | Untyped data crossing a boundary where provenance must be attached |
| `react/no-danger` | Rendering scraped content as HTML |
| `no-restricted-globals` on `process.env` outside config | Environment access scattered through domain code |

### Python — ruff

Enabled rule families: `E`/`W` (pycodestyle), `F` (pyflakes), `I` (isort),
`N` (naming), `UP` (pyupgrade), `B` (bugbear), `ASYNC` (async correctness),
`S` (bandit security), `DTZ` (timezone-aware datetimes), `RET`, `SIM`, `PTH`.

Two of these are load-bearing rather than cosmetic:

- **`ASYNC`** — catches blocking calls inside async handlers. ADR-003 records
  this as the failure mode whose symptom is furthest from its cause.
- **`DTZ`** — forbids naive datetimes. Every observation in this system carries a
  timestamp (`data-principles.md` §9), and recency decay is computed from them.
  A naive datetime is a silent correctness bug in the evidence model. It is also a
  retention bug: `expires_at` is computed from these timestamps
  (`data-retention-policy-v1.md` §6).

### Tenancy and numeric-scale checks

Two classes of bug are severe enough to deserve their own automated checks
(Mission 0.2), because review does not reliably catch either:

| Check | Catches |
|-------|---------|
| Repository/query lint for tenant-scoped tables | A query on a tenant-scoped table with no `workspace_id` filter — a cross-tenant data leak, not a rendering bug (ADR-005) |
| Cache-key and vector-filter enforcement in client wrappers | The two leak paths that do not go through SQL and so never appear in a query audit |
| Contract range validators | A `confidence` outside `[0,1]` or a `*_score` outside `0–100` (`scoring-framework-v1.1.md` §4.1) |
| `MarketScope` shape validators | A `COUNTRY` scope with two countries, an empty list, or an uncanonicalized list — all of which break scope equality and therefore cache and dedup keys (Ontology V2 §4.4) |
| Registry-vs-enum lint | A domain taxonomy declared as a union type or a database enum instead of a registry reference (Ontology V2 §14.3) |

`mypy --strict` is required, not optional: without it Pydantic validates the
edges while the interior stays untyped, and the guarantee ADR-003 was made for
stops at the boundary.

---

## 4. Formatting strategy

| Files | Tool |
|-------|------|
| `.ts .tsx .js .jsx .json .md .yml .yaml` | Prettier |
| `.py` | ruff format |
| Whitespace baseline for everything | `.editorconfig` |

Rules:

- **Formatting is never a review comment.** If a human mentions formatting in a
  review, the automation has failed.
- **CI checks, it does not fix.** `format:check` fails the build; a bot pushing
  format commits makes history unreadable.
- **One formatter per file type.** No exceptions.
- **Markdown is formatted too.** Documentation is production code
  (`PROJECT_MANIFEST.md` §Repository Philosophy).

---

## 5. CI pipeline (planned)

Placeholders in `.github/workflows/`. They are `workflow_dispatch`-only until
Mission 0.2, so they cannot fail on a repository that has no lockfile yet.

```
PR opened
  ├─ changed-paths detection        (avoid running everything on every PR)
  ├─ secret scan                    ALWAYS runs, never path-filtered
  ├─ format:check                   fast fail
  ├─ lint            ─┐
  ├─ typecheck        ├─ parallel
  ├─ test:unit       ─┘
  ├─ contract tests                 schemas still parse the fixtures
  ├─ integration tests              testcontainers: postgres, redis, qdrant
  └─ build

main (post-merge)
  ├─ everything above
  ├─ dependency audit
  └─ image build

nightly
  ├─ E2E (Playwright)
  ├─ full integration suite
  └─ dependency audit
```

### Rules

1. **The secret scan is never path-filtered and never skipped.** It is the one
   gate whose failure is unrecoverable: a leaked credential is compromised the
   moment it is pushed, and reverting the commit does not un-leak it.
2. **Path filtering everywhere else.** ADR-001 accepted "CI must be path-filtered
   or it becomes slow" as a known cost; this is the payment.
3. **E2E is nightly, not per-PR.** Flaky per-PR E2E teaches people to re-run
   failing jobs without reading them, which destroys the value of every other
   gate.
4. **No test in CI touches a live external source.** Recorded fixtures only.
   Otherwise the build depends on a third party's uptime and rate limits, and
   `data-principles.md` §3 gets violated by a CI run.
5. **CI has no production credentials.**

---

## 6. Branch protection (when the remote exists)

- `main` protected, no direct pushes.
- Required status checks: format, lint, typecheck, unit, contract, integration,
  secret scan.
- Required review via `CODEOWNERS` — **D-09 resolved**: the owner is `@Speekyx`
  and `CODEOWNERS` is updated accordingly. Note for any future change: GitHub
  does not error on an unresolvable owner. It silently assigns no reviewer, so
  branch protection would appear configured while enforcing nothing.
- Linear history, no merge commits from feature branches.
- Conversation resolution required.

---

## 7. What automation cannot check

These stay in human review, and they are the ones that matter most in this
system:

| Check | Why a machine cannot do it |
|-------|---------------------------|
| Is this claim correctly typed as `OBSERVED` vs `INFERRED`? | Requires knowing what the data actually supports |
| Is this confidence value justified? | Requires judgment about the evidence |
| Does this contradict an authoritative specification? | Requires reading both |
| Is this LLM prompt injection-safe? | Requires adversarial thinking |
| Is this source's usage lawful? | Requires reading terms of service |
| Is the evidence aggregation sound? | Requires domain reasoning |
| Is this retention period justified by the source terms? | Requires reading the terms and recording a `basis` (`data-retention-policy-v1.md` §3) |
| Is this job genuinely idempotent? | Requires reasoning about at-least-once delivery (ADR-004) |
| Are these two discoveries the same opportunity? | Identity resolution is an analytical judgment, not a unique constraint (Ontology V2 §12.3) |
| Should this taxonomy value be a new registry entry or an alias of an existing one? | Requires domain judgment |

The PR template (`.github/PULL_REQUEST_TEMPLATE.md`) asks about these explicitly,
because a checklist item is the cheapest available prompt to think about them.
