import asyncio
import json
import re

from core.ai_providers import (
    claude_generate,
    get_gemini,
    gpt_generate,
    OPENAI_AVAILABLE,
)


def _extract_json(text: str) -> dict:
    """Strip markdown code fences (```json ... ```) before parsing JSON."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(cleaned)

_PARSE_PROMPT = """
Extract the following from this CV text and return as JSON only (no markdown):
{{
  "full_name": "",
  "email": "",
  "phone": "",
  "summary": "",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{
      "company": "",
      "title": "",
      "start_date": "",
      "end_date": "",
      "bullets": ["achievement1"]
    }}
  ],
  "education": [
    {{
      "institution": "",
      "degree": "",
      "field": "",
      "graduation_year": ""
    }}
  ],
  "certifications": []
}}

CV TEXT:
{cv_text}
"""

_TAILOR_PROMPT = """
You are an expert CV writer. Rewrite the CV below to better match the job description.
Rules:
- Keep all facts true, do not invent experience
- Mirror the language and keywords from the job description where honest
- Strengthen bullet points with measurable achievements
- Do not add skills the candidate does not have
- Keep the same structure, only improve the language
{writing_style_instructions}
JOB DESCRIPTION:
{job_description}

ORIGINAL CV:
{cv_text}

Return the improved CV as plain text, ready to format.
"""

_GAP_PROMPT = """
Compare this candidate's CV against the job description.
Return JSON only (no markdown):
{{
  "match_percentage": 0,
  "strong_matches": ["skill or experience that matches well"],
  "gaps": [
    {{
      "gap": "what is missing",
      "importance": "critical|important|nice_to_have",
      "how_to_close": "specific actionable suggestion"
    }}
  ],
  "interview_risks": ["areas the interviewer will likely probe"]
}}

JOB DESCRIPTION:
{job_description}

CANDIDATE CV:
{cv_text}
"""

_GENERATE_PROMPT = """
A candidate has described their background in free text, in {language}.
Turn this description into a complete, well-written CV. Infer reasonable structure
and phrasing from the description, expand bullet points into measurable
achievements where possible, but do not invent facts (companies, titles, dates,
schools) that are not implied by the description.

Return JSON only (no markdown), with all text fields written in {language}:
{{
  "full_name": "",
  "email": "",
  "phone": "",
  "summary": "",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{
      "company": "",
      "title": "",
      "start_date": "",
      "end_date": "",
      "bullets": ["achievement1"]
    }}
  ],
  "education": [
    {{
      "institution": "",
      "degree": "",
      "field": "",
      "graduation_year": ""
    }}
  ],
  "certifications": []
}}

CANDIDATE DESCRIPTION:
{description}
"""

_IMPROVE_TRANSLATE_PROMPT = """
You are an expert CV writer. Improve and translate the CV data below into {language}.
Rules:
- Keep all facts true, do not invent experience, employers, dates, or schools
- Strengthen bullet points with clearer, more impactful language and measurable
  achievements where the original implies them
- Translate every text field (summary, titles, bullets, degree names, etc.) into
  {language}, including section content, while keeping proper nouns (names,
  companies, institutions) as-is unless they have a well-known translation
- Preserve the same JSON structure as the input

Return JSON only (no markdown), with the same shape as the input CV data:
{cv_json}
"""


async def generate_cv_from_description(description: str, language: str = "English") -> dict:
    raw = await claude_generate(
        _GENERATE_PROMPT.format(description=description, language=language), max_tokens=2048
    )
    return _extract_json(raw)


async def improve_and_translate_cv(structured_data: dict, language: str = "English") -> dict:
    prompt = _IMPROVE_TRANSLATE_PROMPT.format(
        cv_json=json.dumps(structured_data, ensure_ascii=False), language=language
    )

    gemini = get_gemini()
    if gemini is not None:
        resp = await gemini.aio.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        return _extract_json(resp.text)

    raw = await claude_generate(prompt, max_tokens=4096)
    return _extract_json(raw)


async def parse_cv(cv_text: str) -> dict:
    raw = await claude_generate(_PARSE_PROMPT.format(cv_text=cv_text), max_tokens=2048)
    return _extract_json(raw)


async def tailor_cv(cv_text: str, job_description: str, writing_style: dict | None = None) -> str:
    writing_style_instructions = ""
    if writing_style:
        writing_style_instructions = (
            "- Write in a tone and style consistent with this candidate's writing style: "
            f"{json.dumps(writing_style)}\n"
        )

    return await claude_generate(
        _TAILOR_PROMPT.format(
            cv_text=cv_text,
            job_description=job_description,
            writing_style_instructions=writing_style_instructions,
        ),
        max_tokens=4096,
    )


async def gap_analysis(cv_text: str, job_description: str) -> dict:
    raw = await claude_generate(
        _GAP_PROMPT.format(cv_text=cv_text, job_description=job_description),
        max_tokens=2048,
    )
    return _extract_json(raw)


_CV_ONLY_GAP_PROMPT = """
You are an expert career coach. Analyze the candidate's CV below WITHOUT a specific
job description. Assess the overall quality and competitiveness of the CV on the
current job market.

