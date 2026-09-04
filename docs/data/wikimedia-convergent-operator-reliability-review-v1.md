# The completed Wikimedia convergent reliability review

**`wikimedia-convergent-operator-reliability-review@1.0.0`**, performed under **`human-reliability-assessment-rubric@1.0.0`**. Authored by the reviewer; this page is rendered from it.

**This is a completed review, not a preparation packet** — which is why it carries a number where the Mission 1.44 packet carried a blank. That packet records the question as it stood and is not rewritten by this answer.

---

## The scope

```text
source_id         wikimedia-pageviews
resource_id       metrics/pageviews/per-article/en.wikipedia.org
record_kind_id    content_request_count
claim_type        OBSERVED
proposition_kind  platform_counted_content_request_change_witnessed
```

It binds **18 Evidence rows across 6 Claims**, with witness cardinalities `4`, `3`, `3`, `3`, `3`, `2` — spanning articles `Docker_(software)`, `Kubernetes`, `Podman`, directions `INCREASING`, `DECREASING` and requester classes `user`, because a reliability scope carries none of them.

Exactly five fields, matched in full or not at all. The existing wikimedia-pageviews assessment at 0.65 shares FOUR of them and differs on proposition_kind, which is a different reliability question and not a baseline for this one. The scope carries no article, no direction, no requester class, no period and no witness count, so one judgement binds every convergent Evidence row from this measurement.

## The judgement

| | |
|---|---|
| **Reliability** | **0.6** |
| Origin | `HUMAN_REVIEW` |
| Reviewer | `thibchm` |
| Gate | `NUMERIC_JUDGEMENT_PERMITTED` |
| Rubric | `human-reliability-assessment-rubric@1.0.0` |

Supplied by the reviewer. Not rounded, not rescaled, not derived from the ordinal ranks, not anchored to the 0.65 at the detailed Wikimedia scope, not copied from the 0.55 at the convergent TED scope, and not an average of anything. It is a human summary of the recorded ordinal profile above, and the profile is what a second reviewer reproduces.

## The ordinal profile the number summarises

| dimension | state |
|---|---|
| `MEASUREMENT_DEFINITION` | `DOCUMENTED_AND_BOUNDED` |
| `SOURCE_SIDE_VALIDATION` | `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` |
| `HISTORICAL_MUTABILITY` | `PARTIALLY_DOCUMENTED` |
| `COMPLETENESS_AND_MISSINGNESS` | `PARTIALLY_DOCUMENTED` |
| `SOURCE_SIDE_CHECKABILITY` | `NOT_ESTABLISHED` |

NOT_ESTABLISHED is not 0, not low, not a midpoint, not 0.5 and not a weakness on a scale. It has no ordinal rank in the rubric precisely so that it cannot be interpolated or averaged, and nothing here converts it to a number.

## Material unknowns

| dimension | unknown | documented | material? |
|---|---|---|---|
| `HISTORICAL_MUTABILITY` | whether a published per-article daily value may later be revised, recomputed or corrected, and whether a consumer could tell that it had been | `PARTIAL` | **YES** |
| `SOURCE_SIDE_VALIDATION` | whether requester-class tagging may be re-applied retroactively to values already published | `PARTIAL` | **YES** |
| `HISTORICAL_MUTABILITY` | whether a systematic reclassification would remove EVERY witness of one convergent Claim at once, given that the witnesses share one methodology and their independence is UNKNOWN | `NOT_ESTABLISHED` | **NO** |
| `MEASUREMENT_DEFINITION` | whether the pageview definition or the tagging rules changed across the 2024-03 witness periods | `NOT_ESTABLISHED` | **NO** |
| `SOURCE_SIDE_CHECKABILITY` | how long a published per-article daily value remains retrievable at the source | `NOT_ESTABLISHED` | **UNSURE** |
| `COMPLETENESS_AND_MISSINGNESS` | whether any of the six witness dates in 2024-03 falls inside an entry on the known-problems list | `NOT_ESTABLISHED` | **UNSURE** |

Two UNSURE answers are preserved as UNSURE. UNSURE is not YES, not NO, not low confidence and not a number, and the rubric permits it precisely because a reviewer who cannot yet tell whether an unknown matters has said something real. Both are carried into the stated limitation rather than quietly resolved.

## Hard stops

| hard stop | triggered |
|---|---|
| `MEASUREMENT_SEMANTICS_NOT_ESTABLISHED` | **NO** |
| `PROPOSITION_EXCEEDS_MEASUREMENT` | **NO** |
| `AUTHORITATIVE_DOCUMENTS_CONTRADICT` | **NO** |
| `SOURCE_OBSERVATIONS_NOT_RECOVERABLE` | **NO** |

