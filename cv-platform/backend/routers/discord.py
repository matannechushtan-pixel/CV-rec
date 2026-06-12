import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.auth import get_current_user, require_job_seeker
from core.config import settings
from core.database import get_db
from models.discord import DiscordConnection
from services.discord_service import exchange_code, get_discord_user, bot_invite_url

router = APIRouter()
logger = logging.getLogger(__name__)

_REDIRECT_URI = "http://localhost:3000/auth/discord/callback"
_SCOPES = "identify"


class SetupRequest(BaseModel):
    channel_id: str
    guild_id: str | None = None


class DiscordStatusOut(BaseModel):
    connected: bool
    discord_username: str | None = None
    channel_id: str | None = None
    guild_id: str | None = None
    is_active: bool = False
    bot_invite_url: str


@router.get("/connect")
async def discord_connect():
    url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={_SCOPES}"
    )
    return {"url": url}


@router.get("/callback")
async def discord_callback(
    code: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        token_data = await exchange_code(code, _REDIRECT_URI)
        discord_user = await get_discord_user(token_data["access_token"])
    except Exception as e:
        logger.error("Discord OAuth exchange failed: %s", e)
        raise HTTPException(status_code=400, detail="Discord OAuth failed")

    user_id = uuid.UUID(user["id"])
    discord_user_id = str(discord_user["id"])
    discord_username = discord_user.get("username") or discord_user.get("global_name")

    result = await db.execute(
        select(DiscordConnection).where(DiscordConnection.user_id == user_id)
    )
    conn = result.scalar_one_or_none()

    if conn:
        conn.discord_user_id = discord_user_id
        conn.discord_username = discord_username
        conn.is_active = True
    else:
        conn = DiscordConnection(
            user_id=user_id,
            discord_user_id=discord_user_id,
            discord_username=discord_username,
        )
        db.add(conn)

    await db.flush()
    return {"discord_username": discord_username}


@router.post("/setup")
async def discord_setup(
    body: SetupRequest,
    user: dict = Depends(require_job_seeker),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    result = await db.execute(
        select(DiscordConnection).where(DiscordConnection.user_id == user_id)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connect Discord first")

    conn.channel_id = body.channel_id
    conn.guild_id = body.guild_id
    conn.is_active = True
    await db.flush()
    return {"ok": True}


@router.get("/status", response_model=DiscordStatusOut)
async def discord_status(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    result = await db.execute(
        select(DiscordConnection).where(DiscordConnection.user_id == user_id)
    )
    conn = result.scalar_one_or_none()
    return DiscordStatusOut(
        connected=conn is not None,
        discord_username=conn.discord_username if conn else None,
        channel_id=conn.channel_id if conn else None,
        guild_id=conn.guild_id if conn else None,
        is_active=conn.is_active if conn else False,
        bot_invite_url=bot_invite_url(),
    )


@router.delete("/disconnect")
async def discord_disconnect(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(user["id"])
    result = await db.execute(
        select(DiscordConnection).where(DiscordConnection.user_id == user_id)
    )
    conn = result.scalar_one_or_none()
    if conn:
        await db.delete(conn)
    return {"ok": True}
