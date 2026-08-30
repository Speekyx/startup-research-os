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
 * contract_version: 1.9.0
 * ontology_version: 2
 */


export const CONTRACT_VERSION = "1.9.0" as const;
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
 * HOW a review condition can be checked. Exists so APPROVED_WITH_CONDITIONS cannot silently mean 'a collector may run': each condition is satisfied individually, and one that no machine can verify must say so rather than pretending it can.
 * @see source-registry-v1.md; Mission 1.3 §24
 */
export const CONDITION_VERIFICATION_VALUES = [
  "CONFIG_REFERENCE",
  "CAPABILITY",
  "RETENTION_LIMIT",
  "ACCESS_METHOD",
  "HUMAN_CONFIRMATION",
] as const;
export type ConditionVerification = (typeof CONDITION_VERIFICATION_VALUES)[number];
export function isConditionVerification(v: unknown): v is ConditionVerification {
  return typeof v === "string" && (CONDITION_VERIFICATION_VALUES as readonly string[]).includes(v);
}

/**
 * The outcome of running a verifier against one review condition. Four values rather than a boolean, because 'we could not establish it' and 'it does not hold' call for different next steps and only one of them is a bug. UNKNOWN never becomes SATISFIED, and only SATISFIED clears the condition.
 * @see source-condition-gap-analysis-v1.md; Mission 1.4 §19
 */
export const CONDITION_VERIFICATION_RESULT_VALUES = [
  "SATISFIED",
  "UNSATISFIED",
  "UNKNOWN",
  "NOT_APPLICABLE",
] as const;
export type ConditionVerificationResult = (typeof CONDITION_VERIFICATION_RESULT_VALUES)[number];
export function isConditionVerificationResult(v: unknown): v is ConditionVerificationResult {
  return typeof v === "string" && (CONDITION_VERIFICATION_RESULT_VALUES as readonly string[]).includes(v);
}

/**
 * One required part of a source's attribution obligation. A closed enum because the renderer branches exhaustively: an element it does not recognise must be a contract change, never a silently dropped requirement.
 * @see acquisition-authorization-v1.md; Mission 1.4 §6
 */
export const ATTRIBUTION_ELEMENT_VALUES = [
  "SOURCE_CREDIT",
  "LICENCE_IDENTIFIER",
  "EXACT_NOTICE",
  "MODIFICATION_STATEMENT",
  "DATASET_DOI",
  "ACCESS_DATE",
  "DISCLAIMER",
] as const;
export type AttributionElement = (typeof ATTRIBUTION_ELEMENT_VALUES)[number];
export function isAttributionElement(v: unknown): v is AttributionElement {
  return typeof v === "string" && (ATTRIBUTION_ELEMENT_VALUES as readonly string[]).includes(v);
}

/**
 * Why an acquisition attempt did not produce records. A closed vocabulary so the orchestrator branches on a meaning rather than on a third party's exception class -- an upstream library changing its exception hierarchy must not change how this system retries. Each value also fixes whether it is worth retrying, which is the decision that costs money when it is wrong.
 * @see world-bank-collector-v1.md; Mission 1.5 §32
 */
export const ACQUISITION_ERROR_CODE_VALUES = [
  "AUTHORIZATION_REJECTED",
  "RESOURCE_NOT_PERMITTED",
  "NETWORK_TIMEOUT",
  "RATE_LIMITED",
  "TEMPORARY_UPSTREAM",
  "UPSTREAM_CLIENT_ERROR",
  "INVALID_RESPONSE",
  "PARSING_FAILURE",
  "PERSISTENCE_FAILURE",
  "CANCELLED",
] as const;
export type AcquisitionErrorCode = (typeof ACQUISITION_ERROR_CODE_VALUES)[number];
export function isAcquisitionErrorCode(v: unknown): v is AcquisitionErrorCode {
  return typeof v === "string" && (ACQUISITION_ERROR_CODE_VALUES as readonly string[]).includes(v);
}

/**
 * Whether the platform's own licence covers a particular resource. Aggregators republish material they do not own, so platform approval is not resource approval. UNKNOWN exists because it is the common case and must fail closed rather than be guessed either way.
 * @see acquisition-authorization-v1.md; Mission 1.4 §12
 */
