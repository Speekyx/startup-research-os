# ADR-020 — A Signal is a derivation, not a labelled observation

**Status:** Accepted
**Date:** 2026-08-30
**Mission:** Sprint 1 / Mission 1.11
**Supersedes:** nothing. Replaces the placeholder shape `nlp.signals` has
carried since Mission 0.1.
**Extends:** [ADR-008](ADR-008-postgresql-primary-store.md) (closed enums as
`TEXT` + `CHECK`, taxonomies as registry rows),
[ADR-009](ADR-009-contract-first-code-generation.md) (generated contracts),
[ADR-012](ADR-012-row-level-security.md) (two tenancy layers),
[ADR-019](ADR-019-lexical-frequency-observation.md) (canonical absences stated
rather than filled in).
**Related:** [`signal-contract-v1.md`](../../data/signal-contract-v1.md),
[`signal-model-gap-analysis-v1.md`](../../data/signal-model-gap-analysis-v1.md),
[`signal-taxonomy-v1.md`](../../data/signal-taxonomy-v1.md),
[`signal-temporal-semantics-v1.md`](../../data/signal-temporal-semantics-v1.md).

---

## Context

`nlp.signals` was created in Mission 0.1, before any source existed, and it
encodes three assumptions that the two sources which now exist all falsify:

| Assumption | Where it lives | Falsified by |
|---|---|---|
| A signal comes from exactly one normalized record | `normalized_record_id UUID` | Every derivation that says anything an observation does not already say |
| A signal is a demand signal | `CHECK (signal_family IN ('PAIN','DESIRE','BEHAVIORAL','MARKET'))` | A GDELT term count and a World Bank population figure, neither of which is evidence of demand |
| A signal is produced by a language model | `model_version`, `prompt_version`, and no extractor identity at all | The first extractors, which are arithmetic |

A fourth problem is arithmetic rather than architectural:
`value DOUBLE PRECISION CHECK (value BETWEEN 0 AND 1)` cannot hold a change from
55 to 81, and is a float in a system that parses source numbers with
`parse_float=Decimal` precisely so IEEE-754 never touches them.

The table is empty, nothing writes to it and nothing reads it. Migration 0005
made the same correction to `scoring.evidence` and said the thing worth
repeating: this is the cheapest it will ever be.

Four decisions follow. Each is hard to reverse once rows exist, which is why
they are recorded here rather than only in the contract.

---

## Decision 1 — a Signal requires at least two distinct source observations

A derivation whose output is a function of exactly one observation, and whose
assertion is recoverable from that observation's payload alone, is the
observation renamed. `LEXICAL_FREQUENCY_OBSERVED(climate, 55)` adds nothing to a
record that already says `climate` and `55`, and putting it in a table called
`signals` would make a reader believe a derivation happened.

A contrast needs something to contrast against, and there are exactly two
candidates: another observation, or a reviewed reference baseline. No baseline
exists, and inventing one is the pattern
`evidence-aggregation-framework-v1.md` §9 forbids by name.

**Distinctness is over `observation_key`, never over `normalized_record_id`.**
One observation can have several normalized rows — a revision, or a newer
normalizer version — and **D-08** has not decided which to read. Counting rows
would let a normalizer upgrade manufacture a contrast out of a single
observation. A derivation whose contributing inputs share an `observation_key`
is refused with `AMBIGUOUS_OBSERVATION_LINEAGE`: failing closed on the undecided
case, without deciding it.

### Cost accepted

A genuinely single-observation indication cannot be represented. If a reviewed
baseline is ever authorised — with a recorded basis, the way a geography map
entry has one — this rule is revisited by an ADR and not by an extractor
deciding for itself.

---

## Decision 2 — the Signal family classifies the quantity, not the demand

`quantity_family` is a new closed enum, `LEXICAL_FREQUENCY | MEASURED_SERIES`,
and it replaces the demand families on this table.

The demand taxonomy classifies demand. A contrast between two GDELT term
frequencies says how often two tokens occurred in text GDELT processed — which
may equally be a news event, a crisis, a celebrity, weather, politics, a
disaster or a sports fixture. A World Bank population delta is a demographic
measurement. Forcing either into `MARKET` puts an interpretation in the one
field a consumer branches on, which is exactly what
`normalized-record-v1.md` refuses one layer down.

`ATTENTION` was considered as the GDELT family and rejected for the same reason
in weaker form: attention is something people pay, and what GDELT counts is how
often a token appeared.

**Ontology V2 §3.6 is not amended.** The demand families remain four, closed and
unchanged. What stops being true is the claim that every row of `nlp.signals`
carries one. When a signal type genuinely produces a demand statement, it
projects onto `demand_signal_type` through the `maps_to` mechanism migration
0010 already added — recorded once on the reviewable type, never set per row by
an extractor.

### Cost accepted

