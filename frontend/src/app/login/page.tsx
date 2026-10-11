import type { Metadata } from "next";
import Link from "next/link";
import { pageWidth, panel, textLink } from "@/lib/ui";
import { LoginForm } from "./login-form";

export const metadata: Metadata = {
  title: "Attorney sign in | Litigation Funding Underwriting Agent",
};

export default function LoginPage() {
  return (
    <main id="main" tabIndex={-1} className={`${pageWidth} flex flex-1 flex-col justify-center py-16`}>
      <div className="mx-auto w-full max-w-sm">
        <Link href="/" className={`${textLink} text-sm`}>
          Back to home
        </Link>
        <h1 className="mt-6 font-serif text-3xl font-semibold text-ink-950">Attorney portal</h1>
        <p className="mt-2 text-ink-700">Sign in to review cases.</p>
        <div className={`${panel} mt-8 p-6`}>
          <LoginForm />
        </div>
      </div>
    </main>
  );
}