None triggered, and the fourth answer is the one worth reading twice. SOURCE_SIDE_CHECKABILITY is NOT_ESTABLISHED and SOURCE_OBSERVATIONS_NOT_RECOVERABLE is NO, which are consistent rather than contradictory: the first says the held basis does not establish long-term checkability, the second would be the stronger claim that the observations are KNOWN to be unrecoverable. The reviewer answered the weaker fact and the stronger claim separately, and software did not derive one from the other.

A human decision, taken against the profile above. The rubric defines the gate as judgement rather than an arithmetic function; nothing recomputed it from the ordinal states, and the two YES materiality answers did not automatically refuse it, because §13 of the rubric forbids blocking on every unknown.

## Rationale

The reliability judgement is based on first-party Wikimedia documentation that defines the pageview measurement, requester-class tagging rules, documented exclusions, and known-problem history.

The measurement definition is documented and bounded for this proposition, while requester classification relies on documented heuristic tagging. Historical revision behaviour and completeness are only partially documented, and source-side long-term checkability is not established.

I consider the documentary basis sufficient to permit a numeric reliability judgement while preserving unresolved questions concerning retroactive revision/reclassification and long-term retrievability.

## Stated limitation

The held documentation does not fully establish how historical pageview values or requester classifications may be revised or reprocessed after publication, nor how a consumer would detect such changes.

Long-term retrievability of historical daily values remains unestablished, and it is also unresolved whether any reviewed witness date coincides with a documented known-problem period.

Multiple witnesses share the same publisher, counting methodology, requester-classification mechanism and pipeline, so witness cardinality does not establish independent corroboration.

Both texts were PREPARED AS DRAFTS by the assistant and are recorded here so the reviewer can read the exact wording before it becomes theirs. They are NOT yet human-authored: the accountable persistence workflow prints this file and requires the reviewer to type a confirmation stating that what it contains is THEIR judgement, and that keystroke is what converts a draft into a review. Until it is typed, this file is a proposal.

## Documentary basis

- **Research:Page view** (`Definition; Tagging`, `MEASUREMENT_METHODOLOGY`, retrieved 2026-09-03) — **REUSED**. It defines what a pageview IS and how requester classes are tagged. The convergent proposition reads exactly the same measurement through exactly the same rules, and the document is if anything more load-bearing here, because audience_class is one of the six identity fields the convergence contract keeps.
  - *Finding:* The pageview definition is an explicit conjunction of HTTP-status, host and header conditions with an enumerated exclusion list; automated traffic is tagged by ua-parser plus custom regex.
- **Data Platform / Data Lake / Traffic / Pageviews** (`Events and known problems since 2015-05-01`, `KNOWN_LIMITATION`, retrieved 2026-09-03) — **PARTIALLY_APPLICABLE**. The fact is unchanged and remains a real limitation. Its weight moves in two directions at once under an existential: a LOCALISED problem matters less, because only one surviving witness is needed, while a SYSTEMATIC reclassification matters more, because the several witnesses share a methodology and their independence is UNKNOWN. The reviewer weighed both.
  - *Finding:* A dated known-problems list exists and records a 2016 user-agent classification incident; revision and backfill practice is not documented.

Both documents were already held on the detailed Wikimedia assessment and NOTHING WAS FETCHED for this review: the convergent proposition reads the same measurement through the same rules. No SROS engineering validation is among them. The convergence contract's determinism, the witness-key duplicate guard, the Evidence idempotency repair, lineage recovery and passing CI establish that the implementation does what its specification says, and nothing about how dependable the platform's counting is.

## What this is not

- HUMAN_REVIEW, and NOT CALIBRATION. REFERENCE_PROFILE_V1 remains UNCALIBRATED and this value fits no parameter.
- NOT A PROBABILITY that any Claim is true.
- NOT SOURCE-WIDE. The scope is five fields; wikimedia-pageviews alone matches nothing.
- NOT AN AUDIENCE SCORE. A request is what a reader makes of a server, and the requester class is the platform's own label rather than a statement about people.
- NOT A PRODUCT SCORE. It says nothing about Docker, Kubernetes or Podman as products, and the scope carries no article at all.
- NOT INDEPENDENT CORROBORATION. The witnesses share one publisher, one counting methodology, one requester-classification mechanism and one pipeline, and independence stays UNKNOWN.
- NOT a judgement about the detailed Wikimedia proposition, whose 0.65 belongs to a different scope and is untouched.

## What it produced

Assessment `19e0ce16-957f-4543-9b15-738a77b13060`, version **1**, recorded 2026-09-04T06:51:19.661075+00:00.

This field was null until the accountable workflow recorded the assessment, and it was filled in with the id, version and timestamp only after the reviewer had typed the confirmation. It is here so this file states what its own judgement PRODUCED rather than what it hoped to produce, and so the review and the row it created can be read against each other.
