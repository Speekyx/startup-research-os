/* eslint-disable */
/**
 * DO NOT EDIT. GENERATED FILE.
 *
 * Source of truth : packages/contracts/schema/domain.v1.json
 * Generator       : packages/contracts/tools/generate.py
 * Regenerate      : python packages/contracts/tools/generate.py
 *
 * Editing this file by hand will be overwritten and will fail the contract
 * check in CI. Change the source of truth instead.
 *
 * contract_version: 1.2.0
 * ontology_version: 2
 */


export const CONTRACT_VERSION = "1.2.0" as const;
export const ONTOLOGY_VERSION = "2" as const;
export const RESEARCH_CONTEXT_SCHEMA_VERSION = "1.0.0" as const;

// --- Identifiers -----------------------------------------------------------
// Branded so that a WorkspaceId cannot be passed where an OpportunityId is
// expected. In a multi-tenant system that mix-up has a data-leak shape.

declare const __brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [__brand]: B };

/** A principal. Not a tenant. See ADR-005. (format: uuid) */
export type UserId = Brand<string, "UserId">;
/** The tenant boundary. Required on every tenant-scoped contract. (format: uuid) */
export type WorkspaceId = Brand<string, "WorkspaceId">;
/** Persistent workspace-scoped research objective. Ontology V2 §11.2. (format: uuid) */
export type ResearchProjectId = Brand<string, "ResearchProjectId">;
/** The only persisted execution entity. Ontology V2 §11.4. Replaces the retired 'run_id'. (format: uuid) */
export type ResearchSessionId = Brand<string, "ResearchSessionId">;
/** A domain hypothesis. Not owned by the session that found it. Ontology V2 §12. (format: uuid) */
export type OpportunityId = Brand<string, "OpportunityId">;
/** An assertion about an Opportunity that evidence can independently support or contradict. Ontology V2.1 §17. STABLE across statement revisions: the text may be rewritten, the identity may not. Distinct from ClaimType, which is an epistemic category and not an identity. (format: uuid) */
export type ClaimId = Brand<string, "ClaimId">;
/** An evidence record with mandatory provenance. (format: uuid) */
export type EvidenceId = Brand<string, "EvidenceId">;
/** An extracted demand signal. (format: uuid) */
export type SignalId = Brand<string, "SignalId">;
/** A registered external source. Global, not tenant-scoped. Registry contents are D-07, still open. (format: slug) */
export type SourceId = Brand<string, "SourceId">;

export const IDENTIFIER_FORMATS = {
  UserId: "uuid",
  WorkspaceId: "uuid",
  ResearchProjectId: "uuid",
  ResearchSessionId: "uuid",
  OpportunityId: "uuid",
  ClaimId: "uuid",
  EvidenceId: "uuid",
  SignalId: "uuid",
  SourceId: "slug",
} as const;

// --- Closed enums ----------------------------------------------------------
// Changing any of these is a material semantic change: new ontology version,
// plus an ADR where architectural. Ontology V2 §14.2.

/**
 * How an analytical statement is supported. Never conflated in any output.
 * @see opportunity-ontology-v2.md §7
 */
export const CLAIM_TYPE_VALUES = [
  "OBSERVED",
  "INFERRED",
  "PREDICTED",
  "RECOMMENDED",
  "HYPOTHESIS",
] as const;
export type ClaimType = (typeof CLAIM_TYPE_VALUES)[number];
export function isClaimType(v: unknown): v is ClaimType {
  return typeof v === "string" && (CLAIM_TYPE_VALUES as readonly string[]).includes(v);
}

/**
 * Geographic scope discriminator. Geographic axis only; segment scoping is A-12 and is NOT modelled.
 * @see opportunity-ontology-v2.md §4.1
 */
export const MARKET_SCOPE_TYPE_VALUES = [
  "GLOBAL",
  "REGION",
  "COUNTRY",
  "MULTI_COUNTRY",
] as const;
export type MarketScopeType = (typeof MARKET_SCOPE_TYPE_VALUES)[number];
export function isMarketScopeType(v: unknown): v is MarketScopeType {
  return typeof v === "string" && (MARKET_SCOPE_TYPE_VALUES as readonly string[]).includes(v);
}

/**
 * Session lifecycle. Budget exhaustion is COMPLETED with reduced Research Completeness, never a status. A session that finds nothing is COMPLETED, not FAILED.
 * @see opportunity-ontology-v2.md §15
 */
