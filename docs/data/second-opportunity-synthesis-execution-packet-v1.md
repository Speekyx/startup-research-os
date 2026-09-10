# SECOND-OPPORTUNITY-SYNTH-EXEC-V1 v1

Generated from `second-opportunity-synthesis-execution-packet-v1.json`. Do not edit by hand.

Mission 1.84 section 33. The exact call, frozen. An operator approval must cite this packet's id, version and digest, and no approval survives a change to the prompt, the model, the representation, the parameters or the ceilings.

**EXECUTION_PACKET_SHA256** `570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92`

**OPERATOR_EXECUTION_APPROVAL_RECORDED = False**

THIS DOCUMENT RECORDS NO APPROVAL. A future approval lives beside it, never inside it, because marking a frozen document approved changes the bytes that were approved. AND NO OLD APPROVAL AUTHORISES THIS CALL: the TED egress decision permitted the material to leave, which is a different act from executing this model with this prompt at this cost.

## The egress decision this rests on

- `TED-EGRESS-OPPSYNTH-V1` v1
- `f27c34460f413def15c260e72fd2261a1fba666b574e9e2ee60bf7ef38a39577`

## The payload

- subject `ted-eu:CPV-class:9261` (Sports facilities operation services)
- selected packet `e218b56a8f938f4d5f7fc961e7f0c2cfe184c4396395334140c6199b48316592`
- preparation `opportunity-preparation@5.0.0`
- purpose bounded external inference for Opportunity hypothesis synthesis
- representation `opportunity-transmission-representation@1.0.0`
- **REPRESENTATION_SHA256** `2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72`
- 5 claims, 3604 characters

## The route

- provider `anthropic`, posture **APPROVED**
- route The Anthropic API accessed with an API key under the Commercial Terms of Service. Consumer products are a DIFFERENT route and are not assessed.
- model `claude-sonnet-5` on tier `STRONG_MODEL`

deterministic: exactly one provider route in the register currently satisfies every required property. gemini is NOT_APPROVED on its assessed unpaid route, which trains on submitted content; fake is NEVER_PRODUCTION by name. No preference, brand or capability judgement entered the choice.

deterministic: exactly one text tier is configured in this deployment. LLM_TIER_FAST and LLM_TIER_BALANCED both bind provider 'null', which `TierBinding.configured` reads as unconfigured, and the embedding tier is local and forbidden here. There is no smaller approved model to prefer, and nothing was chosen for being strongest.

## The prompt

- `second-opportunity-synthesis-prompt` v1.0.0
- **PROMPT_SHA256** `af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080`

## Generation parameters

| parameter | value |
|---|---|
| `tier` | `STRONG_MODEL` |
| `requires_structured_output` | `True` |
| `response_schema` | `second-opportunity-synthesis-output@1.0.0` |
| `timeout_seconds` | `60.0` |
| `max_retries` | `0` |
| `temperature` | `None` |
| `top_p` | `None` |
| `seed` | `None` |
| `reasoning_effort` | `None` |

null means the Gateway does not expose it, not that a default is accepted silently. Whatever the provider's own default is, it is not a parameter this repository froze.

0, overriding the Gateway default of 2 and the deployment's LLM_MAX_RETRIES=2. A retry is a second call, and this packet authorises one.

## Budget

- input estimate 9125 tokens, max output 3000, ceiling 12125
- pricing version `anthropic-published-2026-09-02`
- 0.002 cost units per 1000 input tokens, from the deployment's configured pricing table
- 0.01 cost units per 1000 output tokens, from the same table
- **WORST_CASE_CALL_COST 0.04825** cost units
- **EXECUTION_COST_CEILING 0.1** cost units
- MAX_MODEL_CALLS 1, timeout 60.0s

roughly twice the worst case, so a single oversized call is covered and a second call or a much larger one is not. The deployment's session budget is 5 cost units over 120 calls, which this packet does not rely on: a per-execution ceiling is what stops one authorised call from becoming several.

