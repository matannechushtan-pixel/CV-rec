from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import json, numpy as np, os, time
from tqdm import tqdm

load_dotenv(Path(__file__).parent.parent / ".env")

DATA_DIR = Path(__file__).parent
client   = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Embed job postings ───────────────────────────────────────
jobs = json.loads((DATA_DIR / "jobs_clean.json").read_text())
texts = [j["embedding_text"][:8000] for j in jobs]

total_tokens = sum(len(t) for t in texts) // 4
cost = total_tokens / 1_000_000 * 0.02
print(f"Jobs to embed:  {len(texts)}")
print(f"Approx tokens:  {total_tokens:,}")
print(f"Approx cost:    ${cost:.4f} USD")

BATCH    = 100
all_vecs = []
for i in tqdm(range(0, len(texts), BATCH), desc="Embedding jobs"):
    batch = texts[i : i + BATCH]
    resp  = client.embeddings.create(
        model="text-embedding-3-small", input=batch)
    all_vecs.extend([e.embedding for e in resp.data])
    time.sleep(0.3)

arr = np.array(all_vecs, dtype=np.float32)
np.save(DATA_DIR / "job_embeddings.npy", arr)

index = [{"id": j["id"], "title": j["title"],
           "source": j["source"]} for j in jobs]
(DATA_DIR / "job_embeddings_index.json").write_text(
    json.dumps(index))

print(f"Job embeddings: {arr.shape}")

# ── Embed skill→profession map ───────────────────────────────
sp_map = json.loads(
    (DATA_DIR / "skill_profession_map.json").read_text())
sp_texts = [r["embedding_text"][:2000] for r in sp_map]

sp_vecs = []
for i in tqdm(range(0, len(sp_texts), BATCH),
              desc="Embedding skill-profession"):
    batch = sp_texts[i : i + BATCH]
    resp  = client.embeddings.create(
        model="text-embedding-3-small", input=batch)
    sp_vecs.extend([e.embedding for e in resp.data])
    time.sleep(0.2)

sp_arr = np.array(sp_vecs, dtype=np.float32)
np.save(DATA_DIR / "skill_profession_embeddings.npy", sp_arr)
print(f"Skill-profession embeddings: {sp_arr.shape}")
print("DONE ✓")
