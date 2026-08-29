/**
 * Shared conformance suite (TypeScript side).
 *
 * Reads packages/contracts/conformance/cases.json — the SAME file the Python
 * suite reads. If the two implementations ever disagree, one of these suites
 * goes red. That is what makes "TS and Python contracts are synchronized" a
 * tested property rather than a claim.
 *
 * Runs on the Node built-in test runner with native type stripping, so it needs
 * no install:  node --test --experimental-strip-types
 */

import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import test, { describe } from "node:test";

import { ContractError } from "../src/errors.ts";
import { checkNumeric } from "../src/numeric.ts";
import {
  marketScopeEquals,
  marketScopeKey,
  marketScopeToJson,
  parseMarketScope,
} from "../src/marketScope.ts";
import { parseRegistryRef, registryRefToJson } from "../src/registry.ts";
import {
  parseResearchContext,
  researchContextCanonicalJson,
} from "../src/researchContext.ts";
import {
  CLAIM_LIFECYCLE_VALUES,
  CLAIM_TYPE_VALUES,
  RESEARCH_SESSION_STATUS_VALUES,
  isClaimLifecycle,
  isClaimOrigin,
  isClaimTemporality,
  isClaimType,
  isEvidenceDirection,
  isEvidenceIndependenceState,
  isEvidenceObservationCategory,
  isObservationKind,
  isResearchSessionStatus,
  type NumericTypeName,
} from "../src/generated/domain.ts";

/**
 * The shape of `conformance/cases.json`.
 *
 * Typed rather than left as `any`: the fixture file is the shared contract
 * between this suite and the Python one, so its shape deserves to be checked
 * here too.
 */
interface NumericCases {
  valid: unknown[];
  invalid: unknown[];
}

interface EnumCases {
  valid: unknown[];
  invalid: unknown[];
}

/** Added in Mission 1.2 with the Claim entity. */
interface ClaimModelCases {
  claim_id: EnumCases;
  claim_temporality: EnumCases;
  claim_origin: EnumCases;
  claim_lifecycle: EnumCases;
  evidence_direction: EnumCases;
  evidence_independence_state: EnumCases;
  observation_category: EnumCases;
  observation_kind: EnumCases;
}
interface ScopeCase {
  name: string;
  input: unknown;
  canonical: unknown;
  key: string;
}
interface InvalidCase {
  name: string;
  input: unknown;
  reason: string;
}
interface EqualityCase {
  name: string;
  a: unknown;
  b: unknown;
  equal: boolean;
}
interface ContextCase {
  name: string;
  input: unknown;
  canonical_json: string;
}
interface ConformanceCases {
  numeric: Record<string, NumericCases>;
  market_scope: {
    valid: ScopeCase[];
    invalid: InvalidCase[];
    equality: EqualityCase[];
  };
  registry_ref: {
    valid: { registry: string; id: string }[];
    invalid: { case: unknown; reason: string }[];
  };
  claim_type: { valid: unknown[]; invalid: unknown[] };
  claim_model: ClaimModelCases;
  research_session_status: { valid: unknown[]; invalid: unknown[] };
  research_context: { valid: ContextCase[]; invalid: InvalidCase[] };
  forbidden_fields: { names: string[] };
}

const here = path.dirname(fileURLToPath(import.meta.url));
const CASES = JSON.parse(
  readFileSync(path.join(here, "..", "conformance", "cases.json"), "utf8"),
) as ConformanceCases;

function assertContractError(fn: () => unknown, label: string): void {
  assert.throws(fn, (err: unknown) => err instanceof ContractError, label);
}

describe("numeric conformance", () => {
  test("valid and invalid ranges", () => {
    for (const [typeName, cases] of Object.entries(CASES.numeric)) {
            for (const value of cases.valid) {
        checkNumeric(typeName as NumericTypeName, value);
      }
      for (const value of cases.invalid) {
        assertContractError(
          () => checkNumeric(typeName as NumericTypeName, value),
          `${typeName} should reject ${JSON.stringify(value)}`,
        );
      }
    }
  });

  test("confidence and score are not interchangeable", () => {
    // The single most likely silent numeric bug in the system.
    checkNumeric("Score", 82);
    assertContractError(() => checkNumeric("Confidence", 82), "82 is not a confidence");
    checkNumeric("Confidence", 0.82);
    assertContractError(() => checkNumeric("Score", 0.82), "0.82 is not a score");
  });
});

describe("MarketScope conformance", () => {
  test("valid cases canonicalize", () => {
    for (const c of CASES.market_scope.valid) {
      const scope = parseMarketScope(c.input);
      assert.deepEqual(marketScopeToJson(scope), c.canonical, c.name);
      assert.equal(marketScopeKey(scope), c.key, c.name);
    }
  });

  test("invalid cases rejected", () => {
    for (const c of CASES.market_scope.invalid) {
      assertContractError(() => parseMarketScope(c.input), `${c.name}: ${c.reason}`);
    }
  });

  test("equality cases", () => {
    for (const c of CASES.market_scope.equality) {
      const a = parseMarketScope(c.a);
      const b = parseMarketScope(c.b);
      assert.equal(marketScopeEquals(a, b), c.equal, c.name);
    }
  });

  test("segment is not implemented (A-12 stays open)", () => {
    assert.throws(
      () => parseMarketScope({ type: "SEGMENT" }),
      (err: unknown) => err instanceof ContractError && err.message.includes("A-12"),
    );
  });

  test("scope objects are frozen", () => {
    const scope = parseMarketScope({ type: "COUNTRY", countries: ["fr"] });
    assert.equal(Object.isFrozen(scope), true);
  });
});

