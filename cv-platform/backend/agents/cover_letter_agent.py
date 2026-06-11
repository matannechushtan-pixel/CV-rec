import json

from core.ai_providers import anthropic_client, get_gemini

_COVER_LETTER_PROMPT = """
Write a professional cover letter for this candidate applying to this job.
- Tone should match the company culture described
- Reference specific requirements from the job description
- Highlight the candidate's most relevant achievements
- Keep it to 3 paragraphs, under 300 words
- Do not use clichés like "I am passionate about" or "team player"
{writing_style_instructions}
COMPANY CULTURE: {company_culture}
JOB DESCRIPTION: {job_description}
CANDIDATE CV: {cv_text}
CANDIDATE NAME: {candidate_name}

Return only the cover letter text, no preamble.
"""


async def generate_cover_letter(
    cv_text: str,
    candidate_name: str,
    job_description: str,
    company_culture: str = "professional and collaborative",
    writing_style: dict | None = None,
) -> str:
    writing_style_instructions = ""
    if writing_style:
        writing_style_instructions = (
            "- Write in a tone and style consistent with this candidate's writing style: "
            f"{json.dumps(writing_style)}\n"
        )

    prompt = _COVER_LETTER_PROMPT.format(
        company_culture=company_culture,
        job_description=job_description,
        cv_text=cv_text,
        candidate_name=candidate_name,
        writing_style_instructions=writing_style_instructions,
    )

    gemini = get_gemini("gemini-2.0-flash")
    if gemini is not None:
        resp = await gemini.generate_content_async(prompt)
        return resp.text

    # Fall back to Anthropic when GEMINI_API_KEY is not configured.
    msg = await anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text
