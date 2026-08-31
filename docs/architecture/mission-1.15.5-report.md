# Mission 1.15.5 — Use-Profile-Aware Source Review, Eligibility & Authorization V1

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.15.5` · **ADR:** ADR-027

**Success criterion met.** The registry can now say, truthfully and at the same
time:

```text
ted-eu  under  commercial-multi-tenant-research-v1   REQUIRES_REVIEW
ted-eu  under  local-private-research-v1             APPROVED_WITH_CONDITIONS
```

and no authorization can be requested without naming which one it is about.

---

## 0. One correction, up front

Mission 1.15.4 reported that *"every approval in this registry is an answer to a
use case the model never records"*. **That was wrong in a way worth fixing.**

`PolicyReview.assessed_use_case` is a **required** field and has been since
Mission 1.0, and the catalog's own prose says *"a **COMMERCIAL multi-tenant
SaaS** … Every assessment below is scoped to that use."* The model's error
message even explains why it is required: *"an approval that does not say what it
approved cannot be relied on for anything else."*

**The use case was recorded. It had no identity.** It was prose — it could not be
required, compared or matched, and the gate never saw it. That is a smaller and
more precise gap, and it made the migration far more defensible: attaching the
legacy profile **canonicalises a sentence that was already there** rather than
inventing a scope for 55 reviews.

---

# The §50 questions

## What was structurally wrong with the old source policy model?

`evaluate_eligibility(source)` knew the source and nothing about what was being
done with it, while the reviewer had answered a question about a specific use.
The gate and the reviewer were answering different questions, and only the
reviewer knew it.

## Did historical reviews already implicitly assess a use case?

**Yes, and explicitly rather than implicitly** — in `assessed_use_case`, on every
review, from Mission 1.0.

## Was that use case persisted before?

**Yes, as prose.** What was missing was identity.

## What is `AssessedUseProfile`?

A registered, versioned entity carrying the facts a reviewer needs in order to
know what they are approving: deployment, operator scope, public access,
external customers, raw redistribution, raw resale, customer-facing source
access, derived internal analysis, commercial purpose, model inference, model
training, embeddings, personal-data posture.

A **registry**, not a closed enum — nothing branches exhaustively on it, it is
compared. That is `docs/CLAUDE.md` §Taxonomies applied unchanged.

## What canonical profiles now exist?

Two.

| | `commercial-multi-tenant-research-v1` | `local-private-research-v1` |
|---|---|---|
| Deployment | PUBLIC_MULTI_TENANT | LOCAL |
| Public access / customers / redistribution / resale | yes | **no** |
| Derived internal analysis · model inference | yes | yes |
| **Commercial purpose** | **yes** | **yes** |
| Model training · embeddings | no | no |

**No `public-commercial-service` was created**: it is the first profile under the
name the historical prose already used, and a second near-identical profile
would be the proliferation §5 warns against.

## What profile represents historical reviews?

`commercial-multi-tenant-research-v1`, on all 55.

## What profile represents current Startup Research OS runtime?

`local-private-research-v1`, declared through `SROS_USE_PROFILE`.

## Does local deployment mean non-commercial source use?

**No**, and this is the rule most easily taken backwards. `commercial_purpose` is
**true on both profiles**, asserted by test. The research this system produces is
used to launch commercial products, so a commercial-use right still has to be
positively granted by the source's own evidence.

## Can a source now hold different current verdicts under different profiles?

**Yes.** TED does.

## Is current-review uniqueness profile-scoped?

**Yes**, in the model, in the loader and in the database:
`UNIQUE (source_id, assessed_use_profile, review_version)`.

## Were historical review verdicts changed?

**No.** 5 / 13 / 8 / 3, asserted by test.

## Were historical evidence rows changed?

**No.**

## How was historical review migration handled?

A `DEFAULT` on the new column filled history in one statement and was **dropped
immediately after**, so a future review that fails to say what it assessed cannot
inherit an answer nobody gave. Recorded as a migration interpretation, not a
conclusion, in `use-profile-migration-v1.md`.

**Review row ids keep the historical derivation for the legacy profile**, because
rows hang off them — conditions, and the condition *verifications* recording who
checked what and when. Re-deriving every id would have orphaned them; deleting
them to tidy a reload would destroy the record the registry exists to keep.

## Must runtime authorization declare a profile?

**Yes.** `SROS_USE_PROFILE`, read at the entry point and passed down. A
collection job takes the profile as a parameter and falls back only to the
declaration.

## What happens when the profile is missing?

**It raises.** There is no default, because the convenient default is the narrow
local profile — exactly the one an operator running a public service would most
want assumed for them.

## What happens when it is unknown?

Refused: *no policy review exists for use profile 'x'*, and **never resolved
against another profile or the legacy verdict**.

## Can approval transfer between profiles?

**No**, asserted four ways: TED's local approval does not authorise the
commercial profile; an unknown profile returns `approval_state=None` rather than
the legacy answer; `world-bank` is approving under the legacy profile and refused
under the local one; and compliance configuration does not leak either.

## Is route/resource distinct from use profile?

**Yes** (§19). A profile answers *how and why*; `authorize_resource` answers
*which data*, unchanged, below the gate. No route is encoded in a profile id.

## Does `AcquisitionAuthorizationContext` contain the profile?

**Yes**, and it survives `to_json()`.

## Is the profile preserved in acquisition provenance?

**Reconstructible, and deliberately not duplicated.** The context carries it, the
job holds the context, and `source_policy_reviews` records which review each
verification was made against.

## Did any hard-to-reverse provenance decision require an ADR?

**Yes, and it is recorded as a future one.** If retention ever removes the job
record before the raw records it produced, the profile becomes
unreconstructible and a durable column on `RawRecord` becomes necessary.
ADR-027 says so. Adding a column later is cheap; adding it speculatively creates
a second place the profile can be wrong.

## What is TED's legacy-profile verdict?

`REQUIRES_REVIEW`, review v5, unchanged.

## Was a `LOCAL_PRIVATE_RESEARCH` TED review created?

**Yes** — version 1 under `local-private-research-v1`, by `mission-1.15.5`.

## If yes, what first-party evidence supports it?

Four documents, each re-cited with its applicability to *this profile* stated
(§17):

1. **Commission Decision 2011/833/EU** — reuse defined by purpose, granted
   commercially, without charge or application. Grants the six load-bearing
   activities.
2. **TED Developer Docs, Search API** — *"for analysis and reuse"*, *"primarily
   targeted at data reusers"*, commercial organisations and researchers named as
   audiences, `fields` parameter for minimisation at acquisition.
3. **TED Open Data Service** — *"publish it for analysis and re-use"*, *"use this
   information in your research and applications"*, Connect-your-app.
4. **TED and SIMAP legal notice** — the reuse sentence, and the source of the
   attribution, authenticity and third-party-rights conditions.

## What is its verdict?

`APPROVED_WITH_CONDITIONS` — 15 conditions (all 11 legacy ones carried forward
verbatim, plus 4) and 4 required conditions.

## Are Search API and ODS authorised?

**Yes**, both, and only those two.

## Is bulk mirroring still blocked?

**Yes.** `ted-bulk-xml-daily`, `ted-bulk-xml-monthly` and `ted-csv-historical`
are excluded **by name**, with `require_dataset_family` true so an unclassified
resource is denied. Profile support did not become a loophole.

## Is H-36A still open?

**Yes. NOT ESTABLISHED**, under both profiles.

## Is broad H-36B still open?

**Yes. NOT ADDRESSED** for broad corpus extraction, under both profiles.

**A profile changes the exposure and the acts performed; it does not change the
law.** What the local review relies on instead is the operator's own published
intended use for its two routes, plus the structural fact that Article 7(2)(b)'s
re-utilisation limb — *making available to the public* — is not engaged by a use
that redistributes nothing. Neither is a licence, and the review says so.

## Is model training blocked?

**Yes**, on both profiles and in the review's conditions.

## Is D-12 still open?

**Yes.** No embeddings.

## Is personal-data minimisation unchanged?

**Yes**, and now enforced at acquisition: the compliance profile lists the
allowed fields, requested through the Search API's `fields` parameter, with the
entire contact block excluded. `monetary_amount_type` is in the allowed list
deliberately — an amount without its semantic is the flattening into
`price_paid` that nothing downstream can undo.

## Can a TED local-profile `AcquisitionAuthorizationContext` now be built?

**No, and the refusal is the informative part.**

```text
build_authorization('ted-eu', 'local-private-research-v1')
  -> review conditions not satisfied:
       ted-database-right-residual-exposure-accepted
       ted-official-route-only
       ted-personal-data-minimisation
