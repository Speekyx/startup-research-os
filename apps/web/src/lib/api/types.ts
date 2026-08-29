/**
 * Typed gateway responses.
 *
 * **Domain vocabulary is imported, never redeclared.** `ResearchSessionStatus`
 * and the identifier brands come from `@sros/contracts`, which is generated
 * from the one source of truth (ADR-009). Retyping them here would recreate
 * audit C-02 — the claims taxonomy defined twice with different values — in the
 * place it is hardest to notice, because the frontend copy would only be wrong
 * for users.
 *
 * A lint rule refuses a local redeclaration of any canonical enum
 * (`packages/eslint-config`), so this is enforced rather than remembered.
 */

import type {
  ResearchProjectId,
  ResearchSessionId,
  ResearchSessionStatus,
  WorkspaceId,
} from "@sros/contracts";

/** The gateway's single error shape. Every failure looks like this. */
export interface GatewayErrorBody {
  readonly error: string;
  readonly detail: string;
  readonly correlation_id: string;
}

export interface HealthResponse {
  readonly status: string;
  readonly service: string;
  readonly environment: string;
}

export interface ReadinessResponse {
  readonly status: "ready" | "not_ready";
  readonly dependencies: Readonly<Record<string, string>>;
  readonly optional_dependencies: Readonly<Record<string, string>>;
  /** RLS posture, reported rather than assumed (ADR-012). */
  readonly security: Readonly<Record<string, string>>;
  readonly correlation_id: string;
}

export interface ResearchProject {
  readonly id: ResearchProjectId;
  readonly workspace_id: WorkspaceId;
  readonly name: string;
  readonly description: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface ResearchSession {
  readonly id: ResearchSessionId;
  readonly workspace_id: WorkspaceId;
  readonly project_id: ResearchProjectId;
  readonly status: ResearchSessionStatus;

  /** The immutable snapshot, exactly as persisted (Ontology V2 §11.3). */
  readonly research_context: Readonly<Record<string, unknown>>;
  readonly research_context_hash: string;
  readonly research_context_schema_version: string;

  readonly created_at: string;
  readonly started_at: string | null;
  readonly completed_at: string | null;

  /**
   * A score family on 0–100 (`scoring-framework-v1.1.md` §4.1), NOT a
   * confidence. Null until scoring runs, which D-03 blocks — and a null here
   * must render as "not computed", never as zero.
   */
  readonly research_completeness_score: number | null;
}

export interface CreateResearchProjectInput {
  readonly name: string;
  readonly description?: string;
}

export interface CreateResearchSessionInput {
  readonly research_context: Record<string, unknown>;
}
