# Evidence & Confidence Framework V1

## 1. Purpose

This framework defines how the system records, evaluates, and communicates evidence.

The primary objective is to prevent unsupported AI-generated claims from being presented as market facts.

## 2. Evidence levels

### Level 0 — Hypothesis

No meaningful external evidence.

Example:

"Users might like this."

Should have minimal influence on evidence-backed scoring.

### Level 1 — Weak Signal

A small or isolated indication.

Example:

A few relevant comments.

### Level 2 — Repeated Signal

A recurring pattern observed multiple times.

Example:

Many independent users express a similar desire.

### Level 3 — Strong Multi-Source Signal

A relevant pattern appears across multiple sufficiently independent sources.

Example:

Community discussion plus search trend plus store reviews.

### Level 4 — Market Evidence

Evidence of real economic or behavioral activity.

Examples:

- purchases
- subscriptions
- established competing products
- repeated demand
- meaningful adoption indicators

### Level 5 — Direct Validation

Direct validation for the specific opportunity.

Examples:

- user interviews
- waitlist signups
- prototype usage
- preorders where appropriate
- real usage
- actual payments

Level 5 is the strongest form of validation but may not be available during early research.

## 3. Source reliability

> **Amended in Mission 1.14.** The list below is retained as a historical record
> of how this framework first described reliability. **It is not usable as
> stored values, and nothing may read it as a table.**
>
> Read literally it is a source-type coefficient table — *first-party structured
> data: high* — and a coefficient is exactly what
> [`evidence-aggregation-framework-v1.md`](evidence-aggregation-framework-v1.md)
> §3 and [`../data/evidence-reliability-contract-v1.md`](../data/evidence-reliability-contract-v1.md)
> forbid. A platform is not a reliability: the same platform carries a
> maintainer's release note and an anonymous rumour, and one number cannot be
> right for both.
>
> **What supersedes it.** Reliability is a reviewed judgement about a
> **measurement** (source, resource, record kind) for a **purpose** (claim type,
> proposition kind), resting on retrieved first-party documentation, versioned
> and superseded rather than updated. A scope nobody has assessed produces no
> number and the record stays `NON_SCORABLE`. See
> [`../data/evidence-reliability-contract-v1.md`](../data/evidence-reliability-contract-v1.md)
> and [ADR-026](../architecture/adr/ADR-026-reliability-assessment-scope-and-binding.md).
>
> The one sentence below that survives unchanged is the first:
> **reliability is context-dependent.** Mission 1.14 makes "context" a thing the
> system can name rather than a caveat.

Source reliability is context-dependent.

Initial heuristic examples (**historical, not usable as values**):

- Direct observed transaction: very high
- First-party structured data: high
- App/store reviews: medium-high
- Technical repositories: medium-high depending on claim
- Community posts: medium
- Social comments: lower and highly context-dependent
- LLM-generated reasoning: not market evidence

These were starting priors and were never immutable constants. Since Mission
1.14 they are not priors either: an unreviewed scope has no value at all, and a
prior would be a placeholder wearing a rationale.

## 4. Evidence independence

Repeated copies of the same underlying claim do not constitute independent evidence.

The system should attempt to detect:

- reposts
- copied articles
- syndicated content
- duplicated comments
- derivative discussions
- shared upstream sources

An `independence` estimate should be retained when practical.

## 5. Recency

Evidence value may decay over time.

Decay should depend on the domain:

- fast-moving social trends: rapid decay
- software/platform behavior: moderate decay
- demographic or structural market data: slower decay

The system should store observation timestamps and avoid treating old and recent signals as equivalent by default.

## 6. Evidence object

Conceptual structure:

```json
{
  "signal": "high_desire",
  "value": 0.87,
  "source": "example_source",
  "source_type": "community",
  "observed_at": "2026-08-20T00:00:00Z",
  "independence": 0.91,
  "reliability": 0.75,
  "confidence": 0.82,
  "evidence_level": 3
}
```

The actual production schema may differ.

## 7. Confidence dimensions

Keep distinct:

### Evidence confidence

Confidence that the underlying evidence is reliable and correctly represented.

### Model confidence

Confidence that the analytical model correctly interpreted the evidence.

### Research completeness

Confidence that enough of the relevant search space has been examined.

## 8. Claims taxonomy

Every important analytical statement should be classified as one of:

- OBSERVED
- INFERRED
- PREDICTED
- RECOMMENDED
- HYPOTHESIS

User-facing language should reflect the distinction.

## 9. Anti-hallucination rule

If a claim cannot be supported by collected evidence:

- classify it as a hypothesis,
- reduce confidence,
- or omit the claim.

Never invent:

- statistics
- sources
- citations
- competitor details
- market sizes
- prices
- user counts
- research results

## 10. Provenance

Where technically possible, evidence should retain:

- source identifier
- URL/reference
- collection timestamp
- source type
- acquisition method
- extraction method
- relevant content hash/fingerprint
- parent/derivative relationship if known

## 11. Evidence aggregation

Evidence should be aggregated using:

- source reliability
- independence
- recency
- relevance
- evidence level
- contradiction signals

Contradictory evidence should be preserved, not discarded simply because it hurts the score.

## 12. Versioning

Every important evidence-derived result should be traceable to the evidence snapshot and framework version used to calculate it.

**Since Mission 1.14 this extends to reliability.** A result records, per
contributing record, which reliability assessment produced its value — id,
version, origin, reviewer and review time — so a score's coefficients can be
reconstructed rather than trusted. Assessments are superseded and never updated,
so a result that used version N stays explicable after version N+1 lands
([ADR-026](../architecture/adr/ADR-026-reliability-assessment-scope-and-binding.md)).
