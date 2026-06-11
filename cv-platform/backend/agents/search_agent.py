import asyncio

from agents.cv_agent import gap_analysis, tailor_cv
from services.adzuna import fetch_adzuna_jobs
from services.jsearch import fetch_jsearch_jobs

_CANDIDATE_POOL_SIZE = 8
_TOP_N = 5


async def _score_job(cv_text: str, job: dict) -> dict | None:
    description = job.get("description") or ""
    if not description:
        return None
    try:
        analysis = await gap_analysis(cv_text, description)
    except Exception:
        return None

    return {
        "job": job,
        "match_percentage": analysis.get("match_percentage", 0),
        "strong_matches": analysis.get("strong_matches", []),
        "gaps": analysis.get("gaps", []),
    }


async def _tailor_snippet(cv_text: str, job: dict) -> str | None:
    description = job.get("description") or ""
    try:
        return await tailor_cv(cv_text, description)
    except Exception:
        return None


async def find_best_jobs(title: str, location: str, cv_text: str) -> list[dict]:
    """Fetch live jobs, score each against the candidate's CV, and return the
    top-ranked matches with a tailored CV snippet for each."""
    fetched: list[dict] = []
    try:
        fetched += await fetch_adzuna_jobs(title, location)
    except Exception:
        pass
    try:
        fetched += await fetch_jsearch_jobs(title, location)
    except Exception:
        pass

    if not fetched:
        return []

    candidates = fetched[:_CANDIDATE_POOL_SIZE]
    scored = await asyncio.gather(*(_score_job(cv_text, job) for job in candidates))
    scored = [s for s in scored if s is not None]
    scored.sort(key=lambda s: s["match_percentage"], reverse=True)

    top = scored[:_TOP_N]
    snippets = await asyncio.gather(*(_tailor_snippet(cv_text, s["job"]) for s in top))
    for result, snippet in zip(top, snippets):
        result["tailored_cv_snippet"] = snippet

    return top
