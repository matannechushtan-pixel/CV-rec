from datasets import load_dataset
from collections import Counter
from pathlib import Path
import pandas as pd
import hashlib

print("=" * 60)
print("EDA — ahmedheakl/resume-atlas")
print("=" * 60)

print("\nDownloading dataset...")
ds = load_dataset("ahmedheakl/resume-atlas", split="train")
df = ds.to_pandas()

# ── BASIC SHAPE ──────────────────────────────────────────────
print(f"\n── BASIC INFO ──")
print(f"Total rows:    {len(df)}")
print(f"Columns:       {list(df.columns)}")
print(f"Memory usage:  {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

# ── MISSING VALUES ───────────────────────────────────────────
print(f"\n── MISSING VALUES ──")
missing   = df.isnull().sum()
empty_str = (df == "").sum()
for col in df.columns:
    print(f"  {col:<12} null={missing[col]:>5}  "
          f"empty_string={empty_str[col]:>5}")

# ── TEXT LENGTH STATS ────────────────────────────────────────
print(f"\n── TEXT LENGTH STATS ──")
df["text_len"] = df["Text"].fillna("").str.len()
stats = df["text_len"].describe()
print(f"  min:    {int(stats['min']):>8} chars")
print(f"  25%:    {int(stats['25%']):>8} chars")
print(f"  median: {int(stats['50%']):>8} chars")
print(f"  75%:    {int(stats['75%']):>8} chars")
print(f"  max:    {int(stats['max']):>8} chars")
print(f"  mean:   {int(stats['mean']):>8} chars")

too_short = df[df["text_len"] < 100]
print(f"\n  Rows with text < 100 chars: {len(too_short)}")
if len(too_short) > 0:
    print("  Examples:")
    for _, row in too_short.head(3).iterrows():
        print(f"    [{row['Category']}] '{row['Text'][:80]}'")

# ── DUPLICATES ───────────────────────────────────────────────
print(f"\n── DUPLICATES ──")
exact_dups = df.duplicated(subset=["Text"]).sum()
print(f"  Exact duplicate texts:           {exact_dups}")

df["fingerprint"] = df["Text"].fillna("").str.strip().str[:200] \
    .apply(lambda x: hashlib.md5(x.encode()).hexdigest())
near_dups = df.duplicated(subset=["fingerprint"]).sum()
print(f"  Near-duplicates (first 200 chars): {near_dups}")

cat_dups = df.duplicated(subset=["Category", "fingerprint"]).sum()
print(f"  Same category + near-duplicate:    {cat_dups}")

# ── CATEGORY DISTRIBUTION ────────────────────────────────────
print(f"\n── CATEGORY DISTRIBUTION ──")
cat_counts = df["Category"].value_counts()
print(f"  Total categories: {len(cat_counts)}")
print(f"  {'Category':<35} {'Count':>6}  {'%':>6}")
print(f"  {'-'*52}")
for cat, count in cat_counts.items():
    bar = "█" * int(count / cat_counts.max() * 20)
    pct = count / len(df) * 100
    print(f"  {cat:<35} {count:>6}  {pct:>5.1f}%  {bar}")

# ── IMBALANCE WARNING ────────────────────────────────────────
print(f"\n── CLASS IMBALANCE ──")
print(f"  Most common:   {cat_counts.index[0]} ({cat_counts.iloc[0]})")
print(f"  Least common:  {cat_counts.index[-1]} ({cat_counts.iloc[-1]})")
ratio = cat_counts.iloc[0] / cat_counts.iloc[-1]
print(f"  Max/min ratio: {ratio:.1f}x")
if ratio > 5:
    print("  ⚠️  HIGH IMBALANCE — will cap at 500 per category")

# ── CLEANING PREVIEW ─────────────────────────────────────────
total_remove = df[
    df["Text"].isnull() |
    (df["Text"] == "") |
    (df["text_len"] < 100) |
    df.duplicated(subset=["fingerprint"])
].shape[0]

print(f"\n── CLEANING PREVIEW ──")
print(f"  Null / empty:      {df['Text'].isnull().sum() + (df['Text']=='').sum()}")
print(f"  Text < 100 chars:  {len(too_short)}")
print(f"  Near-duplicates:   {near_dups}")
print(f"  Total to remove:   {total_remove}")
print(f"  Rows remaining:    {len(df) - total_remove} (before cap)")

if ratio > 10:
    print("\n  ⚠️  WARNING: imbalance ratio > 10x")
if near_dups > 1000:
    print("\n  ⚠️  WARNING: near-duplicates > 1000")

df.head(100).to_csv(Path(__file__).parent / "eda_raw_sample.csv",
                     index=False)
print(f"\n  Saved first 100 rows → eda_raw_sample.csv")
print("\nEDA COMPLETE ✓")
