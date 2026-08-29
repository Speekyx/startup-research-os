/**
 * Gateway API client tests.
 *
 * Runs on a bare Node runtime with native type stripping — no bundler, no build
 * step, no browser — because every cross-package import in the client is
 * type-only and therefore erased. Same argument as ADR-009: a check that needs a
 * build is a check that gets skipped when the build is what is broken.
 *
 *     node --test --experimental-strip-types apps/web/test/api-client.test.ts
 *
 * `fetch` is stubbed. These tests assert what the client SENDS and how it
 * interprets what comes back; `src/lib/api/smoke.ts` is what proves those
 * assumptions match a real gateway.
 */

import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";

import { GatewayClient } from "../src/lib/api/client.ts";
import { loadConfig } from "../src/lib/api/config.ts";
import { ConfigurationError } from "../src/lib/api/config.ts";
import {
  GatewayError,
  GatewayUnreachableError,
  MalformedResponseError,
} from "../src/lib/api/errors.ts";

const WORKSPACE = "00000000-0000-4000-8000-000000000001";

interface Call {
  url: string;
  init: RequestInit;
}

const realFetch = globalThis.fetch;
let calls: Call[] = [];

function stubFetch(responses: Response[] | (() => Promise<Response>)): void {
  calls = [];
  const queue = Array.isArray(responses) ? [...responses] : null;
  globalThis.fetch = ((url: string, init: RequestInit) => {
    calls.push({ url: String(url), init });
    if (queue) {
      const next = queue.shift();
      if (!next) throw new Error("unscripted fetch call");
      return Promise.resolve(next);
    }
    return (responses as () => Promise<Response>)();
  }) as typeof fetch;
}

function json(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...headers },
  });
}

function client(overrides: Partial<ReturnType<typeof loadConfig>> = {}): GatewayClient {
  return new GatewayClient({
    gatewayUrl: "http://127.0.0.1:8412",
    devWorkspaceId: WORKSPACE,
    requestTimeoutMs: 5000,
    ...overrides,
  });
}

afterEach(() => {
  globalThis.fetch = realFetch;
});

describe("configuration", () => {
  it("reads the gateway url from the environment and strips a trailing slash", () => {
    const config = loadConfig({ NEXT_PUBLIC_GATEWAY_URL: "http://127.0.0.1:9999///" });
    assert.equal(config.gatewayUrl, "http://127.0.0.1:9999");
  });

  it("refuses a relative gateway url", () => {
    assert.throws(
      () => loadConfig({ NEXT_PUBLIC_GATEWAY_URL: "/api" }),
      ConfigurationError,
    );
  });

  it("refuses a non-positive timeout, because there are no unbounded requests", () => {
    assert.throws(
      () => loadConfig({ NEXT_PUBLIC_REQUEST_TIMEOUT_MS: "0" }),
      ConfigurationError,
    );
  });
});

describe("headers are built in exactly one place (§31)", () => {
  it("sends the workspace header on every request without a component naming it", async () => {
    stubFetch([json([]), json([])]);
    const api = client();
    await api.listProjects();
    await api.health();

    for (const call of calls) {
      const headers = call.init.headers as Record<string, string>;
      assert.equal(headers["x-workspace-id"], WORKSPACE);
    }
  });

  it("omits the workspace header when none is configured", async () => {
    stubFetch([json([])]);
    await client({ devWorkspaceId: null }).listProjects();
    const headers = calls[0]?.init.headers as Record<string, string>;
    assert.equal(headers["x-workspace-id"], undefined);
  });

  it("exposes no way for a caller to inject its own headers", () => {
    // The surface is the assertion: a client that accepted per-call headers
    // would scatter the workspace across the component tree, and removing it
    // when authentication arrives would mean finding every one of them.
    const surface = Object.getOwnPropertyNames(GatewayClient.prototype);
    assert.ok(!surface.includes("request"));
    assert.ok(!surface.includes("headers"));
  });
});

