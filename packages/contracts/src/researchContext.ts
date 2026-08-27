/**
 * ResearchContext: the research specification.
 *
 * Ontology V2 §11.3. A **value object**, not an entity: no identity, no
 * lifecycle, and two contexts with identical parameters are the same
 * specification.
 *
 * Serialized as an **immutable snapshot** on a ResearchSession. The snapshot is
 * the reproducibility guarantee: editing a project's default context must never
 * retroactively change what a past session says it ran with.
 *
 * `canonicalJson` is what gets persisted and hashed — deterministic, sorted
 * keys, canonicalized members — so the same specification always produces the
 * same bytes.
 */

import { ContractError } from "./errors.ts";
import { RESEARCH_CONTEXT_SCHEMA_VERSION } from "./generated/domain.ts";
import {
  marketScopeToJson,
  parseMarketScope,
  type MarketScope,
} from "./marketScope.ts";
import { parseRegistryRef, registryRefToJson, type RegistryRef } from "./registry.ts";

const FIELDS = new Set([
  "schema_version",
  "market_scope",
  "market_types",
  "product_types",
  "domains",
  "audience",
  "languages",
  "budget_constraints",
  "technical_constraints",
  "desired_mvp_complexity",
  "research_depth",
  "time_horizon_days",
  "excluded_markets",
  "excluded_categories",
  "filters",
]);

export interface BudgetConstraints {
  readonly max_cost_units: number | null;
  readonly max_llm_calls: number | null;
}

export interface ResearchContext {
  readonly schema_version: string;
  readonly market_scope: MarketScope;
  readonly market_types: readonly RegistryRef[];
  readonly product_types: readonly RegistryRef[];
  readonly domains: readonly string[];
  readonly audience: string | null;
  readonly languages: readonly string[];
  readonly budget_constraints: BudgetConstraints | null;
  readonly technical_constraints: readonly string[];
  readonly desired_mvp_complexity: string | null;
  readonly research_depth: string | null;
  readonly time_horizon_days: number | null;
  readonly excluded_markets: readonly RegistryRef[];
  readonly excluded_categories: readonly string[];
  readonly filters: Readonly<Record<string, unknown>>;
}

function strings(value: unknown, field: string): string[] {
  if (value === undefined || value === null) return [];
  if (!Array.isArray(value)) throw new ContractError(field, "expected a list");
  return value.map((item) => {
    if (typeof item !== "string") throw new ContractError(field, "expected strings");
    return item;
  });
}

function refs(value: unknown): RegistryRef[] {
  if (value === undefined || value === null) return [];
  if (!Array.isArray(value)) {
    throw new ContractError("research_context", "registry fields expect a list");
  }
  return value.map(parseRegistryRef);
}

function parseBudget(value: unknown): BudgetConstraints | null {
  if (value === undefined || value === null) return null;
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new ContractError("budget_constraints", "expected an object");
  }
  const record = value as Record<string, unknown>;
  const unknown = Object.keys(record).filter(
    (k) => k !== "max_cost_units" && k !== "max_llm_calls",
  );
  if (unknown.length > 0) {
    throw new ContractError("budget_constraints", `unknown fields: ${unknown.sort().join(", ")}`);
  }
  const cost = record["max_cost_units"] ?? null;
  const calls = record["max_llm_calls"] ?? null;
  if (cost !== null && (typeof cost !== "number" || cost < 0)) {
    throw new ContractError("budget_constraints.max_cost_units", "must not be negative");
  }
  if (calls !== null && (typeof calls !== "number" || calls < 0)) {
    throw new ContractError("budget_constraints.max_llm_calls", "must not be negative");
  }
  return Object.freeze({
    max_cost_units: cost,
    max_llm_calls: calls,
  });
}

export function parseResearchContext(data: unknown): ResearchContext {
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new ContractError("research_context", "expected an object");
  }
  const record = data as Record<string, unknown>;

  const unknown = Object.keys(record).filter((k) => !FIELDS.has(k));
  if (unknown.length > 0) {
    throw new ContractError(
      "research_context",
      `unknown fields: ${unknown.sort().join(", ")}. Unknown fields are rejected so a ` +
        `typo is not silently dropped from a snapshot.`,
    );
  }
  if (!("market_scope" in record)) {
    throw new ContractError("research_context.market_scope", "required");
  }

  const horizon = record["time_horizon_days"] ?? null;
  if (
    horizon !== null &&
    (typeof horizon !== "number" || !Number.isInteger(horizon) || horizon < 1)
  ) {
    throw new ContractError("research_context.time_horizon_days", "must be a positive integer");
  }

  const languages = [
    ...new Set(strings(record["languages"], "research_context.languages").map((l) => l.toLowerCase())),
  ].sort();

  const audience = record["audience"] ?? null;
  const mvp = record["desired_mvp_complexity"] ?? null;
  const depth = record["research_depth"] ?? null;

  return Object.freeze({
    schema_version:
      typeof record["schema_version"] === "string"
        ? record["schema_version"]
        : RESEARCH_CONTEXT_SCHEMA_VERSION,
    market_scope: parseMarketScope(record["market_scope"]),
    market_types: Object.freeze(refs(record["market_types"])),
    product_types: Object.freeze(refs(record["product_types"])),
    domains: Object.freeze(strings(record["domains"], "research_context.domains")),
    audience: typeof audience === "string" ? audience : null,
    languages: Object.freeze(languages),
    budget_constraints: parseBudget(record["budget_constraints"]),
    technical_constraints: Object.freeze(
      strings(record["technical_constraints"], "research_context.technical_constraints"),
    ),
    desired_mvp_complexity: typeof mvp === "string" ? mvp : null,
    research_depth: typeof depth === "string" ? depth : null,
    time_horizon_days: horizon,
    excluded_markets: Object.freeze(refs(record["excluded_markets"])),
    excluded_categories: Object.freeze(
      strings(record["excluded_categories"], "research_context.excluded_categories"),
    ),
    filters: Object.freeze({ ...(record["filters"] as Record<string, unknown> | undefined) }),
  });
}

type Json = Record<string, unknown>;

export function researchContextToJson(ctx: ResearchContext): Json {
  const payload: Json = {
    audience: ctx.audience,
    desired_mvp_complexity: ctx.desired_mvp_complexity,
    domains: [...ctx.domains],
    excluded_categories: [...ctx.excluded_categories],
    excluded_markets: ctx.excluded_markets.map(registryRefToJson),
    filters: { ...ctx.filters },
    languages: [...ctx.languages],
    market_scope: marketScopeToJson(ctx.market_scope),
    market_types: ctx.market_types.map(registryRefToJson),
    product_types: ctx.product_types.map(registryRefToJson),
    research_depth: ctx.research_depth,
    schema_version: ctx.schema_version,
    technical_constraints: [...ctx.technical_constraints],
    time_horizon_days: ctx.time_horizon_days,
  };
  if (ctx.budget_constraints !== null) {
    payload["budget_constraints"] = { ...ctx.budget_constraints };
  }
  return payload;
}

/** Deterministic JSON with recursively sorted keys. Mirrors Python `json.dumps(sort_keys=True)`. */
export function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") {
    // JSON.stringify returns undefined for `undefined` and for functions.
    // The declared type hides that, so the fallback stays.
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    return JSON.stringify(value) ?? "null";
  }
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  const record = value as Record<string, unknown>;
  const parts = Object.keys(record)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`);
  return `{${parts.join(",")}}`;
}

/** What gets persisted and hashed. Byte-identical to the Python implementation. */
export const researchContextCanonicalJson = (ctx: ResearchContext): string =>
  stableStringify(researchContextToJson(ctx));
