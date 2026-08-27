/**
 * Typed identifiers.
 *
 * The branded types come from the generated vocabulary. This module adds the
 * runtime constructors that validate format at the boundary, so an id that
 * reached the system from JSON is checked once rather than trusted everywhere.
 *
 * The branding matters: a `WorkspaceId` accepted where an `OpportunityId` was
 * expected is a bug the type system should catch, and in a multi-tenant system
 * that mix-up has a data-leak shape (ADR-005).
 */

import { ContractError } from "./errors.ts";
import type {
  EvidenceId,
  OpportunityId,
  ResearchProjectId,
  ResearchSessionId,
  SignalId,
  SourceId,
  UserId,
  WorkspaceId,
} from "./generated/domain.ts";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SLUG_PATTERN = /^[a-z0-9][a-z0-9._-]{0,127}$/;

function uuidId<T extends string>(name: string, value: unknown): T {
  if (typeof value !== "string") {
    throw new ContractError(name, `expected a string, got ${typeof value}`);
  }
  if (!UUID_PATTERN.test(value)) {
    throw new ContractError(name, `not a valid UUID: ${JSON.stringify(value)}`);
  }
  return value.toLowerCase() as T;
}

export const userId = (v: unknown): UserId => uuidId<UserId>("UserId", v);
export const workspaceId = (v: unknown): WorkspaceId => uuidId<WorkspaceId>("WorkspaceId", v);
export const researchProjectId = (v: unknown): ResearchProjectId =>
  uuidId<ResearchProjectId>("ResearchProjectId", v);
export const researchSessionId = (v: unknown): ResearchSessionId =>
  uuidId<ResearchSessionId>("ResearchSessionId", v);
export const opportunityId = (v: unknown): OpportunityId =>
  uuidId<OpportunityId>("OpportunityId", v);
export const evidenceId = (v: unknown): EvidenceId => uuidId<EvidenceId>("EvidenceId", v);
export const signalId = (v: unknown): SignalId => uuidId<SignalId>("SignalId", v);

export function sourceId(value: unknown): SourceId {
  if (typeof value !== "string") {
    throw new ContractError("SourceId", `expected a string, got ${typeof value}`);
  }
  if (!SLUG_PATTERN.test(value)) {
    throw new ContractError(
      "SourceId",
      `must be a lowercase stable slug matching ${SLUG_PATTERN.source}, got ${JSON.stringify(value)}`,
    );
  }
  return value as SourceId;
}
