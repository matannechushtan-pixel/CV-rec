from pathlib import Path
from collections import Counter
import json

DATA_DIR = Path(__file__).parent

atlas = json.loads((DATA_DIR / "resume_atlas_clean.json").read_text())
synth = json.loads((DATA_DIR / "synthetic_cvs.json").read_text())

merged = []

for r in atlas:
    merged.append({
        "id":             r["id"],
        "source":         "resume_atlas",
        "category":       r["category"],
        "skills":         [],
        "embedding_text": r["embedding_text"],
    })

for r in synth:
    skills = r.get("skills", [])
    merged.append({
        "id":             r["id"],
        "source":         "synthetic",
        "category":       r.get("title", ""),
        "skills":         skills,
        "embedding_text": (
            f"{r.get('title','')} professional with "
            f"{r.get('years_experience', 0)} years. "
            f"Skills: {', '.join(skills[:5])}. "
            f"Industry: {r.get('industry', '')}."
        ),
    })

(DATA_DIR / "all_cv_profiles.json").write_text(
    json.dumps(merged, ensure_ascii=False, indent=2)
)

src  = Counter(r["source"]   for r in merged)
cats = Counter(r["category"] for r in merged)
print(f"Merged dataset: {len(merged)} total profiles")
print(f"  resume_atlas: {src['resume_atlas']}")
print(f"  synthetic:    {src['synthetic']}")
print(f"  categories:   {len(cats)}")
print(f"  top 10:")
for cat, count in cats.most_common(10):
    print(f"    {cat:<35} {count}")
