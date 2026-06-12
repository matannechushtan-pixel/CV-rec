from datasets import load_dataset
from pathlib import Path
from collections import Counter
import json, re, hashlib, pandas as pd

DATA_DIR = Path(__file__).parent

# ── Load LinkedIn jobs ───────────────────────────────────────
print("Loading linkedin-job-postings...")
ds1  = load_dataset("xanderios/linkedin-job-postings", split="train")
df1  = ds1.to_pandas()
orig = len(df1)
removed = Counter()

# 1. Drop rows with null title or description
mask = df1["title"].isnull() | df1["description"].isnull()
removed["null_title_or_desc"] = int(mask.sum())
df1 = df1[~mask].copy()

# 2. Drop descriptions shorter than 100 chars
df1["desc_len"] = df1["description"].str.len()
mask_short = df1["desc_len"] < 100
removed["desc_too_short"] = int(mask_short.sum())
df1 = df1[~mask_short].copy()

# 3. Drop exact duplicates (title + first 300 chars of description)
df1["fingerprint"] = (
    df1["title"].str.lower().str.strip() + "|" +
    df1["description"].str[:300]
).apply(lambda x: hashlib.md5(x.encode()).hexdigest())
mask_dup = df1.duplicated(subset=["fingerprint"], keep="first")
removed["duplicates"] = int(mask_dup.sum())
df1 = df1[~mask_dup].copy()

# 4. Normalize title: strip whitespace, title-case
df1["title_clean"] = df1["title"].str.strip().str.title()

# 5. Cap at 200 per title (prevents "Software Engineer" × 5000)
CAP = 200
before_cap = len(df1)
df1["_rank"] = df1.groupby("title_clean").cumcount()
mask_cap = df1["_rank"] >= CAP
removed["capped"] = int(mask_cap.sum())
df1 = df1[~mask_cap].drop(columns="_rank").reset_index(drop=True)

print(f"\nCleaning summary (LinkedIn):")
for reason, count in removed.items():
    print(f"  Removed ({reason}): {count}")
print(f"  Final rows: {len(df1)}")

# Build job records
def make_job_embedding_text(row) -> str:
    title    = str(row.get("title_clean", ""))
    skills   = str(row.get("skills_desc", ""))[:300]
    desc     = re.sub(r"\s+", " ", str(row.get("description", "")))[:400]
    exp      = str(row.get("formatted_experience_level", ""))
    return f"{title}. {exp}. Skills: {skills}. {desc}"

linkedin_jobs = []
for _, row in df1.iterrows():
    linkedin_jobs.append({
        "id":             f"lkdn_{int(row.get('job_id', 0)):07d}",
        "source":         "linkedin",
        "title":          row["title_clean"],
        "description":    re.sub(r"\s+", " ",
                                 str(row["description"]))[:1000],
        "skills":         str(row.get("skills_desc", ""))[:500],
        "location":       str(row.get("location", "")),
        "experience_level": str(row.get("formatted_experience_level","")),
        "min_salary":     row.get("min_salary"),
        "max_salary":     row.get("max_salary"),
        "embedding_text": make_job_embedding_text(row),
    })

# ── Load cover-letter skills dataset ─────────────────────────
print("\nLoading cover-letter-dataset...")
ds2 = load_dataset("ShashiVish/cover-letter-dataset", split="train")
df2 = ds2.to_pandas()

# Build skill→profession mapping
# Format: { "Python, SQL, Machine Learning": "Data Scientist", ... }
skill_to_profession = []
for _, row in df2.iterrows():
    title  = str(row.get("Job Title", "")).strip()
    skills = str(row.get("Skillsets", "")).strip()
    quals  = str(row.get("Qualifications", "")).strip()
    if not title or not skills or skills.lower() == "nan":
        continue
    skill_to_profession.append({
        "profession": title,
        "skills":     skills,
        "qualifications": quals,
        "embedding_text": f"{title}. Skills required: {skills}. {quals}",
    })

print(f"Skill→profession pairs: {len(skill_to_profession)}")

# ── Save both ─────────────────────────────────────────────────
(DATA_DIR / "jobs_clean.json").write_text(
    json.dumps(linkedin_jobs, ensure_ascii=False, indent=2)
)
(DATA_DIR / "skill_profession_map.json").write_text(
    json.dumps(skill_to_profession, ensure_ascii=False, indent=2)
)

# Summary
title_counts = Counter(j["title"] for j in linkedin_jobs)
print(f"\nFinal jobs dataset: {len(linkedin_jobs)} jobs")
print(f"Unique titles: {len(title_counts)}")
print(f"Top 10 titles:")
for title, count in title_counts.most_common(10):
    print(f"  {title:<40} {count}")