Return JSON only (no markdown):
{{
  "overall_score": 0,
  "summary": "a short 2-3 sentence overview of the CV's strengths and weaknesses",
  "missing_sections": ["sections that are absent but would strengthen the CV"],
  "weak_sections": [
    {{
      "section": "name of the section",
      "issue": "what is weak about it",
      "suggestion": "specific actionable improvement"
    }}
  ],
  "recommended_roles": [
    {{
      "role": "job title this candidate is well-suited for",
      "match_reason": "why this role fits their background",
      "gap_to_close": "what they'd need to develop to be a stronger fit"
    }}
  ],
  "quick_wins": ["fast, high-impact improvements the candidate can make today"],
  "keywords_to_add": ["industry/role keywords missing from the CV that recruiters search for"]
}}

CANDIDATE CV:
{cv_text}
"""


async def cv_only_gap_analysis(cv_text: str) -> dict:
    """Analyze a CV on its own (no job description) and suggest improvements and roles."""
    raw = await claude_generate(_CV_ONLY_GAP_PROMPT.format(cv_text=cv_text), max_tokens=2048)
    return _extract_json(raw)


async def _gap_analysis_openai(cv_text: str, job_description: str) -> dict:
    raw = await gpt_generate(
        _GAP_PROMPT.format(cv_text=cv_text, job_description=job_description),
        max_tokens=2048,
    )
    return _extract_json(raw)


async def gap_analysis_multi(cv_text: str, job_description: str) -> dict:
    """Run gap analysis with both Claude and GPT (when available) for a second opinion."""
    if not OPENAI_AVAILABLE:
        return {"claude": await gap_analysis(cv_text, job_description), "openai": None}

    claude_result, openai_result = await asyncio.gather(
        gap_analysis(cv_text, job_description),
        _gap_analysis_openai(cv_text, job_description),
        return_exceptions=True,
    )
    if isinstance(claude_result, Exception):
        raise claude_result
    return {
        "claude": claude_result,
        "openai": None if isinstance(openai_result, Exception) else openai_result,
    }


ENRICHMENT_QUESTIONS = [
    "Describe a recent project or task you're proud of, and what made it successful.",
    "How do you prefer to work: independently, in a small team, or in a large cross-functional group?",
    "Tell us about a time you faced a setback or conflict at work. How did you handle it?",
    "What kind of work motivates you most, and what tends to drain your energy?",
    "How would your colleagues describe your communication and writing style?",
]

_ENRICHMENT_PROMPT = """
A candidate answered the following interview questions about their work style and
communication. Based on their answers, infer:

1. A "behavioral_profile": a JSON object summarizing their working style, strengths,
   motivations, collaboration preferences, and how they handle challenges.
2. A "writing_style": a JSON object describing tone, formality, sentence length
   preference, and any notable phrasing patterns observed in their answers, so this
   can be used to personalize generated text (CVs, cover letters) to sound like them.

Return JSON only (no markdown):
{{
  "behavioral_profile": {{
    "work_style": "",
    "strengths": [],
    "motivations": [],
    "collaboration_preference": "",
    "challenge_handling": ""
  }},
  "writing_style": {{
    "tone": "",
    "formality": "casual|neutral|formal",
    "sentence_length": "short|medium|long",
    "notable_patterns": []
  }}
}}

QUESTIONS AND ANSWERS:
{qa_text}
"""


async def extract_behavioral_profile(answers: list[str]) -> dict:
    qa_text = "\n\n".join(
        f"Q: {q}\nA: {a}" for q, a in zip(ENRICHMENT_QUESTIONS, answers)
    )
    raw = await claude_generate(_ENRICHMENT_PROMPT.format(qa_text=qa_text), max_tokens=1500)
    return _extract_json(raw)


_KEYWORD_EXTRACT_PROMPT = """
You are an expert CV analyst.
Read this CV and extract the most important professional keywords.

Return JSON only — no markdown:
{{
  "job_titles_mentioned":  ["exact job titles from experience"],
  "core_skills":           ["top 10 technical and soft skills"],
  "industries":            ["industries this person has worked in"],
  "seniority_signals":     ["junior|mid|senior|lead|manager|director"],
  "education_keywords":    ["degree types, fields, institutions"],
  "search_query":          "a 1-sentence search query describing
                            the ideal job for this person, written
                            as if searching a job board"
}}

CV:
{cv_text}
"""


async def extract_cv_keywords(cv_text: str) -> dict:
    """Use Claude to extract structured keywords from a CV.

    These keywords are used to build an embedding for job matching.
    """
    raw = await claude_generate(_KEYWORD_EXTRACT_PROMPT.format(cv_text=cv_text), max_tokens=1024)
    return _extract_json(raw)
