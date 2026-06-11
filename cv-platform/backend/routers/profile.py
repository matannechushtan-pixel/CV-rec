import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.auth import require_job_seeker
from core.database import get_db
from models.cv import CV
from models.user import Profile
from agents import cv_agent, roadmap_agent

router = APIRouter()


class EnrichRequest(BaseModel):
    answers: list[str]


class EnrichResponse(BaseModel):
    behavioral_profile: dict
    writing_style: dict


class UpskillGapOut(BaseModel):
    skill: str
    priority: str
    resource_url: str
    estimated_weeks: int


class UpskillReportResponse(BaseModel):
    current_level: str
    target_role: str
    gaps: list[UpskillGapOut]
    total_estimated_weeks: int


class UpskillReportRequest(BaseModel):
    target_role: str | None = None


async def _get_profile(db: AsyncSession, user_id: uuid.UUID) -> Profile:
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/enrich-questions")
async def enrich_questions():
    return cv_agent.ENRICHMENT_QUESTIONS


@router.post("/enrich", response_model=EnrichResponse)
async def enrich_profile(
    body: EnrichRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    if len(body.answers) != len(cv_agent.ENRICHMENT_QUESTIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Expected {len(cv_agent.ENRICHMENT_QUESTIONS)} answers",
        )

    user_id = uuid.UUID(user["id"])
    profile = await _get_profile(db, user_id)

    try:
        result = await cv_agent.extract_behavioral_profile(body.answers)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to analyze answers")

    profile.behavioral_profile = result.get("behavioral_profile")
    profile.writing_style = result.get("writing_style")
    await db.flush()

    return EnrichResponse(
        behavioral_profile=profile.behavioral_profile or {},
        writing_style=profile.writing_style or {},
    )


@router.post("/upskill-report", response_model=UpskillReportResponse)
async def upskill_report(
    body: UpskillReportRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    profile = await _get_profile(db, user_id)

    target_role = body.target_role or profile.target_role
    if not target_role:
        raise HTTPException(status_code=400, detail="No target role set on profile")

    result = await db.execute(
        select(CV)
        .where(CV.user_id == user_id)
        .order_by(CV.is_base.desc(), CV.created_at.desc())
        .limit(1)
    )
    cv = result.scalars().first()
    if not cv or not cv.raw_text:
        raise HTTPException(status_code=400, detail="Upload a CV before generating an upskill report")

    try:
        report = await roadmap_agent.generate_upskill_report(cv.raw_text, target_role)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to generate upskill report")

    return report
