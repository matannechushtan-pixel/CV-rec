import json
import logging
import re
from pathlib import Path

from core.ai_providers import claude_generate, gemini_generate

logger = logging.getLogger(__name__)

_SECTION_EXAMPLES: dict[str, list[str]] = json.loads(
    (Path(__file__).parent.parent / "data" / "section_examples.json").read_text()
)


def _examples(key: str, n: int = 6) -> str:
    return ", ".join(_SECTION_EXAMPLES.get(key, [])[:n])


_CLASSIFICATION_RULES = """
CLASSIFICATION RULES (apply these strictly when assigning content to sections):
- Courses, bootcamps, and certifications belong in "education", not "skills".
  Examples: {courses_examples}
- Technical tools, programming languages, software, and frameworks belong in "skills".
  Examples: {skills_examples}
- Personal activities, sports, and pastimes belong only in "hobbies", never in "skills" or "experience".
  Examples: {hobbies_examples}
- Soft skills (e.g. "communication", "leadership") belong in "skills" only if the
  candidate explicitly states them.
- Education entries (degrees, schools) look like: {education_examples}
- Work experience entries look like: {experience_examples}
- Military service belongs in "military", not "experience". Examples: {military_examples}
- Volunteering belongs in "volunteering", not "experience". Examples: {volunteering_examples}
""".format(
    courses_examples=_examples("courses_and_certifications"),
    skills_examples=_examples("skills"),
    hobbies_examples=_examples("hobbies"),
    education_examples=_examples("education"),
    experience_examples=_examples("experience"),
    military_examples=_examples("military"),
    volunteering_examples=_examples("volunteering"),
)

_CV_SCHEMA = """{
  "full_name": "",
  "summary": "",
  "contact": {
    "location": "",
    "phone": "",
    "email": ""
  },
  "education": [
    {
      "institution": "",
      "degree": "",
      "dates": "",
      "notes": ""
    }
  ],
  "languages": [
    {"name": "", "level": ""}
  ],
  "skills": ["skill1", "skill2"],
  "hobbies": "",
  "experience": [
    {
      "company": "",
      "location": "",
      "role": "",
      "dates": "",
      "bullets": ["achievement1", "achievement2"]
    }
  ],
  "military": {
    "unit": "",
    "role": "",
    "dates": "",
    "bullets": []
  },
  "volunteering": [
    {"org": "", "year": "", "description": ""}
  ]
}"""


def _parse_json(text: str) -> dict:
    """Strip markdown code fences (```json ... ```) before parsing JSON."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(cleaned)


_HEBREW_NOTE = """
IMPORTANT — Hebrew output rules:
- Write ALL text in fluent, professional Israeli Hebrew
- Use formal (גוף שלישי / לשון רשמית) register
- Action verbs: ניהל, בנה, הוביל, פיתח, השיג, הגדיל...
- Do NOT mix Hebrew and English (except company names and
  technical terms that are commonly used in English in Israel)
- Numbers and dates stay in Western format (2023, 15%)
"""


def _hebrew_note(language: str) -> str:
    if language and language.lower() in ("hebrew", "עברית", "he"):
        return _HEBREW_NOTE
    return ""


_GENERATE_PROMPT = """
You are an expert CV writer. A candidate described their background in free text below,
written in {language}. Turn this description into a complete, well-structured CV.

Rules:
- Write all text fields in {language}
- Infer reasonable structure from the description, expand bullet points into clear,
  measurable achievements where possible
- Do not invent companies, titles, dates, or schools that are not implied by the description
- Omit "military" if not mentioned, omit "volunteering" if not mentioned
{hebrew_note}
{classification_rules}

- Return ONLY valid JSON (no markdown, no commentary), matching exactly this shape:

{schema}

CANDIDATE DESCRIPTION:
{description}
"""

_IMPROVE_PROMPT = """
You are an expert CV writer. Below is the raw text extracted from a candidate's existing CV.
Restructure and improve it into a polished CV in {language}.

Rules:
- Keep all facts true: do not invent employers, titles, dates, schools, or skills
- Strengthen bullet points with clearer, more impactful language and measurable
  achievements where the original implies them
- Translate/write all text fields in {language}, keeping proper nouns (names,
  companies, institutions) as-is unless they have a well-known translation
- Omit "military" if not present in the source, omit "volunteering" if not present
{hebrew_note}
{classification_rules}

