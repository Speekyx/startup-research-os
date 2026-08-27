/**
 * Validated numeric domain types.
 *
 * `scoring-framework-v1.1.md` §4.1 defines four distinct quantities. They are
 * not interchangeable, and the single most likely silent bug in this system is
 * a confidence rendered on the score scale or vice versa.
 *
 * Naming rule, enforced here and by lint:
 *   a field named `confidence` is always [0.0, 1.0]
 *   a field named `*_score`     is always 0-100
 */

import { ContractError } from "./errors.ts";
import { NUMERIC_BOUNDS, type NumericTypeName } from "./generated/domain.ts";

export function checkNumeric(
  typeName: NumericTypeName,
  value: unknown,
  field?: string,
): number {
  const name = field ?? typeName;
  const bounds = NUMERIC_BOUNDS[typeName];
  // Runtime guard at a boundary: the type says this cannot happen, but this
  // function is reachable from JSON and from JavaScript callers.
  // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
  if (bounds === undefined) {
    throw new ContractError(name, `unknown numeric type ${String(typeName)}`);
  }

  if (typeof value !== "number") {
    throw new ContractError(name, `expected a number, got ${typeof value}`);
  }
  if (!Number.isFinite(value)) {
    throw new ContractError(name, "must be finite");
  }

  if (bounds.integer && !Number.isInteger(value)) {
    throw new ContractError(name, `${typeName} must be an integer, got ${value}`);
  }

  if (value < bounds.min || value > bounds.max) {
    throw new ContractError(
      name,
      `${typeName} must be within [${bounds.min}, ${bounds.max}], got ${value}`,
    );
  }

  return value;
}

export const confidence = (v: unknown, field = "confidence"): number =>
  checkNumeric("Confidence", v, field);

export const probability = (v: unknown, field = "probability"): number =>
  checkNumeric("Probability", v, field);

export const reliability = (v: unknown, field = "reliability"): number =>
  checkNumeric("Reliability", v, field);

export const independence = (v: unknown, field = "independence"): number =>
  checkNumeric("Independence", v, field);

export const score = (v: unknown, field = "score"): number =>
  checkNumeric("Score", v, field);

export const evidenceLevel = (v: unknown, field = "evidence_level"): number =>
  checkNumeric("EvidenceLevel", v, field);

/** Presentation helper. 0.82 -> 82. Never the reverse without going through here. */
export const confidenceToPercent = (v: number): number =>
  Math.round(confidence(v) * 100);