describe("correlation", () => {
  it("generates an id when the caller supplies none", async () => {
    stubFetch([json([])]);
    await client().listProjects();
    const headers = calls[0]?.init.headers as Record<string, string>;
    assert.ok(headers["x-correlation-id"]);
  });

  it("uses the caller's id so several calls share one user action", async () => {
    stubFetch([json([]), json([])]);
    const api = client();
    await api.listProjects({ correlationId: "one-action" });
    await api.health({ correlationId: "one-action" });

    for (const call of calls) {
      const headers = call.init.headers as Record<string, string>;
      assert.equal(headers["x-correlation-id"], "one-action");
    }
  });

  it("attaches the server's id to an error, because that is the one in its logs", async () => {
    stubFetch([
      json(
        { error: "not_found", detail: "no such session", correlation_id: "server-side-id" },
        404,
        { "x-correlation-id": "server-side-id" },
      ),
    ]);
    await assert.rejects(
      () => client().getSession("00000000-0000-4000-8000-00000000dead"),
      (error: unknown) => {
        assert.ok(error instanceof GatewayError);
        assert.equal(error.correlationId, "server-side-id");
        assert.ok(error.isNotFound);
        return true;
      },
    );
  });
});

describe("error interpretation", () => {
  it("maps the gateway's four error codes onto branchable properties", async () => {
    const cases = [
      [400, "workspace_required", "isWorkspaceRequired"],
      [404, "not_found", "isNotFound"],
      [409, "invalid_transition", "isInvalidTransition"],
      [422, "contract_violation", "isContractViolation"],
    ] as const;

    for (const [status, code, property] of cases) {
      stubFetch([json({ error: code, detail: "d", correlation_id: "c" }, status)]);
      await assert.rejects(
        () => client().listProjects(),
        (error: unknown) => {
          assert.ok(error instanceof GatewayError);
          assert.equal(error.status, status);
          assert.equal(error[property], true);
          return true;
        },
      );
    }
  });

  it("distinguishes a server that said no from something that is not the gateway", async () => {
    // A proxy or a captive portal answering with HTML is a real failure mode,
    // and treating it as a server-side bug sends the reader to the wrong logs.
    stubFetch([new Response("<html>502</html>", { status: 502 })]);
    await assert.rejects(() => client().listProjects(), MalformedResponseError);
  });

  it("reports an unreachable gateway distinctly from a rejected request", async () => {
    stubFetch(() => Promise.reject(new TypeError("failed to fetch")));
    await assert.rejects(() => client().listProjects(), GatewayUnreachableError);
  });
});

describe("readiness", () => {
  it("returns the dependency report on 503 rather than raising", async () => {
    // Regression test. The first version raised MalformedResponseError here,
    // because /ready is the one endpoint that answers a non-2xx with its own
    // body instead of the gateway's error shape — so a status page had no way
    // to learn WHICH dependency was down, which is the only thing it needed.
    // Found by running the client against a live gateway, not by typechecking.
    stubFetch([
      json(
        {
          status: "not_ready",
          dependencies: { postgres: "ok", redis: "unavailable" },
          optional_dependencies: { qdrant: "ok" },
          security: { rls_policies: "active", app_db_role: "sros_app" },
          correlation_id: "c",
        },
        503,
      ),
    ]);

    const readiness = await client().readiness();
    assert.equal(readiness.status, "not_ready");
    assert.equal(readiness.dependencies.redis, "unavailable");
    assert.equal(readiness.security.rls_policies, "active");
  });

  it("still raises on a status it did not opt into", async () => {
    stubFetch([json({ error: "not_found", detail: "d", correlation_id: "c" }, 404)]);
    await assert.rejects(() => client().readiness(), GatewayError);
  });
});

describe("request shape", () => {
  it("sends no body on a GET", async () => {
    stubFetch([json([])]);
    await client().listProjects();
    assert.equal(calls[0]?.init.body, undefined);
  });

  it("sends a JSON body on a POST", async () => {
    stubFetch([json({ id: "x" }, 201)]);
    await client().createProject({ name: "a project" });
    assert.equal(calls[0]?.init.body, JSON.stringify({ name: "a project" }));
  });

  it("encodes path parameters", async () => {
    stubFetch([json({})]);
    await client().getProject("a/b?c");
    assert.ok(calls[0]?.url.endsWith("/api/v1/research-projects/a%2Fb%3Fc"));
  });

  it("has no method that could mutate a context snapshot", () => {
    // Ontology V2 §11.3: a new specification means a new session. The gateway
    // has no such route either, so a method here would fail at runtime rather
    // than at compile time — which is why the absence is asserted.
    const surface = Object.getOwnPropertyNames(GatewayClient.prototype);
    for (const forbidden of ["updateSession", "patchSession", "updateSessionContext"]) {
      assert.ok(!surface.includes(forbidden), `${forbidden} must not exist`);
    }
  });
});
