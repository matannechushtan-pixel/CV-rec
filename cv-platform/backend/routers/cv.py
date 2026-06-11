import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from core.auth import require_job_seeker
from core.database import get_db
from core.supabase_client import upload_cv_pdf
from models.cv import CV
from models.user import Profile
from agents import cv_agent, match_agent
from services.cv_parser import extract_text
from services.latex_builder import build_latex_cv, render_cv_pdf

router = APIRouter()

_FONTS_PATH = Path(__file__).parent.parent / "data" / "cv_fonts.json"
_FONTS: list[dict] = json.loads(_FONTS_PATH.read_text())

_PROFESSION_TEMPLATES: list[dict] = [
    {
        "id": "software_engineer",
        "label": "Software Engineer",
        "fields": [
            {"name": "full_name", "label": "Full name", "type": "text"},
            {"name": "email", "label": "Email", "type": "text"},
            {"name": "phone", "label": "Phone", "type": "text"},
            {"name": "years_experience", "label": "Years of experience", "type": "text"},
            {"name": "languages_frameworks", "label": "Languages & frameworks", "type": "text"},
            {"name": "key_projects", "label": "Key projects / achievements", "type": "textarea"},
            {"name": "education", "label": "Education", "type": "text"},
        ],
    },
    {
        "id": "marketing",
        "label": "Marketing Professional",
        "fields": [
            {"name": "full_name", "label": "Full name", "type": "text"},
            {"name": "email", "label": "Email", "type": "text"},
            {"name": "phone", "label": "Phone", "type": "text"},
            {"name": "years_experience", "label": "Years of experience", "type": "text"},
            {"name": "channels_tools", "label": "Channels & tools (SEO, paid social, HubSpot...)", "type": "text"},
            {"name": "campaigns", "label": "Notable campaigns / results", "type": "textarea"},
            {"name": "education", "label": "Education", "type": "text"},
        ],
    },
    {
        "id": "finance",
        "label": "Finance / Accounting",
        "fields": [
            {"name": "full_name", "label": "Full name", "type": "text"},
            {"name": "email", "label": "Email", "type": "text"},
            {"name": "phone", "label": "Phone", "type": "text"},
            {"name": "years_experience", "label": "Years of experience", "type": "text"},
            {"name": "certifications", "label": "Certifications (CPA, CFA...)", "type": "text"},
            {"name": "achievements", "label": "Key achievements / responsibilities", "type": "textarea"},
            {"name": "education", "label": "Education", "type": "text"},
        ],
    },
    {
        "id": "designer",
        "label": "Designer",
        "fields": [
            {"name": "full_name", "label": "Full name", "type": "text"},
            {"name": "email", "label": "Email", "type": "text"},
            {"name": "phone", "label": "Phone", "type": "text"},
            {"name": "years_experience", "label": "Years of experience", "type": "text"},
            {"name": "tools", "label": "Design tools (Figma, Adobe CC...)", "type": "text"},
            {"name": "portfolio_highlights", "label": "Portfolio highlights / achievements", "type": "textarea"},
            {"name": "education", "label": "Education", "type": "text"},
        ],
    },
]


class CVOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    version_name: str | None
    structured_data: dict | None
    is_base: bool
    pdf_url: str | None = None
    latex_source: str | None = None
    font_id: str | None = None
    created_at: datetime


class GenerateCVRequest(BaseModel):
    description: str
    language: str = "English"
    font_id: str | None = None
    version_name: str | None = None


class ImproveCVRequest(BaseModel):
    language: str = "English"
    font_id: str | None = None


class ImproveCVResponse(BaseModel):
    cv: CVOut
    original_structured_data: dict


class TailorRequest(BaseModel):
    job_description: str


class TailorResponse(BaseModel):
    tailored_text: str


class GapItemOut(BaseModel):
    gap: str
    importance: str
    how_to_close: str


class GapAnalysisResponse(BaseModel):
    match_percentage: int
    strong_matches: list[str]
    gaps: list[GapItemOut]
    interview_risks: list[str]


class FitEvaluationResponse(BaseModel):
    score: int
    recommendation: str
    reasons: list[str]


async def _get_owned_cv(db: AsyncSession, user_id: uuid.UUID, cv_id: str) -> CV:
    try:
        cv_uuid = uuid.UUID(cv_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="CV not found")

    result = await db.execute(select(CV).where(CV.id == cv_uuid, CV.user_id == user_id))
    cv = result.scalar_one_or_none()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv


