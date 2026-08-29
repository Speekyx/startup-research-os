# RawRecord Gap Analysis V1

**Status:** Analysis record. Produced by Mission 1.5 §51 **before** the schema was
changed, so the migration can be checked against what was missing rather than
against what was convenient to add.
**Date:** 2026-08-30
**Reads:** `acquisition.raw_records` as migration `0001_foundation` defines it,
against the requirements of Mission 1.5 §17–§25 and §50.
**Related:** [`acquisition-authorization-v1.md`](acquisition-authorization-v1.md),
[`data-principles.md`](data-principles.md),
[`data-retention-policy-v1.md`](data-retention-policy-v1.md),
`evidence-confidence-framework-v1.md` §10.

---

## 0. Why this document exists

`acquisition.raw_records` was designed in Mission 0.1 against a specification,
with no collector to test it. Mission 1.5 is the first mission that writes to it.

§51 says to use the existing schema where possible and to produce a gap analysis
before changing it. This is that analysis. It concludes that **four requirements
cannot be represented at all** by the current columns, and that the table is
otherwise sound — in particular its identity constraint turns out to be exactly
right, which was not obvious until the update semantics were worked through.

The table is empty, so every column added here is `NOT NULL` where it should be
rather than nullable-for-migration-convenience.

---

## 1. What the table has today

```sql
id, workspace_id, research_session_id,
source_id, source_reference, acquisition_method, content_hash, parent_record_id,
payload_ref, content_language,
collected_at, expires_at, created_at,
UNIQUE (workspace_id, source_id, content_hash)
```

Tenancy, retention and exact-duplicate detection are all already correct. RLS is
enabled and forced (migration 0003), `expires_at` is `NOT NULL` so a record
cannot outlive a retention policy by omission, and the unique constraint gives
content-hash deduplication per `data-principles.md` §6.

---

## 2. Requirement by requirement

| Requirement | Column today | Verdict |
|---|---|---|
| Tenant scoping | `workspace_id` + RLS | **covered** |
| Session linkage | `research_session_id` | **covered** |
| Source identity | `source_id` FK to the registry | **covered** |
| Retrieval time | `collected_at` | **covered** |
| Retention | `expires_at NOT NULL` | **covered** |
| Exact-duplicate detection | `content_hash` + unique | **covered**, see §3 |
| Derivative linkage | `parent_record_id` | **covered** |
| Acquisition method | `acquisition_method` | **covered** |
| Where the payload lives | `payload_ref NOT NULL` | **partial**, see §4 |
| **Source-observation identity** | — | **GAP 1** |
| **Event time** | — | **GAP 2** |
| **Provenance beyond source and time** | — | **GAP 3** |
| **Which collector produced it** | — | **GAP 4** |

### GAP 1 — a logical observation has no identity

§23 and §24 require the system to distinguish *the same observation retrieved
again unchanged* from *an upstream revision of that observation*. Economic data
is revised; a 2020 GDP figure published today is not necessarily the one
published last year, and both are true statements about what the source said
when.

With only `content_hash`, a revision produces a row that is unrelated to the row
it revises. Nothing links them, so the question "what has this source said about
FR GDP for 2020, and when did it change" cannot be asked. `parent_record_id`
exists but means *derivative of*, which is a different relationship: a revision
is not derived from its predecessor, it replaces it.

**Needs:** a stable key over the source facts that identify the observation
(source, resource, indicator, geography, period) and specifically **not** over
its value or its retrieval time — plus a way to mark which row is current.

### GAP 2 — no event time

`data-principles.md` §9 is unambiguous: prefer event time over ingestion time,
because "trend analysis computed on ingestion timestamps produces artifacts that
look exactly like real market movements — and once the ingestion-time column is
the only one you kept, it cannot be recovered."

`normalized_records` has `observed_at`. `raw_records` does not, so the raw layer
would keep only the time we fetched. For an indicator series the observation
period *is* the event time and is present in every response; discarding it at the
raw layer and recovering it at normalization would mean the raw record could not
be audited on its own.

### GAP 3 — provenance is not answerable

