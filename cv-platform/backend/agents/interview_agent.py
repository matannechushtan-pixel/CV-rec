import anthropic

from core.config import settings
from agents.cv_agent import _extract_json

_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

_QUESTIONS_PROMPT = """
You are an interview coach. Based on the candidate's CV and the target role / job description below,
generate likely interview questions and guidance for answering them.

Return JSON only (no markdown):
{{
  "questions": [
    {{
      "question": "the interview question",
      "type": "behavioral",
      "guidance": "How to answer using the STAR method (Situation, Task, Action, Result), tailored to this candidate's background"
    }}
  ]
}}

Generate exactly 5 questions with "type": "behavioral" (each with STAR-method guidance)
and 5 questions with "type": "technical" (each with guidance describing a strong approach
to answering, referencing the candidate's actual skills/experience where relevant).

TARGET ROLE / JOB DESCRIPTION:
{job_description}

CANDIDATE CV:
{cv_text}
"""


async def generate_questions(cv_text: str, job_description: str) -> dict:
    msg = await _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[
            {
                "role": "user",
                "content": _QUESTIONS_PROMPT.format(
                    job_description=job_description, cv_text=cv_text
                ),
            }
        ],
    )
    return _extract_json(msg.content[0].text)
