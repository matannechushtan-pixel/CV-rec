import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from core.auth import require_job_seeker
from core.database import get_db
from core.supabase_client import upload_cv_pdf
from models.cv import CV
from models.cover_letter import CoverLetter
from models.job import JobListing
from models.user import Profile
from agents import brainstorm_agent, cover_letter_agent, cv_agent, gemini_cv_agent, match_agent
from services.cv_html_builder import build_cv_html, get_templates
from services.embeddings import embed_text
from services.cv_parser import extract_text
from services.latex_builder import build_latex_cv, render_cv_pdf

logger = logging.getLogger(__name__)

router = APIRouter()

_FONTS_PATH = Path(__file__).parent.parent / "data" / "cv_fonts.json"
_FONTS: list[dict] = json.loads(_FONTS_PATH.read_text())

_FONT_OPTIONS_PATH = Path(__file__).parent.parent / "data" / "font_options.json"
_FONT_OPTIONS: list[dict] = json.loads(_FONT_OPTIONS_PATH.read_text())

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
    html_content: str | None = None
    source: str | None = None
    language: str | None = None
    cv_template_id: str | None = None
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


class CoverLetterRequest(BaseModel):
    job_description: str
    company_culture: str | None = None
    job_listing_id: str | None = None


class CoverLetterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_listing_id: uuid.UUID | None
    content: str | None
    created_at: datetime


class GapItemOut(BaseModel):
    gap: str
    importance: str
    how_to_close: str


class GapAnalysisResponse(BaseModel):
    match_percentage: int
    strong_matches: list[str]
    gaps: list[GapItemOut]
    interview_risks: list[str]


class MultiGapAnalysisResponse(BaseModel):
    claude: GapAnalysisResponse
    openai: GapAnalysisResponse | None = None


class FitEvaluationResponse(BaseModel):
    score: int
    recommendation: str
    reasons: list[str]


class GenerateFromDescriptionRequest(BaseModel):
    description: str
    language: str = "English"
    version_name: str | None = None
    cv_template_id: str = "classic_blue_photo"
    photo_base64: str | None = None
    section_titles: dict | None = None
    accent_color: str | None = None
    font_family: str | None = None


class GenerateFromTemplateRequest(BaseModel):
    template_id: str
    answers: dict
    language: str = "English"
    version_name: str | None = None
    cv_template_id: str = "classic_blue_photo"
    photo_base64: str | None = None
    section_titles: dict | None = None
    accent_color: str | None = None
    font_family: str | None = None


class UpdateCVContentRequest(BaseModel):
    structured_data: dict
    cv_template_id: str | None = None


def _apply_style_fields(
    structured: dict,
    section_titles: dict | None = None,
    accent_color: str | None = None,
    font_family: str | None = None,
) -> dict:
    """Persist optional section-title/accent-colour/font overrides into the CV's structured data."""
    if section_titles:
        structured["section_titles"] = section_titles
    if accent_color:
        structured["accent_color"] = accent_color
    if font_family:
        structured["font_family"] = font_family
    return structured


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
        logger.warning("Failed to parse CV for %s, saving without structured data", file.filename)
        structured = None

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


@router.post("/{cv_id}/parse", response_model=CVOut)
async def parse_cv(
    cv_id: str,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)

    if not cv.raw_text:
        raise HTTPException(status_code=400, detail="This CV has no extracted text to parse")

    try:
        cv.structured_data = await cv_agent.parse_cv(cv.raw_text)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to parse CV")

    await db.flush()
    await db.refresh(cv)
    return cv


@router.get("/fonts")
async def list_fonts():
    return _FONTS


@router.get("/templates")
async def list_templates():
    return _PROFESSION_TEMPLATES


@router.get("/design-templates")
async def list_design_templates():
    return get_templates()


@router.get("/font-options")
async def list_font_options():
    return _FONT_OPTIONS


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


