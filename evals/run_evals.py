"""Run the extraction eval suite against a running backend and a local PII leak check.

    python evals/generate_cases.py
    python evals/run_evals.py            # backend must be running on http://localhost:8000
    python evals/run_evals.py --render-only   # rebuild results.md from results.json, no API calls

Reads SERVICE_TOKEN from backend/.env (never printed). Writes evals/results.json and evals/results.md.
Set LFA_API_URL to point at a different backend.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
CASES = EVALS / "cases"
API_URL = os.getenv("LFA_API_URL", "http://localhost:8000").rstrip("/")

sys.path.insert(0, str(ROOT / "backend"))
from lfa.redaction import redact  # noqa: E402  (pure regex module, no env vars needed)

FIELDS = ["injury_type", "incident_date", "insurer", "policy_limit", "claimed_damages", "liability_indicators"]


def read_service_token() -> str:
    for line in (ROOT / "backend" / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("SERVICE_TOKEN="):
            token = line.split("=", 1)[1].strip()
            if token:
                return token
    sys.exit("SERVICE_TOKEN is missing from backend/.env")


def value(field: dict | None):
    return field.get("value") if isinstance(field, dict) else None


def concept_hit(concept: str, haystack: str) -> bool:
    """A concept matches if any of its '|' alternatives is a substring."""
    return any(alt.strip() in haystack for alt in concept.split("|"))


def score_case(label: dict, ext: dict) -> tuple[dict[str, bool], dict[str, object]]:
    """Returns (correct per field, extracted value per field)."""
    got: dict[str, object] = {}
    ok: dict[str, bool] = {}

    injury = value(ext.get("injury_type"))
    got["injury_type"] = injury
    ok["injury_type"] = bool(injury) and any(k in str(injury).lower() for k in label["injury_type_keywords"])

    d = value(ext.get("incident_date"))
    got["incident_date"] = d
    ok["incident_date"] = d == label["incident_date"]

    ins = value(ext.get("insurance_coverage")) or {}
    insurer = ins.get("insurer") if isinstance(ins, dict) else None
    limit = ins.get("policy_limit") if isinstance(ins, dict) else None
    got["insurer"], got["policy_limit"] = insurer, limit
    want_insurer = label["insurer"]
    if want_insurer is None:
        ok["insurer"] = not insurer
    else:
        a, b = str(insurer or "").lower().strip(), want_insurer.lower()
        ok["insurer"] = bool(a) and (a in b or b in a)
    want_limit = label["policy_limit"]
    if want_limit is None:
        ok["policy_limit"] = limit is None
    else:
        ok["policy_limit"] = isinstance(limit, (int, float)) and float(limit) == float(want_limit)

    dmg = value(ext.get("claimed_damages"))
    got["claimed_damages"] = dmg
    want_dmg = label["claimed_damages"]
    if want_dmg is None:
        ok["claimed_damages"] = dmg is None
    else:
        ok["claimed_damages"] = isinstance(dmg, (int, float)) and abs(float(dmg) - want_dmg) <= 0.01 * want_dmg

    indicators = [str(i.get("value") or "") for i in (ext.get("liability_indicators") or []) if isinstance(i, dict)]
    got["liability_indicators"] = indicators
    joined = " | ".join(indicators).lower()
    concepts = label["liability_concepts"]
    if concepts:
        ok["liability_indicators"] = all(concept_hit(c, joined) for c in concepts)
    else:
        ok["liability_indicators"] = not indicators or label["liability_direction"] == "mixed"

    return ok, got


def expected(label: dict) -> dict[str, object]:
    return {
        "injury_type": "any of " + ", ".join(label["injury_type_keywords"]),
        "incident_date": label["incident_date"],
        "insurer": label["insurer"],
        "policy_limit": label["policy_limit"],
        "claimed_damages": label["claimed_damages"],
        "liability_indicators": "must mention: " + "; ".join(label["liability_concepts"]) if label["liability_concepts"] else "none required",
    }


def pii_check(text: str, label: dict) -> dict:
    planted = label["planted_pii"]
    doc_only = redact(text).text
    with_name = redact(text, [label["claimant_name"]]).text
    leaked_doc = [p for p in planted if p in doc_only]
    leaked_name = [p for p in planted if p in with_name]
    return {"planted": len(planted), "leaked_doc_only": leaked_doc, "leaked_with_form_name": leaked_name}


def pct(n: int, d: int) -> str:
    return f"{100 * n / d:.1f}%" if d else "n/a"


def fmt(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, list):
        return "[" + "; ".join(v) + "]" if v else "[]"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def main() -> None:
    labels: dict = json.loads((CASES / "labels.json").read_text(encoding="utf-8"))
    token = read_service_token()
    results = []

    with httpx.Client(timeout=120) as client:
        for case_id, label in labels.items():
            text = (CASES / f"{case_id}.txt").read_text(encoding="utf-8")
            row: dict = {"case": case_id, "description": label["description"], "pii": pii_check(text, label)}
            started = time.perf_counter()
            try:
                r = client.post(f"{API_URL}/extract", json={"text": text}, headers={"X-Service-Token": token})
                r.raise_for_status()
                ext = r.json()
                ok, got = score_case(label, ext)
                row.update(
                    correct=ok,
                    extracted=got,
                    expected=expected(label),
                    grounding=ext.get("grounding") or {"checked": 0, "grounded": 0, "ungrounded_fields": []},
                    model=ext.get("model"),
                    error=None,
                )
            except Exception as e:  # keep going; an errored case scores 0 on every field
                status = getattr(getattr(e, "response", None), "status_code", None)
                row.update(
                    correct={f: False for f in FIELDS},
                    extracted={},
                    expected=expected(label),
                    grounding={"checked": 0, "grounded": 0, "ungrounded_fields": []},
                    model=None,
                    error=f"{type(e).__name__}{f' (HTTP {status})' if status else ''}: {str(e)[:200]}",
                )
            row["seconds"] = round(time.perf_counter() - started, 2)
            results.append(row)
            mark = "ERROR" if row["error"] else f"{sum(row['correct'].values())}/{len(FIELDS)}"
            print(f"  {case_id}: {mark}  ({row['seconds']}s)")

    # Aggregate
    n = len(results)
    per_field = {f: sum(r["correct"][f] for r in results) for f in FIELDS}
    total_correct = sum(per_field.values())
    total_fields = n * len(FIELDS)
    checked = sum(r["grounding"]["checked"] for r in results)
    grounded = sum(r["grounding"]["grounded"] for r in results)
    ungrounded = {r["case"]: r["grounding"]["ungrounded_fields"] for r in results if r["grounding"]["ungrounded_fields"]}
    planted = sum(r["pii"]["planted"] for r in results)
    leaks_doc = sum(len(r["pii"]["leaked_doc_only"]) for r in results)
    leaks_name = sum(len(r["pii"]["leaked_with_form_name"]) for r in results)
    errors = {r["case"]: r["error"] for r in results if r["error"]}
    model = next((r["model"] for r in results if r["model"]), None)

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "api_url": API_URL,
        "model": model,
        "cases": n,
        "errors": errors,
        "per_field_accuracy": {f: {"correct": per_field[f], "total": n} for f in FIELDS},
        "overall": {"correct": total_correct, "total": total_fields, "accuracy": total_correct / total_fields},
        "grounding": {"grounded": grounded, "checked": checked, "rate": grounded / checked if checked else None,
                      "ungrounded_by_case": ungrounded},
        "pii": {
            "planted": planted,
            "leaked_doc_only": leaks_doc,
            "recall_doc_only": (planted - leaks_doc) / planted,
            "leaked_with_form_name": leaks_name,
            "recall_with_form_name": (planted - leaks_name) / planted,
        },
    }
    (EVALS / "results.json").write_text(json.dumps({"summary": summary, "cases": results}, indent=2) + "\n",
                                        encoding="utf-8")
    (EVALS / "results.md").write_text(render_markdown(summary, results), encoding="utf-8")

    print()
    print(summary_table(summary))
    if summary["overall"]["accuracy"] < 0.8:
        print("\nOverall accuracy is below 80%. Failing fields:")
    else:
        print("\nFailing fields:")
    for r in results:
        for f in FIELDS:
            if not r["correct"][f]:
                print(f"  {r['case']} {f}: extracted={fmt(r['extracted'].get(f))} expected={fmt(r['expected'][f])}")
    if errors:
        print("\nErrors:", json.dumps(errors, indent=2))
    print("\nWrote evals/results.json and evals/results.md")


FIELD_NAMES = {
    "injury_type": "Injury type",
    "incident_date": "Incident date",
    "insurer": "Insurer",
    "policy_limit": "Policy limit",
    "claimed_damages": "Claimed damages",
    "liability_indicators": "Liability indicators",
}


def summary_table(s: dict) -> str:
    n = s["cases"]
    rows = ["| Metric | Result |", "|---|---|"]
    for f, v in s["per_field_accuracy"].items():
        rows.append(f"| {FIELD_NAMES[f]} | {v['correct']}/{n} ({pct(v['correct'], n)}) |")
    o = s["overall"]
    rows.append(f"| **Overall field accuracy** | **{o['correct']}/{o['total']} ({pct(o['correct'], o['total'])})** |")
    g = s["grounding"]
    rows.append(f"| Grounding rate (source quotes found verbatim) | {g['grounded']}/{g['checked']} ({pct(g['grounded'], g['checked'])}) |")
    p = s["pii"]
    rows.append(f"| PII leaks, document only | {p['leaked_doc_only']} of {p['planted']} planted (recall {p['recall_doc_only']:.1%}) |")
    rows.append(f"| PII leaks, with intake-form name (production path) | {p['leaked_with_form_name']} of {p['planted']} planted (recall {p['recall_with_form_name']:.1%}) |")
    return "\n".join(rows)


def render_markdown(s: dict, results: list[dict]) -> str:
    short = {"injury_type": "Injury", "incident_date": "Date", "insurer": "Insurer", "policy_limit": "Limit",
             "claimed_damages": "Damages", "liability_indicators": "Liability"}
    lines = [
        "# Extraction eval results",
        "",
        f"Run {s['run_at']} against `{s['api_url']}`, model `{s['model']}`, {s['cases']} synthetic cases "
        f"({len(FIELDS)} scored fields each). Errors: {len(s['errors'])}.",
        "",
        "## Summary",
        "",
        summary_table(s),
        "",
        "## Per case",
        "",
        "| Case | Scenario | " + " | ".join(short[f] for f in FIELDS) + " | Grounded | PII leaks (doc / with name) |",
        "|---|---|" + "|".join(":-:" for _ in FIELDS) + "|:-:|:-:|",
    ]
    for r in results:
        marks = " | ".join("✓" if r["correct"][f] else "✗" for f in FIELDS)
        g = r["grounding"]
        lines.append(
            f"| {r['case']} | {r['description']} | {marks} | {g['grounded']}/{g['checked']} | "
            f"{len(r['pii']['leaked_doc_only'])} / {len(r['pii']['leaked_with_form_name'])} |"
        )

    lines += ["", "## Failures", ""]
    fails = [(r, f) for r in results for f in FIELDS if not r["correct"][f]]
    if not fails:
        lines.append("None.")
    else:
        lines += ["| Case | Field | Extracted | Expected |", "|---|---|---|---|"]
        for r, f in fails:
            got = "(request failed)" if r["error"] else fmt(r["extracted"].get(f))
            lines.append(f"| {r['case']} | {FIELD_NAMES[f]} | {got.replace('|', '/')} | {fmt(r['expected'][f]).replace('|', '/')} |")

    lines += ["", "## Ungrounded source quotes", ""]
    ung = s["grounding"]["ungrounded_by_case"]
    lines += [f"- {c}: {', '.join(v)}" for c, v in ung.items()] if ung else ["None."]

    lines += ["", "## PII that survived redaction", ""]
    leaked = [(r["case"], r["pii"]) for r in results if r["pii"]["leaked_doc_only"] or r["pii"]["leaked_with_form_name"]]
    if leaked:
        for case, p in leaked:
            lines.append(f"- {case}: document only: {len(p['leaked_doc_only'])} "
                         f"({', '.join(kind_of(x) for x in p['leaked_doc_only']) or 'none'}); "
                         f"with form name: {len(p['leaked_with_form_name'])}")
    else:
        lines.append("None.")

    # The analysis is written by a person after reading the failures, so it lives in its own file.
    lines += ["", "## Failure analysis", ""]
    analysis = EVALS / "analysis.md"
    if analysis.exists():
        lines.append(analysis.read_text(encoding="utf-8").strip())
    else:
        lines.append("_Not written yet. Review the failures above and add evals/analysis.md._")
    return "\n".join(lines) + "\n"


def kind_of(pii: str) -> str:
    if "@" in pii:
        return "email"
    if any(c.isalpha() for c in pii):
        return "name"
    return "number"


def render_only() -> None:
    """Rebuild results.md from the saved results.json (for example after editing analysis.md)."""
    data = json.loads((EVALS / "results.json").read_text(encoding="utf-8"))
    (EVALS / "results.md").write_text(render_markdown(data["summary"], data["cases"]), encoding="utf-8")
    print(summary_table(data["summary"]))
    print("\nRebuilt evals/results.md from evals/results.json")


if __name__ == "__main__":
    render_only() if "--render-only" in sys.argv else main()
