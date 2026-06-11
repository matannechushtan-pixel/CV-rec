"""Generate a synthetic CV dataset used to power job recommendations.

Run with: python -m data.synthetic_cvs
Writes 200 synthetic profiles to data/synthetic_cvs.json.
"""

import json
import random
from pathlib import Path

random.seed(42)

_PROFILES = {
    "Data Science": {
        "titles": [
            "Data Scientist",
            "Machine Learning Engineer",
            "Data Analyst",
            "ML Researcher",
            "Applied Scientist",
        ],
        "skills": [
            "Python", "SQL", "Pandas", "Scikit-learn", "TensorFlow", "PyTorch",
            "Statistics", "A/B Testing", "Data Visualization", "Spark", "NLP",
            "Computer Vision", "Deep Learning", "Tableau", "MLOps",
        ],
        "preferred_roles": [
            "Data Scientist", "Machine Learning Engineer", "Data Analyst",
            "AI Engineer", "Research Scientist",
        ],
    },
    "Tech": {
        "titles": [
            "Software Engineer", "Backend Engineer", "Frontend Engineer",
            "Full Stack Developer", "DevOps Engineer", "Site Reliability Engineer",
        ],
        "skills": [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "Go",
            "Docker", "Kubernetes", "AWS", "PostgreSQL", "REST APIs",
            "Microservices", "CI/CD", "System Design",
        ],
        "preferred_roles": [
            "Software Engineer", "Backend Engineer", "Full Stack Developer",
            "DevOps Engineer", "Platform Engineer",
        ],
    },
    "Marketing": {
        "titles": [
            "Marketing Manager", "Growth Marketer", "Content Strategist",
            "SEO Specialist", "Brand Manager", "Digital Marketing Specialist",
        ],
        "skills": [
            "SEO", "Content Strategy", "Google Analytics", "Social Media",
            "Email Marketing", "Brand Strategy", "Copywriting", "Paid Media",
            "Marketing Automation", "A/B Testing", "CRM",
        ],
        "preferred_roles": [
            "Marketing Manager", "Growth Marketer", "Content Strategist",
            "Brand Manager", "Digital Marketing Manager",
        ],
    },
    "Finance": {
        "titles": [
            "Financial Analyst", "Investment Analyst", "Accountant",
            "FP&A Manager", "Risk Analyst", "Finance Manager",
        ],
        "skills": [
            "Financial Modeling", "Excel", "Forecasting", "Budgeting",
            "Valuation", "Accounting", "Risk Management", "SQL",
            "Power BI", "GAAP", "Financial Reporting",
        ],
        "preferred_roles": [
            "Financial Analyst", "Finance Manager", "FP&A Manager",
            "Investment Analyst", "Risk Analyst",
        ],
    },
}

_EDUCATION_LEVELS = ["Bachelor's", "Master's", "PhD", "Bootcamp", "Associate's"]


def generate_profiles(n: int = 200) -> list[dict]:
    profiles = []
    industries = list(_PROFILES.keys())
    for i in range(n):
        industry = industries[i % len(industries)]
        cfg = _PROFILES[industry]
        title = random.choice(cfg["titles"])
        skills = random.sample(cfg["skills"], k=min(len(cfg["skills"]), random.randint(4, 7)))
        profiles.append(
            {
                "id": f"synthetic-{i + 1:03d}",
                "title": title,
                "skills": skills,
                "years_experience": random.randint(0, 15),
                "education_level": random.choice(_EDUCATION_LEVELS),
                "industry": industry,
                "preferred_roles": random.sample(
                    cfg["preferred_roles"], k=min(len(cfg["preferred_roles"]), random.randint(2, 4))
                ),
            }
        )
    return profiles


if __name__ == "__main__":
    data = generate_profiles(200)
    out_path = Path(__file__).parent / "synthetic_cvs.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(f"Wrote {len(data)} profiles to {out_path}")
