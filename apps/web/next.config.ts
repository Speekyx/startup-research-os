import type { NextConfig } from "next";

/**
 * Next.js configuration.
 *
 * `transpilePackages` is required because `@sros/contracts` ships TypeScript
 * source rather than a build artifact (ADR-009: the contracts package has no
 * build step, so a contract change is visible to every consumer immediately,
 * with no publish and no stale `dist/`).
 *
 * No environment variable is hard-coded here. ADR-007 portability rule 1:
 * configuration comes from the environment, and `src/lib/api/config.ts` is the
 * only place it is read.
 */
const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@sros/contracts"],
  typescript: {
    // A type error must fail the build. Ignoring them would make `tsc` in CI
    // the only thing standing between a type error and production, and CI is
    // exactly what gets skipped under time pressure.
    ignoreBuildErrors: false,
  },
  eslint: {
    // Linting runs once, from the repository root, over the whole workspace.
    // Running it again during the build would apply a different rule set than
    // the one CI enforces.
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