- Return ONLY valid JSON (no markdown, no commentary), matching exactly this shape:

{schema}

RAW CV TEXT:
{cv_text}
"""

_TEMPLATE_PROMPT = """
You are an expert CV writer. A candidate filled out a structured form with the answers below.
Use these answers to produce a polished, complete CV in {language}.

Rules:
- Write all text fields in {language}
- Polish phrasing and expand bullet points into clear, measurable achievements where
  the answers imply them, but do not invent facts not present in the answers
- Omit "military" if not provided, omit "volunteering" if not provided
{hebrew_note}
{classification_rules}

- Return ONLY valid JSON (no markdown, no commentary), matching exactly this shape:

{schema}

FORM ANSWERS (JSON):
{answers_json}
"""


async def _run_prompt(prompt: str, max_tokens: int = 3000) -> tuple[dict, str]:
    """Run a structured-CV prompt on Gemini, falling back to Claude on failure.

    Returns a tuple of (parsed_json, model_used) so callers can surface which
    model actually produced the result (e.g. "Generated by Claude (fallback)").
    """
    try:
        raw = await gemini_generate(prompt)
        return _parse_json(raw), "gemini-2.0-flash"
    except Exception as e:
        logger.warning("Gemini failed (%s), falling back to Claude", e)
        raw = await claude_generate(prompt, max_tokens=max_tokens)
        return _parse_json(raw), "claude-sonnet-4-6 (fallback)"


async def generate_from_description(description: str, language: str = "English") -> tuple[dict, str]:
    """Generate a structured CV from a free-text description of the candidate's background."""
    prompt = _GENERATE_PROMPT.format(
        description=description, language=language, schema=_CV_SCHEMA,
        classification_rules=_CLASSIFICATION_RULES, hebrew_note=_hebrew_note(language),
    )
    return await _run_prompt(prompt)


async def improve_uploaded_cv(cv_text: str, language: str = "English") -> tuple[dict, str]:
    """Restructure and improve raw CV text extracted from an uploaded file."""
    prompt = _IMPROVE_PROMPT.format(
        cv_text=cv_text, language=language, schema=_CV_SCHEMA,
        classification_rules=_CLASSIFICATION_RULES, hebrew_note=_hebrew_note(language),
    )
    return await _run_prompt(prompt)


async def fill_from_template(answers: dict, language: str = "English") -> tuple[dict, str]:
    """Generate a structured CV from answers to a structured CV template form."""
    prompt = _TEMPLATE_PROMPT.format(
        answers_json=json.dumps(answers, ensure_ascii=False),
        language=language,
        schema=_CV_SCHEMA,
        classification_rules=_CLASSIFICATION_RULES,
        hebrew_note=_hebrew_note(language),
    )
    return await _run_prompt(prompt)


_COVER_LETTER_PROMPT = """You are an expert cover letter writer.
Write a compelling, personalised cover letter in {language}.

Rules:
- 3 paragraphs: hook + why I fit + call to action
- Mirror keywords from the job description
- Sound human, not robotic — no clichés like "I am a hardworking individual"
- Max 300 words
- Return ONLY the letter text, no subject line, no JSON

Candidate CV:
{cv_str}

Job description:
{job_description}
"""


async def generate_cover_letter(cv_data: dict, job_description: str, language: str = "English") -> str:
    """Write a personalised cover letter for the given CV and job description."""
    cv_str = json.dumps(cv_data, ensure_ascii=False)
    prompt = _COVER_LETTER_PROMPT.format(cv_str=cv_str, job_description=job_description, language=language)
    try:
        return (await gemini_generate(prompt)).strip()
    except Exception as e:
        logger.warning("Gemini failed (%s), falling back to Claude", e)
        return (await claude_generate(prompt)).strip()


_TRANSLATE_PROMPT = """Translate all text fields in this CV JSON to {target_language}.
Keep the exact same JSON structure and keys in English.
Only translate the values (names, bullets, descriptions).
Return ONLY valid JSON. No markdown.

CV: {cv_str}
"""


async def translate_cv(cv_data: dict, target_language: str) -> tuple[dict, str]:
    """Translate every text value in a structured CV into the target language."""
    cv_str = json.dumps(cv_data, ensure_ascii=False)
    prompt = _TRANSLATE_PROMPT.format(cv_str=cv_str, target_language=target_language)
    return await _run_prompt(prompt)
