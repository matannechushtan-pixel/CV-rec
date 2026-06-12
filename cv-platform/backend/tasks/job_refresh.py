import asyncio
import logging
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.job_refresh.check_job_emails")
def check_job_emails():
    """
    Celery task: read unread job alert emails and save to DB.
    Runs every hour automatically.
    """
    asyncio.run(_check_job_emails_async())


async def _check_job_emails_async():
    from services.gmail_reader import fetch_and_parse_job_emails
    from services.job_saver    import save_jobs_to_db
    from core.database         import AsyncSessionLocal

    logger.info("Starting email job check...")

    jobs = await fetch_and_parse_job_emails(max_emails=50)
    logger.info("Parsed %d jobs from emails", len(jobs))

    if not jobs:
        return

    async with AsyncSessionLocal() as db:
        stats = await save_jobs_to_db(jobs, db)

    logger.info(
        "Email job check complete: saved=%d skipped=%d errors=%d",
        stats["saved"], stats["skipped"], stats["errors"]
    )


@celery_app.task(name="tasks.job_refresh.refresh_all_jobs")
def refresh_all_jobs():
    """
    Celery task: fetch live jobs from JSearch/Adzuna every 6h.
    """
    asyncio.run(_refresh_all_jobs_async())


async def _refresh_all_jobs_async():
    from agents.job_agent      import fetch_jobs_for_profile
    from services.job_saver    import save_jobs_to_db
    from core.database         import AsyncSessionLocal
    from sqlalchemy            import select
    from models.user           import Profile

    logger.info("Starting job refresh...")

    async with AsyncSessionLocal() as db:
        # Get all unique target roles from user profiles
        result = await db.execute(
            select(Profile.target_role)
            .where(Profile.target_role.isnot(None))
            .distinct()
        )
        roles = [r[0] for r in result.fetchall()]

    if not roles:
        logger.info("No target roles found — skipping refresh")
        return

    logger.info("Refreshing jobs for %d roles", len(roles))

    for role in roles:
        try:
            jobs = await fetch_jobs_for_profile(
                title=role, location="Israel", limit=40)
            async with AsyncSessionLocal() as db:
                stats = await save_jobs_to_db(jobs, db)
            logger.info(
                "Role '%s': saved=%d skipped=%d",
                role, stats["saved"], stats["skipped"])
        except Exception as e:
            logger.error("Error refreshing role '%s': %s", role, e)
