"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { textLink } from "@/lib/ui";

export function RefreshButton() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <button
      type="button"
      onClick={() => startTransition(() => router.refresh())}
      disabled={pending}
      className={`${textLink} text-sm disabled:cursor-wait disabled:opacity-60`}
    >
      {pending ? "Refreshing…" : "Refresh"}
    </button>
  );
}
