"""Salary benchmarking.

Tries to derive a salary range from live Adzuna listings for the given job
title and location. If Adzuna has no salary data (no key configured, or no
listings with salary info), falls back to an AI estimate via Gemini (or
Anthropic if Gemini isn't configured), clearly marked as an estimate.
"""

import json

import httpx

from agents.cv_agent import _extract_json
from core.ai_providers import anthropic_client, get_gemini
from core.config import settings

_BASE = "https://api.adzuna.com/v1/api/jobs"

_ESTIMATE_PROMPT = """
Estimate a realistic annual salary range (in USD) for this role and location.
Return JSON only (no markdown):
{{
  "salary_min": 0,
  "salary_max": 0
}}

JOB TITLE: {job_title}
LOCATION: {location}
"""


async def _adzuna_salary_range(job_title: str, location: str, country: str = "us") -> dict | None:
    if not settings.ADZUNA_APP_ID or not settings.ADZUNA_APP_KEY:
        return None

    params = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "what": job_title,
        "where": location,
        "results_per_page": 50,
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{_BASE}/{country}/search/1", params=params)
        resp.raise_for_status()
        data = resp.json()

    mins, maxs = [], []
    for item in data.get("results", []):
        lo, hi = item.get("salary_min"), item.get("salary_max")
        if lo:
            mins.append(lo)
        if hi:
            maxs.append(hi)

    if not mins or not maxs:
        return None

    return {
        "salary_min": round(sum(mins) / len(mins)),
        "salary_max": round(sum(maxs) / len(maxs)),
        "currency": "USD",
        "source": "adzuna",
    }


async def _ai_salary_estimate(job_title: str, location: str) -> dict:
    prompt = _ESTIMATE_PROMPT.format(job_title=job_title, location=location)

    gemini = get_gemini()
    if gemini is not None:
        resp = await gemini.aio.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        data = _extract_json(resp.text)
    else:
        msg = await anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_json(msg.content[0].text)

    return {
        "salary_min": int(data.get("salary_min", 0)),
        "salary_max": int(data.get("salary_max", 0)),
        "currency": "USD",
        "source": "ai_estimate",
    }


async def get_salary_range(job_title: str, location: str) -> dict:
    try:
        adzuna_result = await _adzuna_salary_range(job_title, location)
    except Exception:
        adzuna_result = None

    if adzuna_result:
        return adzuna_result

    try:
        return await _ai_salary_estimate(job_title, location)
    except Exception:
        return {"salary_min": None, "salary_max": None, "currency": "USD", "source": "unavailable"}
