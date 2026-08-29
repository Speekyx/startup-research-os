/**
 * The gateway API client (Mission 0.4 §30).
 *
 * `apps/web` calls the gateway and nothing else. Import from here rather than
 * from the individual modules, so the surface a component may use stays visible
 * in one place.
 */

export { GatewayClient, type RequestOptions } from "./client.ts";
export { ConfigurationError, loadConfig, type WebConfig } from "./config.ts";
export {
  GatewayError,
  GatewayUnreachableError,
  MalformedResponseError,
  isGatewayErrorBody,
} from "./errors.ts";
export type {
  CreateResearchProjectInput,
  CreateResearchSessionInput,
  GatewayErrorBody,
  HealthResponse,
  ReadinessResponse,
  ResearchProject,
  ResearchSession,
} from "./types.ts";
