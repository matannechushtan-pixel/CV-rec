from tasks.celery_app import celery_app


@celery_app.task(name="tasks.job_refresh.refresh_all_jobs")
def refresh_all_jobs():
    """Fetch top 100 jobs per active user's target role, deduplicate by external_id."""
    # Phase 3 implementation:
    # 1. Query all profiles with a target_role
    # 2. For each unique role, call fetch_jobs_for_profile()
    # 3. Upsert into job_listings on conflict external_id
    # 4. Kick off scoring.score_new_jobs.delay() for each new listing
    pass
