import anthropic

from core.config import settings
from core.ai_providers import claude_generate
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


_EVALUATE_ANSWER_PROMPT = """
You are an interview coach. Evaluate the candidate's answer to the following interview question.

QUESTION:
{question}

CANDIDATE'S ANSWER:
{user_answer}

CANDIDATE'S CV:
{cv_text}

Return JSON only (no markdown):
{{
  "score": <integer 0-100, overall quality of the answer>,
  "strengths": ["specific strength 1", "specific strength 2"],
  "improvements": ["specific improvement 1", "specific improvement 2"],
  "better_answer": "a STAR-structured (Situation, Task, Action, Result) model answer tailored to this candidate's background"
}}
"""


async def evaluate_answer(question: str, user_answer: str, cv_text: str) -> dict:
    raw = await claude_generate(
        prompt=_EVALUATE_ANSWER_PROMPT.format(
            question=question, user_answer=user_answer, cv_text=cv_text
        ),
        max_tokens=2048,
    )
    return _extract_json(raw)
