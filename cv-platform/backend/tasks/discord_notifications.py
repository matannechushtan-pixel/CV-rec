import asyncio
import logging
from datetime import datetime, timedelta, timezone

from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.discord_notifications.send_daily_jobs")
def send_daily_jobs():
    asyncio.run(_send_daily_jobs_async())


async def _send_daily_jobs_async():
    from core.database import AsyncSessionLocal
    from models.discord import DiscordConnection
    from models.user import Profile
    from models.job import JobListing
    from services.discord_service import send_jobs_embed
    from sqlalchemy import select, and_

    logger.info("Starting daily Discord job notifications")
    since = datetime.now(timezone.utc) - timedelta(hours=25)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(DiscordConnection).where(
                and_(
                    DiscordConnection.is_active == True,
                    DiscordConnection.channel_id.isnot(None),
                )
            )
        )
        connections = result.scalars().all()

    logger.info("Found %d active Discord connections", len(connections))

    for conn in connections:
        try:
            async with AsyncSessionLocal() as db:
                profile_result = await db.execute(
                    select(Profile).where(Profile.user_id == conn.user_id)
                )
                profile = profile_result.scalar_one_or_none()
                target_role = (profile.target_role if profile else None) or "Software Engineer"

                jobs_result = await db.execute(
                    select(JobListing)
                    .where(JobListing.fetched_at >= since)
                    .where(
                        JobListing.title.ilike(f"%{target_role.split()[0]}%")
                    )
                    .order_by(JobListing.fetched_at.desc())
                    .limit(10)
                )
                jobs = jobs_result.scalars().all()
                jobs_dicts = [
                    {
                        "title": j.title,
                        "company": j.company,
                        "location": j.location,
                        "apply_url": j.apply_url,
                        "salary_min": j.salary_min,
                        "salary_max": j.salary_max,
                    }
                    for j in jobs
                ]

            if not jobs_dicts:
                logger.info("No new jobs for user %s (role: %s)", conn.user_id, target_role)
                continue

            sent = await send_jobs_embed(conn.channel_id, jobs_dicts, target_role)

            if sent:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(DiscordConnection).where(DiscordConnection.id == conn.id)
                    )
                    c = result.scalar_one()
                    c.last_notified_at = datetime.now(timezone.utc)
                logger.info(
                    "Sent %d jobs to Discord for user %s", len(jobs_dicts), conn.user_id
                )

        except Exception as e:
            logger.error("Discord notification failed for user %s: %s", conn.user_id, e)
