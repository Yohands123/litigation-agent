import logging
import re
from typing import Literal, Optional

import httpx
from fastapi import (APIRouter, BackgroundTasks, Depends, File, Form, HTTPException,
                     Request, UploadFile)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import MAX_UPLOAD_MB, N8N_WEBHOOK_URL, SERVICE_TOKEN
from .db import SessionLocal, get_db
from .documents import extract_text
from .extraction import extract_case_facts
from .models import AuditLog, Case, User
from .redaction import merge_counts, redact
from .scoring import compute_score, explain_score
from .security import (create_token, current_user, require_service, verify_password,
                       write_audit)

log = logging.getLogger("lfa")
router = APIRouter()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- helpers ----------

def _get_case(db: Session, case_id: str) -> Case:
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return case


def _case_text(case: Case) -> str:
    return (
        f"{case.document_text_redacted}\n\n"
        f"--- Claimant's description (reported injury: {case.injury_type_reported}) ---\n"
        f"{case.incident_description_redacted}"
    )


def _summary(c: Case) -> dict:
    extracted_injury = ((c.extraction or {}).get("injury_type") or {}).get("value")
    return {
        "id": c.id,
        "status": c.status,
        "injury_type": extracted_injury or c.injury_type_reported,
        "risk_score": c.risk_score,
        "funding_low": c.funding_low,
        "funding_high": c.funding_high,
        "recommendation": c.recommendation,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _detail(c: Case) -> dict:
    return {
        **_summary(c),
        "claimant": {"name": c.claimant_name, "email": c.claimant_email, "phone": c.claimant_phone},
        "injury_type_reported": c.injury_type_reported,
        "incident_description_redacted": c.incident_description_redacted,
        "document_filename": c.document_filename,
        "document_text_redacted": c.document_text_redacted,
        "redaction_counts": c.redaction_counts,
        "extraction": c.extraction,
        "score_factors": c.score_factors,
        "reasoning": c.reasoning,
        "memo": c.memo,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _run_extraction(db: Session, case: Case, actor: str) -> dict:
    case.status = "processing"
    db.commit()
    try:
        extraction = extract_case_facts(_case_text(case))
    except Exception as e:
        case.status = "failed"
        write_audit(db, actor=actor, action="case.extraction_failed", case_id=case.id,
                    details={"error": str(e)[:300]})
        db.commit()
        raise HTTPException(502, "Extraction failed")
    case.extraction = extraction
    case.status = "extracted"
    write_audit(db, actor=actor, action="case.extracted", case_id=case.id,
                details={"grounding": extraction["grounding"]})
    db.commit()
    return extraction


def trigger_n8n(case_id: str) -> None:
    if not N8N_WEBHOOK_URL:
        log.warning("N8N_WEBHOOK_URL not set; case %s not sent to workflow", case_id)
        return
    try:
        r = httpx.post(N8N_WEBHOOK_URL, json={"case_id": case_id},
                       headers={"X-Service-Token": SERVICE_TOKEN}, timeout=15)
        r.raise_for_status()
    except Exception as e:
        log.exception("Failed to trigger n8n for case %s", case_id)
        with SessionLocal() as db:
            case = db.get(Case, case_id)
            if case:
                case.status = "trigger_failed"
            write_audit(db, actor="system:backend", action="case.trigger_failed",
                        case_id=case_id, details={"error": str(e)[:300]})
            db.commit()


# ---------- public ----------

@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/cases", status_code=201)
def create_case(
    request: Request,
    background: BackgroundTasks,
    claimant_name: str = Form(..., min_length=1, max_length=200),
    claimant_email: str = Form(..., max_length=255),
    claimant_phone: Optional[str] = Form(None, max_length=64),
    injury_type: str = Form(..., min_length=1, max_length=128),
    incident_description: str = Form(..., min_length=10, max_length=5000),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not EMAIL_RE.match(claimant_email):
        raise HTTPException(422, "Invalid email address")

    data = file.file.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_UPLOAD_MB} MB")
    try:
        raw_text = extract_text(file.filename, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(400, "Could not read the uploaded document")
    if not raw_text:
        raise HTTPException(422, "No text found in document (scanned PDFs are not supported yet)")

    # Redact BEFORE storing or sending anywhere. The raw file is never persisted.
    known_names = [claimant_name]
    doc = redact(raw_text, known_names)
    desc = redact(incident_description, known_names)
    del raw_text, data

    case = Case(
        claimant_name=claimant_name.strip(),
        claimant_email=claimant_email.strip(),
        claimant_phone=(claimant_phone or "").strip() or None,
        injury_type_reported=injury_type.strip(),
        incident_description_redacted=desc.text,
        document_filename=file.filename,
        document_text_redacted=doc.text,
        redaction_counts=merge_counts(doc.counts, desc.counts),
    )
    db.add(case)
    db.flush()
    write_audit(db, actor="public:portal", action="case.created", case_id=case.id,
                details={"filename": file.filename, "redactions": case.redaction_counts},
                request=request)
    db.commit()

    background.add_task(trigger_n8n, case.id)
    return {"case_id": case.id, "status": case.status}


# ---------- agent tools (called by n8n with X-Service-Token) ----------

class ExtractRequest(BaseModel):
    case_id: Optional[str] = None
    text: Optional[str] = Field(None, max_length=200_000)  # for evals: raw text, redacted here


class ScoreRequest(BaseModel):
    case_id: str


class MemoRequest(BaseModel):
    memo: str = Field(..., min_length=20, max_length=20_000)


@router.post("/extract")
def extract(body: ExtractRequest, actor: str = Depends(require_service),
            db: Session = Depends(get_db)):
    if body.case_id:
        case = _get_case(db, body.case_id)
        return {"case_id": case.id, **_run_extraction(db, case, actor)}
    if body.text:
        return extract_case_facts(redact(body.text).text)
    raise HTTPException(422, "Provide case_id or text")


@router.post("/score")
def score(body: ScoreRequest, actor: str = Depends(require_service),
          db: Session = Depends(get_db)):
    case = _get_case(db, body.case_id)
    extraction = case.extraction or _run_extraction(db, case, actor)

    result = compute_score(extraction)
    result["reasoning"] = explain_score(result)

    case.risk_score = result["risk_score"]
    case.funding_low = result["funding_range"]["low"]
    case.funding_high = result["funding_range"]["high"]
    case.recommendation = result["recommendation"]
    case.score_factors = result["factors"]
    case.reasoning = result["reasoning"]
    case.status = "scored"
    write_audit(db, actor=actor, action="case.scored", case_id=case.id,
                details={"risk_score": case.risk_score, "recommendation": case.recommendation})
    db.commit()
    return {"case_id": case.id, **result}


@router.post("/cases/{case_id}/memo")
def save_memo(case_id: str, body: MemoRequest, actor: str = Depends(require_service),
              db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    case.memo = body.memo
    case.status = "ready_for_review"
    write_audit(db, actor=actor, action="case.memo_saved", case_id=case.id,
                details={"memo_chars": len(body.memo)})
    db.commit()
    # Safe to post to Slack: no claimant PII in this payload.
    return {
        "case_id": case.id,
        "injury_type": _summary(case)["injury_type"],
        "risk_score": case.risk_score,
        "funding_low": case.funding_low,
        "funding_high": case.funding_high,
        "recommendation": case.recommendation,
        "status": case.status,
    }


# ---------- auth ----------

class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    ok = verify_password(body.password, user.password_hash if user else None)
    if not user or not ok:
        write_audit(db, actor="anonymous", action="auth.login_failed",
                    details={"email": body.email[:255]}, request=request)
        db.commit()
        raise HTTPException(401, "Invalid email or password")
    write_audit(db, actor=f"attorney:{user.email}", action="auth.login", request=request)
    db.commit()
    return {"access_token": create_token(user), "token_type": "bearer",
            "user": {"email": user.email, "role": user.role}}


# ---------- attorney dashboard (JWT) ----------

class StatusUpdate(BaseModel):
    status: Literal["approved", "declined", "needs_info", "ready_for_review"]
    note: Optional[str] = Field(None, max_length=1000)


@router.get("/cases")
def list_cases(request: Request, user: User = Depends(current_user),
               db: Session = Depends(get_db)):
    cases = db.scalars(select(Case).order_by(Case.created_at.desc()).limit(200)).all()
    write_audit(db, actor=f"attorney:{user.email}", action="case.list_viewed",
                details={"count": len(cases)}, request=request)
    db.commit()
    return [_summary(c) for c in cases]


@router.get("/cases/{case_id}")
def get_case(case_id: str, request: Request, user: User = Depends(current_user),
             db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    write_audit(db, actor=f"attorney:{user.email}", action="case.viewed",
                case_id=case.id, request=request)
    db.commit()
    return _detail(case)


@router.patch("/cases/{case_id}")
def update_case(case_id: str, body: StatusUpdate, request: Request,
                user: User = Depends(current_user), db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    old = case.status
    case.status = body.status
    write_audit(db, actor=f"attorney:{user.email}", action="case.status_changed",
                case_id=case.id, details={"from": old, "to": body.status, "note": body.note},
                request=request)
    db.commit()
    return _summary(case)


@router.get("/cases/{case_id}/audit")
def case_audit(case_id: str, user: User = Depends(current_user),
               db: Session = Depends(get_db)):
    _get_case(db, case_id)
    rows = db.scalars(select(AuditLog).where(AuditLog.case_id == case_id)
                      .order_by(AuditLog.created_at.asc())).all()
    return [{"actor": r.actor, "action": r.action, "details": r.details,
             "at": r.created_at.isoformat()} for r in rows]
