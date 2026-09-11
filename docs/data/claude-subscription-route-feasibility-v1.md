# Claude subscription route feasibility

Generated from `claude-subscription-route-feasibility-v1.json`. Do not edit by hand.

**CLAUDE_MAX_ROUTE_NOT_SUPPORTED_FOR_SROS_EXECUTION**

Mission 1.84.1. Whether the already-frozen second-Opportunity synthesis can execute through the operator's Claude subscription instead of the Anthropic API. Three independent answers of no, and only one of them is a governance question.

The subscription authenticates an AGENT HARNESS, not a bounded inference call. Both subscription-backed surfaces run an agent loop that decides its own number of model requests and composes its own system prompt, so neither can transmit the frozen prompt bytes nor honour MAX_MODEL_CALLS = 1. That is a property of the surface and no operator decision changes it. The provider-governance gap is real and is recorded separately, because it would still block even if the surface problem were solved, and because reporting it as the primary would send the operator to change an account setting that unblocks nothing.

Recorded beside it: **CLAUDE_MAX_ROUTE_REQUIRES_PROVIDER_GOVERNANCE_REVIEW**. The review was performed here rather than deferred, and it concluded NOT_APPROVED. Recording a posture that refuses is the opposite of manufacturing one.

## The premise, corrected

The mission is written about a **MAX** subscription. The subscription this machine holds reports `pro` at rate-limit tier `default_claude_ai`, so **MAX_TIER = NOT_MAX_ON_THIS_MACHINE**.

Plan identity is not a secret and was read; no token value was read, printed, persisted or committed. The operator may hold a Max subscription on another account, which is an operator-declared fact this mission cannot establish and does not assume. Nothing in the three blockers depends on which plan it is.

## Three blockers, and only one is a governance question

### 1. The frozen prompt bytes cannot be transmitted

`PROMPT_SHA256` af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080 covers the rendered system region, trusted context, the supplied statements, the task and the output schema, and nothing else.

An agent harness sends its own system prompt, its own tool definitions, its own context files and its own loop scaffolding, in addition to whatever the caller supplies.

`--system-prompt` replaces the harness prompt and does not remove tool definitions or the harness's own framing. A run whose transmitted bytes differ from the frozen ones is a different execution, and calling it the same one would make the digest a label rather than a check.

Cleared by an operator decision: **False**.

### 2. Exactly one model call cannot be enforced

The frozen packet binds MAX_MODEL_CALLS 1, max_retries 0, MAX_OUTPUT_TOKENS 3000 and a timeout of 60.0s. One invocation is one TASK, not one model request.

Flags checked and absent: `--max-turns`, `--timeout`, `--max-output-tokens`.

- Present but the wrong unit: --max-budget-usd, a dollar cap on API calls, which is not the billing unit on a subscription.
- Present but the wrong unit: --fallback-model, which is an automatic fallback and is forbidden by section 18.

Cleared by an operator decision: **False**.

### 3. The provider posture does not satisfy TED's own condition

the register's `anthropic` entry already says so in its own words, written in Mission 1.23 and not for this question: 'Consumer products (Claude Free, Pro, Max) are a DIFFERENT route with different terms and are not assessed here.' The scope of an assessment is a recorded fact, not an inference this mission had to make.

The condition, quoted: the TED egress decision's condition 3, frozen and adopted: 'Transmission only to a provider whose reviewed posture is APPROVED in the provider policy register: its own terms commit, for the API route this deployment would use, that submitted content is not used to train its models, and its retention posture is documented and bounded.'

What the subscription route offers instead: a setting the account holder turns on or off, which decides both whether submitted content trains models and whether retention is five years or thirty days.

**PROVIDER_GOVERNANCE_STATE = NOT_APPROVED**, registered as `anthropic-claude-subscription`. so a future adapter is refused BY NAME rather than by absence, and so nothing can reach the API route's APPROVED posture by calling itself anthropic.

Cleared by an operator decision: partly, and only by the operator deciding that an account setting satisfies a condition written as 'its own terms commit'. That is a reading of their own adopted condition and is theirs to make. It is not made here, and it would not clear blockers 1 or 2.

## The switch

`--bare` is documented as: 'Minimal mode: skip hooks, LSP, plugin sync, attribution, auto-memory, background prefetches, keychain reads, and CLAUDE.md auto-discovery. ... Anthropic auth is strictly ANTHROPIC_API_KEY or apiKeyHelper via --settings (OAuth and keychain are never read).'

'--bare is the recommended mode for scripted and SDK calls, and will become the default for -p in a future release.'

the one configuration that gives a scripted call a clean, reproducible, context-free surface is exactly the configuration that cannot use the subscription. The two properties SROS needs sit on opposite sides of one switch, and choosing either one gives up the other.

## Routes

