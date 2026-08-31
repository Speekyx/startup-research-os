# Use-Profile-Aware Source Policy V1

**Authoritative.** Mission 1.15.5, ADR-027. How source permission is scoped to
the use it was granted for.

**One sentence:** a verdict has a subject, the subject is registered and
versioned, the gate requires it, and permission never transfers between
subjects.

---

## 1. The model

```text
        SOURCE  ×  ASSESSED USE PROFILE
                    ↓
              POLICY REVIEW          one CURRENT review per pair,
                    ↓                append-only version line per pair
          VERDICT + CONDITIONS
                    ↓
            eligibility gate         requires the profile, no default
                    ↓
   AcquisitionAuthorizationContext   carries the profile
                    ↓
              RESOURCE SCOPE         which datasets, below the gate
```

**A profile answers *how and why*. A resource answers *which data*.** They are
kept apart on purpose (§19): `authorize_resource` already narrows resources
correctly, below the gate, and folding routes into a profile id would have
produced `ted-search-api-local-private-v1` — an identity that changes when
either half changes.

## 2. The registered profiles

| | `commercial-multi-tenant-research-v1` | `local-private-research-v1` |
|---|---|---|
| Deployment | PUBLIC_MULTI_TENANT | LOCAL |
| Operator scope | MULTI_OPERATOR | SINGLE_OPERATOR |
| Public access | yes | **no** |
| External customers | yes | **no** |
| Raw redistribution | yes | **no** |
| Raw resale | yes | **no** |
| Customer-facing source access | yes | **no** |
| Derived internal analysis | yes | yes |
| **Commercial purpose** | **yes** | **yes** |
| Model inference | yes | yes |
| Model training | no | no |
| Embeddings | no | no |
| Personal data | MINIMISED | MINIMISED |

### `commercial_purpose` is true on both, and that is the point

Running locally does not make the use non-commercial. The research this system
produces is used to discover, evaluate and launch **commercial** products, so a
commercial-use right still has to be positively granted by the source's own
evidence (`docs/CLAUDE.md` §Deployment model).

**This is the rule most easily taken backwards**, and taking it backwards would
produce exactly the narrowed assessed use case §Source governance forbids: a
permission obtained by describing a smaller product is a permission for a
product we are not building. A test asserts it on every registered profile.

### Why there is no `public-commercial-service` profile

There is one: it is called `commercial-multi-tenant-research-v1`, under the name
the historical prose already used. A second, near-identical profile would be the
premature proliferation the mission warns against, and the property that matters
— an approval under one profile never authorising another — is demonstrated by
the two that exist.

## 3. Identity

`^[a-z][a-z0-9-]*-v[0-9]+$` — a slug carrying its **semantic version**.

If a profile's meaning materially changes, it becomes a new profile
(`local-private-research-v2`) rather than an edit. Reviews name a profile id, so
an edited profile would silently move every verdict that pointed at it into
answering a question nobody asked.

## 4. Fail-closed behaviour

| Situation | Result |
|---|---|
| Profile missing | **raises** — a caller that never decided what it was doing |
| Profile not registered | refused: *no policy review exists for use profile 'x'* |
| Registered, no review for this source | refused. **Absence is a refusal**, never a reason to consult another profile |
| Review not approving | refused, naming the profile |
| Approving, conditions unsatisfied | refused, naming the conditions |

**There is no fallback anywhere in that table** — not to another profile, not to
the source's legacy verdict, and not to a "best available" answer (§11).

## 5. The runtime declares its profile

```bash
SROS_USE_PROFILE=local-private-research-v1
```

Read once at the entry point and passed down. **Never inferred** from an
environment name, the host, a container, a user count or the absence of billing.

A profile is not a deployment environment: `development` and `production` say
where code runs, a profile says what is being done with somebody else's data,
and the same binary in the same container can be operated under either. Startup
Research OS may legitimately run in development while evaluating what a public
commercial deployment would be permitted to do.

**There is no default**, because the convenient default is the narrow local
profile — exactly the one an operator running a public service would most want
assumed for them.

Reporting commands (`sros-source`) default to the legacy profile and take
`--use-profile`, because a report is not an authorization and changing what an
existing command means is a worse failure than making the operator type a flag.
Collection commands have no such flag.

## 6. What `SourceRecord.review` means now

**The current review under the legacy profile, and nothing else.**

Kept rather than removed, because every document, validator and rendered catalog
written before ADR-027 was about that profile — so every existing statement
stays true.

**It is not an authorization input.** The gate uses `review_for(profile)`, and an
AST test asserts that `eligibility.py`, `authorization.py` and
`verification.py` never read `.review`. That fence is the only thing that makes
keeping it safe, and it exists because `.review` reads more naturally than
`.review_for(profile)` — which is precisely how the mistake would be made.

## 7. Conditions and evidence across profiles

**Conditions belong to the review that imposed them** (§18), and verification is
per `(source, profile)`. A narrower profile never relaxes an obligation: TED's
local review carries all eleven legacy conditions verbatim plus four of its own.

**A document may support several reviews** (§17). The same Decision, the same
legal notice and the same route documentation support TED under both profiles.
They are re-cited rather than duplicated into new prose, and each finding states
its **applicability to that profile** explicitly — because the same sentence can
be load-bearing for one use and irrelevant to another.

## 8. Reading a verdict

**Never report a naked verdict** (§31, §44). A source's standing is a table, not
a value:

```text
ted-eu
  commercial-multi-tenant-research-v1   REQUIRES_REVIEW            not eligible
  local-private-research-v1             APPROVED_WITH_CONDITIONS   not eligible
                                          (3 human confirmations outstanding)
```

`sros-source list` and the generated catalog documents present the **legacy**
profile and say so. That is not a rollup: it is one named profile's answer,
which is what those documents have always shown.

## 9. What this does not do

- **It does not resolve any legal question.** TED's H-36A and H-36B are open
  under both profiles. A profile changes the exposure and the acts performed; it
  does not change the law.
- **It does not rescue a restricted source.** Profiles exist to persist the
  question a review answered, not to find a narrower question a blocked source
  might pass.
- **It does not make anything eligible.** Eligibility still requires an
  approving review *and* every condition satisfied, and a `HUMAN_CONFIRMATION`
  condition is satisfiable by nobody in this repository.