export const RESOURCE_CONTENT_ORIGIN_VALUES = [
  "PLATFORM_LICENSED",
  "THIRD_PARTY",
  "UNKNOWN",
] as const;
export type ResourceContentOrigin = (typeof RESOURCE_CONTENT_ORIGIN_VALUES)[number];
export function isResourceContentOrigin(v: unknown): v is ResourceContentOrigin {
  return typeof v === "string" && (RESOURCE_CONTENT_ORIGIN_VALUES as readonly string[]).includes(v);
}

/**
 * What kind of thing authorises one resource. Closed because authorization branches exhaustively on it and an unhandled value would mean a resource of unknown standing being treated as authorised. Two values, deliberately: there is no UNKNOWN member, because an unestablished basis is the ABSENCE of one -- expressed as null and refused -- and a third value that looked like an answer would be the exact fabrication this enum exists to prevent. A DIRECT_GRANT never satisfies a rule that requires a NAMED_LICENCE.
 * @see acquisition-rights-basis-gap-analysis-v1.md; Mission 1.9.1 §14
 */
export const RIGHTS_BASIS_VALUES = [
  "NAMED_LICENCE",
  "DIRECT_GRANT",
] as const;
export type RightsBasis = (typeof RIGHTS_BASIS_VALUES)[number];
export function isRightsBasis(v: unknown): v is RightsBasis {
  return typeof v === "string" && (RIGHTS_BASIS_VALUES as readonly string[]).includes(v);
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

/**
 * The STRUCTURAL completeness of a normalized record, and nothing else. Not a confidence and not a reliability: those are epistemic judgments on [0,1] that belong to the evidence model, and a value of that kind here would invite a downstream stage to multiply a parsing outcome by an evidence weight. Closed because every consumer must decide what to do with each state, and an unhandled fourth value would be a bug rather than a gap.
 * @see normalized-record-v1.md §8; Mission 1.6 §25
 */
export const NORMALIZED_RECORD_QUALITY_VALUES = [
  "VALID",
  "PARTIAL",
  "INVALID",
] as const;
export type NormalizedRecordQuality = (typeof NORMALIZED_RECORD_QUALITY_VALUES)[number];
export function isNormalizedRecordQuality(v: unknown): v is NormalizedRecordQuality {
  return typeof v === "string" && (NORMALIZED_RECORD_QUALITY_VALUES as readonly string[]).includes(v);
}

/**
 * Why a normalized record is not VALID. A closed vocabulary rather than free text, for the same reason AcquisitionErrorCode is one: a consumer branches on the MEANING -- a record with no reported value is skipped, a record whose geography is unclassified is still usable -- and a message it had to pattern-match would make that branch break on a reworded string.
 * @see normalized-record-v1.md §8; Mission 1.6 §26
 */
export const NORMALIZATION_QUALITY_REASON_VALUES = [
  "VALUE_NOT_REPORTED",
  "MALFORMED_NUMERIC_VALUE",
  "GEOGRAPHY_NOT_CLASSIFIED",
  "GEOGRAPHY_MISSING",
  "METRIC_MISSING",
  "PERIOD_NOT_SUPPORTED",
  "PERIOD_TIMEZONE_NOT_ESTABLISHED",
  "LANGUAGE_NOT_MAPPED",
] as const;
export type NormalizationQualityReason = (typeof NORMALIZATION_QUALITY_REASON_VALUES)[number];
export function isNormalizationQualityReason(v: unknown): v is NormalizationQualityReason {
  return typeof v === "string" && (NORMALIZATION_QUALITY_REASON_VALUES as readonly string[]).includes(v);
}

/**
 * Why a normalization attempt produced no record at all. Distinct from NormalizationQualityReason, which explains a record that EXISTS and is degraded. Closed so orchestration branches on a meaning rather than on a Python exception class, the same argument AcquisitionErrorCode makes.
 * @see normalized-record-v1.md §13; Mission 1.6 §28
 */
export const NORMALIZATION_ERROR_CODE_VALUES = [
  "UNSUPPORTED_SOURCE",
  "UNSUPPORTED_COLLECTOR_VERSION",
  "INVALID_RAW_RECORD",
  "UNSUPPORTED_RECORD_TYPE",
  "NON_DETERMINISTIC_OUTPUT",
  "PERSISTENCE_FAILURE",
  "CANCELLED",
] as const;
export type NormalizationErrorCode = (typeof NORMALIZATION_ERROR_CODE_VALUES)[number];
export function isNormalizationErrorCode(v: unknown): v is NormalizationErrorCode {
  return typeof v === "string" && (NORMALIZATION_ERROR_CODE_VALUES as readonly string[]).includes(v);
}

/**
 * The temporal shape of a canonical observation. Closed because downstream time handling must branch exhaustively -- a YEAR is not an INSTANT, and code that treated the start of a yearly period as an exact event time would produce trend artifacts indistinguishable from real market movements (data-principles.md §9). An adapter supports only the forms its real records use and reports the rest rather than approximating them.
 * @see normalized-record-v1.md §7.1; Mission 1.6 §16
 */
export const NORMALIZED_PERIOD_TYPE_VALUES = [
  "YEAR",
  "QUARTER",
  "MONTH",
  "DAY",
  "INSTANT",
  "INTERVAL",
] as const;
export type NormalizedPeriodType = (typeof NORMALIZED_PERIOD_TYPE_VALUES)[number];
export function isNormalizedPeriodType(v: unknown): v is NormalizedPeriodType {
  return typeof v === "string" && (NORMALIZED_PERIOD_TYPE_VALUES as readonly string[]).includes(v);
}

/**
 * What kind of entity a source geography code names. Closed because the branch is exhaustive and consequential: a COUNTRY can join to a MarketScope country list and an AGGREGATE must never be counted as one. UNKNOWN exists because it is the safe failure -- an unclassified code keeps its source form and is never promoted to a country.
 * @see normalized-record-v1.md §7.2; Mission 1.6 §15
 */
export const NORMALIZED_GEOGRAPHY_KIND_VALUES = [
  "COUNTRY",
  "AGGREGATE",
  "UNKNOWN",
] as const;
export type NormalizedGeographyKind = (typeof NORMALIZED_GEOGRAPHY_KIND_VALUES)[number];
export function isNormalizedGeographyKind(v: unknown): v is NormalizedGeographyKind {
  return typeof v === "string" && (NORMALIZED_GEOGRAPHY_KIND_VALUES as readonly string[]).includes(v);
}

/**
 * Whether a canonical numeric observation carries a measurement. Closed and mandatory because the alternative is representing 'the source published no figure' as the number zero -- and zero is a real measurement, so the two would become permanently indistinguishable with no way for any downstream stage to recover the difference.
 * @see normalized-record-v1.md §6.2; Mission 1.6 §14
 */
export const NORMALIZED_VALUE_STATE_VALUES = [
  "REPORTED",
  "NOT_REPORTED",
  "UNREADABLE",
] as const;
export type NormalizedValueState = (typeof NORMALIZED_VALUE_STATE_VALUES)[number];
export function isNormalizedValueState(v: unknown): v is NormalizedValueState {
  return typeof v === "string" && (NORMALIZED_VALUE_STATE_VALUES as readonly string[]).includes(v);
}

/**
 * Whether a canonical numeric observation carries a unit, and why not when it does not. Closed so that 'the source does not publish units on this endpoint' stays distinguishable from 'we have not established the unit' -- the first is a settled fact about the access path and the second is work someone could do. Neither is ever resolved by reading the metric name.
 * @see normalized-record-v1.md §6.3; Mission 1.6 §17
 */
export const NORMALIZED_UNIT_STATE_VALUES = [
  "PUBLISHED",
  "NOT_PUBLISHED",
  "UNKNOWN",
] as const;
export type NormalizedUnitState = (typeof NORMALIZED_UNIT_STATE_VALUES)[number];
export function isNormalizedUnitState(v: unknown): v is NormalizedUnitState {
  return typeof v === "string" && (NORMALIZED_UNIT_STATE_VALUES as readonly string[]).includes(v);
}

/**
 * Whether the timezone of a canonical period's bounds is established. Closed because the branch is exhaustive and consequential: an ESTABLISHED period carries timezone-aware bounds and an event time, and a NOT_ESTABLISHED one carries wall-clock bounds and no event time at all. The distinction cannot be collapsed -- a source that publishes a bucket label and no offset is not the same as one that publishes UTC, and storing an aware datetime beside a note saying it is not really UTC would be a lie next to a disclaimer.
 * @see normalized-record-v1.md §7.1; Mission 1.10 §4
 */
export const NORMALIZED_TIMEZONE_STATE_VALUES = [
  "ESTABLISHED",
  "NOT_ESTABLISHED",
] as const;
export type NormalizedTimezoneState = (typeof NORMALIZED_TIMEZONE_STATE_VALUES)[number];
export function isNormalizedTimezoneState(v: unknown): v is NormalizedTimezoneState {
  return typeof v === "string" && (NORMALIZED_TIMEZONE_STATE_VALUES as readonly string[]).includes(v);
}

/**
 * Whether a source language label has been mapped to a canonical language tag. Closed for the reason NormalizedGeographyKind is: the safe failure has to be nameable. A source publishing a human-readable language name is not publishing a language tag, and a name sitting in a field whose contract means a tag is a guess wearing the clothes of a fact. The source label is preserved either way.
 * @see normalized-record-v1.md §7.3; Mission 1.10 §5
 */
export const NORMALIZED_LANGUAGE_MAPPING_VALUES = [
  "ESTABLISHED",
  "NOT_ESTABLISHED",
] as const;
export type NormalizedLanguageMapping = (typeof NORMALIZED_LANGUAGE_MAPPING_VALUES)[number];
export function isNormalizedLanguageMapping(v: unknown): v is NormalizedLanguageMapping {
  return typeof v === "string" && (NORMALIZED_LANGUAGE_MAPPING_VALUES as readonly string[]).includes(v);
}

/**
 * What kind of quantity a derived Signal is about. Closed because consumers branch exhaustively on it and the families have different scope shapes -- a lexical signal carries a term and NO geography key, a series signal carries a metric and a geography -- so an unhandled third value is a bug rather than a gap. It is deliberately NOT DemandSignalFamily: PAIN/DESIRE/BEHAVIORAL/MARKET classify demand, and a count of how often a token occurred in news text is not evidence of demand. It is also not the registry called signal_family, which says what a SOURCE could expose (ADR-017). Three relations, three subjects, three names.
 * @see signal-taxonomy-v1.md; Mission 1.11 §5
 */
export const SIGNAL_QUANTITY_FAMILY_VALUES = [
  "LEXICAL_FREQUENCY",
  "MEASURED_SERIES",
] as const;
export type SignalQuantityFamily = (typeof SIGNAL_QUANTITY_FAMILY_VALUES)[number];
export function isSignalQuantityFamily(v: unknown): v is SignalQuantityFamily {
  return typeof v === "string" && (SIGNAL_QUANTITY_FAMILY_VALUES as readonly string[]).includes(v);
}

/**
 * Which way the derived quantity moved. About CHANGE ONLY: POSITIVE and NEGATIVE are deliberately absent because they are sentiment, and a complaint-frequency signal can be INCREASING while the sentiment of the underlying text is negative -- one enum holding both would make that sentence unrepresentable. Any value other than NOT_APPLICABLE requires a temporal basis of ORDERED_PERIODS or COMPARABLE_INSTANTS, because increasing is a statement about before and after.
 * @see signal-contract-v1.md; Mission 1.11 §33
 */
export const SIGNAL_DIRECTION_VALUES = [
  "INCREASING",
  "DECREASING",
  "UNCHANGED",
  "INDETERMINATE",
  "NOT_APPLICABLE",
] as const;
export type SignalDirection = (typeof SIGNAL_DIRECTION_VALUES)[number];
export function isSignalDirection(v: unknown): v is SignalDirection {
  return typeof v === "string" && (SIGNAL_DIRECTION_VALUES as readonly string[]).includes(v);
}

/**
 * How to read a Signal's magnitude. Closed because a ratio of 2 and a difference of 2 are not the same fact, and a consumer that could not tell them apart would compare them. There is no LEVEL value: a level is one observation, and one observation is not a Signal.
 * @see signal-contract-v1.md; Mission 1.11 §33
 */
export const SIGNAL_MAGNITUDE_KIND_VALUES = [
  "ABSOLUTE_CHANGE",
  "ABSOLUTE_DIFFERENCE",
  "RATIO",
  "OBSERVATION_COUNT",
] as const;
export type SignalMagnitudeKind = (typeof SIGNAL_MAGNITUDE_KIND_VALUES)[number];
export function isSignalMagnitudeKind(v: unknown): v is SignalMagnitudeKind {
  return typeof v === "string" && (SIGNAL_MAGNITUDE_KIND_VALUES as readonly string[]).includes(v);
}

/**
 * Whether a Signal's magnitude carries a unit, and why not when it does not. The counterpart of NormalizedUnitState one layer up, and it exists for the same reason: GDELT publishes four columns and none is a unit, so a change over GDELT counts has no unit to inherit. Naming one here would assert the source did something it did not.
 * @see signal-contract-v1.md; Mission 1.11 §33
 */
export const SIGNAL_MAGNITUDE_UNIT_STATE_VALUES = [
  "INHERITED",
  "DIMENSIONLESS",
  "NOT_ESTABLISHED",
] as const;
export type SignalMagnitudeUnitState = (typeof SIGNAL_MAGNITUDE_UNIT_STATE_VALUES)[number];
export function isSignalMagnitudeUnitState(v: unknown): v is SignalMagnitudeUnitState {
  return typeof v === "string" && (SIGNAL_MAGNITUDE_UNIT_STATE_VALUES as readonly string[]).includes(v);
}

/**
 * What temporal relation a derivation actually used. Closed and consequential: ORDER and GLOBAL INSTANT are different questions needing different evidence, and collapsing them is how a timezone gets invented. Only COMPARABLE_INSTANTS may carry window bounds or leave observed_at non-null; every other basis carries neither.
 * @see signal-temporal-semantics-v1.md; Mission 1.11 §12, §13
 */
export const SIGNAL_TEMPORAL_BASIS_VALUES = [
  "NONE",
  "SAME_PERIOD_LABEL",
  "ORDERED_PERIODS",
  "COMPARABLE_INSTANTS",
] as const;
export type SignalTemporalBasis = (typeof SIGNAL_TEMPORAL_BASIS_VALUES)[number];
export function isSignalTemporalBasis(v: unknown): v is SignalTemporalBasis {
  return typeof v === "string" && (SIGNAL_TEMPORAL_BASIS_VALUES as readonly string[]).includes(v);
}

/**
 * A canonical fact a derivation declares it needs. Closed because each value maps to a specific set of NormalizationQualityReason values that withhold it and to the record kinds that can supply it, so the check is mechanical rather than a judgement. The point is that PARTIAL must not automatically mean unusable: what matters is whether the SPECIFIC missing fact matters to the SPECIFIC derivation.
 * @see signal-contract-v1.md §10; Mission 1.11 §11
 */
export const SIGNAL_REQUIRED_FACT_VALUES = [
  "EXACT_NUMERIC_VALUE",
  "LEXICAL_TERM",
  "SOURCE_PERIOD_LABEL",
  "SOURCE_RELATIVE_ORDER",
  "COMPARABLE_INSTANT",
  "SOURCE_LANGUAGE_LABEL",
  "CANONICAL_LANGUAGE",
  "CLASSIFIED_GEOGRAPHY",
] as const;
export type SignalRequiredFact = (typeof SIGNAL_REQUIRED_FACT_VALUES)[number];
export function isSignalRequiredFact(v: unknown): v is SignalRequiredFact {
  return typeof v === "string" && (SIGNAL_REQUIRED_FACT_VALUES as readonly string[]).includes(v);
}

/**
 * How a Signal was produced. Closed and mandatory so that a Signal not being inherently LLM-generated is a constraint rather than a sentence: DETERMINISTIC requires model and prompt versions to be ABSENT, and MODEL_DERIVED requires a model version.
 * @see signal-contract-v1.md §8; Mission 1.11 §23
 */
export const SIGNAL_DERIVATION_KIND_VALUES = [
  "DETERMINISTIC",
  "MODEL_DERIVED",
] as const;
export type SignalDerivationKind = (typeof SIGNAL_DERIVATION_KIND_VALUES)[number];
export function isSignalDerivationKind(v: unknown): v is SignalDerivationKind {
  return typeof v === "string" && (SIGNAL_DERIVATION_KIND_VALUES as readonly string[]).includes(v);
}

/**
 * Whether an input actually entered the derivation. Excluded inputs are recorded rather than dropped: we looked at ten and used six must be visible, and a signal that quietly used six of ten is indistinguishable from one that was offered six.
 * @see signal-contract-v1.md §9; Mission 1.11 §19
 */
export const SIGNAL_INPUT_ROLE_VALUES = [
  "CONTRIBUTED",
  "EXCLUDED",
] as const;
export type SignalInputRole = (typeof SIGNAL_INPUT_ROLE_VALUES)[number];
export function isSignalInputRole(v: unknown): v is SignalInputRole {
  return typeof v === "string" && (SIGNAL_INPUT_ROLE_VALUES as readonly string[]).includes(v);
}

/**
 * Why an input was excluded, or why a whole derivation produced no Signal. One vocabulary for both, because a refused derivation is usually an exclusion having happened often enough. A refusal is a RETURNED VALUE, never a row: a record in a table of signals says a signal exists, and one meaning no signal exists is a misleading signal.
 * @see signal-contract-v1.md §11; Mission 1.11 §27
 */
export const SIGNAL_REFUSAL_REASON_VALUES = [
  "INPUT_RECORD_INVALID",
  "REQUIRED_FACT_WITHHELD",
  "AMBIGUOUS_OBSERVATION_LINEAGE",
  "INCOMPATIBLE_INPUT_KINDS",
  "INCOMPATIBLE_SERIES",
  "NON_CONTIGUOUS_SOURCE_BUCKETS",
  "INSUFFICIENT_INPUT_OBSERVATIONS",
  "UNSUPPORTED_SIGNAL_TYPE",
  "PARAMETERS_INCOMPLETE",
] as const;
export type SignalRefusalReason = (typeof SIGNAL_REFUSAL_REASON_VALUES)[number];
export function isSignalRefusalReason(v: unknown): v is SignalRefusalReason {
  return typeof v === "string" && (SIGNAL_REFUSAL_REASON_VALUES as readonly string[]).includes(v);
}

/**
 * How a Claim's proposition was produced from Signals. Closed and mandatory wherever an interpreter was involved, so that 'an LLM is a reasoning mechanism and not a market-data source' is a constraint rather than a sentence: DETERMINISTIC requires model and prompt versions to be ABSENT, and MODEL_DERIVED requires a model version. It is the claim-layer counterpart of SignalDerivationKind, and the same defect it fixes -- a table whose only producer identity is a model version reads as a table of model outputs.
 * @see claim-evidence-interpretation-contract-v1.md §6; Mission 1.13 §20
 */
export const CLAIM_INTERPRETATION_KIND_VALUES = [
  "DETERMINISTIC",
  "MODEL_DERIVED",
] as const;
export type ClaimInterpretationKind = (typeof CLAIM_INTERPRETATION_KIND_VALUES)[number];
export function isClaimInterpretationKind(v: unknown): v is ClaimInterpretationKind {
  return typeof v === "string" && (CLAIM_INTERPRETATION_KIND_VALUES as readonly string[]).includes(v);
}

/**
 * Why an interpretation produced no Claim. A RETURNED VALUE, never a row: a claim stored to record that no claim could be made is exactly the unsupported assertion this layer exists to prevent, and a claim table row saying 'nothing' is worse than no row.
 * @see claim-evidence-interpretation-contract-v1.md §11; Mission 1.13 §22
 */
export const CLAIM_EVIDENCE_REFUSAL_REASON_VALUES = [
  "NO_SUPPORTING_SIGNAL",
  "UNSUPPORTED_INTERPRETATION",
  "SIGNAL_NOT_CITED",
  "INCOMPATIBLE_TEMPORAL_SEMANTICS",
  "INCOMPATIBLE_LANGUAGE_SEMANTICS",
  "PROPOSITION_NOT_IDENTIFIABLE",
  "INTERPRETER_PROVENANCE_INCOMPLETE",
] as const;
export type ClaimEvidenceRefusalReason = (typeof CLAIM_EVIDENCE_REFUSAL_REASON_VALUES)[number];
export function isClaimEvidenceRefusalReason(v: unknown): v is ClaimEvidenceRefusalReason {
  return typeof v === "string" && (CLAIM_EVIDENCE_REFUSAL_REASON_VALUES as readonly string[]).includes(v);
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
  "normalization_record_kind",
  "signal_family",
  "signal_type",
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
