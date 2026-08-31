# TED-EU Authorization Bootstrap V1

**Authoritative.** Mission 1.15.6. How the pre-collector authorization deadlock
was resolved without weakening TED governance, and what is still outstanding.

**State: `APPROVING_BUT_NOT_ELIGIBLE`, with ONE outstanding condition.** Three
of TED's four conditions under `local-private-research-v1` now verify
`SATISFIED` against configuration. The fourth is a human judgement, it has not
been recorded, and `AcquisitionAuthorizationContext` still cannot be built.

**No collector exists, no TED procurement data has been collected, and neither
follows from this document.**

---

## 1. The deadlock

Mission 1.15.5 left TED approving under the local profile and ineligible, with
three `HUMAN_CONFIRMATION` conditions outstanding:

```text
build_authorization('ted-eu', 'local-private-research-v1')
  review conditions not satisfied:
    ted-database-right-residual-exposure-accepted
    ted-official-route-only
    ted-personal-data-minimisation
```

Its own readiness document recorded why two of the three could not move:

> The first two are outstanding for a plain reason as well — **there is no
> collector yet**, so there is nothing whose route or field selection a person
> could confirm.

That is a **bootstrap**, and it is circular in the direction that matters. A
collector may only run with an authorization context; the context cannot be
built until a person confirms what the collector does; the person cannot confirm
it until the collector exists. Left alone, the loop breaks in exactly one place
and it is the wrong one: somebody writes the collector first and confirms it
afterwards, which is the sequence §12 of the mission brief exists to forbid.

```text
NOT THIS                                  THIS
policy review                             policy review
  -> a human promises a future               -> use profile
     collector will behave                   -> resource
  -> authorization                           -> COLLECTOR CONFIGURATION
  -> collector implementation                -> condition verification
                                             -> authorization
                                             -> network acquisition
```

## 2. The finding

**Two of the three conditions were never about a collector.** They are about the
**configuration a collector is given**, and that configuration exists before any
code does.

| Condition | What it actually requires | Classification |
|---|---|---|
| `ted-official-route-only` | that acquisition binds to one named access route, and that the route is not the bulk packages | **CONFIGURATION_INVARIANT** |
| `ted-personal-data-minimisation` | that the field selection sent to the source is a subset of the authorised fields | **CONFIGURATION_INVARIANT** |
| `ted-database-right-residual-exposure-accepted` | that a named person accepts an unresolved legal exposure | **HUMAN_JUDGMENT** |

`ted-attribution` was already **MACHINE_VERIFIABLE_INVARIANT** and already
`SATISFIED`, verified by the `source-attribution-display` capability.

No new verification taxonomy was introduced. `ConditionVerification` still has
its five values, and both reclassified conditions use `CAPABILITY` — the
existing semantic for *a named product capability is implemented and enabled,
checked against this source's real configuration*.

### 2.1 Why `ACCESS_METHOD` could not carry the route condition

The obvious candidate was the existing `ACCESS_METHOD` verification and its
`AccessRestriction`. It does not fit, and the reason is worth recording because
it looks like it should.

**`AccessRestriction` is a statement about the SOURCE. The route condition is a
statement about US.** `_verify_access_method` passes when the registry records
*exactly* the approved access profiles and no others. TED can be reached by bulk
XML: the daily and monthly packages are published, documented and downloadable
without signing in, and `ted-bulk-xml` is in the registry because that is true.

Making `ACCESS_METHOD` pass would have required deleting `ted-bulk-xml` from the
registry — **falsifying a fact about a source in order to obtain a permission**,
which is the worst habit this layer could acquire. An access profile says how a
source *can* be reached and has never said anything about permission
(`source-registry-v1.md` §8).

So the two questions are different, and both are worth asking:

| Question | Answered by | Subject |
|---|---|---|
| Can this source be reached only by approved paths? | `ACCESS_METHOD` | the source |
| Does our acquisition bind to an approved route? | `source-route-binding` | our configuration |

### 2.2 The defect the investigation found

`build_authorization` put **every registered access profile** into
`context.access`, because an access profile is a fact about the source and the
context had nothing to filter it with. A collector then selects its route by
label from that tuple — `GdeltWebNgramCollector._route` is the existing pattern,
and its own docstring records the hazard:

> GDELT carries a second, deferred profile for the DOC API; taking
> `context.access[0]` would work today and would silently authorise
> `api.gdeltproject.org` the day the profile order changed.

