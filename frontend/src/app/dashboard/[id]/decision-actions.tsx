"use client";

import { useActionState, useRef, useState } from "react";
import { buttonDestructive, buttonPrimary, buttonSecondary, inputBase, labelBase } from "@/lib/ui";
import { decideCase, type DecisionState } from "./actions";

const DECISIONS = [
  { status: "approved", label: "Approve", className: buttonPrimary },
  { status: "needs_info", label: "Needs info", className: buttonSecondary },
  { status: "declined", label: "Decline", className: buttonDestructive },
] as const;

export function DecisionActions({ caseId, currentStatus }: { caseId: string; currentStatus: string }) {
  const [state, formAction, pending] = useActionState<DecisionState, FormData>(decideCase, null);
  const [chosen, setChosen] = useState<string | null>(null);
  // Holds the action result that was current when the confirmation opened; a new result closes it.
  const [confirmFor, setConfirmFor] = useState<{ state: DecisionState } | null>(null);
  const confirmingDecline = confirmFor !== null && confirmFor.state === state;
  const confirmRef = useRef<HTMLButtonElement>(null);
  const declineRef = useRef<HTMLButtonElement>(null);
  const hasCurrent = DECISIONS.some((d) => d.status === currentStatus);

  return (
    <form action={formAction} className="space-y-4">
      <input type="hidden" name="case_id" value={caseId} />
      <div>
        <label htmlFor="decision-note" className={labelBase}>
          Note <span className="font-normal text-ink-500">(optional, saved to the audit trail)</span>
        </label>
        <textarea
          id="decision-note"
          name="note"
          rows={2}
          maxLength={1000}
          autoComplete="off"
          disabled={pending}
          className={`${inputBase} mt-1.5 resize-y text-sm`}
        />
      </div>

      {confirmingDecline ? (
        <div className="space-y-3 rounded-md border border-danger/30 bg-danger-bg p-3">
          <p id="decline-confirm-text" className="text-sm font-medium text-danger">
            Decline this case? The claimant will not receive funding.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              ref={confirmRef}
              type="submit"
              name="status"
              value="declined"
              onClick={() => setChosen("declined")}
              disabled={pending}
              aria-describedby="decline-confirm-text"
              className={`${buttonDestructive} flex-1 bg-paper-50`}
            >
              {pending && chosen === "declined" ? "Submitting…" : "Confirm decline"}
            </button>
            <button
              type="button"
              onClick={() => {
                setConfirmFor(null);
                requestAnimationFrame(() => declineRef.current?.focus());
              }}
              disabled={pending}
              className={`${buttonSecondary} flex-1 bg-paper-50`}
            >
              Keep case open
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {DECISIONS.map((d) => {
            const isCurrent = currentStatus === d.status;
            const isPending = pending && chosen === d.status;
            const describedBy = isCurrent ? "decision-current" : undefined;
            const disabled = pending || isCurrent;

            if (d.status === "declined") {
              return (
                <button
                  key={d.status}
                  ref={declineRef}
                  type="button"
                  onClick={() => {
                    setConfirmFor({ state });
                    requestAnimationFrame(() => confirmRef.current?.focus());
                  }}
                  disabled={disabled}
                  aria-describedby={describedBy}
                  className={`${d.className} flex-1`}
                >
                  {d.label}
                </button>
              );
            }
            return (
              <button
                key={d.status}
                type="submit"
                name="status"
                value={d.status}
                onClick={() => setChosen(d.status)}
                disabled={disabled}
                aria-describedby={describedBy}
                className={`${d.className} flex-1`}
              >
                {isPending ? "Submitting…" : d.label}
              </button>
            );
          })}
        </div>
      )}

      {hasCurrent ? (
        <p id="decision-current" className="text-sm text-ink-500">
          The button for the current decision is disabled.
        </p>
      ) : null}
      <div role="status" aria-live="polite">
        {state ? (
          <p
            className={`rounded-md px-3 py-2 text-sm ${state.ok ? "bg-success-bg text-success" : "bg-danger-bg text-danger"}`}
          >
            {state.message}
          </p>
        ) : null}
      </div>
    </form>
  );
}
