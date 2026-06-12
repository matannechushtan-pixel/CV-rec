import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.auth import require_job_seeker, get_current_user
from core.database import get_db
from models.cv import CV
from models.job import JobListing
from models.user import Profile
from services.adzuna import fetch_adzuna_jobs
from services.jsearch import fetch_jsearch_jobs
from services.jobs_api14 import fetch_jobs_api14
from services.recommendation_engine import recommend_jobs
from services.salary_lookup import get_salary_range
from agents import search_agent

router = APIRouter()


class JobListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str | None
    source: str | None
    title: str | None
    company: str | None
    location: str | None
    description: str | None
    required_skills: dict | list | None
    salary_min: int | None
    salary_max: int | None
    apply_url: str | None
    fetched_at: datetime


class GapItemOut(BaseModel):
    gap: str
    importance: str
    how_to_close: str


class RecommendedJobsRequest(BaseModel):
    cv_id: str


class RecommendedJobOut(JobListingOut):
    match_score: int


class SmartSearchRequest(BaseModel):
    title: str | None = None
    location: str | None = None


class SmartSearchResult(BaseModel):
    job: JobListingOut
    match_percentage: int
    strong_matches: list[str]
    gaps: list[GapItemOut]
    tailored_cv_snippet: str | None


async def _upsert_job(db: AsyncSession, job: dict) -> JobListing:
    stmt = (
        pg_insert(JobListing)
        .values(**job)
        .on_conflict_do_update(
            index_elements=["external_id"],
            set_={k: v for k, v in job.items() if k != "external_id"},
        )
        .returning(JobListing)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def _refresh_jobs(db: AsyncSession, title: str, location: str) -> None:
    fetched: list[dict] = []
    try:
        fetched += await fetch_adzuna_jobs(title, location)
    except Exception:
        pass
    try:
        fetched += await fetch_jsearch_jobs(title, location)
    except Exception:
        pass
    try:
        fetched += await fetch_jobs_api14(title, location)
    except Exception:
        pass

    for job in fetched:
        if not job.get("external_id"):
            continue
        stmt = (
            pg_insert(JobListing)
            .values(**job)
            .on_conflict_do_nothing(index_elements=["external_id"])
        )
        await db.execute(stmt)
    if fetched:
        await db.flush()


@router.get("/", response_model=list[JobListingOut])
async def list_jobs(
    title: str | None = None,
    location: str | None = None,
    remote: bool | None = None,
    salary_min: int | None = None,
    date_posted: str | None = None,
    employment_type: str | None = None,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])

    if not title:
        result = await db.execute(select(Profile.target_role).where(Profile.user_id == user_id))
        title = result.scalar_one_or_none()

    title = title or "Software Engineer"
    location = location or "Remote"

    await _refresh_jobs(db, title, location)

    query = select(JobListing).order_by(JobListing.fetched_at.desc())
    if title:
        query = query.where(
            or_(JobListing.title.ilike(f"%{title}%"), JobListing.description.ilike(f"%{title}%"))
        )
    if remote:
        query = query.where(
            or_(JobListing.location.ilike("%remote%"), JobListing.description.ilike("%remote%"))
        )
    if salary_min is not None:
        query = query.where(
            or_(JobListing.salary_min >= salary_min, JobListing.salary_max >= salary_min)
        )
    if date_posted in ("day", "week", "month"):
        days = {"day": 1, "week": 7, "month": 30}[date_posted]
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.where(JobListing.fetched_at >= cutoff)
    if employment_type:
        query = query.where(
            JobListing.required_skills["employment_type"].astext.ilike(employment_type)
        )
    query = query.limit(30)

    result = await db.execute(query)
    jobs = result.scalars().all()
    return jobs


@router.post("/smart-search", response_model=list[SmartSearchResult])
async def smart_search(
    body: SmartSearchRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])

    title = body.title
    location = body.location or "Remote"

    if not title:
        result = await db.execute(select(Profile.target_role).where(Profile.user_id == user_id))
        title = result.scalar_one_or_none() or "Software Engineer"

    result = await db.execute(
        select(CV)
        .where(CV.user_id == user_id)
        .order_by(CV.is_base.desc(), CV.created_at.desc())
        .limit(1)
    )
    cv = result.scalars().first()
    if not cv or not cv.raw_text:
        raise HTTPException(status_code=400, detail="Upload a CV before using smart search")

    ranked = await search_agent.find_best_jobs(title, location, cv.raw_text)

    response = []
    for item in ranked:
        job_row = await _upsert_job(db, item["job"])
        response.append(
            SmartSearchResult(
                job=JobListingOut.model_validate(job_row),
                match_percentage=item["match_percentage"],
                strong_matches=item["strong_matches"],
                gaps=item["gaps"],
                tailored_cv_snippet=item.get("tailored_cv_snippet"),
            )
        )
    return response


@router.post("/recommended", response_model=list[RecommendedJobOut])
async def recommended_jobs(
    body: RecommendedJobsRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])

    try:
        cv_uuid = uuid.UUID(body.cv_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="CV not found")

    result = await db.execute(select(CV).where(CV.id == cv_uuid, CV.user_id == user_id))
    cv = result.scalar_one_or_none()
    if not cv or not cv.structured_data:
        raise HTTPException(status_code=400, detail="CV has no parsed data")

    experience = cv.structured_data.get("experience") or []
    title = experience[0].get("title") if experience else None
    title = title or "Software Engineer"

    await _refresh_jobs(db, title, "Remote")

    result = await db.execute(
        select(JobListing).order_by(JobListing.fetched_at.desc()).limit(50)
    )
    jobs = result.scalars().all()
    job_dicts = [JobListingOut.model_validate(j).model_dump(mode="json") for j in jobs]

    ranked = await recommend_jobs(cv.structured_data, job_dicts, top_n=10)
    return ranked


@router.get("/debug/jsearch-cache")
async def jsearch_cache_stats(user=Depends(get_current_user)):
    from services.jsearch import cache_stats
    return cache_stats()


@router.get("/{job_id}/salary")
async def job_salary(
    job_id: str, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")

    job = await db.get(JobListing, job_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.salary_min and job.salary_max:
        return {
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "currency": "USD",
            "source": "listing",
        }

    return await get_salary_range(job.title or "Software Engineer", job.location or "Remote")


@router.get("/{job_id}", response_model=JobListingOut)
async def get_job(
    job_id: str, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")

    job = await db.get(JobListing, job_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
