from datasets import load_dataset
from pathlib import Path
from collections import Counter
import json, re, hashlib, pandas as pd

DATA_DIR = Path(__file__).parent

print("Loading resume-atlas...")
ds = load_dataset("ahmedheakl/resume-atlas", split="train")
df = ds.to_pandas()
original_count = len(df)
print(f"Original rows: {original_count}")

removed = Counter()

# 1. Drop null / empty
mask_null = df["Text"].isnull() | (df["Text"].str.strip() == "")
removed["null_or_empty"] = int(mask_null.sum())
df = df[~mask_null].copy()

# 2. Drop text < 100 chars
df["text_len"] = df["Text"].str.len()
mask_short = df["text_len"] < 100
removed["too_short"] = int(mask_short.sum())
df = df[~mask_short].copy()

# 3. Drop near-duplicates (keep first)
df["fingerprint"] = df["Text"].str.strip().str[:200] \
    .apply(lambda x: hashlib.md5(x.encode()).hexdigest())
mask_dup = df.duplicated(subset=["fingerprint"], keep="first")
removed["duplicates"] = int(mask_dup.sum())
df = df[~mask_dup].copy()

# 4. Cap per-category at 500 rows
CAP = 500
before_cap = len(df)
df["_rank"] = df.groupby("Category").cumcount()
mask_cap = df["_rank"] >= CAP
removed["capped"] = int(mask_cap.sum())
df = df[~mask_cap].drop(columns="_rank").reset_index(drop=True)

print(f"\nCleaning summary:")
for reason, count in removed.items():
    print(f"  Removed ({reason}): {count}")
print(f"  {'─'*30}")
print(f"  Final rows: {len(df)}")

# 5. Build clean records
def make_embedding_text(text: str, category: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return f"{category} professional. {text[:600]}"

records = []
for i, row in df.iterrows():
    text = re.sub(r"\s+", " ", row["Text"]).strip()
    records.append({
        "id":             f"atlas_{i:05d}",
        "source":         "resume_atlas",
        "category":       row["Category"],
        "text_snippet":   text[:800],
        "embedding_text": make_embedding_text(text, row["Category"]),
        "text_length":    len(text),
    })

out = DATA_DIR / "resume_atlas_clean.json"
out.write_text(json.dumps(records, ensure_ascii=False, indent=2))

# Post-clean distribution
print(f"\nPost-clean category distribution:")
cats = Counter(r["category"] for r in records)
for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
    bar = "█" * int(count / max(cats.values()) * 20)
    print(f"  {cat:<35} {count:>4}  {bar}")

avg_len = sum(r["text_length"] for r in records) // len(records)
print(f"\nAvg text length: {avg_len} chars")
print(f"Saved {len(records)} clean records → {out.name}")
