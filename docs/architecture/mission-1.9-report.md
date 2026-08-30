# Mission 1.9 — GDELT collector: the audit that stopped it being written

**Date:** 2026-08-30
**Branch:** `sprint-1/mission-1.9`
**Status:** **Incomplete as specified, and deliberately so.** The collector was
not implemented. §17's audit — which the brief requires *before* persistence
contracts change — found that it could not be responsibly written yet.

**Deliverables:**
[`gdelt-raw-record-gap-analysis-v1.md`](../data/gdelt-raw-record-gap-analysis-v1.md) ·
one governance defect fixed · `test_gdelt_readiness.py`

---

## 0. What happened, in one paragraph

§17 required auditing the real DOC API response shape before designing RawRecord
semantics. Doing that turned up three things in order: GDELT's article mode
returns publisher references rather than the themes, entities and tone the
authorised minimisation profile permits; the timeline modes that *would* fit
cannot have their JSON envelopes observed from here and GDELT does not publish
them; and neither of GDELT's access profiles recorded an endpoint, so the host
allowlist any collector derives from the registry was **empty** and no request
could ever have been made.

The first two block the collector. The third was fixed.

**Writing the collector anyway would have meant inventing the field names of a
response nobody has seen, and validating that parser with fake responses built
from the same invention.** That is a test passing by checking a guess against
itself — the failure mode Mission 1.6.1 recorded as worse than no test.

## 1. The collector architecture that was not built

Everything it needs already exists, which is worth stating because it is *not*
what is missing:

| Requirement | Status |
|---|---|
| Authorization mandatory by signature (§10) | exists — `WorldBankCollector.collect` is the pattern |
| Host allowlist derived from the registry (§12) | exists in `transport.py`, and now has a host to derive |
| Redirects refused rather than followed | exists |
| Bounded response size, explicit timeouts | exists |
| Bounds, pacing, retry taxonomy (§13–§16) | exist, with a working precedent |
| Idempotent, revision-aware persistence (§44) | exists |
| **A parser for the response** | **cannot be written — §3** |

The missing piece was never the collector.

## 2. DOC API scope

`https://api.gdeltproject.org/api/v2/doc/doc`, parameters `QUERY`, `MODE`,
`FORMAT`, `TIMESPAN`, `STARTDATETIME`/`ENDDATETIME`, `MAXRECORDS` (default 75,
**max 250**), `SORT`. Modes span article listings, timelines, tone charts and
image collages.

Only `gdelt-doc-api` was in scope. `gdelt-bulk-files` was not touched, and
deliberately still records **no endpoint** — the allowlist is derived from
profiles, so giving it one would authorise a host no collector may reach.

## 3. Raw-response audit

### 3.1 `ArtList`, observed

```json
{"articles": [{"url": "…", "url_mobile": "…", "title": "…",
               "seendate": "20260829T171500Z", "socialimage": "…",
               "domain": "ksat.com", "language": "English",
               "sourcecountry": "United States"}]}
```

### 3.2 Against the committed minimisation profile

| Field | Category | Verdict |
|---|---|---|
| `seendate` | `observation_period` | allowed |
| `sourcecountry` | `geography` | allowed |
| `title` | **`publisher_content`** | **excluded by name** |
| `socialimage` | `publisher_content` | **excluded** |
| `url`, `url_mobile`, `domain` | publisher reference | **not in the allowed list** |
| `language` | — | **not in the allowed list** |

**`ArtList` yields two dimensions and no measurement.** There is no
`event_identifier`, no `theme_identifier`, no `entity_mention` and no
`tone_score` anywhere in the mode.

### 3.3 Two workarounds considered and rejected

**Counting the articles** — *(query, date, country) → N* — uses only permitted
categories and contains no publisher content. It is also a **fabricated
measurement**: `MAXRECORDS` caps the response, so `N` measures our own request
bound rather than GDELT's index. A record saying "37 articles" would be true
about our HTTP call and false about the world, and indistinguishable from the
latter once stored.

**A presence observation** — *"at least one article existed"* — is honest, thin
to the point of near-uselessness, and carries the identity problem in §5.

## 4. The minimisation boundary, and where it came from

The profile permits themes, entities, tone and events. Those are GDELT's
**GKG and Events** data model — the bulk files, which §54 forbids implementing.
The DOC API's article mode serves something else.

