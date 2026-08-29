/**
 * A runnable check that the API client actually talks to the gateway.
 *
 * Not a unit test: it needs the stack and a running gateway, which is exactly
 * why it exists. `tsc` proves the types line up with what the client *claims*
 * the gateway returns; only a real call proves they line up with what it
 * *does* return. Mission 0.3 found three defects that no amount of static
 * checking could have caught, and this is the same argument applied to the web
 * boundary.
 *
 *     uv run uvicorn "sros_gateway.app:create_app" --factory --port 8412
 *     NEXT_PUBLIC_DEV_WORKSPACE_ID=00000000-0000-4000-8000-000000000001 \
 *       node --experimental-strip-types apps/web/src/lib/api/smoke.ts
 *
 * It runs under bare Node with type stripping — no bundler, no build step —
 * because every cross-package import in this client is type-only and therefore
 * erased. That is a property worth keeping: a check that needs a build is a
 * check that gets skipped when the build is what is broken (ADR-009).
 */

/* eslint-disable no-console -- this file IS a console program.
 *
 * `no-console` exists to stop stray debugging output reaching application code.
 * A CLI whose entire output is what it prints is the case the rule is not for,
 * and leaving eleven warnings standing would teach the next reader that warnings
 * in this repository are decorative. */

import { GatewayClient } from "./client.ts";
import { loadConfig } from "./config.ts";
import { GatewayError, GatewayUnreachableError } from "./errors.ts";

async function main(): Promise<number> {
  const config = loadConfig();
  const client = new GatewayClient(config);
  const correlationId = `smoke-${Date.now().toString(36)}`;

  console.log(`gateway: ${client.gatewayUrl}`);
  console.log(`workspace: ${config.devWorkspaceId ?? "(none — expect workspace_required)"}`);

  try {
    const health = await client.health({ correlationId });
    console.log(`health: ${health.status} (${health.service}, ${health.environment})`);

    const readiness = await client.readiness({ correlationId });
    console.log(
      `ready: ${readiness.status} deps=${JSON.stringify(readiness.dependencies)} ` +
        `security=${JSON.stringify(readiness.security)}`,
    );

    const projects = await client.listProjects({ correlationId });
    console.log(`projects: ${projects.length}`);

    const created = await client.createProject(
      { name: `web-smoke-${Date.now().toString(36)}` },
      { correlationId },
    );
    console.log(`created project ${created.id} in workspace ${created.workspace_id}`);

    const session = await client.createSession(
      created.id,
      { research_context: { market_scope: { type: "COUNTRY", countries: ["fr"] } } },
      { correlationId },
    );
    console.log(
      `created session ${session.id} status=${session.status} ` +
        `context_hash=${session.research_context_hash.slice(0, 12)} ` +
        `completeness=${session.research_completeness_score ?? "not computed"}`,
    );

    // Canonicalization happened server-side: "fr" went in, "FR" came back.
    const scope = session.research_context.market_scope as { countries?: string[] };
    console.log(`canonicalized scope: ${JSON.stringify(scope.countries)}`);

    const sessions = await client.listSessions(created.id, { correlationId });
    console.log(`sessions for project: ${sessions.length}`);

    // The error path matters as much as the happy one: a client that cannot
    // report a failure usefully is a client that produces silent blank pages.
    try {
      await client.getSession("00000000-0000-4000-8000-00000000dead", { correlationId });
      console.error("FAIL: an unknown session should not resolve");
      return 1;
    } catch (error) {
      if (!(error instanceof GatewayError) || !error.isNotFound) throw error;
      console.log(`not_found handled, correlation ${error.correlationId}`);
    }

    console.log("OK");
    return 0;
  } catch (error) {
    if (error instanceof GatewayUnreachableError) {
      console.error(`gateway unreachable: ${error.message}`);
    } else if (error instanceof GatewayError) {
      console.error(`gateway error: ${error.code} ${error.detail} [${error.correlationId}]`);
    } else {
      console.error(error);
    }
    return 1;
  }
}

process.exitCode = await main();
