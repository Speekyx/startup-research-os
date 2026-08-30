# Source Registry V1

**Status:** Authoritative. Created in Mission 1.0, resolving **D-07**.
**Version:** 1.2 (Mission 1.7 added the two coverage tables to §3, the new
families to §2, and restated §10. Mission 1.4 added §4 "How a condition gets
cleared", "Two views of eligibility" and "Eligible, enabled, implemented")
**Date:** 2026-08-30
**Governs:** `registry.sources` and the tables around it, the collector
eligibility gate, retention overrides, source coverage, and every future
collector.
**Related:** `data-principles.md` §13, `data-retention-policy-v1.md`,
[ADR-013](../architecture/adr/ADR-013-source-registry-governance.md),
[ADR-016](../architecture/adr/ADR-016-compliance-capabilities-and-acquisition-authorization.md),
[`acquisition-authorization-v1.md`](acquisition-authorization-v1.md),
`opportunity-ontology-v2.md` §14.

---

## 0. What this document is for

Before this registry, "which sources may we collect from" was answered by
whoever was writing the collector, at the moment they were writing it, from
memory. That is the failure mode `data-principles.md` §13 was written against
and it is the one this document closes.

The registry answers three questions, and keeps them apart:

| Question | Answered by | Never answers |
|----------|-------------|---------------|
| How could this source be reached? | `source_access_profiles` | whether it may be |
| What do its own documents permit? | `source_policy_reviews` + `source_policy_evidence` | how to reach it |
| May a collector run against it? | the eligibility gate | either of the above alone |

Keeping them apart is the point. A single "is this source OK" field would let a
technical fact — *a browser could load this page* — be read as a permission.

### What this system is not

**It is not a legal decision engine.** It records what a source's own published
documents say, who read them, when, and what was still unclear. It does not
determine legality, it does not produce legal advice, and no output of it may be
presented as either. Jurisdiction analysis (GDPR applicability and equivalents)
remains a human decision, deliberately not guessed
(`data-retention-policy-v1.md` §7).

**It is not an approval optimiser.** The measure of this registry is not how
many sources are approved. A registry in which every platform came back approved
would be evidence that the gate is not doing anything.

---

## 1. The rules that cannot be traded away

These are invariants. Code that violates one is wrong even if it passes.

1. **Public visibility is not permission.** A source never becomes
   collector-eligible because its data is publicly reachable. Reachability lives
   in the access profile; permission lives in the review; the gate requires the
   review.
2. **Uncertainty is never permission.** When the documents are silent, absent,
   unreachable, or ambiguous, the result is `NOT_ADDRESSED` / `UNCLEAR` and the
   source stays `REQUIRES_REVIEW`. There is no path from *we could not check* to
   *we may proceed*.
3. **An approval requires retrieved, authoritative evidence.** Not a blog post,
   not a tutorial, not a forum answer, not a Stack Overflow reply, and not model
   recall. Authoritative means the source's own published documents, an operator
   response, or a recorded legal review.
4. **No credential is ever stored here.** Access profiles carry configuration
   **key names** (`REDDIT_CLIENT_ID`). A value that looks like a credential is
   refused by the model, so a secret cannot be written into a file that every
   reader of the repository can open.
5. **No circumvention.** Login requirements, API restrictions, rate limits,
   robots directives, anti-automation measures, CAPTCHAs and technical
   protections are limits, not obstacles. The registry never describes getting
   around one, and inconvenience of an official API is not a reason to create a
   scraper.
6. **The stricter rule wins.** A retention override may only shorten retention
   below the project baseline, never lengthen it
   (`data-retention-policy-v1.md` §1).
7. **No invented numbers.** No arbitrary per-platform reliability weights, no
   "legal confidence = 83%". Reliability is a scoring concern and is blocked by
   D-03; inventing a value here would decide D-03 by the back door.

---

## 2. Enumerations

Every vocabulary below is a **closed enum** (Ontology V2 §14): they require
exhaustive branching, so adding a value is a contract change, not a data change.
They are defined once in `packages/contracts/schema/domain.v1.json` and
generated into TypeScript and Python.

Mission 1.3 added `ConditionVerification`; Mission 1.4 added
`ConditionVerificationResult`, `AttributionElement` and `ResourceContentOrigin`.
All four are specified in
[`acquisition-authorization-v1.md`](acquisition-authorization-v1.md) rather than
restated here.

### `SourceApprovalState`

| Value | Meaning |
|-------|---------|
| `DRAFT` | A candidate was recorded. No review has been attempted |
| `REQUIRES_REVIEW` | A review was attempted and did not reach a conclusion. **The default outcome of uncertainty** |
| `APPROVED_WITH_CONDITIONS` | Permitted for the assessed use case, subject to recorded conditions |
| `APPROVED` | Permitted for the assessed use case |
| `RESTRICTED` | Some assessed activities are permitted and others are not; the source may not be collected for this use case |
| `PROHIBITED` | The documents forbid the assessed use |
| `SUSPENDED` | Previously usable, stopped pending re-review |

Only `APPROVED` and `APPROVED_WITH_CONDITIONS` are approving states.

### `SourceAccessMethod` — technical only

`OFFICIAL_API`, `PUBLIC_API`, `RSS_OR_FEED`, `DATASET_DOWNLOAD`, `PUBLIC_WEB`,
`BROWSER_AUTOMATION`, `MANUAL_IMPORT`.

`BROWSER_AUTOMATION` appearing on a source means a browser **could** reach it. It
never means anyone may.

### `PolicyAssessment` — per activity

`PERMITTED`, `PERMITTED_WITH_CONDITIONS`, `NOT_PERMITTED`, `NOT_ADDRESSED`,
`UNCLEAR`, `NOT_ASSESSED`.

`NOT_ADDRESSED` means the documents were read and were silent. `UNCLEAR` means
they spoke and the meaning could not be settled. `NOT_ASSESSED` means nobody has
looked. All three block; they are kept distinct because they call for different
next steps.

### `PolicyEvidenceType`

`OFFICIAL_API_DOCS`, `OFFICIAL_TERMS`, `OFFICIAL_LICENCE`, `OFFICIAL_PRIVACY`,
`OFFICIAL_ACCESS_CONTROL`, `OPERATOR_CORRESPONDENCE`, `LEGAL_REVIEW`.

Every one is first-party or a recorded review. There is deliberately no
`THIRD_PARTY_ARTICLE` value: the type system refuses to record a blog post as
the basis of an approval.

### `SourceLifecycle`, `SourceAcquisitionCost`, `PersonalDataRisk`

`ACTIVE` / `DEPRECATED`; `FREE` / `FREE_WITH_LIMITS` / `PAID` /
`USAGE_BASED` / `UNKNOWN`; `NONE_EXPECTED` / `PSEUDONYMOUS` / `IDENTIFIABLE` /
`SENSITIVE_POSSIBLE` / `UNKNOWN`.

`PersonalDataRisk` is a **handling classification, not a legal ruling**, and its
values say what KIND of data may be present rather than how bad it would be. It
drives pseudonymisation and identifier-discard expectations, nothing else.

*(Corrected in Mission 1.4: this section listed severity words —
`LOW`/`MEDIUM`/`HIGH` — which were never the contract vocabulary. Mission 1.3
found and fixed the same mistake in nine draft reviews; the specification kept
it until now.)*

### `source_family` — a registry, not an enum

Families (`community`, `forum`, `app_store`, `content_platform`,
`product_discovery`, `search_trends`, `economic_data`, `developer`, `social`,
`gaming`, `creator`, `knowledge`, `news`, `public_dataset`) are rows in
`registry.registry_entries`. Adding one must never require a migration, per
Ontology V2 §14 — the last three arrived in Mission 1.7 as an `INSERT`.

**A family is a discovery attribute and never an eligibility one.** The gate
does not read this column, and a `gaming` source is neither more nor less
collectable for being one.

---

## 3. Data model

Eight tables in the `registry` schema. All **global**: none carries a
`workspace_id`, none has a row-level-security policy.

```text
registry.sources ──┬── source_access_profiles      how it could be reached
                   ├── source_policy_reviews  ──┬── source_policy_evidence
                   │                            └── source_review_conditions
                   │                                     │
                   │                                     └── source_condition_
                   │                                         verifications
                   ├── source_retention_policies   an override, if any
                   ├── source_capabilities         what data it can supply
                   ├── source_signal_coverage      what could be LEARNED from it
                   └── source_behavior_coverage    which behaviours it records
                   ▲
        registry.source_eligibility (VIEW)  the verdict, derived
```

The condition tables were added by Missions 1.3 and 1.4; the two coverage tables
by Mission 1.7 ([ADR-017](../architecture/adr/ADR-017-source-signal-coverage.md)).

**Coverage is potential, never permission.** A source may cover `entertainment`
and be `PROHIBITED`. The eligibility view does not read either coverage table,
and it must never start: a field describing what a source could tell us, sitting
next to a field describing whether we may ask, is exactly the single "is this
source OK" column §0 exists to prevent. A condition is what an
approving review depends on; a verification is the record of somebody having
checked one, and is the only thing that can mark a condition satisfied.

### Why global rather than per workspace

Source metadata is a property of the platform, not of a tenant. A source
assessed as permitted in one workspace and prohibited in another would make
provenance incomparable across workspaces, and would mean the same evidence
record carried two different meanings. Consequently:

- there is no `workspace_id` on any registry table;
- there is no RLS policy on any of them (ADR-012 covers tenant tables; this is
  not one);
- the runtime role holds `SELECT` only. Every write goes through the migration
  role via the `sros-source` CLI.

### Eligibility is a view, never a column

`registry.source_eligibility` derives the verdict and returns
`blocking_reasons TEXT[]`. It is not a stored boolean, because a stored boolean
can drift away from the reasons behind it, and the drift is discovered by
whoever trusted it.

`collector_enabled` on `registry.sources` is the operational switch and is a
different thing: eligibility says *may it*, `collector_enabled` says *is it
turned on*. A `BEFORE UPDATE` trigger refuses to set it on a source the view
does not clear, so the switch cannot get ahead of the gate.

### Approval cannot outrun its evidence

Evidence rows reference their review, so both are written in one transaction. A
`DEFERRABLE INITIALLY DEFERRED` constraint trigger therefore checks at COMMIT:
an approving review with no authoritative evidence is refused, while a
legitimate review written atomically is accepted.

---

## 4. The eligibility gate

```text
collector_eligible(source) =
        lifecycle is ACTIVE
    AND source is not suspended
    AND a policy review exists
    AND the review is in an approving state
    AND the review has at least one AUTHORITATIVE evidence record
    AND the review is not stale (past next_review_at)
    AND at least one access profile is configured
    AND every profile requiring a credential names a configuration reference
    AND any retention override present records its basis
```

Three properties matter as much as the conditions.

**It fails closed.** Anything missing blocks.

**It explains itself, in full.** A refusal returns *every* failed condition, not
the first. A gate that reports one blocker at a time trains a reviewer to
distrust it; a gate that says *"policy review is REQUIRES_REVIEW; policy review
has no evidence"* ends the conversation.

**It exists twice, and the two are compared.** The Python implementation
(`sros_acquisition.registry.eligibility`) runs with no database, in the CLI and
the zero-dependency validator. The SQL view backs the database trigger, so no
`UPDATE` from any client can enable a collector on an ineligible source. A test
asserts the two agree on every source in the catalog rather than assuming it.

### Staleness

Approvals expire. A review past `next_review_at` blocks, because platform terms
change and an approval nobody has re-checked is a statement about the past
presented as a statement about now. The interval is per source
(`review_interval_days`, default 180): platforms differ in how often they revise
terms, and no single universal interval is defensible.

### Conditions must be checkable, not just written down

Added in Mission 1.3. `APPROVED_WITH_CONDITIONS` must never silently mean "a
collector may run", so each condition is a row rather than a sentence:

```text
key                  stable across review versions
description          what must be true, for a human
verification         CONFIG_REFERENCE | CAPABILITY | RETENTION_LIMIT
                     | ACCESS_METHOD | HUMAN_CONFIRMATION
verification_detail  the config key, capability or day count checked
satisfied            ENVIRONMENT state. A catalog load can never set it
```

The gate blocks an approving review until **every** condition is satisfied, in
both the Python implementation and the SQL view.

`HUMAN_CONFIRMATION` is a real answer and the honest one for anything a program
cannot establish. Encoding legal prose as executable logic — "attribution is
adequate" as a boolean — would be worse than admitting a person has to decide.

`satisfied` is deliberately not something the catalog can assert about itself. A
catalog that could declare its own conditions met would make the state
meaningless.

### How a condition gets cleared

Added in Mission 1.4, and specified in full by
[`acquisition-authorization-v1.md`](acquisition-authorization-v1.md).

**A verifier clears a condition, and nothing else does.** Each verification
writes an append-only record — which condition, which verifier, at which
version, when, the result, why, what was inspected — and `satisfied` is synced
from it. A `BEFORE` trigger refuses to set the boolean true with no `SATISFIED`
record behind it, whoever issues the `UPDATE`. There is no manual path, no
catalog field and no migration that can grant it.

Results are `SATISFIED | UNSATISFIED | UNKNOWN | NOT_APPLICABLE`. **Only
`SATISFIED` clears.** `UNKNOWN` — the verifier could not run, or none is
registered — blocks exactly as a failure does and is never promoted.

No verifier can satisfy a `HUMAN_CONFIRMATION` condition. That branch returns
`UNKNOWN` unconditionally, and no code in this repository writes a human
confirmation.

**Re-verification takes a source out of eligibility as readily as into it.** A
capability removed after the fact produces `UNSATISFIED` on the next run and the
boolean is cleared, which is why CI re-verifies rather than trusting what is
recorded.

### Two views of eligibility

Since conditions became clearable there are two, and they can legitimately
disagree:

| View | Shows | Where |
|---|---|---|
| **Catalog** | The reviews, with no condition verified | `source-catalog-v1.md` — generated, committed, CI-checked |
| **Environment** | The same reviews with the verifiers run here | `sros-source eligibility`, `conditions`, `GET /sources/{id}/eligibility` |

A committed file cannot hold the environment view without drifting with the
machine that generated it, and a catalog can never assert its own conditions
satisfied. Each command and each document says which view it is showing.

### Eligible, enabled, implemented

Three facts, and collapsing any two of them is the mistake this section exists
to prevent:

| Fact | Means |
|---|---|
| **collector-eligible** | The governance gate passes. Derived, never stored |
| **collector-enabled** | The operational switch is on. `registry.sources.collector_enabled` |
| **collector implemented** | Code exists that can collect from it |

After Mission 1.4, two sources are eligible, **none is enabled, and none is
implemented**. `sros-source enable` refuses a source with no implemented
collector — a switch ahead of the thing it switches reads as "this is running" —
and the orchestrator blocks acquisition under `NO-COLLECTOR-IMPLEMENTED` rather
than dispatching a job no worker can run.

---

## 5. Per-activity assessment

A source is assessed for **eleven activities separately**, because their
conditions genuinely differ — permitting automated API reads while forbidding
commercial use is the common case, not the exception:

`automated_access`, `api_use`, `browser_automation`, `commercial_use`,
`storage`, `retention`, `redistribution`, `derived_analytics`,
`model_processing`, `personal_data_handling`, `attribution_required`.

Every review states `assessed_use_case` — the single use the verdicts cover. **An
assessment does not transfer.** A source that permits academic research has not
permitted this system's use, and a permission granted for a narrower purpose
does not widen to cover a broader one.

### Writing an assessment honestly

Forbidden, unless the conclusion is directly supported by the documented terms
recorded as evidence:

- "scraping is legal"
- "commercial use is allowed"
- any percentage of legal confidence

Required instead: the enum value, the evidence it rests on, and — where the
answer is not settled — an entry in `open_questions` naming the exact document
that still needs to be read.

---

## 6. Retention

The baseline is the policy default: **30 days raw, 365 days normalized**
(`data-retention-policy-v1.md` §2).

A `source_retention_policies` row overrides it, and resolution takes the
**minimum**: an override can only shorten. An override asking for longer
retention would be a platform's terms being used to weaken our own policy, which
§1 of the retention policy forbids.

Every override must record a `basis`. An override with no recorded justification
is indistinguishable from someone having wanted more data, and cannot be
re-verified when the source's terms change.

---

## 7. Access profiles and secrets

A profile records what is needed, never what it is:

- `requires_authentication`, `requires_api_key`, `requires_oauth`,
  `requires_account`, `requires_developer_app`, `requires_approval`
- `secret_references` — configuration **key names** only, e.g. `REDDIT_CLIENT_ID`
- rate limits, with `rate_limit_origin` ∈ `DOCUMENTED | OBSERVED`

**An unknown rate limit is recorded as unknown.** A number with no stated origin
is a guess, and a collector would trust it. `UNKNOWN` is a real answer and must
stay expressible.

The model refuses any `secret_references` entry that looks like a credential
value, so the prohibition is mechanical rather than remembered.

---

## 8. Who may change what

| Action | Path | Not possible via |
|--------|------|------------------|
| Register a candidate | edit `source-catalog-v1.json`, run `sros-source load` | HTTP |
| Record a review or evidence | same | HTTP |
| Enable a collector | `sros-source enable <id>` | HTTP; a JSON edit |
| Read the registry | `GET /api/v1/sources`, `sros-source list/show` | — |

There is **no write endpoint**. Authentication does not exist yet (ADR-005), so
an HTTP endpoint able to approve a source or enable a collector would make this
entire review process optional for anyone who can reach the service. The API is
read-only, and the runtime database role holds `SELECT` only on `registry.*`, so
the restriction is enforced twice.

Loading the catalog never enables a collector. A JSON file is not a review, and
the loader writes `collector_enabled = FALSE` unconditionally.

---

## 9. Consuming the registry

The Research Orchestrator asks the registry, per source, whether acquisition can
proceed (`sros_orchestrator.sources`). Three outcomes:

| Registry says | Plan |
|---------------|------|
| at least one eligible source | ACQUISITION is planned for those sources |
| sources exist, none eligible | ACQUISITION blocked, naming each source and its reasons |
| registry not consulted | ACQUISITION blocked — an unwired registry is a refusal |

The third row is deliberate. A planner with no registry wired must behave
identically to one that found nothing, or a missing integration would read as a
permission.

---

## 10. Current state

**Twenty-seven candidate sources** after Mission 1.7, across fourteen families.
The eligible count still depends on where you ask:

| Where | Eligible |
|---|---|
| From the catalog alone | **0** — a catalog can never assert its own conditions satisfied |
| An environment with the capabilities verified and no credential (CI, a fresh clone) | **2** — `world-bank`, `eurostat` |
| The same, plus `FRED_API_KEY` configured | **3** — `fred` joins them |

That spread is the model working, not a discrepancy. `fred` differs from the
other two by one condition whose answer is a property of the deployment rather
than of the code: with no credential it is **design-eligible and not runnable**,
and the canonical gate refuses it. Configuring the key satisfies that condition
through the same verifier as every other, and nothing else changes.

### Verdicts

| State | Count |
|---|---|
| `APPROVED` | 0 |
| `APPROVED_WITH_CONDITIONS` | 8 |
| `RESTRICTED` | 6 |
| `REQUIRES_REVIEW` | 10 |
| `PROHIBITED` | 3 |

**Eight sources are in an approving state and three are eligible.** The five
Mission 1.7 approved — `gdelt`, `wikimedia-pageviews`, `openalex`,
`npm-registry`, `pypi` — carry eleven conditions that no verifier can clear,
because the capabilities that would check them are parameterised for a collector
and none of the five has one. This is the state Mission 1.3 left the economic
three in, and Mission 1.4 is the shape of the work that resolves it.

### The bias the expansion made measurable

Every consumer-facing family is registered and **none is approving**:

| | Registered | Approving |
|---|---|---|
| `economic_data` | 3 | 3 |
| `knowledge`, `news`, `developer` | 9 | 5 |
| `social`, `community`, `gaming`, `creator`, `app_store` | 11 | **0** |

That is a fact about platform terms rather than about the review, and it is the
reason [`source-signal-coverage-v1.md`](source-signal-coverage-v1.md) exists:
seven of sixteen signal families have no usable source at all, `problem` and
`desire` among them.

### What is still true

See [`source-catalog-v1.md`](source-catalog-v1.md) for the full assessment
table, [`source-review-guide.md`](source-review-guide.md) for how to conduct a
review,
[`acquisition-authorization-v1.md`](acquisition-authorization-v1.md) for how a
condition is cleared, and
[`source-portfolio-v1.md`](source-portfolio-v1.md) for what to build next.

Several sources could not be assessed because their terms were not retrievable
at review time; per §1 rule 2 those are `REQUIRES_REVIEW` with the exact
outstanding documents named, rather than assumed. Mission 1.7 added four more of
those and confirmed that Mission 1.3's two are still unreachable.

**One collector exists** (`world-bank`, Mission 1.5) and `collector_enabled` is
true for it alone. `acquisition.raw_records` holds six records and
`normalized_records` six, unchanged by Mission 1.7.

**Federated networks cannot currently be expressed.** Mastodon and Lemmy are one
protocol with thousands of independently-governed instances, and this model is
one source with one policy. They are deliberately unregistered rather than
flattened into a verdict that would be false for most instances; the modelling
decision is **H-13** in the human review queue.

## 11. Still open

- **Evidence reliability weights** — blocked by **D-03**. The registry
  deliberately assigns no per-platform reliability number.
- **Jurisdiction analysis** — requires human or legal input
  (`data-retention-policy-v1.md` §7). `jurisdiction_review_required` defaults to
  true and no code sets it false.
- **Deletion mechanics** — retention semantics are defined; deletion logic is
  not implemented.