That was survivable while no approving source had a route its review refused.
**TED is the first that does, and its refused route is a full bulk download of
the corpus whose database-right exposure is the open question.** A TED context,
had one been buildable, would have handed a collector `ted-bulk-xml` with its
endpoint — and the transport's host allowlist is derived from `context.access`,
so the blocked host would have been allowlisted too.

This was not hypothetical. It was the behaviour.

## 3. What was built

### 3.1 `RouteAuthorization`

Per `(source, use profile)`, in `source-compliance-v1.json`:

```json
"route_authorization": {
  "allowed_labels": ["ted-search-api", "ted-open-data-sparql"],
  "blocked_labels": ["ted-bulk-xml"],
  "preferred_label": "ted-search-api",
  "basis": "..."
}
```

Four rules, each refused at load time:

- **an empty allowlist is refused.** It denies everything, which is a
  source-level refusal wearing a route restriction's name;
- **an empty blocklist is refused.** Naming a permitted path without refusing an
  excluded one records a preference, not a restriction — the same argument
  `_verify_access_method` already makes about excluded dataset families;
- **a label in both lists is refused.** Which rule applies would depend on which
  the reader checked first;
- **a bound with no stated basis is refused.** A restriction nobody can
  re-check against the review that granted it survives every later review by
  looking deliberate.

`preferred_label` is an **implementation preference and never a permission**. It
must name an authorised route, and it widens nothing.

**The load-bearing change is in `build_authorization`**: where a route
authorization exists, `context.access` carries the authorised routes **and no
others**. A blocked label is not in the tuple, so there is no endpoint to read,
no host to allowlist, and the transport has nothing to be pointed at. Route
binding survives into acquisition execution because the alternative was never
put in the collector's reach.

An authorised label the registry does not record is **refused**, not skipped: a
route with no access profile has no endpoint and nothing to check a host
against, and skipping it would quietly narrow the authorisation to whatever
happened to exist.

Sources with no reviewed route restriction are unchanged. `None` means the
question has not been asked for that `(source, profile)` — not that every route
is fine — and every entry predating this mission is in that state. See §7.

### 3.2 Acquisition-time field minimisation

`DataMinimisationProfile` held the allowed and excluded categories since Mission
1.4 and **nothing consulted them**. `permits(category)` answered a question
about one category and had no caller in the gate.

`refusals(requested)` answers the question a request actually asks — *may I ask
for these* — and it fails closed in every empty shape:

| Request | Result |
|---|---|
| `None` | refused: an unstated selection is not a minimised one |
| `()` | refused: a request naming no field is not a request |
| a field in `excluded` | refused **by name** |
| a field in neither list | refused: an unreviewed field is not an approved one |
| the authorised set | allowed |

An excluded field is refused whether it arrives alone or hidden among authorised
fields, which is the shape a real over-broad request has.

**This is not collect-then-filter.** The Search API's request body carries a
`fields` parameter, so a request that took the contact block and discarded it
afterwards would have retrieved the contact block, and the obligation is about
what is retrieved. There is deliberately no method here that takes a collected
record and removes fields from it; filtering after collection may exist later as
a defensive second layer, but it cannot be the primary control
(`ted-eu-local-private-research-review-v1.md`, condition 14).

### 3.3 Two capabilities

| Capability | Establishes |
|---|---|
| `source-route-binding` | the gate accepts exactly the reviewed routes, and refuses the blocked ones by name, an unreviewed one, and acquisition that names no route |
| `source-field-minimisation` | the gate accepts the authorised selection, and refuses each excluded field alone and in company, an unreviewed field, and a request that states no selection |

Each check asserts its **control case** first — the authorised routes are
accepted, the authorised field set is accepted — because a gate that refused
everything would pass every refusal assertion and authorise nothing, which is a
refusal dressed as a restriction.

Both report **unimplemented** when the restriction they check does not exist. A
capability that returned `SATISFIED` for a source with no route authorization
would satisfy the condition by having no rules.

### 3.4 The registry gained the route it already authorised

The local review authorises the TED Open Data Service SPARQL endpoint, and the
registry recorded **no access profile for it** — so an authorised route had no
endpoint, no rate-limit record and nothing to check a host against.
`ted-open-data-sparql` was added: `OFFICIAL_API`, `https://data.ted.europa.eu/`,
no authentication, rate limit **UNKNOWN**.

That is a fact about how the source can be reached, recorded because it is true.
It grants nothing; the review decides that, and the review already had.

