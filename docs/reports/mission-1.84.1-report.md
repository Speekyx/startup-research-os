# Mission 1.84.1 — A subscription authenticates a harness, not a call

**Outcome: `CLAUDE_MAX_ROUTE_NOT_SUPPORTED_FOR_SROS_EXECUTION`.**

**Recorded beside it: `CLAUDE_MAX_ROUTE_REQUIRES_PROVIDER_GOVERNANCE_REVIEW`**, and the review was
performed here rather than deferred. It concluded **NOT_APPROVED**.

Three independent answers of no, and only one of them is a governance question. The frozen API
packet is untouched, unapproved and still the recommendation.

---

## Report

```
START_COMMIT                  = 1512f68      BRANCH = sprint-1/mission-1.84.1

API_EXECUTION_PACKET_V1_SHA256 = 570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92
V1_UNCHANGED                  = true         file sha256 7132fc35… before and after

CLAUDE_CLI_PRESENT            = true         CLAUDE_CLI_VERSION = 2.1.116
AGENT_SDK_PRESENT             = false        AGENT_SDK_VERSION  = none

SUBSCRIPTION_AUTH_SUPPORTED   = true   (`claude setup-token`, "requires Claude subscription")
NON_INTERACTIVE_SUPPORTED     = true   (`claude -p`, --output-format json, --json-schema)

ANTHROPIC_API_KEY_PRESENT     = false in this agent's process
                                TRUE in infrastructure/compose/.env, value not read
SUBSCRIPTION_ROUTE_FAILS_CLOSED = false, because there is no route concept to fail closed

CANDIDATE_SUBSCRIPTION_ROUTES = claude-cli-print-subscription-oauth,
                                claude-agent-sdk-subscription
SELECTED_SUBSCRIPTION_ROUTE   = NONE

PROVIDER_GOVERNANCE_STATE     = NOT_APPROVED, registered as anthropic-claude-subscription
APPROVED_PROVIDERS            = ["anthropic"], before and after

AVAILABLE_SUBSCRIPTION_MODELS = NOT_ESTABLISHED
SELECTED_SUBSCRIPTION_MODEL   = NONE

BILLING_CLASS                 = SUBSCRIPTION_USAGE for the candidate route, API_PAYG for V1
API_PAYG                      = true for V1
SUBSCRIPTION_USAGE_LIMITED    = true    free = false    unlimited = false

REPRESENTATION_SHA256         = 2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72
PROMPT_SHA256                 = af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080
REPRESENTATION_UNCHANGED      = true    PROMPT_UNCHANGED = true

REMOTE_TEST_CALLS             = 0
TED_BYTES_SENT                = 0
OPPORTUNITY_MODEL_CALLS       = 0
ALL_REMOTE_MODEL_CALLS        = 0
documentation requests        = 10 (6 returned content, 4 were redirects, all counted)

EXECUTION_PACKET_V2_CREATED   = false        EXECUTION_PACKET_V2_SHA256 = none
                                6 of 9 section-20 conditions met

RECOMMENDED_EXECUTION_PACKET  = V1
PRIMARY_OUTCOME               = CLAUDE_MAX_ROUTE_NOT_SUPPORTED_FOR_SROS_EXECUTION
NEXT_ACTION                   = approve or refuse SECOND-OPPORTUNITY-SYNTH-EXEC-V1 by its digest

raw_records 325  signals 60  claims 91  revisions 92  evidence 112  assessments 4
independence groups 0  opportunities 1  opportunity revisions 2  evidence links 14
source reviews 71  — every counter identical, measured against the live database

VIOLATIONS_CAUGHT / ESCAPED   = 66 / 0       positive controls 8 of 8
TESTS                         = 3831 bare-python across 9 packages; 3431 pytest
CI_GATES                      = 64 -> 65
```

---

## The premise was wrong, and correcting it costs nothing

The mission is written about a Claude **Max** subscription. The subscription this machine holds
reports `subscriptionType = pro` at `rateLimitTier = default_claude_ai`. So **MAX_TIER =
NOT_MAX_ON_THIS_MACHINE**, and no field in any record says MAX.

Plan identity is not a credential and was read; no token value was read, printed, persisted or
committed. The operator may hold a Max subscription on another account, which is an
operator-declared fact this mission cannot establish and does not assume. **Nothing in the three
blockers depends on which plan it is**, which is why correcting the premise changes the record and
not the answer.

---

## Blocker 1: the frozen prompt bytes cannot be transmitted

`PROMPT_SHA256` covers the rendered system region, the trusted context, the six supplied
statements, the task and the output schema — and nothing else. That is what Mission 1.84 froze and
what a future approval would name.

An agent harness sends its own system prompt, its own tool definitions, its own context files and
its own loop scaffolding, in addition to whatever the caller supplies. `--system-prompt` replaces
the harness prompt and does not remove the rest.

Section 16 is explicit: if adapting transport changes transmitted prompt bytes, **STOP**, and do
not call it the same execution. **Calling it the same one would make the digest a label rather
than a check.**

**No operator decision clears this.**

