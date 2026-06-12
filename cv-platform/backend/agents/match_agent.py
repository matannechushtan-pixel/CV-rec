import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from agents.cv_agent import gap_analysis, _extract_json
from core.ai_providers import claude_generate, gpt_generate, OPENAI_AVAILABLE
from models.cv import CV
from models.job import JobListing

logger = logging.getLogger(__name__)


async def score_cv_against_job(cv_id: str, job_id: str, db: AsyncSession) -> dict:
    cv_row = await db.get(CV, cv_id)
    job_row = await db.get(JobListing, job_id)

    if not cv_row or not job_row:
        raise ValueError("CV or job not found")

    if cv_row.embedding is None or job_row.embedding is None:
        return {"vector_score": 0.0, "match_percentage": 0}

    result = await db.execute(
        text(
            "SELECT 1 - ((:cv_emb)::vector <=> (:job_emb)::vector) AS similarity"
        ),
        {"cv_emb": str(cv_row.embedding), "job_emb": str(job_row.embedding)},
    )
    vector_score: float = result.scalar() or 0.0

    if vector_score > 0.5 and cv_row.raw_text and job_row.description:
        detailed = await gap_analysis(cv_row.raw_text, job_row.description)
        return {
            "vector_score": round(vector_score, 4),
            "match_percentage": detailed.get("match_percentage", round(vector_score * 100)),
            "strong_matches": detailed.get("strong_matches", []),
            "gaps": detailed.get("gaps", []),
        }

    return {
        "vector_score": round(vector_score, 4),
        "match_percentage": round(vector_score * 100),
    }


# ── GPT-4o-mini: classification, scoring, embeddings ─────────────────────────
# GPT is used here because it gives reliable structured JSON output, is fast,
# and is cheap enough for the high-volume scoring/classification calls below.

_FIT_PROMPT = """
You are a career advisor. Evaluate how good a fit this candidate is for the job below
before they spend time tailoring a CV or writing a cover letter.

Return ONLY valid JSON, no markdown:
{{
  "score": 0,
  "recommendation": "apply" | "stretch" | "skip",
  "reasons": ["short reason 1", "short reason 2"]
}}

Guidance:
- score >= 70 -> "apply"
- score 40-69 -> "stretch"
- score < 40 -> "skip"
- Give 2-4 concise reasons referencing specific skills/experience.

JOB DESCRIPTION:
{job_description}

CANDIDATE CV:
{cv_text}
"""


async def evaluate_fit(cv_text: str, job_description: str) -> dict:
    """Score how well a CV fits a job (GPT-4o-mini: reliable structured JSON, consistent scoring)."""
    prompt = _FIT_PROMPT.format(job_description=job_description, cv_text=cv_text)

    try:
        if OPENAI_AVAILABLE:
            raw = await gpt_generate(prompt, max_tokens=512)
        else:
            raw = await claude_generate(prompt, max_tokens=512)
        data = _extract_json(raw)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("evaluate_fit failed (%s), returning safe default", e)
        return {"score": 0, "recommendation": "skip", "reasons": ["Could not evaluate fit."]}

    score = int(data.get("score", 0))
    recommendation = data.get("recommendation") or (
        "apply" if score >= 70 else "stretch" if score >= 40 else "skip"
    )
    return {
        "score": score,
        "recommendation": recommendation,
        "reasons": data.get("reasons", []),
    }


_EXTRACT_SKILLS_PROMPT = """
Extract the key skills, tools, technologies, and qualifications required by this job posting.

Return ONLY valid JSON, no markdown:
{{
  "skills": ["skill1", "skill2", "..."]
}}

JOB DESCRIPTION:
{job_description}
"""


async def extract_skills(job_description: str) -> list[str]:
    """Extract required skills from a job description (GPT-4o-mini: fast, cheap extraction)."""
    prompt = _EXTRACT_SKILLS_PROMPT.format(job_description=job_description)

    try:
        if OPENAI_AVAILABLE:
            raw = await gpt_generate(prompt, max_tokens=512)
        else:
            raw = await claude_generate(prompt, max_tokens=512)
        data = _extract_json(raw)
        skills = data.get("skills", [])
        return [s for s in skills if isinstance(s, str)]
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("extract_skills failed (%s), returning empty list", e)
        return []


_SCORE_MATCH_PROMPT = """
Score how well this candidate's CV matches the job listing below, on a scale of 0-100.

Return ONLY valid JSON, no markdown:
{{
  "match_percentage": 0
}}

CANDIDATE CV:
{cv_text}

JOB LISTING:
{job_text}
"""


async def score_job_match(cv_json: dict, job: dict) -> int:
    """Score a CV against a job listing (GPT-4o-mini: low cost + consistency for high volume)."""
    cv_text = json.dumps(cv_json, ensure_ascii=False)
    job_text = json.dumps(job, ensure_ascii=False)
    prompt = _SCORE_MATCH_PROMPT.format(cv_text=cv_text, job_text=job_text)

    try:
        if OPENAI_AVAILABLE:
            raw = await gpt_generate(prompt, max_tokens=256)
        else:
            raw = await claude_generate(prompt, max_tokens=256)
        data = _extract_json(raw)
        return int(data.get("match_percentage", 0))
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("score_job_match failed (%s), returning 0", e)
        return 0
