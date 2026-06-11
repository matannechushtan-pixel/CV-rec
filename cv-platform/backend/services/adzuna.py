import httpx
from core.config import settings

_BASE = "https://api.adzuna.com/v1/api/jobs"


async def fetch_adzuna_jobs(
    title: str,
    location: str,
    results_per_page: int = 20,
    country: str = "us",
) -> list[dict]:
    if not settings.ADZUNA_APP_ID or not settings.ADZUNA_APP_KEY:
        return []

    params = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "what": title,
        "where": location,
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{_BASE}/{country}/search/1", params=params)
        resp.raise_for_status()
        data = resp.json()

    jobs = []
    for item in data.get("results", []):
        jobs.append(
            {
                "external_id": f"adzuna_{item['id']}",
                "source": "adzuna",
                "title": item.get("title"),
                "company": item.get("company", {}).get("display_name"),
                "location": item.get("location", {}).get("display_name"),
                "description": item.get("description"),
                "apply_url": item.get("redirect_url"),
                "salary_min": item.get("salary_min"),
                "salary_max": item.get("salary_max"),
            }
        )
    return jobs