---

## Blocker 2: exactly one model call cannot be enforced

The frozen packet binds `MAX_MODEL_CALLS = 1`, `max_retries = 0`, `MAX_OUTPUT_TOKENS = 3000` and a
60-second timeout. **One `claude -p` invocation is one TASK, not one model request**: an agent loop
decides for itself how many requests a task needs.

Flags checked in the installed CLI and **absent**: `--max-turns`, `--timeout`,
`--max-output-tokens`. Flags present but in the wrong unit: `--max-budget-usd`, a dollar cap on API
calls, which is not the billing unit on a subscription; and `--fallback-model`, which is an
automatic fallback and is forbidden outright by section 18.

**No operator decision clears this either.** It is what the surface is.

---

## Blocker 3: the provider posture, and the register had already said so

Section 10 asks whether the existing `anthropic` posture can cover the subscription route. **The
register answers in its own words, written in Mission 1.23 and not for this question**:

> Consumer products (Claude Free, Pro, Max) are a DIFFERENT route with different terms and are not
> assessed here.

So the scope of that assessment is a recorded fact rather than an inference this mission had to
make. What decides the new route is the property the operator's own adopted condition names:

> PROVIDER-BOUND, BY PROPERTY AND NOT BY NAME. Transmission only to a provider whose reviewed
> posture is APPROVED in the provider policy register: **its own terms commit**, for the API route
> this deployment would use, that submitted content is not used to train its models, and its
> retention posture is documented and bounded.

The API route has a sentence that commits: *"Anthropic may not train models on Customer Content
from Services."* The subscription route has a setting instead. Anthropic's own Claude Code data
policy states it and names Claude Code inside it:

> **Consumer users (Free, Pro, and Max plans)**: We give you the choice to allow your data to be
> used to improve future Claude models. We will train new models using data from Free, Pro, and Max
> accounts when this setting is on (including when you use Claude Code from these accounts).

Retention moves with the same setting: five years where data use is allowed, thirty days where it
is not, against a documented thirty days on the API route. And the Consumer Terms put the two
routes under different instruments outright: *"Our Commercial Terms of Service govern your use of
any Anthropic API key, the Anthropic Console, or any other Anthropic offerings that reference the
Commercial Terms of Service."*

**A setting the account holder can turn on is not a term that commits**, and reading it as one
would let a provider approval rest on a checkbox nobody re-checks. That is the register's own
definition of `NOT_APPROVED`: *the terms do not establish that it does not.*

**The review was performed rather than deferred**, and the route is registered as its own provider
id `anthropic-claude-subscription` with two retrieved first-party evidence rows. Recording a
posture that refuses is the opposite of manufacturing one — and a separate id means a future
adapter is refused **by name** rather than by absence, so nothing reaches the API route's approval
by calling itself Anthropic.

**The set of APPROVED providers is `["anthropic"]` before and after.**

This one is *partly* clearable, and only by the operator deciding that an account setting satisfies
a condition they wrote as *its own terms commit*. That is a reading of their own condition and is
theirs to make. **It would not clear blockers 1 or 2.**

---

## The switch, in the tooling's own words

The sharpest fact this mission found is not in anybody's reasoning. It is in a flag description:

> `--bare` — Minimal mode: skip hooks, LSP, plugin sync, attribution, auto-memory, background
> prefetches, keychain reads, and CLAUDE.md auto-discovery. … **Anthropic auth is strictly
> ANTHROPIC_API_KEY or apiKeyHelper via `--settings` (OAuth and keychain are never read).**

And, from the documentation: *"`--bare` is the recommended mode for scripted and SDK calls, and
will become the default for `-p` in a future release."*

**The one configuration that gives a scripted call a clean, reproducible, context-free surface is
exactly the configuration that cannot use the subscription.** The two properties SROS needs sit on
opposite sides of one switch, and choosing either gives up the other.

---

## Why the governance gap is the secondary and not the primary

All three blockers are real. Reporting the governance one as primary would send the operator to
change an account setting, come back, and still be blocked by a surface that cannot transmit the
frozen bytes or bound the call count. **That is Mission 1.77's lesson: do not misattribute the
blocker to a layer that is not the binding one.** So the primary names what no decision fixes, and
the governance gap is recorded in full beside it, because it would still block even if the surface
problem were solved.

---

## The environment collision, and why two answers were recorded

`ANTHROPIC_API_KEY` is **absent** from this agent's own process and **present** in
`infrastructure/compose/.env`, declared and non-empty. Its value was not read; only its presence
and length class.

**The environment this mission can inspect is the one Claude Code gave it; the environment an SROS
job inherits is the compose one.** Reporting the first as though it were the second would have
recorded *no key present* about a deployment that has one — and the whole point of section 6 is
that a key being present is what makes a silent fallback possible.

`SUBSCRIPTION_ROUTE_FAILS_CLOSED = false` today, and the reason is worth stating precisely: the
Gateway has **no route concept at all**. `AnthropicProvider` is one dataclass bound to one endpoint
that reads `ANTHROPIC_API_KEY` at construction. There is no field a caller could set to request a
subscription route, so **there is nothing to fail closed** — a subscription request would not be
refused, it would be unexpressible, and the nearest thing to it would silently be a pay-as-you-go
call.

