import { EMPTY, sentenceCase } from "@/lib/format";

type Tone = "success" | "warning" | "danger" | "neutral";

const TONE_CLASSES: Record<Tone, string> = {
  success: "bg-success-bg text-success",
  warning: "bg-warning-bg text-warning",
  danger: "bg-danger-bg text-danger",
  neutral: "bg-paper-200 text-ink-700",
};

const STATUS: Record<string, { label: string; tone: Tone }> = {
  submitted: { label: "Submitted", tone: "neutral" },
  processing: { label: "Processing", tone: "neutral" },
  extracted: { label: "Extracted", tone: "neutral" },
  scored: { label: "Scored", tone: "neutral" },
  ready_for_review: { label: "Ready for review", tone: "warning" },
  needs_info: { label: "Needs info", tone: "warning" },
  approved: { label: "Approved", tone: "success" },
  declined: { label: "Declined", tone: "danger" },
  failed: { label: "Extraction failed", tone: "danger" },
  trigger_failed: { label: "Workflow not started", tone: "danger" },
};

function Pill({ tone, children }: { tone: Tone; children: React.ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-sm px-2 py-0.5 text-xs font-medium ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS[status] ?? { label: sentenceCase(status), tone: "neutral" as const };
  return <Pill tone={s.tone}>{s.label}</Pill>;
}

export function riskTone(score: number): Tone {
  if (score >= 70) return "danger";
  if (score >= 40) return "warning";
  return "success";
}

const RISK_LABEL: Record<Tone, string> = {
  success: "low risk",
  warning: "moderate risk",
  danger: "high risk",
  neutral: "",
};

export function RiskBadge({ score }: { score: number | null }) {
  if (typeof score !== "number") return <span className="text-ink-500">{EMPTY}</span>;
  const tone = riskTone(score);
  return (
    <span
      className={`inline-flex min-w-10 justify-center rounded-sm px-2 py-0.5 text-sm font-semibold tabular-nums ${TONE_CLASSES[tone]}`}
      aria-label={`Risk score ${score} out of 100, ${RISK_LABEL[tone]}`}
    >
      {score}
    </span>
  );
}

export function GroundedBadge({ grounded }: { grounded: boolean }) {
  return grounded ? (
    <Pill tone="success">
      <svg aria-hidden="true" viewBox="0 0 12 12" className="size-3" fill="none">
        <path d="M2.5 6.5l2.2 2.2L9.5 3.8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      Grounded
    </Pill>
  ) : (
    <Pill tone="danger">Unverified</Pill>
  );
}
