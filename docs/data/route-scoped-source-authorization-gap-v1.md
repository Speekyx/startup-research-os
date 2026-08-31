# Route-Scoped Source Authorization — Gap Analysis V1

**Authoritative.** Mission 1.15.4 §25, §26. Whether a source can stay globally
`REQUIRES_REVIEW` while a narrow official route and use profile are authorised.

**It cannot, in the current model, and the model should not be worked around.**

The gap is not a missing field. It is that **every approval in this system is a
statement about a use case the model never records**, so there is nowhere to put
a second, narrower answer.

---

## 0. The question, and the empirical answer

> Can a SOURCE remain globally `REQUIRES_REVIEW` for broad commercial/bulk reuse
> while a narrowly defined official access resource and use profile is authorised?

**No.** Demonstrated rather than asserted — this is Mission 1.15.4 §29's attempt,
run against the real catalog:

```text
ted-eu review v5 -> REQUIRES_REVIEW
build_authorization(ted-eu)  ->  AcquisitionNotAuthorizedError
    reasons:
      - policy review is REQUIRES_REVIEW
```

**One blocking reason, and it is not about the route, the resource, the use
profile or the evidence.** It is the source-level approval state. There is no
argument the caller could add — no route, no profile, no narrower scope — that
would change the answer, because `evaluate_eligibility` has no parameter for any
of them.

## 1. What the model does have

The registry is not crude. It already narrows in two dimensions **below** an
approving source:

```text
SOURCE  ──approval_state──►  the gate           evaluate_eligibility
   │                                            requires review.is_approving
   ├── access_profiles      ──►  routes         described, never approved
   │                                            individually
   └── ResourceScope        ──►  which datasets authorize_resource, every
        AuthorizedDataset                       rule denies, none permits
```

`authorize_resource` is a genuinely careful piece of design: every rule refuses,
a resource is allowed only when no rule objected, and an unexamined resource is
refused because it is unexamined. Mission 1.4 built it precisely so that *"a
source-level approval is not a resource-level one"*.

**But it all hangs below the gate.** The resource layer answers *which of an
approved source's resources*; it cannot answer *whether this source is approved
for this use*.

## 2. What the model does not have

```text
grep -rniE "use_profile|deployment_profile|LOCAL_PRIVATE|MULTI_TENANT" \
     --include=*.py --include=*.json --include=*.sql packages services infrastructure
→ (no matches)
```

**Zero occurrences.** There is no use-profile concept anywhere: not in the
contracts, not in the registry models, not in the compliance layer, not in the
database schema. The gap is total, not partial.

`SourceApprovalState` has seven values — `DRAFT`, `REQUIRES_REVIEW`,
`APPROVED_WITH_CONDITIONS`, `APPROVED`, `RESTRICTED`, `PROHIBITED`, `SUSPENDED` —
and **every one of them is a property of the source**, full stop. None is
relative to anything.

## 3. The thing that was always implicit

Here is the actual finding, and it is not about TED.

**Every review in this registry already assessed a use case. The model just never
recorded which one.**

`docs/data/source-review-guide.md` tells a reviewer to assess *"the assessed use
case"*, and `docs/CLAUDE.md` carries the rule that gives it teeth:

> **Do not narrow the assessed use case to rescue a source**: the use case
> describes the product, and a permission obtained by describing a smaller
> product is a permission for a product we are not building.

That rule exists because the use case is load-bearing. And the use case is
**nowhere in the data model.** Twenty-nine sources carry approval states that are
answers to an unrecorded question.

For twenty-eight of them that has cost nothing, because one product was being
built and one use case was assessed. TED is the first source where the product
has **two** shapes at once — what it is today, and what it intends to become —
and the model has one slot.

## 4. Three ways to hack it, and why each is worse than the gap

### A. Flip TED to `APPROVED_WITH_CONDITIONS` and let conditions hold the line

The tempting one. Conditions already carry scoping statements; condition 9 scopes
machine processing, condition 10 scopes licences per resource. Add condition 12:
*"local private research only"*.

**It fails, and not subtly.** `approval_state` is read by the eligibility view,
`validate_source_registry`, the portfolio documents, the coverage tables, the
priority document and every future consumer. All of them would report TED as
**approving** — for the commercial multi-tenant use case that was actually
assessed and is still unresolved. The conditions would be prose next to a boolean
that says otherwise, and the boolean is what code reads.

This is the *"local authorization silently migrating to production SaaS
authorization"* that §8 exists to prevent, and it would happen the first time
somebody deployed the product publicly without re-reading a condition.

### B. Give a source two current reviews, one per profile

Reviews are an **append-only version history of one assessment**. `source.review`
means "the current answer". Two current reviews means two answers to one
question, which the codebase refuses everywhere else — `claim_type` was dropped
from `scoring.evidence` for exactly this reason, and the compliance layer refuses
an authorization whose config targets a different review version.

