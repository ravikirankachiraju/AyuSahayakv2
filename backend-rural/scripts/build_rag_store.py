from sentence_transformers import SentenceTransformer
import json
import os

model = SentenceTransformer("all-MiniLM-L6-v2")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAG_PATH = os.path.join(DATA_DIR, "rag_store.json")

# Load existing RAG store
with open(RAG_PATH, "r", encoding="utf-8") as f:
    rag = json.load(f)

# Add embeddings
for r in rag:
    r["embedding"] = model.encode(
        [r["text"]],
        normalize_embeddings=True
    )[0].tolist()

# ✅ WRITE BACK TO THE SAME FILE
with open(RAG_PATH, "w", encoding="utf-8") as f:
    json.dump(rag, f, indent=2)

print("✅ RAG embeddings ready")
