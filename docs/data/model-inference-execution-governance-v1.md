# Model Inference Execution Governance V1 — where inference may run, and when content may leave

**Authoritative for the BOUNDARY.** Mission 1.23, ADR-033.

> **This document authorises no transmission.** It defines the four gates that
> must all pass before source-derived content may leave this deployment for a
> third-party model processor, and records which of them currently pass. At the
> time of writing the boundary is closed: no provider is configured, so nothing
> can be sent, and the last gate says so by name rather than by silence.

---

## 1. The question that had no slot

Mission 1.22 tried to evaluate semantic equivalence over Stack Exchange
questions and stopped before calling a model. The reason was not a missing
credential. It was that the contract could not express the question it needed to
ask.

`model_processing` asks **may a model read this material**. Stack Exchange's
local review had answered it: `PERMITTED_WITH_CONDITIONS`, on CC BY-SA 4.0's
grant to reproduce and to produce Adapted Material.

The question Mission 1.22 actually had was different:

> May this material **leave the deployment** so that a **third party's** model
> can read it?

That is not the same act. It has different exposure, a different counterparty,
and a different instrument deciding it. One field was answering a question that
is two.

**The repository has met this shape before.** A content licence decides REUSE; a
separate instrument decides ACCESS. Mission 1.18 found Stack Exchange's API
Terms constraining a route CC BY-SA left open. Mission 1.21 found a robots
directive closing a route a perfect licence had opened. Here a licence permits
processing while saying nothing at all about a processor.

---

## 2. The four gates

Authorization is the conjunction. `authorize_external_inference` evaluates all
four **before any source text is serialised**, and returns a decision a caller
must hold before it may build a request.

| # | Gate | Subject | Where it is recorded |
|---|------|---------|----------------------|
| 1 | `external_model_transmission` | may THIS SOURCE's material undergo the act | the source's review, per profile |
| 2 | `external_model_egress` | does THIS DEPLOYMENT permit the class of egress | the use profile |
| 3 | provider posture | what THIS PROCESSOR does with what it receives | `model-provider-policy-v1.json` |
| 4 | configuration | is that provider actually wired here | the environment |

**Neither substitutes for another.** A permissive source cannot rescue a silent
deployment. A permissive deployment cannot replace a source review. An approved
provider grants no copyright permission over anything, and a licence approves no
provider.

### Every gate reports, even after one refuses

All four are evaluated whatever the first one says. An operator who is told only
the first failure will fix it and be refused again — three more times, once per
remaining gate. The refusal codes are distinct for the same reason: a governance
decision must not look like an outage.

```
SOURCE_EXTERNAL_MODEL_TRANSMISSION_NOT_ASSESSED
SOURCE_EXTERNAL_MODEL_TRANSMISSION_REFUSED
SOURCE_REVIEW_MISSING_FOR_PROFILE
PROFILE_EXTERNAL_MODEL_EGRESS_NOT_ASSESSED
PROFILE_EXTERNAL_MODEL_EGRESS_DENIED
PROVIDER_DATA_USE_POSTURE_NOT_ASSESSED
PROVIDER_NOT_APPROVED
PROVIDER_IS_A_TEST_DOUBLE
PROVIDER_NOT_CONFIGURED
```

---

## 3. NOT_ASSESSED is a state, not a default that decides

Both new fields distinguish three things where a boolean would collapse two:

- **NOT_ASSESSED** — nobody looked. Refuses.
- **DENIED / NOT_PERMITTED** — somebody looked and said no. Refuses.
- **PERMITTED** — somebody looked and said yes, on a recorded basis.

The two refusing states are not interchangeable. One is a decision that can be
cited; the other is a question that is still open, and telling them apart is most
of what this registry is for.

**Every review written before ADR-033 reads NOT_ASSESSED**, because the contract
had no slot and no reviewer could have answered. Migration 0027 adds both columns
nullable with no default and writes no existing row. A mass `UPDATE` to any value
would have invented sixty-four answers.

---

## 4. Why this activity is not one of rule 8's six

Rule 8 requires a GRANT for six materially required activities before a source is
eligible at all. `external_model_transmission` is deliberately **not** among
them.

It gates **one operation**. World Bank's deterministic collector does not become
ineligible because nobody assessed model egress for World Bank — that would make
a contract addition a breaking change for twenty-nine sources, and would punish
sources for a question they were never asked.

The property is tested directly: for every registered source, the reasons an
ordinary acquisition is refused never mention this activity.

---

