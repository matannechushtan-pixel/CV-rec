import asyncio
import json
import logging

from core.ai_providers import claude_generate, gemini_generate, gpt_generate

logger = logging.getLogger(__name__)


_SUMMARY_PROMPT = """You are an expert CV writer. Write a compelling professional summary
(2-4 sentences) for the candidate described by the CV data below.

Rules:
- Highlight their strongest skills and experience
- Be specific, avoid generic phrases like "hardworking team player"
- Return ONLY the summary text, no quotes, no markdown, no labels

CV DATA:
{cv_str}
"""


async def brainstorm_cv_summary(cv_data: dict) -> dict:
    """Generate 3 alternative professional summaries, one per model, for the user to compare."""
    cv_str = json.dumps(cv_data, ensure_ascii=False)
    prompt = _SUMMARY_PROMPT.format(cv_str=cv_str)

    gemini_result, claude_result, gpt_result = await asyncio.gather(
        gemini_generate(prompt),
        claude_generate(prompt, max_tokens=300),
        gpt_generate(prompt, max_tokens=300),
        return_exceptions=True,
    )

    def _clean(result, label):
        if isinstance(result, Exception):
            logger.warning("brainstorm_cv_summary: %s failed (%s)", label, result)
            return None
        return result.strip().strip('"')

    return {
        "gemini": _clean(gemini_result, "gemini"),
        "claude": _clean(claude_result, "claude"),
        "gpt": _clean(gpt_result, "gpt"),
    }


_JOB_FIT_PROMPT = """You are a career advisor. Given the candidate's CV and the list of job
listings below, rank the jobs from best fit to worst fit for this candidate.

Return ONLY valid JSON, no markdown:
{{
  "ranking": [
    {{"job_id": "", "rank": 1, "reason": "short reason"}}
  ]
}}

CANDIDATE CV:
{cv_str}

JOB LISTINGS:
{jobs_str}
"""


async def brainstorm_job_fit(cv_data: dict, jobs: list[dict]) -> dict:
    """Get job-fit rankings from all 3 models in parallel, for side-by-side comparison."""
    cv_str = json.dumps(cv_data, ensure_ascii=False)
    jobs_str = json.dumps(jobs, ensure_ascii=False)
    prompt = _JOB_FIT_PROMPT.format(cv_str=cv_str, jobs_str=jobs_str)

    gemini_result, claude_result, gpt_result = await asyncio.gather(
        gemini_generate(prompt),
        claude_generate(prompt, max_tokens=1024),
        gpt_generate(prompt, max_tokens=1024),
        return_exceptions=True,
    )

    def _parse(result, label):
        if isinstance(result, Exception):
            logger.warning("brainstorm_job_fit: %s failed (%s)", label, result)
            return None
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            return json.loads(cleaned).get("ranking", [])
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning("brainstorm_job_fit: %s returned invalid JSON (%s)", label, e)
            return None

    return {
        "gemini": _parse(gemini_result, "gemini"),
        "claude": _parse(claude_result, "claude"),
        "gpt": _parse(gpt_result, "gpt"),
    }


_CAREER_PATHS_PROMPT = """You are a career advisor. Based on the candidate's CV below,
suggest 3-5 realistic career paths/roles this person could pursue next.

Return ONLY valid JSON, no markdown:
{{
  "suggestions": [
    {{"role": "job title", "reason": "why this fits their background"}}
  ]
}}

CANDIDATE CV:
{cv_str}
"""


async def brainstorm_career_paths(cv_data: dict) -> dict:
    """Get career-path suggestions from all 3 models, then merge into a voted list."""
    cv_str = json.dumps(cv_data, ensure_ascii=False)
    prompt = _CAREER_PATHS_PROMPT.format(cv_str=cv_str)

    gemini_result, claude_result, gpt_result = await asyncio.gather(
        gemini_generate(prompt),
        claude_generate(prompt, max_tokens=1024),
        gpt_generate(prompt, max_tokens=1024),
        return_exceptions=True,
    )

    def _parse(result, label):
        if isinstance(result, Exception):
            logger.warning("brainstorm_career_paths: %s failed (%s)", label, result)
            return []
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            return json.loads(cleaned).get("suggestions", [])
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning("brainstorm_career_paths: %s returned invalid JSON (%s)", label, e)
            return []

    per_model = {
        "gemini": _parse(gemini_result, "gemini"),
        "claude": _parse(claude_result, "claude"),
        "gpt": _parse(gpt_result, "gpt"),
    }

    # Merge suggestions across models, voting by role name (case-insensitive)
    merged: dict[str, dict] = {}
    for model, suggestions in per_model.items():
        for s in suggestions:
            role = s.get("role", "").strip()
            if not role:
                continue
            key = role.lower()
            if key not in merged:
                merged[key] = {"role": role, "reasons": [], "votes": 0, "models": []}
            merged[key]["votes"] += 1
            merged[key]["models"].append(model)
            reason = s.get("reason", "")
            if reason:
                merged[key]["reasons"].append(reason)

    merged_list = sorted(merged.values(), key=lambda x: x["votes"], reverse=True)

    return {
        "per_model": per_model,
        "merged": merged_list,
    }
