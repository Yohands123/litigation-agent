import "server-only";
import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";
import type { AuditEntry, CaseDetail, CaseSummary, DecisionStatus } from "./types";

export const TOKEN_COOKIE = "lfa_token";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export class BackendError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

/**
 * Calls the FastAPI backend with the attorney's JWT from the httpOnly cookie.
 * The token never leaves the server. A missing or rejected token sends the user to /login.
 */
async function backendFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = (await cookies()).get(TOKEN_COOKIE)?.value;
  if (!token) redirect("/login");

  const res = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...init?.headers,
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (res.status === 401) redirect("/login");
  if (res.status === 404) notFound();
  if (!res.ok) {
    throw new BackendError(await readDetail(res), res.status);
  }
  return (await res.json()) as T;
}

async function readDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // Non-JSON error body; fall through to the generic message.
  }
  return `Backend request failed (${res.status})`;
}

export function listCases(): Promise<CaseSummary[]> {
  return backendFetch<CaseSummary[]>("/cases");
}

export function getCase(id: string): Promise<CaseDetail> {
  return backendFetch<CaseDetail>(`/cases/${encodeURIComponent(id)}`);
}

export function getCaseAudit(id: string): Promise<AuditEntry[]> {
  return backendFetch<AuditEntry[]>(`/cases/${encodeURIComponent(id)}/audit`);
}

export function updateCaseStatus(id: string, status: DecisionStatus, note?: string) {
  return backendFetch<CaseSummary>(`/cases/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(note ? { status, note } : { status }),
  });
}
