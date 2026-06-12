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

import numpy as np

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


_DATA = Path(__file__).parent.parent / "data"

_profiles   = None
_embeddings = None
_index      = None


def _load_profiles():
    global _profiles, _embeddings, _index
    if _profiles is not None:
        return
    emb = _DATA / "cv_profile_embeddings.npy"
    idx = _DATA / "cv_embeddings_index.json"
    pro = _DATA / "all_cv_profiles.json"
    if not emb.exists():
        raise FileNotFoundError(
            "Run: python3 data/build_embeddings.py first"
        )
    _embeddings = np.load(emb)
    _index      = json.loads(idx.read_text())
    _profiles   = json.loads(pro.read_text())


def _cosine_sim(query: np.ndarray,
                matrix: np.ndarray) -> np.ndarray:
    q = query  / (np.linalg.norm(query)                      + 1e-10)
    m = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
    return m @ q


async def find_similar_cv_profiles(
    user_embedding: list[float],
    top_n: int = 5,
    source_filter: str | None = None,
) -> list[dict]:
    _load_profiles()
    query  = np.array(user_embedding, dtype=np.float32)
    scores = _cosine_sim(query, _embeddings)

    if source_filter:
        mask = np.array([
            1.0 if _index[i]["source"] == source_filter else 0.0
            for i in range(len(_index))
        ])
        scores = scores * mask

    top_idx = np.argsort(scores)[::-1][:top_n]
    return [
        {
            "id":         _index[i]["id"],
            "category":   _index[i]["category"],
            "source":     _index[i]["source"],
            "similarity": round(float(scores[i]), 4),
        }
        for i in top_idx
    ]


async def get_role_recommendations(
    user_embedding: list[float],
    top_n: int = 5,
) -> list[dict]:
    similar = await find_similar_cv_profiles(
        user_embedding, top_n=20
    )
    from collections import Counter
    cat_scores: dict[str, list[float]] = {}
    for p in similar:
        cat_scores.setdefault(p["category"], []).append(
            p["similarity"]
        )

    results = [
        {
            "role":          cat,
            "match_score":   round(
                sum(sims) / len(sims) * (1 + 0.1 * len(sims)), 3
            ),
            "profile_count": len(sims),
        }
        for cat, sims in cat_scores.items()
    ]
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_n]


# ── Job matching ─────────────────────────────────────────────

_job_embeddings      = None
_job_index           = None
_job_records         = None
_sp_embeddings       = None
_sp_records          = None


def _load_jobs():
    global _job_embeddings, _job_index, _job_records
    global _sp_embeddings, _sp_records
    if _job_embeddings is not None:
        return
    je = _DATA / "job_embeddings.npy"
    ji = _DATA / "job_embeddings_index.json"
    jr = _DATA / "jobs_clean.json"
    se = _DATA / "skill_profession_embeddings.npy"
    sr = _DATA / "skill_profession_map.json"

    if not je.exists():
        raise FileNotFoundError(
            "Run: python3 data/build_job_embeddings.py first"
        )
    _job_embeddings = np.load(je)
    _job_index      = json.loads(ji.read_text())
    _job_records    = json.loads(jr.read_text())
    _sp_embeddings  = np.load(se)
    _sp_records     = json.loads(sr.read_text())


async def match_cv_to_jobs(
    cv_embedding: list[float],
    top_n: int = 10,
) -> list[dict]:
    """Find the top N job postings that match a CV embedding.

    Returns job title, id, similarity score, and salary range.
    """
    _load_jobs()
    query  = np.array(cv_embedding, dtype=np.float32)
    scores = _cosine_sim(query, _job_embeddings)
    top_idx = np.argsort(scores)[::-1][:top_n]

    results = []
    for i in top_idx:
        job = _job_records[i]
        results.append({
            "job_id":     job["id"],
            "title":      job["title"],
            "location":   job.get("location", ""),
            "experience": job.get("experience_level", ""),
            "min_salary": job.get("min_salary"),
            "max_salary": job.get("max_salary"),
            "similarity": round(float(scores[i]), 4),
        })
    return results


async def match_cv_keywords_to_profession(
    keywords: dict,
) -> list[dict]:
    """Given Claude-extracted keywords from a CV, find the best
    matching professions using the skill→profession map.

    keywords: output of extract_cv_keywords()
    """
    _load_jobs()
    from openai import OpenAI as _OAI
    from dotenv import load_dotenv as _lde
    import os as _os
    _lde(_DATA.parent / ".env")
    oai = _OAI(api_key=_os.getenv("OPENAI_API_KEY"))

    # Build a search text from the keywords
    skills_str = ", ".join(keywords.get("core_skills", [])[:8])
    titles_str = ", ".join(keywords.get("job_titles_mentioned", [])[:3])
    query_text = (
        f"{keywords.get('search_query', '')} "
        f"Experience as: {titles_str}. "
        f"Skills: {skills_str}."
    )[:1000]

    # Embed the query
    resp = oai.embeddings.create(
        model="text-embedding-3-small",
        input=[query_text],
    )
    query_vec = np.array(resp.data[0].embedding, dtype=np.float32)

    # Match against skill→profession map
    scores  = _cosine_sim(query_vec, _sp_embeddings)
    top_idx = np.argsort(scores)[::-1][:10]

    seen        = set()
    professions = []
    for i in top_idx:
        rec  = _sp_records[i]
        prof = rec["profession"]
        if prof in seen:
            continue
        seen.add(prof)
        professions.append({
            "profession": prof,
            "match_score": round(float(scores[i]), 4),
            "required_skills": rec["skills"][:150],
        })
    return professions[:5]
