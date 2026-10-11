"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { buttonPrimary, buttonSecondary, inputBase, labelBase, panel, textLink } from "@/lib/ui";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const MAX_BYTES = 10 * 1024 * 1024;

const INJURY_TYPES = [
  "Car accident - whiplash",
  "Car accident - fracture",
  "Slip and fall",
  "Workplace injury",
  "Other",
] as const;

const FIELDS = ["claimant_name", "claimant_email", "claimant_phone", "injury_type", "incident_description", "file"] as const;
type Field = (typeof FIELDS)[number];
type FieldErrors = Partial<Record<Field, string>>;

type State =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "error"; message: string | null; fields: FieldErrors }
  | { kind: "done"; caseId: string };

function isField(value: unknown): value is Field {
  return typeof value === "string" && (FIELDS as readonly string[]).includes(value);
}

/** Maps a FastAPI error body to per-field messages where possible, otherwise one form-level message. */
function parseDetail(detail: unknown): { message: string | null; fields: FieldErrors } {
  if (typeof detail === "string") {
    if (/email/i.test(detail)) return { message: null, fields: { claimant_email: detail } };
    if (/file|document|MB/i.test(detail)) return { message: null, fields: { file: detail } };
    return { message: detail, fields: {} };
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const fields: FieldErrors = {};
    const loose: string[] = [];
    for (const d of detail) {
      const key = Array.isArray(d?.loc) ? d.loc[d.loc.length - 1] : null;
      const msg = String(d?.msg ?? "Invalid value");
      if (isField(key)) fields[key] ??= msg;
      else loose.push(msg);
    }
    return { message: loose.length ? loose.join(". ") : null, fields };
  }
  return { message: null, fields: {} };
}

function clientCheck(form: FormData): FieldErrors {
  const errors: FieldErrors = {};
  if (String(form.get("incident_description") ?? "").trim().length < 10) {
    errors.incident_description = "Describe the incident in at least 10 characters.";
  }
  const file = form.get("file");
  if (!(file instanceof File) || file.size === 0) {
    errors.file = "Choose a .pdf or .txt document to upload.";
  } else if (!/\.(pdf|txt)$/i.test(file.name)) {
    errors.file = "Upload a .pdf or .txt file. Other formats are not supported.";
  } else if (file.size > MAX_BYTES) {
    errors.file = "Upload a file of 10 MB or smaller.";
  }
  return errors;
}