The error is traceable and nobody was careless: Mission 1.7 recorded GDELT's
capabilities from the project's general description; Mission 1.8 wrote a
minimisation profile from those capabilities; Mission 1.9 is the first to ask
what the reviewed *access profile* actually returns.

**`TimelineTone` would fit the committed profile exactly** — tone over time is
`tone_score` plus `observation_period`, with no publisher content whatever. It
is the right mode and its envelope is unobtainable.

## 5. Identity, documented rather than papered over

§19 asks for a source-native observation key and says to document the gap if
there is not one.

There is not one. World Bank's key is `source | indicator | geography | period`
and every part is the source's own. GDELT's DOC API has no series identifier:
what identifies a timeline observation is `(query, mode, timestep)`, and **the
query is ours**. Two research questions phrased differently produce different
keys for the same coverage.

That is workable and it is a weaker guarantee than World Bank has. Deriving an
identity from an article title instead would be exactly the instability §19 warns
against.

## 6. Pacing — and evidence that it is needed

GDELT returned **HTTP 429 Too Many Requests** to a probe after a handful of
requests spaced over minutes.

`rate_limit_known` stays **false** on both profiles. 429 proves a limit exists
without revealing what it is, and §13 forbids recording an invented number as a
provider quota. What it does settle is that the conservative local pacing §13
mandates is a real requirement rather than a politeness — and that the value,
when chosen, must be marked as our policy and never as GDELT's.

## 7. This environment cannot reach GDELT

| Target | Result |
|---|---|
| `api.worldbank.org` — control, collected from in Mission 1.5 | **HTTP 200** |
| `api.gdeltproject.org/api/v2/doc/doc` | `ConnectTimeout` |
| `api.gdeltproject.org/` | `ConnectTimeout` |

Same client, same process, moments apart. Fourteen attempts across two routes
produced `ConnectTimeout`, `ECONNRESET`, `429` and finally `ECONNREFUSED`.

**§34's controlled acquisition could not have succeeded here even with a
finished collector.** That is an environment limitation and says nothing about
GDELT's willingness to serve a well-behaved client from elsewhere.

## 8. The governance defect that was fixed

```text
before   gdelt-doc-api  endpoint_url = None  ->  host allowlist: EMPTY
after    gdelt-doc-api  endpoint_url = https://api.gdeltproject.org/api/v2/doc/
                                            ->  host allowlist: {api.gdeltproject.org}
```

The collector derives its allowlist from the registry precisely so that revoking
a profile revokes the host (Mission 1.5 §10 forbids a hard-coded domain). With no
endpoint recorded, GDELT authorised **no host at all** and the transport refuses
an empty allowlist rather than defaulting to a guess — fail-closed, and not what
Mission 1.7 intended when it registered the source.

Found by trying to use the registration rather than by reading it. `bulk-files`
deliberately still has none.

## 9. The defect that was NOT fixed

`context.datasets` is empty, so `authorized_dataset(...)` returns `None` and no
draft can be built. Populating it requires deciding what one GDELT resource *is*,
which depends on which mode the collector uses — the question §3 could not
answer. Fixing the symptom now would lock in the wrong answer.

Inside it sits a smaller decision: `AuthorizedDataset.licence` is required and
non-empty, and **GDELT names no licence** — it grants unlimited use directly.
Recorded as **H-28** rather than settled in passing.

## 10. Tests and CI

`test_gdelt_readiness.py`, 9 tests. They assert the governance a collector will
need, and they are written **against the derived allowlist rather than the JSON
field**, because the derived value is what the transport is handed and it is what
was broken.

Three assert the absence of things, which is the honest shape here: no
`gdelt.py` in the collection package, `gdelt` not in `IMPLEMENTED_COLLECTORS`,
`collector_enabled` false. A half-written collector left on a branch reads as
available to the next person who greps for it.

**Zero GDELT network requests in CI**, unchanged — there is no collector to make
one.

## 11. Existing-data survival

Verified field by field: six raw and six normalized records, `source_id`
`world-bank` only, values identical to Mission 1.6.1, every session link intact.
Registry state unchanged across the full suite.

## 12. What would unblock this, in order

1. **Capture one `TimelineTone` and one `TimelineVolRaw` response as JSON**, from
   anywhere that can reach the API, and commit them as fixtures. **This is the
   entire blocker** (**H-27**).
2. **Decide the resource model** — one authorised dataset per mode — and populate
   `datasets`, including what to record for a source that names no licence
   (**H-28**).
