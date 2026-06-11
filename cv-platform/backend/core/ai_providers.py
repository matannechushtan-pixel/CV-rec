"""Central registry for AI provider clients.

Anthropic is always configured (required for core CV/roadmap/interview agents).
OpenAI and Gemini are optional — when their API keys are not set, the
corresponding helpers return ``None`` / report unavailable, and calling code
falls back to the Anthropic client so the app keeps working with a single key.
"""

import anthropic
from openai import AsyncOpenAI
import google.generativeai as genai

from core.config import settings

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

OPENAI_AVAILABLE = bool(settings.OPENAI_API_KEY)
GEMINI_AVAILABLE = bool(settings.GEMINI_API_KEY)

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if OPENAI_AVAILABLE else None

if GEMINI_AVAILABLE:
    genai.configure(api_key=settings.GEMINI_API_KEY)


def get_gemini(model: str = "gemini-2.0-flash"):
    """Return a Gemini GenerativeModel, or None if GEMINI_API_KEY is unset."""
    if not GEMINI_AVAILABLE:
        return None
    return genai.GenerativeModel(model)
