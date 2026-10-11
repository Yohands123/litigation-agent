# Evals

Measures how accurately the extraction step pulls case facts out of documents, whether its source quotes are real, and whether PII redaction holds.

## Run

The backend must be running on `http://localhost:8000` with `SERVICE_TOKEN` and `OPENAI_API_KEY` set in `backend/.env`. From the repo root (Windows paths shown):

```powershell
backend\venv\Scripts\python.exe evals\generate_cases.py
backend\venv\Scripts\python.exe evals\run_evals.py
```

`generate_cases.py` is deterministic (fixed seed, no LLM), so the cases and labels are identical on every run. `run_evals.py` calls the real model, so results can vary slightly between runs.

Set `LFA_API_URL` to evaluate a different backend. After editing `analysis.md`, rebuild the report without calling the API:

```powershell
backend\venv\Scripts\python.exe evals\run_evals.py --render-only
```

## What it does

1. **Cases.** `generate_cases.py` writes 15 synthetic police reports, premises reports, demand letters, statements and hospital bills to `cases/`, with ground truth in `cases/labels.json`. They vary liability (clear, disputed, claimant at fault), insurance (full, insurer only, none), damages (total line, itemized only, prose, none), injury type, date format, and document layout. Two cases state key facts only in prose, one is older than two years, and two mention the claimant's name in unlabeled prose to test redaction.
2. **Extraction accuracy.** Each case is sent as `{"text": ...}` to `POST /extract` with `X-Service-Token`. The backend redacts PII, then extracts. Six fields are scored per case:

   | Field | Correct when |
   |---|---|
   | Injury type | Any accepted keyword appears in the extracted value |
   | Incident date | Exact ISO match |
   | Insurer | Case-insensitive substring match either way; null must be null |
   | Policy limit | Exact numeric match; null must be null |
   | Claimed damages | Within 1%; null must be null |
   | Liability indicators | Every expected concept appears in the joined indicator values (`a\|b` means either is accepted) |

3. **Grounding.** The backend checks that every `source_text` quote appears verbatim in the redacted document. The eval reports total grounded quotes over total checked.
4. **PII leak check.** Runs locally by importing `backend/lfa/redaction.py`. For each case it redacts the text and counts planted PII strings (claimant name, phone, email, SIN or SSN) that survive. It reports two numbers: redaction from the document alone, and redaction with the claimant's name from the intake form, which is what production does.

## Output

- `results.json`: raw per-case extractions, scores and grounding.
- `results.md`: summary table, per-case table, every failure with extracted and expected values, and the failure analysis from `analysis.md`.
