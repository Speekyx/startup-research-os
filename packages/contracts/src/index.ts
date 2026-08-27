/**
 * Startup Research OS shared domain contracts (TypeScript).
 *
 * The generated vocabulary in `./generated/domain.js` is derived from
 * `packages/contracts/schema/domain.v1.json`. Do not edit it. See ADR-009.
 *
 * Everything a service or app needs from the domain vocabulary comes from here.
 * Redeclaring a canonical enum locally is a lint failure
 * (`packages/eslint-config`), because a duplicated enum is how the claims
 * taxonomy drifted in the first place (audit C-02).
 */

export * from "./errors.ts";
export * from "./generated/domain.ts";
export * from "./ids.ts";
export * from "./marketScope.ts";
export * from "./numeric.ts";
export * from "./registry.ts";
export * from "./researchContext.ts";