Without a discriminator, `source.review` becomes ambiguous, and every caller
inherits a coin-flip.

### C. Encode the profile as a verifiable condition

Closer to right, and still insufficient. Conditions are cleared by verifiers
against environment state, and *"this deployment is local and private"* is
genuinely environment state a verifier could check.

But **conditions gate an approving source; they do not create approval.** Option
C still requires option A to get past the gate, and inherits A's failure whole.

## 5. The minimal extension

Not built in this mission. Proposed, so the next one starts from a design rather
than from the same afternoon of reading.

**Record the thing that was always true, then let the gate ask for the right
one.**

```text
1.  Review gains  assessed_use_profile   a closed vocabulary value.
                                         Every existing review is
                                         COMMERCIAL_MULTI_TENANT — which is what
                                         they DID assess. This is labelling, not
                                         a new claim about any source.

2.  A source may carry one CURRENT review PER PROFILE.
                                         source.review becomes
                                         source.review_for(profile). Not two
                                         answers to one question: (source,
                                         profile) is one question with one
                                         answer, and the version history stays
                                         append-only within each profile.

3.  evaluate_eligibility(source, use_profile, …)
                                         requires an approving review FOR THAT
                                         PROFILE. A source with no review for
                                         the requested profile is refused, in
                                         the same voice as every other refusal:
                                         "no policy review exists for use
                                         profile X".

4.  build_authorization(source, use_profile, …)
                                         threads it through and STAMPS the
                                         profile onto the context, so a
                                         collector holding an authorization can
                                         be asked which profile it is for.

5.  The runtime DECLARES its profile from configuration.
                                         Never inferred from whether a public
                                         port happens to be open, never
                                         defaulted. A missing profile is an
                                         error in every environment — the same
                                         rule workspace_id already follows.
```

**Why the fail-closed direction is the whole design.** A profile the review does
not name is refused. Deploying publicly does not silently promote a local
authorization; it requests a profile nothing has approved, and the gate says so
by name.

**Why it is minimal.** It adds one field, one lookup and one parameter. It
creates no new table, no rule language, no second approval concept, and it makes
`authorize_resource` and the whole conditions machinery work unchanged
underneath. It also makes twenty-eight existing reviews *more* honest by writing
down what they assessed.

**Why it is not free.** It touches `evaluate_eligibility`, which is the most
safety-critical function in the repository, and it multiplies the review surface
per source. It needs an ADR, a migration, and a mission of its own. Doing it as a
side effect of a TED mission would be the change control violation
`docs/CLAUDE.md` §Change control describes.

## 6. The profile that would be authorised

Defined here so the extension has a first customer, and **explicitly not
authorised** — no `AcquisitionAuthorizationContext` exists and none can be built.

```text
profile          LOCAL_PRIVATE_RESEARCH
source           ted-eu
routes           TED Search API          https://api.ted.europa.eu/v3/notices/search
                 TED Open Data Service   https://data.ted.europa.eu/  (SPARQL)
resource         contract award notices and contract notices, eForms,
                 1 March 2023 onwards  — the ODS coverage window
fields           notice id · publication date · award/contract date ·
                 buyer organisation · supplier organisation · CPV ·
                 procurement classification · monetary amount ·
                 MONETARY AMOUNT TYPE · currency · country/region ·
                 award status
                 …requested through the Search API `fields` parameter, so
                 minimisation happens AT acquisition
discarded        every natural-person field, the whole contact block, logos,
                 unrelated full text
processing       extraction · classification · inference · structured analysis
NOT authorised   model training · embeddings (D-12) · redistribution · resale ·
                 public or multi-tenant deployment · bulk XML packages ·
                 the ted-csv historical CSV subset · any resource not named above
```

**What still would not be settled even with the extension built.** H-36A and
H-36B stay open. The extension changes what the registry can *express*; it does
not change what the Publications Office has *said*. A narrow-profile review would
still have to argue that the volume taken by bounded queries under a local
private profile sits within what the operator's documented intended use and the
Decision cover — and that argument is a judgement the operator of this system
makes and records, not a legal resolution of the database right.

## 7. Recommendation

| | |
|---|---|
| **Do not** | flip TED's verdict, add a use-profile condition to an unapproved source, or build a collector against a source the gate refuses |
| **Do** | keep TED at `REQUIRES_REVIEW`, keep the route evidence in review v5 where it belongs, and treat the extension as its own mission with an ADR |
| **In parallel** | review `usaspending` (H-35). It is the only other transaction-class candidate, and it does not compete with either the clarification reply or this extension |

**The gap is the useful finding.** Mission 1.15.4 set out to authorise a narrow
route and instead discovered that twenty-nine approvals are answers to a question
the model does not record. That is worth more than a TED authorisation would have
been, and it was only visible because a source finally needed two answers.
