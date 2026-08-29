/**
 * The gateway API client.
 *
 * Mission 0.4 §30 and §31. `apps/web` calls the gateway and nothing else
 * (`service-boundaries.md` §4 invariant 1): no datastore, no other service.
 *
 * **One place builds headers.** `#headers()` is private, and every method goes
 * through `#request`. That is the §31 requirement stated as a structural
 * property rather than a convention: when authentication arrives, an
 * `Authorization` header is added in exactly one method, and no component
 * changes. A client that let call sites pass their own headers would scatter
 * the workspace across the component tree, and removing it later would mean
 * finding every one of them.
 *
 * **Every request carries a correlation id**, generated here when the caller
 * does not supply one, and attached to every error. `RequestContext.task_headers`
 * on the server propagates the same id through HTTP → queue → worker, so one id
 * traces a user action across the whole system (ADR-004, ADR-005).
 *
 * **Every request has a timeout.** An unbounded fetch in a browser is a tab
 * that spins forever with no error to report.
 */

import { loadConfig, type WebConfig } from "./config.ts";
import {
  GatewayError,
  GatewayUnreachableError,
  MalformedResponseError,
  isGatewayErrorBody,
} from "./errors.ts";
import type {
  CreateResearchProjectInput,
  CreateResearchSessionInput,
  HealthResponse,
  ReadinessResponse,
  ResearchProject,
  ResearchSession,
} from "./types.ts";

const CORRELATION_HEADER = "x-correlation-id";
const WORKSPACE_HEADER = "x-workspace-id";

export interface RequestOptions {
  /** Supply one to tie several calls to a single user action. */
  readonly correlationId?: string;
  readonly signal?: AbortSignal;
}

