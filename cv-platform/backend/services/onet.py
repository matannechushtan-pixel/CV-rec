import httpx
from core.config import settings

_BASE = "https://services.onetcenter.org/ws"


async def get_onet_occupation_data(occupation_title: str) -> dict:
    if not settings.ONET_USERNAME or not settings.ONET_PASSWORD:
        return {"note": "O*NET credentials not configured"}

    auth = (settings.ONET_USERNAME, settings.ONET_PASSWORD)

    try:
        async with httpx.AsyncClient(timeout=15, auth=auth) as client:
            search = await client.get(
                f"{_BASE}/search/",
                params={"keyword": occupation_title, "start": 1, "end": 1},
                headers={"Accept": "application/json"},
            )
            search.raise_for_status()
            results = search.json()

            occupations = results.get("occupation", [])
            if not occupations:
                return {"note": f"No O*NET match for: {occupation_title}"}

            code = occupations[0]["code"]
            skills_resp = await client.get(
                f"{_BASE}/occupations/{code}/skills/",
                headers={"Accept": "application/json"},
            )
            skills_resp.raise_for_status()
    except httpx.HTTPError:
        return {"note": "O*NET data unavailable"}

    return {"occupation": occupations[0], "skills": skills_resp.json()}
