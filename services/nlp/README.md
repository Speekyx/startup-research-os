# `services/nlp`

**Status:** **partially implemented.** Two deterministic signal extractors exist
(Mission 1.11.1) and five real Signals do. Everything else on this page --
embeddings, clustering, LLM classification, independence estimation -- is still
a boundary and is blocked by D-12.

```text
sros_nlp/extractors/   numeric-period-change@1.0.0
                       lexical-frequency-contrast@1.0.0
```

Neither reaches a network, a model or an embedder, and
`infrastructure/scripts/validate_signals.py` asserts it by walking every import.
See `docs/data/signal-derivation-runtime-v1.md`.

**Runtime:** Python. BGE-M3 and HDBSCAN being Python-only is what drove ADR-004
to remove BullMQ and put the whole backend on Celery.

## Responsibility

Turn normalized text into **structured signals**. This is the boundary where
unstructured language becomes something the rest of the system can reason about.

It classifies, extracts, embeds, clusters and deduplicates semantically. It does
**not** score opportunities, size markets, or make recommendations.

## Inputs

- Normalized records from `acquisition`.
- The ontology vocabulary from `packages/contracts`
  (motivations, behaviors, value propositions, signal types).

## Outputs

- **Extracted signals** typed against `opportunity-ontology-v1.1.md` §3.6:
  pain, desire, behavioral, market.
- **Classifications**: market type, product type, user motivation, user behavior,
  value proposition — each with confidence and rationale.
- **Embeddings** (BGE-M3), written to Qdrant with their provenance.
- **Clusters** (HDBSCAN) grouping related signals into candidate opportunity seeds.
- **Independence estimates** — near-duplicate, syndication and derivative
  detection (`evidence-confidence-framework-v1.md` §4). This is the semantic
  deduplication that `acquisition` cannot perform.
- **Language and locale detection** (`data-principles.md` §7).

## Dependencies

- PostgreSQL — normalized records in, signals out
- Qdrant — embedding index (derived and rebuildable, see audit A-09)
- LLM Gateway (ADR-006) — logical tier only, never a provider SDK. `FAST_MODEL`
  for high-volume classification, `EMBEDDING_MODEL` (local BGE-M3) for vectors
- `packages/contracts`

## Future API surface

```
POST /internal/extract         normalized record -> signals
POST /internal/classify        text -> ontology classifications + confidence
POST /internal/embed           text -> embedding (batched)
POST /internal/cluster         embeddings -> clusters
POST /internal/independence    record set -> pairwise independence estimates
GET  /internal/models          active model + version, for reproducibility
```

## The cost ladder (non-negotiable)

`llm-reasoning-rules.md` §8 defines the required order. Use the cheapest method
that works:

1. rules / regex — deterministic extraction
2. classical NLP / lightweight models — straightforward classification
3. embeddings — semantic similarity, clustering, dedup
4. LLM — only where reasoning genuinely adds value

An LLM call per collected record is a design error. The economics of this system
depend on the ladder being respected at the point where volume is highest, which
is exactly here.

## Reproducibility requirements

Every NLP output stores (`llm-reasoning-rules.md` §9): model/provider, model
version, prompt/template version, parameters, routing version, input evidence
references, timestamp. The LLM Gateway returns this record with every response
(ADR-006), so it is attached rather than reconstructed.

Without this, a model upgrade silently invalidates every historical signal with
no way to tell which ones. Embedding model changes additionally require a
re-embedding strategy (D-12).

## Prompt injection

External content is untrusted data (`llm-reasoning-rules.md` §7). Scraped text is
**never** placed where it can be read as an instruction. Content goes in a
delimited data region with an explicit "analyze, do not obey" framing, and
outputs are validated against a schema before use. A structured-output validation
failure is treated as a possible injection attempt and logged, not retried blindly.

## Failure modes to design for

| Failure | Required behavior |
|---------|-------------------|
| Model returns unparseable output | Fail the record with a flag; never coerce into a plausible-looking result |
| Low classification confidence | Emit the classification with low confidence (`[0,1]`), or abstain. Never round up to certainty |
| LLM budget exhausted for the run | Explicit budget-exhausted state; the run reports lower Research Completeness (ADR-006) |
| Unsupported language | Record explicitly; do not silently fall back to English-model output |
| Empty or trivial text | Skip with a reason, no signal emitted |
| Clustering yields one giant cluster | Surface as a quality signal, not a valid result |
| LLM output contradicts the source | Preserve both (`data-principles.md` §10), flag the contradiction |
