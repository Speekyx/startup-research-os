import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Startup Research OS",
  description: "Evidence-driven AI Opportunity Research Engine",
};

/**
 * Root layout.
 *
 * Deliberately unstyled. `PROJECT_MANIFEST.md` §Forbidden During Foundation
 * rules out dashboards and user-facing workflows during Sprint 0, and a design
 * system built before there is anything to display is a design system built
 * against guesses. Styling arrives with `packages/ui`, whose components carry
 * specification obligations (score families never collapsed, claim types always
 * labelled) that only matter once there is data to get wrong.
 */
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
          margin: 0,
          padding: "2rem",
          lineHeight: 1.5,
        }}
      >
        {children}
      </body>
    </html>
  );
}