export function ApplyForm() {
  const [state, setState] = useState<State>({ kind: "idle" });
  const [dirty, setDirty] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const formErrorRef = useRef<HTMLParagraphElement>(null);
  const submitting = state.kind === "submitting";
  const fieldErrors = state.kind === "error" ? state.fields : {};

  // Warn before leaving with an unsent application.
  useEffect(() => {
    if (!dirty || state.kind === "done") return;
    const onBeforeUnload = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [dirty, state.kind]);

  function showErrors(message: string | null, fields: FieldErrors) {
    setState({ kind: "error", message, fields });
    // Focus the first invalid field in form order, or the form-level message.
    requestAnimationFrame(() => {
      const first = FIELDS.find((f) => fields[f]);
      if (first) document.getElementById(first)?.focus();
      else formErrorRef.current?.focus();
    });
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    if (!String(form.get("claimant_phone") ?? "").trim()) form.delete("claimant_phone");

    const problems = clientCheck(form);
    if (Object.keys(problems).length > 0) {
      showErrors(null, problems);
      return;
    }

    setState({ kind: "submitting" });
    try {
      const res = await fetch(`${API_URL}/cases`, { method: "POST", body: form });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        const parsed = parseDetail(body?.detail);
        showErrors(
          parsed.message ??
            (Object.keys(parsed.fields).length ? null : `Submission failed (${res.status}). Check your details and submit again.`),
          parsed.fields,
        );
        return;
      }
      setDirty(false);
      setState({ kind: "done", caseId: String(body.case_id) });
    } catch {
      showErrors("Could not reach the intake service. Check your connection and submit again.", {});
    }
  }

  function fieldProps(name: Field, hintId?: string) {
    const error = fieldErrors[name];
    const describedBy = [hintId, error ? `${name}_error` : null].filter(Boolean).join(" ") || undefined;
    return {
      id: name,
      name,
      "aria-invalid": error ? true : undefined,
      "aria-describedby": describedBy,
      className: `${inputBase} mt-1.5 ${error ? "border-danger hover:border-danger" : ""}`,
    };
  }

  function fieldError(name: Field) {
    const error = fieldErrors[name];
    return error ? (
      <p id={`${name}_error`} className="mt-1.5 text-sm font-medium text-danger">
        {error}
      </p>
    ) : null;
  }

  if (state.kind === "done") {
    return (
      <section className={`${panel} mt-8 p-6`} aria-labelledby="confirmation-title">
        <div role="status" aria-live="polite">
          <h2 id="confirmation-title" className="font-serif text-2xl font-semibold text-ink-950">
            Application received
          </h2>
          <p className="mt-3 text-ink-700">An attorney will review your case.</p>
          <p className="mt-4 text-sm text-ink-700">Case reference</p>
          <p translate="no" className="mt-1 break-all font-medium tabular-nums text-ink-950">
            {state.caseId}
          </p>
        </div>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/" className={buttonSecondary}>
            Back to home
          </Link>
          <button
            type="button"
            className={buttonSecondary}
            onClick={() => {
              setState({ kind: "idle" });
              formRef.current?.reset();
            }}
          >
            Submit another case
          </button>
        </div>
      </section>
    );
  }

  return (
    <form ref={formRef} onSubmit={onSubmit} onInput={() => setDirty(true)} className="mt-8 space-y-6">
      <div className="grid gap-6 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label htmlFor="claimant_name" className={labelBase}>
            Full name
          </label>
          <input {...fieldProps("claimant_name")} type="text" required maxLength={200} autoComplete="name" />
          {fieldError("claimant_name")}
        </div>
        <div className="min-w-0">
          <label htmlFor="claimant_email" className={labelBase}>
            Email
          </label>
          <input
            {...fieldProps("claimant_email")}
            type="email"
            required
            maxLength={255}
            autoComplete="email"
            spellCheck={false}
          />
          {fieldError("claimant_email")}
        </div>
        <div className="min-w-0">
          <label htmlFor="claimant_phone" className={labelBase}>
            Phone <span className="font-normal text-ink-500">(optional)</span>
          </label>
          <input {...fieldProps("claimant_phone")} type="tel" inputMode="tel" maxLength={64} autoComplete="tel" />
          {fieldError("claimant_phone")}
        </div>
      </div>

      <div>
        <label htmlFor="injury_type" className={labelBase}>
          Injury type
        </label>
        <select {...fieldProps("injury_type")} required defaultValue="" autoComplete="off">
          <option value="" disabled>
            Select the closest match
          </option>
          {INJURY_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        {fieldError("injury_type")}
      </div>

      <div>
        <label htmlFor="incident_description" className={labelBase}>
          Incident description
        </label>
        <p id="incident_description_hint" className="mt-1 text-sm text-ink-500">
          What happened, where, and when. At least 10 characters.
        </p>
        <textarea
          {...fieldProps("incident_description", "incident_description_hint")}
          required
          minLength={10}
          maxLength={5000}
          rows={5}
          autoComplete="off"
        />
        {fieldError("incident_description")}
      </div>

      <div>
        <label htmlFor="file" className={labelBase}>
          Supporting document
        </label>
        <input
          {...fieldProps("file", "file_hint")}
          type="file"
          required
          accept=".pdf,.txt,application/pdf,text/plain"
        />
        <p id="file_hint" className="mt-1.5 text-sm text-ink-500">
          PDF or plain text, up to 10&nbsp;MB. Personal information is redacted before AI analysis.
        </p>
        {fieldError("file")}
      </div>

      <div role="alert" aria-live="assertive">
        {state.kind === "error" && state.message ? (
          <p
            ref={formErrorRef}
            tabIndex={-1}
            className="rounded-md border border-danger/30 bg-danger-bg px-4 py-3 text-sm text-danger focus:outline-none"
          >
            {state.message}
          </p>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <button type="submit" className={buttonPrimary} disabled={submitting}>
          {submitting ? "Submitting…" : "Submit application"}
        </button>
        <Link href="/" className={`${textLink} text-sm`}>
          Cancel
        </Link>
      </div>
    </form>
  );
}
