from datasets import load_dataset
from collections import Counter
from pathlib import Path
import pandas as pd, hashlib

print("=" * 60)
print("EDA — Jobs Datasets")
print("=" * 60)

# ── Dataset 1: LinkedIn Job Postings (33K, MIT) ──────────────
print("\n── DATASET 1: xanderios/linkedin-job-postings ──")
ds1 = load_dataset("xanderios/linkedin-job-postings", split="train")
df1 = ds1.to_pandas()

print(f"Rows:    {len(df1)}")
print(f"Columns: {list(df1.columns)}")

# Missing values
print("\nMissing values:")
for col in ["title", "description", "skills_desc",
            "formatted_experience_level", "location"]:
    if col in df1.columns:
        null_count = df1[col].isnull().sum()
        empty_count = (df1[col] == "").sum()
        print(f"  {col:<35} null={null_count:>5}  empty={empty_count:>5}")

# Title distribution (top 20)
print("\nTop 20 job titles:")
title_counts = df1["title"].value_counts().head(20)
for title, count in title_counts.items():
    print(f"  {title:<45} {count}")

# Experience level distribution
if "formatted_experience_level" in df1.columns:
    print("\nExperience levels:")
    for level, count in df1["formatted_experience_level"].value_counts().items():
        print(f"  {str(level):<30} {count}")

# Description length stats
df1["desc_len"] = df1["description"].fillna("").str.len()
print(f"\nDescription length:")
print(f"  min={int(df1['desc_len'].min())}  "
      f"median={int(df1['desc_len'].median())}  "
      f"max={int(df1['desc_len'].max())}")

# Duplicates
dup_titles = df1.duplicated(subset=["title", "description"]).sum()
print(f"\nDuplicate (title+description): {dup_titles}")

# ── Dataset 2: Cover Letter / Skills Dataset (1.16K) ────────
print("\n── DATASET 2: ShashiVish/cover-letter-dataset ──")
ds2 = load_dataset("ShashiVish/cover-letter-dataset", split="train")
df2 = ds2.to_pandas()

print(f"Rows:    {len(df2)}")
print(f"Columns: {list(df2.columns)}")

print("\nJob title distribution (top 20):")
for title, count in df2["Job Title"].value_counts().head(20).items():
    print(f"  {title:<45} {count}")

print("\nMissing values:")
for col in df2.columns:
    n = df2[col].isnull().sum()
    if n > 0:
        print(f"  {col:<35} null={n}")

print("\nSkillsets sample (first 5):")
for _, row in df2.head(5).iterrows():
    print(f"  [{row['Job Title']}] {str(row.get('Skillsets',''))[:80]}")

print("\nEDA COMPLETE ✓")
