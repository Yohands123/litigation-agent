// Shared class strings so every interactive element gets the same hover, focus and active states.

export const focusRing =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 focus-visible:ring-offset-2 focus-visible:ring-offset-paper-50";

const buttonBase = `inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-60 ${focusRing}`;

export const buttonPrimary = `${buttonBase} bg-ink-900 text-paper-50 hover:bg-ink-700 active:bg-ink-950 disabled:hover:bg-ink-900`;

export const buttonSecondary = `${buttonBase} border border-ink-300 text-ink-900 hover:bg-paper-100 active:bg-paper-200 disabled:hover:bg-transparent`;

export const buttonDestructive = `${buttonBase} border border-danger text-danger hover:bg-danger-bg active:bg-paper-200 disabled:hover:bg-transparent`;

export const textLink = `rounded-sm text-ink-900 underline decoration-ink-300 underline-offset-4 transition-colors duration-150 hover:text-ink-700 hover:decoration-ink-700 active:text-ink-950 ${focusRing}`;

export const inputBase = `block w-full rounded-md border border-ink-500 bg-paper-50 px-3 py-2 text-[15px] text-ink-950 placeholder:text-ink-500 transition-colors duration-150 hover:border-ink-700 hover:bg-paper-100 active:border-ink-900 focus-visible:border-ink-900 disabled:opacity-60 ${focusRing}`;

export const labelBase = "block text-sm font-medium text-ink-900";

export const panel = "rounded-md border border-paper-200 bg-paper-100";

export const sectionTitle = "text-lg font-medium uppercase tracking-wide text-ink-500";

export const pageWidth = "mx-auto w-full max-w-[1120px] px-6";