cost units are provider-agnostic by ADR-006: a unit is whatever the configured table's author intended. The ceiling is expressed in the same units the budget ledger compares and subtracts, so it is enforceable without this record asserting a currency.

Exact tokenizer available: False. no tokenizer package is installed in this environment and none was fetched. Mission 1.31.1's provider response reported 5967 input tokens for the docker prompt. That prompt was re-rendered here at 12868 wire characters, giving 2.1565 characters per token, giving a raw estimate of 7299.7 tokens over 15742 wire characters, multiplied by 1.25.

the docker prompt re-renders one sentence differently from what was sent in 1.31.1, because the reliability sentence is now derived from the packet. A ratio is robust to a one-sentence difference and the multiplier covers more than that, but the pair is a measurement of a slightly different string and is recorded as such.

No test request was sent: True.

## What the call cannot reach

| capability | state |
|---|---|
| TRAINING | False |
| FINE_TUNING | False |
| EMBEDDINGS | False |
| WEB | False |
| TOOLS | False |
| EXTERNAL_RETRIEVAL | False |

the model reasons over the approved subject, the approved canonical Claims, the deterministic metadata the representation contract permits, and the synthesis instructions. Nothing else is reachable, and no tool exists for an instruction inside a supplied statement to reach.

## Retention, if it runs

| what | kept |
|---|---|
| raw_provider_response | RETAINED, as the bytes the gate judged; a gate verdict over a response nobody kept is unverifiable |
| parsed_structured_output | RETAINED |
| provider_request_id | RETAINED |
| usage_metadata | RETAINED (tokens, provider, model, routing version) |
| cost_metadata | RETAINED |
| timestamps | RETAINED |
| error_metadata | RETAINED on failure |
| hidden_reasoning | NOT RETAINED, and not requested. No chain-of-thought is stored even if the provider exposes it |

only what the application contract requires, and the contract requires the response because the gate's verdict is about it.

## Persistence

- persist on a gate verdict alone: False
- human review before persistence: True
- Opportunities created by this packet: 0
- score persisted: False, independence group: False

The first revision must carry: the selected candidate artifact, preparation v5, the input representation digest, the prompt digest, this execution packet digest, the provider and model, the response digest, the exact Evidence ids.

the mutation shape is not hard-coded here. A future execution reads the schema, and counting rows before inspecting it is how a migration surprises a mission.

## Failure

**EXECUTION_FAILED_NO_RETRY**. a transport or provider failure ends the execution. No automatic retry, no fallback model, no second provider. A retry needs a later operator decision.

a timeout is not permission to retry.

## What preparing this cost

| counter | value |
|---|---|
| MODEL_CALLS | 0 |
| BYTES_SENT_TO_ANY_EXTERNAL_MODEL | 0 |
| TOKENS_SENT | 0 |
| PROVIDER_REQUESTS | 0 |
| TEST_REQUESTS | 0 |
| research_data_fetches | 0 |
| network_discovery_calls | 0 |
| canonical_research_mutation | 0 |
| opportunities_created | 0 |
| opportunity_revisions_created | 0 |
| claims_created | 0 |
| evidence_created | 0 |
| signals_created | 0 |
| embeddings_created | 0 |
| scores_persisted | 0 |
| independence_groups_created | 0 |
| credential_values_read_or_logged | 0 |

the model universe and the prices come from configuration this deployment already holds. Nothing was discovered over the network and no price was invented.

## What the digest binds

the packet id and version, the egress decision it rests on, the subject and selected packet, the preparation version, the purpose, the representation schema and digest, the provider and its posture, the model and tier, the prompt id, version and digest, every generation parameter, the token and cost ceilings, the call limit, the timeout, the output schema and gate versions, the persistence policy, the six capability negatives and the failure outcome. It excludes itself, the preparation date and the explanatory notes, so an approval recorded beside this packet does not move it and a changed prompt, model, parameter or ceiling does.
