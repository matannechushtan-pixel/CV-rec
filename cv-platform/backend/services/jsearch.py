import httpx
from core.config import settings

_BASE = "https://jsearch.p.rapidapi.com/search"


async def fetch_jsearch_jobs(title: str, location: str, num_pages: int = 1) -> list[dict]:
    if not settings.JSEARCH_API_KEY:
        return []

    params = {
        "query": f"{title} in {location}",
        "page": "1",
        "num_pages": str(num_pages),
    }
    headers = {
        "X-RapidAPI-Key": settings.JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(_BASE, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    jobs = []
    for item in data.get("data", []):
        jobs.append(
            {
                "external_id": f"jsearch_{item.get('job_id')}",
                "source": "jsearch",
                "title": item.get("job_title"),
                "company": item.get("employer_name"),
                "location": f"{item.get('job_city', '')}, {item.get('job_country', '')}",
                "description": item.get("job_description"),
                "apply_url": item.get("job_apply_link"),
                "salary_min": item.get("job_min_salary"),
                "salary_max": item.get("job_max_salary"),
            }
        )
    return jobs
