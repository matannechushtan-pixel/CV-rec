import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.auth import require_job_seeker
from core.database import get_db
from models.application import Application
from models.job import JobListing

router = APIRouter()

ALLOWED_STATUSES = {"applied", "viewed", "interview", "rejected", "offer"}


class JobListingMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    company: str | None
    location: str | None
    apply_url: str | None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_listing_id: uuid.UUID | None
    cv_id: uuid.UUID | None
    match_score: float | None
    status: str
    applied_at: datetime
    updated_at: datetime
    notes: str | None
    cover_letter_id: uuid.UUID | None
    job: JobListingMini | None = Field(default=None, validation_alias="job_listing")


class CreateApplicationRequest(BaseModel):
    job_listing_id: uuid.UUID
    cv_id: uuid.UUID | None = None
    match_score: float | None = None


class UpdateApplicationRequest(BaseModel):
    status: str | None = None
    notes: str | None = None


class ApplicationStats(BaseModel):
    applied: int = 0
    viewed: int = 0
    interview: int = 0
    rejected: int = 0
    offer: int = 0


@router.post("/", response_model=ApplicationOut, status_code=201)
async def create_application(
    body: CreateApplicationRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])

    job = await db.get(JobListing, body.job_listing_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    application = Application(
        user_id=user_id,
        job_listing_id=body.job_listing_id,
        cv_id=body.cv_id,
        match_score=body.match_score,
    )
    db.add(application)
    await db.flush()
    await db.refresh(application, attribute_names=["job_listing"])
    return application


@router.get("/", response_model=list[ApplicationOut])
async def list_applications(
    user: dict = Depends(require_job_seeker), db: AsyncSession = Depends(get_db)
):
    user_id = uuid.UUID(user["id"])
    result = await db.execute(
        select(Application)
        .where(Application.user_id == user_id)
        .options(selectinload(Application.job_listing))
        .order_by(Application.applied_at.desc())
    )
    return result.scalars().all()


@router.get("/stats", response_model=ApplicationStats)
async def application_stats(
    user: dict = Depends(require_job_seeker), db: AsyncSession = Depends(get_db)
):
    user_id = uuid.UUID(user["id"])
    result = await db.execute(
        select(Application.status).where(Application.user_id == user_id)
    )
    counts = ApplicationStats()
    for (status,) in result.all():
        if hasattr(counts, status):
            setattr(counts, status, getattr(counts, status) + 1)
    return counts


@router.patch("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: str,
    body: UpdateApplicationRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    if body.status is not None and body.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    user_id = uuid.UUID(user["id"])
    try:
        app_uuid = uuid.UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Application not found")

    result = await db.execute(
        select(Application)
        .where(Application.id == app_uuid, Application.user_id == user_id)
        .options(selectinload(Application.job_listing))
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if body.status is not None:
        application.status = body.status
    if body.notes is not None:
        application.notes = body.notes
    await db.flush()
    await db.refresh(application, attribute_names=["job_listing"])
    return application
