export const EMPTY = "—";

const currency = new Intl.NumberFormat("en-CA", {
  style: "currency",
  currency: "CAD",
  currencyDisplay: "narrowSymbol",
  maximumFractionDigits: 0,
});

const dateFmt = new Intl.DateTimeFormat("en-CA", {
  year: "numeric",
  month: "short",
  day: "numeric",
  timeZone: "America/Toronto",
});

const dateTimeFmt = new Intl.DateTimeFormat("en-CA", {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
  timeZone: "America/Toronto",
  timeZoneName: "short",
});

export function formatMoney(value: number | null | undefined): string {
  return typeof value === "number" ? currency.format(value) : EMPTY;
}

export function formatRange(low: number | null | undefined, high: number | null | undefined): string {
  if (typeof low !== "number" || typeof high !== "number") return EMPTY;
  return `${currency.format(low)} – ${currency.format(high)}`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return EMPTY;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? EMPTY : dateFmt.format(d);
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return EMPTY;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? EMPTY : dateTimeFmt.format(d);
}

export function formatImpact(impact: number): string {
  if (impact > 0) return `+${impact}`;
  if (impact < 0) return `−${Math.abs(impact)}`;
  return "0";
}

const RECOMMENDATION_LABELS: Record<string, string> = {
  fund: "Fund",
  review: "Review",
  decline: "Decline",
};

export function formatRecommendation(value: string | null | undefined): string {
  if (!value) return EMPTY;
  return RECOMMENDATION_LABELS[value] ?? sentenceCase(value);
}

export function sentenceCase(value: string): string {
  const s = value.replace(/[_.]+/g, " ").trim();
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

export function shortId(id: string): string {
  return id.slice(0, 8).toUpperCase();
}
