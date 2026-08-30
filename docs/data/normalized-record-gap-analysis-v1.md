# NormalizedRecord Gap Analysis V1

**Status:** Analysis record. Produced by Mission 1.6 §4 **before** the schema was
changed, so migration `0009` can be checked against what was missing rather than
against what was convenient to add.
**Date:** 2026-08-30
**Reads:** `acquisition.normalized_records` as migration `0001_foundation` defines
it, against the requirements of Mission 1.6 §5–§31.
**Related:** [`raw-record-gap-analysis-v1.md`](raw-record-gap-analysis-v1.md),
[`normalized-record-v1.md`](normalized-record-v1.md),
[`world-bank-collector-v1.md`](world-bank-collector-v1.md),
[`data-principles.md`](data-principles.md),
[`data-retention-policy-v1.md`](data-retention-policy-v1.md).

---

## 0. Why this document exists

`acquisition.normalized_records` was designed in Mission 0.1 against a
specification, with no normalizer to test it and no raw record to normalize.
Mission 1.6 is the first mission that writes to it.

§4 says to audit every existing field before touching the schema. This is that
audit. It follows the convention Mission 1.3 set and Mission 1.5 repeated:
**write down what is missing before deciding what to add**, so the migration can
be reviewed against a requirement rather than against a preference.

The table holds **zero rows**. Every column added here is therefore `NOT NULL`
where it should be, rather than nullable-for-migration-convenience — the same
freedom Mission 1.5 had, and the last mission that will have it for this table.

---

## 1. What the table has today

