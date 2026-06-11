from tasks.celery_app import celery_app


@celery_app.task(name="tasks.scoring.score_cv_job_pair")
def score_cv_job_pair(cv_id: str, job_id: str):
    """Run match scoring for a cv/job pair and persist the result."""
    # Phase 3 implementation:
    # 1. Run match_agent.score_cv_against_job(cv_id, job_id, db)
    # 2. Upsert into applications or a match_scores cache table
    pass
