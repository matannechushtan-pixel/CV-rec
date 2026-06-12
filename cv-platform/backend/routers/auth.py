import logging
import uuid
from threading import Lock

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from supabase import create_client, Client

from core.config import settings
from core.database import get_db
from core.auth import get_current_user
from models.user import User, Profile

router = APIRouter()
logger = logging.getLogger(__name__)

_supabase_lock = Lock()
_supabase_client: Client | None = None


def get_supabase() -> Client:
    global _supabase_client
    with _supabase_lock:
        if _supabase_client is None:
            _supabase_client = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
            )
    return _supabase_client


def reset_supabase():
    global _supabase_client
    with _supabase_lock:
        _supabase_client = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # job_seeker | company_admin
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OAuthSyncRequest(BaseModel):
    role: str | None = None


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if body.role not in ("job_seeker", "company_admin"):
        raise HTTPException(status_code=400, detail="role must be job_seeker or company_admin")

    try:
        res = get_supabase().auth.admin.create_user(
            {
                "email": body.email,
                "password": body.password,
                "email_confirm": True,
                "user_metadata": {"role": body.role},
            }
        )
    except Exception as e:
        reset_supabase()
        logger.error("Supabase error during register: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

    supabase_id = uuid.UUID(res.user.id)
    user = User(id=supabase_id, email=body.email, role=body.role)
    db.add(user)

    if body.role == "job_seeker":
        db.add(Profile(user_id=supabase_id, full_name=body.full_name))

    await db.flush()

    try:
        sign_in = get_supabase().auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception as e:
        reset_supabase()
        logger.error("Supabase error during post-register sign-in: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "access_token": sign_in.session.access_token,
        "refresh_token": sign_in.session.refresh_token,
        "user": {"id": str(supabase_id), "email": user.email, "role": user.role},
    }


@router.post("/login")
async def login(body: LoginRequest):
    try:
        res = get_supabase().auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception as e:
        reset_supabase()
        logger.error("Supabase error during login: %s", e, exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "user": {
            "id": res.user.id,
            "email": res.user.email,
            "role": res.user.user_metadata.get("role"),
        },
    }


@router.post("/oauth/sync")
async def oauth_sync(
    body: OAuthSyncRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()

    if not db_user:
        metadata = user.get("user_metadata", {})
        candidate_role = body.role or metadata.get("role")
        role = candidate_role if candidate_role in ("job_seeker", "company_admin") else "job_seeker"
        db_user = User(id=user_id, email=user["email"], role=role)
        db.add(db_user)

        if role == "job_seeker":
            full_name = metadata.get("full_name") or metadata.get("name")
            db.add(Profile(user_id=user_id, full_name=full_name))

        await db.flush()

    return {"id": str(db_user.id), "email": db_user.email, "role": db_user.role}


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    return {"message": "Logged out"}


@router.get("/me")
async def me(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user["email"]))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(db_user.id), "email": db_user.email, "role": db_user.role}