| route | auth | usage model | governed by | posture | shape |
|---|---|---|---|---|---|
| `anthropic-platform-api` | API key | pay-as-you-go, metered per token | Anthropic Commercial Terms of Service | **APPROVED** | one bounded request, parameters supplied by the caller |
| `claude-cli-print-subscription-oauth` | claude.ai OAuth, established by `claude setup-token` | subscription usage limits, rolling session and weekly windows | Anthropic Consumer Terms of Service | **NOT_APPROVED** | an agent loop that decides its own number of model requests |
| `claude-agent-sdk-subscription` | documented authentication is API key or a cloud provider's credentials; the SDK overview directs third-party developers away from claude.ai login | whatever the authentication resolves to | Commercial Terms for the SDK itself; the account's terms for the call | **NOT_APPROVED** | an agent loop, in the caller's own process |

**SELECTED_SUBSCRIPTION_ROUTE = None**

## Local tooling

- Claude CLI present: True, version `2.1.116`
- Agent SDK present: False
- Subscription auth supported: True (`claude setup-token`, documented by the installed CLI as 'Set up a long-lived authentication token (requires Claude subscription)')
- Non-interactive supported: True (`claude -p`, with --output-format json and --json-schema)
- Credential values read / printed / persisted: 0 / 0 / 0

neither `claude_agent_sdk` for Python nor `@anthropic-ai/claude-agent-sdk` for Node is installed in this repository's environment, and neither is the `anthropic` client SDK. The Gateway speaks raw HTTP on purpose (Mission 0.4 section 20), so adding one would be a dependency decision rather than a wiring detail.

## The environment collision

- `ANTHROPIC_API_KEY` in this agent's process: False
- `ANTHROPIC_API_KEY` in the deployment environment: **True** (`infrastructure/compose/.env`, declared, non-empty, long, value read: False)

the environment this mission can inspect is the one Claude Code gave it, and the environment an SROS job inherits is the compose one. Reporting the first as though it were the second would have recorded 'no key present' about a deployment that has one.

**SUBSCRIPTION_ROUTE_FAILS_CLOSED_TODAY = False.** the Gateway has no route concept at all. `AnthropicProvider` is one dataclass bound to one endpoint, and it reads ANTHROPIC_API_KEY from the environment at construction. There is no field a caller could set to request a subscription route, so there is nothing to fail closed -- a subscription request would not be refused, it would be unexpressible, and the nearest thing to it would silently be a pay-as-you-go call.

Required future invariant: REQUESTED_ROUTE = CLAUDE_SUBSCRIPTION must never execute through ANTHROPIC_PLATFORM_API. Billing-route ambiguity is a hard failure, and a fallback between billing routes is forbidden.

## Billing

- V1: `API_PAYG`, API_PAYG True
- Subscription: `SUBSCRIPTION_USAGE`, usage limited True, free False, unlimited False

the costs documentation states that 'Claude Max and Pro subscribers have usage included in their subscription', and separately describes hitting a session limit and a weekly limit, with usage credits as the way to continue past them. Included in a subscription is not free and not unlimited.

## Models

**AVAILABLE_SUBSCRIPTION_MODELS = NOT_ESTABLISHED.** no local configuration enumerates what this account is entitled to, and the only ways to find out are a model call or an account page. Section 25 prefers zero remote calls and the answer would change nothing, because the route is blocked upstream of model choice.

Not assumed: that the API model names are the subscription model names, and that every Anthropic model is available on every plan. The CLI's `--model` flag documents aliases it accepts, which is a fact about the flag rather than about the account.

## No V2

**EXECUTION_PACKET_V2_CREATED = False**, 6 of 9 conditions met.

- Failed: 3. route can execute non-interactively AS A SINGLE BOUNDED CALL
- Failed: 4. provider posture satisfies TED's conditions
- Failed: 8. exactly-one-call semantics can be enforced

section 20 requires nine established properties and three fail: the route cannot transmit the approved prompt bytes, exactly-one-call cannot be enforced, and the provider posture does not satisfy the TED condition. A V2 produced anyway would be an executable record of a call that may not be made.

**RECOMMENDED_EXECUTION_PACKET = V1.** V1 is unchanged, still frozen, still unapproved, and still the only route whose provider posture is APPROVED and whose shape is a single bounded call. Section 23 says to recommend V1 where the subscription route has unresolved governance or route ambiguity, and here it has both plus a surface mismatch.

## What this mission spent

| counter | value |
|---|---|
| REMOTE_TEST_CALLS | 0 |
| TED_BYTES_SENT | 0 |
| OPPORTUNITY_MODEL_CALLS | 0 |
| ALL_REMOTE_MODEL_CALLS | 0 |
| documentation_requests | 10 |
| canonical_research_mutation | 0 |
| opportunities_created | 0 |
| credential_values_exposed | 0 |

6 returned content, 4 were redirect responses, all counted.

**Next: Approve or refuse SECOND-OPPORTUNITY-SYNTH-EXEC-V1 by its digest. The subscription route does not change what that packet says and does not remove the need to decide it.**
