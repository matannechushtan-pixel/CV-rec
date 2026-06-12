"""
Uses Claude to extract structured job listings from email HTML/text.
Handles all Israeli job board email formats automatically.
"""
import json
import logging
import re
from core.ai_providers import claude_generate

logger = logging.getLogger(__name__)

# Known Israeli job board senders — used to prioritize parsing
KNOWN_JOB_SENDERS = {
    "alljobs":    ["alljobs.co.il", "noreply@alljobs.co.il"],
    "drushim":    ["drushim.co.il", "jobs@drushim.co.il"],
    "jobmaster":  ["jobmaster.co.il"],
    "linkedin":   ["linkedin.com", "jobalerts@linkedin.com"],
    "indeed":     ["indeed.com", "alert@indeed.com"],
    "glassdoor":  ["glassdoor.com"],
    "jobnet":     ["jobnet.co.il"],
}

_EXTRACT_PROMPT = """
You are an expert at reading job alert emails from Israeli job boards.
Extract ALL job listings from this email content.

Rules:
- Extract EVERY job mentioned, even if briefly
- If salary is in ILS (₪/NIS), convert to numbers (e.g. "20,000" → 20000)
- If salary is in USD ($), keep as-is
- Location: prefer Israeli city names. If "Remote" appears, use "Remote, Israel"
- company: extract company name. If not found, use the job board name
- source_board: which job board sent this email ({source_board})
- For missing fields, use null — never invent data

Return ONLY valid JSON array, no markdown:
[
  {{
    "title":       "exact job title",
    "company":     "company name or null",
    "location":    "city, Israel or Remote, Israel",
    "description": "job description snippet (max 500 chars)",
    "apply_url":   "direct application URL or null",
    "salary_min":  null or number (monthly ILS or annual USD),
    "salary_max":  null or number,
    "salary_currency": "ILS" or "USD" or null,
    "employment_type": "Full-time" or "Part-time" or "Contract" or null,
    "required_skills": ["skill1", "skill2"]
  }}
]

If no jobs found, return: []

Email content:
{email_content}
"""

def _detect_source(sender: str) -> str:
    """Identify which job board sent this email."""
    sender_lower = sender.lower()
    for board, domains in KNOWN_JOB_SENDERS.items():
        if any(d in sender_lower for d in domains):
            return board
    return "email_unknown"

def _clean_html(html: str) -> str:
    """Extract readable text from HTML email."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    # Remove script/style tags
    for tag in soup(["script", "style", "head", "meta"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()[:8000]   # Claude context limit safety

async def extract_jobs_from_email(
    sender:       str,
    subject:      str,
    body_html:    str,
    body_text:    str,
) -> list[dict]:
    """
    Main function: given a raw email, return list of job dicts.
    Returns [] if no jobs found or parsing fails.
    """
    source_board = _detect_source(sender)

    # Build readable content for Claude
    if body_html:
        content = _clean_html(body_html)
    else:
        content = body_text[:8000]

    # Add subject for context
    content = f"Subject: {subject}\n\nBody:\n{content}"

    try:
        raw = await claude_generate(
            prompt=_EXTRACT_PROMPT.format(
                email_content=content,
                source_board=source_board,
            ),
            model="claude-haiku-4-5-20251001",  # Fast + cheap for parsing
            max_tokens=4096,
        )
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw.strip())
        jobs = json.loads(raw)

        if not isinstance(jobs, list):
            return []

        # Add source_board to each job
        for job in jobs:
            job["source"] = f"email_{source_board}"

        logger.info(
            "Extracted %d jobs from %s email: %s",
            len(jobs), source_board, subject[:50]
        )
        return jobs

    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from email: %s", subject[:50])
        return []
    except Exception as e:
        logger.error("Email parsing error: %s", e)
        return []
