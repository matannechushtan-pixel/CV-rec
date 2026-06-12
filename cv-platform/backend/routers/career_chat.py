import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.auth import get_current_user
from core.database import get_db
from agents.career_coach_agent import chat_stream
from models.cv import CV
from models.application import Application
from routers.applications import ApplicationStats

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class CareerChatRequest(BaseModel):
    messages: list[ChatMessage]
    cv_id: str | None = None


@router.post("/career-chat/stream")
async def career_chat_stream(
    body: CareerChatRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.messages:
        raise HTTPException(status_code=400, detail="messages is required")

    user_id = uuid.UUID(user["id"])

    cv_context = None
    if body.cv_id:
        try:
            cv_uuid = uuid.UUID(body.cv_id)
        except ValueError:
            cv_uuid = None
        if cv_uuid:
            result = await db.execute(select(CV).where(CV.id == cv_uuid, CV.user_id == user_id))
            cv = result.scalar_one_or_none()
            if cv and cv.structured_data:
                cv_context = cv.structured_data

    applications_context = await _build_applications_context(db, user_id)

    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    async def event_stream():
        async for text in chat_stream(messages, cv_context, applications_context):
            yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def _build_applications_context(db: AsyncSession, user_id: uuid.UUID) -> str | None:
    result = await db.execute(
        select(Application)
        .where(Application.user_id == user_id)
        .options(selectinload(Application.job_listing))
        .order_by(Application.applied_at.desc())
        .limit(10)
    )
    applications = result.scalars().all()
    if not applications:
        return None

    counts = ApplicationStats()
    result = await db.execute(select(Application.status).where(Application.user_id == user_id))
    for (status,) in result.all():
        if hasattr(counts, status):
            setattr(counts, status, getattr(counts, status) + 1)

    total = counts.applied + counts.viewed + counts.interview + counts.rejected + counts.offer
    lines = [
        f"Total applications: {total} "
        f"(applied/viewed: {counts.applied + counts.viewed}, "
        f"interviews: {counts.interview}, offers: {counts.offer}, rejected: {counts.rejected})",
        "Recent applications:",
    ]
    for app in applications:
        job = app.job_listing
        title = job.title if job else "Unknown role"
        company = job.company if job else "Unknown company"
        lines.append(f"- {title} at {company} — status: {app.status}")

    return "\n".join(lines)
