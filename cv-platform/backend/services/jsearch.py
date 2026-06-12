import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

_BASE = "https://jsearch.p.rapidapi.com/search"

# ── In-memory TTL cache ──────────────────────────────────────────
_CACHE: dict[str, tuple[float, list[dict]]] = {}
_CACHE_TTL = 60 * 60 * 3  # 3 hours


def _cache_key(query: str, page: int) -> str:
    raw = f"{query}|{page}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> list[dict] | None:
    entry = _CACHE.get(key)
    if entry is None:
        return None
    timestamp, jobs = entry
    if time.time() - timestamp > _CACHE_TTL:
        _CACHE.pop(key, None)
        return None
    return jobs


def _cache_set(key: str, jobs: list[dict]) -> None:
    _CACHE[key] = (time.time(), jobs)


def cache_stats() -> dict:
    now = time.time()
    valid = sum(
        1 for timestamp, _ in _CACHE.values() if now - timestamp <= _CACHE_TTL
    )
    return {
        "total": len(_CACHE),
        "valid": valid,
        "ttl_hours": _CACHE_TTL // 3600,
    }


# ── Hebrew job-title translations ────────────────────────────────
_HE_TITLES = {
    "software engineer": "מהנדס תוכנה",
    "software developer": "מפתח תוכנה",
    "data scientist": "מדען נתונים",
    "data analyst": "אנליסט נתונים",
    "data engineer": "מהנדס נתונים",
    "machine learning engineer": "מהנדס למידת מכונה",
    "backend developer": "מפתח backend",
    "frontend developer": "מפתח frontend",
    "full stack developer": "מפתח full stack",
    "fullstack developer": "מפתח full stack",
    "devops engineer": "מהנדס דבאופס",
    "product manager": "מנהל מוצר",
    "project manager": "מנהל פרויקטים",
    "qa engineer": "מהנדס בדיקות",
    "quality assurance engineer": "מהנדס בדיקות",
    "ux designer": "מעצב חוויית משתמש",
    "ui designer": "מעצב ממשק משתמש",
    "ui/ux designer": "מעצב UX/UI",
    "system administrator": "מנהל מערכות",
    "network engineer": "מהנדס רשתות",
    "security engineer": "מהנדס אבטחת מידע",
    "cyber security analyst": "אנליסט אבטחת מידע",
    "business analyst": "אנליסט עסקי",
    "hr manager": "מנהל משאבי אנוש",
    "marketing manager": "מנהל שיווק",
    "sales manager": "מנהל מכירות",
    "accountant": "רואה חשבון",
    "financial analyst": "אנליסט פיננסי",
    "mobile developer": "מפתח מובייל",
    "android developer": "מפתח אנדרואיד",
    "ios developer": "מפתח iOS",
    "team lead": "ראש צוות",
}


def _get_hebrew_title(title: str) -> str | None:
    lowered = title.strip().lower()
    if lowered in _HE_TITLES:
        return _HE_TITLES[lowered]
    for key, value in _HE_TITLES.items():
        if key in lowered or lowered in key:
            return value
    return None


# ── Query builder ─────────────────────────────────────────────────
def build_queries(title: str, location: str = "Israel") -> list[str]:
    queries: list[str] = []

    queries.append(f"{title} in Israel")
    queries.append(f"{title} in Tel Aviv")
    queries.append(f"{title} jobs Israel")

    hebrew_title = _get_hebrew_title(title)
    if hebrew_title:
        queries.append(f"{hebrew_title} ישראל")
        queries.append(f"{hebrew_title} תל אביב")

    queries.append(f"remote {title} Israel")

    queries.append(f"{title} Herzliya OR Raanana OR Petah Tikva")

    queries.append(f"{title} Haifa OR Beer Sheva")

    if location and location.lower() not in ("israel", "tel aviv"):
        queries.append(f"{title} in {location}")

    queries.append(f"senior {title} Israel")
    queries.append(f"junior {title} Israel")

    # Deduplicate while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)

    return unique_queries


