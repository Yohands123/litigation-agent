"""Deterministic rules decide the score and funding range. The LLM only explains them.

risk_score: 0 (very safe) to 100 (very risky).
"""
from datetime import date

from .config import LIMITATION_YEARS
from .llm import chat_text

FAVORABLE = (
    "cited", "citation", "ticket", "red light", "ran a red", "ran the red", "rear-end",
    "rear end", "impaired", "dui", "dwi", "intoxicat", "admitted fault",
    "admitted responsibility", "failed to yield", "failure to yield", "speeding",
    "distracted", "texting", "on phone", "on his phone", "on her phone", "wrong way",
    "stop sign", "at fault",
)
# Checked first, so "claimant was cited" is never counted as favorable.
UNFAVORABLE = (
    "plaintiff was cited", "claimant was cited", "plaintiff cited", "claimant cited",
    "not wearing", "no seatbelt", "without a seatbelt", "disputed", "dispute",
    "conflicting", "contradict", "comparative", "jaywalk", "pre-existing", "preexisting",
    "no witnesses", "plaintiff admitted", "claimant admitted", "unclear who", "both drivers",
    "claimant at fault", "plaintiff at fault",
)
SEVERITY = (
    (("brain", "tbi", "spinal", "paralys", "amputat"), 3.0, "severe"),
    (("fracture", "broken", "surgery", "torn", "herniat", "disc"), 2.0, "moderate"),
    (("whiplash", "sprain", "strain", "soft tissue", "bruis", "contusion"), 1.2, "minor"),
)


def _severity(injury: str | None) -> tuple[float, str]:
    text = (injury or "").lower()
    for keywords, mult, label in SEVERITY:
        if any(k in text for k in keywords):
            return mult, label
    return 1.5, "unclassified"


def _round_down_500(x: float) -> int:
    return int(max(x, 0) // 500 * 500)


def compute_score(extraction: dict, today: date | None = None) -> dict:
    today = today or date.today()
    factors: list[dict] = []
    risk = 50

    def add(factor: str, impact: int, evidence: str | None = None):
        nonlocal risk
        risk += impact
        factors.append({"factor": factor, "impact": impact, "evidence": evidence})

    # Liability
    indicators = extraction.get("liability_indicators") or []
    fav_total, unfav_total = 0, 0
    for item in indicators:
        text = str(item.get("value") or "").lower()
        if any(k in text for k in UNFAVORABLE):
            if unfav_total < 30:
                step = min(10, 30 - unfav_total)
                unfav_total += step
                add(f"Liability concern: {item.get('value')}", step, item.get("source_text"))
        elif any(k in text for k in FAVORABLE):
            if fav_total < 25:
                step = min(8, 25 - fav_total)
                fav_total += step
                add(f"Favorable liability: {item.get('value')}", -step, item.get("source_text"))
    if not indicators:
        add("No liability evidence found in documents", 15)

    # Insurance
    ins_field = extraction.get("insurance_coverage") or {}
    ins = ins_field.get("value") or {}
    policy_limit = ins.get("policy_limit") if isinstance(ins, dict) else None
    insurer = ins.get("insurer") if isinstance(ins, dict) else None
    if policy_limit:
        add(f"Identified coverage with ${policy_limit:,.0f} policy limit", -10, ins_field.get("source_text"))
    elif insurer:
        add(f"Insurer identified ({insurer}) but no policy limit", -3, ins_field.get("source_text"))
    else:
        add("No identifiable insurance coverage", 15)

    # Damages
    dmg_field = extraction.get("claimed_damages") or {}
    damages = dmg_field.get("value")
    if not damages:
        add("No documented damages amount", 15)
    elif dmg_field.get("grounded"):
        add(f"Damages of ${damages:,.0f} supported by documents", -5, dmg_field.get("source_text"))
    if damages and policy_limit and damages > policy_limit:
        add("Claimed damages exceed policy limit; recovery may be capped", 5)

    # Limitation period
    date_field = extraction.get("incident_date") or {}
    incident = None
    try:
        incident = date.fromisoformat(str(date_field.get("value")))
    except (TypeError, ValueError):
        pass
    if incident is None:
        add("Incident date unknown; limitation period cannot be verified", 10)
    else:
        try:
            deadline = incident.replace(year=incident.year + LIMITATION_YEARS)
        except ValueError:  # Feb 29
            deadline = incident.replace(year=incident.year + LIMITATION_YEARS, day=28)
        days_left = (deadline - today).days
        if days_left < 0:
            add(f"Claim may be time-barred ({LIMITATION_YEARS}-year limitation period passed)", 40, date_field.get("source_text"))
        elif days_left < 90:
            add(f"Limitation period expires in {days_left} days", 10, date_field.get("source_text"))

    # Severity
    sev_mult, sev_label = _severity((extraction.get("injury_type") or {}).get("value"))
    if sev_label == "severe":
        add("Severe injury supports higher case value", -5)
    elif sev_label == "minor":
        add("Minor injury limits case value", 5)

    # Extraction quality
    ungrounded = (extraction.get("grounding") or {}).get("ungrounded_fields") or []
    if ungrounded:
        add(f"{len(ungrounded)} extracted value(s) not found verbatim in documents", 5 * len(ungrounded))

    risk = max(0, min(100, risk))

    # Funding range: a fraction of risk-adjusted expected recovery.
    expected = (damages or 0) * sev_mult
    if policy_limit:
        expected = min(expected, policy_limit)
    expected *= (1 - risk / 100)

    if risk >= 70:
        recommendation, low, high = "decline", 0, 0
    else:
        recommendation = "fund" if risk < 40 else "review"
        low, high = _round_down_500(expected * 0.10), _round_down_500(expected * 0.20)

    return {
        "risk_score": risk,
        "funding_range": {"low": low, "high": high},
        "recommendation": recommendation,
        "severity": sev_label,
        "factors": factors,
    }


EXPLAIN_PROMPT = """You are writing the reasoning section for a litigation funding underwriter.
You are given a risk score, funding range, and the exact rule-based factors that produced them.
Write 3-5 plain sentences explaining the result. Use ONLY the factors provided.
Do not change, recompute, or invent any numbers. Do not add legal advice."""


def explain_score(score: dict) -> str:
    lines = [f"- {f['factor']} (risk impact {f['impact']:+d})" for f in score["factors"]]
    user = (
        f"Risk score: {score['risk_score']}/100\n"
        f"Funding range: ${score['funding_range']['low']:,} - ${score['funding_range']['high']:,}\n"
        f"Recommendation: {score['recommendation']}\n"
        f"Factors:\n" + "\n".join(lines)
    )
    try:
        return chat_text(EXPLAIN_PROMPT, user)
    except Exception:
        return "Score determined by rules: " + "; ".join(f["factor"] for f in score["factors"]) + "."