§19 lists what an analyst must be able to establish without inferring anything
from a URL string. Of fourteen items, the table can answer four. Missing:
access profile, review version, condition/authorization snapshot, resource and
dataset identity, indicator, geography, licence, content origin, correlation id,
and request/page identity.

`source_reference` is a single text field. Packing ten facts into it would be
exactly the "infer provenance from a URL string" the section forbids.

### GAP 4 — no collector attribution

§50 requires that a record can be traced to the implementation that produced it,
so that a future collector change does not make old records unauditable. There is
no column for it, and no convention that would survive a second collector.

---

## 3. What turned out NOT to be a gap

**`UNIQUE (workspace_id, source_id, content_hash)` is exactly right**, and the
first design considered here replaced it, which would have been a mistake.

The fingerprint is computed over the canonical payload, which *includes* the
observation's identifying facts. So:

- the same observation with the same value produces the same hash → the
  constraint rejects the insert, and the retrieval is recorded as a re-sighting
  rather than a second row. That is idempotency (§23) with no extra machinery;
- a revised value produces a different hash → the insert succeeds, and the new
  row is linked to the old one by the observation key from GAP 1. That is
  revision (§24);
- two genuinely different observations cannot collide, because their identifying
  facts are inside the hashed payload.

Adding a second unique constraint over the observation key would have **broken**
revisions: it would have rejected the very insert that records one.

**`payload_ref` is not a gap either**, but it is incomplete on its own. It names
where the payload lives, and object storage (D-10) is undecided and
unimplemented. For an indicator observation the payload is a few hundred bytes,
so an inline column is proportionate, and `payload_ref` keeps its meaning by
recording that the payload is inline rather than pointing at a store that does
not exist.

---

## 4. Proposed change

Ten columns on `acquisition.raw_records`, forward-only, no other table touched.

| Column | Type | Closes |
|---|---|---|
| `observation_key` | `TEXT NOT NULL` | GAP 1 |
| `superseded_at` | `TIMESTAMPTZ` | GAP 1 |
| `last_seen_at` | `TIMESTAMPTZ NOT NULL` | GAP 1 — re-sightings without new rows |
| `observed_at` | `TIMESTAMPTZ` | GAP 2 |
| `provenance` | `JSONB NOT NULL` | GAP 3 |
| `review_version` | `INTEGER NOT NULL` | GAP 3 — the audit question people actually ask |
| `correlation_id` | `TEXT NOT NULL` | GAP 3 |
| `collector_id` | `TEXT NOT NULL` | GAP 4 |
| `collector_version` | `TEXT NOT NULL` | GAP 4 |
| `payload` | `JSONB` | §18, and see §3 |

Plus an index on `(workspace_id, source_id, observation_key, collected_at DESC)`,
which is the access path for "the history of this observation".

### Why `provenance` is JSONB and the other four are columns

The four promoted to columns — review version, correlation id, collector id and
version — are the ones an auditor filters *by*: "which records did collector
1.0.0 write", "which records rest on review version 2", "what did correlation
`abc` produce". Filtering on JSONB for those would work and would be slower and
uglier to read.

Everything else in §19 is read *with* a record rather than searched across, and
differs per source: an indicator id and a geography mean nothing for a forum
collector. Promoting them now would bake one source's shape into a table that
five more sources have to share. Mission 1.6 owns normalization and can promote
what it actually queries.

### Why not a separate provenance table

Considered and rejected. A raw record without its provenance is not a usable
record, so the two would always be written and read together, and the join would
buy nothing but a way for them to come apart. The composite-FK tenancy work in
Mission 1.2 also means a second tenant table is not free.

---

## 5. What deliberately does not change

- **No change to `normalized_records`.** Mission 1.6 owns normalization; §36 is
  explicit that parsing a response into raw records is not normalization.
- **No change to the unique constraint.** §3 explains why it is already correct.
- **No change to RLS.** The policies on `raw_records` are unchanged, and the new
  columns are inside the same row and therefore inside the same policy.
- **No new enum in the database for the error taxonomy.** Acquisition errors are
  a runtime result, not stored state; nothing persists one.
