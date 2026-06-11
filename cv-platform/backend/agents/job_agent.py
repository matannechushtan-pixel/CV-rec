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


async def fetch_jobs_for_profile(title: str, location: str, limit: int = 20) -> list[dict]:
    adzuna = await fetch_adzuna_jobs(title, location, limit)
    jsearch = await fetch_jsearch_jobs(title, location, limit)
    return adzuna + jsearch
