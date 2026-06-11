import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from agents.cv_agent import gap_analysis, _extract_json
from core.ai_providers import anthropic_client, openai_client, OPENAI_AVAILABLE
from models.cv import CV
from models.job import JobListing


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


_FIT_PROMPT = """
You are a career advisor. Evaluate how good a fit this candidate is for the job below
before they spend time tailoring a CV or writing a cover letter.

Return JSON only (no markdown):
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
    """Score how well a CV fits a job before generating tailored content (Task 7b)."""
    prompt = _FIT_PROMPT.format(job_description=job_description, cv_text=cv_text)

    if OPENAI_AVAILABLE:
        resp = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
    else:
        msg = await anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_json(msg.content[0].text)

    score = int(data.get("score", 0))
    recommendation = data.get("recommendation") or (
        "apply" if score >= 70 else "stretch" if score >= 40 else "skip"
    )
    return {
        "score": score,
        "recommendation": recommendation,
        "reasons": data.get("reasons", []),
    }