function newCorrelationId(): string {
  // `crypto.randomUUID` needs a secure context; a plain fallback is fine
  // because this id is for tracing, never for authentication or secrecy.
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `web-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export class GatewayClient {
  readonly #config: WebConfig;

  constructor(config: WebConfig = loadConfig()) {
    this.#config = config;
  }

  get gatewayUrl(): string {
    return this.#config.gatewayUrl;
  }

  /**
   * The ONLY place request headers are assembled.
   *
   * The workspace header is temporary and lives here alone (ADR-005): while
   * authentication does not exist the gateway accepts one, and when it does
   * the server resolves the workspace from the session and this line is
   * deleted without touching a single component.
   */
  #headers(correlationId: string): Record<string, string> {
    const headers: Record<string, string> = {
      "content-type": "application/json",
      [CORRELATION_HEADER]: correlationId,
    };
    if (this.#config.devWorkspaceId) {
      headers[WORKSPACE_HEADER] = this.#config.devWorkspaceId;
    }
    return headers;
  }

  async #request<T>(
    path: string,
    init: { method: string; body?: unknown; accept?: readonly number[] },
    options: RequestOptions = {},
  ): Promise<T> {
    const correlationId = options.correlationId ?? newCorrelationId();
    const controller = new AbortController();
    const timer = setTimeout(() => {
      controller.abort();
    }, this.#config.requestTimeoutMs);

    if (options.signal) {
      options.signal.addEventListener("abort", () => {
        controller.abort();
      });
    }

    // Built conditionally rather than with `body: undefined`:
    // `exactOptionalPropertyTypes` distinguishes "absent" from "present and
    // undefined", and a GET with an explicitly undefined body is the second.
    const request: RequestInit = {
      method: init.method,
      headers: this.#headers(correlationId),
      signal: controller.signal,
      cache: "no-store",
    };
    if (init.body !== undefined) {
      request.body = JSON.stringify(init.body);
    }

    let response: Response;
    try {
      response = await fetch(`${this.#config.gatewayUrl}${path}`, request);
    } catch (cause) {
      throw new GatewayUnreachableError(
        `could not reach the gateway at ${this.#config.gatewayUrl}${path}`,
        correlationId,
        { cause },
      );
    } finally {
      clearTimeout(timer);
    }

    // The server's id wins when present: it is the one that appears in the
    // server's logs, which is where the reader of an error will look.
    const serverCorrelationId = response.headers.get(CORRELATION_HEADER) ?? correlationId;

    let payload: unknown = null;
    const text = await response.text();
    if (text) {
      try {
        payload = JSON.parse(text) as unknown;
      } catch {
        throw new MalformedResponseError(
          `the gateway returned a non-JSON body with status ${response.status}`,
          serverCorrelationId,
        );
      }
    }

    // A status the caller declared meaningful is returned as a payload rather
    // than raised. Only `/ready` uses this, and it has to: it answers a 503
    // with a dependency report, which is exactly the information a caller
    // wants and would lose if the status alone decided the outcome.
    const accepted = init.accept?.includes(response.status) ?? false;

    if (!response.ok && !accepted) {
      if (isGatewayErrorBody(payload)) {
        throw new GatewayError(response.status, payload);
      }
      throw new MalformedResponseError(
        `status ${response.status} with no recognisable error body`,
        serverCorrelationId,
      );
    }

    return payload as T;
  }

  // -- infrastructure ------------------------------------------------------

  /**
   * Process liveness. Consults no dependency, and neither should a caller's
   * interpretation of it: a healthy process with a down database is a real and
   * meaningful state.
   */
  health(options?: RequestOptions): Promise<HealthResponse> {
    return this.#request<HealthResponse>("/health", { method: "GET" }, options);
  }

  /**
   * Dependency readiness.
   *
   * Returns the payload **even on 503**, because "not ready, and here is which
   * dependency" is the useful answer — and it is the only answer a status page
   * can act on. A 503 here is a result, not a failure.
   *
   * `/ready` is the one endpoint that answers a non-2xx with its own body
   * rather than the gateway's error shape, so it is the one endpoint that opts
   * into `accept`. Everything else keeps the single-error-shape rule.
   */
  readiness(options?: RequestOptions): Promise<ReadinessResponse> {
    return this.#request<ReadinessResponse>(
      "/ready",
      { method: "GET", accept: [503] },
      options,
    );
  }

  // -- research projects ---------------------------------------------------

  listProjects(options?: RequestOptions): Promise<ResearchProject[]> {
    return this.#request<ResearchProject[]>(
      "/api/v1/research-projects",
      { method: "GET" },
      options,
    );
  }

  getProject(projectId: string, options?: RequestOptions): Promise<ResearchProject> {
    return this.#request<ResearchProject>(
      `/api/v1/research-projects/${encodeURIComponent(projectId)}`,
      { method: "GET" },
      options,
    );
  }

  createProject(
    input: CreateResearchProjectInput,
    options?: RequestOptions,
  ): Promise<ResearchProject> {
    return this.#request<ResearchProject>(
      "/api/v1/research-projects",
      { method: "POST", body: input },
      options,
    );
  }

  // -- research sessions ---------------------------------------------------

  listSessions(projectId: string, options?: RequestOptions): Promise<ResearchSession[]> {
    return this.#request<ResearchSession[]>(
      `/api/v1/research-projects/${encodeURIComponent(projectId)}/sessions`,
      { method: "GET" },
      options,
    );
  }

  getSession(sessionId: string, options?: RequestOptions): Promise<ResearchSession> {
    return this.#request<ResearchSession>(
      `/api/v1/research-sessions/${encodeURIComponent(sessionId)}`,
      { method: "GET" },
      options,
    );
  }

  /**
   * Create the execution RECORD. No research runs.
   *
   * There is deliberately no `updateSessionContext`: the snapshot is the
   * reproducibility guarantee, and a new specification means a new session
   * (Ontology V2 §11.3). The gateway has no such route either, so adding one
   * here would fail at runtime rather than compile time — which is why the
   * absence is stated instead of left to be noticed.
   */
  createSession(
    projectId: string,
    input: CreateResearchSessionInput,
    options?: RequestOptions,
  ): Promise<ResearchSession> {
    return this.#request<ResearchSession>(
      `/api/v1/research-projects/${encodeURIComponent(projectId)}/sessions`,
      { method: "POST", body: input },
      options,
    );
  }
}
