# Litigation Funding Underwriting Agent

## Project rules
- Backend (backend\) is written and tested. Do not modify backend\lfa\*, main_lfa.py, or create_attorney.py unless explicitly asked.
- Never print, log, or commit secrets (.env, .env.local, API keys, SERVICE_TOKEN, Slack webhook URLs).
- JWT lives only in an httpOnly cookie. Never use localStorage. Dashboard data is fetched server-side.
- Synthetic data only. Windows + PowerShell: use curl.exe, not the curl alias.

## Frontend design system (non-negotiable)
Installed skills (frontend-design, web-design-guidelines, vercel-react-best-practices)

### Direction
Legal-tech for underwriters and attorneys: calm, precise, trustworthy, editorial. Think a well-designed law firm brief or financial terminal, not a SaaS landing page.

### Typography (load with next/font/google)
- Headings: "Source Serif 4", weight 600. Body and UI: "Inter". Numbers in tables and scores: Inter with `tabular-nums`.
- Clear hierarchy: page title text-3xl, section title text-lg uppercase tracking-wide text-ink-500, body text-[15px] leading-relaxed.

### Color tokens (define in Tailwind theme / CSS variables; use only these)
- ink: 950 #0B1220, 900 #111A2E, 700 #2A3550, 500 #5B6680, 300 #A9B1C3
- paper: 50 #FAF8F4 (page background), 100 #F2EEE6 (panels), 200 #E4DED2 (borders)
- accent (brass): 600 #9A6B1F, 500 #B7832F, 100 #F5EAD3
- semantic: success #1F6F4A on #E3F1E9, warning #8A5A00 on #FBEFD5, danger #A12C2C on #F7E1E1
- Risk score: <40 success, 40-69 warning, >=70 danger. Status badges use the semantic pairs.

### Banned defaults
- No purple or blue-purple gradients. No gradients on backgrounds at all.
- No generic `bg-white shadow-md rounded-lg` cards. Panels use paper-100 with a 1px paper-200 border, rounded-md, no drop shadow (or shadow-sm at most).
- No emoji in the UI. No stock illustrations. No centered hero with giant gradient text.

### Interaction (required on every interactive element)
- Every button, link, input, and row link has explicit `hover:`, `focus-visible:` (2px accent-500 ring with offset), and `active:` styles.
- Primary button: ink-900 background, paper-50 text, hover ink-700. Secondary: transparent with ink-300 border, hover paper-100. Destructive: danger text and border.
- Disabled and loading states are visible (reduced opacity plus a "Submitting…" label).
- Transitions: `transition-colors duration-150`. No bouncy or decorative animation.

### Layout
- Max content width 1120px, generous whitespace (py-10 sections, gap-6 grids).
- Dashboard table: sticky header, zebra rows using paper-100, right-aligned numeric columns, whole row clickable with hover state.
- Case detail: two-column on desktop (main: memo, facts, factors; side: decision actions, claimant card, redaction summary, audit trail). Stack on mobile.
- Source quotes: italic, left border 2px accent-500, pl-3, text-ink-700.
- Grounded badge: success pair with a check mark. Unverified badge: danger pair.

### Accessibility
- WCAG AA contrast. Labels on every input. aria-live region for form errors and success. Keyboard-navigable.
