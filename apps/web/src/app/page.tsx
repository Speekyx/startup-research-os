import Link from "next/link";

/**
 * The index.
 *
 * There is no console here, and that is the honest state of the product: every
 * research capability is blocked (D-07 acquisition, D-03 scoring, D-12 and
 * Mission 0.4 §34 NLP), so a dashboard would be a page of empty panels
 * implying work that cannot run.
 */
export default function Home() {
  return (
    <main>
      <h1>Startup Research OS</h1>
      <p>
        Foundation phase. The API client and its typed responses exist; the
        research console does not.
      </p>
      <p>
        <Link href="/dev">Development status page</Link>
      </p>
    </main>
  );
}
