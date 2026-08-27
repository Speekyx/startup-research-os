/**
 * Shared ESLint flat config.
 *
 * Most lint rules are style. The ones here are not: each blocks a specific
 * specification violation, which is why they live in a shared config rather
 * than in a review checklist.
 *
 * Requires `eslint` and `typescript-eslint` at the consumer. Not runnable until
 * dependencies are installed; the rule set is fixed here so the config
 * implements a decision rather than a default.
 *
 * @see docs/architecture/quality-gates.md §3
 */

/** Provider SDKs may be imported ONLY inside the gateway's providers package (ADR-006). */
const PROVIDER_SDKS = [
  "@anthropic-ai/sdk",
  "openai",
  "@google/generative-ai",
  "@google/genai",
  "cohere-ai",
  "openrouter",
];

/** Canonical domain enums. Redeclaring one locally is how audit C-02 happened. */
const CANONICAL_ENUM_NAMES = [
  "ClaimType",
  "MarketScopeType",
  "ResearchSessionStatus",
  "DemandSignalFamily",
  "ScoreFamily",
  "LlmTier",
  "RegistryStatus",
];

/** Registry taxonomies. Encoding one as a closed union undoes A-07. */
const REGISTRY_TAXONOMY_NAMES = [
  "ProductType",
  "MarketType",
  "UserMotivation",
  "UserBehavior",
  "ValueProposition",
  "RetentionMechanism",
  "MonetizationModel",
  "DistributionChannel",
  "RiskType",
  "RegionId",
];

const enumSelectors = CANONICAL_ENUM_NAMES.flatMap((name) => [
  {
    selector: `TSEnumDeclaration[id.name='${name}']`,
    message:
      `${name} is a canonical domain enum. Import it from @sros/contracts. ` +
      `A duplicated enum is how the claims taxonomy drifted (audit C-02).`,
  },
  {
    selector: `TSTypeAliasDeclaration[id.name='${name}'] > TSUnionType`,
    message:
      `${name} is a canonical domain type. Import it from @sros/contracts ` +
      `instead of redeclaring the union locally.`,
  },
]);

const registrySelectors = REGISTRY_TAXONOMY_NAMES.flatMap((name) => [
  {
    selector: `TSEnumDeclaration[id.name='${name}']`,
    message:
      `${name} is an EXTENSIBLE REGISTRY, not an enum (Ontology V2 §14.3). ` +
      `Use a RegistryRef. Enumerating it in code recreates the ` +
      `migration-per-concept problem the registry split prevents.`,
  },
  {
    selector: `TSTypeAliasDeclaration[id.name='${name}'] > TSUnionType`,
    message:
      `${name} is an EXTENSIBLE REGISTRY, not a closed union (Ontology V2 §14.3). ` +
      `Use a RegistryRef.`,
  },
]);

/** @type {import("eslint").Linter.Config[]} */
export const base = [
  {
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
    },
    rules: {
      // --- architectural boundaries -------------------------------------
      "no-restricted-imports": [
        "error",
        {
          paths: [
            ...PROVIDER_SDKS.map((name) => ({
              name,
              message:
                "Provider SDKs may only be imported inside the LLM Gateway's " +
                "providers package. Business services request a logical tier " +
                "from the gateway (ADR-006).",
            })),
          ],
          patterns: [
            {
              group: ["**/services/*/src/**", "!**/services/*/src/index*"],
              message:
                "Do not import another context's internals. Cross-context calls " +
                "go through the declared interface (service-boundaries.md §4).",
            },
          ],
        },
      ],

      // --- domain vocabulary --------------------------------------------
      "no-restricted-syntax": ["error", ...enumSelectors, ...registrySelectors],

      // --- correctness ----------------------------------------------------
      // An unhandled claim type or score family is the conflation §8 forbids.
      "@typescript-eslint/switch-exhaustiveness-check": "error",
      // In a pipeline, a dropped promise is lost evidence.
      "@typescript-eslint/no-floating-promises": "error",
      // Untyped data crossing a boundary where provenance must be attached.
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unnecessary-condition": "warn",
      eqeqeq: ["error", "always", { null: "ignore" }],
      "no-console": ["warn", { allow: ["warn", "error"] }],
    },
  },
];

/** For `packages/*`. */
export const library = [...base];

/** For `apps/web`. */
export const next = [
  ...base,
  {
    rules: {
      // Opportunity text derives from scraped sources. Rendering it as HTML is
      // how untrusted content becomes executable (llm-reasoning-rules.md §7).
      "react/no-danger": "error",
    },
  },
];

/** Files that are generated: never lint them, they are not hand-maintained. */
export const ignores = [
  {
    ignores: [
      "**/generated/**",
      "**/dist/**",
      "**/.next/**",
      "**/node_modules/**",
      "**/.turbo/**",
    ],
  },
];

export default base;