# ── Single-page fetch ──────────────────────────────────────────────
async def _fetch_one(client: httpx.AsyncClient, query: str, page: int = 1) -> list[dict]:
    key = _cache_key(query, page)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    if not settings.JSEARCH_API_KEY:
        return []

    params = {
        "query": query,
        "page": str(page),
        "num_pages": "1",
        "country": "il",
        "language": "en_GB",
        "date_posted": "month",
    }
    headers = {
        "X-RapidAPI-Key": settings.JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    try:
        resp = await client.get(_BASE, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        logger.warning("JSearch timeout for query=%r page=%s", query, page)
        return []
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "JSearch HTTP error %s for query=%r page=%s",
            exc.response.status_code, query, page,
        )
        return []
    except Exception:
        logger.exception("JSearch unexpected error for query=%r page=%s", query, page)
        return []

    jobs = _parse_results(data.get("data", []))
    _cache_set(key, jobs)
    return jobs


# ── Result parsing ──────────────────────────────────────────────────
def _parse_results(items: list[dict]) -> list[dict]:
    jobs = []
    for item in items:
        description = (item.get("job_description") or "")[:1500]

        location_parts = [
            p for p in (item.get("job_city"), item.get("job_country")) if p
        ]
        location = ", ".join(location_parts)

        jobs.append(
            {
                "external_id": f"jsearch_{item.get('job_id')}",
                "source": "jsearch",
                "title": item.get("job_title"),
                "company": item.get("employer_name"),
                "location": location,
                "description": description,
                "apply_url": item.get("job_apply_link"),
                "salary_min": item.get("job_min_salary"),
                "salary_max": item.get("job_max_salary"),
                "salary_currency": item.get("job_salary_currency"),
                "employment_type": item.get("job_employment_type"),
                "is_remote": bool(item.get("job_is_remote")),
                "posted_at": item.get("job_posted_at_datetime_utc"),
                "required_experience": item.get("job_required_experience"),
                "required_skills": item.get("job_required_skills"),
                "highlights": item.get("job_highlights"),
            }
        )
    return jobs


# ── Deduplication ─────────────────────────────────────────────────
def _deduplicate(jobs: list[dict]) -> list[dict]:
    seen_ids = set()
    seen_pairs = set()
    unique = []

    for job in jobs:
        external_id = job.get("external_id")
        pair = (
            (job.get("title") or "").strip().lower(),
            (job.get("company") or "").strip().lower(),
        )

        if external_id in seen_ids:
            continue
        if pair in seen_pairs:
            continue

        seen_ids.add(external_id)
        seen_pairs.add(pair)
        unique.append(job)

    return unique


# ── Relevance scoring ────────────────────────────────────────────
def relevance_score(job: dict) -> float:
    score = 0.0
    location = (job.get("location") or "").lower()

    if "israel" in location:
        score += 3.0

    israeli_cities = [
        "tel aviv", "jerusalem", "haifa", "herzliya", "raanana", "ra'anana",
        "petah tikva", "beer sheva", "be'er sheva", "ramat gan", "netanya",
        "rehovot", "holon", "bnei brak", "givatayim",
    ]
    for city in israeli_cities:
        if city in location:
            score += 2.0
            break

    if job.get("is_remote"):
        score += 1.0

    if job.get("salary_min") or job.get("salary_max"):
        score += 0.5

    if job.get("posted_at"):
        score += 0.25

    return score


# ── Public API ─────────────────────────────────────────────────────
async def fetch_jsearch_jobs(
    title: str,
    location: str = "Israel",
    pages: int = 2,
    max_jobs: int = 50,
) -> list[dict]:
    if not settings.JSEARCH_API_KEY:
        return []

    queries = build_queries(title, location)

    semaphore = asyncio.Semaphore(5)

    async def _bounded_fetch(client: httpx.AsyncClient, query: str, page: int) -> list[dict]:
        async with semaphore:
            return await _fetch_one(client, query, page)

    async with httpx.AsyncClient(timeout=15) as client:
        tasks = [
            _bounded_fetch(client, query, page)
            for query in queries
            for page in range(1, pages + 1)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: list[dict] = []
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)
        elif isinstance(result, Exception):
            logger.warning("JSearch fetch task failed: %s", result)

    unique = _deduplicate(all_jobs)
    unique.sort(key=relevance_score, reverse=True)

    return unique[:max_jobs]
