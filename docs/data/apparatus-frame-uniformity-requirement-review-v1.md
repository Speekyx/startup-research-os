# Apparatus requirement review — configuration uniformity across the frame

Generated from `apparatus-frame-uniformity-requirement-review-v1.json`.
Do not edit by hand.

**Candidate rule:** `APPARATUS_CONFIGURATION_MUST_BE_UNIFORM_ACROSS_THE_FRAME`

**Decision: ADOPT.** Registry 14 to 15.

Produced before final candidate selection, because a rule adopted after seeing
which candidates it would eliminate is a rule chosen for its outcome.

## 1. The failure mode

One apparatus applies different measurement configurations to different parts of its own population during the same nominal observation window, so that the load-bearing predicate is eligible in one part of the frame and not eligible in another. A single count then merges sub-populations selected under different measurement definitions, and the difference lives INSIDE the apparatus rather than between apparatuses, where a comparison would expose it.

*Worked case:* If TCP/22 is inside the port set applied to partition P1 and outside the set applied to partition P2, an address in P2 is not eligible to appear at all. A count over the whole frame reports a number whose deficit is indistinguishable from an address genuinely not answering on 22.

*Why this is not merely incompleteness:* Incompleteness is a known shortfall against a defined population. Here the population itself has no single definition, so there is no quantity the count is incomplete with respect to.

## 2. Distinctness

| compared against | verdict |
|---|---|
| `SAMPLING_IS_LOAD_BEARING` | DISTINCT |
| `THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME` | DISTINCT |
| `APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE` | DISTINCT |

**Against sampling.** Sampling asks which ELIGIBLE targets were actually attempted. Uniformity asks whether the predicate was ELIGIBLE AT ALL in that part of the frame. A perfectly executed census of a partition whose configuration never opens TCP/22 returns zero for the construct, and no sampling disclosure repairs that: the sampling was complete and the measurement was never defined there.

Uniformity is upstream of sampling. Sampling presupposes an eligible set, and uniformity is what decides whether one exists.

**Against the retrievable frame.** That rule governs what the REQUESTER may retrieve from what the apparatus measured — Mission 1.62's case, where an apparatus scans everything and can show a requester only their own networks. Uniformity governs what the apparatus MEASURED, before retrieval is reached at all. A uniformity failure survives unrestricted retrieval, because the observations that would have closed the gap were never generated.

**Against time-addressability.** Time-addressability asks WHEN a configuration applied. Uniformity asks WHERE within the frame it applied, inside one window. The two are independent in both directions: an apparatus can publish a perfectly dated configuration history that is heterogeneous across regions at every date, and an apparatus can be uniform across its whole frame while publishing only a current, undated port list.

## 3. Demonstrated, twice, in two shapes

### First instance — ONYPHE, declared regional partitions

> Once per week: a week from US, the other one from FR, same list of 500 ports
>
> Once per week: a week from SG, the other one from CN, TOP 25 ports
>

*Source:* ONYPHE Data Refresh Rate page, datascan category, same table, retrieved first-party in Mission 1.66.2 and recorded in docs/data/onyphe-datascan-port-configuration-public-doc-review-v2.json

*Reading:* One apparatus applies at least two port configurations to different parts of the population it measures, within one category. Whether TCP/22 sits inside the 500 and outside the TOP 25 is exactly what is not published, which is what makes this a rule about PUBLISHED STRUCTURE rather than a complaint about a particular port set.

### Second instance — Shodan, per-step randomisation

> Generate a random IPv4 address
>
> Generate a random port to test from the list of ports that Shodan understands
>
> the crawlers don't scan incremental network ranges. The crawling is performed completely random to ensure a uniform coverage of the Internet.
>

*Source:* https://book.shodan.io/behind-the-scenes/crawler-algorithm/

*Reading:* Heterogeneity here is not partitioned by region but produced by randomisation per crawl step: the port under test is drawn per step, so TCP/22 is not applied to every crawled address within a window. The effective configuration varies across the frame by construction rather than by policy.

**Why two shapes matter.** A rule demonstrated only by regional partitioning would look like a rule about scanner geography. Two shapes — declared regional partitions and per-step randomisation — show the rule is about whether the apparatus publishes enough structure to say which configuration reached which part of the frame, however the heterogeneity arose.

## 4. Effect on qualification

It becomes a gate applied BEFORE candidate selection rather than a risk noted afterwards. Any candidate publishing regional scanner groups, tiered port sets, randomised target or port selection, or per-customer scan profiles must now be asked whether the configuration that reached each part of the frame is determinable. Both apparatuses evaluated in this mission would have been asked it, and one of them raised it unprompted.

*What it does not do:* It does not by itself fail an apparatus. An apparatus whose partitions are explicitly published and separable, or whose configuration identity is carried per observation, satisfies it — and so does one whose load-bearing port is included in every partition.

## 5. The rule as added

> Where one apparatus applies different measurement configurations to different parts of its own population during the same governed measurement period, it must publish enough structure to determine which configuration applied to which part of the frame during that period. Otherwise a single count may silently combine several effective populations. This is not sampling, which asks which eligible targets were attempted; it is not the retrievable frame, which asks what a requester may retrieve; and it is not time-addressability, which asks when a configuration applied. Explicitly published and separable partitions satisfy it, as does a load-bearing port included in every partition, as does configuration identity carried per observation.

*No retrospective weakening:* Mission 1.66.2 recorded this as a named risk and moved no gate. §45 forbids editing that package so a new rule retroactively fails it.