## 4. What this establishes, stated precisely

**Not** *"the future collector follows the rules."* Nothing in this repository
can establish that, and a capability that claimed to would be lying about its
own contract.

**This**: *the configuration supplied to authorization satisfies the policy
constraints, and the authorization hands a collector nothing else.*

The two halves are different in kind and both are needed:

- the **verified** half — the route gate and the field gate accept what the
  review named and refuse everything else, checked against TED's real
  configuration with no network call and no collector;
- the **structural** half, which is the load-bearing one — a collector may only
  run with an `AcquisitionAuthorizationContext`, and the context carries only
  authorised routes. There is no blocked endpoint in it to reach.

The remaining obligation is on the collector mission: **it must be built so that
it cannot execute without an authorized configuration**, the way
`test_collector_conformance.py` already asserts for resource access.

## 5. The condition state now

| Condition | Verification | State |
|---|---|---|
| `ted-attribution` | `CAPABILITY` `source-attribution-display` | **SATISFIED** |
| `ted-official-route-only` | `CAPABILITY` `source-route-binding` | **SATISFIED** |
| `ted-personal-data-minimisation` | `CAPABILITY` `source-field-minimisation` | **SATISFIED** |
| `ted-database-right-residual-exposure-accepted` | `HUMAN_CONFIRMATION` | **OUTSTANDING** |

```text
build_authorization('ted-eu', 'local-private-research-v1')
  review conditions not satisfied:
    ted-database-right-residual-exposure-accepted
```

**One genuine human decision remains, and it is the right one.**

## 6. The residual database-right exposure stays human

`ted-database-right-residual-exposure-accepted` was not reclassified and must
not be. It is not an objective property of anything; it is a person deciding to
carry a risk that nobody has resolved.

**Nothing can satisfy it but a person.** A `HUMAN_CONFIRMATION` condition
dispatches to the human branch before any configuration is consulted, so no
route authorization, no minimisation profile and no capability can reach it. The
database refuses a hand-set `satisfied` boolean with no `SATISFIED` verification
behind it. And no verifier in this repository writes one.

**The existence of this mission is not acceptance.** Neither is the fact that
the deployment is local: local is not non-commercial, and a narrower use changes
the exposure without changing the law. H-36A is still NOT ESTABLISHED and H-36B
is still NOT ADDRESSED, under both profiles.

### 6.1 Nothing was recorded

The operator supplied no acceptance in this mission, so none exists. The
condition is outstanding, TED is ineligible, and the gate says so by name.

### 6.2 The exact statement a later action must record

Recording it is a **separate, explicit operator action**. This is the text:

> I, ⟨full name⟩, operating Startup Research OS as its single local operator,
> record the following.
>
> 1. I have read `ted-eu-local-official-route-readiness-v1.md` and
>    `ted-eu-authorization-bootstrap-v1.md` in full.
> 2. I understand that **H-36A is NOT ESTABLISHED**: nothing determines whether
>    a sui generis database right subsists in the TED corpus, or who would hold
>    it.
> 3. I understand that **H-36B is NOT ADDRESSED** for broad corpus extraction:
>    nothing establishes that such a right, if it subsists, has been granted or
>    waived.
> 4. I understand that the local approval of `ted-eu` is **deliberately narrow**.
>    It rests on Commission Decision 2011/833/EU, the TED and SIMAP legal notice,
>    the `COM_REUSE` dataset metadata and the Publications Office's own published
>    intended use for its two query routes — and that **none of those four is a
>    database-right grant**.
> 5. I understand that it further rests on bounded, purpose-scoped queries
>    through the official routes, on field minimisation at acquisition, and on
>    the fact that nothing is redistributed — and that **if any of those three
>    stops being true, the basis for this acceptance stops with it**.
> 6. I understand that **this is not a legal clearance**, that no lawyer has
>    reviewed it, and that it resolves neither H-36A nor H-36B.
> 7. I accept the residual, unresolved database-right exposure for **`ted-eu`
>    under `local-private-research-v1`, at review version 2, and for nothing
>    else**.
>
> This acceptance does **not** extend to `commercial-multi-tenant-research-v1`;
> to any future public, customer-facing, sold, subscription-based or
> multi-tenant deployment; to the bulk XML packages; to the `ted-csv` historical
> subset; to any other source; or to a materially changed future TED review.
>
> Recorded by: ⟨identifier⟩ · Date: ⟨ISO 8601⟩