## 5. Provider posture is decided on first-party contract text

A provider is approved on what **its own terms** commit to, not on preference.
Two properties are load-bearing: whether content submitted for inference is used
to train the provider's models, and whether retention is documented and bounded.

`docs/data/model-provider-policy-v1.json` records the posture, the exact route
assessed, and the evidence. Two conclusions there are worth stating here because
they are the whole reason a policy file exists:

- One provider's commercial terms state that it may not train models on customer
  content from the services, with backend deletion inside a bounded window. That
  route is **APPROVED**.
- Another provider's **unpaid** route states that submitted content is used to
  provide, improve and develop its products and machine learning technologies,
  that human reviewers may read the input and output, and that confidential
  information should not be submitted. That route is **NOT_APPROVED**, and the
  policy records the route rather than the vendor, because the same vendor's paid
  route is a different assessment nobody has made.

**Postures are reviewed statements, not permanent facts.** A provider changing
its terms changes this file, not the code.

### No vendor is named in a source review

Stack Exchange's review v2 states the **property** a provider must have. It names
no company. A source review that named one would need re-versioning every time a
provider list changed, and would put provider governance inside the source
registry, where it does not belong. The two domains meet in exactly one place:
`authorize_external_inference`.

---

## 6. What is decided today

| Subject | State |
|---|---|
| `local-private-research-v1` | `PERMITTED_TO_APPROVED_PROVIDERS` |
| `commercial-multi-tenant-research-v1` | `NOT_ASSESSED`, stated explicitly |
| Stack Exchange, local review v2 | `PERMITTED_WITH_CONDITIONS` |
| Every other source | `NOT_ASSESSED` |
| Approved provider configured | **no** |

The commercial profile's `NOT_ASSESSED` is written out rather than inherited.
Whether a public multi-tenant service may send third-party licensed content to an
external processor is a materially harder question than the local one, and a
mission that answered it in passing would be answering it for a product nobody
has built. It refuses, and it refuses as an open question.

**The boundary is therefore closed.** Stack Exchange under the local profile
passes gates 1, 2 and 3 against the approved provider and fails gate 4:
`PROVIDER_NOT_CONFIGURED`. Nothing has been sent, and nothing can be until an
operator configures a credential.

---

## 7. Appending a review version invalidates its verifications

Recording the new assessment meant appending **review v2** to Stack Exchange, and
that alone broke deterministic acquisition for the source — not through the new
activity, but because `resolve_effective_verifications` refuses a compliance
configuration written for an older review version, on the stated ground that a
re-review can change what a condition means.

**That guard is right, and the repair was to perform the re-check rather than to
silence it.** v2's `required_conditions` array — the set the configuration
actually verifies, with its keys, descriptions, verification methods and
verification details — is byte-identical to v1's. What v2 adds is an assessment,
prose, evidence and open questions, none of which a capability verifies. The
equality is asserted in code before the version is bumped, and a test pins it, so
a future review that **does** alter a required condition cannot be waved through
by editing a number.

This is a cost of appending a review, and it is worth naming: a review version is
not free, and a mission that bumps one owes the re-check.

---

## 8. What an operator would do, and what they would not

Configuring a provider is an operator act, performed outside the repository. No
credential is committed, no key is fabricated, and no tracked file is a place to
paste one.

To check the boundary without sending anything:

```bash
uv run sros-source --use-profile local-private-research-v1 inference-authorization stack-exchange --provider anthropic --credential-env ANTHROPIC_API_KEY
```

The command reads the registry and the policy, reports every gate, and reaches no
network. It is a permission report, not an invocation.

**`--use-profile` is required and is a global option, before the subcommand.**
Reporting commands in this CLI do not read `SROS_USE_PROFILE`; they fall back to
the legacy commercial profile and say so in their banner. Omitting the flag here
reports the commercial profile's answer, which is a refusal on two gates -- a
correct answer to a different question.

---

## 9. What this document does not do

It does not authorise training on transmitted content — the source condition
excludes it by name, and a provider whose route trains is not eligible whatever
its other properties. It does not authorise embeddings, vector similarity or
fine-tuning; none is in scope for this repository. It does not authorise the
commercial profile. It builds no candidate generator, no rubric, no classifier,
no model-derived Signal, no INFERRED Claim and no Evidence. It configures
nothing and it sends nothing.

**What it establishes is narrower and is the point:** the question of where
inference may run now has a machine-verifiable answer, the answer is currently
*not yet*, and the reason is a named gate rather than a silence.
