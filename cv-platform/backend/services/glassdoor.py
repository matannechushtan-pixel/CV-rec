import httpx
from core.config import settings


async def get_company_reviews(company_name: str) -> dict:
    """Glassdoor partner API — returns culture summary data."""
    if not settings.GLASSDOOR_PARTNER_ID or not settings.GLASSDOOR_KEY:
        return {}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://api.glassdoor.com/api/api.htm",
            params={
                "v": "1",
                "format": "json",
                "t.p": settings.GLASSDOOR_PARTNER_ID,
                "t.k": settings.GLASSDOOR_KEY,
                "action": "employers",
                "q": company_name,
                "ps": 1,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    employers = data.get("response", {}).get("employers", [])
    if not employers:
        return {}

    emp = employers[0]
    return {
        "name": emp.get("name"),
        "overall_rating": emp.get("overallRating"),
        "culture_rating": emp.get("cultureAndValuesRating"),
        "work_life_rating": emp.get("workLifeBalanceRating"),
        "featured_review": emp.get("featuredReview", {}).get("pros"),
    }
