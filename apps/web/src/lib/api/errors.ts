/**
 * Client-side error types.
 *
 * The gateway returns one error shape for every failure
 * (`services/gateway/README.md` §Error shape), and this file is where it stops
 * being JSON and becomes something a component can branch on.
 *
 * **Every error carries the correlation id.** That is the whole reason the
 * gateway echoes `x-correlation-id` on every response: a user reporting "it
 * failed" with an id turns an unreproducible bug into a log query.
 */

import type { GatewayErrorBody } from "./types.ts";

export class GatewayError extends Error {
  readonly status: number;
  readonly code: string;
  readonly detail: string;
  readonly correlationId: string;

  constructor(status: number, body: GatewayErrorBody) {
    super(`${body.error}: ${body.detail}`);
    this.name = "GatewayError";
    this.status = status;
    this.code = body.error;
    this.detail = body.detail;
    this.correlationId = body.correlation_id;
  }

  /**
   * No workspace in context.
   *
   * 400 rather than 401 on purpose: authentication does not exist, and a
   * misleading 401 would send a reader looking for a login problem.
   */
  get isWorkspaceRequired(): boolean {
    return this.code === "workspace_required";
  }

  /** Absent, or belonging to another workspace — deliberately indistinguishable. */
  get isNotFound(): boolean {
    return this.code === "not_found";
  }

  /** A domain contract rejected the input (422). */
  get isContractViolation(): boolean {
    return this.code === "contract_violation";
  }

  /** A session lifecycle transition Ontology V2 §15 does not allow (409). */
  get isInvalidTransition(): boolean {
    return this.code === "invalid_transition";
  }
}

/** The gateway could not be reached, or did not answer in time. */
export class GatewayUnreachableError extends Error {
  readonly correlationId: string;

  constructor(message: string, correlationId: string, options?: { cause?: unknown }) {
    super(message, options);
    this.name = "GatewayUnreachableError";
    this.correlationId = correlationId;
  }
}

/**
 * The response was not the shape the client expected.
 *
 * Distinct from `GatewayError`: that one means the server said no in the agreed
 * language, this one means something answered that is not the gateway — a
 * proxy, a captive portal, a stale deployment. Treating the two the same would
 * make a misconfigured URL look like a server-side bug.
 */
export class MalformedResponseError extends Error {
  readonly correlationId: string;

  constructor(message: string, correlationId: string) {
    super(message);
    this.name = "MalformedResponseError";
    this.correlationId = correlationId;
  }
}

export function isGatewayErrorBody(value: unknown): value is GatewayErrorBody {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.error === "string" &&
    typeof candidate.detail === "string" &&
    typeof candidate.correlation_id === "string"
  );
}
