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
 * contract_version: 1.0.0
 * ontology_version: 2
 */


export const CONTRACT_VERSION = "1.0.0" as const;
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