export const RESEARCH_SESSION_STATUS_VALUES = [
  "PENDING",
  "PLANNING",
  "COLLECTING",
  "ANALYZING",
  "SCORING",
  "COMPLETED",
  "FAILED",
  "CANCELLED",
] as const;
export type ResearchSessionStatus = (typeof RESEARCH_SESSION_STATUS_VALUES)[number];
export function isResearchSessionStatus(v: unknown): v is ResearchSessionStatus {
  return typeof v === "string" && (RESEARCH_SESSION_STATUS_VALUES as readonly string[]).includes(v);
}

/**
 * Closed. Signal TYPES within a family are a registry, not an enum.
 * @see opportunity-ontology-v2.md §3.6
 */
export const DEMAND_SIGNAL_FAMILY_VALUES = [
  "PAIN",
  "DESIRE",
  "BEHAVIORAL",
  "MARKET",
] as const;
export type DemandSignalFamily = (typeof DEMAND_SIGNAL_FAMILY_VALUES)[number];
export function isDemandSignalFamily(v: unknown): v is DemandSignalFamily {
  return typeof v === "string" && (DEMAND_SIGNAL_FAMILY_VALUES as readonly string[]).includes(v);
}

/**
 * The five families. Never collapsed into a single number, not in an API, a sort key or a badge.
 * @see scoring-framework-v1.1.md §2
 */
export const SCORE_FAMILY_VALUES = [
  "OPPORTUNITY",
  "EVIDENCE",
  "EXECUTION",
  "RESEARCH_COMPLETENESS",
  "MODEL_CONFIDENCE",
] as const;
export type ScoreFamily = (typeof SCORE_FAMILY_VALUES)[number];
export function isScoreFamily(v: unknown): v is ScoreFamily {
  return typeof v === "string" && (SCORE_FAMILY_VALUES as readonly string[]).includes(v);
}

/**
 * Logical tier. Business services request a tier, never a provider or model name.
 * @see ADR-006
 */
export const LLM_TIER_VALUES = [
  "FAST_MODEL",
  "BALANCED_MODEL",
  "STRONG_MODEL",
  "EMBEDDING_MODEL",
] as const;
export type LlmTier = (typeof LLM_TIER_VALUES)[number];
export function isLlmTier(v: unknown): v is LlmTier {
  return typeof v === "string" && (LLM_TIER_VALUES as readonly string[]).includes(v);
}

/**
 * Deprecation, never deletion. A deprecated entry stops being offered for new classification but keeps resolving for historical records.
 * @see opportunity-ontology-v2.md §14.4
 */
export const REGISTRY_STATUS_VALUES = [
  "ACTIVE",
  "DEPRECATED",
] as const;
export type RegistryStatus = (typeof REGISTRY_STATUS_VALUES)[number];
export function isRegistryStatus(v: unknown): v is RegistryStatus {
  return typeof v === "string" && (REGISTRY_STATUS_VALUES as readonly string[]).includes(v);
}

/**
 * Where a source stands in the governance gate. Closed: collector eligibility branches exhaustively on it, and an unhandled value would mean a source of unknown standing being treated as usable. Public visibility never produces APPROVED on its own.
 * @see source-registry-v1.md §5
 */
export const SOURCE_APPROVAL_STATE_VALUES = [
  "DRAFT",
  "REQUIRES_REVIEW",
  "APPROVED_WITH_CONDITIONS",
  "APPROVED",
  "RESTRICTED",
  "PROHIBITED",
  "SUSPENDED",
] as const;
export type SourceApprovalState = (typeof SOURCE_APPROVAL_STATE_VALUES)[number];
export function isSourceApprovalState(v: unknown): v is SourceApprovalState {
  return typeof v === "string" && (SOURCE_APPROVAL_STATE_VALUES as readonly string[]).includes(v);
}

/**
 * HOW access is technically performed. It says nothing about whether access is PERMITTED: permission is a separate dimension carried by the policy review. BROWSER_AUTOMATION being available never implies it is allowed.
 * @see source-registry-v1.md §8
 */
export const SOURCE_ACCESS_METHOD_VALUES = [
  "OFFICIAL_API",
  "PUBLIC_API",
  "RSS_OR_FEED",
  "DATASET_DOWNLOAD",
  "PUBLIC_WEB",
  "BROWSER_AUTOMATION",
  "MANUAL_IMPORT",
] as const;
export type SourceAccessMethod = (typeof SOURCE_ACCESS_METHOD_VALUES)[number];
export function isSourceAccessMethod(v: unknown): v is SourceAccessMethod {
  return typeof v === "string" && (SOURCE_ACCESS_METHOD_VALUES as readonly string[]).includes(v);
}

