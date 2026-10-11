export type CaseStatus =
  | "submitted"
  | "processing"
  | "failed"
  | "extracted"
  | "trigger_failed"
  | "scored"
  | "ready_for_review"
  | "approved"
  | "declined"
  | "needs_info";

export type DecisionStatus = "approved" | "declined" | "needs_info" | "ready_for_review";

export type CaseSummary = {
  id: string;
  status: CaseStatus | string;
  injury_type: string | null;
  risk_score: number | null;
  funding_low: number | null;
  funding_high: number | null;
  recommendation: string | null;
  created_at: string | null;
};

export type Grounded<T> = {
  value: T | null;
  source_text: string | null;
  grounded: boolean;
} | null;

export type Extraction = {
  injury_type?: Grounded<string>;
  incident_date?: Grounded<string>;
  insurance_coverage?: Grounded<{ insurer: string | null; policy_limit: number | null }>;
  claimed_damages?: Grounded<number>;
  liability_indicators?: NonNullable<Grounded<string>>[] | null;
  grounding?: { checked: number; grounded: number; ungrounded_fields: string[] } | null;
  model?: string;
} | null;

export type ScoreFactor = { factor: string; impact: number; evidence: string | null };

export type CaseDetail = CaseSummary & {
  claimant: { name: string; email: string; phone: string | null };
  injury_type_reported: string | null;
  incident_description_redacted: string | null;
  document_filename: string | null;
  redaction_counts: Record<string, number> | null;
  extraction: Extraction;
  score_factors: ScoreFactor[] | null;
  reasoning: string | null;
  memo: string | null;
  updated_at: string | null;
};

export type AuditEntry = {
  actor: string;
  action: string;
  details: Record<string, unknown> | null;
  at: string;
};
