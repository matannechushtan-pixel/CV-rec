import logging
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

_API = "https://discord.com/api/v10"
_OAUTH_TOKEN_URL = "https://discord.com/api/v10/oauth2/token"
_OAUTH_ME_URL = "https://discord.com/api/v10/users/@me"


async def exchange_code(code: str, redirect_uri: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _OAUTH_TOKEN_URL,
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_discord_user(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _OAUTH_ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def send_jobs_embed(channel_id: str, jobs: list[dict], target_role: str) -> bool:
    if not settings.DISCORD_BOT_TOKEN:
        logger.warning("DISCORD_BOT_TOKEN not set — skipping notification")
        return False

    if not jobs:
        return True

    lines = [f"**Daily Job Matches for: {target_role}**\n"]
    for i, job in enumerate(jobs[:10], 1):
        title = job.get("title", "Untitled")
        company = job.get("company", "Unknown")
        location = job.get("location", "")
        apply_url = job.get("apply_url", "")
        salary = ""
        if job.get("salary_min") and job.get("salary_max"):
            salary = f" · ${job['salary_min']:,}–${job['salary_max']:,}"

        line = f"**{i}. {title}** — {company}"
        if location:
            line += f" · {location}"
        line += salary
        if apply_url:
            line += f"\n   [Apply](<{apply_url}>)"
        lines.append(line)

    content = "\n\n".join(lines)
    if len(content) > 2000:
        content = content[:1997] + "..."

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(
                f"{_API}/channels/{channel_id}/messages",
                headers={
                    "Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={"content": content},
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            logger.error("Discord send failed for channel %s: %s", channel_id, e.response.text)
            return False
        except Exception as e:
            logger.error("Discord send error for channel %s: %s", channel_id, e)
            return False


def bot_invite_url() -> str:
    return (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&permissions=2048"
        f"&scope=bot"
    )
