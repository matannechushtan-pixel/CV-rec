"""Central registry for AI provider clients and model-specific helpers.

Smart multi-brain architecture — each model is used for what it does best:

  - Gemini 2.0 Flash : CV writing, translation, cover letters (gemini_generate)
  - Claude Sonnet    : analysis, coaching, deep reasoning   (claude_generate)
  - GPT-4o-mini      : classification, scoring, embeddings  (gpt_generate)

Anthropic is always configured (required for core CV/roadmap/interview agents).
OpenAI and Gemini are optional — when their API keys are not set, the
corresponding helpers raise ``RuntimeError`` (or return ``None`` clients), and
calling code can fall back to Claude so the app keeps working with a single key.
"""

import asyncio
import logging

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from google import genai as _genai

from core.config import settings

logger = logging.getLogger(__name__)

# ── Clients ────────────────────────────────────────────────────────────────
anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

OPENAI_AVAILABLE = bool(settings.OPENAI_API_KEY)
GEMINI_AVAILABLE = bool(settings.GEMINI_API_KEY)

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if OPENAI_AVAILABLE else None
gemini_client = _genai.Client(api_key=settings.GEMINI_API_KEY) if GEMINI_AVAILABLE else None

# Legacy alias (kept for existing call sites)
genai_client = gemini_client


def get_gemini() -> "_genai.Client | None":
    """Return the Gemini client, or None if GEMINI_API_KEY is unset."""
    return gemini_client


# ── Gemini helper ────────────────────────────────────────────────────────────
async def gemini_generate(prompt: str, model: str = "gemini-2.0-flash") -> str:
    """Run a Gemini generation call in a thread pool (google-genai SDK is sync-only).

    Raises RuntimeError if GEMINI_API_KEY is not set.
    """
    if not gemini_client:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to backend/.env to enable CV generation."
        )
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: gemini_client.models.generate_content(model=model, contents=prompt),
    )
    return response.text


# ── Claude helper ────────────────────────────────────────────────────────────
async def claude_generate(
    prompt: str,
    system: str = "",
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 2048,
) -> str:
    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    if system:
        kwargs["system"] = system
    msg = await anthropic_client.messages.create(**kwargs)
    return msg.content[0].text


# ── GPT helper ───────────────────────────────────────────────────────────────
async def gpt_generate(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 1024) -> str:
    if not openai_client:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    resp = await openai_client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content
