import type { Metadata } from "next";
import Link from "next/link";
import { pageWidth, textLink } from "@/lib/ui";
import { ApplyForm } from "./apply-form";

export const metadata: Metadata = {
  title: "Apply for funding | Litigation Funding Underwriting Agent",
};

export default function ApplyPage() {
  return (
    <main id="main" tabIndex={-1} className={`${pageWidth} py-10`}>
      <div className="mx-auto max-w-2xl">
        <Link href="/" className={`${textLink} text-sm`}>
          Back to home
        </Link>
        <h1 className="mt-6 font-serif text-3xl font-semibold text-ink-950">Apply for funding</h1>
        <p className="mt-2 text-ink-700">
          Tell us about your injury and upload one document, such as a police report or hospital statement.
        </p>
        <div
          role="note"
          className="mt-6 rounded-md border border-warning/30 bg-warning-bg px-4 py-3 text-sm font-medium text-warning"
        >
          Demo only. Do not submit real personal information.
        </div>
        <ApplyForm />
      </div>
    </main>
  );
}
