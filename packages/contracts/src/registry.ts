/**
 * Registry references and entries.
 *
 * Ontology V2 §14: evolving taxonomies are registry rows, not enums. This
 * module declares the *reference* and *entry* shapes; it never enumerates
 * values. Doing so would recreate the migration-per-concept problem the
 * registry split exists to prevent.
 */

import { ContractError } from "./errors.ts";
import {
  REGISTRY_NAMES,
  type RegistryName,
  type RegistryStatus,
} from "./generated/domain.ts";

const ID_PATTERN = /^[a-z0-9][a-z0-9._-]{0,127}$/;

/**
 * A reference into an extensible registry.
 *
 * Persists the **stable identifier**, never the display name. Storing a display
 * name means a rename silently rewrites history (Ontology V2 §14.4).
 */
export interface RegistryRef {
  readonly registry: RegistryName;
  readonly id: string;
}

/** One registry row. Deprecation, never deletion. */
export interface RegistryEntry {
  readonly registry: RegistryName;
  readonly id: string;
  readonly name: string;
  readonly version: number;
  readonly status: RegistryStatus;
  readonly description?: string | null;
  readonly aliases?: readonly string[];
}

export function parseRegistryRef(data: unknown): RegistryRef {
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new ContractError("registry_ref", "expected an object");
  }
  const record = data as Record<string, unknown>;
  const unknown = Object.keys(record).filter((k) => k !== "registry" && k !== "id");
  if (unknown.length > 0) {
    throw new ContractError("registry_ref", `unknown fields: ${unknown.sort().join(", ")}`);
  }

  const { registry, id } = record;
  if (typeof registry !== "string" || !(REGISTRY_NAMES as readonly string[]).includes(registry)) {
    throw new ContractError(
      "registry",
      `unknown registry ${JSON.stringify(registry)}. Closed enums (ClaimType, ` +
        `MarketScopeType, ResearchSessionStatus, DemandSignalFamily, ScoreFamily) ` +
        `are not registries. Known registries: ${REGISTRY_NAMES.join(", ")}`,
    );
  }
  if (typeof id !== "string" || !ID_PATTERN.test(id)) {
    throw new ContractError(
      `${registry}.id`,
      `registry ids are lowercase stable slugs matching ${ID_PATTERN.source}, got ${JSON.stringify(id)}`,
    );
  }

  return Object.freeze({ registry: registry as RegistryName, id });
}

export const registryRefToJson = (ref: RegistryRef): { id: string; registry: string } => ({
  id: ref.id,
  registry: ref.registry,
});

export function parseRegistryEntry(data: unknown): RegistryEntry {
  if (typeof data !== "object" || data === null) {
    throw new ContractError("registry_entry", "expected an object");
  }
  const record = data as Record<string, unknown>;
  const ref = parseRegistryRef({ registry: record["registry"], id: record["id"] });

  const name = record["name"];
  if (typeof name !== "string" || name.length === 0) {
    throw new ContractError(`${ref.registry}.${ref.id}.name`, "canonical name is required");
  }

  const version = record["version"] ?? 1;
  if (typeof version !== "number" || !Number.isInteger(version) || version < 1) {
    throw new ContractError(`${ref.registry}.${ref.id}.version`, "version starts at 1");
  }

  // Validate the RAW value, then narrow. Casting first would make the check
  // tautological, which is exactly what the linter caught.
  const rawStatus: unknown = record["status"] ?? "ACTIVE";
  if (rawStatus !== "ACTIVE" && rawStatus !== "DEPRECATED") {
    throw new ContractError(
      `${ref.registry}.${ref.id}.status`,
      "status must be ACTIVE or DEPRECATED",
    );
  }
  const status: RegistryStatus = rawStatus;

  const description = record["description"];
  const aliases = record["aliases"];

  return Object.freeze({
    registry: ref.registry,
    id: ref.id,
    name,
    version,
    status,
    description: typeof description === "string" ? description : null,
    aliases: Array.isArray(aliases)
      ? Object.freeze(aliases.filter((a): a is string => typeof a === "string"))
      : Object.freeze([]),
  });
}
