"use client";

import { useCallback, useEffect, useState } from "react";

import {
  GatewayClient,
  GatewayError,
  GatewayUnreachableError,
  type HealthResponse,
  type ReadinessResponse,
  type ResearchProject,
  type ResearchSession,
} from "@/lib/api";

/**
 * Development status page.
 *
 * Mission 0.4 §30 permits a simple page showing API health, readiness, projects
 * and sessions, and says to keep the UI intentionally minimal. This is that page
 * and nothing more: it renders what the gateway returns, in a table, unstyled.
 *
 * It is a **client** component so that the fetches happen in the browser
 * against the browser's view of the gateway. Rendering it on the server would
 * hide exactly the class of problem this page exists to surface — a
 * misconfigured `NEXT_PUBLIC_GATEWAY_URL`, a CORS refusal, a workspace header
 * that never arrives.
 *
 * Note what it does NOT do: no component here builds a header or knows a
 * workspace exists. That is §31 — when authentication arrives, one method in
 * `GatewayClient` changes and this file does not.
 */

type Panel<T> = { state: "loading" } | { state: "ok"; data: T } | { state: "error"; message: string };

function describe(error: unknown): string {
  if (error instanceof GatewayError) {
    // The correlation id is the point: it turns "it failed" into a log query.
    return `${error.code} (${error.status}) — ${error.detail} [correlation ${error.correlationId}]`;
  }
  if (error instanceof GatewayUnreachableError) {
    return `${error.message} [correlation ${error.correlationId}]`;
  }
  return error instanceof Error ? error.message : String(error);
}

export default function DevStatusPage() {
  const [health, setHealth] = useState<Panel<HealthResponse>>({ state: "loading" });
  const [readiness, setReadiness] = useState<Panel<ReadinessResponse>>({ state: "loading" });
  const [projects, setProjects] = useState<Panel<ResearchProject[]>>({ state: "loading" });
  const [sessions, setSessions] = useState<Panel<ResearchSession[]>>({ state: "loading" });

  const load = useCallback(async () => {
    let client: GatewayClient;
    try {
      client = new GatewayClient();
    } catch (error) {
      const message = describe(error);
      setHealth({ state: "error", message });
      setReadiness({ state: "error", message });
      setProjects({ state: "error", message });
      setSessions({ state: "error", message });
      return;
    }

    // One correlation id for the whole page load, so every request this page
    // makes appears under one identifier in the gateway's logs.
    const correlationId =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `dev-page-${Date.now().toString(36)}`;
    const options = { correlationId };

    await Promise.all([
      client
        .health(options)
        .then((data) => {
          setHealth({ state: "ok", data });
        })
        .catch((error: unknown) => {
          setHealth({ state: "error", message: describe(error) });
        }),
      client
        .readiness(options)
        .then((data) => {
          setReadiness({ state: "ok", data });
        })
        .catch((error: unknown) => {
          setReadiness({ state: "error", message: describe(error) });
        }),
    ]);

    let loaded: ResearchProject[] = [];
    try {
      loaded = await client.listProjects(options);
      setProjects({ state: "ok", data: loaded });
    } catch (error) {
      setProjects({ state: "error", message: describe(error) });
      setSessions({ state: "error", message: "no projects to list sessions for" });
      return;
    }

    // Destructured rather than indexed: `noUncheckedIndexedAccess` is on, and
    // it is on because an index that might be absent is exactly the class of
    // bug that reaches production as a blank panel.
    const [first] = loaded;
    if (!first) {
      setSessions({ state: "ok", data: [] });
      return;
    }
    try {
      setSessions({ state: "ok", data: await client.listSessions(first.id, options) });
    } catch (error) {
      setSessions({ state: "error", message: describe(error) });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <main>
      <h1>Development status</h1>
      <p>
        Reads the gateway from the browser. Nothing here starts research: every
        capability is blocked (D-07, D-03, D-12).
      </p>
      <button type="button" onClick={() => void load()}>
        Reload
      </button>

      <Section title="Health (no dependency consulted)">
        <Render panel={health} />
      </Section>

      <Section title="Readiness (PostgreSQL and Redis gate; Qdrant does not)">
        <Render panel={readiness} />
      </Section>

      <Section title="Research projects">
        {projects.state === "ok" && projects.data.length === 0 ? (
          <p>No projects in this workspace.</p>
        ) : (
          <Render panel={projects} />
        )}
      </Section>

      <Section title="Research sessions (first project)">
        {sessions.state === "ok" && sessions.data.length === 0 ? (
          <p>No sessions.</p>
        ) : (
          <Render panel={sessions} />
        )}
      </Section>
    </main>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginTop: "2rem" }}>
      <h2 style={{ fontSize: "1rem" }}>{title}</h2>
      {children}
    </section>
  );
}

function Render<T>({ panel }: { panel: Panel<T> }) {
  if (panel.state === "loading") return <p>loading…</p>;
  if (panel.state === "error") return <pre style={{ color: "#b00" }}>{panel.message}</pre>;
  return (
    <pre style={{ overflowX: "auto", background: "#f5f5f5", padding: "0.75rem" }}>
      {JSON.stringify(panel.data, null, 2)}
    </pre>
  );
}
