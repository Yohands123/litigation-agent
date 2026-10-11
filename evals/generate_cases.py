"""Deterministic generator for 15 synthetic, labeled personal-injury cases.

No LLM is involved. Every label is known by construction from the template values,
so the ground truth in labels.json is exact. Run from the repo root:

    python evals/generate_cases.py
"""
from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

SEED = 20261011
OUT = Path(__file__).resolve().parent / "cases"

FIRST = ["Priya", "Daniel", "Amara", "Lucas", "Mei", "Tomasz", "Fatima", "Jordan", "Aisha", "Mateo",
         "Hannah", "Kwame", "Sofia", "Ravi", "Elena", "Noah", "Leila", "Owen", "Yuki", "Marcus"]
LAST = ["Raman", "Osei", "Nwosu", "Tremblay", "Chen", "Kowalski", "Haddad", "Brooks", "Siddiqui", "Alvarez",
        "Fischer", "Mensah", "Rossi", "Patel", "Petrova", "Gagnon", "Karimi", "Doyle", "Tanaka", "Reid"]
OFFICERS = ["Okafor", "Lindqvist", "Moreau", "Baptiste", "Singh", "Walsh"]
STREETS = [("King St N", "University Ave W"), ("Weber St", "Victoria St"), ("Bay St", "Dundas St W"),
           ("Main St", "Elm Ave"), ("Queen St E", "Parliament St"), ("Fischer-Hallman Rd", "Ottawa St S")]

INJURIES = {
    "whiplash": {
        "diagnosis": "Whiplash-associated disorder (WAD II), cervical strain",
        "keywords": ["whiplash", "cervical", "neck"],
    },
    "fracture_wrist": {
        "diagnosis": "Fractured left wrist (distal radius fracture)",
        "keywords": ["fractur", "broken", "wrist", "radius"],
    },
    "fracture_tibia": {
        "diagnosis": "Closed fracture of the right tibia",
        "keywords": ["fractur", "broken", "tibia", "leg"],
    },
    "fracture_clavicle": {
        "diagnosis": "Displaced fracture of the left clavicle",
        "keywords": ["fractur", "broken", "clavicle", "collarbone"],
    },
    "concussion": {
        "diagnosis": "Concussion (mild traumatic brain injury) with post-concussive headaches",
        "keywords": ["concussion", "traumatic brain injury", "tbi", "brain"],
    },
    "tbi": {
        "diagnosis": "Moderate traumatic brain injury with loss of consciousness",
        "keywords": ["traumatic brain injury", "tbi", "brain", "concussion"],
    },
    "sprain_lumbar": {
        "diagnosis": "Grade II lumbar sprain (soft-tissue injury)",
        "keywords": ["sprain", "soft tissue", "soft-tissue", "lumbar", "back"],
    },
    "sprain_ankle": {
        "diagnosis": "Grade II sprain of the right ankle (soft-tissue injury)",
        "keywords": ["sprain", "soft tissue", "soft-tissue", "ankle"],
    },
    "herniated_disc": {
        "diagnosis": "L4-L5 disc herniation with radiculopathy",
        "keywords": ["herniat", "disc", "disk"],
    },
}

