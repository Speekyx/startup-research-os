/**
 * MarketScope: the canonical geographic scope of an analysis.
 *
 * Ontology V2 §4. Geographic axis only — audience/segment scoping is A-12 and
 * is deliberately NOT modelled here.
 *
 * Canonicalization matters more than it looks: a scope is used as a cache key,
 * a dedup key and an equality test, so the same scope written two ways must
 * produce one representation. That is why `parseMarketScope` normalizes rather
 * than merely validating.
 */

import { ContractError } from "./errors.ts";
import {
  COUNTRY_CODE_PATTERN,
  MARKET_SCOPE_TYPE_VALUES,
  type MarketScopeType,
} from "./generated/domain.ts";

const REGION_PATTERN = /^[a-z0-9][a-z0-9._-]{0,63}$/;

export interface MarketScope {
  readonly type: MarketScopeType;
  readonly countries: readonly string[];
  readonly regions: readonly string[];
}

/** The wire shape: absent arrays rather than empty ones. */
export interface MarketScopeJson {
  type: string;
  countries?: readonly string[];
  regions?: readonly string[];
}

function canonicalCountries(value: unknown): string[] {
  if (!Array.isArray(value)) {
    throw new ContractError("market_scope.countries", "expected a list");
  }
  const codes = value.map((item) => {
    if (typeof item !== "string") {
      throw new ContractError("market_scope.countries", "country codes must be strings");
    }
    return item.trim().toUpperCase();
  });
  return [...new Set(codes)].sort();
}

function canonicalRegions(value: unknown): string[] {
  if (!Array.isArray(value)) {
    throw new ContractError("market_scope.regions", "expected a list");
  }
  const regions = value.map((item) => {
    if (typeof item !== "string") {
      throw new ContractError("market_scope.regions", "region ids must be strings");
    }
    return item.trim().toLowerCase();
  });
  return [...new Set(regions)].sort();
}

export function parseMarketScope(data: unknown): MarketScope {
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new ContractError("market_scope", "expected an object");
  }

  const record = data as Record<string, unknown>;
  const unknown = Object.keys(record).filter(
    (k) => k !== "type" && k !== "countries" && k !== "regions",
  );
  if (unknown.length > 0) {
    throw new ContractError("market_scope", `unknown fields: ${unknown.sort().join(", ")}`);
  }

  const rawType = record["type"];
  if (rawType === undefined || rawType === null) {
    throw new ContractError("market_scope.type", "discriminator 'type' is required");
  }
  if (
    typeof rawType !== "string" ||
    !(MARKET_SCOPE_TYPE_VALUES as readonly string[]).includes(rawType)
  ) {
    const hint =
      typeof rawType === "string" && rawType.toUpperCase() === "SEGMENT"
        ? " Segment scoping is A-12 and is not implemented; MarketScope is geographic only."
        : "";
    throw new ContractError(
      "market_scope.type",
      `unknown scope type ${JSON.stringify(rawType)}. Known: ${MARKET_SCOPE_TYPE_VALUES.join(", ")}.${hint}`,
    );
  }
  const type = rawType as MarketScopeType;

  const countries = canonicalCountries(record["countries"] ?? []);
  const regions = canonicalRegions(record["regions"] ?? []);

  for (const code of countries) {
    if (!COUNTRY_CODE_PATTERN.test(code)) {
      throw new ContractError(
        "market_scope.countries",
        `"${code}" is not an ISO 3166-1 alpha-2 code (pattern ${COUNTRY_CODE_PATTERN.source})`,
      );
    }
  }
  for (const region of regions) {
    if (!REGION_PATTERN.test(region)) {
      throw new ContractError("market_scope.regions", `"${region}" is not a valid region identifier`);
    }
  }

  switch (type) {
    case "GLOBAL":
      if (countries.length > 0 || regions.length > 0) {
        throw new ContractError(
          "market_scope",
          "GLOBAL carries no members. Absence of scope is GLOBAL, never an empty list on another type.",
        );
      }
      break;
    case "COUNTRY":
      if (regions.length > 0) {
        throw new ContractError("market_scope", "COUNTRY carries no regions");
      }
      if (countries.length !== 1) {
        throw new ContractError(
          "market_scope",
          `COUNTRY carries exactly one country code, got ${countries.length}. Two or more is MULTI_COUNTRY.`,
        );
      }
      break;
    case "MULTI_COUNTRY":
      if (regions.length > 0) {
        throw new ContractError("market_scope", "MULTI_COUNTRY carries no regions");
      }
      if (countries.length < 2) {
        throw new ContractError(
          "market_scope",
          `MULTI_COUNTRY carries two or more country codes, got ${countries.length}. One is COUNTRY.`,
        );
      }
      break;
    case "REGION":
      if (countries.length > 0) {
        throw new ContractError("market_scope", "REGION carries no countries");
      }
      if (regions.length < 1) {
        throw new ContractError("market_scope", "REGION carries at least one region");
      }
      break;
  }

  return Object.freeze({ type, countries: Object.freeze(countries), regions: Object.freeze(regions) });
}

export const globalScope = (): MarketScope => parseMarketScope({ type: "GLOBAL" });

export const countryScope = (code: string): MarketScope =>
  parseMarketScope({ type: "COUNTRY", countries: [code] });

export const multiCountryScope = (codes: readonly string[]): MarketScope =>
  parseMarketScope({ type: "MULTI_COUNTRY", countries: [...codes] });

export const regionScope = (regions: readonly string[]): MarketScope =>
  parseMarketScope({ type: "REGION", regions: [...regions] });

export function marketScopeToJson(scope: MarketScope): MarketScopeJson {
  const out: MarketScopeJson = { type: scope.type };
  if (scope.countries.length > 0) out.countries = [...scope.countries];
  if (scope.regions.length > 0) out.regions = [...scope.regions];
  return out;
}

/** A stable cache/dedup key. Equal scopes always produce equal keys. */
export function marketScopeKey(scope: MarketScope): string {
  if (scope.type === "GLOBAL") return "GLOBAL";
  const members = scope.countries.length > 0 ? scope.countries : scope.regions;
  return `${scope.type}:${members.join(",")}`;
}

export const marketScopeEquals = (a: MarketScope, b: MarketScope): boolean =>
  marketScopeKey(a) === marketScopeKey(b);
