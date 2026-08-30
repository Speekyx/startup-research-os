# GDELT RawRecord Gap Analysis V1

**Status:** Analysis record. Produced by Mission 1.9 §17, **before** any
persistence contract was designed — which is why the collector in that mission
was not written.
**Date:** 2026-08-30
**Reads:** the GDELT DOC 2.0 API as its own documentation describes it and as one
observed response shows it; the committed `gdelt` entries in
[`source-catalog-v1.json`](source-catalog-v1.json) and
[`source-compliance-v1.json`](source-compliance-v1.json).
**Related:** [`gdelt-compliance-v1.md`](gdelt-compliance-v1.md),
[`world-bank-collector-v1.md`](world-bank-collector-v1.md),
[`new-source-compliance-gap-analysis-v1.md`](new-source-compliance-gap-analysis-v1.md).

---

## 0. What this document concluded

Mission 1.9 set out to implement the GDELT DOC API collector. §17 required this
audit **before** persistence contracts changed. The audit found that the
collector cannot be responsibly written yet, for a reason that is neither a code
problem nor a policy problem but a mismatch between two governance artefacts
that were each correct on their own terms.

**The authorised data categories and the reviewed access profile do not
intersect.** The minimisation profile permits themes, entities, tone, events,
period and geography. The reviewed `gdelt-doc-api` profile, in its article mode,
returns article references — URLs, headlines, images, domains — and none of the
permitted categories except period and geography, neither of which is a measure.

Building on top of that would have produced either an empty collector or a
governance violation. Both are worse than stopping.

---

## 1. What was established, and how

| Fact | How |
|---|---|
| DOC 2.0 base endpoint and parameters | GDELT's own announcement post, retrieved 2026-08-30 |
| The `ArtList` JSON envelope | **one live response observed**, non-persisting |
| `TimelineVol` / `TimelineTone` envelopes | **not established** — §5 |
| GDELT enforces rate limiting | HTTP 429 returned to a probe, §6 |
| This environment cannot reach GDELT over HTTP | twelve consecutive failures against a working control, §7 |

Nothing below is inferred from memory. Where a shape could not be observed it is
recorded as unobserved rather than reconstructed.

## 2. The endpoint and its parameters

```text
https://api.gdeltproject.org/api/v2/doc/doc
```

| Parameter | Values |
|---|---|
| `QUERY` | search expression; supports `domain:`, `theme:`, `tone:` operators |
| `MODE` | `ArtList`, `TimelineVol`, `TimelineVolRaw`, `TimelineTone`, `ToneChart`, image and word-cloud modes |
| `FORMAT` | HTML by default; `json` available |
| `TIMESPAN` | e.g. `1d`, `1week`, `3months` |
| `STARTDATETIME` / `ENDDATETIME` | `YYYYMMDDHHMMSS` |
| `MAXRECORDS` | default 75, **maximum 250**, article modes only |
| `SORT` | `DateDesc`, `DateAsc`, `ToneDesc`, `ToneAsc`, `HybridRel` |

`MAXRECORDS` capping at 250 matters more than it looks — §4.2.

## 3. The `ArtList` envelope, observed

```json
{"articles": [
  {"url": "...", "url_mobile": "...", "title": "...",
   "seendate": "20260829T171500Z", "socialimage": "...",
   "domain": "ksat.com", "language": "English",
   "sourcecountry": "United States"}
]}
```

Eight fields. One top-level key.

## 4. Every returned field against the committed minimisation profile

The profile is the one Mission 1.8 committed, quoted from
`source-compliance-v1.json` rather than from anybody's memory of it:

```text
allowed   event_identifier · theme_identifier · entity_mention · tone_score
          observation_period · geography · content_origin
excluded  article_full_text · publisher_content · personal_data · user_identifier
```

| Returned field | Category | Verdict |
|---|---|---|
| `seendate` | `observation_period` | **allowed** |
| `sourcecountry` | `geography` | **allowed** |
| `title` | **`publisher_content`** | **excluded by name** — a headline is the publisher's text |
| `socialimage` | `publisher_content` | **excluded** |
| `url`, `url_mobile` | publisher reference | **not in the allowed list** |
| `domain` | publisher identifier | **not in the allowed list** |
| `language` | — | **not in the allowed list** |

§6 of the mission brief is explicit that presence in a response is not permission
to persist, and §21 makes URL storage conditional on the profile permitting it —
*"if URL storage is permitted by the current minimisation profile"*. It is not.

### 4.1 What survives is two dimensions and no measurement

`ArtList` yields exactly `observation_period` and `geography`. There is no
`event_identifier`, no `theme_identifier`, no `entity_mention` and no
`tone_score` anywhere in the mode — and nothing that measures anything.

An observation with two dimensions and no measure is not an observation.

### 4.2 The obvious workaround is a fabrication, and was rejected

The tempting move is to count the returned articles and persist
*(query, date, country) → N articles*. That uses only permitted categories and
contains no publisher content.

**It would be a fabricated measurement.** `MAXRECORDS` caps the response at 250,
so `N` measures our own request bound, not GDELT's index. A record saying "37
articles" would be a true statement about our HTTP call and a false one about the
world, and it would be indistinguishable from the latter once stored.
`data-principles.md` forbids exactly this, and it is worse than collecting
nothing because a downstream consumer cannot tell.

### 4.3 A presence observation was also considered

*(query, date, country) → "at least one article existed"* is honest, contains no
publisher content, uses only permitted categories, and is thin to the point of
near-uselessness. It also has the identity problem in §8: the query is **our**
construct, not GDELT's, so the observation key would not be source-native.

