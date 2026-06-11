import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.auth import require_job_seeker
from core.database import get_db
from models.cv import CV
from models.user import Profile
from agents import interview_agent

router = APIRouter()


class InterviewQuestionsRequest(BaseModel):
    job_description: str | None = None


class InterviewQuestionOut(BaseModel):
    question: str
    type: Literal["behavioral", "technical"]
    guidance: str


class InterviewQuestionsResponse(BaseModel):
    questions: list[InterviewQuestionOut]


@router.post("/questions", response_model=InterviewQuestionsResponse)
async def generate_questions(
    body: InterviewQuestionsRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])

    result = await db.execute(
        select(CV)
        .where(CV.user_id == user_id)
        .order_by(CV.is_base.desc(), CV.created_at.desc())
        .limit(1)
    )
    cv = result.scalars().first()
    if not cv or not cv.raw_text:
        raise HTTPException(status_code=400, detail="Upload a CV before generating questions")

    job_description = body.job_description
    if not job_description:
        result = await db.execute(select(Profile.target_role).where(Profile.user_id == user_id))
        target_role = result.scalar_one_or_none()
        job_description = target_role or "General role matching the candidate's experience"

    try:
        generated = await interview_agent.generate_questions(cv.raw_text, job_description)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to generate interview questions")

    return generated
