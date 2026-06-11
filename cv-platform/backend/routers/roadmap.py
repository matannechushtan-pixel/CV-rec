import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.auth import require_job_seeker
from core.database import get_db
from models.cv import CV
from models.user import Profile
from models.roadmap import Roadmap
from agents import roadmap_agent

router = APIRouter()


class RoadmapStepOut(BaseModel):
    area: str
    priority: int
    action: str
    resource: str
    estimated_weeks: int


class RoadmapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_role: str | None
    gap_analysis: dict | None
    steps: list[RoadmapStepOut] | None
    estimated_timeline_weeks: int | None
    created_at: datetime


class GenerateRoadmapRequest(BaseModel):
    target_role: str | None = None


@router.post("/generate", response_model=RoadmapOut, status_code=201)
async def generate_roadmap(
    body: GenerateRoadmapRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])

    target_role = body.target_role
    if not target_role:
        result = await db.execute(select(Profile.target_role).where(Profile.user_id == user_id))
        target_role = result.scalar_one_or_none()

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
        raise HTTPException(status_code=400, detail="Upload a CV before generating a roadmap")

    try:
        generated = await roadmap_agent.generate_roadmap(cv.raw_text, target_role)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to generate roadmap")

    roadmap = Roadmap(
        user_id=user_id,
        target_role=generated.get("target_role") or target_role,
        gap_analysis={
            "current_readiness_percentage": generated.get("current_readiness_percentage"),
            "immediate_actions": generated.get("immediate_actions", []),
            "quick_wins": generated.get("quick_wins", []),
        },
        steps=generated.get("gaps", []),
        estimated_timeline_weeks=generated.get("estimated_weeks_to_ready"),
    )
    db.add(roadmap)
    await db.flush()
    await db.refresh(roadmap)
    return roadmap


@router.get("/", response_model=RoadmapOut | None)
async def get_roadmap(user: dict = Depends(require_job_seeker), db: AsyncSession = Depends(get_db)):
    user_id = uuid.UUID(user["id"])
    result = await db.execute(
        select(Roadmap).where(Roadmap.user_id == user_id).order_by(Roadmap.created_at.desc()).limit(1)
    )
    return result.scalars().first()
