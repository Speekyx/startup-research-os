# Signal Model Gap Analysis V1

**Status:** Written **before** any persistence change, per Mission 1.11 §32.
**Date:** 2026-08-30 (Sprint 1 / Mission 1.11)
**Compares:** the Signal contract proposed in
[`signal-contract-v1.md`](signal-contract-v1.md) against `nlp.signals` as
migration 0001 created it and as it stands today.
**Related:** [`signal-taxonomy-v1.md`](signal-taxonomy-v1.md),
[`signal-temporal-semantics-v1.md`](signal-temporal-semantics-v1.md),
[ADR-020](../architecture/adr/ADR-020-signal-derivation-model.md).

---

## 0. Method, and why the table was not trusted

`nlp.signals` has existed since Mission 0.1. Mission 1.11 §31 says not to assume
its shape is correct merely because it exists, so it was audited against the
contract rather than the contract being fitted to it.

The audit is cheap and the finding is unambiguous: **the table is empty, nothing
in the repository writes to it, and nothing reads it.** The only references are
three test modules asserting it is empty and one RLS test listing it as tenant
data. That is the position `scoring.evidence` was in at Mission 1.2, and
migration 0005 said the thing worth repeating here — this is the cheapest a
correction will ever be.

```text
nlp.signals                     0 rows
writers in the repository       none
readers in the repository       none
```

---

## 1. The table as it stands

