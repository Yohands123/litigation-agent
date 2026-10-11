"use server";

import { revalidatePath } from "next/cache";
import { unstable_rethrow } from "next/navigation";
import { BackendError, updateCaseStatus } from "@/lib/backend";
import type { DecisionStatus } from "@/lib/types";

export type DecisionState = { ok: boolean; message: string } | null;

const LABELS: Partial<Record<DecisionStatus, string>> = {
  approved: "Approved",
  declined: "Declined",
  needs_info: "Needs info",
};

const CASE_ID = /^[0-9a-f-]{36}$/i;

export async function decideCase(_prev: DecisionState, formData: FormData): Promise<DecisionState> {
  const caseId = String(formData.get("case_id") ?? "");
  const status = String(formData.get("status") ?? "") as DecisionStatus;
  const note = String(formData.get("note") ?? "").trim().slice(0, 1000);

  if (!CASE_ID.test(caseId) || !(status in LABELS)) {
    return { ok: false, message: "That decision could not be recorded. Reload the page and try again." };
  }

  try {
    // The backend authorizes this with the JWT from the httpOnly cookie.
    await updateCaseStatus(caseId, status, note || undefined);
  } catch (error) {
    unstable_rethrow(error);
    const detail = error instanceof BackendError ? error.message : "The underwriting service is unreachable.";
    return { ok: false, message: `Decision not saved. ${detail}` };
  }

  revalidatePath(`/dashboard/${caseId}`);
  revalidatePath("/dashboard");
  return { ok: true, message: `Decision recorded: ${LABELS[status]}.` };
}
