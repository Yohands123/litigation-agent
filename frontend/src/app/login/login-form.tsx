"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { buttonPrimary, inputBase, labelBase } from "@/lib/ui";

export function LoginForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const emailRef = useRef<HTMLInputElement>(null);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError(null);
    setSubmitting(true);

    let message: string | null = null;
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
      });
      if (res.ok) {
        router.push("/dashboard");
        router.refresh();
        return;
      }
      const body = await res.json().catch(() => null);
      message =
        res.status === 401
          ? "Invalid email or password"
          : (body?.error ?? "Sign-in failed. Wait a moment and sign in again.");
    } catch {
      message = "Could not reach the server. Check your connection and sign in again.";
    }
    setError(message);
    setSubmitting(false);
    emailRef.current?.focus();
  }

  const invalid = error ? true : undefined;
  const describedBy = error ? "login-error" : undefined;

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div>
        <label htmlFor="email" className={labelBase}>
          Email
        </label>
        <input
          ref={emailRef}
          id="email"
          name="email"
          type="email"
          required
          autoComplete="username"
          spellCheck={false}
          aria-invalid={invalid}
          aria-describedby={describedBy}
          className={`${inputBase} mt-1.5`}
        />
      </div>
      <div>
        <label htmlFor="password" className={labelBase}>
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoComplete="current-password"
          aria-invalid={invalid}
          aria-describedby={describedBy}
          className={`${inputBase} mt-1.5`}
        />
      </div>
      <div role="alert" aria-live="assertive">
        {error ? (
          <p id="login-error" className="rounded-md border border-danger/30 bg-danger-bg px-3 py-2 text-sm text-danger">
            {error}
          </p>
        ) : null}
      </div>
      <button type="submit" className={`${buttonPrimary} w-full`} disabled={submitting}>
        {submitting ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