```

| Condition | Verification | State |
|---|---|---|
| `ted-attribution` | CAPABILITY | **SATISFIED** |
| the other three | HUMAN_CONFIRMATION | outstanding |

**No verifier in this repository can satisfy a `HUMAN_CONFIRMATION` condition,
and none ever will.** That is deliberate for the third one: a residual-risk
acceptance that code could satisfy would be a judgement nobody made.

The other two attempts refuse differently, which is the point:

```text
commercial-multi-tenant-research-v1  ->  policy review for use profile
                                         'commercial-multi-tenant-research-v1'
                                         is REQUIRES_REVIEW
invented-profile-v1                  ->  no policy review exists for use profile
                                         'invented-profile-v1'
```

## Were any collectors implemented?

**No.** No API client, no SPARQL client, no parser, no worker task. Asserted
against `IMPLEMENTED_COLLECTORS`, `IMPLEMENTED_NORMALIZERS`, the file tree, and
`SPARQLWrapper` anywhere in the repository.

## Was any external research data collected?

**No.**

## Did the existing 12 / 12 / 7 / 7 / 7 remain unchanged?

**Yes.** RawRecords 12, NormalizedRecords 12, Signals 7, Claims 7,
ClaimRevisions 7, Evidence 7, Reliability 0, Opportunities 0, Embeddings 0,
Scores 0, TED rows 0.

## Is the full test suite green?

**Yes** — see §2 below.

## If TED local official access is now authorization-ready, is the next mission TED Official API Collector V1?

**Not yet.** Three human confirmations stand between the review and eligibility.
Once recorded, the next mission is
**TED Official API Collector V1 — Local Private Research Profile**, scoped by
`ted-eu-local-official-route-readiness-v1.md`.

## If not, what exact blocker remains?

Three recorded operator decisions:

| Condition | What a person must record |
|---|---|
| `ted-official-route-only` | the deployed collector uses the Search API or the ODS, never the bulk packages |
| `ted-personal-data-minimisation` | the deployed profile requests only the authorised fields |
| **`ted-database-right-residual-exposure-accepted`** | a named operator accepts the residual, unresolved database-right exposure |

The first two are also blocked for a plain reason: **there is no collector yet**,
so there is nothing whose route or fields could be confirmed.

---

## 1. Three things worth recording

**The gap was smaller and better than reported, which made the migration
honest.** Mission 1.15.4 said the model never recorded the use case. It did, in
prose, required, since Mission 1.0. Discovering that turned the migration from
"invent a scope for 55 reviews" into "canonicalise the sentence they all
inherited" — and it is why the historical distribution could be asserted
unchanged rather than merely hoped to be.

**A required argument beats an assertion.** Making `use_profile_id` a
second-positional with no default meant mypy walked all 68 call sites before
anything ran, and removed the shape that would have been most dangerous:
`use_profile_id=None` meaning "the source's current review" is one careless edit
from a silent fallback to a global verdict. The tests then assert the
*signature*, which survives a rewrite of the body. Recorded as
`testing-strategy.md` §44.

**A regression was caught by the test that exists for exactly it.** The first
rebuild of `registry.source_eligibility` was based on migration 0004's
definition and silently dropped migration 0006's condition columns *and* the
`review conditions not satisfied` blocking reason — the rule that makes
`APPROVED_WITH_CONDITIONS` mean anything. `test_the_python_gate_and_the_sql_view_agree`
went red. The `GRANT SELECT` was missing too, which migration 0006 had recorded
failing exactly that way once.

## 2. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | pass |
| Pytest suites | pass — 1005 acquisition tests, database unchanged |
| `validate_source_registry` | pass — 29 sources, 42 evidence records, 0 warnings |
| All other validators | pass |
| Contracts generation `--check` | current |
| Generated catalog documents `--check` | current |
| `ruff` / `mypy` | pass |
| New tests | 38 in `test_use_profile_policy.py`, plus two Mission 1.15.4 assertions **inverted** rather than deleted |

## 3. Where this leaves the registry

**Twenty-nine approvals stopped answering an unrecorded question.**

The immediate effect is one source with two honest verdicts. The durable effect
is that the rule which has governed every review since Mission 1.8 — *a
permission obtained by describing a smaller product is a permission for a product
we are not building* — stopped being a sentence in a guide and became something
the gate enforces.

And deploying this system publicly can no longer inherit a permission granted for
a laptop. It requests a profile nothing has approved, and the gate refuses it by
name.