/**
 * The verdict for ONE activity. Activities are assessed separately because their conditions differ: a source may permit automated API access and forbid commercial use. A single boolean called `allowed` would erase exactly that difference.
 * @see source-registry-v1.md §6
 */
export const POLICY_ASSESSMENT_VALUES = [
  "PERMITTED",
  "PERMITTED_WITH_CONDITIONS",
  "NOT_PERMITTED",
  "NOT_ADDRESSED",
  "UNCLEAR",
  "NOT_ASSESSED",
] as const;
export type PolicyAssessment = (typeof POLICY_ASSESSMENT_VALUES)[number];
export function isPolicyAssessment(v: unknown): v is PolicyAssessment {
  return typeof v === "string" && (POLICY_ASSESSMENT_VALUES as readonly string[]).includes(v);
}

/**
 * What kind of document supports an assessment. Ordered by the evidence hierarchy: official operator documentation outranks anything else, and nothing below OFFICIAL_* may support an APPROVED state on its own.
 * @see source-registry-v1.md §7
 */
export const POLICY_EVIDENCE_TYPE_VALUES = [
  "OFFICIAL_API_DOCS",
  "OFFICIAL_TERMS",
  "OFFICIAL_LICENCE",
  "OFFICIAL_PRIVACY",
  "OFFICIAL_ACCESS_CONTROL",
  "OPERATOR_CORRESPONDENCE",
  "LEGAL_REVIEW",
] as const;
export type PolicyEvidenceType = (typeof POLICY_EVIDENCE_TYPE_VALUES)[number];
export function isPolicyEvidenceType(v: unknown): v is PolicyEvidenceType {
  return typeof v === "string" && (POLICY_EVIDENCE_TYPE_VALUES as readonly string[]).includes(v);
}

/**
 * Whether the source itself still exists as a target. Separate from approval: a deprecated source may have been approved, and an active source may never have been reviewed.
 * @see source-registry-v1.md §4
 */
export const SOURCE_LIFECYCLE_VALUES = [
  "ACTIVE",
  "DEPRECATED",
] as const;
export type SourceLifecycle = (typeof SOURCE_LIFECYCLE_VALUES)[number];
export function isSourceLifecycle(v: unknown): v is SourceLifecycle {
  return typeof v === "string" && (SOURCE_LIFECYCLE_VALUES as readonly string[]).includes(v);
}

/**
 * The shape of what access costs, not an amount. Concrete prices are versioned configuration because operators change them; a price compiled in here would be wrong within months and would look authoritative.
 * @see source-registry-v1.md §10
 */
export const SOURCE_ACQUISITION_COST_VALUES = [
  "FREE",
  "FREE_WITH_LIMITS",
  "PAID",
  "USAGE_BASED",
  "UNKNOWN",
] as const;
export type SourceAcquisitionCost = (typeof SOURCE_ACQUISITION_COST_VALUES)[number];
export function isSourceAcquisitionCost(v: unknown): v is SourceAcquisitionCost {
  return typeof v === "string" && (SOURCE_ACQUISITION_COST_VALUES as readonly string[]).includes(v);
}

/**
 * How likely the source is to carry personal data. A RISK CLASSIFICATION, not a legal ruling: it records what must be handled carefully and what still needs jurisdiction-specific review. GDPR analysis is separate and remains a human decision.
 * @see source-registry-v1.md §9
 */
export const PERSONAL_DATA_RISK_VALUES = [
  "NONE_EXPECTED",
  "PSEUDONYMOUS",
  "IDENTIFIABLE",
  "SENSITIVE_POSSIBLE",
  "UNKNOWN",
] as const;
export type PersonalDataRisk = (typeof PERSONAL_DATA_RISK_VALUES)[number];
export function isPersonalDataRisk(v: unknown): v is PersonalDataRisk {
  return typeof v === "string" && (PERSONAL_DATA_RISK_VALUES as readonly string[]).includes(v);
}

/**
 * How one Evidence record bears on a Claim. Support and contradiction are aggregated SEPARATELY and never averaged together, so this drives exhaustive branching and is closed.
 * @see evidence-aggregation-framework-v1.md §5
 */
