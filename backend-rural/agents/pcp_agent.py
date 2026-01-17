import json
import re
import numpy as np
from typing import Dict, List, Tuple, Optional
from sentence_transformers import SentenceTransformer
import os

# ============================================================
# Configuration
# ============================================================

MODEL = "all-MiniLM-L6-v2"
SIM_THRESHOLD = 0.45
TOP_RAG = 3

ALLOWED_MEDS = [
    "Doctor may consider Paracetamol",
    "Doctor may consider ORS",
    "Doctor may consider zinc",
    "Doctor may consider antacid",
    "Doctor may consider antihistamine"
]

# ============================================================
# Embedding model
# ============================================================

model = SentenceTransformer(MODEL)

def embed(text: str) -> np.ndarray:
    return model.encode([text], normalize_embeddings=True)[0]

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))

# ============================================================
# Load data
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

with open(os.path.join(DATA_DIR, "syndrome_library.json"), encoding="utf-8") as f:
    SYNDROMES: List[Dict] = json.load(f)

with open(os.path.join(DATA_DIR, "pcp_rules.json"), encoding="utf-8") as f:
    RULES: Dict[str, Dict] = json.load(f)

# Pre-compute embeddings for syndromes
for s in SYNDROMES:
    s["_vec"] = embed(" ".join(s.get("keywords", [])))

# ============================================================
# Utilities
# ============================================================

def extract_days(text: str) -> int:
    """Extract number of days mentioned in text."""
    m = re.search(r"(\d+)\s*day", text.lower())
    return int(m.group(1)) if m else 0

# ============================================================
# Syndrome matching (FIXED & SAFE)
# ============================================================

def match_syndrome(text: str) -> Tuple[Optional[Dict], float]:
    """
    Always returns:
      (syndrome_dict | None, similarity_score)
    Never returns floats in place of dicts.
    """
    v = embed(text)
    scored = [(cosine(v, s["_vec"]), s) for s in SYNDROMES]
    scored.sort(reverse=True)

    if not scored:
        return None, 0.0

    best_score, best_syndrome = scored[0]

    if best_score < SIM_THRESHOLD:
        return None, float(best_score)

    return best_syndrome, float(best_score)

# ============================================================
# RAG helper
# ============================================================

def rag(query: str, store: List[Dict]) -> List[Dict]:
    qv = embed(query)
    scored = []

    for r in store:
        emb = np.array(r["embedding"], dtype=np.float32)
        score = cosine(qv, emb)
        if score > 0.25:
            scored.append((score, r))

    scored.sort(reverse=True)
    return [r for _, r in scored[:TOP_RAG]]

# ============================================================
# Main PCP planner (FULLY HARDENED)
# ============================================================

def build_plan(case_text: str, vitals: Dict, rag_store: List[Dict]) -> Dict:
    """
    Deterministic PCP plan builder.
    GUARANTEES:
      - No floats treated as dicts
      - Safe fallbacks
      - Clear errors instead of silent crashes
    """

    # -------- Duration safety --------
    if extract_days(case_text) >= 6:
        return {"error": "prolonged"}

    # -------- Syndrome matching --------
    syndrome, score = match_syndrome(case_text)

    # -------- Fallback if no valid syndrome --------
    if not isinstance(syndrome, dict):
        syndrome = next(
            s for s in SYNDROMES if s.get("id") == "non_specific_mild_illness"
        )
        score = 0.4

    # -------- HARD ASSERT (prevents float bug forever) --------
    if not isinstance(syndrome, dict):
        raise RuntimeError(
            f"PCP ERROR: Invalid syndrome object: {syndrome} ({type(syndrome)})"
        )

    template = syndrome.get("default_template")

    if not isinstance(template, str) or template not in RULES:
        raise RuntimeError(
            f"PCP ERROR: Invalid default_template '{template}' "
            f"for syndrome '{syndrome.get('id')}'"
        )

    rule = RULES[template]

    # -------- RAG augmentation --------
    snippets = rag(syndrome.get("name", ""), rag_store)

    def add_snippets(base: List[str]) -> List[str]:
        out = list(base)
        for s in snippets:
            out.append(f"{s['text']} (Source: {s['source']})")
        return out[:6]

    # -------- Medicines filtering --------
    meds = [
        m for m in rule.get("medicines_advised", [])
        if any(a.lower() in m.lower() for a in ALLOWED_MEDS)
    ]

    # -------- Final plan --------
    return {
        "condition_summary": rule.get("condition_summary", ""),
        "possible_causes": rule.get("possible_causes", []),
        "nurse_actions": add_snippets(rule.get("nurse_actions", [])),
        "escalation_criteria": add_snippets(rule.get("escalation_criteria", [])),
        "medicines_advised": meds,
        "meta": {
            "syndrome": syndrome.get("id"),
            "score": round(float(score), 2),
        },
    }