# Liability scenarios. Concepts may list alternatives with "|"; each concept must match somewhere
# in the joined extracted liability values. {d1} is the claimant's vehicle, {d2} the other party.
LIABILITY = {
    "rear_end": {
        "text": "Vehicle 1 was stopped at a red light when Vehicle 2 struck it from behind. "
                "Driver 2 told the attending officer he looked down at his phone and did not see traffic stop.",
        "concepts": ["rear|from behind|struck it from behind"],
        "direction": "favorable",
    },
    "red_light": {
        "text": "Vehicle 2 entered the intersection against a red signal and struck Vehicle 1 on the driver side. "
                "An independent witness confirmed Vehicle 2 ran the red light. Driver 2 was cited for failing to stop at a red light.",
        "concepts": ["red light|red signal", "cited|charged|ticket"],
        "direction": "favorable",
    },
    "dui": {
        "text": "Vehicle 2 crossed the centre line and collided head-on with Vehicle 1. Driver 2 failed a roadside "
                "breath test and was charged with impaired driving.",
        "concepts": ["impaired|dui|alcohol|breath|intoxicat"],
        "direction": "favorable",
    },
    "speeding": {
        "text": "Vehicle 2 was travelling at an estimated 92 km/h in a 50 km/h zone and lost control, striking Vehicle 1 "
                "in the oncoming lane. Driver 2 was cited for speeding.",
        "concepts": ["speed", "cited|charged|ticket"],
        "direction": "favorable",
    },
    "claimant_cited": {
        "text": "Vehicle 1 changed lanes without signalling and moved into the path of Vehicle 2. "
                "Driver 1 was cited for an unsafe lane change. Driver 2 was not charged.",
        "concepts": ["lane change|changed lanes", "cited|charged|ticket"],
        "direction": "unfavorable",
    },
    "conflicting": {
        "text": "Witness accounts conflict. Witness 1 stated that Vehicle 1 entered the intersection on a stale amber light. "
                "Witness 2 stated that Vehicle 2 ran the red light. No charges were laid pending further investigation.",
        "concepts": ["witness|conflict|disputed|unclear"],
        "direction": "mixed",
    },
    "no_seatbelt": {
        "text": "Vehicle 2 failed to stop at a stop sign and struck Vehicle 1 on the passenger side. "
                "Driver 1 was not wearing a seatbelt at the time of the collision.",
        "concepts": ["stop sign", "seatbelt|seat belt"],
        "direction": "mixed",
    },
    "claimant_following": {
        "text": "Vehicle 1 struck the rear of Vehicle 2 when Vehicle 2 braked for a pedestrian. "
                "Driver 1 was cited for following too closely and was not wearing a seatbelt.",
        "concepts": ["following too closely|follow", "seatbelt|seat belt"],
        "direction": "unfavorable",
    },
    "slip_wet_floor": {
        "text": "The claimant slipped on an unmarked wet floor in aisle 7. No warning signs were posted. "
                "The store's incident log shows the spill was reported 40 minutes earlier and had not been cleaned.",
        "concepts": ["wet|spill", "sign|warning|not been cleaned|not cleaned"],
        "direction": "favorable",
    },
    "slip_icy_steps": {
        "text": "The claimant fell on the building's front steps, which were covered in ice. The property manager "
                "confirmed the steps had not been salted or cleared that morning despite a freezing rain warning.",
        "concepts": ["ice|icy", "salt|cleared|not been salted"],
        "direction": "favorable",
    },
    "none": {"text": "", "concepts": [], "direction": "mixed"},
}

ITEMS = [
    ("Emergency department visit", 2400), ("Ambulance transport", 850), ("CT scan", 1350), ("MRI (lumbar spine)", 2100),
    ("X-ray series", 420), ("Orthopedic consultation", 650), ("Orthopedic surgery (ORIF)", 18750),
    ("Physiotherapy (12 sessions)", 1850), ("Physiotherapy (20 sessions)", 3100), ("Neurology follow-up", 780),
    ("Prescription medication", 265), ("Chiropractic care (8 sessions)", 960), ("Cervical collar and brace", 180),
    ("Occupational therapy assessment", 540), ("Pain management injections", 2250),
]

# One spec per case. Fields not listed default to the structured, easy form.
SPECS = [
    dict(injury="whiplash", liability="rear_end", insurance=("Northgate Mutual Insurance", 1_000_000), damages="total",
         date=date(2026, 3, 14), date_fmt="iso", id_kind="sin", layout="police+medical"),
    dict(injury="fracture_wrist", liability="red_light", insurance=("Maple Shield Insurance", 2_000_000), damages="total",
         date=date(2026, 1, 22), date_fmt="long", id_kind="sin", layout="police+medical"),
    dict(injury="concussion", liability="dui", insurance=("Lakeshore General Insurance", None), damages="itemized",
         date=date(2025, 11, 28), date_fmt="dmy", id_kind="sin", layout="police+medical"),
    dict(injury="herniated_disc", liability="claimant_cited", insurance=("Tri-County Casualty", 500_000), damages="total",
         date=date(2026, 5, 19), date_fmt="iso", id_kind="sin", layout="police+medical"),
    dict(injury="sprain_lumbar", liability="conflicting", insurance=None, damages="itemized",
         date=date(2026, 2, 17), date_fmt="long", id_kind="sin", layout="police+medical"),
    dict(injury="whiplash", liability="no_seatbelt", insurance=("Empire State Auto Insurance", 250_000), damages=None,
         date=date(2026, 4, 30), date_fmt="iso", id_kind="ssn", layout="police"),
    dict(injury="fracture_tibia", liability="speeding", insurance=("Great Lakes Indemnity", None), damages="total",
         date=date(2025, 9, 13), date_fmt="dmy", id_kind="sin", layout="police+medical"),
    # Narrative-only case 1: date, insurer, policy limit and damages appear only in prose.
    dict(injury="tbi", liability="red_light", insurance=("Ridgeline Insurance Group", 1_000_000), damages="prose",
         date=date(2026, 6, 3), date_fmt="prose", id_kind="sin", layout="letter"),
    dict(injury="sprain_ankle", liability="slip_wet_floor", insurance=("Harbourfront Commercial Insurance", 2_000_000),
         damages="itemized", date=date(2026, 7, 8), date_fmt="iso", id_kind="ssn", layout="premises+medical"),
    # Older than two years: outside a typical limitation period.
    dict(injury="herniated_disc", liability="rear_end", insurance=None, damages="total",
         date=date(2023, 8, 19), date_fmt="long", id_kind="sin", layout="police+medical"),
    # Medical bill only: no liability or insurance information at all.
    dict(injury="whiplash", liability="none", insurance=None, damages="total",
         date=date(2026, 2, 9), date_fmt="iso", id_kind="sin", layout="medical"),
    # Hard PII: claimant named in unlabeled narrative prose.
    dict(injury="concussion", liability="conflicting", insurance=("Prairie Mutual", None), damages=None,
         date=date(2026, 3, 27), date_fmt="dmy", id_kind="sin", layout="police", name_in_prose=True),
    # Narrative-only case 2: date and liability appear only in prose.
    dict(injury="fracture_clavicle", liability="dui", insurance=("Northgate Mutual Insurance", 1_000_000),
         damages="itemized", date=date(2025, 12, 31), date_fmt="prose", id_kind="sin", layout="statement+medical"),
    dict(injury="sprain_ankle", liability="claimant_following", insurance=("Coastal Shield Insurance", 300_000),
         damages="total", date=date(2026, 8, 2), date_fmt="iso", id_kind="ssn", layout="police+medical"),
    dict(injury="herniated_disc", liability="slip_icy_steps", insurance=("Summit Property & Casualty", None),
         damages="itemized", date=date(2026, 1, 16), date_fmt="dmy", id_kind="sin", layout="premises+medical",
         name_in_prose=True),
]


