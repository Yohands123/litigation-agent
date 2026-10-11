import Link from "next/link";
import { buttonSecondary, focusRing, pageWidth } from "@/lib/ui";

export default function DashboardLayout({ children }: LayoutProps<"/dashboard">) {
  return (
    <>
      <header className="border-b border-paper-200 bg-paper-100">
        <div className={`${pageWidth} flex flex-wrap items-center justify-between gap-4 py-4`}>
          <Link
            href="/dashboard"
            className={`rounded-sm font-serif text-lg font-semibold text-ink-950 transition-colors duration-150 hover:text-ink-700 active:text-ink-950 ${focusRing}`}
          >
            Litigation Funding Underwriting Agent
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-ink-500">Signed in</span>
            <form action="/api/auth/logout" method="post">
              <button type="submit" className={`${buttonSecondary} py-1.5`}>
                Log out
              </button>
            </form>
          </div>
        </div>
      </header>
      {children}
    </>
  );
}
