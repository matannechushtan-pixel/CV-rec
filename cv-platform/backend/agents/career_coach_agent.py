import json
from typing import AsyncIterator

from core.ai_providers import anthropic_client, claude_generate

SYSTEM_PROMPT = """You are an expert career coach and employment advisor with 20 years
of experience helping job seekers across many industries find roles that fit their
skills, experience, and goals.

Guidelines:
- Be warm, encouraging, and practical. Give specific, actionable advice rather than
  generic platitudes.
- When the user shares their CV or career goals, tailor your advice to their actual
  background — reference specific skills, roles, or experience they have.
- Help with: career planning, job search strategy, interview preparation, salary
  negotiation, CV/resume improvements, LinkedIn profiles, career transitions, and
  professional development.
- Keep responses focused and conversational — avoid overly long lists unless the
  user asks for a detailed breakdown.
- If you don't have enough information to give tailored advice, ask a clarifying
  question.
- Respond in the same language the user writes in (Hebrew or English).
"""


FOLLOW_UP_INSTRUCTION = """
At the end of your reply, ask exactly ONE focused follow-up question to keep the
conversation moving toward a concrete next step for the user's job search or career.
"""


def _build_system(cv_context: dict | None, applications_context: str | None = None) -> str:
    system = SYSTEM_PROMPT
    if cv_context:
        system += f"\n\nUser's current CV data:\n{json.dumps(cv_context, indent=2, ensure_ascii=False)}"
    if applications_context:
        system += f"\n\nUser's job application activity:\n{applications_context}"
    system += FOLLOW_UP_INSTRUCTION
    return system


async def chat(
    messages: list[dict], cv_context: dict | None = None, applications_context: str | None = None
) -> str:
    """Non-streaming career coach reply (Claude — empathy + nuanced reasoning)."""
    system = _build_system(cv_context, applications_context)
    if len(messages) == 1:
        return await claude_generate(messages[0]["content"], system=system, max_tokens=1024)

    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    return response.content[0].text


async def chat_stream(
    messages: list[dict], cv_context: dict | None = None, applications_context: str | None = None
) -> AsyncIterator[str]:
    """Streaming career coach reply (Claude — empathy + nuanced reasoning)."""
    system = _build_system(cv_context, applications_context)
    async with anthropic_client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text