def fmt_date(d: date, kind: str) -> str:
    if kind == "iso":
        return d.isoformat()
    if kind == "dmy":
        return d.strftime("%d/%m/%Y")
    return f"{d.strftime('%B')} {d.day}, {d.year}"  # "long" and "prose"


def money(n: int) -> str:
    return f"${n:,.2f}"


class Person:
    def __init__(self, rng: random.Random, idx: int, id_kind: str):
        self.first = rng.choice(FIRST)
        self.last = rng.choice(LAST)
        self.name = f"{self.first} {self.last}"
        area = rng.choice(["519", "416", "647", "905"])
        line = f"{rng.randint(100, 199):04d}"
        self.phone = rng.choice([f"({area}) 555-{line}", f"{area}-555-{line}", f"+1 {area}.555.{line}"])
        self.email = f"{self.first.lower()}.{self.last.lower()}{idx:02d}@example.com"
        if id_kind == "ssn":
            self.gov_id = f"{rng.randint(100, 665):03d}-{rng.randint(10, 99):02d}-{rng.randint(1000, 9999):04d}"
            self.gov_label = "SSN"
        else:
            self.gov_id = f"{rng.randint(100, 899):03d} {rng.randint(100, 999):03d} {rng.randint(100, 999):03d}"
            self.gov_label = "SIN"
        self.dob = f"{rng.randint(1965, 2002)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"


