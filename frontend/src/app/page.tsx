import Link from "next/link";
import { focusRing, pageWidth } from "@/lib/ui";

const ENTRIES = [
  {
    href: "/apply",
    title: "Apply for funding",
    body: "Describe your injury and upload one supporting document. An attorney reviews every case.",
  },
  {
    href: "/login",
    title: "Attorney portal",
    body: "Review underwriting memos, extracted facts and risk scores, then record a decision.",
  },
] as const;

export default function Home() {
  return (
    <main id="main" tabIndex={-1} className={`${pageWidth} flex flex-1 flex-col justify-center py-16`}>
      <div className="max-w-2xl">
        <h1 className="font-serif text-3xl font-semibold text-balance text-ink-950 sm:text-4xl">
          Litigation Funding Underwriting Agent
        </h1>
        <p className="mt-3 text-lg text-ink-700">
          AI-assisted case intake and underwriting for pre-settlement funding
        </p>
      </div>

      <ul className="mt-10 grid gap-6 sm:grid-cols-2">
        {ENTRIES.map((entry) => (
          <li key={entry.href}>
            <Link
              href={entry.href}
              className={`group block h-full rounded-md border border-paper-200 bg-paper-100 p-6 transition-colors duration-150 hover:border-ink-300 hover:bg-paper-200 active:bg-paper-200 active:border-ink-500 ${focusRing}`}
            >
              <span className="font-serif text-xl font-semibold text-ink-950 underline decoration-transparent underline-offset-4 transition-colors duration-150 group-hover:decoration-ink-700">
                {entry.title}
              </span>
              <span className="mt-2 block text-ink-700">{entry.body}</span>
            </Link>
          </li>
        ))}
      </ul>

      <p className="mt-10 text-sm text-ink-500">Demo with synthetic data only.</p>
    </main>
  );
}
