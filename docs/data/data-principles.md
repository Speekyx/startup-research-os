# Data Principles V1

## 1. Purpose

These principles govern data acquisition, storage, quality, provenance, and responsible use.

## 2. Source strategy

No single source is treated as the truth.

Use multiple source families where relevant:

- search/trend signals
- communities
- product launches
- app stores
- developer ecosystems
- content platforms
- public websites
- structured datasets
- first-party sources

The exact source registry will be created during the Data Engineering phase.

## 3. Acquisition

Use official APIs where available and appropriate.

For scraping or browser automation:

- comply with applicable terms and policies,
- respect access controls,
- respect rate limits,
- do not bypass authentication or technical protections,
- minimize collection,
- collect only data necessary for the research objective.

API credentials and secrets must be kept outside source control.

## 4. Raw data preservation

Where lawful and appropriate, preserve enough raw/reference information to reproduce important transformations.

Recommended conceptual pipeline:

`raw → normalized → deduplicated → enriched → signal → feature → score`

## 5. Data quality

Track:

- completeness
- freshness
- duplication
- provenance
- parsing quality
- source reliability
- temporal coverage
- geographic coverage
- language coverage

## 6. Deduplication

Deduplicate at multiple levels:

- exact duplicates
- near duplicates
- syndicated content
- repeated events
- reposts
- same-source updates

Do not destroy provenance when deduplicating.

## 7. Language and geography

The engine should support multilingual and multi-country research.

Do not assume English-language data represents the global market.

Language detection and locale-aware processing should be explicit.

## 8. Privacy

Avoid unnecessary personal data.

Where possible, aggregate or anonymize user-level information.

The system's research purpose does not justify collecting arbitrary personal information.

## 9. Temporal modeling

Every time-sensitive observation should have an observation timestamp.

Prefer event-time semantics over ingestion-time semantics for market analysis when both are available.

## 10. Contradictions

Do not overwrite conflicting evidence.

Store competing observations and allow the analytical layer to reason about disagreement.

## 11. Data lineage

Important derived values should be traceable to:

- source
- raw/reference record
- transformation
- model/version
- timestamp

## 12. Cost control

Data collection should be incremental.

Prefer:

- caching
- deduplication before expensive processing
- batching
- incremental updates
- selective deep research

Avoid repeatedly collecting identical data.

## 13. Legal and policy review

Before integrating a new source, record:

- access method
- API availability
- relevant usage restrictions
- rate limits
- retention constraints
- data licensing considerations
- authentication requirements

A source being publicly visible does not automatically mean unrestricted commercial reuse is permitted.
