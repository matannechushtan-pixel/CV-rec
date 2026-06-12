"""
Saves extracted job listings to the database.
Skips duplicates using external_id or title+company fingerprint.
"""
import hashlib
import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.job import JobListing

logger = logging.getLogger(__name__)


def _make_external_id(job: dict) -> str:
    """Create a stable external_id for email-sourced jobs."""
    key = (
        (job.get("title") or "").lower().strip() + "|" +
        (job.get("company") or "").lower().strip() + "|" +
        (job.get("apply_url") or "")
    )
    return "email_" + hashlib.md5(key.encode()).hexdigest()[:16]


async def save_jobs_to_db(
    jobs: list[dict],
    db:   AsyncSession,
) -> dict:
    """
    Save a list of extracted job dicts to job_listings.
    Returns stats: {saved, skipped, errors}
    """
    stats = {"saved": 0, "skipped": 0, "errors": 0}

    for job in jobs:
        try:
            ext_id = (
                job.get("external_id") or
                _make_external_id(job)
            )

            # Check for duplicate
            existing = await db.execute(
                select(JobListing).where(
                    JobListing.external_id == ext_id)
            )
            if existing.scalar_one_or_none():
                stats["skipped"] += 1
                continue

            listing = JobListing(
                id            = uuid.uuid4(),
                external_id   = ext_id,
                source        = job.get("source", "email"),
                title         = job.get("title", ""),
                company       = job.get("company"),
                location      = job.get("location"),
                description   = job.get("description"),
                apply_url     = job.get("apply_url"),
                salary_min    = job.get("salary_min"),
                salary_max    = job.get("salary_max"),
                required_skills = {
                    "skills":          job.get("required_skills", []),
                    "employment_type": job.get("employment_type"),
                    "salary_currency": job.get("salary_currency"),
                },
            )
            db.add(listing)
            stats["saved"] += 1

        except Exception as e:
            logger.error("Error saving job '%s': %s",
                         job.get("title", "?"), e)
            stats["errors"] += 1

    await db.commit()
    return stats