def build_case(i: int, spec: dict, rng: random.Random) -> tuple[str, dict]:
    p = Person(rng, i, spec["id_kind"])
    other = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    officer = rng.choice(OFFICERS)
    street_a, street_b = rng.choice(STREETS)
    injury = INJURIES[spec["injury"]]
    liab = LIABILITY[spec["liability"]]
    d = spec["date"]
    ins = spec["insurance"]
    layout = spec["layout"]

    # Damages
    damages_label: int | None
    damages_lines: list[str] = []
    damages_prose = ""
    if spec["damages"] in ("total", "itemized", "prose"):
        items = rng.sample(ITEMS, k=rng.randint(3, 4))
        damages_label = sum(a for _, a in items)
        if spec["damages"] == "prose":
            damages_prose = (f"Medical expenses incurred to date come to {money(damages_label)}, "
                             f"according to the treating clinic's records.")
        else:
            damages_lines = [f"{name}: {money(amount)}" for name, amount in items]
            if spec["damages"] == "total":
                damages_lines.append(f"Total amount billed: {money(damages_label)}")
    else:
        items = []
        damages_label = None

    insurer, limit = (ins if ins else (None, None))
    date_text = fmt_date(d, spec["date_fmt"])
    sections: list[str] = []

    if layout.startswith("police"):
        lines = [
            "MOTOR VEHICLE COLLISION REPORT (SYNTHETIC)",
            f"Report No: MVC-{d.year}-{rng.randint(1000, 9999):04d}",
            f"Date of Collision: {date_text}",
            f"Location: {street_a} and {street_b}",
            "",
            f"Driver 1: {p.name}",
            f"DOB: {p.dob}",
            f"Phone: {p.phone}",
            f"Email: {p.email}",
            f"{p.gov_label}: {p.gov_id}",
            "",
            f"Driver 2: {other}",
        ]
        if insurer and limit:
            lines.append(f"Insurer (Driver 2): {insurer}, policy limit ${limit:,}")
        elif insurer:
            lines.append(f"Insurer (Driver 2): {insurer}")
        narrative = liab["text"]
        if spec.get("name_in_prose"):
            narrative += f" {p.name} was transported to hospital by ambulance and later gave a statement at the scene."
        lines += ["", f"Narrative: {narrative}", f"Officer {officer} attended the scene."]
        if spec["injury"] and layout == "police":
            lines.append(f"Injuries reported at scene: {injury['diagnosis']}.")
        sections.append("\n".join(lines))

    if layout.startswith("premises"):
        lines = [
            "PREMISES INCIDENT REPORT (SYNTHETIC)",
            f"Incident date: {date_text}",
            f"Claimant: {p.name}",
            f"Phone: {p.phone}",
            f"Email: {p.email}",
            f"{p.gov_label}: {p.gov_id}",
        ]
        if insurer and limit:
            lines.append(f"Property owner's liability insurer: {insurer}, policy limit ${limit:,}")
        elif insurer:
            lines.append(f"Property owner's liability insurer: {insurer}")
        narrative = liab["text"]
        if spec.get("name_in_prose"):
            narrative += f" A neighbour helped {p.name} inside and called for an ambulance."
        lines += ["", f"Description: {narrative}"]
        sections.append("\n".join(lines))

    if layout == "letter":
        sections.append("\n".join([
            "LETTER OF REPRESENTATION (SYNTHETIC)",
            "Re: Personal injury claim",
            "",
            f"Driver 1: {p.name}",
            f"Phone: {p.phone}",
            f"Email: {p.email}",
            f"{p.gov_label}: {p.gov_id}",
            "",
            f"On the evening of {date_text}, our client was driving east on {street_a} when the collision occurred. "
            f"{liab['text']} Our client was diagnosed with a {injury['diagnosis'].lower()} and spent four days in hospital. "
            f"The other driver's carrier, {insurer}, has confirmed a liability limit of ${limit:,} on the policy. "
            f"{damages_prose}",
        ]))

    if layout.startswith("statement"):
        sections.append("\n".join([
            "CLAIMANT STATEMENT (SYNTHETIC)",
            f"Driver 1: {p.name}",
            f"Phone: {p.phone}",
            f"Email: {p.email}",
            f"{p.gov_label}: {p.gov_id}",
            "",
            f"I was driving home on New Year's Eve, {date_text}, along {street_a}. {liab['text']} "
            f"Officer {officer} took my statement at the hospital. "
            f"The other driver is insured with {insurer}, policy limit ${limit:,}.",
        ]))

    if layout.endswith("medical") or layout == "medical":
        lines = [
            "HOSPITAL ITEMIZED STATEMENT (SYNTHETIC)",
            f"Patient: {p.name}",
        ]
        if layout == "medical":
            lines += [f"Phone: {p.phone}", f"Email: {p.email}", f"{p.gov_label}: {p.gov_id}",
                      f"Date of injury: {date_text}"]
        lines.append(f"Diagnosis: {injury['diagnosis']}")
        lines += damages_lines
        sections.append("\n".join(lines))
    elif damages_lines:
        sections.append("\n".join(["BILLING SUMMARY (SYNTHETIC)", *damages_lines]))

    text = "\n\n---\n".join(sections) + "\n"

    label = {
        "case": f"case_{i:02d}",
        "description": f"{spec['injury']} / {spec['liability']} / insurance={'none' if not ins else ('full' if limit else 'insurer only')}"
                       f" / damages={spec['damages']} / date={spec['date_fmt']} / layout={layout}"
                       + (" / name in prose" if spec.get("name_in_prose") else ""),
        "injury_type_keywords": injury["keywords"],
        "incident_date": d.isoformat(),
        "insurer": insurer,
        "policy_limit": limit,
        "claimed_damages": damages_label,
        "liability_concepts": liab["concepts"],
        "liability_direction": liab["direction"],
        "planted_pii": [p.name, p.phone, p.email, p.gov_id],
        "claimant_name": p.name,
    }
    return text, label


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    labels = {}
    for i, spec in enumerate(SPECS, start=1):
        text, label = build_case(i, spec, rng)
        (OUT / f"case_{i:02d}.txt").write_text(text, encoding="utf-8", newline="\n")
        labels[label["case"]] = label
    (OUT / "labels.json").write_text(json.dumps(labels, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {len(labels)} cases and labels.json to {OUT}")


if __name__ == "__main__":
    main()
