from celery import Celery
from celery.schedules import crontab

from core.config import settings

celery_app = Celery(
    "cv_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.job_refresh", "tasks.scoring"],
)

celery_app.conf.beat_schedule = {
    "refresh-jobs-every-6-hours": {
        "task": "tasks.job_refresh.refresh_all_jobs",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # NEW — check email for job alerts every hour
    "check-job-emails-hourly": {
        "task": "tasks.job_refresh.check_job_emails",
        "schedule": crontab(minute=0),  # every hour at :00
    },
}

celery_app.conf.timezone = "UTC"
