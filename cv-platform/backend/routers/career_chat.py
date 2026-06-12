import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.auth import get_current_user
from core.database import get_db
from agents.career_coach_agent import chat_stream
from models.cv import CV

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

    cv_context = None
    if body.cv_id:
        try:
            cv_uuid = uuid.UUID(body.cv_id)
        except ValueError:
            cv_uuid = None
        if cv_uuid:
            result = await db.execute(
                select(CV).where(CV.id == cv_uuid, CV.user_id == uuid.UUID(user["id"]))
            )
            cv = result.scalar_one_or_none()
            if cv and cv.structured_data:
                cv_context = cv.structured_data

    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    async def event_stream():
        async for text in chat_stream(messages, cv_context):
            yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
