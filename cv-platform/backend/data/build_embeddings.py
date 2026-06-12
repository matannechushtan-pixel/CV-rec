from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import json, numpy as np, os, time
from tqdm import tqdm

load_dotenv(Path(__file__).parent.parent / ".env")

DATA_DIR = Path(__file__).parent
client   = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

profiles = json.loads(
    (DATA_DIR / "all_cv_profiles.json").read_text()
)
texts = [p["embedding_text"][:8000] for p in profiles]

total_chars   = sum(len(t) for t in texts)
approx_tokens = total_chars // 4
approx_cost   = approx_tokens / 1_000_000 * 0.02
print(f"Profiles to embed: {len(texts)}")
print(f"Approx tokens:     {approx_tokens:,}")
print(f"Approx cost:       ${approx_cost:.4f} USD")
print("Starting...\n")

BATCH    = 100
all_vecs = []

for i in tqdm(range(0, len(texts), BATCH), desc="Embedding"):
    batch = texts[i : i + BATCH]
    resp  = client.embeddings.create(
        model="text-embedding-3-small",
        input=batch,
    )
    all_vecs.extend([e.embedding for e in resp.data])
    time.sleep(0.3)

arr = np.array(all_vecs, dtype=np.float32)
np.save(DATA_DIR / "cv_profile_embeddings.npy", arr)

index = [
    {"id": p["id"], "category": p["category"], "source": p["source"]}
    for p in profiles
]
(DATA_DIR / "cv_embeddings_index.json").write_text(json.dumps(index))

print(f"\nEmbeddings shape: {arr.shape}")
print(f"Index entries:    {len(index)}")
print("DONE ✓")
