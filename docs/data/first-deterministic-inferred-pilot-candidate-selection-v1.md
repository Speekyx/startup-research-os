# First Deterministic Inferred Pilot — Candidate Selection V1

**Mission 1.56 — First Deterministic Inferred Claim Persistence Pilot V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_inferred_pilot.py`.

Every held Signal was inventoried from the live deployment and put through the fifteen hard gates of §4. No source was preselected, and the evaluator was not run: §3 forbids using the expected direction as a selection criterion, and §9 requires the threshold to be frozen before any evaluation exists.

**33 Signals inspected across 7 families. 1 family passes, 18 Signals.**

| family | n | unit state | verdict | why |
| --- | --- | --- | --- | --- |
| `content_request_change` | 18 | INHERITED | **PASSES** | Unit inherited from the source's own measurement, day buckets documented UTC on Wikimedia's own `Research:Page view` page (Mission 1.19), reviewed canonical subject already registered, and both the counting rule and the known-problems list are HELD by the repository. |
| `community_question_volume` | 1 | DIMENSIONLESS | **FAILS gate 14** | Stack Exchange's own methodology documentation is UNREACHABLE: the site's robots policy blocks this environment's fetcher, established in Mission 1.36 and confirmed in Mission 1.47. METHODOLOGY_SEMANTICS therefore cannot be reviewed from material the project holds, and §43 forbids browsing to rescue a candidate. This is the same insufficiency for which the operator declined both Stack Exchange reliability scopes in Mission 1.36.1. |
| `community_question_without_accepted_answer_volume` | 1 | DIMENSIONLESS | **FAILS gate 14** | The same unreachable methodology, plus Mission 1.32's finding that an unaccepted answer reports one participant's non-action -- which makes the METHODOLOGY_SEMANTICS dimension harder rather than easier. |
| `numeric_period_change` | 4 | NOT_ESTABLISHED | **FAILS gate 5** | The normalized records carry `unit_state = NOT_PUBLISHED` and `unit = null`: the World Bank does not publish a unit for SP.POP.TOTL. `TargetProposition` requires a unit, and writing `persons` would be inferring a unit from a metric name -- exactly what `normalized-record-v1.md` forbids and what the normalizer already refused. §43 forbids fetching documentation to establish one. |
| `procurement_value_contrast` | 6 | INHERITED | **FAILS gate 6** | H-37 is open. The period labels are dates carrying an offset but no time -- `2023-03-10+01:00` -- and Mission 1.15.8 recorded that a published DATE does not become a moment: `observed_at` is NULL and the bounds are naive. The time bound is therefore not exact. |
| `lexical_frequency_change` | 2 | NOT_ESTABLISHED | **FAILS gate [5, 6]** | No unit, and H-29 leaves the bucket timezone unestablished, so neither the unit nor the time bound is exact. |
| `lexical_frequency_contrast` | 1 | NOT_ESTABLISHED | **FAILS gate [5, 6]** | The same two. |

*community_question_volume — It passes every other gate, including the unit gate, and would otherwise have been a strong candidate on §5B.*

*numeric_period_change — This is the ONLY held family whose metric names a quantity in the world rather than an artifact on a platform: Germany's population exists whether or not anyone counts it, and Eurostat, Destatis and FRED could each produce a witness. It is the family for which the INFERRED layer's multi-witness value is real, and it is excluded by a missing unit rather than by anything semantic.*

*procurement_value_contrast — The magnitude is a max-minus-min spread over a cohort SROS assembled, and the subject is `ted-eu:CPV-division:90`, which Mission 1.33 established is a purchasing CATEGORY rather than a product.*

## Selection within the passing family

All 18 are the same family, the same unit, the same number of transformations, the same one-day scope and the same held documentation, so A through F do not discriminate.

Tie-break: the deterministic (source_id, signal_id) rule §5 names. Selected `064d12bf-e7bb-56e7-a90c-bdd08e89d2ac`.

**The magnitude was not a criterion.** The 18 candidates were ordered by `signal_id` and the first was taken. That ordering is blind to magnitude and to direction, and a reader can reproduce it with `SELECT id FROM nlp.signals WHERE signal_type_id='content_request_change' ORDER BY id LIMIT 1`.

*The selected Signal's magnitude and direction were read AFTER the tie-break, for the manifest record.*

## The selected candidate

- `signal_id`: 064d12bf-e7bb-56e7-a90c-bdd08e89d2ac
- `source_id`: wikimedia-pageviews
- `record_kind_id`: content_request_count
- `signal_type_id`: content_request_change
- `magnitude`: 912
- `magnitude_unit`: requests
- `period_labels`: ['2024-03-03', '2024-03-04']
- `content_id`: Kubernetes
- `content_platform`: en.wikipedia.org
- `audience_class`: user
- `access_channel`: all-access

## The fifteen hard gates

|  | gate | how |
| --- | --- | --- |
| 1 | already held canonically | a live row in nlp.signals in workspace dev, derived in Mission 1.19 |
| 2 | one exact scalar numeric measurement suitable for Decimal | magnitude 912, stored NUMERIC and read as Decimal |
| 3 | subject identity exact | `canonical-subject-registry-v1.json` maps `wikimedia-pageviews:content:en.wikipedia.org|Kubernetes` to subject `kubernetes` with a stated basis, reviewed in Mission 1.30 |
| 4 | metric definition exact | the metric names the quantity, the content location, the requester class and the access channel, each taken verbatim from the Signal scope |
| 5 | unit semantics exact | `requests`, INHERITED from the source's own measurement; not inferred here |
| 6 | time bound exact | 2024-03-03 and 2024-03-04, DAY resolution, documented UTC partitioning on the operator's own `Research:Page view` page (Mission 1.19) |
| 7 | population or geography exact or not applicable | the per-article endpoint applies no geographic restriction and the access channel is all-access, so the quantity is global by construction |
| 8 | no unit conversion | target unit equals witness unit exactly |
| 9 | no creative time alignment | the target's time bound is the Signal's own two day labels |
| 10 | no latent behavioural construct | the proposition is about REQUESTS, never readers, viewers, users, demand or interest. Mission 1.19 named that distinction and the wording keeps it |
| 11 | expressible as deterministic THRESHOLD_STATE | a Decimal comparison of one change against one frozen bound |
| 12 | provenance reaches RawRecord and NormalizedRecord | 2 signal inputs, both with a normalized record and a raw record present |
| 13 | governance permits continued analytical use | see the held-data basis below |
| 14 | equivalence reviewable from held material | `Research:Page view` and the known-problems list are both held; see the equivalence artifact |
| 15 | no model needed | the comparison is arithmetic and the equivalence is documentary |

## Held-data analytical use

**§42. May this already-held record still be used for local private derived analytical work?**

The current `local-private-research-v1` review for `wikimedia-pageviews`, version 2, is APPROVED_WITH_CONDITIONS with `derived_analytics = PERMITTED`, `storage = PERMITTED` and `retention = PERMITTED`, read from the live registry.

Mission 1.19 answered H-24 from the Analytics API access policy's own `Data licensing` heading: the data is CC0 1.0, which waives copyright and related rights including the sui generis database right BY NAME. There is no reuse condition left for continued analytical use to breach.

*Mission 1.43 recorded that Wikimedia is currently BLOCKED for NEW acquisition by three unsatisfied capability conditions. §42 anticipates exactly this: eligibility to COLLECT and permission to keep using what is already held are different questions, and this pilot performs no collection.*

## The limitation, stated before approval

**`SOURCE_INDEPENDENCE_IS_PARTIAL`.** ADR-036's INFERRED layer exists so that several apparatuses can bear on ONE proposition. This proposition is about requests to a specific article on a specific wiki platform, and only that platform's own logs can measure it. So the pilot exercises the machinery correctly and cannot demonstrate the multi-witness value the layer was built for.

The subject is a quantity of events that occurred -- requests received -- rather than a publication act. The source did not itself report `the change is at least 1000`; it reported two daily counts, and the threshold proposition is entailed by them. That is ADR-036's own test.

*Where the measurer does enter.* The requester class `user` is Wikimedia's OWN classification, produced by ua-parser plus custom regex and documented as heuristic. It is part of the metric definition because Mission 1.19 made `audience.class` REQUIRED so that one item over one period cannot carry two counts under one name. Dropping it to make the proposition look cleaner would break the correspondence with the measurement.

*`numeric_period_change` over World Bank population, excluded on the unit gate above. Recorded so the next mission can see what it would take: a reviewed unit for SP.POP.TOTL, which needs documentation this mission may not fetch.*

