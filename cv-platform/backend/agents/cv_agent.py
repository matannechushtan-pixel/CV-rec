import json
import re

from core.ai_providers import anthropic_client as _client, get_gemini


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
    msg = await _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": _GENERATE_PROMPT.format(description=description, language=language),
            }
        ],
    )
    return _extract_json(msg.content[0].text)


async def improve_and_translate_cv(structured_data: dict, language: str = "English") -> dict:
    prompt = _IMPROVE_TRANSLATE_PROMPT.format(
        cv_json=json.dumps(structured_data, ensure_ascii=False), language=language
    )

    gemini = get_gemini("gemini-2.0-flash")
    if gemini is not None:
        resp = await gemini.generate_content_async(prompt)
        return _extract_json(resp.text)

    msg = await _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(msg.content[0].text)


async def parse_cv(cv_text: str) -> dict:
    msg = await _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": _PARSE_PROMPT.format(cv_text=cv_text)}],
    )
    return _extract_json(msg.content[0].text)


async def tailor_cv(cv_text: str, job_description: str, writing_style: dict | None = None) -> str:
    writing_style_instructions = ""
    if writing_style:
        writing_style_instructions = (
            "- Write in a tone and style consistent with this candidate's writing style: "
            f"{json.dumps(writing_style)}\n"
        )

    msg = await _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": _TAILOR_PROMPT.format(
                    cv_text=cv_text,
                    job_description=job_description,
                    writing_style_instructions=writing_style_instructions,
                ),
            }
        ],
    )
    return msg.content[0].text


async def gap_analysis(cv_text: str, job_description: str) -> dict:
    msg = await _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": _GAP_PROMPT.format(
                    cv_text=cv_text, job_description=job_description
                ),
            }
        ],
    )
    return _extract_json(msg.content[0].text)


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
    msg = await _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": _ENRICHMENT_PROMPT.format(qa_text=qa_text)}],
    )
    return _extract_json(msg.content[0].text)