@router.post("/upload", response_model=CVOut, status_code=201)
async def upload_cv(
    file: UploadFile = File(...),
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    try:
        text = extract_text(contents, file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    try:
        structured = await cv_agent.parse_cv(text)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to parse CV")

    user_id = uuid.UUID(user["id"])

    result = await db.execute(select(CV.id).where(CV.user_id == user_id))
    has_existing = result.first() is not None

    cv = CV(
        user_id=user_id,
        version_name=file.filename,
        raw_text=text,
        structured_data=structured,
        is_base=not has_existing,
    )
    db.add(cv)
    await db.flush()
    await db.refresh(cv)
    return cv


@router.get("/fonts")
async def list_fonts():
    return _FONTS


@router.get("/templates")
async def list_templates():
    return _PROFESSION_TEMPLATES


@router.post("/generate", response_model=CVOut, status_code=201)
async def generate_cv(
    body: GenerateCVRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    if not body.description.strip():
        raise HTTPException(status_code=400, detail="Description is required")

    try:
        structured = await cv_agent.generate_cv_from_description(body.description, body.language)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to generate CV")

    user_id = uuid.UUID(user["id"])

    result = await db.execute(select(CV.id).where(CV.user_id == user_id))
    has_existing = result.first() is not None

    latex_source = build_latex_cv(structured, body.font_id)

    cv = CV(
        user_id=user_id,
        version_name=body.version_name or "Generated CV",
        structured_data=structured,
        latex_source=latex_source,
        font_id=body.font_id,
        is_base=not has_existing,
    )
    db.add(cv)
    await db.flush()
    await db.refresh(cv)

    try:
        pdf_bytes = render_cv_pdf(structured, body.font_id)
        cv.pdf_url = upload_cv_pdf(f"{user_id}/{cv.id}.pdf", pdf_bytes)
        await db.flush()
        await db.refresh(cv)
    except Exception:
        pass

    return cv


@router.post("/improve-uploaded", response_model=ImproveCVResponse, status_code=201)
async def improve_uploaded_cv(
    file: UploadFile = File(...),
    language: str = "English",
    font_id: str | None = None,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    try:
        text = extract_text(contents, file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    try:
        original_structured = await cv_agent.parse_cv(text)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to parse CV")

    try:
        improved_structured = await cv_agent.improve_and_translate_cv(original_structured, language)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to improve CV")

    user_id = uuid.UUID(user["id"])

    result = await db.execute(select(CV.id).where(CV.user_id == user_id))
    has_existing = result.first() is not None

    latex_source = build_latex_cv(improved_structured, font_id)

    cv = CV(
        user_id=user_id,
        version_name=f"Improved – {file.filename}",
        raw_text=text,
        structured_data=improved_structured,
        latex_source=latex_source,
        font_id=font_id,
        is_base=not has_existing,
    )
    db.add(cv)
    await db.flush()
    await db.refresh(cv)

    try:
        pdf_bytes = render_cv_pdf(improved_structured, font_id)
        cv.pdf_url = upload_cv_pdf(f"{user_id}/{cv.id}.pdf", pdf_bytes)
        await db.flush()
        await db.refresh(cv)
    except Exception:
        pass

    return ImproveCVResponse(cv=cv, original_structured_data=original_structured)


@router.get("/", response_model=list[CVOut])
async def list_cvs(user: dict = Depends(require_job_seeker), db: AsyncSession = Depends(get_db)):
    user_id = uuid.UUID(user["id"])
    result = await db.execute(
        select(CV).where(CV.user_id == user_id).order_by(CV.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{cv_id}", response_model=CVOut)
async def get_cv(
    cv_id: str, user: dict = Depends(require_job_seeker), db: AsyncSession = Depends(get_db)
):
    user_id = uuid.UUID(user["id"])
    return await _get_owned_cv(db, user_id, cv_id)


@router.patch("/{cv_id}/activate", response_model=CVOut)
async def activate_cv(
    cv_id: str, user: dict = Depends(require_job_seeker), db: AsyncSession = Depends(get_db)
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)

    await db.execute(update(CV).where(CV.user_id == user_id).values(is_base=False))
    cv.is_base = True
    await db.flush()
    await db.refresh(cv)
    return cv


@router.post("/{cv_id}/tailor", response_model=TailorResponse)
async def tailor_cv(
    cv_id: str,
    body: TailorRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)
    if not cv.raw_text:
        raise HTTPException(status_code=400, detail="CV has no extracted text")

    result = await db.execute(select(Profile.writing_style).where(Profile.user_id == user_id))
    writing_style = result.scalar_one_or_none()

    try:
        tailored = await cv_agent.tailor_cv(cv.raw_text, body.job_description, writing_style)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to tailor CV")

    return TailorResponse(tailored_text=tailored)


@router.post("/{cv_id}/gap-analysis", response_model=GapAnalysisResponse)
async def gap_analysis(
    cv_id: str,
    body: TailorRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)
    if not cv.raw_text:
        raise HTTPException(status_code=400, detail="CV has no extracted text")

    try:
        result = await cv_agent.gap_analysis(cv.raw_text, body.job_description)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to run gap analysis")

    return result


@router.post("/{cv_id}/evaluate-fit", response_model=FitEvaluationResponse)
async def evaluate_fit(
    cv_id: str,
    body: TailorRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)
    if not cv.raw_text:
        raise HTTPException(status_code=400, detail="CV has no extracted text")

    try:
        result = await match_agent.evaluate_fit(cv.raw_text, body.job_description)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to evaluate fit")

    return result


@router.delete("/{cv_id}", status_code=204)
async def delete_cv(
    cv_id: str, user: dict = Depends(require_job_seeker), db: AsyncSession = Depends(get_db)
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)
    await db.delete(cv)
    return None
