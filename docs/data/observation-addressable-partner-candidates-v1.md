# Observation-Addressable Partner Candidates V1

**Mission 1.60 — Observation-Addressable Scanner Pair Selection V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_scanner_pair_selection.py`.

Class frozen: `INTERNET_WIDE_ACTIVE_SCANNING`.

Section 10. The search asked for active scanners exposing per-observation scan timestamps and raw banners, not for alternatives or competitors to a named vendor. Brand-first search biases toward commercial similarity rather than apparatus requirements.

Pruning order: A1 active measurement producer → A2 observation-addressable exposure → A3 protocol-native exposure → A5 frame documented → A9 product relevance → A7 lineage → A8 reliability reviewability → pair gates.

*Section 38. Expensive lineage and access research is not spent on an apparatus already dead on observation-time exposure.*

## Candidates

| identity | first failing gate | verdict | researched here |
| --- | --- | --- | --- |
| Censys | `A2` | **SNAPSHOT_TIME_SEMANTICS_NOT_ALIGNABLE** | False |
| The Shadowserver Foundation | `A6` | **DOCUMENTATION_NOT_RETRIEVABLE** | True |
| ONYPHE | `A6` | **DOCUMENTATION_NOT_RETRIEVABLE** | True |
| LeakIX | `A6` | **DOCUMENTATION_NOT_RETRIEVABLE** | True |

**Censys.** 

**The Shadowserver Foundation.** Its network-reporting page states the technical documentation has moved to an external wiki, and the substantive wiki pages did not load at the path tried. So the data model, the record timestamp semantics, the banner exposure and the covered address space could not be established from first-party documentation within budget.

**ONYPHE.** The documented path redirected to another host and the redirected path returned HTTP 404. No first-party statement about observation timestamps, query filtering or banner exposure was obtained.

**LeakIX.** The documented API introduction path returned HTTP 404.

## Result

Inspected **4**, researched here **3**, reached pair analysis **0**, qualifying **0**.

Every partner probed failed at A6 rather than at a substantive gate: their first-party technical documentation was not retrievable at the paths tried within budget. That is a fact about this mission's reach, not a finding about those apparatuses, and it is recorded as such.

**Establishes.** No second observation-addressable scanner was qualified in this mission.

**Does not establish.** That none exists. Three candidates were left at a documentation wall rather than at a verdict, and a mission with working documentation paths could take any of them further.

*The anchor was qualified from four first-party documents. The partners were not qualified because their equivalent documents were not reachable. The asymmetry is in documentation access, not in apparatus quality.*

Pairs constructed: **0**. Section 39. Pairs are generated only between individually qualifying apparatuses. The anchor does not individually qualify (A7 and A8 block it), and no partner was qualified, so there was no pair to test.

