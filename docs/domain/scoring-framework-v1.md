# Scoring Framework V1

## 1. Purpose

The scoring framework ranks opportunities using multiple dimensions while adapting to the type of opportunity being evaluated.

The system is not a guaranteed-success predictor. Scores represent structured estimates from available evidence.

## 2. Separate score families

Every opportunity should conceptually expose:

### Opportunity Score

How attractive the opportunity appears given the selected research context.

### Evidence Score

How strong and sufficiently diverse the supporting evidence is.

### Execution Score

How feasible the opportunity appears for the requested constraints.

### Research Completeness

How comprehensively the relevant research space appears to have been covered.

### Model Confidence

How confident the analytical model is in its interpretation.

These should not be collapsed into a single number.

## 3. Dimensions

Candidate dimensions:

- Problem
- Desire
- Utility
- Engagement
- Retention
- Virality
- Market
- Momentum
- Competition Gap
- Monetization
- Distribution
- Feasibility

Education-oriented profiles may also explicitly score Learning Value.

## 4. Normalization

Dimension scores are normalized to 0–100.

A score must have:

- value
- rationale
- supporting evidence references where applicable
- confidence
- timestamp/version

## 5. Dynamic scoring profiles

Weights depend on the opportunity profile.

Example starting hypotheses:

### B2B productivity

Higher emphasis on:

- Problem
- Utility
- Monetization
- Market
- Retention
- Competition Gap
- Feasibility

Lower emphasis on virality.

### B2C entertainment

Higher emphasis on:

- Desire
- Engagement
- Retention
- Virality
- Market
- Momentum

Lower emphasis on pain.

### Education

Higher emphasis on:

- Desire
- Learning Value
- Engagement
- Retention
- Utility
- Market

These are V1 hypotheses, not scientific truths. They must be evaluated and later calibrated against data.

## 6. Score calculation

Conceptually:

`Opportunity Score = weighted combination of relevant dimensions`

Weights must be explicit, versioned, and sum to 100% for each scoring profile.

The system must retain the component scores so users can understand why opportunities rank differently.

## 7. Evidence-aware scoring

Weak evidence must not be allowed to create false precision.

The system should be able to produce:

```text
Opportunity Score: 82
Evidence Score: 61
Model Confidence: 74
Research Completeness: 58
```

Interpretation:

The opportunity looks promising, but the evidence base is incomplete.

## 8. Competition

Competition is not inherently negative.

Existing competitors may indicate validated demand.

The relevant concept is the `Competition Gap`, including:

- unmet needs
- weak UX
- underserved segments
- poor localization
- pricing gaps
- distribution gaps
- missing capabilities
- emerging technology shifts

## 9. Market-specific scoring

Scores should be calculated for the selected market context where sufficient data exists.

An opportunity may have substantially different scores by country.

Example:

```text
Global: 72
USA: 89
France: 76
Japan: 84
India: 67
```

Country scores must include their own evidence and confidence.

## 10. No false precision

Do not present `82.37` when the evidence only justifies an approximate score.

User-facing scores may be rounded.

Internal calculations can retain higher precision if useful.

## 11. Versioning

Every score must be traceable to:

- scoring framework version
- scoring profile version
- model version if applicable
- input evidence snapshot/time
