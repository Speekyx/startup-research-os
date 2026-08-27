# Scoring Framework V1.1

**Status:** Authoritative. Supersedes `scoring-framework-v1.md`.
**Date:** 2026-08-27
**Supersedes:** V1 (retained as a historical specification, not deleted)
**Authorized by:** Sprint 0 / Mission 0.1.1, §6 and §7

---

## 0. Changes from V1

V1.1 inherits V1 in full. Only the following changes are authorized, and only
they were applied. Section numbering is preserved so V1 references remain valid.

| Change | Section | Reason |
|--------|---------|--------|
| Confidence is internally represented on the unit interval `[0,1]` | §4, §4.1 | Resolves audit **C-04** — V1 §7 showed `Model Confidence: 74` while `evidence-confidence-framework-v1.md` §6 showed `"confidence": 0.82`. The same field name carried two scales |
| Confidence is presented as a percentage `[0,100]%` | §4.1 | Presentation rule, separated from the storage rule |
| Explicit distinction between score, confidence, probability and evidence strength | §4.1 (new) | These are four different quantities that V1 did not separate. Conflating them is the most likely source of silent numeric error in the system |
| Dimension and score-family semantics preserved on 0–100 | §4, §6 | Explicitly retained. Unit-interval representation is permitted internally with a lossless mapping |
| Claims taxonomy reference aligned to five uppercase values | §12 (new) | Consistency with `opportunity-ontology-v1.1.md` §7 |
| Evidence aggregation explicitly recorded as **not defined** | §13 (new) | Audit A-02/A-03/A-04. Prevents an implementer from inventing the formula |

**No new scoring weights were invented.** **No evidence aggregation formula was
created.** Dimensions, profiles, weighting rules, competition semantics and
market-specific scoring are identical to V1.

---

## 1. Purpose

The scoring framework ranks opportunities using multiple dimensions while
adapting to the type of opportunity being evaluated.

The system is not a guaranteed-success predictor. Scores represent structured
estimates from available evidence.

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

> **V1.1 note.** `Model Confidence` is a **score family**, not a confidence
> field. It is expressed on the 0–100 score scale like every other family. The
> `confidence` *field* attached to an individual score, dimension or evidence
> object is a different quantity on the unit interval. See §4.1 — this collision
> of names is real and is the single most likely source of a silent numeric bug
> in the system.

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

> **V1.1 clarification.** The 0–100 scale is the **canonical semantic scale for
> scores** and is preserved. Internal computation (ML pipelines, aggregation,
> storage of intermediate values) may use the equivalent unit interval `[0,1]`,
> since the mapping `unit = score / 100` is exact and lossless. What must never
> vary is which quantity is being expressed — see §4.1.

## 4.1 Numeric representation — canonical rules

**New in V1.1.** This section resolves audit finding C-04.

### The four quantities

They are distinct. Do not interchange them, do not store them in a shared
column, do not render them with the same component.

| Quantity | What it expresses | Canonical range | Presentation |
|----------|-------------------|-----------------|--------------|
| **Score** | An assessed magnitude on a defined scale (Opportunity Score, a dimension score, a score family) | `0–100` | `0–100`, integer |
| **Confidence** | How much the system trusts a value or an interpretation | `[0.0, 1.0]` | percentage, e.g. `82%` |
| **Probability** | Likelihood of an event or outcome | `[0.0, 1.0]` | percentage |
| **Evidence strength** | How strong the underlying evidence is | `evidence_level` integer `0–5`, plus `reliability` and `independence` on `[0.0, 1.0]` | level label + percentages |

A high score with low confidence is a normal and meaningful state. So is a low
score with high confidence. Collapsing the two loses exactly the information this
system exists to preserve.

### Storage and contract rules

- **Confidence, reliability, independence, probability, and signal `value`:**
  unit interval `[0.0, 1.0]`. This applies to the database, to API and domain
  contracts, and to ML calculations.
- **Scores and score families:** 0–100 semantics. Internal representation may be
  the equivalent unit interval where a pipeline benefits from it, provided the
  scale is unambiguous at every boundary.
- **`evidence_level`:** integer `0–5`. Never rescaled, never expressed as a
  percentage, never averaged into a score.

### Presentation rules

- Confidence and probability render as percentages: `0.82` → `82%`.
- Scores render as integers on 0–100.
- **No false precision** (§10). `82`, never `82.37`. `82%`, never `82.37%`.

### Naming rule

A field named `confidence` is always on `[0,1]`. A field named `*_score` is
always on `0–100`. A contract that violates this naming rule is a bug, not a
style choice — `packages/contracts` is the single place both are declared, and
its validators enforce the ranges.

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

These are V1 hypotheses, not scientific truths. They must be evaluated and later
calibrated against data.

## 6. Score calculation

Conceptually:

`Opportunity Score = weighted combination of relevant dimensions`

Weights must be explicit, versioned, and sum to 100% for each scoring profile.

The system must retain the component scores so users can understand why
opportunities rank differently.

> **V1.1 note.** Whether a profile weights every dimension (dense, with zeros) or
> only its own subset (sparse) remains **open** — audit A-01. It is not resolved
> here. Whichever is chosen, the sum-to-100% rule is validated at profile load
> time, not at score time.

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

> **V1.1 note.** All four values above are **score families** on 0–100 (§4.1).
> The `confidence` field attached to each individual dimension score inside them
> is on `[0,1]`.

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

Scores should be calculated for the selected market context where sufficient data
exists.

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

> **V1.1 note.** Scores produced under this framework record
> `scoring_framework_version = "1.1"`. Scores produced under V1, if any exist,
> retain `"1.0"` and are not retroactively relabeled.

## 12. Claim typing of scores

**New in V1.1.** Consistency with `opportunity-ontology-v1.1.md` §7.

Every score and every rationale carries a claim type from the canonical
five-value taxonomy:

```text
OBSERVED | INFERRED | PREDICTED | RECOMMENDED | HYPOTHESIS
```

In practice a computed score is `INFERRED` (derived analytically from
observations) or `PREDICTED` (a model estimate about an unknown outcome). A score
computed from an evidence set too thin to support it is `HYPOTHESIS`, and must be
presented as such rather than as a lower `INFERRED` number.

## 13. Evidence aggregation — NOT DEFINED

**New in V1.1.** This section exists to prevent an implementer from filling the
gap by choosing values.

The Evidence Score has a defined *purpose* (§2) and an illustrative *value* (§7),
but **no aggregation function**. `evidence-confidence-framework-v1.md` §11 lists
six aggregation inputs (source reliability, independence, recency, relevance,
evidence level, contradiction signals) with no formula, no weights and no decay
parameters.

The following remain **undefined and must not be invented**:

- the Evidence Score aggregation formula (audit A-02)
- recency decay families and half-lives per source domain (audit A-03)
- the independence threshold gating evidence level 3 (audit A-04)
- contradiction penalties

### Blocking dependency

> **`services/scoring` must not be implemented until
> `docs/domain/evidence-aggregation-framework-v1.md` exists and is authorized.**

Implementing scoring first means someone chooses those constants. They become
load-bearing, they are unfalsifiable after the fact because nothing records that
they were guessed, and every score in the system then rests on them. That is
precisely the false precision §10 forbids, applied to the foundation rather than
to a display digit.

This dependency is tracked as decision **D-03** and is deliberately still open at
the end of Mission 0.1.1.
