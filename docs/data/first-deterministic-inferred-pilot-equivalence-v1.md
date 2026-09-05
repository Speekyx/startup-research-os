# First Deterministic Inferred Pilot — Semantic Equivalence V1

**Mission 1.56 — First Deterministic Inferred Claim Persistence Pilot V1 — basis `first-deterministic-inferred-pilot-equivalence-v1`, recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_inferred_pilot.py`.

Whether the source-native measurement carried by Signal 064d12bf bears on the candidate target proposition. It is a DOCUMENTARY judgement, not a computation: the evaluator consumes this decision and never derives it, and nothing here was produced by a model.

Network requests **0**, model calls **0**, every document already held **True**.

## Documents relied on

| document | held since | establishes |
| --- | --- | --- |
| Research:Page view | Mission 1.36 | The complete definition of a pageview: a conjunction of HTTP-status, host and header conditions with an enumerated exclusion list, a UTC request timestamp, and daily partitioning 0:00 to 23:59 UTC. |
| Wikimedia Analytics known problems | Mission 1.44 | A dated incident list, including a 2016 user-agent classification incident, and no stated revision policy. |
| canonical-subject-registry-v1.json | Mission 1.30 | That `wikimedia-pageviews:content:en.wikipedia.org|Kubernetes` names canonical subject `kubernetes`, on the basis that the encyclopedia records no other subject under that title so the article needs no disambiguator. |
| wikimedia-pageviews-v1.md | Mission 1.19 | The collector's own record that `user` means traffic NOT identified as automated by ua-parser plus custom regex -- a heuristic classification, and never a claim that a person read anything. |

## The eight dimensions

| dimension | finding |
| --- | --- |
| `CANONICAL_SUBJECT` | The measurement's content id is the English Wikipedia article `Kubernetes`; the target's subject is the reviewed canonical subject `kubernetes`, which the registry maps to exactly that article key with a stated basis. Exact, and reviewed before this mission existed. |
| `METRIC_DEFINITION` | The target metric is the day-over-day change in content requests, which is precisely what the Signal's extractor computes: the difference between two source-native daily counts. `Research:Page view` supplies the definition of the counted event. |
| `TIME_BOUND` | The target names the same two day labels the Signal carries, and Wikimedia documents its own daily partitioning as 0:00 to 23:59 UTC. Mission 1.19 earned `ESTABLISHED` period semantics on that documentation rather than on the label's shape. |
| `POPULATION` | Requester class `user`. The target names the platform's own class rather than translating it, so the correspondence is exact even though the class itself is a heuristic. It does NOT mean human, person, reader or customer. |
| `GEOGRAPHY` | The per-article endpoint applies no geographic restriction and the access channel is all-access, so the quantity is global by construction. The target says `global` for that reason and not as a default. |
| `UNIT` | `requests`, inherited from the source's own measurement contract. The target uses the same word for the same thing, and no conversion occurs. |
| `ADJUSTMENT` | None on either side. The measurement is a raw difference of two published counts, seasonally unadjusted, and the target asks for the same. |
| `METHODOLOGY_SEMANTICS` | Both sides rest on the same counting rule, because the target is worded from the same document the measurement was produced under. The residuals are recorded as limitations rather than resolved: the requester classification is heuristic, and no revision or backfill policy is documented. |

## Verdict — `EQUIVALENT`

The target proposition was written FROM the measurement's own documented semantics rather than matched against them afterwards, so the correspondence is definitional on seven dimensions and reviewed-by-registry on the eighth. Nothing is inferred from a matching label or a similar name.

### Interpretation confidence — 0.9

Confidence that the Claim's WORDING faithfully states what the cited Signal showed. It is NOT an evidence strength, not a probability, and it is multiplied by nothing.

**Why not 1.0.** ADR-037 §17 forbids setting it to 1.0 merely because the arithmetic is exact. Two documented residuals bear on the wording: the requester class is produced by a heuristic classifier that has been changed before, and no revision policy is documented, so a recomputed day could in principle differ from the day this system holds.

**Why not lower.** The wording names the platform's own class and the platform's own day labels rather than translating either, so a reader of `Research:Page view` can check the sentence against the definition line by line.

*Decided by: proposed here and adopted by the operator's approval of the pilot manifest hash, which is where the human decision for this pilot lives.*

## Stated limitations

- The requester class `user` is heuristic. It means traffic not identified as automated by ua-parser plus custom regex, and a reclassification has happened before (2016).
- Wikimedia documents no revision or backfill policy for these counts, so `the day as this system holds it` and `the day as the platform would recompute it today` are not established to be the same.
- Only Wikimedia's own logs can measure this quantity, so this proposition can never accumulate an independent second witness. The pilot exercises the INFERRED machinery; it does not demonstrate the multi-witness value the layer exists for.
- A request is not a reader. Nothing here supports a claim about people, attention, demand or interest.

Reviewed by **thibchm**, prepared from held documents and adopted by the operator's approval of the pilot manifest hash.

