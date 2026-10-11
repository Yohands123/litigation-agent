"""LLM extraction of case facts, each with verbatim source text, plus a grounding check."""
import re
from datetime import date

from .config import OPENAI_MODEL
from .llm import chat_json

MAX_DOC_CHARS = 30_000

SYSTEM_PROMPT = """You extract facts from personal-injury case documents for a litigation funding underwriter.
Personal information has already been replaced with tags like [NAME], [PHONE], [EMAIL]. Never try to reconstruct it.

Return ONLY a JSON object with exactly these keys:
  injury_type, incident_date, liability_indicators, insurance_coverage, claimed_damages

Shapes:
  injury_type:          {"value": string|null, "source_text": string|null}
  incident_date:        {"value": "YYYY-MM-DD"|null, "source_text": string|null}
  liability_indicators: [{"value": string, "source_text": string}, ...]
  insurance_coverage:   {"value": {"insurer": string|null, "policy_limit": number|null}|null, "source_text": string|null}
  claimed_damages:      {"value": number|null, "source_text": string|null}

Rules:
- source_text MUST be copied verbatim from the document: an exact substring, at most about 200 characters. Never paraphrase it.
- If the document does not state a fact, use null for value and source_text. Never guess.
- injury_type: short lowercase label, e.g. "whiplash", "fractured wrist", "traumatic brain injury".
- liability_indicators: facts bearing on who was at fault, written as short phrases, e.g.
  "other driver cited for running red light", "claimant not wearing seatbelt". Empty list if none.
- insurance_coverage: the at-fault party's liability coverage.
- claimed_damages: total dollars claimed as a plain number. If only itemized amounts are given, sum them,
  and use the line with the total (or the largest item) as source_text.
"""

_QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                         "\u2013": "-", "\u2014": "-"})


def _norm(s: str) -> str:
    s = s.translate(_QUOTES).lower()
    return re.sub(r"\s+", " ", s).strip()


def is_grounded(source: str | None, doc_norm: str) -> bool | None:
    """True if every piece of the quoted source text appears in the document."""
    if not source:
        return None
    pieces = re.split(r"\.\.\.|\u2026", source)
    pieces = [_norm(p).strip(" .,;:\"'") for p in pieces]
    pieces = [p for p in pieces if p]
    return bool(pieces) and all(p in doc_norm for p in pieces)


def _to_number(v):
    if v is None or isinstance(v, (int, float)):
        return v
    try:
        return float(re.sub(r"[^\d.]", "", str(v)))
    except ValueError:
        return None


def _field(raw) -> dict:
    if isinstance(raw, dict):
        return {"value": raw.get("value"), "source_text": raw.get("source_text")}
    return {"value": raw, "source_text": None}


def extract_case_facts(text: str) -> dict:
    doc = (text or "")[:MAX_DOC_CHARS]
    raw = chat_json(SYSTEM_PROMPT, f"DOCUMENT:\n\"\"\"\n{doc}\n\"\"\"")
    doc_norm = _norm(doc)

    result: dict = {}
    for key in ("injury_type", "incident_date", "insurance_coverage", "claimed_damages"):
        result[key] = _field(raw.get(key))

    # Normalise types.
    result["claimed_damages"]["value"] = _to_number(result["claimed_damages"]["value"])
    ins = result["insurance_coverage"]["value"]
    if isinstance(ins, dict):
        ins["policy_limit"] = _to_number(ins.get("policy_limit"))
    d = result["incident_date"]["value"]
    if d:
        try:
            date.fromisoformat(str(d))
        except ValueError:
            result["incident_date"]["value_invalid"] = True

    li_raw = raw.get("liability_indicators") or []
    if isinstance(li_raw, dict):  # tolerate {"value": [...]}
        li_raw = li_raw.get("value") or []
    result["liability_indicators"] = [_field(i) for i in li_raw if i]

    # Grounding check: every source_text must literally appear in the document.
    checked, ungrounded = 0, []
    for key in ("injury_type", "incident_date", "insurance_coverage", "claimed_damages"):
        g = is_grounded(result[key]["source_text"], doc_norm)
        result[key]["grounded"] = g
        if g is not None:
            checked += 1
            if not g:
                ungrounded.append(key)
    for i, item in enumerate(result["liability_indicators"]):
        g = is_grounded(item["source_text"], doc_norm)
        item["grounded"] = g
        if g is not None:
            checked += 1
            if not g:
                ungrounded.append(f"liability_indicators[{i}]")

    result["grounding"] = {
        "checked": checked,
        "grounded": checked - len(ungrounded),
        "ungrounded_fields": ungrounded,
    }
    result["model"] = OPENAI_MODEL
    return result
