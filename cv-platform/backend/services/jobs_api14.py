import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

_BASE = "https://jobs-api14.p.rapidapi.com/v2/list"
_HEADERS = {
    "x-rapidapi-host": "jobs-api14.p.rapidapi.com",
}

_SEARCH_QUERIES = [
    ("Israel", "LinkedIn"),
    ("Tel Aviv", "LinkedIn"),
    ("Israel", "Indeed"),
    ("Tel Aviv", "Indeed"),
]


def _parse(item: dict, source_label: str) -> dict:
    return {
        "external_id": f"jobsapi14_{item.get('id') or item.get('url', '')[-40:]}",
        "source": f"jobsapi14_{source_label.lower()}",
        "title": item.get("title"),
        "company": item.get("company"),
        "location": item.get("location"),
        "description": (item.get("description") or "")[:1500],
        "apply_url": item.get("url"),
        "salary_min": None,
        "salary_max": None,
    }


async def fetch_jobs_api14(title: str, location: str = "Israel") -> list[dict]:
    if not settings.JOBS_API14_KEY:
        return []

    headers = {**_HEADERS, "x-rapidapi-key": settings.JOBS_API14_KEY}
    jobs: list[dict] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(timeout=15) as client:
        for loc, provider in _SEARCH_QUERIES:
            params = {
                "query": f"{title} in {loc}",
                "location": loc,
                "autoTranslateLocation": "false",
                "remoteOnly": "false",
                "employmentTypes": "fulltime;parttime;intern;contractor",
            }
            try:
                resp = await client.get(_BASE, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
            except httpx.TimeoutException:
                logger.warning("jobs-api14 timeout for query=%r provider=%s", title, provider)
                continue
            except httpx.HTTPStatusError as exc:
                logger.warning("jobs-api14 HTTP %s for query=%r", exc.response.status_code, title)
                continue
            except Exception:
                logger.exception("jobs-api14 unexpected error for query=%r", title)
                continue

            for item in data.get("jobs", []):
                parsed = _parse(item, provider)
                eid = parsed["external_id"]
                if eid not in seen_ids:
                    seen_ids.add(eid)
                    jobs.append(parsed)

    return jobs