describe("closed enum conformance", () => {
  test("ClaimType exact values and order", () => {
    assert.deepEqual(
      [...CLAIM_TYPE_VALUES],
      ["OBSERVED", "INFERRED", "PREDICTED", "RECOMMENDED", "HYPOTHESIS"],
    );
    for (const v of CASES.claim_type.valid) assert.equal(isClaimType(v), true, String(v));
    for (const v of CASES.claim_type.invalid) assert.equal(isClaimType(v), false, String(v));
  });

  test("the claim model enums match the shared cases", () => {
    // The same fixture the Python suite reads. A value one language accepts and
    // the other rejects fails the build rather than a request.
    const guards: Array<[keyof ClaimModelCases, (v: unknown) => boolean]> = [
      ["claim_temporality", isClaimTemporality],
      ["claim_origin", isClaimOrigin],
      ["claim_lifecycle", isClaimLifecycle],
      ["evidence_direction", isEvidenceDirection],
      ["evidence_independence_state", isEvidenceIndependenceState],
      ["observation_category", isEvidenceObservationCategory],
      ["observation_kind", isObservationKind],
    ];
    for (const [key, guard] of guards) {
      const cases = CASES.claim_model[key];
      for (const v of cases.valid) assert.equal(guard(v), true, `${key}: ${String(v)}`);
      for (const v of cases.invalid) assert.equal(guard(v), false, `${key}: ${String(v)}`);
    }
  });

  test("no claim lifecycle value is an epistemic verdict", () => {
    // The absence is the feature. A stored VALIDATED would freeze a conclusion
    // that later evidence could contradict (Mission 1.2 §38).
    assert.deepEqual([...CLAIM_LIFECYCLE_VALUES], ["ACTIVE", "WITHDRAWN"]);
    for (const forbidden of ["VALIDATED", "REJECTED", "CONFIRMED", "DISPROVEN"]) {
      assert.equal(isClaimLifecycle(forbidden), false, forbidden);
    }
  });

  test("HYPOTHESIS is first class", () => {
    // Without it the anti-hallucination rule has nowhere to put a claim.
    assert.equal(isClaimType("HYPOTHESIS"), true);
  });

  test("ResearchSessionStatus values", () => {
    for (const v of CASES.research_session_status.valid) {
      assert.equal(isResearchSessionStatus(v), true, String(v));
    }
    for (const v of CASES.research_session_status.invalid) {
      assert.equal(isResearchSessionStatus(v), false, String(v));
    }
  });

  test("no invented lifecycle states", () => {
    const names = new Set<string>(RESEARCH_SESSION_STATUS_VALUES);
    assert.equal(names.has("BUDGET_EXHAUSTED"), false);
    assert.equal(names.has("PARTIAL"), false);
    assert.equal(names.has("COMPLETED"), true);
  });
});

describe("registry conformance", () => {
  test("valid refs", () => {
    for (const c of CASES.registry_ref.valid) {
      const ref = parseRegistryRef(c);
      assert.deepEqual(registryRefToJson(ref), { id: c.id, registry: c.registry });
    }
  });

  test("invalid refs", () => {
    for (const c of CASES.registry_ref.invalid) {
      assertContractError(() => parseRegistryRef(c.case), c.reason);
    }
  });

  test("closed enums are not registries", () => {
    // A-07: ClaimType is an enum, not a registry.
    assertContractError(
      () => parseRegistryRef({ registry: "claim_type", id: "observed" }),
      "claim_type is not a registry",
    );
  });
});

describe("ResearchContext conformance", () => {
  test("valid cases produce the expected canonical JSON", () => {
    for (const c of CASES.research_context.valid) {
      const ctx = parseResearchContext(c.input);
      assert.equal(researchContextCanonicalJson(ctx), c.canonical_json, c.name);
    }
  });

  test("invalid cases rejected", () => {
    for (const c of CASES.research_context.invalid) {
      assertContractError(() => parseResearchContext(c.input), `${c.name}: ${c.reason}`);
    }
  });

  test("parsed context is frozen (snapshot immutability)", () => {
    const ctx = parseResearchContext({ market_scope: { type: "GLOBAL" } });
    assert.equal(Object.isFrozen(ctx), true);
    assert.throws(() => {
      (ctx as { audience: string | null }).audience = "nope";
    });
  });

  test("identical specifications serialize identically", () => {
    const a = parseResearchContext({
      market_scope: { type: "MULTI_COUNTRY", countries: ["us", "fr"] },
    });
    const b = parseResearchContext({
      market_scope: { type: "MULTI_COUNTRY", countries: ["FR", "US"] },
    });
    assert.equal(researchContextCanonicalJson(a), researchContextCanonicalJson(b));
  });
});

describe("blocked work guard", () => {
  test("no D-03 aggregation fields leak into contracts", () => {
    const forbidden: string[] = CASES.forbidden_fields.names;
    const srcDir = path.join(here, "..", "src");
    const offenders: string[] = [];
    const walk = (dir: string): void => {
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) walk(full);
        else if (entry.name.endsWith(".ts")) {
          const text = readFileSync(full, "utf8");
          for (const name of forbidden) {
            if (text.includes(name)) offenders.push(`${entry.name}: ${name}`);
          }
        }
      }
    };
    walk(srcDir);
    assert.deepEqual(offenders, [], `D-03 leakage into contracts: ${offenders.join(", ")}`);
  });
});
