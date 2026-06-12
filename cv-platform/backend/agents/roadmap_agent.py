import json

from core.ai_providers import claude_generate
from services.onet import get_onet_occupation_data
from agents.cv_agent import _extract_json

_ROADMAP_PROMPT = """
You are a career coach. Based on the candidate's current profile and their target role,
create a realistic career roadmap.

Return JSON only (no markdown):
{{
  "target_role": "",
  "current_readiness_percentage": 0,
  "estimated_weeks_to_ready": 0,
  "gaps": [
    {{
      "area": "skill or experience gap",
      "priority": 1,
      "action": "specific thing to do",
      "resource": "course, project, or certification name",
      "estimated_weeks": 4
    }}
  ],
  "immediate_actions": ["do this week"],
  "quick_wins": ["things that will improve your profile fast"]
}}

TARGET ROLE: {target_role}
ONET REQUIREMENTS FOR THIS ROLE:
{onet_data}

CANDIDATE PROFILE:
{cv_text}
"""


_UPSKILL_PROMPT = """
You are a career coach. Compare the candidate's current profile against the target role
and produce a focused upskilling plan.

Return JSON only (no markdown):
{{
  "current_level": "junior|mid|senior|lead",
  "target_role": "{target_role}",
  "gaps": [
    {{
      "skill": "specific skill or knowledge area",
      "priority": "critical|important|nice_to_have",
      "resource_url": "a specific, real, well-known learning resource URL",
      "estimated_weeks": 4
    }}
  ],
  "total_estimated_weeks": 0
}}

TARGET ROLE: {target_role}
ONET REQUIREMENTS FOR THIS ROLE:
{onet_data}

CANDIDATE PROFILE:
{cv_text}
"""


async def generate_upskill_report(cv_text: str, target_role: str) -> dict:
    onet_data = await get_onet_occupation_data(target_role)
    raw = await claude_generate(
        _UPSKILL_PROMPT.format(
            target_role=target_role,
            onet_data=json.dumps(onet_data, indent=2),
            cv_text=cv_text,
        ),
        max_tokens=2048,
    )
    return _extract_json(raw)


async def generate_roadmap(cv_text: str, target_role: str) -> dict:
    onet_data = await get_onet_occupation_data(target_role)
    raw = await claude_generate(
        _ROADMAP_PROMPT.format(
            target_role=target_role,
            onet_data=json.dumps(onet_data, indent=2),
            cv_text=cv_text,
        ),
        max_tokens=3000,
    )
    return _extract_json(raw)