```sql
CREATE TABLE nlp.signals (
    id                    UUID PRIMARY KEY,
    workspace_id          UUID NOT NULL REFERENCES core.workspaces (id),
    normalized_record_id  UUID REFERENCES acquisition.normalized_records (id) ON DELETE SET NULL,
    research_session_id   UUID REFERENCES research.research_sessions (id) ON DELETE SET NULL,
    signal_family         TEXT NOT NULL,        -- CHECK IN ('PAIN','DESIRE','BEHAVIORAL','MARKET')
    signal_type_registry  TEXT NOT NULL DEFAULT 'demand_signal_type',
    signal_type_id        TEXT NOT NULL,
    value                 DOUBLE PRECISION,     -- CHECK BETWEEN 0 AND 1
    confidence            DOUBLE PRECISION,     -- CHECK BETWEEN 0 AND 1
    model_version         TEXT,
    prompt_version        TEXT,
    extraction_method     TEXT NOT NULL,
    observed_at           TIMESTAMPTZ,
    collected_at          TIMESTAMPTZ NOT NULL,
    expires_at            TIMESTAMPTZ NOT NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Read as a design rather than as a list of columns, it encodes three assumptions,
all of them made before any source existed:

1. **A signal comes from exactly one normalized record.** One nullable
   `normalized_record_id`.
2. **A signal is a demand signal.** The family CHECK is Ontology V2 §3.6's
   closed demand taxonomy.
3. **A signal is produced by a language model.** `model_version`,
   `prompt_version` and a mandatory `extraction_method` are the only identity a
   producer has; there is no extractor id and no extractor version.

Every one of the three is false for the two sources that now exist.

---

## 2. The contract this is measured against, in one page

Full text in [`signal-contract-v1.md`](signal-contract-v1.md). The requirements
that bear on storage:

| # | Requirement |
|---|---|
| R-1 | A Signal derives from **two or more distinct source observations**. One observation cannot be a Signal (contract §3) |
| R-2 | Inputs are identified by `observation_key`, and two normalized rows sharing one may not both count (contract §9) |
| R-3 | Every contributing and every **excluded** input is recorded, machine-readably, with the quality it had |
| R-4 | A derivation declares the canonical facts it requires; an input withholding one is excluded, and a derivation with none left is **refused rather than stored** |
| R-5 | Magnitude is an **exact decimal in a stated kind and unit state** — never a unit-interval strength, never a float |
| R-6 | `derivation_confidence` is `[0,1]` and is about the derivation, not about the phenomenon |
| R-7 | Direction is about **change only**; sentiment is not modelled |
| R-8 | Scope states the dimensions the inputs agree on and **omits the key** for dimensions no input carries |
| R-9 | The temporal window declares a **basis**; an event time exists only under `COMPARABLE_INSTANTS` |
| R-10 | Identity is deterministic over workspace, type, extractor, schema, ordered inputs, parameters and window |
| R-11 | Parameters are serialised, ordered and fingerprinted |
| R-12 | Extractor id and version are mandatory; model and prompt versions belong only to a model-derived extractor |
| R-13 | Lineage reaches the raw records and the source ids, so Evidence Aggregation can decide independence later |
| R-14 | Tenant isolation is enforced by composite foreign keys, not by convention |

---

## 3. Gaps

Classification is Mission 1.11 §32's: **domain-model only** (a rule that lives
in code and documents), **contract change** (`domain.v1.json`, hence both
generated surfaces), **database migration**, **future extractor concern** (real
but not this mission's).

### GAP-1 — a signal cannot have more than one input

**Class: database migration.**

`normalized_record_id` is a single nullable column. R-1 makes a multi-input
derivation the *only* kind of Signal V1 recognises, so the table cannot store
one valid Signal. Not a degradation — a total block.

`ON DELETE SET NULL` compounds it: deleting one normalized record would leave a
Signal claiming to be derived from nothing, silently, with no state saying so.
Lineage that can be nulled is not lineage.

**Resolution.** A child table `nlp.signal_inputs`, one row per input, carrying
its role and — where it was set aside — why.

### GAP-2 — the family column classifies demand, and V1 signals are not about demand

**Class: contract change + database migration.**

`CHECK (signal_family IN ('PAIN','DESIRE','BEHAVIORAL','MARKET'))` is the
Opportunity ontology's demand taxonomy. Neither derivation the two real sources
support is a demand signal:

- a contrast between two GDELT term frequencies in one bucket says how often two
  tokens occurred in text GDELT processed. Mission 1.11 §25 lists what else that
  can be — a news event, a crisis, a celebrity, weather, politics, a disaster, a
  sports fixture;
- a change in a World Bank population figure between two years is a demographic
  measurement.

Forcing either into `MARKET` would assert a demand reading the data does not
carry, in the one field a consumer branches on. Full argument in
[`signal-taxonomy-v1.md`](signal-taxonomy-v1.md) §2.

**Resolution.** The column is renamed `quantity_family` and re-CHECKed against a
new closed enum saying what kind of quantity the signal is about. **Ontology V2
§3.6 is not changed**: the demand families remain exactly what they are, and
what stops being true is the claim that every row of this table carries one.

### GAP-3 — `value DOUBLE PRECISION CHECK BETWEEN 0 AND 1` cannot hold a magnitude

**Class: database migration.** The single worst column in the table, for two
independent reasons.

**It is bounded to the unit interval.** A frequency change from 55 to 81 does
not fit. Neither does a population delta. The bound presumes every signal
magnitude is a normalised strength — the design Mission 1.11 §8 and §30 both
reject, because a GDELT term frequency and a World Bank population figure are
not measurements of comparable things and putting them on one scale would
manufacture a comparison nobody can defend.

**It is a float.** The normalization layer bans floats for source numbers
(`normalized-record-v1.md` §13) because a value that has been through IEEE-754
may differ from what the source sent. A derivation *over* those exact decimals
that immediately rounded its result through a float would give the guarantee
back at the first arithmetic operation.

**Resolution.** `magnitude NUMERIC NOT NULL`, beside `magnitude_kind`,
`magnitude_unit` and `magnitude_unit_state`. **No 0–100 strength is introduced**,
because no cross-signal comparison justifies one (contract §5).

### GAP-4 — there is no extractor identity

**Class: contract change + database migration.**

`model_version`, `prompt_version` and `extraction_method` are a language model's
provenance. A deterministic extractor has no model and no prompt, and under the
current schema it would identify itself by writing a string into
`extraction_method` — free text, in the field that decides whether a result is
reproducible.

Worse, the shape *invites* the design Mission 1.11 §23 forbids: a table whose
only producer identity is a model version reads as a table of model outputs.

**Resolution.** `extractor_id` and `extractor_version` become mandatory;
`signal_schema_id` and `signal_schema_version` join them, versioned
independently for the reason `normalized-record-v1.md` §21 gives. A closed
`derivation_kind` (`DETERMINISTIC | MODEL_DERIVED`) governs the model columns
with a CHECK: a deterministic signal may not carry a model version, and a
model-derived one may not omit it. §23's rule becomes a constraint rather than a
sentence.

### GAP-5 — there is no derivation identity, so nothing is idempotent

**Class: database migration.**

The primary key is an opaque UUID and there is no unique constraint. Re-running
the same derivation over the same inputs with the same parameters inserts a
second row, and the two are indistinguishable from two independent findings —
which is exactly the shape Evidence Aggregation must never be handed
(`evidence-aggregation-framework-v1.md` §7).

**Resolution.** `derivation_fingerprint TEXT NOT NULL` with
`UNIQUE (workspace_id, derivation_fingerprint)`, and a UUIDv5 row id over the
same material, so a re-run converges on the row that exists. Same mechanism as
`acquisition.normalized_records`, one layer up.

### GAP-6 — derivation parameters have nowhere to live

**Class: database migration.**

A window size, a comparison strategy, a minimum observation count. Mission 1.11
§29 is explicit that a signal is not reproducible if these are hidden defaults,
and there is no column for them.

**Resolution.** `parameters JSONB NOT NULL` plus `parameter_fingerprint TEXT NOT
NULL` over its canonical serialisation. The fingerprint enters the derivation
identity; the parameters stay readable beside it.

### GAP-7 — scope has nowhere to live

**Class: database migration.**

A Signal must say what it is about. The table carries no term, no metric, no
geography, no language and no source set.

**Resolution.** `scope JSONB NOT NULL`, following the `payload` precedent, with
the normalization layer's rule about absence carried up: a dimension no input
carries has **no key at all**, never a null. A GDELT lexical signal legitimately
has no geography (Mission 1.11 §15), and that is what its scope looks like.

### GAP-8 — temporal semantics collapse to one nullable instant

**Class: contract change + database migration.**

`observed_at TIMESTAMPTZ` is the only temporal field. It cannot express which of
two periods a comparison ran between, at what resolution, over how many
observations — and, critically, it cannot express *that the inputs have no
comparable instant at all*, which is the state every GDELT observation is in
while H-29 is open.

A `TIMESTAMPTZ` column offers exactly one way to store a GDELT bucket: invent an
offset. That is the invention `NormalizedTimezoneState` exists to prevent one
layer down, and the Signal layer must not undo it.

**Resolution.** `temporal_window JSONB NOT NULL` carrying a closed
`SignalTemporalBasis`, the exact source period labels, the resolution and the
observation count, plus a CHECK that leaves `observed_at` **NULL unless the
basis is `COMPARABLE_INSTANTS`**. The database then refuses a GDELT signal with
an event time. Reasoning in
[`signal-temporal-semantics-v1.md`](signal-temporal-semantics-v1.md).

### GAP-9 — quality has no interaction model

**Class: domain-model only.**

Nothing in the table relates a Signal to the `NormalizedRecordQuality` of the
records behind it. Mission 1.11 §10 requires more than a filter: `INVALID` must
not be derivable from, and `PARTIAL` must **not** automatically mean unusable —
what matters is whether the *specific* missing fact matters to the *specific*
derivation.

**Resolution.** `SignalRequiredFact`, a closed vocabulary, each value declaring
which `NormalizationQualityReason` values withhold it. A derivation states what
it requires; the model computes what each input withholds. **No column**: the
requirement belongs to the extractor specification, and the outcome is already
recorded per input in `nlp.signal_inputs`.

### GAP-10 — there is no way to record a refusal, and none should be added here

**Class: domain-model only, and deliberately not a migration.**

Mission 1.11 §27 asks whether a blocked derivation should produce an artifact.
It should not produce a **Signal**. A row in a table of signals says a signal
exists; a row that means "no signal exists" is a misleading signal, and the
brief's own preference is not to create one.

**Resolution.** `SignalDerivationRefusal` — a returned value object with a closed
reason code, never a `nlp.signals` row, and no lifecycle enum on the Signal
itself. Where a refusal should be *logged* is a derivation-run concern for
Mission 1.11.1, not a shape the Signal table needs.

### GAP-11 — `research_session_id` is lineage but is shaped like ownership

**Class: domain-model only.**

The column is right; what was missing was a rule. Mission 1.11 §39 asks whether
the same observations may contribute to signals across sessions. If the session
entered the derivation identity, two sessions deriving the same thing would
produce two rows — which the aggregation layer would be entitled to read as two
findings.

**Resolution.** The session is **lineage, never identity**. Ontology V2 §12
already settled the same question for Opportunity, and Mission 1.2 applied it to
Claim; `research.claim_session_observations` is the existing shape for
per-session attribution of a shared artifact, available unchanged if it is ever
needed.

### GAP-12 — `scoring.evidence.signal_id` is not tenant-safe

**Class: database migration.** Found while auditing the Evidence boundary, and
pre-existing.

```sql
signal_id UUID REFERENCES nlp.signals (id) ON DELETE SET NULL
```

A single-column reference. Migration 0005 made `claim_id` and
`independence_group_id` composite for precisely this reason — a workspace A
evidence row must not be able to name a workspace B object — and left this one
as it was, because no signal existed to point at.

**Resolution.** `UNIQUE (workspace_id, id)` on `nlp.signals`, and a composite
`FOREIGN KEY (workspace_id, signal_id)` with a column-specific
`ON DELETE SET NULL (signal_id)`. The single-column FK stays: it carries the
delete behaviour, and removing a guard because a stronger one exists is a
regression (ADR-012).

`acquisition.normalized_records` needs the same `UNIQUE (workspace_id, id)` so
`nlp.signal_inputs` can reference it compositely. `raw_records` already has one,
added by migration 0009 for the same reason.

### GAP-13 — the default signal type registry has no entries any migration writes

**Class: database migration.** Pre-existing, and it makes the table unwritable.

`signal_type_registry` defaults to `demand_signal_type`, and
`FOREIGN KEY (signal_type_registry, signal_type_id)` points at
`registry.registry_entries`. No migration inserts a single `demand_signal_type`
row. The only two live in `infrastructure/db/seed/0002_registry_seed.sql`, which
is development-only and runs after every migration.

So `nlp.signals` accepts an insert on a developer's seeded machine and rejects
every insert on the empty database CI and any real deployment start from. This
is the exact failure `validate_schema.py`'s last check was added for, in Mission
1.7 — that check catches a migration mapping to a seeded entry, and does not
catch a table whose runtime writes depend on one.

**Resolution.** The `signal_type` registry entries this mission registers are
written by the migration. The default becomes `signal_type`.

### GAP-14 — the contract does not list every registry the database has

**Class: contract change.** Pre-existing.

`REGISTRY_NAMES` omits `signal_family`, which migration 0010 created and
populated with sixteen entries (ADR-017). The contract is meant to be the place
a registry name is declared once for both language surfaces.

**Resolution.** `signal_family` and the new `signal_type` are both added. They
are different registries with confusingly similar names, which is
[`signal-taxonomy-v1.md`](signal-taxonomy-v1.md) §1's subject.

### GAP-15 — `collected_at` is not a fact about a derived artifact

**Class: database migration.**

A Signal is not collected. Its inputs were, at various times, from possibly
several sources; a single `collected_at` on the derived row has no referent.
`acquisition.normalized_records` already established the pattern — it anchors
its retention CHECK on `normalized_at`, the time *that* representation was
produced.

**Resolution.** `collected_at` becomes `derived_at`, with
`CHECK (expires_at > derived_at)`. `validate_schema.py`'s retention check learns
one start column per table instead of assuming `collected_at`.

### GAP-16 — nothing states which sources are behind a signal

**Class: database migration.**

Mission 1.11 §22 forbids computing independence at this layer and requires
preserving enough source and group information for Evidence Aggregation to
decide later. The current table reaches one normalized record and stops; the raw
records and the source ids behind it are two joins away, across a table that
expires eleven months sooner.

**Resolution.** `nlp.signal_inputs` denormalizes `source_id`, `raw_record_id`,
`observation_key`, `record_kind_id` and the input's quality, for the reason
migration 0009 denormalized provenance onto the normalized record: the thing you
need at audit time outlives the row you would have joined to.

**No independence state, no group id and no reliability appears on a Signal.**
Those are Evidence's fields and mean something Evidence decides.

---

## 4. What is already right, and stays

| | |
|---|---|
| `workspace_id UUID NOT NULL` + RLS `ENABLE` and `FORCE` | The tenant boundary. Unchanged, and extended to the new child table |
| `signal_type` as a **registry reference** rather than a CHECK list | Ontology V2 §14.3. The original design got this right; only the registry it defaults to was wrong |
| `confidence` on `[0,1]` with a CHECK | The naming rule holds (`scoring-framework-v1.1.md` §4.1). It is renamed for precision, not rescaled |
| `expires_at TIMESTAMPTZ NOT NULL` | `signal` is a tier-2.2 artifact — twelve months, the same window as a normalized record |
| `model_version`, `prompt_version` | Right fields, wrong obligation. They become the model-derived branch of a CHECK rather than the only producer identity |
| `research_session_id` nullable, `ON DELETE SET NULL` | Correct. A signal outlives the session that first derived it |

---

## 5. What this analysis does not decide

- **D-08 is not solved.** Two normalized rows can represent one observation under
  two normalizer versions. The contract refuses a derivation whose inputs
  contain both (`AMBIGUOUS_OBSERVATION_LINEAGE`) rather than choosing between
  them. Failing closed on the undecided case is not the same as deciding it.
- **D-03 is not touched.** No aggregation result is stored, no weight, no
  reliability, no independence judgement. `derivation_confidence` is not an
  `EvidenceScore` input and is not multiplied by anything.
- **D-12 is not touched.** Nothing here reads or writes a vector, and the Signal
  model has no embedding dependency.
- **H-29 and H-30 are not answered.** They are made *expressible*: the contract
  can state which derivations they block and which they do not.
- **No extractor is specified.** Minimum observation counts, window sizes and
  comparison strategies are extractor specification (Mission 1.11 §28), and
  picking production thresholds is out of scope by §28's own words.
- **`nlp.embedding_provenance.normalized_record_id`** carries the same
  single-column FK weakness as GAP-12. It is left alone: D-12 is open, nothing
  writes it, and widening this mission to a table it does not touch would be the
  change nobody asked for.