@router.get("/cover-letters", response_model=list[CoverLetterOut])
async def list_cover_letters(
    user: dict = Depends(require_job_seeker), db: AsyncSession = Depends(get_db)
):
    user_id = uuid.UUID(user["id"])
    result = await db.execute(
        select(CoverLetter)
        .where(CoverLetter.user_id == user_id)
        .order_by(CoverLetter.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/cover-letters/{cover_letter_id}", status_code=204)
async def delete_cover_letter(
    cover_letter_id: str,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    try:
        cl_uuid = uuid.UUID(cover_letter_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Cover letter not found")

    result = await db.execute(
        select(CoverLetter).where(CoverLetter.id == cl_uuid, CoverLetter.user_id == user_id)
    )
    cover_letter = result.scalar_one_or_none()
    if not cover_letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")

    await db.delete(cover_letter)
    return None


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


@router.post("/{cv_id}/cover-letter", response_model=CoverLetterOut)
async def generate_cover_letter(
    cv_id: str,
    body: CoverLetterRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)
    if not cv.raw_text:
        raise HTTPException(status_code=400, detail="CV has no extracted text")

    result = await db.execute(
        select(Profile.full_name, Profile.writing_style).where(Profile.user_id == user_id)
    )
    row = result.first()
    full_name = row[0] if row else None
    writing_style = row[1] if row else None

    job_listing_uuid: uuid.UUID | None = None
    if body.job_listing_id:
        try:
            job_listing_uuid = uuid.UUID(body.job_listing_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job_listing_id")

    try:
        kwargs = dict(
            cv_text=cv.raw_text,
            candidate_name=full_name or "Candidate",
            job_description=body.job_description,
            writing_style=writing_style,
        )
        if body.company_culture:
            kwargs["company_culture"] = body.company_culture
        content = await cover_letter_agent.generate_cover_letter(**kwargs)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to generate cover letter")

    cover_letter = CoverLetter(
        user_id=user_id,
        job_listing_id=job_listing_uuid,
        content=content,
    )
    db.add(cover_letter)
    await db.flush()
    await db.refresh(cover_letter)
    return cover_letter


@router.post("/{cv_id}/gap-analysis", response_model=MultiGapAnalysisResponse)
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
        result = await cv_agent.gap_analysis_multi(cv.raw_text, body.job_description)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to run gap analysis")

    return result


@router.post("/{cv_id}/auto-gap-analysis")
async def auto_gap_analysis(
    cv_id: str,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)

    if cv.structured_data:
        cv_text = json.dumps(cv.structured_data, ensure_ascii=False)
    elif cv.raw_text:
        cv_text = cv.raw_text
    else:
        raise HTTPException(status_code=400, detail="CV has no content to analyze")

    try:
        return await cv_agent.cv_only_gap_analysis(cv_text)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to run gap analysis")


@router.post("/{cv_id}/match-professions")
async def match_professions(
    cv_id: str,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)

    if cv.structured_data:
        cv_text = json.dumps(cv.structured_data, ensure_ascii=False)
    elif cv.raw_text:
        cv_text = cv.raw_text
    else:
        raise HTTPException(status_code=400, detail="CV has no content to analyse")

    # Step 1: Claude reads the CV and extracts keywords
    try:
        keywords = await cv_agent.extract_cv_keywords(cv_text)
    except Exception:
        logging.getLogger(__name__).error("Keyword extraction failed for CV %s", cv_id)
        raise HTTPException(status_code=502, detail="Failed to analyse CV")

    # Step 2: Match to professions via skill-profession map
    from services.recommendation_engine import (
        match_cv_keywords_to_profession,
        match_cv_to_jobs,
    )

    try:
        professions = await match_cv_keywords_to_profession(keywords)

        # Step 3: Embed full CV text for job matching
        cv_embedding = await embed_text(cv_text[:8000])
        top_jobs = await match_cv_to_jobs(cv_embedding, top_n=10) if cv_embedding else []
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "extracted_keywords": keywords,
        "matched_professions": professions,
        "matched_jobs":        top_jobs,
    }


@router.post("/{cv_id}/brainstorm-summary")
async def brainstorm_summary(
    cv_id: str,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)
    if not cv.structured_data:
        raise HTTPException(status_code=400, detail="CV has no structured data")

    try:
        return await brainstorm_agent.brainstorm_cv_summary(cv.structured_data)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to brainstorm summaries")


class BrainstormJobFitRequest(BaseModel):
    job_ids: list[str]


@router.post("/{cv_id}/brainstorm-job-fit")
async def brainstorm_job_fit(
    cv_id: str,
    body: BrainstormJobFitRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)
    if not cv.structured_data:
        raise HTTPException(status_code=400, detail="CV has no structured data")

    if not body.job_ids:
        raise HTTPException(status_code=400, detail="job_ids is required")

    job_uuids = [uuid.UUID(j) for j in body.job_ids]
    result = await db.execute(select(JobListing).where(JobListing.id.in_(job_uuids)))
    jobs = result.scalars().all()
    if not jobs:
        raise HTTPException(status_code=404, detail="No matching jobs found")

    jobs_payload = [
        {"job_id": str(j.id), "title": j.title, "company": j.company, "description": j.description}
        for j in jobs
    ]

    try:
        return await brainstorm_agent.brainstorm_job_fit(cv.structured_data, jobs_payload)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to brainstorm job fit")


@router.post("/{cv_id}/brainstorm-career-paths")
async def brainstorm_career_paths(
    cv_id: str,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)
    if not cv.structured_data:
        raise HTTPException(status_code=400, detail="CV has no structured data")

    try:
        return await brainstorm_agent.brainstorm_career_paths(cv.structured_data)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to brainstorm career paths")


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


@router.post("/generate/from-description", response_model=CVOut, status_code=201)
async def generate_from_description(
    body: GenerateFromDescriptionRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    if not body.description.strip():
        raise HTTPException(status_code=400, detail="Description is required")

    try:
        structured, model_used = await gemini_cv_agent.generate_from_description(body.description, body.language)
    except Exception as e:
        logging.getLogger(__name__).error("CV generation failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="CV generation is temporarily unavailable. Please try again in a moment.",
        )

    structured = _apply_style_fields(structured, body.section_titles, body.accent_color, body.font_family)
    structured["generation_model"] = model_used
    html_content = build_cv_html(
        structured, body.cv_template_id, body.photo_base64,
        accent_color=body.accent_color, font_family=body.font_family,
        language=body.language,
    )

    user_id = uuid.UUID(user["id"])
    result = await db.execute(select(CV.id).where(CV.user_id == user_id))
    has_existing = result.first() is not None

    cv = CV(
        user_id=user_id,
        version_name=body.version_name or "Generated CV",
        structured_data=structured,
        html_content=html_content,
        source="description",
        language=body.language,
        cv_template_id=body.cv_template_id,
        is_base=not has_existing,
    )
    db.add(cv)
    await db.flush()
    await db.refresh(cv)
    return cv


@router.post("/generate/from-template", response_model=CVOut, status_code=201)
async def generate_from_template(
    body: GenerateFromTemplateRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    if not body.answers:
        raise HTTPException(status_code=400, detail="Template answers are required")

    try:
        structured, model_used = await gemini_cv_agent.fill_from_template(body.answers, body.language)
    except Exception as e:
        logging.getLogger(__name__).error("CV generation failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="CV generation is temporarily unavailable. Please try again in a moment.",
        )

    structured = _apply_style_fields(structured, body.section_titles, body.accent_color, body.font_family)
    structured["generation_model"] = model_used
    html_content = build_cv_html(
        structured, body.cv_template_id, body.photo_base64,
        accent_color=body.accent_color, font_family=body.font_family,
        language=body.language,
    )

    user_id = uuid.UUID(user["id"])
    result = await db.execute(select(CV.id).where(CV.user_id == user_id))
    has_existing = result.first() is not None

    cv = CV(
        user_id=user_id,
        version_name=body.version_name or "Generated CV",
        structured_data=structured,
        html_content=html_content,
        source="template",
        language=body.language,
        cv_template_id=body.cv_template_id,
        is_base=not has_existing,
    )
    db.add(cv)
    await db.flush()
    await db.refresh(cv)
    return cv


@router.post("/generate/improve-uploaded", response_model=CVOut, status_code=201)
async def generate_improve_uploaded(
    file: UploadFile = File(...),
    language: str = "English",
    cv_template_id: str = "classic_blue_photo",
    photo_base64: str | None = Form(default=None),
    section_titles: str | None = Form(default=None),
    accent_color: str | None = Form(default=None),
    font_family: str | None = Form(default=None),
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
        structured, model_used = await gemini_cv_agent.improve_uploaded_cv(text, language)
    except Exception as e:
        logging.getLogger(__name__).error("CV generation failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="CV generation is temporarily unavailable. Please try again in a moment.",
        )

    parsed_titles = json.loads(section_titles) if section_titles else None
    structured = _apply_style_fields(structured, parsed_titles, accent_color, font_family)
    structured["generation_model"] = model_used
    html_content = build_cv_html(
        structured, cv_template_id, photo_base64,
        accent_color=accent_color, font_family=font_family,
        language=language,
    )

    user_id = uuid.UUID(user["id"])
    result = await db.execute(select(CV.id).where(CV.user_id == user_id))
    has_existing = result.first() is not None

    cv = CV(
        user_id=user_id,
        version_name=f"Improved – {file.filename}",
        raw_text=text,
        structured_data=structured,
        html_content=html_content,
        source="upload",
        language=language,
        cv_template_id=cv_template_id,
        is_base=not has_existing,
    )
    db.add(cv)
    await db.flush()
    await db.refresh(cv)
    return cv


@router.get("/{cv_id}/html", response_class=HTMLResponse)
async def get_cv_html(
    cv_id: str, user: dict = Depends(require_job_seeker), db: AsyncSession = Depends(get_db)
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)

    if cv.html_content:
        return HTMLResponse(content=cv.html_content)
    if cv.structured_data:
        return HTMLResponse(content=build_cv_html(
            cv.structured_data, cv.cv_template_id or "classic_blue_photo",
            accent_color=cv.structured_data.get("accent_color"),
            font_family=cv.structured_data.get("font_family"),
        ))
    raise HTTPException(status_code=404, detail="CV has no content to render")


@router.post("/{cv_id}/translate", response_model=CVOut, status_code=201)
async def translate_cv_endpoint(
    cv_id: str,
    target_language: str = Query(..., description="Target language: 'Hebrew' or 'English'"),
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)
    if not cv.structured_data:
        raise HTTPException(status_code=400, detail="CV has no structured data to translate")

    try:
        translated_data, model_used = await gemini_cv_agent.translate_cv(cv.structured_data, target_language)
    except Exception as e:
        logging.getLogger(__name__).error("CV translation failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="CV translation is temporarily unavailable. Please try again in a moment.",
        )

    translated_data["generation_model"] = model_used
    html_content = build_cv_html(
        translated_data,
        template_id=cv.cv_template_id or "classic_blue_photo",
        photo_base64=None,
        accent_color=translated_data.get("accent_color"),
        font_family=translated_data.get("font_family"),
        language=target_language,
    )

    new_cv = CV(
        user_id=user_id,
        version_name=f"{cv.version_name} ({target_language})",
        html_content=html_content,
        structured_data=translated_data,
        cv_template_id=cv.cv_template_id,
        source="translated",
        language=target_language,
    )
    db.add(new_cv)
    await db.flush()
    await db.refresh(new_cv)
    return new_cv


@router.patch("/{cv_id}/content", response_model=CVOut)
async def update_cv_content(
    cv_id: str,
    body: UpdateCVContentRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)

    cv.structured_data = body.structured_data
    if body.cv_template_id:
        cv.cv_template_id = body.cv_template_id
    cv.html_content = build_cv_html(
        body.structured_data, cv.cv_template_id or "classic_blue_photo",
        accent_color=body.structured_data.get("accent_color"),
        font_family=body.structured_data.get("font_family"),
    )
    await db.flush()
    await db.refresh(cv)
    return cv


@router.delete("/{cv_id}", status_code=204)
async def delete_cv(
    cv_id: str, user: dict = Depends(require_job_seeker), db: AsyncSession = Depends(get_db)
):
    user_id = uuid.UUID(user["id"])
    cv = await _get_owned_cv(db, user_id, cv_id)
    await db.delete(cv)
    return None
