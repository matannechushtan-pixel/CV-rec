import asyncio
import json
import anthropic

from core.config import settings
from services.adzuna import fetch_adzuna_jobs
from services.jsearch import fetch_jsearch_jobs

_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

_SKILL_EXTRACT_PROMPT = """
Extract required and preferred skills from this job description.
Return JSON only (no markdown):
{{
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill3"],
  "years_experience_required": 0,
  "education_required": "",
  "key_responsibilities": ["responsibility1"]
}}

JOB DESCRIPTION:
{job_description}
"""


async def extract_skills(job_description: str) -> dict:
    msg = await _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": _SKILL_EXTRACT_PROMPT.format(job_description=job_description),
            }
        ],
    )
    return json.loads(msg.content[0].text)


async def fetch_jobs_for_profile(
    title:    str,
    location: str  = "Israel",
    limit:    int  = 40,
) -> list[dict]:
    """
    Fetch jobs from all sources for a given profile.
    JSearch is primary for Israel; Adzuna is secondary.
    """
    # Run both in parallel
    jsearch_task = fetch_jsearch_jobs(
        title=title,
        location=location,
        pages=2,
        max_jobs=35,
    )
    adzuna_task = fetch_adzuna_jobs(title, location, limit=15)

    jsearch_jobs, adzuna_jobs = await asyncio.gather(
        jsearch_task, adzuna_task, return_exceptions=True
    )

    all_jobs = []
    if isinstance(jsearch_jobs, list):
        all_jobs.extend(jsearch_jobs)
    if isinstance(adzuna_jobs, list):
        all_jobs.extend(adzuna_jobs)

    return all_jobs[:limit]
