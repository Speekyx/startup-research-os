# The redirect evidence, graded

Generated from `globalping-redirect-contract-review-v2.json`. Do not edit by hand.

**The question:**

> For a Globalping HTTP measurement using method HEAD against requested URL U, when the response to U is HTTP 3xx with a Location header naming V, does Globalping return the response to U without automatically issuing a subsequent HTTP request to V?

## Why it is load-bearing

if SROS reports the initial response and Globalping silently follows redirects and reports the final one, both return one status and one header set while observing different HTTP interactions -- and the difference is invisible in the resulting values.

## Surfaces reviewed

| surface | redirect mentions | relevant to HTTP measurement |
|---|---|---|
| OpenAPI specification | 0 | True |
| API repository (jsdelivr/globalping) | 2 | False |
| probe repository (jsdelivr/globalping-probe) | 1 | False |
| CLI repository (jsdelivr/globalping-cli) | 4 | False |
| website repository (jsdelivr/globalping.io) | 5 | False |

Notes:

- **OpenAPI specification** — verified on the retrieved bytes rather than on a summary: 124,793 bytes, zero case-insensitive matches for 'redirect' and zero for '3xx'. The 27 'Location' matches are the API's own asynchronous-measurement header and example keys such as pingLocations, not an HTTP redirect Location.
- **API repository (jsdelivr/globalping)** — a package.json dependency name and an ETag middleware test about the API's own responses
- **probe repository (jsdelivr/globalping-probe)** — one match, in the probe adoption-server test, unrelated to HTTP measurement
- **CLI repository (jsdelivr/globalping-cli)** — all in OAuth authentication paths (redirect URI), not measurement
- **website repository (jsdelivr/globalping.io)** — server routing, auth store and trailing-slash middleware; site infrastructure

**Documented in any reviewed surface: False.**
Zero matches mean `NOT_DOCUMENTED_IN_REVIEWED_SURFACE`, and that they prove no redirect is
**False**.

## What the provider did say

From jsdelivr/globalping issue #347, Improve HTTP response handling, by a provider maintainer:

> the body may be empty in some cases, most often redirects and error responses

*Establishes:* the statement PRESUPPOSES that a redirect response appears in a Globalping result, which is what a non-following apparatus produces. It is an incidental premise in an argument about rawOutput formatting.

*Does not establish:* a commitment about redirect behaviour. It defines nothing, promises nothing, and appears in a discussion about output formatting rather than about the measurement contract.

*Graded:* `PROVIDER_MAINTAINER_STATEMENT_INCIDENTAL`

## The answer that closed it

Asked through the provider's public technical channel and answered by `jimaek` (`MEMBER`) on 2026-09-06T13:32:15Z, at [5559554359](https://github.com/jsdelivr/globalping/issues/907#issuecomment-5559554359):

> It will return the response and not follow the redirect

Frozen verbatim in `globalping-r1-provider-reply-v1.json`, digest `a73b60fd64c1061e…`, retrieved by `RAW_GITHUB_REST_API_READ`. The issue it sits under is byte-identical to the frozen packet body, so it answers the question this project asked and not a paraphrase of it.

| half | state | from |
|---|---|---|
| the redirect response is returned | `ESTABLISHED` | It will return the response |
| the redirect is not followed | `ESTABLISHED` | and not follow the redirect |

clause 2 forecloses the only competing reading of clause 1. If the redirect is not followed there is no post-redirect response for 'the response' to denote, so the referent is forced rather than chosen. The reading does not depend on charity toward the answer.

*Does not establish:* documentation. The specification still contains zero occurrences of 'redirect', so the behaviour is declared and not specified: a future change would contradict no published document, and it says nothing about methods other than HEAD, about redirect chains beyond the first hop, or about whether following is configurable.

## Implementation, kept in its place

- follows redirects: **NO**
- contract status: **NON_NORMATIVE**
- run against a live target: **False**
- provider tests asserting redirect behaviour: **0**

## Verdict

**`R1_PASS_PROVIDER_DECLARED_NO_REDIRECT`**, at evidence level `R1_A2_SOLICITED_RESPONSIVE_PROVIDER_ANSWER`.

the provider was asked the exact frozen question through the channel this project established as first-party, and an organisation member answered it directly and on the record. Both required semantics are established, and the second clause forecloses the only competing reading of the first. Five surfaces of implementation evidence agree with the answer rather than contradicting it. The behaviour is DECLARED rather than DOCUMENTED, which is why the verdict says so.

*Why the maintainer statement did not upgrade it:* unchanged and still true of the INCIDENTAL statement: an incidental premise in an issue about output formatting is neither R1-A nor R1-B, however strongly it points the right way. The level moved on the SOLICITED answer, which is a different document.