export const EVIDENCE_DIRECTION_VALUES = [
  "SUPPORTS",
  "CONTRADICTS",
  "NEUTRAL",
] as const;
export type EvidenceDirection = (typeof EVIDENCE_DIRECTION_VALUES)[number];
export function isEvidenceDirection(v: unknown): v is EvidenceDirection {
  return typeof v === "string" && (EVIDENCE_DIRECTION_VALUES as readonly string[]).includes(v);
}

/**
 * What is KNOWN about an evidence record provenance relationship to the rest of the set. UNKNOWN is a distinct third state and is never silently promoted to KNOWN_INDEPENDENT.
 * @see evidence-aggregation-framework-v1.md §10, §13
 */
export const EVIDENCE_INDEPENDENCE_STATE_VALUES = [
  "KNOWN_INDEPENDENT",
  "KNOWN_DEPENDENT",
  "UNKNOWN",
] as const;
export type EvidenceIndependenceState = (typeof EVIDENCE_INDEPENDENCE_STATE_VALUES)[number];
export function isEvidenceIndependenceState(v: unknown): v is EvidenceIndependenceState {
  return typeof v === "string" && (EVIDENCE_INDEPENDENCE_STATE_VALUES as readonly string[]).includes(v);
}

/**
 * WHAT KIND of thing was observed, independent of how strong it is. Gates EvidenceLevel 4 and 5, which quantity of evidence must never reach on its own. Closed because level eligibility branches exhaustively over it.
 * @see evidence-aggregation-framework-v1.md §11
 */
export const EVIDENCE_OBSERVATION_CATEGORY_VALUES = [
  "STATED_OPINION",
  "REPORTED_BEHAVIOUR",
  "OBSERVED_BEHAVIOUR",
  "MARKET_ACTIVITY",
  "DIRECT_VALIDATION",
  "UNCATEGORISED",
] as const;
export type EvidenceObservationCategory = (typeof EVIDENCE_OBSERVATION_CATEGORY_VALUES)[number];
export function isEvidenceObservationCategory(v: unknown): v is EvidenceObservationCategory {
  return typeof v === "string" && (EVIDENCE_OBSERVATION_CATEGORY_VALUES as readonly string[]).includes(v);
}

/**
 * Whether a claim decays. A property of the CLAIM, never of the source: the same platform can carry an evergreen fact and a trend that is stale in a week. Closed because freshness branches exhaustively over it.
 * @see evidence-aggregation-framework-v1.md §9
 */
export const CLAIM_TEMPORALITY_VALUES = [
  "EVERGREEN",
  "TEMPORALLY_SENSITIVE",
] as const;
export type ClaimTemporality = (typeof CLAIM_TEMPORALITY_VALUES)[number];
export function isClaimTemporality(v: unknown): v is ClaimTemporality {
  return typeof v === "string" && (CLAIM_TEMPORALITY_VALUES as readonly string[]).includes(v);
}

/**
 * What PROCESS produced the claim, at the level of kind rather than instance. Deliberately carries no model, provider or prompt name: those change constantly and belong in provenance columns, where a new one does not require a contract change.
 * @see claim-model-v1.md §6
 */
export const CLAIM_ORIGIN_VALUES = [
  "MANUAL",
  "DETERMINISTIC_EXTRACTION",
  "LLM_EXTRACTION",
  "INFERRED",
  "SYSTEM_GENERATED",
  "IMPORTED",
] as const;
export type ClaimOrigin = (typeof CLAIM_ORIGIN_VALUES)[number];
export function isClaimOrigin(v: unknown): v is ClaimOrigin {
  return typeof v === "string" && (CLAIM_ORIGIN_VALUES as readonly string[]).includes(v);
}

/**
 * EDITORIAL state, never epistemic. There is deliberately no VALIDATED or REJECTED value: evidence can change, and a lifecycle state derived from EvidenceLevel would freeze a conclusion the evidence no longer supports (Mission 1.2 §38). What a claim is worth is read from its aggregation, never from this column.
 * @see claim-model-v1.md §8
 */
export const CLAIM_LIFECYCLE_VALUES = [
  "ACTIVE",
  "WITHDRAWN",
] as const;
export type ClaimLifecycle = (typeof CLAIM_LIFECYCLE_VALUES)[number];
export function isClaimLifecycle(v: unknown): v is ClaimLifecycle {
  return typeof v === "string" && (CLAIM_LIFECYCLE_VALUES as readonly string[]).includes(v);
}