Recorded because it is the only ArtList design that is not a fabrication, not
because it is recommended.

## 5. The modes that would fit could not be observed

`TimelineTone` returns tone over time. That maps onto the permitted categories
exactly — `tone_score` plus `observation_period` — and contains no publisher
content whatever. It is the mode this collector should be built on.

**Its JSON envelope could not be established.** Fourteen attempts across two
routes returned `ConnectTimeout`, `ECONNRESET`, `HTTP 429` and finally
`ECONNREFUSED`. GDELT's own documentation describes the modes' *semantics* —
`TimelineVol` reports volume as a percentage of all monitored coverage,
`TimelineVolRaw` returns raw counts plus a `norm` field — but **does not publish
the JSON field names**.

**No parser was written for it, and that is the finding rather than a shortfall
of effort.** A parser composed from invented field names would be validated by
fake responses composed from the same invention: the tests would pass by testing
a guess against itself, which is the failure mode
`test-data-isolation-audit-v1.md` and Mission 1.6.1 both record as worse than no
test at all.

## 6. GDELT rate-limits despite publishing no limit

A probe returned **HTTP 429 Too Many Requests** after a handful of requests
spaced over minutes.

The registry records `rate_limit_known = false` for both profiles, and that stays
true: §13 requires that no invented number be recorded as a provider quota, and
429 tells us a limit exists without telling us what it is. What it does settle is
that the conservative local pacing §13 mandates is a real requirement rather than
a courtesy — and the pacing value must be marked as our own policy, never as
GDELT's.

## 7. This environment cannot reach GDELT

| Target | Result |
|---|---|
| `api.worldbank.org` (control, collected from in Mission 1.5) | **HTTP 200** |
| `api.gdeltproject.org/api/v2/doc/doc` | `ConnectTimeout` |
| `api.gdeltproject.org/` | `ConnectTimeout` |

The same HTTP client, in the same process, moments apart. One `ArtList` response
was obtained through a different, proxied route before that route also began
refusing.

So §34's controlled real acquisition could not have succeeded here even with a
finished collector. That is an environment limitation and is recorded as one — it
says nothing about GDELT's willingness to serve a well-behaved client from
somewhere else.

## 8. Identity, if the collector is later built

§19 asks for a stable observation key from **source-native** identity.

The World Bank key is `source | indicator | geography | period`, and every part
is the source's own: the indicator code is GDELT's equivalent of a series id.

GDELT's DOC API has no equivalent. What identifies a timeline observation is
`(query, mode, timestep)` — and **the query is ours**. Two research questions
phrased differently produce different keys for the same underlying coverage, and
the same query re-run over an overlapping window produces the same key with
possibly different values, which is a revision the model can represent.

That is workable and it is not the same guarantee World Bank has. §19 requires
the gap be documented rather than papered over with a title-derived identity,
which would be unstable in exactly the way it warns about.

## 9. Two defects found in the committed governance

Both are real, both were found by trying to use the registration rather than by
reading it, and both would block **any** GDELT collector.

### 9.1 No `endpoint_url` on either access profile

```text
gdelt-doc-api      endpoint_url = None
gdelt-bulk-files   endpoint_url = None
    -> host allowlist derived by the collector: EMPTY
```

The collector derives its host allowlist from `context.access[].endpoint_url`,
deliberately — Mission 1.5 §10 forbids a hard-coded domain so that revoking a
profile in the registry revokes the host. With no endpoint recorded, GDELT
authorises **no host at all**, and the transport refuses an empty allowlist
rather than defaulting to a guess.

The registration was never wrong about policy; it simply never recorded where
the approved API lives, because Mission 1.7 registered a source nobody was going
to call and Mission 1.8 configured obligations rather than endpoints.

**Fixed in this mission**, because it is unambiguous and needed by any future
attempt.

### 9.2 No authorised datasets

`context.datasets` is empty for GDELT, so `authorized_dataset(...)` returns
`None` for every resource and `build_draft` refuses to build a row. That is the
resource model failing closed exactly as designed — a resource nobody reviewed
has no licence, no family and no content origin.

**Not fixed here.** Populating it requires deciding what a GDELT resource *is*,
and that decision depends on which mode the collector uses, which depends on §5.
Guessing it now would fix the symptom and lock in the wrong answer.

There is also a smaller question waiting there: `AuthorizedDataset.licence` is
required and non-empty, and **GDELT names no licence** — it grants unlimited use
directly rather than through a named instrument. The honest value is an
identifier for the grant instrument itself rather than a licence name, and since
`licence_allowlist` is `null` nothing matches against it. Worth deciding
deliberately rather than in passing.

## 10. What would unblock this

In order.

1. **Observe a `TimelineTone` and `TimelineVolRaw` response** from an
   environment that can reach `api.gdeltproject.org`. One response per mode is
   enough. This is the only genuine blocker.
2. **Decide the resource model** — one authorised dataset per mode, most likely
   — and populate `datasets` on the compliance entry, including what to record
   for a source that names no licence.
3. **Confirm the minimisation profile against the chosen mode.** If the
   collector uses `TimelineTone`, the committed profile already fits and needs no
   change. If a volume mode is wanted, the profile has no category for a count
   and would need a reviewed addition — which is governance work, not collector
   work.
4. Then build the collector. Everything else it needs already exists: the
   transport enforces the host allowlist and refuses redirects, the authorization
   context is mandatory by signature, bounds and pacing have a working precedent,
   and the persistence layer is idempotent and revision-aware.

**None of steps 1 to 3 is code.** That is the shape of this finding: the missing
piece was never the collector.
