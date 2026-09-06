# Mission 1.72 — The bounded HTTP load profile

Generated from `bounded-http-load-profile-v1.json`. Do not edit by hand.

**`BOUNDED_HTTP_LOAD_PROFILE_V1`.** the smallest operationally useful initial profile, optimised for
a bounded pilot rather than throughput.

**Every value below is a project policy default.** None of them is a discovered safety
fact, an industry standard, a legal requirement or a provider recommendation.

| bound | value | unit | source |
|---|---|---|---|
| `MAX_CORPUS_TARGETS` | 500 | targets | `PROJECT_POLICY_DEFAULT` |
| `GLOBAL_CONCURRENCY` | 4 | in-flight requests | `PROJECT_POLICY_DEFAULT` |
| `PER_ORIGIN_CONCURRENCY` | 1 | in-flight requests per origin | `PROJECT_POLICY_DEFAULT` |
| `PER_ORIGIN_REQUEST_RATE` | 0.2 | requests per second per origin | `PROJECT_POLICY_DEFAULT` |
| `CONNECT_TIMEOUT` | 10 | seconds | `PROJECT_POLICY_DEFAULT` |
| `READ_TIMEOUT` | 20 | seconds | `PROJECT_POLICY_DEFAULT` |
| `MAX_REDIRECTS` | 5 | hops | `PROJECT_POLICY_DEFAULT` |
| `MAX_RETRIES` | 0 | retries | `PROJECT_POLICY_DEFAULT` |
| `MAX_HEADER_BYTES` | 65536 | bytes | `PROJECT_POLICY_DEFAULT` |
| `MAX_RESPONSE_READ_BYTES` | 1048576 | bytes | `PROJECT_POLICY_DEFAULT` |
| `MAX_TOTAL_BYTES_PER_TARGET` | 2097152 | bytes | `PROJECT_POLICY_DEFAULT` |
| `MAX_RUN_DURATION` | 21600 | seconds | `PROJECT_POLICY_DEFAULT` |
| `ROBOTS_REQUEST_BUDGET` | 1 | requests per origin per run | `PROJECT_POLICY_DEFAULT` |
| `MAX_REQUESTS_PER_TARGET` | 6 | requests | `PROJECT_POLICY_DEFAULT` |
| `BACKOFF_POLICY` | DISABLED | policy | `PROJECT_POLICY_DEFAULT` |

Why, for each:

- **MAX_CORPUS_TARGETS** — small enough that one run is reviewable by a person reading its accounting, and large enough that a population is not trivially one site
- **GLOBAL_CONCURRENCY** — a bounded pilot on one operator machine; throughput is explicitly not the objective
- **PER_ORIGIN_CONCURRENCY** — one request at a time to any one host is the lowest burden a measurement can impose while still finishing
- **PER_ORIGIN_REQUEST_RATE** — one request every five seconds; deliberately slower than a browsing human
- **CONNECT_TIMEOUT** — long enough for a slow but working host
- **READ_TIMEOUT** — bounded so a slow-drip response cannot hold a worker indefinitely
- **MAX_REDIRECTS** — matches the floor RFC 9309 §2.3.1.2 states for robots retrieval, so one number governs both paths and a reader is not comparing two limits
- **MAX_RETRIES** — a retry can observe a different world state, and Mission 1.71 deferred the which-attempt-counts rule to the construct. With no construct, zero avoids creating records whose selection rule nobody has decided
- **MAX_HEADER_BYTES** — 64 KiB of headers is far beyond ordinary and finite
- **MAX_RESPONSE_READ_BYTES** — 1 MiB read cap. This is the NETWORK bound and it applies even though no body is persisted, because not storing is not the same as not receiving
- **MAX_TOTAL_BYTES_PER_TARGET** — 2 MiB across every hop, so a redirect chain cannot multiply the read cap
- **MAX_RUN_DURATION** — six hours; a run that cannot finish inside one operator sitting is not a bounded pilot
- **ROBOTS_REQUEST_BUDGET** — one fetch per origin, no cache across runs, and it counts toward the origin budget
- **MAX_REQUESTS_PER_TARGET** — one initial request plus MAX_REDIRECTS hops. Robots is counted per ORIGIN rather than per target, so it is not included here
- **BACKOFF_POLICY** — explicitly disabled rather than absent, because MAX_RETRIES is 0 and a backoff with nothing to back off from would be a setting nobody could reach

## One target is not one request

One target equals one request: **False**. Redirects and robots retrievals both count toward the origin budget, and a run must
report:

- requests per manifest target
- requests per origin
- total requests

## Body disabled, network still bounded

Body persistence is `DISABLED` and the network read is bounded
by `MAX_RESPONSE_READ_BYTES`. Not persisting a body means not receiving
bytes: **False**.