```sql
CREATE TABLE acquisition.normalized_records (
    id                     UUID PRIMARY KEY,
    workspace_id           UUID NOT NULL REFERENCES core.workspaces (id),
    raw_record_id          UUID NOT NULL REFERENCES acquisition.raw_records (id),
    research_session_id    UUID      REFERENCES research.research_sessions (id),
    source_id              TEXT NOT NULL REFERENCES registry.sources (id),
    extraction_method      TEXT NOT NULL,
    transformation_version TEXT NOT NULL,
    content_hash           TEXT NOT NULL,
    content_language       TEXT,
    observed_at            TIMESTAMPTZ,
    collected_at           TIMESTAMPTZ NOT NULL,
    expires_at             TIMESTAMPTZ NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Row-level security is enabled and forced (migration `0003`), and both retention
columns are `NOT NULL`, so a normalized record cannot outlive a retention policy
by omission. Those two properties are the foundation the rest of this rests on
and neither is changed.

---

## 2. Field-by-field classification (§4)

The five verdicts §4 asks for. "Ambiguous" is used where the column can carry the
requirement but its *meaning* was never written down — which is a real finding,
because an ambiguous column gets two meanings the moment two people use it.

| # | Column | Verdict | Detail |
|---|---|---|---|
| 1 | `id` | **usable as-is** | Its *derivation* becomes deterministic (§6), which is a code decision, not a schema one |
| 2 | `workspace_id` | **usable as-is** | Tenancy + RLS already correct (§30) |
| 3 | `raw_record_id` | **additive change required** | The column is right; its FK does **not** carry `workspace_id`, so it cannot make a cross-tenant reference structurally impossible (§31). See GAP 8 |
| 4 | `research_session_id` | **additive change required** | Same as above, and for the same reason |
| 5 | `source_id` | **usable as-is** | FK to the global registry |
| 6 | `extraction_method` | **ambiguous** | Nothing records what values it may take or what question it answers. Resolved by giving it a documented vocabulary rather than a new column — see §3 |
| 7 | `transformation_version` | **incompatible** | One column cannot carry two independently-evolving versions (§21). See GAP 3 |
| 8 | `content_hash` | **usable as-is** | Becomes the normalized semantic fingerprint (§22) |
| 9 | `content_language` | **usable as-is** | `NULL` for a numeric observation, which is the honest answer, not a gap ("language where applicable", §5) |
| 10 | `observed_at` | **usable as-is** | Event time. Not *sufficient* on its own — see GAP 6 — but the column itself is right |
| 11 | `collected_at` | **ambiguous** | Two readings: when the source observation was collected, or when normalization ran. Resolved in §3, and the second reading needs its own column (GAP 6) |
| 12 | `expires_at` | **usable as-is** | Written at normalization time from the resolved **normalized** window (§10) |
| 13 | `created_at` | **usable as-is** | Row-insertion time. Deliberately not the same fact as `normalized_at` |

**Deferred, and named so it is not mistaken for an oversight:**

| Item | Why deferred |
|---|---|
| A `NUMERIC` projection of the observed value | Unnecessary. The canonical payload is `JSONB`, and `(payload -> 'observation' ->> 'value')::numeric` is an exact, lossless query path. A second column holding the same number is drift waiting to happen, and nothing aggregates these yet |
| Re-normalization *policy* — which of several versions downstream should read | **D-08**, and §49 is explicit that Mission 1.6 must not resolve it. The schema makes coexistence possible and takes no position on selection |
| Object storage for large canonical payloads | **D-10**, unchanged since Mission 1.5. A numeric observation is a few hundred bytes |
| Personal-data / language columns beyond `content_language` | No adapter produces text yet. Adding them now would bake a shape no normalizer has |

---

## 3. The two ambiguous columns, resolved

Neither needs a new column. Both need a written-down meaning, which is what was
actually missing.

**`extraction_method`** answers *how the canonical representation was produced*.
It takes a small closed vocabulary; Mission 1.6 defines one value,
`DETERMINISTIC_ADAPTER`, and that is not a placeholder — it is the property §18
and §41 require, recorded on the row. A future LLM-assisted or ML-assisted
normalizer would carry a different value, and a reader filtering for
"transformations no model influenced" gets a correct answer without knowing which
normalizers existed when.

**`collected_at`** means *when the source observation was collected* — inherited
verbatim from the raw record. It is the same fact the column of that name carries
on `raw_records` and on `nlp.signals`, and making it mean something else on one
table in the middle of the chain is how a lineage question gets two answers.
*When normalization ran* is a different fact and gets `normalized_at` (GAP 6).

---

## 4. The gaps

Nine requirements the table cannot represent at all.

### GAP 1 — there is nowhere to put the canonical representation

The largest gap, and the one that makes the table unusable as it stands: there
is **no payload column**. `content_hash` fingerprints content the table has no
column for.

A NormalizedRecord's whole purpose is to carry the canonical form of one source
observation (§2, §12). Without it the row is metadata about a transformation
whose output was discarded, and every downstream stage would have to re-run the
normalizer against the raw record — which expires in 30 days while the normalized
record lives 12 months (`data-retention-policy-v1.md` §2.1, §2.2).

**Needs:** a canonical payload column, and a record-kind discriminator saying
which canonical shape it holds (§11).

### GAP 2 — no record kind

§11 requires a minimal extensible taxonomy of canonical record kinds, with a
clean extension mechanism. Nothing in the table says whether a payload is a
numeric observation, a document or a discussion post.

`extraction_method` and `transformation_version` describe *how* the row was made,
never *what shape it is*. A consumer cannot tell whether a payload is safe to
read as a measurement.

**Needs:** a registry reference, not a database enum. Ontology V2 §14.3 is
explicit that evolving taxonomies are rows; a `CHECK` list of record kinds would
require a migration for every future adapter, which is precisely the
migration-per-concept problem §14 exists to prevent. The pattern already exists
in this schema: `nlp.signals` references `registry.registry_entries` by
`(registry, id)` composite FK.

### GAP 3 — one version column for two independent versions

`transformation_version` is a single `TEXT NOT NULL`. §21 requires two versions
that **evolve independently**:

- the **normalizer implementation** version — a parsing fix that changes no
  canonical semantics;
- the **canonical normalized schema** version — a change to what the canonical
  representation *means*.

Packing both into one string makes every consumer parse it, which is the same
defect §8 names for URLs: *lineage must not require parsing a string*. Splitting
them later would mean rewriting whatever convention had accumulated.

There is also no `normalizer_id`. With one normalizer the version alone reads
unambiguously; with two it does not, and the records written in between become
unauditable — the identical argument Mission 1.5 §50 made for `collector_id`.

**Needs:** `normalizer_id`, `normalizer_version`, `normalization_schema_id`,
`normalization_schema_version`. `transformation_version` is **renamed** to
`normalizer_version` rather than duplicated: the table is empty, nothing reads
it, and two columns holding one fact drift apart. This is the one non-additive
change in migration `0009`, and §57 permits it exactly here — the existing
semantics are genuinely incompatible with §21, not merely inconvenient.

### GAP 4 — a normalized representation has no stable identity

§6 requires that repeated normalization of an unchanged RawRecord be idempotent,
and §23 requires that it not generate uncontrolled duplicate rows. The table has
a `PRIMARY KEY (id)` and **no unique constraint over anything meaningful**, so
running the normalizer twice inserts two rows and nothing notices.

§6 also requires three identities kept apart. The table can express one:

| Identity | Question | Column today |
|---|---|---|
| source observation | WHICH observation | — (GAP 5) |
| raw version | WHAT the source said, and when | `raw_record_id` ✔ |
| normalized representation | WHICH transformation of that | — |

**Needs:** a unique constraint over
`(workspace_id, raw_record_id, normalization_schema_version, normalizer_id, normalizer_version)`.

That single constraint delivers three requirements at once, which is why it is
the right one rather than a convenient one:

- **§23 idempotency** — re-running the same normalizer on the same raw record
  collides, so a duplicate Celery delivery updates instead of inserting;
- **§24 / §49 re-normalization** — a *different* normalizer or schema version
  does **not** collide, so representation A survives when B is written;
- **§7 / §48 revision** — a revised RawRecord is a different `raw_record_id`, so
  it does not collide either, and both normalized versions coexist.

A constraint over the *observation* instead would have rejected all three of the
inserts that record a revision, a re-normalization, or both. This is the same
trap Mission 1.5 §3 documented at the raw layer, one level up.

### GAP 5 — no observation key, and no revision marker

§7 and §48 require that a revised RawRecord be able to produce a revised
NormalizedRecord, with the earlier normalized representation left intact and
distinguishable.

Two rows related through `raw_record_id → raw_records.observation_key` are
joinable in principle, but:

- the raw record **expires after 30 days** while the normalized record lives 12
  months (`data-retention-policy-v1.md` §2.1, §2.2). After day 31 the join
  returns nothing and the lineage is gone — which §4 of that policy explicitly
  legislates against: *"provenance survives the content it describes"*;
- there is no column saying *this normalized representation is no longer the
  current one for its observation*, so "give me the latest normalized value for
  FR population 2020" cannot be answered at all.

**Needs:** `observation_key` denormalized onto the row, and `superseded_at`.

`superseded_at` records **an upstream fact** — the raw record this represents was
superseded by a later retrieval — and is set only within one
`(schema version, normalizer id, normalizer version)` lineage. Crossing lineages
would make writing schema v2 quietly retire schema v1, which is exactly the
"policy selecting which one downstream must use" §49 forbids inventing.

### GAP 6 — the lineage questions are not answerable

§8 lists nine questions every NormalizedRecord must answer. The table answers
four.

| §8 question | Column today |
|---|---|
| Which RawRecord produced me? | `raw_record_id` ✔ |
| Which source produced that RawRecord? | `source_id` ✔ |
| When was the source observation made? | `observed_at` ✔ |
| When was it collected? | `collected_at` ✔ (once §3 fixes its meaning) |
| Which collector / version produced it? | **missing** |
| Which normalizer / version transformed it? | **missing** (GAP 3) |
| Which source review authorized acquisition? | **missing** |
| Which conditions were satisfied? | **missing** |
| Which attribution obligations follow me? | **missing** (GAP 7) |
| When was it normalized? | **missing** |

The first four missing items could be read from `raw_records.provenance` —
**until day 31**, when the raw record expires and the answers disappear. A
derived record whose provenance evaporates is precisely what
`data-retention-policy-v1.md` §4 was written to prevent.

**Needs:** `normalized_at`, `correlation_id`, `collector_id`,
`collector_version`, `review_version` as columns, and a `provenance` JSONB for
the rest.

The split follows Mission 1.5's rule exactly, because the rule turned out to be
right: **promote what an auditor filters *by*, keep as JSONB what is read *with*
a record.** "Which records did normalizer 1.1 write", "which rest on review
version 2", "what did correlation `abc` produce" are filters. The condition
snapshot, the licence and the dataset family are read alongside a row and differ
per source, so promoting them would bake one adapter's shape into a table five
more adapters have to share.

### GAP 7 — attribution has nowhere to survive to

§9 and §46 are unconditional: an attribution obligation on a RawRecord must
still be on the NormalizedRecord, and there must be **no API through which a
normalizer can drop it**.

Today there is no column it could occupy. Normalizing a CC-BY-4.0 World Bank
observation would produce a row with no credit attached, and the obligation would
survive only as long as the raw record — 30 days — after which the derived data
is unattributed and there is no way to discover that it should not be.

**Needs:** the rendered attribution inside `provenance`, populated from the raw
record's own provenance and **never from a parameter**. Enforced by construction:
the builder has no attribution argument, and refuses a raw record that carries
none.

### GAP 8 — a cross-tenant reference is structurally possible

§31 asks for composite foreign keys carrying `workspace_id`, so that a
NormalizedRecord in workspace A referencing a RawRecord in workspace B is
impossible rather than merely checked for.

`normalized_records.raw_record_id` references `raw_records (id)` alone.
`raw_records` has `PRIMARY KEY (id)` and **no `UNIQUE (workspace_id, id)`**, so
the composite FK cannot even be declared yet. The same applies to
`research_session_id`, although `research_sessions` already gained
`UNIQUE (workspace_id, id)` in migration `0005`.

RLS and the repository filter would both have to fail for this to be exploited,
which is the argument for it being a *third* layer rather than the first — but
ADR-012's own reasoning applies: layers are added because the previous one can be
forgotten, and a structural impossibility cannot be forgotten.

**Needs:** `UNIQUE (workspace_id, id)` on `raw_records`, then composite FKs on
`(workspace_id, raw_record_id)` and `(workspace_id, research_session_id)`.

Mission 1.2 established this pattern for claims and evidence (migration `0005`),
so this is applying a settled convention, not inventing one.

### GAP 9 — quality and its reasons cannot be recorded

§25 and §26 require a structural quality state and, for anything below `VALID`,
the reasons. §26 also forbids discarding a problematic RawRecord: *"a failed
normalization must remain auditable"*.

With no column for either, the only ways to handle a record that cannot be fully
represented are to drop it — losing the audit trail — or to store it looking
exactly like a clean one, which is worse.

**Needs:** `quality` (closed enum, `TEXT` + `CHECK` per ADR-008) and
`quality_reasons` `JSONB` holding a list of reason codes with detail.

Not a confidence score, and not a numeric weight. §25 is explicit, and the
distinction matters: quality here is *structural completeness*, which is decided
by looking at the record. Reliability is an epistemic judgment that belongs to
the evidence model and would be a different number with a different meaning.

---

## 5. What turned out NOT to be a gap

**`content_hash` is exactly the right column, and its semantics change.** At the
raw layer it fingerprints *what the source said*. Here it fingerprints *what the
canonical representation is* — and deliberately **not** the schema version,
normalizer version, normalization timestamp, correlation id or job id (§22).

That looked wrong at first and is right: if normalizer 1.0 and 1.1 produce byte-
identical canonical content, their fingerprints *should* match, because the
content is the same. Identity is what distinguishes them (GAP 4), and that is a
different question — the same separation Mission 1.5 §7 drew between
`observation_key` and `content_hash`, and folding the versions into the hash
would destroy the ability to notice that a normalizer upgrade changed nothing.

**RLS needs no change.** Every column added here lives in the same row and is
therefore already inside the existing policy — the same conclusion Mission 1.5
reached for `raw_records`, and for the same reason.

**Retention needs no new mechanism.** `resolve_retention` already returns
`normalized_days` alongside `raw_days`, already takes the stricter of baseline
and override in that direction only, and has done since Mission 1.0. Mission 1.6
consumes it; nothing about it changes. The gap was never the resolver — it was
that nothing called it for the normalized tier.

**The unique constraint on `raw_records` stays untouched.** Migration `0009` adds
`UNIQUE (workspace_id, id)` *alongside* `UNIQUE (workspace_id, source_id, content_hash)`.
The second is what makes raw idempotency and revision work
(`raw-record-gap-analysis-v1.md` §3); replacing it would break both.

---

## 6. Proposed change

Fifteen columns on `acquisition.normalized_records`, one rename, one unique
constraint on `raw_records`, one registry seed. Forward-only, migration `0009`.

| Change | Closes |
|---|---|
| rename `transformation_version` → `normalizer_version` | GAP 3 |
| `normalizer_id TEXT NOT NULL` | GAP 3 |
| `normalization_schema_id TEXT NOT NULL` | GAP 3 |
| `normalization_schema_version INTEGER NOT NULL` | GAP 3 |
| `record_kind_registry TEXT NOT NULL DEFAULT 'normalization_record_kind'` | GAP 2 |
| `record_kind_id TEXT NOT NULL` + composite FK to `registry.registry_entries` | GAP 2 |
| `payload JSONB NOT NULL` | GAP 1 |
| `observation_key TEXT NOT NULL` | GAP 5 |
| `superseded_at TIMESTAMPTZ` | GAP 5 |
| `normalized_at TIMESTAMPTZ NOT NULL` | GAP 6 |
| `correlation_id TEXT NOT NULL` | GAP 6 |
| `collector_id TEXT NOT NULL` | GAP 6 |
| `collector_version TEXT NOT NULL` | GAP 6 |
| `review_version INTEGER NOT NULL` | GAP 6 |
| `provenance JSONB NOT NULL` | GAP 6, GAP 7 |
| `quality TEXT NOT NULL` + `CHECK` | GAP 9 |
| `quality_reasons JSONB NOT NULL DEFAULT '[]'` | GAP 9 |
| `UNIQUE (workspace_id, raw_record_id, normalization_schema_version, normalizer_id, normalizer_version)` | GAP 4 |
| `UNIQUE (workspace_id, id)` on `acquisition.raw_records` | GAP 8 |
| composite FKs on `(workspace_id, raw_record_id)` and `(workspace_id, research_session_id)` | GAP 8 |
| registry seed: `normalization_record_kind` / `numeric_observation` | GAP 2 |

Plus two indexes: `(workspace_id, source_id, observation_key, normalized_at DESC)`
— the access path for "every normalized representation of this observation" — and
`(workspace_id, correlation_id)`, which is how an operator debugs one job.

### Why `quality` is a closed enum and `record_kind` is a registry

They look alike and are governed differently, so the reason is written down here
rather than left to be re-derived.

`quality` has exactly three values and **code branches on all of them**: a
downstream stage must decide what to do with `PARTIAL`, and an unhandled fourth
value would be a bug rather than a gap. That is Ontology V2 §14.1's definition of
a closed enum, so it is `TEXT` + `CHECK`, and `validate_schema.py` compares the
`CHECK` list against the contract source of truth.

`record_kind` is open-ended by construction: every future adapter may bring one,
and §11 asks for "a clean extension mechanism". A `CHECK` list would need a
migration per adapter — the migration-per-concept problem §14 exists to prevent —
so it is a registry row, following `nlp.signals.signal_type_id` exactly.

---

## 7. What deliberately does not change

- **No change to `acquisition.raw_records` beyond one unique constraint.** §27:
  the raw layer records what the source returned, and normalization does not get
  to make it more convenient. No column is added, none is rewritten, and no
  payload is corrected.
- **No change to `nlp.signals` or `nlp.embedding_provenance`.** §42 and §43 put
  signal extraction and embeddings outside this mission. Their existing
  `normalized_record_id` FKs already point here and need nothing.
- **No change to `research.claims` or `scoring.evidence`.** §44.
- **No aggregation column anywhere.** D-03 stays blocked, and
  `validate_schema.py` fails the build if one appears.
- **No `NUMERIC` value column.** See §2, Deferred.
- **No re-normalization selection policy.** D-08, and §49 forbids resolving it.