### 6.3 Where it is recorded

**The mechanism already exists and needs no extension.**
`registry.source_condition_verifications` (migration 0007) is the append-only
log, and its own comment says what a human row is:

> **WHO decided.** A name, not a person: these are programs. A human decision is
> recorded by a human writing a row with their own identifier here.

Every field §18 asks for is present or derivable:

| Required | Column |
|---|---|
| `source_id` | `source_id` |
| `condition_id` | `condition_id` |
| `condition_key` | `condition_key` |
| review id / version | via `condition_id` → `registry.source_review_conditions.review_id` |
| **use profile** | via that review's `assessed_use_profile` (migration 0021) |
| actor | `verifier` |
| decision | `result` |
| `recorded_at` | `verified_at` |
| rationale | `reason`, and `reference` for the document |

**Profile scoping is structural, not a convention.** The row hangs off a
condition, the condition hangs off one review, and that review names exactly one
`assessed_use_profile`. An acceptance recorded against TED's local review cannot
reach the commercial profile, because the commercial review does not carry the
condition an acceptance would clear.

**No CLI command writes one, and none was built.** A verb that records human
confirmations is one flag away from a script that records them, and the property
worth more than the convenience is that every such row was typed by a person who
meant it.

## 7. The general rule, and what was deliberately not migrated

**Objective properties of what a collector is CONFIGURED to do should be
configuration-verifiable, not human-confirmed.** A `HUMAN_CONFIRMATION`
condition describing a mechanical property is a real cost: it cannot be checked,
it cannot regress visibly, and it makes a person the load-bearing element for
something a person is worse at than a gate.

The rule has a boundary, and the boundary is the point:

- **objective, and a property of configuration** → make it configuration-verifiable;
- **a judgement, a risk acceptance, a legal conclusion, a promise about the
  future** → `HUMAN_CONFIRMATION`, and `source-review-guide.md` §9's instruction
  stands: *do not reword a legal obligation until it sounds checkable — that
  produces a verifier that checks something else.*

Recorded in `acquisition-authorization-v1.md` §6 and `source-review-guide.md`
§9.

**No other source's conditions were migrated.** The route mechanism is generic
and only TED uses it. The four other approving sources keep the previous
behaviour — `context.access` carries every registered access profile — because
`route_authorization` is absent for them and absence means the question was not
asked. That is a known, named gap rather than a silent one:

> **Open:** `world-bank`, `eurostat`, `fred` and `gdelt` have no reviewed route
> restriction. GDELT is the one that matters, because it carries a second,
> deferred access profile for the DOC API that no review has assessed. Adding a
> route authorization for it is a review act, not a configuration edit, and it
> belongs to a mission that says so.

## 8. What did not change

- **`ted-eu` + `commercial-multi-tenant-research-v1` = `REQUIRES_REVIEW`.**
- **`ted-eu` + `local-private-research-v1` = `APPROVED_WITH_CONDITIONS`.**
- **H-36A NOT ESTABLISHED. H-36B NOT ADDRESSED**, under both profiles.
- **Model training NOT AUTHORISED. Embeddings blocked, D-12 open.**
- **Bulk XML blocked. `ted-csv` historical blocked.** Under every profile, at the
  route gate and again at the resource gate.
- **Redistribution NOT PERMITTED** under this profile, which is what keeps the
  Article 7(2)(b) re-utilisation limb structurally unengaged.
- **Local review v1 was not rewritten.** v2 is appended, carries every
  assessment, condition, open question and evidence row of v1 unchanged, and
  differs in exactly two condition classifications. v1 still records that both
  were `HUMAN_CONFIRMATION` when it was written.
- **No collector, no client, no parser, no normalizer, no network call.**
- **No TED procurement data.** Research counts unchanged.

## 9. Next mission

**TED Official Search API Collector V1 — `local-private-research-v1`**, if and
when the operator records the acceptance in §6.2.

Until then `build_authorization` refuses and the collector has nothing to be
built against, which is the correct order and the one the bootstrap was blocking.

The collector must: obtain its route from `context.access` and bind to
`ted-search-api`; request only fields `context.authorize_fields` permits; issue
bounded, purpose-scoped queries; throttle conservatively against an
**UNKNOWN** rate limit rather than an invented one; preserve provenance
including the use profile; distinguish every monetary semantic rather than
flattening into `price_paid`; **never become a TED mirror**; and remain refused
under `commercial-multi-tenant-research-v1`.