The required invariant is recorded: `REQUESTED_ROUTE = CLAUDE_SUBSCRIPTION` must never execute
through `ANTHROPIC_PLATFORM_API`, and "try subscription, then API" is named as the forbidden shape.

---

## What was determined and deliberately not built

The smallest architecture is that **a route is part of provider identity rather than a parameter
beside it**. The register already keys postures by provider id, so registering the subscription
route as its own id is the whole of the governance half, and it is done. The execution half would
be a second adapter naming that id, and **it was not written**: an adapter for a route whose
posture is NOT_APPROVED is code that cannot be authorised to run. The refusal it would need already
exists — a provider whose posture is not APPROVED is refused at authorization, and one absent from
the register resolves `NOT_ASSESSED` and is refused too.

---

## What was not assumed

**No model was assumed available.** `AVAILABLE_SUBSCRIPTION_MODELS = NOT_ESTABLISHED`: no local
configuration enumerates what this account is entitled to, and the only ways to find out are a
model call or an account page. The CLI's `--model` flag documents the aliases it accepts, which is
a fact about the flag and not about the account. API model names were not copied across as
subscription model names.

**Neither route was called free.** The costs documentation says subscribers have usage *included in
their subscription*, and separately describes hitting a session limit and a weekly limit. Included
is not free and not unlimited. **No dollar saving is claimed and no quota percentage was
invented**, because Anthropic exposes none programmatically.

**No remote call of any kind was made to any model.** Section 9's default held: `REMOTE_TEST_CALLS
= 0`, and no live call was needed, because nothing a test call could return would clear blockers 1,
2 or 3.

---

## Adversarial probe

**66 deliberate violations, 66 caught, 0 escaped. 8 positive controls, 8 accepted.**

**Two escaped on the first run, and both were this gate's own rule.** Swapping V1's provider to the
subscription route, and swapping its model, both slipped through — because those edits move V1's
digest, so *Mission 1.84's* gate would have caught them. **A gate that relies on a sibling to
enforce its own rule stops working the moment the sibling is skipped.** Section 2 is this mission's
prohibition, so this gate now pins V1's provider, posture, model and tier directly.

The cases attack the register (an approved subscription route, a reused provider id, a grown
approved set, evidence with no date or no retrievable address, the API route's exclusion of
consumer products edited away), the record's claims (the existing posture covering the new route,
the TED condition paraphrased into something a setting satisfies, an agent harness claimed to
transmit the frozen bytes, one-call claimed enforceable, an invented `--max-turns`), the billing
(free, unlimited, unmetered, a dollar saving, an invented quota percentage, PAYG marked false), the
frozen payload (a moved representation or prompt digest, V1 edited, repointed, marked approved, or
its approval invented), V2 (claimed with conditions unmet, every condition marked met with no
packet, recommended while absent), the fail-closed position, and secrets — an `sk-ant-` key and a
JWT-shaped token dropped into the record are both refused.

The controls prove the gate is not simply refusing everything: the governance and billing-ambiguous
outcomes stay representable, `NOT_ASSESSED` is accepted as a refusing state, a third refusing
provider may be registered, more retrieved evidence strengthens rather than breaks the refusal, a
fourth candidate route may be described and left unselected, more documentation requests are still
zero model calls, and **an established Max tier would be recordable** — which matters, because a
gate that could not express the premise the brief assumed would be a gate that forced this
mission's particular answer.

---

## Verification

`ruff format --check` and `ruff check` clean over 979 files, with three SIM102 nested-ifs
**collapsed by hand** and the probe re-run afterwards — Mission 1.83 found that a mechanical
collapse once folded a sibling check inside a `raise`. `mypy` clean over 199 files across the 14 CI
package paths. Contracts, catalog and review results in sync. Source registry: 29 sources, 45
evidence records, 0 warnings. **All 65 CI gates green locally**, the new one included. 3831
bare-python tests across 9 packages; 3431 pytest, database reported unchanged across 29 tenant
tables.

**Zero canonical research mutation.** Every counter measured against the live database and
identical: 325 / 60 / 91 / 92 / 112 / 4 / 0 / 1 / 2 / 14, source reviews 71.

---

## Next

**The decision that was waiting is still the decision that is waiting.**
`SECOND-OPPORTUNITY-SYNTH-EXEC-V1` version 1, digest
`570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92`, is byte-identical, still
frozen and still unapproved. The subscription route does not change what that packet says and does
not remove the need to decide it.

If it is approved, **Mission 1.84.2 — Second Opportunity Synthesis Execution V1** performs exactly
one inference on the API route and persists an Opportunity hypothesis only if every gate accepts it
*and* a named human has reviewed the output.

**Do not execute either packet. Do not send TED data. Do not build a subscription adapter** — the
route is registered NOT_APPROVED, and building an execution path for a refused route is building
for a permission nobody has.

