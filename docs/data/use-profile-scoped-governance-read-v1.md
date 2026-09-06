# Use-profile scoped governance reads — v1

**Status: adopted, Mission 1.75.** Governs the three HTTP read surfaces that serve
source governance state.

---

## 1. The defect this replaces

`registry.source_policy_reviews` has been keyed on `(source_id, assessed_use_profile)`
since Mission 1.15.5, and `registry.source_eligibility` has produced one row per
`(source, use profile)` since the same migration. The HTTP layer joined that view on
`source_id` alone.

| route | what it did |
|---|---|
| `GET /api/v1/sources` | returned a source **once per profile that had reviewed it** |
| `GET /api/v1/sources/{id}` | returned **an arbitrary profile's** verdict, review body and evidence |
| `GET /api/v1/sources/{id}/eligibility` | returned an arbitrary profile's verdict beside the **union** of every profile's conditions |

Mission 1.15.7 found the first. Mission 1.17 grew it from one source to six and recorded
it as a tripwire rather than fixing it, because **choosing which profile the HTTP layer
answers for is a design decision and there was no legitimate default.** By Mission 1.19 it
was eight sources, and the tripwire predicted it would keep growing.

The database was never wrong. `require_eligibility_for_collector` looks up the row for the
profile enablement was granted under, and the view's own COMMENT says an absent row is a
refusal. **The HTTP layer was the defective boundary**, and this document is the decision
that was missing.

## 2. The contract

    ONE HTTP GOVERNANCE READ
    + ONE EXPLICIT USE PROFILE
    = ONLY FACTS BELONGING TO THAT EXACT PROFILE

`use_profile` is a **required query parameter** on all three routes.

## 3. Why there is no default

Not caution. Both registered profiles are real deployments that reach **different
verdicts about the same sources**, so any default would answer a question the caller did
not ask — and would look exactly like an answer.

Every candidate default was available and each is refused for its own reason:

| candidate | refused because |
|---|---|
| `local-private-research-v1` | this deployment's profile is not every caller's profile, and the API is not the deployment |
| `commercial-multi-tenant-research-v1` | the profile with the most reviews is not the profile the caller meant |
| environment-selected | makes the same request return different governance facts on different machines |
| workspace-derived | `use_profile` is **not** `workspace_id`; see §7 |
| first available review | makes the answer depend on row order |
| fall back to the other profile | the exact leak this repairs |

## 4. Request semantics

- **Missing** `use_profile` → **422**. FastAPI's own required-parameter refusal, which is
  also what makes it discoverable in OpenAPI as `required: true`.
- **Unregistered** `use_profile` → **422 `contract_violation`**, raised as a
  `ContractError` naming the field.
- **Validity** is resolved against `registry.use_profiles`, the canonical vocabulary.
  Not a hard-coded pair, and not the set of profiles that happen to have reviews — a
  registered profile nobody has reviewed under yet is **valid**, which is the state every
  new profile begins in.
- **Status is not filtered.** Reading the governance history of a retired profile is a
  legitimate question, and inventing a status rule inside a router would be a governance
  decision made in the wrong place.

## 5. Response semantics

**`/sources`** returns **each registered source exactly once**. The profile is a join
predicate, so there is no duplication to deduplicate. The join is `LEFT`: a source the
requested profile has never reviewed is still **listed**, because hiding it would make
"not reviewed under this profile" indistinguishable from "not registered".

For every source, identity and catalog metadata stay global; **approval state, staleness,
evidence count, blocking reasons and eligibility come only from the requested profile.**

**Absent review = refusal.** A source with no row for the requested profile returns
`approval_state: null`, `collector_eligible: false`, and one blocking reason naming the
profile. It never borrows another profile's verdict, conditions, evidence or approval.

**The response says which profile it describes** — on the envelope and on **each source
object**, because a single source object is what a caller stores, forwards and compares.

**`collector_enabled` carries its own profile.** It is a column on the source with a
`collector_use_profile`, and the trigger checks eligibility under *that* profile. Served
flat beside a scoped verdict it reads as "enabled for you", which for a source enabled
under one profile and listed under another is false. So `collector_use_profile` and
`collector_enabled_for_requested_profile` are returned with it.

## 6. Cross-profile rules

1. Conditions belong only to the requested profile.
2. Review, policy state and review evidence belong only to it.
3. A missing review stays missing; another profile's review cannot satisfy it.
4. One `condition_key` under two profiles is **two facts**, not one.
5. An approving profile never upgrades a restricted one.
6. No response is a union over profiles.
7. Ordering is deterministic and repeated requests return the same result.

## 7. `use_profile` is not `workspace_id`

A workspace says **whose data** is being worked on. A use profile says **which governance
regime** the caller is asking about. Neither answers the other, `RequestContext`
deliberately carries no profile, and a request with a tenant header still gets a 422
without one. Source reviews remain **global platform metadata** and are not
workspace-owned.

## 8. What this does not establish

- It does not change any verdict. No review was created, edited or superseded.
- It does not make historical `RawRecords` profile-bearing. Records written before
  `use_profile` existed remain without it, and inventing their profile would create
  provenance that was never recorded.
- It does not decide which profile any particular caller should ask for.
- It does not touch the CLI's own reporting paths beyond removing one unused hard-coded
  default.
- It says nothing about authorisation. There is still none, and a caller naming a profile
  is not a caller entitled to it.
