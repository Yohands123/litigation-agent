import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { GroundedBadge, StatusBadge, riskTone } from "@/components/badges";
import { getCase, getCaseAudit } from "@/lib/backend";
import {
  EMPTY,
  formatDate,
  formatDateTime,
  formatImpact,
  formatMoney,
  formatRange,
  formatRecommendation,
  sentenceCase,
  shortId,
} from "@/lib/format";
import type { AuditEntry, CaseDetail, Extraction } from "@/lib/types";
import { pageWidth, panel, sectionTitle, textLink } from "@/lib/ui";
import { DecisionActions } from "./decision-actions";
import { Memo } from "./memo";

export const metadata: Metadata = {
  title: "Case review | Litigation Funding Underwriting Agent",
};

export default function CasePage({ params }: PageProps<"/dashboard/[id]">) {
  return (
    <main id="main" tabIndex={-1} className={`${pageWidth} py-10`}>
      <Link href="/dashboard" className={`${textLink} text-sm`}>
        All cases
      </Link>
      <Suspense fallback={<DetailSkeleton />}>
        <CaseView params={params} />
      </Suspense>
    </main>
  );
}

async function CaseView({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [c, audit] = await Promise.all([getCase(id), getCaseAudit(id)]);

  return (
    <>
      <CaseHeader c={c} />
      <div className="mt-10 grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0 space-y-6">
          <Section title="Underwriting memo" id="memo">
            {c.memo ? (
              <Memo markdown={c.memo} />
            ) : (
              <p className="text-ink-700">
                No memo yet. It appears here when the automated workflow finishes for this case.
              </p>
            )}
          </Section>
          <Section title="Extracted facts" id="facts">
            <ExtractedFacts extraction={c.extraction} reported={c.injury_type_reported} />
          </Section>
          <Section title="Scoring factors" id="factors">
            <ScoringFactors c={c} />
          </Section>
        </div>

        <aside className="min-w-0 space-y-6" aria-label="Case actions and details">
          <Section title="Decision" id="decision">
            <DecisionActions caseId={c.id} currentStatus={c.status} />
          </Section>
          <Section title="Claimant" id="claimant">
            <p className="text-sm text-ink-500">Visible to attorneys only. Never sent to the AI.</p>
            <dl className="mt-4 space-y-3">
              <Field label="Name" value={c.claimant.name} />
              <Field label="Email" value={c.claimant.email} breakAll noTranslate />
              <Field label="Phone" value={c.claimant.phone ?? EMPTY} />
            </dl>
          </Section>
          <Section title="Redaction" id="redaction">
            <p className="text-ink-950">{redactionSummary(c.redaction_counts)}</p>
            {c.document_filename ? (
              <p className="mt-2 break-all text-sm text-ink-500">
                Source document: <span translate="no">{c.document_filename}</span>
              </p>
            ) : null}
          </Section>
          <Section title="Audit trail" id="audit">
            <AuditTrail entries={audit} />
          </Section>
        </aside>
      </div>
    </>
  );
}

function CaseHeader({ c }: { c: CaseDetail }) {
  const tone = typeof c.risk_score === "number" ? riskTone(c.risk_score) : null;
  const scoreColor = tone === "danger" ? "text-danger" : tone === "warning" ? "text-warning" : tone ? "text-success" : "text-ink-500";

  return (
    <header className="mt-6 border-b border-paper-200 pb-8">
      <div className="flex flex-wrap items-start justify-between gap-8">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-serif text-3xl font-semibold text-ink-950">Case {shortId(c.id)}</h1>
            <StatusBadge status={c.status} />
          </div>
          <p translate="no" className="mt-2 break-all text-sm tabular-nums text-ink-500">
            {c.id}
          </p>
          <p className="mt-1 text-sm text-ink-700">
            Submitted {formatDate(c.created_at)}. Last updated {formatDateTime(c.updated_at)}.
          </p>
        </div>

        <dl className="flex flex-wrap items-end gap-x-10 gap-y-4">
          <div>
            <dt className="text-sm text-ink-500">Risk score</dt>
            <dd className={`font-serif text-5xl font-semibold leading-none tabular-nums ${scoreColor}`}>
              {c.risk_score ?? EMPTY}
              {typeof c.risk_score === "number" ? (
                <span className="ml-1 font-sans text-base font-normal text-ink-500">/ 100</span>
              ) : null}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-ink-500">Funding range</dt>
            <dd className="text-xl font-semibold tabular-nums text-ink-950">{formatRange(c.funding_low, c.funding_high)}</dd>
          </div>
          <div>
            <dt className="text-sm text-ink-500">Recommendation</dt>
            <dd className="text-xl font-semibold text-ink-950">{formatRecommendation(c.recommendation)}</dd>
          </div>
        </dl>
      </div>
    </header>
  );
}

function Section({ title, id, children }: { title: string; id: string; children: React.ReactNode }) {
  const headingId = `${id}-title`;
  return (
    <section aria-labelledby={headingId} className={`${panel} p-6`}>
      <h2 id={headingId} className={`${sectionTitle} scroll-mt-6`}>
        {title}
      </h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Field({
  label,
  value,
  breakAll,
  noTranslate,
}: {
  label: string;
  value: string;
  breakAll?: boolean;
  noTranslate?: boolean;
}) {
  return (
    <div>
      <dt className="text-sm text-ink-500">{label}</dt>
      <dd translate={noTranslate ? "no" : undefined} className={`text-ink-950 ${breakAll ? "break-all" : "break-words"}`}>
        {value}
      </dd>
    </div>
  );
}

function Quote({ children }: { children: React.ReactNode }) {
  return <blockquote className="mt-2 border-l-2 border-accent-500 pl-3 italic text-ink-700">{children}</blockquote>;
}

type FactRow = {
  label: string;
  value: string;
  source: string | null;
  grounded: boolean | null;
  note?: string;
};

function factRows(e: NonNullable<Extraction>, reported: string | null): FactRow[] {
  const coverage = e.insurance_coverage?.value;
  const coverageText = coverage
    ? [coverage.insurer, typeof coverage.policy_limit === "number" ? `policy limit ${formatMoney(coverage.policy_limit)}` : null]
        .filter(Boolean)
        .join(", ") || EMPTY
    : EMPTY;

  const rows: FactRow[] = [
    {
      label: "Injury type",
      value: e.injury_type?.value ? sentenceCase(e.injury_type.value) : EMPTY,
      source: e.injury_type?.source_text ?? null,
      grounded: e.injury_type ? e.injury_type.grounded : null,
      note: reported ? `Claimant reported: ${reported}` : undefined,
    },
    {
      label: "Incident date",
      value: e.incident_date?.value ? formatDate(`${e.incident_date.value}T12:00:00Z`) : EMPTY,
      source: e.incident_date?.source_text ?? null,
      grounded: e.incident_date ? e.incident_date.grounded : null,
    },
    {
      label: "Insurance coverage",
      value: coverageText,
      source: e.insurance_coverage?.source_text ?? null,
      grounded: e.insurance_coverage ? e.insurance_coverage.grounded : null,
    },
    {
      label: "Claimed damages",
      value: formatMoney(e.claimed_damages?.value),
      source: e.claimed_damages?.source_text ?? null,
      grounded: e.claimed_damages ? e.claimed_damages.grounded : null,
    },
  ];

  for (const [i, li] of (e.liability_indicators ?? []).entries()) {
    rows.push({
      label: i === 0 ? "Liability indicators" : "",
      value: li.value ?? EMPTY,
      source: li.source_text,
      grounded: li.grounded,
    });
  }
  return rows;
}

function ExtractedFacts({ extraction, reported }: { extraction: Extraction; reported: string | null }) {
  if (!extraction) {
    return <p className="text-ink-700">Facts have not been extracted yet.</p>;
  }
  const g = extraction.grounding;
  const rows = factRows(extraction, reported);
  const hasLiability = (extraction.liability_indicators ?? []).length > 0;

  return (
    <>
      {g ? (
        <p className="text-ink-950">
          <span className="font-semibold tabular-nums">
            {g.grounded}/{g.checked}
          </span>{" "}
          values verified against source document
          {g.ungrounded_fields.length > 0 ? (
            <span className="text-danger">. Unverified: {g.ungrounded_fields.map(sentenceCase).join(", ")}</span>
          ) : null}
          .
        </p>
      ) : null}
      <dl className="mt-4 divide-y divide-paper-200 border-t border-paper-200">
        {rows.map((row, i) => (
          <div key={i} className="grid gap-1 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6">
            <dt className="text-sm text-ink-500">{row.label}</dt>
            <dd className="min-w-0">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="font-medium text-ink-950">{row.value}</span>
                {row.grounded !== null ? <GroundedBadge grounded={row.grounded} /> : null}
              </div>
              {row.source ? <Quote>{row.source}</Quote> : null}
              {row.note ? <p className="mt-2 text-sm text-ink-500">{row.note}</p> : null}
            </dd>
          </div>
        ))}
        {!hasLiability ? (
          <div className="grid gap-1 py-4 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-6">
            <dt className="text-sm text-ink-500">Liability indicators</dt>
            <dd className="text-ink-950">{EMPTY}</dd>
          </div>
        ) : null}
      </dl>
    </>
  );
}

function ScoringFactors({ c }: { c: CaseDetail }) {
  const factors = c.score_factors ?? [];
  if (factors.length === 0) {
    return <p className="text-ink-700">This case has not been scored yet.</p>;
  }
  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] border-collapse text-left text-sm">
          <caption className="sr-only">
            Scoring factors. Negative impact lowers risk, positive impact raises it.
          </caption>
          <thead>
            <tr className="border-b border-paper-200">
              <th scope="col" className="py-2 pr-4 font-medium text-ink-500">
                Factor
              </th>
              <th scope="col" className="py-2 pr-4 text-right font-medium text-ink-500">
                Impact
              </th>
              <th scope="col" className="py-2 font-medium text-ink-500">
                Evidence
              </th>
            </tr>
          </thead>
          <tbody>
            {factors.map((f, i) => (
              <tr key={i} className="border-b border-paper-200 align-top last:border-b-0">
                <td className="py-3 pr-4 text-ink-950">{f.factor}</td>
                <td
                  className={`whitespace-nowrap py-3 pr-4 text-right font-semibold tabular-nums ${f.impact < 0 ? "text-success" : f.impact > 0 ? "text-danger" : "text-ink-700"}`}
                >
                  {formatImpact(f.impact)}
                </td>
                <td className="py-3">
                  {f.evidence ? (
                    <span className="block border-l-2 border-accent-500 pl-3 italic text-ink-700">{f.evidence}</span>
                  ) : (
                    EMPTY
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-sm text-ink-500">Negative impact lowers risk. Positive impact raises it.</p>
      {c.reasoning ? <p className="mt-4 max-w-[72ch] text-ink-950">{c.reasoning}</p> : null}
    </>
  );
}

const REDACTION_LABELS: Record<string, [string, string]> = {
  name: ["name", "names"],
  email: ["email address", "email addresses"],
  phone: ["phone number", "phone numbers"],
  sin: ["SIN", "SINs"],
  dob: ["date of birth", "dates of birth"],
  address: ["address", "addresses"],
  postal_code: ["postal code", "postal codes"],
  health_card: ["health card number", "health card numbers"],
};

function redactionSummary(counts: Record<string, number> | null): string {
  const parts = Object.entries(counts ?? {})
    .filter(([, n]) => n > 0)
    .map(([key, n]) => {
      const [one, many] = REDACTION_LABELS[key] ?? [sentenceCase(key).toLowerCase(), `${sentenceCase(key).toLowerCase()} items`];
      return `${n} ${n === 1 ? one : many}`;
    });
  return parts.length > 0
    ? `Redacted before AI analysis: ${parts.join(", ")}.`
    : "No personal information was detected for redaction.";
}

function actorLabel(actor: string): string {
  const [kind, who] = actor.split(":", 2);
  if (kind === "attorney" && who) return who;
  if (actor === "service:n8n") return "Automated workflow";
  if (actor === "public:portal") return "Intake portal";
  if (kind === "system") return "System";
  return actor;
}

function AuditTrail({ entries }: { entries: AuditEntry[] }) {
  if (entries.length === 0) return <p className="text-ink-700">No activity recorded yet.</p>;
  return (
    <ol className="space-y-4">
      {entries.map((e, i) => (
        <li key={`${e.at}-${i}`} className="border-l-2 border-paper-200 pl-3">
          <p className="font-medium text-ink-950">{sentenceCase(e.action)}</p>
          <p className="break-all text-sm text-ink-700">{actorLabel(e.actor)}</p>
          <p className="text-sm tabular-nums text-ink-500">
            <time dateTime={e.at}>{formatDateTime(e.at)}</time>
          </p>
        </li>
      ))}
    </ol>
  );
}

function DetailSkeleton() {
  return (
    <div className={`${panel} mt-6 px-6 py-10`} role="status" aria-live="polite">
      <p className="text-ink-500">Loading case…</p>
    </div>
  );
}