/**
 * How one ResearchSession related to a persisted entity it encountered. Promoted to the canonical contract in Mission 1.2: it already governed opportunity observations as a SQL CHECK plus a Python frozenset, which is exactly the drift ADR-009 exists to prevent. Not a scoring judgement.
 * @see opportunity-ontology-v2.md §12; claim-model-v1.md §7
 */
export const OBSERVATION_KIND_VALUES = [
  "DISCOVERED",
  "CORROBORATED",
  "CONTRADICTED",
] as const;
export type ObservationKind = (typeof OBSERVATION_KIND_VALUES)[number];
export function isObservationKind(v: unknown): v is ObservationKind {
  return typeof v === "string" && (OBSERVATION_KIND_VALUES as readonly string[]).includes(v);
}

/**
 * Whether the PARAMETERS of a profile have been calibrated against data. Separate from whether the algorithm is defined: defining equations calibrates nothing. Production scoring requires CALIBRATED.
 * @see evidence-aggregation-framework-v1.md §14
 */
export const AGGREGATION_PROFILE_STATUS_VALUES = [
  "DRAFT",
  "UNCALIBRATED",
  "CALIBRATED",
  "RETIRED",
] as const;
export type AggregationProfileStatus = (typeof AGGREGATION_PROFILE_STATUS_VALUES)[number];
export function isAggregationProfileStatus(v: unknown): v is AggregationProfileStatus {
  return typeof v === "string" && (AGGREGATION_PROFILE_STATUS_VALUES as readonly string[]).includes(v);
}

/**
 * Whether the numbers in a result may be read as covering the evidence set. A result that silently dropped half its items would be indistinguishable from one that used all of them.
 * @see evidence-aggregation-framework-v1.md §16
 */
export const EVIDENCE_AGGREGATION_STATUS_VALUES = [
  "COMPLETE",
  "PARTIAL",
  "UNAVAILABLE",
] as const;
export type EvidenceAggregationStatus = (typeof EVIDENCE_AGGREGATION_STATUS_VALUES)[number];
export function isEvidenceAggregationStatus(v: unknown): v is EvidenceAggregationStatus {
  return typeof v === "string" && (EVIDENCE_AGGREGATION_STATUS_VALUES as readonly string[]).includes(v);
}

// --- Numeric bounds --------------------------------------------------------
// A field named `confidence` is always [0,1]. A field named `*_score` is
// always 0-100. scoring-framework-v1.1.md §4.1.

export const NUMERIC_BOUNDS = {
  Confidence: { min: 0.0, max: 1.0, integer: false, kind: "unit_interval" },
  Probability: { min: 0.0, max: 1.0, integer: false, kind: "unit_interval" },
  Reliability: { min: 0.0, max: 1.0, integer: false, kind: "unit_interval" },
  Independence: { min: 0.0, max: 1.0, integer: false, kind: "unit_interval" },
  Score: { min: 0, max: 100, integer: true, kind: "score" },
  EvidenceLevel: { min: 0, max: 5, integer: true, kind: "level" },
} as const;

export type NumericTypeName = keyof typeof NUMERIC_BOUNDS;

// --- Registry names --------------------------------------------------------
// These are EXTENSIBLE registries, not enums. Ontology V2 §14.3.
// This list names the registries; it never enumerates their entries.

export const REGISTRY_NAMES = [
  "market_type",
  "product_type",
  "user_motivation",
  "user_behavior",
  "value_proposition",
  "demand_signal_type",
  "retention_mechanism",
  "monetization_model",
  "distribution_channel",
  "risk",
  "region",
  "source_family",
] as const;
export type RegistryName = (typeof REGISTRY_NAMES)[number];

// --- MarketScope rules -----------------------------------------------------
// Country codes uppercased, deduplicated, sorted. Region ids lowercased, deduplicated, sorted. One scope therefore has exactly one representation, which is what makes it safe as a cache key, a dedup key and an equality test.

export const COUNTRY_CODE_PATTERN = /^[A-Z]{2}$/;
export const MARKET_SCOPE_RULES = {
  "COUNTRY": {
    "countries_exact": 1,
    "regions": 0
  },
  "GLOBAL": {
    "countries": 0,
    "regions": 0
  },
  "MULTI_COUNTRY": {
    "countries_min": 2,
    "regions": 0
  },
  "REGION": {
    "countries": 0,
    "regions_min": 1
  }
} as const;