A third quantity family requires a contract change and an ADR. That is the
intended friction: consumers branch exhaustively on this value and the two
families have different scope shapes, so an unhandled third value is a bug
rather than a gap.

---

## Decision 3 — order and instant are different facts, and neither is granted to GDELT

`SignalTemporalBasis` has four values — `NONE`, `SAME_PERIOD_LABEL`,
`ORDERED_PERIODS`, `COMPARABLE_INSTANTS` — and the required facts behind the
last two are separate: `SOURCE_RELATIVE_ORDER` and `COMPARABLE_INSTANT`.

`COMPARABLE_INSTANT` is withheld from GDELT by **H-29**: no first-party document
states a timezone for the WEB-NGRAM `DATE`.

`SOURCE_RELATIVE_ORDER` is a genuinely different question, and it is recorded as
**H-32**. The argument for granting it is good — `YYYYMMDDHHMMSS` is fixed-width
so lexicographic order is chronological within any fixed offset, and the label is
the published filename, which cannot repeat inside a directory. The argument is
an *inference about the publisher's mechanism*, not a retrieved statement about
the data, and if the stamps were local time in a zone observing daylight saving,
one hour a year would repeat and order would invert inside it. That is the same
class of reasoning `geography-mapping-v1.json` exists to replace.

The escape hatch is a reviewed map, `ORDER_ESTABLISHED_WITHOUT_TIMEZONE`, which
is **empty** and whose entries require a stated basis. H-32 is strictly weaker
than H-29 and separately answerable: a page stating the zone closes both, a page
stating only that the stamps are monotonic closes H-32 alone and unblocks every
within-stream sequential derivation without anyone asserting UTC.

Two structural consequences, both enforced rather than documented:

- `start` and `end` exist **only** under `COMPARABLE_INSTANTS`, and
  `observed_at` on the row is `NULL` under every other basis — a database CHECK,
  so the database refuses a GDELT signal with an event time.
- A direction other than `NOT_APPLICABLE` requires an ordered basis. "Increasing"
  is a statement about before and after, so **no GDELT signal can carry a
  direction while H-29 and H-32 are open.**

### Cost accepted

Six of nine candidate GDELT temporal derivations are blocked, including every
form of frequency change. The source with six `VALID` records supports more
temporal derivations than the source with two `PARTIAL` ones, and the entire
difference is these two open questions. That is the honest position and it is
visible rather than discovered later.

---

## Decision 4 — a blocked derivation produces no Signal, and there is no lifecycle enum

A row in a table of signals says a signal exists. A row meaning "no signal
exists" is a misleading signal.

So there is no `DRAFT`, no `BLOCKED`, no `INSUFFICIENT_DATA` and no reuse of
`NormalizedRecordQuality`, which states whether a *source observation* could be
structurally represented and would carry a word meaning something else here. A
refusal is a returned value object, `SignalDerivationRefusal`, with a closed
reason code — the same vocabulary that explains one excluded input, because a
refused derivation is usually that having happened often enough.

`PARTIAL` inputs are not filtered out. What matters is whether the *specific*
missing fact matters to the *specific* derivation, so an extractor declares its
`SignalRequiredFact` set and the model computes what each input withholds from
that record's own quality reasons. Every GDELT record is `PARTIAL` and a
within-bucket contrast between two terms needs neither of the things it is
missing.

### Cost accepted

Nothing in `nlp.signals` records that a derivation was attempted and refused.
Where a refusal should be logged is a derivation-run concern for the extractor
mission; adding a log to the signal table would be solving it in the wrong
place.

---

## Consequences

**Positive**

- The table can hold a valid Signal, which it could not before.
- Determinism is enforced by a CHECK rather than by intent: a `DETERMINISTIC`
  signal may not carry a model version, and a `MODEL_DERIVED` one may not omit
  one.
- Re-running a derivation converges on the row that exists —
  `UNIQUE (workspace_id, derivation_fingerprint)` and a UUIDv5 row id over the
  same material — so the aggregation layer is never handed two copies of one
  finding.
- Two pre-existing defects are closed on the way past:
  `scoring.evidence.signal_id` becomes tenant-safe, and the signal type registry
  entries are written by a migration instead of only by a development seed —
  which had made `nlp.signals` unwritable on the empty database CI starts from.

**Negative, and accepted**

- `nlp.signals` gains a child table, three JSONB columns and a fingerprint. It is
  a larger shape than the placeholder, and the placeholder could not hold a
  signal.
- Signals from different sources cannot be compared by magnitude. That is
  intended (§30) and it will be asked for.
- D-08 becomes visible one layer higher: several extractor versions coexist and
  which to read is still undecided.

**Neutral**

- No extractor exists. `SIGNAL_EXTRACTORS` is empty, `nlp.signals` holds 0 rows,
  and every test in this mission uses synthetic objects.
- D-03 and D-12 are untouched. No aggregation result is stored and nothing here
  reads or writes a vector.
