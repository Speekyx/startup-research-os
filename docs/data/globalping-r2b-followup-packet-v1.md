# GP-R2-B-Q1 — one question, and it is the one that was not answered

Generated from `globalping-r2b-enquiry-packet-v1.json`. Do not edit by hand.

**`send_status: NOT_AUTHORIZED`.** THIS DOCUMENT RECORDS NO AUTHORIZATION, and never that none exists. An approval lives beside a packet, not inside it.

## The packet

| | |
|---|---|
| question | `GP-R2-B-Q1` v1 |
| residual | `R2-B` |
| subject | Terms scope: HEAD measurements of publicly reachable third-party websites |
| channel | `PROVIDER_REPLY_THREAD_ESTABLISHED_BY_THE_PRIOR_EXCHANGE` |
| recipient | `DETERMINED_BY_THE_THREAD_NOT_SUPPLIED` |
| maximum outward replies | **1** |
| content hash | `fe312c37b8622e5a…` |

### The frozen body

> Thanks for confirming the commercial-use point.
> 
> Just to clarify the remaining part of my question: does Globalping permit bounded HTTP HEAD measurements of publicly reachable third-party websites that I do not own or operate, provided the measurements comply with Globalping's limits and are not abusive, exploitative, or used as a proxy?

## It asks one thing

GP-R2-Q1 asked four things and was answered. This asks one of them again, alone, which is a different question rather than a further version of that one -- and a new question must not be reachable by an approval written for the old one.

Asks about commercial use: **False**. R2-A closed in Mission 1.74 on the provider's own FAQ, and the last reply confirmed it again. Asking a settled question is how a compound enquiry gets the easy clause answered twice.

Deliberately not broadened to: `arbitrary HTTP methods`, `GET body retrieval`, `scanning`, `proxying`, `infrastructure exploitation`, `unlimited or unbounded traffic`, `any target the user does own or operate`.

## The thread is what is bound

the sender of the reply being answered is NOT_ESTABLISHED -- Mission 1.76.1 attempted the mailbox read and the connector refused it -- so no address is known and inventing one would fabricate the field the whole exchange hangs on. The mechanism does not need one: a reply inside a thread inherits its recipient from the thread rather than having it typed. What binds the act is therefore the THREAD, and a thread is tighter than a mailbox: it pins the conversation, the question that opened it and the reply being answered.

| bound | value |
|---|---|
| thread subject | Terms scope: HEAD measurements of publicly reachable third-party websites |
| prior enquiry digest | `987f3ff57ce661c6…` |
| prior reply digest | `be3845f89b636b96…` |

## The discriminator, frozen before dispatch

R2-B closes only on a reply that explicitly establishes one of:

- **`PERMITTED`** — the described bounded HEAD measurements may target publicly reachable third-party websites the user does not own or operate, subject to stated limits
- **`NOT_PERMITTED`** — the described third-party target use is outside permitted scope
- **`CONDITIONALLY_PERMITTED`** — the described third-party target use is permitted only under explicitly stated additional conditions

It does **not** close on:

- silence
- a generic commercial-use permission
- 'publicly reachable target' appearing only in technical API documentation
- product behaviour
- the proxy limitation alone
- absence from the prohibited-use list
- implication or presupposition

**Mission 1.76.1 found the strongest available argument that the last reply answered R2-B -- a no-proxy carve-out presupposes third-party targets -- and refused it, because a presupposition is not a statement. Writing that into the discriminator stops the same argument being rediscovered as a novelty.**

## No approval, and no spent one reaches it

- `docs/data/globalping-r2-dispatch-approval-v1.json` — spent by an attempt that bounced, and it names a different content digest
- `docs/data/globalping-r2-v2-dispatch-approval-v1.json` — spent by the one send it authorised, and it names GP-R2-Q1 v2's digest. A new question is a different action however similar the thread

## Authority stays a separate question

Sender of the earlier reply: **`NOT_ESTABLISHED`**. the evidentiary strength of whatever comes back. A reply in this thread inherits the same attribution problem, so establishing the sender remains a separate and still-open action.

## Nothing was performed

| | |
|---|---|
| emails_sent | 0 |
| gmail_reads | 0 |
| gmail_writes | 0 |
| mail_connector_calls | 0 |
| github_writes | 0 |
| globalping_api_executions | 0 |
| globalping_measurements_created | 0 |
| target_http_requests | 0 |
| research_api_calls | 0 |
| model_calls | 0 |
| embeddings | 0 |
| canonical_research_mutations | 0 |
