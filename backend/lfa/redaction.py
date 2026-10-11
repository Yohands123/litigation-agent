"""Regex-based PII redaction, applied before any text reaches the LLM.

Limitations (documented honestly): regex cannot catch every name. We combine
(1) names the claimant typed into the form, (2) names after labels like
"Driver:" or "Patient:", and (3) names after titles like "Mr." or "Officer".
"""
import re
from dataclasses import dataclass, field

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4}(?!\d)")
SIN = re.compile(r"(?<!\d)\d{3}[ -]\d{3}[ -]\d{3}(?!\d)")
DOB = re.compile(
    r"(?i)\b(DOB|D\.O\.B\.|date of birth)(\s*[:\-]?\s*)"
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|[A-Z][a-z]+\.? \d{1,2},? \d{4})"
)
TITLE_NAME = re.compile(
    r"\b(Mr|Mrs|Ms|Miss|Dr|Officer|Ofc|Sgt|Det|Constable)(\.?\s+)"
    r"([A-Z][a-z'\-]+(?:[ \t]+[A-Z][a-z'\-]+)?)"
)
LABEL_NAME = re.compile(
    r"(?im)^(\s*(?:full[ \t]+)?(?:name|patient(?:[ \t]+name)?|claimant|plaintiff|"
    r"driver(?:[ \t]*\d)?|insured|witness(?:[ \t]*\d)?|owner|passenger|policyholder)"
    r"[ \t]*:[ \t]*)([A-Z][A-Za-z'\-]+(?:[ \t]+[A-Z][A-Za-z'\-\.]+){0,3})"
)


@dataclass
class RedactionResult:
    text: str
    counts: dict = field(default_factory=dict)


def redact(text: str, known_names: list[str] | None = None) -> RedactionResult:
    counts: dict[str, int] = {}

    def apply(pattern: re.Pattern, repl, s: str, key: str) -> str:
        new, n = pattern.subn(repl, s)
        if n:
            counts[key] = counts.get(key, 0) + n
        return new

    out = text or ""

    # 1. Structured identifiers first (emails often contain names).
    #    Order matters: SSN and phone before SIN.
    out = apply(EMAIL, "[EMAIL]", out, "email")
    out = apply(SSN, "[SSN]", out, "ssn")
    out = apply(PHONE, "[PHONE]", out, "phone")
    out = apply(SIN, "[SIN]", out, "sin")
    out = apply(DOB, lambda m: f"{m.group(1)}{m.group(2)}[DOB]", out, "dob")

    # 2. Names the claimant gave us: full name first, then each part.
    for name in known_names or []:
        name = name.strip()
        if not name:
            continue
        parts = [p for p in re.split(r"\s+", name) if len(p) >= 2]
        for candidate in sorted({name, *parts}, key=len, reverse=True):
            pattern = re.compile(rf"\b{re.escape(candidate)}\b", re.IGNORECASE)
            out = apply(pattern, "[NAME]", out, "name")

    # 3. Labelled and titled names.
    out = apply(LABEL_NAME, lambda m: f"{m.group(1)}[NAME]", out, "name")
    out = apply(TITLE_NAME, lambda m: f"{m.group(1)}{m.group(2)}[NAME]", out, "name")


    return RedactionResult(text=out, counts=counts)


def merge_counts(*counts: dict) -> dict:
    merged: dict[str, int] = {}
    for c in counts:
        for k, v in c.items():
            merged[k] = merged.get(k, 0) + v
    return merged