3. **Confirm the minimisation profile against the chosen mode.** `TimelineTone`
   needs no change. A volume mode would need a reviewed category for a count,
   which is governance work.
4. Then build the collector, which is then a day's work against machinery that
   already exists.

**None of steps 1 to 3 is code.**

---

## The questions §53 asks explicitly

| Question | Answer |
|---|---|
| Is the GDELT collector implemented? | **No** — §0, and the reason is §3 |
| Is GDELT still collector-eligible? | **Yes**, unchanged. `APPROVED_WITH_CONDITIONS`, condition satisfied |
| Is GDELT enabled? | **No**, and it must not be — nothing implements it |
| Which access profile does it use? | None. `gdelt-doc-api` is the one it *would* use; `gdelt-bulk-files` was not touched and still authorises no host |
| Can it operate without `AcquisitionAuthorizationContext`? | No collector exists. The pattern it would follow makes the context the required first argument with no overload |
| Can it reach a resource without `authorize_resource`? | No collector exists. `context.datasets` is empty, so every resource is refused today |
| Can it fetch publisher article pages? | **No.** No collector, and the transport takes a path plus a query against an authorised base — there is no signature anywhere that accepts a URL |
| Can it persist article full text? | **No**, and this is why nothing was built: the profile excludes `publisher_content` by name, and `title` is the publisher's text |
| Is third-party content fail-closed? | **Yes** — `third_party_denied`, plus `require_dataset_family`. `THIRD_PARTY`, `UNKNOWN` and unclassified are all refused |
| Is attribution attached to every GDELT RawRecord? | Vacuously — there are none. The obligation is configured and its condition verifies `SATISFIED` |
| Is retention governance-derived? | Yes, baseline 30/365 via the authorization context. No collector can choose its own |
| Is pacing an internal decision rather than an official limit? | **Yes**, and `rate_limit_known` stays false. GDELT returned 429, which proves a limit exists without revealing it |
| Is duplicate Celery delivery safe? | No GDELT task exists. The persistence layer it would use is idempotent by `content_hash` |
| Are GDELT RawRecords tenant-isolated? | Vacuously — there are none. RLS and the workspace filter apply to `raw_records` regardless of source |
| Did the live smoke succeed? | **No, and it was not written.** This environment cannot reach the host — §7 |
| Did controlled real acquisition succeed? | **No.** Blocked by §3 and independently by §7 |
| How many real GDELT RawRecords now exist? | **Zero** |
| Were any third-party publisher requests made? | **No.** The only external requests were to GDELT's own API for shape-establishing, and to CC BY-SA's legal code in Mission 1.8 |
| Did all twelve World Bank rows remain unchanged? | **Yes**, verified field by field |
| Were GDELT records normalized? | No — there are none. `normalized_records` is World Bank only |
| Were any signals created? | **No.** 0 |
| Were any embeddings created? | **No.** 0. D-12 open |
| Were any Claims/Evidence created? | **No.** 0 |
| Was any scoring performed? | **No.** Aggregation uncalibrated |
| Is Mission 1.10 safe to begin? | **Yes**, and it should begin with H-27 rather than with code |

### Against §52's success criteria

**Criteria 1 and 13 are not met**: the collector does not exist and no controlled
acquisition happened. Criteria 5, 6, 7, 14 and 15 hold — vacuously for some, and
by governance for the rest. The remainder are conditional on a collector.

**This mission did not succeed on its own terms**, and the reason is a finding
rather than an absence of effort.

---

## What was actually learned

The brief was written on the premise that Mission 1.8 had left GDELT ready to
collect from. It had left it *approved*, which is a different thing, and the gap
between them was invisible until something tried to use it.

Three artefacts each correct in isolation — a review recording GDELT's
capabilities from its general description, a minimisation profile written from
those capabilities, and an access profile approving the DOC API — combined into a
registration that authorises data the approved route does not serve, at a host it
does not name.

**§17 exists to catch exactly this, and it did.** The instruction to audit the
response shape *before* changing persistence contracts is the only reason this
was found now rather than after a collector had been written, tested against
invented fixtures, and shipped.

---

## Validation

Full suite green · registry and tenant state unchanged · ruff · mypy ·
`sros-source validate` (27 sources, 30 evidence records, 0 warnings) ·
all generated documents in sync · six raw and six normalized World Bank records
unchanged · **zero GDELT records, zero signals, zero embeddings, zero claims**.
