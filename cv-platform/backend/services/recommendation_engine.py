"""Job recommendation engine.

Scores live job listings against a candidate's parsed CV. When
OPENAI_API_KEY is configured, scoring uses text-embedding-3-small +
cosine similarity, with a small relevance boost from the synthetic CV
dataset's "preferred roles" for the most similar synthetic profile.
Without an OpenAI key, falls back to keyword-overlap scoring so the
feature still works.
"""

import json
import math
import re
from pathlib import Path

from services.embeddings import embed_text

_SYNTHETIC_PATH = Path(__file__).parent.parent / "data" / "synthetic_cvs.json"
_synthetic_profiles: list[dict] = json.loads(_SYNTHETIC_PATH.read_text())
_synthetic_embeddings_cache: dict[str, list[float]] = {}


def _cv_query_text(cv_json: dict) -> str:
    title = ""
    experience = cv_json.get("experience") or []
    if experience:
        title = experience[0].get("title", "")
    skills = cv_json.get("skills") or []
    return f"{title} | {' | '.join(skills)}"


def _job_text(job: dict) -> str:
    return f"{job.get('title') or ''} {job.get('description') or ''}"


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z+#.]*")


def _keyword_overlap_score(cv_json: dict, job: dict) -> float:
    skills = {s.lower() for s in (cv_json.get("skills") or [])}
    job_words = {w.lower() for w in _WORD_RE.findall(_job_text(job))}
    if not skills:
        return 0.0
    overlap = sum(1 for s in skills if s.lower() in job_words)
    return overlap / len(skills)


async def _ensure_synthetic_embeddings() -> None:
    if _synthetic_embeddings_cache:
        return
    for profile in _synthetic_profiles:
        text = f"{profile['title']} | {' | '.join(profile['skills'])}"
        embedding = await embed_text(text)
        if embedding is not None:
            _synthetic_embeddings_cache[profile["id"]] = embedding


async def _nearest_synthetic_profile(cv_embedding: list[float]) -> dict | None:
    await _ensure_synthetic_embeddings()
    if not _synthetic_embeddings_cache:
        return None

    best_id, best_score = None, -1.0
    for profile_id, embedding in _synthetic_embeddings_cache.items():
        score = _cosine_similarity(cv_embedding, embedding)
        if score > best_score:
            best_id, best_score = profile_id, score

    return next((p for p in _synthetic_profiles if p["id"] == best_id), None)


async def recommend_jobs(cv_json: dict, jobs: list[dict], top_n: int = 10) -> list[dict]:
    """Return the top_n jobs ranked by relevance to the candidate's CV.

    Each returned dict is the original job with an added "match_score" (0-100).
    """
    cv_embedding = await embed_text(_cv_query_text(cv_json))

    if cv_embedding is not None:
        nearest = await _nearest_synthetic_profile(cv_embedding)
        boost_roles = {r.lower() for r in (nearest or {}).get("preferred_roles", [])}

        scored = []
        for job in jobs:
            job_embedding = await embed_text(_job_text(job))
            score = _cosine_similarity(cv_embedding, job_embedding) if job_embedding else 0.0
            if (job.get("title") or "").lower() in boost_roles:
                score = min(1.0, score + 0.05)
            scored.append((score, job))
    else:
        scored = [(_keyword_overlap_score(cv_json, job), job) for job in jobs]

    scored.sort(key=lambda pair: pair[0], reverse=True)

    results = []
    for score, job in scored[:top_n]:
        results.append({**job, "match_score": round(score * 100)})
    return results
