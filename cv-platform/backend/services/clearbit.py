import httpx
from core.config import settings


async def get_company_info(domain: str) -> dict:
    if not settings.CLEARBIT_API_KEY:
        return {}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"https://company.clearbit.com/v2/companies/find",
            params={"domain": domain},
            headers={"Authorization": f"Bearer {settings.CLEARBIT_API_KEY}"},
        )
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()
        data = resp.json()

    return {
        "name": data.get("name"),
        "description": data.get("description"),
        "industry": data.get("category", {}).get("industry"),
        "employees": data.get("metrics", {}).get("employees"),
        "logo": data.get("logo"),
    }
