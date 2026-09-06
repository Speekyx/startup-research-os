# Mission 1.74 — The redirect evidence, graded

Generated from `globalping-redirect-contract-review-v1.json`. Do not edit by hand.

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

## Implementation, kept in its place

- follows redirects: **NO**
- contract status: **NON_NORMATIVE**
- run against a live target: **False**
- provider tests asserting redirect behaviour: **0**

## Verdict

**`R1_PARTIAL_IMPLEMENTATION_ONLY`**, at evidence level `R1_C_IMPLEMENTATION_OBSERVED`.

five first-party surfaces reviewed, zero documenting the behaviour, no provider test asserting it, one incidental maintainer statement consistent with not following, and an implementation that does not follow. Everything points the same way and nothing commits the provider to it.

*Why the maintainer statement did not upgrade it:* §3's R1-A needs a normative provider contract and R1-B needs the provider to declare a published implementation normative. An incidental premise in an issue about output formatting is neither, however strongly it points the right way.
