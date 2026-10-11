import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { RiskBadge, StatusBadge } from "@/components/badges";
import { listCases } from "@/lib/backend";
import { EMPTY, formatDate, formatRange, formatRecommendation, sentenceCase } from "@/lib/format";
import { pageWidth, panel, textLink } from "@/lib/ui";
import { RefreshButton } from "./refresh-button";

export const metadata: Metadata = {
  title: "Cases | Litigation Funding Underwriting Agent",
};

export default function DashboardPage() {
  return (
    <main id="main" tabIndex={-1} className={`${pageWidth} py-10`}>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-semibold text-ink-950">Cases</h1>
          <p className="mt-1 text-ink-700">Newest first. Select a case to open its underwriting memo.</p>
        </div>
        <RefreshButton />
      </div>
      <div className="mt-6">
        <Suspense fallback={<TableSkeleton />}>
          <CasesTable />
        </Suspense>
      </div>
    </main>
  );
}

const COLUMNS = [
  { label: "Submitted", numeric: false },
  { label: "Injury type", numeric: false },
  { label: "Status", numeric: false },
  { label: "Risk score", numeric: true },
  { label: "Funding range", numeric: true },
  { label: "Recommendation", numeric: false },
] as const;

async function CasesTable() {
  const cases = await listCases();

  if (cases.length === 0) {
    return (
      <div className={`${panel} px-6 py-10`}>
        <h2 className="font-serif text-xl font-semibold text-ink-950">No cases yet</h2>
        <p className="mt-2 max-w-prose text-ink-700">
          New applications appear here after a claimant submits one. To test the flow, submit a case from the{" "}
          <Link href="/apply" className={textLink}>
            application form
          </Link>
          .
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-md border border-paper-200 md:overflow-visible">
      <table className="w-full min-w-[720px] border-collapse text-left text-sm">
        <caption className="sr-only">Submitted cases, newest first</caption>
        <thead>
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.label}
                scope="col"
                className={`sticky top-0 z-10 border-b border-paper-200 bg-paper-50 px-4 py-3 font-medium text-ink-500 ${col.numeric ? "text-right" : ""}`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr
              key={c.id}
              className="relative border-b border-paper-200 transition-colors duration-150 last:border-b-0 even:bg-paper-100 hover:bg-paper-200 active:bg-paper-200"
            >
              <td className="whitespace-nowrap px-4 py-3 tabular-nums text-ink-700">
                <Link
                  href={`/dashboard/${c.id}`}
                  className="scroll-mt-16 rounded-sm text-ink-950 outline-none after:absolute after:inset-0 after:rounded-sm focus-visible:after:ring-2 focus-visible:after:ring-inset focus-visible:after:ring-accent-500"
                  aria-label={`Open case submitted ${formatDate(c.created_at)}, ${c.injury_type ?? "injury type unknown"}`}
                >
                  {formatDate(c.created_at)}
                </Link>
              </td>
              <td className="max-w-[16rem] break-words px-4 py-3 text-ink-950">{c.injury_type ? sentenceCase(c.injury_type) : EMPTY}</td>
              <td className="px-4 py-3">
                <StatusBadge status={c.status} />
              </td>
              <td className="px-4 py-3 text-right">
                <RiskBadge score={c.risk_score} />
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right tabular-nums text-ink-950">
                {formatRange(c.funding_low, c.funding_high)}
              </td>
              <td className="px-4 py-3 text-ink-950">{formatRecommendation(c.recommendation)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className={`${panel} px-6 py-10`} role="status" aria-live="polite">
      <p className="text-ink-500">Loading cases…</p>
    </div>
  );
}
