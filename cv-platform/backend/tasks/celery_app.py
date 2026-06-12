from celery import Celery
from celery.schedules import crontab

from core.config import settings

celery_app = Celery(
    "cv_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.job_refresh", "tasks.scoring", "tasks.discord_notifications"],
)

celery_app.conf.beat_schedule = {
    "refresh-jobs-every-6-hours": {
        "task": "tasks.job_refresh.refresh_all_jobs",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "check-job-emails-hourly": {
        "task": "tasks.job_refresh.check_job_emails",
        "schedule": crontab(minute=0),
    },
    "discord-daily-jobs-1400": {
        "task": "tasks.discord_notifications.send_daily_jobs",
        "schedule": crontab(hour=11, minute=0),  # 14:00 Israel time (UTC+3)
    },
}

celery_app.conf.timezone = "UTC"
