/**
 * Web application configuration.
 *
 * ADR-007 portability rule 1: configuration comes from the environment, never
 * from a file baked into an image and never from a constant in code.
 *
 * Every variable is read HERE and nowhere else. A component reading
 * `process.env` directly is a component that works in development and fails
 * silently in a build where the variable was not inlined — Next.js only
 * substitutes `NEXT_PUBLIC_*` references it can see statically.
 */

export interface WebConfig {
  /** Base URL of the gateway. No trailing slash. */
  readonly gatewayUrl: string;
  /**
   * The workspace this browser session acts as.
   *
   * TEMPORARY, and the only reason it exists is that authentication does not
   * (ADR-005, Mission 0.4 §31). When it arrives, the workspace comes from the
   * authenticated session and this field disappears — which is safe precisely
   * because no component reads it: only `GatewayClient` does.
   */
  readonly devWorkspaceId: string | null;
  readonly requestTimeoutMs: number;
}

export class ConfigurationError extends Error {}

const DEFAULT_GATEWAY_URL = "http://127.0.0.1:8412";

/**
 * `127.0.0.1`, never `localhost`.
 *
 * Measured in Mission 0.3: on Windows `localhost` resolves to `::1` first and
 * Docker publishes on IPv4 only, so every connection paid a ~15 second IPv6
 * timeout before falling back. 0.01s versus 15.05s.
 */
export function loadConfig(env: Record<string, string | undefined> = process.env): WebConfig {
  const gatewayUrl = (env.NEXT_PUBLIC_GATEWAY_URL ?? DEFAULT_GATEWAY_URL).replace(/\/+$/, "");

  if (!/^https?:\/\//.test(gatewayUrl)) {
    throw new ConfigurationError(
      `NEXT_PUBLIC_GATEWAY_URL must be an absolute http(s) URL, got ${gatewayUrl}`,
    );
  }

  const timeout = Number(env.NEXT_PUBLIC_REQUEST_TIMEOUT_MS ?? "10000");
  if (!Number.isFinite(timeout) || timeout <= 0) {
    throw new ConfigurationError(
      "NEXT_PUBLIC_REQUEST_TIMEOUT_MS must be a positive number. There are no unbounded requests.",
    );
  }

  return {
    gatewayUrl,
    devWorkspaceId: env.NEXT_PUBLIC_DEV_WORKSPACE_ID || null,
    requestTimeoutMs: timeout,
  };
}
