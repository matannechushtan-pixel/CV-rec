from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

from .config import settings

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": settings.SUPABASE_SERVICE_KEY,
            },
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return resp.json()


async def require_job_seeker(user: dict = Depends(get_current_user)) -> dict:
    if user.get("user_metadata", {}).get("role") != "job_seeker":
        raise HTTPException(status_code=403, detail="Job seekers only")
    return user


async def require_company_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("user_metadata", {}).get("role") != "company_admin":
        raise HTTPException(status_code=403, detail="Company admins only")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("user_metadata", {}).get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user
