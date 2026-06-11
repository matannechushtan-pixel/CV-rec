from core.ai_providers import openai_client, OPENAI_AVAILABLE


def _cv_embed_text(structured_data: dict) -> str:
    """Build a focused string from parsed CV data for embedding."""
    parts: list[str] = []
    if structured_data.get("summary"):
        parts.append(structured_data["summary"])
    for exp in structured_data.get("experience", []):
        parts.append(f"{exp.get('title', '')} at {exp.get('company', '')}")
    parts.extend(structured_data.get("skills", []))
    return " | ".join(filter(None, parts))


async def embed_text(text: str) -> list[float] | None:
    """Embed text with OpenAI text-embedding-3-small.

    Returns None when OPENAI_API_KEY is not configured — callers should
    treat embeddings as an optional enhancement and fall back to
    keyword-based matching.
    """
    if not OPENAI_AVAILABLE:
        return None

    resp = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
    )
    return resp.data[0].embedding


async def embed_cv(structured_data: dict) -> list[float] | None:
    return await embed_text(_cv_embed_text(structured_data))


async def embed_job(title: str, description: str, required_skills: list[str]) -> list[float] | None:
    text = f"{title} | {' | '.join(required_skills)} | {description[:500]}"
    return await embed_text(text)
